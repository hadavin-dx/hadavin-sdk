# CAPABILITY of core-c (Q1)

Probed 2026-11-20T05:19:20Z (10:49 IST). Raw output first, plain summary at the end.

```

$ nproc
4
[exit 0]

$ free -g
               total        used        free      shared  buff/cache   available
Mem:              15           0          15           0           0          15
Swap:              0           0           0
[exit 0]

$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        252G  8.9G   60G  13% /
[exit 0]

$ python3 --version
Python 3.13.18
[exit 0]

$ uv --version
uv 0.11.32 (x86_64-unknown-linux-gnu)
[exit 0]

$ uv python list
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
cpython-3.15.0b4-linux-x86_64-gnu                 <download available>
cpython-3.15.0b4+freethreaded-linux-x86_64-gnu    <download available>
cpython-3.14.6-linux-x86_64-gnu                   <download available>
cpython-3.14.6+freethreaded-linux-x86_64-gnu      <download available>
cpython-3.13.18-linux-x86_64-gnu                  /usr/local/bin/python3.13
cpython-3.13.18-linux-x86_64-gnu                  /usr/local/bin/python3 -> python3.13
cpython-3.13.18-linux-x86_64-gnu                  /usr/local/bin/python -> python3.13
cpython-3.13.18-linux-x86_64-gnu                  /usr/bin/python3.13
cpython-3.13.18-linux-x86_64-gnu                  /usr/bin/python3 -> /etc/alternatives/python3
cpython-3.13.18-linux-x86_64-gnu                  /usr/bin/python -> /etc/alternatives/python
cpython-3.13.14-linux-x86_64-gnu                  <download available>
cpython-3.13.14+freethreaded-linux-x86_64-gnu     <download available>
cpython-3.12.13-linux-x86_64-gnu                  <download available>
cpython-3.12.3-linux-x86_64-gnu                   /usr/bin/python3.12
cpython-3.11.18-linux-x86_64-gnu                  /usr/bin/python3.11
cpython-3.11.15-linux-x86_64-gnu                  <download available>
cpython-3.10.20-linux-x86_64-gnu                  <download available>
cpython-3.9.25-linux-x86_64-gnu                   <download available>
cpython-3.8.20-linux-x86_64-gnu                   <download available>
pypy-3.11.15-linux-x86_64-gnu                     <download available>
pypy-3.10.16-linux-x86_64-gnu                     <download available>
pypy-3.9.19-linux-x86_64-gnu                      <download available>
pypy-3.8.16-linux-x86_64-gnu                      <download available>
graalpy-3.12.0-linux-x86_64-gnu                   <download available>
[exit 0]

$ docker info
Client: Docker Engine - Community
 Version:    29.10.0
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.39.0
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.7.1
    Path:     /usr/libexec/docker/cli-plugins/docker-compose

Server:
failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock: connect: no such file or directory
[exit 1]

$ pg_ctl --version
environment: line 12: pg_ctl: command not found
[exit 127]

$ psql --version
psql (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
[exit 0]

$ ls /usr/lib/postgresql; which postgres initdb pg_ctlcluster
16
/usr/bin/pg_ctlcluster
clusterdb
createdb
createuser
dropdb
dropuser
initdb
oid2name
pg_amcheck
pg_archivecleanup
pg_basebackup
pg_checksums
pg_config
pg_controldata
pg_ctl
pg_dump
pg_dumpall
pg_isready
pg_receivewal
pg_recvlogical
pg_resetwal
pg_restore
pg_rewind
pg_test_fsync
pg_test_timing
pg_upgrade
pg_verifybackup
pg_waldump
pgbench
postgres
psql
reindexdb
vacuumdb
vacuumlo

$ apt-cache policy postgresql-14 postgresql-16 postgresql-17
postgresql-16:
  Installed: 16.15-0ubuntu0.24.04.1
  Candidate: 16.15-0ubuntu0.24.04.1
  Version table:
 *** 16.15-0ubuntu0.24.04.1 100
        100 /var/lib/dpkg/status
[exit 0]

$ id -un
root
[exit 0]

$ git --version
git version 2.43.0
[exit 0]

$ gh --version
gh version 2.89.0 (2026-03-26)
https://github.com/cli/cli/releases/tag/v2.89.0
[exit 0]

$ gh auth status (masked)
github.com
  X Failed to log in to github.com using token (GH_TOKEN)
  - Active account: true
  - The token in GH_TOKEN is invalid.

$ ruff --version
ruff 0.16.9
[exit 0]

$ uv run --version
error: unexpected argument '--version' found

  tip: a similar argument exists: '--verbose'

Usage: uv run --verbose...

For more information, try '--help'.
[exit 2]
```

## Plain summary
CAN run:
- 4 cores, 15 GB memory, 60 GB free disk.
- Python 3.13.18 (default), 3.12.3 and 3.11.18 are installed; uv 0.11.32 can download 3.12.13 and other versions.
- git 2.43.0, ruff 0.16.9, uv.
- PostgreSQL 16.15 binaries are installed (psql, and initdb, pg_ctl, postgres under /usr/lib/postgresql/16/bin; pg_ctl is not on PATH). NOT TRIED: starting a server. This box runs as root and PostgreSQL refuses to start as root, so it would need the postgres user. UNVERIFIED.

CANNOT run:
- Docker: the client is installed but there is no Docker daemon (no /var/run/docker.sock). No containers.
- PostgreSQL 14 and 17: no packages known to apt here (only 16). Not tried from another source.
- gh CLI: installed, but its token is rejected ("The token in GH_TOKEN is invalid"). GitHub reading and writing works through git push/fetch and the GitHub connector tools instead.
