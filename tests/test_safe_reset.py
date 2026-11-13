"""The safe reset deletes the working files of a demo and nothing else. Made-up data only: every test works inside
its own temporary folder and never names a path outside it (the files it must keep are made there too).

Rows: dry run is the default; apply deletes only the named files; every path escape is refused before anything is
deleted; a live or unreadable process id file refuses; a stale or ended one is cleaned; a held or untestable lock
refuses and none is created; an answering port refuses; only the first stage (demo) may be reset; a missing or bad
config refuses; the shell wrapper passes exit codes through; the PowerShell wrapper is checked as text (it cannot run
here); a seeded fuzz never touches a file outside the data folder; ``confined`` answers a refusal, not a crash."""

import fcntl
import io
import os
import random
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import safe_reset
from hadavin_sdk.config import ConfigError, confined
from hadavin_sdk.safe_reset import (
    EXIT_CONFIG,
    EXIT_LOCK,
    EXIT_OK,
    EXIT_PID,
    EXIT_PORT,
    EXIT_STAGE,
    load_reset_config,
    run_reset,
)

ROOT = Path(__file__).resolve().parents[1]
KEEP = "keep me"


class World:
    """A temp folder with a data folder, an outside folder and a config writer."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.data = base / "data"
        self.data.mkdir()
        self.outside = base / "outside"
        self.outside.mkdir()
        self.config = base / "reset.yaml"
        self.spec: dict = {"stage": "demo", "data_dir": "data"}

    def file(self, name: str, folder: Path | None = None) -> Path:
        path = (folder or self.data) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(KEEP, encoding="utf-8")
        return path

    def write(self, **spec: object) -> Path:
        self.spec.update(spec)
        self.config.write_text(yaml.safe_dump(self.spec), encoding="utf-8")
        return self.config

    def run(self, apply: bool = False, **spec: object) -> tuple[int, str]:
        out = io.StringIO()
        code = run_reset(self.write(**spec), apply=apply, out=out)
        return code, out.getvalue()

    def kept(self, *paths: Path) -> bool:
        return all(p.exists() and p.read_text(encoding="utf-8") == KEEP for p in paths)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


# -- dry run and apply
def test_a_dry_run_is_the_default_and_deletes_nothing(world: World) -> None:
    db = world.file("app.db")
    code, out = world.run(delete=["app.db"])
    assert code == EXIT_OK and "would delete app.db" in out, out
    assert db.exists(), "the dry run deleted a file"


def test_apply_deletes_only_the_named_files_and_says_so(world: World) -> None:
    db, log, other = world.file("app.db"), world.file("sub/app.log"), world.file("other.txt")
    outside = world.file("o.txt", world.outside)
    code, out = world.run(apply=True, delete=["app.db", "sub/app.log", "gone.log"])
    assert code == EXIT_OK and "reset done" in out, out
    assert not db.exists() and not log.exists(), "a named file was not deleted"
    assert "reset: delete app.db" in out and "reset: absent gone.log" in out
    assert world.kept(other, outside), "a file that was not named was deleted"
    assert KEEP not in out and str(world.base) not in out, (
        "the audit line shows a content or a full path"
    )


# -- path escapes: nothing at all is deleted when any entry escapes
ESCAPES = [
    "../outside/o.txt",
    "sub/../../outside/o.txt",
    "./../outside/o.txt",
    "/etc/hostname",
    "..",
    ".",
    "a\0b",
]


def test_a_path_that_leaves_the_data_folder_is_refused_and_nothing_is_deleted(world: World) -> None:
    db = world.file("app.db")
    outside = world.file("o.txt", world.outside)
    for entry in ESCAPES:
        code, out = world.run(apply=True, delete=["app.db", entry])
        assert code == EXIT_CONFIG and "refused" in out, f"escape was accepted: {entry!r}: {out}"
        assert world.kept(db, outside), "a file was deleted although a path escaped"


def test_a_symlink_that_points_out_of_the_data_folder_is_refused(world: World) -> None:
    outside = world.file("o.txt", world.outside)
    (world.data / "link.txt").symlink_to(outside)
    (world.data / "dirlink").symlink_to(world.outside, target_is_directory=True)
    for entry in ("link.txt", "dirlink/o.txt"):
        code, out = world.run(apply=True, delete=[entry])
        assert code == EXIT_CONFIG, f"escape was accepted: {entry}: {out}"
    assert world.kept(outside)


def test_a_symlink_loop_inside_the_data_folder_is_no_crash_and_only_the_link_goes(
    world: World,
) -> None:
    """Python 3.13 resolves a loop to the link's own place (older versions raise); either way the answer is a refusal
    or the deletion of that one link, never a crash and never another file."""
    keep = world.file("keep.txt")
    (world.data / "loop").symlink_to("loop")
    code, _ = world.run(apply=True, delete=["loop"])
    assert code in (EXIT_OK, EXIT_CONFIG) and world.kept(keep)
    assert code == EXIT_CONFIG or not os.path.lexists(world.data / "loop")


def test_a_folder_is_never_deleted(world: World) -> None:
    (world.data / "sub").mkdir()
    inner = world.file("sub/x.txt")
    code, out = world.run(apply=True, delete=["sub"])
    assert code == EXIT_CONFIG and "only files" in out, out
    assert world.kept(inner)


def test_the_data_folder_itself_is_never_a_target(world: World) -> None:
    keep = world.file("app.db")
    code, out = world.run(apply=True, delete=["."])
    assert code == EXIT_CONFIG and "data folder itself" in out, (
        f"the data folder itself was not refused as such: {out}"
    )
    assert world.kept(keep)


def test_a_data_folder_that_is_a_root_or_home_is_refused(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    code, out = world.run(data_dir="/", delete=["x"])
    assert code == EXIT_CONFIG and "root or a home" in out, f"a root folder was accepted: {out}"
    monkeypatch.setenv(
        "HOME", str(world.base)
    )  # the home folder is now the folder that holds the data folder
    code, out = world.run(data_dir=str(world.base), delete=["x"])
    assert code == EXIT_CONFIG and "root or a home" in out, f"a home folder was accepted: {out}"
    (world.data / "me").mkdir()
    monkeypatch.setenv("HOME", str(world.data / "me"))  # now the data folder is a folder ABOVE home
    code, out = world.run(data_dir="data", delete=["x"])
    assert code == EXIT_CONFIG and "root or a home" in out, (
        f"a folder above home was accepted: {out}"
    )


# -- process id files
def sleeper() -> subprocess.Popen[bytes]:
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])


def test_a_live_process_in_a_pid_file_refuses_and_nothing_is_deleted(world: World) -> None:
    db = world.file("app.db")
    child = sleeper()
    try:
        pidfile = world.data / "app.pid"
        pidfile.write_text(str(child.pid), encoding="utf-8")
        code, out = world.run(apply=True, delete=["app.db"], pid_files=["app.pid"])
        assert code == EXIT_PID and "still running" in out, f"a live process did not refuse: {out}"
        assert world.kept(db) and pidfile.exists(), "a file was deleted under a live process"
        assert child.poll() is None, "the reset stopped a process (it must never do that)"
    finally:
        child.kill()
        child.wait()


def test_a_stale_pid_file_is_cleaned_with_the_rest(world: World) -> None:
    child = sleeper()
    child.kill()
    child.wait()  # ended and collected: the number is free
    db = world.file("app.db")
    pidfile = world.data / "app.pid"
    pidfile.write_text(str(child.pid), encoding="utf-8")
    code, out = world.run(apply=True, delete=["app.db"], pid_files=["app.pid"])
    assert code == EXIT_OK, out
    assert not db.exists() and not pidfile.exists(), "the stale pid file was not cleaned"


@pytest.mark.skipif(
    sys.platform == "win32", reason="an ended but uncollected process is a POSIX state"
)
def test_an_ended_but_uncollected_process_counts_as_gone(world: World) -> None:
    ended = subprocess.Popen([sys.executable, "-c", "pass"])

    def zombie() -> bool:
        return safe_reset._state(ended.pid) == "Z"

    for _ in range(200):
        if zombie():
            break
        subprocess.run(["sleep", "0.05"], check=False)  # noqa: S607
    try:
        assert zombie(), "the test child did not become a zombie"
        assert safe_reset.process_alive(ended.pid) is False, (
            "a zombie was taken for a running process"
        )
    finally:
        ended.wait()


@pytest.mark.parametrize(
    "text", ["", "abc", "12 34", "-1", "1.5", "0", "00", "1" * 11, "\x00", "$(touch x)"]
)
def test_a_pid_file_that_does_not_hold_one_number_refuses(world: World, text: str) -> None:
    db = world.file("app.db")
    (world.data / "app.pid").write_text(text, encoding="utf-8")
    code, out = world.run(apply=True, delete=["app.db"], pid_files=["app.pid"])
    assert code == EXIT_PID and "does not hold one process id" in out, f"{text!r}: {out}"
    assert world.kept(db)


def test_pid_zero_is_refused_before_any_signal_is_sent(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pid 0 would address the caller's whole process group: the number is refused first."""
    monkeypatch.setattr(safe_reset, "process_alive", lambda pid: False)
    (world.data / "app.pid").write_text("0", encoding="utf-8")
    code, out = world.run(apply=True, pid_files=["app.pid"])
    assert code == EXIT_PID and "does not hold one process id" in out, (
        f"pid zero was not refused: {out}"
    )


