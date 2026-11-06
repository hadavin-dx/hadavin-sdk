# Package ticket P8b: one README per kind, the drift report and the ledger check. DRAFT revision 3

Revision 3 written 2026-11-06 about 03:25 UTC (08:55 IST; IST = UTC+5:30) by the ticket revision author from `handover/reviews/P8b-round2-resolve.md` (32 finding ids, ADV 19 and COR 13, in 22 decision rows; all 22 PROPOSE FIX, four of them partly CONTESTED and two partly DECLINED, each applied as the resolve decided). The replacement texts R1 to R7 (the Blocker and every Major) are in this revision word for word; where the resolve set them as a quote, the quote marks are dropped and the words are unchanged. Revision 2 was written 2026-11-06 about 03:00 UTC (08:30 IST), commit `10805bc`; revision 1, commit `0d04aa3`. Text only: no code, no suite run, no pull request.
> **Build notes win.** Revision 3 is frozen text. Where a build note BN-1 to BN-17 (from `handover/reviews/P8b-round3-resolve.md`, copied into the section "Build notes (round 3)" at the end of this ticket) differs from the revision 3 text, the build note wins. R1 to R7 in the CHANGELOG are the replacement texts of `handover/reviews/P8b-round2-resolve.md` (round 2); BN-n are the round 3 fixes. The CHANGELOG sections are history, not instructions.

**Where the code facts were read (revision 3):** every code line cited below was re-read with `git show 4ec3616:<file>` at `origin/main` = `4ec3616` (2026-11-06 03:12 UTC, 08:42 IST), not on a worktree. The counts of `TABLE` came from importing `backends/table.py` out of a `git archive 4ec3616 src` copy with `python3 -I` (no `uv`). Ledger facts were read on branch `core/cloud-handover` at commit `ea6402f`; the ledger keeps growing while sessions work, so every ledger count is "read at `ea6402f`" and is never "today's". Anything not read is marked UNVERIFIED. "PENDING LEAD" means the author proposes it and no lead decision exists yet.

**Round rule:** order 20 item 6 (`LEAD-ORDERS.md:80`): at most 3 rounds counting from round 1. This revision answers round 2, and round 3 is the last (P8b is not a money or redaction package, so there is no round 4). Minors left after round 3 go to the build notes; then freeze; then the build-start review (order 20 item 3, `LEAD-ORDERS.md:77`; order 21 item 17, `LEAD-ORDERS.md:88`).

## CHANGELOG (revision 2 to revision 3), one line per decision row of the resolve
1. **R2-ADV-1 = R2-COR-1 (Blocker; Major), R1.** The evidence header is no longer `git rev-parse origin/main`. Core files record `base` (origin/main) and `head` (the docs PR branch `core/P8b`) through `hdr_core`; ledger files record the `core/cloud-handover` commit through `hdr_ledger`, after a clean-file check. A rebase makes the core files stale, and they are re-run; the lead re-runs steps 6 and 9 at the merge commit. Done item 2 is reworded to match. Step 1 is now "Branch".
2. **R2-ADV-2 (Major), R2.** New run order: inputs first (step 2), then the ledger faults (3), then the pages (4), then the control run and the page faults in a named scratch copy with `cd` (5), then the real checks (6), drift (7), the draft PR review (8) and the ledger checks last (9).
3. **R2-ADV-3 = R2-COR-13, with R2-COR-12, R3.** The artifact test now covers all four closed statuses, FIXED-VERIFIED included. New fault P23. The "Unresolved" definition gains "or any of these four with an empty or `-` artifact cell".
4. **R2-ADV-4 (Major; partly CONTESTED), R3.** A line that holds a `|` but does not start with one prints `BAD-STRAY`; the separator must contain a `-`, so an all-blank row becomes `BAD-LAYOUT`. The reviewer's wider rule ("any non-blank non-pipe line is bad") is not taken: ledger lines 1 and 358 are prose headings and would fail for no fault. New faults P24 and P25.
5. **R2-ADV-5 = R2-COR-7 (Major; Minor), R4.** No new T7 (cut surface, order 8). T6 gains: the positive "production choice" rule, the 8 headings as exact lines, at most 60 lines, the not-a-kind line above heading 1 on the 7 non-table pages, the two "not the same as" links, and the two A6 outlines inside heading 4. New faults P26 to P31. T4's pass rule is defined (row 8).
6. **R2-ADV-6 (Major; partly CONTESTED), R4.** New literal block `forbidden.txt` ("re-cased", "caught by nothing"), checked on every page and on the README paragraph (fault P27). "covered" and "all copies" are not forbidden: no order forbids them. Each required phrase is written on one line. One owner-visible-limit line cites order 19 B.
7. **R2-ADV-7 with R2-COR-4 (Major; Minor; partly CONTESTED), R5.** `tools/proof_pack.py` is removed from `section9-list.txt` (a tool, not a test file; P8c owns its own row). The cite is `plan-v3.md:174-184`. The reviewer's detail "`tools/` does not exist yet" is wrong: `tools/` exists on main (`tools/scan_repo.py`, `scan_allowlist.txt`, `scan_banned_extra.txt`). "Either order with P8c" stays.
8. **R2-ADV-8 (Major), R6.** The INFO route is deleted (the skill has no INFO class). "Open drift" = a bullet in `drift.md` with no row in the lead-checked `drift-dispositions.md`. The narrower scope than plan row 188 is PENDING LEAD 9. The INFO sentence is deleted from the Source field and from the revision 2 CHANGELOG below.
9. **R2-ADV-9 = R2-COR-6 (Major; Minor), R7.** Fixed content of headings 3 and 6 for the 7 non-table pages. The channel and executor outlines sit under heading 4 only; heading 8 repeats only the v1.1 row. T6 (d) checks the placement (P31).
10. **R2-ADV-10 (Minor).** `t1.sh` uses `sort -u`, an `IN-BOTH` check (`comm -12`) and an output-based rc. Rule: a name in both lists means the table wins; the name is deleted from `extra-kinds.txt` and the page loses its not-a-kind line. Fault P32.
11. **R2-ADV-11 = R2-COR-5 (Minor; Minor).** Data files carry no header; each file generated from code has a `<name>.log` with the header and rc; literal blocks are copied from this ticket; the full file list is in step 2. `readme-redaction.txt` is written to a temporary folder inside `t6.sh`, and nothing is copied into the checkout root. The evidence folder sits on `core/cloud-handover`, never in the docs PR.
12. **R2-ADV-12 (Minor).** Reworded: "Every check except T4 and the T3 count check has a planted fault. P20's result is recorded by the lead on its first run; `ledger_lint.py` has none (tool not visible)."
13. **R2-ADV-13 (Minor) + PENDING LEAD 8.** The Reviewers field states the round rule of order 20 item 6. Depends on gains item 5 (freeze and build-start review; S0 EXIT per order 21 item 17). Who writes the pages and who runs the checks is PENDING LEAD 8 (sent to the lead as NEEDS LEAD 42).
14. **R2-ADV-14 (Minor; the suggested cut DECLINED).** Every count is "read at `<sha>`". Done item 2 says "the T1 set, derived at run time". A renamed `_UNVERIFIED` makes the `roles.txt` import fail with a non-zero rc in `roles.log`, which stops the run (fail closed). The "not yet run live" label stays.
15. **R2-ADV-15 (Minor), R2 steps 7-9.** One order: checks, then the draft PR review, then the fix batch, then a re-run of steps 5 (control) and 6, then closing the rows, then the final ledger step.
16. **R2-ADV-16 = R2-COR-3 (Minor; Minor).** Files, Change: the root README redaction paragraph is rewritten (it fails T6 on main today, fault P33).
17. **R2-ADV-17 + R2-COR-11 + R2-COR-2 (Nit; Nit; Minor; one part DECLINED).** `DEV_ONLY` is cited `table.py:593-602`. The pages cite the refusal that exists now (`config.py:366-369`, `config.py:391-392`); the P6a condition is deleted. The `BAD-PROD-CHOICE` match on "not a production choice" stays fail-closed on purpose.
18. **R2-ADV-18 (Nit).** "Existing core code reused" names `tests/contracts/`.
19. **R2-ADV-19 (Nit).** PENDING LEAD 6: the lead spot-checks every rewritten severity against its review file before the T2 run.
20. **R2-COR-8 (Minor; partly CONTESTED).** "textnorm, usage and meter are planned as single modules inside shared folders (their packages create them before P8a)". `defaults.py` is on `origin/main` (`git ls-tree 4ec3616` lists `src/hadavin_sdk/defaults.py`), so "P8b does not touch it" stays a true statement.
21. **R2-COR-9 (Minor; reuse).** Step 6 runs the existing scanner `python tools/scan_repo.py` (CI runs it at `.github/workflows/ci.yml:83`) in the PR checkout after the pages are committed, saved as `E/scan.txt`; pass `rc=0`. No new grep.
22. **R2-COR-10 (Nit).** The section 9 test-path rows are cited `plan-v3.md:174-184`.
- **Also changed by the author (checked):** the code-read header now points at `4ec3616` read with `git show`; the expected lines of P5 (`... line 4`), P9 and P17 (`SET-DIFF <name>`, the `t1.sh` output) and P15 (also `NO-ROWS`) are written as the scripts print them; the evidence file names follow R2 (`t1.txt`, `t5.txt`, `t6.txt` replace `readme-set.txt`, `section9-paths.txt`, `t6-pages.txt`). The UNVERIFIED item on `git ls-files` glob pathspecs is removed: `git ls-files 'tests/warden_port/test_redaction*.py'` lists 6 files and `git ls-files 'tests/test_redact*.py'` lists none.
- **PENDING LEAD:** 8 and 9 are new (from the resolve); 6 and 7 are extended (items 19 and the coupling on the artifact rule).

