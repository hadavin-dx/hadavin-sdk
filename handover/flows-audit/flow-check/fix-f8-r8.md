# Fix log, round f8-r8 (fixer, security path, no round cap)

Input: `review-f8-r7-findings.md`. Static edits only. Nothing ran against n8n, Postgres, HubSpot or the network. Made-up data only. Nothing committed.
Files edited: `take_check.sh`, `test_take_check.sh`, `README.md`, and `run_all.sh` (only the one-helper change of item 7).

## Honest status first
- `run_all.sh` itself was NOT run (only `bash -n`). Its changes are covered only through the take_check tests and the patched-copy suite.
- Some new tests do not fail on the r7 script (the TAKE_CHECK_TODAY variant, the shell-note case, README wording and copy-detector checks). They guard the new behaviour but do not prove the old one broken.
- Review claim "Opus with a Cyrillic s passes" is untrue: the mixed-alphabet rule already refused it. Every other claim was reproduced.
- Known passes remain (short blacklist, by design): for example "Botty" and "Agentic". The README now says it is a short blacklist, not a proof.

## Exit codes (all run after the edits)
- `bash -n run_all.sh`, `take_check.sh`, `test_take_check.sh`: 0 (syntax-all-ok)
- `bash test_take_check.sh` on the patched real-v5 copy: 444 of 444 cases pass, rc=0
- Same suite against the r7 script (`TEST_TAKE_SCRIPT` mirror): 333 of 443 pass, 110 fail (91 word-check cases, 19 whole-take or other)
- `python3 -I tools/check_secrets.py`: rc=0, "PASS 0 hits in 1857 files"
- `python3 tools/check_refs.py`: rc=0, "PASS 5168 references"
- `ruff check .`: rc=0
- `ruff format --check .`: rc=0 (573 files already formatted)
- `git status --short` printed nothing at the end, so `flow-check/raw` and `flow-check/selftest-output` were not left changed (no restore needed).

## Per finding (fixed per class at one point)
- M1: `reviewer_ok` reads no plain shell variable; `REVIEWER_TODAY` has no effect (README says so). Test: mirror tests.
- M2 + M3: one shared normalisation function (`REVIEWER_NORM_PY`, `scan()`) used by both the check and `safe_text`: categories C, Zl, Zp, Mn, Mc, Me stripped, hand-written Default_Ignorable table, NFKD folding.
- M4: confusables skeleton table (written with `\u` escapes) before matching.
- M5 + M6: longer lists, s/es stems for listed words of 4+ letters, leet reading (digit 1 both ways, capped at 8 positions), @/$/! reading, squeezed matching per piece; README says short blacklist.
- m1 to m5, n1: fixed in the same helper; single-letter initial now needs a dot; text cut at 300 characters; line above 1000 characters refused; large input goes by stdin and fails closed.
- Item 7: word lists live only in `take_check.sh`; `run_all.sh` and README ask it (`--reviewer-words` prints 3 lines, `--standin-name`, `--safe-text`, `--check-reviewer-line`). Test `no_list_copy` detects copies.
- Stand-in line in `run_all.sh` now carries the pin's own date.

## Lead decisions needed
1. Now refused as names: Llamas, Alexa, Siri, Jarvis, Bard, Bing, Manus. Keep?
2. Single-letter initial needs a dot. John Doe and Jane Doe are refused phrases.
3. The 1000-character cap.
4. "session" is a whole-word match.
5. The date window allows one day ahead (documented).
6. Run `run_all.sh` for real (needs the lead's environment).
