# Ready-to-apply core patches (ORDER 012 item 2)

STATUS (2026-11-16, second fixer pass, static review: no database was started). Tested on scratch copies of commit `b4cce5b` (a copy made with
`git archive`: the files only, no git history). Commands and raw results: `../fix-patchcopies1.md` (first pass) and
`../../fix-patchcopies2.md` (this pass). Two words used below: "unpatched copy" = a fresh `git archive b4cce5b` with nothing applied;
"patched copy" = a fresh `git archive b4cce5b` with `C-01.patch` and then `A-01.patch` applied.

NOT checked, plainly:
- Every database behaviour (the audit outbox drain against a real Postgres, the dead-man query, the read-only login) is UNVERIFIED in this pass.
  The first pass ran the dead-man query once on a throwaway Postgres, not on the real store: cite it as "seen once on a throwaway Postgres, not the
  real store". The audit tests of A-01 use the in-memory table of the audit kind, not Postgres.
- The full suite was run in an archive folder, not in a real git checkout (two tests need git; see "pass criterion"). It has not been run in a real checkout.
- `C-01.patch` and `A-01.patch` were not rebuilt for commits after `b4cce5b`.

## Where the files are, and which commit they fit
- The files are in this folder: `handover/flows-audit/reviews-of-core-patches/patch-copies/` (`C-01.patch`, `A-01.patch`,
  `DEAD-MAN-CHECK.md`). There is no `G5-wording.patch` here and none must be created (see "G5 wording drop").
- They fit commit `b4cce5b` (the base all line numbers below refer to) and nothing newer. Checked on 2026-11-16 with `git apply --check`:
  `A-01.patch` (first version) also fitted `176a0cbe0` and `ec65e4614`; `C-01.patch` did NOT (exit code 1; the environment check in
  `config.py` and the head of `tests/warden_port/test_gate.py` changed). That check was made on the first version of `A-01.patch`; the second
  version (new tests only differ) was checked on `b4cce5b` only. On a newer commit, rebuild from the text of the hunks; not done here.
  Line numbers at head `ec65e4614`: Route `config.py:64`, `refused = []` at `config.py:393`.

## Apply recipe (tested on 2026-11-16, run from any folder)
```
P=/absolute/path/to/handover/flows-audit/reviews-of-core-patches/patch-copies   # absolute: the next lines change folder
cd /path/to/the/repository/with/the/git/history        # git archive needs the history
W=$(mktemp -d)                                         # a new empty folder, not a fixed /tmp path
mkdir "$W/unpatched" "$W/patched"
git archive b4cce5b | tar -x -C "$W/unpatched"         # the unpatched copy
git archive b4cce5b | tar -x -C "$W/patched"           # the patched copy, before the patches
cd "$W/patched"
git apply --check "$P/C-01.patch"; echo "check C-01 exit=$?"     # saw: exit=0, no other output
git apply --check "$P/A-01.patch"; echo "check A-01 exit=$?"     # saw: exit=0
git apply "$P/C-01.patch" && git apply "$P/A-01.patch"; echo "apply exit=$?"   # saw: exit=0
```
(`git apply` works in a folder that is not a git repository.) The order matters only for `DEAD-MAN-CHECK.md`, which needs `A-01.patch`.
The real change goes in as a branch and a pull request opened by the builder; nobody merges from here.

## How to prove it works (pass criterion)
Who runs it: a named person (the studio head or the lead; a human, not an agent session), on the patched copy or on the pull-request branch.
An agent that builds the change holds no approver credential and no executor credential: it opens the pull request and never merges.
(That sentence is the rule, not something this static pass could check: what the builder holds was not inspected.)

Run every command with no cloud settings in the environment (the repository rule `verify-tests-and-evals.md`), for example with `env -i`:

| Gate command | Pass means | Saw on the patched copy (2026-11-16) |
|---|---|---|
| `uv run --all-extras --group test ruff check` | exit 0 | exit 0, "All checks passed!" (run through `uv`, offline from its cache) |
| `uv run --all-extras --group test ruff format --check` | exit 0 | exit 0, "301 files already formatted" |
| `bandit -q -r src demos -ll` (the form in `.github/workflows/ci.yml:119`) | exit 0, no medium or high finding | exit 0, 0 findings, output only tool warnings about comments (the `bandit -ll -r src` form also exit 0) |
| the full test run below | exactly the named failures, no others | see next block |

