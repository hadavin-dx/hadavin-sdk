"""The Python versions CI runs must agree with pyproject's `requires-python`.

CI runs the tests on every supported Python: the required job `check` on the newest (3.13) and the job `tests-py312`
on the oldest. Those are two jobs and not a `strategy.matrix` on purpose (a matrix would rename the required check
"check" and the two jobs differ in steps and env). The rules enforced here:

* the lowest version CI runs is the `requires-python` floor (`>=3.12.3` keeps floor 3.12: only MAJOR.MINOR counts),
  no pin is below it, and when `requires-python` has an upper bound `<X` no CI version is at or above X;
* the highest version CI runs is the one the main job `check` uses. DELIBERATE: an extra, newer pre-release job
  (say a 3.14 canary) fails this test until MAIN_JOB or the assertion is updated by hand: a version that nothing
  required runs on must be a conscious decision, not a drive-by edit.

Every way of pinning a Python in `.github/workflows/*.yml|yaml` and `.github/actions/**/action.y*ml` is read: a
`python-version` input of any step or reusable-workflow call, `strategy.matrix.python-version` and
`matrix.include` entries, `python-version-file` (followed: `.python-version`, `pyproject.toml`, `.tool-versions`),
`UV_PYTHON` / `PYTHON_VERSION` in `env` at workflow, job or step level, `--python X` of any `uv`/`uvx` command,
`uv python install|pin X` in any `run:` text, `python:X` images (job `container`, `services`, `docker://` steps) and a
repo-root `.python-version`. A value that cannot be resolved fails loudly, except a plain `${{ matrix.python-version }}`
(counted through the matrix) and, in a composite action, `${{ inputs.NAME }}` (its default). An unquoted YAML float
(`3.10` is read as 3.1) fails with "quote the version".

Each assertion carries a marker comment `[A:<id>]`; the planted tests (`test_planted_<id>_...`) each make exactly that
assertion fire on a tmp copy, so deleting the assertion turns its test red.
"""

import re
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MAIN_JOB = "check"
ENV_KEYS = ("UV_PYTHON", "PYTHON_VERSION")
MATRIX_REF = re.compile(r"\$\{\{\s*matrix\.python-version\s*\}\}")
INPUT_REF = re.compile(r"\$\{\{\s*inputs\.([\w-]+)\s*\}\}")
_VERSION = re.compile(
    r"(?:cpython-|python|pypy-?)?(\d+)\.(\d+)(?:\.(?:\d+|x))?(?:t|-?(?:dev|alpha|beta|rc|a|b)[\w.]*)?"
)
UV_PYTHON_FLAG = re.compile(r"\buvx?\b[^\n;&|]*?\s--python(?:=|\s+)(?P<v>[^\s;&|]+)")
UV_PYTHON_CMD = re.compile(r"\buv\s+python\s+(?:install|pin)\b(?P<args>[^\n;&|]*)")
PY_IMAGE = re.compile(r"(?:docker://)?(?:docker\.io/)?(?:library/)?python:(?P<tag>\S+)")


def _ver(text: str) -> tuple[int, int]:
    m = _VERSION.fullmatch(str(text).strip().strip("'\""))
    assert m, f"cannot read a MAJOR.MINOR python version from {text!r}"  # [A:ver]
    return int(m[1]), int(m[2])


def requires_floor(pyproject: Path) -> tuple[int, int]:
    spec = tomllib.loads(pyproject.read_text())["project"]["requires-python"]
    lowers = re.findall(
        r"(?:>=|~=|==)\s*(\d+\.\d+)", spec
    )  # `>=3.12.3` yields 3.12: patch levels are ignored
    assert len(lowers) == 1, (
        f"cannot read one lower bound from requires-python {spec!r}"
    )  # [A:one-lower]
    return _ver(lowers[0])


def requires_ceiling(pyproject: Path) -> tuple[int, int] | None:
    spec = tomllib.loads(pyproject.read_text())["project"]["requires-python"]
    uppers = re.findall(r"(?<![<>=!~])<(?!=)\s*(\d+)(?:\.(\d+))?", spec)
    assert len(uppers) <= 1, (
        f"more than one upper bound in requires-python {spec!r}"
    )  # [A:one-upper]
    return (int(uppers[0][0]), int(uppers[0][1] or 0)) if uppers else None


