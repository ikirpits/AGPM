"""Inter-rater reliability for the AGPM ratings, computed from the anonymized dataset.
Usage: python agpm_reliability.py AGPM_dataset_anonymized.xlsx [seed]

Outputs (printed, and written next to the script):
  agpm_reliability_criterion_level.csv   Supplementary Table S1 (per group and criterion)
  agpm_reliability_panel_level.csv       per group and dimension
and prints the split-half and leave-one-rater-out stability of the GABS ranking.

Definitions
  Ordinal alpha: Krippendorff's alpha for ordinal data (missing ratings allowed). Targets are the methods
    of a group (criterion level) or the method x criterion cells of a dimension (panel level).
  ICC(A,1) and ICC(A,k): two-way random effects, absolute agreement, single rater and mean of k raters
    (McGraw and Wong, 1996). Rows are targets (methods), columns are raters. At panel level each rater's score
    is the mean of the criteria of the dimension. Raters who did not complete a session
    are dropped from the criteria of that session. Cells with missing ratings use the complete-case rows.
  Same score and Within 1 point: share of rater pairs, over all targets, with identical scores or scores
    that differ by at most one point.
  Thresholds: alpha >= 0.667 is the conventional lower limit for tentative conclusions and >= 0.80 for
    reliable conclusions (Krippendorff, 2004; Hayes and Krippendorff, 2007). They are applied to the
    rater-level alpha; the ICC(A,k) of the mean ratings is reported separately because the study
    interprets the aggregated ratings."""
import sys, itertools, numpy as np, pandas as pd
from scipy.stats import spearmanr

SRC = sys.argv[1] if len(sys.argv) > 1 else 'AGPM_dataset_anonymized.xlsx'
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
L = pd.read_excel(SRC, 'Ratings_long')
CR = [f'A{i}' for i in range(1, 6)] + [f'G{i}' for i in range(1, 6)]

def krippendorff_ordinal(M):
    """M: raters x targets (nan = missing). Ordinal metric on the 1-5 categories."""
    cats = np.arange(1, 6)
    o = np.zeros((5, 5))
    for j in range(M.shape[1]):
        v = M[:, j]; v = v[~np.isnan(v)].astype(int)
        m = len(v)
        if m < 2: continue
        for a, b in itertools.permutations(range(m), 2):
            o[v[a] - 1, v[b] - 1] += 1.0 / (m - 1)
    n_c = o.sum(1); n = n_c.sum()
    def d2(c, k):
        lo, hi = min(c, k), max(c, k)
        return (n_c[lo:hi + 1].sum() - (n_c[lo] + n_c[hi]) / 2) ** 2
    num = sum(o[c, k] * d2(c, k) for c in range(5) for k in range(5))
    den = sum(n_c[c] * n_c[k] * d2(c, k) for c in range(5) for k in range(5)) / (n - 1)
    return 1 - num / den

def icc_a(M):
    """M: targets x raters, complete cases only. Returns ICC(A,1), ICC(A,k)."""
    n, k = M.shape; g = M.mean()
    ssr = k * ((M.mean(1) - g) ** 2).sum(); ssc = n * ((M.mean(0) - g) ** 2).sum()
    sst = ((M - g) ** 2).sum(); sse = sst - ssr - ssc
    msr = ssr / (n - 1); msc = ssc / (k - 1); mse = sse / ((n - 1) * (k - 1))
    a1 = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    ak = (msr - mse) / (msr + (msc - mse) / n)
    return a1, ak

def pair_agree(M):
    """M: raters x targets. Share of rater pairs with equal scores and within one point."""
    eq = w1 = tot = 0
    for j in range(M.shape[1]):
        v = M[:, j]; v = v[~np.isnan(v)]
        for a, b in itertools.combinations(v, 2):
            tot += 1; eq += a == b; w1 += abs(a - b) <= 1
    return 100 * eq / tot, 100 * w1 / tot

def matrix(d, targets):
    """raters x targets matrix from long data; targets are (method, criterion) tuples."""
    raters = sorted(d.rater_id.unique()); ri = {r: i for i, r in enumerate(raters)}
    ti = {t: i for i, t in enumerate(targets)}
    M = np.full((len(raters), len(targets)), np.nan)
    for r, m, c, s in zip(d.rater_id, d.method, d.criterion, d.score):
        if (m, c) in ti: M[ri[r], ti[(m, c)]] = s
    return M

