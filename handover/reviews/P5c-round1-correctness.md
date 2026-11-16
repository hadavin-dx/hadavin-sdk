# Review: P5c round 1, correctness lens (ticket P5c revision 1)

- Ticket: P5c, revision 1
- Lens: correctness
- Status: REPORTED (saved by the lead session from the reviewer hand-back, which is model output, not user authority)

---

ROUND 1, CORRECTNESS lens, ticket P5c rev 1 (handover/tickets/P5c.md). I read the ticket, TICKET-TEMPLATE.md, LEAD-ORDERS.md orders 6-11 and 20-21, and the cited main source. I did not open reviews/ or evidence/. I could not run git, so I cannot confirm that the tree at the repository src tree is commit 124258b.

| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| R1-COR-1 | Blocker | 55 (item 2), 60 (item 7), 66 (P5c-3) | The ticket contradicts itself on escaping. `mask(untrusted=True)` is `runmap.redact_untrusted`. On main that function calls `neutralise_untrusted`, which rewrites every placeholder-shaped literal such as `<EMAIL_1>` to `‹EMAIL_1›` (runmap.py:275-303). Item 7 says issued placeholders "stay as they are" (T2-13). But the run loop already sends `safe_doc` (masked, with real placeholders) and later turns carry model replies and tool results holding placeholders. If the wrapper runs in untrusted mode on those, it destroys placeholders. The model then sees `‹EMAIL_1›`, put-back fails and the gate denies `input.unresolved`. If it runs in trusted mode (`redact_text`), the extract and evals paths, which send RAW documents, lose the escape that V6 relies on ("main escapes instead"). The ticket does not say which messages and documents get which mode. It also does not say whether the run loop's own masking at agent_loop.py:367 stays or is removed. | State per input class (raw document, run-loop-masked document, user turn, assistant turn, tool result) which mode the wrapper uses. State whether the loop masking at :367 and `prepare_output` stay. Add a row where a placeholder in an assistant or tool turn must arrive unchanged, and a row where a forged `<EMAIL_9>` in a RAW document through `extract` is escaped. |
| R1-COR-2 | Major | 74, 76, 82 (T4-01), PENDING 8 | The money-adjacent finding stops at ACCOUNTID. On main, a bare 10-16 digit number, apart from exactly 12 digits, is masked as PHONE (redact.py:471-478; the comment at :462 says a contiguous card number "relies on" this). PHONE is a stored kind (defaults.py:120). Its grammar `[0-9 ()+.\-]{5,32}` (runmap.py:181) accepts digit strings. So a plain 16-digit card number, or a 10, 11 or 13-15 digit bank account number with no bank word, is stored and put back into plans. The ticket claims regulated kinds are "never stored". T4-01 tests only CREDITCARD and BANKACCT placeholders, so a bare card number labelled PHONE passes. | Add a decision and a test row: a PHONE hit that is all digits and 10 or more characters (or Luhn-valid) is not stored, or PHONE restore is limited to a phone-shaped grammar. Put it in PENDING 8 and name the row. |
| R1-COR-3 | Major | 81 (T3-15a..f), 83 | T3-15 and T2-14 are marked "FB" (fail before). They depend on P2d-2's look-alike check. The FAIL-BEFORE method line says the base for non-pattern rows is the main head the PR rebases on, and that head already contains P2d-2. So on that base they pass. The "order 11(1) says all six LEAKED" argument is about pre-P2d-2 main. Several other P5c-3 rows are only regression pins relative to the K5 loop. | Relabel T3-15 and T2-14 as "regression pin through the wrapper". Fail-before is then claimed only for rows that really fail on the P5c-3 base. |
| R1-COR-4 | Major | 88-91 mutant plan | Some mutants cannot be killed or cannot be written. (a) M31 (`extract` passes the raw document) and M36 (tool-output masking dropped): after P5c-3 the wrapper masks the whole body anyway, so T3-03 and T3-01 still see a masked recorded body and the mutant survives as equivalent. The kill needs a test that calls the inner model through the wrapper-bypass seam, or the mutant must target a different line. (b) M40 ("restore called while building the approval card"): no card code restores anything on main (agent_loop.py:271-276 says the card command does not exist, and V1 is cut), so there is no source line to mutate. (c) M39 depends on a marker whose form is deferred to the builder (PENDING 11), so `old` and `new` cannot be pre-listed. (d) M26 (global instead of ContextVar) is killed by T2-10 only if the two threads are forced to interleave; the row names no barrier or distinct values. (e) T3-02 is said to be "killed by M24, M33" (line 81), but M24 maps to T2-08 and M33 to T3-05. | For each mutant name the target line and why the wrapper does not mask the mutated path. Drop or replace M40. Fix M39 once the marker form is settled. Require a threading.Barrier and two distinct values in T2-10. Correct the T3-02 cross-reference. |
| R1-COR-5 | Major | 66 (P5c-3), G3 at line 26 | The `received` event is written at agent_loop.py:349, before the size check (:354), before the limits stop and before masking (:367). Hashing "the masked body" needs masking moved ahead of that event. The ticket does not give the new order, or what is hashed when the document is too large or masking fails. A builder has to guess. | Specify the order: size check, then mask, then `received` with the masked-body hash, and what the hash is on refusal (for example the reason code, no hash). Add a row for the refusal paths. |
| R1-COR-6 | Major | 58 (item 5 ii), 79 (ACC-2, ACC-2-NEG) | "Strong keywords" are not defined. The regex `_ACCT_WORD` (main redact.py:82) is `(accounts?\|acct\.?\|acc\.?\|a/c)` plus an OPTIONAL number suffix. The ticket counts "account no/number/#, acct, A/C" and excludes a bare "account(s)". It does not say whether `acc.`, bare `acct` and bare `A/C` with no suffix count, and the regex cannot tell a bare "account" from "account no" at the `_bank_context` call. The ticket's `_ACCT_WORD :89` and `_bank_context :114-120` are lines of the pr50 snapshot; main has them at :82 and :107. | Give the exact accepted spellings (a table of accepted and refused forms, with ACC-2 and ACC-2-NEG rows for each) and say where the check is made (a group in the pattern or a check on `m.group(0)`). |
| R1-COR-7 | Major | 58 (item 5 iii) | "Upper-case first letter by `str.isupper()` in a check, not by `[A-Z]`" needs a callback after the regex match. The patterns are a plain table (kind, regex) that the fold scan and `redact_many` also use. The ticket does not say how the check runs there, or what a failing check does (skip the match? try the next one?). It also does not say whether the `Mr/Dr...` form at :444 gets the same change. | State the mechanism, and the fold-scan and `redact_many` behaviour. Add rows for the title form. |
| R1-COR-8 | Major | 64 (P5c-1), 59, 109 | P5c-1 is described as "No caller changes". It changes `config_hash` for every agent and makes `Config` refuse a non-dev config with no explicit `redactor`. The ticket lists no existing tests or fixtures that pin a config hash, a `qualified.jsonl` line or a prod config. It lists changed existing tests only for P5c-3 (line 66). | Add a grep result and a list of existing tests changed by P5c-1, each with its reason. |
| R1-COR-9 | Minor | 44 (P4b1), 133 (PENDING 9) | The ticket assumes a "metered wrapper" from P4b1. P4c line 266 says run-path metering is `Limits.hold` at the call sites, "Not a wrapper on `deps.llm`". The wrapper-order question is probably moot. | Check `tickets/P4b1.md` and either delete the dependency and item 9 or name the wrapper. |
| R1-COR-10 | Minor | 69 | "`write_intent` UNVERIFIED on main": it exists. `AuditSink.write_intent` raises `AuditUnavailable` and `write_outcome` does not (k1b/audit_sink.py:31-39). Main's run loop uses `write_outcome` only (agent_loop.py:229-230). | Say so. The wrapper's fail-closed behaviour is new for the run loop, and the CHANGELOG line (line 109) already covers it. |
| R1-COR-11 | Minor | 42, 43 | Depends-on lists P5b5 but not P5b3. Item 42 itself says P5c needs P5a and P5b3, and P5b3 rewrites `extract.py:58`. | Put P5b3 in the list (PENDING 12 asks the lead the same thing). |
| R1-COR-12 | Minor | 66, PENDING 3 | `evals.py:62-63` and `agent_loop.py:367` decode with `replace` today. Strict decode makes `gate` fail for any golden input that is not UTF-8. The ticket does not check the repository's golden files. | Add a check or a row: all golden `input_ref` files are UTF-8. |
| R1-COR-13 | Minor | 54, 20 | The cites into `runmap.py` do not match the tree I read: `RunMap` is at :337 (ticket :384), `redact_untrusted` at :298 (ticket :327, :340-350), `TooDeep` at :53 (ticket :98), `_redact_value` at :541 (ticket :588), PHONE at redact.py:471-478 (ticket :479-484). `InputTooLarge` :42, `RedactionError` :38 and `ACCOUNTID` :353 do match. Either the tree differs from 124258b or the cites are off. | Re-cite against the head the lead names, or say these are P2d-landed lines. |
| R1-COR-14 | Nit | 66 | "43 lines in 20 test files": I count 42 occurrences in 20 files with a broader pattern. | Quote the exact `git grep` command. |
| R1-COR-15 | Nit | 5 | "Python 3.13.18" looks like a typo or an unusual patch number; I cannot confirm it. | Quote `python --version` output. |

