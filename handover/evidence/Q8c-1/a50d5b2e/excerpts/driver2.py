import subprocess, re, os, sys
B = "/home/user/build/EV-Q8c1b14-a50d5b2e"; S = B + "/scratch2"; PY = B + "/venv/bin/python"
HEAD = "a50d5b2e6e5b0f828bc60e43df93cb3333a3805f"
def git(*a, **k): return subprocess.run(["git", "-c", "user.email=ev@example.invalid", "-c", "user.name=ev", *a], cwd=S, capture_output=True, text=True)
base_main = subprocess.run(["git", "rev-parse", "origin/main"], cwd=B + "/wt", capture_output=True, text=True).stdout.strip()
BASES = [("origin/main", base_main), ("c65d9c27", "c65d9c27ccf757cf9210bafa7b15d610b3e09e37")]
NOTES = "handover/evidence/Q8c-1/b14/NOTES.md"
def rd(f): return open(os.path.join(S, f)).read()
def wr(f, t):
    p = os.path.join(S, f); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(t)
def rep(f, old, new):
    t = rd(f); assert t.count(old) == 1, (f, old, t.count(old)); wr(f, t.replace(old, new))
def app(f, new): wr(f, (rd(f) if os.path.exists(os.path.join(S, f)) else "") + new)
def rowline(prefix):
    t = rd(NOTES).split("\n"); i = [k for k, l in enumerate(t) if l.startswith(prefix)]; assert len(i) == 1, (prefix, len(i)); return t, i[0]
UNIT = "| tests/policy_mutants.py | `B14 notes check accepts a unit cell that names nothing that exists` |"
def row_edit(prefix, fn):
    t, i = rowline(prefix); t[i] = fn(t[i]); wr(NOTES, "\n".join(t))
def row_add(prefix, fn):
    t, i = rowline(prefix); t.insert(i + 1, fn(t[i])); wr(NOTES, "\n".join(t))
def e_mutant():
    t = rd("tests/policy_mutants.py")
    m = re.search(r'    mutant\(\n        "B11 notes check does not read class methods",.*?\n    \),\n', t, re.S); assert m
    blk = m.group(0).replace("B11 notes check does not read class methods", "B11 notes check does not read class")
    wr("tests/policy_mutants.py", t.replace(m.group(0), m.group(0) + blk, 1))
