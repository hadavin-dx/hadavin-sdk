# P8c round 1 resolve (egm:egm-resolve, AUTO mode, author)

- **Status:** resolved. Ticket `tickets/P8c.md` is now **revision 2, FROZEN** (lead order 84 item 2: one review round, then freeze, build after P8a). Only its BUILD NOTES section may grow, append-only.
- **Target:** `tickets/P8c.md` (revision 1, 97 lines, full file) -> revision 2, 116 lines.
- **Gate:** AUTO mode. The skill's interactive gate was skipped because the lead's brief said so. Every PROPOSE FIX below was applied in one batch. This file replaces the skill's default `goldfish_review_report.md`, because the brief named this file.
- **Findings:** `reviews/P8c-round1-design.md` (D-F1..D-F11) and `reviews/P8c-round1-codebase.md` (C-F1..C-F19). The two reports reuse the same F numbers, so this file prefixes them D- and C-.
- **Facts checked by me on the snapshot `main-1e4752f` (read-only):**
  - `config.py:52` (`extra="forbid"`), `:55-59` (Route), `:317` (environment Literal dev/pilot/prod), `:366-369` (fake kinds refused outside `dev`), `:436` (`load_config`; `_read_yaml` at `:418` returns `{}` for a missing file).
  - `backends/table.py:582-589` (DEFAULTS has no `llm` and no `audit`) and `:593-602` (DEV_ONLY).
  - `limits.py:14` and `:20-30` (`blocked(agent_id) -> list[str]`, which also reads the budget).
  - `llm/fake.py:25`, `:40`, `:44` (the call is recorded BEFORE the raise at `:47`).
  - `approvals/channel.py:85`, `:101`, `:110`.
  - `tools/mutation_runner.py:73-104` (Mutant), `:214` (`--noconftest`), `:365-376` (run_mutants), `:464-474` (the copy holds only src, the listed tests and `extra_dirs`), `:177-190` (`_locate` lists the copied tree, so `tools` must be in `extra_dirs`).
  - `tools/scan_repo.py` (it has no rule for e-mail or phone patterns).
  - `pyproject.toml:6`, `:50` (pytest 9.2.0 is in group `dev`, which is the default group, `:62`), `:54` (bandit is in group `scan`).
  - Frozen tickets: `P2a.md:84`, `:87`; `P4b1.md:92-100`; `P1.md:42`, `:44` (`fold_key is identity_key`); `P4c.md:49`, `:84`, `:101`, `:128`, `:343`; `P5c.md:141`, `:204-215`; `P6a.md:15`; `P8b.md:78` (docs only).
  - `sys.monitoring` exists on the local CPython 3.13.18.

## Honest note (first)
- **Not checked: the pytest skip probe on 9.2.0.** pytest is not installed here, and there is no network. The RUNG TABLE says UNVERIFIED, and a new evidence command makes the evidence runner rerun the probe. The 9.1.1 probe of revision 1 ran in another environment, and I did not rerun it.
- **Not checked: pytest options.** "pytest has no built-in fail-on-skip option" is from memory and is marked UNVERIFIED.
- **Not checked: Faker.** I did not read its licence or version. It is rejected, not added.
- **Not checked: `tests/` on main.** The snapshot has no `tests/`. So these are open:
  - the BANNED name list that `scan_repo.py` reads;
  - whether the repo tests flag `demo_only/` or the made-up e-mail and phone;
  - the `tests/<topic>_mutants.py` pattern. I took it from frozen tickets that name `tests/stop_state_mutants.py` and others, not from code.
- **Not checked: entry points of unmerged packages** (P1a/b, P2a-1, P4b1, P4c, P5a, P5c, P4d). Revision 2 adds names from the frozen tickets only. The builder confirms them at P8a's commit.
- **Not checked: P5c placeholders.** I do not know whether P5c placeholders are the same on every run. That decides whether a pre-made recording can match (PENDING LEAD 8).
- **Not run: the counts.** The 33 test rows and 22 mutants are counted from the ticket text.
- **Not done by design:** I ran nothing that writes outside the ticket and this file. No commit, no push, no DECISIONS.md, no questions-for-lead.md.
- **One deviation from the lead worker's list.** C-F1 says to "rename stage to environment". I went one step further: the pack now holds NO environment literal at all. The core validator refuses fake kinds outside the one allowed environment, and the pack maps `ConfigError` to exit 2. So rev 1's own stage check and its mutant MP9 were replaced by "the validator is bypassed" (MP11, killer R1).

