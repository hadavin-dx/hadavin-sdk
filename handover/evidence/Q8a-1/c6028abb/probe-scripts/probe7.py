"""EVIDENCE probe (item 7): plant faults into a TEMP COPY of one src module (kept outside the repo, passed in memory), run the
same function the guard test runs (tests.test_stage_names._guard_violations) over the real sources with that one module replaced.
Records for each fault whether the guard reports a NEW violation. Nothing in the repo is edited."""
import ast, sys, json, tempfile, pathlib, shutil
sys.path.insert(0, sys.argv[1])                     # the worktree root (for `tests` and `tools`)
import tests.test_stage_names as T
MOD = "sources/kubernetes.py"
real = T._src_sources()
base_found, base_stale = T._guard_violations(real)
print("baseline on real sources: violations", len(base_found), "stale", len(base_stale))
tmp = pathlib.Path(tempfile.mkdtemp(prefix="ev7-"))          # the temp copy lives outside the repo
(tmp / "kubernetes.py").write_text(real[MOD], encoding="utf-8")
FAULTS = {
 # the ten the brief named, written by me (names chosen to test the class, not the listed spellings)
 "F1 renamed variable (val = self.namespaces[0]; f-string of val)": "def f1(self):\n    val = self.namespaces[0]\n    raise SourceError(f\"bad {val}\")",
 "F2 + with a variable prefix (prefix + self.namespaces[0])": "def f2(self, prefix):\n    raise SourceError(prefix + self.namespaces[0])",
 "F3 \"%s\" % name": "def f3(self, name):\n    raise SourceError(\"bad %s\" % name)",
 "F4 .format with a variable template": "def f4(self, tmpl, name):\n    raise SourceError(tmpl.format(name))",
 "F5 \", \".join(names)": "def f5(self, names):\n    raise SourceError(\", \".join(names))",
 "F6 msg += name": "def f6(self, name):\n    msg = 'x '\n    msg += name\n    raise SourceError(msg)",
 "F7 a logger not named log (audit.warning)": "def f7(self, host):\n    audit.warning('x %s', host)",
 "F8 a comprehension variable": "def f8(self):\n    raise SourceError('; '.join(f'{t} bad' for t in self._cfg.namespaces))",
 "F9 attribute of an object not named settings (self._cfg.api_url)": "def f9(self):\n    raise SourceError(f'bad {self._cfg.api_url}')",
 "F10 pass-through f'{exc}'": "def f10(self, fn):\n    try:\n        fn()\n    except OSError as exc:\n        raise SourceError(f'kubernetes: {exc}') from None",
 # my extra shapes (not asked): to list what the guard does not see
 "X1 rename through an unlisted loop-free assignment of a listed name (label = name; f'{label}')": "def x1(self, name):\n    label = name\n    raise SourceError(f'bad {label}')",
 "X2 value through a helper function (def fmt(v): return f'bad {v}'; raise E(fmt(name)))": "def fmt(v):\n    return f'bad {v}'\ndef x2(self, name):\n    raise SourceError(fmt(name))",
 "X3 percent with a dict (%(a)s % {'a': name})": "def x3(self, name):\n    raise SourceError('bad %(a)s' % {'a': name})",
 "X4 string.Template substitute": "def x4(self, name):\n    from string import Template\n    raise SourceError(Template('bad $n').substitute(n=name))",
 "X5 print(name)": "def x5(self, name):\n    print(name)",
 "X6 warnings.warn(name)": "def x6(self, name):\n    import warnings\n    warnings.warn(name)",
 "X7 sys.stderr.write(name)": "def x7(self, name):\n    import sys\n    sys.stderr.write(name)",
 "X8 logging with extra={'n': name}": "def x8(self, name):\n    audit.warning('x', extra={'n': name})",
 "X9 raise with the value as a non-first argument (raise E('x', name))": "def x9(self, name):\n    raise SourceError('x', name)",
 "X10 exception notes (exc.add_note(name))": "def x10(self, name):\n    e = SourceError('x')\n    e.add_note(name)\n    raise e",
 "X11 str(exc) into a variable then a message (m = str(exc); raise E(m))": "def x11(self, fn):\n    try:\n        fn()\n    except OSError as exc:\n        m = str(exc)\n        raise SourceError(m) from None",
 "X12 format_map": "def x12(self, name):\n    raise SourceError('bad {n}'.format_map({'n': name}))",
 "X13 f-string with an unlisted variable (f'bad {thing}')": "def x13(self, thing):\n    raise SourceError(f'bad {thing}')",
 "X14 dict/JSON body printed (json.dumps({'ns': name}))": "def x14(self, name):\n    import json\n    raise SourceError(json.dumps({'ns': name}))",
 "X15 f-string of a listed name inside a nested call (f'{len(name)} {name!r}' via repr)": "def x15(self, name):\n    raise SourceError(repr(name))",
}
out = []
for label, code in FAULTS.items():
    src = real[MOD] + "\n\n" + code + "\n"
    (tmp / "planted.py").write_text(src, encoding="utf-8")    # kept in the temp dir for the record
    srcs = dict(real); srcs[MOD] = src
    found, stale = T._guard_violations(srcs)
    new = [f for f in found if f not in base_found]
    out.append((label, bool(new), new[:1]))
    print(("FOUND    " if new else "NOT SEEN ") + label)
    for n in new[:1]: print("          ->", n.split(": ", 1)[1][:110])
json.dump(out, open(sys.argv[2], "w"), indent=0)
print("\nfound", sum(1 for o in out if o[1]), "of", len(out), "; not seen:", [o[0].split(" ")[0] for o in out if not o[1]])
shutil.rmtree(tmp)
