const fmt = d3.format(',');
const fmt1 = d3.format(',.1f');
const dayFmt = d3.utcFormat('%b %-d');
const dayYr = d3.utcFormat('%b %-d, %Y');
const rowsOf = (id) => { const g = dash.data(id); return g.status === 'ok' ? g.data : null; };
const dflt = (rows) => rows.reduce((a, b) => (b.total_miles > a.total_miles ? b : a)).team;
const picked = (rows) => { const p = dash.params().team; return rows.some((r) => r.team === p) ? p : dflt(rows); };
const accent = () => dash.colors[0];

// headline calc: every figure in the header and the tiles
dash.calc('headline', {
  title: 'Headline figures',
  description: 'League-wide extremes and averages worked out from the team summary and the trip list.',
  inputs: ['team_summary', 'team_legs'],
  fn: (team_summary, team_legs) => {
    const by = (key) => team_summary.slice().sort((a, b) => b[key] - a[key]);
    const most = by('total_miles')[0];
    const least = by('total_miles')[team_summary.length - 1];
    const longest = team_legs.reduce((a, b) => (b.miles > a.miles ? b : a), team_legs[0]);
    const sum = (key) => team_summary.reduce((s, r) => s + r[key], 0);
    return [{
      most_team: most.team,
      most_miles: most.total_miles,
      least_team: least.team,
      least_miles: least.total_miles,
      avg_miles: Math.round(sum('total_miles') / team_summary.length),
      gap_miles: most.total_miles - least.total_miles,
      longest_leg_miles: longest.miles,
      longest_leg_team: longest.team,
      longest_leg_route: longest.from_city + ' to ' + longest.to_city,
      avg_travel_b2b: Math.round(10 * sum('travel_back_to_backs') / team_summary.length) / 10,
      first_game: team_summary.map((r) => r.first_game).sort()[0],
      last_game: team_summary.map((r) => r.last_game).sort().reverse()[0],
    }];
  },
});

// league average running total of miles, per game date
dash.calc('league_cum', {
  title: 'League average miles piled up',
  description: 'For each date, the average across teams of the miles travelled so far.',
  inputs: ['team_legs'],
  fn: (team_legs) => {
    const teams = {};
    team_legs.forEach((r) => { (teams[r.team] = teams[r.team] || []).push(r); });
    const names = Object.keys(teams);
    names.forEach((t) => teams[t].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0)));
    const dates = Array.from(new Set(team_legs.map((r) => r.date))).sort();
    const idx = {};
    names.forEach((t) => { idx[t] = 0; });
    const out = [];
    dates.forEach((d) => {
      let total = 0;
      names.forEach((t) => {
        const list = teams[t];
        while (idx[t] < list.length && list[idx[t]].date <= d) idx[t] += 1;
        total += idx[t] ? list[idx[t] - 1].cum_miles : 0;
      });
      out.push({ date: d, avg_cum: Math.round(total / names.length) });
    });
    return out;
  },
});

// figures and words drawn straight from the headline row
const fields = {
  most_team: ['most_team', (v) => v],
  most_miles: ['most_miles', fmt],
  least_team: ['least_team', (v) => v],
  least_miles: ['least_miles', fmt],
  avg_miles: ['avg_miles', fmt],
  gap_miles: ['gap_miles', fmt],
  longest_miles: ['longest_leg_miles', fmt],
  longest_team: ['longest_leg_team', (v) => v],
  longest_route: ['longest_leg_route', (v) => v],
  avg_b2b: ['avg_travel_b2b', fmt1],
  first_game: ['first_game', (v) => dayFmt(new Date(v))],
  last_game: ['last_game', (v) => dayYr(new Date(v))],
};
Object.entries(fields).forEach(([name, [field, f]]) => {
  dash.draw(name, (el) => {
    const rows = rowsOf('headline');
    el.textContent = rows && rows[0] ? f(rows[0][field]) : '—';
  });
});
['sel_name', 'sel_name2', 'sel_name3'].forEach((name) => {
  dash.draw(name, (el) => {
    const rows = rowsOf('team_summary');
    el.textContent = rows ? picked(rows) : '—';
  });
});

dash.draw('sel_rank', (el) => {
  const rows = rowsOf('team_schedule'), summary = rowsOf('team_summary');
  const row = rows && summary ? withAltitudeChoice(rows).find((r) => r.team === picked(summary)) : null;
  el.textContent = row ? fmt(row.difficulty_rank) : '—';
});

dash.draw('teamsel', (sel) => {
  const rows = rowsOf('team_summary');
  sel.replaceChildren(...(rows ? rows.map((r) => r.team).sort().map((t) => new Option(t)) : []));
  if (rows) sel.value = picked(rows);
  sel.onchange = () => dash.setParams({ team: sel.value });
});

// ---- chart helpers
function makeTip(box) {
  const tip = d3.select(box).append('div').attr('class', 'nt-tip').style('display', 'none');
  return {
    show(event, lines) {
      tip.selectAll('div').remove();
      lines.forEach((l) => tip.append('div').text(l));
      const [x, y] = d3.pointer(event, box);
      tip.style('display', 'block');
      const w = tip.node().offsetWidth;
      tip.style('left', Math.max(0, Math.min(x + 12, box.clientWidth - w)) + 'px').style('top', Math.max(0, y - 36) + 'px');
    },
    hide() { tip.style('display', 'none'); },
  };
}
function textWidth(svg, labels) {
  const probe = svg.append('text').attr('class', 'nt-probe').attr('opacity', 0);
  let w = 0;
  labels.forEach((l) => { probe.text(l); w = Math.max(w, probe.node().getComputedTextLength()); });
  probe.remove();
  return w;
}
function startSvg(el, w, h) {
  el.replaceChildren();
  return d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('width', '100%').attr('role', 'img');
}

// ---- bars: season miles per team
dash.draw('bars', (el) => {
  const rows = rowsOf('team_summary');
  if (!rows) { el.textContent = '—'; return; }
  const data = rows.slice().sort((a, b) => b.total_miles - a.total_miles);
  const sel = picked(rows);
  const w = el.clientWidth || 640, rowH = 24, m = { t: 4, r: 52, b: 4 };
  const h = m.t + m.b + rowH * data.length;
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', 'Season miles by team');
  m.l = Math.ceil(textWidth(svg, data.map((d) => d.team))) + 12;
  const x = d3.scaleLinear([0, d3.max(data, (d) => d.total_miles)], [0, Math.max(40, w - m.l - m.r)]);
  const tip = makeTip(el);
  const g = svg.selectAll('g.row').data(data).join('g').attr('class', 'row').attr('transform', (d, i) => `translate(0,${m.t + i * rowH})`);
  g.append('text').attr('x', m.l - 8).attr('y', rowH / 2).attr('dy', '0.32em').attr('text-anchor', 'end')
    .attr('class', (d) => (d.team === sel ? 'nt-strong' : null)).text((d) => d.team);
  g.append('rect').attr('x', m.l).attr('y', 4).attr('height', rowH - 8).attr('rx', 2)
    .attr('width', (d) => x(d.total_miles)).style('fill', (d) => (d.team === sel ? accent() : 'var(--chart-muted)'));
  g.append('text').attr('x', (d) => m.l + x(d.total_miles) + 6).attr('y', rowH / 2).attr('dy', '0.32em').text((d) => fmt(d.total_miles));
  g.append('rect').attr('class', 'nt-hit').attr('width', w).attr('height', rowH)
    .on('click', (e, d) => dash.setParams({ team: d.team }))
    .on('mousemove', (e, d) => tip.show(e, [d.team, fmt(d.total_miles) + ' miles', fmt(d.miles_per_game) + ' per game', d.travel_back_to_backs + ' back-to-backs with travel']))
    .on('mouseleave', tip.hide);
});

