from modules.compare import _min_max, _ranks_hardest_first, build_comparison_rows
from modules.external_sources import (HOOPS_MENU, LEGION_BACK_TO_BACKS, LEGION_REMAINING, LEGION_ROAD_AND_HOME,
                                      YAHOO_FLIGHTS, YAHOO_MILES)


def test_every_source_covers_the_same_thirty_teams():
    teams = set(HOOPS_MENU)
    assert len(teams) == 30
    assert teams == set(LEGION_BACK_TO_BACKS) == set(YAHOO_MILES) == {t for t, _ in LEGION_REMAINING}
    assert teams == set(LEGION_ROAD_AND_HOME) == set(YAHOO_FLIGHTS)


def test_legion_back_to_backs_total_matches_the_nba_average():
    # the NBA says teams average 14.2 back-to-backs, which is 426 across 30 teams
    assert sum(LEGION_BACK_TO_BACKS.values()) == 426


def test_every_ranking_source_covers_the_same_thirty_teams():
    from modules.compare import _source_ranks

    for name, ranks in _source_ranks().items():
        assert set(ranks) == set(HOOPS_MENU), name
        assert min(ranks.values()) == 1 and max(ranks.values()) == 30, name


def test_tied_values_share_a_rank():
    from modules.compare import _ranks_with_ties

    assert _ranks_with_ties({'a': 2, 'b': 2, 'c': 1}) == {'a': 1, 'b': 1, 'c': 3}


def test_ranks_run_hardest_first():
    assert _ranks_hardest_first({'a': 1, 'b': 3, 'c': 2}) == {'b': 1, 'c': 2, 'a': 3}


def test_min_max_scales_to_zero_and_one_hundred():
    assert _min_max({'a': 5, 'b': 10, 'c': 7.5}) == {'a': 0, 'b': 100, 'c': 50}


def test_comparison_rows_join_our_numbers_to_theirs():
    schedule_rows = [{'team': t, 'difficulty_rank': i + 1, 'load_rank_no_altitude': 30 - i, 'three_in_four': i,
                      'tz_hours_crossed': i,
                      'rest_disadvantage_games': i, 'second_night_road_b2b': 8, 'both_nights_road_b2b': 4,
                      'longest_road_trip': 5, 'longest_homestand': 6, 'flights': 57}
                     for i, t in enumerate(sorted(HOOPS_MENU))]
    summaries = {t: {'total_miles': 40000.4 + i, 'back_to_backs': 14} for i, t in enumerate(sorted(HOOPS_MENU))}
    rows = build_comparison_rows(schedule_rows, summaries)

    assert len(rows) == 30
    pelicans = next(r for r in rows if r['team'] == 'New Orleans Pelicans')
    assert (pelicans['hm_rank'], pelicans['legion_rank'], pelicans['legion_b2b']) == (1, 1, 16)
    assert all(1 <= r['my_rank_no_altitude'] <= 30 for r in rows)
