# P8b round 2, correctness review (ticket revision 2)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

TICKET REVIEW round 2, CORRECTNESS, P8b revision 2. Reviewer: egm-codebase-details, read-only. Nothing under handover/reviews/ or handover/evidence/ was read.

VERDICT: no Blocker. One Major, several Minors and Nits. Every code cite I could check is correct on the current checkout. I have no git access, so the commit cites (601be32, 397ec97) are UNVERIFIED. The current checkout may differ from them. I can only say the cited lines match today's files. The ledger already differs from the ticket's figures (see Verified).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | Evidence step 1; step 5 (T1/T5/T6 "at the step 1 commit"); step 7 (T2) | Every evidence file's first line is `git rev-parse origin/main`. But the pages exist only on the docs PR branch, not on origin/main. `handover/ledger.md` lives on branch `core/cloud-handover`, not on origin/main either. So the recorded sha does not identify the pages or the ledger the checks read. The ledger and `main` also move while the pages are written (step 3). A T2 pass cannot be tied to the "one step 1 commit" that Done item 2 requires. T5 runs `git ls-files` "on the step 1 commit" but the pages are not there. | Record two shas per file: the docs PR head (`git rev-parse HEAD`) and the ledger branch head. State that T1/T5/T6 run on the PR head rebased on origin/main. Re-run step 1 after step 3. |
| R2-COR-2 | Minor | Interface item 3 (Backends, "dev only"); Interface item 2 bullet on the client profile | The ticket says the refusal in the client profile is named only if P6a is merged. The refusal already exists on main. `config.py:365-373` refuses every `DEV_ONLY` pair when `environment != "dev"`. `NOT_PROD` is refused only when `environment == "prod"` (`config.py:391-392`). A6 says "dev_only mechanism already exists". Pages written to this ticket would leave out true current behaviour. They also would not say that pilot refuses dev-only but allows not-for-production kinds. | Say the pages cite `config.py:366-373` and `config.py:391-392` now. Keep the P6a condition only for any extra refusal P6a adds. |
| R2-COR-3 | Minor | Files field, "Change" bullet; Interface item 3; Done item 2 | The ticket treats the root README edit as conditional ("only if T6 fails"). On this checkout the README paragraph (`README.md:31`, starts "Redaction is pattern-based and bounded") contains none of the three `phrases.txt` phrases. I grepped `only plain copies`, `8 to 11 characters` and `hex and base64`: 0 matches. T6 will fail on the first run. | List `README.md` under Change as certain. Keep the T6 re-run as the pass criterion. |
| R2-COR-4 | Minor | Interface item 4 "Two items are flagged in advance"; Evidence step 5 (T5) | The block lists 17 paths. Only `tests/test_redact*.py` is flagged as missing. On this checkout most of the others also match nothing: `test_textnorm_differential`, `test_stop_state*`, `test_migration_numbers`, `test_usage*`, `test_meter*` (a `tests/demo_askdata/test_meter.py` exists but does not match), `test_run_cap`, `test_training_lock`, `test_secrets_import`, `test_env_lint`, `test_kind_identity`, `test_c1_acceptance`, `test_diagnostics_hostile`, `test_client_profile`. `tools/proof_pack.py` is also absent. They are created by other packages, so this is expected before P8b. The text reads as if only one path is wrong. | Reword: "all paths other than `tests/contracts/` and `tests/warden_port/` are created by other packages. Only a path still missing after P8a counts." Keep `test_redact*.py` as the known mismatch. |
| R2-COR-5 | Minor | Evidence step 1 ("every later file's first line must equal it") vs. step 5 | Contradiction. `table-keys.txt` is explicitly kept as one name per line (sha and rc go to `table-keys.log`). `extra-kinds.txt`, `phrases.txt` and `section9-list.txt` are literal blocks. `roles.txt` is read by the T6 `sh` loop with `read kind be labels`. If `roles.txt` follows the universal `{ git rev-parse...; cmd; echo rc; } > file` form, its first line (a sha) and the `rc=` line become bogus rows, and T6 fails with `NO-ROW`. The ticket does not say how `roles.txt` is written. | List which files are pure data (no sha/rc lines) and give each a `.log` twin, as is done for table-keys. Name `roles.txt` explicitly. |
| R2-COR-6 | Minor | Interface item 2 (Single dependency bullets) vs. headings 4 and 8 | The channel and executor outlines are said to be written in heading 8 ("What it does not do"). The outline-with-trigger belongs under heading 4 ("Single dependency: ... or the outline with its trigger"). The pages and the T-checks may disagree about where it goes. | Say once: the outline is under heading 4. Heading 8 repeats only the v1.1 row. |
| R2-COR-7 | Minor | Tests, T6 (four things) | T6 never checks the positive side of "production choice". Pages that omit the label, or that put it on a row with no labels such as `detector regex`, pass. The rule "production choice = neither dev only nor not for production" is not tested either. Plant P19 covers only the `config default` label. | Add a T6 check: a row whose code labels contain neither `dev only` nor `not for production` must contain `production choice`. Add one planted fault for it. Update the counts (22 → 23, T6 3 → 4). |
| R2-COR-8 | Minor | Problem; Target module ("textnorm, usage and meter are single modules inside shared folders") | Written as current fact. No `textnorm`, `usage`, `meter`, `stop_state` or `diagnostic` module exists under `src/hadavin_sdk` on this checkout. They arrive with P1, P4a, P4b, P2a and P5a. The same applies to "`defaults.py`" being untouched. | Say "after the owning packages merge", or UNVERIFIED until P8a. |
| R2-COR-9 | Minor | "Source" paragraph; Files field | The Security note says the CI secret-and-name scan "must stay green", but the T6 phrase block and the pages quote code names. No check of the new pages for real-looking tokens is run before the PR (the scan runs only in CI). | Optional. Add one `grep` for key-like strings over `docs/kinds/` to T6, or accept CI as the only gate. |
| R2-COR-10 | Nit | Interface item 4, "`plan-v3.md:173-188`" | The test-path block is lines 174-188. Line 173 is the "Every v1 code row merged" row. | Cite 174-188. |
| R2-COR-11 | Nit | Interface item 3, `table.py:593-601` | `DEV_ONLY` closes at line 602 (`)`). | Cite 593-602. |
| R2-COR-12 | Nit | Words, "Unresolved" vs. awk | The definition lets WAIVED, OWNER-ONLY and IMPOSSIBLE-NOW pass. The awk also demands a non-empty artifact cell (`BAD-NO-ARTIFACT`). That is stricter than the definition. | Add "with a named artifact" to the definition. |
| R2-COR-13 | Nit | Evidence, T2 "Pass: rc=0" | `FIXED-VERIFIED` rows are never checked for an artifact, although `blocker-ledger-rule.md` demands one. | Optional: note it as a gap. |

