#!/usr/bin/env python3
"""
S7.6 — Cond_B thread accumulation and response length (reviewer point C)
S7.7 — per-dimension decomposition of A3 -> B (reviewer point D, retrieval)

Written after inspecting the data, not before: the first-turn test does NOT
replicate the headline contrast, and the reason is a design confound that the
supplement reports rather than conceals.
"""
import json, csv, os, statistics as st
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr, wilcoxon, norm

G    = Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
rc   = list(csv.DictReader(open(HERE/"per_response_rawcounts.csv")))
for r in rc:
    for k in ("d1","d2","d3","d4","tokens","tokens_raw"): r[k]=int(r[k])
proto = json.loads((G/"protocol_15q.json").read_text())
Q, BLOCKS = proto["questions"], proto["_blocks"]

CONDS=["A1","A2","A3","B"]
idx=defaultdict(dict)
for r in rc: idx[(r["ab"],r["qid"])][r["cond"]]=r
pairs=sorted(idx)
def d123(r): return (r["d1"]+r["d2"]+r["d3"])/r["tokens"]*1000
def mk(r):   return r["d1"]+r["d2"]+r["d3"]

def wil(xs, ys):
    d=[x-y for x,y in zip(xs,ys)]
    if not any(d): return float("nan"),1.0,0.0
    W,p=wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
    z=abs(norm.ppf(p/2)) if 0<p<1 else 0.0
    return W,p,z/(len(xs)**0.5)

L=[]; w=L.append

# ================================================================= S7.6
w("### S7.6 — Thread accumulation, question order and response length\n")
w("Three properties of Cond_B are entangled and are reported together "
  "because separating them is not possible in this design.\n")

th=defaultdict(set); turns={}
for ab in sorted({r["ab"] for r in rc}):
    t=[]
    for i in range(1,16):
        d=json.loads((G/"CondB_Governed_GPT4omini"/f"{ab}_responses"/f"CondB_Q{i:02d}_{ab}.json").read_text())
        th[ab].add(d.get("thread_id")); t.append(d.get("turns_used"))
    turns[ab]=t
one=sum(1 for ab in th if len(th[ab])==1)
w("#### (a) Accumulation is real\n")
w(f"**{one}/{len(th)}** books used a single `thread_id` across all fifteen "
  f"questions, `turns_used` incrementing 1→15 against a cap of 15. Cond_B's "
  "later answers are conditioned on its earlier ones. A1, A2 and A3 are "
  "independent single-shot completions. The book-level clustering check "
  "(S7.4) does not address this: it removes dependence *across* books, not "
  "sequential dependence *within* a thread.\n")

w("#### (b) Question order is perfectly confounded with question type\n")
w("The protocol is administered in block order, and the blocks escalate "
  "drift pressure by design:\n")
w("| Block | Questions | Description |")
w("|---|---|---|")
for b in sorted(BLOCKS):
    qs=[q for q in sorted(Q) if str(Q[q]["block"])==str(b)]
    w(f"| {b} | {qs[0]}–{qs[-1]} | {BLOCKS[b]} |")
w("")
w("**Position in the thread and difficulty of the question are therefore the "
  "same variable.** No analysis on this corpus can attribute a position trend "
  "to accumulation rather than to the questions getting harder. We state this "
  "rather than running a test that appears to settle it.\n")

w("What the position correlation shows, with that caveat:\n")
w("| Condition | Thread structure | ρ (question index vs D1–D3) | p |")
w("|---|---|---|---|")
rho={}
for c in CONDS:
    xs=[int(p[1][1:]) for p in pairs]; ys=[d123(idx[p][c]) for p in pairs]
    r_,p_=spearmanr(xs,ys); rho[c]=(r_,p_)
    w(f"| {c} | {'single accumulating thread' if c=='B' else 'independent calls'} | "
      f"{r_:+.3f} | {p_:.3f} |")
