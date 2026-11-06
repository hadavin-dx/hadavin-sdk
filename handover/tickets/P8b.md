# Package ticket P8b: one README per kind, the drift report and the ledger check. DRAFT revision 2

Revision 2 written 2026-11-06 about 03:00 UTC (08:30 IST; IST = UTC+5:30) by the ticket revision author from `handover/reviews/P8b-round1-resolve.md` (24 decision rows: 23 PROPOSE FIX, each applied as decided below; 1 CONTEST, ADV-18, kept as revision 1 had it). Revision 1 was written 2026-11-06 about 02:45 UTC (08:15 IST), commit `0d04aa3`. Text only: no code, no suite run, no pull request. **Where the code facts were read (revision 2):** the worktree `src/` at branch head `601be32`, after checking with `git diff --quiet origin/main -- <file>` (origin/main = `397ec97` at that moment) that every file cited below is identical to `origin/main`, except `guard/redact.py` (a one-line change elsewhere in the file; the two cited lines `:862` and `:1244` are the same on both). `guard/http.py`, `guard/runmap.py` and `tools.py` also differ, and none of them is cited for a line. Ledger facts are "read at commit `<sha>`" and are never "today's" (the ledger grows while sessions work). Anything not read is marked UNVERIFIED. "PENDING LEAD" means the author proposes it and no lead decision exists yet. Tier B: one fresh reviewer, one round, at most 2 fix batches (order 6(b), `LEAD-ORDERS.md:19`). Per order 6(c), the lead runs everything in this ticket; this text gives the commands, the pass criteria and the evidence files.

## CHANGELOG (revision 1 to revision 2)
- **Ledger check script replaced** (ADV-1 = COR-1, ADV-2, ADV-11 = COR-10, ADV-19). The old row filter `/^\| *[A-Z][A-Z]-/` skipped every id with a digit or three letters in its prefix (`R1-`, `R2-`), including this ticket's own OPEN Blocker review rows. The new script, `handover/evidence/P8b/p8b_ledger_check.awk`, reads every table row except the one header and the separator lines. It requires exactly one header and at least one row, and it flags a bad layout, a bad id, a duplicate id and a waiver row with an empty artifact cell. It prints the id on every message. The sentence "a new prefix is checked, not skipped" is deleted. New planted faults: P12 to P16, P21 and P22.
- **Drift scope cut to `docs/kinds/`** (ADV-3 = COR-5). Frozen tickets and plan-v3 are inputs only. A ticket claim the code proves false is one INFO line in `drift.md`, never blocking, and the ticket is not edited. The root `README.md` redaction paragraph is checked by the new deterministic T6, not by the LLM skill, and it is added to the Files field.
- **Ledger close-out moved into "Depends on"** (ADV-4 = COR-4). Its owner is PENDING LEAD 5. Done says who closes P8b's own rows and the rows that drift creates. The hard figures in the Honest note are gone (COR-2).
- **Every ledger figure is now "read at commit `<sha>`"** (COR-2). The fail-before has no exact count string, and the `BS-*` block is not cited by line numbers.
- **P8a is written** (ADV-12 = COR-3): P8a ticket revision 1 (draft, `db09637`). P8a item 8 (`P8a.md:78`) is taken into Interface item 4: P8b sends the corrected section 9 row "Demos re-pinned".
- **The Backends roles are defined from code** (ADV-5 = COR-6): config default, dev only, not for production, open standard, production choice. The glossary example is fixed, and the detector config is a list. New fault P19.
- **Redactor and detector settled from code** (ADV-6 = COR-7): they are different parts with different jobs. The item is removed from UNVERIFIED.
- **Channel and executor outlines use A6's words** and are written into `channel.md` and `executor.md` themselves (COR-8). PENDING LEAD 3 is CLOSED by A6.
- **The README set check is derived from code** (ADV-7). `table-keys.txt` comes from importing `TABLE`, `extra-kinds.txt` is a literal block in this ticket, and `comm` compares them with `ls docs/kinds`. `expected.txt` is gone. New fault P17.
- **New check T6, deterministic page checks** (ADV-8): roles in each Backends row, plus the redactor phrases in `redactor.md` and in the root README paragraph. P10 moves from T4 to T6. New faults P18 and P19, and P20 for the laptop tools. T4 (the LLM report) has no planted fault, and the ticket now says so.
- **One numbered run order** (ADV-9). There is no normalisation step any more: the cloud normalises its own rows (PENDING LEAD 6, ADV-15).
- **Every evidence command has the same form**, `{ git rev-parse origin/main; <command>; echo "rc=$?"; } > <file> 2>&1` (ADV-10 = COR-9).
- Smaller fixes, each applied as decided:
  - ids P1 (P1m, P1a, P1b) and P6b1, P6b2 (ADV-13);
  - the exact section 9 path block, with two items flagged in advance (ADV-14);
  - a laptop-count equality check (ADV-16);
  - glossary entries for plan-v3, memo 6, A6 and the ledger prefixes (ADV-17);
  - the label "allowed only in `dev`" (COR-11);
  - "23 of 31" (COR-12);
  - where the not-a-kind line sits, and "at most 60 lines" (COR-13).