def test_an_unreadable_pid_file_refuses(world: World) -> None:
    (world.data / "app.pid").mkdir()  # a folder where a file should be: cannot be read
    code, out = world.run(apply=True, pid_files=["app.pid"])
    assert code == EXIT_PID and "cannot be read" in out, out


def test_a_pid_file_path_outside_the_data_folder_is_refused(world: World) -> None:
    code, out = world.run(apply=True, pid_files=["../outside/x.pid"])
    assert code == EXIT_CONFIG and "not inside the data folder" in out, (
        f"a pid file path outside was not refused: {out}"
    )


# -- lock files
def test_a_lock_held_by_another_process_refuses(world: World) -> None:
    db = world.file("app.db")
    lock = world.file("app.db.lock")
    with lock.open("a+b") as holder:
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, out = world.run(apply=True, delete=["app.db"], lock_files=["app.db.lock"])
    assert code == EXIT_LOCK and "holds a lock file" in out, f"a held lock did not refuse: {out}"
    assert world.kept(db)


def test_a_free_lock_file_does_not_refuse_and_a_missing_one_is_not_created(world: World) -> None:
    lock = world.file("app.db.lock")
    code, _ = world.run(
        apply=True, delete=["app.db.lock"], lock_files=["app.db.lock", "never.lock"]
    )
    assert code == EXIT_OK, "a missing lock file refused the reset"
    assert not lock.exists()
    assert not (world.data / "never.lock").exists(), "a refusal or check created a lock file"