// ---- scatter: miles against travel back-to-backs
dash.draw('scatter', (el) => {
  const rows = rowsOf('team_summary');
  if (!rows) { el.textContent = '—'; return; }
  const sel = picked(rows);
  const w = el.clientWidth || 480, h = 340, m = { t: 14, r: 20, b: 48, l: 48 };
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', 'Season miles against back-to-backs with travel, one dot per team');
  const [lo, hi] = d3.extent(rows, (d) => d.total_miles);
  const x = d3.scaleLinear([lo - 2000, hi + 2000], [m.l, w - m.r]).nice();
  const y = d3.scaleLinear([0, d3.max(rows, (d) => d.travel_back_to_backs) + 1], [h - m.b, m.t]).nice();
  svg.append('g').attr('class', 'tick-grid').selectAll('line').data(y.ticks(5)).join('line')
    .attr('class', 'nt-grid-line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(w < 420 ? 3 : 5).tickFormat(fmt));
  const ya = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
  [xa, ya].forEach((a) => a.attr('font-size', null).attr('font-family', null));
  svg.append('text').attr('x', (m.l + w - m.r) / 2).attr('y', h - 8).attr('text-anchor', 'middle').text('Season miles');
  svg.append('text').attr('transform', `translate(12,${(m.t + h - m.b) / 2}) rotate(-90)`).attr('text-anchor', 'middle').text('Back-to-backs with travel');
  const tip = makeTip(el);
  const ordered = rows.slice().sort((a, b) => (a.team === sel) - (b.team === sel));
  svg.selectAll('circle').data(ordered).join('circle')
    .attr('cx', (d) => x(d.total_miles)).attr('cy', (d) => y(d.travel_back_to_backs))
    .attr('r', (d) => (d.team === sel ? 7 : 5)).style('cursor', 'pointer')
    .style('fill', (d) => (d.team === sel ? accent() : 'var(--chart-muted)')).style('fill-opacity', (d) => (d.team === sel ? 1 : 0.75))
    .style('stroke', 'var(--color-panel)').style('stroke-width', 1.5)
    .on('click', (e, d) => dash.setParams({ team: d.team }))
    .on('mousemove', (e, d) => tip.show(e, [d.team, fmt(d.total_miles) + ' miles', d.travel_back_to_backs + ' back-to-backs with travel']))
    .on('mouseleave', tip.hide);
  const s = rows.find((d) => d.team === sel);
  const sx = x(s.total_miles), anchor = sx > w - 140 ? 'end' : 'start';
  svg.append('text').attr('class', 'nt-strong').attr('x', sx + (anchor === 'end' ? -10 : 10)).attr('y', y(s.travel_back_to_backs) - 10).attr('text-anchor', anchor).text(s.team);
});

// ---- running total of miles, selected team against the league average
dash.draw('cum', (el) => {
  const rows = rowsOf('team_summary'), legs = rowsOf('team_legs'), avg = rowsOf('league_cum');
  if (!rows || !legs || !avg) { el.textContent = '—'; return; }
  const sel = picked(rows);
  const parse = (s) => new Date(s + 'T00:00:00Z');
  const mine = legs.filter((r) => r.team === sel).sort((a, b) => (a.date < b.date ? -1 : 1))
    .map((r) => ({ t: parse(r.date), v: r.cum_miles }));
  const lg = avg.map((r) => ({ t: parse(r.date), v: r.avg_cum }));
  if (!mine.length || !lg.length) { el.textContent = '—'; return; }
  const w = el.clientWidth || 480, h = 340, m = { t: 14, b: 28, l: 54 };
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', `Running total of miles for ${sel} and the league average`);
  const endA = `${sel} ${fmt(mine[mine.length - 1].v)}`, endB = `League avg ${fmt(lg[lg.length - 1].v)}`;
  m.r = Math.min(w * 0.4, Math.ceil(textWidth(svg, [endA, endB])) + 12);
  const x = d3.scaleUtc([d3.min(lg, (d) => d.t), d3.max(lg, (d) => d.t)], [m.l, w - m.r]);
  const y = d3.scaleLinear([0, d3.max([...mine, ...lg], (d) => d.v)], [h - m.b, m.t]).nice();
  svg.append('g').selectAll('line').data(y.ticks(5)).join('line').attr('class', 'nt-grid-line')
    .attr('x1', m.l).attr('x2', w - m.r).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(w < 420 ? 3 : 5).tickFormat(d3.utcFormat('%b')));
  const ya = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(fmt));
  [xa, ya].forEach((a) => a.attr('font-size', null).attr('font-family', null));
  const line = d3.line().x((d) => x(d.t)).y((d) => y(d.v)).curve(d3.curveStepAfter);
  svg.append('path').datum(lg).attr('d', line).style('fill', 'none').style('stroke', 'var(--chart-reference)').style('stroke-width', 2).style('stroke-dasharray', '5 4');
  svg.append('path').datum(mine).attr('d', line).style('fill', 'none').style('stroke', accent()).style('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
  // end labels, nudged apart when the lines finish close together
  let ya1 = y(mine[mine.length - 1].v), ya2 = y(lg[lg.length - 1].v);
  if (Math.abs(ya1 - ya2) < 16) { const mid = (ya1 + ya2) / 2, d = ya1 <= ya2 ? -8 : 8; ya1 = mid + d; ya2 = mid - d; }
  svg.append('text').attr('class', 'nt-strong').attr('x', w - m.r + 6).attr('y', ya1).attr('dy', '0.32em').text(endA);
  svg.append('text').attr('x', w - m.r + 6).attr('y', ya2).attr('dy', '0.32em').text(endB);
});

// ---- longest trips for the selected team
dash.draw('legsbody', (tb) => {
  const rows = rowsOf('team_summary'), legs = rowsOf('team_legs');
  if (!rows || !legs) { tb.replaceChildren(); return; }
  const sel = picked(rows);
  const top = legs.filter((r) => r.team === sel).sort((a, b) => b.miles - a.miles).slice(0, 8);
  tb.replaceChildren(...top.map((r) => {
    const tr = document.createElement('tr');
    tr.dataset.key = r.leg_id;
    [dayFmt(new Date(r.date)), r.from_city, r.to_city, fmt(r.miles), fmt1(r.hours)].forEach((v, i) => {
      const td = document.createElement('td');
      if (i === 1 || i === 2) td.className = 'nt-left';
      td.textContent = v;
      tr.append(td);
    });
    return tr;
  }));
});

// ---- route map: the selected team's season, scrubbed or played game by game
const FRAME = [-128, 17, -64, 52];
const albers = (lon, lat) => {
  const rad = Math.PI / 180, n = (Math.sin(29.5 * rad) + Math.sin(45.5 * rad)) / 2;
  const c = Math.cos(29.5 * rad) ** 2 + 2 * n * Math.sin(29.5 * rad);
  const rho = (l) => Math.sqrt(c - 2 * n * Math.sin(l * rad)) / n;
  const theta = n * (lon + 96) * rad;
  return [rho(lat) * Math.sin(theta), rho(37.5) - rho(lat) * Math.cos(theta)];
};
const frameEdge = [];
for (let lo = FRAME[0]; lo <= FRAME[2]; lo += 2) frameEdge.push([lo, FRAME[1]], [lo, FRAME[3]]);
for (let la = FRAME[1]; la <= FRAME[3]; la += 2) frameEdge.push([FRAME[0], la], [FRAME[2], la]);
const frameXY = frameEdge.map(([lo, la]) => albers(lo, la));
const FX = d3.extent(frameXY, (d) => d[0]), FY = d3.extent(frameXY, (d) => d[1]);

