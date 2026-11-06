# Package ticket P5c: the redactor kind, the masked model wrapper and safe put-back (C1a to C1d plus C1f), four pull requests (P5c-1 to P5c-4). DRAFT revision 3

**Revision 3, written 2026-11-06, started 03:44 UTC (09:14 IST; IST = UTC+5:30), by a ticket-revision author (lead order 20 item 6; orders 21-26 read and applied where they touch P5c). It applies every decision of `handover/reviews/P5c-round2-resolve.md`: 22 decision rows covering the 30 round-2 finding ids (R2-ADV-1..10, R2-COR-1..20) plus the resolve's own finding RES-1. No decision was left out; see the CHANGELOG (revision 2 -> revision 3).** Revision 2 was written 2026-11-06 03:06 UTC (08:36 IST); revision 1 at 02:42 UTC (08:12 IST). Text only: no code, no pull request, no test run, no sub-agent. **Path class: redaction, money-adjacent. This ticket is on the money and redaction path.** It decides which parts of an invoice reach a model (bank account numbers included) and which values are put back into a plan that can lead to a payment. **Extended review: result review has no round cap; ticket review is capped by order 20 item 6** (R2-COR-19). This is Tier A (plan-v3 section 4 rule 3). **Review round 3 is next.** Order 20 item 6 caps ticket review at 3 rounds counting from round 1. A redaction package whose last round had no Blocker and at most 2 Majors may take one more round. Round 2 had 1 Blocker and 14 Majors, so round 3 is allowed, and a round 4 only if round 3 has no Blocker and at most 2 Majors. The result review of the built code keeps the two-clean-rounds stop rule (order 16(5)).
> **Build notes win.** Revision 3 is frozen text (no round 4: round 3 had 9 Majors). Where a build note BN-1 to BN-18 (from `handover/reviews/P5c-round3-resolve.md`, copied into the section "Build notes (round 3 resolve)" at the end of this ticket) differs from the revision 3 text, the build note wins. Lead-order notes BN-19 to BN-21, appended after them in the same section, win the same way (BN-21: P5b1 PENDING LEAD 27 relay, lead order 41 item 91). NEEDS LEAD 34, 35 and 36 (money and redaction) are open: until the lead answers, the builder takes the default each build note names. The CHANGELOG sections are history, not instructions. Find every code cite by its name at the rebased head, not by its line number (BN-17).

**What is not verified, first.**
- I ran no test and no mutant. Every new test row, every mutant and every "fails before" argument below is a hand argument until the evidence runner reports.
- **Revision 3 (this author):** I ran no probe. I re-read, with `git show 124258b:<path>`, every NEW code cite that revision 3 adds (listed in the CHANGELOG). The resolve's one run (the Blocker leak reproduced with `python3 -I`) is the resolve's evidence, not mine. The new `_bank_context` clause (item 5(ii)) is argued by reading `redact.py:107-113` and `:925-941`, and was NOT run by anyone.
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

## CHANGELOG of this ticket (revision 2 -> revision 3)

One line per resolve row; the finding ids are in brackets. Every code cite added here was re-read by me at `124258b`.

**The Blocker (money and redaction path):**
1. **No new capturing group in any redact pattern** [R2-COR-1 Blocker, R2-ADV-1]. Revision 2's "named group for the keyword" would have made `_mask` (`redact.py:929`, `original = next((g for g in m.groups() if g is not None), m.group(0))`) take the KEYWORD as the value and leave the digits in clear (the resolve reproduced this with the real module: output `bank <BANKACCT_1>: <8 digits>`, the digits in clear). Now `_bank_context` (`redact.py:107-113`) gains one clause that reads the text BEFORE the digits group: `_ACCT_STRONG.match(m.string, m.start(), m.start(1)) is not None`. `m.groups()` does not change. ACC-2 now asserts the digits are gone, the keyword is kept and the map holds exactly one BANKACCT entry equal to the digits. New mutant M50 puts the group back. Item 5 gains the rule sentence "a pattern's first capturing group is the value; never add a group before it".

**Cut (surface removed):**
2. **`_map_of` is no longer used in `agent_loop.py`** [R2-ADV-2, R2-COR-2, R2-COR-3; PENDING LEAD 24]. The run loop keeps its own `RunMap` (`agent_loop.py:352`) and every plain-map use, and seeds the session with it: `llm.run(run_id, principal, seed=rmap)`. `restore` is no longer listed as a caller (it takes a plain map). T1-17 is complete in P5c-1.
3. **Non-text content blocks are refused, not masked** [R2-ADV-7; PENDING LEAD 31]. New row T2-18, mutant M55.
4. **T3-03 and T3-15g leave the reverse-check list** [R2-COR-7]: `extract` masks on its own, so a pass-through wrapper passes them.

