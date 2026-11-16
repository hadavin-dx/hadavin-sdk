import importlib.util, os, subprocess, sys, tempfile
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
work = tempfile.mkdtemp(prefix="chd.")
os.makedirs(work + "/e", exist_ok=True)
fake_git = work + "/e/git"
open(fake_git, "w").write("#!/bin/sh\necho FAKE-GIT-RAN\n"); os.chmod(fake_git, 0o755)
os.makedirs(work + "/v/.venv/bin", exist_ok=True)
fake_py = work + "/v/.venv/bin/python"
open(fake_py, "w").write("#!/bin/sh\necho FAKE-PY-RAN\n"); os.chmod(fake_py, 0o755)
os.symlink("/", work + "/lnk")
git = "/usr/bin/git" if os.path.exists("/usr/bin/git") else "/bin/git"
E = {"PATH": "/usr/bin:/bin"}
cases = [
 ("01 control ok git --version", lambda: r.Child([git, "--version"], env=E, stdout=subprocess.DEVNULL)),
 ("02 positional extra bufsize", lambda: r.Child([git, "--version"], 0, env=E)),
 ("03 positional extra executable (bufsize,executable)", lambda: r.Child([git, "--version"], -1, "/bin/sh", env=E)),
 ("04 env=None", lambda: r.Child([git, "--version"], env=None)),
 ("05 env missing", lambda: r.Child([git, "--version"])),
 ("06 env extra LD_PRELOAD", lambda: r.Child([git, "--version"], env={"PATH": "/bin", "LD_PRELOAD": "/x.so"})),
 ("07 env extra GIT_DIR", lambda: r.Child([git, "--version"], env={"PATH": "/bin", "GIT_DIR": "/x"})),
 ("08 env non-text value", lambda: r.Child([git, "--version"], env={"PATH": 1})),
 ("09 shell=True list", lambda: r.Child([git, "--version"], env=E, shell=True)),
 ("10 shell=True string", lambda: r.Child(git + " --version", env=E, shell=True)),
 ("11 executable=/bin/sh", lambda: r.Child([git, "--version"], env=E, executable="/bin/sh")),
 ("12 preexec_fn", lambda: r.Child([git, "--version"], env=E, preexec_fn=lambda: None)),
 ("13 user=0", lambda: r.Child([git, "--version"], env=E, user=0)),
 ("14 umask=0", lambda: r.Child([git, "--version"], env=E, umask=0)),
 ("15 pass_fds", lambda: r.Child([git, "--version"], env=E, pass_fds=(0,))),
 ("16 relative cwd", lambda: r.Child([git, "--version"], env=E, cwd="rel/dir")),
 ("17 cwd absolute via symlink", lambda: r.Child([git, "--version"], env=E, cwd=work + "/lnk/tmp", stdout=subprocess.DEVNULL)),
 ("18 program /bin/sh", lambda: r.Child(["/bin/sh", "-c", "echo SH-RAN"], env=E)),
 ("19 program /usr/bin/env", lambda: r.Child(["/usr/bin/env", "true"], env=E)),
 ("20 program named git elsewhere (script)", lambda: r.Child([fake_git], env=E)),
 ("21 path with .. to real git", lambda: r.Child(["/usr/../usr/bin/git", "--version"], env=E, stdout=subprocess.DEVNULL)),
 ("22 unicode lookalike (cyrillic i in git)", lambda: r.Child(["/usr/bin/gіt", "--version"], env=E)),
 ("23 8 MB argument", lambda: r.Child([git, "--version", "A" * 8_000_000], env=E)),
 ("24 NUL in argument", lambda: r.Child([git, "a\0b"], env=E)),
 ("25 args as tuple", lambda: r.Child((git, "--version"), env=E)),
 ("26 args as one string no shell", lambda: r.Child(git + " --version", env=E)),
 ("27 relative program git", lambda: r.Child(["git", "--version"], env=E)),
 ("28 fake .venv/bin/python anywhere", lambda: r.Child([fake_py], env=E)),
 ("29 start_new_session=False", lambda: r.Child([git, "--version"], env=E, start_new_session=False)),
 ("30 close_fds=False", lambda: r.Child([git, "--version"], env=E, close_fds=False)),
 ("31 process_group=0", lambda: r.Child([git, "--version"], env=E, process_group=0)),
 ("32 pipesize / unknown kw", lambda: r.Child([git, "--version"], env=E, pipesize=1)),
 ("33 many args total 8 MB (800 x 10 KB)", lambda: r.Child([git, "--version"] + ["B" * 10000] * 800, env=E)),
 ("34 program with trailing space", lambda: r.Child(["/usr/bin/git ", "--version"], env=E)),
 ("35 program path symlink named git -> /bin/sh", lambda: ((os.makedirs(work+"/s",exist_ok=True), os.symlink("/bin/sh", work + "/s/git")) if not os.path.exists(work+"/s/git") else None, r.Child([work + "/s/git", "-c", "echo SYMSH"], env=E))[1]),
]
for name, f in cases:
    try:
        p = f()
        try: out = p.communicate(timeout=20)
        except Exception: p.kill(); out = ("(wait failed)",)
        print(f"ROW|{name}|STARTED rc={p.returncode} out={str(out)[:60]!r}")
    except r.Refused as e: print(f"ROW|{name}|REFUSED: {str(e)[:100]}")
    except Exception as e: print(f"ROW|{name}|OTHER-EXC {type(e).__name__}: {str(e)[:100]}")
