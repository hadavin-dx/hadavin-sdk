# REVIEW of core-hardening (branch cloud/core-hardening, folder handover/core-hardening), ORDER 005

Reviewer: system-map cloud session, independent (I did not write the target). Static review of code snapshot b4cce5b (the commit the target audited). No product program was run, no network, made-up data only. Detail files are in `work/`.

## VERDICT: RELIABLE WITH CORRECTIONS
Scale (PLAN.md, step 7): RELIABLE = no Blocker WRONG and at most 10 percent of checked Majors WRONG; RELIABLE WITH CORRECTIONS = no Blocker WRONG, and any Blocker rated too high; NOT RELIABLE = a Blocker WRONG, or more than 25 percent of Majors WRONG.
Numbers behind it (from `work/verify-V1..V4.md`, `work/verify-V6.md`, my own reading in `work/lead-notes.md`):
- Checked: all 5 Blockers and all 80 Majors (85 of 85), not only the half the order asks. Nits (65) were not checked.
- WRONG as a whole finding: 0 of 85. CONFIRMED: 85 of 85 (X-15 only in part: three of its example files are not in the snapshot; parts of B-01, B-10, B-22 need a running system).
- Severity too high: 3 of 5 Blockers (A-02, D2-01, B-01) and 24 of 80 Majors (30 percent). Severity too low: none.
- Wrong line numbers: 15 cites point past the end of their file (limits.py x9, factory.py:109, prompt.py:400/408, test_k5_round6_contracts.py:45) and a few more are off by 1 to 3 lines. The facts behind them still hold.
So the target's facts are sound; its severities are inflated, it counts some issues twice, and its two proposed patches are incomplete.

## What failed or was not checked (first)
1. Not checked: the 65 Nits; the 473-row MASTER-MAP table row by row (183 rows have no `path:line`); anything needing n8n, a database, a scheduler or a deployment outside this repo.
2. The citation checker covered only 36 cites (it needs a quote beside each cite); `work/evidence-ch-1.md` numbers for lane B ("no path:line") are a counting artefact of that lane's bullet format, not a defect of the target. My loose check (`work/loose_cite_check.py`, `work/evidence-ch-2-loose-cites.txt`): 760 `path:line` cites, 681 resolve and are in range, 15 past end of file, 6 cut-off file names, 58 ambiguous file names (not judged).
3. The 22 files in `src/` that differ between b4cce5b and today's head: 18 are cited by the target (list in `work/evidence-ch-1.md` (d)); a claim about them may be stale. The other 4 (stages.py, store/migration_numbers.py, testing/__init__.py, testing/mutation.py) are not cited.
4. Verifier agents are unverified until sampled: I re-read all 5 Blockers myself and V6 re-read them independently (agree on facts). I did not re-read a sample of the 80 Major lines; verifiers quoted file:line for each and gave no WRONG, so this is a gap: nothing contradicts them, but I did not test them against a deliberately wrong line.
5. Round 2 of the result review is described at the end (FINAL in REPORT.md).

## Blockers, one by one
| id | claim (short) | verdict | severity | note |
|---|---|---|---|---|
| A-01 | audit events parked in the outbox or memory are never written back; no tick step; no log | CONFIRMED (me, V1, V6) | AGREES | `audit.reconcile()` has no caller in src (only tests/test_cuj.py:202 and tests/warden_port/test_audit_chain.py:514). A tick step drains only the shared table or folder; events parked in memory of another process stay lost. Extra caller (missed by the target): `Limits.stop` (limits.py:43-46) uses `write_outcome`, so a failed emergency-stop audit write parks and is never drained. The test pinning the tick step list (tests/test_p7_tick.py:79-92) must change with the fix. No patch is offered for A-01. |
| A-02 | the outbound "G5" leak check is promised and not built | CONFIRMED (me, V1, V6) | TOO HIGH: Major | Only comments (redact.py:15-17; gate.py:42-44, :63) promise it; gate.py:5-7 says "Not ported"; README.md:31 states the limit. A false comment, not a code regression. The target's patch fixes only the redact.py comment (see CORRECTIONS). |
| B-01 | a failed re-probe disables a source only inside the tick process | CONFIRMED as code fact (me, V2, V6) | TOO HIGH: Major (me, V6); V2 said AGREES | Set is process-local (app.py:58, tick.py:235). Target's own text says it is a Blocker only if tick runs separately, "UNVERIFIED". The "exit code 1" statement is wrong in the likely case (build probes scope and exits 2 at start, app.py:125-128). Tools keep their own READ_OPERATIONS, so it is defence in depth. |
| C-01 | zero, negative or NaN model price switches off every spend limit | CONFIRMED (me, V3, V6) | AGREES | config.py:47, 57-59 have no price floor; only k1b/replay.py:85-90 refuses zero. Its limits.py cites are wrong (real lines limits.py:20-30). The target's patch fits but is not enough (see CORRECTIONS). |
| D2-01 | demo `ask` skips kill switch, meter, audit and ledger | CONFIRMED for code (me, V4, V6) | TOO HIGH: Major at most | cli.py:99 calls `source.run` directly; the README labels `ask` a spike with a scripted model and does not say it uses the controls (V4, V6). Read-only login, no paid call. |

