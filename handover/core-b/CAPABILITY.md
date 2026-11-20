# CAPABILITY of core-b's cloud container (2026-11-20 05:20 UTC / 10:50 IST)
Raw output of every command: handover/core-b/evidence/capability-raw.txt

## CANNOT run
- Docker: client 29.10.0 is installed, but no Docker service is running (no /var/run/docker.sock). Nothing that needs a container can run here.
- PostgreSQL 14 and 17: not installed, and the package index offers no candidate for either (apt-cache policy printed nothing). Only PostgreSQL 16 exists here. NOT TRIED: installing 14 or 17 from another package source.
- gh (GitHub command line): version 2.89.0 is installed, but its login fails ("The token in GH_TOKEN is invalid"). Git fetch, pull and push over the session's own git remote do work.
- Session cron (CronCreate): refused by this session's permission check. See ESCALATIONS.md E1.

## CAN run
- 4 cores, 15 GB memory (0 used at probe), disk 60 GB free of 252 GB (13 percent used). User is root.
- Python 3.13.18 (default), 3.12.3 and 3.11.18 are installed; uv 0.11.32 can download 3.12.13, 3.13.14, 3.14.6.
- PostgreSQL 16.15: started and stopped a throwaway server as the postgres user on 127.0.0.1 port 55439, select version() answered. pg_ctl is not on PATH; it is at /usr/lib/postgresql/16/bin/.
- git 2.43.0, ruff 0.16.9, uv dependency resolution (uv sync --dry-run resolved; a full install and a test run were NOT done in this probe).

## Not checked
- A real pytest run (left to the lead's baselines, per the GO message item 4).
- bandit (comes through uv; not run).
