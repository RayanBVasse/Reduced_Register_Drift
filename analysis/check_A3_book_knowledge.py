#!/usr/bin/env python3
"""
Does Cond_A3 — which receives NO book content in its prompt — nonetheless
display book-specific knowledge from pretraining?

Tests for book-specific proper nouns and concepts that could only come from
the model's parameters, since the A3 prompt names only title and author.
Reads raw response JSONs; depends on no intermediate file.
"""
import json, re, os
from pathlib import Path
GFI=Path("/sessions/practical-admiring-babbage/mnt/5. Extended GFI/GFI_data_analysis")
HERE=Path(os.path.dirname(os.path.abspath(__file__)))

# entities internal to each work; none appear in the A3 prompt, which gives
# only title and author.
MARKERS={
 "nw":  ["Saladin","Recha","Templar","Ring Parable","Three Rings","Daja","Al-Hafi","Sittah"],
 "aow": ["Attack by Stratagem","Sun Tzu","terrain","Laying Plans","spies","deception"],
 "med": ["Marcus Aurelius","Stoic","logos","providence","Antoninus","assent"],
 "coa": ["Monica","Carthage","Ambrose","pear","Manich","conversion"],
 "sbf": ["double consciousness","veil","Booker T. Washington","Atlanta","sorrow songs"],
 "lofd": ["Covey","Auld","Baltimore","Sophia","slaveholder"],
 "wdocd":["Concord","Walden Pond","Emerson","civil disobedience","poll tax","bean"],
 "aobf": ["thirteen virtues","Philadelphia","Poor Richard","printer","errata"],
 "jsm":  ["Bentham","utilitarian","James Mill","mental crisis","Harriet"],
 "vre":  ["Gifford","varieties","conversion","saintliness","mysticism","healthy-minded"],
}
L=[];w=L.append
w("Does Cond_A3 show book knowledge it was never given?\n")
w("The A3 system prompt supplies title and author only. Any book-internal")
w("entity in an A3 reply therefore comes from pretraining, not from context.\n")
w(f"{'Book':<44}{'A3 replies w/ internal entity':>30}{'B (has retrieval)':>20}")
tot_a3=tot_b=0
for ab,ms in MARKERS.items():
    pat=re.compile("|".join(re.escape(m) for m in ms), re.I)
    cnt={}
    for cond,folder,pre in (("A3","CondA3_ScholarlyPrompt_GPT4omini","CondA3"),
                            ("B","CondB_Governed_GPT4omini","CondB")):
        n=0
        for i in range(1,16):
            rp=str(json.loads((GFI/folder/f"{ab}_responses"/f"{pre}_Q{i:02d}_{ab}.json").read_text()).get("reply") or "")
            if pat.search(rp): n+=1
        cnt[cond]=n
    tot_a3+=cnt["A3"]; tot_b+=cnt["B"]
    title=json.loads((GFI/"book_registry.json").read_text())["books"][ab]["title"]
    w(f"{title[:43]:<44}{cnt['A3']:>21}/15{cnt['B']:>17}/15")
w("")
w(f"TOTAL: A3 {tot_a3}/150 replies contain book-internal entities; B {tot_b}/150.")
w("")
w("Implication: A3 is not a 'no book knowledge' condition. It is a 'no book")
w("content in the prompt' condition applied to a model that already knows these")
w("works. The A3 vs B contrast therefore tests whether an explicit interpretive")
w("profile adds anything for texts the model has already absorbed -- not whether")
w("book-specific governance matters in general.")
(HERE/"A3_book_knowledge_output.txt").write_text("\n".join(L))
print("\n".join(L))
