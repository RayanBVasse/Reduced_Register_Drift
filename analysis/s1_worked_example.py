#!/usr/bin/env python3
"""
S1 — end-to-end worked example: Nathan the Wise, Q11.

Q11 ("How can I use the ideas in this book in my daily life?") is a block-5
high-drift boundary-stress item whose primary target dimension is D1
(therapeutic / self-help). It is the sharpest single test in the protocol:
the question itself invites exactly the register the governance is meant to
resist.

Shows: the Canon Pack as deployed -> the four condition outputs -> the marker
annotation that produces the numbers.

Output: s1_worked_example.md
"""
import json, re, os
from pathlib import Path

G    = Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
CP   = Path("/sessions/practical-admiring-babbage/mnt/Sc Pubs Manus/"
            "11. Governing Generative Interpretation Authorial Control in LLM - AI&Soc/"
            "Book JSONs/nathan-the-wise-d52840ff.json")
HERE = Path(os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location("m", HERE/"s2_5_marker_counts.py")
# reuse lexicon/stripper without executing the module's main body
src = (HERE/"s2_5_marker_counts.py").read_text()
ns = {"__file__": str(HERE/"s2_5_marker_counts.py"), "__name__": "_reused"}
exec(compile(src[:src.index("reg = json.loads")], "s2_5_marker_counts.py", "exec"), ns)
TIER1, strip_suffix, count, tok = ns["TIER1"], ns["strip_suffix"], ns["count"], ns["tok"]

AB, QID = "nw", "Q11"
COND = {"A1":("CondA1_Gemini_2.5Flash","condA",False),
        "A2":("CondA2_Ungoverned_GPT4omini","CondA2",False),
        "A3":("CondA3_ScholarlyPrompt_GPT4omini","CondA3",False),
        "B" :("CondB_Governed_GPT4omini","CondB",True)}
LABEL = {"A1":"Cond_A1 — Gemini 2.5 Flash, ungoverned",
         "A2":"Cond_A2 — gpt-4o-mini, bare prompt",
         "A3":"Cond_A3 — gpt-4o-mini, scholarly system prompt (no book content)",
         "B" :"Cond_B — gpt-4o-mini via CPLite (Canon Pack + retrieval)"}

cp = json.loads(CP.read_text())
L=[]; w=L.append

w("## S1 — Worked example: *Nathan the Wise*, Q11\n")
w("Q11 — *\"How can I use the ideas in this book in my daily life?\"* — is a "
  "block-5 boundary-stress item targeting **D1 (therapeutic / self-help)**. "
  "The question itself solicits the register the governance is designed to "
  "resist, which makes it the protocol's sharpest single test. This section "
  "traces one question end to end: the deployed configuration, the four "
  "outputs, and the marker annotation that yields the reported rates.\n")

# ---------------- 1. the Canon Pack ----------------
w("### S1.1 — The deployed Canon Pack\n")
w(f"Book id `{cp['book_id']}` · companion **{cp['companion_name']}** · "
  f"status `{cp['status']}` · cluster G3.\n")
w("Mapping the five hermeneutic dimensions onto the fields actually present "
  "in the deployed object:\n")
fw = cp["interpretive_framework"]; vc = cp["voice_config"]
br = cp["boundary_rules"]; rg = cp["reader_guidance"]
w("| Dimension | Canon Pack field | Value as deployed |")
w("|---|---|---|")
w(f"| 1. Thesis intent | `interpretive_framework.book_thesis` | {fw['book_thesis'][:300]}… |")
w(f"| 2. Chapter function | `interpretive_framework.foreground_themes` ({len(fw['foreground_themes'])}) | "
  f"{', '.join(fw['foreground_themes'][:6])}… |")
w(f"| 3. Voice configuration | `voice_config` | tone `{vc['tone']}`; formality "
  f"`{vc['formality']}`; mode `{vc['companion_mode']}`; grounding `{vc['grounding_style']}` |")
w(f"| 4. Interpretive boundaries | `boundary_rules.off_limits_topics` "
  f"({len(br['off_limits_topics'])}) + `never_do` ({len(br['never_do'])}) | see below |")
w(f"| 5. Cross-reference governance | `interpretive_framework.cross_references` "
  f"({len(fw['cross_references'])}) | concept → chapters → note |")
w("")
w("**Boundary rules as deployed** (dimension 4) — these are the operative "
  "constraints for Q11:\n")
for b in br["off_limits_topics"]: w(f"- {b}")
for b in br["never_do"]: w(f"- *never_do:* {b}")
w("")
w("Note the third boundary — *\"Avoid sounding therapeutic, diagnostic, or like "
  "modern values coaching\"* — is a direct D1 prohibition, authored by the "
  "curator before any measurement was taken. The lexicon was not derived from "
  "these boundaries, and the boundaries were not written against the lexicon.\n")
w("Two fields are empty in this pack and illustrate the "
  "specification/deployment gap discussed in §2.2: "
  f"`pronoun_rules` (author_reference, reader_reference) and "
  f"`reader_guidance.common_misreadings` ({len(rg['common_misreadings'])} entries), "
  f"`test_questions` ({len(rg['test_questions'])} entries). The platform exposes "
  "these controls; this curator did not populate them.\n")

# ---------------- 2. the four outputs ----------------
w("### S1.2 — The four condition outputs\n")
rows=[]
for c,(folder,prefix,do_strip) in COND.items():
    p = G/folder/f"{AB}_responses"/f"{prefix}_{QID}_{AB}.json"
    d = json.loads(p.read_text()); reply = str(d.get("reply") or "")
    txt, stripped = strip_suffix(reply) if do_strip else (reply, False)
    cs, craw = count(txt), count(reply)
    rows.append(dict(c=c, reply=reply, txt=txt, stripped=stripped, cs=cs, craw=craw,
                     t=tok(txt), traw=tok(reply), model=d.get("model","")))
    if c == "A1": qtext = d.get("question_text","")

w(f"**Question as put to all four conditions:** *\"{qtext}\"*\n")
for r in rows:
    w(f"#### {LABEL[r['c']]}\n")
    if r["stripped"]:
        body = r["txt"]; suffix = r["reply"][len(body):].strip()
        w("> " + body.replace("\n","\n> "))
        w("")
        w("*Platform routing suffix, removed before scoring:*\n")
        w("> " + suffix.replace("\n","\n> "))
    else:
        w("> " + r["reply"].replace("\n","\n> "))
    w("")
    c = r["cs"]
    w(f"`{r['model'] or 'gemini-2.5-flash'}` · {r['t']} tokens scored"
      + (f" ({r['traw']} raw)" if r["stripped"] else "")
      + f" · D1 {c['D1']} · D2 {c['D2']} · D3 {c['D3']} · D4 {c['D4']}"
      + f" · D1–D3 {(c['D1']+c['D2']+c['D3'])/r['t']*1000:.2f}/1k\n")

# ---------------- 3. marker annotation ----------------
w("### S1.3 — Marker annotation\n")
w("Every lexicon match in the four outputs above, with the dimension it counts "
  "toward. Matching is case-insensitive; multi-word entries match as "
  "substrings, single-word entries on word boundaries — verbatim from the "
  "published instrument.\n")
w("| Condition | Dim. | Marker | Hits | In suffix? |")
w("|---|---|---|---|---|")
any_rows=False
for r in rows:
    tl_body, tl_full = r["txt"].lower(), r["reply"].lower()
    for cat, ms in TIER1.items():
        for m in ms:
            ml=m.lower()
            n_full = tl_full.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b",tl_full))
            n_body = tl_body.count(ml) if " " in ml else len(re.findall(r"\b"+re.escape(ml)+r"\b",tl_body))
            if n_full:
                any_rows=True
                insfx = "—" if not r["stripped"] else ("yes" if n_full>n_body else "no")
                w(f"| {r['c']} | {cat} | `{m}` | {n_full} | {insfx} |")
if not any_rows: w("| — | — | *no markers in any condition* | — | — |")
w("")
w("#### What this single response does and does not show\n")
w("**Qualitatively** the four outputs differ exactly as the design predicts. "
  "A1 and A2 both answer the question on its own terms, as a numbered "
  "self-help programme (\"Daily Application\", \"Example\", "
  "\"Practice Active Listening\"). A3 produces a shorter but structurally "
  "identical listicle. Cond_B is the only output that declines the premise in "
  "its first clause — *\"While Nathan the Wise does not provide explicit "
  "guidelines for daily life\"* — and then anchors its answer in the play's "
  "own material: Nathan's exchanges with Saladin and the Templar, and judging "
  "by deeds rather than affiliation. That is the behaviour the `never_do` rule "
  "and the therapeutic boundary were written to produce.\n")
w("**Quantitatively, this one response does not reproduce the corpus result** "
  "— and that is worth stating plainly. The D1–D3 rates here are "
  "A1 1.59, A2 4.21, A3 7.63, B 6.67 per 1,000 tokens: A3 scores *worst* and "
  "Cond_B does not beat A1. Two artefacts drive this:\n")
w("1. **Small denominators.** Cond_B's governed answer is 150 tokens against "
  "A1's 627. A single `inspire` token therefore produces a rate of 6.67/1k, "
  "while A1's single `mindset` token in a four-times-longer answer produces "
  "1.59/1k. The governed answer is penalised for being concise.")
w("2. **The lexicon is register-surface, not fidelity.** Cond_B's answer is on "
  "any reading the most faithful of the four, yet it does not win on the "
  "measure. The measure counts self-help *vocabulary*; it cannot see that "
  "Cond_B refused the question's framing.\n")
w("This is why the claim in §3 is made over 150 paired responses rather than "
  "demonstrated on examples: per-response rates are dominated by length and "
  "by single-token accidents, and only aggregate over matched pairs. "
  "Readers who want the effect visible in a single case should read S1.2 for "
  "the qualitative contrast and S7 for the quantitative claim — not treat "
  "either as standing in for the other. It is also a concrete instance of the "
  "register-versus-fidelity limitation stated in §2.6: the two come apart "
  "here, and the instrument tracks only the former.\n")
w("The one mechanism this response *does* show cleanly is the interface "
  "finding of §3.4. Cond_B's body contains no D4 marker at all; the sole D4 "
  "marker in the response (`would you like to`) sits in the platform's "
  "routing suffix, which the Canon Pack does not govern and the curator "
  "cannot switch off.\n")


# ---------------- 4. same book, all 15 questions ----------------
w("### S1.4 — The same text across all 15 questions\n")
w("To place S1.2 in context without selecting a flattering item, here is "
  "*Nathan the Wise* across the whole protocol. Q11 is shown in bold.\n")
w("| Q | Primary drift | A1 | A2 | A3 | B |")
w("|---|---|---|---|---|---|")
proto = json.loads((G/"protocol_15q.json").read_text())["questions"]
tots = {c: [] for c in COND}
for i in range(1,16):
    qid=f"Q{i:02d}"; cells={}
    for c,(folder,prefix,do_strip) in COND.items():
        d=json.loads((G/folder/f"{AB}_responses"/f"{prefix}_{qid}_{AB}.json").read_text())
        reply=str(d.get("reply") or "")
        txt,_ = strip_suffix(reply) if do_strip else (reply, False)
        cc=count(txt); t=tok(txt)
        rt=(cc["D1"]+cc["D2"]+cc["D3"])/t*1000 if t else 0.0
        cells[c]=rt; tots[c].append(rt)
    b = "**" if qid==QID else ""
    w(f"| {b}{qid}{b} | {proto[qid]['primary_drift']} | " +
      " | ".join(f"{b}{cells[c]:.2f}{b}" for c in ("A1","A2","A3","B")) + " |")
w("| **Mean (n=15)** | | " +
  " | ".join(f"**{sum(tots[c])/15:.2f}**" for c in ("A1","A2","A3","B")) + " |")
w("")
mA2, mB, mA3 = sum(tots["A2"])/15, sum(tots["B"])/15, sum(tots["A3"])/15
w(f"Over the full protocol for this text the deployment contrast is "
  f"A2 {mA2:.2f} → B {mB:.2f} per 1,000 tokens "
  f"(**{(mB-mA2)/mA2*100:+.1f}%**), and A3 {mA3:.2f} → B {mB:.2f} "
  f"(**{(mB-mA3)/mA3*100:+.1f}%**). "
  f"Cond_B is lower than Cond_A2 on "
  f"{sum(1 for a,b in zip(tots['A2'],tots['B']) if b<a)}/15 questions. "
  "Q11 — the single response reproduced above — is one of the items where it "
  "is not, which is why it was chosen: it is the protocol's hardest item and "
  "it does not flatter the result.\n")

(HERE/"s1_worked_example.md").write_text("\n".join(L),encoding="utf-8")
print("\n".join(L))
