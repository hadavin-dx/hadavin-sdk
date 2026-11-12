"""Run the real "Stale gitleaks ignore entries" step of ci.yml in throwaway git repositories.

Branches named `wip/cloud-*` are handover lane refs: they carry the same handover files as `core/cloud-handover` and never
merge into main. The guard must let those two names through and still fail for every other branch name, and it must still fail
when the checked-out head itself carries such a file, even if a lane ref carries the same commit. The step text is taken from
ci.yml and run as it is (bash -e, like the runner), so a change to the real lines changes what these tests exercise.
"""

import datetime
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from tests.test_ci_gitleaks_scope import CI, _load, _step

STEP = "Stale gitleaks ignore entries"
HANDOVER_FILE = "handover/reviews/x/round1.md"
TOML = "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\ntargetRules = [\"generic-api-key\"]\npaths = ['''^handover/(reviews|tickets|evidence)/[^/]+\\.md$''']\n"


def _git(repo, *args):
    env = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "PATH": "/usr/bin:/bin",
    }
    out = subprocess.run(  # noqa: S603 (fixed argv, no shell)
        ["/usr/bin/git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return out.stdout.strip()


def _commit(repo, name, text, message):
    path = Path(repo) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _remove(repo, name, message):
    _git(repo, "rm", "-q", name)
    _git(repo, "commit", "-q", "-m", message)


def _ref(repo, branch, sha):
    _git(repo, "update-ref", f"refs/remotes/origin/{branch}", sha)


def _expires():
    day = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    return f"# EXPIRES {day}\n"


@pytest.fixture
def repo(tmp_path):
    """main with a config and an empty ignore list; origin/main and origin/core/cloud-handover (one handover file) exist;
    HEAD is a clean branch from main."""
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "work")
    _commit(r, ".gitleaks.toml", TOML, "config")
    _commit(r, ".gitleaksignore", _expires(), "ignore list")
    main = _git(r, "rev-parse", "HEAD")
    _ref(r, "main", main)
    _commit(r, HANDOVER_FILE, "note\n", "handover lane")
    _ref(r, "core/cloud-handover", _git(r, "rev-parse", "HEAD"))
    _git(r, "reset", "-q", "--hard", main)
    return r


def _lane_branch(repo, branch):
    """A remote branch `branch` off main that carries the handover file."""
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, HANDOVER_FILE, "note two\n", f"handover on {branch}")
    _ref(repo, branch, sha)
    _git(repo, "reset", "-q", "--hard", keep)
    return sha


def _run_guard(repo, path_prefix=""):
    script = repo / "step.sh"
    script.write_text(_step(_load(), STEP)["run"])
    res = subprocess.run(  # noqa: S603 (fixed argv, no shell string)
        ["/bin/bash", "-e", str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{path_prefix}:/usr/bin:/bin" if path_prefix else "/usr/bin:/bin",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
        },
        check=False,
    )
    script.unlink()
    return res.returncode, res.stdout + res.stderr


def test_the_guard_passes_a_clean_checkout(repo):
    rc, out = _run_guard(repo)
    assert rc == 0, out


@pytest.mark.parametrize("branch", ["wip/cloud-x", "wip/cloud-245-B-P4da2", "wip/cloud-a.b_c"])
def test_a_wip_cloud_lane_branch_with_a_handover_file_passes(repo, branch):
    _lane_branch(repo, branch)
    rc, out = _run_guard(repo)
    assert rc == 0, out


@pytest.mark.parametrize(
    "branch",
    [
        "core/other",
        "wip/other",
        "wip/cloudx",
        "wip",
        "cloud-x",
        "feature/wip/cloud-x",
        "wip/cloud-x/y",  # a slash: the git glob would match it, the pattern does not
        "wip/cloud-",  # an empty suffix
        "wip/cloud-a+b",
    ],
)
def test_any_other_branch_with_a_handover_file_still_fails(repo, branch):
    _lane_branch(repo, branch)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "handover notes exist in the history" in out


