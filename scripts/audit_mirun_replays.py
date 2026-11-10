"""Audit reviewer reconstructions, preserving discrepancies with published pilots.

Inputs are the immutable-source reconstructions produced by the companion replay
script. Repeated worlds reused across tables are not independent new samples.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.verification import audit_results, file_hash, read_csv, REQUIRED_COLUMNS
from src.evaluation.week3_audit import markdown_report, provenance, read_json, save_source_snapshot, write_json


def _compare(actual, claimed, label):
    rows = []
    for field, value in claimed.items():
        if field not in actual:
            continue
        other = actual[field]
        matched = other is None and value is None
        if other is not None and value is not None:
            matched = math.isclose(other, value, abs_tol=1e-12, rel_tol=1e-10)
        rows.append({**label, 'field': field, 'claimed': value, 'recomputed': other,
                     'absolute_delta': abs(value - other) if other is not None and value is not None else None,
                     'matched': matched})
    return rows


def audit_replays(calendar_dir, legacy_dir):
    calendar_dir, legacy_dir = Path(calendar_dir), Path(legacy_dir)
    paths = [calendar_dir / n for n in ('plan.json', 'raw_intervals.csv', 'execution_manifest.json', 'source_snapshot.tar')]
    manifest = read_json(calendar_dir / 'execution_manifest.json')
    replay_plan = read_json(legacy_dir / 'replay_plan.json')
    if (manifest['source_commit'] != replay_plan['source_commit'] or
            manifest['source_archive_sha256'] != file_hash(calendar_dir / 'source_snapshot.tar') or
            replay_plan['source_archive_sha256'] != manifest['source_archive_sha256']):
        raise ValueError('Replay source identities disagree')
    rows = read_csv(calendar_dir / 'raw_intervals.csv', REQUIRED_COLUMNS)
    plan = read_json(calendar_dir / 'plan.json')
    comparisons = []
    original = calendar_dir / 'source/results/week2_mc.json'
    claims = read_json(original)
    paths += [original, legacy_dir / 'replay_plan.json']
    calendar_report = audit_results(rows, plan)
    index = {(s['scenario'], s['cell']): s for s in calendar_report['summaries']}
    for run in claims['runs']:
        scenario = f"gamma{run['gamma']:g}_tau{run['tau']:g}"
        for key, claimed in run['results'].items():
            fold, var = key.split('/')
            cell = f"{fold}_xfit__{'naive' if var == 'naive' else 'robust'}_var"
            summary = index[scenario, cell]
            aliases = {'successful_reps': 'valid', 'coverage': 'coverage95', 'mc_se_coverage': 'coverage_mcse',
                       'bias': 'bias', 'rmse': 'rmse', 'mean_interval_width': 'mean_ci_width',
                       'empirical_size': 'empirical_size', 'mc_se_size': 'size_mcse'}
            actual = {k: summary[v] for k, v in aliases.items()}
            comparisons.extend(_compare(actual, claimed, {'variant': 'full_membership_overlap',
                'artifact': 'week2_mc.json', 'scenario': scenario, 'cell': cell}))
    legacy_rows, scenarios, unique = [], [], set()
    for target in replay_plan['targets']:
        name = target['artifact'] + ':' + target['scenario']
        truth = target['config'].get('tau', 1.)
        scenarios.append({'id': name, 'truth': truth, 'role': 'primary',
                          'replication_ids': list(range(target['reps']))})
        if len(target['keys']) != target['reps'] or len(set(target['keys'])) != target['reps']:
            raise ValueError('Invalid legacy attempt plan')
        by_cell = {}
        for r, key in enumerate(target['keys']):
            path = legacy_dir / 'attempts' / (key + '.json')
            attempt = read_json(path)
            if attempt['config']['seed'] != 10000 + r or any(attempt['config'][k] != v for k, v in target['config'].items()):
                raise ValueError('Legacy replay config/seed mismatch')
            unique.add(key)
            paths.append(path)
            for cell in attempt['cells']:
                label = cell['folds'] + '/' + cell['variance']
                by_cell.setdefault(label, []).append(cell)
                legacy_rows.append({'scenario': name, 'replication': str(r),
                    'cell': f"{cell['folds']}_xfit__{cell['variance']}_var", 'panel_id': key,
                    'truth': truth, 'confidence_level': .95, 'status': cell['status'],
                    'estimate': cell['tau'], 'lower': cell['lo'], 'upper': cell['hi'], 'error': cell['error'],
                    'seconds': attempt['runtime_by_scheme'].get(cell['folds'])})
        # The archived legacy tables use the first-membership CR1 variant.
        for cell, claimed in target['claimed']['results'].items():
            valid = [c for c in by_cell[cell] if c['status'] == 'ok']
            if not valid:
                actual = {k: None for k in claimed}
            else:
                count = len(valid)
                coverage = sum(c['lo'] <= truth <= c['hi'] for c in valid) / count
                sd = statistics.stdev(c['tau'] for c in valid) if count > 1 else None
                mean_se = statistics.mean(c['se'] for c in valid)
                actual = {'coverage': coverage, 'mc_se_cov': math.sqrt(coverage * (1 - coverage) / count),
                    'bias': statistics.mean(c['tau'] - truth for c in valid),
                    'width': statistics.mean(c['hi'] - c['lo'] for c in valid),
                    'sd_tau': sd, 'mean_se': mean_se, 'se_to_sd_ratio': mean_se / sd if sd else None}
            comparisons.extend(_compare(actual, claimed, {'variant': 'legacy_first_membership_cr1',
                'artifact': target['artifact'], 'scenario': target['scenario'], 'cell': cell}))
    legacy_plan = {**plan, 'scenarios': scenarios}
    legacy_report = audit_results(legacy_rows, legacy_plan)
    failures = [c for c in comparisons if not c['matched']]
    return {'calendar': calendar_report, 'legacy': legacy_report, 'comparisons': comparisons,
        'comparison_summary': {'numeric_fields_checked': len(comparisons), 'discrepancies': len(failures),
            'coverage_discrepancies': sum(c['field'] == 'coverage' for c in failures),
            'max_absolute_delta': max((c['absolute_delta'] or 0 for c in comparisons), default=0),
            'legacy_unique_worlds': len(unique), 'legacy_scenario_references': len(legacy_rows) // 4,
            'calendar_rows': len(rows), 'legacy_rows': len(legacy_rows)},
        'source_commit': manifest['source_commit'], 'reviewer_environment': replay_plan,
        'interpretation': 'Reviewer reconstruction, not the missing original raw archive. Source/environment provenance cannot establish why archived continuous summaries differ. Variants are never pooled.',
        'original_reporting_gaps': ['No original per-replication archive/environment lock.',
            'Width and paired MCSEs absent from original tables; supplementary values are reconstructed.',
            'No approved design, robustness subset or daily-return panel supplied.'],
        'provenance': provenance(sorted(set(paths)), extra_sources=[__file__])}, legacy_rows, legacy_plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calendar-dir', type=Path, required=True)
    parser.add_argument('--legacy-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--summary', type=Path, help='Optional small reviewable table; raw evidence remains separate')
    args = parser.parse_args(argv)
    report, rows, plan = audit_replays(args.calendar_dir, args.legacy_dir)
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'audit.json', report)
    write_json(args.output / 'legacy_plan.json', plan)
    with (args.output / 'legacy_intervals.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for variant in ('calendar', 'legacy'):
        (args.output / (variant + '.md')).write_text(markdown_report(report[variant]), encoding='utf-8')
    snapshot = save_source_snapshot(args.output, report['provenance'], extra_sources=[__file__])
    report['verifier_source_archive'] = snapshot
    write_json(args.output / 'audit.json', report)
    if args.summary:
        differences = [c for c in report['comparisons'] if not c['matched']]
        write_json(args.summary, {
            'evidence_kind': 'reviewer_reconstruction_of_exploratory_pilots',
            'source_commit': report['source_commit'], 'comparison_summary': report['comparison_summary'],
            'coverage_rates_checked': sum(c['field'] == 'coverage' for c in report['comparisons']),
            'discrepancies_by_field': {field: {'count': sum(c['field'] == field for c in differences),
                'max_absolute_delta': max(c['absolute_delta'] or 0 for c in differences if c['field'] == field)}
                for field in sorted({c['field'] for c in differences})},
            'reviewer_packages': report['reviewer_environment']['packages'],
            'calendar_summaries': report['calendar']['summaries'],
            'legacy_summaries': report['legacy']['summaries'],
            'central_paired_comparisons': {variant: [c for c in report[variant]['comparisons'] if c['central_comparison']]
                                         for variant in ('calendar', 'legacy')},
            'interpretation': report['interpretation'], 'original_reporting_gaps': report['original_reporting_gaps'],
            'full_audit_sha256': file_hash(args.output / 'audit.json'),
            'full_audit_location': str(args.output / 'audit.json')})
    print(json.dumps(report['comparison_summary'], indent=2))
    return 2 if report['comparison_summary']['discrepancies'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
