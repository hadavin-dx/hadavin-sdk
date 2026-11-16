#!/bin/bash
# v9 re-run: PGSOCK=<dir of the scratch server socket> PGPORT=<port> bash run-v9.sh  (same sections a to k as run.sh, plus l, m, n)
# Needs a throwaway Postgres 13+ server YOU started: local socket = trust, host 127.0.0.1 = scram-sha-256 (password login); made-up data only. Writes only to mktemp dirs, removes them at the end.
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d); trap 'rm -rf "$S"' EXIT
P="psql -X -q -h $PGSOCK -p $PGPORT -U postgres"
$P -d postgres -c "DROP DATABASE IF EXISTS take_db" -c "DROP DATABASE IF EXISTS n8n_db" -c "DROP ROLE IF EXISTS own_t" -c "DROP ROLE IF EXISTS cnt_t" -c "CREATE ROLE own_t LOGIN SUPERUSER PASSWORD 'madeup-own'" -c "CREATE ROLE cnt_t LOGIN PASSWORD 'madeup-cnt'" -c "CREATE DATABASE take_db" -c "CREATE DATABASE n8n_db" 2>&1 | grep -v NOTICE
seed() { $P -d $1 -c "DROP SCHEMA IF EXISTS app CASCADE" -c "CREATE SCHEMA app" -c "CREATE TABLE app.mf_leads(lead_key text PRIMARY KEY, state text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')), crm_id text, created_at timestamptz NOT NULL DEFAULT now())" -c "INSERT INTO app.mf_leads(lead_key,state,crm_id) VALUES ('made-up-1','done','101'),('made-up-2','unknown',NULL),('made-up-3','done',''),(E'made-up-line\nbreak','done','104')" -c "GRANT USAGE ON SCHEMA app TO cnt_t" -c "GRANT SELECT ON app.mf_leads TO cnt_t" >/dev/null 2>&1; }
cnt() { $P -d take_db -At -c 'select count(*) from app.mf_leads'; }
export PGPASSFILE=$S/pgpass; umask 077; printf '127.0.0.1:%s:*:own_t:madeup-own\n127.0.0.1:%s:*:cnt_t:madeup-cnt\n' $PGPORT $PGPORT > $PGPASSFILE; chmod 600 $PGPASSFILE
export PGURL="postgresql://own_t@127.0.0.1:$PGPORT/take_db" COUNTURL="postgresql://cnt_t@127.0.0.1:$PGPORT/take_db" SCHEMA=app TAKE_DB_NAME=take_db
FW=$S/fakewc; mkdir $FW; printf '#!/bin/sh\nsleep ${FAKE_WC_SLEEP:-0}\nif [ -n "$FAKE_WC_LIE" ]; then echo $FAKE_WC_LIE; else exec /usr/bin/wc "$@"; fi\n' > $FW/wc; chmod +x $FW/wc
paste_run() { ( bash $H/10b-clean-start.sh 2>&1 ); }   # the paste, verbatim
sha() { sha256sum "$1" | cut -c1-12; }
seed take_db; seed n8n_db
echo "=== a. WRONG database (PGURL points at n8n_db, expected take_db): must STOP, rows stay 4, no OUT file"
OUT=$S/a.out; ( PGURL="postgresql://own_t@127.0.0.1:$PGPORT/n8n_db" OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT exists: $([ -e $OUT ] && echo yes || echo no)"
echo "=== b. export line count cannot match (a fake wc says 99): must STOP, rows stay 4; the half-failed attempt leaves OUT behind"
OUT=$S/list.tsv; ( PATH=$FW:$PATH FAKE_WC_LIE=99 OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT exists: $([ -e $OUT ] && echo yes || echo no) lines: $(wc -l < $OUT)"
echo "=== c. second run on the same OUT: must STOP at the guard, nothing changed"
h1=$(sha $OUT); ( OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT sha $h1 -> $(sha $OUT)"
echo "=== d. recovery for b/c (table still has rows, OUT is from a failed attempt): move OUT aside with mv, run again"
mv $OUT $OUT.attempt1; ( OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT lines: $(wc -l < $OUT)  aside kept: $([ -e $OUT.attempt1 ] && echo yes || echo no)"
echo "--- OUT content (the key with a line break stays on ONE line):"; cat $OUT
echo "=== e1. copy OUT somewhere safe (exact line of step 4b)"
copy_line() { if [ -e "$OUT_COPY" ] || [ -L "$OUT_COPY" ]; then echo "OUT_COPY exists: STOP, nothing copied"; else cp "$OUT" "$OUT_COPY" && cmp "$OUT" "$OUT_COPY" && echo "copy ok"; fi; }
OUT_COPY=$S/safe-place.tsv; copy_line
echo "=== e2. the same line a second time refuses to overwrite the copy"
copy_line
cp $OUT $S/list.keep
echo "=== f. OLD v7 paste (no guard) on the same OUT, table now empty: this is finding V7-1"
( PGURL="$PGURL" OUT=$OUT bash $H/10b-clean-start-v7.sh 2>&1 | grep -v "^#" ); echo "OUT lines now: $(wc -l < $OUT)  sha $(sha $OUT) (was $(sha $S/list.keep)): THE LIST IS GONE"
cp $S/list.keep $OUT
echo "=== g. NEW v8 paste, table has 1 new row, same OUT: must STOP at the guard; list intact"
$P -d take_db -c "INSERT INTO app.mf_leads(lead_key) VALUES ('made-up-new')"; ( OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT sha $(sha $OUT) (kept list: $(sha $S/list.keep))"
echo "=== h. interrupted attempt: psql killed (kill -9) after the file was written, before COMMIT"
seed take_db; OUT=$S/int.tsv
( PATH=$FW:$PATH FAKE_WC_SLEEP=6 OUT=$OUT paste_run ) > $S/int.log 2>&1 &
for i in $(seq 1 30); do [ -s $OUT ] && break; sleep 0.3; done
pkill -9 -f "psql postgresql://own_t@127.0.0.1:$PGPORT/take_db -X -w" ; wait
echo "rows now: $(cnt) (killed run rolled back)  OUT lines: $(wc -l < $OUT)  lock left behind: $($P -d take_db -At -c "select count(*) from pg_locks l join pg_class c on c.oid=l.relation where c.relname='mf_leads' and l.granted and l.mode='AccessExclusiveLock'")"
echo "--- rerun on the same OUT stops; recovery by mv; run again:"
( OUT=$OUT paste_run ); mv $OUT $OUT.attempt1; ( OUT=$OUT paste_run ); echo "rows now: $(cnt)  OUT lines: $(wc -l < $OUT)"
echo "=== i. password file: wrong password in the file, then file mode 644 (psql ignores such a file); both must STOP with no prompt, rows stay"
seed take_db
OUT=$S/pw1.tsv; ( PGPASSFILE=$S/badpass; printf '127.0.0.1:%s:*:own_t:wrong\n' $PGPORT > $S/badpass; chmod 600 $S/badpass; export PGPASSFILE; OUT=$OUT paste_run </dev/null ); echo "rows now: $(cnt) OUT exists: $([ -e $OUT ] && echo yes || echo no)"
OUT=$S/pw2.tsv; cp $PGPASSFILE $S/loose; chmod 644 $S/loose; ( PGPASSFILE=$S/loose OUT=$OUT paste_run </dev/null ); echo "rows now: $(cnt) OUT exists: $([ -e $OUT ] && echo yes || echo no)"
echo "=== j. step 2 (state of the prep record) and step 5 (count) as the read-only role"
step2() { psql "$COUNTURL" -X -w -At -v ON_ERROR_STOP=1 -v k="$PREP_KEY" -v tbl="$SCHEMA.mf_leads" <<'SQL'
SELECT state FROM :tbl WHERE lead_key = :'k';
SQL
}
step5() { psql "$COUNTURL" -X -w -At -v ON_ERROR_STOP=1 -v tbl="$SCHEMA.mf_leads" <<'SQL'
SELECT count(*) FROM :tbl;
SQL
}
PREP_KEY=made-up-2; echo "step 2, key made-up-2 (state unknown): $(step2)"
PREP_KEY=made-up-1; echo "step 2, key made-up-1 (state done): $(step2)"
PREP_KEY='made-up-no-such'; echo "step 2, key not stored: [$(step2)] (empty = no such row)"
PREP_KEY="it's-a-quote"; echo "step 2, key with a quote char: [$(step2)] (no error, the quote was passed as data)"
echo "step 5 before the paste: $(step5)"
OUT=$S/k.tsv; ( OUT=$OUT paste_run ) | tail -n 2; echo "step 5 after the paste: $(step5)"
echo "step 5 with the count role cannot empty the table: $(psql "$COUNTURL" -X -w -At -c 'TRUNCATE app.mf_leads' 2>&1 | head -n 1)"
echo "=== k. step 3 check: nothing answers on the health address (curl prints 000)"
python3 -I -m http.server 55499 --bind 127.0.0.1 >/dev/null 2>&1 & SP=$!; sleep 1
echo "server up   : $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:55499/ ; echo " curl exit=$?")"
kill $SP; wait $SP 2>/dev/null; sleep 0.5
echo "server down : $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:55499/ ; echo " curl exit=$?")"
echo "=== l. step 2 (v9): fresh prep key, state read BEFORE sending must be an empty line; a leftover row with the same key gives a false pass"
seed take_db
before() { psql "$COUNTURL" -X -w -At -v ON_ERROR_STOP=1 -v k="$PREP_KEY" -v tbl="$SCHEMA.mf_leads" <<'SQL'
SELECT state FROM :tbl WHERE lead_key = :'k';
SQL
}
PREP_KEY="made-up-prep-$(date -u +%Y%m%d%H%M%S)"; B=$(before); echo "fresh key $PREP_KEY: rc=$? before=[$B] (pass: empty)"
PREP_KEY=made-up-1; B=$(before); echo "leftover key made-up-1: rc=$? before=[$B] (not empty = STOP, take a new key)"
echo "--- why: the stored row wins (ON CONFLICT DO NOTHING, as in mf-form.json), so a resend of a used key never changes the state and the read after sending would show the OLD 'done':"
$P -d take_db -c "INSERT INTO app.mf_leads(lead_key,state) VALUES ('made-up-1','new') ON CONFLICT (lead_key) DO NOTHING" ; echo "state after the (ignored) resend: [$(PREP_KEY=made-up-1 before)]  <- false pass if step 2a were skipped"
PREP_KEY=made-up-new-key; $P -d take_db -c "INSERT INTO app.mf_leads(lead_key,state) VALUES ('made-up-new-key','new') ON CONFLICT (lead_key) DO NOTHING"; echo "fresh key after sending: [$(before)] (new = not final, wait)"
$P -d take_db -c "UPDATE app.mf_leads SET state='done' WHERE lead_key='made-up-new-key'"; echo "fresh key after processing: [$(before)] (done = pass)"
echo "=== m. step 6 (v9): deletion list = union of OUT and every OUT.attemptN, duplicates removed; split case"
dl() { if [ -e "$OUT.deletion-list" ] || [ -L "$OUT.deletion-list" ]; then echo "deletion-list exists: STOP"; else cat "$OUT" "$OUT".attempt* 2>/dev/null | LC_ALL=C sort -u > "$OUT.deletion-list"; wc -l < "$OUT.deletion-list"; fi; }
OUT=$S/split.tsv; printf 'k-a\t11\nk-b\t\nk-c\t\\N\n' > $OUT.attempt1; printf 'k-c\t\\N\nk-d\t14\nk-line\\nbreak\t15\n' > $OUT; printf 'k-e\t16\nk-a\t11\n' > $OUT.attempt2
echo "OUT has $(wc -l < $OUT) lines, attempt1 $(wc -l < $OUT.attempt1), attempt2 $(wc -l < $OUT.attempt2); union (5 distinct + 1 line-break key = 6 expected: a b c d line e):"; echo "lines in deletion list: $(dl)"; cat $OUT.deletion-list
echo "second run refuses:"; dl
echo "--- no attempt files at all, OUT only:"; OUT=$S/only.tsv; printf 'k-x\t1\n' > $OUT; echo "lines: $(dl)"
echo "=== n. real recovery path of test h then step 6: killed run leaves OUT; mv to OUT.attempt1; rerun; union must hold all 4 rows"
seed take_db; OUT=$S/rec.tsv
( PATH=$FW:$PATH FAKE_WC_SLEEP=6 OUT=$OUT paste_run ) > $S/rec.log 2>&1 &
for i in $(seq 1 30); do [ -s $OUT ] && break; sleep 0.3; done
pkill -9 -f "psql postgresql://own_t@127.0.0.1:$PGPORT/take_db -X -w" ; wait
mv $OUT $OUT.attempt1; ( OUT=$OUT paste_run ) | tail -n 2; echo "OUT lines: $(wc -l < $OUT) attempt1 lines: $(wc -l < $OUT.attempt1); count now $(cnt)"; echo "lines in deletion list: $(dl) (expected 4)"
