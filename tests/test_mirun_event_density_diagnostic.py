import pytest
from research.week2_completion.dgp import Config, build_world
from scripts.mirun_event_density_diagnostic import event_memberships, summarize_memberships

def test_mapping_matches_integrated_dgp_exactly():
    cfg=Config(n=40,T=60,H=5,p=5,density=.5,n_regimes=4,seed=12345)
    world=build_world(cfg)
    got=event_memberships(seed=cfg.seed,n=cfg.n,T=cfg.T,H=cfg.H,
        density=cfg.density,n_regimes=cfg.n_regimes,sd_shock=cfg.sd_shock)
    assert got == world["cluster_memberships"]

def test_zero_density_has_no_exposed_events_or_shared_pairs():
    r=summarize_memberships([tuple(),tuple(),tuple()],4)
    assert r["exposed_event_share"] == 0
    assert r["shared_regime_pair_density"] == 0
    assert r["multi_regime_event_share"] == 0

def test_one_cluster_has_pair_density_one():
    r=summarize_memberships([(0,),(0,),(0,),(0,)],1)
    assert r["exposed_event_share"] == 1
    assert r["shared_regime_pair_density"] == 1
    assert r["mean_regimes_per_event"] == 1

def test_multi_membership_pairs_are_not_double_counted():
    r=summarize_memberships([(0,),(0,1),(1,),tuple()],2)
    assert r["exposed_event_share"] == .75
    assert r["multi_regime_event_share"] == .25
    assert r["shared_regime_pair_density"] == pytest.approx(3/6)

def test_invalid_membership_id_is_rejected():
    with pytest.raises(ValueError):
        summarize_memberships([(0,),(2,)],2)
