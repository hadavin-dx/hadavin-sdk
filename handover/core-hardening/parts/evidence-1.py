#!/usr/bin/env python3
"""EVIDENCE RUNNER for the core-hardening static audit (AUDIT-PLAN.md step 2, R4, R5, R6).

Lists candidates and counts; never judges. Python standard library only; git is called only for
`git ls-files`, `git rev-parse`, `git branch -a` and `git remote -v`. No network, no model call.

Run from the repo root:   python3 -I handover/core-hardening/parts/evidence-1.py
Sampler (section 14):     python3 -I handover/core-hardening/parts/evidence-1.py --sample 10 --seed 7
"""

from __future__ import annotations

import argparse
import ast
import collections
import difflib
import hashlib
import importlib.metadata as imd
import random
import re
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path.cwd()
PARTS = ROOT / "handover" / "core-hardening" / "parts"
CORE = ROOT / "handover" / "core-hardening"

# ---- thresholds (R4); recorded at the top of evidence-1.md ----
THRESH = {
    "public_name": "no leading underscore",
    "dup_min_statements": 6,
    "dup_difflib_ratio": 0.80,
    "dup_ratio_text": "ast.dump text (char level, autojunk off); a token-level ratio >= 0.70 is only a pre-filter",
    "literal_min_chars": 12,
    "claims_regex": r"(\d+)\s+(tests?|modules?|kinds?|backends?|rules?) | v?\d+\.\d+\.\d+ | port\s*\d{2,5}",
    "md_cap_lines_per_subsection": 200,
    "long_literal_chars_hidden": 40,
}
CAP = THRESH["md_cap_lines_per_subsection"]

INSCOPE_HANDOVER = re.compile(
    r"^handover/(README\.md|STATUS\.md|MANIFEST-SUMMARY\.md|ledger\.md|MODEL-ROUTING\.md|"
    r"BRIEF-PREAMBLE[^/]*\.md|CLOUD-[^/]*\.md)$"
)
NO_OPEN = re.compile(r"(^|/)\.env|\.pem$|\.key$|id_rsa|\.p12$|\.pfx$|\.jks$|\.keystore$")


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, check=False)
    return p.returncode, p.stdout


def safe_line(line: str) -> str:
    s = line.strip()
    if re.search(r"""(["'])[^"'\n]{41,}\1""", s):
        return "<line holds a string literal longer than 40 chars; omitted>"
    return s[:140]


def cell(x: object) -> str:
    return str(x).replace("|", "/").replace("\n", " ").strip() or "UNVERIFIED"


def lit_show(s: str) -> str:
    h = hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:8]
    if len(s) <= 40:
        if re.search(r"AKIA|[A-Za-z0-9+/=]{32,}", s) and s != "AKIAIOSFODNN7EXAMPLE":
            return f"<secret-like literal hidden len={len(s)} sha1={h}>"
        return repr(s)
    if re.search(r"AKIA|[A-Za-z0-9+/=]{32,}", s):
        return f"<long literal len={len(s)} sha1={h}>"
    return f"{s[:30]!r}... <len={len(s)} sha1={h}>"


# ---------------------------------------------------------------- output sink
class Out:
    def __init__(self) -> None:
        self.md: list[str] = []
        self.full_files: list[str] = []

    def sec(self, sid: str, title: str, lines: list[str], cap: int = CAP, note: str = "") -> None:
        self.md.append(f"\n### {sid} {title}\n")
        if note:
            self.md.append(note + "\n")
        n = len(lines)
        if n == 0:
            self.md.append("(none found)")
            return
        if n > cap:
            fn = f"evidence-1-full-{re.sub(r'[^A-Za-z0-9]+', '_', sid)}.txt"
            (PARTS / fn).write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.full_files.append(f"{fn} ({n} lines)")
            self.md.append(f"count: {n}; showing first {cap}; full list: parts/{fn}\n")
            lines = lines[:cap]
        else:
            self.md.append(f"count: {n}\n")
        self.md.extend(lines)

    def raw(self, text: str) -> None:
        self.md.append(text)


out = Out()


# ---------------------------------------------------------------- repo model
def load_repo():
    rc, ls = git("ls-files")
    files = [f for f in ls.splitlines() if f]
    return rc, files


def module_name(path: str) -> str:
    p = path[:-3] if path.endswith(".py") else path
    if p.startswith("src/"):
        p = p[4:]
    elif p.startswith("demos/ask-your-data/"):
        p = p[len("demos/ask-your-data/"):]
    parts = p.split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def area(path: str) -> str:
    if path.startswith("src/"):
        return "src"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("demos/"):
        return "demos"
    return "other"


class Defs(ast.NodeVisitor):
    """Collect defs with line ranges and imports with a lazy flag."""

    def __init__(self) -> None:
        self.ranges: list[tuple[int, int, str]] = []
        self.imports: list[tuple[int, str, bool]] = []  # lineno, dotted, lazy
        self.stack: list[str] = []
        self.fdepth = 0

    def _def(self, node, is_func):
        self.stack.append(node.name)
        self.ranges.append((node.lineno, node.end_lineno or node.lineno, ".".join(self.stack)))
        if is_func:
            self.fdepth += 1
        self.generic_visit(node)
        if is_func:
            self.fdepth -= 1
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self._def(node, True)

    def visit_AsyncFunctionDef(self, node):
        self._def(node, True)

    def visit_ClassDef(self, node):
        self._def(node, False)

    def visit_Import(self, node):
        for a in node.names:
            self.imports.append((node.lineno, a.name, self.fdepth > 0))

    def visit_ImportFrom(self, node):
        base = node.module or ""
        if node.level:
            base = "." * node.level + base
        self.imports.append((node.lineno, base, self.fdepth > 0))
        for a in node.names:
            if a.name != "*":
                self.imports.append((node.lineno, f"{base}.{a.name}", self.fdepth > 0))


