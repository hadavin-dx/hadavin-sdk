# EV7 PLAN: independent evidence run on the r7 patch (EVIDENCE RUNNER brief, directly executable)

Written 2026-11-13 by the AM builder. Copied from what EV6 really ran (`/home/user/build/rr6/out/EV6/`: `EVIDENCE.md`, `run-group.sh`, `run-alone.sh`, `alone-chain.sh`, `run-fb-file.sh`, `run6.sh`, `run-hostile.sh`, `lint.log`, `suppress.txt`). Nothing in this plan was run on r7 (the r7 patch did not exist when this was written). The recipes that WERE run on r6 are marked "ran on r6"; the new scripts of this plan are marked with what was tested.

You are an EVIDENCE RUNNER. You run, measure and save raw output. You never judge ("passed", "ok" only next to the command and its output). Made-up data only, no live service, no spend, loopback only (inside `unshare -n`). Never answer y/yes to any prompt of any script: a prompt means stop and report. Never spawn sub-agents. Stop every process you start. Do not touch `/home/user/build/rr6/tree-R7`, `/home/user/build/rr6/out/R7`, `demo-frozen/repo2` (read-only: `git archive` / `git clone` from it), `tree-EV2.stale-before-run`, or any other existing tree; work only in `tree-EV7`, `tree-old-EV7`, `tree-FB-EV7`, `tmp-EV7`, `out/EV7` (create them). Checkpoint note every 30 minutes to `out/EV7/checkpoint.md` (time, load average, done, next); stop at the time box the lead gave you and report.

Variables used below (set them in every script):

```
R=/home/user/build/rr6; O=$R/out/EV7; T=$R/tree-EV7; PY=$R/venv-br/bin/python
FIX=/home/user/hadavin-sdk/handover/core/fix        # core-fix-on-frozen-r7.patch and core-fix-on-frozen-r7-lf.patch must be here
AM=$R/out/AM                                        # apply_matrix.sh, required_fails.py, this plan
mkdir -p $O $R/tmp-EV7
```

## 0. File layout and the first rule

Everything goes to `$O`. The FIRST section of `$O/EVIDENCE.md` is "NOT RUN / NOT CHECKED". Create it first with the expected gaps (below), and extend it whenever something is skipped, times out, or runs on a different machine state. At the end the first section is the last thing you re-read. A claim with no command and no raw output next to it is not written.

Expected entries (copy, then correct): Windows PowerShell scripts never run (no Windows; line endings and patch application only); no CodeQL / SonarCloud / CodeRabbit / semgrep run; peak memory from `getrusage(RUSAGE_CHILDREN)` in the wrapper (no `/usr/bin/time`, no `ss`: listening sockets read from /proc/net/tcp); NUL byte in an environment value or argument cannot be started by the operating system; other agents' processes on the machine (record `uptime` and the top-5 CPU processes before each heavy step).

Layout:

```
$O/EVIDENCE.md           first section 0 NOT RUN / NOT CHECKED, then 1 APPLY ... 9 (below); raw numbers, no verdicts
$O/checkpoint.md         time-stamped notes with load average
$O/sha256.txt            sha256 of both r7 patches and (if given) the r6->r7 delta
$O/apply/                apply_matrix output (apply-matrix.out, last-matrix.tsv)
$O/groupA.txt groupB.txt full-A.log full-B.log     suite groups and logs
$O/alone/                one log per alone re-run
$O/fb/ fb-passes-on-old.txt fb2/ fb2-passes-on-old.txt required-fails-*.txt   fail-before
$O/lint.log suppress.txt cols.txt bandit.log
$O/hostile/              results*.jsonl, *.out, hostile-table.md
$O/mutants/              mutants.tsv, one log per mutant, mutant-diffs/
```

## 1. Tree setup and head check

```
cd $R
git -C $R/demo-frozen/repo2 rev-parse 'frozen2^{tree}'                    # must print 49d3c85938fe5323a3378a49195d3b8da434b3ca
sha256sum $FIX/core-fix-on-frozen-r7.patch $FIX/core-fix-on-frozen-r7-lf.patch > $O/sha256.txt
rm -rf $T $R/tree-old-EV7; git clone -q --branch frozen2 $R/demo-frozen/repo2 $T       # r7 tree (a clone: has .git, as EV6 did)
git clone -q --branch frozen2 $R/demo-frozen/repo2 $R/tree-old-EV7                      # clean frozen = "old" for hostile and fail-before
( cd $T && git rev-parse 'HEAD^{tree}' && git write-tree && git apply --check $FIX/core-fix-on-frozen-r7.patch && git apply $FIX/core-fix-on-frozen-r7.patch; echo apply rc=$? )
( cd $T && git add -N -A . && git diff --numstat | wc -l )               # number of changed files; compare with: cd /tmp && git apply --numstat $FIX/core-fix-on-frozen-r7.patch | wc -l
( cd $T && for f in scripts/reset.ps1 scripts/start_all.ps1; do echo "$f lines=$(wc -l < $f) lines-with-CR=$(grep -c "$(printf '\r')" $f)"; done )
diff -rq -x .git -x __pycache__ -x data $T $R/tree-R7 > $O/diff-vs-tree-R7.txt; echo rc=$?       # READ ONLY comparison with the builder tree; record, do not touch
```

