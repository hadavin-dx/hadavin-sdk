"""Open-loop load driver for the desk's POST /leads. Standard library only. Formats: load_tools/README.md.

Run: python -m load_tools.load_driver --base-url http://127.0.0.1:8765 --scenario burst:200 --log req.jsonl
     scenarios: burst:N (N at one moment) | rate:R:D (R requests/s for D seconds) |
                dupmix:TOTAL:FRACTION (a share of the requests are repeats, some through both doors at once)
Open loop: each request has an INTENDED send time fixed before the run; a slow reply never moves a later request.
The actual send time and the lag are logged, so a driver that could not keep up shows in the log."""

from __future__ import annotations

import http.client
import json
import math
import multiprocessing
import os
import platform
import queue
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentTypeError
from collections import Counter
from pathlib import Path
from typing import Any

try:  # started as a script (python load_tools/load_driver.py): the repository folder is not on the path yet
    from tools.pathconfine import PathRefused, confine
except ImportError:  # a foreign `tools` package WITHOUT these names is dropped and ours is used; a foreign
    # `tools.pathconfine` with the SAME names is NOT detected (it is used as it is)
    _repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(_repo))
    for _name in [n for n in sys.modules if n == "tools" or n.startswith("tools.")]:
        _file = getattr(sys.modules[_name], "__file__", None)  # a `tools` package of another project, already loaded
        if _file is None or not Path(_file).resolve().is_relative_to(_repo):
            del sys.modules[_name]
    from tools.pathconfine import PathRefused, confine

try:  # started as a script without the src folder on the path: it is added (the desk's own file reader is imported)
    from lead_desk.constants import (
        EXIT_BAD_SETTING_OR_PATH,
        EXIT_REFUSED,
        EXIT_UNREACHABLE,
        LOAD_FILE_MAX_BYTES,
        LOAD_LINE_MAX_BYTES,
        LOAD_RATE_MAX,
        LOAD_SECONDS_MAX,
        LOAD_SEED_MAX,
        LOAD_THREADS_MAX,
        LOAD_TOTAL_MAX,
        LOAD_WORKERS_MAX,
        LOOPBACK_HOSTS,
        MAX_TEXT_BYTES,
    )
    from lead_desk.envnum import read_number
    from lead_desk.jsonread import loads_bounded
    from lead_desk.netconnect import connect_bounded
    from lead_desk.regfile import FileRefused, iter_regular_lines, open_output, read_regular_text
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from lead_desk.constants import (
        EXIT_BAD_SETTING_OR_PATH,
        EXIT_REFUSED,
        EXIT_UNREACHABLE,
        LOAD_FILE_MAX_BYTES,
        LOAD_LINE_MAX_BYTES,
        LOAD_RATE_MAX,
        LOAD_SECONDS_MAX,
        LOAD_SEED_MAX,
        LOAD_THREADS_MAX,
        LOAD_TOTAL_MAX,
        LOAD_WORKERS_MAX,
        LOOPBACK_HOSTS,
        MAX_TEXT_BYTES,
    )
    from lead_desk.envnum import read_number
    from lead_desk.jsonread import loads_bounded
    from lead_desk.netconnect import connect_bounded
    from lead_desk.regfile import FileRefused, iter_regular_lines, open_output, read_regular_text

from scripts.http_guard import ReplyTooBig, open_http, read_reply, reason_word
from tools.refusing_args import RefusingParser, bounded_int, http_address

FALLBACK_RETRY_VALUES = (
    0.1,
    1.0,
    30.0,
)  # BURST_BACKOFF_SECONDS, BURST_BACKOFF_MAX_SECONDS, BURST_RETRY_DEADLINE_SECONDS
_backoff: float
_backoff_max: float
_deadline: float
try:  # one source of truth for the retry policy of the burst script (contract.md "Burst script")
    from lead_desk import constants as _constants

    _backoff = _constants.BURST_BACKOFF_SECONDS
    _backoff_max = _constants.BURST_BACKOFF_MAX_SECONDS
    _deadline = _constants.BURST_RETRY_DEADLINE_SECONDS
except ImportError:  # run without src on the path: same values (a test pins them to lead_desk.constants)
    _backoff, _backoff_max, _deadline = FALLBACK_RETRY_VALUES

