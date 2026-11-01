# NBA schedule load, 2026–27

How many wins does each team's schedule cost, or give back? This project turns the 2026–27 NBA schedule into one
number per team, **schedule load**, measured in wins for a league-average team. Positive is harder.

It started as a travel-distance count and turned into a strength-of-schedule model. The effects of rest, travel,
time zones and altitude are not guessed. They are measured from ten seasons of results.

**Live dashboard: https://jeffreymelzer.github.io/nba-schedule-load/**

The dashboard is a static page in [`docs/`](docs/). To run it locally, use `python -m http.server --directory docs`.

## What it found

- **The spread is small.** Minnesota has the heaviest schedule (about 0.7 wins lost) and Denver the lightest
  (about 1.2 wins gained). The 90% ranges of most teams overlap, so only 16 of 30 loads are clearly away from zero.
- **The second night of a back-to-back is the costly part.** It is worth about 1.8 points of margin (1.6 after
  shrinking toward zero). Travelling east and a third game in four nights cost about half a point each.
- **Distance on its own does not matter.** Once back-to-backs are counted, a thousand extra miles is worth
  about +0.1 ± 0.3 points, which is no effect.
- **Altitude is the least certain input.** It is measured from only two teams' home games (Denver and Utah) and
  cannot be separated from those teams simply being strong at home. The dashboard has a switch that leaves it out
  everywhere.
- **Better teams face weaker opponents, but the total load barely follows.** Last season's win percentage has a
  correlation of −0.50 with opponent strength, measured against an even schedule. With total schedule load it is
  −0.27, which is within the noise for 30 teams. Rest and travel counts show no link.

## How it works

1. **Collect games.** The schedule comes from an ECAL calendar; results and standings come from ESPN.
2. **Measure the effects.** Every game gives one equation: the home team's margin is home court, plus the
   difference in team strength, plus what each situation (back-to-back, rest, miles, time zones, three games in four
   nights, a visit to altitude) is worth times the home team's value minus the visitor's. Strength is fitted
   separately for each team and season, so strong teams' wins do not look like rest effects. Home court is fitted
   for each season and averaged, leaving out 2020–21, when arenas were mostly empty.
3. **Pool noisy effects.** Estimates are pulled toward zero by an amount that depends on how noisy each is, so one
   uncertain factor cannot swing a team's rank on its own.
4. **Apply them to the coming schedule.** Opponents are rated with last season's fitted ratings, scaled by how much
   of a rating carries over from one season to the next (about 0.57). Each game's win chance comes from its expected
   margin, and schedule load is the sum of (0.5 − win chance) over the season for a league-average team.
5. **Report the uncertainty.** The 90% ranges and rank ranges come from 400 draws of the measured effects.

Schedule load does not predict how a team will perform. It measures the schedule, not the team.

The dashboard also compares the ranking with other sites. [`analysis/reverse_engineer.py`](analysis/reverse_engineer.py)
reproduces several of their published numbers to work out how they are calculated.

## Running it

```
pip install -r requirements.txt
python -X utf8 main.py          # reads data/, writes docs/data/*.json and a few charts in output/
python -m pytest                # tests
python -m http.server --directory docs
```

- `data/schedule_2026_27.json` is the games list. To refresh it, set `NBA_SCHEDULE_URL` to an ECAL calendar
  subscription (an https link ending in `.ics`) or an NBA.com schedule JSON link and run `main.py`.
- `data/results_<year>.json` and `data/standings_2025_26.json` are ESPN responses that `main.py` fetches and caches
  on the first run, which takes a few minutes and needs a network connection. They are not in the repository. Delete
  one to fetch it again.
- `python -m utils.basemap_export` rebuilds the map outline in `docs/data/basemap.json` (needs cartopy).

## Layout

| Path | What it holds |
| --- | --- |
| `modules/calibrate.py` | the regression for home court, rest and travel effects, shrinkage and rating carryover |
| `modules/expected_wins.py` | schedule load, its components and its uncertainty |
| `modules/travel.py`, `modules/strength.py` | distances, back-to-backs, flights, homestands and other counts |
| `modules/results.py`, `modules/standings.py` | ESPN data |
| `modules/external_sources.py`, `modules/compare.py` | other sites' figures and the comparison with them |
| `docs/` | the website: `index.html`, `app.js`, `dash.js`, `data/` |

## Caveats

- Figures from other sites in `modules/external_sources.py` were copied by hand from their pages on 31 October 2026
  and have not been independently checked.
- The calendar does not yet include games whose teams are still to be decided, such as the NBA Cup knockout rounds.
- The back-to-back effect looks larger in recent seasons (about −1.1 points in the earlier five seasons and −2.5 in
  the latest five), possibly because stars now rest on the second night. The model uses one effect for all ten seasons.
- ESPN's endpoints are public but unofficial and may change.

An independent project, not affiliated with the NBA, ESPN or any site named here. The code is released under the
[MIT licence](LICENSE); the licence does not cover ESPN's data or the other sites' figures.
