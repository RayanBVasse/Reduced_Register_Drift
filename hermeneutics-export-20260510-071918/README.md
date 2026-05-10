# Hermeneutics paper — evidence export

Generated: **2026-05-10T07:19:25.892161+00:00**

## Counts
- Projects (books): **13**
- Companion-Behavior (CB) proposals: **26**
- Scope & Boundaries (SB) proposals: **13**
- Book Knowledge (BK) proposals: **20**
- A/B preview pairs: **24**

## Directory structure

- `a-llm-default-bias/`
  - `all-cb-packets.md` — voice / tone corrections (the paper's core evidence)
  - `sb-scope-corrections.md` — scope / grounding corrections
  - `bk-book-knowledge-corrections.md` — factual-content corrections
- `b-complete-cp-examples/<book-slug>/`
  - `00-project-metadata.md`
  - `01-step1-agent1-output.md` — chapter map + concepts + claims from manuscript
  - `02-step2-author-review.md` — author's reviewed artifacts / QC state
  - `03-step3-companion-preview.md` — author's Step-3 lever choices
  - `04-acr-room-setup.md` — companion display name, welcome, caps
  - `05-governance-history.md` — every 3A proposal with full transcript
  - `raw.json` — complete project + edits + packets in JSON
- `c-governance-impact/`
  - `ab-preview-pairs.md` — literal before/after response pairs

## Suggested reading order for the paper

1. Start with `a-llm-default-bias/all-cb-packets.md` — scan a handful of 
   entries to see the recurring pattern in the author's pushback (tone, 
   directness, commercial-register complaints).
2. Pick 1–2 books from `b-complete-cp-examples/` and walk the full chain 
   to show the paper's reader what the CP-lite protocol actually looks 
   like end-to-end — from raw manuscript to tuned live companion.
3. Pull the most striking A/B pair from `c-governance-impact/` as an 
   illustrative figure or appendix.

## Privacy note

This export contains owner emails + full author–3A transcripts. 
Add the output directory to `.gitignore` or move it out of the 
repo before committing anything.