Record in EVIDENCE.md section 1: both `git rev-parse` values, the two sha256 lines, apply rc, changed-file count both ways, the `.ps1` line check. If the head tree is not `49d3c859...` or apply rc is not 0: stop and report; do not run anything else.

## 2. Apply matrix (ran on r6: 24 cells, all three recommended cells passed; pytest 59 passed in each)

```
mkdir -p $O/apply; cd $O/apply
sh $AM/apply_matrix.sh $FIX/core-fix-on-frozen-r7.patch $FIX/core-fix-on-frozen-r7-lf.patch > apply-matrix.out 2>&1; echo rc=$? >> apply-matrix.out
```

(about 90 s; `--check` skips the pytest part: about 17 s). Exit 0 only if the cells that the README recommends pass; it prints the working commands per checkout type. Paste the whole table and the final line into section 2; if rc is not 0, paste the lines marked `FAIL` / `<<<` first.

## 3. FULL SUITE ONCE, alone, quiet machine (ran on r6: A 2347 passed 3 skipped 755 s; B 2470 passed 2 skipped 874 s)

Quiet check (no other heavy job of yours; record the output in section 3):

```
uptime; nproc; ps -eo pid,pcpu,etime,args --sort=-pcpu | head -6 | cut -c1-150
```

Start only if the 1-minute load average is below 1.5 on this 6-core machine. If it is higher: look who uses the CPU (you never kill a process you did not start), check again at most 10 times with a bounded `sleep 60` each; if still busy, run anyway and write the load numbers in section 0 as "NOT A QUIET RUN". Do not start any other heavy job (suite, mutation, fail-before, hostile) while the suite runs.

Split into two groups of about 55 test files (the tests folder has 110 files in r6; r7 will have a few more). Start from the EV6 groups so that timing stays comparable, add new files to the lighter group, and prove union and no overlap:

```
cd $T
ls tests/test_*.py | sort > $O/all-tests.txt
python3 - <<'EOF'
import os
O="/home/user/build/rr6/out/EV7"; E="/home/user/build/rr6/out/EV6"
allf=[l.strip() for l in open(O+"/all-tests.txt")]
A=[l.strip() for l in open(E+"/groupA.txt") if l.strip() in allf]
B=[l.strip() for l in open(E+"/groupB.txt") if l.strip() in allf]
for f in allf:
    if f not in A and f not in B: (A if len(A)<=len(B) else B).append(f)
assert set(A)|set(B)==set(allf) and not set(A)&set(B)
open(O+"/groupA.txt","w").write("\n".join(A)+"\n"); open(O+"/groupB.txt","w").write("\n".join(B)+"\n")
print(len(allf),len(A),len(B),"union equals present: True; overlap: 0")
EOF
```

Recipe that ran on r6 (`run-group.sh`, here with the paths of r7; the env vars are all required):

```
cat > $O/run-group.sh <<'EOF'
#!/bin/bash
g=$1; R=/home/user/build/rr6; O=$R/out/EV7; cd $R/tree-EV7
mkdir -p $R/tmp-EV7/$g; s=$(date +%s)
TMPDIR=$R/tmp-EV7/$g PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD/src PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout 2400 unshare -n python $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs --durations=10 $(cat $O/group$g.txt | tr '\n' ' ') > $O/full-$g.log 2>&1
echo "rc=$? wall=$(( $(date +%s)-s ))s" >> $O/full-$g.log
EOF
chmod +x $O/run-group.sh
cd $O && setsid nohup bash -c './run-group.sh A; ./run-group.sh B' > $O/groups.out 2>&1 &
```

(`unshare -n` gives an empty network; `lo_up-q4g.py` brings loopback up and then runs the command. Both groups run one after the other, about 28 min in total: more than a foreground command may take, so it is detached; check with a bounded `tail -n 3 $O/full-A.log` every few minutes, never an endless loop.) `--durations=10` is on from the start this time (EV6 group A lacked it). After the run: paste both summary lines, the skip lines and the slowest-10 lists. Pass/fail lines are copied, not summarised.

## 4. Alone re-runs

(a) Every test that failed or errored in A or B (from `-rf`): re-run each alone, twice, with the same recipe:

