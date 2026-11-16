"""Removal guard (design 7.1): features and vendors that must not exist here, proven on the real tree and on bad trees.

Forbidden words are built from parts, never written as literals, so this file cannot trip the guard it implements.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def j(*parts: str) -> str:
    return "".join(parts)


MODULES = {
    j("eld", "ane"),
    j("eld", "ane_slack"),
    "critique",
    "autonomy",
    "discuss",
    "extend",
    "plan_review",
    "plan_shape",
    j("aws", "watch"),
    j("dep", "watch"),
    "code_fix",
    "code_gate",
    "github_app",
    j("trip", "wire"),
    "decide",
    "routing",
    "workflows",
    "activities",
    "codec",
    "runtime_base",
    "temporal_history",
    "mcp_server",
    "approval_page",
    "passkeys",
    "slack_login",
    "chatops",
}
VENDORS = {
    j("temporal", "io"),
    j("slack", "_sdk"),
    "torch",
    "transformers",
    "boto3",
    "botocore",
    "kubernetes",
    "psycopg",
    "webauthn",
    "opentelemetry",
    "anthropic",
    "openai",
    "google",
}
CONFIG_KEYS = {
    "autonomy",
    "critic",
    j("eld", "ane"),
    "discuss",
    "discussion",
    "discussion_channel",
    "code_fix",
    "auto_merge",
    "second_opinion",
}
PHRASES = [
    j("eld", "ane"),
    j("ward", " ", "gem"),
    j("rebut", "tal"),
    j("objection", " ", "round"),
    j("discussion", " ", "channel"),
    j("autonomy", " ", "level"),
    j("conversations", ".", "history"),
    j("conversations", ".", "replies"),
]
PHRASE_RX = re.compile(
    r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(p) for p in PHRASES) + r")(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
LEVEL_RX = re.compile(r"^L[0-2]$")


def py_files(root: Path) -> list[Path]:
    return [
        p
        for d in ("src", "tests")
        for p in sorted((root / d).rglob("*.py"))
        if "__pycache__" not in p.parts
    ]


def yaml_files(root: Path) -> list[Path]:
    return [
        p
        for d in ("config", "src")
        if (root / d).is_dir()
        for p in sorted((root / d).rglob("*.yaml"))
    ]


def module_problems(root: Path) -> list[str]:
    out = []
    for d in ("src", "tests"):
        for p in (root / d).rglob("*"):
            if p.is_file() and p.stem in MODULES and "__pycache__" not in p.parts:
                out.append(f"file {p.name}")
    for p in py_files(root):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names = [n.module or ""] + [a.name for a in n.names if not n.module or n.level]
            for dotted in names:
                if set(dotted.split(".")) & MODULES:
                    out.append(f"{p.name}:{n.lineno}: import of a removed module")
    return out


def vendor_problems(root: Path) -> list[str]:
    out = []
    for p in py_files(root):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            mods = (
                [a.name for a in n.names]
                if isinstance(n, ast.Import)
                else ([n.module or ""] if isinstance(n, ast.ImportFrom) and n.level == 0 else [])
            )
            out += [
                f"{p.name}:{n.lineno}: vendor import {m.split('.')[0]}"
                for m in mods
                if m.split(".")[0] in VENDORS
            ]
    return out


def walk_yaml(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield str(k), v, path
            yield from walk_yaml(v, path + "/" + str(k))
    elif isinstance(node, list):
        for v in node:
            yield from walk_yaml(v, path)


def config_problems(root: Path) -> list[str]:
    out = []
    for p in yaml_files(root):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for k, v, _path in walk_yaml(doc):
            if k.casefold() in CONFIG_KEYS:
                out.append(f"{p.name}: key {k}")
            if k == "levels":
                vals = v if isinstance(v, list) else [v]
                out += [f"{p.name}: level {x}" for x in vals if x not in ("shadow", "suggest")]
            if isinstance(v, str) and LEVEL_RX.match(v):
                out.append(f"{p.name}: value {v}")
    return out


def text_problems(root: Path) -> list[str]:
    out = []
    for p in py_files(root):
        text = p.read_text(encoding="utf-8")
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type in (tokenize.COMMENT, tokenize.STRING) and PHRASE_RX.search(t.string):
                out.append(f"{p.name}:{t.start[0]}: removed wording")
    for d in ("src", "config", "docs"):
        base = root / d
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                if p.suffix in (".md", ".yaml", ".yml") and PHRASE_RX.search(
                    p.read_text(encoding="utf-8")
                ):
                    out.append(f"{p.name}: removed wording")
    return out


# ----------------------------------------------------------------------------------- real tree
def test_no_removed_module_exists_or_is_imported():
    assert module_problems(ROOT) == []


def test_no_vendor_import_in_src_or_tests():
    assert vendor_problems(ROOT) == []


def test_config_has_no_removed_keys_levels_or_values():
    assert config_problems(ROOT) == []


def test_no_removed_wording_in_comments_strings_or_text_files():
    assert text_problems(ROOT) == []


def test_action_kind_is_the_closed_set_of_six():
    from jagrat.models import ActionKind

    assert {a.value for a in ActionKind} == {
        "restart_pods",
        "scale_up",
        "rollback_deploy",
        "terminate_connections",
        "no_action",
        "escalate_to_human",
    }


# ----------------------------------------------------------------------------------- the guard bites
def tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, body in files.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
    return tmp_path


def test_module_guard_flags_file_and_lazy_import(tmp_path):
    bad = tree(
        tmp_path,
        {
            "src/jagrat/critique.py": "x = 1\n",
            "src/jagrat/a.py": "def f():\n    from .workflows import X\n",
            "src/jagrat/ok.py": "from .extended import y\nextend = 1\n",
        },
    )
    probs = module_problems(bad)
    assert len(probs) == 2 and any("file critique" in p for p in probs)


def test_vendor_guard_flags_any_depth(tmp_path):
    bad = tree(
        tmp_path,
        {
            "src/jagrat/a.py": "def f():\n    import boto3.session\n",
            "tests/test_x.py": "from google.cloud import x\n",
            "src/jagrat/ok.py": "import json\n",
        },
    )
    assert len(vendor_problems(bad)) == 2


def test_config_guard_flags_keys_levels_and_values(tmp_path):
    bad = tree(tmp_path, {"src/c.yaml": "a:\n  Autonomy: 1\nlevels: [shadow, act]\nb: L1\n"})
    assert len(config_problems(bad)) == 3
    ok = tree(tmp_path / "ok", {"src/c.yaml": "levels: [shadow, suggest]\nname: L10\n"})
    assert config_problems(ok) == []


def test_text_guard_flags_comment_string_and_markdown_but_not_substrings(tmp_path):
    word = j("eld", "ane")
    reb, obj = j("rebut", "tal"), j("objection", " ", "round")
    bad = tree(
        tmp_path,
        {
            "src/jagrat/a.py": f"# {word} said so\nx = 'a {reb}'\n",
            "docs/n.md": f"an {obj} happened\n",
        },
    )
    assert len(text_problems(bad)) == 3
    ok = tree(tmp_path / "ok", {"src/jagrat/a.py": f"x = '{word}s_not_a_word_x'\ny = '{reb}s'\n"})
    assert text_problems(ok) == []
