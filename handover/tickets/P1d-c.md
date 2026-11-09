# Package ticket P1d-c: an operator cannot see what is inside an approval request whose card was withheld (ledger BL-core-p1d-010, BN-P1d-9). DRAFT revision 1 (plan review round 1 not yet run). Options-first: the lead (and, for option C, the owner) chooses.

**Status (2026-11-09 06:40 UTC / 12:10 IST):** text only, no code, nothing run for this ticket. Drafted by `egm:egm-draft` (headless; the skill's `resources/execution_instructions.md` is missing from the plugin cache). P1d behaviour cited here (withheld card, `WITHHELD_NOTICE`, per-leaf notice in `redact_value`, the operator log line, the approve refusal) is from ticket P1d rev 5 and `round5-resolve.md` and is UNVERIFIED until P1d is built. Code facts marked R were read on `core/cloud-handover` head `391767b`. Marker: CODE-LAST v1.
**Scope check against the sibling report:** no sibling S1-S16 is assigned to P1d-c by P1d rev 5 or round5-resolve. S8-S10, S13-S15 are inside P1d (one choke point); S6 is P2d-2; S11, S12 and S16 are P1d-b (ledger 006, 009; P1d.md line 176). So this ticket covers ledger row 010 only.

## The problem in plain words
After P1d, when an approval request's text holds something that looks like a split secret, the card sent to the approvers shows a fixed sentence instead of the text, has no buttons, and cannot be approved. The operator (the person who runs the studio's deployment for the client) gets one log line with the request id and the reason, but no way to see WHICH part of the request caused it. Today (R) the only ways out are: the request moves up its approval steps and then expires (`requests.sweep`), or someone reads the raw request in the database. The first wastes the approvers' time on a request they cannot act on; the second shows the raw secret to a person and is not logged. If false withholds happen often (P1d BS-3 measures the rate), a request the business needs is blocked with no explanation.

## Words used
- **Withheld request** = a stored approval request whose card P1d replaced by `WITHHELD_NOTICE` (P1d "Not approvable").
- **Field view** = the request's summary and each leaf of its plan inputs, each passed SEPARATELY through `runmap.redact_value` / `redact_text` (the P1d choke point, default withhold mode) with a fresh run map: a field that passes is shown masked; a field that fails shows `WITHHELD_NOTICE` in its place.
- **Operator command** = a subcommand of the existing `hadavin-sdk` command line (`src/hadavin_sdk/cli.py`, R: subcommands `gate`, `limits`, `tick`, `migrate`, `audit`, ...).

## Options (cost and risk in plain words; no default is applied until the lead chooses, rule 16 / options-first)
| | what the operator gets | new surface | risk | cost (estimate) |
|---|---|---|---|---|
| **A. No content view** | the log line (id, reason, counts) only; the request runs out through the existing step timeouts | none; one runbook paragraph and a pin test that a withheld request expires and is never approvable | a false withhold stays unexplained; approvers are asked again at each step escalation (each card withheld); the operator may go to the database by hand (raw secret, no log) | under 1 agent-hour |
| **B. Field view by operator command** | `hadavin-sdk approvals show <id>`: the request's fields, each masked through the P1d choke point; the failing field(s) show only the notice, plus the field path and P1d's reason | one read-only subcommand, no endpoint, no schema change | the operator sees every field that passed P1d (the same text an approver would see on a normal card); a field that fails is still hidden, so a false withhold inside one long field stays unexplained | 3-4 agent-hours plus review |
| **C. Raw view, break-glass** | the raw stored text | a subcommand plus approval by two different people, an audit row, a time limit | a person sees the real secret; needs the owner's yes (secrets rule) | 8-12 agent-hours plus uncapped review |
**Counter-arguments the lead should weigh:** B shows nothing new for a one-field request (a summary only), which is the common shape if plans are short (UNVERIFIED: no measured plan shape); A is enough if BS-3's false-withhold rate is near 0; C contradicts "redaction before a person" (R447 guarantee) and is listed only so the choice is explicit. B and A combine: A's runbook and pin test are part of B.

