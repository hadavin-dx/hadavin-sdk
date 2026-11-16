# Lead fill-ins before running (UNVERIFIED 15): TAKE_DB_NAME, SCHEMA, PGURL (owner or superuser login to the take's database), OUT (export file, outside any repo).
# Stop n8n (or deactivate every flow) first, so no row can arrive while this runs. The LOCK below is a second guard, not a replacement.
export OUT
psql "$PGURL" -X -q -v ON_ERROR_STOP=1 -v want="$TAKE_DB_NAME" -v tbl="$SCHEMA.mf_leads" -v out="$OUT" <<'SQL'
SELECT current_database() = :'want' AS db_ok \gset
\if :db_ok
\else
  \echo WRONG DATABASE: current_database() is not the expected name. STOP, nothing was changed.
  SELECT 1/0 AS wrong_database_stop;
\endif
BEGIN;
LOCK TABLE :tbl IN ACCESS EXCLUSIVE MODE;
SELECT count(*) AS n FROM :tbl \gset
\echo rows before: :n
\copy :tbl (lead_key, crm_id) TO :'out'
\set lines `wc -l < "$OUT"`
SELECT (:lines = :n) AS export_ok \gset
\if :export_ok
  TRUNCATE :tbl;
  SELECT count(*) AS n_after FROM :tbl \gset
  SELECT (:n_after = 0) AS empty_ok \gset
  \if :empty_ok
    COMMIT;
    \echo OK: exported :n rows to the file, table emptied, count now :n_after
  \else
    ROLLBACK;
    \echo COUNT AFTER TRUNCATE IS NOT 0. STOP, rolled back.
    SELECT 1/0 AS not_empty_stop;
  \endif
\else
  ROLLBACK;
  \echo EXPORT LINE COUNT (:lines) DOES NOT MATCH ROW COUNT (:n). STOP, nothing was emptied.
  SELECT 1/0 AS export_mismatch_stop;
\endif
SQL
echo "psql rc=$?"
