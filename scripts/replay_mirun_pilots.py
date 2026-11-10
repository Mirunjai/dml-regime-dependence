"""Reconstruct the already-published exploratory tables from pinned team source.

No new grid/budget is selected. Raw output is a reviewer reconstruction, never an
original archive or approved full run. Run the independent companion audit after
both variants finish. Requires NumPy, SciPy and scikit-learn.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
from importlib.metadata import version
import io
import json
import multiprocessing
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.week3_audit import write_json

REF = '26e65f109d1aea552169bb57cbae894e4ea65e8c'


def initialize(source):
    sys.path.insert(0, str(source))


def worker(job):
    variant, key, config = job
    if variant == 'calendar':
        from research.week2_completion.dgp import Config, build_world as simulate, STREAMS
        from research.week2_completion.dml import run_dml
    else:
        from research.week2_mirun.dgp import Config, simulate_dgp as simulate, STREAMS
        from research.week2_mirun.dml import run_dml
    started = time.perf_counter()
    cfg = Config(**config)
    try:
        cells, runtime = run_dml(simulate(cfg), n_folds=5, seed=cfg.seed)
        for cell in cells:
            cell.update(status='ok', error=None)
    except Exception as exc:
        cells = [dict(folds=f, variance=v, status='failed', error=repr(exc),
                      tau=None, se=None, lo=None, hi=None)
                 for f in ('random', 'grouped') for v in ('naive', 'multiway' if variant == 'calendar' else 'robust')]
        runtime = {}
    return key, {'config': config, 'cells': cells, 'runtime_by_scheme': runtime,
                 'total_seconds': time.perf_counter() - started,
                 'rng_streams': {name: {'entropy': cfg.seed, 'spawn_key': [i]} for i, name in enumerate(STREAMS)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-ref', default=REF)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    sha = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--verify', args.source_ref + '^{commit}'], text=True).strip()
    archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive', sha, 'research', 'requirements-week2.txt', 'results/week2_mc.json'])
    calendar = args.output / 'calendar'
    calendar.mkdir()
    (calendar / 'source_snapshot.tar').write_bytes(archive)
    source = calendar / 'source'
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter='data')
    initialize(source)
    from research.week2_completion.dgp import Config as CalendarConfig
    from research.week2_mirun.dgp import Config as LegacyConfig
    environment = {'source_commit': sha, 'source_archive_sha256': hashlib.sha256(archive).hexdigest(),
        'python': sys.version, 'platform': platform.platform(),
        'packages': {name: version(name) for name in ('numpy', 'scipy', 'scikit-learn')},
        'purpose': 'Reviewer reconstruction of published unapproved pilot tables',
        'replay_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    scenarios, jobs = [], []
    for gamma in (0., 1.):
        for tau in (1., 0.):
            name = f'gamma{gamma:g}_tau{tau:g}'
            scenarios.append({'id': name, 'truth': tau, 'replication_ids': list(range(20)), 'role': 'primary'})
            for r in range(20):
                jobs.append(('calendar', (name, r), asdict(CalendarConfig(gamma=gamma, tau=tau, seed=20000+r))))
    # These packages are intentionally isolated in fresh subprocesses so the
    # installed current research namespace cannot shadow the pinned archive.
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    import csv
    fields = ['scenario', 'replication', 'cell', 'panel_id', 'truth', 'confidence_level',
              'status', 'estimate', 'lower', 'upper', 'error', 'seconds']
    executions = []
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context('spawn'),
                             initializer=initialize, initargs=(source,)) as pool:
        with (calendar / 'raw_intervals.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for (name, r), attempt in pool.map(worker, jobs):
                cfg = attempt['config']
                for cell in attempt['cells']:
                    var = 'naive' if cell['variance'] == 'naive' else 'robust'
                    writer.writerow({'scenario': name, 'replication': r,
                        'cell': f"{cell['folds']}_xfit__{var}_var", 'panel_id': f"{name}-seed{cfg['seed']}",
                        'truth': cfg['tau'], 'confidence_level': .95, 'status': cell['status'],
                        'estimate': cell['tau'], 'lower': cell['lo'], 'upper': cell['hi'], 'error': cell['error'],
                        'seconds': attempt['runtime_by_scheme'].get(cell['folds'], attempt['total_seconds'])})
                stream.flush()
                executions.append({'scenario': name, 'replication': r, **attempt})
        plan = {'schema_version': 1, 'evidence_kind': 'simulation', 'failure_policy': 'report',
                'confidence_level': .95, 'scenarios': scenarios}
        write_json(calendar / 'plan.json', plan)
        write_json(calendar / 'execution_manifest.json', {**environment, 'executions': executions})
        legacy = args.output / 'legacy'
        (legacy / 'attempts').mkdir(parents=True)
        unique, targets = {}, []
        for filename in ('mc_gamma_ablation_200reps.json', 'mc_factor_ablation.json', 'mc_original_gamma1_pilot.json'):
            table = json.loads((source / 'research/week2_mirun/results' / filename).read_text())
            for name, claimed in table.items():
                if name == 'toy':
                    continue
                keys = []
                for r in range(claimed['reps']):
                    cfg = asdict(LegacyConfig(**claimed['config'], seed=10000+r))
                    key = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:20]
                    unique[key] = cfg
                    keys.append(key)
                targets.append({'artifact': filename, 'scenario': name, 'reps': claimed['reps'],
                                'keys': keys, 'config': claimed['config'], 'claimed': claimed})
        write_json(legacy / 'replay_plan.json', {**environment, 'targets': targets, 'unique_configs': len(unique)})
        for count, (key, attempt) in enumerate(pool.map(worker, [('legacy', k, v) for k, v in unique.items()]), 1):
            write_json(legacy / 'attempts' / (key + '.json'), attempt)
            if count % 50 == 0:
                print(f'{count}/{len(unique)} legacy worlds saved', flush=True)
    print(f'Reconstruction complete. Audit --calendar-dir {calendar} --legacy-dir {legacy}')


if __name__ == '__main__':
    main()
