// Equivalence check for the pages/overview.js hunk of js-portal.patch, run on the REAL files (no re-typed copy).
// node equiv-overview-real.js <portal dir A> <portal dir B> [cases] [seed]
// Each dir holds portal.js and pages/overview.js. Both are loaded unchanged into their own node vm context with a stand-in page.
// The harness only (1) catches the page definition passed to Portal.page and (2) replaces Portal.poll with a call that hands the
// generated summary to the page at once; the page's own mount() then builds the whole Overview with build(summary).
// For every generated summary the full rendered tree (tags, attributes, text) of A and B is compared; the first difference stops the run.
// Made-up data only.
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path');
const [dirA, dirB] = [process.argv[2], process.argv[3]];
const CASES = Number(process.argv[4] || 5000);
let seed = Number(process.argv[5] || 20261112);
function rnd(n) { seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff; return (seed >>> 8) % n; } // high bits: the low bits of this generator repeat with a short period

function el(tag) {
  const o = { tag, attrs: {}, dataset: {}, style: {}, children: [], parent: null, nodeType: 1, namespaceURI: 'x', hidden: false,
    classList: { add() {}, remove() {}, contains() { return false; }, toggle() {} },
    setAttribute(k, v) { o.attrs[k] = String(v); }, getAttribute(k) { return k in o.attrs ? o.attrs[k] : null; }, removeAttribute(k) { delete o.attrs[k]; },
    addEventListener() {}, appendChild(k) { if (k && k.nodeType === 1) k.parent = o; o.children.push(k); return k; }, insertBefore(k) { return o.appendChild(k); },
    querySelectorAll() { return []; }, querySelector() { return null; }, focus() {}, remove() {}, closest() { return null; }, contains() { return false; },
    get firstChild() { return o.children[0] || null; } };
  let text = '';
  Object.defineProperty(o, 'textContent', { get() { return text; }, set(v) { text = v; if (v === '') o.children = []; } });
  Object.defineProperty(o, 'isConnected', { get() { return true; } });
  return o;
}
function loadTree(dir) {
  const els = {};
  const doc = { documentElement: el('html'), hidden: false, createElement: el, createElementNS: (ns, t) => el(t), createTextNode: (t) => ({ nodeType: 3, t }),
    getElementById: (id) => (els[id] = els[id] || el(id)), addEventListener() {}, querySelectorAll() { return []; }, querySelector() { return null; }, head: el('head'), body: el('body') };
  const win = { document: doc, location: { hash: '#/overview' }, addEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }),
    localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} }, sessionStorage: { getItem() { return null; }, setItem() {}, removeItem() {} }, scrollTo() {}, navigator: {} };
  win.window = win;
  const ctx = vm.createContext(Object.assign(win, { console, setTimeout, clearTimeout, MutationObserver: function () { this.observe = () => {}; }, fetch: () => new Promise(() => {}) }));
  vm.runInContext(fs.readFileSync(path.join(dir, 'portal.js'), 'utf8'), ctx, { filename: path.join(dir, 'portal.js') });
  const P = ctx.Portal, defs = {};
  let current = null;
  P.page = (id, def) => { defs[id] = def; };
  P.poll = (key, p, ms, onData) => { onData(current, 200); return () => {}; };
  vm.runInContext(fs.readFileSync(path.join(dir, 'pages/overview.js'), 'utf8'), ctx, { filename: path.join(dir, 'pages/overview.js') });
  if (!defs.overview) throw new Error('overview page not registered from ' + dir);
  return function render(summary) {
    current = summary;
    const root = el('main');
    const def = Object.create(defs.overview);
    def.mount.call(def, root);
    if (def.unmount) def.unmount();
    return root;
  };
}
function ser(n) {
  if (!n || typeof n !== 'object') return String(n);
  if (n.nodeType === 3) return { t: n.t };
  return [n.tag, n.attrs, n.textContent, n.children.map(ser)];
}
function findTestid(n, id) {
  if (n.attrs && n.attrs['data-testid'] === id) return n;
  for (const k of n.children || []) { const r = k.nodeType === 1 && findTestid(k, id); if (r) return r; }
  return null;
}
const STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 30, 60, 90];
function summaryFor(step, buckets) {
  return { now: 2000000, desk_started_at: 1, mode: { demo_tools: false, sample_data: false }, counts: { received: 3, new: 2, duplicate: 1, review: 0, open: 0 }, needs_action: 0, waiting: 0,
    followups: { pending: 0, sending: 0, sent: 1, failed: 0, unknown: 0, did_not_finish: 0 }, doors: [{ source: 'form', received: 3, last_seen: 1999990 }],
    series: { bucket_seconds: step, buckets }, recent: [], refused_at_door: 0, reconciled: true };
}
function gen(c) {
  // fixed edge cases first, then random ones
  const fixed = [[5, 0], [5, 1], [5, 2], [5, 3], [5, 4], [5, 60], [5, 61], [5, 62], [1, 300], [1, 301], [7, 43], [60, 5], [90, 3]];
  let step, len;
  if (c < fixed.length) [step, len] = fixed[c]; else { step = rnd(4) === 0 ? 1 + rnd(30) : STEPS[rnd(STEPS.length)]; len = rnd(4) === 0 ? rnd(4) : rnd(320); }
  const zero = rnd(3) === 0; // a third of the cases are mostly empty: the "nothing decided" branch
  const buckets = [];
  for (let i = 0; i < len; i++) {
    const v = () => (zero && rnd(10) > 0 ? 0 : rnd(6));
    buckets.push({ t: 1990000 + i * step, new: v(), duplicate: v(), review: v() });
  }
  return summaryFor(step, buckets);
}
const A = loadTree(dirA), B = loadTree(dirB);
let same = 0, withBars = 0, gOver1 = 0, partial = 0;
for (let c = 0; c < CASES; c++) {
  const s = gen(c);
  const ra = A(s), rb = B(s);
  const sa = JSON.stringify(ser(ra)), sb = JSON.stringify(ser(rb));
  const step = s.series.bucket_seconds, g = Math.max(1, Math.round(15 / step)), n = Math.min(s.series.buckets.length, Math.ceil(300 / step));
  if (g > 1) gOver1++;
  if (n % g) partial++;
  if (JSON.stringify(ser(findTestid(ra, 'activity'))).includes('ov-bar ')) withBars++;
  if (sa !== sb) {
    console.log('MISMATCH at case', c, 'bucket_seconds', step, 'buckets', s.series.buckets.length);
    console.log('A activity:', JSON.stringify(ser(findTestid(ra, 'activity'))).slice(0, 600));
    console.log('B activity:', JSON.stringify(ser(findTestid(rb, 'activity'))).slice(0, 600));
    process.exit(1);
  }
  same++;
}
const sample = gen(5); // 60 buckets of 5 s, the state probe's shape
console.log('sample activity card (60 buckets of 5 s), A:', JSON.stringify(ser(findTestid(A(sample), 'activity'))).slice(0, 400) + ' ...');
console.log(JSON.stringify({ dirA, dirB, cases: CASES, identical: same, casesWithBars: withBars, casesJoiningBuckets: gOver1, casesWithDroppedPartialGroup: partial }));
console.log('IDENTICAL full Overview render on all', same, 'generated summaries');
