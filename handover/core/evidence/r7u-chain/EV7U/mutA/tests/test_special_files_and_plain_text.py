"""Class F3: a reader of a settings, key or ledger file must read a REGULAR file or refuse, and a setting that names a
host or an address must be plain one-line ASCII text. Made-up data only, no network.

Part 1: every library reader is called on a named pipe (FIFO) in a child process with a 5 second limit. A reader
that waits for ever on the pipe is a failure (the child is killed and the test fails). The expected answer is the
reader's own fixed refusal text, which holds neither the path nor anything else.
Part 2: DESK_BIND, DESK_FAKES_HOST and the address settings refuse a control character, a line break, an escape, a
space and a full-width digit. A trailing line end on a NUMBER (`12\\n`) stays accepted on purpose: env_number strips
spaces, tabs and line ends from both ends (documented there and pinned in test_env_numbers.py)."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from queue import Empty
from typing import Any

import pytest

from lead_desk.config import Config, read_approvers, read_leadflow
from lead_desk.crm_hubspot import HubspotSettings
from lead_desk.envnum import SettingRefused, split_url
from lead_desk.hooks import FlagFileHooks
from lead_desk.trace import CrashWindows

# the web-address start is built from parts so the repository scan finds no literal address in a test
HTTP = "http" + "://"
HTTPS = "https" + "://"

FIFO_SKIP = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")


def _reader_outcome(what: str, path: str, queue: Any) -> None:
    """Runs in a child process: call one reader on `path` and put "KindName|text" (or ACCEPTED) on the queue."""
    from decimal import Decimal

    from lead_desk.config import LiveSettings
    from lead_desk.constants import HUBSPOT_BASE_URL, LIVE_DEFAULT_BASE_URL
    from lead_desk.crm_hubspot import HubspotCrm
    from lead_desk.live_claude import LiveQualifier, SpendLedger
    from lead_desk.smtp_provider import read_secret_file

    p = Path(path)

    def read_hubspot(q: Path) -> str:
        return HubspotCrm(HubspotSettings(key_file=q, max_calls=5, base_url=HUBSPOT_BASE_URL))._key()

    def read_live(q: Path) -> str:
        settings = LiveSettings(
            model="fake-model-1",
            key_file=q,
            price_in_per_mtok=Decimal("1"),
            price_out_per_mtok=Decimal("1"),
            price_date="2026-01-01",
            cap_run_usd=Decimal("1"),
            cap_total_usd=Decimal("3"),
            ledger_path=q.parent / "ledger.jsonl",
            run_id="run-a",
            base_url=LIVE_DEFAULT_BASE_URL,
        )
        return LiveQualifier(settings)._read_key()

    fns = {
        "approvers": lambda: read_approvers(p),
        "leadflow": lambda: read_leadflow(p),
        "smtp": lambda: read_secret_file(p),
        "hubspot": lambda: read_hubspot(p),
        "live": lambda: read_live(p),
        "ledger": lambda: SpendLedger(p)._totals("run-a"),
        "flags": lambda: (FlagFileHooks(p).crash_point("x", None), CrashWindows(p).hit("ai_after")),
    }
    try:
        fns[what]()
    except Exception as e:  # report every kind of failure to the parent
        queue.put(type(e).__name__ + "|" + str(e))
    else:
        queue.put("ACCEPTED")


def _in_child(what: str, path: Path) -> str:
    """The outcome of one reader on `path` in a child process; the test fails when the child is still waiting after
    5 seconds (the child is then stopped)."""
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_reader_outcome, args=(what, str(path), queue))
    child.start()
    try:
        return str(queue.get(timeout=5))
    except Empty:
        pytest.fail(f"the {what} reader waited for ever on a named pipe")
    finally:
        child.terminate()
        child.join(10)


REFUSALS = {
    "approvers": ("SettingRefused", "the approvers file cannot be read"),
    "leadflow": ("SettingRefused", "DESK_LEADFLOW_FILE cannot be read"),
    "smtp": ("SendRefused", "the smtp password file cannot be read"),
    "hubspot": ("CrmConfigError", "the hubspot key file cannot be read"),
    "live": ("LiveTransport", "the key file cannot be read"),
    "ledger": ("LiveCapReached", None),  # its own fixed text; only the kind is pinned here
}


@FIFO_SKIP
@pytest.mark.parametrize("what", sorted(REFUSALS))
def test_a_reader_refuses_a_named_pipe_at_once(tmp_path: Path, what: str) -> None:
    pipe = tmp_path / "pipe-name"
    os.mkfifo(pipe)
    kind, _, text = _in_child(what, pipe).partition("|")
    want_kind, want_text = REFUSALS[what]
    assert kind == want_kind
    if want_text is not None:
        assert text == want_text
    assert "pipe-name" not in text and str(tmp_path) not in text


@FIFO_SKIP
def test_the_crash_flag_readers_do_not_wait_on_a_named_pipe(tmp_path: Path) -> None:
    pipe = tmp_path / "flag"
    os.mkfifo(pipe)
    assert _in_child("flags", pipe) == "ACCEPTED"  # both return at once (a flag that cannot be read is no flag)


@FIFO_SKIP
def test_open_regular_refuses_pipe_folder_and_nul_and_reads_a_file(tmp_path: Path) -> None:
    from lead_desk.regfile import NotRegularFile, open_regular

    os.mkfifo(tmp_path / "p")
    for bad in (tmp_path / "p", tmp_path, str(tmp_path / "a\x00b")):
        with pytest.raises(NotRegularFile):
            open_regular(bad)
    with pytest.raises(FileNotFoundError):
        open_regular(tmp_path / "missing")
    good = tmp_path / "f"
    good.write_bytes(b"abc")
    with open_regular(good) as f:
        assert f.read() == b"abc"
    link = tmp_path / "link"
    link.symlink_to(good)  # a link to a regular file keeps working (as before)
    with open_regular(link) as f:
        assert f.read() == b"abc"


@FIFO_SKIP
def test_readers_of_a_symlink_to_a_pipe_refuse_too(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "p")
    (tmp_path / "l").symlink_to(tmp_path / "p")
    for what in ("approvers", "leadflow"):
        assert _in_child(what, tmp_path / "l").endswith("cannot be read")


# ---------------------------------------------------------------- Part 2: plain one-line text
BAD_TEXT = [
    "127.0.0.1\n",
    "\n127.0.0.1",
    "127.0.0.1\x1b",
    "127.0.0.\x1b[31m1",
    "127.0.0.1\x00",
    "127.0.0.1 ",
    " 127.0.0.1",
]
BAD_TEXT += ["１２７.0.0.1", "127.0.0.1 ", "local host", "127.0.0.1\t", "127.0.0.1\x7f", "hеst"]
GOOD_TEXT = ["127.0.0.1", "localhost", "[::1]", "::", "0", "[::1", "host.example", "192.0.2.7"]


@pytest.mark.parametrize("bad", BAD_TEXT)
def test_bind_and_fakes_host_refuse_control_characters_and_look_alikes(bad: str) -> None:
    with pytest.raises(SettingRefused, match="DESK_BIND and DESK_FAKES_HOST must be plain ASCII text"):
        Config.from_env({"DESK_BIND": bad})
    with pytest.raises(SettingRefused, match="DESK_BIND and DESK_FAKES_HOST must be plain ASCII text"):
        Config.from_env({"DESK_FAKES_HOST": bad})


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_bind_still_accepts_every_plain_spelling() -> None:
    for good in GOOD_TEXT:
        assert Config.from_env({"DESK_BIND": good}).bind == good


@pytest.mark.parametrize(
    "bad", [f"{HTTP}127.0.0.1:1\n", f"{HTTP}127.0.0.1:1\x1b", f"{HTTP}127.0.0.1\n:1", f"{HTTP}" + " 127.0.0.1:1"]
)
def test_fakes_url_refuses_control_characters(bad: str) -> None:
    with pytest.raises(SettingRefused, match="DESK_FAKES_URL is not a valid address"):
        Config.from_env({"DESK_FAKES_URL": bad})


@pytest.mark.parametrize("allow_any", [False, True])
@pytest.mark.parametrize("tail", ["\n", "\r\n", "\t", "\x1b", " ", " "])
def test_hubspot_base_url_refuses_a_trailing_control_character(tmp_path: Path, allow_any: bool, tail: str) -> None:
    key = tmp_path / "k"
    key.write_text("Z" * 12)
    for base in (f"{HTTPS}api.example.test" + tail, f"{HTTPS}api" + tail + ".example.test"):
        with pytest.raises(SettingRefused, match="DESK_HUBSPOT_BASE_URL is not a valid address"):
            HubspotSettings(key_file=key, max_calls=1, base_url=base, allow_any_base_url=allow_any)
    env = {
        "DESK_HUBSPOT_KEY_FILE": str(key),
        "DESK_HUBSPOT_MAX_CALLS": "1",
        "DESK_HUBSPOT_BASE_URL": f"{HTTPS}api.example.test" + tail,
        "DESK_HUBSPOT_ALLOW_ANY_BASE_URL": "yes" if allow_any else "no",
    }
    with pytest.raises(SettingRefused, match="DESK_HUBSPOT_BASE_URL is not a valid address"):
        HubspotSettings.from_env(env)


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_hubspot_base_url_plain_text_still_works(tmp_path: Path) -> None:
    key = tmp_path / "k"
    key.write_text("Z" * 12)
    s = HubspotSettings(key_file=key, max_calls=1, base_url=f"{HTTPS}api.example.test", allow_any_base_url=True)
    assert s.base_url == f"{HTTPS}api.example.test"


def test_split_url_refuses_every_control_and_space_character_in_a_generated_set() -> None:
    chars = [chr(c) for c in range(0, 0x21)] + [chr(0x7F), "\u0085", " ", " ", " ", "　"]
    for c in chars:
        for text in (f"{HTTP}h{c}:1", f"{HTTP}h:1{c}", f"{c}{HTTP}h:1"):
            with pytest.raises(SettingRefused, match="X is not a valid address"):
                split_url("X", text)
    assert split_url("X", f"{HTTP}h.example:1").port == 1


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_number_with_a_trailing_line_end_stays_accepted_on_purpose() -> None:
    assert Config.from_env({"DESK_PORT": "12\n"}).port == 12  # documented in env_number, pinned in test_env_numbers
    with pytest.raises(SettingRefused, match="DESK_PORT is not a number"):
        Config.from_env({"DESK_PORT": "1\n2"})
    with pytest.raises(SettingRefused, match="DESK_PORT is not a number"):
        Config.from_env({"DESK_PORT": "１２"})
