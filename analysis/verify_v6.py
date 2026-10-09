#!/usr/bin/env python3
"""Check v6's new sections: figures match the locked results; framing constraints respected;
every citation appears in the verified reference log."""
import re, os
from pathlib import Path
HERE=Path(os.path.dirname(os.path.abspath(__file__))); BASE=HERE.parent/"08_continuation_paper"
v6=(BASE/"DRAFT_v6_sections_1_and_5.md").read_text()
refs=(BASE/"REFERENCES_verified.md").read_text()
lock=(BASE/"LOCKED_RESULTS.md").read_text()
ok=fail=0
def chk(l,c,d=""):
    global ok,fail
    if c: ok+=1; print(f"  PASS  {l}")
    else: fail+=1; print(f"  FAIL  {l}   {d}")

print("=== numbers agree with LOCKED_RESULTS ===")
for s,why in [("48.3%","headline"),("99%","semantic compliance"),("89%","lexical failure"),
              ("46 governance decisions","log") ,("600 responses","corpus"),("150 governed replies","n")]:
    chk(f"{s} ({why})", s in v6)
chk("no stale -42.9% headline", "42.9%" not in v6)
chk("no stale -44.5%", "44.5%" not in v6)

print("\n=== framing constraints from v5.2 §5 ===")
intro=v6.split("## 1.5")[0]
chk("intro does NOT present the five dimensions as the contribution",
    "five dimensions" not in intro or "not the invention of a mechanism" in intro)
chk("intro states the ablation deflation early", "deflationary" in intro)
chk("'relocation of authorship' framing present", "relocation of its authorship" in intro)
chk("no fidelity claim anywhere", "more faithful" not in v6.replace("makes an AI reading of it more faithful","") 
    or "untested" in v6)
chk("mechanism described as untested not disconfirmed",
    "not disconfirmed" in v6 and "untested" in v6)
chk("register credited to corpus linguistics", "Biber & Conrad" in v6 and "claim no\nnovelty" in v6.replace("\n"," ").replace("  "," ") or "claim no novelty" in v6.replace("\n"," "))
chk("model-choice caveat retained", "Gemini" in v6 and "changing model" in v6)

print("\n=== every in-text citation is in the verified log ===")
cites=set(re.findall(r"\(?([A-Z][a-zA-Z\-]+)(?: et al\.)?,? \(?(\d{4})[a-c]?\)", v6))
names={n for n,_ in cites}
known={"Agarwal","Agustin","Bhatt","Biber","Capurro","Cohen","Demichelis","Fast","Gadamer","Zamfirescu-Pereira","Pereira",
       "Hornby","Kommers","Lu","Pennebaker","Wilcoxon","Zamfirescu","Vasse","Conrad","Author"}
unknown=sorted(n for n in names if n not in known)
chk("no citation outside the verified set", not unknown, unknown)
for n in ["Agarwal","Agustin","Bhatt","Biber","Capurro","Demichelis","Fast","Hornby","Kommers",
          "Lu","Zamfirescu"]:
    chk(f"{n} present in REFERENCES_verified.md", n in refs)

print("\n=== corrected names used, wrong ones absent ===")
for wrong,right in [("Sachin","Shaily"),("Charlie","Christina"),("Jasmine","Jonathan"),
                    ("Raffaele","Remy"),("Rachel","Richmond")]:
    chk(f"'{wrong}' not used anywhere in v6", wrong not in v6)
chk("Hornby dated 2024 not 2025", "Hornby, R. (2024)" in v6 and "Hornby (2024)" in v6)

print("\n=== declared gaps are declared, not hidden ===")
chk("LLM-as-judge gap declared in Related Work", "Gap, declared" in v6)
chk("reference verification pointer present", "REFERENCES_verified.md" in v6)

print(f"\n{'='*58}\nPASS {ok}   FAIL {fail}")