let step = 1, stepTeam = null, stepMax = 1, timer = null;
function stopPlay() {
  if (timer) { clearInterval(timer); timer = null; }
  document.querySelectorAll('#nt-play').forEach((b) => b.setAttribute('aria-pressed', 'false'));
}
function stepFor(team, max) {
  if (stepTeam !== team) { stepTeam = team; step = max; stopPlay(); }
  stepMax = max;
  step = Math.max(1, Math.min(step, max));
  return step;
}
function routeOf(legs, team) {
  const mine = legs.filter((r) => r.team === team).sort((a, b) => a.leg_no - b.leg_no);
  if (!mine.length) return [];
  return [{ city: mine[0].from_city, date: null, cum: 0 }, ...mine.map((r) => ({ city: r.to_city, date: r.date, cum: r.cum_miles }))];
}
const refreshRoute = () => { dash.draw('map'); dash.draw('maplabel'); dash.draw('stepper'); };

dash.draw('stepper', (el) => {
  const rows = rowsOf('team_summary'), legs = rowsOf('team_legs');
  if (!rows || !legs) return;
  const stops = routeOf(legs, picked(rows));
  el.min = 1;
  el.max = Math.max(1, stops.length);
  el.value = stepFor(picked(rows), Math.max(1, stops.length));
  el.oninput = () => { step = +el.value; stopPlay(); dash.draw('map'); dash.draw('maplabel'); };
});
document.querySelectorAll('#nt-play').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (timer) { stopPlay(); return; }
    if (step >= stepMax) step = 1;
    btn.setAttribute('aria-pressed', 'true');
    refreshRoute();
    timer = setInterval(() => {
      if (step >= stepMax) { stopPlay(); return; }
      step += 1;
      refreshRoute();
    }, 140);
  });
});

dash.draw('maplabel', (el) => {
  const rows = rowsOf('team_summary'), legs = rowsOf('team_legs');
  if (!rows || !legs) { el.textContent = '—'; return; }
  const sel = picked(rows), stops = routeOf(legs, sel);
  if (!stops.length) { el.textContent = '—'; return; }
  const n = stepFor(sel, stops.length), s = stops[n - 1];
  el.textContent = `Game ${n} of ${stops.length}: ${s.date ? dayFmt(new Date(s.date)) + ' at ' : 'at '}${s.city}, ${fmt(s.cum)} miles so far`;
});

dash.draw('mapnote', (el) => {
  const rows = rowsOf('team_summary'), legs = rowsOf('team_legs'), cities = rowsOf('cities');
  if (!rows || !legs || !cities) { el.hidden = true; return; }
  const pos = Object.fromEntries(cities.map((c) => [c.city, c]));
  const away = Array.from(new Set(routeOf(legs, picked(rows)).map((s) => s.city)))
    .filter((c) => pos[c] && (pos[c].lon < FRAME[0] || pos[c].lon > FRAME[2] || pos[c].lat < FRAME[1] || pos[c].lat > FRAME[3]));
  el.hidden = !away.length;
  el.textContent = away.length ? `Also plays in ${away.join(' and ')}, outside the map.` : '';
});

dash.draw('map', (el) => {
  const land = rowsOf('basemap'), cities = rowsOf('cities'), legs = rowsOf('team_legs'), rows = rowsOf('team_summary');
  if (!land || !cities || !legs || !rows) { el.textContent = '—'; return; }
  const sel = picked(rows), stops = routeOf(legs, sel);
  if (!stops.length) { el.textContent = '—'; return; }
  const n = stepFor(sel, stops.length);
  const w = el.clientWidth || 640, pad = 6;
  const scale = (w - 2 * pad) / (FX[1] - FX[0]);
  const h = Math.round((FY[1] - FY[0]) * scale + 2 * pad);
  const P = (lon, lat) => { const [x, y] = albers(lon, lat); return [pad + (x - FX[0]) * scale, pad + (FY[1] - y) * scale]; };
  const pathOf = (pts, close) => 'M' + pts.split(' ').map((p) => P(...p.split(',').map(Number)).map((v) => v.toFixed(1)).join(',')).join('L') + (close ? 'Z' : '');
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', `Route map of ${sel}, game ${n} of ${stops.length}`);
  svg.append('path').attr('class', 'nt-land').attr('d', land.filter((r) => r.kind === 'land').map((r) => pathOf(r.pts, true)).join(''));
  svg.append('path').attr('class', 'nt-border').attr('d', land.filter((r) => r.kind === 'border').map((r) => pathOf(r.pts, false)).join(''));

  const pos = Object.fromEntries(cities.map((c) => [c.city, c]));
  const onMap = (c) => pos[c] && pos[c].lon >= FRAME[0] && pos[c].lon <= FRAME[2] && pos[c].lat >= FRAME[1] && pos[c].lat <= FRAME[3];
  const xy = (c) => P(pos[c].lon, pos[c].lat);
  const visits = {};
  stops.slice(0, n).forEach((s) => { visits[s.city] = (visits[s.city] || 0) + 1; });

  const segs = [];
  for (let i = 1; i < n; i++) {
    const a = stops[i - 1].city, b = stops[i].city;
    if (a !== b && onMap(a) && onMap(b)) segs.push([a, b]);
  }
  const segPath = (list) => list.map(([a, b]) => `M${xy(a).map((v) => v.toFixed(1)).join(',')}L${xy(b).map((v) => v.toFixed(1)).join(',')}`).join('');
  const lineStyle = (s, width, opacity) => s.style('fill', 'none').style('stroke', accent()).style('stroke-width', width).style('stroke-opacity', opacity).attr('stroke-linecap', 'round');
  lineStyle(svg.append('path').attr('d', segPath(segs.slice(0, -1))), 1.1, 0.3);
  if (segs.length) lineStyle(svg.append('path').attr('d', segPath(segs.slice(-1))), 2.4, 1);

  const tip = makeTip(el);
  const dots = cities.filter((c) => onMap(c.city));
  svg.selectAll('circle.city').data(dots).join('circle').attr('class', 'city')
    .attr('cx', (c) => xy(c.city)[0]).attr('cy', (c) => xy(c.city)[1])
    .attr('r', (c) => (visits[c.city] ? 3 + 1.6 * Math.sqrt(visits[c.city]) : 2.5))
    .style('fill', (c) => (visits[c.city] ? accent() : 'var(--chart-muted)'))
    .style('fill-opacity', (c) => (visits[c.city] ? 0.85 : 0.5))
    .style('stroke', 'var(--color-panel)').style('stroke-width', 1)
    .on('mousemove', (e, c) => tip.show(e, [`${c.city}, ${c.state}`, visits[c.city] ? `${visits[c.city]} game${visits[c.city] > 1 ? 's' : ''} so far` : 'not visited yet']))
    .on('mouseleave', tip.hide);
  const now = stops[n - 1].city;
  if (onMap(now)) {
    const [cx, cy] = xy(now);
    svg.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 9).style('fill', 'none').style('stroke', 'var(--color-fg)').style('stroke-width', 2);
  }
});

