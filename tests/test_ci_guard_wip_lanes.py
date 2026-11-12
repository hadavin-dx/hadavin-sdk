"""Run the real "Stale gitleaks ignore entries" step of ci.yml in throwaway git repositories.

Branches named `wip/cloud-*` are handover lane refs: they carry the same handover files as `core/cloud-handover` and never
merge into main. The guard must let those two names through and still fail for every other branch name, and it must still fail
when the checked-out head itself carries such a file, even if a lane ref carries the same commit. The step text is taken from
ci.yml and run as it is (bash -e, like the runner), so a change to the real lines changes what these tests exercise.
"""

import datetime
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_ci_gitleaks_scope import _load, _step

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


def _lane_branch(repo, branch, ignore_line=None):
    """A remote branch `branch` off main that carries the handover file (and optionally an ignore line for its commit)."""
    keep = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, HANDOVER_FILE, "note two\n", f"handover on {branch}")
    _ref(repo, branch, sha)
    _git(repo, "reset", "-q", "--hard", keep)
    return sha


def _run_guard(repo):
    script = repo / "step.sh"
    script.write_text(_step(_load(), STEP)["run"])
    res = subprocess.run(  # noqa: S603 (fixed argv, no shell string)
        ["/bin/bash", "-e", str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
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
    "branch", ["core/other", "wip/other", "wip/cloudx", "wip", "cloud-x", "feature/wip/cloud-x"]
)
def test_any_other_branch_with_a_handover_file_still_fails(repo, branch):
    _lane_branch(repo, branch)
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "files under handover/ exist in the history" in out


def test_a_head_built_on_a_lane_commit_still_fails_even_if_a_lane_ref_has_it(repo):
    """The lane refs are subtracted from the range, so only the separate check of HEAD's own history sees this."""
    sha = _lane_branch(repo, "wip/cloud-x")
    _git(repo, "merge", "-q", "--no-edit", sha)  # HEAD now contains the lane commit
    _remove(repo, HANDOVER_FILE, "delete the file again: the tree is clean, the history is not")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "history of HEAD itself" in out


def test_a_head_tree_with_a_handover_file_fails(repo):
    _commit(repo, HANDOVER_FILE, "x\n", "file in the tree")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "checkout's tree" in out


def _ignore_entry(sha):
    return f"{_expires()}{sha}:handover/reviews/x/round1.md:generic-api-key:3\n"


def test_an_ignore_entry_on_a_wip_cloud_branch_is_accepted_and_on_another_branch_is_stale(repo):
    lane = _lane_branch(repo, "wip/cloud-x")
    keep = _git(repo, "rev-parse", "HEAD")
    other = _commit(repo, "notes/x.txt", "x\n", "a commit on another branch, outside handover/")
    _ref(repo, "core/other", other)
    _git(repo, "reset", "-q", "--hard", keep)
    # the ignore list must exist in the tree of HEAD: commit it on the clean branch
    _commit(repo, ".gitleaksignore", _ignore_entry(lane), "ignore entry on a lane commit")
    rc, out = _run_guard(repo)
    assert rc == 0, out
    _commit(repo, ".gitleaksignore", _ignore_entry(other), "ignore entry on another branch")
    rc, out = _run_guard(repo)
    assert rc == 1, out
    assert "stale ignore entry" in out


def test_the_step_text_has_no_unquoted_glob_and_a_valid_name():
    step = _step(_load(), STEP)
    assert ": " not in step["name"]
    assert "'--remotes=origin/wip/cloud-*'" in step["run"]
    assert "wip/cloud-[A-Za-z0-9._-]+" in step["run"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
