"""Mutant runner for sonar-p3-final-v2-minors-v21-delta / -risky-v21-delta. usage: runner.py TREE GROUP [name-prefix ...]
GROUP: old (the 65 earlier mutants of the minors state, re-aimed at the v21 text) | dom (dominance mutants D, E1-E14)
       | new (v21: result-used mutants V1-V8, one per real site, echo-sanitising mutants) | risky (R01-R13 incl. R6, R7, R9)
Every mutant runs tests/test_path_confinement.py under `unshare -rn` (new network namespace, loopback up, connect blocker
from sitecustomize-q4g.py): the file holds P3's own loopback self-test that answers y. Env MUT_K narrows to a -k expression."""
import subprocess, sys, os
tree, which = sys.argv[1], sys.argv[2]
os.chdir(tree)
CI="load_tools/check_invariants.py"; LD="load_tools/load_driver.py"; P="tools/pathconfine.py"; RR="scripts/run_real_check.py"; N8="scripts/n8n_api.py"; SC="tools/scrub_n8n_export.py"; CT="load_tools/catcher.py"
G='        path = confine_existing(path, what="log file")'
T="tests/test_path_confinement.py"
OLD = [
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
 ("S03 site read_book (normal)", CI, '            path = confine_existing(path, what=f"book {shown}")', '            path = Path(path)'),
 ("S04 site read_book (anywhere)", CI, '            path = confine_anywhere(path, what=f"book {shown}")', '            path = Path(path)'),
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
 ("N14 read_book echoes the raw base name again", CI, 'shown = _shown_name(path.name)', 'shown = path.name'),
 ("N15 n8n_api import: refusal does not name LEAD_DESK_PATH_ROOTS", "scripts/n8n_api.py", 'raise SystemExit(f"cannot read a workflow: {e}. {FOLDERS_HINT}") from None', 'raise SystemExit(f"cannot read a workflow: {e}") from None'),
 ("N16 n8n_api import: no PathRefused branch (old generic message)", "scripts/n8n_api.py", '        except PathRefused as e:  # the message names the argument and the rule, never the path text', '        except ZeroDivisionError as e:  # x'),
 ("D01 read_jsonl: guard under a conditional (AST test only)", CI, '        path = confine_existing(path, what="log file")', '        path = confine_existing(path, what="log file") if path else path'),
 ("D02 _drain_marker: handler falls through (AST test only)", CI, '        path = confine_existing(path, what="--drain")\n    except PathRefused as e:\n        raise InputError(str(e)) from e', '        path = confine_existing(path, what="--drain")\n    except PathRefused:\n        pass'),
 ("D03 load_env: guard in a branch (AST test only)", "scripts/run_real_check.py", '    config = confine_anywhere(path, what="--config")\n', '    config = confine_anywhere(path, what="--config") if path else path\n'),
]
DOM = [
("D01 read_jsonl guard under conditional expr", CI, G, G+' if path else path'),
("D02 _drain_marker handler falls through", CI, '        path = confine_existing(path, what="--drain")\n    except PathRefused as e:\n        raise InputError(str(e)) from e','        path = confine_existing(path, what="--drain")\n    except PathRefused:\n        pass'),
("D03 load_env guard in branch", RR, '    config = confine_anywhere(path, what="--config")\n','    config = confine_anywhere(path, what="--config") if path else path\n'),
("E1 helper call AFTER the sink (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        obj = json.loads(path.read_text(encoding="utf-8"))', '    try:\n        obj = json.loads(path.read_text(encoding="utf-8"))'),
("E2 helper only in unreachable if False/else (read_crm)", CI, '        path = confine_existing(path, what="CRM dump")', '        if len(str(path)) > 10**9:\n            path = confine_existing(path, what="CRM dump")'),
("E3 helper in nested function never called (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    def _never() -> None:\n        confine_existing(path, what="CRM dump")\n'),
("E4 early return before helper (_intended)", CI, '    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        return int(', '    if path:\n        return int(json.loads(path.read_text(encoding="utf-8"))["intended_requests"])\n    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        return int('),
("E5 try/except that skips it (_intended)", CI, '    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        return int(', '    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused:\n        path = path\n    try:\n        return int('),
("E6 for loop zero iterations (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    for _ in [] if not path else []:\n        path = confine_existing(path, what="CRM dump")\n'),
("E6b while zero iterations (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    while not path:\n        path = confine_existing(path, what="CRM dump")\n'),
("E7 conditional expression (read_jsonl)", CI, G, '        path = confine_existing(path, what="log file") if str(path) else path'),
("E8 walrus under and (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    ok = bool(path) and (q := confine_existing(path, what="CRM dump"))\n'),
("E8b walrus certain but result unused (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    (q := confine_existing(path, what="CRM dump"))\n'),
("E9 result discarded (scrub src)", SC, '        src_path = confine_existing(src, what="in.json")', '        confine_existing(src, what="in.json")\n        src_path = Path(src)'),
("E10 contextlib.suppress around helper (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    with contextlib.suppress(Exception):\n        path = confine_existing(path, what="CRM dump")\n'),
("E11 assert guard (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    assert confine_existing(path, what="CRM dump")\n'),
("E12 match/case guard (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    match path:\n        case Path():\n            path = confine_existing(path, what="CRM dump")\n'),
("E13 helper in try-else/finally only (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    try:\n        pass\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    else:\n        confine_existing(path, what="CRM dump")\n'),
("E14 compare chain (read_crm)", CI, '    try:\n        path = confine_existing(path, what="CRM dump")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n', '    ok = (not path) < (confine_existing(path, what="CRM dump") is None)\n'),
]
RISKY13 = [
("N14 read_book echoes raw name", CI, 'name = path.name if path.name.isprintable() else "(a name with a control character)"', 'name = path.name'),
("N14b isprintable -> isascii", CI, 'path.name.isprintable()', 'path.name.isascii()'),
("N14c name check only in confine_existing branch", CI, 'path = confine_anywhere(path, what=f"book {name}")', 'path = confine_anywhere(path, what=f"book {path.name}")'),
("N15 n8n: PathRefused not caught", N8, '        except PathRefused as e:', '        except ZeroDivisionError as e:'),
("N16 n8n no roots hint", N8, 'FOLDERS_HINT = (', 'FOLDERS_HINT = "x" if True else ('),
("N17 n8n echoes the path", N8, 'raise SystemExit(f"cannot read a workflow: {e}. {FOLDERS_HINT}") from None', 'raise SystemExit(f"cannot read a workflow from {a[2]}: {e}. {FOLDERS_HINT}") from None'),
("R1 no loose-name refusal", P, '        if last and entry.name != part:', '        if False:'),
("R2 refusal for every part (folders too)", P, '        if last and entry.name != part:', '        if entry.name != part:'),
("R3 refusal only NFC-different, not case", P, '        if last and entry.name != part:', '        if last and unicodedata.normalize("NFC", entry.name) != unicodedata.normalize("NFC", part) and False:'),
("R4 wide check: root not refused", P, '    if not os.path.splitroot(real)[2]:\n        return True\n', ''),
("R5 wide check: home not refused", P, '    return os.path.normcase(real) == os.path.normcase(os.path.realpath(os.path.expanduser("~")))', '    return False'),
("R6 wide check uses unresolved home", P, 'os.path.normcase(os.path.realpath(os.path.expanduser("~")))', 'os.path.normcase(os.path.expanduser("~"))'),
("R7 cwd not realpathed", P, 'here = [r for r in [os.path.realpath(os.getcwd())] if not _is_wide(r)]', 'here = [r for r in [os.getcwd()] if not _is_wide(r)]'),
("R8 wide check removed", P, 'if not _is_wide(r)]', 'if True]'),
("R9 wide also drops extra", P, 'candidates = [*here, str(REPO_ROOT), tempfile.gettempdir(), *extra]', 'candidates = [*here, str(REPO_ROOT), tempfile.gettempdir(), *[e for e in extra if not _is_wide(os.path.realpath(e))]]'),
("R10 wide drops repo when wide", P, 'candidates = [*here, str(REPO_ROOT), tempfile.gettempdir(), *extra]', 'candidates = [*here, *([str(REPO_ROOT)] if here else []), tempfile.gettempdir(), *extra]'),
("R11 refusal message lacks cause", P, 'a file whose name differs only in Unicode form or case already exists', 'refused'),
("R12 wide: only exact root with trailing sep", P, 'if not os.path.splitroot(real)[2]:', 'if real != "/":'),
("R13 loose refusal applies to confine_existing", P, 'return Path(_locate_existing(root, _parts(relative), what))\n\n\ndef confine_anywhere', 'return Path(_locate(root, _parts(relative), what))\n\n\ndef confine_anywhere'),
]
RISKY5 = [
 ("R01 a working folder that is a file-system top is allowed", P, '    if not os.path.splitroot(real)[2]:\n        return True', '    if False:\n        return True'),
 ("R02 a working folder that is the home folder is allowed", P, '    return os.path.normcase(real) == os.path.normcase(os.path.realpath(os.path.expanduser("~")))', '    return False'),
 ("R03 working folder wide check dropped", P, 'here = [r for r in [os.path.realpath(os.getcwd())] if not _is_wide(r)]', 'here = [os.path.realpath(os.getcwd())]'),
 ("R04 a written file is found by its loose name", P, '        if last and entry.name != part:', '        if False:'),
 ("R05 folders on the way compared exactly on a write", P, '        if last and entry.name != part:', '        if entry.name != part:'),
]

SRC='        src_path = confine_existing(src, what="in.json")'
def v(k, new, expect="KILLED"): return (k, SC, SRC, new, expect)
NEW = [
 v("V1 result discarded (`_ =`), raw name used", '        _ = confine_existing(src, what="in.json")\n        src_path = Path(src)'),
 v("V2 result assigned, a different variable used", '        other = confine_existing(src, what="in.json")\n        src_path = Path(src)'),
 v("V3 helper result used only on one branch", '        src_path = confine_existing(src, what="in.json") if dst else Path(src)'),
 v("V4 helper called on a copy of the path", '        copy = src\n        confine_existing(copy, what="in.json")\n        src_path = Path(src)'),
 v("V5 bare expression statement then raw name", '        confine_existing(src, what="in.json")\n        src_path = Path(src)'),
 v("V6 variable reassigned after the helper", '        src_path = confine_existing(src, what="in.json")\n        src_path = Path(src)'),
 v("V7 sink on the original via a tuple unpack", '        _h, src_path = confine_existing(src, what="in.json"), src'),
 v("V8 FINE: Path(str(result)) (must NOT be killed)", '        src_path = Path(str(confine_existing(src, what="in.json")))', "SURVIVES"),
 ("W1 read_jsonl result discarded", CI, '        path = confine_existing(path, what="log file")', '        confine_existing(path, what="log file")', "KILLED"),
 ("W2 read_crm result in another name", CI, '        path = confine_existing(path, what="CRM dump")', '        other = confine_existing(path, what="CRM dump")', "KILLED"),
 ("W3 read_book else-branch result discarded", CI, '            path = confine_existing(path, what=f"book {shown}")', '            confine_existing(path, what=f"book {shown}")', "KILLED"),
 ("W4 _intended result discarded", CI, '    try:\n        path = confine_existing(path, what="--facts")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        return int(', '    try:\n        confine_existing(path, what="--facts")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    try:\n        return int(', "KILLED"),
 ("W5 _drain_marker result discarded", CI, '        path = confine_existing(path, what="--drain")', '        confine_existing(path, what="--drain")', "KILLED"),
 ("W6 load_driver --log result discarded", LD, '    log = confine(log, what="--log")', '    confine(log, what="--log")', "KILLED"),
 ("W7 load_driver --facts result discarded", LD, '    facts_path = confine(facts_path, what="--facts")', '    confine(facts_path, what="--facts")', "KILLED"),
 ("W8 scrub dst result discarded", SC, '        dst_path = confine(dst, what="out.json")', '        confine(dst, what="out.json")\n        dst_path = Path(dst)', "KILLED"),
 ("W9 n8n_api inline helper replaced by tuple pick", N8, 'confine_existing(a[2], what="FILE").read_text', '(confine_existing(a[2], what="FILE"), Path(a[2]))[1].read_text', "KILLED"),
 ("W10 load_env result discarded", RR, '    config = confine_anywhere(path, what="--config")', '    confine_anywhere(path, what="--config")\n    config = path', "KILLED"),
 ("W11 catcher --out result discarded", CT, '        out = confine(args.out, what="--out")', '        confine(args.out, what="--out")\n        out = args.out', "KILLED"),
 ("W12 catcher --control result discarded (not opened in this function: the AST test has no sink to see)", CT, 'control = confine(args.control or out.with_name(out.name + ".mode"), what="--control")', 'confine(args.control or out.with_name(out.name + ".mode"), what="--control"); control = args.control or out.with_name(out.name + ".mode")', "SURVIVES"),
 ("X1 _shown_name returns the raw name", CI, '    return name if name.isprintable() else "(a name with a special character)"', '    return name', "KILLED"),
 ("X2 _shown_name: isascii instead of isprintable", CI, 'return name if name.isprintable() else', 'return name if name.isascii() else', "KILLED"),
 ("X3 read_jsonl 'not JSON' echoes the raw name", CI, '{_shown_name(path.name)} line {n}: not JSON', '{path.name} line {n}: not JSON', "KILLED"),
 ("X4 read_crm 'cannot read' echoes the raw name", CI, 'cannot read CRM dump {_shown_name(path.name)}', 'cannot read CRM dump {path.name}', "KILLED"),
 ("X5 read_crm 'expected a list' echoes the raw name", CI, '{_shown_name(path.name)}: expected a list', '{path.name}: expected a list', "KILLED"),
 ("X6 read_book 'no such book' echoes the raw name", CI, 'no such book: {_shown_name(path.name)}', 'no such book: {path.name}', "KILLED"),
 ("X7 read_book 'cannot read book' echoes the raw name", CI, 'cannot read book {_shown_name(path.name)}', 'cannot read book {path.name}', "KILLED"),
 ("X8 driver facts message echoes the raw name", CI, 'cannot read the driver facts {_shown_name(path.name)}', 'cannot read the driver facts {path.name}', "KILLED"),
 ("X9 drain marker message echoes the raw name", CI, 'cannot read drain marker {_shown_name(path.name)}', 'cannot read drain marker {path.name}', "KILLED"),
 ("X10 read_jsonl 'cannot read' echoes the raw name", CI, 'cannot read {_shown_name(path.name)}:', 'cannot read {path.name}:', "KILLED"),
 ("X11 read_jsonl 'not a JSON object' echoes the raw name", CI, '{_shown_name(path.name)} line {n}: not a JSON object', '{path.name} line {n}: not a JSON object', "KILLED"),
 ("X12 n8n_api generic branch echoes the raw argument", N8, 'cannot read a workflow from {shown_arg}', 'cannot read a workflow from {a[2]}', "KILLED"),
 ("X13 n8n_api shown_arg: isascii", N8, 'a[2] if a[2].isprintable() else', 'a[2] if a[2].isascii() else', "KILLED"),
 ("X14 placeholder wording back to 'control character'", CI, '(a name with a special character)', '(a name with a control character)', "KILLED"),
]
GROUPS = {"old": [(a,b,c,d,"KILLED") for a,b,c,d in OLD], "dom": [(a,b,c,d,"KILLED") for a,b,c,d in DOM],
          "new": NEW, "risky": [(a,b,c,d,"KILLED") for a,b,c,d in RISKY13] + [(a,b,c,d,"KILLED") for a,b,c,d in RISKY5]}
M = GROUPS[which]
k_expr = os.environ.get("MUT_K"); ONLY = sys.argv[3:]
DESEL = "tests/test_path_confinement.py::test_v1_a_config_below_a_traverse_only_folder_is_refused_with_a_message_as_an_unprivileged_user"
bad = []
for k, f, a, b, expect in M:
    if ONLY and not any(k.startswith(o) for o in ONLY): continue
    orig = open(f).read()
    if orig.count(a) != 1:
        print("NOMATCH", k, orig.count(a), flush=True); bad.append(k + " (no match)"); continue
    open(f, "w").write(orig.replace(a, b, 1))
    try:
        cmd = ["unshare","-rn","python3","/tmp/demo-push/handover/demo/real-run/lo_up-q4g.py",sys.executable,"-m","pytest",T,"-q","-x","-p","no:cacheprovider","--deselect",DESEL] + (["-k", k_expr] if k_expr else [])
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=dict(os.environ, PYTHONPATH="/tmp/work/rv39-1/sc"))
        last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED","ERROR"))]
        got = "KILLED" if r.returncode else "SURVIVES"
        flag = "" if got == expect else "   <== UNEXPECTED (expected %s)" % expect
        if flag: bad.append(k)
        print(got, k, "|", (last[0][:130] if last else (r.stdout.strip().splitlines() or [r.stderr[-90:]])[-1][:90]), flag, flush=True)
    finally:
        open(f, "w").write(orig)
print("group", which, "mutants run:", len(M) if not ONLY else "subset", "unexpected:", bad)
