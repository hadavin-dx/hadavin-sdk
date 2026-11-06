# Package ticket P8b: one README per kind, the drift report and the ledger check. DRAFT revision 1

Revision 1 written 2026-11-06 about 02:45 UTC (08:15 IST) by a Sonnet 5.5 ticket author (lead order 20 item 6, `LEAD-ORDERS.md:80`). Text only: no code, no suite run, no pull request. Code cites were read on `origin/main` with `git show origin/main:<path>` (the worktree's `src/` differs from `origin/main` in `guard/http.py`, `guard/runmap.py` and `tools.py`, so the worktree was not used for cites). Ledger facts were read on `handover/ledger.md` as of commit `124258b` (1,474 lines). Anything not read is marked UNVERIFIED. "PENDING LEAD" means the author proposes it and no lead decision exists yet. Tier B: one fresh reviewer, one round, at most 2 fix batches (order 6(b), `LEAD-ORDERS.md:19`). Per order 6(c), the lead runs everything in this ticket; this text gives the commands, the pass criteria and the evidence files.

## Words used in this ticket
- **kind**: one replaceable part of the core behind a fixed interface, with a default and an alternative (or a written outline with the event that would make us build it, called its **trigger**). Example: the `store` kind, whose default is Postgres.
- **kind README**: one short plain-word page per kind, saying what the kind does, which backends exist, which one is the default and what it does not do.
- **drift**: a sentence in a document that no longer matches the code (for example, a README that names a default the code does not use). **Drift report**: the output of the `egm:egm-drift-report` skill.
- **ledger**: the table of review findings, `handover/ledger.md` in the cloud and `egm/BLOCKER-LEDGER.md` on the laptop (plan-v3 line 26). **Unresolved**: a BLOCKER or MAJOR row whose status is anything except FIXED-VERIFIED, WAIVED, OWNER-ONLY or IMPOSSIBLE-NOW.
- **planted fault**: a deliberate error put into a throwaway copy of an input to prove a check catches it. Here it plays the part a code mutant plays in a code package.

## Template fields in the template's order

- **Package id and name:** P8b, "One README per kind, the drift report and the ledger check" (plan-v3 row, `studio-notes/plan-v3.md:113`). One docs pull request to core (the READMEs) plus two checks the lead runs. Step S5, milestone v1, consumers: none.
- **Path class:** other. **Extended review (no round cap): no.** Not a money, redaction or security path: P8b adds no code. Only the redactor README describes a redaction path; its wording follows orders 14 and 15 (field "Interface", item 3).
- **Depends on (merged first):** P8a (plan-v3 row, `plan-v3.md:113`). P8a depends on every v1 row except P8a, P8b and P8c (`plan-v3.md:112`), so P8b starts only after every v1 code row is merged and the demos are re-pinned. **The P8a ticket is not written yet** (`ls tickets/` has no `P8a.md`), so this ticket depends on "P8a, ticket revision not yet written". The P0d tool changes are a hard dependency of the laptop check (field "Evidence commands", step 3). P8b is not in the code merge chain of order 20 item 4 (`LEAD-ORDERS.md:78`: P1m, P1a, P1b, P3a and P4d chain, P2a-1, P2d-1, P2d-2, P4a). It merges after all of those and after P8a, in either order with P8c. The two share no file: P8c writes `tools/proof_pack.py` and P8b writes `docs/kinds/`. `defaults.py` (order 20 item 5, `LEAD-ORDERS.md:79`): P8b adds no constants and does not touch the file.
- **Problem in plain words:** The core has eight kinds in its backend table and seven more parts that plan-v3 section 5 calls kinds, but no page says, for each one, what it does, which backends exist and what it does not do. There is no `README.md` anywhere under `src/hadavin_sdk/` (`find src/hadavin_sdk -name README.md` prints nothing). Two of plan-v3's own claims about kinds were already found wrong in code (memo 6: "llm defaults to Anthropic" is false, and "channel has one or two backends" is really one), so README text written from the plan instead of the code would be wrong on day one. Separately, "v1 is done" needs proof that no BLOCKER or MAJOR finding is left unresolved. Today the cloud ledger cannot even be checked reliably: 25 of its 1,468 rows use a different column layout (field "Evidence commands", step 2), and 727 BLOCKER or MAJOR rows are unresolved.
- **Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:** No code. The READMEs are written from the code at the P8a merge commit (written into the evidence file). The sources, in order of authority: (1) code; (2) `studio-notes/memos/memo-6-kernel-and-claims.md` section B (the claim checks); (3) each package's frozen ticket; (4) plan-v3 section 5. Where these disagree, the code wins and the disagreement is a drift item. Not taken: plan-v2's "rollback tags" item for P8b (`plan-v2.md:117`). Plan-v3 section 10 gives tagging to the lead before each merge (`plan-v3.md:193`).
- **Target module and path in `src/hadavin_sdk/`:** none. The READMEs go to `docs/kinds/<kind>.md`, plus an index `docs/kinds/README.md` (PENDING LEAD item 1). Reasons not to put them under `src/`: textnorm, usage and meter are single modules inside shared folders, so "README in the kind's folder" has no single meaning. The build backend is `uv_build` (`pyproject.toml:57-58`), and whether it would ship a non-Python file inside the package is UNVERIFIED.
- **Interface (names, argument and return types, errors):**
  1. **The kind set: 15 READMEs** (PENDING LEAD item 2). (a) Every capability key of `TABLE` in `backends/table.py` (`:386`): `secrets` (`:387`), `signer` (`:427`), `anchor` (`:467`), `store` (`:492`), `audit` (`:502`), `llm` (`:512`), `detector` (`:543`), `channel` (`:558`). These are the same eight fields as `Backends` in `config.py:62-72`. (b) Plus the plan-v3 section 5 rows that are not table keys (`plan-v3.md:75-84`): `textnorm`, `stop_state`, `usage`, `meter`, `diagnostic`, `redactor`, `executor`. Each page's first line says plainly which pages are not kinds in the code. `diagnostic` "is a rendering rule, not a kind" (P5a ticket and plan-v3 line 80). `executor` "is not a kind in the table" (memo 6 section B): it is `class Executor` (`actions/executor.py:47`), chosen per action contract through `NoneExecutor`, `ManualExecutor` and `HttpExecutor` (`actions/contract.py:15, 22, 33`). Whether `redactor` (pattern-based `guard.redact`) and the `detector` capability are the same thing is UNVERIFIED. If they are, the two pages link to each other and neither repeats the other.
  2. **Fixed headings of every kind README** (one screen at most, plain words, no model ids, no prices, no real-looking values):
     1. What it does: 2 to 4 sentences.
     2. Interface: the protocol or class name with `file:line`.
     3. Backends: a table of name, role and module. The role is default, alternative, dev only (from `DEV_ONLY`, `table.py:593-601`) or not for production (from `NOT_PROD`, `table.py:604`). Each backend also carries "not yet run live" when its entry has `status=_UNVERIFIED` (`table.py:380`).
     4. Single dependency: the default, then the alternative or the outline with its trigger. Memo 6's corrections apply: llm has no default and config must name one. The secrets default `fake` and the `env` backend are dev only, so production uses `mounted_file` or `vault`. Channel has one real backend (Slack), and its missing outline is PENDING LEAD item 3.
     5. Identity and rights: as declared by P6b, or "none declared".
     6. Configuration keys: from `config.py`.
     7. Tests that cover it: the test file paths, for example `tests/contracts/` for store.
     8. What it does not do: plain facts, each with its v1.1 row and trigger, never "known limitation".
  3. **Redactor wording (orders 14 and 15).** These sentences are copied in meaning, and the drift report checks them against the P1, P2d and P5c tickets as merged:
     - For secrets of 8 to 11 characters, the redactor catches "only plain copies". The case-folded sweep is v1.1 row LKV-2, trigger "before any pilot with real client data" (order 15, `LEAD-ORDERS.md:44`).
     - A known value hidden in invisible characters, base64 or hex is not caught in v1, EXCEPT exact hex and base64 copies of a secret handed to a tool, which `tools.py` scrubs (order 14(1) as narrowed by the PL46(a) answer, `LEAD-ORDERS.md:38, 67`). The README uses the final wording of the merged P1 ticket, not this paraphrase.
     - The root `README.md` redaction paragraph (line 31 on `origin/main`) is in the drift scope and must agree with the page.
  4. **Section 9 test-file table.** Plan-v3 line 190 gives P8b one more duty: "if a package names its test file differently, P8b updates this table". P8b checks every test path named in section 9 against `main` (Evidence step 4) and sends the corrected rows to the lead, who edits `plan-v3.md`.
- **Neutral default / working alternative (or written outline with trigger):** not applicable. P8b adds no dependency. Single-dependency audit: each README states its kind's default and alternative, and any kind with neither gets a drift item that the lead must answer before "done". Known case: channel has no second backend and no outline in the repo (memo 6). The proposed outline is "email-link approval channel; trigger: a client without Slack", which is memo 6's wording and is not found in the repo (PENDING LEAD item 3).
- **Files to create, change, delete (each with the reason):** create `docs/kinds/README.md` (the index: one line per kind with a link) and the 15 pages `docs/kinds/{secrets,signer,anchor,store,audit,llm,detector,channel,textnorm,stop_state,usage,meter,diagnostic,redactor,executor}.md`. Change `CHANGELOG.md` with one append-only line ("docs: one page per kind"). Change nothing in `src/` or `tests/`, delete nothing, and add no new tool or CI job (cut surface, order 8; a CI check that the README set matches `TABLE` is a v1.1 row, trigger: a kind added after v1 without its page). Evidence files: `handover/evidence/P8b/ledger-check-cloud.txt`, `ledger-check.txt` (laptop), `drift.md`, `readme-set.txt`, `section9-paths.txt`, `planted-faults.txt`.
- **Existing core code reused (checked):** `backends/table.py` (`TABLE`, `DEV_ONLY`, `NOT_PROD`, `_UNVERIFIED`) and `config.py` `Backends` are the source of each backend table. They were read, not changed. Memo 6 section B is the claims check. Hashing, k1b/atomic, k1b/redaction, stats, evals and store/memory are not relevant: no code is written.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):** docs only, with no identity, no rights and no secret. The public-repo rule (order 20 item 4, `LEAD-ORDERS.md:78`; order 8(5), `LEAD-ORDERS.md:21`) applies: no owner names, no studio paths, no real-looking key or token, even as an example; placeholders such as `<KEY>`. The CI secret-and-name scan must stay green on the docs PR. The pages must not print dev-only backends as production options: every `DEV_ONLY` pair is labelled "dev only, refused in the client profile".
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** no unit tests (no code). The checks below are the tests. Each has a planted-fault row, and the planted faults are run before the real check, so a check that cannot fail is caught first.
  - **T1, README set:** the 15 file names in `docs/kinds/` equal the kind set of Interface item 1, and every `TABLE` key appears (Evidence step 5).
  - **T2, ledger check (cloud):** exit 0 on `handover/ledger.md` (Evidence step 2). **Fail-before:** on today's ledger (`124258b`) it exits 1 with `rows=1468 bad_layout=25 unresolved_blocker_major=727`, split as OPEN 585 and FIXED-UNVERIFIED 142. The author ran this read-only in scratch; it is not evidence, and the runner re-runs it.
  - **T3, ledger check (laptop):** `ledger_check.py` and `ledger_lint.py` both exit 0 (Evidence step 3).
  - **T4, drift report:** no open drift (Evidence step 6).
  - **T5, section 9 paths:** every named test path exists on `main` (Evidence step 4).
  - Hostile inputs, races and contract suite: not applicable (no code).
