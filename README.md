# AGPM data and code package

Supporting material for "The agility-governance gap in software development methods: A multi-rater comparative assessment" (Journal of Systems and Software).

## Files

| File | Content |
|---|---|
| AGPM_dataset_anonymized.xlsx | Anonymized ratings of 20 methods by 88 independent practitioners (tabs: README, Participants, Ratings_long, Ratings_wide, Methods, Results) |
| agpm_reproduce.py | Reproduces X, Y, GABS, quadrants, ranks, the Wilcoxon test and the X-Y Spearman correlation from Ratings_long |
| agpm_verify.py | Independent Python bootstrap (5,000 resamples) that cross-checks the intervals produced by Code.gs |
| Code.gs | Google Apps Script used in the rating workbook: bootstrap, split-half agreement, quadrant stability, sensitivity and bias tabs (seed 2026, 5,000 resamples) |
| agpm_weight_sensitivity.py | Random-weight robustness analysis (10,000 Dirichlet draws, seed 2026) from criterion-level sums |
| Supplementary_Table_S1_criterion_level.csv | Criterion-level agreement statistics (Supplementary Table S1 of the manuscript) |
| AGPM_Fig5_positioning_matrix.xlsx, AGPM_Fig6_GABS.xlsx | Native Excel versions of the positioning figure and the GABS ranking figure, with the ratings and formulas behind them |
| Agility_criteria_cards.pptx, Governance_criteria_cards.pptx | Evidence cards and anchored scales shown to raters |

## Run order

```
pip install pandas numpy scipy openpyxl
python agpm_reproduce.py AGPM_dataset_anonymized.xlsx
python agpm_verify.py AGPM_dataset_anonymized.xlsx 2026
python agpm_weight_sensitivity.py
```

Expected primary results: mean X 3.4109, mean Y 2.6649, mean gap -0.7459, Wilcoxon exact p = 0.00486 (W = 32), normal approximation p = 0.0064, Spearman rho = -0.0556 (p = 0.8158). SAFe ranks first (GABS 3.898), DevOps second, KIBO third. FDD (2.7777) ranks 10 and Kanban (2.7775) ranks 11, using unrounded GABS.

## Notes

- Bootstrap intervals in the Results tab come from Code.gs (JavaScript random generator, seed 2026). agpm_verify.py uses a different generator, so limits agree within a few thousandths and a best or worst rank can differ by one position.
- Rater identifiers are random. Emails, comments and free text are not included. Roles with fewer than three raters are shown as Other.
- The Apps Script reads a private tab (Form responses) that contains emails and is not part of this package. The public dataset contains the resulting anonymized ratings.
- Scores are used as given. No missing scores were imputed. Where a rater submitted more than once for the same group and session, the latest submission was used.
- The two figure workbooks recalculate X, Y and GABS from the Ratings tab. Bootstrap limits in them are inputs copied from Code.gs. The probability column P(Integrated Leaders) in the Fig. 5 workbook comes from an earlier Python bootstrap and is only used for reference.
- The rating scales shown to raters are in the two criteria-card pptx files. The stored form responses contain emails and are not part of this package.
