"""Mutants of the signed trigger endpoint (`triggers/endpoint.py`), its worker half (`triggers/worker.py`), the quiet
server classes (`triggers/server.py`) and the crash helper of step E (`testing/crash.py`), run by the P1m runner
(`tools/mutation_runner.py`). Not collected by pytest.

Each mutant reverts ONE guard in a temp copy of the package; the test in `killer` must be the one that fails first, with a
first failing line that holds `expect`. Thirty-three groups (G32 is E1: ten mutants, G33 is E1 fix2: six), one per guarantee:

    G1  the dedupe key: tenant, sender and the NUL separator are all part of `derive_run_id`
    G2  the payload-hash conflict: the document hash is in `trigger_ref`, and `Runner.start` compares it on a hit
    G3  the ack comes only after the run row exists; the slot is held until the loop ends; no slot is not a 503 at once
    G4  the timestamp check: the endpoint hands its own clock to the verifier
    G5  the signature is verified before the body is parsed
    G6  the secrets are checked at start: minimum length, and distinct across senders
    G7  the crash helper: disarm before the crash, a `BaseException`, the pytest-only gate, before and after not swapped
    G8  the quiet server: an empty 503 body, nothing on stderr, an empty refusal, no Server header with the Python version
    G9  the secrets at start, two later rules: at most two per sender, no whitespace around a value
    G10 the timestamp boundary: the clock is cut to whole seconds before the window is checked
    G11 the wait with no free slot: the pause doubles, and a waiting request takes a slot that frees
    G12 bind and shutdown: loopback unless the switch is set, no IPv6, no trigger_ref in the 409 line, SIGTERM stops
    G13 the endpoint's own checks: every secret tried, exactly one sender matches, MAX_SENDERS, sender and secret ids line
        up, the upper bound of max_body_bytes, the size cap before the body is read
    G14 the rules for a secret value: no byte-order mark or zero-width character, no control character, no repeated value
    G15 the quiet server: a timeout on the request line or in the headers is a stalled client, 414, the request_version
        default, and the `_answer_begun` flag (set in send_error, read in `_refuse_stalled`)
    G16 the quiet server: HTTP 2.0 and up is 400, no version is closed quietly, underscore names, two Content-Length,
        Transfer-Encoding, and the process environment kept out of the request (`os_environ = {}`)
    G17 Retry-After on a 503, and DEBUG for a request that did not verify
    G18 the cap on waiting requests (`max_waiting`) and its release, `runner.close()` in `serve`, the close warning, and a
        waiter that is told 503 when the Runner is closed
    G19 store errors told from bugs (by type), no 409 from an exception type, the BaseException of a run thread, the
        memory-store warning
    G20 the bounds of Runner: max_running, ack_wait_s, poll_s, max_waiting, and make_app turning them into a ConfigError
    G21 the quiet server's own bounds and hooks: the connection cap, the absolute read deadline (against a per-recv
        timeout), `handle_error`, `process_request_thread`
    G22 `Runner.close` sets the closed flag (read the log after a close: no ERROR line, the pool is never asked)
    G23 the 409 of `_answer` on the agent of the row, and on the principal (two mutants, one killer test with two params)
    G24 the header set of a refusal (a 401 with an `X-Reason` header)
    G25 `sender_map`: a sender id listed twice
    G26 `parse_body`: a duplicate member, and exactly the fields key and document
    G27 `_content_length`: ASCII digits only
    G28 `check_bind`: only the value True is the switch for a non-loopback host
    G29 `check_senders`: agent not qualified, principal unknown, principal not of kind service
    G30 the size cap is on the raw body bytes (the guard itself; not a cap on the decoded document), G31 an empty document
        is a document (`parse_body` does not refuse it)
    G32 E1 (d-fix6, d-fix8): the 409 audit event and its cap, /health, the degraded start and its recovery, the no-audit warning
    G33 E1 fix2 (d-fix9): `_close_app` in `_recover`, the ping set after start, the 2 s audit wait, `DEGRADED_FATAL_AFTER`,
        the per-sender cap, an unsigned request is never a sender

G4: the five-minute window itself lives inside `approvals/hmac_v0.verify`. That file is NOT mutated and not edited here: the
mutant is on the endpoint side only (the request's own timestamp is passed as "now", so the window can never close).

G5a and G5b are ONE mutant (the same text change) with two killers, seen as the status (G5a) and by the parse spy (G5b).
G20a and G20c are MESSAGE GUARDS: with the guard gone a later check still refuses the same value (the pool, or the
POLL_S_MIN bound), so only the text of the ValueError differs; their `expect` is the failed `match=`.
G12d and G18c are POSIX killers: their tests skip on win32 (no SIGTERM there). On win32 this script does NOT run them: it
prints `NOT RUN HERE (win32, ...)` for each, lists them at the end and exits 3 (never 0, never a SURVIVED row).
G7a: line 178 of `test_n2_before_crashes_and_nothing_was_written` is `assert fired == (..) and armed() is None`; only the
second conjunct fails under the mutant, so the first E line is `assert (('...',) == ('...',)` with both sides equal, which
no other fault gives (the `expect` carries the `AssertionError: assert ((` prefix).
G29b (d-fix3): without the unknown-principal refusal the next line, `_field(principal, "kind", ..)`, raises a ConfigError with another text, so the kill is the failed `match=` (a message guard).

One test of `tests/triggers/test_worker.py`, `test_main_without_a_triggers_block_exits_2`, takes the fixture `cfg_dir` from
`tests/conftest.py`. The runner runs pytest with `--noconftest` on purpose, so under it that test errors at setup and the
unmutated copy would not pass. It kills no mutant of this list and is deselected for every run here, the baseline included
(`NEEDS_CONFTEST`, handed to the pytest child as `PYTEST_ADDOPTS`); no file is changed for it. When that test builds its
config folder without the conftest fixture, delete `NEEDS_CONFTEST` and the two lines that use it.

G1 has no mutant for the guard `"\\0" in value` of `derive_run_id`: dropping it changes nothing (the two field patterns
already refuse a NUL, so every bad triple is still a ValueError and the mutant SURVIVES). The separator mutant is G1c.

LEFT OUT of G13 to G20, found by a probe run (each was run once and SURVIVED):
  - the `len(senders) > MAX_SENDERS` line of `make_wsgi` is EQUIVALENT: with it gone, `check_secrets` (called next) refuses
    the same nine senders with the same text ("more than 8 trigger senders"). The check of `check_secrets` is G13c.
  - `if closed: return NO_ACK` in `_decide` (the line after `_submit`): EQUIVALENT in the answer. With it gone the call goes
    on with `job` None and the loop's own `if self._closed: return NO_ACK` gives the same 503 at its first look (one more
    row read, no other difference). Not run.
  (`QuietServer.handle_error` and `self._closed = True` were here as TEST MISSING; the tests now exist: G21c and G22.)
  G19c is the "409 from the exception type" mutant of the lead's list: a StaleState of `get_run` is turned into 409; the
  loop's own exceptions never reach `_decide` (`_run` swallows them), so the type check can only be placed there.

G8 to G12 have no mutant left out: each of their thirteen is killed. G8a takes away the two class lines `error_headers`
and `error_body` together (one piece of text). G8c is pinned to the stalled-client case: there the status line stays
`400 Bad Request` and the first failing line is the HTML body (with a broken request line the status line fails first).

Two test files run a child process: `tests/triggers/test_t5_process.py` (G12d, case D3) and one test of `test_worker.py`.
`test_t5_process.py` imports `make_cfg` from `tests/conftest.py` as a plain module and takes no fixture from it, so it
runs under `--noconftest` as it is (the whole `tests` folder is in the copy). G12d waits out the 15 seconds of D3.
Weak `expect` fragments (the line is a bare "DID NOT RAISE ValueError", or a bare boolean, so the kill rests on `pinned`):
G13c to G13e, G14a to G14c, G18c ("assert (False)"), G20b, G20d to G20i, G25, G26a, G26b, G28, G29a, G29c, G21c and G21d (`AssertionError: []`: the log is empty). The `expect` of G11a is weak: the assertion message is the number of store reads, about 100 and not the same in every
run, so only `AssertionError: ` is matched and the kill is tied to its test by `pinned` alone.

Most killer assertions are bare (no message text), so `expect` is then a fragment of the compared VALUES in the first failing
line (`400 == 401`, `== (409, {})`), and the kill is tied to its test by `pinned`. Run from the repo root (no database, no
network). The first lines are `# sha256` of the trigger files, `crash.py` and this script. Every `old` text must occur
exactly once in its file or the script stops with `ERROR anchor ...` (exit 2) before anything runs. Exit 0 only when every
mutant not on the KNOWN SURVIVORS list is good (KILLED, or CRASH where allowed) and every listed one still SURVIVES (a
listed mutant that gets killed is a problem: take it off the list); the list (empty if every mutant has a killer test) is
printed. A mutant with no killer test is written `mutant(..., known_survivor=True)`: its whole test file runs and the
expected verdict is SURVIVED. The last lines are `N killed, M crash-accepted (names), K known survivors` and
`N of N run are as expected; problems: []`. The run is POSIX (see G12d and G18c above):

    uv run python tests/endpoint_mutants.py            # all; exit 1 if any is not as expected
    uv run python tests/endpoint_mutants.py G3         # only names that hold the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools import mutation_runner
from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TE = "tests/triggers/test_endpoint.py"
TW = "tests/triggers/test_worker.py"
TC = "tests/test_testing_crash.py"
TS = "tests/triggers/test_t5_wsgiref.py"
TP = "tests/triggers/test_t5_process.py"
ENDPOINT = "src/hadavin_sdk/triggers/endpoint.py"
WORKER = "src/hadavin_sdk/triggers/worker.py"
CRASH = "src/hadavin_sdk/testing/crash.py"
SERVER = "src/hadavin_sdk/triggers/server.py"
T6 = "tests/triggers/test_d_fix6_e1.py"
T8 = "tests/triggers/test_d_fix8_e1fix.py"
T9 = "tests/triggers/test_d_fix9_e1fix2.py"

JOINED = 'joined = f"{tenant}\\0{sender}\\0{key}".encode()'
VERIFY = (
    "        sender = verify_any(headers, body, clock(), secrets)\n"
    "        if sender is None:\n"
    "            return 401, None, None\n"
)
PARSE_FIRST = (
    "        try:\n"
    "            parse_body(body)\n"
    "        except BadRequest:\n"
    "            return 400, None, None\n"
)
CLOSED = "            if closed:\n                return NO_ACK\n"
SECRETS_TEST = "test_check_secrets_refuses_and_names_the_sender_not_the_value"
SIGNED_TEST = "test_signed_request_over_the_socket_is_acked_with_run_id_and_state_only"
QUIET_ERROR = (
    '    error_headers: ClassVar[list[tuple[str, str]]] = [("Content-Length", "0")]\n'
    '    error_body = b""\n'
)
LOG_NOTHING = '        """Nothing: the arguments hold the request line, which is text chosen by the caller."""\n'
EMPTY_REFUSAL = (
    "        self.send_response_only(code)\n"
    '        self.send_header("Content-Length", "0")\n'
    '        self.send_header("Connection", "close")\n'
    "        self.end_headers()\n"
)
LOG_409 = '_LOG.warning("trigger status=409 sender=%s run=%s", req.sender, req.run_id)'
READ_THEN_CAP = (
    "        if length > max_body:\n"
    "            return 413, None, None  # the body is not read\n"
    "        try:\n"
    '            body = environ["wsgi.input"].read(length)\n'
    "        except Exception:  # noqa: BLE001 - a broken or timed-out connection is the sender's fault\n"
    "            return 400, None, None\n"
)
CAP_GUARD = (
    "        if length > max_body:\n            return 413, None, None  # the body is not read\n"
)
READ_AND_PARSE = (
    "        try:\n"
    '            body = environ["wsgi.input"].read(length)\n'
    "        except Exception:  # noqa: BLE001 - a broken or timed-out connection is the sender's fault\n"
    "            return 400, None, None\n"
    "        if not isinstance(body, bytes) or len(body) != length:\n"
    "            return 400, None, None\n"
    "        ts, sig = environ.get(ts_env), environ.get(sig_env)\n"
    "        headers = {\n"
    '            TIMESTAMP_HEADER: ts if isinstance(ts, str) else "",\n'
    '            SIGNATURE_HEADER: sig if isinstance(sig, str) else "",\n'
    "        }\n"
    "        sender = verify_any(headers, body, clock(), secrets)\n"
    "        if sender is None:\n"
    "            return 401, None, None\n"
    "        try:\n"
    "            key, document = parse_body(body)\n"
    "        except BadRequest:\n"
    "            return 400, sender, None\n"
)
EXCEPT_STORE = (
    "        except Exception as exc:  # noqa: BLE001 - no ack in every case, the sender retries\n"
)
STALL_1 = (
    "            self.raw_requestline = self.rfile.readline(MAX_REQUEST_LINE + 1)\n"
    "        except TimeoutError:\n"
)
STALL_2 = "            parsed = self.parse_request()\n        except TimeoutError:\n"
NO_VERSION = (
    "        if not isinstance(\n"
    "            self.headers, Message\n"
    "        ):  # a request line with no version has no header block\n"
)
OS_ENVIRON = (
    "    os_environ: ClassVar[\n"
    "        dict[str, str]\n"
    "    ] = {}  # the stdlib default is a copy of the process environment\n"
)
N15 = "test_n15_runner_bounds_are_refused"
# The order matters: a test of `test_worker.py` leaves the stderr handler of `_log_to_stderr` on the `hadavin_sdk`
# logger (bound to a captured stream that is closed later), and `test_t5_wsgiref.py` then fails on "Logging error" text
# in stderr. `test_worker.py` therefore runs LAST (a finding for the test files; not edited here).
TESTS = [TE, TC, TS, TP, TW, T6, T8, T9]
NEEDS_CONFTEST = "tests/triggers/test_worker.py::test_main_without_a_triggers_block_exits_2"  # see the module text


KNOWN_SURVIVORS: set[str] = set()  # names of mutants that have no killer test: see the module text


def mutant(name, src, old, new, test_file, killer, expect, known_survivor=False, **kw):
    if known_survivor:  # no test exists: the whole file runs and the expected verdict is SURVIVED
        KNOWN_SURVIVORS.add(name)
        return Mutant(name, src, old, new, expect, test_file=test_file, **kw)
    pin = test_file[:-3] + "::" + killer
    return Mutant(
        name,
        src,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer.split("[")[0],
        pinned=pin,
        **kw,
    )


M = [
    # --- G1 the dedupe key
    mutant(
        "G1a the tenant is dropped from derive_run_id",
        ENDPOINT,
        JOINED,
        'joined = f"{sender}\\0{key}".encode()',
        TE,
        "test_tenant_is_part_of_the_run_id_at_the_endpoint",
        # both tenants give the id of sha256(b"sender-a\0order-1")
        "'run-3896ff0f114a33cd96d0f2f9807ef7c1' != 'run-3896ff0f114a33cd96d0f2f9807ef7c1'",
    ),
    mutant(
        "G1b the sender is dropped from derive_run_id",
        ENDPOINT,
        JOINED,
        'joined = f"{tenant}\\0{key}".encode()',
        TE,
        "test_two_senders_same_key_give_two_run_ids_and_their_own_identity",
        # both senders give the id of sha256(b"tenant-one\0order-1")
        "'run-b8214310dd20928c17270600a192fdb2' != 'run-b8214310dd20928c17270600a192fdb2'",
    ),
    mutant(
        "G1c the NUL separator is dropped from the hash input",
        ENDPOINT,
        JOINED,
        'joined = f"{tenant}{sender}{key}".encode()',
        TE,
        "test_derive_run_id_separates_tenant_sender_and_key",
        # ("ab", "c", "d") and ("a", "bc", "d") both give the id of sha256(b"abcd")
        "'run-88d4266fd4e6338d13b845fcf289579d' != 'run-88d4266fd4e6338d13b845fcf289579d'",
    ),
    # --- G2 the payload-hash conflict
    mutant(
        "G2a the document hash is dropped from trigger_ref",
        ENDPOINT,
        'return f"{sender}/{key}#{hashlib.sha256(document).hexdigest()}"',
        'return f"{sender}/{key}"',
        TE,
        "test_trigger_ref_changes_with_the_document",
        "'sender-a/order-1' ==",
    ),
    mutant(
        "G2b Runner.start skips the trigger_ref comparison on a hit",
        WORKER,
        "        or found.trigger_ref != req.trigger_ref\n",
        "",
        TW,
        "test_same_key_with_another_document_is_409_and_writes_nothing",
        "'NO_ACTION'}) == (409, {})",
    ),
    # --- G3 the ack only after the run row exists
    mutant(
        "G3a 202 right after submit, the row is not read",
        WORKER,
        CLOSED,
        CLOSED
        + "            if job is not None:\n"
        + '                return 202, {"run_id": req.run_id, "state": "RECEIVED"}\n',
        TW,
        "test_no_row_within_ack_wait_is_503_and_the_slot_stays_taken",
        "'RECEIVED'}) == (503, {})",
    ),
    mutant(
        "G3b the slot is released right after submit",
        WORKER,
        "            self._jobs.add(job)\n",
        "            self._jobs.add(job)\n            self._slots.release()\n",
        TW,
        "test_no_row_within_ack_wait_is_503_and_the_slot_stays_taken",
        "assert not True",
    ),
    mutant(
        "G3c no free slot answers 503 at once",
        WORKER,
        CLOSED,
        CLOSED + "            if job is None:\n                return NO_ACK\n",
        TW,
        "test_pool_full_is_503_and_a_later_retry_is_acked",
        ">= 1.0",
    ),
    # --- G4 the timestamp check (hmac_v0.verify itself is not mutated)
    mutant(
        "G4 the endpoint passes the request's own timestamp as now",
        ENDPOINT,
        "verify_any(headers, body, clock(), secrets)",
        "verify_any(headers, body, "
        "float(ts) if isinstance(ts, str) and ts.isascii() and ts.isdigit() else clock(), secrets)",
        TE,
        "test_t5_3_timestamp_window[-301-401]",
        "202 == 401",
    ),
    # --- G5 the signature before parsing
    mutant(
        "G5a the body is parsed before the signature (ONE mutant with G5b, two killers: the status)",
        ENDPOINT,
        VERIFY,
        PARSE_FIRST + VERIFY,
        TE,
        "test_t5_6b_malformed_and_unsigned_is_401_not_400[array]",
        "400 == 401",
    ),
    mutant(
        "G5b the body is parsed before the signature (ONE mutant with G5a, two killers: the parse spy)",
        ENDPOINT,
        VERIFY,
        PARSE_FIRST + VERIFY,
        TE,
        "test_t5_2_bad_signature_is_401_and_the_body_is_never_parsed[altered body]",
        "hellp\"}'] == []",
    ),
    # --- G6 the secrets at start
    mutant(
        "G6a the minimum secret length is not checked",
        ENDPOINT,
        "            if len(value) < MIN_SECRET_CHARS:\n",
        "            if False:\n",
        TE,
        SECRETS_TEST + "[secrets2-sender-a]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G6b two senders may share a secret",
        ENDPOINT,
        "            if other != sender:\n",
        "            if False:\n",
        TE,
        SECRETS_TEST + "[secrets0-sender-b]",
        "DID NOT RAISE ValueError",
    ),
    # --- G7 the crash helper (step E)
    mutant(
        "G7a the point is not disarmed before the crash",
        CRASH,
        "            if not self._disarm():\n                return\n",
        "",
        TC,
        "test_n2_before_crashes_and_nothing_was_written",
        # line 178 of the test, `assert fired == (..) and armed() is None`: only the SECOND conjunct fails here, so
        # pytest's first line shows the first one equal to itself, and no other fault gives that line
        "AssertionError: assert (('store.create_run:before',) == ('store.create_run:before',)",
    ),
    mutant(
        "G7b SimulatedCrash derives from Exception",
        CRASH,
        "class SimulatedCrash(BaseException):",
        "class SimulatedCrash(Exception):",
        TC,
        "test_n6_crash_before_the_model_call_leaves_the_run_working",
        "assert (True and not True)",
    ),
    mutant(
        "G7c the pytest-only gate is dropped",
        CRASH,
        "        if _GATE not in os.environ:\n",
        "        if False:\n",
        TC,
        "test_h1_cannot_be_built_outside_a_pytest_run",
        "DID NOT RAISE RuntimeError",
    ),
    mutant(
        "G7d before and after are swapped",
        CRASH,
        'before, after = f"{name}.{method}:before", f"{name}.{method}:after"',
        'after, before = f"{name}.{method}:before", f"{name}.{method}:after"',
        TC,
        "test_n2_before_crashes_and_nothing_was_written",
        "DID NOT RAISE NotFound",
    ),
    # --- G8 the quiet server (step E2)
    mutant(
        "G8a the default error body and headers of the standard library are written again",
        SERVER,
        QUIET_ERROR,
        "",
        TS,
        "test_an_app_that_raises_is_503_empty_and_logged_by_class_name_only",
        "A server error occurred",
    ),
    mutant(
        "G8b log_message prints the request line to stderr again",
        SERVER,
        LOG_NOTHING,
        LOG_NOTHING + "        super().log_message(format, *args)\n",
        TS,
        SIGNED_TEST,
        '"POST /v1/trigger HTTP/1.1" 202',
    ),
    mutant(
        "G8c send_error is the standard library's again (an HTML page as the refusal)",
        SERVER,
        EMPTY_REFUSAL,
        "        super().send_error(code, message, explain)\n",
        TS,
        "test_stall_before_the_headers_end_is_400_empty_at_the_timeout[drive_headers_then_stall]",
        "<!DOCTYPE HTML",
    ),
    mutant(
        "G8d the Server header names the Python version again",
        SERVER,
        "    server_software = None  # no Server header: it would name the Python version\n",
        "",
        TS,
        SIGNED_TEST,
        "wsgiserver/0.2 cpython",
    ),
    # --- G9 the secrets at start, the two later rules
    mutant(
        "G9a more than two secrets per sender are accepted",
        ENDPOINT,
        "        if len(values) > MAX_SECRETS_PER_SENDER:\n",
        "        if False:\n",
        TE,
        "test_check_secrets_refuses_more_than_two_secrets_per_sender",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G9b whitespace around a secret value is accepted",
        ENDPOINT,
        "            if value != value.strip():\n",
        "            if False:\n",
        TE,
        "test_check_secrets_refuses_whitespace_around_a_value_and_names_only_the_sender[0-both ends]",
        "DID NOT RAISE ValueError",
    ),
    # --- G10 the timestamp boundary
    mutant(
        "G10 the clock is not cut to whole seconds in verify_any",
        ENDPOINT,
        "    now = int(now_ts)\n",
        "    now = now_ts\n",
        TE,
        "test_verify_any_window_edge_is_exact_with_a_fractional_clock[0.001--300-sender-a]",
        "None == 'sender-a'",
    ),
    # --- G11 the wait with no free slot
    mutant(
        "G11a the pause never grows while no slot is free",
        WORKER,
        "min(pause * 2, pause_cap)\n",
        "pause\n",
        TW,
        "test_a_refused_request_reads_the_store_a_few_times_not_a_hundred",
        # the message is the number of reads (about 100, not the same in every run): WEAK, the kill rests on `pinned`
        "AssertionError: ",
    ),
    mutant(
        "G11b a waiting request never takes a freed slot",
        WORKER,
        "                    job = self._submit(req)[0]\n",
        "",
        TW,
        "test_a_waiting_request_takes_the_slot_as_soon_as_it_is_free",
        "(503, {})",
    ),
    # --- G12 bind and shutdown
    mutant(
        "G12a check_bind accepts a non-loopback address without the switch",
        WORKER,
        "    if not loopback and allow_non_loopback is not True:\n",
        "    if False:\n",
        TW,
        "test_non_loopback_host_needs_the_switch",
        "DID NOT RAISE ConfigError",
    ),
    mutant(
        "G12b check_bind accepts the IPv6 loopback address",
        WORKER,
        "    if address.version != 4:\n",
        "    if address.version != 4 and not address.is_loopback:\n",
        TW,
        "test_ipv6_hosts_are_refused_the_loopback_one_too",
        "DID NOT RAISE ConfigError",
    ),
    mutant(
        "G12c the 409 log line carries trigger_ref",
        WORKER,
        LOG_409,
        LOG_409[:-1].replace('run=%s"', 'run=%s ref=%s"') + ", req.trigger_ref)",
        TW,
        "test_409_writes_one_log_line_with_status_sender_and_run_id_only",
        # pytest shortens both texts; the tail is the end of the hash of the second document
        "assert 'sender-a/ke...676eb87eecc2' not in 'WARNING",
    ),
    mutant(
        "G12d the SIGTERM handler does not stop the server",
        WORKER,
        '        threading.Thread(target=server.shutdown, name="trigger-stop", daemon=True).start()\n',
        "        return None\n",
        TP,
        "test_d3_sigterm_stops_a_serving_worker_cleanly",
        "the child did not end within",
    ),
    # --- G13 the checks of the endpoint itself
    mutant(
        "G13a verify_any stops after the first secret that verifies",
        ENDPOINT,
        "                matched.add(sender)\n",
        "                return sender\n",
        TE,
        "test_verify_any_tries_every_secret_with_no_early_stop",
        "bbbbbbbbbbbb'] == ['aaaaaaaaaaa...ffffffffffff']",
    ),
    mutant(
        "G13b verify_any accepts two matching senders (exactly one is not required)",
        ENDPOINT,
        "    return next(iter(matched)) if len(matched) == 1 else None\n",
        "    return min(matched) if matched else None\n",
        TE,
        "test_verify_any_refuses_when_two_senders_match",
        "assert 'sender-a' is None",
    ),
    mutant(
        "G13c check_secrets accepts more than eight senders",
        ENDPOINT,
        "    if len(secrets) > MAX_SENDERS:\n",
        "    if False:\n",
        TE,
        SECRETS_TEST + "[secrets7-more than 8]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G13d make_wsgi does not compare the sender ids with the secret ids",
        ENDPOINT,
        "    if set(secrets) != set(senders):\n",
        "    if False:\n",
        TE,
        "test_make_wsgi_refuses_a_bad_setup",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G13e make_wsgi has no upper bound for max_body_bytes",
        ENDPOINT,
        "    if max_body > MAX_BODY_BYTES_LIMIT:\n",
        "    if False:\n",
        TE,
        "test_make_wsgi_has_its_own_upper_bounds_for_a_callers_settings_object",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G13f the body is read before the size cap is looked at",
        ENDPOINT,
        READ_THEN_CAP,
        (
            "        try:\n"
            '            body = environ["wsgi.input"].read(length)\n'
            "        except Exception:  # noqa: BLE001 - a broken or timed-out connection is the sender's fault\n"
            "            return 400, None, None\n"
            "        if length > max_body:\n"
            "            return 413, None, None\n"
        ),
        TE,
        "test_t5_7_content_length_over_the_cap_is_413_without_reading",
        "assert 1 == 0",
    ),
    # --- G14 the rules for a secret value
    mutant(
        "G14a a byte-order mark or zero-width character in a secret is accepted",
        ENDPOINT,
        "            if any(char in value for char in UNSEEN_CHARS):\n",
        "            if False:\n",
        TE,
        "test_check_secrets_refuses_an_unseen_character_anywhere_in_a_value[start-byte-order mark]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G14b a control character inside a secret is accepted",
        ENDPOINT,
        '            if any(unicodedata.category(char) == "Cc" for char in value):\n',
        "            if False:\n",
        TE,
        "test_check_secrets_refuses_a_control_character_inside_a_value[C1]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G14c the same value twice for one sender is accepted",
        ENDPOINT,
        "            if values.count(value) > 1:\n",
        "            if False:\n",
        TE,
        "test_check_secrets_refuses_the_same_value_twice_for_one_sender",
        "DID NOT RAISE ValueError",
    ),
    # --- G15 the quiet server: timeouts and the long request line
    mutant(
        "G15a a timeout on the request line is not a stalled client",
        SERVER,
        STALL_1,
        STALL_1.replace("TimeoutError", "KeyError"),
        TS,
        "test_stall_before_the_headers_end_is_400_empty_at_the_timeout[drive_silent_client]",
        "Seen(raw=b'', end='closed'",
    ),
    mutant(
        "G15b a timeout in the header block is not a stalled client",
        SERVER,
        STALL_2,
        STALL_2.replace("TimeoutError", "KeyError"),
        TS,
        "test_stall_before_the_headers_end_is_400_empty_at_the_timeout[drive_headers_then_stall]",
        "Seen(raw=b'', end='closed'",
    ),
    mutant(
        "G15c a request line over the cap is not answered 414",
        SERVER,
        "        if len(self.raw_requestline) > MAX_REQUEST_LINE:\n",
        "        if False:\n",
        TS,
        "test_request_line_over_64_kb_is_414_empty",
        "AssertionError: (b'HTTP/1.0 400 Bad Request",
    ),
    mutant(
        "G15d the stalled-client refusal needs no request_version default",
        SERVER,
        '        if not hasattr(self, "request_version"):\n',
        "        if False:\n",
        TS,
        "test_stall_before_the_headers_end_is_400_empty_at_the_timeout[drive_silent_client]",
        "Seen(raw=b'', end='closed'",
    ),
    mutant(
        "G15e send_error does not note that an answer was begun",
        SERVER,
        "        self._answer_begun = True\n",
        "",
        TS,
        "test_n9_a_timeout_while_a_refusal_is_written_gives_no_second_status_line",
        "AssertionError: [b'HTTP/1.0 431 Request Header Fields Too Large",
    ),
    mutant(
        "G15f a stalled client is answered although an answer was begun",
        SERVER,
        "        if self._answer_begun:\n",
        "        if False:\n",
        TS,
        "test_n9_a_timeout_while_a_refusal_is_written_gives_no_second_status_line",
        "AssertionError: [b'HTTP/1.0 431 Request Header Fields Too Large",
    ),
    # --- G16 the quiet server: framing, names, version and the environment
    mutant(
        "G16a an HTTP version of 2.0 or higher is answered 505 again",
        SERVER,
        "            code >= SERVER_ERROR\n",
        "            False\n",
        TS,
        "test_f1_http_version_2_or_higher_is_400_empty_never_a_5xx[HTTP/2.0]",
        "Seen(raw=b'HTTP/1.0 505 HTTP Version Not Supported",
    ),
    mutant(
        "G16b a request line with no version is not closed quietly",
        SERVER,
        NO_VERSION,
        "        if False:\n",
        TS,
        "test_f2_a_request_line_without_a_version_is_closed_on_purpose",
        "assert [('WARNING', ...ributeError')] == [('DEBUG', 't...h no answer')]",
    ),
    mutant(
        "G16c a header name with an underscore is accepted",
        SERVER,
        '        if any("_" in name for name in self.headers):\n',
        "        if False:\n",
        TS,
        "test_f3_a_header_name_with_an_underscore_is_400_empty[signed names]",
        "Seen(raw=b'HTTP/1.0 202 Accepted",
    ),
    mutant(
        "G16d two Content-Length headers are accepted",
        SERVER,
        '        if len(self.headers.get_all("Content-Length", [])) > 1:\n',
        "        if False:\n",
        TS,
        "test_f4_two_content_lengths_or_a_transfer_encoding_is_400_before_the_body_is_read[two equal lengths]",
        "Seen(raw=b'HTTP/1.0 202 Accepted",
    ),
    mutant(
        "G16e a Transfer-Encoding header is accepted",
        SERVER,
        '        return "Transfer-Encoding" in self.headers\n',
        "        return False\n",
        TS,
        "test_f4_two_content_lengths_or_a_transfer_encoding_is_400_before_the_body_is_read[chunked]",
        "Seen(raw=b'HTTP/1.0 202 Accepted",
    ),
    mutant(
        "G16f the application handler takes the process environment again",
        SERVER,
        OS_ENVIRON,
        "",
        TS,
        "test_n11_a_process_variable_cannot_stand_in_for_a_missing_header",
        "Seen(raw=b'HTTP/1.0 202 Accepted",
    ),
    # --- G17 the 503 hint and the log level of a refusal
    mutant(
        "G17a a 503 carries no Retry-After header",
        ENDPOINT,
        "        if status == 503:\n            response_headers.append(",
        "        if False:\n            response_headers.append(",
        TE,
        "test_503_carries_retry_after_and_no_other_answer_does",
        "assert None == '1'",
    ),
    mutant(
        "G17b a request that did not verify is logged at INFO",
        ENDPOINT,
        "            level = logging.INFO if sender else logging.DEBUG  # DEBUG: refused before it verified\n",
        "            level = logging.INFO\n",
        TS,
        "test_n10_refusals_before_the_signature_are_debug_and_a_verified_request_is_info",
        "('INFO', 'trigger status=401 sender=-')",
    ),
    # --- G18 the cap on waiting requests and the drain
    mutant(
        "G18a no cap on the requests waiting inside start",
        WORKER,
        "        if not self._waiting.acquire(blocking=False):\n",
        "        if False:\n",
        TW,
        "test_m2_a_hung_store_cannot_pile_up_request_threads",
        "assert ([] == [(503, {})]",
    ),
    mutant(
        "G18b the waiting place is not given back",
        WORKER,
        "        try:\n            return self._decide(req)\n        finally:\n            self._waiting.release()\n",
        "        return self._decide(req)\n",
        TW,
        "test_m2_a_place_is_given_back_after_every_answer",
        "assert 503 in (200, 202)",
    ),
    mutant(
        "G18c serve does not close the runner",
        WORKER,
        "        runner.close()\n        for number, handler in previous.items():\n",
        "        for number, handler in previous.items():\n",
        TW,
        "test_serve_gives_the_previous_sigterm_handler_back",
        "assert (False)",
    ),
    mutant(
        "G18d close writes no warning for a loop still going",
        WORKER,
        "        if going:\n",
        "        if False:\n",
        TW,
        "test_m3_close_warns_once_when_a_loop_is_still_going",
        "assert (0 == 1)",
    ),
    mutant(
        "G18e close warns although nothing is running",
        WORKER,
        "        if going:\n",
        "        if True:\n",
        TW,
        "test_m3_close_with_nothing_running_is_quiet",
        "assert ['trigger wor...longest run)'] == []",
    ),
    mutant(
        "G18f a waiter keeps polling after the runner was closed",
        WORKER,
        "                    if self._closed:\n                        return NO_ACK  # closed while it waited: no loop begins here any more\n",
        "",
        TW,
        "test_n3_a_waiter_gets_503_at_once_when_the_runner_is_closed",
        "assert ([] == [(503, {})]",
    ),
    # --- G19 what a store error and a bug are told apart by, and what is logged
    mutant(
        "G19a every error of start is logged as a store error",
        WORKER,
        "            if is_store_error(exc):\n",
        "            if True:\n",
        TW,
        "test_n5_a_store_error_is_a_warning_and_a_bug_is_an_error_both_503",
        "ZeroDivisionError('secret-text-4')",
    ),
    mutant(
        "G19b every error of start is logged as internal",
        WORKER,
        "            if is_store_error(exc):\n",
        "            if False:\n",
        TW,
        "test_n5_a_store_error_is_a_warning_and_a_bug_is_an_error_both_503",
        "StoreUnavailable('secret-text-1')",
    ),
    mutant(
        "G19c a StaleState of the store is answered 409 from its type",
        WORKER,
        EXCEPT_STORE,
        EXCEPT_STORE
        + "            if isinstance(exc, StaleState):\n                return CONFLICT\n",
        TW,
        "test_n5_a_store_error_is_a_warning_and_a_bug_is_an_error_both_503",
        "assert (409, {}) == (503, {})",
    ),
    mutant(
        "G19d the exception of a run thread is not logged",
        WORKER,
        "        if exc is not None:\n",
        "        if False:\n",
        TW,
        "test_n7_a_base_exception_of_a_run_thread_is_logged_by_class_name_and_frees_the_slot",
        "assert (0 == 1)",
    ),
    mutant(
        "G19e the memory store is not warned about",
        WORKER,
        "    if not isinstance(store, MemoryStore):\n",
        "    if True:\n",
        TW,
        "test_n1_the_memory_store_is_warned_about_and_the_start_goes_on",
        "assert True is False",
    ),
    # --- G20 the bounds of Runner
    mutant(
        "G20a max_running below one is not refused by the Runner (message guard: a later check still refuses, only the text differs)",
        WORKER,
        "max_running < 1 or ",
        "",
        TW,
        "test_bad_arguments_are_refused",
        "Regex pattern did not match.",
    ),
    mutant(
        "G20b ack_wait_s of zero is accepted",
        WORKER,
        "0 < ack_wait_s <= ACK_WAIT_S_CEILING",
        "ack_wait_s <= ACK_WAIT_S_CEILING",
        TW,
        "test_bad_arguments_are_refused",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20c poll_s of zero is not refused as such (message guard: the POLL_S_MIN check still refuses, only the text differs)",
        WORKER,
        " or poll_s <= 0:",
        ":",
        TW,
        "test_bad_arguments_are_refused",
        "Regex pattern did not match.",
    ),
    mutant(
        "G20d max_running has no ceiling",
        WORKER,
        "    if max_running > MAX_RUNNING_CEILING:\n",
        "    if False:\n",
        TW,
        N15 + "[kw0-at most 64]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20e ack_wait_s has no ceiling",
        WORKER,
        "0 < ack_wait_s <= ACK_WAIT_S_CEILING",
        "0 < ack_wait_s",
        TW,
        N15 + "[kw1-at most 30]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20f poll_s has no lower bound",
        WORKER,
        "POLL_S_MIN <= poll_s <= POLL_S_MAX",
        "poll_s <= POLL_S_MAX",
        TW,
        N15 + "[kw2-between 0.01 and 1]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20g poll_s has no upper bound",
        WORKER,
        "POLL_S_MIN <= poll_s <= POLL_S_MAX",
        "POLL_S_MIN <= poll_s",
        TW,
        N15 + "[kw3-between 0.01 and 1]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20h max_waiting of zero is accepted",
        WORKER,
        " or max_waiting < 1:",
        ":",
        TW,
        N15 + "[kw4-max_waiting]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20i max_waiting may be a bool",
        WORKER,
        "isinstance(max_waiting, bool) or ",
        "",
        TW,
        N15 + "[kw5-max_waiting]",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20j make_app lets a bound of the Runner through as a ValueError",
        WORKER,
        "    except ValueError as exc:  # these messages name senders and bounds, never a value\n",
        "    except KeyError as exc:  # these messages name senders and bounds, never a value\n",
        TW,
        "test_n15_make_app_turns_a_bound_into_a_config_error",
        "ValueError: max_running must be at most 64",
        allow_crash=True,
        crash_type="ValueError",
    ),
    # --- G21 the quiet server: the two bounds on a client, and its fault hooks (d-fix2)
    mutant(
        "G21a the cap on connection threads is removed (a connection over the cap is not closed)",
        SERVER,
        "        if not self._slots.acquire(blocking=False):\n",
        "        if False:\n",
        TS,
        "test_connections_above_the_cap_are_closed_at_once_unread_and_the_cap_frees_again",
        "end='client timeout'",
    ),
    mutant(
        "G21b the absolute read deadline is replaced by the pause limit of each recv",
        SERVER,
        "        left = self._end - time.monotonic()\n",
        "        left = 10**9\n",
        TS,
        "test_a_slow_body_is_cut_at_the_absolute_deadline_not_at_the_pause_limit",
        "Seen(raw=b'HTTP/1.0 202 Accepted",
    ),
    mutant(
        "G21c QuietServer.handle_error is deleted (the stdlib prints a traceback)",
        SERVER,
        "    def handle_error(self, request: Any, client_address: Any) -> None:\n",
        "    def _not_handle_error(self, request: Any, client_address: Any) -> None:\n",
        TS,
        "test_a_fault_in_setup_or_finish_on_a_real_connection_is_one_quiet_log_line[setup-RuntimeError-WARNING]",
        "AssertionError: []",
    ),
    mutant(
        "G21d QuietServer.process_request_thread is deleted (a BaseException reaches the thread hook)",
        SERVER,
        "    def process_request_thread(self, request: Any, client_address: Any) -> None:\n",
        "    def _not_process_request_thread(self, request: Any, client_address: Any) -> None:\n",
        TS,
        "test_a_fault_in_setup_or_finish_on_a_real_connection_is_one_quiet_log_line[setup-Boom-WARNING]",
        "AssertionError: []",
    ),
    # --- G22 Runner.close
    mutant(
        "G22 Runner.close does not set the closed flag (the shut-down pool refuses the work instead)",
        WORKER,
        "            self._closed = True\n",
        "            pass\n",
        TW,
        "test_after_close_a_new_key_is_503_at_once_with_no_error_line_and_the_pool_is_never_asked",
        "assert [(<bound meth",
    ),
    # --- G23 the 409 rule of _answer: agent and principal, one mutant each
    mutant(
        "G23a _answer does not compare the agent of the row (T-1)",
        WORKER,
        "        found.agent_id != req.agent_id\n        or found.principal_id",
        "        found.principal_id",
        TW,
        "test_same_key_and_ref_but_another_agent_or_principal_is_409[agent_id]",
        "'RECEIVED'}) == (409, {})",
    ),
    mutant(
        "G23b _answer does not compare the principal of the row (T-1)",
        WORKER,
        "        or found.principal_id != req.principal_id\n",
        "",
        TW,
        "test_same_key_and_ref_but_another_agent_or_principal_is_409[principal_id]",
        "'RECEIVED'}) == (409, {})",
    ),
    # --- G24 the header set of a refusal
    mutant(
        "G24 a 401 carries an extra header X-Reason (the refused() header subset)",
        ENDPOINT,
        '        if status == 405:\n            response_headers.append(("Allow", METHOD))\n',
        '        if status == 405:\n            response_headers.append(("Allow", METHOD))\n'
        '        if status == 401:\n            response_headers.append(("X-Reason", "bad"))\n',
        TE,
        "test_t5_8b_removed_old_secret_is_refused",
        "'X-Reason': 'bad'}",
    ),
    # --- G25 sender_map
    mutant(
        "G25 sender_map accepts a sender id listed twice",
        ENDPOINT,
        "        if sender.id in out:\n",
        "        if False:\n",
        TE,
        "test_make_wsgi_refuses_a_bad_setup",
        "DID NOT RAISE ValueError",
    ),
    # --- G26 parse_body
    mutant(
        "G26a parse_body takes a duplicate member (no _no_duplicates hook)",
        ENDPOINT,
        'json.loads(body.decode("utf-8"), object_pairs_hook=_no_duplicates)',
        'json.loads(body.decode("utf-8"))',
        TE,
        "test_parse_body_refuses[duplicate document]",
        "DID NOT RAISE BadRequest",
    ),
    mutant(
        "G26b parse_body does not require exactly key and document",
        ENDPOINT,
        " or set(obj) != BODY_FIELDS:",
        ":",
        TE,
        "test_parse_body_refuses[extra NaN]",
        "DID NOT RAISE BadRequest",
    ),
    # --- G27 the Content-Length guard
    mutant(
        "G27 _content_length takes a signed, spaced or non-ASCII number (digits-only guard removed)",
        ENDPOINT,
        "    if not isinstance(raw, str) or not (raw.isascii() and raw.isdigit()):\n",
        "    if not isinstance(raw, str):\n",
        TE,
        "test_t5_7b_content_length_missing_or_not_digits_or_zero_is_400[]",
        "assert 503 == 400",
    ),
    # --- G30 the cap is on the raw bytes; G31 the empty document
    mutant(
        "G30a the size cap guard is deleted (no 413 for an escaped body over the cap)",
        ENDPOINT,
        CAP_GUARD,
        "",
        TE,
        "test_e11_cap_is_on_the_raw_bytes_not_on_the_decoded_document[nul-document0]",
        "assert 202 == 413",
    ),
    mutant(
        "G30b the cap is on the decoded document length after parse_body, not on the raw bytes",
        ENDPOINT,
        CAP_GUARD + READ_AND_PARSE,
        READ_AND_PARSE
        + "        if len(document) > max_body:\n            return 413, sender, None\n",
        TE,
        "test_e11_cap_is_on_the_raw_bytes_not_on_the_decoded_document[nul-document0]",
        "assert 202 == 413",
    ),
    mutant(
        "G31 parse_body refuses an empty document",
        ENDPOINT,
        '    try:\n        return key, document.encode("utf-8")\n',
        '    if not document:\n        raise BadRequest("empty document")\n    try:\n        return key, document.encode("utf-8")\n',
        TE,
        "test_parse_body_round_trip",
        "BadRequest: empty document",
        allow_crash=True,
        crash_type="BadRequest",
    ),
    # --- G28 the bind switch
    mutant(
        "G28 check_bind takes any truthy value as the non-loopback switch",
        WORKER,
        "    if not loopback and allow_non_loopback is not True:\n",
        "    if not loopback and not allow_non_loopback:\n",
        TW,
        "test_non_loopback_host_needs_the_switch",
        "DID NOT RAISE ConfigError",
    ),
    # --- G29 check_senders, the three refusals
    mutant(
        "G29a check_senders does not refuse an agent that is not qualified",
        WORKER,
        "        if sender.agent_id not in qualified:\n",
        "        if False:\n",
        TP,
        "test_d2_check_senders_refuses_a_bad_agent_or_principal[unknown-agent]",
        "DID NOT RAISE ConfigError",
    ),
    mutant(
        "G29b check_senders does not refuse a principal that is unknown",
        WORKER,
        "        if principal is None:\n",
        "        if False:\n",
        TP,
        "test_d2_check_senders_refuses_a_bad_agent_or_principal[unknown-principal]",
        "AssertionError: Regex pattern did not match.",  # d-fix3: None now gives the ConfigError of `_field`, other text
    ),
    mutant(
        "G29c check_senders does not refuse a principal that is not of kind service",
        WORKER,
        '        if _field(principal, "kind", f"principal {sender.principal_id} kind") != "service":\n',
        "        if False:\n",
        TP,
        "test_d2_check_senders_refuses_a_bad_agent_or_principal[principal-not-service]",
        "DID NOT RAISE ConfigError",
    ),
    # --- G32 E1: the 409 audit event, /health, the degraded start (killers need no conftest fixture: `rt` is local)
    mutant(
        "G32a the per-minute cap of the 409 audit events is never reached",
        WORKER,
        "            if seen > self._cap:\n",
        "            if False:\n",
        T6,
        "test_e1_the_11th_conflict_in_a_minute_writes_no_event_but_is_still_409_and_counted",
        "assert (11 == 10)",
    ),
    mutant(
        "G32b the conflict event result carries the payload text",
        WORKER,
        '        result="conflict",\n',
        '        result="conflict:" + req.document.decode(),\n',
        T6,
        "test_e1_a_409_writes_one_audit_event_with_exactly_ids_and_both_hashes",
        "AssertionError: assert {'run_id'",  # same first line as G32c: the dict compare, told apart by pinned only
    ),
    mutant(
        "G32c the stored hash of the conflict event is taken from the new request",
        WORKER,
        "output_hash=_hash_of(found.trigger_ref)",
        "output_hash=_hash_of(ref)",
        T6,
        "test_e1_a_409_writes_one_audit_event_with_exactly_ids_and_both_hashes",
        "AssertionError: assert {'run_id'",
    ),
    mutant(
        "G32d the /health body gets an extra key",
        ENDPOINT,
        '"store_failures": failures}',
        '"store_failures": failures, "extra": 1}',
        T6,
        "test_e1_start_with_the_store_down_starts_and_health_is_503[StoreUnavailable]",
        "'extra': 1} == {'status'",
    ),
    mutant(
        "G32e /health is answered with no health callable (the path is not an ordinary 404)",
        ENDPOINT,
        'health_app is not None and environ.get("PATH_INFO") == HEALTH_PATH',
        'environ.get("PATH_INFO") == HEALTH_PATH',
        T6,
        "test_e1_without_a_health_callable_the_path_is_an_ordinary_404",
        "'NoneType' object is not callable",
        allow_crash=True,
        crash_type="TypeError",
    ),
    mutant(
        "G32f the degraded worker never starts its re-check thread",
        WORKER,
        "    degraded.start()\n",
        "    pass\n",
        T8,
        "test_e1fix_a_worker_started_with_the_store_down_recovers_in_the_same_process",
        "no 503 then 202 in one process",
    ),
    mutant(
        "G32g the recovery does not ping the store before it takes the real app",
        WORKER,
        "    up, _failures = runner.health()\n",
        "    up = True\n",
        T8,
        "test_e1fix_a_worker_started_with_the_store_down_recovers_in_the_same_process",
        "assert 1 > 2",
    ),
    mutant(
        "G32h Runner.health starts a new ping thread on every call",
        WORKER,
        "            if ping is None or ping.done.is_set():\n",
        "            if True:\n",
        T8,
        "test_e1fix_the_health_ping_is_bounded_and_never_leaks_more_than_one_thread",
        "assert 2 == 1",
    ),
    mutant(
        "G32i Runner.health never times the ping out (a hung store reads as up)",
        WORKER,
        "        if not ping.done.wait(HEALTH_PING_TIMEOUT_S):\n",
        "        if not (ping.done.wait(HEALTH_PING_TIMEOUT_S) or True):\n",
        T8,
        "test_e1fix_the_health_ping_is_bounded_and_never_leaks_more_than_one_thread",
        "_failures': 0} == {",
    ),
    mutant(
        "G32j _prepare does not warn that the App has no audit",
        WORKER,
        "    wsgi, runner, app = _build_app(args)\n    _warn_no_audit(app)\n    port",
        "    wsgi, runner, app = _build_app(args)\n    port",
        T8,
        "test_e1fix_main_warns_once_when_the_app_has_no_audit_and_make_app_does_not",
        "assert (0 == 1)",
    ),
    # --- G33 E1 fix2 (d-fix9): the guards of worker.py's re-check, the audit write bound, the per-sender cap
    mutant(
        "G33a _recover does not close the App's store after a failed try",
        WORKER,
        "            runner.close(0)\n            _close_app(app)\n",
        "            runner.close(0)\n",
        T9,
        "test_fix2_recover_closes_the_store_on_every_failed_try",
        "assert 0 == 1",
    ),
    mutant(
        "G33b Runner.health puts the ping in place before its thread has started",
        WORKER,
        "                fresh = _Ping(self._store, self._count_store_failure)\n",
        "                fresh = _Ping(self._store, self._count_store_failure)\n                self._ping = fresh\n",
        T9,
        "test_fix2_a_ping_thread_that_does_not_start_is_a_counted_503_and_the_next_call_works",
        "assert (False, 2) == (True, 1)",
    ),
    mutant(
        "G33c the conflict audit write is waited for 30 s, not 2 s",
        WORKER,
        "AUDIT_WRITE_TIMEOUT_S: Final[float] = (\n    2.0",
        "AUDIT_WRITE_TIMEOUT_S: Final[float] = (\n    30.0",
        T9,
        "test_fix2_a_blocked_audit_write_costs_the_409_at_most_2_s_and_one_write_is_pending",
        "assert 30.0 == 2.0",
    ),
    mutant(
        "G33d a degraded worker never stops on repeated non-store errors",
        WORKER,
        "                    if other >= DEGRADED_FATAL_AFTER:\n",
        "                    if False:\n",
        T9,
        "test_fix2_five_non_store_failures_in_a_row_stop_the_worker_with_exit_3",
        "the worker did not stop on its own",  # pytest.fail: the leading class is `Failed`, not an assertion
        allow_crash=True,
        crash_type="Failed",
    ),
    mutant(
        "G33e the 409 event cap uses one shared key for all senders",
        WORKER,
        "            start, seen = self._conflict_windows.get(req.sender, (at, 0))\n"
        "            if at - start >= CONFLICT_WINDOW_S or at < start:\n"
        "                start, seen = at, 0\n"
        "            seen += 1\n"
        "            self._conflict_windows[req.sender] = (start, seen)\n",
        "            start, seen = self._conflict_windows.get('-', (at, 0))\n"
        "            if at - start >= CONFLICT_WINDOW_S or at < start:\n"
        "                start, seen = at, 0\n"
        "            seen += 1\n"
        "            self._conflict_windows['-'] = (start, seen)\n",
        T9,
        "test_fix2_the_cap_is_per_sender_and_the_window_dict_is_bounded_by_the_senders",
        "assert (0 == 1)",
    ),
    mutant(
        "G33f an unsigned request is taken as the first configured sender",
        ENDPOINT,
        "        sender = verify_any(headers, body, clock(), secrets)\n",
        "        sender = verify_any(headers, body, clock(), secrets) or next(iter(senders))\n",
        T9,
        "test_fix2_an_unsigned_or_wrongly_signed_conflicting_document_writes_no_event",
        "assert 409 == 401",
    ),
]

POSIX_ONLY = ("G12d", "G18c")  # their killers skip on win32 (SIGTERM is not delivered there)


def check_anchors(mutants):
    """Every `old` text must occur EXACTLY once in its source file: the runner replaces every occurrence and a
    stale or ambiguous anchor would otherwise give a wrong or no mutant. Returns the list of problems."""
    bad = []
    for m in mutants:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        n = text.count(m.old)
        if n != 1:
            bad.append(f"ERROR anchor of {m.name!r} occurs {n} times in {m.file} (must be 1)")
    return bad


def header():
    import hashlib

    files = sorted((ROOT / "src/hadavin_sdk/triggers").glob("*.py"))
    files += [ROOT / CRASH, Path(__file__).resolve()]
    print(f"# endpoint mutants run, python {sys.version.split()[0]}, platform {sys.platform}")
    for f in files:
        print(f"# sha256 {hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(ROOT)}")
    sys.stdout.flush()


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    header()
    problems = check_anchors(M)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(2)  # a stale anchor is loud and nothing runs
    skipped = []
    todo = M
    if sys.platform == "win32":
        skipped = [m.name for m in M if m.name.startswith(POSIX_ONLY)]
        todo = [m for m in M if m.name not in skipped]
        for name in skipped:
            print(f"NOT RUN HERE (win32, POSIX killer) {name}", flush=True)
    first_lines = {}

    def show(row):
        name, v, test_id, good = row
        listed = name in KNOWN_SURVIVORS
        tag = "ok " if good else "BAD"
        if listed:
            tag = "SURV(known)" if v == "SURVIVED" else "BAD"
        print(f"{tag} {v:12} {name}  [{test_id.split('::')[-1][:70]}]", flush=True)
        if not good and not (listed and v == "SURVIVED"):
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    # set for the pytest child only (the runner's fixed child variables), not in this process's environment
    mutation_runner.CHILD_FIXED_ENV["PYTEST_ADDOPTS"] = f"--deselect {NEEDS_CONFTEST}"
    res = run_mutants(
        ROOT,
        todo,
        TESTS,
        extra_dirs=("tests",),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
        baseline_timeout=900,
    )
    known = [n for n, v, _, _ in res if n in KNOWN_SURVIVORS and v == "SURVIVED"]
    bad = [n for n, v, _, g in res if not g and not (n in KNOWN_SURVIVORS and v == "SURVIVED")]
    killed = sum(1 for n, v, _, g in res if g and v == "KILLED" and n not in KNOWN_SURVIVORS)
    crashed = [n.split()[0] for n, v, _, g in res if g and v == "CRASH"]
    print(
        f"{killed} killed, {len(crashed)} crash-accepted ({', '.join(crashed)}), {len(known)} known survivors"
    )
    print(
        "KNOWN SURVIVORS (missing test): the mutant is not killed by any test; listed, not a pass"
    )
    for n in sorted(known) or ["(none: every mutant of the list has a killer test)"]:
        print(f"  - {n}")
    if skipped:
        print(f"NOT RUN HERE (win32): {skipped}")
    print(f"{len(res) - len(bad)} of {len(res)} run are as expected; problems: {bad}")
    sys.exit(1 if bad else (3 if skipped else 0))
