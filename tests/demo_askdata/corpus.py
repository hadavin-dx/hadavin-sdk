"""The validator corpus (P2): attacks, each tagged with the rule that must reject it, a category and the harm it
would do if it reached a privileged session; and benign statements that must be accepted.

`harm` is checked against a real PostgreSQL by test_validate_harm.py:
  write          committed state changed (rows, relations, roles, large objects)
  lock           takes a row-level lock on a base table (RowShareLock or stronger)
  leak:<needle>  returns a cell containing <needle> from data the exposed views hide
  exec           runs to completion on a privileged session (server information, privilege or session change)
  abuse          still running when a 1.2 s statement_timeout cancels it (resource exhaustion)
  pg-refuses     PostgreSQL itself raises an error; the validator is defence in depth and the test says so
"""

# ruff: noqa: S608, ISC004  # SQL text is the test data; implicit concatenation keeps long statements readable

from __future__ import annotations

from typing import NamedTuple

NUL = chr(0)
BACKSLASH = chr(92)
ESC = chr(27)
CR = chr(13)
FF = chr(12)
NBSP = chr(0xA0)
ZWSP = chr(0x200B)
RLO = chr(0x202E)
BOM = chr(0xFEFF)
NEL = chr(0x85)
GREEK_QUESTION = chr(0x37E)  # looks like a semicolon
CYR_I = chr(0x0456)  # looks like Latin i
FULLWIDTH_S = chr(0xFF33)
EACUTE = chr(0xE9)

O = "analytics.orders_v"  # short names keep the table readable
C = "analytics.customers_v"
P = "analytics.products_v"
I = "analytics.order_items_v"


class Attack(NamedTuple):
    name: str
    sql: str
    rule: str
    category: str
    harm: str


def _nested(depth: int) -> str:
    sql = f"SELECT order_id FROM {O}"
    for i in range(depth):
        sql = f"SELECT order_id FROM ({sql}) t{i}"
    return sql


def _joins(n: int) -> str:
    return f"SELECT 1 FROM {O} o0 " + " ".join(
        f"JOIN {O} o{i} ON o{i}.order_id = o0.order_id" for i in range(1, n + 1)
    )


def _ctes(n: int) -> str:
    return (
        "WITH "
        + ", ".join(f"c{i} AS (SELECT order_id FROM {O})" for i in range(n))
        + " SELECT count(*) FROM c0"
    )


