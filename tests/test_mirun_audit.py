"""Independent adapter contracts: omitted work, corrupt provenance, failed CIs."""
from dataclasses import asdict
import json

import pytest

from research.week2_completion.dgp import Config
from src.evaluation.mirun_audit import audit_calendar_run, load_calendar_records
from src.evaluation.week3_audit import write_json


@pytest.fixture
def saved_run(tmp_path):
    root = tmp_path / 'producer'
    root.mkdir()
    cfg = asdict(Config(n=10, T=20, H=2, gamma=0., tau=0., seed=7))
    provenance = {'git_commit': 'a' * 40, 'git_dirty': False,
                  'source_sha256': {name: 'b' * 64 for name in
                                    ('__init__.py', 'dgp.py', 'dml.py', 'run_week2.py', 'validation.py')}}
    write_json(root / 'manifest.json', {'schema_version': 2, 'provenance': provenance,
        'arguments': {'n': 10, 'T': 20, 'H': 2, 'K': 4, 'density': .5, 'folds': 2,
                      'reps': 2, 'seed': 7, 'gamma_values': [0.], 'tau_values': [0.], 'out': '/old/path/run.json'}})
    d = root / 'gamma0_tau0'
    d.mkdir()
    write_json(d / 'config.json', {'config': cfg, 'reps': 2, 'folds': 2, 'seed0': 7})
    for r in range(2):
        seed = 7 + r
        cells = [dict(folds=f, variance=v, status='ok', tau=0., se=1., lo=-1., hi=1.,
                      error=None, fold_ids=[0, 1] * 5, fold_diagnostics={})
                 for f in ('random', 'grouped') for v in ('naive', 'multiway')]
        write_json(d / f'rep_{r:06d}.json', {'schema_version': 1, 'replication': r, 'seed': seed,
            'config': {**cfg, 'seed': seed}, 'confidence_level': .95,
            'estimator': {'n_folds': 2, 'seed': seed, 'learner': 'RandomForestRegressor',
                          'n_estimators': 40, 'min_samples_leaf': 8, 'max_features': .5, 'n_jobs': 1},
            'rng_streams': {k: {'entropy': seed, 'spawn_key': [i]} for i, k in enumerate(
                ('cov', 'dates', 'vol', 'factor', 'layout', 'shock', 'regime_treat', 'treat', 'noise'))},
            'cells': cells, 'runtime_by_scheme': {'random': 1., 'grouped': 1.}})
    return root


def edit(path, change):
    data = json.loads(path.read_text())
    change(data)
    write_json(path, data)


def test_accounting_missing_summary_and_attempt(saved_run, tmp_path):
    report, rows, plan = audit_calendar_run(saved_run, source_root=tmp_path)
    assert len(rows) == 8 and report['all_records_successful']
    assert report['claimed_summaries']['status'] == 'discrepancies'
    assert report['producer']['source_check']['status'] == 'unverified'
    (saved_run / 'gamma0_tau0/rep_000001.json').unlink()
    report, _, _ = audit_calendar_run(saved_run, source_root=tmp_path)
    assert all(s['planned'] == 2 and s['missing'] == 1 for s in report['summaries'])


def test_entire_unfinished_scenario_is_planned(saved_run, tmp_path):
    edit(saved_run / 'manifest.json', lambda m: m['arguments']['gamma_values'].append(1.))
    report, _, _ = audit_calendar_run(saved_run, source_root=tmp_path)
    missing = [s for s in report['summaries'] if s['scenario'] == 'gamma1_tau0']
    assert len(missing) == 4 and all(s['missing'] == 2 for s in missing)


@pytest.mark.parametrize('change', [
    lambda r: r.update(seed=8),
    lambda r: r['config'].update(tau=1),
    lambda r: r['rng_streams']['cov'].update(spawn_key=[True]),
    lambda r: r['estimator'].update(n_jobs=True),
    lambda r: r['cells'].pop(),
    lambda r: r['cells'][0].update(fold_ids=[0] * 10),
    lambda r: r['cells'][0].update(fold_ids=None),
    lambda r: r['cells'][0].update(lo=2.),
])
def test_corrupt_records_rejected(saved_run, tmp_path, change):
    edit(saved_run / 'gamma0_tau0/rep_000000.json', change)
    with pytest.raises(ValueError):
        audit_calendar_run(saved_run, source_root=tmp_path)


