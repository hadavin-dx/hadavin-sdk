# CAPABILITY of the core-a container (queue item Q1). Probed 2026-11-20 05:21 UTC / 10:51 IST

Raw output of every command: handover/core-a/raw/capability-raw.txt and raw/capability-raw-2.txt (same folder).

## What this container CAN run (each line was run and seen)
- 4 cores (`nproc`), 15 GB memory (`free -g`), disk / 252G size, 8.9G used, 60G free (`df -h /`). Ubuntu 24.04.5. User: root.
- Python 3.13.18 (default), 3.12.3 (/usr/bin/python3.12), 3.11.18. uv 0.11.32 can also download 3.12.13 and 3.14.6 (listed as "download available"; download NOT tried).
- The project environment installs: `uv run --all-extras --group test python -c "import hadavin_sdk"` printed "import ok 3.13.18" (78 packages installed).
- ruff 0.17.1 inside the project environment (the pinned one); a system ruff 0.16.9 also exists: use only the `uv run` one.
- git 2.43.0. Fetch and push to this repo work through the session's git proxy (push to cloud/core-a succeeded 3 times).
- PostgreSQL 16.15 server programs are installed (/usr/lib/postgresql/16/bin: initdb, pg_ctl, postgres, psql, pgbench) and a `postgres` system user exists (uid 102). They are not on PATH (only psql is). Starting a server was NOT tried yet: it needs a run as the postgres user because PostgreSQL refuses to start as root. UNVERIFIED until a ticket needs it.

## What this container CANNOT run
- Docker: client 29.10.0 is installed but there is no daemon ("failed to connect to the docker API at unix:///var/run/docker.sock"). No containers, no testcontainers.
- PostgreSQL 14 and 17: not installed and not in the package index of this machine (`apt-cache policy` lists only postgresql-16). Not installable without adding an outside package source: not tried, would need the lead's yes.
- gh (GitHub command line 2.89.0): installed, but `gh auth status` says "The token in GH_TOKEN is invalid". GitHub reads go through the session's GitHub tools instead; scope is hadavin-sdk and hadavin-portal-kit only.
- n8n: not checked (no `n8n` command was probed). Template files can be written and checked as JSON; running them in n8n is NOT possible here unless the lead says how.

## What this means for my steps
- E and D unit tests (fake stores, signed requests) can run here on Python 3.13 and 3.12.
- Tests that need real PostgreSQL 16 are possible in principle (UNVERIFIED, see above); the evidence campaign on real PostgreSQL 16 stays with the lead on the laptop (ORDER 004 item 6). PostgreSQL 14 and 17 runs: NOT possible here.
