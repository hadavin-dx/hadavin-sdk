# AK4a round 2 resolve (ticket revision 2, commit 4d06a6a)

**Honest note (read first).** This is the resolve step. I ran `egm:egm-resolve` in AUTO mode and skipped the interactive gate, as the lead ordered. The skill's default report name (`goldfish_review_report.md`) and layout were replaced by this file and the round 1 resolve layout.
- **My own slip.** Round 1 resolve fact 6 (written at this same step) gave the P5c cites `:141`, `:294` and `:348`. Revision 2 copied them. Round 2 correctness (R2-COR-4) shows they are wrong. The right lines are `P5c.md:349` and `:496` (fact 9).
- **What is "main".** The core source I read is this worktree's checkout. `git diff --stat origin/main HEAD -- src tests` lists 23 differing files. None of the files cited below is among them, so every code cite holds on `origin/main` 4ec3616.
- **What main does NOT have.** Main has no unmerged ticket's code: no `testing/` package, no P4a-2 or P4b2-a booking, no AK1 gate, no P5c wrapper. Every such name below is read from ticket text. The one exception is P1m's manifest, which I read on branch `origin/core/P1m` (unmerged, draft PR 61).
- **What I ran.** `python3 -I` one-liners for stdlib behaviour and arithmetic (facts 4, 5, 6, 13). I read pytest 9.1.1's own source in the project's virtual environment (facts 3, 12). I ran no repository code, no test and no install.
- **Not checked.**
  - The full transitive import closure of `evals.py`. I checked its own imports and one level below (fact 10).
  - Whether the core masking leaves the attempt marker of row 4 unchanged. H0 checks that.
  - P4b2's review state. P4b2 is cited as the owner of F5, and its text may still change.
- **A gap no reviewer raised (row 4).** Revision 2 never says how C-FAULT knows which item an attempt belongs to. I added a row for it.
- **Status:** resolved (AUTO). The author writes revision 3 from the table. I did not edit the ticket, commit, push or write DECISIONS.md.
- **Target:** `tickets/AK4a.md` revision 2 (352 lines, full file, unchanged since 4d06a6a by `git diff`).
- **Gate (order 20 item 6):** round 2 of at most 3. The adversarial report has a Blocker, so the round is not clean. Next steps:
  - revision 3;
  - round 3 with FRESH reviewers and one Opus resolve.
  - AK4a is a money, redaction and security package. A 4th round is allowed only if round 3 has no Blocker and at most 2 Majors.

## Facts I checked myself (they decide rows)
1. **Only one caller of `evals.gate` in src.** A grep of `src/hadavin_sdk` for `evals.gate` finds one call, `cli.py:148`. The other hits are docstrings: `k1b/loop.py:3` and `runtime/evidence.py:122`.
2. **The k1b loop halts the run after an abandoned call.**
   - `k1b/loop.py:166-171`: on `CallTimeout` it charges `worst_case_usd` once and sets `halt="aborted"`. The comment says "stop the run: at most one such call per invocation".
   - `k1b/replay.py:151-178`: `stop = o.halt`, and every later bundle gets an `error` outcome with no call.
   - `loop.py:81`: `MIN_WAIT_S = 1.0`. Main's test `tests/test_k1b_replay.py:501-504` patches it to 0.05 and uses a `Hung(ScriptedLLM)` that waits on an `Event`.
   - P4a-2 books a `CallTimeout` at the whole-call maximum, request count x attempts x W (`P4a.md:47`; table row `:117`).
3. **Pytest's fd capture bypasses descriptor 1 for `print`.** In pytest 9.1.1, `_pytest/capture.py:490-500`, `FDCapture` sets `syscapture = SysCapture(targetfd, self.tmpfile)`. So `sys.stdout` writes straight into pytest's temp file object, not to descriptor 1. A later `os.dup2` on descriptor 1 does not see `print`. R2-ADV-4 holds.
4. **What a log record holds, and when.** Checked with a `setLogRecordFactory` wrapper in `python3 -I`, with C as the canary:
   - `log.info("%(a)s", {"a": 1, "b": C})`: `getMessage()` lacks C; `repr(record.args)` holds it.
   - `log.info("x", extra={"who": C})`: the field is NOT in the record when the factory runs, but IS on the same record object afterwards.
   - `log.exception("failed")` over `ValueError(C)`: the message lacks C; `exc_info` holds it.
