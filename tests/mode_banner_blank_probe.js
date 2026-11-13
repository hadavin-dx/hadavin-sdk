// Test harness (run by tests/test_mode_banner.py): which single characters does the page read as "nothing visible"?
// argv: <js path>. Prints JSON: the code points the page treats as blank as inclusive ranges, and the code points that
// JavaScript's own trim() calls white space (a test compares both with Python's str.isspace and the Python list).
const api = require(process.argv[2]);
function ranges(test) {
  const out = [];
  let start = -1;
  for (let cp = 0; cp <= 0x10ffff; cp++) {
    if (cp >= 0xd800 && cp <= 0xdfff) { if (start >= 0) { out.push([start, cp - 1]); start = -1; } continue; }
    if (test(cp)) { if (start < 0) start = cp; } else if (start >= 0) { out.push([start, cp - 1]); start = -1; }
  }
  if (start >= 0) out.push([start, 0x10ffff]);
  return out;
}
const page = ranges((cp) => api.usable({ mode: 'demo', tone: 'demo', tag: String.fromCodePoint(cp), text: 'x', standins: '', real: [], stand_ins: [], overridden: [] }).tone !== 'demo');
const trim = ranges((cp) => String.fromCodePoint(cp).trim() === '');
console.log(JSON.stringify({ page, trim }));
