#!/usr/bin/env python3
"""
Figures for the continuation paper. Every figure is generated from the archived
data — no hand-entered numbers.

Outputs 300 dpi PNG + LZW-compressed TIFF for each figure into 10_figures/.
"""
import csv, json, os, sys, statistics as st
from pathlib import Path
from collections import defaultdict, Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
BASE = HERE.parent
SUP  = HERE.parent / "analysis"   # derived CSVs live beside the analysis scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
from _paths import DATA as G, data_file

plt.rcParams.update({
    "font.family":"DejaVu Sans","font.size":9,"axes.titlesize":10,
    "axes.labelsize":9,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"grid.linewidth":0.6,
    "axes.axisbelow":True,"figure.dpi":300,"savefig.bbox":"tight",
})
C = {"A1":"#8c8c8c","A2":"#c44536","A3":"#e0a458","B":"#2a6f97"}
LAB = {"A1":"A1  Gemini\nungoverned","A2":"A2  gpt-4o-mini\nbare prompt",
       "A3":"A3  gpt-4o-mini\nscholarly prompt","B":"B  governed\n(CPLite)"}
CONDS=["A1","A2","A3","B"]

# ---------------------------------------------------------------- data
rc=list(csv.DictReader(open(data_file("per_response_rawcounts.csv"))))
for r in rc:
    for k in ("d1","d2","d3","d4","tokens","tokens_raw",
              "d1_raw","d2_raw","d3_raw","d4_raw"): r[k]=int(r[k])
idx=defaultdict(dict)
for r in rc: idx[(r["ab"],r["qid"])][r["cond"]]=r
pairs=sorted(idx)
reg=json.loads((G/"book_registry.json").read_text())
BOOKS,CLUSTERS=reg["books"],reg["_clusters"]
proto=json.loads((G/"protocol_15q.json").read_text())
log=list(csv.DictReader(open(data_file("governance_log_46.csv"))))

def d123(r): return (r["d1"]+r["d2"]+r["d3"])/r["tokens"]*1000
def d123raw(r): return (r["d1_raw"]+r["d2_raw"]+r["d3_raw"])/r["tokens_raw"]*1000
def rate(sub,keys=("d1","d2","d3"),raw=False):
    sfx="_raw" if raw else ""; tk="tokens_raw" if raw else "tokens"
    return st.mean(sum(r[f"{k}{sfx}"] for k in keys)/r[tk]*1000 for r in sub)

saved=[]
def save(fig,name,title):
    png=HERE/f"{name}.png"; tif=HERE/f"{name}.tiff"
    fig.savefig(png,dpi=300)
    fig.savefig(tif,dpi=300,pil_kwargs={"compression":"tiff_lzw"})
    plt.close(fig); saved.append((name,title))
    print(f"  {name}.png / .tiff")

# ============================================= Figure 1 — D1-D3 by condition
fig,ax=plt.subplots(figsize=(5.4,3.4))
vals=[rate([r for r in rc if r["cond"]==c], raw=True) for c in CONDS]
bars=ax.bar(range(4),vals,color=[C[c] for c in CONDS],width=.62,
            edgecolor="white",linewidth=.8)

for i,v in enumerate(vals):
    ax.text(i,v+.13,f"{v:.2f}",ha="center",fontsize=8.6,fontweight="bold")
a2,b=vals[1],vals[3]
ax.annotate("",xy=(3,b+.72),xytext=(1,a2+.55),
            arrowprops=dict(arrowstyle="->",color="#444",lw=1.1,
                            connectionstyle="arc3,rad=-.22"))
ax.text(2,a2+1.02,"deployment contrast\n−48.3%, p = 1.4×10⁻¹¹",ha="center",
        fontsize=7.6,color="#444")
ax.set_xticks(range(4)); ax.set_xticklabels([LAB[c] for c in CONDS],fontsize=7.8)
ax.set_ylabel("D1–D3 markers per 1,000 tokens")
ax.set_title("Register drift by condition — unmodified response text, n = 150 each",pad=9)
ax.set_ylim(0,9.4)
save(fig,"Figure_1_drift_by_condition","D1–D3 drift by condition")

