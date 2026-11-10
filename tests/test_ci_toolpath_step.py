"""Run the real text of the CI step "System tools resolve outside the workspace" in bash on a temporary tree.

The step must fail when a tool on PATH is, or is a link to, a file inside the workspace, and must accept the legitimate venv: python3, uv
and uvx may sit in <workspace>/.venv/bin, but only as links to a file outside the workspace. Linux and bash only (the CI runner is Linux).
"""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
SYSTEM = [
    *("readlink", "sha256sum", "tar", "curl", "git", "grep", "date"),
    *("tr", "cut", "sort", "head", "mktemp", "rm", "touch"),
]
VENV = ["python3", "uv", "uvx"]
BASH = shutil.which("bash")
GIT = shutil.which("git")  # an absolute path, so the calls below are not partial-path calls


def _run(argv, *, check=False, **kw):
    """The one place this file starts a program; every argument list is fixed by the test (no input from outside)."""
    return subprocess.run(argv, check=check, **kw)  # noqa: S603


pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or BASH is None or shutil.which("git") is None,
    reason="needs Linux, bash and git",
)


def _step_text():
    wf = yaml.safe_load(CI.read_text())
    steps = [
        s
        for s in wf["jobs"]["security"]["steps"]
        if s.get("name", "").startswith("System tools resolve")
    ]
    assert len(steps) == 1
    return steps[0]["run"]


class Tree:
    """tmp/outside/bin holds the 'system' tools (links to the real ones); tmp/ws is the workspace."""

    def __init__(self, tmp_path):
        self.tmp = tmp_path
        self.out = tmp_path / "outside" / "bin"
        self.out.mkdir(parents=True)
        self.ws = tmp_path / "ws"
        self.ws.mkdir()
        _run([GIT, "init", "-q", str(self.ws)], check=True)
        for name in SYSTEM:
            real = shutil.which(name)
            assert real, name
            (self.out / name).symlink_to(real)
        (self.out / "python3").symlink_to(os.path.realpath(sys.executable))
        for name in ("uv", "uvx"):  # stand-ins: the step only looks at where they resolve
            (self.out / name).write_text("#!/bin/sh\n")
            (self.out / name).chmod(0o755)
        self.path = [str(self.out)]

    def evil(self, rel="evil"):
        f = self.ws / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("#!/bin/sh\n")
        f.chmod(0o755)
        return f

    def run(self, workspace=None):
        env = {
            "PATH": os.pathsep.join(self.path),
            "GITHUB_WORKSPACE": str(workspace or self.ws),
            "HOME": str(self.tmp),
        }
        r = _run(
            [BASH, "-e", "-c", _step_text()],
            cwd=self.ws,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return r.returncode, r.stdout + r.stderr


@pytest.fixture
def tree(tmp_path):
    return Tree(tmp_path)


def test_a_clean_tree_passes(tree):
    assert tree.run()[0] == 0


def test_the_legitimate_venv_passes(tree):
    venv = tree.ws / ".venv" / "bin"
    venv.mkdir(parents=True)
    for name in VENV:
        (venv / name).symlink_to(
            os.path.realpath(sys.executable) if name == "python3" else tree.out / name
        )
    tree.path.insert(0, str(venv))
    assert tree.run() == (0, "")


@pytest.mark.parametrize("name", SYSTEM)
def test_a_system_tool_found_inside_the_workspace_fails(tree, name):
    bin_dir = tree.ws / "bin"
    bin_dir.mkdir()
    (bin_dir / name).write_text("#!/bin/sh\n")
    (bin_dir / name).chmod(0o755)
    tree.path.insert(0, str(bin_dir))
    rc, out = tree.run()
    assert rc == 1 and f"{name} resolves inside the workspace" in out


@pytest.mark.parametrize("name", SYSTEM + VENV)
def test_a_tool_that_is_a_link_to_a_workspace_file_fails(tree, name):
    (tree.out / name).unlink()
    (tree.out / name).symlink_to(tree.evil())
    rc, out = tree.run()
    # a stand-in readlink prints nothing, which must fail too (it cannot vouch for anything)
    expect = "cannot resolve" if name == "readlink" else f"{name} is a link into the workspace"
    assert rc == 1 and expect in out


def test_a_two_step_link_chain_into_the_workspace_fails(tree):
    (tree.out / "curl").unlink()
    hop = tree.tmp / "outside" / "hop"
    hop.symlink_to(tree.evil())
    (tree.out / "curl").symlink_to(hop)
    assert tree.run()[0] == 1


def test_a_workspace_reached_through_a_link_is_still_the_workspace(tree):
    (tree.out / "tar").unlink()
    (tree.out / "tar").symlink_to(tree.evil())
    alias = tree.tmp / "ws-alias"
    alias.symlink_to(tree.ws)
    rc, out = tree.run(workspace=alias)
    assert rc == 1 and "is a link into the workspace" in out


@pytest.mark.parametrize("name", VENV)
def test_a_regular_file_in_the_venv_fails(tree, name):
    venv = tree.ws / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / name).write_text("#!/bin/sh\n")
    (venv / name).chmod(0o755)
    tree.path.insert(0, str(venv))
    rc, out = tree.run()
    assert rc == 1 and f"{name} is a link into the workspace" in out


