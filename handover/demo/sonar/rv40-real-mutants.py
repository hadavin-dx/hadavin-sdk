import subprocess, sys, pathlib
T = pathlib.Path(sys.argv[1])
M = [
("Q1 scrub main: walrus-in-and rebinds src_path to raw (only for names ending .raw)", "tools/scrub_n8n_export.py",
 "    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))",
 "    _ = src.endswith(\".raw\") and (src_path := Path(src))\n    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))"),
("Q2 scrub main: loop with break leaves src_path = raw", "tools/scrub_n8n_export.py",
 "    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))",
 "    for _i in src.split(\"#\"):\n        src_path = Path(src)\n        if _i:\n            break\n        src_path = confine_existing(src, what=\"in.json\")\n    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))"),
("Q3 scrub main: nested function with nonlocal swaps in raw", "tools/scrub_n8n_export.py",
 "    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))",
 "    def _swap() -> None:\n        nonlocal src_path\n        if src.endswith(\".raw\"):\n            src_path = Path(src)\n    _swap()\n    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))"),
("Q4 scrub main: list element overwritten", "tools/scrub_n8n_export.py",
 "        src_path = confine_existing(src, what=\"in.json\")\n",
 "        src_path = confine_existing(src, what=\"in.json\")\n        _box = [src_path]\n        if src.endswith(\".raw\"):\n            _box[0] = Path(src)\n        src_path = _box[0]\n"),
("Q5 scrub main: reader kept as bound method of raw path", "tools/scrub_n8n_export.py",
 "    wf = json.loads(src_path.read_text(encoding=\"utf-8\"))",
 "    _rd = (Path(src) if src.endswith(\".raw\") else src_path).read_text\n    wf = json.loads(_rd(encoding=\"utf-8\"))"),
("Q6 scrub main: dst written through os.replace of a temp file onto raw dst (op not in the sink list)", "tools/scrub_n8n_export.py",
 "    dst_path.write_text(json.dumps(scrub(wf), indent=2, ensure_ascii=False) + chr(10), encoding=\"utf-8\")",
 "    dst_path.write_text(json.dumps(scrub(wf), indent=2, ensure_ascii=False) + chr(10), encoding=\"utf-8\")\n    if dst.endswith(\".raw\"):\n        import os\n        os.replace(dst_path, dst)"),
("Q7 scrub main: src_path = confined / raw (absolute raw replaces the base)", "tools/scrub_n8n_export.py",
 "        src_path = confine_existing(src, what=\"in.json\")\n",
 "        src_path = confine_existing(src, what=\"in.json\") / (src if src.endswith(\".raw\") else \"\")\n"),
("Q8 read_jsonl: try body rebinding then handler reads (path reassigned raw before reading, inside try)", "load_tools/check_invariants.py",
 "    rows: list[dict[str, Any]] = []\n    try:\n        text = path.read_text(encoding=\"utf-8\")\n    except OSError as e:",
 "    rows: list[dict[str, Any]] = []\n    try:\n        if str(path).endswith(\".raw\"):\n            path = Path(str(path))\n        text = path.read_text(encoding=\"utf-8\")\n    except OSError as e:"),
("Q9 read_jsonl: path content as path (sink on a path read from the file)", "load_tools/check_invariants.py",
 "    rows: list[dict[str, Any]] = []\n    try:\n        text = path.read_text(encoding=\"utf-8\")\n    except OSError as e:",
 "    rows: list[dict[str, Any]] = []\n    try:\n        text = Path(path.read_text(encoding=\"utf-8\").strip()).read_text(encoding=\"utf-8\") if str(path).endswith(\".raw\") else path.read_text(encoding=\"utf-8\")\n    except OSError as e:"),
("Q10 read_jsonl: except-branch re-reads raw via .exit() object", "load_tools/check_invariants.py",
 "    try:  # a file that is read: it must exist and lie in an allowed folder (tools/pathconfine.py)\n        path = confine_existing(path, what=\"log file\")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n",
 "    try:  # a file that is read: it must exist and lie in an allowed folder (tools/pathconfine.py)\n        path = confine_existing(path, what=\"log file\")\n    except PathRefused as e:\n        raise InputError(str(e)) from e\n    except KeyError:\n        path = Path(\"x\")\n        e = ValueError()\n        e.exit = lambda: None\n        e.exit()\n"),
]
sel = ["tests/test_path_confinement.py","tests/test_load_tools.py","tests/test_scrub_n8n_export.py","tests/test_n8n_api_url.py"]
for name, rel, old, new in [m for m in M if m[0][:2] in ("Q1","Q2","Q3","Q4","Q6","Q7","Q9")]:
    f = T / rel; src = f.read_text()
    assert src.count(old) == 1, (name, src.count(old))
    f.write_text(src.replace(old, new))
    try:
        r = subprocess.run(["bash", "/tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/w/run.sh", str(T), *sel], capture_output=True, text=True)
        last = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:] 
        print(("KILLED  " if "failed" in " ".join(last) else "SURVIVES") , name, last, flush=True)
    finally:
        f.write_text(src)
