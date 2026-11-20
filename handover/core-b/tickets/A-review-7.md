# A-review-7: schema-qualified audit statements, `_Db._t` (branch cloud/core-b, step A9)

Reviewer: fresh, read-only on source. One run, no workers:
`HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test uv run --all-extras --group test pytest -q -p no:cacheprovider tests/test_audit_schema_qualified_pg.py tests/test_audit_drain_write_path.py` -> **7 passed in 1.18s**.

Verdict: **CLEAN** (nothing above Minor). Four Minor, one Note.

## 1. The regex rewrite (src/hadavin_sdk/audit/chain.py:66, :181)

`_TABLE_NAME = \b(audit_entries|audit_checkpoints|audit_outbox)\b`, applied after `?` -> `%s`.

- Index and column names: `_` is a word character, so `\b` does not fire inside `audit_entries_by_run` (the real index,
  :59), `audit_entries_idx`, or a column `audit_outbox_id`. Not rewritten. Correct.
- String literals: the rewrite is blind to quoting, but no statement in chain.py contains a literal holding one of the
  three words, a `?` or a `%` (checked every SQL string: :282-:646, the pg `substring(body from '"ts":"([^"]*)"')`
  has no `?`). Event bodies and the quarantine prefix go through bound parameters (:326, :404, :453), so JSON text is
  never touched. Correct for the current statements.
- Double qualification: `_t` is applied once per statement (`_q` is the only caller, :184; `transaction()` yields `_q`,
  so `q(...)` is not wrapped twice). No call site passes an already-qualified name (grep of the file: none). Latent only:
  `"s".audit_entries` would become `"s"."s".audit_entries`, and a quoted `"audit_entries"` would become
  `""s".audit_entries"` (syntax error). Also a `?` or the table words inside any future literal would be rewritten.
  - **Minor-1** (:66, :181): add a negative lookbehind `(?<![."\w])` (and a lookahead for `"`) or state in the docstring
    that statements must be written unqualified, unquoted, literal-free; a one-line unit test of `_t` on
    `'audit_entries_by_run'`, a `"audit_outbox_id"` column and a literal would pin it. Not a defect today.

## 2. Schema quoting and the lazy fallback

- Quoting (:180): `"` + replace(`"`, `""`) + `"` is the correct PG identifier quoting; an uppercase name or one with a
  quote or dot is preserved exactly (the schema comes from `current_schema()` or the store, which are the stored name).
  **Minor-2**: no test uses a mixed-case or quote-bearing schema (the fixture names are `t_<hex>`); the quoting branch is
  unexercised.
- Fallback (:175-179): resolved once, under the lock (every path reaches `_t` through `run` or `transaction`, which hold
  `self.lock`), and `current_schema()` never answers `pg_temp`. Pinning is the desired behaviour: if search_path changes
  later on the same connection the chain keeps the schema the migrated tables live in, and it matches the store, whose
  `_schema` is also resolved once (store/postgres.py:226). A pool is not a case here: the store has one
  connection per process (chain.py:826 comment, `autocommit=True` at store/postgres.py:163) and `build()` passes the
  store's own `_schema`, so the fallback is only reached by a direct `_Db(..., pg=True)` with no schema.
  **Note**: inside `transaction()` after the advisory-lock statement the first-use `current_schema()` runs in the open
  transaction; harmless, since no production path reaches the fallback.

## 3. The decoy test, mutant run

Scratch copy /tmp/core-b-scratch-A9/repo (repo untouched), `_t` reduced to `return sql.replace("?", "%s")` (unqualified):

- `test_the_chain_in_a_non_default_schema_leaves_decoy_tables...` **FAILS** with
  `RuntimeError: audit outbox: 1 unreadable rows kept`: with search_path `<schema>,public` and the pg_temp decoys, the
  unqualified outbox resolves to pg_temp first and the drain reads the decoy `x` row. So the decoy test genuinely
  distinguishes the unqualified mutant, through the exact shadowing the change exists for (pg_temp first).
- `test_unqualified_names_fail_this_test` passes under the mutant too, by design (it expects failure).
  **Minor-3** (tests/test_audit_schema_qualified_pg.py:121-125): it swallows ANY exception and `return`s, so it would also
  pass if `_exercise` broke for an unrelated reason (a typo, a fixture error); it does not prove the mutant fails for the
  decoy reason. Cheap fix: assert on the exception (`RuntimeError`/`psycopg.Error`) or on `after != before`, and drop the
  broad catch. The first test carries the real guarantee, so this is a weakness of the second only.

## 4. Test 3 of the write-path file (tests/test_audit_drain_write_path.py:83-95), sqlite trigger as a role

Faithful enough for what it asserts: the property is "any exception from the parking INSERT falls through to memory and
leaves `_outbox_dirty` False" (chain.py:322-337 catches `Exception`), independent of the error class; the sqlite
`RAISE(ABORT)` (IntegrityError) and PG 42501 take the same branch. PG-specific risk (an aborted transaction poisoning the
next statement) does not apply: the store connection is autocommit and the parking INSERT is outside `transaction()`.
A dedicated PG role test is not needed for the logic, and the PG side is already covered with a real denial:
tests/test_release_expired_spend_pg.py:428-450 (`test_a_lost_outcome_with_the_real_chain...`) runs the real chain on the
release login (no INSERT on audit_outbox, rights pinned at :270-276 and :280-292) and asserts `len(audit._pending) == 1`
and one chain row; tests/test_stop_state_roles.py:558-559 pins the outbox denial.
**Minor-4**: that PG test does not assert `audit._outbox_dirty is False`, the exact property of test 3; one added assert
there would make the real-role path pin it (test edit, not a code change).

## 5. New

Nothing above Minor. `?`->`%s` runs on all pg statements, including ones with a `%` literal in SQL: none exist (the LIKE
`%` is in a bound parameter), so psycopg's placeholder parsing is safe today.

## Severity summary

- Blocker / Major: none.
- Minor-1 regex fragile to future quoted/qualified/literal SQL (chain.py:66,:181); Minor-2 no mixed-case or quoted schema
  test; Minor-3 broad `except Exception: return` in the mutant test (:121-125); Minor-4 missing `_outbox_dirty` assert in
  the PG release test.
- Note: lazy fallback pinned once, matches the store.

**CLEAN.**
