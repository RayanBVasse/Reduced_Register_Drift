#!/usr/bin/env python3
"""S3 (system & controls), S6.1/6.3/6.4/6.5 (governance log), S2.4 (A3 prompt), S8 (manifest)."""
import json, csv, os, glob
from pathlib import Path
from collections import Counter, defaultdict
import statistics as st, datetime as dt

G    = Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
CP   = Path("/sessions/practical-admiring-babbage/mnt/Sc Pubs Manus/"
            "11. Governing Generative Interpretation Authorial Control in LLM - AI&Soc/"
            "Book JSONs/nathan-the-wise-d52840ff.json")
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
TODO = "> **[NEEDS AUTHOR INPUT]**"

log = list(csv.DictReader(open(HERE/"governance_log_46.csv")))
L=[]; w=L.append

# =============================================== S2.4
w("### S2.4 — The Cond_A3 scholarly instruction, in full\n")
w("The ablation condition's system prompt. The book title and author are "
  "interpolated per book; nothing else varies. Cond_A3 receives **no book "
  "content** — no pack, no retrieval, no chapter text — so any improvement "
  "over Cond_A2 is attributable to the instruction alone.\n")
a3 = json.loads(Path(sorted(glob.glob(str(G/"CondA3_ScholarlyPrompt_GPT4omini"/"nw_responses"/"*.json")))[0]).read_text())
w("```text")
for line in a3["system_prompt"].split("\n"): w(line)
w("```")
w("")
w(f"Served at temperature **{a3.get('temperature')}** to "
  f"`{a3.get('model')}` (returned `{a3.get('model_version_returned')}`).\n")
w("The instruction was written to be a *strong* baseline, not a straw man: it "
  "names the four register failures the lexicon measures (self-help, "
  "therapeutic, motivational, productivity), forbids appended reflective "
  "prompts, and demands doctrinal specificity. It is deliberately the best "
  "prompt-only intervention we could write, because the question it exists to "
  "answer is whether structured governance adds anything beyond one.\n")
w("Its one structural disadvantage is that it cannot name book-specific "
  "distortions: it says \"do not translate into self-help language\" where a "
  "Canon Pack says \"do not present this play as generic interfaith "
  "inspiration.\" Whether that difference is detectable is exactly what §3.2 "
  "tests, and on this measure it is not.\n")

# =============================================== S3
w("## S3 — System and controls\n")
w("### S3.1 — Pipeline\n")
w("Six stages, as described in §2.3. The diagram below is the normative "
  "reference; a rendered figure is supplied separately.\n")
w("```")
w("  (1) PARSE        source text --> chapter-segmented document")
w("       |")
w("  (2) CHUNK        sentence-aware, 512 tokens, 64-token overlap,")
w("       |           never crossing a chapter boundary")
w("  (3) EMBED        --> book-specific vector namespace")
w("       |")
w("  (4) GENERATE     AI-drafted Canon Pack  --> curator review --> accepted pack")
w("       |                                        ^")
w("  (5) RENDER       pack --> system prompt        |  3A governance loop")
w("       |                                        |  (propose / preview / apply)")
w("  (6) SERVE        system prompt + retrieval ----+")
w("                   --> reader-facing companion")
w("```")
w("")
w("Rendered as **Figure S6** (`Figure_S6_pipeline.png` / `.tiff`, 300 dpi). "
  "The ASCII reference above is retained because it is the normative "
  "description and survives copy-paste into plain-text contexts.\n")

w("### S3.2 — The ten controls\n")
w("Grouped by family, as exercised in the governance log. `Uses` is the "
  "number of proposals in the 46-proposal log that moved that control.\n")
uses = Counter(r["lever"] for r in log)
CONTROLS = [
 ("CB","warmth","Affective register of the companion's voice","enum (e.g. analytical_clear, reflective_calm, warm_accessible)"),
 ("CB","directness","How directly the companion states a position","enum"),
 ("CB","interpretive_depth","How far the companion elaborates beyond the literal","enum"),
 ("CB","question_frequency","How often the companion puts questions to the reader","enum"),
 ("SB","topic_scope","How tightly answers must anchor to the book","enum (implicit_reference / explicit_anchor)"),
 ("SB","hard_boundary","Free-text prohibitions injected into the prompt","list of strings"),
 ("SB","redirect_firmness","How firmly off-topic readers are redirected","enum (e.g. gentle / firm)"),
 ("BK","author_guidance","Free-text framing of how the book should be read","string"),
 ("BK","chapter_emphasis","Per-chapter weighting for retrieval and emphasis","map chapter -> weight"),
 ("BK","concept_refresh","Re-derivation of the pack's concept/cross-reference set","action"),
]
FAM={"CB":"Companion behaviour","SB":"Scope and boundary","BK":"Book knowledge"}
w("| Family | Control | What it governs | Value type | Uses |")
w("|---|---|---|---|---|")
for fam,lev,desc,typ in CONTROLS:
    w(f"| {FAM[fam]} ({fam}) | `{lev}` | {desc} | {typ} | {uses.get(lev,0)} |")
