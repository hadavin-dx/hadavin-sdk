# review-code-F-gate-1 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# Early review: cloud/core-c, guard/ new code (read-only, nothing executed)

## Verdict
The gate on disk is still the pre-ORDER-007 version: it runs a refusing pattern check (`runmap.is_masked`), not map enforcement. The money, audit and exception ordering is sound. Not mergeable as-is: 1 Blocker, 4 Majors, 9 Minors.

Every finding below comes from reading; none was confirmed by a run.

## What I reviewed (worktree `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-c`)

| File | Lines read | State vs baseline |
|---|---|---|
| `src\hadavin_sdk\guard\model_gate.py` | 238, all | new |
| `src\hadavin_sdk\guard\runmap.py` | 668, all (baseline 625, all) | changed |
| `src\hadavin_sdk\guard\redact.py` | 836-1055 and 1186-1256 only | looks unchanged: 1256 lines both sides, same 48 top-level anchors at the same line numbers; not byte-compared |
| `tests\test_model_gate.py` | 867, all | new |
| `tests\test_runmap_is_masked.py` | 302, all | new |

- **Absent in this worktree:** `guard\textnorm*`, `_confusables.py`, `_scripts.py`, `tests\gate_mutants.py`, `tests\test_p1c_gaps.py`. There is no fold, P1d-a, P2d-1 or G4 code and no G6 wording.
- **Specs read in full:** the F ticket with Amendment 1, `F-review-1.md`, `G-text-deltas.md`, `G-review-1.md`, `G4-P1c-redactor-gaps.md`, both G surveys, ESCALATIONS E2, ORDERS 001-008, `ii_meter.py`, the interfaces README, and `draft-F-install.md` (section 10).
- **Board note:** `STATUS-BOARD.md` (05:42Z) says the ORDER 007 rework is "under way". The files I read do not contain it, so newer commits may supersede the Blocker.

## Invariants

| # | Invariant | State | Evidence |
|---|---|---|---|
| 1 | No provider call without an open reservation | HELD | `model_gate.py:159-166` reserves inside a try and re-raises on any exception; `_llm.chat` is only at `:168`. Tests T12 and `test_worst_case_raising...`. |
| 2a | One settle on success | HELD | `:191`, test T3. |
| 2b | One settle on provider error | HELD, but the amount is wrong for one case (M2) | `:176-181`. |
| 2c | Timeout | HELD as ORDER 006.8 says (worst case, `:182-184`) | Conflicts with interfaces README contract point 4, "timeout: do NOT settle" (m1). |
| 2d | KeyboardInterrupt / SystemExit | Zero settles by design | `:185-189`, per contract point 4; test T14. This is not "exactly one". |
| 2e | Exception in the mask step | HELD | It runs before the reserve (`:156-158`), so there is no reservation and no settle. |
| 2f | Exception in audit | HELD | `_note` suppresses `Exception` (`:227`); T17 and `test_a_raising_audit_sink...`. |
| 2g | No double settle | HELD | No path reaches both `:191` and `_failed`. |
| 3 | Failed reserve or mask step means zero provider contact | HELD for the check as built | `:156-166`. |
| 4 | Enforce never writes the map; byte-identical when nothing raw occurs | NOT IMPLEMENTED YET | No enforce step exists. The current check does not write the map or the cache (`runmap.py:514-518`), and passes the caller's objects through by identity (`:168-175`). |
| 5 | Placeholders untouched, no double or partial replacement, length ordering, overlaps | NOT IMPLEMENTED YET | See "Traps for the enforce build" below. |
| 6 | Success row via the non-raising writer; audit failure never fails or repeats the call | HELD | `:195`, `:223-238` use `write_outcome` only, with one call attempt. |
| 7 | Inner client's exceptions pass through unchanged | HELD | Bare `raise` at `:178, 181, 184, 189`; T13 asserts identity. |
| 8 | `bind` returns an object satisfying the LLM Protocol | HELD | `BoundGate.chat` (`:146-155`) matches `llm\protocol.py:19-28`; test `:710`. |
| 9 | Thread safety of shared state | HELD for the gate's own state; open for the live map | `BoundGate` is immutable after `__init__`, with no module state. The live map is a hazard (M4). |

ORDER 007 and Amendment 1 items not implemented:
- Enforce by replacement (I12 to I15).
- `mapping=None` means no step. Today `:210` substitutes `{}` and pattern-scans.
- `worst_case` computed on the enforced copies.
- `tests\gate_mutants.py` (ORDER 008).
- Not calling `is_masked` (Amendment item 11).

## Findings