## CHANGELOG (revision 1 to revision 2), kept for history
- **Ledger check script replaced** (ADV-1 = COR-1, ADV-2, ADV-11 = COR-10, ADV-19). The old row filter `/^\| *[A-Z][A-Z]-/` skipped every id with a digit or three letters in its prefix (`R1-`, `R2-`). Revision 3 replaces the script again (R3).
- **Drift scope cut to `docs/kinds/`** (ADV-3 = COR-5). Frozen tickets and plan-v3 are inputs only. (The INFO sentence that stood here was deleted in revision 3, R6.) The root `README.md` redaction paragraph is checked by the deterministic T6, not by the LLM skill.
- **Ledger close-out moved into "Depends on"** (ADV-4 = COR-4), owner PENDING LEAD 5; every ledger figure "read at commit `<sha>`" (COR-2).
- **P8a is written** (ADV-12 = COR-3): P8a ticket revision 1 (draft, `db09637`); P8a item 8 (`P8a.md:78`) is taken into Interface item 4.
- **Backends roles defined from code** (ADV-5 = COR-6); **redactor and detector settled from code** (ADV-6 = COR-7); **channel and executor outlines in A6's words** (COR-8, PENDING LEAD 3 closed by A6); **README set derived from code** (ADV-7); **new T6** (ADV-8); **one run order** (ADV-9); **one evidence command form** (ADV-10 = COR-9); smaller fixes ADV-13, 14, 16, 17, COR-11, 12, 13.
- **Kept by CONTEST (ADV-18):** the "not yet run live" tag stays per row: detector `regex` (`table.py:544`) has no `status`, and `llm_judge` (`table.py:546-548`) has `status=_UNVERIFIED`.

## Words used in this ticket
- **kind**: one replaceable part of the core behind a fixed interface, with a default and an alternative (or a written outline with the event that would make us build it, called its **trigger**). Example: the `store` kind. Its **config default** (what the core uses when the config names nothing) is `memory`, which is dev only; its production backend is Postgres.
- **kind README** (or **page**): one short plain-word page per kind, saying what the kind does, which backends exist, what role each plays, and what it does not do.
- **drift**: a sentence in a document that no longer matches the code. **Drift report**: the output of the `egm:egm-drift-report` skill. It is an LLM skill (a model writes it), so its output is not the same on every run. **Open drift**: defined in step 7.
- **ledger**: the table of review findings. It is `handover/ledger.md` in the cloud (on branch `core/cloud-handover`, not on `main`) and `egm/BLOCKER-LEDGER.md` on the laptop (`plan-v3.md:26`). **Unresolved**: a BLOCKER or MAJOR row whose status is anything except FIXED-VERIFIED, WAIVED, OWNER-ONLY or IMPOSSIBLE-NOW, or any of these four with an empty or `-` artifact cell.
- **ledger id prefixes**: `BL-` rows from the lead; `BS-` rows from build-start reviews; `R1-`, `R2-` and `R3-` rows from ticket reviews of rounds 1, 2 and 3.
- **plan-v3**: the core plan, `studio-notes/plan-v3.md`. **memo 6**: the lead's check of plan-v3's claims against the code (`studio-notes/memos/memo-6-kernel-and-claims.md`). **A6**: amendment 6 in `studio-notes/amendments.md:9`. An amendment wins over plan-v3.
- **planted fault**: a deliberate error put into a throwaway copy of an input, to prove that a check catches it. Here it plays the part a code mutant plays in a code package. A **control** is a copy with no error, which must pass.
- **`E/`**: the evidence folder `handover/evidence/P8b/` on branch `core/cloud-handover`.

## Template fields in the template's order

