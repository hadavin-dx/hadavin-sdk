"""Mutants of the signed trigger endpoint (`triggers/endpoint.py`), its worker half (`triggers/worker.py`) and the crash
helper of step E (`testing/crash.py`), run by the P1m runner (`tools/mutation_runner.py`). Not collected by pytest.

Each mutant reverts ONE guard in a temp copy of the package; the test in `killer` must be the one that fails first, with a
first failing line that holds `expect`. Seven groups, one per guarantee:

    G1  the dedupe key: tenant, sender and the NUL separator are all part of `derive_run_id`
    G2  the payload-hash conflict: the document hash is in `trigger_ref`, and `Runner.start` compares it on a hit
    G3  the ack comes only after the run row exists; the slot is held until the loop ends; no slot is not a 503 at once
    G4  the timestamp check: the endpoint hands its own clock to the verifier
    G5  the signature is verified before the body is parsed
    G6  the secrets are checked at start: minimum length, and distinct across senders
    G7  the crash helper: disarm before the crash, a `BaseException`, the pytest-only gate, before and after not swapped

G4: the five-minute window itself lives inside `approvals/hmac_v0.verify`. That file is NOT mutated and not edited here: the
mutant is on the endpoint side only (the request's own timestamp is passed as "now", so the window can never close).

One test of `tests/triggers/test_worker.py`, `test_main_without_a_triggers_block_exits_2`, takes the fixture `cfg_dir` from
`tests/conftest.py`. The runner runs pytest with `--noconftest` on purpose, so under it that test errors at setup and the
unmutated copy would not pass. It kills no mutant of this list and is deselected for every run here, the baseline included
(`NEEDS_CONFTEST`, handed to the pytest child as `PYTEST_ADDOPTS`); no file is changed for it. When that test builds its
config folder without the conftest fixture, delete `NEEDS_CONFTEST` and the two lines that use it.

G1 has no mutant for the guard `"\\0" in value` of `derive_run_id`: dropping it changes nothing (the two field patterns
already refuse a NUL, so every bad triple is still a ValueError and the mutant SURVIVES). The separator mutant is G1c.

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
        "test_garbage_instead_of_a_request_line_is_400_empty",
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
        "sender-a/key-1#",
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
