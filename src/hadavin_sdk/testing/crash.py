"""Crash points for tests: stop the program at a named place and look at what is left.

Test-only. Not public API, not exported from any package, not used at run time. A test wraps an
object it already hands to the code under test (a store, a model double) and arms one point named
`<name>.<method>:before` or `<name>.<method>:after`. When the wrapped method reaches that point,
mode "raise" raises `SimulatedCrash` in the same process, and mode "exit" ends the process at once.
Mode "exit" is for a child process: the parent arms a flag file, the child reads it. One arm gives
one crash: the point is disarmed (or its flag file deleted) before the crash. If the delete is
refused it is tried again; if it still fails nothing fires at that call, and the next matching call
tries again.

Flag file: one line of text, `<point>` or `<point>#<nth>`, written by `arm`. A missing, unreadable
or malformed file means "not armed". A read error (a sharing violation on Windows) means "not armed
this time", and the `nth` count does not advance for that call. Arm before the child starts, one child per case. Counts are never reset in a child: it
counts the matching calls for as long as it lives. On leaving the `with` block a flag that never
fired is deleted; if the delete is refused (Windows can refuse while a reader holds the file open)
it is tried again, 20 times at 20 ms apart, then `RuntimeError` names the path. With an error
already in flight the block reports nothing about a stuck flag and does not replace that error.

What a test must know, or the helper misleads it:

- The gate is a speed bump, not a security control. It is the environment variable
  PYTEST_CURRENT_TEST: a `CrashPoints` refuses to be built outside a test, also at import or
  collection time (pytest sets the variable only while a test runs). A child process inherits the
  variable; a child started with another environment cannot build one.
- Mode "raise": the code under test can catch the crash, or run `finally` blocks that still use the
  working wrapped store (the proxy keeps working after a crash). A real crash tidies nothing up.
  So assert `cp.fired` yourself; a real kill needs mode "exit".
- Exit code 137 is also what a shell reports for a real forced kill (128 + 9). A test of mode
  "exit" asserts the marker line on the child's stdout AND the exit code; the exit code alone
  proves nothing. The marker is written straight to file descriptor 1, so text still buffered in
  `sys.stdout` is lost, as in a real crash. `os.write` emits a bare newline on every platform: read
  the marker with `text=True` and `splitlines()`, never compare raw bytes. If the marker cannot be
  written (a closed stdout), the process still exits with the code, with no marker.
- A flag file left on disk kills the next child that uses the same path. Arm inside a `with` block
  (it deletes a flag that never fired and raises if the file stays), or delete the flag in a
  `finally`.
- The proxy from `wrap` is not transparent: no setattr through it, no `isinstance`, no dunder
  methods (wrap refuses those names). Coroutine, async generator and generator functions are
  refused too: their body runs after the call returns, so `:after` would be wrong. The refusal
  covers function kinds only, not a sync function that returns a coroutine or a generator.
- Only references that go through the proxy are covered. Wrap EVERY reference the code under test
  uses: the runtime keeps its own store reference, so wrapping the test's reference is not enough.
  Two wraps with the same name and method share one point and one nth counter.
- A misspelled point never matches, so in mode "exit" the child simply runs on and a test that only waits for
  the end passes without a crash: an exit-mode test must assert the marker line and the exit code.
- Mode "raise" behind a thread: the test thread sees nothing; poll `cp.fired`.
- `hit` is an extension hook: a caller may subclass `CrashPoints` and override it.
- Mode "raise" behind a worker pool: the crash is stored in the Future and the process lives on.
  Behind the real HTTP server it becomes a 503, not a crash. Use mode "exit" in a child there.
"""

from __future__ import annotations

import functools
import inspect
import os
import re
import threading
import time
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any, Final, Literal, Self, cast

CRASH_EXIT_CODE: Final[int] = 137
CRASH_MARKER: Final[str] = "simulate crash"
Mode = Literal["raise", "exit"]

_GATE: Final[str] = "PYTEST_CURRENT_TEST"  # pytest sets it per test; a child process inherits it
_WORD: Final[str] = r"[a-z_][a-z0-9_]{0,59}"
_NAME: Final[re.Pattern[str]] = re.compile(_WORD)
_POINT: Final[re.Pattern[str]] = re.compile(rf"{_WORD}\.{_WORD}:(?:before|after)")
_NTH: Final[re.Pattern[str]] = re.compile(r"[1-9][0-9]{0,8}")
_NTH_LIMIT: Final[int] = 10**9
_UNLINK_TRIES: Final[int] = 20  # tries to delete the flag file (a refused delete is retried)
_UNLINK_PAUSE_S: Final[float] = 0.02  # pause between two tries


class SimulatedCrash(BaseException):
    """The same-process crash. A `BaseException` on purpose: code that catches `Exception` to tidy
    up must not catch it, because a real crash tidies nothing up."""

    def __init__(self, point: str) -> None:
        super().__init__(point)
        self.point = point


class _Proxy:
    """Stands in for the target: the listed methods go through the crash points, all else is the
    target's."""

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


def _still_there(path: Path) -> bool:
    """Whether the file is still on disk after a delete was refused. An error while asking (Python 3.12 on
    Windows can raise PermissionError) counts as "still there": the delete is refused, and the error must not
    reach the code under test."""
    try:
        return os.path.exists(path)
    except OSError:
        return True