# ---- config block ----
DOORS = ("form", "webhook")
BACKOFF_SECONDS = _backoff  # wait before the second try; doubles after each try
BACKOFF_MAX_SECONDS = _backoff_max  # the wait never grows past this
ATTEMPT_TIMEOUT_SECONDS = 20.0  # one try
# A patient sender (n8n, a mail relay) keeps trying while the desk restarts: tries are bounded by TIME, not by count.
REQUEST_DEADLINE_SECONDS = _deadline  # no new try after this long since the first try
START_LEAD_SECONDS = 1.5  # time to start the workers before the first intended send
DEFAULT_WORKERS = 4
DEFAULT_THREADS = 64
DUP_BOTH_DOORS_SHARE = 0.5  # of the repeats: this share go through the other door at the same moment
DUP_LATER_MAX_SECONDS = 2.0  # the other repeats come this much later at most
DUPMIX_DEFAULT_RATE = 200.0  # requests per second for dupmix
RETRY_CODES = (503,)  # plus every network error and timeout
ACK_CODES = (200, 201, 202)
ID_PREFIX = "ld"
# A request id is `<prefix>-<n>` and also the part before the @ of the made-up e-mail address (so: letters, digits and
# `. _ -` only, starting and ending with a letter or digit). The longest prefix leaves room for "-" and a counter of
# up to 6 digits inside the 64 characters an e-mail name may have (and far inside SOURCE_REF_MAX, the desk's limit).
ID_PREFIX_FORM = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
ID_PREFIX_MAX = 40
ID_PREFIX_TEXT = f"must be 1 to {ID_PREFIX_MAX} letters, digits, dots, underscores or hyphens"
UNREACHABLE_TEXT = "the desk cannot be reached: every request ended in a connection error (is it running?)"
NOT_LISTENING_TEXT = "the desk cannot be reached: nothing answers at that address (is it running?); no request was sent"
STOPPED_EARLY_TEXT = (
    "the run was stopped early: {n} of {total} requests were never sent or were given up, because the first tries "
    "got no answer; the desk answered only later, so this run does not show how the desk handles those requests "
    "(run it again)"
)
GIVEN_UP_TEXT = (
    "{n} of {total} requests were not accepted: {given_up} until their retry time was over (gave_up deadline in the "
    "log), {stopped} because the run was stopped early, {errors} because the driver itself failed (gave_up "
    "driver_error); the desk did not take them, so this run is not a pass "
    "(exit code 3); run check_invariants.py on the log"
)
CONNECT_PROBE_SECONDS = 1.0  # one look for a listener before any worker starts (nothing is sent on it)
STOP_LOOK_SECONDS = 0.5  # a worker that waits for its schedule looks at the stop flag this often
STOP_AFTER_ERRORS_PER_THREAD = 2  # stop all workers after this many connection errors per thread with no success yet
EMAIL_DOMAIN = "example.com"
TCP_STATE_TIME_WAIT = "06"
MIN_TCP_LINE_FIELDS = 4
DUPMIX_RATE_INDEX = 2


def _retry_after(value: str | None) -> float | None:
    """The Retry-After header as seconds; an HTTP date, a negative number or junk gives None."""
    try:
        seconds = float(value) if value is not None else None
    except ValueError:
        return None
    return seconds if seconds is not None and seconds >= 0 else None


def next_wait(wait: float, retry_after: float | None, left: float) -> float:
    """Seconds to sleep before the next try: the doubling back-off, or the desk's Retry-After if longer, never more than
    BACKOFF_MAX_SECONDS and never past the deadline. (Same rule as demo_only.burst.next_wait; a test pins both.)"""
    asked = wait if retry_after is None else max(wait, retry_after)
    return max(0.0, min(asked, BACKOFF_MAX_SECONDS, left))