def test_a_lock_that_cannot_be_tested_refuses(world: World) -> None:
    db = world.file("app.db")
    (
        world.data / "app.db.lock"
    ).mkdir()  # a folder at the lock path: nothing says that no process holds it
    code, out = world.run(apply=True, delete=["app.db"], lock_files=["app.db.lock"])
    assert code == EXIT_LOCK and "cannot be tested" in out, (
        f"an untestable lock did not refuse: {out}"
    )
    assert world.kept(db)


# -- ports
def test_a_port_that_answers_refuses(world: World) -> None:
    db = world.file("app.db")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        code, out = world.run(apply=True, delete=["app.db"], ports=[free_port(), port])
    assert code == EXIT_PORT and f"port {port}" in out, f"an answering port did not refuse: {out}"
    assert world.kept(db)


def test_a_port_that_does_not_answer_is_fine(world: World) -> None:
    world.file("app.db")
    code, _ = world.run(apply=True, delete=["app.db"], ports=[free_port()])
    assert code == EXIT_OK


# -- stage
def test_only_the_demo_stage_may_be_reset(world: World) -> None:
    db = world.file("app.db")
    for stage in ("pilot", "prod"):
        code, out = world.run(apply=True, stage=stage, delete=["app.db"])
        assert code == EXIT_STAGE and "only demo" in out, f"{stage} was reset: {out}"
        assert world.kept(db)


def test_a_value_that_is_not_a_stage_is_refused_as_a_config_error(world: World) -> None:
    db = world.file("app.db")
    for stage in ("dev", "Demo", "DEMO", " demo", "staging", "", "uat"):
        code, _ = world.run(apply=True, stage=stage, delete=["app.db"])
        assert code == EXIT_CONFIG, f"{stage!r} was accepted as a stage"
        assert world.kept(db)


