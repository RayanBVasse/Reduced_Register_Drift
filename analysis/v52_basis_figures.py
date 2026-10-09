
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""Every figure v5.2 needs on the FULL-TEXT (unstripped) basis."""
import csv, json, statistics as st, itertools
from pathlib import Path
from collections import defaultdict
from scipy.stats import wilcoxon, norm
G=DATA
rc=list(csv.DictReader(open(data_file("per_response_rawcounts.csv"))))
for r in rc:
    for k in ("d1","d2","d3","d4","tokens","tokens_raw","d1_raw","d2_raw","d3_raw","d4_raw"): r[k]=int(r[k])
reg=json.loads((G/"book_registry.json").read_text())["books"]
proto=json.loads((G/"protocol_15q.json").read_text())
idx=defaultdict(dict)
for r in rc: idx[(r["ab"],r["qid"])][r["cond"]]=r
pairs=sorted(idx); C=["A1","A2","A3","B"]

def rate(r,keys):                      # full-text basis for every condition
    return sum(r[f"{k}_raw"] for k in keys)/r["tokens_raw"]*1000
def test(a,b,keys):
    xs=[rate(idx[p][a],keys) for p in pairs]; ys=[rate(idx[p][b],keys) for p in pairs]
    d=[x-y for x,y in zip(xs,ys)]
    if not any(d): return None
    W,p=wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
    z=abs(norm.ppf(p/2)) if 0<p<1 else 0.
    return dict(ma=st.mean(xs),mb=st.mean(ys),pct=(st.mean(ys)-st.mean(xs))/st.mean(xs)*100,
                W=W,p=p,r=z/150**.5)

D123=("d1","d2","d3"); T1=("d1","d2","d3","d4")
print("### condition means, FULL TEXT, D1-D3")
for c in C: print(f"   {c}: {st.mean(rate(idx[p][c],D123) for p in pairs):.3f}")
print("\n### headline + mechanism (full text, D1-D3)")
for a,b in (("A2","B"),("A2","A3"),("A3","B"),("A1","A2"),("A1","B"),("A1","A3")):
    t=test(a,b,D123)
    print(f"   {a}->{b}: {t['ma']:.2f} -> {t['mb']:.2f}  {t['pct']:+.1f}%  W={t['W']:.0f}  p={t['p']:.2e}  r={t['r']:.3f}")
print("\n### per dimension A2->B (full text)")
for lab,k in (("D1",("d1",)),("D2",("d2",)),("D3",("d3",))):
    t=test("A2","B",k); print(f"   {lab}: {t['ma']:.3f} -> {t['mb']:.3f}  {t['pct']:+.1f}%  p={t['p']:.2e}  r={t['r']:.3f}")
print("\n### Tier-1 A2->B (full text)")
t=test("A2","B",T1); print(f"   {t['ma']:.2f} -> {t['mb']:.2f}  {t['pct']:+.1f}%  p={t['p']:.2e}  r={t['r']:.3f}")

print("\n### per book, D1-D3 full text  (does 10/10 hold?)")
red=0
for ab,b in sorted(reg.items(), key=lambda kv:kv[1]["title"]):
    m={c: st.mean(rate(idx[(ab,q)][c],D123) for q in [f'Q{i:02d}' for i in range(1,16)]) for c in C}
    d=(m["B"]-m["A2"])/m["A2"]*100; red+= d<0
    print(f"   {b['title'][:44]:46s} A2={m['A2']:5.2f}  B={m['B']:5.2f}  {d:+6.1f}%")
print(f"   --> books reducing: {red}/10")

print("\n### book-level clustered (n=10, full text)")
for a,b in (("A2","A3"),("A2","B"),("A3","B")):
    xs=[];ys=[]
    for ab in sorted(reg):
        qs=[f'Q{i:02d}' for i in range(1,16)]
        xs.append(st.mean(rate(idx[(ab,q)][a],D123) for q in qs))
        ys.append(st.mean(rate(idx[(ab,q)][b],D123) for q in qs))
    W,p=wilcoxon(xs,ys,alternative="two-sided",zero_method="wilcox")
    print(f"   {a}->{b}: {st.mean(xs):.2f} -> {st.mean(ys):.2f}  {(st.mean(ys)-st.mean(xs))/st.mean(xs)*100:+.1f}%  p={p:.2e}  {sum(x>y for x,y in zip(xs,ys))}/10")

print("\n### by block, D1-D3 full text")
for blk in sorted(proto["_blocks"]):
    qs=[q for q in proto["questions"] if str(proto["questions"][q]["block"])==str(blk)]
    m={c: st.mean(rate(idx[p][c],D123) for p in pairs if p[1] in qs) for c in C}
    print(f"   block {blk}: A1={m['A1']:5.2f} A2={m['A2']:5.2f} A3={m['A3']:5.2f} B={m['B']:5.2f}   A2->B {(m['B']-m['A2'])/m['A2']*100:+6.1f}%")
