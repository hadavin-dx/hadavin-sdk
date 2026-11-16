# AK1 round 3, correctness review

Status: REPORTED (saved by the lead session from the reviewer hand-back, which is model output, not user authority).

AK1 revision 3 (3a3fcca), round 3 CORRECTNESS review. Read-only. I did not open handover/reviews/ or handover/evidence/. I read the ticket in full, LEAD-ORDERS (orders 6-30), amendments A1-A14, the template, and the cited code in <repo>/hadavin-sdk-handover/src and /tests.

Verdict: NOT ready to freeze as written. 0 Blockers, 5 Majors, 5 Minors, 2 Nits. The three cycle and lint Majors (R3-COR-1, -2, -3) are real build failures that a builder would hit on the first run. Each fix is a few lines of ticket text.

Main differs from the cited commit: I cannot confirm the HEAD sha. <repo>/hadavin-sdk-handover/.git is not a directory here, so `git log` was not possible. All line cites below were checked against the files on disk.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | AK1.md:71 (Import boundary), :154 (Interface 11 (ii)), Interface 6a (2) | AK1-c makes `config.py` loop over "every gated kind", but the only gated-kind table is `KIND_CLASS` in `guard/outbound.py`. The boundary paragraph says outbound imports config, limits and llm/*, and `limits.py:9` imports `registry`, which imports `config` at module level (`registry.py:20`). So `config -> guard.outbound -> limits -> registry -> config` is a cycle if config imports outbound at module level. The ticket only covers the `gate_context` import of `Config`. | Put the pure-data classification (gated kinds, or an `Entry` flag or a `GATED_KINDS` frozenset) in `backends/table.py`. That file imports no hadavin module, and `NOT_YET_GATED` already lives there for this reason. `config.py` then imports only from table. Add a cycle test: import `hadavin_sdk.config` in a fresh interpreter, and import `guard.outbound` first. |
| R3-COR-2 | Major | AK1.md:122 (Interface 3 (d)), :119 (a3), :146 (P7) | A second cycle that the Import boundary paragraph misses. `pipeline/step.py` gets `OutboundRefused` as a class key in `REASON_BY_ERROR` (S13 confirms the keys are classes), so it imports `guard/outbound.py`. `guard/outbound.py` imports `current_object_ref` from `pipeline/step.py` (P7). | Move the `ContextVar` and `current_object_ref()` into a leaf module (for example `pipeline/context.py`), or define `OutboundRefused` in a leaf module. Or let `guard/outbound.py` register its row into `REASON_BY_ERROR` at import. State the direction in the Import boundary paragraph and add a fresh-interpreter import test. |
| R3-COR-3 | Major | AK1.md:126 (KIND_CLASS), :164 (Files), :336 (Done) | `tests/test_lockin_guard.py` rule c (`test_core_logic_names_no_vendor`) scans every src module not in `VENDOR_MODULES` (:599-616). Its "bare vendor name" pattern (:520-521) is `^(slack\|aws\|azure\|gcp\|bedrock\|anthropic\|gemini\|openai\|kms\|s3...)(:\|$)`. The tuple keys `("llm","anthropic")`, `("llm","bedrock")`, `("llm","gemini")` and `("channel","slack")` in `guard/outbound.py` are bare string constants that match. `guard/outbound.py` is not in `VENDOR_MODULES` or `LITERAL_OK`. AK1-b will fail that test, and "all gates green" in Done includes `test_lockin_guard.py`. No file list or hot-file entry mentions `tests/test_lockin_guard.py` (A4/F6 list it as hot). Kind names like `bedrock_guardrail` and `aws_kms` do not match, because the next character is `_`. | Add `LITERAL_OK` rows (module, literal, reason) in `tests/test_lockin_guard.py` for the four names. Or store the classification as a field on `Entry` in `backends/table.py`, where the scan skips the TABLE nodes (:552-562). List the file under Files and the hot-file list. Mutant M-C9 and row L1 still apply. |
| R3-COR-4 | Major | AK1.md:41, :133, :235 (C2) | Wrong cite, and an unbuildable row. `tests/contracts/kinds/detectors.py:50` builds `make("detector", JudgeSettings(kind="llm_judge"...), llm=...)`, the judge, not the vendor screen. The guardrail contract rows build `GuardrailDetector` directly (detectors.py:90-98). The test that really calls `make` on the vendor screen is `tests/test_p6_detectors.py:344-355`: boto3 env patched, `check_filter` monkeypatched, then `make("detector", guardrail_settings())`. C2 says "`make("detector", <GuardrailSettings>, llm=None)` called directly with a fake client (as detectors.py:50 does) still builds". `bedrock_guardrail.make` (:61-70) always builds real boto3 clients, so no fake client can be passed in. | Fix the cite to `tests/test_p6_detectors.py:355`. Reword C2 to "with `check_filter` and the AWS env patched as in that test". Keep the "make never refuses `NOT_YET_GATED`" rule, which that test needs. |
| R3-COR-5 | Major | AK1.md:72 (hot files; table.py "new on this list"), :82 (split table), :94 | Dependency and merge order against the amendments is incomplete. Amendment F6 already lists `backends/table.py` as hot (P5b3, P5b4, P5c, P6b2, P6a), `config.py` (P4b1, P5b3, P5c, P6a) and `app.py` (P6a, P6b2). The ticket calls table.py "new on this list". AK1-b edits table.py and AK1-c edits config.py and app.py, but the dependency lists omit P5b3, P5b4 and P6b2. The ticket's own rule is "two packages never edit one file at once". | Add P5b3, P5b4 and P6b2 as "merge order only" constraints on AK1-b (table.py) and AK1-c (config.py, app.py), or state who rebases on whom. Correct the "new on this list" wording. |
| R3-COR-6 | Minor | AK1.md:32, :155, :168 ("app.py:89-97") | Stale by one line. The `sources=` and `tools=` refusals are at `app.py:90-98`. Line 89 is the purge-DSN raise. All other app.py cites match: 82/83/144-146/154/161/162/165/167-169/170/171. | Change to `:90-98`. |
| R3-COR-7 | Minor | AK1.md:71, :42 | `tests/test_repo_rules.py` cites are off. `SECRET_FREE` is at :296 and the module list at :297-302, not :295-301. `:420-421` is a parametrize row for a mixed import, not the "only backends.table allowed" rule; the allow-table rows are :410-411. | Use :296-302 and :410-411. |
| R3-COR-8 | Minor | AK1.md:164 (Files), :84 | `codes.py` and `OWN_CODES` do not exist on main (no `src/hadavin_sdk/codes.py`; P5a creates it). Files says "CHANGE `codes.py`" for AK1-b unconditionally, and AK1-b does not depend on P5a. The sentence "if before, AK1-b adds it" is ambiguous. | Write "CHANGE codes.py only if P5a has merged; otherwise P5a adds the row". |
| R3-COR-9 | Minor | AK1.md:187 (G rows header), :216 (G29) | The test copies are underspecified. `make` indexes `ALLOWED[capability]` (factory.py:52) and `TABLE[capability][kind]` (:36), so a `"probe"` capability also needs test copies of `TABLE` and `ALLOWED`, not only `KIND_CLASS` and `GATE_REGISTRY`. The patch target for the `Final` constants is unstated. | Name the four objects to patch, and where `make` reads them. |
| R3-COR-10 | Minor | AK1.md:94, :81, :84 | "Can build when" for AK1-b names 3 of the 7 direct dependencies. It omits P5c-1, P4a-1, P4a-2 and P4b1-a, and transitive P4d. Order 20 item 4 merges P4a last in its chain and P5c "later". The lead's SEPARATE standing S0 EXIT for kit packages (order 23: "S0-EXIT-style standing order after freeze") has not been given. | List all of them in the "Can build when" cell, and say AK1 builds only after a numbered S0 EXIT for AK1. |
| R3-COR-11 | Minor | AK1.md:164, :338 (Rollback), CHANGELOG | Moving `mask_leaves` into `guard/redactor.py` and editing `llm/masked.py` changes the P5c masking fingerprint, which is part of each agent's config hash (P5c.md:38 says so for its own PRs). AK1 says "behaviour-preserving" and never mentions this. | Add a CHANGELOG and Rollback line: "the masking fingerprint and config_hash change", and a test that pins the new value. |
| R3-COR-12 | Nit | AK1.md:7 | Header says orders 6-29. LEAD-ORDERS now has order 30 (P1m, items 64-66). It does not touch AK1, but items 64 and 66 touch P5c scope. Also `tickets/AK0.md:60` cites `AK1.md:288` and `:324`, which are stale after this revision (a relay). | Say "orders 6-30" and add the AK0 relay. |
| R3-COR-13 | Nit | AK1.md:168 | "Existing core code reused" omits `tests/test_lockin_guard.py`'s existing vendor-import scan (`VENDOR_IMPORTS`, `LIBRARY_IMPORTS`, `import_problems`, :38-110). L8 is a second scanner over a similar closed list (reuse rule). | Say L8 either reuses or intentionally does not reuse that scanner. |

## Verified
Everything below was read in the code or ticket text on disk.
- **Make calls:** `make(` has 25 calls in 3 files: app.py 9 (82, 144, 145, 146, 154, 161, 162, 165, 170), cli.py 11 (line 150 has two; 184, 187, 188, 189, 190, 215, 221, 222, 329) and k1b/audit_sink.py 5 (66, 68-71). There are none in demos/. The other `make` hits are `def make` factories.
- **factory.py:** `Deps` at :18-26, `make` at :29-57, and `ALLOWED` filtering at :50-53.
- **table.py:**
  - `Entry` at :333-344, and the `hosts` comment at :339-341.
  - llm_judge comment at :545, `bedrock_guardrail` at :549, `ALLOWED["detector"]` at :577.
  - `DEV_ONLY` at :593-602 and `NOT_PROD` at :604.
  - table.py imports no hadavin module.
  - TABLE kinds match the ticket's grouping, and `audit` has `chain` (:504).
- **config.py:** imports at :18-21; `entries()` at :74-76; `environment` at :317. The validator refusals are at :365-373, with the DEV_ONLY block at :366-369. `ConfigError` is raised at :453-454.
- **Other main files:**
  - `cli.py:136`, `:212` (`_k1b`), `:222` and `:289`.
  - `deferred.py:33`.
  - `bedrock_guardrail.py:61-70`: client built and `check_filter` run at build; `:98-101` regex mask before `apply_guardrail`.
  - `llm/protocol.py:10` and `:18`.
  - `models.py`: `new_id` :23-24, `sha256_hex` :46-47 with `ensure_ascii=False`, so a lone surrogate really raises at `.encode`. Also `NEEDS_PERSON` :60 and `AuditEvent` :188-190.
  - `audit/protocol.py:19-29` (contract text as quoted).
  - `defaults.py:121` "TENANT" is a mask kind name.
  - `producers.py:55` and `llm/common.py` (:24, :59, :111, :193, :250-251, :255).
- **Network imports:** my grep of the L8 closed list in src and demos found exactly the 21 src modules plus the 2 demo modules the ticket names (the three azure modules included). The ssl-only claim holds (app.py:10, retry.py:16, tools.py:25, secrets_vault.py:21, plus guard/http.py:15). No import uses `from urllib/http/google/azure import ...`, so no spelling slips past L8.
- **Transport importers:**
  - guard.http importers: executor:21, common:19, tools:44, secrets_vault:32.
  - `llm.common` sender importers: slack_channel:23, anthropic:20, bedrock:19, gemini:17, openai_compat:20.
  - Harmless-name importers: loop:27, judge:23, and the demos meter.py:31 and llm_io.py:20.
- **Factory imports:** `backends/builtin.py:8-13` and `guard/judge.py:21-24` import no L8 library. No src or demo module imports a gated kind's factory module (L9 passes on main).
- **Vendor-screen tests:** 37 lines in 8 .py files (12/10/8/2/2/1/1/1). No YAML, JSON or MD under tests/ or demos/ names it. No test loads a `Config` with `bedrock_guardrail` (PENDING LEAD 5's cost of 0 holds).
- **Repo guard tests:** `test_no_hardcoded_values.py` :22-39 and :140-157; `test_k5_producers.py` :78-107; `tests/contracts/conftest.py` :34-36; `audit_chain.py` `chain` :120 and `chain_postgres` :128; `receiver.py` :24-37 (empty bodies).
- **Counts:**
  - 64 test rows: S 13 + G 29 + L 15 (L6 retired) + C 7.
  - 76 mutants: A 20, B 36 (B11 retired), C 20.
  - Split 19 / 50 / 7: A1-A19; A20 + 36 B + 13 C (C1, 2, 3, 8, 9, 10, 12, 13, 14, 17, 18, 19, 20); C4, 5, 6, 7, 11, 15, 16. Every mutant is covered exactly once.
  - Every killer row named in the mutation table exists.
- **Template:** all 17 fields are present and in template order.
- **Times:** every UTC-to-IST conversion in the header and CHANGELOG is correct (+5:30).
- **Orders:**
  - Order 20 item 6's round cap and the "one more round" condition are quoted correctly.
  - Order 20 item 4 branch naming is correct.
  - Orders 6(e), 23 items 1 and 4, 27 items 54/56/57/63, and 22 items 22 and 30 are used as written.
  - No amendment A1-A14 retires P7b, and only A3 mentions it.
  - `StrEnum` is fine (requires-python >=3.12, `models.py:13`), and `new_id` prefixes (`run`, `pln`, `apr`, `evt`, `k1b`) fit `ITEM_ID_PATTERN`.
- **Frozen-ticket cites, spot-checked:** P5c.md:272 (run context with principal), :281, :286, :288, :342, :343; P6b1.md:196; P5a.md:39; P4c.md:177; P4b2.md:57 and :17; P4b1.md:102 and :298; AK0.md:60; AK2a.md:351. P5c.md:274/335 confirm `Runtime` requires `MaskedLLM(MeteredLLM(raw))`, so AK1's wrap-order claims C4/C5 are consistent with P5c.
- **Secrets:** I found no real-looking secret in the ticket. The values are placeholders such as `person-1@example.invalid` and `<EMAIL_9>`.

## Not checked (UNVERIFIED)
- I did not run any test or lint. Whether L8, L16, `test_no_hardcoded_values` or `test_lockin_guard` pass after the changes is by reading only, except R3-COR-3, which follows from the pattern and the scan loop.
- `src/hadavin_sdk/pipeline/`, `guard/outbound.py`, `guard/redactor.py`, `llm/masked.py`, `llm/metered.py`, `meter.py`, `money.py` and `codes.py` do not exist on main. Every name taken from P4a, P4b1, P4b2, P4c, P4d, P5a, P5c, P6a or P6b1 (`book_call`, `current_masking`, `current_scope`, `Limits.hold`/`caps`, `billing_outcome`, `AttemptCounts`, `request_bound`, the W rule) is from ticket text only.
- Cross-ticket line cites I did not open: P4b1.md :107, :158, :262, :270, :51; P4b2.md :111; P4d.md :76, :292; AK2a.md :48, :50, :61; P5c.md :281 beyond the lines read above; plan-v1.md:93.
- The bodies of `llm/gemini.py`, `llm/openai_compat.py`, `sources/` and the rest of `llm/common.py` (U6). Whether any name in `llm/common.py` other than the four listed opens a connection.
- The multi-line import at `llm/bedrock.py:19` and `llm/openai_compat.py:20` (the imported names).
- Whether `P4b1-b`'s and `P5c-2`'s `ContextVar`s are module-level (U2), the name of P5c-3's redactor object (U3), and whether P5c-3/P5c-4 edit `llm/masked.py` (U4).
- The `mutation_runner` command line (P1m, PR 61, unmerged); no `tools/mutation_runner.py` exists on main.
- Round 1 and round 2 review contents (excluded by the independence rule), including the "9th file was a .pyc" claim and the "8 Majors vs header 6" remark.
- Whether the lead has answered PENDING LEAD 2, 4, 5 or 6. No order or amendment I read answers them.