## Decisions

| id(s) | category | decision |
|---|---|---|
| D-F1 | PROPOSE FIX | Positive redactor checks: `len(calls) >= 1`, no made-up value in `json.dumps(calls)`, at least one placeholder present, `restore` gives the original. New mutant MP10 (the model call is skipped), killer G1. |
| D-F2, C-F12 | PROPOSE FIX | Allowlist table with one row per kind. The check is function identity (`is`, or `__func__` for a bound method), never `__module__`. New S2 test (a `functools.wraps` stand-in) and MP5. The store counts `missing_methods` only together with the round trip. |
| D-F3 | PROPOSE FIX (option a) | Cut `--store postgres`. The total line prints `store=memory`. Added v1.1 row V1. Old PENDING LEAD 2 is withdrawn; new item 5 replaces it. |
| D-F4 | PROPOSE FIX | Rung table filled in: rung 1 is excluded with a reason (order 67: guarantee-class steps never live in a no-code flow); Faker becomes a dated REJECTED line; `sys.monitoring` is given as CPython 3.12.0+ (PEP 669); the 9.2.0 probe is UNVERIFIED plus an evidence command; I weighed the pytest fail-on-skip hook plus junit counts and found them under 80 percent (no per-kind command line, no identity check, and `--noconftest` at `mutation_runner.py:214` turns a conftest hook off); the old 1-7 scale is mapped to the new 0-5 scale. |
| D-F5 | PROPOSE FIX | Who makes `recorded/`: the test helper `write_recording`, using the call recorded before the raise (`llm/fake.py:44-47`). `UnknownRecording` gives exit 2 (a data error). New H4 row. Placeholder determinism is PENDING LEAD 8. |
| D-F6 | PROPOSE FIX | A public `STEPS` dict and a fixed, independent `EXPECTED_KINDS` tuple. Lines are printed by walking the tuple. The script-copy variant is dropped. |
| D-F7 | PROPOSE FIX | D1 is a stdlib scan of `src/`. The wheel check moves to the evidence commands. The evidence uses `-rs`, and 0 skipped is expected. |
| D-F8, C-F1, C-F2 | PROPOSE FIX | The pack calls `load_config` (`config.py:436`). The real keys are listed. "stage" is renamed to the core `environment` field, and the value is whatever the merged core allows (`dev` on main, `demo` after P0t). The pack's own check covers the llm, channel and store kinds only. P6a-1 is dropped from depends-on. |
| D-F9, C-F16 | PROPOSE FIX | wall_alert stays as the 7th line, marked blocked-on-merge for the exact count. The check is `>= 1`, and the second spend adds none. `== 1` only if merged P4c guarantees it. The registry, `alert_to` and claim wiring are named. |
| D-F10, C-F15 | PROPOSE FIX | Counts fixed: rev 1 had 12 ids but really 18 mutants. MP6 is split into MP7a and MP7b. Every row has one killer. 22 mutants now. |
| D-F11 | PROPOSE FIX (Nit) | Deleted "under 150 lines". The P8b UNVERIFIED is closed: `P8b.md:78` says docs only. |
| C-F3 | PROPOSE FIX | `Limits` construction written out. `blocked(agent_id) -> list[str]` as on main. The `P2a.md:87` contradiction is reported (PENDING LEAD 6). |
| C-F4 | PROPOSE FIX | A fresh store, channel and fake per kind. `OverBudget.which == "day"`. New C3b row and MP15. |
| C-F5 | PROPOSE FIX | Cite changed to `P4b1.md:96-100`. `Meter.settle(hold.reservation_id, ...)` is called directly; the `Hold` is not entered as a context manager. |
| C-F6 | PROPOSE FIX | C tests require the exact line `kind=<k> runs=0 result=FAIL`. E tests also require `error=<Class>`, which the output format now has. |
| C-F7 | PROPOSE FIX | MP8 becomes MP9 in rev 2, with killer G1. |
| C-F8 | PROPOSE FIX | The runner call is spelled out: `extra_dirs=("tests/fixtures","tools")`, `only_test` and `expect` for each mutant, D1 never a killer. Data comes from `tmp_path`, so `demo_only/` is not copied. |
| C-F9 | PROPOSE FIX | Tests build data in `tmp_path` (`make_data`). Only the manual command and the evidence read `demo_only/proof_pack`. |
| C-F10 | PROPOSE FIX | `Redactor.mask` (bound to the regex-kind instance). The wrapper's class name comes from merged P5c-2. |
| C-F11 | PROPOSE FIX | `allow_equal(...) is AllowVerdict.LOOKALIKE`, never truthiness. identity_key cite is `P1.md:44`; `fold_key` is the same object. |
| C-F13 | PROPOSE FIX | The re-read rule now covers every `file:line` in the ticket. |
| C-F14 | PROPOSE FIX | `uv run --group scan bandit -ll ...`. I also added `tools/scan_repo.py` to the evidence. |
| C-F17 | PROPOSE FIX (Nit) | `--data` is relative to the repo root, found as `Path(__file__).resolve().parents[1]`. |
| C-F18 | DECLINE (Nit) | The reviewer said "None" (the cite is fine). No change. |
| C-F19 | PROPOSE FIX (Nit) | The fail-before for Z1-Z7 is the mutant run (MP1a-g). |