## Severity corrections for Majors (24 of 80 rated too high)
V1: A-10 (Nit: dead helper code), X-05 (duplicate of A-02, count once), X-06 (roll-up of B-22, A-05, C-19), X-09 (Nit: three strings repeated), X-10 (in part), X-11 (Nit: provenance note), X-13 (Nit: wrong line numbers, already in target 9a). V2: B-03, B-07, B-08, B-09 (dead code, target's own verdict NOT-NEEDED), D1-03 (target's own 9d narrows it). V3: C-10, C-11, C-17, C-19, D3-06, D3-09, D3-10, D3-20. V4: D2-06, D2-07, D2-08, D2-18.
Double counting: X-05 = A-02; D3-08 = C-09; D3-09 = C-10; B-11 and D1-01 are one item. Corrected tally if all proposals are accepted: 2 Blockers (A-01, C-01) and 54 Majors (80 minus 24 lowered, minus the two duplicates not already among the 24: D3-08 and one of B-11/D1-01).

## What the target MISSED (found independently by H1, H2, V1, V2, V4, V5; I checked the ones marked "me")
- Limits.stop parked in the outbox (extends A-01) (me, limits.py:43-46).
- `on_decided` (agent_loop.py:753) calls execute without a state check for any caller (V2; the map mentions on_decided, the findings do not).
- One secrets provider object is passed to executor, model key, signer, anchor, store, approvals channel and HMAC key (app.py:82-173) (H1-10, Major as a design point; tools do keep their own secret names, app.py:254-261). No IAM or role policy text, per-action reasons or negative tests are shipped for the cloud kinds (H1-11; the map has 6 hits for IAM, no finding).
- The `audit` kind exception names its trigger as "none" (H1-17).
- The demo import guard (tests/demo_askdata/test_imports.py:9) names only psycopg and sqlglot; a new boto3 or anthropic import in demos/ passes both guards (H1-01).
- `exec(compile(...))` of pinned bytes at tools.py:389 (Nit; guarded by a pin) (H1-16).
- Demo-local generic code with no promotion entry: safe_text.py (its ANSI pattern is weaker than core guard/redact.py:820), meter.py, a torn-tail append in the ledger (H2). Demo lacks a `demo_only/` folder (target D2-12 covers).
- The target's own patch text for A-02 cites "gate.py says so" while gate.py:42, 63 say G5 is built (V3, V5a, V6).
Not misses (the target has them): stage name "dev" accepted and "demo" refused (X-01, B-11, A-19, question 8; H1 called it Blocker, I keep it as the target's Major with an owner decision pending because renaming breaks existing config files); money as Decimal not integers (target 9 section, D2-19); banned vendor strings under handover/ (D3-01, X-15; I confirmed "Port.io" at handover/BRIEF-PREAMBLE-studio-2026-11-06.md:17 and that tests/test_no_reference_material.py scans it, so that test fails by static reading; not run).

## One-place verdicts and cut list (V5a, V5b, H2)
- V5b classified 91 module files blind: 88 NEEDED, 3 idle (approvals/receiver.py, extract.py, guard/producers.py), 0 DUPLICATE. Target MASTER-MAP: producers.py "NEEDED", receiver.py "UNVERIFIED"; extract.py is on the cut list as NOT-NEEDED. I compared only these items, not all 113 rows.
- H2: no dead module (nine kind modules load by name through backends/table.py strings); idle: extract.py (only tests call it, can make 2 model calls with no budget check), save_approval_decision (second, non-atomic path), dead-letter store methods (only reachable from extract.py), guard/producers.py, receiver `serve`.
- Cut list: "never delete" is respected (target: "Nothing was cut"). Wrong calls: archiving breaks something for CLOUD-RESUME-2026-11-07 (4 lines name it), CLOUD-RESUME-2026-11-09 (10 lines; PARALLEL-PLAN-2026-11-10.md:30 needs it), CLOUD-PROMPT.md (8 references), and the two bible-extract files (byte-identical, 10 and 11 references: keep one name and a redirect). Safe to archive: BRIEF-PREAMBLE-studio-2026-11-06.md (one history line; also the banned string), CLOUD-RESUME-2026-11-06.md, CLOUD-RESUME.md after one edit at questions-for-lead.md:1127. Code items are not archive items: replay_records is a live gate read at deferred.py:95 on every registry load (archiving gives an ImportError and breaks 3 test files); trigger_ref is a NOT NULL column used by 12 tests; dead_letters is an applied migration with no reader or writer; the `live` marker is used by ci.yml:88; only `min_redaction_window` is truly unread in src (3 test uses). An archive folder inside the repo is still scanned by the banned-string test.
- Contradiction inside the target: the cut list marks extract.py NOT-NEEDED, the fix plan keeps it inside guarded_call (X-02).

## Rung table (tool ladder; V5a, 20 rows in `work/verify-V5a.md`)
Most fixes are rung 1 (reuse) and RIGHT RUNG. Too high (cut to config plus thin glue): X-06 heartbeat ping (rung 2 or 3; tick.py:9-11 says the ping is pending), B-10 connection reconnect (use a library pool), A-05 approval receiver hosting (a webhook). The target's fix plan (section 4) has no per-component rung table, a Major under preamble rule 20.

## Claims without evidence
Statements with no `path:line` exist but their count is unreliable (see item 2 above). Cites to non-existent lines: D3-05 "70-plus PR numbers" gives about 9 in V3's grep; D3-11 row counts reproduce only for the 272 five-column rows; D1-03 says a cadence test "does not exist" but the file exists without a cadence test; B-06 waiver is README:38 not :33.

## Open for the laptop lead
Decide the three severity changes (CORRECTIONS), the stage rename (X-01), whether zero price is allowed for the fake and local-model kinds (C-01 patch), where audit reconcile runs, and the archive moves (owner yes).
