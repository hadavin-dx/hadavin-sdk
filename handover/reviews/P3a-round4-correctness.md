# P3a ticket, round 4, CORRECTNESS review
- Reviewer: egm:egm-codebase-details (fresh, read-only, Sonnet 5.5). Ticket tickets/P3a.md rev 5 (60e16a5). Nothing run.
- Result: BLOCKER 1, MAJOR 8, MINOR 8 (C1-C17). Stop rule NOT met.
- Saved by the lead 2026-11-05, CONDENSED to one short line per finding (evidence dropped; the full text was delivered to the lead in chat). The author re-checks every claim in the code. Ledger BL-core-p3a-r4-cor-*.

| id | sev | problem / fix |
|---|---|---|
| C1 | BLOCKER | The `gone` split by number is wrong for the package's own case: ledger 0001-0004 + `0006_evidence`, folder ends at 0005: 6>5 so the "newer, do not rename" text is printed, but runbook (b)/(e) and CHANGELOG line 11 require the rename. Cases (h),(i) cannot give their stated text. Fix: classify by name suffix (`0006_evidence` vs file `0005_evidence` = rename), or print both advices when a gone number exceeds the max; tests for that and a mixed list. |
| C2 | MAJOR | FAIL-BEFORE 7 asserts text contains "newer than this release" and NOT "rename", but the new text says "do not rename..."; the old text also has "rename". Cannot pass/discriminate (M18, M19). Fix: assert "newer than this release" in and "by hand"/"no file in this release" not in. |
| C3 | MAJOR | `tests/test_k2_migrations.py:387-394` breaks (ledger 0001-0005, patched list drops 0005: 5>4 gives the "newer" text, test matches "no file in this release"). Ticket claims it still passes; P4d.md lines 150, 184 reuse it. Fix: keep the phrase in both messages or list the test change and tell P4d; add an "existing tests that change" section. |
| C4 | MAJOR | "Old messages word for word" but names use `ascii()` which keeps quotes; `test_plant_badly_named_file_is_caught` (test_k2:50-55) compares exactly. Fix: `ascii(x)[1:-1]` or list the test as changed. |
| C5 | MAJOR | `statement_text` strips single-quoted strings before comments: released files have apostrophes in `--` comments (0004 l.4 "deployment's", 0005 l.1/19 "run's") so strings run on/swallow statements (incl. `CREATE TABLE tool_calls`); unterminated-string behaviour unstated; bypass `-- don't` / `COMMIT;` / `-- it's`. Fix: single-pass lexer (comment, string, E-string, `''`, `$tag$`, nested `/* */`), define unterminated quote, tests over all five real files and the plant. |
| C6 | MAJOR | Refusal (b) lists only `SET ROLE`/`SET SESSION AUTHORIZATION` but `SET LOCAL ROLE`, `SET LOCAL SESSION AUTHORIZATION`, `SET [LOCAL] session_replication_role=replica` (disables audit triggers for a superuser migration role), `set_config('role',..)` pass. Fix: refuse them; whitelist SET LOCAL targets (`search_path`, `lock_timeout`); planted files. |
| C7 | MAJOR | M5 (accept directories/dangling links) survives FAIL-BEFORE 4-5: removing `is_file()` still gives an OSError "cannot be read" refusal. Fix: assert the distinct "not a regular file" message or merge M5 into M9. |
| C8 | MAJOR | Layer 1 planted cases only add/change; no REMOVAL (`DROP TRIGGER audit_entries_append_only`, `DROP CONSTRAINT runs_state_check`, `DROP TABLE`, `ALTER COLUMN TYPE`, `SET NOT NULL`); M27 mutants drop whole kinds, so an additions-only comparer survives. Fix: planted removals per kind and finer mutants (type only, NOT NULL only, relation existence, trigger removal). |
| C9 | MAJOR | `ACCEPTED_CHANGES` consumer named is P4d-b `CHECK (usd >= 0)`, which P4d.md does not have; the real first consumer is P2a-1a (trigger on old `kill_switch`); layer 2 excludes new table+trigger, but P2a.md line 73 relies on P3a's downgrade-read test. Fix: name P2a-1a, replace the P4d example, tell P2a what P3a provides. |
| C10 | MINOR | `0000_a.sql` matches NAME, gap check `range(1,max+1)` never reports 0. Refuse number 0 or state intent; test. |
| C11 | MINOR | P4d.md line 183 cites P3a.md line 99; the layer-2 request is line 100. P3a says P4d's `require_backend` replaces the check "if it merges first" but P3a is ordered first. Fix cite and wording. |
| C12 | MINOR | "runbook cases vii and v" do not exist (runbook is (a)-(f)); two lettering schemes collide; audit/evidence columns are readable in 0002/0005. Fix refs, distinct labels. |
| C13 | MINOR | Recipe omits that psql must use the same `search_path`/schema as `migrate`. Add "same DSN options". |
| C14 | MINOR | `ALTER TYPE ... ADD VALUE` is allowed in a transaction since PG 12: give it its own reason; missing refusals `CLUSTER` without table, `DISCARD ALL`, `CREATE/DROP SUBSCRIPTION` (add or declare out of scope). |
| C15 | MINOR | No test kills dropping the "start of a statement" anchor (mid-statement `END`, `CASE...END`, `COMMENT ON ... 'begin'`); `BEGIN ATOMIC ... END;` behaviour undecided. |
| C16 | MINOR | FAIL-BEFORE 6 must say "real files plus the planted file"; the planted file alone gives ConfigError on ce70eb5 before connecting. |
| C17 | MINOR | M13 killer ("ledger fuzz case") non-specific; name a pure test: applied `{"٠٠٠٩_x"}`, file `0005_a`, expect `[]`. |

Also noted: header claim that P3a must merge before P5b3/P5b4/P5c/P6a/P6b2 is overbroad (P3a does not touch cli.py).
Model used: Sonnet 5.5 (set by the lead).
