"""The Python versions CI runs must agree with pyproject's `requires-python`.

CI runs the tests on every supported Python: the required job `check` on the newest (3.13) and the job `tests-py312`
on the oldest. Those are two jobs and not a `strategy.matrix` on purpose (a matrix would rename the required check
"check" and the two jobs differ in steps and env). This test reads the versions from every `python-version:` of a
setup step and from any `matrix.python-version` list, so it holds for either layout: the lowest version CI
runs must be the `requires-python` floor, the highest must be the one the main job `check` uses, and no job may pin a
Python below the floor.
"""

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAIN_JOB = "check"


def _ver(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)\.(\d+)", str(text).strip())
    assert m, f"not a MAJOR.MINOR python version: {text!r}"
    return int(m[1]), int(m[2])


def requires_floor(pyproject: Path) -> tuple[int, int]:
    spec = tomllib.loads(pyproject.read_text())["project"]["requires-python"]
    lowers = re.findall(r"(?:>=|~=|==)\s*(\d+\.\d+)", spec)
    assert len(lowers) == 1, f"cannot read one lower bound from requires-python {spec!r}"
    return _ver(lowers[0])


def ci_versions(ci: Path) -> dict[str, list[tuple[int, int]]]:
    """job name -> every Python version the job pins (setup step input or matrix list)."""
    jobs = yaml.safe_load(ci.read_text())["jobs"]
    out: dict[str, list[tuple[int, int]]] = {}
    for name, job in jobs.items():
        found: list[str] = []
        matrix = (job.get("strategy") or {}).get("matrix") or {}
        listed = matrix.get("python-version", [])
        found += [listed] if isinstance(listed, str) else list(listed)
        for step in job.get("steps", []):
            value = (step.get("with") or {}).get("python-version")
            if value is not None:
                assert "${{" not in str(value) or matrix, (
                    f"{name}: python-version is an expression but there is no matrix"
                )
                if "${{" not in str(value):
                    found.append(str(value))
        if found:
            out[name] = [_ver(v) for v in found]
    return out


def check_agreement(pyproject: Path, ci: Path) -> None:
    floor = requires_floor(pyproject)
    versions = ci_versions(ci)
    assert MAIN_JOB in versions, f"job {MAIN_JOB!r} pins no python-version"
    everything = [v for vs in versions.values() for v in vs]
    below = {job: vs for job, vs in versions.items() if min(vs) < floor}
    assert not below, f"jobs pin a Python below requires-python {floor}: {below}"
    assert min(everything) == floor, (
        f"lowest CI Python {min(everything)} != requires-python floor {floor}"
    )
    assert max(everything) == max(versions[MAIN_JOB]), (
        f"highest CI Python {max(everything)} is not the main job's {max(versions[MAIN_JOB])}"
    )


def test_ci_python_versions_agree_with_requires_python():
    check_agreement(ROOT / "pyproject.toml", ROOT / ".github" / "workflows" / "ci.yml")


def _copy(
    tmp_path: Path, *, ci_floor: str | None = None, requires: str | None = None
) -> tuple[Path, Path]:
    pyproject = tmp_path / "pyproject.toml"
    ci = tmp_path / "ci.yml"
    text = (ROOT / "pyproject.toml").read_text()
    if requires:
        text = text.replace('requires-python = ">=3.12"', f'requires-python = "{requires}"')
    pyproject.write_text(text)
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    if ci_floor:
        ci_text = ci_text.replace('python-version: "3.12"', f'python-version: "{ci_floor}"')
    ci.write_text(ci_text)
    return pyproject, ci


def test_the_copies_agree_unchanged(tmp_path):
    check_agreement(*_copy(tmp_path))


def test_ci_floor_below_requires_python_fails(tmp_path):
    try:
        check_agreement(*_copy(tmp_path, ci_floor="3.11"))
    except AssertionError as exc:
        assert "below requires-python" in str(exc)
    else:
        raise AssertionError("a CI job on 3.11 passed against requires-python >=3.12")


def test_requires_python_raised_above_ci_floor_fails(tmp_path):
    try:
        check_agreement(*_copy(tmp_path, requires=">=3.13"))
    except AssertionError as exc:
        assert "below requires-python" in str(exc)
    else:
        raise AssertionError("CI on 3.12 passed against requires-python >=3.13")


def test_ci_floor_above_requires_python_fails(tmp_path):
    try:
        check_agreement(*_copy(tmp_path, ci_floor="3.13"))
    except AssertionError as exc:
        assert "lowest CI Python" in str(exc)
    else:
        raise AssertionError("CI starting at 3.13 passed against requires-python >=3.12")
