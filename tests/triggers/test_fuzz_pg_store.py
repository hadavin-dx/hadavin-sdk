"""A10: hostile concurrency and crash fuzz of the signed trigger door on the REAL PostgreSQL store.

Needs HADAVIN_TEST_PG_DSN (a superuser on a throwaway server) and HADAVIN_REQUIRE_PG=1. New tests only; no
product code is touched. Workers are child processes of ``tests/triggers/crash_launcher.py`` (the real
endpoint, Runner and server on a PostgresStore). Rows are read back by plain SQL on a connection of the
test's own.

Seeds: FUZZ_SEED (default 20261120) plus the test name make each test's random stream; the seed and every
random choice that matters are printed (``-s``) and appended to the file in FUZZ_PG_LOG when it is set.

Load rule: a test waits (up to 180 s) for a 1-minute load average of 3.5 or less before it starts, and its
wall-clock assertion is applied only when the load stayed at 4 or less.

  (a) same key, same document / same key, other documents, at high concurrency across 2 worker processes
  (b) kill -9 of workers at random moments during a burst, restart, re-POST everything
  (c) store outage (pg_terminate_backend of the workers' connections) during a burst, then recovery
  (d) hostile bytes (truncated, oversized, slow loris, connection cap) while a legitimate stream runs
"""

# ruff: noqa: S311  (seeded fuzz randomness, not cryptography)
from __future__ import annotations

import json
import os
import random
import select
import socket
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from hadavin_sdk.approvals import hmac_v0
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import k5_cfg
from tests.triggers.crash_launcher import (
    HOST,
    PATH,
    PREFIX,
    Child,
    signed_post,
    wire_body,
)
from tests.triggers.test_t5_postgres import (
    AGENT,
    OK,
    SECRET,
    SENDER,
    _calls,
    _ref,
    _rows,
    _run_id,
    _stuck_tick,
)

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg

SEED = int(os.environ.get("FUZZ_SEED", "20261120"))
SECRETS = {SENDER: SECRET}
IN_PROGRESS = ("RECEIVED", "WORKING")
LOAD_START_MAX, LOAD_TIME_MAX, LOAD_WAIT_S = 3.5, 4.0, 180.0
TEST_BUDGET_S = 60.0


# --- plumbing -------------------------------------------------------------------------------------


