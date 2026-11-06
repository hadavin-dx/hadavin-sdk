# AK4a round 3, correctness review

Status: REPORTED (saved by the lead session from the reviewer hand-back, which is model output, not user authority).

AK4a round 3 CORRECTNESS review (revision 3, commit 831d013). Read-only. I did not open handover/reviews/ or handover/evidence/. The checkout has no git, so I could not check "main differs from cited commits". Every code cite was read on the checkout at <repo>/hadavin-sdk-handover.

VERDICT: 0 Blocker, 3 Major, 5 Minor, 2 Nit. Majors 1 and 3 are quick edits. Major 2 needs the k1b marker design settled before AK4a-2 is buildable. By the round cap in the header, this leaves a 4th round open only if the resolve leaves at most 2 Majors.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 160, 297 (Files and Done) | `tests/test_k5_producers.py:78-100` parses every `.py` under `src/hadavin_sdk` and fails on any module that calls `.chat(` or `.apply_guardrail(` and is not in `guard/producers.py` `MODEL_CALLERS` (`producers.py:55-65`). The same test requires each member of `MODEL_CALLERS` to have a `PRODUCERS` row or an `OUTSIDE_THE_CHOKE_POINT` reason (`:102-107`). `testing/faults.py` (`FaultLLM` calls `inner.chat`) and the step adapter's test step in `testing/harness.py` would be unregistered, so AK4a-2 cannot go green. Done names this test as a gate, but Files lists no edit to `guard/producers.py`. Related: `tickets/P4c.md:218` (T8) adds a similar AST scan for attribute `chat`, with a status row per module and failure for any new module. Its table also says "`evals.py` not capped", which AK4a-3 changes. | Add `guard/producers.py` to the Files of AK4a-2: new `MODEL_CALLERS` entries plus `OUTSIDE_THE_CHOKE_POINT` reasons ("test fake; receives only what the caller sends"). Or keep `.chat(` calls out of `src`. List P4c T8 and its `evals.py` row under Couplings. |
| R3-COR-2 | Major | 133 (Interface 11), 146 (C-FAULT), 186 (H0), 200 (H11 k1b) | The k1b marker cannot be matched by whole line. `loop.py:144-148` sends the model `_dumps({"alert": bundle.alert, "alert_time": ...})`, which is one JSON line, and a newline inside a JSON string is escaped. A `Bundle` has no free "document", only the `alert` dict of strings with fixed keys (`bundle.py:96`, `:225-238`), and `case_id` is never sent. So `text.splitlines()` equality with `item-<id>` never matches for k1b. Every k1b attempt would then be `unattributed_attempt`. The H11 k1b clauses ("C-FAULT gives no finding") and any k1b row run with C-FAULT would fail. "In the bundle's document, with the case id" is not buildable. | State where the marker rides in a k1b bundle, for example a value in `alert.labels` (strings of at most 200 characters, `bundle.py:229-235`). State how C-FAULT reads it from the JSON message text, for example by decoding the JSON of the first user message and comparing the exact string value. Extend H0's marker clause to cover `redact_bundle`'s `_walk` on that field. Keep the `item-1` versus `item-10` exactness test. |
| R3-COR-3 | Major | 204 (H15) | H15 asserts that two k1b runs give "the same outputs digest (`hash_files` over `outputs_files`)". `outputs_files` includes every file under `run*/`, so `run1/run.json` (`replay.py:78-82`). `run.json` holds `replay_run_id`, which is `new_id("k1b")` = uuid4 (`replay.py:135`, `:232`, `models.py:23-24`). So the digest differs on every run, and the row cannot pass. | Compare only the per-case files plus a normalised `run.json` with `replay_run_id` removed. Or patch `models.new_id` / `replay.new_id` to a seeded source in the row, and say which. |
| R3-COR-4 | Minor | 271 (M-H26), 187 (H1 clause 7) | M-H26 ("`sys.stdout` not swapped, descriptor capture only") is killed by `print` only while pytest's fd capture is on. Under `-s` or `--capture=no`, `print` goes to descriptor 1 and the mutant survives. The mutation runner's pytest flags are UNVERIFIED (P1m is not on disk). | Make clause 7 independent of the capture mode. It should replace `sys.stdout` with a non-fd-backed object (an `io.StringIO`) before calling `capture()`, then `print`. |
| R3-COR-5 | Minor | 114 (Interface 8, schedule), 166 | `pyproject.toml:74` has ruff `extend-select` including `S`. `random.Random(...)` in `testing/faults.py` raises S311, which `llm/retry.py:106` silences with `# noqa: S311`. CLAUDE.md says no suppressions. The ticket does not mention the ruff or bandit result for the draw. | Say either "`# noqa: S311` with the reason, as `retry.py:106`", or derive the draw from `hashlib.sha256(f"{seed}:{k}")`, which is also hash-seed independent. |
| R3-COR-6 | Minor | 136 (Interface 12) | "`sys.stdout`/`sys.stderr` text wrappers writing to the same temporary file" as the dup2 of fds 1 and 2. If a wrapper opens the file separately, it gets its own offset and overwrites the descriptor output. Only wrappers over a dup of the same descriptor, or opened append-only, share one offset. | State "wrappers over `os.dup` of the same descriptor (shared offset)". Add a test that interleaves `print` and `os.write(1)` and sees both. |
| R3-COR-7 | Minor | 139 (Interface 13), 113-118, 292 | `K1bReplayPipeline` is under-specified against `replay.py`. `_replay` needs a `K1bAudit` (`audit_sink.py:26-27`), not the plain `AuditSink` that `Pipeline.run(audit=...)` carries. It also needs `cause_list_dir` (`replay.py:127`), a `Detector`, and a k1b config with `case_timeout_s`. `k1b` takes a `Callable[[], float]` clock (`replay.py:107`, `loop.py:137`), but `FakeClock` is described with `sleep` only. H10d needs a scripted tick sequence like `[0, 0, 299.99, 1000...]` (`test_k1b_replay.py:513-515`), not a hand-advanced clock. Replies built by `FaultLLM` need `model_id`, which `Reply` requires (`models.py:295`). | Add one sentence naming the `K1bAudit` wrap, the cause list fixture, the detector and the clock callable. Describe H10d's tick script. State where `model_id` comes from. |
| R3-COR-8 | Minor | 61, 84, order 25 item 4 | `LEAD-ORDERS.md:135`: "the studio laptop is Windows; tests keep a Windows-capable form unless the ticket says Linux-only". The ticket says nothing about Windows. `os.dup2`, a daemon-thread join, `HADAVIN_REQUIRE_PG` and X3's multi-process helpers all run there, and the lead runs the mutants on Windows. | Add one line: "Windows-capable (no POSIX-only calls)" or "X3 is Linux-only because ...". |
| R3-COR-9 | Nit | 133, 194 | The example ids `item-1` and `item-10` cannot be StepInput ids. AK1 `ITEM_ID_PATTERN = [a-z][a-z0-9_]{0,23}-[0-9a-f]{32}` (`tickets/AK1.md:105`). The marker is then `item-name-<32 hex>`. | Use ids of that shape in H8 and H12, and say that `new_id` gives them. |
| R3-COR-10 | Nit | 108, 112, 110 | Cites are off by 1 to 2 lines. `registry.py:165-171`: the `eval_threshold` block is `:164-170`. `models.py:273` is the comment line, and the field is `:274`. `config.py:365-373` is correct. | Re-point, or write "about". |