def test_a_head_built_on_a_lane_commit_still_fails_even_if_a_lane_ref_has_it(repo):
    """The lane ref holds both the commit that adds the file and the commit that deletes it, so no commit in the subtracted
    range touches it and the tree is clean: only the separate check of HEAD's own history can see it."""
    _commit(repo, HANDOVER_FILE, "note\n", "lane commit adds the file")
    _remove(repo, HANDOVER_FILE, "lane commit deletes it again")
    _ref(repo, "wip/cloud-x", _git(repo, "rev-parse", "HEAD"))
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def test_a_lane_ref_pointing_at_another_branchs_commits_cannot_excuse_them_in_head(repo):
    # This pins a documented weakness: outside HEAD the lane subtraction hides another branch's notes (the repository ruleset is the
    # control). A later hardening must change this test on purpose.
    keep = _git(repo, "rev-parse", "HEAD")
    other = _commit(repo, HANDOVER_FILE, "note\n", "handover file on another branch")
    _ref(repo, "core/other", other)
    _ref(repo, "wip/cloud-y", other)  # a writer points a lane name at that branch's tip
    _git(repo, "reset", "-q", "--hard", keep)
    # outside HEAD the range is hygiene only: the lane ref hides the other branch's file there (the repository ruleset is the answer)
    rc, out = _run_guard(repo)
    assert rc == 0, out
    # but once HEAD contains those commits the control reports them
    _git(repo, "merge", "-q", "--no-edit", other)
    _remove(repo, HANDOVER_FILE, "delete the file again")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def test_a_missing_core_cloud_handover_ref_is_reported_without_a_git_error(repo):
    _git(repo, "update-ref", "-d", "refs/remotes/origin/core/cloud-handover")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "and branch core/cloud-handover is missing" in out
    assert "fatal" not in out


def test_a_head_tree_with_a_handover_file_fails(repo):
    _commit(repo, HANDOVER_FILE, "x\n", "file in the tree")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "checkout's tree" in out


def _ignore_entry(sha):
    return f"{_expires()}{sha}:handover/reviews/x/round1.md:generic-api-key:3\n"


NOTE = "handover/reviews/round1.md"


@pytest.mark.parametrize(
    ("path", "rule"),
    [
        (
            NOTE,
            "generic-api-key",
        ),  # even a handover note with the generic rule: a lane-only entry has no legitimate use
        ("handover/tickets/t1.md", "generic-api-key"),
        ("src/app.py", "generic-api-key"),
        ("src/app.py", "private-key"),
        (NOTE, "private-key"),
    ],
)
def test_an_ignore_entry_on_a_lane_only_commit_is_stale(repo, path, rule):
    lane = _lane_branch(repo, "wip/cloud-x")
    _commit(repo, ".gitleaksignore", f"{_expires()}{lane}:{path}:{rule}:3\n", "ignore entry")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry (not on a named handover branch)" in out


def test_an_ignore_entry_for_a_sha_that_is_not_in_the_clone_is_stale_and_later_checks_run(repo):
    """git branch --contains exits 129 for an unknown sha: that must neither abort the step nor skip the checks after it."""
    entry = f"{'0' * 40}:{NOTE}:generic-api-key:3\n"
    _commit(repo, ".gitleaksignore", entry, "entry without an EXPIRES line")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry" in out
    assert "no '# EXPIRES YYYY-MM-DD' line" in out  # a later check still ran
    assert "fatal" not in out and "error:" not in out


