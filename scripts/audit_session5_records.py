"""Independent standard-library audit of reconstructed Session 5 control records.

Manifest/calibration and explicit planned count define expected work; summaries
never supply missing raw attempts. This does not grant scientific approval.
"""
import argparse
import csv
from pathlib import Path

from src.evaluation.verification import audit_results, file_hash
from src.evaluation.week3_audit import read_json, write_json, markdown_report, provenance, save_source_snapshot


def audit_controls(directory, planned):
    root = Path(directory)
    calibration = read_json(root/'calibration.json')
    paths, rows, scenarios = [root/'calibration.json'], [], []
    for name, config in calibration['configs'].items():
        truth = config['tau']
        scenarios.append(dict(id=name, truth=truth, role='primary', replication_ids=list(range(planned))))
        for path in sorted((root/name).glob('rep_*.json')):
            rec = read_json(path)
            rep = rec['rep']
            if type(rep) is not int or not 0 <= rep < planned or path.name != f'rep_{rep:05d}.json':
                raise ValueError('Unplanned replication or filename mismatch')
            if rec['condition'] != name or type(rec['seed']) is not int or rec['seed'] != 70000+rep:
                raise ValueError('Condition/seed mismatch')
            cells = rec['cells']
            expected = {(f,v) for f in ('random','grouped') for v in ('naive','multiway')}
            if len(cells) != 4 or {(c['folds'],c['variance']) for c in cells} != expected:
                raise ValueError('Expected four unique cells')
            for c in cells:
                rows.append(dict(scenario=name, replication=str(rep),
                    cell=f"{c['folds']}_xfit__{'naive' if c['variance']=='naive' else 'robust'}_var",
                    panel_id=f'{name}:{rec["seed"]}', truth=truth, confidence_level=.95,
                    status=c['status'], estimate=c['tau'], lower=c['lo'], upper=c['hi'], error=c['error']))
            paths.append(path)
    plan=dict(schema_version=1,evidence_kind='simulation',failure_policy='report',confidence_level=.95,
              scenarios=scenarios,design_status='Reviewer engineering reconstruction; not approved robustness campaign')
    report=audit_results(rows,plan)
    report['provenance']=provenance(paths,extra_sources=[__file__])
    report['scope']='Fresh reviewer reconstruction; original 200-rep control archive was not supplied. tau=1 rejection is power, not size.'
    return report,rows,plan


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controls',type=Path,required=True)
    p.add_argument('--planned',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.planned < 1: p.error('planned must be positive')
    report,rows,plan=audit_controls(a.controls,a.planned)
    a.output.mkdir(parents=True,exist_ok=False)
    write_json(a.output/'plan.json',plan)
    with (a.output/'intervals.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report['verifier_source_archive']=save_source_snapshot(a.output,report['provenance'],extra_sources=[__file__])
    write_json(a.output/'audit.json',report)
    (a.output/'audit.md').write_text(markdown_report(report))
    print({'rows':len(rows),'complete':report['all_records_successful']})
    return 0 if report['all_records_successful'] else 2

if __name__=='__main__':
    raise SystemExit(main())