```
cat > $O/run-alone.sh <<'EOF'
#!/bin/bash
l=$1; shift; R=/home/user/build/rr6; O=$R/out/EV7; cd $R/tree-EV7; mkdir -p $R/tmp-EV7/alone-$l $O/alone; s=$(date +%s)
TMPDIR=$R/tmp-EV7/alone-$l PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD/src PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout 1500 unshare -n python $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs --durations=5 "$@" > $O/alone/$l.log 2>&1
echo "rc=$? wall=$(( $(date +%s)-s ))s" >> $O/alone/$l.log
EOF
chmod +x $O/run-alone.sh
```

(b) The known timing / alone list from EV6 (all passed alone on r6: drawer 3x 2.7 s; crm_hubspot 56 passed 31 s x2; portal_lead_pages file 31 passed 44 s; scrub_n8n_export 254 passed 27 s; shell_single_bracket 146 passed 4 s; burst_same_email 1 passed 7 s). Run exactly, one after the other, nothing else running:

```
cd $O
./run-alone.sh drawer1 tests/test_portal_lead_pages.py::test_approve_and_deny_live_in_the_lead_drawer_with_a_confirm_dialog_and_a_decided_line
./run-alone.sh drawer2 tests/test_portal_lead_pages.py::test_approve_and_deny_live_in_the_lead_drawer_with_a_confirm_dialog_and_a_decided_line
./run-alone.sh drawer3 tests/test_portal_lead_pages.py::test_approve_and_deny_live_in_the_lead_drawer_with_a_confirm_dialog_and_a_decided_line
./run-alone.sh portal-lead-pages-file tests/test_portal_lead_pages.py
./run-alone.sh crm1 tests/test_crm_hubspot.py
./run-alone.sh crm2 tests/test_crm_hubspot.py
./run-alone.sh scrub tests/test_scrub_n8n_export.py
./run-alone.sh shell tests/test_shell_single_bracket.py
./run-alone.sh burst tests/test_desk_edge_cases.py::test_burst_same_email
```

(c) Also run alone any new r7 test file that uses time, a port or a thread and any test named in the r7 notes as flaky: list them with `git -C $T diff --name-only` on the tests folder and `grep -ln "time.sleep\|monotonic\|socket\|Thread" <new test files>`. Table: test, run 1 rc/wall, run 2 rc/wall. A test that fails alone: copy the failure text, run it a third time, report all three.

(d) Step 6 of EV6 (`run6.sh root|nonroot`, `$O/step6-files.txt` = the test files that touch file permissions) ran the same files as root and as user 65534 with a bind-mounted `/dev/null`. Repeat it if the r7 patch touches permission-dependent tests: copy `$R/out/EV6/run6.sh` and `step6-files.txt` to `$O`, replace `tree-EV6` by `tree-EV7`, `tmp-EV6` by `tmp-EV7`, `out/EV6` by `$O`.

## 5. FAIL-BEFORE as a REQUIRED-FAILS CHECK

EV6 result: 1355 test ids of the r6 test files passed on old frozen code (`$R/out/EV6/fb-passes-on-old.txt`) and 1440 on r5 code (`fb2-passes-on-old.txt`). Most of those are old tests in changed files. The new script finds, among tests that are NEW or CHANGED, those that pass on old code.

Script: `$AM/required_fails.py` (tested on the EV6 lists, see below).

```
python3 $AM/required_fails.py NEW_IDS OLD_RESULT --old-tests <old tests folder> --new-tests <new tests folder> [--justified FILE] [--out FILE]
```

Steps:

1. Old trees. `tree-FB-EV7` = clean frozen clone (fail-before against the whole patch). `tree-FB2-EV7` = clean copy of the r6 head (frozen + r6 patch; fail-before against the r6 to r7 change only). Both without the new test files.
   ```
   git clone -q --branch frozen2 $R/demo-frozen/repo2 $R/tree-FB-EV7
   git clone -q --branch frozen2 $R/demo-frozen/repo2 $R/tree-FB2-EV7 && (cd $R/tree-FB2-EV7 && git apply $FIX/core-fix-on-frozen-r6.patch)
   ```
2. Test files new or changed in r7 against frozen: `(cd $T && git add -N -A . && git diff --name-only -- tests | grep '^tests/test_.*\.py$') > $O/fb-testfiles-all.txt`; against r6: `diff -rq` of `tree-FB2-EV7/tests` and `$T/tests` (changed or only in r7) into `$O/fb2-testfiles.txt`. Copy those test files from `$T` into the old tree (same relative path). Also copy any new support file in `tests/` (conftest, fixtures) that they import; if a new test imports a module that does not exist on old code, the collection error is the expected fail-before result.
3. Run each test file alone on the old tree, with `-rA` and a timeout (this is `run-fb-file.sh` of EV6, ran on r6; `FB_TIMEOUT=300` because `tests/test_r4_refusals.py` hung to 300 s on old code):
   ```
   cat > $O/run-fb-file.sh <<'EOF'
   #!/bin/bash
   f=$1; tree=$2; out=$3; n=$(echo $f | tr '/' '_'); R=/home/user/build/rr6; cd $R/$tree; mkdir -p $R/tmp-EV7/FB/$n $out; s=$(date +%s)
   TMPDIR=$R/tmp-EV7/FB/$n PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD/src PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout -k 5 ${FB_TIMEOUT:-600} unshare -n python $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -p no:cacheprovider -rA --continue-on-collection-errors $f > $out/$n.log 2>&1
   echo "rc=$? wall=$(( $(date +%s)-s ))s" >> $out/$n.log
   EOF
   chmod +x $O/run-fb-file.sh
   for f in $(cat $O/fb-testfiles-all.txt); do FB_TIMEOUT=300 $O/run-fb-file.sh $f tree-FB-EV7 $O/fb; done      # 3 files at a time at most; the machine is shared
   ```
   Build the list of passing ids with the EV6 helper: `python3 $R/out/EV6/fbsum.py $O/fb` (prints a table, writes `$O/fb-passes-on-old.txt`). Same for `tree-FB2-EV7` into `$O/fb2`.
