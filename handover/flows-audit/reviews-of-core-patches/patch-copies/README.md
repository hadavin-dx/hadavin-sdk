# Core patch copies A-01 and C-01 (ORDER 012 item 2): a ready copy, NOT to be applied now

**STATUS (read this first).** `../REVIEW.md:5` (the file one folder up) says, word for word: "A-01 is DEFERRED, the C-01 extras (the token ceiling)
are CUT, the G5 wording patch is KEPT (text only)", and item 3 of its list says "C-01: DO NOT APPLY NOW". Those three are the lead's default of 2026-11-16, not a confirmed decision of the
studio head; he may veto them. So today: **apply nothing from this folder**, and when something is applied later, only on a copy of the commit `b4cce5b`, never on head
(section "Which commit these patches fit").
- **Price check (C-01):** the default, if the studio head keeps it, is `C-01-price-only.patch` (price rule only, no `max_tokens` ceiling, no `defaults.py` change, 24 new tests, plus 6 of A-01 = 30 in the recipe).
  `C-01.patch` is the alternative that also carries the ceiling that was cut (26 new tests; 32 with A-01). Use one of the two, never both. Do not edit either file by hand.
- **A-01 (the tick drains the audit outbox):** there is NO applicable A-01 today. Even if the studio head says yes to row 1 of the decision table, `A-01.patch` must stay off until rows 5 and 6 are decided,
  and row 6 needs a per-row guard in the chain drain for which no patch file exists. The file is kept only as a ready copy.
- **G5 wording:** text only, no patch file (section "G5 wording drop").

Date of this text: 2026-11-16, fifth fixer pass. Nothing that needs a database was run (no database was started); the lint, `git apply --check` and test runs named below were re-run in this pass.