// ---- strength of schedule: how each measure lines up with last season's win percentage
dash.calc('schedule_links', {
  title: 'Schedule measures against last season win percentage',
  description: 'Pearson correlation between last season win percentage and each schedule measure, strongest first.',
  inputs: ['team_schedule'],
  fn: (team_schedule) => {
    const measures = [
      ['sos_vs_balanced', 'Opponent strength vs. an even schedule'],
      ['total_miles', 'Season miles'],
      ['travel_back_to_backs', 'Back-to-backs with travel'],
      ['net_rest_edge', 'Rest edge'],
      ['three_in_four', 'Three-in-four-night stretches'],
      ['tz_hours_crossed', 'Time-zone hours crossed'],
      ['flights', 'Flights'],
      ['second_night_road_b2b', 'Back-to-backs, second night away'],
      ['longest_road_trip', 'Longest road trip'],
      ['longest_homestand', 'Longest homestand'],
      ['altitude_road_games', 'Road games at altitude'],
      ['difficulty_index', 'Wins lost to the schedule'],
    ];
    const mean = (xs) => xs.reduce((s, v) => s + v, 0) / xs.length;
    const pearson = (xs, ys) => {
      const mx = mean(xs), my = mean(ys);
      let sxy = 0, sxx = 0, syy = 0;
      xs.forEach((x, i) => { sxy += (x - mx) * (ys[i] - my); sxx += (x - mx) ** 2; syy += (ys[i] - my) ** 2; });
      return sxy / Math.sqrt(sxx * syy);
    };
    const wins = team_schedule.map((r) => r.win_pct_prev);
    return measures.map(([metric, label]) => ({
      metric, label,
      r: Math.round(100 * pearson(wins, team_schedule.map((r) => r[metric]))) / 100,
      noise: 0.36,
    })).sort((a, b) => Math.abs(b.r) - Math.abs(a.r));
  },
});
dash.calc('link_headline', {
  title: 'Strength of schedule headline',
  description: 'The strongest link and how many measures clear the noise level (r of 0.36 is the 5 percent level for 30 teams).',
  inputs: ['schedule_links', 'team_schedule'],
  fn: (schedule_links, team_schedule) => [{
    ...((rows) => {
      const view = (rankKey, winsKey, lowKey, highKey, suffix) => {
        const hard = rows.reduce((a, b) => (b[rankKey] < a[rankKey] ? b : a));
        const easy = rows.reduce((a, b) => (b[rankKey] > a[rankKey] ? b : a));
        const wins = rows.map((r) => r[winsKey]);
        return {
          ['hard_team' + suffix]: hard.team, ['hard_wins' + suffix]: Math.round(100 * hard[winsKey]) / 100,
          ['easy_team' + suffix]: easy.team, ['easy_wins' + suffix]: Math.round(100 * easy[winsKey]) / 100,
          ['spread' + suffix]: Math.round(100 * (Math.max(...wins) - Math.min(...wins))) / 100,
          ['n_far' + suffix]: rows.filter((r) => r[lowKey] > 0 || r[highKey] < 0).length,
        };
      };
      return {
        ...view('difficulty_rank', 'difficulty_index', 'load_low', 'load_high', ''),
        ...view('load_rank_no_altitude', 'load_wins_no_altitude', 'load_low_no_altitude', 'load_high_no_altitude', '_no_alt'),
        n_teams: rows.length,
      };
    })(team_schedule),
    top_label: schedule_links[0].label.charAt(0).toLowerCase() + schedule_links[0].label.slice(1),
    top_r: schedule_links[0].r,
    n_signal: schedule_links.filter((r) => Math.abs(r.r) >= r.noise).length,
    n_total: schedule_links.length,
    threshold: schedule_links[0].noise,
  }],
});
const linkFields = {
  hard_team: ['hard_team', (v) => v],
  easy_team: ['easy_team', (v) => v],
  spread: ['spread', d3.format('.2f')],
  hard_wins: ['hard_wins', d3.format('+.2f')],
  easy_wins: ['easy_wins', d3.format('+.2f')],
  hard_wins_abs: ['hard_wins', d3.format('.2f')],
  easy_wins_abs: ['easy_wins', (v) => d3.format('.2f')(Math.abs(v))],
  n_far: ['n_far', fmt],
  n_teams: ['n_teams', fmt],
  top_label: ['top_label', (v) => v],
  top_r: ['top_r', d3.format('+.2f')],
  n_signal: ['n_signal', fmt],
  n_total: ['n_total', fmt],
  threshold: ['threshold', d3.format('.2f')],
};
// these headline figures have a version without the altitude term
const ALTITUDE_FIELDS = new Set(['hard_team', 'hard_wins', 'easy_team', 'easy_wins', 'spread', 'n_far']);
Object.entries(linkFields).forEach(([name, [field, f]]) => {
  dash.draw(name, (el) => {
    const rows = rowsOf('link_headline');
    const column = noAlt() && ALTITUDE_FIELDS.has(field) ? field + '_no_alt' : field;
    el.textContent = rows && rows[0] ? f(rows[0][column]) : '—';
  });
});
const metricOf = (rows) => { const p = dash.params().metric; return (rows.find((r) => r.metric === p) || rows[0]); };
dash.draw('metric_name', (el) => { const r = rowsOf('schedule_links'); el.textContent = r ? metricOf(r).label : '—'; });
dash.draw('metric_r', (el) => { const r = rowsOf('schedule_links'); el.textContent = r ? d3.format('+.2f')(metricOf(r).r) : '—'; });

