"""Independent matrix identities, not empirical evidence of DML calibration."""
import numpy as np
import pytest

from research.final_validation.inference import component_cr2


def dense_reference(y,x,memberships):
    from research.week2_completion.dml import _components
    labels = _components(memberships)
    J=x@x; theta=x@y/J; e=y-x*theta
    M=np.eye(len(x))-np.outer(x,x)/J
    directions=[]; scores=[]
    for g in np.unique(labels):
        ix=np.flatnonzero(labels==g); H=np.outer(x[ix],x[ix])/J
        eigen, vectors=np.linalg.eigh(np.eye(len(ix))-H)
        A=(vectors/np.sqrt(eigen))@vectors.T
        direction=np.zeros(len(x));direction[ix]=A@x[ix]
        directions.append(M@direction)
        scores.append(x[ix]@A@e[ix])
    Q=np.array(directions).T@np.array(directions)
    return np.sqrt(np.sum(np.array(scores)**2))/J, np.trace(Q)**2/np.trace(Q@Q)


def test_scalar_formula_matches_dense_adjustment_and_quadratic_form():
    rng=np.random.default_rng(782)
    x=rng.normal(size=25);y=.7*x+rng.normal(size=25)
    membership=[(0,)]*5+[(1,)]*9+[()] *11
    actual=component_cr2(y,x,membership);se,df=dense_reference(y,x,membership)
    np.testing.assert_allclose([actual['se'],actual['df']],[se,df],rtol=1e-12)


def test_balanced_intercept_only_regression_reduces_to_t_G_minus_one():
    rng=np.random.default_rng(19);x=np.ones(40);y=rng.normal(size=40)
    m=[(g,) for g in range(4) for _ in range(10)]
    actual=component_cr2(y,x,m)
    assert actual['df']==pytest.approx(3.)
    means=y.reshape(4,10).mean(axis=1)
    assert actual['se']==pytest.approx(means.std(ddof=1)/2)


def test_one_cluster_or_constant_treatment_information_is_explicitly_undefined():
    with pytest.raises(ValueError,match='two informative'):
        component_cr2(np.arange(8.),np.ones(8),[(0,)]*8)
    with pytest.raises(ValueError,match='information'):
        component_cr2(np.arange(8.),np.zeros(8),[()]*8)


def test_overlapping_memberships_are_clustered_by_full_connected_component():
    x=np.arange(1.,13);y=np.sin(x)
    m=[(0,),(0,1),(1,),(),(2,),(2,),(),(),(),(),(),()]
    actual=component_cr2(y,x,m)
    assert actual['informative_clusters']==9
    se,df=dense_reference(y,x,m)
    np.testing.assert_allclose([actual['se'],actual['df']],[se,df])
