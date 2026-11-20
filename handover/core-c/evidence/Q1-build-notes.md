# Q1 build notes: the gate masks the model's reply (E25 option a) and `put_back`

Branch `wip/cloud-core-c/q1-reply-mask` from `origin/cloud/core-c`. Not merged.

## What was built
- `guard/model_gate.py`, `BoundGate.chat`: after a successful provider call, `_mask_reply` runs the call's map snapshot over
  `reply.text` and every string (key and value) in each `tool_calls[].input`, through the request's own `_chunk` (enforce step
  plus the held-value net). Same snapshot as the request (no second redactor build), FRESH `EnforceBudget` (the provider call's wall
  time must not eat the mask budget). Unchanged reply: the same object. Changed: a `model_copy` (cost, usage, model id, stop reason kept).
  `usable_cost` is read from the client's own reply before masking.
- Row marker: `decision` ends in `+reply_masked` (e.g. `map_enforced+reply_masked`) when the text was changed. No new vocabulary for the
  normal path.
- Failure: any raise, budget, or net hit while masking never returns the raw reply. Cost settled by rule (a) (no settle by rule (c) when the
  cost is unusable), row `refused` / new code `reply_mask_failed` (in `AUDIT_CODES`), `ReplyMaskFailed(GateRefused)` raised (bare, no cause/context).
  NOTE for callers: this is a `GateRefused` although the call WAS made and paid (docs say "no call made" for the others).
- `_enforced` now returns a 4-tuple (adds the snapshot); only `chat` calls it.
- `guard/putback.py`: `put_back(value, mapping, kinds=None)` = `runmap.restore_value` (existing restore code) with `kinds` intersected with
  `STORED_KINDS` (can only narrow). Secret kinds are never restored; a placeholder not in the map is left as is.
- Tests: strict xfail flipped to `test_f2_a_reply_with_a_planted_secret_is_returned_masked`; new `test_q1_*` (tool-call argument, unchanged
  reply byte-identical/same object, invented value left alone, put_back kinds, mask failure settles and withholds, no-cost failure, net hit).
  Three existing tests adjusted because the reply now also passes the enforce hook (d9 x2: 3 calls on one snapshot; g14: third outcome).
- Mutants Q1a..Q1i added; G3b's search text updated for the 4-tuple. `MIN_MUTANTS` 159 -> 168 (measured `len(M)` = 168).
- model_gate SECURITY docstring block rewritten (the F2 "not masked" bullet is now the Q1 guarantee, with named tests; D8 test passes).

## TESTED
- `tests/test_model_gate.py`, `test_runmap_enforce_map.py`, `test_gate_mutants_picked_up.py`, `test_gate_install_callers.py`, `test_s3_gate.py`:
  399 passed, 1 skipped, 6 xfailed. ruff check and format clean on touched files.
- `python tests/gate_mutants.py Q1` : 9 of 9 KILLED. `... G3b`: killed.

## NOT RUN
- Whole `python tests/gate_mutants.py` (another gate_mutants process was running; R8 caution). Other G/R mutants were not re-run; Q1 changes
  could affect any mutant whose killer's reply now goes through the mask (none observed in the picked-up checks).
- The rest of the repo's test suite; the real Postgres store path; the real provider adapters.

## SECURITY-gap-style note for the docs pass (do not edit root SECURITY.md)
- New guarantee: a value the run's map holds is not returned by `BoundGate.chat` in the reply text or in tool-call arguments; the caller gets
  its placeholder and uses `guard.putback.put_back` for identifier kinds only.
- Limits: only registered values (a value the model invents or derives is not covered); tool-call `name`, `stop_reason`, `model_id` and other
  Reply fields are not masked; the map snapshot is the one taken for the request (a value registered during the provider call is not covered
  until the next call); a spelling the sweep does not catch (encodings, letter case) passes, as for requests; the independent substring net
  is Q3. A reply that cannot be masked is withheld after the model was paid: a refusal, cost settled (rule a/c), code `reply_mask_failed`.
  Put-back reintroduces real identifier values into caller memory/logs by design; secret kinds never come back.
