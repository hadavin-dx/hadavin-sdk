"""Strict JSON for every WP0-owned reader of input or config (settings, rules, checks, isolation): NaN, Infinity, -Infinity, duplicate keys and deep
nesting are refused. Each behavioural test fails on the code before the seam (json.loads accepts all of them)."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import date

import pytest
from astscan import build_aliases, dotted

from conftest import ROOT
from intake import checks, isolation, rules, settings, strictjson
from intake.codes import ConfigError, Refused

BAD_TEXTS = [
    '{"a": NaN}',
    '{"a": Infinity}',
    '{"a": -Infinity}',
    '{"a": 1e999}',
    '{"a": -1e999}',
    '{"a": 1, "a": 2}',
    '{"o": {"x": 1, "x": 1}}',
    '[{"k": 1, "k": 2}]',
    "[" * 100000 + "]" * 100000,  # the parser runs out of stack
    "[" * 70 + "]" * 70,  # within the parser's limit, over the depth cap
    '{"a":' * 70 + "1" + "}" * 70,
]
GOOD_TEXTS = ['{"a": 1.5, "b": [1, 2, {"c": null}], "d": "NaN"}', "[" * 60 + "]" * 60, "{}", "[]", '"x"', "0"]


@pytest.mark.parametrize("text", BAD_TEXTS, ids=lambda s: f"{s[:12]}..len{len(s)}")
def test_the_seam_refuses(text):
    with pytest.raises(ValueError):
        strictjson.loads(text)


@pytest.mark.parametrize("text", GOOD_TEXTS)
def test_the_seam_accepts_ordinary_json(text):
    assert strictjson.loads(text) == json.loads(text)


def test_bytes_and_bad_utf8():
    assert strictjson.loads(b'{"a": 1}') == {"a": 1}
    with pytest.raises(ValueError):
        strictjson.loads(b"\xff\xfe")


def test_the_core_copy_is_the_registered_byte_copy():
    meta = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))["allowed_local"]["src/intake/core_copy/strict_json.py"]
    raw = (ROOT / "src/intake/core_copy/strict_json.py").read_bytes()
    assert b"\r\n" not in raw and hashlib.sha256(raw).hexdigest() == meta["source_sha256"] and meta["source_sha256"] in meta["reason"]
    assert meta["expires"] == "2027-01-31" and "src/intake/core_copy/strict_json.py" in (ROOT / "CORE_COPIES.md").read_text(
        encoding="utf-8"
    )


JSON_OK_ATTRS = frozenset({"dumps", "dump"})
# exact files allowed to touch the json parser (no blanket directory exemption)
JSON_EXEMPT = {
    "src/intake/core_copy/strict_json.py": "the byte copy itself",
    "src/intake/adapters/fake_erp.py": "existing order-flow seed loader; owner: the order-flow demo (not Intake); adopting strictjson is the lead-scheduled reuse step of errata 35",
}


def scan_json(source: str, rel: str) -> list[str]:
    """Any route to the json parser or to ``ast.literal_eval`` through import aliases, star imports and getattr (a convention scan, not a proof)."""
    tree = ast.parse(source)
    alias, stars = build_aliases(tree)
    found = [f"star import of {s}" for s in stars if s in ("json", "ast", "json.decoder")]
    for node in ast.walk(tree):
        d = dotted(node, alias) if isinstance(node, ast.Name | ast.Attribute) else None
        if d:
            parts = d.split(".")
            if parts[0] == "json" and len(parts) >= 2 and parts[1] not in JSON_OK_ATTRS:
                found.append(f"{d} (line {node.lineno})")
            if d in ("ast.literal_eval", "builtins.eval"):
                found.append(f"{d} (line {node.lineno})")
        if isinstance(node, ast.ImportFrom) and node.module in ("json", "json.decoder", "ast"):
            found += [f"from {node.module} import {a.name}" for a in node.names if a.name not in JSON_OK_ATTRS]
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "json"
            and not node.args
            and not node.keywords
        ):
            found.append(f"response.json() (line {node.lineno})")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and node.args:
            if (dotted(node.args[0], alias) or "") in ("json", "ast", "json.decoder"):
                found.append(f"getattr on a json module (line {node.lineno})")
    return sorted(set(found))


def test_no_other_route_to_the_json_parser_in_the_product_code():
    """Class-level: any parse of JSON from a file or request in src/intake goes through the seam; exact exempt files only."""
    bad = {}
    for p in sorted((ROOT / "src" / "intake").rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if "__pycache__" in p.parts or rel in JSON_EXEMPT:
            continue
        f = scan_json(p.read_text(encoding="utf-8"), rel)
        if f:
            bad[rel] = f
    assert not bad, bad


@pytest.mark.parametrize(
    "src",
    [
        "import json\njson.loads('1')\n",
        "import json\njson.load(f)\n",
        "import json as j\nj.loads('1')\n",
        "import json\nx = json.JSONDecoder()\n",
        "import json\nx = json.decoder.JSONDecoder()\n",
        "import json.decoder\nx = json.decoder.JSONDecoder()\n",
        "from json import JSONDecoder\nJSONDecoder()\n",
        "from json import loads as l\nl('1')\n",
        "from json.decoder import JSONDecoder\n",
        "from json import *\n",
        "import json\nx = getattr(json, 'loads')\n",
        "import ast\nast.literal_eval('1')\n",
        "from ast import literal_eval\n",
        "import ast as a\na.literal_eval('1')\n",
    ],
)
def test_the_json_scan_catches(src):
    assert scan_json(src, "src/intake/pipeline.py"), src


@pytest.mark.parametrize(
    "src", ["import json\njson.dumps({})\njson.dump({}, f)\n", "from json import dumps\n", "import ast\nast.parse('x')\n"]
)
def test_the_json_scan_allows_writing_and_other_ast_use(src):
    assert scan_json(src, "src/intake/pipeline.py") == [], src


UNTOUCHED_ORDER_FLOW = frozenset(JSON_EXEMPT)


def test_the_json_exempt_files_exist():
    for rel in JSON_EXEMPT:
        assert (ROOT / rel).is_file(), rel


@pytest.mark.parametrize(
    "text",
    [
        '"\\ud800"',
        '{"\\udfff": 1}',
        '["\\udc00"]',
        '{"a": ["x", {"\\ud800k": 1}]}',
        "\ufeff{}",
        "[1,]",
        '{"a": 1,}',
        "1" * 5000,
        "",
        "{",
        "NaN",
        "[1] [2]",
    ],
    ids=lambda s: f"{s[:14]}..len{len(s)}",
)
def test_more_hostile_inputs_are_refused(text):
    with pytest.raises(ValueError):
        strictjson.loads(text)


def test_a_valid_surrogate_pair_is_accepted():
    assert strictjson.loads('"\\ud83d\\ude00"') == chr(0x1F600)


def test_the_kit_source_matches_the_registered_sha_and_commit():
    """The registered sha256 is self-referential (it pins our own copy); with the kit file reachable (INTAKE_KIT_SOURCE) recompute it from the source and
    check that the recorded kit commit exists. Under CI (the CI variable set) a missing kit file FAILS instead of skipping: the CI workflow must provide it."""
    import os
    import subprocess
    from pathlib import Path

    meta = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))["allowed_local"]["src/intake/core_copy/strict_json.py"]
    assert re.fullmatch(r"[0-9a-f]{40}", meta["source_commit"])
    src = os.environ.get("INTAKE_KIT_SOURCE")
    if not src or not Path(src).is_file():
        if os.environ.get("CI"):
            pytest.fail("INTAKE_KIT_SOURCE (the kit's strict_json.py) must be set under CI")
        pytest.skip("INTAKE_KIT_SOURCE (the kit's strict_json.py) is not set")
    assert hashlib.sha256(Path(src).read_bytes()).hexdigest() == meta["source_sha256"]
    r = subprocess.run(
        ["git", "-C", str(Path(src).parent), "cat-file", "-e", meta["source_commit"] + "^{commit}"], capture_output=True, check=False
    )
    assert r.returncode == 0, "the recorded kit commit does not exist in the kit repository"


# ---- the four WP0-owned readers ---------------------------------------------------------------------------------------------------------------------
def write(tmp_path, text, name="x.json"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.parametrize("text", ['{"a": NaN}', '{"a": 1, "a": 2}', "[" * 100000 + "]" * 100000], ids=["nan", "duplicate", "deep"])
def test_settings_config_refuses(tmp_path, text):
    with pytest.raises(ConfigError) as ei:
        settings.read_config(write(tmp_path, text))
    assert ei.value.code == "bad_config"


def test_settings_config_refuses_a_nan_value_inside_a_valid_looking_file(tmp_path):
    d = (ROOT / "config" / "service.json").read_text(encoding="utf-8").replace('"max_tokens": 2048', '"max_tokens": NaN')
    with pytest.raises(ConfigError):
        settings.read_config(write(tmp_path, d))
    dup = (ROOT / "config" / "service.json").read_text(encoding="utf-8").replace('"port": 8750,', '"port": 8750, "port": 8751,')
    with pytest.raises(ConfigError):
        settings.read_config(write(tmp_path, dup))


PRICES = (
    '{"prices_micro_usd_per_million_tokens": {"read": {"in": 1, "out": 1}, "fallback": {"in": 1, "out": 1}}, '
    '"prices_as_of": "2026-11-03", "anthropic_version": "v"%s}'
)


def test_prices_file_control_is_valid(tmp_path):
    assert settings.load_prices(write(tmp_path, PRICES % ""), date(2026, 11, 3)).read_in == 1


@pytest.mark.parametrize(
    "extra",
    [', "prices_as_of": "2026-11-02"', ', "extra": NaN', ', "extra": ' + "[" * 100000 + "]" * 100000],
    ids=["duplicate", "nan", "deep"],
)
def test_prices_file_refuses(tmp_path, extra):
    with pytest.raises(Refused) as ei:
        settings.load_prices(write(tmp_path, PRICES % extra), date(2026, 11, 3))
    assert ei.value.code == "prices_missing"


def test_kill_switch_with_a_duplicate_key_is_engaged(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CONFIG", tmp_path)
    write(tmp_path, '{"executor": {"kill_switch": true, "kill_switch": false}, "client_id": "x"}', "policy.json")
    assert settings.read_kill_switch() is True  # json.loads would have taken the last value (false)
    write(tmp_path, '{"executor": {"kill_switch": NaN}}', "policy.json")
    assert settings.read_kill_switch() is True


@pytest.mark.parametrize("text", ['{"a": NaN}', '{"a": 1, "a": 2}', "[" * 100000 + "]" * 100000], ids=["nan", "duplicate", "deep"])
def test_rules_isolation_and_checks_readers_refuse(tmp_path, monkeypatch, text):
    p = write(tmp_path, text)
    with pytest.raises(ValueError):
        rules.load_policy(p)
    with pytest.raises(ValueError):
        rules.load_exceptions(p)
    with pytest.raises(ValueError):
        isolation.policy_namespaces(p)
    monkeypatch.setattr(checks, "CONFIG", tmp_path)
    with pytest.raises(ValueError):
        checks._j("x.json")


def test_the_shipped_config_files_still_load_strictly():
    assert rules.load_policy().max_lines_per_draft == 25
    assert isolation.policy_namespaces()[0] == "demo-intake" and rules.load_exceptions() and checks._j("bank_spec.json")
    assert settings.read_config()["service"]["port"] == 8750 and settings.read_tenant_id() == "demo-intake"


def test_duplicate_keys_written_with_different_escapes_are_duplicates():
    for text in ('{"a": 1, "\\u0061": 2}', '{"\\u00e9": 1, "\\u00E9": 2}', '{"x": {"k": 1, "\\u006b": 2}}'):
        with pytest.raises(ValueError):
            strictjson.loads(text)


def test_a_raw_lone_surrogate_in_the_text_and_nul_are_refused():
    for text in ('"' + chr(0xD800) + '"', '{"' + chr(0xDFFF) + '": 1}', '"' + chr(0) + '"', '"\\u0000"', '{"\\u0000": 1}'):
        with pytest.raises(ValueError):
            strictjson.loads(text)


def test_bom_bytes_through_the_path_reader(tmp_path):
    p = tmp_path / "x.json"
    p.write_bytes(chr(0xFEFF).encode() + b"{}")
    with pytest.raises(ValueError):
        strictjson.load_path(p)


def test_a_huge_integer_is_refused_even_with_the_interpreter_limit_disabled():
    import sys

    old = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(0)  # no limit: the parser itself would accept it
    try:
        assert json.loads("1" * 5000) > 0  # the plain parser accepts it
        for text in ("1" * 5000, "[" + "9" * 40 + "]", '{"a": -' + "9" * 40 + "}"):
            with pytest.raises(ValueError):
                strictjson.loads(text)
        assert strictjson.loads("[" + str(2**79) + "]") == [2**79]  # a large but sane integer still loads
    finally:
        sys.set_int_max_str_digits(old)


def test_json_scan_catches_response_json_calls():
    assert scan_json("r = client.get(u)\nx = r.json()\n", "src/intake/pipeline.py")
    assert scan_json("x = requests.post(u).json()\n", "src/intake/pipeline.py")
    assert scan_json("import httpx\nx = httpx.get(u).json()\n", "src/intake/pipeline.py")
    assert scan_json("x = obj.json(arg)\n", "src/intake/pipeline.py") == []  # not the zero-argument response form


def test_a_json_file_over_the_size_cap_is_refused_before_parsing(tmp_path):
    p = tmp_path / "big.json"
    p.write_bytes(b"[" + b"1," * 1_200_000 + b"1]")
    assert p.stat().st_size > strictjson.MAX_FILE_BYTES
    with pytest.raises(ValueError):
        strictjson.load_path(p)
    small = tmp_path / "s.json"
    small.write_text("[1]", encoding="utf-8")
    assert strictjson.load_path(small) == [1] and strictjson.load_path(small, max_bytes=3) == [1]
    with pytest.raises(ValueError):
        strictjson.load_path(small, max_bytes=2)


def test_the_kit_test_fails_under_ci_without_the_kit_file():
    """Meta test: run the kit test in a child pytest with CI set and no INTAKE_KIT_SOURCE; it must FAIL (not skip). Kills the 'skips under CI' mutant."""
    import os
    import subprocess
    import sys

    env = {k: v for k, v in os.environ.items() if k != "INTAKE_KIT_SOURCE"}
    env["CI"] = "1"
    node = "tests/test_strict_json.py::test_the_kit_source_matches_the_registered_sha_and_commit"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", node],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert r.returncode != 0 and "must be set under CI" in r.stdout + r.stderr, r.stdout[-500:]
    env["CI"] = ""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", node],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert r.returncode == 0 and "skipped" in r.stdout, r.stdout[-500:]
