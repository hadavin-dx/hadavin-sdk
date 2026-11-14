#!/usr/bin/env python3
"""Scratch shim (NOT part of the repo): maps the few docker commands the evidence harness uses onto a NATIVE Postgres 16 (the disk has no room for the image). Loopback, port 55432, made-up data."""
import sys, os, subprocess, shutil, time
LB = "127.0" + ".0.1"   # loopback
B = "/usr/lib/postgresql/16/bin"; D = "/tmp/rr/pgnative/data"; PW = "/tmp/rr/pgnative/pw"; LOG = "/tmp/rr/pgnative/pg.log"
a = sys.argv[1:]
def as_pg(cmd, **k): return subprocess.run(["runuser", "-u", "postgres", "--"] + cmd, capture_output=True, text=True, **k)
def up(): return subprocess.run([B + "/pg_isready", "-h", LB, "-p", "55432"], capture_output=True).returncode == 0
c = a[0] if a else ""
if c == "ps":
    if up(): print("nativepg")
    sys.exit(0)
if c == "pull": sys.exit(0)
if c == "run":
    pw = os.environ["POSTGRES_PASSWORD"]; shutil.rmtree(D, ignore_errors=True); os.makedirs("/tmp/rr/pgnative", exist_ok=True)
    open(PW, "w").write(pw); os.chmod(PW, 0o644); shutil.chown("/tmp/rr/pgnative", "postgres")
    pwf = "/tmp/rr/pgnative/pwinit"; open(pwf, "w").write(pw); shutil.chown(pwf, "postgres")
    r = as_pg([B + "/initdb", "-D", D, "-U", "postgres", "--auth=scram-sha-256", "--pwfile=" + pwf]); os.remove(pwf)
    if r.returncode: print(r.stderr); sys.exit(1)
    r = as_pg([B + "/pg_ctl", "-D", D, "-l", LOG, "-o", "-p 55432 -c listen_addresses=" + LB + " -c unix_socket_directories=/tmp/rr/pgnative", "-w", "start"])
    if r.returncode: print(r.stderr); sys.exit(1)
    print("nativepg"); sys.exit(0)
if c == "exec":
    rest = a[2:]; pw = open(PW).read().strip()
    if rest[0] == "pg_isready": sys.exit(subprocess.run([B + "/pg_isready", "-h", LB, "-p", "55432"]).returncode)
    if rest[0] == "psql":
        r = subprocess.run([B + "/psql", "-h", LB, "-p", "55432"] + rest[1:], env=dict(os.environ, PGPASSWORD=pw), capture_output=True, text=True)
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
if c == "kill": sys.exit(as_pg([B + "/pg_ctl", "-D", D, "-m", "immediate", "stop"]).returncode)       # like docker kill: no clean shutdown
if c == "start": r = as_pg([B + "/pg_ctl", "-D", D, "-l", LOG, "-o", "-p 55432 -c listen_addresses=" + LB + " -c unix_socket_directories=/tmp/rr/pgnative", "-w", "start"]); sys.exit(r.returncode)
if c == "rm": as_pg([B + "/pg_ctl", "-D", D, "-m", "immediate", "stop"]); shutil.rmtree(D, ignore_errors=True); sys.exit(0)
sys.stderr.write("shim: unsupported docker command: %s\n" % " ".join(a)); sys.exit(2)