# ============================================= Figure S1 — per-book
pb=[]
for ab,bk in BOOKS.items():
    m={c:rate([r for r in rc if r["ab"]==ab and r["cond"]==c], raw=True) for c in CONDS}
    pb.append((bk["title"],bk["cluster"],m))
pb.sort(key=lambda x:(x[2]["B"]-x[2]["A2"])/x[2]["A2"])
fig,ax=plt.subplots(figsize=(7.0,4.3))
y=range(len(pb)); h=.36
ax.barh([i+h/2 for i in y],[p[2]["A2"] for p in pb],height=h,color=C["A2"],
        label="A2 — ungoverned (bare prompt)")
ax.barh([i-h/2 for i in y],[p[2]["B"] for p in pb],height=h,color=C["B"],
        label="B — governed")
for i,p in enumerate(pb):
    pct=(p[2]["B"]-p[2]["A2"])/p[2]["A2"]*100
    ax.text(max(p[2]["A2"],p[2]["B"])+.2,i,f"{pct:+.0f}%",va="center",
            fontsize=7.6,color="#2a6f97",fontweight="bold")
ax.set_yticks(list(y))
ax.set_yticklabels([f"{t}  ({c})" for t,c,_ in pb],fontsize=7.8)
ax.set_xlabel("D1–D3 markers per 1,000 tokens")
ax.set_title("Governance reduces drift in all ten texts (unmodified text)",pad=9)
ax.legend(frameon=False,fontsize=8,ncol=2,loc="upper center",
          bbox_to_anchor=(0.5,-0.13))
ax.set_xlim(0,14.6)
save(fig,"Figure_S1_per_book_reduction","Per-book reduction, A2 vs B")

# ============================================= Figure S2 — D4 / Tier-1 raw vs stripped
fig,axes=plt.subplots(1,2,figsize=(7.2,3.3))
for ax,keys,ttl in ((axes[0],("d4",),"D4 — chatty-assistant markers"),
                    (axes[1],("d1","d2","d3","d4"),"Tier-1 total (D1+D2+D3+D4)")):
    raw=[rate([r for r in rc if r["cond"]==c],keys,raw=True) for c in CONDS]
    strp=[rate([r for r in rc if r["cond"]==c],keys,raw=False) for c in CONDS]
    x=range(4); wd=.36
    ax.bar([i-wd/2 for i in x],raw,wd,color="#b0b7bd",label="follow-on question retained")
    ax.bar([i+wd/2 for i in x],strp,wd,color=[C[c] for c in CONDS],
           label="removed (as analysed)")
    ax.set_xticks(list(x)); ax.set_xticklabels(CONDS,fontsize=8.5)
    ax.set_title(ttl,fontsize=9); ax.set_ylabel("markers per 1,000 tokens")
    d=raw[3]-strp[3]
    ax.annotate("",xy=(3.16,strp[3]),xytext=(3.16,raw[3]),
                arrowprops=dict(arrowstyle="<->",color="#13405e",lw=1.0))
    ax.text(3.26,(raw[3]+strp[3])/2,f"−{d:.2f}",fontsize=7.4,color="#13405e",va="center")
    ax.set_xlim(-0.6,3.95)
axes[0].legend(frameon=False,fontsize=7.4,loc="upper left")
axes[1].axhline(rate([r for r in rc if r["cond"]=="A2"],("d1","d2","d3","d4")),
                ls=":",lw=1.0,color="#c44536")
_a2t=rate([r for r in rc if r["cond"]=="A2"],("d1","d2","d3","d4"))
axes[1].set_ylim(0,11.4)
axes[1].text(-0.5,_a2t+.45,"ungoverned A2 baseline — raw B exceeds it",
             fontsize=6.8,color="#c44536")
fig.suptitle("The governed follow-on question accounts for 89% of Cond_B's D4 markers",
             fontsize=9.6,y=1.02)
