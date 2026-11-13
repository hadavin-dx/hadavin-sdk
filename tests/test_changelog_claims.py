"""The Unreleased pathguard entry in CHANGELOG.md makes claims about the code. Each claim is checked against the code in its
own test, so the text cannot drift from what runs. The entry is the heading bullet and the indented bullets under it."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.config import confined
from hadavin_sdk.errors import ConfigError

ROOT = Path(__file__).resolve().parent.parent
LINES = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
START = next(i for i, line in enumerate(LINES) if line.startswith("- **Path checks:"))
END = next((i for i in range(START + 1, len(LINES)) if LINES[i].startswith("- ")), len(LINES))
ENTRY = "\n".join(LINES[START:END])
BULLETS = [line.strip() for line in LINES[START + 1 : END] if line.startswith("  - ")]


def bullet(start: str) -> str:
    found = [b for b in BULLETS if b.startswith(f"- **{start}")]
    assert len(found) == 1, f"expected one bullet that starts with {start!r}, found {len(found)}"
    return found[0]


def test_the_heading_is_narrow_and_names_the_scan_it_depends_on():
    assert LINES[START].startswith(
        "- **Path checks: `hadavin_sdk/pathguard.py` holds the rules for the file operations"
    )
    assert "package tripwire test lists" in LINES[START]
    assert "tests/fixtures/pathguard_exceptions.txt" in ENTRY


def test_the_module_docstring_makes_the_same_narrow_claim():
    first = (pathguard.__doc__ or "").splitlines()[0]
    assert "listed by the package tripwire test" in first or "tripwire test" in first


@pytest.mark.parametrize("n", range(1, 14))
def test_every_rule_from_r1_to_r13_is_named_as_a_whole_word(n):
    assert re.search(rf"\(R{n}\)|\bR{n}\b", bullet("The rules (R1 to R13)")), f"R{n} is not named"


def test_the_rule_list_does_not_name_a_rule_that_does_not_exist():
    text = bullet("The rules (R1 to R13)")
    named = {int(m) for m in re.findall(r"\bR(\d+)\b", text)}
    assert named <= set(range(1, 14))


def test_the_numbers_in_the_entry_are_the_numbers_in_the_code():
    assert f"at most {pathguard.MAX_COMPONENT_BYTES} bytes" in ENTRY
    assert f"at most {pathguard.MAX_PATH_CHARS} characters" in ENTRY
    assert f"{pathguard.MAX_WRITE_NAME_BYTES} bytes" in ENTRY
    assert f"{len(pathguard.CONTROL_RANGES)} ranges" in ENTRY


@pytest.mark.parametrize("name", ["con", "aux", "com1"])
def test_device_names_named_in_the_entry_are_refused(name):
    assert f"`{name}`" in ENTRY
    with pytest.raises(pathguard.PathRefused):
        pathguard.component(name, what="n")


def test_r6_r7_and_r12_apply_to_names_from_data_and_not_to_inside(tmp_path):
    assert "`component` and `join`" in bullet("R6, R7 and R12 apply")
    pathguard.inside(tmp_path, tmp_path / "con", what="n")  # a device name is not refused by inside
    with pytest.raises(pathguard.PathRefused):
        pathguard.join(tmp_path, "con", what="n")


def test_a_refusal_names_the_argument_never_the_value(tmp_path):
    bullet("A refusal names the argument")
    with pytest.raises(
        pathguard.PathRefused, match="^outputs folder: contains a control character$"
    ):
        pathguard.operator_dir(str(tmp_path) + chr(0x202E), what="outputs folder")


def test_the_atomic_write_signature_and_temp_name_claims(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    text = bullet("`k1b.atomic.atomic_write(path, text)` is now")
    assert "`.<name>.<random>.tmp`" in text
    atomic_write(tmp_path, "f.txt", "x")
    assert [p.name for p in tmp_path.iterdir()] == ["f.txt"]


def test_atomic_write_refuses_a_folder_and_a_taken_temp_name_as_r13(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    assert "(R13)" in bullet("`atomic_write` refuses what it cannot replace")
    (tmp_path / "d").mkdir()
    with pytest.raises(pathguard.PathRefused) as caught:
        atomic_write(tmp_path, "d", "x")
    assert caught.value.rule == "R13"


def test_confined_keeps_its_text_and_a_nul_is_a_config_error(tmp_path):
    assert "path escapes its folder" in bullet("`config.confined` refuses")
    with pytest.raises(ConfigError, match="path escapes its folder"):
        confined(tmp_path, "../x")
    with pytest.raises(ConfigError):
        confined(tmp_path, "a\x00b")
    with pytest.raises(ConfigError):
        confined(tmp_path, "a" + chr(0x202E))


def test_outputs_files_raises_for_a_missing_folder(tmp_path):
    from hadavin_sdk.k1b.replay import outputs_files

    assert "raises a `ConfigError` for a missing outputs folder" in bullet("`replay.outputs_files`")
    with pytest.raises(ConfigError):
        outputs_files(tmp_path / "missing")


def test_the_sonar_claim_says_nothing_is_cleared():
    text = bullet("What this does not claim")
    assert "does not claim that any SonarCloud finding is cleared" in text
    assert not re.search(r"(?<!not )\b(clears|fixes) the SonarCloud", ENTRY)


def test_the_entry_states_the_limits_it_knows():
    text = bullet("What this does not claim")
    for limit in ("260 characters", "hard links", "mount points", "junctions"):
        assert limit in text


def test_the_entry_does_not_say_for_any_reason_or_everywhere():
    assert "for any reason" not in ENTRY and "everywhere" not in ENTRY.lower()


def test_the_exception_list_the_entry_names_has_seven_columns_and_a_reason_each():
    path = ROOT / "tests" / "fixtures" / "pathguard_exceptions.txt"
    rows = [
        r
        for r in path.read_text(encoding="utf-8").splitlines()
        if r.strip() and not r.startswith("#")
    ]
    assert rows and all(len(r.split(" | ")) == 7 for r in rows)


def test_the_backslash_is_written_once_in_the_rules():
    assert "`/` or `\\`" in bullet("The rules (R1 to R13)")
    assert "`\\\\`" not in bullet("The rules (R1 to R13)")


def test_a_strict_join_sits_right_before_each_of_the_four_reads():
    bullet("A strict join right before the read.")
    root = ROOT / "src" / "hadavin_sdk"
    for rel in ("k1b/score.py", "hashing.py", "actions/secrets_file.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "must_exist=True" in text and 'kind="file"' in text, rel
    score = (root / "k1b/score.py").read_text(encoding="utf-8")
    assert score.count('kind="file"') >= 3  # answers file, digest file, output files
