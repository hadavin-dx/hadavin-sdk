import subprocess, sys, shutil, os
os.chdir(sys.argv[1])
T = "tests/test_path_confinement.py"
P = "tools/pathconfine.py"
CI = "load_tools/check_invariants.py"
M = [
 # ---- helper (tools/pathconfine.py)
 ("M01 _inside: startswith instead of commonpath", P, 'return os.path.commonpath([os.path.normcase(real), os.path.normcase(root)]) == os.path.normcase(root)', 'return os.path.normcase(real).startswith(os.path.normcase(root))'),
 ("M02 _inside: always true", P, 'return os.path.commonpath([os.path.normcase(real), os.path.normcase(root)]) == os.path.normcase(root)', 'return True'),
 ("M03 no path-length check", P, '    if len(text) > MAX_PATH_CHARS:\n        raise PathRefused(f"{what}: path too long")\n', ''),
 ("M04 non-folder in the middle accepted", P, 'if not last and not is_folder:', 'if False:'),
 ("M05 a folder as the last name accepted", P, 'if last and is_folder:', 'if False:'),
 ("M06 no normcase in the listing match", P, 'return os.path.normcase(unicodedata.normalize("NFC", name))', 'return unicodedata.normalize("NFC", name)'),
 ("M07 no NFC in the listing match", P, 'return os.path.normcase(unicodedata.normalize("NFC", name))', 'return os.path.normcase(name)'),
 ("M08 loose match wins over exact", P, '        if e.name == part:\n            return e\n', ''),
 ("M09 no device-name check", P, '    if name.split(".", 1)[0].lower() in _DEVICES:', '    if False:'),
 ("M10 device check only without extension", P, 'name.split(".", 1)[0].lower() in _DEVICES', 'name.lower() in _DEVICES'),
 ("M11 no trailing-dot check", P, ' or name.endswith(".")', ''),
 ("M12 com0/lpt0 not devices", P, 'for n in range(10)})', 'for n in range(1, 10)})'),
 ("M13 device check case-sensitive", P, 'name.split(".", 1)[0].lower() in _DEVICES', 'name.split(".", 1)[0] in _DEVICES'),
 ("M14 no containment refusal", P, '        if _inside(real, root):\n            relative', '        if True:\n            relative'),
 ("M15 C1 controls allowed", P, r'r"[\x00-\x1f\x7f-\x9f]"', r'r"[\x00-\x1f\x7f]"'),
 ("M16 DEL allowed", P, r'r"[\x00-\x1f\x7f-\x9f]"', r'r"[\x00-\x1f\x80-\x9f]"'),
 ("M17 system temp folder not a root", P, 'candidates = [*here, str(REPO_ROOT), tempfile.gettempdir(), *extra]', 'candidates = [*here, str(REPO_ROOT), *extra]'),
 ("M18 explicit roots= not resolved", P, 'return tuple(os.path.realpath(r) for r in roots)', 'return tuple(os.path.abspath(r) for r in roots)'),
 ("M19 path equal to an allowed root accepted", P, '            if relative == os.curdir:', '            if False:'),
 ("M20 anywhere: the top itself accepted", P, '    if not tail:\n        raise PathRefused(f"{what}: names a folder, not a file")\n    return top, tail', '    return top, tail'),
 ("M21 deleted working folder: traceback", P, '    except OSError:  # the folder the tool was started in no longer exists', '    except ZeroDivisionError:  # x'),
 ("M22 repository folder not a root", P, 'candidates = [*here, str(REPO_ROOT), tempfile.gettempdir(), *extra]', 'candidates = [*here, tempfile.gettempdir(), *extra]'),
 ("M23 working folder not a root", P, '        here = [os.getcwd()]', '        here = []'),
 ("M24 LEAD_DESK_PATH_ROOTS ignored", P, 'extra = [p for p in os.environ.get(ROOTS_ENV, "").split(os.pathsep) if p]', 'extra = []'),
 ("M25 new name copied from the argument", P, '        return "".join(_NAME_CHARS[c] for c in name)', '        return name'),
 ("M26 no 255-character limit on a new name", P, 'len(name) > MAX_NAME_CHARS or ', ''),
 ("M27 a listing failure is not a refusal", P, '        raise PathRefused(f"{what}: a folder on the path cannot be listed") from None', '        return None'),
 ("M28 links not followed (abspath for realpath)", P, 'return os.path.realpath(text)  # follows', 'return os.path.abspath(text)  # follows'),
 ("M29 no link-loop check", P, '    if entry.is_symlink():', '    if False:'),
 ("M30 SQLite option mode=rw", P, '+ "?mode=ro"', '+ "?mode=rw"'),
 ("M31 SQLite path not percent-encoded", P, 'return Path(path).absolute().as_uri() + "?mode=ro"', 'return "file:" + str(Path(path).absolute()) + "?mode=ro"'),
 ("M32 confine_existing accepts a missing file", P, 'return Path(_locate_existing(root, _parts(relative), what))\n\n\ndef confine_anywhere', 'return Path(_locate(root, _parts(relative), what))\n\n\ndef confine_anywhere'),
 ("M33 confine_anywhere accepts a new name", P, '    return Path(_locate_existing(top, _parts(relative), what))', '    return Path(_locate(top, _parts(relative), what))'),
 ("M34 empty text accepted", P, 'if not isinstance(text, str) or not text.strip():', 'if not isinstance(text, str):'),
 ("M35 non-path types accepted", P, '    if not isinstance(path, (str, os.PathLike)):\n        raise PathRefused(f"{what}: not a path")\n', ''),
 ("M36 split_root drops the drive/share", P, '    return drive + root, tail', '    return root, tail'),
 ("M37 anywhere walk falls back to the raw argument", P, '    return Path(_locate_existing(top, _parts(relative), what))', '    try:\n        return Path(_locate_existing(top, _parts(relative), what))\n    except PathRefused:\n        return Path(text)'),
 ("M38 anywhere also applies containment", P, '    top, tail = _split_root(_resolve(text, what))\n', '    top, tail = _split_root(_resolve(text, what))\n    _real_inside(text, allowed_roots(), what)\n'),
 ("M39 tail match picks the loose entry only", P, '        if loose is None and _key(e.name) == _key(part):\n            loose = e\n', ''),
 ("M40 realpath errors escape (no PathRefused)", P, '    except (OSError, RuntimeError, ValueError) as exc:  # a link loop', '    except ZeroDivisionError as exc:  # a link loop'),
 # ---- one per call site: the helper call is replaced by the raw path
 ("S01 site read_jsonl", CI, '        path = confine_existing(path, what="log file")', '        path = Path(path)'),
 ("S02 site read_crm", CI, '        path = confine_existing(path, what="CRM dump")', '        path = Path(path)'),
 ("S03 site read_book (normal)", CI, '            path = confine_existing(path, what=f"book {path.name}")', '            path = Path(path)'),
 ("S04 site read_book (anywhere)", CI, '            path = confine_anywhere(path, what=f"book {path.name}")', '            path = Path(path)'),
 ("S05 site _intended", CI, 'def _intended(path: Path) -> int:\n    try:\n        path = confine_existing(path, what="--facts")', 'def _intended(path: Path) -> int:\n    try:\n        path = Path(path)'),
 ("S06 site _facts_say_live", CI, '    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused:\n        return True', '    try:\n        path = Path(path)\n    except PathRefused:\n        return True'),
 ("S07 site _drain_marker", CI, '        path = confine_existing(path, what="--drain")', '        path = Path(path)'),
 ("S08 site load_driver.run --log", "load_tools/load_driver.py", '    log = confine(log, what="--log")', '    log = Path(log)'),
 ("S09 site load_driver.run --facts", "load_tools/load_driver.py", '    facts_path = confine(facts_path, what="--facts")', '    facts_path = Path(facts_path)'),
 ("S10 site scrub read", "tools/scrub_n8n_export.py", '        src_path = confine_existing(src, what="in.json")', '        src_path = Path(src)'),
 ("S11 site scrub write", "tools/scrub_n8n_export.py", '        dst_path = confine(dst, what="out.json")', '        dst_path = Path(dst)'),
 ("S12 site n8n_api import", "scripts/n8n_api.py", 'confine_existing(a[2], what="FILE").read_text', 'Path(a[2]).read_text'),
 ("S13 site run_real_check.load_env", "scripts/run_real_check.py", '    config = confine_anywhere(path, what="--config")', '    config = Path(path)'),
 ("S14 site catcher --out", "load_tools/catcher.py", '        out = confine(args.out, what="--out")', '        out = Path(args.out)'),
 ("S15 site catcher --control", "load_tools/catcher.py", 'control = confine(args.control or out.with_name(out.name + ".mode"), what="--control")', 'control = Path(args.control or out.with_name(out.name + ".mode"))'),
 ("S16 site check_invariants.main pre-check --requests", CI, '        requests = _confined(a.requests, "--requests")', '        requests = a.requests'),
 ("S17 site check_invariants.main pre-check --json", CI, 'json_out = _confined(a.json, "--json", output=True) if a.json else None', 'json_out = a.json if a.json else None'),
 ("S18 site run_real_check sending_rows book anywhere", "scripts/run_real_check.py", 'read_book(db, anywhere=True)["followups"]', 'read_book(db)["followups"]'),
 ("S19 site run_real_check end-of-run book anywhere", "scripts/run_real_check.py", '        book = read_book(db, anywhere=True)\n', '        book = read_book(db)\n'),
]
only = sys.argv[2:] 
res = []
for k, f, a, b in M:
    if only and not any(k.startswith(o) for o in only): continue
    orig = open(f).read()
    assert orig.count(a) == 1, (k, orig.count(a))
    open(f, "w").write(orig.replace(a, b, 1))
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", T, "-q", "-x", "-p", "no:cacheprovider"], capture_output=True, text=True, timeout=400)
        last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))]
        res.append((k, "KILLED" if r.returncode else "SURVIVED", (last[0][:120] if last else "")))
    except subprocess.TimeoutExpired:
        res.append((k, "KILLED(timeout)", ""))
    finally:
        open(f, "w").write(orig)
    print(res[-1], flush=True)
print("mutants:", len(res), "killed:", sum(1 for r in res if r[1].startswith("KILLED")), "survived:", [r[0] for r in res if r[1]=="SURVIVED"])