- **Mutation plan: which behaviours get a mutant, which test kills each.** These are planted faults, each in a throwaway copy, never in the real ledger or the real docs. P1 through P8 are a valid header and one FIXED-VERIFIED MAJOR row, plus the one row named below. **The author ran P1 to P8 on scratch copies and got the expected exit codes; this is not evidence, and the runner re-runs them.**

  | Fault | Planted row or change | Killed by | Expected |
  |---|---|---|---|
  | P1 | a 5-column row `\| BS-PX-1 \| Major \| PX \| s \| OPEN \|` | T2 layout rule | exit 1, `BAD-LAYOUT` |
  | P2 | BLOCKER with status OPEN | T2 | exit 1 |
  | P3 | lower-case `major` with status FIXED-UNVERIFIED | T2 (case fold of severity) | exit 1 |
  | P4 | unknown status `DONE` | T2 (fail closed) | exit 1 |
  | P5 | severity `Major/Minor` | T2 severity rule | exit 1, `BAD-SEVERITY` |
  | P6 | status `OPEN (build notes)` (words after the status) | T2 (first word only) | exit 1 |
  | P7, control | MINOR with status OPEN | T2 | exit 0 |
  | P8, control | MAJOR with status WAIVED | T2 | exit 0, and the row id printed as `WAIVED <id>` |
  | P9 | delete `docs/kinds/channel.md` in a scratch copy | T1 | the missing name printed, exit 1 |
  | P10 | in a scratch copy, `secrets.md` names `env` as the production default | T4 | the drift report lists it (`DEV_ONLY` has `("secrets","env")`, `table.py:597-598`) |
  | P11 | add a non-existent path to a copy of the section 9 list | T5 | the path printed as missing |