### The full test run, the baseline and the rule
Command (the live and the timing tests are left out with the markers the repository defines in `pyproject.toml`: `live`, `perf`; CI does the same
at `ci.yml:88`, and runs the `perf` ones in a separate step, `ci.yml:94`, which this static pass did not run):
```
env -i PATH=/usr/bin:/bin HOME="$W/home" PYTHONPATH=src python -m pytest -q -p no:cacheprovider -m "not live and not perf" -rf > run.log 2>&1; echo "exit=$?"
grep '^FAILED' run.log | sed 's/ - .*//' | sort > failed.txt
```
Baseline (run the same command in the unpatched copy first): measured on 2026-11-16 on the unpatched copy of `b4cce5b`:
`2 failed, 9364 passed, 454 skipped, 26 deselected in 225.52s`, exit 1. The two failures, by name:
1. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` (scans the files under `handover/`; finds a vendor name in two of them)
2. `tests/test_repo_rules.py::test_licences_are_proprietary` (calls `git ls-files`, which fails in a folder that is not a git repository)

Rule: pass = the patched run's failed tests are exactly these two names and no others (`diff baseline-failed.txt failed.txt` prints nothing),
AND the passed count is the baseline's plus the number of new tests: 9364 + 32 = 9396, with the same skipped and deselected counts.
In a real checkout the second failure should disappear and the first one depends on what is in `handover/`; so in a real checkout, take the baseline
by running the same command on the base branch first, and compare the two failed-test lists the same way. This pass could not do that (no checkout run).
Result on the patched copy (2026-11-16): `2 failed, 9396 passed, 454 skipped, 26 deselected in 247.81s`, exit 1; the two failed names are exactly the two above, and 9396 = 9364 + 32. Raw lines in `../../fix-patchcopies2.md`.

Gate on the exit code of each command itself, never on a `| tail` pipe.

### Proof that the new tests fail on the old code
Run on the unpatched copy with only the two new test files copied in; the files are read from the patched copy:
```
cp "$W/patched/tests/test_a01_audit_reconcile.py" "$W/patched/tests/test_c01_route_limits.py" "$W/unpatched/tests/"
cd "$W/unpatched" && env -i PATH=/usr/bin:/bin HOME="$W/home" PYTHONPATH=src python -m pytest -q -p no:cacheprovider \
  tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py -rf     # expected exit 1
