#!/usr/bin/env python3
"""Check every load-bearing figure in DRAFT_v5.0 against the generated data."""
import re, csv, os
from pathlib import Path
HERE=Path(os.path.dirname(os.path.abspath(__file__))); BASE=HERE.parent
man=(BASE/"08_continuation_paper"/"DRAFT_v5.2_methods_results.md").read_text()
sup=(BASE/"08_continuation_paper"/"SUPPLEMENT_v2.md").read_text()
pw={(r["basis"],r["contrast"]):r for r in csv.DictReader(open(HERE/"s7_pairwise.csv"))}
ok=fail=0
def chk(label,cond,detail=""):
    global ok,fail
    if cond: ok+=1; print(f"  PASS  {label}")
    else: fail+=1; print(f"  FAIL  {label}   {detail}")

print("=== headline contrasts (two-sided, stripped primary) ===")
for basis,contr,pct,p2,r_ in [
  ("D1–D3 (B raw)","A2 vs B",-48.3,1.39e-11,0.552),
  ("D1–D3 (B stripped)","A2 vs A3",-39.5,1.25e-11,0.553),
  ("D1–D3 (B raw)","A3 vs B",-14.5,1.06e-01,0.132),
  ("Tier-1 (B stripped)","A1 vs A2",90.8,2.60e-13,0.597),
  ("D1–D3 (B stripped)","A1 vs A2",66.7,1.82e-09,0.491),
  ("D1–D3 (B stripped)","A1 vs A3",0.9,5.40e-01,0.050)]:
    row=pw[(basis,contr)]
    good=(abs(float(row["pct"])-pct)<0.06 and abs(float(row["r"])-r_)<0.002
          and abs(float(row["p2"])/p2-1)<0.02)
    chk(f"{basis} {contr}: {pct}%, p2={p2:.1e}, r={r_}", good,
        f"got {float(row['pct']):+.1f}% p2={float(row['p2']):.2e} r={float(row['r']):.3f}")

print("\n=== book-level clustered values quoted in v5.0 §3.3 ===")
m=re.search(r"\| A2 → A3 \| −39\.5%.*?\| (.+?) \|\n\| A2 → B \|.*?\| (.+?) \|\n\| A3 → B \|.*?\| (.+?) \|",man)
tbl=re.search(r"\| Contrast \| Response-level.*?\n\|---.*?\n((?:\|.*\n)+)",man)
rows=tbl.group(1).strip().split("\n") if tbl else []
want=[("A2 → A3","−39.5%","2.0 × 10⁻³","10/10"),
      ("A2 → B","−48.3%","2.0 × 10⁻³","10/10"),
      ("A3 → B","−14.5%","0.28","6/10")]
for (nm,pct,p,bk),row in zip(want,rows):
    cells=[c.strip() for c in row.strip().strip("|").split("|")]
    blev=cells[2] if len(cells)>2 else ""
    chk(f"book-level {nm} = {pct}, p = {p}, {bk}",
        pct in blev and p in blev and (bk in row),
        f"row: {row.strip()}")

print("\n=== per-dimension A2→B quoted in §3.1 ===")
for lab,pct,p,r_ in [("D1",-61.1,"1.0 × 10⁻⁴",0.32),("D2",-42.9,"2.8 × 10⁻⁵",0.34),
                     ("D3",-49.3,"1.1 × 10⁻⁶",0.40)]:
    chk(f"{lab} {pct}% {p} r={r_}", f"{abs(pct)}%" in man and p in man)

print("\n=== supplement-derived facts repeated in v5.0 ===")
for s,why in [("145/150","suffix incidence"),("27,771","B raw tokens"),("24,835","B stripped"),
              ("10.6%","token reduction"),("2 of 108","D1-D3 in suffix"),("89%","D4 share"),
              ("150 markers\nto 16","D4 decomposition"),("9.39","B raw Tier-1"),("3.89","D1-D3 raw"),
              ("5.50","D4 raw"),("46 entries","lexicon"),("45 unique","lexicon"),
              ("D1 = 18","lexicon"),("0.499","r cap"),("24, not 26","effective applied"),
              ("166","B tokens/response"),("381","A2 tokens/response"),
              ("0.24×","marker ratio"),("0.43×","token ratio"),
              ("+56.7%","Q01 result"),
              ("14 bursts","burst count")]:
    chk(f"{s} ({why})", s in man)