w("")
w(f"All ten controls were exercised at least once across the ten texts "
  f"({sum(uses.values())} proposals total). Two write to the stored book "
  "representation (`author_guidance`, `hard_boundary`); the remaining eight "
  "are read directly from the governance packets by the runtime — a "
  "distinction that matters for S6.6.\n")
w("**Per-book lever quotas.** The Author Control Room caps the number of "
  "governance actions per book per family, displayed to the curator as a "
  "running count (`n/10 CB · n/6 BK · n/4 SB`). The caps are a platform "
  "feature, not a study design choice, and they bound what the governance log "
  "in S6 could in principle contain.\n")
_CAP={"CB":10,"BK":6,"SB":4}
_per=defaultdict(Counter)
for r in log: _per[r["book"]][r["family"]]+=1
w("| Family | Cap per book | Maximum observed in any book | Books reaching the cap |")
w("|---|---|---|---|")
for f,cap in _CAP.items():
    mx=max(_per[b][f] for b in _per); at=sum(1 for b in _per if _per[b][f]>=cap)
    w(f"| {f} | {cap} | {mx} ({max(_per, key=lambda b:_per[b][f])[:34]}) | {at} |")
w("")
w("**No cap was reached on any book in any family.** The closest approach is "
  f"{max(_per[b]['CB'] for b in _per)} of 10 Companion-Behaviour actions on "
  "*Meditations*, and one book sits one below the Scope/Boundary cap. The "
  "distribution of proposals across families reported in §3.6 and S6.3 is "
  "therefore the curator's allocation of effort, **not an interface ceiling**. "
  "We state this because a reader who sees the quota counters in the interface "
  "would otherwise be right to ask whether the family shares are an artefact "
  "of the caps. They are not. A weaker caveat does survive: the counters are "
  "visible while governing, so a curator may ration actions in anticipation of "
  "a cap they never reach, and nothing in the log would show that.\n")

w("### S3.3 — CPLite interface\n")
w("Screenshots are the only items in this supplement that cannot be generated "
  "from the archived data. Those marked **NW** are captures of *Nathan the "
  "Wise* — the S1 worked example and a corpus text — so the interface figures "
  "and the worked example document the same book.\n")
w("| # | Screen | Book | What it evidences |")
w("|---|---|---|---|")
for n,(sc,bk,ev) in enumerate([
 ("Author intake","**NW**","Manuscript upload, the curator's free-text intake "
  "notes, rights confirmation, and the staged processing pipeline (parse → "
  "chapter structure → concepts and claims → QC) — stages 1–4 of Figure S6. "
  "The Project ID shown is `d52840ff-…`, which is the `book_id` of the "
  "deployed Canon Pack reproduced in S1.1."),
 ("Canon draft review","—","The four Agent-1 drafts (Structure, Key Ideas, "
  "Claims, QC) with per-draft download and re-upload, plus the review "
  "co-pilot — the curator-review step inside stage 4"),
 ("Fidelity and permitted moves","**NW**","`interpretive_depth` as three "
  "fidelity levels, and the editable *What the AI may do* list with per-line "
  "use/omit toggles — the `reader_guidance.suggested_entry_points` of S1.1"),
 ("Boundaries","**NW**","*What the AI should avoid* as six editable lines. "
  "These are verbatim the `boundary_rules.off_limits_topics` of the deployed "
  "pack in S1.1, including the therapeutic prohibition that §3.2 and S1 "
  "discuss"),
 ("Tone and grounding","—","`warmth` (primary tone) and `directness` as "
  "separate settings, and `topic_scope` as three grounding levels"),
 ("Go-live","—","Companion naming, welcome message, and the choice between "
  "fast-track publication and opening the Author Control Room to iterate with "
  "3A before readers see anything"),
 ("Author Control Room — Tuning","—","The governance surface: **Consult 3A**; "
  "the **A/B Preview / History / Reference / Testing & Caps** tabs; the *Tune "
  "your companion* dialogue with its free-text complaint box and **Send to "
  "3A**; the per-book lever quota counters; and live operations (reader "
  "counts, feedback, turn usage)"),
 ("Author Control Room — History","**NW**","Two applied governance actions "
  "rendered as `from → to` diffs under author-facing family headings (*What "
  "it can talk about*, *Voice & Tone*). Both match entries in the S6.2 log by "
  "verbatim summary text; both are the follow-on-question rules analysed in "
  "**S6.7**")],1):
    w(f"| {n} | {sc} | {bk} | {ev} |")
