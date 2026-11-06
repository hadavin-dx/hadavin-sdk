# AK1 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

## Honest note (read first: what I did NOT check, and what my probes do and do not prove)
- **No suite, lint, mutant or ruff was run.** I wrote no git state. I did not edit the ticket, and I did not touch `DECISIONS.md`, `owner-visible-limits.md` or `questions-for-lead.md`. This file replaces the skill's default name `goldfish_review_report.md`. The skill's interactive gate was skipped because the lead's brief says AUTO.
- **I ran three read-only probes** with the repository's `.venv` interpreter (Python 3.13.18, pydantic 2.14.1, `-I`). Each one used a throwaway copy of `src/hadavin_sdk` outside the repository. They are scratch output, not evidence.
  - **(P-a) Import shapes.** I planted stub modules into the copy. Revision 3's two shapes fail on import: `config` -> `guard.outbound` -> `config`/`limits` -> `registry` -> `config`, and `pipeline.step` <-> `guard.outbound`. The fixed shape in BN-1 and BN-2 imports cleanly: I imported every one of the 105 modules FIRST, each in its own fresh interpreter, with 0 failures. The stubs stand in for files that do not exist yet: `guard/redactor.py`, `llm/masked.py`, `llm/metered.py`, `meter.py` and `money.py` (P5c, P4b1). **So the probe proves the cycles on main's real modules. It does not prove that P5c's and P4b1's modules add no new cycle.** That is why BN-2 adds a lasting fresh-interpreter test (L17) instead of relying on my probe.
  - **(P-b) Hashing.** `models.sha256_hex(b"ab")` raises `TypeError`. `sha256_hex("ab")` hashes the JSON text `"ab"` (with quotes), not the UTF-8 bytes. `sha256_hex("\ud800")` raises `UnicodeEncodeError`.
  - **(P-c) Imports.** I listed, by AST, the imports of every `src/` and `demos/` module, and the dynamic-import calls (results in Facts F5, F6).
