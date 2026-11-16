# Hand-off v17: what changed from v16 (v16 files are unchanged)

**Failures and gaps first.** (1) Not run: unit tests of the product change (none written), `bandit`, CodeQL, the EGM skills (not invokable from this agent; review of v17 is owed, and DB-3 and the v17 guard are money and audit path text no reviewer has read). (2) `gate4` was NOT run in v17; the v16 baseline (`pytest` rc=1, two guard tests outside this folder, L20) is carried and the tree may have changed since. (3) Postgres results are 16.15 only; 14 and 17.10 are not run (L18). (4) All v17 runs are author-run (an independent re-run is asked for). (5) Everything in `evidence-handoff-v17/` is prototype code. (6) DB-3 changes nothing until the owner says yes (L22) and the lead names the operator role (L23); until then the exposure of v16 section 0 item 5 stands. (7) The guard is a text check on `.sql` files; a function made by hand in a console is only caught by the start-up check. (8) The DB-1 timing numbers differ between runs by more than I can explain (machine noise).

Evidence: `pg_v17.py` 49 of 49 in two runs; the 175 v16 checks on the v17 files 175 of 175 in two runs; 20 guard mutants (12 missed by the v16 guard) and 10 real files clean; secrets 7 checks, 0 failures. Raw files: `evidence-handoff-v17/raw/`.

Column "Fails on v16" says what I ran to show the new test or control does not pass on the v16 design (C = control run in the raw file; T = text only, no run).

| Finding | Fix (where in v17 file) | Test | Fails on v16 |
|---|---|---|---|
| Sec M1 kill switch and total lowering | DB-3, 5.6 item 1(o); L22, L23; 5.10b | G0 to G11 (`pg_v17.py`); product `tests/test_guarded_writes_pg.py` (not written) | C: runtime zeroes a settled total of 10; releases the switch with a chosen `by` (G controls) |
| Sec M2 guard bypassed | v17 guard, 5.6 item 1(j) | S01 to S20 in `secdef_mutants_v17.py`, plus the real files | C: 12 mutants missed by the v16 guard (`raw-secdef-mutants-v17.txt`) |
| Sec M3 audit-reader secret | 5.6 item 1(g2): placement, start-up probe, spy test replaced | `run_secrets_v17.sh` M3a to M3g; product `tests/test_audit_reader_secret.py` (not written) | C: M3g (group-readable file) is READ by the agent, so the check detects the bad setup; v16 had only the spy test |
| Sec m4 NaN via INSERT branch | 5.4 item 4b(i) both branches | H1 | C: positive reserve on a NaN row returns NaN with no check |
| Sec m5 record failure blocks switch | 5.6 item 1(m), DB-2 file v17 | K m5 (3 checks) | C: the v16 file blocks switch ON |
| Sec m6 breaker code | 5.3 `circuit_open` in codes, 5.5 table and text | `tests/test_breaker.py` (not written) | T |
| Sec m7 reason-code list | verified in `src/` by hand (guard reason codes read); UNVERIFIED mark removed for `src/` only | none | T |
| Sec m8 pilot leniency, L-2 date | 5.6 item 4 (pilot with a paid kind refuses); 5.10b slip rule | start-up tests (not written) | T |
| Ma1 G-4(i) test undefined; item 4 vs DB-1 | 5.4 item 4, 5.6 (c): inline ALTER, test defined with owner S-2a | `test_store_emits_update_for_negative_deltas` (not written) | T |
| Ma2 upgrade file ownerless; DB-2 tests in DB-1 | 7.1 rows DB-1 and DB-2 | the lock test of every file (L series) | C: L series |
| Ma3 breaker unspecified | 5.1 settings, 5.3 spec | `tests/test_breaker.py` (not written) | T |
| Ma4 `GuardrailPrice` source | 5.7 `Deps.spend`, `ALLOWED` | none written | T |
| Ma5 two reservers | 5.8 `ChainReserver` | `tests/test_chain_reserver.py` (not written) | T |
| Ma6 gate type | 5.3 `Gate`, S-2a owns the test sites | none written | T |
| Ma7 pass rule, defaults | 7.2 pass rule, section 10 | none | T |
| Ma8 timing numbers | 5.6 (b) v16 and v17 raw numbers | raw files | C: v16 text printed v15 numbers |
| Mi1 to Mi9 | 5.3 (frozenset constant; kept total owner; Ticket limits; route rule), 5.1 (cli rule), 7.2 (one gate4 path, census owners), section 10 (lists), 5.6 (g) signatures | none written | T |
| Evid 1 DB-2 no `lock_timeout` | line added in the DB-2 file (sha in section 8), 5.6 (n) | lock test for each held file | C: the v16 file waits to my 12 s cap (57014) |
| Evid 2 section 8 hashes | full table of five files, v15 hash labelled as v15 | `sha256sum -c sha256-v17.txt` | T |
| Evid 3 `redact.py:1162` | read by hand: the word `"dev"` in `_COMMON`; H-0 adds `"demo"` | none | T |