w("")
w("**What these establish beyond illustration.** Three things that would "
  "otherwise rest on assertion:\n")
w("1. **The author-facing labels differ from the internal lever names.** "
  "\"How closely should the AI stay to the exact meaning of your book?\" is "
  "`interpretive_depth`; \"How explicitly should the AI stay tied to the "
  "book?\" is `topic_scope`; the tone block is `warmth` and `directness`. A "
  "reader comparing S3.2 with the interface would otherwise find two "
  "vocabularies and no bridge.")
w("2. **The deployed pack is what the interface produced.** The intake "
  "screen's Project ID is the pack's `book_id`, and the six boundary lines in "
  "the review screen are the six `off_limits_topics` in the pack JSON. The "
  "chain from intake notes to deployed object is visible end to end.")
w("3. **The governance log records a dialogue, not direct parameter edits.** "
  "The curator types an unstructured symptom (\"Describe what feels off — "
  "e.g. \u2018It sounds too cold\u2019\"); the structured "
  "`lever` / `from_value` / `to_value` triple is the *system's* proposal in "
  "response. The History tab then renders the applied result as a diff. This "
  "is the provenance of the `curator_complaint` column in S6.2.\n")
w(TODO + " **one capture is still missing: a populated A/B preview.** "
  "Screenshot 7 shows that pane in its empty state (*\"No proposed change "
  "yet\"*), and screenshot 8 shows the *outcome* of two proposals as diffs, "
  "but neither shows the before/after response pair the curator actually "
  "compared before deciding. Twenty-one of the 46 proposals carry a stored "
  "preview, so a real one can be opened rather than staged. Until then §3.6 "
  "and S6 describe a preview step the reader is told about but never sees. "
  "Two smaller points: the modal in screenshot 7 overlays the right of the "
  "Tuning panel, and screenshots 2, 5, 6 and 7 are of a book outside the "
  "corpus — recapturing those on *Nathan the Wise* would make the whole "
  "section single-book.\n")

w("### S3.4 — Canon Pack schema\n")
cp = json.loads(CP.read_text())
def shape(o, pre="", depth=0):
    out=[]
    if isinstance(o, dict):
        for k,v in o.items():
            if isinstance(v, dict):
                out.append(f"{pre}{k}: object"); out += shape(v, pre+"  ", depth+1)
            elif isinstance(v, list):
                inner = "object" if (v and isinstance(v[0], dict)) else "string"
                out.append(f"{pre}{k}: array<{inner}>")
                if v and isinstance(v[0], dict):
                    out += shape(v[0], pre+"  ", depth+1)
            else:
                out.append(f"{pre}{k}: {type(v).__name__}")
    return out
w("Structure of the deployed pack object, from the *Nathan the Wise* "
  "instance (S1.1). Field names are verbatim.\n")
w("```yaml")
for line in shape(cp): w(line)
w("```")
w("")
w("### S3.5 — Retrieval configuration\n")
w("| Parameter | Value |")
w("|---|---|")
for k,v in [("Chunking","sentence-aware, never crossing a chapter boundary"),
            ("Chunk size","512 tokens"),("Chunk overlap","64 tokens"),
            ("Namespace","one vector namespace per book"),
            ("Scope","retrieval restricted to the book's own namespace"),
            ("Weights","unmodified — governance is prompt- and retrieval-layer only"),
            ("Training use","none; book text is never used as training data")]:
    w(f"| {k} | {v} |")
w("")
w("The last two rows are the legally consequential ones: because no weights "
  "are modified and no text is retained for training, deploying a governed "
  "companion over an in-copyright or estate-held work requires no grant of "
  "training rights (§2.3).\n")

