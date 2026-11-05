"""A CONVENTION SCAN (defence in depth), NOT A PROOF, over the product files: which of them may read the process environment, name the key file or folder,
list or probe directories, reach the key-file parser, or pass anything but the literal ``True`` for ``file_only``.

Still passes (stated, not closed): ``eval``, ``exec`` and ``compile`` on text built at run time, names built at run time (``"".join(...)``, ``chr`` arithmetic, data read from elsewhere, reflection through objects the scan cannot see). The
real controls are: ``secret_store`` is the only reader of the key file, the independent review of the final tree, and file permissions. The scan
resolves import aliases and attribute chains through our own modules, bans modules passed around as values, and relies on the modules NOT re-exporting
``os`` or ``secret_store`` (``settings`` and ``cli`` import only the names they use, under private names where unavoidable). This scan is FROZEN as such.

Plus a working-tree guard for invisible characters (untracked files too)."""

from __future__ import annotations

import ast
import re

import pytest
from astscan import build_aliases, candidate_texts, docstring_nodes, dotted, fold_str, parents

from conftest import ROOT
from intake import secret_store

SECRET_NAMES = frozenset(secret_store.NAMES)
ENV_NAMES = ("os.environ", "os.environb", "os.getenv", "os.getenvb")
KEY_FILE_FUNCS = frozenset({"parse", "present_names", "secrets_path", "check_value"})
SS = "intake.secret_store"
WATCH_MODULES = frozenset({"os", "posix", "nt", "sys", "json", "secret_store", "environ", "_environ", "getenv", "environb"})
VALUE_BANNED = frozenset({"os", "sys", "json", SS})  # these modules may not be passed around as values
BUILTIN_BANNED_VALUES = frozenset({"getattr", "vars", "globals", "locals", "eval", "exec", "__import__", "setattr", "compile"})
BANNED_IMPORTS = frozenset({"posix", "nt", "operator", "inspect", "importlib", "zipfile", "tarfile", "gc", "builtins"})
SHUTIL_BANNED = frozenset({"copytree", "make_archive", "copy", "copy2", "copyfile", "move", "unpack_archive", "rmtree"})
# attributes of the secret store any product file may use (reading a named secret, status lines, the names)
SAFE_ATTRS = frozenset(
    {
        "get",
        "status",
        "mode_state",
        "mode_problems",
        "lock_state",
        "inside_repo",
        "secrets_location",
        "parse_problem",
        "API_KEY",
        "WEBHOOK_SECRET",
    }
    | {"APPROVER_PASSPHRASE", "N8N_ENCRYPTION_KEY", "N8N_PASSWORD", "NAMES", "PASSPHRASE_COPY", "LOCK_FILE", "REPO_ROOT", "MIN_LENGTH"}
)
# exact files; value = what is allowed there
ENV_WHOLE_OK = frozenset(
    {"src/intake/data_source.py", "src/intake/settings.py"}
)  # the whole environment only as `_environ if env is None else env`
ENV_VAR_KEYS_OK = {  # the named variable `env`: only `env.get/pop/setdefault("NAME")` with these literal names
    "src/intake/settings.py": frozenset({"HADAVIN_LOCAL", "INTAKE_MODEL_BACKEND", "INTAKE_LOG"}),
    "src/intake/data_source.py": frozenset({"INTAKE_DEMO_DATA"}),
}
KEY_ATTR_ALLOWED = {  # beyond SAFE_ATTRS; "*" = everything
    "src/intake/secret_store.py": "*",
    "tools/make_secrets.py": "*",
    "tests/conftest.py": frozenset({"secrets_path"}),
}
PATH_CONSTANT_OK = {
    "src/intake/secret_store.py": None,  # None = every path constant
    "tools/make_secrets.py": None,
    "tests/conftest.py": None,  # the helper that writes the FAKE key file in a temporary folder
    "src/intake/isolation.py": frozenset({"secrets"}),  # an unrelated namespace-kind string that predates this work
    "tools/make_run_env.py": frozenset(
        {"n8n.env"}
    ),  # WP7: the one-line file that hands the n8n key to docker compose (name only, never a value)
    "demo_only/e2e/test_n8n_wiring.py": frozenset(
        {"n8n.env"}
    ),  # WP7: the e2e rig reads that file's folder name to start its own containers
}
DIRLIST_OK = {
    "demo_only/data/gen.py": "the existing data generator lists its own folder",
    "tests/conftest.py": "mini_hashes lists the fixture folder",
    "demo_only/tools/demo_ctl.py": "register lists the one folder the lead names (allowlisted, resolved, plain files only); reset empties the demo home's inbox and out folders (guarded by the made-up-data marker)",
    "src/intake/exporter.py": "lists only intake/out for stale temporary CSV files (invoices.csv.*.tmp) left by a killed export; never the key folder",
    "src/intake/inbox.py": "lists INTAKE_HOME/inbox only (os.scandir on the inbox directory descriptor on POSIX, on the inbox path on Windows), non-recursively, for the scan; never the key folder",
    "demo_only/eval/eval_live.py": "stage_inbox lists the inbox of INTAKE_HOME (a temporary folder in a replay, the configured folder in a live run) only to refuse a non-empty one; the names are not read",
}
PROBE_OK = {  # exact files that may test a path (exists, is_file, is_dir, open, stat)
    "tests/conftest.py": "demo folder test and the helper that writes the fake key folder",
    "tools/mutate_src.py": "existing mutation harness",
    "src/intake/secret_store.py": "mode, lock and presence checks of the key folder",
    "tools/make_secrets.py": "creates and locks the key folder",
    "src/intake/data_source.py": "existing demo-data loader: is_dir on the configured folder",
    "src/intake/strictjson.py": "opens the small local JSON files it is handed (config, policy, prices); size-capped",
    "src/intake/model_anthropic.py": "``opener.open(request)`` is the HTTP opener of the live backend, not a file probe",
    "src/intake/inbox.py": "lstat/os.open/fstat of inbox entries and of the one file `intake extract` names; never the key folder; a test pins the probe calls to read_plain_file and the scan loop",
    "src/intake/lockfile.py": "the single-writer lock file: exists/is_dir checks and the open that takes the lock (no content is read)",
    "src/intake/csvsink.py": "exists/stat on intake/out and invoices.csv only, to report their mode bits in ``intake check``; no content is read",
    "tools/private_file.py": "WP7: the single os.open(O_EXCL, 0600) that creates the one-line n8n key file (make_run_env.py itself probes nothing)",
    "src/intake/workqueue.py": "exists/stat on the queue database and its two WAL files in the intake folder (never the key folder); creates the empty queue file 0600 before sqlite writes",
}
FRAME_ATTRS = frozenset({"f_globals", "f_locals", "f_back", "f_builtins", "gi_frame", "tb_frame", "cr_frame", "ag_frame"})
SYS_FRAME_CALLS = frozenset({"sys._getframe", "sys.exc_info", "sys.settrace", "sys.setprofile", "sys._current_frames"})
DUNDER_OK = frozenset({"__name__", "__file__", "__doc__", "__init__"})
GETATTR_WATCHED = frozenset({"os", "json", "ast", SS})
GETATTR_SAFE = frozenset({"O_NOFOLLOW"})
DIRLIST_CALLS = frozenset({"os.listdir", "os.scandir", "os.walk", "os.fwalk", "glob.glob", "glob.iglob"})
PROBE_CALLS = frozenset({"os.path.exists", "os.path.isfile", "os.path.isdir", "os.stat", "os.lstat", "os.open"})
PROBE_ATTRS = frozenset({"exists", "is_file", "is_dir", "open", "stat", "lstat"})


