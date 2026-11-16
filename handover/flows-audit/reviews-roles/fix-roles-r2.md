# fix-roles-r2

NOT DONE / UNCERTAIN (first)
- Nothing run on Postgres; all Postgres facts and SQLSTATE codes UNVERIFIED (manual unreachable, no database).
- Not done: SQL kept inside ROLES-PROPOSAL.md instead of a separate .sql file (brief said edit only that file); protection = DO-block paste guard + NOT BEFORE THE VIDEO banners. Guard syntax itself untested.
- Not re-checked: film-v5 vs real-v5 identical (claim removed from text; script runs on both).
- No review of this version.

DONE
- Security: reorder (additive part A, flows switched and tested, then part B removal window with re-grant rollback, called downtime); banner vs section 7 (never before video; after with owner yes + backup + group L; administrator runs by hand); matrix recipes (SET col = DEFAULT WHERE false; has_column_privilege for I cells of sub/recover/alert; positive controls defined); SQLSTATE per row; nits (schema owner, default privileges, group membership stop, REVOKE CREATE on schema, pg_catalog, VALID UNTIL open sessions, pooling in C6).
- Coverage script: handover/flows-audit/roles-coverage-check/check_grants_cover_queries.py. Run: 28 nodes covered, exit 0; with claim_token removed from recover SELECT: ClaimStuck UNCOVERED, exit 1.
- Reader: danger sentence first, owner box, jargon explained in section 0, overclaims softened, test ids renamed (L, MX, FW, C, WS), "alert claim" named, estimate in hours.