def _post(url: str, body: bytes) -> tuple[int | None, str | None, dict[str, Any], float | None]:
    """One try. Returns (code, error class name, parsed reply, Retry-After seconds). A 4xx/5xx reply is a code, not an
    error."""
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})  # noqa: S310 (loopback, from args)

    def parse(raw: bytes) -> dict[str, Any]:
        try:
            obj = loads_bounded(raw or b"{}")
        except ValueError:
            return {}
        return obj if isinstance(obj, dict) else {}

    try:
        # http and https only, checked before the opener, which knows no other scheme; no proxy (loopback)
        with open_http(req, ATTEMPT_TIMEOUT_SECONDS, use_proxy=False) as r:
            status = int(r.status)
            try:
                return status, None, parse(read_reply(r)), None
            except ReplyTooBig:  # the status counts; a body over the limit is not used (the receipt fields stay empty)
                return status, None, {}, None
    except urllib.error.HTTPError as e:
        after = _retry_after(e.headers.get("Retry-After"))
        try:
            return int(e.code), None, parse(read_reply(e)), after
        except (OSError, ValueError, http.client.HTTPException):  # a body that broke off or is too big: the code counts
            return int(e.code), None, {}, after
    except urllib.error.URLError as e:
        return None, reason_word(e.reason), {}, None
    except (OSError, ValueError, http.client.HTTPException):  # reset, timeout, half-read reply, bad status line
        return None, "error", {}, None


def send_with_retries(url: str, item: dict[str, Any]) -> dict[str, Any]:
    """Send one intended request; retry 503 and network errors with doubling waits (BACKOFF_SECONDS up to
    BACKOFF_MAX_SECONDS; a Retry-After is honoured up to that maximum) until the reply is final or
    REQUEST_DEADLINE_SECONDS have passed since the first try.
    An answer other than 503 stops the retries (a 200/201/202 is never sent twice). A request still not answered when
    the deadline ends is logged `accepted: false`, `gave_up: "deadline"` with the last code or error as final_status.
    After every try `_note_attempt(code)` is asked (code None: a connection error or timeout); a True answer stops the
    retries at once and the line says `gave_up: "stopped"` (the run is being ended because the desk answered nothing at
    all).
    Returns the log line (format in README.md)."""
    body = json.dumps(item["envelope"]).encode()
    attempts: list[dict[str, Any]] = []
    first = time.monotonic()  # the deadline and the latencies use this one
    first_ts = time.time()  # wall-clock: stored as sent_ts, compared with the schedule's epoch seconds
    reply: dict[str, Any] = {}
    wait = BACKOFF_SECONDS
    after: float | None = None
    stopped = False
    while True:
        t0 = time.time()  # wall-clock: stored in the log line
        t0_mono = time.monotonic()
        code, error, reply, after = _post(url, body)
        attempts.append({"ts": t0, "code": code, "error": error, "latency_s": round(time.monotonic() - t0_mono, 4)})
        stop_now = _note_attempt(code)  # FIRST and for every code: any answer (200, 202, 4xx, 503) marks the desk as
        # answering (the retry test below must not skip it)
        if not (code in RETRY_CODES or code is None):
            break
        if stop_now:
            stopped = True
            break
        left = REQUEST_DEADLINE_SECONDS - (time.monotonic() - first)
        if left <= 0:
            break
        time.sleep(next_wait(wait, after, left))
        wait = min(wait * 2, BACKOFF_MAX_SECONDS)
    last = attempts[-1]
    final = last["code"] if last["code"] is not None else last["error"]
    accepted = last["code"] in ACK_CODES
    return {
        "request_id": item["request_id"],
        "door": item["door"],
        "intended_ts": item["intended_ts"],
        "sent_ts": first_ts,
        "lag_s": round(first_ts - item["intended_ts"], 4),  # replaced by the worker with the monotonic lag
        "done_ts": time.time(),  # wall-clock: calendar stamp
        "scenario": item["scenario"],
        "kind": item["kind"],
        "attempts": attempts,
        "attempt_count": len(attempts),
        "first_attempt_ts": attempts[0]["ts"],
        "last_attempt_ts": last["ts"],
        "codes": [a["code"] if a["code"] is not None else a["error"] for a in attempts],
        "final_status": final,
        "accepted": accepted,
        "gave_up": "stopped"
        if stopped
        else ("deadline" if (last["code"] is None or last["code"] in RETRY_CODES) else None),
        "receipt_id": reply.get("receipt_id"),
        "verdict": reply.get("verdict"),
    }