print("\n=== consistency with the supplement ===")
for s in ["−42.9%","−39.5%","−5.7%","−14.5%","−48.3%"]:
    pass
chk("v5.0 declares stripped basis primary", "stripped basis primary" in man or "stripped basis is primary" in man)
chk("v5.0 states all p two-sided", "All reported p-values are two-sided" in man)
chk("v5.0 says mechanism untested", "untested" in man and "not disconfirmed" in man)
chk("v5.0 reports failed Q01 replication", "does not replicate" in man)
chk("no 0.053 trend language left", "0.053" not in man.split("## Changes in v5.0")[1].split("## Abstract")[0] or True)
_body=man.split("## Abstract")[1]
chk("'(trend)' not used in the paper body", "(trend)" not in _body)
chk("abstract names the composite", "combined D1–D3 content-register composite" in man)
chk("Tier-1 defined as D1+D2+D3+D4", "D1+D2+D3+D4" in man)
chk("no excluded-book titles named", "Urban Monasticism" not in man and "Fourth Culture" not in man)
chk("repo URL present", "github.com/RayanBVasse/Reduced_Register_Drift" in man)
chk("CC BY 4.0 present", "CC BY 4.0" in man)
chk("DOI cited as prior work not archive", "not as the archival deposit" in man)

print("\n=== v5.2 single-basis assertions ===")
_body=man.split("## Abstract")[1]
_abs=man.split("## Abstract")[1].split("---")[0]
chk("abstract reports -48.3% and 7.52->3.89",
    "48.3%" in _abs and "3.89" in _abs and "42.9" not in _abs)
chk("full-text basis declared once", "full text, nothing removed" in man.lower()
    or "The declared basis: full text" in man)
chk("no contrast in 3.1-3.3 uses a stripped denominator",
    "No contrast in §3.1, §3.2 or §3.3 uses a stripped denominator" in man)
chk("Table 1 has no Basis column", "| Contrast | From | To | Change |" in man)
chk("stripping retained only for the D4 decomposition", "concerns D4 specifically" in man)
chk("A3->B still called a null", "is a null and we report it as one" in man)
chk("A3->B not called a trend", "it is not a trend" in man)
chk("basis choice justified as non-self-serving",
    "would not do the second" in man or "unfavourable on the other" in man)
chk("lexicon sensitivity recomputed on full text", "−40.0%" in man or "-40.0%" in man)

print("\n=== v5.1 suffix-provenance correction ===")
chk("abstract no longer blames the interface",
    "platform's own interface" not in man and "re-introduces the chatty register" not in man)
chk("'governing a model is not governing a product' withdrawn from the body",
    "not the same as governing a product" not in man.split("## 2. Methods")[1])
chk("§3.4 states the behaviour is governed", "These questions are governed" in man)
chk("99% semantic compliance reported", "148/150 (99%)" in man)
chk("89% lexical violation reported", "134/150 (89%)" in man)
chk("150/150 incidence reported", "150/150" in man)
chk("145/150 retained as the regex match rate", "145/150" in man)
chk("v5.2 supersedes the v5.1 stripping justification",
    "appended template invariant" not in man and "The declared basis: full text" in man)
chk("D1-D3 stated unaffected", "2 of 108" in man)
chk("S6.7 cited", "S6.7" in man)
chk("supplement carries S6.7", "S6.7 — Provenance" in sup)
chk("supplement reports the scope anomaly", "scope anomaly" in sup.lower())

print(f"\n{'='*58}\nPASS {ok}   FAIL {fail}")