## Behaviour of option B, exactly (the only option drafted to build depth)
1. `cli.py` gets `approvals show <approval_id>`; it refuses the memory store with the existing message (R, `cli.py:173`), exit 2.
2. It reads the request with the existing `store.get_approval_request` (R, `requests.py:148`) under the read role the `tick`/`audit` commands already use (BS-0 names that role and proves it has no write right, negative test).
3. It prints: approval id, status, current step, P1d reason from the stored record if P1d stores one (else "see operator log"), then one line per field: the field path and the field view. The approval id is printed only if it matches `[A-Za-z0-9_-]{1,64}` (P1d RK11 rule).
4. No call path can print a raw field: every field string goes through `redact_text` default mode; a leaf above `P1D_MAX_TEXT_CHARS` prints the notice (P1d rule, no slices).
5. It never approves, denies, re-sends or changes the request (read only). Getting a request out sooner than expiry is NOT added here (P1d's stop rule owns the one-bit `display_withheld` and an operator deny call if BS-0 needs it).
6. The command writes one audit row "operator viewed withheld request <id>" through the existing audit sink, if the read role may write audit rows; if not, a log line, and BS-0 states which (open question 2).

## RUNG TABLE (scale of 2026-11-06, R447)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| reading the request | fetch one stored request | 2: `store.get_approval_request` | R `requests.py:148` | nothing | CUT-TO-CONFIG+GLUE |
| masking fields | show only what passed redaction | 2: P1d `redact_value`/`redact_text` | P1d rev 5 caller table (UNVERIFIED until built) | nothing new: no new masker | CUT-TO-CONFIG+GLUE |
| operator route | where the operator looks | 1: a no-code admin table (n8n, a sheet) over the store; 3: a database client (psql) | R447; a no-code view reads raw rows (no redaction) unless it calls our code; psql shows raw text | the guarantee that the text passed the choke point first | KEEP-CODE, about 40 lines (estimate), a thin subcommand |
| break-glass (C) | raw view with control | 2: none in core | R (no two-person read path found by grep of `approvals/`) | approval by two different people, audit | only if chosen |
80 percent rule: rungs 1-3 show raw text, which fails the one need that matters (no raw secret before a person); so the subcommand stays as glue over rung 2.

## Template fields
- **Package id:** P1d-c, "operator view of a withheld request". **Path class:** redaction and security; extended review, no round cap: yes.
- **Depends on:** P1d merged (notice, per-leaf `redact_value`, stored reason if any). Blocks client data until the lead decides (ledger 010, ORDER 168 item 2); it does NOT set a marker of its own unless the lead says so (open question 3).
- **Source of the code:** our own; nothing copied.
- **Target:** `src/hadavin_sdk/cli.py` (option B); docs `docs/` operator runbook paragraph (BS-0 names the file; A and B).
- **Interface (B):** `hadavin-sdk [--config DIR] approvals show APPROVAL_ID`; exit 0 shown, 2 config or memory store, 3 not found (BS-0 checks 3 is free), 4 store unreachable (existing).
- **Neutral default / alternative:** no vendor; the store kind is already pluggable.
- **Files (B):** change `cli.py`; create `tests/test_p1d_c.py`; change `CHANGELOG.md`, the runbook file. (A): the runbook file and `tests/test_p1d_c.py` (pin test only).
- **Existing core code reused (checked):** `cli.py` store refusal (R), `get_approval_request` (R), `requests.sweep` (R), P1d `redact_value`, `is_withheld`. Checked, not reused: `approvals/receiver.py` (it serves approver clicks, not operators; no new endpoint, ORDER 166 item 3).
- **Security and least privilege:** read-only role; no secret printed (test greps stdout and the log for the key built from parts); the role cannot write the request (negative test); no new identity.
- **Tests (B):** a withheld request with three fields, one holding `AKIA**` + `IOSFODNN7EXAMPLE` + `**` -> that field prints the notice, the other two print masked text, the key appears nowhere in stdout or logs (fb: the command does not exist on the base); a normal request prints its masked fields; an unknown id exits 3; the memory store exits 2; a field above the cap prints the notice; an approval id with a newline is printed as `?`; the command makes no store write (a store fake that fails on any write). (A): `test_withheld_request_expires_and_is_never_approvable`.
- **Mutation plan (B):** MC1 print the raw field when the masked one equals the notice (killed by the key grep); MC2 skip the per-field split and mask the whole request at once (killed by "other two fields printed"); MC3 drop the id check (newline row); MC4 call a write method (write-fails fake).
- **Evidence commands:** `uv run --all-extras --group test pytest tests/test_p1d_c.py -q > handover/evidence/P1d-c/rows.txt 2>&1; echo rc=$?`; fail-before on a worktree of the base; one full suite on the final head through the heavy slot; ruff check, ruff format --check, bandit -ll.
- **Reviewers:** `egm-design` + `egm-implementation-readiness` (plan); `egm-codebase-details` + `egm-design` (result); fresh, given the diff, this ticket and the evidence only.
- **Done =** the lead's choice recorded in this ticket; a fresh round finds no blocker or major; gates green; row 010 FIXED-VERIFIED (B), or re-classified by the lead (A: OWNER-ONLY/accepted by the lead in writing; C: needs the owner).
- **Rollback:** tag `pre-P1d-c`; no migration; the subcommand can be removed.
- **Real clock (estimate):** B builds in 3-4 agent-hours after P1d merges; plan review can run now in parallel with P1d's build.

## Open questions for the lead
1. **Choose A, B or C** (C also needs the owner's yes). Nothing is built before the answer.
2. **Audit row for a view (B):** an audit row needs the audit writer identity in the CLI process; a log line does not. Which?
3. **Marker:** should the client profile also require a `P1DC_APPLIED` marker (like P1d-b), or does the lead's decision alone close row 010?
4. **Brief vs ticket:** your brief listed S16 under P1d-c; ledger 009 and P1d.md put it in P1d-b, and P1d-b rev 1 carries it. Confirm.

## UNVERIFIED
All P1d behaviour cited; whether P1d stores the withhold reason with the request; the read role the CLI uses; exit code 3 being free; the runbook file; typical plan shape (number and size of fields); whether escalation re-sends a withheld card to new approvers (R: `sweep` clears `sent_at`, so it likely does).

## Rules cited
R447, R448, R449; preamble rules 5, 6, 11, 13, 14, 16, 20; ORDER 166 item 3, ORDER 168 item 2.

## Revision log
Rev 1 (2026-11-09): first draft (egm:egm-draft, headless), from ledger row 010, P1d rev 5 (operator route, stop rule, BN-P1d-9), round5-resolve D2, ORDERS 165-168.
