# P5c round 3, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

REVIEW R3 correctness, P5c rev 3 (money/redaction). Verdict: 0 Blocker, 3 Major, 5 Minor, 2 Nit. This review had no shell, only Read/Grep/Glob. So I ran NO python3 -I probe and NO script, and I could not run `git show 124258b:`. Counts came from Grep plus hand tally. Disk `src/` is not 124258b: the runmap.py lines on disk are about 47 lower, which the ticket itself says. Cites of the form `redact.py:N`, `agent_loop.py:N` and others match disk exactly. Ticket line numbers are the ticket's own, from the Read output.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 348, 349, 536 | `evals.py:109` calls `judge.qualify(JudgeDetector(llm,...))`. That calls `injection_check(judge, ...)` (`judge.py:107`), which calls `self.llm.chat` (`judge.py:72`). This is outside any per-(case,k) `llm.run(...)`. After P5c-3 the wrapper raises `SessionClosed` (T2-11). P5c-3 also makes `injection_check` re-raise `RedactionError` (line 350), so `gate` crashes for every agent with an `llm_judge`. The ticket names no run for judge qualification. No row or mutant covers it. | Say that `gate` opens one run, with a fixed id and the code identity "gate", around `judge.qualify`. Add a row, e.g. T3-10c "judge qualification runs inside a run". Add a mutant. |
| R3-COR-2 | Major | 294, 348, 505 | (a) The table says the gate's `redact_untrusted` at `evals.py:63` "STAYS ... over the run's session". But `redact_untrusted` takes a plain dict (`runmap.py:298`), the session is not a dict, and T1-17 bars `_map_of` outside `redactor.py`. The gate has no plain map, so it must call `llm.redactor.mask(..., ctx.session, untrusted=True)`. The same change breaks the `producers.py:40` row and its AST test, which look for `redact_untrusted` in `gate`. Row T3-17 does not say how. (b) On disk the document is escaped ONCE per case, before the k loop (`evals.py:60-63`), with `{}`. Fresh sessions per (case,k) force the escape into the k loop. T3-10 says "fresh per case". (c) `evals.py:64-70` turns every `RedactionError` into `ConfigError` (exit 2). `decode_document` raises `RedactorRefusal`, a `RedactionError`. That contradicts line 348, "counts as FAILED with reason `unsupported_input`", and T3-05b. | State the exact call. Fix the T3-17 expectation for the row at `producers.py:40`. Say whether the session is per case or per (case,k). Add an explicit `except RedactorRefusal` before the `ConfigError` branch, with T3-05b pinned to it. |
| R3-COR-3 | Major | 338-339, 505 | The run loop's chat call (`agent_loop.py:425-439`) catches only `ProviderError`. The ticket adds only `AuditUnavailable` there. Wrapper refusals (`forged_mark`, `self_check_failed`, `session_closed`, `unsupported_input` for non-text blocks) are `RedactionError`s and are not caught at that site. They would leave `handle` as an uncaught exception, with the run stuck in WORKING. The new `_screen` catch does not cover this. T3-13 covers only audit-down. | In the chat block, catch `RedactionError` and route it to `_redaction_failed` (`:547`). Add a row (wrapper raises `forged_mark` at chat, ends NEEDS_PERSON `redaction_error`, one inner call fewer). Add a mutant. |
| R3-COR-4 | Minor | 356, 501, 513 | Existing tests set the model after construction: `rt.llm.chat = ...` (`test_p5_llm.py:56`, `:168`; `test_p5p6_followups.py:102`; `test_p1a_fixes.py:35`) and `rt.llm = ScriptLLM(...)` (`test_k5_tools.py:608`). These bypass or replace the mandatory wrapper after the `isinstance` check. The "floor" grep `\b(Runtime|gate|extract|JudgeDetector)\(` cannot find them. T3-06 tests only constructors. | Add `git grep -n -E 'rt\.llm( |\.chat) ?='` to the evidence list. Decide: read-only `llm` property on `Runtime`, or the test patches `rt.llm.inner`. |
| R3-COR-5 | Minor | 10, 18 | In-ticket contradiction. Line 18 gives `redact_text` at :464 (the def). Line 10 puts the NFKC second pass at `runmap.py:464-475`. On disk the def is at 417 and the second pass at 452-471, so the second pass at 124258b is near 499-518 (UNVERIFIED, offset only). The NAME-DECOMPOSED argument rests on this cite. | Re-cite as about `:499-518`, after `git show`. |
| R3-COR-6 | Minor | 337, 493 | T3-05 asserts "`received` then the `guard`/`document` `stopped` event". Between them the run writes `state` WORKING (`agent_loop.py:350`; `test_s5_runtime.py:137` pins `[:2] == ["received","state"]`). Say "in order, as a subsequence". Also the new `unsupported_input` handler must sit before `except Exception` at `:376`, or it becomes `redaction_error`. `GUARD_STOP_REASONS` (`:83`) is not addressed, so `caught_by` for `unsupported_input` is unstated. | Add a sentence on where the handler sits, and on whether `unsupported_input` joins `GUARD_STOP_REASONS`. Reword T3-05. |
| R3-COR-7 | Minor | 287, 281-284 | The wrapper may add placeholders on pass 1 or 2 of a chat call. Map saves in the run loop happen only at `:363, :379, :475, :498, :648`, and none follows a chat. `:379` says "before anything is sent: a crash now loses no placeholder". A wrapper-minted placeholder that the model then uses in a plan is not in the stored map unless `_submit` saves it (`:648` runs only if `validate_proposal` is set). | Either say `_submit` saves the map unconditionally, or save after each chat. Add a row. UNVERIFIED which path is real. |
| R3-COR-8 | Minor | 246-248 | The ticket gives no regex text for `_ACCT_STRONG`: only "any characters up to the digits". If a builder writes a trailing `.*`, behaviour on parenthesised qualifiers (`_BANK_KV` allows `Account (number):`) is undefined. ACC-2-NEG has no parenthesis case. | Give the body (the table's forms only, then end of slice) and add the case `Account (no): <8 digits>` to ACC-2-NEG. |
| R3-COR-9 | Nit | 97, 8 | `python3 --version` = "Python 3.13.18" and the F10 probe results are the author's. I could not run them. The comment cite `judge.py:68-69` is at lines 69-70 on disk. | UNVERIFIED. Fix the cite. |
| R3-COR-10 | Nit | 170-183 | Template says the Problem field is 3-5 sentences with no unexplained jargon. The field holds 4 numbered points plus 5 bullets and uses "fingerprint", "session" and "kind". | Shorten, or point to the Words section. |

**ACC-2 / M50 trace.** Confirmed by reading `redact.py`. UNVERIFIED by run.
- Pattern 1 (`:333-336`) is `(?i)` + `_NOT_IN_WORD` + optional `bank ` + `_ACCT_WORD` + `_BANK_KV` + `_ACCT_DIGITS`. The only capturing group is group 1, inside `_ACCT_DIGITS` (`:86-89`). `_NOT_IN_WORD`, `_BANK_KV` and `_ACCT_WORD` hold only `(?:...)` groups. So `m.groups()` is `(digits,)` and `_mask` (`:929`) takes the digits.
- The gate (`:939-941`) is `_CARD_SHAPE.fullmatch(original) or not (bank_near or _bank_context(m))`. Without a bank word, `_bank_context` (`:107-113`) is false today, so `m.group(0)` is returned unchanged. The ticket's OR-ed clause `_ACCT_STRONG.match(m.string, m.start(), m.start(1))` has valid `Pattern.match(string, pos, endpos)` semantics. It reads only the keyword and key-value text before the digits.
- Masking: `m.group(0).replace(original, placeholder)` (`:956`) leaves the keyword. The digits are replaced.
- Map: `_place` (`:958-971`) adds exactly one entry for BANKACCT. BANKACCT is not in `SECRET_KINDS` (`:1140-1156`), so no extra "piece" entries. The text is ASCII with none of `\%&`, so there is no second pass. So ACC-2's three assertions (digits gone, keyword kept, one BANKACCT entry equal to the digits) hold.
- M50: a group around `_ACCT_WORD` makes `groups()` = `(keyword, digits)`, so the keyword becomes `original`. `m.start(1)` equals the match start, so the slice is empty and the new clause is false. With no bank word, `m.group(0)` is returned and the digits stay in clear. ACC-2 (no bank word) fails on "digits absent". Killer named correctly.
- ACC-12: BANKACCT (`:333`) runs before ACCOUNTID (`:353`), so `Account No: <12 digits>` becomes BANKACCT. On base the context test fails, the match is left alone, and ACCOUNTID takes it, so ACC-12b is a real fail-before.

**Verified** (Read/Grep, on disk)
- Template: all 17 fields are present, in order.
- Sub-PRs: 4.
- Test rows by Grep tally: 16 + 14 + 17 + 32 + 12 = 91 (T1-03, T2-12, T3-08 and T4-06 are cut; T3-15a..f count as 6). T2-P gives 92. Strict xfail: 4 (ACC-1a, ACC-1b, ACC-3, NAME-NONASCII-INITIAL).
- Mutants: 19 + 15 + 11 + 5 = 50. Every named killer exists as a row. T2-15c is a case inside T2-15.
- ACC-2 case count: 16 + 2 + 16 + 1 + 8 + 16 = 59. ACC-2-NEG: 4 weak forms + 1 = 5.
- PENDING LEAD numbering is contiguous, 1 to 33. 24-33 are the new ones.
- Test and grep counts:
  - 14 files for `config_hash|qualified\.jsonl`.
  - 21 files for `config_hash|qualified`.
  - 42 lines in 20 files for the raw-model grep.
  - 62 `"pilot"|"prod"` hits in 13 files.
  - 10 golden inputs plus `tests/fixtures/golden/test-agent.jsonl`.
- `redact.py` cites: `:82`, `:93-94`, `:107-113`, `:333-336`, `:339-349`, `:353`, `:444`, `:447`, `:476`, `:925-956`, `:929`, `:939-941`.
- `agent_loop.py` cites: `:87`, `:201`, `:229`, `:269-284`, `:295`, `:310-316`, `:349`, `:352`, `:354`, `:361-377`, `:367`, `:387`, `:425`, `:520`, `:547`, `:569`, `:794-797`. Every listed plain-map line `:363` to `:648` is a real `rmap` use.
- Other source cites that match disk:
  - `defaults.py` `STORED_KINDS` :108-122 (13 kinds, 12 after PHONE), `MAX_REDACT_CHARS` :38, `MAX_BUNDLE_CHARS` :40, `CUT_MARGIN` :44, `REDACT_BUDGET_S` :49.
  - `config.py:215`, `:256`.
  - `cli.py:120`, `:150`, `:216`, `:221`.
  - `app.py:162`.
  - `registry.py:105` (config_hash exempts only `levels` today).
  - `tools.py:936`, `:976`, `:1162`, `:1178`.
  - `extract.py:11`, `:46-52`, `:58`.
  - `evals.py:63`, `:73`.
  - `judge.py:71`, `:72`.
  - `injection.py:89-101`.
  - `k1b/loop.py:94`, `:104`.
  - `k1b/audit_sink.py:35`, `:59`.
  - `audit/protocol.py:19`.
  - `limits.py:50`.
  - `producers.py:28`, `:29`, `:40`, `:55-65`.
  - `table.py:92`, `:386`, `:388`, `:570`, `:582`, `:593`.
  - `test_lockin_guard.py:381`.
  - `test_s5_runtime.py:137`.
  - `conftest.py:58`.
  - PHONE end `(?![\w.])` at `:476`. Unchanged 17+ digit behaviour holds by reading.
- Orders 20 item 6, 22 items 22/24/27/30, 24 item 39, 25 item 4 and 26 item 2 are paraphrased accurately.
- `handover/owner-visible-limits.md` does not exist, as the ticket says.
- `_map_of` AST-restriction logic and the claim that `restore` takes a plain map are internally consistent.
- NAME-CAPS: `Dear MARY`, `Dear ALL` and `Dear JohnSmith` do not match the base `[A-Z][a-z]+`. The new class matches whole words by reading.

**Not checked**
- Anything needing a run: probes (a) and (b), `python3 --version`, every test, mutant and fail-before claim, the new `_bank_context` clause.
- All `git show 124258b:` / `ce70eb5` claims: the runmap cites `:98`, `:340`, `:345`, `:384`, `:464`, `:588`, `:607`, `runmap.py:532-540`, and the PHONE `748849c` lines. Disk runmap lines (:53, :293, :298, :337, :417, :541, :560) are offset 45-47, consistent with the ticket's offset claim but not proven.
- C1a branch `8460813` lines, the C1 ticket and the FROZEN amendments text, `amendments.md` details (only grepped), order 11(5), designs, P1/P2d/P4b1/P4c/P5a/P5b3 ticket cites, and `_RunEnded`.
- `tests/test_p5c*`, mutants, and anything under `handover/reviews/` or `handover/evidence/` (deliberately not read).
- Whether any audit reader flags an intent-only `outbound` row. Whether `tools.py` importing `guard/redactor.py` creates a cycle. FakeLLM recording rename count. `demos/` grep, MANIFEST rows.