dash.draw('links', (el) => {
  const rows = rowsOf('schedule_links');
  if (!rows) { el.textContent = '—'; return; }
  const sel = metricOf(rows).metric;
  const w = el.clientWidth || 480, rowH = 42, m = { t: 22, r: 12, b: 26, l: 12 };
  const h = m.t + m.b + rows.length * rowH;
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', 'Correlation of each schedule measure with last season win percentage');
  const reach = Math.max(0.6, Math.ceil(10 * d3.max(rows, (d) => Math.abs(d.r))) / 10 + 0.1);
  const x = d3.scaleLinear([-reach, reach], [m.l + 28, w - m.r - 28]);
  const noise = rows[0].noise;
  svg.append('rect').attr('x', x(-noise)).attr('width', x(noise) - x(-noise)).attr('y', m.t - 6).attr('height', h - m.t - m.b + 6)
    .style('fill', 'var(--chart-grid)').style('fill-opacity', 0.55);
  svg.append('text').attr('x', x(0)).attr('y', 10).attr('text-anchor', 'middle').text('noise range');
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b})`)
    .call(d3.axisBottom(x).ticks(w < 400 ? 5 : 7).tickFormat(d3.format('+.1f')));
  xa.attr('font-size', null).attr('font-family', null);
  svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', m.t - 6).attr('y2', h - m.b).style('stroke', 'var(--chart-axis)');
  const tip = makeTip(el);
  const g = svg.selectAll('g.row').data(rows).join('g').attr('class', 'row').attr('transform', (d, i) => `translate(0,${m.t + i * rowH})`);
  g.append('text').attr('x', m.l).attr('y', 11).attr('class', (d) => (d.metric === sel ? 'nt-strong' : null)).text((d) => d.label);
  g.append('rect').attr('x', (d) => x(Math.min(0, d.r))).attr('width', (d) => Math.abs(x(d.r) - x(0))).attr('y', 18).attr('height', 14).attr('rx', 2)
    .style('fill', (d) => (Math.abs(d.r) >= d.noise ? accent() : 'var(--chart-muted)'))
    .style('stroke', (d) => (d.metric === sel ? 'var(--color-fg)' : 'none')).style('stroke-width', 1.5);
  g.append('text').attr('x', (d) => (d.r < 0 ? x(d.r) - 6 : x(d.r) + 6)).attr('y', 25).attr('dy', '0.32em')
    .attr('text-anchor', (d) => (d.r < 0 ? 'end' : 'start')).text((d) => d3.format('+.2f')(d.r));
  g.append('rect').attr('class', 'nt-hit').attr('width', w).attr('height', rowH)
    .on('click', (e, d) => dash.setParams({ metric: d.metric }))
    .on('mousemove', (e, d) => tip.show(e, [d.label, 'correlation ' + d3.format('+.2f')(d.r), Math.abs(d.r) >= d.noise ? 'clears the noise range' : 'inside the noise range']))
    .on('mouseleave', tip.hide);
});

dash.draw('linkscatter', (el) => {
  const rows = rowsOf('team_schedule'), links = rowsOf('schedule_links'), summary = rowsOf('team_summary');
  if (!rows || !links) { el.textContent = '—'; return; }
  const metric = metricOf(links), key = metric.metric;
  const sel = summary ? picked(summary) : null;
  const yFmt = key === 'sos_vs_balanced' ? d3.format('+.3f') : key === 'difficulty_index' ? d3.format('.1f') : fmt;
  const w = el.clientWidth || 480, h = 340, m = { t: 14, r: 20, b: 48, l: 56 };
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', `${metric.label} against last season win percentage, one dot per team`);
  const x = d3.scaleLinear([0.15, 0.85], [m.l, w - m.r]);
  const y = d3.scaleLinear(d3.extent(rows, (d) => d[key]), [h - m.b, m.t]).nice();
  svg.append('g').selectAll('line').data(y.ticks(5)).join('line').attr('class', 'nt-grid-line')
    .attr('x1', m.l).attr('x2', w - m.r).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(w < 420 ? 4 : 7).tickFormat(d3.format('.0%')));
  const ya = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(yFmt));
  [xa, ya].forEach((a) => a.attr('font-size', null).attr('font-family', null));
  svg.append('text').attr('x', (m.l + w - m.r) / 2).attr('y', h - 8).attr('text-anchor', 'middle').text('Win percentage last season');
  // least-squares trend through the 30 dots
  const mx = d3.mean(rows, (d) => d.win_pct_prev), my = d3.mean(rows, (d) => d[key]);
  const slope = d3.sum(rows, (d) => (d.win_pct_prev - mx) * (d[key] - my)) / d3.sum(rows, (d) => (d.win_pct_prev - mx) ** 2);
  const [x0, x1] = [0.2, 0.8];
  svg.append('line').attr('x1', x(x0)).attr('x2', x(x1)).attr('y1', y(my + slope * (x0 - mx))).attr('y2', y(my + slope * (x1 - mx)))
    .style('stroke', 'var(--chart-reference)').style('stroke-width', 1.5).style('stroke-dasharray', '5 4');
  const tip = makeTip(el);
  const ordered = rows.slice().sort((a, b) => (a.team === sel) - (b.team === sel));
  svg.selectAll('circle').data(ordered).join('circle')
    .attr('cx', (d) => x(d.win_pct_prev)).attr('cy', (d) => y(d[key])).attr('r', (d) => (d.team === sel ? 7 : 5)).style('cursor', 'pointer')
    .style('fill', (d) => (d.team === sel ? accent() : 'var(--chart-muted)')).style('fill-opacity', (d) => (d.team === sel ? 1 : 0.75))
    .style('stroke', 'var(--color-panel)').style('stroke-width', 1.5)
    .on('click', (e, d) => dash.setParams({ team: d.team }))
    .on('mousemove', (e, d) => tip.show(e, [d.team, `${d.wins_prev}–${d.losses_prev} last season`, `${metric.label}: ${yFmt(d[key])}`]))
    .on('mouseleave', tip.hide);
  const s = rows.find((d) => d.team === sel);
  if (s) {
    const sx = x(s.win_pct_prev), anchor = sx > w - 150 ? 'end' : 'start';
    svg.append('text').attr('class', 'nt-strong').attr('x', sx + (anchor === 'end' ? -10 : 10)).attr('y', y(s[key]) - 10).attr('text-anchor', anchor).text(s.team);
  }
});

// ---- sortable team tables: click a header to sort, click a row to follow that team
function makeSortable(tableId, drawName, state) {
  document.querySelectorAll(`#${tableId} th button`).forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.sort;
      state.dir = key === state.key ? -state.dir : (key === 'team' || key === 'difficulty_rank' ? 1 : -1);
      state.key = key;
      document.querySelectorAll(`#${tableId} th`).forEach((th) => th.setAttribute('aria-sort', th === btn.parentElement ? (state.dir > 0 ? 'ascending' : 'descending') : 'none'));
      dash.draw(drawName);
    });
  });
  document.querySelectorAll(`#${tableId} tbody`).forEach((tb) => {
    tb.addEventListener('click', (e) => {
      const tr = e.target.closest('tr[data-key]');
      if (tr) dash.setParams({ team: tr.dataset.key });
    });
  });
}
const byKey = (state) => (a, b) => (state.key === 'team' ? a.team.localeCompare(b.team) : a[state.key] - b[state.key]) * state.dir;
function fillRows(tb, list, sel, cellsOf, keyField = 'team') {
  tb.replaceChildren(...list.map((r) => {
    const tr = document.createElement('tr');
    tr.dataset.key = r[keyField];
    if (r.team === sel) tr.className = 'nt-picked';
    cellsOf(r).forEach((v) => { const td = document.createElement('td'); td.textContent = v; tr.append(td); });
    return tr;
  }));
}

const allSort = { key: 'total_miles', dir: -1 };
dash.draw('allbody', (tb) => {
  const rows = rowsOf('team_summary');
  if (!rows) { tb.replaceChildren(); return; }
  const q = ((document.getElementById('nt-search') || {}).value || '').trim().toLowerCase();
  const list = rows.filter((r) => r.team.toLowerCase().includes(q)).sort(byKey(allSort));
  fillRows(tb, list, picked(rows), (r) => [r.team, ...[r.games, r.total_miles, r.miles_per_game, r.back_to_backs, r.travel_back_to_backs, r.longest_trip].map(fmt)]);
});
makeSortable('nt-all-table', 'allbody', allSort);
document.querySelectorAll('#nt-search').forEach((inp) => inp.addEventListener('input', () => dash.draw('allbody')));

const schedSort = { key: 'difficulty_rank', dir: 1 };
dash.draw('schedbody', (tb) => {
  const rows = rowsOf('team_schedule'), summary = rowsOf('team_summary');
  if (!rows) { tb.replaceChildren(); return; }
  fillRows(tb, withAltitudeChoice(rows).sort(byKey(schedSort)), summary ? picked(summary) : null, (r) => [
    r.team, fmt(r.difficulty_rank), fmt(r.load_rank_no_altitude), d3.format('+.2f')(r.difficulty_index), d3.format('+.2f')(r.load_low), d3.format('+.2f')(r.load_high), d3.format('.3f')(r.win_pct_prev), d3.format('+.3f')(r.sos_vs_balanced), d3.format('+d')(r.net_rest_edge),
    fmt(r.three_in_four), fmt(r.tz_hours_crossed), fmt(r.flights), fmt(r.second_night_road_b2b), fmt(r.longest_road_trip),
    fmt(r.longest_homestand), fmt(r.altitude_road_games),
  ]);
});
makeSortable('nt-sched-table', 'schedbody', schedSort);

