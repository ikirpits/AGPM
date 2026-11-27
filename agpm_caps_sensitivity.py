#!/usr/bin/env python3
"""Optional-element cap scenarios (manuscript Table 10), from the anonymized ratings and the
author classification in instruments/AGPM_caps_classification.csv (80 governance cells, G2 to G5;
10 cells in 5 methods are optional or tailorable; the classification is author-coded from the evidence
cards and not independently verified).
Usage: python agpm_caps_sensitivity.py AGPM_dataset_anonymized.xlsx [instruments/AGPM_caps_classification.csv]
Each individual governance rating in an optional (tailorable) cell is capped at the scenario value
before aggregation: score = min(score, cap). Ratings of prescribed cells and of A1-A5 and G1 are unchanged.
Reports, per scenario: mean X, mean Y, gap (Y - X), exact Wilcoxon p, Spearman rho of GABS against the
primary GABS, and the methods that change quadrant at threshold 3.0 (and the top three)."""
import sys, numpy as np, pandas as pd
from scipy.stats import wilcoxon, spearmanr
SRC = sys.argv[1] if len(sys.argv) > 1 else 'AGPM_dataset_anonymized.xlsx'
CLS = sys.argv[2] if len(sys.argv) > 2 else 'instruments/AGPM_caps_classification.csv'
L = pd.read_excel(SRC, 'Ratings_long'); C = pd.read_csv(CLS)
cls = {(r.method, r.criterion): r.classification for r in C.itertuples()}
# input validation: exactly one valid class for every rated method x G2..G5 cell
assert not C.duplicated(['method', 'criterion']).any(), 'duplicate method-criterion rows in the classification file'
assert set(C.classification) <= {'prescribed', 'optional', 'tailorable'}, 'invalid class in the classification file'
need = set(zip(L.method, L.criterion)) ; need = {k for k in need if k[1] in ('G2', 'G3', 'G4', 'G5')}
missing = need - set(cls); assert not missing, f'no classification for {sorted(missing)}'
SCEN = [(3, 4), (2, 4), (2, 3), (3, 3), (2, 2)]   # (optional cap, tailorable cap)
def run(co=None, ct=None):
    d = L.copy()
    if co is not None:
        k = [cls.get((m, c), 'prescribed') for m, c in zip(d.method, d.criterion)]  # G1 and A1-A5 are not classified
        cap = pd.Series([co if x == 'optional' else ct if x == 'tailorable' else 99 for x in k], index=d.index)
        d['score'] = np.minimum(d.score, cap)
    d['axis'] = d.criterion.str[0].map({'A': 'X', 'G': 'Y'})
    r = d.groupby(['method', 'group', 'axis']).score.mean().unstack('axis').groupby('method').mean()
    r['GABS'] = 2 * r.X * r.Y / (r.X + r.Y); return r
def quad(r): return (r.X >= 3).map({True: 'A', False: 'B'}) + (r.Y >= 3).map({True: 'G', False: 'g'})
base = run(); qb = quad(base); rows = []
for co, ct in [(None, None)] + SCEN:
    r = run(co, ct); q = quad(r)
    top3 = ', '.join(r.GABS.sort_values(ascending=False).index[:3])
    rows.append(dict(scenario='primary' if co is None else f'optional {co}, tailorable {ct}', meanX=round(r.X.mean(), 4),
        meanY=round(r.Y.mean(), 4), gap=round(r.Y.mean() - r.X.mean(), 4), wilcoxon_exact_p=round(wilcoxon(r.Y, r.X, method='exact').pvalue, 5),
        spearman_vs_primary=round(spearmanr(base.GABS, r.GABS)[0], 3),
        quadrant_changes=int((q != qb).sum()), changed=', '.join(r.index[q != qb]), top3=top3))
o = pd.DataFrame(rows); print(o.to_string(index=False)); o.to_csv('agpm_caps_scenarios.csv', index=False)
