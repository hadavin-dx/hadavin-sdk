# out-v5: read-only check of notes-r1fix8 against /tmp/final-series
Method: read the new text and the code or tests it cites; no pytest run. One SQLite check was run (below). Studio bible R-numbers not read (studio path not given); none cited.

| row | verdict | evidence | correct wording if FALSE |
|---|---|---|---|
| M2 tests.md P5 | TRUE | docs/tests.md:120; docs/limits.md:82 heading "Load and limits", :84 holds the `LEAD_DESK_LOAD_N=300 ... measure_burst` command and "No result of this test is stored here"; tests/test_server_hardening.py:225 | |
| M3 limits.md:91 | TRUE (skipped, bullet gone) | git diff docs/limits.md shows the "Known gaps in these figures" bullet removed | |
| M5 tests.md:127 | TRUE | docs/n8n-recipe.md:69 heading "4. What to know when the desk sits behind n8n"; :71 "no n8n run result is stored here" | |
| M6 README replay/counts | TRUE | src/lead_desk/portal/portal.js:58 `duplicate: 'Repeat'`; desk.py:272-281 `_COUNTS_SQL` counts rows of receipts; desk.py:1363 `ON CONFLICT ... attempts = attempts + 1`; tests/test_flow.py:102 attempts == 22 after replays. README:37, 63, 66, 79, 83 and the Words entries read correctly | |
| M10 sonar.yml:13-14 | TRUE | .github/workflows/sonar.yml:13-14 read "is not decided;" / "nothing else in this repository records it." Not parsed by me (notes say yaml.safe_load ok) | |
| N1 README:41 | TRUE | contract.md:171 and :212 (`F<lead_id>\|R<receipt_id>\|D<receipt_id>\|O<receipt_id>\|N<lead_id>`); heading contract.md:263 | |
| N2 README:9 | TRUE | demo_only/leadflow.json:6 `"nudge_after_seconds":90`; README:22 says 90 s | |
| N3 tests.md P10 / contract failed-follow-up card | TRUE | tests.md:125 has 12 `<br>- ` (counted); contract.md:131-138 one parent bullet, 5 direct children, 3 grandchildren = 8 nested. Only `<br>` use in the docs (noted by author) | |
| N4 contract.md:47-52 | TRUE | contract.md:47 now a 2-space child of (4), lines 48-52 at 4 spaces, (5) at top level on 53 | |
| N5 settings.md:78 | TRUE | smtp_provider.py:241 `min(timeout, self._s.timeout_seconds)`; :322-323 clamps to min(send_timeout_seconds, 9.0); constants.py:82 `CALL_DEADLINE_MAX_SECONDS = 9.0`; desk.py:1437 `_call_deadline` = min(send_timeout_seconds, 9) and desk.py:2023 passes it to `outbox.send` | |
| N6 DPLD / revenue-operations / dpld | TRUE | settings.md:152; README:8 ("revenue-operations person (someone who runs a company's sales tools)"); hubspot-probe.md:12 | |
| N7 check_schema.py:1-2 | TRUE | scripts/check_schema.py:1-2; `expect_error` is called per trigger and constraint (:100-338). "once" is loose (some checks add positive cases) but not wrong | |
| N8, N10 | n/a (skipped by owner of that file / lead) | | |
| N9 limits.md:60 | TRUE | tests/test_http.py:292-293 (parametrize keyed, blind), :336 `test_crash_d2_subprocess_with_the_blind_smtp_sender` (blind SMTP) | |
| minor "a new row after" | TRUE | contract.md:327 contains the new text; gate.py:48 `PENDING_GRACE_SECONDS = 2`; gate.py:87; desk.py:741 | |
| C1 why-this-code.md:37 | TRUE | file scripts/hubspot_probe.py exists; docs/hubspot-probe.md exists | |
| C2 "can use up a receipt number ... (no test pins this)" | TRUE | I ran sqlite3 3.53.1 on a copy of the pattern (AUTOINCREMENT + ON CONFLICT DO UPDATE): ids were 1 then 3 after one replay, so every replay burns a number; "can" understates but is not false. No test asserts a skipped number (grep of tests found none). schema.sql:7 AUTOINCREMENT | |
| C3 contract.md:91 | TRUE | tests/test_portal_api.py:56 RESTARTS = 20, :1462 and :1511 `port = free_port()` fixed per test, x20 restarts. "most" is safe. I did not count how many tests use port 0 | |
| C4 contract.md "bare object()" | TRUE | tests/test_followup_edge_cases.py:416 `{"n": object()}`; sits on contract.md:285 | |
| C5 desk.py:1354 comment | TRUE for that comment | desk.py:1354 now "4401-digit"; tests/test_followup_edge_cases.py:416 `10**4400` = 4401 digits | |
| C6 limits.md:30 | TRUE with a small ambiguity | tests/test_live_claude.py exists and demo_only/fake_model_server.py is a local stand-in model server; but README:31 defines "Demo servers" (plural) and the CRM/mail one is a different program. Suggested clearer wording: "The live step was run only against the local demo model server (`demo_only/fake_model_server.py`)." | (optional) |
| C7 crash_desk.py:3-4 | TRUE | scripts/crash_desk.py:3-4; README:76 uses `$env:PYTHONPATH = "src"`; ';' is the Windows path separator | |
| C8 = N1 | TRUE | see N1 | |

## Extras asked
- Receipt wording "can skip (no test pins this)": TRUE (above). Inconsistency left: docs/tests.md:116 (P1) still says "uses up one receipt number (no test pins the skipped number)". Not FALSE; suggest "can use up" for matching.
- "most tests use port 0": TRUE (above).
- bare `object()` instance: TRUE.
- 4401 in desk.py comment vs `10**4400`: TRUE. BUT contract.md:285 (not in the notes) still says in the same sentence "a 4301-digit number" and later "a number of 4401 digits" - a contradiction. Correct wording at contract.md:285: "(mixed-type keys, a set, a date, a 4401-digit number)". Same sentence lists "a date" and says "no test uses a date"; that is consistent, but the desk.py comment also lists "a date" (same status).
- limits.md:30 "demo server": see C6.
- crash_desk.py PowerShell form: TRUE.

## Hygiene grep (README.md, contract.md, docs/*.md whole files, plus the 52 added diff lines)
- Drive-letter paths: none (whole files and added lines).
- IPs other than loopback: none; only 127.0.0.1 appears.
- 40+ character runs of [A-Za-z0-9+/=_-]: none.
- Links: only loopback URLs: README.md:24,61,65,66,78,82,83; contract.md:258 (127.0.0.1:8765/leads), :112 `http://<allowed...>`, :150 `http://<host...>`, :179 `http://[` (IPv6 placeholder text); docs/hubspot-probe.md:46 `http://127.0.0.1:PORT`; docs/limits.md:84; docs/n8n-recipe.md:24,133(settings); docs/portal.md:5; docs/settings.md:28 `http://[`, :133. No external links, no markdown links.

## Not checked
yaml parse of sonar.yml (taken from notes), line-length limits, any pytest/ruff result, the count of tests using port 0, the notes' test totals.
Files written: /tmp/work/d/out-v5.md only. Nothing in /tmp/final-series edited. EGM skipped: read-only verifier.