```
Seen: exit 1, `13 failed, 19 passed`. Each failure is about behaviour, not about a missing name (the tests write the numbers out and call only
code that already exists on the old tree):
- 6 price cases: `Failed: DID NOT RAISE ConfigError` (a price of 0 or -1 loads on old code).
- `test_max_tokens_above_the_ceiling_is_refused`: `DID NOT RAISE ConfigError` (200_001 loads on old code).
- `test_the_step_is_in_the_tick_list`: `'audit_reconcile' in ['sweep', 'reconcile', 'stuck', 'checkpoint', 'purge_evidence', 'reprobe_sources']` is false.
- `test_the_step_drains_the_outbox_and_logs_the_count`: the real tick loop ran and logged only `tick ok=True failed=-`; nothing drained.
- `test_a_kind_without_reconcile_fails_the_step_instead_of_recording_a_success`: `assert 0 == 1` (no step ran, so no failure was recorded).
- 3 log tests (`..._never_the_body`, `..._an_error_line_is_logged`, `local_dir_sink_logs...`): the captured log text is empty.
The 19 that pass on old code are controls: the priced live route and the fake model still load, `max_tokens=200_000` loads and `0` is refused (both
true on old code), and the 16 NaN and Infinity cases, which the existing pydantic field check already refuses, so they pin today's behaviour and
cannot fail on old code. NaN and Infinity: pydantic 2.14.1 (the version in the repository's lock file and in the `.venv` used); `match="finite"` was
confirmed by the passing run.

| Patch | Files | RUNG (tool ladder) | Tests added |
|---|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `tests/test_c01_route_limits.py` | existing code (the `Route` field and `Config` validator already exist) + one documented default in `defaults.py`; CODE-LAST holds: a safety guarantee (no spend limit may be bypassed by price 0) | 26 cases (6 zero or negative price, 16 NaN or Infinity price, 1 priced route, 1 fake model, 2 `max_tokens`) |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | existing code (`reconcile()` exists on the audit Protocol, `audit/protocol.py:27`; nothing in `src` calls it) + a 10-line tick step and log lines | 6 new tests + 2 edits |
| (G5 wording, no patch file) | `guard/redact.py`, `approvals/gate.py`, `tests/warden_port/test_gate.py` | text only: comments and docstrings, no behaviour | none needed |
| `DEAD-MAN-CHECK.md` | none (a documented check) | existing code: `tick_state` rows already exist | negative test described; seen once on a throwaway Postgres, not the real store |

## C-01: price above 0 at load, and a ceiling on `max_tokens`
- Price: for every route, `min(input, output) <= 0` is refused when `backends.llm.kind != "fake"` (the recorded fake never spends).
  Before: `Money` rejects floats only (`config.py` `Money` annotation), nothing refused 0 or a negative price.
  The replay path already had its own refusal (`k1b/replay.py:85-90`, called at :118); this closes the live path at the choke point.
- Which `llm.kind` values exist at `b4cce5b` (`backends/table.py:512-540`): `fake`, `anthropic`, `bedrock`, `openai_compat`, `gemini`. Only `fake`
  spends nothing. The recorded replay is not a kind: it is the `fake` kind with `recorded_dir`. The one config in the tree that names an llm kind is
  `tests/fixtures/config/config.yaml` (kind `fake`); `demos/` holds no config with an llm kind (grep for `llm` in yaml, yml, toml, json files outside
  `handover/`). **Open and needs the studio head's decision:** `openai_compat` also serves a local model (the file says "a local Ollama", a keyless
  `http` address on this machine is allowed, `backends/table.py:71-85`), whose honest price is 0. C-01 as written refuses that setup. Options: (a)
  keep the refusal and have such a config state a small non-zero price; (b) exempt `openai_compat` with a keyless loopback `base_url`. No code for (b)
  was written, because it changes what the patch promises and needs the decision first.
- NaN and Infinity: a price such as `NaN`, `sNaN`, `Infinity` or `-Infinity` never reaches that check. The existing field check of pydantic refuses it
  first ("Input should be a finite number"), and `load_config` turns that into a `ConfigError`. Seen on pydantic 2.14.1 for the live and the fake
  kind (16 cases in the test file). A new test pins it so a later library change cannot turn it into a raw `InvalidOperation`.
- `max_tokens`: `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; the ceiling is `200_000` in `defaults.py`, one place. **The number is a DEFAULT PENDING THE
  STUDIO HEAD'S YES** (my choice, not taken from a provider page; no live lookup here). If the studio head wants another value, change that one line;
  the tests write 200_000 and 200_001 out, so the two test lines change with it. Existing fixtures use 64 and 1024 (grep of `tests`); `demos/` has
  no route config.
- The test config for a live model is `{kind: anthropic, platform: api, api_key_secret_name: <name>}`; this matches `AnthropicSettings` in
  `backends/table.py:43-61` (platform `api` needs `api_key_secret_name`). `test_a_priced_live_route_still_loads` asserts those settings
  parsed, so a refusal elsewhere cannot hide behind the price rule. The fixture environment is `dev`, which the environment table does not refuse.
- Negative tests: price 0, 0.00 and -1 on input and on output are each refused for a live kind (6 cases, `match="zero or negative price"`); a priced
  live route loads; the fake kind with price 0 still loads (so the rule is not over-broad); `max_tokens` 200_001 is refused (`match="less than or equal
  to 200000"`), 0 is refused (`match="greater than 0"`), 200_000 loads.
- Cites at b4cce5b: `config.py:55-60` (Route), `:316` (Config), `:365` (`refused = []`, where the check goes), `defaults.py:104`.

## A-01: the tick drains the audit outbox and says when a write failed
- New last step `audit_reconcile` (append-only, as the tick contract asks): calls `app.audit.reconcile()` and logs `audit_reconcile drained=<n>`.
  The name fits the `tick_state` CHECK `^[a-z_]+$` (`0003_approvals_tick.sql:31`), so no migration is needed.
- A kind without `reconcile` now FAILS the step (error text "the audit kind has no reconcile", saved in `tick_state.last_error`, exit code 1 of the
  tick), instead of the first version's quiet skip that recorded a success. Why: a step that drained nothing and still recorded success would let the
  dead-man check show healthy. Checked: both audit kinds in the table (`local_dir`, `chain`: `backends/table.py:502-511`) have `reconcile`
  (`local_dir.py:126`, `chain.py:232`) and the audit protocol requires it (`audit/protocol.py:27`), so no shipped kind fails. `K1bAudit`
  (`k1b/audit_sink.py:26`) has no `reconcile`, but it is built only for the `k1b` commands (`cli.py:213`), never as the `app.audit` the tick uses
  (`app.py:161`, built by `make("audit", ...)`); so it cannot cause this today.
