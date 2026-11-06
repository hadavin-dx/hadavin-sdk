# P6b1 round 3 resolve report (egm:egm-resolve, Opus 5.5)

Honest note (read first):
- I am a fresh resolve session. I did not write the ticket and I have no memory of the author's reasoning. Every position below rests on the files and the probes named here, not on recall.
- I ran small stdlib and pydantic probes with `python -I` in a scratch folder: Python 3.13.18 with pydantic 2.13.5, and Python 3.12.3 with the stdlib only (pydantic is not installed for 3.12 here). The ticket cites pydantic 2.14.1, which I did not have. I ran no repository test, no mutant and no `uv` command.
- I read the code cites the reports rely on (listed under Facts). I did NOT read: `pinned()` in `llm/`, the rest of `llm/*.py`, the P6a ticket, the mutation runner, or the hot-file lists.
- One finding (R3-COR-1) is valid for a reason the reviewer did not give: CPython's normal C code does NOT put the input in the error text, but the pure-Python fallback does. I keep the fix and I state both facts.
- I found one sibling defect outside P6b1 (`config.py:360-363` prints a system's raw `base_url` in a refusal). I did not fix it. It goes to the lead as PENDING LEAD 14 with an owner package, so it is not lost.
- I did not edit the ticket, commit, push or write DECISIONS.md, as the brief asked.

Status: resolved (categorised; the ticket is NOT edited here). Recommendation: NO revision 4. The fixes go into a "Build notes (order 20)" section at the end of revision 3, using the exact text below.
Target: `handover/tickets/P6b1.md` revision 3 (561 lines; security path, Tier A; round 3 = the last ticket round). Inputs: `reviews/P6b1-round3-adversarial.md` (R3-ADV-1..12: 0 Blocker, 2 Major, 7 Minor, 3 Nit) and `reviews/P6b1-round3-correctness.md` (R3-COR-1..8: 0 Blocker, 1 Major, 4 Minor, 3 Nit). Merged for the fix, one decision each: ADV-4 with COR-3 (expected hosts the pattern cannot hold). Closed by a cut: ADV-3 and COR-4 (by the ADV-2 cut), COR-7 (by the ADV-1 cut).
Gate: the skill's "wait for the user" step is skipped (auto mode). Nothing goes to the owner from me.
- Round cap (order 20(6)): the cap is 3 rounds counting from round 1, and this was round 3. One more round is allowed only for "a money or redaction package whose last round had no Blocker and at most 2 Majors".
- P6b1 fails BOTH conditions. (1) Its path class is security (ticket line 128). R3-ADV-9 asks the lead to confirm that (PENDING LEAD 12). (2) Round 3 had 3 Majors in total (ADV-1, ADV-2, COR-1), not at most 2.
- So the cap does NOT allow round 4, even if the lead reclassifies the package as redaction. A round 4 would need a new numbered lead order that overrides 20(6) by name. I do not recommend one. The two cuts remove surface, and the one design fix (COR-1) is a single caught exception with three test rows. The build-start review (order 19 A, order 21 item 17) reads revision 3 plus these build notes and is the independent check. Its brief should name the three Majors below.
- Revision 4 or build notes: build notes. Ticket line 4, order 20(3) ("defects are fixed in the ticket's build notes, not in new revisions") and orders 16-18 all point that way. Risk, stated: the two cuts touch about 30 lines of the body, so a builder could follow stale body text. Mitigation: the lead adds ONE banner line under ticket line 4: "Build notes (order 20) at the end of this file replace the lines they name; where they conflict with the body, the build notes win."

Facts I checked myself (2026-11-06; read = read the file; ran = probe output seen):
- Ran, 3.12.3 and 3.13.18: `date.fromisoformat` on strings that match `[0-9]{4}-[0-9]{2}-[0-9]{2}` but are impossible dates gives texts with no input: `2026-13-45` gives `month must be in 1..12`, `2026-02-30` gives `day is out of range for month`, `0000-00-00` gives `year 0 is out of range`.
- Ran, both versions: the pure-Python fallback `_pydatetime.date.fromisoformat` (used when the C `_datetime` module is missing) gives `Invalid isoformat string: '<the input>'` for the same three strings. Non-ASCII digit dates give that same input-bearing text on the C path too, but the `[0-9]` rule stops them before `fromisoformat`.
- Ran, 3.13 + pydantic 2.13.5: with `hide_input_in_errors=True`, `str(ValidationError)` holds the validator's message (`Value error, month must be in 1..12`) and no `input_value`. `errors()` still holds `input` (it is not printed by `config.py`). So `hide_input_in_errors` hides the input field, not the message text, as COR-1 says.
- Ran, 3.13 + pydantic 2.13.5: a `Field(pattern=r"^...$")` refuses a trailing newline. Python `re.match(r"^[a-z]{3}$", "abc\n")` accepts it, and `re.fullmatch` refuses it. ADV-8 is real for a builder who writes `re.match` with `$`.
- Ran, 3.13: `urlsplit(u).hostname` keeps ESC, BEL and NUL (`https://ex<ESC>ample.com/v1` gives `ex<ESC>ample.com`). It drops tab and newline. It returns an international name as Unicode (`bücher.example`). It returns `None` for `https:///v1` and `::1` for `[::1]`. ADV-4 and COR-3 are real.
- Read `backends/table.py:71-85`: `OpenAICompatSettings` checks only the scheme and loopback, so such a `base_url` loads.
- Ran: a frozen pydantic model with a `list[str]` field is unhashable (`unhashable type: 'list'`), and `tuple[str, ...]` refuses a bare string. Read: nothing in `src/` hashes these settings (ADV-12's grep; not repeated by me).
- Read `config.py:150-159, 328, 360-370`: the config refuses only the `allow_insecure_loopback` flag in pilot and prod. Nothing in `config.py` refuses an llm `base_url` on loopback in pilot. So the T14 `[::1]` row loads, as the ticket says.
- Read `guard/http.py:105-115`: "must not point ... at a loopback name" is docstring guidance. The function connects a loopback name as it is and does not refuse it.
- Read `llm/openai_compat.py:40-60`: `floating()` returns True for a loopback host with a model id that has no `:`, and `make` passes it to `pinned(...)`. I did NOT read `pinned` (UNVERIFIED that it raises).
- Read `backends/factory.py:29-57`: `make` imports `entry.factory`'s module and has no logger. Read `table.py:28-29`: `FakeLLMSettings` has no `no_training` attribute (COR-4 holds).
- Read `config.py:360-363` (sibling): `ValueError(f"system {name}: base_url must be https ...: {system.base_url}")` prints the operator's raw URL, which may carry `user:password@` (PENDING LEAD 14).
- Counted: `tests/test_k3_pilot_env.py` has 11 matches for `pilot_cfg(`, including the `def` at :35, so 10 calls (COR-6 holds).

## Decisions

| id(s) | category | decision |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX (cut) | Cut `Config.no_training_max_age_days`, its ceiling constant, the T4 field and bounds rows, M13 and M28. The limit is the fixed constant 90 in `defaults.py`. Exact text in Build notes BN-1. The no-hardcoding question goes to PENDING LEAD 13. |
| R3-ADV-2 (Major) | PROPOSE FIX (cut) | Cut the `factory.make` log line, the `factory.py` edit, T11 and M16. The config file in version control is the record. Test ids go from 19 to 18. Exact text in BN-2. |
| R3-ADV-3 (Minor) | PROPOSE FIX (closed by the BN-2 cut) | T11 no longer exists, so its SDK claim goes with it. No other row calls `make`. |
| R3-ADV-4 + R3-COR-3 (Minor, Minor) | PROPOSE FIX | In (f), print an expected host only if it fullmatches the hosts pattern; print any other as `<host not usable in a statement>`. State the ASCII/punycode and 253-character limit in plain words. Add three T14 rows. BN-4. |
| R3-ADV-5 (Minor) | PROPOSE FIX | One sentence in "What the code does NOT check", the README and the CHANGELOG: port, scheme and path are not bound. No code. BN-5. |
| R3-ADV-6 (Minor) | PROPOSE FIX | M21 is "killed", but by a construction error before the equality runs. Add one direct assertion on field names. BN-6. |
| R3-ADV-7 (Minor) | PROPOSE FIX (no new mutant ids) | No mutant survives: the reviewer's own text names a killer for each of the four. Add one sentence naming the killers. Do not add M32-M34, because mutant surface is cut where it closes nothing (order 7(3)). BN-7. |
| R3-ADV-8 (Minor) | PROPOSE FIX | Name `re.fullmatch` (patterns without `^` and `$`) as the one mechanism for `reference`, `hosts` and the date. Add three trailing-newline T7 rows. BN-8. |
| R3-ADV-9 (Minor) | PROPOSE FIX | Add PENDING LEAD 12 (confirm "security"). My position: security is right, because the check masks nothing (see Positions). Either way the round cap is unchanged (Gate). |
| R3-ADV-10 (Nit) | PROPOSE FIX | Count line: write "T7 and T14 rows are not counted". BN-10. |
| R3-ADV-11 (Nit) | PROPOSE FIX | One sentence: if the runner has no "equivalent, stated" status, the evidence file records it by hand with the reason. BN-11. |
| R3-ADV-12 (Nit) | DECLINE | Keep `list[str]`. Nothing hashes the settings. A change would touch the type, T7 and the pattern code for no gain. Recorded for the build notes (BN-12). |
| R3-COR-1 (Major) | PROPOSE FIX | Catch the `ValueError` from `date.fromisoformat` and raise the fixed text. Add three T7 impossible-date rows that also assert the input is absent. Add one mutant (M32). The input-bearing text comes from the pure-Python fallback, not CPython's C path (Facts). BN-3. |
| R3-COR-2 (Minor) | PROPOSE FIX | "never holds" becomes "must not hold". Add a name to the stated tripwire gaps and the README. BN-9. |
| R3-COR-4 (Minor) | PROPOSE FIX (closed by the BN-2 cut) | The log line is gone, so no code reads `settings.no_training` on `fake`. `_no_training_refusals` returns early for DEV_ONLY pairs (ticket line 196), so it does not read it either. |
| R3-COR-5 (Minor) | PROPOSE FIX | One sentence on the T14 loopback row: it loads at config time, nothing in `config.py` refuses a loopback llm in pilot, `guard/http.py` only advises against it, and `floating()` marks a tagless model on loopback. Keep `pinned` behaviour UNVERIFIED. BN-13. |
| R3-COR-6 (Nit) | PROPOSE FIX | Line 101: "11 matches: the definition and 10 calls". BN-14. |
| R3-COR-7 (Nit) | PROPOSE FIX (closed by the BN-1 cut) | The T4 bounds rows (0, 180, 181) are deleted, so the inconsistency goes away. |
| R3-COR-8 (Nit) | PROPOSE FIX | Line 128: add "order 20(6) and order 16 supersede orders 6(b) and 8(1) for ticket rounds". BN-15. |

## Build notes (order 20): exact replacement text

Each item names ticket lines in revision 3. "Replace" means the whole named line or bullet. Mutant numbers are not reused: M13, M16 and M28 stay as "cut" lines.

BN-1 (R3-ADV-1, Major: cut the age-limit field)
- Line 161 replace: `  - `config.py`: `_utc_today`, `_no_training_refusals`, one call in `_cross_checks`. No new `Config` field.`
- Line 162 replace: `  - `defaults.py`: two constants.`
- Lines 190-193 replace with:
  `  - No `Config` field. The age limit is the fixed constant `NO_TRAINING_MAX_AGE_DAYS = 90` in its own block of `defaults.py` (the repo's "re-verify tool facts within 90 days", `tool-ladder-before-code.md`). No operator setting can raise or lower it, so the 90-day rule cannot be weakened from a config file. Beside it: `NO_TRAINING_FUTURE_SLACK_DAYS = 1` (an operator in IST can write tomorrow's UTC date). Changing either is a reviewed code change. Neither is in `config_hash`.`
- Line 195 replace: `  - `_no_training_refusals(environment: str, llm: KindSettings, today: date) -> list[str]` in `config.py`. It reads the limit from `defaults.NO_TRAINING_MAX_AGE_DAYS`.`
- Line 206: unchanged. `<m>` is now always 90.
- Line 234 replace "the field, `_utc_today`" with "`_utc_today`".
- Line 235 replace "three constants" with "two constants".
- Line 243 replace: `    - renewal every 90 days (fixed in v1; not a config setting);`
- Lines 305-311 (T4) replace with:
  `  - T4 (staleness; kills M3, M3b, M27). On `_no_training_refusals` with an injected `today`: age 90 passes, age 91 is refused. At load with `_utc_today` patched: age 90 passes and age 91 is refused. PIN: a top-level key `no_training_max_age_days: 30` is refused as an unknown key (`extra="forbid"`; it passes on old code and must keep passing).`
- Line 398 replace: `  - M13 cut (build notes BN-1: the field no longer exists).`
- Line 413 replace: `  - M28 cut (build notes BN-1: the ceiling no longer exists).`
- Fail-before table, row "T4 bounds (0, 180, 181)" replace: `| T4 unknown-key pin | passes (unknown key) | PIN |`. Line 464: add "the T4 unknown-key pin" to the list of pins.
- Line 473 replace: `  - The change is additive in code and in the config schema: one new optional field inside `backends.llm`.`
- PENDING LEAD 5 (line 524) replace: `5. (changed in build notes) A fixed 90-day limit with no config field and no ceiling, plus the `contract_terms` / `account_setting` / `self_hosted` vocabulary. Recommended: keep. A client that needs a different period is a v1.1 row (trigger: a client contract names a review period other than 90 days).` Its sub-bullets 525-526 stay.
- v1.1 list: add `- A configurable age limit (shorter or longer than 90 days). Trigger: a client contract names a different review period. Not built: a field an operator can raise weakens the studio's 90-day rule.`

BN-2 (R3-ADV-2, Major: cut the start-up log line)
- Line 105 replace "In the README, the CHANGELOG, the log line and the refusal texts" with "In the README, the CHANGELOG and the refusal texts".
- Line 112 replace "the log says "operator-attested"" with "the README and the CHANGELOG say "operator-attested"".
- Line 163 delete (`backends/factory.py`: one log line).
- Lines 213-218 replace with one bullet: `  - No start-up log line (cut in build notes, R3-ADV-2: it enforced nothing and `build(llm=...)` skipped it). The client's config file in version control is the record of the statement.`
- Line 236 delete. Line 251: add `backends/factory.py` to "NOT changed, on purpose".
- Line 262 delete (`FakeSecretProvider` and `make` (log test)).
- Line 276 delete (success log prints `reference`). Line 336 delete (T8 success-path log row).
- Lines 342-346 (T11) replace: `  - T11 cut (build notes BN-2).`
- Line 381 replace: `  - Count: 18 test ids: T1, T1b, T2, T3, T4, T5, T6, T6b, T7, T7b, T8, T9b, T10, T12, T13, T14, T15, T16 (T9a cut in revision 3, T11 cut in build notes). Fixed-size rows I counted: T1 8, T2 18, T3 3, T16 29; T7 and T14 rows are not counted.` (This also closes R3-ADV-10.)
- Line 401 replace: `  - M16 cut (build notes BN-2: no log line).`
- Fail-before table, row T11: delete.
- Line 501 (contested "three times per process"): append "Moot after build notes BN-2 (no log line)."
- PENDING LEAD 6 (line 527) replace the last clause with: "the client's config file in version control is the record (the start-up log line was cut in build notes BN-2). Revisit when P6a defines client-profile evidence."
- UNVERIFIED line 548 (T11 log capture): delete.

BN-3 (R3-COR-1, Major: impossible dates must give the fixed text)
- Lines 180-183 replace with:
  `    - `checked_on: date`. A `BeforeValidator` accepts only (a) a `datetime.date` that is not a `datetime.datetime`, or (b) a `str` that `re.fullmatch`es `[0-9]{4}-[0-9]{2}-[0-9]{2}` (ASCII digits only) and then parses with `date.fromisoformat`.`
  `      - The validator wraps that parse in `try`/`except ValueError` and raises `ValueError("checked_on must be a date written YYYY-MM-DD") from None`. This covers impossible dates such as `2026-13-45`, `2026-02-30` and `0000-00-00`.`
  `      - Reason: CPython's C `date.fromisoformat` raises fixed texts such as `month must be in 1..12` (checked on 3.12.3 and 3.13.18). The pure-Python fallback `_pydatetime` raises `Invalid isoformat string: '<the input>'` (checked on both). `hide_input_in_errors` hides the input field, not the message text.`
  `      - Everything else is refused with the same fixed text: numbers, digit strings, floats, `bool`, any datetime, an ISO datetime string, and non-ASCII digits. YAML `checked_on: 2026-11-05` (a date) and `"2026-11-05"` still load.`
- Line 318 (T7 `checked_on` refused list): append `"2026-13-45"`, `"2026-02-30"` and `"0000-00-00"`. For these three, the row also asserts that `str(ConfigError)` contains `checked_on must be a date written YYYY-MM-DD` and does NOT contain the input string.
- Mutation plan: add `  - M32 the `except ValueError` around `date.fromisoformat` removed: T7 impossible-date rows (on CPython the message becomes `month must be in 1..12`, so the fixed-text assertion fails).` Line 382 then reads "32 mutant numbers, M1 to M32; M13, M16 and M28 are cut, so 29 are run."
- Evidence step 0 (line 422, "the date rule"): append ", including `2026-13-45`, `2026-02-30` and `0000-00-00`, through the final validator and through `_pydatetime.date.fromisoformat`."

BN-4 (R3-ADV-4 + R3-COR-3)
- After line 203 add: `      - An expected host is printed only if it fullmatches the hosts pattern. Any other expected host is printed as `<host not usable in a statement>`, so a control character or an escape sequence in a `base_url` never reaches the error text or the terminal.`
- Line 178 replace: `      - That accepts every ASCII value the host functions can return (`::1`, short names, a Foundry resource with capitals or a 12-digit run). Limit, stated in the README: a host name must be ASCII (write an international name in its `xn--` punycode form in `base_url`) and at most 253 characters. An endpoint whose host is not can never match a statement, so pilot and prod refuse it (fails closed).`
- Line 208 replace: `    - The reference text is never put in a message. Hosts may be, in (f), but only in the pattern-checked form above.`
- T14 add three refused rows, each asserting `hosts do not match`, `<host not usable in a statement>`, and that the raw host is absent from `str(ConfigError)`: an openai_compat `base_url` with a non-ASCII host; a `base_url` host holding an ESC character (built from parts); a Foundry `resource` long enough that the host exceeds 253 characters.

BN-5 (R3-ADV-5): add to "What the code does NOT check", the README and the CHANGELOG: `- Port, scheme and path. The statement is bound to the host name only, so two endpoints on one host (two ports, or `/v1` and `/v2` on one gateway) share one statement.`

BN-6 (R3-ADV-6): T8 add: `- For every llm settings class in TABLE["llm"], the field named `no_training` exists where expected, and no field whose type is `NoTrainingStatement | None` has a name ending in `_secret_name` (read from `model_fields`, no object built).` M21's killer becomes "T8 (field-name assertion; the `secret_names()` equality as well)".

BN-7 (R3-ADV-7): add after line 416: `  - Weakenings checked against existing rows, with no new number: `environment != "dev"` changed to `== "prod"` (T1 pilot rows); the `if h` filter dropped from the expected set (T14 no-host row); the age subtraction reversed (T4); `self_hosted` added to the anthropic, bedrock or gemini set (T3).`

BN-8 (R3-ADV-8): after line 171 add: `      - Mechanism for `reference`, `hosts` and the date: Python `re.fullmatch` with patterns written without `^` and `$`. Never `re.match` or `re.search` with `$`, which accepts a trailing newline.` Line 171's pattern loses its `^` and `$`, and line 177's likewise. T7 add refused rows: `"2026-11-05\n"` (checked_on), `"llm.example\n"` (a hosts entry), and a valid reference followed by `\n`.

BN-9 (R3-COR-2): line 173 replace "It never holds" with "It must not hold". Line 273: append "; a person's or party's name that fits the character set also passes (the rule is written guidance for the operator, not a code check)". README (line 247): "must not hold a person's or party's name; the code does not check this".

BN-10: closed inside BN-2 (line 381).

BN-11 (R3-ADV-11): line 385 append: "If the runner has no such status, the evidence file records each equivalent mutant by hand with its stated reason, and it is never counted as killed."

BN-12 (R3-ADV-12, declined): record: "`hosts` stays `list[str]`; settings objects are not hashable and nothing hashes them. If a later package hashes settings, change the type to `tuple[str, ...]` (it also refuses a bare string)."

BN-13 (R3-COR-5): after line 357 add: `      - This row only proves the config loads. Nothing in `config.py` refuses a loopback llm in pilot. `guard/http.py:112-115` only advises against it. `llm/openai_compat.py:49` marks a model id with no tag on a loopback host as floating, and `make` hands that to `pinned()` (not read; UNVERIFIED whether it refuses). The README sample says a loopback `self_hosted` endpoint is for a model server on the same machine and needs a tagged model id.` Keep the README-loopback item in the UNVERIFIED list.

BN-14 (R3-COR-6): line 101 replace "`pilot_cfg(` appears 11 times in that file" with "`pilot_cfg(` has 11 matches in that file (the definition at :35 and 10 calls)".

BN-15 (R3-COR-8): line 128 append: "Order 20(6) and order 16 supersede orders 6(b) and 8(1) for ticket rounds."

## Positions
- ADV-1 and ADV-2 are cuts that close findings without adding design (order 7(3), order 8(1)). Neither cut loses a safety property. The field could only move the limit (up to 180, which weakens the 90-day rule, or down). The log line enforced nothing and had a known bypass (`build(llm=...)`).
- What is lost, stated: an operator who wants a stricter 30-day period cannot set one in v1 (v1.1 row). Nothing in the process output shows which statement is in force; the config file shows it.
- COR-1: the reviewer's premise "can carry input text" is false on CPython's C path and true on the pure-Python fallback (Facts). Either way the ticket's own contract ("every validator message is a fixed text", line 166) is not met without the catch, so the fix stands. The leak value is low: the input is a date-shaped string, not a secret.
- ADV-9: "redaction" in the studio's sense is masking data before it reaches a model, log or audit trail. P6b1 masks nothing: it refuses a start-up. Its class is "client-profile gate", which is security. The lead decides (PENDING LEAD 12). The answer does not change the round cap, because round 3 had 3 Majors.
- ADV-7: no surviving mutant was shown, so no new mutant numbers. One sentence naming the killers closes it.

## Couplings
- BN-1 and BN-3 both change the mutation-plan header (line 382): 32 numbers, 29 run.
- BN-2 and BN-10 both rewrite line 381. BN-2's text already includes the BN-10 fix.
- BN-4 depends on BN-8: "fullmatches the hosts pattern" means `re.fullmatch` with the pattern without anchors.
- BN-1 touches `defaults.py`. It goes from three constants to two, in P6b1's own block (order 20(5)).
- BN-2 removes `backends/factory.py` from P6b1's files. PENDING LEAD 2's hot-file amendment no longer needs any entry for `factory.py` (it had none).
- The build-start review (order 19 A) should be told the three Majors and BN-4, so it checks the merged reading of body plus build notes.

## PENDING LEAD (continuing the ticket's numbering; 1-11 stand, 5 and 6 changed by BN-1 and BN-2)
12. Path class (R3-ADV-9). Recommended: keep "security". The package refuses a start-up and masks nothing. If the lead chooses "redaction", order 20(6) still gives no extra ticket round, because round 3 had 3 Majors. RESULT review stays uncapped either way.
13. No config field for the age limit (R3-ADV-1). The studio rule says thresholds "come from validated config in one place". Recommended: the constant in `defaults.py` meets that rule, as the existing constants there do (order 8(2) put MAX_USD there the same way). A config field here could only be used to weaken the 90-day rule. If the lead reads the rule as requiring an operator field, restore the field with `le=90` (shorter only) instead of a ceiling of 180.
14. (new; sibling found while resolving, not a P6b1 defect) `config.py:360-363` puts a system's raw `base_url` into the `ConfigError` text. A URL written with `user:password@` would be printed. Recommended: P6b2 (the secret-boundary package) owns it: print the scheme and host only, with a canary test row. It is a found defect, so it is never dropped (order 7(3)). The lead logs it in the ledger.

## Counts
- Findings: 20 (Majors 3, Minors 11, Nits 6; no Blocker).
- Decision rows: 19 (ADV-4 and COR-3 share a row).
- PROPOSE FIX: 19 findings, of which 2 are cuts (ADV-1, ADV-2) and 3 are closed by those cuts (ADV-3, COR-4, COR-7).
- DECLINE: 1 (ADV-12). CONTEST: 0. ESCALATE: 0.
- Majors: all 3 get a fix, with exact text in BN-1, BN-2 and BN-3.
- Net surface: tests go from 19 to 18 ids; mutants run go from 31 to 29 (M13, M16 and M28 cut; M32 added); one config field, one constant, one file edit (`factory.py`) and one logger removed; one caught exception and about 10 test rows added.
- New PENDING LEAD items: 3 (12-14).
- Round: no round 4 (Gate). Freeze revision 3 plus these build notes.
