# Core patch copies A-01 and C-01 (ORDER 012 item 2): a ready copy, NOT to be applied now

**STATUS (read this first).** `REVIEW.md:5` (in the folder above this one) says, word for word: "A-01 is DEFERRED, the C-01 extras (the token ceiling)
are CUT, the G5 wording patch is KEPT (text only)", and `REVIEW.md` item 3 of its list (line 62) says "C-01: DO NOT APPLY NOW ... The file as written carries the
token ceiling (cut by the lead's default) and does not apply to this checkout." Those three are the lead's default of 2026-11-16, not a confirmed decision of the
studio head; he may veto them. So: **do not apply `A-01.patch` or `C-01.patch` today.** Everything below is the ready copy, kept so that it can be applied
quickly if the studio head decides to bring A-01 back or to keep the price check of C-01. `C-01.patch` as it stands still carries the token ceiling that was cut; to
apply only the price check, delete the `max_tokens` line (hunk 1) and the `defaults.py` hunk first (see the decision table, row 2).

Date of this text: 2026-11-16, third fixer pass, static for databases: no database was started.

## Words used here (plain meanings; each word keeps this one meaning in this folder)
| Word | Meaning here |
|---|---|
| tick | the small program a scheduler starts every 30 to 60 seconds; it runs the housekeeping jobs listed under "step" and then exits |
| step | one housekeeping job inside a tick (`sweep`, `reconcile`, `stuck`, `checkpoint`, ...). A step records "ok" or "failed" in the table `tick_state`. Not "a step of this recipe": those are called "recipe step" |
| kind | one pluggable part of the core (for example the audit kind, the llm kind), chosen by name in the config. Every kind has a default and at least one alternative |
| audit kind | the kind that writes the tamper-evident audit trail; two exist at `b4cce5b`: `chain` (in the database) and `local_dir` (files in a folder) |
| outbox | a holding table (`audit_outbox`) or folder where an audit event waits when it could not be written at once; "draining" it means writing the waiting events for real |
| reconcile (three different things) | (1) the tick step `reconcile` (matches finished work against the store); (2) the audit method `reconcile()` that drains the outbox; (3) the tick step `audit_reconcile` that A-01 adds, which calls (2). This folder always writes which one |
| owner (three different things) | "the studio head" = the person who owns the studio and decides; "database owner" = the database login that owns the tables; "table owner" = the same idea for one table. This folder never uses the bare word "owner" |
| studio head vs lead | the studio head is a person (called "the owner" in older studio notes). The lead is the AI session that directs the other sessions and runs the reviews; the lead is not a person |
| builder vs fixer | a builder is a session that builds a change; a fixer is a session that corrects an earlier piece of work after a review. Both open pull requests and never merge |
| pass, check, gate | "gate" = a command the repository requires to succeed before a change goes in (`ruff`, `pytest`, `bandit`); "check" = any command or reading whose result is reported; "pass" = a gate command ended with the exit code the table below names |
| `b4cce5b` and "head" | `b4cce5b` = the commit `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c`, the one both patches were built on; "head" = commit `f05790e42`, the newest commit of this working copy on 2026-11-16 (branch `cloud/flows-audit`). Every file and line cite below says "at `b4cce5b`" or "at head" |
| unpatched copy / patched copy | a fresh clone checked out at `b4cce5b` with nothing applied / the same with `C-01.patch` then `A-01.patch` applied |
| G5, G2, G3, G4 | rules of an older outbound text gate: G3 = remove untrusted text, G4 = withhold commands, G5 = block leaked secrets, G2 = flag unverifiable claims. Only G3 and G4 exist in the code |
| RUNG, CODE-LAST | the ladder from "use something that already exists" to "write our own code" (BRIEF-PREAMBLE rule 20): our own code is the last resort |
| dead-man check | a query run by something outside the tick that alarms when the tick has stopped; see `DEAD-MAN-CHECK.md` |

## Decisions that are not mine to make (ONE table; each row says who decides and whether it stops a merge)
| # | Decision | Who decides | Blocks a merge? | Default if nobody decides |
|---|---|---|---|---|
| 1 | Bring A-01 back at all (it is deferred) | studio head (may veto the lead's default) | yes: nothing of A-01 is applied while it is deferred | stays deferred |
| 2 | Keep only the price check of C-01 and where it lives (`REVIEW.md` rows C-3 and Decision 18) | studio head | yes for C-01 | C-01 stays "do not apply now" |
| 3 | The `max_tokens` ceiling (`200_000` in `defaults.py`) | studio head; the number is my placeholder, not from a provider page | only if the ceiling comes back; it is cut today | ceiling cut; delete the hunk |
| 4 | Self-hosted model price: the RECORDED decision (`REVIEW.md` row C-8) is: the only exemption is the kind `fake`; a self-hosted model sets a positive stand-in price. The number of that price | studio head (Decision 19) | no (the rule is recorded); each config that has price 0 must be changed first (see "Rollout note") | none: a config with price 0 refuses to start |
| 5 | Which database login the tick runs under, and whether the drain gets its own login (`REVIEW.md` rows X-2, X-5, X-6) | studio head | yes for A-01 (rating "Major, conditional") | one runtime login, accepted in writing by the studio head |
| 6 | Per-row guard in the chain drain (`REVIEW.md` row A-6) before A-01 goes live | studio head decides; a builder writes it | yes for A-01 (see "A-01 precondition") | not applied: one bad row turns the step red on every tick |
| 7 | G5 wording: approve the new sentences | studio head | no (text only) | not applied |
| 8 | Dead-man check: the limit in seconds, the second alert channel, who is the database owner who creates the login | studio head names the person; see `DEAD-MAN-CHECK.md` | no (a note, no core code) | not set up |
| 9 | Two files under `handover/` hold a banned vendor name (see "Pass criterion", failure 1) | the lead rewords them (they are studio notes); I may not edit them | yes: the repository gate needs every guard test green | the gate stays red at `b4cce5b` |

## Who runs each step
| Step | Who | What they hold |
|---|---|---|
| Clone, apply, run the gates (recipe below) | any person or session; it writes only into a new temporary folder | no credential, no cloud setting (the commands run with `env -i`) |
| Open the pull request with a patch | a builder session | no approver credential, no executor credential; opens the pull request and never merges (`CLAUDE.md`: cloud sessions never merge) |
| Merge | the lead (BRIEF-PREAMBLE rule 9), after the gates and reviews | a normal merge right; nothing here changes branch protection |
| Create the dead-man login, run its grants | a named human database owner (studio head names him or her) | the database owner login; not an agent |
| Everything marked "run on the real store" | the lead asks the studio head for a test database | not available to this static review |

## Where the files are, and which commit they fit
- This folder: `handover/flows-audit/reviews-of-core-patches/patch-copies/`: `C-01.patch`, `A-01.patch`, `DEAD-MAN-CHECK.md`, this file. The earlier
  G5 patch file is gone on purpose and must NOT be recreated (see "G5 wording drop"). So there is no four-file set: two patches, one note, one hand-edit list.
- `git apply --check` of both patches on fresh `git archive` copies, run 2026-11-16 in this pass:
  at `b4cce5b`: `C-01.patch` exit 0, `A-01.patch` exit 0; at head (`f05790e42`): `C-01.patch` exit 1 (`error: patch failed: src/hadavin_sdk/config.py:362`),
  `A-01.patch` exit 0. C-01 fails at head because the stage check was rewritten after `b4cce5b`: hunk 2's context line is
  `if self.environment != "dev":` (at `b4cce5b`, `config.py:366`) but at head the line is `if is_live(self.environment):` (`config.py:394`).
  `C-01.patch` therefore must be rebuilt from the text of its hunks before it can go onto head; not done (C-01 is "do not apply now").
- Line numbers: every `config.py`, `ci.yml` and fixture line cite in this file is at `b4cce5b` unless it says "head". Where they differ:
  `Route` `config.py:55` (head `:64`); `Config` `:316` (head `:332`); `refused = []` `:365` (head `:393`); the allowed-in-demo table is `DEV_ONLY` at
  `backends/table.py:593` (head: `DEMO_ONLY`, `table.py:593`); `ci.yml` bandit line `:119` (head `:181`, and the head form adds `tools`);
  `ci.yml` test line `:88` (head `:92`), timing-test line `:94` (head `:100`); fixture `tests/fixtures/config/config.yaml:2` says `environment: dev` at `b4cce5b`
  and `environment: demo` at head (the stage names were renamed to demo, pilot, prod after `b4cce5b`).

## Apply and test recipe (runnable; written 2026-11-16; run in ONE terminal so the variables stay set)
Needs: `git`, `uv` (it installs the Python and the packages), and either network access once or a warm `uv` cache. Python 3.12 or newer (`pyproject.toml`
`requires-python`; CI uses 3.12 and 3.13). Repository source: the GitHub repository `https://github.com/hadavin-dx/hadavin-sdk` (the commit is on its branch
`cloud/core-hardening`), or, as the fallback, the checkout this working copy lives in (`/home/user/hadavin-sdk` in the session that wrote this).
A tree with no git history (a plain archive of the files) can run the patches but fails the repository rule test `test_licences_are_proprietary`
(it calls `git ls-files`), so use a clone.
```
P=/home/user/hadavin-sdk/handover/flows-audit/reviews-of-core-patches/patch-copies   # absolute path of THIS folder
SRC=https://github.com/hadavin-dx/hadavin-sdk                                         # or the fallback path of a local checkout
SHA=b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c
W=$(mktemp -d)                    # new empty working folder
for t in unpatched patched; do
  git clone -q "$SRC" "$W/$t"
  git -C "$W/$t" fetch -q origin "$SHA"          # a plain clone may not hold the commit
  git -C "$W/$t" checkout -q "$SHA"
done
cd "$W/patched"
git apply --check "$P/C-01.patch"; echo "check C-01 exit=$?"     # saw 0
git apply --check "$P/A-01.patch"; echo "check A-01 exit=$?"     # saw 0
git apply "$P/C-01.patch" && git apply "$P/A-01.patch"; echo "apply exit=$?"   # saw 0
```
(`git apply` writes the files; nothing is committed. Add `--offline` after `uv run` below only if the machine has no network and a warm `uv` cache; add
`HTTPS_PROXY="$HTTPS_PROXY"` after `env -i` if the network needs a proxy.)

### Gates on the patched copy (each must end with the exit code shown)
Run each command with no cloud settings in the environment (repository rule `.claude/rules/verify-tests-and-evals.md`), which `env -i` gives. Gate on the
exit code of the command itself, never on a `| tail` pipe.
```
cd "$W/patched"
E="env -i PATH=$PATH HOME=$HOME"
$E uv run --all-extras --group test ruff check;                 echo "ruff check exit=$?"          # expect 0
$E uv run --all-extras --group test ruff format --check;        echo "ruff format exit=$?"         # expect 0
$E uv run --all-extras --group test bandit -q -r src demos tools -ll; echo "bandit exit=$?"        # expect 0 (the form of ci.yml:181 at head)
```

### Baseline, then the patched run (the full test run)
The markers `live` and `perf` come from `pyproject.toml`; CI leaves them out of the main run (`ci.yml:88` at `b4cce5b`, `:92` at head) and runs `perf` in its own step
(`:94`, head `:100`), which this pass did not run.
```
run() {  # $1 = folder, $2 = tag
  ( cd "$1" && env -i PATH="$PATH" HOME="$HOME" uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" -rf > "$W/$2.log" 2>&1; echo "$2 exit=$?" )
  tail -n 1 "$W/$2.log"
  grep '^FAILED' "$W/$2.log" | sed 's/ - .*//' | sort > "$W/$2-failed.txt"
}
run "$W/unpatched" baseline        # 1. the baseline FIRST, on the unpatched copy; exit 1 is expected while failure 1 below exists
run "$W/patched"   patched         # 2. the patched copy
diff "$W/baseline-failed.txt" "$W/patched-failed.txt" && echo "same failed tests"
```
**Pass criterion:** (a) the `diff` prints nothing (the patched run fails exactly the tests the baseline fails, no others); (b) the patched count line shows
the baseline's `passed` plus 32, with the same `skipped` and `deselected`; (c) the two exit codes are equal (both 1 while the baseline failure exists, both 0 once it is
fixed). This is "no new failure", not "all green": all guard tests must be green before a real merge (`CLAUDE.md`, gate list), which needs failure 1 fixed (decision table, row 9).

Known baseline failure at `b4cce5b` (seen in this pass, see "Results"):
1. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` fails because two files hold a banned vendor name (the list `BANNED`, `tests/test_no_reference_material.py:19-30`):
   `handover/demo/portal/portal-design-v2.md` and `handover/BRIEF-PREAMBLE-studio-2026-11-06.md`. The patches do not cause or touch it. Who must fix: the lead (reword the two
   studio notes in a separate change); I did not edit them (my files were limited to this folder) and I do not print the banned string here.
(The second failure of the earlier pass, `test_licences_are_proprietary`, came only from running in a folder without git history; with a clone it passes.)

### Proof that the new tests fail on the old code
Run on the unpatched copy with only the two new test files copied in (copied from the patched copy):
```
cp "$W/patched/tests/test_a01_audit_reconcile.py" "$W/patched/tests/test_c01_route_limits.py" "$W/unpatched/tests/"
cd "$W/unpatched" && env -i PATH="$PATH" HOME="$HOME" uv run --all-extras --group test pytest -q -p no:cacheprovider \
  tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py -rf ; echo "exit=$?"     # expected exit 1
```
Seen in the first pass: exit 1, `13 failed, 19 passed`. (This third pass re-ran it: see "Results".) Each failure is about behaviour, not a missing name:
- 6 price cases: `Failed: DID NOT RAISE ConfigError` (a price of 0 or -1 loads on old code).
- `test_max_tokens_above_the_ceiling_is_refused`: `DID NOT RAISE ConfigError` (200_001 loads on old code).
- `test_the_step_is_in_the_tick_list`: `'audit_reconcile' in [...]` is false.
- `test_the_step_drains_the_outbox_and_logs_the_count`: the real tick loop ran and logged only `tick ok=True failed=-`; nothing drained.
- `test_a_kind_without_reconcile_fails_the_step_instead_of_recording_a_success`: `assert 0 == 1` (no step ran, so no failure was recorded).
- 3 log tests (`..._never_the_body`, `..._an_error_line_is_logged`, `local_dir_sink_logs...`): the captured log text is empty.
The 19 that pass on old code are controls: the priced live route and the fake model still load, `max_tokens=200_000` loads and `0` is refused (both true on old code),
and 16 NaN and Infinity price cases, which pydantic already refuses (pydantic 2.14.1 in `uv.lock`; `match="finite"` depends on that library's message text, so a library
upgrade may need that one word changed). Those 16 pin today's behaviour and cannot fail on old code.

### Results of the runs of this pass (2026-11-16, third pass)
RESULTS_PLACEHOLDER

## What each patch is
| Patch | Files | RUNG (tool ladder) | Tests added |
|---|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `tests/test_c01_route_limits.py` | existing code (the `Route` field and the `Config` validator already exist) + one documented default in `defaults.py`; CODE-LAST holds: a safety guarantee (no spend limit may be bypassed by price 0) | 26 cases (6 zero or negative price, 16 NaN or Infinity price, 1 priced route, 1 fake model, 2 `max_tokens`) |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | existing code (`reconcile()` exists on the audit Protocol, `audit/protocol.py:27`; nothing in `src` calls it) + a short tick step and log lines | 6 new tests; `test_p7_tick.py` gets one hunk with 2 changed assertions |
| (G5 wording, no patch file) | `guard/redact.py`, `approvals/gate.py`, `tests/warden_port/test_gate.py` | text only: comments and docstrings, no behaviour | none needed |
| `DEAD-MAN-CHECK.md` | none (a documented check) | existing code: `tick_state` rows already exist | negative test described; seen once on a throwaway Postgres, not the real store |

## C-01: price above 0 at load (and, in the file as written, a ceiling on `max_tokens`)
- Price: for every route, `min(input, output) <= 0` is refused when `backends.llm.kind != "fake"` (the recorded fake never spends). Before: `Money` rejects floats only
  (`config.py` `Money` annotation at `b4cce5b`), nothing refused 0 or a negative price. The replay path already had its own refusal (`k1b/replay.py:85-90`, called at
  `:118`); this closes the live path at the choke point.
- Stage rule behind the exemption (decision table, row 4, recorded in `REVIEW.md` row C-8): the only kind with no price rule is `fake`, and `fake` is itself a
  demo-only kind (`DEV_ONLY` at `backends/table.py:593`, head `DEMO_ONLY`) refused in live stages (`config.py:366-368` at `b4cce5b`, `:394-396` at head). So in a live
  stage nothing is exempt. There is no exemption for a keyless loopback address or for the kind `openai_compat`, because that kind also points at paid hosted endpoints and an
  address test would reopen the bug for them.
- **Rollout note (exact text, C-6 and C-8):** "Any pilot or production config with a price of 0 or a negative price now refuses to start. A model you run yourself
  (kind `openai_compat`, for example a local Ollama) needs a positive stand-in price: the number you set is what the machine costs per million tokens (for example the machine's
  hourly cost divided by the millions of tokens it handles in an hour), so the per-run, daily and monthly limits still fire. Change that config before the update."
  The demo `demos/ask-your-data/askdata/config.py:61-70` builds its `Route` itself and never passes through this check (C-3); no yaml, json or toml file under `demos/` holds a price.
  Rollback note: the check lives only in `Config`; to go back, revert the hunk. Configs kept outside this tree (a client's own repository) are not visible from here and must be
  checked by whoever owns them.
- **Missing test, to be added if C-01 returns:** `test_a_self_hosted_model_priced_zero_is_refused_and_a_notional_price_loads` (kind `openai_compat`, `http` loopback, no key: price 0 raises
  `ConfigError`; a positive stand-in price loads). It does not exist in `test_c01_route_limits.py` today.
- Not covered by the patch (stated, not fixed here): routes built without `load_config` (C-3: the demo builds `Route` itself); and the replay check tests `== 0` (`k1b/replay.py:87`),
  so a negative price passes replay while C-01 refuses it at load (C-4); a tiny positive price such as 0.000001 passes both and still makes a cap useless (C-4).
- NaN and Infinity: a price such as `NaN`, `sNaN`, `Infinity` or `-Infinity` never reaches that check; the existing field check of pydantic refuses it first ("Input should be a
  finite number") and `load_config` turns that into a `ConfigError` (16 cases in the test file; pydantic 2.14.1).
- `max_tokens`: `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; ceiling `200_000` in `defaults.py`: this part is CUT today (decision table, row 3). If it returns, the studio head
  confirms the number; change that one line and the two test lines that write 200_000 and 200_001. Existing fixtures use 64 and 1024; `demos/` has no route config.
- The test config for a live model is `{kind: anthropic, platform: api, api_key_secret_name: <name>}` (matches `AnthropicSettings`, `backends/table.py:43-61`).
  `test_a_priced_live_route_still_loads` asserts those settings parsed. The fixture environment is `dev` at `b4cce5b` (`demo` at head), which the environment table does not refuse.
- Which `llm.kind` values exist at `b4cce5b` (`backends/table.py:512-541`): `fake`, `anthropic`, `bedrock`, `openai_compat`, `gemini`. Only `fake` spends nothing; the
  recorded replay is not a kind but `fake` with `recorded_dir`. The one config in the tree that names an llm kind is `tests/fixtures/config/config.yaml` (kind `fake`).
- Negative tests: price 0, 0.00 and -1 on input and on output are each refused for a live kind (6 cases, `match="zero or negative price"`); a priced live route loads; the fake kind with
  price 0 still loads; `max_tokens` 200_001 is refused (`match="less than or equal to 200000"`), 0 is refused (`match="greater than 0"`), 200_000 loads.
- Cites at `b4cce5b`: `config.py:55-60` (Route), `:316` (Config), `:365` (`refused = []`, where the check goes), `defaults.py:104`.

## A-01: the tick drains the audit outbox and says when a write failed
- New last step `audit_reconcile` (append-only, as the tick contract asks): calls `app.audit.reconcile()` (the outbox drain, meaning 2 in the words box) and logs
  `audit_reconcile drained=<n>`. The name fits the `tick_state` CHECK `^[a-z_]+$` (`0003_approvals_tick.sql:31`), so no migration is needed. The docstring hunk in `tick.py` also adds
  `reprobe_sources` to the contract line (A-8), and `tests/test_p7_tick.py` gets one hunk: the step list gains the new name and an assertion that a saved success row exists for it.
- A kind without `reconcile` FAILS the step (error text "the audit kind has no reconcile", saved in `tick_state.last_error`; exit code 1 of the tick **when the store is reachable**;
  `tick.py:357-369` returns 4 when the store is unreachable after the steps) instead of the first version's quiet skip. Checked: both audit kinds (`local_dir`, `chain`:
  `backends/table.py:502-511`) have `reconcile` (`local_dir.py:126`, `chain.py:232`), and the audit protocol requires it (`audit/protocol.py:27`). `K1bAudit`
  (`k1b/audit_sink.py:26`) has none, but it is built only for the `k1b` commands (`cli.py:213`), never as the `app.audit` the tick uses (`app.py:161`).
