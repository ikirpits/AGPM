/**
 * AGPM: recalculation of the parts based on random resampling
 * (bootstrap, split-half, quadrant stability, sensitivity, bias).
 * Source: sheet "Form responses" (Group A or B, Counted not No).
 */
var CFG = {
  source: 'Form responses',
  methodsA: ['Waterfall','Scrum','Spiral','XP','SAFe','V-Model','KIBO','ASD','PRINCE2 Agile','DevOps','Scrumban'],
  methodsB: ['Waterfall','Scrum','UP/RUP','Kanban','LeSS','Crystal','DSDM','FDD','MSF','DAD','AUP'],
  A: ['A1','A2','A3','A4','A5'], G: ['G1','G2','G3','G4','G5'],
  flagged: [],
  nBoot: 5000, nSplit: 1000, seed: 2026
};

function onOpen() {
  SpreadsheetApp.getUi().createMenu('AGPM')
    .addItem('Recalculate (bootstrap, sensitivity, bias)', 'agpmRecompute')
    .addToUi();
}

// ---------- helpers
function rng(seed) { var a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function mean(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return a.length ? s / a.length : NaN; }
function median(a) { if (!a.length) return NaN; var b = a.slice().sort(function (x, y) { return x - y; }); var m = Math.floor(b.length / 2); return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2; }
function pct(a, p) { var b = a.slice().sort(function (x, y) { return x - y; }); var h = (b.length - 1) * p, lo = Math.floor(h), hi = Math.ceil(h); return b[lo] + (b[hi] - b[lo]) * (h - lo); }
function ranks(a) { var idx = a.map(function (v, i) { return [v, i]; }).sort(function (x, y) { return x[0] - y[0]; }); var r = new Array(a.length), i = 0; while (i < idx.length) { var j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++; var avg = (i + j) / 2 + 1; for (var k = i; k <= j; k++) r[idx[k][1]] = avg; i = j + 1; } return r; }
function pearson(x, y) { var mx = mean(x), my = mean(y), sxy = 0, sx = 0, sy = 0; for (var i = 0; i < x.length; i++) { sxy += (x[i] - mx) * (y[i] - my); sx += (x[i] - mx) * (x[i] - mx); sy += (y[i] - my) * (y[i] - my); } return sxy / Math.sqrt(sx * sy); }
function spearman(x, y) { return pearson(ranks(x), ranks(y)); }
function descRank(a) { return ranks(a.map(function (v) { return -v; })); }
function normCdf(z) { var t = 1 / (1 + 0.2316419 * Math.abs(z)); var d = 0.3989423 * Math.exp(-z * z / 2); var p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return z > 0 ? 1 - p : p; }
function gammln(x) { var c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]; var y = x, t = x + 5.5; t -= (x + 0.5) * Math.log(t); var s = 1.000000000190015; for (var j = 0; j < 6; j++) s += c[j] / ++y; return -t + Math.log(2.5066282746310005 * s / x); }
function gammq(a, x) { if (x < a + 1) { var ap = a, sum = 1 / a, del = sum; for (var n = 0; n < 200; n++) { ap++; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 1e-12) break; } return 1 - sum * Math.exp(-x + a * Math.log(x) - gammln(a)); } var b = x + 1 - a, c = 1e300, d = 1 / b, h = d; for (var i = 1; i < 200; i++) { var an = -i * (i - a); b += 2; d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300; c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300; d = 1 / d; var del2 = d * c; h *= del2; if (Math.abs(del2 - 1) < 1e-12) break; } return Math.exp(-x + a * Math.log(x) - gammln(a)) * h; }
function tieSum(all) { var r = {}; all.forEach(function (v) { r[v] = (r[v] || 0) + 1; }); var s = 0; for (var k in r) s += Math.pow(r[k], 3) - r[k]; return s; }
function kruskal(groups) { var all = [].concat.apply([], groups), N = all.length, rk = ranks(all), pos = 0, H = 0; groups.forEach(function (g) { var s = 0; for (var i = 0; i < g.length; i++) s += rk[pos + i]; pos += g.length; H += s * s / g.length; }); H = 12 / (N * (N + 1)) * H - 3 * (N + 1); H /= 1 - tieSum(all) / (N * N * N - N); return gammq((groups.length - 1) / 2, H / 2); }
function mannWhitney(a, b) { var all = a.concat(b), N = all.length, rk = ranks(all), r1 = 0; for (var i = 0; i < a.length; i++) r1 += rk[i]; var u = r1 - a.length * (a.length + 1) / 2, mu = a.length * b.length / 2; var sd = Math.sqrt(a.length * b.length / 12 * ((N + 1) - tieSum(all) / (N * (N - 1)))); var z = (Math.abs(u - mu) - 0.5) / sd; return 2 * (1 - normCdf(z)); }
function quad(x, y, t) { return x >= t ? (y >= t ? 'Integrated Leaders' : 'Agile-First') : (y >= t ? 'Governance-Heavy' : 'Baseline'); }