// ---- comparison with other sources
dash.calc('agreement', {
  title: 'Agreement with other sources',
  description: 'For each measure we also have from another site: correlation, teams with identical values, and average gap.',
  inputs: ['source_comparison'],
  fn: (source_comparison) => {
    const pairs = [
      ['Season miles', 'Yahoo Sports', 'my_miles', 'yahoo_miles'],
      ['Season miles', 'Hoops Menu', 'my_miles', 'hm_miles'],
      ['Back-to-backs', 'Legion Report', 'my_b2b', 'legion_b2b'],
      ['Back-to-backs', 'Hoops Menu', 'my_b2b', 'hm_b2b'],
      ['Rest-disadvantage games', 'Hoops Menu', 'my_rest_disadv', 'hm_rest_disadv'],
      ['Three-in-four-night stretches', 'Hoops Menu', 'my_3in4', 'hm_3in4'],
      ['Back-to-backs, second night away', 'Legion Report', 'my_second_night_road', 'legion_second_night_road'],
      ['Back-to-backs, both nights away', 'Legion Report', 'my_both_nights_road', 'legion_both_nights_road'],
      ['Longest road trip', 'Legion Report', 'my_road_trip', 'legion_road_trip'],
      ['Longest homestand', 'Legion Report', 'my_homestand', 'legion_homestand'],
      ['Flights', 'Yahoo Sports', 'my_flights', 'yahoo_flights'],
      ['Overall rank', 'Hoops Menu', 'my_rank', 'hm_rank'],
      ['Overall rank', 'Legion Report', 'my_rank', 'legion_rank'],
      ['Overall rank', 'Power Rankings Guru, remaining', 'my_rank', 'prg_remaining_rank'],
      ['Overall rank', 'CraftedNBA, remaining', 'my_rank', 'crafted_remaining_rank'],
      ['Overall rank', 'ESPN RPI, games so far', 'my_rank', 'espn_rpi_rank'],
      ['Overall rank', 'Power Rankings Guru, games so far', 'my_rank', 'prg_played_rank'],
      ['Overall rank', 'CraftedNBA, games so far', 'my_rank', 'crafted_past_rank'],
      ['Overall rank, their recipe on our counts', 'Hoops Menu', 'recipe_rank', 'hm_rank'],
    ];
    const mean = (xs) => xs.reduce((s, v) => s + v, 0) / xs.length;
    const pearson = (xs, ys) => {
      const mx = mean(xs), my = mean(ys);
      let sxy = 0, sxx = 0, syy = 0;
      xs.forEach((x, i) => { sxy += (x - mx) * (ys[i] - my); sxx += (x - mx) ** 2; syy += (ys[i] - my) ** 2; });
      return sxy / Math.sqrt(sxx * syy);
    };
    // every comparison of our rank is made twice: with the altitude term and with it left out
    const withBoth = [];
    pairs.forEach(([measure, source, a, b]) => {
      if (a === 'my_rank') {
        withBoth.push([measure, source, a, b, 'with'], [measure, source, 'my_rank_no_altitude', b, 'without']);
      } else {
        withBoth.push([measure, source, a, b, 'both']);
      }
    });
    return withBoth.map(([measure, source, a, b, altitude]) => {
      const xs = source_comparison.map((r) => r[a]), ys = source_comparison.map((r) => r[b]);
      return {
        key: measure + ' | ' + source + ' | ' + altitude, measure, source, altitude,
        r: Math.round(100 * pearson(xs, ys)) / 100,
        exact: xs.filter((x, i) => x === ys[i]).length,
        n: xs.length,
        gap: Math.round(10 * mean(xs.map((x, i) => Math.abs(x - ys[i])))) / 10,
      };
    });
  },
});
dash.calc('compare_headline', {
  title: 'Comparison headline',
  description: 'The rank correlations with each source, and how many teams have identical back-to-back counts.',
  inputs: ['agreement'],
  fn: (agreement) => {
    const find = (m, s, alt) => agreement.find((r) => r.measure === m && r.source === s && (!alt || r.altitude === alt));
    return [{
      hm_r: find('Overall rank', 'Hoops Menu', 'with').r,
      legion_r: find('Overall rank', 'Legion Report', 'with').r,
      hm_r_no_alt: find('Overall rank', 'Hoops Menu', 'without').r,
      legion_r_no_alt: find('Overall rank', 'Legion Report', 'without').r,
      recipe_r: find('Overall rank, their recipe on our counts', 'Hoops Menu').r,
      b2b_exact: find('Back-to-backs', 'Legion Report').exact,
      b2b_n: find('Back-to-backs', 'Legion Report').n,
    }];
  },
});
dash.calc('biggest_gaps', {
  title: 'Largest rank gaps against Hoops Menu',
  description: 'The three teams whose rank on this dashboard differs most from their Hoops Menu rank.',
  inputs: ['source_comparison'],
  fn: (source_comparison) => ['with', 'without'].flatMap((altitude) => source_comparison
    .map((r) => {
      const mine = altitude === 'with' ? r.my_rank : r.my_rank_no_altitude;
      return { key: r.team + ' | ' + altitude, altitude, team: r.team, my_rank: mine, hm_rank: r.hm_rank, gap: Math.abs(mine - r.hm_rank) };
    })
    .sort((a, b) => b.gap - a.gap).slice(0, 3)),
});
const compareFields = {
  hm_r: ['hm_r', d3.format('+.2f')],
  legion_r: ['legion_r', d3.format('+.2f')],
  recipe_r: ['recipe_r', d3.format('+.2f')],
  b2b_exact: ['b2b_exact', fmt],
  b2b_n: ['b2b_n', fmt],
};
Object.entries(compareFields).forEach(([name, [field, f]]) => {
  dash.draw(name, (el) => {
    const rows = rowsOf('compare_headline');
    const column = noAlt() && (name === 'hm_r' || name === 'legion_r') ? field + '_no_alt' : field;
    el.textContent = rows && rows[0] ? f(rows[0][column]) : '—';
  });
});
dash.draw('biggest_gaps', (el) => {
  const all = rowsOf('biggest_gaps');
  const rows = all ? all.filter((r) => r.altitude === (noAlt() ? 'without' : 'with')) : null;
  el.textContent = rows ? 'Largest gaps against Hoops Menu: ' + rows.map((r) => `${r.team} (ours #${r.my_rank}, theirs #${r.hm_rank})`).join('; ') + '.' : '—';
});
dash.draw('agreebody', (tb) => {
  const all = rowsOf('agreement');
  if (!all) { tb.replaceChildren(); return; }
  const rows = all.filter((r) => r.altitude === 'both' || r.altitude === (noAlt() ? 'without' : 'with'));
  fillRows(tb, rows, null, (r) => [r.measure, r.source, d3.format('+.2f')(r.r), `${fmt(r.exact)} of ${fmt(r.n)}`, fmt1(r.gap)], 'key');
  tb.querySelectorAll('td:nth-child(-n+2)').forEach((td) => { td.className = 'nt-left'; });
});
dash.onData(() => {
  document.querySelectorAll('.nt-key').forEach((s) => s.style.setProperty('--k', dash.colors[+s.dataset.series]));
});

