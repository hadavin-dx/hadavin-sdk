"""tools/scan_repo.py: each rule hits, near misses and the documented placeholder do not, the allow-list is rule-scoped.
Fake secrets are built from parts so this file itself never holds one. The real tools/*.txt files are never rewritten:
the script takes --allowlist/--extra/--banned-src."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
# tests/test_scan_repo_mutations.py points this at a deliberately broken copy of the script to prove these tests notice
SCRIPT = Path(os.environ.get("SCAN_REPO_SCRIPT") or REPO_ROOT / "tools" / "scan_repo.py")
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


def _repo(tmp_path, files, links=None):
    """A git repo with `files` (text or bytes) and, optionally, symlinks (`links` maps a path to its target text)."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode())
    for name, target in (links or {}).items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            p.symlink_to(target)
        except OSError:
            pytest.skip("this machine cannot make symbolic links")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607
    return tmp_path


def _scan(repo, allow="", extra="", banned_src=None, suppress="", args=()):
    """Run the script on `repo` with temporary list files (never the real ones)."""
    work = repo.parent / (repo.name + "-lists")
    work.mkdir(exist_ok=True)
    allow_f, extra_f, supp_f = work / "allow.txt", work / "extra.txt", work / "supp.txt"
    supp_f.write_text(suppress, encoding="utf-8", newline="\n")
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
        "--suppressions",
        str(supp_f),
    ]
    if banned_src is not None:
        cmd += ["--banned-src", str(banned_src)]
    cmd += list(args)
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


def test_clean_repo_and_clean_binary_files_pass(tmp_path):
    files = {"a.py": "print('hi')\n", "b.bin": b"\0\x01\xff\xfe" + bytes(range(256)) + b"\n"}
    assert _scan(_repo(tmp_path, files)) == (0, "\n")


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
        allow="ok.txt:llm-id-sk:fixture for the test\nok2.txt:llm-id-sk:the wrong rule on purpose\n",
    )
    assert rc == 1 and "bad.txt:1:" in out and "ok.txt:1:" not in out
    assert "ok2.txt:1: vcs-id-classic" in out  # a different rule on a listed file is still flagged


def test_allowlist_entry_without_a_reason_or_for_a_missing_file_fails(tmp_path):
    repo = _repo(tmp_path, {"a.txt": "x = 1\n"})
    assert "needs path:rule:reason" in _scan(repo, allow="a.txt:sk-api-key\n")[1]
    assert _scan(repo, allow="a.txt:llm-id-sk:reviewed fixture for the test\n")[0] == 0
    rc, out = _scan(repo, allow="gone.txt:llm-id-sk:was needed once\n")
    assert rc == 1 and "stale entry, gone.txt is not tracked" in out


def test_extra_banned_list_is_read_and_the_list_file_does_not_flag_itself(tmp_path):
    repo = _repo(
        tmp_path,
        {"x.txt": "contains zzfakename here\n", "tools/scan_banned_extra.txt": "zzfakename\n"},
    )
    pin = _supp_line("tools/scan_banned_extra.txt", "scanner-config-file", _sha("zzfakename\n"))
    rc, out = _scan(repo, extra="zzfakename\n", suppress=pin)
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
    assert rc == 0 and time.monotonic() - start < 20


# ---- suppression markers and scanner-config files (built from parts so this file holds no live marker) ----
H = "#" + " "
MARKERS = {
    "suppress-nosec": "x = f(1)  " + H + "nos" + "ec B310",
    "suppress-semgrep-ignore": "x = f(1)  " + H + "nosem" + "grep: some.rule",
    "suppress-gitleaks-allow": "x = 'abc'  " + H + "gitleaks:" + "allow",
    "suppress-trivy-ignore": H + "trivy:" + "ignore:AVD-DS-0002",
    "suppress-noqa-security": "x = f(1)  " + H + "no" + "qa: S603",
}
MORE_MARKERS = {
    "suppress-nosec": ["x = f(1)  //nos" + "ec", "x = 1 -- nos" + "ec"],
    "suppress-semgrep-ignore": ["x = 1  " + H + "nosem", "x = 1  " + H + "nosem: some.rule"],
    "suppress-noqa-security": [
        "x = 1  " + H + "ruff: no" + "qa",
        "x = 1  " + H + "ruff: no" + "qa: S101",
        "x = 1  " + H + "ruff:no" + "qa: F401",
        "x = 1  " + H + "flake8: no" + "qa",
        "x = 1  " + H + "no" + "qa",
        "x = 1  " + H + "no" + "qa: BLE001, S112",
        "x = 1  " + H + "no" + "qa:S603 reason",
        "x = 1  #no" + "qa : S101",
    ],
}
NOT_MARKERS = [
    "the word nos" + "ec in prose",
    "we do not use the semgrep marker here",
    "x = 1  " + H + "no" + "qa: BLE001",
    "x = 1  " + H + "no" + "qa: F401, E501",
    "x = 1  " + H + "noqafoo",
    "x = 'S603'  " + H + "plain comment",
    "we mention ruff: no" + "qa and nosem in prose",
    "x = 1  " + H + "nosemantic note",
]


def _val(*texts):
    """The list value of a marker rule: count@sha256 of the sorted line texts (written out here, apart from the script)."""
    digest = hashlib.sha256("\n".join(sorted(texts)).encode()).hexdigest()
    return f"{len(texts)}@{digest}"


ONE = "1@" + "0" * 64  # well-formed value for list-format tests


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _supp_line(path, rule, value, reason="reviewed for the test"):
    return f"{path}:{rule}:{value}:{reason}\n"


@pytest.mark.parametrize("rule", MARKERS)
def test_each_suppression_marker_hits_unlisted_and_prints_no_text(tmp_path, rule):
    rc, out = _scan(_repo(tmp_path, {"a/x.py": "ok\n" + MARKERS[rule] + "\n"}))
    assert rc == 1 and out.strip() == f"a/x.py:2: {rule}"


@pytest.mark.parametrize(("rule", "line"), [(r, m) for r, ms in MORE_MARKERS.items() for m in ms])
def test_other_shapes_of_a_suppression_marker_hit(tmp_path, rule, line):
    rc, out = _scan(_repo(tmp_path, {"a.py": line + "\n"}))
    assert rc == 1 and f"a.py:1: {rule}" in out