def log(message: str) -> None:
    line = f"[fuzz-pg] {message}"
    print(line, flush=True)
    path = os.environ.get("FUZZ_PG_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write(line + "\n")


def _load1() -> float:
    with open("/proc/loadavg", encoding="ascii") as fh:
        return float(fh.read().split()[0])


@pytest.fixture
def budget(request):
    """Wait for a quiet box, log the load before and after, and apply the 60 s budget only when the load allowed it."""
    waited = 0.0
    while _load1() > LOAD_START_MAX and waited < LOAD_WAIT_S:
        time.sleep(5.0)
        waited += 5.0
    before = _load1()
    if before > LOAD_START_MAX:
        pytest.fail(f"load {before} stayed above {LOAD_START_MAX} for {LOAD_WAIT_S} s: not started")
    failed_before = request.session.testsfailed
    started, peak = time.monotonic(), [before]
    stop = threading.Event()

    def watch() -> None:
        while not stop.wait(2.0):
            peak[0] = max(peak[0], _load1())

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    yield
    stop.set()
    elapsed = time.monotonic() - started
    log(
        f"{request.node.name}: seed={SEED} load1 start={before:.2f} peak={peak[0]:.2f} end={_load1():.2f} "
        f"elapsed={elapsed:.1f}s"
    )
    if peak[0] <= LOAD_TIME_MAX and request.session.testsfailed == failed_before:
        assert elapsed < TEST_BUDGET_S, f"{elapsed:.1f} s is over the {TEST_BUDGET_S:.0f} s budget"


def rng_for(name: str) -> random.Random:
    log(f"{name}: seed={SEED} (random.Random(f'{SEED}-{name}'))")
    return random.Random(f"{SEED}-{name}")


@pytest.fixture
def dsn():
    yield from pg_schema()


def start_worker(
    tmp_path: Path, name: str, dsn: str, *extra: str, app_name: str | None = None
) -> Child:
    """A launcher child on the schema of `dsn`. The same `name` again is a restart (same config, same calls file).
    With `app_name` the worker's connections carry that application_name (the test's own do not)."""
    home = tmp_path / name
    config_dir = home / "config"
    if not config_dir.exists():
        k5_cfg(home)
    runs = len(list(home.glob("run-*")))
    worker_dsn = f"{dsn} application_name={app_name}" if app_name else dsn
    args = ["--calls-file", str(home / "calls"), *extra]
    return Child(home / f"run-{runs}", config_dir, SECRETS, *args, dsn=worker_dsn).__enter__()


def document(n: int, variant: str = "a") -> str:
    return f"checkout 5xx from 10.0.0.{n}, revision {n}{variant}"


def post(port: int, key: str, doc: str) -> tuple[int | None, bytes]:
    return signed_post(port, wire_body(key, doc), SECRET)


def run_rows(dsn: str) -> dict[str, tuple]:
    return {row[0]: row for row in _rows(dsn)}


def wait_quiet(dsn: str, *, limit_s: float = 25.0, still_s: float = 2.0) -> list[tuple]:
    """Rows once no state has changed for `still_s` (runs killed in the loop stay WORKING for good)."""
    deadline, last, since = time.monotonic() + limit_s, None, time.monotonic()
    while True:
        rows = _rows(dsn)
        if rows != last:
            last, since = rows, time.monotonic()
        if time.monotonic() - since >= still_s or time.monotonic() > deadline:
            return rows
        time.sleep(0.1)


def money_check(dsn: str, runs: set[str]) -> dict:
    """The money invariants of the door, by plain SQL: at most one reservation per run, none for an unknown run,
    at most one open hold per run, and the day total of the `spend` table equals the sum of the rows
    (settled amount, or the reserved amount while open)."""
    with psycopg.connect(dsn) as db:
        res = db.execute(
            "SELECT reservation_id, run_id, day, reserved_usd, settled_usd, status FROM spend_reservations"
        ).fetchall()
        totals = {
            day: usd
            for agent, day, usd in db.execute("SELECT agent_id, day, usd FROM spend").fetchall()
        }
    per_run = Counter(row[1] for row in res)
    assert [r for r, n in per_run.items() if n > 1] == [], (
        f"two reservation rows for a run: {per_run}"
    )
    assert set(per_run) <= runs, f"reservation for an unknown run: {set(per_run) - runs}"
    open_per_run = Counter(row[1] for row in res if row[5] == "open")
    assert all(n == 1 for n in open_per_run.values())
    expected: dict = {}
    for _rid, _run, day, reserved, settled, _status in res:
        expected[day] = expected.get(day, 0) + (settled if settled is not None else reserved)
    for day in set(expected) | set(totals):
        assert totals.get(day, 0) == expected.get(day, 0), (
            day,
            totals.get(day),
            expected.get(day),
            res,
        )
    return {
        "reservations": len(res),
        "open": sum(open_per_run.values()),
        "day_totals": dict(totals),
    }


def posts_parallel(
    jobs: list[tuple[int, str, str]], threads: int
) -> list[tuple[str, str, int | None, bytes]]:
    """Send (port, key, document) jobs from a thread pool; returns (key, document, status, body) in job order."""

    def go(job):
        port, key, doc = job
        status, data = post(port, key, doc)
        return key, doc, status, data

    with ThreadPoolExecutor(max_workers=threads) as pool:
        return list(pool.map(go, jobs))


def repost_all(
    ports: list[int], keys: dict[str, str], rng: random.Random, limit_s: float = 30.0
) -> Counter:
    """Send every key again until it is answered 2xx with the right run id; returns the status counts seen."""
    seen: Counter = Counter()
    for key, doc in keys.items():
        deadline = time.monotonic() + limit_s
        while True:
            status, data = post(rng.choice(ports), key, doc)
            seen[status] += 1
            if status in OK:
                assert json.loads(data)["run_id"] == _run_id(SENDER, key)
                break
            assert status in (None, 503), (key, status, data)
            assert time.monotonic() < deadline, f"{key}: no answer in {limit_s} s: {seen}"
            time.sleep(0.2)
    return seen


# --- (a) concurrent signed POSTs across two workers -------------------------------------------------


def test_a_same_key_burst_and_document_conflicts_across_two_workers(dsn, tmp_path, budget):
    """18 keys, 248 signed POSTs from 48 threads over 2 worker processes sharing one schema. 10 keys: the same
    document 12 times. 8 keys: two documents, 8 posts each. Expected: every answer of a same-document key is
    200/202 with the one derived run id; per conflicting key one document wins (all its posts 200/202) and the
    other gets 409 (empty body) every time; never a 503; one row per key (ref of the winner); one model call and
    one reservation per run; the money checks hold."""
    rng = rng_for("a")
    w1 = start_worker(tmp_path, "w1", dsn, "--max-running", "24")
    w2 = start_worker(tmp_path, "w2", dsn, "--max-running", "24")
    try:
        same = {f"same-{n}": document(n) for n in range(10)}
        two = {f"two-{n}": (document(n, "a"), document(n, "b")) for n in range(8)}
        jobs = []
        for key, doc in same.items():
            jobs += [(rng.choice((w1.port, w2.port)), key, doc) for _ in range(12)]
        for key, (doc_a, doc_b) in two.items():
            jobs += [(rng.choice((w1.port, w2.port)), key, doc_a) for _ in range(8)]
            jobs += [(rng.choice((w1.port, w2.port)), key, doc_b) for _ in range(8)]
        rng.shuffle(jobs)
        log(f"a: {len(jobs)} posts, ports {w1.port} {w2.port}")
        replies = posts_parallel(jobs, 48)
        by_key: dict[str, list] = {}
        for key, doc, status, data in replies:
            by_key.setdefault(key, []).append((doc, status, data))
        counts = Counter(status for _k, _d, status, _b in replies)
        log(f"a: status counts {dict(counts)}")
        assert set(counts) <= {200, 202, 409}, counts  # no 503, no connection failure, nothing else
        winners: dict[str, str] = dict(same)
        for key in same:
            for _doc, status, data in by_key[key]:
                assert status in OK and json.loads(data)["run_id"] == _run_id(SENDER, key)
        for key, (doc_a, doc_b) in two.items():
            got = by_key[key]
            ok_docs = {d for d, s, _ in got if s in OK}
            conflict_docs = {d for d, s, _ in got if s == 409}
            assert len(ok_docs) == 1 and conflict_docs == {doc_a, doc_b} - ok_docs, (key, got)
            assert all(b == b"" for _d, s, b in got if s == 409)
            assert all(
                json.loads(b)["run_id"] == _run_id(SENDER, key) for _d, s, b in got if s in OK
            )
            winners[key] = next(iter(ok_docs))
        rows = wait_quiet(dsn)
        by_run = {row[0]: row for row in rows}
        assert len(rows) == len(winners) == len(by_run)
        for key, doc in winners.items():
            row = by_run[_run_id(SENDER, key)]
            assert (
                row[1] == AGENT and row[3] == _ref(SENDER, key, doc) and row[4] not in IN_PROGRESS
            ), row
        assert len({row[3] for row in rows}) == len(rows)
        calls = _calls(tmp_path / "w1" / "calls") + _calls(tmp_path / "w2" / "calls")
        money = money_check(dsn, set(by_run))
        log(f"a: rows={len(rows)} model_calls={calls} money={money}")
        assert (
            calls == len(winners) and money["reservations"] == len(winners) and money["open"] == 0
        )
    finally:
        w1.kill()
        w2.kill()


# --- (b) kill -9 of workers during a burst ----------------------------------------------------------


def test_b_kill9_of_workers_at_random_moments_then_restart_and_repost(dsn, tmp_path, budget):
    """20 keys started 0.07-0.12 s apart, each re-posted by its own thread until the killer is done, while a killer SIGKILLs a random worker (of 2) three times at
    random moments and restarts it. Then every key is posted again. Expected: during the burst only 200/202, 503
    or no answer, and a 2xx names the right run id; after: every key 2xx; exactly one row per key; at most one
    reservation per run and at most one open hold per run; day total = sum of the rows; model calls never above
    the reservations; one tick a day later ends every run that the kill left open, and adds no reservation."""
    rng = rng_for("b")
    delay = rng.choice((0.03, 0.05, 0.08))
    kill_gaps = [rng.uniform(0.1, 0.9) for _ in range(3)]
    victims = [rng.choice(("w1", "w2")) for _ in range(3)]
    log(f"b: llm_delay={delay} kill_gaps={[round(g, 3) for g in kill_gaps]} victims={victims}")
    extra = ("--llm-delay-s", str(delay), "--max-running", "16")
    workers = {
        "w1": start_worker(tmp_path, "w1", dsn, *extra),
        "w2": start_worker(tmp_path, "w2", dsn, *extra),
    }
    lock = threading.Lock()
    keys = {f"k{n}": document(n) for n in range(20)}
    during: list[tuple[str, int | None, bytes]] = []
    done = threading.Event()

    def killer() -> None:
        for gap, victim in zip(kill_gaps, victims, strict=True):
            time.sleep(gap)
            with lock:
                workers[victim].proc.kill()
                workers[victim].proc.wait(timeout=30)
            fresh = start_worker(tmp_path, victim, dsn, *extra)
            with lock:
                workers[victim] = fresh
        done.set()

    t_zero = [0.0]
    pace = rng.uniform(
        0.07, 0.12
    )  # seconds between the first posts of two keys: runs start all through the kills

    def poster(share: list[tuple[int, str, str]]) -> None:
        for n, key, doc in share:
            time.sleep(max(0.0, t_zero[0] + n * pace - time.monotonic()))
            passes = 0
            while passes < 3 or not done.is_set():
                with lock:
                    port = workers[rng_local.choice(("w1", "w2"))].port
                status, data = post(port, key, doc)
                with lock:
                    during.append((key, status, data))
                passes += 1
                time.sleep(rng_local.uniform(0.02, 0.15))

    rng_local = random.Random(f"{SEED}-b-local")
    try:
        items = [(n, key, doc) for n, (key, doc) in enumerate(keys.items())]
        t_zero[0] = time.monotonic()
        killer_thread = threading.Thread(target=killer)
        killer_thread.start()
        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(poster, [[item] for item in items]))
        killer_thread.join(120)
        assert done.is_set()
        counts = Counter(status for _k, status, _d in during)
        log(f"b: burst status counts {dict(counts)}")
        for key, status, data in during:
            assert status in (200, 202, 503, None), (key, status, data)
            if status in OK:
                assert json.loads(data)["run_id"] == _run_id(SENDER, key)
        assert all(w.proc.poll() is None for w in workers.values())
        ports = [w.port for w in workers.values()]
        seen = repost_all(ports, keys, rng)
        log(f"b: repost status counts {dict(seen)}")
        rows = wait_quiet(dsn)
        by_run = {row[0]: row for row in rows}
        assert sorted(by_run) == sorted(_run_id(SENDER, key) for key in keys), "not one row per key"
        assert all(row[1] == AGENT for row in rows)
        for key, doc in keys.items():
            assert by_run[_run_id(SENDER, key)][3] == _ref(SENDER, key, doc)
        again = repost_all(ports, keys, rng)  # a second full repost: answered, still no new row
        assert set(again) <= {200, 202}
        left = [row for row in _rows(dsn) if row[4] in IN_PROGRESS]
        money = money_check(dsn, set(by_run))
        calls = sum(_calls(tmp_path / name / "calls") for name in ("w1", "w2"))
        log(f"b: rows={len(rows)} left_in_progress={len(left)} calls={calls} money={money}")
        assert calls <= money["reservations"] <= len(keys)
        ended = _stuck_tick(tmp_path, "w1", dsn)
        after = _rows(dsn)
        log(f"b: tick exit {ended}; states {dict(Counter(r[4] for r in after))}")
        assert ended == 0 and not [
            r for r in after if r[4] in IN_PROGRESS
        ]  # run_tick returns an exit code
        assert len(after) == len(keys)
        assert money_check(dsn, set(by_run))["reservations"] == money["reservations"]
        assert sum(_calls(tmp_path / name / "calls") for name in ("w1", "w2")) == calls
    finally:
        for worker in workers.values():
            worker.kill()


