# LESSONS for the checklist (cloud session flows-audit, 2026-11-16)
1. Count with the script first. This session's plan said 54 flow files; the script said 52. A number in a plan needs the command that produced it next to it.
2. A test fixture that cannot fail proves nothing: the first masking test passed with the rule broken because no fixture separated the right rule from the wrong one. Break the code on purpose and watch the test fail.
3. A check script that skips by file-name prefix can skip a file it should scan (tools/scratch vs tools/scratch_probe.txt). Skip whole folders with a trailing slash only.
4. LLM lane agents must never retype machine data: a small script assembles the table from their judgement cells (tools/assemble_lane.py), so a copying slip cannot happen and check_names.py can compare cell for cell.
5. Many parallel flow versions were the owner's "duplicates" worry: keep one current folder per variant and archive the rest in the same change that makes the next version.
6. A claims sheet must carry its own numbers' source; this one cites relayed measurements whose raw files are not in the repository (UNVERIFIED until they are).
7. Table definition files drift when copied: one DDL file, read by the flows, the harness and the docs.
