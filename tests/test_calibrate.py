import numpy as np
import pytest

from modules.calibrate import carryover, fit_effects, shrink_effects
from modules.context import FEATURES, build_game_contexts
from modules.expected_wins import schedule_load
from modules.schedule_scraper import ScheduleScraper
from modules.travel import build_city_lookup, build_tz_lookup

TRUE_HOME_COURT = 2.0
TRUE_EFFECTS = {'b2b': -2.0, 'b2b_road': 0.0, 'long_rest': 0.0, 'miles_k': -0.3, 'tz_east': -0.5, 'tz_west': 0.0,
                'three_in_four': -0.5, 'altitude_visit': -1.0}


@pytest.fixture(scope='module')
def schedule():
    scraper = ScheduleScraper('data/schedule_2026_27.json')
    scraper.run()
    return scraper.games, build_city_lookup('cities.csv'), build_tz_lookup('cities.csv')


def simulate(games, city_lookup, tz_lookup, seed=0, noise=1.0, home_court=TRUE_HOME_COURT):
    """Give the real schedule margins generated from known strengths and effects, plus a little noise."""
    rng = np.random.default_rng(seed)
    teams = sorted({g['home'] for g in games})
    strength = dict(zip(teams, rng.normal(0, 5, len(teams))))
    simulated = []
    for context in build_game_contexts(games, city_lookup, tz_lookup):
        game = context['game']
        margin = (0 if game['neutral'] else home_court) + strength[game['home']] - strength[game['away']]
        margin += sum(TRUE_EFFECTS[f] * (context['home'][f] - context['away'][f]) for f in FEATURES)
        margin += rng.normal(0, noise)
        simulated.append({**game, 'home_score': 100 + margin, 'away_score': 100})

    return simulated, strength


def test_fit_recovers_known_effects(schedule):
    games, city_lookup, tz_lookup = schedule
    simulated, strength = simulate(games, city_lookup, tz_lookup)
    fit = fit_effects({2027: simulated}, city_lookup, tz_lookup)

    assert fit['home_court'][0] == pytest.approx(TRUE_HOME_COURT, abs=0.2)
    for name, truth in TRUE_EFFECTS.items():
        assert fit['effects'][name][0] == pytest.approx(truth, abs=0.3), name
    mean = np.mean(list(strength.values()))
    for team, truth in strength.items():
        assert fit['ratings'][(2027, team)] == pytest.approx(truth - mean, abs=0.5)


def test_home_court_average_can_leave_a_season_out(schedule):
    games, city_lookup, tz_lookup = schedule
    normal, _ = simulate(games, city_lookup, tz_lookup, seed=1, home_court=3.0)
    empty_arenas, _ = simulate(games, city_lookup, tz_lookup, seed=2, home_court=0.0)
    seasons = {2020: normal, 2021: empty_arenas}

    everything = fit_effects(seasons, city_lookup, tz_lookup)
    without = fit_effects(seasons, city_lookup, tz_lookup, home_court_exclude=(2021,))

    assert everything['home_court'][0] == pytest.approx(1.5, abs=0.3)
    assert without['home_court'][0] == pytest.approx(3.0, abs=0.3)
    assert without['home_court_by_season'][2021][0] == pytest.approx(0.0, abs=0.3)


def test_shrinkage_pulls_noisy_estimates_further_than_clear_ones():
    shrunk, spread = shrink_effects({'clear': (-3.0, 0.3), 'noisy': (-3.0, 3.0), 'null': (0.1, 0.5)})

    assert abs(shrunk['clear'][0]) > abs(shrunk['noisy'][0])
    assert abs(shrunk['clear'][0]) < 3.0
    assert spread > 0


def test_carryover_is_the_slope_through_the_origin():
    ratings = {(1, 'a'): 10.0, (1, 'b'): -10.0, (2, 'a'): 5.0, (2, 'b'): -5.0}
    assert carryover(ratings, [1, 2]) == pytest.approx(0.5)


def test_schedule_with_no_effects_and_equal_teams_has_no_load(schedule):
    games, city_lookup, tz_lookup = schedule
    teams = sorted({g['home'] for g in games})
    fit = {'ratings': {(2026, t): 0.0 for t in teams}, 'sigma': 13.0, 'home_court': (0.0, 0.0),
           'effects': {f: (0.0, 0.0) for f in FEATURES}}
    rows = schedule_load(games, fit, 1.0, 2026, city_lookup, tz_lookup, draws=5)

    assert all(r['load_wins'] == pytest.approx(0) for r in rows)


def test_a_team_facing_stronger_opponents_has_more_load(schedule):
    games, city_lookup, tz_lookup = schedule
    teams = sorted({g['home'] for g in games})
    ratings = {(2026, t): (8.0 if t == 'Boston Celtics' else 0.0) for t in teams}
    fit = {'ratings': ratings, 'sigma': 13.0, 'home_court': (0.0, 0.0), 'effects': {f: (0.0, 0.0) for f in FEATURES}}
    rows = {r['team']: r for r in schedule_load(games, fit, 1.0, 2026, city_lookup, tz_lookup, draws=5)}

    # every team except Boston plays Boston a few times, so everyone else carries load and Boston carries none
    assert rows['Boston Celtics']['load_wins'] == pytest.approx(0)
    assert rows['New York Knicks']['load_wins'] > 0.1
