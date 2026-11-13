# notes-r1fix4 (EGM skipped for this note: docs and docstring wording edits by the lead's order; EGM review is the lead's step)
R-numbers: none looked up (studio folder not given). Token use: not measured.

## Proof run (copy /tmp/b4copy of /tmp/v8work, under unshare -n with loopback up, made-up canned leads, nothing answered at a prompt)
Command (Linux form): `PYTHONPATH=src python3 scripts/crash_desk.py`
  -> exit 1, "RuntimeError: ... the folder demo_only is missing" (ModuleNotFoundError: No module named 'demo_only').
Command: `PYTHONPATH=src:. python3 scripts/crash_desk.py` (demo server `PYTHONPATH=src:. python3 -m demo_only.fakes_server --outbox keyed` running)
  -> "crash flag file: ..." then "desk listening on http://127.0.0.1:8765"; /counts answers. After `echo D2 > crash.flag` and one feed,
     desk printed "simulate crash" and exited 137.
  Without the demo server the desk exits 1 "cannot reach the demo servers", so the doc names the demo server command.
Replay run (same desk, `scripts/feed.py --source form --index 1`, `1`, `2`):
  canned-1 -> receipt_id 1 verdict new replayed false
  canned-1 -> receipt_id 1 verdict new replayed true
  canned-2 -> receipt_id 3 verdict new replayed false
  receipts table: [(1, 'canned-1', 2), (3, 'canned-2', 1)]  (attempts 2 for the repeated one)
  Plain sqlite repro (3 repeats between): ids 1 then 5, attempts 4 -> each repeat uses up one number.
Cause: src/lead_desk/desk.py:1363 `ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts + 1`; src/lead_desk/schema.sql:7
  `receipt_id INTEGER PRIMARY KEY AUTOINCREMENT`.
Follow-up start: desk.py:1285 (`elif self._pending_and_due(...)`: drive) ; tests/test_flow.py:115-124 (replay of a pending follow-up drives it once, a sent one not).
Counter: tests/test_flow.py:102 asserts attempts == 22 after 21 repeats. No test asserts the skipped receipt number (grep).

## Table
| sentence | file:line | old | new | proof |
|---|---|---|---|---|
| first bullet of "What you will see" | README.md:20 | "...gets `replayed: true` and changes nothing." | same lead and receipt number; no second lead, no second email; counted in `attempts`; uses up one receipt number (1, then 3); starts a due unsent follow-up | run above, desk.py:1285,1363 |
| "Replayed" word entry | README.md:37 | "...and changed nothing." | "...created no second lead and no second email. The repeat is counted in `attempts` and uses up one receipt number." | same |
| Linux feed comment | README.md:62 | "..., nothing changes" | "..., no second lead, no second email, one receipt number used up" | same |
| Windows feed comment | README.md:79 | "..., nothing changes" | same new text | same |
| "Claimed" bullet | README.md:104 | "...stored answer and changes nothing." | "...stored answer; no second lead and no second email is made. The repeat is counted and uses up one receipt number." | same |
| P1 (b) | docs/tests.md:116 | "...marked `replayed` and changes nothing." | no second lead/email; `attempts` 22 after 21 repeats (test_replay_same_source_ref); uses up one receipt number (no test pins it); a repeat of a `new` request starts a pending, due follow-up (`_pending_and_due`) | tests/test_flow.py:102, desk.py:1285,1417 |
| crash command | docs/tests.md:26 | `PYTHONPATH=src python scripts/crash_desk.py` | `PYTHONPATH=src:. ...`, why, and the demo server command | run above |
| Windows note | docs/tests.md:26 | (none) | "the Linux form was run, the Windows form was not run" | not run |
| docstring | scripts/crash_desk.py:3 | `PYTHONPATH=src ... set PYTHONPATH=src first` | `PYTHONPATH=src:. ... set PYTHONPATH=src;. first` | ruff check and format --check pass; line <=120 |

## Left out on purpose
- core's "cannot use up the 5 tries": not written in README or tests.md. contract.md:315 keeps "not meant to", which matches the evidence
  there (no test replays with the wait passing until the 5th try). desk.py:1418 docstring says "cannot burn the try cap" but the test gap stands.
- No other file says a repeat "changes nothing": grep of the whole tree (contract.md, docs/*.md, load_tools/README.md) found only unrelated uses
  (sent follow-up drive, unknown retry, rejected body, etc.). contract.md and load_tools/README.md needed no change. No other doc gives the crash command.
- Windows crash form not run (Linux only).
- Not fixed: README.md:144 / docs lines that say nothing about crash_desk need no change.

## Tests (docs-reading tests only, under unshare, DPLD_REQUIRE_SCAN unset; hygiene skipped by order)
See result line appended below.
Command: unshare run of pytest on tests/test_crash_points.py test_gitleaks_exceptions.py test_gitleaks_semgrep_lock.py test_path_confinement.py
test_portal_mode.py test_portal_wording_and_masking.py test_vendor_hosts.py -> "521 passed, 1 skipped in 121.67s".
Not run: test_hygiene.py (by order), test_load_tools.py, test_portal_api.py, test_portal_browser (they name README but were not run; no change to what they read was made by wording of the replay lines only).