4. Collect the ids of the NEW tests: `cd $T && PYTHONPATH=$PWD/src TMPDIR=$R/tmp-EV7 $PY -m pytest --collect-only -q -p no:cacheprovider $(cat $O/fb-testfiles-all.txt | tr '\n' ' ') | grep '::' > $O/new-ids.txt` (ran on r6: 2458 ids in 2.8 s).
5. The check (give the frozen tests folder through a throw-away `git archive frozen2 -- tests` copy):
   ```
   mkdir -p $R/tmp-EV7/frozen-tests && git -C $R/demo-frozen/repo2 archive frozen2 tests | tar -x -C $R/tmp-EV7/frozen-tests
   python3 $AM/required_fails.py $O/new-ids.txt $O/fb-passes-on-old.txt --old-tests $R/tmp-EV7/frozen-tests/tests --new-tests $T/tests --out $O/required-fails-vs-frozen.txt > $O/required-fails-vs-frozen.out
   python3 $AM/required_fails.py $O/new-ids2.txt $O/fb2-passes-on-old.txt --old-tests $R/tree-FB2-EV7/tests --new-tests $T/tests --out $O/required-fails-vs-r6.txt > $O/required-fails-vs-r6.out
   ```
   (`new-ids2.txt` = ids collected from the files of `fb2-testfiles.txt`.) Output: counts, a per-file table, one `REQUIRED <id>` line per new/changed test that passes on old code, and `helper-changed` files (a change only in a helper or fixture is not seen: for those files list the helper diff by hand). Exit 1 = some REQUIRED lines (that is a finding for the lead, not an error of the run). The lead must see each REQUIRED id justified as a control/pin or fixed. You do not judge.
6. Tested on the EV6 lists (ran on r6, `$AM/rf-test-ast.out`): of 2458 ids in the 35 r6 test files, 969 were new or changed against frozen, 24 of them pass on old code (list in `$AM/rf-required.txt`: 1 in test_crm_hubspot, 8 in test_file_call_guard, 2 test_live_claude, 2 test_portal_demo, 3 test_special_files_and_plain_text, 8 test_special_output_files); 1489 unchanged tests were skipped; 9 files have a changed helper. The 945 other ids have no passing line on old code; the EV6 list contains passing ids only, so failed, errored and never run cannot be told apart there. For r7 keep the full `-rA` logs (as `run-fb-file.sh` does): `required_fails.py` reads `FAILED`/`ERROR` lines from them directly, pass the concatenated logs (`cat $O/fb/*.log > $O/fb-all.log`) as OLD_RESULT instead of the passes-only list to get the three groups apart.

## 6. Lint, bandit, suppressions, long lines (ran on r6, `lint.log`, `suppress.txt`)

The pinned ruff is 0.17.1, NOT the one in `venv-br` (that is 0.17.4):

```
RUFF=/.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff     # (EV6 printed it as //.cache/...; same file)
cd $T; { $RUFF --version; echo '$ ruff check'; $RUFF check; echo rc=$?; echo '$ ruff format --check'; $RUFF format --check; echo rc=$?; } > $O/lint.log 2>&1
{ echo '## bandit -ll'; bandit -ll -r . -x ./tests,./.git 2>&1 | tail -n 40; } >> $O/lint.log
```

(Take the exact bandit arguments from the repo's CI file `.github/workflows/ci.yml` or `pyproject.toml`; EV6 used `bandit -ll` with the repo's own configuration and found 0 medium and 0 high. Print the command you really used.) If the pinned binary is gone: `uv tool run ruff@0.17.1` is not possible offline; then say so in section 0 and use the `venv-br` one with its version printed.

Suppression table, frozen vs r7, same method as EV6 (count of LINES containing the word over every tracked or new file; verified on r6: frozen = noqa 250, type: ignore 121, nosec 12, nosemgrep 32, S603 52):

