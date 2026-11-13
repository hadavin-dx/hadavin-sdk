# RERUN-RUNBOOK: n8n evidence harness on a fresh Linux machine like the probe machine

Written 2026-11-13 from N8N-ENV-PROBE.md and DOCKER-PROBE.md. Links, hosts and long hashes are written in words (hygiene rule). Every step is marked TESTED (I ran it on this machine, in the probe) or UNTESTED (not run; the harness branch is not here yet). Words in angle brackets are placeholders you fill in. No secret is needed anywhere; never print env values.

Machine facts the steps rely on (probe): root user; 4 cpus; 16 GB memory; Python 3.13 and Node 22 and npm 10 pre-installed; git, tmux, nohup, setsid present; Docker client 29.9.2 with no daemon running, dockerd binary present; native Postgres 16.15 installed; no ss command (use a bash /dev/tcp check); no IPv6; the machine can restart (processes die, files in the temp area stay).

## 0. Names used below
- `/tmp/rerun` is the scratch root (outside any repo). The harness path comes with the branch order; this runbook writes `<harness folder>` and `<repo root>` where it matters (UNTESTED).
- `DOCKER_HOST=unix:///tmp/rerun/docker.sock` the private daemon socket.
- Digest of postgres 16 seen on 2026-11-13 (manifest list): `sha256:` followed by `63e83b5a3dc36a917dccb76fe1bd2ac5` then `1ec9c1deb47ff20d4f04233bf6eae9` (join the two halves; no space). The brief from the lead may name a newer digest: use that one.

