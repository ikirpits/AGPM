"""Check the headline AGPM results from the public aggregate file, without rater-level data.
Usage: python agpm_verify_aggregate.py [agpm_method_results.csv]
Recomputes from the per-method X (agility) and Y (governance) scores: the mean scores and gap,
the exact Wilcoxon signed-rank test, the Spearman correlation, GABS, the quadrant counts
and the KIBO-exclusion sensitivity. Scores in the file are rounded to three decimals,
so the last digit of some statistics can differ from the manuscript, which uses unrounded scores.
The rater-level ratings are not part of the public package (see README)."""
import sys, pandas as pd
from scipy.stats import wilcoxon, spearmanr
d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "agpm_method_results.csv")
def summary(t, label):
    gap = (t.Y_governance - t.X_agility)
    w = wilcoxon(t.Y_governance, t.X_agility, method="exact")
    rho, p = spearmanr(t.X_agility, t.Y_governance)
    gabs = 2 * t.X_agility * t.Y_governance / (t.X_agility + t.Y_governance)
    q = (t.assign(q=[("Integrated Leaders" if x >= 3 and y >= 3 else "Agile-Dominant" if x >= 3 else "Governance-Dominant" if y >= 3 else "Developing")
                     for x, y in zip(t.X_agility, t.Y_governance)]).q.value_counts().to_dict())
    print(f"{label}: n={len(t)} X={t.X_agility.mean():.4f} Y={t.Y_governance.mean():.4f} gap={gap.mean():.4f} "
          f"Wilcoxon W={w.statistic:.0f} exact p={w.pvalue:.5f} lower on governance={int((gap<0).sum())}/{len(t)} "
          f"Spearman={rho:.3f} (p={p:.4f}) max|GABS diff|={abs(gabs-t.GABS).max():.3f}")
    print("  quadrants:", q)
summary(d, "All methods")
summary(d[d.method != "KIBO"], "Excluding KIBO")
