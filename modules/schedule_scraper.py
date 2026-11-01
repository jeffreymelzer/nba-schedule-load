"""
This script is used to load the NBA schedule from an ECAL .ics calendar (local file or URL),
from the NBA.com schedule JSON, or from a games list written by save_games.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

import requests

# venues whose location string has no state/country part
INTERNATIONAL_CITIES = {'Manchester': 'UK'}


class ScheduleScraper:
    """
    This class loads the season schedule into self.schedule_lookup:
    {team name: [(utc datetime, arena city, arena state), ...]} sorted by date.
    """

    def __init__(self, source):
        self.schedule_lookup = defaultdict(list)
        self.cities = set()
        self.games = []
        self.source = source

    def run(self):

        text = self.read_source()

        if self.source.lower().split('?')[0].endswith('.ics'):
            self.parse_ics(text)
        else:
            data = json.loads(text)
            if isinstance(data, list):
                self.parse_games(data)
            else:
                self.parse_nba_json(data)

        for team_schedule in self.schedule_lookup.values():
            team_schedule.sort()

    def save_games(self, path):
        """Write the games as a plain list, so the schedule can be shared without the calendar it came from."""
        rows = [{**g, 'datetime': g['datetime'].isoformat()} for g in self.games]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)

    def parse_games(self, rows):

        for game in rows:
            self.add_game_to_lookup(datetime.fromisoformat(game['datetime']), game['city'], game['state'],
                                    game['away'], game['home'])

    def read_source(self):

        if os.path.exists(self.source):
            with open(self.source, encoding='utf-8') as f:
                return f.read()

        response = requests.get(self.source, timeout=30)
        response.raise_for_status()
        return response.text

    def parse_ics(self, text):

        # undo RFC 5545 line folding
        text = text.replace('\r\n', '\n').replace('\n ', '')

        for event in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', text, re.S):
            fields = dict(re.findall(r'^([A-Z-]+)[^:\n]*:(.*)$', event, re.M))
            summary = fields.get('SUMMARY', '')
            location = fields.get('LOCATION', '').replace('\\,', ',')

            # ignore non-game events and games without a venue yet
            if ' @ ' not in summary or location in ('', 'TBC'):
                continue
            # ignore preseason
            if 'Preseason' in fields.get('DESCRIPTION', ''):
                continue

            away_team, home_team = summary.split(' @ ')
            away_team = away_team.split('🏀')[-1].strip()
            # ignore placeholder games (e.g. the NBA Cup final) whose teams are not known yet
            if 'TBD' in (away_team, home_team.strip()):
                continue

            parts = [p.strip() for p in location.split(',')]
            arena_city = parts[-2] if len(parts) >= 3 else parts[-1]
            arena_state = parts[-1] if len(parts) >= 3 else INTERNATIONAL_CITIES.get(parts[-1], '')

            date_time = datetime.strptime(fields['DTSTART'], '%Y%m%dT%H%M%SZ')
            self.add_game_to_lookup(date_time, arena_city, arena_state, away_team, home_team.strip())

    def parse_nba_json(self, r):

        for game_date in r['leagueSchedule']['gameDates']:
            for game in game_date['games']:
                # ignore preseason games
                if game['weekNumber'] == 0:
                    continue
                # ignore tournament games
                if game['gameStatusText'] == 'TBD':
                    continue

                date_time = datetime.fromisoformat(game['gameDateTimeUTC'].replace('Z', '+00:00'))
                date_time = date_time.astimezone(timezone.utc).replace(tzinfo=None)
                away_team = ' '.join([game['awayTeam']['teamCity'], game['awayTeam']['teamName']])
                home_team = ' '.join([game['homeTeam']['teamCity'], game['homeTeam']['teamName']])
                self.add_game_to_lookup(date_time, game['arenaCity'], game['arenaState'], away_team, home_team)

    def add_game_to_lookup(self, date_time, arena_city, arena_state, away_team, home_team):

        self.cities.add(', '.join(filter(None, [arena_city, arena_state])))
        self.games.append({'datetime': date_time, 'city': arena_city, 'state': arena_state,
                           'away': away_team, 'home': home_team})

        for team in (away_team, home_team):
            self.schedule_lookup[team].append((date_time, arena_city, arena_state))
