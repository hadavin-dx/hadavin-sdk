"""The spike corpus: attacks (each tagged with the rule that must reject it) and benign statements."""

# ruff: noqa: S608, ISC004  # SQL text is the test data; implicit concatenation keeps long statements readable

NUL = chr(0)
BACKSLASH = chr(92)
ESC = chr(27)


def _nested(depth: int) -> str:
    sql = "SELECT order_id FROM analytics.orders_v"
    for i in range(depth):
        sql = f"SELECT order_id FROM ({sql}) t{i}"
    return sql


# (name, sql, rule id)
ATTACKS: list[tuple[str, str, str]] = [
    ("stacked-delete", "SELECT 1; DELETE FROM shop.orders", "V01"),
    ("stacked-after-comment", "SELECT 1 /* x */ ; DELETE FROM shop.orders", "V01"),
    ("insert", "INSERT INTO shop.orders VALUES (1, 1, DATE '2026-01-01', 'paid', 1)", "V03"),
    ("update", "UPDATE shop.orders SET status = 'x'", "V03"),
    ("delete", "DELETE FROM shop.orders", "V03"),
    ("drop", "DROP TABLE shop.orders", "V03"),
    ("truncate", "TRUNCATE shop.orders", "V03"),
    ("copy-program", "COPY (SELECT 1) TO PROGRAM 'echo x'", "V03"),
    ("set-role", "SET ROLE postgres", "V03"),
    ("explain-analyze", "EXPLAIN ANALYZE SELECT 1", "V03"),
    ("select-into", "SELECT 1 INTO scratch_t", "V03"),
    ("for-update", "SELECT * FROM analytics.orders_v FOR UPDATE", "V03"),
    (
        "data-modifying-cte",
        "WITH d AS (DELETE FROM shop.orders RETURNING *) SELECT * FROM d",
        "V03",
    ),
    ("restricted-column", "SELECT email FROM analytics.customers_v", "V05"),
    ("whole-row-alias", "SELECT o FROM analytics.orders_v o", "V05"),
    ("base-table", "SELECT * FROM shop.customers", "V04"),
    ("catalog-table", "SELECT * FROM pg_shadow", "V04"),
    ("table-function", "SELECT * FROM generate_series(1, 10)", "V04"),
    ("pg-sleep", "SELECT pg_sleep(10)", "V06"),
    ("version", "SELECT version()", "V06"),
    ("current-date", "SELECT current_date", "V06"),
    ("regclass-cast", "SELECT 'pg_shadow'::regclass", "V07"),
    (
        "with-recursive",
        "WITH RECURSIVE r AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM r) SELECT * FROM r",
        "V08",
    ),
    ("cross-join", "SELECT 1 FROM analytics.orders_v CROSS JOIN analytics.customers_v", "V08"),
    ("nul-byte", "SELECT 1 AS " + NUL, "V09"),
    ("backslash-literal", "SELECT 'a" + BACKSLASH + "' FROM analytics.orders_v", "V09"),
    ("dollar-quote", "SELECT $$x$$", "V09"),
    ("escape-prefix", "SELECT E'abc'", "V09"),
    ("unicode-lookalike", "SELECT customer_" + chr(0x0456) + "d FROM analytics.orders_v", "V09"),
    ("terminal-escape", "SELECT 1 " + ESC + "[2K", "V09"),
    ("parameter", "SELECT * FROM analytics.orders_v WHERE order_id = $1", "V09"),
    ("unterminated-comment", "SELECT 1 /* never closed", "V01"),
    (
        "frame",
        "SELECT sum(total_amount) OVER (ORDER BY order_date ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)"
        " FROM analytics.orders_v",
        "V10",
    ),
    (
        "cte-shadows-catalog",
        "WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles",
        "V04",
    ),
    ("cte-self-read", "WITH x AS (SELECT * FROM x) SELECT * FROM x", "V04"),
    ("regex-operator-on-call", "SELECT 1 FROM analytics.orders_v WHERE LOWER(status) ~ 'a'", "V10"),
    (
        "containment-operator-on-call",
        "SELECT 1 FROM analytics.orders_v WHERE LOWER(status) @> 'a'",
        "V10",
    ),
    ("deep-nesting", _nested(12), "V10"),
    ("upper-quoted-view", 'SELECT * FROM analytics."Orders_V"', "V12"),
]

BENIGN: list[tuple[str, str]] = [
    ("count", "SELECT count(*) FROM analytics.orders_v"),
    (
        "group-by",
        "SELECT category, count(*) AS n FROM analytics.products_v GROUP BY 1 ORDER BY n DESC LIMIT 5",
    ),
    (
        "join",
        "SELECT c.country, count(*) AS orders FROM analytics.orders_v o JOIN analytics.customers_v c"
        " ON c.customer_id = o.customer_id GROUP BY c.country ORDER BY orders DESC",
    ),
    (
        "cte",
        "WITH t AS (SELECT customer_id, sum(total_amount) AS s FROM analytics.orders_v GROUP BY customer_id)"
        " SELECT avg(s) FROM t",
    ),
    (
        "window-rank",
        "SELECT customer_id, rank() OVER (ORDER BY total_amount DESC) AS r FROM analytics.orders_v",
    ),
    (
        "date-trunc",
        "SELECT date_trunc('month', order_date) AS m, sum(total_amount) FROM analytics.orders_v GROUP BY 1",
    ),
    (
        "percentile",
        "SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY total_amount) FROM analytics.orders_v",
    ),
    ("filter", "SELECT count(*) FILTER (WHERE status = 'paid') FROM analytics.orders_v"),
    (
        "case",
        "SELECT CASE WHEN total_amount > 100 THEN 'big' ELSE 'small' END AS size, count(*)"
        " FROM analytics.orders_v GROUP BY 1",
    ),
    ("time-zone", "SELECT order_date AT TIME ZONE 'UTC' FROM analytics.orders_v"),
    (
        "literals-with-comment-markers",
        "SELECT 'a--b', 'c/*d*/' FROM analytics.orders_v -- real comment",
    ),
    ("star", "SELECT * FROM analytics.customers_v"),
    ("union", "SELECT 1 AS a UNION ALL SELECT 2"),
    ("interval", "SELECT order_date + INTERVAL '7 days' FROM analytics.orders_v"),
    (
        "exists",
        "SELECT 1 FROM analytics.orders_v o WHERE EXISTS"
        " (SELECT 1 FROM analytics.customers_v c WHERE c.customer_id = o.customer_id)",
    ),
    (
        "cast",
        "SELECT CAST(total_amount AS NUMERIC(10, 2)), order_date::text FROM analytics.orders_v",
    ),
    ("like-percent", "SELECT full_name FROM analytics.customers_v WHERE full_name LIKE 'A%'"),
]