def _driver_error_line(item: dict[str, Any], error: BaseException) -> dict[str, Any]:
    """A request the driver itself could not finish still gets its log line (check 1 then reports it lost)."""
    now = time.time()  # wall-clock: calendar stamp
    return {
        "request_id": item["request_id"],
        "door": item["door"],
        "intended_ts": item["intended_ts"],
        "sent_ts": now,
        "lag_s": round(now - item["intended_ts"], 4),
        "done_ts": now,
        "scenario": item["scenario"],
        "kind": item["kind"],
        "attempts": [],
        "attempt_count": 0,
        "first_attempt_ts": None,
        "last_attempt_ts": None,
        "codes": [],
        "final_status": "driver:error",
        "accepted": False,
        "gave_up": "driver_error",
        "receipt_id": None,
        "verdict": None,
    }


def _envelope(door: str, ref: str, email: str) -> dict[str, Any]:
    payload = {"name": f"Load {ref}", "email": email, "phone": "555 0100", "message": "Please call me."}
    return {"source": door, "source_ref": ref, "payload": payload}


def _item(door: str, ref: str, ts: float, scenario: str, kind: str) -> dict[str, Any]:
    email = f"{ref}@{EMAIL_DOMAIN}"
    return {
        "request_id": ref,
        "door": door,
        "intended_ts": ts,
        "scenario": scenario,
        "kind": kind,
        "envelope": _envelope(door, ref, email),
    }


SCENARIO_FORM = "bad scenario: use burst:N, rate:R:D or dupmix:TOTAL:FRACTION[:RATE] (numbers only)"
SCENARIO_NUMBERS = "bad scenario: numbers must be positive (a fraction is 0 to 1)"  # fixed: no typed text
SCENARIO_TOO_BIG = "bad scenario: a number is too big (see the limits in lead_desk/constants.py: LOAD_*_MAX)"


def parse_scenario(text: str) -> tuple[str, list[float]]:
    """burst:N | rate:R:D | dupmix:TOTAL:FRACTION[:RATE]. Returns (name, numbers); raises ValueError."""
    parts = text.split(":")
    try:
        name, nums = parts[0], [read_number(p, float) for p in parts[1:]]  # ASCII only: no `1_0`
    except ValueError:  # Python's own text repeats the word that was typed: not used
        raise ValueError(SCENARIO_FORM) from None
    want = {"burst": (1, 1), "rate": (2, 2), "dupmix": (2, 3)}
    if name not in want or not want[name][0] <= len(nums) <= want[name][1]:
        raise ValueError(SCENARIO_FORM)
    if not all(math.isfinite(x) for x in nums):  # "nan" and "inf" are numbers to float(): int(nan) is a ValueError
        raise ValueError(SCENARIO_NUMBERS)  # and int(inf) an OverflowError, each with a traceback
    positive = nums[:2] if name != "dupmix" else [nums[0], *nums[2:]]  # a dupmix fraction may be 0
    if any(x <= 0 for x in positive) or (name == "dupmix" and not 0 <= nums[1] < 1):
        raise ValueError(SCENARIO_NUMBERS)
    if _planned_total(name, nums) < 1:  # burst:0.5 or rate:0.1:1 would plan no request at all
        raise ValueError(SCENARIO_NUMBERS)
    if _too_big(name, nums):
        raise ValueError(SCENARIO_TOO_BIG)
    return name, nums


def _planned_total(name: str, nums: list[float]) -> int:
    """How many requests the numbers plan (the count build_schedule makes). `nums` are finite; a product that
    overflows to infinity plans nothing here and is refused as too big afterwards."""
    if name != "rate":
        return int(nums[0])
    product = nums[0] * nums[1]
    return int(product) if math.isfinite(product) else LOAD_TOTAL_MAX + 1


def _too_big(name: str, nums: list[float]) -> bool:
    """True when a number is above the limits in constants.py."""
    if name == "burst":
        return nums[0] > LOAD_TOTAL_MAX
    if name == "rate":
        return nums[0] > LOAD_RATE_MAX or nums[1] > LOAD_SECONDS_MAX or nums[0] * nums[1] > LOAD_TOTAL_MAX
    rate = nums[DUPMIX_RATE_INDEX] if len(nums) > DUPMIX_RATE_INDEX else DUPMIX_DEFAULT_RATE
    return nums[0] > LOAD_TOTAL_MAX or rate > LOAD_RATE_MAX or nums[0] / rate > LOAD_SECONDS_MAX