w("### S3.6 — Dimension → control mapping, with gaps\n")
w("Reproduced from §2.2 for reference, with the log evidence attached.\n")
w("| Framework dimension | Operationalized as | Mapping fidelity | Log uses |")
w("|---|---|---|---|")
MAP=[("Thesis intent","system-prompt content (book thesis field); `author_guidance`",
      "Direct, but realised as prompt text rather than a distinct control",["author_guidance"]),
     ("Chapter-level function","`chapter_emphasis`, `concept_refresh`",
      "Partial — encoded in the pack, only partly exposed as a lever",["chapter_emphasis","concept_refresh"]),
     ("Voice configuration","`warmth`, `directness`, `interpretive_depth`, `question_frequency`",
      "Direct and well covered",["warmth","directness","interpretive_depth","question_frequency"]),
     ("Interpretive boundaries","`hard_boundary`, `topic_scope`, `redirect_firmness`",
      "Direct",["hard_boundary","topic_scope","redirect_firmness"]),
     ("Cross-reference governance","*(not exposed as a control)*",
      "**Not operationalized** — encoded in the pack, no curator-facing lever",[])]
for dim, op, fid, levs in MAP:
    n = sum(uses.get(l,0) for l in levs)
    w(f"| {dim} | {op} | {fid} | {n if levs else '—'} |")
w("")
w("The log confirms the gap empirically: cross-reference governance attracted "
  "**zero** proposals across ten texts, because there is no surface through "
  "which to make one. The *Nathan the Wise* pack carries nine populated "
  "cross-references (S1.1) that the curator could not subsequently adjust.\n")

# =============================================== S6
w("## S6 — Governance log\n")
w("### S6.1 — Scope and coding scheme\n")
w("The platform hosts governed companions beyond this study. The raw export "
  "covers **59 proposals across 12 books**; the two books that are not "
  "public-domain canonical texts fall outside the study corpus and are "
  "excluded, leaving the **46 proposals across the ten corpus texts** "
  "analysed here and in §3.6. Corpus membership is defined by "
  "`book_registry.json`, and the extraction script filters against that "
  "registry rather than against a hard-coded list, so the corpus cannot "
  "silently diverge between the data and the analysis.\n")
w("| Field | Meaning |")
w("|---|---|")
for k,v in [("`family`","CB / SB / BK — the lever family (S3.2)"),
            ("`lever`","which of the ten controls the proposal moves"),
            ("`status`","`applied` or `rejected`; `proposed` / `previewing` = undecided"),
            ("`from_value` → `to_value`","the exact parameter change requested"),
            ("`created`","timestamp, used for the burst analysis in S6.5"),
            ("`curator_complaint`","the curator's own first statement of the problem"),
            ("`has_ab_preview`","whether a stored A/B preview accompanies the proposal")]:
    w(f"| {k} | {v} |")
w("")
sc = Counter(r["status"] for r in log)
w(f"Status mix for the 46: **applied {sc['applied']}, rejected {sc['rejected']}**, "
  "with **no undecided proposals** — all four in-flight proposals in the raw "
  "export belong to the two excluded books. Acceptance rate is therefore "
  f"{sc['applied']}/{sc['applied']+sc['rejected']} = "
  f"**{sc['applied']/(sc['applied']+sc['rejected'])*100:.1f}%** with no "
  "denominator ambiguity.\n")
w(f"{sum(r['has_ab_preview']=='True' for r in log)} of the 46 carry a stored "
  "A/B preview pair (the before/after responses the curator saw before "
  "deciding). These are the raw material for a future fidelity study, since "
  "they are matched pairs differing by exactly one governance parameter.\n")

w("### S6.3 — Lever usage by cluster\n")
w("| Lever | Family | G1 | G2 | G3 | Total |")
w("|---|---|---|---|---|---|")
byl = defaultdict(lambda: Counter())
for r in log: byl[r["lever"]][r["cluster"]] += 1
for lev,_ in uses.most_common():
    c = byl[lev]; fam = next(r["family"] for r in log if r["lever"]==lev)
    w(f"| `{lev}` | {fam} | {c['G1']} | {c['G2']} | {c['G3']} | {sum(c.values())} |")
