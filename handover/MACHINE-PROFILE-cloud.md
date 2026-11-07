# Machine profile: the cloud session (written by the cloud session; the lead only reads it)

Updated: 2026-11-07T06:54Z. Update this file whenever a setting below changes. Machine-specific values live HERE and in the session scratch, never in repo files or PRs.

## Hardware and OS (measured)
- nproc 4; RAM 15 GB total (about 13 GB available, the rest page cache); swap 0 used; disk: a fixed per-session allowance (see df).
- OS: Ubuntu 24.04.5 LTS, kernel 6.18.44-fc-v310. Runs as root; Postgres must run as the `postgres` user (`runuser -u postgres`).
- Tools: uv 0.11.32 (x86_64-unknown-linux-gnu), Python 3.13.18 (system), project venvs for Python 3.13 and 3.12 created with `uv sync --python`, Postgres 16 server binaries under /usr/lib/postgresql/16/bin (CI uses 17.10: differences are reported), gitleaks in the session scratch, ruff/bandit from each project venv. No Docker daemon. No Vault (Vault tests skip).

## Heavy slots and the queue
- Heavy slots: 3 (calibration in q265: 1.5x slowdown at 3 copies, 2.7x at 6; CPU is the limit, memory is not). Do not raise. Lower to 2 if free memory drops under 3 GB.
- Slots are three flock files under /tmp (names heavy-slot-1..3.lock), shared by the two entry points in /home/user/build: heavy.sh (legacy blocking wrapper) and the queue runner qrun.sh. Builders submit with qsubmit.sh (owner, priority 1 = money/redaction, 2 = other, log file, command); it returns at once and the log ends with a line exit=<rc>. Queue directories: /home/user/build/queue/{pending,running,done}.
- Rule: nobody waits in a shell; builders queue, work on something else, and read the log.

## Postgres
- One server per run, started just before the run and stopped after it (pg_ctl -m fast stop), as the postgres user, data dir created with install -d -o postgres. Ports used: 55460-55483 for builders, 56010-56160 for evidence runs. Never run Python 3.12 and 3.13 against one cluster at once (cluster-wide role clash).
- Env var NAMES used: HADAVIN_TEST_PG_DSN (a postgresql:// URL with trust auth on 127.0.0.1), PGHOST, PGPORT, PGUSER (needed by tests/demo_askdata/test_validate_harm.py[dblink-connect]), UV_PROJECT_ENVIRONMENT (own venv per builder), HADAVIN_TEST_VAULT_ADDR (unset here). Values are never committed.

## Where things live
- Handover worktree: /home/user/hadavin-sdk-handover/handover (branch core/cloud-handover). Builder worktrees /home/user/build/<TICKET> (branch core/<ticket>). Detached evidence snapshots /home/user/build/EV-<ticket>-<sha7>/wt. Evidence scripts: evid.sh, qsubmit.sh, qrun.sh, calib/ in /home/user/build. Scrubbed evidence is copied to handover/evidence/<ticket>/<head>/ and handover/reviews/.

## Settings and hooks of THIS session that are not the laptop's
- GitHub through the MCP tools only (no gh pr create, no GraphQL); full CI runs only on PRs whose base is main.
- A hook requires every general-purpose sub-agent brief to start with the STUDIO-PREAMBLE v1 text containing EGM-GATE v1. The egm:* reviewer agents need none.
- Standing rules from the user's CLAUDE.md apply (EGM order for major tasks, DECISIONS.md log, brutal honesty). The session container can restart and then stops background agents; a restart does not stop processes started with nohup, but queued state in /home/user/build/queue survives only while the disk does.
- The commit trailers and PR footer are fixed (see the system reminder); path-limited commits only.

## Lane split (order 118)
- Cloud: builders and fix lanes, 3 heavy slots on the heads they build, independent EGM reviewers, scrubbed evidence files.
- Laptop (6 cores, 32 GB, 4 slots, Docker Postgres): lead S0 items, ci.yml additions, scan-job PR, evidence on STABLE heads (PR 63 bf955e9 first), spot-checks. If a head already has a green evidence file from either machine, do not run it again; every register row for a test run names the machine and the head.

## Machine-specific values found in committed files
- Sweep done (src, tests, tools, demos, .github on every origin/core/* branch for /home/user, 127.0.0.1:55xxx/56xxx, C:\\): no machine-specific value of this cloud machine is committed. The hits (about 6 per branch) are inherited from main: a documented example port 55432 in demos/ask-your-data/README.md (docker example, CI-style DSN) and Windows-path strings used as test inputs in tests/test_mutation_runner.py and tests/test_provider_errors_failbefore.py. They are examples/fixtures, not this machine's settings. Not changed; the lead may judge the README port.

## Postgres cluster creation (learned 2026-11-07)
Create every test cluster with `initdb -E UTF8 --locale=C.UTF-8 -A trust -U postgres`. Without those flags the cluster is SQL_ASCII and psycopg returns bytes ("TypeError: expected str instance, bytes found"), which shows up as 100+ false Postgres test failures. Found by the PR 66 builder; the PR 83 builder's first DSN run hit it.
