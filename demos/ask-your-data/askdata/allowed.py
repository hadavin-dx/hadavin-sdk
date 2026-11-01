"""Spike allowlists (hand-written for the spike; derived by a tool from the gold set in phase P2).

Everything here is a positive list: a relation, column, function or cast target that is not listed is rejected.
`db/verify_checks.sql` holds the same view and column list; a test keeps the two equal.
"""

from __future__ import annotations

SCHEMA = "analytics"

# exposed view -> its columns (no email column anywhere)
VIEWS: dict[str, tuple[str, ...]] = {
    "customers_v": ("customer_id", "full_name", "country", "signup_date"),
    "products_v": ("product_id", "product_name", "category", "unit_price"),
    "orders_v": ("order_id", "customer_id", "order_date", "status", "total_amount"),
    "order_items_v": (
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
        "line_amount",
    ),
}

# Function names as the Postgres generator prints them (lower case). Typed sqlglot nodes are checked by the
# name they generate, not by the class they parse to; every anonymous (unknown) function is rejected.
FUNCTIONS: frozenset[str] = frozenset(
    {
        # aggregates
        "count", "sum", "avg", "min", "max", "bool_and", "bool_or", "stddev", "variance", "stddev_samp", "var_samp",
        "percentile_cont",
        # date
        "date_trunc", "date_part", "age", "extract",
        # math
        "abs", "round", "ceil", "floor", "greatest", "least", "nullif", "power", "sqrt", "coalesce",
        # string
        "lower", "upper", "length", "concat", "strpos", "replace", "substring", "trim", "ltrim", "rtrim",
        # window
        "row_number", "rank", "dense_rank", "lag", "lead", "first_value", "last_value", "ntile",
    }
)  # fmt: skip

# Constructs that look like functions in the tree but are syntax (checked by node class in validate.py).
SYNTAX_FUNCTIONS: frozenset[str] = frozenset({"Cast", "Case", "If", "Exists"})

# sqlglot DataType.Type member names that a cast may target.
CAST_TARGETS: frozenset[str] = frozenset(
    {"DATE", "TIMESTAMP", "TIMESTAMPTZ", "SMALLINT", "INT", "BIGINT", "DECIMAL", "DOUBLE", "TEXT",
     "VARCHAR", "BOOLEAN"}
)  # fmt: skip

# Units allowed in INTERVAL '<n> <unit>'.
INTERVAL_UNITS: frozenset[str] = frozenset(
    {"day", "days", "week", "weeks", "month", "months", "year", "years"}
)
