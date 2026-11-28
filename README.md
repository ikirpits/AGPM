# AGPM data and code package

Supporting material for "The agility-governance gap in software development methods: A multi-rater comparative assessment" (Journal of Systems and Software).

## Files

| File | Content |
|---|---|
| agpm_method_results.csv | Per-method results: X (agility), Y (governance), GABS, rank, bootstrap limits and quadrant for the 20 methods |
| agpm_verify_aggregate.py | Recomputes the headline results (mean scores, gap, exact Wilcoxon test, Spearman correlation, quadrant counts, KIBO-exclusion sensitivity) from agpm_method_results.csv, without rater-level data |
| agpm_reproduce.py | Reproduces X, Y, GABS, quadrants, ranks, the Wilcoxon test and the X-Y Spearman correlation from the rater-level workbook (restricted, see Data access) |
| agpm_verify.py | Independent Python bootstrap (5,000 resamples) that cross-checks the GABS, X and Y intervals and rank limits produced by Code.gs, and writes agpm_quadrant_probabilities.csv |
| agpm_reliability.py | Ordinal alpha, ICC(A,1), ICC(A,k), rater-pair agreement, split-half and leave-one-rater-out stability, from the anonymized workbook (reproduces Supplementary Table S1) |
| Code.gs | Google Apps Script used in the rating workbook: bootstrap, split-half agreement, quadrant stability, sensitivity and bias tabs (seed 2026, 5,000 resamples) |
| agpm_weight_sensitivity.py | Random-weight robustness analysis (10,000 Dirichlet draws, seed 2026) read from the anonymized workbook |
| agpm_caps_sensitivity.py | Optional-element cap scenarios (Table 10), computed from the ratings and instruments/AGPM_caps_classification.csv; writes agpm_caps_scenarios.csv |
| agpm_robustness.py | Median aggregation, exclusion of G1 and G4, and alternative quadrant thresholds (2.75, 2.5, 3.25, 3.5) with bootstrap stability; writes agpm_robustness_scenarios.csv and agpm_threshold_stability.csv |
| agpm_kibo_exclusion.py | Sensitivity analysis excluding KIBO (the authors' own method) from the comparative set, with the exact Wilcoxon test, the X-Y correlation, quadrant counts and ranking agreement; writes agpm_kibo_exclusion.csv |
| agpm_kibo_exclusion.csv | Output of agpm_kibo_exclusion.py |
| AGPM_reports_sought_full_text.csv | The 145 reports sought for full-text retrieval, with title, first author, year, DOI and the source database where it could be traced (17 reports could not be traced and are marked not traced) |
| agpm_caps_scenarios.csv | Output of agpm_caps_sensitivity.py |
| AGPM_academic_background_summary.csv | Aggregate frequencies of self-reported academic background by group (Table 5). Not in the participant tab, to limit disclosure risk |
| Supplementary_Table_S1_criterion_level.csv | Criterion-level agreement statistics (Supplementary Table S1 of the manuscript) |
| AGPM_Table2_research_design.xlsx | Editable version of Table 2 (research design) |
| AGPM_Fig2_positioning_matrix.xlsx, AGPM_Fig3_GABS.xlsx, AGPM_Fig4_heatmap.xlsx | Native Excel versions of the positioning figure, the GABS ranking figure and the criterion heatmap, with the criterion means and formulas behind them (rater-level ratings removed) |
| instruments/ | Text of the four questionnaire forms (Groups A and B, sessions 1 and 2: consent, instructions, scales, item structure), the 200 evidence cards with sources (AGPM_evidence_cards.csv) and the author classification of the 80 governance cells as prescribed, optional or tailorable (AGPM_caps_classification.csv, with the basis and the card sources). Extracted from the Jotforms. No responses or emails |
| Agility_criteria_cards.pptx, Governance_criteria_cards.pptx | The anchored five-point rating scales of the ten criteria shown to raters. The 200 method-specific evidence cards are in instruments/AGPM_evidence_cards.csv |

License: scripts under MIT (LICENSE), data and documentation under CC BY 4.0 (DATA_LICENSE.md).

## Data access

The questionnaire consent promised that findings would be presented in summary form. For this reason the rater-level ratings (AGPM_dataset_anonymized.xlsx, including participant roles and experience) are not published in this repository. This package contains the code, the instruments and evidence cards, and all aggregate results. The rater-level workbook is available from the authors on reasonable request, subject to the consent terms and institutional approval.

Without the workbook, run `python agpm_verify_aggregate.py` to recompute the headline results from agpm_method_results.csv. Scores in that file are rounded to three decimals, so the last digit of a statistic can differ from the manuscript.

## Run order

The seven scripts below need the restricted workbook AGPM_dataset_anonymized.xlsx, which is not in this repository.

```
pip install -r requirements.txt
python agpm_reproduce.py AGPM_dataset_anonymized.xlsx
python agpm_verify.py AGPM_dataset_anonymized.xlsx 2026
python agpm_weight_sensitivity.py AGPM_dataset_anonymized.xlsx
python agpm_reliability.py AGPM_dataset_anonymized.xlsx
python agpm_caps_sensitivity.py AGPM_dataset_anonymized.xlsx
python agpm_robustness.py AGPM_dataset_anonymized.xlsx
python agpm_kibo_exclusion.py AGPM_dataset_anonymized.xlsx
```

All scripts were run in a clean environment with the library versions pinned in requirements.txt (pandas 3.0.5, numpy 2.5.3, scipy 1.18.1, openpyxl 3.1.5).

Expected primary results: mean X 3.4109, mean Y 2.6649, mean gap -0.7459 (convention: gap = Y - X, governance minus agility), Wilcoxon exact p = 0.00486 (W = 32), normal approximation p = 0.0064, Spearman rho = -0.0556 (p = 0.8158). SAFe ranks first (GABS 3.898), DevOps second, KIBO third. FDD (2.7777) ranks 10 and Kanban (2.7775) ranks 11, using unrounded GABS.

## Notes

- Bootstrap intervals in the Results tab come from Code.gs (JavaScript random generator, seed 2026). agpm_verify.py uses a different generator, so the limits differ slightly. With seed 2026 the largest absolute differences between the two implementations are 0.012 (lower) and 0.012 (upper) for X, 0.013 and 0.012 for Y, and 0.012 and 0.010 for GABS, and the lower percentile rank differs by one position for 2 methods (upper: none). The rank limits are the 2.5th and 97.5th percentiles of the bootstrap ranks.
- Rater identifiers are random. Emails, comments and free text are not included. Roles with fewer than three raters are shown as Other in the restricted workbook.
- The Apps Script reads a private tab (Form responses) that contains emails and is not part of this package. The restricted workbook contains the resulting anonymized ratings.
- Scores are used as given. No missing scores were imputed. Where a rater submitted more than once for the same group and session, the latest submission was used.
- The figure workbooks recalculate X, Y and GABS from the criterion means they contain. Bootstrap limits in them are inputs copied from Code.gs. The last column of the Fig. 2 workbook is the share of the 5,000 Code.gs resamples in which a method stays in its quadrant (whole percentages, as in tab 4 of the rating workbook). agpm_verify.py reproduces these shares with a different random generator, so they can differ by about one percentage point (for example DevOps 99.3% against 100% rounded).
- agpm_reliability.py uses seed 2026 for the split-half splits. Its mean split-half rho (0.967) and fifth percentile (0.931) differ by 0.001 from the Code.gs values (0.966 and 0.932) because the generators differ. It also reports that the top three methods are unchanged in all 88 leave-one-rater-out runs.
- The rating scales, consent text and evidence cards shown to raters are in instruments/ and in the two criteria-card pptx files. The stored form responses contain emails and are not part of this package.

## Reproducibility coverage

Literature review: the search expressions and result counts are in Appendix A of the manuscript. A record-level screening log was not retained, so none is provided. AGPM_reports_sought_full_text.csv lists the reports sought for full-text retrieval. It makes no statement about eligibility, which is reported as counts in the manuscript. Source databases were traced by matching titles against the database exports of 27 November 2026. Three pairs of rows (column same_paper_as_no) are two files of the same paper, and the counts in the manuscript are reported as recorded.

Reproduced from the restricted workbook with the scripts in this package (the headline results can also be checked from the public aggregate file): X, Y, GABS, ranks, quadrants, Wilcoxon and Spearman tests, panel-level and criterion-level alpha and ICC, pairwise agreement, bootstrap intervals and quadrant probabilities, split-half and leave-one-rater-out stability, random and extreme criterion weights, and the optional-element cap scenarios, median aggregation, the exclusion of G1 and G4, the alternative quadrant thresholds, and the exclusion of KIBO from the comparative set.
Still requiring the original rating workbook (Code.gs reads a private tab with emails): the exploratory governance-expertise comparison, which is not reproducible from the aggregate files because the participant attributes needed to identify the specialist subgroup are withheld to protect confidentiality.
The threshold stability counts of agpm_robustness.py match the manuscript (18, 18, 16 and 16 methods at 90 percent or more at 3.0, 2.75, 2.5 and 3.5). At 3.25 the script finds 15 where Code.gs gives 16, because PRINCE2 Agile lies on the 90 percent line (89.8 to 90.0 percent depending on the random generator).

## Provenance

- Ratings were collected with four online forms (Jotform: Groups A and B, sessions 1 and 2) and exported to a Google Sheet. The authors cleaned the data, applied the sample rules in the manuscript (Section 3.4, Step 6) and removed emails and free text to create the anonymized workbook (restricted).
- The original analysis was run in Google Apps Script (Code.gs). The Python scripts in this package recompute the reported results from the anonymized workbook (restricted), and the authors ran them and compared the output with the manuscript.
- Generative AI tools (Claude) were used to help transfer the exports into the analysis workbook and to prepare scripts, figure files and this documentation, as declared in the manuscript. The authors ran and checked all outputs.
