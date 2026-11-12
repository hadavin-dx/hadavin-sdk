"""Every workflow file is valid YAML, and no step name holds an unquoted colon followed by a space.

The class: a plain (unquoted) YAML value that holds ": " is read as a nested mapping, so the whole file stops
parsing and every test that reads it fails at once (round 2 of the demo-only banner work: one step name broke
tests/test_ci_gitleaks_scope.py). The check lives here, over every file under .github/workflows, so a new workflow
file is covered with no edit.
"""

import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
FILES = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
# `- name: value` or `name: value` where the value is plain: it does not start with a quote, a block marker or an anchor.
NAME_LINE = re.compile(r"^\s*(?:-\s+)?name:\s+(?P<value>[^\"'|>&*!#\s].*)$")


def unquoted_colon_names(text: str) -> list[tuple[int, str]]:
    """(line number, name) for each plain `name:` value that holds a colon followed by a space or ends in a colon."""
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        match = NAME_LINE.match(line)
        if match and re.search(r":(\s|$)", match["value"].split(" #")[0]):
            out.append((number, match["value"]))
    return out


def test_there_are_workflow_files_to_check() -> None:
    assert FILES, "no workflow file found: the checks below would pass on nothing"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_the_workflow_file_parses_as_yaml(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data.get("jobs"), f"{path.name} is not a workflow mapping"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_step_name_holds_an_unquoted_colon(path: Path) -> None:
    found = unquoted_colon_names(path.read_text(encoding="utf-8"))
    assert not found, (
        f"{path.name}: quote or reword these names (a colon and a space breaks YAML): {found}"
    )


def test_the_detector_finds_the_broken_name_and_the_parse_really_fails() -> None:
    """The control: the exact shape that broke ci.yml is found by the detector and is invalid for the parser."""
    broken = "jobs:\n  a:\n    steps:\n      - name: Copy run (only when it is there: tests must pass)\n        run: true\n"
    assert unquoted_colon_names(broken) == [
        (4, "Copy run (only when it is there: tests must pass)")
    ]
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(broken)
    for fine in (
        '- name: "Copy run: quoted"',
        "- name: Copy run; reworded",
        "- name: Run # a comment: here",
        "- name: a:b has no space",
    ):
        assert unquoted_colon_names(fine) == [], fine