## 1. Disk first (step 11 of the order, put first on purpose)
Free disk was 5.7 GB at the start of the probe (4.2 GB later; it varies). Needs, in order of use: Node 24 about 0.1 GB; Postgres image 0.64 GB; n8n node_modules 3.0 GB (the probe's own install; the harness folder may differ: UNTESTED); logs and results small. Total about 3.8 GB.
```
df -h /tmp | tail -1          # Avail must be at least 5.0G; if not: stop and tell the lead
```
Order that never runs out: (a) Node 24, (b) pull the image, (c) npm ci, (d) rebuild. The image is pulled BEFORE npm ci because it is the smaller step and the one that can fail by rate limit (retry, step 5): if the disk is going to run out, it runs out at npm ci, before any run time is spent. Run `df -h /tmp | tail -1` after every step and write the line in your notes. Never delete the n8n install to make room; if short, delete the image (`docker rmi`) and say so. TESTED: sizes. UNTESTED: harness npm ci size.

## 2. Node 24.22.2 into a scratch folder (TESTED, no root, no apt)
```
mkdir -p /tmp/rerun/node && cd /tmp/rerun/node && npm init -y >/dev/null && npm install node@24.22.2
export PATH=/tmp/rerun/node/node_modules/.bin:$PATH
node --version          # must print v24.22.2
```
Why: n8n 2.46.6 needs Node 24 or newer; the machine's Node 22 makes n8n print "not supported" and exit. The export must be in EVERY shell, tmux window and nohup that runs npm or n8n (put it in `/tmp/rerun/env.sh` and `. /tmp/rerun/env.sh`; the file may hold the PATH line only, no secret).

## 3. Fetch the harness branch (clone of the public main TESTED, 2 s; the harness branch name and access UNTESTED)
```
mkdir -p /tmp/rerun && cd /tmp/rerun
git clone --branch <harness branch> --single-branch --depth 1 <repository address the lead gives> repo
```
Use the repository address and read access the lead provides. If a clone is refused, stop and report; do not widen access.

## 4. Postgres image by digest, retry on 429 (TESTED)
Start the daemon (step 5) first, then:
```
export DOCKER_HOST=unix:///tmp/rerun/docker.sock
D=sha256:<digest, halves joined>
for i in 1 2 3 4 5 6; do docker pull postgres:16@$D && break; sleep $((30*i)); done
docker images --digests          # tag shows <none>: normal, we pulled by digest
```
Probe: the tag pull and the first two digest pulls got HTTP 429 (anonymous Docker Hub rate limit); the third digest pull worked in 9 s. Use ONLY `postgres:16@sha256:<digest>` in every docker run (there is no local tag "postgres:16"). If all 6 fail: stop and report (the fallback would be the installed native Postgres 16.15 in a scratch folder as a non-root user: UNTESTED and needs a harness change).

## 5. Start dockerd in the background (TESTED, first try, ready in 1 s)
```
mkdir -p /tmp/rerun/dockerd
setsid dockerd --host=unix:///tmp/rerun/docker.sock --data-root=/tmp/rerun/dockerd/data \
  --exec-root=/tmp/rerun/dockerd/exec --pidfile=/tmp/rerun/dockerd/d.pid > /tmp/rerun/dockerd/dockerd.log 2>&1 &
export DOCKER_HOST=unix:///tmp/rerun/docker.sock
for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 1; done
docker info | grep -E "Server Version|Storage Driver"     # expect 29.9.2 and overlayfs
```
Harmless log lines: "Could not process rule ... delete table" (nftables) and a cgroup v1 deprecation warning. No iptables flag and no vfs were needed. If the harness expects the DEFAULT socket, start dockerd without `--host` and drop DOCKER_HOST (UNTESTED; the default socket path is /var/run/docker.sock).
Order to run: section 1 (disk), 2, 5 (start dockerd), 4 (pull), 6, 7, 8, 9, 10, 11, 12, 13. The numbers are not the run order only because the disk section comes first.

## 6. npm ci under Node 24, then rebuild isolated-vm (npm ci UNTESTED; rebuild TESTED)
```
. /tmp/rerun/env.sh ; node --version          # v24.22.2 again, in THIS shell
cd <harness folder> && npm ci                  # UNTESTED; probe's plain npm install took 6 min 5 s and 3.0 GB
npm rebuild isolated-vm                        # TESTED: 2 min 28 s; exit 0 "rebuilt dependencies successfully"
```
Why both: a build made under Node 22 and run under Node 24 crashed with "Could not initialize the vm expression engine". Because npm ci runs install scripts by default, running it under Node 24 should already build the right one; the rebuild is the belt and braces the probe proved. If npm ci was ever run under Node 22 by mistake, run the rebuild under Node 24 before anything else.

## 7. Python venv with pytest (TESTED; Python 3.13 has no pytest by default)
```
python3 -m venv /tmp/rerun/venv && /tmp/rerun/venv/bin/pip install -q pytest     # pytest 9.2.0 on the probe
/tmp/rerun/venv/bin/python -m pytest --version
```
If the harness lists more test requirements, install exactly those (UNTESTED).

## 8. Harness tests (UNTESTED; command from the lead)
```
cd <repo root> && /tmp/rerun/venv/bin/python -m pytest demo_only/n8n_evidence/harness/tests -q
```
Write down the last line (passed/failed/skipped counts). A failure: stop, copy the output to the result folder, report; do not edit tests.

## 9. Smoke run (UNTESTED)
```
/tmp/rerun/venv/bin/python -m <harness package>.run_all --smoke       # exact module name comes with the branch
```
Read `smoke_readiness.json` in the result folder: (the lead names the fields; UNTESTED) at minimum look for the n8n readiness answer 200, the task-runner port, the Postgres readiness, and any field saying false or an error text. What the probe saw for the same things by hand: n8n readiness 503 at 4 s and 200 at 8 s; task broker port listening from 4 s; Postgres ready over TCP 2 s after the container started.
Settings the probe needed for n8n on this machine (the harness may set them itself; check; UNTESTED in the harness): `N8N_LISTEN_ADDRESS=127.0.0.1` (no IPv6, the default "::" fails); the task broker's default port is 5679, the SAME as the order's `N8N_PORT=5679`, so set `N8N_RUNNERS_BROKER_PORT=5780` (probe-proven); `N8N_RUNNERS_ENABLED=true`; and to keep the machine quiet and private `N8N_DIAGNOSTICS_ENABLED=false` and `N8N_VERSION_NOTIFICATIONS_ENABLED=false`. Use a scratch `N8N_USER_FOLDER`. If the harness uses other ports, ports must be free before the run: check each with `bash -c 'exec 3<>/dev/tcp/127.0.0.1/PORT' && echo OPEN || echo free`.

## 10. Quiet-machine check (vmstat command TESTED; the `--min-idle` flag UNTESTED)
```
vmstat 1 120 > /tmp/rerun/vmstat.txt ; awk 'NR>3{i+=$15;n++} END{print "mean idle", i/n}' /tmp/rerun/vmstat.txt
```
Probe result: mean idle 90.1 percent on the 130 rows (the first data row is the since-boot average; it is skipped above), steady-state rows 100 percent. The pass line is idle of 80 percent or more. If lower: wait and measure again once; if still lower the run goes ahead only with `--min-idle 0` and the result file MUST say so (the harness writes it; read it back and confirm the words are in the result; UNTESTED). Do not start docker or n8n before the measure; they add load.

## 11. Full run: tmux, SIGTERM-safe stop (tmux/setsid present, TESTED as tools; the run itself UNTESTED)
```
tmux new-session -d -s rerun ". /tmp/rerun/env.sh; export DOCKER_HOST=unix:///tmp/rerun/docker.sock; cd <repo root>; /tmp/rerun/venv/bin/python -m <harness package>.run_all > /tmp/rerun/run.log 2>&1"
tmux ls ; tail -n 20 /tmp/rerun/run.log
```
With no tmux use: `setsid nohup <same command> > /tmp/rerun/run.log 2>&1 &` and record the pid and the process group id (`ps -o pgid= -p <pid>`).
Stop safely: send TERM to the whole process GROUP, never `pkill -f`: `kill -TERM -- -<pgid>`; wait 10 s; look at the log for the harness's own "stopped" line (UNTESTED; ask the lead what it writes); only then `kill -KILL -- -<pgid>`. The probe did exactly this for n8n alone: TERM, 6 s, KILL, then 0 processes left and both ports free.
Machine restart warning: the probe machine restarted once (processes died, files stayed). After a restart, the run is not resumable unless the harness says so (UNTESTED): start clean from step 12 cleanup.

## 12. Cleanup (docker part, kill and "by label" TESTED; the harness's label name UNTESTED)
```
export DOCKER_HOST=unix:///tmp/rerun/docker.sock
docker ps -aq --filter label=<harness label> | xargs -r docker rm -fv      # label name comes with the branch
docker ps -a --format '{{.Names}}' | wc -l                               # must print 0
kill -TERM $(cat /tmp/rerun/dockerd/d.pid); sleep 8; pgrep -x dockerd | wc -l ; pgrep -x containerd | wc -l   # 0 and 0
tmux kill-session -t rerun 2>/dev/null
for p in 5679 5780 55432; do bash -c "exec 3<>/dev/tcp/127.0.0.1/$p" 2>/dev/null && echo "$p OPEN" || echo "$p free"; done
```
Probe: dockerd stopped with "Daemon shutdown complete", no processes, socket gone. Add any other harness ports. Then, AFTER the result folder is copied out (step 13): `rm -rf /tmp/rerun`; `df -h /tmp | tail -1` (probe: 4.2G free after its cleanup).

## 13. What to push back
Only the harness RESULT folder (result json files, logs, vmstat.txt, the run.log, the df lines you wrote). Never node_modules, the docker data folder, the venv, the n8n user folder (it holds an auto-generated encryption key file), or anything with an env value. Before pushing: `grep -rn` the result folder for long random strings (40 or more characters of letters and digits) and for links, host names, paths of home folders and mail-style addresses; write them in words or drop them (hygiene rule). Push only to the branch the lead names. UNTESTED: the result folder name.

## 14. Short list of what the probe proved and what it did not
- PROVED: Node 24.22.2 from npm; plain install of the pinned n8n; the crash when built under Node 22; the rebuild fix; n8n readiness 200 within 8 s after the four fixes (listen address, broker port, runners, Node 24); the two ports free after killing the group; dockerd start; digest pull with retry; Postgres container on 127.0.0.1:55432 with pg_isready over TCP; venv plus pytest 9.2.0; tmux, setsid, nohup present; vmstat idle 90 percent.
- PROVED LATER (16:35Z, no harness needed): a clone of the public repo main with depth 1 over the web works (2 s, 5.0 MB, no login; head f3c39cf); venv plus pytest 9.2.0 runs a repo test file with no secrets (tests/test_input_edge_cases.py: 5 passed in 8 s); `docker ps -aq --filter label=<name> | xargs -r docker rm -fv` removed exactly the 2 labelled containers and left an unlabelled one (then removed by name); pull by digest worked on the first try this time; dockerd killed, 0 processes, ports free; scratch deleted.
- NOT PROVED (UNTESTED): npm ci in the harness folder; the harness tests, smoke, run_all, its flags (`--smoke`, `--min-idle`), its result file names, its labels and ports; the clone of the branch; running n8n AND Postgres together under load; time of a full run; behaviour after a restart.