## Words used here (plain meanings; each word keeps this one meaning in this folder)
| Word | Meaning here |
|---|---|
| tick | the small program a scheduler starts every 30 to 60 seconds; it runs the housekeeping jobs listed under "step" and then exits |
| step | one housekeeping job inside a tick (`sweep`, `reconcile`, `stuck`, `checkpoint`, ...). A step records "ok" or "failed" in the table `tick_state`. Not "a step of this recipe": those are called "recipe step" |
| kind | one pluggable part of the core (for example the audit kind, the llm kind), chosen by name in the config. Every kind has a default and at least one alternative |
| audit kind | the kind that writes the tamper-evident audit trail; two exist at `b4cce5b`: `chain` (in the database) and `local_dir` (files in a folder) |
| outbox | a holding table (`audit_outbox`) or folder where an audit event waits when it could not be written at once; "draining" it means writing the waiting events for real |
| reconcile (three different things) | (1) the tick step `reconcile` (matches finished work against the store); (2) the audit method `reconcile()` that drains the outbox; (3) the tick step `audit_reconcile` that A-01 adds, which calls (2). This folder always writes which one |
| studio head, database administrator, migrations login | "the studio head" = the person who owns the studio and decides. "the migrations login" = the database login that owns the tables and runs the migrations (`store/migrate.py`); only it can hand out rights on a table. "the database administrator" = the named human who is allowed to sign in with that login (the studio head names him or her). This folder never uses the bare words "owner" or "database owner" |
| studio head vs lead | the studio head is a person (called "the owner" in older studio notes). The lead is the AI session that directs the other sessions and runs the reviews; the lead is not a person |
| builder vs fixer | a builder is a session that builds a change; a fixer is a session that corrects an earlier piece of work after a review. Both open pull requests and never merge |
| gate, check, guard test, verdict | "gate" = a command the repository requires to succeed before a change goes in; locally these are four: `ruff check`, `ruff format --check`, `pytest` and `bandit -ll` (the pull-request checks CodeQL, SonarCloud and CodeRabbit run on GitHub, cannot be run here and are NOT part of any local verdict). "check" = any command or reading whose result is reported. "guard test" = a test in `tests/test_repo_rules.py`, `tests/test_no_reference_material.py` or `tests/test_lockin_guard.py` (the repository rules; listed by name under "Pass rule"). "verdict" = exactly one of three names defined under "Pass rule": PASSED, ADDS NO NEW FAILURE, NOT PASSED |
| `b4cce5b` and "head" | `b4cce5b` = the commit `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c`, the one the patches were built on; "head" = the newest commit of this working copy (branch `cloud/flows-audit`): `5b5b8933a` when this pass ran. Earlier text said `f05790e42`; `src/` and `tests/` are identical in the two, so every head result below holds for both. Every file and line cite below says "at `b4cce5b`" or "at head" |
| unpatched copy / patched copy | a fresh clone checked out at `b4cce5b` with nothing applied / the same with `C-01-price-only.patch` (or `C-01.patch`) then `A-01.patch` applied |
| G5, G2, G3, G4 | rules of an older outbound text gate: G3 = remove untrusted text, G4 = withhold commands, G5 = block leaked secrets, G2 = flag unverifiable claims. Only G3 and G4 exist in the code |
| RUNG, CODE-LAST | the ladder from "use something that already exists" to "write our own code" (`handover/BRIEF-PREAMBLE.md` rule 20): our own code is the last resort |
| I, my, the assistant | the fixer session (an assistant run, not a person) that last edited this file. Older text said "I" without saying who |
| `../REVIEW.md` and its row ids (C-3, C-4, C-6, C-8, A-1, A-3, A-6, A-8, G-1, X-2, X-5, X-6, D-3) | the review file one folder up (`handover/flows-audit/reviews-of-core-patches/REVIEW.md`); the ids are rows of its findings table: find a row by its id, or an item by its number in the plain summary at the top |
| "Decision 18, 19, 23" | numbered questions the studio head is asked in item 11 of `../REVIEW.md`; here only: 18 = where the price check lives, 19 = the stand-in price of a self-hosted model |
| ORDER 012 | `handover/flows-audit/ORDERS.md`, section "ORDER 012": the lead's order that asked for these copies. ORDER 009 is cited in the G5 section; its text is not in this checkout (searched `handover/`), so what is said about it there is UNVERIFIED |
| `system-map` Decision B | the "Decision B" of the system-map review folder `handover/flows-audit/reviews-of-system-map/`; its text was not found there. Here it means only: who picks, and pays for, a second alert channel (row D4 of `DEAD-MAN-CHECK.md`) |
| BRIEF-PREAMBLE rules 9 and 20 | numbered rules in `handover/BRIEF-PREAMBLE.md`: 9 = cloud sessions open pull requests and never merge, 20 = code last |
| dead-man check | a query run by something outside the tick that alarms when the tick has stopped; see `DEAD-MAN-CHECK.md` |

