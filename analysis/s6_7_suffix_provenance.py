#!/usr/bin/env python3
"""
S6.7 — Provenance of the Cond_B follow-on question.

Established from the governance log plus the response corpus: the trailing
question in Cond_B is a GOVERNED behaviour with a logged, applied governance
action -- not an ungoverned platform artefact, as earlier drafts of this paper
described it. This section documents the evidence and what it changes.

Output: s6_7_suffix_provenance.md
"""
import csv, json, re, os
from pathlib import Path
from collections import Counter

G    = Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
log  = list(csv.DictReader(open(HERE/"governance_log_46.csv")))
reg  = json.loads((G/"book_registry.json").read_text())["books"]

src=(HERE/"s2_5_marker_counts.py").read_text()
ns={"__file__":str(HERE/"s2_5_marker_counts.py"),"__name__":"_r"}
exec(compile(src[:src.index("reg = json.loads")],"s","exec"),ns)
strip_suffix=ns["strip_suffix"]
ANCH=re.compile(r"chapter|act |scene|part |section|book |verse|lecture",re.I)

# ---- measure the behaviour
endq=caught=anchored=0; forms=Counter(); per_book={}
for ab in sorted(reg):
    n=0
    for i in range(1,16):
        rp=str(json.loads((G/"CondB_Governed_GPT4omini"/f"{ab}_responses"/f"CondB_Q{i:02d}_{ab}.json").read_text()).get("reply") or "").strip()
        if rp.endswith("?"): endq+=1
        if strip_suffix(rp)[1]: caught+=1; n+=1
        last=re.split(r'(?<=[.!?])\s+',rp)[-1]
        if last.endswith("?"):
            forms[" ".join(last.split()[:3]).lower()]+=1
            if ANCH.search(last): anchored+=1
    per_book[ab]=n
others={}
for cond,folder,pre in (("A1","CondA1_Gemini_2.5Flash","condA"),
                        ("A2","CondA2_Ungoverned_GPT4omini","CondA2"),
                        ("A3","CondA3_ScholarlyPrompt_GPT4omini","CondA3")):
    others[cond]=sum(1 for ab in sorted(reg) for i in range(1,16)
        if str(json.loads((G/folder/f"{ab}_responses"/f"{pre}_Q{i:02d}_{ab}.json").read_text()).get("reply") or "").strip().endswith("?"))

qf=[r for r in log if r["lever"]=="question_frequency"]
hb=[r for r in log if r["lever"]=="hard_boundary" and "follow-on" in r["to_value"].lower()]

L=[]; w=L.append
w("### S6.7 — Provenance of the Cond_B follow-on question\n")
w("> **This section corrects a claim made in earlier drafts of this paper.** The "
  "trailing question appended to Cond_B replies was described as an ungoverned "
  "platform artefact — \"the product surface wrapped around\" the governance "
  "layer. The governance log shows it is a **governed behaviour with a logged, "
  "applied governance action**. The correction is set out here and the "
  "consequences are carried into §2.6 and §3.4.\n")

w("#### The governance actions\n")
w("Two proposals, both **applied**, twenty-one minutes apart, both on "
  "*Nathan the Wise*:\n")
w("| Time (UTC) | Family / lever | Summary | from → to |")
w("|---|---|---|---|")
for r in sorted(qf+hb, key=lambda x:x["created"]):
    to=r["to_value"]
    w(f"| {r['created'][:16]} | {r['family']} / `{r['lever']}` | {r['summary']} | "
      f"`{r['from_value'] or '—'}` → {('`'+to+'`') if len(to)<40 else 'see below'} |")
w("")
w("The second proposal's full text, which is the operative instruction:\n")
w("> " + hb[0]["to_value"])
w("")
w("Two features of it matter. It is a **semantic specification** — append "
  "exactly one follow-on question, anchored in the book, tied to specific "
  "characters, exchanges or tensions. And it carries a **lexical prohibition** "
  "— *avoid generic phrases like 'Would you like to explore…' and "
  "therapy/coaching language*. The curator anticipated precisely the register "
  "failure the D4 category measures, and legislated against it.\n")

w("#### What the corpus shows\n")
w("| Measure | Cond_A1 | Cond_A2 | Cond_A3 | Cond_B |")
w("|---|---|---|---|---|")
w(f"| Replies ending in a question | {others['A1']}/150 | {others['A2']}/150 | "
  f"{others['A3']}/150 | **{endq}/150** |")
w("")
w(f"- **{endq}/150** Cond_B replies end in a follow-on question; "
  f"**{others['A2']}/150** in A2 and **{others['A3']}/150** in A3. The "
  "behaviour is unique to the governed condition.")
w(f"- **{anchored}/150 ({anchored/150*100:.0f}%)** of those questions carry an "
  "explicit structural anchor (chapter, act, part, lecture). "
  "**The semantic half of the instruction was followed.**")
w(f"- **{forms['would you like']}/150 ({forms['would you like']/150*100:.0f}%)** "
  "open with *\"Would you like…\"* — the phrase family the instruction "
  "explicitly forbade. **The lexical half was not followed.**\n")
