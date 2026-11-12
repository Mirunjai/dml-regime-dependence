import numpy as np
import pytest

from research.week2_completion.dgp import Config, build_world, simulate_calendar_regimes
from research.week2_completion.dml import _multiway_meat, _components, make_folds, estimate

def test_dgp_shapes_and_memberships():
    d=build_world(Config(n=80,T=100,H=5,p=5,density=.5,n_regimes=4,seed=11))
    assert d["Y"].shape==(80,)
    assert d["X"].shape==(80,5)
    assert len(d["cluster_memberships"])==80
    assert all(tuple(sorted(set(m)))==m for m in d["cluster_memberships"])
    assert np.isfinite(d["Y"]).all()

def test_gamma_ablation_keeps_exogenous_streams_fixed():
    a=build_world(Config(seed=8,gamma=0))
    b=build_world(Config(seed=8,gamma=1))
    for key in ("X","t0","U_t","rid_t","sig","z"):
        assert np.array_equal(a[key],b[key])
    # Treatment can change because gamma is the intended ablation.

def test_regime_layout_validates_and_exact_active_period_count():
    ids,U,shocks=simulate_calendar_regimes(100,.3,4,.4,np.random.default_rng(1),np.random.default_rng(2))
    assert np.sum(ids>=0)==30
    assert np.all(U[ids<0]==0)
    with pytest.raises(ValueError):
        simulate_calendar_regimes(100,1.2,4,.4,np.random.default_rng(1),np.random.default_rng(2))

def test_multiway_inclusion_exclusion_counts_pairs_sharing_any_regime_once():
    # Events 0 and 1 share regime 1; 1 and 2 share regime 2; 0 and 2 do not.
    psi=np.array([1.,2.,3.,4.])
    memberships=[(1,),(1,2),(2,),()]
    meat,_=_multiway_meat(psi,memberships)
    expected=(1+2)**2+(2+3)**2-(2)**2+4**2
    # S={1}: (1+2)^2; {2}: (2+3)^2; {1,2}: subtract event 1 squared.
    assert meat==pytest.approx(expected)

def test_dependence_graph_connected_components():
    labels=_components([(0,),(0,1),(1,),(2,),()])
    assert labels[0]==labels[1]==labels[2]
    assert labels[3]!=labels[0]
    assert labels[4]!=labels[3]

def test_grouped_folds_refuse_too_few_independent_components():
    memberships=[(0,),(0,1),(1,),(2,),(3,)]
    with pytest.raises(ValueError,match="independent dependence-graph components"):
        make_folds("grouped",memberships,4,np.random.default_rng(4))

def test_estimator_rejects_zero_residualized_treatment():
    with pytest.raises(ValueError,match="zero/near-zero"):
        estimate(np.arange(10.),np.zeros(10),[() for _ in range(10)])
