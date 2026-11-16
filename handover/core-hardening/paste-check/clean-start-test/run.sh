#!/bin/bash
# Re-run: PGSOCK=<dir with the scratch server socket> PGPORT=<port> bash run.sh   (needs a throwaway Postgres 13+ server you started; made-up data only)
H=$(cd "$(dirname "$0")" && pwd); P="psql -X -q -h $PGSOCK -p $PGPORT -U postgres"
$P -d postgres -c "DROP DATABASE IF EXISTS take_db" -c "DROP DATABASE IF EXISTS n8n_db" -c "CREATE DATABASE take_db" -c "CREATE DATABASE n8n_db"
seed() { $P -d $1 -c "DROP SCHEMA IF EXISTS app CASCADE" -c "CREATE SCHEMA app" -c "CREATE TABLE app.mf_leads(lead_key text PRIMARY KEY, crm_id text, created_at timestamptz NOT NULL DEFAULT now())" -c "INSERT INTO app.mf_leads(lead_key,crm_id) VALUES ('made-up-1','101'),('made-up-2',NULL),('made-up-3',''),(E'made-up-line\nbreak','104')"; }
run() { echo "=== $1"; shift; ( export PGURL="postgresql://postgres@127.0.0.1:$PGPORT/$DB" SCHEMA=app; env "$@" bash $H/10b-clean-start.sh 2>&1 | sed "s#$PGSOCK#\$SOCK#g" ); echo "rows now: $($P -d $DB -At -c 'select count(*) from app.mf_leads')"; }
seed take_db >/dev/null; seed n8n_db >/dev/null
DB=n8n_db   run "WRONG database (connected to n8n_db, expected take_db): must STOP, rows stay 4" TAKE_DB_NAME=take_db OUT=$(mktemp)
DB=take_db  run "export file cannot match (OUT=/dev/null): must STOP, rows stay 4" TAKE_DB_NAME=take_db OUT=/dev/null
OUT=$(mktemp)
DB=take_db  run "RIGHT database: export 4 rows, truncate, count 0" TAKE_DB_NAME=take_db OUT=$OUT
echo "--- export file ($(wc -l < $OUT) lines; the key with a line break is escaped on ONE line):"; cat $OUT
# lock proof: a second session inserting while the first holds the lock waits, and its row lands AFTER the truncate
