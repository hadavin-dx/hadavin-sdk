<!-- full hand-back report of sub-agent a55fde8a, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW round 2, Q8c-1, head a77fab72 (snapshot /home/user/build/snap/q8c1-a77fab7/). Read-only, static reading only. Nothing was run by me.

VERDICT: NOT CLEAN, with a small residue. 0 Blocker, 1 Major, 9 Minor. Every round-1 Major is closed in the code. The one new Major is about labelling and evidence for the new `+` grant. No "cannot fail" test and no mutant-runner tree problem found. Ruff check, ruff format, bandit, scan_repo, `policy_page.py --check` and gitleaks are shown passing at this head (evidence 03-gates-output.txt). The a77fab7 RESULTS.md has not arrived, so I could not confirm the test runs, the mutant run or the engine tests.

## Round 1 closure (checked in code)
- Design M1 (refusal stated as fact): CLOSED as wording. The page and CHANGELOG say "have not run yet"; `ENGINE_RUN` is None (policy_page.py:45); test_policy_docs.py:14-23 pins it. The server tests themselves have still never run anywhere (see the end).
- Design M2 (R17 star form too wide): CLOSED. `{mount}/data/{path_prefix}+` (secrets_vault.py:237). `binding_problems` (test_policy_guard.py:615-644) ties the resource to the request path. The old star form has a guard plant (:2292) and an engine plant (test_policy_engine.py:286). `_fetch` rejecting `a/b`, `..` and an empty name is tested at test_policy_guard.py:1850.
- Design M3 (guard misses): CLOSED for the shown plants.
  - Literal `getattr` is refused unless on `getattr_ok` (:474-481).
  - Banned names are read in `ast.alias` (:447-450).
  - `attrgetter`, `partial`, `vars`, `__dict__` and `__import__` are banned.
  - Every import must be on a per-module list.
  - `.authed` taken as a value is refused (:482-487).
  - `_opener` and `open` are limited to the sender function.
  - The Kubernetes call site is checked for path shape and query names (:549-597).
  - Residual holes are in Minor 1 and 2.
- Round-1 Minors:
  - m1 closed.
  - m2 closed: `repr=False`.
  - m3 closed: `Engine.undo` plus `clean_up`.
  - m4 closed: 200/204 only (:189-197).
  - m5 closed as wording (:109-113, 92-day cap); the date-based red is accepted, see Minor 6.
  - m6 closed (policy_page.py:536-543).
  - m7 closed (`_unprintable`).
  - m8 closed (`+` is a wildcard for D1; `_vault_path_problems`).
  - m9 closed (:415-419, :751).
  - m10 closed: `data_problems` runs the cross-kind rules, stray modules and source ids.
  - m11 closed as wording (kubernetes.py:433-439, :464-469).
  - m12 closed; the labelling is partly honest, see the Major.
  - m13 closed: patch, undelete, subkeys, byok-export, rotate, trim and restore were added.
  - m14 closed: CI step at ci.yml:96-97, 41 mutants, and test_policy_docs.py:68 asserts the step.
  - m15 closed.
  - m16 closed: `PENDING_NAMES` entries for the three role names.
- Evidence item (reserved or privileged values): CLOSED (policy_page.py:191-230, :741-742, :727).
- Changed existing tests: none found. The round-1 diff touched no existing test, and line counts of 12 sampled existing test files equal main (EV-Q8c1-fb-main). The CI change adds only one env var and one step; ci_security_golden.json has the same line count as main.

## Findings

**MAJOR 1. The `+` meaning of R17 rests on rows nobody but the fix builder has read, yet R17 is marked verified and gets copy-ready text.**
- Where: secrets_vault.py:245-254 (`verified` lists V-POL, V-ACL, V-PARSE, B-POL, B-ACL), `claims_unverified = ()` at :256, `copy_ready` (policy_page.py:852-857), fixture header lines 8-10 and 16-17.
- Failure: ERRATA E2 defines `verified` as found by the evidence runner. The fixture header itself says the `+` claim, V-ACL, V-PARSE, B-ACL and the paths undelete, subkeys and byok-export were read by the fix builder alone, "nobody else has re-read them yet". The `verified` tuple, the page cell ("2026-11-11, sources ...") and the test at test_policy_guard.py:1279-1284 cannot tell these rows from evidence-runner rows. The page offers a copy-ready Vault policy whose only wildcard is the one claim not independently read, and no server has run. If the claim were wrong (for example `+` also matching a longer path, or being refused), the page would hand out a wrong policy.
- My own knowledge agrees with the claim: `+` is a whole segment, and `+*` is refused by the parser. That is not a source read by me.
- Smallest fix, either of these:
  - (a) Put "`+` matches exactly one path part: read by the fix builder only, no server run" into R17 `claims_unverified`. That removes the copy-ready block for that kind until the evidence runner re-reads V-ACL, V-PARSE and B-ACL, or the CI engine run is recorded in `ENGINE_RUN`.
  - (b) Have the evidence runner re-read those rows and update the header.

