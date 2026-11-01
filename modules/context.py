"""
The situation each team plays a game in: rest, travel, time zone, altitude, schedule density.
The same features are built for past seasons (to measure what they cost) and for the coming schedule (to apply it).
"""

from collections import defaultdict

from modules.travel import city_key, get_city_distance, local_day

FEATURES = ['b2b', 'b2b_road', 'long_rest', 'miles_k', 'tz_east', 'tz_west', 'three_in_four', 'altitude_visit']

ALTITUDE_CITIES = {'Denver, CO', 'Salt Lake City, UT'}
# venues outside the US and Canada, where no team is at home
INTERNATIONAL_STATES = {'Mexico City': 'MX', 'Paris': 'FR', 'Berlin': 'DE', 'London': 'UK', 'Manchester': 'UK'}
LONG_REST_DAYS = 3


def normalize_game(game):
    """Fill the state of international venues so the city key matches cities.csv; mark them neutral."""
    state = game.get('state') or INTERNATIONAL_STATES.get(game['city'], '')
    neutral = bool(game.get('neutral')) or state in set(INTERNATIONAL_STATES.values())
    return {**game, 'state': state, 'neutral': neutral}


def build_game_contexts(games, city_lookup, tz_lookup):
    """
    Return one dict per game (in date order) with the contexts of its two teams:
    {'game': game, 'home': {feature: value}, 'away': {feature: value}}.
    """
    games = [normalize_game(g) for g in sorted(games, key=lambda g: g['datetime'])]
    by_team = defaultdict(list)
    for index, game in enumerate(games):
        by_team[game['home']].append((index, 'home'))
        by_team[game['away']].append((index, 'away'))

    contexts = [{'game': g, 'home': None, 'away': None} for g in games]
    for team, appearances in by_team.items():
        previous = None
        days = []
        for position, (index, side) in enumerate(appearances):
            game = games[index]
            here = city_key(game['city'], game['state'])
            day = local_day(game['datetime'], game['city'], game['state'], tz_lookup)
            days.append(day)
            on_road = side == 'away' and not game['neutral']

            rest_days = None if previous is None else (day - previous['day']).days - 1
            shift = 0 if previous is None else tz_lookup[here] - tz_lookup[previous['here']]
            miles = 0 if previous is None or previous['here'] == here else get_city_distance(previous['here'], here, city_lookup)
            back_to_back = rest_days == 0

            contexts[index][side] = {
                'b2b': int(back_to_back),
                'b2b_road': int(back_to_back and on_road),
                'long_rest': int(rest_days is not None and rest_days >= LONG_REST_DAYS),
                'miles_k': miles / 1000,
                'tz_east': max(0, shift),
                'tz_west': max(0, -shift),
                'three_in_four': int(position >= 2 and (day - days[position - 2]).days <= 3),
                'altitude_visit': int(on_road and here in ALTITUDE_CITIES),
            }
            previous = {'day': day, 'here': here}

    return contexts
