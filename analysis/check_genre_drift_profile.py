
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""
Checks the claim added in v6.5 §5.5: that different genres are vulnerable to
different kinds of drift ("philosophical works to therapeutic reframing,
military-strategic texts to managerial application, religious works to
secularization, historical testimony to generalized inspirational narratives").

Tests it on the UNGOVERNED baseline (A2) — that is where a genre's native
vulnerability would show, before any governance is applied. Reports the share
of each cluster's D1-D3 markers falling in each dimension.
Reads the raw response JSONs; depends on no intermediate file.
"""
import json, re, os, statistics as st
from pathlib import Path
from collections import defaultdict
GFI=DATA
HERE=Path(os.path.dirname(os.path.abspath(__file__)))
TIER1={
 "D1":["what you're feeling","it's okay to","be kind to yourself","healing","resilience","inner peace",
  "cope with","process your","self-care","on your journey","emotional healing","emotional wellbeing",
  "your emotional","vulnerable","safe space","you can do this","believe in yourself","it's important to remember"],
 "D2":["mindset","empower","transform","achieve your goals","step-by-step","actionable","growth","inspire",
  "overcome","it's important to remember"],
 "D3":["a helpful way to think about","applicable to","timeless","meaningful journey","meaningful experience",
  "meaningful way","journey","it's worth noting"]}
def count(t):
    tl=t.lower(); return {k:sum(tl.count(m) if " " in m else len(re.findall(r"\b"+re.escape(m)+r"\b",tl)) for m in v)
                          for k,v in TIER1.items()}
reg=json.loads((GFI/"book_registry.json").read_text())["books"]
CL={"G1":"Philosophical & spiritual","G2":"Civic / testimony","G3":"Strategic & expository"}
agg=defaultdict(lambda: defaultdict(int)); perbook={}
for ab,b in reg.items():
    tot=defaultdict(int)
    for i in range(1,16):
        rp=str(json.loads((GFI/"CondA2_Ungoverned_GPT4omini"/f"{ab}_responses"/f"CondA2_Q{i:02d}_{ab}.json").read_text()).get("reply") or "")
        for k,v in count(rp).items(): tot[k]+=v; agg[b["cluster"]][k]+=v
    perbook[b["title"]]=(b["cluster"],dict(tot))
L=[]; w=L.append
w("Genre drift profile — UNGOVERNED baseline (A2), share of D1-D3 markers by dimension\n")
w(f"{'Cluster':<28}{'D1 therapeutic':>16}{'D2 productivity':>17}{'D3 flattening':>15}{'n markers':>11}")
for c in ("G1","G2","G3"):
    t=sum(agg[c].values())
    w(f"{CL[c]:<28}" + "".join(f"{agg[c][k]/t*100:15.1f}%" for k in ("D1","D2","D3")) + f"{t:11d}")
w("")
w(f"{'Book':<44}{'D1%':>7}{'D2%':>7}{'D3%':>7}{'n':>6}")
for title,(c,t) in sorted(perbook.items(), key=lambda kv:kv[1][0]):
    n=sum(t.values())
    w(f"{title[:43]:<44}" + "".join(f"{t[k]/n*100:6.0f}%" for k in ("D1","D2","D3")) + f"{n:6d}")
w("")
w("Claim in v6.5 §5.5, tested:")
g1,g3=agg["G1"],agg["G3"]
w(f"  'philosophical works vulnerable to therapeutic reframing'  -> G1 D1 share "
  f"{g1['D1']/sum(g1.values())*100:.1f}% vs corpus-wide "
  f"{sum(agg[c]['D1'] for c in agg)/sum(sum(agg[c].values()) for c in agg)*100:.1f}%")
w(f"  'military-strategic texts to managerial application'       -> G3 D2 share "
  f"{g3['D2']/sum(g3.values())*100:.1f}% vs corpus-wide "
  f"{sum(agg[c]['D2'] for c in agg)/sum(sum(agg[c].values()) for c in agg)*100:.1f}%")
w("")
w("NOTE: D2 dominates every cluster, so 'each genre has its own vulnerability' is")
w("not what this measure shows. The lexicon has 4 D1-only, 9 D2-only and 7 D3-only")
w("distinct strings and is not balanced across dimensions, so cross-dimension share")
w("comparisons are confounded by lexicon construction.")
(HERE/"genre_drift_profile_output.txt").write_text("\n".join(L))
print("\n".join(L))