# --- (c) store outage mid-burst ---------------------------------------------------------------------


def _terminate(dsn: str, app_name: str) -> int:
    with psycopg.connect(dsn, autocommit=True) as admin:
        got = admin.execute(
            "SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity"
            " WHERE application_name = %s AND pid <> pg_backend_pid()",
            (app_name,),
        ).fetchone()
    return got[0]


def test_c_store_outage_by_pg_terminate_backend_then_recovery(dsn, tmp_path, budget):
    """Two workers whose store connection carries an application name. 18 keys start 0.07-0.12 s apart and are
    re-posted for 5 s; at a random moment in the first second `pg_terminate_backend` ends the workers' backends
    (repeatedly, for 1 s). Expected during the outage: only 200/202, 503 or no answer (never 409, never a wrong run
    id) and at least one 503 or lost answer. Then: do the workers answer again WITHOUT a restart (logged; the
    store has no reconnect, see test_c_min below)? If not, both are restarted. After that: every key 2xx with the
    right run id, one row per key, at most one reservation per run and one open hold per run, calls never above
    reservations (no double start), day total = sum of the rows, a tick a day later ends every run left open."""
    rng = rng_for("c")
    app_name = f"fzc{rng.randrange(10**6)}"
    cut_at, window = rng.uniform(0.2, 1.0), 1.0
    pace = rng.uniform(0.07, 0.12)
    log(f"c: application_name={app_name} cut_at={cut_at:.2f}s window={window}s pace={pace:.3f}s")
    extra = ("--llm-delay-s", "0.05", "--max-running", "16")
    w = {
        "w1": start_worker(tmp_path, "w1", dsn, *extra, app_name=app_name),
        "w2": start_worker(tmp_path, "w2", dsn, *extra, app_name=app_name),
    }
    keys = {f"k{n}": document(n) for n in range(18)}
    results: list[tuple[str, int | None, bytes]] = []
    lock = threading.Lock()
    t_zero = [0.0]
    terminated = [0]
    stop_posting = threading.Event()
    try:

        def terminator() -> None:
            time.sleep(cut_at)
            end = time.monotonic() + window
            while time.monotonic() < end:
                terminated[0] += _terminate(dsn, app_name)
                time.sleep(rng.uniform(0.005, 0.03))

        def poster(item: tuple[int, str, str]) -> None:
            n, key, doc = item
            local = random.Random(f"{SEED}-c-local-{n}")
            time.sleep(max(0.0, t_zero[0] + n * pace - time.monotonic()))
            while not stop_posting.is_set():
                status, data = post(local.choice([w["w1"].port, w["w2"].port]), key, doc)
                with lock:
                    results.append((key, status, data))
                time.sleep(local.uniform(0.02, 0.15))

        items = [(n, key, doc) for n, (key, doc) in enumerate(keys.items())]
        t_zero[0] = time.monotonic()
        t = threading.Thread(target=terminator)
        t.start()
        threading.Timer(5.0, stop_posting.set).start()
        with ThreadPoolExecutor(max_workers=18) as pool:
            list(pool.map(poster, items))
        t.join(30)
        counts = Counter(status for _k, status, _d in results)
        log(
            f"c: backends terminated={terminated[0]} burst status counts {dict(counts)} posts={len(results)}"
        )
        for key, status, data in results:
            assert status in (200, 202, 503, None), (key, status, data)
            if status in OK:
                assert json.loads(data)["run_id"] == _run_id(SENDER, key)
        assert terminated[0] > 0
        assert counts.get(503, 0) + counts.get(None, 0) > 0, "the outage was never seen by a client"
        assert all(x.proc.poll() is None for x in w.values()), "a worker died"
        # recovery without a restart?
        probe_until, healed = time.monotonic() + 8.0, False
        while time.monotonic() < probe_until and not healed:
            healed = post(w["w1"].port, "k0", keys["k0"])[0] in OK
            time.sleep(0.25)
        log(f"c: a worker answers k0 again without a restart within 8 s after the outage: {healed}")
        if not healed:
            for name in ("w1", "w2"):
                w[name].kill()
                w[name] = start_worker(tmp_path, name, dsn, *extra, app_name=app_name)
        ports = [x.port for x in w.values()]
        seen = repost_all(ports, keys, rng, limit_s=20.0)
        log(f"c: repost status counts {dict(seen)}")
        rows = wait_quiet(dsn)
        by_run = {row[0]: row for row in rows}
        assert sorted(by_run) == sorted(_run_id(SENDER, k) for k in keys), "not one row per key"
        for key, doc in keys.items():
            assert by_run[_run_id(SENDER, key)][3] == _ref(SENDER, key, doc)
        money = money_check(dsn, set(by_run))
        calls = sum(_calls(tmp_path / n / "calls") for n in ("w1", "w2"))
        left = [r for r in rows if r[4] in IN_PROGRESS]
        log(f"c: rows={len(rows)} left_in_progress={len(left)} calls={calls} money={money}")
        assert calls <= money["reservations"] <= len(keys)
        ended = _stuck_tick(tmp_path, "w1", dsn)
        assert ended == 0 and not [
            r for r in _rows(dsn) if r[4] in IN_PROGRESS
        ]  # run_tick returns an exit code
        assert money_check(dsn, set(by_run))["reservations"] == money["reservations"]
    finally:
        for x in w.values():
            x.kill()


