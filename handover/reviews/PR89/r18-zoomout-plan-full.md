<!-- full hand-back report of sub-agent a30d9a6c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

ZOOM-OUT PLAN REVIEW: D-002 (PR89 round-18 fix approach). Mode: REVIEW. Read-only; nothing was run.

Verdict: do NOT build D-002 as written. Option (b) (a k-gram pass on top of the denylist) is the wrong main fix for M2, and M3 as stated breaks CI. A smaller, more provable plan exists and it is an extension, not a rewrite.

Files read: the persona and zoom-out standard; `/home/user/hadavin-sdk/handover/AUTONOMOUS-DECISIONS.md`; the three r18 reports; `/home/user/build/snap/p89-db0d9eb/tools/mutation_runner.py` (all 1,278 lines); `/home/user/build/snap/p89-db0d9eb/src/hadavin_sdk/testing/mutation.py`; `/home/user/hadavin-sdk/CLAUDE.md` and the three rule files; `/home/user/hadavin-sdk/src/hadavin_sdk/guard/runmap.py` lines 280-559; `/home/user/hadavin-sdk/.github/workflows/ci.yml` lines 30-99. `DIFF.patch` only in part (see the end).

## PROBLEMS

### P1. Major (close to Blocker). M3's database-name marker refuses the CI address, and the plan has no step for it
- Scope: D-002 "For M3: refuse non-loopback host/non-socket and require database-name marker".
- Scenario: `ci.yml` lines 86 and 93 set `HADAVIN_TEST_PG_DSN: postgresql://postgres@localhost:5432/postgres`. The host passes the loopback check. The database name `postgres` carries no marker, so any `run_mutants(pass_env=...)` call with the CI value is refused.
- The marker also checks the wrong thing for this repo's fixture pattern. `/home/user/hadavin-sdk/tests/demo_askdata/conftest.py` (lines 3-5, 44-48) treats the variable as an ADMIN address and creates its own `askdata_t_<8 hex>` databases. The login is a superuser on a trust-auth server, so the blast radius is the whole server whatever the name in the address says.
- Proposed change: the plan must pick one of these and write it down before building.
  - (a) Keep the marker and change the three CI steps in the same PR to a marked database (for example `POSTGRES_DB` on the service). Every other test that reads the variable then uses that database too.
  - (b) Drop the marker and state the residual risk.
  - I recommend (a) only if the CI edit is accepted as in scope; otherwise (b).
- Either way, say in plain words what the check does not prove: loopback is not "throwaway". An SSH tunnel or a cloud database proxy puts a production database on `localhost:5432`.

### P2. Major. The M3 override is a boolean wildcard, and loopback-only breaks container CI
- Scenario: a job that runs inside a container (GitHub `container:`, GitLab services, docker compose, a devcontainer) reaches the database as host `postgres` or `db`, never as loopback. Every such demo must pass `allow_remote_address=True`, which then permits ANY host, production included. The control is off exactly where it matters.
- This contradicts CLAUDE.md "exact actions and resources (no `*`)".
- Proposed change: replace the boolean with an exact allowlist such as `throwaway_hosts=("postgres",)`, compared with the parsed host. The default is the loopback literals (`localhost`, `127.0.0.1`, `::1`) and a socket path. Add a negative test per refusal.

### P3. Major. M3 needs a parser, and the plan does not say which; a second, looser one is new attack surface
- The file already has a strict allowlist grammar, `_address_parts` (lines 456-483). The plan does not mention reusing it.
- That grammar returns `unparsed` for any key=value address with a password word, any URL with a query, and any URL password holding `@`, `/`, `?`, `#` or a space. So M3 must either refuse those values (fail closed, a new refusal for callers) or parse them loosely.
- Loose-parse scenarios the plan must exclude:
  - `host=localhost hostaddr=10.0.0.5`: libpq connects to `hostaddr`.
  - `host=localhost service=prod`: `HOME` is in `CHILD_ENV`, so `~/.pg_service.conf` is read.
  - `postgresql://localhost/db?host=prod.example`: the query overrides the host.
  - Today `_address_parts` accepts unknown keys in key=value form (only four keys are checked, lines 472-480), so the first two pass as "localhost".
- Proposed change: M3 reuses `_address_parts`, extended to return its parts. `unparsed` is refused when `pass_env` is set. Key=value form gets a key allowlist (`host`, `hostaddr`, `port`, `dbname`, `user`, plus named harmless options). Both `host` and `hostaddr` must be allowed hosts. One grammar then serves the lock name, the host check and (see P4) the no-password check.

