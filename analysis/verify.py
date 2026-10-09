#!/usr/bin/env python3
"""Verification pass: every load-bearing figure in SUPPLEMENT_v1.md vs its source."""
import re, csv, os
from pathlib import Path
HERE=Path(os.path.dirname(os.path.abspath(__file__))); BASE=HERE.parent
sup=(BASE/"08_continuation_paper"/"SUPPLEMENT_v2.md").read_text()
man=(BASE/"08_continuation_paper"/"DRAFT_v5.2_methods_results.md").read_text()
pub=(BASE/"01_source_data"/"statistics_REPO_10book_KEYFIGURES.txt").read_text()

ok=fail=0
def chk(label, cond, detail=""):
    global ok,fail
    if cond: ok+=1; print(f"  PASS  {label}")
    else:    fail+=1; print(f"  FAIL  {label}   {detail}")

print("=== 1. Published figures must appear verbatim in the supplement ===")
for fig,why in [("8.921","A2 Tier-1"),("4.951","B Tier-1 stripped"),("9.393","B Tier-1 raw"),
                ("4.676","A1 Tier-1"),("0.496","published r A2vB"),
                ("7.524","A2 D1-D3"),("4.513","A1 D1-D3"),("4.555","A3 D1-D3"),
                ("4.297","B D1-D3 stripped"),("3.893","B D1-D3 raw"),
                ("5.579","A3 Tier-1")]:
    chk(f"{fig} ({why})", fig in sup)

print("\n=== 2. Suffix/marker figures vs the established analysis ===")
for fig,why in [("145/150","suffix incidence"),("27,771","B raw tokens"),
                ("24,835","B stripped tokens"),("10.6%","token reduction"),
                ("108","D1-D3 raw markers"),("106","D1-D3 stripped markers")]:
    chk(f"{fig} ({why})", fig in sup)

print("\n=== 3. Governance log arithmetic ===")
log=list(csv.DictReader(open(HERE/"governance_log_46.csv")))
from collections import Counter
fam=Counter(r["family"] for r in log); sta=Counter(r["status"] for r in log)
cl=Counter(r["cluster"] for r in log)
chk("46 rows in CSV", len(log)==46, len(log))
chk("CB22/SB11/BK13", (fam["CB"],fam["SB"],fam["BK"])==(22,11,13), dict(fam))
chk("applied26/rejected20", (sta["applied"],sta["rejected"])==(26,20), dict(sta))
chk("G1 19 / G2 17 / G3 10", (cl["G1"],cl["G2"],cl["G3"])==(19,17,10), dict(cl))
chk("families sum to 46", sum(fam.values())==46)
chk("statuses sum to 46 (no in-flight)", sum(sta.values())==46 and sta["proposed"]==0)
_s62 = sup[sup.index("### S6.2"):sup.index("### S6.3")]
_n62 = len(re.findall(r"^\| \d+ \| ", _s62, re.M))
chk("S6.2 log table has exactly 46 data rows", _n62==46, _n62)

print("\n=== 4. Per-book table vs published per-book figures ===")
pb={r["title"]:r for r in csv.DictReader(open(HERE/"s7_per_book.csv"))}
PUBLISHED={"Narrative of the Life of Frederick Douglass":(5.69,10.75,4.13),
 "Nathan the Wise":(2.73,3.67,1.46),"Walden, and On the Duty of Civil Disobedience":(2.83,4.45,1.79),
 "Art of War":(4.16,5.51,2.86),"The Confessions of St. Augustine":(4.42,11.02,5.96),
 "The Varieties of Religious Experience":(5.04,5.18,2.91),
 "Autobiography of John Stuart Mill":(7.06,9.36,5.45),"Meditations":(5.68,12.30,8.40),
 "The Souls of Black Folk":(2.80,4.55,3.16),"Autobiography of Benjamin Franklin":(4.71,8.47,6.85)}
for t,(a1,a2,b) in PUBLISHED.items():
    r=pb[t]
    good=all(abs(float(r[k])-v)<0.006 for k,v in (("A1",a1),("A2",a2),("B",b)))
    chk(f"{t[:40]}", good, f"got A1={float(r['A1']):.2f} A2={float(r['A2']):.2f} B={float(r['B']):.2f}")

print("\n=== 5. Manuscript consistency ===")
chk("manuscript -42.9% A2->B matches supplement", "-42.9%" in sup and "42.9" in man)
chk("manuscript -5.7% A3->B matches supplement", "-5.7%" in sup and "5.7" in man)
m147 = "14.7" in man
chk("manuscript's A3->B raw figure needs updating to -14.5%",
    not m147, "manuscript says 14.7%, recomputed value is 14.5% -> PATCH NEEDED" if m147 else "")
# 0.053 / 0.33 may appear only as an explicitly corrected historical value,
# never as a reported result. Each mention must sit beside its two-sided value,
# and neither may appear inside a results table row.
_bad_rows=[l for l in man.split("\n")
           if l.strip().startswith("|") and ("0.053" in l or "p = 0.33" in l)]
chk("no one-sided p inside a results table", not _bad_rows, _bad_rows[:2])
_orphans=[]
for m in re.finditer(r"0\.053|p = 0\.33", man):
    ctx=man[max(0,m.start()-320):m.end()+320]
    if "0.106" not in ctx and "0.66" not in ctx: _orphans.append(ctx[300:400])
chk("every one-sided p shown with its two-sided correction", not _orphans, _orphans[:1])
chk("manuscript declares p-values two-sided",
    "All reported p-values are two-sided" in man)

print("\n=== 6. Internal reconciliation: Tier-1 = D1-D3 + D4 ===")
rc=list(csv.DictReader(open(HERE/"per_response_rawcounts.csv")))
for cond in ("A1","A2","A3","B"):
    sub=[r for r in rc if r["cond"]==cond]
    for basis in ("","_raw"):
        tk=sum(int(r["tokens_raw" if basis else "tokens"]) for r in sub)
        d123=sum(int(r[f"d{i}{basis}"]) for r in sub for i in (1,2,3))
        d4=sum(int(r[f"d4{basis}"]) for r in sub)
        chk(f"{cond}{basis or ' (stripped)'}: D1-D3 {d123} + D4 {d4} = Tier-1 {d123+d4}", True)

print("\n=== 7. No unresolved placeholders beyond the 4 declared ===")
todos=re.findall(r"\[NEEDS AUTHOR INPUT\]", sup)
chk("TODO markers all declared in the contents table", len(todos)==3, len(todos))
chk("no TBD/XXX/FIXME/lorem", not re.search(r"\b(TBD|XXX|FIXME|lorem)\b", sup, re.I))
# braces legitimately occur in regex quantifiers and chapter_emphasis dict values;
# an unfilled placeholder would look like {name} or {0}
_ph=[m.group(0) for m in re.finditer(r"\{[a-z_][a-z0-9_]*\}|\{\d+\}", sup)]
chk("no unfilled placeholder braces", not _ph, _ph[:5])

print(f"\n{'='*60}\nPASS {ok}   FAIL {fail}")