**Changed:**
5. **`check` uses the sweep's own rule** (`_Redactor.sweep`, `redact.py:1011`; `_sweep` :1202; `_replace_standalone` :1223): any copy of a secret, only standalone copies of an identifier [R2-ADV-3, R2-COR-8; PENDING LEAD 25]. T2-15c is now pass/fail; new mutant M52.
6. **The fingerprint also covers `tools.py` and the masking values of `defaults`** (`STORED_KINDS` :108, `MAX_REDACT_CHARS` :38, `CUT_MARGIN` :44, `REDACT_BUDGET_S` :49, `MAX_BUNDLE_CHARS` :40) [R2-ADV-4, R2-COR-9; PENDING LEAD 26]. New formula, T1-02 extended, new mutant M51. Rollback and CHANGELOG lines now say that P5c-1, P5c-3 (if it edits a listed file) and P5c-4 each change the fingerprint.
7. **Where `config_hash` gets the fingerprint:** `guard.redactor.fingerprint_of(kind)` [R2-ADV-5, R2-COR-18]; no signature change; merged after P4c-2's edit of the same function.
8. **PHONE removal told truthfully** [R2-ADV-6, R2-COR-10; PENDING LEAD 30]. Revision 2's Rollback sentence "phone numbers saved before it are still put back" was FALSE: the kind filter (`agent_loop.py:284`, `:295`) drops them. A config naming PHONE is refused at load (`config.py:256`). Two CHANGELOG lines; new row T4-10.
9. **One intent-only `outbound` row per call; CHANGELOG wording fixed** [R2-ADV-8; PENDING LEAD 33]. Intent-only rows already exist on main (`limits.py:50`, `k1b/audit_sink.py:35`).
10. **NAME keeps the wide letter class; the width is stated and pinned** [R2-ADV-9, R2-COR-17; PENDING LEAD 32]. New row NAME-CAPS.
11. **Count line reworded** [R2-ADV-10, R2-COR-15]: `test_p5c4_putback.py` holds 11 rows; T4-04 is in `test_c1_acceptance.py`.
12. **`_screen` catches the wrapper's refusals for both callers** (`agent_loop.py:310-316`, callers `:387` and `:520`) [R2-COR-4]. New row T3-12b, mutant M53.
13. **`extract`'s retry text relies on P5b3's closed text** (`tickets/P5b3.md:192-193`) [R2-COR-5]. New rows T3-03c, T3-03d, with a fallback if P5b3's merged text still echoes input.
14. **Signatures decided** [R2-COR-6; PENDING LEAD 29]: `extract(..., principal, ...)`, the gate's run ids and code identity `"gate"`, `cli gate` builds its audit with `k1b.audit_sink.build_audit` (`k1b/audit_sink.py:59-72`), audit down means the gate is never GREEN (new row T3-10b), and `MaskedLLM.redactor` is a public read-only property.
15. **Brought up to orders 22 and 24** [R2-COR-11; PENDING LEAD 27, 28]: PENDING LEAD 9, 17 and 23 are ANSWERED; `Runtime` requires exactly `MaskedLLM(MeteredLLM(raw))` and P5c-3 replaces P4c-2's check (new row T3-06b, mutant M54); order 22 item 27's two rows T4-11 and T4-12; order 22 item 24 recorded as a coupling.
16. **Strict UTF-8 in the run loop and the gate, with state, reason and order** [R2-COR-12]. New row T3-05b.
17. **Stale cites fixed** [R2-COR-13]: `tickets/P4b1.md:249`, `:258`; the "Not a wrapper on `deps.llm`" coupling is deleted (that text is gone from `tickets/P4c.md`, which now wraps `deps.llm` once at `:8` and `:177`).
18. **k1b's thread carries the run context** [R2-COR-14]: `k1b/loop.py:104` starts a plain `threading.Thread(target=work)`; it becomes `contextvars.copy_context().run(work)`. New row T3-11b.
19. **`MODEL_CALLERS` cite `:55-65`** (was `:55-60`) [R2-COR-16]. The `TooDeep` `:98` part is CONTESTED and kept: `git show 124258b:src/hadavin_sdk/guard/runmap.py` has `class TooDeep(RedactionError):` at line 98 (re-read by me).
20. **The "Extended review" field reworded** [R2-COR-19].
21. **T3-16 wording** [R2-COR-20]: at `124258b` the 11 paths with "golden" in the name are 10 input documents plus `tests/fixtures/golden/test-agent.jsonl` (re-counted by me with `git ls-tree`).
22. **One strict decode helper `decode_document`** [RES-1, the resolve's own finding]: revision 2 had `extract` call `redactor.mask` on `bytes`, but `mask` takes `str`. The wrapper, `extract`, the run loop and `evals.py` all call the one helper. T3-03e is a case inside T3-05, not a new row.

**Also applied from orders 21-26:** order 26 item 2 (a mutant's `expect` is a distinctive fragment of the intended failing line, never the killer's name; Mutation plan) and order 25 item 4 (new tests must also run on Windows; Evidence).

**Counts, recomputed from this file:** 91 test rows (16 + 14 + 17 + 32 + 12), 92 with the `perf` row T2-P; 4 strict-xfail records (unchanged); 50 mutants (19 + 15 + 11 + 5), each with a named killer. PENDING LEAD 24-33 are new.

## CHANGELOG of this ticket (revision 1 -> revision 2)

**Cut (surface removed; each closes a round-1 finding by deleting, order 8(1)):**
1. **The `MaskedLLM.premasked` wrapper and the downgrade of its refusal to a warning** (operator flag `--i-know-data-is-already-masked`, `cli.py:120`; rule-id suffix `;premasked[;unverified]`). Also cut: T2-12, the premasked part of T3-07(d), M27. *Reason:* a flag that turns a masking refusal into a warning is a way around the mandatory wrapper (R1-ADV-17a). Placeholders pass the trusted re-mask unchanged, so masking k1b's bundles a second time changes nothing (`judge.py:68-69` comment). `k1b/loop.py` now uses `MaskedLLM.of` like every other caller. The flag keeps its one existing meaning: skip k1b's own bundle masking. The wrapper still masks. (PENDING LEAD 18.)
2. **`RegexRedactorSettings`.** *Reason:* it has no fields in v1. `backends/table.py:388` already wires a kind that has no settings with the base `KindSettings` (`"fake": Entry(KindSettings, ...)`). A new name would also sit next to the existing `RegexSettings` (:92) and could be mistaken for it (R1-ADV-17d).
3. **The shared contract suite `tests/contracts/kinds/redactor.py`.** *Reason:* there is one backend. V3 writes the suite when the second backend is built (R1-ADV-17d).
4. **The "mask messages and documents as ONE joined text, split back after" step and its separator.** *Reason:* a split that does not line up had no defined behaviour. Views and NUL cleaning can change the separator. The cap and the time budget grew with the length of the conversation (R1-ADV-2). It is replaced by two passes over the leaves (item 7).
5. **The hand-pinned `REDACT_SOURCE_SHA256`, its start-up `ConfigError`, T1-03, M1, and the "revert P2d and P5c-1 together" lock in Rollback.** *Reason:* the pin covered only `redact.py`, while masking also depends on `runmap.py`, P1's fold and P2d's check (R1-ADV-7). #59 has already changed `redact.py`'s hash once, which shows how easily a hand pin breaks. It is replaced by a fingerprint computed at import over every masking source file (item 4). (PENDING LEAD 16.)
6. **`__copy__` and `__deepcopy__` on `MaskSession`, and mutants M4, M5 and M40.** *Reason:* probe (a) shows that a raising `__getstate__` alone makes F10's whole list raise, so M4 and M5 could never be killed (R1-ADV-9). M40 mutated a card-restore call that does not exist (no card code calls restore; V1 is cut).
7. **T4-06 (restore after close raises `session_closed`).** *Reason:* it contradicted the execute-time seam, which runs after the run's session has closed and reads the stored map (R1-ADV-4). `restore` now takes a plain map (item 8).
8. **T3-08 and the second module list of T3-07.** *Reason:* `guard/producers.py:55-65` `MODEL_CALLERS` (cite corrected in revision 3) already lists the modules that call a model, so a second list would be a second registry of one fact (R1-ADV-5).
9. **The `adhoc:<uuid4>` context for a model call made outside `run(...)`.** *Reason:* such a call silently lost its put-back and its audit link (R1-ADV-17e). A call outside `run(...)` now raises `SessionClosed` (code `session_closed`, no new code). `gate` and `extract` open their own `run(...)`. (PENDING LEAD 22.)
10. **The `str.isupper()` check after a NAME match.** *Reason:* it needed a callback that the plain (kind, regex) table, the fold scan and `redact_many` do not have (R1-COR-7). The cost is that names whose FIRST letter is a non-ASCII capital (for example a name starting with `Ø`, `É` or `Ł`) are not masked; they go on the README "not masked" list and get row NAME-NONASCII-INITIAL (strict xfail). (PENDING LEAD 21.)
11. **The raw-document hash in the `received` audit event, with no reordering.** *Reason:* revision 1 said "hash the masked body" but `received` is written before masking (`agent_loop.py:349` vs `:367`). Moving the masking earlier would change audit order and the too-large path (R1-ADV-11, R1-COR-5). `received` stays the first event (pinned by `tests/test_s5_runtime.py:137`) and simply carries no `inputs_hash`. No `src/` code reads `received.inputs_hash` (resolve, by grep; not re-run by me). The wrapper's per-call `outbound` event records the hash of what was sent. (PENDING LEAD 19.)
12. **PHONE storage (PENDING LEAD 17; answered yes by order 22 item 27).** *Reason:* a bare 16-digit card number, or a bank number of 10-11 or 13-16 digits with no bank word, is masked as PHONE. PHONE is a stored kind (`defaults.py:120`), and its grammar `[0-9 ()+.\-]{5,32}` (`runmap.py:228`) accepts plain digits, so these numbers could be put back into a plan (R1-COR-2). The fix removes one line from the default `STORED_KINDS`. *Rejected alternative:* a Luhn rule or a phone-shape grammar in `runmap.storable_original`, which is more design and sits in P2d's file.

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
- R1-COR-9 (P4b1 has no wrapper): `tickets/P4b1.md:249` reads "P4b1-b: the wrapper around model calls (`MeteredLLM`)", and `:258` gives `MeteredLLM(inner: LLM, limits: Limits, routes: dict[str, Route])` (lines re-read for revision 3; revision 2 cited :219 and :228, which have since moved). The dependency stays, and the wrapper is now named.
- R1-COR-15 (Python version): `python3 --version` prints `Python 3.13.18`.

## Words used in this ticket (defined once)
- **mask**: replace a protected value (an e-mail address, an account number, a key...) with a **placeholder** such as `<EMAIL_1>` before text goes to a model. **put back** (restore): replace a placeholder with its original value again, in code, after the model has answered.
- **escape**: turn placeholder-shaped text that came from OUTSIDE (for example a `<EMAIL_9>` typed into a document) into a harmless look-alike (`‹EMAIL_9›`), so nobody mistakes it for a real placeholder. `runmap.redact_untrusted` escapes and masks; `runmap.redact_text` only masks (issued placeholders and `<<TOOL RESULT` markers pass unchanged).
- **run map**: on main, the one placeholder-to-value dictionary of a run (`guard/runmap.py:384` `RunMap`, a `dict` subclass). **mask session** (`MaskSession`, new): the object this package puts around the run map. It holds the map in a private slot (since revision 3 that map is the run loop's own object, passed in as a seed, item 3), cannot be copied, and can be closed.
- **redactor kind**: the replaceable part, chosen by configuration, that masks text (plan-v3 section 5, row "redactor"). Its default is `regex` (the patterns of `guard/redact.py`).
- **masked model wrapper** (`MaskedLLM`, new): the only object through which core code may call a model. It re-masks every message and document of a call with the run's session and checks the result before the inner model sees it.
- **stored kinds**: the kinds of identifier whose originals may be saved and put back. Today (`defaults.py:108-122` `STORED_KINDS`) they are ACCOUNTID, ADDRESS, ARN, AZURERESOURCE, EMAIL, GCPRESOURCE, HOSTNAME, IPV4, IPV6, MAC, NAME, PHONE and TENANT. P5c-4 removes PHONE (PENDING LEAD 17, answered yes by order 22 item 27), leaving 12. Every secret kind, and the regulated kinds IBAN, CREDITCARD, BANKACCT, BANKCODE, SSN, AADHAAR and PAN, is masked but never stored and never put back. A regulated number that is MASKED AS a stored kind is stored. Two cases: a bare 12-digit number is ACCOUNTID (PENDING LEAD 8), and today a bare 10-11 or 13-16 digit number is PHONE (until P5c-4).
- **fingerprint**: one string that names the masking code and the masking settings exactly (item 4); it is part of an agent's config hash.
- **text leaf**: a piece of a model call that is plain text: a `str` message `content`, the `text` of a `type == "text"` block, the text of a `tool_result` block, or a string inside a `tool_use` input. Only text leaves are masked (item 7).
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
- **Path class:** redaction (personal data before the model) and money-adjacent (bank numbers on invoices; values put back into plans an executor may act on). **Extended review: result review has no round cap; ticket review is capped by order 20 item 6** (R2-COR-19). The lead verifies at most one redaction pull request at a time (plan-v3 section 3).
- **Depends on (merged first):**
  - **P2d-2** (rev 6, FROZEN): `LookalikeCopy` (a `RedactionError`) must exist for T2-14 and T3-15. P2d's module joins `MASKING_SOURCES` (item 4). P2d rev 6's section "How P5c rebases on this" (`tickets/P2d.md:344`, "P5c pins the `redact.py` hash after P2d-2") and its Rollback lock fall away if PENDING LEAD 16 is accepted. The lead notes this in P2d's build notes.
  - **P2d-2b** before P5c-3. Both edit `runtime/agent_loop.py` (P2d-2b at the `error_reason` call, design section 8).
  - **P1a and P1b**: P1's fold modules (`guard/textnorm.py`, `guard/_confusables.py`) and `FOLD_VERSION` enter `MASKING_SOURCES` and the fingerprint (item 4).
  - **P5a** before P5c-1. P5a's discovery test fails any pull request that adds its own exception class without an `OWN_CODES` row, and P5a reserves `session_closed` for P5c (`tickets/P5a.md`, item "The sixth code `session_closed`").
  - **P5b3** before P5c-3. It rewrites `extract.py:57-64` (`tickets/P5b3.md:192-193`), lines P5c-3 also touches (R1-COR-11). P5c relies on P5b3's closed retry text: "error type names, or the code and a `position` fact" (R2-COR-5; fallback in the `extract.py` entry under Files).
  - **P5b5** (plan-v3 row P5c, "P2d, P5b5"): kept until the lead answers PENDING LEAD 12. Honest reason: P5c needs only P5a and P5b3, and I found no file that P5b4 or P5b5 shares with P5c.
  - **P4c-2** before P5c-1 (`registry.py`) and before P5c-3 (`runtime/agent_loop.py`). P4c's T8 table of model-calling modules reads `producers.MODEL_CALLERS` (T3-08 is cut), and P5c-3 marks those rows "through `MaskedLLM`". Three overlaps, each settled by rebasing P5c on the merged P4c-2 (P4c is frozen, so its text is not edited; the lead notes them in P4c's build notes):
    - **`config_hash`:** P4c-2 excludes `alert_to` from the agent dump (`tickets/P4c.md:59`, `:180`(c)); P5c-1 adds its `masking` key after P4c's exclude (item 6). T1-04 asserts both.
    - **The `Runtime` check:** P4c-2 makes `Runtime.__init__` refuse a non-`MeteredLLM` (`tickets/P4c.md:190`(i)). **P5c-3 REPLACES that check** with the two-layer check of item 7 and changes P4c's `self.llm.scope(...)` to `self.llm.inner.scope(...)` (PENDING LEAD 27).
    - **`_screen`:** P4c-2 edits it (`tickets/P4c.md:190`(e); it raises a private `_RunEnded(run)` that `handle` catches once, `tickets/P4c.md:13`). P5c-3 adds its catch inside `_screen` on top of that (R2-COR-4).
  - **P4b1-b** (`MeteredLLM`, `tickets/P4b1.md:249`, `:258`) before P5c-3. The masked wrapper sits OUTSIDE the metered one, `MaskedLLM(MeteredLLM(raw))`, so the meter counts the masked body (PENDING LEAD 9, ANSWERED by order 22 item 22: ONE `MeteredLLM` on `deps.llm`). `MeteredLLM.__getattr__` delegation (P4b1-b) is what lets tests read `rt.llm.inner.calls`; `MaskedLLM` deliberately has none. (Revision 2's coupling "Not a wrapper on `deps.llm`" is deleted: that text is no longer in `tickets/P4c.md`, which wraps `deps.llm` once, `:8`, `:177`.)
  - **P6a (order 22 item 24):** P6a-2 must not merge before P5c, and P6a's cuts rely on P5c's T1-12 and the `Runtime` check. **So neither T1-12 nor the `Runtime` check may be cut in a later P5c revision.**
  - **Merge order (order 20 item 4):** P5c comes after the lead's chain (P1m, P1a, P1b, P3a and P4d, P2a-1, P2d-1, P2d-2, P4a). Order 20 item 2 is the standing S0 EXIT for "P5c later", effective once P5c's freeze and its build-start review are done. Inside P5c the order is P5c-1, P5c-2, P5c-3, P5c-4.
  - **Hot files (plan rule 10, A4, A9 F6, order 17):**
    - `config.py`: P4b1, P5b3, P5c, P6a;
    - `registry.py`: P4c, P5b3, P5c;
    - `cli.py` and `backends/table.py`: P5b3, P5b4, P5c, P6b2, P6a;
    - `tests/test_lockin_guard.py`: P4d, P5c, P6b2, P6a;
    - `runtime/agent_loop.py`: P4c, P2d-2b, P5c;
    - `app.py`: A9 F6 lists P6a and P6b2; **P5c-3 also edits it** (PENDING LEAD 14);
    - `extract.py`: P5b3, P5c;
    - **`tools.py`: P2a, P2d, the look-alike design, then P5c-4** (order 17; P5c-4 rebases after them). From P5c-1 on, `tools.py` is also a fingerprint input (item 4): P2a, P2d and the look-alike design merge before P5c-1, so they cost no extra gate run, but **every later `tools.py` edit re-qualifies every agent** (fails safe). The lead adds this to plan rule 10's note;
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
    - **its version and source-hash pin (`REDACT_SOURCE_SHA256`, start-up refusal `:435-439`): replaced by the computed fingerprint** (CHANGELOG rev 2 cut 5).
  - **NOT taken from C1:**
    - the `forged_mark` refusal of documents (main escapes instead; V6), although `forged_mark` remains the code of the body check (item 7);
    - F9's `evals._restore_all` (V7);
    - D7's approval-card display and per-field `restorable` paths (V1, V2);
    - F6's operator downgrade (CHANGELOG rev 2 cut 1).
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
     - **`check` (changed in revision 3, R2-ADV-3, R2-COR-8; PENDING LEAD 25)** raises `RedactorRefusal("self_check_failed")` when a session original of 4 or more characters is left where `_Redactor.sweep` would have masked it, and `RedactorRefusal("forged_mark")` if `text` holds a placeholder that the session did not issue. **It uses the sweep's own rule, not a new one** (`redact.py:1011` `sweep`, `_sweep` :1202, `_replace_standalone` :1223): any copy of a SECRET-kind value, but only a STANDALONE copy of an identifier. So a stored made-up name inside a longer word is NOT a refusal, because the masker itself leaves it alone by design.
       - **Effect.** The wrapper re-masks with the same map first, so `check` fires only when masking was skipped or stubbed (the purpose of R1-ADV-8).
       - **Why not refuse the longer word:** it would stop legitimate runs (a false abstain, a person looks for nothing) and gains no safety: the same text would be sent anyway if `check` did not exist. It is UNVERIFIED that P2d-2's look-alike check does not itself refuse the same benign text.
     - **Unexpected errors:** any exception inside `mask` or `check` that is not a `RedactionError` becomes `RedactorRefusal("internal")` (C1 D9).
  3. **`MaskSession` (P5c-1) and rule F10.**
     - **Shape.** It is neither a `dict` nor a `Mapping`. It holds a private `RunMap` (`__slots__ = ("_map", "_closed", "_lock")`).
     - **Methods:** `storable(kinds) -> dict[str, str]`, `issued(mark) -> bool`, `counts() -> dict[str, int]`, `close() -> None`, and use as a context manager (`__exit__` closes). `repr` shows only the count.
     - **Copy refusal: only `__getstate__` raises `TypeError`** (`__copy__` and `__deepcopy__` are cut, CHANGELOG rev 2 cut 6). After `close()`, every method except `closed` raises `SessionClosed`.
     - **The seed (new in revision 3, R2-ADV-2, R2-COR-2, R2-COR-3; PENDING LEAD 24).** A session is built over a `RunMap` it is given (the run loop's own, see item 7 `run(..., seed=...)`), or over an empty one.
     - **The module-private accessor `_map_of(session) -> RunMap`. Its callers are exactly the `regex` kind inside `guard/redactor.py`, pinned by an AST test (T1-17), complete at P5c-1.** `restore` is not a caller: it takes a plain map (item 8). **`agent_loop.py` does not call `_map_of` at all (cut):** the run loop keeps building its own map, `rmap = runmap.RunMap(mapping or {})` (`agent_loop.py:352`), and keeps every plain-map use it has on main unchanged: `:363`, `:367`, `:379`, `:382`, `:454`, `:468`, `:475-476`, `:489`, `:498`, `:502` and `:645-648` (every line re-read by me at `124258b`). It hands that same object to the session as the seed.
     - **State plainly:** F10 protects the SESSION object: it cannot be copied, pickled, or used after close, and a late call through it is refused. **The run loop still holds the plain map for its run, as on main.** The map never leaves the process except to the store, and then only for stored kinds. `tools.py` keeps taking a plain map for `invoke` and `prepare_output`.
     - **Rule F10, word for word ("F10 / D5 amendment" item 1):** "a MaskSession cannot be pickled (all protocols), copied or deep-copied, and direct calls to __reduce__ and __reduce_ex__ (0..5) raise TypeError. The mechanism may be __getstate__/__copy__/__deepcopy__ (the builder removed __reduce__ because object.__reduce__ calls the raising __getstate__). A test must assert exactly this list, including the two direct calls."
     - **Probes.**
       - Revision 1's probe (a stand-in with all three hooks): every item on the list raised, for a `__slots__` class AND for a `dict` subclass. But `dict(o)` copied the `dict` subclass's values without error, which is why the session is not a `dict`.
       - Revision 2's probe (a): `__getstate__` alone is enough.
       - T1-05 asserts F10's list plus `dict(session)` and `{**session}` raising `TypeError`.
       - Python 3.12 and 3.14: UNVERIFIED.
  4. **`regex` kind and the computed fingerprint (P5c-1; changed, CHANGELOG rev 2 cut 5; PENDING LEAD 16).**
     - **Construction:** `RegexRedactor(name="regex", version=REGEX_VERSION)`, with `REGEX_VERSION: Final = "4"`. Settings: the base `KindSettings` (CHANGELOG rev 2 cut 2).
     - **The fingerprint, computed ONCE at import (formula changed in revision 3, R2-ADV-4, R2-COR-9; PENDING LEAD 26):** `RegexRedactor.FINGERPRINT = "regex@" + REGEX_VERSION + ":" + FOLD_VERSION + ":" + sha256(LF-normalised bytes of MASKING_SOURCES, in list order, + b"\0" + repr(MASKING_VALUES).encode("utf-8"))[:16]`.
     - **`MASKING_SOURCES`** = `guard/redact.py`, `guard/runmap.py`, `guard/redactor.py`, P1's `guard/textnorm.py` and `guard/_confusables.py`, P2d's look-alike module, and **`tools.py`, the whole file** (new: it holds `prepare_output`, `tools.py:936`, and `redact_layered`, `:976`, which mask tool results). P2d-2's module name is UNVERIFIED until it merges; the builder reads it from the merged code.
     - **`MASKING_VALUES` (new)** = a tuple of the `repr()` of these `defaults` values, in this order: `STORED_KINDS` (`defaults.py:108`), `MAX_REDACT_CHARS` (:38), `CUT_MARGIN` (:44), `REDACT_BUDGET_S` (:49), `MAX_BUNDLE_CHARS` (:40). The VALUES are hashed, not `defaults.py`, so an unrelated constant does not re-qualify every agent. Why it is needed: `config_hash` dumps with `exclude_defaults` (`registry.py:105-118`), so a changed default re-qualifies nothing on its own.
     - **Where `config_hash` reads it (new, R2-ADV-5, R2-COR-18):** a module function `guard.redactor.fingerprint_of(kind: str) -> str`. It looks the configured kind name (`self.config.backends.redactor.kind`) up in a module dict filled at import, `{"regex": RegexRedactor.FINGERPRINT}`. An unknown kind raises `ConfigError`. No redactor object is handed to `Registry`, so `config_hash` keeps its signature. T3-18 reuses `fingerprint_of`.
     - **Each of P5c-1, P5c-3 (if it edits a listed file) and P5c-4 (`redactor.py`, `tools.py` and `STORED_KINDS`) changes the fingerprint.** See Rollback.
     - **Unreadable file:** a listed file that cannot be read makes the import raise (fails closed). Whether an install without `.py` sources exists anywhere is UNVERIFIED.
     - **No start-up comparison and no hand pin.** Editing any listed file changes the fingerprint, and through it every config hash, so a new gate run is needed (it fails safe).
  5. **Pattern changes in `guard/redact.py` (P5c-1; design section 9 PL-LK-7 and 9b PL-LK-23).** Lines are `124258b` lines unless marked; P2d-2 moves them. All three changes are covered by the fingerprint (no hand bump of the hash; `REGEX_VERSION` goes from C1a's "3" to "4" once).
     - **(i) PHONE's end.** It changes from `(?![\w.])` (`124258b` :476; `748849c` :483) to `(?!\w|\.\w)`. A 10-16 digit number at the end of a sentence is then masked, while `<digits>.5`, `<digits>.txt` and two runs joined by a full stop are not. UNCHANGED.
     - **(ii) Strong account keywords count as bank context (exact forms; changed, R1-ADV-16, R1-COR-6).** The source is `_ACCT_WORD` (:82: `(?:accounts?|acct\.?|acc\.?|a/c)(?:[ _\-\xa0]?(?:number|num\.?|nbr\.?|no\.?|#))?`).
       - **Rule (new in revision 3):** "a pattern's first capturing group is the value; never add a group before it". Why: `_mask` takes `original = next((g for g in m.groups() if g is not None), m.group(0))` (`redact.py:929`). Revision 2's "named group for the keyword" would have made the keyword the value and left the digits in clear (R2-COR-1, the Blocker; the resolve reproduced the leak with the real module). **Revision 2's mechanism is deleted.**
       - **Mechanism (revision 3): NO new capturing group in any redact pattern.** `_bank_context(m)` (`redact.py:107-113`) gains one clause, OR-ed with its two existing ones: `_ACCT_STRONG.match(m.string, m.start(), m.start(1)) is not None`.
         - `_ACCT_STRONG` is compiled with the BANKACCT flags (`(?i)`, pattern 1 at `redact.py:333-336`) and is anchored at the match start: an optional `bank[ _\-]?`, then one strong form of the table below, then any characters up to the digits.
         - The clause reads only the text BEFORE the digits group (`m.start()` to `m.start(1)`), so `m.groups()` and `_mask`'s `original` do not change.
         - **The second BANKACCT pattern** (`<BANKCODE_n>` then digits, `redact.py:339-349`) starts with `<`, so `match` returns `None` and nothing raises. It already has bank context through `_BANK_CONTEXT`'s `<BANKCODE_\d+>` alternative (`redact.py:93-94`).
         - **Coverage:** `redact_many` and the fold scan share `_mask` (`redact.py:925-956`), so they get the clause with no change.
         - The clause sits where BANKACCT is gated today (`redact.py:939-941`: `_CARD_SHAPE.fullmatch(original) or not (self.bank_near or _bank_context(m))`). By reading only; not run.
       - **The table:**

         | form | suffix (`number`, `num`, `num.`, `nbr`, `nbr.`, `no`, `no.`, `#`) | counts as context? |
         |---|---|---|
         | `account`, `accounts` | with a suffix | yes (strong) |
         | `account`, `accounts` | none | NO (weak: common in logs) |
         | `acct`, `acct.` | with or without | yes |
         | `a/c` | with or without | yes |
         | `acc`, `acc.` | with a suffix | yes |
         | `acc`, `acc.` | none | NO (weak) |

       - **Effect:** `Account No: <6-17 digits>` is masked as BANKACCT with no bank word; the DIGITS become the placeholder and the keyword stays as written (ACC-2 asserts both).
     - **(iii) NAME letters (changed, CHANGELOG rev 2 cut 10).** In the `Dear` form (:447) and the title form beside it (:444), each name part changes from `[A-Z][a-z]+` to `[A-Z][^\W\d_]+(?:-[A-Z][^\W\d_]+)?`. The first letter stays `[A-Z]`. It stays a plain (kind, regex) row, so the fold scan and `redact_many` need no change. As a result, `Dear <first> <last>-<last>` and `Dear Jürgen <last>` are masked whole (probe (b)). Not masked: a name whose FIRST letter is a non-ASCII capital.
       - **The width, in words (revision 3, R2-ADV-9, R2-COR-17; PENDING LEAD 32).** After the first capital, `[^\W\d_]` takes any letter, capitals included. So all-caps names are masked (`Dear MARY <last>`): on invoices, names written in capitals are real names, and narrowing the class to exclude `A-Z` would leak them. The cost is over-masking: `Dear ALL` and `Dear JohnSmith` each become one NAME placeholder (the resolve's probe matched all three whole). That fails safe: a stored NAME that nobody puts back. Row NAME-CAPS pins all three examples.
  6. **Config hash (P5c-1; source named in revision 3).** `registry.config_hash` (`registry.py:105`) ALWAYS adds `"masking": fingerprint_of(self.config.backends.redactor.kind)` (C1 F4; item 4). It keeps its signature. P5c-1 rebases on P4c-2, which edits the same function (`exclude={"levels", "alert_to"}`, `tickets/P4c.md:59`, `:180`(c)), and adds its key after P4c's exclude. Every existing hash changes once, and every agent needs one new `hadavin-sdk gate <agent>` run per fingerprint change (Rollback).
  7. **`MaskedLLM` (P5c-2; rewritten, R1-COR-1, R1-ADV-1, -2, -8, -17).**
     - **Construction.** `MaskedLLM.of(inner: LLM, redactor: Redactor, audit: AuditSink) -> MaskedLLM` returns `inner` unchanged when it already is a `MaskedLLM` with the same redactor fingerprint and the same audit sink. A different fingerprint or sink raises `TypeError` (T2-17). `__init__(..., *, _token)` raises `TypeError` on a wrong token.
     - **Public read-only properties (revision 3):** `redactor` (R2-COR-6; `extract` uses it with `ctx.session`) and `inner` (the wrapped model; the `Runtime` check reads it). **`MaskedLLM` has NO `__getattr__` delegation**, so no name of the inner model is reached around the wrapper. Tests that read `rt.llm.calls` change to `rt.llm.inner.calls` (through `MeteredLLM.__getattr__`, P4b1-b).
     - **`chat`.** `chat(messages, *, system, route, tools=None, documents=None, output_schema=None) -> Reply` has the same signature as `LLM.chat`.
     - **The run context.** `run(run_id: str, principal: str, *, seed: RunMap | None = None) -> ContextManager[RunCtx]` (`seed` is new in revision 3: the run loop passes its own `rmap`; `None` means an empty map). `RunCtx(run_id, principal, session)` lives in a `contextvars.ContextVar`. Thread hops use `contextvars.copy_context().run`.
     - **k1b's thread (R2-COR-14).** `k1b/loop.py:104` starts `threading.Thread(target=work, daemon=True, ...)`, which does not carry the `ContextVar`. P5c-3 changes it to run `contextvars.copy_context().run(work)` in that thread. A late call from an abandoned thread then finds the closed session and raises `SessionClosed` before the audit row and before the inner call; the existing handler logs the class name only (`k1b/loop.py:97-101`). Row T3-11b.
     - **`Runtime`'s check (revision 3, R2-COR-11; order 22 item 30; PENDING LEAD 27):** `isinstance(llm, MaskedLLM) and isinstance(llm.inner, MeteredLLM)`, so the exact order is `MaskedLLM(MeteredLLM(raw))`. A raw model, `MaskedLLM(raw)` and `MeteredLLM(MaskedLLM(raw))` are each refused (T3-06b). P5c-3 replaces P4c-2's `isinstance(llm, MeteredLLM)`.
     - **The one strict decode (RES-1).** `llm/masked.py` exports `decode_document(data: bytes) -> str`: strict UTF-8, a BOM stripped; invalid UTF-8, a NUL byte, or a PDF, PNG, JPEG, GIF or zip signature raises `RedactorRefusal("unsupported_input")`. The wrapper's step (a), `extract`, the run loop (`agent_loop.py:367`) and `evals.py:63` all call it, so the four decodes cannot drift apart.
     - **Calls outside a run (changed, CHANGELOG rev 2 cut 9).** A `chat` outside any `run(...)` raises `SessionClosed` and makes no inner call.
     - **What each call does, in order:**
       - **(a) Decode.** Bytes documents go through `decode_document` (above).
       - **(a2) Only text is masked (revision 3, R2-ADV-7; PENDING LEAD 31; cut).** The wrapper masks and checks only text leaves (defined in "Words"): `str` `content`, the `text` of `type == "text"` blocks, `tool_result` content text, and the string leaves of `tool_use` input in assistant turns (model text, re-masked only). **Any other block type (image, document, or an unknown type) in any turn gives `RedactorRefusal("unsupported_input")`, with zero inner calls and no audit row** (T2-18). Before writing the list, the builder records in the evidence which block types the run loop builds today (UNVERIFIED by me and by the resolve).
       - **(b) The wrapper never escapes.** It re-masks every text leaf of `messages` and of `documents` with `redactor.mask(..., untrusted=False)` over the run's session.
         - **Pass 1** goes through the leaves in a fixed order: documents first, then messages.
         - **Pass 2:** if the session's map grew during pass 1, every leaf is masked once more, so a value first seen in a later leaf is masked in earlier leaves too.
         - There is no join and no split (CHANGELOG rev 2 cut 4).
         - The caps (`defaults.MAX_REDACT_CHARS`) and the time budget (`defaults.REDACT_BUDGET_S`) apply per `redact_text` call (per leaf), as on main.
         - The whole body is still scanned on every call (C1 F2): there is no exemption for issued placeholders.
       - **(c) Check the body.** `check` runs over every leaf except assistant turns. An unissued placeholder gives `forged_mark`; a plain session original gives `self_check_failed`. This catches an entry point that forgot to escape (R1-ADV-8).
       - **(d) Check the configuration.** `system`, `tools` and `output_schema` are `check`ed and never masked (C1 F3).
       - **(e) Audit before the call.** One audit event is written with `write_intent` BEFORE the inner call (C1 D8): `domain="llm"`, `operation="outbound"`, `inputs_hash=sha256_hex(masked body)`, `rule_id=redactor.fingerprint`, `result="chars=<in>/<out>;" + sorted "kind:n"` counts. If it raises `AuditUnavailable`, that goes to the caller and no call is made. **There is no outcome row after the call (revision 3, R2-ADV-8; PENDING LEAD 33).** Intent rows with no outcome row already exist on main (`limits.py:50` `reset`; `k1b/audit_sink.py:35` `emit`; `AuditSink.reconcile` only drains the outbox, `audit/protocol.py:27-29`). An outcome row would add a second failure path after a call that may already be billed, and P4b1's meter records the call's outcome anyway. Whether any audit READER (verify, export, reconcile) flags an unpaired intent is UNVERIFIED: the builder greps the readers and lists the result in the evidence.
       - **(f) The inner call.** `inner.chat(...)`. Any refusal raises `RedactorRefusal` or `RedactionError`, and the inner model is never called.
     - **One masking mode per input class (PENDING LEAD 15).** Raw external text is escaped ONCE, where it enters, with `redact_untrusted`:

       | input class | where it is escaped (before the wrapper) | what the wrapper does |
       |---|---|---|
       | raw `extract` document | **NEW:** `extract` calls `llm.redactor.mask(decode_document(doc), ctx.session, untrusted=True)` before the call (RES-1: `document` is `bytes`, `mask` takes `str`) | re-mask (trusted) and check |
       | raw gate case (`evals.py`) | STAYS (`evals.py:63`), now over the run's session, not a fresh `{}`, and decoded by `decode_document` instead of `decode("utf-8", "replace")` | re-mask and check |
       | run-loop document | STAYS (`agent_loop.py:367`), decoded by `decode_document` instead of `decode("utf-8", "replace")` | re-mask (no change expected) and check |
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
  - **Outline, not built:** a detector-model backend (a local named-entity model behind the same protocol, for names in free prose and document types the patterns miss). Trigger: "a client document type the patterns miss" (plan-v3 section 5). It also writes the shared contract suite (V3; CHANGELOG rev 2 cut 3).
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
      - `Runtime.__init__` requires `isinstance(llm, MaskedLLM) and isinstance(llm.inner, MeteredLLM)` (item 7; REPLACES P4c-2's check), and outside `dev` it refuses a wrapper whose fingerprint differs from `fingerprint_of(configured kind)` (T3-18). P4c's `self.llm.scope(...)` becomes `self.llm.inner.scope(...)`;
      - `handle` keeps `rmap = runmap.RunMap(mapping or {})` (`:352`) and every plain-map use, and enters `with llm.run(run.run_id, principal_id, seed=rmap) as ctx:` for its whole body (revision 3; no `_map_of` here);
      - `received` carries no `inputs_hash` (CHANGELOG rev 2 cut 11);
      - **strict UTF-8 decoding, with its order and result (revision 3, R2-COR-12):** `received` (`:349`) stays the first event, then the too-large check (`:354`), then `decode_document` at `:367`. On `unsupported_input` (invalid UTF-8, NUL, or a file signature): `self._note(run, "guard", "document", result="stopped", error_code="unsupported_input")` (`_note` at `:229`), then `self._abstain(run, NEEDS_PERSON, "unsupported_input", cited)` (`_abstain` at `:569`), with zero model calls. `_REASON_TEXT["unsupported_input"]` is added (`_REASON_TEXT` at `:87`);
      - the chat block also catches `AuditUnavailable`, so a person looks with reason `audit_unavailable` (C1 F7);
      - **`_screen` (`:310-316`) catches the wrapper's refusals itself (revision 3, R2-COR-4).** Today it calls `injection_check` with no `try`, and neither caller (`:387` document, `:520` tool output) is wrapped; `injection_check` turns every exception into `guard_unavailable` (`guard/injection.py:89-101`), and P5c-3 makes it re-raise. Inside `_screen`: `RedactionError` -> `_redaction_failed` (reason `redaction_error`, `:547`), and `AuditUnavailable` -> NEEDS_PERSON `audit_unavailable`, with zero further model calls. Inside `_screen`, not at each caller, so a third caller cannot forget it. It ends the run through P4c-2's `_RunEnded` (`tickets/P4c.md:13`), on which P5c-3 rebases;
      - the session is closed in `finally`.
    - **`app.py`:** `:162` wraps the built model with `MaskedLLM.of` BEFORE the detector is built; `build(llm=raw)` wraps too.
    - **`cli.py`:** the gate at `:150` and k1b at `:221` build their wrappers over one raw model (C1 F6). The flag at `:120` keeps its meaning (CHANGELOG rev 2 cut 1).
      - **`cli gate`'s audit sink (revision 3, R2-COR-6; PENDING LEAD 29).** Today `cli gate` (`cli.py:146-153`) builds the model and no audit sink. It now builds one with `k1b.audit_sink.build_audit(cfg, secrets)` (`k1b/audit_sink.py:59-72`) and passes its `.sink`, as k1b does at `cli.py:216`. `local_dir` needs no store; `chain` builds store, signer and anchor.
      - **Audit down during a gate run:** `AuditUnavailable` stops the gate. The command prints the code and exits non-zero, and nothing is written to `qualified.jsonl`. A gate run is never GREEN without its audit rows (T3-10b).
    - **`extract.py` (signature decided in revision 3, R2-COR-6):** `extract(llm, document: bytes, schema, *, run_id, principal, route, system="")` (today `extract.py:34-42` has no `principal`). `principal` is required, with no default. It requires the wrapper; puts the whole retry loop in one `llm.run(run_id, principal)`; decodes with `decode_document` and escapes with `llm.redactor.mask(..., ctx.session, untrusted=True)` before the call (RES-1); returns placeholders only.
      - **The retry text (R2-COR-5).** Today `:58` builds it with `safe_head(str(exc), 300)`, which masks with a FRESH map (`guard/runmap.py:532-540`, `redact_bounded(text, {} if mapping is None else mapping)`). P5b3 rewrites `:57-64` so the retry text holds closed text only: error type names, or a code and a `position` fact (`tickets/P5b3.md:192-193`). With no echoed value there is no `<EMAIL_9>` to forge and nothing for a fresh map to number, so **P5c-3 adds no masking to that line.** Rows T3-03c and T3-03d check it through the wrapper.
      - **Fallback:** if P5b3's merged text still echoes input, P5c-3 escapes the error text with `llm.redactor.mask(..., ctx.session, untrusted=True)` over the run's session. The builder records in the evidence which case applies.
    - **`evals.py` (R2-COR-6, R2-COR-12):** requires the wrapper; `gate` keeps its signature. Each (case, k-run) opens `llm.run(f"gate-{uuid4().hex}-{case_id}-{k}", "gate")`; `"gate"` is a fixed code identity, not a person. The existing `redact_untrusted` at `:63` uses that run's session and decodes with `decode_document`. **A case that is not UTF-8 counts as FAILED with reason `unsupported_input`**, so the gate cannot be GREEN on a corrupted case (T3-05b).
    - **`guard/judge.py`:** `JudgeDetector.__init__` requires the wrapper. `:71`'s own `redact_text(text, {})` is removed, so judge placeholders equal run placeholders.
    - **`guard/injection.py`:** re-raises `RedactionError` and `AuditUnavailable` (C1 D9, F7, F11).
    - **`guard/producers.py`:** the judge row (`:28`) and the evals row (`:40`) become "through `MaskedLLM`". The vendor guardrail row (`:29`) is unchanged: `guard/bedrock_guardrail.py` is not a `.chat(` door and keeps its own `redact_text`.
    - **`tests/test_k5_producers.py`:** checks the new rows (T3-17).
    - **`k1b/loop.py`:** uses `MaskedLLM.of`; `except RedactionError` and `except AuditUnavailable` give status `error` and halt `aborted`; `_call_with_deadline`'s thread (`:104`) runs `contextvars.copy_context().run(work)` (item 7, R2-COR-14).
    - **Tests that read `rt.llm.calls`** change to `rt.llm.inner.calls` (item 7; no `__getattr__` on `MaskedLLM`). The builder lists them in the evidence.
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
      - **`defaults.py`:** PHONE is removed from `STORED_KINDS` (PENDING LEAD 17, ANSWERED yes by order 22 item 27), leaving 12 kinds. `Config.evidence.stored_kinds` may only narrow. **A config that lists `PHONE` in `evidence.stored_kinds` is refused at load** by the existing check (`config.py:256`, `if unknown := sorted(set(self.stored_kinds) - set(defaults.STORED_KINDS))`); this is kept (fails closed and loud), not narrowed silently (R2-ADV-6, R2-COR-10; PENDING LEAD 30; row T4-10). The default (`config.py:215`) follows `STORED_KINDS`. The builder lists the existing tests that relied on stored phones, each with its reason;
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
  - **Card and bank numbers labelled PHONE (G10; PENDING LEAD 17, ANSWERED yes by order 22 item 27).** With PHONE out of the default stored kinds, a bare 16-digit card number, or a 10-11 or 13-16 digit bank number masked as PHONE, is still MASKED in the body but never stored and never put back (T4-12 pins "masked, not stored"; T4-11 pins the exact list of 12 stored kinds). The cost: a phone number is no longer put back into a plan (v1.1 row V10).
  - **The plain run map (PENDING LEAD 24).** The run loop holds the plain `RunMap` for its run, as on main; the session wraps that same object. F10 protects the session object, not the run loop's own reference. The map leaves the process only to the store, and only for stored kinds.
  - **`extract` in v1 (PENDING LEAD 20).** Core `extract` returns placeholders and offers no restore handle. A field whose schema checks the format of a masked value (an IBAN, an all-digits account) fails its check on the placeholder and goes to `DeadLetter`. **Intake cannot move its invoice supplier payment details (the bank account on an invoice) extraction onto core `extract` in v1** (v1.1 row V9). The retry text sent back to the model holds closed text only (error type names, or a code and a position, after P5b3), and no document value.
  - **What P5c does NOT promise.** Each item is in the README "not masked" list, pinned by a test that the README names it (C1 D12):
    - (a) names in free prose with no title or `Dear`;
    - **(a2) names whose first letter is a non-ASCII capital** (PENDING LEAD 21; NAME-NONASCII-INITIAL);
    - (b) plain account numbers (see "Order 11(5)" below);
    - (c) **look-alike copies of secrets of 8 to 11 characters: only plain copies are caught** (order 15);
    - (d) **a known value encoded in base64, hex or invisible characters is not read by the look-alike check.** Only the tool-output scrubber removes the exact hex and base64 spellings of a secret handed to a tool; nothing else in v1 catches an encoded copy (order 19 C, PL46(a));
    - (e) partial or one-character-changed copies (design section 8);
    - (f) images, PDFs and other non-text documents are refused, and so are text documents that are not UTF-8 (PENDING LEAD 3), and non-text content blocks in a model call (PENDING LEAD 31);
    - (f2) a stored identifier written inside a longer word is not masked (the sweep's standalone rule) and `check` does not refuse it (PENDING LEAD 25);    - (g) prompts, contract descriptions and schemas are checked but not masked (V5);
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
    - ACC-2: the strong keywords of the table plus 6-17 digits (item 5 (ii); the digits are masked, the keyword is kept);
    - **PHONE-labelled numbers are no longer stored** (PENDING LEAD 17, answered by order 22 item 27; T4-01, T4-12).
  - **What stays open in v1, with the reason:**
    - 8-9 and 17+ digits with no keyword: a pattern of those lengths would mask dates, amounts and invoice numbers;
    - digits glued to letters;
    - JSON numbers.
  - These are strict-xfail records (ACC-1a, ACC-1b, ACC-3) and v1.1 row V4.
  - Intake's own masking (`promotion-inputs/intake-a12/src/intake/mask.py`) is UNVERIFIED; the lead's statement of the gap is taken as given.
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** row ids are fixed. FB = fails before (on the main head the pull request rebases on, P2d-2 included; for pattern rows, the merged P2d-2 head). PIN = regression pin. NEW = new surface, guarded by mutants. XF = `xfail(strict=True)` record with its v1.1 row.
  - **P5c-1, `tests/test_p5c1_redactor.py` (16 rows):**
    - T1-01 `test_protocol_members_exact` (no `put_back`; `mask` has no default for `untrusted`) NEW.
    - **T1-02 `test_fingerprint_computed_over_masking_sources`** (extended in revision 3). Editing any listed file, simulated on a temporary copy, changes the fingerprint; **so does changing any one value of `MASKING_VALUES`** on a temporary copy. The list covers every `hadavin_sdk.guard` module that `guard/redactor.py` imports, directly or through other modules (AST walk), **and `tools.py` is in the list**. `REGEX_VERSION == "4"` and `FOLD_VERSION` is part of the string. `fingerprint_of("regex") == RegexRedactor.FINGERPRINT`, and an unknown kind raises `ConfigError`. NEW.
    - T1-04 `test_config_hash_includes_masking` (revision 3: asserts both the `masking` key AND P4c-2's `alert_to` exclusion) FB.
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
    - **T1-17 `test_map_of_callers_ast`** (revision 3: `_map_of` is used only in `guard/redactor.py`; complete at P5c-1, nothing deferred to P5c-3) NEW.
    - T1-03 is cut (CHANGELOG rev 2 cut 5).
  - **P5c-1, `tests/test_p5c1_patterns.py` (14 rows; made-up digits built in the test):**
    - ACC-1c FB.
    - ACC-1c-NEG NEW.
    - **ACC-2** (changed): one parametrised case per strong form of the item-5 table, 59 cases: `account`/`accounts` x 8 suffixes = 16; `acct`/`acct.` bare = 2; `acct`/`acct.` x 8 suffixes = 16; `a/c` bare = 1; `a/c` x 8 = 8; `acc`/`acc.` x 8 = 16. Each with 8 made-up digits and no bank word, giving BANKACCT. **Each case asserts (strengthened in revision 3, R2-COR-1): the 8 digits are absent from the output; the keyword text is still present; the map holds exactly one BANKACCT entry, whose value equals the digits.** FB.
    - **ACC-2-NEG** (changed): one case per weak form (`account`, `accounts`, `acc`, `acc.`, bare: 4 cases), plus `Account No: <5 digits>`; none gives BANKACCT. NEW.
    - ACC-12 (bare 12 digits gives ACCOUNTID, stored; `Account No: <12 digits>` gives BANKACCT, not stored) FB for the second half.
    - NAME-HYPH FB.
    - NAME-NONASCII (`Dear Jürgen <last>`) FB.
    - **NAME-TITLE** (the title form with a hyphenated part and a non-ASCII following letter) FB.
    - **NAME-DECOMPOSED** (`Dear Jose` + U+0301 + ` <last>`: the whole name is absent from the output) PIN, by reading only (probe (b); main's NFKC second pass).
    - **NAME-NONASCII-INITIAL** XF (a name with a non-ASCII first capital; V4b).
    - **NAME-CAPS** (new in revision 3, R2-ADV-9, R2-COR-17): `Dear MARY <last>` is masked whole, and `Dear ALL` and `Dear JohnSmith` each become one NAME placeholder (the width of item 5(iii) pinned). FB for `Dear MARY` (on base `[a-z]+` does not match it, by reading).
    - ACC-1a XF (V4).
    - ACC-1b XF (V4).
    - ACC-3 XF (V4, LKV-8).
    - The repository suite runs with item 5 in place. Any existing pin that item 5 changes is listed with its reason, never weakened.
  - **P5c-2, `tests/test_p5c2_masked_llm.py` (17 rows, all through `RecordingLLM`):**
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
    - **T2-15 `test_body_check`** (new): (a) a raw document holding a forged `<EMAIL_9>`, sent with no escape, gives `forged_mark` and zero inner calls; (b) a plain session original left in a leaf (masker stubbed) gives `self_check_failed`; **(c) pass/fail since revision 3 (R2-ADV-3, R2-COR-8): a stored made-up name inside a longer made-up word gives ONE inner call and no refusal, and the longer word arrives unchanged**; (d) a stored made-up SECRET-kind value inside a longer word, masker stubbed, gives `self_check_failed` (the sweep's "any copy of a secret" half). NEW.
    - **T2-16 `test_issued_marks_and_markers_arrive_unchanged`** (new): an issued placeholder in an assistant turn and in a tool turn, and a `<<TOOL RESULT` marker, appear byte-identical in the recorded body. NEW.
    - **T2-17 `test_of_refuses_a_different_redactor_or_sink`** NEW.
    - **T2-18 `test_non_text_block_refused`** (new in revision 3, R2-ADV-7): an image block, a document block and an unknown block type, each in a user turn and in a tool turn, give `unsupported_input`, zero inner calls and no audit row. NEW.
    - T2-12 is cut (CHANGELOG rev 2 cut 1).
  - **P5c-3, `tests/test_p5c3_wiring.py`, `tests/test_c1_acceptance.py`, `tests/test_k5_producers.py` (32 rows). Each row names its entry path:**
    - **T3-01 `test_pii_never_reaches_llm`** (acceptance; `app.build(llm=RecordingLLM(...))`, at least 3 tool steps, a new value at step 2, judge calls included). FB on the `extract` and audit paths; PIN on the run loop.
    - **T3-02 `test_raising_redactor_needs_person_no_chat_no_judge`**: PIN (run loop). It has no mutant of its own (the "M24, M33" cross-reference is removed, R1-ADV-15).
    - **T3-03 `test_extract_document_masked`**: path `extract`, FB. Both the first call and the retry call hold placeholders only.
    - **T3-03b `test_extract_forged_mark_escaped`**: path `extract`; a forged `<EMAIL_9>` arrives as `‹EMAIL_9›` and the call succeeds. FB (on base the raw text is sent).
    - **T3-03c `test_extract_model_invented_mark_gives_dead_letter`** (new in revision 3, R2-COR-5): path `extract` through the wrapper; the model's first reply holds `<EMAIL_9>` and fails validation; the second call is made and holds no `<EMAIL_9>`; `extract` returns `DeadLetter`, not a `forged_mark` raise. NEW.
    - **T3-03d `test_extract_retry_body_has_no_fresh_map_mark`** (new in revision 3, R2-COR-5): path `extract`; the retry body holds no placeholder numbered by a fresh map (every placeholder in it was issued by the run's session). NEW.
    - **T3-04 `test_received_has_no_raw_document_hash`**: path run loop, FB.
    - **T3-05 `test_non_utf8_document_refused`** (revision 3, R2-COR-12, RES-1): path run loop, parametrised over invalid UTF-8, a NUL byte and each file signature; asserts state NEEDS_PERSON, reason `unsupported_input`, the event order `received` then the `guard`/`document` `stopped` event, and zero model calls. **Case T3-03e** (a non-UTF-8 `extract` document is refused with zero inner calls) is a parametrised case of this row, not a new row. FB.
    - **T3-05b `test_gate_non_utf8_case_fails`** (new in revision 3, R2-COR-12): path gate; a case that is not UTF-8 counts as failed with reason `unsupported_input`, and the gate is not GREEN. FB (on base `evals.py:63` decodes with `replace`).
    - T3-06 `test_wrapper_required_isinstance` over `Runtime.__init__`, `evals.gate`, `extract.extract`, `JudgeDetector.__init__`: FB.
    - **T3-06b `test_runtime_requires_masked_over_metered`** (new in revision 3, R2-COR-11): a raw model, `MaskedLLM(raw)` and `MeteredLLM(MaskedLLM(raw))` are each refused by `Runtime.__init__`; `MaskedLLM(MeteredLLM(raw))` is accepted. NEW.
    - **T3-07 `test_raw_llm_import_graph_ast`** (changed): (b) every `make("llm", ...)` is in `app.build_llm` or `cli.py`'s named builders; (c) no module outside `llm/`, `backends/builtin.py` and `app.py` imports a raw llm kind module; (d) `demos/ask-your-data/askdata/pipeline.py` is scanned, or its exclusion is written with a reason. FB.
    - **T3-09 `test_judge_uses_run_session`** (rewritten): path judge. Call `JudgeDetector.check` with text holding a NEW raw made-up e-mail plus an issued `<EMAIL_1>` of another value. After P5c the new value gets `EMAIL_2`. On base the fresh map numbers it `EMAIL_1`, a collision, so the row is FB.
    - T3-10 `test_gate_session_fresh_per_case`: path gate, NEW.
    - **T3-10b `test_gate_audit_down_never_green`** (new in revision 3, R2-COR-6): path `cli gate`; the audit sink raises `AuditUnavailable`; the command exits non-zero, prints the code, and writes nothing to `qualified.jsonl`. NEW.
    - **T3-11 `test_k1b_goes_through_the_wrapper`**: path k1b, NEW.
    - **T3-11b `test_abandoned_k1b_call_after_close_sends_nothing`** (new in revision 3, R2-COR-14): path k1b; a call from an abandoned thread that ends after the session closed makes zero inner calls and writes no `outbound` row. NEW.
    - T3-12 `test_redactor_raises_on_second_call_reason_is_redaction_error`: path injection check, both `_screen` callers (`:387` document, `:520` tool output), FB (`injection.py` turns it into `guard_unavailable` today).
    - **T3-12b `test_judge_audit_unavailable_needs_person`** (new in revision 3, R2-COR-4): path injection check, parametrised over both `_screen` callers; the judge's wrapped call raises `AuditUnavailable`; the run ends NEEDS_PERSON `audit_unavailable` with zero further model calls. NEW.
    - T3-13 `test_audit_unavailable_at_outbound_needs_person`: path run loop, NEW.
    - T3-14 `test_output_tree_has_no_seeded_values` (logs, audit rows, stored runs, cards, exception texts): PIN on the run loop.
    - **T3-14b `test_tool_result_forged_mark_escaped`** (new): path tool result; the run continues, and the recorded body holds `‹...›`. PIN (`prepare_output` escapes today).
    - **T3-15a..f `test_lookalike_copy_in_document_zero_model_calls[...]`** (the lead's order 11(1) rows: Cyrillic/Greek, fullwidth, zero-width, combining mark, split over two lines, other case): path run loop, **PIN through the wrapper** (relabelled).
    - **T3-15g `test_extract_lookalike_copy_zero_model_calls`** (new): path `extract`, FB (on base `extract` sends the raw document).
    - **T3-16 `test_golden_and_eval_input_ref_files_are_strict_utf8`**: the 10 input documents (`tests/fixtures/inputs/golden-NN.txt`, all strict UTF-8 per revision 2's check) and the golden set file `tests/fixtures/golden/test-agent.jsonl` (R2-COR-20; the 11 paths re-counted by me at `124258b`). Other `input_ref` files are UNVERIFIED. PIN.
    - **T3-17 `test_k5_producers_judge_and_evals_through_maskedllm`** (new, in `tests/test_k5_producers.py`) FB.
    - **T3-18 `test_runtime_refuses_mismatched_fingerprint_outside_dev`** (new) NEW.
    - T3-08 is cut (CHANGELOG rev 2 cut 8).
  - **P5c-4: 12 rows. `tests/test_p5c4_putback.py` holds 11 rows; T4-04 is in `tests/test_c1_acceptance.py`** (R2-ADV-10, R2-COR-15):
    - **T4-01 `test_secret_regulated_and_phone_labelled_numbers_never_restored`**: IBAN, CREDITCARD, each SECRET kind, BANKACCT, BANKCODE, SSN, AADHAAR, PAN and UUID stay placeholders, **plus a bare made-up 16-digit card number, a 10-digit and a 14-digit number (masked as PHONE)**. FB for the PHONE part; PIN for the rest.
    - T4-02 `test_withheld_line_placeholder_not_restored` FB.
    - **T4-03 `test_restore_called_only_at_three_seams_ast`** (changed: `inputs_view`, `_run_tool`, `ToolBox.invoke`; no `runmap.restore_value` call left in `agent_loop.py` or `tools.py`) FB.
    - T4-04 (in `test_c1_acceptance.py`) `test_restored_values_appear_only_in_the_proposal`: PIN plus the new seams.
    - T4-05 `test_plan_with_unresolved_mark_never_executes` PIN.
    - T4-07 `test_restorable_key_refused_at_load` FB.
    - T4-08 `test_restore_gives_written_spelling` NEW.
    - **T4-09 `test_restore_at_approval_in_fresh_process_from_store_only`** (new, R1-ADV-4) PIN.
    - **ACC-12b `test_account_number_12_digits_never_put_back`** (new, R1-ADV-6): `Account Number: <12 digits>` gives BANKACCT; the plan input stays a placeholder; the gate denies `input.unresolved`. FB (on base it is ACCOUNTID and is restored).
    - **T4-10 `test_config_naming_phone_refused_at_load`** (new in revision 3, R2-ADV-6, R2-COR-10): a config whose `evidence.stored_kinds` lists `PHONE` fails to load with the `config.py:256` error. FB.
    - **T4-11 `test_stored_kinds_exact_list`** (new in revision 3, order 22 item 27): `defaults.STORED_KINDS` equals the exact 12-kind tuple ACCOUNTID, ADDRESS, ARN, AZURERESOURCE, EMAIL, GCPRESOURCE, HOSTNAME, IPV4, IPV6, MAC, NAME, TENANT, in the file's order. FB.
    - **T4-12 `test_bare_16_digit_card_masked_not_stored`** (new in revision 3, order 22 item 27): a bare made-up 16-digit card number is masked in the body and absent from the stored map. FB for the "not stored" half.
    - T4-06 is cut (CHANGELOG rev 2 cut 7).
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
    - invalid UTF-8, NUL, file signatures (T2-09, T3-05 with its `extract` case T3-03e, T3-05b, T3-16);
    - non-text content blocks (T2-18);
    - a keyword before account digits (ACC-2: the digits, not the keyword, are masked);
    - a model-invented placeholder in an `extract` reply (T3-03c, T3-03d);
    - a late call from an abandoned k1b thread (T3-11b);
    - audit down inside the judge and inside the gate (T3-12b, T3-10b);
    - look-alike copies (T3-15a..g, T2-14);
    - threads with a barrier (T2-10);
    - a raising redactor (T2-08, T3-02, T3-12);
    - audit down (T2-07, T3-13);
    - copies and pickles (T1-05);
    - use after close and calls outside a run (T1-06, T2-11);
    - restore of secret kinds, PHONE-labelled numbers and folded spellings (T4-01, T4-02, T4-08);
    - a mismatched wrapper or the wrong wrapper order (T2-17, T3-18, T3-06b).
    - **Size and time:** main's caps apply per leaf. The `perf`-marked row **T2-P** (changed) is a 20-step history whose leaves are each near `MAX_REDACT_CHARS`, made of the adversarial shapes of C1 F11 plus 5,000 distinct e-mails and IBANs. The runner measures the time and pins it; the budget number is UNVERIFIED.
  - **Contract suite:** none in v1 (one backend; CHANGELOG rev 2 cut 3, row V3).
  - **Totals (re-derived from this file for revision 3):** **91 rows**: `test_p5c1_redactor.py` 16; `test_p5c1_patterns.py` 14 (+NAME-CAPS); `test_p5c2_masked_llm.py` 17 (+T2-18); P5c-3 32 (+T3-03c, T3-03d, T3-05b, T3-06b, T3-10b, T3-11b, T3-12b); P5c-4 12 (+T4-10, T4-11, T4-12), of which 11 are in `test_p5c4_putback.py` and T4-04 is in `test_c1_acceptance.py`. 16 + 14 + 17 + 32 + 12 = 91. Plus the `perf` row T2-P: **92**. Of the 91, 4 are strict-xfail records (ACC-1a, ACC-1b, ACC-3, NAME-NONASCII-INITIAL), unchanged. ACC-2 runs 59 parametrised cases and ACC-2-NEG runs 5. T3-03e is a case of T3-05, not a row; T3-15a..f counts as 6 rows (as in revision 2). Revision 2 had 79 + 1; revision 1 had 68 + 1.
- **Mutation plan (which behaviours get a mutant, which test kills each):**
  - **How mutants run.** They run through P1m's runner from `tests/p5c_mutants.py` (`Mutant(name, file, old, new, expect, ...)`). `old` is the exact source line the builder writes, so it cannot be listed in advance. Each mutant must end KILLED, never CRASH or WRONG_REASON, and each killing test is run twice. The table "mutant -> killing test" is pasted into the evidence BEFORE the run (C1 F11). **Each mutant's `expect` is a distinctive fragment of the killer's intended failing line (the assertion that must fail), never equal to the killing test's name** (order 26 item 2), so the judge can tell which guard the mutant broke.
  - **50 mutants** (revision 2 had 44; M50-M55 are new in revision 3). Every mutant has a named killer.
  - **P5c-1 (19):**
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
    - **M46 `MASKING_SOURCES` drops `guard/runmap.py` -> T1-02;**
    - **M50 (new, the Blocker) pattern 1 of BANKACCT wraps `_ACCT_WORD` in a capturing group -> ACC-2** (the digits appear in the output: group 1 becomes the keyword, so either the keyword is masked as the value or, because `m.start(1)` moves, the new clause finds no strong form; both fail ACC-2's "digits absent" assertion);
    - **M51 (new) `MASKING_VALUES` drops `STORED_KINDS` -> T1-02.**
  - **P5c-2 (15):**
    - M20 documents not masked -> T2-02;
    - **M21 pass 2 skipped when the map grew -> T2-02;**
    - M22 `system` masked instead of checked -> T2-04;
    - M23 the audit `write_intent` after the inner call -> T2-06;
    - M24 a redactor exception passed through to the inner call -> T2-08;
    - M25 `decode_document` decodes with `replace` -> T2-09;
    - M26 the context in a module global instead of a `ContextVar` -> T2-10 (the barrier forces interleaving);
    - M28 issued-placeholder regions exempted from the scan -> T2-13;
    - M29 `AuditUnavailable` swallowed -> T2-07;
    - **M42 `check` skipped on the body -> T2-15;**
    - **M44 `of()` returns the existing wrapper despite a different fingerprint or sink -> T2-17;**
    - **M47 a call outside `run(...)` opens an implicit session -> T2-11;**
    - **M48 the wrapper masks leaves with `untrusted=True` -> T2-16** (issued placeholders become `‹...›`);
    - **M52 (new) `check` uses a plain substring test instead of the sweep rule -> T2-15c** (the benign longer word is refused);
    - **M55 (new) a non-text block is masked as text instead of refused -> T2-18.**
  - **P5c-3 (11):**
    - M30 `app.build(llm=raw)` not wrapped -> T3-06 and T3-01;
    - **M31 (retargeted) `extract` skips the untrusted escape (`untrusted=False`) -> T3-03b.** Why the wrapper does not hide it: the wrapper does not escape, so the forged mark reaches the body check, which refuses with `forged_mark`, while T3-03b requires a successful call holding `‹EMAIL_9›`.
    - **M32 `received` keeps `inputs_hash` of the raw document -> T3-04;**
    - M33 the run loop at `:367` decodes with `.decode("utf-8", "replace")` instead of calling `decode_document` -> T3-05 (M25 mutates the helper itself; M33 bypasses it in the run loop, so the two stay distinct);
    - M34 the `isinstance` check removed in `Runtime.__init__` -> T3-06;
    - M35 `injection_check` swallows `RedactionError` -> T3-12;
    - **M36 (retargeted) tool-output masking dropped (`prepare_output` returns the raw text) -> T3-14 and T3-14b.** Why the wrapper does not hide it: the wrapper re-masks the model body, but the stored run and the log lines carry the tool output unmasked (T3-14), and a forged mark in a tool result is no longer escaped, so the body check stops the run (T3-14b requires it to continue).
    - M37 the judge given a fresh session -> T3-09;
    - **M45 `Runtime.__init__` ignores a fingerprint mismatch outside `dev` -> T3-18;**
    - **M53 (new) `_screen` drops the `RedactionError` catch -> T3-12;**
    - **M54 (new) the `Runtime` check accepts `MaskedLLM(raw)` (the `inner` half removed) -> T3-06b.**
  - **P5c-4 (5):**
    - M38 the kind filter removed from `restore` -> T4-01;
    - M39 the withheld/folded marker ignored -> T4-02 (written once the merged P2d-2 marker form is known, PENDING LEAD 11);
    - M41 an unresolved placeholder allowed to execute -> T4-05;
    - **M43 PHONE added back to `STORED_KINDS` -> T4-01 and T4-11;**
    - **M49 `tools.py:1178` calls `runmap.restore_value` again -> T4-03.**
  - **Reverse check:** a wrapper that returns `inner.chat(...)` unchanged must fail T2-02, T2-13, T2-15 and T3-01 (pasted count). T3-03 and T3-15g are NOT in the list (revision 3, R2-COR-7): `extract` masks and escapes on its own, so a pass-through wrapper passes them. No stub row is added (it would test the stub).
  - **Count check:** 19 + 15 + 11 + 5 = 50.
- **Evidence commands (exact), and where the raw output is saved:**
  - **Who and where.** A SEPARATE evidence runner (its brief says "EVIDENCE RUNNER") runs these once on the final commit of each fix batch, on Python 3.13 (CI's version), and on 3.12 when the lead runs them on the laptop. Raw output goes under `handover/evidence/P5c/` as `P5c-<n>-<step>.txt`. Exit codes come from pytest itself, never from a `| tail` pipe. **The new tests must also run on Windows** (order 25 item 4; the studio laptop is Windows): T2-10's barrier and T3-11b's threads use only the standard library; no new test uses symlinks. Whether the lead also runs P5c's mutants on Windows is the lead's choice (order 25 names it for P1m).
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
  uv run --all-extras --group test python -I -c "from hadavin_sdk.guard.redactor import RegexRedactor, MASKING_SOURCES, MASKING_VALUES, fingerprint_of; print(RegexRedactor.FINGERPRINT, fingerprint_of('regex')); print(MASKING_SOURCES); print(MASKING_VALUES)" > P5c-1-fingerprint.txt 2>&1; echo rc=$?
  git grep -n -E '\b(Runtime|gate|extract|JudgeDetector)\(' HEAD -- tests demos > P5c-3-raw-model-sites.txt; echo rc=$?
  git grep -l -E 'config_hash|qualified' HEAD -- tests > P5c-1-hash-tests.txt; echo rc=$?
  ```
  - **Also saved:**
    - the fail-before table with entry paths;
    - the block types the run loop builds today (before T2-18's list is written);
    - the audit readers grep (verify, export, reconcile): does any flag an `outbound` intent with no outcome? (PENDING LEAD 33);
    - which `extract` retry-text case applies after P5b3 merges (closed text, or the fallback escape);
    - the tests changed from `rt.llm.calls` to `rt.llm.inner.calls`;
    - the `BL-core-c1a-*` disposition table (44 rows);
    - the list of changed existing tests with reasons (P5c-1, P5c-3, P5c-4);
    - `git diff --stat origin/main` per pull request.
  - The runner's mutation arguments are taken from P1m's merged README (UNVERIFIED here). The exact names `RegexRedactor.FINGERPRINT` and `fingerprint_of` are fixed by this ticket; the rest of the constructor is UNVERIFIED until P5c-1 is written.
- **Reviewers:** correctness + adversarial, fresh `egm:*` agents each round. They get the diff, this ticket and the evidence only (plan-v3 section 4), on a snapshot of the pull request head (never the disk tree; see "Base"). The adversarial brief names the redaction path and the money-adjacent put-back.
- **Done =** the plan's stop rule for the RESULT review (two rounds in a row at the final commit with no blocker and no major, and evidence green at that commit), and all gates green:
  - tests, `ruff check`, `ruff format --check` and `bandit -ll`;
  - the guard tests (`test_lockin_guard`, `test_no_hardcoded_values`, `test_k5_producers`, `test_repo_rules`, `test_no_reference_material`);
  - CodeQL, SonarCloud and CodeRabbit;
  - 50 of 50 mutants killed;
  - the fail-before table pasted;
  - `grep -n xfail` lists exactly ACC-1a, ACC-1b, ACC-3 and NAME-NONASCII-INITIAL from this package;
  - the README sections exist: supported input types; the NOT masked list; where personal data is kept; the plain-hash limit; `extract` gives no put-back;
  - the CHANGELOG entries (below).
- **Rollback:**
  - **Tags.** The lead tags `pre-P5c-<n>` before each merge. There is no migration and no change to the stored-data format.
  - **Non-revertible in effect (marked):**
    - P5c-1 changes every agent's config hash (one new gate run each). Reverting it changes the hashes again (another gate run). **The P2d/P5c-1 "revert together" lock is gone (CHANGELOG rev 2 cut 5):** reverting P2d changes the fingerprint and needs a gate run, but nothing refuses to start.
    - **Each of P5c-1, P5c-3 (if it edits a file in `MASKING_SOURCES`) and P5c-4 (it edits `redactor.py`, `tools.py` and `STORED_KINDS`) changes the fingerprint, and each needs one gate run per agent** (revision 3, R2-ADV-4, R2-COR-9). The lead MAY merge P5c-1 to P5c-4 back to back and run the gate once after P5c-4: an agent that is not qualified is refused in the meantime, which fails safe.
    - Any later edit to a `MASKING_SOURCES` file (now including `tools.py`) or to a `MASKING_VALUES` value needs a new gate run.
    - P5c-3's refusal of non-UTF-8 documents is a behaviour change that operators see.
    - **P5c-4's removal of PHONE from the stored kinds (corrected in revision 3; revision 2's sentence "phone numbers saved before it are still put back from old saved maps" was FALSE, R2-ADV-6, R2-COR-10):** after P5c-4, PHONE entries in old saved maps are NOT put back, because every seam filters by kind (`agent_loop.py:284` and `:295` pass `self._kinds`, which comes from `evidence.stored_kinds`, `:201`). **A run waiting for approval whose plan input is a PHONE placeholder is denied `input.unresolved` at execute time, and a person looks.** **A config that lists `PHONE` in `evidence.stored_kinds` no longer loads** (`config.py:256`; fails closed and loud). New runs store no phone. Reverting P5c-4 brings PHONE storage back (fails open for card and bank numbers labelled PHONE, so the lead decides).
  - **CHANGELOG lines:**
    - the config-hash rule and the gate run after each of P5c-1, P5c-3 (if it edits a masking file) and P5c-4;
    - every edit to a masking file (now including `tools.py`) or to a masking value of `defaults` re-qualifies every agent;
    - `Runtime(...)`, `gate`, `extract` and `JudgeDetector` need a `MaskedLLM`;
    - a model call outside a run is refused;
    - `received` no longer carries a hash of the raw document;
    - non-UTF-8 and binary documents are refused;
    - "adds one signed audit row before each model call" (revision 3 wording, R2-ADV-8; it replaces "roughly doubles the audit rows"); it ties model calls to the audit sink being up, which is new for the run loop and for `cli gate`;
    - non-text content blocks in a model call are refused;
    - `extract` takes a required `principal`;
    - `extract` returns placeholders and offers no put-back, and Intake cannot use it for bank details;
    - the README "not masked" list, including names with a non-ASCII first capital;
    - 12-digit ACCOUNTID numbers are stored, while `Account Number: <12 digits>` is never put back;
    - PHONE is no longer put back;
    - "a config naming PHONE in stored_kinds no longer loads: remove it";
    - "approvals pending at upgrade whose inputs hold a phone number are denied; settle or re-run them before upgrading";
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
9. **ANSWERED (order 22 item 22; see 27):** wrapper order with P4b1's `MeteredLLM` (`tickets/P4b1.md:249`, `:258`): `MaskedLLM(MeteredLLM(raw))`, ONE `MeteredLLM` on `deps.llm`.
10. **Read tools keep getting restored arguments of stored kinds** (`agent_loop.py:295`, `tools.py:1178`). Recommended: keep; restore goes through `redactor.restore` (T4-03).
11. **`RESTORE-1` marker form** (P2d L5). Recommended: the builder decides after reading the merged P2d-2; M39 and T4-02 are written then.
12. **Depends-on P5b5:** the real needs are P5a and P5b3 (P5b3 is now in the list). Recommended: narrow the plan row to "P2d-2, P5a, P5b3".
13. **`EXCEPTIONS` row date** `review_by` 2027-01-31. Recommended: yes.
14. **Hot-file list:** add P5c to `app.py` (A9 F6) and `extract.py`, and P5c-4 to `tools.py` after P2a, P2d and the look-alike design. Recommended: yes.
15. **One masking mode per input class** (R1-COR-1, the Blocker; redaction path). The wrapper re-masks in trusted mode and checks the body; escaping happens once at each raw entry point; `extract` gains one. Recommended: yes. Reversible before P5c-2 merges. Confidence 80%.
16. **Computed masking fingerprint; delete the hand pin and its start-up refusal** (R1-ADV-7). This reverses the C1 version-pin form and P2d's "pins after P2d-2" section. Recommended: yes. Reversible. Confidence 75%.
17. **ANSWERED yes (order 22 item 27):** PHONE out of the default stored kinds (R1-COR-2, money-adjacent), with V10 and the two required rows T4-11 (exact list) and T4-12 (bare 16-digit card masked, not stored).
18. **Delete the `premasked` wrapper and its operator downgrade** (R1-ADV-17a). Recommended: yes. Confidence 85%.
19. **`received` keeps its place and drops the raw hash** (R1-ADV-11, R1-COR-5). Recommended: yes. Confidence 85%.
20. **Core `extract` gives no put-back in v1; Intake cannot use it for bank details** (R1-ADV-12; the owner can see this). Recommended: state it, row V9. Confidence 80%.
21. **NAME patterns: no `isupper` callback; names with a non-ASCII first capital are not masked** (R1-COR-7; a limit the owner can see). Recommended: yes, row V4b. Confidence 70%.
22. **A model call outside `run(...)` is refused** (R1-ADV-17e). Recommended: yes. Confidence 80%.
23. **ANSWERED (order 22 items 22 and 30):** ONE `MeteredLLM` on `deps.llm`; `Runtime` refuses a model object that is not the `MeteredLLM` (reconciled with P5c in 27).

**New in revision 3 (from `reviews/P5c-round2-resolve.md`; each with the resolve's recommended answer; final under order 6(g) unless the lead replies):**

24. **`_map_of` used only inside `guard/redactor.py`; the run loop seeds the session with its own `RunMap`** (R2-ADV-2, R2-COR-2, R2-COR-3; redaction path). Recommended: yes. Reversible before P5c-1 merges. Confidence 80%.
25. **`check` uses the sweep rule (a secret anywhere, an identifier only standalone)** (R2-ADV-3, R2-COR-8; redaction path). Recommended: yes. Reversible. Confidence 75%. It is UNVERIFIED that P2d-2's look-alike check does not itself refuse the same benign text.
26. **The fingerprint also covers `tools.py` and the masking values of `defaults`** (R2-ADV-4, R2-COR-9). Recommended: yes. Cost: every `tools.py` edit re-qualifies every agent. Confidence 75%.
27. **`Runtime` requires exactly `MaskedLLM(MeteredLLM(raw))`; `MaskedLLM` has no attribute delegation; P5c-3 replaces P4c-2's check** (reconciles order 22 item 30 with P5c; money and redaction path). Recommended: yes. Confidence 80%.
28. **PENDING LEAD 9, 17 and 23 are closed by order 22 items 22, 27 and 30** (no decision needed; listed so that the lead sees the closure).
29. **`extract` takes a required `principal`; the gate uses the code identity `"gate"`; `cli gate` builds its audit with `build_audit`; audit down means the gate is never GREEN** (R2-COR-6). Recommended: yes. Confidence 75%.
30. **A config naming PHONE in `stored_kinds` is refused at load; approvals pending at upgrade with a phone input are denied** (R2-ADV-6, R2-COR-10; operators see it). Recommended: yes, with the two CHANGELOG lines. Confidence 80%.
31. **Non-text content blocks are refused (`unsupported_input`), not masked** (R2-ADV-7). Recommended: yes. Confidence 80%.
32. **NAME keeps the wide letter class: all-caps names are masked, at the cost of over-masking `Dear ALL`** (R2-ADV-9, R2-COR-17). Recommended: yes. Confidence 70%.
33. **One intent-only `outbound` row per model call, with no outcome row** (R2-ADV-8). Recommended: yes. Confidence 70% (audit readers not checked).

**New after round 3 (from `reviews/P5c-round3-resolve.md`, section "PENDING LEAD"; 34-36 are NEEDS LEAD, the builder takes each default until the lead answers; 37 is INFORM):**

34. **NEEDS LEAD (money path): an account keyword without a suffix plus 6-17 digits (R3-ADV-4).**
    - Default meanwhile: (c).
    - (a) Every keyword form counts as bank context. It is the most masking, but cloud ids written `account <12 d>` become BANKACCT and are never put back (pins `:296-298` change).
    - (b) Keep revision 3. `Account: <8 d>` (an invoice supplier account) goes to the model in clear. It is recorded as a strict xfail, a V4 clause, a README item and an owner-visible limit.
    - (c) RECOMMENDED: the weak forms count except at exactly 12 digits, which stay ACCOUNTID. Nothing keyworded of 6-17 digits goes in clear. Pins `:240-241` and `:289-292` change.
    - Confidence 70%. Reversible until P5c-1 merges, and after that with one gate run per agent.
35. **NEEDS LEAD (redaction path): a document value equal to a prompt or schema word refuses every call (R3-ADV-2).**
    - Default meanwhile: (a).
    - (a) RECOMMENDED: keep the check (fails closed), add hostile row T2-20, and set the ceiling at 0 refusals over the golden inputs and fixtures. The README states it.
    - (b) Trusted-config exemption (`trust_config`, one method, one mutant). It closes the denial and keeps the check for caller-built `extract` config.
    - (c) Drop the `self_check_failed` half on config. It is the smallest, but a caller-built `extract` `system` holding a document value is then sent.
    - Confidence 60%. The live false-abstain rate is unmeasured. Reversible.
36. **NEEDS LEAD (money path, least privilege): bare 12-digit numbers are stored and put back (R3-ADV-6).**
    - Default meanwhile: (b).
    - (a) Keep. Argument for it: cloud-operation agents read and act on account ids (pins `:296-298`), and a plan passes the approval gate before any executor. Against it: a bare 12-digit bank number on an invoice can go back into a plan.
    - (b) RECOMMENDED: ACCOUNTID leaves the DEFAULT stored kinds, and an agent opts in by config (deny by default; one constant, one row, one mutant).
    - (c) Remove ACCOUNTID from `STORED_KINDS`. No agent gets ids back, which breaks cloud-operation agents.
    - Confidence 70%. Reversible with one gate run per agent.
37. **INFORM: gate runs are per case; judge cases each get a run; `MaskedLLM.current()` and a read-only `Runtime.llm` are added** (R3-COR-1, -2, -4). There is no owner rule here. Reversible before P5c-3 merges.

**Totals after the round 3 build notes (defaults of NEEDS LEAD 34, 35 and 36; from the resolve's Counts and BN-18):** 101 rows (was 91) plus the T2-P measurement; 4 strict xfail; 66 mutants (was 50). The variants for other lead answers are in BN-18.

**For the lead (not a decision):** order 24 item 39 asks for `handover/owner-visible-limits.md` (for P5b3). That file does not exist yet (checked: `ls` fails). P5c's owner-visible limits (PENDING LEAD 20 and 21, and v1.1 row V4) belong there too; the lead decides whether to add them now. This ticket does not create it.

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
- **New in revision 3:**
  - The new `_bank_context` clause (item 5(ii)): argued by reading, not run; no probe of it by me or by the resolve.
  - Which message block types the run loop builds today (T2-18's list; the builder records it).
  - Whether any audit reader (verify, export, reconcile) flags an `outbound` intent with no outcome row.
  - Whether P2d-2's look-alike check refuses a stored name inside a longer word (T2-15c's benign case).
  - P5b3's `validation_text` behaviour (cited by `tickets/P5b3.md:192-193` only) and whether its merged retry text echoes input.
  - P4c-2's `_RunEnded` mechanism (`tickets/P4c.md:13`), P4c's `alert_to` exclusion and `Runtime` check, and P4b1-b's `MeteredLLM.__getattr__`: names from frozen tickets, no code yet.
  - That `fingerprint_of` reading `self.config.backends.redactor.kind` works when a dev config names no redactor (the default `"regex"` from `backends/table.py` is assumed).

## Rules and sources cited
- **Plan:** plan-v3 sections 3, 4 (rules 3, 4, 5, 8, 9, 10), 5 (row redactor), 6 (row P5c, note 7) and 9; amendments A4, A5, A9 F6.
- **Lead orders:** 6(e), 6(g), 7(3), 8(1), 8(3), 8(5), 11(1), 11(5), 15, 16(5), 17, 19 A, C and G, 20 items 2, 4, 5 and 6; 22 items 22, 24, 27 and 30; 24 item 39; 25 item 4; 26 item 2.
- **Reviews:** `reviews/P5c-round1-adversarial.md`, `reviews/P5c-round1-correctness.md`, `reviews/P5c-round1-resolve.md`; `reviews/P5c-round2-adversarial.md`, `reviews/P5c-round2-correctness.md`, `reviews/P5c-round2-resolve.md`.
- **C1:** `studio-notes/C1-ticket-v3.md` D1-D12 and `C1-ticket-v3-FROZEN-amendments.md` F1-F14.
- **Other tickets and designs:** `tickets/P2d.md` rev 6 (:344, Rollback, L1, L5); `tickets/P1.md` rev 16 (`FOLD_VERSION`, the fold modules); `tickets/P4b1.md:249`, `:258`; `tickets/P4c.md` :8, :13, :59, :177, :180(c), :190(e) and (i); `tickets/P5b3.md:192-193`; `designs/lookalike-leak.md` draft 11 sections 8, 9, 9b and 11.
- **Lead notes:** `questions-for-lead.md` INFORM 22, 23 and 27; `handover/ledger-seed.md` rows `BL-core-c1a-*`.

## Build notes (round 3 resolve)

Source: `reviews/P5c-round3-resolve.md`, build notes BN-1 to BN-18, copied as written. These win over the text above. Ticket line numbers in the notes (for example `:216`, `:180`, `:348`) are lines of revision 3 before the banner and the new PENDING LEAD lines were added; code line numbers are disk lines as the resolve read them. Find each place by its text or name (BN-17).

**BN-1. `check` calls `_sweep` itself, with no length rule of its own (R3-ADV-1).**
- **Rule.** `check(text, session)` refuses `self_check_failed` exactly when the sweep would have changed `text`. The sweep here means `_Redactor.sweep`, the same split on placeholder tokens and the same `_sweep(placeholder, original)` / `_replace_standalone`, run over the session's map.
  - The builder may implement it by running that sweep on the text and comparing: any difference is a refusal.
  - `check` has NO threshold of its own. The ticket's "of 4 or more characters" (:216) is deleted.
  - The `forged_mark` half is unchanged and runs first.
- What this means, from `redact.py:1202-1217`:
  - an original under 3 characters: never;
  - a SECRET kind with 4 or more characters: any copy;
  - a 3-character SECRET-kind value: standalone copies only (it falls through to the identifier rule);
  - an all-digit identifier under 6 characters, or a `_COMMON` word: never;
  - any other identifier: standalone copies only.
- **T2-15 gains 5 cases.** (e) to (g) give ONE inner call and no refusal; (h) and (i) are the boundaries. Each uses a stubbed masker:
  - (e) a session TENANT `prod`, standalone in a leaf: one inner call;
  - (f) a 5-digit identifier, standalone: one inner call;
  - (g) a 2-character identifier: one inner call;
  - (h) a 3-character, non-common identifier, standalone: `self_check_failed`;
  - (i) a 3-character SECRET-kind value inside a longer word: one inner call.
- T2-15 (d) reads "a SECRET-kind value held in the session (never stored)".
- **Mutant M56** (P5c-2): `check` uses its own rule `len(original) >= 4` in place of `_sweep`. Killers: T2-15 (e) (`prod` is refused) and (h) (the 3-character value is not refused).

**BN-2. A document value equal to a word of the prompt or schema (R3-ADV-2; NEEDS LEAD 35, default (a)).**
- Default (a): the config check stays as written. It refuses, which fails closed and never leaks.
- New hostile row **T2-20** `test_planted_config_word_refused_not_sent`:
  - a made-up document line `tenant_id=<a standalone word of the system prompt>` (not a `_COMMON` word) puts that word in the session;
  - the next call gives `self_check_failed`, zero inner calls and no `outbound` row;
  - through the run loop, the run ends NEEDS_PERSON `redaction_error` (BN-9).
- **False-abstain ceiling (new, rule false-abstain-reporting).** The builder runs the 10 golden inputs and every repository fixture document through the wrapper with each fixture agent's prompt, and writes the count of `self_check_failed` refusals to `P5c-2-false-abstain.txt`.
  - The ceiling is 0 on that set. Any refusal there fails the build, and the builder names the shared value.
  - The live rate is unknown, and the README says so in the "not masked" list item (g): "a document value that equals a word of the agent's prompt or schema stops the run for a person".
- If the lead answers (b): add `RunCtx.trust_config(system, tools, output_schema)`.
  - It can be called once per run, before the first chat. The run loop and the gate call it with their registry-built config; the judge registers its constant `PROMPT`/`SCHEMA`.
  - `check` skips a config leaf that is byte-identical (system) or equal by canonical-JSON sha256 (tools, schema) to the trusted one. A caller-built `extract` `system` is still checked in full.
  - Adds one row (T2-20 then asserts ONE inner call) and one mutant.
- If the lead answers (c): drop the `self_check_failed` half of the config check (`forged_mark` stays), and cut T1-15 and M12.

**BN-3. What `close()` does to the seeded map (R3-ADV-3).**
- `MaskSession.close()` sets `_closed`, then empties the seed (`self._map.clear()` and `self._map.redact_cache.clear()`), then sets `self._map = None`.
- It runs in `handle`'s `finally`, after the last map save. On today's tree no use of `rmap` follows the `with` block (Facts). The builder re-checks this on the P4c-2-rebased file and records it in the evidence.
- **G6 is closed for the run loop's map:** after the run, the originals are gone from that object.
- What stays, stated in Security notes ("The plain run map") and the README "where personal data is kept":
  - the caller's own `mapping` dict (`handle` copies it: `RunMap(mapping or {})`);
  - the stored kinds in the store.
- Ticket :180 reads "a session that cannot be copied and whose run map is emptied when the run ends". Problem item 3 reads "The masking state of a run can be copied, and it outlives the run."
- **Row T1-06b** `test_close_empties_the_seed_map`: a seeded `RunMap` holding 2 made-up entries is empty after `close()`, and `redact_cache` is empty.
- **Mutant M57** (P5c-1): `close()` leaves the seed untouched. Killer: T1-06b.

**BN-4. Weak keyword plus digits (R3-ADV-4; NEEDS LEAD 34, default (c)).**
- Default (c): a WEAK form (`account`, `accounts`, `acc`, `acc.` with no suffix) also counts as bank context, EXCEPT when the digit group, without separators, has exactly 12 digits.
  - Then BANKACCT leaves the match, and ACCOUNTID (`redact.py:353`) masks it as today, so cloud audit lines `account <12 d> assumed role` keep their kind (pin `test_redaction_bank.py:296-298` unchanged).
  - The clause becomes `_ACCT_STRONG.match(m.string, m.start(), m.start(1)) is not None or len(re.sub(r"\D", "", m.group(1))) != 12`.
  - Nothing with an account keyword and 6-17 digits then reaches the model in clear.
- **ACC-2-NEG is renamed ACC-2-WEAK** (FB). It has 11 cases:
  - each of the 4 weak forms with 8 made-up digits: masked BANKACCT, digits absent, keyword kept;
  - each of the 4 weak forms with 12 digits: ACCOUNTID;
  - `Account: <5 digits>`: not masked (under 6);
  - `Account (no): <8 d>` and `Account (number): <8 d>`: masked (R3-COR-8).
  - M16 keeps a killer: a bare `account` made strong turns the 12-digit cases into BANKACCT.
- **Mutant M71** (P5c-1): the "not 12 digits" carve removed. Killer: ACC-2-WEAK's 12-digit cases.
- **Existing pins that change (listed in the evidence, never weakened):** `test_redaction_bank.py:240-241` (`account <8 d>` becomes masked) and `:289-292` (W2: an 8-digit account past the window becomes masked). README item (b) reads "plain account numbers with no account keyword".
- If the lead answers (b): rewrite ACC-2-NEG as strict-xfail record ACC-2-WEAK-LEAK (5 cases plus the two parenthesised cases, which still kills M16 when it XPASSes) and drop M71.
  - V4 gains "a weak keyword (`account`, `accounts`, `acc`) plus 6-17 digits".
  - README (b) names that form, and the owner-visible limits file lists it.
  - Strict xfails go to 5.
- If the lead answers (a): drop the 12-digit carve and M71. The pins `:296-298` also change (cloud ids written `account <12 d>` become BANKACCT, never put back).

**BN-5. The exact `_ACCT_STRONG`, one source table, shape cases (R3-ADV-5, R3-ADV-7, R3-ADV-11, R3-COR-8).**
- In `redact.py`, replacing the literal at `:82` with the same bytes built from parts:
  ```
  _ACCT_SUFFIX = r"(?:number|num\.?|nbr\.?|no\.?|#)"
  _ACCT_WORD = r"(?:accounts?|acct\.?|acc\.?|a/c)(?:[ _\-\xa0]?" + _ACCT_SUFFIX + r")?"
  _ACCT_STRONG = re.compile(
      r"(?i)(?:bank[ _\-]?)?(?:accounts?[ _\-\xa0]?" + _ACCT_SUFFIX
      + r"|acct\.?|a/c|acc\.?[ _\-\xa0]?" + _ACCT_SUFFIX + r")"
  )
  ```
- **No tail and no DOTALL.** `Pattern.match(string, pos, endpos)` anchors at `pos` and does not need to reach `endpos`. So the separator text (`_BANK_KV`: quotes, marks, `:`, `=`, `#`, a dash, one line break) is never matched by `_ACCT_STRONG`. Probe 1 and probe 2 (Facts) show the line-break and JSON-key forms read as strong.
- **ACC-2 gains 13 cases (59 to 72)**, each with the three assertions (digits absent; keyword kept; one BANKACCT entry equal to the digits):
  - separator between keyword and suffix: `_`, `-`, nbsp (3);
  - `Account No:` + line break; `"account_no": "<d>"`; `\"acct\":\"<d>\"`; `*Acct No:* <d>`; `Acct = <d>`; `A/C # <d>`; `Account Number - <d>` (7);
  - digits `4-4` dashed and `4 4` grouped (2);
  - **context from another clause** (R3-ADV-7): `<BANKCODE_1> Account No: <d>`. Under M50 the keyword becomes the value and the digits stay, so "digits absent" fails. This is the Blocker's own failure mode (1).
- **New row ACC-TABLE** (P5c-1 patterns):
  - `_ACCT_WORD` equals the `:82` string byte for byte;
  - each of the 59 table strings fullmatches `_ACCT_WORD` and matches `_ACCT_STRONG`;
  - each weak form fullmatches `_ACCT_WORD` and does not match `_ACCT_STRONG`.
- **New row ACC-GROUPS:** each `PATTERNS` entry labelled BANKACCT has `pattern.groups == 1`.
- **Mutant M58** (P5c-1): `_ACCT_STRONG` drops `[ _\-\xa0]?`. Killer: ACC-2's `_`, `-` and nbsp cases.
- The reviewer's DOTALL mutant is not added: with no `.` in the pattern it is an equivalent mutant.

**BN-6. Bare 12-digit numbers (R3-ADV-6; NEEDS LEAD 36, default (b)).**
- Default (b): `defaults.py` gains `DEFAULT_STORED_KINDS` = `STORED_KINDS` minus ACCOUNTID (11 kinds).
  - `Config.evidence.stored_kinds` defaults to it (`config.py:215`).
  - `STORED_KINDS` stays the 12-kind allowed set (T4-11 unchanged), so a config that names ACCOUNTID loads (`:256`).
  - `DEFAULT_STORED_KINDS` joins `MASKING_VALUES` (BN-16).
- A cloud-operation agent writes `evidence.stored_kinds` with ACCOUNTID, and its config hash shows it.
- **Row T4-13** `test_bare_12_digits_not_stored_by_default`: with the default config, a bare made-up 12-digit number is masked ACCOUNTID and absent from the stored map. With `stored_kinds` naming ACCOUNTID it is stored.
- **Mutant M70** (P5c-4): the default includes ACCOUNTID. Killer: T4-13.
- The builder lists every existing test and fixture that relied on an ACCOUNTID put-back (4 files name ACCOUNTID; reliance UNVERIFIED) and adds the field there. The check is never loosened.
- Security notes (b) and the CHANGELOG line read "a bare 12-digit number is masked; it is stored and put back only for an agent whose config lists ACCOUNTID".
- If the lead answers (a): T4-13 and M70 drop, and the README and a hostile row ACC-12c pin "a bare 12-digit bank number is stored and can be put back into a plan".

**BN-7. Judge qualification runs inside runs (R3-COR-1).**
- `judge.qualify` keeps its signature. For case `i` it opens `with judge.llm.run(f"gate-judge-{tag}-{i}", "gate") as ctx:`. `tag` is one `uuid4().hex` per call of `qualify`.
- It escapes the raw golden text with `judge.llm.redactor.mask(case["text"], ctx.session, untrusted=True)`, then calls `injection_check`.
- Results:
  - `RedactionError` (now re-raised by `injection_check`): the case FAILS (the docstring's "a judge error fails its case");
  - `AuditUnavailable`: propagates, so the gate stops and is never GREEN (BN-8, T3-10b).
- `JudgeDetector.check` takes the run's session for its own re-mask through a new read-only `MaskedLLM.current()` (it returns the `RunCtx`, and raises `SessionClosed` outside a run). It calls `self.llm.redactor.mask(text, self.llm.current().session, untrusted=False)`. So the judge row in `producers.py:28` becomes `{"mask"}` and the AST guard stays real (see BN-8).
- **Row T3-10c** `test_gate_judge_qualification_runs_in_runs`: a gate with an `llm_judge` completes, makes one run per judge case, and raises no `SessionClosed`. A judge case holding a forged `<EMAIL_9>` arrives escaped.
- **Mutant M59** (P5c-3): `qualify` calls without a run. Killer: T3-10c.

**BN-8. The gate's exact calls (R3-COR-2).**
- **(b) One run per CASE.** Each case opens `with llm.run(f"gate-{tag}-{case_id}", "gate") as ctx:`, and its k calls run inside it. The document is decoded and escaped ONCE, before the k loop, as on disk. T3-10's name ("fresh per case") stands. Ticket :348's per-(case, k) run id is void.
- **(a) The call:** `doc = llm.redactor.mask(decode_document(raw), ctx.session, untrusted=True).encode("utf-8")`. `runmap.redact_untrusted` is no longer called in `gate`.
- **(c) Order of handlers:** `except RedactorRefusal as exc` with `exc.code == "unsupported_input"` comes FIRST. The case then counts as FAILED with reason `unsupported_input` (`case_passes = 0`, no model call, all k counted failed). Every other `RedactionError` keeps the `ConfigError` branch (exit 2).
- **`producers.py` and `tests/test_k5_producers.py` (T3-17):**
  - the gate row (`:40`) becomes `frozenset({"mask"})`, and so does the judge row (`:28`) (BN-7);
  - `CHOKE_FAMILY` gains `"mask": "guard/redactor.py"`, so `test_every_redaction_function_reaches_the_one_choke_point` proves `mask` reaches `redact_text`;
  - `REDACTORS` gains `"mask"`.
- **Mutants:** M60 (P5c-3): `RedactorRefusal` falls into the `ConfigError` branch. Killer: T3-05b, which then sees exit 2, not a FAILED case. M65 is in BN-14.

**BN-9. Wrapper refusals at the chat call (R3-COR-3).**
- The chat block (`agent_loop.py:424-439`) catches, in this order:
  - `AuditUnavailable`: NEEDS_PERSON `audit_unavailable`;
  - `RedactionError`, `RedactorRefusal` included: `self._redaction_failed(run, cited)`;
  - then `ProviderError` as today.
- **Row T3-13b** `test_wrapper_refusal_at_chat_needs_person`: parametrised over `forged_mark`, `self_check_failed` and `unsupported_input` (non-text block). The run ends NEEDS_PERSON `redaction_error`, is not left in WORKING, and makes zero inner calls for that step.
- **Mutant M61** (P5c-3): the `RedactionError` clause removed. Killer: T3-13b.

**BN-10. No reassignment around the wrapper (R3-COR-4).**
- `Runtime` keeps the model in `self._llm` and exposes a read-only `llm` property (no setter).
- `MaskedLLM` has `__slots__` and a `__setattr__` that raises `AttributeError` once `__init__` is done.
- The 5 sites (Facts) build their fake with the wanted behaviour before `Runtime` (or patch the raw model object they hold). They are never rewritten to patch around the wrapper.
- Evidence gains `git grep -n -E 'rt\.llm( |\.chat) ?=' HEAD -- tests demos`, which must print nothing at the head.
- **Row T2-19** `test_wrapper_attributes_read_only` (P5c-2): assigning `chat`, `inner` or `redactor` raises. **Row T3-06c** `test_runtime_llm_read_only` (P5c-3).
- **Mutants:** M62 (P5c-2): the `__setattr__` refusal removed. Killer: T2-19. M63 (P5c-3): `llm` a plain attribute. Killer: T3-06c.

**BN-11. Strict decode placement (R3-COR-6).**
- In `handle`, `decode_document(document)` runs in its own `try` right before the `redact_untrusted` `try` (`:366`). `except RedactorRefusal` gives `_note(... "unsupported_input")` and then `_abstain(... "unsupported_input")`. The generic `except Exception` (`:376`) never sees it.
- `unsupported_input` is NOT added to `GUARD_STOP_REASONS`. It is a failure to produce a proposal, like `document_too_large` (`:80-85`), so it has no `caught_by`.
- T3-05 asserts the events in order as a subsequence: `received`, then the `guard`/`document` `stopped` event. The `state` WORKING event lies between them (`test_s5_runtime.py:137`).

**BN-12. Map saved after each chat (R3-COR-7).**
- Right after `self.llm.chat(...)` returns, and before the reply is used, the run loop calls `self._save_map(run, rmap)` in its own `try`. A failure goes to `_evidence_unavailable(run, cited, "map")`.
- **Row T3-19** `test_map_saved_after_each_chat`: `validate_proposal` is None and the model's first reply text holds a raw made-up e-mail. After the second call, the stored map holds the EMAIL entry the wrapper minted.
- **Mutant M64** (P5c-3): the post-chat save removed. Killer: T3-19.

**BN-13. Mutant file in every sub-PR (R3-ADV-8).** The Files lists of P5c-2, P5c-3 and P5c-4 each add "extend `tests/p5c_mutants.py` with this PR's mutants". P5c-2's "No other file" reads "No other `src/` file".

**BN-14. Mutants for unguarded rows (R3-ADV-9).**
- M65 (P5c-3): the gate decodes with `replace`. Killer: T3-05b.
- M66 (P5c-3): `extract` decodes with `replace`. Killer: T3-05's `extract` case (T3-03e).
- M67 (P5c-3): `cli gate` writes `qualified.jsonl` after `AuditUnavailable`. Killer: T3-10b.
- M68 (P5c-3): `_screen` drops the `AuditUnavailable` catch. Killer: T3-12b.
- M69 (P5c-3): k1b's thread runs `work` without `copy_context()`. Killer: T3-11b.
- `_RunEnded` is P4c-2's code with P4c's own mutants. A broken end through it fails T3-12 and T3-12b here.
- M39's killer T4-02 is written once the P2d-2 marker form is read (PENDING LEAD 11). The Done line reads "every listed mutant killed, M39 included once T4-02 exists; if the marker form is still unknown at P5c-4, the lead decides before merge".

**BN-15. T2-P is a measurement (R3-ADV-10).** T2-P runs alone and writes its time to `P5c-2-perf.txt`. It has no pass/fail budget and is not counted in the Done gate or in the row totals. A budget number becomes a gate only by a lead order.

**BN-16. Fingerprint formula (R3-ADV-12).**
- `FINGERPRINT = "regex@" + REGEX_VERSION + ":" + FOLD_VERSION + ":" + sha256(b"".join(rel_path.encode("utf-8") + b"\0" + sha256(lf_bytes).digest() for rel_path in MASKING_SOURCES) + b"\0" + repr(MASKING_VALUES).encode("utf-8")).hexdigest()[:16]`.
- `rel_path` is the path under `hadavin_sdk/`, with `/`.
- `MASKING_VALUES` gains `DEFAULT_STORED_KINDS` (BN-6) after `STORED_KINDS`.
- A missing `.py` source (bytecode-only install) keeps the fail-closed import error. The CHANGELOG states "installs must ship sources".
- T1-02 adds: swapping the contents of two listed files changes the fingerprint.

**BN-17. Cites by name (R3-ADV-13, R3-COR-5, R3-COR-9).**
- At P5c-1's base the builder re-reads by name every `runmap.py`, `agent_loop.py`, `tools.py`, `evals.py` and `k1b` cite in the ticket, and writes the "name -> line at base" table into the evidence. The result review checks that table at the PR head.
- The NAME-DECOMPOSED argument cites "the second pass over the canonical view in `redact_text`". It is at `:452-471` on disk, so at about `:499-518` at `124258b` (offset only, UNVERIFIED).
- The judge comment is `judge.py:69-70`.

**BN-18. Counts after BN-1 to BN-17 (defaults of NEEDS LEAD 34, 35, 36).**
- Rows (each counted once in its own sub-PR):
  - P5c-1 redactor 17 (+T1-06b);
  - P5c-1 patterns 16 (+ACC-TABLE, ACC-GROUPS; ACC-2-NEG renamed ACC-2-WEAK);
  - P5c-2 19 (+T2-19, T2-20);
  - P5c-3 36 (+T3-06c, T3-10c, T3-13b, T3-19);
  - P5c-4 13 (+T4-13).
  - **101 rows**, plus the T2-P measurement. Strict xfail: 4 (unchanged).
  - ACC-2: 72 cases. ACC-2-WEAK: 11 cases. T2-15: 9 cases (a-i).
- Mutants:
  - P5c-1 22 (+M57, M58, M71);
  - P5c-2 17 (+M56, M62);
  - P5c-3 21 (+M59, M60, M61, M63, M64, M65, M66, M67, M68, M69);
  - P5c-4 6 (+M70).
  - **66 mutants** (M56-M71 new). Done's "50 of 50" reads "66 of 66".
- Other answers:
  - NEEDS LEAD 34 (b): 101 rows, 5 strict xfail, 65 mutants.
  - NEEDS LEAD 36 (a): 101 rows (ACC-12c replaces T4-13), 65 mutants.
  - NEEDS LEAD 35 (b): +1 mutant. (c): -1 row (T1-15) and -1 mutant (M12).

**BN-19. Lead answers to NEEDS LEAD 34, 35, 36 (orders 29-30, items 64-66).** These lines win over BN-18's "Other answers".
- NL-34 (item 64): option (c). A weak keyword followed by digits counts as bank context except at exactly 12 digits. Add a measurement row that counts false refusals on the benign golden set and writes the figure to the evidence folder. If the figure exceeds the ticket's stated bound, report it to the lead; do not loosen the rule silently.
- NL-35 (item 65): option (a). Keep the refusal; hostile row; ceiling 0 on the golden set.
- NL-36 (item 66): option (b). Store a bare 12-digit ACCOUNTID only when an agent's config lists ACCOUNTID. No other path stores it.
- Counts: the measurement row is a measurement, not a pass/fail row (like T2-P). Rows stay 101, mutants stay 66, as in BN-18.

**BN-20 (lead order 35). Options paragraph: a client's own gateway for masking.** Scope of this ticket is UNCHANGED. Ticket text only; no build, no round.
- (a) Our redactor (default, as ticketed).
- (b) A client's own LLM gateway or masking service (LiteLLM, Portkey, Kong AI Gateway and Concentrate are named only as examples) as an optional second layer. Trigger: a client already runs a gateway. Outlined as a v1.1 row: an adapter only, tested against a fake gateway; no vendor import outside its kind module.
- An adapter cannot give these unless the gateway gives them itself: restoring masked values in our code (not in the gateway); our coverage of look-alike letters and encoded or re-spelled copies of a known value. In the lead's test the default Presidio analyser missed 13 of 30 hostile inputs (plain keys, a password assignment, and full-width, Cyrillic, zero-width, percent-coded and HTML-entity spellings) and flagged 7 of 14 lines that must stay readable (`reviews/gateway-check-lead-reading-1.md`). So a gateway layer is never a replacement for this redactor.

**BN-21 (lead order 41 item 91). A provider request id is masked like every other logged fact (relay from P5b1 BN-7, P5b1 PENDING LEAD 27).**
- **Source and reason.** `reviews/P5b1-round3-resolve.md` BN-7: after P5b1, `ProviderError.request_id` holds one of two closed shapes (`req_` plus 8 to 36 letters and digits, or a UUID), but a hostile provider or a server in the middle still chooses its characters, so it can carry a short word or a letters-and-digits run of a secret. It gets no exemption from masking.
- **Rule for P5c.** No code that P5c adds or changes writes a `request_id` (or any other `ProviderError` fact) to the audit trail, the run store, a card or a log without passing it through the redactor's one choke point (`redact_text`, reached through `mask`, as `CHOKE_FAMILY` proves, BN-8) first. There is no allow-list entry, no `trust_config`-style exemption and no "safe by shape" rule for it. Today nothing writes it: the chat block's `except ProviderError` (`runtime/agent_loop.py:432-438` on ce70eb5, the "`ProviderError` as today" branch of BN-9) audits only `error_code` through `_note` (`:229-230`, an `AuditEvent` via `_event`, `:219-227`) and ends the run NEEDS_PERSON. That stays so. The wrapper's outbound audit event (`write_intent`, item (e) of the wrapper) holds only the masked body's hash and counts, unchanged.
- **Row T3-20** `test_provider_request_id_not_written_raw` (P5c-3): the inner model raises `ProviderError("x")` whose `request_id` is a made-up id built from parts (`"req_"` plus a letters-and-digits canary run), set by the P5b1 keyword, or by plain assignment if P5b1 is not merged at P5c's base (as P5b1 R18 builds its instances). Expected: the run ends NEEDS_PERSON `provider_error`; the canary appears in no audit event (every field of every `write_intent` and `write_outcome` call), in no store record of the run and in no card text. NEW.
- **Mutant M72** (P5c-3): the chat block's `_note` gains `result=f"failed {exc.request_id}"` (the raw id written to the audit trail). Killer: T3-20.
- **Counts (supersede BN-18 and BN-19):** P5c-3 37 rows (+T3-20), **102 rows**, plus the T2-P measurement; P5c-3 22 mutants (+M72), **67 mutants**. Done's "66 of 66" (BN-18) reads "67 of 67". Each "Other answers" count of BN-18 also gains 1 row and 1 mutant.

## Build note after the freeze (lead order 53 item 2, genericity audit; continues the BN numbering above)

**BN-22 (genericity audit finding G-13, lead order 53).** Wording only: the scope sentence (line 3, "decides which parts of an invoice reach a model") and the path class (line 144, "bank numbers on invoices") read "documents that carry bank details (for example an invoice)". Seven "invoice" mentions in all; Intake stays as the named example and trigger. Rows, types and constants are unchanged (no invoice-named field).
Build note only; the freeze is not reopened.

**BN-23 (RUNG TABLE, lead order 56, R448).** Gate of R448 / preamble rule 20 for this ticket. Source: `reviews/rung-audit-1-part-D.md` (2026-11-06; tool facts marked RAN were run on made-up files outside the repo, READ-WHEEL means read in the installed package; the docs hosts docs.astral.sh, docs.litellm.ai and semgrep.dev were not reachable, so facts from memory are UNVERIFIED). Rows copied from the audit; no verdict changed. Ticket stays frozen.
Size: 1013 lines, over about 250. Redaction path; 7 rows. Candidate to split (lead decides); the audit says the cost is the ticket size, not the rung.

| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| Detection engine (patterns) | already on main: `guard/redact.py`, `guard/runmap.py`; P5c does NOT port it (`P5c.md:131`) | 5: Microsoft Presidio; Protect AI LLM Guard Anonymize/Deanonymize | UNVERIFIED (no docs fetched; Presidio MIT-licensed from memory: UNVERIFIED) | Not built in P5c, nothing to cut. Presidio fits as the second `redactor` kind (R363 working alternative, outline with a trigger such as name recall on a golden set), not a replacement | KEEP (already built; no change) |
| `Redactor` protocol, `regex` kind, kind wiring | G1, item 2 (`:117`, `:238-247`) | 1: the kind system (reused) | ticket | n/a | KEEP-CODE |
| `MaskSession` (no copy, no pickle, closable, seeded with run map) | item 3, rule F10 | none | n/a | Run-scoped state that cannot leak after the run | KEEP-CODE |
| Computed fingerprint in `config_hash` | items 4, 6, BN-16 | none | n/a | Evals that gate: a masking change forces a new qualification run | KEEP-CODE |
| Account-number pattern rows (PHONE end, `_ACCT_STRONG`) | item 5, BN-4 to BN-6 | 5: Presidio recognizers (UNVERIFIED) | UNVERIFIED | Fixes to the engine already in use | KEEP-CODE |
| `MaskedLLM` single door (re-mask, check, audit before call, strict decode, `MaskedLLM(MeteredLLM(raw))`) | item 7 (`:268-299`) | 5: gateway guardrails (LiteLLM Presidio pre-call masking: UNVERIFIED) | UNVERIFIED | Redaction BEFORE text leaves our process (a gateway masks after); audit intent before the call; meter counts the masked body; one door enforced by type | KEEP-CODE |
| Put-back (stored kinds only, never a folded spelling, three seams; PHONE out of `STORED_KINDS`) | item 8; G9, G10 | 5: Presidio deanonymize (UNVERIFIED) | UNVERIFIED | Stored-kinds rule and "no regulated number put back into a plan an executor may act on" (money-adjacent) | KEEP-CODE |

Build only; the freeze is not reopened.

**BN-24 (genericity audit G-6 APPROVED WITH CONDITIONS, lead order 58 item 2; redaction path: the review of this note is a SECURITY review with NO round cap).** The P5c-1 redactor kind gains a setting `kept_host_suffixes: tuple[str, ...] = ()`. `_KEPT_HOST` (`guard/redact.py`) is built from it. DEFAULT EMPTY, so `.cluster.local`, `compute.internal` and `ec2.internal` names are MASKED by default; the old keep-behaviour is NOT the default. A project lists the suffixes its tools act on. Conditions: (a) validation: each entry a plain DNS suffix, no wildcard, no empty string, a maximum length (the builder names the number in config, not in code); a malformed entry refuses start; (b) each use that keeps a name is logged in the audit; (c) stages `pilot` and `prod` refuse a non-empty list unless the project config carries an approval record for it (the record's shape is an open question for the builder's review, UNVERIFIED); demo stage allows it. Tests (named rows): default config masks `api.svc.cluster.local`, a `compute.internal` name and an `ec2.internal` name; a listed suffix keeps only names ending in that suffix and masks the rest; a malformed entry (wildcard, empty, over-length) refuses start; pilot and prod with a non-empty list and no approval record refuse start; the audit records a kept name. Mutants: default list non-empty; wildcard accepted; no audit write; stage gate removed. Counts not recomputed (UNVERIFIED). Relay: P2d redact interface (reads the setting only).