rows = []; panel = []
for g, dg in L.groupby('group'):
    methods = sorted(dg.method.unique())
    for c in CR:
        t = [(m, c) for m in methods]; M = matrix(dg[dg.criterion == c], t)
        M = M[~np.isnan(M).all(1)]
        M = M[(~np.isnan(M)).sum(1) == len(methods)]   # raters who rated every method on this criterion
        a1, ak = icc_a(M.T); s, w = pair_agree(M)
        rows.append([g, c, M.shape[0], round(krippendorff_ordinal(M), 3), round(s), round(w), round(a1, 3), round(ak, 3)])
    for dim, cs in (('Agility', CR[:5]), ('Governance', CR[5:])):
        t = [(m, c) for m in methods for c in cs]; M = matrix(dg[dg.criterion.isin(cs)], t)
        M = M[(~np.isnan(M)).sum(1) == len(t)]
        alpha = krippendorff_ordinal(M)                      # targets: method x criterion cells
        W = M.reshape(M.shape[0], len(methods), len(cs)).mean(2)   # rater's mean over the dimension, per method
        a1, ak = icc_a(W.T)                                  # targets: methods
        panel.append([g, dim, M.shape[0], len(t), round(alpha, 3), round(a1, 3), round(ak, 3)])
S1 = pd.DataFrame(rows, columns=['Group', 'Criterion', 'Raters', 'Ordinal alpha', 'Same score (%)', 'Within 1 point (%)', 'ICC(A,1)', 'ICC(A,k)'])
P = pd.DataFrame(panel, columns=['Group', 'Dimension', 'Raters', 'Targets', 'Ordinal alpha', 'ICC(A,1)', 'ICC(A,k)'])
S1.to_csv('agpm_reliability_criterion_level.csv', index=False); P.to_csv('agpm_reliability_panel_level.csv', index=False)
print(S1.to_string(index=False)); print(); print(P.to_string(index=False))
print('\nCriterion-level ordinal alpha range', S1['Ordinal alpha'].min(), 'to', S1['Ordinal alpha'].max(),
      '| criteria with alpha >= 0.667:', int((S1['Ordinal alpha'] >= 0.667).sum()), 'of', len(S1), '| >= 0.80:', int((S1['Ordinal alpha'] >= 0.80).sum()))
print('Panel-level ordinal alpha', P['Ordinal alpha'].min(), 'to', P['Ordinal alpha'].max(), '| ICC(A,k)', P['ICC(A,k)'].min(), 'to', P['ICC(A,k)'].max())

# ---- split-half and leave-one-rater-out stability of the GABS ranking
raters = {g: sorted(d.rater_id.unique()) for g, d in L.groupby('group')}
methods = sorted(L.method.unique()); mi = {m: i for i, m in enumerate(methods)}
grp_of = {m: sorted(L[L.method == m].group.unique()) for m in methods}
cell = {(g, m, c): d for (g, m, c), d in L.groupby(['group', 'method', 'criterion'])}
sc = {}
for (g, m, c), d in cell.items(): sc[(g, m, c)] = dict(zip(d.rater_id, d.score))
def gabs(keep):
    X = np.zeros(20); Y = np.zeros(20)
    for m in methods:
        xs = []; ys = []
        for g in grp_of[m]:
            ks = set(keep[g])
            vx = [v for c in CR[:5] for r, v in sc[(g, m, c)].items() if r in ks]
            vy = [v for c in CR[5:] for r, v in sc[(g, m, c)].items() if r in ks]
            xs.append(np.mean(vx)); ys.append(np.mean(vy))
        X[mi[m]] = np.mean(xs); Y[mi[m]] = np.mean(ys)
    return 2 * X * Y / (X + Y)
full = gabs(raters)
rng = np.random.default_rng(SEED); rho = []
for _ in range(1000):
    h1 = {}; h2 = {}
    for g, rs in raters.items():
        p = list(rng.permutation(rs)); k = len(p) // 2; h1[g] = p[:k]; h2[g] = p[k:]
    rho.append(spearmanr(gabs(h1), gabs(h2))[0])
print('\nSplit-half (1,000 random splits within group): mean rho %.3f, median %.3f, 5th percentile %.3f' % (np.mean(rho), np.median(rho), np.percentile(rho, 5)))
loo = []
for g, rs in raters.items():
    for r in rs:
        keep = {h: [x for x in v if not (h == g and x == r)] for h, v in raters.items()}
        loo.append(spearmanr(full, gabs(keep))[0])
print('Leave-one-rater-out: minimum rho %.3f (n = %d runs), mean %.3f' % (min(loo), len(loo), np.mean(loo)))