Tally:
- **32 finding ids:** 31 PROPOSE FIX, 1 DECLINE (C-F18), 0 CONTEST, 0 ESCALATE.
- **25 table rows:** five rows hold more than one id (D-F2+C-F12, D-F8+C-F1+C-F2, D-F9+C-F16, D-F10+C-F15).

## Positions
- **D-F3:** I accept option a. The plan's section 9 command is the plain run. A Postgres path adds a secrets lookup, a connection and an allowlist branch, and no test covers them. P4d's contract suite already owns Postgres behaviour.
- **D-F4, runner verdict:** it stays KEEP-CODE. It is an eval gate, which is on the R448 guarantee list. The higher rung (pytest plus a hook) covers less than 80 percent, for the three checkable reasons in the table. The runner is about 40 lines inside the one file.
- **C-F1:** as described in the Honest note, the pack carries no environment literal. This fits rule 21: core tests the stage, and the pack never tests a name.
- **D-F10:** test volume went up a little (30 rows to 33, 18 mutants to 22), against the reviewer's wish to trim. Each added row answers a Major (S2, C3b, H4). I cut nothing that has a unique killer.

## Couplings
- **P0t:** the name of the fake-allowed environment (`dev` -> `demo`). The data file holds the value, and the script holds none.
- **P2a-1:** the shape of `blocked` (PENDING LEAD 6).
- **P4c-1 and P4c-2:** the wall_alert entry point and its exact count.
- **P5c-1 and P5c-2:** how a `MaskSession` is opened, the wrapper's class name, and whether placeholders are deterministic (PENDING LEAD 8).
- **P8b:** no file shared (`P8b.md:78`).
- **Merge order is unchanged:** after P8a, in parallel with P8b.

## PENDING LEAD (continues the ticket's numbering; none blocks the build)
5. Cut `--store postgres`; v1.1 row V1. Recommendation: accept.
6. Frozen P2a contradiction: `P2a.md:87` writes `blocked()` with no argument, but core's `blocked(agent_id) -> list[str]` (`limits.py:20-30`) also reads the budget. Recommendation: core's shape stands; a build note goes on P2a.
7. `TICKET-TEMPLATE.md` still shows the old 1-7 rung scale, while order 67 set 0-5. Recommendation: the lead updates the template line.
8. Placeholder determinism in P5c decides whether a pre-made recording matches. Recommendation: the builder checks this first and reports it; the pack is not changed to hide it.
- Items 1, 3 and 4 still stand (4 is widened to name the P5c-2 wrapper class and the P4c-2 alerter). Item 2 is withdrawn.

## Counts
- **Ticket:** 97 -> 116 lines.
- **Test rows:** 30 -> 33 (+S2, +C3b, +H4).
- **Mutants:** rev 1 said 12 ids, which were really 18 mutants. Rev 2 has 22 (MP1a-g are 7, MP2-MP15 with MP7a/b are 15).
- **Allowlist table:** 7 rows.
- **Rung table:** 6 rows.
- **PENDING LEAD:** 8 items (1, 3, 4 stand; 2 withdrawn; 5-8 new).
- **v1.1 rows:** 1.
- **Findings:** 32 ids: 31 PROPOSE FIX, 1 DECLINE, 0 CONTEST, 0 ESCALATE.