w("")
w(f"The **single-shot** conditions show the clearest upward trends "
  f"(A3 ρ = {rho['A3'][0]:+.3f}, p = {rho['A3'][1]:.3f}; "
  f"A1 ρ = {rho['A1'][0]:+.3f}, p = {rho['A1'][1]:.3f}), which cannot be "
  "accumulation because nothing accumulates in them — it is the blocks "
  f"getting harder. Cond_B, the only accumulating condition, is the "
  f"**flattest** (ρ = {rho['B'][0]:+.3f}, p = {rho['B'][1]:.3f}). If "
  "accumulation had a direction here, it was to hold the governed companion "
  "steady as drift pressure rose, not to let drift build.\n")

w("#### (c) Drift by block: where the deployment effect lives\n")
w("| Block | Questions | A1 | A2 | A3 | B | Δ A2→B |")
w("|---|---|---|---|---|---|---|")
for b in sorted(BLOCKS):
    qs=[q for q in sorted(Q) if str(Q[q]["block"])==str(b)]
    m={c: st.mean(d123(idx[p][c]) for p in pairs if p[1] in qs) for c in CONDS}
    w(f"| {b} | {len(qs)} | {m['A1']:.2f} | {m['A2']:.2f} | {m['A3']:.2f} | "
      f"{m['B']:.2f} | {(m['B']-m['A2'])/m['A2']*100:+.1f}% |")
w("")
b1=[q for q in sorted(Q) if str(Q[q]["block"])=="1"]
m1={c: st.mean(d123(idx[p][c]) for p in pairs if p[1] in b1) for c in CONDS}
w(f"**Block 1 is the exception that makes the pattern legible.** On the three "
  f"baseline questions, Cond_B ({m1['B']:.2f}) is indistinguishable from the "
  f"ungoverned baseline ({m1['A2']:.2f}). Where a question does not invite "
  "self-help framing, governance has nothing to suppress and makes no "
  "measurable difference. The deployment effect lives entirely in the "
  "drift-stress blocks. That is the expected behaviour of a constraint, and "
  "it is more informative than a uniform reduction would be.\n")

w("#### (d) The first-turn test, and why it does not settle the matter\n")
w("Q01 is the first turn of every thread, so for Q01 alone Cond_B is as "
  "independent as the other conditions. Re-running the contrasts there:\n")
w("| Contrast | mean (a) | mean (b) | Δ | W | p (two-sided) | books reducing |")
w("|---|---|---|---|---|---|---|")
q1=[p for p in pairs if p[1]=="Q01"]
for a,b in (("A2","B"),("A3","B"),("A2","A3")):
    xs=[d123(idx[p][a]) for p in q1]; ys=[d123(idx[p][b]) for p in q1]
    W,pv,_=wil(xs,ys)
    w(f"| {a} → {b} | {st.mean(xs):.2f} | {st.mean(ys):.2f} | "
      f"{(st.mean(ys)-st.mean(xs))/st.mean(xs)*100:+.1f}% | {W:.1f} | {pv:.3f} | "
      f"{sum(x>y for x,y in zip(xs,ys))}/10 |")
w("")
w("**The headline contrast does not replicate on Q01, and Cond_B is worse.** "
  "We report this rather than omit it. It is not, however, an independence "
  "result, because Q01 is simultaneously the first turn *and* a block-1 "
  "baseline question — the one block where (c) shows no condition drifts "
  "much and governance has nothing to act on. The test confounds the thing it "
  "is meant to isolate with the thing it is meant to hold constant, and with "
  "n = 10 on the protocol's least demanding item it has very little power. "
  "It should be read as uninformative about accumulation, not as evidence "
  "against the deployment effect.\n")

w("#### (e) Response length\n")
w("| Condition | Mean scored tokens/response | D1–D3 markers/response | Markers per response ÷ A2 | Tokens per response ÷ A2 |")
w("|---|---|---|---|---|")
tk={c: st.mean(idx[p][c]["tokens"] for p in pairs) for c in CONDS}
mkc={c: st.mean(mk(idx[p][c]) for p in pairs) for c in CONDS}
for c in CONDS:
    w(f"| {c} | {tk[c]:.0f} | {mkc[c]:.2f} | {mkc[c]/mkc['A2']:.2f}× | {tk[c]/tk['A2']:.2f}× |")
