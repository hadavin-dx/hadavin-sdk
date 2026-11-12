"""Safe reset: wipe the working files of a DEMO, and nothing else.

A demo leaves files behind (a database, its lock file, logs, process-id files). This module deletes exactly the files a
reset config names, and only after every check below passed. It never stops a program, never deletes a folder, and
never touches pilot or prod.

Run it as ``python -m hadavin_sdk.safe_reset --config reset.yaml`` (a dry run: it only says what it would delete) and add
``--apply`` to delete. ``tools/reset.sh`` and ``tools/reset.ps1`` are thin wrappers around that command.

The ONE config (a YAML or JSON file; every relative path in it is relative to the data folder):

    stage: demo                  # must be exactly demo; pilot and prod are refused
    data_dir: ./data             # relative to the config file; the only place anything is deleted
    delete: [app.db, app.log]    # files to delete (names or sub-paths inside data_dir)
    pid_files: [app.pid]         # files holding one process id; a live process refuses the reset
    lock_files: [app.db.lock]    # existing lock files; a lock held by another process refuses the reset
    ports: [8080]                # loopback ports; something answering refuses the reset

Exit codes: 0 done (or dry run complete), 2 config or path refused, 3 lock held or cannot be tested, 4 a port answers,
6 a process id file names a live process or cannot be read, 7 the stage is not demo. Every refusal happens before the
first file is deleted. Output is one audit line per file plus one summary line; no file contents, no secrets.
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import stat
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from hadavin_sdk.config import ConfigError, confined, load_yaml
from hadavin_sdk.stages import STAGES, is_live

__all__ = [
    "EXIT_CONFIG",
    "EXIT_LOCK",
    "EXIT_OK",
    "EXIT_PID",
    "EXIT_PORT",
    "EXIT_STAGE",
    "Refusal",
    "ResetConfig",
    "load_reset_config",
    "main",
    "process_alive",
    "run_reset",
]

EXIT_OK, EXIT_CONFIG, EXIT_LOCK, EXIT_PORT, EXIT_PID, EXIT_STAGE = 0, 2, 3, 4, 6, 7
CONFIG_ENV = "HADAVIN_RESET_CONFIG"
CONNECT_SECONDS = 1.0
LOOPBACK_HOST = "127.0.0.1"  # only this machine is asked; a reset never connects elsewhere
MAX_ENTRIES = 64
_PID = re.compile(r"[0-9]{1,10}")


class Refusal(Exception):
    """Nothing was deleted; ``code`` is the exit code and ``str`` the one-line reason."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class ResetConfig(BaseModel):
    """The reset settings. Strict: an unknown key is refused; errors never echo a value."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    stage: str
    data_dir: Path
    delete: tuple[str, ...] = Field(default=(), max_length=MAX_ENTRIES)
    pid_files: tuple[str, ...] = Field(default=(), max_length=MAX_ENTRIES)
    lock_files: tuple[str, ...] = Field(default=(), max_length=MAX_ENTRIES)
    ports: tuple[int, ...] = Field(default=(), max_length=MAX_ENTRIES)

    @field_validator("stage")
    @classmethod
    def _stage(cls, value: str) -> str:
        if value not in STAGES:
            raise ValueError(f"stage must be one of {', '.join(STAGES)}")
        return value

    @field_validator("delete", "pid_files", "lock_files")
    @classmethod
    def _names(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for v in values:
            if not v or v != v.strip() or "\0" in v:
                raise ValueError("a file name must be non-empty text without edge spaces or NUL")
        return values

    @field_validator("ports")
    @classmethod
    def _ports(cls, values: tuple[int, ...]) -> tuple[int, ...]:
        if any(not 1 <= p <= 65535 for p in values):
            raise ValueError("a port must be from 1 to 65535")
        return values


def load_reset_config(path: str | os.PathLike[str] | None) -> tuple[ResetConfig, Path]:
    """Read and validate the config; returns it with the resolved data folder. Any problem is a ``Refusal`` (2)."""
    chosen = path or os.environ.get(CONFIG_ENV)
    if not chosen:
        raise Refusal(
            EXIT_CONFIG,
            f"refused: no config given (use --config or {CONFIG_ENV}); nothing was deleted",
        )
    file = Path(chosen)
    try:
        raw = load_yaml(file.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigError("expected a mapping at the top level")
        cfg = ResetConfig.model_validate(raw)
    except (OSError, ValueError, ConfigError, ValidationError, TypeError, yaml.YAMLError) as exc:
        # ValidationError and yaml errors are ValueError / ConfigError: the type name only, never the text of a value
        raise Refusal(
            EXIT_CONFIG,
            f"refused: the reset config is missing or not valid ({type(exc).__name__}); nothing was deleted",
        ) from exc
    try:
        data = (file.resolve().parent / cfg.data_dir).resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise Refusal(
            EXIT_CONFIG, "refused: the data folder cannot be resolved; nothing was deleted"
        ) from exc
    if not data.is_dir():
        raise Refusal(EXIT_CONFIG, "refused: the data folder does not exist; nothing was deleted")
    if (
        data == Path(data.anchor)
        or data == Path.home().resolve()
        or data in Path.home().resolve().parents
    ):
        raise Refusal(
            EXIT_CONFIG,
            "refused: the data folder is a filesystem root or a home folder; nothing was deleted",
        )
    return cfg, data


def _inside(data: Path, names: Sequence[str]) -> list[Path]:
    """Every name must resolve (symlinks and ``..`` followed) to a place strictly inside the data folder."""
    out: list[Path] = []
    for name in names:
        try:
            path = confined(data, name)
        except ConfigError as exc:
            raise Refusal(
                EXIT_CONFIG,
                "refused: a configured path is not inside the data folder; nothing was deleted",
            ) from exc
        if path == data:
            raise Refusal(
                EXIT_CONFIG,
                "refused: a configured path is the data folder itself; nothing was deleted",
            )
        out.append(path)
    return out


def process_alive(pid: int) -> bool:
    """True when a process with this id exists and has not ended. A process that has ended but is not yet collected
    by its parent (a zombie) counts as gone."""
    if sys.platform == "win32":
        return _alive_windows(pid)
    try:
        os.kill(
            pid, 0
        )  # signal 0 only tests; pid is a checked positive number, never 0 (a process group)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists, it is only not ours
    return _state(pid) != "Z"


def _state(pid: int) -> str:
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
        return text.rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        pass
    try:
        out = subprocess.run(  # noqa: S603
            ["ps", "-p", str(pid), "-o", "stat="],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "?"
    return out[:1] or "?"


def _alive_windows(pid: int) -> bool:
    try:
        out = subprocess.run(  # noqa: S603
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return True  # cannot tell: refuse
    return f'"{pid}"' in out


def _check_pids(files: Sequence[Path]) -> None:
    for file in files:
        if not os.path.lexists(file):
            continue
        try:
            text = file.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise Refusal(
                EXIT_PID, "refused: a process id file cannot be read; nothing was deleted"
            ) from exc
        if not _PID.fullmatch(text) or int(text) == 0:
            raise Refusal(
                EXIT_PID,
                "refused: a process id file does not hold one process id; nothing was deleted",
            )
        if process_alive(int(text)):
            raise Refusal(
                EXIT_PID,
                "refused: a process listed in a process id file is still running; nothing was deleted",
            )


def _lock_held(file: Path) -> bool:
    """True when another process holds the lock; raises OSError when it cannot be tested. Never creates the file."""
    if sys.platform == "win32":
        import msvcrt

        with file.open("r+b") as f:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                if exc.errno in (13, 36):  # EACCES (locking violation), EDEADLK
                    return True
                raise
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return False
    import fcntl

    fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
    try:
        if not stat.S_ISREG(
            os.fstat(fd).st_mode
        ):  # a folder or a device cannot be a lock: not known, so refuse
            raise OSError("not a regular file")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)  # closing also releases the lock


def _check_locks(files: Sequence[Path]) -> None:
    for file in files:
        if not os.path.lexists(file):
            continue
        try:
            held = _lock_held(file)
        except OSError as exc:
            raise Refusal(
                EXIT_LOCK,
                "refused: a lock file cannot be tested, so it is not known whether the app runs; nothing was deleted",
            ) from exc
        if held:
            raise Refusal(
                EXIT_LOCK,
                "refused: a process still holds a lock file (the app is running); nothing was deleted",
            )


def answers(port: int) -> bool:
    """True when something accepts a connection on this loopback port."""
    try:
        with socket.create_connection((LOOPBACK_HOST, port), timeout=CONNECT_SECONDS):
            return True
    except OSError:
        return False


def _check_ports(ports: Sequence[int]) -> None:
    for port in ports:
        if answers(port):
            raise Refusal(
                EXIT_PORT, f"refused: something still answers on port {port}; nothing was deleted"
            )


def _remove(path: Path, data: Path, out: IO[str], apply: bool) -> None:
    rel = path.relative_to(data).as_posix()
    if not os.path.lexists(path):
        print(f"reset: absent {rel}", file=out)
        return
    print(f"reset: {'delete' if apply else 'would delete'} {rel}", file=out)
    if apply:
        path.unlink()


def run_reset(
    config_path: str | os.PathLike[str] | None, *, apply: bool = False, out: IO[str] | None = None
) -> int:
    """Check everything, then (only with ``apply``) delete. Returns the exit code; never raises for a refusal."""
    out = out or sys.stdout
    try:
        cfg, data = load_reset_config(config_path)
        if is_live(cfg.stage):
            raise Refusal(
                EXIT_STAGE,
                f"refused: stage is {cfg.stage}; only {STAGES[0]} may be reset; nothing was deleted",
            )
        files = _inside(data, cfg.delete)
        pids = _inside(data, cfg.pid_files)
        locks = _inside(data, cfg.lock_files)
        _check_pids(pids)
        _check_locks(locks)
        _check_ports(cfg.ports)
        # a folder in the plan is found before anything is deleted, so a refusal never leaves a half reset
        for path in (*files, *pids):
            if path.is_dir():
                raise Refusal(
                    EXIT_CONFIG,
                    "refused: a configured path is a folder, only files are deleted; nothing was deleted",
                )
        for path in (*files, *pids):
            _remove(path, data, out, apply)
    except Refusal as refusal:
        print(str(refusal), file=out)
        return refusal.code
    print(
        "reset done" if apply else "reset dry run: nothing was deleted (add --apply to delete)",
        file=out,
    )
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hadavin_sdk.safe_reset", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--config", help=f"the reset config file (or set {CONFIG_ENV})")
    parser.add_argument(
        "--apply", action="store_true", help="delete; without it nothing is deleted"
    )
    args = parser.parse_args(argv)
    return run_reset(args.config, apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())
