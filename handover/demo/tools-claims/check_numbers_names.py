"""Throwaway cross-check of the docs against the code (NOT part of the repository).
Usage: python check_numbers_names.py <repo root> > numbers-names-check.md
Extracts backticked names, paths, routes and constant values from the docs and looks each up in the code."""
from __future__ import annotations

import ast
import dataclasses
import glob
import importlib
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1])
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
DOCS = ["README.md", "SECURITY.md", "versions.md", "contract.md"] + sorted(glob.glob("docs/*.md"))
CODE_DIRS = ["src", "scripts", "demo_only", "load_tools", "tools", "n8n", ".github"]
CODE_EXT = (".py", ".sh", ".ps1", ".yml", ".yaml", ".js", ".json", ".example", ".toml", ".txt", ".html", ".env")


def read(p: str) -> str:
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


code_text: dict[str, str] = {}
for d in CODE_DIRS:
    for dp, _, fns in os.walk(d):
        if "__pycache__" in dp:
            continue
        for fn in fns:
            code_text[os.path.join(dp, fn)] = read(os.path.join(dp, fn))
for fn in ("pyproject.toml", "sonar-project.properties", "patterns.txt", "exceptions.txt") + tuple(glob.glob("requirements*")):
    code_text[fn] = read(fn)
test_text = {p: read(p) for p in glob.glob("tests/*.py") + glob.glob("tests/**/*.py", recursive=True)}
ALL_CODE = "\n".join(code_text.values())
ALL_TESTS = "\n".join(test_text.values())

consts = importlib.import_module("lead_desk.constants")
CONST = {k: v for k, v in vars(consts).items() if k.isupper() and isinstance(v, (int, float)) and not isinstance(v, bool)}
cfg_mod = importlib.import_module("lead_desk.config")
CFG = {}
try:
    c = cfg_mod.Config()
    CFG = {f.name: getattr(c, f.name) for f in dataclasses.fields(c)}
except Exception as e:  # noqa: BLE001
    print(f"<!-- Config() failed: {e} -->", file=sys.stderr)

rows: list[tuple[str, str, str, str, str]] = []  # loc, claim, where, verdict, note
# Rows the script cannot judge but a person checked by hand (claim text -> reason). They print as OK-explained, never silently.
EXPLAINED = {
    "/health": "the doc says the desk has NO page at /health",
    "/fake/...": "placeholder: the dots stand for the demo servers' own addresses",
    "/review/...": "placeholder for the review routes (see the routes table)",
    "POST /review/...": "placeholder for the review routes (see the routes table)",
    "POST /crm/v3/objects/contacts/gdpr-delete": "HubSpot's address; used by scripts/hubspot_probe.py (string built from parts)",
    "POST /webhook/proof-run": "n8n adds the /webhook/ prefix; the path proof-run is in n8n/proof.json",
    "/webhook/proof-run": "n8n adds the /webhook/ prefix; the path proof-run is in n8n/proof.json",
    "result.json": "the report file name written by scripts/run_real_check.py (also in scripts/real-run.env.example)",
    "cfg.txt": "an example name in the hygiene test text, not a repository file",
    "x_api_key.txt": "an example name in the hygiene test text, not a repository file",
    "sqlite3.sqlite_version": "attribute of the Python standard library module",
    "ALLOW_ANY_BASE_URL": "suffix after the DESK_LIVE_ prefix (config.py)",
    "MESSAGE_ID_DOMAIN": "suffix after a DESK_SMTP_ or DESK_SMTPP_ prefix; found in smtp_outbox.py and smtp_provider.py",
    "MAX_SENDS": "suffix after a prefix; found in smtp_provider.py and run_real_check.py",
    "STATS_FILE": "suffix after a prefix; found in smtp_provider.py, crm_hubspot.py and run_real_check.py",
    "KEY_FILE": "suffix after a prefix; found in config.py and run_real_check.py",
    "BASE_URL": "suffix after a prefix; found in config.py and crm_hubspot.py",
    "MAX_429_RETRIES": "suffix after a prefix; found in crm_hubspot.py",
    "MISSING_SCOPES": "an error word of the HubSpot service, quoted from the author's probe run",
    "N8N_PORT": "n8n's own setting name (docs/n8n-recipe.md names it as n8n's)",
    "PLAYWRIGHT_BROWSERS_PATH": "Playwright's own setting name",
    "DESK_SMTP_HOST default 127.0.0.1": "dataclass default in smtp_outbox.py (Config().bind), not a Config field",
    "DESK_SMTP_FROM default desk@example.test": "dataclass default of the sender in smtp_outbox.py",
    "DESK_SMTP_MESSAGE_ID_DOMAIN default example.test": "dataclass default in smtp_outbox.py",
    "DESK_SMTP_TIMEOUT_SECONDS default 5.0": "dataclass default Config().send_timeout_seconds = 5.0 in smtp_outbox.py",
    "DESK_SMTPP_MESSAGE_ID_DOMAIN default example.invalid": "dataclass default in smtp_provider.py (line 87)",
    "DESK_SMTPP_TIMEOUT_SECONDS default 5.0": "dataclass default Config().send_timeout_seconds in smtp_provider.py (line 88)",
}


