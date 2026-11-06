# Package ticket P8c (REVISION 1, DRAFT): the proof pack `tools/proof_pack.py` (run every v1 kind once on made-up data)

CODE-LAST v1. Revision line: **revision 1, DRAFT**, written 2026-11-06 under lead order 84 item 2 (one review round by an egm pair, then freeze, build after P8a). Sources read: `studio-notes/plan-v3.md` (P8c row at line 114, not 117 as the brief said; section 9 row at line 187; section 5 kinds at lines 72-84), `LEAD-ORDERS.md` orders 53, 54, 56, 57, 67, 68, 83, 84, `bible-extract-R447-R450.md` (R450 m, n, o), `TICKET-TEMPLATE.md`, sibling `tickets/P0t.md`, and the frozen tickets named below. Core cites are `file:line` on `origin/main` = `1e4752f`, read with `git show` (the working tree is at an older commit, so it was not used). I ran one probe (pytest skip exit code, below); nothing else was run. "UNVERIFIED" = not read in code or not run. No EGM brainstorm or design doc: Tier B tool package, small; the lead asked for the ticket directly (order 84 item 2). Body is under 150 lines on purpose.

## Summary
- **Package id and name:** P8c, proof pack (plan-v3 line 114).
- **Path class:** other. Tier B (plan row). **Extended review: no.** One review round by a fresh egm pair (order 84 item 2), then freeze.
- **DEMAND (order 57 A2):** core-chain item plan-v3 section 9 row "Proof pack" (line 187): the lead's v1 done check runs `python tools/proof_pack.py` and needs "exit 0 and a printed line per v1 kind with a run count above zero", saved as `proofpack.txt`. No other consumer. Also relay P4c PENDING LEAD 9 (`tickets/P4c.md:349`, standing as recommended per `:340`): add "a wall alert was sent once on the fake channel".
- **Depends on (merged first), in merge order:** P8a (plan row; P8a itself waits for every v1 row, `tickets/P8a.md:32`). P8c uses the entry points of P1a and P1b (textnorm), P2a-1 (stop state), P3a-2 and P4d (store), P4b1 (meter), P4c (wall alert), P5a (diagnostic), P5c-1 to P5c-4 (redactor and masked wrapper), P6a-1 (stage rules). P8c merges after P8a, in parallel with P8b (plan-v3 section 7 step 8, line 159); it changes no file P8b changes (P8b writes `docs/kinds/` READMEs; UNVERIFIED that P8b touches no `tools/` file).
- **Problem in plain words:** The core has six replaceable parts ("kinds") that v1 promises: text folding, the stop switch, the spending meter, the redactor that masks personal data, the record store, and the safe error message ("diagnostic"). Each has its own tests, but nothing proves that all six work together in one ordinary run. The proof pack is one script that runs each kind at least once on made-up data with the fake model, prints one line per kind with how many times it ran correctly, and fails if any kind ran zero times. A test suite cannot give this on its own: a skipped test counts as green (probe below).
- **Source of the code and what is NOT taken:** new script, our own; no MANIFEST ids. Not taken: no live model call (R4, plan-v3 line 46), no paid service, no network, no Postgres requirement for the default run, no new dependency.