**Minor 1. The Kubernetes query-name rule has holes that matter.**
- Where: test_policy_guard.py:600-612 (regex `[?&]([A-Za-z_]\w*)=`), :193-215 of kubernetes.py (`_items`, path and query built at :201), allowlist `("_items", 203, "_get")` at test_policy_guard.py:287.
- The `_items` allowlist asserts only that the operation argument is a parameter of the function. The path and query handed to `_get` at :203 are never read, and `query_name_problems` sees only literal fragments. These pass with no report:
  - `query = f"?limit={limit}&watch"`: no `=`, so no match. To my knowledge, not verified here, Kubernetes treats a bare `watch` as true.
  - `f"&{name}=1"`.
  - `"&" + "watch=true"`.
- Calls with a literal path are caught (`kubernetes_path_problems` flags a missing `=`, :592). Only the wrapper line and constants built from pieces escape.
- Fix: regex `[?&]([A-Za-z_]\w*)(?==|&|$)`, and either have `_items` use one constant query and compare it to `PAGING`, or flag any non-literal part of the query in `_items`.

**Minor 2. Vault: the sender function is a blind spot, and `.call` is not policed outside the declared modules.**
- Where: test_policy_guard.py:241-242 and :497 (`raw_http = {"__init__","call"}`), :1675 (only `.authed` is checked outside declared modules).
- A second HTTP request added inside `VaultProvider.call` is not seen; it is exempt wholesale. `client_user_problems` flags `.authed` but not the public `.call`.
- The remaining route is a module that obtains a provider object without importing the module. That is unlikely, but the page's "refused by listed rules" sentence rests on it.
- Fix: one `Request` or `open` call inside `call`, enforced by count, and an allowlist of `.call` callers.

**Minor 3. Fixture hashes are never tested, and there are small pin inconsistencies.**
- Where: policy_sources_2026-11-11.txt:23-29, :30-33, :39-41; test_policy_guard.py:2169-2186.
- Format is self-consistent: 19 rows, five columns, unique ids, 64-hex digests, and `/blob/{commit}/` in every URL.
- All 16 hashes agree with the evidence runner's source-hashes.txt (my reading of the two files). The 40-character commit expansions of the B-* and K-* rows were expanded by the second builder and are not hash-confirmed by anyone else; the 7-character prefixes match the evidence.
- No test or tool re-hashes anything, so a mistyped hash passes; the header admits this.
- The seven Vault documentation rows are pinned by a 7-character commit, which is a weak pin. The OpenBao documentation rows are at `0d706a0`, but B-ACL is at the v2.4.0 tag, so the OpenBao claims are not tied to one version.
- `len(rows) == 19` (:2171) breaks on any new source row.
- Fix: a CI-side `--verify-sources` or an evidence-runner step; full commit ids; state or pin the OpenBao version.

**Minor 4. No cross-check between a Vault never-path and the Vault grants.**
- Where: policy_page.py:684-691 (`cross_problems`; only `type == action` is compared).
- A grant whose (resource, capability) a never `path` entry would cover is not found. Today there is none, since the data/\* never entry lists create, update, patch and delete and R17 holds read. It stays a one-line gap for PR 2.

**Minor 5. Line-number allowlists are brittle against other work, and the message does not say what to do.**
- Where: test_policy_guard.py:241, 268, 287 (lines 101, 104, 40, 168, 184, 203).
- Any edit above those lines in these three modules, for example the Q8a-1 work in secrets_vault.py, turns the A1 tests red (`stale allowlist entry`, :702-706). The message does not say "move the line in SHAPES".
- Fix: add that hint to the message.

**Minor 6. The suite goes red by date on 2026-12-12 (accepted, carried over).**
- Where: test_policy_guard.py:44-45 and :86-91 (review_by 2026-12-11), TODAY from test_lockin_guard.py.
- Two tests fail for everybody at once: `test_every_kind_is_declared_pending_or_holds_no_identity` and `test_every_grant_name_is_verified_or_pending...`. The message now says what to do. The plants use fixed dates, so they are not affected.

**Minor 7. test_policy_docs.py is brittle.**
- Where: test_policy_docs.py:15, 18, 32.
- `ENGINE_RUN is None` is asserted, so recording the first CI run requires editing the test in the same commit (the comment says so).
- `changelog[...][:4000]` is a slice by position.
- `"least-privilege polic" not in README` fails on any future README mention.
- The file imports `ROOT` and `_policies` from another test module.
- Fix: loosen the README assertion to the one new paragraph; keep the others as they are.

