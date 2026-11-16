# v10-OPEN-FOR-LEAD (things only the lead can decide or fix)

1. L1 (open ruling): the plan's marker 2 default says the owner decides; decision 7 says otherwise. The checklist refuses `accept 2` until `L1_RULED=yes`; the lead must rule and write the answer. The fill list question 2 is headed as an open ruling.
2. L2: the lead must name the person the checklist tells the user to ask in D2 (it says "the builder in the channel"); confirm that is right.
3. Q1: the location of BP (`handover/BRIEF-PREAMBLE.md` of the repository) is assumed for the laptop; confirm the laptop copy has the same path.
4. Stale references in `PLAN-CHAIN.md` (not mine to edit): the CHAIN=4 marker lines 777/778 (right values are in checklist A0), the old step 4 checksum `b0caeb84c5a28a9d` / `b0caeb84...` (right: `28f92c5d1211207c`), and the 16-character checksum typo ending `d`.
5. Apply script defects (not mine to edit): F3 a damaged or missing RENUMBER line is not refused (writes a wrong plan, sha `5453169115cd74c4`); F4 a dangling symlink at the output path is written through. The checklist guards both (sha check; symlink check in step4), but the script should refuse.
6. The control file pid line name `P-4b-HIT pid=N` is taken from P-4b.sh as it is; if P-4b.sh changes its output wording, WSL-2/WSL-3 and C2c need the same change.
7. Nothing was run on Git Bash, WSL or the laptop: the lead should have the first real run done by a person with the builder on call, or a short dry run on the laptop first.
