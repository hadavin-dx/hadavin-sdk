"""Lock folder probes (task 7). EVIDENCE RUNNER instrument: records what the tool does; never judges. Run as root (uid 0) unless RUN_AS is given."""
import fcntl
import json
import os
import shutil
import stat
import subprocess
import sys

WT = "/home/user/build/EV-PR89-r22"
PY = "/home/user/build/venv-evpr89r22/bin/python"
RAW = "/home/user/build/evidence-raw/PR89-c2f98f49/lock"
WORK = sys.argv[1]
os.makedirs(RAW, exist_ok=True)
DSN = "postgresql://postgres@localhost:5432/postgres"
NAME = "hadavin_mutation_locks_%d"
PG = __import__("pwd").getpwnam("postgres")

TESTSRC = '''
import os
from pk import core
MARK = %r


def test_a():
    open(os.path.join(MARK, "ran-%%d" %% os.getpid()), "w").close()
    assert core.go(1) == 1
'''


def snap(base):
    out = {}
    for top in ("tmp", "xdg", "target", "outside"):
        p = os.path.join(base, top)
        if not os.path.lexists(p):
            continue
        for dp, dn, fn in os.walk(p):
            for n in [".", *dn, *fn]:
                q = os.path.normpath(os.path.join(dp, n))
                st = os.lstat(q)
                kind = "link->" + os.readlink(q).replace(base, "<BASE>") if stat.S_ISLNK(st.st_mode) else ("dir" if stat.S_ISDIR(st.st_mode) else ("fifo" if stat.S_ISFIFO(st.st_mode) else "file"))
                out[os.path.relpath(q, base)] = f"{kind} mode={stat.S_IMODE(st.st_mode):04o} uid={st.st_uid} size={st.st_size if kind == 'file' else '-'} nlink={st.st_nlink if kind == 'file' else '-'}"
    return out


