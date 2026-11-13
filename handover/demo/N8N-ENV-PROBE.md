# N8N-ENV-PROBE (raw output, no judging). Machine: this cloud Linux box. Probe 15:30Z to about 15:55Z, 2026-11-13.
Links, host names and long hashes are written as <link> or split, by the hygiene rule. No secret, key, account or real data was used. Env values were never printed.

## 0. Short answers (from the raw output below)
- Machine restarted at about 15:30Z (uptime 0 min at the first command). Processes started before then do not survive a restart; files in the scratch area do.
- n8n 2.46.6 (the version in versions.md of the demo repo) says engines node >=24.0.0. This machine's default Node is v22.23.4: n8n 2.46.6 PRINTS "not supported" and EXITS. (section 5a)
- Node 24.22.2 (the exact version versions.md lists) CAN be installed from the npm registry as the package "node" into a scratch folder; no root, no apt. (5b)
- npm install of n8n run under Node 22 builds the native module isolated-vm for Node 22; starting under Node 24 then crashes ("Could not initialize the vm expression engine"). Fix that worked: `npm rebuild isolated-vm` under Node 24 (2 min 28 s). Better: run the whole npm install under Node 24. (5c, 5e)
- IPv6 is not available: default listen address "::" fails; with N8N_LISTEN_ADDRESS=127.0.0.1 it works. (5d)
- N8N_PORT=5679 collides with the task broker's DEFAULT port 5679 ("Task Broker's port 5679 is already in use"). Needs N8N_RUNNERS_BROKER_PORT=5780 for the broker to listen on 5780. (5f)
- With Node 24.22.2 + rebuilt isolated-vm + N8N_LISTEN_ADDRESS=127.0.0.1 + N8N_PORT=5679 + N8N_RUNNERS_BROKER_PORT=5780 + N8N_RUNNERS_ENABLED=true: readiness 503 at 4 s, 200 at 8 s, 200 again 20 s later; 5780 listening from 4 s; after kill of the process group both ports free, zero processes left. (5g)
- Disk: only 5.7 GB free before and 1.1 GB free after the n8n install (node_modules 3.0 GB). A second full install will not fit unless the first is deleted.
- Docker: client 29.9.2 present, NO daemon running (no socket). Postgres 16.15 server binaries ARE installed (apt), not on PATH, in the postgresql 16 bin folder. Docker Hub and ghcr answer HTTP 401 (reachable, need a token); the anonymous token endpoint answers 200.

## 1. Basics
## uname
Linux vm 6.18.44-fc-v445 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux
## nproc
4
## free -m
               total        used        free      shared  buff/cache   available
Mem:           16086         474       15558          16         273       15611
Swap:              0           0           0
## df -h <probe>
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        252G   33G  5.7G  86% /
## python3 --version
(eval):2: command not found: python3 --version
## node --version
(eval):2: command not found: node --version
## npm --version
(eval):2: command not found: npm --version
## git --version
(eval):2: command not found: git --version
## docker --version
(eval):2: command not found: docker --version
## uptime
 15:30:56 up 0 min,  0 user,  load average: 0.00, 0.00, 0.00
