"""
Join our schedule numbers with other sites' published figures, team by team.
"""

import numpy as np

from modules.external_sources import (CRAFTED_NBA, ESPN_RPI_SOS, HOOPS_MENU, LEGION_BACK_TO_BACKS, LEGION_REMAINING,
                                      LEGION_ROAD_AND_HOME, PRG_PLAYED, PRG_REMAINING, YAHOO_FLIGHTS, YAHOO_MILES,
                                      full_name)


def _ranks_hardest_first(values):
    order = sorted(values, key=lambda team: -values[team])
    return {team: i + 1 for i, team in enumerate(order)}


def _ranks_with_ties(values):
    """Rank hardest first (highest value), teams with equal values share the best rank among them."""
    return {team: 1 + sum(1 for other in values.values() if other > value) for team, value in values.items()}


def _source_ranks():
    """Each outside source's rank (1 is the hardest schedule) by full team name."""
    return {
        'prg_remaining': {full_name(team): rank for rank, team, _ in PRG_REMAINING},
        'prg_played': {full_name(team): rank for rank, team, _ in PRG_PLAYED},
        'crafted_remaining': _ranks_with_ties({full_name(t): v[1] for t, v in CRAFTED_NBA.items()}),
        'crafted_past': _ranks_with_ties({full_name(t): v[0] for t, v in CRAFTED_NBA.items()}),
        'espn_rpi': {full_name(team): i + 1 for i, (team, _) in enumerate(ESPN_RPI_SOS)},
    }


def _min_max(values):
    low, high = min(values.values()), max(values.values())
    if high == low:
        return {team: 0 for team in values}
    return {team: 100 * (v - low) / (high - low) for team, v in values.items()}


def hoops_menu_recipe_ranks(schedule_rows, summaries):
    """Rank teams with Hoops Menu's recipe (equal-weight min-max of five measures) applied to our own counts."""
    columns = [
        {r['team']: summaries[r['team']]['total_miles'] for r in schedule_rows},
        {r['team']: summaries[r['team']]['back_to_backs'] for r in schedule_rows},
        {r['team']: r['three_in_four'] for r in schedule_rows},
        {r['team']: r['tz_hours_crossed'] for r in schedule_rows},
        {r['team']: r['rest_disadvantage_games'] for r in schedule_rows},
    ]
    scaled = [_min_max(c) for c in columns]
    index = {team: float(np.mean([s[team] for s in scaled])) for team in scaled[0]}
    return _ranks_hardest_first(index)


def build_comparison_rows(schedule_rows, summaries):
    """One row per team with our value next to each outside source's value."""
    recipe = hoops_menu_recipe_ranks(schedule_rows, summaries)
    hoops_rank = _ranks_hardest_first({t: v[0] for t, v in HOOPS_MENU.items()})
    legion_rank = {team: i + 1 for i, (team, _) in enumerate(LEGION_REMAINING)}
    legion_pct = dict(LEGION_REMAINING)
    other = _source_ranks()
    crafted = {full_name(t): v for t, v in CRAFTED_NBA.items()}
    espn_sos = {full_name(t): v for t, v in ESPN_RPI_SOS}

    rows = []
    for r in schedule_rows:
        team = r['team']
        hm = HOOPS_MENU[team]
        rows.append({
            'team': team,
            'my_rank': r['difficulty_rank'],
            'my_rank_no_altitude': r['load_rank_no_altitude'],
            'hm_rank': hoops_rank[team],
            'hm_index': hm[0],
            'legion_rank': legion_rank[team],
            'legion_opp_win_pct': legion_pct[team],
            'recipe_rank': recipe[team],
            'prg_remaining_rank': other['prg_remaining'][team],
            'prg_played_rank': other['prg_played'][team],
            'crafted_remaining_rank': other['crafted_remaining'][team],
            'crafted_remaining': crafted[team][1],
            'crafted_past_rank': other['crafted_past'][team],
            'crafted_past': crafted[team][0],
            'espn_rpi_rank': other['espn_rpi'][team],
            'espn_rpi_sos': espn_sos[team],
            'my_miles': round(summaries[team]['total_miles']),
            'hm_miles': hm[1],
            'yahoo_miles': YAHOO_MILES[team],
            'my_b2b': summaries[team]['back_to_backs'],
            'hm_b2b': hm[2],
            'legion_b2b': LEGION_BACK_TO_BACKS[team],
            'my_3in4': r['three_in_four'],
            'hm_3in4': hm[3],
            'my_rest_disadv': r['rest_disadvantage_games'],
            'hm_rest_disadv': hm[5],
            'my_second_night_road': r['second_night_road_b2b'],
            'legion_second_night_road': LEGION_ROAD_AND_HOME[team][0],
            'my_both_nights_road': r['both_nights_road_b2b'],
            'legion_both_nights_road': LEGION_ROAD_AND_HOME[team][1],
            'my_road_trip': r['longest_road_trip'],
            'legion_road_trip': LEGION_ROAD_AND_HOME[team][2],
            'my_homestand': r['longest_homestand'],
            'legion_homestand': LEGION_ROAD_AND_HOME[team][3],
            'my_flights': r['flights'],
            'yahoo_flights': YAHOO_FLIGHTS[team],
        })

    return rows
