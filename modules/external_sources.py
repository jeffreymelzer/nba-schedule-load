"""
Published 2026-27 schedule figures from other sites, copied from their pages on 2026-10-31 for comparison.
These are transcriptions, so spot-check them against the live pages before quoting them.
Legion Report's remaining-opponents ranking rebuilds as results come in, so it is a snapshot.
"""

RETRIEVED = '2026-10-31'

SOURCES = {
    'hoops_menu': {
        'name': 'Hoops Menu',
        'url': 'https://hoopsmenu.com/nba/schedule-rankings',
        'measures': 'Mean of five equal-weight measures (miles, back-to-backs, 3-in-4 stretches, time-zone crossings, '
                    'rest-disadvantage games), each scaled 0-100. No opponent strength.',
    },
    'legion_b2b': {
        'name': 'Legion Report back-to-backs',
        'url': 'https://legionreport.com/nba-back-to-backs/',
        'measures': 'Games on consecutive days, counted from the BALLDONTLIE schedule.',
    },
    'legion_remaining': {
        'name': 'Legion Report remaining schedule',
        'url': 'https://legionreport.com/?p=47297',
        'measures': 'Combined current record of every remaining opponent, once per game left. Hardest first.',
    },
    'yahoo_miles': {
        'name': 'Yahoo Sports air miles',
        'url': 'https://sports.yahoo.com/nba/article/nba-schedule-release-pelicans-and-spurs-will-fly-the-most-miles-in-2026-27-season-knicks-will-travel-the-least-021750216.html',
        'measures': 'Estimated flight miles between arenas with a 4% margin for weather.',
    },
}

# team: (difficulty index, miles, back-to-backs, 3-in-4 stretches, time-zone crossings, rest-disadvantage games)
HOOPS_MENU = {
    'New Orleans Pelicans': (86.7, 55529, 16, 16, 28, 13),
    'Dallas Mavericks': (78.5, 44779, 16, 15, 32, 14),
    'Golden State Warriors': (64.4, 45658, 15, 15, 29, 12),
    'Boston Celtics': (63.3, 41282, 16, 14, 23, 14),
    'Denver Nuggets': (61.5, 47910, 14, 13, 40, 12),
    'Brooklyn Nets': (58.4, 37595, 16, 15, 17, 14),
    'Cleveland Cavaliers': (56.5, 39350, 16, 14, 24, 12),
    'Los Angeles Lakers': (56.1, 43717, 15, 15, 25, 11),
    'Sacramento Kings': (55.2, 48270, 14, 14, 31, 11),
    'Chicago Bulls': (53.6, 35394, 15, 14, 36, 11),
    'Milwaukee Bucks': (50.6, 41492, 14, 13, 38, 11),
    'Houston Rockets': (49.7, 45337, 14, 14, 28, 11),
    'Toronto Raptors': (48.2, 35111, 15, 15, 19, 13),
    'Portland Trail Blazers': (45.6, 44606, 15, 14, 23, 9),
    'Phoenix Suns': (45.4, 46585, 13, 13, 34, 11),
    'Indiana Pacers': (45.0, 37559, 15, 13, 25, 12),
    'Atlanta Hawks': (38.4, 37157, 14, 14, 21, 12),
    'Orlando Magic': (38.2, 43327, 14, 12, 23, 12),
    'Detroit Pistons': (37.5, 35984, 15, 13, 28, 9),
    'Miami Heat': (35.3, 49573, 13, 13, 19, 11),
    'San Antonio Spurs': (34.7, 54086, 13, 11, 29, 9),
    'Utah Jazz': (33.7, 48813, 13, 11, 37, 8),
    'Minnesota Timberwolves': (31.3, 47309, 13, 13, 30, 7),
    'Memphis Grizzlies': (30.9, 45676, 13, 12, 36, 7),
    'LA Clippers': (30.2, 47451, 13, 12, 30, 8),
    'Oklahoma City Thunder': (23.4, 44283, 13, 12, 29, 7),
    'Charlotte Hornets': (23.2, 36520, 13, 13, 23, 10),
    'Washington Wizards': (22.2, 35744, 14, 11, 21, 11),
    'Philadelphia 76ers': (21.9, 41319, 13, 11, 22, 11),
    'New York Knicks': (18.1, 35134, 13, 12, 20, 11),
}

