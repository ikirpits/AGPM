"""Check the headline AGPM results from the public aggregate file, without rater-level data.
Usage: python agpm_verify_aggregate.py [agpm_method_results.csv]
agpm_method_results.csv holds the mean score of every method on the ten criteria (A1 to A5, G1 to G5)
at full precision, together with X, Y, GABS and the bootstrap limits. From the criterion means this
script recomputes X, Y and GABS and checks them against the file, then reports the mean scores and gap,
the exact Wilcoxon signed-rank test, the Spearman correlation, the quadrant counts, the KIBO-exclusion
sensitivity and the exclusion of G1 and G4 (scenario of agpm_robustness.py).
The rater-level ratings are not part of the public package (see README), so reliability, bootstrap,
split-half, leave-one-rater-out and cap analyses cannot be run from this file."""
import sys, numpy as np, pandas as pd
from scipy.stats import wilcoxon, spearmanr
d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "agpm_method_results.csv")
A = [f"A{i}" for i in range(1, 6)]; G = [f"G{i}" for i in range(1, 6)]
def quad(x, y):
    return np.where(x >= 3, np.where(np.round(y, 9) >= 3, "Integrated Leaders", "Agile-First"),
                    np.where(np.round(y, 9) >= 3, "Governance-Heavy", "Baseline"))
def summary(t, label, gcols=G):
    x = t[A].mean(axis=1); y = t[gcols].mean(axis=1); gap = y - x
    gabs = 2 * x * y / (x + y)
    w = wilcoxon(y, x, method="exact"); rho, p = spearmanr(x, y)
    q = pd.Series(quad(x.values, y.values)).value_counts().to_dict()
    print(f"{label}: n={len(t)} X={x.mean():.4f} Y={y.mean():.4f} gap={gap.mean():.4f} Wilcoxon W={w.statistic:.0f} "
          f"exact p={w.pvalue:.5f} lower on governance={int((gap < 0).sum())}/{len(t)} Spearman={rho:.3f} (p={p:.4f})")
    print("  quadrants:", {k: q.get(k, 0) for k in ["Integrated Leaders", "Agile-First", "Governance-Heavy", "Baseline"]})
    return x, y, gabs
x, y, gabs = summary(d, "All methods")
print(f"  largest difference from the file: X {abs(x - d.X_agility).max():.2e}, Y {abs(y - d.Y_governance).max():.2e}, GABS {abs(gabs - d.GABS).max():.2e}")
summary(d[d.method != "KIBO"], "Excluding KIBO")
mx, my = x, d[[c for c in G if c != "G1"]].mean(axis=1)
base = pd.Series(quad(x.values, y.values)); ch = lambda cols: int((pd.Series(quad(x.values, d[cols].mean(axis=1).values)) != base).sum())
print("Quadrant changes when excluding G1:", ch([c for c in G if c != "G1"]), "| G4:", ch([c for c in G if c != "G4"]),
      "| G1 and G4:", ch([c for c in G if c not in ("G1", "G4")]))