Positive findings (Verified)
- Template: all 17 fields are present, in template order (`TICKET-TEMPLATE.md:3-19`). The Problem field is 5 sentences. The Path class field gives the class and the extended-review answer.
- Counts. 45 test rows: E1-E15 = 15; AK4a-2 = H0, H1, H2, H4-H17 (14), H7b, H10b, H10c, H10d = 21; AK4a-3 = H3, X1, X2, X3, X4, X4b, X5, X5b, X7 = 9. 61 mutants: M-E1..21, M-H1..31, M-X1..9. Every killer row cited in the mutation table exists in Tests. Real, weak and strict-xfail counts match the text. 19 INFORM, 4 PENDING LEAD, 5 findings and 8 later rows are all consistent.
- Code cites that match the checkout:
  - `k1b/loop.py`: `:41`, `:51-53`, `:57`, `:81`, `:104-106`, `:115-122`, `:130`, `:154-156`, `:166-171`, `:173-175`, `:179-188`, `:200-202`, `:215`.
  - `k1b/replay.py`: `:44`, `:85-90`, `:93-108` (`clock` and `llm` are injected), `:114-115`, `:119-123`, `:136`, `:166`, `:175-178`, `:222`, `:224`, `:226`, `:261`.
  - `llm/retry.py`: `:22-23`, `:31-36`, `:39-40`, `:55-63`, `:66-74`, `:83-108`, and the jitter and sleep at `:106-107`.
  - `llm/fake.py:17`, `:21-54`; `llm/protocol.py:10`, `:14`, `:18-28`.
  - `evals.py:13-20`, `:26-32`, `:35`, `:45`, `:63`, `:73-79`, `:81`, `:95`, `:98-100`, `:104-110`, `:123-126`, `:131`, `:133-140`; `models.py:50-52`, `:257-280`.
  - `config.py:317`, `:320-324`, `:365-373`; `runtime/agent_loop.py:58`, `:76`, `:101-124`, `:141-157`; `cli.py:146-153` (`make("llm")` at `:150`); `defaults.py:85`; `config.py:263`.
  - Existing tests: `tests/test_k1b_replay.py:502-528` (patch at `:505`), `tests/k1b_support.py:17-35` and `:269-289`.
