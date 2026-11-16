# P5b2 round 3 resolve (egm:egm-resolve, AUTO mode)

- **Status:** resolved (AUTO mode; the interactive gate was skipped as the lead ordered, order 7(1)). I did NOT edit the ticket, commit, push or write DECISIONS.md. **Round 4 is NOT allowed:** round 3 has 0 Blocker but 5 distinct Majors (7 Major ids after merging duplicates), more than the "at most 2 Majors" of order 20 item 6. So P5b2 is FROZEN at revision 3, and every decision below goes into a new ticket section **"Build notes (build-start review, order 20)"** (text in section "Build notes" below). The lead decides PENDING LEAD 13 to 15 (section "PENDING LEAD").
- **Honest note (read first):**
  - **The checkouts differ, and the reviewers read a different commit from the ticket.** The ticket cites `origin/main` = `397ec97`. My working tree is the handover branch (`ef6eee6`), and `origin/main` has since moved to **`4ec3616`** (PR #60, "CI: scan tracked files for secrets and banned names"). The reviewers read the handover checkout. There, `pyproject.toml` has two extra lines (`extend-exclude`, `:70`), so every pyproject cite moves by +2. `ci.yml` there is an older file, without the "Stale gitleaks ignore entries" step, and `.gitleaks.toml` there has one allowlist. I checked with `git show 397ec97:<file>`: the ticket's cites (`pyproject.toml:69, :76, :84`, `ci.yml:79, :81, :119, :164-170, :176-182`, two allowlists) hold exactly on `397ec97`. So the line-number findings R3-ADV-15 and R3-COR-4 are contested, but `4ec3616` changes three facts that the build must use (row RES-2).
  - **What I ran:** read-only `git show`, `git archive 397ec97 src` into a scratch folder, and two small `python3 -I` syntax-tree scripts over that export on Python **3.13.18 only**. I also ran `ruff==0.17.1` (through `uvx`) and `bandit` on two throwaway runner skeletons in the scratch folder. I ran no repository code, no repository test and no pytest. The 3.12 figures are still UNVERIFIED.
  - **What the scripts showed on `397ec97`:**
    - site classes `ConfigError`, `BundleError`, `StoreUnavailable`, each with only a docstring and one base (`ValueError`, `ConfigError`, `ConfigError`);
    - **171 constructions in 37 files**, first argument **42 literal / 114 f-string / 15 other**, so the ticket's 171, 42, 114 and 15 are now verified on 3.13;
    - **0** constructions with a second positional, keyword or starred argument;
    - the only factory is `k1b/bundle.py::_fail`;
    - **32 raiser helpers** (functions that raise a site construction interpolating their own parameter), with **81 plain-name calls** and **0 calls that pass a handler-bound exception name directly** (taint through locals NOT checked);
    - no symlinks, and no non-ASCII class or function names;
    - no function both raises and returns a site construction.
  - **NOT checked:**
    - the 17 exception-variable sites (I took the reviewers' line checks);
    - how many rows the wider taint locks;
    - the shapes on 3.12;
    - the merged P5a layout;
    - the P1m runner;
    - P3a's exact `MigrationNumberError` code (it is not built; I read only `tickets/P3a.md:30`).
  - **One defect neither reviewer found** (RES-1, which I rate Major): P3a is frozen and merges before P5b2. Its `MigrationNumberError(ConfigError)` carries a field `problems` and builds its own message (`tickets/P3a.md:30`), so it almost certainly defines `__init__`. P5b2's rule "a site class that defines `__init__` ... raises `SitesError`" (ticket `:65`) would then stop the generator at the merge base, and the CI test could never pass. The ticket's own known-changes table (`:260`) saw this risk but left it UNVERIFIED.
  - Some Majors are partly the author's own earlier choices (the "AssertionError" verdict rule came from my round-2 decision on R2-ADV-7). I fix them, not defend them.
- **Target:** `handover/tickets/P5b2.md`, revision 3, full file (273 lines).
- **Findings:**
  - `handover/reviews/P5b2-round3-adversarial.md`: R3-ADV-1 to 17, with 0 Blocker, 4 Major, 10 Minor and 3 Nit.
  - `handover/reviews/P5b2-round3-correctness.md`: R3-COR-1 to 16, with 0 Blocker, 3 Major, 8 Minor and 5 Nit. Its header says "7 Minors", but its table has 8 (COR-4 to COR-11).
  - Together: 33 ids, 8 duplicate pairs merged, 25 rows, plus 2 rows I found (RES-1, RES-2).
- **Gate:** one decision per row, including the Minors and Nits.
  - Order 8(1) asks me to cut surface. Five rows are closed by narrowing or deleting:
    - COR-2: the runner runs one file per mutant, so 31 node ids are not needed;
    - ADV-5: any symlink is refused;
    - ADV-10: an import allowlist replaces a ban list;
    - ADV-8: the class-body rule becomes "docstring only", plus one `__init__` form;
    - COR-12: a clause is deleted.
  - ESCALATE: none.
  - CONTEST: one row (ADV-15/COR-4), plus one part-contest (ADV-11).
- **Facts I checked myself** (read-only; each is in a file the reviewers could read):
  1. `397ec97:pyproject.toml`: `:50` `ruff==0.17.1`, `:69` `src = [...]`, `:76` `ban-relative-imports`, `:84` `pythonpath`. On the handover checkout these lines are `:71`, `:78` and `:86`, which matches what the reviewers saw.
  2. `397ec97:.github/workflows/ci.yml`: `:79`, `:81` ruff `src tests demos`; `:119` bandit; `:126` "Stale gitleaks ignore entries"; `:164` gitleaks; `:176` Trivy. `397ec97:.gitleaks.toml` has two `[[allowlists]]` (`:12`, `:28`).
  3. `4ec3616` (`origin/main` now) has no `src/` change from `397ec97` (empty `git diff 397ec97 4ec3616 -- src`). It adds:
     - `tools/scan_repo.py`, `tools/scan_allowlist.txt` and `tools/scan_banned_extra.txt`, with **no `tools/__init__.py`**;
     - in CI, `ruff check` and `ruff format --check` of `src tests demos tools/scan_repo.py` (`:79`, `:81`);
     - a new step "Secrets and banned names in the tracked files" (`:82-83`, `python tools/scan_repo.py`; it reads `git ls-files`, so it covers `tests/data/config_error_sites.csv`).
     - It also moves lines: bandit is `:121`, gitleaks `:166` and Trivy `:178`.
  4. `tools.py` `parse_manifest` is `:102-124` on `397ec97`, `4ec3616` and the handover checkout. Its raises are at `:107, :113, :120, :123`, and `fields` is at `:119`. The ticket's `tools.py:100-120` (`:63`, `:236`) holds only three of the four raises, so COR-8 is right.
  5. `397ec97:tests/test_no_hardcoded_values.py:22`: `PATTERNS` is a dict from rule name to compiled regex (`key`, `long-secret-shape`, `account-id`, `arn`, `url`, `host`). `reason_problems` exists nowhere in `tests/`.
  6. `397ec97:tests/` holds 67 `# noqa` comments, for example `tests/test_k5_classes.py:489` (`# noqa: S603`). I ran `ruff==0.17.1 --select S` on a runner skeleton:
     - `subprocess.run(argv)` with a built argument list gives **S603**;
     - a literal list gives **S607**;
     - a skeleton that starts `pytest.main` in a `multiprocessing.get_context("spawn")` process gives **no S finding** and no bandit finding. The only hit is PLC0415, which the repo does not select (`extend-select = B, DTZ, I, S, TID, UP`).
  7. `plan-v3.md:106` marks P5b2 Tier A, and order 6(b) lists it as Tier B. COR-10 is right that the ticket names neither.
  8. `design-v3.md:16` defines T1 as "operator configuration values (secret names, **paths**, bucket names, config keys)". `:53` defines OPERATOR as "interpolates T1 values: config keys, paths, secret names, bucket names". This bears on R3-ADV-11.
  9. `tickets/P3a.md:30` (revision 10, frozen) contains:
     - "`class MigrationNumberError(ConfigError)`, field `problems: tuple[str, ...]`";
     - "Message of the subclass: `"migrations are inconsistent: "` + problems joined by `"; "`, capped".

| id(s) | category | decision (exact text is in "Build notes") |
|---|---|---|
| R3-ADV-1 (Major), R3-COR-1 (Major) | PROPOSE FIX | `load_csv` accepts an empty `class` and returns `""`; every other word outside `CLASSES` raises. Add a unit (7) case "write twice with blank rows present: no error, bytes identical". Add a hostile case "one blank `class` lands only in `blank_class`; class `" LITERAL"` (leading space) raises". New mutant **M24e** (`load_csv` refuses an empty `class`), killed by that unit (7) case. M10 is now reachable. **BN-1.** |
| R3-ADV-2 (Major), R3-COR-3 (Major) | PROPOSE FIX | Delete "with an `AssertionError`". The verdict comes from pytest's exit code plus the junit file, never from an exception type. KILLED = exit 1 and at least one `<failure>`; this includes `DID NOT RAISE` and a `SitesError` raised in a test body. CRASH = exit 2-5, or exit 1 with only `<error>`, or the mutated file fails a parse/import pre-check. SURVIVED = exit 0. SKIPPED = a `<skipped>` element. **BN-2.** |
| R3-COR-2 (Major) | PROPOSE FIX (CUT) | Do not add 31 node ids. Per mutant, the runner runs the **whole file** `tests/test_config_error_sites.py` once (the file is small, and this is the same rule as BN-2). "Killed by" becomes "expected killer". The evidence lists the failed test ids per mutant and flags a row whose expected killer is not among them; such a row still counts as KILLED, because a killed mutant is the proof. F1 and M12's killer are named: `tests/test_config_error_sites.py::test_planted_unclassified_site_is_refused`. **BN-2.** |
| R3-ADV-3 (Major) | PROPOSE FIX (option for the lead) | The hole is real in principle: a raiser helper's callers give no rows, so a later `_bad(str(exc))` passes CI. It is empty today: I found 0 direct handler-name calls among the 81 plain-name calls of the 32 raisers on `397ec97` (taint through locals UNVERIFIED). Recommended rule **C5**: a resolvable call of a raiser whose argument bound to an interpolated parameter is tainted becomes a locked FOREIGN row. Untainted calls give no row, so 0 rows are expected today. Method calls and non-exception foreign values (document text) stay a stated limit, pinned by a strict xfail. New mutant **M30**. Options and recommendation: **PENDING LEAD 13. BN-3.** |
| R3-ADV-4 (Major) | PROPOSE FIX | `auto_class=LITERAL` only for at most one positional argument, no keyword and no starred argument, and that argument constant or absent. Every other shape is FOREIGN, with taint over ALL arguments. Today 0 constructions have another shape (my scan), so no row changes. Unit (1b) gets four shape cases. New mutant **M29** (only the first argument is read). **BN-4.** |
| R3-ADV-5 (Minor) | PROPOSE FIX (CUT) | **Any** symlink (file or folder) under `package_dir` raises `SitesError`. This is simpler than resolving targets, and there are none today (my scan). The hostile symlink case expects `SitesError`. **BN-5.** |
| R3-ADV-6 (Minor), R3-COR-6 (Minor) | PROPOSE FIX | `reason_problems(rows, patterns) -> list[str]` is a NEW function in `tests/test_config_error_sites.py`. `patterns` is the `PATTERNS` dict (fact 5). Note that its `host` rule means a reason must not name a host. **BN-6.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | The taint sources gain the calls `sys.exc_info()`, `sys.exception()`, `traceback.format_exc()`, `traceback.format_exception(...)` and `traceback.format_exception_only(...)`, wherever they appear. An inner `def`, a `lambda` or a closure is its own function: taint does not cross into it, so such a row lands in `unproven-origin` (human). One parametrized unit (3) case. No new mutant; listed in "Not covered by a mutant". **BN-7.** |
| R3-ADV-8 (Minor) | PROPOSE FIX (CUT) | Replace the five-dunder list with a body rule. A site class may hold only a docstring, `pass`, class annotations and non-dunder assignments, plus (PENDING LEAD 14) one `__init__` of a fixed shape. It may have no decorator, no class keyword, and exactly one base that is a site class (`ConfigError` itself: exactly `ValueError`). Otherwise `SitesError`. This closes `__str__ = helper`, mixins and `with_traceback` overrides. Add one line saying that non-`ConfigError` exceptions are out of scope, and why. M26 is redefined. **BN-8.** |
| R3-ADV-9 (Minor), R3-COR-13 (Nit) | PROPOSE FIX (part DECLINE) | (a) New mutant **M19b** (direction 2 of `wrong_literal`), killed by unit (9) direction-2 case. (b) Unit (9) also asserts `report.ok is False` per case and `True` on the clean case. List precedence is already covered by the two overlap cases, so it gets no new row. (c) The cheap refusals (missing CSV, `.csv` suffix, relative `--csv`, exit codes, no `*.py`, no `ConfigError`, invalid UTF-8, factory through factory) go into a new line "Not covered by a mutant; covered by the named unit or hostile case". (d) **DECLINE** splitting M8c. A taint gap can only move a row to human review, never pass it (ticket `:54`), so per-form mutants buy little; M8c is stated as group-level. A LITERAL class on a locked row still fails through `wrong_literal`, so it needs no row (COR-13). **BN-9.** |
| R3-ADV-10 (Minor) | PROPOSE FIX (CUT) | Replace the stdlib check with an **import allowlist**: `__future__, argparse, ast, csv, dataclasses, hashlib, pathlib, re, sys, typing`. Also: no `__import__`, `exec`, `eval` or builtin `compile`; no attribute call on `os` or `subprocess` (neither may be imported anyway); no write to `sys.path`. Adding a module is a ticket change that the built-code review sees. M17 is unchanged (`importlib` is not allowed). **BN-10.** |
| R3-ADV-11 (Minor) | PROPOSE FIX (part CONTEST) | **Contest** the definition point: T1 and OPERATOR include "paths" (`design-v3.md:16`, `:53`), and a bundle case folder is a path the operator hands to the replay. **Fix** the reasons: the `_fail` reason names the check that runs before the use (`rel` against the fixed layout at `bundle.py:207-211`; `key` against `ALERT_KEYS` at `:227`). `:190` (`case` = `path.name` that FAILED `CASE_RE`) gets its own row note: "operator-supplied folder name; control characters are not escaped here, which is P5b3's concern". **BN-11.** |
| R3-ADV-12 (Minor), R3-COR-10 (Minor) | PROPOSE FIX | Rewrite the path-class line: ticket rounds are capped by order 20 item 6, which overrides plan-v3's Tier A (`plan-v3.md:106`) and order 6(b)'s Tier B for ticket rounds; built-code depth is PENDING LEAD 1. **BN-12.** |
| R3-ADV-13 (Minor) | PROPOSE FIX | F1 lives in `tests/test_config_error_sites.py` (named in BN-2). For the P5a-dependent shapes (rows 005 and 033, the appended hostile test): "if the merged P5a shape differs from the ticket, the builder follows the merged file and records the difference in the build notes and the evidence". **BN-13.** |
| R3-ADV-14 (Minor) | PROPOSE FIX | PENDING LEAD 6 gets a defined outcome at 31 or more FOREIGN. The builder still decides every row, opens the draft pull request marked `STOP: FOREIGN=<n>`, and lists the rows; the lead decides; P5b3 plans for up to `<n>` rewrites. No pre-agreed widening. **BN-14.** |
| R3-ADV-15 (Nit), R3-COR-4 (Minor) | CONTEST (part PROPOSE FIX) | **Contest:** every disputed cite holds on the commit the ticket names, `397ec97` (facts 1-2). The reviewers read the handover checkout `ef6eee6`. **Fix:** `origin/main` is now `4ec3616` (fact 3), so the build notes record the moved lines, and the builder re-reads every cite at the merge base (the ticket already says the builder's count wins). **BN-15**, with RES-2. |
| R3-ADV-16 (Nit), R3-COR-16 (Nit) | PROPOSE FIX | `symbol` is the dotted chain of enclosing `ClassDef`, `FunctionDef` and `AsyncFunctionDef` names only. A lambda, decorator, default argument or comprehension adds no part, and the nearest enclosing def or class is used, else `<module>`. A non-ASCII name in that chain raises `SitesError`. There are none today (my scan). **BN-16.** |
| R3-ADV-17 (Nit), R3-COR-11 (Minor) | PROPOSE FIX | One resolver for factory (C4) and raiser (C5) calls. It matches a plain name defined in the same module, a name imported by `from M import F [as A]`, and `M.F` where `M` is an import of the defining module. It does not match `self.F` or `obj.F` (stated limit), and an unrelated `_fail` in another module is not matched. A factory that assigns and then returns (`e = Cls(...); return e`) raises `SitesError`. A function that both raises and returns is a factory, and its raises are ordinary rows; there are none today. **BN-17.** |
| R3-COR-5 (Minor) | PROPOSE FIX | Delete "112" (`:10`, `:239`). 114 + 15 = 129 and 129 - 18 = 111 (verified on 3.13). **BN-18.** |
| R3-COR-7 (Minor) | PROPOSE FIX | PENDING LEAD 6 wording: "158 start with `auto_class=FOREIGN`, of which at least 18 are locked and at most 140 are `unproven-origin`". **BN-14.** |
| R3-COR-8 (Minor) | PROPOSE FIX | Cite `tools.py:102-124` (raises `:107, :113, :120, :123`) at `:63` and `:236`, and `tools.py:119-120` at `:38`. The reviewer's own range holds on all three commits (fact 4). **BN-18.** |
| R3-COR-9 (Minor) | PROPOSE FIX | The runner starts each mutant run with `multiprocessing.get_context("spawn")` and `pytest.main(...)`, so it does not use `subprocess`. This passes ruff 0.17.1 S rules and bandit (fact 6), so no `# noqa` is needed. Reword the absolute claim: "the new code holds no `# noqa`; the repository CLAUDE.md forbids new suppressions; 67 older ones exist in `tests/`". If P1m's runner already solves this, use P1m's. **BN-2.** |
| R3-COR-12 (Nit) | PROPOSE FIX (CUT) | Delete "every row whose `class` differs from the automatic class" at `:48`. It never fires on its own. **BN-18.** |
| R3-COR-14 (Nit) | PROPOSE FIX | `:30` "its mutant M9" becomes "P5b3's mutant M9 (not P5b2's M9)". **BN-18.** |
| R3-COR-15 (Nit) | PROPOSE FIX | `:129` "reads with universal newlines" becomes "opens the file with `newline=""`; the `csv` module accepts CRLF rows". **BN-18.** |
| RES-1 (found by this resolve; I rate it Major) | PROPOSE FIX (option for the lead) | P3a's `MigrationNumberError` (fact 9) would trip the fail-closed `__init__` rule at the merge base. Recommended: allow exactly one `__init__` shape, whose text reaches the base only through one `super().__init__(<expr>)`. That call is its own site row (`symbol` = `<Class>.__init__`, classified like any construction; P3a's `problems` join of file names is a human OPERATOR or FOREIGN decision). New mutant **M31**. **PENDING LEAD 14. BN-8.** |
| RES-2 (found by this resolve; Minor) | PROPOSE FIX | `4ec3616` facts (fact 3): (i) `tools/` exists on main without `__init__.py`; P5b2 still waits for P1m's `tools/__init__.py` (`:23`), because a namespace `tools` can be shadowed by an installed regular package named `tools`. (ii) CI already lints a single file under `tools/` (`tools/scan_repo.py`), so PENDING LEAD 3's ask becomes "add `tools/gen_config_error_sites.py`, or `tools`, to `:79`, `:81` and bandit `:121`". (iii) `scan_repo.py` scans every tracked file, so it is a fourth layer over the `reason` column (secrets and banned names). It does not cover URLs or account ids, so the reason test stays. **BN-15.** |

## Build notes (build-start review, order 20): exact text to append to the ticket

This is the replacement text for the new section **"Build notes (build-start review, order 20)"**, placed after "Revision 3: what changed". It is appended without a new revision, because the ticket is FROZEN at revision 3. The build-start review (order 19 A, order 20 item 3, order 21 item 17: two fresh reviewers and one resolve) reads revision 3 plus this section. **Where a build note and the revision-3 text disagree, the build note wins.** BN-3 and the `__init__` part of BN-8 hold the recommended option until the lead answers PENDING LEAD 13 and 14.

- **BN-1 (R3-ADV-1, R3-COR-1). Replaces the `load_csv` bullet (`:67`):**
  - "`load_csv(path: Path) -> list[Row]` (`Row` = `site`, `class`, `reason`). An empty `class` is accepted and returned as `""`: it is how `write()` marks a site a person must decide, and `compare` reports it as `blank_class`.
  - It raises `SitesError` on:
    - a wrong header (any header other than `COLUMNS`, including an extra or an old column);
    - a non-empty `class` not in `CLASSES` (for example `literal`, `SAFE`, `" LITERAL"`);
    - a duplicate `site`;
    - a non-ASCII byte;
    - a `reason` over `REASON_MAX` or with a newline.
  - A missing file raises `SitesError` (a missing file is not "no rows")."
  - **Added tests:**
    - Unit (7): "with blank-class rows present, `write`, then `write` again: no `SitesError`, identical bytes, the blank rows stay blank".
    - Hostile: "a CSV with one blank `class` loads and lands only in `blank_class`"; "class `" LITERAL"` raises".
  - **New mutant M24e:** `load_csv` refuses an empty `class`. Expected killer: the unit (7) write-twice case.
- **BN-2 (R3-ADV-2, R3-COR-2, R3-COR-3, R3-COR-9, R3-ADV-13). Replaces the "runner's tree" command sentence and the "Verdicts" bullet (`:133`, `:135`):**
  - **How each mutant runs:**
    - "Per mutant, the runner first checks that the mutated `tools/gen_config_error_sites.py` passes `ast.parse` and imports in a fresh interpreter; otherwise the row is CRASH.
    - It then runs the whole file `tests/test_config_error_sites.py` once, in a fresh interpreter started with `multiprocessing.get_context("spawn")`. That interpreter changes to `<tmp>`, puts `<tmp>` first on `sys.path`, and calls `pytest.main(["-p", "no:cacheprovider", "--rootdir", <tmp>, "-q", "--junitxml", <tmp>/result.xml, "tests/test_config_error_sites.py"])`.
    - There is no `subprocess`, so ruff's S603 does not apply and the file needs no `# noqa`. The repository CLAUDE.md forbids new suppressions; 67 older ones exist in `tests/`. If P1m's runner already does this, use P1m's."
  - **Verdicts** (from the exit code and `result.xml` only, never from an exception type):
    - KILLED = exit code 1 and at least one `<failure>` element. A failed assert, `Failed: DID NOT RAISE` and any exception raised in a test body all count.
    - CRASH = exit code 2, 3, 4 or 5; or exit code 1 with only `<error>` elements (setup, teardown or collection); or a failed pre-check.
    - SURVIVED = exit code 0.
    - SKIPPED = any `<skipped>` element.
  - **Baseline:** the unmutated tree runs with 0 failures, 0 errors and 0 skips, else exit 2.
  - **Exit 0** only when every row is KILLED.
  - **The "Killed by" column** becomes "expected killer". The evidence lists the failed test ids per mutant and flags any row whose expected killer is not among them (such a row is still KILLED).
  - **F1 and M12's expected killer** is `tests/test_config_error_sites.py::test_planted_unclassified_site_is_refused`.
- **BN-3 (R3-ADV-3; PENDING LEAD 13, option (a) recommended). New scan rule (e) after (d):**
  - "**(e) Calls of raiser helpers (rule C5).** A raiser is a function whose body raises a site construction that interpolates one of its own parameters (32 on `397ec97`, for example `tools.py::parse_manifest` and `backends/platform_secrets.py::resolve`).
  - Each call of a raiser that the resolver of rule C4 can resolve (BN-17) is checked. If an argument bound to an interpolated parameter is tainted (`exception-variable` under the taint rules), the call becomes its own row: `kind` = the class raised, `auto_class=FOREIGN`, `auto_reason=exception-variable`, so it is locked. An untainted call gives no row.
  - On `397ec97`, no call passes a handler-bound name directly (round-3 resolve scan; taint through locals UNVERIFIED), so 0 rows are expected.
  - `--review` lists, for every raiser's own construction row, its resolvable callers.
  - **Limit** (in the docstring and in 'What the scan does not detect'): a raiser called as a method, and a non-exception foreign value (document or model text) passed into a raiser, give no row. A pinned `xfail(strict=True)` test, `test_raiser_called_with_document_text_is_not_detected`, shows this."
  - Unit (12) keeps its case "an untainted raiser call gives no row" and adds: "a raiser called with `str(exc)` inside a handler gives one locked row".
  - **New mutant M30:** C5 ignored. Expected killer: that unit (12) case.
  - M28 is unchanged.
- **BN-4 (R3-ADV-4). Replaces the `auto_class` bullet (`:52`):**
  - "`auto_class`: `LITERAL` only when the call has no keyword argument, no starred argument (`*a`, `**k`) and at most one positional argument, and that argument is absent, a string constant, an implicit concatenation of string constants, or an f-string with no `{}` part. Any other shape is `FOREIGN`, because `str()` of an exception built with two or more arguments prints the whole tuple.
  - For every `FOREIGN` row, the taint test of `auto_reason` runs over ALL arguments (positional, keyword and starred), not only the first.
  - On `397ec97`, no construction has a second, keyword or starred argument (round-3 resolve scan), so no row changes."
  - **New unit (1b):** `ConfigError("x", exc)`, `ConfigError("x", detail=v)`, `ConfigError(*parts)` and `ConfigError(**kw)` are FOREIGN. The first, inside `except ... as exc`, is `exception-variable`.
  - **New mutant M29:** `auto_class` reads only the first argument. Expected killer: unit (1b).
- **BN-5 (R3-ADV-5).** In `scan` (`:59`), "no symlink followed outside the tree" becomes: "any symlink (file or folder) under `package_dir` raises `SitesError`". The hostile symlink case expects `SitesError`.
- **BN-6 (R3-ADV-6, R3-COR-6).** `:79` reads: "asserts that `reason_problems(rows: list[Row], patterns: dict[str, re.Pattern[str]]) -> list[str]`, a NEW function in `tests/test_config_error_sites.py`, finds nothing in the real CSV. `patterns` is the dict `PATTERNS` imported from `tests.test_no_hardcoded_values` (`:22`; rules key, long-secret-shape, account-id, arn, url and host), so a `reason` must not name a host either."
- **BN-7 (R3-ADV-7).** Append to the taint bullet (`:54`):
  - "The calls `sys.exc_info()`, `sys.exception()`, `traceback.format_exc()`, `traceback.format_exception(...)` and `traceback.format_exception_only(...)` are tainted expressions wherever they appear.
  - An inner `def`, a `lambda` or a closure is its own function: taint does not cross into it, so a site there that reads a handler name lands in `unproven-origin` and needs a person."
  - Unit (3) gains one parametrized case over the five calls.
- **BN-8 (R3-ADV-8, RES-1; the `__init__` part is PENDING LEAD 14, option (a) recommended).** Replaces the last fail-closed item of `:65` ("a site class that defines `__init__` ..."):
  - "A site class body may hold only a docstring, `pass`, class-level annotations and assignments to names that are not dunder names, plus at most one `__init__` of this shape: its body calls the base initialiser exactly once, as `super().__init__(<expr>)`, and otherwise only assigns attributes of `self`.
  - That `super().__init__(...)` call is a site row of its own: `symbol` = `<Class>.__init__`, hashed with `node_hash`, classified like any construction, with the taint and shape rules run over the `__init__` body.
  - The following raise `SitesError`:
    - any other `def`;
    - a second call to the base initialiser;
    - an assignment to a dunder name (for example `__str__ = helper`);
    - a decorator;
    - a class keyword (for example `metaclass=`);
    - a base list other than exactly one site class (for `ConfigError` itself: exactly `ValueError`).
  - On `397ec97`, all three site classes hold only a docstring and have one base."
  - Add to Problem: "Only `ConfigError` and its subclasses are in scope. Other exception types that reach the operator (for example a `ValueError` inside a pydantic validator) reach the screen through an existing site such as `config.py:120`, which is locked FOREIGN."
  - The hostile list gains one case per refusal, plus a class shaped like P3a's `MigrationNumberError` (one `__init__` with `self.problems = ...` and one `super().__init__(...)`), which gives one row.
  - M26 is redefined: "the body rule removed". Expected killer: the hostile `__str__ = helper` case.
  - **New mutant M31:** "the `super().__init__` call is not a row". Expected killer: the P3a-shaped hostile case.
  - Remove the sentence "a new subclass must not define `__str__` and the like" from the known-changes row P3a (`:260`) and replace it with "P3a's `MigrationNumberError` is accepted under BN-8 and gives one row for its `super().__init__` call".
- **BN-9 (R3-ADV-9, R3-COR-13).**
  - **New mutant M19b:** "`class` other than `LITERAL` accepted on a `LITERAL` row". Expected killer: `compare` (9), `wrong_literal` direction 2.
  - Unit (9) also asserts `report.ok is False` in every planted case, and `report.ok is True` on the clean case.
  - New line after the table: "**Not covered by a mutant; covered by the named unit or hostile case:**
    - missing CSV is not 'no rows';
    - `--csv` must end in `.csv`;
    - relative `--csv` resolves against `--root`;
    - CLI exit codes;
    - no `*.py`;
    - no `ConfigError` class found;
    - invalid UTF-8;
    - factory called through a factory;
    - the taint sources of BN-7.

    M8c disables all its forms in one edit and proves only that the group has teeth; per-form mutants are not built, because a taint gap moves a row to human review and never lets it pass."
- **BN-10 (R3-ADV-10).** `test_generator_imports_standard_library_only` (`:80`) becomes:
  - "parses the generator's file and asserts that every imported top-level module is in the allowlist `__future__, argparse, ast, csv, dataclasses, hashlib, pathlib, re, sys, typing`;
  - that there is no call to `__import__`, `exec`, `eval` or the builtin `compile`;
  - and that nothing assigns to, or calls a method of, `sys.path`.
  - Adding a module to the allowlist is a ticket change that the built-code review sees."
  - M17 is unchanged.
- **BN-11 (R3-ADV-11).** In the `_fail` judgement case (`:213`):
  - The shared reason names the checks that run before use: "bundle case folder and file names given by the operator; `rel` is checked against the fixed layout (`bundle.py:207-211`) and `key` against `ALERT_KEYS` (`:227`) before use; no caller passes exception text".
  - `bundle.py:190` gets its own reason: "operator-supplied folder name that failed `CASE_RE`; control characters are not escaped here (P5b3)".
  - The builder re-reads each of the 29 calls.
- **BN-12 (R3-ADV-12, R3-COR-10).** `:16` "Extended review (no round cap): **no**, because order 20 item 6 replaced it for tickets" becomes:
  - "Extended review (no round cap): for TICKET rounds, no. Order 20 item 6 caps them at 3, plus one more for a redaction package under its condition (not met in round 3: 5 Majors). This overrides plan-v3's Tier A (`plan-v3.md:106`) and order 6(b)'s Tier B for ticket rounds.
  - For the BUILT code, the depth is PENDING LEAD 1 (recommended (b): two clean rounds in a row, the no-cap rule the repository CLAUDE.md sets for redaction paths)."
- **BN-13 (R3-ADV-13).** In Files (`:91-95`) add: "If the merged P5a shape of rows 005 and 033, or of the appended hostile test, differs from this ticket, the builder follows the merged file and records the difference in these build notes and in the evidence."
- **BN-14 (R3-ADV-14, R3-COR-7).** PENDING LEAD 6 reads:
  - "It applies to the reviewed table. On ce70eb5, 158 rows start with `auto_class=FOREIGN` (129 non-literal constructions plus 29 factory calls); at least 18 of them are locked, and at most 140 are `unproven-origin`.
  - If the reviewed table has 31 or more `FOREIGN` rows, the builder still decides every row, opens the draft pull request titled with `STOP: FOREIGN=<n>`, and lists every FOREIGN row by site. The lead decides. P5b3 plans for up to `<n>` rewrites. There is no pre-agreed widening of the limit."
- **BN-15 (R3-ADV-15, R3-COR-4, RES-2).** Add to "Verified" and to the known-changes table:
  - "`origin/main` moved to `4ec3616` (PR #60) after revision 3. It changes nothing under `src/` (empty diff from `397ec97`).
    - It adds `tools/scan_repo.py`, `tools/scan_allowlist.txt` and `tools/scan_banned_extra.txt`, but no `tools/__init__.py`, so P5b2 still waits for P1m's `tools/__init__.py`.
    - CI now lints `tools/scan_repo.py` (`ci.yml:79`, `:81`), so PENDING LEAD 3 becomes 'add `tools/gen_config_error_sites.py` (or `tools`) to `:79`, `:81` and bandit `:121`'.
    - A new CI step (`:82-83`) scans every tracked file, so also the CSV, for secrets and banned names: a fourth layer over `reason`. It does not cover URLs or account ids, so `test_reasons_hold_no_key_url_or_account_id` stays.
    - New line numbers on `4ec3616`: bandit `:121`, gitleaks `:166`, Trivy `:178`.
  - The handover checkout's `pyproject.toml` is two lines longer than main's (`extend-exclude`), which explains the reviewers' +2.
  - The builder re-reads every cite at the merge base."
- **BN-16 (R3-ADV-16, R3-COR-16).** Add to the `site` column (`:46`):
  - "`symbol` is the dotted chain of the enclosing `ClassDef`, `FunctionDef` and `AsyncFunctionDef` names only. A lambda, a decorator, a default argument and a comprehension add no part; the nearest enclosing def or class is used, else `<module>`.
  - A non-ASCII name in that chain raises `SitesError`."
  - A hostile case is added.
- **BN-17 (R3-ADV-17, R3-COR-11).** Replaces "Each call of a factory, in any file" (`:63`):
  - "A call of a factory (and, under BN-3, of a raiser) is resolved only in these forms:
    - a plain name `F` used in the module that defines `F`;
    - a name brought in by `from M import F` or `from M import F as A`, where `M` defines `F`;
    - `X.F`, where `X` names an import of the module that defines `F`.
  - `self.F(...)` and `obj.F(...)` are not resolved (a stated limit). A function of the same name in another module is a different function.
  - A function that assigns a site construction to a name and then returns that name raises `SitesError` ('return the construction directly').
  - A function that both returns and raises a site construction is a factory, and its raises are ordinary rows (none today)."
  - Unit (12) gets one case for each resolved form and one for the same name in another module.
- **BN-18 (R3-COR-5, R3-COR-8, R3-COR-12, R3-COR-14, R3-COR-15). Small text fixes:**
  - delete "112" at `:10` and `:239`;
  - `tools.py:100-120` becomes `tools.py:102-124 (raises at :107, :113, :120, :123)` at `:63` and `:236`;
  - `tools.py:118-120` becomes `tools.py:119-120` at `:38`;
  - delete "every row whose `class` differs from the automatic class," at `:48`;
  - `:30` "its mutant M9" becomes "P5b3's mutant M9 (P5b2's own M9 is a different mutant)";
  - `:129` "the loader reads with universal newlines" becomes "the loader opens the file with `newline=""`; the `csv` module accepts CRLF rows".
- **Mutant count after the build notes:**
  - 31 + 3 unconditional (M19b, M24e, M29) = **34**;
  - plus M30 if PENDING LEAD 13 is (a), and M31 if PENDING LEAD 14 is (a): **36** with both recommendations;
  - M26 is redefined;
  - M20, M22 and M25 stay retired.

## Positions
- **Why freeze instead of round 4.** Order 20 item 6 allows a round 4 only for round 3 with no Blocker and at most 2 Majors. There are 5 distinct Majors, and I did not lower any severity. Freezing costs little: every Major now has exact replacement text, and the build-start review (two fresh reviewers) reads those notes before any code. A round 4 would re-review the same text.
- **Where I cut instead of adding (order 8(1)):**
  - COR-2: run the whole file, not 31 node ids;
  - ADV-5: refuse every symlink;
  - ADV-8: a body rule instead of a dunder list;
  - ADV-10: an allowlist instead of a growing ban list;
  - COR-12: delete a clause;
  - the ADV-9(d) split is declined.
- **Where I added surface, and why it is needed** (all on the redaction path, each one rule with one mutant):
  - ADV-4: shape rule, which narrows LITERAL;
  - ADV-3: C5, which adds rows only for tainted calls, 0 expected today;
  - ADV-7: five taint-source call names;
  - RES-1: one `__init__` form, without which the generator cannot run once P3a merges.
- **Contested:**
  - ADV-15/COR-4 line numbers: they hold on the named commit `397ec97` (`git show`).
  - ADV-11's definition point: T1 includes "paths" (`design-v3.md:16`).
  - Both are checkable in files the reviewers could read.
- **Not contested, though I considered it:** ADV-3 and ADV-4 describe holes that are empty today (my scan). That is not a reason to keep them: the table is a gate for future code.

## Couplings (relay to the named tickets)
1. **P3a (frozen, revision 10):** under PENDING LEAD 14 (a), `MigrationNumberError` must use a plain `__init__` with exactly one `super().__init__(<message>)` and no decorator, no `__str__` and no second base. A `@dataclass` would fail closed. Under option (b), P3a's builder builds the message at each raise and gives the class no `__init__`. Either way, this is a P3a build note.
2. **P5b3:** its D11 taint guard reuses `tainted_names`, so it inherits the BN-7 sources and the BN-4 "all arguments" rule. A raiser called with a tainted argument (BN-3) is also a P5b3 guard case. P5b3 should say whether its guard checks raiser calls, or relies on P5b2's C5. "P5b3's M9" is the class-name rule (BN-18).
3. **P1m:** `tools/__init__.py` is still P1m's file (`4ec3616` has `tools/` without it). If P1m's mutant runner already uses a spawn or in-process runner, P5b2 reuses it (BN-2).
4. **Lead (CI):** PENDING LEAD 3 now has a precedent on main: `tools/scan_repo.py` is listed file by file at `ci.yml:79`, `:81`.

## PENDING LEAD (continuing the ticket's 1-12)
- **13 (new, R3-ADV-3). Raiser-helper calls.**
  - Option (a): rule C5 (BN-3). Tainted resolvable calls become locked FOREIGN rows; 0 rows expected today; method calls and document text are a stated limit with a strict xfail; one mutant (M30).
  - Option (b): state the limit only (docstring, Source line, strict xfail), with no new rule.
  - Option (c): every resolvable raiser call is a row (81 or more plain-name calls on `397ec97`, each a human decision, which raises the FOREIGN > 30 risk).
  - **Recommended: (a).** It closes the exception-text case at the cost of one rule and no new human rows.
  - Reversible (a rule in a tool, no runtime change).
- **14 (new, RES-1). P3a's `MigrationNumberError`.**
  - Option (a): allow one `__init__` shape and make its `super().__init__(...)` call a row (BN-8, mutant M31).
  - Option (b): keep the fail-closed rule and ask P3a's builder to build the message at each raise, with no `__init__`.
  - **Recommended: (a).** P3a is frozen. The class's message joins file names, which need a classified row anyway. And (b) would move message building to every raise.
  - Reversible.
- **15 (new). Confirm the freeze.**
  - Option (a): P5b2 FROZEN at revision 3, with the build-notes section above appended verbatim. The build-start review (two fresh reviewers, one resolve) reads both.
  - Option (b): grant a round 4 against order 20 item 6.
  - **Recommended: (a).** Every Major has exact text. A round 4 would re-review it on paper, and the build-start review sees it anyway.
- **Updates to open items:**
  - **1** is still open (recommended (b)), and BN-12 states it in the path-class line.
  - **3** has its ask narrowed by BN-15.
  - **6** has its wording and STOP procedure set by BN-14.

## Counts
- Ids:
  - 33 (17 ADV, 16 COR);
  - 8 duplicate pairs merged, giving 25 rows;
  - plus 2 rows found by this resolve (RES-1, RES-2), giving **27 rows**.
- Decisions:
  - **PROPOSE FIX 26 rows.** 5 of them are cuts: COR-2, ADV-5, ADV-8, ADV-10, COR-12. 2 hold an option for the lead: ADV-3, RES-1. 1 is part-contest (ADV-11) and 1 is part-decline (ADV-9(d)).
  - **CONTEST 1 row** (ADV-15/COR-4, with a part fix for `4ec3616`).
  - **ESCALATE 0.**
  - **DECLINE 0 whole rows.**
- Severities as filed:
  - 0 Blocker;
  - Major: 4 ADV and 3 COR ids, which are 5 distinct Majors;
  - plus RES-1, which I rate Major.
- Build notes: BN-1 to BN-18.
- Mutants:
  - 31 now, 34 unconditional after the build notes, 36 with PENDING LEAD 13 (a) and 14 (a);
  - M26 is redefined.
- PENDING LEAD:
  - 13, 14 and 15 are new;
  - 1, 3 and 6 are updated;
  - 2, 4, 5, 7, 8, 10, 11 and 12 are unchanged;
  - 9 stays closed.
- Round state: round 3 of 3 is done. Round 4 is not allowed (5 distinct Majors, more than 2). FROZEN at revision 3 plus build notes, pending PENDING LEAD 15.