P = []
def p(i, desc, fn): P.append((i, desc, fn))
p("a", "new test file, no notes row", lambda: app("tests/test_zz_plant_a.py", "def test_plant_a_new_test_without_row():\n    assert True\n"))
p("b1", "only a NEW unused function added to tests/k1b_support.py", lambda: app("tests/k1b_support.py", "\n\ndef zz_plant_unused():\n    return 1\n"))
p("b2", "only a value used by many tests changed in tests/k1b_support.py (severity page -> ticket)", lambda: rep("tests/k1b_support.py", '"alert": {"title": "High latency", "severity": "page"', '"alert": {"title": "High latency", "severity": "ticket"'))
p("b3", "only the body of azure_secret_client (tests/contracts/http_fake.py) changed", lambda: rep("tests/contracts/http_fake.py", '    """A real `SecretClient`. Like Key Vault, the first unauthenticated call gets a 401 bearer challenge."""\n', '    """A real `SecretClient`. Like Key Vault, the first unauthenticated call gets a 401 bearer challenge."""\n    _zz = 1\n'))
p("b4", "only the body of gcp_secret_client (tests/contracts/http_fake.py) changed", lambda: rep("tests/contracts/http_fake.py", '    """A real `SecretManagerServiceClient` on its REST transport."""\n', '    """A real `SecretManagerServiceClient` on its REST transport."""\n    _zz = 1\n'))
p("b5", "only the body of _azure (tests/contracts/kinds/secrets_neutral.py) changed", lambda: rep("tests/contracts/kinds/secrets_neutral.py", "def _azure(seed):\n", "def _azure(seed):\n    _zz = 1\n"))
p("b6", "only FakeVault.__init__ (tests/contracts/vault_fake.py) changed (self.reads = 0 -> 1)", lambda: rep("tests/contracts/vault_fake.py", "        self.reads = 0\n", "        self.reads = 1\n"))
p("b7", "only fake_vault() (tests/contracts/vault_fake.py) changed", lambda: rep("tests/contracts/vault_fake.py", "def fake_vault() -> FakeVault:\n    global _ONE\n", "def fake_vault() -> FakeVault:\n    global _ONE\n    _zz = 1\n"))
p("c1", "module-level pytestmark skip in tests/test_p4b_secrets.py", lambda: rep("tests/test_p4b_secrets.py", "\nimport pytest\n", "\nimport pytest\n\npytestmark = pytest.mark.skip(reason='plant')\n"))
p("c2", "pytest_collection_modifyitems skip hook added to tests/conftest.py", lambda: app("tests/conftest.py", "\n\ndef pytest_collection_modifyitems(config, items):\n    for item in items:\n        item.add_marker(pytest.mark.skip(reason='plant'))\n"))
p("c3", "autouse fixture that calls pytest.skip added to tests/conftest.py", lambda: app("tests/conftest.py", "\n\n@pytest.fixture(autouse=True)\ndef _plant_skip():\n    pytest.skip('plant')\n"))
p("c4", "xfail collection hook added to tests/contracts/conftest.py", lambda: app("tests/contracts/conftest.py", "\n\ndef pytest_collection_modifyitems(config, items):\n    for item in items:\n        item.add_marker(pytest.mark.xfail(reason='plant'))\n"))
p("d1", "an extra row for a mutant that does not exist (unit cell `B99 no such mutant exists here`)", lambda: row_add(UNIT, lambda l: l.replace("`B14 notes check accepts a unit cell that names nothing that exists`", "`B99 no such mutant exists here`", 1)))
p("d2", "unit cell of the existing row gets a `;` item `B99 no such mutant exists here`", lambda: row_edit(UNIT, lambda l: l.replace("`B14 notes check accepts a unit cell that names nothing that exists`", "`B14 notes check accepts a unit cell that names nothing that exists; B99 no such mutant exists here`", 1)))
p("d3", "reason cell of the row names `test_no_such_test_anywhere`", lambda: row_edit(UNIT, lambda l: l.replace("killed by `test_a_row_whose_unit_cell_names_a_mutant_or_a_test_that_exists_nowhere_is_a_problem`", "killed by `test_no_such_test_anywhere`", 1)))
p("d4", "reason cell of the row names backticked `B99 no such mutant exists here`", lambda: row_edit(UNIT, lambda l: l.replace("killed by `test_a_row_whose_unit_cell_names_a_mutant_or_a_test_that_exists_nowhere_is_a_problem`", "killed by `B99 no such mutant exists here`", 1)))
p("e", "new mutant `B11 notes check does not read class` (a substring of `B11 notes check does not read class methods`), no row of its own", e_mutant)
os.system(f"rm -rf {S}; git clone -q --no-checkout {B}/wt {S}")
git("checkout", "-q", "--detach", HEAD)
out = open(B + "/plants/results2.md", "w"); raw = open(B + "/plants/raw2.log", "w")
for (i, desc, fn) in P:
    git("reset", "-q", "--hard", HEAD); git("clean", "-qfd")
    try: fn()
    except AssertionError as e:
        raw.write(f"## {i}: PLANT NOT APPLIED {e}\n\n"); continue
    git("add", "-A"); git("commit", "-qm", "plant " + i)
    res = []
    for (bn, bh) in BASES:
        r = subprocess.run([PY, "tools/notes_lines_check.py", "--auto", bh], cwd=S, capture_output=True, text=True)
        outp = "\n".join(l for l in (r.stdout + r.stderr).strip().splitlines() if "UV_NATIVE" not in l)
        raw.write(f"## {i}: {desc}\n--auto {bn}: exit {r.returncode}; lines {len(outp.splitlines())}\n{outp[:6000]}\n\n"); raw.flush()
        first = outp.splitlines()[0][:170] if outp else "no output"
        res.append(f"exit {r.returncode}, {len(outp.splitlines())} lines; first: {first}")
    out.write(f"| {i} | {desc} | {res[0]} | {res[1]} |\n"); out.flush()
git("reset", "-q", "--hard", HEAD)
