# review-code-F-gate-2 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# Result review round 2 of 3: cloud/core-c gate, run map, redactor (read-only, nothing executed)

## Verdict
No Blocker remains. Two Majors remain, so this is not yet clean:
- **MJ1:** ORDER 013 is not in the files on disk.
- **MJ2:** `enforce_map` is not idempotent for one input shape, and what is sent then holds a known identifier raw and standing alone.

The round-1 Blocker (B1) and Majors M1 to M4 are fixed in the code as read. Every statement below comes from reading; no test, mutant or timing run was done.

## What I reviewed
Worktree `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-c`, each file read once in full, as on disk at the time of reading:

| File | Lines |
|---|---|
| `src\hadavin_sdk\guard\model_gate.py` | 346 |
| `src\hadavin_sdk\guard\runmap.py` | 786 |
| `src\hadavin_sdk\guard\redact.py` | 1305 |
| `tests\test_model_gate.py` | 1468 |
| `tests\test_runmap_enforce_map.py` | 342 |
| `tests\gate_mutants.py` | 183 |
| `tests\test_redact_context_after_sweep.py` | 345 |
| `tests\test_runmap_is_masked.py` | 419 |

Also read: ORDERS.md (all), the round-1 report, `ii_meter.py` and the interfaces README, ESCALATIONS.md lines 1-16, `llm\common.py` lines 80-108, and grep hits in STATUS-BOARD.md and `tools\mutation_runner.py`.

Baseline `sdk-main` was only grepped, not diffed:
- `runmap.py` on main still has `mapping.clear()` at :524.
- `redact.py` on main has no `settle`, `_CONTEXT_*` or `ContextNotSettled`.
- `redact.py` grew from 1256 lines (round-1 count) to 1305, which matches the G7 additions being the only change. This is not a byte comparison.

## Round-1 findings

| Finding | State | Evidence |
|---|---|---|
| B1 gate refused on pattern hits | FIXED | `model_gate.py:233-237` and `:288-326` enforce by replacement through `runmap.enforce_map` (`runmap.py:588-639`). With `mapping=None` there is no enforce step (`:303`, `:316`). `worst_case` gets the enforced copies (`:239`). The old refusal tests and the two strict expected-failures are gone; trap tests are at `test_model_gate.py:505-558` and `test_runmap_enforce_map.py:148-217`. |
| M1 test that cannot fail | FIXED | The guard walks the syntax tree of the whole module (`test_model_gate.py:1175-1243`). Nine planted leaks prove it can fail (`:1245-1273`), plus mutants G7a to G7e. Small holes are listed under m-new-6. |
| M2 settle rule | FIXED | `model_gate.py:255-276` follows ORDER 011: (a) usable cost is settled; (b) only an error marked refused-before-response is settled at 0 (`:134-140`); (c) everything else is not settled. Rule (b) cannot fire today because no adapter sets the mark (`test_model_gate.py:801-817`); that matches the order. |
| M3 no mutant script | FIXED as a file | `tests\gate_mutants.py` has 27 mutants in the ORDER 008 format. The board records "12 of 12 good" for an older version; the current 27 are not shown as run. |
| M4 live map cleared | FIXED | `runmap.py:536-539` has no `clear()`. Tests: `test_runmap_enforce_map.py:276-342` (the one at `:292` is deterministic; the thread one at `:304` is probabilistic). Mutant R3 pins it. |
| m1 timeout | FIXED | Not settled (`model_gate.py:263-265`). |
| m2 paid call written as failed | FIXED | `:278-286`. |
| m3 reservation id in the row | FIXED | `:342`. |
| m4 reason allowlist | FIXED | `:117-119`, `:242-244`. |
| m5 bad cost | FIXED | `:143-148`, `:269-273`, tested at `test_model_gate.py:855-895`. |
| m6 misnamed test | FIXED | `test_model_gate.py:469`. |
| m7 is_masked shapes | PARTLY | Shapes A and B are added (`test_runmap_is_masked.py:360`, `:390`). `is_masked` now has no caller in `src`; ORDER 011 offered dropping it. Deleting it and its 419-line test file is the smaller choice. |
| m8 cache read outside the try | FIXED | `runmap.py:504-510`, tested at `test_runmap_is_masked.py:408`. |
| m9 producers row | Not on this branch | Arrives with core-b's install. |

## New findings

### Major

