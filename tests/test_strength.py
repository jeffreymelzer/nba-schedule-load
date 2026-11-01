from datetime import datetime, timedelta

import pytest

from modules.strength import (DIFFICULTY_METRICS, add_difficulty_index, build_back_to_back_lookup, build_team_games,
                              correlation, summarize_strength)
from modules.travel import build_tz_lookup

START = datetime(2026, 11, 1, 23)
STANDINGS = {
    'A': {'win_pct': 0.8, 'net_rating': 8.0},
    'B': {'win_pct': 0.5, 'net_rating': 0.0},
    'C': {'win_pct': 0.2, 'net_rating': -8.0},
}


def game(days, home, away, city='Boston', state='MA'):
    return {'datetime': START + timedelta(days=days), 'city': city, 'state': state, 'home': home, 'away': away}


def summarize(team, games):
    tz_lookup = build_tz_lookup('cities.csv')
    by_team = build_team_games(games, tz_lookup)
    return summarize_strength(team, by_team[team], build_back_to_back_lookup(by_team), STANDINGS, tz_lookup)


def test_rest_edge_counts_second_nights_against_a_rested_opponent():
    # A plays on days 0 and 1 (back-to-back); B and C were rested for those games except B on day 1
    games = [game(0, 'A', 'B'), game(1, 'C', 'A'), game(5, 'B', 'C')]
    stats = summarize('A', games)

    assert stats['rest_disadvantage_games'] == 1
    assert stats['rest_advantage_games'] == 0
    assert stats['net_rest_edge'] == -1


def test_back_to_back_is_consecutive_calendar_days_not_hours():
    # 7 pm Boston tip, then a 10 pm Boston tip the next night: 27 hours apart but still consecutive days
    games = [{'datetime': datetime(2026, 11, 2, 0), 'city': 'Boston', 'state': 'MA', 'home': 'A', 'away': 'B'},
             {'datetime': datetime(2026, 11, 3, 3), 'city': 'Boston', 'state': 'MA', 'home': 'A', 'away': 'C'}]
    tz_lookup = build_tz_lookup('cities.csv')

    assert build_team_games(games, tz_lookup)['A'][1]['back_to_back']


def test_three_in_four_counts_a_dense_stretch_once():
    # days 0, 1, 3 and 4 give two overlapping windows that count as one stretch
    games = [game(0, 'A', 'B'), game(1, 'C', 'A'), game(3, 'A', 'B'), game(4, 'B', 'A'), game(12, 'A', 'C')]
    assert summarize('A', games)['three_in_four'] == 1


def test_opponent_strength_is_measured_against_a_balanced_schedule():
    # A faces only C (0.2) while a balanced schedule would face B and C (average 0.35)
    stats = summarize('A', [game(0, 'A', 'C'), game(3, 'C', 'A')])
    assert stats['sos_opp_win_pct'] == pytest.approx(0.2)
    assert stats['sos_vs_balanced'] == pytest.approx(0.2 - 0.35)


def test_longest_road_trip_and_time_zones():
    games = [game(0, 'B', 'A'), game(2, 'C', 'A', 'Los Angeles', 'CA'), game(4, 'A', 'B', 'Boston', 'MA')]
    stats = summarize('A', games)

    assert stats['longest_road_trip'] == 2
    assert stats['longest_homestand'] == 1
    assert stats['tz_hours_crossed'] == 6
    assert stats['flights'] == 2


def test_second_night_on_the_road_and_both_nights():
    # away on days 0, 1 and 2: two back-to-backs with the second game away, both with the first game away too
    games = [game(0, 'B', 'A'), game(1, 'C', 'A', 'Chicago', 'IL'), game(2, 'B', 'A', 'Boston', 'MA'),
             game(6, 'A', 'B', 'Boston', 'MA')]
    stats = summarize('A', games)

    assert stats['second_night_road_b2b'] == 2
    assert stats['both_nights_road_b2b'] == 2


def test_home_second_night_is_not_a_road_back_to_back():
    games = [game(0, 'B', 'A'), game(1, 'A', 'C'), game(6, 'A', 'B')]
    stats = summarize('A', games)

    assert stats['second_night_road_b2b'] == 0
    assert stats['both_nights_road_b2b'] == 0


def test_difficulty_index_is_centered_and_ranked():
    rows = [{metric: v for metric in DIFFICULTY_METRICS} for v in (1, 2, 3)]
    add_difficulty_index(rows)

    assert sum(r['difficulty_index'] for r in rows) == pytest.approx(0)
    assert [r['difficulty_rank'] for r in rows] == [3, 2, 1]


def test_correlation():
    rows = [{'x': 1, 'y': 2}, {'x': 2, 'y': 4}, {'x': 3, 'y': 6}]
    assert correlation(rows, 'x', 'y') == pytest.approx(1)
