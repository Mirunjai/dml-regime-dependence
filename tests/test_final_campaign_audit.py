"""Adversarial end-to-end checks of final-campaign identities and intervals."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import pytest
from research.final_validation.campaign import main as produce
from scripts.audit_final_campaign import audit

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def tiny(tmp_path):
    plan=json.loads((ROOT/'configs/experiments/final-validation/final_design_20261112.json').read_text())
    plan['phase']='SOFTWARE_CHECK';plan['scenarios']=deepcopy(plan['scenarios'][:2]);plan['replications']=2
    for i,s in enumerate(plan['scenarios']):
        s['id']='fixture_'+str(i);s['config'].update(n=60,T=40);s['replications']=2;s['seed0']=850000
    plan_path=tmp_path/'plan.json';plan_path.write_text(json.dumps(plan))
    out=tmp_path/'run';produce(['--plan',str(plan_path),'--out',str(out),'--workers','1'])
    return plan_path,out

def rehash(out,p):
    c=out/'completion.json';r=json.loads(c.read_text());r['files_sha256'][str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest();c.write_text(json.dumps(r))

def test_small_actual_campaign_is_independently_auditable(tiny):
    plan,out=tiny;r,rows=audit(plan,[out],ROOT)
    assert r['saved_blocks']==r['complete_blocks']==4
    assert len(rows)==16
    assert r['primary']['all_planned_records_present']

def test_rehashed_wrong_seed_is_rejected(tiny):
    plan,out=tiny;p=next(out.glob('*/rep_*.json'));r=json.loads(p.read_text());r['seed']+=1;p.write_text(json.dumps(r));rehash(out,p)
    with pytest.raises(ValueError,match='seed mismatch'):audit(plan,[out],ROOT)

def test_rehashed_artificially_widened_interval_is_rejected(tiny):
    plan,out=tiny;p=next(out.glob('*/rep_*.json'));r=json.loads(p.read_text());c=r['cells'][0];c['lower']-=1.;c['upper']+=1.;p.write_text(json.dumps(r));rehash(out,p)
    with pytest.raises(ValueError,match='registered pivot'):audit(plan,[out],ROOT)