@pytest.mark.xfail(
    strict=True,
    reason="FINDING A10-1: PostgresStore has no reconnect (store/postgres.py:516 'reconnect-on-error arrives with "
    "S11 hosting'); one pg_terminate_backend leaves the worker answering 503 until it is restarted",
)
def test_c_min_one_terminated_connection_is_survived_without_a_restart(dsn, tmp_path, budget):
    """Minimal form of the finding of (c): one worker, one stored key, ONE pg_terminate_backend of the worker's
    connection, nothing else. Expected by the task text ("recovery"): the worker answers 200 within 15 s without a
    restart. Observed: 503 for as long as it runs. xfail(strict): turns into a failure the day it is fixed."""
    app_name = "fzcmin"
    worker = start_worker(tmp_path, "w1", dsn, app_name=app_name)
    try:
        assert post(worker.port, "k1", document(1))[0] in OK
        wait_quiet(dsn, still_s=1.0)
        assert _terminate(dsn, app_name) >= 1
        deadline, last = time.monotonic() + 15.0, None
        while time.monotonic() < deadline:
            last = post(worker.port, "k1", document(1))[0]
            if last in OK:
                break
            time.sleep(0.25)
        assert last in OK, f"still {last} 15 s after one terminated backend"
    finally:
        worker.kill()


