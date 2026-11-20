"""The Python versions CI runs must agree with pyproject's `requires-python`.

CI runs the tests on every supported Python: the required job `check` on the newest (3.13) and the job `tests-py312`
on the oldest. Those are two jobs and not a `strategy.matrix` on purpose (a matrix would rename the required check
"check" and the two jobs differ in steps and env). The rules enforced here:

* the lowest version CI runs is the `requires-python` floor (`>=3.12.3` keeps floor 3.12: only MAJOR.MINOR counts),
  no pin is below it, and when `requires-python` has an upper bound `<X` no CI version is at or above X;
* the highest version CI runs is the one the main job `check` uses. DELIBERATE: an extra, newer pre-release job
  (say a 3.14 canary) fails this test until MAIN_JOB or the assertion is updated by hand: a version that nothing
  required runs on must be a conscious decision, not a drive-by edit.

What is read. The structured parser reads `python-version` inputs (steps, reusable-workflow calls, `strategy.matrix`
and `matrix.include`), `python-version-file` (followed: `.python-version`, `pyproject.toml`, `.tool-versions`),
`UV_PYTHON` / `PYTHON_VERSION` in `env` at workflow, job or step level, `--python X` of `uv`/`uvx` and
`uv python install|pin X` in `run:` text (trailing comments and flags are ignored; a path or shell variable is not a
version and is skipped), `python:X` images (job `container`, `services`, `docker://` steps) and a repo-root
`.python-version` (a local-dev file: it must satisfy the floor but is NOT compared with the highest/main rule).
An unquoted YAML float (`3.10` is read as 3.1) fails with "quote the version"; `3` / `3.x` is an unknown minor and
fails only when its file has no resolvable version at all. A RAW TEXT scan of every file under `.github/` (comment-only
lines skipped) catches any Python version below the floor that stands next to a python-ish marker (`python3.11`,
`python:3.11`, `-p 3.11`, `UV_PYTHON=3.11`, `python=3.11`, image names, ...). NOT seen: reusable-workflow
`workflow_call` input defaults used without `with:`, and versions assembled at run time by shell variables or
`fromJSON` (a `fromJSON` matrix fails loudly; shell variables are unknowable).

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
VALUE_FLAGS = ("--install-dir", "-i", "--mirror", "--pypy-mirror", "--python-preference")
UV_PYTHON_CMD = re.compile(r"\buv\s+python\s+(?:install|pin)\b(?P<args>[^\n;&|]*)")
UNKNOWN_MINOR = re.compile(r"\d+(?:\.[x*])?")  # `3`, `3.x`: a major only
NOT_A_VERSION = re.compile(
    r"[/\\$`~]|^\."
)  # a path or a shell variable, e.g. `.venv/bin/python`, `"$VIRTUAL_ENV"`
RAW_PIN = re.compile(
    r"(?<![A-Za-z0-9])(?P<marker>python|py|pyenv\s+(?:install|local|global|shell)|UV_PYTHON|PYTHON_VERSION|-p|--python)[\s:=/@_-]{0,3}3\.(?P<minor>\d{1,2})(?!\d)",
    re.IGNORECASE,
)
UNKNOWN: list[str] = []  # unknown-minor values met by the current ci_versions() run
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
    out = []
    for t in tokens:
        if UNKNOWN_MINOR.fullmatch(t.strip("'\"")):
            UNKNOWN.append(f"{where}: {t}")
        else:
            out.append(_ver(t))
    return out


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
    found = [
        _ver(m["v"]) for m in UV_PYTHON_FLAG.finditer(text) if not NOT_A_VERSION.search(m["v"])
    ]
    for m in UV_PYTHON_CMD.finditer(text):
        words = m["args"].split("#")[0].split()  # a trailing comment is not an argument
        for i, word in enumerate(words):
            if word.startswith("-") or NOT_A_VERSION.search(word):
                continue
            if i and words[i - 1] in VALUE_FLAGS:
                continue
            found.append(_ver(word))
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
    UNKNOWN.clear()

    count = [0, 0]  # versions added, unknown values seen, in the current file

    def add(key: str, versions: list[tuple[int, int]]) -> None:
        count[0] += len(versions)
        if versions:
            out.setdefault(key, []).extend(versions)

    def end_file(name: str) -> None:
        assert count[0] or len(UNKNOWN) == count[1], (  # [A:unknown-minor]
            f"{name}: {UNKNOWN[count[1] :]} name no minor (3 / 3.x) and the file has no resolvable version"
        )
        count[:] = [0, len(UNKNOWN)]

    files = sorted([*ci.parent.glob("*.yml"), *ci.parent.glob("*.yaml")])
    for wf in files:
        doc = yaml.safe_load(wf.read_text()) or {}
        if not isinstance(doc, dict):
            continue
        prefix = "" if wf.resolve() == ci.resolve() else f"{wf.name}:"
        add(f"{prefix}(workflow env)", _env_pins(doc.get("env"), f"{wf.name} workflow", None))
        for name, job in (doc.get("jobs") or {}).items():
            add(f"{prefix}{name}", _job_pins(job or {}, f"{wf.name}:{name}", root))
        end_file(wf.name)
    actions = root / ".github" / "actions"
    for act in sorted([*actions.glob("**/action.yml"), *actions.glob("**/action.yaml")]):
        doc = yaml.safe_load(act.read_text()) or {}
        inputs = doc.get("inputs") or {}
        where = str(act.relative_to(root))
        pins: list[tuple[int, int]] = []
        for step in (doc.get("runs") or {}).get("steps") or []:
            pins += _step_pins(step, where, root, None, inputs)
        add(where, pins)
        end_file(where)
    pv = root / ".python-version"
    if pv.is_file():
        add(".python-version", _file_pins(".python-version", root, ".python-version"))
    return out


def raw_below_floor(github: Path, floor: tuple[int, int]) -> list[str]:
    """Catch-all: a Python version below the floor next to a python-ish marker anywhere under .github/ (raw text)."""
    problems = []
    for path in sorted(p for p in github.rglob("*") if p.is_file()):
        rel = path.relative_to(github.parent)
        for n, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            code = re.sub(r"\s#.*$", "", line)  # a trailing comment is not CI
            for m in RAW_PIN.finditer(code):
                if (3, int(m["minor"])) < floor:
                    problems.append(
                        f"raw scan: {rel}:{n}: {m[0]!r} names Python 3.{m['minor']}, below the requires-python "
                        f"floor {floor[0]}.{floor[1]} (line: {line.strip()!r})"
                    )
    return problems


def check_agreement(pyproject: Path, ci: Path) -> None:
    floor = requires_floor(pyproject)
    ceiling = requires_ceiling(pyproject)
    versions = ci_versions(ci, pyproject.parent)
    assert MAIN_JOB in versions, f"job {MAIN_JOB!r} pins no python-version"  # [A:no-main]
    # a committed .python-version is a local-dev file: it must satisfy the floor, nothing else is compared with it
    everything = [v for k, vs in versions.items() if k != ".python-version" for v in vs]
    below = {job: vs for job, vs in versions.items() if min(vs) < floor}
    assert not below, f"jobs pin a Python below requires-python {floor}: {below}"  # [A:below]
    if ceiling:
        above = {job: vs for job, vs in versions.items() if max(vs) >= ceiling}
        assert not above, (
            f"jobs pin a Python at or above the requires-python bound <{ceiling}: {above}"
        )  # [A:above]
    raw = raw_below_floor(pyproject.parent / ".github", floor)
    assert not raw, "\n".join(raw)  # [A:raw-below]
    assert min(everything) == floor, (  # [A:floor]
        f"lowest CI Python {min(everything)} != requires-python floor {floor}"
    )
    assert max(everything) == max(versions[MAIN_JOB]), (  # [A:main-highest]
        f"highest CI Python {max(everything)} is not the main job's {max(versions[MAIN_JOB])}"
    )


# Derived from the real files so that raising the floor or the main version does not break the planted tests.
FLOOR = requires_floor(ROOT / "pyproject.toml")
TOP = max(ci_versions(ROOT / ".github" / "workflows" / "ci.yml", ROOT)[MAIN_JOB])
FLOOR_S, ABOVE_FLOOR_S = f"{FLOOR[0]}.{FLOOR[1]}", f"{FLOOR[0]}.{FLOOR[1] + 1}"
TOP_S, ABOVE_TOP_S = f"{TOP[0]}.{TOP[1]}", f"{TOP[0]}.{TOP[1] + 1}"


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
        text, n = re.subn(r'(?m)^requires-python = ".*"$', f'requires-python = "{requires}"', text)
        assert n == 1
    pyproject.write_text(text)
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    if ci_floor:
        assert f'python-version: "{FLOOR_S}"' in ci_text
        ci_text = ci_text.replace(f'python-version: "{FLOOR_S}"', f'python-version: "{ci_floor}"')
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
        check_agreement(*_copy(tmp_path, requires=f">={ABOVE_FLOOR_S}"))
    except AssertionError as exc:
        assert "below requires-python" in str(exc)
    else:
        raise AssertionError("CI on the floor passed against a raised requires-python")


def test_ci_floor_above_requires_python_fails(tmp_path):
    try:
        check_agreement(*_copy(tmp_path, ci_floor=ABOVE_FLOOR_S))
    except AssertionError as exc:
        assert "lowest CI Python" in str(exc)
    else:
        raise AssertionError("CI starting above the floor passed against requires-python")


def test_planted_floor_ci_never_reaches_the_floor(tmp_path):
    # [A:floor] lowest CI Python above the floor (the pre-existing case, here with a requires-python of 3.11)
    _must_fail(tmp_path, "lowest CI Python", requires=">=3.11")


def _setup_step(job: dict) -> dict:
    """The step of `job` with a python-version input, found by key and not by position."""
    return next(st for st in job["steps"] if "python-version" in (st.get("with") or {}))


def _swap_main_and_oldest(doc):
    main = _setup_step(doc["jobs"][MAIN_JOB])["with"]
    oldest = next(
        _setup_step(j)["with"]
        for n, j in doc["jobs"].items()
        if n != MAIN_JOB
        and any(
            str(st.get("with", {}).get("python-version")) == FLOOR_S for st in j.get("steps", [])
        )
    )
    main["python-version"], oldest["python-version"] = (
        oldest["python-version"],
        main["python-version"],
    )


def test_planted_main_highest_check_on_312_while_tests_on_313(tmp_path):
    # [A:main-highest] the main job on the floor while the oldest job is on the main version
    _must_fail(tmp_path, "is not the main job's", edit=_swap_main_and_oldest)


def test_planted_main_highest_extra_job_on_314(tmp_path):
    # [A:main-highest] an extra job pinned above the main job
    _must_fail(
        tmp_path, "is not the main job's", edit=_add_job("canary", _job(_setup(ABOVE_TOP_S)))
    )


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
        strategy={"matrix": {"python-version": [FLOOR_S, TOP_S]}},
    )
    pyproject, ci = _tree(tmp_path, edit=_add_job("m", job))
    check_agreement(pyproject, ci)
    assert ci_versions(ci, tmp_path)["m"] == [FLOOR, TOP]


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
    ci.write_text(ci.read_text().replace(f'python-version: "{FLOOR_S}"', "python-version: 3.10"))
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
            doc["jobs"][MAIN_JOB]["env"] = {key: "3.11"}
        else:
            _setup_step(doc["jobs"][MAIN_JOB])["env"] = {key: "3.11"}

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
    # [A:ver] `--python latest` is a word, not a version, a path or a variable
    _must_fail(
        tmp_path,
        "cannot read a MAJOR.MINOR",
        edit=_add_job("r", _job({"run": "uv run --python latest t"})),
    )


@pytest.mark.parametrize(
    "run",
    [
        "uv run --python .venv/bin/python pytest",
        'uv pip install --python "$VIRTUAL_ENV" x',
        "uv pip install --python $VIRTUAL_ENV/bin/python x",
        "uvx --python=/usr/bin/python3 ruff",
        "uv python install 3.12 # why not 3.11",
        "uv python install 3.12 --install-dir /opt",
        "uv python install --install-dir /opt 3.12",
        "uv python install --install-dir opt 3.12",
    ],
)
def test_run_text_paths_variables_comments_and_flags_are_not_versions(tmp_path, run):
    run = run.replace("3.12", FLOOR_S)
    check_agreement(*_tree(tmp_path, edit=_add_job("r", _job({"run": run}))))


@pytest.mark.parametrize("unknown", ["3", "3.x"])
def test_unknown_minor_is_skipped_when_the_file_has_a_resolvable_version(tmp_path, unknown):
    check_agreement(*_tree(tmp_path, edit=_add_job("m", _job(_setup(unknown)))))


@pytest.mark.parametrize("unknown", ["3", "3.x"])
def test_planted_unknown_minor_only(tmp_path, unknown):
    # [A:unknown-minor] a workflow file whose only python pin is `3` / `3.x` resolves to no version
    other = yaml.safe_dump({"on": "push", "jobs": {"x": _job(_setup(unknown))}})
    _must_fail(tmp_path, "no resolvable version", files={".github/workflows/o.yml": other})


def test_run_text_without_a_python_flag_is_not_a_pin(tmp_path):
    run = "uv run pytest -p no:cacheprovider --python-preference only-system\nuv python list"
    check_agreement(*_tree(tmp_path, edit=_add_job("r", _job({"run": run}))))


def test_run_text_pin_at_or_above_the_floor_passes(tmp_path):
    run = f"uv run --python {TOP_S} pytest && uv python install {FLOOR_S} {TOP_S}"
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


def test_root_python_version_file_above_main_is_not_compared(tmp_path):
    # a repo-root .python-version is local-dev: above the main job is NOT compared (the floor still applies, see above)
    check_agreement(*_tree(tmp_path, files={".python-version": f"cpython-{ABOVE_TOP_S}.0\n"}))


def test_root_python_version_file_at_floor_passes(tmp_path):
    check_agreement(*_tree(tmp_path, files={".python-version": f"{FLOOR_S}\n"}))


def test_root_python_version_file_cannot_stand_in_for_the_ci_floor(tmp_path):
    # [A:floor] a .python-version at the floor must not make a CI that never reaches the floor agree
    _must_fail(tmp_path, "lowest CI Python", requires=">=3.11", files={".python-version": "3.11\n"})


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
    check_agreement(*_tree(tmp_path / "ok", files={path: action(TOP_S)}))
    _must_fail(tmp_path / "bad", "below requires-python", files={path: action("3.11")})


def test_planted_above_requires_python_upper_bound(tmp_path):
    # [A:above] an upper bound at the main job's version
    _must_fail(tmp_path, "at or above the requires-python bound", requires=f">={FLOOR_S},<{TOP_S}")


def test_requires_python_upper_bound_above_every_ci_version_passes(tmp_path):
    check_agreement(*_tree(tmp_path, requires=f">={FLOOR_S},<{ABOVE_TOP_S}"))


def test_requires_python_patch_floor_keeps_the_minor_floor(tmp_path):
    # `>=MAJOR.MINOR.3` is the floor MAJOR.MINOR: the job on the floor still agrees
    pyproject, ci = _tree(tmp_path, requires=f">={FLOOR_S}.3")
    assert requires_floor(pyproject) == FLOOR
    check_agreement(pyproject, ci)


def test_planted_empty_python_version(tmp_path):
    # [A:empty] an empty python-version value
    _must_fail(tmp_path, "empty python version", edit=_add_job("m", _job(_setup(""))))


def test_planted_one_lower_two_lower_bounds(tmp_path):
    # [A:one-lower] requires-python with two lower bounds is ambiguous
    _must_fail(tmp_path, "cannot read one lower bound", requires=f">=3.11,>={FLOOR_S}")


def test_planted_one_upper_two_upper_bounds(tmp_path):
    # [A:one-upper] requires-python with two upper bounds is ambiguous
    _must_fail(tmp_path, "more than one upper bound", requires=">=3.12,<3.14,<3.15")


# ---------------------------------------------------------------- the raw text scan (catch-all)

_WF = ".github/workflows/x.yml"
_ACTION = ".github/actions/x/action.yml"


def _workflow(run: str) -> str:
    body = "\n".join(f"          {line}" for line in run.splitlines())
    return f"on: push\njobs:\n  x:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: |\n{body}\n"


RAW_EXAMPLES = [
    ("ghcr.io/astral-sh/uv:python3.11-bookworm", ".github/Dockerfile", "FROM {}\n"),
    ("mirror.gcr.io/library/python:3.11", ".github/Dockerfile", "FROM {}\n"),
    (
        "mcr.microsoft.com/devcontainers/python:3.11",
        ".github/devcontainer.json",
        '{{"image": "{}"}}\n',
    ),
    ("cimg/python:3.11", ".github/ci.yml", "docker:\n  - image: {}\n"),
    ("docker://ghcr.io/x/python:3.11", _WF, None),
    ("docker://python:3.11", _ACTION, "runs:\n  using: docker\n  image: {}\n"),
    ("uv run -p 3.11 pytest", _WF, None),
    ("UV_PYTHON=3.11 uv sync", _WF, None),
    ('echo "UV_PYTHON=3.11" >> $GITHUB_ENV', _WF, None),
    ("docker run python:3.11", _WF, None),
    ("pipx run --python 3.11 tool", _WF, None),
    ("pyenv install 3.11", _WF, None),
    ("conda create -n e python=3.11", _WF, None),
    ("python3.11 -m venv .venv", _WF, None),
    ("see the notes on Python 3.9 below", ".github/notes.md", "{}\n"),
]


def _raw_files(path: str, template: str | None, text: str) -> dict[str, str]:
    return {path: _workflow(text) if template is None else template.format(text)}


@pytest.mark.parametrize("text, path, template", RAW_EXAMPLES, ids=[e[0] for e in RAW_EXAMPLES])
def test_planted_raw_below_floor_text_anywhere_under_github(tmp_path, text, path, template):
    # [A:raw-below] a below-floor version next to a python-ish marker, in a form the structured parser cannot read
    try:
        check_agreement(*_tree(tmp_path, files=_raw_files(path, template, text)))
    except AssertionError as exc:
        message = str(exc)
        assert "raw scan" in message and path in message, message
        assert text in message, message
    else:
        raise AssertionError(f"{text!r} in {path} passed")


def test_raw_scan_names_file_line_and_text(tmp_path):
    files = {".github/x.sh": "set -e\n# python3.11 in a comment\nuv run -p 3.11 pytest\n"}
    with pytest.raises(
        AssertionError, match=r"raw scan: \.github/x\.sh:3: .*uv run -p 3\.11 pytest"
    ):
        check_agreement(*_tree(tmp_path, files=files))


HARMLESS = [
    "uvx --from semgrep==1.181.0 semgrep scan",
    "uv run pytest -p no:cacheprovider",
    "python tools/x.py",
    "image: postgres:17.10",
    "container: node:20",
    "# python3.11 and UV_PYTHON=3.11 in a comment-only line",
    "run: uv run pytest  # was python 3.11 once",
    "name: version 3.13 and 3.12 themselves",
    "image: python:{floor}",
    "UV_PYTHON={top} uv sync",
    "python{floor} -m venv .venv",
    "python-version: {floor}",
    "pip install pytest-3.11x",
]


@pytest.mark.parametrize("line", HARMLESS)
def test_raw_scan_ignores_harmless_text(tmp_path, line):
    line = line.format(floor=FLOOR_S, top=TOP_S)
    files = {".github/notes.txt": line + "\n", ".github/x.sh": line + "\n"}
    assert raw_below_floor(tmp_path, FLOOR) == []
    check_agreement(*_tree(tmp_path, files=files))


def test_raw_scan_passes_on_the_real_github_directory():
    assert raw_below_floor(ROOT / ".github", FLOOR) == []


def test_raw_scan_does_not_fail_on_newer_versions(tmp_path):
    files = {".github/x.sh": f"python{ABOVE_TOP_S} -m venv .venv\nUV_PYTHON={ABOVE_TOP_S}\n"}
    check_agreement(*_tree(tmp_path, files=files))


def test_planted_raw_floor_follows_the_patch_floor(tmp_path):
    # the minor floor logic: `>=FLOOR.3` is still the floor minor, a text one minor below it fails the raw scan
    below = f"{FLOOR[0]}.{FLOOR[1] - 1}"
    files = {".github/x.sh": f"python{below} -m venv\n"}
    with pytest.raises(AssertionError, match="raw scan"):
        check_agreement(*_tree(tmp_path, requires=f">={FLOOR_S}.3", files=files))
    check_agreement(
        *_tree(
            tmp_path / "ok", requires=f">={FLOOR_S}.3", files={".github/x.sh": f"python{FLOOR_S}\n"}
        )
    )