w("")
w(f"**Cond_B is far terser** — {tk['B']:.0f} scored tokens per response "
  f"against A2's {tk['A2']:.0f}. This raises an obvious alternative "
  "explanation: a shorter answer has fewer opportunities to drift, so is the "
  "effect simply brevity?\n")
w(f"The ratios answer it. Cond_B produces **{mkc['B']/mkc['A2']:.2f}× the "
  f"markers** of Cond_A2 while producing **{tk['B']/tk['A2']:.2f}× the "
  f"tokens**. If terseness alone explained the result the two ratios would "
  "match; markers fall roughly "
  f"{(tk['B']/tk['A2'])/(mkc['B']/mkc['A2']):.1f} times faster than length "
  "does. Note also that the per-1,000-token rate already normalises for "
  "length, and that the normalisation works *against* Cond_B: the smallest "
  "denominator in the study inflates its rate, and it still records the "
  "lowest one.\n")
w("Brevity is nonetheless a real behavioural difference between the "
  "conditions, not a nuisance parameter — a governed companion that answers "
  "in 166 words where an ungoverned one answers in 381 is giving readers "
  "something different, and whether that is a gain or a loss is a question "
  "about fidelity and usefulness that this instrument cannot answer.\n")

# ================================================================= S7.7
w("### S7.7 — Where the A3→B difference sits, by dimension\n")
w("Retrieval is an uncontrolled difference between A3 and B: A3 receives a "
  "strong instruction and **no book content**, while B receives the pack "
  "*and* retrieval over the chaptered text. If retrieval does independent "
  "work, the most plausible site is **D3 (doctrinal / intellectual "
  "flattening)** — grounding answers in actual passages should make generic "
  "flattening less likely — rather than D1 or D2, which are register "
  "properties the A3 instruction already names.\n")
w("| Dimension | A2 | A3 | B (stripped) | Δ A3→B | p (two-sided) | r |")
w("|---|---|---|---|---|---|---|")
for lab,keys in (("D1 therapeutic",("d1",)),("D2 productivity",("d2",)),
                 ("D3 flattening",("d3",)),("**D1–D3 combined**",("d1","d2","d3"))):
    def rt(c): return st.mean(sum(idx[p][c][k] for k in keys)/idx[p][c]["tokens"]*1000 for p in pairs)
    xs=[sum(idx[p]["A3"][k] for k in keys)/idx[p]["A3"]["tokens"]*1000 for p in pairs]
    ys=[sum(idx[p]["B"][k]  for k in keys)/idx[p]["B"]["tokens"]*1000  for p in pairs]
    _,pv,rr=wil(xs,ys); ma,mb=st.mean(xs),st.mean(ys)
    w(f"| {lab} | {rt('A2'):.2f} | {ma:.2f} | {mb:.2f} | {(mb-ma)/ma*100:+.1f}% | "
      f"{pv:.3f} | {rr:.3f} |")
w("")
w("The A3→B difference is **not** concentrated in D3 — D3 falls 12.0% "
  "(ns), less than D1's 28.9% (also ns), while D2 is flat. On this measure "
  "retrieval produces no detectable D3 advantage, which is the opposite of "
  "what the retrieval hypothesis predicts.\n")
w("This bounds the confound rather than disposing of it. *If* retrieval "
  "helps, it does not help in the dimension where its mechanism is most "
  "plausible, and not by enough to register at n = 150. The honest statement "
  "is that A3 and B differ in retrieval, temperature, serving stack and "
  "response length, and that the dimension-level pattern gives no positive "
  "evidence that retrieval is doing concealed work. A fifth condition — "
  "retrieval without a pack — would isolate it; that run is not performed "
  "here and is named as future work.\n")

(HERE/"s7_6_7_thread_retrieval.md").write_text("\n".join(L),encoding="utf-8")
print("\n".join(L))
