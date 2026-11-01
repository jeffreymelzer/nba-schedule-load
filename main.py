"""
Main script for analyzing NBA schedule travel and strength of schedule.
"""

import csv
import json
import os

import matplotlib.pyplot as plt

from modules.calibrate import carryover, fit_effects, shrink_effects
from modules.compare import build_comparison_rows
from modules.expected_wins import schedule_load
from modules.external_sources import SOURCE_METHODS
from modules.results import drop_bubble_games, fetch_season_results
from modules.schedule_scraper import ScheduleScraper
from modules.standings import fetch_standings
from modules.strength import (add_difficulty_index, build_back_to_back_lookup, build_team_games, correlation,
                              summarize_strength)
from modules.travel import (build_city_lookup, build_tz_lookup, check_cities, city_key, summarize_team,
                            team_leg_rows)
from utils.plotter import plot_bar, plot_route

# The schedule is read from the games list in data/. To refresh it, set NBA_SCHEDULE_URL to an ECAL calendar
# subscription (webcal:// is plain https://) or an NBA.com schedule JSON link, and the list is rewritten.
SCHEDULE_URL = os.environ.get('NBA_SCHEDULE_URL')
SCHEDULE_CACHE = r'data/schedule_2026_27.json'
STANDINGS_CACHE = r'data/standings_2025_26.json'
PREVIOUS_SEASON_END_YEAR = 2026
CITIES_CSV = r'cities.csv'
OUTPUT_DIR = r'output'
SITE_DATA_DIR = r'docs/data'  # what the website reads; the map outline is written here by utils/basemap_export.py

# seasons of results used to measure what rest, travel and the rest of a game's situation are worth (ending years)
RESULT_SEASONS = tuple(range(2017, 2027))
# 2020-21 (ending year 2021) was played mostly in empty arenas, so its home-court edge is left out of the average
HOME_COURT_EXCLUDE = (2021,)

# how each fitted effect is described on the dashboard: label, unit (always the effect on the team's own margin)
EFFECT_LABELS = {
    'home_court': ('Home court (2020–21 left out)', 'points for the home team'),
    'b2b': ('Second night of a back-to-back', 'points per game'),
    'b2b_road': ('Extra cost when that game is on the road', 'points per game'),
    'long_rest': ('Three or more days of rest', 'points per game'),
    'miles_k': ('Distance travelled since the last game', 'points per 1,000 miles'),
    'tz_east': ('Travelling east', 'points per time zone crossed'),
    'tz_west': ('Travelling west', 'points per time zone crossed'),
    'three_in_four': ('Third game in four nights', 'points per game'),
    'altitude_visit': ('Visiting Denver or Salt Lake City', 'points per game'),
}

# schedule columns compared against last season's win percentage
COMPARED_METRICS = ['total_miles', 'flights', 'travel_back_to_backs', 'second_night_road_b2b', 'sos_opp_win_pct',
                    'sos_vs_balanced', 'net_rest_edge', 'three_in_four', 'tz_hours_crossed', 'longest_road_trip',
                    'longest_homestand', 'difficulty_index']


def get_schedule():
    if not SCHEDULE_URL and not os.path.exists(SCHEDULE_CACHE):
        raise FileNotFoundError(f'{SCHEDULE_CACHE} is missing; set NBA_SCHEDULE_URL to download the schedule')
    scraper = ScheduleScraper(SCHEDULE_URL or SCHEDULE_CACHE)
    scraper.run()
    if SCHEDULE_URL:
        scraper.save_games(SCHEDULE_CACHE)
    return scraper


def build_team_schedule_rows(scraper, summaries, standings, tz_lookup):
    """One row per team joining travel, strength of schedule and last season's record."""
    by_team = build_team_games(scraper.games, tz_lookup)
    opp_back_to_back = build_back_to_back_lookup(by_team)
    rows = []
    for team, team_games in by_team.items():
        row = summarize_strength(team, team_games, opp_back_to_back, standings, tz_lookup)
        row.update({
            'wins_prev': standings[team]['wins'],
            'losses_prev': standings[team]['losses'],
            'win_pct_prev': standings[team]['win_pct'],
            'net_rating_prev': standings[team]['net_rating'],
            'total_miles': summaries[team]['total_miles'],
            'travel_back_to_backs': summaries[team]['travel_back_to_backs'],
        })
        rows.append(row)

    return add_difficulty_index(rows)


