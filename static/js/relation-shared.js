(function (global) {
  const STORAGE_KEY = 'relation.shared.v1';
  const listeners = new Set();

  function normalize(raw) {
    const base = { selected: [], relationType: 'couple', lastResult: null };
    if (!raw || typeof raw !== 'object') return base;
    const selected = Array.isArray(raw.selected) ? raw.selected.slice(0, 2).map(String) : [];
    const relationType = raw.relationType || raw.relation_type || 'couple';
    const lastResult = raw.lastResult || raw.last_result || null;
    return { selected, relationType, lastResult };
  }

  function read() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      return normalize(raw);
    } catch (e) {
      return normalize();
    }
  }

  function write(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // ignore quota errors
    }
  }

  function notify(state, source) {
    listeners.forEach((fn) => {
      try { fn(state, source); } catch (_) {}
    });
  }

  function broadcast(state) {
    const packet = { type: 'relation:update', payload: state };
    const targets = new Set();
    targets.add(global);
    if (global.parent && global.parent !== global) targets.add(global.parent);
    for (let i = 0; i < global.frames.length; i++) {
      const f = global.frames[i];
      if (f) targets.add(f);
    }
    targets.forEach((win) => {
      try { win.postMessage(packet, '*'); } catch (_) {}
    });
  }

  function apply(state, source, shouldBroadcast) {
    const next = normalize(state);
    write(next);
    notify(next, source || 'local');
    if (shouldBroadcast) broadcast(next);
    return next;
  }

  function setSelection(selected, relationType) {
    const current = read();
    const next = normalize({
      selected: Array.isArray(selected) ? selected : current.selected,
      relationType: relationType || current.relationType,
      lastResult: current.lastResult,
    });
    return apply(next, 'local', true);
  }

  function setResult(resultPayload) {
    const current = read();
    const next = normalize({
      selected: current.selected,
      relationType: current.relationType,
      lastResult: resultPayload || null,
    });
    return apply(next, 'local', true);
  }

  function reset() {
    return apply(normalize(), 'local', true);
  }

  function subscribe(fn) {
    if (typeof fn === 'function') listeners.add(fn);
    return () => listeners.delete(fn);
  }

  global.addEventListener('message', (event) => {
    if (!event || !event.data || event.data.type !== 'relation:update') return;
    const incoming = normalize(event.data.payload);
    apply(incoming, 'remote', false);
  });

  global.RelationShared = {
    getState: read,
    setSelection,
    setResult,
    reset,
    subscribe,
  };
})(window);