### P4. Major. A k-gram pass is still a denylist and will not converge; it is the weaker class fix
- Scope: D-002 option (b), "every substring >= 6 chars of any secret, plus its percent-decoded/base64/hex forms".
- `class-level-fixes.md` says "fix at the shared choke point with an allowlist or spec-derived grammar". A list of encodings is open-ended. Round 19 can name HTML entities, a `repr` of bytes with `\x` escapes, JSON `\u` escapes, a percent-encoded slice, reversed text, or a pprint wrap. The existing "Not covered" paragraph (lines 88-93) already admits several.
- The pass also sits on top of the existing head/tail machinery (`_fragment_spans`, KMP tables, three work bounds) without retiring any of it, so two overlapping mechanisms and a 60-line masking docstring remain.
- `_masked` is not where child text enters; it has six call sites. The real entry point is `_row` plus `_refuse_skips_in_baseline`, where JUnit text becomes output.
- Proposed change, in order of size and provability:
  1. Smallest: no secret enters. With the strict grammar from P3, refuse a value whose login holds a `:` or that carries a password key. The CI value has no password and passes unchanged. Credentials come from trust auth on a throwaway container or `~/.pgpass`. Proof: nothing secret is in the child's environment, so nothing can leak. Cost: callers with a password in the address must change, and end-to-end tests that pass a password through `run_mutants` would have to change, which touches "no deleted or weakened tests". This option needs written evidence and likely the owner's yes.
  2. Recommended for this batch: when `secrets` is non-empty, output is a fixed projection, never free text. At `_row`:
     - `first_lines` holds only the leading exception class name (it must match an identifier), a fixed word for whether `expect` matched, and the caller's own `expect` text.
     - The test-id column holds only the file path and function name, with any `[parameter]` part replaced by a fixed word. A parametrised id can carry the address.
     - The existing `_masked` stays, unchanged, as a second layer over the projection. A line `E   hunter2secret` would otherwise show a password as the "class name".
     - `judge` and the `crash_type` check keep reading the raw line internally, as now.
     - Size is roughly 20-30 lines. No existing API or masker test is removed. Fuzz test: for random secrets and random child text, no 4-character slice of a secret appears in any output field outside the caller's `expect`.
  3. The k-gram pass: only if 1 and 2 are both rejected, and then with P5 handled.
- D-002 already holds option 2 as a conditional ("only when pass_env set if tests still pass"). Make it the primary and drop the k-gram pass.
- Cost of option 2, stated honestly: under `pass_env` a WRONG_REASON row no longer shows the actual line; the developer re-runs that one test by hand. Tests that assert the exact masked line on the `pass_env` path need their expected text changed. I counted 4 exact-match assertions on `first_lines` in the diff by pattern; I did not read them.

### P5. Major, if the k-gram pass is kept. Six-character grams shred ordinary output for the CI address
- Scenario: for `postgresql://postgres@localhost:5432/postgres` the grams include `postgr`, `ostgre`, `stgres`, `localh`, `ocalho`, `calhos`, `alhost` and `:5432/`.
  - A test id such as `tests/test_k5_postgres::test_x` becomes `tests/test_k5_[REDACTED]::test_x`. The id column is what evidence and `pinned` baselines are read against.
  - A driver line such as `connection to server at "localhost" (127.0.0.1), port 5432 failed` loses `localhost`.
  - Any line with `postgresql` or `psycopg ... postgres` is cut.
- Short secrets: a password under 6 characters has no gram, so the pass adds nothing for it; that limit is information-theoretic and should be stated as such, not as a gap. Lowering k toward the existing 2-character head/tail rule garbles everything.
- Base64: the base64 of a slice is not a substring of the base64 of the whole unless the slice starts at a multiple of 3, so three alignments are needed and the edge characters mix with neighbours. A naive "every substring" build is quadratic on a 2,000-character value; only the length-6 windows are needed.
- Proposed change, if kept:
  - Apply grams ONLY to password texts, never to the whole value. Host, port, scheme and database name of a throwaway loopback database are not secrets once M3 holds.
  - Never apply grams to the test-id column.
  - Build a set of length-k windows and slide once over the text.
  - Add a test with the literal CI value proving that `postgres`, `localhost` and a `test_k5_postgres` id survive.

### P6. Major. D-002 covers two of the four Majors; M1 and M4 are not in the plan
- r18-design M1: the 155 new mutants and 4 conftest mutants never executed. M4: the full suite was never run after the `judge()` change and the new autouse fixture.
- The plan adds more code to a base that has not been proven. All findings are marked "unverified by lead until reproduced", and D-002 records verification only of the M3 premise.
- Proposed change: add step 0, an EVIDENCE RUNNER on `db0d9eb` (mutants file, full suite, bandit, Postgres tests), before any fix. Fix what it shows, then M2 and M3.

