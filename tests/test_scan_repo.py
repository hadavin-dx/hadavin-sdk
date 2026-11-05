"""tools/scan_repo.py: each rule hits, the documented placeholder and clean files do not, the allow-list works.
Fake secrets are built from parts so this file itself never holds one."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "scan_repo.py"
BANNED_NAME = "Context" + " Lake"  # a BANNED entry, split so this file stays clean
EXAMPLE_KEY = "AKIA" + "IOSFODNN7EXAMPLE"

CASES = {
    "aws-access-key-id": "k = '" + "AKIA" + "ABCDEFGHIJKLMNOP" + "'",
    "anthropic-api-key": "k = '" + "sk-" + "ant-" + "a" * 24 + "'",
    "sk-api-key": "k = '" + "sk-" + "b" * 40 + "'",
    "private-key-header": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
    "slack-token": "t = '" + "xox" + "b-" + "1234567890-abcdef" + "'",
    "github-token": "t = '" + "gh" + "p_" + "c" * 36 + "'",
    "github-fine-grained-token": "t = '" + "github" + "_pat_" + "d" * 30 + "'",
    "password-literal": "pass" + "word = 'hunter22xyz'",
    "banned-name": "see " + BANNED_NAME,
}


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode())
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607
    return tmp_path


def _scan(repo):
    r = subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), "--root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, r.stdout


@pytest.mark.parametrize("rule", CASES)
def test_each_rule_hits_and_masks(tmp_path, rule):
    rc, out = _scan(_repo(tmp_path, {"a/x.txt": "ok\n" + CASES[rule] + "\n"}))
    assert rc == 1
    assert f"a/x.txt:2: {rule} " in out
    assert CASES[rule].split("'")[-2:-1] != out  # sanity: output is not the raw line
    assert "*" in out and "k = " not in out


def test_masked_output_never_holds_the_full_secret(tmp_path):
    _, out = _scan(_repo(tmp_path, {"x.txt": CASES["sk-api-key"]}))
    assert "b" * 40 not in out


def test_aws_example_placeholder_is_allowed(tmp_path):
    assert _scan(_repo(tmp_path, {"x.txt": f"key = {EXAMPLE_KEY}\n"})) == (0, "\n")


def test_psql_variable_is_not_a_password_literal(tmp_path):
    assert _scan(_repo(tmp_path, {"x.sql": "ALTER ROLE r PASSWORD :'ro_password';\n"}))[0] == 0


def test_clean_repo_and_binary_files_pass(tmp_path):
    files = {"a.py": "print('hi')\n", "b.bin": b"\0" + CASES["sk-api-key"].encode()}
    assert _scan(_repo(tmp_path, files))[0] == 0


def test_untracked_files_are_not_scanned(tmp_path):
    _repo(tmp_path, {"a.py": "x = 1\n"})
    (tmp_path / "late.txt").write_text(CASES["sk-api-key"])
    assert _scan(tmp_path)[0] == 0


def test_allowlist_skips_the_listed_file_only(tmp_path):
    allow = SCRIPT.parent / "scan_allowlist.txt"
    before = allow.read_text(encoding="utf-8")
    repo = _repo(tmp_path, {"ok.txt": CASES["sk-api-key"], "bad.txt": CASES["sk-api-key"]})
    try:
        allow.write_text(before + "ok.txt:fixture for the test\n", encoding="utf-8")
        rc, out = _scan(repo)
    finally:
        allow.write_text(before, encoding="utf-8")
    assert rc == 1 and "bad.txt:1:" in out and "ok.txt" not in out


def test_extra_banned_list_is_read(tmp_path):
    extra = SCRIPT.parent / "scan_banned_extra.txt"
    before = extra.read_text(encoding="utf-8")
    repo = _repo(tmp_path, {"x.txt": "contains zzfakename here\n"})
    try:
        extra.write_text(before + "zzfakename\n", encoding="utf-8")
        rc, out = _scan(repo)
    finally:
        extra.write_text(before, encoding="utf-8")
    assert rc == 1 and "x.txt:1: banned-name" in out
