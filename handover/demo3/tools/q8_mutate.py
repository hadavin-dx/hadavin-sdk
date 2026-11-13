"""Q8 mutation runner: one exact-text change per mutant, in the private worktree only. Raw logs outside git."""
import subprocess, os, sys, time, datetime, json
WT = "/home/user/work/q8-base"
F = "tools/pathconfine.py"
LOG = "/home/user/work/q8-logs"
PY = "/home/user/work/final-venv/bin/python"
env = dict(os.environ, TMPDIR="/home/user/work/q8-tmp", PYTHONPATH="src:.")
M = [
 ("M01", 'if not isinstance(path, (str, os.PathLike)):', 'if False:'),
 ("M02", 'if not isinstance(text, str):', 'if False:'),
 ("M03", 'text = str.__str__(text)', 'pass'),
 ("M04", 'if not text.strip():', 'if not text:'),
 ("M05", r'[\x00-\x1f\x7f-\x9f]")', r'[\x00-\x1f\x7f]")'),
 ("M06", r'[\x00-\x1f\x7f-\x9f]")', r'[\x01-\x1f\x7f-\x9f]")'),
 ("M07", r'[\x00-\x1f\x7f-\x9f]")', r'[\x00-\x1f\x80-\x9f]")'),
 ("M08", 'if len(text) > MAX_PATH_CHARS:', 'if len(text) >= MAX_PATH_CHARS:'),
 ("M09", 'if len(text) > MAX_PATH_CHARS:', 'if len(text) > MAX_PATH_CHARS + 1:'),
 ("M10", 'return os.path.commonpath([os.path.normcase(real), os.path.normcase(root)]) == os.path.normcase(root)', 'return True'),
 ("M11", '    except ValueError:\n        return False', '    except ValueError:\n        return True'),
 ("M12", 'if relative == os.curdir:', 'if False:'),
 ("M13", 'for root in allowed:', 'for root in allowed[:1]:'),
 ("M14", 'return os.path.realpath(text)  # follows', 'return os.path.abspath(text)  # follows'),
 ("M15", 'except (OSError, RuntimeError, ValueError) as exc:', 'except (OSError, RuntimeError) as exc:'),
 ("M16", 'if entry.is_symlink():', 'if False:'),
 ("M17", 'if last and is_folder:', 'if False:'),
 ("M18", 'if not last and not is_folder:', 'if False:'),
 ("M19", ' or name.endswith(".")', ''),
 ("M20", 'len(name) > MAX_NAME_CHARS', 'len(name) >= MAX_NAME_CHARS'),
 ("M21", 'name.split(".", 1)[0].lower() in _DEVICES', 'name.split(".", 1)[0] in _DEVICES'),
 ("M22", 'for n in range(10)})', 'for n in range(1, 10)})'),
 ("M23", 'return "".join(_NAME_CHARS[c] for c in name)', 'return name'),
 ("M24", 'unicodedata.normalize("NFC", name)', 'name'),
 ("M25", 'if loose is None and _key(e.name)', 'if loose is not None and _key(e.name)'),
 ("M26", '            if not last:\n                raise PathRefused(f"{what}: a folder on the path does not exist")', '            if False:\n                raise PathRefused(f"{what}: a folder on the path does not exist")'),
 ("M27", '            raise PathRefused(f"{what}: no such file")', '            return os.path.join(current, part)'),
 ("M28", 'if path_module.sep == "\\\\" and flat.startswith("\\\\??\\\\"):', 'if False:'),
 ("M29", '.replace("/", "\\\\")[:2] == "\\\\\\\\":', '.replace("/", "\\\\")[:2] == "xx":'),
 ("M30", 'return text  # the caller must use ONLY', 'return str(path)  # the caller must use ONLY'),
 ("M31", '.as_uri() + "?mode=ro"', '.as_uri() + ""'),
 ("M32", 'except UnicodeEncodeError:  # text', 'except KeyError:  # text'),
 ("M33", 'if not tail:\n        raise', 'if False:\n        raise'),
 ("M34", 'return drive + root, tail', 'return root, tail'),
]
only = sys.argv[1:]
def now():
    n = datetime.datetime.now(datetime.timezone.utc); i = n + datetime.timedelta(hours=5, minutes=30)
    return f"UTC {n:%Y-%m-%d %H:%M:%S} | IST {i:%Y-%m-%d %H:%M:%S}"
def sh(cmd, log, t=300):
    with open(log, "w") as fh:
        try:
            r = subprocess.run(cmd, cwd=WT, env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=t)
            return r.returncode
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
def failed(log):
    for l in open(log, errors="replace"):
        if l.startswith("FAILED") or l.startswith("ERROR"): return l.strip()[:200]
    return ""
res = []
orig = open(f"{WT}/{F}").read()
for k, (mid, old, new) in enumerate(M):
    if only and mid not in only: continue
    assert orig.count(old) == 1, (mid, orig.count(old))
    open(f"{WT}/{F}", "w").write(orig.replace(old, new))
    try:
        imp = sh([PY, "-c", "import tools.pathconfine"], f"{LOG}/{mid}-import.log", 60)
        if imp != 0:
            r = dict(id=mid, result="INVALID", by="does not import")
        else:
            rc = sh(["timeout", "300", PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--tb=no", "--basetemp=/home/user/work/q8-tmp/bt", "tests/test_path_confinement.py"], f"{LOG}/{mid}-main.log", 320)
            by = failed(f"{LOG}/{mid}-main.log")
            r = dict(id=mid, result="KILLED" if rc == 1 else ("SURVIVED" if rc == 0 else f"RC={rc}"), by=by)
            if rc == 0:
                for nm, files in (("other", ["tests/test_sonar_p2_choke_points.py", "tests/test_followup_b.py"]), ("quick", ["tests/test_n8n_api_url.py", "tests/test_load_tools.py"])):
                    rc2 = sh(["timeout", "300", PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--tb=no", "--basetemp=/home/user/work/q8-tmp/bt2", *files], f"{LOG}/{mid}-{nm}.log", 320)
                    r[nm] = "killed: " + failed(f"{LOG}/{mid}-{nm}.log") if rc2 == 1 else ("passed" if rc2 == 0 else f"RC={rc2}")
    finally:
        subprocess.run(["git", "-C", WT, "checkout", "--", F])
    r["old"], r["new"] = old, new
    res.append(r)
    with open(f"{LOG}/results.jsonl", "a") as fh: fh.write(json.dumps(r) + "\n")
    if len(res) % 5 == 0 or k == len(M) - 1:
        with open("/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q8.txt", "a") as fh:
            fh.write(f"{now()} | {len(res)} mutants done, last {mid} {r['result']}\n")