A = Attack
ATTACKS: list[Attack] = [
    # ---- stacked and multiple statements (V01)
    A("stacked-delete", "SELECT 1; DELETE FROM shop.order_items", "V01", "multiple-statements", "write"),
    A("stacked-after-comment", "SELECT 1 /* x */ ; DELETE FROM shop.order_items", "V01", "multiple-statements", "write"),
    A("stacked-after-line-comment", "SELECT 1 -- x\n; DELETE FROM shop.order_items", "V01", "multiple-statements", "write"),
    A("stacked-two-selects", "SELECT 1; SELECT 2", "V01", "multiple-statements", "exec"),
    A("stacked-leading-semicolon", "; DELETE FROM shop.order_items", "V01", "multiple-statements", "write"),
    A("stacked-commit-then-write", "COMMIT; BEGIN READ WRITE; DELETE FROM shop.order_items; COMMIT", "V01", "multiple-statements", "write"),
    A("stacked-comment-with-quote", "SELECT 'a' /* ' */ ; DELETE FROM shop.order_items -- '", "V01", "comments", "write"),
    A("stacked-after-nested-comment", "SELECT 1 /* a /* b */ c */ ; DELETE FROM shop.order_items", "V01", "nested-comments", "write"),
    A("nested-comment-unbalanced-close", "SELECT 1 /* a /* b */ ; DELETE FROM shop.order_items", "V01", "nested-comments", "pg-refuses"),
    A("unterminated-comment", "SELECT 1 /* never closed", "V01", "comments", "pg-refuses"),
    A("unterminated-string", "SELECT 'never closed FROM " + O, "V01", "comments", "pg-refuses"),
    A("unterminated-qident", 'SELECT "never closed FROM ' + O, "V01", "comments", "pg-refuses"),
    A("stacked-before-parse-error", "SELECT 1; SELEC", "V01", "multiple-statements", "pg-refuses"),
    # ---- root statement type and writes (V02 / V03)
    A("insert", "INSERT INTO shop.orders VALUES (900001, 1, DATE '2026-01-01', 'paid', 1)", "V03", "writes", "write"),
    A("update", "UPDATE shop.orders SET status = 'x'", "V03", "writes", "write"),
    A("delete", "DELETE FROM shop.order_items", "V03", "writes", "write"),
    A("merge", "MERGE INTO shop.order_items t USING shop.order_items s ON t.order_item_id = s.order_item_id WHEN MATCHED THEN DELETE", "V03", "writes", "write"),
    A("drop", "DROP TABLE shop.orders CASCADE", "V03", "writes", "write"),
    A("truncate", "TRUNCATE shop.orders CASCADE", "V03", "writes", "write"),
    A("create-table", "CREATE TABLE scratch.t AS SELECT 1 AS x", "V03", "writes", "write"),
    A("create-role", "CREATE ROLE askdata_p2_evil LOGIN SUPERUSER", "V03", "writes", "write"),
    A("alter-table", "ALTER TABLE shop.orders ADD COLUMN x integer", "V03", "writes", "write"),
    A("grant", "GRANT ALL ON ALL TABLES IN SCHEMA shop TO PUBLIC", "V03", "writes", "write"),
    A("copy-program", "COPY (SELECT 1) TO PROGRAM 'echo x'", "V03", "writes", "exec"),
    A("copy-to-file", "COPY shop.customers TO '/tmp/askdata_p2_copy.csv'", "V03", "writes", "exec"),
    A("call", "CALL shop.purge()", "V03", "writes", "write"),
    A("do-block", "DO 'BEGIN DELETE FROM shop.order_items; END'", "V03", "writes", "write"),
    A("set-role", "SET ROLE postgres", "V03", "session-state", "exec"),
    A("set-readwrite", "SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE", "V03", "session-state", "exec"),
    A("set-statement-timeout", "SET statement_timeout = 0", "V03", "session-state", "exec"),
    A("transaction-commit", "COMMIT", "V02", "session-state", "exec"),
    A("transaction-begin-readwrite", "BEGIN READ WRITE", "V02", "session-state", "exec"),
    A("show", "SHOW ALL", "V03", "session-state", "exec"),
    A("prepare", "PREPARE p AS SELECT 1", "V03", "session-state", "exec"),
    A("explain-analyze", "EXPLAIN ANALYZE SELECT 1", "V03", "explain", "exec"),
    A("explain-analyze-delete", "EXPLAIN ANALYZE DELETE FROM shop.order_items", "V03", "explain", "write"),
    A("explain-plain", f"EXPLAIN SELECT * FROM {O}", "V03", "explain", "exec"),
    A("values-root", "VALUES (1), (2)", "V02", "root-type", "exec"),
    A("table-shorthand", "TABLE shop.customers", "V01", "root-type", "leak:@"),
    A("select-into", "SELECT 1 INTO scratch_t", "V03", "select-into", "write"),
    A("select-into-temp", f"SELECT * INTO TEMP t FROM {O}", "V03", "select-into", "exec"),
    A("select-into-from-base", "SELECT * INTO scratch_copy FROM shop.customers", "V03", "select-into", "write"),
    A("for-update", f"SELECT * FROM {O} FOR UPDATE", "V03", "locking", "lock"),
    A("for-share", f"SELECT * FROM {O} FOR SHARE", "V03", "locking", "lock"),
    A("for-no-key-update-nowait", f"SELECT * FROM {O} FOR NO KEY UPDATE NOWAIT", "V03", "locking", "lock"),
    A("for-update-skip-locked", f"SELECT * FROM {O} o FOR UPDATE OF o SKIP LOCKED", "V03", "locking", "lock"),
    A("for-update-in-subquery", f"SELECT * FROM (SELECT * FROM {O} FOR UPDATE) s", "V03", "locking", "lock"),
    A("data-modifying-cte", "WITH d AS (DELETE FROM shop.order_items RETURNING *) SELECT * FROM d", "V03", "data-modifying-cte", "write"),
    A("data-modifying-cte-insert", "WITH i AS (INSERT INTO shop.orders VALUES (900002, 1, DATE '2026-01-01', 'paid', 1) RETURNING *) SELECT count(*) FROM i", "V03", "data-modifying-cte", "write"),
    A("data-modifying-cte-update", "WITH u AS (UPDATE shop.orders SET status = 'x' RETURNING order_id) SELECT count(*) FROM u", "V03", "data-modifying-cte", "write"),
    A("data-modifying-cte-nested", "SELECT * FROM (WITH d AS (DELETE FROM shop.order_items RETURNING *) SELECT * FROM d) s", "V03", "data-modifying-cte", "pg-refuses"),
    A("with-over-insert", "WITH t AS (SELECT 1 AS x) INSERT INTO shop.orders SELECT 900003, 1, DATE '2026-01-01', 'paid', x FROM t", "V03", "data-modifying-cte", "write"),
    # ---- relations (V04)
    A("base-table", "SELECT * FROM shop.customers", "V04", "relations", "leak:@"),
    A("base-table-email-join", f"SELECT s.email FROM {C} c JOIN shop.customers s ON s.customer_id = c.customer_id", "V04", "relations", "leak:@"),
    A("catalog-table", "SELECT * FROM pg_shadow", "V04", "relations", "leak:postgres"),
    A("catalog-qualified", "SELECT * FROM pg_catalog.pg_authid", "V04", "relations", "leak:postgres"),
    A("information-schema", "SELECT * FROM information_schema.tables", "V04", "relations", "leak:shop"),
    A("quoted-catalog-table", 'SELECT * FROM "pg_shadow"', "V04", "relations", "leak:postgres"),
    A("three-part-name", "SELECT * FROM postgres.analytics.orders_v", "V04", "relations", "pg-refuses"),
    A("unqualified-view", "SELECT * FROM orders_v", "V04", "relations", "pg-refuses"),
    A("subquery-over-base", "SELECT email FROM (SELECT * FROM shop.customers) s", "V04", "relations", "leak:@"),
    A("scalar-subquery-catalog", "SELECT (SELECT count(*) FROM pg_class)", "V04", "relations", "exec"),
    A("exists-subquery-catalog", f"SELECT 1 FROM {O} WHERE EXISTS (SELECT 1 FROM pg_roles)", "V04", "relations", "exec"),
    A("union-catalog", f"SELECT customer_id::text FROM {C} UNION SELECT rolname::text FROM pg_roles", "V04", "relations", "leak:postgres"),
    A("table-function", "SELECT * FROM generate_series(1, 10)", "V04", "table-functions", "exec"),
    A("table-function-count-huge", "SELECT count(*) FROM generate_series(1, 100000000000)", "V04", "table-functions", "abuse"),
    A("table-function-unnest", "SELECT * FROM unnest(ARRAY[1, 2])", "V04", "table-functions", "exec"),
    A("table-function-rows-from", "SELECT * FROM ROWS FROM (generate_series(1, 3))", "V04", "table-functions", "exec"),
    A("table-function-lateral", f"SELECT * FROM {O} o JOIN LATERAL generate_series(1, 3) g ON g = o.order_id", "V04", "table-functions", "exec"),
    A("table-function-query-to-xml", "SELECT * FROM query_to_xml('select email from shop.customers', true, true, '')", "V04", "table-functions", "leak:@"),
    A("table-function-pg-ls-dir", "SELECT * FROM pg_ls_dir('.')", "V04", "table-functions", "exec"),
    A("table-function-json-each", "SELECT * FROM json_each('{\"a\": 1}')", "V04", "table-functions", "exec"),
    A("table-function-after-join", f"SELECT 1 FROM {O} o JOIN generate_series(1, 3) g ON g = o.order_id", "V04", "table-functions", "exec"),
    A("tablesample", f"SELECT * FROM {O} TABLESAMPLE SYSTEM (10)", "V04", "table-functions", "pg-refuses"),
    A("lateral-subquery", f"SELECT * FROM {O} o JOIN LATERAL (SELECT o.order_id AS x) s ON s.x = o.order_id", "V04", "table-functions", "exec"),
    # ---- CTE scoping (V04)
    A("cte-shadows-catalog", "WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles", "V04", "cte-scoping", "leak:postgres"),
    A("cte-forward-ref-catalog", "WITH a AS (SELECT count(*) AS n FROM pg_class), pg_class AS (SELECT 1 AS z) SELECT n FROM a", "V04", "cte-scoping", "exec"),
    A("cte-forward-ref", "WITH a AS (SELECT * FROM b), b AS (SELECT 1 AS x) SELECT * FROM a", "V04", "cte-scoping", "pg-refuses"),
    A("cte-sibling-in-subquery", "SELECT * FROM (WITH t AS (SELECT 1 AS x) SELECT x FROM t) s JOIN t ON s.x = t.x", "V04", "cte-scoping", "pg-refuses"),
    A("cte-nested-shadow-leak", "WITH a AS (WITH pg_class AS (SELECT 1 AS x) SELECT x FROM pg_class) SELECT count(*) FROM pg_class", "V04", "cte-scoping", "exec"),
    A("cte-self-read", "WITH x AS (SELECT * FROM x) SELECT * FROM x", "V04", "cte-scoping", "pg-refuses"),
    A("cte-named-like-exposed-view", f"WITH orders_v AS (SELECT * FROM {C}) SELECT * FROM orders_v", "V04", "cte-scoping", "exec"),
    A("cte-named-information-schema", "WITH information_schema AS (SELECT 1 AS x) SELECT * FROM information_schema", "V04", "cte-scoping", "exec"),
    A("cte-reads-later-sibling-in-body", f"SELECT * FROM (SELECT * FROM later) q WHERE EXISTS (SELECT 1 FROM {O})", "V04", "cte-scoping", "pg-refuses"),
    A("cte-name-leaks-out-of-subquery", f"SELECT * FROM {O} o WHERE o.order_id IN (WITH t AS (SELECT order_id FROM {O}) SELECT order_id FROM t) AND EXISTS (SELECT 1 FROM t)", "V04", "cte-scoping", "pg-refuses"),
    A("cte-in-second-union-leg", f"SELECT order_id FROM {O} UNION ALL SELECT order_id FROM later_cte", "V04", "cte-scoping", "pg-refuses"),
    # ---- columns, star, whole-row (V05)
    A("restricted-column", f"SELECT email FROM {C}", "V05", "columns", "pg-refuses"),
    A("restricted-column-upper", f"SELECT EMAIL FROM {C}", "V05", "identifier-folding", "pg-refuses"),
    A("restricted-column-qualified", f"SELECT c.email FROM {C} c", "V05", "columns", "pg-refuses"),
    A("restricted-column-schema-qualified", f"SELECT analytics.customers_v.email FROM {C}", "V05", "columns", "pg-refuses"),
    A("restricted-column-in-where", f"SELECT 1 FROM {C} WHERE email LIKE '%@%'", "V05", "columns", "pg-refuses"),
    A("restricted-column-in-order-by", f"SELECT customer_id FROM {C} ORDER BY email", "V05", "columns", "pg-refuses"),
    A("restricted-column-in-subquery", f"SELECT (SELECT max(email) FROM {C})", "V05", "columns", "pg-refuses"),
    A("restricted-column-in-having", f"SELECT country FROM {C} GROUP BY country HAVING max(email) > 'a'", "V05", "columns", "pg-refuses"),
    A("restricted-column-bare-in-having", f"SELECT country FROM {C} GROUP BY country HAVING email = 'x'", "V05", "columns", "pg-refuses"),
    A("keyword-as-column-in-having", f"SELECT country FROM {C} GROUP BY country HAVING max(country) - INTERVAL > 1", "V05", "columns", "pg-refuses"),
    A("wrong-view-column", f"SELECT o.email FROM {O} o", "V05", "columns", "pg-refuses"),
    A("whole-row-alias", f"SELECT o FROM {O} o", "V05", "star-whole-row", "exec"),
    A("whole-row-relation-name", f"SELECT customers_v FROM {C}", "V05", "star-whole-row", "exec"),
    A("whole-row-in-function", f"SELECT count(o) FROM {O} o", "V05", "star-whole-row", "exec"),
    A("whole-row-of-subquery", f"SELECT t FROM (SELECT * FROM {O}) t", "V05", "star-whole-row", "exec"),
    A("whole-row-to-json", f"SELECT to_json(o) FROM {O} o", "V06", "star-whole-row", "exec"),
    A("whole-row-row-to-json", f"SELECT row_to_json(c) FROM {C} c", "V06", "star-whole-row", "exec"),
    A("whole-row-is-null", f"SELECT o IS NULL FROM {O} o", "V05", "star-whole-row", "exec"),
    A("row-constructor", f"SELECT ROW(o.order_id, o.status) FROM {O} o", "V06", "star-whole-row", "exec"),
    A("star-over-unknown-relation", "SELECT t.* FROM (SELECT * FROM pg_shadow) t", "V04", "star-whole-row", "leak:postgres"),
    # ---- functions (V06)
    A("pg-sleep", "SELECT pg_sleep(10)", "V06", "resource-abuse", "abuse"),
    A("pg-sleep-qualified", "SELECT pg_catalog.pg_sleep(10)", "V06", "qualified-functions", "abuse"),
    A("pg-sleep-upper", "SELECT PG_SLEEP(10)", "V06", "function-case", "abuse"),
    A("pg-sleep-quoted", 'SELECT "pg_sleep"(10)', "V06", "function-case", "abuse"),
    A("pg-sleep-quoted-upper", 'SELECT "PG_SLEEP"(10)', "V06", "function-case", "pg-refuses"),
    A("pg-sleep-in-where", f"SELECT 1 FROM {O} WHERE pg_sleep(10) IS NOT NULL", "V06", "resource-abuse", "abuse"),
    A("pg-sleep-in-subquery", f"SELECT (SELECT pg_sleep(10)) FROM {O}", "V06", "resource-abuse", "abuse"),
    A("pg-sleep-for", "SELECT pg_sleep_for(INTERVAL '10 seconds')", "V06", "resource-abuse", "abuse"),
    A("generate-series-select-list", "SELECT sum(g) FROM (SELECT generate_series(1, 100000000000) AS g) s", "V06", "resource-abuse", "abuse"),
    A("repeat-large", "SELECT length(repeat('x', 50000000))", "V06", "resource-abuse", "exec"),
    A("lpad-large", "SELECT length(lpad('x', 50000000, 'y'))", "V06", "resource-abuse", "exec"),
    A("version", "SELECT version()", "V06", "public-functions", "exec"),
    A("current-database", "SELECT current_database()", "V06", "public-functions", "exec"),
    A("current-setting", "SELECT current_setting('server_version')", "V06", "public-functions", "exec"),
    A("set-config", "SELECT set_config('default_transaction_read_only', 'off', false)", "V06", "public-functions", "exec"),
    A("query-to-xml", "SELECT query_to_xml('select email from shop.customers', true, true, '')", "V06", "public-functions", "leak:@"),
    A("table-to-xml", "SELECT table_to_xml('shop.customers', true, false, '')", "V06", "public-functions", "leak:@"),
    A("dblink-connect", "SELECT dblink_connect('dbname=postgres')", "V06", "public-functions", "exec"),
    A("lo-import", "SELECT lo_import('/etc/passwd')", "V06", "public-functions", "write"),
    A("lo-from-bytea", "SELECT lo_from_bytea(0, 'x'::bytea)", "V06", "public-functions", "write"),
    A("pg-ls-dir", "SELECT pg_ls_dir('.')", "V06", "public-functions", "exec"),
    A("pg-read-file", "SELECT pg_read_file('/etc/passwd')", "V06", "public-functions", "leak:root"),
    A("pg-terminate-backend", "SELECT pg_terminate_backend(0)", "V06", "public-functions", "exec"),
    A("pg-advisory-lock", "SELECT pg_advisory_lock(1)", "V06", "public-functions", "exec"),
    A("nextval", "SELECT nextval('shop.nothing_seq')", "V06", "public-functions", "pg-refuses"),
    A("pg-notify", "SELECT pg_notify('c', 'p')", "V06", "public-functions", "exec"),
    A("pg-get-viewdef", "SELECT pg_get_viewdef('analytics.orders_v'::text)", "V06", "public-functions", "leak:shop.orders"),
    A("current-date", "SELECT current_date", "V06", "clock", "exec"),
    A("now", "SELECT now()", "V06", "clock", "exec"),
    A("current-timestamp", "SELECT current_timestamp", "V06", "clock", "exec"),
    A("clock-timestamp", "SELECT clock_timestamp()", "V06", "clock", "exec"),
    A("random", "SELECT random()", "V06", "clock", "exec"),
    A("current-user", "SELECT current_user", "V06", "public-functions", "exec"),
    A("session-user", "SELECT session_user", "V06", "public-functions", "exec"),
    A("schema-qualified-allowed-function", f"SELECT pg_catalog.count(*) FROM {O}", "V06", "qualified-functions", "exec"),
    A("schema-qualified-user-function", f"SELECT public.my_func(order_id) FROM {O}", "V06", "qualified-functions", "pg-refuses"),
    A("function-in-filter-clause", f"SELECT count(*) FILTER (WHERE pg_sleep(10) IS NOT NULL) FROM {O}", "V06", "resource-abuse", "abuse"),
    A("function-in-order-by", f"SELECT 1 FROM {O} ORDER BY (pg_sleep(10) IS NULL)", "V06", "resource-abuse", "abuse"),
    A("function-in-join-on", f"SELECT 1 FROM {O} a JOIN {O} b ON a.order_id = b.order_id AND pg_sleep(10) IS NOT NULL", "V06", "resource-abuse", "abuse"),
    A("function-in-case", f"SELECT CASE WHEN true THEN pg_sleep(10) END FROM {O}", "V06", "resource-abuse", "abuse"),
    A("function-in-window-order", f"SELECT row_number() OVER (ORDER BY (pg_sleep(10) IS NULL)) FROM {O}", "V06", "resource-abuse", "abuse"),
    # ---- casts (V07)
    A("regclass-cast", "SELECT 'pg_shadow'::regclass", "V07", "casts", "exec"),
    A("regclass-cast-function-form", "SELECT CAST('pg_shadow' AS regclass)", "V07", "casts", "exec"),
    A("regproc-cast", "SELECT 'pg_sleep'::regproc", "V07", "casts", "exec"),
    A("regclass-then-oid", "SELECT 'pg_shadow'::regclass::oid", "V07", "casts", "exec"),
    A("oid-cast", "SELECT 1::oid", "V07", "casts", "exec"),
    A("xml-cast", "SELECT '<a/>'::xml", "V07", "casts", "exec"),
    A("json-cast", "SELECT '{}'::json", "V07", "casts", "exec"),
    A("bytea-cast", "SELECT 'x'::bytea", "V07", "casts", "exec"),
    A("name-cast", "SELECT 'x'::name", "V07", "casts", "exec"),
    A("array-cast", "SELECT '{1}'::int[]", "V07", "casts", "exec"),
    A("interval-cast", "SELECT '1 day'::interval", "V07", "casts", "exec"),
    A("qualified-type-cast", "SELECT 'x'::information_schema.sql_identifier", "V07", "casts", "exec"),
    A("cast-type-parameter-is-a-column", f"SELECT CAST(customer_id AS DECIMAL(email, 2)) FROM {C}", "V07", "casts", "pg-refuses"),
    A("typed-literal-regclass", "SELECT regclass 'pg_shadow'", "V07", "casts", "exec"),
    A("cast-of-column-to-regclass", f"SELECT status::regclass FROM {O}", "V07", "casts", "pg-refuses"),
    # ---- joins and recursion (V08)
    A("with-recursive", "WITH RECURSIVE r AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM r) SELECT count(*) FROM r", "V08", "recursion", "abuse"),
    A("cross-join", f"SELECT 1 FROM {O} CROSS JOIN {C}", "V08", "joins", "exec"),
    A("comma-join", f"SELECT 1 FROM {O}, {C}", "V08", "joins", "exec"),
    A("natural-join", f"SELECT 1 FROM {O} NATURAL JOIN {C}", "V08", "joins", "exec"),
    A("join-on-true", f"SELECT 1 FROM {O} a JOIN {O} b ON true", "V08", "joins", "exec"),
    A("join-on-one-equals-one", f"SELECT 1 FROM {O} a JOIN {O} b ON 1 = 1", "V08", "joins", "exec"),
    # ---- raw-text hazards (V09)
    A("nul-byte", "SELECT 1 AS " + NUL, "V09", "control-characters", "pg-refuses"),
    A("terminal-escape", "SELECT 1 " + ESC + "[2K", "V09", "control-characters", "pg-refuses"),
    A("carriage-return", "SELECT 1" + CR + "; DELETE FROM shop.order_items", "V09", "control-characters", "write"),
    A("form-feed", "SELECT 1" + FF + "; DELETE FROM shop.order_items", "V09", "control-characters", "write"),
    A("c1-control-in-literal", f"SELECT '{NEL}' FROM {O}", "V09", "control-characters", "exec"),
    A("backslash-literal", f"SELECT 'a{BACKSLASH}' FROM {O}", "V09", "backslash", "exec"),
    A("backslash-quote-differential", f"SELECT 1 FROM {O} WHERE status = 'a{BACKSLASH}'; DELETE FROM shop.order_items; --'", "V09", "parser-differential", "write"),
    A("backslash-in-comment", f"SELECT 1 -- {BACKSLASH}\n; DELETE FROM shop.order_items", "V09", "backslash", "write"),
    A("backslash-in-qident", f'SELECT 1 AS "a{BACKSLASH}"; DELETE FROM shop.order_items; --"', "V09", "backslash", "write"),
    A("dollar-quote", "SELECT $$x$$", "V09", "dollar-quoting", "exec"),
    A("dollar-tag-hides-stack", "SELECT $a$ ; DELETE FROM shop.order_items; $a$", "V09", "dollar-quoting", "exec"),
    A("dollar-quote-in-where", f"SELECT 1 FROM {O} WHERE status = $q$x$q$", "V09", "dollar-quoting", "exec"),
    A("dollar-in-identifier-position", "SELECT 1 AS $x", "V09", "dollar-quoting", "pg-refuses"),
    A("escape-prefix", "SELECT E'abc'", "V09", "escape-strings", "exec"),
    A("escape-prefix-lower", "SELECT e'abc'", "V09", "escape-strings", "exec"),
    A("escape-string-quote-differential", f"SELECT E'a{BACKSLASH}'; DELETE FROM shop.order_items; --'", "V09", "escape-strings", "exec"),
    A("unicode-escape-string", "SELECT U&'\\0041'", "V09", "escape-strings", "exec"),
    A("unicode-escape-identifier", f'SELECT 1 AS U&"d{BACKSLASH}0061ta"', "V09", "escape-strings", "exec"),
    A("bit-string-prefix", "SELECT B'101'", "V09", "escape-strings", "exec"),
    A("hex-string-prefix", "SELECT X'1F'", "V09", "escape-strings", "exec"),
    A("national-prefix", "SELECT N'abc'", "V09", "escape-strings", "exec"),
    A("parameter", f"SELECT * FROM {O} WHERE order_id = $1", "V09", "placeholders", "pg-refuses"),
    A("parameter-cast", f"SELECT * FROM {O} WHERE order_id = $1::int", "V09", "placeholders", "pg-refuses"),
    A("placeholder-percent-s", f"SELECT * FROM {O} WHERE order_id = %s", "V09", "placeholders", "pg-refuses"),
    A("placeholder-percent-named", f"SELECT * FROM {O} WHERE order_id = %(id)s", "V09", "placeholders", "pg-refuses"),
    A("placeholder-colon-name", f"SELECT * FROM {O} WHERE order_id = :id", "V09", "placeholders", "pg-refuses"),
    A("placeholder-question-mark", f"SELECT * FROM {O} WHERE order_id = ?", "V09", "placeholders", "pg-refuses"),
    A("unicode-lookalike-identifier", f"SELECT customer_{CYR_I}d FROM {O}", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-greek-question-mark", f"SELECT 1{GREEK_QUESTION} DELETE FROM shop.order_items", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-fullwidth-keyword", f"{FULLWIDTH_S}ELECT 1", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-nbsp-between-tokens", f"SELECT{NBSP}1", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-zero-width-in-identifier", f"SELECT customer_{ZWSP}id FROM {O}", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-bidi-override", f"SELECT 1 {RLO}", "V09", "unicode-lookalikes", "exec"),
    A("unicode-byte-order-mark", BOM + "SELECT 1", "V09", "unicode-lookalikes", "pg-refuses"),
    A("unicode-in-quoted-identifier", f'SELECT 1 AS "caf{EACUTE}"', "V09", "unicode-lookalikes", "exec"),
    A("oversize-text", "SELECT '" + "x" * 5000 + "'", "V09", "size-limits", "exec"),
    # ---- constructs and operators, size limits (V10)
    A("frame-rows", f"SELECT sum(total_amount) OVER (ORDER BY order_date ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) FROM {O}", "V10", "window-frames", "exec"),
    A("frame-range", f"SELECT sum(total_amount) OVER (ORDER BY order_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM {O}", "V10", "window-frames", "exec"),
    A("regex-operator-on-call", f"SELECT 1 FROM {O} WHERE LOWER(status) ~ 'a'", "V10", "operators", "exec"),
    A("regex-operator-redos", f"SELECT 1 FROM {O} WHERE status ~ '(a+)+$'", "V10", "operators", "exec"),
    A("regex-operator-insensitive", f"SELECT 1 FROM {O} WHERE status ~* 'a'", "V10", "operators", "exec"),
    A("containment-operator-on-call", f"SELECT 1 FROM {O} WHERE LOWER(status) @> 'a'", "V10", "operators", "pg-refuses"),
    A("json-arrow-operator", f"SELECT status -> 'a' FROM {O}", "V10", "operators", "pg-refuses"),
    A("json-text-operator", f"SELECT status ->> 'a' FROM {O}", "V10", "operators", "pg-refuses"),
    A("operator-syntax", f"SELECT 1 OPERATOR(pg_catalog.+) 1 FROM {O}", "V10", "operators", "exec"),
    A("collate", f"SELECT status COLLATE \"C\" FROM {O}", "V10", "operators", "exec"),
    A("subscript", f"SELECT (ARRAY[1, 2])[1] FROM {O}", "V10", "operators", "exec"),
    A("array-constructor", f"SELECT ARRAY[order_id] FROM {O}", "V06", "operators", "exec"),
    A("similar-to", f"SELECT 1 FROM {O} WHERE status SIMILAR TO '(a|b)+'", "V10", "operators", "exec"),
    A("at-time-zone-column", f"SELECT order_date AT TIME ZONE status FROM {O}", "V10", "operators", "pg-refuses"),
    A("interval-huge", f"SELECT order_date + INTERVAL '99999 days' FROM {O}", "V10", "size-limits", "exec"),
    A("interval-unit-seconds", f"SELECT order_date + INTERVAL '5 seconds' FROM {O}", "V10", "size-limits", "exec"),
    A("filter-on-non-aggregate", f"SELECT lower(status) FILTER (WHERE true) FROM {O}", "V10", "operators", "pg-refuses"),
    A("within-group-non-percentile", f"SELECT mode() WITHIN GROUP (ORDER BY status) FROM {O}", "V10", "operators", "exec"),
    A("deep-nesting", _nested(12), "V10", "size-limits", "exec"),
    A("too-many-joins", _joins(9), "V10", "size-limits", "exec"),
    A("too-many-ctes", _ctes(5), "V10", "size-limits", "exec"),
    A("too-many-nodes", "SELECT " + "+".join(["1"] * 1400), "V10", "size-limits", "exec"),
    A("long-literal", f"SELECT '{'x' * 300}' FROM {O}", "V10", "size-limits", "exec"),
    A("deep-parentheses", "SELECT " + "(" * 500 + "1" + ")" * 500, "V01", "size-limits", "exec"),
    # ---- re-parse identity (V11)
    A("generator-disagreement", f"SELECT 1 FROM {O}", "V11", "reparse-identity", "none"),
    # ---- identifiers (V12)
    A("upper-quoted-view", 'SELECT * FROM analytics."Orders_V"', "V12", "identifier-folding", "pg-refuses"),
    A("upper-quoted-schema", 'SELECT * FROM "ANALYTICS".orders_v', "V12", "identifier-folding", "pg-refuses"),
    A("upper-quoted-column", f'SELECT "Order_Id" FROM {O}', "V12", "identifier-folding", "pg-refuses"),
    A("quoted-identifier-with-space", f'SELECT 1 AS "my col" FROM {O}', "V12", "identifier-folding", "exec"),
    A("quoted-identifier-trailing-space", f'SELECT "order_id " FROM {O}', "V12", "identifier-folding", "pg-refuses"),
    A("quoted-identifier-with-semicolon", f'SELECT 1 AS "a;b" FROM {O}', "V12", "identifier-folding", "exec"),
    A("quoted-identifier-doubled-quote", f'SELECT 1 AS "a""b" FROM {O}', "V12", "identifier-folding", "exec"),
    A("quoted-upper-alias", f'SELECT order_id AS "Total" FROM {O}', "V12", "identifier-folding", "exec"),
]  # fmt: skip

# (name, sql)
BENIGN: list[tuple[str, str]] = [
    ("count", f"SELECT count(*) FROM {O}"),
    ("count-distinct", f"SELECT count(DISTINCT customer_id) FROM {O}"),
    (
        "cte-later-uses-earlier",
        f"WITH a AS (SELECT customer_id FROM {O}), b AS (SELECT customer_id FROM a) SELECT count(*) FROM b",
    ),
    ("cte-nested-own-scope", "SELECT * FROM (WITH t AS (SELECT 1 AS x) SELECT x FROM t) s"),
    ("cte-column-list", f"WITH t(a, b) AS (SELECT order_id, status FROM {O}) SELECT a, b FROM t"),
    ("cte-named-like-base-table", f"WITH orders AS (SELECT * FROM {O}) SELECT count(*) FROM orders"),
    (
        "cte-used-in-subquery",
        f"WITH t AS (SELECT order_id FROM {O}) SELECT * FROM {O} WHERE order_id IN (SELECT order_id FROM t)",
    ),
    (
        "group-by",
        f"SELECT category, count(*) AS n FROM {P} GROUP BY 1 ORDER BY n DESC LIMIT 5",
    ),
    (
        "group-by-having",
        f"SELECT customer_id, sum(total_amount) AS s FROM {O} GROUP BY customer_id HAVING sum(total_amount) > 100",
    ),
    (
        "limit-offset",
        f"SELECT order_id FROM {O} ORDER BY order_id LIMIT 10 OFFSET 20",
    ),
    (
        "join",
        f"SELECT c.country, count(*) AS orders FROM {O} o JOIN {C} c"
        " ON c.customer_id = o.customer_id GROUP BY c.country ORDER BY orders DESC",
    ),
    (
        "join-using",
        f"SELECT count(*) FROM {O} JOIN {C} USING (customer_id)",
    ),
    (
        "left-join",
        f"SELECT c.full_name, count(o.order_id) FROM {C} c LEFT JOIN {O} o ON o.customer_id = c.customer_id GROUP BY c.full_name",
    ),
    (
        "three-way-join",
        f"SELECT p.category, sum(i.line_amount) FROM {I} i JOIN {P} p ON p.product_id = i.product_id"
        f" JOIN {O} o ON o.order_id = i.order_id WHERE o.status = 'paid' GROUP BY p.category",
    ),
    (
        "cte",
        f"WITH t AS (SELECT customer_id, sum(total_amount) AS s FROM {O} GROUP BY customer_id)"
        " SELECT avg(s) FROM t",
    ),
    (
        "window-rank",
        f"SELECT customer_id, rank() OVER (ORDER BY total_amount DESC) AS r FROM {O}",
    ),
    (
        "window-partition",
        f"SELECT order_id, row_number() OVER (PARTITION BY customer_id ORDER BY order_date) AS n FROM {O}",
    ),
    (
        "window-lag",
        f"SELECT order_id, lag(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) FROM {O}",
    ),
    (
        "date-trunc",
        f"SELECT date_trunc('month', order_date) AS m, sum(total_amount) FROM {O} GROUP BY 1",
    ),
    ("extract-year", f"SELECT extract(year FROM order_date) AS y, count(*) FROM {O} GROUP BY 1"),
    ("date-part", f"SELECT date_part('month', order_date) FROM {O}"),
    (
        "percentile",
        f"SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY total_amount) FROM {O}",
    ),
    ("filter", f"SELECT count(*) FILTER (WHERE status = 'paid') FROM {O}"),
    (
        "case",
        f"SELECT CASE WHEN total_amount > 100 THEN 'big' ELSE 'small' END AS size, count(*)"
        f" FROM {O} GROUP BY 1",
    ),
    ("coalesce-nullif", f"SELECT coalesce(nullif(status, ''), 'none') FROM {O}"),
    ("round-numeric", f"SELECT round(avg(total_amount), 2) FROM {O}"),
    ("greatest-least", f"SELECT greatest(total_amount, 0), least(total_amount, 1000) FROM {O}"),
    ("string-functions", f"SELECT upper(full_name), lower(country), length(full_name) FROM {C}"),
    ("concat-operator", f"SELECT full_name || ' (' || country || ')' FROM {C}"),
    ("time-zone", f"SELECT order_date AT TIME ZONE 'UTC' FROM {O}"),
    (
        "literals-with-comment-markers",
        f"SELECT 'a--b', 'c/*d*/' FROM {O} -- real comment",
    ),
    ("literal-with-semicolon-and-quote", f"SELECT 'x'';DELETE FROM shop.order_items;--' FROM {O}"),
    ("literal-with-percent-and-colon", f"SELECT 'a%s:b?c' FROM {O} LIMIT 1"),
    ("literal-non-ascii", f"SELECT 1 FROM {C} WHERE full_name = 'Zo{EACUTE}'"),
    ("line-comment-hides-statement", f"SELECT 1 FROM {O} -- ; DELETE FROM shop.order_items"),
    ("nested-comment-hides-statement", f"SELECT 1 /* a /* ; DELETE FROM shop.order_items */ b */ FROM {O}"),
    ("trailing-semicolon", f"SELECT 1 FROM {O};"),
    ("quoted-plain-identifiers", 'SELECT "order_id" FROM analytics."orders_v"'),
    ("unquoted-upper-folds", "SELECT ORDER_ID FROM ANALYTICS.ORDERS_V"),
    ("star", f"SELECT * FROM {C}"),
    ("star-qualified", f"SELECT o.* FROM {O} o"),
    ("star-in-count", f"SELECT count(*) FROM (SELECT * FROM {O}) s"),
    ("union", "SELECT 1 AS a UNION ALL SELECT 2"),
    ("intersect", f"SELECT customer_id FROM {O} INTERSECT SELECT customer_id FROM {C}"),
    ("except", f"SELECT customer_id FROM {C} EXCEPT SELECT customer_id FROM {O}"),
    ("interval", f"SELECT order_date + INTERVAL '7 days' FROM {O}"),
    ("interval-months", f"SELECT order_date - INTERVAL '3 months' FROM {O}"),
    ("age", f"SELECT age(order_date, DATE '2026-01-01') FROM {O}"),
    (
        "exists",
        f"SELECT 1 FROM {O} o WHERE EXISTS"
        f" (SELECT 1 FROM {C} c WHERE c.customer_id = o.customer_id)",
    ),
    ("not-exists", f"SELECT count(*) FROM {C} c WHERE NOT EXISTS (SELECT 1 FROM {O} o WHERE o.customer_id = c.customer_id)"),
    ("in-list", f"SELECT count(*) FROM {O} WHERE status IN ('paid', 'shipped')"),
    ("between", f"SELECT count(*) FROM {O} WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-03-31'"),
    ("is-null", f"SELECT count(*) FROM {O} WHERE status IS NOT NULL"),
    ("ilike", f"SELECT full_name FROM {C} WHERE full_name ILIKE 'a%'"),
    ("scalar-subquery", f"SELECT order_id, total_amount - (SELECT avg(total_amount) FROM {O}) FROM {O}"),
    (
        "cast",
        f"SELECT CAST(total_amount AS NUMERIC(10, 2)), order_date::text FROM {O}",
    ),
    ("cast-int", f"SELECT order_id::bigint, total_amount::double precision FROM {O}"),
    ("like-percent", f"SELECT full_name FROM {C} WHERE full_name LIKE 'A%'"),
    ("modulo", f"SELECT order_id % 2 FROM {O}"),
    ("distinct", f"SELECT DISTINCT status FROM {O}"),
    ("order-by-expression", f"SELECT status FROM {O} ORDER BY length(status) DESC, status"),
    ("boolean-aggregate", f"SELECT bool_and(total_amount > 0) FROM {O}"),
    ("stddev", f"SELECT stddev(total_amount), variance(total_amount) FROM {O}"),
]  # fmt: skip
