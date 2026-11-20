# F: static findings on the money definer functions

## F1 (real): unqualified call of hadavin_release_expired_spend
- File: src/hadavin_sdk/store/postgres.py:1002 (`"SELECT * FROM hadavin_release_expired_spend(%s, %s)"`).
- Rule: the store calls every definer function by its schema-qualified name (an unqualified name is looked up in the
  temporary schema first; the same reasoning as `_t` / `_money_call`).
- Proposed fix: build it with `self._money_call("hadavin_release_expired_spend", "%s, %s")` (arguments `(agent_id, day)`).
- Test: tests/test_money_definer_static.py::test_postgres_py_has_no_unqualified_call_of_any_hadavin_function
  (xfail strict=False until fixed; remove the mark then).
