# Interpretive Governance of AI Reading Companions

Data, analysis code and materials for a curator-governed deployment of the Canon Pack framework
across ten public-domain canonical texts.

**Licence:** CC BY 4.0

---

## What this study found

When a general-purpose language model is asked to explain a book, it tends to answer in the
register of contemporary self-improvement regardless of what the book is. This repository
contains a four-condition test of whether a book-specific governance layer changes that, and by
how much.

**Governance works.** Against the bare-prompt default a reader encounters today, the governed
companion reduced content-register markers (therapeutic, productivity, doctrinal-flattening) from
**7.52 to 3.89 per 1,000 tokens — a 48.3% reduction** (n = 150 paired, p = 1.4 × 10⁻¹¹, r = 0.55),
in the same direction in all ten books, computed on complete unmodified response text.

**But a strong generic prompt does most of that work.** A prompt-only ablation with no
book-specific content reached 4.56, and the additional difference between generic instruction and
book-specific governance was **not statistically detectable** (−14.5%, p = 0.11). The result is
deflationary about mechanism: the Canon Pack is not shown here to be a novel form of model
control. Its contribution is infrastructural — making expert interpretive instruction persistent,
inspectable, book-specific, and available to readers who cannot write it themselves.

**Whether book-specific governance improves interpretive *fidelity*, as distinct from register,
is untested.** The instrument counts vocabulary. It cannot tell you whether a reading is true to
a book.

---

## Contents

### Response corpus — 600 responses, 4 conditions × 10 books × 15 questions

| Folder | Condition |
|---|---|
| `CondA1_Gemini_2.5Flash/` | Gemini 2.5 Flash, ungoverned, minimal prompt |
| `CondA2_Ungoverned_GPT4omini/` | gpt-4o-mini, minimal prompt — the matched baseline |
| `CondA3_ScholarlyPrompt_GPT4omini/` | gpt-4o-mini, strong generic scholarly instruction, **no book content** |
| `CondB_Governed_GPT4omini/` | gpt-4o-mini via CPLite with the book-specific Canon Pack + retrieval |

Each reply is stored with its model, temperature, timestamp, token usage and — for A3 — the full
system prompt that produced it.

### Analysis

| File | What it does |
|---|---|
| `analysis/REPRODUCE_ALL.py` | **Start here.** Recomputes every figure in the manuscript from the raw response JSONs and asserts it against the published value. Exits non-zero if anything fails to reproduce. |
| `analysis/ablation_4way.py` | The four-condition analysis including the A3 ablation |
| `analysis/per_response_4way.csv` | 600 scored responses |
| `analysis/per_response_rawcounts.csv` | Marker counts and token bases, raw and suffix-stripped |
| `analysis/governance_log_46.csv` | The 46-proposal curator governance log |
| `analysis/s*.py`, `build_*.py`, `check_*.py` | Scripts generating each supplement section |
| `analysis/verify*.py` | Assertion suites checking the manuscript against the data |
| `drift_reduction_3way.py` | The earlier three-condition analysis, retained for continuity |

### Materials

- `canon_packs/` — the ten deployed Canon Pack objects
- `analysis/protocol_15q.json` — the 15-question protocol, five blocks of escalating drift pressure
- `analysis/book_registry.json` — the ten texts, genre clusters, companion names
- `hermeneutics-export-.../` — the raw platform governance export
- `figures/` — all figures at 300 dpi, PNG and TIFF, plus the script that generates them

---

## The instrument

A deterministic lexicon across four categories:

- **D1** therapeutic / self-help
- **D2** productivity / application
- **D3** doctrinal / intellectual flattening
- **D4** chatty-assistant

**46 entries, 45 unique strings** (`it's important to remember` is counted under both D1 and D2),
with D1 = 18. Matching is case-insensitive: whole-word for single tokens, substring for phrases.
Rates are markers per 1,000 whitespace-tokenized tokens.

The paper's primary measure is the **D1–D3 composite**, which excludes D4. D4 is reported
separately because the deployed platform appends a follow-on question to governed replies, so D4
partly measures that behaviour rather than the interpretive content of the answer.

An earlier version of the lexicon documented 43 unique strings with D1 = 16. The difference is a
single substitution: the bare word `emotional` was narrowed to three specific phrases. Every
contrast has been re-run under both versions and no significance verdict changes.

---

## Reproducing the results

```bash
git clone https://github.com/RayanBVasse/Reduced_Register_Drift.git
cd Reduced_Register_Drift
pip install scipy pandas matplotlib

python analysis/REPRODUCE_ALL.py     # every manuscript figure, asserted against the data
python analysis/ablation_4way.py     # regenerate the four-condition analysis
python figures/make_figures.py       # regenerate all figures
```

Requires Python 3.11+. **No API key and no network access are needed**: all 600 responses are
archived, so every number and figure in the paper regenerates offline.

Regenerating the *responses* themselves does require an OpenAI key (A2, A3, B) and a Gemini key
(A1), and will not reproduce them exactly — condition B runs at temperature 0.4 and neither
provider freezes its models.

One note on Python version: the governance export encodes timestamps with five-digit fractional
seconds, which `datetime.fromisoformat` rejects before 3.11. The extraction script normalises
them; a naive parse silently drops three of the 46 proposals.

---

## Known limitations

These are stated in full in the paper and repeated here so that anyone using the data knows what
it will and will not support.

- **The measure is register, not fidelity.** A response can avoid every marker and still misread
  a book.
- **The A3 ablation is not a book-ignorance condition.** The prompt carries no book content, but
  104 of 150 A3 replies contain entities internal to the work, which can only have come from
  pretraining. The contrast therefore tests whether an explicit interpretive profile adds
  anything for works the model has already absorbed.
- **Condition B differs from A3 in more than the governance object** — temperature (0.4 vs 0.0),
  retrieval, response length, and conversational accumulation.
- **One curator, one platform.** The governance log describes one person's practice and supports
  no generalisation.
- **All ten authors are deceased**, so this is curator-governed rather than author-governed
  deployment, and interpretive fidelity cannot be adjudicated on this corpus.

---

## Citation

Vasse, R. (2026). *Interpretive governance of AI reading companions: A curator-governed
deployment across ten canonical texts.*

Platform: CPLite, authors.living-literature.org
