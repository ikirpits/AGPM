#!/usr/bin/env python3
"""Median aggregation, exclusion of G1 and/or G4, and alternative quadrant thresholds (manuscript Tables 8 and 9),
from the anonymized ratings. Usage: python agpm_robustness.py AGPM_dataset_anonymized.xlsx [seed]
Aggregation follows Code.gs: values of all raters and criteria of an axis are stacked within a group, the mean (or median) is
taken, and the group results are averaged for methods rated in both groups. Bootstrap: 5,000 resamples of raters within group.
Threshold stability is the share of resamples in which a method stays in its quadrant, reported as the number of methods
with at least 90 percent stability (Code.gs, tab 4, uses a different random generator, so small differences are possible)."""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr
SRC = sys.argv[1] if len(sys.argv) > 1 else 'AGPM_dataset_anonymized.xlsx'
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
L = pd.read_excel(SRC, 'Ratings_long')
methods = sorted(L.method.unique()); mi = {m: i for i, m in enumerate(methods)}
A = [f'A{i}' for i in range(1, 6)]; G = [f'G{i}' for i in range(1, 6)]

def xy(gcodes, agg='mean', L=L):
    X = {}; Y = {}
    for (m, g), d in L.groupby(['method', 'group']):
        f = np.median if agg == 'median' else np.mean
        X.setdefault(m, []).append(f(d[d.criterion.isin(A)].score)); Y.setdefault(m, []).append(f(d[d.criterion.isin(gcodes)].score))
    x = np.array([np.mean(X[m]) for m in methods]); y = np.array([np.mean(Y[m]) for m in methods]); return x, y, 2 * x * y / (x + y)
def quad(x, y, t=3.0): return np.where(x >= t, 'A', 'a') + np.where(y >= t, 'G', 'g')
x0, y0, g0 = xy(G); q0 = quad(x0, y0)
rows = []
for name, gc, agg in [('Median instead of mean', G, 'median'), ('Excluding G1', G[1:], 'mean'), ('Excluding G4', [c for c in G if c != 'G4'], 'mean'),
                      ('Excluding G1 and G4', [c for c in G if c not in ('G1', 'G4')], 'mean')]:
    x, y, g = xy(gc, agg); q = quad(x, y)
    rows.append(dict(scenario=name, spearman_vs_main=round(spearmanr(g0, g)[0], 3), quadrant_changes=int((q != q0).sum()),
                     changed=', '.join(np.array(methods)[q != q0]), top3=', '.join(np.array(methods)[np.argsort(-g)[:3]])))
R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv('agpm_robustness_scenarios.csv', index=False)

# bootstrap quadrant stability at several thresholds
rng = np.random.default_rng(SEED); NB = 5000
grp = {}
for g, d in L.groupby('group'):
    rs = sorted(d.rater_id.unique()); S = {k: np.zeros((len(rs), 20)) for k in ('sx', 'cx', 'sy', 'cy')}
    for r, m, c, v in zip(d.rater_id, d.method, d.criterion, d.score):
        i = rs.index(r); j = mi[m]
        if c in A: S['sx'][i, j] += v; S['cx'][i, j] += 1
        else: S['sy'][i, j] += v; S['cy'][i, j] += 1
    grp[g] = S
both = np.array([[m in set(L[L.group == g].method) for m in methods] for g in ('A', 'B')])
XB = np.zeros((NB, 20)); YB = np.zeros((NB, 20))
for b in range(NB):
    xs = np.full((2, 20), np.nan); ys = np.full((2, 20), np.nan)
    for k, g in enumerate(('A', 'B')):
        S = grp[g]; n = S['sx'].shape[0]; w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        with np.errstate(invalid='ignore', divide='ignore'):
            xs[k] = (w @ S['sx']) / (w @ S['cx']); ys[k] = (w @ S['sy']) / (w @ S['cy'])
    XB[b] = np.nanmean(xs, 0); YB[b] = np.nanmean(ys, 0)
out = []
for t in (3.0, 2.75, 2.5, 3.25, 3.5):
    base = quad(x0, y0, t); share = (quad(XB, YB, t) == base).mean(0)
    out.append(dict(threshold=t, methods_ge_90pct_stable=int((share >= .9).sum()), integrated_leaders=int((base == 'AG').sum()),
                    min_share_integrated_leaders=round(float(share[base == 'AG'].min()), 4) if (base == 'AG').any() else None))
T = pd.DataFrame(out); print(); print(T.to_string(index=False)); T.to_csv('agpm_threshold_stability.csv', index=False)
# methods closest to the 90 percent line at each threshold (for transparency)
for t in (3.25,):
    share = (quad(XB, YB, t) == quad(x0, y0, t)).mean(0)
    near = [(methods[i], round(float(share[i]), 3)) for i in np.argsort(np.abs(share - .9))[:3]]
    print('\nClosest to 90 percent at', t, near)
