"""Synthetic-structure checks for the diagnostic fold variants (not DML results)."""
import numpy as np
from dataclasses import replace
from research.week2_completion.dgp import Config, build_world
from scripts.mirun_fold_variance_diagnostics import leakage, overlap_matrix
from scripts.mirun_grouped_spread_mechanism import fold_sets


def test_variants_have_expected_structure():
    data = build_world(replace(Config(), n_regimes=4, density=.5, gamma=1., seed=30000))
    rf, gf, smf, gpf = fold_sets(data, 30000)
    reg = overlap_matrix(data["cluster_memberships"]) > 0
    np.fill_diagonal(reg, False)
    assert leakage(reg, gf)[0] == 0                                  # real grouped: no regime leakage
    assert leakage(reg, gpf)[0] > 0                                   # pseudo-blocks ignore the real regimes
    assert np.array_equal(np.bincount(smf, minlength=5), np.bincount(gf, minlength=5))  # sizes matched
    assert leakage(reg, smf)[0] > 0