- `ChainAudit.write_outcome` and `LocalDirSink.write_outcome` log a WARNING when an outcome goes to the outbox (error type and event id only, never the body) and an ERROR when even the outbox
  write fails.
- **A-01 precondition (REVIEW.md row A-6, must be in place before this goes live):** in the chain kind, `audit/chain.py:243` calls `AuditEvent.model_validate_json(body)` with no guard, so one
  bad outbox row raises before the `DELETE` on `:244`; the row stays (nothing is lost), but every row after it (ordered by `event_id`, `:239`) is never drained on any later tick, and the
  step goes red on every tick. A-01.patch does not change `reconcile`. Without the per-row guard, turning A-01 on can turn a healthy-looking system red and block draining. (The local
  directory kind moves an unreadable file to `outbox/corrupt/` and carries on, but silently.) The guard is decision-table row 6.
- **Which login runs the step (REVIEW.md row X-2, Major if A-01 returns):** the patch says nothing. One runtime login serves the agent, the tick and the approval receiver (row X-6;
  `store/migrate.py:25-26`, `:61`); it already holds `SELECT, INSERT, DELETE` on `audit_outbox` (`migrate.py:59`), which `reconcile` needs, so no new grant. Whether to accept that
  breadth in writing or to give the drain its own login (X-5.1) is decision-table row 5. The per-action reason (read waiting rows, write them to the trail, delete a written row) and a
  negative test (the drain login cannot write other tables) are not in the patch; the least-privilege rule asks for both for a new write function.
