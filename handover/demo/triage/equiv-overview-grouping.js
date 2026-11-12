// Proof that the new bucket-joining loop (pages/overview.js activityCard) gives the same result as the old
// slice().forEach() version, over many random made-up inputs. Run: node equiv-overview-grouping.js
function oldWay(b0, g) { var b = []; for (var j = 0; j < b0.length; j += g) { var grp = { t: b0[j].t, 'new': 0, duplicate: 0, review: 0 };
  b0.slice(j, j + g).forEach(function (x) { grp['new'] += x['new']; grp.duplicate += x.duplicate; grp.review += x.review; }); b.push(grp); } return b; }
function newWay(b0, g) { var b = []; for (var j = 0; j < b0.length; j += g) { var grp = { t: b0[j].t, 'new': 0, duplicate: 0, review: 0 };
  for (var jj = j, jEnd = Math.min(j + g, b0.length); jj < jEnd; jj++) { grp['new'] += b0[jj]['new']; grp.duplicate += b0[jj].duplicate; grp.review += b0[jj].review; } b.push(grp); } return b; }
var seed = 12345; function rnd(n) { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed % n; }
var cases = 0;
for (var c = 0; c < 20000; c++) {
  var len = rnd(60), g = 1 + rnd(9), b0 = [];
  for (var i = 0; i < len; i++) b0.push({ t: i * 5, 'new': rnd(5), duplicate: rnd(5), review: rnd(5) });
  if (JSON.stringify(oldWay(b0, g)) !== JSON.stringify(newWay(b0, g))) { console.log('MISMATCH', len, g); process.exit(1); }
  cases++;
}
console.log('equivalent on', cases, 'random cases (incl. empty list and partial last group)');