**MJ1. ORDER 013 is not built.** `redact.py:704-718`, `:955-972`; ESCALATIONS.md:3 says E5 is "NOT fixed".
- What is on disk is the narrow ORDER 012 fix: only the two BANKACCT patterns run again after the sweep.
- E5 is still open. A known value followed by a short tail after `Bearer` leaves the tail readable after one pass (`Bearer <SECRET_1>xy`). By my reading the tail can be up to 7 characters, not 2: the value is 4 or more, and value plus tail is under 12.
- There is no property test over the hostile and fuzz corpora (`redact(redact(x)) == redact(x)`, and no map original raw in the output). There is no list of strict expected-failures for what still fails.
- `test_redact_context_after_sweep.py:203-223` claims the table has no other pattern that depends on a placeholder. Its filter only looks for patterns that name a placeholder; it cannot see patterns whose value class admits `<` and `>` (BEARER `redact.py:403`, BASIC `:405`, authorization `:488`), which is the E5 class.
- ORDER 013 says "one extra pass, never a loop". `settle` is a loop of up to 4 rounds plus a check (`:962-972`). It is bounded and fails closed (`ContextNotSettled`, turned into `RedactionError` at `runmap.py:685-686`), so this is a wording conflict rather than a hazard. The lead should accept it or have it changed.
- Fix: build ORDER 013 as written, or record the leave-out and the limits in the ticket and SECURITY wording.

**MJ2. `enforce_map` is not idempotent when an identifier is glued to a shorter secret.** `runmap.py:592`, `:631-637`; cause in `redact.py:1089-1097`.
- The sweep handles values longest first and never looks again at a segment.
- Trace: map `{"<TENANT_1>": "abc123xyz9", "<SECRET_1>": "Zq9x"}`, text `abc123xyz9Zq9x`.
  - The identifier goes first and is skipped because `Z` touches it (`redact.py:1284-1288`).
  - The secret is then replaced, giving `abc123xyz9<SECRET_1>`.
  - A second `enforce_map` replaces the identifier, because the segment now ends before the placeholder.
- So the docstring claim "doing it twice changes nothing more" and ORDER 007 item 1 ("idempotent") are false for this shape. The text sent to the model holds a known identifier raw and standing alone.
- The stated limit ("an identifier touching a letter or digit is not swept") describes the input, not the output, so it does not cover this.
- The `_enforce` test helper asserts idempotence only on the inputs the tests happen to use (`test_runmap_enforce_map.py:46`).
- Chains are possible (identifier, identifier, secret), so one extra pass is not always enough.
- Fix: in `enforce_map`, repeat the sweep while the text changes, with a small fixed cap and `RedactionError` past it. Add the trace above as a test. Otherwise state the limit and correct the docstring.
- This is from reading, not a run. The same behaviour exists in `redact()` itself and belongs in the ORDER 013 property test.

### Minor

**m-new-1. `enforce_map` has no time budget and one path is never cached.** `runmap.py:619-637`.
- ORDER 007 item 3 names "budget exceeded" as an enforce failure; only the size cap exists.
- When any map value is a piece of a placeholder token, the "late" path builds a fresh uncached `_Redactor` for every message and document on every call (`:633`). It then does one substring test, and possibly one sweep, per late value (`:634-636`).
- The trigger is easy: a short upper-case name or user name such as `ID`, `PAN`, `NAME`, or one letter. `late` does not require the value to be sweepable.
- A hostile document can plant many such values (`user_id=ECRET_1` and so on), making every later gate call cost late values times text size.
- Fix: leave out of `late` every value whose `_sweep` rule is None, and add the `REDACT_BUDGET_S` check.

**m-new-2. The late-value test is narrower than the trap.** `runmap.py:585`, `:626`.
- `_TOKEN_PART.fullmatch` assumes genuine upper-case keys. A map with a non-genuine key (`<host_1>`) and a value `host` still gets the in-placeholder rewrite. Dropping the `fullmatch` and keeping `original in tokens` covers it.
- A related shape is not covered at all: a known value that spans the end of a just-written placeholder plus the next characters (for example `1>abc`), when it also occurs raw in the same segment. The result is a corrupted placeholder; no raw value is exposed. It is contrived.

**m-new-3. Limits that exist but are not in the stated list.** `model_gate.py:5-24`.
- A known value that itself holds a placeholder-shaped token is never replaced, because the sweep splits on tokens (`redact.py:1078`).
- A known value written inside angle brackets as `<ABC_1>` is read as a placeholder and left.
- A copy split by NUL bytes, or a UTF-16 document (decoded as UTF-8, every second character is NUL), passes. `enforce_map` does not run `_clean`.
- With partial overlap, a late value always loses to a first-group value even when it is longer. The docstring says the longer one wins (`runmap.py:613-615`).