w("Opening words of the final question, all 150 Cond_B replies:\n")
w("| Opening | n |")
w("|---|---|")
for k,v in forms.most_common(6): w(f"| *\"{k}…\"* | {v} |")
w("")
w("A representative instance, from a book with no logged follow-on rule of its "
  "own: *\"Would you like to **explore** how Franklin's discussion of his "
  "thirteen virtues in Chapter 10 supports this central argument?\"* — "
  "book-anchored exactly as instructed, and opening with the exact construction "
  "the instruction prohibited.\n")

w("#### The scope anomaly\n")
w(f"`question_frequency` is used **once** in the entire 46-proposal corpus log, "
  "and the follow-on `hard_boundary` likewise — both on *Nathan the Wise*. Yet "
  "the behaviour appears in all ten books:\n")
w("| Book | Suffix-matched replies |")
w("|---|---|")
for ab,b in sorted(reg.items(), key=lambda kv:kv[1]["title"]):
    mark=" ← the only book with a logged rule" if ab=="nw" else ""
    w(f"| {b['title']} | {per_book[ab]}/15{mark} |")
w("")
w("Two readings are consistent with the evidence available here, and this "
  "study cannot distinguish them: either the platform applies follow-on "
  "questions by default and the *Nathan the Wise* proposals tuned an existing "
  "behaviour, or a rule authored against one book propagated beyond its scope. "
  "**The second would be a governance-scoping defect of the same family as the "
  "misattributed packets in S6.6** — a rule taking effect somewhere its author "
  "did not intend — and it is resolvable only by inspecting the platform's "
  "serving configuration, not from the archived data. It should be resolved "
  "before publication, because the two readings support different claims about "
  "how precisely per-book governance is scoped.\n")

w("#### The stripping regexes are incomplete\n")
w(f"The seven documented patterns (S2.2) match **{caught}/150** replies. All "
  f"**{endq}/150** carry a follow-on question; the {endq-caught} missed cases "
  "use syntactic forms the patterns do not cover (*\"How does Du Bois's…\"*, "
  "*\"In what ways does…\"*). Consequences:\n")
w(f"1. The incidence figure reported as \"{caught}/150 (97%)\" is the **regex "
  f"match rate**, not the incidence of the behaviour, which is {endq}/150 "
  "(100%). Both are now stated.")
w(f"2. The \"stripped\" basis is not fully suffix-free: {endq-caught} follow-on "
  "questions survive into it, so part of Cond_B's residual D4 (16 markers) is "
  "un-stripped follow-on text rather than D4 in the body.")
w("3. The direction of this error is conservative for the governance claim — "
  "it leaves *more* D4 in the governed condition, not less.\n")

w("#### What this changes\n")
w("| Claim | Status |")
w("|---|---|")
for a,b_ in [
 ("D1–D3 headline (−42.9%) and every contrast on the primary composite",
  "**Unaffected.** 2 of 108 D1–D3 markers sit in suffix text (S2.5)."),
 ("D4 and Tier-1 figures as numbers","**Unaffected.** The counts are what they were."),
 ("\"The platform's interface re-introduces the chatty register\"",
  "**Wrong.** The curator asked for the behaviour through the governance system."),
 ("\"Governing a model is not the same as governing a product\"",
  "**Withdrawn.** This was not a product surface acting outside governance."),
 ("\"The curator has ten controls and none governs the suffix\"",
  "**Wrong.** Two of the ten govern it, and both were used."),
 ("Stripping justified as removing \"platform artefact, not response content\"",
  "**Re-justified.** It is governed content; stripping is defensible as "
  "separating generated prose from an appended template, which is a different "
  "argument and is now made explicitly (§2.6).")]:
    w(f"| {a} | {b_} |")
w("")
w("**The replacement finding is stronger than the one it displaces.** A curator "
  "specified a behaviour in two parts — *what to do* (append one book-anchored "
  f"question) and *what words not to use* (not \"Would you like to explore\"). "
  f"The system honoured the first in {anchored/150*100:.0f}% of replies and "
  f"violated the second in {forms['would you like']/150*100:.0f}%. "
  "Prompt-layer governance turns out to be reliable for semantic specification "
  "and unreliable for lexical prohibition, and the drift instrument detects "
  "exactly the half that failed. That is a finding about the limits of this "
  "class of intervention, measured rather than asserted, and it generalises "
  "beyond this platform: any governance scheme that works by instructing a "
  "model inherits it.\n")
w("It also explains the D4 result without appeal to an interface: Cond_B's raw "
  "D4 rate is high because the curator required a question after every "
  "substantive answer and the model wrote those questions in the register it "
  "defaults to. The governance did not fail to reach the surface — it reached "
  "it, and the surface was written in assistant-register anyway.\n")

(HERE/"s6_7_suffix_provenance.md").write_text("\n".join(L),encoding="utf-8")
print("\n".join(L))
