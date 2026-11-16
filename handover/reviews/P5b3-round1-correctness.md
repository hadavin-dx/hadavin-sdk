# P5b3 round 1, correctness review (ticket revision 1)
Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

TICKET REVIEW round 1, CORRECTNESS, P5b3 (read-only). Verdict: no Blocker, 6 Majors, 8 Minors, 3 Nits. Fix the Majors before this ticket is frozen.

Basis and limits. I read the four listed handover files and the ticket in full, and every cited line in `src` and `/tests`. I have no git and no way to run anything, so I could not tell whether the on-disk tree is `cd2243f`. Where a cite is wrong on disk, that may mean "current main differs from the cited commit"; the ticket itself says `tools.py` and `runmap.py` changed after `ce70eb5`. I did not read `handover/reviews/` or `handover/evidence/`.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R1-COR-1 | Major | 123, 182, 287 | `_message` is deleted, but 5 tests call `tick_mod._message(...)` directly: `tests/test_k5_round7.py:42`, `tests/test_k5_fixes3.py:120`, `tests/test_k5_round8.py:73`, `tests/test_k5_round9.py:196` and `tests/test_k5_round12_fuzz.py:132`. The ticket names only round8 and round9. Round7, fixes3 and round12_fuzz are missing from the change list and from evidence command 1. `test_k5_round7.py:41` and `test_k5_fixes3.py:112` test the function's behaviour, so "no deleted tests" needs a replacement for each. | List all 5 files and their tests in "Change". Add them to evidence command 1. Say what replaces `test_k5_round7.py:41` and `test_k5_fixes3.py:112`. |
| R1-COR-2 | Major | 130 | Moving the three rows out of `PRODUCERS` breaks two tests the ticket does not name. (a) `tests/test_k5_producers.py:98-107` (`test_every_module_that_calls_a_model_is_registered`): `extract.py` is in `MODEL_CALLERS` and is registered only by the row "extract validation errors" (`guard/producers.py:36`). Without that row, `extract.py` is "unexplained" and the test fails. The row is not in `OUTSIDE_THE_CHOKE_POINT`, and `extract()` is not a pure diagnostic writer, since its retry prompt still carries `reply.text`. (b) `tests/test_k5_round9.py:204` asserts `set(DRIVERS) == {r[0] for r in PRODUCERS}`, so removing 3 rows desynchronises it. The ticket says only that the assertions change. | Say how `extract.py` stays registered, either by keeping a `PRODUCERS` row for the model-bound `reply.text` path or by adding it to `OUTSIDE_THE_CHOKE_POINT` with a reason. Say that the key set at `test_k5_round9.py:204` is adjusted to match the new `PRODUCERS`. |
| R1-COR-3 | Major | 101, 109, 290 | The expected CSV count contradicts itself. Line 101 says the 13 class-name rows are "not locked to FOREIGN" and become `OPERATOR`. Line 109 says the 5 rewritten rows drop out. Line 290 then says "FOREIGN must drop by 5". If P5b2's reviewed baseline has the 13 as FOREIGN, FOREIGN drops by up to 18. If they are already OPERATOR, the generator rule and mutant M9 do nothing. | State P5b2's baseline label of the 13 rows and give one number, with the arithmetic. If it is UNVERIFIED, mark it so and tie it to `P5b2` revision 2. |
| R1-COR-4 | Major | 88, 103 | `from_cause` passes `key=f"backends.{cap}"`, which contains a dot. Line 88 says `token40` "allows letters and digits". By the ticket's own description the key is always dropped and counted in `dropped_facts`. The `key` fact then carries nothing for the main backend-settings case, and no test row would show it. | Confirm `token40`'s charset against P5a (mark UNVERIFIED if not read). Pass `key=cap` only, or require `token40` to allow `.`. Add a test row for this call. |
| R1-COR-5 | Major | 113-114, 184, 316 | The operator-visible change is understated. Rule 2 of `_refusal_text` accepts only 1-400 printable-ASCII characters; everything else becomes `render(diagnose(exc))`. Many LITERAL ConfigErrors are long joins: `registry.py:215` and `:227` (`"; ".join(...)`), `config.py:443`/`:445`, and the `config.py:373` and `:358` messages. A join of several problems can pass 400 characters or carry a non-ASCII value. These operators lose the actionable text and get a code-only line. CHANGELOG line 184 and rollback line 316 say only "`refused:` text for 5 places change". Decision 5 (line 334) names the backstop but not this cost. | Measure how many existing LITERAL messages exceed 400 characters or contain non-ASCII (UNVERIFIED now). Either raise or split the cap, or truncate and then print, or add the cost to the CHANGELOG, the v1.1 rows and PENDING LEAD 5. Add a test row for a long `"; ".join` problem list. |
| R1-COR-6 | Major | 46-56, 330 | "Depends on (merged first)" omits P4b1, P4c and P4a. Amendment A4 says "P4b before P5b3 before P5c; P4c after P4b and before P5b3". F6 puts P4b1 on `config.py`, P4c on `registry.py` and `agent_loop.py`, and P4a on `llm/anthropic.py` (P4a, P5b1, P5b3, P6b1), all of which P5b3 edits. The ticket names them only as hot-file co-owners. The merge-order text (line 52) never places P4b1 or P4c. | Add P4b1 and P4c, and P4a for `llm/anthropic.py`, to Depends and the merge order, or say why A4's order is not needed. |
| R1-COR-7 | Minor | 137, 325 | "6 of the 21 messages interpolate values" is wrong. I count 11 interpolating `raise ValueError` lines: `backends/table.py:60` and `:279`, and `config.py:254`, `:257`, `:266`, `:272`, `:292`, `:354`, `:358`, `:361`, `:373`. The count of 11 (`config.py`) + 10 (`backends/table.py`) = 21 is correct. | Correct 6 to 11 in the ticket and in v1.1 row V5. |
| R1-COR-8 | Minor | 135 | `config.py:43` (`_money`) is a plain helper, not a validator body. It is one of the 11 `config.py` lines, so "11 lines in validators" is not exact. The ticket already marks this UNVERIFIED (line 350), but the count is attached to a validator list. | Say "10 in validators plus `_money`" and check how `_money` is called. |
| R1-COR-9 | Minor | 61 | "agent and principal models in `registry.py:34-59`": that range holds `Budget`, `AgentRecord` and `Chain`. `Principal` is at `identity.py:10-11` and `ActionContract` at `actions/contract.py:47`. The claim that none sets `hide_input_in_errors` is true (`config.py:52` is the only one named that does). FB1 uses a principal, so cite `identity.py`. | Change the cite to `registry.py:33-62`, `identity.py:10-11` and `actions/contract.py:47`. |
| R1-COR-10 | Minor | 150, 144 | The cite `guard/runmap.py:523` is a docstring line of `redact_value`. The raise that carries a class name is `runmap.py:476` (`raise RedactionError(type(exc).__name__)`). Line 527 raises `InputTooLarge("InputTooLarge")`, which has no foreign text. The sweep and the "Verified" claim (line 344, "every `file:line` cite") are therefore off here. This may be drift from `cd2243f`. Line 100 also calls `evals.py:67`'s `{exc}` "our own RedactionError", but its text is a foreign exception class name from `runmap.py:476`, so the sweep must fix `runmap.py:476` first. | Cite `runmap.py:476`. Add the order dependency (fix `runmap.py:476` before relying on `evals.py:67`'s text). Re-check against the real base. |
| R1-COR-11 | Minor | 144, 150 | `tools.py:620` (`raise ToolRefused(f"HTTP {code}")`) is counted as a raise hit in the 24, and line 144 also puts `int` on the SAFE list "because of `tools.py:620`". But `code = exc.code` is an attribute, not `int(...)`. `.code` is not in the TEXT forms (line 141), so the guard would not flag it, and `int` would not be needed. | Remove `tools.py:620` from the 24 hits, or make `code` an `int()` call and keep `int` on SAFE. Fix the count to 23 if removed. |
| R1-COR-12 | Minor | 150, 344 | `llm/retry.py:99` and `:101`: `describe(exc, detail)` builds `type(exc).__name__` at `retry.py:79`, and the raises are `:99` and `:102-103`. The cite does not match the lines. UNVERIFIED anyway, since P5b1 owns this file. | Cite `retry.py:79` plus the raises at `:99` and `:102`. |
| R1-COR-13 | Minor | 52, 309, 330 | PENDING LEAD 1 ("S0 EXIT for lane R not given") is answered by ORDER 21 item 17. That order says the standing S0 EXIT of order 20 applies to P5a, P5b1 to P5b5, P5c and the others, each effective after its freeze and its build-start review. | Close PENDING LEAD 1 with the order 21(17) cite. Keep the build-start review as the gate. |
| R1-COR-14 | Minor | 53, 341 | Line 53 lists `codes.py (P5a, P5b1, P5b3, P5c)` as a hot file "(A4, F6...)". Neither A4 nor F6 lists `codes.py`, and PENDING LEAD 12 adds it. `src/hadavin_sdk/codes.py` does not exist on disk, so P5a creates it. | Move `codes.py` to the "not in F6" group on line 54. Say P5a creates it. |
| R1-COR-15 | Minor | 58-66 | Template field 4 asks for 3-5 plain sentences. The ticket gives a lead sentence and 6 bullets with function names and line numbers. | Cut to 3-5 sentences. Move the detail to Interface. |
| R1-COR-16 | Nit | 243 | "args[0] ... at most 400 plus the summary length": the real bound is `len(summary) + 3 + 400`, because the template is `"{summary} ({render})"`. | State the exact bound. |
| R1-COR-17 | Nit | 186 | "10 lines in 5 files" for `grep -rn -E "error_kind=\|refused: \|tick: config error\|last_error" tests`. I get 10 lines in 6 files (`test_store.py` 2, `test_p7_tick.py` 4, `test_k5_round5.py`, `test_k5_round12_fuzz.py`, `test_p1b_backends.py` and `test_k1b_cli.py` 1 each). "20 test files reference `_message`, `safe_head` or the producers table" matches only the noisy pattern; it includes `log_message` fakes in `tests/fixtures`, `tls_support.py` and `contracts/vault_fake.py`. | Say 6 files. Narrow the pattern for the second count, or drop it. |
| R1-COR-18 | Nit | 39-41 | "Extended review (no round cap): yes", while the ticket-review cap is 3 rounds plus one (order 20 item 6). The text covers both, but the header could read as uncapped ticket review. | Write "no cap on result review; ticket review per order 20(6)". |

