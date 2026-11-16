# run.py r11 builder hand-back (condensed copy), 2026-11-16. Builder evidence only; no independent review yet.
## Failed, not done, not checked (first)
- Limit (d) NOT fixed: plain --restore still trusts a forged marker plus matching backup (same-user attacker). Making --sha mandatory is an owner/lead proposal (end of pointer-file-DESIGN.md).
- Start-up signal window reduced, not closed: handlers in place after 30-46 ms; builder probe (24 runs) still saw default-action deaths up to 0.08 s and one KeyboardInterrupt traceback at 0.01 s. Only a tiny launcher plus module would shrink it: lead decision.
- First full run had 1 failure (T95d3: minor-6 change refused a genuine 0664 marker); fixed via REF_MODES from the tar header; third full run clean.
- Deviation on minor 6: "any write bit for others, and any group write bit the git archive file does not have" (literal lead wording breaks genuine restores).
- Not verified: signals as nobody, power loss, pthread_sigmask failure path, independent mutation controls N0-N10 on r11, an idle machine. Pointer file NOT built (6 questions in pointer-file-DESIGN.md).
## Fixed
MAJ-1 setuid from forged marker (mode cut to 9 bits on plain restore, post-write mode check); MAJ-2 tests (T98 alone on r9: 4 of 7 fail; text checks labelled); minor 1 long -k/-m (also a real r10 crash); minor 2 path length 4095; minor 3 --raw folder before state check; minor 4/5 relabelled; minor 6; minor 7; S603 option (b) check_child_call, 0 noqa.
## Evidence (builder)
New tests on r10: 15 of 52 fail. r11: 0 of 26. Full run root 0 of 458, uid 65534 0 of 103, none skipped. ruff clean. run.r11.py sha256 4f7382d64c2d56f6eb97bf30f7307c19c02dd8b9020ea7e6060111f228be0fe7; safety-tests.r11.sh d3f8868d54d9a65c231cb0663a478609bee96b9bce7642b777551e9bb20c054e.
## Decisions for lead/owner
1 --sha mandatory for --restore (or --trust-state-folder flag); 2 pointer-file questions; 3 launcher split.
