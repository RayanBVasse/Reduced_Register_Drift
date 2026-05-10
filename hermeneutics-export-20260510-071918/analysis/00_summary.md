# Governance-effort analysis — summary

- Source export: `hermeneutics-export-20260510-071918`
- Generated: 2026-05-10T08:04:29.481452+00:00
- Books analysed: **10** (G1=4, G2=4, G3=2)
- Books excluded: Urban Monasticism, The Fourth Culture
- Total proposals: **46** (CB=22, SB=11, BK=13)
- Status mix: applied=26, rejected=20

## ⚠ Representation divergence

The following applied packets carry a lever type that writes to `book_representation.data`, but the live representation does NOT reflect the lever_to value.  Causes: a force-apply via service-role SQL that skipped `apply_book_representation_patch()`, or a dual-write RPC failure at apply time.  Reconcile by replaying the patch (call `apply_book_representation_patch` on each packet) or by re-running the apply via the UI.

| Book | Lever | Kind | Expected | Actual list |
|---|---|---|---|---|
| The Confessions of St. Augustine | hard_boundary | missing | Do not offer modern business, personal development, or self-help applications unless explicitly requested. Always present Sun Tzu's original military-strategic doctrine first. | Avoid over-interpreting beyond the text without clear justification, Avoid sounding therapeutic, diagnostic, or like modern self-help, Avoid adding claims the book does not actually make, Avoid recasting Augustine’s Christian theology as generic spirituality or secular introspection, Avoid turning specific theological claims into universal life lessons by default, Avoid flattening prayer, confession, sin, grace, and conversion into wellness language |
| The Confessions of St. Augustine | hard_boundary | missing | Always present Sun Tzu's original military-strategic context first. The principle 'supreme excellence is subduing the enemy without fighting' (Chapter III) refers to military victory through superior strategy, not personal or business success. | Avoid over-interpreting beyond the text without clear justification, Avoid sounding therapeutic, diagnostic, or like modern self-help, Avoid adding claims the book does not actually make, Avoid recasting Augustine’s Christian theology as generic spirituality or secular introspection, Avoid turning specific theological claims into universal life lessons by default, Avoid flattening prayer, confession, sin, grace, and conversion into wellness language |

## Files in this folder

- `00_summary.md` — this file
- `01_q1_genre_3a_effort.{md,csv}` — Q1: counts and per-book averages
- `02_q3_acceptance_rejection.{md,csv}` — Q3: status × category × genre
- `03_q4_proposal_clusters.{md,csv}` — Q4: per-book inter-proposal timing
- `04_q5_lever_by_genre.{md,csv}` — Q5: lever × cluster matrix

## Methodology notes

- Proposals are filtered to category ∈ {CB, SB, BK}; rows with
  any other category (none observed in this run) are dropped.
- Acceptance rate denominator = applied + rejected.
- Cluster threshold for Q4 = 60 minutes (tunable).
- Genre map: `tools/genre_map.json` (single source of truth;
  edit there to refine the cluster mapping).
- Representation divergence check (above) only applies to
  `author_guidance` (BK) and `hard_boundary` (SB) lever types —
  these are the only two that write to `book_representation.data`.
  Other lever types are read directly from `governance_packets`
  by the runtime, so divergence is structurally impossible.