def main_run() -> int:
    t0 = time.time()
    rc_ls, files = load_repo()
    rc_sha, sha = git("rev-parse", "--short=7", "HEAD")
    sha = sha.strip()
    rc_br, branches = git("branch", "-a")
    rc_rem, remotes = git("remote", "-v")
    exit_codes = {
        "git ls-files": rc_ls,
        "git rev-parse --short=7 HEAD": rc_sha,
        "git branch -a": rc_br,
        "git remote -v": rc_rem,
    }

    def in_scope(p: str) -> bool:
        if p.startswith("handover/"):
            return bool(INSCOPE_HANDOVER.match(p))
        return True

    scope = [f for f in files if in_scope(f)]
    out_of_scope = [f for f in files if not in_scope(f)]

    texts: dict[str, str] = {}
    lines_of: dict[str, list[str]] = {}
    not_opened: list[str] = []
    for f in scope:
        if NO_OPEN.search(f):
            not_opened.append(f)
            continue
        p = ROOT / f
        try:
            if p.stat().st_size > 400_000:
                continue
            b = p.read_bytes()
            if b"\x00" in b[:2048]:
                continue
            texts[f] = b.decode("utf-8", "replace")
            lines_of[f] = texts[f].splitlines()
        except OSError:
            continue

    pyfiles = [f for f in scope if f.endswith(".py") and f in texts]
    mods: dict[str, str] = {}
    path_mod: dict[str, str] = {}
    for f in pyfiles:
        m = module_name(f)
        mods[m] = f
        path_mod[f] = m

    trees: dict[str, ast.AST] = {}
    defs: dict[str, Defs] = {}
    doc_lines: dict[str, set[int]] = {}
    parse_fail: list[str] = []
    for f in pyfiles:
        try:
            t = ast.parse(texts[f], filename=f)
        except SyntaxError as e:
            parse_fail.append(f"{f}: SyntaxError line {e.lineno}")
            continue
        trees[f] = t
        d = Defs()
        d.visit(t)
        defs[f] = d
        dl: set[int] = set()
        for n in ast.walk(t):
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                b = n.body
                if (
                    b
                    and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)
                ):
                    dl.update(range(b[0].lineno, (b[0].end_lineno or b[0].lineno) + 1))
        doc_lines[f] = dl

    def enclosing(f: str, line: int) -> str:
        best = None
        for a, b, q in defs[f].ranges if f in defs else []:
            if a <= line <= b and (best is None or (b - a) < (best[1] - best[0])):
                best = (a, b, q)
        return best[2] if best else "<module>"

    def resolve(name: str, f: str) -> str | None:
        """Longest prefix of an imported dotted name that is a first-party module."""
        if name.startswith("."):
            return None
        parts = name.split(".")
        for i in range(len(parts), 0, -1):
            c = ".".join(parts[:i])
            if c in mods:
                return c
        return None

    # edges: file -> set(module) ; lazy flags
    edges: dict[str, set[str]] = collections.defaultdict(set)
    lazy_edges: dict[tuple[str, str], bool] = {}
    third_party_full: collections.defaultdict[str, set[str]] = collections.defaultdict(set)
    for f, d in defs.items():
        for ln, dotted, lazy in d.imports:
            tgt = resolve(dotted, f)
            if tgt and tgt != path_mod[f]:
                edges[f].add(tgt)
                lazy_edges[(f, tgt)] = lazy_edges.get((f, tgt), True) and lazy
            elif not tgt and not dotted.startswith("."):
                third_party_full[dotted.split(".")[0]].add(dotted)

    importers: dict[str, set[str]] = collections.defaultdict(set)
    for f, ts in edges.items():
        for m in ts:
            importers[m].add(f)

    src_mods = sorted(m for m, f in mods.items() if f.startswith("src/"))
    src_nonpkg = [m for m in src_mods if not mods[m].endswith("__init__.py")]

    REG_FILES = [
        "src/hadavin_sdk/registry.py",
        "src/hadavin_sdk/backends/factory.py",
        "src/hadavin_sdk/backends/builtin.py",
        "src/hadavin_sdk/sources/kinds.py",
    ]
    ALSO_LAZY = ["src/hadavin_sdk/deferred.py"]

    # string constants by file (non-docstring)
    strings: dict[str, list[tuple[int, str]]] = {}
    for f, t in trees.items():
        res = []
        for n in ast.walk(t):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.lineno not in doc_lines[f]:
                res.append((n.lineno, n.value))
        strings[f] = res

    # -------- header
    rc_py = 0
    hdr = [
        "# evidence-1.md (EVIDENCE RUNNER output; lists, never judges)",
        "",
        f"- audited sha (`git rev-parse --short=7 HEAD`): {sha}",
        "- command: `python3 -I handover/core-hardening/parts/evidence-1.py` (repo root), "
        "sampler: `python3 -I handover/core-hardening/parts/evidence-1.py --sample 10 --seed 7`",
        "- SCRIPT_EXIT_CODE: PENDING",
        "- exit codes of git calls: " + "; ".join(f"`{k}` = {v}" for k, v in exit_codes.items()),
        f"- python: {sys.version.split()[0]}; run date: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC",
        "- thresholds (R4): " + "; ".join(f"{k} = {v}" for k, v in THRESH.items()),
        f"- files tracked: {len(files)}; in scope: {len(scope)}; out of scope (handover/ except the listed files): "
        f"{len(out_of_scope)}; python files parsed: {len(trees)}; parse failures: {len(parse_fail)}; "
        f"files not opened (name matches env/key pattern): {len(not_opened)}",
        "- no pytest, no mutation or plant script, no network, no model call; files written only under "
        "handover/core-hardening/parts/",
        "- shallow clone: " + ("yes (no history)" if (ROOT / ".git" / "shallow").exists() else "no"),
    ]
    if parse_fail:
        hdr += ["- parse failures: " + "; ".join(parse_fail)]
    out.raw("\n".join(hdr))

    # ============================ 1 import graph
    L = []
    for m in src_mods:
        imp = sorted(importers.get(m, ()))
        by = collections.Counter(area(x) for x in imp)
        srcs = [path_mod[x] for x in imp if area(x) == "src"]
        L.append(
            f"{m} <- src:{by['src']} tests:{by['tests']} demos:{by['demos']} | src importers: "
            f"{', '.join(srcs) or '-'} | tests: {', '.join(sorted(Path(x).name for x in imp if area(x) == 'tests')[:6]) or '-'}"
            f" | demos: {', '.join(sorted(Path(x).name for x in imp if area(x) == 'demos')) or '-'}"
        )
    out.sec("1", "Import graph: src module -> importers (lazy = import inside a function is counted too)", L, cap=CAP)

    # ============================ 2 zero importers
    reg_strings: dict[str, set[str]] = {}
    for f in REG_FILES + ALSO_LAZY:
        reg_strings[f] = {s for _, s in strings.get(f, [])}
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8")) if (ROOT / "pyproject.toml").exists() else {}
    entry_points = pyproject.get("project", {}).get("scripts", {})
    entry_mods = set()
    for _, v in entry_points.items():
        entry_mods.add(v.split(":")[0])

    def reg_hit(m: str) -> list[str]:
        stem = m.rsplit(".", 1)[-1]
        hits = []
        for f, ss in reg_strings.items():
            for s in ss:
                if s == m or s.startswith(m + ":") or s.startswith(m + ".") or s == stem:
                    hits.append(f"{f}")
                    break
        return hits

    zero, init_only, tests_only, demos_only, excluded_reg, excluded_ep, mixed_none = [], [], [], [], [], [], []
    for m in src_nonpkg:
        imp = importers.get(m, set())
        srcprod = [x for x in imp if area(x) == "src" and not x.endswith("__init__.py")]
        inits = [x for x in imp if area(x) == "src" and x.endswith("__init__.py")]
        tst = [x for x in imp if area(x) == "tests"]
        dem = [x for x in imp if area(x) == "demos"]
        if srcprod:
            continue
        tag = f"{m} ({mods[m]}) | __init__ importers: {', '.join(sorted(path_mod[x] for x in inits)) or '-'} | tests: {len(tst)} | demos: {len(dem)}"
        if m in entry_mods:
            excluded_ep.append(tag + " | pyproject entry point")
            continue
        rh = reg_hit(m)
        if rh:
            excluded_reg.append(tag + " | string in " + ", ".join(rh))
            continue
        if inits and not tst and not dem:
            init_only.append(tag)
        elif tst and not inits and not dem:
            tests_only.append(tag)
        elif dem and not inits and not tst:
            demos_only.append(tag)
        elif inits or tst or dem:
            mixed_none.append(tag)
        else:
            zero.append(tag)
    out.sec("2a", "src modules with ZERO importers anywhere (after the exclusions below)", zero)
    out.sec("2b-init", "Excluded: only importers are __init__.py re-exports", init_only)
    out.sec("2b-reg", "Excluded: name found as a string in registry.py, backends/factory.py, backends/builtin.py, sources/kinds.py or deferred.py (module has no src importer)", excluded_reg)
    out.sec("2b-entry", "Excluded: pyproject entry points", excluded_ep)
    out.sec("2c", "Referenced only by tests (no src/demos importer, no __init__, not excluded above)", tests_only)
    out.sec("2d", "Referenced only by demos", demos_only)
    out.sec("2e", "No production importer; mixture of __init__ / tests / demos importers", mixed_none)

    # suffix-string candidates for zero/tests/init-only modules
    cand = []
    reg_all = set()
    for ss in reg_strings.values():
        reg_all |= ss
    for tag in zero + tests_only + init_only + mixed_none:
        m = tag.split(" ")[0]
        stem = m.rsplit(".", 1)[-1]
        if "_" in stem:
            suf = stem.split("_", 1)[1]
            if suf in reg_all:
                cand.append(f"{m}: suffix string {suf!r} appears in a registry file (kind-name match, not a proven link)")
    out.sec("2f", "Candidates: module stem suffix equals a string literal in a registry file", cand)

    # 2b dynamic imports
    dyn = []
    dyn_re = re.compile(r"importlib\.import_module|import_module\(|__import__\(|importlib\.util|spec_from_file_location|\bgetattr\(|runpy|pkgutil")
    for f in pyfiles:
        if area(f) == "tests" and False:
            continue
        for i, line in enumerate(lines_of[f], 1):
            if dyn_re.search(line) and i not in doc_lines.get(f, ()):
                dyn.append(f"{f}:{i} [{enclosing(f, i)}] {safe_line(line)}")
    out.sec("2g-dynamic", "Dynamic-import and getattr hits (all python files; line text shown unless it holds a literal over 40 chars)", dyn)
    dl_ = []
    for f in ALSO_LAZY:
        if f in lines_of:
            for i, line in enumerate(lines_of[f], 1):
                if re.search(r"\bimport\b|lazy|load", line):
                    dl_.append(f"{f}:{i} [{enclosing(f, i)}] {safe_line(line)}")
    out.sec("2g-deferred", "deferred.py lines mentioning import / lazy / load", dl_)

    dotted_lit = []
    pref_re = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)+(:\w+)?$")
    mod_prefixes = {m.split(".")[0] for m in mods}
    for f, ss in strings.items():
        for ln, s in ss:
            if pref_re.match(s) and (s.split(":")[0].split(".")[0] in mod_prefixes or resolve(s.split(":")[0], f)):
                tgt = resolve(s.split(":")[0], f)
                dotted_lit.append(f"{f}:{ln} [{enclosing(f, ln)}] literal {s!r} -> module {tgt or 'UNRESOLVED'}")
    # f-string / concatenated prefixes
    for f, t in trees.items():
        for n in ast.walk(t):
            if isinstance(n, ast.JoinedStr) and n.values:
                first = n.values[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    v = first.value
                    if re.match(r"^(hadavin_sdk|askdata)\.[\w.]*$", v) or re.match(r"^[\w.]*\.(signer|anchor|secrets)_?$", v):
                        dotted_lit.append(f"{f}:{n.lineno} [{enclosing(f, n.lineno)}] f-string built module path prefix {v!r}")
    out.sec("2g-dotted", "String literals equal to a module dotted path (or an f-string building one), with the line where built", dotted_lit)

    # ============================ 3 public defs with zero references
    refs = {a: collections.Counter() for a in ("src", "tests", "demos")}
    doc_words = collections.Counter()
    for f, t in trees.items():
        a = area(f)
        if a == "other":
            a = "src"
        for n in ast.walk(t):
            if isinstance(n, ast.Name):
                refs[a][n.id] += 1
            elif isinstance(n, ast.Attribute):
                refs[a][n.attr] += 1
            elif isinstance(n, ast.alias):
                refs[a][n.name.split(".")[-1]] += 1
            elif isinstance(n, ast.keyword) and n.arg:
                refs[a][n.arg] += 1
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.lineno not in doc_lines[f]:
                if re.fullmatch(r"[A-Za-z_]\w*", n.value):
                    refs[a][n.value] += 1
    for f, tx in texts.items():
        if not f.endswith(".py") and f.endswith((".md", ".yml", ".yaml", ".toml", ".sh")):
            for w in re.findall(r"[A-Za-z_]\w+", tx):
                doc_words[w] += 1
    L3, L3t, L3m = [], [], []
    for f in pyfiles:
        if f not in trees or area(f) == "tests":
            continue
        t = trees[f]
        for n in t.body:  # type: ignore[attr-defined]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                nm = n.name
                rs, rt, rd = refs["src"][nm], refs["tests"][nm], refs["demos"][nm]
                kind = "class" if isinstance(n, ast.ClassDef) else "function"
                row = f"{f}:{n.lineno} {kind} {nm} refs src={rs} tests={rt} demos={rd} docs-words={doc_words[nm]}"
                if rs + rt + rd == 0:
                    L3.append(row)
                elif rs + rd == 0 and rt > 0:
                    L3t.append(row)
                if isinstance(n, ast.ClassDef):
                    for mth in n.body:
                        if isinstance(mth, (ast.FunctionDef, ast.AsyncFunctionDef)) and not mth.name.startswith("_"):
                            c = refs["src"][mth.name] + refs["tests"][mth.name] + refs["demos"][mth.name]
                            if c == 0:
                                L3m.append(f"{f}:{mth.lineno} method {nm}.{mth.name} refs by attribute/name = 0 (all areas)")
    out.sec("3a", "Public functions/classes (module level, src and demos) with ZERO references by name in src, tests, demos (definitions do not count; references = Name, Attribute, import alias, keyword, bare-identifier string)", L3)
    out.sec("3b", "Public functions/classes referenced only from tests", L3t)
    out.sec("3c", "Public methods of public classes with zero references by name (a same-named attribute anywhere counts as a reference)", L3m)

    # ============================ 4 test file -> module map
    L4 = []
    tested_by: dict[str, set[str]] = collections.defaultdict(set)
    for f in sorted(pyfiles):
        if area(f) != "tests":
            continue
        ts = sorted(m for m in edges.get(f, ()) if mods[m].startswith(("src/", "demos/")))
        for m in ts:
            tested_by[m].add(f)
        helper = sorted(x for x in (edges.get(f, set())) if mods[x].startswith("tests/"))
        ntests = sum(1 for n in ast.walk(trees[f]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")) if f in trees else 0
        L4.append(f"{f} (def test_: {ntests}) -> {', '.join(ts) or '-'} | test helpers: {', '.join(helper) or '-'}")
    out.sec("4a", "Test file -> modules it imports (src and demos), plus test helper modules imported", L4)
    L4b = [f"{m} ({mods[m]})" for m in src_nonpkg if not tested_by.get(m)]
    out.sec("4b", "src modules (non-package) imported by NO test file", L4b)
    L4c = []
    for f in sorted(pyfiles):
        if area(f) != "tests":
            continue
        for ln, dotted, _ in defs[f].imports if f in defs else []:
            if dotted.startswith(("hadavin_sdk.", "askdata.")) and not resolve(dotted, f):
                L4c.append(f"{f}:{ln} import {dotted} (no first-party module resolves)")
            elif dotted.startswith(("hadavin_sdk.", "askdata.")):
                tgt = resolve(dotted, f)
                if tgt and tgt != dotted:
                    # name imported from module: check defined name exists
                    nm = dotted[len(tgt) + 1:].split(".")[0]
                    tf = mods[tgt]
                    if nm and tf in trees:
                        top = {x.name for x in ast.iter_child_nodes(trees[tf]) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
                        assigns = set()
                        for x in ast.iter_child_nodes(trees[tf]):
                            if isinstance(x, ast.Assign):
                                for tg in x.targets:
                                    if isinstance(tg, ast.Name):
                                        assigns.add(tg.id)
                            elif isinstance(x, ast.AnnAssign) and isinstance(x.target, ast.Name):
                                assigns.add(x.target.id)
                            elif isinstance(x, (ast.Import, ast.ImportFrom)):
                                for a_ in x.names:
                                    assigns.add((a_.asname or a_.name).split(".")[0])
                        if nm not in top and nm not in assigns and nm not in mods and f"{tgt}.{nm}" not in mods and "__getattr__" not in texts.get(tf, ""):
                            L4c.append(f"{f}:{ln} imports name {nm} from {tgt}: not defined at module level there (candidate: removed or renamed code)")
    out.sec("4c", "Test imports whose names do not resolve in src/demos (candidates: tests for removed code)", L4c)

    # ============================ 5 state, log and retry patterns ; 6 credentials/egress/personal
    TEXT_EXT = (".py", ".yml", ".yaml", ".sh")
    pat5 = {
        "sqlite3": r"sqlite3|\.sqlite",
        "open-write": r"""\bopen\([^)]*['"][rwabx+]*[wax+][rwabx+]*['"]""",
        "write_text": r"\.write_text\(",
        "write_bytes": r"\.write_bytes\(",
        "jsonl": r"\.jsonl",
        "psycopg": r"psycopg",
        "DSN": r"\bDSN\b|\bdsn\b",
        "getLogger": r"logging\.getLogger|getLogger\(",
        "retry": r"retry|retries",
        "backoff": r"backoff",
        "timeout": r"timeout",
        "sleep": r"\bsleep\(",
        "max_attempts": r"max_attempts",
    }
    pat6 = {
        "environ": r"environ",
        "getenv": r"getenv",
        "secret": r"secret",
        "token": r"token",
        "urllib": r"urllib",
        "http.client": r"http\.client",
        "requests": r"\brequests\b",
        "httpx": r"httpx",
        "boto3": r"boto3",
        "socket": r"\bsocket\b",
        "email": r"email",
        "phone": r"phone",
        "retention": r"retention",
        "ttl": r"\bttl\b|_ttl|ttl_",
        "pii": r"\bpii\b|_pii|pii_",
    }
    cre5 = {k: re.compile(v, re.I if k not in ("open-write",) else 0) for k, v in pat5.items()}
    cre6 = {k: re.compile(v, re.I) for k, v in pat6.items()}
    hits5: dict[str, list[tuple[int, str, str, str]]] = collections.defaultdict(list)
    hits6: dict[str, list[tuple[int, str, str, str]]] = collections.defaultdict(list)
    ident = re.compile(r"[\w.]+")

    def collect(f: str, pats, store, allow_docs: bool = False):
        ls = lines_of[f]
        dl = doc_lines.get(f, set())
        for i, line in enumerate(ls, 1):
            ctx = "doc" if i in dl else ("comment" if line.lstrip().startswith("#") else "code")
            for k, rx in pats.items():
                m = rx.search(line)
                if not m:
                    continue
                # identifier containing the match
                s, e = m.span()
                a = s
                while a > 0 and (line[a - 1].isalnum() or line[a - 1] in "._"):
                    a -= 1
                b = e
                while b < len(line) and (line[b].isalnum() or line[b] in "._"):
                    b += 1
                idn = line[a:b][:60]
                store[f].append((i, k, ctx, idn))

    for f in scope:
        if f not in texts or not f.endswith(TEXT_EXT):
            continue
        collect(f, cre5, hits5)
        collect(f, cre6, hits6)

    def table(hits, pats):
        rows = []
        for f in sorted(hits):
            c = collections.Counter(k for (_, k, ctx, _) in hits[f] if ctx == "code")
            if c:
                rows.append(f"{f} | " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
        return rows

    out.sec("5a", "Per-file counts of state/log/retry pattern hits (code lines only; comments and docstrings counted separately in 5b)", table(hits5, pat5))
    l5 = []
    for f in sorted(hits5):
        for i, k, ctx, idn in hits5[f]:
            l5.append(f"{f}:{i} {k} [{ctx}] [{enclosing(f, i) if f in defs else '-'}] {idn}")
    out.sec("5b", "Every pattern hit: file:line pattern [line kind] [enclosing def] identifier (lines kept in full file)", l5)
    out.sec("6a", "Per-file counts of credential, egress and personal-data-word hits (names only, code lines only)", table(hits6, pat6))
    l6 = []
    for f in sorted(hits6):
        for i, k, ctx, idn in hits6[f]:
            l6.append(f"{f}:{i} {k} [{ctx}] [{enclosing(f, i) if f in defs else '-'}] {idn}")
    out.sec("6b", "Every credential/egress/personal-data-word hit: file:line pattern [line kind] [enclosing def] identifier", l6)
    env_names = collections.defaultdict(set)
    for f in pyfiles:
        for ln, s in strings.get(f, []):
            if re.fullmatch(r"[A-Z][A-Z0-9_]{3,}", s) and any(w in s for w in ("KEY", "TOKEN", "SECRET", "URL", "DSN", "HOST", "ENDPOINT", "PASSWORD", "REGION", "PROFILE", "PORT", "CREDENTIAL")):
                env_names[s].add(f"{f}:{ln}")
    out.sec("6c", "Upper-case configuration/credential NAMES found as string literals (names only, first 3 locations)", [f"{k} <- {', '.join(sorted(v)[:3])}" for k, v in sorted(env_names.items())])

    # ============================ 7 claims
    doc_files = [f for f in scope if f.endswith(".md") and f in texts]
    claim_re = re.compile(r"(\d+)\s+(tests?|modules?|kinds?|backends?|rules?)\b", re.I)
    ver_re = re.compile(r"v?\d+\.\d+\.\d+")
    port_re = re.compile(r"port\s*\d{2,5}", re.I)
    pj_versions = {pyproject.get("project", {}).get("version", "")}
    for dep in pyproject.get("project", {}).get("dependencies", []):
        pj_versions.add(dep.split("==")[-1])
    for ex in pyproject.get("project", {}).get("optional-dependencies", {}).values():
        for dep in ex:
            pj_versions.add(dep.split("==")[-1])
    for g in pyproject.get("dependency-groups", {}).values():
        for dep in g:
            pj_versions.add(dep.split("==")[-1])
    cl_counts, cl_ver, cl_port = [], [], []
    for f in doc_files:
        for i, line in enumerate(lines_of[f], 1):
            for m in claim_re.finditer(line):
                cl_counts.append(f"{f}:{i} claim {m.group(0)!r} | {safe_line(line)}")
            for m in ver_re.finditer(line):
                v = m.group(0).lstrip("v")
                cl_ver.append(f"{f}:{i} version {m.group(0)} matches-a-pyproject-pin-or-project-version={'yes' if v in pj_versions else 'no'}")
            for m in port_re.finditer(line):
                cl_port.append(f"{f}:{i} {m.group(0)!r}")
    # actual counts
    n_def_test, per_dir = 0, collections.Counter()
    test_files = [f for f in pyfiles if f.startswith("tests/") and Path(f).name.startswith("test_")]
    for f in pyfiles:
        if f.startswith("tests/") and f in trees:
            c = sum(1 for n in ast.walk(trees[f]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_"))
            n_def_test += c
            per_dir[str(Path(f).parent)] += c
    src_py = [f for f in pyfiles if f.startswith("src/")]
    kinds = collections.defaultdict(list)
    for f in src_py:
        st = Path(f).stem
        for pre in ("secrets_", "signer_", "anchor_"):
            if st.startswith(pre):
                kinds[pre.rstrip("_")].append(st)
    llm_backends = sorted(Path(f).stem for f in src_py if "/llm/" in f and Path(f).stem not in ("__init__", "common", "protocol", "retry"))
    facts = [
        f"count `def test_` / `async def test_` by ast in tests/**/*.py: {n_def_test} (in {len(test_files)} test_*.py files; per dir: {dict(per_dir)}); parametrized cases not expanded; pytest NOT run: every doc test-count claim is UNVERIFIED-against-pytest",
        f"python files under src/: {len(src_py)} (non-__init__: {len([f for f in src_py if not f.endswith('__init__.py')])})",
        f"files by kind prefix: " + "; ".join(f"{k}: {len(v)} {sorted(v)}" for k, v in sorted(kinds.items())),
        f"llm backend module candidates (src/hadavin_sdk/llm minus common/protocol/retry): {len(llm_backends)} {llm_backends}",
        f"pyproject project.version = {pyproject.get('project', {}).get('version')}; requires-python = {pyproject.get('project', {}).get('requires-python')}",
        f"test_*.py counts by dir: " + str(dict(collections.Counter(str(Path(f).parent) for f in test_files))),
        f".claude/rules files: {len([f for f in scope if f.startswith('.claude/rules/')])}",
    ]
    out.sec("7a", "Actual counts (computed)", facts)
    out.sec("7b", "Doc claims of the form '<n> tests|modules|kinds|backends|rules' (file:line, claim text, line)", cl_counts)
    out.sec("7c", "Doc version strings and whether the number equals a pyproject pin or the project version", cl_ver)
    # ports vs code literals
    code_ports = []
    for f in pyfiles:
        for i, line in enumerate(lines_of[f], 1):
            if i in doc_lines.get(f, ()):
                continue
            if re.search(r"port\W{0,4}\d{2,5}|PORT\w*\W+\d{2,5}|:\d{4,5}\b", line, re.I) and not line.lstrip().startswith("#"):
                m = re.search(r"\d{2,5}", line[re.search(r"port|:\d{4,5}", line, re.I).start():])  # type: ignore[union-attr]
                code_ports.append(f"{f}:{i} [{enclosing(f, i)}] port-like number {m.group(0) if m else '?'}")
    out.sec("7d", "Doc port claims ('port NNNN')", cl_port)
    out.sec("7e", "Code port-like literals", code_ports)
    # file-name claims
    ext = r"(?:py|md|yml|yaml|json|jsonl|toml|sh|txt|sql|csv|html|cfg)"
    nm_re = re.compile(r"`([\w./-]+\.%s)`" % ext)
    all_files = set(files)
    by_base = collections.defaultdict(list)
    for f in files:
        by_base[Path(f).name].append(f)
    missing = []
    total_claims = 0
    for f in doc_files:
        if f.startswith("handover/"):
            continue
        for i, line in enumerate(lines_of[f], 1):
            for m in nm_re.finditer(line):
                nm = m.group(1)
                total_claims += 1
                if nm in all_files or any(x.endswith("/" + nm) for x in all_files) or nm in by_base:
                    continue
                missing.append(f"{f}:{i} names file `{nm}`: no tracked path equals it or ends with it, no tracked file has that base name")
    out.sec("7f", f"Back-ticked file names in docs (non-handover) that match NO tracked file (checked {total_claims} names)", missing)

    # ============================ 8 dependencies
    stdlib = set(sys.stdlib_module_names)
    first_party = {m.split(".")[0] for m in mods} | {"tests", "conftest", "hadavin_sdk", "askdata"}
    declared: dict[str, list[str]] = {}
    pp = pyproject.get("project", {})

    def add(dep, where):
        name = re.split(r"[\[<>=!~ ;]", dep, maxsplit=1)[0]
        declared.setdefault(name, []).append(where)

    for d in pp.get("dependencies", []):
        add(d, "dependencies")
    for k, v in pp.get("optional-dependencies", {}).items():
        for d in v:
            add(d, f"extra:{k}")
    for k, v in pyproject.get("dependency-groups", {}).items():
        for d in v:
            add(d, f"group:{k}")
    for d in pyproject.get("build-system", {}).get("requires", []):
        add(d, "build-system")
    norm = lambda s: re.sub(r"[-_.]+", "-", s).lower()  # noqa: E731
    try:
        pd = imd.packages_distributions()
    except Exception:  # noqa: BLE001
        pd = {}
    inv: dict[str, list[str]] = collections.defaultdict(list)
    for top, ds in pd.items():
        for d in ds:
            inv[norm(d)].append(top)
    table_map = {
        "pyyaml": ["yaml"], "markdown-it-py": ["markdown_it"], "pydantic": ["pydantic"],
        "pydantic-settings": ["pydantic_settings"], "anthropic": ["anthropic"], "boto3": ["boto3", "botocore"],
        "cryptography": ["cryptography"], "psycopg": ["psycopg"], "sqlglot": ["sqlglot"],
        "azure-identity": ["azure.identity"], "azure-keyvault-keys": ["azure.keyvault.keys"],
        "azure-keyvault-secrets": ["azure.keyvault.secrets"], "azure-storage-blob": ["azure.storage.blob"],
        "google-cloud-kms": ["google.cloud.kms"], "google-cloud-secret-manager": ["google.cloud.secretmanager"],
        "google-cloud-storage": ["google.cloud.storage"], "moto": ["moto"], "pglast": ["pglast"],
        "pytest": ["pytest", "_pytest"], "ruff": [], "pip-audit": [], "bandit": [], "zizmor": [],
        "uv-build": [],
    }
    imported_all = set()
    for f, d in defs.items():
        for ln, dotted, lazy in d.imports:
            if not dotted.startswith(".") and dotted.split(".")[0] not in stdlib and dotted.split(".")[0] not in first_party:
                imported_all.add(dotted)
    L8 = []
    unmapped = []
    covered_imports = set()
    for dist, wheres in sorted(declared.items()):
        n = norm(dist)
        prefixes = table_map.get(n) or inv.get(n)
        src_of = "table" if n in table_map else ("site-packages top_level" if inv.get(n) else "UNMAPPED")
        if prefixes is None:
            unmapped.append(dist)
            L8.append(f"{dist} [{', '.join(wheres)}] -> import names UNMAPPED")
            continue
        used = sorted(i for i in imported_all if any(i == p or i.startswith(p + ".") or p.startswith(i + ".") for p in prefixes))
        covered_imports |= set(used)
        files_using = sorted({f for f, d in defs.items() for ln, dotted, _ in d.imports if dotted in used})
        L8.append(f"{dist} [{', '.join(wheres)}] map({src_of})={prefixes} -> imported as {used[:4] or 'NOT IMPORTED'} in {len(files_using)} files {files_using[:3]}")
    out.sec("8a", "Declared dependency (pyproject: dependencies, extras, groups, build) -> import names mapped and whether any python file imports them", L8)
    lock_names = []
    if (ROOT / "uv.lock").exists():
        try:
            lk = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
            lock_names = sorted(p["name"] for p in lk.get("package", []))
        except Exception as e:  # noqa: BLE001
            lock_names = [f"uv.lock parse error {type(e).__name__}"]
    decl_norm = {norm(d) for d in declared}
    out.sec("8b", f"Imported third-party names NOT covered by a declared dependency mapping (top-level shown; {len(lock_names)} packages in uv.lock)",
            [f"{i} (first dist-name match in uv.lock: {'yes' if norm(i.split('.')[0]) in {norm(x) for x in lock_names} else 'no'})" for i in sorted(imported_all - covered_imports)])
    out.sec("8c", "uv.lock package names that are neither declared in pyproject nor imported by top-level name (transitive candidates; list only)",
            [x for x in lock_names if norm(x) not in decl_norm and norm(x).replace("-", "_") not in {i.split(".")[0] for i in imported_all}][:2000])
    out.sec("8d", "Dist names with no import-name mapping (not in site-packages, not in the written table)", unmapped)

    # ============================ 9 duplicates
    out.raw("\n## 9 Duplicate candidates")
    funcs = []  # (file, qual, node)
    for f in pyfiles:
        if f not in trees or area(f) == "tests":
            continue
        for n in ast.walk(trees[f]):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nstm = sum(1 for x in ast.walk(n) if isinstance(x, ast.stmt)) - 1
                if nstm >= THRESH["dup_min_statements"]:
                    body = list(n.body)
                    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                        body = body[1:]
                    dump = "".join(ast.dump(b, annotate_fields=True, include_attributes=False) for b in body)
                    funcs.append((f, n.name, n.lineno, nstm, dump))
    byhash = collections.defaultdict(list)
    for f, nm, ln, ns, dump in funcs:
        byhash[hashlib.sha1(dump.encode()).hexdigest()].append((f, nm, ln, ns))
    exact = [f"hash {h[:8]} ({v[0][3]} stmts): " + "; ".join(f"{a}:{c} {b}" for a, b, c, _ in v) for h, v in byhash.items() if len(v) > 1]
    out.sec("9a", "Exact AST-hash equal function bodies (>= 6 statements, docstring removed, argument names kept)", exact)
    tok = [re.findall(r"\w+", d) for *_, d in funcs]
    pairs = []
    t_start = time.time()
    for i in range(len(funcs)):
        fi = funcs[i]
        for j in range(i + 1, len(funcs)):
            fj = funcs[j]
            if fi[0] == fj[0] and fi[1] == fj[1]:
                continue
            la, lb = len(fi[4]), len(fj[4])
            if min(la, lb) / max(la, lb) < 0.75:
                continue
            if fi[4] == fj[4]:
                continue
            sm = difflib.SequenceMatcher(None, tok[i], tok[j], autojunk=False)
            if sm.real_quick_ratio() < 0.7 or sm.quick_ratio() < 0.7 or sm.ratio() < 0.70:
                continue
            r = difflib.SequenceMatcher(None, fi[4], fj[4], autojunk=False).ratio()
            if r >= THRESH["dup_difflib_ratio"]:
                pairs.append((r, f"{fi[0]}:{fi[2]} {fi[1]} <-> {fj[0]}:{fj[2]} {fj[1]} ratio={r:.3f} stmts={fi[3]}/{fj[3]}"))
    pairs.sort(key=lambda x: -x[0])
    out.sec("9b", f"Function pairs with difflib ratio >= 0.80 on ast.dump text, bodies >= 6 statements (pairs compared across all src and demos functions; {len(funcs)} functions; {time.time() - t_start:.0f}s)", [p for _, p in pairs])

    names = collections.defaultdict(list)
    for f in pyfiles:
        if f not in trees or area(f) == "tests":
            continue
        for n in trees[f].body:  # type: ignore[attr-defined]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                names[n.name].append(f"{f}:{n.lineno}")
    out.sec("9c", "Same-named public functions/classes in different files (src and demos)", [f"{k}: " + "; ".join(v) for k, v in sorted(names.items()) if len({x.split(':')[0] for x in v}) > 1])

    lits = collections.defaultdict(list)
    rx_lits = collections.defaultdict(list)
    for f, t in trees.items():
        if area(f) == "tests":
            continue
        rxl = set()
        for n in ast.walk(t):
            if isinstance(n, ast.Call):
                fn = n.func
                if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "re" and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    rxl.add(n.args[0].lineno)
                    if len(n.args[0].value) >= THRESH["literal_min_chars"]:
                        rx_lits[n.args[0].value].append(f"{f}:{n.args[0].lineno}")
        for ln, s in strings.get(f, []):
            if len(s) >= THRESH["literal_min_chars"] and ln not in rxl:
                lits[s].append(f"{f}:{ln}")
    out.sec("9d", "Duplicate regex literals (passed to re.*, >= 12 chars) appearing in 2 or more files",
            [f"{lit_show(k)} in {len({x.split(':')[0] for x in v})} files: " + "; ".join(sorted(set(v))[:4]) for k, v in sorted(rx_lits.items(), key=lambda kv: -len(kv[1])) if len({x.split(':')[0] for x in v}) > 1])
    out.sec("9e", "Duplicate string literals (>= 12 chars, not docstrings, not regexes) appearing in 2 or more files (src and demos)",
            [f"{lit_show(k)} in {len({x.split(':')[0] for x in v})} files: " + "; ".join(sorted(set(v))[:4]) for k, v in sorted(lits.items(), key=lambda kv: -len(kv[1])) if len({x.split(':')[0] for x in v}) > 1])

    # demo vs core (R5)
    R5 = {
        "audit": ["audit/chain.py", "audit/local_dir.py"],
        "ledger": ["limits.py", "stats.py", "audit/"],
        "meter": ["limits.py", "stats.py", "audit/"],
        "policy": ["guard/", "actions/authorizer.py"],
        "config": ["config.py", "defaults.py"],
        "pgsource": ["store/postgres.py", "sources/"],
        "safe_text": ["guard/redact.py", "scrub_settings.py", "guard/injection.py"],
        "validate": ["guard/redact.py", "scrub_settings.py", "guard/injection.py"],
        "allowed": ["guard/redact.py", "scrub_settings.py", "guard/injection.py"],
        "prompt": ["llm/", "evals.py"],
        "llm_io": ["llm/", "evals.py"],
        "compare": ["llm/", "evals.py"],
    }
    core_base = "src/hadavin_sdk/"
    demo_files = sorted(f for f in pyfiles if f.startswith("demos/ask-your-data/askdata/"))
    L9 = []
    for df in demo_files:
        st = Path(df).stem
        if st not in R5:
            L9.append(f"{df} | no core counterpart: not in the R5 pair list")
            continue
        cands = []
        for pat in R5[st]:
            if pat.endswith("/"):
                cands += [f for f in pyfiles if f.startswith(core_base + pat)]
            else:
                if core_base + pat in texts:
                    cands.append(core_base + pat)
                else:
                    L9.append(f"{df} | R5 core file {core_base + pat} does not exist in the tree")
        rs = []
        a = lines_of[df]
        for c in sorted(set(cands)):
            r = difflib.SequenceMatcher(None, a, lines_of[c], autojunk=False).ratio()
            rs.append((r, c))
        rs.sort(reverse=True)
        L9.append(f"{df} | best 3 line-level ratios: " + "; ".join(f"{c} {r:.3f}" for r, c in rs[:3]))
    out.sec("9f", "Demo module (demos/ask-your-data/askdata) -> best three line-level difflib ratios against the R5 core pair list", L9)

    # parity of kinds
    L9g = []
    fam = {"secrets": "secrets_", "signer": "signer_", "anchor": "anchor_"}
    for fname, pre in fam.items():
        members = sorted(f for f in src_py if Path(f).stem.startswith(pre))
        base = sorted(f for f in src_py if Path(f).stem in (fname, fname + "s", "protocol", "anchors") and Path(f).parent == (Path(members[0]).parent if members else Path(".")))
        meth: dict[str, set[str]] = {}
        classes: dict[str, list[str]] = {}
        for f in members + base:
            if f not in trees:
                continue
            ms, cs = set(), []
            for n in trees[f].body:  # type: ignore[attr-defined]
                if isinstance(n, ast.ClassDef) and not n.name.startswith("_"):
                    cs.append(n.name)
                    for x in n.body:
                        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and not x.name.startswith("_"):
                            ms.add(f"{n.name}.{x.name}")
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
                    ms.add(f"fn:{n.name}")
            meth[f] = ms
            classes[f] = cs
        allm = sorted({m.split(".")[-1] for ms in meth.values() for m in ms})
        L9g.append(f"## family {fname}: members {[Path(f).name for f in members]} base files {[Path(f).name for f in base]}")
        for f in members + base:
            if f not in meth:
                continue
            have = {m.split(".")[-1] for m in meth[f]}
            tests_named = sorted(
                t for t in test_files
                if Path(f).stem in texts[t] or any(c in texts[t] for c in classes.get(f, []))
            )
            L9g.append(
                f"- {f} classes={classes.get(f)} | lacks (vs union of family public names): {[m for m in allm if m not in have][:12]} | "
                f"test files naming the module or its classes: {tests_named[:8] or 'no test found by grep for ' + Path(f).stem}"
            )
    out.sec("9g", "Parity table of secrets_*, signer_*, anchor_* kinds: public names per member and test files that name each", L9g, cap=CAP)
    # llm backends parity
    L9h = []
    llmf = sorted(f for f in src_py if "/llm/" in f)
    for f in llmf:
        if f not in trees:
            continue
        cs = [n.name for n in trees[f].body if isinstance(n, ast.ClassDef) and not n.name.startswith("_")]  # type: ignore[attr-defined]
        tn = sorted(t for t in test_files if Path(f).stem in texts[t] or any(c in texts[t] for c in cs))
        L9h.append(f"{f} classes={cs} | test files naming it: {tn[:8] or 'no test found by grep for ' + Path(f).stem}")
    out.sec("9h", "llm backends: public classes and test files that name each", L9h)

    series = collections.defaultdict(list)
    for f in test_files:
        series[re.sub(r"\d+", "#", Path(f).name)].append(f)
    L9i = []
    for k, v in sorted(series.items()):
        if len(v) > 1:
            v = sorted(v)
            for a_, b_ in zip(v, v[1:]):
                r = difflib.SequenceMatcher(None, lines_of[a_], lines_of[b_], autojunk=False).ratio()
                L9i.append(f"{k}: {a_} <-> {b_} line-level ratio {r:.3f}")
    out.sec("9i", "Test files whose names differ only by a number (consecutive pairs) and their ratio", L9i)

    # ============================ 11 reachability
    adj: dict[str, set[str]] = collections.defaultdict(set)  # module -> modules
    for f, ts in edges.items():
        m = path_mod[f]
        adj[m] |= ts
    # parent packages
    def parents(m: str) -> list[str]:
        ps = m.split(".")
        return [".".join(ps[:i]) for i in range(1, len(ps)) if ".".join(ps[:i]) in mods]

    str_edges: dict[str, set[str]] = collections.defaultdict(set)
    for f in pyfiles:
        if f not in strings:
            continue
        for ln, s in strings[f]:
            if pref_re.match(s):
                t = resolve(s.split(":")[0], f)
                if t:
                    str_edges[path_mod[f]].add(t)
    for f in REG_FILES + ALSO_LAZY:
        if f not in path_mod:
            continue
        for ln, s in strings.get(f, []):
            for m in src_nonpkg:
                if s == m.rsplit(".", 1)[-1]:
                    str_edges[path_mod[f]].add(m)

    def closure(roots: set[str], use_str: bool = True) -> set[str]:
        seen: set[str] = set()
        stack = list(roots)
        while stack:
            m = stack.pop()
            if m in seen or m not in mods:
                continue
            seen.add(m)
            stack += parents(m)
            stack += list(adj.get(m, ()))
            if use_str:
                stack += list(str_edges.get(m, ()))
        return seen

    roots = {m for m in entry_mods if m in mods} | {"hadavin_sdk"} | {m for m in mods if m == "hadavin_sdk.__main__"}
    reach = closure(roots)
    test_roots = {path_mod[f] for f in pyfiles if area(f) == "tests"}
    demo_roots = {path_mod[f] for f in pyfiles if area(f) == "demos"}
    reach_t = closure(test_roots)
    reach_d = closure(demo_roots)
    L11 = [f"roots used: {sorted(roots)}; reachable src modules: {len([m for m in reach if mods[m].startswith('src/')])} of {len(src_mods)}"]
    unreach = [m for m in src_mods if m not in reach]
    out.raw("\n## 11 Reachability (excluding tests as roots)")
    out.sec("11a", "src modules NOT reachable from the roots (entry point, package __init__ chain, registry/deferred string names), with whether tests or demos reach them", L11 + [f"{m} ({mods[m]}) | reached by tests: {'yes' if m in reach_t else 'no'} | reached by demos: {'yes' if m in reach_d else 'no'}" for m in unreach])
    out.sec("11b", "Reached only by tests (not from the roots, reached from test files)", [f"{m} ({mods[m]})" for m in unreach if m in reach_t and m not in reach_d])

    # ============================ 12 config keys
    cfg_files = [f for f in ("src/hadavin_sdk/config.py", "src/hadavin_sdk/defaults.py", "src/hadavin_sdk/scrub_settings.py") if f in trees]
    L12 = []
    for cf in cfg_files:
        for n in ast.walk(trees[cf]):
            if isinstance(n, ast.ClassDef):
                for x in n.body:
                    if isinstance(x, ast.AnnAssign) and isinstance(x.target, ast.Name) and not x.target.id.startswith("_"):
                        k = x.target.id
                        use = collections.Counter()
                        for f, t in trees.items():
                            if f == cf:
                                continue
                            c = 0
                            for y in ast.walk(t):
                                if (isinstance(y, ast.Attribute) and y.attr == k) or (isinstance(y, ast.keyword) and y.arg == k) or (isinstance(y, ast.Constant) and y.value == k and isinstance(y.value, str)):
                                    c += 1
                            if c:
                                use[area(f)] += c
                        inside = sum(1 for y in ast.walk(trees[cf]) if isinstance(y, ast.Attribute) and y.attr == k)
                        L12.append(f"{cf}:{x.lineno} {n.name}.{k} | uses outside file: src={use['src']} tests={use['tests']} demos={use['demos']} | attribute uses inside same file: {inside}")
    out.raw("\n## 12 Config keys defined vs used")
    out.sec("12a", "Pydantic/class fields in config.py, defaults.py, scrub_settings.py with reference counts (all fields listed; zero outside the file and zero inside = candidate unused)", L12)
    yaml_keys = collections.defaultdict(list)
    for f in scope:
        if f in texts and f.endswith((".yaml", ".yml")) and not f.startswith(".github/") and not f.startswith("handover/"):
            for i, line in enumerate(lines_of[f], 1):
                m = re.match(r"^\s*([A-Za-z_][\w-]*):", line)
                if m:
                    yaml_keys[(f, m.group(1))].append(i)
    py_all_text = "\n".join(texts[f] for f in pyfiles)
    out.sec("12b", "YAML keys in non-workflow yaml files and the number of times the key name appears as a word in python text", [f"{f}:{ls[0]} key {k} (x{len(ls)} in file) | python word hits {len(re.findall(r'\\b' + re.escape(k) + r'\\b', py_all_text))}" for (f, k), ls in sorted(yaml_keys.items())])

    # ============================ 10 skeleton + 13 coverage
    LANE_NAMES = {"A": "security", "B": "state and runtime", "C": "models and top level", "D1": "tests", "D2": "demos", "D3": "around code"}
    C_TOP = {"__init__", "app", "cli", "config", "defaults", "evals", "extract", "hashing", "identity", "limits", "models", "replay_records", "scrub_settings", "stats", "tools", "errors"}

    def lane(p: str) -> str:
        if p.startswith("src/hadavin_sdk/"):
            r = p[len("src/hadavin_sdk/"):]
            top = r.split("/")[0]
            if top in ("actions", "approvals", "audit", "guard"):
                return "A"
            if top in ("store", "backends", "runtime", "k1b", "sources") or r in ("registry.py", "deferred.py"):
                return "B"
            if top == "llm" or (("/" not in r) and Path(r).stem in C_TOP):
                return "C"
            return "D3"
        if p.startswith("tests/demo_askdata") or p.startswith("demos/"):
            return "D2"
        if p.startswith("tests/"):
            return "D1"
        return "D3"

    def kind_of(p: str) -> str:
        if p.startswith("tests/fixtures/"):
            return "test fixture"
        if p.startswith("tests/"):
            return "test"
        if p.startswith(".github/workflows/"):
            return "CI job file"
        if p.startswith(".github/"):
            return "CI config"
        if p.startswith(".claude/hooks/"):
            return "hook"
        if p.startswith(".claude/rules/"):
            return "doc (rule)"
        if p.startswith(".claude/"):
            return "config (agent settings)"
        if p.startswith("handover/"):
            return "doc (handover)"
        if p.startswith("demos/") and p.endswith(".py"):
            return "demo module"
        if p.startswith("demos/") and p.endswith(".md"):
            return "doc (demo)"
        if p.startswith("demos/"):
            return "demo data/config"
        if p.startswith("docs/"):
            return "doc"
        if p.startswith("src/") and p.endswith("__init__.py"):
            return "package"
        if p.startswith("src/") and p.endswith(".py"):
            return "module"
        if p.startswith("src/"):
            return "data/resource in package"
        if p.endswith(".md"):
            return "doc"
        if p.endswith((".toml", ".lock", ".yaml", ".yml", ".properties")):
            return "config"
        if p.startswith("."):
            return "dotfile config"
        return "file"

    cred_hit_files = {f for f in hits6 if any(ctx == "code" and k in ("environ", "getenv", "secret", "token", "urllib", "http.client", "requests", "httpx", "boto3", "socket") for (_, k, ctx, _) in hits6[f])}
    state_hit_files = {f for f in hits5 if any(ctx == "code" and k in ("sqlite3", "open-write", "write_text", "write_bytes", "jsonl", "psycopg", "DSN", "getLogger", "retry", "backoff", "timeout", "sleep", "max_attempts") for (_, k, ctx, _) in hits5[f])}
    full_rows = state_hit_files | cred_hit_files

    def short_hits(f: str, store, keys) -> str:
        parts = []
        for i, k, ctx, idn in store.get(f, []):
            if ctx == "code" and k in keys:
                parts.append(f"{k}@{i}")
        return ", ".join(parts[:5]) or "UNVERIFIED"

    mentioned: dict[str, list[str]] = {}
    small_texts = {f: t for f, t in texts.items() if len(t) < 200_000}
    for f in scope:
        base = Path(f).name
        if len(base) < 5:
            continue
        who = [g for g, t in small_texts.items() if g != f and (f in t or base in t)]
        mentioned[f] = who

    counters = collections.Counter()
    rows_by_lane: dict[str, list[str]] = collections.defaultdict(list)
    covered = set()
    for f in sorted(scope):
        ln = lane(f)
        counters[ln] += 1
        rid = f"M-{ln}-{counters[ln]:02d}"
        k = kind_of(f)
        purpose = "UNVERIFIED"
        if f in trees:
            ds = ast.get_docstring(trees[f])
            if ds:
                purpose = safe_line(ds.strip().splitlines()[0])
        elif f.endswith(".md") and f in lines_of:
            for l0 in lines_of[f][:15]:
                if l0.startswith("#"):
                    purpose = "doc: " + safe_line(l0.lstrip("# "))
                    break
        elif f in not_opened:
            purpose = "file not opened (name matches env/key pattern)"
        if f in path_mod:
            imp = sorted(path_mod[x] for x in importers.get(path_mod[f], ()))
            used = ", ".join(imp[:8]) + (f" (+{len(imp) - 8})" if len(imp) > 8 else "") if imp else "no importers"
        else:
            used = ", ".join(mentioned.get(f, [])[:5]) + (f" (+{len(mentioned.get(f, [])) - 5})" if len(mentioned.get(f, [])) > 5 else "") if mentioned.get(f) else "no mention found by name"
        tested = ", ".join(sorted(Path(x).name for x in tested_by.get(path_mod.get(f, ""), ()))[:6]) or ("no test file imports it" if f in path_mod and area(f) in ("src", "demos") else "UNVERIFIED")
        if f in full_rows:
            notes = f"state/log/retry: {short_hits(f, hits5, list(pat5))} | cred/egress/personal words: {short_hits(f, hits6, list(pat6))}"
            row = (
                f"| {rid} | {cell(k)} | {cell(f)} | {cell(purpose)} | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | "
                f"{cell(short_hits(f, hits5, ['retry', 'backoff', 'timeout', 'sleep', 'max_attempts']))} | UNVERIFIED | "
                f"{cell(short_hits(f, hits5, ['getLogger', 'jsonl', 'sqlite3', 'open-write', 'write_text', 'write_bytes', 'psycopg', 'DSN']))} | "
                f"{cell(short_hits(f, hits6, ['environ', 'getenv', 'secret', 'token']))} | {cell(tested)} | {cell(used)} | {cell(notes)} | UNVERIFIED |"
            )
            rows_by_lane[ln + "|full"].append(row)
        else:
            rows_by_lane[ln + "|short"].append(f"| {rid} | {cell(k)} | {cell(f)} | {cell(purpose)} | {cell(used)} | UNVERIFIED |")
        covered.add(f)

    # extra rows (D3): branches, remotes, entry points, hooks, CI jobs
    extra = []
    n_d3 = counters["D3"]

    def nid():
        nonlocal n_d3
        n_d3 += 1
        return f"M-D3-{n_d3:02d}"

    for b in branches.splitlines():
        extra.append(f"| {nid()} | repo branch | `git branch -a` entry {b.strip()} (run {time.strftime('%Y-%m-%d', time.gmtime())}) | UNVERIFIED | UNVERIFIED | UNVERIFIED |")
    for r_ in remotes.splitlines():
        extra.append(f"| {nid()} | git remote | `git remote -v`: {cell(re.sub(r'(https?://)[^@/]+@', r'\1<redacted>@', r_))} | UNVERIFIED | UNVERIFIED | UNVERIFIED |")
    for k_, v_ in entry_points.items():
        extra.append(f"| {nid()} | entry point | pyproject [project.scripts] {k_} = {v_} | UNVERIFIED | UNVERIFIED | UNVERIFIED |")
    for f in scope:
        if f.startswith(".github/workflows/") and f in lines_of:
            inj = False
            for i, line in enumerate(lines_of[f], 1):
                if re.match(r"^jobs:", line):
                    inj = True
                    continue
                m = re.match(r"^  ([\w-]+):\s*$", line) if inj else None
                if m:
                    extra.append(f"| {nid()} | CI job | {f}:{i} job {m.group(1)} | UNVERIFIED | UNVERIFIED | UNVERIFIED |")
    if ".claude/settings.json" in texts:
        for i, line in enumerate(lines_of[".claude/settings.json"], 1):
            m = re.search(r'"command"\s*:\s*"([^"]*)"', line)
            if m:
                cmd = m.group(1)
                extra.append(f"| {nid()} | hook (settings.json) | .claude/settings.json:{i} command runs `{cell(cmd[:60])}` | UNVERIFIED | UNVERIFIED | UNVERIFIED |")
    handover_top = sorted({f.split("/")[1] for f in files if f.startswith("handover/")})
    out_dirs = collections.Counter(f.split("/")[1] if f.count("/") > 1 else "<top-level file>" for f in out_of_scope)

    # write skeleton file
    sk = [f"# skeleton-map.md (EVIDENCE RUNNER output, audited sha {sha}; generated by evidence-1.py)", "",
          "Rows are skeletons: id, path, purpose line (first docstring or heading line), importers or mentions, test files that import it, and pattern-hit names with line numbers. Every UNVERIFIED cell is for the builder to fill. Verdict column is added (R6): NEEDED, DUPLICATE, NOT-NEEDED, CRM-COULD-DO, UNVERIFIED. Lane by R6 path-prefix table. Full rows (16 columns incl. verdict) are for files with a hit in evidence section 5 or 6 (code lines); the rest use 5 columns plus verdict.", ""]
    for ln in ["A", "B", "C", "D1", "D2", "D3"]:
        sk.append(f"## Lane {ln}: {LANE_NAMES[ln]} ({counters[ln]} file rows" + (f", {len(extra)} non-file rows" if ln == "D3" else "") + ")")
        sk.append("")
        fr = rows_by_lane.get(ln + "|full", [])
        sr = rows_by_lane.get(ln + "|short", [])
        if fr:
            sk.append("### Full rows")
            sk.append("| id | kind-of-thing | path | purpose | owner of the job | inputs | outputs | failure path | retry/timeout | idempotency | where it logs | identity it runs as | where tested | who uses it | notes | verdict |")
            sk.append("|" + "---|" * 16)
            sk += fr
            sk.append("")
        if sr or (ln == "D3" and extra):
            sk.append("### Short rows")
            sk.append("| id | kind | path | purpose | used-by | verdict |")
            sk.append("|---|---|---|---|---|---|")
            sk += sr
            if ln == "D3":
                sk += extra
            sk.append("")
    sk.append("## Out of scope (R6 / AUDIT-PLAN lanes): not given rows")
    sk.append("")
    sk.append(f"handover/ files not in the D3 list: {len(out_of_scope)} files in {len(out_dirs)} groups: " + "; ".join(f"{k}={v}" for k, v in sorted(out_dirs.items())))
    sk.append("")
    sk.append("Directory listing of handover/ (D3, names only): " + ", ".join(handover_top))
    sk.append("")
    (PARTS / "skeleton-map.md").write_text("\n".join(sk) + "\n", encoding="utf-8")

    # 10 + 13 in evidence
    out.raw("\n## 10 Skeleton map rows")
    out.raw(f"Written to parts/skeleton-map.md: file rows per lane {dict(counters)}; full-column rows {sum(len(v) for k, v in rows_by_lane.items() if k.endswith('full'))}; short rows {sum(len(v) for k, v in rows_by_lane.items() if k.endswith('short'))}; extra non-file D3 rows (branches, remotes, entry point, CI jobs, hooks): {len(extra)}")
    out.raw("\n## 13 Coverage")
    missing_cov = [f for f in scope if f not in covered]
    out.raw(f"git ls-files paths: {len(files)}; in scope: {len(scope)}; with a skeleton row: {len(covered)}; in scope without a row: {len(missing_cov)}; NOT-AUDITED (out of scope): {len(out_of_scope)}")
    out.sec("13a", "In-scope paths without a skeleton row", missing_cov)
    out.sec("13b", "NOT-AUDITED groups (handover/ files outside the D3 list) with file counts", [f"handover/{k}: {v} files" for k, v in sorted(out_dirs.items())])
    out.sec("13c", "In-scope files not opened (name matches env/key pattern; row exists, contents never read)", not_opened)
    big = [f for f in scope if f not in texts and f not in not_opened]
    out.sec("13d", "In-scope files not read as text (binary, over 400 KB, or unreadable); row exists", big)

    # ============================ 14 sampler note
    out.raw("\n## 14 Sampler\nImplemented: `python3 -I handover/core-hardening/parts/evidence-1.py --sample N --seed S` (reads MASTER-MAP.md and AUDIT-FINDINGS.md, prints a seeded sample of ids to stdout only; does not rewrite this file). Not run as part of this evidence (the merged files do not exist yet).")

    out.raw(f"\n## Run summary\n- files written: parts/evidence-1.md, parts/skeleton-map.md, full lists: {', '.join(out.full_files) or 'none'}\n- elapsed: {time.time() - t0:.0f}s")
    (PARTS / "evidence-1.md").write_text("\n".join(out.md) + "\n", encoding="utf-8")
    return rc_py


def sample(n: int, seed: int) -> int:
    ids = {"finding": set(), "map": set()}
    for fn, key in (("AUDIT-FINDINGS.md", "finding"), ("MASTER-MAP.md", "map")):
        p = CORE / fn
        if not p.exists():
            print(f"MISSING {p.relative_to(ROOT)}: no {key} ids to sample")
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("|"):
                continue
            first = line.split("|")[1].strip() if line.count("|") > 1 else ""
            if key == "finding" and re.fullmatch(r"(?:[A-C]|D[123]|X)-\d+", first):
                ids[key].add(first)
            if key == "map" and re.fullmatch(r"M-(?:A|B|C|D1|D2|D3|X)-\d+", first):
                ids[key].add(first)
    rng = random.Random(seed)
    for key in ("finding", "map"):
        pool = sorted(ids[key])
        pick = sorted(rng.sample(pool, min(n, len(pool)))) if pool else []
        print(f"{key} ids: pool={len(pool)} seed={seed} sample={n}: {', '.join(pick) or '(none)'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    if not (ROOT / ".git").exists():
        print("run from the repo root", file=sys.stderr)
        sys.exit(2)
    if a.sample:
        sys.exit(sample(a.sample, a.seed))
    PARTS.mkdir(parents=True, exist_ok=True)
    sys.exit(main_run())
