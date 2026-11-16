# roles-coverage-check

`check_grants_cover_queries.py` reads the flow JSON files and the database-login grants and fails (exit 1, a `FAIL` line each) on: a table other than `mf_leads`, a statement kind other than SELECT/INSERT/UPDATE (DELETE, TRUNCATE, DROP and similar are refused), a column a query needs but no grant gives, a grant wider than the queries need (table-level grant, or a column no query uses: "unused grant"), a login with no grants, a missing folder, an unreadable flow file, a folder with zero Postgres nodes.

Where the grants come from: the script PARSES them from section 4 (part A) of `../ROLES-PROPOSAL.md` (option `--roles-doc PATH` to use another copy). Nothing is copied into the script, so the script and the document cannot differ. A test (`test_script_and_document_cannot_differ`) fails if grants are hardcoded again.

Run: `python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5`
Tests: `python3 -m unittest -v test_check_grants` (set `SCRIPT=<path>` to test another copy of the script).

Limit that stays: it is a text parser, so unusual SQL can slip past it; the database tests are the real proof. The mapping of flow node to login (`NODE_LOGIN`) is still in the script, because the document does not contain it.
