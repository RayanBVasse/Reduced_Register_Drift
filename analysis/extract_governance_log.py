
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT as EXPORT_DIR, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""
S6 — extract the full corpus-filtered 3A governance log (46 proposals).

Reads the three lever-family markdown files from the platform export and emits
a tidy CSV + a markdown table for the supplement.

Scope: the raw export covers every book governed on the platform. The study
corpus is defined by book_registry.json; any book absent from the registry is
outside the study and is excluded. No titles are hard-coded here -- the
registry is the single source of truth for corpus membership.

Output:  governance_log_46.csv , governance_log_46.md
"""
import re, csv, os, json

EXPORT = str(EXPORT_DIR)
OUT = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "CB": "all-cb-packets.md",
    "BK": "bk-book-knowledge-corrections.md",
    "SB": "sb-scope-corrections.md",
}
# Corpus membership and genre cluster both come from the registry.
_REG = json.load(open(DATA / "book_registry.json"))["books"]

def _norm(t):
    return " ".join(t.lower().replace("\u2019", "'").split())

# registry title -> cluster, matched case/whitespace-insensitively
_REG_BY_TITLE = {_norm(b["title"]): b["cluster"] for b in _REG.values()}

# a few export titles differ from the registry in capitalisation only
CLUSTER = {
    "Meditations": "G1",
    "The Confessions of St. Augustine": "G1",
    "The Varieties of Religious Experience": "G1",
    "Autobiography of John Stuart Mill": "G1",
    "Autobiography of Benjamin Franklin": "G2",
    "Narrative of the Life of Frederick Douglass": "G2",
    "Walden, and On The Duty Of Civil Disobedience": "G2",
    "The Souls of Black Folk": "G2",
    "Art of War": "G3",
    "Nathan the Wise": "G3",
}

PROP = re.compile(
    r"## #(\d+)\.\s*`(\S+?)`\s*/\s*`(\S+?)`\s*—\s*status\s*`(\w+)`(.*?)(?=\n## #|\Z)", re.S)

def field(block, label):
    m = re.search(r"\*\*" + label + r":\*\*\s*`?(.*?)`?\s*\n", block)
    return (m.group(1).strip() if m else "").strip("`")

rows = []
for fam, fn in FILES.items():
    txt = open(os.path.join(EXPORT, fn), encoding="utf-8").read()
    parts = re.split(r"\n### Book: \*(.+?)\*\n", txt)
    for i in range(1, len(parts), 2):
        book, body = parts[i].strip(), parts[i + 1]
        for m in PROP.finditer(body):
            _, cat, lever, status, rest = m.groups()
            # first USER line of the transcript = the curator's complaint
            cm = re.search(r"\*\*USER:\*\*\s*\n\s*\n>\s*(.*?)\n", rest)
            in_corpus = _norm(book) in _REG_BY_TITLE
            rows.append({
                "family": fam,
                "book": book,
                "cluster": _REG_BY_TITLE.get(_norm(book), CLUSTER.get(book, "—")),
                "in_corpus": in_corpus,
                "category": cat,
                "lever": lever,
                "status": status,
                "proposal_id": field(rest, "Proposal ID"),
                "created": field(rest, "Created"),
                "from_value": field(rest, "From value"),
                "to_value": field(rest, "To value"),
                "summary": field(rest, "3A summary"),
                "curator_complaint": (cm.group(1).strip() if cm else ""),
                "has_ab_preview": "### A/B preview comparison" in rest,
            })

rows.sort(key=lambda r: (r["created"] or ""))
corpus = [r for r in rows if r["in_corpus"]]

# ---- integrity check: does to_value mention another corpus book's subject? ----
SENTINEL = {"Art of War": ["sun tzu", "military-strategic", "attack by stratagem"]}
flags = []
for r in corpus:
    for other, keys in SENTINEL.items():
        if r["book"] != other and any(k in r["to_value"].lower() for k in keys):
            flags.append((r, other))

hdr = ["family","book","cluster","category","lever","status","proposal_id","created",
       "from_value","to_value","summary","curator_complaint","has_ab_preview","in_corpus"]
with open(os.path.join(OUT, "governance_log_46.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
    for r in corpus: w.writerow(r)

def trunc(s, n):
    s = (s or "").replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"

with open(os.path.join(OUT, "governance_log_46.md"), "w", encoding="utf-8") as f:
    f.write("# S6.2 — Complete 3A governance log (46 proposals, ten corpus texts)\n\n")
    f.write(f"Raw export: {len(rows)} proposals across {len({r['book'] for r in rows})} books. "
            f"Excluding the two non-corpus books leaves **{len(corpus)}** proposals "
            f"across {len({r['book'] for r in corpus})} texts.\n\n")
    f.write("| # | Book | Cl. | Family | Lever | Status | Created | From → To | Curator's stated problem |\n")
    f.write("|---|---|---|---|---|---|---|---|---|\n")
    for n, r in enumerate(corpus, 1):
        arrow = f"`{trunc(r['from_value'],28) or '—'}` → `{trunc(r['to_value'],60)}`"
        f.write(f"| {n} | {trunc(r['book'],34)} | {r['cluster']} | {r['family']} | "
                f"`{r['lever']}` | {r['status']} | {r['created'][:10]} | {arrow} | "
                f"{trunc(r['curator_complaint'],90)} |\n")

# ---- console report ----
from collections import Counter
print("RAW export      :", len(rows), "proposals,", len({r['book'] for r in rows}), "books")
print("  by family     :", dict(Counter(r['family'] for r in rows)))
print("  by status     :", dict(Counter(r['status'] for r in rows)))
print()
print("CORPUS-FILTERED :", len(corpus), "proposals,", len({r['book'] for r in corpus}), "books")
print("  by family     :", dict(Counter(r['family'] for r in corpus)))
print("  by status     :", dict(Counter(r['status'] for r in corpus)))
print("  by cluster    :", dict(Counter(r['cluster'] for r in corpus)))
print("  A/B previews  :", sum(r['has_ab_preview'] for r in corpus))
print()
print("  applied/decided by family:")
for fam in ("CB","SB","BK"):
    s = [r for r in corpus if r['family']==fam]
    a = sum(r['status']=='applied' for r in s); d = sum(r['status'] in ('applied','rejected') for r in s)
    print(f"    {fam}: n={len(s):2d} ({len(s)/len(corpus)*100:4.1f}% of log)  applied {a}/{d} = {a/d*100:.1f}%")
print("  applied/decided by cluster:")
for cl in ("G1","G2","G3"):
    s = [r for r in corpus if r['cluster']==cl]
    a = sum(r['status']=='applied' for r in s); d = sum(r['status'] in ('applied','rejected') for r in s)
    print(f"    {cl}: n={len(s):2d}  applied {a}/{d} = {a/d*100:.1f}%")
print("  lever frequency:", dict(Counter(r['lever'] for r in corpus).most_common()))
print()
print("INTEGRITY FLAGS :", len(flags))
for r, other in flags:
    print(f"  !! '{r['book']}' {r['family']}/{r['lever']} [{r['status']}] {r['created'][:19]}")
    print(f"     to_value references *{other}*: {trunc(r['to_value'],150)}")
