"""
Last season's results, used as the measure of team strength.
"""

import json
import os

import requests

ESPN_STANDINGS_URL = 'https://site.api.espn.com/apis/v2/sports/basketball/nba/standings'


def fetch_standings(season_end_year, cache_path):
    """
    Return {team name: {wins, losses, win_pct, net_rating}} for the season ending in season_end_year
    (2026 is 2025-26). The ESPN answer is cached so reruns do not hit the network.
    """
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    response = requests.get(ESPN_STANDINGS_URL, params={'season': season_end_year}, timeout=30)
    response.raise_for_status()
    answer = response.json()

    teams = {}
    for conference in answer['children']:
        for entry in conference['standings']['entries']:
            stats = {s['name']: s['value'] for s in entry['stats'] if 'value' in s}
            teams[entry['team']['displayName']] = {
                'wins': int(stats['wins']),
                'losses': int(stats['losses']),
                'win_pct': round(stats['winPercent'], 3),
                'net_rating': round(stats['differential'], 1),
            }

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(teams, f, indent=1)

    return teams
