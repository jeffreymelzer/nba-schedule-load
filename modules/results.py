"""
Past seasons' game results from ESPN, used to measure what rest, travel and the rest of the schedule cost a team.
"""

import json
import os
from datetime import datetime

import requests

ESPN_TEAM_SCHEDULE_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule'
# ESPN's team ids; each team's schedule lists its games, so every game appears twice
ESPN_TEAM_IDS = list(range(1, 31))


def drop_bubble_games(games):
    """Remove the 2020 restart games played in the Orlando bubble, where no team was really at home or on the road."""
    return [g for g in games if g['city'] != 'Lake Buena Vista']


def fetch_season_results(season_end_year, cache_path):
    """
    Return the finished regular-season games of the season ending in season_end_year (2026 is 2025-26) as
    game dicts: id, datetime (UTC), home, away, home_score, away_score, city, state, neutral.
    The answers are cached so reruns do not hit the network.
    """
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return [{**g, 'datetime': datetime.fromisoformat(g['datetime'])} for g in json.load(f)]

    games = {}
    for team_id in ESPN_TEAM_IDS:
        response = requests.get(ESPN_TEAM_SCHEDULE_URL.format(team_id=team_id),
                                params={'season': season_end_year}, timeout=30)
        response.raise_for_status()
        for event in response.json()['events']:
            competition = event['competitions'][0]
            if competition['status']['type']['name'] != 'STATUS_FINAL' or event['id'] in games:
                continue
            sides = {c['homeAway']: c for c in competition['competitors']}
            venue = competition.get('venue', {}).get('address', {})
            games[event['id']] = {
                'id': event['id'],
                'datetime': datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ'),
                'home': sides['home']['team']['displayName'],
                'away': sides['away']['team']['displayName'],
                'home_score': int(sides['home']['score']['displayValue']),
                'away_score': int(sides['away']['score']['displayValue']),
                'city': venue.get('city', ''),
                'state': venue.get('state', ''),
                'neutral': bool(competition.get('neutralSite')),
            }

    results = sorted(games.values(), key=lambda g: g['datetime'])
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump([{**g, 'datetime': g['datetime'].isoformat()} for g in results], f)

    return results