def scan_files():
    for base in ("src/intake", "tools", "demo_only"):
        root = ROOT / base
        if not root.is_dir():  # demo_only is absent in the cut job
            continue
        for p in sorted(root.rglob("*.py")):
            if "__pycache__" not in p.parts:  # core_copy is scanned too: no directory exemption
                yield p
    yield ROOT / "tests" / "conftest.py"


def is_key_path(raw: str) -> bool:
    s = raw.lower()
    return (
        s == "secrets"
        or "secrets.env" in s
        or "approver-passphrase" in s
        or "secrets/" in s
        or "secrets\\" in s
        or s.endswith(".env")
        or "*.env" in s
    )


def scan_capabilities(source: str, rel: str) -> list[str]:
    tree = ast.parse(source)
    alias, stars = build_aliases(tree)
    par = parents(tree)
    docs = docstring_nodes(tree)
    found: list[str] = []

    def ln(n):
        return getattr(n, "lineno", 0)

    if rel != "src/intake/secret_store.py":
        found += [f"star import of {s}" for s in stars if s in (SS, "os", "json", "ast", "glob", "sys")]
    allowed_attrs = KEY_ATTR_ALLOWED.get(rel, frozenset())
    for node in ast.walk(tree):
        d = dotted(node, alias) if isinstance(node, ast.Name | ast.Attribute) else None
        p = par.get(node)
        # ---- imports -------------------------------------------------------------------------------------------------------------------------------
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in BANNED_IMPORTS:
                    found.append(f"import of {a.name} (line {ln(node)})")
        if isinstance(node, ast.ImportFrom):
            base = ("intake" + ("." + node.module if node.module else "")) if node.level else (node.module or "")
            if base.split(".")[0] in BANNED_IMPORTS:
                found.append(f"import from {base} (line {ln(node)})")
            if base == "os" and any(a.name in ("environ", "environb", "getenv", "getenvb") for a in node.names) and rel not in ENV_WHOLE_OK:
                found.append(f"from os import an environment name (line {ln(node)})")
            if base.startswith("intake.") and base != SS:  # a module of ours re-exporting os, sys, json or the secret store
                found += [f"from {base} import {a.name} (line {ln(node)})" for a in node.names if a.name in WATCH_MODULES]
            if base == SS or (node.level and (node.module or "") == "secret_store"):
                for a in node.names:
                    if allowed_attrs != "*" and a.name not in SAFE_ATTRS and a.name not in allowed_attrs:
                        found.append(f"import of secret_store.{a.name} not allowed in {rel} (line {ln(node)})")
            if base == "shutil" and any(a.name in SHUTIL_BANNED for a in node.names):
                found.append(f"shutil copy or archive import (line {ln(node)})")
        # ---- chains through modules, modules and reflection helpers passed as values ---------------------------------------------------------------
        if d:
            parts = d.split(".")
            if parts[0] in ("os", "sys", "json", "ast") and any(x in ("os", "sys", "posix", "nt") for x in parts[1:]):
                found.append(f"module reached through a module: {d} (line {ln(node)})")
            if parts[0] == "intake" and len(parts) >= 3 and parts[1] != "secret_store" and any(x in WATCH_MODULES for x in parts[2:]):
                found.append(f"module reached through an intake module: {d} (line {ln(node)})")
            if d == "sys.modules":
                found.append(f"sys.modules used (line {ln(node)})")
            if d.startswith("shutil.") and parts[1] in SHUTIL_BANNED:
                found.append(f"{d} (line {ln(node)})")
            is_base_of_attr = isinstance(p, ast.Attribute) and p.value is node
            if isinstance(node, ast.Name) and not is_base_of_attr and not isinstance(getattr(node, "ctx", None), ast.Store):
                if d in VALUE_BANNED:
                    found.append(f"module {d} used as a value (line {ln(node)})")
                if d in BUILTIN_BANNED_VALUES and not (isinstance(p, ast.Call) and p.func is node):
                    found.append(f"{d} used as a value (line {ln(node)})")
            if (
                isinstance(node, ast.Attribute)
                and d.startswith(SS + ".")
                and parts[2] in KEY_FILE_FUNCS | SAFE_ATTRS
                and not (isinstance(p, ast.Call) and p.func is node)
            ):
                if parts[2] in (
                    "get",
                    "status",
                    "mode_state",
                    "mode_problems",
                    "lock_state",
                    "inside_repo",
                    "secrets_location",
                    "parse_problem",
                    *KEY_FILE_FUNCS,
                ):
                    if allowed_attrs != "*":
                        found.append(f"secret_store function {d} used as a value (line {ln(node)})")
        # ---- environment access (any alias form) ---------------------------------------------------------------------------------------------------
        if d in ENV_NAMES:
            key = None
            if d.endswith(("getenv", "getenvb")):
                if isinstance(p, ast.Call) and p.func is node and p.args:
                    key = p.args[0]
            elif (
                isinstance(p, ast.Attribute) and p.attr in ("get", "pop", "setdefault") and isinstance(par.get(p), ast.Call) and par[p].args
            ):
                key = par[p].args[0]
            elif isinstance(p, ast.Subscript) and p.value is node:
                key = p.slice
            k = fold_str(key) if key is not None else None
            if key is None:
                gp = par.get(p) if isinstance(p, ast.IfExp) else None
                ok_shape = (
                    isinstance(gp, ast.Assign)
                    and len(gp.targets) == 1
                    and isinstance(gp.targets[0], ast.Name)
                    and gp.targets[0].id == "env"
                    or isinstance(gp, ast.Attribute)
                    and gp.attr == "get"
                )
                if rel not in ENV_WHOLE_OK or not ok_shape:
                    found.append(f"whole environment used (line {ln(node)})")
            elif k is None:
                found.append(f"environment lookup with a non-constant key (line {ln(node)})")
            elif k in SECRET_NAMES:
                found.append(f"environment lookup of a secret name (line {ln(node)})")
        # ---- the named variable `env` in the files that may hold the environment: exact uses only ----------------------------------------------
        if rel in ENV_VAR_KEYS_OK and isinstance(node, ast.Name) and node.id == "env" and isinstance(node.ctx, ast.Load):
            allowed = ENV_VAR_KEYS_OK[rel]
            ok_use = (
                (isinstance(p, ast.Compare) and p.left is node)  # env is None
                or (isinstance(p, ast.IfExp) and p.orelse is node)  # ... else env
                or (
                    isinstance(p, ast.Attribute)
                    and p.attr in ("get", "pop", "setdefault")
                    and isinstance(par.get(p), ast.Call)
                    and par[p].func is p
                    and bool(par[p].args)
                    and fold_str(par[p].args[0]) in allowed
                    and isinstance(par[p].args[0], ast.Constant)
                )
            )
            if not ok_use:
                found.append(f"env used other than env.get/pop/setdefault at a named literal key (line {ln(node)})")
        if (
            rel in ENV_VAR_KEYS_OK
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.IfExp)
        ):
            args = node.args
            if node.func.attr not in ("get", "pop", "setdefault") or not args or fold_str(args[0]) not in ENV_VAR_KEYS_OK[rel]:
                found.append(f"environment expression used other than .get at a named literal key (line {ln(node)})")
        # ---- the key-file parser and the rest of the store, through any alias -----------------------------------------------------------------------
        if isinstance(node, ast.Name | ast.Attribute) and d and d.startswith(SS + "."):
            attr = d.split(".")[2]
            if allowed_attrs != "*" and attr not in SAFE_ATTRS and attr not in allowed_attrs:
                found.append(f"secret_store.{attr} not allowed in {rel} (line {ln(node)})")
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "secrets_path"
            and rel not in {"src/intake/secret_store.py", "tools/make_secrets.py", "tests/conftest.py"}
        ):
            found.append(f".secrets_path used in {rel} (line {ln(node)})")
        # ---- every dunder attribute and the names __import__ / __builtins__ in any position -----------------------------------------------------
        if isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr.endswith("__") and node.attr not in DUNDER_OK:
            found.append(f"dunder attribute {node.attr} (line {ln(node)})")
        if isinstance(node, ast.Name) and node.id in ("__import__", "__builtins__"):
            found.append(f"{node.id} used (line {ln(node)})")
        # ---- reflection --------------------------------------------------------------------------------------------------------------------------------
        if isinstance(node, ast.Attribute) and node.attr == "__dict__":
            found.append(f"__dict__ used (line {ln(node)})")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("vars", "globals", "locals"):
            found.append(f"{node.func.id}() used (line {ln(node)})")
        if isinstance(node, ast.Attribute) and node.attr in FRAME_ATTRS:
            found.append(f"frame attribute {node.attr} (line {ln(node)})")
        if d in SYS_FRAME_CALLS:
            found.append(f"{d} (line {ln(node)})")
        if isinstance(node, ast.Call) and dotted(node.func, alias) == "getattr" and node.args:
            target = dotted(node.args[0], alias) or ""
            name = fold_str(node.args[1]) if len(node.args) > 1 else None
            if name is not None and name.startswith("__"):
                found.append(f"getattr with the dunder name {name} (line {ln(node)})")
            if name is not None and name in FRAME_ATTRS:
                found.append(f"getattr with the frame attribute {name} (line {ln(node)})")
            if (target in GETATTR_WATCHED or target.startswith("os.")) and name not in GETATTR_SAFE:
                found.append(f"getattr on {target} (line {ln(node)})")
        # ---- directory listing and path probing ----------------------------------------------------------------------------------------------------
        if isinstance(node, ast.Call):
            fd = dotted(node.func, alias)
            attr = node.func.attr if isinstance(node.func, ast.Attribute) else None
            if (fd in DIRLIST_CALLS or attr in ("glob", "rglob", "iterdir", "walk")) and rel not in DIRLIST_OK:
                found.append(f"directory listing (line {ln(node)})")
            if (fd in PROBE_CALLS or attr in PROBE_ATTRS) and rel not in PROBE_OK and not rel.startswith("demo_only/"):
                found.append(f"path probing (line {ln(node)})")
        # ---- path constants (case-insensitive, bytes, f-strings, %, .format, + folded) ---------------------------------------------------------------
        if isinstance(node, ast.Constant | ast.BinOp | ast.JoinedStr | ast.Call) and id(node) not in docs:
            for s in candidate_texts(node):
                if is_key_path(s):
                    ok = PATH_CONSTANT_OK.get(rel, frozenset())
                    if ok is not None and s not in ok:
                        found.append(f"path constant {s!r} in {rel} (line {ln(node)})")
    return sorted(set(found))


