"""Verify structural metrics against the actual generator and full covariance."""
import numpy as np
from research.final_validation.structure import structural_world
from research.week2_completion.dgp import Config,build_world


def test_membership_pair_count_and_exposure_match_actual_calendar_generator():
    cfg=Config(n=80,T=60,H=5,n_regimes=16,density=.5,seed=810123,sd_factor=0.)
    w=build_world(cfg);r=structural_world(cfg.seed,cfg.n,cfg.n_regimes,cfg.density,cfg.T,cfg.H)
    pairs=sum(bool(set(a)&set(b)) for i,a in enumerate(w['cluster_memberships']) for b in w['cluster_memberships'][i+1:])
    assert r['shared_pairs']==pairs
    assert r['exposed_share']==np.mean(w['exposed'])


def test_analytical_mean_correlation_matches_explicit_full_covariance():
    cfg=Config(n=30,T=60,H=5,n_regimes=4,density=.5,seed=810126,sd_factor=0.)
    w=build_world(cfg);r=structural_world(cfg.seed,cfg.n,cfg.n_regimes,cfg.density,cfg.T,cfg.H)
    load=np.array([[(w['rid_t'][ix]==g).sum() for g in range(4)] for ix in w['idx']])
    covariance=.4**2*(load@load.T)+5*np.eye(30)
    correlation=covariance/np.sqrt(np.outer(np.diag(covariance),np.diag(covariance)))
    expected=correlation[np.triu_indices(30,1)].mean()
    np.testing.assert_allclose(r['average_common_shock_correlation'],expected,rtol=1e-12)