Verified (read on disk; hash and commit-history claims excluded):
- All 17 template fields are present and in template order.
- Counts that match:
  - 27 mutants (M1-M27) and 8 fail-before rows (FB1-FB8).
  - The 13 class-name places: 2+1+1+1+2+2+1+1+1+1.
  - 13+5 = 18 places; 17 direct plus 1 derived (`tools.py:120`).
  - 171 `ConfigError(...)` constructions: grep gives 172, one of which is the class definition.
  - 48 `type(x).__name__` or `__class__.__name__` lines in 24 files.
  - 11 `raise ValueError` in `config.py` and 10 in `backends/table.py`.
  - Sink-hit counts: 11 log, 6 print, 3 `reason=` and 1 audit; the 24 raise hits add up arithmetically.
- Cites confirmed:
  - `cli.py`: 75, 78-83, 191-200, 205, 268-269, 300-308.
  - `tick.py`: 73, 207, 284-292, 316-317, 324, 328-329, 343, 345, 356, 363.
  - `extract.py`: 57-64.
  - `guard/injection.py`: 92-96.
  - `guard/producers.py`: 30-37, with 4-tuples and `"tick error message"` pointing at `_message`.
  - `approvals/receiver.py`: 62-63.
  - `registry.py`: 179-180, 224. `config.py`: 52, 120, 413, 454.
  - `llm/anthropic.py`: 56. `tools.py`: 120, 397, 620.
  - `app.py`: 192. `slack_channel.py`: 177. `agent_loop.py`: 567.
  - `requests.py`: 118-121, 187-188, 225-228. `k1b/loop.py`: 100, 187, 194. `chain.py`: 213, 316, 331.
  - `local_dir.py`: 108.
  - `tests/test_p7_tick.py`: 110, 112. `tests/test_k5_round5.py`: 589.
