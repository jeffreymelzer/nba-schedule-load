"""
Measure from past results what home court, rest, travel and the rest of a game's situation are worth in points.

Each game gives one equation: the home team's margin equals the home-court edge (zero at a neutral site), plus the
home team's strength minus the visitor's, plus what each situation feature is worth times the home team's value minus
the visitor's. Strength is fitted separately for every team and season, so a strong team's wins do not look like
rest or travel effects.
"""

import numpy as np

from modules.context import FEATURES, build_game_contexts


def fit_effects(seasons, city_lookup, tz_lookup, home_court_exclude=()):
    """
    seasons maps a season label to its list of finished games (see modules.results). Home court is fitted for each
    season, because it moved a lot in 2020-21 when arenas were empty; the value returned is the average over the
    seasons except those named in home_court_exclude. Returns {'home_court': (points, standard error),
    'home_court_by_season': {season: (points, standard error)}, 'effects': {feature: (points, standard error)},
    'sigma': residual standard deviation of a margin, 'ratings': {(season, team): points}, 'n_games': int}.
    """
    rows, targets, keys = [], [], []
    for season, games in seasons.items():
        for context in build_game_contexts(games, city_lookup, tz_lookup):
            game = context['game']
            rows.append((season, game, context))
            targets.append(game['home_score'] - game['away_score'])
            keys.extend([(season, game['home']), (season, game['away'])])

    season_order = sorted(seasons)
    n_court = len(season_order)
    first_feature = n_court
    team_keys = sorted(set(keys))
    column = {key: first_feature + len(FEATURES) + i for i, key in enumerate(team_keys)}
    X = np.zeros((len(rows), first_feature + len(FEATURES) + len(team_keys)))
    for i, (season, game, context) in enumerate(rows):
        if not game['neutral']:
            X[i, season_order.index(season)] = 1
        for j, name in enumerate(FEATURES):
            X[i, first_feature + j] = context['home'][name] - context['away'][name]
        X[i, column[(season, game['home'])]] = 1
        X[i, column[(season, game['away'])]] = -1

    y = np.array(targets, dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    rank = np.linalg.matrix_rank(X)
    residual_variance = float(((y - X @ beta) ** 2).sum() / (len(y) - rank))
    covariance = residual_variance * np.linalg.pinv(X.T @ X)
    standard_errors = np.sqrt(np.diag(covariance))

    ratings = {key: float(beta[column[key]]) for key in team_keys}
    for season in seasons:  # centre each season's ratings on zero; only differences between teams are identified
        mean = np.mean([r for (s, _), r in ratings.items() if s == season])
        ratings = {k: (r - mean if k[0] == season else r) for k, r in ratings.items()}

    by_season = {s: (float(beta[k]), float(standard_errors[k])) for k, s in enumerate(season_order)}
    kept = [s for s in season_order if s not in home_court_exclude] or season_order
    home_court = (float(np.mean([by_season[s][0] for s in kept])),
                  float(np.sqrt(sum(by_season[s][1] ** 2 for s in kept)) / len(kept)))

    return {
        'home_court': home_court,
        'home_court_by_season': by_season,
        'effects': {name: (float(beta[first_feature + j]), float(standard_errors[first_feature + j]))
                    for j, name in enumerate(FEATURES)},
        'sigma': float(np.sqrt(residual_variance)),
        'ratings': ratings,
        'n_games': len(y),
    }


def shrink_effects(effects):
    """
    Partial pooling toward zero. Each situation effect is measured with noise, and noisy ones (altitude, three
    games in four nights) would otherwise swing a team's rank. The common spread of true effects is estimated
    from how far the estimates stray beyond their own noise, and each estimate moves toward zero by the share of its
    variance that is noise. Home court is not shrunk. Returns {feature: (shrunk points, posterior standard error)}.
    """
    excess = [b ** 2 - se ** 2 for b, se in effects.values()]
    tau2 = max(float(np.mean(excess)), 1e-6)
    shrunk = {}
    for name, (b, se) in effects.items():
        weight = tau2 / (tau2 + se ** 2)
        shrunk[name] = (b * weight, float(np.sqrt(weight) * se))

    return shrunk, float(np.sqrt(tau2))


def carryover(ratings, seasons):
    """
    How much of a team's rating carries into the next season: the slope of next season's rating on this season's,
    through the origin, pooled over consecutive seasons. Used to shrink last season's ratings for the coming one.
    """
    seasons = sorted(seasons)
    now, nxt = [], []
    for first, second in zip(seasons, seasons[1:]):
        for (season, team), rating in ratings.items():
            if season == first:
                now.append(rating)
                nxt.append(ratings[(second, team)])
    now, nxt = np.array(now), np.array(nxt)

    return float(now @ nxt / (now @ now))