- **Evidence commands (exact), and where the raw output is saved** (all under `handover/evidence/P8b/`; every command's own exit code is recorded, never a pipe's):
  1. Merge commit: `git rev-parse origin/main`, written as the first line of every evidence file.
  2. **Cloud ledger check** (the command named for `handover/ledger.md`; read-only awk, kept in this ticket, not added to the repo). **First the lead normalises the 25 `BS-*` rows** (`ledger.md:1450-1474`; layout `id | severity | package | summary | status`, severity `Major` or `Major/Minor`) into the 7-column layout of line 3: `id | package | severity | summary | status | verifying artifact | reviewed commit`, with the severity in capitals, and each `Major/Minor` decided from its review file. Then the lead runs:
     ```
     awk -f p8b_ledger_check.awk handover/ledger.md > handover/evidence/P8b/ledger-check-cloud.txt 2>&1; rc=$?; echo "rc=$rc" >> handover/evidence/P8b/ledger-check-cloud.txt
     ```
     with `p8b_ledger_check.awk` saved in the lead's scratch folder from this text:
     ```
     BEGIN { FS="|" }
     /^\| *[A-Z][A-Z]-/ && !/^\| *id *\|/ {
       rows++
       if (NF != 9) { bad++; printf "BAD-LAYOUT line %d\n", NR; next }
       id=$2; gsub(/ /,"",id); sev=toupper($4); gsub(/ /,"",sev)
       st=$6; sub(/^ +/,"",st); split(st,w," "); s=toupper(w[1])
       if (sev!="BLOCKER" && sev!="MAJOR" && sev!="MINOR" && sev!="NIT") { bad++; printf "BAD-SEVERITY line %d\n", NR; next }
       if (sev!="BLOCKER" && sev!="MAJOR") next
       if (s=="FIXED-VERIFIED") next
       if (s=="WAIVED" || s=="OWNER-ONLY" || s=="IMPOSSIBLE-NOW") { printf "%s %s\n", s, id; next }
       open++; os[s]++
     }
     END {
       printf "rows=%d bad_layout=%d unresolved_blocker_major=%d\n", rows, bad+0, open+0
       for (k in os) printf "  status %s: %d\n", k, os[k]
       exit (bad+open > 0) ? 1 : 0
     }
     ```
     Pass: `rc=0`, `bad_layout=0`, `unresolved_blocker_major=0`, and every WAIVED row's "verifying artifact" cell names the owner's waiver id. The check reads every row whose id starts with two capital letters and a hyphen, so a new prefix is checked, not skipped. A MINOR or NIT row never blocks.
  3. **Laptop ledger check** (plan-v3 section 9, row "No unresolved findings", `plan-v3.md:185`), run after the lead has copied the cloud rows into the laptop ledger (plan-v3 line 54): `python egm/tools/ledger_check.py --topic core > ledger-check.txt 2>&1; echo "rc=$?" >> ledger-check.txt`, then `python egm/tools/ledger_lint.py >> ledger-check.txt 2>&1; echo "rc=$?" >> ledger-check.txt`. Pass: both `rc=0`, with WAIVED rows listed by id. UNVERIFIED: both tools are in the studio repo, not here. `ledger_lint.py` and the WAIVED status are built by P0d (`plan-v3.md:92`). Inventory A (`inventory-A.md:10`) records that the laptop check expects 9 columns while the cloud ledger has 7, so the lead's copy step maps the columns.
  4. **Section 9 paths:** for each test path or glob in `plan-v3.md:173-188`, `git ls-files '<path>'` on `main`. Any empty result is written to `section9-paths.txt` as `MISSING <path>`, and the corrected row goes to the lead.
  5. **README set:** `ls docs/kinds/ > readme-set.txt`, compared with the 15 names of Interface item 1 by `diff <(sort expected.txt) <(ls docs/kinds | grep -v '^README.md$' | sed 's/\.md$//' | sort)`, plus `git show origin/main:src/hadavin_sdk/backends/table.py | grep -E '^    "[a-z_]+": \{'` to list the `TABLE` keys at the merge commit. Pass: empty diff, and every key has a page.
  6. **Drift report:** the lead invokes `egm:egm-drift-report` through the Skill tool (never by reading the skill file) with this scope: `docs/kinds/`, the root `README.md`, and the frozen tickets in `handover/tickets/`, compared with core `main` at the step 1 commit. Output: `drift.md`. Pass: "no open drift" (plan-v3 line 188). Every drift item is either fixed in the docs pull request or, if the code is wrong, made a ledger row, and step 2 then fails until that row is closed. Per the blocker-ledger rule, the drift step also runs the ledger check: steps 2 and 3 are run last, after the drift fixes.
  7. **Planted faults:** P1 to P11 are run first. Output: `planted-faults.txt`, one line per fault with its exit code or printed line.
