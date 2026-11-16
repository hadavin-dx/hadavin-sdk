"""Spike allowlists (hand-written for the spike; derived by a tool from the gold set in phase P2).

Everything here is a positive list: a relation, column, function or cast target that is not listed is rejected.
`db/verify_checks.sql` holds the same view and column list; a test keeps the two equal.
"""

from __future__ import annotations

import json
from pathlib import Path

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
        "date_trunc", "date_part", "age", "extract", "make_date", "to_char",
        # math
        "abs", "round", "ceil", "floor", "greatest", "least", "nullif", "power", "sqrt", "coalesce",
        # string
        "lower", "upper", "length", "concat", "strpos", "position", "replace", "substring", "trim", "ltrim", "rtrim", "left", "right",
        # window
        "row_number", "rank", "dense_rank", "lag", "lead", "first_value", "last_value", "ntile",
    }
)  # fmt: skip

# Argument counts (min, max; None = no upper limit) for the allowlisted functions written with commas. Syntax forms
# (EXTRACT ... FROM, SUBSTRING ... FROM, TRIM(BOTH ...), POSITION(... IN ...)) are not in this table.
ARITY: dict[str, tuple[int, int | None]] = {
    **dict.fromkeys(
        ("count", "sum", "avg", "min", "max", "bool_and", "bool_or", "stddev", "variance", "stddev_samp", "var_samp",
         "percentile_cont", "abs", "ceil", "floor", "sqrt", "lower", "upper", "length", "first_value", "last_value",
         "ntile"),
        (1, 1),
    ),
    **dict.fromkeys(("nullif", "power", "strpos", "to_char", "left", "right", "date_part"), (2, 2)),
    **dict.fromkeys(("row_number", "rank", "dense_rank"), (0, 0)),
    **dict.fromkeys(("greatest", "least", "coalesce", "concat"), (1, None)),
    "date_trunc": (2, 3), "age": (1, 2), "make_date": (3, 3), "round": (1, 2), "replace": (3, 3),
    "ltrim": (1, 2), "rtrim": (1, 2), "lag": (1, 3), "lead": (1, 3),
}  # fmt: skip

# The Lumen Goods catalog (the gold set's seven exposed views), read from the dataset contract so the two cannot drift.
LUMEN_VIEWS: dict[str, tuple[str, ...]] = {
    view: tuple(cols)
    for view, cols in json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "dataset_contract.json").read_text(
            encoding="utf-8"
        )
    )["contract"]["views"].items()
}

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

# Fields EXTRACT(<field> FROM x) may name.
EXTRACT_FIELDS: frozenset[str] = frozenset(
    {
        "year",
        "quarter",
        "month",
        "week",
        "day",
        "dow",
        "doy",
        "isodow",
        "isoyear",
        "hour",
        "minute",
        "second",
        "epoch",
    }
)

# Units date_trunc(<unit>, x) may name.
TRUNC_UNITS: frozenset[str] = frozenset(
    {
        "second",
        "minute",
        "hour",
        "day",
        "week",
        "month",
        "quarter",
        "year",
        "decade",
        "century",
        "millennium",
    }
)
