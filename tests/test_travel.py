from datetime import datetime

import pytest

from modules.schedule_scraper import ScheduleScraper
from modules.travel import build_city_lookup, build_tz_lookup, check_cities, get_city_distance, summarize_team

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
LOCATION:United Center\\, Chicago\\, IL
DTSTART:20261101T000000Z
SUMMARY:🏀 Charlotte Hornets @ Chicago Bulls
DESCRIPTION:NBA Regular Season
END:VEVENT
BEGIN:VEVENT
LOCATION:TBC
DTSTART:20261102T000000Z
SUMMARY:🏀 Charlotte Hornets @ Chicago Bulls
DESCRIPTION:NBA Regular Season
END:VEVENT
BEGIN:VEVENT
LOCATION:Co-op Live\\, Manchester
DTSTART:20261103T000000Z
SUMMARY:🏀 Orlando Magic @ Memphis Grizzlies
DESCRIPTION:NBA Regular Season
END:VEVENT
END:VCALENDAR
"""


@pytest.fixture
def city_lookup():
    return build_city_lookup('cities.csv')


def test_distance_uses_western_hemisphere(city_lookup):
    assert get_city_distance('Boston, MA', 'Los Angeles, CA', city_lookup) == pytest.approx(2600, abs=60)


def test_us_cities_have_western_longitudes(city_lookup):
    for key, (lat, long) in city_lookup.items():
        if key.split(', ')[-1] not in ('FR', 'UK', 'DE'):
            assert long < 0, key


def test_parse_ics(tmp_path):
    path = tmp_path / 'test.ics'
    path.write_text(ICS, encoding='utf-8')
    scraper = ScheduleScraper(str(path))
    scraper.run()

    assert scraper.schedule_lookup['Charlotte Hornets'] == [(datetime(2026, 11, 1), 'Chicago', 'IL')]
    assert scraper.schedule_lookup['Orlando Magic'][0][1:] == ('Manchester', 'UK')


def test_saved_games_load_back_the_same(tmp_path):
    ics = tmp_path / 'test.ics'
    ics.write_text(ICS, encoding='utf-8')
    scraper = ScheduleScraper(str(ics))
    scraper.run()
    scraper.save_games(str(tmp_path / 'games.json'))
    again = ScheduleScraper(str(tmp_path / 'games.json'))
    again.run()

    assert again.games == scraper.games
    assert again.schedule_lookup == scraper.schedule_lookup
    assert again.cities == scraper.cities


def test_missing_city_raises(city_lookup):
    with pytest.raises(KeyError):
        check_cities({'Nowhere, ZZ'}, city_lookup)


def test_summarize_team_counts_travel_back_to_back(city_lookup):
    games = [
        (datetime(2026, 11, 1, 0), 'Boston', 'MA'),
        (datetime(2026, 11, 2, 0), 'Chicago', 'IL'),
        (datetime(2026, 11, 2, 23), 'Chicago', 'IL'),
        (datetime(2026, 11, 6, 0), 'Boston', 'MA'),
    ]
    s = summarize_team(games, city_lookup, build_tz_lookup('cities.csv'))

    assert s['back_to_backs'] == 2
    assert s['travel_back_to_backs'] == 1
    assert s['total_miles'] == pytest.approx(2 * get_city_distance('Boston, MA', 'Chicago, IL', city_lookup))