- **A-1 (wording to fix when A-01 returns):** the docstring says the step drains events held "or in memory"; the memory list `_pending` (`chain.py:173`) lives only in the process that
  wrote it, so a tick process cannot drain the agent's memory list. And the error text says "held in memory only"; the exact fact is "lost if this process exits".
- **A-3:** `audit_reconcile drained=0` is logged for an empty outbox and for a stuck backlog alike (`_drain` and the database-down path swallow errors, `chain.py:238-255`). So the log line cannot
  show a backlog; see the "What it does not cover" paragraph of `DEAD-MAN-CHECK.md`.
- **A-8:** the docstring hunk named above and the extra assertion in `test_p7_tick.py` are now named (they were not in the first README).
- The tests drive the real tick loop (`run_tick`, with the step list cut to `audit_reconcile`) against a minimal fake store and the in-memory audit table; they assign `log._append`,
  `log._db.run` and `sink._write` on instances. In this third pass the test for a kind without `reconcile` got a log assertion (before, it took `caplog` and never read it:
  the tick's ERROR line `step=audit_reconcile error_kind=RuntimeError` is now asserted), and the step logs `int(fn())`, so a kind whose `reconcile` returns `None` fails the
  step (red in `tick_state`) instead of printing a logging error and recording a success. The test count stays 6 new tests (one test file grew by one line).
- Negative tests: drain count and empty outbox after the step; a kind without reconcile fails the step and records no success; the log line holds type and id but not the error text or run id
  (chain kind); outbox failure logs the memory-only error (chain and local-directory kinds); `test_p7_tick.py` lists the new step and asserts a saved success row for it.
- Cites at `b4cce5b`: `tick.py:177` (checkpoint, same pattern), `:249` (STEPS), `chain.py:215-231` (write_outcome), `:232` (reconcile), `local_dir.py:110-125`, `protocol.py:27`,
  `tests/test_p7_tick.py:81` (edit at `:86-95`).

## G5 wording drop (text and comments only; no patch file: rebuild by hand from this list)
The earlier patch file is gone on purpose (its context lines carried a personal handle). Exact old sentences, taken with `git show b4cce5b:<path>`; the new sentences are proposed
text for the studio head to approve (decision table, row 7). Nothing else changes; the three guard-test files named in ORDER 009 are not touched. No code in `approvals/gate.py`
implements G5: its functions at `b4cce5b` are `sanitise_text`, `withhold_commands`, `normalise` and helpers; there is no leak-check function. So the old sentences claim a check that does not exist.
1. `src/hadavin_sdk/guard/redact.py`, module docstring (lines 16-17 of `b4cce5b`).
   Old: "the control; HIGHENTROPY is their backstop; the outbound gate's G5 re-runs them, independently, on everything that leaves."
   New: "the control; HIGHENTROPY is their backstop. There is NO independent second check on what leaves: the outbound gate's G5 (a second scan) is not built in this repository."
2. `src/hadavin_sdk/approvals/gate.py`, module docstring. The line "The original module notes follow." is line 7 of `b4cce5b`; the paragraph "The outbound gate: the last check on what WARDEN says
   before it leaves the process." is line 9. Insert the new sentence after line 7 (before that paragraph).
   New: "Only G3 (untrusted text) and G4 (commands) are built here. G5 (leaks) and G2 (unverifiable claims) are NOT built; the notes below describe the original design, not this module."
3. `src/hadavin_sdk/approvals/gate.py`, the sentence "- **G5, leaks.** If the final text still contains anything the redactor classes as secret (every kind except the identifiers an operator may choose to show),
   the message is BLOCKED and a stub goes out instead: a person reads the full report locally." Prefix with "(Design only, not built here.) ". Same prefix for the G2 paragraph ("- **G2, unverifiable claims** (`hedge`, Phase 1).").
4. `src/hadavin_sdk/approvals/gate.py`, "Verdicts: PASS (unchanged), REWRITE (G3 removed something), BLOCK (G5)." Append "(BLOCK exists only in the original design.)".
5. `tests/warden_port/test_gate.py`, line 3 of the docstring. Old: "The outbound gate v0 (Phase 0): G3 untrusted-text hygiene, G5 leak block, and the Slack wiring."
   New: "The outbound gate v0 (Phase 0): G3 untrusted-text hygiene and the Slack wiring (the G5 leak block is not built here)."
Left unchanged on purpose: `gate.py:203` ("... `AKIA<ZWSP>...` passed G5 and went out whole"), a history note about the original module.
Check after the hand edit: `ruff format --check` and `ruff check` on the three files; the test file is a docstring change only.
Risk: sentences 2-4 touch a docstring that `REVIEW.md` row G-1 said might understate existing protection; the strength of the redaction patterns that exist was not compared. UNVERIFIED.

## Not checked
No live model or network call to a model. No database was started (standing order of this review). `K1bAudit` was not changed. The patches were not rebuilt for commits after
`b4cce5b` (C-01 does not apply at head, see above). The `perf` tests were not run. A run with an EMPTY `uv` cache was not made (the runs used a warm cache, offline). Nothing was committed or pushed.
