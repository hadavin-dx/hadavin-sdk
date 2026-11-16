# P2a round 1: disposition of the 34 findings (applies `P2a-round1-resolve-report.md` to `handover/tickets/P2a.md`, revision 3)

Written 2026-11-05 (UTC) by the ticket author (Sonnet 5.5). Counts: FIXED 31, REJECTED 0, ESCALATED 3. Each finding's cited line was re-read in the snapshots (`pr50-748849c`, `pr50-2e8a28c`) or core `ce70eb5` before the ticket was edited. "Section" = the ticket field that now carries the answer.

| id | severity | disposition | section | one line |
|---|---|---|---|---|
| A1 | BLOCKER | FIXED | Interface "Who may do what"; Security | Name list called a typo guard; real enforcement is a database trigger plus reset role (gating item); negative tests are direct store writes with the runtime credential; residual risk stated. Exact SQL UNVERIFIED, lead item 3. |
| A2 | BLOCKER | FIXED | Interface "Who may do what"; Rollback | Stop is open to everyone and audited; `stop_identities` deleted; empty `reset_names` bootstrap and dormant breakglass role defined. |
| A3 | BLOCKER | FIXED | Interface `Limits.reset`, Masking | Raw name checked first, label masked once in `Limits._event` and `KillSwitch.by`; list holds raw logins. |
| A4 | MAJOR | FIXED | Interface Masking; Tests fail-before (3),(4) | Masking moved to the choke point; CLI path and table column tested. |
| A5 | MAJOR | FIXED | Interface "Label key" | Fallback refused outside dev via `Config.environment` (`config.py:317, 365-373`), `key_id` in the label, old-key retention stated. |
| A6 | MAJOR | FIXED | Interface `Limits.reset`, CLI | `expect` is required; CLI `status` shows and `reset` requires the token; mutant row added. |
| A7 | MAJOR | FIXED | Interface "Compare-and-set never degrades" | `Limits.stop` returns the record; no token means `release` refuses; constructor requires the new methods; "written vs not written" split. Verified `stop_gate.py:336-338, 385-388`. |
| A8 | MAJOR | FIXED | Interface "Release re-stop window" | One conditional store write, `_gen` checked right before it; no second stop write; test (f). Verified `stop_gate.py:394-411`. |
| A9 | MAJOR | ESCALATED | Open point 1; Tests end to end | Owner not decidable here; recommended P4c (edits `agent_loop.py`); gate labelled "unwired" until named; end-to-end loop test added to P2a-1. |
| A10 | MAJOR | FIXED | Tests race and process | Store-level interleaving hook, deterministic; 8 distinct audit rows and consistent pair; CI must fail without Postgres. |
| A11 | MAJOR | FIXED | Interface "Barrier scope" | Documented as per process; `complete` defined; `cache_ttl` capped; cross-process test documents the limit. Cross-process waiting not built (needs a store lease). |
| A12 | MAJOR | ESCALATED | Open point 4; Files P2a-2, P2a-3 | Plan row names three PRs; recommended to keep, stated as no core caller, wiring claim removed; lead may move them to the first consumer. |
| A13 | MAJOR | FIXED | Files; Done | P2a-2 first and owns runner, judge, `testing/`, mutants file, contracts; P2a-1 and P2a-3 only append rows. |
| A14 | MAJOR | ESCALATED | Depends on; Open point 2 | F6 lists P2a only for `limits.py`; recommended extension (config, cli, app, agent_loop, store, migrate; after P3a and P4d). Cross-checked against A11/A13: money SQL is in P4d, so P4b1 no longer edits the store files. |
| A15 | MAJOR | FIXED | Interface Config; Rollback | Verified `extra="forbid"` at `config.py:52, 316`; fail-before test at core; first-deploy bootstrap defined. |
| A16 | MAJOR | FIXED | Interface "Fail closed" | Checked `agent_loop.py:190-480`: no handler around lines 359, 421, 460; `_limits_stop` change and test added; tick.py handling UNVERIFIED. |
| A17 | MAJOR | FIXED | Files P2a-2 | Runner is under `tools/`, not in the wheel. Premise partly wrong: the runner already works on a temp copy (`mutation_runner.py:194-212`) and the judge only reads output; added a git-status-clean check. |
| A18 | MINOR | FIXED | Interface CLI | `status` prints "N earlier stops are in the audit". |
| A19 | MINOR | FIXED | Neutral default | `StopBackend` protocol named, contract suite runs on it, dated review 2027-01-31. |
| A20 | MINOR | FIXED | Tests hostile inputs | Column is TIMESTAMPTZ (`0001_core.sql:94-100`); round-trip test added; server-side counter needs a migration and is not built. |
| A21 | MINOR | FIXED | Mutation plan "failing test" | Step 0 moved to the evidence runner, who names the test. |
| A22 | MINOR | FIXED | Interface | "Allowed names" wording; `complete` defined in one sentence; "audited reset" defined once. |
| C1 | BLOCKER | FIXED | Interface (all of "Who may do what", `Limits(...)`, CLI) | Same as A1-A3; `Limits` constructor takes the list; `app.py:171` and `cli.py:209` in the change list. |
| C2 | MAJOR | FIXED | Interface Masking | Every principal hashed (not only `@` removed); CLI and table covered; lead may relax (item 6). |
| C3 | MAJOR | FIXED | Depends on | "Lead decision" wording removed; orders named on `config.py`, store files, `conftest.py`; new method gets rows in `tests/contracts/test_store.py` after P4d-a; P4d split into three PRs (A13) reflected. |
| C4 | MAJOR | FIXED | Files; Done | P2a-2 first with `testing/__init__.py`, judge, runner, mutants file, contracts. |
| C5 | MAJOR | FIXED | Interface "Compare-and-set never degrades" | `restore(True)` records the token; a missing token refuses; tests per path. |
| C6 | MAJOR | FIXED | Mutation plan | Recounted by importing the runner's list (not running it): 262 rows total, 103 for P2a (gate 48, rows 20, view 14, runner 21); killer files per sub-PR listed; 5 rows unresolved by name. Reviewer's 190 literal rows was an undercount. |
| C7 | MAJOR | FIXED | Files | The five existing tests, `app.py`, `conftest.py`, `test_store.py`, new contract kind listed with order against P4d. |
| C8 | MINOR | FIXED | Mutation plan "weak row" | Mechanism corrected (WRONG_REASON, whole list runs, `mutation.py:61-62`); snippet fixed to match the three-line constant; new test for the unbounded guard. Verified at both heads (`rowstore.py:73-75` pushed; `:134-138` local; `test_promoted_controls.py:1791`, `:491`). |
| C9 | MINOR | FIXED | Interface Errors; CLI | `StopNotPermitted` and `SwitchChanged` derive from `RuntimeError` (`store/protocol.py:33-38` treats `OSError` as unreachable); `cli.py` reason reworded. |
| C10 | MINOR | FIXED | Files P2a-3 | Claim of a `ConfigHolder` link removed; module ships without a core caller; reset list changes on restart; the `contracts.py` import claim removed. |
| C11 | MINOR | FIXED | Interface "Label key" | Uses the existing `Config.environment` field; `agent_loop._restored_digest` (`agent_loop.py:256-267`) cited as the keyed-hash precedent. |
| C12 | MINOR | FIXED | Source; Interface | `limits.py:43-51`; killswitch is 21 source files (counted by `find`); engage `timeout: float \| None` added; Problem section is 5 sentences; I dropped the `ledger.md` line count (it is now 142 lines and changes). |

## ESCALATED (also to be listed in `handover/questions-for-lead.md` by the lead)
1. A9 wiring owner: recommend P4c (it edits `agent_loop.py`); until named the gate is "unwired" in CHANGELOG and ledger.
2. A14 hot-file extension (F6) and Depends-on additions P3a and P4d for P2a-1: recommend extend; one PR in two commits.
3. A12 whether P2a-2 and P2a-3 stay in v1: recommend keep (plan row, apexc copies), with no claim of a core caller.

Related items I flagged as PENDING LEAD in the ticket although they are not separate findings: database reset guard deviates from "read-only runtime" (trigger instead; runtime keeps UPDATE); hash every principal; evidence file name; runner overlap with P2c.