tc = Counter(r["cluster"] for r in log)
w(f"| **Total** | | **{tc['G1']}** | **{tc['G2']}** | **{tc['G3']}** | **{len(log)}** |")
w("")
w(f"`warmth` alone accounts for {uses['warmth']}/{len(log)} "
  f"({uses['warmth']/len(log)*100:.0f}%) of all proposals and "
  f"{uses['warmth']}/{sum(1 for r in log if r['family']=='CB')} "
  "of the Companion-Behaviour family. The single most common governance act "
  "across the corpus is adjusting the companion's affective register — which "
  "is precisely the D1/D4 territory the instrument measures.\n")

w("### S6.4 — Applied rate by family and cluster\n")
w("| Grouping | n | Applied | Rejected | Applied rate |")
w("|---|---|---|---|---|")
def blk(title, keyf, keys):
    w(f"| **{title}** | | | | |")
    for k in keys:
        s=[r for r in log if keyf(r)==k]
        a=sum(r["status"]=="applied" for r in s); rj=len(s)-a
        w(f"| {k} | {len(s)} | {a} | {rj} | {a/len(s)*100:.1f}% |")
blk("By lever family", lambda r:r["family"], ["CB","SB","BK"])
blk("By genre cluster", lambda r:r["cluster"], ["G1","G2","G3"])
w(f"| **All** | {len(log)} | {sc['applied']} | {sc['rejected']} | "
  f"{sc['applied']/len(log)*100:.1f}% |")
w("")
w("Companion-Behaviour proposals are accepted least often "
  f"({sum(1 for r in log if r['family']=='CB' and r['status']=='applied')}/"
  f"{sum(1 for r in log if r['family']=='CB')}) and raised most often: the "
  "curator experimented repeatedly with voice and discarded most attempts, "
  "while scope and book-knowledge corrections were usually kept. With 10–22 "
  "proposals per cell these are descriptive patterns, not statistical claims.\n")

w("### S6.5 — Proposal timing and bursts\n")
w("A *burst* is ≥2 proposals on one book separated by ≤60 minutes — the "
  "signature of a curator iterating to converge on a fix rather than making "
  "one considered change.\n")
import re as _re
def parse_ts(v):
    """ISO-8601 with an arbitrary-length fractional second (the export emits 5
    digits, which datetime.fromisoformat rejects before Python 3.11)."""
    v = _re.sub(r"\.(\d+)", lambda m: "." + m.group(1)[:6].ljust(6, "0"), v.strip())
    return dt.datetime.fromisoformat(v)

ts = defaultdict(list); unparsed = 0
for r in log:
    try: ts[r["book"]].append(parse_ts(r["created"]))
    except Exception: unparsed += 1
assert unparsed == 0, f"{unparsed} unparseable timestamps"
assert sum(len(v) for v in ts.values()) == len(log)
w("| Book | Cluster | n | Span (h) | Median gap (min) | Bursts |")
w("|---|---|---|---|---|---|")
_bursts = {}
for book in sorted(ts, key=lambda b:(-len(ts[b]), b)):
    t=sorted(ts[book]); cl=next(r["cluster"] for r in log if r["book"]==book)
    if len(t)<2:
        _bursts[book]=0; w(f"| {book} | {cl} | {len(t)} | 0.0 | — | 0 |"); continue
    gaps=[(b-a).total_seconds()/60 for a,b in zip(t,t[1:])]
    nb=0; run=1
    for g in gaps:
        if g<=60: run+=1
        else:
            if run>=2: nb+=1
            run=1
    if run>=2: nb+=1
    _bursts[book]=nb
    w(f"| {book} | {cl} | {len(t)} | {(t[-1]-t[0]).total_seconds()/3600:.1f} | "
      f"{st.median(gaps):.1f} | {nb} |")
w("")
_n = {b: len(v) for b, v in ts.items()}
_hi = max(_n, key=lambda b: _n[b]); _lo = min(_n, key=lambda b: _n[b])
w(f"| **Total** | | **{sum(_n.values())}** | | | **{sum(_bursts.values())} "
  f"bursts across {sum(1 for v in _bursts.values() if v)} books** |")
w("")
w(f"Governance is bursty and uneven: *{_hi}* drew {_n[_hi]} proposals while "
  f"*{_lo}* drew {_n[_lo]}. Effort tracks the curator's dissatisfaction with "
  "particular companions rather than the length or difficulty of the text — "
  "*Meditations* and *Art of War* are among the shortest texts in the corpus "
  "and attracted the most governance.\n")