@pytest.mark.parametrize("line", NOT_MARKERS)
def test_prose_and_style_codes_are_not_suppression_hits(tmp_path, line):
    assert _scan(_repo(tmp_path, {"a.py": line + "\n"}))[0] == 0


@pytest.mark.parametrize("rule", MARKERS)
def test_a_listed_marker_with_the_exact_count_passes(tmp_path, rule):
    repo = _repo(tmp_path, {"a.py": MARKERS[rule] + "\nx = 2\n" + MARKERS[rule] + "\n"})
    assert _scan(repo, suppress=_supp_line("a.py", rule, _val(*[MARKERS[rule]] * 2))) == (0, "\n")


@pytest.mark.parametrize("rule", MARKERS)
@pytest.mark.parametrize("listed", [1, 3])
def test_a_count_that_differs_from_the_list_fails_both_ways(tmp_path, rule, listed):
    repo = _repo(tmp_path, {"a.py": MARKERS[rule] + "\n" + MARKERS[rule] + "\n"})
    rc, out = _scan(repo, suppress=_supp_line("a.py", rule, _val(*[MARKERS[rule]] * listed)))
    assert rc == 1 and "suppression-list count is 2" in out


def test_a_list_entry_covers_only_its_own_file_and_rule(tmp_path):
    files = {"a.py": MARKERS["suppress-nosec"], "b.py": MARKERS["suppress-nosec"]}
    one = _supp_line("a.py", "suppress-nosec", _val(MARKERS["suppress-nosec"]))
    rc, out = _scan(_repo(tmp_path, files), suppress=one)
    assert rc == 1 and "b.py:1: suppress-nosec" in out and "a.py" not in out
    both = MARKERS["suppress-nosec"] + "\n" + MARKERS["suppress-noqa-security"]
    rc, out = _scan(_repo(tmp_path / "r2", {"a.py": both}), suppress=one)
    assert rc == 1 and "a.py:2: suppress-noqa-security" in out


def test_a_file_the_allowlist_skips_is_still_checked_for_markers(tmp_path):
    repo = _repo(tmp_path, {"a.py": MARKERS["suppress-nosec"]})
    rc, out = _scan(repo, allow="a.py:banned-name:fixture names a banned word\n")
    assert rc == 1 and "a.py:1: suppress-nosec" in out


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        (
            "gone.py:suppress-nosec:" + ONE + ":reason\n",
            "stale entry, gone.py suppress-nosec not tracked",
        ),
        (
            "a.py:suppress-nosec:" + ONE + ":reason\n",
            "stale entry, a.py suppress-nosec has no such marker",
        ),
        ("a.py:suppress-nosec:" + ONE + ":\n", "malformed"),
        ("a.py:suppress-nosec:" + ONE + "\n", "malformed"),
        ("a.py:suppress-everything:" + ONE + ":reason\n", "unknown rule"),
        ("a.py:suppress-nosec:many:reason\n", "positive count"),
        ("a.py:suppress-nosec:0:reason\n", "positive count"),
        ("a.py:suppress-nosec:1:reason\n", "count@sha256"),
        ("a.py:scanner-config-file:abc:reason\n", "sha256"),
        (
            "a.py:suppress-nosec:"
            + ONE
            + ":a reason one\na.py:suppress-nosec:"
            + ONE
            + ":again now\n",
            "duplicate",
        ),
    ],
)
def test_a_bad_list_line_is_itself_a_hit(tmp_path, entry, message):
    repo = _repo(tmp_path, {"a.py": "x = 1\n"})
    rc, out = _scan(repo, suppress=entry)
    assert rc == 1 and message in out


@pytest.mark.parametrize(
    "name",
    [
        ".gitleaksignore",
        ".gitleaks.toml",
        ".semgrepignore",
        ".trivyignore",
        "sub/dir/.trivyignore",
        "zizmor.yml",
        "ruff.toml",
        ".ruff.toml",
        "trivy-secret.yaml",
        "bandit.yaml",
        "bandit.yml",
        "setup.cfg",
        "sub/tox.ini",
        "zizmor.yaml",
        ".checkov.yml",
        ".checkov.yaml",
        ".hadolint.yaml",
        "a/.hadolint.yml",
        ".gitattributes",
        "sub/.gitattributes",
        ".github/codeql-config.yml",
        ".github/zizmor.yaml",
        "docs/My-CodeQL-notes.md",
        ".tfsec/config.yml",
        ".checkov/x.yml",
    ],
)
def test_a_scanner_config_file_hits_unless_listed_with_its_hash(tmp_path, name):
    content = "anything\n"
    repo = _repo(tmp_path, {name: content})
    rc, out = _scan(repo)
    assert rc == 1 and f"{name}:1: scanner-config-file" in out
    sha = hashlib.sha256(content.encode()).hexdigest()
    assert _scan(repo, suppress=_supp_line(name, "scanner-config-file", sha)) == (0, "\n")
    rc, out = _scan(repo, suppress=_supp_line(name, "scanner-config-file", "0" * 64))
    assert rc == 1 and "hash differs" in out


