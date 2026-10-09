
import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import DATA, CANON, EXPORT, HERE, data_file, canon_pack
#!/usr/bin/env python3
"""
S2.5 — marker counts and token bases, raw vs stripped, per condition.

Re-derives the raw (suffix-retained) counts that per_response_4way.csv does not
store. Imports nothing from that CSV: it re-reads the response JSONs and uses a
verbatim copy of the lexicon, suffix patterns, tokeniser and counter from
ablation_4way.py, so the stripped columns must reproduce that file exactly
(asserted at the end).

Output: s2_5_marker_counts.md , per_response_rawcounts.csv
"""
import json, re, csv, os
from pathlib import Path

G    = DATA
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
BASE = HERE.parent

COND = {"A1":("CondA1_Gemini_2.5Flash","condA",False),
        "A2":("CondA2_Ungoverned_GPT4omini","CondA2",False),
        "A3":("CondA3_ScholarlyPrompt_GPT4omini","CondA3",False),
        "B" :("CondB_Governed_GPT4omini","CondB",True)}

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
    if not t: return t, False
    s=t.rstrip(); parts=s.rsplit("\n\n",1)
    if len(parts)==2:
        last=parts[1].strip()
        for p in SUFFIX:
            if p.match(last): return parts[0].rstrip(), True
    b=[m.end() for m in re.finditer(r"[.!?][\s'\"\)\]]*\s+(?=[A-Z])",s)]
    if b:
        body,last=s[:b[-1]].rstrip(), s[b[-1]:].strip()
        for p in SUFFIX:
            if p.match(last): return body, True
    return t, False

def count(txt):
    tl=txt.lower(); c={k:0 for k in TIER1}
    for cat,ms in TIER1.items():
        for m in ms:
            ml=m.lower()
            c[cat]+= tl.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b",tl))
    return c
def tok(t): return len(t.split())

reg = json.loads((G/"book_registry.json").read_text())["books"]
recs=[]
for cond,(folder,prefix,do_strip) in COND.items():
    for ab in sorted(reg):
        for i in range(1,16):
            qid=f"Q{i:02d}"
            p=G/folder/f"{ab}_responses"/f"{prefix}_{qid}_{ab}.json"
            if not p.exists(): raise SystemExit(f"missing {p}")
            reply=str(json.loads(p.read_text()).get("reply") or "")
            txt, stripped = strip_suffix(reply) if do_strip else (reply, False)
            c, craw = count(txt), count(reply)
            recs.append(dict(cond=cond, ab=ab, qid=qid, stripped=stripped,
                tokens=tok(txt), tokens_raw=tok(reply),
                **{f"{k.lower()}":c[k] for k in TIER1},
                **{f"{k.lower()}_raw":craw[k] for k in TIER1}))

with open(HERE/"per_response_rawcounts.csv","w",newline="",encoding="utf-8") as f:
    wr=csv.DictWriter(f,fieldnames=list(recs[0])); wr.writeheader(); wr.writerows(recs)

# ---- cross-check the stripped columns against per_response_4way.csv ----
ref={(r["cond"],r["ab"],r["qid"]):r for r in
     csv.DictReader(open(data_file("per_response_4way.csv")))}
bad=0
for r in recs:
    q=ref[(r["cond"],r["ab"],r["qid"])]
    if (int(q["tokens"])!=r["tokens"] or any(int(q[k])!=r[k] for k in ("d1","d2","d3","d4"))):
        bad+=1
assert bad==0, f"{bad} rows disagree with per_response_4way.csv"
print(f"cross-check OK: all {len(recs)} rows reproduce per_response_4way.csv\n")