- **Package id and name:** P8b, "One README per kind, the drift report and the ledger check" (plan-v3 row, `plan-v3.md:113`). It is one docs pull request to core (the pages, the root README redaction paragraph and one CHANGELOG line), plus checks. Step S5, milestone v1, consumers: none.
- **Path class:** other. **Extended review (no round cap): no.** P8b adds no code, so it is not a money, redaction or security path. Only the redactor page and the root README paragraph describe a redaction path. Their wording follows orders 14, 15 and 19 C and is checked by T6 (field "Interface", item 3).
- **Depends on (merged first):**
  1. **P8a, ticket revision 1 (draft, `db09637`).** P8a depends on every v1 row except P8a, P8b and P8c (`plan-v3.md:112`), so P8b starts only after every v1 code row is merged and the demos are re-pinned.
  2. **Ledger close-out finished.** Every BLOCKER or MAJOR row is FIXED-VERIFIED, WAIVED, OWNER-ONLY or IMPOSSIBLE-NOW with a named artifact, except the rows of P8b itself (its ticket review rows `R1-P8b-*`, `R2-P8b-*`, `R3-P8b-*` and the docs pull request's review rows). Who does this pass is PENDING LEAD 5.
  3. **The cloud's 5-cell ledger rows are normalised** (PENDING LEAD 6). Until then T2 fails with `BAD-LAYOUT` by design.
  4. **The P0d tool changes** are a hard dependency of the laptop check (step 9).
  5. **P8b's freeze and its build-start review** (order 20 item 3; S0 EXIT per order 21 item 17, `LEAD-ORDERS.md:88`).

  P8b is not in the code merge chain of order 20 item 4 (`LEAD-ORDERS.md:78`: P1m, P1a, P1b, the P3a and P4d chain, P2a-1, P2d-1, P2d-2, P4a). It merges after all of those and after P8a, in either order with P8c. P8b and P8c share no file: P8c writes `tools/proof_pack.py` and P8b writes `docs/kinds/`, and `tools/proof_pack.py` is not in P8b's T5 list (P8c owns plan row 187). `defaults.py` (order 20 item 5, `LEAD-ORDERS.md:79`) exists on `origin/main` (read at `4ec3616`); P8b adds no constants and does not touch it.
- **Problem in plain words:**
  - The core has eight kinds in its backend table and seven more parts that plan-v3 section 5 calls kinds. No page says, for each one, what it does, which backends exist, what role each backend plays and what it does not do.
  - There is no `README.md` under `src/hadavin_sdk/` (read at `4ec3616`: `git ls-tree -r 4ec3616 src/hadavin_sdk` lists none).
  - Two of plan-v3's claims about kinds were already found wrong in code (A6: llm has no configured default; channel has one real backend). So pages written from the plan instead of the code would be wrong on day one.
  - Separately, "v1 is done" needs proof that no BLOCKER or MAJOR finding is left unresolved. Read at `ea6402f`, the cloud ledger cannot pass a check: the revision 3 check (R3) gives `rows=1711 bad=268 unresolved_blocker_major=727` (OPEN 585, FIXED-UNVERIFIED 142), rc 1; all 268 bad lines are `BAD-LAYOUT` (5-cell rows), with 0 `BAD-STRAY` and 0 `BAD-NO-ARTIFACT`. The newest row, `R3-P5a-COR-1`, is still in 5 cells.
- **Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:** No code. The pages are written from the code at the `base` commit of step 1 (written into every core evidence file). The sources, in order of authority:
  1. code;
  2. A6 and memo 6 section B (the claim checks);
  3. each package's frozen ticket;
  4. plan-v3 section 5.

  Where these disagree, the code wins. A disagreement found in a page is fixed in the page. If the code itself is wrong, it becomes a ledger row for the package that owns the code. Frozen tickets and plan-v3 are inputs only, never in the drift scope, and are not edited by P8b. Not taken: plan-v2's "rollback tags" item for P8b (`plan-v2.md:117`), because plan-v3 section 10 gives tagging to the lead before each merge (`plan-v3.md:193`).
- **Target module and path in `src/hadavin_sdk/`:** none. The pages go to `docs/kinds/<kind>.md`, plus an index `docs/kinds/README.md` (PENDING LEAD item 1). `docs/` already exists in core: read at `4ec3616`, `git ls-tree 4ec3616 docs/` lists 2 files, both about Slack. Reasons not to put the pages under `src/`: textnorm, usage and meter are planned as single modules inside shared folders (their packages create them before P8a), so "README in the kind's folder" has no single meaning. Also, the build backend is `uv_build` (`pyproject.toml:57-58`), and whether it ships a non-Python file inside the package is UNVERIFIED. With the pages in `docs/`, that question does not arise.
- **Interface (names, argument and return types, errors):**
  1. **The kind set: the T1 set, derived at run time** (PENDING LEAD item 2). Read at `4ec3616` it is 15 pages:
     - (a) The capability keys of `TABLE` (`backends/table.py:386`), read at `4ec3616`: `secrets` (`:387`), `signer` (`:427`), `anchor` (`:467`), `store` (`:492`), `audit` (`:502`), `llm` (`:512`), `detector` (`:543`) and `channel` (`:558`). They are the same eight fields as `Backends` (`config.py:62-72`). Read at `4ec3616`, the table has 31 entries in all. A key added later by P5c or P6b2 changes the set without editing this ticket.
     - (b) The plan-v3 section 5 rows that are not table keys (`plan-v3.md:75-84`), written as the literal block `extra-kinds.txt` used by T1:
       ```
       diagnostic
       executor
       meter
       redactor
       stop_state
       textnorm
       usage
       ```
     - **If a name is in both lists, the table wins:** the name is deleted from `extra-kinds.txt`, and the page loses its not-a-kind line (`t1.sh` prints `IN-BOTH <name>` until then; fault P32).
     - Each of the pages in (b) has one line under the page title, above heading 1, that says it "is not a kind in the backend table" (checked by T6 (c)). `diagnostic` "is a rendering rule, not a kind" (P5a ticket and `plan-v3.md:80`). `executor` is not a table kind (A6): it is `class Executor` (`actions/executor.py:47`), chosen per action contract through `NoneExecutor`, `ManualExecutor` and `HttpExecutor` (`actions/contract.py:15, 22, 33`).
     - **Redactor and detector are different parts** (settled from code):
       - `redactor.md` covers `guard.redact`: `redact` (`guard/redact.py:862`, exported by `guard/__init__.py:3`) and `redact_many` (`guard/redact.py:1244`, not exported there). Its job is masking values before text leaves.
       - `detector.md` covers the `detector` capability: the `Detector` protocol (`guard/injection.py:19`); `RegexDetector` (`guard/injection.py:38`), built by `regex_detector` (`backends/builtin.py:43`); and the other backends, `llm_judge` and `bedrock_guardrail` (`table.py:546-556`). Its job is scoring text for prompt injection.
       - `redactor.md` carries the line `not the same as [detector](detector.md)` and `detector.md` carries `not the same as [redactor](redactor.md)` (checked by T6 (d)).
  2. **Fixed headings of every page.** At most 60 lines; plain words; no model ids, no prices, no real-looking values. The eight headings are written as these exact lines (checked by T6 (b)): `## What it does`, `## Interface`, `## Backends`, `## Single dependency`, `## Identity and rights`, `## Configuration keys`, `## Tests that cover it`, `## What it does not do`.
     1. What it does: 2 to 4 sentences.
     2. Interface: the protocol or class name with `file:line`.
     3. **Backends:** one table row per `TABLE` entry, in the form `` | `<backend>` | <labels> | <module> | ``. The labels column holds every label that applies, comma-separated, in these words, taken from code in this order:
        - **config default**: the `DEFAULTS` entry (`table.py:582-589`, read at `4ec3616`: secrets `fake`, signer `none`, anchor `none`, store `memory`, detector `regex`, channel `fake`), used when the config names nothing. `audit` and `llm` have no entry, so their pages say "no default; config must name one".
        - **dev only**: the pair is in `DEV_ONLY` (`table.py:593-602`). The page explains it once as "allowed only in `dev` (`table.py:591`)". The page cites the refusal that exists now: `config.py:366-369` (dev-only pairs refused outside `dev`) and `config.py:391-392` (not-for-production pairs refused in `prod` only, so `pilot` allows them). A refusal that P6a adds later is caught by T4.
        - **not for production**: the pair is in `NOT_PROD` (`table.py:604`): signer `none` and anchor `none`.
        - **open standard**: the entry has `neutral=True` (`table.py:342-344`).
        - **not yet run live**: the entry has `status=_UNVERIFIED` (`table.py:380`). Read at `4ec3616` this is 23 of the 31 entries, and the tag is per row (ADV-18 contested in round 1). If `_UNVERIFIED` is renamed, the `roles.txt` import fails with a non-zero rc in `roles.log`, which stops the run (fail closed).
        - **production choice**: an entry that is neither dev only nor not for production. Such a row always says "production choice", and a dev-only or not-for-production row never does (checked by T6 (a)). The label words are used only in the labels column; a page that writes "not a production choice" in a row fails T6 on purpose (fail closed).

        Each page with a config default says in one line whether that default is dev only or not for production. Read at `4ec3616`, five of the six are: secrets `fake`, store `memory` and channel `fake` are dev only, and signer `none` and anchor `none` are not for production. Only detector `regex` is neither. The detector page says the config holds a list (`config.py:71`: `detector: tuple[KindSettings, ...]`), so several detectors can run at once.
     4. Single dependency: the default, then the alternative, or the outline with its trigger. A6 applies:
        - llm has four real backends and no default, so config must name one.
        - secrets `fake` and `env` are dev only, so production uses `mounted_file` or `vault` (or a cloud manager).
        - channel has one real backend, Slack. **Channel outline (A6 words):** "second channel = email; trigger: a client needs email approvals". It is written in `channel.md` heading 4.
        - **Executor outline (A6 words):** "per-contract none/manual/http; http refused in pilot and prod; manual not built; outline with trigger". It is written in `executor.md` heading 4.
     5. Identity and rights: as declared by P6b2 (kind identity and rights), or "none declared".
     6. Configuration keys: from `config.py`.
     7. Tests that cover it: the test file paths, for example `tests/contracts/` for store.
     8. What it does not do: plain facts, each with its v1.1 row and trigger, never "known limitation".

     For the 7 pages that are not table kinds, heading 3 holds one line, "Not in the backend table: `<module or rule>` (`file:line` once its package has merged)". Heading 6 lists the config keys that the part's own package added to `config.py`, or says "No configuration keys". The channel and executor outlines are written under heading 4 only; heading 8 repeats only the v1.1 row and its trigger. T6 (d) checks the heading-4 placement.
  3. **Redactor wording (orders 14, 15 and 19 C).** `redactor.md` and the root `README.md` paragraph that starts "Redaction is pattern-based and bounded" (found by those words, not by a line number; read at `4ec3616` it is `README.md:31`) both say the following:
     - For secrets of 8 to 11 characters, the redactor catches "only plain copies" (order 15, `LEAD-ORDERS.md:44`). The case-folded sweep is v1.1 row LKV-2, trigger "before any pilot with real client data".
     - A known value hidden in invisible characters, base64 or hex is not caught in v1, except the exact hex and base64 spellings of a secret handed to a tool, which `tools.py` scrubs (`tools._secret_forms`, `tools.py:744`; order 14(1) as narrowed by order 19 C, PL46(a), `LEAD-ORDERS.md:38, 67`).

     The pages use the wording of the frozen P1 coverage sentence (`P1.md:20`: "copies of secrets of 8 to 11 characters, which are common passwords, reach the model"; "only the tool-output scrubber removes the exact hex and base64 spellings of a secret handed to a tool"), plus order 15's phrase "only plain copies". T6 (e) checks these phrases (block `phrases.txt`, step 2); **each required phrase is written on one line** (a phrase wrapped over two lines fails closed with `MISSING-PHRASE`). No page and not the README paragraph may contain a retracted wording of block `forbidden.txt`: "re-cased" (order 15 retracts "plain and re-cased", `LEAD-ORDERS.md:44`) and "caught by nothing" (order 19 C retracts it, `LEAD-ORDERS.md:67`). "covered" and "all copies" are not forbidden: no order forbids them. If P1's merged wording differs from revision 16, both blocks change with it. **Owner-visible limit:** the short-password limit is one the lead shows the owner (order 19 B, `LEAD-ORDERS.md:66`); the pages state it, they do not soften it.
  4. **Section 9 test-file table and the "Demos re-pinned" row.** `plan-v3.md:190` gives P8b a duty for "All test files named above": "if a package names its test file differently, P8b updates this table". P8b checks every path in the block below on the docs PR head (step 6, T5) and sends the corrected rows to the lead, who edits `plan-v3.md`. The block of test paths named in `plan-v3.md:174-184` (`section9-list.txt`) is:
     ```
     tests/test_textnorm_differential.py
     tests/test_redact*.py
     tests/warden_port/
     tests/test_stop_state*.py
     tests/test_migration_numbers.py
     tests/contracts/
     tests/test_usage*.py
     tests/test_meter*.py
     tests/test_run_cap.py
     tests/test_training_lock.py
     tests/test_secrets_import.py
     tests/test_env_lint.py
     tests/test_kind_identity.py
     tests/test_c1_acceptance.py
     tests/test_diagnostics_hostile.py
     tests/test_client_profile.py
     ```
     Today only `tests/contracts/` and `tests/warden_port/` exist. Every other path is created by the package in column 2 before P8a, and T5 runs after all of them are merged, so only a path still missing then counts. `tests/test_redact*.py` is the one known mismatch: the replacement name comes from the P2d ticket. `tools/proof_pack.py` is not in the list: it is a tool, not a test file (line 190), and P8c owns its section 9 row (line 187).

     Each `MISSING` row goes to the lead with the replacement name from the owning ticket. P8b also sends the corrected "Demos re-pinned" row (P8a item 8, `P8a.md:78`; A7 and A9 F9): the command is `tools/core_sync_check.py --core <core> --demo <dir> [--strict-pin]` (studio), not `python tools/check_core_copies.py`.
- **Neutral default / working alternative (or written outline with trigger):** not applicable: P8b adds no dependency. Single-dependency audit: each page states its kind's default and alternative, or its outline with a trigger. A kind with neither gets a drift item that the lead must answer before "done". The two known cases are already decided by A6 and are written in the pages under heading 4 (channel: email, trigger "a client needs email approvals"; executor: per-contract outline). So the repo gains both outlines with this pull request.
- **Files to create, change, delete (each with the reason):**
  - **Create:** `docs/kinds/README.md` (the index: one line per kind, with a link) and one page per name of the T1 set, read at `4ec3616` the 15 pages `docs/kinds/{secrets,signer,anchor,store,audit,llm,detector,channel,textnorm,stop_state,usage,meter,diagnostic,redactor,executor}.md`, so 16 files in all.
  - **Change:** `CHANGELOG.md`, one append-only line ("docs: one page per kind"). Root `README.md`: the redaction paragraph is rewritten (it fails T6 on main today, fault P33).
  - **Not changed:** nothing in `src/` or `tests/`. Nothing is deleted, and no new tool or CI job is added (cut surface, order 8). A CI check that the page set matches `TABLE` is a v1.1 row, trigger: a kind added after v1 without its page.
  - **Evidence files** (all under `E/` on branch `core/cloud-handover`, never in the docs pull request; the full list is in step 2).
- **Existing core code reused (checked):** `backends/table.py` (`TABLE`, `DEFAULTS`, `DEV_ONLY`, `NOT_PROD`, `_UNVERIFIED`, `Entry.neutral`, `Entry.status`) and `config.py` `Backends` are the source of every Backends table; they are read, not changed. `config.py:366-369` and `:391-392` are the refusal the pages cite. `tools/scan_repo.py` (the CI secret-and-name scanner, `.github/workflows/ci.yml:83`) is reused as the step 6 scan; it is not changed. `tests/contracts/` exists (store contract suite); it is cited by `store.md` heading 7 and not changed. A6 and memo 6 section B are the claims check. Hashing, k1b/atomic, k1b/redaction, stats, evals and store/memory are not relevant, because no code is written.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):**
  - Docs only, with no identity, no rights and no secret.
  - The public-repo rule applies (order 20 item 4, `LEAD-ORDERS.md:78`; order 8(5), `LEAD-ORDERS.md:21`): no owner names, no studio paths, and no real-looking key or token, even as an example. Use placeholders such as `<KEY>`.
  - The CI secret-and-name scan must stay green on the docs pull request; step 6 runs the same scanner first (`E/scan.txt`, pass `rc=0`).
  - No page shows a dev-only or not-for-production backend as a production choice. T6 (a) checks every `DEV_ONLY` and `NOT_PROD` pair.
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** there are no unit tests (no code); the checks below are the tests. Every check except T4 and the T3 count check has a planted fault. P20's result is recorded by the lead on its first run; `ledger_lint.py` has none (tool not visible). The planted faults run before the real checks, so a check that cannot fail is caught first. T4 is an LLM report that the lead reads, with a mechanical pass rule (step 7).
  - **T1, page set:** `t1.sh` (step 2, R4) prints nothing but `t1_fail=0`: no `IN-BOTH` name, no `SET-DIFF` between the `TABLE` keys plus `extra-kinds.txt` and the pages in `docs/kinds` (without `README.md`), and the index exists.
  - **T2, ledger check (cloud):** `p8b_ledger_check.awk` exits 0 on `handover/ledger.md` (step 9). **Fail-before:** on the ledger before the close-out, the check exits 1 and prints `UNRESOLVED` and `BAD-LAYOUT` lines. Read at `ea6402f` (author's scratch run, mawk 1.3.4): `rows=1711 bad=268 unresolved_blocker_major=727`, rc 1. That is not evidence, and the runner re-runs it.
  - **T3, ledger check (laptop):** `ledger_check.py` and `ledger_lint.py` both exit 0, and the copied BLOCKER and MAJOR count equals the cloud count (step 9).
  - **T4, drift report:** no open drift in `docs/kinds/` (step 7). No planted fault.
  - **T5, section 9 paths:** every path of `section9-list.txt` exists on the docs PR head, or is reported as `MISSING` with its replacement (step 6).
  - **T6, deterministic page checks** (`t6.sh`, grep and awk, no LLM; step 6):
    - (a) every Backends row has exactly the code's labels; a row with neither dev only nor not for production says "production choice", and any other row does not;
    - (b) every page has the 8 headings as exact lines and at most 60 lines;
    - (c) the 7 non-table pages have the not-a-kind line above heading 1;
    - (d) the no-default sentence on `audit.md` and `llm.md`, the two cross links, and the two A6 outlines inside heading 4;
    - (e) `redactor.md` and the README paragraph contain every phrase of `phrases.txt`, each written on one line, and no page contains a phrase of `forbidden.txt`.
  - **Scan:** `python tools/scan_repo.py` exits 0 on the docs PR head (step 6).
  - Hostile inputs, races and contract suite: not applicable (no code).
- **Mutation plan: which behaviours get a mutant, which test kills each.** These are planted faults, each in a throwaway copy, never in the real ledger or the real docs.
  - **Ledger faults (P1 to P8, P12 to P14, P21 to P25):** each is a ledger file of the header line, the separator line, one FIXED-VERIFIED MAJOR row with artifact `a`, and the row named below (line 4). **P15 and P16:** as stated in the table.
  - **Page and set faults (P9, P10, P17 to P19, P26 to P33):** each on a fresh scratch copy of the committed pages (step 5). **P11:** the T5 loop on a scratch `section9-list.txt`. **P20:** laptop, step 9.
  - **The author's scratch runs** (not evidence; the runner re-runs every fault): all 18 T2 faults with the revision 3 awk on mawk 1.3.4, plus the three P24 forms and both P23 forms; the control and all 13 T1 and T6 faults with `t1.sh` and `t6.sh` on dash, on scratch pages generated from `roles.txt` (read at `4ec3616`), each giving exactly the line below. P11 and P20 were not run.

  | Fault | Planted row or change | Killed by | Expected |
  |---|---|---|---|
  | P1 | 5-cell row `\| BS-PX-1 \| Major \| PX \| s \| OPEN \|` | T2 layout rule | rc 1, `BAD-LAYOUT line 4 id BS-PX-1` |
  | P2 | BLOCKER, status OPEN | T2 | rc 1, `UNRESOLVED OPEN <id>` |
  | P3 | lower-case `major`, status FIXED-UNVERIFIED | T2 (severity case fold) | rc 1, `UNRESOLVED FIXED-UNVERIFIED <id>` |
  | P4 | unknown status `DONE` | T2 (fail closed) | rc 1, `UNRESOLVED DONE <id>` |
  | P5 | severity `Major/Minor` | T2 severity rule | rc 1, `BAD-SEVERITY <id> line 4` |
  | P6 | status `OPEN (build notes)` | T2 (first word only) | rc 1, `UNRESOLVED OPEN <id>` |
  | P7, control | MINOR, status OPEN | T2 | rc 0 |
  | P8, control | MAJOR, status WAIVED, artifact cell `W-1` | T2 | rc 0, `WAIVED <id>` printed |
  | P9 | delete `docs/kinds/channel.md` in a scratch copy | T1 | rc 1, `SET-DIFF channel` |
  | P10 | scratch `secrets.md`: the `env` row says only `production choice` | T6 (a) | rc 1, at least the lines `WRONG-LABEL secrets env 'dev only' code=1 page=0` and `BAD-PROD-CHOICE secrets env` (the run also prints `WRONG-LABEL secrets env 'not yet run live' code=1 page=0`) |
  | P11 | add `tests/no_such_file.py` to a copy of `section9-list.txt` | T5 | `MISSING tests/no_such_file.py` |
  | P12 | 5-cell `\| R2-PX-1 \| Blocker \| PX \| s \| OPEN \|` | T2 layout rule | rc 1, `BAD-LAYOUT line 4 id R2-PX-1` |
  | P13 | the same id in 7 cells, BLOCKER, OPEN | T2 (digit in prefix read) | rc 1, `UNRESOLVED OPEN R2-PX-1` |
  | P14 | `\| ABC-1 \| PX \| BLOCKER \| s \| OPEN \| a \| c \|` | T2 (3-letter prefix read) | rc 1, `UNRESOLVED OPEN ABC-1` |
  | P15 | empty file | T2 header and row rules | rc 1, `BAD-HEADER count=0` and `NO-ROWS` |
  | P16 | one valid row, no header line | T2 header rule | rc 1, `BAD-HEADER count=0` |
  | P17 | append `fakekind` to a scratch copy of `table-keys.txt` | T1 | rc 1, `SET-DIFF fakekind` |
  | P18 | delete the line with "only plain copies" from a scratch `redactor.md` | T6 (e) | rc 1, `MISSING-PHRASE docs/kinds/redactor.md: only plain copies` |
  | P19 | scratch `store.md`: the `postgres` row says `config default` | T6 (a) | rc 1, `WRONG-LABEL store postgres 'config default' code=0 page=1` |
  | P20 | scratch copy of the laptop ledger with one MAJOR OPEN row | T3 | `ledger_check.py` exits non-zero; the exact output is recorded by the lead on its first run (UNVERIFIED: the tool is not visible here) |
  | P21 | MAJOR, status WAIVED, empty artifact cell | T2 artifact rule | rc 1, `BAD-NO-ARTIFACT WAIVED <id>` |
  | P22 | a second row with the id of the FIXED-VERIFIED row | T2 duplicate rule | rc 1, `BAD-DUP <id> lines 3 4` |
  | P23 | MAJOR, status FIXED-VERIFIED, artifact cell empty (and a second copy with `-`) | T2 artifact rule | rc 1, `BAD-NO-ARTIFACT FIXED-VERIFIED <id>` |
  | P24 | a BLOCKER OPEN 7-cell row indented by two spaces (also run with `> ` and with a tab in front) | T2 stray rule | rc 1, `BAD-STRAY line 4` |
  | P25 | `\| \| \| \| \| \| \| \|` | T2 (separator needs `-`) | rc 1, `BAD-LAYOUT line 4 id ` |
  | P26 | `detector.md`: the `regex` row loses "production choice" | T6 (a) | `MISSING-PROD-CHOICE detector regex`, rc 1 |
  | P27 | append "Plain and re-cased copies." to `redactor.md` | T6 (e) | `FORBIDDEN-PHRASE docs/kinds/redactor.md: re-cased`, rc 1 |
  | P28 | delete the line `## Tests that cover it` from `usage.md` | T6 (b) | `MISSING-HEADING usage: ## Tests that cover it`, rc 1 |
  | P29 | pad `meter.md` to 61 or more lines | T6 (b) | `TOO-LONG meter <n>`, rc 1 |
  | P30 | delete the not-a-kind line from `textnorm.md` | T6 (c) | `MISSING-NOT-A-KIND textnorm`, rc 1 |
  | P31 | move the executor outline from heading 4 to the end of the page | T6 (d) | `MISSING-OUTLINE executor`, rc 1 |
  | P32 | append `redactor` to a scratch `table-keys.txt` | T1 | `IN-BOTH redactor`, rc 1 |
  | P33 | the root `README.md` of `origin/main` as it is (fail-before) | T6 (e) | three `MISSING-PHRASE ...readme-redaction.txt: ...` lines, rc 1 |

  Every fault has a named killer: 33 faults, of which P7 and P8 are controls that must pass. That gives T2 18 (P1-P8, P12-P16, P21-P25), T1 3 (P9, P17, P32), T6 10 (P10, P18, P19, P26-P31, P33), T5 1 (P11) and T3 1 (P20). The step 5 control run is a named control, not a fault.
- **Evidence commands (exact), and where the raw output is saved:**

  All evidence files go under `handover/evidence/P8b/` on branch `core/cloud-handover` (written `E/`), never in the docs pull request. Two trees are read, and each evidence file names the one it read on its first line:
  - **Core files** (T1, T4, T5, T6, the scanner and the page faults) are run with the current folder at the core checkout on branch `core/P8b`. Their first line comes from `hdr_core`:
    `hdr_core() { git fetch -q origin && git merge-base --is-ancestor origin/main HEAD && [ -z "$(git status --porcelain -- docs README.md CHANGELOG.md)" ] && printf 'base=%s head=%s\n' "$(git rev-parse origin/main)" "$(git rev-parse HEAD)" || { echo "HDR-FAIL core (not rebased on origin/main, or uncommitted page edits)"; return 1; }; }`
  - **Ledger files** (T2 and the ledger faults' control row) are run in the `core/cloud-handover` checkout. Their first line comes from `hdr_ledger`:
    `hdr_ledger() { git diff --quiet HEAD -- handover/ledger.md && printf 'ledger_branch=%s ledger_commit=%s\n' "$(git rev-parse --abbrev-ref HEAD)" "$(git rev-parse HEAD)" || { echo "HDR-FAIL ledger (uncommitted ledger edits)"; return 1; }; }`
  - Every command is written as `{ hdr_core && <command>; echo "rc=$?"; } > E/<file> 2>&1` (or `hdr_ledger`). A header failure gives a non-zero `rc`.
  - Pass needs every core file of one run to carry the same `base` and `head`. After any rebase or new commit on `core/P8b`, the core files are stale: steps 5 and 6 (and step 7 if pages changed) are re-run.
  - Before merging, the lead re-runs steps 6 and 9 at the merge commit (order 20 item 4). Those files are the ones Done counts.

  **Run order (one order, nothing else):**
  1. **Branch:** `git fetch origin && git switch -c core/P8b origin/main`, in the core checkout. Write `E/base.txt` with `hdr_core`.
  2. **Inputs, at the step 1 head, before any page exists.**
     - Generated from code, data only: `E/table-keys.txt` (the T1 one-liner) and `E/roles.txt` (the T6 body). Each is written as `{ hdr_core && uv run python -c '<body>' > E/<name>.txt; echo "rc=$?"; } > E/<name>.log 2>&1`. A failed import (for example a renamed `_UNVERIFIED`) gives a non-zero `rc` and stops the run.
     - Literal, copied from this ticket (no header): `extra-kinds.txt`, `phrases.txt`, `forbidden.txt` (`re-cased`, `caught by nothing`), `section9-list.txt`, `p8b_ledger_check.awk` (R3), `t1.sh` and `t6.sh` (R4).
     - All evidence files: `base.txt`, the inputs above with `table-keys.log` and `roles.log`, `planted-faults.txt`, `t1.txt`, `t5.txt`, `t6.txt`, `scan.txt`, `drift.md`, `drift-dispositions.md`, `ledger-check-cloud.txt`, `ledger-check.txt`.

     The bodies of the two generated inputs:
     - **T1 one-liner** (`table-keys.txt`): `from hadavin_sdk.backends.table import TABLE; print('\n'.join(sorted(TABLE)))`. There is no grep, so no other dict can match.
     - **T6 body** (`roles.txt`):
       ```
       from hadavin_sdk.backends.table import TABLE, DEFAULTS, DEV_ONLY, NOT_PROD, _UNVERIFIED
       for k in sorted(TABLE):
           for b in sorted(TABLE[k]):
               e = TABLE[k][b]
               labels = [n for n, on in (('config default', DEFAULTS.get(k) == b), ('dev only', (k, b) in DEV_ONLY), ('not for production', (k, b) in NOT_PROD), ('open standard', e.neutral), ('not yet run live', e.status == _UNVERIFIED)) if on]
               print(k, b, ';'.join(labels) or '-', sep='\t')
       ```
       The author ran this body read-only with `python3 -I` on a `git archive 4ec3616 src` copy: 31 lines, 6 config defaults, 23 not yet run live, 10 open standard, 6 `DEV_ONLY` pairs, 2 `NOT_PROD` pairs (read at `4ec3616`). Not evidence.
     - **`phrases.txt`**, literal:
       ```
       only plain copies
       secrets of 8 to 11 characters
       exact hex and base64 spellings of a secret handed to a tool
       ```
     - **`forbidden.txt`**, literal:
       ```
       re-cased
       caught by nothing
       ```
     - **`p8b_ledger_check.awk`** (R3), run-checked on mawk 1.3.4:
       ```
       BEGIN { FS="|" }
       /^\| *id *\| *package *\| *severity *\|/ { hdr++; next }
       /^\|[-:| ]+$/ && /-/ { next }
       !/^\|/ && /\|/ { bad++; printf "BAD-STRAY line %d\n", NR; next }
       /^\|/ {
         rows++
         id=$2; gsub(/ /,"",id)
         if (NF != 9 || id !~ /^[A-Za-z0-9]+(-[A-Za-z0-9]+)+$/) { bad++; printf "BAD-LAYOUT line %d id %s\n", NR, id; next }
         if (id in seen) { bad++; printf "BAD-DUP %s lines %d %d\n", id, seen[id], NR; next }
         seen[id]=NR
         sev=toupper($4); gsub(/ /,"",sev)
         st=$6; sub(/^ +/,"",st); split(st,w," "); s=toupper(w[1])
         if (sev!="BLOCKER" && sev!="MAJOR" && sev!="MINOR" && sev!="NIT") { bad++; printf "BAD-SEVERITY %s line %d\n", id, NR; next }
         if (sev!="BLOCKER" && sev!="MAJOR") next
         if (s=="FIXED-VERIFIED" || s=="WAIVED" || s=="OWNER-ONLY" || s=="IMPOSSIBLE-NOW") {
           art=$7; gsub(/ /,"",art)
           if (art=="" || art=="-") { bad++; printf "BAD-NO-ARTIFACT %s %s\n", s, id; next }
           if (s!="FIXED-VERIFIED") printf "%s %s\n", s, id
           next
         }
         open++; os[s]++; printf "UNRESOLVED %s %s\n", s, id
       }
       END {
         if (hdr != 1) { bad++; printf "BAD-HEADER count=%d\n", hdr }
         if (rows == 0) { bad++; print "NO-ROWS" }
         printf "rows=%d bad=%d unresolved_blocker_major=%d\n", rows, bad+0, open+0
         for (k in os) printf "  status %s: %d\n", k, os[k]
         exit (bad+open > 0) ? 1 : 0
       }
       ```
       A line that holds a pipe but does not start with one (indented, quoted or tab-indented) is `BAD-STRAY`. Prose headings and blank lines are allowed. A separator must contain `-`, so an all-blank row is read as a row and fails as `BAD-LAYOUT`. All four closed statuses need a non-empty artifact cell other than `-`. Also: every table row is read; an id that does not parse is BAD-LAYOUT; a row with a cell count other than 7 is BAD-LAYOUT; a MINOR or NIT row never blocks. The pattern of the waiver id in a WAIVED row's artifact cell stays a manual check by the lead, because the P0d format is not visible here.
     - **`t1.sh`** (R4). Both scripts are POSIX `sh`, read their inputs from `$E`, use relative page paths, and are run with the current folder at the tree under test (the real checkout or the scratch copy). Run-checked on dash.
       ```
       E="${E:?set E to the evidence folder}"
       t="$(mktemp -d)"
       sort -u "$E/table-keys.txt" > "$t/k"
       sort -u "$E/extra-kinds.txt" > "$t/x"
       sort -u "$t/k" "$t/x" > "$t/want"
       ls docs/kinds | grep -v '^README\.md$' | sed 's/\.md$//' | sort -u > "$t/have"
       { comm -12 "$t/k" "$t/x" | sed 's/^/IN-BOTH /'
         comm -3 "$t/want" "$t/have" | sed 's/^/SET-DIFF /'
         [ -f docs/kinds/README.md ] || echo "NO-INDEX"; } > "$t/out"
       cat "$t/out"
       if [ -s "$t/out" ]; then rm -rf "$t"; echo "t1_fail=1"; exit 1; fi
       rm -rf "$t"; echo "t1_fail=0"; exit 0
       ```
     - **`t6.sh`** (R4):
       ```
       E="${E:?set E to the evidence folder}"
       fail=0
       tab="$(printf '\t')"
       t="$(mktemp -d)"
       # (a) labels of every Backends row, and the positive and negative "production choice" rule
       while IFS="$tab" read -r kind be labels; do
         page="docs/kinds/$kind.md"
         row=$(grep -E "^\| *\`$be\` *\|" "$page")
         if [ -z "$row" ]; then echo "NO-ROW $kind $be"; fail=1; continue; fi
         for want in "config default" "dev only" "not for production" "open standard" "not yet run live"; do
           case ";$labels;" in *";$want;"*) code=1 ;; *) code=0 ;; esac
           case "$row" in *"$want"*) page_has=1 ;; *) page_has=0 ;; esac
           if [ "$code" != "$page_has" ]; then echo "WRONG-LABEL $kind $be '$want' code=$code page=$page_has"; fail=1; fi
         done
         case ";$labels;" in
           *";dev only;"*|*";not for production;"*)
             case "$row" in *"production choice"*) echo "BAD-PROD-CHOICE $kind $be"; fail=1 ;; esac ;;
           *)
             case "$row" in *"production choice"*) ;; *) echo "MISSING-PROD-CHOICE $kind $be"; fail=1 ;; esac ;;
         esac
       done < "$E/roles.txt"
       # (b) every page: the 8 headings as exact lines, at most 60 lines
       cat "$E/table-keys.txt" "$E/extra-kinds.txt" | sort -u > "$t/pages"
       while read -r k; do
         page="docs/kinds/$k.md"
         [ -f "$page" ] || { echo "NO-PAGE $k"; fail=1; continue; }
         for h in "## What it does" "## Interface" "## Backends" "## Single dependency" "## Identity and rights" "## Configuration keys" "## Tests that cover it" "## What it does not do"; do
           grep -qxF "$h" "$page" || { echo "MISSING-HEADING $k: $h"; fail=1; }
         done
         n=$(wc -l < "$page"); [ "$n" -le 60 ] || { echo "TOO-LONG $k $n"; fail=1; }
       done < "$t/pages"
       # (c) the seven non-table pages: the not-a-kind line above heading 1
       while read -r k; do
         awk '/^## /{exit} /is not a kind in the backend table/{f=1} END{exit !f}' "docs/kinds/$k.md" || { echo "MISSING-NOT-A-KIND $k"; fail=1; }
       done < "$E/extra-kinds.txt"
       # (d) fixed sentences: no default, the two cross links, the two A6 outlines under heading 4
       for k in audit llm; do
         grep -qF "no default; config must name one" "docs/kinds/$k.md" || { echo "MISSING-NO-DEFAULT $k"; fail=1; }
       done
       grep -qF "not the same as [detector](detector.md)" docs/kinds/redactor.md || { echo "MISSING-LINK redactor"; fail=1; }
       grep -qF "not the same as [redactor](redactor.md)" docs/kinds/detector.md || { echo "MISSING-LINK detector"; fail=1; }
       sec4() { awk '/^## Single dependency$/{p=1; next} /^## /{p=0} p' "$1"; }
       sec4 docs/kinds/channel.md | grep -qF "second channel = email; trigger: a client needs email approvals" || { echo "MISSING-OUTLINE channel"; fail=1; }
       sec4 docs/kinds/executor.md | grep -qF "per-contract none/manual/http; http refused in pilot and prod; manual not built" || { echo "MISSING-OUTLINE executor"; fail=1; }
       # (e) redactor wording: required phrases (each on one line) and retracted wordings
       awk '/Redaction is pattern-based and bounded/ {p=1} p && /^$/ {exit} p' README.md > "$t/readme-redaction.txt"
       [ -s "$t/readme-redaction.txt" ] || { echo "NO-README-PARAGRAPH"; fail=1; }
       for f in docs/kinds/redactor.md "$t/readme-redaction.txt"; do
         while IFS= read -r phrase; do
           grep -qiF -- "$phrase" "$f" || { echo "MISSING-PHRASE $f: $phrase"; fail=1; }
         done < "$E/phrases.txt"
       done
       for f in docs/kinds/*.md "$t/readme-redaction.txt"; do
         while IFS= read -r bad; do
           grep -qiF -- "$bad" "$f" && { echo "FORBIDDEN-PHRASE $f: $bad"; fail=1; }
         done < "$E/forbidden.txt"
       done
       rm -rf "$t"
       echo "t6_fail=$fail"
       exit "$fail"
       ```
  3. **Ledger faults** P1 to P8, P12 to P16 and P21 to P25. Each fault is a scratch file `"$S/<fault>.md"` with `S=$(mktemp -d)`, run as `awk -f E/p8b_ledger_check.awk "$S/<fault>.md"`. One line per fault (fault id, rc, first printed line) goes to `E/planted-faults.txt`.
  4. **Write the 15 pages, the index, the README paragraph and the CHANGELOG line**, and commit them on `core/P8b`.
  5. **Control run, then the page faults, in a scratch copy.** `S=$(mktemp -d); cp -R docs README.md "$S/"`.
     - Control first: `(cd "$S" && E="$E" sh "$E/t1.sh" && E="$E" sh "$E/t6.sh")` must give rc 0. If it does not, the pages are fixed before any fault run.
     - Then each fault of the T1 and T6 rows (P9, P10, P17 to P19, P26 to P33), each on a fresh copy, with the same command. P17 and P32 edit a scratch copy of `table-keys.txt` and point `E` at a scratch input folder.
     - P11: the T5 loop of step 6 on a scratch copy of `section9-list.txt`.
     - Results go to `E/planted-faults.txt`.
  6. **Real checks in the core checkout:** `t1.txt` (`E="$E" sh "$E/t1.sh"`), `t5.txt` (the T5 loop), `t6.txt` (`E="$E" sh "$E/t6.sh"`) and `scan.txt` (`python tools/scan_repo.py`). Each uses the `hdr_core` form.
     - **The T5 loop:** for each line `p` of `section9-list.txt`, `git ls-files "$p"` at the docs PR head; an empty result prints `MISSING $p`. Pass: no `MISSING` line, or each `MISSING` line followed by the replacement name the lead accepted.
     - Pass for `t1.txt` and `t6.txt`: `t1_fail=0`, `t6_fail=0` and `rc=0`. Pass for `scan.txt`: `rc=0`.
  7. **T4 drift** (R6). After any page fix: commit, then re-run steps 5 (control only) and 6.

     **T4, the drift report.** Run in the core checkout at the step 1 head. The lead or the cloud (PENDING LEAD 8) invokes `egm:egm-drift-report` through the Skill tool on `docs/kinds/`, and saves the output as `E/drift.md`.
     - Each bullet in it gets one row in `E/drift-dispositions.md`: `| page | bullet (quoted) | FIXED <commit> | LEDGER <row id> | NOT-DRIFT <reason> |`. NOT-DRIFT is allowed only for "logic not described by the page" outside the 8 headings, and the lead checks each one.
     - **Open drift** = a bullet without a row. Pass: every `## ` section says "No drift detected", or every bullet has a row.
     - Frozen tickets and plan-v3 are not in scope, so the INFO route is deleted.
     - The plan row 188 run on the studio repo stays the lead's (PENDING LEAD 9).
  8. **Draft pull request and its review.** The reviewer reads the diff, this ticket and the evidence of steps 1-7. One fix batch, then a re-run of steps 5 (control) and 6 (and 7 if a page changed). The lead then closes P8b's own ledger rows, citing the fixing commit.
  9. **Ledger checks last:** P20, then T2 (`{ hdr_ledger && awk -f E/p8b_ledger_check.awk handover/ledger.md; echo "rc=$?"; } > E/ledger-check-cloud.txt 2>&1`), then T3 as revision 2 wrote it (lead, laptop). Revision 2's text, kept:
     - T2 pass: `rc=0`, `bad=0`, `unresolved_blocker_major=0`.
     - T3 (plan-v3 section 9, row "No unresolved findings", `plan-v3.md:185`), run after the lead has copied the cloud rows into the laptop ledger (`plan-v3.md:54`): `python egm/tools/ledger_check.py --topic core` and `python egm/tools/ledger_lint.py`, both written to `E/ledger-check.txt` in the same form. Pass: both `rc=0`, with WAIVED rows listed by id.
     - **Count check:** the number of BLOCKER and MAJOR rows the lead copied to the laptop ledger equals the number of BLOCKER and MAJOR rows in the cloud check. Both numbers are written in `E/ledger-check.txt`. The source of the laptop count is UNVERIFIED until the tool is seen.
     - The laptop check expects 9 columns while the cloud ledger has 7, so the copy step maps the columns (`inventory-A.md:10`; not re-read by this author, UNVERIFIED).
- **Reviewers: correctness + adversarial (fresh agents; they get the diff, this ticket and the evidence only):** order 20 item 6: at most 3 rounds counting from round 1. This revision answers round 2, and round 3 is the last. For the built docs pull request (step 8): one fresh `egm:*` reviewer (`egm-codebase-details`, which checks every page claim against its `file:line` at the `base` commit), one round, at most 2 fix batches (Tier B, order 6(b), `LEAD-ORDERS.md:19`).
- **Done =** all of the following:
  1. The dependencies are met: P8a merged, the ledger close-out finished (PENDING LEAD 5), the cloud rows normalised (PENDING LEAD 6), and the freeze and build-start review done.
  2. T1, T2, T3, T5 and T6 pass with one `base`/`head` pair on every core file and one `ledger_commit` on every ledger file, from the final run (the lead's run at the merge commit). T4's `drift.md` shows no open drift in `docs/kinds/`. That means:
     - one page per name of the T1 set, derived at run time, and the pages match the code's key set;
     - every Backends label matches the code, and every page has its 8 headings;
     - the redactor phrases are present and no forbidden phrase is;
     - every section 9 path exists, or its correction was sent to the lead;
     - the scanner exits 0;
     - the cloud check exits 0;
     - both laptop tools exit 0, with matching counts.
  3. P1 to P33 behave as in the table, and the step 5 control passes.
  4. **P8b's own rows** (its ticket review rows and the docs pull request's review rows) are closed by the lead before the final step 9 run (step 8). Each cites the revision or the pull request commit that fixed it. Drift items that became ledger rows in step 7 are closed by the package that owns the code; until they are, P8b is not done.
  5. The docs pull request is green on every gate: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit, and the CI secret-and-name scan.

  **Honest note:** if the ledger close-out has not happened, step 9 fails, and that is the intended stop, not a bug. Most unresolved rows come from ticket-paper reviews whose fixes landed in later ticket revisions, but no row was moved to FIXED-VERIFIED. P8b cannot close those rows: only the package that built a fix can verify it (PENDING LEAD 5). Every new 5-cell row written by a cloud session also makes T2 fail with `BAD-LAYOUT` until PENDING LEAD 6 is done, and the R3 artifact rule makes any FIXED-VERIFIED row without an artifact fail too.
- **Rollback:** the lead tags `pre-P8b` before the merge (plan-v3 section 10). The change is docs only and is undone with a revert pull request. There is no migration and no semantic change.

## PENDING LEAD
1. **README location:** `docs/kinds/<kind>.md` plus an index (recommended; `docs/` already exists in core, and R1 needs the pages in one PR branch), or `README.md` inside each kind's source folder (rejected above: single-module kinds share folders).
2. **Kind set:** the T1 set derived at run time, read at `4ec3616` the 15 of Interface item 1 (recommended; each non-table page says so in one line under its title), or only the `TABLE` keys.
3. **CLOSED by A6** (`amendments.md:9`; A14(6) lets an amendment answer a pending item). The channel outline is "second channel = email; trigger: a client needs email approvals", and it is written in `channel.md` heading 4.
4. **SPLIT into items 5 and 6.**
5. **Who closes the ledger before P8b.**
   - Option (a): each package's result review closes its own rows (FIXED-VERIFIED with the frozen revision and the build evidence, or WAIVED by the owner), and the lead runs one close-out pass before P8b starts.
   - Option (b): P8b closes them.
   - Recommend (a): only the package that built the fix can verify it, and (b) would make a docs package judge code. Reversible.
6. **INFORM: the cloud normalises its own 5-cell rows now.** Read at `ea6402f`, 268 rows use the layout `id | severity | package | summary | status` (178 at revision 2's read, 262 at the round 2 resolve's; the newest row, `R3-P5a-COR-1`, is still in 5 cells).
   - The cloud session rewrites them into the 7-column layout of the ledger header (`id | package | severity | summary | status | verifying artifact | reviewed commit`), with the severity in capitals.
   - The `Major/Minor` rows are decided from their review files.
   - Duplicate ids are renamed with the suffix `-b`, and both review files are cited.
   - "(build notes via resolve)" moves from the status cell to the artifact cell.
   - Every new row is written in 7 columns from then on.
   - The lead spot-checks every rewritten severity against its review file before the T2 run.

   This is a file under `handover/` (allowed by the orders), not a status change. Recommend: yes, as one cloud commit, then run the new awk and save its output; it should then report `bad=0`. Reversible (one commit).
7. **The new awk as the cloud's own check.** Optional: the cloud runs `p8b_ledger_check.awk` after each ledger write and fails its own step on any `BAD-*` line. This now includes the R3 artifact rule: a session that writes FIXED-VERIFIED (or WAIVED, OWNER-ONLY, IMPOSSIBLE-NOW) without an artifact fails its own step. Recommend yes: it costs one command and keeps item 6 from slipping back (the 5-cell count rose from 178 to 268 between revision 2 and this revision). No repo change.
8. **Who writes the pages and who runs the checks** (sent to the lead as NEEDS LEAD 42). Order 6(c) (`LEAD-ORDERS.md:19`) says the lead runs P8 packages. Order 21 item 17 (`:88`) gives P8 packages the standing S0 EXIT, which under order 20 item 4 means the cloud builds on `core/<package>` and opens a draft PR.
   - Option (a): the cloud writes the pages and runs steps 1-8 and T2. The lead runs P20 and T3 on the laptop and re-runs steps 6 and 9 at the merge commit.
   - Option (b): the lead does everything.
   - Recommend (a): the later order wins, and the laptop steps stay with the lead. Reversible.
   - **Working assumption of this revision: option (a)**, written as an assumption, not yet executed. The lead may switch to (b); then every step runs as written, with "the lead" as the runner, and no other text changes.
9. **The drift gate is narrower than plan row 188** (sent to the lead as INFORM 43). The row says "studio repo: `egm:egm-drift-report`, no open drift". P8b runs it on core `docs/kinds/` with the dispositions table (R6).
   - Option (a): accept the narrow P8b run, and keep the studio-repo run as the lead's final section 9 check (plan-v3 section 3, `plan-v3.md:52`: "the final checks of section 9" are the lead's).
   - Option (b): P8b must make the whole studio repo drift-free.
   - Recommend (a): the cloud cannot see the studio repo, and SKILL.md counts any logic not described in a doc as drift, so (b) has no reachable end for a docs package. The lead edits row 188's command column to name both runs. Reversible.

## UNVERIFIED
- `ledger_check.py` and `ledger_lint.py`: their behaviour, arguments and laptop-count output (studio repo, not visible here), and so P20's exact result.
- The P0d WAIVED format and the waiver-id pattern (a manual check by the lead).
- `inventory-A.md:10` (the 9-column versus 7-column claim; not re-read).
- Whether `uv_build` ships non-Python files in the package (moot while the pages sit in `docs/`).
- The live status of the 23 of 31 entries marked `_UNVERIFIED` (read at `4ec3616`); the other 8 are not marked.
- The final redactor wording in the merged P1, P2d and P5c tickets. `phrases.txt` and `forbidden.txt` follow P1 revision 16 (`P1.md:20`) and orders 15 and 19 C.
- The output of `egm:egm-drift-report` (an LLM skill; not deterministic; not run by this author).
- The awk and `sh` text on gawk or busybox (run on mawk 1.3.4 and dash only).
- `uv run` of the two Python bodies (the author ran them with plain `python3 -I` on a `git archive 4ec3616` copy, not through `uv`).
- The behaviour of `tools/scan_repo.py` on the new pages (it exists at `4ec3616` and CI runs it; not run by this author).
- `hdr_core` and `hdr_ledger` (copied word for word from the resolve; not run by this author).
- The T5 loop on the docs PR head (`git ls-files` glob pathspecs were checked on the handover branch, not on `core/P8b`); P11 not run.

## Build notes (round 3 resolve; these win over the text above)

**BN-1. Two checkouts, one absolute `E`.** The runner uses two worktrees of the core repo. `<core>` is the core checkout on branch `core/P8b`, where the pages are written and every core file is run. `<ledger>` is the checkout on branch `core/cloud-handover`, which holds the evidence folder and `handover/ledger.md`. Before step 1, in the one shell that runs every step, the runner runs the BN-1 block below. That block makes `E` absolute or stops. Every `E/<file>` in this ticket means `"$E/<file>"`, in redirects and in `awk -f` too. Core commands run with the current folder at `<core>`. Step 3 runs as `awk -f "$E/p8b_ledger_check.awk" "$S/<fault>.md"`. Step 9's T2 runs as the second line of the BN-1 block. The runner commits the evidence on `core/cloud-handover` in `<ledger>` (`git add handover/evidence/P8b` and then `git commit`), never on `core/P8b`. It commits after step 9, and earlier whenever the lead must see a step's files. Committing evidence does not make a ledger file stale. `hdr_ledger` records the commit whose `handover/ledger.md` it read, and it refuses only uncommitted ledger edits.

**BN-2. One head per run.** A run is the set of core files written at one `head` of `core/P8b`: `base.txt`, `table-keys.log`, `roles.log`, `t1.txt`, `t5.txt`, `t6.txt` and `scan.txt`. Step 2 writes the generated inputs first, at the step 1 head, and the page writer uses that `roles.txt`. Later heads are: after step 4, after each fix commit, after each rebase, and the lead's merge-commit run. At each of them, before steps 5 and 6, the runner writes `base.txt`, `table-keys.txt`/`.log` and `roles.txt`/`.log` again with the same commands. The new files replace the old ones (the git history of `core/cloud-handover` keeps the old ones). The literal inputs are not written again. Pass needs every file of the run to carry the same `base` and `head`. Each step 5 block in `planted-faults.txt` starts with one `hdr_core` line. `drift.md` follows BN-3, not this rule. This replaces the revision 3 bullet "Pass needs every core file of one run to carry the same `base` and `head`" and Done item 2's "with one `base`/`head` pair on every core file". The new Done wording is "with one `base`/`head` pair on every file of the final run (BN-2), `drift.md` under BN-3".

**BN-3. T4 runs at the pages head.** Replace "Run in the core checkout at the step 1 head" with: run in `<core>` at the head of `core/P8b` after step 4, and again after every commit that changes `docs/kinds/`. The runner first writes `hdr_core > "$E/drift.md"` and then appends the skill output, so line 1 of `drift.md` names its `head`. Done rule: at the head of the final run, and at the merge commit, `git diff --quiet <drift.md head> HEAD -- docs/kinds src` exits 0. If it does not, T4 is run again. A rebase that changes neither the pages nor `src/` keeps the old `drift.md`. Per order 24 item 42, the cloud runs T4 (see BN-17).

**BN-4. The two generated inputs run from files.** The T1 one-liner and the T6 body become the literal files `table_keys.py` (that one line) and `roles.py` (the body as written), copied from this ticket into `$E` like the other literal blocks. Both are added to the step 2 literal list and to "All evidence files". Each is run with the current folder at `<core>` as `{ hdr_core && uv run python "$E/table_keys.py" > "$E/table-keys.txt"; echo "rc=$?"; } > "$E/table-keys.log" 2>&1`, and the same with `roles.py`, `roles.txt` and `roles.log`. The form `uv run python -c '<body>'` is withdrawn, because both bodies hold single quotes. Resolver check, with a stub for `uv run python` on dash: the `-c` form gives `NameError: name 'n' is not defined` (T1, rc 1) and `: not found` (T6, rc 127). The file form gives rc 0, 8 keys and 31 lines. `uv run` itself was not run (UNVERIFIED).

**BN-5. The README paragraph is one bullet.** In `t6.sh`, replace the `awk '/Redaction is pattern-based and bounded/ {p=1} p && /^$/ {exit} p' ...` line with the BN-5 block below. The README "paragraph" is the bullet that holds those words plus its continuation lines, up to the next bullet, blank line or heading. In Interface item 3, read "paragraph" as "bullet". The rewritten README keeps the redaction text as one bullet, with each required phrase inside it. **New fault P34:** a scratch copy whose `README.md` redaction bullet loses "only plain copies" while the next bullet gains it. P34 is killed by T6 (e). Expected: `MISSING-PHRASE <tmp>/readme-redaction.txt: only plain copies`, rc 1. Resolver check at `4ec3616` (mawk 1.3.4): the old line cuts 12 lines (31-42), and the new line cuts line 31 only.

**BN-6. P8a cites.** Depends on, item 1, reads: "P8a, merged, built from its frozen revision (revision 2 or later; P8a is not in `freeze-list.md` yet)". It has no sha. In Interface item 4, the "Demos re-pinned" correction is P8a item 8 (`P8a.md:174`). The corrected row names the command as `P8a.md:123` writes it (R4): `python <studio>/tools/core_sync_check.py --core <core checkout> --demo <dir>` (with `--demo` repeated once per demo) `--strict-pin --json`. The cite `P8a.md:78` and the sha `db09637` (in the revision 1 to 2 CHANGELOG) are history, not cites.

**BN-7. The outlines are A6 paraphrased.** Read every "A6 words" in Interface item 4 and in PENDING LEAD 3 as "A6 paraphrased (`amendments.md:9`)". A6 reads "second channel = email, trigger: a client needs email approvals" and "per-contract none/manual/http; http refused in pilot/prod, manual unbuilt". The page strings and the T6 (d) greps stay as revision 3 writes them (`;`, "pilot and prod", "manual not built"). The content is the same, the words are plainer, and the pages and the greps agree.

**BN-8. One T5 rule.** Delete "`tests/test_redact*.py` is the one known mismatch: the replacement name comes from the P2d ticket". Frozen P2d creates `tests/test_redact_fold.py`, `_fold_budget`, `_fold_property` and `_fold_seams` (`P2d.md:101`), and `tests/test_redact_lookalike.py`, `_lookalike_fr` and `tests/test_redact_hidden.py` (`P2d.md:288`). The glob matches them, so no mismatch is known. The rule, in step 6 and in Done item 2: **T5 passes when `t5.txt` has no `MISSING` line.** If a path is missing, the runner looks up the real name in the owning package's merged files. It writes `| old path | new path | owning ticket file:line |` into `E/t5-corrections.md`, changes that line in `E/section9-list.txt`, sends the rows to the lead (the lead edits `plan-v3.md`) and runs T5 again. Done item 2's "or its correction was sent to the lead" becomes "every path of `E/section9-list.txt` exists, and each line changed from this ticket's block has a row in `E/t5-corrections.md` that was sent to the lead". The lead's acceptance is not part of pass.

**BN-9. P33 command.** P33 runs on a fresh scratch copy made as in step 5, followed by `git show origin/main:README.md > "$S/README.md"`, run in `<core>` (`origin/main` is the run's `base`). Expected: rc 1 with at least the three `MISSING-PHRASE ...readme-redaction.txt: ...` lines. Resolver check at `4ec3616` with the BN-5 cut: line 31 holds no required phrase and no forbidden phrase, so it prints exactly those three lines and no `FORBIDDEN-PHRASE`.

**BN-10. Fixed-string row match.** In `t6.sh` (a), the row match becomes `` row=$(grep -F "| \`$be\` |" "$page") ``. Every Backends row is written with single spaces, as Interface item 3 gives it: `` | `<backend>` | <labels> | <module> | ``. A row with other spacing prints `NO-ROW` (fail closed). Today no name holds a regex character: all 31 names match `^[a-z0-9_]+$`, read at `4ec3616`. But a later name with `.` could have matched a second row and passed on that row's labels.

**BN-11. Two `comm` calls in `t1.sh`.** Replace the `comm -3 ... SET-DIFF` line with the BN-11 block below. The P9 expected line becomes `MISSING-PAGE channel`, and the P17 line becomes `MISSING-PAGE fakekind`. T1's pass text reads "no `IN-BOTH`, `MISSING-PAGE`, `EXTRA-PAGE` or `NO-INDEX` line". Resolver check on dash, with scratch empty pages: the control gives `t1_fail=0`, rc 0. P9 gives `MISSING-PAGE channel`, rc 1. An extra page gives `EXTRA-PAGE extra`, rc 1. Deleting the index gives `NO-INDEX`, rc 1.

**BN-12. Fault coverage.** New faults: **P35**: delete `docs/kinds/README.md`. T1 kills it, with `NO-INDEX`, rc 1. **P36**: delete the line "no default; config must name one" from `llm.md`. T6 (d) kills it, with `MISSING-NO-DEFAULT llm`, rc 1. **P37**: delete the `not the same as [redactor](redactor.md)` line from `detector.md`. T6 (d) kills it, with `MISSING-LINK detector`, rc 1. **P38**: move the channel outline from heading 4 to the end of `channel.md`. T6 (d) kills it, with `MISSING-OUTLINE channel`, rc 1. P34 is in BN-5. The Tests field claim reads: "Every check except T4 and the T3 count check has at least one planted fault. These output lines have no fault of their own: `MISSING-NO-DEFAULT audit` and `MISSING-LINK redactor` (the same code as P36 and P37), `BAD-PROD-CHOICE` on a `NOT_PROD` row (the same `case` arm as P10), `EXTRA-PAGE` (resolver scratch run only), and `NO-ROW`, `NO-PAGE` and `NO-README-PARAGRAPH` (each fails closed through another line: `WRONG-LABEL` or `MISSING-PROD-CHOICE`, `MISSING-PAGE`, `MISSING-PHRASE`)." The count becomes 38 faults: T2 18, T1 4 (P9, P17, P32, P35), T6 14 (P10, P18, P19, P26-P31, P33, P34, P36-P38), T5 1, T3 1. Done item 3 reads "P1 to P38".

**BN-13.** Depends on, item 2, adds: "P8b's own rows are exempt only until step 8. They are closed before the final step 9 run (Done item 4), or T2 fails." Read now, the ledger has 36 `R*-P8b-*` rows, 29 of them in 5 cells. Those 29 fail `BAD-LAYOUT` until PENDING LEAD 6 is done.

**BN-14.** After the awk block, add: "`NF` counts the empty field before the first `|` and the one after the last, so a row of 7 cells has `NF == 9`."

**BN-15.** T6 (e) reads: "no file in `docs/kinds/` (the index `README.md` included) and not the README bullet contains a phrase of `forbidden.txt`".

**BN-16.** The gloss of R1 to R7 is in the banner: they are the replacement texts of `handover/reviews/P8b-round2-resolve.md`.

**BN-17.** PENDING LEAD 8 is answered by order 24 item 42 (`LEAD-ORDERS.md:126`), option (a). The cloud writes the pages and runs steps 1 to 8 and T2. The lead runs P20 and T3 on the laptop and does the merge-commit re-run (steps 2 generated part, 6 and 9, plus the BN-3 diff check). The "working assumption" wording is void.

**BN-1 block** (run once, in the shell that runs every step; `<ledger>` is the absolute path of the `core/cloud-handover` checkout):
```
export E="$(cd <ledger> && pwd)/handover/evidence/P8b"; mkdir -p "$E"; case "$E" in /*) ;; *) echo "E-NOT-ABSOLUTE"; exit 1 ;; esac
( cd <ledger> && { hdr_ledger && awk -f "$E/p8b_ledger_check.awk" handover/ledger.md; echo "rc=$?"; } > "$E/ledger-check-cloud.txt" 2>&1 )
```
The second line is step 9's T2, and it replaces the step 9 command of revision 3.

**BN-5 block** (replaces the first line under `# (e)` in `t6.sh`):
```
awk '/Redaction is pattern-based and bounded/ {p=1; print; next} p && (/^$/ || /^- / || /^#/) {exit} p' README.md > "$t/readme-redaction.txt"
```

**BN-11 block** (replaces `comm -3 "$t/want" "$t/have" | sed 's/^/SET-DIFF /'` in `t1.sh`):
```
  comm -23 "$t/want" "$t/have" | sed 's/^/MISSING-PAGE /'
  comm -13 "$t/want" "$t/have" | sed 's/^/EXTRA-PAGE /'
```

## Build note after the freeze (lead order 53 item 2, genericity audit; continues the BN numbering above)

**BN-18 (genericity audit finding G-11, lead order 53).** The drift report flags the word "incident" in core docstrings outside an ops-pack module (`defaults.py:32` "the largest incident document a run takes"; `runtime/evidence.py:6`; `sources/__init__.py:1`). The wording becomes "the run's input document". Report only; P8b edits no source.
Build note only; the freeze is not reopened.

**BN-19 (genericity audit finding G-15, lead order 53; rename part).** Ledger row: move `tests/warden_port/` to `tests/ported/` in one rename-only pull request with `git mv` (no test deleted, no test edited); the layout lines that name `tests/warden_port/` (lines 130 and 145) then read `tests/ported/` once that pull request merges. The k1b test names (`tests/test_k1b_*.py`, `tests/k1b_support.py`) follow AK4a BN-20.
Build note only; the freeze is not reopened.
