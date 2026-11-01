"""
Schedule load in wins: how many wins a league-average team gives up to this schedule compared with a schedule of
average opponents on neutral terms. Every game's win probability comes from the point effects measured in
modules.calibrate; a positive number means a harder schedule.
"""

from math import erf, sqrt

import numpy as np

from modules.context import FEATURES, build_game_contexts

# situation features grouped into the components shown on the dashboard
COMPONENTS = {
    'rest': ['b2b', 'b2b_road', 'long_rest'],
    'travel': ['miles_k'],
    'timezone': ['tz_east', 'tz_west'],
    'density': ['three_in_four'],
    'altitude': ['altitude_visit'],
}
_erf = np.vectorize(erf)


def _win_probability(margin, sigma):
    return 0.5 * (1 + _erf(margin / (sigma * sqrt(2))))


def team_games_matrix(games, fit, carry, last_season, city_lookup, tz_lookup):
    """
    One record per team-game: team, opponent strength term, venue sign, and the feature gaps to the opponent.
    A team never plays itself, so opponent strength is measured against the average of the other teams: the term
    is the opponent's expected strength minus what an even spread over every other team would give.
    """
    expected = {team: carry * rating for (season, team), rating in fit['ratings'].items() if season == last_season}
    total = sum(expected.values())
    others_mean = {team: (total - strength) / (len(expected) - 1) for team, strength in expected.items()}

    teams, opp_terms, venue, gaps = [], [], [], []
    for context in build_game_contexts(games, city_lookup, tz_lookup):
        game = context['game']
        for side, other in (('home', 'away'), ('away', 'home')):
            teams.append(game[side])
            opp_terms.append(expected[game[other]] - others_mean[game[side]])
            venue.append(0 if game['neutral'] else (1 if side == 'home' else -1))
            gaps.append([context[side][f] - context[other][f] for f in FEATURES])

    return np.array(teams), np.array(opp_terms), np.array(venue, dtype=float), np.array(gaps, dtype=float)


def _wins_lost(margin, sigma, teams, names):
    lost = 0.5 - _win_probability(margin, sigma)
    return np.array([lost[teams == name].sum() for name in names])


def schedule_load(games, fit, carry, last_season, city_lookup, tz_lookup, effects=None, draws=400, seed=0):
    """
    Return one row per team: load_wins (total wins lost to the schedule), the share from each component, a 90 percent
    range from re-drawing the effects within their standard errors, and the rank (1 is the hardest).
    effects maps each feature to (points, standard error); the raw fitted effects are used if it is not given.
    """
    effects = effects or fit['effects']
    teams, opp_terms, venue, gaps = team_games_matrix(games, fit, carry, last_season, city_lookup, tz_lookup)
    names = sorted(set(teams))
    sigma = fit['sigma']
    hca = fit['home_court'][0]
    coef = np.array([effects[f][0] for f in FEATURES])
    columns = {f: i for i, f in enumerate(FEATURES)}

    def margins(hca_value, coef_values, parts=None):
        """Expected margin of an average team; parts limits it to some of: opponent, venue and component names."""
        parts = parts if parts is not None else {'opponent', 'venue', *COMPONENTS}
        margin = np.zeros(len(teams))
        if 'opponent' in parts:
            margin -= opp_terms
        if 'venue' in parts:
            margin += hca_value * venue
        for name, features in COMPONENTS.items():
            if name in parts:
                idx = [columns[f] for f in features]
                margin += gaps[:, idx] @ coef_values[idx]
        return margin

    total = _wins_lost(margins(hca, coef), sigma, teams, names)
    # the same load without the altitude term, because altitude rests on two teams' home games and is the least certain
    without_altitude = _wins_lost(margins(hca, coef, {'opponent', 'venue', *(set(COMPONENTS) - {'altitude'})}),
                                  sigma, teams, names)
    rows = {name: {'team': name, 'load_wins': float(t), 'load_wins_no_altitude': float(n)}
            for name, t, n in zip(names, total, without_altitude)}
    for part in ['opponent', 'venue', *COMPONENTS]:
        lost = _wins_lost(margins(hca, coef, {part}), sigma, teams, names)
        for name, value in zip(names, lost):
            rows[name][f'load_{part}'] = float(value)

    # re-draw the effects within their standard errors; each draw gives the load with and without the altitude term
    rng = np.random.default_rng(seed)
    se = np.array([effects[f][1] for f in FEATURES])
    no_altitude_parts = {'opponent', 'venue', *(set(COMPONENTS) - {'altitude'})}
    draws_all, draws_no_altitude = [], []
    for _ in range(draws):
        hca_draw, coef_draw = rng.normal(hca, fit['home_court'][1]), rng.normal(coef, se)
        draws_all.append(_wins_lost(margins(hca_draw, coef_draw), sigma, teams, names))
        draws_no_altitude.append(_wins_lost(margins(hca_draw, coef_draw, no_altitude_parts), sigma, teams, names))

    def ranges(point, draws_array):
        """90 percent range of the load, its rank, and the 90 percent range of the rank."""
        draws_array = np.array(draws_array)
        low, high = np.percentile(draws_array, [5, 95], axis=0)
        draw_ranks = (-draws_array).argsort(axis=1).argsort(axis=1) + 1
        rank_low, rank_high = np.percentile(draw_ranks, [5, 95], axis=0)
        return low, high, (-point).argsort().argsort() + 1, rank_low, rank_high

    low, high, ranks, rank_low, rank_high = ranges(total, draws_all)
    low_n, high_n, ranks_n, rank_low_n, rank_high_n = ranges(without_altitude, draws_no_altitude)
    for i, name in enumerate(names):
        rows[name].update({
            'load_low': float(low[i]), 'load_high': float(high[i]), 'load_rank': int(ranks[i]),
            'load_rank_low': int(round(rank_low[i])), 'load_rank_high': int(round(rank_high[i])),
            'load_low_no_altitude': float(low_n[i]), 'load_high_no_altitude': float(high_n[i]),
            'load_rank_no_altitude': int(ranks_n[i]),
            'load_rank_low_no_altitude': int(round(rank_low_n[i])),
            'load_rank_high_no_altitude': int(round(rank_high_n[i])),
        })

    return [rows[name] for name in names]
