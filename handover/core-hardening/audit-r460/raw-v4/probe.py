import sys; sys.path.insert(0, sys.argv[2])
import sys, json
from hadavin_sdk.approvals.gate import withhold_commands, WITHHELD
from hadavin_sdk.approvals.channel import clean
# (id, text, v4 claim on old code: "shown"/"withheld"/"candidate-untraced", section)
E = []
def a(i, t, c, s): E.append((i, t, c, s))
# 4.9 twelve G3 lines (v4 table 'Line' column); claim from F2/G3 row: lowercase SQL is shown today
for i, t in enumerate(["drop table users;", "`drop table users`", "delete from users where id = 1",
    "update only t as a set x=1", "insert into t values (1)", "$ drop table users", "drop table pressure",
    "we should delete from the queue only after a fix", "update its set of rules",
    "delete from the queue where possible", "drop table users", "we will drop table pressure; then rest"], 1):
    a(f"G3-{i:02d}", t, "shown", "4.9 G3 line")
a("G3-UP-1", "UPDATE t AS a SET x=1", "shown", "4.9 alias gap (leaks)")
a("G3-UP-2", "UPDATE ONLY t SET x=1", "shown", "4.9 alias gap (leaks)")
a("G3-UP-0", "UPDATE t SET x=1", "withheld", "4.9 upper-case control")
a("G3-UC-1", "DROP TABLE users", "withheld", "4.9 upper-case unchanged")
a("G3-UC-2", "DELETE FROM users WHERE id = 1", "withheld", "4.9 upper-case unchanged")
a("G2a-W", "kubectl \\\ndelete ns prod", "shown", "G2a (leaks)")
a("G2a-W-caret", "kubectl ^\ndelete ns prod", "shown", "G2a variant (extra, not in v4 table)")
a("G2a-W-tick", "kubectl `\ndelete ns prod", "shown", "G2a variant (extra, not in v4 table)")
a("G2a-S", "we wrap lines with a backslash \\\nlike this", "shown", "G2a shown example")
a("G2b-W", "kubectl > /dev/null delete pod x", "shown", "G2b (leaks)")
a("G2b-v3", "> /dev/null kubectl delete pod x", "withheld", "v3 example; v4 says NOT the real bypass")
a("G2b-S", "the aws Lambda runtime", "shown", "G2b/pinned shown")
a("G2c-W", "KUBECTL.EXE delete ns prod", "candidate-untraced", "G2c (candidate)")
a("G2c-S", "the tf module was reviewed", "shown", "G2c shown")
a("G4a-W", "rm -v -rf /x", "shown", "G4a (leaks)")
a("G4a-S", "rm the file", "shown", "G4a/pinned shown")
a("G5a-W", "aws secretsmanager get-secret-value --secret-id x", "shown", "G5a (leaks)")
a("G5a-S", "aws s3 ls", "shown", "G5a shown")
a("G5b-W", "git rebase -i HEAD~3", "candidate-untraced", "G5b (candidate)")
a("G5b-S", "the docker image was rebuilt overnight", "shown", "G5b/pinned shown")
a("PIN-kubectl", "a 'kubectl rollout restart' replaced the pods", "shown", "4.9 pinned shown")
a("T98", "update its set of rules", "shown", "tests/test_g4_parity.py:98")
a("T221", "we should delete from the queue only after a fix", "shown", "tests/test_g4_parity.py:221")
a("T222", "drop table pressure", "shown", "tests/test_g4_parity.py:222")
rows = []
for i, t, c, s in E:
    w = withhold_commands(t); cl = clean(t)
    obs = "withheld" if WITHHELD in w else "shown"
    if obs == "shown" and w != t: obs = "CHANGED-BUT-NO-MARKER"
    clobs = "withheld" if WITHHELD in cl else ("shown" if cl == t else "changed")
    ok = "n/a (untraced)" if c.startswith("candidate") else ("yes" if c == obs else "NO")
    rows.append(dict(id=i, text=t, claim=c, obs=obs, wc=w, clean=cl, cleanobs=clobs, match=ok, sect=s))
json.dump(rows, open(sys.argv[1], "w"), indent=1)
for r in rows: print(f"{r['id']:12} claim={r['claim']:20} obs={r['obs']:9} clean={r['cleanobs']:9} match={r['match']}  withhold_commands={r['wc']!r}  clean={r['clean']!r}")