5. **A string-seeded random generator gives the same draws everywhere.** `random.Random(f"{seed}:{k}")` gave the same draws under `PYTHONHASHSEED` 1 and 2.
6. **Echo billing.** A text reply ends a k1b case after one call (`loop.py:183-188`).
7. **The P1m pin.** On `origin/core/P1m`, `tests/fixtures/mutation_manifest.json` pins `src/hadavin_sdk/testing/__init__.py` (and `mutation.py`, `tools/__init__.py`, `tools/mutation_runner.py`) by sha256. `P1.md:72` says the same. R2-COR-1 holds.
8. **F5 already has an owner.** P4b2-a fixes it:
   - `P4b2.md:55-56`: `with_retry` stamps `AttemptCounts`, and a successful `chat` copies `prior_unknown` onto the `Reply`.
   - `P4b2.md:112`: the k1b answered path books answered cost + `prior_unknown x W`, and deletes PL55's fake-only guard.
   - `P4b2.md:146`: row G15, hidden attempts on the meter path.
   - `P4b1.md:266`: the meter books `answered + u x W`.
   - Until P4b2-a merges, k1b refuses every real llm kind (`P4a.md:560`, PL55; V36 at `:466` names P4b2-a as the trigger).
9. **The P5c cites.**
   - `P5c.md:141` is the P5c-2 header; `:294` is an `extract` row; `:348` is an `extract.py` fallback.
   - The `evals.py` contract is at `:349`: the wrapper is required; each (case, k-run) opens `llm.run(...)`; `:63` uses that run's session and `decode_document`; a non-UTF-8 case counts as FAILED `unsupported_input` (T3-05b).
   - The wrapper-required row is `:496` (T3-06).
   - The llm-path intent event is `:288` (e): `domain="llm"`, `operation="outbound"`, `inputs_hash=sha256_hex(masked body)`, written before the inner call. That line does not give the byte form of "masked body".
10. **No import cycle.**
    - `evals.py:13-20` imports `defaults`, `config`, `guard` (`judge`, `runmap`), `llm.protocol`, `models`, `registry`, `runtime.evidence` and `stats`.
    - `runtime/__init__.py` has no import.
    - A grep of those modules, plus `deferred`, `actions/contract`, `store/protocol`, `llm/common`, `guard/egress|injection|redact`, `replay_records` and `identity`, finds no import of `hadavin_sdk.runtime` or of `evals`.
    - So `agent_loop` can import `evals` at the top. The full closure was not run.
11. **`worst_case_usd`.** On main it takes `(route: Route, system, messages)` (`loop.py:115`). After P4a-2 it takes `(route, system, messages, *, tools, requests=1)` (`P4a.md:327`). `LLM.chat` receives `route` as a name string.
12. **`xfail(raises=...)`.** Pytest `_pytest/skipping.py:84`: when `raises` is set, a test that fails another way is reported as a failure.
13. **Arithmetic** (`python3 -I`, Decimal). With P4a's made-up W = 0.082080 / 3 = 0.027360 and R = 0.004:
    - booking the upper bound of 2 hidden attempts per answered call books 0.058720, which is 14.68 times R;
    - H10d (row 7): 3W billed is above a cap of 2W, and the F1 pre-check refuses 0 + 3W > 2W.
14. **The P4a `:72` line.** `P4a.md:72` (the revision 7 changelog) is REVERSED by PL38 (`:541`, "REVERSED in revision 9 by PL50"); V28 is at `:458`. R2-COR-8 holds.

## Decisions (27 finding ids plus 1 resolver row, in 24 rows; one decision per row)

