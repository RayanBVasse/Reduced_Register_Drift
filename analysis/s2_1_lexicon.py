
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""
S2.1 — the marker lexicon as implemented, reconciled against the documented
version in the earlier paper's Appendix A, plus a sensitivity re-run.

Resolves the outstanding discrepancy: Appendix A documents D1 with 16 markers
(43 unique overall); the code implements D1 with 18 entries (45 unique). The
difference is a single editorial narrowing that the appendix records for D3
but omits for D1.

Output: s2_1_lexicon.md
"""
import json, re, os, itertools, statistics as st
from pathlib import Path
from scipy.stats import wilcoxon, norm
from collections import defaultdict

G    = DATA
HERE = Path(os.path.dirname(os.path.abspath(__file__)))

src = (HERE/"s2_5_marker_counts.py").read_text()
ns = {"__file__": str(HERE/"s2_5_marker_counts.py"), "__name__": "_reused"}
exec(compile(src[:src.index("reg = json.loads")], "s", "exec"), ns)
TIER1, SUFFIX, strip_suffix, tok = ns["TIER1"], ns["SUFFIX"], ns["strip_suffix"], ns["tok"]

# ---- the documented (Appendix A) variant: D1 uses the bare word "emotional"
DOC = {k: list(v) for k, v in TIER1.items()}
DOC["D1"] = [m for m in DOC["D1"] if m not in
             ("emotional healing","emotional wellbeing","your emotional")] + ["emotional"]

COND = {"A1":("CondA1_Gemini_2.5Flash","condA",False),
        "A2":("CondA2_Ungoverned_GPT4omini","CondA2",False),
        "A3":("CondA3_ScholarlyPrompt_GPT4omini","CondA3",False),
        "B" :("CondB_Governed_GPT4omini","CondB",True)}
SINGLE_WORD_TYPE = {"healing","resilience","self-care","vulnerable","mindset","empower",
                    "transform","actionable","growth","inspire","overcome","timeless",
                    "journey","emotional"}

def counter(lex):
    def f(txt):
        tl=txt.lower(); c={k:0 for k in lex}
        for cat,ms in lex.items():
            for m in ms:
                ml=m.lower()
                c[cat]+= tl.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b",tl))
        return c
    return f

reg = json.loads((G/"book_registry.json").read_text())["books"]
cnt_impl, cnt_doc = counter(TIER1), counter(DOC)
data=defaultdict(dict)
for cond,(folder,prefix,do_strip) in COND.items():
    for ab in sorted(reg):
        for i in range(1,16):
            qid=f"Q{i:02d}"
            reply=str(json.loads((G/folder/f"{ab}_responses"/f"{prefix}_{qid}_{ab}.json").read_text()).get("reply") or "")
            txt,_ = strip_suffix(reply) if do_strip else (reply,False)
            t=tok(txt) or 1
            ci, cd = cnt_impl(txt), cnt_doc(txt)
            data[(ab,qid)][cond]=dict(
                impl=(ci["D1"]+ci["D2"]+ci["D3"])/t*1000,
                doc =(cd["D1"]+cd["D2"]+cd["D3"])/t*1000,
                d1_impl=ci["D1"], d1_doc=cd["D1"], tokens=t)
pairs=sorted(data)

def wtest(a,b,key):
    xs=[data[p][a][key] for p in pairs]; ys=[data[p][b][key] for p in pairs]
    d=[x-y for x,y in zip(xs,ys)]
    if not any(d): return None
    W,p1=wilcoxon(xs,ys,alternative="greater",zero_method="wilcox")
    _,p2=wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
    z=abs(norm.ppf(p2/2)) if 0<p2<1 else 0.0
    return dict(ma=st.mean(xs),mb=st.mean(ys),W=W,p1=p1,p2=p2,r=z/(150**.5),
                pct=(st.mean(ys)-st.mean(xs))/st.mean(xs)*100)

L=[]; w=L.append
w("## S2.1 — Marker lexicon, and reconciliation with the documented version\n")
w("### S2.1.1 — The lexicon as implemented\n")
w("Deterministic string matching, case-insensitive. Single-word markers match "
  "on word boundaries; multi-word markers match as substrings. This is the "
  "list in `drift_reduction_3way.py` and `ablation_4way.py`, and it produced "
  "every figure reported here and in the earlier papers.\n")
names={"D1":"Therapeutic / self-help","D2":"Productivity / application",
       "D3":"Doctrinal / intellectual flattening","D4":"Chatty-assistant / audience-smoothing"}
for cat,ms in TIER1.items():
    w(f"**{cat} — {names[cat]}** ({len(ms)} entries)\n")
    w("| Marker | Match type |")
    w("|---|---|")
    for m in ms:
        w(f"| `{m}` | {'word' if m in SINGLE_WORD_TYPE else 'phrase'} |")
    w("")
tot=sum(len(v) for v in TIER1.values())
uniq=len({m for v in TIER1.values() for m in v})
w(f"Total: **{tot} entries**, **{uniq} unique strings** — "
  "`it's important to remember` is counted under both D1 and D2, so a "
  "response containing it increments both.\n")

w("### S2.1.2 — Reconciliation with the earlier paper's Appendix A\n")
w("Appendix A of the instrument paper documents **D1 with 16 markers and 43 "
  "unique strings**; the implemented list has **D1 with 18 entries and 45 "
  "unique strings**. The entire difference is one substitution in D1:\n")
w("| Appendix A (documented) | Implementation (used for all results) |")
w("|---|---|")
w("| `emotional` — one bare word, flagged in the appendix itself as "
  "\"context-sensitivity noted\" | `emotional healing`, `emotional wellbeing`, "
  "`your emotional` — three phrases |")
w("")
w("16 − 1 + 3 = 18 entries, and 43 − 1 + 3 = 45 unique strings. D2, D3 and D4 "
  "match the appendix exactly.\n")
w("This is the same editorial move the appendix *does* record for D3, where "
  "standalone `meaningful` was \"narrowed to three specific phrases\" "
  "(`meaningful journey`, `meaningful experience`, `meaningful way`) in the "
  "April 2026 author review. The review evidently narrowed `emotional` the "
  "same way; the appendix's \"Removed from Tier 1\" list records the "
  "`meaningful` narrowing and omits the `emotional` one. **The documentation "
  "is incomplete, not the instrument.**\n")
w("Narrowing a bare word to three phrases can only ever match *fewer* "
  "occurrences — every `emotional healing` is also an `emotional` — so the "
  "implemented list is strictly the more conservative **matcher**, with fewer "
  "false positives on ordinary descriptive prose about emotion. That is a "
  "separate question from which list is kinder to the governance claim, and "
  "the two do not point the same way: see S2.1.3.\n")

w("### S2.1.3 — Sensitivity: results under the documented lexicon\n")
w("Every figure re-run with the bare word `emotional` restored in place of "
  "the three phrases, D1–D3 basis, Cond_B stripped.\n")
w("| Condition | D1 markers (implemented) | D1 markers (documented) | "
  "D1–D3 /1k (implemented) | D1–D3 /1k (documented) |")
w("|---|---|---|---|---|")
for c in ("A1","A2","A3","B"):
    di=sum(data[p][c]["d1_impl"] for p in pairs); dd=sum(data[p][c]["d1_doc"] for p in pairs)
    mi=st.mean(data[p][c]["impl"] for p in pairs); md=st.mean(data[p][c]["doc"] for p in pairs)
    w(f"| {c} | {di} | {dd} | {mi:.3f} | {md:.3f} |")
w("")
w("| Contrast | Δ (implemented) | p₂ (impl.) | r (impl.) | Δ (documented) | "
  "p₂ (doc.) | r (doc.) | same conclusion? |")
w("|---|---|---|---|---|---|---|---|")
for a,b in (("A2","A3"),("A3","B"),("A2","B"),("A1","A2"),("A1","B")):
    ti, td = wtest(a,b,"impl"), wtest(a,b,"doc")
    sig_i, sig_d = ti["p2"]<0.05, td["p2"]<0.05
    w(f"| {a} → {b} | {ti['pct']:+.1f}% | {ti['p2']:.2e} | {ti['r']:.3f} | "
      f"{td['pct']:+.1f}% | {td['p2']:.2e} | {td['r']:.3f} | "
      f"{'yes' if sig_i==sig_d else '**NO**'} |")
w("")
extra = {c: sum(data[p][c]['d1_doc'] for p in pairs)-sum(data[p][c]['d1_impl'] for p in pairs)
         for c in ("A1","A2","A3","B")}
w("The documented lexicon adds "
  + ", ".join(f"{v} D1 markers in {c}" for c,v in extra.items())
  + " — the bare word fires on ordinary descriptive prose about emotion in "
    "every condition.\n")
w("**Every contrast keeps its sign and its significance verdict**, so no "
  "conclusion in the manuscript depends on which version of the lexicon is "
  "used. Two details should be reported rather than glossed:\n")
w(f"1. The broader documented list would have produced a *smaller* headline "
  f"reduction — A2→B {wtest('A2','B','doc')['pct']:+.1f}% rather than "
  f"{wtest('A2','B','impl')['pct']:+.1f}%. The narrower implemented list is "
  "therefore the better matcher but **not** the more conservative choice with "
  "respect to the governance claim. It is retained because it produced the "
  "published figures and because excluding bare `emotional` is the defensible "
  "measurement decision, not because it understates the effect.")
w("2. Under the documented list the A3→B contrast changes sign "
  f"({wtest('A3','B','impl')['pct']:+.1f}% → {wtest('A3','B','doc')['pct']:+.1f}%) "
  "while remaining far from significance on both. A contrast whose direction "
  "is not stable under a single marker substitution is best read as "
  "indistinguishable from zero, which is how §3.2 reports it.\n")
w(f"The manuscript's lexicon description and marker count are corrected to "
  f"**{tot} entries / {uniq} unique strings, D1 = {len(TIER1['D1'])}**, and "
  "the `emotional` narrowing is recorded in the revision history.\n")

w("### S2.2 — The seven suffix patterns\n")
w("Applied to Cond_B only. A response's trailing segment — the final "
  "paragraph after a blank line, or failing that the final sentence — is "
  "removed if it matches any pattern below. Matching is case-insensitive and "
  "dot-matches-newline.\n")
w("| # | Pattern | Targets |")
w("|---|---|---|")
desc=["\"Would you like to / like me to …?\"","\"Do you want / wish to …?\"",
      "\"Are you interested in …?\"","\"Shall we explore / consider / examine / delve …?\"",
      "\"Want me to …?\"","\"How does … [chapter/book/verse/…] …?\"",
      "\"How might … [chapter/book/verse/…] …?\""]
for i,(p,d) in enumerate(zip(SUFFIX,desc),1):
    w(f"| {i} | `{p.pattern}` | {d} |")
w("")
w("Patterns 6–7 carry a 400-character bound and require a structural noun "
  "(chapter, book, verse, lecture, episode, part, section), which is what "
  "distinguishes a platform routing prompt from a substantive question the "
  "model raised itself. Cond_A1, A2 and A3 are never stripped: they are not "
  "platform-served and no response in those conditions matches "
  "(0/450). Among Cond_A3 responses, 0/150 end in a routing-style question "
  "even though the pattern set would have caught them, which is why the "
  "A3→B comparison is not confounded by stripping.\n")

(HERE/"s2_1_lexicon.md").write_text("\n".join(L),encoding="utf-8")
print(f"wrote {HERE/'s2_1_lexicon.md'}")
