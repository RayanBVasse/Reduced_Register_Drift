#!/usr/bin/env python3
"""
TASK 1 — Biber convergence check.

Scores all 450 study responses on Biber's lexicogrammatical features, so we can
show that the bespoke 43-marker drift lexicon agrees with the established
instrument. This pre-empts the obvious NLP-reviewer objection ("why not Biber?").

RUN THIS ON YOUR OWN MACHINE (Claude's sandbox can't download the spaCy model).

    pip install pybiber polars spacy
    python -m spacy download en_core_web_sm
    python biber_extract.py

Edit GFI_DIR below if your path differs. Output: biber_features.csv  -> send to Claude.
"""
from pathlib import Path
import json, sys

# ---- EDIT THIS if needed -----------------------------------------------------
GFI_DIR = Path("")   # <-- set me
OUT_CSV = Path("biber_features.csv")
# ------------------------------------------------------------------------------

COND_DIRS = {                       # folder name -> file prefix
    "A1": ("CondA1_Gemini_2.5Flash",        "condA"),
    "A2": ("CondA2_Ungoverned_GPT4omini",   "CondA2"),
    "B":  ("CondB_Governed_GPT4omini",      "CondB"),
    # If you run Task 2, uncomment to include the ablation:
    # "A3": ("CondA3_ScholarlyPrompt_GPT4omini", "CondA3"),
}

def collect():
    rows = []
    registry = json.loads((GFI_DIR / "book_registry.json").read_text(encoding="utf-8"))["books"]
    for cond, (folder, prefix) in COND_DIRS.items():
        root = GFI_DIR / folder
        if not root.exists():
            print(f"  [skip] {root} not found"); continue
        for abbrev in sorted(registry):
            for i in range(1, 16):
                qid = f"Q{i:02d}"
                p = root / f"{abbrev}_responses" / f"{prefix}_{qid}_{abbrev}.json"
                if not p.exists():
                    print(f"  [warn] missing {p.name}"); continue
                reply = str(json.loads(p.read_text(encoding="utf-8")).get("reply") or "")
                if not reply.strip(): continue
                rows.append({"doc_id": f"{cond}__{abbrev}__{qid}", "text": reply})
    return rows

def main():
    if not GFI_DIR.exists():
        sys.exit(f"ERROR: set GFI_DIR — '{GFI_DIR}' does not exist")
    rows = collect()
    print(f"collected {len(rows)} responses (expect 450, or 600 with A3)")
    if not rows: sys.exit("nothing to score")

    import polars as pl, spacy
    from pybiber import spacy_parse, biber

    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    corp = pl.DataFrame(rows)
    print("parsing with spaCy (a few minutes)...")
    toks = spacy_parse(corp, nlp)
    print("extracting Biber features (normalised per 1,000 tokens)...")
    feats = biber(toks, normalize=True)

    # split doc_id back into condition / book / question
    feats = feats.with_columns([
        pl.col("doc_id").str.split("__").list.get(0).alias("condition"),
        pl.col("doc_id").str.split("__").list.get(1).alias("abbrev"),
        pl.col("doc_id").str.split("__").list.get(2).alias("qid"),
    ])
    feats.write_csv(OUT_CSV)
    print(f"\n[done] wrote {OUT_CSV}  ({feats.height} rows x {feats.width} cols)")
    print("Send biber_features.csv back to Claude for the convergence analysis.")

if __name__ == "__main__":
    main()