## Interface
- **Command:** `python tools/proof_pack.py [--data <dir>] [--store memory|postgres]`. Defaults: `--data demo_only/proof_pack`, `--store memory`. `postgres` reads its connection name through the secrets kind (named lookup, never a literal); see PENDING LEAD 2.
- **Output:** one line per kind, fixed order: `proof_pack kind=<name> runs=<n> result=ok|FAIL` for `textnorm, stop_state, meter, redactor, store, diagnostic, wall_alert`, then `proof_pack total_kinds=7 failed=<k>`.
- **Exit codes:** 0 = every kind `runs>=1` and no check failed; 1 = any kind `runs=0` or any check failed (the line names it); 2 = refused before any step: stage is not `demo` (R449, preamble rule 21), the llm kind selected is not the fake model, or the data folder or one of its files is missing or empty.
- **Counting rule (the core of the package):** a run counts only when (a) the step called the kind's real entry point through one helper `_call(kind, fn, *args, **kw)`, (b) `fn.__module__` is in a fixed allowlist per kind (for example `hadavin_sdk.guard.textnorm`), and (c) the step's check of the returned value passed. A step that never calls `_call`, calls a stand-in, swallows an exception, or gets a wrong answer leaves the count at 0. The printed line and the exit code are computed from the same counter dict, which `main()` also returns (for the tests).
- **Entry points used (each from its frozen ticket; all UNVERIFIED against code because those packages are not merged; the builder re-reads each at P8a's commit and writes the real line numbers in the evidence):**

| kind | entry point used | source | what the step checks |
|---|---|---|---|
| textnorm | `identity_key(raw) -> str`, `allow_equal(a, b) -> AllowVerdict` in `guard/textnorm.py` | `tickets/P1.md:39-43` (P1a) | a width variant gives the same key; a look-alike pair gives `LOOKALIKE` |
| stop_state | `Limits.stop(by)`, `Limits.status()`, `Limits.blocked()`, `Limits.reset(by, *, expect_version, expect_open)` | `tickets/P2a.md:85-88` (P2a-1) | blocked after stop; not blocked after a reset with the read pair |
| meter | `Meter(store)`, `Meter.reserve(agent_id, worst, caps, *, run_id=None) -> Hold`, `Meter.settle(reservation_id, actual) -> Settled`, `SpendMicro`, `Caps`, `OverBudget` | `tickets/P4b1.md:92-99` | first settle `applied=True` with the charged amount; second settle `applied=False`; a reserve over a made-up day cap raises `OverBudget` |
| redactor | `mask(text, session, *, untrusted)`, `restore(value, mapping, kinds)`, `MaskSession`, wrapper in `llm/masked.py`, over `FakeLLM` (`llm/fake.py:21`, records `.calls`) | `tickets/P5c.md:204-215`, `:301` | no made-up personal value reaches `FakeLLM.calls`; `restore` puts it back. How a `MaskSession` is opened: UNVERIFIED (not found in the lines read) |
| store | `MemoryStore` (`store/memory.py:28`), `create_run`/`get_run` (`:51`, `:57`), `missing_methods(store)` (`store/protocol.py:151`) | exists on main; P4d adds methods (`tickets/P4d.md:16`) | round trip of a made-up run; `missing_methods` returns `[]` |
| diagnostic | `diagnose(exc, *, step, facts=None) -> Diagnostic`, `render(d) -> str`, `Where.other` | `tickets/P5a.md:41`, `:47`, `:56`, `:62` | a made-up exception whose message holds a made-up e-mail renders with a closed code and without the e-mail |
| wall_alert | the P4c-2 daily wall path over `FakeChannel.notify` (`approvals/channel.py:85`, `:110`, records `.notices`) | `tickets/P4c.md:84`, `:349` | exactly one notice after two spends past the made-up daily cap. Exact P4c entry point: UNVERIFIED |

## Files
- create `tools/proof_pack.py`: the script (stdlib plus `hadavin_sdk`; `tools/` is not in the wheel, `tools/mutation_runner.py` header says so on main). Target size under 200 lines; if it grows past that, the builder says why in the PR.
- create `demo_only/proof_pack/` (new folder at the repo root; demo-only data rule): `note.txt` (one made-up short note with a made-up name, an `example.com` e-mail and a `555-01xx` phone number), `textnorm_pairs.json` (a width-variant pair and a look-alike pair, generic words only), `config.yaml` (stage `demo`, llm kind fake, channel kind fake, store memory), `recorded/` (the fake model's recorded replies, named `<sha256>-<attempt>.json` as the fake looks them up, `llm/fake.py:39-45`). No project words (order 53: no domain nouns, no vendor or client names); no real-looking secret; no credential of any shape.
- create `tests/test_proof_pack.py` (the tests below).
- change `CHANGELOG.md`: one entry. Nothing in `src/` changes. If a kind needs a change to be callable here, that is a defect of that kind's package, reported to the lead, not patched in P8c.
- **Existing core code reused (checked):** `llm/fake.py` `FakeLLM`; `store/memory.py` `MemoryStore`; `store/protocol.py` `missing_methods`; `approvals/channel.py` `FakeChannel`; `tools/mutation_runner.py` (P1m, `Mutant` at `:73`) for the mutants; `guard/redact.py` `redact` (`:862`) only through P5c's kind, never directly. Not relevant: `hashing.py`, `k1b/atomic.py`, `stats.py`, `evals.py`.
- **Security and least-privilege notes:** the script holds no credential in the default run. `--store postgres` gets its connection only through the secrets kind. Personal data: made-up only, and the redactor check asserts it never reaches the fake model. Stage `demo` only; P6a-1 refuses fake kinds in pilot and prod, so the pack never runs there (exit 2 is the pack's own guard, before any step).

## RUNG TABLE (ladder v2, orders 67/68: 0 client tool, 1 no-code, 2 core module, 3 existing free tool, 4 free library, 5 own code). Effort tier B (R450 m: internal tool, no client data, no new dependency).

| component | need | rung tried | evidence (source, date) or UNVERIFIED | licence (SPDX), version, date | what only our code gives | verdict |
|---|---|---|---|---|---|---|
| runner + counter + exit rule | run 7 kinds, count checked runs, print a line each, exit 1 on any zero | 0: CLIENT-EXCLUDED, 2026-11-06, plan-v3 line 114 (core tool, no client). 1: no-code flow cannot import Python kinds in-process; UNVERIFIED, not researched (tier B). 3: pytest considered | probe 2026-11-06: a test that only calls `pytest.skip` gives `1 skipped`, exit 0 (pytest 9.1.1 in the local env; `pyproject.toml:50` pins 9.2.0) | pytest: MIT (package metadata), 9.1.1, 2026-11-06 | a kind that is skipped or never called fails the run; per-kind count line the plan's command needs | KEEP-CODE (one stdlib file, under 200 lines) |
| run detection | know the kind really ran | 4: `sys.monitoring` (stdlib, Python 3.12+, `pyproject.toml:6`) considered | counts function entry, not a correct result; UNVERIFIED by run | PSF-2.0, CPython 3.12+, 2026-11-06 | count only after the result check passed | CUT (not used) |
| the seven kind steps | call each kind once | 2: the kinds themselves | entry points in the table above (frozen tickets) | n/a (our core) | nothing new: glue only, under about 15 lines per step | CUT-TO-CONFIG+GLUE |
| made-up data | inputs for each step | 4: Faker considered | adds a dependency for about 6 strings; UNVERIFIED version | not read (not used) | n/a | CUT-TO-CONFIG+GLUE (data files in `demo_only/`) |
| fake model, fake channel, memory store | no live call, no network | 2: `FakeLLM`, `FakeChannel`, `MemoryStore` | `llm/fake.py:21`, `approvals/channel.py:85`, `store/memory.py:28` (read 2026-11-06) | n/a (our core) | n/a | CUT-TO-CONFIG+GLUE (reuse) |
| tests of the pack | prove each zero-run case fails | 3: pytest + P1m mutation runner | `tools/mutation_runner.py:1-25` (read 2026-11-06) | pytest MIT 9.1.1, 2026-11-06 | n/a | KEEP-CODE (one test file) |

Enforcement status (R450 o): the table shape is checked by the lead's cloud_check; the 80 percent re-count is review-only.

## Tests (`tests/test_proof_pack.py`; all on made-up data, no network)
- **Z1-Z7, one per kind, the fail-before rows (each fails on a base where that kind ran zero times):** parametrised over the 7 kinds; the test removes that kind's step from the step table and asserts exit 1 and the line `kind=<name> runs=0 result=FAIL`. Fail-before: the same test against a copy of the script with that step present but its `_call` replaced by `return None` must also give exit 1 (a step that "ran" without calling the kind).
- **G1 green run:** default command exits 0; every line has `runs>=1`; the returned dict equals the printed lines.
- **C1-C7, one per kind, wrong answer:** the kind's entry point is monkeypatched to return a wrong but well-typed value (textnorm: always a new key; stop_state: `blocked()` stays false; meter: second settle `applied=True`; redactor: text returned unmasked; store: `get_run` returns a different id; diagnostic: render keeps the e-mail; wall_alert: zero or two notices). Each must give exit 1 with that kind's line FAIL.
- **E1-E7 raise:** the entry point raises; exit 1, not a crash with exit 0 and not a silent count.
- **S1 stand-in:** a step calls a local function instead of the kind; the module allowlist refuses it; exit 1.
- **N1 no network:** `socket.socket.connect` patched to raise; the green run still exits 0 (proves no live call). **N2:** config with a non-fake llm kind gives exit 2 and zero calls on the patched socket.
- **R1 stage:** config with stage `pilot` or `prod` gives exit 2 before any step.
- **H1-H3 hostile data:** data folder missing; `note.txt` empty; `textnorm_pairs.json` an empty list. Each gives exit 2 (never a green run with nothing checked).
- **D1 data stays demo-only:** no file under `src/` mentions `demo_only` (a `git grep` in the test); the wheel built by `uv build` lists no `demo_only/` or `tools/` path.
- Race or process tests: none (no shared state beyond one memory store per run). Contract suite: not this package (P4d owns the store contract).

## Mutant list (what the proof pack must catch; registered for the P1m runner; each killer named)
| id | mutant | killer |
|---|---|---|
| MP1 | a kind's step deleted from the step table (one mutant per kind, 7) | Z1-Z7 |
| MP2 | `_call` counts before the result check | C1-C7 |
| MP3 | `_call` wraps the call in `try/except Exception: pass` | E1-E7 |
| MP4 | module allowlist check removed | S1 |
| MP5 | final exit always 0 | Z1, C1 |
| MP6 | zero test reads `< 0` instead of `== 0`, or checks only the first kind | Z2-Z7 |
| MP7 | printed line built from a separate variable, not the counter | G1, Z1 |
| MP8 | redactor step sends the raw note to the fake model (wrapper bypassed) | C4 |
| MP9 | stage check removed | R1 |
| MP10 | llm-kind check removed | N2 |
| MP11 | missing or empty data treated as zero items, not exit 2 | H1-H3 |
| MP12 | meter step drops the second-settle check | C3 |

## Evidence commands (exact; raw output under `handover/evidence/P8c/`; run by a separate EVIDENCE RUNNER)
- `uv run --all-extras --group test python tools/proof_pack.py > handover/evidence/P8c/proofpack.txt 2>&1; echo "exit=$?" >> handover/evidence/P8c/proofpack.txt`
- `uv run --all-extras --group test python tools/proof_pack.py --store postgres > handover/evidence/P8c/proofpack-postgres.txt 2>&1; echo "exit=$?" >> handover/evidence/P8c/proofpack-postgres.txt` (local throwaway Postgres as in P4d; see PENDING LEAD 2)
- `uv run --all-extras --group test pytest -q tests/test_proof_pack.py > handover/evidence/P8c/tests.txt 2>&1; echo "exit=$?" >> handover/evidence/P8c/tests.txt`
- `uv run --all-extras --group test pytest -q > handover/evidence/P8c/full.txt 2>&1; echo "exit=$?" >> handover/evidence/P8c/full.txt` (once, at the final head)
- `uv run --all-extras --group test ruff check . > handover/evidence/P8c/ruff.txt 2>&1`; `uv run --all-extras --group test ruff format --check . >> handover/evidence/P8c/ruff.txt 2>&1`; `bandit -ll -r tools/proof_pack.py > handover/evidence/P8c/bandit.txt 2>&1`
- the P1m runner on MP1-MP12 (command as in `tools/mutation_runner.py`; flags UNVERIFIED) `> handover/evidence/P8c/mutants.txt 2>&1`
- `uv build > handover/evidence/P8c/build.txt 2>&1` and the wheel's file list; `git grep -n demo_only -- src > handover/evidence/P8c/grep-src.txt` (expected: empty)

## Gates
- **Reviewers:** one fresh egm pair (correctness + adversarial; diff, this ticket and the evidence only). Brief line: "Does a rung before this one (1 no-code, 2 core module, 3 free tool, 4 library) cover 80 percent or more, and is the licence recorded? A missing table or licence line is a Major." Genericity check (order 53): any project word in data, names or output is a Major.
- **Done =** `python tools/proof_pack.py` exits 0 at the merge commit with 7 lines `runs>=1`; Z1-Z7 and all other rows green; MP1-MP12 killed; ruff, format, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit green; `proofpack.txt` saved for plan-v3 section 9.
- **Rollback:** tag `pre-P8c`. No migration, no `src/` change; revert deletes the script, its tests and `demo_only/proof_pack/`.

## PENDING LEAD
1. Plan row names six kinds; P4c PENDING LEAD 9 adds the wall alert as a seventh line. Recommendation: keep it (7 lines); the section 9 expected result then reads "7 lines".
2. Store: plan-v3 line 78 makes Postgres the store default and memory demo-only. A memory-only run proves the demo backend only. Recommendation: the section 9 run uses both commands (memory and `--store postgres` on a throwaway local Postgres); the default stays memory so the pack runs without a database.
3. Brief cites plan-v3 line 117 for the P8c row; the row is at line 114 (line 117 is note 1). No action unless another file copies 117.
4. The `MaskSession` opening call (P5c) and the P4c wall entry point are not stated in the lines I read; the builder takes them from the merged code. Recommendation: accept; a missing entry point at build time is reported, not invented.
