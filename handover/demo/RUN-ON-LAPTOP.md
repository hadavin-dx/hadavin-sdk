# RUN-ON-LAPTOP: Design A kill series (T8 to T13, K1 to K5) on another machine

Written by the cloud demo session. Everything here is made-up data, no spend, no secrets, no real mailbox. Nothing in this file is a result. LOOPBACK below means the machine's own loopback address; the scripts use it internally.
I have NOT run this exact procedure on a laptop. What I ran: the same scripts on one Linux machine with a native Postgres behind a small docker wrapper (part 6). Steps marked CHECK are the places where a first run on a new machine may need a fix; send me the driver.out and I read it.

## 1. What you need (details in n8n-mainframe/requirements-runner.txt)
- Node.js 24.22.x, n8n 2.46.6 (exact), Python 3.12+ (standard library only), Docker (for Postgres 16), a POSIX shell (Linux, macOS, or WSL2). The driver uses process groups to stop stand-ins and kills n8n by recorded pid; it does not work on plain Windows. CHECK: macOS/WSL2 were not tried by me.
- A checkout of the public repo duplicate-proof-lead-desk-n8n at the commit the evidence harness came from (n8n_evidence fix15 candidate). It gives: the harness folder `demo_only/n8n_evidence/harness` (api.py, lib.py, setup.py, run_all helpers), `demo_only/fake_model_server.py`, and the desk package `src/lead_desk`. I used a clean `git archive` export of the repo as the desk folder; any clean checkout is the same code.
- This branch: `handover/demo/` on demo/handover of the sdk repo (this folder tree).

## 2. Set up (once)
```bash
export REPO=/path/to/desk-checkout          # the public repo checkout (clean, no data/ leftovers)
export DEMO=/path/to/handover/demo           # this folder
export N8N_HARNESS_DIR=$REPO/demo_only/n8n_evidence/harness
export DN1_DESK_REPO=$REPO
export NODE_DIR=/path/to/node-v24.22.x/bin   # folder that holds the node binary; also put it on PATH
mkdir -p $HOME/mf-nm && cd $HOME/mf-nm
printf '{"name":"n8n-evidence","private":true,"dependencies":{"n8n":"2.46.6"}}' > package.json
npm install            # CHECK: writes package-lock.json; the harness repo's own smoke folder used npm ci with its lock file. Check `npm ls n8n` says 2.46.6
```
The harness refuses a run folder that is not fresh, so run_chain.py copies this folder (package.json, lock file, node_modules) into a new work folder for every test and removes it afterwards (about 1 GB each time).

## 3. Ports (must be free; the driver waits up to 150 s after a stop because the stand-ins do not set address reuse)
- n8n 5679, desk (unused by Design A but reserved by the base driver) 8765, fakes 8766, model stand-in 48767, counting proxy 8760 (reserved), CRM stand-in 8771, cap + model stage 8770, mail stand-in 8791, Postgres 55432 (container name n8n-publish-pg, label n8n-evidence.run=1).
- T14 (new): idle stack for 120 s (MF_IDLE_S), recovery running, no lead sent: pass = 0 stage requests, 0 model calls, 0 CRM requests, 0 mails (so no alert), 0 SMTP connections, 0 table rows. Run: python run_chain.py --tests "T14" --reps 1 ...
- Do not run two runs at once. Refuses to start if a container with that label exists or a port is busy.

## 4. Run
One test per run (so a machine restart costs one run, and each result lands on disk as it ends):
```bash
cd $DEMO/n8n-mainframe
python run_chain.py --tests "T8 T13 K1 K2 K3B K3 K4 K5 T10 T11 T12 T9" --reps 8 --lease 20 \
  --out $HOME/mf-out --work-root $HOME/mf-work --node-dir $NODE_DIR --node-modules $HOME/mf-nm --tag L
python count_table.py $HOME/mf-out
```
- `--reps` = kills per point (8 first; then 20: rerun with `--reps 20 --tag L20`). `--lease 20` is the TEST lease so recovery fits inside a run; the design lease is 120 s (flows in n8n-flows/ are built with 120; the test deploys its own build with the test lease). `--min-idle 80` is the harness load gate (CPU idle percent needed before each test; do not set it to 0). Machine busy for 10 minutes: exit 3.
- One test alone: `python run_mf.py --work-dir W --node-dir $NODE_DIR --skip-args "K3B"` (W = fresh folder with node_modules copied in; the test names go in --skip-args).
- Run time per test (8 kills): minutes; T10, T11, T13, K3B take longest (40 s holds, recovery waits). Do NOT kill a run from outside except by pid: stand-ins and n8n are killed by the driver's own cleanup.
- Check first that the harness works at all: run `--tests "M0 M1 T9"` (passes in my runs) before the kill series.