- **Reviewers: correctness + adversarial (fresh agents; they get the diff, this ticket and the evidence only):** Tier B: one fresh `egm:*` reviewer (`egm-codebase-details`, which checks every README claim against its `file:line` at the merge commit), one round, at most 2 fix batches (order 6(b)). The ticket itself gets the same single round (order 20 item 6, cap of 3 rounds, `LEAD-ORDERS.md:80`).
- **Done =** all of the following:
  1. T1 to T5 pass at one merge commit, written in every evidence file. That means the cloud check exits 0 with no bad layout and no unresolved BLOCKER or MAJOR, both laptop tools exit 0 with WAIVED rows listed by id, the drift report shows no open drift, all 15 pages exist, and every section 9 path exists.
  2. P1 to P11 behave as in the table.
  3. The docs pull request is green on every gate: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit, and the CI secret-and-name scan.

  **Honest note:** on today's ledger, step 2 fails with 727 unresolved rows. Most come from ticket-paper reviews whose fixes landed in later ticket revisions, but no row was ever moved to FIXED-VERIFIED (0 rows have that status). P8b cannot close them: each row is closed by its own package's build evidence and review before P8a, or is WAIVED by the owner. If that pass does not happen in each package, P8b will fail by design (PENDING LEAD item 4).
- **Rollback:** the lead tags `pre-P8b` before the merge (plan-v3 section 10). The change is docs only and is undone with a revert pull request. No migration and no semantic change.