def case(cid, prepare, xdg=None, run_uid=None, hold=None):
    base = os.path.join(WORK, cid)
    shutil.rmtree(base, ignore_errors=True)
    root, tmp, mark = (os.path.join(base, x) for x in ("pkg", "tmp", "mark"))
    for d in (root + "/src/pk", root + "/tests", tmp, mark):
        os.makedirs(d)
    open(root + "/src/pk/__init__.py", "w").close()
    open(root + "/src/pk/core.py", "w").write("def go(flag):\n    return flag\n")
    open(root + "/tests/test_probe.py", "w").write(TESTSRC % mark)
    uid = run_uid if run_uid is not None else os.getuid()
    ctx = {"base": base, "tmp": tmp, "lockdir": os.path.join(tmp, NAME % uid), "uid": uid}
    prepare(ctx)
    cfg = {"wt": WT, "root": root, "tests": ["tests/test_probe.py"], "result": os.path.join(base, "result.json"), "kw": {"pass_env": ["HADAVIN_TEST_PG_DSN"]}, "mutants": []}
    json.dump(cfg, open(os.path.join(base, "cfg.json"), "w"))
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
    env["TMPDIR"] = tmp
    env["HADAVIN_TEST_PG_DSN"] = DSN
    if xdg is not None:
        env["XDG_RUNTIME_DIR"] = xdg.replace("<BASE>", base)
    before = snap(base)
    held = None
    if hold:
        held = os.open(hold.replace("<BASE>", base), os.O_RDONLY)
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    kw = {}
    if run_uid is not None:
        for dp, dn, fn in os.walk(base):
            if dp.startswith(os.path.join(base, "pkg")) or dp == base or dp.startswith(mark):
                os.chown(dp, run_uid, -1)
        os.chmod(base, 0o755)
        os.chown(base, run_uid, -1)
        kw = {"user": run_uid, "group": PG.pw_gid, "extra_groups": []}
        env["HOME"] = base
    try:
        proc = subprocess.run([PY, os.path.join(os.path.dirname(__file__), "worker.py"), os.path.join(base, "cfg.json")], env=env, capture_output=True, timeout=120, **kw)
        rc, se = proc.returncode, proc.stderr.decode("utf-8", "replace")[-400:]
        res = json.load(open(cfg["result"], encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        res, rc, se = {"harness_error": type(exc).__name__ + ": " + str(exc)[:300]}, None, ""
    if held is not None:
        os.close(held)
    after = snap(base)
    exc = res.get("exc")
    rec = {
        "case": cid, "run_as_uid": uid, "XDG_RUNTIME_DIR": "unset" if xdg is None else xdg,
        "outcome": "REFUSED" if exc else ("RAN" if res.get("rows") is not None else "HARNESS ERROR"),
        "exc_type": exc["type"] if exc else "", "message": (exc["str"] if exc else "").replace(base, "<BASE>"),
        "pytest_calls": res.get("pytest_calls"), "child_markers": len(os.listdir(mark)), "worker_rc": rc, "stderr_tail": se.replace(base, "<BASE>"),
        "harness_error": res.get("harness_error", ""),
        "before": before, "added": {k: v for k, v in after.items() if k not in before}, "changed": {k: [before[k], v] for k, v in after.items() if k in before and before[k] != v},
        "removed": [k for k in before if k not in after],
    }
    return rec


def mk(path, mode=0o700, uid=None):
    os.makedirs(path)
    os.chmod(path, mode)
    if uid is not None:
        os.chown(path, uid, -1)


LOCKFILE = "hadavin_mutation_LOCKNAME.lock"
recs = []
r0 = case("A-no-folder-xdg-unset", lambda c: None)
recs.append(r0)
names = [k for k in r0["added"] if k.endswith(".lock")]
LF = os.path.basename(names[0]) if names else None

P = []
P.append(("B-folder-is-symlink-to-own-private-dir", lambda c: (mk(c["base"] + "/target"), os.symlink(c["base"] + "/target", c["lockdir"])), None))
P.append(("B2-folder-is-dangling-symlink", lambda c: os.symlink(c["base"] + "/target", c["lockdir"]), None))
P.append(("C-folder-is-a-regular-file", lambda c: open(c["lockdir"], "w").close(), None))
P.append(("C2-folder-is-a-fifo", lambda c: os.mkfifo(c["lockdir"]), None))
P.append(("D-folder-mode-0777", lambda c: mk(c["lockdir"], 0o777), None))
P.append(("D2-folder-mode-0750", lambda c: mk(c["lockdir"], 0o750), None))
P.append(("D3-folder-mode-0701", lambda c: mk(c["lockdir"], 0o701), None))
P.append(("D4-folder-mode-0700-own", lambda c: mk(c["lockdir"], 0o700), None))
P.append(("D5-folder-mode-0500-own", lambda c: mk(c["lockdir"], 0o500), None))
P.append(("D6-folder-mode-1700-sticky", lambda c: mk(c["lockdir"], 0o1700), None))
P.append(("E-folder-owned-by-postgres-0700", lambda c: mk(c["lockdir"], 0o700, PG.pw_uid), None))
P.append(("E2-folder-owned-by-postgres-0777", lambda c: mk(c["lockdir"], 0o777, PG.pw_uid), None))


def by_postgres(c):
    os.chmod(c["tmp"], 0o1777)
    os.chmod(c["base"], 0o755)
    subprocess.run(["su", "postgres", "-c", f"mkdir -m 700 {c['lockdir']}"], check=True)


P.append(("E3-folder-made-by-the-postgres-user-itself-in-sticky-tmp", by_postgres, None))
P.append(("F-xdg-private-own-folder", lambda c: mk(c["base"] + "/xdg", 0o700), "<BASE>/xdg"))
P.append(("G-xdg-world-writable-0777", lambda c: mk(c["base"] + "/xdg", 0o777), "<BASE>/xdg"))
P.append(("G2-xdg-world-writable-1777-with-planted-symlink-lock-folder", lambda c: (mk(c["base"] + "/xdg", 0o1777), mk(c["base"] + "/target"), os.symlink(c["base"] + "/target", c["base"] + "/xdg/" + NAME % c["uid"])), "<BASE>/xdg"))
P.append(("G3-xdg-group-readable-0750", lambda c: mk(c["base"] + "/xdg", 0o750), "<BASE>/xdg"))
P.append(("H-xdg-does-not-exist", lambda c: None, "<BASE>/xdg"))
P.append(("H2-xdg-relative", lambda c: None, "xdg"))
P.append(("H3-xdg-owned-by-postgres-0700", lambda c: mk(c["base"] + "/xdg", 0o700, PG.pw_uid), "<BASE>/xdg"))
P.append(("H4-xdg-is-symlink-to-private-own-folder", lambda c: (mk(c["base"] + "/target"), os.symlink(c["base"] + "/target", c["base"] + "/xdg")), "<BASE>/xdg"))
P.append(("H5-xdg-empty-string", lambda c: None, ""))
P.append(("F2-xdg-private-with-planted-symlink-lock-folder", lambda c: (mk(c["base"] + "/xdg", 0o700), mk(c["base"] + "/target"), os.symlink(c["base"] + "/target", c["base"] + "/xdg/" + NAME % c["uid"])), "<BASE>/xdg"))
P.append(("F3-xdg-private-lock-folder-inside-0777", lambda c: (mk(c["base"] + "/xdg", 0o700), mk(c["base"] + "/xdg/" + NAME % c["uid"], 0o777)), "<BASE>/xdg"))
P.append(("T-tmpdir-read-only-0500 (root ignores modes)", lambda c: os.chmod(c["tmp"], 0o500), None))
if LF:
    def lf(c):
        mk(c["lockdir"], 0o700)
        return os.path.join(c["lockdir"], LF)

    def f_symlink(c):
        p = lf(c)
        mk(c["base"] + "/outside")
        open(c["base"] + "/outside/victim", "w").write("keep")
        os.symlink(c["base"] + "/outside/victim", p)

    def f_mode(c, mode=0o666, uid=None):
        p = lf(c)
        open(p, "w").close()
        os.chmod(p, mode)
        if uid is not None:
            os.chown(p, uid, -1)

    def f_hard(c):
        p = lf(c)
        mk(c["base"] + "/outside")
        open(c["base"] + "/outside/victim", "w").write("keep")
        os.chmod(c["base"] + "/outside/victim", 0o600)
        os.link(c["base"] + "/outside/victim", p)

    P.append(("I-lock-file-is-symlink-to-outside-file", f_symlink, None))
    P.append(("I2-lock-file-mode-0666", f_mode, None))
    P.append(("I3-lock-file-mode-0640", lambda c: f_mode(c, 0o640), None))
    P.append(("I4-lock-file-mode-0600-own", lambda c: f_mode(c, 0o600), None))
    P.append(("I5-lock-file-mode-0400-own", lambda c: f_mode(c, 0o400), None))
    P.append(("I6-lock-file-owned-by-postgres-0600", lambda c: f_mode(c, 0o600, PG.pw_uid), None))
    P.append(("I7-lock-file-is-hard-link-to-outside-file", f_hard, None))
    P.append(("I8-lock-file-is-a-fifo", lambda c: os.mkfifo(lf(c)), None))
    P.append(("I9-lock-file-is-a-folder", lambda c: os.mkdir(lf(c)), None))
for cid, prep, xdg in P:
    recs.append(case(cid, prep, xdg))
if LF:
    recs.append(case("J-lock-held-by-another-process", lambda c: f_mode(c, 0o600), None, hold="<BASE>/tmp/" + NAME % 0 + "/" + LF))
# the tool run as the postgres user (uid != 0, so file modes are enforced by the kernel)
U = PG.pw_uid
recs.append(case("U-A-as-postgres-no-folder", lambda c: os.chown(c["tmp"], U, -1), None, run_uid=U))
recs.append(case("U-E-as-postgres-folder-owned-by-root-0700", lambda c: (os.chmod(c["tmp"], 0o1777), mk(c["lockdir"], 0o700)), None, run_uid=U))
recs.append(case("U-E2-as-postgres-folder-owned-by-root-0777", lambda c: (os.chmod(c["tmp"], 0o1777), mk(c["lockdir"], 0o777)), None, run_uid=U))
recs.append(case("U-B-as-postgres-folder-is-root-made-symlink-to-postgres-private-dir", lambda c: (os.chmod(c["tmp"], 0o1777), mk(c["base"] + "/target", 0o700, U), os.symlink(c["base"] + "/target", c["lockdir"])), None, run_uid=U))
recs.append(case("U-T-as-postgres-tmpdir-read-only-0555-root-owned", lambda c: os.chmod(c["tmp"], 0o555), None, run_uid=U))
recs.append(case("U-G-as-postgres-xdg-world-writable-1777-root-planted-folder-0700", lambda c: (os.chown(c["tmp"], U, -1), mk(c["base"] + "/xdg", 0o1777), mk(c["base"] + "/xdg/" + NAME % U, 0o700)), "<BASE>/xdg", run_uid=U))
recs.append(case("U-F-as-postgres-xdg-private-own", lambda c: (os.chown(c["tmp"], U, -1), mk(c["base"] + "/xdg", 0o700, U)), "<BASE>/xdg", run_uid=U))
json.dump(recs, open(os.path.join(RAW, "lock-records.json"), "w"), indent=1)
for r in recs:
    print(f"{r['case']} | uid {r['run_as_uid']} | XDG {r['XDG_RUNTIME_DIR']} | {r['outcome']} {r['exc_type']} | pytest {r['pytest_calls']} markers {r['child_markers']} | {r['message'][:150]} {r['harness_error']}\n     added {r['added']} changed {r['changed']} removed {r['removed']} {r['stderr_tail'][-150:] if r['outcome']=='HARNESS ERROR' else ''}")