- Other facts confirmed:
  - `StoreUnavailable` subclasses `ConfigError` (`store/protocol.py:41`), so `cls` return keeps exit code 4.
  - `is_connectivity_error` exists at `store/protocol.py:29`.
  - `ConfigError` is a `ValueError` (`errors.py:4`).
  - `registry.py`'s `_yaml` goes through `config.load_yaml`.
  - `hide_input_in_errors` is absent in the registry, identity and contract models.
- Order and amendment cites match:
  - Order 20(4) and (5), order 20(6) round cap, F8's `DeadLetter.errors` fail-before (FB4), and F6 for `errors.py`, `cli.py`, `registry.py`, `app.py`, `store/postgres.py` and `agent_loop.py`.
  - The merge-order chain wording.
- No real-looking secrets or tokens in the ticket; canaries are described as built from parts.

Not checked (UNVERIFIED):
- Commit shas, git history ("src changed only in guard/http.py, guard/runmap.py, tools.py"), and whether the on-disk tree is `cd2243f`.
- The PyYAML 6.0.3 and pydantic 2.14.1 probe claims. I did not run them.
- P5a, P5b1 and P5b2 names and behaviour: `token40` charset, `class_name_of`, `validation_text`, `tainted_names` and the corpus row ids. I did not read those tickets; the reviews are off limits.
- That pydantic exposes the raised exception as `ctx["error"]`, and that each of the 21 validator lines is reached via a pydantic validator.
- The driver structure in `test_k5_round8.py` and `test_k5_round9.py`.
- The taint-guard hit totals, since no guard exists yet, and the 8-12 h estimate.
- Whether `tools/gen_config_error_sites.py`, `tests/data/config_error_sites.csv`, `codes.py` and P1m's runner exist. They are absent on disk and arrive from other packages.