w("Two timing caveats. The median gap is computed only over consecutive "
  "proposals on the same book, so books with two proposals have a single "
  "interval and no meaningful median. And the spans conflate working sessions "
  "with calendar time: *The Souls of Black Folk* shows a 295-hour span "
  "because two sessions sit twelve days apart, not because any proposal took "
  "twelve days.\n")

w("### S6.6 — Two misattributed packets (data integrity)\n")
w("Reported because it is a finding about curator-governed deployment, not "
  "merely an erratum.\n")
bad=[r for r in log if "Sun Tzu" in r["to_value"]]
w("Two `hard_boundary` packets logged against *The Confessions of St. "
  "Augustine* contain *Art of War* content:\n")
for r in bad:
    w(f"- `{r['proposal_id'][:8]}` · {r['created'][:19]} · status "
      f"`{r['status']}` — to_value: \"{r['to_value'][:170]}…\"")
w("")
w("Both are marked `applied`. The platform's own representation-divergence "
  "check reports that **neither reached the live book representation**: "
  "Augustine's deployed boundary list contains six Augustine-appropriate "
  "rules and no Sun Tzu text. The Cond_B responses for Augustine were "
  "therefore generated from the correct configuration.\n")
w("The timestamps explain the cause. Both were created on 20 April 2026 "
  "between 13:14 and 13:24; an *Art of War* `chapter_emphasis` proposal "
  "referencing \"Chapter III: Attack by Stratagem\" was created at 13:27. The "
  "curator was composing Art of War boundaries while the Augustine project "
  "was the active context. The correct Art of War `hard_boundary` was "
  "authored two days later, on 22 April.\n")
w("Three things follow, and the paper should say all three:\n")
w("1. **The log overstates effective applications by two.** 26 proposals are "
  "marked applied; 24 took effect. §3.6's rates are reported on the log as "
  "recorded, with this note attached.")
w("2. **A dual-write safeguard caught it.** Because `hard_boundary` writes to "
  "the stored book representation through a patch function, the divergence was "
  "detectable after the fact. The eight controls read directly from the "
  "packets have no equivalent cross-check, so an analogous error in those "
  "would be silent.")
w("3. **The interface permitted a cross-book error at all.** A curator "
  "managing ten companions can write one book's boundary into another's "
  "configuration with no confirmation step. That is a usability finding about "
  "multi-text governance, and it is the kind of failure that scales badly: it "
  "would be invisible to the reader and, absent this check, to the curator.\n")

# =============================================== S8
REPO = "https://github.com/RayanBVasse/Reduced_Register_Drift"
LIC  = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
w("## S8 — Open materials manifest\n")
w("### S8.1 — Repository and licence\n")
w(f"**Repository:** <{REPO}> (public)  \n**Licence:** {LIC}\n")
w("The repository currently hosts the *predecessor* three-condition study. It "
  "**must be updated before submission**: as published it does not contain "
  "the ablation condition, and its README describes a corpus and a lexicon "
  "that this paper supersedes. The table separates what is already there from "
  "what has to be added.\n")
w("| Item | Status in the repository |")
w("|---|---|")
present=[("`book_registry.json` — the ten texts, clusters, companions","present"),
 ("`protocol_15q.json` — the 15 questions (S5)","present"),
 ("`CondA1_…`, `CondA2_…`, `CondB_…` — 450 response JSONs","present"),
 ("`drift_reduction_3way.py` — the published three-way analysis","present"),
 ("`hermeneutics-export-…` — the raw 3A governance export","present"),
 ("`3way_drift_results/` — published statistics and per-book tables","present")]
toadd=[("`CondA3_ScholarlyPrompt_GPT4omini/` — **150 ablation response JSONs**","**missing — must be added**"),
 ("`ablation_4way.py` — the four-condition analysis","**missing — must be added**"),
 ("`per_response_4way.csv` — 600 scored responses","**missing — must be added**"),
 ("`per_response_rawcounts.csv` — raw + stripped marker counts (S2.5)","**missing — must be added**"),
 ("`governance_log_46.csv` — the corpus-filtered governance log (S6.2)","**missing — must be added**"),
 ("Supplement generation scripts — regenerate every table here","**missing — must be added**"),
 ("Figure generation script and figure files","**missing — must be added**"),
 ("Canon Pack JSON for each of the ten texts","**missing — must be added**"),
 ("Biber feature matrix — 450 responses × 71 features","**missing — optional; not analysed here**")]