def test_the_product_files_pass_the_capability_scan():
    bad = {}
    for p in scan_files():
        rel = p.relative_to(ROOT).as_posix()
        f = scan_capabilities(p.read_text(encoding="utf-8"), rel)
        if f:
            bad[rel] = f
    assert not bad, bad


def test_the_allowlists_name_existing_files():
    names = {*ENV_WHOLE_OK, *ENV_VAR_KEYS_OK, *KEY_ATTR_ALLOWED, *PATH_CONSTANT_OK, *DIRLIST_OK, *PROBE_OK}
    for rel in names:
        if rel.startswith("demo_only/") and not (ROOT / "demo_only").is_dir():
            continue  # the cut job deletes the demo-only folder
        assert (ROOT / rel).is_file(), rel


def test_modules_do_not_re_export_os_or_the_secret_store():
    """Structural: a chain through a product module finds nothing (the scan's alias resolution is a second layer)."""
    import importlib

    for mod in ("settings", "cli", "data_source", "strictjson", "validators", "reader", "flags", "codes"):
        m = importlib.import_module(f"intake.{mod}")
        for name in (
            "os",
            "secret_store",
            "json",
            "environ",
            "getenv",
            "posix",
            "nt",
        ):  # `sys` stays in cli and secret_store: the scan covers chains
            assert not hasattr(m, name), (mod, name)