LEGION_BACK_TO_BACKS = {
    'Brooklyn Nets': 16, 'Boston Celtics': 16, 'Cleveland Cavaliers': 16, 'Dallas Mavericks': 16,
    'New Orleans Pelicans': 16, 'Chicago Bulls': 15, 'Detroit Pistons': 15, 'Golden State Warriors': 15,
    'Indiana Pacers': 15, 'Los Angeles Lakers': 15, 'Portland Trail Blazers': 15, 'Toronto Raptors': 15,
    'Atlanta Hawks': 14, 'Denver Nuggets': 14, 'Houston Rockets': 14, 'Milwaukee Bucks': 14, 'Orlando Magic': 14,
    'Sacramento Kings': 14, 'Washington Wizards': 14, 'Charlotte Hornets': 13, 'LA Clippers': 13,
    'Memphis Grizzlies': 13, 'Miami Heat': 13, 'Minnesota Timberwolves': 13, 'New York Knicks': 13,
    'Oklahoma City Thunder': 13, 'Philadelphia 76ers': 13, 'Phoenix Suns': 13, 'San Antonio Spurs': 13,
    'Utah Jazz': 13,
}

# hardest first, as printed: (team, opponents' combined win percentage over the games left)
LEGION_REMAINING = [
    ('New Orleans Pelicans', .538), ('Sacramento Kings', .523), ('Minnesota Timberwolves', .515),
    ('Chicago Bulls', .514), ('LA Clippers', .513), ('Utah Jazz', .511), ('Portland Trail Blazers', .510),
    ('Los Angeles Lakers', .508), ('San Antonio Spurs', .507), ('Denver Nuggets', .507), ('Brooklyn Nets', .507),
    ('Phoenix Suns', .506), ('Indiana Pacers', .504), ('Memphis Grizzlies', .502), ('Golden State Warriors', .501),
    ('Charlotte Hornets', .500), ('Toronto Raptors', .499), ('Oklahoma City Thunder', .499),
    ('Dallas Mavericks', .499), ('Houston Rockets', .497), ('Milwaukee Bucks', .494), ('New York Knicks', .494),
    ('Washington Wizards', .491), ('Miami Heat', .491), ('Orlando Magic', .490), ('Boston Celtics', .487),
    ('Cleveland Cavaliers', .474), ('Atlanta Hawks', .473), ('Philadelphia 76ers', .469), ('Detroit Pistons', .466),
]

YAHOO_MILES = {
    'New Orleans Pelicans': 55529, 'San Antonio Spurs': 53947, 'Utah Jazz': 49289, 'Sacramento Kings': 48637,
    'Denver Nuggets': 47924, 'Miami Heat': 47889, 'LA Clippers': 47451, 'Minnesota Timberwolves': 47310,
    'Houston Rockets': 46396, 'Portland Trail Blazers': 46329, 'Memphis Grizzlies': 46097,
    'Golden State Warriors': 45659, 'Oklahoma City Thunder': 44789, 'Dallas Mavericks': 44776,
    'Phoenix Suns': 44640, 'Los Angeles Lakers': 43717, 'Orlando Magic': 43532, 'Milwaukee Bucks': 42348,
    'Philadelphia 76ers': 41320, 'Boston Celtics': 41283, 'Cleveland Cavaliers': 39351, 'Brooklyn Nets': 37596,
    'Indiana Pacers': 37248, 'Atlanta Hawks': 37092, 'Charlotte Hornets': 36969, 'Detroit Pistons': 36380,
    'Chicago Bulls': 36230, 'Washington Wizards': 35744, 'Toronto Raptors': 35455, 'New York Knicks': 35134,
}

