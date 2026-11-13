# DOCKER-PROBE (raw output, no judging). 2026-11-13, about 15:52Z to 15:58Z. Links, hosts, long hashes written in words or split (hygiene rule). The throwaway password was random, local, kept in an env var and never printed.

## Short answers
1. dockerd STARTS on the first try, as root, in its own process group: default storage (overlayfs via the containerd snapshotter), no vfs, no iptables switch needed. Ready after 1 s. Only warnings: nftables cleanup lines ("Could not process rule ... delete table") and cgroup v1 deprecation. I used a private socket and data folder in the scratch area (--host, --data-root, --exec-root), so the default socket stays absent; the harness must set DOCKER_HOST to that socket or start dockerd without --host.
2. Pull: the TAG pull `docker pull postgres:16` failed twice with HTTP 429 Too Many Requests from the Docker Hub registry (anonymous rate limit, 1 s each). Pull by DIGEST worked on the third try after waits (9 s): so the harness should RETRY with backoff. Image: linux/amd64, 667 MB shown (661037654 bytes), 638 MB on disk in the data root; free disk went 4.2 GB to 3.5 GB.
3. Digest it resolves to: sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1ec9c1deb47ff20d4f04233bf6eae9 (join the two halves; this equals the manifest-list digest seen in N8N-ENV-PROBE.md; the machine pulled the linux/amd64 child). Because the pull was by digest, the local tag "postgres:16" does not exist; `docker run postgres:16@sha256:<digest>` works.
4. Container: `docker run -d -e POSTGRES_PASSWORD=<random> -p 127.0.0.1:55432:5432` ok. pg_isready over TCP from the host (the host's own pg_isready) "accepting connections" after 2 s; `docker exec pgprobe pg_isready -U postgres` accepting; `docker exec pgprobe psql -U postgres -tAc "select version()"` returned PostgreSQL 16.16 (Debian 16.16-1.pgdg13+1) on x86_64. Stopped and removed; 0 containers left; port 55432 free.
5. Cleanup: dockerd killed with TERM ("Daemon shutdown complete"); 0 processes in its group, no dockerd or containerd left, socket gone, no mounts left, 55432 free. Image data folder deleted afterwards (see df lines).
6. Step 3 of the order (native Postgres) is not needed because docker works. Not probed: native pg_ctl/initdb. Server binaries 16.15 are installed (see N8N-ENV-PROBE.md). The harness files (g12e.py, g3e.py, setup.py, lib.py, run_all.py) are NOT readable from here: I searched every remote branch of this repo for them and for "docker exec" and found nothing but README text and a test file. So I cannot list their calls; send me the branch name when it exists.

## Raw: dockerd start (first try)
```
command: dockerd with --host unix socket, --data-root, --exec-root, --pidfile in the scratch folder, setsid, background
ready after 1s
time="2026-11-13T15:54:18.086702175Z" level=info msg="fetch failed after status: 429 Too Many Requests" host=<registry host> method=HEAD url="<link>"
time="2026-11-13T15:54:18.088821005Z" level=error msg="Handler for POST /images/create returned error" error-response="unknown: failed to resolve reference \"docker.io/library/postgres@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1e
time="2026-11-13T15:54:57.378764216Z" level=info msg="image pulled" digest="sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9" remote="docker.io/library/postgres@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1
time="2026-11-13T15:55:05.241748139Z" level=info msg="connecting to shim <container id>" address="unix:<socket> id>
time="2026-11-13T15:55:05.322103110Z" level=info msg="sbJoin: gwep4 ''->'ae065a0d2727', gwep6 ''->''" eid=ae065a0d2727 ep=pgprobe net=bridge nid=269667f3d385
time="2026-11-13T15:55:06.930988813Z" level=info msg="shim disconnected" id=<container id> namespace=moby
time="2026-11-13T15:55:06.931016434Z" level=info msg="cleaning up after shim disconnected" id=<container id> namespace=moby
time="2026-11-13T15:55:06.931021672Z" level=info msg="cleaning up dead shim" id=<container id> namespace=moby
time="2026-11-13T15:55:06.931221215Z" level=info msg="received task-delete event from containerd" container=<container id> module=libcontainerd namespace=moby topic=/tasks/delete t
time="2026-11-13T15:55:55.044723869Z" level=info msg="Processing signal 'terminated'"
time="2026-11-13T15:55:55.045906717Z" level=info msg="stopping event stream following graceful shutdown" error="grpc: the client connection is closing: context canceled" module=libcontainerd namespace=moby
time="2026-11-13T15:55:55.062533305Z" level=info msg="stopping event stream following graceful shutdown" error="context canceled" module=libcontainerd namespace=plugins.moby
time="2026-11-13T15:55:55.062480101Z" level=info msg="stopping containerd healthcheck following graceful shutdown" binary=/usr/bin/containerd module=supervisor pid=5542
time="2026-11-13T15:55:56.068721183Z" level=info msg="Daemon shutdown complete"
```
## Raw: docker info lines
```
 Server Version: 29.9.2
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: cgroupfs
 Cgroup Version: 1
 Runtimes: io.containerd.runc.v2 runc
 containerd version: <container id>
 Kernel Version: 6.18.44-fc-v445
 Operating System: Ubuntu 24.04.5 LTS
 Total Memory: 15.71GiB
 Docker Root Dir: <dp>/data
```
## Raw: pulls
```
Error response from daemon: unknown: failed to resolve reference "docker.io/library/postgres:16": unexpected status from HEAD request to <link> 429 Too Many Requests
pull exit 1 in 1s
-- digest pull try 1
Error response from daemon: unknown: failed to resolve reference "docker.io/library/postgres@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9": unexpected status from HEAD request to <link> 429 Too Many Requests
-- digest pull try 2
Error response from daemon: unknown: failed to resolve reference "docker.io/library/postgres@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9": unexpected status from HEAD request to <link> 429 Too Many Requests
-- digest pull try 3
Status: Downloaded newer image for postgres@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9
docker.io/library/postgres:16@sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9
```
## Raw: image and container
```
postgres:<none> sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9 667MB
linux/amd64 size=661037654
(data root 638M; run exit 0; pg_isready over TCP: 127.0.0.1:55432 - accepting connections; 2 s)
```
## df after each step (df -h of the work area, Avail)
start of probe 4.2G; dockerd up 4.2G; after failed tag pulls 4.2G; after digest pull 3.5G; with container running 3.5G; after dockerd stopped and data folder deleted: see next line
after cleanup: 4.2G free