def build_load_model(scraper, city_lookup, tz_lookup):
    """
    Measure the effects from past results and apply them to the coming schedule. Returns the schedule-load rows,
    the effect rows (measured and used) and a one-row summary of the model.
    """
    seasons = {year: drop_bubble_games(fetch_season_results(year, f'data/results_{year}.json'))
               for year in RESULT_SEASONS}
    fit = fit_effects(seasons, city_lookup, tz_lookup, HOME_COURT_EXCLUDE)
    # the same fit on each half of the seasons, to show whether an effect has moved over time
    middle = len(RESULT_SEASONS) // 2
    halves = [fit_effects({y: seasons[y] for y in years}, city_lookup, tz_lookup, HOME_COURT_EXCLUDE)
              for years in (RESULT_SEASONS[:middle], RESULT_SEASONS[middle:])]
    carry = carryover(fit['ratings'], list(seasons))
    used, spread = shrink_effects(fit['effects'])
    load_rows = schedule_load(scraper.games, fit, carry, max(RESULT_SEASONS), city_lookup, tz_lookup, effects=used)

    points_to_win_pct = 100 * 0.3989 / fit['sigma']  # one point of margin near an even game, in win probability
    effect_rows = []
    measured = {'home_court': fit['home_court'], **fit['effects']}
    earlier, recent = ({'home_court': h['home_court'], **h['effects']} for h in halves)
    for key, (label, unit) in EFFECT_LABELS.items():
        b, se = measured[key]
        used_b, used_se = (b, se) if key == 'home_court' else used[key]
        effect_rows.append({
            'effect': label, 'unit': unit, 'measured': b, 'measured_se': se, 'used': used_b, 'used_se': used_se,
            'earlier_seasons': earlier[key][0], 'recent_seasons': recent[key][0],
            'win_pct_per_game': used_b * points_to_win_pct,
            'clear': 'Clearly measured' if abs(b / se) >= 1.96 else 'Uncertain',
        })
    summary = {
        'games': fit['n_games'], 'seasons': len(seasons), 'sigma': fit['sigma'], 'carryover': carry,
        'prior_spread': spread, 'win_pct_per_point': points_to_win_pct,
    }

    return load_rows, effect_rows, summary


def add_schedule_load(schedule_rows, load_rows):
    """
    Make the expected-wins load the headline difficulty (difficulty_index is wins lost, difficulty_rank 1 is the
    hardest) and keep the earlier average-of-standardized-measures ranking as zscore_index and zscore_rank.
    """
    by_team = {r['team']: r for r in load_rows}
    for row in schedule_rows:
        row['zscore_index'], row['zscore_rank'] = row.pop('difficulty_index'), row.pop('difficulty_rank')
        load = by_team[row['team']]
        row.update({k: v for k, v in load.items() if k not in ('team', 'load_wins', 'load_rank')})
        row['difficulty_index'], row['difficulty_rank'] = load['load_wins'], load['load_rank']

    return schedule_rows


def round_row(row):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}


