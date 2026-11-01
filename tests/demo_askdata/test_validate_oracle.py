"""T-E4: the Postgres grammar (pglast, CI-only differential oracle) agrees that every accepted statement and its
canonical text is exactly one SELECT. A missing oracle is an ImportError, i.e. a red collection, never a skip."""

import pglast
import pytest
from askdata.validate import validate
from pglast import ast

from .corpus import BENIGN


def test_oracle_is_the_pinned_version():
    assert pglast.__version__.lstrip("v") == "8.7"


@pytest.mark.parametrize(("name", "sql"), BENIGN, ids=[b[0] for b in BENIGN])
def test_oracle_parses_original_and_canonical_to_one_select(name, sql):
    canonical = validate(sql).canonical_sql
    for text in (sql, canonical):
        stmts = pglast.parse_sql(text)
        assert len(stmts) == 1, name
        assert isinstance(stmts[0].stmt, ast.SelectStmt), name


def test_oracle_sees_what_the_validator_rejects():
    for text in ("DELETE FROM shop.orders", "SELECT 1; SELECT 2"):
        stmts = pglast.parse_sql(text)
        assert len(stmts) != 1 or not isinstance(stmts[0].stmt, ast.SelectStmt)


def test_validator_rejects_what_the_oracle_calls_not_a_single_select():
    from askdata.validate import Rejected

    for text in ("DELETE FROM shop.orders", "SELECT 1; SELECT 2"):
        with pytest.raises(Rejected):
            validate(text)
