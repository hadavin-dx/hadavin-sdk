"""tools/scan_repo.py: each rule hits, near misses and the documented placeholder do not, the allow-list is rule-scoped.
Fake secrets are built from parts so this file itself never holds one. The real tools/*.txt files are never rewritten:
the script takes --allowlist/--extra/--banned-src."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "scan_repo.py"
BANNED_NAME = "Context" + " Lake"  # a BANNED entry, split so this file stays clean
EXAMPLE_KEY = "AKIA" + "IOSFODNN7EXAMPLE"

CASES = {
    "cloud-id-prefix": "k = '" + "AKIA" + "ABCDEFGHIJKLMNOP" + "'",
    "llm-id-ant": "k = '" + "sk-" + "ant-" + "a" * 24 + "'",
    "llm-id-sk": "k = '" + "sk-" + "b" * 40 + "'",
    "pem-block-header": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
    "chat-id-xox": "t = '" + "xox" + "b-" + "1234567890-abcdef" + "'",
    "vcs-id-classic": "t = '" + "gh" + "p_" + "c" * 36 + "'",
    "vcs-id-fine": "t = '" + "github" + "_pat_" + "d" * 30 + "'",
    "credential-literal": "pass" + "word = 'hunter22xyz'",
    "banned-name": "see " + BANNED_NAME,
}
# more shapes of the same rules that must also be caught
MORE_HITS = {
    "cloud-id-prefix": "k = " + "ASIA" + "ABCDEFGHIJKLMNOP",
    "llm-id-sk": "k = '" + "sk-" + "proj-" + "e" * 30 + "_" + "f" * 10 + "'",
    "pem-block-header": "-----BEGIN " + "PGP PRIVATE" + " KEY BLOCK-----",
    "chat-id-xox": "t = '" + "xox" + "e-" + "1234567890-abcdef" + "'",
    "credential-literal": "DB_PASS" + "WORD = 'hunter22xyz'",
}
# shapes that must NOT be flagged (too short, wrong prefix, no literal)
NEAR_MISSES = [
    "k = 'sk-short'",
    "t = 'ghp_short'",
    "k = AKIA" + "SHORT",
    "pass" + "word = 'short'",
    "x = os.environ['DB_PASS" + "WORD']",
]


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode())
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607
    return tmp_path


def _scan(repo, allow="", extra="", banned_src=None):
    """Run the script on `repo` with temporary list files (never the real ones)."""
    work = repo.parent / (repo.name + "-lists")
    work.mkdir(exist_ok=True)
    allow_f, extra_f = work / "allow.txt", work / "extra.txt"
    allow_f.write_text(allow, encoding="utf-8", newline="\n")
    extra_f.write_text(extra, encoding="utf-8", newline="\n")
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--root",
        str(repo),
        "--allowlist",
        str(allow_f),
        "--extra",
        str(extra_f),
    ]
    if banned_src is not None:
        cmd += ["--banned-src", str(banned_src)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    return r.returncode, r.stdout + r.stderr


@pytest.mark.parametrize("rule", CASES)
def test_each_rule_hits_and_prints_no_text(tmp_path, rule):
    rc, out = _scan(_repo(tmp_path, {"a/x.txt": "ok\n" + CASES[rule] + "\n"}))
    assert rc == 1
    assert f"a/x.txt:2: {rule}" in out
    assert out.strip() == f"a/x.txt:2: {rule}"


@pytest.mark.parametrize("rule", MORE_HITS)
def test_other_shapes_of_each_rule_hit(tmp_path, rule):
    rc, out = _scan(_repo(tmp_path, {"a.txt": MORE_HITS[rule] + "\n"}))
    assert rc == 1 and f"a.txt:1: {rule}" in out


@pytest.mark.parametrize("line", NEAR_MISSES)
def test_near_misses_are_not_flagged(tmp_path, line):
    assert _scan(_repo(tmp_path, {"a.txt": line + "\n"}))[0] == 0


def test_output_never_holds_any_part_of_the_secret(tmp_path):
    _, out = _scan(_repo(tmp_path, {"x.txt": CASES["llm-id-sk"]}))
    assert "bbbb" not in out
    _, out = _scan(_repo(tmp_path, {"y.txt": CASES["vcs-id-classic"]}))
    assert "cccc" not in out


def test_aws_example_placeholder_is_allowed(tmp_path):
    assert _scan(_repo(tmp_path, {"x.txt": f"key = {EXAMPLE_KEY}\n"})) == (0, "\n")


def test_a_real_key_beside_the_example_is_still_flagged(tmp_path):
    line = f"a = {EXAMPLE_KEY} b = " + "AKIA" + "ABCDEFGHIJKLMNOP"
    rc, out = _scan(_repo(tmp_path, {"x.txt": line + "\n"}))
    assert rc == 1 and "cloud-id-prefix" in out


def test_psql_variable_is_not_a_password_literal(tmp_path):
    assert _scan(_repo(tmp_path, {"x.sql": "ALTER ROLE r PASSWORD :'ro_password';\n"}))[0] == 0


def test_clean_repo_and_binary_files_pass(tmp_path):
    files = {"a.py": "print('hi')\n", "b.bin": b"\0" + CASES["llm-id-sk"].encode()}
    assert _scan(_repo(tmp_path, files))[0] == 0


def test_untracked_files_are_not_scanned(tmp_path):
    _repo(tmp_path, {"a.py": "x = 1\n"})
    (tmp_path / "late.txt").write_text(CASES["llm-id-sk"])
    assert _scan(tmp_path)[0] == 0


def test_allowlist_skips_only_the_listed_rule_on_the_listed_file(tmp_path):
    files = {
        "ok.txt": CASES["llm-id-sk"],
        "bad.txt": CASES["llm-id-sk"],
        "ok2.txt": CASES["vcs-id-classic"],
    }
    rc, out = _scan(
        _repo(tmp_path, files),
        allow="ok.txt:llm-id-sk:fixture for the test\nok2.txt:llm-id-sk:wrong rule\n",
    )
    assert rc == 1 and "bad.txt:1:" in out and "ok.txt:1:" not in out
    assert "ok2.txt:1: vcs-id-classic" in out  # a different rule on a listed file is still flagged


def test_allowlist_entry_without_a_reason_or_for_a_missing_file_fails(tmp_path):
    repo = _repo(tmp_path, {"a.txt": "x = 1\n"})
    assert "needs path:rule:reason" in _scan(repo, allow="a.txt:sk-api-key\n")[1]
    rc, out = _scan(repo, allow="gone.txt:llm-id-sk:was needed once\n")
    assert rc == 1 and "stale entry, gone.txt is not tracked" in out


def test_extra_banned_list_is_read_and_the_list_file_does_not_flag_itself(tmp_path):
    repo = _repo(
        tmp_path,
        {"x.txt": "contains zzfakename here\n", "tools/scan_banned_extra.txt": "zzfakename\n"},
    )
    rc, out = _scan(repo, extra="zzfakename\n")
    assert rc == 1 and "x.txt:1: banned-name" in out
    assert "tools/scan_banned_extra.txt" not in out


def test_missing_or_empty_banned_list_fails_closed(tmp_path):
    repo = _repo(tmp_path, {"a.txt": "x = 1\n"})
    empty = tmp_path / "empty_src.py"
    empty.write_text("OTHER = ('x',)\n", encoding="utf-8")
    rc, out = _scan(repo, banned_src=empty)
    assert rc != 0 and "no BANNED names found" in out
    annotated = tmp_path / "ann_src.py"
    annotated.write_text("BANNED: tuple = ('zzfake',)\n", encoding="utf-8")
    repo2 = _repo(tmp_path / "r2", {"a.txt": "has zzfake\n"})
    assert _scan(repo2, banned_src=annotated)[0] == 1


def test_allowlist_entry_with_an_empty_reason_fails(tmp_path):
    repo = _repo(tmp_path, {"a.txt": "x = 1\n"})
    rc, out = _scan(repo, allow="a.txt:llm-id-sk:\n")
    assert rc == 1 and "needs path:rule:reason" in out


def test_long_word_runs_do_not_hang_the_password_rule(tmp_path):
    """A minified or base64 line must not cost quadratic time (the rule has no open-ended prefix)."""
    import time

    repo = _repo(tmp_path, {"min.js": "a" * 300_000 + "\n" + "pass" + "word" * 50_000 + "\n"})
    start = time.monotonic()
    rc, _ = _scan(repo)
    # A wall-clock ceiling on purpose, and not a growth test: the scan runs in a child process (processor time of this
    # process would not count it), and the failure this guards against is a hang, not a slow-down. Measured on 2026-11-11
    # (Linux, quiet machine): 0.09 s for the whole test. A quadratic cost on a line of 300,000 characters is about
    # 9 * 10**10 steps, far more than 20 s, so the ceiling sits about 200 times above the normal time and far below the
    # failure; a busy machine cannot move one across the other.
    assert rc == 0 and time.monotonic() - start < 20