- Runtime claims: `matches`, the abstain count over all pairs, and the append with fsync behave as stated. The only `evals.gate(` caller under `src` is `cli.py:148`; the other two hits are docstrings (`runtime/evidence.py:122`, `k1b/loop.py:3`), which an AST lint ignores.
- X7 lint: no `evals.gate` caller in `src` outside `cli.py` today.
- Import graph and cycle: `evals.py` imports `runtime.evidence`, which imports no `evals` or `agent_loop`. `agent_loop` is imported only by `app.py` and `cli.py`, so `agent_loop` importing `evals.meets_current` adds no cycle. `runtime/__init__.py` being empty was not re-checked (ticket claim only). The full transitive closure was not run.
- Lint and guard claims:
  - The canary literals do not trip `test_no_hardcoded_values.py`: the host regex at `:34-38` has no `invalid` TLD.
  - The EMAIL pattern (`guard/redact.py:235-240`) matches the canary shape by its regex.
  - `src/hadavin_sdk/testing/` does not exist on this checkout.
  - `test_repo_rules.py` has 0 hits for `testing`.
  - `tests/fixtures/golden/test-agent.jsonl` has exactly 10 lines (E1 and E12).
- Pytest 9.1.1 in `.venv` (Python 3.13; `requires-python >=3.12`):
  - `_pytest/capture.py:500` is `SysCapture(targetfd, self.tmpfile)`, so `sys.stdout` goes to the capture tmpfile and not to fd 1 (resolve fact 3).
  - The `skipping.py` xfail marker text says that with `raises=` set, a test failing another way is "a true failure".
  - `xfail(strict=True, raises=AssertionError)` with a `RuntimeError` precondition behaves as the ticket claims.
- P1m pin: `tickets/P1.md:72` lists `testing/__init__.py` among the four P1m files pinned by sha256. The ticket therefore correctly adds files beside it and edits none of them.
- Retry and fault arithmetic:
  - `Throttled` with `status_code` 429 and `headers={"retry-after": "2"}` is retried; the sleep is exactly 2.0, which is between 2 and 8.
  - Without `headers`, `retry_after` returns 0 and the sleep is at most 0.5 or 1.
  - `TimeoutError` is an `OSError`, so it is retried.
