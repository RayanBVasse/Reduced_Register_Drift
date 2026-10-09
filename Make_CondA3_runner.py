#!/usr/bin/env python3
"""
TASK 2 — build the Cond_A3 ablation runner.

WHY A PATCHER, NOT A FRESH SCRIPT: the ablation is only valid if A3 is identical
to A2 in every respect except the system prompt. So rather than retype your
runner (and risk a silent difference), this generates the A3 runner by making
FOUR exact substitutions to your existing gpt4mini-extended-runner.py.
Model, temperature (0.0), question order, conversation threading, retry logic
and output format are therefore guaranteed identical.

    python make_cond_a3_runner.py          # writes gpt4mini-A3-scholarly-runner.py
    export OPENAI_API_KEY=...
    python gpt4mini-A3-scholarly-runner.py # ~150 calls, a few cents

Run it from inside your GFI_data_analysis folder.
"""
from pathlib import Path
import sys

SRC = Path("gpt4mini-extended-runner.py")
DST = Path("gpt4mini-A3-scholarly-runner.py")

# The steelman baseline. This must be the STRONGEST reasonable generic prompt,
# not a weak strawman — otherwise the ablation is rigged toward governance and a
# reviewer will say so. It targets the same drift categories the Canon Pack
# targets, but contains NO book-specific content (that is the whole point).
NEW_PROMPT = '''SYSTEM_PROMPT_TEMPLATE = (
    "You are a scholarly reading companion for the book {title} by {author}. "
    "Answer questions about this book in the intellectual register of the work itself.\\n\\n"
    "Principles:\\n"
    "- Explain the book on its own terms, in the conceptual vocabulary and genre it occupies. "
    "Do not translate it into contemporary self-help, therapeutic, motivational, wellness, or "
    "productivity language.\\n"
    "- Preserve the author's argumentative structure and doctrinal specificity. Do not soften "
    "strong or difficult claims into general life lessons, universal values, or broad human themes.\\n"
    "- Keep the historical and generic situation of the text visible. Avoid anachronistic framing "
    "and modern idiom that the work does not support.\\n"
    "- Be direct and substantive. Do not append reflective prompts, invitations to continue, "
    "or follow-up questions to the reader unless explicitly asked.\\n"
    "- Where the text is ambiguous, unresolved, or self-contradictory, say so, rather than "
    "resolving it into a clean takeaway.\\n"
    "- Ground claims in the book's own content, and state plainly when a question falls outside "
    "what the book addresses."
)'''

OLD_PROMPT = '''SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant that answers questions about the book "
    "{title} by {author}."
)'''

SUBS = [
    (OLD_PROMPT, NEW_PROMPT),
    ('RESPONSES_ROOT = HERE / "Ungoverned_GPT4omini"',
     'RESPONSES_ROOT = HERE / "CondA3_ScholarlyPrompt_GPT4omini"'),
    ('return f"CondA2_{qid}_{abbrev}.json"',
     'return f"CondA3_{qid}_{abbrev}.json"'),
    ('CONDITION_LABEL = "A2_ungoverned_matched_model"',
     'CONDITION_LABEL = "A3_scholarly_prompt_matched_model"'),
]

def main():
    if not SRC.exists():
        sys.exit(f"ERROR: run this inside GFI_data_analysis — '{SRC}' not found")
    text = SRC.read_text(encoding="utf-8")
    for old, new in SUBS:
        n = text.count(old)
        if n != 1:
            sys.exit(f"ERROR: expected exactly 1 match, found {n} for:\n---\n{old[:120]}\n---\n"
                     "Your runner differs from what Claude inspected. Send it over and it'll be re-patched.")
        text = text.replace(old, new)
    DST.write_text(text, encoding="utf-8")
    print(f"[done] wrote {DST}")
    print("  4/4 substitutions applied. Model, temperature and protocol unchanged.")
    print("\nNext:  export OPENAI_API_KEY=...   then   python", DST)

if __name__ == "__main__":
    main()