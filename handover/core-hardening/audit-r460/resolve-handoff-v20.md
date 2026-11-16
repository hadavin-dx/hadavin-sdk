# Resolve, hand-off v19 reviews (security, readiness) and the independent evidence run of v19. Hand-off v20.

Status words: FIXED-IN-TEXT, RUN (a raw file in `evidence-handoff-v20/raw/` shows it on 16.15 with reference code, author-run), STATED (not closed, reason given), OWNER-ONLY, LEAD-ONLY, T (text only: the product code is written by a later PR). Nothing is "verified" beyond the evidence named. The EGM resolve skill was not invoked (a builder cannot call it); the lead runs it. Every id with its test: `v20-CHANGES.md`.

| Id | Status | Where |
|---|---|---|
| Sec B1 (RETURN-form definer) | FIXED-IN-TEXT; RUN (server runs it with owner rights; v19 guard clean, v20 flags; mutants) | 5.6c item 1 |
| Sec M1 (`%I.name(` in EXECUTE) | FIXED-IN-TEXT; RUN | 5.6c item 1 |
| Sec M2 (trigger DROP and neuter) | FIXED-IN-TEXT; RUN (lowerings stop being recorded on the server) | 5.6c item 1 |
| Sec M3 (MERGE, USING, TABLE) | FIXED-IN-TEXT; RUN | 5.6c item 1 |
| Sec M4 and runner F1 (replacement bodies of listed functions) | FIXED-IN-TEXT as text fingerprints and statement-kind pins; RUN; the catalog body hash is NOT done (STATED: stability on 14 and 17 not shown) | 5.6c item 1 |
| Sec m1 and runner F2 (expressions) | FIXED-IN-TEXT; RUN | 5.6c item 1 |
| Sec m2, m3 | FIXED-IN-TEXT; RUN (m3: six cases against the server; vertical tab is refused by the server, harmless) | 5.6c item 1 |
| Sec m4 (agent id, locale, encoding) | FIXED-IN-TEXT in DB-3; RUN on UTF8 with two collations and LATIN1; SQL_ASCII: the product `migrate()` fails before any held file (STATED, the client must be told); the character set is a lead decision (L25) | 5.6c item 2 |
| Sec m5 (volume) | measured (RUN), not restricted; lead decision L24 | 5.6c item 5 |
| Sec m6 (cutover) | FIXED-IN-TEXT; RUN (open reservation refused at settle, apply-time refusal and rollback, month row, lock timeout inside `migrate()`); after the commit there is no down file (STATED, needs its own review) | 5.6c item 7 |
| Ready M1 (stale v16 path) | FIXED-IN-TEXT | 7.2 E0-S1-5 |
| Ready M2 (L19) | FIXED-IN-TEXT; test row; product code T | 5.6 L19, 5.5b item 3 |
| Ready M3 (`limits status --check`) | FIXED-IN-TEXT (spec); code T; the schedule and the person to tell stay L13 (nobody named) | 5.6c item 5 |
| Ready M4 (start-up query inputs) | FIXED-IN-TEXT (spec); code T | 5.6c item 4 |
| Ready M5 (Grant function kind, migrate keyword) | FIXED-IN-TEXT (spec); the L-2 store code remains dated design only (STATED, 5.10b) | 5.6c item 6 |
| Ready M6 (L18 commands) | FIXED-IN-TEXT; the commands were run as written (secrets: from `/opt/hv20`) | 5.6 L18 |
| Ready minors (comparator, six cells, section 10 numbers, heading, identical run files, rows, hashes, 5.1 item 7) | FIXED-IN-TEXT; `raw-pg-v20-run1.txt` and `-run2.txt`: see `INVENTORY.md` | see `v20-CHANGES.md` |
| Runner F4 (temp table `spend`) | RUN; stated in text | 5.6c item 3 |
| Runner F5 (empty results, lookalike ids) | RUN; store rule T with test row `E0-F5` | 5.6c items 2 and 3 |
| Runner F6 (gate4, PG 14 and 17 not run) | PARTLY: ruff, format, bandit, pytest, perf run one by one; 14 and 17 NOT run (needs servers I do not have; next step: L18) | 0-v20 |

**Classification of what stays open (rule "fix, don't defer"):** the catalog body hash (cannot be tested here on 14 and 17: third-party version; next step an independent runner on 14 and 17); Postgres 14 and 17.10 (same); the down file (needs an owner or lead decision and its own review); L24 and L25 (lead decisions); the product code of the start-up check, `limits status --check`, `function_grants` and the store's empty-result rule (written by S-2b and DB-3 after two independent reviews of this text, as the hand-off says).

**Honest limit of the whole batch.** The guard is a list of the cases I and the reviewers thought of; each round found new ones. v20 closes every named case and the classes behind them (bodies, expressions, triggers, statement kinds), but a fresh reviewer may find another. The safety does not rest on the guard alone: it rests on the guard plus the start-up catalog check plus the owner-only apply step plus review.