Recount results (all match the ticket):
- 15 pages plus the index (16 files): 8 table keys (`secrets`, `signer`, `anchor`, `store`, `audit`, `llm`, `detector`, `channel`) plus 7 other parts (`diagnostic`, `executor`, `meter`, `redactor`, `stop_state`, `textnorm`, `usage`). The 7 match the 7 non-table kinds of `plan-v3.md:75-84`.
- 31 table entries: 7 secrets, 6 signer, 4 anchor, 2 store, 2 audit, 5 llm, 3 detector, 2 channel. `grep -c "Entry("` also gives 31.
- 23 entries marked `_UNVERIFIED`: 6+5+3+1+1+4+2+1 = 23. The 8 unmarked are secrets `fake`, signer `none`, anchor `none`, store `memory`, audit `local_dir`, llm `fake`, detector `regex`, channel `fake`.
- 10 entries with `neutral=True`, and 6 config defaults (`DEFAULTS` at `table.py:582-589`), both as the ticket says.
- 22 planted faults: T2 15 (P1-P8, P12-P16, P21, P22), T1 2 (P9, P17), T6 3 (P10, P18, P19), T5 1 (P11), T3 1 (P20). Total 22. P7 and P8 are the controls.
- I traced the expected output of every ledger fault (P1-P8, P12-P16, P21, P22) through the awk text by hand. All match: `NF` is 9 for a 7-cell row, the id regex, severity, status first word, waiver artifact, duplicate and header rules. I did not run the awk, so mawk-vs-gawk behaviour is UNVERIFIED.

Verified against source on the current checkout:
- `table.py`:
  - `TABLE` at :386, and the keys at :387, :427, :467, :492, :502, :512, :543, :558.
  - `Entry.neutral` at :342-344; `_UNVERIFIED` at :380.
  - detector `regex` at :544 (no status) and `llm_judge` at :546-548 (`_UNVERIFIED`); :546-556 covers `llm_judge` and `bedrock_guardrail`.
  - `DEFAULTS` at :582-589 with exactly the six defaults; `audit` and `llm` have none. Comment at :591; `DEV_ONLY` at :593 (six pairs); `NOT_PROD` at :604 (`signer none`, `anchor none`).
  - Five of the six defaults are dev only or not for production; only `detector regex` is neither.