def test_the_stage_is_required(world: World) -> None:
    world.write()
    spec = yaml.safe_load(world.config.read_text(encoding="utf-8"))
    del spec["stage"]
    world.config.write_text(yaml.safe_dump(spec), encoding="utf-8")
    assert run_reset(world.config, apply=True, out=io.StringIO()) == EXIT_CONFIG


# -- config
def test_no_config_at_all_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(safe_reset.CONFIG_ENV, raising=False)
    out = io.StringIO()
    assert (
        run_reset(None, apply=True, out=out) == EXIT_CONFIG and "no config given" in out.getvalue()
    )


def test_the_config_may_come_from_the_environment(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    world.write(delete=["app.db"])
    db = world.file("app.db")
    monkeypatch.setenv(safe_reset.CONFIG_ENV, str(world.config))
    assert run_reset(None, apply=True, out=io.StringIO()) == EXIT_OK and not db.exists()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "- a\n- b\n",
        "stage: [",
        "stage: demo\n",
        "stage: demo\ndata_dir: nowhere\n",
    ],
)
def test_a_missing_or_bad_config_refuses(world: World, text: str) -> None:
    keep = world.file("app.db")
    world.config.write_text(text, encoding="utf-8")
    out = io.StringIO()
    assert run_reset(world.config, apply=True, out=out) == EXIT_CONFIG, out.getvalue()
    assert "nothing was deleted" in out.getvalue() and world.kept(keep)


def test_an_unknown_config_key_refuses(world: World) -> None:
    keep = world.file("app.db")
    world.config.write_text("stage: demo\ndata_dir: data\nsurprise: 1\n", encoding="utf-8")
    out = io.StringIO()
    code = run_reset(world.config, apply=True, out=out)
    assert code == EXIT_CONFIG, f"an unknown key was ignored: {out.getvalue()}"
    assert world.kept(keep)


def test_a_config_file_that_does_not_exist_refuses(world: World) -> None:
    assert run_reset(world.base / "none.yaml", apply=True, out=io.StringIO()) == EXIT_CONFIG


def test_an_error_never_shows_a_value_of_the_config(world: World) -> None:
    odd_value = "value-that-must-not-leak"
    world.config.write_text(
        f"stage: demo\ndata_dir: data\nports: [{odd_value}]\n", encoding="utf-8"
    )
    out = io.StringIO()
    run_reset(world.config, apply=True, out=out)
    assert odd_value not in out.getvalue(), "a config value was echoed"


@pytest.mark.parametrize("ports", [[0], [65536], [-1]])
def test_a_port_out_of_range_refuses(world: World, ports: list[int]) -> None:
    assert world.run(ports=ports)[0] == EXIT_CONFIG


