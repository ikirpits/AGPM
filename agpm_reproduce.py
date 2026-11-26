#!/usr/bin/env python3
"""
AGPM primary results from the anonymized dataset.

Usage
    python agpm_reproduce.py AGPM_dataset_anonymized.xlsx

Needs: pandas, numpy, scipy, openpyxl

Reads the tab Ratings_long and reproduces
  1. criterion means per method and questionnaire group, X (mean of A1 to A5),
     Y (mean of G1 to G5), GABS = 2XY/(X+Y), quadrant (threshold 3.0) and rank.
     For the two methods rated in both groups (Waterfall, Scrum) the two group
     means are averaged. Ranks use the unrounded GABS.
  2. Wilcoxon signed-rank test of Y versus X across the 20 methods (exact and normal
     approximation) and the Spearman correlation between X and Y.
  3. Reliability summaries are in the manuscript (Section 5.1) and Supplementary Table S1.

Prints the results and writes agpm_reproduced_results.csv next to the input file.
The bootstrap intervals are checked by agpm_verify.py (independent Python implementation)
against the Google Apps Script in Code.gs.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, spearmanr, rankdata

THRESHOLD = 3.0
src = Path(sys.argv[1])
L = pd.read_excel(src, "Ratings_long")
L["axis"] = L["criterion"].str[0].map({"A": "X", "G": "Y"})

# mean of all ratings of a method on an axis within a group, then average of the groups
gm = L.groupby(["method", "group", "axis"]).score.mean().unstack("axis")
r = gm.groupby("method").mean()
r["GABS"] = 2 * r.X * r.Y / (r.X + r.Y)
r["rank"] = rankdata(-r.GABS, method="min").astype(int)


def quad(x, y):
    if x >= THRESHOLD:
        return "Integrated Leaders" if y >= THRESHOLD else "Agile-First"
    return "Governance-Heavy" if y >= THRESHOLD else "Baseline"


r["quadrant"] = [quad(x, y) for x, y in zip(r.X, r.Y)]
r = r.sort_values("rank")
print(r.round(4).to_string())

d = r.Y - r.X
print(f"\nMean X {r.X.mean():.4f}  mean Y {r.Y.mean():.4f}  mean gap (Y-X) {d.mean():.4f}")
print("Methods with Y below X:", int((d < 0).sum()), "of", len(d))
w = wilcoxon(r.Y, r.X, method="exact")
print(f"Wilcoxon exact: W = {w.statistic:.0f}, p = {w.pvalue:.5f}")
wn = wilcoxon(r.Y, r.X, method="approx")
print(f"Wilcoxon normal approximation: p = {wn.pvalue:.4f}")
rho, p = spearmanr(r.X, r.Y)
print(f"Spearman X-Y across methods: rho = {rho:.4f}, p = {p:.4f}")
r.round(6).to_csv(src.with_name("agpm_reproduced_results.csv"))
