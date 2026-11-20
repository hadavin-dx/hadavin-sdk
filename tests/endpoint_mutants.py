"""Mutants of the signed trigger endpoint (`triggers/endpoint.py`), its worker half (`triggers/worker.py`), the quiet
server classes (`triggers/server.py`) and the crash helper of step E (`testing/crash.py`), run by the P1m runner
(`tools/mutation_runner.py`). Not collected by pytest.

Each mutant reverts ONE guard in a temp copy of the package; the test in `killer` must be the one that fails first, with a
first failing line that holds `expect`. Twenty groups, one per guarantee:

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

G4: the five-minute window itself lives inside `approvals/hmac_v0.verify`. That file is NOT mutated and not edited here: the
mutant is on the endpoint side only (the request's own timestamp is passed as "now", so the window can never close).

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
  - `QuietServer.handle_error` (the override that logs the class name): TEST MISSING, no test reaches it. `handle` catches
    every `Exception`, so it takes an error outside `handle` (a failing `setup` or `finish`, or a BaseException) with a
    stderr capture: without the override the stdlib prints a traceback and the client address.
  - `self._closed = True` in `Runner.close`: TEST MISSING. A closed Runner still answers 503 without it, because the
    shut-down pool refuses the submit (RuntimeError, caught in `_decide` and logged as an internal error), so every
    status test passes. A test must read the log: after `close`, a new key gives 503 with NO ERROR line and the pool
    is not asked (`runner._pool.submit` is never called).
  G19c is the "409 from the exception type" mutant of the lead's list: a StaleState of `get_run` is turned into 409; the
  loop's own exceptions never reach `_decide` (`_run` swallows them), so the type check can only be placed there.

G8 to G12 have no mutant left out: each of their thirteen is killed. G8a takes away the two class lines `error_headers`
and `error_body` together (one piece of text). G8c is pinned to the stalled-client case: there the status line stays
`400 Bad Request` and the first failing line is the HTML body (with a broken request line the status line fails first).

Two test files run a child process: `tests/triggers/test_t5_process.py` (G12d, case D3) and one test of `test_worker.py`.
`test_t5_process.py` imports `make_cfg` from `tests/conftest.py` as a plain module and takes no fixture from it, so it
runs under `--noconftest` as it is (the whole `tests` folder is in the copy). G12d waits out the 15 seconds of D3.
Weak `expect` fragments (the line is a bare "DID NOT RAISE ValueError", or a bare boolean, so the kill rests on `pinned`):
G13c to G13e, G14a to G14c, G18c ("assert (False)"), G20b, G20d to G20i. The `expect` of G11a is weak: the assertion message is the number of store reads, about 100 and not the same in every
run, so only `AssertionError: ` is matched and the kill is tied to its test by `pinned` alone.

Most killer assertions are bare (no message text), so `expect` is then a fragment of the compared VALUES in the first failing
line (`400 == 401`, `== (409, {})`), and the kill is tied to its test by `pinned`. Run from the repo root (no database, no
network; exit 0 only when every mutant is good, and the last line is `N of N good; problems: []`):

    uv run python tests/endpoint_mutants.py            # all; exit 1 if any is not good
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
NEEDS_CONFTEST = "tests/triggers/test_worker.py::test_main_without_a_triggers_block_exits_2"  # see the module text


def mutant(name, src, old, new, test_file, killer, expect, **kw):
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
        "G5a the body is parsed before the signature (seen as the status)",
        ENDPOINT,
        VERIFY,
        PARSE_FIRST + VERIFY,
        TE,
        "test_t5_6b_malformed_and_unsigned_is_401_not_400[array]",
        "400 == 401",
    ),
    mutant(
        "G5b the body is parsed before the signature (seen by the parse spy)",
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
        "            if not self._take():\n                return\n",
        "",
        TC,
        "test_n2_before_crashes_and_nothing_was_written",
        "('store.create_run:before',) == ('store.create_run:before',)",
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
        "    return next(iter(matched)) if matched else None\n",
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
        "        if status == 503:\n",
        "        if False:\n",
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
        "        runner.close()\n        if previous is not None:\n",
        "        if previous is not None:\n",
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
        "G20a max_running below one is not refused by the Runner",
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
        " or ack_wait_s <= 0",
        "",
        TW,
        "test_bad_arguments_are_refused",
        "DID NOT RAISE ValueError",
    ),
    mutant(
        "G20c poll_s of zero is not refused as such",
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
        "        if ack_wait_s > ACK_WAIT_S_CEILING:\n",
        "        if False:\n",
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
    ),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    # set for the pytest child only (the runner's fixed child variables), not in this process's environment
    mutation_runner.CHILD_FIXED_ENV["PYTEST_ADDOPTS"] = f"--deselect {NEEDS_CONFTEST}"
    res = run_mutants(
        ROOT,
        M,
        [TE, TW, TC, TS, TP],
        extra_dirs=("tests",),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
