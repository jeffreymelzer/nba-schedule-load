"""
Strength-of-schedule metrics: opponent quality, rest, schedule density, time zones, altitude.
Opponent quality uses last season's results, so it measures the schedule as it looked before tip-off.
"""

from collections import defaultdict

import numpy as np

from modules.travel import city_key, is_back_to_back, local_day

ALTITUDE_CITIES = {'Denver, CO', 'Salt Lake City, UT'}

# metrics averaged (as z-scores, higher = harder) into the difficulty index
DIFFICULTY_METRICS = ['sos_vs_balanced', 'total_miles', 'flights', 'travel_back_to_backs', 'second_night_road_b2b',
                      'net_rest_edge', 'three_in_four', 'tz_hours_crossed', 'longest_homestand']
# net_rest_edge is games with a rest edge minus games at a rest disadvantage, and a long homestand is a long
# stretch without travel, so both count against difficulty when high
EASIER_WHEN_HIGHER = {'net_rest_edge', 'longest_homestand'}


def build_team_games(games, tz_lookup):
    """
    Return {team: [game dicts in date order]} with the opponent, venue and whether the game is the second
    night of a back-to-back (consecutive local calendar days after the team's previous game).
    """
    by_team = defaultdict(list)
    for game in sorted(games, key=lambda g: g['datetime']):
        by_team[game['home']].append({**game, 'team': game['home'], 'opp': game['away'], 'is_home': True})
        by_team[game['away']].append({**game, 'team': game['away'], 'opp': game['home'], 'is_home': False})

    for team_games in by_team.values():
        previous = None
        for game in team_games:
            current = (game['datetime'], game['city'], game['state'])
            game['back_to_back'] = previous is not None and is_back_to_back(previous, current, tz_lookup)
            previous = current

    return by_team


def build_back_to_back_lookup(by_team):
    """{(team, tip-off): True if that game was the team's second night of a back-to-back}."""
    return {(team, g['datetime']): g['back_to_back'] for team, team_games in by_team.items() for g in team_games}


def summarize_strength(team, team_games, opp_back_to_back, standings, tz_lookup):
    opp_win_pct = [standings[g['opp']]['win_pct'] for g in team_games]
    opp_net = [standings[g['opp']]['net_rating'] for g in team_games]

    # A team never plays itself, so a strong team's opponents are weaker on average by construction.
    # The balanced figure is the opponent average if the team faced every other team equally often.
    others = [v['win_pct'] for t, v in standings.items() if t != team]
    balanced_opp_win_pct = float(np.mean(others))

    rest_disadvantage = rest_advantage = 0
    for g in team_games:
        mine, theirs = g['back_to_back'], opp_back_to_back[(g['opp'], g['datetime'])]
        rest_disadvantage += mine and not theirs
        rest_advantage += theirs and not mine

    # distinct stretches of three games in four local days; overlapping stretches count once
    days = [local_day(g['datetime'], g['city'], g['state'], tz_lookup) for g in team_games]
    three_in_four, previous_end = 0, -1
    for start in range(len(days) - 2):
        if (days[start + 2] - days[start]).days <= 3:
            if start > previous_end:
                three_in_four += 1
            previous_end = start + 2

    tz_hours_crossed = flights = 0
    for a, b in zip(team_games, team_games[1:]):
        from_key, to_key = city_key(a['city'], a['state']), city_key(b['city'], b['state'])
        tz_hours_crossed += abs(tz_lookup[to_key] - tz_lookup[from_key])
        flights += from_key != to_key

    longest_road_trip = longest_homestand = road_run = home_run = 0
    for g in team_games:
        road_run = 0 if g['is_home'] else road_run + 1
        home_run = home_run + 1 if g['is_home'] else 0
        longest_road_trip = max(longest_road_trip, road_run)
        longest_homestand = max(longest_homestand, home_run)

    # second night of a back-to-back played away, and the harder case where the first night was away too
    second_night_road = both_nights_road = 0
    for a, b in zip(team_games, team_games[1:]):
        if b['back_to_back'] and not b['is_home']:
            second_night_road += 1
            both_nights_road += not a['is_home']

    return {
        'team': team,
        'sos_opp_win_pct': float(np.mean(opp_win_pct)),
        'sos_vs_balanced': float(np.mean(opp_win_pct)) - balanced_opp_win_pct,
        'sos_opp_net_rating': float(np.mean(opp_net)),
        'rest_disadvantage_games': int(rest_disadvantage),
        'rest_advantage_games': int(rest_advantage),
        'net_rest_edge': int(rest_advantage - rest_disadvantage),
        'three_in_four': int(three_in_four),
        'tz_hours_crossed': int(tz_hours_crossed),
        'flights': int(flights),
        'second_night_road_b2b': int(second_night_road),
        'both_nights_road_b2b': int(both_nights_road),
        'altitude_road_games': sum(1 for g in team_games
                                   if not g['is_home'] and city_key(g['city'], g['state']) in ALTITUDE_CITIES),
        'longest_road_trip': int(longest_road_trip),
        'longest_homestand': int(longest_homestand),
    }


def add_difficulty_index(rows):
    """Add 'difficulty_index' (mean z-score of DIFFICULTY_METRICS, higher = harder schedule) and its rank."""
    z_scores = []
    for metric in DIFFICULTY_METRICS:
        values = np.array([r[metric] for r in rows], dtype=float)
        spread = values.std()
        z = (values - values.mean()) / spread if spread else np.zeros(len(values))
        z_scores.append(-z if metric in EASIER_WHEN_HIGHER else z)

    index = np.mean(z_scores, axis=0)
    ranks = (-index).argsort().argsort() + 1
    for row, value, rank in zip(rows, index, ranks):
        row['difficulty_index'] = float(value)
        row['difficulty_rank'] = int(rank)

    return rows


def correlation(rows, x_key, y_key):
    """Pearson correlation between two columns of the team rows."""
    return float(np.corrcoef([r[x_key] for r in rows], [r[y_key] for r in rows])[0, 1])
