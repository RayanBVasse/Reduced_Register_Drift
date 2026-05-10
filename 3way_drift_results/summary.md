# Three-way drift reduction analysis — 10-book corpus

## Conditions

| Code | Setup | Purpose |
|---|---|---|
| **A1** | Google Gemini 2.5 Flash, ungoverned, fresh chat session per book, system prompt names the book/author | H2H paper Cond_A replication across 10 books |
| **A2** | OpenAI gpt-4o-mini-2024-07-18, ungoverned, fresh chat session per book, system prompt names the book/author | Matched-model ungoverned baseline (model held constant with Cond_B) |
| **B**  | OpenAI gpt-4o-mini via Living Literature platform, full Canon-Pack governance, 15 Qs per book through the platform chat endpoint | Governed companion responses |

All three conditions used the same 15-question protocol (H2H Appendix B) and the same Tier 1 lexicon for drift detection (H2H Appendix A — 43 markers across D1-D4).

## Headline pairwise results — Tier 1 total drift, paired Wilcoxon

| Comparison | Hypothesis | n | Mean ungoverned | Mean governed/other | Diff (per 1k tok) | W | p | r | Sig |
|---|---|---|---|---|---|---|---|---|---|
| A1 vs B | A1 > B | 150 | 4.676 | 4.952 | -0.275 | 3892.0 | 0.71268 | 0.000 | ns |
| A2 vs B | A2 > B | 150 | 8.921 | 4.952 | +3.969 | 7453.0 | 0.00000 | 0.496 | *** |
| A1 vs A2 | two-sided | 150 | 4.676 | 8.921 | -4.245 | 1419.0 | 0.00000 | 0.499 | *** |

Significance codes: \* p<0.05, \*\* p<0.01, \*\*\* p<0.001, (trend) p<0.10, ns p≥0.10.

## Per-category results — D1 / D2 / D3 / D4

| Comparison | Category | n | Mean ungov. | Mean gov./other | Diff | W | p | r | Sig |
|---|---|---|---|---|---|---|---|---|---|
| A1 vs B | D1 (Therapeutic / self-help) | 150 | 1.195 | 0.667 | +0.527 | 1124.0 | 0.00151 | 0.242 | ** |
| A1 vs B | D2 (Productivity / applicatio) | 150 | 1.863 | 2.503 | -0.641 | 2026.0 | 0.94146 | 0.000 | ns |
| A1 vs B | D3 (Doctrinal / intellectual ) | 150 | 1.455 | 1.126 | +0.329 | 1540.0 | 0.06665 | 0.123 | (trend) |
| A1 vs B | D4 (Chatty-assistant / audien) | 150 | 0.164 | 0.655 | -0.491 | 66.0 | 0.99844 | 0.000 | ns |
| A2 vs B | D1 (Therapeutic / self-help) | 150 | 1.511 | 0.667 | +0.844 | 1110.0 | 0.00024 | 0.285 | *** |
| A2 vs B | D2 (Productivity / applicatio) | 150 | 3.974 | 2.503 | +1.471 | 4601.0 | 0.00021 | 0.288 | *** |
| A2 vs B | D3 (Doctrinal / intellectual ) | 150 | 2.039 | 1.126 | +0.913 | 2513.0 | 0.00001 | 0.350 | *** |
| A2 vs B | D4 (Chatty-assistant / audien) | 150 | 1.396 | 0.655 | +0.742 | 1257.0 | 0.00249 | 0.229 | ** |
| A1 vs A2 | D1 (Therapeutic / self-help) | 150 | 1.195 | 1.511 | -0.316 | 1148.0 | 0.10292 | 0.133 | ns |
| A1 vs A2 | D2 (Productivity / applicatio) | 150 | 1.863 | 3.974 | -2.112 | 1446.0 | 0.00000 | 0.488 | *** |
| A1 vs A2 | D3 (Doctrinal / intellectual ) | 150 | 1.455 | 2.039 | -0.584 | 1527.5 | 0.00522 | 0.228 | ** |
| A1 vs A2 | D4 (Chatty-assistant / audien) | 150 | 0.164 | 1.396 | -1.233 | 34.0 | 0.00000 | 0.499 | *** |

