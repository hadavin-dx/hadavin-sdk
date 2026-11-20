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
import json
import os
import sys
import threading
import time
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from hadavin_sdk.models import Reply, RunState, now
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from tests.k5_support import ScriptLLM, build_runtime

AGENT, PRINCIPAL, TENANT = "test-agent", "svc:test-agent", "tenant-a"
HOST = "127.0.0.1"
SECRETS_ENV, DSN_ENV = "TRIGGER_CHILD_SECRETS", "CRASH_CHILD_DSN"
RUNTIME_POINTS = ("create_run", "transition", "touch")
RUNNER_POINTS = ("get_run",)


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

    senders = [
        SimpleNamespace(
            id=sender, secret_names=[f"{sender}-secret"], agent_id=AGENT, principal_id=PRINCIPAL
        )
        for sender in sorted(secrets)
    ]
    settings = SimpleNamespace(
        tenant=TENANT,
        senders=senders,
        max_body_bytes=args.max_body_bytes,
        max_running=args.max_running,
        ack_wait_s=args.ack_wait_s,
        poll_s=0.02,
    )
    by_name = {f"{sender}-secret": value for sender, value in secrets.items()}
    app = SimpleNamespace(
        config=SimpleNamespace(triggers=settings),
        registry=runtime.registry,
        runtime=runtime,
        store=for_runner,
        trigger_resolve=by_name.__getitem__,
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