- **Not checked:**
  - Every name taken from P4a, P4b1, P4b2, P4c, P4d, P5a, P5c, P6a and P6b1 is still ticket text, not code (the ticket's U1 still stands). For SessionClosed's base class and for MeterError, I read only the lines I cite.
  - I did not re-read `plan-v1.md`, `AK2a.md` or `AK4a.md`.
  - The hot-file check in BN-5 counts MENTIONS of each file in other tickets. It does not count real edits.
  - Whether the P1m runner accepts the planted-edit mutants (U8 stands).
- **One judgement a reader may dispute.** BN-2 moves `OutboundRefused` into `errors.py` instead of moving the `ContextVar` into `pipeline/context.py`.
  - **My reason, from probe P-a case F2b:** a leaf module inside `pipeline/` still cycles when `pipeline/__init__.py` re-exports `step` and `guard.outbound` is imported first. `errors.py` is an existing leaf whose own docstring states exactly this purpose.
  - **The cost:** P5a's `OWN_CODES` key string changes (PENDING LEAD 11).

## Status, target, gate
- **Status:** resolved (AUTO; categorised). The ticket is NOT edited. The fixes are build notes BN-1 to BN-17 below, and they win over the ticket text.
- **Target:** `handover/tickets/AK1.md` revision 3 DRAFT, commit `3a3fcca`, full file (430 lines), all three sub-PRs.
- **Findings:** 23 ids. Severity is taken from the tables and never changed here.
  - `reviews/AK1-round3-adversarial.md` R3-ADV-1..10: 0 Blocker, 4 Major, 5 Minor, 1 Nit.
  - `reviews/AK1-round3-correctness.md` R3-COR-1..13: 0 Blocker, 5 Major, **6 Minor** (COR-6 to COR-11; the report's header says 5, and the table is what is counted), 2 Nit.
- **Gate (order 20 item 6):** round 3 is the last round under the cap of 3. A money and redaction ticket gets a 4th round only if its last round had no Blocker and at most 2 Majors. Round 3 has **9 Majors**: ADV-1 to ADV-4 and COR-1 to COR-5. Every one is a distinct defect, and no two are duplicates. **So there is NO round 4.**
  - The ticket freezes at revision 3 with this file attached. The banner below goes under its revision line.
  - The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together.
  - Nothing is escalated to the owner. PENDING LEAD 10 is for the lead, not the owner. PENDING LEAD 7, 8, 9, 11 and 12 are INFORM.

## Facts I checked myself (on disk at `<repo>`; "probe" = run as described in the Honest note)
- **F1 (COR-1 TRUE; probe).**
  - The chain: `config.py:18-21` imports only `defaults`, `deferred`, `backends.table`, `errors`, `scrub_settings`; `limits.py:9` `from hadavin_sdk.registry import Registry`; `registry.py:20` `from hadavin_sdk.config import Config, ...`.
  - **Revision 3 as written:** `config` imports `KIND_CLASS` from `guard.outbound`, and `guard.outbound` imports `config` and `limits`. This fails on `import hadavin_sdk.config`, on `import hadavin_sdk.guard.outbound` and on `import hadavin_sdk.app`, each with "partially initialized module".
  - **Revision 3's own fallback also fails:** importing `Config` inside `gate_context` only still cycles through `limits` -> `registry` -> `config`.
  - `backends/table.py` imports no `hadavin_sdk` module; its imports are `re`, `collections.abc`, `dataclasses`, `pathlib`, `typing`, `urllib.parse`, `pydantic`.
- **F2 (COR-2 TRUE; probe).**
  - The revision 3 shape cycles in both import orders: `pipeline/step.py` imports `OutboundRefused` from `guard.outbound`, and `guard.outbound` imports `current_object_ref` from `pipeline.step`.
  - A `pipeline/context.py` leaf works only if `pipeline/__init__.py` does not import `step` (case F2b fails).
  - `errors.py` is a 5-line leaf with no imports, whose docstring reads "Errors shared by ``config`` and ``backends``, kept here so neither has to import the other". `make` (backends) raises `OutboundRefused("ungated_kind")`.
  - P5a keys `OWN_CODES` by `"module:Qualname"` and checks it with an identity walk over `sys.modules[cls.__module__]` (`P5a.md:54`, `:282`).
- **F3 (COR-3 TRUE).** In `tests/test_lockin_guard.py`:
  - The bare-vendor-name pattern is at `:520-521`.
  - `literal_problems` (`:595-631`) scans every module outside `VENDOR_MODULES` (`:493-500`).
  - **In `backends/table.py` it skips only vendor-named classes and functions, and a top-level assignment whose first 12 unparsed characters contain `TABLE` (`:552-562`).** So a `KIND_CLASS` literal is scanned in `table.py` just as in `guard/outbound.py`.
  - Stale `LITERAL_OK` entries fail (`:626-630`). `(hadavin_sdk.config, "slack")` already exists (`:509`).
  - Over today's `TABLE` (probe P-c), exactly four kind names match: `anthropic`, `bedrock`, `gemini` (llm) and `slack` (channel). `openai_compat`, `bedrock_guardrail`, `aws_kms` and `s3_object_lock` do not match, because each is followed by `_`.
- **F4 (COR-4 TRUE).**
  - `tests/contracts/kinds/detectors.py:49-52` builds the judge (`make("detector", JudgeSettings(kind="llm_judge"...))`).
  - The contract rows for `bedrock_guardrail` build `GuardrailDetector(...)` directly (`:89-98`).
  - `tests/test_p6_detectors.py:344-358` patches the AWS environment and `check_filter`, then calls `make("detector", guardrail_settings())` at `:355`. It skips without `boto3` (`:345`).
  - `guard/bedrock_guardrail.py:61-70` `make` always builds real clients.
- **F5 (ADV-2: the `src/` half is FALSE).** `tests/test_lockin_guard.py` rule a is ALREADY a default-deny for `src/`.
  - An import is allowed only if it is stdlib, `hadavin_sdk`, `BASE_OK = {"pydantic", "pydantic_settings", "yaml"}` (`:38`), or listed for that very module in `VENDOR_IMPORTS`/`LIBRARY_IMPORTS` (`:58-76`, `:140-152`). Anything else fails as "unknown ... outside its allowed modules".
  - A dynamic import call outside `DYNAMIC_IMPORT_OK = {backends.factory, actions.executor, tools}` fails (`:79-83`, `:122-125`). So does `import importlib` outside it (`:138-139`).
  - So `urllib3`, `websockets`, `grpc`, `slack_sdk`, `cohere`, `voyageai`, `mcp`, `importlib.import_module` and `__import__` in any `src/` module (AK2a's `ingest/` included) already fail `test_lockin_guard.py`, which Done requires green.
  - **TRUE remainder (probe P-c):** that scan covers `SRC` only (`:21`), so `demos/` has no default-deny. It also allows every stdlib module, so `ftplib`, `imaplib`, `poplib`, `nntplib`, `xmlrpc`, `socketserver`, `asyncio`, `multiprocessing` and `ctypes` pass both scans. None of these nine is imported anywhere in `src/` or `demos/` today.
  - Demos' third-party imports today: `pydantic`, `yaml`, `sqlglot`, and `psycopg` (only in the pre-listed `pgsource.py`). No demo module makes a dynamic import call.
  - `tests/__init__.py` exists and `pyproject.toml:86` sets `pythonpath = ["."]`, so a test can import helpers from `tests.test_lockin_guard`.
- **F6 (ADV-3 TRUE, wider than reported; probe P-b).**
  - `canonical_json` (`models.py:38-43`) is `json.dumps(..., ensure_ascii=False)`, so `sha256_hex` (`:46-47`) raises `TypeError` for `bytes` and hashes a JSON-quoted string for `str`.
  - `"\ud800".encode("utf-8")` raises `UnicodeEncodeError`. `content_sha256` therefore cannot be `sha256_hex(body)`.
- **F7 (ADV-4 TRUE as a statement gap; there is precedent).**
  - `P4b1.md:269` says plainly that a failing call with 3 attempts books 3 times its reservation, and can pass its cap by `count x (attempts - 1) x W`. Its PENDING LEAD 17 (`P4b1.md:409`) proposes the same.
  - Order 19 D ACCEPTED the whole-call maximum PL54 (`requests x attempts x W`). Order 27 item 45 accepted P4b1 PL23's window.
  - AK1's `book_call` IS P4b1-b's function, moved (Interface 7 P10). A different hold on the gate would break "one implementation".
- **F8 (ADV-7).** `class SessionClosed(RedactorRefusal)` (`P5c.md:210`). `OverBudget` and `MeterUnavailable` are subclasses of `MeterError` (`P4b1.md:31`). `OverBudget(("kill_switch",))` is P4b1's (`P4b1.md:32`, `:37`). `rule_id=redactor.fingerprint` is P5c's (`P5c.md:288`).
- **F9 (COR-11 TRUE in part).**
  - `guard/redactor.py` is in P5c's `MASKING_SOURCES` (`P5c.md:237`), and `config_hash` always adds the fingerprint (`P5c.md:267`). So AK1-b's `mask_leaves` move changes every agent's `config_hash`.
  - `llm/masked.py` is NOT in that list.
  - P5c replaced hand-pinned hashes with a computed fingerprint on purpose (`P5c.md:67`).
- **F10 (cites).**
  - **COR-6:** `app.py:89` is the purge-DSN raise; `sources=` and `tools=` are refused at `:90-98`.
  - **COR-7:** `tests/test_repo_rules.py:296` is `SECRET_FREE` and `:297-302` is the module list; `:410-411` are the allow rows.
  - **COR-8:** `src/hadavin_sdk/codes.py` does not exist.
  - **COR-9:** `make` reads `TABLE[capability][settings.kind]` (`factory.py:36`) and `ALLOWED[capability]` (`:52`). Both are plain `dict`s and are the same objects as in `backends.table` (probe).
  - **ADV-8:** `cli._k1b` builds its own llm and detectors at `cli.py:221-222`. `P5c.md:343` wraps there and T3-11 (`P5c.md:502`) tests "k1b goes through the wrapper", not the judge's identity.
  - **COR-12:** the stale cites are at `AK0.md:63` (the reviewer said `:60`). `AK1.md:288` and `:324` are now mutant rows M-B21 and M-C20.
  - **ADV-5:** no `src/` code calls `model_copy`/`model_construct` on a `Config` (grep). The validator bypass applies to every `Config` refusal on main (`DEV_ONLY`, loopback, anchors), not only AK1's.

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK1-round3-adversarial.md`, `reviews/AK1-round3-correctness.md`) had 9 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-17 in `reviews/AK1-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes, and the AK1-b delta note of BN-11. The CHANGELOG sections are history, not instructions. Totals after the notes: 66 test rows (S 14, G 29, L 16, C 7), 82 mutants (A 22, B 38 with M-B11 retired, C 22), split 21 / 53 / 8. `KIND_CLASS` lives in `backends/table.py` and `OutboundRefused` in `errors.py` (BN-1, BN-2). `RESERVED_GATED` is deleted (BN-6).

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-COR-1 (Major) | PROPOSE FIX | TRUE (F1, probe). The pure-data classification moves into `backends/table.py`; `config.py` imports only from there. A fresh-interpreter import row L17 is added, with mutant M-C22. **BN-1.** |
| R3-COR-2 (Major) | PROPOSE FIX (PENDING LEAD 11, INFORM) | TRUE (F2, probe). `OutboundRefused` is defined in the leaf `errors.py`, and `guard/outbound.py` re-exports it. `pipeline/step.py` never imports `guard/outbound.py`. Mutant M-B39 is added. **BN-2.** |
| R3-COR-3 (Major) | PROPOSE FIX | TRUE (F3). `LITERAL_OK` rows are added for exactly the literals rule c reports. `tests/test_lockin_guard.py` joins Files and the hot-file list. **BN-3.** |
| R3-COR-4 (Major) | PROPOSE FIX | TRUE (F4). The cites are fixed in four places, and C2's second half is reworded. **BN-4.** |
| R3-COR-5 (Major) | PROPOSE FIX | TRUE. "New on this list" is wrong (amendment F6). Merge-order-only constraints are added for `backends/table.py`, `config.py`, `app.py`, and the two files the BNs add (`errors.py`, `tests/test_lockin_guard.py`). **BN-5.** |
| R3-ADV-1 (Major) | PROPOSE FIX (surface cut; PENDING LEAD 8, INFORM) | TRUE. A closed map in the lint lists the classes each capability may carry. Any capability missing from the map may only be `gated`. `RESERVED_GATED` is deleted, and L3, L7, L10 and M-C2 are rewritten. **BN-6.** |
| R3-ADV-2 (Major) | CONTEST for `src/`; PROPOSE FIX for the remainder | CONTEST with cites (F5): `test_lockin_guard.py:38`, `:140-152`, `:79-83`, `:122-125` and `:138-139` already fail every unlisted third-party import and every dynamic import in `src/`. TRUE remainder: `demos/` has no default-deny, and stdlib network modules are missing from L8. L8 reuses the lockin helpers (closes COR-13), adds nine stdlib modules and a demos default-deny with a 3-entry allowlist, and gains L12 teeth and M-C21. **BN-7.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE (F6). `content_sha256` is defined on raw bytes. A lone surrogate in a `str` body is refused by the `StepInput` constructor, so step (a) cannot raise. S14, M-A21 and M-A22 are added. **BN-8.** |
| R3-ADV-4 (Major) | PROPOSE FIX (statement and pin; PENDING LEAD 9, INFORM, money) | TRUE as a gap (F7). The hold stays at `request_bound x W`, the same as the llm path. The cap window is stated in Security and in Rules. G27 gains an `attempts=3` case, and M-B38 is added. **BN-9.** |
| R3-ADV-5 (Minor) | PROPOSE FIX (state the limit; cut, no new refusal) | TRUE, but general to every `Config` refusal (F10). Security gains the limit, and P6a (the `Config` owner) gets a relay. **BN-10.** |
| R3-ADV-9 (Minor) | PROPOSE FIX | TRUE. AK1-b's first build step is a delta note, read in the build-start review (no new round). U1 gains `Redactor.fingerprint` and `OverBudget(("kill_switch",))` with cites (F8). **BN-11.** |
| R3-ADV-6 (Minor) | PROPOSE FIX | TRUE. M-C9 is in `backends/factory.py` (C1's lookup) and is killed by G16. It differs from M-B16 (fallback vs removal). **BN-12.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | TRUE (F8). G5 gains a pass through `run_step`. No masking run ends `needs_person masking_refused`; no meter scope ends `needs_person step_error`. **BN-12.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | TRUE (F10). C5 gains the `cli._k1b` case (pin; dev, because k1b replay is dev-only in v1, order 19 D). **BN-12.** |
| R3-ADV-10 (Nit) | PROPOSE FIX | Interface 3 (d) catches `Exception` only. Every other `BaseException` propagates after (e). **BN-12.** |
| R3-COR-6 (Minor), R3-COR-7 (Minor) | PROPOSE FIX | TRUE (F10). Cites: `app.py:90-98`; `test_repo_rules.py:296-302` and `:410-411`. **BN-13.** |
| R3-COR-8 (Minor) | PROPOSE FIX | TRUE (F10). `codes.py` changes only if P5a has merged; otherwise P5a adds the row. **BN-13.** |
| R3-COR-9 (Minor) | PROPOSE FIX | TRUE (F10). The four patch targets are named, together with where `make` reads each. **BN-14.** |
| R3-COR-10 (Minor) | PROPOSE FIX (PENDING LEAD 10, lead) | TRUE. "Can build when" lists all 7 direct dependencies and P4d. There is no build before a numbered S0 EXIT for AK1. **BN-15.** |
| R3-COR-11 (Minor) | PROPOSE FIX; the "pin the value" part is CONTESTED | TRUE in part (F9): `guard/redactor.py` is a masking source, so the fingerprint and `config_hash` change. CHANGELOG, Rollback and the evidence record this. No literal pin, because P5c replaced hand pins on purpose (`P5c.md:67`). **BN-16.** |
| R3-COR-12 (Nit) | PROPOSE FIX | The header says "orders 6-31". The AK0 relay is re-pointed (F10). **BN-17.** |
| R3-COR-13 (Nit) | PROPOSE FIX | L8 REUSES `test_lockin_guard`'s scanner helpers. Part of **BN-7.** |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. Where the classification lives (R3-COR-1).**
- `KIND_CLASS` (the `(capability, kind) -> (class, reason)` data of Interface 4) moves from `guard/outbound.py` to `backends/table.py`, next to `DEV_ONLY`, `NOT_PROD` and `NOT_YET_GATED`. It stays pure data, and `table.py` keeps importing no `hadavin_sdk` module.
- `guard/outbound.py` imports `KIND_CLASS` and `NOT_YET_GATED` from `backends.table`. `GATE_REGISTRY`, `NON_TABLE_PATHS`, `RECIPIENT_PATHS`, `TRANSPORT_IMPORTS`, `Gated`, `GateContext` and `gate_context` stay in `guard/outbound.py`.
- **`config.py` (AK1-c) reads `KIND_CLASS` and `NOT_YET_GATED` from `backends.table` only, and never imports `guard.outbound`, `backends.factory`, `limits` or `registry`.**
- `guard/outbound.py` may import `config` and `limits` at module level (probe P-a: clean). The ticket's sentence "if a cycle appears, the builder imports `Config` inside `gate_context`" is deleted, because that fallback still cycles (F1).
- The Import boundary paragraph gains the direction: `config` -> `backends.table` only. `backends.factory` -> `guard.outbound` -> {`backends.table`, `config`, `limits`, `errors`, `pipeline.step`, `llm/masked.py`, `llm/metered.py`, `guard/redactor.py`, `audit.protocol`}. Nothing on that list imports `guard.outbound` or `backends.factory`.
- **New row L17 (in `tests/test_outbound_gate_lint.py`), fresh-interpreter imports.** The row is parametrised over a list written in the test: `hadavin_sdk.config`, `hadavin_sdk.backends.table`, `hadavin_sdk.backends.factory`, `hadavin_sdk.guard.outbound`, `hadavin_sdk.pipeline`, `hadavin_sdk.pipeline.step`, `hadavin_sdk.errors`, `hadavin_sdk.limits`, `hadavin_sdk.registry`, `hadavin_sdk.guard.redactor`, `hadavin_sdk.llm.masked`, `hadavin_sdk.llm.metered`, `hadavin_sdk.app`, `hadavin_sdk.cli`.
  - For each module, `subprocess.run([sys.executable, "-I", "-c", f"import {m}"])` with the package on `sys.path` exits 0, with that module imported FIRST.
  - A module that does not exist yet on the branch is a test failure, not a skip.
  - The list grows when a module joins the import chain.
- **Mutant M-C22** (`config.py`, planted edit): `config.py` imports `KIND_CLASS` from `guard.outbound`. Killed by L17.
- Files that change because of this note: M-C1 (`bedrock_guardrail` re-classified `local`) is applied in `backends/table.py`. L1 and L7 now patch `backends.table.KIND_CLASS`.

**BN-2. Where `OutboundRefused` lives (R3-COR-2).**
- `class OutboundRefused(RuntimeError)` and `OUTBOUND_CODES` are defined in `src/hadavin_sdk/errors.py` (AK1-b), and `guard/outbound.py` re-exports both (`from hadavin_sdk.errors import OUTBOUND_CODES, OutboundRefused`).
- `pipeline/step.py` takes the `REASON_BY_ERROR` key from `hadavin_sdk.errors` and NEVER imports `guard.outbound`.
- `current_object_ref()` and its `ContextVar` stay in `pipeline/step.py`, and `guard/outbound.py` imports them from there. `pipeline/__init__.py` may re-export `step` (probe P-a: clean with this layout).
- The Import boundary paragraph says: `pipeline.step` -> {`errors`, `audit.protocol`, `models`, and the P4b1/P5c error modules}, never `guard.outbound`.
- **P5a's row key becomes `"hadavin_sdk.errors:OutboundRefused" -> egress_refused`.** P5a's identity walk resolves the class through `sys.modules[cls.__module__]` (F2). Interface 8's row text changes to this key (PENDING LEAD 11).
- `errors.py` is a hot file (amendment F6: P5a, P5b3, P5b5); see BN-5.
- **Mutant M-B39** (`pipeline/step.py`, planted edit): `step.py` imports `OutboundRefused` from `guard.outbound`. Killed by L17.

**BN-3. Lock-in literals (R3-COR-3).**
- AK1-b adds `LITERAL_OK` rows to `tests/test_lockin_guard.py` for exactly the `(module, literal)` pairs that rule c (`test_core_logic_names_no_vendor`) reports on the AK1-b branch, each with the reason "a `KIND_CLASS` key names this TABLE kind (AK1)" or "a `RECIPIENT_PATHS` entry names this TABLE kind (AK1)".
- **Expected on the BN-1 layout:** `(hadavin_sdk.backends.table, "anthropic")`, `(…, "bedrock")`, `(…, "gemini")`, `(…, "slack")`. Add `(hadavin_sdk.guard.outbound, "slack")` if `RECIPIENT_PATHS` writes the slack kind as a bare string.
- The builder pastes rule c's output before and after. A row is never added for a literal that rule c does not report, because stale rows fail (`:626-630`).
- An `Entry` field was considered and rejected: it changes every `Entry(...)` in a hot file. A name chosen to fall under the `TABLE` skip (`:560`) was also rejected: it games the scanner.
- Files: AK1-b CHANGES `tests/test_lockin_guard.py` (`LITERAL_OK` only). The file joins the hot-file list (BN-5). Done is unchanged: `test_lockin_guard.py` must pass.

**BN-4. The vendor-screen cites and C2 (R3-COR-4).**
- **"What I read" (`:41`):** `tests/contracts/kinds/detectors.py:50` calls `make` for the JUDGE (`llm_judge`). The `bedrock_guardrail` contract rows build `GuardrailDetector(...)` directly (`detectors.py:89-98`). The one test that calls `make` on the vendor screen is `tests/test_p6_detectors.py:355`, with the AWS environment and `check_filter` patched (`:344-354`).
- **Interface 5 (`:133`), PENDING LEAD 5 (`:357`) and I5:** each cite of `detectors.py:50` becomes `tests/test_p6_detectors.py:355`.
- **C2, second half:** "`make("detector", guardrail_settings())` with `check_filter` and the AWS environment patched as in `tests/test_p6_detectors.py:344-355` still builds; the row needs extra `aws` and is skipped without `boto3`, as that test is." The rule "`make` never refuses `NOT_YET_GATED`" is kept, because that test needs it.

**BN-5. Hot files and merge order (R3-COR-5).**
- The words "new on this list" are deleted: amendment F6 already lists `backends/table.py`.
- **Merge-order-only constraints (not build dependencies).** No AK1 sub-PR is open at the same time as another package that edits the same file. Kit work yields to v1 (order 23 item 5), so the AK1 sub-PR rebases after the v1 package that is open.
  - **AK1-b** shares files as follows:
    - `backends/table.py`: P5b3, P5b4, P5c, P6b2, P6a.
    - `errors.py`: P5a, P5b3, P5b5.
    - `tests/test_lockin_guard.py`: P4d, P5c, P6b2, P6a.
    - `guard/redactor.py`, `llm/masked.py`: P5c.
    - `llm/metered.py`: P4b1.
  - **AK1-c** shares files as follows:
    - `config.py`: P4b1, P5b3, P5c, P6a, P6b1, P6b2.
    - `app.py`: P4c-2, P5c-3, P6a, P6b2.
- At build start, the builder reads each named ticket's Files field and lists in the evidence which of them really edit the file. My list counts mentions only (Honest note). The lead sets the order where two are open.

**BN-6. A closed list of classes per capability (R3-ADV-1; surface cut).**
- `tests/test_outbound_gate_lint.py` holds `CLASSES_BY_CAPABILITY`, written in the test:
  - `secrets`, `signer`, `anchor`, `store`, `audit`: `{"no_text", "local"}`.
  - `detector`: `{"local", "through_llm", "gated"}`.
  - `channel`: `{"recipient", "local"}`.
  - `llm`: `{"gated"}`.
- **A capability that is not a key may carry only `gated`.** So a new capability (`ocr`, `vision`, `embedder`, `reranker`, `scan_reader`) cannot be labelled `no_text`, `local`, `recipient` or `through_llm` without an edit to this lint, which a reviewer sees.
- `local` is allowed where `no_text` is because it is the stricter label: L16 checks it and L2 forbids it when `hosts` is set.
- **L3 rewritten:** for every `(c, k)` in `KIND_CLASS`, the class is in `CLASSES_BY_CAPABILITY.get(c, {"gated"})`.
- **Cut:** `RESERVED_GATED` is DELETED from `guard/outbound.py` and from every place the ticket names it (split table, Interface 4, L3, L10, M-C2, V9's wording). The map's default covers it, and no src code read it.
- **L10 (ii) rewritten:** `REGISTRY_CAPS` = every capability with a `GATE_REGISTRY` row, plus every capability literal in a `make(` call that is not a key of `CLASSES_BY_CAPABILITY`. So `make("embedder"` outside `app.py`, or without `gate=`, still fails (M-C13 and M-C19 keep their killers). `llm` keeps rule (iii).
- **L7 gains two cases.** (a) A test copy of `TABLE` with a new capability `"ocr"` whose kind is labelled `no_text` makes L3 fail. (b) The same with `"ocr"` labelled `gated` passes L3. (b) still fails L5 (no registry row), as intended.
- **M-C2 redefined:** "(meta) L3's lookup gives an unlisted capability every class instead of `{"gated"}`". Killed by L7 (a).
- Interface 4's limit paragraph gains this sentence: "a capability not in the lint's closed map can only be `gated`".

**BN-7. L8: reuse, stdlib network modules, demos default-deny (R3-ADV-2 remainder, R3-COR-13).**
- **Reuse.** L8 imports `module_name`, `_dynamic_target` and `factory_modules` from `tests.test_lockin_guard` (F5) and writes no second AST walker. The ticket's "Existing core code reused" line names them. `test_lockin_guard.py`'s rule a stays THE default-deny for third-party and dynamic imports in `src/`. L8 does not duplicate it, and the ticket says so.
- **Closed list additions (stdlib, any submodule):** `ftplib`, `imaplib`, `poplib`, `nntplib`, `xmlrpc`, `socketserver`, `asyncio`, `multiprocessing`, `ctypes`. On main nothing imports them (F5), so no row is needed.
  - `pipeline/step.py` must not import `asyncio`: BN-12 catches `Exception` only, so `asyncio.CancelledError` propagates without a name. S7 imports it in the test.
- **Demos default-deny (new, L8 part (b)).** A module under `demos/` with no `NON_TABLE_PATHS` row may import only: the stdlib, `hadavin_sdk`, its own demo package (the top-level name of its folder, `askdata` today), and `DEMO_LIBRARIES = {"pydantic", "yaml", "sqlglot"}`, written in the test. Any dynamic import call (`_dynamic_target`) in `demos/` fails. Both rules pass on main (F5).
- **L12 gains two planted cases:** a demo module importing `urllib3`, and a demo module calling `importlib.import_module("x")`. Each makes L8 fail.
- **Mutant M-C21:** "(meta) L8's demos default-deny removed". Killed by L12.
- **Security item (8) rewritten:** "a module that reaches the network through a stdlib module not on L8's list, or through `os.system`/`os.exec*`, is not seen by L8; third-party and dynamic imports in `src/` are refused by `test_lockin_guard.py` rule a, and in `demos/` by L8 (b)."

**BN-8. `content_sha256` and lone surrogates (R3-ADV-3).**
- **Definition:** `content_sha256 = hashlib.sha256(body if type(body) is bytes else body.encode("utf-8")).hexdigest()` (strict UTF-8). It is NOT `models.sha256_hex`, which raises for `bytes` and hashes a JSON-quoted string (F6). A `str` body and the `bytes` of its UTF-8 encoding give the same hash.
- **Refusal:** the `StepInput` constructor encodes a `str` body with strict UTF-8 and raises `ValueError("body: not valid UTF-8")` on failure. The message holds no body text, and the error is raised `from None`. So the property cannot raise, and step (a) of `run_step` cannot raise from it.
- The final-state rule is unchanged: a `StepInput` that cannot be built is not an item. Its caller (AK2a's reader) owns its final state, as for every other constructor refusal (Interface 2).
- **New row S14:**
  - (i) a `str` body with `"\ud800"` gives `ValueError`, and a canary in the body is not in the message;
  - (ii) a `bytes` body's hash equals `hashlib.sha256(body).hexdigest()`;
  - (iii) `StepInput(body="ab")` and `StepInput(body=b"ab")` have equal hashes;
  - (iv) `run_step`'s intent `inputs_hash` equals `content_sha256`.
- **New mutants:**
  - M-A21 (`pipeline/step.py`): `content_sha256` uses `models.sha256_hex(body)`. Killed by S14 (ii) and (iii).
  - M-A22 (`pipeline/step.py`): the constructor's UTF-8 check is removed. Killed by S14 (i).

**BN-9. Reservation vs failure booking (R3-ADV-4; PENDING LEAD 9).**
- The hold stays `request_bound(raw) x W`, exactly as on the llm path (`P4b1.md:269`), because `book_call` is P4b1-b's one function.
- **Security "What the gate does NOT stop" gains item (9):** "a failed send of a kind with `max_attempts` > 1 books `count x attempts x W` against a hold of `count x W`, so a daily cap can be passed by up to `count x (attempts - 1) x W` (2W for count 1 and 3 attempts); the next reserve is then refused. This is the llm path's window (`P4b1.md:269`, its PENDING LEAD 17; order 19 D accepted the whole-call maximum) and applies to every registry kind."
- The Rules money paragraph (`:74`) ends with "…; on a failed send the booking can exceed the reservation and the cap by the window in Security item (9)."
- **G27 gains case (ii):** a raw fake with `REQUESTS_PER_CHAT=1` and `max_attempts=3`. The `worst` passed to `limits.hold` equals `1 x W`. A failing send then books `3 x W` (spy on `book_call`'s `count`, `attempts` and `w`).
- **New mutant M-B38** (`guard/outbound.py`): the reservation is multiplied by `attempts`. Killed by G27 (ii).

**BN-10. `Config` built without its validator (R3-ADV-5; cut, no new refusal).**
- Security gains item (10): "a `Config` built with `model_construct` or changed with `model_copy(update=...)` skips the validator, so the vendor-screen refusal (and every other validator refusal on main: `DEV_ONLY`, loopback, anchors) does not run; no `src/` code does this today (grep). It is in-repo code only, like item (5)."
- Relay to P6a (owner of `config.py`): one rule for the whole `Config` (for example, `app.build` re-validates `cfg` with `Config.model_validate(cfg.model_dump())`) belongs there, not in AK1. Revision 3's cut of the `app.py` refusal stands.

**BN-11. AK1-b's first build step: a delta note (R3-ADV-9).**
- Before any AK1-b edit, the builder writes `handover/evidence/AK1/AK1-b-delta.md`. For each borrowed name, it gives the name as this ticket states it, the merged code's name, file and line, and "same" or the difference. The names are: `mask_leaves`, `book_call`, `current_masking`, `current_scope`, the run context, `Limits.hold`, `Limits.caps`' shape, `request_bound`, the W rule, `billing_outcome`, `AttemptCounts`, `METER_MIN_MICRO`, `Redactor.fingerprint`, `OverBudget(("kill_switch",))`, `SessionClosed`, `MeterError`, `RedactionError`, `_no_training_refusals`.
- It is read in the build-start review (order 19 A); this is not a new review round. Where it differs, the builder follows the merged code, keeps the ticket's rule, and asks the lead only if a rule cannot be kept.
- U1 gains: `Redactor.fingerprint` (`P5c.md:288`) and `OverBudget(("kill_switch",))` (`P4b1.md:32`, `:37`), both from ticket text.

**BN-12. Small test and wording fixes (R3-ADV-6, -7, -8, -10).**
- **M-C9:** the file is `backends/factory.py` (C1's `KIND_CLASS` lookup in `make`), and the killer is G16 (an unclassified kind gives `ungated_kind`). It stays separate from M-B16, which removes the check, while M-C9 replaces it with a fallback.
- **G5 gains (iii)**, run through `run_step` with a gated `probe` step: no masking run ends `needs_person masking_refused`, because `SessionClosed` subclasses `RedactorRefusal` (`P5c.md:210`); no meter scope ends `needs_person step_error`, because `MeterError` is not in `REASON_BY_ERROR` and only its subclasses `OverBudget`/`MeterUnavailable` are (`P4b1.md:31`). Raw calls are 0 in both.
- **C5 gains a `cli._k1b` case (pin):** in dev (k1b replay is dev-only in v1, order 19 D), with a spy on `replay_cmd`, the `llm_judge` detector holds the very llm object passed to `replay_cmd`, and that object is P5c-4's wrapper (`P5c.md:343`). AK1 does not edit `cli.py`, and no mutant is added. If P5c's wrap is missing, this pin fails.
- **Interface 3 (d) wording:** "`run_step` catches `Exception` only, and the `REASON_BY_ERROR` walk applies to it. Every `BaseException` that is not an `Exception` (the four stop requests and any other) propagates unchanged after (e) writes `step_error` best effort."

**BN-13. Cites and the codes row (R3-COR-6, -7, -8).**
- `app.py:89-97` becomes `app.py:90-98` (three places: `:32`, `:155`, `:168`).
- `tests/test_repo_rules.py:295-301` becomes `:296-302`; `:295` becomes `:296`; `:420-421` becomes `:410-411`.
- Files and the split table: "CHANGE `codes.py` (one `OWN_CODES` row, key per BN-2) only if P5a has merged; otherwise P5a's first build step adds it (`P5a.md:39`)."

**BN-14. Test copies for `"probe"` (R3-COR-9).** `make` reads four module-level names of `hadavin_sdk.backends.factory`:
- `TABLE` (`factory.py:36`) and `ALLOWED` (`:52`), the same `dict` objects as in `backends.table`;
- `KIND_CLASS` (BN-1, imported by name from `backends.table`);
- `GATE_REGISTRY` (imported by name from `guard.outbound`).

How the G rows patch them:
- `monkeypatch.setitem(table.TABLE, "probe", {...})` and `monkeypatch.setitem(table.ALLOWED, "probe", frozenset())`;
- `monkeypatch.setattr` of `KIND_CLASS` and `GATE_REGISTRY` on BOTH `hadavin_sdk.backends.factory` and `hadavin_sdk.guard.outbound` (and on `hadavin_sdk.config` for C3), each with a copy that adds the probe rows.

The probe `Entry.factory` string points at a test module. G29 lists these patches as its setup.

**BN-15. "Can build when" (R3-COR-10; PENDING LEAD 10).**
- **AK1-b:** "after AK1-a, P5c-1, P5c-2, P4a-1, P4a-2, P4b1-a, P4b1-b and P4b2-a merge (and P4d, which P4b1 needs); P4a merges last in its chain (order 20 item 4), P5c later".
- **AK1-c:** "after AK1-b, P4c-2, P5c-3, P6a-1 and P6b1 merge".
- **All three:** "and only after a numbered S0 EXIT order that names AK1 (order 23 says the kit takes an S0-EXIT-style standing order after freeze; none names AK1 yet)".

**BN-16. Masking fingerprint changes (R3-COR-11).**
- Rollback for AK1-b no longer says "behaviour-preserving" alone. It adds: "`guard/redactor.py` is a P5c masking source (`P5c.md:237`), so the masking fingerprint and every agent's `config_hash` change on merge and change back on revert."
- The CHANGELOG line for AK1-b says the same.
- The evidence prints the fingerprint on the base and on the head (`AK1-b-fingerprint.txt`), and P5c's own fingerprint test (T1-02) must pass on the head.
- No literal pin is added: P5c replaced hand pins with the computed value on purpose (`P5c.md:67`).

**BN-17. Header and relays (R3-COR-12, plus the BN deltas).**
- The authorities line reads "orders 6-31". Orders 30 and 31 are P1m's. Order 30 items 64 and 66 touch P5c's scope, not AK1's.
- Relay to AK0: `AK0.md:63` cites `AK1.md:288` and `:324`, which are now M-B21 and M-C20. AK0 should cite I2 by name (`AK1.md:342` today) and the AK0 relay line (`:368`).
- **Table delta for the builder (one place):**
  - New rows: S14, L17.
  - Changed rows: L3, L7, L8, L10, L12, G5, G27, C2, C5.
  - New mutants: M-A21, M-A22, M-B38, M-B39, M-C21, M-C22.
  - Redefined: M-C2, and the files and killers of M-C1 and M-C9.
  - Deleted: `RESERVED_GATED`.
- **Totals:** 66 test rows (S 14, G 29, L 16 = L1-L5 and L7-L17, C 7). 82 mutants (A 22; B 38 = M-B1..M-B39 minus M-B11; C 22).
- **Split:**
  - AK1-a: M-A1..M-A19, M-A21, M-A22 = 21.
  - AK1-b: M-A20, 38 B, and M-C1, C2, C3, C8, C9, C10, C12, C13, C14, C17, C18, C19, C20, C21 = 53.
  - AK1-c: M-C4, C5, C6, C7, C11, C15, C16, C22 = 8.

## Positions
- **BN-1 and BN-2 choose existing leaves over new modules.** `backends/table.py` already holds the environment tables "for this reason", and `errors.py`'s docstring states the same purpose. Two new modules (for example `pipeline/context.py` and a classification module) were the alternative. Probe P-a case F2b shows the `pipeline/context.py` leaf is fragile.
- **BN-6 cuts surface.** One lint map replaces `RESERVED_GATED`, and the default is fail closed. It narrows who may skip the gate and widens nothing. Hard rule: least privilege.
- **BN-7 contests half of ADV-2 on a file the reviewer could read** (`tests/test_lockin_guard.py`). It adds only what is missing, and it reuses that file's helpers instead of a second scanner (COR-13).
- **BN-9 keeps one booking rule for every gated call.** Holding `count x attempts x W` on the gate alone would make the gate and `MeteredLLM` differ, which decision 1(c) forbids. Changing both would reopen frozen P4b1.
- **BN-10 states a general limit instead of re-adding the `app.py` refusal** that revision 3 cut. The bypass is not AK1's: it applies to every `Config` validator refusal.
- **BN-16 contests only the literal pin.** The rest of COR-11 is applied.

## Couplings
- **BN-1/BN-3 and every package that adds a TABLE kind** (P5b3, P5b4, P5c, P6b2, P6a, AK2b, AK2c): it adds a `KIND_CLASS` row in the same file (`backends/table.py`). A kind named like a vendor (`^name$` in rule c's pattern) also needs a `LITERAL_OK` row. A new capability needs a `CLASSES_BY_CAPABILITY` edit unless it is `gated` (BN-6).
- **BN-2 and P5a:** the `OWN_CODES` key is `"hadavin_sdk.errors:OutboundRefused"`. Whichever of P5a and AK1-b merges second rebases on `errors.py` (amendment F6).
- **BN-7 and AK2a:** `ingest/` is in `src/`, so `test_lockin_guard.py` rule a already refuses any vendor or unknown library there. AK2a needs no L8 row unless it imports a library on L8's list.
- **BN-9 and AK2b/AK2c:** their kinds inherit the cap window. Their retry layer must still be `llm/retry.py` (unchanged relay).
- **BN-10 and P6a:** the whole-`Config` re-validation, if wanted, is P6a's.
- **BN-12 (C5) and P5c-4:** the `cli._k1b` pin depends on P5c-4's wrap at `cli.py:221` (`P5c.md:343`).
- **BN-15 and the lead's freeze list:** AK1 shows "frozen at rev 3 + build notes; no S0 EXIT yet".
- **BN-17 and AK0:** the relay above. AK0's text is not edited here.

## PENDING LEAD (continuing the ticket's numbering after 6)
Routing rule: an item that touches an owner hard rule (least privilege, thresholds, money, redaction) and that I cannot recommend on checkable evidence is NEEDS LEAD. An item I can recommend that way is INFORM, and the builder takes the recommendation meanwhile.
7. **NEW, INFORM. Freeze with build notes, no round 4.** Round 3 had 9 distinct Majors. Recommend: yes, per order 20 item 6. The banner goes under the revision line. The build-start review reads the ticket, this file and the BN-11 delta note.
8. **NEW, INFORM (least privilege). Closed class map per capability (BN-6).** Recommend: accept. A capability not in the lint's map can only be `gated`, so a new outbound part that was mislabelled fails closed at test time. Cost: a future ticket that truly needs a new non-gated capability edits one lint line, in review. Confidence 85 percent. Reversible (one test constant).
9. **NEW, INFORM (money). Cap window on failed sends with retries (BN-9).** Recommend: keep the hold at `request_bound x W` for gated kinds, as on the llm path, and state the window `count x (attempts - 1) x W`. Reasons:
   - The rule and its window were accepted for the llm path (order 19 D, PL54; `P4b1.md:269`, `:409`).
   - `book_call` is one shared function.
   - Holding the full failure bound would refuse more work early, for example a 3-attempt kind needing 3x headroom.
   
   This is INFORM, not NEEDS LEAD, because the lead already accepted the identical rule. If the lead reads order 19 D as covering the llm only, it becomes NEEDS LEAD, and the alternative is "hold `count x attempts x W` on both paths" (a P4b1 build note). Recommend that the lead adds this window to `owner-visible-limits.md` next to P4b1's. Confidence 75 percent. Reversible before the AK2b merge.
10. **NEW, LEAD (not owner). S0 EXIT for AK1 (BN-15).** Order 23 promises an "S0-EXIT-style standing order after freeze" for kit packages, but no numbered order names AK1. Recommend: a standing S0 EXIT for AK1-a now, effective when its build-start review resolve is done. AK1-a needs nothing unmerged. AK1-b and AK1-c are each effective when their dependencies in BN-15 merge. Only the lead can give it.
11. **NEW, INFORM. `OutboundRefused` moves to `errors.py` (BN-2).** Recommend: accept. It is the only probe-clean layout that keeps `pipeline/__init__.py` free to re-export `step`. Cost: P5a's key string changes, and `errors.py` gains a fourth sharer. The lead relays the key to P5a. Confidence 80 percent. Reversible (one class, one re-export).
12. **NEW, INFORM. `Config` validator bypass stated, not fixed in AK1 (BN-10).** Recommend: accept. P6a decides whether `app.build` re-validates the whole `Config`. Confidence 70 percent.

## Counts
- **Finding ids: 23** (ADV 10, COR 13).
  - Majors: 9 (ADV-1 to -4, COR-1 to -5). No duplicates.
  - Minors: 11 (ADV-5 to -9, COR-6 to -11).
  - Nits: 3 (ADV-10, COR-12, COR-13).
  - No Blocker. No severity changed.
- **Categories:**
  - PROPOSE FIX: 22. One of these has a CONTESTED part (COR-11, the literal pin). Two are surface cuts (ADV-1, which deletes `RESERVED_GATED`; ADV-5, which states a limit instead of adding a refusal).
  - CONTEST plus PROPOSE FIX for the remainder: 1 (ADV-2; the `src/` half is contested with cites).
  - DECLINE: 0. ESCALATE: 0.
- **Build notes:** 17 (BN-1 to BN-17; BN-17 holds the table delta and totals).
- **Totals after the notes:**
  - Rows: 66 (+S14, +L17).
  - Mutants: 82 (+M-A21, M-A22, M-B38, M-B39, M-C21, M-C22).
  - Split: 21 / 53 / 8.
- **PENDING LEAD:** 6 new (7, 8, 9, 11 and 12 are INFORM; 10 is the lead's). None goes to the owner.
- **Probes run:** 3, read-only, on a throwaway copy, not evidence. Tests, lints and mutants run: 0.
- **Fixes applied to the ticket in this step:** 0 (they are build notes). Remaining unaddressed findings: 0.