## By genre cluster — Tier 1 total mean per 1k tokens

| Cluster | A1 | A2 | B | A1 − B | A2 − B |
|---|---|---|---|---|---|
| G1 | 5.787 | 11.049 | 6.635 | -0.848 | +4.414 |
| G2 | 4.153 | 8.232 | 4.557 | -0.404 | +3.675 |
| G3 | 3.501 | 6.042 | 2.375 | +1.126 | +3.667 |

## By book — Tier 1 total mean per 1k tokens

| Book | Cluster | A1 | A2 | B | A1 − B | A2 − B |
|---|---|---|---|---|---|---|
| Autobiography of Benjamin Franklin (aobf) | G2 | 4.849 | 9.621 | 8.031 | -3.182 | +1.590 |
| Art of War (aow) | G3 | 4.162 | 6.454 | 2.858 | +1.304 | +3.596 |
| The Confessions of St. Augustine (coa) | G1 | 5.048 | 12.253 | 7.199 | -2.151 | +5.054 |
| Autobiography of John Stuart Mill (jsm) | G1 | 7.306 | 10.548 | 6.4 | +0.906 | +4.148 |
| Narrative of the Life of Frederick Douglass (lofd) | G2 | 5.914 | 11.581 | 4.522 | +1.392 | +7.059 |
| Meditations (med) | G1 | 5.75 | 14.405 | 9.616 | -3.866 | +4.789 |
| Nathan the Wise (nw) | G3 | 2.839 | 5.63 | 1.893 | +0.946 | +3.737 |
| The Souls of Black Folk (sbf) | G2 | 3.022 | 5.568 | 3.156 | -0.134 | +2.412 |
| The Varieties of Religious Experience (vre) | G1 | 5.045 | 6.99 | 3.323 | +1.722 | +3.667 |
| Walden, and On the Duty of Civil Disobedience (wdocd) | G2 | 2.828 | 6.158 | 2.517 | +0.311 | +3.641 |

## Methodology notes

- **Tier 1 lexicon only.** 43 markers across four register categories (D1 therapeutic / D2 productivity / D3 doctrinal / D4 chatty), all derived from prior literature (H2H Appendix A). Tier 2 markers and any governance-log-derived lexicon are not used.
- **No GFI / TRS composite.** This analysis reports drift counts and pairwise differences only. Target Register Score and any composite Governance Fidelity Index from the H2H paper are not computed for the 10-book corpus.
- **Whitespace tokenisation.** Same as H2H paper for cross-paper comparability.
- **Paired Wilcoxon signed-rank.** One-sided alternative for A1>B and A2>B (governance hypothesis). Two-sided for A1 vs A2 (no directional hypothesis on the model effect).
- **Effect size r = Z / sqrt(N).** Standard non-parametric effect size for paired Wilcoxon.
- **Temperature confound.** Cond_A1 and Cond_A2 ran at temperature 0.0; Cond_B uses the platform's default 0.4 (server-side). The matched-model comparison A2-vs-B retains a small temperature confound. The H2H original Cond_B also used temperature 0.4, so this matches the published methodology.
- **Model snapshot pinning.** Cond_A1 used `gemini-2.5-flash` (alias). Cond_A2 used `gpt-4o-mini-2024-07-18` (pinned snapshot). Cond_B used the same `gpt-4o-mini-2024-07-18` snapshot via the Living Literature platform's chat endpoint.

## Files in this folder

- `summary.md` — this file
- `per_response.csv` — one row per (book × qid × condition)
- `per_pair.csv` — paired drift differences for the three comparisons
- `statistics.txt` — full Wilcoxon results
- `by_book.csv` — per-book mean drift by condition
- `by_cluster.csv` — per-cluster mean drift by condition
- `charts/overall_by_category.png` — all categories × all conditions
- `charts/per_cluster_by_category.png` — same, split by genre cluster