def test_failed_robust_cell_keeps_naive(saved_run, tmp_path):
    def fail(r):
        r['cells'][1].update(status='failed', error='negative sandwich meat', lo=None, hi=None, se=None)
    edit(saved_run / 'gamma0_tau0/rep_000000.json', fail)
    report, _, _ = audit_calendar_run(saved_run, source_root=tmp_path)
    assert report['summaries'][0]['valid'] == 2
    assert report['summaries'][1]['valid'] == 1 and report['summaries'][1]['failed'] == 1
    assert report['summaries'][1]['coverage_lower_all_planned'] == .5


def test_source_invalidation_and_path_escape(saved_run, tmp_path):
    (saved_run / 'source_changed.json').write_text('{}')
    with pytest.raises(ValueError, match='invalidated'):
        load_calendar_records(saved_run)
    (saved_run / 'source_changed.json').unlink()
    path = saved_run / 'gamma0_tau0/rep_000000.json'
    external = tmp_path / 'external.json'
    external.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(external)
    with pytest.raises(ValueError, match='escapes'):
        load_calendar_records(saved_run)


def test_unrounded_gamma_preserved(saved_run, tmp_path):
    gamma = 1.23456789
    (saved_run / 'gamma0_tau0').rename(saved_run / 'gamma1.23457_tau0')
    edit(saved_run / 'manifest.json', lambda m: m['arguments'].update(gamma_values=[gamma]))
    edit(saved_run / 'gamma1.23457_tau0/config.json', lambda r: r['config'].update(gamma=gamma))
    for p in (saved_run / 'gamma1.23457_tau0').glob('rep_*.json'):
        edit(p, lambda r: r['config'].update(gamma=gamma))
    assert len(load_calendar_records(saved_run, source_root=tmp_path)[0]) == 8


def test_complete_claims_match_and_changed_claim_fails(saved_run, tmp_path):
    values = {'attempted_reps': 2, 'successful_reps': 2, 'failed_reps': 0,
              'coverage': 1., 'mc_se_coverage': 0., 'bias': 0., 'mc_se_bias': 0., 'rmse': 0.,
              'mean_interval_width': 2., 'mc_se_width': 0., 'empirical_size': 0., 'mc_se_size': 0.,
              'power': None, 'mc_se_power': None}
    manifest = json.loads((saved_run / 'manifest.json').read_text())
    attempts = [json.loads(p.read_text()) for p in sorted((saved_run / 'gamma0_tau0').glob('rep_*.json'))]
    write_json(saved_run / 'run.json', {'schema_version': 2, 'provenance': manifest['provenance'],
        'runs': [{'gamma': 0., 'tau': 0., 'reps_requested': 2, 'attempts': attempts,
                  'results': {f + '/' + v: dict(values) for f in ('random', 'grouped') for v in ('naive', 'multiway')}}]})
    assert audit_calendar_run(saved_run, source_root=tmp_path)[0]['claimed_summaries']['status'] == 'matched'
    edit(saved_run / 'run.json', lambda s: s['runs'][0]['results']['random/naive'].update(coverage=.5))
    report = audit_calendar_run(saved_run, source_root=tmp_path)[0]
    assert report['claimed_summaries']['discrepancies'][0]['field'] == 'coverage95'
    (saved_run / 'gamma0_tau0/rep_000001.json').unlink()
    assert audit_calendar_run(saved_run, source_root=tmp_path)[0]['inline_attempt_inconsistencies']


def test_calendar_monitor_snapshot_and_input_error(saved_run, tmp_path):
    from src.evaluation.monitor import main
    output = tmp_path / 'monitor'
    assert main(['--interval', '1', '--iterations', '1', '--producer', 'calendar',
                 '--output-root', str(output), '--', '--run-dir', str(saved_run)]) == 2
    assert (output / 'snapshot-000001/audit.json').is_file()
    (saved_run / 'source_changed.json').write_text('{}')
    output = tmp_path / 'monitor-invalid'
    assert main(['--interval', '1', '--producer', 'calendar', '--output-root', str(output),
                 '--', '--run-dir', str(saved_run)]) == 2
    assert (output / 'snapshot-000001/input_error.json').is_file()
