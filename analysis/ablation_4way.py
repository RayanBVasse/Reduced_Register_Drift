
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""4-way analysis incl. Cond_A3 ablation. Reads response JSONs directly from drive.
Methodology identical to drift_reduction_3way.py (lexicon, suffix stripping, whitespace
tokenisation, per-1k, paired Wilcoxon, r=Z/sqrt(N)). Suffix stripping applies to B only
(platform artifact); A1/A2/A3 are not platform-served so are never stripped."""
import json, re
from pathlib import Path
import pandas as pd, numpy as np
from scipy.stats import wilcoxon, norm

G = DATA
OUT = Path(__file__).resolve().parent
COND = {  # cond -> (folder, file-prefix, strip?)
 "A1":("CondA1_Gemini_2.5Flash","condA",False),
 "A2":("CondA2_Ungoverned_GPT4omini","CondA2",False),
 "A3":("CondA3_ScholarlyPrompt_GPT4omini","CondA3",False),
 "B": ("CondB_Governed_GPT4omini","CondB",True),
}
TIER1={
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
SUFFIX=[re.compile(p,re.I|re.S) for p in [
 r"^\s*would you like (?:to|me to)\b.*\?\s*$", r"^\s*do you (?:want|wish) (?:to|me to)\b.*\?\s*$",
 r"^\s*are you interested in\b.*\?\s*$", r"^\s*shall we (?:explore|consider|examine|delve)\b.*\?\s*$",
 r"^\s*want me to\b.*\?\s*$",
 r"^\s*how does\b.{1,400}\b(?:chapter|book|verse|lecture|episode|part|section)\b[^?]*\?\s*$",
 r"^\s*how might\b.{1,400}\b(?:chapter|book|verse|lecture|episode|part|section)\b[^?]*\?\s*$"]]
def strip_suffix(t):
    if not t: return t,False
    s=t.rstrip(); parts=s.rsplit("\n\n",1)
    if len(parts)==2:
        last=parts[1].strip()
        for p in SUFFIX:
            if p.match(last): return parts[0].rstrip(),True
    b=[m.end() for m in re.finditer(r"[.!?][\s'\"\)\]]*\s+(?=[A-Z])",s)]
    if b:
        body,last=s[:b[-1]].rstrip(),s[b[-1]:].strip()
        for p in SUFFIX:
            if p.match(last): return body,True
    return t,False
def count(txt):
    tl=txt.lower(); c={k:0 for k in TIER1}
    for cat,ms in TIER1.items():
        for m in ms:
            ml=m.lower()
            c[cat]+= tl.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b",tl))
    return c
def tok(t): return len(t.split())

reg=json.loads((G/"book_registry.json").read_text())["books"]
rows=[]
for cond,(folder,prefix,do_strip) in COND.items():
    for ab in sorted(reg):
        for i in range(1,16):
            qid=f"Q{i:02d}"; p=G/folder/f"{ab}_responses"/f"{prefix}_{qid}_{ab}.json"
            if not p.exists(): print("missing",p.name); continue
            reply=str(json.loads(p.read_text()).get("reply") or "")
            txt=reply; stripped=False
            if do_strip: txt,stripped=strip_suffix(reply)
            _,would=strip_suffix(reply)
            c=count(txt); t=tok(txt)
            craw=count(reply); traw=tok(reply)
            rows.append(dict(cond=cond,ab=ab,qid=qid,
                d1=c["D1"],d2=c["D2"],d3=c["D3"],d4=c["D4"],tokens=t,
                d123_per1k=(c["D1"]+c["D2"]+c["D3"])/t*1000 if t else 0,
                total_per1k=sum(c.values())/t*1000 if t else 0,
                d123_per1k_raw=(craw["D1"]+craw["D2"]+craw["D3"])/traw*1000 if traw else 0,
                total_per1k_raw=sum(craw.values())/traw*1000 if traw else 0,
                stripped=stripped,would_strip=would))
df=pd.DataFrame(rows)
df.to_csv(OUT/"per_response_4way.csv",index=False)

def test(col,x,y,alt="greater"):
    pv=df[df.cond.isin([x,y])].pivot_table(index=["ab","qid"],columns="cond",values=col).dropna()
    d=pv[x].values-pv[y].values
    if np.allclose(d,0): return None
    W,p=wilcoxon(d,alternative=alt)
    z=norm.ppf(1-min(max(min(p*2,1.0),1e-15),.999999)/2)
    return dict(n=len(d),mx=pv[x].mean(),my=pv[y].mean(),
        red=100*(pv[x].mean()-pv[y].mean())/pv[x].mean(),W=W,p=p,r=z/np.sqrt(len(d)))

L=[]
def say(s=""): print(s); L.append(s)
say("="*78); say("4-WAY ABLATION — full 10-book corpus, n=150 pairs/condition"); say("="*78)
say(f"rows={len(df)} | per cond={df.groupby('cond').size().to_dict()}")
a3q=int(df[df.cond=="A3"].would_strip.sum())
say(f"A3 replies ending in a routing-style question (NOT stripped; counted as content): {a3q}/150")
say("")
say("DECOMPOSITION — D1-D3 (suffix-independent basis), means per 1,000 tokens:")
for c in ["A1","A2","A3","B"]:
    say(f"   {c}: {df[df.cond==c].d123_per1k.mean():.3f}")
say("")
def line(lbl,x,y,col="d123_per1k",alt="greater"):
    t=test(col,x,y,alt)
    if not t: say(f"   {lbl}: (no variation)"); return
    say(f"   {lbl:<46s} {x}={t['mx']:5.2f} {y}={t['my']:5.2f}  {t['red']:+6.1f}%  "
        f"W={t['W']:7.1f} p={t['p']:.2e} r={t['r']:.3f}")
say("THE KEY QUESTION — does governance add anything over a strong scholarly prompt? (D1-D3)")
line("A2 vs A3  (bare prompt -> scholarly prompt)","A2","A3")
line("A3 vs B   (scholarly prompt -> governance, B stripped)","A3","B")
line("A3 vs B   (scholarly prompt -> governance, B RAW)","A3","B","d123_per1k_raw")
line("A2 vs B   (combined, for continuity)","A2","B")
say("")
say("Tier-1 total (D1-D4):")
line("A2 vs A3","A2","A3","total_per1k")
line("A3 vs B (B stripped)","A3","B","total_per1k")
line("A3 vs B (B RAW)","A3","B","total_per1k_raw")
say("")
say("Context:")
line("A1 vs A3  (Gemini vs scholarly-prompted gpt-4o-mini)","A1","A3")
line("A1 vs B   (Gemini vs governed)","A1","B")
(OUT/"results_ablation.txt").write_text("\n".join(L))
say(f"\n[written] {OUT/'results_ablation.txt'} and per_response_4way.csv")
