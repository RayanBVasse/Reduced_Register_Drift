#!/usr/bin/env python3
"""
Extended GFI study — three-way drift reduction analysis.

Reads response JSONs from all three conditions across 10 books and
computes Tier 1 register-drift markers per response, normalised per
1,000 tokens. Runs three pairwise paired-Wilcoxon comparisons:

    A1 vs B    full effect      (governance + model)
                                = H2H paper Cond_A vs Cond_B replication
    A2 vs B    matched-model    (pure governance, model held constant)
                                = the H2H paper's stated future-work goal
    A1 vs A2   pure model       (Gemini vs gpt-4o-mini ungoverned)

Methodology (deliberately constrained to validated, reviewer-defensible
choices):
    - Tier 1 lexicon only (43 markers, lit-derived; H2H Appendix A)
    - Frequency per 1,000 tokens (whitespace tokenisation)
    - Paired Wilcoxon signed-rank (one-sided "ungoverned > governed" for
      A1 vs B and A2 vs B; two-sided for A1 vs A2)
    - Effect size r = Z / sqrt(N)
    - No TRS, no GFI composite, no D1-D5 drift labelling — only DRS
      (drift reduction = mean(X) - mean(Y) per 1k tokens) and the four
      D1-D4 categories that the H2H Tier 1 lexicon already specifies

Inputs
------
    book_registry.json
    protocol_15q.json
    Gemini_15_responses/<abbrev>_responses/condA_QNN_<abbrev>.json
    Ungoverned_GPT4omini/<abbrev>_responses/CondA2_QNN_<abbrev>.json
    Governed_GPT4omini/<abbrev>_responses/CondB_QNN_<abbrev>.json

Outputs (3way_drift_results/)
-----------------------------
    summary.md             headline findings + interpretation
    per_response.csv       one row per (book × qid × condition)
    per_pair.csv           one row per (book × qid × pairing) with diff
    statistics.txt         Wilcoxon results for each comparison
    by_book.csv            per-book drift means per condition
    by_cluster.csv         per-cluster (G1/G2/G3) drift means per cond
    charts/
       overall_by_category.png
       per_cluster_by_category.png

Usage:
    pip install scipy matplotlib pandas
    python drift_reduction_3way.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import norm, wilcoxon

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "book_registry.json"
PROTOCOL_PATH = HERE / "protocol_15q.json"

COND_DIRS = {
    "A1": HERE / "Gemini_15_responses",
    "A2": HERE / "Ungoverned_GPT4omini",
    "B":  HERE / "Governed_GPT4omini",
}

# How each condition's per-book file is named.
COND_FILE = {
    "A1": "condA_{qid}_{abbrev}.json",
    "A2": "CondA2_{qid}_{abbrev}.json",
    "B":  "CondB_{qid}_{abbrev}.json",
}

OUT_DIR = HERE / "3way_drift_results"


# ---------------------------------------------------------------------------
# Tier 1 lexicon (H2H Appendix A — 43 markers across D1–D4)
# Identical to register_drift_counter.py for cross-paper comparability.
# ---------------------------------------------------------------------------

TIER1 = {
    "D1": [
        "what you're feeling", "it's okay to", "be kind to yourself",
        "healing", "resilience", "inner peace", "cope with", "process your",
        "self-care", "on your journey",
        "emotional healing", "emotional wellbeing", "your emotional",
        "vulnerable", "safe space",
        "you can do this", "believe in yourself",
        "it's important to remember",
    ],
    "D2": [
        "mindset", "empower", "transform", "achieve your goals",
        "step-by-step", "actionable", "growth", "inspire", "overcome",
        "it's important to remember",  # shared D1/D2 per H2H Appendix
    ],
    "D3": [
        "a helpful way to think about", "applicable to", "timeless",
        "meaningful journey", "meaningful experience", "meaningful way",
        "journey", "it's worth noting",
    ],
    "D4": [
        "let's explore", "consider this", "i hope this helps",
        "we can discuss", "take a moment to", "reflect on",
        "would you like to", "feel free to ask", "i'm here to help",
        "is there anything else",
    ],
}

CATEGORIES = ("D1", "D2", "D3", "D4")
CATEGORY_LABELS = {
    "D1": "Therapeutic / self-help",
    "D2": "Productivity / application",
    "D3": "Doctrinal / intellectual flattening",
    "D4": "Chatty-assistant / audience-smoothing",
}


# ---------------------------------------------------------------------------
# Platform interface suffix stripping (Cond_B only)
#
# CPLite appends a terminal "interface routing" question to most Vera/Marcus/
# etc. responses to invite continued reading. The H2H paper Section 5.4
# explicitly identified these as platform-interface artefacts that the
# Tier 1 lexicon does not distinguish from mid-response audience-smoothing,
# inflating D4 in Cond_B.
#
# Two observed patterns at the end of replies:
#   "Would you like to explore / delve into / examine ...?"   (most books)
#   "How does <Author/Title> ... in Chapter/Book N ...?"      (sbf, others)
#
# We strip these from Cond_B replies before counting, while ALSO retaining
# the raw counts so both perspectives are reported.
# ---------------------------------------------------------------------------

SUFFIX_PATTERNS = [
    # "Would you like to ..." family
    r"^\s*would you like (?:to|me to)\b.*\?\s*$",
    r"^\s*do you (?:want|wish) (?:to|me to)\b.*\?\s*$",
    r"^\s*are you interested in\b.*\?\s*$",
    r"^\s*shall we (?:explore|consider|examine|delve)\b.*\?\s*$",
    r"^\s*want me to\b.*\?\s*$",
    # Companion follow-up question with explicit chapter/book reference
    r"^\s*how does\b.{1,400}\b(?:chapter|book|verse|lecture|episode|part|section)\b[^?]*\?\s*$",
    r"^\s*how might\b.{1,400}\b(?:chapter|book|verse|lecture|episode|part|section)\b[^?]*\?\s*$",
]
SUFFIX_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in SUFFIX_PATTERNS]


def strip_platform_suffix(text: str) -> tuple[str, str | None]:
    """
    If `text` ends with a recognised platform-interface suffix, return
    (stripped_text, suffix_extracted). Otherwise return (text, None).
    """
    if not text:
        return text, None
    s = text.rstrip()

    # Try last paragraph first (after final \n\n)
    parts = s.rsplit("\n\n", 1)
    if len(parts) == 2:
        body, last = parts
        last_stripped = last.strip()
        for pat in SUFFIX_RE:
            if pat.match(last_stripped):
                return body.rstrip(), last_stripped

    # Fallback: try last sentence (no \n\n separator, suffix is inline)
    boundaries = [m.end() for m in re.finditer(
        r"[.!?][\s'\"\)\]]*\s+(?=[A-Z])", s
    )]
    if boundaries:
        last_boundary = boundaries[-1]
        body = s[:last_boundary].rstrip()
        last = s[last_boundary:].strip()
        for pat in SUFFIX_RE:
            if pat.match(last):
                return body, last

    return text, None


# ---------------------------------------------------------------------------
# Marker counting (logic identical to H2H register_drift_counter.py)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> int:
    return len(text.split())


def count_markers(text: str) -> dict[str, int]:
    """Return per-category drift counts for one response."""
    text_lower = text.lower()
    counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    for cat, markers in TIER1.items():
        for marker in markers:
            ml = marker.lower()
            if " " in ml:
                counts[cat] += text_lower.count(ml)
            else:
                counts[cat] += len(re.findall(r"\b" + re.escape(ml) + r"\b",
                                              text_lower))
    return counts


def per_1k(count: int, tokens: int) -> float:
    return (count / tokens * 1000) if tokens else 0.0


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["books"]


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))["questions"]


def response_path(cond: str, abbrev: str, qid: str) -> Path:
    return COND_DIRS[cond] / f"{abbrev}_responses" / COND_FILE[cond].format(
        qid=qid, abbrev=abbrev
    )


def reply_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("reply") or "")
    except Exception as exc:
        print(f"  [warn] failed to parse {path}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Build per-response dataframe
# ---------------------------------------------------------------------------

def build_per_response_df(registry: dict, protocol: dict) -> pd.DataFrame:
    """
    Build the per-response dataframe.  For Cond_B we count markers on
    BOTH the raw reply (suffix included) and the stripped reply
    (platform-interface suffix removed).  D4_raw and total_raw retain
    the full-reply numbers for transparency; the primary D4/total
    columns reflect the stripped reply (= content-drift estimate).
    For Cond_A1 / Cond_A2 the raw and stripped versions are identical
    by construction (no stripping applied).
    """
    rows = []
    n_b_total = 0
    n_b_stripped = 0
    suffix_examples: dict[str, list[str]] = defaultdict(list)

    for abbrev in sorted(registry.keys()):
        meta = registry[abbrev]
        for i in range(1, 16):
            qid = f"Q{i:02d}"
            qrec = protocol[qid]
            for cond in ("A1", "A2", "B"):
                path = response_path(cond, abbrev, qid)
                text_raw = reply_text(path)
                if text_raw is None:
                    print(f"  [warn] missing {cond} {abbrev} {qid}", file=sys.stderr)
                    continue

                if cond == "B":
                    n_b_total += 1
                    text_for_count, suffix = strip_platform_suffix(text_raw)
                    if suffix is not None:
                        n_b_stripped += 1
                        if len(suffix_examples[abbrev]) < 1:
                            suffix_examples[abbrev].append(suffix[:140])
                    suffix_was_stripped = (suffix is not None)
                else:
                    text_for_count = text_raw
                    suffix_was_stripped = False

                # Counts on the (possibly stripped) text used for analysis
                counts = count_markers(text_for_count)
                tokens = tokenize(text_for_count)

                # Raw counts (unchanged for A1/A2; full-reply counts for B)
                counts_raw = count_markers(text_raw)
                tokens_raw = tokenize(text_raw)

                row = {
                    "abbrev":         abbrev,
                    "title":          meta["title"],
                    "cluster":        meta["cluster"],
                    "qid":            qid,
                    "block":          qrec["block"],
                    "primary_drift":  qrec["primary_drift"],
                    "condition":      cond,
                    "suffix_was_stripped": suffix_was_stripped,
                    # Stripped (primary, used in pairwise analysis)
                    "tokens":         tokens,
                    "d1":             counts["D1"],
                    "d2":             counts["D2"],
                    "d3":             counts["D3"],
                    "d4":             counts["D4"],
                    "total":          sum(counts.values()),
                    "d1_per1k":       per_1k(counts["D1"], tokens),
                    "d2_per1k":       per_1k(counts["D2"], tokens),
                    "d3_per1k":       per_1k(counts["D3"], tokens),
                    "d4_per1k":       per_1k(counts["D4"], tokens),
                    "total_per1k":    per_1k(sum(counts.values()), tokens),
                    # Raw (full-reply) counts for transparency / contrast
                    "tokens_raw":     tokens_raw,
                    "d4_raw":         counts_raw["D4"],
                    "total_raw":      sum(counts_raw.values()),
                    "d4_per1k_raw":   per_1k(counts_raw["D4"], tokens_raw),
                    "total_per1k_raw": per_1k(sum(counts_raw.values()), tokens_raw),
                }
                rows.append(row)

    # Diagnostic summary
    if n_b_total:
        print(f"\n  Cond_B suffix stripping: {n_b_stripped}/{n_b_total} replies "
              f"had a recognised platform suffix removed "
              f"({n_b_stripped/n_b_total*100:.0f}%).")
        for ab in sorted(suffix_examples):
            ex = suffix_examples[ab][0]
            print(f"    {ab}: example suffix = '{ex}{'...' if len(ex) >= 140 else ''}'")

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Pairwise comparisons
# ---------------------------------------------------------------------------

PAIRS = [
    ("A1", "B",  "greater",  "Cond_A1 (Gemini ungoverned) vs Cond_B (governed)"),
    ("A2", "B",  "greater",  "Cond_A2 (gpt-4o-mini ungoverned) vs Cond_B (governed)  [matched-model]"),
    ("A1", "A2", "two-sided","Cond_A1 (Gemini) vs Cond_A2 (gpt-4o-mini ungoverned)  [model effect]"),
]


def pivot_for_pair(df: pd.DataFrame, x: str, y: str, col: str) -> pd.DataFrame:
    """Pivot to one row per (book × qid) with X and Y columns of `col`."""
    sub = df[df.condition.isin([x, y])]
    pv = sub.pivot_table(
        index=["abbrev", "title", "cluster", "qid", "block", "primary_drift"],
        columns="condition",
        values=col,
    ).dropna()
    if x not in pv.columns or y not in pv.columns:
        return pd.DataFrame()
    pv = pv.reset_index().rename(columns={x: "x_value", y: "y_value"})
    pv["diff_x_minus_y"] = pv["x_value"] - pv["y_value"]
    return pv


def wilcoxon_one_pair(x_vals, y_vals, alternative: str) -> dict:
    diff = x_vals - y_vals
    n = len(diff)
    if n == 0:
        return {"n": 0, "note": "no paired data"}
    if all(d == 0 for d in diff):
        return {"n": n, "note": "all differences zero",
                "mean_x": float(x_vals.mean()),
                "mean_y": float(y_vals.mean()),
                "mean_diff": 0.0}
    try:
        stat, p = wilcoxon(diff, alternative=alternative)
    except Exception as exc:
        return {"n": n, "note": f"wilcoxon failed: {exc}"}
    # Effect size r = Z / sqrt(N) — convert one/two-sided p to z safely.
    p_for_z = p if alternative == "two-sided" else min(p * 2, 1.0)
    p_for_z = max(min(p_for_z, 0.999999), 1e-9)
    z = norm.ppf(1 - p_for_z / 2)
    r = z / (n ** 0.5)
    return {
        "n": n,
        "W": float(stat),
        "p": round(float(p), 5),
        "r": round(float(r), 3),
        "mean_x": round(float(x_vals.mean()), 4),
        "mean_y": round(float(y_vals.mean()), 4),
        "mean_diff": round(float((x_vals - y_vals).mean()), 4),
    }


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def md_table(headers: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(str(h) for h in headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    return out


def signif(p: float | None) -> str:
    if p is None:
        return "—"
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "(trend)"
    return "ns"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "charts").mkdir(parents=True, exist_ok=True)

    registry = load_registry()
    protocol = load_protocol()

    print("[1] Building per-response dataframe...")
    df = build_per_response_df(registry, protocol)
    print(f"    {len(df)} rows ({len(df) // 3} expected = 10 books × 15 Qs × 3 conds)")
    df.to_csv(OUT_DIR / "per_response.csv", index=False)
    print(f"    saved: {OUT_DIR / 'per_response.csv'}")

    # ----------------------------------------------------------------------
    # Pairwise comparisons
    # ----------------------------------------------------------------------
    print("\n[2] Pairwise paired Wilcoxon tests...")
    stats_lines: list[str] = []
    stats_lines.append("=" * 72)
    stats_lines.append("DRIFT REDUCTION — pairwise paired Wilcoxon results")
    stats_lines.append("=" * 72)
    stats_lines.append("")
    stats_lines.append("Tier 1 lexicon (43 markers, H2H Appendix A).")
    stats_lines.append("Score = drift markers per 1,000 tokens, paired by (book, qid).")
    stats_lines.append("Effect size r = Z / sqrt(N).")
    stats_lines.append("")

    pair_results: list[dict] = []
    all_pair_rows: list[dict] = []  # for per_pair.csv

    for x, y, alt, label in PAIRS:
        stats_lines.append("-" * 72)
        stats_lines.append(f"COMPARISON: {label}")
        stats_lines.append(f"  Hypothesis: {x} {'>' if alt == 'greater' else '!='} {y}")
        stats_lines.append("-" * 72)

        # Total Tier 1
        pv = pivot_for_pair(df, x, y, "total_per1k")
        stat = wilcoxon_one_pair(pv["x_value"].values, pv["y_value"].values, alt)
        stat["pair"] = f"{x}_vs_{y}"
        stat["category"] = "Tier 1 total"
        stat["label"] = label
        pair_results.append(stat)
        if stat.get("note"):
            stats_lines.append(f"  Tier 1 total: {stat['note']}")
        else:
            stats_lines.append(
                f"  Tier 1 total — n={stat['n']:3d}  "
                f"mean({x})={stat['mean_x']:.3f}  "
                f"mean({y})={stat['mean_y']:.3f}  "
                f"diff={stat['mean_diff']:+.3f}"
            )
            stats_lines.append(
                f"                W={stat['W']:.1f}  "
                f"p={stat['p']:.5f} {signif(stat['p']):>10s}  "
                f"r={stat['r']:.3f}"
            )

        # Per-category
        for cat in CATEGORIES:
            pv_cat = pivot_for_pair(df, x, y, f"{cat.lower()}_per1k")
            cat_stat = wilcoxon_one_pair(
                pv_cat["x_value"].values, pv_cat["y_value"].values, alt
            )
            cat_stat["pair"] = f"{x}_vs_{y}"
            cat_stat["category"] = cat
            cat_stat["label"] = label
            pair_results.append(cat_stat)
            if cat_stat.get("note"):
                stats_lines.append(
                    f"  {cat} ({CATEGORY_LABELS[cat]}): {cat_stat['note']}"
                )
            else:
                stats_lines.append(
                    f"  {cat} ({CATEGORY_LABELS[cat][:30]:<30s})  "
                    f"mean({x})={cat_stat['mean_x']:.3f}  "
                    f"mean({y})={cat_stat['mean_y']:.3f}  "
                    f"diff={cat_stat['mean_diff']:+.3f}  "
                    f"W={cat_stat['W']:.1f}  "
                    f"p={cat_stat['p']:.5f} {signif(cat_stat['p']):>10s}  "
                    f"r={cat_stat['r']:.3f}"
                )

        # Per-pair CSV rows
        for _, row in pv.iterrows():
            all_pair_rows.append({
                "pair":        f"{x}_vs_{y}",
                "abbrev":      row["abbrev"],
                "title":       row["title"],
                "cluster":     row["cluster"],
                "qid":         row["qid"],
                "block":       row["block"],
                "primary_drift": row["primary_drift"],
                "x_value":     round(row["x_value"], 4),
                "y_value":     round(row["y_value"], 4),
                "diff":        round(row["diff_x_minus_y"], 4),
            })

        stats_lines.append("")

    # ------------------------------------------------------------------
    # D4 raw vs stripped — shows the platform-interface contribution
    # ------------------------------------------------------------------
    stats_lines.append("=" * 72)
    stats_lines.append("D4 RAW vs STRIPPED — platform interface contribution to D4")
    stats_lines.append("=" * 72)
    stats_lines.append("")
    stats_lines.append("D4 markers per 1,000 tokens, three conditions, two views:")
    stats_lines.append("  raw      = full reply incl. terminal interface suffix (Cond_B only)")
    stats_lines.append("  stripped = reply with platform suffix removed before counting")
    stats_lines.append("Cond_A1 and Cond_A2 are not stripped (no platform suffix exists).")
    stats_lines.append("")

    for cond in ("A1", "A2", "B"):
        sub = df[df.condition == cond]
        d4_stripped_mean = sub["d4_per1k"].mean()
        d4_raw_mean = sub["d4_per1k_raw"].mean()
        n_stripped = int(sub["suffix_was_stripped"].sum())
        stats_lines.append(f"  {cond}:  D4 raw = {d4_raw_mean:.3f}  "
                           f"D4 stripped = {d4_stripped_mean:.3f}  "
                           f"Δ = {d4_raw_mean - d4_stripped_mean:+.3f}  "
                           f"(suffixes stripped: {n_stripped}/{len(sub)})")
    stats_lines.append("")

    # Equivalent contrast for Tier 1 totals
    stats_lines.append("Tier 1 total per 1,000 tokens, three conditions:")
    for cond in ("A1", "A2", "B"):
        sub = df[df.condition == cond]
        tot_stripped = sub["total_per1k"].mean()
        tot_raw = sub["total_per1k_raw"].mean()
        stats_lines.append(f"  {cond}:  total raw = {tot_raw:.3f}  "
                           f"total stripped = {tot_stripped:.3f}  "
                           f"Δ = {tot_raw - tot_stripped:+.3f}")
    stats_lines.append("")

    (OUT_DIR / "statistics.txt").write_text(
        "\n".join(stats_lines), encoding="utf-8"
    )
    print(f"    saved: {OUT_DIR / 'statistics.txt'}")

    pair_df = pd.DataFrame(all_pair_rows)
    pair_df.to_csv(OUT_DIR / "per_pair.csv", index=False)
    print(f"    saved: {OUT_DIR / 'per_pair.csv'}")

    # ----------------------------------------------------------------------
    # Per-book and per-cluster aggregates
    # ----------------------------------------------------------------------
    print("\n[3] Per-book and per-cluster aggregates...")

    by_book = (df.groupby(["abbrev", "title", "cluster", "condition"])
                 [["d1_per1k", "d2_per1k", "d3_per1k", "d4_per1k", "total_per1k"]]
                 .mean().round(4).reset_index())
    by_book.to_csv(OUT_DIR / "by_book.csv", index=False)
    print(f"    saved: {OUT_DIR / 'by_book.csv'}")

    by_cluster = (df.groupby(["cluster", "condition"])
                    [["d1_per1k", "d2_per1k", "d3_per1k", "d4_per1k", "total_per1k"]]
                    .mean().round(4).reset_index())
    by_cluster.to_csv(OUT_DIR / "by_cluster.csv", index=False)
    print(f"    saved: {OUT_DIR / 'by_cluster.csv'}")

    # ----------------------------------------------------------------------
    # Charts
    # ----------------------------------------------------------------------
    print("\n[4] Charts...")

    # Overall: 4 categories × 3 conditions
    fig, ax = plt.subplots(figsize=(10, 5))
    cond_order = ["A1", "A2", "B"]
    cond_label = {"A1": "Cond_A1\nGemini ungov.",
                  "A2": "Cond_A2\ngpt-4o-mini ungov.",
                  "B":  "Cond_B\ngpt-4o-mini governed"}
    cond_color = {"A1": "#d9534f", "A2": "#f0ad4e", "B": "#5bc0de"}
    width = 0.25
    x_pos = list(range(len(CATEGORIES)))
    for i, cond in enumerate(cond_order):
        means = [df[df.condition == cond][f"{c.lower()}_per1k"].mean()
                 for c in CATEGORIES]
        offset = (i - 1) * width
        bars = ax.bar([p + offset for p in x_pos], means, width,
                      label=cond_label[cond], color=cond_color[cond], alpha=0.85)
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=7)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{c}\n({CATEGORY_LABELS[c][:20]})" for c in CATEGORIES])
    ax.set_ylabel("Mean drift markers per 1,000 tokens")
    ax.set_title("10-book corpus — drift by category, three conditions")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "charts" / "overall_by_category.png", dpi=150)
    plt.close()
    print(f"    saved: charts/overall_by_category.png")

    # Per-cluster: 3 clusters × 4 categories × 3 conditions
    clusters = sorted(df["cluster"].unique())
    fig, axes = plt.subplots(1, len(clusters), figsize=(5 * len(clusters), 5),
                             sharey=True)
    if len(clusters) == 1:
        axes = [axes]
    for ax, cl in zip(axes, clusters):
        sub = df[df.cluster == cl]
        for i, cond in enumerate(cond_order):
            means = [sub[sub.condition == cond][f"{c.lower()}_per1k"].mean()
                     for c in CATEGORIES]
            offset = (i - 1) * width
            ax.bar([p + offset for p in x_pos], means, width,
                   label=cond_label[cond], color=cond_color[cond], alpha=0.85)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(CATEGORIES)
        ax.set_title(f"Cluster {cl}")
        ax.set_ylabel("Markers per 1k tokens")
    axes[-1].legend(fontsize=7, loc="upper right")
    plt.suptitle("Drift by category × cluster")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "charts" / "per_cluster_by_category.png", dpi=150)
    plt.close()
    print(f"    saved: charts/per_cluster_by_category.png")

    # ----------------------------------------------------------------------
    # Summary markdown
    # ----------------------------------------------------------------------
    print("\n[5] Writing summary.md...")

    lines: list[str] = []
    lines.append("# Three-way drift reduction analysis — 10-book corpus")
    lines.append("")
    lines.append("## Conditions")
    lines.append("")
    lines.append("| Code | Setup | Purpose |")
    lines.append("|---|---|---|")
    lines.append("| **A1** | Google Gemini 2.5 Flash, ungoverned, fresh chat session per book, "
                 "system prompt names the book/author | H2H paper Cond_A replication "
                 "across 10 books |")
    lines.append("| **A2** | OpenAI gpt-4o-mini-2024-07-18, ungoverned, fresh chat session "
                 "per book, system prompt names the book/author | Matched-model "
                 "ungoverned baseline (model held constant with Cond_B) |")
    lines.append("| **B**  | OpenAI gpt-4o-mini via Living Literature platform, "
                 "full Canon-Pack governance, 15 Qs per book through the platform "
                 "chat endpoint | Governed companion responses |")
    lines.append("")
    lines.append("All three conditions used the same 15-question protocol "
                 "(H2H Appendix B) and the same Tier 1 lexicon for drift detection "
                 "(H2H Appendix A — 43 markers across D1-D4).")
    lines.append("")

    # Headline pairwise table
    lines.append("## Headline pairwise results — Tier 1 total drift, paired Wilcoxon")
    lines.append("")
    headers = ["Comparison", "Hypothesis", "n", "Mean ungoverned",
               "Mean governed/other", "Diff (per 1k tok)", "W", "p", "r", "Sig"]
    rows = []
    for s in pair_results:
        if s["category"] != "Tier 1 total":
            continue
        if s.get("note"):
            rows.append([s["label"], "—", s.get("n", 0), "—", "—",
                         "—", "—", "—", "—", s["note"]])
            continue
        pair_short = s["pair"].replace("_vs_", " vs ")
        x, y = s["pair"].split("_vs_")
        hyp = f"{x} > {y}" if pair_short != "A1 vs A2" else "two-sided"
        rows.append([
            pair_short, hyp, s["n"],
            f"{s['mean_x']:.3f}", f"{s['mean_y']:.3f}",
            f"{s['mean_diff']:+.3f}",
            f"{s['W']:.1f}", f"{s['p']:.5f}", f"{s['r']:.3f}",
            signif(s['p']),
        ])
    lines.extend(md_table(headers, rows))
    lines.append("")
    lines.append("Significance codes: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, "
                 "(trend) p<0.10, ns p≥0.10.")
    lines.append("")

    # Per-category table
    lines.append("## Per-category results — D1 / D2 / D3 / D4")
    lines.append("")
    headers = ["Comparison", "Category", "n", "Mean ungov.", "Mean gov./other",
               "Diff", "W", "p", "r", "Sig"]
    rows = []
    for s in pair_results:
        if s["category"] == "Tier 1 total":
            continue
        if s.get("note"):
            rows.append([s["pair"].replace("_vs_", " vs "), s["category"],
                         s.get("n", 0), "—", "—", "—", "—", "—", "—",
                         s["note"]])
            continue
        rows.append([
            s["pair"].replace("_vs_", " vs "),
            f"{s['category']} ({CATEGORY_LABELS[s['category']][:25]})",
            s["n"],
            f"{s['mean_x']:.3f}", f"{s['mean_y']:.3f}",
            f"{s['mean_diff']:+.3f}",
            f"{s['W']:.1f}", f"{s['p']:.5f}", f"{s['r']:.3f}",
            signif(s['p']),
        ])
    lines.extend(md_table(headers, rows))
    lines.append("")

    # Per-cluster table (Tier 1 total, by condition)
    lines.append("## By genre cluster — Tier 1 total mean per 1k tokens")
    lines.append("")
    cl_pivot = (by_cluster.pivot_table(index="cluster", columns="condition",
                                       values="total_per1k").round(3))
    headers = ["Cluster"] + list(cl_pivot.columns) + ["A1 − B", "A2 − B"]
    rows = []
    for cl in cl_pivot.index:
        row = [cl] + [cl_pivot.loc[cl, c] for c in cl_pivot.columns]
        a1_b = cl_pivot.loc[cl, "A1"] - cl_pivot.loc[cl, "B"] if "A1" in cl_pivot.columns and "B" in cl_pivot.columns else None
        a2_b = cl_pivot.loc[cl, "A2"] - cl_pivot.loc[cl, "B"] if "A2" in cl_pivot.columns and "B" in cl_pivot.columns else None
        row.extend([f"{a1_b:+.3f}" if a1_b is not None else "—",
                    f"{a2_b:+.3f}" if a2_b is not None else "—"])
        rows.append(row)
    lines.extend(md_table(headers, rows))
    lines.append("")

    # Per-book table
    lines.append("## By book — Tier 1 total mean per 1k tokens")
    lines.append("")
    bk_pivot = (by_book.pivot_table(index=["abbrev", "title", "cluster"],
                                    columns="condition",
                                    values="total_per1k").round(3))
    headers = ["Book", "Cluster"] + list(bk_pivot.columns) + ["A1 − B", "A2 − B"]
    rows = []
    for (abbrev, title, cluster), row_data in bk_pivot.iterrows():
        row = [f"{title} ({abbrev})", cluster] + [row_data[c] for c in bk_pivot.columns]
        a1_b = row_data.get("A1", None)
        b = row_data.get("B", None)
        a2_b_val = row_data.get("A2", None) - b if row_data.get("A2", None) is not None and b is not None else None
        a1_b_val = a1_b - b if a1_b is not None and b is not None else None
        row.extend([f"{a1_b_val:+.3f}" if a1_b_val is not None else "—",
                    f"{a2_b_val:+.3f}" if a2_b_val is not None else "—"])
        rows.append(row)
    lines.extend(md_table(headers, rows))
    lines.append("")

    # Caveats
    lines.append("## Methodology notes")
    lines.append("")
    lines.append("- **Tier 1 lexicon only.** 43 markers across four register categories "
                 "(D1 therapeutic / D2 productivity / D3 doctrinal / D4 chatty), "
                 "all derived from prior literature (H2H Appendix A). Tier 2 markers "
                 "and any governance-log-derived lexicon are not used.")
    lines.append("- **No GFI / TRS composite.** This analysis reports drift counts "
                 "and pairwise differences only. Target Register Score and any composite "
                 "Governance Fidelity Index from the H2H paper are not computed for the "
                 "10-book corpus.")
    lines.append("- **Whitespace tokenisation.** Same as H2H paper for cross-paper "
                 "comparability.")
    lines.append("- **Paired Wilcoxon signed-rank.** One-sided alternative for A1>B and "
                 "A2>B (governance hypothesis). Two-sided for A1 vs A2 (no directional "
                 "hypothesis on the model effect).")
    lines.append("- **Effect size r = Z / sqrt(N).** Standard non-parametric effect size "
                 "for paired Wilcoxon.")
    lines.append("- **Temperature confound.** Cond_A1 and Cond_A2 ran at temperature 0.0; "
                 "Cond_B uses the platform's default 0.4 (server-side). The matched-model "
                 "comparison A2-vs-B retains a small temperature confound. The H2H "
                 "original Cond_B also used temperature 0.4, so this matches the "
                 "published methodology.")
    lines.append("- **Model snapshot pinning.** Cond_A1 used `gemini-2.5-flash` (alias). "
                 "Cond_A2 used `gpt-4o-mini-2024-07-18` (pinned snapshot). Cond_B used "
                 "the same `gpt-4o-mini-2024-07-18` snapshot via the Living Literature "
                 "platform's chat endpoint.")
    lines.append("")

    lines.append("## Files in this folder")
    lines.append("")
    lines.append("- `summary.md` — this file")
    lines.append("- `per_response.csv` — one row per (book × qid × condition)")
    lines.append("- `per_pair.csv` — paired drift differences for the three comparisons")
    lines.append("- `statistics.txt` — full Wilcoxon results")
    lines.append("- `by_book.csv` — per-book mean drift by condition")
    lines.append("- `by_cluster.csv` — per-cluster mean drift by condition")
    lines.append("- `charts/overall_by_category.png` — all categories × all conditions")
    lines.append("- `charts/per_cluster_by_category.png` — same, split by genre cluster")

    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"    saved: {OUT_DIR / 'summary.md'}")

    # ----------------------------------------------------------------------
    # Console headline
    # ----------------------------------------------------------------------
    print("\n=== Headline ===")
    for s in pair_results:
        if s["category"] != "Tier 1 total":
            continue
        if s.get("note"):
            print(f"  {s['pair']:8s}  Tier 1 total: {s['note']}")
        else:
            print(f"  {s['pair']:8s}  Tier 1 total  "
                  f"mean({s['pair'].split('_vs_')[0]})={s['mean_x']:.3f}  "
                  f"mean({s['pair'].split('_vs_')[1]})={s['mean_y']:.3f}  "
                  f"diff={s['mean_diff']:+.3f}  "
                  f"W={s['W']:.1f}  p={s['p']:.5f} {signif(s['p'])}  "
                  f"r={s['r']:.3f}")
    print(f"\n[done] outputs in: {OUT_DIR}")


if __name__ == "__main__":
    main()
