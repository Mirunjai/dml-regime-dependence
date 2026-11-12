"""S13 validation: one generated world, four outcomes, full-block pairing."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import json
import pytest
from src.infra import dml_engine as e


def test_one_world_generated_and_passed_once_to_four_cell_estimator(monkeypatch):
    cfg=e.load_proposal('configs/mirun_gate3.yaml');v=e.resolve_parameters(cfg,smoke=True);condition=e.make_conditions(cfg,v)[0]
    calls=[];original_build=e.build_world;original_dml=e.run_dml
    def build(config):
        data=original_build(config);calls.append(('build',id(data)));return data
    def fit(data,**kwargs):
        calls.append(('fit',id(data)));return original_dml(data,**kwargs)
    monkeypatch.setattr(e,'build_world',build);monkeypatch.setattr(e,'run_dml',fit)
    record=e.run_replication(cfg,v,condition,0,20261112,label='smoke_exploratory',overrides={'n':80,'T':60})
    assert calls==[('build',calls[0][1]),('fit',calls[0][1])]
    assert len(record['cells'])==4 and all(c['status']=='ok' for c in record['cells'])


def test_one_failed_cell_excludes_entire_block_from_paired_contrasts(tmp_path):
    cfg=e.load_proposal('configs/mirun_gate3.yaml');v=e.resolve_parameters(cfg,smoke=True);c=e.make_conditions(cfg,v)[0]
    d=tmp_path/'run';e.run_condition(cfg,c,d,3,1234,smoke=True,overrides={'n':80,'T':60})
    p=d/'rep_000000.json';r=json.loads(p.read_text());r['cells'][0].update(status='failed',error='deliberately failed naive variance',estimate=None,lower=None,upper=None)
    r["paired_block_status"]="incomplete"
    p.write_text(json.dumps(r));s=e.aggregate(d)
    assert s['paired_audit']['complete_blocks']==2 and s['paired_audit']['incomplete_blocks']==1
    assert s['paired']['grouped_robust_minus_random_robust']['valid_pairs']==2
    assert s['cells']['random_xfit__robust_var']['valid']==3


def test_frozen_validation_driver_matches_reference_exactly():
    path=Path('compute-tools/final-validation/validation_driver.py');spec=importlib.util.spec_from_file_location('ada_validation_test',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    plan=json.loads(Path('configs/experiments/final-review/exploratory_validation_20261112.json').read_text())
    case=deepcopy(plan['scenarios'][0]);case['config'].update(n=80,T=60)
    record=m.run_one((case,0));config=e.Config(**{**case['config'],'seed':case['seed0']})
    rows,_=e.run_dml(e.build_world(config),seed=config.seed)
    for actual,expected in zip(record['cells'],rows):
        assert actual['estimate']==expected['tau'] and actual['lower']==expected['lo'] and actual['upper']==expected['hi']
    assert len(record['world_sha256'])==64