### Blocker
**B1. The gate contradicts ORDER 007.** `model_gate.py:107, 156-158, 206-221`.
- It refuses on a pattern hit, and with `mapping=None` it scans against an empty map. The docstrings at `:3-6` and `:123-125` describe the old design.
- The tests pin the wrong behaviour:
  - `test_model_gate.py:150` asserts the default check is `is_masked`.
  - T4 to T9 (`:237-312`) expect refusal for raw secrets not in the map.
  - `:289` and `:382-393` expect a refusal where ORDER 007 wants a replacement.
  - `:396-403` expects a refusal with no map.
  - The two `xfail(strict=True)` tests at `:840-867` assert that real producer output is refused.
- Installed as-is, real runs stop. This is E2 Fact 1 and Fact 2.
- Fix: build the enforce step, delete the `mask_check` parameter and `_all_masked`, and rewrite those tests (I12 to I15, zero refusals).

### Major
**M1. `test_i9` cannot fail on the code it guards.** `test_model_gate.py:680-691`.
- `source.split('"""')[2]` is only the text between the module docstring and the first class docstring, which is `model_gate.py:11-80` (imports and constants).
- A `str(exc)`, `__cause__` or `logging` call inside `chat`, `_failed` or `_note` would pass.
- Fix: walk the `ast` for banned names and attributes, or strip strings with `tokenize` and scan the whole file.

**M2. A plain `ProviderError` settles at 0, but a billed reply that fails to parse is also a plain `ProviderError`.** `model_gate.py:179-181`.
- `llm\common.py:193-196` says "a malformed answer is a ProviderError"; `retry.py:97-99` converts any non-transient exception, including the `ValueError` at `gemini.py:106`.
- A model steered off schema is therefore paid and booked at 0 on every call, so the cap is not exact. This contradicts draft-F-install H4 ("a judge steered off schema is still charged once").
- The test comment at `test_model_gate.py:477` assumes parse failures arrive as `ValueError`; through `NetworkLLM` they do not.
- Fix: settle the worst case for every `ProviderError` unless the adapter marks it as refused before a response (a subclass or a flag set in `with_retry`). This needs a lead decision, because ORDER 006.8 assumed the two cases are distinguishable.

**M3. `tests\gate_mutants.py` does not exist.** Under ORDER 008 item 1, the three gate guarantees count as NOT RUN, which means not done.

**M4. The live map can be read while empty.** `runmap.py:487-488` (baseline `:524-525`).
- `redact_text` does `mapping.clear()` then `mapping.update(current)`. The gate holds the map by reference (`model_gate.py:123-125`).
- A gate call on another thread can snapshot an empty map in that window. With the current check this is mostly harmless. With enforcement it fails open: no replacement, the known value is sent raw, and no error is raised.
- Fix: drop the `clear()`. `current` is always a superset, because `_Redactor` copies the map and only adds (`redact.py:897, 962`).
- I did not verify whether any install site calls a bound gate concurrently with a map write (`k1b\loop.py:104` runs the call in a thread). Treat this as Major if one does, Minor otherwise.

### Minor
- **m1. Timeout spec conflict.** `model_gate.py:182-184` and `test_model_gate.py:478` settle a timeout at the worst case (ORDER 006.8); README contract point 4 says not to settle. The booked amount is the same, but the row is closed rather than left for the sweep. The lead should pick one and fix the other text.
- **m2. Misleading row for a paid call.** `:192-194`: a call that returned a reply but whose settle failed is written as `result="failed"`. Anyone counting failed calls will be misled. Suggest `ok` with `error_code=settle_failed`.
- **m3. Audit row cannot be reconciled with spend.** `:229-237` carries no reservation id and no route. `AuditEvent.object_ref` is free (`models.py:203`); put the reservation id there.
- **m4. Reason codes are not allowlisted.** `:163-165` takes `.reason` from any exception type (for example `URLError.reason`) if it is one lowercase word. Restrict it to `SpendRefused` or the five published reasons once `limits.SpendRefused` lands.
- **m5. Wrong code for a bad reply.** `:191`: a reply with no `cost_usd`, or a NaN or negative cost, is recorded as `settle_failed`. The outcome is acceptable (worst case stays booked) but untested (F-install H5).
- **m6. Misnamed test.** `test_model_gate.py:363` is called "changed by another thread" but has no thread; it uses a Mapping whose `__iter__` raises.
- **m7. Promised `is_masked` cases are missing.** `G-review-1.md` cb-1-3 promised shape A (an escaped placeholder look-alike such as `&lt;ID_5&gt;` after `redact_untrusted`) and shape B (BSB account second pass) as a pass or a strict xfail. Neither is in `test_runmap_is_masked.py`. My reading is that shape A is a false "not masked" (fail-closed), not a leak. The round-trip loop (`:281-302`) has no layer that would hit either.
- **m8. Cache read moved outside the try.** `runmap.py:486`: `getattr(mapping, "redact_cache", None)` was inside the try on the baseline (`:493`). An exotic mapping whose attribute access raises would no longer become `RedactionError`. Negligible.
- **m9. Producers registry not updated.** `guard\producers.py` has no `model_gate` row (`requests\1-producers.patch` is not applied), so `tests\test_k5_producers.py` is expected red on this branch. This is known from F-review rd-1-B6; I did not verify it.