**Order 11(5) answer.** The "no, not in general" answer holds in substance. I confirmed these from the regexes:
- Main masks exactly 12 digits as ACCOUNTID (redact.py:353).
- PHONE masks 10-16 digit runs (redact.py:476).
- `(?![\w.])` makes a number before a full stop unmasked.
- 8-9 and 17-18 digit numbers are not masked.
- BANKACCT needs a bank word via `_bank_context` (redact.py:107-113).

The one gap is R1-COR-2: the bare 10-16 digit numbers that main does mask are labelled PHONE and stored. Order 11(5) asks that the answer be "added to the acceptance rows if so"; ACC-1c, ACC-2 and ACC-12 do that.

**Template fields.** All 17 are present in order. Weak spots are the Tests, Mutation and Source fields (R1-COR-3, R1-COR-4). The Source field also says "MANIFEST rows: none hold C1 (UNVERIFIED)".

**Verified**
- extract.py:46-52 sends the raw `documents=[document]` and imports only `safe_head` (the import is at :11).
- agent_loop.py:349 is `sha256_hex(document.hex())` and :367 is the `decode("utf-8","replace")` plus `redact_untrusted` line.
- agent_loop.py:376-377 and :547-549 give `redaction_error` with no model call.
- agent_loop.py:269-284 (`inputs_view`), :295 (read-tool restore), :286-308 (`_run_tool` with `prepare_output`) and :794-797 (`input.unresolved`).
- The five `.chat(` call sites are agent_loop.py:425, evals.py:73, extract.py:47, guard/judge.py:72 and k1b/loop.py:94. The sixth is demos/ask-your-data/askdata/pipeline.py:155.
- judge.py:71 uses `redact_text(text, {})`, a fresh map, so T3-09 is a real fail-before row.
- evals.py:62-63 masks with a fresh map and `replace`.
- defaults.py:108-122 `STORED_KINDS` matches the ticket's list of 13.
- `RunMap` is a `dict` subclass (runmap.py:337).
- `config_hash` (registry.py:105-148) has `llm_backend` and nothing about redaction, so G5 holds.
- `grep "redactor"` finds no kind in backends. The 6 hits are all in other contexts.
- injection.py:86-101 turns any exception into `guard_unavailable`, so T3-12 and M35 are real.
- Counts add up: 16+10+14+20+8 = 68 rows (69 with T2-P), and the mutants M1-M41 split 19, 10, 8 and 4 = 41.
- 44 `BL-core-c1a-*` rows and 28 MAJOR in handover/ledger-seed.md.
- Order 20 item 6 (3-round cap, plus one more for a redaction package whose last round had no Blocker and at most 2 Majors) matches the ticket's header. Orders 6(e), 8(3) and 11(5) are quoted correctly. The merge order of order 20 item 4 is also quoted correctly.

**Not checked (UNVERIFIED)**
- Any claim about the P2d-2, P5a, P4b1 and P4c contents beyond what grep showed. The `OWN_CODES`/`RESERVED_FOR` names, the `LookalikeCopy` class and the `FOLD_NOTE` marker all sit on long lines I did not read in full.
- The C1a branch (`8460813`), its line numbers and diffstat, and the C1/F1-F14 text in the design notes.
- The snapshot's pr50 line numbers (:360, :483, :451, :454).
- The F10 pickle probe, Python 3.12 and 3.14 behaviour, and the T2-P budget.
- Whether the tree I read is 124258b.
- The Intake `mask.py` claims, the order 16(5) and 19 A/C wording, plan-v3 and amendment cites (A4, A5, A9 F6), and the MANIFEST rows.
