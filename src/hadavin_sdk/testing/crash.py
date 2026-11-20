"""Crash points for tests: stop the program at a named place and look at what is left.

Test-only. Not public API, not exported from any package, not used at run time. A `CrashPoints`
object cannot be built outside a pytest run. A test wraps an object it already hands to the code
under test (a store, a model double) and arms one point named `<name>.<method>:before` or
`<name>.<method>:after`. When the wrapped method reaches that point, mode "raise" raises
`SimulatedCrash` in the same process, and mode "exit" ends the process at once. Mode "exit" is for
a child process: the parent arms a flag file, the child reads it. One arm gives one crash: the
point is disarmed (or its flag file deleted) before the crash, and if that fails nothing happens.

Flag file: one line of text, `<point>` or `<point>#<nth>`. A missing, unreadable or malformed file
means "not armed". `arm` writes it through a temp file in the same folder and `os.replace`, so a
reader never sees half a flag. A child counts the matching calls per flag text: when the text it
reads changes (another process armed again), the count starts again.

What a test must know, or the helper misleads it:

- The gate is a speed bump, not a security control. It is the environment variable
  PYTEST_CURRENT_TEST: a `CrashPoints` refuses to be built outside a test, also at import or
  collection time (pytest sets the variable only while a test runs). A child process inherits the
  variable; a child started with another environment cannot build one.
- Exit code 137 is also what a shell reports for a real forced kill (128 + 9). A test of mode
  "exit" asserts the marker line on the child's stdout AND the exit code; the code alone proves
  nothing. The marker is written straight to file descriptor 1, so text still buffered in
  `sys.stdout` is lost, as in a real crash. If the marker cannot be written (a closed stdout), the
  process still exits with the code, with no marker.
- A flag file left on disk kills the next child that uses the same path. Arm inside a `with` block
  (it deletes a flag that never fired and raises if the file stays), or delete the flag in a
  `finally`.
- The proxy from `wrap` is not transparent: no setattr through it, no `isinstance`, no dunder
  methods (wrap refuses those names). Coroutine, async generator and generator methods are refused
  too: their body runs after the call returns, so `:after` would be wrong.
- Mode "raise" behind a worker pool: the crash is stored in the Future and the process lives on.
  Behind the real trigger server it becomes a 503, not a crash. Use mode "exit" in a child there.
- A swallowed crash can let a test pass. With the default, assert `cp.fired` yourself. Opt in with
  `CrashPoints(require_claim=True)`: then `cp.expect_fired(point)` claims a point that fired, and
  leaving the `with` block raises if a point fired and was never claimed. In mode "exit" the child
  fires, not the parent: the parent asks `cp.flag_taken()`.
- A real crash tidies nothing up, but in mode "raise" `finally` blocks run and may still use the
  wrapped object. `CrashPoints(latch=True)` makes every later call through any proxy of that
  object raise `SimulatedCrash` before it touches the target. A reference to the unwrapped object
  escapes the latch. The default is off: tests that go on using the proxy after a crash keep
  working.
"""

from __future__ import annotations

import inspect
import os
import re
import threading
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


class CrashPoints:
    """The set of crash points of one test. Use it in a `with` block: a point still armed at the
    end is an error."""

    def __init__(
        self,
        *,
        mode: Mode = "raise",
        flag_path: Path | None = None,
        latch: bool = False,
        require_claim: bool = False,
    ) -> None:
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
        if latch and mode != "raise":
            raise ValueError('latch is for mode "raise"')
        self._mode: Mode = mode
        self._flag = flag_path
        self._lock = threading.Lock()
        self._memory: tuple[str, int] | None = None
        self._seen: dict[str, int] = {}
        self._fired: list[str] = []
        self._latch = bool(latch)
        self._latched: str | None = None  # set once a raise-mode crash fired and latch is on
        self._require_claim = bool(require_claim)
        self._claimed: set[str] = set()
        self._text: str | None = None  # the flag text the per-process count belongs to
        self._was_armed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        with self._lock:
            left = self._current()
            if left is not None:
                self._take()
            stuck = left is not None and self._flag is not None and self._flag.exists()
        if exc_type is not None:
            return
        if stuck:
            raise RuntimeError(f"the flag file could not be deleted: {self._flag}")
        if left is not None:
            raise RuntimeError(f"crash point left armed, it never fired: {left[0]}")
        if self._require_claim:
            loose = [p for p in dict.fromkeys(self._fired) if p not in self._claimed]
            if loose:
                raise RuntimeError(f"crash point fired and was never claimed: {', '.join(loose)}")

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
            self._was_armed = True
            if self._flag is None:
                self._memory = (point, nth)
            else:
                # Write beside the flag, then swap: a reader sees the old flag or the new, never half.
                temp = self._flag.with_name(f"{self._flag.name}.{os.getpid()}.tmp")
                temp.write_text(point if nth == 1 else f"{point}#{nth}", encoding="utf-8")
                os.replace(temp, self._flag)

    def armed(self) -> str | None:
        """The armed point, or None."""
        with self._lock:
            current = self._current()
        return None if current is None else current[0]

    def hit(self, point: str) -> None:
        """Called at a crash point. Does nothing unless exactly this point is armed and this is its
        nth call."""
        with self._lock:
            current = self._current()
            if current is None or current[0] != point:
                return
            self._seen[point] = self._seen.get(point, 0) + 1
            if self._seen[point] < current[1]:
                return
            # Disarm BEFORE the crash. If the flag could not be deleted, another process took it.
            if not self._take():
                return
            self._fired.append(point)
            if self._mode == "raise":
                if self._latch:
                    self._latched = point
                raise SimulatedCrash(point)
            try:
                # Straight to the descriptor: text still buffered in sys.stdout stays unwritten.
                os.write(1, f"{CRASH_MARKER}\n".encode())
            finally:  # a closed stdout must not turn the crash into an ordinary exception
                os._exit(CRASH_EXIT_CODE)

    def expect_fired(self, point: str) -> None:
        """Claim a point that fired in this process. `RuntimeError` naming the point if it did not
        (a crash that something swallowed, or a call that never happened)."""
        with self._lock:
            if point not in self._fired:
                raise RuntimeError(f"crash point did not fire: {point}")
            self._claimed.add(point)

    def flag_taken(self) -> bool:
        """Mode "exit", in the parent: True once a child took the flag, that is, the flag file armed
        by this object no longer exists. False if nothing was armed yet."""
        if self._flag is None:
            raise RuntimeError('flag_taken is for mode "exit"')
        with self._lock:
            return self._was_armed and not self._flag.exists()

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

        def call(*args: Any, **kwargs: Any) -> Any:
            if self._latched is not None:
                raise SimulatedCrash(self._latched)
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
            self._text = None
            self._seen.clear()
            return None
        if text != self._text:  # another process armed again: count from the start
            self._text = text
            self._seen.clear()
        return point, int(count) if sep else 1

    def _take(self) -> bool:
        """Disarm. False if a flag file could not be deleted (someone else took it). Call with the
        lock held."""
        if self._flag is None:
            self._memory = None
            return True
        try:
            self._flag.unlink()
        except OSError:
            return False
        return True