## python3 --version
Python 3.13.18
## node --version
v22.23.4
## npm --version
10.9.9
## git --version
git version 2.43.0
## docker --version
Docker version 29.9.2, build a82e528
## psql --version
psql (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
## postgres --version
bash: line 2: postgres: command not found
## which
/usr/local/bin/python3
<node22dir>/bin/node
<node22dir>/bin/npm
/usr/bin/git
/usr/bin/docker
/usr/bin/psql
/usr/bin/apt-get
## pg binaries
16

## 2. Registry, Docker Hub, Postgres image
```
## npm view n8n
{
  "version": "2.47.7",
  "dist-tags": {
    "stable": "2.47.7",
    "latest": "2.47.7",
    "rc": "2.47.7",
    "next": "2.48.4",
    "beta": "2.48.4"
  }
}
npm notice
npm notice New major version of npm available! 10.9.9 -> 12.2.2
npm notice Changelog: <link>
npm notice To update run: npm install -g npm@12.2.2
npm notice
## npm view n8n@2.46.6 version engines
{
  "version": "2.46.6",
  "engines": {
    "node": ">=24.0.0"
  }
}
## n8n versions count and last 8
1255
['2.47.5', '2.47.6', '2.47.7', '2.48.0', '2.48.1', '2.48.2', '2.48.3', '2.48.4']
2.46.6 listed: True
## postgres:16 manifest list (anonymous token, no secret)
HTTP/1.1 200 Connection Established
HTTP/2 200 
docker-content-digest: sha256: 63e83b5a3dc36a917dccb76fe1bd2ac5 1f1ec9c1deb47ff20d4f04233bf6eae9
application/vnd.oci.image.index.v1+json
[('linux', '386'), ('linux', 'amd64'), ('linux', 'arm'), ('linux', 'arm64'), ('linux', 'ppc64le'), ('linux', 'riscv64'), ('linux', 's390x'), ('unknown', 'unknown')]
```
(node install via npm of node@24.22.2: exit 0; <node24dir> bin/node --version = v24.22.2; the 'node' package gave 2 packages added)
## pg 16 bin
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
## id
0
## dockerd
/usr/bin/dockerd
/usr/bin/containerd
## apt dpkg state
+++-==============-======================-============-=========================================================
ii  postgresql-16  16.15-0ubuntu0.24.04.1 amd64        The World's Most Advanced Open Source Relational Database
## unshare/ports
bash: line 4: ss: command not found

## 3. Outbound network (curl HTTP status; 401 = reachable, token needed; github front page 400 to a bare curl)
## docker info
Client: Docker Engine - Community
 Version:    29.9.2
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.38.1
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.6.1
    Path:     /usr/libexec/docker/cli-plugins/docker-compose

Server:
failed to connect to the docker API at unix://<docker socket>; check if the path is correct and if the daemon is running: dial unix <docker socket>: connect: no such file or directory
## network
<link> -> 200
<link> -> 400
<link> -> 200
<link> -> 401
<link> -> 401
<link> -> 200
## apt
2 not fully installed or removed.
Conf zsh-common (5.9-6ubuntu2 Ubuntu:24.04/noble [all])
Conf zsh (5.9-6ubuntu2 Ubuntu:24.04/noble [amd64])
pypi simple index 200; npm registry 200; docker auth 200; docker registry 401; ghcr 401; github 400 (answered).

## 4. Two minutes idle, vmstat 1 120 (file has 132 lines; first data row is the since-boot average)
```
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  1      0 15931384  23512 256264    0    0 23721   130 1764    5  5  4 89  2  0  0
 0  0      0 15927080  24268 258168    0    0  1984     8  772 1000  3  1 96  0  0  0
 0  0      0 15927080  24268 258168    0    0     0     0  254  231  1  0 99  0  0  0
 0  0      0 15927972  24268 258168    0    0     0     0  216  139  0  0 100  0  0  0
 0  1      0 15927656  24276 260684    0    0  2620     4  390  353  2  1 96  0  0  0
 0  0      0 15834416  28312 345596    0    0 87616     8 3496 4297  5  6 78 10  1  0
 0  0      0 15834416  28312 345596    0    0     0     0  120   97  0  0 100  0  0  0
 0  0      0 15837192  28312 345704    0    0   108     0  288  200  2  0 98  0  0  0
 0  0      0 15838436  28312 345704    0    0     0     0  224  146  0  0 100  0  0  0
 0  0      0 15839304  28312 345704    0    0     0     0   40   31  0  0 100  0  0  0
... (middle rows all id=100) ...
 0  0      0 15674848  31680 504516    0    0     0    24  103  103  0  0 100  0  0  0
 0  0      0 15674848  31680 504516    0    0     0     0   52   65  0  0 100  0  0  0
 0  0      0 15674848  31680 504516    0    0     0     0   69   74  0  0 100  0  0  0
 0  0      0 15674848  31680 504516    0    0     0     0   86   84  0  0 100  0  0  0
 0  0      0 15674848  31680 504516    0    0     0     0   98  122  0  0 100  0  0  0
 0  0      0 15674848  31680 504516    0    0     0     0   52   68  0  0 100  0  0  0
```
mean over rows after the first: us=1.0155 sy=0.27907 id=90.1395 wa=0.751938 rows=129
uptime before: 15:30:56 load 0.00 0.00 0.00; after:  15:32:55 up 2 min,  0 user,  load average: 0.06, 0.04, 0.01

## 5. n8n 2.46.6 in a scratch folder outside the repo
### 5-install (npm install n8n@2.46.6 --ignore-scripts=false, under Node 22): exit 0, 2303 packages, 6 min 5 s wall, 3.0 GB, 166 audit notes. EBADENGINE warnings: 15 lines, first:
```
npm warn EBADENGINE Unsupported engine {
npm warn EBADENGINE   package: 'n8n@2.46.6',
npm warn EBADENGINE   required: { node: '>=24.0.0' },
npm warn EBADENGINE   current: { node: 'v22.23.4', npm: '10.9.9' }
```
### 5a start under Node 22 (N8N_PORT=5679, runners on): output then readiness polled 60 s: always 000, 5780 never listening
```

Your Node.js version 22.23.4 is currently not supported by n8n.
Please use a Node.js version that satisfies the following version range: >=24.0.0

```
### 5c start under Node 24.22.2, install built under Node 22 (IPv6 default): output
```
No encryption key found - Auto-generating and saving to: <scratch>/uf/.n8n/config
Initializing n8n process
n8n's address '::' is not available. Please run n8n with a different address, provide correct address in the environment variables N8N_LISTEN_ADDRESS and/or N8N_WORKER_SERVER_ADDRESS.
```
### 5d with N8N_LISTEN_ADDRESS=127.0.0.1 only: ends with
```
Finished migration AddSkillMcpAvailability1793000146414
n8n Task Broker's port 5679 is already in use. Do you have another instance of n8n running already?
```
### 5e with broker port 5780 but the Node-22-built isolated-vm: readiness 000 for 79 s; log lines:
```
Could not initialize the vm expression engine (see errors above for details). If they point at isolated-vm, check that it installed correctly, e.g. that native build scripts were not skipped.
Could not initialize the vm expression engine (see errors above for details). If they point at isolated-vm, check that it installed correctly, e.g. that native build scripts were not skipped.
Error: Could not initialize the vm expression engine (see errors above for details). If they point at isolated-vm, check that it installed correctly, e.g. that native build scripts were not skipped.
```
### 5f npm rebuild isolated-vm under Node 24
rebuilt dependencies successfully
exit 0
wall 2 min 28 s
### 5g the ordered 60-second start (Node 24.22.2, rebuilt isolated-vm, 127.0.0.1, N8N_PORT=5679, broker 5780, runners enabled; own process group via setsid)
```
pid 5240 pgid 5240 start 15:48:20
t=0s readiness=000 port5780=no
t=2s readiness=000 port5780=no
t=4s readiness=503 port5780=LISTEN
t=6s readiness=503 port5780=LISTEN
t=8s readiness=200 port5780=LISTEN
20s later: readiness=200
port 5679 free
port 5780 free
```
log lines:
```
n8n ready on 127.0.0.1, port 5679
n8n Task Broker ready on 127.0.0.1, port 5780
Registered runner "JS Task Runner" (EQhg2d826w2XcBrKVBYPN) 
Editor is now accessible via:
```
error word count in that log: 2 (lines contain the migration names or normal text; none stopped the start)
kill: TERM to the process group, 6 s, KILL; then ports 5679 and 5780 free and 0 processes in the group.

## 6. Pinned version in the demo repo docs
versions.md section 'n8n (demo only)': n8n 2.46.6, regular mode, one process, SQLite inside n8n; Node.js 24.22.2. docs/n8n-recipe.md points there. Registry today: latest/stable/rc 2.47.7, next/beta 2.48.4; 2.46.6 is still listed (1255 versions).
