# P5b5 round 1 resolve (egm:egm-resolve, AUTO mode, Opus 5.5)

**Status:** resolved (AUTO: no interactive gate, by the lead's order 20 item 6 instruction). Ticket NOT edited; this file is the input for revision 2.
**Target:** `handover/tickets/P5b5.md` revision 1, full file (145 lines).
**Findings:** `reviews/P5b5-round1-adversarial.md` (R1-ADV-1..18: 1 Blocker, 8 Major, 7 Minor, 2 Nit) and `reviews/P5b5-round1-correctness.md` (R1-COR-1..13: 4 Major, 7 Minor, 2 Nit). 31 ids.
**Gate:** order 20 item 6 (cap 3 rounds counting from round 1; redaction ticket: one extra round only if the last round had no Blocker and at most 2 Majors). This is round 1. Round 2 is due on revision 2.

**Facts checked by me (cheap, raw commands in this session):**
- F-a. `git -C /home/user/hadavin-sdk-handover show cd2243f:src/hadavin_sdk/guard/runmap.py | grep -n "def safe_head"` gives **532**. The on-disk `src/` (branch `core/cloud-handover`, an older `src/`) gives 485. `git diff --stat HEAD cd2243f -- src` shows `guard/runmap.py` +61 lines. Both reviewers read the on-disk tree, not `cd2243f`. The ticket's line is right.
- F-b. `git grep -n "safe_head(" cd2243f -- src/hadavin_sdk` finds exactly 5 calls: `extract.py:58`, `guard/injection.py:96`, `k1b/loop.py:187`, `:194`, `runtime/tick.py:292`. This matches the ticket's F2. The ast-walk output itself was never saved (ADV-16).
- F-c. Python 3.13.18, `inspect.getsource(http.server.BaseHTTPRequestHandler.log_message)`: the default body is `sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), ..., message...))`. It writes directly to `sys.stderr` and never goes through `logging`. If the override at `receiver.py:62` were deleted, the client address and request line would go to stderr, and a `caplog` test would not see them.
- F-d. `tickets/P5b3.md:131`: "`approvals/receiver.py:62-63`: the body becomes `return`. The override stays...". `tickets/P5b4.md:59` and `:181` say instead that P5b3 "removes" `log_message`, which is a wording conflict. P5b3's mutant M25 (`:280`) is killed by `test_receiver_logs_nothing`, "a `caplog` check at DEBUG". Per F-c, that test does not catch deletion of the method.
- F-e. Ownership of the F1 rows:
  - L1 (`_message`, `_DRIVERS`): deleted by P5b3 (`P5b3.md:123`, `:185`).
  - L2 (extract): P5b3 `:128`.
  - L3 (injection): P5b3 `:129`.
  - L4 `refused:`: P5b3 `:111` (`_refusal_text`).
  - L4 debug branch: rewritten by BOTH P5b3 `:118` ("diagnostic plus `chain=`") and P5b4 `:118` ("one Grammar A line"). They conflict.
  - L5 `basicConfig`: P5b4 `:147`.
  - L6 (receiver no-op): P5b3 `:131`.
  - L7 (producers rows move to `DIAGNOSTIC_WRITERS`): P5b3 `:130`.
  - Nothing in L1-L7 is left to P5b5.
- F-f. `git grep -n -E "import traceback|from traceback|basicConfig|exc_info|stack_info|\.exception\(" cd2243f -- src/hadavin_sdk` finds only `cli.py:32` and `cli.py:287`. In P5a, P5b1 and P5b4, the traceback module appears only in test or corpus text (`P5a.md:89`, `P5b1.md:259`). P5b4's formatter drops `exc_info`, `exc_text` and `stack_info` "every time" (`P5b4.md:88`, mutant K2 killed by U6).
- F-g. P5b4's exit table (`P5b4.md:103-116`, U19 `:216`) has 9 rows. Its `run_tick` row is "0, 1, 2 or 4". At `cd2243f`, `runtime/tick.py:337, 350` returns 2 (`STORE_NOT_READY`). `cli.py:200` returns 4 (kill switch, store unreachable) and `cli.py:194` returns 3 (audit, store unreachable); P5b4's table does not list those two.
- F-h. `P5a.md:89`: `LEDGER_IDS` = `BL-core-c18a-001..051`; each id has exactly one BASE row. `P5a.md:70`: `STEPS` ends `"R2", "R5"`.
- F-i. `cd2243f:tests/test_p7_tick.py:606-617`: `_psycopg_error` builds fakes with `__module__ = "psycopg.errors"`; the pins are at `:613-617`. `:284` already calls `serve(app.approvals, port=0)`, so a real-socket receiver test is cheap.
- F-j. `guard/producers.py` at `cd2243f`: `safe_head` is one of six `CHOKE_FAMILY` members. The other stores of model or document text (card text, approval summary, evidence, tool results, judge input, eval case) are rows calling `redact_text`, `redact_untrusted`, `redact_value`, `redact_layered`, `redact_bounded` or `clean`, and `tests/test_k5_producers.py:46-53` pins them. That test asserts the function exists ("does not exist") and that it calls a listed name. It is unchanged between `cd2243f` and HEAD.
- F-k. `pyproject.toml:6` is `requires-python = ">=3.12"`. CI runs Python 3.13 (`.github/workflows/ci.yml:73`, `:109`) and `bandit -q -r src demos -ll` (`ci.yml:119`), the same command as the ticket.
- F-l. `P4a.md:96, :105` edit `run_case` (merges before P5b5). `P5c.md:66` edits `k1b/loop.py` (after P5b5). `P5c.md:135` (PENDING LEAD 12) recommends dropping P5b5 from P5c's Depends-on.
- F-m. Order 21 item 17 gives the standing S0 EXIT to P5a and P5b1 to P5b5, effective after freeze and the build-start review.

**Honest note (what I did NOT check):**
- I did not read `design-v3.md` or the D-amendments in full. I only grepped D11 and D12; D12 at line 50 has the `tick-fd2.log` / `capture_fd2` text.
- I did not read memo-5, or P5a, P5b3 and P5b4 in full. I read the sections cited above.
- I did not read P8b's T6 wording check, only its file list (`P8b.md:137`).
- I ran no test and no probe of the proposed checker.
- There is no P5b4 head, so every "expected empty at P5b4 head" below is a prediction that step 0 must measure.
- I did not verify that P5a's built `diagnose` will not import `traceback` in `src/`. That is why the allow-list below is measured, not assumed empty.
- The skill's default output name (`goldfish_review_report.md`, per-finding layout) was replaced by the file name and layout the caller ordered.
- I did not edit the ticket and did not write DECISIONS.md.

## Is P5b5 now only tests plus a page?
**Yes.** F-e shows that P5b3 and P5b4 (both revision 1) own every deletion L1-L7. Revision 2 should say: **P5b5 changes no file under `src/`**. It creates:
- `tests/test_diagnostics_legacy_gone.py`;
- one block in `tests/test_diagnostics_hostile.py` and the `CORPUS_STEP = "R5"` bump;
- `docs/diagnostics.md`;
- `tests/diagnostic_r5_mutants.py`;
- one CHANGELOG line.

The conditional "Change, only if step 0 finds the leftover" list (ticket :59) is deleted. Step 0 keeps only the STOP rule: if a leftover is found, the builder stops and reports, and the owning package fixes it. The builder never deletes it in P5b5. The path class stays **redaction** (ADV-12): the pins guard what may still turn foreign text into output.

## Decisions for revision 2
| id(s) | category | decision for revision 2 |
|---|---|---|
| R1-ADV-1 (Blocker) | PROPOSE FIX | State in Interface and Security: `Handler.log_message` MUST stay as an override whose body drops `format` and `args` (P5b3 `:131`). Deleting it is a leak: the stdlib default writes the client address and request line to `sys.stderr` (F-c). Rename the rule `server_log_passthrough` to **`server_log_noop`**: `approvals/receiver.py` must define `log_message` inside class `Handler`, and its body, after an optional docstring, is exactly one `return` or `pass`. Missing or anything else is a finding. Add test **R4b `test_receiver_writes_nothing_to_stderr`**: `serve(approvals, port=0)` as at `test_p7_tick.py:284`, one real POST in a thread, then `capfd` stderr has no address and no path. Add mutant **M7b "delete the method"**, killed by R4 and R4b. M7 (forwarding body) is killed by R4. |
| R1-ADV-2, R1-COR-2 | PROPOSE FIX | Rewrite the header, Depends-on and UNVERIFIED with "depends on P5b4 rev 1 and P5b3 rev 1 (drafts, not clean)". Replace F1's "Replaced by" column with the owner and line from F-e. Delete the conditional change list (ticket :59) and PENDING LEAD 6. Keep the STOP rule (PL 7). Name the debug-branch double ownership as a coupling (C3), not a P5b5 task. |
| R1-ADV-3 | PROPOSE FIX | Add plant **P7 `run_case` loses its `safe_head` call** on a `tmp_path` copy. The equality check must report the missing pair. M16 (subset instead of equality) is then killed by P7. |
| R1-ADV-4 | PROPOSE FIX | After the cuts in ADV-5 and COR-9, four rules remain: `safe_head_caller`, `server_log_noop`, `traceback_import`, `basic_config`. Each rule gets at least one plant and one "rule removed" mutant. Required alias plants: `from hadavin_sdk.guard.runmap import safe_head as sh`; `runmap.safe_head(...)`; `import traceback as tb`; `from traceback import print_exc`; `from logging import basicConfig as bc`; `logging.basicConfig(...)`; a deleted and a forwarding `log_message`. Keep the syntax-error file plant. |
| R1-ADV-5 | PROPOSE FIX (cut) | **Cut rule `exc_info_arg`** (and M6, M14, plant P5). P5b4's handler drops `exc_info`, `exc_text` and `stack_info` on every record (`P5b4.md:88`, K2 and U6), and P5b3's taint guard lists `exc_info=` and `.exception(` as OBJECT sinks. That also ends the `.exception(` receiver problem. **Replace the 6-name `traceback_print` call list with `traceback_import`:** any `import traceback` or `from traceback import ...` in `src/` is a finding unless `(file)` is in `TRACEBACK_IMPORTERS: Final = frozenset()`, with equality semantics. Step 0 runs the checker at the P5b4 head and records the measured set. If it is not empty, each entry needs a reason line in the ticket, or the builder stops and reports. On `cd2243f` the only importer is `cli.py:32` (F-f). |
| R1-ADV-6 | PROPOSE FIX | Add the evidence (F-j): `safe_head` is one of six choke-family members. Every other store of model or document text is a `PRODUCERS` row on another member, pinned by `test_k5_producers.py`. After P5b3, `last_error` and `DeadLetter.errors` hold closed text only (`render`, `validation_text`), so they need no cleaner. Add the rename rule: a pull request that renames or splits `run_case`, or adds a caller, updates `SAFE_HEAD_CALLERS` in the same PR with a reason. The equality failure is the intended review point. Step 0 measures the set at the P5b4 head, after P4a has edited `run_case` (F-l). Relay to P5c (C6). |
| R1-ADV-7 | PROPOSE FIX (cut) | Fix the page format: two tables, headed `\| Code \| Meaning \|` and `\| Fact \| Meaning \|`, with the first cell in backticks. R7 reads only the first column and requires equality with the `Code` / `FactKey` members. **Cut page item (4), the exit codes, from the page and from R7.** P5b4 owns the exit table and its tests (U19), and a copy drifts. The page links to P5b4's CHANGELOG entry instead (PL 10). |
| R1-ADV-8 | PROPOSE FIX | Cite P5b4's canary test as **S1** (`P5b4.md:222`, file `tests/test_output_guard_process.py`) and U19/U20. Add `tests/test_taint_guard.py` (P5b3 `:139`), `tests/test_output_guard_process.py` and R4b to the evidence command at the P5b5 head. |
| R1-ADV-9, R1-COR-7 | PROPOSE FIX (cut) | Cite "51" as `P5a.md:89` (`LEDGER_IDS` = `BL-core-c18a-001..051`). **Cut R8** (stale waiver). The waiver file is P5b3's (`P5b3.md:146`), so the refusal of a waiver whose file, function or `stmt_hash` matches nothing belongs in P5b3's loader (coupling C4). That removes the unmutated row. |
| R1-ADV-10 | PROPOSE FIX | Page item (6) adds: the k1b stored raw model output and tool input (`k1b/loop.py` `run_case`) is masked by patterns only, and can still hold names and invoice lines. |
| R1-ADV-11 | PROPOSE FIX | `docs/diagnostics.md` is the single source for operators. P8b's `docs/kinds/diagnostic.md` links to it and does not restate it. Relay: add `docs/diagnostics.md` to P8b's wording check (C7). |
| R1-ADV-12 | PROPOSE FIX | One sentence: the class stays redaction although P5b5 is now tests plus a page (see the shrink section). |
| R1-ADV-13, R1-COR-4 | PROPOSE FIX | Replace ticket :23 and PENDING LEAD 5 with: "S0 EXIT: order 21 item 17, effective after freeze and the build-start review (order 20 item 3)". PL 5 is closed. |
| R1-ADV-14 | CONTEST | The bandit line is CI's own command (`ci.yml:119`: `bandit -q -r src demos -ll`). CI Python is 3.13 (`ci.yml:73`) and the ticket's 3.12 line already says "not run, with the reason". One clarifying clause, folded into COR-13: "3.13 = CI; 3.12 if installed". |
| R1-ADV-15 | PROPOSE FIX | Adopted as rule `traceback_import` (see ADV-5). V2 shrinks to names computed at run time (`getattr(mod, name)`, `importlib.import_module(<computed>)`). |
| R1-ADV-16 | PROPOSE FIX | Step 0 saves the ast-walk script and its output as `handover/evidence/P5b5/step0-safe-head-callers.txt`, at `cd2243f` and at the P5b4 head, with `git rev-parse HEAD` in the file. The `cd2243f` result is F-b. |
| R1-ADV-17 | DECLINE | Nit; wording. "leftover" keeps its one definition. |
| R1-ADV-18 | PROPOSE FIX | Mark the mutation-runner line and the `<sha>` placeholders as "filled at build start from the merged P1m". |
| R1-COR-1 | CONTEST | At the stated base, `def safe_head` is `cd2243f:src/hadavin_sdk/guard/runmap.py:532` (F-a). The reviewer read the older on-disk `src/` (485). No change. The builder already re-measures at step 0 (ADV-16 adds `rev-parse`). |
| R1-COR-3 | PROPOSE FIX | Page item (6) is written from the MERGED P5b4. Per P5b4 rev 1 PENDING LEAD 2, fd 2 goes to the null device, with no `tick-fd2.log` and no `capture_fd2`, and C-level crash output is lost. The D12 file appears on the page only if the lead rejects that PL. Add **R7b**: every backticked `logging.<key>` and every file path the page names exists at the head (a config-model field or a path string in `output_guard.py`). |
| R1-COR-5 | PROPOSE FIX (cut) | Closed by cutting page item (4) (ADV-7). For the record: P5b4's table covers 2 = store not ready through its `run_tick` row (F-g). Neither table lists the kill-switch 4 or the audit 3 (`cli.py:194, :200`); see PL 10. |
| R1-COR-6 | PROPOSE FIX | Reword: "fakes whose `__module__` is `psycopg.errors`, `tests/test_p7_tick.py:606-617`" (F-i). |
| R1-COR-8 | PROPOSE FIX | `safe_head_caller` keys a call by its innermost enclosing `def`. A call in a lambda counts for the enclosing def. A call at module level or in a class body is keyed `<module>` and is always a finding. Add plant **P8 module-level `safe_head(...)`**. |
| R1-COR-9 | PROPOSE FIX (cut) | State the behaviour (F-j, `test_k5_producers.py:46-53`). P5b3 moves the three rows to `DIAGNOSTIC_WRITERS` (`P5b3.md:130`). **Cut R5 and M8.** A row that names `safe_head` forces its function to call `safe_head`, which the R2 equality pin already fails. |
| R1-COR-10 | PROPOSE FIX | Cite orders 6(b), 8(1) and the order 16 header ("stays for RESULT review") instead of 16 item 5. |
| R1-COR-11 | PROPOSE FIX | Say that `tools/mutation_runner.py` (P1m), `tests/data/` (P5a, P5b3) and `tests/test_llm_text_channels.py` (P5b1) appear only when those packages merge. |
| R1-COR-12 | DECLINE | Nit; moving the words block is cosmetic and the template order is unaffected. |
| R1-COR-13 | PROPOSE FIX | Cite `pyproject.toml:6` (`>=3.12`) and `ci.yml:73` (3.13). |

**Rows and mutants after these decisions** (the author numbers them in revision 2):
- Rows:
  - R2: equality pin of `SAFE_HEAD_CALLERS`.
  - R3: no `traceback_import` or `basic_config` finding.
  - R4: `server_log_noop`.
  - R4b: `test_receiver_writes_nothing_to_stderr`.
  - R6: corpus closed at R5.
  - R7: Code / Fact table equality.
  - R7b: the page names only real keys and paths.
  - Plants P1-P8: the existing P1-P4 and P6 as revised, plus the ADV-4 alias plants, P7 and P8.
  - Cut: R1, R5, R8 and plant P5.
- Mutants:
  - M2, M3 and M4 (re-add `import traceback` and `print_exc`).
  - M5, M7, M7b, M9, M10.
  - One "rule removed" mutant each for the four rules.
  - Alias-resolution mutants.
  - M15 (skip unparsable).
  - M16 (subset), killed by P7.
  - Cut: M1, M6, M8, M14.

## Positions (where I disagree with a reviewer, and why)
- **COR-1:** wrong tree. The commit is readable; the ticket is right.
- **ADV-14:** the commands already match CI.
- **ADV-5 / ADV-4:** the reviewers asked for MORE rules and an allow-list for `exc_info`. I cut the rule instead, because two other packages enforce it: at runtime in P5b4 (K2 and U6), and by the AST taint guard in P5b3. The cheaper import ban (ADV-15) replaces the traceback call list. This follows order 8 / 7(3): cut surface rather than add design.
- **ADV-1 severity** is kept as a Blocker. F-c confirms it, and P5b3's own killer test would also pass on deletion (F-d).

## Couplings (other tickets; relay, do not edit here)
- **C1 P5b3:** `test_receiver_logs_nothing` (killer of M25) uses `caplog`. A deleted override writes to `sys.stderr` and passes it (F-c). Recommend `capfd`, or rely on P5b5's R4/R4b and say so.
- **C2 P5b4 `:59`, `:181`:** "P5b3 removes `log_message`" contradicts `P5b3.md:131` (the override is kept, with body `return`). Fix the P5b4 wording.
- **C3 P5b3 `:118` vs P5b4 `:118`:** both rewrite `cli.py:81-82` (the `HADAVIN_DEBUG` branch) with different output ("plus `chain=`" against "one Grammar A line"; P5b4's U20 would fail on P5b3's `chain=`). One owner is needed (PL 12).
- **C4 P5b3 `:146`:** the waiver loader refuses an entry whose file, function or `stmt_hash` matches nothing (it takes over the cut R8).
- **C5 P5b3 `:52`, `:330`; P5b4 `:34`, `:336`:** the same stale S0 EXIT text; order 21 item 17 answers it.
- **C6 P5c `:66`, `:135` and P4a `:96`, `:105`:** both edit `k1b/loop.py`. A change to `run_case`'s `safe_head` use updates `SAFE_HEAD_CALLERS` in the same PR. If P5c PL 12 drops P5b5 from P5c's Depends-on, P5b5 leaves the critical path, and the reason in P5b5's PL 1 ("so the plan edge P5c depends on P5b5 stays") goes.
- **C7 P8b `:137`, T6:** `docs/kinds/diagnostic.md` links to `docs/diagnostics.md`, and the wording check covers `docs/diagnostics.md`.
- **C8 P5b4 PENDING LEAD 2** (fd 2 to the null device against D12's file) decides page item (6) (COR-3).

## PENDING LEAD (continues the ticket's numbering; 5 closed by order 21 item 17, 6 deleted as decided by P5b3/P5b4)
8. **P5b5 shrinks to tests plus a page, with zero `src/` changes** (shrink section). Recommend yes. Alternative: fold it into P5b4's PR. Cheaper if P5c PL 12 is accepted, but it makes a large redaction PR larger. Recommend keeping it separate.
9. **Checker cuts:** rules `tick_driver_names` (redundant with the R2 equality pin and P5b3's guard) and `exc_info_arg` (P5b4 K2/U6, P5b3 OBJECT sink); rows R5 and R8; mutants M1, M6, M8, M14. Recommend yes.
10. **Exit codes leave the page;** it links to P5b4. Recommend yes. Alternative: copy P5b4's 9 U19 rows plus kill switch 4 and audit 3 (`cli.py:194, :200` at `cd2243f`), with a drift test.
11. **The receiver no-op is pinned by its shape (R4) and by a real-socket stderr test (R4b);** the override is never deleted. Recommend yes. It closes the Blocker.
12. **C3, the one owner of the `HADAVIN_DEBUG` branch.** Recommend P5b4, which owns `main()`. P5b3 removes `print_exc()` and prints `render(diagnose(exc))` only, without `chain=`, so P5b4's U20 holds unchanged.

## What round 2 needs
- Two fresh `egm:*` reviewers (correctness and adversarial) read revision 2, then one Opus resolve. This is round 2 of a cap of 3 (order 20 item 6).
- It is a redaction ticket, so round 4 is allowed only if round 3 ends with no Blocker and at most 2 Majors. Otherwise the ticket freezes after round 3, and what remains goes to its v1.1 or limits list in plain words.
- Give the round-2 reviewers `git show cd2243f:<path>` access, or a `cd2243f` snapshot, so the stale-tree finding (COR-1) does not repeat.
- What round 2 should attack first:
  1. the `server_log_noop` shape rule and R4b;
  2. the `TRACEBACK_IMPORTERS` equality and its step-0 measurement;
  3. R7b against P5b4's final fd-2 choice;
  4. whether any L1-L7 row is now owned by nobody;
  5. the rename rule of `SAFE_HEAD_CALLERS` against P4a and P5c.

## Counts
- 31 ids, by severity: 1 Blocker, 12 Major, 14 Minor, 4 Nit.
- By decision:
  - PROPOSE FIX: 27. Five of them are closed by a cut: ADV-5, ADV-7, ADV-9 with COR-7, COR-5, COR-9.
  - CONTEST: 2 (COR-1, ADV-14).
  - DECLINE: 2 (ADV-17, COR-12).
  - ESCALATE: 0.
- Duplicate pairs: ADV-2 = COR-2, ADV-13 = COR-4, ADV-9 (R8 part) = COR-7.
- PENDING LEAD: 5 new (8-12); 1 closed (5); 1 deleted (6).
- Couplings: 8.
- Unaddressed: 0.