**m-new-4. New refusals at install time.** `model_gate.py:300-302`, `:314`.
- Content that is not `str` is refused even with `mapping=None`. The adapters accept it today via `str(m["content"])` (`llm\common.py:96`).
- With any map, including an empty one, a message over `MAX_REDACT_CHARS` is refused. Messages had no cap before.
- Both fail closed. The install change must check that no caller sends either.

**m-new-5. Tests that can hide a gap.**
- `test_model_gate.py:701-702` skips when `handover\...\ii_meter.py` is absent. The lead picks code commits by path (`src`, `tests`), so on main this interface-equality test skips silently.
- `test_runmap_is_masked.py:333-354` is a strict expected-failure that holds a hard assert (`:353`, the map is not written). A regression there would be swallowed as the expected failure. Move that assert to a passing test.
- `test_runmap_enforce_map.py:304` (reader thread) can pass with the bug present. Only `:292` and mutant R3 are certain.
- The perf tests at `test_redact_context_after_sweep.py:310-345` only run in the perf step.

**m-new-6. Small holes in the source guard.** `test_model_gate.py:1160-1223`.
- `getattr(exc, "args")` or `getattr(exc, "__cause__")` passes, because `getattr` is allowed with any attribute name.
- `sys.exception()` and `sys.exc_info()` are not banned.
- Fix: allow `getattr` on an exception only with the constants `"reason"` and `"refused_before_response"`.

**m-new-7. Concurrent writers can give one placeholder number to two values.** `runmap.py:539`.
- Two threads in `redact_text` on the same map each number from their own copy; the later `update` wins. This existed before the change and is not a regression. It matters only if two producers ever write one run's map at the same time.

## Checks that held
- **Map and cache:** the enforce step never writes the caller's map or cache. It works on `dict(mapping)` and a private shallow cache copy (`runmap.py:621`, `:630`); `_build` only rebinds.
- **Byte-identical:** when nothing is replaced, the same message dict and the same bytes object are passed on (`model_gate.py:307-309`, `:321-323`). The sweep's split and join round-trips. Invalid bytes are untouched unless a replacement happened.
- **Settle exactly once:** no path reaches two settles. KeyboardInterrupt, timeout, an unmarked ProviderError, exhausted retries and a bad cost are not settled.
- **No provider call on failure:** a failed enforce, `worst_case` or reserve never reaches the client (`:234-245`).
- **Exceptions unchanged:** every handler uses a bare `raise`. `UnmaskedInput` is raised outside any handler, so it carries no cause.
- **Threads:** `dict(mapping)` on a `RunMap` is one atomic copy under the interpreter lock. A custom mapping that changes during the copy is a refusal, not a leak.
- **Redactor bounds:** the second look is bounded (at most 5 iterations, each at most two pattern passes and one sweep), skipped without `<BANKCODE_` in the text, and adds no new regular expression. The two re-run patterns are possessive or bounded, and `_bank_context` searches a fixed 100-character window. The size caps and the time budget in `_scan` are unchanged (`runmap.py:650-687`).
- **Nothing unmasked:** `find` and `sweep` bodies read as unchanged; `settle` only adds masks or raises.

## Not checked
- Nothing was run: no pytest, no `gate_mutants.py`, no perf tests, no timing numbers.
- No diff of `redact.py` against main.
- `tests\test_stage_names.py`: the board reported it red because of a sample word in `test_runmap_enforce_map.py`; `"prod"` is still at `:234`, `:235` and `:243`. I did not confirm whether it still fails.
- `tools\mutation_runner.py` beyond the replace line (`:541`, which replaces every occurrence, so G3a hits both `if mapping is not None:` lines).
- `llm\retry.py` (the signature used at `test_model_gate.py:814`), adapters other than `common.turns`, the audit sinks, and `tests\k5_support.py`.
- Install sites: none bind the gate yet. I did not check whether any caller puts run data into `system`.
- ORDER 012 item 2 (the `redact_untrusted` caller trace), the G7 ticket, evidence files, DECISIONS.md and both request files.
- Other changed tests outside the three modules (textnorm, grants).
- Whether commits landed while I read; each file was read once.