def test_changing_a_listed_scanner_config_file_fails_until_the_list_changes(tmp_path):
    repo = _repo(tmp_path, {".gitleaksignore": "one\n"})
    sha = hashlib.sha256(b"one\n").hexdigest()
    supp = _supp_line(".gitleaksignore", "scanner-config-file", sha)
    assert _scan(repo, suppress=supp)[0] == 0
    (repo / ".gitleaksignore").write_text("one\ntwo\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)  # noqa: S603, S607
    assert _scan(repo, suppress=supp)[0] == 1


def test_the_real_repo_passes_with_its_own_list():
    cmd = [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    assert r.returncode == 0, r.stdout[-2000:]


def test_the_real_list_has_no_generic_baseline_reason_and_names_the_code_owners_limit():
    text = REAL_LIST.read_text()
    assert "CODEOWNERS" in text and "NOT done here" in text
    assert "not individually reviewed" not in text.lower()
    assert "carries its own inline reason" not in text.lower()


# ---- round 1 fixes (A24 PR91): marker text pin, NUL files, broader markers, glob allowlist, pinned list files ----
NOSEC = MARKERS["suppress-nosec"]
NOQA = MARKERS["suppress-noqa-security"]


def test_a_marker_widened_on_the_same_line_fails_even_with_the_same_count(tmp_path):
    repo = _repo(tmp_path, {"a.py": NOQA + "\n"})
    supp = _supp_line("a.py", "suppress-noqa-security", _val(NOQA))
    assert _scan(repo, suppress=supp) == (0, "\n")
    wide = _repo(tmp_path / "w", {"a.py": NOQA + ", S101\n"})
    rc, out = _scan(wide, suppress=supp)
    assert rc == 1 and "text hash differs" in out


def test_one_marker_replaced_by_a_different_one_in_the_same_file_fails(tmp_path):
    other = "y = g(2)  " + H + "no" + "qa: S607"
    supp = _supp_line("a.py", "suppress-noqa-security", _val(NOQA, NOQA))
    assert _scan(_repo(tmp_path, {"a.py": NOQA + "\n" + NOQA + "\n"}), suppress=supp)[0] == 0
    rc, out = _scan(_repo(tmp_path / "r", {"a.py": NOQA + "\n" + other + "\n"}), suppress=supp)
    assert rc == 1 and "text hash differs" in out


def test_a_marker_moved_to_another_line_with_identical_text_still_passes(tmp_path):
    """Documented: the pin is the set of marker line texts, not their positions; identical text on another line is the same marker."""
    supp = _supp_line("a.py", "suppress-noqa-security", _val(NOQA))
    assert _scan(_repo(tmp_path, {"a.py": NOQA + "\nx = 1\n"}), suppress=supp)[0] == 0
    assert _scan(_repo(tmp_path / "m", {"a.py": "x = 1\n\n" + NOQA + "\n"}), suppress=supp)[0] == 0


@pytest.mark.parametrize("name", [".trivyignore", ".semgrepignore", ".gitleaksignore", "a/.bandit"])
def test_a_scanner_config_with_a_nul_byte_still_hits(tmp_path, name):
    repo = _repo(tmp_path, {name: b"line\0line\n"})
    rc, out = _scan(repo)
    assert rc == 1 and f"{name}:1: scanner-config-file" in out
    sha = hashlib.sha256(b"line\0line\n").hexdigest()
    rc, out = _scan(repo, suppress=_supp_line(name, "scanner-config-file", sha))
    assert (
        rc == 1 and f"{name}:1: nul-in-text-file" in out
    )  # pinned, but a NUL in a config is never accepted (fail closed)
    assert "scanner-config-file" not in out
    rc, out = _scan(repo, suppress=_supp_line(name, "scanner-config-file", "1" * 64))
    assert rc == 1 and "hash differs" in out


@pytest.mark.parametrize("name", ["a.py", "ci.yml", "x.sh"])
def test_a_source_file_with_a_nul_byte_is_refused_not_skipped(tmp_path, name):
    rc, out = _scan(_repo(tmp_path, {name: b"x = 1\0\n"}))
    assert rc == 1 and f"{name}:1: nul-in-text-file" in out


def test_a_marker_in_a_nul_file_is_not_hidden(tmp_path):
    rc, out = _scan(_repo(tmp_path, {"a.py": b"\0\n" + NOSEC.encode() + b"\n"}))
    assert rc == 1 and "a.py:2: suppress-nosec" in out


def test_an_allowlist_path_that_is_a_glob_is_refused(tmp_path):
    repo = _repo(tmp_path, {"a.txt": CASES["llm-id-sk"]})
    for glob in ("*", "*.txt", "a.t?t", "[a].txt"):
        rc, out = _scan(repo, allow=f"{glob}:*:disable everything\n")
        assert rc == 1 and "no glob" in out and "a.txt:1: llm-id-sk" in out


@pytest.mark.parametrize("path", ["tools/scan_allowlist.txt", "tools/scan_banned_extra.txt"])
def test_the_scan_list_files_are_pinned_like_a_scanner_config(tmp_path, path):
    repo = _repo(tmp_path, {path: "one\n"})
    rc, out = _scan(repo)
    assert rc == 1 and f"{path}:1: scanner-config-file" in out
    assert _scan(repo, suppress=_supp_line(path, "scanner-config-file", _sha("one\n")))[0] == 0
    (repo / path).write_text("one\ntwo\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)  # noqa: S603, S607
    rc, out = _scan(repo, suppress=_supp_line(path, "scanner-config-file", _sha("one\n")))
    assert rc == 1 and "hash differs" in out


def test_print_list_writes_a_list_the_scan_accepts_and_keeps_reasons(tmp_path):
    repo = _repo(tmp_path, {"a.py": NOSEC + "\n" + NOQA + "\n", ".trivyignore": "x\n"})
    old = _supp_line("a.py", "suppress-nosec", ONE, "a kept reason that is long enough")
    work = tmp_path.parent / (tmp_path.name + "-lists")
    work.mkdir(exist_ok=True)
    (work / "old.txt").write_text("# header\n" + old)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--root",
        str(repo),
        "--suppressions",
        str(work / "old.txt"),
    ]
    r = subprocess.run([*cmd, "--print-list"], capture_output=True, text=True, check=False)  # noqa: S603
    assert r.returncode == 0 and r.stdout.startswith("# header\n")
    assert (
        ":a kept reason that is long enough" in r.stdout
        and "NEW, needs a reviewed reason" in r.stdout
    )
    # the placeholder is refused by the scan until a reviewer writes a real reason (round 2, M6)
    rc, out = _scan(repo, suppress=r.stdout)
    assert rc == 1 and "placeholder" in out
    reviewed = r.stdout.replace("NEW, needs a reviewed reason", "reviewed by hand for this test")
    assert _scan(repo, suppress=reviewed) == (0, "\n")


REAL_LIST = REPO_ROOT / "tools" / "scan_suppressions.txt"


def test_a_weakened_copy_of_the_real_list_fails_the_scan(tmp_path):
    """The guard is only as strong as the list it reads: remove an entry, or change a count or a hash, and the real repo fails."""
    root = REPO_ROOT
    lines = REAL_LIST.read_text().splitlines(keepends=True)
    entries = [i for i, ln in enumerate(lines) if ln.strip() and not ln.startswith("#")]
    marker_entry = next(i for i in entries if "@" in lines[i])
    variants = {
        "entry removed": [ln for i, ln in enumerate(lines) if i != marker_entry],
        "hash changed": [_flip(ln) if i == marker_entry else ln for i, ln in enumerate(lines)],
    }
    for name, new in variants.items():
        f = tmp_path / (name.replace(" ", "_") + ".txt")
        f.write_text("".join(new))
        cmd = [sys.executable, str(SCRIPT), "--root", str(root), "--suppressions", str(f)]
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
        assert r.returncode == 1, name


def _flip(line):
    head, sep, rest = line.partition("@")
    return head + sep + ("1" if rest[0] != "1" else "2") + rest[1:]


# ---- round 2 fixes (A24 PR91): case, more markers, nested configs, NUL fail closed, reasons ----
def _p(*parts):
    return "".join(parts)


CASE_HITS = {  # upper and mixed case of each original rule
    "suppress-nosec": [H + "NO" + "SEC", H + "No" + "Sec B310", "x = 1  //NO" + "SEC"],
    "suppress-semgrep-ignore": [H + "NO" + "SEMGREP", "x  " + H + "No" + "Sem", "NO" + "SEMGREP"],
    "suppress-gitleaks-allow": ["x = 'a'  " + H + "GITLEAKS:" + "ALLOW", "Gitleaks:" + "Allow"],
    "suppress-trivy-ignore": [H + "TRIVY:" + "IGNORE:X", H + "Trivy:" + "Ignore"],
    "suppress-noqa-security": [
        "x = 1  " + H + "NO" + "QA",
        "x = 1  " + H + "No" + "Qa: S101",
        "x = 1  " + H + "no" + "qa: s101",
        "x = 1  " + H + "NO" + "QA: s603",
        "x = 1  " + H + "RUFF: NO" + "QA",
    ],
}
NEW_HITS = {  # one rule per tool added in round 2, several shapes each
    "suppress-nosec": [H + "nos" + "ec:B101", "x  #nos" + "ec-B101", "x  " + H + "nos" + "ecurity"],
    "suppress-semgrep-ignore": [
        "we do not use nosem" + "grep here",
        "x = 1  " + H + "nosem" + "grep:r",
    ],
    "suppress-ruff-range": [
        H + "ruff: dis" + "able[S101]",
        H + "ruff: ig" + "nore[S101]",
        H + "ruff: en" + "able[S101]",
        "x = 1  //ruff:en" + "able",
        H + "RUFF: DIS" + "ABLE[S101]",
    ],
    "suppress-nosonar": [
        H + "NO" + "SONAR",
        "x = 1  // NO" + "SONAR S8707: why",
        "x  " + H + "no" + "sonar",
    ],
    "suppress-lgtm": ["x = 1  " + H + "lg" + "tm[py/path-injection]", "// LG" + "TM [js/x]"],
    "suppress-codeql": ["// code" + "ql[js/x]", "x  " + H + "Code" + "QL[py/y]"],
    "suppress-zizmor-ignore": [
        H + "zizmor: ig" + "nore[template-injection]",
        H + "zizmor:ig" + "nore[x]",
    ],
    "suppress-allowlist-secret": [
        H + "pragma: allow" + "list secret",
        H + "pragma: allowlist next" + "line secret",
        H + "pragma: white" + "list secret",
    ],
    "suppress-nopmd": ["x = 1  // NO" + "PMD", "x  " + H + "no" + "pmd reason"],
    "suppress-checkov-skip": [H + "checkov:" + "skip=CKV_AWS_1: why", "x  //checkov:" + "skip=A"],
    "suppress-tfsec-ignore": [H + "tfsec:" + "ignore:aws-s3-x", "x  #tfsec:" + "ignore:y"],
}
NEW_MISSES = [  # prose that names a tool, or its ordinary comments, is not a suppression
    "the NO" + "SONAR marker in prose",
    "NO" + "PMD in prose",
    "x = 1  " + H + "codeql runs in CI",
    "x = 1  " + H + "zizmor runs offline",
    "x = 1  " + H + "pragma: no cover",
    "x = 1  " + H + "checkov runs in CI",
    "x = 1  " + H + "tfsec is used here",
    "x = 1  " + H + "ruff is the linter",
    "x = 1  " + H + "ruff format notes",
    "x = 1  " + H + "no" + "qa: BLE001",
    "x = 1  " + H + "NO" + "QA: ble001",
    "x = 1  " + H + "nosemantic note",
]


@pytest.mark.parametrize(
    ("rule", "line"), [(r, m) for r, ms in {**CASE_HITS, **NEW_HITS}.items() for m in ms]
)
def test_case_and_round_two_marker_shapes_hit(tmp_path, rule, line):
    rc, out = _scan(_repo(tmp_path, {"a.py": line + "\n"}))
    assert rc == 1 and f"a.py:1: {rule}" in out


@pytest.mark.parametrize("line", NEW_MISSES)
def test_round_two_prose_is_not_a_hit(tmp_path, line):
    assert _scan(_repo(tmp_path, {"a.py": line + "\n"})) == (0, "\n")


@pytest.mark.parametrize("rule", list(NEW_HITS))
def test_each_round_two_rule_can_be_listed_with_its_text_hash(tmp_path, rule):
    line = NEW_HITS[rule][0]
    repo = _repo(tmp_path, {"a.py": line + "\n"})
    assert _scan(repo, suppress=_supp_line("a.py", rule, _val(line))) == (0, "\n")


@pytest.mark.parametrize(
    "name",
    [
        ".flake8",
        "sub/mypy.ini",
        "sonar-project.properties",
        ".sonarcloud.properties",
        ".github/codeql/codeql-config.yml",
        ".github/codeql/queries/x.ql",
        ".coderabbit.yaml",
        ".semgrep.yml",
        ".semgrep/rules/a.yml",
        "trivy.yml",
        ".pre-commit-config.yaml",
        ".secrets.baseline",
        ".snyk",
        "a/.FLAKE8",
        "Setup.CFG",
    ],
)
def test_more_scanner_config_names_are_pinned(tmp_path, name):
    repo = _repo(tmp_path, {name: "anything\n"})
    rc, out = _scan(repo)
    assert rc == 1 and f"{name}:1: scanner-config-file" in out
    assert _scan(repo, suppress=_supp_line(name, "scanner-config-file", _sha("anything\n"))) == (
        0,
        "\n",
    )


NESTED = '[project]\nname = "x"\n'
NESTED_BAD = {
    "ruff": NESTED + '[tool.ruff.lint]\nignore = ["S"]\n',
    "ruff top": NESTED + "[tool.ruff]\nline-length = 100\n",
    "bandit": NESTED + '[tool.bandit]\nskips = ["B101"]\n',
    "semgrep": NESTED + "[tool.semgrep]\nx = 1\n",
    "spaced": NESTED + "  [tool.ruff]\n",
}


def test_a_nested_pyproject_is_a_pinned_scanner_config(tmp_path):
    repo = _repo(tmp_path, {"demos/x/pyproject.toml": NESTED})
    rc, out = _scan(repo)
    assert rc == 1 and "demos/x/pyproject.toml:1: scanner-config-file" in out
    pin = _supp_line("demos/x/pyproject.toml", "scanner-config-file", _sha(NESTED))
    assert _scan(repo, suppress=pin) == (0, "\n")
    rc, out = _scan(
        repo, suppress=_supp_line("demos/x/pyproject.toml", "scanner-config-file", "0" * 64)
    )
    assert rc == 1 and "hash differs" in out


def test_the_root_pyproject_is_not_a_scanner_config_here(tmp_path):
    """The root one is pinned key by key in tests/test_ci_gitleaks_scope.py, so this scan leaves it alone."""
    assert _scan(_repo(tmp_path, {"pyproject.toml": NESTED_BAD["ruff"]})) == (0, "\n")


@pytest.mark.parametrize("kind", list(NESTED_BAD))
def test_a_nested_pyproject_with_a_scanner_table_fails_even_when_pinned(tmp_path, kind):
    text = NESTED_BAD[kind]
    repo = _repo(tmp_path, {"demos/x/pyproject.toml": text})
    pin = _supp_line("demos/x/pyproject.toml", "scanner-config-file", _sha(text))
    rc, out = _scan(repo, suppress=pin)
    assert rc == 1 and "demos/x/pyproject.toml:1: nested-pyproject-scanner-table" in out
    assert "scanner-config-file" not in out  # pinned, so only the table is reported


@pytest.mark.parametrize(
    "name", ["x.env", "Dockerfile", "x.html", "Makefile", "a.conf", "x.pyi", "c.go"]
)
def test_a_nul_byte_hides_nothing_from_the_scan_in_any_text_like_file(tmp_path, name):
    for body in (
        b"\0\n" + EXAMPLE_KEY.encode() + b"\n",
        b"ok\n" * 3000 + b"\0\n",
    ):  # early NUL, NUL past 8000 bytes
        rc, out = _scan(_repo(tmp_path / str(len(body)), {name: body}))
        assert rc == 1 and f"{name}:1: nul-in-text-file" in out


@pytest.mark.parametrize("name", ["x.env", "Dockerfile", "x.html"])
def test_a_real_key_behind_a_nul_byte_is_found_too(tmp_path, name):
    key = ("AKIA" + "ABCDEFGHIJKLMNOP").encode()
    rc, out = _scan(_repo(tmp_path, {name: b"\0\nx = " + key + b"\n"}))
    assert rc == 1 and f"{name}:2: cloud-id-prefix" in out and "nul-in-text-file" in out


@pytest.mark.parametrize(
    "name", ["a.png", "b.JPG", "c.pdf", "d.zip", "e.woff2", "f.whl", "g.parquet", "h.db", "i.bin"]
)
def test_a_nul_byte_in_a_known_binary_format_is_allowed_when_nothing_secret_is_in_it(
    tmp_path, name
):
    body = (
        b"\x89\0\0" + bytes(range(256)) + b"\0" + EXAMPLE_KEY.encode()
    )  # the placeholder key is fine
    assert _scan(_repo(tmp_path, {name: body})) == (0, "\n")


@pytest.mark.parametrize(
    "reason",
    [
        "NEW, needs a reviewed reason",
        "NEW",
        "NEW: fill in later please",
        "too short",
        "x" * 14,
        "a b c d e f g",
        "x" * 15,
        "x" * 200,
        "same same same same",
        "abc abc abc abc abc",
        "baseline of 2742c1b; the marker carries its own inline reason; not individually reviewed",
        "Not   Individually\tReviewed by anyone at all",
        "the marker carries its own inline reason",
        "taken as part of the baseline of 2742c1b",
    ],
)
def test_a_placeholder_or_short_reason_is_refused(tmp_path, reason):
    repo = _repo(tmp_path, {"a.py": NOSEC + "\n"})
    rc, out = _scan(repo, suppress=_supp_line("a.py", "suppress-nosec", _val(NOSEC), reason))
    assert rc == 1 and "suppression-list reason" in out


@pytest.mark.parametrize(
    "reason", ["NEWS desk fixture, reviewed in PR", "newly added test helper", "S603 on fixed argv"]
)
def test_a_real_reason_is_accepted(tmp_path, reason):
    repo = _repo(tmp_path, {"a.py": NOSEC + "\n"})
    assert _scan(repo, suppress=_supp_line("a.py", "suppress-nosec", _val(NOSEC), reason)) == (
        0,
        "\n",
    )


def test_print_list_output_is_never_accepted_before_review(tmp_path):
    repo = _repo(tmp_path, {"a.py": NOSEC + "\n", ".trivyignore": "x\n"})
    r = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(repo),
            "--print-list",
            "--suppressions",
            str(tmp_path / "none.txt"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0 and r.stdout.count("NEW, needs a reviewed reason") == 2
    rc, out = _scan(repo, suppress=r.stdout)
    assert rc == 1 and out.count("placeholder") == 2


@pytest.mark.parametrize(
    "line",
    [
        H + "ruff: no" + "qa",
        H + "flake8: no" + "qa",
        "//ruff:no" + "qa",
        H + "ruff: no" + "qa  # why",
        H + "ruff: no" + "qa: " + "why",
    ],
)
def test_a_file_level_noqa_without_codes_cannot_be_listed(tmp_path, line):
    repo = _repo(tmp_path, {"a.py": line + "\n"})
    rule = "suppress-noqa-security"
    rc, out = _scan(repo, suppress=_supp_line("a.py", rule, _val(line)))
    assert rc == 1 and "a.py:1: file-noqa-without-codes" in out


@pytest.mark.parametrize(
    "line",
    [
        H + "ruff: no" + "qa: S608",
        H + "ruff: no" + "qa: S608, ISC004  # why",
        H + "flake8: no" + "qa: E501",
    ],
)
def test_a_file_level_noqa_that_names_codes_can_be_listed(tmp_path, line):
    repo = _repo(tmp_path, {"a.py": line + "\n"})
    supp = _supp_line(
        "a.py", "suppress-noqa-security", _val(line), "file-level, codes named, reviewed"
    )
    assert _scan(repo, suppress=supp) == (0, "\n")


def test_the_real_repo_has_no_file_level_noqa_without_codes():
    out = subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert "file-noqa-without-codes" not in out


# ---- round 3 fixes (A24 PR91, fix batch 3) ----
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
GH_KEY = "gh" + "p_" + "c" * 36
SK_KEY = "sk-" + "b" * 40


# M3 (r3): a NUL byte after a known-binary extension used to hide the whole file from the secret rules
BINARY_NAMES = [
    "x.png", "x.jpg", "x.gif", "x.ico", "x.pdf", "x.zip", "x.gz", "x.tar", "x.whl", "x.jar",
    "x.woff2", "x.ttf", "x.parquet", "x.db", "x.sqlite", "x.pyc", "x.so", "x.exe", "x.wasm",
    "x.npy", "x.bin", "x.PNG", "dir/x.Bin",
]  # fmt: skip


@pytest.mark.parametrize("name", BINARY_NAMES)
@pytest.mark.parametrize(
    ("rule", "secret"),
    [
        ("cloud-id-prefix", AWS_KEY),
        ("llm-id-sk", SK_KEY),
        ("vcs-id-classic", GH_KEY),
        ("pem-block-header", "-----BEGIN " + "RSA PRIVATE" + " KEY-----"),
    ],
)
def test_a_secret_behind_a_nul_byte_in_a_known_binary_format_is_found(tmp_path, name, rule, secret):
    body = b"\x89PNG\0\0\n" + secret.encode() + b"\n\0\xff"
    rc, out = _scan(_repo(tmp_path, {name: body}))
    assert rc == 1 and f"{name}:2: {rule}" in out
    assert (
        "nul-in-text-file" not in out
    )  # a known binary format is not refused for its NUL, only read


def test_a_secret_in_a_binary_file_with_high_bytes_around_it_is_found(tmp_path):
    body = bytes(range(128, 256)) + b"\0" + AWS_KEY.encode() + bytes(range(128, 200))
    rc, out = _scan(_repo(tmp_path, {"a.bin": body}))
    assert (
        rc == 1 and "a.bin:" in out and "cloud-id-prefix" in out
    )  # line numbers of a binary file mean little


def test_the_allowlist_can_skip_one_rule_on_one_binary_file(tmp_path):
    files = {"a.bin": b"\0" + AWS_KEY.encode(), "b.bin": b"\0" + AWS_KEY.encode()}
    rc, out = _scan(
        _repo(tmp_path, files), allow="a.bin:cloud-id-prefix:a made-up key in a test blob\n"
    )
    assert rc == 1 and "b.bin:1: cloud-id-prefix" in out and "a.bin" not in out


# N5 (r3): a text-like file that really holds NUL (xlsx, pkl, onnx, h5) can be listed per path, with a reason
@pytest.mark.parametrize("name", ["x.xlsx", "model.onnx", "d.h5", "x.pkl"])
def test_nul_in_a_text_like_file_can_be_allowed_per_path_with_a_reason(tmp_path, name):
    files = {name: b"PK\0\0data\n", "other.dat": b"PK\0\0data\n"}
    repo = _repo(tmp_path, files)
    allow = f"{name}:nul-in-text-file:a binary format that is not on the known list\n"
    rc, out = _scan(repo, allow=allow)
    assert rc == 1 and "other.dat:1: nul-in-text-file" in out and f"{name}:" not in out
    key = AWS_KEY.encode()
    rc, out = _scan(_repo(tmp_path / "k", {name: b"\0" + key + b"\n"}), allow=allow)
    assert rc == 1 and f"{name}:1: cloud-id-prefix" in out and "nul-in-text-file" not in out


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("a.txt:*:disable every rule on this file\n", "unknown rule"),
        ("a.txt:no-such-rule:a reason with enough words\n", "unknown rule"),
        ("a.txt:Llm-Id-Sk:a reason with enough words\n", "unknown rule"),
        ("a.txt:llm-id-sk:ok\n", "shorter than"),
        ("a.txt:llm-id-sk:words words words other\n", "fewer than"),
        ("a.txt:llm-id-sk:" + "x" * 30 + "\n", "fewer than"),
        ("a.txt:llm-id-sk:baseline of 2742c1b, not individually reviewed\n", "generic baseline"),
        ("a.txt:llm-id-sk:NEW, needs a reviewed reason\n", "placeholder"),
    ],
)
def test_an_allowlist_line_with_a_bad_rule_or_reason_is_refused_and_skips_nothing(
    tmp_path, entry, message
):
    repo = _repo(tmp_path, {"a.txt": CASES["llm-id-sk"] + "\n"})
    rc, out = _scan(repo, allow=entry)
    assert rc == 1 and message in out and "a.txt:1: llm-id-sk" in out


# M2 (r3): the nested-pyproject rule read lines with a regex; the file is parsed as TOML now, so every spelling counts
NESTED_SPELLINGS = {
    "spaces in brackets": "[ tool.ruff ]\nline-length = 1\n",
    "spaces around the dot": '[tool . ruff.lint]\nignore = ["S"]\n',
    "quoted key": '[tool."ruff"]\nline-length = 1\n',
    "quoted table name": '["tool".ruff]\nline-length = 1\n',
    "literal quoted": "[tool.'bandit']\nskips = ['B101']\n",
    "tool table plus key": "[tool]\nruff = { line-length = 1 }\n",
    "dotted top-level key": 'tool.ruff.lint.ignore = ["S"]\n',
    "inline table": "tool = { ruff = { line-length = 1 } }\n",
    "dotted semgrep": "tool.semgrep.rules = 1\n",
    "upper case": "[tool.RUFF]\nline-length = 1\n",
    "after other tables": '[project]\nname = "x"\n\n[tool.other]\na = 1\n\n[ tool . bandit ]\nskips = []\n',
    "array of tables": "[[tool.ruff.x]]\na = 1\n",
    "comment after": "[tool.ruff]  # why not\n",
}


@pytest.mark.parametrize("kind", list(NESTED_SPELLINGS))
def test_every_toml_spelling_of_a_scanner_table_in_a_nested_pyproject_is_refused(tmp_path, kind):
    import tomllib

    text = NESTED_SPELLINGS[kind]
    assert "tool" in tomllib.loads(
        text
    )  # the spelling really is valid TOML (so a regex miss would be a bypass)
    path = "demos/x/pyproject.toml"
    repo = _repo(tmp_path, {path: text})
    rc, out = _scan(repo, suppress=_supp_line(path, "scanner-config-file", _sha(text)))
    assert rc == 1 and f"{path}:1: nested-pyproject-scanner-table" in out


@pytest.mark.parametrize(
    "text",
    ["[tool.ruff\n", "x = \n", "a = 1\na = 2\n", '[tool]\n"ruff" = [\n', "\x00 = 1\n"],
)
def test_a_nested_pyproject_that_does_not_parse_is_refused(tmp_path, text):
    path = "a/b/pyproject.toml"
    rc, out = _scan(
        _repo(tmp_path, {path: text}), suppress=_supp_line(path, "scanner-config-file", _sha(text))
    )
    assert rc == 1 and (
        f"{path}:1: nested-pyproject-unparsable" in out or f"{path}:1: nul-in-text-file" in out
    )


@pytest.mark.parametrize(
    "text",
    [
        '[project]\nname = "x"\n',
        "[tool.pytest.ini_options]\naddopts = '-q'\n",
        "[tool.hatch.build]\nx = 1\n",
        "ruff = 1\n[tool]\nother = 2\n",
        '[project]\nname = "ruff-bandit-semgrep"\n',
    ],
)
def test_a_nested_pyproject_without_a_scanner_key_only_needs_its_pin(tmp_path, text):
    path = "demos/x/pyproject.toml"
    repo = _repo(tmp_path, {path: text})
    assert _scan(repo, suppress=_supp_line(path, "scanner-config-file", _sha(text))) == (0, "\n")


# M1 (r3): a config-named path that is not a regular file (ruff reads ruff.toml even if it is a link to /dev/null)
@pytest.mark.parametrize(
    "name",
    [
        "ruff.toml",
        ".ruff.toml",
        "sub/.gitleaksignore",
        "demos/x/pyproject.toml",
        ".gitleaks.toml",
        "setup.cfg",
    ],
)
def test_a_tracked_symlink_with_a_config_name_is_a_hit_even_if_listed(tmp_path, name):
    repo = _repo(tmp_path, {"real.txt": "x = 1\n"}, {name: "/dev/null"})
    pin = _supp_line(name, "scanner-config-file", _sha(""))
    for supp in ("", pin):
        rc, out = _scan(repo, suppress=supp)
        assert rc == 1 and f"{name}:1: scanner-config-not-a-file" in out


def test_a_symlink_to_a_file_inside_the_repo_with_a_config_name_is_still_a_hit(tmp_path):
    repo = _repo(tmp_path, {"cfg/real.toml": "x = 1\n"}, {"ruff.toml": "cfg/real.toml"})
    rc, out = _scan(repo)
    assert rc == 1 and "ruff.toml:1: scanner-config-not-a-file" in out


def test_a_symlink_named_like_a_config_folder_is_a_hit(tmp_path):
    repo = _repo(tmp_path, {"real/x.yml": "a: 1\n"}, {".semgrep": "real"})
    rc, out = _scan(repo)
    assert rc == 1 and ".semgrep:1: scanner-config-not-a-file" in out


def test_a_tracked_config_file_removed_from_the_work_tree_is_a_hit(tmp_path):
    repo = _repo(tmp_path, {"ruff.toml": "x = 1\n"})
    (repo / "ruff.toml").unlink()
    rc, out = _scan(repo)
    assert rc == 1 and "ruff.toml:1: scanner-config-not-a-file" in out


def test_a_symlink_with_an_ordinary_name_is_scanned_as_the_text_git_stores(tmp_path):
    """Git stores a link as its target text; the file it points to is its own tracked path (or not repository content)."""
    repo = _repo(tmp_path, {"real.txt": CASES["llm-id-sk"]}, {"alias.txt": "real.txt"})
    rc, out = _scan(repo)
    assert (
        rc == 1 and out.strip() == "real.txt:1: llm-id-sk"
    )  # the alias is clean, its target is reported once
    assert _scan(_repo(tmp_path / "ok", {"real.txt": "x = 1\n"}, {"alias.txt": "real.txt"}))[0] == 0
    leaky = _repo(tmp_path / "leaky", {"a.py": "x = 1\n"}, {"alias.txt": AWS_KEY})
    rc, out = _scan(leaky)
    assert rc == 1 and "alias.txt:1: cloud-id-prefix" in out


def test_a_dangling_symlink_with_an_ordinary_name_is_not_a_hit(tmp_path):
    repo = _repo(tmp_path, {"a.py": "x = 1\n"}, {"gone.txt": "nowhere"})
    assert _scan(repo) == (0, "\n")


def test_print_list_never_writes_a_line_for_a_config_named_link(tmp_path):
    repo = _repo(tmp_path, {"a.py": "x = 1\n"}, {"ruff.toml": "/dev/null"})
    rc, out = _scan(repo, args=["--print-list"])
    assert rc == 0 and "ruff.toml" not in out


# M4 (r3): `\b` saw no boundary after `_` or after the letter of an escape
LEAD_HITS = {
    "cloud-id-prefix": [
        '"a\\n' + AWS_KEY + '"',
        "id_" + AWS_KEY,
        "x\\t" + AWS_KEY,
        "x\\x0a" + AWS_KEY,
        "x\\u000a" + AWS_KEY,
        "-" + AWS_KEY,
        "'" + AWS_KEY + "_",
        "k=" + AWS_KEY + "_suffix",
        '"a\\n' + "ASIA" + "ABCDEFGHIJKLMNOP",
    ],
    "llm-id-sk": ["api_" + SK_KEY, '"a\\n' + SK_KEY, "x\\r" + SK_KEY],
    "vcs-id-classic": ["KEY_" + GH_KEY, '"a\\n' + GH_KEY, "_" + GH_KEY],
    "chat-id-xox": ["t_xox" + "b-1234567890-abcdef", '"a\\n' + "xox" + "b-1234567890-abcdef"],
    "vcs-id-fine": ["t_github" + "_pat_" + "d" * 30, '"a\\n' + "github" + "_pat_" + "d" * 30],
}
LEAD_MISSES = [
    "x" + AWS_KEY,
    "9" + AWS_KEY,
    AWS_KEY + "x",
    AWS_KEY + "Q",
    "task-" + "b" * 40,
    "pghp".replace("p", "x", 1) + "_" + "c" * 36,
    "x" + GH_KEY,
    "x" + "xox" + "b-1234567890-abcdef",
    "Xgithub" + "_pat_" + "d" * 30,
]


@pytest.mark.parametrize(
    ("rule", "line"), [(r, ln) for r, lines in LEAD_HITS.items() for ln in lines]
)
def test_a_secret_after_an_underscore_or_an_escape_letter_is_found(tmp_path, rule, line):
    rc, out = _scan(_repo(tmp_path, {"a.py": "v = " + line + "\n"}))
    assert rc == 1 and f"a.py:1: {rule}" in out


@pytest.mark.parametrize("line", LEAD_MISSES)
def test_a_secret_shape_inside_a_longer_word_is_not_flagged(tmp_path, line):
    assert _scan(_repo(tmp_path, {"a.py": "v = " + line + "\n"})) == (0, "\n")


def test_the_example_key_after_an_underscore_is_still_the_allowed_placeholder(tmp_path):
    assert _scan(_repo(tmp_path, {"a.py": "v = id_" + EXAMPLE_KEY + "\n"})) == (0, "\n")


# M6 (r3): more scanner-config files; M4 (design r3): .gitattributes can blind gitleaks
BLIND_LINES = [
    "cred.txt -diff",
    "* -diff",
    "*.png binary",
    "  x\t-diff",
    "* binary",
    "a b -diff c",
    "x text -diff",
]
SEEING_LINES = [
    "* text=auto eol=lf",
    "# x -diff in a comment",
    "x -text",
    "x diff=foo",
    "x merge=binary",
    "x binary-ish",
    "x -diffs",
    "*.sh eol=lf",
]


@pytest.mark.parametrize("line", BLIND_LINES)
def test_a_gitattributes_line_that_hides_the_diff_is_a_hit_even_when_pinned(tmp_path, line):
    text = "* text=auto\n" + line + "\n"
    repo = _repo(tmp_path, {".gitattributes": text})
    rc, out = _scan(repo, suppress=_supp_line(".gitattributes", "scanner-config-file", _sha(text)))
    assert rc == 1 and ".gitattributes:2: gitattributes-hides-diff" in out


@pytest.mark.parametrize("line", SEEING_LINES)
def test_a_gitattributes_line_that_leaves_the_diff_alone_only_needs_its_pin(tmp_path, line):
    text = line + "\n"
    repo = _repo(tmp_path, {"sub/.gitattributes": text})
    assert _scan(repo)[0] == 1
    pin = _supp_line("sub/.gitattributes", "scanner-config-file", _sha(text))
    assert _scan(repo, suppress=pin) == (0, "\n")


# N8 (r3): the config hash is taken on line-ending-normalised bytes (a Windows checkout may turn LF into CRLF)
def test_a_config_file_checked_out_with_crlf_has_the_same_hash(tmp_path):
    repo = _repo(tmp_path, {".gitleaksignore": b"one\r\ntwo\r\n"})
    pin = _supp_line(".gitleaksignore", "scanner-config-file", _sha("one\ntwo\n"))
    assert _scan(repo, suppress=pin) == (0, "\n")
    other = _repo(tmp_path / "o", {".gitleaksignore": b"one\r\nthree\r\n"})
    rc, out = _scan(other, suppress=pin)
    assert rc == 1 and "hash differs" in out


# N1, N2 (r3): an empty noqa and a bare lgtm
@pytest.mark.parametrize(
    "line",
    [
        "x = 1  " + H + "no" + "qa:",
        "x = 1  " + H + "no" + "qa: ",
        "x = 1  " + H + "no" + "qa:  " + H + "why",
        "x = 1  #no" + "qa:",
        "x = 1  " + H + "no" + "qa: because it is fine",
        "x = 1  " + H + "NO" + "QA :",
    ],
)
def test_an_empty_or_codeless_noqa_is_a_blanket_noqa_hit(tmp_path, line):
    rc, out = _scan(_repo(tmp_path, {"a.py": line + "\n"}))
    assert rc == 1 and "a.py:1: suppress-noqa-security" in out


@pytest.mark.parametrize(
    "line",
    [
        "x = 1  " + H + "lg" + "tm",
        "x = 1  //LG" + "TM",
        "x = 1  " + H + "lg" + "tm, thanks",
        H + "lg" + "tm",
    ],
)
def test_a_bare_lgtm_comment_is_a_marker_like_the_bracket_form(tmp_path, line):
    rc, out = _scan(_repo(tmp_path, {"a.py": line + "\n"}))
    assert rc == 1 and "a.py:1: suppress-lgtm" in out


@pytest.mark.parametrize(
    "line",
    [
        "the lgtm word in prose",
        "x = 'lgtm'",
        "x = 1  " + H + "slgtm",
        "x = 1  " + H + "no" + "qa: E501",
    ],
)
def test_prose_with_lgtm_and_a_coded_noqa_are_not_hits(tmp_path, line):
    assert _scan(_repo(tmp_path, {"a.py": line + "\n"})) == (0, "\n")


# design r3 N9: ruff skips some folders by default, so a tracked Python file there is never linted
@pytest.mark.parametrize(
    "name",
    [
        "build/x.py",
        "a/dist/b.py",
        "venv/x.pyi",
        "src/node_modules/y/z.py",
        "a/site-packages/b.py",
        ".tox/t.py",
        "_build/x.py",
        "a/.venv/x.py",
    ],
)
def test_a_python_file_below_a_folder_that_ruff_skips_is_a_hit(tmp_path, name):
    rc, out = _scan(_repo(tmp_path, {name: "x = 1\n"}))
    assert rc == 1 and f"{name}:1: py-in-ruff-skipped-dir" in out


@pytest.mark.parametrize(
    "name", ["src/build.py", "dist.py", "build/notes.txt", "a/building/x.py", "venv.py"]
)
def test_other_files_near_those_folder_names_are_fine(tmp_path, name):
    assert _scan(_repo(tmp_path, {name: "x = 1\n"})) == (0, "\n")