## 5. What each script is
- `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build_mainframe.py` (writes the four flow files, args: out dir, postgres credential id, smtp credential id, sub-workflow id, lease seconds), `crm_stub.py` (CRM stand-in), `stage_server.py` (cap + model stage; imports the desk's live qualifier and spend ledger; needs the desk checkout), `count_table.py` (prints raw counts).
- `n8n-tests/`: `dn1_common.py` (shared helpers, ports, process control, the exact environment the stage gets), `smtp_catcher.py` (mail stand-in), plus the Design B files (not needed here).
- `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step).
- What needs docker: only Postgres, in five places: run_mf.py (`docker ps/pull/run/exec/rm`), mf.py (`docker exec <name> psql ...`, `pg_isready`, and `docker kill` / `docker start` for the Postgres kill tests K5 and T13).

## 6. Docker or no docker
- Real Docker Desktop: nothing to change. run_mf.py pulls the Postgres 16 image by the digest written in PG_IMAGE (read on a Windows x64 Docker Desktop). CHECK: if the digest does not exist for your CPU type, edit PG_IMAGE to your `postgres:16` image digest and tell me.
- Native Postgres instead: put a program called `docker` first on PATH that maps the same commands onto a native Postgres 16 on port 55432. My version is `n8n-mainframe/examples/docker-native-pg-shim.py` (Linux paths, runs initdb as the postgres user; `kill` = immediate stop without clean shutdown, `start` = start again; `ps` prints a line when up). Copy it to a folder as `docker`, chmod +x, adjust its paths. It is a scratch file, not part of the design.
- The Postgres kill tests (K5, T13) are only meaningful if `docker kill` stops the database without a clean shutdown, as the real container does.

## 7. Counting rule (outside the flow, in mf.py)
After each lead the driver reads, from OUTSIDE n8n: the mail stand-in file (subject starts `[demo] lead <id>`; alerts go to the alert recipient), the CRM stand-in rows, the model stand-in call log, the spend ledger, the SMTP connection log, and the lead table row. Expected set (lead ids sent) against observed sets; ANY id in an observed set that was not sent is an extra and fails the test.
- lost = no final state in time (done, unknown, failed or review), or done without exactly 1 CRM row and 1 mail.
- doubled = more than 1 CRM row, mail, model call or alert for one lead id.
- unknown = state unknown (acceptable only where the test says so; a person decides; 1 alert).
- Every test also checks: model calls = 1 and ledger reserve rows = 1 per lead id.

## 8. Pass criteria per test (what mf.py writes as PASS; read the `why` line, not only the word)
- M0, M1, T9, T12 passed in my runs earlier (smoke before the series).
- T8: cap stage refuses / errors / times out (also under the 3 recovery tries): 0 mails to the intake recipient, 0 CRM writes, 0 model calls, state failed, exactly 1 alert per lead; SMTP connections equal alerts.
- T10: main run held 40 s (CRM answer, then SMTP acknowledgement) with the test lease while recovery fires: 1 CRM row, 1 mail, 1 model call per lead; state done or unknown (unknown is allowed: a lease shorter than the SMTP hold gives a safe but unneeded unknown; that is why the design lease is 120 s).
- T11: 8 leads in flight, n8n killed and restarted, TWO recovery workflows at once: nothing lost, nothing doubled.
- T13: duplicate delivery of one lead id (3 at once), Postgres killed mid-burst of 12 leads, then n8n killed and restarted with half-done runs: nothing lost, nothing doubled.
- K1 n8n killed after the claim insert, before the CRM write. K2 after the CRM write, before the mail step. K3B after mail_sent set while the SMTP node connects (mail not yet delivered). K3 after the mail was delivered, before the table update. K4 desk stage killed mid-call (model stand-in slow). K5 Postgres killed once while n8n waited for the CRM answer.
  For each point: lost 0, doubled 0, extras none, money ok, kill point reached in every sample, every lead ends done, unknown (only K3B and K3 can legitimately end unknown or done) or failed after 3 tries.

## 9. How a runner reports (send exactly this back, no interpretation)
- `python count_table.py OUTDIR` output pasted as is, plus the whole `OUTDIR/<run>/` folders (driver.out, mf_result_*.json, the .log/.jsonl/.conn files; they hold made-up lead data only).
- Per kill point: sample size, lost, doubled, unknown (and how many of those had the mail delivered), failed, kill point not reached, seconds from kill to final state (min/median/max), extras, money ok/not ok. A run that did not reach its kill point in some samples is reported with that count, not hidden.
- Also: OS, CPU type, Docker version or native Postgres version, Node version, `npm ls n8n`, whether the load gate waited, and any run that ended with a non-zero code (rc in the chain output) with its driver.out.
- Do not delete a failed run's folder before it is copied out. Do not edit the scripts mid-chain; if one must change, say which and why.

## 10. Known limits (so nobody reads more into the numbers)
- Stand-ins stand in for the CRM and the mail server; the model is a stand-in; the cap + model stage is my wrapper around the desk's own code (the desk has no endpoint for it yet).
- n8n's own HTTP node timeout (15 s) fires before a 40 s CRM hold, so the CRM-hold variant of T10 does not exercise the lease; the SMTP-hold variant does.
- Not yet done: T4 (node timeout 2 s against 1/3/8 s delays), T7 (planted secret grep), the lead-id safe-pattern check, Design B on the same fault modes.
