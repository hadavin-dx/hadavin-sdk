#!/bin/bash
# v10: bash snippet-run-v10.sh. Cuts the fenced sh snippets of steps 2a, 2c, 4b and 6 out of plan-v10-real-v5-edits.md BY THEIR TEXT (python), writes each to a file and runs that file UNCHANGED (bash file) against a mock psql (a script that only answers the state query from a made-up table file and logs its arguments and the SQL it was given). Made-up data only, mktemp dir.
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d); trap 'rm -rf "$S"' EXIT
python3 -I - "$H/plan-v10-real-v5-edits.md" "$S" <<'PY'
import re,sys
md=open(sys.argv[1]).read(); out=sys.argv[2]
new=md[md.index("## 10b. Before the take"):]
def snip(marker, must):
    i=new.index(marker); m=re.search(r"```sh\n(.*?)\n```",new[i:],re.S); t=m.group(1)
    assert must in t,(marker,must); return t
open(out+"/s2a.sh","w").write(snip("**2a. Fresh key","PREP_KEY=")+"\n")
open(out+"/s2c.sh","w").write(snip("**2c. Read the state again","SELECT state")+"\n")
open(out+"/s4b.sh","w").write(snip("**4b. Copy","mkdir")+"\n")
open(out+"/s6.sh","w").write(snip("**The deletion list is the union","sort -u")+"\n")
print("extracted 4 snippets from the plan text")
PY
# 4b: the line must equal the function line used in clean-start-test/copy-test-v10.sh
L=$(grep '^copy_line()' $H/clean-start-test/copy-test-v10.sh | sed 's/^copy_line() { //; s/; }$//'); [ "$L" = "$(cat $S/s4b.sh)" ] && echo "4b snippet in the plan == line tested in copy-test-v10.sh: identical" || echo "4b snippet DIFFERS from the tested line: STOP"
# mock psql
mkdir $S/bin; cat > $S/bin/psql <<'MOCK'
#!/bin/bash
# mock: records args and SQL; answers the state query from $MOCK_TABLE (key<TAB>state); MOCK_FAIL=1 simulates a login failure
echo "mock psql args: $*" >> $MOCK_LOG; sql=$(cat); echo "mock psql sql: $sql" >> $MOCK_LOG
[ -n "$MOCK_FAIL" ] && { echo "psql: error: connection failed" >&2; exit 2; }
k=; while [ $# -gt 0 ]; do case "$1" in -v) shift; case "$1" in k=*) k=${1#k=};; esac;; esac; shift; done
[ -n "$MOCK_ALL" ] && { echo "$MOCK_ALL"; exit 0; }
awk -F'\t' -v k="$k" '$1==k{print $2}' $MOCK_TABLE
MOCK
chmod +x $S/bin/psql
export PATH=$S/bin:$PATH MOCK_LOG=$S/log MOCK_TABLE=$S/table COUNTURL=postgresql://cnt_t@127.0.0.1:1/take_db SCHEMA=app PGPASSFILE=$S/pgpass; : > $MOCK_LOG
printf 'made-up-old\tdone\n' > $MOCK_TABLE
echo "=== 2a fresh key (expect: rc=0 key=made-up-prep-<utc time> before=[])"; bash $S/s2a.sh
echo "=== 2a key already used (mock answers done for any key; expect before=[done]: a person must take a new key)"; MOCK_ALL=done bash $S/s2a.sh
echo "=== 2a login fails (expect an error line and rc not 0, before=[])"; MOCK_FAIL=1 bash $S/s2a.sh
echo "=== 2c state read for a key that is stored as processing, then done"
export PREP_KEY=made-up-prep-1; printf 'made-up-prep-1\tprocessing\n' >> $MOCK_TABLE; echo "2c prints: [$(bash $S/s2c.sh)] (expect processing)"
printf 'made-up-prep-1\tdone\n' > $MOCK_TABLE; echo "2c prints: [$(bash $S/s2c.sh)] (expect done)"
printf 'x\tdone\n' > $MOCK_TABLE; echo "2c prints: [$(bash $S/s2c.sh)] (expect empty line: no such row)"
echo "=== what the mock was given (arguments and SQL of the first 2a call and the 2c calls): the key is passed as -v k=..., never inside the SQL text"
grep -m3 "mock psql" $MOCK_LOG | cut -c1-230; grep -c "made-up-prep-1" $MOCK_LOG | sed 's/^/lines of the log holding the key text (expect 3: the three argument lines): /'; grep "mock psql sql" $MOCK_LOG | grep -c "made-up-prep" | sed 's/^/sql lines holding a key: /'
echo "=== 6 deletion list (split case, same files as section m of the clean-start test; expect 6 lines, then a refusal)"
OUT=$S/split.tsv; printf 'k-a\t11\nk-b\t\nk-c\t\\N\n' > $OUT.attempt1; printf 'k-c\t\\N\nk-d\t14\nk-line\\nbreak\t15\n' > $OUT; printf 'k-e\t16\nk-a\t11\n' > $OUT.attempt2; export OUT
echo "step 6 prints: $(bash $S/s6.sh) (expect 6)"; echo "second run: $(bash $S/s6.sh) (expect: deletion-list exists: STOP)"
echo "=== 6 OUT only"; OUT=$S/only.tsv; printf 'k-x\t1\n' > $OUT; export OUT; echo "step 6 prints: $(bash $S/s6.sh) (expect 1)"
echo "=== 4b run from the extracted plan snippet (OUT with two attempt files; expect copy ok: 3 files)"
OUT=$S/c.tsv; export OUT OUT_COPY=$S/safe; printf 'a\t1\n' > $OUT; echo b > $OUT.attempt1; echo c > $OUT.attempt2; bash $S/s4b.sh; bash $S/s4b.sh