@pytest.mark.parametrize("name", VENV)
def test_the_venv_exception_does_not_cover_other_workspace_folders(tree, name):
    other = tree.ws / "tools" / "bin"
    other.mkdir(parents=True)
    (other / name).symlink_to(tree.out / name)
    tree.path.insert(0, str(other))
    rc, out = tree.run()
    assert rc == 1 and f"{name} resolves inside the workspace" in out


def test_a_system_tool_in_the_venv_fails(tree):
    venv = tree.ws / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "curl").symlink_to(tree.out / "curl")
    tree.path.insert(0, str(venv))
    rc, out = tree.run()
    assert rc == 1 and "curl resolves inside the workspace" in out


def test_a_missing_tool_fails(tree):
    (tree.out / "uvx").unlink()
    rc, out = tree.run()
    assert rc == 1 and "uvx not found" in out


def test_a_non_absolute_command_fails(tree):
    step = _step_text().replace("for c in $sys_tools", "alias_ok=1; for c in $sys_tools", 1)
    # a shell function named like a tool is not a file
    r = _run(
        [BASH, "-e", "-c", "curl() { :; }\n" + step],
        cwd=tree.ws,
        env={"PATH": str(tree.out), "GITHUB_WORKSPACE": str(tree.ws)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1 and "curl is not a file" in r.stdout + r.stderr


def test_tracked_files_under_dot_venv_fail(tree):
    (tree.ws / ".venv").mkdir()
    (tree.ws / ".venv" / "marker").write_text("x")
    _run([GIT, "-C", str(tree.ws), "add", "-f", ".venv/marker"], check=True)
    rc, out = tree.run()
    assert rc == 1 and "files under .venv are tracked" in out


def test_an_empty_workspace_variable_fails(tree):
    r = _run(
        [BASH, "-e", "-c", _step_text()],
        cwd=tree.ws,
        env={"PATH": str(tree.out), "GITHUB_WORKSPACE": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1 and "GITHUB_WORKSPACE is empty" in r.stdout + r.stderr


OLD_STEP_COMMIT = (
    "2742c1b"  # the PR90 merge: the step text below is frozen from that commit's ci.yml
)


# sha256 of the old step's `run` text (stripped), taken from `git show 2742c1b:.github/workflows/ci.yml` on 2026-11-10 (the "System tools"
# step of the security job). Pinned here instead of read from git, so the check also runs in a shallow CI checkout (the commit is absent
# there) and never skips.
OLD_STEP_SHA256 = "a5b6306467f55376f5de3cd4197ef541f7c660b9a90dfcec91037844784a93bd"


def test_the_frozen_old_step_text_is_the_one_that_was_stored_in_git_history():
    """Guards the frozen text below against drift; to refresh the hash, re-read the step from the commit named in OLD_STEP_COMMIT."""
    assert hashlib.sha256(_old_step().strip().encode()).hexdigest() == OLD_STEP_SHA256


def _old_step():
    return (
        'for c in sha256sum tar curl git grep date tr cut sort head mktemp rm touch; do p=$(command -v "$c") || exit 1; '
        'case "$p" in /*) ;; *) echo "$c is not a file: $p"; exit 1;; esac; '
        'case "$p" in "$GITHUB_WORKSPACE"/*) echo "$c resolves inside the workspace: $p"; exit 1;; esac; done'
    )


def test_the_old_step_text_misses_a_link_into_the_workspace(tree):
    """Fail-before proof kept as a test: the PR90 step (command -v only) accepts a link whose target is in the workspace."""
    old = _old_step()
    (tree.out / "curl").unlink()
    (tree.out / "curl").symlink_to(tree.evil())
    env = {"PATH": str(tree.out), "GITHUB_WORKSPACE": str(tree.ws)}
    old_run = _run([BASH, "-e", "-c", old], env=env, cwd=tree.ws, check=False)
    assert old_run.returncode == 0
    assert tree.run()[0] == 1