const f1 = d3.format('.1f'), f3 = d3.format('.3f'), fs2 = d3.format('+.2f');
// each source: the column holding its rank, the dot size, and the tooltip line
const RANK_SERIES = [
  { key: 'my_rank', series: 0, r: 6.5, tip: (d) => `This dashboard: #${d.my_rank}` },
  { key: 'hm_rank', series: 1, r: 5, tip: (d) => `Hoops Menu: #${d.hm_rank} (index ${f1(d.hm_index)})` },
  { key: 'legion_rank', series: 2, r: 5, tip: (d) => `Legion Report: #${d.legion_rank} (opponents ${f3(d.legion_opp_win_pct)})` },
  { key: 'prg_remaining_rank', series: 3, r: 5, tip: (d) => `Power Rankings Guru, remaining: #${d.prg_remaining_rank}` },
  { key: 'crafted_remaining_rank', series: 4, r: 5, tip: (d) => `CraftedNBA, remaining: #${d.crafted_remaining_rank} (${fs2(d.crafted_remaining)})` },
];
const PLAYED_SERIES = [
  { key: 'espn_rpi_rank', series: 5, r: 4.5, tip: (d) => `ESPN RPI, so far: #${d.espn_rpi_rank} (${f3(d.espn_rpi_sos)})` },
  { key: 'prg_played_rank', series: 6, r: 4.5, tip: (d) => `Power Rankings Guru, so far: #${d.prg_played_rank}` },
  { key: 'crafted_past_rank', series: 7, r: 4.5, tip: (d) => `CraftedNBA, so far: #${d.crafted_past_rank} (${fs2(d.crafted_past)})` },
];
const playedOn = () => { const c = document.getElementById('nt-played'); return !!(c && c.checked); };

