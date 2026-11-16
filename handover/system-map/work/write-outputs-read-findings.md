# Review of write_outputs.py row-id fix (reader aca5d23c320685334, read-only, ran no code). UNVERIFIED by running.
B4-1 MAJOR write_outputs.py ~129-175: verdict tables still bound to the number inside the id, not to the row. If work/L6.md is renumbered or a row inserted, tables silently give verdicts to the wrong row, exit 0. Stale check only catches deleted ids. Fix: move PIN (id -> name) into the tool and exit when rows[id][1] differs; or key tables by (id, name prefix).
B4-2 MAJOR tests/test_write_outputs_guard.py ~146-160: test 2 (line order) cannot fail on the old code (ids travel with content). Rename it "line order does not change the output"; add a real renumbering test expecting an error (needs B4-1).
B4-3 MINOR test 3 (~162-172): on the OLD code a deleted mid row trips an AssertionError without the text "stale job row ids", so assertIn fails there: test is fine but the claim "passes on old code" in our notes is wrong. Correct the record; add a mid-row deletion case.
B4-4 MINOR write_outputs.py ~202: L6-J-043 special case is in no table, not in PIN, not in the stale check. Add to the stale check and PIN (a SPECIAL set).
B4-5 MINOR ~175-178: an unlisted new row is accepted silently (old code failed loudly on row 060). Exit for any id not in PIN or a registered set.
B4-6 NIT ~120: assert stripped under python -O; use sys.exit(...).
B4-7 NIT tests lines 7,102,112 refer to old line numbers; use table names.
B4-8 NIT test 1 (126-144): assert the swap happened (L6-J-001 under the LOG block, row count unchanged).
B4-9 NIT ~140,286,302,308 "Fix plan row 1, 2 or 7" positions hardcoded; generate from the fixrows list.
Not checked by the reader: never ran the tool or tests; did not diff the generated SWEEP.md / ONE-PLACE-TABLE.md.