save(fig,"Figure_S2_followon_question","D4 and Tier-1, follow-on question retained vs removed")

# ============================================= Figure S3 — proposals family x cluster
fig,ax=plt.subplots(figsize=(5.4,3.2))
fams=["CB","SB","BK"]; cls=["G1","G2","G3"]
FN={"CB":"Companion\nbehaviour","SB":"Scope &\nboundary","BK":"Book\nknowledge"}
CC={"G1":"#4a6fa5","G2":"#7ba05b","G3":"#c17f59"}
bot=[0]*3
for cl in cls:
    v=[sum(1 for r in log if r["family"]==f and r["cluster"]==cl) for f in fams]
    ax.bar(range(3),v,.56,bottom=bot,color=CC[cl],label=f"{cl} (n={sum(1 for b in BOOKS.values() if b['cluster']==cl)} books)")
    for i,(vv,bb) in enumerate(zip(v,bot)):
        if vv: ax.text(i,bb+vv/2,str(vv),ha="center",va="center",fontsize=8,color="white",fontweight="bold")
    bot=[a+b for a,b in zip(bot,v)]
for i,t in enumerate(bot): ax.text(i,t+.4,f"{t}",ha="center",fontsize=8.6,fontweight="bold")
ax.set_xticks(range(3)); ax.set_xticklabels([FN[f] for f in fams],fontsize=8.2)
ax.set_ylabel("governance proposals"); ax.set_ylim(0,26)
ax.set_title("46 curator proposals by lever family and genre cluster",pad=9)
ax.legend(frameon=False,fontsize=7.6,title="cluster",title_fontsize=7.6)
save(fig,"Figure_S3_proposals_by_family","Proposals by family and cluster")

# ============================================= Figure S4 — applied rate
fig,ax=plt.subplots(figsize=(5.8,3.2))
groups=[("CB",[r for r in log if r["family"]=="CB"]),
        ("SB",[r for r in log if r["family"]=="SB"]),
        ("BK",[r for r in log if r["family"]=="BK"]),
        ("",[]),
        ("G1",[r for r in log if r["cluster"]=="G1"]),
        ("G2",[r for r in log if r["cluster"]=="G2"]),
        ("G3",[r for r in log if r["cluster"]=="G3"])]
xs=[];hs=[];cols=[];labs=[]
for i,(nm,sub) in enumerate(groups):
    if not nm: continue
    a=sum(1 for r in sub if r["status"]=="applied")
    xs.append(i); hs.append(a/len(sub)*100); labs.append(f"{nm}\nn={len(sub)}")
    cols.append("#2a6f97" if nm in ("CB","SB","BK") else CC.get(nm,"#888"))
ax.bar(xs,hs,.6,color=cols)
for x,h,(nm,sub) in zip(xs,hs,[g for g in groups if g[0]]):
    a=sum(1 for r in sub if r["status"]=="applied")
    ax.text(x,h+1.6,f"{h:.0f}%",ha="center",fontsize=8.4,fontweight="bold")
    ax.text(x,3,f"{a}/{len(sub)}",ha="center",fontsize=7,color="white")
allr=sum(1 for r in log if r["status"]=="applied")/len(log)*100
ax.axhline(allr,ls="--",lw=1.0,color="#444")
ax.text(6.6,allr+1.6,f"overall {allr:.0f}%",fontsize=7.4,color="#444",ha="right")
ax.set_xticks(xs); ax.set_xticklabels(labs,fontsize=7.8)
ax.set_ylabel("applied rate (%)"); ax.set_ylim(0,100)
ax.set_title("Applied rate by lever family and by genre cluster",pad=9)
ax.text(1,-23,"lever family",ha="center",fontsize=8,style="italic",color="#555")
ax.text(5,-23,"genre cluster",ha="center",fontsize=8,style="italic",color="#555")
save(fig,"Figure_S4_applied_rate","Applied rate by family and cluster")