dash.draw('rankcompare', (el) => {
  const rows = rowsOf('source_comparison'), summary = rowsOf('team_summary');
  if (!rows) { el.textContent = '—'; return; }
  const sel = summary ? picked(summary) : null;
  const active = playedOn() ? RANK_SERIES.concat(PLAYED_SERIES) : RANK_SERIES;
  const data = rows.map((r) => (noAlt() ? { ...r, my_rank: r.my_rank_no_altitude } : r)).sort((a, b) => a.my_rank - b.my_rank);
  const w = el.clientWidth || 640, rowH = 24, m = { t: 22, r: 16, b: 34 };
  const h = m.t + m.b + rowH * data.length;
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', 'Schedule difficulty rank for each team on this dashboard and on other sites');
  m.l = Math.ceil(textWidth(svg, data.map((d) => d.team))) + 14;
  const x = d3.scaleLinear([1, data.length], [m.l + 6, w - m.r]);
  const ticks = [1, 5, 10, 15, 20, 25, data.length];
  svg.append('g').selectAll('line').data(ticks).join('line').attr('class', 'nt-grid-line')
    .attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', m.t - 8).attr('y2', h - m.b);
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b + 4})`)
    .call(d3.axisBottom(x).tickValues(ticks).tickSize(0).tickPadding(6));
  xa.select('.domain').remove();
  xa.attr('font-size', null).attr('font-family', null);
  svg.append('text').attr('x', x(1)).attr('y', 10).text('hardest');
  svg.append('text').attr('x', x(data.length)).attr('y', 10).attr('text-anchor', 'end').text('lightest');
  const tip = makeTip(el);
  const ranks = (d) => active.map((s) => d[s.key]);
  const g = svg.selectAll('g.row').data(data).join('g').attr('class', 'row').attr('transform', (d, i) => `translate(0,${m.t + i * rowH})`);
  g.filter((d) => d.team === sel).append('rect').attr('x', 0).attr('width', w).attr('y', 1).attr('height', rowH - 2).style('fill', 'var(--color-bg)');
  g.append('text').attr('x', m.l - 8).attr('y', rowH / 2).attr('dy', '0.32em').attr('text-anchor', 'end')
    .attr('class', (d) => (d.team === sel ? 'nt-strong' : null)).text((d) => d.team);
  g.append('line').attr('x1', (d) => x(d3.min(ranks(d)))).attr('x2', (d) => x(d3.max(ranks(d)))).attr('y1', rowH / 2).attr('y2', rowH / 2)
    .style('stroke', 'var(--chart-axis)').style('stroke-width', 2).style('stroke-opacity', 0.5);
  // draw the last source first so this dashboard's dot sits on top
  active.slice().reverse().forEach(({ key, series, r }) => {
    g.append('circle').attr('cx', (d) => x(d[key])).attr('cy', rowH / 2).attr('r', r)
      .style('fill', dash.colors[series]).style('stroke', 'var(--color-panel)').style('stroke-width', 1.5);
  });
  g.append('rect').attr('class', 'nt-hit').attr('width', w).attr('height', rowH)
    .on('click', (e, d) => dash.setParams({ team: d.team }))
    .on('mousemove', (e, d) => tip.show(e, [d.team, ...active.map((s) => s.tip(d))]))
    .on('mouseleave', tip.hide);
});
document.querySelectorAll('#nt-played').forEach((box) => {
  box.addEventListener('change', () => {
    document.querySelectorAll('.nt-legend-played').forEach((l) => { l.hidden = !box.checked; });
    dash.draw('rankcompare');
  });
});

dash.draw('methodsbody', (tb) => {
  const rows = rowsOf('source_methods');
  if (!rows) { tb.replaceChildren(); return; }
  fillRows(tb, rows, null, (r) => [r.source, r.measures, r.calculation, r.reproduced], 'source');
});

// ---- what each factor is worth, and the schedule load in wins
dash.calc('effects_headline', {
  title: 'Effects headline',
  description: 'The back-to-back and home-court effects used, how many factors are clearly measured, and the size of the data.',
  inputs: ['schedule_effects', 'model_summary'],
  fn: (schedule_effects, model_summary) => {
    const find = (name) => schedule_effects.find((r) => r.effect === name);
    return [{
      games: model_summary[0].games,
      seasons: model_summary[0].seasons,
      b2b_cost: Math.round(100 * Math.abs(find('Second night of a back-to-back').used)) / 100,
      hca: Math.round(100 * find('Home court (2020–21 left out)').used) / 100,
      miles_measured: find('Distance travelled since the last game').measured,
      miles_se: find('Distance travelled since the last game').measured_se,
      n_clear: schedule_effects.filter((r) => r.clear === 'Clearly measured').length,
      n_total: schedule_effects.length,
      win_pct_per_point: Math.round(10 * model_summary[0].win_pct_per_point) / 10,
      carryover: model_summary[0].carryover,
    }];
  },
});
const effectFields = {
  fx_games: ['games', fmt], fx_seasons: ['seasons', fmt], fx_b2b: ['b2b_cost', d3.format('.1f')],
  fx_hca: ['hca', d3.format('.1f')], fx_clear: ['n_clear', fmt], fx_total: ['n_total', fmt],
  fx_winpct: ['win_pct_per_point', d3.format('.1f')], fx_carry: ['carryover', d3.format('.2f')],
  fx_b2b_tile: ['b2b_cost', d3.format('.1f')], fx_miles: ['miles_measured', d3.format('+.2f')], fx_miles_se: ['miles_se', d3.format('.2f')],
};
Object.entries(effectFields).forEach(([name, [field, f]]) => {
  dash.draw(name, (el) => {
    const rows = rowsOf('effects_headline');
    el.textContent = rows && rows[0] ? f(rows[0][field]) : '—';
  });
});
dash.draw('effectsbody', (tb) => {
  const rows = rowsOf('schedule_effects');
  if (!rows) { tb.replaceChildren(); return; }
  fillRows(tb, rows, null, (r) => [
    r.effect, r.unit, d3.format('+.2f')(r.measured), d3.format('.2f')(r.measured_se), d3.format('+.2f')(r.used),
    d3.format('+.2f')(r.earlier_seasons), d3.format('+.2f')(r.recent_seasons),
    d3.format('+.1f')(r.win_pct_per_game), r.clear,
  ], 'effect');
});

// the altitude switch: with it on, every load figure comes from the version of the model without the altitude term
const noAlt = () => !!document.querySelector('.nt-noalt-box:checked');
const withAltitudeChoice = (rows) => (noAlt() ? rows.map((r) => ({
  ...r,
  difficulty_rank: r.load_rank_no_altitude, difficulty_index: r.load_wins_no_altitude,
  load_low: r.load_low_no_altitude, load_high: r.load_high_no_altitude,
  load_rank_low: r.load_rank_low_no_altitude, load_rank_high: r.load_rank_high_no_altitude,
  load_altitude: 0,
})) : rows.slice());

// each source of load: the column, the legend colour and the tooltip name
const LOAD_PARTS = [
  ['load_opponent', 0, "Opponents' strength"], ['load_rest', 1, 'Back-to-backs and rest'], ['load_travel', 2, 'Distance travelled'],
  ['load_timezone', 3, 'Time zones'], ['load_density', 4, 'Three in four nights'], ['load_altitude', 5, 'Altitude'],
  ['load_venue', 6, 'Home and road mix'],
];
dash.draw('loadchart', (el) => {
  const rows = rowsOf('team_schedule'), summary = rowsOf('team_summary');
  if (!rows) { el.textContent = '—'; return; }
  const sel = summary ? picked(summary) : null;
  const data = withAltitudeChoice(rows).sort((a, b) => b.difficulty_index - a.difficulty_index);
  const w = el.clientWidth || 640, rowH = 30, m = { t: 8, r: 16, b: 34 };
  const h = m.t + m.b + rowH * data.length;
  const svg = startSvg(el, w, h);
  svg.attr('aria-label', 'Wins lost to the schedule for each team, split by source, with a 90 percent range');
  m.l = Math.ceil(textWidth(svg, data.map((d) => d.team))) + 14;
  const stacks = data.map((d) => {
    let pos = 0, neg = 0;
    const parts = LOAD_PARTS.filter(([key]) => !(noAlt() && key === 'load_altitude')).map(([key, series]) => {
      const v = d[key] || 0;
      const part = v >= 0 ? { x0: pos, x1: pos + v, series, key } : { x0: neg + v, x1: neg, series, key };
      if (v >= 0) pos += v; else neg += v;
      return part;
    });
    return { d, parts };
  });
  const lo = d3.min(data, (d) => Math.min(d.load_low, ...stacks.flatMap((s) => s.parts.map((p) => p.x0))));
  const hi = d3.max(data, (d) => Math.max(d.load_high, ...stacks.flatMap((s) => s.parts.map((p) => p.x1))));
  const x = d3.scaleLinear([Math.min(lo, -0.2), Math.max(hi, 0.2)], [m.l + 6, w - m.r]).nice();
  svg.append('g').selectAll('line').data(x.ticks(6)).join('line').attr('class', 'nt-grid-line')
    .attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', m.t).attr('y2', h - m.b);
  const xa = svg.append('g').attr('transform', `translate(0,${h - m.b + 4})`).call(d3.axisBottom(x).ticks(6).tickFormat(d3.format('+.1f')).tickSize(0).tickPadding(6));
  xa.select('.domain').remove();
  xa.attr('font-size', null).attr('font-family', null);
  svg.append('text').attr('x', (m.l + w - m.r) / 2).attr('y', h - 4).attr('text-anchor', 'middle').text('Wins lost to the schedule (positive is harder)');
  const tip = makeTip(el);
  const g = svg.selectAll('g.row').data(stacks).join('g').attr('class', 'row').attr('transform', (s, i) => `translate(0,${m.t + i * rowH})`);
  g.filter((s) => s.d.team === sel).append('rect').attr('x', 0).attr('width', w).attr('y', 1).attr('height', rowH - 2).style('fill', 'var(--color-bg)');
  g.append('text').attr('x', m.l - 8).attr('y', 11).attr('dy', '0.32em').attr('text-anchor', 'end')
    .attr('class', (s) => (s.d.team === sel ? 'nt-strong' : null)).text((s) => s.d.team);
  g.selectAll('rect.part').data((s) => s.parts).join('rect').attr('class', 'part')
    .attr('x', (p) => x(p.x0)).attr('width', (p) => Math.max(0, x(p.x1) - x(p.x0))).attr('y', 4).attr('height', 12)
    .style('fill', (p) => dash.colors[p.series]);
  g.append('line').attr('x1', (s) => x(s.d.load_low)).attr('x2', (s) => x(s.d.load_high)).attr('y1', 23).attr('y2', 23)
    .style('stroke', 'var(--chart-axis)').style('stroke-width', 2).style('stroke-opacity', 0.6);
  g.append('circle').attr('cx', (s) => x(s.d.difficulty_index)).attr('cy', 23).attr('r', 3.5).style('fill', 'var(--color-fg)');
  g.append('rect').attr('class', 'nt-hit').attr('width', w).attr('height', rowH)
    .on('click', (e, s) => dash.setParams({ team: s.d.team }))
    .on('mousemove', (e, s) => tip.show(e, [
      s.d.team,
      `Wins lost ${d3.format('+.2f')(s.d.difficulty_index)} (range ${d3.format('+.2f')(s.d.load_low)} to ${d3.format('+.2f')(s.d.load_high)})`,
      `Rank ${s.d.difficulty_rank}${noAlt() ? ' (altitude left out)' : `, or ${s.d.load_rank_no_altitude} without altitude`}`,
      ...LOAD_PARTS.filter(([key]) => !(noAlt() && key === 'load_altitude')).map(([key, , name]) => `${name}: ${d3.format('+.2f')(s.d[key] || 0)}`),
    ]))
    .on('mouseleave', tip.hide);
});

dash.calc('altitude_shift', {
  title: 'Rank change without altitude',
  description: 'The two teams whose schedule-load rank moves most when the altitude term is left out.',
  inputs: ['team_schedule'],
  fn: (team_schedule) => team_schedule
    .map((r) => ({ team: r.team, rank: r.difficulty_rank, rank_no_altitude: r.load_rank_no_altitude, shift: Math.abs(r.difficulty_rank - r.load_rank_no_altitude) }))
    .sort((a, b) => b.shift - a.shift).slice(0, 2),
});
dash.draw('altshift', (el) => {
  const rows = rowsOf('altitude_shift');
  el.textContent = rows
    ? 'Leaving altitude out moves ' + rows.map((r) => `${r.team} from #${r.rank} to #${r.rank_no_altitude}`).join(' and ')
      + '. Altitude rests on two teams\u2019 home games, so those positions depend on it.'
    : '—';
});

document.querySelectorAll('.nt-noalt-box').forEach((box) => {
  box.addEventListener('change', () => {
    document.querySelectorAll('.nt-noalt-box').forEach((other) => { other.checked = box.checked; });
    ['loadchart', 'schedbody', 'sel_rank', 'rankcompare', 'agreebody', 'biggest_gaps', 'hm_r', 'legion_r',
      'hard_team', 'hard_wins', 'hard_wins_abs', 'easy_team', 'easy_wins', 'easy_wins_abs', 'spread', 'n_far'].forEach((name) => dash.draw(name));
  });
});

dash.start(['team_summary', 'team_legs', 'team_schedule', 'cities', 'basemap', 'source_comparison', 'source_methods', 'schedule_effects', 'model_summary']);