**Minor 8. Mutant "first failing line must hold `expect`" is almost vacuous for `same()` killers.**
- Where: policy_mutants.py (most rows); `same` at test_policy_guard.py:151-154.
- `same` prints the expected text, which already holds the fragment, so a killer that fails for any reason counts as killed.
- Two mutants share the killer test_plant_p09a (:222-232).
- The E5 grammar mutant (:145-152) is killed only by the empty-prefix test, not by a grammar test.
- Not a hole today. Worth knowing before trusting "41 of 41 good".

**Minor 9. A raw non-ASCII character sits in a test literal.**
- Where: test_policy_guard.py:1915, the `" "` entry. It is a non-printing space-like character (presumably U+00A0 or U+2028; I cannot tell which from the view).
- Ruff here does not select the ambiguous-unicode rules, so the gates pass. It is invisible in review. Write it as an escape.

**Minor 10. A default argument freezes the root.**
- Where: policy_page.py:997 (`def page(root: Path = ROOT)`) and :1031 (`target = ROOT / PAGE` read at call time).
- Patching `pp.ROOT` moves the write target but not the page source. The tests work around it by patching `pp.page` itself (test_policy_guard.py:1484, 2147).
- Fix: `root: Path | None = None` and resolve it inside.

## Checked and fine
- **Vault facts against the fixture:**
  - R17 and R18 capabilities are right: GET is read, POST is update. R18 is the exact path without the optional hash part, as the note says.
  - The refusal and control requests of the engine tests, the token-create and revoke parameter names, and the Transit key-create parameters match the Vault API as I know it.
  - `no_default_policy` is checked by asserting that the token holds only the named policy (test_policy_engine.py:146-147).
- **Kubernetes:** list on `apps/deployments` and core `events`, and get on core `pods/log`, are the right verbs and resources for those paths. `_derived` (:976-989) computes them from `READ_OPERATIONS`. The never-list equals `_WRITE_VERBS`, `_SHELL_RESOURCES` and `secrets` (:1006-1012). The `watch` statement matches the code.
- **Renderer:**
  - Values are checked with `fullmatch` plus a `.` and `..` segment check.
  - The empty prefix has its own refusal. Reserved values are refused. Lengths are limited. Duplicate namespaces are refused. An unfilled placeholder is refused.
  - Output strings go through `json.dumps`, and the grammars admit no quote, space or newline.
  - Page mode and values mode behave as E5 says.
- **Mutant tree:**
  - `run_mutants` copies src, the listed test file and the dirs tests, tools and docs (policy_mutants.py:387-392; mutation_runner.py:462-474).
  - test_policy_guard.py reads only src, tests/fixtures, tests/test_policy_engine.py and docs/declared-permissions.md, all of which are copied.
  - The tests that read ci.yml, CHANGELOG.md and README.md were moved to test_policy_docs.py, whose docstring says why. test_policy_engine.py also reads ci.yml but is not in the mutant run.
  - I checked the old strings of all 41 mutants against the head files by reading: each looks unique, at the right indent. The earlier 14 were reported killed (mutant-rows.txt); the later 27 are not evidenced.
- **Timing and ordering:** engine tests use unique names, a 15-minute token and best-effort `clean_up`. No file-order dependence found.

## Not checked
- Whether any test passes at this head: the a77fab7 RESULTS.md is not there. Pytest, the mutants and the engine tests were not run by me.
- The Vault engine tests have never run on a real server. The wording is honest, but the expected statuses (200/204 for the admin controls, 403 for refusals, the policies list at token creation) are the author's reading, not seen results. The first CI run may fail for reasons that cannot be seen statically.
- Vendor source text: I did not open any vendor page or source. The `+` semantics and `+*` refusal are from my own knowledge. The claim about a bare `?watch` is also from my knowledge.
- Whether the 40-character commit ids and the three builder-only hashes are right.
- Whether `docs/declared-permissions.md` equals `page()` byte for byte (read lines 1-80 only).
- `tools.fetch` method binding for Kubernetes: I saw the declaration, not the enforcing code; round 1 said it binds method and path.
- `mutation_runner` internals beyond lines 436-525.

Files: /home/user/build/snap/q8c1-a77fab7/tools/policy_page.py, /home/user/build/snap/q8c1-a77fab7/tests/test_policy_guard.py, /home/user/build/snap/q8c1-a77fab7/tests/test_policy_engine.py, /home/user/build/snap/q8c1-a77fab7/tests/test_policy_docs.py, /home/user/build/snap/q8c1-a77fab7/tests/policy_mutants.py, /home/user/build/snap/q8c1-a77fab7/tests/fixtures/policy_sources_2026-11-11.txt, /home/user/build/snap/q8c1-a77fab7/src/hadavin_sdk/actions/secrets_vault.py, /home/user/build/snap/q8c1-a77fab7/src/hadavin_sdk/audit/signer_vault.py, /home/user/build/snap/q8c1-a77fab7/src/hadavin_sdk/sources/kubernetes.py.
