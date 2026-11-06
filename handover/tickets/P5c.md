# Package ticket P5c: the redactor kind, the masked model wrapper and safe put-back (C1a to C1d plus C1f), four pull requests (P5c-1 to P5c-4). DRAFT revision 2

**Revision 2, written 2026-11-06, started 03:06 UTC (08:36 IST; IST = UTC+5:30), by a ticket-revision author (lead order 20 item 6). It applies every decision of `handover/reviews/P5c-round1-resolve.md` (32 findings: 28 fixes, 11 of them by cutting surface, and 4 contests).** Revision 1 was written 2026-11-06 02:42 UTC (08:12 IST). Text only: no code, no pull request, no test run, no sub-agent. **Path class: redaction, money-adjacent.** It decides which parts of an invoice reach a model (bank account numbers included) and which values are put back into a plan that can lead to a payment. **Extended review: yes.** This is Tier A (plan-v3 section 4 rule 3). **Review round 2 is next.** Order 20 item 6 caps ticket review at 3 rounds counting from round 1. A redaction package whose last round had no Blocker and at most 2 Majors may take one more round. Round 1 had 1 Blocker and 19 Majors, so rounds 2 and 3 are allowed, and a round 4 only if round 3 meets that bar. The result review of the built code keeps the two-clean-rounds stop rule (order 16(5)).

**What is not verified, first.**
- I ran no test and no mutant. Every new test row, every mutant and every "fails before" argument below is a hand argument until the evidence runner reports.
- I ran TWO read-only probes. Both used Python 3.13.18 (that is the exact output of `python3 --version` here), `python3 -I`, and stand-in code rather than the real class:
  - (a) A `__slots__` class whose only hook is a raising `__getstate__`: `copy.copy`, `copy.deepcopy`, pickle protocols 0-5, `__reduce__()` and `__reduce_ex__(0..5)` all raised `TypeError`.
  - (b) The new NAME letter class `[A-Z][^\W\d_]+` with an optional `-` part: it matches `Dear Jürgen <last>` and `Dear <first> <last>-<last>`; it does not match a name whose first letter is `É`. For a name written with a separate accent mark (e followed by U+0301) the match stops before the mark (`[^\W\d_]` does not match U+0301; `\w` does not match it either). By reading only, main's second pass over the NFKC view (`runmap.py:464-475` at `124258b`) composes the letter and masks the whole name; row NAME-DECOMPOSED pins this, UNVERIFIED by run.
- Every name taken from P1 (rev 16, FROZEN), P2d (rev 6, FROZEN), the look-alike design (draft 11, FROZEN), P5a, P4b1 and P4c is cited by item name and is UNVERIFIED against code, because none of that code exists yet.
- **egm-draft was NOT run for P5c**, although lead orders 6(e) and 8(3) asked for it. This author brief forbids sub-agents, and the Skill starts one. See PENDING LEAD item 2.

**Base of every file:line below (CONTESTED in round 1, kept; evidence in the resolve file, re-checked by me for this revision):**
- **Commit read:** `124258b`, read with `git show 124258b:<path>`. I re-read every code cite in this revision at that commit.
- **The `src/` tree on disk is `ce70eb5`, not `124258b`.** `git diff --stat ce70eb5 -- src` prints nothing. Use `git show 124258b:` (or the head the pull request rebases on), never the disk files. Both round-1 reviewers read the disk tree, so their `runmap.py` lines are about 47 lower than the ones here. At `124258b`:
  - `TooDeep` :98, `neutralise_untrusted` :340, `redact_untrusted` :345, `RunMap(dict)` :384;
  - `redact_text` :464, `_redact_value` :588, `restore_value` :607.