def test_settings_does_not_carry_the_key_path():
    import dataclasses

    from conftest import settings_for_tests

    assert "secrets_path" not in {f.name for f in dataclasses.fields(__import__("intake.settings", fromlist=["Settings"]).Settings)}
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        s = settings_for_tests(Path(d))
        key_dir = str(Path(s.local) / "secrets")
        for text in (
            repr(s),
            str(dataclasses.asdict(s)),
            str(dataclasses.astuple(s)),
            str([getattr(s, f.name) for f in dataclasses.fields(s)]),
        ):
            assert (
                key_dir not in text
                and "secrets.env" not in text
                and "secrets" + chr(92) not in text.replace("secrets" + chr(92) + chr(92), "")
            )


# ---- positive controls: each bypass must be caught ----------------------------------------------------------------------------------------------------
PLACE = "src/intake/pipeline.py"
BAD = [
    ("import os\nx = os.environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("import os\nx = os.environ.get('HADAVIN_WEBHOOK_SECRET')\n", PLACE),
    ("import os\nx = os.getenv('N8N_ENCRYPTION_KEY')\n", PLACE),
    ("import os\nfrom intake import secret_store\nx = os.environ.get(secret_store.API_KEY)\n", PLACE),
    ("import os\nx = os.environ.get(name)\n", PLACE),
    ("import os\nfor k, v in os.environ.items():\n    pass\n", PLACE),
    ("import os\nd = dict(os.environ)\n", PLACE),
    ("import os\nenv = os.environ\n", "src/intake/budget.py"),
    ("import os\nenv = os.environ\n", "src/intake/settings.py"),
    ("import os as o\nx = o.environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("import os\no = os\nx = o.environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("import os\nx = os\n", PLACE),
    ("import os\nf(os)\n", PLACE),
    ("import sys\nx = sys.modules['os'].environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("import sys\nx = sys.modules\n", PLACE),
    ("from os import environ as e\nx = e.get('ANTHROPIC_API_KEY')\n", PLACE),
    ("from os import environ\n", PLACE),
    ("from os import getenv\n", PLACE),
    ("from os import *\n", PLACE),
    ("import posix\nx = posix.environ\n", PLACE),
    ("import nt\nx = nt.environ\n", PLACE),
    ("from os import path\nx = path.os.environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("import os\nx = os.path.os.environ\n", PLACE),
    ("import operator\nx = operator.attrgetter('environ')(os)\n", PLACE),
    ("import inspect\nx = inspect.getmembers(m)\n", PLACE),
    ("import importlib\n", PLACE),
    ("import zipfile\n", PLACE),
    ("import tarfile\n", PLACE),
    ("import shutil\nshutil.copytree(a, b)\n", PLACE),
    ("import shutil\nshutil.make_archive(a, 'zip', b)\n", PLACE),
    ("from shutil import copytree\n", PLACE),
    ("g = getattr\nx = g(os, 'environ')\n", PLACE),
    ("import os\nx = getattr(os, 'environ')\n", PLACE),
    ("import os\nx = getattr(os, name)\n", PLACE),
    ("import os\nx = vars(os)['environ']\n", PLACE),
    ("import os\nx = os.__dict__['environ']\n", PLACE),
    ("x = __import__('os').environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("o = __import__\n", PLACE),
    ("x = __builtins__\n", PLACE),
    ("from intake import settings\nx = settings.load.__globals__['_environ']\n", PLACE),
    ("from intake import cli\nx = cli.main.__globals__['status']\n", PLACE),
    ("def f():\n    pass\nx = f.__code__\n", PLACE),
    ("def f():\n    pass\nx = f.__closure__\n", PLACE),
    ("x = ().__class__.__subclasses__()\n", PLACE),
    ("x = fn.__wrapped__\n", PLACE),
    ("x = fn.__builtins__\n", PLACE),
    ("x = getattr(f, '__globals__')\n", PLACE),
    ("x = getattr(f, '__bu' + 'iltins__')\n", PLACE),
    ("import sys\nx = sys._getframe(0).f_back.f_globals['_environ']\n", PLACE),
    ("import sys\nx = sys._getframe(1)\n", PLACE),
    ("import sys\nx = sys.exc_info()[2].tb_frame\n", PLACE),
    ("import sys\nsys.settrace(f)\n", PLACE),
    ("import sys as s\nx = s._getframe()\n", PLACE),
    ("x = gen.gi_frame\n", PLACE),
    ("x = coro.cr_frame\n", PLACE),
    ("x = agen.ag_frame\n", PLACE),
    ("x = frame.f_locals\n", PLACE),
    ("x = getattr(frame, 'f_globals')\n", PLACE),
    ("x = globals()['os']\n", PLACE),
    ("from intake import settings\nx = settings.os.environ['ANTHROPIC_API_KEY']\n", PLACE),
    ("from intake import settings\nx = settings.secret_store.parse(p)\n", PLACE),
    ("from . import settings\nx = settings.secret_store\n", PLACE),
    ("from intake.settings import secret_store\n", PLACE),
    ("from .settings import os\n", PLACE),
    ("from intake.cli import sys\n", PLACE),
    ("import intake.settings\nx = intake.settings.os.environ\n", PLACE),
    ("import os\nenv = os.environ if env is None else env\nx = env['ANTHROPIC_API_KEY']\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nx = env.get(name)\n", "src/intake/data_source.py"),
    ("import os\nenv = os.environ if env is None else env\nx = env.get('HADAVIN_LOCAL')\n", "src/intake/data_source.py"),
    ("import os\nenv = os.environ if env is None else env\nx = env.items()\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nx = dict(env)\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nx = {**env}\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nfor k in env:\n    pass\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nx = env.copy()\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nreturn env\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\ne2 = env\n", "src/intake/settings.py"),
    ("import os\nenv = os.environ if env is None else env\nx = env.get('HADAVIN_LOCAL', x)[0]\nenv.get(k)\n", "src/intake/settings.py"),
    ("import os\nx = (os.environ if env is None else env).items()\n", "src/intake/settings.py"),
    ("from pathlib import Path\np = Path(local, 'secrets')\n", PLACE),
    ("p = base.joinpath('secrets')\n", PLACE),
    ("p = base.joinpath('Secrets')\n", PLACE),
    ("p = base / 'SECRETS'\n", PLACE),
    ("import os\np = os.path.join(a, 'secrets', 'secrets.env')\n", PLACE),
    ("p = base / 'secrets.env'\n", "src/intake/cli.py"),
    ("p = base / 'Secrets.ENV'\n", PLACE),
    ("p = base / b'secrets.env'\n", PLACE),
    ("p = '/x/secrets/approver-passphrase.txt'\n", PLACE),
    ("p = base / 'secrets/x'\n", PLACE),
    ("p = 'secrets/'\n", PLACE),
    ("p = base / '*.env'\n", PLACE),
    ("p = f'{base}/secrets.env'\n", PLACE),
    ("p = '%s/secrets.env' % base\n", PLACE),
    ("p = '{}/secrets.env'.format(base)\n", PLACE),
    ("p = base / ('sec' + 'rets')\n", PLACE),
    ("p = base / ('sec' + 'rets' + '.env')\n", PLACE),
    ("p = base / 'approver-passphrase.txt'\n", PLACE),
    ("from pathlib import Path\nx = list(Path(local).glob('*/*.env'))\n", PLACE),
    ("from pathlib import Path\nx = list(Path(local).rglob('x'))\n", PLACE),
    ("from pathlib import Path\nx = list(Path(local).iterdir())\n", PLACE),
    ("from pathlib import Path\nx = list(Path(local).walk())\n", PLACE),
    ("import os\nx = os.listdir(local)\n", PLACE),
    ("import os\nx = list(os.walk(local))\n", PLACE),
    ("import os\nx = list(os.fwalk(local))\n", PLACE),
    ("import os as o\nx = o.scandir(local)\n", PLACE),
    ("import glob\nx = glob.glob('*')\n", PLACE),
    ("from pathlib import Path\nx = Path(a).exists()\n", PLACE),
    ("from pathlib import Path\nx = Path(a).open()\n", PLACE),
    ("from pathlib import Path\nx = Path(a).is_file()\n", PLACE),
    ("import os\nx = os.path.exists(a)\n", PLACE),
    ("import os\nx = os.stat(a)\n", PLACE),
    ("from intake import secret_store\nsecret_store.parse(s.secrets_path)\n", PLACE),
    ("from intake import secret_store as ss\nss.parse(p)\n", PLACE),
    ("from . import secret_store as ss\nss.present_names(p)\n", PLACE),
    ("import intake.secret_store as ss\nss.check_value('A', 'b')\n", PLACE),
    ("import intake.secret_store\nintake.secret_store.parse(p)\n", PLACE),
    ("from .secret_store import *\nparse(p)\n", PLACE),
    ("from intake.secret_store import *\n", PLACE),
    ("from .secret_store import parse as p\np(x)\n", PLACE),
    ("from intake.secret_store import present_names\n", PLACE),
    ("from intake import secret_store\nsecret_store.present_names(p)\n", "src/intake/cli.py"),
    ("from intake import secret_store\nsecret_store.secrets_path(local)\n", "src/intake/cli.py"),
    ("from intake import secret_store\nx = getattr(secret_store, 'parse')\n", PLACE),
    ("from intake import secret_store\nf(secret_store)\n", PLACE),
    ("from intake import secret_store\nimport functools\np = functools.partial(secret_store.get, a=1)\n", PLACE),
    ("from intake import secret_store\nf = secret_store.get\n", PLACE),
    ("x = settings.secrets_path\n", PLACE),
    ("import os\nx = os.environ.get('HOME')\nbase = x\np = base / 'secrets.env'\n", "tools/other.py"),
    ("import os\nenv = dict(os.environ)\n", "tools/sub/other.py"),
]


@pytest.mark.parametrize("src,rel", BAD, ids=[f"bad{i}" for i in range(len(BAD))])
def test_scan_catches(src, rel):
    assert scan_capabilities(src, rel), (src, rel)


GOOD = [
    ("import os\nx = os.environ.get('HADAVIN_LOCAL', '')\n", "tools/make_secrets.py"),
    ("import os\nx = os.environ['INTAKE_DEMO_DATA']\n", PLACE),
    (
        "from os import environ as _environ\nenv = _environ if env is None else env\nx = env.get('HADAVIN_LOCAL', '')\ny = env is None\n",
        "src/intake/settings.py",
    ),
    (
        "from os import environ as _environ\nx = (_environ if env is None else env).get('INTAKE_DEMO_DATA', '')\n",
        "src/intake/data_source.py",
    ),
    ("import os\ntry:\n    f = os.O_NOFOLLOW\nexcept AttributeError:\n    f = 0\n", "tools/make_secrets.py"),
    ("from intake.secret_store import API_KEY, NAMES, status\nstatus('A', local)\nNAMES\n", "src/intake/cli.py"),
    (
        "from intake import secret_store\nsecret_store.status('A', local)\nsecret_store.get('A', local=l)\nsecret_store.mode_state()\n",
        "src/intake/cli.py",
    ),
    ("from . import secret_store as ss\nss.get('A')\nss.NAMES\nss.API_KEY\n", "src/intake/cli.py"),
    (
        "from intake import secret_store\nsecret_store.parse(p)\nsecret_store.present_names(p)\nx = secret_store.get\n",
        "tools/make_secrets.py",
    ),
    ("from intake import secret_store\nsecret_store.secrets_path(local)\n", "tests/conftest.py"),
    ("from pathlib import Path\nx = Path(a).exists()\n", "src/intake/secret_store.py"),
    ("x = 'secrets'\n", "src/intake/isolation.py"),
    ('"""reads secrets.env somewhere"""\nx = 1\n', PLACE),
    ("x = __name__\ny = __file__\nz = f.__doc__\nclass A:\n    def __init__(self):\n        super().__init__()\n", PLACE),
    ("x = 'sec' + 'tion'\n", PLACE),
    ("import sys\nprint('x', file=sys.stderr)\nx = sys.platform\n", PLACE),
    ("from pathlib import Path\nx = Path(a).read_text()\n", PLACE),
]


@pytest.mark.parametrize("src,rel", GOOD, ids=[f"good{i}" for i in range(len(GOOD))])
def test_scan_allows(src, rel):
    assert scan_capabilities(src, rel) == [], (src, rel)


def test_bytes_constants_are_scanned():
    assert scan_capabilities("p = b'Secrets.Env'\n", PLACE)


# ---- workflows and compose files hold no secret names or paths (WP7 files; absent today) -------------------------------------------------------------------
def test_workflow_and_compose_files_name_no_secret():
    for base in ("workflows", "docker"):
        for p in sorted((ROOT / base).rglob("*")) if (ROOT / base).is_dir() else []:
            if p.is_file() and p.suffix in {".json", ".yml", ".yaml"}:
                text = p.read_text(encoding="utf-8")
                for name in SECRET_NAMES - {"N8N_ENCRYPTION_KEY"}:  # the compose file names the n8n key (name only, no value) by design
                    assert name not in text, (p.name, name)
                assert not is_key_path("x/" + "secrets/") or "secrets/" not in text.lower(), p.name


# ---- working-tree guard for invisible characters (a formatter can inline an escape before the commit) ------------------------------------------
INVISIBLE = re.compile(
    "["
    + "".join(chr(c) for lo, hi in ((0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2064), (0xFEFF, 0xFEFF)) for c in range(lo, hi + 1))
    + "]"
)


def test_no_invisible_character_in_working_tree_files_including_untracked():
    bad = []
    for base in ("src", "tools", "tests", "config"):
        for p in sorted((ROOT / base).rglob("*")):
            if (
                not p.is_file()
                or "__pycache__" in p.parts
                or "core_copy" in p.parts
                or p.suffix not in {".py", ".json", ".txt", ".md", ".csv"}
            ):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if INVISIBLE.search(text):
                bad.append(p.relative_to(ROOT).as_posix())
    assert not bad, bad


def test_the_invisible_scan_catches_a_literal():
    assert INVISIBLE.search("a" + chr(0xFEFF)) and INVISIBLE.search(chr(0x202E)) and not INVISIBLE.search("plain " + chr(0xE9))
