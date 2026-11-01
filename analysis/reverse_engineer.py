"""
Try to reproduce other sites' published schedule numbers from the schedule and the records they show,
to see which formulas they are likely using. Run from the project root: python -m analysis.reverse_engineer
Everything below the data section is analysis; the data are copies of what the sites printed on 2026-10-31.
"""

from collections import defaultdict

import numpy as np

from modules.external_sources import CRAFTED_NBA, HOOPS_MENU, full_name
from modules.schedule_scraper import ScheduleScraper
from modules.strength import build_team_games

# ---- what the sites printed (records are the common snapshot all of them show)
RECORDS = {
    'Pelicans': (1, 4), 'Kings': (0, 5), 'Timberwolves': (4, 2), 'Bulls': (1, 5), 'Clippers': (1, 4), 'Jazz': (1, 4),
    'Trail Blazers': (3, 1), 'Lakers': (4, 2), 'Spurs': (3, 2), 'Nuggets': (3, 2), 'Nets': (0, 5), 'Suns': (1, 3),
    'Pacers': (2, 4), 'Grizzlies': (5, 0), 'Warriors': (3, 3), 'Hornets': (3, 3), 'Raptors': (3, 2), 'Thunder': (4, 1),
    'Mavericks': (4, 2), 'Rockets': (5, 1), 'Bucks': (1, 4), 'Knicks': (2, 4), 'Wizards': (3, 3), 'Heat': (2, 4),
    'Magic': (2, 3), 'Celtics': (4, 1), 'Cavaliers': (3, 2), 'Hawks': (3, 3), '76ers': (5, 1), 'Pistons': (5, 1),
}
# Legion Report: combined record of remaining opponents
LEGION_OPP = {
    'Pelicans': (217, 186), 'Kings': (212, 193), 'Timberwolves': (202, 190), 'Bulls': (207, 196),
    'Clippers': (205, 195), 'Jazz': (205, 196), 'Trail Blazers': (211, 203), 'Lakers': (200, 194),
    'Spurs': (204, 198), 'Nuggets': (204, 198), 'Nets': (208, 202), 'Suns': (209, 204), 'Pacers': (202, 199),
    'Grizzlies': (203, 201), 'Warriors': (197, 196), 'Hornets': (200, 200), 'Raptors': (204, 205),
    'Thunder': (201, 202), 'Mavericks': (195, 196), 'Rockets': (196, 198), 'Bucks': (202, 207), 'Knicks': (197, 202),
    'Wizards': (197, 204), 'Heat': (196, 203), 'Magic': (201, 209), 'Celtics': (199, 210), 'Cavaliers': (194, 215),
    'Hawks': (190, 212), '76ers': (188, 213), 'Pistons': (187, 214),
}
# Power Rankings Guru: the team's own Elo, and for remaining games (opp rank, opp win pct, opp Elo)
PRG_ELO = {
    'Mavericks': 1457, 'Magic': 1529, 'Clippers': 1487, 'Suns': 1489, 'Hawks': 1533, 'Knicks': 1650, 'Nets': 1308,
    '76ers': 1566, 'Warriors': 1484, 'Pistons': 1635, 'Bulls': 1367, 'Thunder': 1680, 'Heat': 1490, 'Rockets': 1599,
    'Jazz': 1317, 'Kings': 1341, 'Timberwolves': 1594, 'Spurs': 1668, 'Wizards': 1336, 'Nuggets': 1579,
    'Celtics': 1608, 'Cavaliers': 1559, 'Raptors': 1530, 'Trail Blazers': 1530, 'Bucks': 1369, 'Pelicans': 1415,
    'Hornets': 1531, 'Lakers': 1573, 'Pacers': 1360, 'Grizzlies': 1417,
}
PRG_REMAINING = {
    'Grizzlies': (14.4, .494, 1513), 'Jazz': (14.5, .505, 1517), 'Pelicans': (14.7, .534, 1511),
    'Kings': (14.8, .517, 1510), 'Pacers': (14.8, .500, 1506), 'Nets': (14.9, .506, 1508),
    'Trail Blazers': (14.9, .503, 1507), 'Wizards': (15.0, .488, 1506), 'Bucks': (15.1, .492, 1507),
    'Raptors': (15.2, .494, 1502), 'Timberwolves': (15.2, .510, 1503), 'Lakers': (15.2, .502, 1503),
    'Hornets': (15.3, .496, 1502), 'Bulls': (15.3, .507, 1500), 'Mavericks': (15.5, .495, 1500),
    'Nuggets': (15.6, .502, 1499), 'Warriors': (15.7, .496, 1496), 'Clippers': (15.7, .508, 1496),
    'Suns': (15.8, .501, 1496), 'Heat': (15.8, .486, 1496), 'Cavaliers': (15.8, .471, 1496),
    'Rockets': (15.9, .494, 1495), 'Spurs': (16.1, .502, 1495), 'Celtics': (16.1, .481, 1496),
    'Magic': (16.1, .487, 1489), 'Knicks': (16.2, .489, 1490), '76ers': (16.2, .468, 1492), 'Hawks': (16.3, .471, 1490),
    'Pistons': (16.4, .465, 1487), 'Thunder': (16.5, .494, 1488),
}
# ESPN RPI page: (RPI, PCT, SOS) by the short names ESPN uses
ESPN_RPI = {
    'Dallas': (.661, .667, .659), 'Houston': (.692, .833, .645), 'Golden State': (.581, .500, .608),
    'Phoenix': (.513, .250, .601), 'Atlanta': (.563, .500, .583), 'Utah': (.487, .200, .582),
    'New York': (.514, .333, .574), 'San Antonio': (.561, .600, .548), 'Miami': (.494, .333, .547),
    'Oklahoma City': (.607, .800, .542), 'Orlando': (.498, .400, .531), 'Philadelphia': (.603, .833, .526),
    'Detroit': (.601, .833, .523), 'Portland': (.576, .750, .518), 'Cleveland': (.537, .600, .515),
    'Memphis': (.626, 1.000, .501), 'Brooklyn': (.372, .000, .496), 'Minnesota': (.533, .667, .488),
    'LA Lakers': (.528, .667, .481), 'Milwaukee': (.408, .200, .478), 'LA': (.400, .200, .467),
    'Charlotte': (.468, .500, .458), 'Chicago': (.374, .167, .443), 'Toronto': (.477, .600, .437),
    'Denver': (.474, .600, .433), 'Sacramento': (.324, .000, .432), 'Washington': (.443, .500, .424),
    'Boston': (.499, .800, .398), 'Indiana': (.362, .333, .372), 'New Orleans': (.250, .200, .267),
}
# CraftedNBA: (raw net rating, projected strength, adjusted net rating) next to the CRAFTED_NBA difficulty figures
CRAFTED_RATINGS = {
    'Dallas': (2.9, -2.4, 5.7), 'New York': (-1.1, 5.2, 1.5), 'Brooklyn': (-10.5, 0.2, -8.6),
    'Clippers': (-5.9, -0.3, -4.0), 'Golden State': (0.9, 2.1, 2.6), 'Hawks': (4.5, 2.6, 6.1),
    'Bulls': (-15.7, -0.6, -14.4), 'Pelicans': (-1.8, -2.3, -0.6), 'Pistons': (8.1, 4.5, 9.2),
    'Magic': (-7.6, 1.4, -6.6), 'Suns': (-11.5, 2.9, -10.6), 'Timberwolves': (14.4, 3.7, 15.1),
    'Nuggets': (-1.6, 8.8, -1.0), '76ers': (3.6, 5.8, 3.7), 'Thunder': (3.4, 10.2, 3.4), 'Cavaliers': (0.3, 8.4, 0.1),
    'Spurs': (6.0, 4.9, 5.7), 'Bucks': (-10.6, -1.7, -11.1), 'Lakers': (6.0, 5.9, 5.4), 'Wizards': (1.2, -1.6, 0.5),
    'Celtics': (9.8, 10.8, 8.9), 'Kings': (-15.7, -3.3, -17.1), 'Hornets': (-8.8, -1.6, -10.2),
    'Rockets': (10.8, 7.7, 9.3), 'Trail Blazers': (7.5, 4.9, 5.9), 'Pacers': (-2.7, 0.5, -4.3),
    'Heat': (-3.6, 3.7, -5.4), 'Grizzlies': (11.9, -2.5, 9.8), 'Jazz': (-8.0, -1.0, -10.2), 'Raptors': (10.8, 3.9, 8.4),
}


