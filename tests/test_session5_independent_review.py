import json
import pytest
from scripts.audit_session5_records import audit_controls
from src.real_data.panel_contract import validate_panel_contract


def test_control_audit_accounts_for_missing_rows_and_rejects_seed_tampering(tmp_path):
    (tmp_path/'calibration.json').write_text(json.dumps({'configs':{'fixture':{'tau':1.}}}))
    (tmp_path/'fixture').mkdir()
    record={'rep':0,'seed':70000,'condition':'fixture','cells':[
        dict(folds=f,variance=v,status='ok',tau=1.,lo=0.,hi=2.,error=None)
        for f in ('random','grouped') for v in ('naive','multiway')]}
    path=tmp_path/'fixture/rep_00000.json';path.write_text(json.dumps(record))
    report,_,_=audit_controls(tmp_path,2)
    assert all(s['missing']==1 and s['valid']==1 and s['coverage95']==1 for s in report['summaries'])
    record['seed']=70001;path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='seed'):
        audit_controls(tmp_path,2)


def test_panel_boolean_return_is_not_accepted():
    report=validate_panel_contract([dict(date='2024-01-02',firm_id='x',value=True,regime='calm')],[],
        value_kind='return',label_source='fixture',window_days=1,min_nonmissing_share=1.,evidence_kind='synthetic_fixture')
    assert any('boolean' in e for e in report['errors'])
