#!/usr/bin/env python3
"""required_fails.py - the REQUIRED-FAILS CHECK of the fail-before step.

A test that is NEW or CHANGED in the patch must FAIL on the old code, otherwise it pins nothing.
This prints every new/changed test id that PASSES on old code, so the lead can ask for each one to be
justified (a control that is meant to stay green, a pin of behaviour that is kept) or fixed.

usage:
  required_fails.py NEW_IDS OLD_RESULT [--old-tests DIR --new-tests DIR] [--justified FILE] [--out FILE]

  NEW_IDS     text file, one pytest id per line (tests/test_x.py::test_y[param]), collected from the test
              files of the new tree, e.g.  pytest --collect-only -q <files> | grep '::'
  OLD_RESULT  the result of running those same tests on the OLD code. Accepted line formats (any mix):
                 PASSED tests/test_x.py::test_y        (pytest -rA short summary)
                 tests/test_x.py::test_y PASSED        (pytest -v)
                 tests/test_x.py::test_y               (a plain list of passing ids, like EV6 fb-passes-on-old.txt)
              Lines starting FAILED / ERROR / SKIPPED mark ids that did NOT pass (counted as 'fails on old').
  --old-tests / --new-tests
              the tests/ folder of the old tree and of the new tree. With both, only tests whose own source
              (ast dump of the function, decorators included) is new or different are checked; without them
              EVERY id in NEW_IDS is checked (then unchanged old tests show up too: expect many).
  --justified FILE  lines 'id<TAB>reason' (or 'id  # reason'): printed as JUSTIFIED instead of REQUIRED.
  --out FILE  also write the REQUIRED list (one id per line) to FILE.

exit code: 0 = no new/changed test passes on old code (or all are justified); 1 = some do; 2 = bad input.
Not detected (said plainly): a change only in a helper, fixture or import at module level (printed as a
count of files whose module-level code changed, 'helper-changed files'); the test then counts as unchanged.
"""
import ast
import hashlib
import re
import sys
from pathlib import Path


def read_lines(p):
    return Path(p).read_text(encoding="utf-8", errors="replace").splitlines()


def parse_old(lines):
    passed, notpassed = set(), set()
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(\S+)", ln)
        if m:
            (passed if m.group(1) in ("PASSED", "XPASS") else notpassed).add(m.group(2))
            continue
        m = re.match(r"^(\S+::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", ln)
        if m:
            (passed if m.group(2) in ("PASSED", "XPASS") else notpassed).add(m.group(1))
            continue
        if re.match(r"^\S+\.py::\S+$", ln):
            passed.add(ln)
    return passed, notpassed


def test_hashes(tests_dir):
    """{ 'tests/test_x.py::name' or '...::Class::name': hash of ast } and {file: hash of the module-level non-test code}"""
    funcs, helpers = {}, {}
    for f in sorted(Path(tests_dir).glob("**/test_*.py")):
        rel = "tests/" + f.relative_to(tests_dir).as_posix()
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            funcs[rel + "::<syntax-error>"] = "syntax-error"
            continue
        rest = []

        def visit(body, prefix):
            for n in body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
                    funcs[prefix + n.name] = hashlib.sha256(ast.dump(n).encode()).hexdigest()[:16]
                elif isinstance(n, ast.ClassDef) and n.name.startswith("Test"):
                    visit(n.body, prefix + n.name + "::")
                elif prefix == rel + "::":
                    rest.append(ast.dump(n))

        visit(tree.body, rel + "::")
        helpers[rel] = hashlib.sha256("\n".join(rest).encode()).hexdigest()[:16]
    return funcs, helpers


def base_id(i):
    return i.split("[", 1)[0]


def main(argv):
    args, opts = [], {}
    it = iter(argv)
    for a in it:
        if a in ("--old-tests", "--new-tests", "--justified", "--out"):
            opts[a] = next(it, None)
        else:
            args.append(a)
    if len(args) != 2 or ((("--old-tests" in opts) != ("--new-tests" in opts))):
        print(__doc__)
        return 2
    new_ids = [x.strip() for x in read_lines(args[0]) if "::" in x]
    passed, notpassed = parse_old(read_lines(args[1]))
    if not new_ids:
        print("ERROR: NEW_IDS holds no test id (expected lines like tests/test_x.py::test_y)")
        return 2
    changed_note = ""
    checked = list(dict.fromkeys(new_ids))
    if "--old-tests" in opts:
        of, oh = test_hashes(opts["--old-tests"])
        nf, nh = test_hashes(opts["--new-tests"])
        keep = [i for i in checked if base_id(i) not in of or of[base_id(i)] != nf.get(base_id(i))]
        # an id whose function is not found in the new tree (e.g. a dynamically named test) is kept: it cannot be proven unchanged
        helper_changed = sorted(f for f in nh if f in oh and oh[f] != nh[f])
        changed_note = (f"unchanged tests skipped: {len(checked) - len(keep)}; "
                        f"helper-changed files (module-level code differs, tests not flagged for it): {len(helper_changed)}")
        for f in helper_changed:
            changed_note += "\n    helper-changed: " + f
        checked = keep
    just = {}
    if "--justified" in opts:
        for ln in read_lines(opts["--justified"]):
            m = re.match(r"^(\S+::\S+?)\s*(?:\t|\s#\s*|\s{2,})(.*)$", ln.strip())
            if m:
                just[m.group(1)] = m.group(2)
    pin_nothing = [i for i in checked if i in passed]
    unknown = [i for i in checked if i not in passed and i not in notpassed]
    required = [i for i in pin_nothing if i not in just]
    print(f"new-test ids given: {len(set(new_ids))}; checked as new/changed: {len(checked)}; "
          f"failed or errored on old code (named FAILED/ERROR in the input): {len(checked) - len(pin_nothing) - len(unknown)}; "
          f"PASS on old code: {len(pin_nothing)}; no result line on old code: {len(unknown)}"
          + ("" if notpassed else " (this input lists passing ids only, so these are failed, errored OR never run: check the run log)"))
    if changed_note:
        print(changed_note)
    by_file = {}
    for i in pin_nothing:
        by_file.setdefault(i.split("::", 1)[0], []).append(i)
    if pin_nothing:
        print("\nPASS ON OLD CODE (pins nothing until justified) per file:")
        for f, v in sorted(by_file.items()):
            print(f"  {len(v):4d}  {f}")
        print()
        for i in pin_nothing:
            print(("JUSTIFIED  " + i + "  # " + just[i]) if i in just else ("REQUIRED   " + i))
    if unknown and notpassed:
        print("\nNO RESULT ON OLD CODE (timeout, collection error or never run: treat as unchecked):")
        for i in unknown:
            print("UNCHECKED  " + i)
    if "--out" in opts:
        Path(opts["--out"]).write_text("\n".join(required) + ("\n" if required else ""), encoding="utf-8")
    return 1 if required else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