# team: (back-to-backs with the second game on the road, with both games on the road,
#        longest road trip in games, longest homestand in games), from Legion Report's back-to-backs page
LEGION_ROAD_AND_HOME = {
    'Brooklyn Nets': (9, 7, 5, 7), 'Boston Celtics': (8, 8, 6, 7), 'Cleveland Cavaliers': (9, 4, 6, 4),
    'Dallas Mavericks': (9, 8, 5, 4), 'New Orleans Pelicans': (10, 7, 7, 5), 'Chicago Bulls': (7, 4, 4, 6),
    'Detroit Pistons': (7, 4, 4, 4), 'Golden State Warriors': (9, 5, 6, 7), 'Indiana Pacers': (8, 7, 5, 5),
    'Los Angeles Lakers': (6, 5, 7, 5), 'Portland Trail Blazers': (6, 6, 6, 7), 'Toronto Raptors': (9, 6, 6, 6),
    'Atlanta Hawks': (7, 3, 6, 7), 'Denver Nuggets': (8, 4, 6, 7), 'Houston Rockets': (7, 6, 5, 5),
    'Milwaukee Bucks': (7, 3, 5, 6), 'Orlando Magic': (10, 6, 5, 7), 'Sacramento Kings': (9, 8, 5, 7),
    'Washington Wizards': (7, 3, 5, 6), 'Charlotte Hornets': (8, 5, 6, 5), 'LA Clippers': (5, 4, 6, 5),
    'Memphis Grizzlies': (7, 5, 4, 8), 'Miami Heat': (7, 5, 5, 5), 'Minnesota Timberwolves': (8, 5, 5, 8),
    'New York Knicks': (5, 3, 7, 5), 'Oklahoma City Thunder': (6, 4, 4, 7), 'Philadelphia 76ers': (7, 3, 5, 4),
    'Phoenix Suns': (8, 4, 6, 7), 'San Antonio Spurs': (9, 6, 6, 5), 'Utah Jazz': (8, 4, 5, 6),
}

# number of flights in the season, from the Yahoo Sports table
YAHOO_FLIGHTS = {
    'New Orleans Pelicans': 59, 'San Antonio Spurs': 58, 'Utah Jazz': 59, 'Sacramento Kings': 57,
    'Denver Nuggets': 57, 'Miami Heat': 56, 'LA Clippers': 57, 'Minnesota Timberwolves': 57, 'Houston Rockets': 56,
    'Portland Trail Blazers': 51, 'Memphis Grizzlies': 61, 'Golden State Warriors': 53, 'Oklahoma City Thunder': 57,
    'Dallas Mavericks': 57, 'Phoenix Suns': 55, 'Los Angeles Lakers': 52, 'Orlando Magic': 56, 'Milwaukee Bucks': 60,
    'Philadelphia 76ers': 62, 'Boston Celtics': 57, 'Cleveland Cavaliers': 60, 'Brooklyn Nets': 56,
    'Indiana Pacers': 59, 'Atlanta Hawks': 56, 'Charlotte Hornets': 58, 'Detroit Pistons': 58, 'Chicago Bulls': 58,
    'Washington Wizards': 55, 'Toronto Raptors': 56, 'New York Knicks': 55,
}


def full_name(short):
    """Resolve a site's short team name (Mavericks, Trail Blazers, LA, Golden State) to the schedule's full name."""
    special = {'LA': 'LA Clippers', 'LA Lakers': 'Los Angeles Lakers'}
    if short in special:
        return special[short]
    matches = [t for t in HOOPS_MENU if t.endswith(' ' + short) or t.startswith(short + ' ')]
    assert len(matches) == 1, (short, matches)
    return matches[0]