def add(loc, claim, where, verdict, note=""):
    if verdict in ("MISMATCH", "CANNOT-TELL") and claim in EXPLAINED:
        verdict, note = "OK-explained", EXPLAINED[claim]
    if verdict == "MISMATCH" and "MAX_HANDLER_THREADS" in claim and (" ~ 4 files" in claim or " ~ 10 s" in claim):
        verdict, note = "OK-explained", "the number belongs to the neighbouring item (4 files per thread; 10 s deadlines), not to MAX_HANDLER_THREADS (1024)"
    rows.append((loc, claim.replace("|", "/")[:150], where, verdict, note))


def word_in(text: str, w: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])", text) is not None


ENV_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")
seen: set[tuple[str, str]] = set()
for doc in DOCS:
    for ln, line in enumerate(read(doc).splitlines(), 1):
        loc = f"{doc}:{ln}"
        for m in re.finditer(r"`([^`\n]+)`", line):
            tok = m.group(1).strip()
            key = (doc, tok)
            if key in seen:
                continue
            seen.add(key)
            # (a)/(e) UPPER_CASE names: constants or env names
            if ENV_RE.match(tok):
                if tok in CONST or re.search(r"^" + re.escape(tok) + r"\b\s*[:=]", ALL_CODE, re.M) or hasattr(consts, tok):
                    add(loc, tok, "constants.py / code definition", "OK")
                elif word_in(ALL_CODE, tok):
                    add(loc, tok, "code (string or env use)", "OK")
                elif word_in(ALL_TESTS, tok):
                    add(loc, tok, "tests only", "OK-tests-only")
                elif tok.startswith(("HTTP_", "EXIT_")) or tok in ("README", "SQL", "JSON"):
                    add(loc, tok, "not found", "MISMATCH", "name not in code")
                else:
                    add(loc, tok, "grep src scripts demo_only tools .github tests", "CANNOT-TELL", "all-caps word not found in code (maybe a plain word or a foreign name)")
                continue
            # test names
            if re.match(r"^test_\w+$", tok):
                if re.search(r"def\s+" + re.escape(tok) + r"\b", ALL_TESTS):
                    add(loc, tok, "tests/ def", "OK")
                else:
                    add(loc, tok, "tests/ def", "MISMATCH", "no such test function")
                continue
            # paths (maybe with ::name or :line)
            pm = re.match(r"^((?:src|tests|scripts|demo_only|load_tools|tools|n8n|docs|\.github)/[\w./\-]+?)(?:::(\w+))?(?::\d+(?:-\d+)?)?$", tok)
            if pm and not re.search(r"[<>*{}]", tok):
                p, sub = pm.group(1), pm.group(2)
                if os.path.exists(p):
                    if sub and p.endswith(".py"):
                        ok = re.search(r"def\s+" + re.escape(sub) + r"\b", read(p))
                        add(loc, tok, p, "OK" if ok else "MISMATCH", "" if ok else "name not defined in that file")
                    else:
                        add(loc, tok, p, "OK")
                else:
                    add(loc, tok, p, "MISMATCH", "path does not exist")
                continue
            if re.match(r"^[\w./\-]+\.(?:py|md|yml|json|sh|ps1|txt|toml|js|html)$", tok) and "/" not in tok:
                base = tok
                hits = [p for p in list(code_text) + list(test_text) + DOCS if os.path.basename(p) == base] + ([base] if os.path.exists(base) else [])
                add(loc, tok, "file name anywhere in tree", "OK" if hits else "MISMATCH", "" if hits else "no file of that name")
                continue
            # routes
            rm = re.match(r"^(?:(GET|POST|PUT|DELETE|PATCH|HEAD)\s+)?(/[\w\-./<>{}:]*)(?:\?.*)?$", tok)
            if rm and len(rm.group(2)) > 1 and "/" in rm.group(2)[1:] + "/":
                path = rm.group(2)
                lit = re.split(r"[<{]", path)[0].rstrip("/")
                if not lit or lit == "/":
                    continue
                hit = lit in ALL_CODE or lit in "\n".join(code_text.get(p, "") for p in code_text if p.endswith((".js", ".html")))
                add(loc, tok, "route literal in src/demo_only", "OK" if hit else "MISMATCH", "" if hit else f"{lit} not in code")
                continue
            # identifiers with dots/calls: Desk.process, desk._call_deadline, name()
            im = re.match(r"^(?:[A-Za-z_][\w]*\.)*([A-Za-z_][\w]*)(\(\))?$", tok)
            if im and ("_" in tok or "." in tok or tok.endswith("()") or re.match(r"[A-Z][a-z]+[A-Z]\w*", tok)):
                last = im.group(1)
                if len(last) < 4 or last in {"self", "None", "True", "False"}:
                    continue
                if word_in(ALL_CODE, last) or word_in(ALL_TESTS, last):
                    add(loc, tok, "code or tests word", "OK")
                else:
                    add(loc, tok, "code and tests", "CANNOT-TELL" if tok.count(".") and tok.endswith(("py", "md")) else "MISMATCH", "name not found in code or tests")
        # numbers: `CONST` followed by a number and a unit
        for m in re.finditer(r"`([A-Z][A-Z0-9_]+)`(?:[^.`;]{0,40}?)[(=]?\s*(?:is |of |= |\()?(?:about )?(\d[\d,_.]*)\s*(s\b|seconds?|ms|milliseconds?|minutes?|bytes?|KiB|MiB|MB|KB|tries|connections|items|threads|files|lines|characters|chars)", line):
            name, num, unit = m.groups()
            if name not in CONST:
                continue
            try:
                val = float(num.replace(",", "").replace("_", ""))
            except ValueError:
                continue
            v = float(CONST[name])
            u = unit.lower()
            fac = {"s": 1, "second": 1, "seconds": 1, "ms": 1e-3, "millisecond": 1e-3, "milliseconds": 1e-3, "minute": 60, "minutes": 60, "kib": 1024, "mib": 1048576, "mb": 1e6, "kb": 1e3}.get(u, 1)
            cands = {val * fac, val}
            ok = any(abs(c - v) < 1e-9 or (v and abs(c - v) / abs(v) < 0.0005) for c in cands)
            add(f"{doc}:{ln}", f"`{name}` ~ {num} {unit}", f"constants.py {name} = {CONST[name]}", "OK" if ok else "MISMATCH", "" if ok else f"doc says {num} {unit}, code value {CONST[name]}")
        # exit codes next to EXIT_ names
        for m in re.finditer(r"`(EXIT_[A-Z_]+)`[^.;]{0,30}?\b(\d{1,3})\b", line):
            name, num = m.groups()
            if name in CONST:
                add(loc, f"`{name}` {num}", f"constants.py {name} = {CONST[name]}", "OK" if int(num) == CONST[name] else "MISMATCH")
        for m in re.finditer(r"\b(?:exit(?: code)?)\s+(\d{1,3})\b", line):
            n = int(m.group(1))
            vals = {int(v) for k, v in CONST.items() if k.startswith("EXIT_")} | {1}
            add(loc, f"exit {n}", "EXIT_* constants in constants.py (+1 for traceback)", "OK" if n in vals else "CANNOT-TELL", "" if n in vals else "not an EXIT_* value (a script of its own?)")
        # env defaults in tables: `DESK_X` ... default `v`
        for m in re.finditer(r"`(DESK_[A-Z0-9_]+)`\s*\(default `([^`]+)`", line):
            env, dv = m.groups()
            f = env[5:].lower()
            if f in CFG:
                act = CFG[f]
                ok = str(act) == dv or str(act).lower() == dv.lower() or (isinstance(act, float) and float(dv) == act) if re.match(r"^[\d.]+$", dv) or isinstance(act, str) else False
                add(loc, f"{env} default {dv}", f"Config.{f} = {act!r}", "OK" if ok else "MISMATCH", "" if ok else "default differs")
            else:
                add(loc, f"{env} default {dv}", "Config field of that name", "CANNOT-TELL", "no Config field of that name")

order = {"MISMATCH": 0, "CANNOT-TELL": 1, "OK-tests-only": 2, "OK-explained": 3, "OK": 4}
rows.sort(key=lambda r: (order[r[3]], r[0]))
from collections import Counter

cnt = Counter(r[3] for r in rows)
print("# numbers-names-check (mechanical cross-check of the docs against the code)\n")
print(f"Tree: {ROOT}. Items: {len(rows)}. " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items(), key=lambda kv: order[kv[0]])) + "\n")
print("Method: every backticked token in README, SECURITY, versions.md, contract.md, docs/*.md is classified (ALL-CAPS name, test name, repo path with optional ::test or :line, bare file name, route, identifier) and looked up in the code (src, scripts, demo_only, load_tools, tools, n8n, .github) or tests; a constant followed by a number and a unit is compared to its value in constants.py; EXIT_* numbers and `DESK_X (default `v`)` pairs are compared to the code. A name found as a word anywhere is OK (it does not prove the sentence around it is right). Not checked: numbers with no constant named next to them.\n")
print("| doc location | claim | where checked | verdict | note |\n|---|---|---|---|---|")
for r in rows:
    print("| " + " | ".join(r) + " |")
