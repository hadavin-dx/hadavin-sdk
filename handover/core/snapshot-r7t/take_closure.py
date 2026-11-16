"""Static import closure of the take entry points (reads text with ast; NOTHING of the repository is run or imported).

usage: python -I take_closure.py <tree> [--compare <other tree>] [--json out.json]

Entry points: scripts/run_real_check.py and scripts/crash_desk.py (the child process the real check starts). The walk
follows `import x`, `from x import y` (module level and inside functions), relative imports, and the literal strings
given to importlib.import_module / __import__ , into src/, scripts/, tools/, demo_only/, load_tools/ of the tree.
For every `from M import n` where M is a file of the tree it records the exact pair (M, n); `import M as a` followed by
`a.n` records (M, n) too. `n` that is itself a module file of the tree is recorded as a module, not a name.
Output: one line per file (closure) and one line per (module, name) pair, with 'defined here' = the name is bound at the
top level of M (def, class, assignment, import) so a missing name is found without importing anything."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ENTRY = ("scripts/run_real_check.py", "scripts/crash_desk.py")
ROOTS = ("src", "scripts", ".")  # the folders on the search path (run_real_check puts src and the repo root there)
OWN_TOP = {"lead_desk", "scripts", "tools", "demo_only", "load_tools"}


def module_file(tree: Path, mod: str) -> Path | None:
    parts = mod.split(".")
    for root in ROOTS:
        base = tree / root
        for cand in (base.joinpath(*parts).with_suffix(".py"), base.joinpath(*parts, "__init__.py")):
            if cand.is_file():
                return cand
    return None


def rel(tree: Path, p: Path) -> str:
    return p.relative_to(tree).as_posix()


def module_name_of(tree: Path, p: Path) -> str:
    r = Path(rel(tree, p))
    parts = list(r.with_suffix("").parts)
    if parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def top_level_names(path: Path) -> set[str]:
    out: set[str] = set()
    t = ast.parse(path.read_text(encoding="utf-8"))
    for n in t.body:
        for x in ast.walk(n) if isinstance(n, (ast.If, ast.Try)) else [n]:
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(x.name)
            elif isinstance(x, ast.Assign):
                for tg in x.targets:
                    out |= {y.id for y in ast.walk(tg) if isinstance(y, ast.Name)}
            elif isinstance(x, (ast.AnnAssign, ast.AugAssign)) and isinstance(x.target, ast.Name):
                out.add(x.target.id)
            elif isinstance(x, ast.Import):
                out |= {a.asname or a.name.split(".")[0] for a in x.names}
            elif isinstance(x, ast.ImportFrom):
                out |= {a.asname or a.name for a in x.names}
    return out


def walk(tree: Path) -> tuple[dict[str, str], set[tuple[str, str]], list[str]]:
    """(file -> why it is in the closure, {(module, name)}, notes)."""
    files: dict[str, str] = {}
    pairs: set[tuple[str, str]] = set()
    notes: list[str] = []
    todo: list[tuple[Path, str]] = [(tree / e, "entry point") for e in ENTRY if (tree / e).is_file()]
    while todo:
        path, why = todo.pop()
        r = rel(tree, path)
        if r in files:
            continue
        files[r] = why
        src = ast.parse(path.read_text(encoding="utf-8"))
        me = module_name_of(tree, path)
        alias: dict[str, str] = {}

        def add(mod: str, via: str) -> None:
            f = module_file(tree, mod)
            if f is not None and rel(tree, f) not in files:
                todo.append((f, f"imported by {r} ({via})"))

        for node in ast.walk(src):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in OWN_TOP or module_file(tree, a.name):
                        add(a.name, "import")
                        if a.asname:
                            alias[a.asname] = a.name
                        else:
                            alias[a.name.split(".")[0]] = a.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:  # relative: start from this file's package, one level up per extra dot
                    pkg = me.split(".") if path.name == "__init__.py" else me.split(".")[:-1]
                    pkg = pkg[: len(pkg) - (node.level - 1)]
                    base = ".".join([*pkg, *([node.module] if node.module else [])])
                if not (base.split(".")[0] in OWN_TOP or module_file(tree, base)):
                    continue
                add(base, "from-import")
                for a in node.names:
                    if a.name == "*":
                        notes.append(f"{r}: star import from {base} (every name; not listed)")
                        continue
                    sub = module_file(tree, f"{base}.{a.name}")
                    if sub is not None:
                        add(f"{base}.{a.name}", "from-import of a module")
                        alias[a.asname or a.name] = f"{base}.{a.name}"
                    else:
                        pairs.add((base, a.name))
            elif isinstance(node, ast.Call):
                fn = ast.unparse(node.func)
                if fn in ("importlib.import_module", "import_module", "__import__") and node.args:
                    a0 = node.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        add(a0.value, f"{fn}({a0.value!r}) at line {node.lineno}")
                        notes.append(f"{r}:{node.lineno}: {fn}({a0.value!r}) followed as a literal")
                    else:
                        notes.append(f"{r}:{node.lineno}: {fn}(<not a literal>) NOT followed")
        # a.n where a is an imported repository module
        for node in ast.walk(src):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in alias:
                mod = alias[node.value.id]
                if module_file(tree, mod) is not None and module_file(tree, f"{mod}.{node.attr}") is None:
                    pairs.add((mod, node.attr))
    return files, pairs, notes


def main() -> None:
    args = sys.argv[1:]
    tree = Path(args[0]).resolve()
    files, pairs, notes = walk(tree)
    result = {
        "files": files,
        "pairs": sorted(pairs),
        "notes": notes,
    }
    defined: dict[str, bool] = {}
    for mod, name in sorted(pairs):
        f = module_file(tree, mod)
        defined[f"{mod}:{name}"] = bool(f) and (name in top_level_names(f))
    result["defined_here"] = defined
    if "--compare" in args:
        other = Path(args[args.index("--compare") + 1]).resolve()
        miss = []
        for mod, name in sorted(pairs):
            f = module_file(other, mod)
            if f is None:
                miss.append(f"{mod}:{name} (module missing)")
            elif name not in top_level_names(f):
                miss.append(f"{mod}:{name}")
        result["missing_in_other"] = miss
    if "--json" in args:
        Path(args[args.index("--json") + 1]).write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    else:
        print(json.dumps(result, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