// ---------- data
function loadData() {
  var sh = SpreadsheetApp.getActive().getSheetByName(CFG.source);
  var v = sh.getDataRange().getValues(), h = v[0], col = {};
  h.forEach(function (x, i) { col[String(x)] = i; });
  var raters = { A: [], B: [] };
  for (var r = 1; r < v.length; r++) {
    var row = v[r], g = String(row[col['Group']]), c = String(row[col['Counted']]);
    if (!row[col['Email']] || (g !== 'A' && g !== 'B') || c === 'No') continue;
    var ms = g === 'A' ? CFG.methodsA : CFG.methodsB, sc = {};
    ms.forEach(function (m) { CFG.A.concat(CFG.G).forEach(function (k) { var x = row[col[m + ' (' + k + ')']]; sc[m + '|' + k] = (x === '' || x === null || isNaN(Number(x))) ? null : Number(x); }); });
    raters[g].push({ email: String(row[col['Email']]).toLowerCase(), exp: String(row[col['Experience']] || 'n/a'), sc: sc });
  }
  return raters;
}
function methods() { var s = {}; CFG.methodsA.concat(CFG.methodsB).forEach(function (m) { s[m] = 1; }); return Object.keys(s); }
// X,Y per method: mean (or median) of all stacked values in each group, then average of the groups
function xy(data, gcodes, agg) {
  agg = agg || 'mean'; gcodes = gcodes || CFG.G; var out = {};
  methods().forEach(function (m) {
    var xs = [], ys = [];
    ['A', 'B'].forEach(function (g) {
      var ms = g === 'A' ? CFG.methodsA : CFG.methodsB; if (ms.indexOf(m) < 0) return;
      var vx = [], vy = [];
      data[g].forEach(function (rt) { CFG.A.forEach(function (k) { var x = rt.sc[m + '|' + k]; if (x !== null) vx.push(x); }); gcodes.forEach(function (k) { var y = rt.sc[m + '|' + k]; if (y !== null) vy.push(y); }); });
      var f = agg === 'median' ? median : mean;
      if (vx.length) xs.push(f(vx)); if (vy.length) ys.push(f(vy));
    });
    var X = mean(xs), Y = mean(ys); out[m] = { X: X, Y: Y, G: 2 * X * Y / (X + Y) };
  });
  return out;
}
function resample(data, rand) { var o = {}; ['A', 'B'].forEach(function (g) { var d = data[g], n = d.length, s = []; for (var i = 0; i < n; i++) s.push(d[Math.floor(rand() * n)]); o[g] = s; }); return o; }
function shuffle(a, rand) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rand() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
function writeByMethod(sheet, firstRow, lastRow, colStart, rowsByMethod) {
  var names = sheet.getRange(firstRow, 1, lastRow - firstRow + 1, 1).getValues();
  var out = names.map(function (n) { return rowsByMethod[n[0]] || rowsByMethod[String(n[0])] || null; });
  var w = 0; out.forEach(function (r) { if (r) w = r.length; });
  sheet.getRange(firstRow, colStart, out.length, w).setValues(out.map(function (r) { return r || new Array(w).fill(''); }));
}