def build_schedule(scenario: str, t0: float, prefix: str, seed: int) -> list[dict[str, Any]]:
    """The whole open-loop schedule, fixed before anything is sent. Sorted by intended time."""
    name, nums = parse_scenario(scenario)
    try:
        id_prefix(prefix)
    except ArgumentTypeError:
        raise ValueError(f"bad id prefix: {ID_PREFIX_TEXT}") from None
    rng = random.Random(seed)  # noqa: S311 (not for security: spreads made-up requests)
    items: list[dict[str, Any]] = []
    if name == "burst":
        for i in range(int(nums[0])):
            items.append(_item(DOORS[i % len(DOORS)], f"{prefix}-{i}", t0, scenario, "first"))
    elif name == "rate":
        rate, seconds = nums
        for i in range(int(rate * seconds)):
            items.append(_item(DOORS[i % len(DOORS)], f"{prefix}-{i}", t0 + i / rate, scenario, "first"))
    else:
        total = int(nums[0])
        repeats = min(round(total * nums[1]), total - 1)  # at least one first request for a repeat to repeat
        rate = nums[DUPMIX_RATE_INDEX] if len(nums) > DUPMIX_RATE_INDEX else DUPMIX_DEFAULT_RATE
        firsts = total - repeats
        if firsts < 1:
            raise ValueError("dupmix needs at least one first request")
        for i in range(firsts):
            items.append(_item(DOORS[i % len(DOORS)], f"{prefix}-{i}", t0 + i / rate, scenario, "first"))
        for _ in range(repeats):
            base = items[rng.randrange(firsts)] if firsts else items[0]
            if rng.random() < DUP_BOTH_DOORS_SHARE:
                other = DOORS[1 - DOORS.index(base["door"])]
                items.append(_item(other, base["request_id"], base["intended_ts"], scenario, "other_door_same_moment"))
            else:
                later = base["intended_ts"] + rng.uniform(0, DUP_LATER_MAX_SECONDS)
                items.append(_item(base["door"], base["request_id"], later, scenario, "repeat_later"))
    items.sort(key=lambda it: (it["intended_ts"], it["door"], it["request_id"]))
    return items


def id_prefix(text: str) -> str:
    """An argparse `type=` for --id-prefix (and the check inside `build_schedule`): ASCII letters, digits, dots,
    underscores and hyphens, 1 to ID_PREFIX_MAX characters. A longer or odder prefix would make ids the desk refuses
    (a refused request is then counted as a result of the DESK), or an e-mail name that is not an address."""
    if len(text) > ID_PREFIX_MAX or not ID_PREFIX_FORM.fullmatch(text) or not text.isascii():
        raise ArgumentTypeError(ID_PREFIX_TEXT)
    return text


def seconds_until(intended_ts: float, base_wall: float, base_mono: float) -> float:
    """Seconds from now to the intended calendar moment, counted on the monotonic clock from one wall-clock reading
    (`base_wall`, taken together with `base_mono`): a later step of the wall clock does not move the schedule."""
    return intended_ts - base_wall - (time.monotonic() - base_mono)


# Shared by the threads of one worker process and, through the pool initializer, by all worker processes of one run:
# when the first STOP_AFTER_ERRORS_PER_THREAD x threads tries all ended in a connection error and no try has had any
# answer yet, every worker stops (the rest of the schedule is logged as `driver:stopped`, no more request is sent).
_STOP: Any = threading.Event()
_ANSWERED: Any = threading.Event()
_ERRORS: Any = None  # a shared counter (multiprocessing.Value) in a run; None = no limit (a direct call of _worker)
_STOP_LIMIT = 0


def _init_worker(stop: Any, answered: Any, errors: Any, limit: int) -> None:
    global _STOP, _ANSWERED, _ERRORS, _STOP_LIMIT  # noqa: PLW0603 (one set of shared flags per worker process)
    _STOP, _ANSWERED, _ERRORS, _STOP_LIMIT = stop, answered, errors, limit


def _note_attempt(code: int | None) -> bool:
    """Called after every try. True = end the run: nothing has answered and the error limit is reached."""
    if code is not None:
        _ANSWERED.set()
        return False
    if _ERRORS is not None and _STOP_LIMIT > 0:
        with _ERRORS.get_lock():
            _ERRORS.value += 1
            reached = _ERRORS.value >= _STOP_LIMIT
        if reached and not _ANSWERED.is_set():
            _STOP.set()
    return _STOP.is_set() and not _ANSWERED.is_set()


