"""Crash points for tests: stop the program at a named place and look at what is left.

Test-only. Not public API, not exported from any package, not used at run time. A `CrashPoints` object cannot be
built outside a pytest run. A test wraps an object it already hands to the code under test (a store, a model
double) and arms one point named `<name>.<method>:before` or `<name>.<method>:after`. When the wrapped method
reaches that point, mode "raise" raises `SimulatedCrash` in the same process, and mode "exit" ends the process
at once. Mode "exit" is for a child process: the parent arms a flag file, the child reads it. One arm gives one
crash: the point is disarmed (or its flag file deleted) before the crash, and if that fails nothing happens.

Flag file: one line of text, `<point>` or `<point>#<nth>`. A missing, unreadable or malformed file means
"not armed".
"""

from __future__ import annotations

import os
import re
import threading
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any, Final, Literal, cast

CRASH_EXIT_CODE: Final[int] = 137
CRASH_MARKER: Final[str] = "simulate crash"
Mode = Literal["raise", "exit"]

_GATE: Final[str] = "PYTEST_CURRENT_TEST"  # pytest sets it per test; a child process inherits it
_WORD: Final[str] = r"[a-z_][a-z0-9_]{0,59}"
_NAME: Final[re.Pattern[str]] = re.compile(_WORD)
_POINT: Final[re.Pattern[str]] = re.compile(rf"{_WORD}\.{_WORD}:(?:before|after)")
_NTH: Final[re.Pattern[str]] = re.compile(r"[1-9][0-9]{0,8}")
_NTH_LIMIT: Final[int] = 10**9


class SimulatedCrash(BaseException):
    """The same-process crash. A `BaseException` on purpose: code that catches `Exception` to tidy up must not
    catch it, because a real crash tidies nothing up."""

    def __init__(self, point: str) -> None:
        super().__init__(point)
        self.point = point


class _Proxy:
    """Stands in for the target: the listed methods go through the crash points, all else is the target's."""

    __slots__ = ("_crash_calls", "_crash_target")

    def __init__(self, target: object, calls: dict[str, Callable[..., Any]]) -> None:
        self._crash_target = target
        self._crash_calls = calls

    def __getattr__(self, attr: str) -> Any:
        if attr in ("_crash_calls", "_crash_target"):  # only before __init__ ran: never recurse
            raise AttributeError(attr)
        if attr in self._crash_calls:
            return self._crash_calls[attr]
        return getattr(self._crash_target, attr)


class CrashPoints:
    """The set of crash points of one test. Use it in a `with` block: a point still armed at the end is an error."""

    def __init__(self, *, mode: Mode = "raise", flag_path: Path | None = None) -> None:
        if _GATE not in os.environ:
            raise RuntimeError(
                "CrashPoints is a test tool: it can only be built inside a pytest run"
            )
        if mode not in ("raise", "exit"):
            raise ValueError(f"unknown mode: {mode!r}")
        if mode == "exit" and flag_path is None:
            raise ValueError('mode "exit" needs a flag_path')
        if mode == "raise" and flag_path is not None:
            raise ValueError('mode "raise" takes no flag_path')
        self._mode: Mode = mode
        self._flag = flag_path
        self._lock = threading.Lock()
        self._memory: tuple[str, int] | None = None
        self._seen: dict[str, int] = {}
        self._fired: list[str] = []

    def __enter__(self) -> CrashPoints:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        with self._lock:
            left = self._current()
            if left is not None:
                self._take()
        if left is not None and exc_type is None:
            raise RuntimeError(f"crash point left armed, it never fired: {left[0]}")

    @property
    def fired(self) -> tuple[str, ...]:
        """The points that fired in this process, in order."""
        with self._lock:
            return tuple(self._fired)

    def arm(self, point: str, *, nth: int = 1) -> None:
        """Arm one point: its `nth` matching call from now on crashes, once."""
        if not isinstance(point, str) or not _POINT.fullmatch(point):
            raise ValueError(
                "a point is <name>.<method>:before or <name>.<method>:after, lower case"
            )
        if not isinstance(nth, int) or not 1 <= nth < _NTH_LIMIT:
            raise ValueError(f"nth must be 1 or more: {nth!r}")
        with self._lock:
            current = self._current()
            if current is not None:
                raise ValueError(f"already armed: {current[0]}")
            self._seen.clear()
            if self._flag is None:
                self._memory = (point, nth)
            else:
                self._flag.write_text(point if nth == 1 else f"{point}#{nth}", encoding="utf-8")

    def armed(self) -> str | None:
        """The armed point, or None."""
        with self._lock:
            current = self._current()
        return None if current is None else current[0]

    def hit(self, point: str) -> None:
        """Called at a crash point. Does nothing unless exactly this point is armed and this is its nth call."""
        with self._lock:
            current = self._current()
            if current is None or current[0] != point:
                return
            self._seen[point] = self._seen.get(point, 0) + 1
            if self._seen[point] < current[1]:
                return
            if (
                not self._take()
            ):  # disarm BEFORE the crash; if another process took the flag, no crash
                return
            self._fired.append(point)
            if self._mode == "raise":
                raise SimulatedCrash(point)
            print(CRASH_MARKER, flush=True)
            os._exit(CRASH_EXIT_CODE)

    def wrap[T](self, target: T, name: str, methods: Collection[str]) -> T:
        """A stand-in for `target` whose listed methods pass `<name>.<method>:before` and `:after`. Everything
        else, results and exceptions included, is the target's. `AttributeError` if the target lacks a method."""
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError(f"bad name: {name!r}")
        if isinstance(methods, str):
            raise TypeError("methods is a collection of method names, not one string")
        calls: dict[str, Callable[..., Any]] = {}
        for method in methods:
            if not isinstance(method, str) or not _NAME.fullmatch(method):
                raise ValueError(f"bad method name: {method!r}")
            if not callable(getattr(target, method)):
                raise AttributeError(f"{name}.{method} is not a method")
            calls[method] = self._edge(target, name, method)
        return cast(T, _Proxy(target, calls))

    def _edge(self, target: object, name: str, method: str) -> Callable[..., Any]:
        before, after = f"{name}.{method}:before", f"{name}.{method}:after"

        def call(*args: Any, **kwargs: Any) -> Any:
            self.hit(before)
            result = getattr(target, method)(*args, **kwargs)
            self.hit(after)
            return result

        return call

    def _current(self) -> tuple[str, int] | None:
        """The armed point and its nth, from memory or from the flag file. Call with the lock held."""
        if self._flag is None:
            return self._memory
        try:
            text = self._flag.read_text(encoding="utf-8")
        except (OSError, ValueError):
            return None
        point, sep, count = text.removesuffix("\n").partition("#")
        if not _POINT.fullmatch(point) or (sep and not _NTH.fullmatch(count)):
            return None
        return point, int(count) if sep else 1

    def _take(self) -> bool:
        """Disarm. False if a flag file could not be deleted (someone else took it). Call with the lock held."""
        if self._flag is None:
            self._memory = None
            return True
        try:
            self._flag.unlink()
        except OSError:
            return False
        return True