### P7. Major. One batch mixes two security changes with 14 minors, and one minor widens the leak surface
- r18-codebase m4 asks to add a "masked first line" to the failed-baseline `RuntimeError` (line 1206). That is a NEW site where free child text reaches output, added while M2 is trying to close that class.
- Proposed change: under `pass_env` the baseline error carries only `_run_end(base_rc)` and the exception class name, the same projection as P4. Split the batch: (1) evidence, (2) M2 + M3 with their fuzz and negative tests proven to fail on old code, (3) the minors. The sha256 pins change once at the end.

### P8. Minor. No ladder line, and no written answer on reusing the core redactor (r18-design m5)
- `tool-ladder-before-code.md` requires a ladder line in every plan. D-002 has none.
- Answer to put in the plan: `guard.runmap.redact_text` should not be the masker here.
  - It finds secrets by pattern and undoes percent, entity and escape layers. It does not mask arbitrary slices of a known value, nor base64 or hex, so it does not close M2.
  - It raises `RedactionError` and has a 6-second budget.
  - It would couple a byte-copied, stdlib-only tool (docstring line 10: "imports only `hadavin_sdk.testing.mutation`") to the product's largest module, which is itself a mutation target.
  - With the P4 projection the residual text is an identifier and a path, so a second redactor adds nothing.

### P9. Minor. The "loses 2,800 lines of tests" reason against option (a) is overstated
- An output projection added at `_row` deletes no masker test; only assertions on the `pass_env` output shape change. `improve-before-replace.md` is satisfied by P4 option 2, so the rule does not force the k-gram pass.

### P10. Nit. The "Revisit if" trigger is backwards
- It says to fall back to the allowlist if the k-gram pass breaks legitimate text. P5 shows it does so for the CI value on day one, so the fallback is the plan.

### P11. Nit. No consumer of `pass_env` in this snapshot outside the runner's own tests
- The diff touches no demo, and a search of `/home/user/hadavin-sdk/demos` finds no reference to `mutation_runner`. The plan should name the first real caller and its address shape (admin address, as in the ask-your-data fixtures) so M3 is designed for it.

## ANSWERS TO THE FOUR QUESTIONS
1. The k-gram pass is not the right class fix. The allowlisted projection (class name, caller's `expect`, sanitised test id) with the existing masker as a second layer is smaller, safer and provable by construction. Refusing password-bearing addresses outright is smaller still but changes the contract and needs the owner.
2. Keep the existing masker as it is, as the second layer; add nothing to it. Do not reuse the core redactor (reasons in P8).
3. Loopback or socket by default is right as a guard against mistakes, but it is not proof of "throwaway". The boolean override should be an exact host list. The name marker as written refuses `postgres@localhost:5432/postgres`; the plan must either change CI in the same PR or drop the marker. The check must reuse `_address_parts` and fail closed.
4. See P5: `postgres`, `localhost` and the port vanish from messages and test ids; passwords under 6 characters get nothing. Handle by not doing grams at all, or by password-only grams that never touch the id column.

## RECOMMENDATION
Revise D-002 before building, in this order:
1. Evidence run on `db0d9eb` (M1, M4).
2. M3: one strict grammar (`_address_parts` extended), fail closed on `unparsed`, loopback or socket default, exact `throwaway_hosts` override, explicit decision on the marker and CI, negative tests.
3. M2: output projection at `_row`, the skip messages and the baseline error when `pass_env` is set; existing masker untouched as the second layer; fuzz test with random slices proven to fail on old code.
4. Minors in a separate commit, with m4 rewritten per P7.
5. Add the ladder line and the redactor-reuse answer.

## NOT CHECKED
- Nothing was executed: no tests, no pytest truncation behaviour, no libpq behaviour. The `hostaddr`, `service=` and query-override claims are from my knowledge of libpq, not from a run.
- `DIFF.patch`: I read only the CHANGELOG hunk, the `tests/conftest.py` hunk and the file list. I did not read `tests/test_mutation_runner_keywords.py` (about 2,900 lines), so the number of tests that P4 option 1 or 2 would change is unknown.
- `guard/redact.py` was read only at lines 862-901. Whether a seeded map makes `redact_text` sweep a known value was not verified.
- Whether any demo or other repository already calls `run_mutants(pass_env=...)`.
- Whether editing `ci.yml` is allowed for this session (D-003 mentions an open security-CI question).
- Windows behaviour, the sha256 pins, and the lock-file findings (m7).
