#!/usr/bin/env python3
"""Sensitivity analysis excluding KIBO (the authors' own method) from the comparative set.
Usage: python agpm_kibo_exclusion.py AGPM_dataset_anonymized.xlsx
Method-level scores follow agpm_robustness.py (all ratings of an axis stacked within a group, group means averaged for
methods rated in both groups). The primary results are recomputed first as a check, then KIBO is removed and the
agility-governance gap, the exact Wilcoxon signed-rank test (X versus Y), the Spearman correlation between X and Y,
the quadrant counts at the 3.0 threshold and the GABS ranking of the remaining 19 methods are reported.
Writes agpm_kibo_exclusion.csv."""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr, wilcoxon
SRC = sys.argv[1] if len(sys.argv) > 1 else 'AGPM_dataset_anonymized.xlsx'
OWN = 'KIBO'
L = pd.read_excel(SRC, 'Ratings_long')
methods = sorted(L.method.unique())
if OWN not in methods: raise ValueError(f'{OWN} not found among methods: {methods}')
A = [f'A{i}' for i in range(1, 6)]; G = [f'G{i}' for i in range(1, 6)]
def scores(L):
    X = {}; Y = {}
    for (m, g), d in L.groupby(['method', 'group']):
        X.setdefault(m, []).append(d[d.criterion.isin(A)].score.mean()); Y.setdefault(m, []).append(d[d.criterion.isin(G)].score.mean())
    ms = sorted(X); x = np.array([np.mean(X[m]) for m in ms]); y = np.array([np.mean(Y[m]) for m in ms])
    return ms, x, y, 2 * x * y / (x + y)
def quad(x, y, t=3.0): return np.where(x >= t, np.where(y >= t, 'Integrated Leaders', 'Agile-First'), np.where(y >= t, 'Governance-Heavy', 'Baseline'))
def crit_means(L):
    c = {}
    for (m, g, k), d in L.groupby(['method', 'group', 'criterion']): c.setdefault((m, k), []).append(d.score.mean())
    return c
def summary(L, label, drop=None):
    ms, x, y, g = scores(L); q = quad(x, y)
    w = wilcoxon(x, y, method='exact'); rho, p = spearmanr(x, y)
    cm = crit_means(L); ag = [np.mean([np.mean(cm[(m, k)]) for m in ms]) for k in A]; gv = [np.mean([np.mean(cm[(m, k)]) for m in ms]) for k in G]
    return dict(set=label, methods=len(ms), mean_agility=round(x.mean(), 4), mean_governance=round(y.mean(), 4), gap_Y_minus_X=round((y - x).mean(), 4),
                governance_below_agility=f'{int((y < x).sum())}/{len(ms)}', integrated_leaders=int((q == 'Integrated Leaders').sum()),
                agile_first=int((q == 'Agile-First').sum()), governance_heavy=int((q == 'Governance-Heavy').sum()), baseline=int((q == 'Baseline').sum()),
                wilcoxon_statistic=float(w.statistic), wilcoxon_exact_p=round(float(w.pvalue), 5), spearman_X_Y=round(float(rho), 3), spearman_p=round(float(p), 4),
                lowest_agility_criterion_mean=round(min(ag), 3), highest_governance_criterion_mean=round(max(gv), 3),
                top3=', '.join(np.array(ms)[np.argsort(-g)[:3]])), ms, x, y, g, q
full, ms0, x0, y0, g0, q0 = summary(L, 'All 20 methods')
ex, ms1, x1, y1, g1, q1 = summary(L[L.method != OWN], 'Excluding KIBO')
# ranking agreement of the remaining 19 methods and quadrant changes
idx = [i for i, m in enumerate(ms0) if m != OWN]
ex['spearman_gabs_vs_full'] = round(float(spearmanr(g0[idx], g1)[0]), 3)
ex['quadrant_changes_vs_full'] = int((q0[idx] != q1).sum())
full['spearman_gabs_vs_full'] = ''; full['quadrant_changes_vs_full'] = ''
R = pd.DataFrame([full, ex]).T; print(R.to_string(header=False))
pd.DataFrame([full, ex]).to_csv('agpm_kibo_exclusion.csv', index=False)