def _stopped_line(item: dict[str, Any]) -> dict[str, Any]:
    """A request that was never sent because the run was stopped: still one log line (check 1 reports it lost)."""
    line = _driver_error_line(item, RuntimeError("stopped"))
    line["final_status"] = "driver:stopped"
    line["gave_up"] = "stopped"
    return line


def desk_listening(base_url: str) -> bool:
    """True when something accepts a connection at the host and port of `base_url` within CONNECT_PROBE_SECONDS.
    Nothing is sent on the connection."""
    parts = urllib.parse.urlsplit(base_url)
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
        # the look-up of the host name is inside the same limit (lead_desk.netconnect: one place for this job)
        connect_bounded(parts.hostname or "", port, CONNECT_PROBE_SECONDS).close()
        return True
    except (OSError, ValueError):
        return False


def _worker(args: tuple[int, str, list[dict[str, Any]], int, Path]) -> None:
    """One worker process: threads take its items in intended-time order, wait until the intended moment, send."""
    index, url, items, threads, part = args
    base_wall = time.time()  # wall-clock: the one reading that turns a schedule's calendar time into a monotonic wait
    base_mono = time.monotonic()
    work: queue.Queue[dict[str, Any]] = queue.Queue()
    for it in items:
        work.put(it)
    lock = threading.Lock()
    out = open_output(part, "w", encoding="utf-8")

    def run() -> None:
        while True:
            try:
                it = work.get_nowait()
            except queue.Empty:
                return
            wait = seconds_until(it["intended_ts"], base_wall, base_mono)
            while wait > 0 and not _STOP.is_set():  # a stop also ends a wait for the schedule (looked at every 0.5 s)
                time.sleep(min(wait, STOP_LOOK_SECONDS))
                wait = seconds_until(it["intended_ts"], base_wall, base_mono)
            stopped = _STOP.is_set()
            # lag from the monotonic schedule (a wall-clock step cannot change it); negative = woke a little early
            lag = -seconds_until(it["intended_ts"], base_wall, base_mono)
            try:
                line = _stopped_line(it) if stopped else send_with_retries(url, it)
            except Exception as e:  # noqa: BLE001 (a request is never dropped: it is logged as a driver error)
                line = _driver_error_line(it, e)
            line["lag_s"] = round(lag, 4)
            line["worker"] = index
            with lock:
                out.write(json.dumps(line) + "\n")
                out.flush()

    pool = [threading.Thread(target=run) for _ in range(max(1, min(threads, len(items))))]
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    out.close()


UNREADABLE = "unreadable"  # what a machine fact holds when its kernel file could not be read (never a silent null)


def _count_time_wait() -> int | str:
    total = 0
    found = False
    for name in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            counted = 0
            for n, ln in enumerate(iter_regular_lines(name, LOAD_FILE_MAX_BYTES, LOAD_LINE_MAX_BYTES)):
                fields = ln.split()
                if n and len(fields) >= MIN_TCP_LINE_FIELDS and fields[3] == TCP_STATE_TIME_WAIT:  # row 0: the header
                    counted += 1
        except (OSError, ValueError):
            continue
        found = True
        total += counted
    return total if found else UNREADABLE


def _read_int(kernel_file: str) -> int | str:
    """One whole number from a fixed kernel file (/proc, /sys) named by this module, never by the command line."""
    try:
        return int(read_regular_text(kernel_file, MAX_TEXT_BYTES).strip())
    except (OSError, ValueError):
        return UNREADABLE