def test_an_ignore_entry_on_a_fixed_named_branch_keeps_any_path_and_rule(repo):
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, "notes/x.txt", "x\n", "a commit outside handover/")
    _ref(repo, "core/cloud-handover", sha)  # the fixed name carries it
    _git(repo, "reset", "-q", "--hard", keep)
    _commit(repo, ".gitleaksignore", f"{_expires()}{sha}:src/app.py:private-key:3\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 0, out


def test_an_ignore_entry_on_another_branch_is_stale(repo):
    keep = _git(repo, "rev-parse", "HEAD")
    other = _commit(repo, "notes/x.txt", "x\n", "a commit on another branch, outside handover/")
    _ref(repo, "core/other", other)
    _git(repo, "reset", "-q", "--hard", keep)
    _commit(repo, ".gitleaksignore", f"{_expires()}{other}:{NOTE}:generic-api-key:3\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry" in out


@pytest.mark.parametrize("branch", ["wip/cloud-x/y", "wip/cloud-", "wip/cloud-a+b"])
def test_an_ignore_entry_on_a_non_matching_lane_name_is_stale(repo, branch):
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, "notes/x.txt", "x\n", "commit")
    _ref(repo, branch, sha)
    _git(repo, "reset", "-q", "--hard", keep)
    _commit(repo, ".gitleaksignore", f"{_expires()}{sha}:{NOTE}:generic-api-key:3\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry" in out


TOML_NO_TARGET = (
    "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = 'AND'\npaths = ['^docs/.*']\n"
)


@pytest.mark.parametrize("toml", ["", "[extend]\nuseDefault = true\n", TOML_NO_TARGET])
def test_the_path_checks_do_not_depend_on_what_the_pull_request_writes_into_gitleaks_toml(
    repo, toml
):
    """A pull request carries its own .gitleaks.toml: rewriting it must not switch the handover path checks off."""
    _commit(repo, ".gitleaks.toml", toml, "the pull request rewrites the config")
    rc, out = _run_guard(repo)
    assert rc == 0, out  # control: no handover note, same config
    _commit(repo, HANDOVER_FILE, "note\n", "a handover note")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "checkout's tree" in out
    _remove(repo, HANDOVER_FILE, "deleted again")
    rc, out = _run_guard(repo)
    assert rc == 1, out  # the history still carries it
    assert "history of HEAD itself" in out


def test_a_tag_named_origin_main_does_not_weaken_the_main_history_check(repo):
    main = _git(repo, "rev-parse", "refs/remotes/origin/main")
    _commit(repo, ".gitignore", "x\n", "later commit")
    _commit(repo, ".gitleaksignore", f"{_expires()}{main}:src/a.py:generic-api-key:3\n", "entry")
    root = _git(repo, "rev-list", "--max-parents=0", "HEAD")
    _git(repo, "tag", "origin/main", root)  # the short name origin/main now resolves to this tag
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "ignore entry is in main history" in out


def test_a_tag_named_origin_core_cloud_handover_does_not_replace_the_deleted_branch(repo):
    tip = _git(repo, "rev-parse", "refs/remotes/origin/core/cloud-handover")
    _git(repo, "tag", "origin/core/cloud-handover", tip)
    _git(repo, "update-ref", "-d", "refs/remotes/origin/core/cloud-handover")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "and branch core/cloud-handover is missing" in out


def test_a_tag_named_origin_core_cloud_handover_does_not_replace_the_branch_in_the_range(repo):
    """The branch still exists (it carries a handover note); a tag of the short name at another commit must not be subtracted
    in its place, or the note would be listed and every pull request would fail."""
    main = _git(repo, "rev-parse", "refs/remotes/origin/main")
    _git(repo, "tag", "origin/core/cloud-handover", main)
    rc, out = _run_guard(repo)
    assert rc == 0, out


def test_a_merge_commit_that_adds_and_a_later_merge_that_removes_a_note_are_still_listed(repo):
    """Neither merge touches the note relative to both parents, so a log without -m shows nothing for them and the tree is clean."""
    base = _git(repo, "rev-parse", "HEAD")
    s1 = _commit(repo, "src/s1.py", "x = 1\n", "side one")
    _git(repo, "reset", "-q", "--hard", base)
    x = _commit(repo, "src/x.py", "x = 2\n", "side x")
    _git(repo, "reset", "-q", "--hard", base)
    _commit(repo, "src/s2.py", "x = 3\n", "side two")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", s1)
    (repo / HANDOVER_FILE).parent.mkdir(parents=True, exist_ok=True)
    (repo / HANDOVER_FILE).write_text("note\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "merge that adds a note")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", x)
    _git(repo, "rm", "-q", "-f", HANDOVER_FILE)
    _git(repo, "commit", "-q", "-m", "merge that removes the note")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def test_a_merge_of_a_side_branch_with_a_handover_note_fails_even_if_the_merge_removes_it(repo):
    base = _git(repo, "rev-parse", "HEAD")
    side = _commit(repo, HANDOVER_FILE, "note\n", "side branch adds a note")
    _git(repo, "reset", "-q", "--hard", base)
    _commit(repo, "src/a.py", "x = 1\n", "work on the main line")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", side)
    _git(
        repo, "rm", "-q", "-f", HANDOVER_FILE
    )  # the merge itself drops the note: the tree is clean
    _git(repo, "commit", "-q", "-m", "merge without the note")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def _fake_git_failing_merge_base(tmp_path):
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text(
        '#!/bin/sh\nif [ "$1" = merge-base ]; then echo "fatal: simulated failure" >&2; exit 128; fi\nexec /usr/bin/git "$@"\n'
    )
    fake.chmod(0o755)
    return str(bin_dir)


def _entry_line(sha):
    return f"{sha}:src/a.py:generic-api-key:3"


def test_an_entry_for_a_commit_in_the_pull_requests_own_history_is_refused_unless_main_has_the_line(
    repo,
):
    """A forged fixed-name branch at a commit of this pull request would otherwise make its entry acceptable."""
    c = _commit(repo, "src/a.py", "x = 1\n", "a commit of this pull request")
    _ref(repo, "core/P2d-1", c)
    _commit(repo, ".gitleaksignore", f"{_expires()}{_entry_line(c)}\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "ignore entry hides a commit in this pull request's own history" in out


def test_an_entry_for_a_commit_in_the_own_history_is_accepted_when_main_has_the_identical_line(
    repo,
):
    base = _git(repo, "rev-parse", "HEAD")
    c = _commit(repo, "src/a.py", "x = 1\n", "fixture commit on the P2d-1 branch")
    _ref(repo, "core/P2d-1", c)
    _git(repo, "reset", "-q", "--hard", base)
    # main's file in its real shape: comments, EXPIRES, then the entry
    text = f"# header\n{_expires()}# why: fake values\n{_entry_line(c)}\n"
    m2 = _commit(repo, ".gitleaksignore", text, "main takes the entry")
    _ref(repo, "main", m2)
    _git(repo, "merge", "-q", "--no-edit", c)  # the pull request head now holds both
    rc, out = _run_guard(repo)
    assert rc == 0, out
    # a different line for the same commit (other path) is not the identical line
    _commit(
        repo, ".gitleaksignore", text.replace("src/a.py", "src/b.py"), "pull request edits the line"
    )
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "own history" in out


def test_an_entry_for_a_commit_outside_the_head_history_keeps_the_old_rule(repo):
    base = _git(repo, "rev-parse", "HEAD")
    c = _commit(repo, "src/a.py", "x = 1\n", "commit on another branch")
    _ref(repo, "core/P2d-1", c)
    _git(repo, "reset", "-q", "--hard", base)
    _commit(repo, ".gitleaksignore", f"{_expires()}{_entry_line(c)}\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 0, out


def test_a_missing_origin_main_is_reported_even_if_a_tag_has_that_name(repo):
    root = _git(repo, "rev-list", "--max-parents=0", "HEAD")
    _git(repo, "tag", "origin/main", root)
    _git(repo, "update-ref", "-d", "refs/remotes/origin/main")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "origin/main is missing" in out


def test_an_evil_merge_on_another_branch_that_introduces_a_note_is_listed_by_the_range_check(repo):
    base = _git(repo, "rev-parse", "HEAD")
    s1 = _commit(repo, "src/s1.py", "x = 1\n", "side one")
    _git(repo, "reset", "-q", "--hard", base)
    _commit(repo, "src/s2.py", "x = 2\n", "side two")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", s1)
    (repo / HANDOVER_FILE).parent.mkdir(parents=True, exist_ok=True)
    (repo / HANDOVER_FILE).write_text("note\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "merge that adds a note")
    _ref(repo, "core/other", _git(repo, "rev-parse", "HEAD"))  # neither HEAD nor a lane
    _git(repo, "reset", "-q", "--hard", base)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "a branch other than core/cloud-handover" in out


def test_an_error_of_git_merge_base_fails_the_step_with_a_message(repo, tmp_path):
    keep = _git(repo, "rev-parse", "HEAD")
    c = _commit(repo, "notes/x.txt", "x\n", "commit on a fixed branch")
    _ref(repo, "core/cloud-handover", c)
    _git(repo, "reset", "-q", "--hard", keep)
    _commit(repo, ".gitleaksignore", f"{_expires()}{_entry_line(c)}\n", "entry")
    rc, out = _run_guard(repo)
    assert rc == 0, out  # control: real git, the entry is fine
    rc, out = _run_guard(repo, path_prefix=_fake_git_failing_merge_base(tmp_path))
    assert rc == 1, out
    assert "git merge-base failed (exit 128)" in out


def test_the_failure_message_names_the_refs_that_hold_the_notes(repo):
    _lane_branch(repo, "core/other")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert f"{HANDOVER_FILE} (on: origin/core/other" in out


def test_the_head_failure_message_names_the_refs_that_hold_the_notes(repo):
    _commit(repo, HANDOVER_FILE, "note\n", "lane commit adds the file")
    _remove(repo, HANDOVER_FILE, "lane commit deletes it again")
    _ref(repo, "wip/cloud-x", _git(repo, "rev-parse", "HEAD"))
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert f"{HANDOVER_FILE} (on: origin/wip/cloud-x" in out


def _own_history_case(repo, main_line, pr_line, tag_main=False):
    """C is a commit of this pull request that the fixed branch core/P2d-1 also holds. main's .gitleaksignore carries
    main_line(C), the pull request's carries pr_line(C). Returns the guard result."""
    base = _git(repo, "rev-parse", "HEAD")
    c = _commit(repo, "src/a.py", "x = 1\n", "fixture commit")
    _ref(repo, "core/P2d-1", c)
    _git(repo, "reset", "-q", "--hard", base)
    m2 = _commit(repo, ".gitleaksignore", f"{_expires()}{main_line(c)}\n", "main takes the entry")
    _ref(repo, "main", m2)
    _git(repo, "merge", "-q", "--no-edit", c)
    if tag_main:
        _git(
            repo, "tag", "origin/main", base
        )  # the short name origin/main resolves to this older commit
    _commit(
        repo, ".gitleaksignore", f"{_expires()}# pull request\n{pr_line(c)}\n", "pull request entry"
    )
    return _run_guard(repo)


def test_an_entry_must_equal_a_whole_line_of_mains_file(repo):
    """grep -x: an entry that is only the start of a main line (line 3 against line 33) is not the identical line."""
    rc, out = _own_history_case(
        repo,
        lambda c: f"{c}:src/a.py:generic-api-key:33",
        lambda c: f"{c}:src/a.py:generic-api-key:3",
    )
    assert rc == 1, out
    assert "own history" in out


def test_an_entry_is_compared_as_a_fixed_string_not_a_pattern(repo):
    """grep -F: the dot in the path of the entry must not match another character in main's line."""
    rc, out = _own_history_case(
        repo,
        lambda c: f"{c}:src/aXpy:generic-api-key:3",
        lambda c: f"{c}:src/a.py:generic-api-key:3",
    )
    assert rc == 1, out
    assert "own history" in out


def test_the_identical_line_is_still_accepted(repo):
    same = lambda c: f"{c}:src/a.py:generic-api-key:3"
    rc, out = _own_history_case(repo, same, same)
    assert rc == 0, out


def test_main_is_read_from_the_branch_not_from_a_tag_of_the_same_short_name(repo):
    same = lambda c: f"{c}:src/a.py:generic-api-key:3"
    rc, out = _own_history_case(repo, same, same, tag_main=True)
    assert rc == 0, out  # the tag points at a commit without the line: only the branch has it


@pytest.mark.parametrize("name", ["é.md", 'q"uote.md', "a[1].md "])
def test_a_note_with_an_unusual_file_name_is_listed_by_every_path_check(repo, name):
    """git quotes such names unless -z is used, and a quoted name no longer starts with handover/."""
    path = f"handover/reviews/{name}"
    # range check: the note is on another branch
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, path, "note\n", "note on another branch")
    _ref(repo, "core/other", sha)
    _git(repo, "reset", "-q", "--hard", keep)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "a branch other than core/cloud-handover" in out
    _git(repo, "update-ref", "-d", "refs/remotes/origin/core/other")
    # tree check
    _commit(repo, path, "note\n", "note in the tree")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "in this checkout's tree" in out
    # HEAD history check only: added and deleted, both commits on a lane ref
    _remove(repo, path, "deleted again")
    _ref(repo, "wip/cloud-x", _git(repo, "rev-parse", "HEAD"))
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def test_a_note_that_is_only_on_a_tag_is_listed_by_the_range_check(repo):
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, HANDOVER_FILE, "note\n", "note under a tag")
    _git(repo, "tag", "t1", sha)
    _git(repo, "reset", "-q", "--hard", keep)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "a branch other than core/cloud-handover" in out


def test_a_fixed_name_must_match_whole_and_handover_src_is_accepted(repo):
    keep = _git(repo, "rev-parse", "HEAD")
    a = _commit(repo, "notes/a.txt", "a\n", "commit on a look-alike name")
    _ref(repo, "core/P2d-1-x", a)
    _git(repo, "reset", "-q", "--hard", keep)
    b = _commit(repo, "notes/b.txt", "b\n", "commit on handover-src")
    _ref(repo, "handover-src/c1a-8460813", b)
    _git(repo, "reset", "-q", "--hard", keep)
    _commit(
        repo,
        ".gitleaksignore",
        f"{_expires()}{b}:src/a.py:generic-api-key:3\n",
        "entry on handover-src",
    )
    rc, out = _run_guard(repo)
    assert rc == 0, out  # positive case: a fixed name, not an ancestor of HEAD
    _commit(
        repo,
        ".gitleaksignore",
        f"{_expires()}{a}:src/a.py:generic-api-key:3\n",
        "entry on a look-alike",
    )
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry" in out


def test_the_failure_message_lists_a_file_name_with_glob_characters_and_trailing_space_literally(
    repo,
):
    """show_where must not trim the name (IFS=)."""
    _lane_branch(repo, "core/other")
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, "handover/reviews/a[1].md ", "note\n", "odd name")
    _ref(repo, "core/other2", sha)
    _git(repo, "reset", "-q", "--hard", keep)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "handover/reviews/a[1].md  (on: origin/core/other2" in out


def test_the_failure_message_reads_a_file_name_with_a_star_as_a_literal_path(repo):
    """With a glob pathspec the star name also matches nz.md and the newest commit (the one on core/nzb) would be named."""
    keep = _git(repo, "rev-parse", "HEAD")
    star = _commit(repo, "handover/reviews/n*.md", "note\n", "star name")
    _ref(repo, "core/starb", star)
    nz = _commit(
        repo, "handover/reviews/nz.md", "note\n", "newer file that a glob would also match"
    )
    _ref(repo, "core/nzb", nz)
    _git(repo, "reset", "-q", "--hard", keep)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    line = next(ln for ln in out.splitlines() if ln.startswith("  handover/reviews/n*.md (on:"))
    assert "origin/core/starb" in line


GUARD_PAT = re.compile(r"^\s*pat='([^']+)'$", re.MULTILINE)


def _guard_pattern():
    return re.search(GUARD_PAT, _step(_load(), STEP)["run"]).group(1)


def _samples(regex):
    """Literal sample paths a toml path regex accepts: strip anchors, expand (a|b) groups, drop [^/]+ and escapes."""
    text = regex.removeprefix("^").removesuffix("$")
    out = [text]
    while any("(" in t for t in out):
        nxt = []
        for t in out:
            m = re.search(r"\(([^()]*)\)", t)
            if not m:
                nxt.append(t)
                continue
            nxt += [t[: m.start()] + alt + t[m.end() :] for alt in m.group(1).split("|")]
        out = nxt
    return [t.replace("[^/]+", "x").replace("\\.", ".") for t in out]


def _guard_gaps(toml_text):
    """Problems where an allowlist path regex that mentions handover/ is not covered by the guard pattern."""
    guard = _guard_pattern()
    gaps = []
    for al in tomllib.loads(toml_text).get("allowlists", []):
        for rx in al.get("paths", []):
            if "handover/" not in rx:
                continue
            if not rx.startswith("^"):
                gaps.append(f"not anchored: {rx}")
            gaps += [f"not guarded: {s}" for s in _samples(rx) if not re.search(guard, s)]
    return gaps


def test_the_guard_pattern_covers_every_handover_path_the_real_toml_allows():
    real = (CI.parents[2] / ".gitleaks.toml").read_text()
    assert _samples("^handover/(reviews|tickets|evidence)/[^/]+\\.md$") == [
        "handover/reviews/x.md",
        "handover/tickets/x.md",
        "handover/evidence/x.md",
    ]
    assert _guard_gaps(real) == []


@pytest.mark.parametrize(
    "regex",
    [
        "handover/(reviews|tickets)/[^/]+\\.md$",
        "^docs/handover/reviews/[^/]+\\.md$",
        "^handover/notes/[^/]+\\.md$",
    ],
)
def test_a_widened_toml_path_is_reported_as_a_gap(regex):
    toml = f"[extend]\nuseDefault = true\n[[allowlists]]\ncondition = 'AND'\npaths = ['{regex}']\n"
    assert _guard_gaps(toml) != []


def test_the_old_allowlist_wording_is_gone_and_the_new_rule_is_stated():
    run = _step(_load(), STEP)["run"]
    assert "would hide generic keys" not in run
    assert "does not run this step as a pull request head" not in run
    assert "they may live only" in run


def test_the_step_name_is_a_plain_string_that_yaml_cannot_misread():
    name = _step(_load(), STEP)["name"]
    assert isinstance(name, str)
    assert ": " not in name  # a mapping
    assert " #" not in name  # a comment
    assert name[0] not in "-?:,[]{}#&*!|>'\"%@`", name  # a YAML indicator character
    assert not name.endswith(":")  # a trailing colon
    assert name == name.strip()
    # the raw text of the line too: " #" would start a YAML comment and silently shorten the parsed name
    raw = [
        ln for ln in CI.read_text().splitlines() if ln.strip().startswith("- name: " + name[:20])
    ]
    assert len(raw) == 1
    assert raw[0].strip() == "- name: " + name


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