- `config.py`:
  - `Backends` at :62-72, with the same eight fields. `llm` is required at :70, so there is no default. `detector: tuple[KindSettings, ...]` at :71.
  - Environment refusal at :365-373 and :391-392 (see R2-COR-2).
- Guard and backend cites:
  - `guard/__init__.py:3` imports `redact` only; `redact_many` is not exported.
  - `guard/redact.py:862` (`redact`) and `:1244` (`redact_many`).
  - `guard/injection.py:19` (`Detector`) and `:38` (`RegexDetector`).
  - `backends/builtin.py:43` (`regex_detector`).
  - `actions/executor.py:47` (`Executor`); `actions/contract.py:15, 22, 33` (`NoneExecutor`, `ManualExecutor`, `HttpExecutor`).
  - `tools._secret_forms` exists at `tools.py:744`.
- `pyproject.toml:57-58` uses `uv_build`. No `README.md` exists under `src/`. `docs/` holds exactly `slack-app.md` and `slack-app-manifest.yaml`.
- `LEAD-ORDERS.md` lines:
  - :19 order 6(b)/(c) (P8b is Tier B).
  - :21 order 8(5); :38 order 14; :44 order 15; :67 order 19 C (PL46(a)).
  - :78 order 20 item 4 (merge chain as quoted); :79 item 5.
- `amendments.md:9` is A6 (llm four backends, no default; channel Slack only; executor not a table kind). A7 and A9 F9 give the `core_sync_check.py` command.
- `plan-v3.md`: :26 ledger paths; :54 cloud ledger copy; :75-84 section 5; :80 diagnostic; :112 P8a; :113 P8b; :185 "No unresolved findings"; :190 the P8b duty; :193 tagging by the lead. `plan-v2.md:117` has the "rollback tags" item.
- `P1.md:20` contains both quoted coverage phrases ("copies of secrets of 8 to 11 characters, which are common passwords, reach the model" and "only the tool-output scrubber removes the exact hex and base64 spellings ..."). `P8a.md:78` is item 8, "Plan text".
- Test paths: `tests/test_redact*.py` matches no file (only `tests/warden_port/test_redaction*.py` exist, which do not match the pathspec). `tests/warden_port/` and `tests/contracts/` exist.
- Ledger on this checkout:
  - 1623 table lines = 1621 rows, which matches the ticket's `rows=1621`.
  - 727 unresolved BLOCKER/MAJOR rows among 7-cell rows, matching.
  - The 5-cell count by my regex is 183 against the ticket's 178 (the ledger grows; my regex may overlap, so treat this as drift to re-read, not an error).
  - 5-cell layout is `id | severity | package | summary | status`, as PENDING LEAD 6 says.
  - Zero ledger rows contain `\|`, and every id starts with letters/digits and hyphens, so the awk id rule does not mis-flag ids.
- Template field order: all 17 template fields are present in order. The CHANGELOG and header times are consistent (03:00 UTC = 08:30 IST; 02:45 UTC = 08:15 IST).

Not checked (UNVERIFIED):
- All shas: `601be32`, `397ec97`, `0d04aa3`, `db09637`. No git access.
- The "24 decision rows: 23 PROPOSE FIX, 1 CONTEST" claim, because the resolve file is off-limits to me.
- `ledger_check.py` and `ledger_lint.py` behaviour, and the P0d waiver format.
- `inventory-A.md:10`. My grep for 9-column/7-column wording found nothing in `inventory-A.md` under `studio-notes`. The file may be elsewhere.
- `P1 V12` and the P2d ticket's replacement test name.
- The `egm:egm-drift-report` output and its file name.
- Running the awk, the T6 `sh` text or the Python one-liners. The ticket's figures "31 lines / 6 defaults / 23 / 10" were recounted by hand from source and match.
- Whether the 16 pages stay within the 60-line cap, which depends on the page text.
- gawk and busybox behaviour of the awk.

Files read: `handover/tickets/P8b.md`, `handover/LEAD-ORDERS.md`, `handover/studio-notes/amendments.md`, `handover/TICKET-TEMPLATE.md`, `handover/studio-notes/plan-v3.md`, `handover/ledger.md`, and the source files cited above under `src/hadavin_sdk`.