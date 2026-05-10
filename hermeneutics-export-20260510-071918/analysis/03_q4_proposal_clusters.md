# Q4 — Proposal clustering over time

A *burst* is defined as a sequence of ≥2 proposals on the same book
each separated from its predecessor by ≤ 60 minutes.
Bursts measure persistent-drift patterns where the author iterates
rapidly to converge on a fix.

## Per-book summary

| Book | Cluster | n props | Span (h) | Median Δ (min) | Min Δ (min) | Max Δ (min) | Bursts |
|---|---|---|---|---|---|---|---|
| Meditations | G1 | 10 | 120.47 | 58.8 | 1.9 | 3796.5 | 3 |
| The Confessions of St. Augustine | G1 | 4 | 5.44 | 9.0 | 2.7 | 314.7 | 2 |
| The Varieties of Religious Experience | G1 | 4 | 1.54 | 21.7 | 20.8 | 49.6 | 1 |
| Autobiography of John Stuart Mill | G1 | 1 | 0.0 |  |  |  | 0 |
| Autobiography of Benjamin Franklin | G2 | 7 | 50.81 | 8.5 | 4.1 | 2468.1 | 3 |
| The Souls of Black Folk | G2 | 5 | 295.04 | 41.5 | 27.7 | 17594.2 | 1 |
| Narrative of the Life of Frederick Douglass | G2 | 3 | 279.77 | 11608.0 | 5178.2 | 11608.0 | 0 |
| Walden, and On The Duty Of Civil Disobedience | G2 | 2 | 0.03 | 1.7 | 1.7 | 1.7 | 1 |
| Art of War | G3 | 8 | 72.92 | 25.8 | 3.9 | 3225.0 | 2 |
| Nathan the Wise | G3 | 2 | 0.35 | 20.8 | 20.8 | 20.8 | 1 |

## Cluster aggregates

| Cluster | Books with ≥2 props | Total inter-prop intervals | Median Δ (min) | Total bursts |
|---|---|---|---|---|
| G1 | 4 | 15 | 43.8 | 6 |
| G2 | 4 | 13 | 39.1 | 5 |
| G3 | 2 | 8 | 25.8 | 3 |

## Methodology notes

- Proposals without a parseable `created_at` are excluded.
- A book with only one proposal contributes 0 intervals and
  0 bursts (no clustering possible).
- The 60-minute threshold is a tunable parameter; see
  `CLUSTER_WINDOW_MIN` in `analyse_governance.py`.