- **`origin/main` is now `397ec97`** (#59, "Hygiene: neutral provenance and test names, drop a dead skip"). `124258b` is its ancestor (`git merge-base --is-ancestor`). `git diff --stat 124258b origin/main -- src` = `approvals/gate.py` and `guard/redact.py`, one line replaced in each, so no line number below moves. The sha256 of `redact.py` does change (see the CHANGELOG, cut 5).
- PR #50's local head `748849c` (branch `origin/handover-src/pr50-local-748849c`) is cited only for P2d's form of `guard/redact.py`. The PHONE lines `:479-484` are `748849c` lines, as before.
- The C1a branch is `origin/handover-src/c1a-8460813` (head `8460813`). Its line numbers come from revision 1 and were not re-read for this revision.

## CHANGELOG of this ticket (revision 1 -> revision 2)

**Cut (surface removed; each closes a round-1 finding by deleting, order 8(1)):**
1. **The `MaskedLLM.premasked` wrapper and the downgrade of its refusal to a warning** (operator flag `--i-know-data-is-already-masked`, `cli.py:120`; rule-id suffix `;premasked[;unverified]`). Also cut: T2-12, the premasked part of T3-07(d), M27. *Reason:* a flag that turns a masking refusal into a warning is a way around the mandatory wrapper (R1-ADV-17a). Placeholders pass the trusted re-mask unchanged, so masking k1b's bundles a second time changes nothing (`judge.py:68-69` comment). `k1b/loop.py` now uses `MaskedLLM.of` like every other caller. The flag keeps its one existing meaning: skip k1b's own bundle masking. The wrapper still masks. (PENDING LEAD 18.)
2. **`RegexRedactorSettings`.** *Reason:* it has no fields in v1. `backends/table.py:388` already wires a kind that has no settings with the base `KindSettings` (`"fake": Entry(KindSettings, ...)`). A new name would also sit next to the existing `RegexSettings` (:92) and could be mistaken for it (R1-ADV-17d).
3. **The shared contract suite `tests/contracts/kinds/redactor.py`.** *Reason:* there is one backend. V3 writes the suite when the second backend is built (R1-ADV-17d).
4. **The "mask messages and documents as ONE joined text, split back after" step and its separator.** *Reason:* a split that does not line up had no defined behaviour. Views and NUL cleaning can change the separator. The cap and the time budget grew with the length of the conversation (R1-ADV-2). It is replaced by two passes over the leaves (item 7).
5. **The hand-pinned `REDACT_SOURCE_SHA256`, its start-up `ConfigError`, T1-03, M1, and the "revert P2d and P5c-1 together" lock in Rollback.** *Reason:* the pin covered only `redact.py`, while masking also depends on `runmap.py`, P1's fold and P2d's check (R1-ADV-7). #59 has already changed `redact.py`'s hash once, which shows how easily a hand pin breaks. It is replaced by a fingerprint computed at import over every masking source file (item 4). (PENDING LEAD 16.)
6. **`__copy__` and `__deepcopy__` on `MaskSession`, and mutants M4, M5 and M40.** *Reason:* probe (a) shows that a raising `__getstate__` alone makes F10's whole list raise, so M4 and M5 could never be killed (R1-ADV-9). M40 mutated a card-restore call that does not exist (no card code calls restore; V1 is cut).
7. **T4-06 (restore after close raises `session_closed`).** *Reason:* it contradicted the execute-time seam, which runs after the run's session has closed and reads the stored map (R1-ADV-4). `restore` now takes a plain map (item 8).
8. **T3-08 and the second module list of T3-07.** *Reason:* `guard/producers.py:55-60` `MODEL_CALLERS` already lists the modules that call a model, so a second list would be a second registry of one fact (R1-ADV-5).
9. **The `adhoc:<uuid4>` context for a model call made outside `run(...)`.** *Reason:* such a call silently lost its put-back and its audit link (R1-ADV-17e). A call outside `run(...)` now raises `SessionClosed` (code `session_closed`, no new code). `gate` and `extract` open their own `run(...)`. (PENDING LEAD 22.)
10. **The `str.isupper()` check after a NAME match.** *Reason:* it needed a callback that the plain (kind, regex) table, the fold scan and `redact_many` do not have (R1-COR-7). The cost is that names whose FIRST letter is a non-ASCII capital (for example a name starting with `Ø`, `É` or `Ł`) are not masked; they go on the README "not masked" list and get row NAME-NONASCII-INITIAL (strict xfail). (PENDING LEAD 21.)
11. **The raw-document hash in the `received` audit event, with no reordering.** *Reason:* revision 1 said "hash the masked body" but `received` is written before masking (`agent_loop.py:349` vs `:367`). Moving the masking earlier would change audit order and the too-large path (R1-ADV-11, R1-COR-5). `received` stays the first event (pinned by `tests/test_s5_runtime.py:137`) and simply carries no `inputs_hash`. No `src/` code reads `received.inputs_hash` (resolve, by grep; not re-run by me). The wrapper's per-call `outbound` event records the hash of what was sent. (PENDING LEAD 19.)
12. **PHONE storage (if PENDING LEAD 17 is accepted).** *Reason:* a bare 16-digit card number, or a bank number of 10-11 or 13-16 digits with no bank word, is masked as PHONE. PHONE is a stored kind (`defaults.py:120`), and its grammar `[0-9 ()+.\-]{5,32}` (`runmap.py:228`) accepts plain digits, so these numbers could be put back into a plan (R1-COR-2). The fix removes one line from the default `STORED_KINDS`. *Rejected alternative:* a Luhn rule or a phone-shape grammar in `runmap.storable_original`, which is more design and sits in P2d's file.

**Changed (no surface cut):**
- One masking mode per input class, in item 7 (R1-COR-1, the Blocker; R1-ADV-1; PENDING LEAD 15).
- `check` runs on the whole masked body (R1-ADV-8).
- Three restore seams, not two; `tools.py` joins P5c-4 (R1-ADV-3).
- `restore` takes a plain map (R1-ADV-4).
- `guard/producers.py` and `tests/test_k5_producers.py` join P5c-3 (R1-ADV-5).
- Both directions of the 12-digit account number are named (R1-ADV-6).
- `extract` gives no put-back in v1, row V9 (R1-ADV-12; PENDING LEAD 20).
- An exact table of strong account keywords (R1-ADV-16, R1-COR-6).
- Rows are relabelled as fail-before or regression pin, with T3-15g and a rewritten T3-09 (R1-ADV-10, R1-COR-3).
- M31 and M36 are retargeted (R1-COR-4).
- Existing tests changed by P5c-1 are listed (R1-COR-8).
- `write_intent` is confirmed (R1-COR-10).
- P5b3 is added to Depends-on (R1-COR-11).
- Golden UTF-8 row T3-16 (R1-COR-12).
- The raw-model grep is quoted and called a floor (R1-ADV-14, R1-COR-14).
- T3-02's cross-reference is fixed and T2-10 gets a barrier (R1-ADV-15).
- `of()` and `Runtime` refuse a mismatched wrapper (R1-ADV-17b, c).

**Contested (revision-1 text kept, with evidence):**
- R1-ADV-13 and R1-COR-13 (cites): the `124258b` cites are right; see "Base" above.
- R1-COR-9 (P4b1 has no wrapper): `tickets/P4b1.md:219` reads "P4b1-b: the wrapper around model calls (`MeteredLLM`)", and `:228` gives `MeteredLLM(inner: LLM, limits: Limits, routes: dict[str, Route])`. The dependency stays, and the wrapper is now named.
- R1-COR-15 (Python version): `python3 --version` prints `Python 3.13.18`.

## Words used in this ticket (defined once)
- **mask**: replace a protected value (an e-mail address, an account number, a key...) with a **placeholder** such as `<EMAIL_1>` before text goes to a model. **put back** (restore): replace a placeholder with its original value again, in code, after the model has answered.
- **escape**: turn placeholder-shaped text that came from OUTSIDE (for example a `<EMAIL_9>` typed into a document) into a harmless look-alike (`‹EMAIL_9›`), so nobody mistakes it for a real placeholder. `runmap.redact_untrusted` escapes and masks; `runmap.redact_text` only masks (issued placeholders and `<<TOOL RESULT` markers pass unchanged).
- **run map**: on main, the one placeholder-to-value dictionary of a run (`guard/runmap.py:384` `RunMap`, a `dict` subclass). **mask session** (`MaskSession`, new): the object this package puts around the run map. It holds the map privately, cannot be copied, and can be closed.
- **redactor kind**: the replaceable part, chosen by configuration, that masks text (plan-v3 section 5, row "redactor"). Its default is `regex` (the patterns of `guard/redact.py`).
- **masked model wrapper** (`MaskedLLM`, new): the only object through which core code may call a model. It re-masks every message and document of a call with the run's session and checks the result before the inner model sees it.
- **stored kinds**: the kinds of identifier whose originals may be saved and put back. Today (`defaults.py:108-122` `STORED_KINDS`) they are ACCOUNTID, ADDRESS, ARN, AZURERESOURCE, EMAIL, GCPRESOURCE, HOSTNAME, IPV4, IPV6, MAC, NAME, PHONE and TENANT. P5c-4 removes PHONE (PENDING LEAD 17). Every secret kind, and the regulated kinds IBAN, CREDITCARD, BANKACCT, BANKCODE, SSN, AADHAAR and PAN, is masked but never stored and never put back. A regulated number that is MASKED AS a stored kind is stored. Two cases: a bare 12-digit number is ACCOUNTID (PENDING LEAD 8), and today a bare 10-11 or 13-16 digit number is PHONE (PENDING LEAD 17).
- **fingerprint**: one string that names the masking code exactly (item 4); it is part of an agent's config hash.
- **a person looks**: the run stops in state NEEDS_PERSON with a reason code, and nothing more is sent to the model.
- **fail before (FB)**: a test that fails on the code before this package and passes after it. **regression pin**: a test that already passes before; it guards the behaviour from now on and is NOT counted as fail-before.

## The finding that shapes this ticket (read this before the fields)
The frozen C1 ticket (`studio-notes/C1-ticket-v3.md` plus `C1-ticket-v3-FROZEN-amendments.md`, called "C1" and "F1..F14" below) and the C1a branch were written on `6608146`. Main has since gained the K5 work, which already does a large part of C1c (all lines at `124258b`):
- **The run loop masks the document before any check or model call.** It uses the run map before the injection check and before the model (`runtime/agent_loop.py:361-377`, `runmap.redact_untrusted` at `:367`). Any redactor failure sends the run to a person with reason `redaction_error` and no model call (`:376-377`, `_redaction_failed` at `:547`).
- **Tool results are masked with the same map.** `_run_tool` (`:286`) calls `prepare_output`, and a redaction failure there also stops the run.
- **Placeholder-shaped text in untrusted input is escaped, not trusted** (`guard/runmap.py:340` `neutralise_untrusted`, `:345` `redact_untrusted`).
- **Put-back exists at THREE seams:**
  - `inputs_view` restores only stored kinds from the saved map (`agent_loop.py:269-284`, restore at `:284`), and a placeholder left over makes the gate deny `input.unresolved` (`agent_loop.py:794-797`);
  - read tools get their arguments restored in `_run_tool` (`:295`);
  - `ToolBox.invoke` restores again (`tools.py:1162`, `runmap.restore_value` at `:1178`).
- **The qualification gate and the judge mask too.** The gate masks each golden document with a fresh map (`evals.py:60-63`). The judge masks its input again with a fresh map (`guard/judge.py:71`; its comment at `:68-69` says placeholders pass unchanged).

What main does NOT have (each is a gap this package closes):
- **(G1) No `redactor` kind.**
- **(G2) No single door for model calls.** Five modules call `.chat(` directly (`agent_loop.py:425`, `evals.py:73`, `extract.py:47`, `guard/judge.py:72`, `k1b/loop.py:94`), plus `demos/ask-your-data/askdata/pipeline.py:155`. **`extract.extract` sends the RAW document to the model**: `extract.py:46-52` passes `documents=[document]`, and the file masks nothing (it imports only `safe_head`, `:11`).
- **(G3) The `received` audit event hashes the RAW document** (`agent_loop.py:349`).
- **(G4) A document that is not UTF-8 is decoded with `replace`** (`agent_loop.py:367`, `evals.py:63`).
- **(G5) The masking rules are not part of what an agent is qualified on** (`registry.config_hash`, `registry.py:105`).
- **(G6) The run map has no end of life:** it is a plain `dict` subclass.
- **(G7) There is no record per model call of what was sent** (C1 D8).
- **(G8) The account-number and name pattern gaps** of order 11(5) and design sections 9 and 9b.
- **(G9) Put-back can return a placeholder made from a FOLDED spelling** (P2d L5, row RESTORE-1).
- **(G10, new in revision 2) A regulated number masked as PHONE is stored and can be put back.**

**Consequence, and my recommendation (PENDING LEAD item 1):** build P5c ON main's run map, and do NOT port the C1a branch's own masking engine (774 lines, 44 ledger rows `BL-core-c1a-*`, 28 of them MAJOR). Take from C1a only what main lacks: the kind wiring, the session's copy refusal and its tests (rewritten against the new class), and the code-only error. The version pin is no longer taken: it is replaced by the computed fingerprint. Every `BL-core-c1a-*` row gets a disposition in the P5c-1 evidence file, either "superseded: engine not ported" or "carried: <test id>" (row 044, the version bump and the sixth code, is carried by T1-02 and T1-06).

## Template fields in the template's order

- **Package id and name:** P5c, "Redactor kind and masked model wrapper (C1a-C1d) plus put-back (C1f)". Four pull requests, each titled with its id:
  - **P5c-1 (C1a): the redactor kind.** Contents: `MaskSession`, the six-code refusal class, the `Redactor` protocol, the `regex` kind over the run map, `REGEX_VERSION = "4"`, the computed fingerprint, the config-hash entry, the kind wiring, and the pattern rows of order 11(5) and design 9b. No change at any place that calls a model. (Existing tests DO change; see Files.)
  - **P5c-2 (C1b): the masked model wrapper.** `llm/masked.py` and its tests only. Nothing calls it yet, so the tree stays green.
  - **P5c-3 (C1c and C1d in ONE pull request): wiring.** The run loop, `app.py`, `cli.py`, `extract.py`, `evals.py`, `guard/judge.py`, `guard/producers.py` and `k1b/loop.py` use the wrapper, and the wrapper becomes mandatory (`isinstance`). It is one pull request because a mandatory wrapper turns every intermediate state red (C1 F12).
  - **P5c-4 (C1f, cut to its safety core): put-back.** Restore happens only through `redactor.restore`, only for stored kinds, never for a folded spelling, and at exactly three seams. PHONE leaves the default stored kinds. This pull request also adds the acceptance file's third row.
- **Path class:** redaction (personal data before the model) and money-adjacent (bank numbers on invoices; values put back into plans an executor may act on). **Extended review (no round cap): yes**, within order 20 item 6 as stated in the header. The lead verifies at most one redaction pull request at a time (plan-v3 section 3).
- **Depends on (merged first):**
  - **P2d-2** (rev 6, FROZEN): `LookalikeCopy` (a `RedactionError`) must exist for T2-14 and T3-15. P2d's module joins `MASKING_SOURCES` (item 4). P2d rev 6's section "How P5c rebases on this" (`tickets/P2d.md:344`, "P5c pins the `redact.py` hash after P2d-2") and its Rollback lock fall away if PENDING LEAD 16 is accepted. The lead notes this in P2d's build notes.
  - **P2d-2b** before P5c-3. Both edit `runtime/agent_loop.py` (P2d-2b at the `error_reason` call, design section 8).
  - **P1a and P1b**: P1's fold modules (`guard/textnorm.py`, `guard/_confusables.py`) and `FOLD_VERSION` enter `MASKING_SOURCES` and the fingerprint (item 4).
  - **P5a** before P5c-1. P5a's discovery test fails any pull request that adds its own exception class without an `OWN_CODES` row, and P5a reserves `session_closed` for P5c (`tickets/P5a.md`, item "The sixth code `session_closed`").
  - **P5b3** before P5c-3. It rewrites `extract.py:58`, a line P5c-3 also touches (R1-COR-11).
  - **P5b5** (plan-v3 row P5c, "P2d, P5b5"): kept until the lead answers PENDING LEAD 12. Honest reason: P5c needs only P5a and P5b3, and I found no file that P5b4 or P5b5 shares with P5c.
  - **P4c-2** before P5c-3, on `runtime/agent_loop.py` and `registry.py` (`tickets/P4c.md` lines 15-16). P4c's T8 table of model-calling modules reads `producers.MODEL_CALLERS` (T3-08 is cut), and P5c-3 marks those rows "through `MaskedLLM`".
  - **P4b1-b** (`MeteredLLM`, `tickets/P4b1.md:219`, `:228`) before P5c-3, if it holds. The masked wrapper sits OUTSIDE the metered one, `MaskedLLM(MeteredLLM(raw))`, so the meter counts the masked body (PENDING LEAD 9). Coupling: `tickets/P4c.md:266` (item 15) says run-path metering is `Limits.hold` and "Not a wrapper on `deps.llm`". The P4c round-2 resolve and the P4b1 round-2 resolve (questions-for-lead INFORM 22 and 23) both recommend ONE `MeteredLLM` wrapper. The lead confirms before P5c-3 (PENDING LEAD 23).
  - **Merge order (order 20 item 4):** P5c comes after the lead's chain (P1m, P1a, P1b, P3a and P4d, P2a-1, P2d-1, P2d-2, P4a). Order 20 item 2 is the standing S0 EXIT for "P5c later", effective once P5c's freeze and its build-start review are done. Inside P5c the order is P5c-1, P5c-2, P5c-3, P5c-4.
  - **Hot files (plan rule 10, A4, A9 F6, order 17):**
    - `config.py`: P4b1, P5b3, P5c, P6a;
    - `registry.py`: P4c, P5b3, P5c;
    - `cli.py` and `backends/table.py`: P5b3, P5b4, P5c, P6b2, P6a;
    - `tests/test_lockin_guard.py`: P4d, P5c, P6b2, P6a;
    - `runtime/agent_loop.py`: P4c, P2d-2b, P5c;
    - `app.py`: A9 F6 lists P6a and P6b2; **P5c-3 also edits it** (PENDING LEAD 14);
    - `extract.py`: P5b3, P5c;
    - **`tools.py`: P2a, P2d, the look-alike design, then P5c-4** (order 17; P5c-4 rebases after them);
    - **`guard/producers.py` and `tests/test_k5_producers.py`: P5c-3**;
    - `defaults.py` (order 20 item 5): no fixed order; each P5c pull request rebases on current main and puts its change in its own block headed `# --- redactor kind (P5c-n) ---`. P5c-4's PHONE line is a removal from the `STORED_KINDS` tuple, with a comment line in that block;
    - `CHANGELOG.md`: append-only, one entry per pull request.
- **Problem in plain words:** Before a model reads a document, the core must replace every personal or secret value with a placeholder, and the person who runs the system must be able to trust that no code path skips this. On main the run loop already does it, but several things are missing:
  1. **There is no single door.** Five modules call the model directly, and one of them, `extract`, sends the raw document unmasked.
  2. **Nothing ties an agent's approval to the masking rules.** Change a pattern and the agent keeps running on its old approval.
  3. **The masking state of a run can be copied and used after the run.**
  4. **Some numbers can be put back as the wrong kind of value.** A put-back value can be a "cleaned-up" spelling rather than what the document said, and a card or bank number labelled as a phone number can be put back into a plan.

  P5c adds:
  - the redactor as a kind, so a second masking method can be plugged in;
  - one wrapper that every model call must go through;
  - a fingerprint of the masking code that forces a new qualification run when the masking changes;
  - a session that cannot leak;
  - narrow rules for putting values back.

  It also closes two account-number gaps that Intake found, and says plainly which ones stay open.
- **Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:**
  - **Taken from main `124258b`, reused and not rewritten:**
    - from `guard/runmap.py`: `RunMap`, `redact_untrusted`, `redact_text`, `redact_value`, `restore_value`, `storable`;
    - the run loop's masking order;
    - `defaults.STORED_KINDS`;
    - the `producers.py` registry.
  - **Taken from `8460813` (C1a branch) as a pattern only, and rewritten:**
    - the copy and pickle refusal (`:278-285`), now with `__getstate__` only;
    - the code-only error (`:117-129`);
    - the kind wiring rows (diff of `backends/table.py`, `backends/builtin.py`, `config.py`, `deferred.py`, `guard/__init__.py`, `tests/test_lockin_guard.py`).
  - **NOT taken from C1a:**
    - its engine (`MaskSession.issue/absorb/snapshot`, `_engine`, `_check` second engine, `_strip`, its size caps, the registry-load prompt lint, `tests/test_c1a_redactor.py`);
    - **its version and source-hash pin (`REDACT_SOURCE_SHA256`, start-up refusal `:435-439`): replaced by the computed fingerprint** (CHANGELOG cut 5).
  - **NOT taken from C1:**
    - the `forged_mark` refusal of documents (main escapes instead; V6), although `forged_mark` remains the code of the body check (item 7);
    - F9's `evals._restore_all` (V7);
    - D7's approval-card display and per-field `restorable` paths (V1, V2);
    - F6's operator downgrade (CHANGELOG cut 1).
  - MANIFEST rows: none hold C1 (UNVERIFIED: I did not search MANIFEST.csv for `guard/redactor.py`).
- **Target module and path in `src/hadavin_sdk/`:** `guard/redactor.py` (new: the protocol, the session, the refusal class, the `regex` kind, `restore`) and `llm/masked.py` (new: the wrapper). Edits are listed under Files.
- **Interface (names, argument and return types, errors):**
  1. **Refusal class and codes (P5c-1). UNCHANGED from revision 1.**
     - **One base class.** Main's `guard/runmap.py:38` `RedactionError(RuntimeError)` stays the base. `InputTooLarge` (:42), `TooDeep` (:98) and P2d's `LookalikeCopy` derive from it.
     - **The coded refusal.** New: `class RedactorRefusal(RedactionError)` with `.code: str`. `__str__` returns the code only; it is raised `from None`, with no message, no value and no cause.
     - **The six codes:** `CODES: Final = ("unsupported_input", "too_large", "forged_mark", "self_check_failed", "internal", "session_closed")`. A code outside `CODES` becomes `internal`.
     - `class SessionClosed(RedactorRefusal)` with code `session_closed`.
     - **The one mapping** `code_of(exc) -> str`: `RedactorRefusal` gives its own code; `InputTooLarge` gives `too_large`; `TooDeep` gives `unsupported_input`; `LookalikeCopy` gives `self_check_failed`; anything else gives `internal`.
     - **Operator page line:** "session_closed: the program used a finished run's masking session, or called a model outside a run; nothing was sent; report it as a bug".
     - **P5a mapping:** two `OWN_CODES` rows, `hadavin_sdk.guard.redactor:RedactorRefusal` -> `scan_failed` and `hadavin_sdk.guard.redactor:SessionClosed` -> `session_closed`. `session_closed` is removed from P5a's `RESERVED_FOR`.
  2. **`Redactor` protocol (P5c-1)** (C1 F10: no `put_back` member):
     - **Members:** `name: str`, `version: str`, `fingerprint: str`, `mask(text: str, session: MaskSession, *, untrusted: bool) -> str` and `check(text: str, session: MaskSession) -> None`.
     - **`untrusted` has NO default (changed, R1-COR-1).** `untrusted=True` is `runmap.redact_untrusted` over the session's map: escape, then mask. `untrusted=False` is `runmap.redact_text`: mask only, so issued placeholders and markers pass unchanged.
     - **`check`** raises `RedactorRefusal("self_check_failed")` if a session original of 4 or more characters occurs in `text` as written, and `RedactorRefusal("forged_mark")` if `text` holds a placeholder that the session did not issue.
     - **Unexpected errors:** any exception inside `mask` or `check` that is not a `RedactionError` becomes `RedactorRefusal("internal")` (C1 D9).
  3. **`MaskSession` (P5c-1) and rule F10.**
     - **Shape.** It is neither a `dict` nor a `Mapping`. It holds a private `RunMap` (`__slots__ = ("_map", "_closed", "_lock")`).
     - **Methods:** `storable(kinds) -> dict[str, str]`, `issued(mark) -> bool`, `counts() -> dict[str, int]`, `close() -> None`, and use as a context manager (`__exit__` closes). `repr` shows only the count.
     - **Copy refusal: only `__getstate__` raises `TypeError`** (`__copy__` and `__deepcopy__` are cut, CHANGELOG cut 6). After `close()`, every method except `closed` raises `SessionClosed`.
     - **The module-private accessor `_map_of(session) -> RunMap`. Its callers are exactly these, pinned by an AST test (T1-17):**
       - `guard/redactor.py`: the `regex` kind and `restore`;
       - `runtime/agent_loop.py`: the toolbox call, `_run_tool`, `prepare_output` and `storable`.
     - **State plainly:** F10 makes the SESSION object impossible to copy, pickle or use after close. Inside one process, core code still hands the underlying map to the named callers. `tools.py` keeps taking a plain map for `invoke` and `prepare_output`.
     - **Rule F10, word for word ("F10 / D5 amendment" item 1):** "a MaskSession cannot be pickled (all protocols), copied or deep-copied, and direct calls to __reduce__ and __reduce_ex__ (0..5) raise TypeError. The mechanism may be __getstate__/__copy__/__deepcopy__ (the builder removed __reduce__ because object.__reduce__ calls the raising __getstate__). A test must assert exactly this list, including the two direct calls."
     - **Probes.**
       - Revision 1's probe (a stand-in with all three hooks): every item on the list raised, for a `__slots__` class AND for a `dict` subclass. But `dict(o)` copied the `dict` subclass's values without error, which is why the session is not a `dict`.
       - Revision 2's probe (a): `__getstate__` alone is enough.
       - T1-05 asserts F10's list plus `dict(session)` and `{**session}` raising `TypeError`.
       - Python 3.12 and 3.14: UNVERIFIED.
  4. **`regex` kind and the computed fingerprint (P5c-1; changed, CHANGELOG cut 5; PENDING LEAD 16).**
     - **Construction:** `RegexRedactor(name="regex", version=REGEX_VERSION)`, with `REGEX_VERSION: Final = "4"`. Settings: the base `KindSettings` (CHANGELOG cut 2).
     - **The fingerprint, computed ONCE at import:** `fingerprint = "regex@" + REGEX_VERSION + ":" + FOLD_VERSION + ":" + sha256(LF-normalised bytes of MASKING_SOURCES, in list order)[:16]`.
     - **`MASKING_SOURCES`** = `guard/redact.py`, `guard/runmap.py`, `guard/redactor.py`, P1's `guard/textnorm.py` and `guard/_confusables.py`, and P2d's look-alike module. P2d-2's module name is UNVERIFIED until it merges; the builder reads it from the merged code.
     - **Unreadable file:** a listed file that cannot be read makes the import raise (fails closed). Whether an install without `.py` sources exists anywhere is UNVERIFIED.
     - **No start-up comparison and no hand pin.** Editing any listed file changes the fingerprint, and through it every config hash, so a new gate run is needed (it fails safe).
  5. **Pattern changes in `guard/redact.py` (P5c-1; design section 9 PL-LK-7 and 9b PL-LK-23).** Lines are `124258b` lines unless marked; P2d-2 moves them. All three changes are covered by the fingerprint (no hand bump of the hash; `REGEX_VERSION` goes from C1a's "3" to "4" once).
     - **(i) PHONE's end.** It changes from `(?![\w.])` (`124258b` :476; `748849c` :483) to `(?!\w|\.\w)`. A 10-16 digit number at the end of a sentence is then masked, while `<digits>.5`, `<digits>.txt` and two runs joined by a full stop are not. UNCHANGED.
     - **(ii) Strong account keywords count as bank context (exact forms; changed, R1-ADV-16, R1-COR-6).** The source is `_ACCT_WORD` (:82: `(?:accounts?|acct\.?|acc\.?|a/c)(?:[ _\-\xa0]?(?:number|num\.?|nbr\.?|no\.?|#))?`).
       - **Mechanism:** the BANKACCT pattern gets a named group for the keyword, and `_bank_context` (:107) tests that group against one compiled `_ACCT_STRONG` regex, compiled with the same flags as the BANKACCT pattern.
       - **The table:**

         | form | suffix (`number`, `num`, `num.`, `nbr`, `nbr.`, `no`, `no.`, `#`) | counts as context? |
         |---|---|---|
         | `account`, `accounts` | with a suffix | yes (strong) |
         | `account`, `accounts` | none | NO (weak: common in logs) |
         | `acct`, `acct.` | with or without | yes |
         | `a/c` | with or without | yes |
         | `acc`, `acc.` | with a suffix | yes |
         | `acc`, `acc.` | none | NO (weak) |

       - **Effect:** `Account No: <6-17 digits>` is masked as BANKACCT with no bank word.
     - **(iii) NAME letters (changed, CHANGELOG cut 10).** In the `Dear` form (:447) and the title form beside it (:444), each name part changes from `[A-Z][a-z]+` to `[A-Z][^\W\d_]+(?:-[A-Z][^\W\d_]+)?`. The first letter stays `[A-Z]`. It stays a plain (kind, regex) row, so the fold scan and `redact_many` need no change. As a result, `Dear <first> <last>-<last>` and `Dear Jürgen <last>` are masked whole (probe (b)). Not masked: a name whose FIRST letter is a non-ASCII capital.
  6. **Config hash (P5c-1). UNCHANGED.** `registry.config_hash` (`registry.py:105`) ALWAYS adds `"masking": redactor.fingerprint` (C1 F4). Every existing hash changes once, and every agent needs one new `hadavin-sdk gate <agent>` run.
  7. **`MaskedLLM` (P5c-2; rewritten, R1-COR-1, R1-ADV-1, -2, -8, -17).**
     - **Construction.** `MaskedLLM.of(inner: LLM, redactor: Redactor, audit: AuditSink) -> MaskedLLM` returns `inner` unchanged when it already is a `MaskedLLM` with the same redactor fingerprint and the same audit sink. A different fingerprint or sink raises `TypeError` (T2-17). `__init__(..., *, _token)` raises `TypeError` on a wrong token.
     - **`chat`.** `chat(messages, *, system, route, tools=None, documents=None, output_schema=None) -> Reply` has the same signature as `LLM.chat`.
     - **The run context.** `run(run_id: str, principal: str) -> ContextManager[RunCtx]`. `RunCtx(run_id, principal, session)` lives in a `contextvars.ContextVar`. Thread hops use `contextvars.copy_context().run` (`k1b/loop.py:94` runs `chat` in a thread).
     - **Calls outside a run (changed, CHANGELOG cut 9).** A `chat` outside any `run(...)` raises `SessionClosed` and makes no inner call.
     - **What each call does, in order:**
       - **(a) Decode.** Bytes documents are decoded as strict UTF-8; a BOM is stripped. Invalid UTF-8, a NUL byte, or a PDF, PNG, JPEG, GIF or zip signature gives `unsupported_input`.
       - **(b) The wrapper never escapes.** It re-masks every `str` leaf of `messages[*].content` (content blocks too) and of `documents` with `redactor.mask(..., untrusted=False)` over the run's session.
         - **Pass 1** goes through the leaves in a fixed order: documents first, then messages.
         - **Pass 2:** if the session's map grew during pass 1, every leaf is masked once more, so a value first seen in a later leaf is masked in earlier leaves too.
         - There is no join and no split (CHANGELOG cut 4).
         - The caps (`defaults.MAX_REDACT_CHARS`) and the time budget (`defaults.REDACT_BUDGET_S`) apply per `redact_text` call (per leaf), as on main.
         - The whole body is still scanned on every call (C1 F2): there is no exemption for issued placeholders.
       - **(c) Check the body.** `check` runs over every leaf except assistant turns. An unissued placeholder gives `forged_mark`; a plain session original gives `self_check_failed`. This catches an entry point that forgot to escape (R1-ADV-8).
       - **(d) Check the configuration.** `system`, `tools` and `output_schema` are `check`ed and never masked (C1 F3).
       - **(e) Audit before the call.** One audit event is written with `write_intent` BEFORE the inner call (C1 D8): `domain="llm"`, `operation="outbound"`, `inputs_hash=sha256_hex(masked body)`, `rule_id=redactor.fingerprint`, `result="chars=<in>/<out>;" + sorted "kind:n"` counts. If it raises `AuditUnavailable`, that goes to the caller and no call is made.
       - **(f) The inner call.** `inner.chat(...)`. Any refusal raises `RedactorRefusal` or `RedactionError`, and the inner model is never called.
     - **One masking mode per input class (PENDING LEAD 15).** Raw external text is escaped ONCE, where it enters, with `redact_untrusted`:

       | input class | where it is escaped (before the wrapper) | what the wrapper does |
       |---|---|---|
       | raw `extract` document | **NEW:** `extract` calls `redactor.mask(doc, session, untrusted=True)` before the call | re-mask (trusted) and check |
       | raw gate case (`evals.py`) | STAYS (`evals.py:63`), now over the run's session, not a fresh `{}` | re-mask and check |
       | run-loop document | STAYS (`agent_loop.py:367`) | re-mask (no change expected) and check |
       | user turn | (core text) | re-mask and check |
       | assistant turn | (model text) | re-mask only. An invented placeholder carries no value, and put-back already denies it as `input.unresolved`. |
       | tool result | STAYS (`prepare_output`, `tools.py:936`) | re-mask and check |
  8. **Put-back (P5c-4; changed, R1-ADV-3, -4).**
     - **Signature.** `restore(value: Any, mapping: Mapping[str, str], kinds: frozenset[str]) -> Any` in `guard/redactor.py` is the only restore in core. It takes a plain map, not a session.
     - **Rules.** It restores stored kinds only: `kinds` must be a subset of `STORED_KINDS`, else `ValueError` at the call site (a programming error). It makes one pass. It never restores a placeholder whose map entry carries the P2d "withheld or folded" marker (P2d L5, RESTORE-1; the marker form is PENDING LEAD 11). The kind filter and the folded-spelling filter apply at every seam.
     - **Called from exactly three places:**
       - `Runtime.inputs_view` (`agent_loop.py:269-284`), passing `store.get_redaction_map(...)` as today, at execute time, after the session is closed;
       - `_run_tool` (`:295`), passing the live map;
       - `ToolBox.invoke` (`tools.py:1178`), passing the live map that the run loop handed it.
     - **A placeholder left over** keeps today's result: the gate denies `input.unresolved` (`:794-797`).
- **Neutral default / working alternative (or written outline with trigger):** the default is `regex` (standard library only, `neutral=True`).
  - **Outline, not built:** a detector-model backend (a local named-entity model behind the same protocol, for names in free prose and document types the patterns miss). Trigger: "a client document type the patterns miss" (plan-v3 section 5). It also writes the shared contract suite (V3; CHANGELOG cut 3).
  - A test double is not an alternative (plan rule 8).
  - **Lock-in guard.** Rule b (`tests/test_lockin_guard.py:5`, table at `:381`) gets one dated `EXCEPTIONS` row for `redactor`, with this trigger and `review_by` 2027-01-31 (PENDING LEAD 13).
- **Files to create, change, delete (each with the reason):**
  - **P5c-1:**
    - **Create:** `src/hadavin_sdk/guard/redactor.py` (items 1-4), `tests/test_p5c1_redactor.py`, `tests/test_p5c1_patterns.py`, `tests/p5c_mutants.py`.
    - **Change:**
      - `guard/redact.py`: item 5;
      - `guard/__init__.py`: `__all__`;
      - `backends/table.py`: `TABLE["redactor"] = {"regex": Entry(KindSettings, ...)}` neutral at `:386`, `ALLOWED["redactor"] = frozenset()` at `:570`, `DEFAULTS["redactor"] = "regex"` at `:582`, no `DEV_ONLY` pair;
      - `backends/builtin.py`: the factory, built after `llm` and before `detector`;
      - `config.py`: records which kinds were named explicitly, and refuses a config without an explicit `redactor` outside `dev` (C1 F12);
      - `registry.py`: item 6;
      - `codes.py`: P5a's table;
      - `tests/test_lockin_guard.py`: the `EXCEPTIONS` row;
      - `CHANGELOG.md`.
    - **Existing tests changed by P5c-1 (R1-COR-8), each listed in the evidence with its reason:**
      - **(a) Tests that pin a config hash or a `qualified.jsonl` line.** The hash changes once. `tests/conftest.py:58` builds it from `registry.config_hash`. Counts at `124258b`, re-derived by me:
        - `git grep -l -E 'config_hash|qualified\.jsonl' 124258b -- tests` = 14 files;
        - the wider `git grep -l -E 'config_hash|qualified' 124258b -- tests` = 21 files;
        - the resolve's "20 files" is reproduced by neither pattern.
        - The builder lists the final set from the second command.
      - **(b) Pilot and prod config fixtures** (62 `"pilot"`/`"prod"` hits in `tests` at `124258b`) are checked against the explicit-`redactor` rule. A fixture gains `[backends.redactor] kind = "regex"`; the rule itself is never loosened.
  - **P5c-2:** create `src/hadavin_sdk/llm/masked.py` and `tests/test_p5c2_masked_llm.py`, and add a `RecordingLLM` test double to `tests/conftest.py` (it records COPIES of the messages, documents, system, tools and schema of every call, C1 D11). No other file.
  - **P5c-3:**
    - **`runtime/agent_loop.py`:**
      - `Runtime.__init__` requires `isinstance(llm, MaskedLLM)`, and outside `dev` it refuses a wrapper whose fingerprint differs from the configured redactor's (T3-18);
      - `handle` enters `llm.run(run.run_id, principal_id)` for its whole body, and the run map becomes the session's;
      - `received` carries no `inputs_hash` (CHANGELOG cut 11);
      - strict UTF-8 decoding;
      - the chat block also catches `AuditUnavailable`, so a person looks with reason `audit_unavailable` (C1 F7);
      - the session is closed in `finally`.
    - **`app.py`:** `:162` wraps the built model with `MaskedLLM.of` BEFORE the detector is built; `build(llm=raw)` wraps too.
    - **`cli.py`:** the gate at `:150` and k1b at `:221` build their wrappers over one raw model (C1 F6). The flag at `:120` keeps its meaning (CHANGELOG cut 1).
    - **`extract.py`:** requires the wrapper; puts the whole retry loop in one `run(...)`; escapes the document with `redactor.mask(..., untrusted=True)` before the call; returns placeholders only.
    - **`evals.py`:** requires the wrapper; each (case, k-run) runs in its own `run(...)`, and the existing `redact_untrusted` at `:63` uses that run's session.
    - **`guard/judge.py`:** `JudgeDetector.__init__` requires the wrapper. `:71`'s own `redact_text(text, {})` is removed, so judge placeholders equal run placeholders.
    - **`guard/injection.py`:** re-raises `RedactionError` and `AuditUnavailable` (C1 D9, F7, F11).
    - **`guard/producers.py`:** the judge row (`:28`) and the evals row (`:40`) become "through `MaskedLLM`". The vendor guardrail row (`:29`) is unchanged: `guard/bedrock_guardrail.py` is not a `.chat(` door and keeps its own `redact_text`.
    - **`tests/test_k5_producers.py`:** checks the new rows (T3-17).
    - **`k1b/loop.py`:** uses `MaskedLLM.of`; `except RedactionError` and `except AuditUnavailable` give status `error` and halt `aborted`.
    - **`tests/conftest.py`:** a shared `masked_llm` fixture.
    - **Tests that build a model user with a raw model.** `git grep -n -E '\b(Runtime|gate|extract|JudgeDetector)\(' 124258b -- tests` = 42 lines in 20 files (re-run by me; revision 1's "43" was wrong by one). This is a FLOOR. The evidence lists the final grep, which includes `tests/demo_askdata` and `demos/`. Each line is changed by wrapping with `MaskedLLM.of(...)`, never by loosening the check.
    - **FakeLLM recordings** keyed by the hash of a masked first document are renamed by a throwaway script outside the repository (C1 D11; how many: UNVERIFIED).
    - README and CHANGELOG.
    - **Create:** `tests/test_p5c3_wiring.py` and `tests/test_c1_acceptance.py`.
  - **P5c-4:**
    - **Change:**
      - `guard/redactor.py`: item 8;
      - `runtime/agent_loop.py`: the two seams call `redactor.restore`;
      - **`tools.py`:** `:1178` calls `redactor.restore`. Whether importing `guard/redactor.py` from `tools.py` creates an import cycle is UNVERIFIED; if it does, the restore function is passed in, not imported;
      - **`defaults.py`:** PHONE is removed from `STORED_KINDS`, if PENDING LEAD 17 is accepted. `Config.evidence.stored_kinds` may only narrow. The builder lists the existing tests that relied on stored phones, each with its reason;
      - `deferred.py`: `DEFERRED_KEYS["restorable"] = "v1.1 row V2"`;
      - README and CHANGELOG.
    - **Create:** `tests/test_p5c4_putback.py`. **Add:** row T4-04 to `tests/test_c1_acceptance.py`.
  - Nothing is deleted. `guard/runmap.py` is NOT edited by P5c (it is P2d's file).
- **Existing core code reused (checked):**
  - **Reused:**
    - `guard/runmap.py`, read at `124258b`;
    - `guard/redact.py` (`124258b`; `748849c` for P2d's form);
    - `guard/producers.py` (`124258b`);
    - `hashing.sha256_hex` (`agent_loop.py:349`);
    - **`AuditSink.write_intent` (`audit/protocol.py:19`), which exists and raises `AuditUnavailable`.** The run loop today uses only `write_outcome`, so failing closed when the audit sink is down is new for the run loop (R1-COR-10);
    - `deferred.DEFERRED_KEYS`;
    - `backends/table.py` (`KindSettings`, `TABLE` :386, `ALLOWED` :570, `DEFAULTS` :582, `DEV_ONLY` :593);
    - `tests/test_lockin_guard.py` `EXCEPTIONS`;
    - P1m's `tools/mutation_runner.py`.
  - **Checked and NOT reused:**
    - `k1b/redaction.py`: the bundle masking stays as it is, and the wrapper re-masks;
    - `stats` and `evals` scoring;
    - `store/memory`: no new store method;
    - `tests/contracts`: no redactor suite in v1.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):**
  - **The redactor kind** has `identity="none"` and `rights=()`. It is pure and in-process: no network, environment or database access. It reads the `MASKING_SOURCES` files once at import to compute the fingerprint.
  - **The wrapper** holds the audit sink it is given and reads no secret.
  - **No `dev_only` pair.** Pilot and prod config must name the redactor explicitly (C1 D6, F12).
  - **Personal data.**
    - Originals live only in the session in memory, and only stored kinds are written to the store. The session is closed at the end of every run, and it cannot be copied or pickled.
    - The outbound audit event holds a plain sha256 of the masked body and counts per kind. The README states the brute-force limit for short bodies.
    - **`received` holds no hash of the raw document** (G3).
  - **Card and bank numbers labelled PHONE (G10; PENDING LEAD 17).** With PHONE out of the default stored kinds, a bare 16-digit card number, or a 10-11 or 13-16 digit bank number masked as PHONE, is never stored and never put back. The cost: a phone number is no longer put back into a plan (v1.1 row V10).
  - **`extract` in v1 (PENDING LEAD 20).** Core `extract` returns placeholders and offers no restore handle. A field whose schema checks the format of a masked value (an IBAN, an all-digits account) fails its check on the placeholder and goes to `DeadLetter`. **Intake cannot move its invoice bank-detail extraction onto core `extract` in v1** (v1.1 row V9). The retry text sent back to the model holds placeholders only.
  - **What P5c does NOT promise.** Each item is in the README "not masked" list, pinned by a test that the README names it (C1 D12):
    - (a) names in free prose with no title or `Dear`;
    - **(a2) names whose first letter is a non-ASCII capital** (PENDING LEAD 21; NAME-NONASCII-INITIAL);
    - (b) plain account numbers (see "Order 11(5)" below);
    - (c) **look-alike copies of secrets of 8 to 11 characters: only plain copies are caught** (order 15);
    - (d) **a known value encoded in base64, hex or invisible characters is not read by the look-alike check.** Only the tool-output scrubber removes the exact hex and base64 spellings of a secret handed to a tool; nothing else in v1 catches an encoded copy (order 19 C, PL46(a));
    - (e) partial or one-character-changed copies (design section 8);
    - (f) images, PDFs and other non-text documents are refused, and so are text documents that are not UTF-8 (PENDING LEAD 3);
    - (g) prompts, contract descriptions and schemas are checked but not masked (V5);
    - (h) `extract` returns placeholders and cannot fill format-checked fields (V9);
    - (i) `DeadLetter.errors` may hold reply text until P5b3 (A5).
  - **Money-adjacent: 12-digit account numbers, both directions (PENDING LEAD 8; R1-ADV-6).**
    - **(a) With a strong keyword: never put back.** A cloud account id written as `Account Number: <12 digits>` becomes BANKACCT under pattern (ii), so it is never stored and never put back. The plan's input stays a placeholder and the gate denies `input.unresolved`: a person looks, and no wrong value is used (row ACC-12b).
    - **(b) Bare: stored.** A bare 12-digit bank number is masked as ACCOUNTID (`redact.py:353`) and stored (`defaults.py:108-109`), so it can be put back into a plan.
    - Recommended: keep ACCOUNTID stored (cloud-operation agents need account ids back), state it in the README, and pin it with ACC-12. Pattern (ii) stays as written, because it fails safe.
  - **Test data.** Fake values in tests are built from parts at run time (a documentation IBAN, an `example.invalid` e-mail, made-up names, `"sk-" + "a" * 30`), never as one literal (order 8(5)). No variable is named `password`, `secret` or `token`.
- **Order 11(5): does the core detector set close Intake's plain account number without a context word? No, not in general.**
  - **What main masks today with NO context word** (`124258b`):
    - 10, 11 and 13-16 digits standing alone are masked as PHONE (`redact.py:476`), and **today PHONE is stored**;
    - exactly 12 digits are masked as ACCOUNTID (`:353`);
    - 8-9 and 17-18 digits are NOT masked;
    - 10-16 digits right before a full stop are NOT masked;
    - digits glued to letters are not masked;
    - a JSON number is never scanned (`runmap.py:588` `_redact_value`).
  - **What P5c closes:**
    - ACC-1c: 10-16 digits at the end of a sentence (item 5 (i));
    - ACC-2: the strong keywords of the table plus 6-17 digits (item 5 (ii));
    - **with PENDING LEAD 17: PHONE-labelled numbers are no longer stored** (T4-01).
  - **What stays open in v1, with the reason:**
    - 8-9 and 17+ digits with no keyword: a pattern of those lengths would mask dates, amounts and invoice numbers;
    - digits glued to letters;
    - JSON numbers.
  - These are strict-xfail records (ACC-1a, ACC-1b, ACC-3) and v1.1 row V4.
  - Intake's own masking (`promotion-inputs/intake-a12/src/intake/mask.py`) is UNVERIFIED; the lead's statement of the gap is taken as given.
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** row ids are fixed. FB = fails before (on the main head the pull request rebases on, P2d-2 included; for pattern rows, the merged P2d-2 head). PIN = regression pin. NEW = new surface, guarded by mutants. XF = `xfail(strict=True)` record with its v1.1 row.
  - **P5c-1, `tests/test_p5c1_redactor.py` (16 rows):**
    - T1-01 `test_protocol_members_exact` (no `put_back`; `mask` has no default for `untrusted`) NEW.
    - **T1-02 `test_fingerprint_computed_over_masking_sources`** (changed). Editing any listed file, simulated on a temporary copy, changes the fingerprint. The list covers every `hadavin_sdk.guard` module that `guard/redactor.py` imports, directly or through other modules (AST walk). `REGEX_VERSION == "4"` and `FOLD_VERSION` is part of the string. NEW.
    - T1-04 `test_config_hash_includes_masking` FB.
    - T1-05 `test_session_cannot_be_copied_or_pickled` (F10's exact list plus `dict(s)` and `{**s}`; not a `Mapping`) NEW.
    - T1-06 `test_closed_session_raises_session_closed` NEW.
    - T1-07 `test_codes_closed_list` NEW.
    - T1-08 `test_refusal_carries_code_only` NEW.
    - T1-09 `test_code_of_mapping` NEW.
    - T1-10 `test_p5a_rows_and_reserved_list_empty` NEW.
    - T1-11 `test_kind_wiring` (`KindSettings`, neutral, build order) FB.
    - T1-12 `test_pilot_and_prod_config_without_explicit_redactor_refused` FB.
    - T1-13 `test_lockin_exceptions_row_is_dated` FB.
    - T1-14 `test_same_value_same_mark_across_texts` NEW.
    - T1-15 `test_check_trusted_config_holding_session_original` NEW.
    - T1-16 `test_check_unissued_mark_in_trusted_config` NEW.
    - **T1-17 `test_map_of_callers_ast`** (exactly the callers of item 3) NEW.
    - T1-03 is cut (CHANGELOG cut 5).
  - **P5c-1, `tests/test_p5c1_patterns.py` (13 rows; made-up digits built in the test):**
    - ACC-1c FB.
    - ACC-1c-NEG NEW.
    - **ACC-2** (changed): one parametrised case per strong form of the item-5 table, 59 cases: `account`/`accounts` x 8 suffixes = 16; `acct`/`acct.` bare = 2; `acct`/`acct.` x 8 suffixes = 16; `a/c` bare = 1; `a/c` x 8 = 8; `acc`/`acc.` x 8 = 16. Each with 8 digits and no bank word, giving BANKACCT. FB.
    - **ACC-2-NEG** (changed): one case per weak form (`account`, `accounts`, `acc`, `acc.`, bare: 4 cases), plus `Account No: <5 digits>`; none gives BANKACCT. NEW.
    - ACC-12 (bare 12 digits gives ACCOUNTID, stored; `Account No: <12 digits>` gives BANKACCT, not stored) FB for the second half.
    - NAME-HYPH FB.
    - NAME-NONASCII (`Dear Jürgen <last>`) FB.
    - **NAME-TITLE** (the title form with a hyphenated part and a non-ASCII following letter) FB.
    - **NAME-DECOMPOSED** (`Dear Jose` + U+0301 + ` <last>`: the whole name is absent from the output) PIN, by reading only (probe (b); main's NFKC second pass).
    - **NAME-NONASCII-INITIAL** XF (a name with a non-ASCII first capital; V4b).
    - ACC-1a XF (V4).
    - ACC-1b XF (V4).
    - ACC-3 XF (V4, LKV-8).
    - The repository suite runs with item 5 in place. Any existing pin that item 5 changes is listed with its reason, never weakened.
  - **P5c-2, `tests/test_p5c2_masked_llm.py` (16 rows, all through `RecordingLLM`):**
    - T2-01 `test_chat_signature_identical_to_llm_chat` NEW.
    - **T2-02 `test_value_first_seen_in_later_leaf_masked_in_earlier`** (changed: two passes, no join) NEW.
    - T2-03 `test_content_blocks_masked` NEW.
    - T2-04 `test_system_tools_schema_checked_not_masked` NEW.
    - T2-05 `test_constructor_token_and_of_idempotent` NEW.
    - T2-06 `test_one_outbound_record_per_call_written_before_chat` NEW.
    - T2-07 `test_audit_unavailable_no_inner_call` NEW.
    - T2-08 `test_redactor_exception_no_inner_call` NEW.
    - T2-09 `test_bytes_document_strict_utf8` NEW.
    - **T2-10 `test_two_threads_two_runs_no_crosstalk`** (changed): a `threading.Barrier(2)` inside `RecordingLLM.chat` and two DISTINCT values, so a module-global context is forced to interleave. NEW.
    - **T2-11 `test_call_outside_run_refused`** (changed: `SessionClosed`, zero inner calls) NEW.
    - T2-13 `test_mark_next_to_raw_value_still_masked` NEW.
    - **T2-14 `test_lookalike_copy_zero_inner_calls`** PIN through the wrapper (relabelled; P2d-2 is in the base).
    - **T2-15 `test_body_check`** (new): (a) a raw document holding a forged `<EMAIL_9>`, sent with no escape, gives `forged_mark` and zero inner calls; (b) a plain session original left in a leaf (masker stubbed) gives `self_check_failed`; (c) a benign collision: a stored short made-up name that also appears inside a longer word. The result of (c) is written down, because the benign-refusal rate is UNVERIFIED. NEW.
    - **T2-16 `test_issued_marks_and_markers_arrive_unchanged`** (new): an issued placeholder in an assistant turn and in a tool turn, and a `<<TOOL RESULT` marker, appear byte-identical in the recorded body. NEW.
    - **T2-17 `test_of_refuses_a_different_redactor_or_sink`** (new) NEW.
    - T2-12 is cut (CHANGELOG cut 1).
  - **P5c-3, `tests/test_p5c3_wiring.py`, `tests/test_c1_acceptance.py`, `tests/test_k5_producers.py` (25 rows). Each row names its entry path:**
    - **T3-01 `test_pii_never_reaches_llm`** (acceptance; `app.build(llm=RecordingLLM(...))`, at least 3 tool steps, a new value at step 2, judge calls included). FB on the `extract` and audit paths; PIN on the run loop.
    - **T3-02 `test_raising_redactor_needs_person_no_chat_no_judge`**: PIN (run loop). It has no mutant of its own (the "M24, M33" cross-reference is removed, R1-ADV-15).
    - **T3-03 `test_extract_document_masked`**: path `extract`, FB. Both the first call and the retry call hold placeholders only.
    - **T3-03b `test_extract_forged_mark_escaped`** (new): path `extract`; a forged `<EMAIL_9>` arrives as `‹EMAIL_9›` and the call succeeds. FB (on base the raw text is sent).
    - **T3-04 `test_received_has_no_raw_document_hash`** (changed): path run loop, FB.
    - T3-05 `test_non_utf8_document_refused`: path run loop, FB.
    - T3-06 `test_wrapper_required_isinstance` over `Runtime.__init__`, `evals.gate`, `extract.extract`, `JudgeDetector.__init__`: FB.
    - **T3-07 `test_raw_llm_import_graph_ast`** (changed): (b) every `make("llm", ...)` is in `app.build_llm` or `cli.py`'s named builders; (c) no module outside `llm/`, `backends/builtin.py` and `app.py` imports a raw llm kind module; (d) `demos/ask-your-data/askdata/pipeline.py` is scanned, or its exclusion is written with a reason. FB.
    - **T3-09 `test_judge_uses_run_session`** (rewritten): path judge. Call `JudgeDetector.check` with text holding a NEW raw made-up e-mail plus an issued `<EMAIL_1>` of another value. After P5c the new value gets `EMAIL_2`. On base the fresh map numbers it `EMAIL_1`, a collision, so the row is FB.
    - T3-10 `test_gate_session_fresh_per_case`: path gate, NEW.
    - **T3-11 `test_k1b_goes_through_the_wrapper`** (changed): path k1b, NEW.
    - T3-12 `test_redactor_raises_on_second_call_reason_is_redaction_error`: path injection check, FB (`injection.py` turns it into `guard_unavailable` today).
    - T3-13 `test_audit_unavailable_at_outbound_needs_person`: path run loop, NEW.
    - T3-14 `test_output_tree_has_no_seeded_values` (logs, audit rows, stored runs, cards, exception texts): PIN on the run loop.
    - **T3-14b `test_tool_result_forged_mark_escaped`** (new): path tool result; the run continues, and the recorded body holds `‹...›`. PIN (`prepare_output` escapes today).
    - **T3-15a..f `test_lookalike_copy_in_document_zero_model_calls[...]`** (the lead's order 11(1) rows: Cyrillic/Greek, fullwidth, zero-width, combining mark, split over two lines, other case): path run loop, **PIN through the wrapper** (relabelled).
    - **T3-15g `test_extract_lookalike_copy_zero_model_calls`** (new): path `extract`, FB (on base `extract` sends the raw document).
    - **T3-16 `test_golden_and_eval_input_ref_files_are_strict_utf8`** (new). I checked the 11 repository paths whose name contains "golden": all decode as strict UTF-8. Other `input_ref` files are UNVERIFIED. PIN.
    - **T3-17 `test_k5_producers_judge_and_evals_through_maskedllm`** (new, in `tests/test_k5_producers.py`) FB.
    - **T3-18 `test_runtime_refuses_mismatched_fingerprint_outside_dev`** (new) NEW.
    - T3-08 is cut (CHANGELOG cut 8).
  - **P5c-4, `tests/test_p5c4_putback.py` (9 rows):**
    - **T4-01 `test_secret_regulated_and_phone_labelled_numbers_never_restored`** (changed): IBAN, CREDITCARD, each SECRET kind, BANKACCT, BANKCODE, SSN, AADHAAR, PAN and UUID stay placeholders, **plus a bare made-up 16-digit card number, a 10-digit and a 14-digit number (masked as PHONE)**. FB for the PHONE part; PIN for the rest.
    - T4-02 `test_withheld_line_placeholder_not_restored` FB.
    - **T4-03 `test_restore_called_only_at_three_seams_ast`** (changed: `inputs_view`, `_run_tool`, `ToolBox.invoke`; no `runmap.restore_value` call left in `agent_loop.py` or `tools.py`) FB.
    - T4-04 (in `test_c1_acceptance.py`) `test_restored_values_appear_only_in_the_proposal`: PIN plus the new seams.
    - T4-05 `test_plan_with_unresolved_mark_never_executes` PIN.
    - T4-07 `test_restorable_key_refused_at_load` FB.
    - T4-08 `test_restore_gives_written_spelling` NEW.
    - **T4-09 `test_restore_at_approval_in_fresh_process_from_store_only`** (new, R1-ADV-4) PIN.
    - **ACC-12b `test_account_number_12_digits_never_put_back`** (new, R1-ADV-6): `Account Number: <12 digits>` gives BANKACCT; the plan input stays a placeholder; the gate denies `input.unresolved`. FB (on base it is ACCOUNTID and is restored).
    - T4-06 is cut (CHANGELOG cut 7).
  - **FAIL-BEFORE method (C1 F14):**
    - Tests import new modules inside the test or with `pytest.importorskip`, and fixtures do not write `[backends.redactor]` or `restorable`.
    - Commit the tests first, run `git checkout <base> -- src` keeping the tests, run them, save the output, then `git checkout HEAD -- src`.
    - Base for the P5c-1 pattern rows: the merged P2d-2 head. For every other row: the main head the pull request rebases on.
    - A table "row | entry path | expected on base: assertion failure / ImportError / skipped" goes in the evidence file. PIN rows are named as such and not counted as FB.
  - **Hostile inputs covered (reviewer checklist):**
    - a value first seen in a later leaf (T2-02);
    - a value next to an issued placeholder (T2-13);
    - forged placeholders: in trusted config (T1-16), in a raw `extract` document (T3-03b, T2-15a), in a tool result (T3-14b);
    - issued placeholders and markers passing unchanged (T2-16);
    - invalid UTF-8, NUL, file signatures (T2-09, T3-05, T3-16);
    - look-alike copies (T3-15a..g, T2-14);
    - threads with a barrier (T2-10);
    - a raising redactor (T2-08, T3-02, T3-12);
    - audit down (T2-07, T3-13);
    - copies and pickles (T1-05);
    - use after close and calls outside a run (T1-06, T2-11);
    - restore of secret kinds, PHONE-labelled numbers and folded spellings (T4-01, T4-02, T4-08);
    - a mismatched wrapper (T2-17, T3-18).
    - **Size and time:** main's caps apply per leaf. The `perf`-marked row **T2-P** (changed) is a 20-step history whose leaves are each near `MAX_REDACT_CHARS`, made of the adversarial shapes of C1 F11 plus 5,000 distinct e-mails and IBANs. The runner measures the time and pins it; the budget number is UNVERIFIED.
  - **Contract suite:** none in v1 (one backend; CHANGELOG cut 3, row V3).
  - **Totals (re-derived):** 79 rows (16 + 13 + 16 + 25 + 9), of which 4 are strict-xfail records (ACC-1a, ACC-1b, ACC-3, NAME-NONASCII-INITIAL), plus the `perf` row T2-P, making 80 with it. ACC-2 runs 59 parametrised cases and ACC-2-NEG runs 5. Revision 1 had 68 + 1.
- **Mutation plan (which behaviours get a mutant, which test kills each):**
  - **How mutants run.** They run through P1m's runner from `tests/p5c_mutants.py` (`Mutant(name, file, old, new, expect, ...)`). `old` is the exact source line the builder writes, so it cannot be listed in advance. Each mutant must end KILLED, never CRASH or WRONG_REASON, and each killing test is run twice. The table "mutant -> killing test" is pasted into the evidence BEFORE the run (C1 F11).
  - **44 mutants** (revision 1 had 41: M1, M4, M5, M27 and M40 are cut, and M42-M49 are new). Every mutant has a named killer.
  - **P5c-1 (17):**
    - M2 `config_hash` omits `masking` -> T1-04;
    - M3 `__getstate__` removed -> T1-05;
    - M6 `MaskSession` derives from `dict` -> T1-05;
    - M7 the closed check raises `internal` -> T1-06;
    - M8 the closed check removed -> T1-06;
    - M9 an unknown code kept as given -> T1-08;
    - M10 `LookalikeCopy` mapped to `internal` -> T1-09;
    - M11 a known value gets a new number -> T1-14;
    - M12 `check` skips `system` -> T1-15;
    - M13 PHONE's end back to `(?![\w.])` -> ACC-1c;
    - M14 PHONE's end widened to `(?!\w)` -> ACC-1c-NEG;
    - **M15 one strong form dropped from `_ACCT_STRONG` -> ACC-2;**
    - **M16 bare `account(s)` added to `_ACCT_STRONG` -> ACC-2-NEG;**
    - M17 the NAME hyphen part removed -> NAME-HYPH;
    - M18 the NAME letter class back to `[a-z]` -> NAME-NONASCII;
    - M19 the explicit-redactor check removed for prod -> T1-12;
    - **M46 `MASKING_SOURCES` drops `guard/runmap.py` -> T1-02.**
  - **P5c-2 (13):**
    - M20 documents not masked -> T2-02;
    - **M21 pass 2 skipped when the map grew -> T2-02;**
    - M22 `system` masked instead of checked -> T2-04;
    - M23 the audit `write_intent` after the inner call -> T2-06;
    - M24 a redactor exception passed through to the inner call -> T2-08;
    - M25 decode with `replace` -> T2-09;
    - M26 the context in a module global instead of a `ContextVar` -> T2-10 (the barrier forces interleaving);
    - M28 issued-placeholder regions exempted from the scan -> T2-13;
    - M29 `AuditUnavailable` swallowed -> T2-07;
    - **M42 `check` skipped on the body -> T2-15;**
    - **M44 `of()` returns the existing wrapper despite a different fingerprint or sink -> T2-17;**
    - **M47 a call outside `run(...)` opens an implicit session -> T2-11;**
    - **M48 the wrapper masks leaves with `untrusted=True` -> T2-16** (issued placeholders become `‹...›`).
  - **P5c-3 (9):**
    - M30 `app.build(llm=raw)` not wrapped -> T3-06 and T3-01;
    - **M31 (retargeted) `extract` skips the untrusted escape (`untrusted=False`) -> T3-03b.** Why the wrapper does not hide it: the wrapper does not escape, so the forged mark reaches the body check, which refuses with `forged_mark`, while T3-03b requires a successful call holding `‹EMAIL_9›`.
    - **M32 `received` keeps `inputs_hash` of the raw document -> T3-04;**
    - M33 `Runtime` decodes with `replace` -> T3-05;
    - M34 the `isinstance` check removed in `Runtime.__init__` -> T3-06;
    - M35 `injection_check` swallows `RedactionError` -> T3-12;
    - **M36 (retargeted) tool-output masking dropped (`prepare_output` returns the raw text) -> T3-14 and T3-14b.** Why the wrapper does not hide it: the wrapper re-masks the model body, but the stored run and the log lines carry the tool output unmasked (T3-14), and a forged mark in a tool result is no longer escaped, so the body check stops the run (T3-14b requires it to continue).
    - M37 the judge given a fresh session -> T3-09;
    - **M45 `Runtime.__init__` ignores a fingerprint mismatch outside `dev` -> T3-18.**
  - **P5c-4 (5):**
    - M38 the kind filter removed from `restore` -> T4-01;
    - M39 the withheld/folded marker ignored -> T4-02 (written once the merged P2d-2 marker form is known, PENDING LEAD 11);
    - M41 an unresolved placeholder allowed to execute -> T4-05;
    - **M43 PHONE added back to `STORED_KINDS` -> T4-01;**
    - **M49 `tools.py:1178` calls `runmap.restore_value` again -> T4-03.**
  - **Reverse check:** a wrapper that returns `inner.chat(...)` unchanged must fail T2-02, T2-13, T2-15, T3-01, T3-03 and T3-15g (pasted count).
- **Evidence commands (exact), and where the raw output is saved:**
  - **Who and where.** A SEPARATE evidence runner (its brief says "EVIDENCE RUNNER") runs these once on the final commit of each fix batch, on Python 3.13 (CI's version), and on 3.12 when the lead runs them on the laptop. Raw output goes under `handover/evidence/P5c/` as `P5c-<n>-<step>.txt`. Exit codes come from pytest itself, never from a `| tail` pipe.
  ```
  uv sync --locked --no-build --all-extras --group test
  uv run --all-extras --group test pytest tests/test_p5c1_redactor.py tests/test_p5c1_patterns.py -q -rA > P5c-1-new.txt 2>&1; echo rc=$?
  uv run --all-extras --group test pytest tests/test_p5c2_masked_llm.py -q -rA -m "not perf" > P5c-2-new.txt 2>&1; echo rc=$?
  uv run --all-extras --group test pytest tests/test_p5c2_masked_llm.py -q -rA -m perf > P5c-2-perf.txt 2>&1; echo rc=$?   # alone
  uv run --all-extras --group test pytest tests/test_p5c3_wiring.py tests/test_c1_acceptance.py tests/test_k5_producers.py tests/test_p5c4_putback.py -q -rA > P5c-34-new.txt 2>&1; echo rc=$?
  uv run --all-extras --group test pytest -q -m "not live and not perf" -rs > P5c-<n>-full.txt 2>&1; echo rc=$?
  uv run --all-extras --group test ruff check src tests demos; uv run --all-extras --group test ruff format --check <touched files>
  uv sync --locked --no-build --only-group scan && bandit -q -r src demos -ll
  uv run --all-extras --group test python tools/mutation_runner.py tests/p5c_mutants.py > P5c-<n>-mutants.txt 2>&1; echo rc=$?
  uv run --all-extras --group test python -I -c "from hadavin_sdk.guard.redactor import RegexRedactor, MASKING_SOURCES; print(RegexRedactor().fingerprint); print(MASKING_SOURCES)" > P5c-1-fingerprint.txt 2>&1; echo rc=$?
  git grep -n -E '\b(Runtime|gate|extract|JudgeDetector)\(' HEAD -- tests demos > P5c-3-raw-model-sites.txt; echo rc=$?
  git grep -l -E 'config_hash|qualified' HEAD -- tests > P5c-1-hash-tests.txt; echo rc=$?
  ```
  - **Also saved:**
    - the fail-before table with entry paths;
    - the `BL-core-c1a-*` disposition table (44 rows);
    - the list of changed existing tests with reasons (P5c-1, P5c-3, P5c-4);
    - `git diff --stat origin/main` per pull request.
  - The runner's mutation arguments are taken from P1m's merged README (UNVERIFIED here). The exact `RegexRedactor()` constructor call is UNVERIFIED until P5c-1 is written.
- **Reviewers:** correctness + adversarial, fresh `egm:*` agents each round. They get the diff, this ticket and the evidence only (plan-v3 section 4), on a snapshot of the pull request head (never the disk tree; see "Base"). The adversarial brief names the redaction path and the money-adjacent put-back.
- **Done =** the plan's stop rule for the RESULT review (two rounds in a row at the final commit with no blocker and no major, and evidence green at that commit), and all gates green:
  - tests, `ruff check`, `ruff format --check` and `bandit -ll`;
  - the guard tests (`test_lockin_guard`, `test_no_hardcoded_values`, `test_k5_producers`, `test_repo_rules`, `test_no_reference_material`);
  - CodeQL, SonarCloud and CodeRabbit;
  - 44 of 44 mutants killed;
  - the fail-before table pasted;
  - `grep -n xfail` lists exactly ACC-1a, ACC-1b, ACC-3 and NAME-NONASCII-INITIAL from this package;
  - the README sections exist: supported input types; the NOT masked list; where personal data is kept; the plain-hash limit; `extract` gives no put-back;
  - the CHANGELOG entries (below).
- **Rollback:**
  - **Tags.** The lead tags `pre-P5c-<n>` before each merge. There is no migration and no change to the stored-data format.
  - **Non-revertible in effect (marked):**
    - P5c-1 changes every agent's config hash (one new gate run each). Reverting it changes the hashes again (another gate run). **The P2d/P5c-1 "revert together" lock is gone (CHANGELOG cut 5):** reverting P2d changes the fingerprint and needs a gate run, but nothing refuses to start.
    - Any later edit to a `MASKING_SOURCES` file needs a new gate run.
    - P5c-3's refusal of non-UTF-8 documents is a behaviour change that operators see.
    - P5c-4's removal of PHONE from the stored kinds: phone numbers saved before it are still put back from old saved maps. New runs store none. Reverting P5c-4 brings PHONE storage back (fails open for card and bank numbers labelled PHONE, so the lead decides).
  - **CHANGELOG lines:**
    - the config-hash rule and the one gate run;
    - every edit to a masking file re-qualifies;
    - `Runtime(...)`, `gate`, `extract` and `JudgeDetector` need a `MaskedLLM`;
    - a model call outside a run is refused;
    - `received` no longer carries a hash of the raw document;
    - non-UTF-8 and binary documents are refused;
    - one signed audit row per model call (it roughly doubles the audit rows and ties model calls to the audit sink being up, which is new for the run loop);
    - `extract` returns placeholders and offers no put-back, and Intake cannot use it for bank details;
    - the README "not masked" list, including names with a non-ASCII first capital;
    - 12-digit ACCOUNTID numbers are stored, while `Account Number: <12 digits>` is never put back;
    - PHONE is no longer put back;
    - the k1b flag no longer exists as a wrapper downgrade.

## v1.1 rows (each cut item, with its trigger; nothing is dropped silently, lead order 7(3))
| Row | What | Trigger |
|---|---|---|
| V1 | Approval-card display of put-back fields (C1 D7) | the K8 card command exists |
| V2 | Per-field `restorable` paths in a contract (C1 D7); key refused at load until then | a contract needs an identifier restored in one field and not another |
| V3 | Detector-model redactor backend, and the shared contract suite with it | a client document type the patterns miss |
| V4 | Plain account numbers of 8-9 or 17+ digits with no keyword, digits glued to letters, JSON numbers (ACC-1a, ACC-1b, ACC-3) | before any pilot with real client data, or Intake registers the field |
| V4b | NAME patterns for names whose first letter is a non-ASCII capital (NAME-NONASCII-INITIAL) | before any pilot with real client data whose names start with such a letter |
| V5 | Registry-load lint of prompts and contract text (C1 "F3 lint table") | a client or operator edits prompts or contracts |
| V6 | `forged_mark` refusal of placeholder-shaped text in documents, in place of main's escape | a test shows an escaped placeholder confusing a reader or a restore |
| V7 | The gate compares golden answers after put-back (C1 F9) | a golden set needs raw expected values |
| V8 | A declared document encoding instead of refusing non-UTF-8 | a client's documents are not UTF-8 |
| V9 | Put-back for `extract` (a restore handle for format-checked fields) | Intake or a client moves extraction onto core `extract` |
| V10 | PHONE put-back with a phone-shape grammar (not all digits) | a contract needs a phone number back |

## PENDING LEAD (each with my recommended answer; final under order 6(g) unless the lead replies)
1. **Build on main's run map; do not port the C1a engine** (major, redaction path). Recommended: (b) build over main's `runmap`. Reversible before P5c-1 merges.
2. **egm-draft for P5c was not run** (orders 6(e), 8(3)). Recommended: the reviews stand in for it (order 19 G accepted Sonnet-drafted tickets for the frozen ones). If the lead wants the draft, it runs on items 1, 15, 16 and 17 only.
3. **Refuse non-UTF-8 text documents** (C1 F13). Recommended: refuse in v1; V8.
4. **Keep one audit row per model call** (C1 D8). Recommended: keep.
5. **The cuts V1, V2, V5, V6, V7** (order 7(3)). Recommended: yes.
6. **One `RedactionError` base** with the coded subclass `RedactorRefusal`. Recommended: yes.
7. **Code mapping** `LookalikeCopy` -> `self_check_failed`, `TooDeep` -> `unsupported_input`, `InputTooLarge` -> `too_large`. Recommended: yes.
8. **ACCOUNTID stays a stored kind** (money-adjacent; both directions now named). A bare 12-digit bank number is stored and can be put back. `Account Number: <12 digits>` (a cloud id included) becomes BANKACCT and is never put back; a person looks (ACC-12b). Recommended: keep, state it in the README, pin ACC-12 and ACC-12b.
9. **Wrapper order with P4b1's `MeteredLLM`** (`tickets/P4b1.md:219`, `:228`): `MaskedLLM(MeteredLLM(raw))`. Recommended: yes, if PENDING LEAD 23 keeps the wrapper.
10. **Read tools keep getting restored arguments of stored kinds** (`agent_loop.py:295`, `tools.py:1178`). Recommended: keep; restore goes through `redactor.restore` (T4-03).
11. **`RESTORE-1` marker form** (P2d L5). Recommended: the builder decides after reading the merged P2d-2; M39 and T4-02 are written then.
12. **Depends-on P5b5:** the real needs are P5a and P5b3 (P5b3 is now in the list). Recommended: narrow the plan row to "P2d-2, P5a, P5b3".
13. **`EXCEPTIONS` row date** `review_by` 2027-01-31. Recommended: yes.
14. **Hot-file list:** add P5c to `app.py` (A9 F6) and `extract.py`, and P5c-4 to `tools.py` after P2a, P2d and the look-alike design. Recommended: yes.
15. **One masking mode per input class** (R1-COR-1, the Blocker; redaction path). The wrapper re-masks in trusted mode and checks the body; escaping happens once at each raw entry point; `extract` gains one. Recommended: yes. Reversible before P5c-2 merges. Confidence 80%.
16. **Computed masking fingerprint; delete the hand pin and its start-up refusal** (R1-ADV-7). This reverses the C1 version-pin form and P2d's "pins after P2d-2" section. Recommended: yes. Reversible. Confidence 75%.
17. **PHONE out of the default stored kinds** (R1-COR-2, money-adjacent). Recommended: yes, with V10. Alternative: a Luhn or phone-shape rule in `runmap.storable_original`. Reversible. Confidence 75%.
18. **Delete the `premasked` wrapper and its operator downgrade** (R1-ADV-17a). Recommended: yes. Confidence 85%.
19. **`received` keeps its place and drops the raw hash** (R1-ADV-11, R1-COR-5). Recommended: yes. Confidence 85%.
20. **Core `extract` gives no put-back in v1; Intake cannot use it for bank details** (R1-ADV-12; the owner can see this). Recommended: state it, row V9. Confidence 80%.
21. **NAME patterns: no `isupper` callback; names with a non-ASCII first capital are not masked** (R1-COR-7; a limit the owner can see). Recommended: yes, row V4b. Confidence 70%.
22. **A model call outside `run(...)` is refused** (R1-ADV-17e). Recommended: yes. Confidence 80%.
23. **P4b1 `MeteredLLM` vs P4c item 15** (a coupling that is not P5c's to decide). The P4c and P4b1 round-2 resolves (INFORM 22, 23) both recommend one `MeteredLLM` wrapper. Recommended: the lead confirms before P5c-3.

No new PENDING LEAD item was added by this revision beyond 15-23.

## UNVERIFIED (not read or not run by me)
- Every test row, mutant and fail-before claim.
- Every name from P1, P2d-2 (`LookalikeCopy`, the RESTORE-1 marker, its look-alike module name), P5a (`codes.py`, `OWN_CODES`, `RESERVED_FOR`), P4b1 and P4c, until those packages merge.
- The design section 9 table, and the claim that ACC-1c fails on `748849c`.
- NAME-NONASCII failing before, and NAME-DECOMPOSED passing via the NFKC second pass (both by reading only).
- The effect of item 5 on the existing redaction tests.
- The F10 probes on Python 3.12 and 3.14 and on the real class.
- How many FakeLLM recordings must be renamed.
- Whether golden expected files hold placeholders.
- The T2-P time budget.
- Intake's `mask.py`.
- Whether any MANIFEST row covers `guard/redactor.py`.
- Whether `demos/ask-your-data` can go behind the wrapper.
- P1m's runner arguments.
- Whether `tools.py` importing `guard/redactor.py` creates an import cycle.
- Whether an install without `.py` sources exists (fingerprint read).
- The benign refusal rate of the body check (T2-15c).
- That `redact_text` masks a known original reappearing in a later leaf on pass 2 (by reading).
- Which existing tests rely on stored phones.
- `input_ref` files whose path does not contain "golden".
- That no test reads `received.inputs_hash` (the resolve grepped `src/` only).
- The resolve's "20 files" for `config_hash`/`qualified.jsonl` (I get 14 or 21 depending on the pattern).
- The C1 ticket text and the C1a line numbers (carried from revision 1, not re-read).

## Rules and sources cited
- **Plan:** plan-v3 sections 3, 4 (rules 3, 4, 5, 8, 9, 10), 5 (row redactor), 6 (row P5c, note 7) and 9; amendments A4, A5, A9 F6.
- **Lead orders:** 6(e), 6(g), 7(3), 8(1), 8(3), 8(5), 11(1), 11(5), 15, 16(5), 17, 19 A, C and G, 20 items 2, 4, 5 and 6.
- **Reviews:** `reviews/P5c-round1-adversarial.md`, `reviews/P5c-round1-correctness.md`, `reviews/P5c-round1-resolve.md`.
- **C1:** `studio-notes/C1-ticket-v3.md` D1-D12 and `C1-ticket-v3-FROZEN-amendments.md` F1-F14.
- **Other tickets and designs:** `tickets/P2d.md` rev 6 (:344, Rollback, L1, L5); `tickets/P1.md` rev 16 (`FOLD_VERSION`, the fold modules); `tickets/P4b1.md:219`, `:228`; `tickets/P4c.md` lines 15-16 and 266; `designs/lookalike-leak.md` draft 11 sections 8, 9, 9b and 11.
- **Lead notes:** `questions-for-lead.md` INFORM 22, 23 and 27; `handover/ledger-seed.md` rows `BL-core-c1a-*`.
