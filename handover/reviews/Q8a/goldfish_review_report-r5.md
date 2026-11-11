Status: resolved (no person available; recommended option taken for every item)

# Goldfish Annotated Review Report

**Target:** branch `core/q8a-1-live-override-refusals`, head ecd5dba1: `src/hadavin_sdk/runtime/tick.py`, `app.py`, `config.py`, `defaults.py`, `CHANGELOG.md`, tests (full files). Security path: no round cap.
**Inputs:** `result-r5-delta-full.md`; evidence `evidence/Q8a-1/ecd5dba/RESULTS.md` (full suite 10754 passed, 0 failed, 1 skipped; perf step 1 failed = the known flaky timing test, not touched by this diff, fixed on `core/fix-timing-harness-flake`, so not a Q8a-1 defect; stage mutants 75/75; fail-before 27 failed; vault suite not run; merge with `core/q8a-2-...` conflicts in CHANGELOG.md only).
The reviewer's line references are quoted from its own reading of the branch; the fix builder re-reads each before editing.

Counts: PROPOSE FIX 8, CONTEST 0, ESCALATE 0, DECLINE 0 (one limit recorded as exception 2(a), see item 9).

## Findings

### 1 [Major M1] "A config error never shows the value that was refused" is false as written
* Reviewer evidence: `Config` and backend models set `hide_input_in_errors=True` (config.py:61, backends/table.py:24), so the earlier premise (`input_value=` echoed) did not hold; but custom validator messages still carry values: config.py:410-413 prints the whole system `base_url` (can hold `user:pw@host`), 407 detector route, 283-297 lists, 136 raw pydantic text with link, 457/115/481 duplicate key, unknown kind, path, 540 `str(exc)` for YAML errors (quotes the offending line), registry.py:224-225.
* ***PROPOSE FIX*** (class fix, not only the sentence): make every custom message value-free at the choke point (`_value_free_text` and the `str(exc)` sites at config.py:136, 540 and registry.py:224-225 name the field and the reason only, never the value; a URL with a login part is refused with "base_url must not contain a login" and no URL). Drop the `__cause__` text for CLI output (`from None` where the cause holds a value). Then keep the CHANGELOG sentence but state exactly which messages are covered. Tests: a made-up credential built from parts in `base_url`, in a YAML line, in a duplicate key, in a registry file; each must be absent from the exception text and from `str(exc.__cause__)` shown by the CLI. Fail-before on ecd5dba1 required.

### 2 [m1] tick.py docstring says "Three refusals"; the duplicate-name refusal is a fourth
* ***PROPOSE FIX***: say "four" or drop the count; same wording in `run_tick` and CHANGELOG.

### 3 [m2] `dataclasses.replace(ctx, ...)` on a live context gives a wrong-sounding message
* ***PROPOSE FIX***: refuse with a message that says "a context is not copied by replace(); build a new one" (field `now` is never None after construction), test `replace(ctx, results={})`; document in the `TickContext` docstring.

### 4 [m3] Subclass ban is a breaking change and is not in the upgrade steps
* ***PROPOSE FIX***: add one sentence to the upgrade steps: "test code that subclasses `TickContext` now fails at import with TypeError; build a plain `TickContext` instead".

### 5 [m4] No mutant for `_value_free_text`; its test passes without it
* ***PROPOSE FIX***: tests with a custom-validator error and a nested error (covered by item 1); mutants for `_value_free_text`, `include_url=False`, `include_context=False` in `stage_mutants.py`.

### 6 [m5] Wording for a non-technical reader
* ***PROPOSE FIX***: split the two 400-700 word bullets under headings (keywords, tick steps, timeout, limits); put the plain sentence "these refusals stop a test object that arrives by accident, not hostile code in the same process" first; gloss "stand-in", "frozen", "built without its constructor", `object.__setattr__` in plain words.

### 7 [n1] In-place edit of `STEPS` between the checks and the loop not named
* ***PROPOSE FIX***: take one copy of `STEPS` at the start of `run_tick` and use it for both checks and the loop (closes the gap, no clause needed); test with a list changed between the two reads.

### 8 [n2] Direct-purge figure stated as fact from an older head
* ***PROPOSE FIX***: the figure is now re-measured at ecd5dba1 (evidence RESULTS.md: `purge_tool_calls` returned 3 and `purge_redaction_maps` returned 3 on pilot and prod); change the CHANGELOG to say "measured at ecd5dba1" with that pointer.

### 9 [lead finding, from the evidence probes] Not-covered probes: `object.__setattr__` on a live context, `TickContext.__new__` plus `object.__setattr__`, and a direct store purge pass on pilot and prod
* Decision: no code fix at this layer. These are same-process attacks: any code that can call `object.__setattr__` or the store directly already holds every right the process has, so a check inside the same process cannot stop it. The refusals are a mistake catcher for a test object arriving in a live build, and the documentation already says so. The real control for deletion is least privilege: the app deletes evidence only through the separate purge identity (test `test_the_app_deletes_evidence_only_through_the_purge_identity` passed in the evidence). Classified exception 2(a) (physically impossible inside one process) with that control as the next step.
* ***PROPOSE FIX*** (wording only): the limit bullet says in plain words that same-process code is out of reach of these refusals, names the three probes with their measured results at ecd5dba1, and points to the purge identity as the control. Add the point to the ledger as IMPOSSIBLE-NOW with that reason.

## Other items for the fix batch
* Merge with `core/q8a-2-neutral-callback-and-guard`: CHANGELOG.md content conflict only; resolve it in the fix batch (take both entries) and re-run the two test files that touch both branches.
* The perf-step failure is not this branch's defect; the timing fix lands separately. State that in the evidence note, do not touch the test here.

## Handoff
Accepted fixes 9 (item 9 wording only). Contested 0. Escalated 0. Declined 0. Unaddressed 0.
Next: fix batch 5 on the branch (one push, delta evidence on the final head, fresh round 6 delta review; security path, so uncapped), then egm-drift-report before READY.
