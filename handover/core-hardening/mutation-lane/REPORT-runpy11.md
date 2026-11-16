# REPORT-runpy11 (run.py round 10, builder)

## Failed, not done, not checked (first)
- Full run 2 on the frozen code failed 3 checks (evidence-r10/full-run-2-3failed.txt). All fixed, rerun clean:
  - T65 planted and T65 control: the test replaced `subprocess.Popen`, but run.py now starts programs through the class `Child` (the S603 fix), so the test never reached its line. Test fixed (it patches `Child` when present); T65 passes on r10, 2 of 2 (dev5-T65-r10.txt), and on r9 code too (dev6-T65-r9code.txt).
  - T97e (mode 4755, only as the unprivileged user nobody): a write by a user without the privilege to keep setuid/setgid clears those bits, so 4755 came back as 755. This was a REAL run.py bug (as root it never shows). Fixed in run.py: the recorded mode is set again after the write, in both write paths.
- Final full run 3 (frozen copy): root FAILED CHECKS 0 of 442; child (uid 65534) 0 of 87; skipped none. Raw: evidence-r10/full-run.txt.
- Not done: the "one fixed pointer file in the state folder" the lead approved. I do not know what it is for (no brief text for it reached me). Needs-lead: which file name, what it holds, and which finding it closes.
- Not verified: Python interpreter start-up window before the first import line finishes (about 20 to 50 ms) still has the default signal action; documented in the docstring, cannot be handled in Python (impossible-now). Plain `--restore` still trusts a forged marker plus matching backup (limit (d), same-user attacker); only `--restore --sha` closes it. Stated in the docstring and pinned by T98d/T98e/T98e2.
- ruff S603 fixed without noqa by one subclass `Child(subprocess.Popen)` used at both start points. Honest note: the argument list was already tool-built, so this is a lint-structure change, not a new protection.

## Changes (r10)
M1, M2, m1-m11 of review-r9-security.md (details in checkpoint-runpy11.md and T97). Coordinator items: (1) any path over 4096 bytes or a name over 255 bytes (--root, --sha, --file, --repo, test args) refused, exit 2, no traceback (T98a); (2) early signal handlers right after the imports, exit 128+N (T98b); (3) S603 gone, 0 noqa (T98c); (4) limit (d) in the docstring plus tests (T98d-f).

## Evidence (all in evidence-r10/)
- New tests fail on r9 code: T97 18 of 19 (guard T97f2 passes by design) in dev1-r9code-T97only.txt; T98 7 of 7 in dev3-r9code-T98only.txt.
- Dev passes on r10: dev1-r10code.txt, dev2-r10code-T96T97T98.txt (46/0).
- Final: full-run.txt (442 root, 87 child, 0 failed). ruff check clean, ruff format clean, bash -n ok.
- Re-read evidence-r9-independent/00-TABLE.md: its findings (long paths, limit d, start-up signal, S603) are all covered above.
- Earlier partial runs kept: full-run-r10base-partial.txt, full-run-2-3failed.txt. A first run was killed by me and left one orphan run.py that I stopped before run 3; no stray processes remain (0 left).

## Hashes
- run.py: de7317661e50c9e1785dc233678b1893adbaf19497c619f5c31d5c4d9d367528
- safety-tests.sh: 1938848903717ab21376a19769e01e14ccbb13bb645d828c226a7485dde07250
- Frozen copies (identical): evidence-r10/frozen/run.py, evidence-r10/frozen/safety-tests.sh; hashes in evidence-r10/hashes.txt.
- Backups unchanged: run.r9.py, safety-tests.r9.sh.