def _resolve(
    value, where: str, matrix: list | None, inputs: dict | None = None
) -> list[tuple[int, int]]:
    """Versions named by one value. `matrix` is None without a matrix, [] for a matrix without python-version."""
    assert not isinstance(value, float), (  # [A:float]
        f"{where}: {value!r} is a YAML float (3.10 reads as 3.1): quote the version"
    )
    text = str(value).strip()
    if "${{" in text:
        if MATRIX_REF.fullmatch(text):
            assert matrix is not None, (
                f"{where}: matrix.python-version but the job has no strategy.matrix"
            )  # [A:expr-nomatrix]
            assert matrix, f"{where}: the matrix has no python-version key"  # [A:matrix-key]
            return []  # the matrix list itself is collected and compared
        ref = INPUT_REF.fullmatch(text)
        if ref and inputs is not None and "default" in (inputs.get(ref[1]) or {}):
            return _resolve((inputs[ref[1]] or {})["default"], where, matrix)
        raise AssertionError(
            f"{where}: cannot resolve the expression {text!r} to a python version"
        )  # [A:expr-unresolvable]
    tokens = [t for t in re.split(r"[\s,]+", text) if t]
    assert tokens, f"{where}: empty python version"  # [A:empty]
    return [_ver(t) for t in tokens]


def _file_pins(spec, root: Path, where: str) -> list[tuple[int, int]]:
    assert "${{" not in str(spec), (
        f"{where}: python-version-file {spec!r} is an expression"
    )  # [A:file-expr]
    path = root / str(spec)
    assert path.is_file() and path.resolve().is_relative_to(root.resolve()), (  # [A:file-missing]
        f"{where}: python-version-file {spec!r} is not a file of this repository"
    )
    if path.name == "pyproject.toml":
        return [requires_floor(path)]
    if path.name in (".python-version", ".tool-versions"):
        lines = [ln.split("#")[0].split() for ln in path.read_text().splitlines()]
        if path.name == ".tool-versions":  # only the `python <version>` line counts
            lines = [ln[1:2] for ln in lines if ln[:1] == ["python"]]
        words = [w for ln in lines for w in ln]
        assert words, f"{where}: {spec!r} names no python version"  # [A:file-empty]
        return [_ver(w) for w in words]
    raise AssertionError(
        f"{where}: cannot follow python-version-file {spec!r} (unsupported file)"
    )  # [A:file-unsupported]


def _run_pins(text: str, where: str) -> list[tuple[int, int]]:
    text = text.replace("\\\n", " ")
    found = [_ver(m["v"]) for m in UV_PYTHON_FLAG.finditer(text)]
    for m in UV_PYTHON_CMD.finditer(text):
        found += [_ver(a) for a in m["args"].split() if not a.startswith("-")]
    return found


def _image_pin(image, where: str) -> list[tuple[int, int]]:
    text = str(image).strip()
    m = PY_IMAGE.fullmatch(text)
    if not m:
        assert not ("python" in text and "${{" in text), (
            f"{where}: cannot resolve the image {text!r}"
        )  # [A:image-expr]
        return []
    tag = re.match(r"(\d+)\.(\d+)", m["tag"])
    assert tag, (
        f"{where}: cannot read a MAJOR.MINOR version from the image {text!r}"
    )  # [A:image-tag]
    return [(int(tag[1]), int(tag[2]))]