# Power Rankings Guru, updated Oct 31 2026 4:35 AM ET: (rank as printed, team, average opponent rank; lower is harder)
PRG_REMAINING = [
    (1, 'Grizzlies', 14.4), (2, 'Jazz', 14.5), (3, 'Pelicans', 14.7), (4, 'Kings', 14.8), (5, 'Pacers', 14.8),
    (6, 'Nets', 14.9), (7, 'Trail Blazers', 14.9), (8, 'Wizards', 15.0), (9, 'Bucks', 15.1), (10, 'Raptors', 15.2),
    (11, 'Timberwolves', 15.2), (12, 'Lakers', 15.2), (13, 'Hornets', 15.3), (14, 'Bulls', 15.3),
    (15, 'Mavericks', 15.5), (16, 'Nuggets', 15.6), (17, 'Warriors', 15.7), (18, 'Clippers', 15.7),
    (19, 'Suns', 15.8), (20, 'Heat', 15.8), (21, 'Cavaliers', 15.8), (22, 'Rockets', 15.9), (23, 'Spurs', 16.1),
    (24, 'Celtics', 16.1), (25, 'Magic', 16.1), (26, 'Knicks', 16.2), (27, '76ers', 16.2), (28, 'Hawks', 16.3),
    (29, 'Pistons', 16.4), (30, 'Thunder', 16.5),
]
PRG_PLAYED = [
    (1, 'Mavericks', 9.7), (2, 'Magic', 10.4), (3, 'Clippers', 10.6), (4, 'Suns', 10.8), (5, 'Hawks', 11.5),
    (6, 'Knicks', 11.7), (7, 'Nets', 11.8), (8, '76ers', 11.8), (9, 'Warriors', 12.2), (10, 'Pistons', 13.0),
    (11, 'Bulls', 13.3), (12, 'Thunder', 13.6), (13, 'Heat', 13.8), (14, 'Rockets', 15.3), (15, 'Jazz', 15.6),
    (16, 'Kings', 16.0), (17, 'Timberwolves', 16.3), (18, 'Spurs', 16.8), (19, 'Wizards', 16.8), (20, 'Nuggets', 17.0),
    (21, 'Celtics', 17.4), (21, 'Cavaliers', 17.4), (23, 'Raptors', 18.4), (24, 'Trail Blazers', 19.0),
    (24, 'Bucks', 19.0), (26, 'Pelicans', 19.6), (27, 'Hornets', 19.8), (28, 'Lakers', 20.2), (29, 'Pacers', 20.8),
    (30, 'Grizzlies', 23.8),
]

# CraftedNBA, last updated 10/31/2026: team: (schedule difficulty so far, remaining schedule difficulty);
# both are relative to an average schedule (0), positive is tougher, and the remaining figure adjusts for venue and rest
CRAFTED_NBA = {
    'Dallas': (2.77, 0.01), 'New York': (2.61, -0.09), 'Brooklyn': (1.92, 0.17), 'Clippers': (1.89, 0.00),
    'Golden State': (1.71, -0.19), 'Hawks': (1.61, -0.46), 'Bulls': (1.28, 0.13), 'Pelicans': (1.18, 0.42),
    'Pistons': (1.07, -0.50), 'Magic': (1.04, -0.27), 'Suns': (0.86, 0.01), 'Timberwolves': (0.72, 0.06),
    'Nuggets': (0.55, 0.03), '76ers': (0.15, -0.27), 'Thunder': (-0.03, -0.30), 'Cavaliers': (-0.21, -0.33),
    'Spurs': (-0.28, -0.08), 'Bucks': (-0.52, 0.10), 'Lakers': (-0.56, 0.08), 'Wizards': (-0.75, 0.13),
    'Celtics': (-0.89, -0.42), 'Kings': (-1.43, 0.49), 'Hornets': (-1.44, 0.29), 'Rockets': (-1.50, -0.19),
    'Trail Blazers': (-1.56, 0.35), 'Pacers': (-1.61, 0.08), 'Heat': (-1.80, -0.23), 'Grizzlies': (-2.15, 0.49),
    'Jazz': (-2.21, 0.46), 'Raptors': (-2.44, 0.05),
}

# ESPN RPI page, strength of schedule so far, hardest first: (team, SOS)
ESPN_RPI_SOS = [
    ('Dallas', .659), ('Houston', .645), ('Golden State', .608), ('Phoenix', .601), ('Atlanta', .583),
    ('Utah', .582), ('New York', .574), ('San Antonio', .548), ('Miami', .547), ('Oklahoma City', .542),
    ('Orlando', .531), ('Philadelphia', .526), ('Detroit', .523), ('Portland', .518), ('Cleveland', .515),
    ('Memphis', .501), ('Brooklyn', .496), ('Minnesota', .488), ('LA Lakers', .481), ('Milwaukee', .478),
    ('LA', .467), ('Charlotte', .458), ('Chicago', .443), ('Toronto', .437), ('Denver', .433), ('Sacramento', .432),
    ('Washington', .424), ('Boston', .398), ('Indiana', .372), ('New Orleans', .267),
]

