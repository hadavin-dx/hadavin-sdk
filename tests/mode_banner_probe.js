// Test harness (run by tests/test_mode_banner.py): paints a banner into a tiny stand-in page with the real
// templates/mode-banner/mode_banner.js and prints what a person would see.
// argv: <js path> <json banner | undefined> [scenario]. Scenarios build the awkward inputs JSON cannot hold.
const api = require(process.argv[2]);
const htmlWrites = []; // every write that would make a page parse HTML; the tests demand none
function el(tag, opts) {
  const o = { tag, cls: '', attrs: Object.assign({}, (opts && opts.attrs) || {}), children: [], hidden: true, text: (opts && opts.text) || '' };
  o.appendChild = (k) => { if (opts && opts.failAppend) throw new Error('append failed'); o.children.push(k); return k; };
  o.setAttribute = (k, v) => { if (opts && (opts.failAttr === true || opts.failAttr === k)) throw new Error('attribute write failed'); o.attrs[k] = String(v); };
  Object.defineProperty(o, 'textContent', { get() { return o.text; }, set(v) { if (opts && opts.failText && v !== '') throw new Error('text write failed'); o.text = v; o.children = []; } });
  Object.defineProperty(o, 'className', { get() { return o.cls; }, set(v) { o.cls = v; } });
  for (const k of ['innerHTML', 'outerHTML']) {
    Object.defineProperty(o, k, { get() { return ''; }, set(v) { htmlWrites.push(k); } });
  }
  for (const k of ['insertAdjacentHTML', 'insertAdjacentElement', 'createContextualFragment']) {
    o[k] = () => { htmlWrites.push(k); };
  }
  return o;
}
let doc = { createElement: (t) => el(t) };
const scenario = process.argv[4] || '';
const raw = process.argv[3];
let input = raw === 'undefined' ? undefined : JSON.parse(raw);
const boom = () => { throw new Error('boom'); };
if (scenario === 'throwing-getter') input = { get tone() { return boom(); }, tag: 'T', text: 'x', real: [], stand_ins: [], mode: 'demo' };
if (scenario === 'proxy') input = new Proxy({}, { get: boom, has: boom, ownKeys: boom, getPrototypeOf: boom });
if (scenario === 'throwing-list') input = { ...input, real: new Proxy([], { get: boom }) };
if (scenario === 'huge-text') input = { ...input, text: '\u{1F600}'.repeat(5000000) };
if (scenario === 'throwing-doc') doc = { createElement: () => { throw new Error('doc broken'); } };
let target = el('div', scenario === 'failing-append' ? { failAppend: true } : scenario === 'failing-every-attribute' ? { failAttr: true, text: 'previous banner text' } : scenario === 'failing-tone-attr' ? { failAttr: 'data-tone', text: 'previous banner text' } : scenario === 'failing-mode-attr' ? { failAttr: 'data-mode' } : scenario === 'failing-text-over-old-claim' ? { failAppend: true, failText: true, text: 'DEMO Every record here is made-up demo data.', attrs: { 'data-tone': 'demo', 'data-mode': 'demo' } } : scenario === 'failing-all-writes' ? { failAppend: true, failText: true, text: 'previous banner text' } : null);
if (scenario === 'null-el') target = null;
let threw = '';
let usableThrew = '';
try { api.usable(input); } catch (e) { usableThrew = String(e.message); }
let shown = null;
// counted work instead of a clock: how many times the page asked Array.from to walk a string while it painted
let arrayFromCalls = 0;
let arrayFromLongest = 0; // the longest string (in UTF-16 units) the page asked Array.from to walk
const realArrayFrom = Array.from;
Array.from = function (...args) { arrayFromCalls++; if (typeof args[0] === 'string') arrayFromLongest = Math.max(arrayFromLongest, args[0].length); return realArrayFrom.apply(this, args); };
const t0 = Date.now();
try { shown = api.paint(target, input, doc); } catch (e) { threw = String(e.message); }
const arrayFromSeen = arrayFromCalls;
Array.from = realArrayFrom;
const lines = target ? target.children.map((c) => ({ cls: c.cls, text: c.text })) : [];
console.log(JSON.stringify({
  lines, tone: target ? target.attrs['data-tone'] : null, mode: target ? target.attrs['data-mode'] : null,
  hidden: target ? target.hidden : null, text: target ? target.text : null, notConfirmed: api.NOT_CONFIRMED,
  shownTone: shown ? shown.tone : null, modes: api.MODES, tones: api.TONES, maxText: api.MAX_TEXT, htmlWrites, threw, usableThrew, ms: Date.now() - t0, arrayFromCalls: arrayFromSeen, arrayFromLongest,
  frozen: [api, api.NOT_CONFIRMED, api.NOT_CONFIRMED.real, api.NOT_CONFIRMED.stand_ins, api.TONES, api.MODES].map(Object.isFrozen),
}));
