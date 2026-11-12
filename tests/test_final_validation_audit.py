"""Adversarial checks for the independent final exploratory-result auditor."""
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import pytest
from scripts.audit_final_validation import audit


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True))


def finish(directory):
    files={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in directory.rglob('*.json') if p.name!='completion.json'}
    save(directory/'completion.json', {'complete':True, 'blocks':len(list(directory.glob('*/rep_*.json'))), 'files_sha256':files})


@pytest.fixture
def run(tmp_path):
    spec=importlib.util.spec_from_file_location('tiny_final_driver', 'compute-tools/final-validation/validation_driver.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    plan=json.loads(Path('configs/experiments/final-review/exploratory_validation_20261112.json').read_text())
    plan['scenarios']=plan['scenarios'][:1];plan['replications']=2
    plan['scenarios'][0]['config'].update(n=80,T=60)
    p=tmp_path/'plan.json';save(p,plan);d=tmp_path/'raw';case=plan['scenarios'][0]
    sources={'validation_driver.py':hashlib.sha256(Path(driver.__file__).read_bytes()).hexdigest()}
    save(d/'manifest.json',{'plan':plan,'plan_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
          'selected_scenarios':[case['id']], 'source_sha256':sources, 'packages':{}})
    record=driver.run_one((case,0))
    assert all(c['status']=='ok' for c in record['cells'])
    for rep in range(2):
        r=record if rep==0 else driver.run_one((case,rep))
        save(d/case['id']/f'rep_{rep:06d}.json',r)
    finish(d)
    return p,d,case['id']


def test_counts_are_independently_recomputed(run):
    p,d,name=run;report,rows,_=audit(p,[d])
    assert report['all_records_successful'] and len(rows)==8
    assert all(s['covered']==round(s['coverage95']*2) for s in report['summaries'])
    assert all(c['complete_four_cell_blocks']==2 for c in report['complete_block_comparisons'])


def test_failed_naive_cell_excludes_full_block_but_not_valid_robust_marginal(run):
    p,d,name=run;f=d/name/'rep_000001.json';r=json.loads(f.read_text())
    r['cells'][0].update(status='failed',estimate=None,lower=None,upper=None,error='injected failure')
    save(f,r);finish(d);report,_,_=audit(p,[d])
    assert not report['all_records_successful']
    assert report['summaries'][1]['valid']==2
    assert all(c['complete_four_cell_blocks']==1 and c['excluded_blocks']==1 for c in report['complete_block_comparisons'])


def test_missing_attempt_stays_missing_in_denominators(run):
    p,d,name=run;(d/name/'rep_000001.json').unlink();finish(d)
    report,_,_=audit(p,[d])
    assert not report['all_planned_records_present']
    assert all(s['missing']==1 and s['planned']==2 for s in report['summaries'])


def test_raw_tampering_is_rejected_before_summaries(run):
    p,d,name=run;f=d/name/'rep_000000.json';f.write_text(f.read_text()+' ')
    with pytest.raises(ValueError,match='fingerprint mismatch'):audit(p,[d])


def test_tampered_seed_rejected_even_with_recomputed_file_hash(run):
    p,d,name=run;f=d/name/'rep_000000.json';r=json.loads(f.read_text());r['seed']+=1;save(f,r);finish(d)
    with pytest.raises(ValueError,match='identity mismatch'):audit(p,[d])


def test_wrong_source_version_rejected(run):
    p,d,name=run;f=d/'manifest.json';r=json.loads(f.read_text());r['source_sha256']['validation_driver.py']='0'*64;save(f,r);finish(d)
    with pytest.raises(ValueError,match='source fingerprint'):audit(p,[d])