- **Kept by CONTEST (ADV-18):** the "not yet run live" tag stays per row. Within one kind the status differs: detector `regex` (`table.py:544`) has no `status`, and `llm_judge` (`table.py:546-548`) has `status=_UNVERIFIED`.
- **New PENDING LEAD items:** 5 (who closes the ledger before P8b), 6 (INFORM: the cloud normalises its own 5-cell rows) and 7 (the new awk as the cloud's own check after each ledger write). Item 3 is closed and item 4 is split into 5 and 6.
- **The author's own corrections to the resolve file**, each checked by me:
  - `guard/__init__.py:3` exports `redact` only. `redact_many` (`guard/redact.py:1244`) is not exported there.
  - `guard/redact.py` also differs from `origin/main` (see the header).
  - The secrets `env` entry carries `status=_UNVERIFIED`, so it is both dev only and not yet run live.

## Words used in this ticket
- **kind**: one replaceable part of the core behind a fixed interface, with a default and an alternative (or a written outline with the event that would make us build it, called its **trigger**). Example: the `store` kind. Its **config default** (what the core uses when the config names nothing) is `memory`, which is dev only; its production backend is Postgres.
- **kind README** (or **page**): one short plain-word page per kind, saying what the kind does, which backends exist, what role each plays, and what it does not do.
- **drift**: a sentence in a document that no longer matches the code (for example, a page that names a default the code does not use). **Drift report**: the output of the `egm:egm-drift-report` skill. It is an LLM skill (a model writes it), so its output is not the same on every run.
- **ledger**: the table of review findings. It is `handover/ledger.md` in the cloud and `egm/BLOCKER-LEDGER.md` on the laptop (plan-v3 line 26). **Unresolved**: a BLOCKER or MAJOR row whose status is anything except FIXED-VERIFIED, WAIVED, OWNER-ONLY or IMPOSSIBLE-NOW.
- **ledger id prefixes**: `BL-` rows from the lead; `BS-` rows from build-start reviews; `R1-` and `R2-` rows from ticket reviews of round 1 and round 2.
- **plan-v3**: the core plan, `studio-notes/plan-v3.md`. **memo 6**: the lead's check of plan-v3's claims against the code (`studio-notes/memos/memo-6-kernel-and-claims.md`). **A6**: amendment 6 in `studio-notes/amendments.md:9`. An amendment wins over plan-v3.
- **planted fault**: a deliberate error put into a throwaway copy of an input, to prove that a check catches it. Here it plays the part a code mutant plays in a code package.

## Template fields in the template's order

- **Package id and name:** P8b, "One README per kind, the drift report and the ledger check" (plan-v3 row, `studio-notes/plan-v3.md:113`). It is one docs pull request to core (the pages, and the root README paragraph only if T6 fails on it), plus checks the lead runs. Step S5, milestone v1, consumers: none.
- **Path class:** other. **Extended review (no round cap): no.** It is not a money, redaction or security path, because P8b adds no code. Only the redactor page and the root README paragraph describe a redaction path. Their wording follows orders 14 and 15 and is checked by T6 (field "Interface", item 3).
- **Depends on (merged first):**
  1. **P8a, ticket revision 1 (draft, `db09637`).** P8a depends on every v1 row except P8a, P8b and P8c (`plan-v3.md:112`), so P8b starts only after every v1 code row is merged and the demos are re-pinned.
  2. **Ledger close-out finished.** Every BLOCKER or MAJOR row is FIXED-VERIFIED, WAIVED, OWNER-ONLY or IMPOSSIBLE-NOW, except the rows of P8b itself (the ticket review rows `R1-P8b-*` and the docs pull request's review rows). Who does this pass is PENDING LEAD 5.
  3. **The cloud's 5-cell ledger rows are normalised** (PENDING LEAD 6). Until then T2 fails with `BAD-LAYOUT` by design.
  4. **The P0d tool changes** are a hard dependency of the laptop check (Evidence step 7).

  P8b is not in the code merge chain of order 20 item 4 (`LEAD-ORDERS.md:78`: P1m, P1a, P1b, the P3a and P4d chain, P2a-1, P2d-1, P2d-2, P4a). It merges after all of those and after P8a, in either order with P8c. P8b and P8c share no file: P8c writes `tools/proof_pack.py` and P8b writes `docs/kinds/`. `defaults.py` (order 20 item 5, `LEAD-ORDERS.md:79`): P8b adds no constants and does not touch the file.
- **Problem in plain words:**
  - The core has eight kinds in its backend table and seven more parts that plan-v3 section 5 calls kinds. No page says, for each one, what it does, which backends exist, what role each backend plays and what it does not do.
  - There is no `README.md` under `src/hadavin_sdk/` (`find src/hadavin_sdk -name README.md` prints nothing).
  - Two of plan-v3's claims about kinds were already found wrong in code (A6: llm has no configured default; channel has one real backend). So pages written from the plan instead of the code would be wrong on day one.
  - Separately, "v1 is done" needs proof that no BLOCKER or MAJOR finding is left unresolved. Read at commit `601be32`, the cloud ledger cannot pass a check: 178 of its rows use a 5-cell layout, and 727 BLOCKER or MAJOR rows are unresolved (OPEN 585, FIXED-UNVERIFIED 142).
- **Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:** No code. The pages are written from the code at the step 1 commit (written into every evidence file). The sources, in order of authority:
  1. code;
  2. A6 and memo 6 section B (the claim checks);
  3. each package's frozen ticket;
  4. plan-v3 section 5.

  Where these disagree, the code wins. A disagreement found in a page is fixed in the page. If the code itself is wrong, it becomes a ledger row for the package that owns the code. A frozen-ticket claim the code proves false is one INFO line in `drift.md`, and the ticket is not edited. Not taken: plan-v2's "rollback tags" item for P8b (`plan-v2.md:117`), because plan-v3 section 10 gives tagging to the lead before each merge (`plan-v3.md:193`).
- **Target module and path in `src/hadavin_sdk/`:** none. The pages go to `docs/kinds/<kind>.md`, plus an index `docs/kinds/README.md` (PENDING LEAD item 1). `docs/` already exists in core: `git ls-tree origin/main docs/` lists 2 files, both about Slack. Reasons not to put the pages under `src/`: textnorm, usage and meter are single modules inside shared folders, so "README in the kind's folder" has no single meaning. Also, the build backend is `uv_build` (`pyproject.toml:57-58`), and whether it ships a non-Python file inside the package is UNVERIFIED. With the pages in `docs/`, that question does not arise.
- **Interface (names, argument and return types, errors):**
  1. **The kind set: 15 pages** (PENDING LEAD item 2).
     - (a) The eight capability keys of `TABLE` (`backends/table.py:386`): `secrets` (`:387`), `signer` (`:427`), `anchor` (`:467`), `store` (`:492`), `audit` (`:502`), `llm` (`:512`), `detector` (`:543`) and `channel` (`:558`). They are the same eight fields as `Backends` (`config.py:62-72`). The table has 31 entries in all.
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
     - Each of the seven pages in (b) has one line under the page title, above heading 1, that says plainly it is not a kind in the backend table. `diagnostic` "is a rendering rule, not a kind" (P5a ticket and plan-v3 line 80). `executor` is not a table kind (A6): it is `class Executor` (`actions/executor.py:47`), chosen per action contract through `NoneExecutor`, `ManualExecutor` and `HttpExecutor` (`actions/contract.py:15, 22, 33`).
     - **Redactor and detector are different parts** (settled from code):
       - `redactor.md` covers `guard.redact`: `redact` (`guard/redact.py:862`, exported by `guard/__init__.py:3`) and `redact_many` (`guard/redact.py:1244`). Its job is masking values before text leaves.
       - `detector.md` covers the `detector` capability: the `Detector` protocol (`guard/injection.py:19`); `RegexDetector` (`guard/injection.py:38`), built by `regex_detector` (`backends/builtin.py:43`); and the other backends, `llm_judge` and `bedrock_guardrail` (`table.py:546-556`). Its job is scoring text for prompt injection.
       - Each of the two pages has one line "not the same as <other>", with a link.
  2. **Fixed headings of every page.** At most 60 lines; plain words; no model ids, no prices, no real-looking values.
     1. What it does: 2 to 4 sentences.
     2. Interface: the protocol or class name with `file:line`.
     3. **Backends:** one table row per `TABLE` entry, in the form `` | `<backend>` | <labels> | <module> | ``. The labels column holds every label that applies, comma-separated, in these words, taken from code in this order:
        - **config default**: the `DEFAULTS` entry (`table.py:582-589`: secrets `fake`, signer `none`, anchor `none`, store `memory`, detector `regex`, channel `fake`), used when the config names nothing. `audit` and `llm` have no entry, so their pages say "no default; config must name one".
        - **dev only**: the pair is in `DEV_ONLY` (`table.py:593-601`). The page explains it once as "allowed only in `dev` (`table.py:591`)". The refusal in the client profile is named only if P6a is merged at the step 1 commit.
        - **not for production**: the pair is in `NOT_PROD` (`table.py:604`): signer `none` and anchor `none`.
        - **open standard**: the entry has `neutral=True` (`table.py:342-344`).
        - **not yet run live**: the entry has `status=_UNVERIFIED` (`table.py:380`). This is 23 of the 31 entries, and the tag is per row (ADV-18 contested).
        - **production choice**: an entry that is neither dev only nor not for production. Such a row never also says dev only or not for production.

        Each page with a config default says in one line whether that default is dev only or not for production. Five of the six are: secrets `fake`, store `memory` and channel `fake` are dev only, and signer `none` and anchor `none` are not for production. Only detector `regex` is neither. The detector page says the config holds a list (`config.py:71`: `detector: tuple[KindSettings, ...]`), so several detectors can run at once.
     4. Single dependency: the default, then the alternative, or the outline with its trigger. A6 applies:
        - llm has four real backends and no default, so config must name one.
        - secrets `fake` and `env` are dev only, so production uses `mounted_file` or `vault` (or a cloud manager).
        - channel has one real backend, Slack. **Channel outline (A6 words):** "second channel = email; trigger: a client needs email approvals". It is written in `channel.md` heading 8.
        - **Executor outline (A6 words):** "per-contract none/manual/http; http refused in pilot and prod; manual not built; outline with trigger". It is written in `executor.md` heading 8.
     5. Identity and rights: as declared by P6b2 (kind identity and rights), or "none declared".
     6. Configuration keys: from `config.py`.
     7. Tests that cover it: the test file paths, for example `tests/contracts/` for store.
     8. What it does not do: plain facts, each with its v1.1 row and trigger, never "known limitation".
  3. **Redactor wording (orders 14 and 15).** `redactor.md` and the root `README.md` paragraph that starts "Redaction is pattern-based and bounded" (found by those words, not by a line number) both say the following:
     - For secrets of 8 to 11 characters, the redactor catches "only plain copies" (order 15, `LEAD-ORDERS.md:44`). The case-folded sweep is v1.1 row LKV-2, trigger "before any pilot with real client data".
     - A known value hidden in invisible characters, base64 or hex is not caught in v1, except the exact hex and base64 spellings of a secret handed to a tool, which `tools.py` scrubs (order 14(1) as narrowed by order 19 C, PL46(a), `LEAD-ORDERS.md:38, 67`).

     The pages use the wording of the frozen P1 coverage sentence (`P1.md:20`: "copies of secrets of 8 to 11 characters, which are common passwords, reach the model"; "only the tool-output scrubber removes the exact hex and base64 spellings of a secret handed to a tool"), plus order 15's phrase "only plain copies". T6 checks these phrases (block `phrases.txt`, Evidence step 5). If P1's merged wording differs from revision 16, the phrase block changes with it.
  4. **Section 9 test-file table and the "Demos re-pinned" row.** Plan-v3 line 190 gives P8b a duty: "if a package names its test file differently, P8b updates this table". P8b checks every path in the block below on `main` (Evidence step 5, T5) and sends the corrected rows to the lead, who edits `plan-v3.md`. The block of paths named in `plan-v3.md:173-188` (`section9-list.txt`) is:
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
     tools/proof_pack.py
     ```
     Two items are flagged in advance:
     - `tests/test_redact*.py` matches no file on the worktree (the P2d row; P1 V12 says the same). The replacement name comes from the P2d ticket.
     - `tests/warden_port/` exists.

     Each `MISSING` row goes to the lead with the replacement name from the owning ticket. P8b also sends the corrected "Demos re-pinned" row (P8a item 8, `P8a.md:78`; A7 and A9 F9): the command is `tools/core_sync_check.py --core <core> --demo <dir> [--strict-pin]` (studio), not `python tools/check_core_copies.py`.
- **Neutral default / working alternative (or written outline with trigger):** not applicable: P8b adds no dependency. Single-dependency audit: each page states its kind's default and alternative, or its outline with a trigger. A kind with neither gets a drift item that the lead must answer before "done". The two known cases are already decided by A6 and are written in the pages (channel: email, trigger "a client needs email approvals"; executor: per-contract outline). So the repo gains both outlines with this pull request.
- **Files to create, change, delete (each with the reason):**
  - **Create:** `docs/kinds/README.md` (the index: one line per kind, with a link) and the 15 pages `docs/kinds/{secrets,signer,anchor,store,audit,llm,detector,channel,textnorm,stop_state,usage,meter,diagnostic,redactor,executor}.md`, so 16 files in all.
  - **Change:** `CHANGELOG.md`, one append-only line ("docs: one page per kind"). Root `README.md`: that redaction paragraph only, and only if T6 fails on it.
  - **Not changed:** nothing in `src/` or `tests/`. Nothing is deleted, and no new tool or CI job is added (cut surface, order 8). A CI check that the page set matches `TABLE` is a v1.1 row, trigger: a kind added after v1 without its page.
  - **Evidence files** (lead-written, all under `handover/evidence/P8b/`; listed under Evidence commands): `p8b_ledger_check.awk`, `planted-faults.txt`, `table-keys.txt`, `extra-kinds.txt`, `readme-set.txt`, `roles.txt`, `phrases.txt`, `t6-pages.txt`, `section9-paths.txt`, `drift.md`, `ledger-check-cloud.txt`, `ledger-check.txt`.
- **Existing core code reused (checked):** `backends/table.py` (`TABLE`, `DEFAULTS`, `DEV_ONLY`, `NOT_PROD`, `_UNVERIFIED`, `Entry.neutral`, `Entry.status`) and `config.py` `Backends` are the source of every Backends table; they are read, not changed. A6 and memo 6 section B are the claims check. Hashing, k1b/atomic, k1b/redaction, stats, evals and store/memory are not relevant, because no code is written.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):**
  - Docs only, with no identity, no rights and no secret.
  - The public-repo rule applies (order 20 item 4, `LEAD-ORDERS.md:78`; order 8(5), `LEAD-ORDERS.md:21`): no owner names, no studio paths, and no real-looking key or token, even as an example. Use placeholders such as `<KEY>`.
  - The CI secret-and-name scan must stay green on the docs pull request.
  - No page shows a dev-only or not-for-production backend as a production choice. T6 checks every `DEV_ONLY` and `NOT_PROD` pair.
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** there are no unit tests (no code); the checks below are the tests. Every check except T4 has at least one planted fault, and the planted faults run before the real check, so a check that cannot fail is caught first. T4 is an LLM report that the lead reads.
  - **T1, page set:** `comm` of the `TABLE` keys taken from code plus `extra-kinds.txt`, against `ls docs/kinds` without `README.md`, prints nothing (Evidence step 5).
  - **T2, ledger check (cloud):** `p8b_ledger_check.awk` exits 0 on `handover/ledger.md` (Evidence step 7). **Fail-before:** on the ledger before the close-out, the check exits 1 and prints `UNRESOLVED` lines and `BAD-LAYOUT` lines. The author ran it on scratch, read at commit `601be32`: `rows=1621 bad=178 unresolved_blocker_major=727`, rc 1. That is not evidence, and the runner re-runs it.
  - **T3, ledger check (laptop):** `ledger_check.py` and `ledger_lint.py` both exit 0, and the copied BLOCKER and MAJOR count equals the cloud count (Evidence step 7).
  - **T4, drift report:** no open drift in `docs/kinds/` (Evidence step 6). No planted fault.
  - **T5, section 9 paths:** every path of `section9-list.txt` exists on `main`, or is reported as `MISSING` with its replacement (Evidence step 5).
  - **T6, deterministic page checks** (grep, no LLM; Evidence step 5). It checks four things:
    - every Backends row carries exactly the labels the code gives it;
    - no dev-only or not-for-production row says "production choice";
    - `audit.md` and `llm.md` say "no default; config must name one";
    - `redactor.md` and the root README redaction paragraph each contain every phrase of `phrases.txt`.
  - Hostile inputs, races and contract suite: not applicable (no code).
- **Mutation plan: which behaviours get a mutant, which test kills each.** These are planted faults, each in a throwaway copy, never in the real ledger or the real docs.
  - **Ledger faults (P1 to P8, P12 to P14, P21 and P22):** each is a ledger file of the header line, the separator line, one FIXED-VERIFIED MAJOR row, and the row named below.
  - **P15 and P16:** as stated in the table (no header, or no file content).
  - **The author's scratch runs** (mawk 1.3.4 only; gawk and busybox awk not tried): P1 to P8 and P12 to P22 except P9, P11, P17 and P20, with the expected results. This is not evidence, and the runner re-runs every fault.

  | Fault | Planted row or change | Killed by | Expected |
  |---|---|---|---|
  | P1 | 5-cell row `\| BS-PX-1 \| Major \| PX \| s \| OPEN \|` | T2 layout rule | rc 1, `BAD-LAYOUT line 4 id BS-PX-1` |
  | P2 | BLOCKER, status OPEN | T2 | rc 1, `UNRESOLVED OPEN <id>` |
  | P3 | lower-case `major`, status FIXED-UNVERIFIED | T2 (severity case fold) | rc 1, `UNRESOLVED FIXED-UNVERIFIED <id>` |
  | P4 | unknown status `DONE` | T2 (fail closed) | rc 1, `UNRESOLVED DONE <id>` |
  | P5 | severity `Major/Minor` | T2 severity rule | rc 1, `BAD-SEVERITY <id>` |
  | P6 | status `OPEN (build notes)` | T2 (first word only) | rc 1, `UNRESOLVED OPEN <id>` |
  | P7, control | MINOR, status OPEN | T2 | rc 0 |
  | P8, control | MAJOR, status WAIVED, artifact cell `W-1` | T2 | rc 0, `WAIVED <id>` printed |
  | P9 | delete `docs/kinds/channel.md` in a scratch copy | T1 | `comm` prints `channel` |
  | P10 | scratch `secrets.md`: the `env` row says `production choice` and not `dev only` | T6 | prints `WRONG-LABEL secrets env 'dev only'` and `BAD-PROD-CHOICE secrets env`, rc 1 |
  | P11 | add `tests/no_such_file.py` to a copy of `section9-list.txt` | T5 | `MISSING tests/no_such_file.py` |
  | P12 | 5-cell `\| R2-PX-1 \| Blocker \| PX \| s \| OPEN \|` | T2 layout rule | rc 1, `BAD-LAYOUT ... id R2-PX-1` |
  | P13 | the same id in 7 cells, BLOCKER, OPEN | T2 (digit in prefix read) | rc 1, `UNRESOLVED OPEN R2-PX-1` |
  | P14 | `\| ABC-1 \| PX \| BLOCKER \| s \| OPEN \| a \| c \|` | T2 (3-letter prefix read) | rc 1, `UNRESOLVED OPEN ABC-1` |
  | P15 | empty file | T2 header and row rules | rc 1, `BAD-HEADER count=0` and `NO-ROWS` |
  | P16 | one valid row, no header line | T2 header rule | rc 1, `BAD-HEADER count=0` |
  | P17 | append `fakekind` to a scratch copy of `table-keys.txt` | T1 | `comm` prints `fakekind` |
  | P18 | delete the line with "only plain copies" from a scratch `redactor.md` | T6 | `MISSING-PHRASE docs/kinds/redactor.md: only plain copies`, rc 1 |
  | P19 | scratch `store.md`: the `postgres` row says `config default` | T6 | `WRONG-LABEL store postgres 'config default' code=0 page=1`, rc 1 |
  | P20 | scratch copy of the laptop ledger with one MAJOR OPEN row | T3 | `ledger_check.py` exits non-zero (UNVERIFIED: the tool's arguments and format are not visible here) |
  | P21 | MAJOR, status WAIVED, empty artifact cell | T2 waiver rule | rc 1, `BAD-NO-ARTIFACT WAIVED <id>` |
  | P22 | a second row with the id of the FIXED-VERIFIED row | T2 duplicate rule | rc 1, `BAD-DUP <id> lines 3 4` |

  Every fault has a named killer: 22 faults, of which P7 and P8 are controls that must pass. That gives 15 on T2, 2 on T1, 3 on T6, 1 on T5 and 1 on T3.
- **Evidence commands (exact), and where the raw output is saved:** all files go under `handover/evidence/P8b/` (written `E/` below). Every command is written as `{ git rev-parse origin/main; <command>; echo "rc=$?"; } > E/<file> 2>&1`, so the first line is the commit and `rc=` is the command's own exit code, never a pipe's. Where a step pipes, the `rc` line is taken with `set -o pipefail` in a `bash -c`. **Run order (one order, nothing else):**
  1. **Commit id:** `git rev-parse origin/main`. This sha is the step 1 commit, and every later file's first line must equal it.
  2. **Ledger faults on scratch copies:** P1 to P8 and P12 to P16, plus P21 and P22, each run as `awk -f E/p8b_ledger_check.awk <scratch file>`. One line per fault (fault id, rc, first printed line) is appended to `E/planted-faults.txt`. The script, saved by the lead as `E/p8b_ledger_check.awk`, is the text of the resolve file (ADV-1 row), split onto lines at its semicolons, with the table escape `\|\|` written as `||`. No token is changed:
     ```
     BEGIN { FS="|" }
     /^\| *id *\| *package *\| *severity *\|/ { hdr++; next }
     /^\|[-:\| ]+$/ { next }
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
       if (s=="FIXED-VERIFIED") next
       if (s=="WAIVED" || s=="OWNER-ONLY" || s=="IMPOSSIBLE-NOW") {
         art=$7; gsub(/ /,"",art)
         if (art=="" || art=="-") { bad++; printf "BAD-NO-ARTIFACT %s %s\n", s, id; next }
         printf "%s %s\n", s, id; next
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
     The rules: every table row is read; an id that does not parse is BAD-LAYOUT. A row with a cell count other than 7 is BAD-LAYOUT. A MINOR or NIT row never blocks. The pattern of the waiver id in a WAIVED row's artifact cell stays a manual check by the lead, because the P0d format is not visible here.
  3. **Write the 15 pages and the index** in the docs pull request.
  4. **Page and set faults on scratch copies:** P9, P10, P11, P17, P18 and P19, run with the commands of step 5 against the scratch copies. Results are appended to `E/planted-faults.txt`.
  5. **T1, T5 and T6 on the real pages,** at the step 1 commit, in the core checkout:
     - **T1:**
       - `uv run python -c "from hadavin_sdk.backends.table import TABLE; print('\n'.join(sorted(TABLE)))"` writes `E/table-keys.txt` (with its commit and rc lines saved alongside as `E/table-keys.log`, so the key file itself stays one name per line). There is no grep, so no other dict can match.
       - `E/extra-kinds.txt` is the literal block of Interface item 1(b).
       - `ls docs/kinds > E/readme-set.txt`.
       - Pass: `bash -c 'comm -3 <(sort E/table-keys.txt E/extra-kinds.txt) <(ls docs/kinds | grep -v "^README.md$" | sed "s/\.md$//" | sort)'` prints nothing, with its output and rc appended to `E/readme-set.txt`.
     - **T5:** for each line `p` of `section9-list.txt` (Interface item 4), `git ls-files "$p"` on the step 1 commit. An empty result writes `MISSING $p` to `E/section9-paths.txt`. Pass: no `MISSING` line, or each `MISSING` line followed by the replacement name the lead accepted.
     - **T6:**
       - `E/roles.txt` comes from code: `uv run python -c` with this body:
         ```
         from hadavin_sdk.backends.table import TABLE, DEFAULTS, DEV_ONLY, NOT_PROD, _UNVERIFIED
         for k in sorted(TABLE):
             for b in sorted(TABLE[k]):
                 e = TABLE[k][b]
                 labels = [n for n, on in (('config default', DEFAULTS.get(k) == b), ('dev only', (k, b) in DEV_ONLY), ('not for production', (k, b) in NOT_PROD), ('open standard', e.neutral), ('not yet run live', e.status == _UNVERIFIED)) if on]
                 print(k, b, ';'.join(labels) or '-', sep='\t')
         ```
         The author ran this body read-only on the worktree with `python3 -I`: 31 lines, 6 config defaults, 23 not yet run live, 10 open standard. Not evidence.
       - `E/phrases.txt` is the literal block:
         ```
         only plain copies
         secrets of 8 to 11 characters
         exact hex and base64 spellings of a secret handed to a tool
         ```
       - Then the lead runs this POSIX `sh` text from the core checkout root, with `roles.txt` and `phrases.txt` copied there, and saves the output to `E/t6-pages.txt`:
         ```
         fail=0
         tab="$(printf '\t')"
         while IFS="$tab" read -r kind be labels; do
           page="docs/kinds/$kind.md"
           row=$(grep -E "^\| *\`$be\` *\|" "$page")
           if [ -z "$row" ]; then echo "NO-ROW $kind $be"; fail=1; continue; fi
           for want in "config default" "dev only" "not for production" "open standard" "not yet run live"; do
             case ";$labels;" in *";$want;"*) code=1 ;; *) code=0 ;; esac
             case "$row" in *"$want"*) page_has=1 ;; *) page_has=0 ;; esac
             if [ "$code" != "$page_has" ]; then echo "WRONG-LABEL $kind $be '$want' code=$code page=$page_has"; fail=1; fi
           done
           case "$labels" in *"dev only"*|*"not for production"*)
             case "$row" in *"production choice"*) echo "BAD-PROD-CHOICE $kind $be"; fail=1 ;; esac ;;
           esac
         done < roles.txt
         for k in audit llm; do
           grep -qF "no default; config must name one" "docs/kinds/$k.md" || { echo "MISSING-NO-DEFAULT $k"; fail=1; }
         done
         awk '/Redaction is pattern-based and bounded/ {p=1} p && /^$/ {exit} p' README.md > readme-redaction.txt
         for f in docs/kinds/redactor.md readme-redaction.txt; do
           while IFS= read -r phrase; do
             grep -qiF -- "$phrase" "$f" || { echo "MISSING-PHRASE $f: $phrase"; fail=1; }
           done < phrases.txt
         done
         echo "t6_fail=$fail"
         exit "$fail"
         ```
         The author ran this text on scratch pages built from `roles.txt`: the control gave rc 0, and P10, P18 and P19 each gave rc 1 with the lines in the table. Not evidence.
       - Pass: `t6_fail=0` and `rc=0`. If only the root README phrases fail, the docs pull request changes that paragraph (Files field).
  6. **T4, the drift report:** the lead invokes `egm:egm-drift-report` through the Skill tool (never by reading the skill file) on the directory `docs/kinds/`, against core `main` at the step 1 commit. Frozen tickets and plan-v3 are inputs, never in scope. The skill writes `{YYYY-MM-DD}_DRIFT_REPORT.md`, which the lead saves as `E/drift.md`.
     - Pass: no open drift in `docs/kinds/`.
     - Each drift item is fixed in the page, or, if the code is wrong, made a ledger row for the package that owns the code.
     - A ticket claim the code proves false is one INFO line, and is not blocking.
     - After any fix, T1 and T6 are re-run.
  7. **Laptop fault, then the ledger checks last:**
     - P20 on a scratch copy of the laptop ledger.
     - Then **T2:** `awk -f E/p8b_ledger_check.awk handover/ledger.md`, written to `E/ledger-check-cloud.txt`. Pass: `rc=0`, `bad=0`, `unresolved_blocker_major=0`.
     - Then **T3** (plan-v3 section 9, row "No unresolved findings", `plan-v3.md:185`), run after the lead has copied the cloud rows into the laptop ledger (plan-v3 line 54):
       - `python egm/tools/ledger_check.py --topic core` and `python egm/tools/ledger_lint.py`, both written to `E/ledger-check.txt` in the same form. Pass: both `rc=0`, with WAIVED rows listed by id.
       - **Count check:** the number of BLOCKER and MAJOR rows the lead copied to the laptop ledger equals the number of BLOCKER and MAJOR rows in the cloud check. Both numbers are written in `E/ledger-check.txt`. The source of the laptop count is UNVERIFIED until the tool is seen.
       - The laptop check expects 9 columns while the cloud ledger has 7, so the copy step maps the columns (`inventory-A.md:10`; not re-read by this author, UNVERIFIED).
- **Reviewers: correctness + adversarial (fresh agents; they get the diff, this ticket and the evidence only):** Tier B: one fresh `egm:*` reviewer (`egm-codebase-details`, which checks every page claim against its `file:line` at the step 1 commit), one round, at most 2 fix batches (order 6(b)). The ticket itself had its single round (round 1, both reports in `handover/reviews/`); this revision applies that round's resolve.
- **Done =** all of the following:
  1. The dependencies are met: P8a merged, the ledger close-out finished (PENDING LEAD 5), and the cloud rows normalised (PENDING LEAD 6).
  2. T1, T2, T3, T5 and T6 pass at one step 1 commit, written as the first line of every evidence file. T4's `drift.md` shows no open drift in `docs/kinds/`. That means:
     - all 15 pages exist and match the code's key set;
     - every Backends label matches the code;
     - the redactor phrases are present;
     - every section 9 path exists, or its correction was sent to the lead;
     - the cloud check exits 0;
     - both laptop tools exit 0, with matching counts.
  3. P1 to P22 behave as in the table.
  4. **P8b's own rows** (the `R1-P8b-*` ticket review rows and the docs pull request's review rows) are closed by the lead before the final step 7 run. Each cites the revision or the pull request commit that fixed it. Drift items that became ledger rows in step 6 are closed by the package that owns the code; until they are, P8b is not done.
  5. The docs pull request is green on every gate: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit, and the CI secret-and-name scan.

  **Honest note:** if the ledger close-out has not happened, step 7 fails, and that is the intended stop, not a bug. Most unresolved rows come from ticket-paper reviews whose fixes landed in later ticket revisions, but no row was moved to FIXED-VERIFIED. P8b cannot close those rows: only the package that built a fix can verify it (PENDING LEAD 5). Every new 5-cell row written by a cloud session also makes T2 fail with `BAD-LAYOUT` until PENDING LEAD 6 is done.
- **Rollback:** the lead tags `pre-P8b` before the merge (plan-v3 section 10). The change is docs only and is undone with a revert pull request. There is no migration and no semantic change.

## PENDING LEAD
1. **README location:** `docs/kinds/<kind>.md` plus an index (recommended; `docs/` already exists in core), or `README.md` inside each kind's source folder (rejected above: single-module kinds share folders).
2. **Kind set:** the 15 of Interface item 1 (recommended; each of the seven non-table pages says so in one line under its title), or only the 8 `TABLE` keys.
3. **CLOSED by A6** (`amendments.md:9`; A14(6) lets an amendment answer a pending item). The channel outline is "second channel = email; trigger: a client needs email approvals", and it is written in `channel.md`.
4. **SPLIT into items 5 and 6.**
5. **Who closes the ledger before P8b.**
   - Option (a): each package's result review closes its own rows (FIXED-VERIFIED with the frozen revision and the build evidence, or WAIVED by the owner), and the lead runs one close-out pass before P8b starts.
   - Option (b): P8b closes them.
   - Recommend (a): only the package that built the fix can verify it, and (b) would make a docs package judge code. Reversible.
6. **INFORM: the cloud normalises its own 5-cell rows now.** Read at commit `601be32`, 178 rows use the layout `id | severity | package | summary | status` (the resolve counted 119 at its own read; the ledger keeps growing).
   - The cloud session rewrites them into the 7-column layout of the ledger header (`id | package | severity | summary | status | verifying artifact | reviewed commit`), with the severity in capitals.
   - The `Major/Minor` rows are decided from their review files.
   - Duplicate ids are renamed with the suffix `-b`, and both review files are cited.
   - "(build notes via resolve)" moves from the status cell to the artifact cell.
   - Every new row is written in 7 columns from then on.

   This is a file under `handover/` (allowed by the orders), not a status change. Recommend: yes, as one cloud commit, then run the new awk and save its output; it should then report `bad=0`. Reversible (one commit).
7. **The new awk as the cloud's own check.** Optional: the cloud runs `p8b_ledger_check.awk` after each ledger write and fails its own step on any `BAD-*` line. Recommend yes: it costs one command and keeps item 6 from slipping back. No repo change.

## UNVERIFIED
- `ledger_check.py` and `ledger_lint.py`: their behaviour, arguments and laptop-count output (studio repo, not visible here), and so P20's exact result.
- The P0d WAIVED format and the waiver-id pattern (a manual check by the lead).
- `inventory-A.md:10` (the 9-column versus 7-column claim; not re-read).
- Whether `uv_build` ships non-Python files in the package (moot while the pages sit in `docs/`).
- The live status of the 23 of 31 entries marked `_UNVERIFIED`; the other 8 are not marked.
- The final redactor wording in the merged P1, P2d and P5c tickets. T6's phrase block follows P1 revision 16 (`P1.md:20`) and order 15.
- The output of `egm:egm-drift-report` (an LLM skill; not deterministic).
- The awk and `sh` text on gawk or busybox (run on mawk 1.3.4 and the local `sh` only).
- `uv run` of the two Python one-liners (the author ran the T6 body with plain `python3 -I` on the worktree, not through `uv`).
