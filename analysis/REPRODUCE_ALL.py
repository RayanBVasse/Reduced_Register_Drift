#!/usr/bin/env python3
"""
REPRODUCE_ALL.py — regenerate every number in the manuscript from the raw
response files and ASSERT it against the value printed in the paper.

Why this exists: intermediate CSVs can be wrong, and an analysis reported in
prose cannot be checked. This script starts from the 600 response JSONs, which
are the only primary artefacts, rebuilds the lexicon counting from scratch, and
fails loudly if any manuscript figure does not reproduce.

Run:  python REPRODUCE_ALL.py
Exit: 0 = every claim in the paper reproduces; 1 = at least one does not.

It depends on NOTHING produced by earlier scripts. Only:
  <GFI>/book_registry.json, protocol_15q.json
  <GFI>/Cond{A1,A2,A3,B}_*/<book>_responses/*.json      (600 files)
  <SUPP>/governance_log_46.csv                          (for the log claims)
"""
import json, csv, os, re, sys, statistics as st
from pathlib import Path
from collections import defaultdict
from scipy.stats import wilcoxon, norm, spearmanr, levene

GFI  = Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
HERE = Path(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- instrument
# Verbatim from the published instrument. 46 entries, 45 unique strings:
# "it's important to remember" is counted under both D1 and D2.
TIER1 = {
 "D1":["what you're feeling","it's okay to","be kind to yourself","healing","resilience",
  "inner peace","cope with","process your","self-care","on your journey","emotional healing",
  "emotional wellbeing","your emotional","vulnerable","safe space","you can do this",
  "believe in yourself","it's important to remember"],
 "D2":["mindset","empower","transform","achieve your goals","step-by-step","actionable",
  "growth","inspire","overcome","it's important to remember"],
 "D3":["a helpful way to think about","applicable to","timeless","meaningful journey",
  "meaningful experience","meaningful way","journey","it's worth noting"],
 "D4":["let's explore","consider this","i hope this helps","we can discuss","take a moment to",
  "reflect on","would you like to","feel free to ask","i'm here to help","is there anything else"],
}
def count(txt):
    tl = txt.lower(); c = {k: 0 for k in TIER1}
    for cat, ms in TIER1.items():
        for m in ms:
            ml = m.lower()
            c[cat] += tl.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b", tl))
    return c
def tok(t): return len(t.split())

COND = {"A1":("CondA1_Gemini_2.5Flash","condA"), "A2":("CondA2_Ungoverned_GPT4omini","CondA2"),
        "A3":("CondA3_ScholarlyPrompt_GPT4omini","CondA3"), "B":("CondB_Governed_GPT4omini","CondB")}

# ---------------------------------------------------------------- load source
reg   = json.loads((GFI/"book_registry.json").read_text())["books"]
proto = json.loads((GFI/"protocol_15q.json").read_text())
D = defaultdict(dict); missing = []
for cond,(folder,pre) in COND.items():
    for ab in sorted(reg):
        for i in range(1,16):
            qid=f"Q{i:02d}"; p = GFI/folder/f"{ab}_responses"/f"{pre}_{qid}_{ab}.json"
            if not p.exists(): missing.append(str(p)); continue
            reply = str(json.loads(p.read_text()).get("reply") or "")
            c = count(reply)
            D[(ab,qid)][cond] = dict(reply=reply, tokens=tok(reply), **c)
PAIRS = sorted(D)

FAILS = []
def check(label, got, want, tol=None, fmt="{:.3f}"):
    if tol is None:
        ok = got == want
    else:
        ok = abs(got-want) <= tol
    print(f"  {'PASS' if ok else 'FAIL'}  {label:<58} got {fmt.format(got) if isinstance(got,float) else got}"
          f"  paper says {fmt.format(want) if isinstance(want,float) else want}")
    if not ok: FAILS.append(label)

def rate(d, keys=("D1","D2","D3")): return sum(d[k] for k in keys)/d["tokens"]*1000
def test(a,b,keys=("D1","D2","D3")):
    xs=[rate(D[p][a],keys) for p in PAIRS]; ys=[rate(D[p][b],keys) for p in PAIRS]
    W,pv = wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
    z = abs(norm.ppf(pv/2)) if 0<pv<1 else 0.0
    return st.mean(xs), st.mean(ys), (st.mean(ys)-st.mean(xs))/st.mean(xs)*100, W, pv, z/len(xs)**0.5

print("="*96); print("REPRODUCE_ALL — manuscript claims vs raw response files"); print("="*96)
print(f"\n[corpus] {len(PAIRS)} question-instances x 4 conditions = {len(PAIRS)*4} responses"
      f" | missing files: {len(missing)}")
check("600 responses present", len(PAIRS)*4, 600)
check("150 per condition", len(PAIRS), 150)
check("10 books", len(reg), 10)
check("15 questions", len(proto["questions"]), 15)

print("\n[instrument] lexicon size")
check("entries", sum(len(v) for v in TIER1.values()), 46)
check("unique strings", len({m for v in TIER1.values() for m in v}), 45)
check("D1 entries", len(TIER1["D1"]), 18)

print("\n[Table 1] primary D1-D3 contrasts, full text")
ma,mb,pct,W,pv,r = test("A2","A3"); check("A2 mean", ma, 7.52, .005, "{:.2f}"); check("A3 mean", mb, 4.56, .005, "{:.2f}")
check("A2->A3 change %", pct, -39.5, .05, "{:+.1f}"); check("A2->A3 r", r, 0.55, .005, "{:.2f}")
check("A2->A3 p < 2e-11", pv < 2e-11, True)
ma,mb,pct,W,pv,r = test("A2","B");  check("B mean", mb, 3.89, .005, "{:.2f}")
check("A2->B change %", pct, -48.3, .05, "{:+.1f}"); check("A2->B W", W, 1413.0, 0.5, "{:.0f}")
check("A2->B r", r, 0.55, .005, "{:.2f}"); check("A2->B p < 2e-11", pv < 2e-11, True)
ma,mb,pct,W,pv,r = test("A3","B")
check("A3->B change %", pct, -14.5, .05, "{:+.1f}"); check("A3->B r", r, 0.13, .005, "{:.2f}")
check("A3->B p ~ 0.11 (ns)", pv, 0.106, .005, "{:.3f}")

print("\n[4.1] per-dimension A2->B")
for lab,k,wpct,wp in (("D1",("D1",),-61.1,1.0e-4),("D2",("D2",),-42.9,2.8e-5),("D3",("D3",),-49.3,1.1e-6)):
    _,_,pct,_,pv,_ = test("A2","B",k)
    check(f"{lab} change %", pct, wpct, .05, "{:+.1f}")
    # paper rounds p to 2 s.f.; accept within 5% relative of the printed value
    check(f"{lab} p = {wp:.1e}", pv, wp, abs(wp)*0.05, "{:.2e}")

print("\n[4.1] direction consistent in all ten books; book-level test")
xs=[];ys=[];same=0
for ab in sorted(reg):
    qs=[f"Q{i:02d}" for i in range(1,16)]
    a=st.mean(rate(D[(ab,q)]["A2"]) for q in qs); b=st.mean(rate(D[(ab,q)]["B"]) for q in qs)
    xs.append(a); ys.append(b); same += b<a
check("books where B < A2", same, 10)
W,pv = wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
check("book-level A2->B p", pv, 0.002, .0005, "{:.4f}")

print("\n[4.3] model choice")
_,_,_,_,pv_a1a2,r_a1a2 = test("A1","A2"); _,_,_,_,pv_a1a3,_ = test("A1","A3")
check("A1 vs A2 significant", pv_a1a2 < 1e-8, True)
check("A1 vs A3 not significant", pv_a1a3 > 0.05, True)

print("\n[4.4 / 3.5] governance log")
log=list(csv.DictReader(open(HERE/"governance_log_46.csv")))
from collections import Counter
sc=Counter(r["status"] for r in log); fam=Counter(r["family"] for r in log)
check("proposals", len(log), 46); check("applied", sc["applied"], 26); check("rejected", sc["rejected"], 20)
check("CB largest family", fam["CB"], 22)
check("CB applied rate lowest",
      sum(1 for r in log if r["family"]=="CB" and r["status"]=="applied")/fam["CB"]
      < min(sum(1 for r in log if r["family"]==f and r["status"]=="applied")/fam[f] for f in ("SB","BK")), True)
bad=[r for r in log if "Sun Tzu" in r["to_value"]]
check("two misattributed Confessions packets", len(bad), 2)
check("both marked applied", all(r["status"]=="applied" for r in bad), True)

# ------------------------------------------------- claims made only in chat
print("\n[chat-only analyses — now on the record, not asserted against the paper]")
out=[]
out.append("A3 (prompt only, no book content) vs B (pack + retrieval), per book, full text")
out.append(f"{'Book':<44}{'A3':>7}{'B':>7}{'delta':>9}")
A3v=[];Bv=[];low=0
for ab,bk in sorted(reg.items(), key=lambda kv:kv[1]["title"]):
    qs=[f"Q{i:02d}" for i in range(1,16)]
    a=st.mean(rate(D[(ab,q)]["A3"]) for q in qs); b=st.mean(rate(D[(ab,q)]["B"]) for q in qs)
    A3v.append(a); Bv.append(b); low += b<a
    out.append(f"{bk['title'][:43]:<44}{a:7.2f}{b:7.2f}{(b-a)/a*100:+8.1f}%")
out.append(f"B lower than A3 in {low}/10 books")
out.append(f"across-book spread: A3 sd {st.stdev(A3v):.2f} range {min(A3v):.2f}-{max(A3v):.2f} | "
           f"B sd {st.stdev(Bv):.2f} range {min(Bv):.2f}-{max(Bv):.2f}")
out.append(f"Levene equal-variance A3 vs B: p = {levene(A3v,Bv).pvalue:.3f}  "
           f"(no evidence the pack makes performance more consistent across books)")
HEDGE=re.compile(r"I (?:do not|don't) have|not familiar|unable to (?:access|recall)|no (?:direct )?access"
                 r"|cannot (?:verify|confirm)|may not be accurate|if I recall", re.I)
for c in ("A3","B"):
    out.append(f"{c}: {sum(1 for p in PAIRS if HEDGE.search(D[p][c]['reply']))}/150 replies hedge about access to the text")
(HERE/"adhoc_checks_output.txt").write_text("\n".join(out))
print("\n".join("  "+l for l in out))
print(f"\n  -> written to {HERE/'adhoc_checks_output.txt'}")

print("\n"+"="*96)
if FAILS:
    print(f"FAILED {len(FAILS)} CHECK(S):"); [print("   -",f) for f in FAILS]; sys.exit(1)
print(f"ALL CHECKS PASSED — every manuscript figure reproduces from the raw response files.")
sys.exit(0)
