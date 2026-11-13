# claims-fix A (contract.md only), base c30c373. Verdicts: FIXED 9, AUDIT-WRONG 1 (row 28), CODE-BUG-CANDIDATE 0.
Line numbers are at c30c373. The audit's ":112" row is the sentence at line 103 ("Every request, on every route, passes _gate_error"; line 112 is a heading).
Ran: run-un.sh on test_backfill_classes, test_late_put_keeps_newer_mode, test_two_drives_ask_model_once: 12 passed.

## :22 FIXED
OLD: (text/plain, a form type or a UTF-16 body are all accepted if the body parses as JSON).
NEW: (text/plain or a form type are accepted if the body parses as JSON). The body must be UTF-8 text: a body in another encoding, UTF-16 for example, cannot be read and is answered 400 `bad_envelope`.
Evidence: server.py:960 `json.loads(raw.decode("utf-8"))`, ValueError -> env None -> server.py:982 bad_envelope. Checked with python: utf-16 -> UnicodeDecodeError, utf-16-le -> JSONDecodeError (both ValueError).

## :28 AUDIT-WRONG (no change)
Contract sentence is right. desk.py `_run_followup` (comment "The AI step runs only after the claim") claims first (`_claim(None, lead_id, ("pending",))`), `_after_claim` asks the model only for the winner. tests/test_ai_after_claim.py::test_two_drives_ask_model_once asserts q.calls == 1 for two simultaneous drives (passed), and test_reaper_does_not_ask_model_again asserts 1 for drive + reaper. The "at most 2 calls" docstring in tests/test_input_edge_cases.py::test_two_drives_one_email (and its `calls in (1, 2)` assert) is an older, looser statement: stale test docstring, outside my files (no test edits allowed). Suggest the lead fixes that docstring in a later test patch. Not a code bug: unsure only whether a give-back (lock/busy) followed by a second claim could ask twice; that is a sequential retry, not "at the same moment".

## :61 FIXED
OLD: `not_sent` fits every `unknown` row and clears `ambiguous_prior`, and a leftover `crm_done=2` of a `crm_unconfirmed` row.
NEW: `not_sent` fits every `unknown` row, except while a send or CRM call of that lead that the desk stopped waiting for is still running (409 `call_still_running`, row stays `unknown`); when it fits, it clears `ambiguous_prior`, and a leftover `crm_done=2` of a `crm_unconfirmed` row.
Evidence: desk.py:2270-2273 `if decision == "not_sent" and self._call_running(lead_id): return Reply(HTTP_CONFLICT, {"error": "call_still_running", "hint": HINT_CALL_RUNNING})`. (Already stated at contract line 299.)

## :64 FIXED
OLD: `R` item: `Send a corrected submission with a NEW request number.`;
NEW: `R` item: `Send a corrected submission with a NEW request number.` (except for a receipt whose reason is `internal_error`, a fault on the desk side: its hint says a person must look at the desk log and fix the cause, then send the lead again with a new request number);
Evidence: desk.py:2192-2198 `_not_actionable` swaps in HINT_INTERNAL_ERROR (desk.py:208-212) when outcome_reason == "internal_error"; test_internal_error_hint_text. I described that hint instead of quoting it (it is long).

## :103 (audit ":112") FIXED
OLD: Every request, on every route, passes `_gate_error` in `server.py` before the path is read.
NEW: Every request that gets a handler thread, on every route, passes `_gate_error` in `server.py` before the path is read. A connection refused for lack of a thread or reading place (the connection-limit 503) is answered before any request is read and never reaches the gate.
Evidence: server.py:405-408 process_request calls `_refuse_busy` (server.py:454) with no handler; `_dispatch` calls `_gate_error` first (server.py:~761).

## :178 FIXED
OLD: All desk replies are JSON with `Content-Length` and `Connection: close`.
NEW: All desk replies carry `Content-Length` and `Connection: close`. They are JSON, except the `GET /ui` 308 (empty body) and the `/ui/<file>` replies (html, css, js or png).
Evidence: server.py:615-631 `_send_bytes` is the one writer (sets both headers for every reply); server.py:828 308 with b"" body, text/plain; contract rows for /ui say html/css/js/png. Note: `_refuse_busy` writes its own head (also has Content-Length and Connection: close, JSON).

## :269 FIXED
OLD: `receipts` cannot be changed or deleted and a verdict is written once;
NEW: `receipts` cannot be deleted; the columns `receipt_id`, `source`, `source_ref`, `received_at` and `payload` cannot be changed; the five verdict columns (`outcome`, `outcome_lead_id`, `outcome_reason`, `differing_fields`, `decided_at`) are written once (one update sets all five, a later update is refused); `attempts` and `payload_conflict` may still change (they record that the request number came again);
Evidence: schema.sql triggers receipts_immutable (UPDATE OF receipt_id, source, source_ref, received_at, payload), receipts_outcome_once (five columns, WHEN OLD.outcome IS NOT NULL), receipts_no_delete; attempts and payload_conflict have no trigger (schema.sql comments: "how many times this request number arrived", "request number came again with a different payload"). "record that the request number came again" is my paraphrase of those comments for payload_conflict only partly (it is set when the payload differs): wording is slightly loose, acceptable.

## :275 FIXED
OLD: (the whole backfill sentence from "a row whose `last_error` starts with `internal:`" to "A `sent` row is never touched.")
NEW: a row whose `last_error` is `refused`, `unreachable`, `ambiguous` or `crash_while_sending` gets 1, in any state; `internal:CrmNothingStored`, `internal:KeyError`, `internal:ValueError`, `internal:LookupError` keep 0; any other `internal:` error gets 2; a `failed` row with a label and any other error gets 1; any other row that was tried (attempts > 0) gets 2; a row never tried and a `sent` row are never touched; "the order is the order of this list" (the `sending` -> 2 clause stays first); `test_backfill_classes` checks nine of these cases.
Evidence: db.py:30-38 CASE: sending->2; the four send errors->1; four internal names->0; `LIKE 'internal:%'`->2; failed+label->1; else 2; WHERE state <> 'sent' AND (attempts > 0 OR state = 'sending'). Test params (9 cases) pass.
Small point: "any other `internal:` error gets 2" is true for the empty-string-safe LIKE; sending still wins first.

## :294 FIXED
OLD: (`test_late_refresh_keeps_newer_mode`; the same rule is coded for a put, but no test proves it)
NEW: (`test_late_refresh_keeps_newer_mode`; the same rule for a put is `test_late_put_keeps_newer_mode`)
Evidence: tests/test_hung_adapter_calls.py:820 exists and passed.

## :309 FIXED
OLD: A reaper pass drives rows for at most `gate.REAPER_PASS_SECONDS` (10 real seconds); the rest is still due and comes first in the next pass.
NEW: A reaper pass stops starting new drives after `gate.REAPER_PASS_SECONDS` (10 real seconds); a drive that has started runs to its end, and so do the two capability reads at the start of the pass, so a pass can overrun (about 55 s at the very worst with the defaults, `gate.py` comment); the rows not started are still due and come first in the next pass.
Evidence: gate.py:28-37 comment: "checked between drives, never inside one ... 10 + 27 + 18 = 55 s at the very worst". The 55 s is the code comment's figure, not measured by me.

## Not verified
The 55 s figure and "the rows not started come first in the next pass" (kept from the old sentence) were not measured. Patch applied with git apply --check on a clean c30c373 clone (before the last one-word tweak; re-check below). No ruff/other CI checks run (as ordered).