def export_dashboard_data(scraper, summaries, schedule_rows, city_lookup, tz_lookup, effect_rows, model_summary):
    """Write the JSON files the website reads."""
    os.makedirs(SITE_DATA_DIR, exist_ok=True)
    summary_rows = [
        {'team': team, **{k: (round(v) if isinstance(v, float) else v) for k, v in s.items()}}
        for team, s in summaries.items()
    ]
    leg_rows = [row for team, games in scraper.schedule_lookup.items()
                for row in team_leg_rows(team, games, city_lookup, tz_lookup)]
    with open(CITIES_CSV) as f:
        # only this season's arena cities; cities.csv also holds venues from past seasons
        city_rows = [{'city': r[0].strip(), 'state': r[1].strip(), 'lat': float(r[2]), 'lon': float(r[3])}
                     for r in csv.reader(f) if city_key(r[0].strip(), r[1].strip()) in scraper.cities]

    for name, rows in [('team_summary', summary_rows), ('team_legs', leg_rows),
                       ('team_schedule', [round_row(r) for r in schedule_rows]), ('cities', city_rows),
                       ('source_comparison', build_comparison_rows(schedule_rows, summaries)),
                       ('source_methods', SOURCE_METHODS),
                       ('schedule_effects', [round_row(r) for r in effect_rows]),
                       ('model_summary', [round_row(model_summary)])]:
        with open(f'{SITE_DATA_DIR}/{name}.json', 'w') as f:
            json.dump(rows, f)


def main():
    scraper = get_schedule()
    city_lookup = build_city_lookup(CITIES_CSV)
    tz_lookup = build_tz_lookup(CITIES_CSV)
    check_cities(scraper.cities, city_lookup)
    standings = fetch_standings(PREVIOUS_SEASON_END_YEAR, STANDINGS_CACHE)
    missing = set(scraper.schedule_lookup) - set(standings)
    if missing:
        raise KeyError(f'teams missing from last season standings: {sorted(missing)}')

    summaries = {team: summarize_team(games, city_lookup, tz_lookup) for team, games in scraper.schedule_lookup.items()}
    schedule_rows = build_team_schedule_rows(scraper, summaries, standings, tz_lookup)
    load_rows, effect_rows, model_summary = build_load_model(scraper, city_lookup, tz_lookup)
    add_schedule_load(schedule_rows, load_rows)

    print(f"what a game's situation is worth, from {model_summary['games']} games (points on the team's own margin)")
    for r in effect_rows:
        print(f"{r['effect']:44}{r['measured']:>+7.2f} +/- {r['measured_se']:.2f}   used {r['used']:>+6.2f}   {r['clear']}")
    print(f"\n{'schedule load, hardest first':28}{'wins lost':>10}{'90% range':>18}{'rank range':>12}")
    for r in sorted(load_rows, key=lambda r: r['load_rank']):
        print(f"{r['team']:28}{r['load_wins']:>+10.2f}{r['load_low']:>+9.2f}{r['load_high']:>+8.2f}"
              f"{r['load_rank_low']:>8}-{r['load_rank_high']:<3}")
    print()

    print(f"{'team':26}{'games':>6}{'miles':>9}{'mi/game':>9}{'b2b':>5}{'travel b2b':>11}")
    for team, s in sorted(summaries.items(), key=lambda kv: -kv[1]['total_miles']):
        print(f"{team:26}{s['games']:>6}{s['total_miles']:>9.0f}{s['miles_per_game']:>9.0f}"
              f"{s['back_to_backs']:>5}{s['travel_back_to_backs']:>11}")

    print('\ncorrelation with last season win percentage (30 teams; |r| below about 0.36 is not distinguishable from noise)')
    for metric in COMPARED_METRICS:
        print(f'{metric:26}{correlation(schedule_rows, "win_pct_prev", metric):>7.2f}')

    export_dashboard_data(scraper, summaries, schedule_rows, city_lookup, tz_lookup, effect_rows, model_summary)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_bar(summaries, 'total_miles', 'Total travel miles by team', f'{OUTPUT_DIR}/total_miles.png')
    plot_bar(summaries, 'travel_back_to_backs', 'Back-to-backs with travel', f'{OUTPUT_DIR}/travel_back_to_backs.png')
    most_travelled = max(summaries, key=lambda t: summaries[t]['total_miles'])
    plot_route(most_travelled, scraper.schedule_lookup[most_travelled], city_lookup,
               f'{OUTPUT_DIR}/route_{most_travelled.replace(" ", "_")}.png')
    plt.show()


if __name__ == '__main__':
    main()
