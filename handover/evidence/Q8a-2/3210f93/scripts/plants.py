"""Step 7: plants, one at a time, into a temp COPY of the head's src tree (outside the repo). Run with cwd = head worktree, PYTHONPATH=<head>/src:<head>."""
import shutil, sys, tempfile
from pathlib import Path
import tests.test_lockin_guard as g

base = Path(tempfile.mkdtemp(prefix="evq8a2f-plants-", dir=sys.argv[1]))
copy = base / "src"
shutil.copytree(g.SRC, copy, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
print("guard file:", g.__file__); print("copied", g.SRC, "->", copy)
NEUTRAL = copy / g.PKG / "runtime" / "tick.py"
TABLE = copy / g.PKG / "backends" / "table.py"

def scans():
    out = {}
    for name, fn in (
        ("import_problems", lambda: g.import_problems(copy, g.VENDOR_IMPORTS, g.LIBRARY_IMPORTS, g.PENDING, g.DYNAMIC_IMPORT_OK, g.TODAY)),
        ("vendor_module_problems", lambda: g.vendor_module_problems(copy, g.VENDOR_IMPORTS, g.factory_modules(), g.VENDOR_HELPERS)),
        ("literal_problems", lambda: g.literal_problems(copy, g.VENDOR_MODULES, g.LITERAL_OK, g.WORD_IN_OK)),
        ("identifier_problems", lambda: g.identifier_problems(copy, g.VENDOR_MODULES, g.IDENTIFIER_OK, g.TABLE_VENDOR_NAMES)),
    ):
        try:
            out[name] = fn()
        except Exception as e:  # recorded, not judged
            out[name] = f"RAISED {type(e).__name__}: {e}"
    return out

def show(res):
    for k, v in res.items():
        print(f"    {k} -> {v!r}")

print("\n== baseline (unchanged copy)"); show(scans())
nlines = NEUTRAL.read_text(encoding="utf-8").count("\n")
print(f"\nneutral module used for plants: {g.PKG}.runtime.tick ({nlines} lines; each plant is appended after a blank line, so it starts at line {nlines + 2})")

PLANTS = [
    "from hadavin_sdk.approvals.slack import HEADER_PREFIX",
    "import hadavin_sdk.approvals.slack_channel as chat",
    "import boto3 as awsclient",
    "pager_duty_key = 1",
    'x = "slack,teams"',
    'x = "slack|teams"',
    'x = "slack teams"',
    'x = "/pager-duty/hook"',
    "x = f\"/sl{'ack'}/hook\"",
    'x = "/sl" "ack/hook"',
    'x = "\\x73lack"',
    'x = b"slack"',
    "def outer():\n    def inner():\n        SLACK = 1",
    'class C:  slack_url: str = ""',
    "def f(*, slack=None): pass",
    "lambda slack: 0",
    "for slack in (): pass",
    "with open(p) as slack: pass",
    "try:\n    pass\nexcept E as slack:\n    pass",
    "def g_():\n    global slack",
    "@slack.hook\ndef h(): pass",
    "obj.slack_token = 1",
    '{"slack": 1}',
    "# slack",
    'def d():\n    """Slack is named here."""',
    "from .slack_x import y",
    "from ..approvals import slack_channel as chat2",
    "import boto3",
    "from hadavin_sdk.approvals import slack_channel",
    "async def slack_poll(): pass",
    "async def poll(aws_key): pass",
    'x = "S3://bucket/key"',
    'x = "arn:aws:iam::123456789012:role/x"',
    'x = "https://hooks.slack.com/services/T0/B0/x"',
    "from sqlalchemy import text as aws_text",
    "import hadavin_sdk.approvals.receiver as slack_receiver",
]
orig = NEUTRAL.read_text(encoding="utf-8")
for i, p in enumerate(PLANTS, 1):
    NEUTRAL.write_text(orig + "\n" + p + "\n", encoding="utf-8")
    try:
        compile(NEUTRAL.read_text(encoding="utf-8"), "tick.py", "exec"); ok = "yes"
    except SyntaxError as e:
        ok = f"NO: {e}"
    print(f"\n== plant {i}: appended text {p!r}  (file still compiles: {ok})")
    show(scans())
    print(f"    receiver-only whole-word pattern (_WHOLE_WORD.findall on the planted text alone) -> {[m.group(0) for m in g._WHOLE_WORD.finditer(p)]!r}")
    NEUTRAL.write_text(orig, encoding="utf-8")
print("\n== neutral module restored; baseline again"); show(scans())

t = TABLE.read_text(encoding="utf-8")
anchor = '    kind: Literal["gcs_retention_lock"]\n'
assert t.count(anchor) == 1
TABLE.write_text(t.replace(anchor, anchor + '    endpoint: str = "https://storage.googleapis.com"\n'), encoding="utf-8")
ln = TABLE.read_text(encoding="utf-8").split("\n").index('    endpoint: str = "https://storage.googleapis.com"') + 1
print(f"\n== GCS plant A: in class GcsRetentionLockSettings ({g.PKG}.backends.table) added line {ln}: endpoint: str = \"https://storage.googleapis.com\"")
show(scans())
TABLE.write_text(t + '\n\nclass GcsOther(KindSettings):\n    gcs_bucket: str = ""\n', encoding="utf-8")
print(f"\n== GCS plant B (A removed): appended to the same module at line {t.count(chr(10)) + 3}: class GcsOther(KindSettings): / gcs_bucket: str = \"\"")
show(scans())
TABLE.write_text(t, encoding="utf-8")
print("\n== table module restored; baseline again"); show(scans())
shutil.rmtree(base); print("temp copy removed:", not base.exists())

import tempfile
sd = Path(tempfile.mkdtemp(prefix="evq8a2f-sql-", dir=sys.argv[1]))
for i, sql in enumerate(["CREATE TABLE t (slack_id text);", "INSERT INTO t VALUES ('slack');", "-- slack\nSELECT 1;", "SELECT 'aws' AS k;", "SELECT s3_key FROM t;", "SELECT 1 /* slack */;"], 1):
    (sd / "0099.sql").write_text(sql + "\n", encoding="utf-8")
    print(f"\n== SQL plant {i}: {sql!r}\n    sql_problems -> {g.sql_problems(sd)!r}")
shutil.rmtree(sd)
