---
name: blocker-ledger-rule
description: "Owner 2026-11-02 HARD RULE: every blocker/major from every EGM review is a row in egm\BLOCKER-LEDGER.md; Done = ledger_check passes for the topic"
metadata:
  node_type: memory
  type: feedback
---

Every blocker and major from every review (earlier, now, future) is one row in `egm\BLOCKER-LEDGER.md` (id, source file + finding id, severity, area, summary, status OPEN / FIXED-UNVERIFIED / FIXED-VERIFIED / OWNER-ONLY / IMPOSSIBLE-NOW, fixing artifact, verified-by, date).

**Rule:** Done = `python egm\tools\ledger_check.py --topic <area>` exits 0 (no BLOCKER/MAJOR OPEN or FIXED-UNVERIFIED). Every review's findings are appended the same turn. A status becomes FIXED-VERIFIED only with a verifying artifact (later review closure line, evidence file, CI run). The `egm:egm-drift-report` step runs `ledger_check`.

**Why:** owner 2026-11-02, so no blocker is lost between review rounds. First fill (2026-11-02) was mechanical; formats vary, so spot-check a topic before calling it clean. Latest-in-series rows are OPEN until verified.

**How to apply:** see [[egm-review-routing]], [[class-level-fixes]], [[reviewer-independence]]. Checker tests: `python -m unittest egm\tools\test_ledger_check`.