# --- (d) hostile bytes while a legitimate stream runs -----------------------------------------------


def _send_raw(port: int, data: bytes, *, read_s: float = 1.5, chunks: int = 1) -> int | None:
    """Send raw bytes, read the answer's status code (None: nothing came, or the peer reset)."""
    try:
        with socket.create_connection((HOST, port), timeout=5) as sock:
            step = max(1, len(data) // chunks)
            for i in range(0, len(data), step):
                sock.sendall(data[i : i + step])
            sock.settimeout(read_s)
            head = sock.recv(64)
            if head.startswith(b"HTTP/1.") and len(head) >= 12:
                return int(head[9:12])
            return None
    except (OSError, ValueError):
        return None


def _signed_head(body: bytes, length: int | None = None, extra: str = "") -> bytes:
    headers = hmac_v0.sign(body, int(time.time()), SECRET, PREFIX)
    lines = [
        f"POST {PATH} HTTP/1.1",
        f"Host: {HOST}",
        f"Content-Length: {len(body) if length is None else length}",
    ]
    lines += [f"{k}: {v}" for k, v in headers.items()]
    return ("\r\n".join(lines) + "\r\n" + extra + "\r\n").encode()


def _hostile(kind: int, rng: random.Random, port: int) -> tuple[str, int | None]:
    body = wire_body(f"hostile-{rng.randrange(10**9)}", "hostile document " * 8)
    if kind == 0:  # truncated signed body, then close
        return "truncated-body", _send_raw(
            port, _signed_head(body) + body[: len(body) // 2], read_s=0.3
        )
    if kind == 1:  # truncated header block, then close
        return "truncated-head", _send_raw(
            port, _signed_head(body)[: rng.randrange(10, 120)], read_s=0.3
        )
    if kind == 2:  # oversized signed body (cap is 65536)
        big = wire_body(f"big-{rng.randrange(10**9)}", "x" * 200_000)
        return "oversized-body", _send_raw(port, _signed_head(big) + big, chunks=8)
    if kind == 3:  # oversized header value (cap 16384 for the block)
        return "oversized-header", _send_raw(
            port, _signed_head(body, extra="X-Pad: " + "a" * 40_000 + "\r\n")
        )
    if kind == 4:  # garbage bytes
        return "garbage", _send_raw(port, rng.randbytes(rng.randrange(1, 4000)) + b"\r\n\r\n")
    if kind == 5:  # giant request line
        return "giant-line", _send_raw(
            port, b"POST /" + b"a" * 70_000 + b" HTTP/1.1\r\nHost: x\r\n\r\n"
        )
    if kind == 6:  # declared length far above what comes
        return "huge-length", _send_raw(port, _signed_head(body, length=10**9) + body, read_s=0.5)
    if kind == 7:  # two Content-Length headers
        return "two-lengths", _send_raw(
            port, _signed_head(body, extra=f"Content-Length: {len(body)}\r\n") + body
        )
    if kind == 8:  # chunked
        return "chunked", _send_raw(
            port, _signed_head(body, extra="Transfer-Encoding: chunked\r\n") + body
        )
    if kind == 9:  # bad signature
        head = _signed_head(body).replace(
            b"x-hadavin-signature: v0=", b"x-hadavin-signature: v0=00"
        )
        return "bad-signature", _send_raw(port, head + body)
    return "negative-length", _send_raw(port, _signed_head(body, length=-5) + body)


def test_d_hostile_bytes_and_connection_cap_while_a_legitimate_stream_runs(dsn, tmp_path, budget):
    """One worker (256 connection slots, 30 s read deadline). A legitimate stream (one thread, 20 keys, round after
    round, one try per request) runs for the whole test. Phase "cap": 300 idle connections at once (hostile threads
    resting): at most 256 may stay open and the others are closed by the server. Phase 1 (8 s): 40 slow-loris
    connections (a few bytes every 2 s), 100 idle connections and 6 threads of hostile requests (truncated, oversized,
    garbage, bad framing, bad signature). Phase 3: the idle sockets are closed; the stream is answered within 3 s.
    Expected: in phase 1 at least 95% of the stream's requests get 200/202 with the right run id; no hostile request
    is answered 2xx or 5xx; the loris sockets (kept dripping) are cut by the server at the 30 s deadline (29 to 34 s after each one's own opening); one row per
    legitimate key and none from the hostile requests; one reservation per run; the worker is alive."""
    rng_for("d")  # logs the seed; the threads of this test draw from their own seeded streams
    worker = start_worker(tmp_path, "w1", dsn, "--max-running", "8")
    port = worker.port
    keys = {f"legit-{n}": document(n) for n in range(20)}
    stream: list[tuple[str, float, int | None, bool]] = []  # (phase, t, status, answer ok)
    phase = ["warm"]
    stop = threading.Event()
    hostile_seen: Counter = Counter()
    pause = threading.Event()
    lock = threading.Lock()

    def legit() -> None:
        local = random.Random(f"{SEED}-d-legit")
        items = list(keys.items())
        while not stop.is_set():
            key, doc = local.choice(items)
            status, data = post(port, key, doc)
            ok = status in OK
            if ok:
                ok = json.loads(data)["run_id"] == _run_id(SENDER, key)
            with lock:
                stream.append((phase[0], time.monotonic(), status, ok))
            time.sleep(0.02)

    def hostile(seed: int) -> None:
        local = random.Random(f"{SEED}-d-hostile-{seed}")
        while not stop.is_set():
            if pause.is_set():
                time.sleep(0.1)
                continue
            kind, status = _hostile(local.randrange(11), local, port)
            with lock:
                hostile_seen[(kind, status)] += 1

    lorises: list[socket.socket] = []
    first_bytes: dict[int, tuple[float, bytes]] = {}
    drips: list[float] = []
    born: dict[int, float] = {}
    dead: dict[int, tuple[float, str]] = {}
    loris_open_at = time.monotonic()
    idle: list[socket.socket] = []
    try:
        for key, doc in keys.items():  # store every legitimate key first so repeats are cheap reads
            assert post(port, key, doc)[0] in OK
        streamer = threading.Thread(target=legit)
        hostiles = [threading.Thread(target=hostile, args=(i,)) for i in range(6)]
        streamer.start()

        def closed_by_peer(socks: list[socket.socket]) -> int:
            """How many sockets the server has closed: drain what it sent (an answer, then the close)."""
            n = 0
            for s in socks:
                try:
                    while True:
                        r, _, _ = select.select([s], [], [], 0)
                        if not r:
                            break
                        got = s.recv(65536)
                        if got:
                            first_bytes.setdefault(
                                id(s), (time.monotonic() - loris_open_at, got[:24])
                            )
                        else:
                            n += 1
                            break
                except OSError:
                    first_bytes.setdefault(id(s), (time.monotonic() - loris_open_at, b"OSError"))
                    n += 1
            return n

        # phase "cap": 300 idle connections at once on a quiet worker: the 256 slots, then closed at once.
        phase[0] = "cap"
        pause.set()

        t_open, refused = time.monotonic(), 0
        for _ in range(
            300
        ):  # paced: the listen queue of the stdlib server is 5, a faster burst is dropped by the kernel
            try:
                idle.append(socket.create_connection((HOST, port), timeout=2))
            except OSError:
                refused += 1
            time.sleep(0.005)
        time.sleep(1.0)
        closed = closed_by_peer(idle)
        alive = len(idle) - closed
        log(
            f"d: cap: opened {len(idle)} idle in {time.monotonic() - t_open:.1f}s; closed by the server {closed}; alive {alive}; connect failures {refused}"
        )
        time.sleep(0.5)
        for s in idle:
            s.close()
        idle = []
        phase[0] = "1"
        pause.clear()
        # phase 1: lorises, idle sockets, hostile requests (8 s) with the stream running
        loris_open_at = time.monotonic()
        for _ in range(40):
            s = socket.create_connection((HOST, port), timeout=5)
            s.sendall(b"POST /v1/trigger HTTP/1.1\r\nHost: x\r\n")
            born[id(s)] = time.monotonic() - loris_open_at
            lorises.append(s)
            time.sleep(0.005)

        def drip() -> (
            None
        ):  # a few bytes every 2 s on every loris, never enough to finish the header block
            local = random.Random(f"{SEED}-d-drip")
            while not stop.is_set():
                drips.append(round(time.monotonic() - loris_open_at, 1))
                for s in lorises:
                    try:
                        s.sendall(b"X-Drip: 1\r\n"[: local.randrange(1, 4)])
                    except OSError as exc:
                        dead.setdefault(
                            id(s), (round(time.monotonic() - loris_open_at, 1), type(exc).__name__)
                        )
                stop.wait(2.0)

        dripper = threading.Thread(target=drip)
        dripper.start()
        for _ in range(100):  # paced, see the cap phase
            idle.append(socket.create_connection((HOST, port), timeout=5))
            time.sleep(0.005)
        for t in hostiles:
            t.start()
        time.sleep(8.0)
        for s in idle:
            s.close()
        idle = []
        phase[0] = "3"
        recovered = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 6.0:
            status, _data = post(port, "legit-0", keys["legit-0"])
            if status in OK:
                recovered = time.monotonic() - t0
                break
            time.sleep(0.1)
        # the lorises keep dripping, so only the 30 s read deadline (from the accept) can cut them; the stream goes on
        cut_at = None
        while time.monotonic() - loris_open_at < 45.0:
            n_closed = closed_by_peer(lorises)
            if n_closed == len(lorises):
                cut_at = time.monotonic() - loris_open_at
                break
            time.sleep(0.5)
        log(f"d: all {len(lorises)} lorises closed by the server after {cut_at}")
        log(
            f"d: loris first answers (s after open, bytes): {sorted({(round(t, 1), b) for i, (t, b) in first_bytes.items() if i in {id(x) for x in lorises}})[:6]}"
        )
        stop.set()
        streamer.join(30)
        for t in hostiles:
            t.join(30)
        dripper.join(30)
        log(
            f"d: drip rounds {len(drips)}, round times {drips}; send errors {sorted(set(dead.values()))[:5]} ({len(dead)} sockets)"
        )
        by_phase: dict[str, Counter] = {}
        for ph, _t, status, ok in stream:
            by_phase.setdefault(ph, Counter())["ok" if ok else f"bad:{status}"] += 1
        log(f"d: stream by phase { ({k: dict(v) for k, v in by_phase.items()}) }")
        by_kind: dict[str, Counter] = {}
        for (kind, status), n in hostile_seen.items():
            by_kind.setdefault(kind, Counter())[status] += n
        log(f"d: hostile answers { ({k: dict(v) for k, v in by_kind.items()}) }")
        one = by_phase.get("1", Counter())
        total1 = sum(one.values())
        assert total1 >= 20, f"the stream sent only {total1} requests in phase 1"
        assert one["ok"] / total1 >= 0.95, one
        bad = [(k, s) for (k, s) in hostile_seen if s is not None and (200 <= s < 300 or s >= 500)]
        assert bad == [], f"hostile requests answered 2xx or 5xx: {bad}"
        assert alive <= 256 and closed >= 40, (alive, closed)
        assert recovered is not None and recovered < 3.0, recovered
        ages = sorted(first_bytes[id(x)][0] - born[id(x)] for x in lorises if id(x) in first_bytes)
        log(
            f"d: loris age at the server's cut (s): min {ages[0]:.1f} max {ages[-1]:.1f} of {len(ages)}"
        )
        # the 30 s deadline (polled every 0.5 s), not the 15 s stall timeout and not later
        assert (
            cut_at is not None and len(ages) == len(lorises) and 29.0 <= ages[0] and ages[-1] < 34.0
        ), ages
        assert worker.proc.poll() is None
        rows = wait_quiet(dsn, still_s=1.0)
        assert sorted(r[0] for r in rows) == sorted(_run_id(SENDER, k) for k in keys), (
            "extra or missing rows"
        )
        money = money_check(dsn, {r[0] for r in rows})
        log(f"d: rows={len(rows)} money={money}")
        assert money["reservations"] == len(keys) and money["open"] == 0
    finally:
        stop.set()
        for s in lorises + idle:
            s.close()
        worker.kill()