- Row arithmetic:
  - E4/E5: `min_traps` values (10,15)=3, (50,15)=8, (60,15)=9, (100,55)=55 are correct, and the floor and float variants give 7 and 56.
  - E8: 5/13 abstain rate and 0.2 false-abstain rate are consistent.
  - H10: 3 calls run on main, ending at 3R against a cap of 2.5R.
  - H10b: billed 9W on main, 3W with P4a-2 only.
  - H10c: the bound W/3 < R <= W/2 gives 3W + 3R > 4W.
  - H10d: 3W billed after the release.
  - PENDING LEAD 4: 0.004 + 2 x 0.02736 = 0.05872, which is 14.68 times 0.004.
- Dependencies and merge order:
  - The branch rule `core/<id>` from `origin/main` matches order 20 item 4.
  - AK4a is not in the lead's merge chain, so it makes no ordering claim against it.
  - Dependencies match `tickets/AK1.md:84` and `:94`.
  - The round-cap wording matches order 20 item 6.
  - Cited order texts match: order 14 item 3 ("UPPER bound", `LEAD-ORDERS.md:40`), order 24 item 32, order 27 items 55 and 63.
- Cited ticket lines that match their text: `P4a.md:47`, `:86-88`, `:104`, `:327` (`tools` is a required keyword and `requests=1` a keyword, as Interface 8 uses it), `:560` (PL55); `P4b2.md:55-56`, `:146`; `P4b1.md:51`, `:239`, `:259`, `:266`; `P4c.md:218`; `P5c.md:288`, `:343`, `:349`, `:496`; `AK1.md:94`, `:104-117`, `:187`, `:381`.

Not checked (UNVERIFIED)
- No git on the checkout, so I could not compare against `origin/main` `4ec3616` or the cited commits `831d013`, `3a3fcca`, `a6509a9`, `4d06a6a`. I did not read or run anything under `handover/reviews/` or `handover/evidence/`.
- The claim that `origin/core/P1m`'s `tests/fixtures/mutation_manifest.json` pins `testing/__init__.py` was not checked. The file is not on disk. I relied on `tickets/P1.md:72` only.
- The P1m mutation runner command line and its pytest flags. The runner could have a rule about which files may sit in `testing/`.
- Whether a pilot `Config` fixture for E1 and E2 can be built (`_anchor_refusals` and the other pilot requirements, `config.py:371`).
- That `redact_bundle` and the gate masking mask the canary and leave the marker unchanged. This is H0's job and is untested. I checked only the EMAIL regex.
- Names from tickets not yet built: AK1-a/b, P4a-2, P4b1-b, P4b2-a (`AttemptCounts`, `prior_unknown`), P5c-2/3, P6a-1. I checked cites against ticket text only.
- AK1 line numbers other than `:84`, `:94`, `:104-124`, `:187`, `:381` (`:108-116`, `:125`, `:134`, `:146`, `:197`, `:227`, `:343`).
- P4a `:72`, `:161-162`, `:458`, `:466`, `:541`; P4b1 `:112`, `:168`; P4b2 `:112`; `kit-plan-v2.md`, `plan-v3.md`, `WORK-PACKAGES.md`.
- `LEAD-ORDERS.md` orders 6-13 and 15 (orders 14, 16-31 were read selectively), and order 14 item 1 and order 15 look-alike wording.
- Whether existing tests run `gate` or `assert_qualified` in pilot or prod (`tests/test_s3_gate.py` and `tests/test_k3_pilot.py` showed none in a quick grep; the full set was not traced).
- Whether the `gate` command is testable by identity for X5b (`cli.py` structure past `:146-153`).
- I ran no code and no tests. Runtime behaviours (thread join, dup2 capture, record factory, `Fraction` boundaries) were reasoned from the source only.