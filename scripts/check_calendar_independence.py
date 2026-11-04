"""Review the calendar pilot's volatility separation and diagnostic sensitivity.

Uses exactly its 20 recorded seeds/configs. The existing diagnostic's 199 whole-
process randomizations and .05 screen remain provisional engineering settings.
This neither runs new DML experiments nor approves manipulation thresholds.
"""
from dataclasses import asdict, replace
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from research.week2_completion.dgp import Config, build_world, simulate_calendar_regimes
from research.week2_completion.dml import make_folds, audit_folds
from src.dgp.independence import conditional_randomization_check
from src.evaluation.verification import rate_summary
from src.evaluation.week3_audit import provenance, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    cfg = Config(gamma=0., tau=1.)
    config = {'base_config': asdict(cfg), 'seeds': list(range(20000, 20020)),
        'randomizations': 199, 'diagnostic_alpha': .05,
        'diagnostic_rng': 'SeedSequence(seed, spawn_key=(90,)); reset for control pairing',
        'null_rng': 'Two independent uint64 seeds from diagnostic RNG per draw: layout, shock',
        'control': 'Actual build_world break_vol_independence=True path',
        'scope': 'Reviewer pilot diagnostic; no Gate 2/3 approval or final robustness subset'}
    write_json(args.output / 'config.json', config)
    sources = [Path(__file__), ROOT / 'research/week2_completion/dgp.py',
               ROOT / 'research/week2_completion/dml.py', ROOT / 'src/dgp/independence.py']
    start = provenance(sources)
    rows = []
    for seed in config['seeds']:
        base = replace(cfg, seed=seed)
        data = build_world(base)
        broken = build_world(replace(base, break_vol_independence=True))
        changed = build_world(replace(base, gamma=1., tau=0., n_regimes=16, density=.8))
        def simulator(T, density, K, rng):
            addresses = rng.integers(0, np.iinfo(np.uint64).max, size=2, dtype=np.uint64)
            ids, shocks, _ = simulate_calendar_regimes(T, density, K, base.sd_shock,
                np.random.default_rng(int(addresses[0])), np.random.default_rng(int(addresses[1])))
            return ids, shocks
        checks = {}
        for name, world in [('independent', data), ('positive_control', broken)]:
            checks[name] = conditional_randomization_check(world['sig']**2, world['rid_t'], world['U_t'],
                simulator, density=base.density, n_regimes=base.n_regimes,
                rng=np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(90,))), randomizations=199)
        fold_diagnostics = {}
        fold_rng = np.random.default_rng(seed)
        for scheme in ('random', 'grouped'):
            fold = make_folds(scheme, data['cluster_memberships'], 5, fold_rng)
            fold_diagnostics[scheme] = audit_folds(data, fold)
        returns = data['sig'] * data['z']
        row = {'seed': seed, **checks, 'unchanged_sigma': bool(np.array_equal(data['sig'], changed['sig'])),
            'unchanged_standardized_innovations': bool(np.array_equal(data['z'], changed['z'])),
            'fold_diagnostics': fold_diagnostics, 'nonfinite_returns': int((~np.isfinite(returns)).sum()),
            'nonpositive_sigma': int((data['sig'] <= 0).sum()),
            'max_abs_idiosyncratic_return': float(np.max(np.abs(returns)))}
        rows.append(row)
        write_json(args.output / f'seed_{seed}.json', row)
    end = provenance(sources)
    if start['input_sha256'] != end['input_sha256']:
        raise ValueError('Source changed during diagnostic review')
    summaries = {}
    for key in ('independent', 'positive_control'):
        usable = [row[key]['p_value'] for row in rows if row[key]['status'] == 'evaluated']
        hits = sum(p <= .05 for p in usable)
        summaries[key] = {'planned': len(rows), 'evaluated': len(usable), 'detections': hits,
                          **rate_summary(hits, len(usable))}
    write_json(args.output / 'summary.json', {'config': config, 'rates': summaries,
        'stream_invariance_failures': sum(not r['unchanged_sigma'] or not r['unchanged_standardized_innovations'] for r in rows),
        'nonfinite_returns': sum(r['nonfinite_returns'] for r in rows),
        'nonpositive_sigma': sum(r['nonpositive_sigma'] for r in rows),
        'max_abs_idiosyncratic_return': max(r['max_abs_idiosyncratic_return'] for r in rows),
        'provenance': end,
        'interpretation': 'Calendar DGP source recheck, not proof of independence, DML calibration, or Gate approval. Calendar-factor fold links are potential dependence sources, not measured effect sizes.'})
    print(summaries)


if __name__ == '__main__':
    main()
