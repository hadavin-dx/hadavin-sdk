# Cloud ledger

| id | package | severity | summary | status | verifying artifact | reviewed commit |
|---|---|---|---|---|---|---|
| BL-core-p1-r1-adv-A1 | P1 | BLOCKER | P1b "Decided choices"; Interface; P1b gap 1: The ticket contradicts itself on identity keys. It says `identity_key` is "the single stable key" and, in the same section, that the identity key "kee... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A2 | P1 | BLOCKER | P1b gap 1 and gap 5 ("extra case readings"): The key-set size is unbounded or under-covered. "Extra case readings" for case-ambiguous letters is not defined. With a per-position cross product, n... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A3 | P1 | BLOCKER | P1a Errors; Length cap; stored keys: Every new error is a `ValueError` subclass: `TextTooLong`, `FoldVersionMismatch`, `TextnormError`. A DENY caller that does `except ValueError:` (routi... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A4 | P1 | MAJOR | P1a `FOLD_VERSION`; Pinned Python; Decision 2: The pin is not enforced where production runs. The memo says "checked at import against the pinned value"; the ticket drops this. The pin exists only... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A5 | P1 | MAJOR | P1a stored keys; F3 "goes to a person": "Goes to a person" is not implementable in P1, and the stored form defeats the alternative. Keys are SHA-256 digests with no raw text kept, so there i... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A6 | P1 | MAJOR | P1a `parse_stored`/`check_stored`: Malformed or attacker-controlled stored strings leak into error messages. The ticket claims `FoldVersionMismatch` "message: both version strings, whic... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A7 | P1 | MAJOR | P1b gap 1 fix: "Table, casefold, table again, to a fixed point" is incomplete and unbounded. `casefold` can reintroduce dropped categories or chars needing NFKC (U+0... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A8 | P1 | MAJOR | P1b gap 2: The order is ambiguous: "apply the table to a code point before the Cn drop". If the table is applied before the drop for every category, any table en... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A9 | P1 | MAJOR | P1a table integrity; Decision 1: The 677 (later ~1,700) entry table is a security artifact with no CI integrity check. The data file is not committed, the generator test is "run by th... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A10 | P1 | MAJOR | P1a differential test: The test has no independent oracle and its own rule contradicts itself. "Every pair any variant equates must be equal AND every pair any variant keeps... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A11 | P1 | MAJOR | P1a views; empty keys: Empty and non-Latin keys are unspecified. `id_key` uses `[^A-Z0-9]` deletion, so every id in CJK, Arabic, Cyrillic-without-mapping, etc. becomes `""`.... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A12 | P1 | MAJOR | P1b Intake `_f` move; `id_key` loose: `id_key(loose=True)` equates O/0, I/1/L, S/5, B/8, Z/2, G/6, Q/9. The ticket plans for Intake to move its "`_f` money-path comparison onto `line_view`... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A13 | P1 | MAJOR | P1b gap 7, nested entities: The 8-round limit is a fixed number that an attacker can exceed. After 8 rounds a still-changing string is silently used. `&amp;` x9 followed by `#65;... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A14 | P1 | MAJOR | P1b cache: The cache design is a sentence. `lru_cache` cannot bound by bytes. How size is counted (`len`, `getsizeof`, UTF-8) is unspecified, and no default name... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A15 | P1 | MAJOR | P1a length cap and time bound: The cap does not bound time. Only `fold`, the views and `has_mixed_script` are listed; `names_equal` and `allow_equal` (which run `_canon` before the... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A16 | P1 | MAJOR | P1a mutation runner and scope: A "small pull request" it is not. P1a carries about 870 lines of module, generator (129), 13 moved tests, three new test files, 3 fixtures, a manifest... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A17 | P1 | MAJOR | P1a loud-failure test: The test, as specified, is built from strings the test crafts itself. The P1a to P1b case ("a P1a-algorithm key read by P1b code raises") needs a froz... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A18 | P1 | MINOR | P1a privacy claim: "Stored keys are SHA-256 digests, never the folded text" is presented as personal-data protection. An unsalted digest of a name or an account number i... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A19 | P1 | MINOR | P1b gap 5: "Dropped characters become a space" is ambiguous (one word, one meaning). NFKD runs first, so a precomposed "é" splits into `e` + a mark, and the mark... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A20 | P1 | MINOR | P1a/P1b hard-coded values: The values 20,000, 8 rounds, the cache default, 3.13 and the golden are stated in several places. The cache default and the entity limit have no name... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A21 | P1 | MINOR | P1a fail-before: Copying the P1a tests into the PR50 worktree fails at import (`FOLD_VERSION`, `view`, `stored_key` do not exist), not at an assertion. That proves not... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A22 | P1 | MINOR | P1a docs: `has_mixed_script` uses a curated prefix list of script names (Runic, Tamil, Bopomofo, Ethiopic, Sinhala and others are absent). The ticket calls it t... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-adv-A23 | P1 | MINOR | Ticket wording: Mixed terms: "scan view" (one key vs a tuple vs `scan_views`), "identity key" vs "identity view", "key" for both a string and a digest, "version" for... | OPEN | reviews/P1-round1-adversarial.md | e35eb4d |
| BL-core-p1-r1-cor-C1 | P1 | MAJOR | P1a Files; Done gates: Moving `_confusables.py` into core turns the repo guard test red. The file's header holds `https://www.unicode.org/terms_of_use.html`. The guard scans... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C2 | P1 | MAJOR | P1b gap 4 row and Interface ("`id_key` gains dash/: The `id_key` change is a no-op, and its fail-before row cannot fail. `id_key` is `squeeze(loose=True)`, and `squeeze` strips every non-`[A-Z0-9]` char... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C3 | P1 | MAJOR | P1b "Decided choices" vs Interface: The identity key contradicts itself. It is "ONE stable key" (F4, gap 1, `identity_key(raw) -> str`), yet "the identity key keeps BOTH readings (3 and... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C4 | P1 | MAJOR | P1b "Fail-before (must fail on `2e8a28c`)": The P1b fail-before tests, as worded, call names that do not exist on 2e8a28c (`identity_key`, `scan_views`, `line_view`, `id_key`). They would fail w... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C5 | P1 | MAJOR | P1a Tests list (13 "textnorm-only" tests): Two of the 13 moved tests are not textnorm-only. `test_the_micro_and_ohm_signs...` calls `check_text(...)` from `guard.egress_text`. `test_a_newline_o... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C6 | P1 | MAJOR | P1a Tests / "Vendored Unicode data: NOT in P1a": The ticket moves the generator tests (879, 908, 2068) into P1a but does not vendor `tools/data/confusables.txt`. `test_the_generator_reproduces_the_ch... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C7 | P1 | MAJOR | P1a Fail-before: The claim "non-`str` input not a clear TypeError" is false for PR #50. `fold(123)` and `fold(None)` already raise TypeError from `unicodedata.normaliz... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C8 | P1 | MAJOR | P1b Tests ("`line_view` never grows the text beyon: The property is false as written. NFKC (applied after the entity step) expands text: U+FDFA gives 18 characters, and `&#xFDFA;` is 8 characters before... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C9 | P1 | MAJOR | P1b Interface (`scan_views`): The key-set is undefined. "for case-ambiguous letters the extra case readings" can be read as 2^k keys for k ambiguous letters (20,000 "η" characters... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C10 | P1 | MAJOR | Header and all sections: which PR #50 head: The ticket says "PR50 head = 2e8a28c" but quotes numbers from the local head 748849c without saying so. The two heads differ outside `textnorm.py` and... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C11 | P1 | MINOR | P1a/P1b Files list: The Files list is incomplete. It omits `tests/textnorm_mutants.py` (the evidence command runs it), the mutation runner and judge files (only mentioned... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C12 | P1 | MINOR | P1b Mutation plan: The 27 reused mutants match exact source strings (for example `.translate(_DIGITS).translate(_TABLE)`, the `_DROP_CATEGORIES` set text). P1b rewrites... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C13 | P1 | MINOR | Gap 7 source claims: Line numbers are wrong. `_unescape` is at lines 447-454, not 431-438 (431-438 is inside the message table). `_f` is lines 465-481, not 465-486 (484+ i... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C14 | P1 | MINOR | Template fields: "Extended review (no round cap): yes/no" is not stated (Tier A text only). The template's order is not kept at top level (Files, Tests, Mutation, Evid... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C15 | P1 | MINOR | Mapping table (verified claim): "verified by reading both files": there is no PR #49 file on disk in any snapshot, so the PR #49 signatures and semantics cannot be checked. Memo-1 gi... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C16 | P1 | MINOR | Interface (cap and TextTooLong): Cap coverage is unclear. The cap is stated for `fold`, the views and `has_mixed_script`. `allow_equal` runs `a == b`, then `_canon` (not capped), then... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C17 | P1 | MINOR | Interface (`FOLD_VERSION`, `stored_key`): `tbl=41740c11` is the sha of the generated `_confusables.py` file, not `DATA_SHA256` (6ed3ee96, the UTS #39 data). "Built at import" would need file a... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C18 | P1 | MINOR | Tests (P1a): The time-ratio and 8-thread tests are in `test_textnorm.py` with no `perf` marker. CI runs `-m "not live and not perf"` and a separate blocking perf s... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C19 | P1 | MINOR | Evidence commands: They differ from CI: CI runs `ruff check src tests demos` and `bandit -q -r src demos -ll`; the ticket runs plain `ruff check` and `bandit -ll -r src`... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p1-r1-cor-C20 | P1 | MINOR | Hot files / Decision 6: "P2a and P2d also touch `textnorm_manifest.json`" is not in memo-5 (only P1 is listed for it, line 28). The ticket does not say whether P2a, P2d, P3b... | OPEN | reviews/P1-round1-correctness.md | e35eb4d |
| BL-core-p2a-r1-adv-A1 | P2a | BLOCKER | "Who may stop, who may reset"; Security notes: The allow-list checks a caller-supplied string, not an authenticated identity. It is a typo guard, not access control. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A2 | P2a | BLOCKER | "Who may stop" plus Rollback (1): Deny-all `stop_identities` makes the emergency stop unavailable by default. The ticket is also inconsistent: only `Limits.reset` is said to check, yet... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A3 | P2a | BLOCKER | Interface: `release`, audited reset, labelkey: Masking is applied in the gate, but the identity check is in `Limits.reset`. The gate calls `Limits.reset(self._lbl(by))`, so `reset_identities` is co... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A4 | P2a | MAJOR | "Personal data in principal": Masking is not at the choke point. `Limits.stop/reset` and the `kill_switch.by` column store whatever `by` the CLI gives, e-mail included, in clear. T... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A5 | P2a | MAJOR | `label_key` / keyed-label fix: The fix is sound (HMAC-SHA256, truncated to 128 bits) but incompletely specified. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A6 | P2a | MAJOR | "Audited reset" / reset race: The compare-and-set is opt-in. The CLI path and plain `Limits.reset(by)` have `expect=None`, which is an unconditional clear. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A7 | P2a | MAJOR | `release`/`engage` semantics: The CAS token can be wrong, and it disappears silently. Both failures make `release` unconditional. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A8 | P2a | MAJOR | `release` re-stop: In `release`, the reset is committed to the store before the gate checks `_gen`. If an engage ran meanwhile, the stop is written again. Between those... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A9 | P2a | MAJOR | "Nothing in core src calls StopGate" / Open point : Module exists, nothing enforces it, and no package owns the wiring ("the lead adds it to P4c or a new row"). For a Tier A control that is a paper cont... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A10 | P2a | MAJOR | Test plan (b), (a), (d): The process tests are vacuous or non-deterministic. (a) "final row equals one of them" passes with an unconditional upsert. (b) cannot force "B writes... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A11 | P2a | MAJOR | In-flight barrier: The barrier is per process. `engage` waits only for this process's `_inflight`. Test (c) covers threads in one process. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A12 | P2a | MAJOR | Open point 2 / row store: `RowStore` is memory-only and has no consumer in core. Nothing imports it except `testing/contracts.py`. The `config_view` has none either, so the onl... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A13 | P2a | MAJOR | Sub-PR coupling and file ownership: Internal contradictions. P2a-1 CREATEs `tests/stop_state_mutants.py`, the runner and `testing/mutation.py`. P2a-2 also adds rows to `stop_state_mutant... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A14 | P2a | MAJOR | Hot files: P2a-1 touches `limits.py`, three store files, `config.py`, `cli.py` and `CHANGELOG.md`, and has to wait for P4d. F6 does not list P2a for `config.py`/... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A15 | P2a | MAJOR | Rollback / non-revertible semantics: Deny-all lists lock out every reset on first deploy. "Old code ignores the list" is only a loud failure if config rejects unknown keys. I saw `extra="... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A16 | P2a | MAJOR | Unreadable store / fail-safe: The fail-closed claim has a gap. The ticket itself marks as UNVERIFIED what `agent_loop._limits_stop` does when `limits.blocked()` raises. The core `L... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A17 | P2a | MAJOR | "Mutation runner carried from PR #50": The runner in `src/hadavin_sdk/testing/mutation.py` ships in the wheel. It rewrites source files, which the repo's own rule says leaves a mutated `src... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A18 | P2a | MINOR | Interface: stop reason: There is no reason and no stop-reason field. Two stops with different reasons overwrite `by` and `ts`; the first one's context survives only in the au... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A19 | P2a | MINOR | Hosted adapter outline: The trigger "a client asks" is vague, and there is no stop-backend interface. `Limits` is a concrete class, so the outline has nothing to implement ag... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A20 | P2a | MINOR | Clock / `ts`: The CAS token uses `ts`, set client-side (`default_factory=now`). Equality on Postgres timestamptz round-trip is untested (tz-naive vs aware, precisio... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A21 | P2a | MINOR | Step 0 / unnamed failing test: The failing test is unnamed, and the builder is asked to "fix at its cause" outside P2a's files. | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-adv-A22 | P2a | MINOR | Wording: "Audited reset" is used for both a gate release and the CLI; "stop identity" and "reset identity" are called "identities" while they are name strings;... | OPEN | reviews/P2a-round1-adversarial.md | b300b6b |
| BL-core-p2a-r1-cor-C1 | P2a | BLOCKER | Interface "Who may stop, who may reset" (L26); Sec: The authorization rule is not buildable as written. (a) It says `Limits.reset` is the "shared choke point" and checks the name. But the gate never pas... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C2 | P2a | MAJOR | Interface "Personal data in principal" (L25); Fail: The e-mail fix covers only the gate path (`_label`). The CLI path (`limits stop/reset --by X`, the main reset path) writes `principal=by` raw into the... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C3 | P2a | MAJOR | Depends on (L9): The ticket says "P4d then P2a-1 (lead decision, amendment A9 F6 and memo-5)". Neither document says that. F6 lists `store/postgres.py` as (P4d, P4b1,... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C4 | P2a | MAJOR | Source / Files / Done: split into 3 PRs (L31-33, L: The three PRs are not separable as written. `tests/stop_state_mutants.py`, `testing/mutation.py` and `tools/mutation_runner.py` are CREATED in P2a-1 (... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C5 | P2a | MAJOR | Interface `release` (L23); Fail closed (L28): The compare-and-set silently degrades to an unconditional clear. `_wrote` is set from `_read_switch()`, which returns None on any read error or if the... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C6 | P2a | MAJOR | Mutation plan (L52-55); Source (L14): The counts are wrong. "189 rows" in `tests/promoted_mutants.py` contradicts the lead's own evidence: ledger BL-core-pr50-ev5-002 says "261 of 262 good... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C7 | P2a | MAJOR | Files (L31): The change list is incomplete for deny-all. These existing tests call `Limits.reset` or the CLI reset with an arbitrary name and would start failing:... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C8 | P2a | MINOR | Weak mutant row (L55): The conclusion is right: the row is weak at PR50-local and not weak at PR50-pushed. The mechanism is stated wrongly. The `Mutant` for `rows: no defaul... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C9 | P2a | MINOR | Files, `cli.py` (L31): The description of today's CLI is not exact. It does not report "any non-audit error as store unreachable": `_kill_switch_store_down` returns exit 4 (... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C10 | P2a | MINOR | P2a-3 (L33): "Only link ... `ConfigHolder.swap(expect=)` lets two administrators change the two allow-lists" describes behaviour no file implements. `Config` is a... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C11 | P2a | MINOR | Open points 4, 3 and UNVERIFIED in Existing code (: "Needs a profile flag; P6a owns profiles" is partly wrong. `Config.environment` (dev, pilot, prod) already exists, with a refusal list in `_cross_chec... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p2a-r1-cor-C12 | P2a | MINOR | various: Small factual slips. `limits.py:36-51` (L12) is 43-51 on ce70eb5 (`stop` 43-46, `reset` 48-51). agent-killswitch has 21 `.py` source files, not 20 (th... | OPEN | reviews/P2a-round1-correctness.md | b300b6b |
| BL-core-p3a-r1-adv-A1 | P3a | BLOCKER | Interface `order_problems`; the message `renumber : The refusal tells the operator to do something the same ticket's gap rule forbids. A file below the highest applied number can only be refused when th... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A2 | P3a | BLOCKER | `folder_problems`: "each entry must be a regular f: The rule runs inside `migrate()` on the installed package folder at production runtime, not only in CI. Installers that link files into site-packages... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A3 | P3a | MAJOR | `folder_problems(folder: Path)` vs `migrate()`: `migrate()` today calls `_migration_files()` with no argument and gets a list. Three existing tests replace it with `lambda: files` to inject bad list... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A4 | P3a | MAJOR | CHANGELOG correction (Open point 2): The ticket names only CHANGELOG lines 10-11. The same false `0006_evidence` rename appears at lines 38, 45 and 52: "the evidence migration is `0006_ev... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A5 | P3a | MAJOR | Previous-release test (schema-compat, layer 1): The test gives false confidence. It records "tables, columns, types, nullability" and the ticket cites `information_schema`. Missed: column defaults (... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A6 | P3a | MAJOR | Layer 2 of the previous-release test: Layer 2 is useless exactly when needed. Any migration that adds a table also needs a `GRANTS` row. The old `check_grants` then reports "created by a m... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A7 | P3a | MAJOR | Safe escape and rollback (attack 1): Lock-out scenarios are not covered by any documented route. (a) Rolling back by reverting code after a later migration ran: the old image's `migrate`... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A8 | P3a | MAJOR | Test plan on Windows (the studio laptop): (1) FAIL-BEFORE 3 says `0002_b.SQL` is "ignored today". On Windows and macOS `glob("*.sql")` is case-insensitive, so it is matched and refused by the... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A9 | P3a | MAJOR | Manifest cost vs benefit: The hash catches an edit to a listed file but not an edit to a line and its file together (Open point 4 leaves this to a manual diff). It adds a manif... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A10 | P3a | MINOR | `order_problems` malformed input: `order_problems(applied, files)` is pure and tested in isolation. A hostile or hand-edited ledger name that does not match `NAME` (non-ASCII digits, e... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A11 | P3a | MINOR | Hard-coded values: The 20-problem cap and the `[0-9]{4}` pattern (so 9999 migrations) are literals. The repo has `tests/test_no_hardcoded_values.py`; the ticket does not... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A12 | P3a | MINOR | Mutation plan: No mutant targets the lock order. M8 removes the `order_problems` call. A mutant that moves `order_problems` before the advisory lock or reads `done`... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A13 | P3a | MINOR | Hot-file ordering and later packages: P3b and P3c builders hit the manifest and `tests/test_k2_migrations.py` together, and the spec says each renames its file and its manifest entry by ha... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-adv-A14 | P3a | MINOR | Wording: "A refusal rolls back (the whole run is one transaction)" is fine, but the ticket also says "partial failure" never occurs. A migration using statemen... | OPEN | reviews/P3a-round1-adversarial.md | 1ed7499 |
| BL-core-p3a-r1-cor-C1 | P3a | MAJOR | Interface, bullet "migrate() calls folder_problems: "As now" is false. Today `migrate()` evaluates `check_ledger(files) + check_grants(files)` in one expression, so `check_grants` always runs. The ticke... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C2 | P3a | MAJOR | Interface (`folder_problems(folder)` vs `check_led: The signatures do not fit together. `folder_problems` takes a folder, `check_ledger` takes a list of paths, and the ticket never says which one `migra... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C3 | P3a | MAJOR | Tests, "FAIL-BEFORE (must pass on new code and fai: Items 1, 5 and 6 can only fail on ce70eb5 by ImportError, because `migration_numbers`, `order_problems`, `folder_problems`, `check_migration_numbers`... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C4 | P3a | MAJOR | Tests, "Previous-release test"; Done: The plan row (plan-v3 section 6 P3a and section 10) wants a test that the previous release's code reads the new schema or fails loudly. Layer 1, the o... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C5 | P3a | MAJOR | Security notes ("`"breaking": true` manifest flag": The flag is mentioned once. It is not in the Interface (`Manifest` fields), the Tests, or the mutants. It is also tied to the manifest, which is condi... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C6 | P3a | MINOR | Mutation plan, M8: The second killer cannot kill M8. `order_problems` needs the ledger, which is only read after `connect()`, so a test with a patched `connect` or the `... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C7 | P3a | MINOR | Several cited line numbers and counts: (a) "asserts at least five files, as `tests/test_k2_migrations.py:30`": it is `assert len(files) >= 4` at line 31. (b) `mig.MIGRATIONS` "used in `test... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C8 | P3a | MINOR | Interface, `order_problems`: "every file whose name is not in `applied`": `applied` holds stems (`done = {r[0] ...}`, ledger stores `path.stem`). A file's `.name` ends in `.sql`,... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C9 | P3a | MINOR | Header (path class, review depth), Done: Three inconsistencies. (1) "Path class: other" with "Extended review (no round cap): yes". Studio rule 8 says non-money/redaction/security packages ge... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p3a-r1-cor-C10 | P3a | MINOR | Tests, FAIL-BEFORE 3 and 4; Evidence: Both depend on the OS. `Path.glob("*.sql")` is case-insensitive on Windows and macOS, so `0002_b.SQL` is already refused there and FAIL-BEFORE 3 would... | OPEN | reviews/P3a-round1-correctness.md | 1ed7499 |
| BL-core-p4d-r1-adv-A1 | P4d | BLOCKER | Interface `reserve_spend`; "Existing core code reu: The ticket tells the builder to reuse the `add_spend` upsert pattern but gives no statement shape for the cap check. The natural form is `INSERT ... O... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A2 | P4d | BLOCKER | `settle_spend`; R2 list; M6: Settle-once is described as sequential ("first call sets status settled"). Nothing says the first-call decision must be one atomic claim, and no concu... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A3 | P4d | BLOCKER | `reserve_spend` idempotency ("Same id and same con: The rule says nothing about the status of the existing reservation. If a content-derived id is reused (for example the same prompt hash), the replay r... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A4 | P4d | MAJOR | Open point 1; Interface; Files (migration, postgre: Authority conflict. Amendment F2 (which wins over any message) says P4b1 holds "the Postgres implementation inside store/postgres.py (after P4d)", and... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A5 | P4d | MAJOR | Interface; "Not in P4d": The interface is not sufficient for P4b1/P4b2, so P4b1 will edit the signature of a method P4d just closed (hot file `store/postgres.py`). Missing: (a... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A6 | P4d | MAJOR | Interface `reserve_spend` errors; "Hostile inputs": Input rules are incomplete and will diverge between backends. (a) No type rule: a float 0.1 is converted to NUMERIC by Postgres (expected) but raises... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A7 | P4d | MAJOR | Hostile inputs ("for add_spend/add_cost current be: The suite pins the permissive behaviour: a contract test asserts a negative `add_spend` is accepted. NaN is not mentioned at all. Negative spend lets... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A8 | P4d | MAJOR | Files (migration 0006 and GRANTS row); Security no: The ticket gives no DDL. Runtime gets `SELECT, INSERT, UPDATE` on the whole table, so any code path or compromised runtime can rewrite `reserved_usd`,... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A9 | P4d | MAJOR | Rollback: "Old code ignores the new table" is wrong for money. Counters in `spend` and `spend_month` include open reservations (the ticket says so for `spend_to... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A10 | P4d | MAJOR | Interface (first paragraph "a store never lets a d: The ticket contradicts itself. The new Protocol rule says no driver exception escapes. R6 expects the new methods to raise a driver error classed NOT... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A11 | P4d | MAJOR | Security (lock-in decision D1, guard changes a-d);: `pg_driver()` returns the psycopg module to any test, so a test calls `pg_driver().connect(...)` without any `import psycopg`; the "only kinds/ may im... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A12 | P4d | MAJOR | Scope ("Files to create, change, delete"): One pull request holds: Store Protocol, two backends, a migration and grant change, 2 money methods, 8 contract gaps, behaviour changes to existing me... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A13 | P4d | MAJOR | Hostile inputs (ids over 2.7 KB, empty ids, NUL, s: The list names cases but gives no rule or expected result for them. Details. (a) An empty `reservation_id` would make every unkeyed call share one res... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A14 | P4d | MAJOR | `require_backend`; R9; Evidence: "Silent skip must fail in CI" is only partly closed. `CI` is checked by being "set": `CI=false` or `CI=0` counts as set. Other skip routes stay: modul... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A15 | P4d | MAJOR | Mutation plan; R2; R7; R9; settle clamp: Mutants and tests that survive or pass vacuously. (a) M4 ("cap check in Python") is killed only by a thread race, which is timing-dependent, so it can... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A16 | P4d | MAJOR | R9 (`check_step_name`); Interface: Python `re` and Postgres POSIX regex disagree on `$`. The Postgres CHECK is `step ~ '^[a-z_]+$'` (0003:31); Python `re.match(r"^[a-z_]+$", "abc\n")` a... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A17 | P4d | MAJOR | Interface `reserve_spend`; R2: Lock order and deadlock/retry are unspecified. Reserve and settle both lock day then month rows, but the reservation row's place is open: if one path... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A18 | P4d | MAJOR | Files (migration 0006 and `migrate.py` row); R5; R: (a) The file name `0006_...` is hard-coded while A3 says "whoever merges first takes the next free number" and P3b/P3c also want one. If the branch is... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A19 | P4d | MAJOR | R2; "Not in P4d" (8-process test is P4b1's): P4d closes as "Tier A done" with only in-process, multi-connection tests. If P4b1's 8-process test finds an overshoot in P4d's SQL, a closed Tier A pa... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A20 | P4d | MINOR | Security (tenants, R8): The deferral to P7b is acceptable for isolation (no tenant concept on main, A3 verified), but the new money table is keyed by a global `reservation_id... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-adv-A21 | P4d | MINOR | Interface; wording: (a) Settle with a different amount on an already-settled id silently returns the first result, but reserve with different content raises `ReservationC... | OPEN | reviews/P4d-round1-adversarial.md | d2d658b |
| BL-core-p4d-r1-cor-C1 | P4d | MAJOR | Contract rows R6; Rollback; Files (0006): R6 tests the wrong direction. memo-3 gap 6 and plan-v3 line 193 ("each migration includes the downgrade-read test of P3a") require old code against th... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C2 | P4d | MAJOR | Files to change: Adding 0006 breaks an existing test the ticket never names. `test_p2_postgres.py:290` asserts `migrate(fresh_dsn) == ["0004_audit_checkpoint_meta", "0... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C3 | P4d | MAJOR | Interface (error rule); R6; Files (`_insert`): The ticket contradicts itself and the plan to implement it is thin. The Protocol rule says "a store never lets a driver exception type escape". R6 exp... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C4 | P4d | MAJOR | R2; Mutation plan (M6): The money races that P4b1 depends on are untested. R2 races `add_spend`, `reserve_spend` against a cap, `transition`, `create_run`, `record_decision`,... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C5 | P4d | MAJOR | Interface (old methods "pinned"); Hostile inputs; : The shared money counter can be poisoned through the unvalidated old path. `add_spend` and `add_cost` accept NaN, Infinity and negatives. Postgres NUM... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C6 | P4d | MAJOR | Security, Lock-in (b); Open point 2: The guard rule as written cannot go green. Rule (b) says "only `tests/contracts/kinds/` may import psycopg". Eight files under `tests/demo_askdata/` i... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C7 | P4d | MAJOR | Files (the six-file `pg_driver` change): "Replace their `import psycopg` lines ... bodies unchanged" does not keep the six files green. (a) There are 12 more `from psycopg ...` lines to chang... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C8 | P4d | MINOR | Header ("Path class"): The ticket labels the path "other" while saying "spend counters, which are money". Template and plan classes are money/redaction/security/other; the w... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C9 | P4d | MINOR | Files (0006), Security: The 0006 DDL is not given. For a Tier A money table the ticket should state the columns, the PK on `reservation_id`, CHECKs (`reserved_usd >= 0`, stat... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C10 | P4d | MINOR | Verified facts, Security: Three wrong citations. (1) `backends/table.py:597 DEV_ONLY` should be :593 (the set) and :599 (`("store","memory")`); A8 says 593. (2) "refused UPDATE... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C11 | P4d | MINOR | Contract rows R1, R4, R5; Tests summary: "FAIL-BEFORE rows named in R1, R4, R5, R9" is misleading. Duplicate `create_run` is already `StaleState` on both stores (memory.py:53, postgres.py:241... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C12 | P4d | MINOR | Rollback / behaviour changes: One side effect is undeclared. New Protocol methods make `missing_methods()` list them for any custom store, and `app.py:147` then refuses to start. T... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C13 | P4d | MINOR | Hostile inputs; R9 step grammar: The Postgres CHECK `step ~ '^[a-z_]+$'` is end-anchored. A Python `re.match(r"^[a-z_]+$")` also accepts "abc\n" (trailing newline), so `check_step_nam... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C14 | P4d | MINOR | Interface (A9 B1 rounding / exponent): A9 B1 says "Decimal with a fixed exponent of -6 at the Store boundary". The ticket says "at most 6 decimal places" and does not quantize outputs. NUME... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C15 | P4d | MINOR | Hot files; template order: Plan rule 10 orders `memory.py`, `migrate.py` and `CHANGELOG.md` as P3a, P4d, P4a, P4b; the ticket gives no order for them. `tests/contracts/test_stor... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p4d-r1-cor-C16 | P4d | MINOR | R2/R7: R7's AST scan counts any call whose attribute name matches a method (`touch`, `get_run`, ...), on any object, so it can pass without a store call. Req... | OPEN | reviews/P4d-round1-correctness.md | d2d658b |
| BL-core-p1-r2-adv-A1 | P1 | MAJOR | Interface, "DENY key-set" and "Match rule": The only matching API is `scan_match(a, b)`, which is whole-key set intersection. A DENY use (blocklist entry inside a document of up to 262,144 chara... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A2 | P1 | MAJOR | "DENY key-set": does it cover mixed ambiguous lett: Coverage is only 3 binary choices (case reading, Ze, split). Table values are one-to-one, with no I/l/1 or O/0 reading. `_confusables.py` has no ASCII... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A3 | P1 | MAJOR | Gap 3, tag characters: The fix says "decode ... and append the decoded text to the text before the scan view". Appending at the end of the whole text destroys adjacency. | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A4 | P1 | MAJOR | Gap 7, entity step: `html.unescape` turns invalid numeric references (`&#0;`, `&#xD800;`, `&#x110000;`) into U+FFFD. U+FFFD is category So and is not dropped (`_DROP_CATE... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A5 | P1 | MAJOR | FOLD_VERSION, Golden test 2: The "forced bump" is vacuous. Test 2 requires a different `alg` only if goldens differ from the file. A developer who changes behaviour regenerates th... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A6 | P1 | MAJOR | P1b stored keys: (a) `salt=None` is the default, so the easiest call stores an unsalted SHA-256 of a personal name. It is brute-forceable from any name list, it correl... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A7 | P1 | MAJOR | Stored-key mismatch, "goes to a person" (F3): Not implementable from this ticket. Nothing here provides a hand-off, a queue or a re-fold path. It is pushed to P3b and P2a as "must name who decides... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A8 | P1 | MAJOR | Error contract (fail-closed), item 3: The contract "any TextnormError means REFUSE" lives in a docstring and in a `deny_scan` helper that exists only in the tests. Consumers can do `except... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A9 | P1 | MAJOR | Intake call-site table / "Intake move after P1b": The rule says ALLOW sites call `allow_equal(extracted candidate, on-file component)`. But Intake `_f` folds the sent text and extracts the candidate f... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A10 | P1 | MAJOR | Scope (P1a/P1b/P1m): P1b is five things in one Tier A PR: algorithm change (gaps 1-5), entity/line view, key-set, stored-key API with a crypto/format surface, cache, and a... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A11 | P1 | MINOR | Bidi controls: Bidi controls are only dropped. An override (U+202E) reverses the displayed order but the stored key keeps logical order. Intake already treats the pr... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A12 | P1 | MINOR | Spaced view and empty keys: "Empty keys are left out of the set" is stated for the key-set, but the spaced pipeline turns Cf/Cc into ONE space. Strip behaviour is not specified.... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A13 | P1 | MINOR | Cap and expansion: The ticket calls the check "NFKC expansion", but `fold` starts with NFKD and `runmap._expanded_len` counts NFKD length (runmap.py:135-147). A builder... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A14 | P1 | MINOR | Cache: `TEXTNORM_CACHE_ENTRIES` patched to 4 cannot work if the cache is a `functools.lru_cache(maxsize=N)` built at import (maxsize is fixed at decoration t... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A15 | P1 | MINOR | Idempotence and convergence tests: The idempotence claim and "pass count 2 or less" are tested over single code points only. Sequence effects are the real risk: dropping a filler or mar... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A16 | P1 | MINOR | Hard-coded values: Not in `defaults.py`: the 80-character cap on a version in the `check_stored` message, the `^alg=fold[0-9]+\/` pattern, and the digit table bound `ran... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A17 | P1 | MINOR | Tests tied to the environment: Fail-before relies on a shim stub that the same author writes. It proves each test can fail but not that it fails for a realistic wrong implementation... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A18 | P1 | MINOR | P1m: The mutation judge (KILLED / WRONG_REASON / CRASH) is what lets Tier A claim "every mutant ends KILLED", yet P1m is proposed as Tier B and was not rea... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-adv-A19 | P1 | MINOR | Wording: "digest" is used both for the SHA-256 of a key and for `TABLE_DIGEST` (SHA-256 of the table), and `keyset_encode` "used only when one value for a whol... | OPEN | reviews/P1-round2-adversarial.md | 41b4c2d |
| BL-core-p1-r2-cor-C1 | P1 | BLOCKER | Interface, "DENY key-set" and "same_person in P1b : Under the ticket's own rules, `same_person` stops over-matching. That is unsafe for the separation-of-duties DENY case. (a) Gap 3 appends the decoded... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C2 | P1 | MAJOR | Interface (match rule, `stored_key`, `stored_key_m: The match rule is incomplete. `scan_match` is only "share one whole key". Blocklists and leak scans are substring checks. The ticket itself says an em... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C3 | P1 | MAJOR | Several: lines 20, 33, 43, 49, 53, 86: The ticket cites lead decisions that do not exist in A13. A13 in `amendments.md` has only items (1)-(6). (3) is the P2a stop/reset identity, not the c... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C4 | P1 | MAJOR | Tests (P1b), fail-before table: The table says each row "must fail on an assertion (a) on the merged P1a head". Several rows use names that P1a does not have: `line_view` (gap 7), `s... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C5 | P1 | MAJOR | Interface, `check_stored` message rule: "The message shows a version only if it matches `^alg=fold[0-9]+\/` and then at most 80 characters". Only a prefix is checked. A stored string such as... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C6 | P1 | MAJOR | Evidence commands; unidata pin: A9 F3 says "Python 3.14 is probed in P1 before relying on gap 2". The evidence loop is `for v in 3.12 3.13` only. The ticket admits 3.14 and 3.12 are... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C7 | P1 | MAJOR | Files: "Vendored data `tools/data/confusables.txt`: The generator's only input is left out of core. memo-5 line 28 lists `tools/data/confusables.txt` and `.gitattributes` as P1 files. No copy exists any... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C8 | P1 | MAJOR | Mutation plan: "re-point the 27 existing mutants .: One of the 27 has no killer among the 13 moved tests. "fold: loose map short" (748849c `promoted_mutants.py` line 435) is killed by `test_a_protected_... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C9 | P1 | MAJOR | Intake `_f` call-site table, rule for the Intake m: The line numbers and the 13-calls-on-10-lines count are correct. But the stated rule does not work as written. At every ALLOW site the candidate is ex... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C10 | P1 | MINOR | Fail-before row 2 (gap 2), table: Wrong line cite. "gen_confusables.py `build`, lines 54-61". At 748849c `build` is lines 66-94. The two filter lines are 77-78 (`NFKC != ch` or categor... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C11 | P1 | MINOR | Gap 1 row; "Existing core code reused": False statement: "PR #50's table already maps U+0130". `0x0130` is absent from `_confusables.py` (Grep of 0x0397, 0x03B7, 0x0417, 0x0437 and 0x03C3 hi... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C12 | P1 | MINOR | P1m and mutation plan: (a) P1m lists two files. 748849c also has `src/hadavin_sdk/testing/__init__.py` (a docstring) and `tools/__init__.py` (empty). Core main has neither t... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p1-r2-cor-C13 | P1 | MINOR | Interface details: (a) `check_pinned_unidata(expected, *, strict)` is required-positional, but the text says "the default `expected` is `defaults.TEXTNORM_PINNED_UNIDATA... | OPEN | reviews/P1-round2-correctness.md | 41b4c2d |
| BL-core-p2a-r2-adv-A1 | P2a | BLOCKER | Security (agent runtime bullet); Files: The ticket narrows the runtime grant on `kill_switch` to `SELECT, UPDATE` and reuses the existing unconditional upsert. In Postgres, `INSERT ... ON CO... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A2 | P2a | BLOCKER | Interface (`StopGate.release`); Security: The gate keeps `release(by)`, which calls `Limits.reset`, inside the agent-runtime process. Reset needs the reset database role, and the ticket says t... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A3 | P2a | MAJOR | Security (trigger); UNVERIFIED "how the reset role: The role name has no workable route into the trigger. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A4 | P2a | MAJOR | Security (trigger bypass): The ticket never says which of `session_user` or `current_user` the trigger tests, and never covers owner, superuser or `ENABLE ALWAYS`. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A5 | P2a | MAJOR | Security (reset role); Breakglass: One shared reset database role is used by every person in `reset_names`, and the same credential is also called "dormant breakglass". Attribution is t... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A6 | P2a | MAJOR | Security; Done: Nothing at startup checks that the DB enforcement is actually present. The code-level `reset_names` check is a typo guard (the ticket says so), and it... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A7 | P2a | MAJOR | Interface (fail closed); agent_loop: The fail-closed fix names only `_limits_stop` (lines 359, 421, 460). The execution-time check `_recheck` at `agent_loop.py:744` calls `limits.blocked`... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A8 | P2a | MAJOR | PENDING LEAD item 1 (wiring); Done: The recommended position is unsafe for a Tier A stop. The gate ships "unwired". `tick.py` has no stop concept (the ticket's own line 44), and the wiri... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A9 | P2a | MAJOR | Depends on; Files; Done: P2a-1 is not "one reviewable package" for Tier A. It combines the Limits identity and compare-and-set change, masking, the gate, the CLI, config, `app... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A10 | P2a | MAJOR | Test plan: The mutation plan has no rows for the parts that enforce the rule. The 48 gate rows and the runner rows mutate Python snippets only. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A11 | P2a | MINOR | Rollback: The Rollback statement is wrong for the trigger. "A revert silently re-allows any reset" is false once the forward-only trigger exists. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A12 | P2a | MINOR | Config (`max_cache_ttl_s`): The `cache_ttl` cap is itself configurable, with default 5 s and no ceiling in code. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A13 | P2a | MINOR | Interface (token): The reset token is `(by, ts)` with `ts` set by the writer's Python clock, while reset sets `ts=now()` in the database. A reset can be refused indefini... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A14 | P2a | MINOR | Masking and keys: The label key sits in the agent-runtime process, so a compromised runtime can compute the label of any known login and write a stop or audit entry und... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A15 | P2a | MINOR | Neutral default / alternative: The `StopBackend` outline defines `clear_if`, but `Limits` and the gate use `Store.clear_kill_switch_if`. Two interfaces, and no statement of how one... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A16 | P2a | MINOR | Row store; neutral default: The memory store kill switch is per process and lost on restart. The ticket only addresses row-store durability (item 5), not the switch. | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-adv-A17 | P2a | MINOR | Wording: (1) "STOP is never refused" is later followed by `Limits.stop` raising after the write when the audit is down; the CLI wording for that case is not sp... | OPEN | reviews/P2a-round2-adversarial.md | 6942174 |
| BL-core-p2a-r2-cor-C1 | P2a | BLOCKER | Security (DB-role design, "GRANTS['kill_switch'] c: As written, the database part cannot be built correctly. (a) The runtime stop cannot be written. `PostgresStore.set_kill_switch` is `INSERT ... ON CON... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C2 | P2a | MAJOR | Interface (`release`, `restore`), Security: The ticket does not say where `StopGate.release(by)` runs. `release` calls `Limits.reset`, which calls `clear_kill_switch_if`. With the trigger in pla... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C3 | P2a | MAJOR | Files: "Existing tests that call reset ... must be: The list is incomplete. A required `expect` and new required CLI flags break more tests. (1) `tests/test_cuj.py:244-249`: `limits reset --by user:a` o... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C4 | P2a | MAJOR | Tests, FAIL-BEFORE (1), (2), (5): The named heads would fail these tests by TypeError or by an unrelated exception, not by an assertion. (1) and (2) call `Limits(..., reset_names=...)`... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C5 | P2a | MAJOR | "THE WEAK ROW" (ii): The ticket says "NEW test `RowStore(max_rows=None)` without opt-in raises `ValueError` (none exists), plus the row `rows: unbounded without opt-in acc... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C6 | P2a | MAJOR | Interface "Release re-stop window"; race test (f): The window is not closed as claimed. In `release`, `_gen` is checked before the store write. In `engage`, the flag is set and `_gen` bumped first, and... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C7 | P2a | MAJOR | Mutation plan: The plan has no mutant for the security property itself. No row for: the migration trigger (removed or loosened), the `reset` field in `GRANTS`, the S... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C8 | P2a | MAJOR | Files (P2a-2): P2a-2 owns the runner and judge rows (5 `mutation.py` + 16 `mutation_runner.py` = 21), but the file list names only `tests/test_stop_state_rowstore.py... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C9 | P2a | MINOR | Fail closed (`agent_loop`): The `_limits_stop` fix says a store error ends the run STOPPED. `_to` and `_note` write to the same store (and audit), so with a really unreachable st... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C10 | P2a | MINOR | Interface "Who may do what": "The old `stop_identities` list is deleted": no such list exists in core, PR50-local or PR50-pushed (grep found nothing in the snapshots). It was only... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C11 | P2a | MINOR | Interface (`StopGate` signature; masking): `StopGate(limits, *, cache_ttl, unaudited)` drops PR50-local's `label_key`. But the gate writes its own audit rows: `restore` events (`stop_gate.py:23... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C12 | P2a | MINOR | Mutation plan "Existing gate rows kept": Two existing rows target code the redesign deletes: `release ... expect=self._wrote` (`promoted_mutants.py:2026-2031`) and `b3: reset ignores a change... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p2a-r2-cor-C13 | P2a | MINOR | Depends-on / hot files: Amendment F6 lists `store/postgres.py` as (P4d, P4b1, P6b2). The ticket says P4b1 no longer edits it (A11 is later and wins) but does not say where P2... | OPEN | reviews/P2a-round2-correctness.md | 6942174 |
| BL-core-p3a-r2-adv-A1 | P3a | MAJOR | Interface `check_ledger`; Tests FAIL-BEFORE 5; `ch: The ticket contradicts itself on unreadable and non-UTF-8 files. FAIL-BEFORE 5 expects `ConfigError` for a non-UTF-8 `.sql` file. But the `check_ledge... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A2 | P3a | MAJOR | Rollback runbook (a); Open point 1: The ticket says the recipe "also covers a hotfix that needs an out-of-order number". It does not cover a hotfix whose number is already taken. Scenari... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A3 | P3a | MAJOR | Interface `order_problems` message; Tests recipe t: The recipe is unsafe or incomplete in four ways. (i) It takes no advisory lock; the key `_LOCK` is derived in code, so an operator cannot know it. A c... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A4 | P3a | MAJOR | Manifest (PENDING LEAD; recommendation): The recommended scope has two holes. (1) "Released" lags "applied". A file merged to main and applied by every main deployment or demo is "unreleased"... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A5 | P3a | MAJOR | Previous-release test, layer 1: Layer 1 reads catalog structure on empty schemas and is blind to several breaking classes, but the ticket says it proves the old schema "is still pres... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A6 | P3a | MAJOR | Merge precondition; CHANGELOG reword (Open point 2: The old CHANGELOG line 11 told dev and demo users to rename the `0005_evidence` ledger row to `0006_evidence`. Anyone who followed it has a database w... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A7 | P3a | MAJOR | Layer 2: Layer 2 is a one-time manual run on a planted ALTER-only migration, and it works only for ALTER-only changes. Later migrations (P4d-b, P3b, P3c) get n... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A8 | P3a | MINOR | `order_problems`: The compare is "number at or below the highest applied". A file with a number equal to an applied one but a different stem is handled by `gone` first,... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A9 | P3a | MINOR | Statements that cannot run in a transaction: The ticket names only `CREATE INDEX CONCURRENTLY`. `ALTER TYPE ... ADD VALUE` (new value unusable in the same transaction), `VACUUM`, `CREATE DATABASE... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A10 | P3a | MINOR | Constants / tests: `PREVIOUS_RELEASE_LAST = "0005_evidence"` becomes stale at the next release if the manifest is declined; the 10-second poll and the 2,000-case count a... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A11 | P3a | MINOR | Test plan, mutants: Missing mutants: manifest rules "numbers run 1..k" and "unreleased above k"; "released file is missing"; "`order_problems` uses min instead of max app... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A12 | P3a | MINOR | Evidence / skip: Postgres tests skip without `HADAVIN_TEST_PG_DSN`; the ticket asks for "0 skipped" only in the evidence output. CI does set the DSN and checks the cli... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-adv-A13 | P3a | MINOR | Wording: (1) "check_grants ... raises ConfigError as now" (see A1). (2) The ticket says "released" in two senses (tagged, or merged when no manifest exists). (... | OPEN | reviews/P3a-round2-adversarial.md | 544eadc |
| BL-core-p3a-r2-cor-C1 | P3a | MAJOR | Interface (`check_ledger`, `migrate()` step 2); Te: The ticket says non-regular entries and unreadable files are refused with `MigrationNumberError`, but the interface does not deliver that for a non-UT... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C2 | P3a | MAJOR | Tests, layer 1 (pg_catalog comparison); Mutation M: Layer 1 compares relations, columns, constraints, indexes, triggers and views. It does not compare functions (`pg_proc`). `0002_audit_chain.sql` defin... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C3 | P3a | MINOR | Tests, FAIL-BEFORE header ("each fails on an asser: Tests 4 and 5 do not fail on an assertion on `ce70eb5`. `IsADirectoryError` (`FileNotFoundError` or `UnicodeDecodeError` for 5) is raised inside `with... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C4 | P3a | MINOR | Tests, layer 2 (lead's plugin): The plugin wraps the old `migrate()`, "calls the original, then runs the new SQL". The old tests call `migrate()` repeatedly on one schema: the fixtur... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C5 | P3a | MINOR | Tests, layer 1: Schemas A and B are different PostgreSQL schemas, but the ticket does not say how to remove the schema name from the compared text. `pg_get_indexdef`... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C6 | P3a | MINOR | Open point 3 (manifest) and Problem 5: The cost of declining the manifest is understated. Plan row P3a (plan-v3.md line 96) says "CI fails on duplicate or out-of-order numbers". Without the... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C7 | P3a | MINOR | Existing code and Security notes: Line-reference slips. (a) `tests/test_k5_round10_postgres.py:136-141` is cited as proving the "runtime role cannot read `schema_migrations`". The test... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C8 | P3a | MINOR | Tests, recipe test (`test_recipe_for_a_late_number: The recipe SQL itself is correct. The ledger column is `version` and the value is the stem without `.sql` (`migrate.py:317, 331`). A multi-statement `... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p3a-r2-cor-C9 | P3a | MINOR | Hostile inputs and property test: `ConfigError` derives from `ValueError` (`src/hadavin_sdk/errors.py:4`). "Must not raise a bare `ValueError`" and "only `MigrationNumberError` is rais... | OPEN | reviews/P3a-round2-correctness.md | 544eadc |
| BL-core-p4d-r2-adv-A1 | P4d | BLOCKER | P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK: The ticket contradicts itself. The stated order is reservation, run, day, month. Rule 1 (reserve) lists the counters as day, month, then run: "per cou... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A2 | P4d | MAJOR | P4d-a `check_usd`, `max_decimals`: `x.normalize()` rounds to the context precision (28 digits) before stripping zeros. I reasoned this from CPython's `_fix`; I did not run it. A value s... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A3 | P4d | MAJOR | Error rule, `@_writes`, money SQL: Nothing sets `lock_timeout` or `statement_timeout`. Every call holds the process-wide `self._lock` for its whole duration, on one connection. | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A4 | P4d | MAJOR | `reserve_spend` step 1, kill switch with `FOR SHAR: The share lock on the kill-switch row is held until the reservation commits. `set_kill_switch` is an UPDATE and conflicts with `FOR SHARE`. The safety... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A5 | P4d | MAJOR | `sweep_spend_reservations`, `settle_spend`, `relea: (a) The sweep can only settle at the reserved worst case. A crashed call that never reached the model keeps its reserved amount in the day, month and... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A6 | P4d | MAJOR | P4d-a `require_backend` and the session-end check : Three contradictions. (1) The check "fails the run when any `tests/contracts` test was skipped" covers the whole directory, but that directory also ho... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A7 | P4d | MAJOR | Order of work: "c may run in parallel with a (diff: Both sub-tickets change `tests/contracts/kinds/store_postgres.py`: a for `require_backend`, the pair and the "behind schema" builder, c for `pg_driver... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A8 | P4d | MAJOR | P4d-b Security, negative tests; P4d-c `pg_driver`: `pg_driver` offers only `connect_admin`. The negative-privilege tests need a runtime-role raw connection, and the ticket does not say how a test gets... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A9 | P4d | MAJOR | P4d-a scope, "no new money SQL": P4d-a is labelled "no new money SQL" but changes `add_spend`/`add_cost` (rejects values, so legitimate callers could now fail), puts a retry-on-class-... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A10 | P4d | MINOR | `sweep_spend_reservations`, `limit` and `older_tha: `limit` has no validation. Memory slices `[:limit]`, so a negative `limit` returns "all but the last" silently, while Postgres errors (`LIMIT must not... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A11 | P4d | MINOR | `check_text`: Scope is "JSON-bound fields". Plain TEXT columns (reasons, tool names, messages, `reason_code`) are not covered. NUL in a TEXT column: Postgres refuse... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A12 | P4d | MINOR | 0006 DDL: `agent_id` and `run_id` have no CHECK, while the PK has one. Python-side only, so a direct runtime-role INSERT can store anything. No FK from `run_id`... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A13 | P4d | MINOR | P4d-b Security: "a compromised runtime cannot rewr: Overstated. The runtime role has `UPDATE` on `spend`, `spend_month` and `runs`, so it can zero the counters directly. The trigger protects the ledger... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A14 | P4d | MINOR | Trigger definition: `BEFORE UPDATE` only. A role with INSERT can insert a row directly as `status='settled'` (CHECKs allow it). The trigger does not fire on a `session_re... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A15 | P4d | MINOR | P4d-c guard: `pg_driver()` returns `sql`, `errors` and the live admin connection, so the test files can reach psycopg through them. c5 only checks that the namespa... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A16 | P4d | MINOR | P4d-a tests: The "recording proxy" counts a call anywhere (fixtures, setup) as coverage, so a method can be "called on every backend" without any assertion. The cl... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-adv-A17 | P4d | MINOR | B7 and process rows: B7 uses `sleep 2s` with `older_than_s=1`, which is slow and flaky on a loaded machine (the shared laptop has had load problems). The SIGKILL test depe... | OPEN | reviews/P4d-round2-adversarial.md | 1c82da1 |
| BL-core-p4d-r2-cor-C1 | P4d | MAJOR | P4d-b "Money SQL rules" 1 vs 2 and the GLOBAL LOCK: The ticket contradicts itself on lock order. The header says reservation, then run, then day, then month, and the settle rule (2) follows it. But `res... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C2 | P4d | MAJOR | P4d-a Interface, `require_backend` and session-end: As specified, the session-end check fails green runs. (a) It fails on "any `tests/contracts` test skipped", but contracts hold a legitimate skip: `tes... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C3 | P4d | MAJOR | Header "Order inside P4d"; P4d-c: The claim "c may run in parallel with a (different files)" is false. P4d-a and P4d-c both change `tests/contracts/kinds/store_postgres.py`. P4d-c's `p... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C4 | P4d | MAJOR | P4d-a, P4d-b "Tests" and "Security" vs P4d-c guard: The new a and b tests need raw driver access. Examples: an admin connection holding `FOR UPDATE`, runtime-role `UPDATE`/`DELETE` that must fail with `... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C5 | P4d | MAJOR | P4d-b "Tests" FAIL-BEFORE; P4d-a FAIL-BEFORE: The template asks for fail-before on an assertion. Every B row fails on ce70eb5 with `AttributeError` (and with `NotImplementedError` in the stub comm... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C6 | P4d | MINOR | P4d-a, `@_writes` retry: The retry fires on "sqlstate class 40". That includes 40003 `StatementCompletionUnknown`, where a write may have been applied, so a blind retry of `ad... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C7 | P4d | MINOR | P4d-a, `check_text` scope vs hostile rows: `check_text` is defined for "JSON-bound fields". The hostile row demands that NUL in a plain text value be a `ValueError` on both stores. MemoryStore... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C8 | P4d | MINOR | Evidence commands, P4d-a and P4d-b: `uv run --group test bandit` fails. bandit is in the `scan` group, not `test`. P3a uses `--group scan`. | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C9 | P4d | MINOR | Verified facts, psycopg counts: `test_p7_store.py` has 1 `importorskip` (line 11), not "+2". All other per-file counts are correct. | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C10 | P4d | MINOR | P4d-a Security: The claim "the only DSN text in the repo is CI's password-less URL (`ci.yml:86`)" is false. `ci.yml:93` repeats it, and about ten tests hold DSN liter... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C11 | P4d | MINOR | P4d-a FAIL-BEFORE and regression pins: Several rows already pass on ce70eb5 and are not labelled as pins. They are the 1 MB, Unicode and SQL-text round trips (parametrized, so they pass). A... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C12 | P4d | MINOR | P4d-b, `@_writes` list: "Five methods, all `@_writes`" includes `get_spend_reservation`, which is a read. The AST sibling check is for write methods. | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C13 | P4d | MINOR | P4d-b, `is_connectivity_error` change: The ticket does not list the other callers or add tests for them. They are `audit/chain.py:531-541` (an unreachable store becomes `StoreUnavailable`),... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C14 | P4d | MINOR | P4d-b, row B8(c): Two points. (1) "How existing tests build an old release is UNVERIFIED" is verifiable: `test_k2_migrations.py:387-394` monkeypatches `_migration_files... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C15 | P4d | MINOR | P4d-b `settle_spend`: "A later call, whatever its amount (even an invalid-looking one that is a valid Decimal)" conflicts with "validate before any SQL". A NaN second call... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C16 | P4d | MINOR | Template order and fields: All 17 template fields are present and "Extended review: yes" is set. The order is not the template's. The header places Neutral default and Existing... | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p4d-r2-cor-C17 | P4d | MINOR | P4d-b, kill switch: Not stated whether `settle_spend`, `release_spend` and sweep ignore the kill switch. They should, so that stopping does not strand reservations. | OPEN | reviews/P4d-round2-correctness.md | 1c82da1 |
| BL-core-p1-r3-adv-A1 | P1 | BLOCKER | "The DENY key-set" ("Four yes/no choices applied t: Whole-text readings cannot express a text where different positions need different readings. The key-set contains only the all-one-way readings, so mi... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A2 | P1 | BLOCKER | P1b "other"; `has_hidden_channel`, `has_bidi_contr: Two separate holes in what the DENY path enforces. (1) `view="id"` calls `id_key(loose)`, which calls `squeeze`, which drops tag characters and variat... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A3 | P1 | MAJOR | P1b "substring scan" (cost, `TEXTNORM_MAX_NEEDLES : The measured cost and the chosen limit do not match. The only measurement is 200 needles x 8x8 searches over 262k keys = 1.93 s, random text. The cons... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A4 | P1 | MAJOR | `scan_hit`, contract paragraph; "Errors": Fail-closed is advisory, not enforceable. `scan_contains` is public and raises. Nothing makes a caller use `scan_hit`. A caller with `except Exception... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A5 | P1 | MAJOR | P1a "Interface", length check: The size rule is ambiguous in a way that over-refuses. "Sum over characters of the cached NFKD length times the longest table value (2)" can be read a... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A6 | P1 | MAJOR | "Which view each caller uses"; `name_key` in VIEWS: `name_key` equals `names_equal`, which does NO look-alike fold. The textnorm.py docstring (lines 15-16, 130-133) says it is neither DENY nor ALLOW. Th... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A7 | P1 | MAJOR | P1c, stored-key API (salt, key id, SaltMismatch): Salt rotation can fail silently into "different", which is fail-open for DENY. `key_id: str | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A8 | P1 | MAJOR | P1c "Mismatch handling" and rolling deploy: The only migration path is "keep the raw text under a role-gated store and re-fold" (`plan_refold`), which cuts against the purpose of storing digests... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A9 | P1 | MAJOR | `same_person` claim "never weakens the PR #50 beha: The claim is false for gap 2. Applying the table to unassigned code points before the drop makes `fold("p\U000113D4")` become `pl`, but PR #50 gave `p... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A10 | P1 | MAJOR | Gap 7 / `line_view`, entity step; `view="id"`: The entity step is only in `line_view` and the "scan keys". `identity_key` and the id view do not unescape. Intake's `_f` does (`_unescape`, invoicech... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A11 | P1 | MAJOR | FOLD_VERSION, `beh`, golden test (item 4): "FOLD_VERSION changes whenever behaviour changes" is not proven. `beh` hashes an enumerated list; a constant omitted from the list is omitted from bot... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A12 | P1 | MINOR | Rollback / shim fail-before: P1c has no shim defined, so its fail-before is an ImportError. `xfail(strict=True)` rows pass as xfail even if they fail for the wrong reason (excepti... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A13 | P1 | MINOR | `scan_hit`: One blocklist entry that folds to empty (a CJK invoice id in the id view, a zero-width string) raises `EmptyKey`, which `scan_hit` turns into True for... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A14 | P1 | MINOR | Interface, `MappingProxyType`: The perf numbers (0.04-0.08 s at the cap, 1.93 s scan) were measured on plain `dict` tables at 748849c. `str.translate` through a `mappingproxy` goes... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A15 | P1 | MINOR | `NotText` (`type(x) is str`): Rejects legitimate `str` subclasses such as `StrEnum` members; refusal is correct for DENY but surfaces as every call raising (role names as `StrEnum`... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A16 | P1 | MINOR | FoldNotConverged / MAX_PASSES: "At most 3 passes", the test says "pass count below 3". Whether the confirming pass counts is not stated; a builder counting it makes inputs that need... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A17 | P1 | MINOR | P1a/P1b: `alg=fold1` "provisional, do not store keys" is not enforced; `identity_key` and `fold_key` are public. P1a exports `FOLD_VERSION` before the stored-k... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A18 | P1 | MINOR | Words / API names: `id_key(raw, loose=True)` defaults loose, `squeeze(raw, loose=False)` defaults not loose, same parameter name. `stored_key` returns a record, not a ke... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A19 | P1 | MINOR | P1m (PENDING LEAD tier): Tier B with an adversarial review of the verdict rules is acceptable. The runner decides what counts as KILLED for Tier A evidence, so the review must... | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p1-r3-adv-A20 | P1 | MINOR | Tests tied to a Python version: Exact counts (677 entries, 56 Cn, 670 digits, 114 non-idempotent, 15.1.0) are facts of Unicode 15.1.0. Tests asserting them fail or lie on 3.12/3.14. | OPEN | reviews/P1-round3-adversarial.md | 221513b |
| BL-core-p2a-r3-adv-A1 | P2a | BLOCKER | Interface, `StopGate.sync_from_store`; race test (: The runtime clears its own emergency stop. Scenario: the store is down, so `engage` sets the local flag and `Limits.stop` fails (`durable=False`). The... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A2 | P2a | MAJOR | Interface (`version` rule), residual risk, CLI: The lock-out by repeated stops is documented, not solved, and the remedy is wrong. The trigger bumps `version` on every UPDATE, including ON to ON, an... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A3 | P2a | MAJOR | Rollback; Effect on old code: The rollback recipe cannot run. It says to run the old release's `migrate --runtime-role` to re-grant INSERT. `migrate()` refuses when the ledger hold... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A4 | P2a | MAJOR | Split / Depends-on: P2a-1a cannot pass its gates alone, and it leaves reset impossible between merges. The migration makes ON-to-OFF a deny-all for everyone except group... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A5 | P2a | MAJOR | Security (roles), `effective_problems`: The membership route to ownership is not blocked. `effective_problems` only tests `owner == role` (migrate.py:219-220); the pairwise check covers only... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A6 | P2a | MAJOR | Security (personal data), `kill_switch_resets`: The table stores the raw `session_user`, a per-person login name, in a table the `0002` trigger makes append-only, so erasure is impossible. This also... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A7 | P2a | MAJOR | Reset path, audit: Audit shows a reset that did not happen. Order is (3) audit intent `reset`, (4) `clear_kill_switch_if`. If step 4 raises (reset handle down, 42501 bec... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A8 | P2a | MAJOR | Security, breakglass; Tier A: Breakglass is "alarmed" with no owner and no mechanism (UNVERIFIED who owns the alarm). The rule requires dormant, disabled and alarmed. The group can... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A9 | P2a | MAJOR | Security, reset credential path: The separation of the reset DSN depends on the secrets store ACL, which the ticket neither specifies nor tests. With the `env`, `mounted_file` and `va... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A10 | P2a | MAJOR | Fail-safe, in-flight and writer lock: No lock or statement timeout is specified for stop writes. A runtime session with UPDATE privilege can `SELECT ... FOR UPDATE` or hold an open UPDATE... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A11 | P2a | MINOR | Trigger, `migrate()`: The reset group is not persisted. Every `migrate` run re-issues the function from its argument; a later run without `--reset-role` (e.g. a routine re-... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A12 | P2a | MINOR | Probe: The probe runs only at start-up and at `limits reset`. A long-running process never re-probes, so an owner `DISABLE TRIGGER` goes unseen until restart... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A13 | P2a | MINOR | Fail-safe, `agent_loop` guard: The stated reason for the 240/744 change ("a one-second blip must not end runs") is contradicted by the ticket's own limit note: with a blip `_to` rai... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A14 | P2a | MINOR | Reset path, missing row: If the `kill_switch` row is missing, reads say ON, plain-UPDATE stop raises, and `clear_kill_switch_if` returns False forever. Nothing recreates the r... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A15 | P2a | MINOR | Personal data: The label hash protects nothing against anyone holding the key (the runtime does) plus a name list. Deleting the key erases all subjects at once, neve... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A16 | P2a | MINOR | Tests: Real-login tests create cluster-global roles: parallel runs or reruns collide, and logins need passwords for TCP auth. The ticket has no unique naming... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-adv-A17 | P2a | MINOR | Mutation plan: The 145 total adds up (43+14+22+17+49). Mutants that would survive: swapping `Limits.stop` to audit-before-switch; moving the reset intent after the c... | OPEN | reviews/P2a-round3-adversarial.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C1 | P2a | BLOCKER | Security "Reset credential path"; Files P2a-1a (`b: The claim "app.py NEVER resolves it; the secret VALUE exists only in the operator's secrets store" is false for the repo's own machinery. `platform_se... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C2 | P2a | MAJOR | Security "Effect on old code and rollback"; Rollba: The documented way back does not work. The ticket says to run the old release's `migrate --runtime-role` to re-grant `SELECT, INSERT, UPDATE`. Old `mi... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C3 | P2a | MAJOR | Depends-on / merge order; Files P2a-1a vs P2a-1b; : P2a-1a cannot be green at its own head. (a) The contract kind `stop_state` is listed in 1a with the rows "reset with the version token, stale token" a... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C4 | P2a | MAJOR | Files P2a-1b ("UPDATE the existing tests"): The update instructions are wrong or incomplete. (1) `rt.limits`/`app.limits` are built without `reset_store` by design (`app.py:171`; `Limits(store,... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C5 | P2a | MAJOR | Interface (Store methods); Security "Probe": The database surface Route A needs is undefined. The ticket adds only `clear_kill_switch_if`. The probe needs catalog reads (trigger, `tgenabled`, `pr... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C6 | P2a | MINOR | Security "Privileges": Deviation from A13(3) ("runtime read-only on kill_switch": the ticket grants SELECT, UPDATE) is needed for an open stop but not flagged as a deviation... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C7 | P2a | MINOR | Interface; Existing code reused; Hot files: Wrong citations and omissions: PR50-local read-then-write is `limits.py:65-70`; FakeLimits at `test_promoted_controls.py:225-248`, signature test `:25... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C8 | P2a | MINOR | Files P2a-2 (runner); Mutation plan "2 new rows": Premise wrong: `judge()` returns SURVIVED for exit 0 (`testing/mutation.py:55-56`) and the runner counts that as not good, so a skipped killer is alre... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C9 | P2a | MINOR | Mutation plan per sub-PR: Per-sub-PR counts inconsistent: "b3: reset ignores a changed switch" is re-pointed in 1a but the 1b count "5 re-pointed" is 4 label rows plus that row... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C10 | P2a | MINOR | Security "Trigger": A routine `migrate` run without `--reset-role` re-issues the function as deny-all: fail-closed but a silent lock-out of resets; the rollback text itse... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p2a-r3-cor-C11 | P2a | MINOR | Tests: FAIL-BEFORE (5): "Fails with the store's own exception" depends on the `handle` callers having no outer catch; the reviewer found none in `_limits_stop`'s path (`agent... | OPEN | reviews/P2a-round3-correctness.md | 6d84ad6 |
| BL-core-p3a-r3-adv-A1 | P3a | BLOCKER | Interface `migrate()` (accept_late); test (d); `or: `accept_late` takes ONE stem, and "every OTHER late file still raises". With two or more late files, no single command can succeed. The refusal messag... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A2 | P3a | MAJOR | Decision and reason for `--accept-late`; Security : Nothing records or limits use. The ledger row written by accept-late is identical to an ordinary row (`version`, `applied_at` only), and the ticket re... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A3 | P3a | MAJOR | Statements that cannot run in the one transaction;: The list names CONCURRENTLY, VACUUM and similar, but omits transaction control and session changes: `COMMIT`, `BEGIN`, `ROLLBACK`, `SAVEPOINT`, `SET T... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A4 | P3a | MAJOR | Accept-late tests (a)-(e); mutants M22-M26: The ticket's central claim, "grants in the same run, removes the forgotten grants failure mode by construction", has no killing test. The planted file... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A5 | P3a | MAJOR | Layer 1 (baseline, "No exemption list is built"); : Two defects that hit the next builders (P4d-b, P3b, P3c). (1) The ticket does not say how schema A (baseline files only) and U are built. If via `migr... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A6 | P3a | MAJOR | Layer 1 compared kinds; plain statement: False confidence. (a) `relacl` and `attacl` are listed as compared, but A, U and F are built without roles. The ACLs that matter are the runtime, port... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A7 | P3a | MAJOR | Merge precondition; Rollback (runbook): The recovery for the one live-database case the ticket worries about is missing. The only fix given is the `0006_evidence` rename. For a database that... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A8 | P3a | MAJOR | Runbook cases (iv), (v); `gone` message: The remaining hand step is the real unreviewed write path. The runbook still asks for `UPDATE schema_migrations SET version=...` and "rename that ledg... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A9 | P3a | MINOR | Open point 3 (manifest, PENDING LEAD): The cost-of-declining argument is overstated, and the recommended scope is the weaker one. In a folder that `check_ledger` already holds gapless and u... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A10 | P3a | MINOR | Interface `order_problems` message; item 7: The message hard-codes "with the same --runtime-role, --purge-role and --portal-role". P2a (A14) adds `--reset-role` and `migrate(reset_role=...)`, so... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A11 | P3a | MINOR | Interface `migrate()` and the message: (1) Accept-late also applies every other pending ordinary file in the same run. The message ("It applies the file and records it") hides that. (2) Aft... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A12 | P3a | MINOR | `check_ledger` problem text; `MAX_PROBLEMS_SHOWN`: File names go into messages raw. A name with control characters or newlines is a log or terminal injection. A name with undecodable bytes (surrogate e... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A13 | P3a | MINOR | Test plan: (1) The accept-late selection logic is only testable on Postgres. It should be a pure function, `late_files(applied, files)`, next to `order_problems`... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A14 | P3a | MINOR | Statements that cannot run in a transaction: (1) Banning CONCURRENTLY forever leaves no documented online index path for a live table. (2) `migrate()` takes `ACCESS EXCLUSIVE` locks with no `lock... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-adv-A15 | P3a | MINOR | Words and definitions: "Released" is defined as the manifest list, but no release exists. The text "First check the file also works on a fresh install (CI does)" is true onl... | OPEN | reviews/P3a-round3-adversarial.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C1 | P3a | MAJOR | Layer 1 "Planted cases" and M27: Several planted cases cannot reach the comparer, because `migrate()` refuses the planted file first (`check_grants`, run before the DB is touched). `C... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C2 | P3a | MAJOR | Layer 1 "Planted cases" and "Seeding": Two planted cases fail inside Postgres, not in the comparer. (a) `UPDATE runs SET state = lower(state)`: `runs.state` has a CHECK on uppercase values... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C3 | P3a | MAJOR | Rollback / runbook (d) and case (iii): Runbook (d) says an older `migrate` on a newer database "must not be forced". The ticket leaves the `gone` message unchanged, and that message tells t... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C4 | P3a | MAJOR | Interface (`cli.py` flag), Files, Mutation plan: The new `--accept-late` flag has no test that it reaches `migrate(accept_late=...)`, and no mutant. The only listed cli evidence is that the old `test... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C5 | P3a | MINOR | Interface, `migrate()` body and M12: The accepted stem must be added to `done`, or the "normal loop" (`migrate.py:327-332`) applies it a second time. `order_problems` returns message stri... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C6 | P3a | MINOR | Security notes (transaction range): The transaction range cited as `migrate.py:312-359` is off: `with (connect(...)` begins at `:308`, `db.transaction()` is `:312`, the last grants check... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C7 | P3a | MINOR | Layer 1 rules, M29: "U must equal F" has no planted case; the only test named is accept-late test (b), a different call site; M29 is not clearly killed. | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C8 | P3a | MINOR | `_UNREAD` additions, M21: `CREATE DATABASE` and `CREATE TABLESPACE` are already refused by the generic path (`_ANY_CREATE` finds them and `_SAFE_CREATE` does not match, `migrat... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C9 | P3a | MINOR | Hot files: The ticket lists only the F6/rule-10 hot-file orders. LEAD-ORDERS 5(a) gives P2a `migrate(reset_role=...)`, which changes `migrate()` and probably `cl... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C10 | P3a | MINOR | Merge precondition rationale: "Why it gates P3a: migrate already refuses a ledger name with no file ... as soon as the folder no longer has that name." Main's folder has never had... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p3a-r3-cor-C11 | P3a | MINOR | `order_problems` message: The message says "See CHANGELOG.md, 'Migration runbook'". The CHANGELOG is a repository file; it may not ship in the package, so an operator with only... | OPEN | reviews/P3a-round3-correctness.md | 2fe14e1 |
| BL-core-p1-r3-cor-C1 | P1 | MAJOR | Interface, input rules (length check): The expansion cap uses "the longest table value (2 for AE)". False: the table has 3-character values (`_confusables.py:443` "lll", `:688` "sss") and g... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C2 | P1 | MAJOR | P1b, DENY key-set choice (1); Gap 1 row: The two case readings contradict the gap-1 fix. Reading "case first" is labelled "(the identity pipeline)", but the gap-1 fix loops table, casefold, t... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C3 | P1 | MAJOR | P1b, "Which view each caller uses"; Gap 3: Hidden tag characters are decoded only in the scan key-set. `view="id"` is `id_key(loose=True)` over the whole text, i.e. `squeeze`, which calls `fold... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C4 | P1 | MAJOR | P1a golden test vs P1c `keyset_encode`: Ordering error: the P1a golden test hashes key-sets "through `keyset_encode`", but the ticket lists `keyset_encode` under P1c; in P1a `scan_keyset` is... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C5 | P1 | MAJOR | P1b `scan_contains`/`scan_hit` complexity; `TEXTNO: The ticket's own measurement contradicts its limits: 200 needles x 8 x 8 searches over 262k keys took 1.93 s (about 150 microseconds per search). The... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C6 | P1 | MAJOR | P1c stored keys: (a) `salt: bytes | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C7 | P1 | MAJOR | Tests (P1m): P1m ships `tools/mutation_runner.py` (295 lines) and `testing/mutation.py` (105 lines), the code that decides whether Tier A evidence is a real kill,... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C8 | P1 | MAJOR | P1b `fold_key` / `fold(casefold=True)`: Only `identity_key` gets the gap-1 loop and the gap-4 tidy-up, but `fold_key` stays an exported name and `allow_equal` is described as "built on `fold... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C9 | P1 | MINOR | Interface: `scan_match` has no signature or place in `VIEWS`/the public list; "pass count below 3" conflicts with `TEXTNORM_MAX_PASSES = 3` (does the confirming... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C10 | P1 | MINOR | P1c version echo: The regex ends in `$`; `re.match` with `$` accepts a trailing newline. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C11 | P1 | MINOR | P1c: Key rotation detected only through `key_id`; same `key_id` with different salt bytes silently gives False; the HMAC input omits version and view. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C12 | P1 | MINOR | Files, P1c: No source file is named for the P1c API; P1b/P1c also change `textnorm.py`, the manifest, the golden file and the corpus. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C13 | P1 | MINOR | Tests, P1a: The moved set drops `test_the_manifest_pins_the_files_a_demo_copies` (2529), so the new `textnorm_manifest.json` is untested (it also requires every p... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C14 | P1 | MINOR | FOLD_VERSION: P1a's `beh` digests "the entity round limit" and the `html5` table, but entity handling arrives only in P1b. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C15 | P1 | MINOR | Tests, golden Test 2: `git show` through `subprocess` in a test trips ruff S603/S607 (`tests/**` ignores only S101); CLAUDE.md forbids suppressions (`pyproject.toml:73-81`)... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C16 | P1 | MINOR | Header: The note on 2e8a28c says only the runner differs (255 lines); `testing/mutation.py` also differs (95 vs 105) and `promoted_mutants.py` is 1,425 vs 2,1... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C17 | P1 | MINOR | Done / differential: "Fails on the old behaviour" is not true for the 748849c shim (`current` rows pass, `p1b` rows xfail); true only for a `runmap.canonical` shim at ce70... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C18 | P1 | MINOR | Key-set limit: A text mixing two Ze meanings (one z, one 3) in one value matches neither whole-text reading; the I/l/O/0 limit is stated, this one is not. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C19 | P1 | MINOR | Downstream, memo 5: P5a depends on P1 (plan row 104) but the ticket does not say P1a or P1b; P2a's memo-5 file list includes the runner/judge now owned by P1m; Decision 8... | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C20 | P1 | MINOR | Generator line cites: One filter spans `gen_confusables.py` lines 77-78; the small-cap block is 82-90; the ASCII/target filter at line 75 is a third skip. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C21 | P1 | MINOR | Timings: Every timing used a plain-dict table; P1a makes it a `MappingProxyType`, which may slow the per-character translate path. | OPEN | reviews/P1-round3-correctness.md | 221513b |
| BL-core-p1-r3-cor-C22 | P1 | MINOR | PENDING LEAD, P1m tier: The recommended Tier B is unsafe for the reasons in C7 (position check). | OPEN | reviews/P1-round3-correctness.md | 221513b |

## P4d round 3 (reviewed commit b215b50)
| BL-core-p4d-r3-adv-A1 | P4d | BLOCKER | `SELECT "on" FROM kill_switch WHERE id=1 FOR KEY SHARE` needs UPDATE privilege on the table in Postgres (any FOR SHARE/UPDATE clause does), but A13/A14 make the runtime role read-only on kill_switch (P2a, same wave); so after P2a every `reserve_spend` raises 42501 (fail-closed but money reservation  | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A2 | P4d | MAJOR | Check (1) fails the run on any `require_backend:` skip, but `require_backend` skips by design when no CI flag is set (laptop workflow needs no Docker, `store_postgres.py:1-2`); check (2) also fails without the `[postgres]` leg: every laptop run of `tests/contracts` without Postgres exits non-zero. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A3 | P4d | MAJOR | `run_id REFERENCES runs` and the INSERT (step 1) precede the run UPDATE (step 3): an unknown run raises raw `ForeignKeyViolation` 23503 at step 1 (the `_writes` mapping names Unique/Check/NotNull/DataError only); the promised `NotFound` at step 3 is unreachable; precedence differs between backends;  | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A4 | P4d | MAJOR | One connection behind one `threading.Lock` held across each whole transaction (`postgres.py:193-197`); `lock_timeout` 5000 ms applies per lock wait; up to 3 retries and no statement/total budget: a call blocked on a counter row holds the process-wide lock for tens of seconds, delaying `Limits.stop() | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A5 | P4d | MAJOR | `day_cap`, `month_cap`, `run_cap` default to `None` = uncapped: a caller that forgets the argument gets no cap, silently (the ticket's own stated bypass); changing the signature later breaks the closed Protocol. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A6 | P4d | MAJOR | The caller supplies `day`; the store only CHECKs 2000..2100: tomorrow's date (or a wrong time zone) books into an empty bucket and never consumes today's cap; the retry-across-midnight rule keeps the original day so the store cannot simply rederive. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A7 | P4d | MAJOR | If a counter is lower than the amount to lower, settle rolls back with `StaleState` forever; no API closes such a row; sweep moves no counters; release/settle on an expired row hits the same damaged counter (ops reset of `spend_month`, or a P4b2 `prune_spend`); the context manager's `finally` cannot | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A8 | P4d | MAJOR | a2 is not one reviewable Tier A package: validators for all models (`check_text` over every field), `check_id` on every write key, `@_writes` on 18 methods, retry/StoreBusy/lock_timeout, a setting field, `plan_id` semantics, step grammar, `list_approvals` order, `is_connectivity_error` change, a 26- | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A9 | P4d | MAJOR | "Replaceable by changing one store kind plus one test helper" is not delivered: `pg_driver()` exposes psycopg's own `sql`, `errors`, `conninfo`; call sites keep using `drv.sql.Identifier` and psycopg exception classes; c5 only checks the namespace has five names; a passthrough helper cannot make a s | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A10 | P4d | MAJOR | P2a changes how the kill switch is stored and read in `store/postgres.py` and `store/memory.py`, but the hot-file lists (P4d, P4b1, P6b2; P3a, P4d, P4a, P4b1) do not name P2a; rule 10 forbids two packages on one file at once, yet P2a and P4d are step 5 together; A1 shows order matters for correctnes | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A11 | P4d | MAJOR | Old methods "keep accepting 8 decimals" but no `max_decimals` is stated for them; memory sums in the default 28-digit context and silently rounds (`1E+22 + 0.000001`), Postgres NUMERIC sums exactly; counters have no ceiling; memory and Postgres diverge; unlisted edge inputs `Decimal("0E-1000")`, `0E | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A12 | P4d | MAJOR | The 8-process row asserts only "total reserved never exceeds the cap": a reserve that always refuses (or raises `StoreBusy` counted as refused) passes; no crash-after-commit-before-ack row (kill a worker after COMMIT, replay the same id from another process: `applied=False`, counters unchanged, then | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A13 | P4d | MAJOR | Billing tags (purpose, model) and post-booking totals have the same "closing a Protocol method is not additive" property that justified `expired`; `SpendCapExceeded` carries only `which`, not the cap or total (R215 wants numbers); P4b2 would have to change the `reserve_spend` signature and the table | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A14 | P4d | MINOR | The recommended subclass of `StoreUnavailable` is wrong: it derives from `ConfigError` (`protocol.py:41`) and `cli.py:191, :300`/`tick` treat it as "cannot reach the store" (exit 4); a busy lock reads as an outage. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A15 | P4d | MINOR | A fourth role for the sweep gives no least-privilege benefit: the runtime must hold UPDATE to settle/release, and the trigger permits open to expired for it; the maintenance identity is needed for pruning (DELETE), not the sweep. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A16 | P4d | MINOR | `created_at` is not forced on INSERT (a future `created_at` is immune to sweep); open to expired is not required to set `settled_usd = reserved_usd`; expired to settled overwrites `closed_at`. | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A17 | P4d | MINOR | String-constant rule `"psycopg"` misses `__module__ = "psycopg.errors"` (`test_p7_tick.py:606-647`) and the dotted patch path at `test_p3b_neutral_audit.py:310`; a substring rule flags them and `test_p7_tick.py`/`test_cuj.py` need allow-list entries the ticket does not list; the `review_by 2026-12-3 | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A18 | P4d | MINOR | `list_open_reservations`/sweep order by `created_at` only (no tie-break); B7 lacks "counters unchanged after sweep"; B3 lacks "settle with actual > reserved on a settled row returns the first result"; `SET LOCAL lock_timeout = <n> ms` cannot take a bind parameter (use `set_config('lock_timeout', %s, | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-adv-A19 | P4d | MINOR | `runs` rows referenced by a reservation can never be deleted (FK, no DELETE grant); table growth unbounded until P4b2; old `migrate` refuses after the new table (documented). | OPEN | reviews/P4d-round3-adversarial.md | b215b50 |
| BL-core-p4d-r3-cor-C1 | P4d | MAJOR | b adds a GRANTS row but misses `tests/test_k5_fixes2.py:260-309`: it builds a temp migration folder (`_REAL[:4]` + `0005_evidence.sql`) and `migrate()` runs `check_grants` first (`migrate.py:305`), which now fails "GRANTS names spend_reservations, which no migration creates" (`:159-161`); the test's | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C2 | P4d | MAJOR | The check requires every public `Store` method called by a test on every backend; `save_plan` and `get_plan` are called by no test under `tests/contracts/`; the plan rows are in a2, so a1 fails its own gate. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C3 | P4d | MAJOR | CHECK `(status IN ('settled','expired')) = (settled_usd IS NOT NULL)` means an expired row has `settled_usd = reserved`; the release text says `settled_usd` stays NULL; releasing an expired row violates the CHECK (23514); B3 "release on expired works" would fail. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C4 | P4d | MAJOR | Sweep sets status expired and `settled_usd` but not `closed_at`; CHECK `(status='open') = (closed_at IS NULL)` fails 23514. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C5 | P4d | MAJOR | Step 1 INSERT with `run_id REFERENCES runs` raises raw `ForeignKeyViolation` 23503 before step 3's `NotFound`; `@_writes` does not map 23503; the negative-test list says `ValueError`, the interface says `NotFound`. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C6 | P4d | MAJOR | Recommended `StoreBusy` subclass of `StoreUnavailable` contradicts the ticket: `is_connectivity_error` returns True for any `StoreUnavailable` (`protocol.py:33`), so the four "answered" callers (chain.py:533, cli.py:368, tick.py:342, :362) would see True; `StoreUnavailable` is a `ConfigError` (`prot | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C7 | P4d | MAJOR | Allow-list not enumerated: files with the string `psycopg`: `tests/test_lockin_guard.py:69,302`, `tests/demo_askdata/test_imports.py:9,51-52`, `tests/test_p7_tick.py:606-607`, `tests/test_cuj.py:301` (if prefix matching). The guard lives in `tests/` and would fail on itself. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C8 | P4d | MAJOR | A13(1) accepted three PRs (a, b, c); the ticket makes four (a1, a2, b, c) with no PENDING LEAD item; P2a ticket line 7 depends on "all three P4d PRs". | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C9 | P4d | MINOR | "All five new methods" is wrong: six new (four writes, two reads); only the four writes take locks. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C10 | P4d | MINOR | "nine fields" wrong: `Shape` adds `schema_version` (`models.py:50-52`): ten; `test_p2_postgres.py:63-64` compares exactly; check `_sql_columns` (`:49-53`) parses multi-line table CHECKs. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C11 | P4d | MINOR | DDL enforces day 2000..2100 and the id grammar; `check_day` is only `type is date`; `check_id` is conditional (PENDING): Postgres refuses, memory accepts. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C12 | P4d | MINOR | "missing kill-switch row is KillSwitchOn" is Postgres-only (memory has no row concept, `memory.py:39`). | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C13 | P4d | MINOR | FOR KEY SHARE needs UPDATE privilege on `kill_switch` (works today only because `_RW`, `migrate.py:55`); record the dependence. **NOTE (lead): the adversarial reviewer A1 rates this a BLOCKER once P2a makes the runtime role read-only; fix per A1 (plain SELECT).** | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C14 | P4d | MINOR | Whether the kill-switch read precedes the replay branch is unspecified; `ReservationConflict` vs `KillSwitchOn` precedence. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C15 | P4d | MINOR | Invariant ignores `add_spend` totals the same test runs. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C16 | P4d | MINOR | (a) table.py attribution to P4d not in A4/F6; (b) P2a-1a edits migrate/protocol/memory/postgres/table/conftest/test_store after P4d (P2a.md line 8) but P4d omits P2a; (c) P3a.md line 99 asks P4d-b for "layer 2 run logged" in Done and a `lock_timeout` decision for `migrate()`. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C17 | P4d | MINOR | Reviewers and Done sit inside the first Depends-on bullet of a1, b, c. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C18 | P4d | MINOR | 31-decimal normalize item is a mutant kill not FAIL-BEFORE; unlabelled pins (races for three methods, A5 privilege rows, "40003 not retried"); a1 registry row already passes. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C19 | P4d | MINOR | `require_backend` does not exist on ce70eb5; the test must call the existing `pg_schema` (`store_postgres.py:22-24`) and not copy the new `kinds/` files. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C20 | P4d | MINOR | Sweep "under the migration identity" in a loop: no command/CLI in scope. | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4d-r3-cor-C21 | P4d | MINOR | `_RW` cite `migrate.py:53-54` covers spend/spend_month; runs is `:47`; `PENDING` shape is checkable (dataclass reason, fix_ref, decided, review_by, keyed (top-level import, module), `test_lockin_guard.py:26-33,79`). | OPEN | reviews/P4d-round3-correctness.md | b215b50 |
| BL-core-p4c-r1-adv-A1 | P4c | MAJOR | Alert, `limits/wall` audit row and `budget wall` ERROR log are attached only to a `SpendCapExceeded` from the reserve (c). `_limits_stop` stays as it is (b): wh | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A2 | P4c | MAJOR | `_screen` calls `injection_check`, which catches every exception and returns `Verdict(flagged=True, reason_code="guard_unavailable")` (`guard/injection.py:85-10 | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A3 | P4c | MAJOR | T6 requires "counters show the worst-case amount (not less)" when real cost exceeds reserved: asserts under-counting as correct. Actual spend exceeds what day/m | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A4 | P4c | MAJOR | After 5 failed sends (~20 min outage) the row is `claimed` forever; that day's alert is lost. The tick step then RAISES every run forever (row stays in `list_un | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A5 | P4c | MAJOR | At least one recipient accepted means `mark_wall_alert_sent`. Failed recipients never retried, no per-recipient state. With `alert_to=[primary, deputy]` and Sla | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A6 | P4c | MAJOR | "LogAlertSink used only when an agent has no alert_to" does not fit one sink per `build`; empty list behaviour undefined. As written zero recipients = "no recip | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A7 | P4c | MAJOR | Template says the limit "has been reached" and "the agent will not start any new model call". A refusal means only THIS call's worst case did not fit the room l | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A8 | P4c | MAJOR | Send is synchronous inside `handle`; no required timeout on `send` ("UNVERIFIED, builder reads `SlackChannel._call`"). With up to 10 recipients one hung call bl | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A9 | P4c | NIT | "Retry window compared with the Python clock (Postgres)" claimed killed by injected-clock rows that exist only for memory. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A10 | P4c | NIT | "Day taken twice" claimed killed by T5 second-day row, but a fixed injected `now` returns the same value twice. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A11 | P4c | NIT | AST scan looks only for `.chat(`; other methods or `getattr` missed. "metered" is a label, not proof. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A12 | P4c | NIT | `agent_loop.py` has P2a-1b before P4c-2 but A9-F6 lists only P4c, P5c; PENDING LEAD item 5 covers `app.py`/`tick.py` only. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A13 | P4c | NIT | Nothing checks `max_run_usd` against the smallest possible worst case; too-low limit refuses every run (`run_budget`) from step 1: quiet outage. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A14 | P4c | NIT | Changing who is told needs no re-qualification and leaves no trace. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A15 | P4c | NIT | "Once per day" is at-least-once (crash between send and `mark` re-sends after 300 s). | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A16 | P4c | NIT | Row for an agent no longer in the registry, or with no `alert_to` now, undefined. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p4c-r1-adv-A17 | P4c | NIT | "Old code ignores open reservations and counters still bound the day" holds only if old code reads the same counters: UNVERIFIED, untested. | OPEN | reviews/P4c-round1-adversarial.md | 63549c7 |
| BL-core-p0c-r1-cor-C1 | P0c | BLOCKER | The two helper scripts are not in the ticket. It says "the two helper scripts below" and "the only code this ticket introduces" but has no script text. Grep of  | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C2 | P0c | MAJOR | `T=$(git merge-tree --write-tree ce70eb5 <ref>)` has no `--no-messages`; on a clean merge git prints "Auto-merging ..." lines (likely for #47, base 6608146), `$ | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C3 | P0c | MAJOR | `-p 55432:5432` and `-p 58200:8200` publish a trust-auth Postgres superuser and a Vault dev server (root token `root`, listens 0.0.0.0) on all host interfaces.  | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C4 | P0c | MAJOR | Conflict count includes `CHANGELOG.md` (probe counts #41=10, #43=4, c1a=4 include it) but the column is titled "Conflict files (non-CHANGELOG)" and REBASE says  | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C5 | P0c | MAJOR | Criterion 9 compares `for-each-ref` to "the Step 0 listing taken before", but Step 0 has no such command; it must be taken after `git fetch` or the fetch alone  | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C6 | P0c | MAJOR | Not exact: (a) perf run `pytest -q -m perf ...` is a placeholder; (b) heavy jobs "only through" `heavy_slot.py` yet no command wrapped, flags UNVERIFIED; (c) `s | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C7 | P0c | MINOR | pytest exit codes 2,3,4,5 and collection errors (`<error>` in junit) not handled; only 0/1 valid. A script reading only `<failure>` shows green. `suite_diff.py` | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C8 | P0c | MINOR | Hostile-input check uses `c18a`, which exists on the laptop, so the check cannot run as written. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C9 | P0c | MINOR | `env | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C10 | P0c | MINOR | Template commit id read in Step 9, after report written in Step 7. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C11 | P0c | MINOR | Missing positions: (a) CI-flag deviation from plan's bare `pytest`; (b) "full suite passes" read as "no new failure against baseline"; (c) DB_SKIP as failed run | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C12 | P0c | MINOR | "Probe commits fall away at the next `git gc`" is inaccurate: unreachable objects survive until prune expiry (default 2 weeks). | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C13 | P0c | MINOR | "Run the banned-name scan and the secret scan" has no command; those CI jobs belong to P0a/P0d (rule 9(h)) and may not exist yet. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C14 | P0c | MINOR | "Once while one other heavy job runs" does not name the job: not reproducible. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C15 | P0c | NIT | Literal `VAULT_DEV_ROOT_TOKEN_ID=root` in a public repo whose rule allows only the `AKIA...` literal; may trip the secret scan. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p0c-r1-cor-C16 | P0c | NIT | Cites "Section 2 (S0 exit)" but S0 exit is plan-v3 note 2; Problem field jargon-heavy for the "plain words" rule. | OPEN | reviews/P0c-round1-reviewer.md | e1ffdb5 |
| BL-core-p6b1-r1-cor-C1 | P6b1 | MAJOR | M14 removes `("llm","fake")` from DEV_ONLY and says T1b kills it. T1b asserts the message `llm: fake`. With M14, `_no_training_refusals` runs for fake, which de | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C2 | P6b1 | MAJOR | The ticket says T1 fails on ce70eb5 by assertion "not an import error" but copies the whole `test_training_lock.py` into the old worktree. The same file calls ` | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C3 | P6b1 | MAJOR | Ticket says refusal text never repeats `reference` (T8), but T8's canary contains `@`, which the pattern refuses at load inside pydantic (`hide_input_in_errors` | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C4 | P6b1 | MINOR | "DID NOT RAISE for all 8 (kind, env) pairs" is false for the 4 prod pairs on ce70eb5: `pilot_cfg` has `ed25519_local` with a key file and an anchor defaulting t | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C5 | P6b1 | MINOR | "a number is refused" too broad; per pydantic lax mode a midnight-aligned Unix timestamp (0, 1766966400) as int or digit string may be accepted as a date. Unver | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C6 | P6b1 | MINOR | Ticket says table.py hot for "P4d, P5b3, P5c, P6b2, P6a"; A9 F6 and A4 give "P5b3, P5b4, P5c, P6b2, P6a". `defaults.py` also changed by P4b1 (six constants), no | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C7 | P6b1 | MINOR | Per-kind minimal valid settings unspecified (anthropic needs platform + fields, bedrock region, gemini/anthropic `api_key_secret_name`, planted kind with `OpenA | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C8 | P6b1 | MINOR | T4 does not say "refused at 30". M17 (local vs UTC) not killable in `_cross_checks`, which reads the real clock; T5 covers only the injected-`today` function. | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p6b1-r1-cor-C9 | P6b1 | MINOR | `self_hosted` accepted for any openai_compat `base_url`, including a public vendor host; log shows `reference` only. | OPEN | reviews/P6b1-round1-correctness.md | 315ab52 |
| BL-core-p3a-r4-adv-A1 | P3a | MAJOR | Split rule "a ledger name without a file with a number above the folder's highest" gives the "newer than this release ... do not rename, drop or edit the ledger | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A2 | P3a | MAJOR | New newer-database message no longer contains "no file in this release". `tests/test_k2_migrations.py:387-394` has ledger `0005_evidence`, files `[:-1]` (folder | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A3 | P3a | MAJOR | Asserts message contains "newer than this release" and not "rename"; new text contains "do not rename". Cannot pass; a builder may weaken the test. | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A4 | P3a | MAJOR | Spec strips single-quoted strings and dollar-quoted bodies first, then comments. An apostrophe in a comment starts a "string". Released files have them: `0005_e | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A5 | P3a | MAJOR | M27 lists one mutant per compared kind, but several rules have no plant: `ALTER COLUMN TYPE` on an old (money) column; `SET NOT NULL` on an existing column; `AD | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A6 | P3a | MAJOR | Layer 2 is the only part reading old code against a new schema (plan: "previous release code reads the new schema or fails loudly"). It is manual, runs once, an | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A7 | P3a | MAJOR | Runbook for a PR #41/#49 database is mostly "wait for the PR that adds the renamed file" (UNVERIFIED); 6(f) asked for a written path. After renaming `0005_measu | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A8 | P3a | MINOR | Hand recipe says "in psql with ON_ERROR_STOP on" with no command (`psql -v ON_ERROR_STOP=1`) and no schema/`search_path` instruction while `migrate` uses `curre | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A9 | P3a | MINOR | Nothing checks a late file is safe after later applied migrations; a data-changing late file (UPDATE/DELETE as 0003) can run on reshaped rows. | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A10 | P3a | MINOR | "Word for word" old messages conflict with `ascii()` on every name (`ascii('0002_Bad.sql')` adds quotes; `test_k2_migrations.py:52-55` asserts the exact string) | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A11 | P3a | MINOR | `SET LOCAL` allowed, so `SET LOCAL ROLE x` / `SET LOCAL search_path` last for the whole run incl. the grants step (`current_schema()`); `SELECT set_config('role | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A12 | P3a | MINOR | Order 6(g) says recommended answers in questions-for-lead.md are final, yet two paths (with/without manifest) are built, doubling the layer-1/test matrix. Uncon | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A13 | P3a | MINOR | CHANGELOG is append-only per rule 10; P3a rewords four lines (fine if flagged, the lead must accept the exception). `tests/test_migration_postgres.py` depends o | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p3a-r4-adv-A14 | P3a | MINOR | `test_late_number` seeds ledger "0001-0003 and 0005" but `test_order_check_sees_committed_ledger` says only "hand-applies 0005 and its ledger row". Test (g) "fo | OPEN | reviews/P3a-round4-adversarial.md | 60e16a5 |
| BL-core-p6b1-r1-adv-A1 | P6b1 | MAJOR | Statement not bound to what it describes: operator can change `base_url`/`platform`/`region`/key type (the Gemini free vs paid case) and keep a fresh statement; | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A2 | P6b1 | MAJOR | "A fifth backend cannot be added silently" rests on T9, whose set is read from `TABLE` and compared with `TABLE`: a tautology; no mutant. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A3 | P6b1 | MAJOR | `detector: bedrock_guardrail` sends client text to a provider and is left uncovered; the ticket recommends "cover it" but is written for "no"; no default stated | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A4 | P6b1 | MAJOR | Hot-file analysis incomplete: P2a adds a `limits` section to `config.py` and is a `table.py` editor (P4c line 20); P4d edits `table.py`; P4c edits `test_k3_pilo | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A5 | P6b1 | MINOR | No clock seam at Config load; call-site mutant survives in UTC CI; load-level rows can flake at midnight UTC. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A6 | P6b1 | MINOR | "A number is refused" probably false: lax mode accepts midnight-aligned ints (e.g. 1767225600); probe used non-aligned values. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A7 | P6b1 | MINOR | Pattern allows a 12-digit account id inside an ARN (logged INFO, committed); free text can hold a person/party name. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A8 | P6b1 | MINOR | Age check only at start-up; long-running process never re-checked; restart on day 91 is an availability event with no prior signal. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A9 | P6b1 | MINOR | `no_training`/"lock" read as a technical block; honesty only in prose. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A10 | P6b1 | MINOR | T1 "DID NOT RAISE for all 8" false for prod (other refusals); valid-statement acceptance asserted only in pilot. | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A11 | P6b1 | MINOR | `defaults.py` "two constants" vs "three"; none of the 8 PENDING LEAD items are in `questions-for-lead.md` (order 3). | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p6b1-r1-adv-A12 | P6b1 | MINOR | No mutants for T8 (secret-suffix rename), "more than one message per kind", first-match order (a)-(e), log skipped when `llm` injected into `App` (app.py 162) o | OPEN | reviews/P6b1-round1-adversarial.md | 315ab52 |
| BL-core-p5b2-r1-cor-C1 | P5b2 | MAJOR | Lock forbids downgrading `exception-variable` rows but nothing stops a human setting `class=LITERAL` on a non-literal `unproven-origin` row (a `reason` suffices | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C2 | P5b2 | MAJOR | Subprocess `python -I -c "import tools.gen_config_error_sites"` cannot pass: `-I` drops cwd/PYTHONPATH, `tools` is not installed; M17 killed for the wrong reaso | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C3 | P5b2 | MAJOR | D2/D7 require wrapping non-literal f-string parts in `t1()`; wrapping ~112 OPERATOR sites changes their hash, they become stale plus new blank `unproven-origin` | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C4 | P5b2 | MAJOR | Scan sees direct constructions only; `k1b/bundle.py` writes ~29 messages via `raise _fail(case, f"...")`; a new `_fail(case, f"{exc}")` is invisible. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C5 | P5b2 | MAJOR | No mutants for report lists `missing_code`, `wrong_literal`; `write()` keeping human fields; `load_csv` refusals (header, duplicate `site`, non-ASCII, `REASON_M | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C6 | P5b2 | MINOR | Rule says "plain assignment"; `tools.py:119-120` (`fields = ", ".join(... exc.errors())` then `f"...({fields})"`) is a derived value, tainted by design section  | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C7 | P5b2 | MINOR | Hash of "the whole raise-argument call" undefined for `return BundleError(...)` (`bundle.py:107`) and bare `raise A`. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C8 | P5b2 | MINOR | `kind` recorded "as written" (alias `CE`, `mod.A`); M1 only killed if `B(A)` file sorts before `A`'s file, unit (4) fixes no names. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C9 | P5b2 | MINOR | Combines two edits (reads `*.pyc`/non-`.py`; skips subfolders). | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C10 | P5b2 | MINOR | `code` "only for FOREIGN" not enforced; no report list. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C11 | P5b2 | MINOR | `python tests/config_error_sites_mutants.py` puts `tests/` not repo root on sys.path; evidence 3 `--write` leaves unproven rows blank (fine, unstated). | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C12 | P5b2 | NIT | "No line numbers so moving code does not change the row" true only within the same symbol. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p5b2-r1-cor-C13 | P5b2 | NIT | Memo-5 row lists 3 files; ticket also changes `tests/test_diagnostics_hostile.py`, `CHANGELOG.md`, adds `tests/config_error_sites_mutants.py`. | OPEN | reviews/P5b2-round1-reviewer.md | 45fe05b |
| BL-core-p0a-r1-cor-C1 | P0a | BLOCKER | Option A's only bypass actor is the Admin role, but the ticket itself says the cloud token very probably acts as the owner's admin account: role-based bypass gi | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C2 | P0a | MAJOR | `PUT .../pulls/<n>/ccr/auto_merge` is not a GitHub endpoint; a 404 proves nothing; a draft PR cannot merge anyway. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C3 | P0a | MAJOR | Throwaway PR "changes one comment line in `handover/README.md`": markdown has no comments, `handover/` is not on main; a successful merge lands in public histor | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C4 | P0a | MAJOR | `security` scans every fetched branch (gitleaks `--all`, `fetch-depth: 0`; P0d history pass): probe branches make `security` red on every PR; proof 2's control  | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C5 | P0a | MAJOR | Cloud token expires 2026-11-05 22:58 UTC, hours after drafting; probes would fail on auth. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C6 | P0a | MINOR | Exact token expiry printed in a public file (credential metadata). | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C7 | P0a | MAJOR | Heading says "none holds a secret value" but the author read 5 of 17; 12 unread. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C8 | P0a | MAJOR | Fixes the 17 findings only; every future branch with test passwords re-reds `security`; "none expected" argued only for handover text. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C9 | P0a | MAJOR | "No deletion of branches" is instruction text, not a control; contents write lets the token delete/force-push any non-main branch; `handover-src/*` backups may  | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C10 | P0a | MAJOR | Plan rule 9 says P0a records the owner's approval for the cloud pushes (owner, 2026-11-05); no step/file/pass criterion. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C11 | P0a | MAJOR | `Analyze (python)`, `Analyze (actions)`, `SonarCloud Code Analysis` made required without checking they report on every PR type (docs-only, `.gitleaksignore`-on | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C12 | P0a | MINOR | "SonarCloud (its token)" in Actions secrets contradicts `ci.yml` (no job uses a secret; SonarCloud external app); `gh secret list` skips Dependabot/environment  | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C13 | P0a | MINOR | Finding 1 says `tests/test_repo_rules.py` fails any other licence text; it checks only files named `LICENSE` and `pyproject.toml` (lines 32-42). | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C14 | P0a | MINOR | "Repository owes no library notice" not scoped to Unicode-derived `_confusables.py`, which ships in the wheel; root `THIRD-PARTY-NOTICES.md` would not travel wi | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C15 | P0a | MINOR | Dangling references ("Step 4", "step 6" do not exist; field 16 "section 8" should be 9); probe order not placed among steps. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C16 | P0a | MINOR | (a) `git tag -l` local only (use `ls-remote --tags`); (b) no `git fetch` before `origin/main`; (c) branch for `handover/evidence` unclear; (d) Step 1 pushes bef | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C17 | P0a | MINOR | Raw `gh api repos/...` JSON committed publicly may carry `temp_clone_token`, lead's permissions. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C18 | P0a | MINOR | PENDING LEAD list incomplete: (a) suppressing 17 findings by fingerprint, (b) tag ruleset scope (`archive/*`, `v*`), (c) P0d fixing `ci.yml` header, (d) backup- | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C19 | P0a | MINOR | S1 `rules/branches/main` lists rule types, only S8's jq shows checks; S5 pushes a vendor-inspired string into public history; S7 failure handling missing. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p0a-r1-cor-C20 | P0a | MINOR | No command for unmerged heads or PR mapping. | OPEN | reviews/P0a-round1-reviewer.md | c826f2d |
| BL-core-p4c-r1-cor-C1 | P4c | MAJOR | `_limits_stop` unchanged; audit row, log and alert attach only to the reserve refusal. When the day total is already at/over the limit `limits.blocked()` return | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C2 | P4c | MAJOR | Zero recipients (allowed in dev; `deferred.py` requires `alert_to` only in pilot/prod): nothing sent, claim never marked, re-claimed 5 times, tick fails permane | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C3 | P4c | MAJOR | (a) one recipient accepting marks `sent`; the others never retried or audited as lost; (b) send and mark are two steps (crash re-sends; a send slower than `retr | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C4 | P4c | MAJOR | Rows at `max_attempts` stay `claimed` forever; no DELETE; tick step raises on them every 300 s: permanent exit 1 hiding other steps' failures; pruning deferred  | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C5 | P4c | MAJOR | `reaches_person = ("channel", channel.name) not in DEV_ONLY`; `build` may get an injected channel (`app.py:67,170`) which `DEV_ONLY` never checks (only configur | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C6 | P4c | MAJOR | One `PRODUCERS` row added, but `test_k5_round9.py:177-205` requires `set(DRIVERS) == {r[0] for r in PRODUCERS}`; `test_k5_round12_fuzz.py:125` has its own map;  | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C7 | P4c | MAJOR | Recipe "worktree at ce70eb5, copy new tests" fails: the P4d harness (`store_pair`, `connect_runtime`, `pg_driver`, `require_backend`, `HADAVIN_REQUIRE_PG`) is n | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C8 | P4c | MAJOR | `tickets/P4b1.md` rev 1 exists and conflicts: (1) P4b1 already creates `Caps` (`meter.py`) and `Limits.caps`/`Limits.hold`; P4c-2 redefines them; (2) R2 wants ` | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C9 | P4c | MAJOR | Tick step `retry_wall_alerts(ctx)` needs the `WallAlerter` via `ctx.app`; `App` (`app.py:45-59`) has no alerter field; ticket only says `build` passes `Hooks(wa | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C10 | P4c | MAJOR | Texts said to "stay true and tested" are false/misleading: (a) "resets 00:00 UTC / 05:30 India" used for the monthly wall too; (b) "has reached its limit"/"will | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C11 | P4c | MINOR | Two things named `WallAlert` (row model; frozen dataclass). | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C12 | P4c | MINOR | P4d forces `created_at := clock_timestamp()` by BEFORE INSERT trigger; `wall_alerts` triggers omit it: a future `claimed_at` is never "older than `retry_after_s | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C13 | P4c | MINOR | `AuditEvent` (`models.py:188-215`) has no field for sink name, recipient count, agent id or day. | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C14 | P4c | MINOR | `tickets/P2a.md:78` says "Recommended owner: P4c" for StopGate wiring; P4c declines, recommends a non-existent P2a-1d. | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C15 | P4c | MINOR | Scan covers only `.chat(`; `guard/bedrock_guardrail.py` (`.apply_guardrail(`, paid) is in `MODEL_CALLERS` and not metered; demo pipeline too. | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4c-r1-cor-C16 | P4c | MINOR | `Money` is `config.py:40-47` (ticket says 36-47); `tick.STEPS` is `tick.py:249-266`. | OPEN | reviews/P4c-round1-correctness.md | 63549c7 |
| BL-core-p4b1-r1-adv-A1 | P4b1 | BLOCKER | Written against P4d rev 4; rev 5 (b, `settle_spend`) still makes `actual > reserved` a `ValueError` leaving the row unchanged ("settles at the reserved worst ca | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A2 | P4b1 | MAJOR | "`run_id` iff run cap not `None`" stops runs without `max_run_usd` (dev, uncapped) from booking `runs.cost_usd` (P4d allows `run_id` with `run_cap=None`); P4c-2 | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A3 | P4b1 | MAJOR | Oracle inconsistent: each granted hold settles at HALF inside the attempt loop; settling frees capacity so later attempts can be granted beyond `floor(cap/amoun | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A4 | P4b1 | MAJOR | Meter takes the day in a configurable zone (`Asia/Kolkata`); `Limits.blocked`/`charge` still use `now().date()` in UTC (`limits.py:18, 24`): meter books one day | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A5 | P4b1 | MAJOR | Every failed call (connect refused, 4xx, 429 storm, outage) books its full worst case permanently; P4d "expired" never frees counters; a retry storm drains the  | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A6 | P4b1 | MAJOR | Body succeeded but the exit settle fails (e.g. `StoreBusy`): no retry; reservation stays open at worst case; "P4b2 sweep will expire it" keeps the worst case; l | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A7 | P4b1 | MAJOR | One estimate error stops ALL agents until a person resets; zero-overshoot rests on unverified assumptions (1 byte/token, 3x per document byte, no check of real  | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A8 | P4b1 | MAJOR | Mismatch with P4c-2: P4c-2 puts one wrapper on `deps.llm` with a run scope opened per step (judge call covered); -b binds ONE agent/run at construction, cannot  | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A9 | P4b1 | MAJOR | Needs the lead first for the mapping (A9 F2 already says replace `askdata/meter.py`, but the mapping is new architecture): moves an offline demo onto a core sto | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A10 | P4b1 | MINOR | Stale vs P4d rev 5: header says rev 4; "all four" P4d PRs (there are five); needs 2-7 adopted in rev 5; only item 1 open; `OverBudget` carries reason names only | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A11 | P4b1 | MINOR | Release-by-id after "any other exception" can hit `NotFound` while the original transaction is still in flight and commits later (orphan, A6); `except Exception | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A12 | P4b1 | MINOR | -b shim calls `FakeLLM` directly when `MeteredLLM` is missing: nothing capped, fails trivially, shows no old behaviour. | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A13 | P4b1 | MINOR | No row/mutant for: `SpendMicro.__sub__` negative; bound `MAX_USD x 1e6` exact and +1; `ceil_cost` zero denominator/negative numerator; `BusinessMoney` ctor (`mi | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A14 | P4b1 | MINOR | Hardcoded in -b: framing 16, 3 bytes/document byte, 10**9 token cut-off, `halt` grammar 40; `zoneinfo` needs tzdata on slim images (even "UTC"); `clock=models.n | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A15 | P4b1 | MINOR | Wrapper sizes with the construction-time `Route`; inner kind builds its own request from its own config; "a reload cannot change the price" half true. | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4b1-r1-adv-A16 | P4b1 | MINOR | `Limits.hold` builds `Meter` lazily without a lock; `Limits.stop("meter:estimate_exceeded")`: P2a-1b masks `by`; registry values with >6 decimals load today, so | OPEN | reviews/P4b1-round1-adversarial.md | 15d01fa |
| BL-core-p4d-r4-adv-A1 | P4d | MAJOR | `add_spend`/`add_cost` refuse >8 decimals with ValueError, but real callers compute `(tokens x price)/1_000_000` unrounded (`llm/common.py:166-169`, ` | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A2 | P4d | MAJOR | Wrapper retries 3x on 40P01; stress passes on "no raw error, no StoreBusy"; inverted lock order (b15) is retried and hidden; same masking on every rac | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A3 | P4d | MAJOR | Memory `clock` defaults to `time.monotonic` for age but must also give a UTC date and datetimes (`created_at`, `closed_at`, `expired_at`): one monoton | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A4 | P4d | MAJOR | Counter of 10**22 unreachable after a2-i (`MAX_USD` 10**12, `MAX_COUNTER_USD` 10**15): max 16+8 = 24 digits < 28-digit context, so i7 is equivalent an | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A5 | P4d | MINOR | Orders say terminal status `expired`; ticket's `expired` can still be settled down once or released; sensible, but not in PENDING LEAD. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A6 | P4d | MINOR | Run checked for existence only, not that `agent_id` equals the run's: wrong agent books cap on one agent, run counter of another. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A7 | P4d | MINOR | `MAX_COUNTER_USD` enforced only in `add_spend`/`add_cost`; `reserve_spend` with caps None can exceed 10**15, after which every `add_spend` is refused  | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A8 | P4d | MINOR | `set_config('lock_timeout', %s, true)` with an int: psycopg3 sends an int OID, `set_config` wants text; likely runtime error (reasoned). | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A9 | P4d | MINOR | Total across retries not enforced inside one transaction (`statement_timeout` is per statement, ~6 lock-taking statements); not said that back-off sle | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A10 | P4d | MINOR | Trigger tested with one forbidden update; allowed-transition matrix (16 pairs, `settled_usd`/`closed_at`/`expired_at` edits) untested. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A11 | P4d | MINOR | Created by an admin connection, so Postgres only, yet stated for both; memory half (silent clamp b11) untested; b12 relies on GIL timing; no mutant fo | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A12 | P4d | MINOR | Under xdist the silent-skip guard does nothing: fail-open if `-n` is added. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A13 | P4d | MINOR | Cap decimals not stated; registry budgets may have >6; fails closed or differs; rounding direction unstated. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A14 | P4d | MINOR | When the cap-qualified UPDATE matches no row no lock is taken; the later read is plain; `current` in the error may differ. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A15 | P4d | MINOR | Same id, closed row, different content: `ReservationConflict` or `StaleState` first? Untested. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-adv-A16 | P4d | MINOR | `limit` max 1000, no cursor: >1000 open rows cannot be reconciled. | OPEN | reviews/P4d-round4-adversarial.md | d12bfa7 |
| BL-core-p4d-r4-cor-C1 | P4d | MAJOR | Same as adversarial A4: counter 10**22 unreachable through the public API; i7 survives; fail-before works only on ce70eb5 (`memory.py:196-198`). | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C2 | P4d | MAJOR | Misses the unrounded LLM-cost caller class (`llm/common.py:166-169`, `llm/fake.py:50-53`; `limits.charge` `limits.py:18` from `agent_loop.py:314/:440` | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C3 | P4d | MAJOR | 40P01 retry (3x) hides inverted lock order. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C4 | P4d | MAJOR | No table has a foreign key (no `REFERENCES` in 0001-0005); a2-ii cannot exercise the mapping; w10's killer is a later PR; in b the run pre-check retur | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C5 | P4d | MAJOR | Guard flags any `pg_driver(` call outside a file allow-list; P4d's own new tests (`test_store_atomic.py`, `test_store_hostile.py`, `test_store_reserve | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C6 | P4d | MINOR | `get_kill_switch` is `postgres.py:444-451`, not 441-451. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C7 | P4d | MINOR | P3a "layer 2 run logged for ALTER-only migrations" is `P3a.md` line 100, not 99. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C8 | P4d | MINOR | `a._db is not b._db` raises AttributeError on MemoryStore (`memory.py:29-43`). | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C9 | P4d | MINOR | "Inputs (30)" but ~39 items; "31-decimal item" absent (29, 40, 1000); `limit`/`older_than_s` rows testable only after b; whether old `add_spend` appli | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C10 | P4d | MINOR | ce70eb5 raises raw `UniqueViolation` (`postgres.py:293`), so `pytest.raises(StaleState)` errors rather than failing an assertion. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C11 | P4d | MINOR | `octet_length(meta::text) <= 2000` vs memory's undefined JSON encoding (JSONB text differs from `json.dumps`). | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C12 | P4d | MINOR | Only `add_spend` and `record_decision` set `lock_timeout`; `set_config(..., true)` does nothing outside a transaction; a blocked `transition`/`set_kil | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C13 | P4d | MINOR | New ValueError on `add_tool_call` etc.; loop handling (`agent_loop.py` ~486) not analysed for NUL/binary tool output. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p4d-r4-cor-C14 | P4d | MINOR | P4d counts the money queue "P4a and P4b1" (A11); `P4c.md` line 11 says "P4a, P4b1, P4b2 and P4d"; plan section 9 names `evidence-p4d.md`. | OPEN | reviews/P4d-round4-correctness.md | d12bfa7 |
| BL-core-p3a-r4-cor-C1 | P3A | BLOCKER | The `gone` split by number is wrong for the package's own case: ledger 0001-0004 + `0006_evidence`, folder ends at 0005: 6>5 so the "newer, do not ren | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C2 | P3A | MAJOR | FAIL-BEFORE 7 asserts text contains "newer than this release" and NOT "rename", but the new text says "do not rename..."; the old text also has "renam | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C3 | P3A | MAJOR | `tests/test_k2_migrations.py:387-394` breaks (ledger 0001-0005, patched list drops 0005: 5>4 gives the "newer" text, test matches "no file in this rel | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C4 | P3A | MAJOR | "Old messages word for word" but names use `ascii()` which keeps quotes; `test_plant_badly_named_file_is_caught` (test_k2:50-55) compares exactly. Fix | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C5 | P3A | MAJOR | `statement_text` strips single-quoted strings before comments: released files have apostrophes in `--` comments (0004 l.4 "deployment's", 0005 l.1/19  | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C6 | P3A | MAJOR | Refusal (b) lists only `SET ROLE`/`SET SESSION AUTHORIZATION` but `SET LOCAL ROLE`, `SET LOCAL SESSION AUTHORIZATION`, `SET [LOCAL] session_replicatio | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C7 | P3A | MAJOR | M5 (accept directories/dangling links) survives FAIL-BEFORE 4-5: removing `is_file()` still gives an OSError "cannot be read" refusal. Fix: assert the | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C8 | P3A | MAJOR | Layer 1 planted cases only add/change; no REMOVAL (`DROP TRIGGER audit_entries_append_only`, `DROP CONSTRAINT runs_state_check`, `DROP TABLE`, `ALTER  | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C9 | P3A | MAJOR | `ACCEPTED_CHANGES` consumer named is P4d-b `CHECK (usd >= 0)`, which P4d.md does not have; the real first consumer is P2a-1a (trigger on old `kill_swi | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C10 | P3A | MINOR | `0000_a.sql` matches NAME, gap check `range(1,max+1)` never reports 0. Refuse number 0 or state intent; test. | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C11 | P3A | MINOR | P4d.md line 183 cites P3a.md line 99; the layer-2 request is line 100. P3a says P4d's `require_backend` replaces the check "if it merges first" but P3 | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C12 | P3A | MINOR | "runbook cases vii and v" do not exist (runbook is (a)-(f)); two lettering schemes collide; audit/evidence columns are readable in 0002/0005. Fix refs | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C13 | P3A | MINOR | Recipe omits that psql must use the same `search_path`/schema as `migrate`. Add "same DSN options". | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C14 | P3A | MINOR | `ALTER TYPE ... ADD VALUE` is allowed in a transaction since PG 12: give it its own reason; missing refusals `CLUSTER` without table, `DISCARD ALL`, ` | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C15 | P3A | MINOR | No test kills dropping the "start of a statement" anchor (mid-statement `END`, `CASE...END`, `COMMENT ON ... 'begin'`); `BEGIN ATOMIC ... END;` behavi | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C16 | P3A | MINOR | FAIL-BEFORE 6 must say "real files plus the planted file"; the planted file alone gives ConfigError on ce70eb5 before connecting. | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p3a-r4-cor-C17 | P3A | MINOR | M13 killer ("ledger fuzz case") non-specific; name a pure test: applied `{"٠٠٠٩_x"}`, file `0005_a`, expect `[]`. | OPEN | reviews/P3a-round4-correctness.md | 60e16a5 |
| BL-core-p5a-r1-adv-A1 | P5A | BLOCKER | `detail`/`t1` content check is only "unchanged by `redact_text(text,{})`"; the ticket admits `input_value='Jane Doe'` passes; charset allows bare name | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A2 | P5A | BLOCKER | Closed code set is not closed in practice: AST discovery misses `type()`-built/aliased/uninstalled-extra classes; `OWN_CODES` keyed `module:Qualname`  | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A3 | P5A | MAJOR | `phase` rules for psycopg (sqlstate class 28/08, `OperationalError` without sqlstate, `ssl.SSLError` in cause) rest on unobserved psycopg behaviour; g | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A4 | P5A | MAJOR | Locator rule (`f_globals is vars(sys.modules[name])` and `co_filename == module.__file__`) untested on wheels/.pyc-only/namespace/frozen; misfire turn | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A5 | P5A | MAJOR | Foreign `module.qualname` printed if identity + charset hold: a runtime-created class (`create_model("Jane_Doe")` with a real `__module__`) leaks docu | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A6 | P5A | MAJOR | Corpus teeth weak: leak check knows only planted canaries; teeth test needs one leaky subject (`f"{type(e).__name__}: {e}"`) which is nearly always sa | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A7 | P5A | MAJOR | Oracle depends on P1b `scan_hit`/`line_view` names (may be renamed); P1b bug becomes corpus-wide false leak; stale P1c text (P1c out of v1 per order 7 | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A8 | P5A | MAJOR | Scope vs "cut surface" (order 7(3)): 21 codes, 20 fact keys, 12 provider types, 26 validation types, JSON message table, schema walker, `t1`, `detail` | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A9 | P5A | MAJOR | Couplings: P5a asserts P1b/P1c `TextnormError` subclasses not in code (P1c cut); P5c redactor codes only by prose; `FactKey.reason` (D8) not added so  | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A10 | P5A | MAJOR | `safe_value` veto relies on core redactor coverage (hidden dependency; a redactor regression leaks with no failing P5a test); order of checks unstated | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A11 | P5A | MAJOR | `validation_text` key paths: discriminated-union tags and `RootModel[dict[...]]` put document text in `loc`; `FIXED_TEXT` canary test runs on one pyda | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A12 | P5A | MAJOR | `diagnose` "never raises" but catches `Exception, RecursionError, MemoryError` (redundant); `CancelledError`/`GeneratorExit` raised by a hostile `__ge | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A13 | P5A | MAJOR | Fail-before shim is hand-written by the corpus author: proves only the author's model of "today". Fix: run the corpus against the real functions at `e | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A14 | P5A | MINOR | `DIAG_MAX_B_CHARS` and `DIAG_TIME_BUDGET_S` have no values (boundary tests unwritable); wall-clock budgets are flaky. Give numbers; assert algorithmic | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A15 | P5A | NIT | 169-row minimum is a count not a coverage argument; `fact_bounds` duplicates `test_facts_bounds_table`; unique `(factory,args)` meta-test blocks hosti | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5a-r1-adv-A16 | P5A | NIT | Template "Existing core code reused" lacks `k1b/atomic`, `k1b/redaction`, `stats`; ticket ~28k tokens. State the `k1b/redaction` check; move the 51-ro | OPEN | reviews/P5a-round1-adversarial.md | def2d2a |
| BL-core-p5b1-r1-adv-A1 | P5B1 | MAJOR | `describe` prints `type(exc).__name__` behind a shape check only; botocore creates a class per modelled error named like the code (verify), so `Access | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A2 | P5B1 | MAJOR | Ticket says P5a not on disk, but P5a.md exists and differs: `diagnose` reads only `status`, `error_type`, `request_id`, `retryable` (no `retry_count`) | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A3 | P5B1 | MAJOR | Hot files: P4b2 edits `llm/protocol.py`, `retry.py`, `common.py`, `bedrock.py` (new `status_of` hook duplicates `facts.status`); no ticket orders P4b2 | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A4 | P5B1 | MAJOR | R4 tripwire cannot fail: adapters read via `safe_attr`/`safe_facts` which swallow `Exception`; `__getattribute__` does not intercept `str(exc)`/`repr( | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A5 | P5B1 | MAJOR | Library loggers omitted: httpx logs reason phrase at INFO, botocore headers/body at DEBUG (verify); R14 may fail and P5b1 cannot fix it; Stubber skips | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A6 | P5B1 | MAJOR | "Adapter can raise nothing" true only for the facts adapters: `transient()` -> `_chain` (`getattr(e,"reason")` unguarded), kind `retryable` hooks (`be | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A7 | P5B1 | MINOR | "Identical for every input" not exact: raising `status_code` property used to escape, now a plain `ProviderError` that `askdata/pipeline.py:163` count | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A8 | P5B1 | MINOR | `default_facts` precedence unstated: `URLError(TimeoutError())`; say any `TimeoutError` in the chain wins, then `OSError`/`SSLError`; rows. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A9 | P5B1 | MINOR | Kind adapters with no library class fall to `status_error_type(status)` only; end each with `return default_facts(exc)`. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A10 | P5B1 | MINOR | Surviving mutants: `retry_count` after retried refusal, neutral status table edges, added table rows, Claude request_id without `req_` (8-40), 100-cha | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A11 | P5B1 | MINOR | R6 grammar accepts any `( [a-z_]+)?`; enumerate `ProviderErrorType` values. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A12 | P5B1 | MINOR | R7 guard flags `with_retry`'s own f-string; name sanitiser functions, one plant each; P5b3's guard supersedes. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A13 | P5B1 | MINOR | Reason for the vendor-table deviation from D5 overstated (rule c has no vendor error codes); reword, keep as a lead decision. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A14 | P5B1 | MINOR | `HADAVIN_DEBUG=1` (`cli.py:79-82`) prints raw cause; D1 puts it in P5b3; consider a closed `cause_kind` fact and `raise ... from None`. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A15 | P5B1 | MINOR | Status 777 retried/billed and unbounded success-body read are lead decisions; P4b2.md does not carry them; add pointer. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A16 | P5B1 | MINOR | `exc.close()` only on the raise path; retried `HTTPError` keeps a body open; extend R8. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A17 | P5B1 | MINOR | Jargon ("zone T2", "tripwire", "R1P", "mutant") unexplained; Problem field over 5 sentences. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p5b1-r1-adv-A18 | P5B1 | MINOR | Stale statements (P4a/P5a "not present", P6b1 touches every backend). Update on rev 2. | OPEN | reviews/P5b1-round1-adversarial.md | 30fd0e8 |
| BL-core-p4b1-r1-cor-C1 | P4B1 | MAJOR | `OverBudget((which+"_budget",))` gives `day_budget`/`month_budget`, but `limits.py:27,29` print `daily_budget`/`monthly_budget` (T2 expects `("daily_b | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C2 | P4B1 | MAJOR | `run_id` iff run cap not None conflicts with P4d-b (allows `run_id` with `run_cap=None`) and P4c-2 R6 (loop passes `run_id` on every reserve); `max_ru | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C3 | P4B1 | MAJOR | Written against P4d rev 4 ("all four" PRs; rev 5 has five); Needs 2-7 already adopted; only Need 1 (settle above reserved) open and rev 5 keeps it as  | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C4 | P4B1 | MAJOR | `OverBudget` carries only names; P4c needs `which`, cap, current, requested and the UTC day (a refusal returns no `Hold`); P4c mutant m4 unkillable. M | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C5 | P4B1 | MAJOR | Overshoot turns the GLOBAL kill switch on (PENDING LEAD 4); P4c rule 6/T6 expect per-run `NEEDS_PERSON run_budget`, audit `guard/estimate_exceeded`, n | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C6 | P4B1 | MAJOR | Overshoot fallback: no rule that excess is booked only on `applied=True` (retry/second process loses or double-books); stored row says reserved so rep | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C7 | P4B1 | MAJOR | `Config.meter` (`cap_zone`, `max_hold_s`) has no path into `Limits.hold` (`app.py:171` builds `Limits(store,audit,reg)`; `app.py` not in Files, a hot  | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C8 | P4B1 | MAJOR | T5 settles inside the run so grants can exceed `floor(cap/amount)`; -b 8-thread row same flaw (P4d B4(i) holds open until a second barrier). | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C9 | P4B1 | MAJOR | T6 registers `@kind("meter", name)` but conftest only builds fixtures per capability via `_kinds("store")` (lines 29-70); nothing consumes `KINDS["met | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C10 | P4B1 | MAJOR | Fail-before copies only the T2 file to ce70eb5, but it imports `hadavin_sdk.money`/`meter` (collection ImportError, not AssertionError). Lazy imports  | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C11 | P4B1 | MAJOR | Step 0 table: gate 1 still fails A for `Decimal` though A1(3)/A9 B1 say that is no longer a reason; owner notice says Intake settles the same reservat | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C12 | P4B1 | MAJOR | -c "holds a `Limits`-style handle": `Limits` needs `Registry` and `AuditSink` the demo lacks; `worst_case_usd` (`pipeline.py:23,145`), `remaining()`,  | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C13 | P4B1 | MINOR | -b fail-before shim fails because nothing exists; label "new feature; killed by mutants". | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C14 | P4B1 | MINOR | `Hold.record(..., halt=)`: no callback/stop call/test; define or remove. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C15 | P4B1 | MINOR | T4(b) import allow-list omits `hadavin_sdk.money` (and stdlib `zoneinfo`, `contextlib`, `logging`). | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C16 | P4B1 | MINOR | M10 claims a T5 row that is absent; M18 claims a T2 kill-switch row that is absent; missing mutants (release on OverBudget/store_busy, `Limits.caps`,  | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C17 | P4B1 | MINOR | Only `reserve` error mapping specified; add one table for settle/release; `NotFound` on reserve for an unknown run is named `unknown_reservation` (mis | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C18 | P4B1 | MINOR | Does not say how "1 byte/token" relates to `llm/common.estimate_tokens` (3 chars/token, `:59`), `k1b/loop.py:115 worst_case_usd`, demo `worst_case_usd | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C19 | P4B1 | MINOR | `zoneinfo` not used in core; `tzdata` Windows-only in `uv.lock`; use `datetime.UTC` for default or pin. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C20 | P4B1 | MINOR | memo-2 gap 6 overstated (`Hold.age_s()` logs one line; sweep uses DB clock). | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C21 | P4B1 | MINOR | PR #48 numstat claims UNVERIFIED by the reviewer; builder re-measures. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C22 | P4B1 | NIT | T2 "1.20 or less, in fact at most 0.80": 1.20 exceeds the 1.00 cap. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C23 | P4B1 | NIT | P4d rev 5 line 11 lists P4b1 among editors of `store/protocol.py`/`postgres.py`; P4b1 says none; record the deviation. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C24 | P4B1 | NIT | "Existing core code reused" lacks what was checked and rejected. | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b1-r1-cor-C25 | P4B1 | NIT | Literals (`2` in `orphan_age_s`, `{1,40}`, 3, 16) vs "no other number in `meter.py`". | OPEN | reviews/P4b1-round1-correctness.md | 15d01fa |
| BL-core-p4b2-r1-cor-C1 | P4B2 | BLOCKER | Maintenance grant `UPDATE (status, settled_usd, closed_at)` omits P4d's twelfth column `expired_at`; P4d's sweep claim sets `expired_at` (P4d.md:135), | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C2 | P4B2 | MAJOR | L1-L7 claimed on each of four kinds, Bedrock cannot do L4/L5: botocore `EndpointConnectionError` is not an `OSError`, no `reason`, cause only implicit | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C3 | P4B2 | MAJOR | *refused* = every 4xx except 408 is a deny-list, contradicts rule 1 (positive proof); Bedrock `ModelErrorException`/`ModelStreamErrorException` are 42 | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C4 | P4B2 | MAJOR | Mutant a1 changes only the CLASS default `ProviderError.refused` to 1, but `with_retry` stamps INSTANCES (`refused=0`), so T3/L5/T9 do not see it; T9  | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C5 | P4B2 | MINOR | Header cites P4d revision 4 and "all four pull requests"; P4d is rev 5 with five sub-tickets (a1, a2-i, a2-ii, b, c); re-check `older_than_s`, `limit` | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C6 | P4B2 | MINOR | "UNLESS the error already carries its own instance stamps" is dead code: a ProviderError from the callable hits `except ProviderError: raise` before t | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C7 | P4B2 | MINOR | `call_bound_s` warning formula 2 x `call_timeout_s` for every kind; Bedrock connect timeout is `min(10, call_timeout_s)` (`bedrock.py:47-48`) so its b | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C8 | P4B2 | MINOR | Sweep SELECT shown without P4d's tie-break `ORDER BY created_at, reservation_id`; copy P4d's statement verbatim (P4d.md:135). | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C9 | P4B2 | MINOR | H1 hostile role names: `_ROLE` is lowercase-only (`migrate.py:70`) so most already refused on ce70eb5; real fail-before cases are lowercase pseudo-rol | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C10 | P4B2 | MINOR | E4/upgrade: every existing Postgres deployment's tick exits 1 each cycle until `maintenance_dsn_secret_name` is set; app start-up does not refuse it ( | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C11 | P4B2 | NIT | "two empty subclasses" hold docstrings; reword. | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-cor-C12 | P4B2 | NIT | `tests/contracts/test_llm.py:76-106` is really 73-107; other ranges not re-checked. | OPEN | reviews/P4b2-round1-correctness.md | f2349e3 |
| BL-core-p4b2-r1-adv-A1 | P4B2 | BLOCKER | One reservation covers up to 3 `with_retry` attempts; unknown failures (408/5xx/timeout) are possibly billed. (a) unknown then success: settle uses on | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A2 | P4B2 | BLOCKER | Release rule "4xx except 408" is a deny-list, not positive proof (rule 1): 499 (client closed), 424 (Bedrock ModelError), 409, 418 released. Fix: allo | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A3 | P4B2 | MAJOR | Nested ProviderError passes through `except ProviderError: raise` and the outer attempts' counts are discarded (outer timeout then inner all-refused r | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A4 | P4B2 | MAJOR | Release rests on Python attribute convention; AST guard stops only static assignments (`setattr`, `vars(e).update`, `__dict__`, `object.__setattr__` b | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A5 | P4B2 | MAJOR | Motivating case is an outage, but black-holed connects end as ConnectTimeout/TimeoutError and are kept; only refused/DNS/certificate released. State t | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A6 | P4B2 | MAJOR | Maintenance grant omits `expired_at` (P4d sweep claim sets it; trigger requires `closed_at`/`expired_at`): real sweep fails 42501. Add it, match the c | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A7 | P4B2 | MAJOR | By the ticket's own analysis expiry moves no money (counters keep worst case) so the maintenance role protects a label while a leaked runtime credenti | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A8 | P4B2 | MAJOR | P4d (lines 118, 137) says the sweep needs no separate role and the maintenance identity is reserved for P4b2's pruning (DELETE); P4b2 inverts it (no D | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A9 | P4B2 | MAJOR | Trigger discriminator "role without INSERT": any other non-owner non-insert role with UPDATE (future audit-reader/portal) counts as maintenance and ca | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A10 | P4B2 | MAJOR | Every Postgres deployment that runs `tick` without `maintenance_dsn_secret_name` fails tick (exit 1) every cycle after upgrade; `platform_secrets.chec | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A11 | P4B2 | MAJOR | Default config warns on every start (call bound 376 > max_hold 300); two "age" meanings (P4b1 `Hold.age_s()` monotonic vs DB-clock sweep). Derive `orp | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A12 | P4B2 | MAJOR | K1b (item 6, K1-K2, mutant a19, hot file `k1b/loop.py`): K1b replay has its own Budget and does not use the meter; a P5c hot file in a money PR. Under | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A13 | P4B2 | MAJOR | P4b2-a spans 5 llm files, wrapper, 2 new test files, contract-suite edit, 19 mutants, new logger; low reviewability, and A1 adds the success-path coun | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A14 | P4B2 | NIT | Migration number plausible (0006 only if P4d-b/P2a-1a merge later); state failure mode if `_scan` rejects the ALTER, and trigger firing order vs P4d's | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A15 | P4B2 | NIT | `_ROLE` already rejects uppercase (H1 `PUBLIC` is a pin); add `pg_*` and `postgres` as refused maintenance names. | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A16 | P4B2 | NIT | `llm/metered.py` hot-file order P4b1-b, P4c-2, P4b2-a conflicts with "P4b2-a does not depend on P4c" if P4c-2 edits it; state one order. | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A17 | P4B2 | NIT | P4a typed missing-usage refusal not tested: must be kept (no stamps) and not set refused; add G14. Audit event `run_id="-"` precedent `limits.py:35`;  | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p4b2-r1-adv-A18 | P4B2 | NIT | "orphan" already means a stuck run in `tick.py` `stuck`; name the step `expire_spend_reservations` consistently. | OPEN | reviews/P4b2-round1-adversarial.md | f2349e3 |
| BL-core-p5a-r1-cor-C1 | P5A | MAJOR | Shim fail-before cannot run: throwaway ce70eb5 + shim `guard/diagnostic.py` still lacks `hadavin_sdk.codes` (`Code`) and P1 `guard/textnorm.py` (`scan | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C2 | P5A | MAJOR | `leaks()` requires `re.fullmatch` of Grammar A/B, so the shim output and all five leaky subjects fail the GRAMMAR, never the leak: (a) "rows safe_head | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C3 | P5A | MAJOR | Mutant "`RecursionError` not caught -> 100000 brackets" is equivalent: `RecursionError`, `MemoryError` are `Exception` subclasses, and `diagnose` walk | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C4 | P5A | MINOR | `tools/mutation_runner.py`, `testing/mutation.py`, `Mutant(name,file,old,new,expect,...)` listed as "existing core code reused (checked)" but do not e | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C5 | P5A | MINOR | `tool_refused` rationale ("broke its own manifest") is only the `tools.py:67` docstring; `ToolRefused` also raised for timeout (`tools.py:521, 1130`), | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C6 | P5A | MINOR | T10 reason wrong: pytest imports `tests/test_*.py` into `sys.modules` so the frame check holds and `lib_frame` shows the test file; only `locator` is  | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C7 | P5A | MINOR | Stale vs order 7(3): P1c waiting/classes (`MalformedStoredKey, FoldVersionMismatch, SaltMismatch`) still listed; dependency is P1a, P1b, P1m only; re- | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C8 | P5A | MINOR | Killers named in the mutation plan missing from Tests: `test_extra_forbidden_*`, `test_loc_rendering`, `test_every_ledger_id_is_covered`, json_reason  | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C9 | P5A | MINOR | T8 `socket.gaierror` on `.invalid` giving `gai=-2` is not marked UNVERIFIED; no resolver can give EAI_AGAIN (-3). Assert `code=os_error` + in-range ga | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C10 | P5A | MINOR | Tick writers cited `tick.py:292`/`:324`; 292 is the `_message` producer, the writes are 316 (error string), 317 (log), 324 (`last_error`). | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p5a-r1-cor-C11 | P5A | NIT | A4/F6 lists `errors.py` hot for P5a, ticket deviates (cite F6); `ConfigError` OR rule only adds `VaultError`/`UnknownRecording` (`llm/fake.py:47` prin | OPEN | reviews/P5a-round1-correctness.md | def2d2a |
| BL-core-p4a-r1-adv-F1 | P4A | BLOCKER | P4a-1 creates the UsageMissing zero-booking window (fail-open); must merge after P4b1-a or stay estimate-capable | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F2 | P4A | MAJOR | implausible_zero rule: cache-read-only prompt; move into cost_usd; P4b2 mapping keeps reservation | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F3 | P4A | MAJOR | SDK getattr fix incomplete (output_tokens missing); reachable hostile forms per kind not shown | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F4 | P4A | MAJOR | Gemini totalTokenCount cross-check unverified; cut to v1.1 | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F5 | P4A | MAJOR | openai_compat two requests per chat(): reservation sized for one; worst_case needs request multiple | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F6 | P4A | MAJOR | worst_case_usd uses a guessed token estimate, not a bound; rename or byte-derived bound; C7 tautology | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F7 | P4A | MAJOR | price_checks: duplicated human record, startup outage after 30 days; cut | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F8 | P4A | MAJOR | P4a-3 (tier, geo multiplier, PriceTable refactor) has no found defect; cut per order 7 | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F9 | P4A | MAJOR | Tier basis after the call: direction of error unstated; cache-excluded reading | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F10 | P4A | MAJOR | Under-count paths asserted safe: Bedrock cache write, unknown nested cache_creation key | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F11 | P4A | MAJOR | Mutants a1-3, a1-14, a2-18 unkillable/equivalent; U10 re-point | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F12 | P4A | MAJOR | U6 lower-bound assertion; demo pipeline.py hand-edit | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F13 | P4A | MAJOR | Reply/Usage validators vs recordings in evals/k1b/demos: greps not stated | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F14 | P4A | MINOR | probe 1 output not saved under evidence/ | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F15 | P4A | MINOR | fail-before ImportError claim is intent, not evidence | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F16 | P4A | MINOR | decimal.Inexact is not a ProviderError | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F17 | P4A | MINOR | unknown service_tier value read as standard (fail-open) | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p4a-r1-adv-F20 | P4A | NIT | one word two meanings: worst case | OPEN | reviews/P4a-round1-adversarial.md | bd061b3 |
| BL-core-p2d-r1-adv-F1 | P2D | MAJOR | fail-before tree lacks P1a defaults.py hunk: collection errors | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F2 | P2D | MAJOR | N2 literals mutant unkillable; import-time binding | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F3 | P2D | MAJOR | surface with no defect: constants move, WARDEN strip, THREAD-1, SEAM-1/2/4, ERR-1 | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F4 | P2D | MAJOR | tag/unassigned hidden keys stay in clear; xfail + proposed P2d-2 has no owner/date | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F5 | P2D | MAJOR | restore pins wrong spelling jose@exemple.fr; store original slice or guard | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F6 | P2D | MAJOR | P1b dependency override unproven; xfail keyed on a P1b name | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F7 | P2D | MAJOR | fail-before 'assertion' claim unsupported for R/H/U rows; module-level imports | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F8 | P2D | MAJOR | scan 4-17x slower; 1.5x already refuses; availability regression | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F9 | P2D | MINOR | N8 self-contradictory; N3 duplicate | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F10 | P2D | MINOR | ALIGN-1 in unit suite; HOSTILE-1 no time assertion | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F11 | P2D | MINOR | redact() direct call gets N x budget | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F12 | P2D | MINOR | evidence step 0 must be a blocking gate | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F13 | P2D | MINOR | P5c coupling unchecked | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p2d-r1-adv-F14 | P2D | NIT | ERR-1 asserts CPython semantics | OPEN | reviews/P2d-round1-adversarial.md | c34fe24 |
| BL-core-p4a-r1-cor-F1 | P4A | MAJOR | test_p5_llm.py:260 breaks by design (Gemini total mismatch); C2 row same trap | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F2 | P4A | MAJOR | Usage validator ValueError not mapped to UsageMissing('invalid'); escapes agent_loop / settles at zero | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F3 | P4A | MAJOR | C2/C7 fail-before fixtures raise ValidationError on ce70eb5 (extra=forbid) | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F4 | P4A | MINOR | 24 recorded files not 48 | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F5 | P4A | MINOR | grep evidence cannot be empty (comment) | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F6 | P4A | MINOR | a1-3 second half equivalent | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F7 | P4A | MINOR | checked_count cap boundary 10**9 untested | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F8 | P4A | MINOR | a2-18 unkillable | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F9 | P4A | MINOR | Gemini missing total + missing candidates undefined | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F10 | P4A | MINOR | openai_compat: raise before the second request | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F11 | P4A | MINOR | interim window has no date/merge-order guard | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F12 | P4A | MINOR | hot-file order omissions vs P5b1/P4b2 | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F13 | P4A | MINOR | 'after round 5 escalates' conflicts with no round cap | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F14 | P4A | NIT | C8 expected results for bool/empty/float | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F15 | P4A | NIT | pilot_cfg tests need price_checks; grep configs | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p4a-r1-cor-F16 | P4A | NIT | rollback departure from template unstated | OPEN | reviews/P4a-round1-correctness.md | bd061b3 |
| BL-core-p5b1-r1-cor-C1 | P5B1 | MAJOR | P5a diagnose does not read retry_count / error_type fallback: golden rows 10,17, R13 unbacked | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C2 | P5B1 | MAJOR | P4b2 undeclared hot files (protocol, retry, common, bedrock); order; two counters; detail references | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C3 | P5B1 | MAJOR | fail-closed gaps: transient/_chain/__eq__/retryable hook/Bedrock _code non-dict | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C4 | P5B1 | MAJOR | llm_wire.py harness and fixtures not in CHANGE list; rows 2-17 sources missing | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C5 | P5B1 | MAJOR | hostile rows do not fit P5a Row format; CORPUS_STEP bump; H14 ledger link | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C6 | P5B1 | MAJOR | describe vs P5a class_name_of; two rules for one class | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C7 | P5B1 | MINOR | R7 forbids the ticket's own raise f-string | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C8 | P5B1 | MINOR | M14 survives on OSError kinds; name Claude kind for 777 | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C9 | P5B1 | MINOR | retried HTTPError bodies left open | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C10 | P5B1 | MINOR | R4 tripwire swallowed by safe_facts; __class__ | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C11 | P5B1 | MINOR | stale header; request-id shape owner | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C12 | P5B1 | MINOR | default_facts timeout vs connection ordering | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C13 | P5B1 | MINOR | missing mutants (row 28, bounds, close) | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p5b1-r1-cor-C14 | P5B1 | NIT | wording/cite fixes; delete kind_hint | OPEN | reviews/P5b1-round1-correctness.md | 30fd0e8 |
| BL-core-p2d-r1-cor-C1 | P2D | MAJOR | N2 unkillable: import-time constants; literals equivalent | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C2 | P2D | MAJOR | FOLD_NOTE exact text not pinned; N6 survives | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C3 | P2D | MAJOR | SEAM-2/ERR-1/SEAM-4 patch the wrong name; cache keys not exposed | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C4 | P2D | MAJOR | P1b dependency / xfail holes / MAP-1 need a lead decision; P2a/P4d order | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C5 | P2D | MINOR | mutant rows 5,7,12,20 stale snippets | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C6 | P2D | MINOR | test 29 does not prove the 4,096-char check | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C7 | P2D | MINOR | no mutants for runmap thread_time edits | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C8 | P2D | MINOR | FOLD_NOTE imports break collection on ce70eb5 | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C9 | P2D | MINOR | test labels A/U wrong; test 27 explanation | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C10 | P2D | MINOR | probes ran code; figures UNVERIFIED | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C11 | P2D | MINOR | P1a rev 5 size rule dependency missing from Depends-on | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C12 | P2D | MINOR | P2a defaults.py/CHANGELOG order | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C13 | P2D | NIT | redact keyword-only signature | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C14 | P2D | NIT | 43 lines not 45 | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2d-r1-cor-C15 | P2D | NIT | guarantee sentence third case | OPEN | reviews/P2d-round1-correctness.md | c34fe24 |
| BL-core-p2a-r4-adv-A1 | P2A | MAJOR | guard function reads public.* tables; fails in non-public schema; build names from current_schema() | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A2 | P2A | MAJOR | breakglass alarm only sees CLI resets; direct psql reset writes no audit row; reconcile kill_switch_resets | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A3 | P2A | MAJOR | limits stop probes first: stop can be delayed/aborted; stop first, probe after | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A4 | P2A | MINOR | mutants G2/G3 equivalent after migrate() re-issue | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A5 | P2A | MINOR | reset done but audit outcome failed: no exit code | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A6 | P2A | MINOR | re-seed version below gate _durable_version | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A7 | P2A | MINOR | trigger does not set NEW.by on ON to OFF | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A8 | P2A | MINOR | guard_dry_run 42501 check vacuous (lost UPDATE / placeholder) | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A9 | P2A | MINOR | set_config needs str(ms) | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A10 | P2A | MINOR | hand-applied guard file leaves deny-all until migrate | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A11 | P2A | NIT | stop returns RETURNING | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-adv-A12 | P2A | NIT | probe dead tuples | OPEN | reviews/P2a-round4-adversarial.md | 1b533fd |
| BL-core-p2a-r4-cor-C1 | P2A | MAJOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C3 | P2A | MAJOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C4 | P2A | MAJOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C5 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C6 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C7 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C8 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C9 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C10 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C11 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C12 | P2A | MINOR | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C13 | P2A | NIT | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p2a-r4-cor-C14 | P2A | NIT | see report | OPEN | reviews/P2a-round4-correctness.md | 1b533fd |
| BL-core-p1-r4-adv-R4-A1 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A2 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A3 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A4 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A5 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A6 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-A7 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B1 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B2 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B3 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B4 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B5 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B6 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B7 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B8 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B9 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B10 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B11 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-B12 | P1 | MINOR | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-N1 | P1 | NIT | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-N2 | P1 | NIT | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p1-r4-adv-R4-N3 | P1 | NIT | see report | OPEN | reviews/P1-round4-adversarial.md | b13ff07 |
| BL-core-p4d-r5-adv-F1 | P4D | MAJOR | b15 unkillable by B4(vii): FK KEY SHARE | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F2 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F3 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F4 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F5 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F6 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F7 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F8 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F9 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-adv-F10 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-adversarial.md | 7e63580 |
| BL-core-p4d-r5-cor-C1 | P4D | MAJOR | i10 half-up not killed by pinned input | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C2 | P4D | MAJOR | row (d) is a value fail-before; i11 unrelated | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C3 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C4 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C5 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C6 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C7 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C8 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C9 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C10 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C11 | P4D | MINOR | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p4d-r5-cor-C12 | P4D | NIT | see report | OPEN | reviews/P4d-round5-correctness.md | edc7c27 |
| BL-core-p1-r4-cor-C1 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C2 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C3 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C4 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C5 | P1 | MAJOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C6 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C7 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C8 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C9 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C10 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C11 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C12 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C13 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C14 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C15 | P1 | MINOR | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C16 | P1 | NIT | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p1-r4-cor-C17 | P1 | NIT | see report | OPEN | reviews/P1-round4-correctness.md | b13ff07 |
| BL-core-p4a-r2-cor-R2-C1 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C2 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C3 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C4 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C5 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C6 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C7 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C8 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C9 | P4A | NIT | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C10 | P4A | NIT | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-cor-R2-C11 | P4A | NIT | see report | OPEN | reviews/P4a-round2-correctness.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-1 | P4A | BLOCKER | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-2 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-3 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-4 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-5 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-6 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-7 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-8 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-9 | P4A | MAJOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-10 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-11 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-12 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-13 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p4a-r2-adv-R2-14 | P4A | MINOR | see report | OPEN | reviews/P4a-round2-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-1 | P3a | BLOCKER | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-2 | P3a | MAJOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-3 | P3a | MAJOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-4 | P3a | MAJOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-5 | P3a | MAJOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-6 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-7 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-8 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-9 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-adv-R5-10 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-adversarial.md | 60fedf6 |
| BL-core-p3a-r5-cor-R5-C1 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-correctness.md | 60fedf6 |
| BL-core-p3a-r5-cor-R5-C2 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-correctness.md | 60fedf6 |
| BL-core-p3a-r5-cor-R5-C3 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-correctness.md | 60fedf6 |
| BL-core-p3a-r5-cor-R5-C4 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-correctness.md | 60fedf6 |
| BL-core-p3a-r5-cor-R5-C5 | P3a | MINOR | see report | OPEN | reviews/P3a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-1 | P2a | BLOCKER | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-2 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-3 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-4 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-5 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-6 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-7 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-8 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-9 | P2a | MAJOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-10 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-11 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-12 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-13 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-14 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-15 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-16 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-adv-R5-17 | P2a | MINOR | see report | OPEN | reviews/P2a-round5-adversarial.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C1 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C3 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C4 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C5 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C6 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C7 | P2A | MAJOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C8 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C9 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C10 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C11 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C12 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C13 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C14 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C15 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C16 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C17 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C18 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C19 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C20 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2a-r5-cor-R5-C21 | P2A | MINOR | see report | OPEN | reviews/P2a-round5-correctness.md | 60fedf6 |
| BL-core-p2d-r2-adv-R2-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-2 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-3 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-4 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-5 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-6 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-7 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-8 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-9 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-adv-R2-10 | P2D | NIT | see report | OPEN | reviews/P2d-round2-adversarial.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C3 | P2D | MAJOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C4 | P2D | MAJOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C5 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C6 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C7 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C8 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C9 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C10 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C11 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p2d-r2-cor-R2-C12 | P2D | MINOR | see report | OPEN | reviews/P2d-round2-correctness.md | d6be4de |
| BL-core-p4d-r6-adv-R6-1 | P4D | MAJOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-2 | P4D | MAJOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-3 | P4D | MAJOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-4 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-5 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-6 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-adv-R6-7 | P4D | NIT | see report | OPEN | reviews/P4d-round6-adversarial.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C1 | P4D | MAJOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C2 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C3 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C4 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C5 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C6 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C7 | P4D | MINOR | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C8 | P4D | NIT | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C9 | P4D | NIT | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4d-r6-cor-R6-C10 | P4D | NIT | see report | OPEN | reviews/P4d-round6-correctness.md | a49b196 |
| BL-core-p4a-r3-adv-R3-1 | P4A | MAJOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-2 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-3 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-6 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p4a-r3-adv-R3-7 | P4A | NIT | see report | OPEN | reviews/P4a-round3-adversarial.md | 72194a2 |
| BL-core-p1-r5-adv-R5-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-2 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-3 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-4 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-5 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-6 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-7 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-8 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-9 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-10 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-11 | P1 | MINOR | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-12 | P1 | NIT | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-13 | P1 | NIT | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-14 | P1 | NIT | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-adv-R5-15 | P1 | NIT | see report | OPEN | reviews/P1-round5-adversarial.md | 11fa7d9 |
| BL-core-p1-r5-cor-C1 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C2 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C3 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C4 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C5 | P1 | MAJOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C6 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C7 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C8 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C9 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C10 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C11 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C12 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C13 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C14 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C15 | P1 | MINOR | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C16 | P1 | NIT | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p1-r5-cor-C17 | P1 | NIT | see report | OPEN | reviews/P1-round5-correctness.md | 11fa7d9 |
| BL-core-p4a-r3-cor-R3-1 | P4A | MAJOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-2 | P4A | MAJOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-3 | P4A | MAJOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-6 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-7 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-8 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-9 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-10 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-11 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-12 | P4A | MINOR | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-13 | P4A | NIT | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p4a-r3-cor-R3-14 | P4A | NIT | see report | OPEN | reviews/P4a-round3-correctness.md | 72194a2 |
| BL-core-p3a-r6-adv-R6-1 | P3A | MAJOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-2 | P3A | MAJOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-3 | P3A | MAJOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-4 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-5 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-6 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-7 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-8 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-adv-R6-9 | P3A | NIT | see report | OPEN | reviews/P3a-round6-adversarial.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-1 | P3A | MAJOR | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-2 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-3 | P3A | MINOR | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-4 | P3A | NIT | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-5 | P3A | NIT | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-6 | P3A | NIT | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p3a-r6-cor-C6-7 | P3A | NIT | see report | OPEN | reviews/P3a-round6-correctness.md | 3c9fe6a |
| BL-core-p2a-r6-adv-R6-1 | P2A | BLOCKER | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-3 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-4 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-5 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-6 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-7 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-8 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-9 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-10 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-11 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-12 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-13 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-14 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-adv-R6-15 | P2A | NIT | see report | OPEN | reviews/P2a-round6-adversarial.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-1 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-3 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-4 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-5 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-6 | P2A | MAJOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-7 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-8 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-9 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-10 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-11 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-12 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-13 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-14 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-15 | P2A | MINOR | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-16 | P2A | NIT | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-17 | P2A | NIT | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-18 | P2A | NIT | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p2a-r6-cor-C6-19 | P2A | NIT | see report | OPEN | reviews/P2a-round6-correctness.md | bd846f2 |
| BL-core-p4a-r4-adv-R4-1 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-2 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-3 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-4 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-5 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-6 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-7 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-8 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-9 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-10 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-11 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-12 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-adv-R4-13 | P4a | NIT | see report | OPEN | reviews/P4a-round4-adversarial.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-1 | P4a | BLOCKER | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-2 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-3 | P4a | MAJOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-4 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-5 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-6 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-7 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-8 | P4a | MINOR | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-9 | P4a | NIT | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4a-r4-cor-C4-10 | P4a | NIT | see report | OPEN | reviews/P4a-round4-correctness.md | 2a93cc7 |
| BL-core-p4d-r7-adv-R7-1 | P4d | MAJOR | see report | OPEN | reviews/P4d-round7-adversarial.md | 8680691 |
| BL-core-p4d-r7-adv-R7-2 | P4d | MAJOR | see report | OPEN | reviews/P4d-round7-adversarial.md | 8680691 |
| BL-core-p4d-r7-adv-R7-3 | P4d | MAJOR | see report | OPEN | reviews/P4d-round7-adversarial.md | 8680691 |
| BL-core-p4d-r7-adv-R7-4 | P4d | MAJOR | see report | OPEN | reviews/P4d-round7-adversarial.md | 8680691 |
| BL-core-p4d-r7-adv-R7-5 | P4d | MAJOR | see report | OPEN | reviews/P4d-round7-adversarial.md | 8680691 |
| BL-core-p2d-r3-adv-ADV-R3-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-3 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-4 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-5 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-6 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-7 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-8 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-9 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-10 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-11 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-12 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-13 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-14 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-adv-ADV-R3-15 | P2D | NIT | see report | OPEN | reviews/P2d-round3-adversarial.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-3 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-4 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-5 | P2D | MAJOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-6 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-7 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-8 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-9 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-10 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-11 | P2D | MINOR | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p2d-r3-cor-COR-R3-12 | P2D | NIT | see report | OPEN | reviews/P2d-round3-correctness.md | 62d3cc8 |
| BL-core-p4d-r7-cor-C7-1 | P4D | MINOR | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-2 | P4D | MINOR | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-3 | P4D | NIT | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-4 | P4D | MINOR | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-5 | P4D | NIT | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-6 | P4D | MINOR | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p4d-r7-cor-C7-7 | P4D | MINOR | see report | OPEN | reviews/P4d-round7-correctness.md | 8680691 |
| BL-core-p3a-r7-adv-ADV-R7-1 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-2 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-3 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-4 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-5 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-6 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-7 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-8 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-9 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-10 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-11 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-12 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-13 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-14 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-adv-ADV-R7-15 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-adversarial.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-1 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-2 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-3 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-4 | P3A | MAJOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-5 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-6 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-7 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-8 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-9 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-10 | P3A | MINOR | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-11 | P3A | NIT | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p3a-r7-cor-COR-R7-12 | P3A | NIT | see report | OPEN | reviews/P3a-round7-correctness.md | dc3d6e5 |
| BL-core-p1-r6-adv-ADV-R6-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-2 | P1 | MAJOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-3 | P1 | MAJOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-4 | P1 | MAJOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-5 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-6 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-7 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-8 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-9 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-10 | P1 | MINOR | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-11 | P1 | NIT | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-adv-ADV-R6-12 | P1 | NIT | see report | OPEN | reviews/P1-round6-adversarial.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-2 | P1 | MINOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-3 | P1 | MINOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-4 | P1 | MINOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-5 | P1 | MINOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-6 | P1 | MINOR | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-7 | P1 | NIT | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p1-r6-cor-COR-R6-8 | P1 | NIT | see report | OPEN | reviews/P1-round6-correctness.md | 99828b6 |
| BL-core-p2a-r7-adv-ADV-R7-1 | P2A | MAJOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-3 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-4 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-5 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-6 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-7 | P2A | NIT | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-8 | P2A | NIT | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p2a-r7-adv-ADV-R7-9 | P2A | NIT | see report | OPEN | reviews/P2a-round7-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-1 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-2 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-3 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-6 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-7 | P4A | NIT | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-8 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-9 | P4A | NIT | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-adv-ADV-R5-10 | P4A | NIT | see report | OPEN | reviews/P4a-round5-adversarial.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-1 | P4A | MAJOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-2 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-3 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-6 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-7 | P4A | MINOR | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-8 | P4A | NIT | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-9 | P4A | NIT | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-10 | P4A | NIT | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p4a-r5-cor-COR-R5-11 | P4A | NIT | see report | OPEN | reviews/P4a-round5-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-1 | P2A | MAJOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-2 | P2A | MAJOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-3 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-4 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-5 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-6 | P2A | MINOR | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-7 | P2A | NIT | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2a-r7-cor-COR-R7-8 | P2A | NIT | see report | OPEN | reviews/P2a-round7-correctness.md | 3b40ae6 |
| BL-core-p2d-r4-adv-ADV-R4-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-3 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-4 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-5 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-6 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-7 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-8 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-9 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-10 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-11 | P2D | NIT | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-adv-ADV-R4-12 | P2D | NIT | see report | OPEN | reviews/P2d-round4-adversarial.md | 74a12aa |
| BL-core-p2d-r4-cor-COR-R4-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-correctness.md | 74a12aa |
| BL-core-p2d-r4-cor-COR-R4-2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round4-correctness.md | 74a12aa |
| BL-core-p2d-r4-cor-COR-R4-3 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-correctness.md | 74a12aa |
| BL-core-p2d-r4-cor-COR-R4-4 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-correctness.md | 74a12aa |
| BL-core-p2d-r4-cor-COR-R4-5 | P2D | MINOR | see report | OPEN | reviews/P2d-round4-correctness.md | 74a12aa |
| BL-core-p4a-r6-adv-ADV-R6-1 | P4A | MAJOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-2 | P4A | MAJOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-3 | P4A | MAJOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-6 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-7 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-8 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-9 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-10 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-11 | P4A | NIT | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-12 | P4A | NIT | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p4a-r6-adv-ADV-R6-13 | P4A | NIT | see report | OPEN | reviews/P4a-round6-adversarial.md | 900c825 |
| BL-core-p2d-r5-adv-ADV-R5-1 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-2 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-3 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-4 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-5 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-6 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-7 | P2D | MAJOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-8 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-9 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-10 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-11 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-12 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-13 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-14 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-15 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-16 | P2D | MINOR | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p2d-r5-adv-ADV-R5-17 | P2D | NIT | see report | OPEN | reviews/P2d-round5-adversarial.md | d2cceb5 |
| BL-core-p4a-r6-cor-COR-R6-1 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-2 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-3 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-4 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-5 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-8 | P4A | MINOR | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-6 | P4A | NIT | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-p4a-r6-cor-COR-R6-7 | P4A | NIT | see report | OPEN | reviews/P4a-round6-correctness.md | 900c825 |
| BL-core-LK-r1-adv-ADV-LK-1 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-adversarial.md | 6772704 |
| BL-core-LK-r1-adv-ADV-LK-2 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-adversarial.md | 6772704 |
| BL-core-LK-r1-adv-ADV-LK-3 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-adversarial.md | 6772704 |
| BL-core-LK-r1-adv-ADV-LK-4 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-adversarial.md | 6772704 |
| BL-core-LK-r1-cor-COR-LK-1 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-correctness.md | 6772704 |
| BL-core-LK-r1-cor-COR-LK-2 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-correctness.md | 6772704 |
| BL-core-LK-r1-cor-COR-LK-3 | LK | MAJOR | see report | OPEN | reviews/lookalike-round1-correctness.md | 6772704 |
| BL-core-P1-r7-adv-ADV-R7-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P1-r7-adv-ADV-R7-2 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P1-r7-adv-ADV-R7-3 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P1-r7-adv-ADV-R7-4 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P1-r7-adv-ADV-R7-5 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P1-r7-adv-ADV-R7-6 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-adversarial.md | 8d56284 |
| BL-core-P3a-r8-adv-ADV-R8-1 | P3a | MAJOR | see report | OPEN | reviews/P3a-round8-adversarial.md | ee96dbc |
| BL-core-P3a-r8-adv-ADV-R8-2 | P3a | MAJOR | see report | OPEN | reviews/P3a-round8-adversarial.md | ee96dbc |
| BL-core-P3a-r8-adv-ADV-R8-3 | P3a | MAJOR | see report | OPEN | reviews/P3a-round8-adversarial.md | ee96dbc |
| BL-core-P3a-r8-adv-ADV-R8-4 | P3a | MAJOR | see report | OPEN | reviews/P3a-round8-adversarial.md | ee96dbc |
| BL-core-P1-r7-cor-COR-R7-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round7-correctness.md | 8d56284 |
| BL-core-LK-r2-adv-ADV-LK2-1 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-adversarial.md | e2f811e |
| BL-core-LK-r2-adv-ADV-LK2-2 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-adversarial.md | e2f811e |
| BL-core-LK-r2-adv-ADV-LK2-3 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-adversarial.md | e2f811e |
| BL-core-LK-r2-adv-ADV-LK2-4 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-adversarial.md | e2f811e |
| BL-core-LK-r2-cor-COR-LK2-1 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-correctness.md | e2f811e |
| BL-core-LK-r2-cor-COR-LK2-2 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-correctness.md | e2f811e |
| BL-core-LK-r2-cor-COR-LK2-3 | LK | MAJOR | see report; decided in reviews/lookalike-round2-resolve.md, applied in draft 3 | OPEN | reviews/lookalike-round2-correctness.md | e2f811e |
| BL-core-LK-r2-res-RES-LK2-A | LK/P5c | MAJOR | PHONE does not mask a 10-16 digit number before a sentence-final full stop (probe); row ACC-1c to P5c | OPEN | reviews/lookalike-round2-resolve.md | e2f811e |
| BL-core-P1-r8-cor-COR-R8-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-correctness.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-1 | LK | BLOCKER | see report | FIXED-UNVERIFIED | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-2 | LK | BLOCKER | see report | FIXED-UNVERIFIED | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-3 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-4 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-5 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-6 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-adv-ADV-LK3-7 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-adversarial.md | 74a6e26 |
| BL-core-LK-r3-cor-COR-LK3-1 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-correctness.md | 74a6e26 |
| BL-core-LK-r3-cor-COR-LK3-2 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-correctness.md | 74a6e26 |
| BL-core-LK-r3-cor-COR-LK3-3 | LK | MAJOR | see report | OPEN | reviews/lookalike-round3-correctness.md | 74a6e26 |
| BL-core-P1-r8-adv-ADV-R8-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-adversarial.md | 74a6e26 |
| BL-core-P1-r8-adv-ADV-R8-2 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-adversarial.md | 74a6e26 |
| BL-core-P1-r8-adv-ADV-R8-3 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-adversarial.md | 74a6e26 |
| BL-core-P1-r8-adv-ADV-R8-4 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-adversarial.md | 74a6e26 |
| BL-core-P1-r8-adv-ADV-R8-5 | P1 | MAJOR | see report | OPEN | reviews/P1-round8-adversarial.md | 74a6e26 |
| BL-core-lookalike-r4-cor-COR-LK4-1 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-correctness.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-1 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-2 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-3 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-4 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-5 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-7 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-8 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-9 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-10 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-11 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-lookalike-r4-adv-ADV-LK4-12 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round4-adversarial.md | bdab309 |
| BL-core-P1-r9-adv-ADV-R9-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-adversarial.md | 82b477e |
| BL-core-P1-r9-adv-ADV-R9-2 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-adversarial.md | 82b477e |
| BL-core-P1-r9-adv-ADV-R9-3 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-adversarial.md | 82b477e |
| BL-core-P1-r9-adv-ADV-R9-4 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-adversarial.md | 82b477e |
| BL-core-P1-r9-adv-ADV-R9-5 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-adversarial.md | 82b477e |
| BL-core-P1-r9-cor-COR-R9-1 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-correctness.md | 82b477e |
| BL-core-P1-r9-cor-COR-R9-2 | P1 | MAJOR | see report | OPEN | reviews/P1-round9-correctness.md | 82b477e |
| BL-core-lookalike-r5-cor-COR-LK5-1 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-correctness.md | 2af179b |
| BL-core-lookalike-r5-cor-COR-LK5-2 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-correctness.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-1 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-2 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-3 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-4 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-5 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r5-adv-ADV-LK5-6 | lookalike | MAJOR | see report | FIXED-UNVERIFIED | reviews/lookalike-round5-adversarial.md | 2af179b |
| BL-core-lookalike-r6-adv-ADV-LK6-1 | lookalike | BLOCKER | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-adv-ADV-LK6-2 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-adv-ADV-LK6-3 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-adv-ADV-LK6-4 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-adv-ADV-LK6-5 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-adv-ADV-LK6-6 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-adversarial.md | 1677d72 |
| BL-core-lookalike-r6-cor-COR-LK6-1 | lookalike | BLOCKER | see report | OPEN | reviews/lookalike-round6-correctness.md | 1677d72 |
| BL-core-lookalike-r6-cor-COR-LK6-2 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-correctness.md | 1677d72 |
| BL-core-lookalike-r6-cor-COR-LK6-3 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-correctness.md | 1677d72 |
| BL-core-lookalike-r6-cor-COR-LK6-4 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-correctness.md | 1677d72 |
| BL-core-lookalike-r6-cor-COR-LK6-5 | lookalike | MAJOR | see report | OPEN | reviews/lookalike-round6-correctness.md | 1677d72 |
