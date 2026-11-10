"""tools/scan_repo.py: each rule hits, near misses and the documented placeholder do not, the allow-list is rule-scoped.
Fake secrets are built from parts so this file itself never holds one. The real tools/*.txt files are never rewritten:
the script takes --allowlist/--extra/--banned-src."""

import hashlib
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


def _scan(repo, allow="", extra="", banned_src=None, suppress=""):
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
    assert _scan(repo, allow="a.txt:llm-id-sk:ok\n")[0] == 0
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
    "suppress-nosemgrep": "x = f(1)  " + H + "nosem" + "grep: some.rule",
    "suppress-gitleaks-allow": "x = 'abc'  " + H + "gitleaks:" + "allow",
    "suppress-trivy-ignore": H + "trivy:" + "ignore:AVD-DS-0002",
    "suppress-noqa-security": "x = f(1)  " + H + "no" + "qa: S603",
}
MORE_MARKERS = {
    "suppress-nosec": ["x = f(1)  //nos" + "ec", "x = 1 -- nos" + "ec"],
    "suppress-nosemgrep": ["x = 1  " + H + "nosem", "x = 1  " + H + "nosem: some.rule"],
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
    "we do not use nosem" + "grep here",
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
    rc, out = _scan(repo, allow="a.py:*:test fixture\n")
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
        ("a.py:suppress-nosec:" + ONE + ":r\na.py:suppress-nosec:" + ONE + ":again\n", "duplicate"),
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
    root = SCRIPT.parents[1]
    cmd = [sys.executable, str(SCRIPT), "--root", str(root)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    assert r.returncode == 0, r.stdout[-2000:]


def test_the_real_list_says_the_baseline_was_not_reviewed_line_by_line():
    text = (SCRIPT.parent / "scan_suppressions.txt").read_text()
    assert "NOT reviewed one" in text and "CODEOWNERS" in text


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
    assert _scan(repo, suppress=_supp_line(name, "scanner-config-file", sha))[0] == 0
    rc, out = _scan(repo, suppress=_supp_line(name, "scanner-config-file", "1" * 64))
    assert rc == 1 and "hash differs" in out


@pytest.mark.parametrize("name", ["a.py", "pyproject.toml", "ci.yml", "x.sh"])
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
    old = _supp_line("a.py", "suppress-nosec", ONE, "kept reason")
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
    assert ":kept reason" in r.stdout and "NEW, needs a reviewed reason" in r.stdout
    assert _scan(repo, suppress=r.stdout) == (0, "\n")


REAL_LIST = SCRIPT.parent / "scan_suppressions.txt"


def test_a_weakened_copy_of_the_real_list_fails_the_scan(tmp_path):
    """The guard is only as strong as the list it reads: remove an entry, or change a count or a hash, and the real repo fails."""
    root = SCRIPT.parents[1]
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
