// Test harness (run by tests/test_mode_banner.py): paints a banner into a tiny stand-in page with the real
// templates/mode-banner/mode_banner.js and prints what a person would see. argv: <js path> <json banner>.
const api = require(process.argv[2]);
function el(tag) {
  const o = { tag, cls: '', attrs: {}, children: [], hidden: true, text: '' };
  o.appendChild = (k) => { o.children.push(k); return k; };
  o.setAttribute = (k, v) => { o.attrs[k] = String(v); };
  Object.defineProperty(o, 'textContent', { get() { return o.text; }, set(v) { o.text = v; if (v === '') o.children = []; } });
  Object.defineProperty(o, 'className', { get() { return o.cls; }, set(v) { o.cls = v; } });
  return o;
}
const doc = { createElement: el };
const target = el('div');
const raw = process.argv[3];
const input = raw === 'undefined' ? undefined : JSON.parse(raw);
const shown = api.paint(target, input, doc);
const lines = target.children.map((c) => ({ cls: c.cls, text: c.text }));
console.log(JSON.stringify({ lines, tone: target.attrs['data-tone'], mode: target.attrs['data-mode'], hidden: target.hidden, notConfirmed: api.NOT_CONFIRMED, shownTone: shown.tone }));
