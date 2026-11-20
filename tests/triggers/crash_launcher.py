"""A trigger worker as a child process, for the kill, two-process and stop-signal tests.

Not a test file and not collected by pytest. Started as
``python -m tests.triggers.crash_launcher --config-dir <dir> ...`` with the repo root as working
directory. It does NOT call ``worker.main``: ``main`` needs the config block ``triggers`` that does
not exist yet, so the pieces are put together here the way ``_prepare`` does it: a Runtime on the
chosen store, then ``worker.make_app`` (the start checks, the Runner, the WSGI callable),
``worker.make_server`` on an ephemeral loopback port and ``worker.serve``.

Crash points: with ``--flag`` ONE ``CrashPoints(mode="exit")`` wraps, after the runtime is built,
the runtime's store (``create_run``, ``transition``, ``touch``) and the store handed to the Runner
(``get_run``). The parent arms a point by writing the flag file.

Stdout, line by line: ``port <n>`` (first line, once the socket is bound); after a clean stop one
``run <run_id> <STATE>`` line per stored run and then ``stopped``. The model double appends one
byte to ``--calls-file`` per call, so the parent can count model calls across restarts.

Environment: ``TRIGGER_CHILD_SECRETS`` is a JSON object sender id -> fake secret value;
``CRASH_CHILD_DSN`` is the PostgreSQL DSN for ``--store postgres``.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import subprocess
import sys
import threading
import time
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.models import Reply, RunState, now
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from tests.k5_support import ScriptLLM, build_runtime

AGENT, PRINCIPAL, TENANT = "test-agent", "svc:test-agent", "tenant-a"
HOST = "127.0.0.1"
SECRETS_ENV, DSN_ENV = "TRIGGER_CHILD_SECRETS", "CRASH_CHILD_DSN"
RUNTIME_POINTS = ("create_run", "transition", "touch")
RUNNER_POINTS = ("get_run",)
ROOT = Path(__file__).resolve().parents[2]
PATH, PREFIX = "/v1/trigger", "X-Hadavin"
START_WAIT_S, EXIT_WAIT_S, REQUEST_TIMEOUT_S = 60.0, 30.0, 30.0


class CountingLLM(ScriptLLM):
    """Always answers "nothing to do"; one byte per call goes to the calls file."""

    def __init__(self, calls_file: Path | None, delay_s: float) -> None:
        super().__init__([])
        self._file, self._delay_s, self._lock = calls_file, delay_s, threading.Lock()

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        with self._lock:
            if self._file is not None:
                with self._file.open("ab") as out:
                    out.write(b"x")
        if self._delay_s:
            time.sleep(self._delay_s)
        return Reply(text="Nothing to do.", model_id="fake-model")


def _store(kind: str):
    if kind == "memory":
        return MemoryStore()
    from hadavin_sdk.store.postgres import PostgresStore, connect

    return PostgresStore(connect(os.environ[DSN_ENV]))


def _all_runs(store) -> list:
    later = now() + timedelta(days=1)
    return [run for state in RunState for run in store.list_runs(state, later, limit=1000)]


def make_trigger_app(runtime, store, secrets: dict[str, str], **over):
    """The stand-in for a built App (the config block `triggers` does not exist yet): every sender
    of `secrets` runs as the test agent and its service principal. `store` goes to the Runner."""
    senders = [
        SimpleNamespace(
            id=sender, secret_names=[f"{sender}-secret"], agent_id=AGENT, principal_id=PRINCIPAL
        )
        for sender in sorted(secrets)
    ]
    base = {
        "tenant": TENANT,
        "senders": senders,
        "max_body_bytes": 65536,
        "max_running": 2,
        "ack_wait_s": 5.0,
        "poll_s": 0.02,
    }
    by_name = {f"{sender}-secret": value for sender, value in secrets.items()}
    return SimpleNamespace(
        config=SimpleNamespace(triggers=SimpleNamespace(**{**base, **over})),
        registry=runtime.registry,
        runtime=runtime,
        store=store,
        trigger_resolve=by_name.__getitem__,
    )


# --- the parent's side: start a child, talk to it over a real socket ------------------------------


class Child:
    """One launcher process. Its output goes to two files, so a full pipe never blocks it. Use it
    in a `with` block: the process is killed at the end whatever happened."""

    def __init__(self, work_dir: Path, config_dir: Path, secrets: dict[str, str], *args: str,
                 dsn: str | None = None) -> None:
        work_dir.mkdir(parents=True, exist_ok=True)
        self._out, self._err = work_dir / "stdout.txt", work_dir / "stderr.txt"
        env = {**os.environ, SECRETS_ENV: json.dumps(secrets)}
        if dsn is not None:
            env[DSN_ENV] = dsn
        store = "postgres" if dsn is not None else "memory"
        command = [sys.executable, "-m", "tests.triggers.crash_launcher", "--config-dir",
                   str(config_dir), "--store", store, *args]
        with self._out.open("wb") as out, self._err.open("wb") as err:
            self.proc = subprocess.Popen(  # noqa: S603 - this interpreter, this repo's launcher, no shell
                command, cwd=ROOT, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL
            )
        self.port = 0

    def __enter__(self) -> Child:
        try:
            self.port = self._wait_for_port()
        except BaseException:
            self.kill()
            raise
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.kill()

    def _wait_for_port(self) -> int:
        deadline = time.monotonic() + START_WAIT_S
        while time.monotonic() < deadline:
            first = self.stdout().partition("\n")
            if first[1] and first[0].startswith("port "):
                return int(first[0].split()[1])
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        raise AssertionError(
            f"the child did not print its port (exit {self.proc.poll()}): {self.stderr()[-2000:]}"
        )

    def stdout(self) -> str:
        return self._out.read_text(encoding="utf-8", errors="replace")

    def stderr(self) -> str:
        return self._err.read_text(encoding="utf-8", errors="replace")

    def wait(self, timeout_s: float = EXIT_WAIT_S) -> int:
        """The exit code; the child is killed and the test fails if it does not end in time."""
        try:
            return self.proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            self.kill()
            raise AssertionError(f"the child did not end within {timeout_s} s") from None

    def kill(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=EXIT_WAIT_S)


def wire_body(key: str, document: str) -> bytes:
    return json.dumps({"key": key, "document": document}).encode("utf-8")


def signed_post(port: int, body: bytes, secret: str) -> tuple[int | None, bytes]:
    """One signed POST over a real loopback socket, signed now. (status, body), or (None, the
    class name of the connection error) when no answer came."""
    headers = hmac_v0.sign(body, int(time.time()), secret, PREFIX)
    conn = http.client.HTTPConnection(HOST, port, timeout=REQUEST_TIMEOUT_S)
    try:
        conn.request("POST", PATH, body=body, headers=headers)
        reply = conn.getresponse()
        return reply.status, reply.read()
    except (OSError, http.client.HTTPException) as exc:
        return None, type(exc).__name__.encode()
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.triggers.crash_launcher")
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--store", choices=("memory", "postgres"), default="postgres")
    parser.add_argument("--flag", type=Path, default=None)
    parser.add_argument("--calls-file", type=Path, default=None)
    parser.add_argument("--llm-delay-s", type=float, default=0.0)
    parser.add_argument("--max-body-bytes", type=int, default=65536)
    parser.add_argument("--max-running", type=int, default=2)
    parser.add_argument("--ack-wait-s", type=float, default=5.0)
    args = parser.parse_args(argv)

    secrets = json.loads(os.environ[SECRETS_ENV])
    plain = _store(args.store)
    llm = CountingLLM(args.calls_file, args.llm_delay_s)
    runtime, _cards = build_runtime(args.config_dir, llm, store=plain)
    for_runner = plain
    if args.flag is not None:  # AFTER the build: the runtime keeps its own reference to the store
        from hadavin_sdk.testing.crash import CrashPoints

        points = CrashPoints(mode="exit", flag_path=args.flag)
        runtime.store = points.wrap(plain, "store", RUNTIME_POINTS)
        for_runner = points.wrap(plain, "store", RUNNER_POINTS)

    app = make_trigger_app(
        runtime,
        for_runner,
        secrets,
        max_body_bytes=args.max_body_bytes,
        max_running=args.max_running,
        ack_wait_s=args.ack_wait_s,
    )
    wsgi, runner = worker.make_app(app)
    server = worker.make_server(HOST, 0, wsgi, args.ack_wait_s + worker.SOCKET_SLACK_S)
    print(f"port {server.server_port}", flush=True)
    code = worker.serve(server, runner)
    for run in _all_runs(plain):
        print(f"run {run.run_id} {RunState(run.state).value}", flush=True)
    print("stopped", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
