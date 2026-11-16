import re
from patch_lib import Doc
d = Doc("CORE-PR-HANDOFF-v14.md")
d.rep("cycles_v13_from_independent.py", "cycles_v14_from_independent.py", count=d.t.count("cycles_v13_from_independent.py"))
d.rep("(`evidence-handoff-v13/raw-pg-b1-v13.txt`, 16 checks, all refused)", "(`evidence-handoff-v13/raw-pg-real-code-v13.txt`, 16 checks, all refused; `raw-pg-b1-v13.txt` holds only 8 hostile statements: citation finding 2)")
d.rep(" Default if you do not answer: the held file carries plain `usd >= 0 AND usd <> 'NaN'::numeric` is NOT used either; the clause is left out and the file is Q34's exact words, `CHECK (usd >= 0)`. You decide.",
      " Default if you do not answer: the clause is NOT built and the held file carries Q34's exact words, `CHECK (usd >= 0)` (which lets a not-a-number total in). Decides: lead.")
d.rep("The attribute `max_requests` (default", "The attribute `max_requests` (**planned, added by S-2a; no `max_requests` exists in `src/` today**; default")
d.rep("sends up to `max_requests` paid requests while", "sends up to the planned `max_requests` (S-2a adds it) paid requests while")
d.rep("`injection_check(detector, text, source, *, spend=\"flag\")` (`guard/injection.py:85`) catches", "`injection_check` (`guard/injection.py:85`; **today it has 3 parameters; S-2a changes the signature to `injection_check(detector, text, source, *, spend=\"flag\")`**) catches")
d.rep("`injection_check(detector, text, source, *, spend=\"flag\")` sets it", "the new `spend=` keyword (planned, S-2a) sets it")
d.rep("evidence-handoff-v14/reserve_table.py", "reserve_table.py (**does not exist yet; the S-2a builder writes it; it is not in `evidence-handoff-v14/`**)")
d.rep("evidence-handoff-v14/mutants.py", "mutants.py (**does not exist yet; the S-2a builder writes it; it is not in `evidence-handoff-v14/`**)")
d.rep("evidence-handoff-v14/needed-check/<PR>.md", "needed-check/<PR>.md (**the folder does not exist yet; the lead creates it when the checker returns**)")
d.rep("19 lines, 18 once one match inside a compiled `.pyc` file is excluded. Most are `llm=ScriptLLM(...)` or similar fakes; I did **not** open them to see whether any is a `NetworkLLM`, so the number of tests that pass a `NetworkLLM` into `app.build` is **unknown**, and the rule",
      "26 `build(llm=` calls once multi-line calls are counted (v13's 19 missed them; independent check `review-handoff-v13-citations.md` item 4); **0 of the 26 pass a `NetworkLLM`** (counted by that check). The rule")
d.rep("(my program says 7, the independent script says 9 today and 10 planned;", "(v13's program said 7 and omitted `llm.common` and `llm.retry`; the independent script says 9 today and 10 planned, group sizes [10,4,3,3,2,2];")
d.rep("(16 checks, all refused)", "(16 checks, all refused: `evidence-handoff-v13/raw-pg-real-code-v13.txt`)", count=d.t.count("(16 checks, all refused)"))
d.save()
o = Doc("CORE-PR-HANDOFF-v14-other-tracks.md")
t = o.t.replace("evidence-handoff-v13", "evidence-handoff-v14")
t = re.sub(r"(_|-)v13(\.|-)", r"\1v14\2", t)
t = t.replace("v13-CHANGES.md", "v14-CHANGES.md").replace("CORE-PR-HANDOFF-v13.md", "CORE-PR-HANDOFF-v14.md")
t = t.replace("cycles_v13_from_independent", "cycles_v14_from_independent")
o.t = t
o.rep("evidence-handoff-v14/masking_damage.py", "masking_damage.py (**does not exist yet; the builder of that PR writes it; not in `evidence-handoff-v14/`**)")
o.rep("evidence-handoff-v14/needed-check/<PR>.md", "needed-check/<PR>.md (**the folder does not exist yet; the lead creates it**)")
o.rep("and `src/hadavin_sdk/audit/chain.py:140` is a comment)", "; the grep covered `docs/`, `README.md` and `SECURITY.md` only, so `src/hadavin_sdk/audit/chain.py:140` is not a grep hit and is named only as a place to read; citation finding 1)")
o.rep("into `hadavin_sdk/fileguard.py:read_private_file(", "into the **new** file `hadavin_sdk/fileguard.py` (K1 creates it; it does not exist in `src/` today) with `read_private_file(")
o.rep("(`mounted_file._fetch` keeps", "(`mounted_file._fetch` keeps") if False else None
o.rep("passes `allow_group_read=True` (0440", "passes the new keyword `allow_group_read=True` (K1 adds it; 0440")
o.save()