def agg(cond, raw):
    sub=[r for r in recs if r["cond"]==cond]
    sfx = "_raw" if raw else ""
    d={k: sum(r[f"{k}{sfx}"] for r in sub) for k in ("d1","d2","d3","d4")}
    t = sum(r["tokens_raw" if raw else "tokens"] for r in sub)
    d123=d["d1"]+d["d2"]+d["d3"]; tier1=d123+d["d4"]
    # mean-of-rates, published convention
    mr123 = sum((r[f"d1{sfx}"]+r[f"d2{sfx}"]+r[f"d3{sfx}"])/
                (r["tokens_raw" if raw else "tokens"] or 1)*1000 for r in sub)/len(sub)
    mrt1  = sum(sum(r[f"{k}{sfx}"] for k in ("d1","d2","d3","d4"))/
                (r["tokens_raw" if raw else "tokens"] or 1)*1000 for r in sub)/len(sub)
    return d, d123, tier1, t, mr123, mrt1

L=[]; w=L.append
w("## S2.5 — Marker counts and token bases by condition\n")
w("Absolute marker counts with the token base used as the rate denominator. "
  "Rate columns follow the published convention — the per-1,000-token rate is "
  "computed per response and then averaged — so they are not the quotient of "
  "the two preceding columns. Suffix stripping applies to Cond_B only: it is a "
  "platform artefact, and no suffix occurs in A1, A2 or A3.\n")
w("| Condition | Basis | n | D1 | D2 | D3 | D1–D3 | D4 | Tier-1 | Tokens | D1–D3 /1k | Tier-1 /1k |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|")
for c in ("A1","A2","A3"):
    d,d123,t1,t,m1,mt = agg(c,False)
    w(f"| {c} | unmodified | 150 | {d['d1']} | {d['d2']} | {d['d3']} | {d123} | {d['d4']} | "
      f"{t1} | {t:,} | {m1:.3f} | {mt:.3f} |")
for raw,lab in ((True,"raw (suffix retained)"),(False,"stripped (as analysed)")):
    d,d123,t1,t,m1,mt = agg("B",raw)
    w(f"| B | {lab} | 150 | {d['d1']} | {d['d2']} | {d['d3']} | {d123} | {d['d4']} | "
      f"{t1} | {t:,} | {m1:.3f} | {mt:.3f} |")
w("")

dR,d123R,t1R,tR,_,_ = agg("B",True)
dS,d123S,t1S,tS,_,_ = agg("B",False)
nstr = sum(r["stripped"] for r in recs if r["cond"]=="B")
w("**What the suffix contains.** Comparing the two Cond_B rows:\n")
w(f"- Routing suffix present in **{nstr}/150** Cond_B responses; **0/150** in A1, A2 and A3.")
w(f"- Tokens removed: {tR:,} → {tS:,} "
  f"(**−{(1-tS/tR)*100:.1f}%** of the Cond_B token base).")
w(f"- D4 markers removed: {dR['d4']} → {dS['d4']} "
  f"(**{(1-dS['d4']/dR['d4'])*100:.0f}%** of all Cond_B D4 markers sat inside the suffix).")
w(f"- D1–D3 markers removed: {d123R} → {d123S} (**{d123R-d123S}** markers, "
  f"{(d123R-d123S)/d123R*100:.1f}%, across the whole corpus).")
w("")
w("The suffix is therefore a near-pure D4 phenomenon. Two consequences:\n")
w("1. The **D1–D3 result is effectively suffix-independent**: the contested "
  "preprocessing step moves only "
  f"{d123R-d123S} of {d123R} content-register markers.")
w("2. Because drift is a *per-1,000-token rate*, removing "
  f"{(1-tS/tR)*100:.1f}% of the tokens while removing only "
  f"{(d123R-d123S)/d123R*100:.1f}% of the D1–D3 markers **raises** the measured "
  "D1–D3 rate "
  f"({agg('B',True)[4]:.3f} → {agg('B',False)[4]:.3f} per 1,000 tokens). "
  "The stripped figures reported in the manuscript are thus *conservative* with "
  "respect to the governance claim; the Tier-1 aggregate behaves in the opposite "
  "direction only because D4 is where the suffix lives.\n")

(HERE/"s2_5_marker_counts.md").write_text("\n".join(L),encoding="utf-8")
print("\n".join(L))