## PENDING LEAD
1. README location: `docs/kinds/<kind>.md` plus an index (recommended), or `README.md` inside each kind's source folder (rejected above: single-module kinds share folders, and packaging is UNVERIFIED).
2. Kind set: the 15 of Interface item 1 (recommended; `diagnostic` and `executor` pages each say in their first line that they are not table kinds), or only the 8 `TABLE` keys.
3. Channel outline text "email-link approval channel; trigger: a client without Slack" (memo 6 wording, not in the repo). Recommend: the lead accepts it, or names the outline, before P8b runs; otherwise T4 cannot pass.
4. Ledger close-out: recommend that every package's result review moves its own ticket-review rows to FIXED-VERIFIED (citing the frozen revision and the build evidence) or to WAIVED, as part of that package, so that P8b only confirms. Also, 25 `BS-*` rows need the normalisation of Evidence step 2: recommend the lead does it now, not at P8b, so that new build-start rows use the 7-column layout.

## UNVERIFIED
`P8a.md` is not written. `ledger_check.py` and `ledger_lint.py` behaviour and arguments (studio repo, not visible here). The P0d WAIVED format. Whether `redactor` and `detector` are the same part. Whether `uv_build` ships non-Python files in the package. The final redactor wording in the merged P1, P2d and P5c tickets. The live status of every backend (all marked `_UNVERIFIED` in `table.py`).