def played_and_remaining(scraper):
    """Per team (full name): games already played (first W+L games by date) and games remaining."""
    by_team = build_team_games(scraper.games, TZ)
    split = {}
    for short, (w, l) in RECORDS.items():
        team = full_name(short)
        split[team] = (by_team[team][:w + l], by_team[team][w + l:])
    return split, by_team


def show(label, observed, predicted, unit=''):
    teams = sorted(observed)
    o = np.array([observed[t] for t in teams], float)
    p = np.array([predicted[t] for t in teams], float)
    print(f'  {label:52} r={np.corrcoef(o, p)[0, 1]:+.3f}  mean abs error={np.abs(o - p).mean():.4f}{unit}  '
          f'exact: {int(np.isclose(o, p, atol=1e-9).sum())}/30')


def min_max(values):
    low, high = min(values.values()), max(values.values())
    return {t: 100 * (v - low) / (high - low) for t, v in values.items()}


if __name__ == '__main__':
    from modules.travel import build_tz_lookup
    TZ = build_tz_lookup('cities.csv')
    scraper = ScheduleScraper('data/schedule_2026_27.json')
    scraper.run()
    split, by_team = played_and_remaining(scraper)
    wins = {full_name(s): w for s, (w, l) in RECORDS.items()}
    losses = {full_name(s): l for s, (w, l) in RECORDS.items()}
    pct = {t: wins[t] / (wins[t] + losses[t]) for t in wins}
    games_after = {t: len(split[t][1]) for t in split}

    print('Hoops Menu: published recipe applied to their own five columns')
    columns = [{t: HOOPS_MENU[t][i] for t in HOOPS_MENU} for i in (1, 2, 3, 4, 5)]
    scaled = [min_max(c) for c in columns]
    recipe = {t: float(np.mean([s[t] for s in scaled])) for t in HOOPS_MENU}
    show('equal-weight mean of five min-max scaled columns', {t: HOOPS_MENU[t][0] for t in HOOPS_MENU}, recipe)

    print('\nLegion Report: combined record of remaining opponents')
    pred_w, pred_l = {}, {}
    for team, (played, remaining) in split.items():
        pred_w[team] = sum(wins[g['opp']] for g in remaining)
        pred_l[team] = sum(losses[g['opp']] for g in remaining)
    show('opponent wins over remaining games', {full_name(s): v[0] for s, v in LEGION_OPP.items()}, pred_w)
    show('opponent losses over remaining games', {full_name(s): v[1] for s, v in LEGION_OPP.items()}, pred_l)
    print(f'  games left matches 80 minus games played for all teams: '
          f'{all(games_after[t] == 80 - wins[t] - losses[t] for t in split)}')

    print('\nESPN RPI: published RPI against its own columns, then SOS rebuilt from records')
    rpi_formula = {t: .25 * v[1] + .75 * v[2] for t, v in ((full_name(k), v) for k, v in ESPN_RPI.items())}
    show('RPI = 0.25 * win pct + 0.75 * SOS', {full_name(k): v[0] for k, v in ESPN_RPI.items()}, rpi_formula, '')
    owp = {t: float(np.mean([pct[g['opp']] for g in split[t][0]])) for t in split}
    oowp = {t: float(np.mean([owp[g['opp']] for g in split[t][0]])) for t in split}
    sos_a = {t: (2 * owp[t] + oowp[t]) / 3 for t in split}
    show('SOS = (2 * OWP + OOWP) / 3, opponents\' plain win pct', {full_name(k): v[2] for k, v in ESPN_RPI.items()}, sos_a)
    agg = {t: sum(wins[g['opp']] for g in split[t][0]) / sum(wins[g['opp']] + losses[g['opp']] for g in split[t][0]) for t in split}
    sos_b = {t: (2 * agg[t] + oowp[t]) / 3 for t in split}
    show('same, OWP weighted by opponents\' games played', {full_name(k): v[2] for k, v in ESPN_RPI.items()}, sos_b)

    print('\nPower Rankings Guru: remaining schedule')
    obs_pct = {full_name(s): v[1] for s, v in PRG_REMAINING.items()}
    show('opp win pct = mean of opponents\' win pct', obs_pct,
         {t: float(np.mean([pct[g['opp']] for g in split[t][1]])) for t in split})
    show('opp win pct = combined opponent record (Legion style)', obs_pct, {t: pred_w[t] / (pred_w[t] + pred_l[t]) for t in split})
    elo = {full_name(s): v for s, v in PRG_ELO.items()}
    obs_elo = {full_name(s): v[2] for s, v in PRG_REMAINING.items()}
    plain = {t: float(np.mean([elo[g['opp']] for g in split[t][1]])) for t in split}
    show('opp Elo = plain mean of opponents\' Elo', obs_elo, plain, ' Elo')
    # a road game counts the opponent as stronger and a home game as weaker, by an unknown amount h
    teams = sorted(split)
    venue = np.array([np.mean([(-1 if g['is_home'] else 1) for g in split[t][1]]) for t in teams])
    gap = np.array([obs_elo[t] - plain[t] for t in teams])
    h = float(venue @ gap / (venue @ venue))
    show(f'opp Elo = plain mean +/- {h:.1f} for venue', obs_elo, {t: plain[t] + h * v for t, v in zip(teams, venue)}, ' Elo')
    print(f'  fitted home-court Elo swing: about {h:.0f} points')
    order = sorted(elo, key=lambda t: -elo[t])
    elo_rank = {t: i + 1 for i, t in enumerate(order)}
    show('opp rank = mean of opponents\' Elo rank', {full_name(s): v[0] for s, v in PRG_REMAINING.items()},
         {t: float(np.mean([elo_rank[g['opp']] for g in split[t][1]])) for t in split})

    print('\nCraftedNBA: remaining difficulty regressed on schedule features (30 teams, so read loosely)')
    cr = {full_name(s): v for s, v in CRAFTED_RATINGS.items()}
    target = {full_name(s): CRAFTED_NBA[s][1] for s in CRAFTED_NBA}
    features = {}
    for team, (played, remaining) in split.items():
        n = len(remaining)
        nxt = by_team[team]
        own_b2b_home = sum(1 for g in remaining if g['back_to_back'] and g['is_home']) / n
        own_b2b_away = sum(1 for g in remaining if g['back_to_back'] and not g['is_home']) / n
        # opponent on a back-to-back that night
        opp_b2b = sum(1 for g in remaining if next(o['back_to_back'] for o in by_team[g['opp']] if o['datetime'] == g['datetime'])) / n
        features[team] = {
            'opp_proj': np.mean([cr[g['opp']][1] for g in remaining]),
            'opp_adj': np.mean([cr[g['opp']][2] for g in remaining]),
            'opp_raw': np.mean([cr[g['opp']][0] for g in remaining]),
            'road_minus_home': np.mean([(-1 if g['is_home'] else 1) for g in remaining]),
            'own_b2b': own_b2b_home + own_b2b_away,
            'opp_b2b': opp_b2b,
            'altitude_road': sum(1 for g in remaining if not g['is_home'] and g['city'] in ('Denver', 'Salt Lake City')) / n,
        }
    y = np.array([target[t] for t in teams])
    for names in (['opp_proj'], ['opp_adj'], ['opp_raw'], ['opp_proj', 'opp_adj', 'opp_raw'],
                  ['opp_proj', 'opp_adj', 'opp_raw', 'road_minus_home'],
                  ['opp_proj', 'opp_adj', 'opp_raw', 'road_minus_home', 'own_b2b', 'opp_b2b', 'altitude_road']):
        X = np.column_stack([[features[t][k] for t in teams] for k in names] + [np.ones(len(teams))])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        r2 = 1 - resid.var() / y.var()
        print(f'  {" + ".join(names):70} R2={r2:.2f}  ' + '  '.join(f'{k}={b:+.2f}' for k, b in zip(names, beta)))
