"""
Travel metrics computed from a team's schedule.
"""

import csv
from datetime import timedelta

import geopy.distance


def city_key(city, state):
    return ', '.join(filter(None, [city, state]))


def build_city_lookup(path):
    """Read cities.csv rows of city, state, lat, long into {'City, ST': (lat, long)}."""
    city_lookup = {}
    with open(path) as f:
        for row in csv.reader(f):
            city_lookup[city_key(row[0].strip(), row[1].strip())] = (float(row[2]), float(row[3]))

    return city_lookup


def build_tz_lookup(path):
    """Read the standard-time UTC offset (fifth column of cities.csv) into {'City, ST': hours}."""
    tz_lookup = {}
    with open(path) as f:
        for row in csv.reader(f):
            tz_lookup[city_key(row[0].strip(), row[1].strip())] = int(row[4])

    return tz_lookup


def local_day(date_time, city, state, tz_lookup):
    """Calendar day of a tip-off at the arena's local time (standard-time offset)."""
    return (date_time + timedelta(hours=tz_lookup[city_key(city, state)])).date()


def is_back_to_back(previous, current, tz_lookup):
    """Two games on consecutive local calendar days; previous and current are (datetime, city, state)."""
    return (local_day(current[0], *current[1:], tz_lookup) - local_day(previous[0], *previous[1:], tz_lookup)).days == 1


def check_cities(cities, city_lookup):
    """Fail loudly instead of silently treating an unknown city as 0 miles."""
    missing = sorted(set(cities) - set(city_lookup))
    if missing:
        raise KeyError(f'cities missing from cities.csv: {missing}')


def get_city_distance(city1, city2, city_lookup):
    return geopy.distance.distance(city_lookup[city1], city_lookup[city2]).miles


def get_legs(team_schedule, city_lookup):
    """Return (miles, hours) between each pair of consecutive games."""
    legs = []
    for previous, current in zip(team_schedule, team_schedule[1:]):
        miles = get_city_distance(city_key(*previous[1:]), city_key(*current[1:]), city_lookup)
        hours = (current[0] - previous[0]).total_seconds() / 3600
        legs.append((miles, hours))

    return legs


def summarize_team(team_schedule, city_lookup, tz_lookup):
    legs = get_legs(team_schedule, city_lookup)
    total_miles = sum(miles for miles, _ in legs)
    back_to_backs = [(m, h) for (m, h), previous, current in zip(legs, team_schedule, team_schedule[1:])
                     if is_back_to_back(previous, current, tz_lookup)]

    return {
        'games': len(team_schedule),
        'total_miles': total_miles,
        'miles_per_game': total_miles / max(len(legs), 1),
        'back_to_backs': len(back_to_backs),
        'travel_back_to_backs': sum(1 for m, _ in back_to_backs if m > 0),
        'longest_trip': max((m for m, _ in legs), default=0),
        'first_game': team_schedule[0][0].date().isoformat(),
        'last_game': team_schedule[-1][0].date().isoformat(),
    }


def team_leg_rows(team, team_schedule, city_lookup, tz_lookup):
    """One row per leg (the trip into each game after the first) with running miles, for the dashboard."""
    rows = []
    cumulative = 0
    for i, (previous, current) in enumerate(zip(team_schedule, team_schedule[1:]), start=1):
        miles = get_city_distance(city_key(*previous[1:]), city_key(*current[1:]), city_lookup)
        hours = (current[0] - previous[0]).total_seconds() / 3600
        cumulative += miles
        rows.append({
            'leg_id': f'{team}|{i}',
            'leg_no': i,
            'team': team,
            'date': current[0].date().isoformat(),
            'from_city': previous[1],
            'to_city': current[1],
            'miles': round(miles),
            'hours': round(hours, 1),
            'back_to_back': is_back_to_back(previous, current, tz_lookup),
            'cum_miles': round(cumulative),
        })

    return rows
