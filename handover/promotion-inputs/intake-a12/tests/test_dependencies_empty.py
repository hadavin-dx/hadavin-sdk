"""The package stays stdlib only after every work package: ``dependencies == []``. Dev-only tools (browser driver, recorder) go in a dependency
group named ``video``, never in ``dependencies``."""

from __future__ import annotations

import tomllib

from conftest import ROOT


def load() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_dependencies_is_an_empty_list():
    assert load()["project"]["dependencies"] == []


def test_no_optional_dependencies_and_dev_groups_are_named():
    d = load()
    assert "optional-dependencies" not in d["project"]
    assert set(d["dependency-groups"]) <= {"test", "video"}


def test_script_marker_and_addopts():
    d = load()
    assert d["project"]["scripts"] == {"intake": "intake.cli:main"}
    opts = d["tool"]["pytest"]["ini_options"]
    assert opts["addopts"] == '-m "not e2e"' and any(m.startswith("e2e:") for m in opts["markers"])


def test_gitignore_lists_the_key_file_its_lock_and_the_passphrase_copy():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for needed in ("secrets.env", "secrets.env.lock", "approver-passphrase.txt", "**/secrets/"):
        assert needed in lines, needed


def test_ci_checks_out_the_kit_at_the_recorded_commit_and_sets_the_variable():
    import json
    import re

    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    commit = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))["allowed_local"]["src/intake/core_copy/strict_json.py"][
        "source_commit"
    ]
    assert ci.count("INTAKE_KIT_SOURCE:") == 2  # the check job and the cut job
    assert ci.count(f"ref: {commit}") == 2 and ci.count("repository: hadavin-dx/hadavin-" + "portal" + "-kit") == 2
    assert ci.count("fetch-depth: 0") >= 2
    for m in re.finditer(r"uses: (actions/checkout)@(\S+)", ci):
        assert re.fullmatch(r"[0-9a-f]{40}", m.group(2)), m.group(0)  # every checkout is pinned to a full commit SHA
    assert ci.count('mv kit "$RUNNER_TEMP/kit"') == 2