- `ChainAudit.write_outcome` and `LocalDirSink.write_outcome` log a WARNING when an outcome goes to the outbox (error type and event id
  only, never the body). Both also log an ERROR when even the outbox write fails (event held in memory only).
- The tests drive the real tick loop (`run_tick`, with the step list cut to `audit_reconcile`) against a minimal fake store and the in-memory audit
  table. They assign `log._append`, `log._db.run` and `sink._write` on instances.
- Negative tests: drain count and empty outbox after the step; a kind without reconcile fails the step and records no success; the log line holds type
  and id but not the error text or run id (chain kind); outbox failure logs the memory-only error (chain kind and local-directory kind);
  `test_p7_tick.py` now lists the new step and asserts a saved success row for it.
- Cites at b4cce5b: `tick.py:177` (checkpoint, same pattern), `:249` (STEPS), `chain.py:215-231` (write_outcome), `:232` (reconcile),
  `local_dir.py:110-125`, `protocol.py:27`, `tests/test_p7_tick.py:81`.
- Which login the tick runs under: not stated by the patches. `REVIEW.md` row X-6 (and `store/migrate.py:25-26`, `:61`) say one runtime login serves the
  agent, the tick and the approval receiver; the grant map gives that role `SELECT, INSERT, DELETE` on `audit_outbox` (`store/migrate.py:59`), which is
  what `reconcile` needs. Whether a deployment uses a separate tick login: not stated: the lead answers.

## G5 wording drop (text and comments only; no patch file: rebuild by hand from this list)
The earlier patch file is gone on purpose (its context lines carried a personal handle). Exact old sentences, taken with `git show b4cce5b:<path>`;
the new sentences are proposed text for the studio head to approve. Nothing else changes; the three guard-test files named in ORDER 009 are not touched.
No code in `approvals/gate.py` implements G5: its functions at `b4cce5b` are `sanitise_text`, `withhold_commands`, `normalise` and helpers; there is no
leak-check function (list of `def` lines read from the archive). So the old sentences claim a check that does not exist.
1. `src/hadavin_sdk/guard/redact.py`, module docstring (lines 16-17 of `b4cce5b`).
   Old: "the control; HIGHENTROPY is their backstop; the outbound gate's G5 re-runs them, independently, on everything that leaves."
   New: "the control; HIGHENTROPY is their backstop. There is NO independent second check on what leaves: the outbound gate's G5 (a second scan) is
   not built in this repository."
2. `src/hadavin_sdk/approvals/gate.py`, module docstring, paragraph starting "The outbound gate: the last check on what WARDEN says before it leaves
   the process." (line 9 of `b4cce5b`). Add one sentence after the header block (before "The original module notes follow", line 7 context):
   New: "Only G3 (untrusted text) and G4 (commands) are built here. G5 (leaks) and G2 (unverifiable claims) are NOT built; the notes below describe
   the original design, not this module."
3. `src/hadavin_sdk/approvals/gate.py`, the sentence "- **G5, leaks.** If the final text still contains anything the redactor classes as secret (every
   kind except the identifiers an operator may choose to show), the message is BLOCKED and a stub goes out instead: a person reads the full report
   locally." Prefix with "(Design only, not built here.) ". Same prefix for the G2 paragraph ("- **G2, unverifiable claims** (`hedge`, Phase 1).").
4. `src/hadavin_sdk/approvals/gate.py`, "Verdicts: PASS (unchanged), REWRITE (G3 removed something), BLOCK (G5)." Append "(BLOCK exists only in the
   original design.)".
5. `tests/warden_port/test_gate.py`, line 3 of the docstring. Old: "The outbound gate v0 (Phase 0): G3 untrusted-text hygiene, G5 leak block, and
   the Slack wiring." New: "The outbound gate v0 (Phase 0): G3 untrusted-text hygiene and the Slack wiring (the G5 leak block is not built here)."
Left unchanged on purpose: `gate.py:203` ("... `AKIA<ZWSP>...` passed G5 and went out whole"), a history note about the original module.
Check after hand edit: `ruff format --check` and `ruff check` on the three files; the test file is a docstring change only.
Risk: sentences 2-4 touch a docstring the earlier review (REVIEW.md G-1) said might understate existing protection; the strength of the redaction
patterns that exist was not compared here. UNVERIFIED.

## Not checked
No live model or network call. No database was started (standing order of this review). `K1bAudit` was not changed. The patches were not rebuilt for
commits after `b4cce5b`. The `perf` tests were not run. The full suite ran outside a git checkout. Nothing was committed or pushed.