SOURCES.update({
    'prg': {
        'name': 'Power Rankings Guru',
        'url': 'https://powerrankingsguru.com/nba/strength-of-schedule',
        'measures': 'Average current power rank of opponents, for games remaining (looks ahead) and games played.',
    },
    'crafted': {
        'name': 'CraftedNBA',
        'url': 'https://craftednba.com/strength-of-schedule',
        'measures': 'Opponent strength from player-minutes ratings, with home court, altitude and back-to-back '
                    'adjustments; remaining and so-far difficulty relative to an average schedule.',
    },
    'espn_rpi': {
        'name': 'ESPN RPI',
        'url': 'https://www.espn.com/nba/stats/rpi/_/sort/SOS',
        'measures': "Strength of schedule so far: opponents' win percentage and their opponents' win percentage.",
    },
})


# How each site appears to calculate its ranking, from its own description and from reproducing its published
# numbers (see analysis/reverse_engineer.py). Shown on the dashboard.
SOURCE_METHODS = [
    {
        'source': 'Hoops Menu',
        'measures': 'Travel and rest, whole season',
        'calculation': 'Five measures (miles, back-to-backs, three-in-four stretches, time-zone crossings, '
                       'back-to-backs against a rested opponent), each scaled 0 to 100 across the league, then '
                       'averaged with equal weight. No opponent quality.',
        'reproduced': 'Yes, from their own columns. Remaining differences look like rounding.',
    },
    {
        'source': 'Legion Report',
        'measures': 'Opponent quality, games left',
        'calculation': "For every game still to play, add the opponent's current wins and losses. Teams are ranked "
                       'by the resulting opponent win percentage.',
        'reproduced': 'Yes, exactly, for every team.',
    },
    {
        'source': 'Power Rankings Guru',
        'measures': 'Opponent quality, games left and games played',
        'calculation': "Opponent win percentage is the plain average of opponents' win percentages. Opponent rating "
                       "is the average of opponents' Elo ratings, with road games counting the opponent as stronger "
                       'and home games as weaker. Power rank is the order of Elo ratings. Teams are ranked by '
                       'average opponent rank.',
        'reproduced': 'Win percentage and rank, to rounding. Elo, once a venue adjustment of roughly 60 points each '
                      'way is fitted. Not the Elo ratings themselves.',
    },
    {
        'source': 'CraftedNBA',
        'measures': 'Opponent quality with venue and rest adjustments',
        'calculation': 'Difficulty relative to an average schedule. Opponent strength blends a projected rating '
                       "(built from players' ratings and minutes) with adjusted net rating. Adds home court, altitude "
                       'and back-to-back adjustments.',
        'reproduced': 'Partly. The opponent blend, about 60 percent projected rating and 40 percent adjusted net '
                      'rating, explains nearly all the variation. The adjustments are too small to separate.',
    },
    {
        'source': 'ESPN RPI',
        'measures': 'Opponent quality, games played',
        'calculation': "RPI is 25 percent own win percentage, 50 percent opponents' win percentage and 25 percent "
                       "opponents' opponents' win percentage. Its strength of schedule works out to two parts "
                       "opponents' win percentage and one part opponents' opponents', divided by three.",
        'reproduced': 'The RPI to schedule-strength relationship, yes. The schedule-strength figure itself, not '
                      'exactly, because the real RPI drops each opponent\'s game against the team.',
    },
    {
        'source': 'Yahoo Sports',
        'measures': 'Travel miles and flights',
        'calculation': 'Estimated flight distance between arenas plus a margin for weather. Flights are the trips '
                       'between different cities, including the trip to the first game.',
        'reproduced': 'Closely. Miles agree within a few hundred per team; flights run about one lower on our side.',
    },
    {
        'source': 'This dashboard',
        'measures': "Wins lost to the schedule: opponents, rest, travel and the rest of each game's situation",
        'calculation': "Each game's win probability for a league-average team comes from point effects measured on "
                       "ten seasons of results (home court, back-to-backs, distance, time zones, three games in four "
                       "nights, altitude), with team strength fitted separately for every team and season. Opponents' "
                       "strength is last season's fitted rating scaled by the share that carried over from year to "
                       "year, measured against an even spread of opponents. Wins lost is the sum over the season of "
                       "the drop from an even game. Noisy effects are pulled toward zero.",
        'reproduced': 'Not applicable.',
    },
]