## Decisions that are not mine to make (ONE table; each row says who decides and whether it stops a merge)
| # | Decision | Who decides | Blocks a merge? | Default if nobody decides |
|---|---|---|---|---|
| 1 | Bring A-01 back at all (it is deferred) | studio head (may veto the lead's default) | yes: nothing of A-01 is applied while it is deferred | stays deferred |
| 2 | Keep only the price check of C-01 and where it lives (`REVIEW.md` rows C-3 and Decision 18) | studio head | yes for C-01 | C-01 stays "do not apply now"; if it is applied, it is `C-01-price-only.patch` |
| 3 | The `max_tokens` ceiling (`200_000` in `defaults.py`) | studio head; the number is my placeholder, not from a provider page | only if the ceiling comes back; it is cut today | ceiling cut; use `C-01-price-only.patch`, which has no ceiling |
| 4 | Self-hosted model price: the RECORDED decision (`REVIEW.md` row C-8) is: the only exemption is the kind `fake`; a self-hosted model sets a positive stand-in price. The number of that price | studio head (Decision 19) | no (the rule is recorded); each config that has price 0 must be changed first (see "Rollout note") | none: a config with price 0 refuses to start |
| 5 | Which database login the tick runs under, and whether the drain gets its own login (`REVIEW.md` rows X-2, X-5, X-6) | studio head | yes for A-01 (rating "Major, conditional") | one runtime login, accepted in writing by the studio head |
| 6 | Per-row guard in the chain drain (`REVIEW.md` row A-6) before A-01 goes live | studio head decides; a builder writes it | yes for A-01 (see "A-01 precondition") | not applied: one bad row turns the step red on every tick |
| 7 | G5 wording: approve the new sentences | studio head | no (text only) | not applied |
| 8 | Dead-man check: the limit in seconds, the second alert channel, who is the database administrator who creates the login | studio head names the person; see `DEAD-MAN-CHECK.md` | no (a note, no core code) | not set up |
| 9 | Two baseline failures caused by files under `handover/`: a banned vendor name in two studio notes, and non-proprietary licence files in copies of seven other projects (see the two baseline failures under the gate recipe) | the lead fixes them in a separate change; I may not edit them | yes: the repository gate needs every guard test green | the gate stays red at `b4cce5b` |

## Who runs each step
| Step | Who | What they hold |
|---|---|---|
| Clone, apply, run the gates (recipe below) | any person or session; it writes only into a new temporary folder | no credential, no cloud setting (the commands run with `env -i`) |
| Open the pull request with a patch | a builder session | no approver credential, no executor credential; opens the pull request and never merges (`CLAUDE.md`: cloud sessions never merge) |
| Merge | the lead (`handover/BRIEF-PREAMBLE.md` rule 9), after the gates and reviews | a normal merge right; nothing here changes branch protection |
| Create the dead-man login, run its grants | the database administrator (a named human; the studio head names him or her) | the migrations login; not an agent |
| Everything marked "run on the real store" | the lead asks the studio head for a test database | not available to this static review |

## Where the files are
This folder, `handover/flows-audit/reviews-of-core-patches/patch-copies/`, holds three patch files (`C-01.patch` = price check plus ceiling, `C-01-price-only.patch` = price check only, `A-01.patch`), one note
(`DEAD-MAN-CHECK.md`), this file, and no G5 patch file: the earlier G5 patch file is gone on purpose and must NOT be recreated (see "G5 wording drop"; G5 is a hand-edit list).

## Which commit these patches fit (the one place that says it: do NOT apply any of them on a copy of head)
All three patches were built on `b4cce5b`, and every test number, exit code and criterion in this file is valid only for a copy of `b4cce5b`. Do not apply any patch on a copy of head.
`git apply --check` run in this pass (2026-11-16) on fresh `git archive` extracts, each in its own new folder, no cloud settings:
| Patch | at `b4cce5b` | at head (`5b5b8933a`) | why |
|---|---|---|---|
| `C-01.patch` | rc 0 | **rc 1** (`error: patch failed: src/hadavin_sdk/config.py:362`) | hunk 2 of `config.py` has the context line `if self.environment != "dev":` (`config.py:366` at `b4cce5b`); at head the stage check was rewritten and the line is `if is_live(self.environment):` (`config.py:394`) |
| `C-01-price-only.patch` | rc 0 | **rc 1** (same error, same line) | same hunk 2, same context line |
| `A-01.patch` | rc 0 | rc 0 (it applies, but nobody ran its tests at head, so it is not cleared for head either) | its files did not change in the lines it touches |
A patch for head would have to be rebuilt from the text of its hunks and re-tested; not done, because nothing here is to be applied now.
- Line numbers: every `config.py`, `ci.yml` and fixture line cite in this file is at `b4cce5b` unless it says "head". Where they differ:
  `Route` `config.py:55` (head `:64`); `Config` `:316` (head `:332`); `refused = []` `:365` (head `:393`); the allowed-in-demo table is `DEV_ONLY` at
  `backends/table.py:593` (head: `DEMO_ONLY`, `table.py:593`); `ci.yml` bandit line `:119` (head `:181`, and the head form adds `tools`);
  `ci.yml` test line `:88` (head `:92`), timing-test line `:94` (head `:100`); fixture `tests/fixtures/config/config.yaml:2` says `environment: dev` at `b4cce5b`
  and `environment: demo` at head (the stage names were renamed to demo, pilot, prod after `b4cce5b`).

## Apply and test recipe (runnable; written 2026-11-16; run in ONE terminal so the variables stay set)
Needs: `git`, `uv` (it installs the Python and the packages), and either network access once or a warm `uv` cache. Python 3.12 or newer (`pyproject.toml`
`requires-python`; CI uses 3.12 and 3.13). Repository source: the GitHub repository `https://github.com/hadavin-dx/hadavin-sdk` (the commit is on its branch
`cloud/core-hardening`), or, as the fallback, the checkout this working copy lives in (`/home/user/hadavin-sdk` in the session that wrote this).
Use a clone, not a plain `git archive` of the files: the repository rule tests ask git for the list of tracked files (`tests/test_repo_rules.py`, `tracked_files`), which a folder without
git data cannot answer. Whatever the patches add must be in that list too, hence the `git add -A` line below (nothing is committed).
```
P=/home/user/hadavin-sdk/handover/flows-audit/reviews-of-core-patches/patch-copies   # absolute path of THIS folder
SRC=https://github.com/hadavin-dx/hadavin-sdk                                         # or the fallback path of a local checkout
SHA=b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c
C=C-01-price-only.patch           # DEFAULT: price check only, +30 tests with A-01. The alternative is C=C-01.patch (price check plus ceiling, +32); the studio head decides (decision table, rows 2 and 3)
W=$(mktemp -d)                    # new empty working folder
for t in unpatched patched; do
  git clone -q "$SRC" "$W/$t"
  git -C "$W/$t" fetch -q origin "$SHA"          # a plain clone may not hold the commit
  git -C "$W/$t" checkout -q "$SHA"
done
cd "$W/patched"
for f in "$C" A-01.patch; do git apply --check "$P/$f"; echo "check $f exit=$?"; done   # expect 0 and 0 (both patches apply to b4cce5b, one after the other)
git apply "$P/$C" && git apply "$P/A-01.patch"; echo "apply exit=$?"                     # expect 0
git add -A                         # new test files must appear in `git ls-files`; this stages, it does not commit
```
`C-01-price-only.patch` and `C-01.patch` cannot be applied together (both change `config.py` at the same place): choose one. The expected number of new tests is **30 with the default `C-01-price-only.patch`**
and 32 with `C-01.patch`. (`git apply` writes the files; nothing is committed. Add `--offline` after `uv run` below only if the machine has no network and a warm `uv` cache; add
`HTTPS_PROXY="$HTTPS_PROXY"` after `env -i` if the network needs a proxy.)

### Expected exit codes (ONE table; the gate commands, run with no cloud settings in the environment as `.claude/rules/verify-tests-and-evals.md` asks, which `env -i` gives)
Gate on the exit code of the command itself, never on a `| tail` pipe. `E="env -i PATH=$PATH HOME=$HOME"`; run each command in the folder named in the column head.
| Command (all start with `$E uv run --all-extras --group test`) | unpatched copy | patched copy |
|---|---|---|
| `ruff check` | 0 | 0 |
| `ruff format --check` | 0 | 0 |
| `bandit -q -r src demos -ll` (the form of `ci.yml:119` at `b4cce5b`; the form at head adds `tools`, a folder that does not exist at `b4cce5b`; bandit prints one `nosec` warning, which is not a failure) | 0 | 0 |
| `pytest -q -p no:cacheprovider -m "not live and not perf" -rf` (the full run, below) | **1** while the two baseline failures exist, 0 after they are fixed | **1** while the two baseline failures exist, 0 after they are fixed |
| `pytest` on the two new test files copied onto the unpatched copy (proof section) | 1 (the new tests fail on old code) | not run |

### Baseline, then the patched run (the full test run)
The markers `live` and `perf` come from `pyproject.toml`; CI leaves them out of the main run (`ci.yml:88` at `b4cce5b`, `:92` at head) and runs `perf` in its own step
(`:94`, head `:100`), which is not part of this recipe.
```
run() {  # $1 = folder, $2 = tag
  ( cd "$1" && env -i PATH="$PATH" HOME="$HOME" uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" -rf > "$W/$2.log" 2>&1; echo "$2 exit=$?" )
  tail -n 1 "$W/$2.log"
  grep '^FAILED' "$W/$2.log" | sed 's/ - .*//' | sort > "$W/$2-failed.txt"
}
run "$W/unpatched" baseline        # 1. the baseline FIRST, on the unpatched copy; exit 1 is expected while the two baseline failures below exist
run "$W/patched"   patched         # 2. the patched copy
diff "$W/baseline-failed.txt" "$W/patched-failed.txt" && echo "(a) same failed tests"
# (d1) the number of licence problems, from both logs; each must print a number, and the two must be equal
n1=$(grep -o 'Left contains [0-9]* more items' "$W/baseline.log"); n2=$(grep -o 'Left contains [0-9]* more items' "$W/patched.log")
echo "baseline: [$n1]  patched: [$n2]"; [ -n "$n1" ] && [ "$n1" = "$n2" ] && echo "(d1) ok" || echo "(d1) FAILED"
# (d2) the files the vendor-name test lists (paths only; the banned strings are cut off and never printed)
offenders() { grep -m1 '^E *AssertionError: vendor brand strings' "$1" | sed 's/^E *AssertionError: [^:]*: //' | tr ';' '\n' | sed -E 's/^ *//; s/: .*//' | sort; }
offenders "$W/baseline.log" > "$W/o-base.txt"; offenders "$W/patched.log" > "$W/o-pat.txt"
[ -s "$W/o-base.txt" ] && diff "$W/o-base.txt" "$W/o-pat.txt" && echo "(d2) ok" || echo "(d2) FAILED"
```
**Pass rule.** Clauses (a) to (d) say "this patch adds no new failure"; they are all needed because the two guard tests that are already red can hide a new problem inside them.
(a) the `diff` prints nothing: the patched run fails exactly the tests the baseline fails, no others.
(b) the patched count line shows the baseline's `passed` plus 30 (default `C-01-price-only.patch` with `A-01.patch`) or plus 32 (`C-01.patch` with `A-01.patch`), the same `skipped` and `deselected`, and the same number of `failed`.
(c) the exit codes of all four gate commands are the ones in the table above, and the two `pytest` exit codes are equal.
(d) the two red guard tests do not hide a new problem: (d1) both logs print a NUMBER after "Left contains" (an empty result is a failure, not a match) and the two numbers are equal (10 at `b4cce5b`), for `test_licences_are_proprietary`; (d2) the list of offending files in the message of `test_no_vendor_brand_string_is_tracked` is not empty and is the same in both logs (3 files at `b4cce5b`, see the baseline failures below), because that test scans untracked files too, so a banned string inside a patch or a new test file would add an entry while (a) to (c) stay silent.
The **guard tests** are the 99 tests in `tests/test_repo_rules.py`, `tests/test_no_reference_material.py` and `tests/test_lockin_guard.py` (`CLAUDE.md` says "the repo guard tests" without a list; this is this folder's definition). Today exactly two of them are red: `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` and `tests/test_repo_rules.py::test_licences_are_proprietary`.
The three **verdicts** (use exactly these names):
- **PASSED**: (a) to (d) hold, and the full run of the patched copy has no failed test at all (so the two baseline failures are fixed, decision table row 9, and its exit code is 0).
- **ADDS NO NEW FAILURE**: (a) to (d) hold, but the baseline failures still exist, so the repository gate is still red. The patch is clean; no pull request with it may be merged until row 9 is done. **This is the verdict today.**
- **NOT PASSED**: any other result: a lint or bandit exit code that differs from the table, a failed test the baseline does not have, a wrong count, a (d) check that prints nothing or differs.
Only the four local gate commands count here. CodeQL, SonarCloud and CodeRabbit (named in `CLAUDE.md`) run on the pull request on GitHub, cannot be run in this recipe, and are not part of any verdict above.

Known baseline failures at `b4cce5b` (seen in this pass in a repository with one commit made from a fresh `git archive b4cce5b`; the earlier passes also saw them in real clones). Both are caused by files under `handover/` and neither is touched by the patches:
1. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`: THREE files are listed (the earlier text said two): `handover/demo/portal/portal-design-v2.md` and `handover/BRIEF-PREAMBLE-studio-2026-11-06.md` hold a banned vendor name (the list `BANNED`, `tests/test_no_reference_material.py:19-30`);
   `handover/reviews/P1a-idempotence-probe.txt` is "not UTF-8 text, cannot be scanned". I do not print the banned string here.
2. `tests/test_repo_rules.py::test_licences_are_proprietary`: 10 problems, all in copies of other projects under `handover/promotion-inputs/`: the `LICENSE` file of `apexc`, `dealdesk`, `helios`,
   `killswitch`, `portal-kit`, `refunds` and `warden` is not the proprietary licence text, and the `pyproject.toml` of `killswitch` (licence and authors) and of `portal-kit` (authors) is not
   the studio's.
**Correction of my own earlier text:** the first and second pass said failure 2 came only from running in a folder without git history. That was wrong: it also fails in a real clone, for the reason above.
Who must fix both: the lead (change or remove those studio copies, or tell the tests to skip `handover/`, in a separate change); I did not edit them (my files were limited to this folder).

### Proof that the new tests fail on the old code
Run on the unpatched copy with only the two new test files copied in (copied from the patched copy):
```
cp "$W/patched/tests/test_a01_audit_reconcile.py" "$W/patched/tests/test_c01_route_limits.py" "$W/unpatched/tests/"
cd "$W/unpatched" && env -i PATH="$PATH" HOME="$HOME" uv run --all-extras --group test pytest -q -p no:cacheprovider \
  tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py -rf ; echo "exit=$?"     # expected exit 1
```
Seen in the first pass and again in the third pass with `C-01.patch`: exit 1, `13 failed, 19 passed`. With `C-01-price-only.patch` (fourth pass, same recipe): exit 1, `12 failed, 18 passed` (no ceiling test, so 6 price + 6 A-01 failures). Each failure is about behaviour, not a missing name:
- 6 price cases: `Failed: DID NOT RAISE ConfigError` (a price of 0 or -1 loads on old code).
- `test_max_tokens_above_the_ceiling_is_refused` (only in `C-01.patch`): `DID NOT RAISE ConfigError` (200_001 loads on old code).
- `test_the_step_is_in_the_tick_list`: `'audit_reconcile' in [...]` is false.
- `test_the_step_drains_the_outbox_and_logs_the_count`: the real tick loop ran and logged only `tick ok=True failed=-`; nothing drained.
- `test_a_kind_without_reconcile_fails_the_step_instead_of_recording_a_success`: `assert 0 == 1` (no step ran, so no failure was recorded).
- 3 log tests (`..._never_the_body`, `..._an_error_line_is_logged`, `local_dir_sink_logs...`): the captured log text is empty.
The 19 that pass on old code (18 with the price-only file) are controls: the priced live route and the fake model still load, `max_tokens=200_000` loads and `0` is refused (both true on old code),
and 16 NaN and Infinity price cases, which pydantic already refuses (pydantic 2.14.1 in `uv.lock`; `match="finite"` depends on that library's message text, so a library
upgrade may need that one word changed). Those 16 pin today's behaviour and cannot fail on old code.

### Results of the fourth pass (2026-11-16): price-only patch and the stricter criterion
Seen in this pass, fresh `git archive b4cce5b` folders turned into a git repository with one commit (not a clone; `uv run --offline`, warm cache, `env -i`):
- `git apply --check`: `C-01.patch` rc 0, `C-01-price-only.patch` rc 0, `A-01.patch` rc 0.
- `C-01-price-only.patch` then `A-01.patch`, full run `-m "not live and not perf"`: `2 failed, 9394 passed, 454 skipped, 26 deselected in 248.76s`, exit 1; 9394 = 9364 + 30; failed: the same two guard tests. `test_licences_are_proprietary`: `Left contains 10 more items` (baseline: 10). Verdict by the criterion above: **NOT PASSED** (clause (e)).
- The three test files `test_a01_audit_reconcile.py`, `test_c01_route_limits.py`, `test_p7_tick.py` on that copy: `71 passed` (24 + 6 + 41).
- The same two new test files on unpatched code: `12 failed, 18 passed`. The price-only test file alone on unpatched code: `6 failed, 18 passed`; patched: `24 passed`.
- `ruff check` (src and the test file) `All checks passed!`; `ruff format --check`: `104 files already formatted`. `bandit` was not re-run in this pass (the price-only patch adds no code that bandit has not seen in `C-01.patch`).
- Not re-run in this pass: the full run with `C-01.patch` (the third-pass numbers below still stand for it), the `perf` tests, and the baseline (the third-pass baseline numbers are reused).

### Results of the runs of the third pass (2026-11-16)
All numbers below were seen in this pass, in real clones checked out at `b4cce5b` (with `uv run --offline`, from a warm `uv` cache; Python 3.13.18, pydantic 2.14.1 from `uv.lock`):
- `git apply --check` on a fresh `git archive b4cce5b` extracted into a new folder, run with `env -i`: `C-01.patch` exit 0, `A-01.patch` exit 0 (final text of both files).
- Baseline, unpatched clone, full run: `2 failed, 9364 passed, 454 skipped, 26 deselected in 239.30s`, exit 1. Failed: `test_no_vendor_brand_string_is_tracked`, `test_licences_are_proprietary` (causes above).
- Patched clone, full run: `2 failed, 9396 passed, 454 skipped, 26 deselected in 277.71s`, exit 1; `diff` of the two failed lists prints nothing (same two names); 9396 = 9364 + 32.
  **Honest limit:** this full run used the text of `A-01.patch` from 10 minutes before the final one; the final text only differs by two lines (the step logs `int(fn())`; the test for a kind
  without `reconcile` asserts the tick's ERROR line). After that change I re-ran only `tests/test_a01_audit_reconcile.py`, `tests/test_c01_route_limits.py` and `tests/test_p7_tick.py`: `73 passed`.
  The full run was not repeated on the final text.
- Gates on the final patched clone: `ruff check`: `All checks passed!`; `ruff format --check`: `301 files already formatted`; `ruff format --check` on the 8 touched python files: `8 files already formatted`;
  `bandit -q -r src demos tools -ll`: exit 0.
- New tests on the unpatched clone (only the two new test files copied in), final text: `13 failed, 19 passed in 6.43s`.

## What each patch is
| Patch | Files | RUNG (tool ladder) | Tests added |
|---|---|---|---|
| `C-01-price-only.patch` | `config.py`, `tests/test_c01_route_limits.py` | as `C-01.patch`, without the ceiling | 24 cases (the 26 of `C-01.patch` minus the 2 `max_tokens` cases) |
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
- `max_tokens`: `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; ceiling `200_000` in `defaults.py`: this part is CUT today (decision table, row 3) and exists only in `C-01.patch`, not in `C-01-price-only.patch`. If it returns, the studio head
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
