"""Review regressions: data preservation, undefined diagnostics and toy arithmetic."""
import csv
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from src.benchmarks.event_study import market_model_event_study
from src.dgp.matched_density import pair_density
from src.dgp.regime_shocks import simulate_regimes
from src.dgp.week2_diagnostics import experiment
from src.real_data.sp500_schema import save_events, validate_event


def event():
    return dict(firm_id='TEST', ticker='TEST', company_name='Fixture',
                announcement_date='2024-09-06', effective_date='2024-09-23',
                event_type='addition', source_url='https://example.org/release')


def test_generator_rows_survive_validation(tmp_path):
    path = tmp_path / 'events.csv'
    save_events((event() for _ in range(1)), path)
    with path.open() as stream:
        assert list(csv.DictReader(stream)) == [event()]


@pytest.mark.parametrize('change', [
    {'company_name': ' '}, {'effective_date': '20240923'}, {'firm_id': True},
    {'source_url': 'https://'}, {'source_url': 'https://bad host/release'},
    {'announcement_date': '2024-09-24'}, {'unexpected': 'field'},
])
def test_invalid_event_never_truncates_prior_file(tmp_path, change):
    path = tmp_path / 'events.csv'
    path.write_text('valuable prior content')
    with pytest.raises(ValueError):
        save_events([{**event(), **change}], path)
    assert path.read_text() == 'valuable prior content'


def test_duplicate_rejected_and_write_failure_is_atomic(tmp_path, monkeypatch):
    path = tmp_path / 'events.csv'
    path.write_text('prior')
    with pytest.raises(ValueError, match='Duplicate'):
        save_events([event(), event()], path)
    def fail(*args, **kwargs):
        raise OSError('simulated interrupted CSV write')
    monkeypatch.setattr(csv.DictWriter, 'writerows', fail)
    with pytest.raises(OSError):
        save_events([event()], path)
    assert path.read_text() == 'prior'
    assert list(tmp_path.iterdir()) == [path]


def test_curated_event_list_schema():
    path = Path(__file__).resolve().parents[1] / 'data/processed/sp500_events_verified.csv'
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 7
    assert all(validate_event(row) for row in rows)


def test_pair_density_matches_direct_unordered_pair_count():
    ids = np.array([-1, -1, 0, 0, 0, 7, 7, 12])
    pairs = list(combinations(ids, 2))
    expected = sum(a == b and a >= 0 for a, b in pairs) / len(pairs)
    assert pair_density(ids) == expected
    assert pair_density([]) == 0 and pair_density([-1]) == 0


@pytest.mark.parametrize('ids', [[1.2, 1.2], [-2, 0], [True, False], [[1, 1]], [np.nan, 1]])
def test_malformed_pair_memberships_rejected(ids):
    with pytest.raises(ValueError):
        pair_density(ids)


@pytest.mark.parametrize('density', [0., 1.])
def test_constant_exposure_association_is_explicitly_undefined(density):
    density_result, association = experiment(density, 5, 42)
    assert association is None
    assert density_result == pytest.approx(0 if density == 0 else 5 * (200 * 199 / 2) / (1000 * 999 / 2))


@pytest.mark.parametrize('keyword,value', [('n_periods', True), ('n_regimes', True), ('density', True), ('density', [0.5])])
def test_regime_dimensions_and_density_are_not_booleans_or_arrays(keyword, value):
    params = dict(n_periods=10, n_regimes=2, density=.5, rng=np.random.default_rng(1))
    params[keyword] = value
    with pytest.raises(ValueError):
        simulate_regimes(**params)


@pytest.mark.parametrize('position,value', [(0, 70.), (1, 80.), (2, True)])
def test_event_indices_are_integer_boundaries(position, value):
    indices = [70, 80, 85]
    indices[position] = value
    market = np.linspace(-.02, .02, 100)
    with pytest.raises(ValueError, match='integers'):
        market_model_event_study(.001 + 1.5 * market, market, *indices)


def test_event_effect_does_not_leak_into_estimation():
    market = np.linspace(-.02, .02, 100)
    stock = .001 + 1.5 * market
    changed = stock.copy()
    changed[80:86] += .02
    before = market_model_event_study(stock, market, 70, 80, 85)
    after = market_model_event_study(changed, market, 70, 80, 85)
    assert before['alpha'] == after['alpha'] and before['beta'] == after['beta']
    assert after['car'] - before['car'] == pytest.approx(.12)


def test_unrepresentable_market_model_fails_explicitly():
    market = np.array([1e308, -1e308, 1e308, -1e308, 1e308])
    with pytest.raises(ValueError, match='representable'):
        market_model_event_study(market, market, 3, 3, 4)
