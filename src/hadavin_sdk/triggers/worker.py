"""The worker half of the signed trigger endpoint: one process that serves the endpoint and runs the agent loop.

`Runner.start` is what the endpoint calls for a verified request. It answers 2xx only after the store has returned
the run row and that row is for the same agent, principal and `trigger_ref` (same sender, key and document). The
answer is always decided from the ROW, never from which exception the loop raised. 202 = the run is RECEIVED or
WORKING, 200 = any later state, 409 = a row exists for the same key but another document (nothing is written),
503 = store not reachable, or no row within `ack_wait_s` (not acknowledged; send again with the same key; it
may already be running). A request that finds no free slot is not refused at once: it waits for the row like any other, because another
request for the same key may be writing it right now. While it waits it takes a slot as soon as one is free, and
it looks at the store less and less often (the pause doubles up to one second, about ten reads in five seconds);
with neither a slot nor a row by the end of `ack_wait_s` it gets 503. At most
one run per key rests on the primary key of the runs table, and every answer on the stored row: nothing in this
process remembers keys.

Several threads at once: what was read, and what was not
- `Runtime` keeps no per-run state on itself: its fields are set once in `__init__` (runtime/agent_loop.py:208-213)
  and a run's working data are locals of `handle` (396-398).
- The memory store takes one lock for every method that reads or writes rows (store/memory.py:31, 52, 58, 64);
  `create_run` checks and inserts under that lock, so of two calls with one run id exactly one wins.
- The call that loses gets `StaleState`, and `handle` then returns the stored run without any work when agent,
  principal and `trigger_ref` are equal, else raises `StaleState` again (agent_loop.py:335-349, 388-393). Two
  parallel `start` calls with one key therefore give one row and one loop.
- The local audit sink writes under a lock (audit/local_dir.py:30, 82); the recorded model double too (llm/fake.py:27).
- Spend is NOT safe in the money sense: the budget is read before a model call and the cost is added after it
  (limits.py:17-30), so N runs of one agent in parallel can pass a budget by up to N calls. This is why
  `max_running` defaults to 1.
- NOT READ, so not shown safe: the real model clients, the detector, the read tools, the card channel, the
  PostgreSQL store and the chain audit under threads. With `max_running` 1 only one loop runs at a time, but the
  short `get_run` reads of request threads still run next to it.
- `handle` runs on a pool thread. If it raises, the class name is logged and nothing else; the process goes on and
  a run that was cut off is ended by the tick's stuck step, so the tick MUST run in the deployment.

Start: `python -m hadavin_sdk.triggers.worker --config-dir <dir>`; host and port come from `config.triggers`
unless given. The stdlib server is not hardened: it listens on loopback unless `triggers.allow_non_loopback` is
true, and TLS is the job of the proxy in front of it.
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import signal
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import wait as wait_all
from pathlib import Path
from typing import Any, Final, Self
from wsgiref.simple_server import WSGIServer

from hadavin_sdk.errors import ConfigError as AnyConfigError
from hadavin_sdk.models import Run, RunState, now
from hadavin_sdk.store.protocol import NotFound, StoreUnavailable, is_connectivity_error
from hadavin_sdk.triggers.endpoint import Accepted, check_secrets, make_wsgi
from hadavin_sdk.triggers.server import QuietRequestHandler, QuietServer

POLL_S: Final[float] = 0.05  # how often `start` looks for the row while it waits
NO_SLOT_POLL_CAP_S: Final[float] = 1.0  # with no free slot the wait doubles from POLL_S up to this
MAX_RUNNING: Final[int] = 1  # see the module text: parallel runs can pass a budget
ACK_WAIT_S: Final[float] = 5.0
CLOSE_WAIT_S: Final[float] = 30.0  # how long `close` waits for running loops
SOCKET_SLACK_S: Final[float] = 10.0  # a connection may stay open ack_wait_s plus this
LOOPBACK: Final[str] = "127.0.0.1"
PORT: Final[int] = 8081
TRIGGER_KIND: Final[str] = "event"
STUCK_STEP: Final[str] = "stuck"  # the tick step that ends a cut-off run
TICK_MAX_AGE_S: Final[float] = 600.0  # a good "stuck" tick older than this is warned about at start
IN_PROGRESS: Final[frozenset[RunState]] = frozenset({RunState.RECEIVED, RunState.WORKING})
NO_ACK: Final[tuple[int, dict[str, str]]] = (503, {})
CONFLICT: Final[tuple[int, dict[str, str]]] = (409, {})
EXIT_OK, EXIT_CONFIG, EXIT_FAILED, EXIT_STORE = 0, 2, 3, 4

_LOG = logging.getLogger("hadavin_sdk.triggers")


class ConfigError(AnyConfigError):
    """A start refusal written in THIS file: its text is built here from ids and bounds, so `main` prints it.
    Any other config or store error is printed by class name only (its text could hold a value)."""


class Runner:
    """Starts at most `max_running` agent loops at a time and tells the endpoint what to answer."""

    def __init__(
        self,
        runtime: Any,
        store: Any,
        max_running: int = MAX_RUNNING,
        ack_wait_s: float = ACK_WAIT_S,
        *,
        poll_s: float = POLL_S,
    ) -> None:
        if max_running < 1 or ack_wait_s <= 0 or poll_s <= 0:
            raise ValueError("max_running, ack_wait_s and poll_s must be above zero")
        self._runtime, self._store = runtime, store
        self._ack_wait_s, self._poll_s = float(ack_wait_s), float(poll_s)
        self._slots = threading.BoundedSemaphore(max_running)
        self._pool = ThreadPoolExecutor(max_workers=max_running, thread_name_prefix="trigger-run")
        self._lock = threading.Lock()  # guards _jobs and _closed
        self._jobs: set[Future[None]] = set()  # handle calls not yet ended, for `close` only
        self._closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self, wait_s: float = CLOSE_WAIT_S) -> None:
        """Take no new work, drop work that has not begun, wait up to `wait_s` for running loops.

        From this call on `start` begins no loop: a key with no row gets 503, a key whose row exists is still
        answered from that row. A loop that is already running is NOT cut off: it runs to its end, also after
        `wait_s` has passed (its thread then keeps the process alive until it ends). May be called twice."""
        with self._lock:
            self._closed = True
            jobs = list(self._jobs)
        self._pool.shutdown(wait=False, cancel_futures=True)
        wait_all(jobs, timeout=wait_s)

    def start(self, req: Accepted) -> tuple[int, dict[str, str]]:
        """The status and answer body for one verified request. Never raises for a store or loop failure."""
        try:
            found = self._row(req.run_id)
            if found is not None:
                return _answer(found, req)
            job, closed = self._submit(req)
            if closed:
                return NO_ACK
            # job None = no free slot: wait for the row all the same, another request may be writing it.
            deadline = time.monotonic() + self._ack_wait_s
            pause, pause_cap = self._poll_s, max(self._poll_s, NO_SLOT_POLL_CAP_S)
            while True:
                # read BEFORE the row, so one look at the row follows the end of the loop
                ended = job is not None and job.done()
                found = self._row(req.run_id)
                if found is not None:
                    return _answer(found, req)
                left = deadline - time.monotonic()
                if ended or left <= 0:
                    return NO_ACK  # the loop ended with no row, or the wait is over: no ack
                if job is None:  # no slot so far: take a free one, else look less often
                    job = self._submit(req)[0]
                    pause = self._poll_s if job is not None else min(pause * 2, pause_cap)
                time.sleep(min(pause, left))
        except Exception as exc:  # noqa: BLE001 - the store failed: no ack, the sender retries
            what = "store unreachable" if is_connectivity_error(exc) else "store error"
            _LOG.warning("trigger start: %s (%s)", what, type(exc).__name__)
            return NO_ACK

    def _row(self, run_id: str) -> Run | None:
        try:
            return self._store.get_run(run_id)
        except NotFound:
            return None

    def _submit(self, req: Accepted) -> tuple[Future[None] | None, bool]:
        """(the new handle call, or None when no slot is free; True when the Runner is closed)."""
        with self._lock:
            if self._closed:
                return None, True
            if not self._slots.acquire(blocking=False):
                return None, False
            try:
                job = self._pool.submit(self._run, req)
            except BaseException:
                self._slots.release()
                raise
            self._jobs.add(job)
        # Outside the lock: a job that has already ended runs the callback at once, in this thread.
        job.add_done_callback(self._ended)
        return job, False

    def _ended(self, job: Future[None]) -> None:
        """The slot is given back only here, when the loop has ended (or was dropped by `close`)."""
        with self._lock:
            self._jobs.discard(job)
        self._slots.release()

    def _run(self, req: Accepted) -> None:
        try:
            self._runtime.handle(
                req.agent_id,
                req.principal_id,
                req.document,
                trigger_kind=TRIGGER_KIND,
                trigger_ref=req.trigger_ref,
                run_id=req.run_id,
            )
        except Exception as exc:  # noqa: BLE001 - never takes the process down; the tick ends a cut-off run
            _LOG.warning("trigger run %s: loop raised %s", req.run_id, type(exc).__name__)


def _answer(found: Run, req: Accepted) -> tuple[int, dict[str, str]]:
    """Decided from the stored row alone: 409 for a foreign row, else 202 while in progress and 200 after."""
    if (
        found.agent_id != req.agent_id
        or found.principal_id != req.principal_id
        or found.trigger_ref != req.trigger_ref
    ):
        _LOG.warning("trigger status=409 sender=%s run=%s", req.sender, req.run_id)
        return CONFLICT
    state = RunState(found.state)
    return (202 if state in IN_PROGRESS else 200), {"run_id": found.run_id, "state": state.value}


def trigger_settings(config: object) -> Any:
    """`config.triggers`, or a ConfigError when the block is missing."""
    settings = getattr(config, "triggers", None)
    if settings is None:
        raise ConfigError("triggers block not configured (config.yaml has no `triggers:`)")
    return settings


def sender_list(settings: Any) -> list[tuple[str, Any]]:
    """(sender id, sender) pairs from a list of senders with `id`, or from a mapping id -> sender."""
    senders = settings.senders
    if isinstance(senders, Mapping):
        return list(senders.items())
    if isinstance(senders, Iterable):
        return [(s.id, s) for s in senders]
    raise ConfigError("triggers.senders is neither a list nor a mapping")


def check_senders(
    senders: list[tuple[str, Any]], agents: Iterable[str], principals: Mapping[str, Any]
) -> None:
    """Every sender runs as a qualified agent and as a principal of kind service, or the worker does not start."""
    qualified = set(agents)
    for sender_id, sender in senders:
        if sender.agent_id not in qualified:
            raise ConfigError(
                f"trigger sender {sender_id}: agent {sender.agent_id} is not qualified"
            )
        principal = principals.get(sender.principal_id)
        if principal is None:
            raise ConfigError(
                f"trigger sender {sender_id}: principal {sender.principal_id} is not in principals.yaml"
            )
        if getattr(principal, "kind", None) != "service":
            raise ConfigError(
                f"trigger sender {sender_id}: principal {sender.principal_id} is not of kind service"
            )


def read_secrets(
    senders: list[tuple[str, Any]], resolve: Callable[[str], str]
) -> dict[str, tuple[str, ...]]:
    """The secret values of each sender, read once by name. A failure names the sender, never a value."""
    out: dict[str, tuple[str, ...]] = {}
    for sender_id, sender in senders:
        names = list(sender.secret_names)
        if len(names) > 1:
            _LOG.warning(
                "trigger sender %s accepts %d secrets: finish the swap", sender_id, len(names)
            )
        try:
            out[sender_id] = tuple(resolve(name) for name in names)
        except Exception as exc:  # noqa: BLE001 - any provider failure stops the start
            raise ConfigError(
                f"trigger sender {sender_id}: a secret could not be read ({type(exc).__name__})"
            ) from None
    return out


def check_bind(host: str, allow_non_loopback: bool) -> None:
    """Refuse a host that is not loopback unless the config says so in plain words. A host must be an IPv4
    address or the name localhost: any other text (an empty one would mean every interface) is refused, and
    so is every IPv6 address, the loopback one too, because the server opens an IPv4 socket only."""
    if host == "localhost":
        return
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        raise ConfigError("--host must be an IP address or localhost") from None
    if address.version != 4:
        raise ConfigError("--host is an IPv6 address: the server listens on IPv4 only")
    loopback = address.is_loopback
    if not loopback and allow_non_loopback is not True:
        raise ConfigError(
            f"--host {host} is not loopback: set triggers.allow_non_loopback: true to listen there"
        )


def make_app(app: Any, *, clock: Callable[[], float] = time.time) -> tuple[Any, Runner]:
    """The WSGI callable and its Runner from a built App (for `main`, or for a WSGI server of the client's
    choice). The caller closes the Runner."""
    settings = trigger_settings(app.config)
    resolve = getattr(app, "trigger_resolve", None)
    if resolve is None:
        raise ConfigError(
            "App.trigger_resolve is not available: the trigger secrets cannot be read"
        )
    senders = sender_list(settings)
    check_senders(senders, app.runtime.agents, app.registry.principals)
    secrets = read_secrets(senders, resolve)
    try:
        check_secrets(secrets)
        runner = Runner(
            app.runtime,
            app.store,
            getattr(settings, "max_running", MAX_RUNNING),
            getattr(settings, "ack_wait_s", ACK_WAIT_S),
            poll_s=getattr(settings, "poll_s", POLL_S),
        )
    except ValueError as exc:  # these messages name senders and bounds, never a value
        raise ConfigError(str(exc)) from None
    try:
        return make_wsgi(settings, secrets, runner.start, clock), runner
    except ValueError as exc:
        runner.close(0)
        raise ConfigError(str(exc)) from None
    except BaseException:
        runner.close(0)
        raise


def make_server(host: str, port: int, wsgi: Any, socket_timeout_s: float) -> WSGIServer:
    """A bound stdlib server (not yet serving). The caller runs `serve_forever` and `server_close`. A port
    that is in use, or an address that cannot be bound, is a ConfigError (exit code 2 in `main`)."""
    handler = type("TriggerHandler", (QuietRequestHandler,), {"timeout": socket_timeout_s})
    try:
        server = QuietServer((host, port), handler)
    except OSError as exc:  # port in use, or an address that cannot be bound: not the store
        raise ConfigError(f"cannot listen on {host}:{port} ({type(exc).__name__})") from None
    server.set_app(wsgi)
    return server


def _qualified_agents(registry: Any) -> list[str]:
    """Every qualified agent, the way the tick command builds its App."""
    from hadavin_sdk.runtime.agent_loop import Unqualified, assert_qualified

    agents = []
    for agent_id in registry.agents:
        try:
            assert_qualified(registry, agent_id)
            agents.append(agent_id)
        except Unqualified:
            _LOG.warning("trigger worker: %s is not qualified; its runs are refused", agent_id)
    return agents


def check_tick(store: Any) -> bool:
    """True when the store holds a good "stuck" tick not older than TICK_MAX_AGE_S. Else one warning; the
    start goes on in every case."""
    try:
        state = store.get_tick_state(STUCK_STEP)
        last = None if state is None else state.last_ok_at
        if last is not None and (now() - last).total_seconds() <= TICK_MAX_AGE_S:
            return True
        seen = "none recorded" if last is None else "the last good one is too old"
    except Exception as exc:  # noqa: BLE001 - a warning only: never a reason not to start
        seen = f"could not be read ({type(exc).__name__})"
    _LOG.warning(
        "trigger worker: no good %s tick in the last %d s (%s): is the tick running?",
        STUCK_STEP,
        TICK_MAX_AGE_S,
        seen,
    )
    return False


def serve(server: WSGIServer, runner: Any) -> int:
    """Serve until Ctrl-C or SIGTERM, then close the socket and wait for the running loops (`Runner.close`).

    The signal handler only starts a thread that calls `server.shutdown()`: called in the thread that serves,
    `shutdown` would wait for itself. Not in the main thread no handler can be set; that is logged."""

    def on_term(signum: int, frame: object) -> None:
        threading.Thread(target=server.shutdown, name="trigger-stop", daemon=True).start()

    previous: Any = None
    try:
        previous = signal.signal(signal.SIGTERM, on_term)
    except ValueError:
        _LOG.warning("trigger worker: not the main thread, SIGTERM is not handled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        runner.close()
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)
    return EXIT_OK


def _prepare(args: argparse.Namespace) -> tuple[WSGIServer, Runner]:
    from hadavin_sdk.app import build
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    config = load_config(args.config_dir)
    settings = trigger_settings(config)  # before anything is built: no secret read, no connection
    host = args.host or getattr(settings, "host", LOOPBACK)
    port = args.port if args.port is not None else getattr(settings, "port", PORT)
    check_bind(host, getattr(settings, "allow_non_loopback", False))
    app = build(args.config_dir, _qualified_agents(load_registry(config)))
    wsgi, runner = make_app(app)
    check_tick(app.store)
    try:
        timeout = getattr(settings, "ack_wait_s", ACK_WAIT_S) + SOCKET_SLACK_S
        return make_server(host, port, wsgi, timeout), runner
    except BaseException:
        runner.close(0)
        raise


def main(argv: list[str] | None = None) -> int:
    """Exit codes: 0 stopped cleanly (Ctrl-C or SIGTERM), 2 config error, 4 store not reachable at start, 3 anything else."""
    parser = argparse.ArgumentParser(prog="python -m hadavin_sdk.triggers.worker")
    parser.add_argument("--config-dir", type=Path, default=None)
    parser.add_argument("--host", default=None, help="default: triggers.host (loopback)")
    parser.add_argument("--port", type=int, default=None, help="default: triggers.port")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    try:
        server, runner = _prepare(args)
    except StoreUnavailable as exc:  # a config error subclass: must come first
        print(f"trigger worker: store unreachable: {type(exc).__name__}", file=sys.stderr)
        return EXIT_STORE
    except ConfigError as exc:  # written in this file: ids and bounds only
        print(f"trigger worker: config error: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except AnyConfigError as exc:  # class name only: the text could hold a value
        print(f"trigger worker: config error: {type(exc).__name__}", file=sys.stderr)
        return EXIT_CONFIG
    except Exception as exc:  # noqa: BLE001 - class name only: the text could hold a value
        if is_connectivity_error(exc):
            print(f"trigger worker: store unreachable: {type(exc).__name__}", file=sys.stderr)
            return EXIT_STORE
        print(f"trigger worker: start failed: {type(exc).__name__}", file=sys.stderr)
        return EXIT_FAILED
    _LOG.info(
        "trigger worker: serving on port %d; the tick must run too, or a cut-off run never reaches a person",
        server.server_port,
    )
    return serve(server, runner)


if __name__ == "__main__":
    raise SystemExit(main())
