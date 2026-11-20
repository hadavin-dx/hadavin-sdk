# Security

Please report a suspected vulnerability privately through GitHub: the **Security** tab of this repository,
**Report a vulnerability**. If that button is not shown, open an issue titled "Security contact request" with no
details, and a private channel will be arranged. Do not post vulnerability details publicly.

Reports are answered within 5 working days (STATED: this is a target. UNVERIFIED: no record of answer times is kept).

## What the core does and does not guarantee in pilot and prod (this round)

**Audit (stated limits).** The audit log is eventual, not instant. An event that could not be written to the audit
chain is parked in the outbox table and written by the next tick (step `audit_drain`). An event parked only in a
process's memory (the database was down for the outbox as well) is written at that process's next successful audit
write, and is lost if the process exits first. That write is not capped: after a long outage the next audit write
of a process also writes every event that process parked. Events a process could not write for a reason other than
an outage are kept in memory, counted in a warning, and lost when the process exits. An outbox row the database
refuses for such a reason is kept and fails the `audit_drain` step with a count. The eval and replay commands do not
write to the chain.

Tamper evidence of past rows is conditional. It holds only when the runtime login (1) does not own the audit tables
and (2) has no UPDATE, DELETE or TRUNCATE on `audit_entries`. `migrate --runtime-role` enforces (2): it grants the
runtime login SELECT and INSERT on `audit_entries` and `audit_checkpoints`, and the append-only triggers also refuse
UPDATE, DELETE and TRUNCATE (a test proves the real attempts fail). It does not enforce (1): it does not refuse a
runtime role that owns the audit tables (an owner can disable the triggers), so the operator must not make the runtime
login the owner. Two runtime rights are wider than they need to be today: DELETE on `audit_outbox` (events parked
there and not yet written can vanish; they are not yet in the chain, so nothing in the chain shows it) and INSERT on
`audit_checkpoints` (a planted row at the head's seq makes verification raise a false alarm). Both are tracked in
handover/core-b/tickets/A-audit-rights.md. Even then this is tamper evidence of past rows, not authenticity: a
runtime process that is itself taken over can append new rows with valid hashes, and the chain cannot tell those from
true ones. A signer and an anchor (checkpoints held outside the database) narrow this; they do not remove it.

**Stop.** A stop takes effect at the next gate check; a call already in flight is not interrupted; the command-line
eval and replay paths do not read the stop state. On PostgreSQL with the grants applied (`migrate --reset-role`), the
runtime's database login can add a stop and cannot clear one; only the reset login can, and its reset is written to
the audit log first. The reset login can append audit rows (as the runtime login already can). The database owner and
a superuser are outside this guarantee. The memory store guarantees nothing. Stated limits: (1) the guarantee is about
the state stored in the database, and the store names its schema in every stop-state statement so a temporary table
cannot hide a stop; a runtime process that is itself taken over can ignore any switch, so stop the process as well.
(2) "Audited first" is done by the `limits reset` command; the database does not force it, so a person holding the
reset login can clear a stop by hand with no audit row. (3) The reset login cannot add a stop row, but it can set the
old flag ON, which is also a stop (the safe direction). (4) A reset clears the stops visible to its clear statement:
a stop committed after that statement began stays ON, and one committed between the audit row and that statement is
cleared; the command reads the state back and exits 2 while it is still ON. (5) As of the last `migrate` that named all roles (the check runs only then: a role or grant added later is not seen
until the next run), `migrate` refuses, when it applies grants, any other role that could clear a stop through a grant on this schema's stop tables or through membership
in a role that holds one (or in the reset role), through UPDATE, DELETE or TRUNCATE on `kill_switch`, INSERT on
`kill_switch_clears` or TRIGGER on any of the three; below PostgreSQL 16 also every non-superuser role with CREATEROLE
(an operator who vouches for such a role can name it with `--accept-admin-role`; the names are printed and logged, the
CI log of that run is the record of who vouched, and a grant on the stop tables still lists the role and its members are
still listed, as is a vouched role that is a member of a listed role; vouching for the schema owner role seeds nothing), from 16 every holder of the ADMIN option on such a role or on the reset
role (so the login that created the reset role is listed until it revokes that option). It refuses when it cannot find the three stop tables in the schema the store
uses. A `migrate` that names no role is refused (exit 2) unless `--no-roles` is given, which applies the schema and checks
and grants nothing (first install only), so name all roles in ONE command. Outside the guarantee and not checked: the schema owner (it can DROP and recreate the stop tables: the
runtime login must not own the schema), superusers and managed-database admin roles that are not superusers
(`rds_superuser`, `azure_pg_admin`, `cloudsqlsuperuser`), SECURITY DEFINER functions or views of a privileged role
(review them), and a role whose only path is membership in the owner role, in a superuser or in a PostgreSQL predefined
role such as `pg_write_all_data`, and a role that may set `session_replication_role` (the append-only triggers do
not fire under `replica`) and holds DELETE or TRUNCATE on a stop table.

**Not guaranteed by the core this round.** In pilot and prod the approved write is performed by the client's own tool
(for example n8n or the CRM) with its own credential, not by the core. For that write the core therefore does NOT
guarantee: that the write matches the plan that was shown; that the named approver approved it; that it happened
exactly once; that the stop switch halts it; that it appears in the core's audit log. These belong to the client's
tool and its own log. Nothing in this package's texts may claim otherwise.

## Capped spend and masked model input: the two guarantees and their limits

**Capped spend.** Every model call the runtime makes goes through one model gate: before the call the most it could cost (system prompt, messages, documents, tool definitions and output schema at one token per byte, the route's full output, times the client's retry attempts) is booked against the agent's day and month budget, and the call is not made when it does not fit; after the call the booking is replaced by the real cost. This holds for model calls made through the gate on PostgreSQL with the grants applied.

Its limits: the `gate` (eval) and `replay` command lines are capped per process in memory (`--max-usd`; `gate` without it uses the agent's daily budget in demo and is refused in pilot and prod) and their calls are not audited one by one; the Bedrock guardrail detector's call is not metered; a stale price table is not refused yet. **A failed call can hold budget without real spend:** when a provider call fails and the provider did not clearly refuse it before doing any work (today that is an HTTP 400, 401, 403, 404, 413 or 422 as the only answer; a call that used up its retries is never treated as refused), the most that call could have cost stays counted against the day and month budget for about an hour (until the tick's expiry step closes it), so a wrong API key or throttling can use up a small daily budget although nothing was spent. The run's own cost moves only when a call is settled.

**Masked model input.** Every value the run has identified (a value in the run's redaction map) is replaced by its placeholder in everything sent to a model: each message and each document, on every call, including text added before the value was identified. This is not "nothing secret can reach a model": a value the redactor did not identify is sent as written, only the spelling the map holds is replaced, the system prompt and tool definitions are operator text and are not touched, and the `gate` and `replay` command lines and the judge have no run map (they redact their own input before sending).

## 1. Stated limits of redaction

The words in capitals (TESTED, MEASURED, FIXED and the others) and the technical terms are defined in the appendix, [Words used here](#words-used-here). The redactor and the secret finder are the same code. This file says "secret finder"; the README and the CHANGELOG say "redactor".

Redaction is pattern based and treats the end of a value the way the secret finder's own value pattern does. Two consequences are known and stated. UNVERIFIED (read in the code; the examples are as built, and each limit's status and evidence are in K46 and K84):

- An unquoted secret value that itself contains a plain (not encoded) space or `;` is masked only up to that character in pass one. Example: `password=my secret phrase`. Its tail is shown, because by the secret finder's definition the value ended there.
  - A quoted value with spaces (`password="my secret phrase"`) is masked whole.
  - A `,` or `&` inside a `key=value` value does not end it either. Then the plain copy of that value elsewhere in the text can stay readable (see K84).
  - Write a secret that holds a space inside quotes (`password="my secret phrase"`), or do not hand it to a tool.
- A form-encoded `;` or `&` inside a value is ambiguous. `password%3Dab%3Bzq9` can be one secret, or a key and a value followed by more text.
  - The secret finder decodes it and masks what its value pattern reaches.
  - It keeps what pass one masked whole when the decoded view would mask less.
  - It cannot know which reading the sender meant.

Each limit has its own status, evidence and owner in the gaps: see K46 (a value that holds a space or `;`) and K84 (punctuation inside a stored secret).

## Spend limits (stated limits)

Exact money and the no-lowering wall are in force; no-overspend holds for the live loop's main model call only and is NOT in force for the listed ungated sites until the model gate installs reserve/settle (F-install).

In force on PostgreSQL after migration 0011: money is exact decimal, and the runtime login can neither lower a booked amount nor change a cap (it can still read a cap, settle a hold it can name, add spend). The caps live in the table `hadavin_caps`, written only under the reset login. The reserve and settle functions exist and are tested.

The live loop's main model call reserves the worst case before the call and settles after: the reservation bounds the booked worst case per call; a reply costing more than the worst case is booked in full (an overshoot, audited); the kill switch is read before the reserve, not atomic with it. NOT gated: `_screen` llm_judge (charged after the fact), `cards.render_shadow` with a detector (an llm_judge cost there is not charged at all), `guard/bedrock_guardrail` (`apply_guardrail`), `k1b/loop.py`, `evals.py`, `guard/judge.py`. Concurrent use of those can overshoot a cap. A hold of a failed run (provider error, crash) stays booked on the day and month counters until an operator runs `release_expired_spend` (see the runbook); the tick only marks it expired. No text of this package may claim a hard spend cap beyond the main call of the live loop.
Control that does not depend on these limits: a tool is not handed a secret it does not need (least privilege). UNVERIFIED: this is the design rule; no test shows it for every tool.

## 2. What the tests show and what is still open

> **These items describe what tests showed on the gate, the secret finder and text folding, each run on its own. No test of the store ran on this branch. None of this describes an agent in use going through the gate. The shared branch is not the released code.**

As of 2026-11-20 15:44 UTC (commit 2552bcc95). The words TESTED, MEASURED and the others, and every technical term, are defined in the appendix, [Words used here](#words-used-here). Read the appendix first if a word is new.

### 2.0 State of the work

- WAITING: the gate is not installed. No point in the code that calls a model goes through it yet. The connector-and-store maintainer must install it.
- STATED (a written order dated 2026-11-20 06:30 UTC, not shipped with the kit): the connector-and-store maintainer will not install the gate yet. The model connectors cannot yet say "refused before any answer".
- TESTED: a batch of the whole test suite, without the slow-timing and live tests, gave 15,955 passed, 561 skipped, 74 expected failures and 10 failures. It ran on the merged code from 14:06 to 14:17 UTC on 2026-11-20.
- STATED (a development note dated 2026-11-20, not shipped). UNVERIFIED: no result line is on file for this split. 6 of the 10 failures were a fault of a secret finder change. It was fixed, and its 4 test files then passed (297 passed). Two were approval-message rows, re-recorded twice since, from the measured output. One is a project file that names a vendor. One failed on the older code too.
- STATED (a development note dated 2026-11-20, not shipped): a later batch of the same kind gave 16,071 passed and 2 failed. The 2 failures were the vendor-string test and a recording that was re-keyed since. UNVERIFIED: the commit of that batch (the note names 2552bcc95 only for the next batch).
- STATED (the same development note): the slow-timing tests on a quiet machine at commit 2552bcc95 gave 96 passed, 1 skipped and 0 failed in 427 seconds.
- The vendor-string test is a repository rule, not a security finding. It checks every file of the project for a vendor's brand string, and one project note outside the code holds one. MEASURED here: in a run of the documentation and brand tests on this head, it is the only one of 72 that fails.
- Since the first batch, these changed: the gate's safety net, the secret finder's punctuation, overlap and host-name rules, and four of the gate's deliberate code breaks.
  - 2.10 lists the batches run on the changed code.
  - The last row of 2.10 has no result line, so what it covers is UNVERIFIED.
- NOT RUN: a batch of the whole test suite whose commit is named and is the code this file describes.
- UNVERIFIED (read in the test file): five install tests are marked as strict expected failures until the gate is installed. Once it is installed, they pass, and that pass fails the batch. Then the connector-and-store maintainer removes the five marks.
- UNVERIFIED: no independent review of the gate as last changed is on file. FIXED on the gate means that the tests of the change pass, unless a review is named.

### 2.1 Masking before a model call (the gate)

Shown by tests. TESTED here means that test_model_gate.py and test_runmap_enforce_map.py passed in the batches named in 2.0. The tests added since passed in the batches listed in 2.10. The last row of 2.10 has no result line, so it does not count, and the safety-net piece rule below is UNVERIFIED:

- TESTED: before a call, the gate masks each known value with its placeholder. This covers message text and documents only. K8 lists what it skips.
- TESTED: the gate searches for no new values. The secret finder does that (K1).
- TESTED: if masking fails, the gate makes no call and reserves no money. Causes: text too long, content that is not text, past its size, step or time budget (its own refusal word), or text still changing after 4 maskings.
- TESTED: that refusal carries a refusal word and no text.
- TESTED: if no known value is present, the text goes out unchanged.
- TESTED: the gate does not change the calling code's messages, documents or run map.
- TESTED: the calling code must name its run map or state "no map". Leaving it out is an error, and so is a plain dict or a copy of the map. Only the test and replay command lines may state "no map" (K9).
- TESTED: the safety net refuses a call when a known secret of 4 or more characters is still readable.
- UNVERIFIED (no result line is on file; see 2.10 and K12): since the latest change it also reads a piece of a secret beside a placeholder, and decoded spellings (K78, K3).
- NOT RUN: the whole file of deliberate code breaks for the gate on this code (140 breaks; one is known to survive as equivalent). No result line is on file for single breaks run by hand.

Known gaps and fixed findings:

- **K1. Not protected:** a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; the secret finder is the control.
- **K2. Not masked, even when known:** any value under 3 characters. Three more cases apply to an identifier and to a secret of exactly 3 characters. They are an all-digit value under 6 characters, a common word (`admin`, `test`), and a copy that a letter or digit touches.
  - Example: the known identifier `abc123` (an account number, not a secret) stays readable inside `xabc1234`, because a letter touches it (MEASURED here).
  - A known phone number is masked where no digit touches it: `build4155550132` becomes `build<PHONE_1>`; `74155550132` stays (MEASURED here).
  - Rule: a secret of 4 or more characters is masked wherever its exact text appears, even when it is all digits or a common word. The exceptions are K3 to K9 and K65.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K3. Not masked by the gate:** a copy spelled differently from the run map. Such spellings include percent codes, web character codes, look-alike letters, hidden characters and the control codes terminals use for colours.
  - Example: the known identifier `qrs789`; the text `qrs&#55;89` (a web code for the digit 7) goes out as written (MEASURED here).
  - TESTED: for a known secret, the safety net now reads decoded spellings. A secret in full-width letters, in UTF-16, in percent codes, or split by NUL or zero-width characters refuses the call.
  - UNVERIFIED (read in the code): web character codes and backslash codes are decoded by the same step.
  - TESTED: an identifier in such a spelling still passes as written. A copy split by colour codes passes too (K79).
  - TESTED: for a known value that is not plain ASCII, the gate also masks its folded spellings.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate.
  - UNVERIFIED: whether the secret finder's text folding catches each such copy before the gate.
- **K4. Not masked:** the same value in other capital or small letters.
  - Example: known `db01.acme.example`, text `DB01.ACME.EXAMPLE` (MEASURED here).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K5. Not masked:** two known identifiers that overlap so that each is touched by a letter of the other. Neither is masked there.
  - Example: known identifiers `abcd` and `cdef`; the text `abcdef` goes out as written. Each standalone copy is still masked.
  - The rest of a held-back identifier also passes the safety net, which checks secrets only.
  - Two overlapping secrets, or a secret and an identifier, are now masked (K78).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K6. Not protected:** a clean key and a clean value that look sensitive only when joined.
  - Example: `"user_id": "abc123"`, where neither part is in the run map.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K7. Not masked:** a known value that itself looks like a placeholder or sits in angle brackets.
  - Example: a known identifier `ab<X_1>cd` goes out as written. For a secret of that shape the safety net refuses the call.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K8. Not masked:** the system prompt, tool descriptions, the role label (who speaks), extra message fields, the requested answer format and the route.
  - Example: an operator puts a customer's name in the system prompt; it goes out unmasked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate.
- **K9. Not masked:** anything, when the calling code states "no map".
  - Example: a replay of an old case sends its text as stored.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K10. Fixed:** the audit row said "map in use" when the map was empty. It also said so when the calling code had supplied its own masking function (allowed for tests). The row now says which.
  - Example: a run with an empty map writes "map empty", not the same row as one with 50 values.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K11. Fixed:** a known secret inside a forged marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a forged marker whose call number contains the known `S3cr3tPw`. Before this fix, `S3cr3tPw` went out.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K12. Changed, not shown fixed:** a secret at a held-back value's edge could leave its tail beside a placeholder.
  - Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A run gave `<SECRET_1><SECRET_2>`, with no leak.
  - UNVERIFIED (a development note names the test; no result line is on file; see 2.10): the safety net now refuses a call whose text holds `<SECRET_1>abcdef`. That is a piece of 4 or more characters of a known secret beside a placeholder. The same note says that test failed before the change.
  - Status: OPEN (the code is changed; FIXED needs a recorded batch of that test). Evidence: UNVERIFIED. Who acts: the text-and-masking maintainer records a batch.
- **K13. Not fully limited:** the time the gate spends on one model call. One budget per call covers the characters, the steps and two time limits of 6.0 seconds each. The first is processor time, read inside the masking step. The second is wall-clock time, read only between values and after each sweep.
  - TESTED: a deadline that passes inside the masking step refuses the call with the code `mask_budget_exceeded`.
  - TESTED: the masking step is given the call's own deadline. A deadline that passes after the start of the call stops it.
  - NOT REPRODUCED: a long stall inside one scan of one stretch of text was reported. A run of the reported shape, as understood, took 0.47 seconds of processor time for the gate's masking step. The secret finder took 0.89 seconds on the same text.
  - MEASURED earlier, before the current budget: 100 messages against a run map of 2,000 entries took 0.018 seconds.
  - Status: OPEN. Evidence: TESTED; NOT REPRODUCED (the stall). Who acts: the text-and-masking maintainer.
- **K14. Not protected:** a run's later tool-using calls. A planted secret of 4 or more characters makes each of them refuse. It does so when it equals a tool's name or a call number, or is a piece of a name in the tool list.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name. Later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the rule as built). Who acts: the owner decides which rule. If the owner does not decide, the plan is to keep the rule as built. Today it is the rule in force.
- **K15. Fixed:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody. See K66 for the tool list.
- **K16. Fixed:** stopping the program by hand while the gate masked, worked out the worst case, asked for a reservation, or in the instant after it, left no audit row. Now a row is written.
  - Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted".
  - The reservation stays booked: the worst case stays booked, not the real cost.
  - Not covered: a stop by hand inside settle or inside the audit write. Settle catches ordinary errors only, so such a stop after a paid reply leaves no row (UNVERIFIED, read in the code).
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: OPEN. Evidence: UNVERIFIED (stated in the code's notes, not run).
  - Who acts: the text-and-masking maintainer adds "one writer per run map" to its install request to the connector-and-store maintainer.
- **K64. Not protected:** a run's later calls, when planted text holds too many values. The limits are more than 4,096 values at a placeholder's edge (such as `password=>aaaa1`), or more than 20,480 values in all. The gate then refuses every later call of that run.
  - Example: one planted document with 4,097 such lines would stop the run (worked out from the code, not run).
  - The agent loop stops a run before that. At its default limit of 2,000 values, or 524,288 characters of values, the run ends asking for a person (UNVERIFIED, read in the code).
  - A separate per-key cap applies to the lookups of one key: see K85.
  - Status: OPEN. Evidence: TESTED (the gate's old cap of 256 held-back values is gone; 257 values no longer stop a run). The secret finder's separate limit of 256 values that need pairing across decoded views stays. Who acts: the text-and-masking maintainer.
- **K65. Not refused:** a known secret that spans a fixed framing word. The safety net checks each stretch of text between fixed framing words on its own.
  - Example: a known secret written as `tool read_logs` inside `password="tool read_logs"` is cut by the fixed word `tool ` and goes out as written.
  - TESTED: the safety net covers every known secret of 4 or more characters, not only held-back ones. A secret hidden in a made-up placeholder-shaped token that is not a key of the map refuses the call.
  - The safety net reads decoded spellings of a secret (K3), but not every spelling (K79, K80).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K66. Fixed:** a known value inside a tool's name. The gate masked it in the line where the model asked for the tool, but the tool list went out as written, so the model saw two names.
  - Now a name that is in the tool list stays exact in the line and in the marker. A secret that equals a listed name, or is a piece of one, refuses the call (see K14).
  - Example: the run map holds `<TENANT_1>` for `billing`. The tool `get_billing_info` is no longer rewritten to `get_<TENANT_1>_info`.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K67. Fixed (the list only):** the install hand-over list and the install test name the judge's call points. They are the agent loop, the approval cards, the approval summaries and the replay loop. A test fails if a new call point appears that the list does not know.
  - Example: the approval summary reaches the judge from a place the old list did not name.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K67a. Not installed:** the gate itself. No call point in the code goes through it yet, even though the list of call points is now complete (K67).
  - Example: the agent loop still calls the model connector directly.
  - Status: WAITING (a written install request to the connector-and-store maintainer; see 2.0 and K18). Evidence: UNVERIFIED (read in the code; five install tests are strict expected failures, see 2.0). Who acts: the connector-and-store maintainer.
- **K69. Not checked:** that the run map given to the gate is the run's own, current map. The gate refuses a plain dict and a `dict(run_map)` copy. It cannot tell the run's own map from another run's map, or from a run map built from a copy. An empty run map is accepted, and the audit row says "map empty".
  - Example: the calling code passes yesterday's run map object. Values found today are not masked, and the row says the map was used.
  - Status: OPEN. Evidence: TESTED (the dict refusal and the empty-map row); UNVERIFIED (the stale-map case, stated in the code).
  - Who acts: the owner decides it together with one question: whether the gate refuses a call when the run map is empty.
  - If the owner does not decide, the plan is to make the gate refuse an empty map. Today it accepts one. Then the text-and-masking maintainer changes the code.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example (UNVERIFIED, read from the code): the agent loop turns a model connector's error into a stop that asks for a person. A gate refusal is a different error, so it is not caught there. The planted-instruction check reports the same refusal as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector-and-store maintainer (written install request).
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED (source: the table of calls kept outside the gate by design, in `tests/test_gate_install_callers.py`). Evidence: UNVERIFIED (read in that table; no test checks that these calls cost money). Who acts: nobody.
- **K78. Fixed:** two known secrets that overlap in the text left part of one readable, and the safety net missed it.
  - Example: known `hunter2-ABCDEFGH` and `ABCDEFGH-ZZZZZZZZ`. The text `x hunter2-ABCDEFGH-ZZZZZZZZ y` used to go out as `x hunter2-<SECRET_2> y`. It now goes out as `x <SECRET_1><SECRET_2> y`, in either map order (MEASURED here).
  - TESTED: a secret and an identifier that overlap are masked with their own placeholders.
  - UNVERIFIED (no result line is on file; see K12 and 2.10): a piece of 4 or more characters of a known secret beside a placeholder refuses the call.
  - Status: FIXED for the overlap masking only. Evidence: TESTED (the overlap masking); MEASURED. Who acts: nobody. The piece refusal is not claimed as fixed (K12).
- **K79. Not refused by the safety net:** a base64 copy of a known secret, an identifier split by NUL characters, and any copy split by terminal colour codes. Each goes out as written.
  - Example: a known secret written in base64 inside a message reaches the model. A base64 copy is the secret finder's work (K37).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K80. Not read by the safety net:** these spellings and pieces of a known secret pass as written.
  - A piece shorter than 4 characters, a piece one character away from a placeholder, and a piece from the middle of a value between two placeholders.
  - The same value in other capital or small letters (K4).
  - Text encodings the decoder does not undo: UTF-7, quoted-printable, hex or ROT13 dumps, reversed text, look-alike letters that the standard folding keeps, and a secret wrapped across lines.
  - A copy in several stacked escape layers that crosses a window edge of a text over 65,536 characters.
  - Example: with known `abcdefghijkl` and two placeholders, a text that keeps `defghi` between them is sent.
  - The rest of a held-back identifier passes too, because the safety net checks secrets only (K5).
  - Status: STATED (the gate's own code notes). Evidence: UNVERIFIED (read in the code; one limit is pinned in K79). Who acts: nobody.
- **K80a. Changed, not shown fixed:** a known secret made only of punctuation (`!!!!!!!!`) is now read as a piece. A piece of 4 or more of its characters that starts or ends it beside a placeholder refuses the call.
  - Example (MEASURED here): `!!!!<HOST_1>` and `<HOST_1>!!!!` are refused.
  - Separators that start a private key's header line stay exempt.
  - Status: OPEN (the code is changed; FIXED needs a recorded batch of its test). Evidence: MEASURED here (the example); UNVERIFIED (the test; no result line, see 2.10). Who acts: the text-and-masking maintainer records a batch.
- **K80b. Not read as a piece, in any letter case:** the public words that start an authorization value. They are `Bearer`, `Basic`, `Token`, `Digest`, `OAuth`, `ApiKey`, `Negotiate`, `NTLM`, `AWS4-HMAC-SHA256`, `Bot` and `Key`.
  - The same word plus one more character of the secret is read.
  - Status: OPEN (a development note names a test for it; no result line is on file; PINNED is not claimed). Evidence: UNVERIFIED (see 2.10). Who acts: the text-and-masking maintainer records a batch.
- **K85. Refused more than needed:** the safety net can refuse ordinary text beside a placeholder. One planted value can make every later call of a run refuse.
  - Example: a known secret `the quick brown fox` makes the text `the <HOST_1>` look like a leak (MEASURED here: the net answers "leak"). The gate reports that as the code `held_value_left`, the same code as a real leak.
  - The message stays in the run's history, so each later call refuses.
  - UNVERIFIED (a development note names the tests; no result line is on file; see 2.10): the refusal is held as built, not PINNED. A strict expected failure records the wanted behaviour (ordinary words beside a placeholder sent).
  - UNVERIFIED (same note): a bare web address start (`https://`) beside a placeholder is not read as a piece. The public authorization words, in any letter case, are not read as a piece either (K80b).
  - UNVERIFIED (same note): one key of the map reads at most 4,096 hits of its first characters (both sides together).
    - A dense hostile text is refused with `mask_budget_exceeded` after about 4,096 lookups, in 0.02 s.
    - The shape is a value `aaaa` followed by 16,380 `c`, beside eight runs of 16,000 `a` and a placeholder.
    - Before, it was accepted after about 16,000 lookups per key and 0.54 s (UNVERIFIED: no run is on file).
    - The refusal stays while the text is in the run's history.
    - On 1,978 ordinary inputs the cap was never reached (UNVERIFIED: no run is on file).
  - UNVERIFIED (same note; no run is on file): the lookups no longer cut a slice before the first-characters test. A 65,536-character value beside 16 placeholders took 1.74 s before and 0.13 s after.
  - UNVERIFIED (same note): long pieces already looked up are kept as a 16-byte digest. The peak memory of the worst shape tried was 367 MB before and 7.1 MB after.
  - Status: OPEN (the refusal is pinned only by a test named in a development note with no result line). Evidence: MEASURED here (the "leak" answer); UNVERIFIED (the rest). Who acts: the text-and-masking maintainer records a batch.
- **K85a. Decisions not made on K85:** three questions are open. Should a piece need a letter-only minimum? Should this refusal get a code of its own? Does the per-key cap of 4,096 stay? None is built. The cap of 4,096 is a number chosen in the code.
  - Status: OPEN. Evidence: UNVERIFIED (no decision is on file; nothing to test). Who acts: the owner decides.

### 2.2 Spending cap

Shown by tests (the gate's tests in the batches named in 2.0):

- TESTED: the gate makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- TESTED: when a reply arrives with a usable cost, the gate settles that real cost.
- TESTED: when the model connector marks an error "refused before any answer", the gate settles 0.00 USD. This holds also for a call whose retries ran out, if every attempt carries that mark.
- NOT RUN: any test of the store's cap on this branch. The store code those tests check is not here, so they skip.

Known gaps:

- **K20. Not released:** the worst case of a failed call. The gate settles 0.00 USD only for an error the model connector marks "refused before any answer". No connector sets that mark yet, so every failed call keeps its worst case booked.
  - Example: a throttled call fails before any answer. With no mark, its worst case stays booked.
  - What the store keeps booked after that is the store's behaviour, and its code is not on this branch.
  - The gate cannot check the mark. A connector must set it only when no attempt may have been billed.
  - Status: WAITING. Evidence: TESTED (an unmarked failure is not settled; a marked one is settled at 0.00 USD); UNVERIFIED (no connector sets the mark, read in the code). Who acts: the connector-and-store maintainer (written request).
- **K21. Booked as free:** a reply with an empty cost field. The connectors' reply form fills an empty cost with 0.00 USD, and the gate settles 0.00 USD.
  - Example: a connector forgets to fill in the cost; a 0.80 USD call is booked as 0.00 USD.
  - Status: WAITING. Evidence: TESTED (the gate's side). UNVERIFIED: that a connector leaves the field empty. Who acts: the connector-and-store maintainer (written request).
- **K22. Not settled:** a reply with an unreadable cost. The worst case stays booked, not the real cost.
  - Example: a reply reports its cost as "not a number"; the full 1.00 USD stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40 USD; attempt 2 costs 0.30 USD; only 0.30 USD is booked.
  - Status: WAITING. Evidence: UNVERIFIED (read from the code). Who acts: the connector-and-store maintainer (written order).
- **K24. The gate passes a higher real cost to settle:** a call that costs more than its worst case is passed to settle at the real cost, on purpose.
  - Example: a call reserved at 1.00 USD that costs 1.20 USD is settled at 1.20 USD.
  - How often this happens depends on the worst-case formula, which does not exist yet (K25).
  - Status: PINNED. Evidence: TESTED (the gate's side). Who acts: nobody (as built).
- **K24a. Not shown:** how the store books a cost above the worst case. The store's code is not on this branch.
  - Status: OPEN. Evidence: NOT RUN (no test of the store's side ran here). Who acts: the connector-and-store maintainer, when its store code reaches this branch.
- **K25. Not written:** the worst-case formula for the gate. The gate takes the function from the installer. It must cover the system prompt, the messages, the tool schemas and the documents, and the attempts. No function in this tree does that.
  - Example: the one worst-case function in the tree prices only the system prompt and the messages, and only the replay command line uses it.
  - The gate accepts a worst case of 0.00 USD, so a faulty function could reserve nothing (UNVERIFIED, read in the code).
  - Status: WAITING. Evidence: UNVERIFIED (read from the code; nothing to test). Who acts: the connector-and-store maintainer (written order).
- **K26. Not enforced by the database:** the runtime login can rewrite the spend counters. On this branch it holds SELECT, INSERT and UPDATE on the tables `spend` and `spend_month`.
  - Example: faulty code could lower the booked amount.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If the owner does not decide, the plan is to tighten them. Today they are not tightened. Then the connector-and-store maintainer changes them.
- **K27. Not refused:** an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED (source: a development note dated 2026-11-20, not shipped with the kit). Evidence: NONE. Who acts: nobody.
- **K28. Not capped across processes:** the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED (source: a development note dated 2026-11-20, not shipped with the kit). Evidence: NONE. Who acts: nobody.

### 2.3 Stop switch

Shown by tests, and what is not:

- TESTED (the gate's tests): a refused reservation, including the stop switch's refusal, means no model call.
- UNVERIFIED: that the store refuses every reservation while the switch is on. This is in the connector-and-store maintainer's code. No test of it ran on this branch.
- NOT RUN: any end-to-end stop of a live run.

Known gaps:

- **K29. Not narrowed by the database:** the runtime login can change the stop switch and sign a stop record with any name. On this branch it holds SELECT, INSERT and UPDATE on the table `kill_switch`, and the migrations add no trigger on it.
  - Example: a stop record says "by: operator" when the runtime wrote it. The runtime can also set the flag back to off.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map and the migrations; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If the owner does not decide, the plan is to tighten them. Today they are not tightened. Then the connector-and-store maintainer changes them.
- **K30. Not stopped:** a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED (source: a development note dated 2026-11-20, not shipped with the kit). Evidence: NONE. Who acts: nobody.

### 2.4 Audit record

Shown by tests:

- TESTED (the gate's tests): the gate tries to write one audit row per call. The row holds the run, the type of action, who asked, the result, and a code from a fixed list.
- TESTED (the gate's tests): the gate's code holds no logging and no error text, and no audit row in those tests held a secret.
- TESTED (the gate's tests): if writing the row or settling fails with an ordinary error after the reply came back, the gate still returns the reply.

Known gaps:

- **K31. Not recorded:** whether anything was masked, and the route.
  - Example: an investigator cannot tell from the row whether a secret was masked.
  - Status: OPEN. Evidence: UNVERIFIED (read from the code: the row's map field covers map use only).
  - Who acts: the owner decides whether to add a "masked: yes or no" field and the route. If the owner does not decide, the plan is to add both. Today neither is added.
- **K32. Not shown on this branch:** whether a login other than the runtime login can add audit rows. Such logins belong to the connector-and-store maintainer's store code, which is not on this branch.
  - On this branch the audit tables are append-only for every login (UNVERIFIED, read from the migrations).
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the connector-and-store maintainer, when its store code reaches this branch.
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (source: a development note dated 2026-11-20, not shipped with the kit). Evidence: NONE. Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

Shown by tests. TESTED here means: in the batches named in 2.0. The tests added since passed in the batches listed in 2.10. The last row of 2.10 has no result line, so it does not count:

- TESTED: it finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- TESTED: it decodes base64 text and masks the whole base64 text when the decoded text holds a value it knows (K37).
- TESTED: one call runs up to 5 search rounds. A text still changing in the last round is refused whole (fail closed).
- TESTED: two values that overlap in the text are masked whole (K72).
- TESTED: a line it cannot mask in place is withheld.

Known gaps and fixed findings:

- **K34. Not found:** a secret in a shape the secret finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED (the published README, section "Limits and trust", since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K35. Not masked:** a bare number with no label.
  - Example: `ref 55556666 paid` stays as written (MEASURED here). In the released code, 24 of 43 such test lines were not masked (MEASURED in a recorded run on that code).
  - A development note dated 2026-11-20 calls this accepted. No written order for that acceptance is on file, so the acceptance is UNVERIFIED.
  - Status: OPEN. Evidence: MEASURED (the gap); UNVERIFIED (the acceptance). Who acts: the owner confirms the acceptance, or the text-and-masking maintainer finds the order.
- **K36. Fixed:** host names with no "host" word in front. A name under a private suffix is now masked whole. So is a label after the word `host` or `hostname` that ends in two digits or in a hyphen and a digit. The private suffixes are `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `.home.arpa`, and `.internal` or `.local` when no label or call follows.
  - Example: `db01.corp.example` becomes `<HOSTNAME_1>` (before: `<HOSTNAME_1>.example`); `host db01 is down` becomes `host <HOSTNAME_1> is down`; `hostname=db01 state=down` becomes `hostname=<HOSTNAME_1> state=down` (MEASURED here).
  - In the released code, 28 of 44 test lines left a label of the name readable (MEASURED in a recorded run on that code).
  - On this branch 7 of the same 44 do (MEASURED here: the 44 lines through `redact_text`).
  - An earlier test file marked 19 host-name rows as strict expected failures (a development note dated 2026-11-20). That 19 is not 28 minus 7 (21). The two-row difference is UNVERIFIED.
  - Names that stay readable, each pinned by a test:
    - a name with a public-looking ending and no private suffix (`db01.acme.example`, `db01.acme.test`);
    - the short in-cluster forms (`billing.payments.svc`, `billing.payments.svc.cluster.local`);
    - a private word in the middle of a name (`db01.internal.acme.example`);
    - a cloud name that mixes an address and a name (`ip-10-0-3-22.eu-west-1.compute.internal` becomes `ip-<IPV4_1>.eu-west-1.compute.internal`).
  - A label after `host` with one trailing digit (`host web1 down`) also stays. A strict expected failure records it.
  - Masked more than before (as built):
    - a program package name that holds a private word (`com.acme.corp.billing.Service`) is masked whole;
    - a build triple after `host` (`host x86_64-w64-mingw32 build`) is masked;
    - a name glued after a non-Latin letter is masked from its first Latin letter, digit, `_` or `-`; up to two characters before it can go into the placeholder.
  - A list of CPU and platform names after `host` (`host x86_64`, `host arm64 runner`) is kept.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K36a. Not decided:** whether to send clients a note on host names and what the masking now does to them (K36).
  - Status: OPEN. Evidence: UNVERIFIED (no decision is on file; nothing to test). Who acts: the owner decides.
- **K37. Fixed:** base64 text under 40 characters was not masked. Now the secret finder decodes base64 text of 12 or more characters. It masks the whole text as `<ENCODED_n>` when the decoded text holds a value it knows. It decodes to a depth of 3 levels (`defaults.B64_MAX_DEPTH`).
  - Example: `secret is cGFzc3dvcmQ9aHVudGVyMnp6` (base64 of `password=hunter2zz`) becomes `secret is <ENCODED_1>` (MEASURED here).
  - In the released code, 41 of 41 such test lines leaked (MEASURED in a recorded run on that code). The limits that stay are in K82 and K82a.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K38. Fixed:** a letter or `_x` glued behind an IPv4 address, a UUID, a phone number written with `+` or an IBAN beside `_` kept it unmasked. Now each is masked, and the glued text stays outside the placeholder.
  - Example: `10.20.30.40_x` now becomes `<IPV4_1>_x` (MEASURED here). An IBAN with `_x` glued behind it becomes `<IBAN_1>_x`. Shapes that are still not masked are in K70 and K71.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K39. Not proven:** that the repeated search finds every value. Each call repeats the patterns and the masking until a round changes no text. A call has 5 rounds in total: the first pass and 4 repeat rounds. A text still changing in round 5 is refused.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is masked.
  - Status: OPEN. Evidence: TESTED (the chain; the loop to a fixed point). Who acts: the text-and-masking maintainer.
- **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies. This happened when the token was found only after a shorter known secret inside it.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`. The line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end`. It now shows `note <BEARER_1>vw end` (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. See K68.
- **K41. Not fully limited:** how long one call of the secret finder takes. Its time budget is 6 seconds of processor time per call. It is read before each search round and inside each masking step, the finder build and the written-forms scan.
  - The budget is not read inside one pattern pass over one text, nor in the loop over the texts of one round.
  - The secret finder has no wall-clock limit. A caller that needs one must add it.
  - Example (MEASURED, processor time, on the test machine): the text `curl -u ` repeated up to the size cap took 4.5 to 5.4 seconds against the 6.0-second budget.
  - A machine 12 to 33 percent slower than the test machine refuses that text (worked out from those runs, not run). A real document of that shape is then lost.
  - Status: OPEN. Evidence: MEASURED. Who acts: the text-and-masking maintainer.
- **K42. Not masked later:** a secret first seen in a tool's error message. It does not enter the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED (read in the code: the error text is masked with a throw-away map). Who acts: the connector-and-store maintainer (written request).
- **K43. Not masked:** a secret spelled like the secret finder's own placeholders. Four shapes stay as typed and get no map entry.
  - A value made only of escaped secret placeholders (`‹SECRET_1›`, with angle quotes), alone or in a run.
  - A value made only of typed secret placeholders (`<SECRET_1> <SECRET_2>`).
  - A value made only of typed placeholders of any kind (`password=<EMAIL_1> <IPV4_1>`).
  - The cut-off start of a secret placeholder, from `<S` to `<SECRET_12`, alone or after such a run.
  - Example: `password=‹SECRET_1›` stays as written, on purpose. A tool's error text is read twice, and the first read wrote that placeholder. A real password `<S` or `<SEC` stays readable (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K44. Fixed:** a secret wrapped in look-alike angle quotes was left readable.
  - Example: `password=‹hunter2zz_1›` is now masked (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K45. Fixed for the one place found:** the secret finder, run again on its own output, turned real placeholders into new secrets. The place was the tool-error path.
  - Example: a tool error quoting `<SECRET_1>` no longer adds a new map entry.
  - Status: FIXED. Evidence: TESTED (that place). UNVERIFIED: that no other place does this. Who acts: nobody.
- **K46. Not masked whole:** a secret that holds a space or `;`. It is masked only up to that character.
  - Example: `password=my secret phrase` shows `password=<SECRET_1> secret phrase` (MEASURED here). A quoted value with spaces is masked whole.
  - A comma or `&` inside a value does not end it; then the plain copy can stay readable (K84).
  - Status: STATED (the SECURITY.md published on 2026-11-04). Evidence: MEASURED (here). Who acts: nobody.
- **K68. Fixed:** after the secret finder undid a half-made entry, an old record could survive, so a later placeholder with the same number could be restored to the wrong value.
  - The text stayed masked; nothing raw went to the model. A tool could have got the wrong account or credential.
  - Example: a token found and then undone left a record for `<BEARER_1>`. A new `<BEARER_1>` for another value was later restored as the old one.
  - Status: FIXED. Evidence: TESTED (two rollback cases). Who acts: nobody.
- **K70. Not masked, as built:** glued shapes the glued-text change leaves readable.
  - A phone number or card number written as one run of digits with a letter right before or after it (`x4155550132`, `telephone4155550132`, `x4242424242424242`).
  - A phone number without `+` with a letter after it (`415-555-0132x123`).
  - A phone number directly before a full stop that a letter, digit or `_` follows (`call 415-555-0132.Thanks`, `call +1 415-555-0142.x`).
  - An IBAN with a letter or digit glued before it, or written inside a file name, a path or an identifier (`acct_iban_DE89...`, `xDE89...`).
  - A US Social Security number with a letter glued to it. A host name with a letter, digit or `_` after its private suffix.
  - Example: `x4155550132` and `acct_iban_DE89370400440532013000` go out as written (MEASURED here).
  - Masked more than before (as built): a number of 10 to 16 digits before a full stop and a space is now masked as a phone number (`ref 1234567890. Next`). Later copies of it glued to a dot are then masked too (`1234567890.tar`).
  - UNVERIFIED (read in the code): a card number written as one run beside `_` (`card_4242424242424242`) is masked as a phone number and kept in the run's map as one.
  - A phone number with a country code and spaced groups before a full stop and a letter or digit is masked only in part. `call +44 20 7946 0958.Thanks` becomes `call <PHONE_1> 0958.Thanks`, and `call 0044 20 5550 1234.5` becomes `call <PHONE_1> 1234.5` (MEASURED here). A strict expected failure pins each (the earlier code did the same).
  - Masked more than before (as built): `tok 4155550132.-Ab9 x` becomes `tok <PHONE_1>.-Ab9 x` (MEASURED here); the earlier code left it. A test pins this output and a strict expected failure records the wanted one.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K70a. Not decided:** whether the defaults of K70, as built, are accepted.
  - Status: OPEN. Evidence: UNVERIFIED (no decision is on file; nothing to test). Who acts: the owner decides.
- **K71. Readable remainder of a long token:** a UUID or a number of 10 or 11 digits is cut out of a long token. It must be set off by `_` or a letter. The rest of the token stays readable when it is under 40 characters. Before the change, the whole token was masked as one value.
  - Example (MEASURED here): `tok_<uuid>_` followed by 32 characters becomes `tok_<UUID_1>_` and the same 32 characters, readable. A remainder of 40 characters or more is masked too.
  - A letter does the same: `tok_<uuid>x` followed by the same 32 characters becomes `tok_<UUID_1>x` and the 32 characters (MEASURED here).
  - A remainder can be up to 39 characters; the measured rows hold 20, 30 and 32.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. This is the limit as built. A change that keeps the token whole is planned and not built.
- **K72. Fixed:** two overlapping values left a readable part of a value the map holds. One case was a written form completed only in a later round. The other was two values that overlap as raw text.
  - Example: plain values `abcdefgh` and `efghijkl` in `abcdefghijkl` used to become `<S1>ijkl`. Both are now masked whole, in either order.
  - A secret that overlaps a value held as another kind now gets a secret entry of its own, and a standalone copy of it is masked as a secret. Before, it reused the other kind's placeholder. Two secrets, or two identifiers, still reuse the held placeholder.
  - The work of the overlap check is counted as it is found, every 256 occurrences. It is no longer counted after the list of occurrences exists, so a hostile text is refused before it uses the memory.
  - The read-back at an edge is made once per edge and rule. Each further place of the same anchor costs a 32nd of a comparison.
  - Limits that stay, each a refusal of the whole call (K73): a sweep still changing after 4 passes, and more than 1,000,000 characters of overlap unions in one call.
  - A long known value written beside its own repeating pattern can need too much work and is refused. UNVERIFIED here, not re-run (a test pins the numbers): a value `ab` repeated 2,000 times (4,000 characters) beside its own period in a 12,002-character text is accepted (1.94 million units). A periodic value of up to about 7,000 characters is accepted. One of 8,000 or more is refused (4.50 million units; the limit is 4 million).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K73. Refused, not read:** a hostile text can make the secret finder refuse a whole document. The refusals fail closed: nothing is shown, and a real document in the same text is lost.
  - `InputTooLarge` is the time or size limit. `NotSettled` is a text still changing in the last round.
  - `SpelledWorkTooMuch` is used past 4,000,000 units of work in one masking step.
  - `SpelledMemoryTooMuch` is used past 1,000,000 characters of written forms in one call.
  - `SpelledNotSettled` and `SpelledUnionTooMuch` come from the overlap step (K72).
  - `FinderMemoryTooMuch` comes from the memory cap (K74).
  - Example (MEASURED): a text of 2,800 written forms in 213,000 characters, then 262,000 characters of copies, needs 6.3 million units. It is refused after 0.49 seconds of processor time.
  - Example (UNVERIFIED here, not re-run): a text that names one known value of 4,900 characters 1,800 times is masked, and 1,900 times is refused.
  - All clocks of these limits read the processor time of the thread (`time.thread_time()`).
  - An older note of the overlap work says "10 seconds". That is a wall-clock figure from one run on a loaded machine. It is not a limit.
  - Status: STATED (written in the code's own notes). Evidence: MEASURED. Who acts: nobody.
- **K74. Fixed:** the memory the secret finder held for very large plain values had no limit. Eight values of 260,000 characters in one call peaked at about 960 MB and took about 9 s. MEASURED: 960 MB and 9.17 s in one run; another recorded run printed 956 MB.
  - Now one build of the finder is refused past 786,432 entries of its search tree (about 360 MB, worked out from measured rates). The refusal word is `FinderMemoryTooMuch`.
  - A run whose map holds more than 524,288 characters of values stops and asks for a person.
  - TESTED: the eight-value shape above is now refused.
  - Not bounded: the pattern passes before the build, finders kept from earlier builds, and the extra spellings of values that are not plain ASCII.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K74a. Not decided:** whether the two limits of K74 (786,432 entries and 524,288 characters of values) are approved. They are defaults chosen in the code.
  - Status: OPEN. Evidence: UNVERIFIED (no approval is on file; nothing to test). Who acts: the owner decides.
- **K75. Extra map entry, not prevented, pinned:** a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. The model sees a secret placeholder instead of the kind. Nothing real is stored in that entry.
  - Example: `password=‹EMAIL_1› host` becomes `password=<SECRET_1> host`, and `<SECRET_1>` stands for `‹EMAIL_1›` (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The alternative (exempt the escaped tokens of other kinds on the tool-error path only) is not built.
- **K76. Not prevented, pinned:** a placeholder written in a spelled form can come back from the secret finder decoded. Examples are `&lt;TENANT_1&gt;`, `%3CTENANT_1%3E` and `&#60;IPV4_1&#62;`. This happens when its digits are not masked.
  - No value stands behind such a placeholder: the run map has no such key, so a later restore gives nothing.
  - A probe found no case in which this returns a real value. That is a probe, not a proof.
  - Example: `&lt;TENANT_1&gt;` comes back as `<TENANT_1>`; `&lt;TENANT_4155550132&gt;` becomes `&lt;TENANT_<PHONE_1>&gt;` (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K77. Fixed:** a password stored with punctuation, a wrapper or an escaped edge at its ends left its plain copy readable.
  - Example: `password=hunter22, hunter22` used to leave the second `hunter22` readable. It now becomes `password=<SECRET_1> <SECRET_2>` (MEASURED here).
  - The same holds for a leading bracket (`password=(hunter22), hunter22`) and a wrapper such as `**hunter22**`.
  - It also holds for an escaped or encoded edge, at the start or the end. Examples are `%0A`, `%XX`, a backslash-u or backslash-x code, `&quot;`, `&#10;`, and a tag such as `<br/>` or `</b>` (`hunter22%0A then hunter22`, `<br/>hunter22 then hunter22`). At the end only, a cut-short form from a closed list (`<br`, `&quot`) is read too.
  - An all-capital value of the shape `ADMIN_1` or `DB_PASS_2` now gets its plain copy too (`password=ADMIN_1, ADMIN_1` becomes `password=<SECRET_1> <SECRET_2>`, MEASURED here). A value that holds one stray `‹` or `›` keeps its plain copy as well (`password=hunter22!› then hunter22`, MEASURED here).
  - One secret then has two placeholders. Both restore to their own text.
  - No plain copy is made when the value is a "no value" word with punctuation (`none!`).
  - No plain copy is made when its core is the text of a real placeholder. Example: `password=EMAIL_1, EMAIL_1 and a@example.com` masks the real address, and the typed `EMAIL_1` stays as written (a stated limit).
  - No plain copy is made when the value holds a look-alike placeholder token (`‹SECRET_1›`), or the edge cut removed both look-alike brackets of one.
  - No plain copy is made when the value is over 4,096 characters and the core differs from it by 16 characters or fewer. A long private key would otherwise take twice the memory.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. What stays readable is in K84.
- **K81. Not masked by any step:** some text reaches the AI service on paths that skip the secret finder. The gate's safety net, where it runs, is the only check left.
  - The replay command line, when the operator states the stored cases are already masked: the cases go out as stored, and the gate has no map.
  - The replay loop's copy of the model's own tool call, and its alert time field, which is checked only as a timestamp.
  - An extraction function that sends the caller's document unmasked; no code calls it.
  - A demo that sends the question a user typed.
  - The check that every model-calling module is registered works per module, not per call (UNVERIFIED, read).
  - Status: OPEN. Evidence: UNVERIFIED (read in the code). Who acts: the connector-and-store maintainer, once a decision on each path is written.
- **K82. Not decoded by the base64 view:** these eight base64 cases stay readable even when they hold a secret. Cases 1 to 4 and 6 each have a named test that is a strict expected failure. Cases 5, 7 and 8 have no test (K82a).
  1. A blob glued to other base64 characters, such as a path (`/v1/blob/` + the blob). Test: `test_limit_glued_prefix`.
  2. A blob split across fields. Test: `test_limit_split_fields`.
  3. A wrapped blob with a log prefix on each line. Test: `test_limit_log_prefixed_lines`.
  4. Base32 and hex. Test: `test_limit_base32_hex`.
  5. Base85, compressed data and quoted-printable text. No test.
  6. A decoded text in which 10 percent or more of the characters are not printable, such as a blob padded with blank-looking characters. Test: `test_limit_padded_blob`.
  7. A blob of capital letters, digits and `_` written between angle brackets. No test.
  8. Base64 whose decoded text holds no shape the secret finder knows (`aHVudGVyMnp6IQ==`, MEASURED here). No test.
  - Status: PINNED for cases 1, 2, 3, 4 and 6 (5 of 8). Evidence: TESTED (the tests are in `tests/test_b64_scan.py`). Who acts: nobody.
- **K82a. Not pinned:** cases 5, 7 and 8 of K82 have no test.
  - Status: OPEN. Evidence: UNVERIFIED (read in the code). Who acts: the text-and-masking maintainer adds a test, or states the limit.
- **K84. Not masked:** the plain copy of a password stored with punctuation inside it, or with an escape that is not on the list.
  - Example: `password=hunter22,x and hunter22` leaves the second `hunter22` readable (MEASURED here). The same holds for `hunter22.x` and `hunter22&x=1`.
  - A double-encoded edge stays: `password=hunter22%250A then hunter22` leaves the second `hunter22` readable (MEASURED here).
  - Not done (UNVERIFIED here, not run):
    - a named entity outside the list at the start of a value (`&copy;`);
    - a mixed-case cut-short entity (`&QUOT`);
    - a tag longer than 16 characters at an edge.
  - Closed since the last version (see K77): `%0A`, `&quot;` and `<br/>` at an edge, an all-capital value such as `ADMIN_1`, and a value with one stray `‹` or `›`. Still open by design of the fix: a password wrapped in a look-alike token (`‹SECRET_x›`) gets no second entry.
  - Status: OPEN. Evidence: MEASURED; UNVERIFIED (the not-done list). Who acts: the text-and-masking maintainer; no fix for interior punctuation is built, and whether to accept it as a stated limit is the owner's to decide.

### 2.6 Text folding (look-alike and hidden characters)

Shown by tests (in the batches named in 2.0):

- TESTED: before the secret finder searches, it folds the text. Look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (see README, section "Python version").

Known gaps and fixed findings:

- **K47. Fixed:** the secret finder's own look-alike search was missing from the shared branch. It is there now.
  - Example: `password=x` written with a Cyrillic "а" is now found.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K48. Not decoded by folding:** escape codes; look-alikes added after Unicode edition 15.1; hidden marks outside two character blocks.
  - Example: the escape code `&#49;` (the code for the digit 1) is not read as `1`, so `abc&#49;` stays as written (MEASURED here).
  - Status: STATED (source: the written limits of the text folding work, dated 2026-11-20, not shipped with the kit). Evidence: UNVERIFIED (a reviewer's reading confirms the limits). Who acts: nobody.
- **K49. Not flagged:** the Chinese character for zero (Unicode name IDEOGRAPHIC NUMBER ZERO, 〇) inside a Latin word.
  - Example: `pay` + 〇 + `al` is not called mixed script. MEASURED: it is the only such character in the folding table.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K50. Over-matching, measured:** the text-folding scan finds a known name inside a longer word or across a space. No masking path uses this scan yet (K83).
  - Example: known `mary` found in `summary`.
  - Setup: hit rates per scan of one 10,000-character chunk of ordinary Latin text (repository prose and code, library docstrings, generated text). The values were drawn at random. MEASURED on 2026-11-20.
  - Hit rates of names: 4 letters 5.3 %; 5 letters 1.0 %; 6 letters 0.4 %; 8 letters or more 0.
  - Corpus words of 5 to 10 letters: 3.9 to 4.1 % in the two recorded runs. The draw is hash-seeded, so this figure moves between runs. A third figure of 4.5 % is in a review only (UNVERIFIED).
  - ASCII ids of 4 to 5 characters 0.22 %; 6 digits 0.007 %.
  - A value that is a whole word of the text counts as a hit. These rates are not a bound for tickets, e-mail, chat or real values.
  - Share of the hits that mask a fragment of a word: 94 % (4 letters), 63.4 % (5 letters), 99 % (ids), 9 % (6-letter names). These shares are not false-hit rates.
  - Hit rates on real interface text: Russian values of 4 to 8 letters 7.6 %; Chinese values of 2 characters 5.2 %. Arabic and Devanagari: synthetic text only, unknown.
  - Status: STATED (source: a measurement note dated 2026-11-20, not shipped with the kit). Evidence: MEASURED. Who acts: nobody (the first user of this scan measures again).
- **K51. Limited by two time budgets:** the planted-instruction check stops at 30 seconds of processor time per check, or at 60 seconds of wall-clock time. It then flags the run as "guard unavailable" (fail closed).
  - The processor time is that of the thread that runs the check. The wall-clock limit is 2 times the processor budget.
  - From the second step of one check on, the processor time still needed may not pass half the wall-clock time left. This is stricter than 2 times: it can flag a check early, not late.
  - The real bound is the deadline plus the longest stretch between two readings of the clocks.
  - Example: a constructed text of 2,000,000 characters took 185 seconds of processor time without the budget and was flagged at 30.1 seconds with it. MEASURED on the build machine, before the wall-clock limit existed.
  - A machine about 1.9 times slower than the build machine would flag the slowest ordinary 2,000,000-character text measured (16.0 s) on every run (worked out, not run).
  - The work on a protected value inside one scan has no clock reading inside it (MEASURED: 7.2 to 7.5 s for a value of 236,879 distinct letters).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The budgets and their scope (per check) are the defaults as built.
- **K52. Refused, not read:** a long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example (MEASURED): 300,000 characters of Chinese, and of Japanese, were refused. Russian prose of that size is read.
  - NOT RUN: a measure of the shortest length that is refused.
  - Status: STATED (source: a development note dated 2026-11-20, not shipped with the kit). Evidence: MEASURED. Who acts: nobody.
- **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation. Three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place.
  - A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - This choice changed the class of 30 code points. They are 20 code points (dashes and the minus sign), 6 quotes and 3 slash look-alikes. The last is the replacement character U+FFFD, which the fold now drops.
  - Each of the 30 has a test and a deliberate code break that the tests catch.
  - Status: PINNED (chosen in a written order dated 2026-11-20 06:15 UTC, not shipped with the kit). Evidence: TESTED. Who acts: nobody.
- **K54. Finds more than before:** an invisible character between a Latin letter and its accent.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED (accepted in a written order dated 2026-11-20 05:47 UTC, not shipped with the kit). Evidence: TESTED. Who acts: nobody.
- **K55. Not decided:** the same wider matching in Korean, Japanese and Indian scripts, for the grounding check.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading).
  - Who acts: the owner decides whether to accept it. If the owner does not decide, the plan is to bring back the older rule for those scripts. Today the wider matching applies. Then the text-and-masking maintainer changes it.
- **K56. Fixed:** a secret stored as `Müller` but shown with a separate accent mark was not masked in tool output.
  - Example: `Mu` + combining accent + `ller` is masked again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K57. Fixed:** look-alike padding before a 32,768-character boundary could hide a planted order from the planted-instruction check.
  - Example: "ignore previous instructions" split across that boundary is found again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K58. Fixed:** on the wrong Python, the connection to the secrets vault was built before the start-up refusal. The refusal now comes first.
  - Example: a pilot build on the wrong Python stops before it builds the connection to the secrets vault.
  - Status: FIXED. Evidence: TESTED (one test, on Python 3.13 with the version faked). Who acts: nobody.
  - NOT RUN: a check of other outside services.
- **K83. Not wired:** 14 public functions of text folding have no caller in the product (UNVERIFIED: a search of `src/` found none). They are working code with tests and deliberate code breaks, kept in the security path.
  - Example (UNVERIFIED, read in the code): the name-matching scan of K50 is one of them; no masking or approval step calls it.
  - The module's own note now also names 8 other public names (`FILLERS`, `key_tag`, `FOLD_VERSION`, `squeeze`, `AllowVerdict`, `fold_views`, `squeeze_views`, `scan_keyset`) as internal helpers, reached only from inside the module.
  - Status: OPEN. Evidence: UNVERIFIED (read in the code). Who acts: the owner decides whether to move or delete them. Until then nothing moves.

### 2.7 Approval messages

Not shown by recorded tests:

- UNVERIFIED: the secret finder runs first on each free-text path found that writes an approval message. A development note names a batch on the branch where the change was built. No result line for it is in 2.10.
- That batch ran before the change joined the shared branch.
- UNVERIFIED (same batch): web addresses are made unclickable last (a dot written as `[.]`).

Read, not tested:

- UNVERIFIED (read in the code; no recorded batch names its test): a message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:

- **K59. Not masked:** the "requested by" line and other id fields.
  - Example (UNVERIFIED: read from the code, not tried on a real chat tool): a requester id such as `chat:U1|<!channel>` could make the chat tool notify everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector-and-store maintainer (written request).
- **K60. Not proven:** that no clickable link remains. The old test used the same patterns as the code it tested. A new test uses its own patterns and also checks against a link-finding library.
  - Example (UNVERIFIED): a link whose end is not in the test's own, finite list of web-address endings could still slip past both.
  - Status: OPEN. Evidence: TESTED (the independent test); UNVERIFIED (the missed link). Who acts: the text-and-masking maintainer.
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` becomes `<EMAIL_1>9` (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
- **K62. Not checked:** approval summaries stored before these fixes, as shown on the admin page.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: the text-and-masking maintainer.

MEASURED slowdown of approval-message masking on the joined code (median, on one test machine):

- a 174-character message took 0.00126 seconds before and 0.00360 seconds now;
- a 71,179-character message took 0.367 seconds before and 0.655 seconds now.

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. Once the text-folding change ships, by design a pilot or prod install there succeeds and the program refuses to start.
  - Example: an operator installs on 3.12; the program then refuses to start (see README, section "Python version").
  - Status: OPEN. Evidence: NOT RUN (no pilot start on 3.12 was tried). UNVERIFIED (read from the file): that the project file allows 3.12.
  - Who acts: the connector-and-store maintainer.

### 2.9 What was not run (NOT RUN)

- A batch of the whole test suite whose commit is named and is the code this file describes (2.0 has the batches that are on record).
- Python 3.12 on this code. UNVERIFIED (a development note says the whole suite ran on Python 3.12 at an earlier commit; no result line is on file).
- The store's tests on database version 17. UNVERIFIED (a development note says the database test files ran on version 17 at an earlier commit and the store's own tests skipped there; no result line is on file).
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The long-token change (not built).
- The whole files of deliberate code breaks for text folding (268 breaks), the gate (140) and the finder (130) on this code. The files for the base64 and host-name change (58), the glued-text change (43) and the punctuation change (35) ran whole on separate branches before they merged. UNVERIFIED (a development note says so; no result line is on file).

### 2.10 Batches on file (separate copies of the code)

Each row is a batch run on a separate copy of the code. The result lines are in development notes dated 2026-11-20, not shipped with the kit. None of these is a batch of the whole suite.

| Change | Tests in the batch | Result | Result line on file |
|---|---|---|---|
| The gate honours "refused before any answer" on an exhausted call | gate tests, install-callers test, picked-up test | 267 passed, 1 skipped, 5 expected failures. The whole file of deliberate breaks was NOT RUN. | yes |
| Merge of the gate and secret finder changes | base64, run-map, gate, repeat-round and break-list tests | 495 passed, 1 skipped, 4 expected failures | yes |
| Punctuation at the end of a secret value | five test files named in the note | 2,760 passed, 41 expected failures. One earlier run had a timing test red under load. | yes |
| Glued text, remaining cases | three test files | 2,544 passed, 46 expected failures | yes |
| Overlaps and repeat rounds | ten test files, timing tests included | 2,498 passed in 197.9 s | yes |
| Host-name patterns | host-name and approval-path test files | 53 passed, 1 expected failure | yes |
| Time budget of the planted-instruction read | text-folding test files; then the timing rows | 1,247 passed in 238 s; 19 timing rows passed in 52 s | yes |
| Gate safety net, first round of fixes | a broad run at commit d462a4c80 | 8 failed, 10,608 passed. The note lists the 8. | yes |
| Gate safety net: piece lookups, per-key cap, separator-only values, authorization words | new tests named in the note | UNVERIFIED: the note names the tests and the figures but holds no result line | no |

## Words used here

Evidence words. Each finding, and each statement about a test or a measurement, carries one of these. Plain explanations do not:

- TESTED: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is written in a file of the project. A TESTED line names its test or batch where 2.0, the opening line of a section or 2.10 gives one. On other lines the test is found by the K number or the topic, and this file does not claim a name on every line.
- MEASURED: a number or an output printed by a direct call or by a recorded run.
  - "MEASURED here" means printed by a direct call on the code at commit 2552bcc95.
  - Any other MEASURED line is a recorded run on a separate copy or on the released code, as that line says.
  - A figure with no recorded run is UNVERIFIED.
- UNVERIFIED: the only basis is someone reading the code or the text, or a note that names tests but holds no result line. Nothing recorded shows it.
- NOT REPRODUCED: a fault was reported. A later run of the reported case, as it was understood, did not show it. The exact case of the report is not on file.
- NOT RUN: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- NONE: no test, run or reading is named. The gap is written down from a written source only, and the line names that source.

Status words (one per known gap):

- FIXED: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on a separate copy or on the merged code. It is not in the released code.
- PINNED: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes. Whoever closes the gap removes that mark.
- STATED: written down in a named source, with no test. Each STATED line names the kind of its source and its date. Nobody is asked to act. "Accepted" is used only where a decision is on file; otherwise the line says "not prevented".
- WAITING: another maintainer must act, and a written request or a written order exists.
- OPEN: nobody has fixed or decided it yet. The line names who must act.

People and code:

- The owner: the person who owns Hadavin and has the final say. The owner decides the open questions named below.
- The connector-and-store maintainer: whoever owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- The text-and-masking maintainer: whoever owns the gate, the secret finder and text folding.
- Reviewer: an independent checker who only reads.
- Operator: the person who installs and runs the kit for a client.
- The kit: this software package.
- Stages: demo (made-up data), pilot (a first, limited use with a real client) and prod (normal live use).
- The shared branch: the pushed line of changes this file describes.
- The released code: what clients get.
- Test: a small program that checks one behaviour.
- Batch: one recorded run of many tests.
- Deliberate code break: a planted fault in the code, used to prove a test can fail. A break that no test catches "survives". A break that cannot change any output is "equivalent".
- Kn: the number of a known gap in this list. A letter after the number (K36a) is a separate question or gap that belongs to that one. A known gap is a weakness we know about, or a gap fixed in this work.

Model and run words:

- Model: the outside AI service that reads text and answers. A model call is one request to it. The system prompt holds the standing instructions sent with each model call.
- Guardrail call: a separate request to the cloud vendor's safety service. It is not a model call.
- Route: which AI service and which model a call goes to.
- Model connector: the code that talks to one AI service and reports the cost of each call.
- Run: one job of one agent, from start to finish. The agent loop is the code that drives a run step by step.
- Tool: an action an agent may use, such as a search. A tool result is the text a tool returns. Each tool call gets a call number. The tool list holds the tools' names and descriptions, sent with a model call.
- Calling code: the program code that hands a call to the gate.
- Test and replay command lines: two staff programs that run saved test cases or re-play a stored case.
- Judge: a model call that rates a text. The planted-instruction check and the approval code use it.
- Prompt registry: the fixed list of system prompts that ship with the kit.
- Planted text: text an attacker put into a document or tool result so that the agent reads it.
- Planted-instruction check: the check that looks for planted orders such as "ignore previous instructions".
- Guard failure: the planted-instruction check's report that it could not finish.
- Grounding check: the check that a name an agent proposes to act on appears in a tool result it cites.
- Approval message: the message that asks a person to approve an action an agent proposes.
- Chat channel: the chat tool where approval messages are posted.
- Admin page: the staff web page that shows stored approval summaries.

Masking words:

- Sensitive value: a secret (password, key, token) or an identifier (e-mail address, host name, account number).
- Known value: a sensitive value already in the run map.
- Mask: put a placeholder where a sensitive value was.
- Placeholder: a fixed text, such as `<SECRET_1>`, that the model sees in place of the value.
- Run map: one table per run, kept in memory, that records which real value each placeholder stands for.
- Restore: put the real value back for a tool that needs it.
- The secret finder: the code that searches new text for sensitive values by their shape and masks them. Only it adds to the run map. The README and the CHANGELOG call the same code the redactor.
- Pass one and second pass: pass one is the secret finder's first read of the text as written. The second pass reads decoded and folded views of the same text.
- Sweep: one walk over a text that replaces every copy of the known values.
- Fixed point: a text that one more round of the same step no longer changes.
- Units of work: the secret finder's own count of the steps in one masking step. The limits are in K72 and K73.
- Search tree and its entries: the structure the secret finder builds to look for many values at once. Its memory is capped by the number of entries (K74).
- HMAC: a hash made with a secret key, so that nobody without the key can recompute it.
- CODEOWNERS: a file in the repository that names who must approve a change to a path.
- Search round: one pass of the secret finder's patterns, then one masking of every copy of the known values. One call of the secret finder runs up to 5 search rounds.
- Kind: the type the secret finder gives each value it finds, such as password, key, token, e-mail or host name.
- Withheld: the secret finder hides a whole line it cannot mask in place, and shows a fixed note.
- Glued: written directly against another character, with no space between.
- Fail closed: when in doubt, refuse the text or the call rather than let it through.
- Text folding: turning look-alike letters, invisible characters and accents into one plain spelling before searching.
- Unicode: the world standard list of characters; each Python version carries one edition of it.
- base64: a common way of writing any data as letters and digits. The base64 view: the secret finder's step that decodes base64 text and searches the decoded text.
- The gate: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- Installed: placed at every point in the code that calls a model. The gate is not installed yet.
- Held back: a known value at a placeholder's edge (it starts with `>` or ends with `<`), or a piece of a placeholder. The gate masks it last.
- Safety net: the gate's last check on each stretch of text before it is sent. It refuses the call when it finds a known secret that is still readable.
- Framing marker: the fixed line the agent loop puts around each tool result. It holds fixed words, the call number and the tool's name. A forged marker is a copy of that line written by planted text.

Money and record words:

- All amounts are in US dollars (USD).
- The store: the database that records spending, reservations, the stop switch and the audit record. The secrets vault is the separate place where secrets are kept.
- Cap: the most money one agent may spend in a day and in a month.
- Worst case: the most a model call could cost.
- Reserve: before a call, count its worst case against the cap.
- Settle: after the call, book the real cost instead of the worst case.
- Booked: the amount counted against the cap at any moment.
- Empty cost field: a reply whose cost was never filled in; it reads as 0.00 USD.
- Unreadable cost: a cost that is absent, negative or not a number.
- Price table: the list of prices per AI service used to work out the worst case.
- Stop switch: a flag in the store. While it is on, the store is meant to refuse every new reservation. A stop record says who turned it on.
- Database login: a named account the software uses to reach the store. The grant map on this branch names a runtime login.
- Audit row: one line in the permanent record of what happened. It holds short codes, not message text.
- Refusal word: the exact short word the gate or store prints when it refuses.
