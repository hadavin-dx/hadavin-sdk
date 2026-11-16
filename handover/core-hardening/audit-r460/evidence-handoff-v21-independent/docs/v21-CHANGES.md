# v21 changes (round 8): finding, fix, place, test

Sources: `review-handoff-v20-readiness.md` (B1, B2, M1-M8, m1-m6), `review-handoff-v20-security.md` (M1-M3, m4-m12), `review-handoff-v20-evidence.md` (independent runner of v20: B1, G1-G8). Everything below was run by the author on Postgres 16.15 only. "Place" means a section of `CORE-PR-HANDOFF-v21.md`; "test" is a check in `evidence-handoff-v21/`.

## What went where (the one-layer rule)
| v20 text | v21 |
|---|---|
| header lines 3 and 5 (v19 / round 5) | two new header paragraphs, round 8 |
| section 0 (v19 text) and section 0-v20 | one section 0, items 0 to 10 |
| 5.6(o) (v19 DB-3 text), (o2), (p) | one (o), (o2), (p), pointing to 5.6c |
| 5.6(j) (v19 guard history) | one live paragraph (shapes S1-S7, N1-N3) and a pointer to 5.6c item 1 |
| 5.6c "what v20 changed" | 5.6c "the specs as they stand", items 1 to 10 |
| 5.10 and 5.10b | one 5.10 (L-2 paragraph folded in) |
| section 7.2 names (gate4_v18/v19/v20, pg_v19/v20, run_*_v19) | `gate4_v21.sh`, `pg_v21.py`, `run_pg_v21.sh`, `run_secrets_v21.sh` |
| section 8 "Files" paragraph and 8-v16 | one section 8 |
| section 10 head and the "v20 additions" paragraph | one head; the open choices L22b, L26, L26b added |
| other-tracks line 3 (history) | one short paragraph and a gate block |

## Readiness findings
- **B1** (5.6(o) named the v19 file and the old design): one (o) with the v21 file, hash `e2f8017c...75fb`; the old figures (120 checks, NOT VALID, NFC rules) are gone. Test: `sha256sum -c sha256-v21.txt`.
- **B2** (grants contradicted): one grant table (5.6c item 5): runtime role reserve and settle; operator role engage and release; nobody else; PUBLIC nothing. `FUNCTION_POLICY` in `secdef_audit_v21.py` says the same. Test: `pg_v21.py` MA4 (`[T,T,F,F]` and `[F,F,T,T]`).
- **M1** (three signatures): one `secdef_problems(db, *, roles, policy=None, owner=None)`; owner default is the database owner read from the catalog. Place: 5.5b and 5.6c item 4. Test: G0 and the M1r series.
- **M2** (L19 detection): one detection (the table `spend_decrease_log` or the audit-reader role), stated once (5.6 (h), (g2), 5.6c item 4).
- **M3** (`limits status --check` sources): 5.6c item 5 names the source of every check; the default alert on "decreases not made by `spend_settle`" is removed (it cannot be built). L24 default changed (section 10).
- **M4** (no owner for E0-F5 and L-2 store code; `spend_add` in 5.10): the store code is part of the DB-3 move PR (row 5b, gate G-5(e)); E0-F5 is S-2b-2's; 5.10 names the four DB-3 functions.
- **M5** (L24, L25 rows missing): rows added to the conditional test table in 7.2.
- **M6** (7.2 names): all renamed to the v21 scripts.
- **M7** (S-2b too large): split into S-2b-1 and S-2b-2 (row 3 of 7.1), each of at most 60 minutes.
- **M8** (other tracks gate): the other-tracks file now names `gate4_v21.sh` and `compare_gate4.py` and its pass rule ("Gate for every PR of this file").
- **m1, m2**: header, sections 0, 8, 9, 10 and 5.6(j), (p), row 5b rewritten. **m3** the old 5.6(b) cost paragraph is replaced by the 5.6c figure. **m5** stays UNVERIFIED for the builder (listed in section 10). **m6** the other-tracks history sentences were cut; `tests/test_g4_parity.py` exists (`ls`).

## Security findings
- **M1 pseudo ids**: OWNER-OPEN L26b with the correction that the lead's default cannot work as written (5.6c item 8). Test: `pg_v21.py` (pseudo ids refused 23514; an existing `-cli` row makes the apply refuse).
- **M2 empty result on a rejected settle**: the DB-3 settle's final SELECT now ends with `AND p_worst >= 0 AND p_actual >= 0`, so a rejected settle returns no row. Test: G6 (existing rows; control: the v20 file returns a row), G6b (NULL day, NULL amounts, an agent without a row).
- **M3 definer owner**: OWNER-OPEN L26 (5.6c item 8, section 10).
- **m4** alias column list and TABLESAMPLE (W02 to W04); **m5** ASCII case folding (W05 to W07); **m6** `search_path` items folded like the server (W08); **m7** `--` comment ends at `\r` (W09); **m8** `EXECUTE` string with a forbidden statement after a `;` (unit checks P3 to P11); **m9** fingerprint keeps the gap between tokens (`@-` and `@ -` differ, shown on the server); **m10** body bound to a non-`pg_catalog` function or operator: `pg_depend` check in the audit (a pg_v21 case); **m11** contextual words, zero timeouts, `INHERITS`, `DROP TRIGGER` table, `AS case`/`AS end`, invoker bodies (W10 to W18); **m12** schedule: the 60-minute alert only fires when `limits status --check` runs, so 5.6c item 5 asks for a 5 to 15 minute schedule (text only; nobody is named, L13).

## Independent evidence of v20 (relayed late)
- **B1 (CHECK text not pinned; H67, H68, H75, H76)**: `ADD_PINS_BY_FILE` pins every `ALTER TABLE ... ADD` statement of every held file. Tests: mutants W21 to W27 (the v20 guard misses all seven) and controls W28, W29. Not done: a catalog comparison of constraint text (5.6c item 1, B1 bullet; impossible now: needs 14 and 17).
- **G6 (silent no-ops of settle)**: listed in 5.6c item 3; test G6b. **G4**: `run_secrets_v21.sh` pre-check imports pydantic, pydantic_settings and `hadavin_sdk.config` as `nobody` (negative test `raw/raw-secrets-v21-precheck-nopackages.txt`). **G7**: R13 is a case of the runner's own script, not of mine; I added G13 (the runtime login locks and `FOR UPDATE`s inside a transaction: refused 42501; lock modes that are allowed are recorded, not judged). **G1**: stated plainly in section 0 item 1 (helper files not linted). **G2, G3**: kept as NOT RUN with a next step (section 0 item 1). G5 and G8 are the runner's own slips; nothing to change.

## My own slips in v21
Listed in section 0 item 1 (deleted v20 scripts before the v21 ones existed; three wrong expectations in the first Postgres run; an /opt copy without packages for the first secrets run).