fix=[("`per_response.csv` in `3way_drift_results/` — stale 8-book partial run (350 rows)","**must be replaced**"),
 ("`README.md` — states \"450 response pairs across 3 conditions\" and a \"43-marker\" lexicon","**must be corrected** to 600 / 4 conditions / 45 unique markers (S2.1)"),
 ("`Documents/_Book-Series/_Website-LL.org/LL.org/gna/` — three HTML files unrelated to this study","**should be removed** (see note below)")]
for a,b_ in present+toadd+fix: w(f"| {a} | {b_} |")
w("")
w("**Two housekeeping notes on the repository.**\n")
w("1. The directory `Documents/_Book-Series/_Website-LL.org/LL.org/gna/` "
  "contains three HTML files (`grant_sris.html`, `kashdan_eg.html`, "
  "`mclean_ni.html`) that belong to a separate book-and-tooling project and "
  "have nothing to do with this study. They should be removed: they undercut "
  "the claim that the repository reproduces the paper and nothing else, and "
  "— since the filenames correspond to published psychometric instruments — "
  "their licensing should be checked before anything in this repository is "
  "released under CC BY 4.0.")
w("2. No release has been published, so no archival snapshot of the code and "
  "data exists yet. See S8.3.\n")

w("### S8.2 — Reproduction\n")
w("```bash")
w("# 1. the headline and ablation figures")
w("python ablation_4way.py              # -> per_response_4way.csv, results_ablation.txt")
w("# 2. every table in this supplement")
w("python s2_5_marker_counts.py         # S2.5  (also cross-checks step 1)")
w("python s2_1_lexicon.py               # S2.1, S2.2 + lexicon sensitivity")
w("python s1_worked_example.py          # S1")
w("python extract_governance_log.py     # S6.2 + integrity check")
w("python build_supplement_tables.py    # S4, S5, S7.1-S7.5")
w("python s7_6_thread_and_retrieval.py  # S7.6, S7.7")
w("python build_s3_s6_s8.py             # S2.4, S3, S6.1/6.3-6.6, S8")
w("python assemble.py                   # -> SUPPLEMENT.md")
w("python verify.py                     # assertions against the published figures")
w("# 3. figures")
w("python make_figures.py               # PNG + TIFF at 300 dpi")
w("```")
w("")
w("Requires Python 3.11+, `scipy`, `pandas`, `matplotlib`. No API keys and no "
  "network access: all 600 responses are archived, so every number and figure "
  "in the paper regenerates offline. Regenerating the *responses* requires an "
  "OpenAI key (A2, A3, B) and a Gemini key (A1) and will not reproduce them "
  "exactly — Cond_B runs at temperature 0.4 and neither provider freezes its "
  "models.\n")
w("Note on Python version: the governance export encodes timestamps with "
  "five-digit fractional seconds, which `datetime.fromisoformat` rejects "
  "before 3.11. The extraction script normalises them; a naive parse silently "
  "drops three of the 46 proposals.\n")

w("### S8.3 — Archival deposit\n")
w("| | |")
w("|---|---|")
w("| Predecessor preprint | [10.5281/zenodo.20133666](https://doi.org/10.5281/zenodo.20133666) — *Authorial Governance Reduces Register Drift in LLM Reading Companions: A Matched-Model Study Across 10 Canonical Texts* (deposited 12 May 2026, CC BY 4.0) |")
w("| Archival deposit of code and data for **this** paper | **not yet created** |")
w("")
w(TODO + " a Zenodo deposit for the *materials*. The DOI above resolves to a "
  "record containing two PDFs — the predecessor manuscript and its "
  "appendices. It is a **preprint** deposit, not a data or software deposit, "
  "and citing it as the archived release of the open materials would "
  "misdescribe it. It should be cited in the references as the predecessor "
  "study, which is a different role.\n")
w("The materials deposit should be made after the repository updates listed "
  "in S8.1, by tagging a GitHub release with the Zenodo integration enabled, "
  "which mints a software DOI automatically. This matters more than usual "
  "here: the platform remains in active use, so the governance log will keep "
  "growing, and an unpinned repository URL would not let a reader recover the "
  "46-proposal state analysed in this paper.\n")

(HERE/"s3_s6_s8.md").write_text("\n".join(L),encoding="utf-8")
print("wrote s3_s6_s8.md —", len(L), "lines")