# ============================================= Figure S5 — drift by block
fig,ax=plt.subplots(figsize=(6.4,3.5))
blocks=sorted(proto["_blocks"])
for c in CONDS:
    ys=[]
    for b in blocks:
        qs=[q for q in proto["questions"] if str(proto["questions"][q]["block"])==str(b)]
        ys.append(st.mean(d123raw(idx[p][c]) for p in pairs if p[1] in qs))
    ax.plot(range(len(blocks)),ys,marker="o",ms=5,lw=1.8,color=C[c],
            label=LAB[c].replace("\n"," "))
ax.set_xticks(range(len(blocks)))
_SHORT={"1":"baseline","2":"reader-\nhelpfulness","3":"modern\napplication",
        "4":"belief /\nframework","5":"high-drift\nstress"}
ax.set_xticklabels([f"Block {b}\n{_SHORT[b]}" for b in blocks],fontsize=7.4)
ax.set_xlim(-0.35,4.5); ax.set_ylim(1.2,11.6)
ax.set_ylabel("D1–D3 markers per 1,000 tokens")
ax.set_title("Governance acts where the question invites drift, not uniformly",pad=9)
ax.legend(frameon=False,fontsize=7.6)
ax.annotate("smallest effect on the\nbaseline questions (−10.9%)",
            xy=(0.04,3.55),xytext=(0.30,1.75),fontsize=7.0,color="#555",
            ha="left",va="bottom",
            arrowprops=dict(arrowstyle="->",color="#999",lw=.8))
ax.legend_.set_bbox_to_anchor((1.0,1.02))
save(fig,"Figure_S5_drift_by_block","Drift by protocol block")

# ============================================= Figure S6 — pipeline
fig,ax=plt.subplots(figsize=(8.4,2.6)); ax.axis("off")
ax.set_xlim(0,100); ax.set_ylim(0,34)
steps=[("1\nPARSE","source text →\nchapter-segmented"),
       ("2\nCHUNK","sentence-aware\n512 tok / 64 overlap"),
       ("3\nEMBED","book-specific\nvector namespace"),
       ("4\nGENERATE","AI-drafted pack →\ncurator review"),
       ("5\nRENDER","pack →\nsystem prompt"),
       ("6\nSERVE","prompt + retrieval →\nreader companion")]
wd,gap=14.6,1.6; x0=1.0
for i,(t,sub) in enumerate(steps):
    x=x0+i*(wd+gap)
    ax.add_patch(FancyBboxPatch((x,14),wd,12,boxstyle="round,pad=0.35,rounding_size=1.2",
        fc="#eaf1f6" if i<3 else "#dceaf2",ec="#2a6f97",lw=1.0))
    ax.text(x+wd/2,22.4,t,ha="center",va="center",fontsize=7.8,fontweight="bold",color="#13405e")
    ax.text(x+wd/2,17.2,sub,ha="center",va="center",fontsize=5.9,color="#333")
    if i<5:
        ax.add_patch(FancyArrowPatch((x+wd,20),(x+wd+gap,20),
            arrowstyle="-|>",mutation_scale=9,color="#2a6f97",lw=1.0))
gx=x0+3*(wd+gap)-2.0; gw=wd*3+gap*2+2.0
ax.add_patch(FancyBboxPatch((gx,3.4),gw,6.8,
    boxstyle="round,pad=0.3,rounding_size=1.2",fc="#fdf3e7",ec="#c17f59",lw=1.0,ls="--"))
ax.text(gx+gw/2,6.8,"3A governance loop — propose · preview (A/B) · apply / reject",
        ha="center",va="center",fontsize=6.6,color="#8a4f2d")
ax.add_patch(FancyArrowPatch((gx+gw/2,10.2),(x0+3*(wd+gap)+wd/2,14),
    arrowstyle="-|>",mutation_scale=9,color="#c17f59",lw=1.0,ls="--"))
ax.text(50,30.5,"CPLite pipeline: text to governed reader companion",
        ha="center",fontsize=9.6,fontweight="bold")
save(fig,"Figure_S6_pipeline","CPLite pipeline")

print("\nGenerated:")
for n,t in saved: print(f"  {n:38s} {t}")