## Text changes (fold, redactor, runmap)
- **Fold / textnorm, P1d-a, P2d-1, G4 (base64, host names), G6 wording:** NOT IMPLEMENTED in this worktree. Nothing to review.
- **`redact.py`:** no change found, with the limit stated above.
- **`runmap.py` diff:** three things only.
  - The `Mapping` import (`:20`).
  - The `redact_text` body moved verbatim into `_scan` (`:524-569`).
  - New `is_masked` (`:492-521`).
- **Regexes:** none added or changed. `REASON_CODE` (`model_gate.py:75`) is a bounded class under `fullmatch`, so it is linear.
- **Size caps:** none removed. `_within_cap` runs at `:485` and `:513`; the budget and `fits_after_nfkc` are unchanged inside `_scan`.
- **Masking:** I see no path that lets previously masked input through. Apart from m8, `redact_text` is unchanged in behaviour.
- **Cache privacy:** the claim at `runmap.py:515-517` holds. `_Redactor._build` rebinds `_ordered`, `_rules`, `_finders` and `_slow` (`redact.py:974-975, 989, 994`) and only assigns the two cache keys (`:1007-1009`).
- **Config and naming:** nothing hard-coded that belongs in config, and no project words (lead, incident, refund, invoice, intake) in `model_gate.py` or the `runmap.py` diff.

## Traps for the enforce build
`_Redactor(mapping, cache).sweep(text)` (`redact.py:1011-1050`) already does "replace known originals by existing placeholders, skip placeholder tokens, longest first, add nothing". A thin `runmap.enforce(text, mapping)` over it avoids new replace logic, with these caveats:

1. **Some known values are never swept.** `_sweep` (`redact.py:1204-1219`) skips originals under 3 characters, digit strings under 6, and `_COMMON` words. Identifier kinds are replaced only where no ASCII letter or digit touches them (`:1225-1243`). The ORDER 007 guarantee sentence is then not literally true; state the limit or decide otherwise.
2. **A placeholder inserted in this pass can be rewritten.** Replacement within a segment is sequential and the segment is not re-split (`:1042-1048`). A later, shorter secret-kind original that is a substring of a just-inserted placeholder (for example `SECRET` or `UUID_1`), and that also occurs raw in the same segment, rewrites the inside of that placeholder (`<<SECRET_2>_1>`). The I13 test needs this case.
3. **Partial overlaps leak a tail.** With `abcd` and `cdef` in `abcdef`, the first replacement leaves `ef` raw. Needs a test and a stated limit.
4. **`sweep` writes the caller's cache.** `_build` writes `redact_cache` (`:1007-1009`). Pass a private copy, as `is_masked` does, or I3' breaks.
5. **Documents must not be re-encoded unless changed.** Decoding with `"replace"` and re-encoding alters invalid bytes. Send the original `bytes` object when no replacement happened, or I15 (byte-identical) breaks.
6. **Seed entries.** `"\0seed..."` originals exist in some maps (`approvals\channel.py:54`). They are harmless to the sweep but need a test.
7. **Encoded spellings.** The sweep sees raw text only. Encoded spellings of a known value (percent, `\u`, full-width) pass. State this as a limit.
8. **Copies.** Send copies of the message dicts and lists, and compute `worst_case` on those copies (Amendment item 7).

## Not checked
- Nothing was executed: no test, lint or mutant run. Every "HELD" is from reading plus the presence of a test.
- `redact.py` lines 1-835 and 1056-1185 on either side.
- The `write_outcome` implementations in `audit\chain.py` and `local_dir.py` (F-review says they are non-raising).
- Provider adapters beyond `retry.py:60-108`, `common.py:184-213` and the grep hits.
- Install sites (`agent_loop.py`, `k1b`, `evals.py`) and any concurrency there.
- Other tests on the branch that differ from baseline (for example `tests\test_grants_negative_roles.py`, step B, outside `guard\`).
- The evidence files under `handover\core-c\evidence\`, `DECISIONS.md` and `requests\1-producers.patch`.
- Whether newer commits landed during the review. `model_gate.py` was read once.
