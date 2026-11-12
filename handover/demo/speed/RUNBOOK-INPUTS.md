# RUNBOOK-INPUTS (lane 6): facts measured in the demo cloud container
Status: DRAFT at 2026-11-12 19:05Z. Facts below were measured with the commands shown while lanes 1, 3, 4 and 5 were running or starting. The idle CPU sample is still to come (it needs all other lanes idle), so it is not here yet.

| Fact | Measured value | Command |
|---|---|---|
| Linux python3 (default) | Python 3.13.18 | python3 --version |
| python3.12 | Python 3.12.3 at /usr/bin/python3.12 (the demo docs ask for 3.12; lane 1 used it) | python3.12 --version |
| uv | 0.11.32 | uv --version |
| node | v22.23.4 | node --version |
| nproc | 4 | nproc |
| memory | 16086 MiB total, 13692 free | free -m |
| disk | /dev/vda 252G total, 9.5G used, 29G available on / | df -h /tmp |
| docker CLI | present (Docker Engine - Community 29.9.2 client) | docker info |
| docker daemon | NOT reachable: "failed to connect to the docker API at unix:///var/run/docker.sock ... no such file or directory" (no daemon; containers cannot run here) | docker ps |
| podman | not installed | which podman |
| outbound network | github.com: HTTP 200; pypi.org/simple: HTTP 200; example.com: HTTP 403 Forbidden from the proxy (so not every host is allowed; the network is an allowlist, not open) | curl |
| load at the sample | load average 0.66 0.54 0.28 with agents just starting | uptime |

Notes
- The browser: Chromium and Playwright are preinstalled (/opt/pw-browsers/chromium); not exercised by this lane.
- Windows pieces cannot run here (cloud is Linux).
- Still to add once the other lanes are idle: uptime and top -bn1 head. I will not write a CPU sample taken while the lanes run as if it were an idle sample.
