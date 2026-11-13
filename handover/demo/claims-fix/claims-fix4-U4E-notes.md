# U4E notes (code docstrings/comments, part7). Preamble rules read; no R-numbers needed (text-only).
Format: file | audit verdict | OLD -> NEW | evidence | mine
1. gate.py:6 | UNBACKED | "SQLite itself is never contended" -> "should not be contended (no test proves that for every path)" | no test | F
2. db.py _migrate | UNBACKED | "rolls the whole thing back, so ... never left" -> same plus pointer to the test for a failed migration in tests/test_desk_http_edge_cases.py, "is not left" | that test (fails at start and end of schema text, book shape equal) EXISTS: audit wrong | S (audit partly W)
3. live_claude.py 429/5xx | UNBACKED | kept, added "by the code path; the crash test checks the reserve, no test reads the ledger after a 429 or 5xx" | tests/test_live_claude.py (crash test; r429/r5xx tests only check the error class) | F (honest label)
4. desk.py _MirrorWait | UNBACKED | "never held across a database write or CRM call" -> "only guards the small dictionary operations of this class (the four methods below): no database write or CRM call runs inside it" | read set/clear/waiting/__contains__: only dict ops | S (code read)
5. desk.py retry (was :2204; the :2222 line is code, not a docstring) | UNBACKED | "never 200" -> "not 200 ... (tests/test_desk_edge_cases.py and tests/test_desk_http_edge_cases.py check this)" | test_desk_http_edge_cases.py test_retry_not_200_sending asserts 409 in_progress and row still sending; test_desk_edge_cases.py asserts same; tests/test_http.py:227 too. Audit wrong (tests exist) | S
6. catcher.py:20 | UNBACKED | "Handles hundreds of connections at once" -> "Serves connections with asyncio (listen backlog 1024; no test opens hundreds at once)" | grep tests for backlog: none | F
7. check_schema.py:3 | UNBACKED | "fire every trigger and constraint once" -> "fire the triggers and constraints it lists (no CI log is shipped)" | schema.sql has 14 CREATE TRIGGER (counted); only 1 trigger name appears literally in the script; script has 47 expect lines; I did not match each of the 14 -> not claimed. CI step exists in .github/workflows/lint.yml but no log | F
8. run_stats.py:1 | UNBACKED | "an atomic replace" -> "a temporary file, then os.replace; no test checks atomicity" | code lines 17-19 read | F
9. trace.py:14 | UNBACKED | "never changes" -> "does not change ... (the test for a trace write failure in tests/test_live_claude.py checks this for the CRM wrapper)" | test_trace_write_failure_does_not_change_the_call asserts PUT result and write_failures==1: exists, audit wrong | S
10. imap_count.py:18 | BACKED (wording absolute) | "ALWAYS ... no settings value can switch that off" -> "checks ...: no value in a settings file can switch that off (code that builds ImapSettings itself may pass its own ssl_context)" | audit text, imap_count.py:68 as cited by audit | F (wording)
11. desk.py _nudge_pass (audit :884) 5 per pass / 2.5 s | UNBACKED | added "(constants; no test of their values)" | grep tests: NUDGES_PER_PASS, NUDGE_PASS_SECONDS not referenced | F (number kept)
12. constants.py PORTAL_MAX_INFLIGHT=8 | UNBACKED | added "(tests/test_portal_api.py)" | test_over_the_cap_gets_503_busy holds 8 requests, the 9th gets 503 busy and /counts still 200: exists, audit wrong | S
13. constants.py DRAIN_MAX_BYTES | UNBACKED | comment now "(a constant; no test of its value)" (the explanatory clause "so the reply is not lost to a reset" was replaced) | grep tests: no use of the constant, no byte-limit test found | F
14. constants.py DUPLICATES_MAX=50 | UNBACKED | added "(the total is given; tests/test_portal_api.py)", "always" removed | test_portal_api.py:388-391 adds MAX+3, asserts total = MAX+3 and list length = MAX; test_later_messages.py:158-163 too | S
15. hubspot_probe.py / loader.py | already done by stage 1: not touched.
Verdicts: S 6 (rows 2,4,5,9,12,14; in 2,5,9,12,14 the audit missed an existing test), F 8 (1,3,6,7,8,10,11,13), O 0, W 0. Total 14 rows.
Owner questions: none.
Not verified: whether check_schema.py covers all 14 triggers; ledger after 429/5xx; drain byte limit behaviour; no test run (text only).
## Proof (text-only), /tmp/work/u4e-proof.py output (ast.dump base HEAD vs now, docstrings stripped):
load_tools/catcher.py AST EQUAL
scripts/check_schema.py AST EQUAL
src/lead_desk/constants.py AST EQUAL
src/lead_desk/db.py AST EQUAL
src/lead_desk/desk.py AST EQUAL
src/lead_desk/gate.py AST EQUAL
src/lead_desk/imap_count.py AST EQUAL
src/lead_desk/live_claude.py AST EQUAL
src/lead_desk/run_stats.py AST EQUAL
src/lead_desk/trace.py AST EQUAL
max line: 119

ruff check (fresh-venv5) on the 10 touched files: All checks passed!
ruff format --check: 10 files already formatted
Patch applies on a fresh copy of the base (git apply --check). No suppression text added.
