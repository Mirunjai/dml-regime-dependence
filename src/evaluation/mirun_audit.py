"""Independently audit the reviewed calendar-DML runner's saved attempts.

Standard library only. The manifest defines planned work, including scenarios
absent from an interrupted run.json. Atomic replication files are authoritative;
inline summaries never fill missing attempts. This does not approve Gate 2/3.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

from .verification import CELLS, audit_results, audit_stability, compare_claims, finite, file_hash
from .week3_audit import (markdown_report, provenance, read_json, save_source_snapshot, write_json)

STREAMS = ('cov', 'dates', 'vol', 'factor', 'layout', 'shock', 'regime_treat', 'treat', 'noise')
SOURCES = ('__init__.py', 'dgp.py', 'dml.py', 'run_week2.py', 'validation.py')
ALIASES = {
    'attempted_reps': 'attempted', 'successful_reps': 'valid', 'failed_reps': 'failed',
    'coverage': 'coverage95', 'mc_se_coverage': 'coverage_mcse',
    'mean_interval_width': 'mean_ci_width', 'mc_se_width': 'width_mcse',
    'bias': 'bias', 'mc_se_bias': 'bias_mcse', 'rmse': 'rmse',
    'empirical_size': 'empirical_size', 'mc_se_size': 'size_mcse',
    'power': 'power', 'mc_se_power': 'power_mcse',
}


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


def _inside(root, path):
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Saved input escapes the run directory')
    return path


def _same_json(a, b):
    # Python equality treats True == 1; provenance contracts must not.
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def source_check(recorded, source_root):
    """Check content against a local Git object, or current files as a fallback.

    This detects inconsistent bytes, not the authenticity of producer metadata.
    A portable archive without source is explicitly unverified.
    """
    hashes = recorded.get('source_sha256', {})
    if (set(hashes) != set(SOURCES) or any(not isinstance(v, str) or
            re.fullmatch('[0-9a-f]{64}', v) is None for v in hashes.values())):
        raise ValueError('Malformed producer source hashes')
    commit = recorded.get('git_commit', '')
    if not isinstance(commit, str) or re.fullmatch('[0-9a-f]{40}', commit) is None:
        raise ValueError('Malformed producer Git commit')
    source_root = Path(source_root)
    try:
        blobs = {name: subprocess.check_output(
            ['git', '-C', str(source_root), 'show', f'{commit}:research/week2_completion/{name}'],
            stderr=subprocess.DEVNULL) for name in SOURCES}
    except (OSError, subprocess.CalledProcessError):
        blobs = None
    if blobs is not None:
        if any(hashlib.sha256(blobs[name]).hexdigest() != hashes[name] for name in SOURCES):
            raise ValueError('Producer hashes disagree with its recorded Git source')
        return {'status': 'matched_recorded_git_object', 'commit': commit,
                'producer_dirty': recorded.get('git_dirty')}
    paths = {name: source_root / 'research/week2_completion' / name for name in SOURCES}
    if all(p.is_file() for p in paths.values()) and all(file_hash(paths[n]) == hashes[n] for n in SOURCES):
        return {'status': 'matched_current_source_bytes', 'commit': commit,
                'note': 'Recorded Git object unavailable; current source contents match'}
    return {'status': 'unverified', 'commit': commit,
            'note': 'Neither recorded Git object nor matching current source is available'}


def load_calendar_records(run_dir, *, source_root=None):
    root = Path(run_dir)
    if (root / 'source_changed.json').exists():
        raise ValueError('Producer invalidated this run because its source changed')
    manifest_path = _inside(root, root / 'manifest.json')
    manifest = read_json(manifest_path)
    if manifest.get('schema_version') != 2 or type(manifest.get('schema_version')) is not int:
        raise ValueError('Calendar runner manifest schema_version must be 2')
    args = manifest['arguments']
    reps = _integer(args['reps'], 'reps', 1)
    seed0 = _integer(args['seed'], 'seed')
    n = _integer(args['n'], 'n', 2)
    folds = _integer(args['folds'], 'folds', 2)
    _integer(args['T'], 'T', 2)
    _integer(args['H'], 'H', 1)
    _integer(args['K'], 'K')
    if not 0 <= finite(args['density']) <= 1 or args['H'] > args['T']:
        raise ValueError('Invalid density or window')
    if folds > n:
        raise ValueError('Too many folds')
    gammas, taus = args['gamma_values'], args['tau_values']
    for values in (gammas, taus):
        if not isinstance(values, list) or not values or len(set(values)) != len(values):
            raise ValueError('Gamma/tau lists must be nonempty and unique')
        for value in values:
            finite(value)
    scenarios, coordinates = [], {}
    for gamma in gammas:
        for tau in taus:
            name = f'gamma{gamma:g}_tau{tau:g}'
            if name in {s['id'] for s in scenarios}:
                raise ValueError('Scenario directory names collide after numeric formatting')
            scenarios.append({'id': name, 'truth': tau, 'replication_ids': list(range(reps)), 'role': 'primary'})
            coordinates[name] = (gamma, tau)
    plan = {'schema_version': 1, 'evidence_kind': 'simulation', 'failure_policy': 'report',
            'confidence_level': .95, 'scenarios': scenarios,
            'design_status': 'Exploratory producer manifest; no scientific approval inferred'}
    source = source_check(manifest['provenance'], source_root or Path(__file__).resolve().parents[2])
    paths, rows, attempts, diagnostics = [manifest_path], [], {}, []
    for scenario in scenarios:
        name = scenario['id']
        directory = _inside(root, root / name)
        files = sorted(directory.glob('rep_*.json'))
        if not directory.exists():
            continue
        cfg_path = _inside(root, directory / 'config.json')
        saved = read_json(cfg_path)
        cfg = saved['config']
        expected = {'n': n, 'T': args['T'], 'H': args['H'], 'n_regimes': args['K'],
                    'density': args['density'], 'gamma': coordinates[name][0],
                    'tau': scenario['truth'], 'seed': seed0}
        if (saved.get('reps') != reps or saved.get('folds') != folds or saved.get('seed0') != seed0
                or any(cfg.get(k) != v or isinstance(cfg.get(k), bool) for k, v in expected.items())):
            raise ValueError('Scenario configuration differs from manifest')
        paths.append(cfg_path)
        for path in files:
            _inside(root, path)
            record = read_json(path)
            r = _integer(record.get('replication'), 'replication')
            if r >= reps or path.name != f'rep_{r:06d}.json':
                raise ValueError('Unplanned replication or filename/ID mismatch')
            seed = seed0 + r
            estimator = {'n_folds': folds, 'seed': seed, 'learner': 'RandomForestRegressor',
                         'n_estimators': 40, 'min_samples_leaf': 8, 'max_features': .5, 'n_jobs': 1}
            streams = {k: {'entropy': seed, 'spawn_key': [i]} for i, k in enumerate(STREAMS)}
            if (type(record.get('schema_version')) is not int or record['schema_version'] != 1
                    or type(record.get('seed')) is not int or record['seed'] != seed
                    or not _same_json(record.get('config'), {**cfg, 'seed': seed})
                    or not _same_json(record.get('estimator'), estimator)
                    or not _same_json(record.get('rng_streams'), streams)
                    or finite(record.get('confidence_level')) != .95):
                raise ValueError('Replication configuration/seed/stream/estimator mismatch')
            cells = record.get('cells')
            keys = [('random', 'naive'), ('random', 'multiway'), ('grouped', 'naive'), ('grouped', 'multiway')]
            if (not isinstance(cells, list) or len(cells) != 4 or
                    sorted((c.get('folds', ''), c.get('variance', '')) for c in cells) != sorted(keys)):
                raise ValueError('Attempt must contain exactly four expected cells')
            fold_ids = {}
            for cell in cells:
                ids = cell.get('fold_ids')
                if ids is not None:
                    if (not isinstance(ids, list) or len(ids) != n or
                            any(type(i) is not int or not 0 <= i < folds for i in ids) or len(set(ids)) != folds):
                        raise ValueError('Malformed fold assignment')
                    if cell['folds'] in fold_ids and fold_ids[cell['folds']] != ids:
                        raise ValueError('Variance cells use different fold assignments')
                    fold_ids[cell['folds']] = ids
                status = cell.get('status')
                if status == 'ok' and ids is None:
                    raise ValueError('Successful cell lacks fold assignment')
                variance = 'naive' if cell['variance'] == 'naive' else 'robust'
                rows.append({'scenario': name, 'replication': str(r),
                    'cell': f"{cell['folds']}_xfit__{variance}_var", 'panel_id': f'{name}:seed{seed}',
                    'truth': scenario['truth'], 'confidence_level': .95, 'status': status,
                    'estimate': cell.get('tau'), 'lower': cell.get('lo'), 'upper': cell.get('hi'),
                    'error': cell.get('error'), 'seconds': record.get('runtime_by_scheme', {}).get(cell['folds'])})
            attempts[name, r] = record
            diagnostics.append({'scenario': name, 'replication': r,
                'numeric': record.get('numeric_diagnostics'),
                'folds': {c['folds']: c.get('fold_diagnostics') for c in cells}})
            paths.append(path)
    return rows, plan, {'manifest': manifest, 'source_check': source,
        'producer_diagnostics': diagnostics, 'diagnostic_scope': 'Saved producer claims; not independently replayed'}, paths, attempts


def audit_calendar_run(run_dir, *, source_root=None):
    rows, plan, metadata, paths, attempts = load_calendar_records(run_dir, source_root=source_root)
    report = audit_results(rows, plan)
    summary_name = Path(metadata['manifest']['arguments']['out']).name
    summary_path = _inside(Path(run_dir), Path(run_dir) / summary_name)
    claims, inconsistencies = [], []
    if summary_path.exists():
        saved = read_json(summary_path)
        if saved.get('provenance') != metadata['manifest']['provenance'] or saved.get('schema_version') != 2:
            raise ValueError('Summary provenance differs from manifest')
        known = {s['id'] for s in plan['scenarios']}
        seen = set()
        for run in saved['runs']:
            name = f"gamma{run['gamma']:g}_tau{run['tau']:g}"
            if name not in known or name in seen:
                raise ValueError('Unplanned or duplicate summary scenario')
            seen.add(name)
            inline = run.get('attempts', [])
            for record in inline:
                r = _integer(record.get('replication'), 'inline replication')
                if attempts.get((name, r)) != record:
                    inconsistencies.append({'scenario': name, 'replication': r,
                                            'reason': 'Inline attempt differs from/missing authoritative raw file'})
            for key, values in run['results'].items():
                fold, variance = key.split('/')
                if fold not in ('random', 'grouped') or variance not in ('naive', 'multiway'):
                    raise ValueError('Unexpected claimed cell')
                claims.append({'scenario': name,
                    'cell': f"{fold}_xfit__{'naive' if variance == 'naive' else 'robust'}_var",
                    'planned': run['reps_requested'], 'missing': 0,
                    **{target: values[source] for source, target in ALIASES.items() if source in values}})
        paths.append(summary_path)
    report.update(claimed_summaries=compare_claims(report, claims),
        inline_attempt_inconsistencies=inconsistencies, stability=audit_stability(rows),
        producer=metadata, open_items=[
            'Team Gate 2/3 design, scientific variance choice and robustness subset remain unapproved.',
            'Producer numeric and fold diagnostics require source/data replay for independent verification.',
            'Regime-only folds/covariance omit possible shared-calendar-factor links.',
            'No labelled daily-return dataset was supplied; no real-data inference is claimed.'])
    report['provenance'] = provenance(paths, extra_sources=[__file__])
    return report, rows, plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--producer-source', type=Path)
    args = parser.parse_args(argv)
    report, rows, plan = audit_calendar_run(args.run_dir, source_root=args.producer_source)
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'plan.json', plan)
    fields = ['scenario', 'replication', 'cell', 'panel_id', 'truth', 'confidence_level',
              'status', 'estimate', 'lower', 'upper', 'error', 'seconds']
    with (args.output / 'intervals.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report['verifier_source_archive'] = save_source_snapshot(args.output, report['provenance'], extra_sources=[__file__])
    write_json(args.output / 'audit.json', report)
    (args.output / 'audit.md').write_text(markdown_report(report), encoding='utf-8')
    return 0 if (report['all_records_successful'] and report['claimed_summaries']['status'] == 'matched'
                 and not report['inline_attempt_inconsistencies'] and
                 report['producer']['source_check']['status'] != 'unverified') else 2


if __name__ == '__main__':
    raise SystemExit(main())