```
count() { ( cd $1 && git add -N -A . >/dev/null 2>&1; for w in noqa "type: ignore" nosec nosemgrep S603; do printf '%s %s\n' "$w" "$(git grep -I -E -h -e "$w" | wc -l)"; done ); }
{ echo "frozen:"; count $R/tree-old-EV7; echo "r7:"; count $T; echo "--- added lines containing suppressions"; ( cd $T && git add -N -A . && git diff -U0 | grep '^+[^+]' | grep -E 'noqa|type: ignore|nosec|nosemgrep|S603' ); } > $O/suppress.txt
{ echo "--- added lines over 100 columns"; ( cd $T && git diff -U0 | awk '/^\+\+\+ /{f=$2} /^\+[^+]/{ if (length($0)-1>100) c100[f]++; if (length($0)-1>120) c120[f]++ } END{for(k in c100) print c100[k], "over100", k; for(k in c120) print c120[k], "over120", k}' ); } > $O/cols.txt
```

Put into EVIDENCE.md a table: word, frozen, r6 (from EV6: noqa 246, type: ignore 127, nosec 11, nosemgrep 32, S603 66), r7, plus every added suppression line verbatim. Lines over 120 columns in r6 were in `README.md` and `docs/limits.md` (1 and 2); compare.

## 7. Hostile re-run for the new r7 cases

Drivers (all under `$R/out/EV6/`, read them before use; they hard-code the paths `tree-EV6`, `tree-old-EV6`, `tmp-EV6`, `out/EV6`): `hostile_driver.py`, `hostile_extra.py`, `hostile_ev3.py`, `rerun_ci.py`, `hostile_resultfile.py`, `hostile_ev5.py` (these six run through `run-hostile.sh`; NOTE it starts with `rm -f hostile/results*.jsonl`: run it FIRST, before any other hostile part, or copy it without that line), then `run6.py` (r6 cases through `hostile_r6.py`) and `run6b.py f|g|h|j|f2`, `hostile_scripts.py` (script wrappers: `start_all.sh`, `reset.sh` with pid files as pipes), `hostile_n8n.py`, `hostile_inproc.py`, `hostile_secret.py`, `hostile_wrap.py` (memory wrapper).

Copy and re-point:

```
mkdir -p $O/hostile; cp $R/out/EV6/hostile_*.py $R/out/EV6/run6.py $R/out/EV6/run6b.py $R/out/EV6/rerun_ci.py $R/out/EV6/run-hostile.sh $R/out/EV6/redo.sh $O/
cd $O && sed -i 's#tree-old-EV6#tree-old-EV7#g; s#tree-EV6#tree-EV7#g; s#tmp-EV6#tmp-EV7#g; s#out/EV6#out/EV7#g; s#EV6#EV7#g' hostile_*.py run6.py run6b.py rerun_ci.py run-hostile.sh redo.sh
grep -n "EV6" hostile_*.py run6*.py rerun_ci.py run-hostile.sh | head          # must print nothing
```

Order (each part alone; old = `tree-old-EV7`, new = `tree-EV7`; 5 s timeout per case unless the driver says otherwise): `bash run-hostile.sh` (about 20 min on r6, writes `hostile/results-*.jsonl`), then `python3 run6.py > run6.out`, then `for p in g h j f f2; do python3 run6b.py $p > run6b-$p.out; done`. Then build the table with `mk_table.py` (copy it, same sed): columns rc, hang, traceback, line count, class name, typed-echo, old vs new.

