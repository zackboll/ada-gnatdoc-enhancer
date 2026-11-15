/* Independent presentation enhancement. Never reads or changes router state. */
(() => {
  'use strict';
  const body = document.body;
  const divider = document.getElementById('navigation-resize');
  const navigation = document.getElementById('resizable-navigation');
  const content = document.querySelector('.document-content');
  if (!divider || !navigation || !content || !divider.setPointerCapture) return;

  const minimum = 240;
  const contentMinimum = 320;
  const handleWidth = 8;
  // The containing API directory is stable across query/history changes and
  // separates GitHub Pages projects, versions and independently hosted APIs.
  const key = 'gnatdoc:sidebar-width:v1:' + new URL('.', location.href).pathname;
  let preferred = null;
  try {
    const raw = localStorage.getItem(key);
    if (raw !== null && /^\d{1,7}(?:\.\d{1,3})?$/.test(raw)) {
      const value = Number(raw);
      if (Number.isFinite(value) && value > 0) preferred = value;
    }
  } catch (_) { /* Storage denial must not disable resizing. */ }

  let maximum = minimum;
  let defaultWidth = minimum;
  let width = minimum;
  let active = null;
  const clamp = value => Math.round(Math.max(minimum, Math.min(maximum, value)));
  function apply(value) {
    width = clamp(value);
    body.style.setProperty('--navigation-width', width + 'px');
    divider.setAttribute('aria-valuemin', String(minimum));
    divider.setAttribute('aria-valuemax', String(maximum));
    divider.setAttribute('aria-valuenow', String(width));
    divider.setAttribute('aria-valuetext', width + ' pixels');
  }
  function save() {
    preferred = width;
    try { localStorage.setItem(key, String(width)); } catch (_) { /* Optional. */ }
  }
  function finish(commit = false) {
    if (active === null) return;
    const pointer = active.id;
    active = null;
    body.classList.remove('navigation-resizing');
    if (divider.hasPointerCapture(pointer)) divider.releasePointerCapture(pointer);
    if (commit) save();
    else apply(preferred === null ? defaultWidth : preferred);
  }
  function layout() {
    finish();
    // Measure the unmodified theme, not our three-column override. This keeps
    // custom themes' existing breakpoint and grid/flex stacked layout intact.
    body.classList.remove('navigation-resizable');
    divider.hidden = true;
    const nav = navigation.getBoundingClientRect();
    const doc = content.getBoundingClientRect();
    maximum = Math.floor(body.getBoundingClientRect().width - contentMinimum - handleWidth);
    const horizontal = doc.left >= nav.right - 1 && Math.abs(doc.top - nav.top) < 2;
    if (!horizontal || maximum < minimum) return;
    defaultWidth = clamp(nav.width);
    body.classList.add('navigation-resizable');
    divider.hidden = false;
    apply(preferred === null ? defaultWidth : preferred);
  }
  divider.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !event.isPrimary || divider.hidden || active !== null) return;
    event.preventDefault();
    divider.focus();
    active = {id: event.pointerId, x: event.clientX, width};
    try { divider.setPointerCapture(event.pointerId); }
    catch (_) { active = null; return; }
    body.classList.add('navigation-resizing');
  });
  divider.addEventListener('pointermove', event => {
    if (active !== null && event.pointerId === active.id) {
      apply(active.width + event.clientX - active.x);
    }
  });
  divider.addEventListener('pointerup', event => {
    if (active !== null && event.pointerId === active.id) finish(true);
  });
  for (const type of ['pointercancel', 'lostpointercapture']) {
    divider.addEventListener(type, event => {
      if (active !== null && event.pointerId === active.id) finish();
    });
  }
  divider.addEventListener('keydown', event => {
    if (divider.hidden || active !== null) return;
    const values = {ArrowLeft: width - 16, ArrowRight: width + 16, Home: minimum, End: maximum};
    if (!Object.prototype.hasOwnProperty.call(values, event.key)) return;
    event.preventDefault();
    apply(values[event.key]);
    save();
  });
  divider.addEventListener('dblclick', () => {
    finish();
    preferred = null;
    try { localStorage.removeItem(key); } catch (_) { /* Optional. */ }
    layout();
  });
  window.addEventListener('resize', layout);
  window.addEventListener('blur', () => finish());
  window.addEventListener('pagehide', () => finish());
  window.addEventListener('pageshow', layout);
  layout();
})();