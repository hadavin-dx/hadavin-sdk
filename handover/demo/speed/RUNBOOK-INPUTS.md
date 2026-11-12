# RUNBOOK-INPUTS (lane 6): facts measured in the demo cloud container
Status: DRAFT (updated below with measured test timings and two CPU samples) at 2026-11-12 19:05Z. Facts below were measured with the commands shown while lanes 1, 3, 4 and 5 were running or starting. The idle CPU sample is still to come (it needs all other lanes idle), so it is not here yet.

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

## Measured serial test times on this container (4 vCPU, shared with other agents; all one pytest process, no xdist)
| Run | Tree | Python | Result | Wall time | Source |
|---|---|---|---|---|---|
| lane 1, no Playwright | initial-code 43110e7 | 3.12.3 venv | 2349 passed, 116 skipped | 886 s | outsider/SUMMARY.md |
| lane 1, with Playwright (system chromium 1243 with playwright==1.63.0) | initial-code 43110e7 | 3.12.3 | 2460 passed, 2 failed (Pillow missing), 3 skipped; 2462 passed, 3 skipped after `pip install pillow` | 1026 s | outsider/08 |
| lane 4, no Playwright | pr-3-tests bee6fff4 | 3.12.3 uv | 2349 passed, 116 skipped | 894.6 s | outsider2/SUMMARY.md |
| lane 4, browser files only | pr-3-tests | 3.12.3 uv | 185 passed, 2 failed (Pillow), 0 skipped | 225 s | outsider2/17 |
| Python resolver base run, with other agents' tests running | initial-code | 3.12.3 | 2349 passed, 116 skipped | 953 s | triage/evidence-py-resolve-03 |
Reading: one serial full run is about 15 minutes without Playwright and about 17 minutes with it on this machine; a lead estimate of 16 minutes holds. The expected 2329 passed / 135 skipped from the laptop did not reproduce: here 2349 passed / 116 skipped without Playwright (20 tests more run; reason not investigated). Two unexplained run anomalies (one hung run killed after more than 10 minutes near test 840 with Playwright, one run that ended at about 87 percent with no summary line): neither reproduced; both happened while other agents ran tests on the same machine.
Needed beyond the docs on a stranger's Linux machine: Pillow (2 browser tests), a matching Playwright version (1.63.0 for the preinstalled chromium 1243; latest 1.65.1 wants build 1254 and skipped all browser tests), PLAYWRIGHT_BROWSERS_PATH and node on PATH, no gitleaks (1 hygiene skip).

## CPU samples
- Sample 1 (taken early, agents starting, no test run active): load average 0.66 0.54 0.28.
- Sample 2 (BUSY label is wrong in the file name, see note): 2026-11-12T19:45:30Z, lanes 1, 4 finished; builder agents running but NO pytest process active at that moment: load average 0.42 0.83 0.87; %Cpu 5.0 us, 95.0 id; 12.2 GiB free of 16 GiB. This is NOT an idle sample of the container under test load; a true idle sample (no agent running) still has to be taken after lane 7 and the DeepSource builder finish.