def test_the_relative_data_dir_is_relative_to_the_config_file_not_the_working_folder(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = world.file("app.db")
    monkeypatch.chdir(world.outside)
    assert world.run(apply=True, delete=["app.db"])[0] == EXIT_OK and not db.exists()


def test_load_reset_config_returns_the_resolved_data_folder(world: World) -> None:
    world.write()
    cfg, data = load_reset_config(world.config)
    assert cfg.stage == "demo" and data == world.data.resolve()


# -- a refusal in a late check leaves everything in place
def test_a_late_refusal_leaves_every_file(world: World) -> None:
    files = [world.file(n) for n in ("a", "b", "c")]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        code, _ = world.run(apply=True, delete=["a", "b", "c"], ports=[listener.getsockname()[1]])
    assert code == EXIT_PORT and world.kept(*files)


# -- the seeded fuzz: whatever the entries are, nothing outside the data folder changes
def test_fuzzed_entries_never_touch_a_file_outside_the_data_folder(world: World) -> None:
    outside = [world.file(n, world.outside) for n in ("o.txt", "sub/p.txt")]
    (world.data / "link.txt").symlink_to(outside[0])
    (world.data / "dirlink").symlink_to(world.outside, target_is_directory=True)
    parts = [
        "..",
        ".",
        "a",
        "sub",
        "link.txt",
        "dirlink",
        "o.txt",
        "p.txt",
        "",
        "/",
        "outside",
        "data",
        "%2e%2e",
        "..\\..",
    ]
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    for _ in range(300):
        entry = "/".join(rng.choice(parts) for _ in range(rng.randint(1, 5)))
        if rng.random() < 0.15:
            entry = str(world.outside / entry.lstrip("/"))
        world.file("a")
        try:
            code, _ = world.run(apply=True, delete=[entry])
        finally:
            assert world.kept(*outside), (
                f"a file outside the data folder changed for entry {entry!r}"
            )
        assert code in (EXIT_OK, EXIT_CONFIG), entry
        if code == EXIT_OK:
            target = (world.data / entry).resolve()
            assert target.is_relative_to(world.data.resolve()), (
                f"accepted entry resolves outside: {entry!r}"
            )


# -- the wrappers
def wrapper_run(world: World, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HADAVIN_PYTHON": sys.executable}
    return subprocess.run(  # noqa: S603
        ["sh", str(ROOT / "tools" / "reset.sh"), *args],  # noqa: S607
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="the shell wrapper needs sh")
def test_the_shell_wrapper_defaults_to_a_dry_run_and_applies_with_the_flag(world: World) -> None:
    db = world.file("app.db")
    world.write(delete=["app.db"])
    dry = wrapper_run(world, "--config", str(world.config))
    assert dry.returncode == 0 and db.exists() and "would delete" in dry.stdout, (
        dry.stdout,
        dry.stderr,
    )
    done = wrapper_run(world, "--config", str(world.config), "--apply")
    assert done.returncode == 0 and not db.exists(), (done.stdout, done.stderr)


@pytest.mark.skipif(sys.platform == "win32", reason="the shell wrapper needs sh")
def test_the_shell_wrapper_passes_every_exit_code_through(world: World) -> None:
    db = world.file("app.db")
    world.write(stage="prod", delete=["app.db"])
    assert wrapper_run(world, "--config", str(world.config), "--apply").returncode == EXIT_STAGE
    world.write(stage="demo", delete=["../outside/o.txt"])
    assert wrapper_run(world, "--config", str(world.config), "--apply").returncode == EXIT_CONFIG
    assert wrapper_run(world).returncode in (EXIT_CONFIG,)  # no config at all
    assert world.kept(db)


def test_the_module_runs_with_dash_m() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "hadavin_sdk.safe_reset", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0 and "--apply" in done.stdout


def test_the_powershell_wrapper_text_is_checked_because_it_cannot_run_here() -> None:
    """No PowerShell on this machine: a parse-level check of the text. It must pass every argument on, return the
    exit code of the checker, and hold no delete command of its own (all deleting is in the Python module)."""
    text = (ROOT / "tools" / "reset.ps1").read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "-m hadavin_sdk.safe_reset @args" in code, "arguments are not passed on"
    assert "exit $LASTEXITCODE" in code, "the exit code is not returned"
    for word in ("Remove-Item", "rm ", "del ", "Stop-Process", "kill"):
        assert word not in code, f"the wrapper does a job of its own: {word}"
    assert code.count("{") == code.count("}") and code.count("(") == code.count(")")
    assert code.count('"') % 2 == 0 and code.count("'") % 2 == 0
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if pwsh:  # where PowerShell exists, its own parser must accept the file
        script = "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$null,[ref]$e); exit $e.Count"
        parsed = subprocess.run(  # noqa: S603
            [pwsh, "-NoProfile", "-Command", script, str(ROOT / "tools" / "reset.ps1")],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert parsed.returncode == 0, parsed.stdout


def test_the_shell_wrapper_holds_no_delete_command_of_its_own() -> None:
    text = (ROOT / "tools" / "reset.sh").read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "-m hadavin_sdk.safe_reset" in code and '"$@"' in code
    for word in ("rm ", "rmdir", "kill", "find "):
        assert word not in code, f"the wrapper does a job of its own: {word}"


def test_the_module_names_no_demo_or_product(world: World) -> None:
    text = (ROOT / "src" / "hadavin_sdk" / "safe_reset.py").read_text(encoding="utf-8").lower()
    for word in ("lead_desk", "hubspot", "n8n", "desk_", "fakes", "demo_only"):
        assert word not in text, word


# -- confined (the shared choke point this module relies on)
def test_confined_refuses_a_nul_character_as_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cannot be resolved"):
        confined(tmp_path, "a\0b")