def _env_pins(
    env, where: str, matrix: list | None, inputs: dict | None = None
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for key in ENV_KEYS:
        if isinstance(env, dict) and key in env:
            out += _resolve(env[key], f"{where} env {key}", matrix, inputs)
    return out


def _step_pins(step, where, root, matrix, inputs=None) -> list[tuple[int, int]]:
    out = _env_pins(step.get("env"), where, matrix, inputs)
    with_ = step.get("with") or {}
    if "python-version" in with_:
        out += _resolve(with_["python-version"], f"{where} python-version", matrix, inputs)
    if "python-version-file" in with_:
        out += _file_pins(with_["python-version-file"], root, where)
    if isinstance(step.get("run"), str):
        out += _run_pins(step["run"], where)
    if isinstance(step.get("uses"), str):
        out += _image_pin(step["uses"], where)
    return out


def _matrix(job: dict, where: str) -> tuple[list | None, list[tuple[int, int]]]:
    """(raw matrix python values or None without matrix, the versions they name)."""
    matrix = (job.get("strategy") or {}).get("matrix")
    if matrix is None:
        return None, []
    assert isinstance(matrix, dict), (
        f"{where}: matrix {matrix!r} is not a mapping, its versions cannot be read"
    )  # [A:matrix-expr]
    raw: list = []
    listed = matrix.get("python-version", [])
    raw += [listed] if isinstance(listed, str | float | int) else list(listed)
    for entry in matrix.get("include") or []:
        if isinstance(entry, dict) and "python-version" in entry:
            raw.append(entry["python-version"])
    versions = [v for item in raw for v in _resolve(item, f"{where} matrix", None)]
    return raw, versions


def _job_pins(job: dict, where: str, root: Path) -> list[tuple[int, int]]:
    raw, out = _matrix(job, where)
    out = list(out)
    out += _env_pins(job.get("env"), where, raw)
    if "python-version" in (job.get("with") or {}):  # a reusable-workflow call
        out += _resolve(job["with"]["python-version"], f"{where} python-version", raw)
    container = job.get("container")
    for image in [container.get("image") if isinstance(container, dict) else container]:
        out += _image_pin(image, where) if image else []
    for service in (job.get("services") or {}).values():
        out += _image_pin(service.get("image") or "", where)
    for step in job.get("steps") or []:
        out += _step_pins(step, where, root, raw)
    return out


def ci_versions(ci: Path, root: Path | None = None) -> dict[str, list[tuple[int, int]]]:
    """name -> every Python version pinned there: jobs of `ci` by job name, other files as `file:job`."""
    root = root or ci.parents[2]
    out: dict[str, list[tuple[int, int]]] = {}

    def add(key: str, versions: list[tuple[int, int]]) -> None:
        if versions:
            out.setdefault(key, []).extend(versions)

    files = sorted([*ci.parent.glob("*.yml"), *ci.parent.glob("*.yaml")])
    for wf in files:
        doc = yaml.safe_load(wf.read_text()) or {}
        if not isinstance(doc, dict):
            continue
        prefix = "" if wf.resolve() == ci.resolve() else f"{wf.name}:"
        add(f"{prefix}(workflow env)", _env_pins(doc.get("env"), f"{wf.name} workflow", None))
        for name, job in (doc.get("jobs") or {}).items():
            add(f"{prefix}{name}", _job_pins(job or {}, f"{wf.name}:{name}", root))
    actions = root / ".github" / "actions"
    for act in sorted([*actions.glob("**/action.yml"), *actions.glob("**/action.yaml")]):
        doc = yaml.safe_load(act.read_text()) or {}
        inputs = doc.get("inputs") or {}
        where = str(act.relative_to(root))
        pins: list[tuple[int, int]] = []
        for step in (doc.get("runs") or {}).get("steps") or []:
            pins += _step_pins(step, where, root, None, inputs)
        add(where, pins)
    pv = root / ".python-version"
    if pv.is_file():
        add(".python-version", _file_pins(".python-version", root, ".python-version"))
    return out


def check_agreement(pyproject: Path, ci: Path) -> None:
    floor = requires_floor(pyproject)
    ceiling = requires_ceiling(pyproject)
    versions = ci_versions(ci, pyproject.parent)
    assert MAIN_JOB in versions, f"job {MAIN_JOB!r} pins no python-version"  # [A:no-main]
    everything = [v for vs in versions.values() for v in vs]
    below = {job: vs for job, vs in versions.items() if min(vs) < floor}
    assert not below, f"jobs pin a Python below requires-python {floor}: {below}"  # [A:below]
    if ceiling:
        above = {job: vs for job, vs in versions.items() if max(vs) >= ceiling}
        assert not above, (
            f"jobs pin a Python at or above the requires-python bound <{ceiling}: {above}"
        )  # [A:above]
    assert min(everything) == floor, (  # [A:floor]
        f"lowest CI Python {min(everything)} != requires-python floor {floor}"
    )
    assert max(everything) == max(versions[MAIN_JOB]), (  # [A:main-highest]
        f"highest CI Python {max(everything)} is not the main job's {max(versions[MAIN_JOB])}"
    )


def test_ci_python_versions_agree_with_requires_python():
    check_agreement(ROOT / "pyproject.toml", ROOT / ".github" / "workflows" / "ci.yml")


# ---------------------------------------------------------------- planted mismatches on tmp copies


def _tree(
    tmp_path: Path, *, ci_floor=None, requires=None, edit=None, files=None
) -> tuple[Path, Path]:
    """A tmp repo: pyproject.toml, .github/workflows/ci.yml (optionally edited), extra files {relpath: text}."""
    pyproject = tmp_path / "pyproject.toml"
    ci = tmp_path / ".github" / "workflows" / "ci.yml"
    ci.parent.mkdir(parents=True)
    text = (ROOT / "pyproject.toml").read_text()
    if requires:
        assert 'requires-python = ">=3.12"' in text
        text = text.replace('requires-python = ">=3.12"', f'requires-python = "{requires}"')
    pyproject.write_text(text)
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    if ci_floor:
        ci_text = ci_text.replace('python-version: "3.12"', f'python-version: "{ci_floor}"')
    if edit:
        doc = yaml.safe_load(ci_text)
        edit(doc)
        ci_text = yaml.safe_dump(doc, sort_keys=False)
    ci.write_text(ci_text)
    for rel, content in (files or {}).items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return pyproject, ci


def _copy(tmp_path: Path, *, ci_floor: str | None = None, requires: str | None = None):
    return _tree(tmp_path, ci_floor=ci_floor, requires=requires)


def _must_fail(tmp_path: Path, needle: str, **kw) -> None:
    """check_agreement on the planted copy must raise an AssertionError that contains `needle`."""
    try:
        check_agreement(*_tree(tmp_path, **kw))
    except AssertionError as exc:
        assert needle in str(exc), f"failed, but not on the planted assertion: {exc}"
    else:
        raise AssertionError(f"the planted mismatch ({needle!r}) passed")


def _job(*steps, **extra) -> dict:
    return {"runs-on": "ubuntu-24.04", "steps": list(steps), **extra}


def _setup(version) -> dict:
    return {"uses": "astral-sh/setup-uv@v1", "with": {"python-version": version}}


def _add_job(name: str, job: dict):
    return lambda doc: doc["jobs"].update({name: job})


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


def test_planted_floor_ci_never_reaches_the_floor(tmp_path):
    # [A:floor] lowest CI Python above the floor (the pre-existing case, here with a requires-python of 3.11)
    _must_fail(tmp_path, "lowest CI Python", requires=">=3.11")


def _swap_main_and_oldest(doc):
    doc["jobs"]["check"]["steps"][1]["with"]["python-version"] = "3.12"
    doc["jobs"]["tests-py312"]["steps"][1]["with"]["python-version"] = "3.13"


def test_planted_main_highest_check_on_312_while_tests_on_313(tmp_path):
    # [A:main-highest] `check` on 3.12 while `tests-py312` is on 3.13
    _must_fail(tmp_path, "is not the main job's", edit=_swap_main_and_oldest)


def test_planted_main_highest_extra_job_on_314(tmp_path):
    # [A:main-highest] an extra job pinned to 3.14 above the main job
    _must_fail(tmp_path, "is not the main job's", edit=_add_job("canary", _job(_setup("3.14"))))


def test_planted_no_main_job(tmp_path):
    # [A:no-main] the main job `check` pins no python-version (renamed)
    def rename(doc):
        doc["jobs"]["renamed"] = doc["jobs"].pop("check")

    _must_fail(tmp_path, "pins no python-version", edit=rename)


def test_planted_below_matrix_list(tmp_path):
    # [A:below] a matrix list reaching 3.11
    job = _job({"run": "true"}, strategy={"matrix": {"python-version": ["3.11", "3.13"]}})
    _must_fail(tmp_path, "below requires-python", edit=_add_job("m", job))


def test_planted_below_matrix_string_and_include(tmp_path):
    # [A:below] matrix python-version given as one string, and as an include entry
    one = _job({"run": "true"}, strategy={"matrix": {"python-version": "3.11"}})
    _must_fail(tmp_path, "below requires-python", edit=_add_job("m", one))
    inc = _job({"run": "true"}, strategy={"matrix": {"include": [{"python-version": "3.11"}]}})
    _must_fail(tmp_path / "inc", "below requires-python", edit=_add_job("m", inc))


def test_a_matrix_referenced_by_expression_is_counted_and_passes(tmp_path):
    job = _job(
        _setup("${{ matrix.python-version }}"),
        strategy={"matrix": {"python-version": ["3.12", "3.13"]}},
    )
    pyproject, ci = _tree(tmp_path, edit=_add_job("m", job))
    check_agreement(pyproject, ci)
    assert ci_versions(ci, tmp_path)["m"] == [(3, 12), (3, 13)]


def test_planted_expr_nomatrix_expression_without_matrix(tmp_path):
    # [A:expr-nomatrix] python-version is `${{ matrix.python-version }}` but the job has no matrix
    _must_fail(
        tmp_path,
        "has no strategy.matrix",
        edit=_add_job("m", _job(_setup("${{ matrix.python-version }}"))),
    )


def test_planted_matrix_key_matrix_without_python_version(tmp_path):
    # [A:matrix-key] a non-empty matrix without a python-version key must not satisfy the expression
    job = _job(_setup("${{ matrix.python-version }}"), strategy={"matrix": {"os": ["a", "b"]}})
    _must_fail(tmp_path, "no python-version key", edit=_add_job("m", job))


def test_planted_expr_unresolvable_expression(tmp_path):
    # [A:expr-unresolvable] any other `${{ }}` value
    job = _job(_setup("${{ vars.PY }}"), strategy={"matrix": {"python-version": ["3.13"]}})
    _must_fail(tmp_path, "cannot resolve the expression", edit=_add_job("m", job))


def test_planted_matrix_expr_matrix_given_as_expression(tmp_path):
    # [A:matrix-expr] `matrix: ${{ fromJSON(...) }}`
    job = _job({"run": "true"}, strategy={"matrix": "${{ fromJSON(needs.x.outputs.m) }}"})
    _must_fail(tmp_path, "is not a mapping", edit=_add_job("m", job))


def test_planted_ver_unreadable_version(tmp_path):
    # [A:ver] a python-version that is no MAJOR.MINOR
    _must_fail(tmp_path, "cannot read a MAJOR.MINOR", edit=_add_job("m", _job(_setup("latest"))))


def test_planted_float_unquoted_yaml_version(tmp_path):
    # [A:float] `python-version: 3.10` is the float 3.1: fail with "quote the version"
    pyproject, ci = _tree(tmp_path)
    ci.write_text(ci.read_text().replace('python-version: "3.12"', "python-version: 3.10"))
    with pytest.raises(AssertionError, match="quote the version"):
        check_agreement(pyproject, ci)


def test_planted_float_in_matrix(tmp_path):
    # [A:float] the same inside a matrix list
    ci_edit = _add_job(
        "m", _job({"run": "true"}, strategy={"matrix": {"python-version": [3.10, "3.13"]}})
    )
    _must_fail(tmp_path, "quote the version", edit=ci_edit)


@pytest.mark.parametrize("where", ["workflow", "job", "step"])
@pytest.mark.parametrize("key", ["UV_PYTHON", "PYTHON_VERSION"])
def test_planted_below_env_pin(tmp_path, where, key):
    # [A:below] UV_PYTHON / PYTHON_VERSION at workflow, job or step level
    def edit(doc):
        if where == "workflow":
            doc["env"][key] = "3.11"
        elif where == "job":
            doc["jobs"]["security"]["env"] = {key: "3.11"}
        else:
            doc["jobs"]["security"]["steps"][-1]["env"] = {key: "3.11"}

    _must_fail(tmp_path, "below requires-python", edit=edit)


def test_planted_expr_unresolvable_env_expression(tmp_path):
    # [A:expr-unresolvable] env pin that is an unresolvable expression
    _must_fail(
        tmp_path,
        "cannot resolve the expression",
        edit=lambda d: d["env"].update({"UV_PYTHON": "${{ vars.P }}"}),
    )


@pytest.mark.parametrize(
    "run",
    [
        "uv run --python 3.11 pytest",
        "uvx --python=3.11 ruff check",
        "uv python install 3.11",
        "uv python install 3.12 3.11",
        "uv python pin 3.11",
        "uv venv \\\n  --python 3.11 .venv",
        "echo hi && uv sync --python 3.11",
    ],
)
def test_planted_below_run_text_pin(tmp_path, run):
    # [A:below] a floor-breaking pin in `run:` text
    _must_fail(tmp_path, "below requires-python", edit=_add_job("r", _job({"run": run})))


def test_planted_ver_run_text_unreadable(tmp_path):
    # [A:ver] `--python "$PY"` cannot be read
    _must_fail(
        tmp_path,
        "cannot read a MAJOR.MINOR",
        edit=_add_job("r", _job({"run": 'uv run --python "$PY" t'})),
    )


def test_run_text_without_a_python_flag_is_not_a_pin(tmp_path):
    run = "uv run pytest -p no:cacheprovider --python-preference only-system\nuv python list"
    check_agreement(*_tree(tmp_path, edit=_add_job("r", _job({"run": run}))))


def test_run_text_pin_at_or_above_the_floor_passes(tmp_path):
    run = "uv run --python 3.13 pytest && uv python install 3.12 3.13"
    check_agreement(*_tree(tmp_path, edit=_add_job("r", _job({"run": run}))))


def test_planted_below_python_version_file_tool_versions(tmp_path):
    # [A:below] python-version-file followed to a .tool-versions whose python line says 3.11
    step = {
        "uses": "actions/setup-python@v5",
        "with": {"python-version-file": ".tool-versions"},
    }
    _must_fail(
        tmp_path,
        "below requires-python",
        edit=_add_job("f", _job(step)),
        files={".tool-versions": "nodejs 20\npython 3.11.4\n"},
    )


def test_python_version_file_pyproject_is_the_floor_and_passes(tmp_path):
    step = {"uses": "actions/setup-python@v5", "with": {"python-version-file": "pyproject.toml"}}
    check_agreement(*_tree(tmp_path, edit=_add_job("f", _job(step))))


def test_planted_file_missing_python_version_file(tmp_path):
    # [A:file-missing] the followed file does not exist
    step = {"uses": "actions/setup-python@v5", "with": {"python-version-file": ".python-version"}}
    _must_fail(tmp_path, "not a file of this repository", edit=_add_job("f", _job(step)))


def test_planted_file_unsupported_python_version_file(tmp_path):
    # [A:file-unsupported] a file kind this test cannot read
    step = {"uses": "actions/setup-python@v5", "with": {"python-version-file": "py.txt"}}
    _must_fail(
        tmp_path, "unsupported file", edit=_add_job("f", _job(step)), files={"py.txt": "3.11"}
    )


def test_planted_file_empty_python_version_file(tmp_path):
    # [A:file-empty] a followed file with no version
    step = {"uses": "actions/setup-python@v5", "with": {"python-version-file": ".python-version"}}
    _must_fail(
        tmp_path,
        "names no python version",
        edit=_add_job("f", _job(step)),
        files={".python-version": "# x\n"},
    )


def test_planted_file_expr_python_version_file_expression(tmp_path):
    # [A:file-expr] the file name is an expression
    step = {"uses": "actions/setup-python@v5", "with": {"python-version-file": "${{ matrix.f }}"}}
    _must_fail(tmp_path, "is an expression", edit=_add_job("f", _job(step)))


@pytest.mark.parametrize("kind", ["container-str", "container-image", "service", "docker-step"])
def test_planted_below_python_image(tmp_path, kind):
    # [A:below] a python:3.11 image as job container, container.image, service, or docker:// step
    job = _job({"run": "true"})
    if kind == "container-str":
        job["container"] = "python:3.11-slim"
    elif kind == "container-image":
        job["container"] = {"image": "docker.io/library/python:3.11.4-bookworm"}
    elif kind == "service":
        job["services"] = {"x": {"image": "python:3.11"}}
    else:
        job["steps"] = [{"uses": "docker://python:3.11"}]
    _must_fail(tmp_path, "below requires-python", edit=_add_job("img", job))


def test_planted_image_tag_unreadable_python_image(tmp_path):
    # [A:image-tag] python:latest names no version
    _must_fail(
        tmp_path,
        "from the image",
        edit=_add_job("i", _job({"run": "t"}, container="python:latest")),
    )


def test_planted_image_expr_python_image_expression(tmp_path):
    # [A:image-expr] a python image with an expression
    _must_fail(
        tmp_path,
        "cannot resolve the image",
        edit=_add_job("i", _job({"run": "t"}, container="python:${{ vars.v }}")),
    )


def test_other_images_are_not_pins(tmp_path):
    check_agreement(*_tree(tmp_path, edit=_add_job("i", _job({"run": "t"}, container="node:20"))))


def test_planted_below_root_python_version_file(tmp_path):
    # [A:below] a repo-root .python-version below the floor
    _must_fail(tmp_path, "below requires-python", files={".python-version": "3.11\n"})


def test_planted_main_highest_root_python_version_file(tmp_path):
    # [A:main-highest] a repo-root .python-version above the main job
    _must_fail(tmp_path, "is not the main job's", files={".python-version": "cpython-3.14.0\n"})


def test_root_python_version_file_at_floor_passes(tmp_path):
    check_agreement(*_tree(tmp_path, files={".python-version": "3.12\n"}))


@pytest.mark.parametrize("name", ["other.yml", "other.yaml"])
def test_planted_below_other_workflow_file(tmp_path, name):
    # [A:below] another workflow file under .github/workflows pins 3.11
    other = yaml.safe_dump({"on": "push", "jobs": {"x": _job(_setup("3.11"))}})
    _must_fail(tmp_path, "below requires-python", files={f".github/workflows/{name}": other})


def test_planted_below_other_workflow_env(tmp_path):
    # [A:below] workflow-level env of another workflow file
    other = yaml.safe_dump(
        {"on": "push", "env": {"UV_PYTHON": "3.11"}, "jobs": {"x": _job({"run": "t"})}}
    )
    _must_fail(tmp_path, "below requires-python", files={".github/workflows/o.yml": other})


def test_planted_below_composite_action(tmp_path):
    # [A:below] a composite action under .github/actions pins 3.11 in a run step
    action = yaml.safe_dump(
        {
            "runs": {
                "using": "composite",
                "steps": [{"run": "uv run --python 3.11 t", "shell": "bash"}],
            }
        }
    )
    _must_fail(tmp_path, "below requires-python", files={".github/actions/x/action.yml": action})


def test_composite_action_input_default_is_resolved(tmp_path):
    def action(default):
        step = {"uses": "astral-sh/setup-uv@v1", "with": {"python-version": "${{ inputs.py }}"}}
        return yaml.safe_dump(
            {
                "inputs": {"py": {"default": default}},
                "runs": {"using": "composite", "steps": [step]},
            }
        )

    path = ".github/actions/x/action.yml"
    check_agreement(*_tree(tmp_path / "ok", files={path: action("3.13")}))
    _must_fail(tmp_path / "bad", "below requires-python", files={path: action("3.11")})


def test_planted_above_requires_python_upper_bound(tmp_path):
    # [A:above] `>=3.12,<3.13` with a 3.13 job
    _must_fail(tmp_path, "at or above the requires-python bound", requires=">=3.12,<3.13")


def test_requires_python_upper_bound_above_every_ci_version_passes(tmp_path):
    check_agreement(*_tree(tmp_path, requires=">=3.12,<3.14"))


def test_requires_python_patch_floor_keeps_the_minor_floor(tmp_path):
    # `>=3.12.3` is floor 3.12: the 3.12 job still agrees
    pyproject, ci = _tree(tmp_path, requires=">=3.12.3")
    assert requires_floor(pyproject) == (3, 12)
    check_agreement(pyproject, ci)


def test_planted_empty_python_version(tmp_path):
    # [A:empty] an empty python-version value
    _must_fail(tmp_path, "empty python version", edit=_add_job("m", _job(_setup(""))))


def test_planted_one_lower_two_lower_bounds(tmp_path):
    # [A:one-lower] requires-python with two lower bounds is ambiguous
    _must_fail(tmp_path, "cannot read one lower bound", requires=">=3.11,>=3.12")


def test_planted_one_upper_two_upper_bounds(tmp_path):
    # [A:one-upper] requires-python with two upper bounds is ambiguous
    _must_fail(tmp_path, "more than one upper bound", requires=">=3.12,<3.14,<3.15")