// ---------- main
function agpmRecompute() {
  var ss = SpreadsheetApp.getActive(), data = loadData(), M = methods(), full = xy(data), rand = rng(CFG.seed);
  var stamp = Utilities.formatDate(new Date(), ss.getSpreadsheetTimeZone(), 'dd/MM/yyyy HH:mm') + ' (A ' + data.A.length + ', B ' + data.B.length + ' raters)';
  var fullG = M.map(function (m) { return full[m].G; });
  // bootstrap
  var B = [];
  for (var b = 0; b < CFG.nBoot; b++) B.push(xy(resample(data, rand)));
  // split-half
  var sh = [];
  for (var s = 0; s < CFG.nSplit; s++) {
    var h1 = {}, h2 = {};
    ['A', 'B'].forEach(function (g) { var p = shuffle(data[g], rand), k = Math.floor(p.length / 2); h1[g] = p.slice(0, k); h2[g] = p.slice(k); });
    var a = xy(h1), c = xy(h2); sh.push(spearman(M.map(function (m) { return a[m].G; }), M.map(function (m) { return c[m].G; })));
  }
  // tab 3
  var t3 = ss.getSheetByName('3 Bootstrap'), rk = {}, gb = {};
  M.forEach(function (m) { rk[m] = []; gb[m] = []; });
  B.forEach(function (bb) { var r = descRank(M.map(function (m) { return bb[m].G; })); M.forEach(function (m, i) { rk[m].push(r[i]); gb[m].push(bb[m].G); }); });
  t3.getRange('B3:B6').setValues([[r3(mean(sh))], [r3(median(sh))], [r3(pct(sh, 0.05))], [stamp]]);
  var rr = {}, gg = {};
  M.forEach(function (m) { rr[m] = [Math.round(pct(rk[m], 0.025)), Math.round(pct(rk[m], 0.975))]; gg[m] = [r3(pct(gb[m], 0.025)), r3(pct(gb[m], 0.975))]; });
  writeByMethod(t3, 10, 29, 6, rr); writeByMethod(t3, 10, 29, 9, gg);
    // tab 4
  var t4 = ss.getSheetByName('4 Quadrants'), q = {}, q2 = {};
  M.forEach(function (m) {
    var row = [];
    [3, 2.75, 2.5].forEach(function (t) { var base = quad(full[m].X, full[m].Y, t), k = 0; B.forEach(function (bb) { if (quad(bb[m].X, bb[m].Y, t) === base) k++; }); row.push(Math.round(100 * k / B.length)); });
    var xs = B.map(function (bb) { return bb[m].X; }), ys = B.map(function (bb) { return bb[m].Y; });
    q[m] = row.concat([r2(pct(xs, .025)), r2(pct(xs, .975)), r2(pct(ys, .025)), r2(pct(ys, .975))]);
    q2[m] = [3.25, 3.5].map(function (t) { var base = quad(full[m].X, full[m].Y, t), k = 0; B.forEach(function (bb) { if (quad(bb[m].X, bb[m].Y, t) === base) k++; }); return Math.round(100 * k / B.length); });
  });
  writeByMethod(t4, 7, 26, 5, q); writeByMethod(t4, 7, 26, 12, q2); t4.getRange('B4').setValue(stamp);
  // tab 5
  var top = function (o) { return M.slice().sort(function (a, b) { return o[b].G - o[a].G; }).slice(0, 3); };
  var topF = top(full);
  var cmp = function (o, label, note) {
    var rho = spearman(fullG, M.map(function (m) { return o[m].G; })), t = top(o);
    var ch = M.filter(function (m) { return quad(full[m].X, full[m].Y, 3) !== quad(o[m].X, o[m].Y, 3); });
    var same = t.slice().sort().join() === topF.slice().sort().join();
    return [label, r3(rho), t.join(', '), same ? 'Yes' : 'No', ch.length, ch.length ? ch.join(', ') : 'none', note || ''];
  };
  var without = function (list) { return CFG.G.filter(function (k) { return list.indexOf(k) < 0; }); };
  var flagged = { A: data.A.filter(function (r) { return CFG.flagged.indexOf(r.email) < 0; }), B: data.B.filter(function (r) { return CFG.flagged.indexOf(r.email) < 0; }) };
  var rows5 = [['Scenario', 'Spearman of GABS ranking vs main model', 'Top three', 'Same top three', 'Quadrant changes (threshold 3.0)', 'Methods that change', 'Note'],
    cmp(full, 'Main model'), cmp(xy(data, CFG.G, 'median'), 'Median instead of mean', 'The integer scale produces ties'),
    cmp(xy(data, without(['G1'])), 'Without G1'), cmp(xy(data, without(['G4'])), 'Without G4'), cmp(xy(data, without(['G1', 'G4'])), 'Without G1 and G4'),
    cmp(xy(flagged), 'Without the raters on the check list', CFG.flagged.join(', '))];
  var loo = [];
  ['A', 'B'].forEach(function (g) { data[g].forEach(function (_, i) { var d = { A: data.A, B: data.B }; d[g] = data[g].filter(function (__, j) { return j !== i; }); var o = xy(d); loo.push([spearman(fullG, M.map(function (m) { return o[m].G; })), M.filter(function (m) { return quad(full[m].X, full[m].Y, 3) !== quad(o[m].X, o[m].Y, 3); }).length, top(o).slice().sort().join() === topF.slice().sort().join()]); }); });
  rows5.push(['Leave-one-rater-out (each rater removed once)', 'minimum ' + fmt(Math.min.apply(null, loo.map(function (x) { return x[0]; })), 3), '', 'Yes in ' + loo.filter(function (x) { return x[2]; }).length + ' of ' + loo.length, 'up to ' + Math.max.apply(null, loo.map(function (x) { return x[1]; })), '', loo.length + ' runs']);
  var t5 = ss.getSheetByName('5 Sensitivity');
  t5.getRange('A4:G40').clearContent();
  t5.getRange(4, 1, rows5.length, 7).setValues(rows5);
  t5.getRange(4 + rows5.length + 1, 1, 3, 1).setValues([['Quadrant thresholds: see tab 4.'], ['Last recalculation: ' + stamp], ['Rater check list and settings: at the top of the Apps Script (CFG).']]);
  // tab 6
  var pr = [];
  ['A', 'B'].forEach(function (g) { var ms = g === 'A' ? CFG.methodsA : CFG.methodsB; data[g].forEach(function (rt) { var vx = [], vy = []; ms.forEach(function (m) { CFG.A.forEach(function (k) { var x = rt.sc[m + '|' + k]; if (x !== null) vx.push(x); }); CFG.G.forEach(function (k) { var y = rt.sc[m + '|' + k]; if (y !== null) vy.push(y); }); }); pr.push({ exp: rt.exp, x: vx.length ? mean(vx) : null, y: vy.length ? mean(vy) : null }); }); });
  var exps = {}; pr.forEach(function (p) { (exps[p.exp] = exps[p.exp] || []).push(p); });
  var rows6 = [['A. Experience', '', '', '', ''], ['Experience', 'Raters', 'Mean X', 'Mean Y', '']];
  Object.keys(exps).sort().forEach(function (e) { var xs = exps[e].filter(function (p) { return p.x !== null; }).map(function (p) { return p.x; }), ys = exps[e].filter(function (p) { return p.y !== null; }).map(function (p) { return p.y; }); rows6.push([e, xs.length, r2(mean(xs)), ys.length ? r2(mean(ys)) : '', '']); });
  var kg = Object.keys(exps).map(function (e) { return exps[e].filter(function (p) { return p.x !== null; }).map(function (p) { return p.x; }); }).filter(function (a) { return a.length >= 3; });
  rows6.push(['Kruskal-Wallis (groups with at least 3 raters), p', kg.length > 1 ? r2(kruskal(kg)) : 'n/a', '', '', '']);
  var done = pr.filter(function (p) { return p.y !== null && p.x !== null; }).map(function (p) { return p.x; }), notd = pr.filter(function (p) { return p.y === null && p.x !== null; }).map(function (p) { return p.x; });
  rows6.push(['', '', '', '', ''], ['B. Dropout after session 1', '', '', '', ''], ['Rater group', 'Raters', 'Mean X', '', ''],
    ['Completed both sessions', done.length, r2(mean(done)), '', ''], ['Session 1 only', notd.length, notd.length ? r2(mean(notd)) : '', '', ''],
    ['Mann-Whitney, p', (done.length && notd.length) ? r2(mannWhitney(done, notd)) : 'n/a', '', '', ''], ['', '', '', '', ''],
    ['C. Group comparison on the shared methods', '', '', '', ''], ['Method', 'Axis', 'Group A', 'Group B', 'Mann-Whitney, p']);
  ['Waterfall', 'Scrum'].forEach(function (m) { [['X', CFG.A], ['Y', CFG.G]].forEach(function (ax) { var per = function (g) { return data[g].map(function (rt) { var v = ax[1].map(function (k) { return rt.sc[m + '|' + k]; }).filter(function (x) { return x !== null; }); return v.length ? mean(v) : null; }).filter(function (x) { return x !== null; }); }; var a = per('A'), b = per('B'); rows6.push([m, ax[0], r2(mean(a)), r2(mean(b)), r2(mannWhitney(a, b))]); }); });
  rows6.push(['', '', '', '', ''], ['Last recalculation: ' + stamp, '', '', '', '']);
  var t6 = ss.getSheetByName('6 Bias');
  t6.getRange('A4:E45').clearContent();
  t6.getRange(4, 1, rows6.length, 5).setValues(rows6);
  ss.toast('Done: ' + stamp, 'AGPM', 8);
}
function r2(x) { return isFinite(x) ? Math.round(x * 100) / 100 : ''; }
function r3(x) { return isFinite(x) ? Math.round(x * 1000) / 1000 : ''; }
function fmt(x, d) { return (Math.round(x * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d).replace('.', ','); }