New r7 cases to add (write each as a new `add(...)`/scenario in a copy named `hostile_r7.py` in the style of `hostile_r6.py`; read the r7 patch's new tests first and cover what they claim; every case runs on old and new, 30 s timeout, results appended to `hostile/results-r7.jsonl`):

| # | case | how (existing driver to copy) | what to record |
|---|---|---|---|
| 1 | IMAP user quoting: user with space, double quote, backslash, CR, LF, `{5}` literal marker, 300 characters, non-ASCII, empty | `hostile_r6.py` scenario `imap_user` (arg = user text) against its local TLS IMAP listener; record the bytes the listener received for the LOGIN line | rc, fixed refusal text, whether the user text appears in output, the exact LOGIN line seen by the server, no second command injected |
| 2 | fake_hubspot with no Content-Length (and `Transfer-Encoding: chunked`, and a Content-Length that is too small) | `hostile_r6.py` scenario `cl_fake_hubspot` (variants huge, neg, nonnum, missing, slow in `run6.py` line 40-42): add `chunked` and `short` | status line, whether the server waits, time to answer, rss |
| 3 | slow sender: 1 byte per second for 15 s with a declared length of 100, to fake_hubspot, fakes_server, fake_model_server, the desk port | `variant == "slow"` in `hostile_r6.py` | the time the server holds the connection, whether it answers other requests meanwhile (second client during the slow one) |
| 4 | `burst.py --url` that cannot connect (port 1, `http://0.0.0.0:1`, `http://[::1]:1`, host that does not resolve) and the three bad URL kinds | `hostile_ev3.py` `BU` list and `hostile_ev5.py` lines 20-26 | rc, one-line refusal, no traceback, time, whether any connect attempt reached a local listener (count accepted connections) |
| 5 | `scripts/start_all.sh` port owner: a listener already on the desk port and on the fakes port (owned by this runner, loopback), then start; also a stale pid file naming a pid that now belongs to another process (a `sleep 600` that you started, never a process of anyone else) | `hostile_scripts.py` (`start_all-desk.pid-fifo` style cases) plus a Python listener on the port | rc, message, which process still owns the port afterwards, that no foreign process was signalled (check with `kill -0` the process you started is still alive) |
| 6 | `scripts/n8n_api.py` exit codes | `hostile_n8n.py` and `hostile_r6.py` scenarios `n8n_key`, `n8n_activate` | table: input kind (good key, empty, fifo, big file, bad URL, unreachable, 401, 5xx, huge Content-Length) vs exit code; r6 note: every refusal exits 1 (owner decision); say whether r7 differs |
| 7 | the r6 survivors' inputs: blank `REAL_IMAP_n_CA_FILE`, blank `DESK_SMTPP_CA_FILE`, SMTP user non-ASCII, HubSpot token with weak chars | `hostile_r6.py` scenarios `smtp_both`, `hubspot_env`, `live_check` | rc, refusal text, whether the old text echoes the typed value |

Section 7 of EVIDENCE.md: counts of rows with a traceback / hang for old and new (as in EV6 section 5), the table above filled with raw rc/text, and what could not be started (NUL byte in env/args).

## 8. MAIL-PATH MUTANT LIST (34-mutant plan; run on the r7 head)

Source of M01-M31: `/home/user/build/rr6/out/REV6M-partial.md` (the r6 mutation run of the reviewer; "r6 result" below is its result). Counting plainly: that file holds 31 ids, M01-M30 with M18 split into M18a and M18b; there is no M31, and one id (M23) has a second line "rerun" (SURVIVED). The brief's "34 mutants" does not match: 31 + the 6 new r7 mutants named below = 37, with the 3 optional extras N07-N09 = 40. Run all 37; N07-N09 are optional (drop them if you need to land on 34 and tell the lead). The file column was found by searching the r6 tree for the symbol in the description; confirm with `grep -n` on the r7 tree before planting, the line may have moved.

Column "expected killing test" is left blank: the runner fills it from the first failing test id, never from the table.

| id | file (r6 tree, confirm) | mutation | r6 result | 3-7 test files to run | killed by (runner fills) | KILLED/SURVIVED |
|---|---|---|---|---|---|---|
| M01 | src/lead_desk/tls_trust.py | blank-setting check removed | KILLED | test_ca_file_reads, test_r5_refusals, test_r6_refusals | | |
| M02 | src/lead_desk/tls_trust.py | cadata PLUS system store (context also trusts the system store) | KILLED | test_ca_file_reads, test_r5_refusals, test_smtp_provider | | |
| M03 | src/lead_desk/tls_trust.py | check_hostname test removed | KILLED | test_r5_refusals, test_ca_file_reads, test_smtp_provider | | |
| M04 | src/lead_desk/tls_trust.py | verify_mode test removed | SURVIVED | test_r5_refusals, test_ca_file_reads, test_smtp_provider, test_r6_refusals | | |
| M05 | src/lead_desk/tls_trust.py | PEM always read as DER | KILLED | test_ca_file_reads, test_smtp_provider | | |
| M06 | src/lead_desk/tls_trust.py | non-ASCII inside a PEM block allowed | KILLED | test_ca_file_reads, test_file_reader_refusals | | |
| M07 | src/lead_desk/tls_trust.py | leftover guard: ssl error translation removed | KILLED | test_ca_file_reads, test_r5_refusals | | |
| M08 | src/lead_desk/regfile.py | S_ISREG check removed (open_regular) | KILLED | test_r5_refusals, test_file_reader_refusals, test_ca_file_reads | | |
| M09 | src/lead_desk/regfile.py | O_NONBLOCK removed | KILLED | test_ca_file_reads, test_file_reader_refusals, test_r5_refusals | | |
| M10 | src/lead_desk/regfile.py | size check removed (read_secret_line) | KILLED | test_r6_refusals, test_file_reader_refusals | | |
| M11 | src/lead_desk/regfile.py | unbounded read (read_secret_line) | KILLED | test_r6_refusals, test_file_reader_refusals | | |
| M12 | src/lead_desk/regfile.py | UTF-16 check removed | KILLED | test_smtp_provider, test_file_reader_refusals, test_live_claude | | |
| M13 | src/lead_desk/regfile.py | multi-line check removed | KILLED | test_smtp_provider, test_file_reader_refusals | | |
| M14 | src/lead_desk/regfile.py | control-character (isprintable) check removed | KILLED | test_r6_refusals, test_live_claude, test_smtp_provider | | |
| M15 | src/lead_desk/regfile.py | ASCII check removed | KILLED | test_r6_refusals, test_live_claude, test_smtp_provider | | |
| M16 | src/lead_desk/regfile.py | BOM strip removed | KILLED | test_r5_refusals, test_smtp_provider, test_live_claude | | |
| M17 | src/lead_desk/smtp_provider.py | no require_verifying in `__init__` | KILLED | test_r5_refusals, test_smtp_provider, test_r6_refusals | | |
| M18a | src/lead_desk/smtp_provider.py | no re-check in send | SURVIVED | test_r5_refusals, test_smtp_provider, test_r6_refusals | | |
| M18b | src/lead_desk/smtp_provider.py | no re-check in `_wrap` | SURVIVED | test_r5_refusals, test_smtp_provider, test_r6_refusals | | |
| M19 | src/lead_desk/smtp_provider.py | ca_file and context both allowed | KILLED | test_r6_refusals, test_smtp_provider | | |
| M20 | src/lead_desk/smtp_provider.py (and scripts/run_real_check.py) | blank DESK_SMTPP_CA_FILE falls back | SURVIVED | test_r6_refusals, test_smtp_provider, test_real_check_dry | | |
| M21 | src/lead_desk/imap_count.py | no require_verifying in `_session` | KILLED | test_r5_refusals, test_smtp_provider | | |
| M22 | src/lead_desk/imap_count.py | default context unverified | KILLED | test_smtp_provider, test_r5_refusals | | |
| M23 | scripts/run_real_check.py | blank REAL_IMAP_n_CA_FILE falls back | CRASH (timeout 120 s in test_real_check_dry), rerun alone with 290 s: SURVIVED | test_real_check_dry (give it 600 s, run it alone), test_r6_refusals | | |
| M24 | src/lead_desk/imap_count.py | user control-character check removed | KILLED | test_r6_refusals, test_smtp_provider | | |
| M25 | src/lead_desk/live_claude.py | live key read AFTER ledger reserve | KILLED | test_live_claude, test_r5_refusals | | |
| M26 | scripts/run_live_check.py | key validation skipped before reserve | KILLED | test_r5_refusals, test_live_claude | | |
| M27 | scripts/n8n_api.py | own weaker reader restored | KILLED | test_n8n_api_url, test_file_reader_refusals | | |
| M28 | src/lead_desk/regfile.py | read_regular_bytes size check removed (CA file) | KILLED | test_file_reader_refusals, test_ca_file_reads | | |
| M29 | src/lead_desk/crm_hubspot.py and scripts/hubspot_probe.py | HubSpot token uses the weak check | SURVIVED | test_hubspot_probe, test_crm_hubspot, test_r6_refusals | | |
| M30 | src/lead_desk/smtp_provider.py | SMTP user non-ASCII check removed | SURVIVED | test_smtp_provider, test_r6_refusals, test_real_check_dry | | |
| N01 | src/lead_desk/imap_count.py | IMAP user quoting removed (the user is sent to LOGIN as typed, not as a quoted string) | new in r7 | test_r6_refusals, test_smtp_provider, the r7 test file for IMAP quoting | | |
| N02 | src/lead_desk/imap_count.py (or ImapSettings validation) | user check removed (the refusal of space, quote, backslash, control characters in the user) | new | same as N01 | | |
| N03 | the file that holds the new cap on a literal / reply line (find: `grep -n -i "literal\|MAX_.*LINE\|maxline" src/lead_desk/imap_count.py src/lead_desk/constants.py`) | literal cap removed (cap raised to infinity or the comparison deleted) | new | tests that name the cap in the r7 patch | | |
| N04 | src/lead_desk/tls_trust.py (find: `grep -n "minimum_version\|TLSVersion"`) | minimum-TLS check removed (the context accepts TLS 1.0/1.1) | new | test_r5_refusals, test_ca_file_reads, the r7 test for the minimum version | | |
| N05 | src/lead_desk/regfile.py | ASCII-only strip reverted (back to the r6 `.strip()` that also removes non-ASCII white space) | new | test_r6_refusals, test_file_reader_refusals, test_smtp_provider | | |
| N06 | the settings class that holds the password or token (find: `grep -n "repr=False" src/lead_desk/*.py`) | `repr=False` reverted (the secret appears in `repr(settings)`) | new | the r7 test that prints or logs settings, test_smtp_provider, test_r6_refusals | | |
| N07 (optional) | scripts/run_real_check.py | IMAP user from the environment is not checked before the first connection | new, suggested | test_real_check_dry, test_r6_refusals | | |
| N08 (optional) | src/lead_desk/smtp_provider.py | SMTP password appears in an exception text (re-raise with the value) | new, suggested | test_smtp_provider, test_r6_refusals | | |
| N09 (optional) | src/lead_desk/imap_count.py | quoting applied to LOGIN but not to the folder name in SELECT | new, suggested | test_smtp_provider, the r7 IMAP test | | |

Rows N03, N04, N06 and the test names are confirmed only after you read the r7 diff; if a symbol is not found, write "mutation point not found: <grep used>" in the table and tell the lead; do not invent one.

How to run (never plant in `tree-EV7` itself; each mutant gets a throw-away copy; a killed run cannot leave a mutation behind):

```
mkdir -p $O/mutants/diffs
run_mutant() {  # $1 id, $2 file (relative), $3 python snippet text that edits the file (reads it as s, sets s), rest = test files
  id=$1; file=$2; edit=$3; shift 3
  rm -rf $R/tmp-EV7/mut-$id; cp -a $T $R/tmp-EV7/mut-$id; cd $R/tmp-EV7/mut-$id
  python3 -c "import sys;p='$file';s=open(p).read();n=s;exec(sys.argv[1]);assert n!=s,'mutation did not change the file';open(p,'w').write(n)" "$edit" || { echo "$id PLANT-FAILED" >> $O/mutants/mutants.tsv; return; }
  git diff --stat > $O/mutants/diffs/$id.txt; git diff >> $O/mutants/diffs/$id.txt     # exactly one file, a few lines
  mkdir -p $R/tmp-EV7/mutt-$id; s0=$(date +%s)
  TMPDIR=$R/tmp-EV7/mutt-$id PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD/src PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout -k 5 ${MUT_TIMEOUT:-420} unshare -n python $R/src-v6/drivers/lo_up-q4g.py $PY -m pytest -q -x -p no:cacheprovider -rf "$@" > $O/mutants/$id.log 2>&1; rc=$?
  k=$(grep -m1 '^FAILED' $O/mutants/$id.log | cut -c8-)
  case $rc in 0) r=SURVIVED;; 1) r=KILLED;; 124|137) r="TIMEOUT(rc=$rc)";; *) r="OTHER(rc=$rc)";; esac
  printf '%s\t%s\t%s\t%ss\n' $id "$r" "$k" $(( $(date +%s)-s0 )) >> $O/mutants/mutants.tsv; cd $R; rm -rf $R/tmp-EV7/mut-$id
}
```

Rules: run the same 3-7 test files once on a plain copy of `tree-EV7` first (the control) and record rc 0: a mutant counts as KILLED only if its control passed. The plant step refuses a mutation that changes nothing (assert), which was tried on r6 files; the rest of `run_mutant` was not run. KILLED = pytest rc 1 with a `FAILED` line (record the first id); rc 124 or a collection error is NOT killed: record TIMEOUT / OTHER and re-run that mutant alone with `MUT_TIMEOUT=600`; SURVIVED = rc 0. For a survivor also run the whole test files of the same module area once (not only the 3-7) and record which; if still alive, copy the diff. Max 4 mutant runs at the same time; `test_real_check_dry.py` (65 s per test, several minutes in all) only alone. Final table in EVIDENCE.md section 8: id, result, killing test id, seconds; counts of KILLED / SURVIVED / TIMEOUT. You do not say whether a survivor is acceptable.

## 9. What section 0 of EVIDENCE.md must say at the end (checklist)

- which of sections 1-8 you did not run or only partly ran, and why;
- apply matrix rc and whether the three recommended cells passed;
- suite: both group lines, skips, slowest ten, the load average at start, whether it was a quiet run;
- alone list: all nine entries, any extra;
- required-fails: counts and the REQUIRED list (or "not run");
- lint: exact ruff binary and version; bandit command; suppression table; columns;
- hostile: parts run, the r7 cases that could not be started;
- mutants: count run of 37 (or 40), TIMEOUT/OTHER ones;
- anything another process of someone else did to the machine while you ran;
- the processes you started and the confirmation that none is left (`pgrep -af "pytest|unshare|lo_up|hostile"` after your last step; stop only yours).

## Scripts delivered with this plan (all under `/home/user/build/rr6/out/AM/`)

| file | what | tested |
|---|---|---|
| `apply_matrix.sh` | apply matrix (section 2) | r6 patches: 24 cells, exit 0, pytest 59 passed on 3 recommended cells; 12 broken-patch runs all exit 1 (raw: `mutation-raw.out`) |
| `required_fails.py` | section 5 | EV6 r6 lists: output in `rf-test-ast.out`, `rf-required.txt`; format test with 3 input formats on a toy list; NOT tested against r7 |
| `mk_mutants.py` | makes the broken patches for the apply matrix mutation proof | used once on r6 |
| the recipes in this file (`run-group.sh`, `run-alone.sh`, `run-fb-file.sh`, `run_mutant`, count/cols shell) | sections 3-8 | copied from the EV6 scripts that ran; the r7 paths and the `run_mutant` function were NOT run (written here, check them with one trial mutant before the batch) |
