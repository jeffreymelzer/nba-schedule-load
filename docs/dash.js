// A small runtime for the page: named datasets loaded from data/*.json, calculations over them, drawings bound to
// elements with data-draw="name", and parameters (the picked team, the picked measure) kept in the URL hash.
const dash = (() => {
  const store = {};
  const calcs = [];
  const drawers = {};
  const loaded = [];
  let started = false;
  let params = Object.fromEntries(new URLSearchParams(location.hash.slice(1)));

  function run(name) {
    const fn = drawers[name];
    if (!fn) return;
    document.querySelectorAll(`[data-draw="${name}"]`).forEach((el) => {
      try { fn(el); } catch (err) { console.error(`drawing ${name} failed`, err); }
    });
  }
  const drawAll = () => Object.keys(drawers).forEach(run);

  function fail(message) {
    const box = document.createElement('p');
    box.className = 'nt-error';
    box.setAttribute('role', 'alert');
    box.textContent = message;
    document.querySelector('.nt').prepend(box);
  }

  async function start(ids) {
    try {
      const sets = await Promise.all(ids.map(async (id) => {
        const response = await fetch(`data/${id}.json`);
        if (!response.ok) throw new Error(`data/${id}.json: ${response.status}`);
        return [id, await response.json()];
      }));
      sets.forEach(([id, rows]) => { store[id] = rows; });
    } catch (err) {
      console.error(err);
      fail('The data could not be loaded. If you opened this file directly, serve the folder instead (python -m http.server).');
      return;
    }
    calcs.forEach(({ name, inputs, fn }) => {
      try { store[name] = fn(...inputs.map((id) => store[id])); } catch (err) { console.error(`calculation ${name} failed`, err); }
    });
    started = true;
    loaded.forEach((fn) => fn());
    drawAll();
  }

  let lastWidth = window.innerWidth;
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (started && window.innerWidth !== lastWidth) drawAll();
      lastWidth = window.innerWidth;
    }, 150);
  });
  window.addEventListener('hashchange', () => {
    params = Object.fromEntries(new URLSearchParams(location.hash.slice(1)));
    if (started) drawAll();
  });

  return {
    start,
    calc(name, { inputs, fn }) { calcs.push({ name, inputs, fn }); },
    draw(name, fn) {
      if (fn) drawers[name] = fn;
      if (started) run(name);
    },
    data(id) { return id in store ? { status: 'ok', data: store[id] } : { status: 'loading' }; },
    params() { return params; },
    setParams(update) {
      params = { ...params, ...update };
      history.replaceState(null, '', '#' + new URLSearchParams(params));
      if (started) drawAll();
    },
    onData(fn) { loaded.push(fn); },
    colors: Array.from({ length: 8 }, (_, i) => `var(--series-${i})`),
  };
})();