def machine_facts() -> dict[str, Any]:
    """Facts that explain a result: recorded once at the start of a run."""
    mem: dict[str, int | str] = {}
    try:
        for ln in read_regular_text("/proc/meminfo", MAX_TEXT_BYTES).splitlines():
            key, _, rest = ln.partition(":")
            if key in ("MemTotal", "MemAvailable"):
                mem[key + "_kb"] = int(rest.split()[0])
    except (OSError, ValueError, IndexError):
        pass
    for name in ("MemTotal_kb", "MemAvailable_kb"):
        mem.setdefault(name, UNREADABLE)  # a missing number is said so in the facts file
    soft = hard = nproc_soft = nproc_hard = None  # the `resource` module does not exist on Windows
    if sys.platform != "win32":
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        nproc_soft, nproc_hard = resource.getrlimit(resource.RLIMIT_NPROC)
    return {
        "ts": time.time(),  # wall-clock: calendar stamp
        "time_wait_count": _count_time_wait(),
        "ulimit_n": {"soft": soft, "hard": hard},
        "somaxconn": _read_int("/proc/sys/net/core/somaxconn"),
        "nproc": {"cpus": os.cpu_count(), "ulimit_u_soft": nproc_soft, "ulimit_u_hard": nproc_hard},
        "memory": mem,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def stopped_count(lines: list[dict[str, Any]]) -> int:
    """THE one place that decides 'the run was stopped early': the requests the stop took out of the run, both the
    ones never sent (`driver:stopped`, from `_stopped_line`) and the ones already retrying when the stop was set
    (`send_with_retries`, final status `error` or a code). Both kinds carry `gave_up == "stopped"` and nothing else
    does; the summary and the exit code read only this count."""
    return sum(1 for d in lines if d.get("gave_up") == "stopped")


def deadline_count(lines: list[dict[str, Any]]) -> int:
    """Requests that were tried until their retry time was over and never accepted (`gave_up == "deadline"`). Since r7j
    they end the run with exit code 3 and one line (see `exit_code_and_line`); the log keeps them and
    `check_invariants.py` also fails on a request that was never accepted."""
    return sum(1 for d in lines if d.get("gave_up") == "deadline")


def driver_error_count(lines: list[dict[str, Any]]) -> int:
    """Requests the driver itself could not finish (`gave_up == "driver_error"`, from `_driver_error_line`): the desk
    never answered them, so the run is not a pass either; they end the run with exit code 3 like the other kinds."""
    return sum(1 for d in lines if d.get("gave_up") == "driver_error")


def desk_unreachable(lines: list[dict[str, Any]]) -> bool:
    """True when the log has requests and EVERY try of EVERY request ended in a connection error (no reply with a code
    at all): the desk is not running, or not on that address. Such a run proves nothing about the desk."""
    return bool(lines) and all(d.get("attempts") and all(a["code"] is None for a in d["attempts"]) for d in lines)


def run(
    base_url: str, scenario: str, log: Path, facts_path: Path, workers: int, threads: int, seed: int, prefix: str
) -> dict[str, Any]:
    log = confine(log, what="--log")  # the real location, checked; the part files and the writes below use only this
    facts_path = confine(facts_path, what="--facts")
    facts = machine_facts()
    t0 = time.time() + START_LEAD_SECONDS  # wall-clock: calendar stamp
    schedule = build_schedule(scenario, t0, prefix, seed)
    url = base_url.rstrip("/") + "/leads"
    workers = max(1, min(workers, len(schedule) or 1))
    # each part file is checked like the log: a pipe left under that name would block the worker that opens it
    parts = [confine(log.with_name(f"{log.name}.part{k}"), what="--log") for k in range(workers)]
    # the paths are checked first (no network); then one probe, before any worker starts or file is written
    if not desk_listening(base_url):
        return {
            "unreachable": True,
            "not_listening": True,
            "intended": len(schedule),
            "logged": 0,
            "final_status": {},
            "max_lag_s": 0.0,
            "last_intended_ts": None,
        }
    jobs = [(k, url, schedule[k::workers], threads, parts[k]) for k in range(workers)]
    facts.update(
        scenario=scenario,
        workers=workers,
        threads_per_worker=threads,
        intended_requests=len(schedule),
        max_in_flight=workers * threads,
        first_intended_ts=t0,
        seed=seed,
        qualifier=os.environ.get("DESK_QUALIFIER", ""),  # lets the checker know the AI step was live
    )
    with open_output(facts_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    ctx = multiprocessing.get_context("spawn")
    stop, answered, errors = ctx.Event(), ctx.Event(), ctx.Value("i", 0)
    limit = STOP_AFTER_ERRORS_PER_THREAD * threads
    with ctx.Pool(workers, initializer=_init_worker, initargs=(stop, answered, errors, limit)) as pool:
        pool.map(_worker, jobs, chunksize=1)
    lines: list[dict[str, Any]] = []
    for p in parts:
        for x in iter_regular_lines(p, LOAD_FILE_MAX_BYTES, LOAD_LINE_MAX_BYTES, LOAD_TOTAL_MAX):
            if x.strip():
                lines.append(loads_bounded(x))
        if len(lines) > LOAD_TOTAL_MAX:
            raise FileRefused("the file is too big")
        p.unlink()
    lines.sort(key=lambda d: (d["intended_ts"], d["door"], d["request_id"]))
    with open_output(log, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(d) + "\n" for d in lines))
    finals = Counter(str(d["final_status"]) for d in lines)
    lag = max((d["lag_s"] for d in lines), default=0.0)
    return {
        "unreachable": desk_unreachable(lines) or (stop.is_set() and not answered.is_set()),
        "intended": len(schedule),
        "logged": len(lines),
        "final_status": dict(finals),
        "given_up": deadline_count(lines),  # requests not accepted before their retry time was over (exit code 3)
        "driver_errors": driver_error_count(lines),  # requests the driver could not finish (exit code 3)
        "stopped": stopped_count(lines),  # requests never sent or given up because the run was stopped early
        "max_lag_s": lag,
        "last_intended_ts": max((d["intended_ts"] for d in lines), default=None),
    }


def exit_code_and_line(summary: dict[str, Any]) -> int:
    """THE one place that decides the exit code of a run that reached the desk: 3 and ONE line on stderr (the same
    count in the line as in the decision) when any request was given up at its retry deadline, taken out by the stop or
    ended in a driver error, else 0. The count in the line is the count of all three kinds."""
    given_up, stopped, total = summary["given_up"], summary["stopped"], summary["intended"]
    errors = summary.get("driver_errors", 0)
    if not (given_up or stopped or errors):
        return 0
    if not (given_up or errors):
        print(f"ERROR: {STOPPED_EARLY_TEXT.format(n=stopped, total=total)}", file=sys.stderr)
    else:
        text = GIVEN_UP_TEXT.format(
            n=given_up + stopped + errors, total=total, given_up=given_up, stopped=stopped, errors=errors
        )
        print(f"ERROR: {text}", file=sys.stderr)
    return EXIT_UNREACHABLE


def main(argv: list[str] | None = None) -> int:
    ap = RefusingParser(prog="load_tools.load_driver")
    ap.add_argument(
        "--base-url",
        type=http_address(LOOPBACK_HOSTS),
        required=True,
        help="desk base URL on this computer, e.g. http://127.0.0.1:8765 (another host is refused)",
    )
    ap.add_argument("--scenario", required=True, help="burst:N | rate:R:D | dupmix:TOTAL:FRACTION[:RATE]")
    ap.add_argument("--log", type=Path, required=True, help="request log (JSONL), one line per intended request")
    ap.add_argument("--facts", type=Path, help="machine facts JSON (default: <log>.facts.json)")
    ap.add_argument("--workers", type=bounded_int(1, LOAD_WORKERS_MAX), default=DEFAULT_WORKERS)
    ap.add_argument(
        "--threads",
        type=bounded_int(1, LOAD_THREADS_MAX),
        default=DEFAULT_THREADS,
        help="threads in each worker process",
    )
    ap.add_argument("--seed", type=bounded_int(-LOAD_SEED_MAX, LOAD_SEED_MAX), default=1)
    ap.add_argument(
        "--id-prefix", type=id_prefix, default=ID_PREFIX, help="request ids are <prefix>-<n>; change it for every run"
    )
    a = ap.parse_args(argv)
    try:
        parse_scenario(a.scenario)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_REFUSED
    facts = a.facts or a.log.with_name(a.log.name + ".facts.json")
    try:
        summary = run(a.base_url, a.scenario, a.log, facts, a.workers, a.threads, a.seed, a.id_prefix)
    except PathRefused as e:  # a log or facts path that cannot be used (exit 4, a bad path): nothing sent or written
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_BAD_SETTING_OR_PATH
    if summary["unreachable"]:  # the summary of a run that reached nothing is not printed
        print(f"ERROR: {NOT_LISTENING_TEXT if summary.get('not_listening') else UNREACHABLE_TEXT}", file=sys.stderr)
        return EXIT_UNREACHABLE
    print(json.dumps(summary, sort_keys=True))
    code = exit_code_and_line(summary)  # an exit-3 run prints its ONE ERROR line there and no other line
    if code == 0 and summary["logged"] != summary["intended"]:  # check_invariants.py check 1 fails such a log too
        print(f"WARNING: {summary['intended']} requests intended, {summary['logged']} logged", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