class CrashPoints:
    """The set of crash points of one test. Use it in a `with` block: a point still armed at the
    end is an error."""

    def __init__(
        self,
        *,
        mode: Mode = "raise",
        flag_path: Path | None = None,
    ) -> None:
        if _GATE not in os.environ:
            raise RuntimeError(
                "CrashPoints is a test tool: it can only be built inside a pytest run"
            )
        if mode not in ("raise", "exit"):
            raise ValueError(f"unknown mode: {mode!r}")
        if flag_path is not None and not isinstance(flag_path, Path):
            raise TypeError(f"flag_path is a pathlib.Path, not {type(flag_path).__name__}")
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

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Delete a flag that never fired. With an error already in flight, report nothing."""
        with self._lock:
            left = self._current()
            if left is not None:
                self._disarm()
            stuck = left is not None and self._flag is not None and _still_there(self._flag)
        if exc_type is not None:
            return
        if stuck:
            raise RuntimeError(f"the flag file could not be deleted: {self._flag}")
        if left is not None:
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
        if isinstance(nth, bool):
            raise TypeError(f"nth is a whole number, not a bool: {nth!r}")
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
        """Called at a crash point. Does nothing unless exactly this point is armed and this is its
        nth call. Extension hook: a caller may override it. The flag is deleted first, retried if
        the delete is refused. If it is still refused nothing fires at this call and the next
        matching call tries again; if another process took the flag, nothing fires."""
        with self._lock:
            current = self._current()
            if current is None or current[0] != point:
                return
            self._seen[point] = self._seen.get(point, 0) + 1
            if self._seen[point] < current[1]:
                return
            # Disarm BEFORE the crash. Fire only if our own delete took the flag.
            if not self._disarm():
                return
            self._fired.append(point)
            if self._mode == "raise":
                raise SimulatedCrash(point)
            try:
                # Straight to the descriptor: text still buffered in sys.stdout stays unwritten.
                os.write(1, f"{CRASH_MARKER}\n".encode())
            finally:  # a closed stdout must not turn the crash into an ordinary exception
                os._exit(CRASH_EXIT_CODE)

    def wrap[T](self, target: T, name: str, methods: Collection[str]) -> T:
        """A stand-in for `target` whose listed methods pass `<name>.<method>:before` and `:after`.
        Everything else, results and exceptions included, is the target's. `AttributeError` if the
        target lacks a method, `TypeError` if it is no method, or if it is a coroutine, async
        generator or generator function, or has a dunder name (the proxy cannot sit in front of
        those). The proxy is not transparent: no setattr, no `isinstance`."""
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError(f"bad name: {name!r}")
        if isinstance(methods, str):
            raise TypeError("methods is a collection of method names, not one string")
        calls: dict[str, Callable[..., Any]] = {}
        for method in methods:
            if not isinstance(method, str) or not _NAME.fullmatch(method):
                raise ValueError(f"bad method name: {method!r}")
            if method.startswith("__") and method.endswith("__"):
                raise TypeError(f"{name}.{method}: dunder methods cannot be wrapped")
            func = getattr(target, method)
            if not callable(func):
                raise TypeError(f"{name}.{method} is not a method")
            if (
                inspect.iscoroutinefunction(func)
                or inspect.isasyncgenfunction(func)
                or inspect.isgeneratorfunction(func)
            ):
                raise TypeError(f"{name}.{method}: async and generator methods cannot be wrapped")
            calls[method] = self._edge(target, name, method)
        return cast(T, _Proxy(target, calls))

    def _edge(self, target: object, name: str, method: str) -> Callable[..., Any]:
        before, after = f"{name}.{method}:before", f"{name}.{method}:after"

        @functools.wraps(getattr(target, method))
        def call(*args: Any, **kwargs: Any) -> Any:
            self.hit(before)
            result = getattr(target, method)(*args, **kwargs)
            self.hit(after)
            return result

        return call

    def _current(self) -> tuple[str, int] | None:
        """The armed point and its nth, from memory or from the flag file. Call with the lock
        held."""
        if self._flag is None:
            return self._memory
        try:
            text = self._flag.read_text(encoding="utf-8")
        except (OSError, ValueError):
            text = ""
        point, sep, count = text.removesuffix("\n").partition("#")
        if not _POINT.fullmatch(point) or (sep and not _NTH.fullmatch(count)):
            return None
        return point, int(count) if sep else 1

    def _disarm(self) -> bool:
        """Delete the flag, trying again if the delete is refused. True only if our own delete
        took it; False if another process took it or it stays refused. Call with the lock held."""
        for attempt in range(_UNLINK_TRIES):
            outcome = self._take()
            if outcome != "refused":
                return outcome == "taken"
            if attempt < _UNLINK_TRIES - 1:
                time.sleep(_UNLINK_PAUSE_S)
        return False

    def _take(self) -> Literal["taken", "gone", "refused"]:
        """One try to disarm. "gone": a flag file is already missing (someone else took it).
        "refused": the file is still there after an error. Call with the lock held."""
        if self._flag is None:
            self._memory = None
            return "taken"
        try:
            self._flag.unlink()
        except FileNotFoundError:
            return "gone"
        except OSError:
            return "refused" if _still_there(self._flag) else "gone"
        return "taken"