| id(s) | category | decision for revision 3 |
|---|---|---|
| R2-ADV-1 (Blocker) | PROPOSE FIX (cut surface) | Valid (fact 1). **`EvalGatePipeline` moves out of `src`:** it becomes a test adapter in `tests/test_pipeline_invariants.py`, implementing the `Pipeline` protocol. A client project has no use for an adapter that tests the core's own gate. X7 then reads: "inside `src/hadavin_sdk`, the only caller of `evals.gate(` is `cli.py` (AST); `tests/` is not scanned". Its teeth row is unchanged: a test copy of `testing/harness.py` with a planted caller makes the lint fail (M-X8). Interface 13, the Files field (AK4a-3), the Target field and D1 drop `EvalGatePipeline` from `testing/harness.py`. H3 stays in AK4a-3. |
| R2-ADV-2 + R2-COR-3 (Majors) | PROPOSE FIX | Valid. **(1) Lazy schedule:** `FaultSchedule(faults: Mapping[int, Fault] = {}, *, seed: int, rate_percent: int = 0, kinds: Collection[Fault] = ())`. `FaultSchedule.random(rate_percent, seed, kinds)` has no explicit entries and NO `n_attempts`. The fault of attempt k is the explicit entry if there is one. Otherwise, when `rate_percent > 0`, `r = random.Random(f"{seed}:{k}")` draws it: a fault when `r.randrange(100) < rate_percent`, of kind `r.choice(sorted(kinds))`. It is a pure function of (seed, k) with no upper bound (fact 5). **(2)** `fault_not_reached` applies ONLY to explicit entries. **(3)** H6 runs single-threaded: items in input order, one at a time. **(4) Prediction:** a reference function in the test walks items in input order and steps in order, numbering attempts from 1. Each call uses attempts until one is answered or `attempts` is used up, and the end comes from the Interface 8 table. **(5)** The `ValueError` list is: attempt number below 1, unknown fault, rate outside 0-100, and `kinds` empty while the rate is above 0. R2-COR-3's "`n_attempts` at most the item count" is not taken: the lazy form removes the need. |
| R2-ADV-3 + R2-COR-2 (Majors) | PROPOSE FIX | Valid: in `StepPipeline` every `bad_reply` is the item's last reply. H11 gains a k1b clause. Case 1's first reply is a `bad_reply` (unoffered tool: its name goes into `hard_check_a` and the loop goes on, `loop.py:200-202`). Its next reply is a scripted good reply with a readable diagnosis. The case ends `ok` -> `done`, and C-FAULT gives no finding. M-H24 is re-pointed to that H11 clause. The sentence "none labelled equivalent" then holds. |
| R2-RES-1 (resolver's own, Major-class; no reviewer raised it) | PROPOSE FIX | **Gap:** C-FAULT ("an item whose LAST reply was ...") and H6's prediction need to know which item each attempt belongs to. `RunRecord` holds no attempts, and the ticket does not say how. **Decision: attribution by data, as D4.** Every made-up item document carries a marker `item-<item_id>`; for k1b, the item id is the case id. C-FAULT gives attempt k to the one item whose marker appears in `received[k].texts`. An attempt with no marker or with two markers gives the new code `unattributed_attempt` (fail closed). This works in threads too (H8). H0 gains a clause: the marker passes both masking paths unchanged (UNVERIFIED until H0 runs). H12 gains a clause: an attempt with no marker gives `unattributed_attempt`. New mutant M-H29 ("an attempt with no marker is skipped"), killed by H12. |
| R2-ADV-4 (Major) | PROPOSE FIX | Valid (fact 3). `capture()` also replaces `sys.stdout` and `sys.stderr` with text wrappers writing to the same temporary file. It flushes them and both descriptors before reading, and restores them on exit (H16 covers them too). H1 gains a `print(canary)` clause and a `sys.stderr.write(canary)` clause, each giving `canary_in_print`. New mutant M-H26 ("`sys.stdout`/`sys.stderr` not swapped; descriptor capture only") is killed by H1's `print` clause. M-H22 (the opposite case) stays, killed by `os.write(2, ...)`. Interface 12's sentence "`print` ... are all seen" is kept, now true. |
| R2-ADV-5 + R2-ADV-9 (Major, Minor) | PROPOSE FIX | Valid (fact 4). **What C-LOG reads from a record:** the factory wrapper only KEEPS each record. The scan runs at check time over: `getMessage()`; the `repr` of each item of `record.args` (and each value of a dict); the formatted `exc_info` text and `stack_info`; and every other value in `record.__dict__`. Because the scan reads the same object later, `extra=` fields and later filter or adapter changes are seen. **H1 clauses:** (a) the args clause becomes `log.info("%(a)s", {"a": 1, "b": canary})`, whose message lacks the canary, so only the args scan kills M-H2; (b) new clause: `log.exception("failed")` inside an `except` over an error that holds the canary gives `canary_in_log`, which kills M-H5, now defined as "the `exc_info` text of a logged record not scanned"; (c) new clause: `log.info("x", extra={"who": canary})` kills new mutant M-H27 ("`record.__dict__` extras not scanned"). **Separate path:** `canary_in_raised` (the run itself raised) stays H1's "raises" clause, with new mutant M-H28 ("the run's raised exception not scanned"). |
| R2-ADV-6 (Major) | PROPOSE FIX; "no finding, no owner" CONTESTED | **CONTEST, with cites (fact 2).** At most one abandoned call can happen per run, because the run halts (`loop.py:166-171`, `replay.py:175`). That call bills at most attempts x W. P4a-2 books a `CallTimeout` at count x attempts x W (`P4a.md:47`, `:117`), and PENDING LEAD 1(a)'s pre-check reserves the same whole-call maximum. So with F1 fixed the cap holds on this path: no F6. **FIX (the missing row):** new fault `hang`. The attempt blocks on an `Event` owned by `FaultLLM` until `FaultLLM.release()`, then behaves as `timeout` (billed `timeout_price`, retried). **New row H10d:** k1b, `attempts=3`, schedule `{1: hang, 2: timeout, 3: timeout}`, 1 bundle, cap 2W, `loop.MIN_WAIT_S` patched to 0.05 as at `tests/test_k1b_replay.py:503`. After the run the harness releases the attempt and joins the thread with a time bound; billed is 3W, above 2W (fact 13). On main and on main plus P4a-2 without the F1 fix, 3W is billed (a later booking does not undo a bill). With the F1 fix, 0 + 3W > 2W is refused before the call, so 0 is billed. The row asserts no `over_cap`, `xfail(strict=True, raises=AssertionError, reason="F1")`. **Fail closed:** C-SPEND run while an attempt is still open gives `ledger_missing`. H13 gains a clause: a released `hang` followed by two timeouts bills 3W, and a check while the attempt is open gives `ledger_missing`. New mutant M-H30 ("an open attempt is ignored by C-SPEND"), killed by H13. |
| R2-ADV-7 (Major) | PROPOSE FIX; "unowned" CONTESTED; calendar date -> PENDING LEAD 4 | **CONTEST "unowned" (fact 8):** P4b2-a owns F5 (`P4b2.md:55-56`, `:112`, `:146` G15; `P4b1.md:266`). **FIX:** the sentence "the lead may want it in the P4b2-a build notes" is deleted. F5 reads: "Owner: P4b2-a (cites). Until it merges, k1b refuses every real llm kind (PL55, `P4a.md:560`), so F5 spends no real money through k1b. The meter path (X3) is the real-money path in a pilot, and P4b2-a's G15 closes it." **Coupling rule:** whichever of AK4a-2/AK4a-3 and P4b2-a merges second does two things in its own PR: it makes `FaultLLM` copy `with_retry`'s attempt counts onto its `Reply` exactly as P4b2-a's kinds do, and it removes the H10c marker. X3 now ASSERTS the cap under timeouts, as a strict expected failure (`raises=AssertionError`, reason "F5"), removed by the same rule. The calendar date belongs to the lead (merge scheduling): PENDING LEAD 4. |
| R2-ADV-8 + R2-COR-6 (Minors) | PROPOSE FIX | Valid. `echo` is an ANSWERED attempt. Its `Reply.cost_usd` is `timeout_price(route, system, messages, tools)`, so a long echo is priced at the upper bound, and it is billed that same `cost_usd`. So "an answered attempt is billed its reply's `cost_usd`" holds for every answered attempt, k1b books what is billed, and no false `over_cap` appears. The text "`timeout` and `echo` are billed `timeout_price`" becomes "`timeout` is billed `timeout_price`; `echo` returns, and is billed, a reply whose `cost_usd` is `timeout_price`". H13 gains a clause: echo billed == its `Reply.cost_usd` == `timeout_price`. New mutant M-H31 ("the echo reply carries cost 0"), killed by H13. |
| R2-ADV-10 (Minor) | PROPOSE FIX (rename, no new design) | X3 is labelled "integration row, no mutant". An X3 failure is a meter defect: the AK4a-3 builder reports it to P4b1-b/P4b2-a's build notes and does not weaken the row. X4 is renamed "C-SPEND-N teeth, arithmetic (booked passed in)". It tests the check, not a store; the store is exercised in X3. |
| R2-ADV-11 (Minor) | PROPOSE FIX | The Done field: "independent evidence, then result reviews repeated until a round finds no Blocker or Major (money, redaction and security: no round cap)". This replaces "two reviews". |
| R2-ADV-12 (Minor) | CONTEST | Fact 10: no module imported by `evals.py`, and none one level below, imports `runtime` or `evals`, and `runtime/__init__.py` imports nothing. So `agent_loop` importing `evals.meets_current` makes no cycle. No `eval_rules.py`. (The full closure was not run; an import error would fail the first test loudly.) |
| R2-ADV-13 (Nit) | DECLINE | A confirmation of the counts; no change asked. Revision 3 recounts anyway (Counts). |
| R2-ADV-14 (Nit) | PROPOSE FIX | One sentence in Interface 8: "the test step returns `needs_person` when `stop_reason == "max_tokens"` or when a tool name is not in its offered set". |
| R2-COR-1 (Major) | PROPOSE FIX (cut surface) | Valid (fact 7). No edit to `testing/__init__.py` and no export line. Consumers import `hadavin_sdk.testing.faults`, `.canary` and `.harness` directly. The Target and Files fields drop "CHANGE `testing/__init__.py`", and the split table drops it from "Unmerged files it truly needs". The manifest is not touched. |
| R2-COR-4 (Major) | PROPOSE FIX | Valid (fact 9; my round 1 slip). **Re-cite:** `P5c.md:349` (the `evals.py` contract) and `:496` (T3-06) replace `:141`, `:294`, `:348` in the Rules, Interface 16 and E13. **The hot-file note now says** that P5c-3 changes the same function in three ways: it opens `llm.run(...)` per (case, k-run), masks at `:63` over that run's session with `decode_document`, and grades a non-UTF-8 case as FAILED `unsupported_input`. **Consequences:** the E fixtures are UTF-8 only, and E12's regression pin is stated for UTF-8 fixtures. H0's "gate masking" target is whatever `evals.py:63` calls on the head where H0 runs. The second to merge of AK4a-1 and P5c-3 also re-runs H0. |
| R2-COR-5 (Minor) | PROPOSE FIX | Fact 11. Interface 8 states the adapter. Before P4a-2: `lambda route, system, messages, tools: worst_case_usd(prices[route], system, messages)`. After P4a-2: `worst_case_usd(prices[route], system, messages, tools=tools, requests=1)`. |
| R2-COR-7 (Minor) | PROPOSE FIX | Fact 12. H10, H10b, H10c, H10d and X3's F5 clause use `xfail(strict=True, raises=AssertionError, reason=...)`, and each asserts the `over_cap` code inside the message. |
| R2-COR-8 (Minor) | PROPOSE FIX | Fact 14. F4 says that `P4a.md:72` was reversed by PL38 (`:541`) and V28 (`:458`), and that the body (`:47`, `:116`) is the rule. The UNVERIFIED line on `:72` is deleted. |
| R2-COR-9 (Minor) | PROPOSE FIX | Fact 9. C-GATE cites `P5c.md:288` for the llm-path intent event. The llm path pairs by order, count and `domain == "llm"`. It compares no hash, because `:288` does not fix the byte form of "masked body". The UNVERIFIED line becomes "the byte form of P5c's masked body (so the llm path has no hash compare)". |
| R2-COR-10 (Minor) | PROPOSE FIX | Interface 4 states the order: compute the bucket counts and `false_abstained`; build the `GateRun` with `green=False`; call `meets_current(cfg, counts=..., run=that)`; then `model_copy(update={"green": ...})`. A missing bucket counts as `BucketStat(n=0, passed=0, abstained=0)`. |
| R2-COR-11 (Minor) | PROPOSE FIX | H2 first computes W from the fixture route and asserts `4 x W < cap` as a precondition, printed in the evidence (an echo is one answered call per bundle, fact 6). |
| R2-COR-12 (Nit) | PROPOSE FIX | Interfaces 1 and 2: label errors come first, as one `ConfigError` naming the case. The combined size list is raised only for a well-formed set. |
| R2-COR-13 (Nit) | PROPOSE FIX | Every mention of AK1's row is written "AK1 V7"; the ticket's own later row stays V7. |

## Positions (kept; checked against the orders)
- **D1-D4** are kept. D1 changes in one place: `EvalGatePipeline` is a test adapter (row 1).
- **I3 (the billing ledger is the truth)** is kept. Echo and `hang` follow it (rows 7 and 9).
- **I6** is reworded as "AK1 V7" (row 24).
- **New INFORM decisions** (final unless the lead says otherwise):
  - **I15:** `EvalGatePipeline` lives in `tests/`, and X7's allowlist in `src` is `cli.py` only.
  - **I16:** no export line in `testing/__init__.py`.
  - **I17:** attempts are given to items by a marker in the data, with `unattributed_attempt`.
  - **I18:** the `hang` fault and row H10d; no F6, because the leaked-thread path is F1's.
  - **I19:** the lazy fault schedule.

## Couplings (text other owners change; this resolve edits none of them)
- **P1m:** the manifest pins `testing/__init__.py`, and AK4a no longer touches it (row 15).
- **P5c-3:** `evals.py` is a semantic overlap (`P5c.md:349`): the masking line `:63`, `llm.run` per (case, k), and non-UTF-8 cases graded FAILED. `gate_llm`, E13 and the H0 re-run are done by whoever merges second (row 16).
- **P5c-2:** the llm-path intent event (`P5c.md:288`) that C-GATE pairs (row 20).
- **P4a-2:** books a `CallTimeout` at the whole-call maximum (`P4a.md:47`). The F1 pre-check (PENDING LEAD 1) closes H10, H10b and H10d.
- **P4b2-a:** F5 (`P4b2.md:112`, `:146`). `FaultLLM` copies the attempt counts, and the H10c and X3 F5 markers are removed by whichever merges second (row 8).
- **P4b1-b / P4b2-a:** own an X3 failure (row 10).
- **AK1:** the name "AK1 V7" (row 24).

## PENDING LEAD (continues the ticket's numbering; 1-3 are unchanged)
4. **NEW: F5's date and form (money).**
   - **(a) Recommended:** F5 stays with its existing owner, P4b2-a (fact 8). It is due in P4b2-a's build PR, and the lead writes the calendar date on the ledger row, because I cannot see the build schedule. Meanwhile:
     - PL55 refuses real llm kinds in k1b, so no real money flows through k1b;
     - H10c and X3's F5 clause stay strict expected failures.
   - **(b)** Put an upper-bound booking into the F1 fix text now, following order 14 item 3 ("book the upper bound"): every answered k1b call books its cost + (attempts - 1) x W. Plain cost on P4a's made-up numbers: 0.058720 instead of 0.004 per call, so a run reaches its cap 14.68 times sooner (fact 13). This becomes moot when P4b2-a merges.
   - **(c)** Both (a) and (b).
   - Why (a): k1b carries no real money in v1, and P4b2-a's design is already exact. Option (b) mainly makes dev runs stop early.

## Counts
- **Finding ids: 27.**
  - Adversarial: 14 by its table: R2-ADV-1 Blocker, ADV-2..7 Major (6), ADV-8..12 Minor (5), ADV-13..14 Nit (2). This matches its header.
  - Correctness: 13 by its table: R2-COR-1..4 Major (4; its header says 3), COR-5..11 Minor (7; its header says 8), COR-12..13 Nit (2). I followed the table.
  - Plus 1 resolver row, R2-RES-1.
- **Rows: 24.** Four merges: ADV-2/COR-3, ADV-3/COR-2, ADV-5/ADV-9, ADV-8/COR-6.
- **Decisions by row:**
  - PROPOSE FIX: 21, of which 2 have a CONTESTED part with cites: row 7 "no F6" and row 8 "unowned";
  - full CONTEST: 1 (R2-ADV-12);
  - DECLINE: 1 (R2-ADV-13);
  - the resolver row: 1;
  - ESCALATE: 0.
- **Surface cut:**
  - `EvalGatePipeline` out of `src`;
  - the `testing/__init__.py` edit;
  - `n_attempts`;
  - the "may want" wording;
  - X4's claim to test a store.
- **Added:**
  - the row H10d;
  - the fault `hang`;
  - the codes `unattributed_attempt` and `ledger_missing` (the latter now also used by C-SPEND);
  - H1 clauses: print, stderr, dict args, `log.exception`, `extra`;
  - clauses in H0, H2, H11, H12 and H13;
  - X3's F5 clause;
  - mutants M-H26..M-H31 (6).
- **Re-pointed:** M-H24 (to H11), M-H2 (new H1 clause), M-H5 (redefined).
- **Expected totals:** 45 rows (AK4a-2 21) and 61 mutants (21 / 31 / 9). The author recounts both and states them in the CHANGELOG.
- **Findings in the ticket:** F1 open (PENDING LEAD 1); F2 and F3 closed by AK4a; F4 closed by P4a-2; F5 owned by P4b2-a (PENDING LEAD 4 for the date).
- **PENDING LEAD:** 4.
- **Majors and Blocker closed on paper:** 1 Blocker and 10 Majors, plus the resolver's row. They count as closed only when round 3 finds them closed.
