"""Real services run: the desk with a REAL CRM (HubSpot free plan) and REAL e-mail (Gmail over SMTP), then a read-back
that COUNTS what really arrived. You run it from your own terminal.

  python scripts/run_real_check.py --config PATH_TO_CONFIG [--live-model] [--cleanup]

PATH_TO_CONFIG is a text file OUTSIDE the repository, one NAME=VALUE per line (# starts a comment). Secrets are never in
it: only the paths of the key files. Required names (the script refuses to start without every one of them):
  DESK_DB_PATH                    a new database file for this run (a folder you can delete afterwards)
  DESK_HUBSPOT_KEY_FILE           one-line file with the HubSpot service key
  DESK_HUBSPOT_MAX_CALLS          hard cap of HubSpot calls per desk process
  REAL_HUBSPOT_READBACK_MAX_CALLS hard cap of HubSpot calls of this script's read-back and clean-up
  DESK_SMTPP_HOST, DESK_SMTPP_USER, DESK_SMTPP_PASSWORD_FILE, DESK_SMTPP_FROM, DESK_SMTPP_RECIPIENTS (your own
                                  inboxes, comma separated), DESK_SMTPP_MAX_SENDS (hard cap per desk process)
  REAL_IMAP_1_USER, REAL_IMAP_1_PASSWORD_FILE, REAL_IMAP_2_USER, REAL_IMAP_2_PASSWORD_FILE  the two counted mailboxes,
                                  in the order of DESK_SMTPP_RECIPIENTS (more can be added: REAL_IMAP_3_*)
Optional: DESK_SMTPP_PORT, DESK_SMTPP_SECURITY, DESK_SMTPP_CA_FILE,
REAL_IMAP_n_HOST (default: MAIL_IMAP_DEFAULT_HOST in src/lead_desk/constants.py),
REAL_IMAP_n_PORT, REAL_IMAP_n_CA_FILE, REAL_IMAP_n_FOLDERS (comma list, default INBOX and the spam folder),
REAL_PERSONS (default 12), REAL_DRAIN_SECONDS
(default 150), REAL_MAIL_WAIT_SECONDS (default 90),
REAL_MAIL_SETTLE_SECONDS (default MAIL_POLL_SECONDS), REAL_RESULT_FILE (default result.json next to the database),
DESK_HUBSPOT_BASE_URL, DESK_PORT. With --live-model also every DESK_LIVE_* name (its own cap in dollars; the key goes
only to the provider's own address or this computer unless the config says DESK_LIVE_ALLOW_ANY_BASE_URL=yes).
Every name is upper-case letters, digits and underscore (a lower-case name is refused). DESK_DB_PATH must NOT exist
yet: the clean-up relies on a book that holds only this run's leads.

What it does: starts the desk on loopback, sends made-up people (@example.com, labelled) through both doors (new
people, repeats through the same door, repeats through the other door, one person with two different e-mail
addresses), stops the desk hard once after the load started (the crash), starts it again, re-sends what was lost,
waits until the desk is idle, then READS BACK: the HubSpot contacts that carry this run's
lead ids, the mails in your inbox
(counted by a header, no body or address is read) and the desk's own book. It prints ONLY counts and a pass/fail table
and writes the same to a JSON file. It never prints a key, an address or a message text.
Nothing is sent to the made-up people: every mail goes to your own inboxes. It first prints the worst case of calls,
mails and dollars and asks y/N."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import re
import shutil
import socket
import stat
import subprocess  # noqa: S404
import sys
import tempfile
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable, Collection
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository folder: tools/ and scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # the desk code, ahead of it

from http_guard import open_http, read_reply

from lead_desk.adapters import CrmError
from lead_desk.config import Config
from lead_desk.constants import (
    CAP_COUNT_MAX,
    DRY_PORT_COUNT,
    EXIT_CHECK_FAILED,
    EXIT_REFUSED,
    EXIT_SIMULATED_KILL,
    EXIT_STOPPED,
    LEAD_ID_HEX_CHARS,
    LEAD_ID_PREFIX,
    MAIL_IMAP_DEFAULT_HOST,
    MAIL_SPAM_FOLDER,
    MODEL_CALLS_PER_LEAD_MAX,
    PORT_MAX,
    REAL_PERSONS_MAX,
    REAL_SECONDS_MAX,
)
from lead_desk.crm_hubspot import HubspotCrm, HubspotSettings
from lead_desk.envnum import env_number
from lead_desk.gate import SEND_WORKERS_MAX
from lead_desk.identity import normalise_email
from lead_desk.imap_count import (
    ImapConnectionError,
    ImapCountError,
    ImapSettings,
    ImapTotalTimeout,
    bad_folder_name,
    counts_by_inbox,
)
from lead_desk.jsonread import loads_bounded
from lead_desk.live_claude import question_text, request_body, worst_case_usd
from lead_desk.regfile import (
    FileRefused,
    load_json_file,
    open_output,
    read_regular_text,
    read_secret_line,
    write_regular_text,
)
from lead_desk.scrub import secret_boundary
from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox
from lead_desk.tls_trust import context_from_ca_file
from load_tools.check_invariants import InputError, read_book, render_table, run_checks
from load_tools.load_driver import send_with_retries
from tools.pathconfine import confine_anywhere, has_control_character
from tools.refusing_args import RefusingParser, refusal

REPO = Path(__file__).resolve().parents[1]

EXIT_FAILED = EXIT_CHECK_FAILED  # the check ran to its end and a check did not hold
# Made-up lead addresses on the reserved example domain (not `.test`: a real CRM may refuse that as an invalid
# address: an assumption). Nothing is ever
# mailed to it: follow-ups go only to the configured inboxes
# (DESK_SMTPP_RECIPIENTS).
EMAIL_DOMAIN = "example.com"
DEFAULT_PERSONS = 12
MIN_PERSONS = 8
DESK_START_SECONDS = 20.0
CRASH_WAIT_SECONDS = 60.0
POLL_SECONDS = 1.0
MAIL_POLL_SECONDS = 10.0
IMAP_LOGINS_MAX = 12
POLL_EXTRA_LOGINS = 3  # after the last wanted mail was seen: one settle poll; at the limit: one final poll; and the
# one repeat of a poll whose connection failed
REPEAT_POLL_SECONDS = 1.0  # a pause before a poll whose connection dropped is repeated
RETRY_TOTAL_FACTOR = 2.0  # a first mailbox read that ran out of time is tried once more with this many times the time
CONFIG_NAME = re.compile(r"[A-Z0-9_]+")  # a setting name: upper-case letters, digits and underscore only
DRY_KEY = "dry-" + "key-" + "for-" + "self-" + "test"  # the made-up key of the fake HubSpot (built from parts)
CRASH_REASON = "crash_while_sending"  # what the desk writes on a follow-up that was being sent when it stopped
PRE_CRASH_DRAIN_SECONDS = 60.0  # wait for the first batch to settle before the crash is armed
# An address starts where a run of address characters starts (the look-behind), so each run is read once. One character
# is taken before the repeated part, and the repeated part cannot take an "@": the first "@" after the first character
# is the one that splits the address, so nothing is tried two ways (the plain form costs n squared steps on a text of
# n address characters, and a text with no "@" is the worst case). It finds the same text as the plain form.
_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+")
CRASH_POINT = "D2"  # after the sender answered and before the result is recorded: the worst moment for a blind sender
MIN_READBACK_CALLS = 5  # fewest HubSpot calls the read-back may be given (a listing page, a few archives)
MODEL_CALLS_PER_LEAD = MODEL_CALLS_PER_LEAD_MAX  # the bound check 5 uses: one source
REQUIRED = (
    "DESK_DB_PATH",
    "DESK_HUBSPOT_KEY_FILE",
    "DESK_HUBSPOT_MAX_CALLS",
    "REAL_HUBSPOT_READBACK_MAX_CALLS",
    "DESK_SMTPP_HOST",
    "DESK_SMTPP_USER",
    "DESK_SMTPP_PASSWORD_FILE",
    "DESK_SMTPP_FROM",
    "DESK_SMTPP_RECIPIENTS",
    "DESK_SMTPP_MAX_SENDS",
    "REAL_IMAP_1_USER",
    "REAL_IMAP_1_PASSWORD_FILE",
    "REAL_IMAP_2_USER",
    "REAL_IMAP_2_PASSWORD_FILE",
)


class DryFakes:
    """Local stand-ins for HubSpot, the mail server and the two mailboxes (demo_only), so the whole script runs end to
    end without any real service. The mailboxes mirror what the fake mail server accepted. Ports: ephemeral (the
    system picks free ones) unless `base_port` is given: then the desk uses base_port, the fake HubSpot base_port + 1,
    the mail server + 2 and the two mailboxes + 3 and + 4. `smtp_script` is a script of demo_only.fake_smtp_tls
    (for example "final_452": every send ends in doubt, so every follow-up ends `unknown`). `close()` stops the fake
    servers and removes the folder that holds the test certificate, its key and the key files."""

    HOST = "localhost"

    def __init__(self, folder: Path, base_port: int | None = None, smtp_script: str = "ok") -> None:
        from demo_only.fake_hubspot import HubspotState, serve  # noqa: PLC0415
        from demo_only.fake_imap import FakeImap  # noqa: PLC0415
        from demo_only.fake_smtp_tls import FakeSmtp, make_cert  # noqa: PLC0415

        def port(offset: int) -> int:
            return 0 if base_port is None else base_port + offset

        self._private = folder / "fakes"  # certificate, keys: removed by close()
        self._private.mkdir(parents=True, exist_ok=True)
        self._stop = threading.Event()
        self._servers: list[Any] = []
        made = make_cert(self._private, self.HOST)
        if made is None:
            shutil.rmtree(self._private, ignore_errors=True)
            raise ValueError("the openssl program is needed for --dry-fakes")
        cert, key = made
        self.state = HubspotState(DRY_KEY, "ok")
        # modelled on the assumption that a real CRM may refuse a made-up `.test` address (an assumption)
        self.state.reject_test_domain = True
        self.hub, self._hub_thread, base = serve(self.state, "127.0.0.1", port(1))
        self.smtp = FakeSmtp(cert, key, self.HOST, smtp_script, port=port(2))
        self.imaps = [
            FakeImap(cert, key, self.HOST, {"INBOX": [], MAIL_SPAM_FOLDER: []}, port=port(3 + n)) for n in range(2)
        ]
        recipients = ("inbox-a@example.test", "inbox-b@example.test")
        for im, rcpt in zip(self.imaps, recipients, strict=True):
            im.user = rcpt  # the mailbox login is the recipient's address, as for a real mailbox
        write_regular_text(self._private / "hs.key", self.state.key)
        write_regular_text(self._private / "pw.txt", self.smtp.password)
        pw = str(self._private / "pw.txt")
        self.env = {
            "DESK_DB_PATH": str(folder / "run" / "desk.db"),
            "DESK_PORT": str(port(0) or free_port()),
            "DESK_HUBSPOT_KEY_FILE": str(self._private / "hs.key"),
            "DESK_HUBSPOT_BASE_URL": base,
            "DESK_HUBSPOT_ALLOW_ANY_BASE_URL": "yes",
            "DESK_HUBSPOT_MAX_CALLS": "600",
            "REAL_HUBSPOT_READBACK_MAX_CALLS": "300",
            "DESK_SMTPP_HOST": self.HOST,
            "DESK_SMTPP_PORT": str(self.smtp.port),
            "DESK_SMTPP_USER": self.smtp.user,
            "DESK_SMTPP_PASSWORD_FILE": pw,
            "DESK_SMTPP_FROM": "desk@example.test",
            "DESK_SMTPP_RECIPIENTS": ",".join(recipients),
            "DESK_SMTPP_MAX_SENDS": "200",
            "DESK_SMTPP_CA_FILE": str(cert),
            "REAL_PERSONS": "8",
            # the dry run proves logic, not speed: the recovery drain (back-off 1+2+4+8 s, 5 s give-backs, 30 s
            # stuck grace)
            # took 44 s idle and 114 s under four heavy jobs, so the dry ceiling is 240 s; the real default (150 s) and
            # check_drain are untouched
            "REAL_DRAIN_SECONDS": "240",
            "REAL_MAIL_WAIT_SECONDS": "10",
            "REAL_MAIL_SETTLE_SECONDS": "1",
        }
        for n, (im, rcpt) in enumerate(zip(self.imaps, recipients, strict=True), 1):
            self.env |= {
                f"REAL_IMAP_{n}_HOST": self.HOST,
                f"REAL_IMAP_{n}_USER": rcpt,
                f"REAL_IMAP_{n}_PASSWORD_FILE": pw,
                f"REAL_IMAP_{n}_PORT": str(im.port),
                f"REAL_IMAP_{n}_CA_FILE": str(cert),
            }
        self._mirror_thread = threading.Thread(target=self._mirror, daemon=True)
        self._mirror_thread.start()

    def _mirror(self) -> None:
        import re  # noqa: PLC0415

        recipients = self.env["DESK_SMTPP_RECIPIENTS"].split(",")
        while not self._stop.is_set():
            for n, im in enumerate(self.imaps):  # recipient n (in the configured order) is mailbox n
                found = [
                    re.search(rb"X-Send-Key: (\S+)", d)
                    for *_, rcpt, d in list(self.smtp.messages)
                    if rcpt == recipients[n]
                ]
                im.folders["INBOX"][:] = [m.group(1).decode() for m in found if m]
            self._stop.wait(0.3)

    def close(self) -> None:
        from demo_only.fake_hubspot import stop  # noqa: PLC0415

        self._stop.set()
        self._mirror_thread.join(2)
        stop(self.hub, self._hub_thread, self.state)
        self.smtp.close()
        for im in self.imaps:
            im.close()
        shutil.rmtree(self._private, ignore_errors=True)


_EPOCH0 = time.time()  # wall-clock: read once, the only calendar read; epoch_now() adds monotonic time to it
_MONO0 = time.monotonic()


def epoch_now() -> float:
    """Epoch seconds that only move forward at the true pace: the wall clock read ONCE at start-up plus the monotonic
    time since. A clock correction (container, NTP) cannot make the drain time or the schedule jump; the desk book's
    own stamps are compared with these, so they must stay on the same scale."""
    return _EPOCH0 + (time.monotonic() - _MONO0)


def free_port() -> int:
    """A port the system has just shown to be free (the desk child process binds it a moment later)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def mask_addresses(text: str) -> str:
    """Every e-mail address in `text` becomes <address>: a failure table must not print the made-up (or any) address."""
    return _ADDRESS.sub("<address>", text)


def mask_result(result: dict[str, Any]) -> dict[str, Any]:
    """The check result with every string passed through mask_addresses."""

    def walk(x: Any) -> Any:
        if isinstance(x, str):
            return mask_addresses(x)
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    out: dict[str, Any] = walk(result)
    return out


def scrub(text: str, env: dict[str, str]) -> str:
    """`text` without any setting value (4 characters or more) it happens to contain: an error line may name a
    setting, never print what the setting holds. Every place where a value occurs is marked first and the places
    that touch or overlap are joined, so a value that holds another, or that overlaps another, is hidden whole."""
    spans: list[tuple[int, int]] = []
    for v in {v for v in env.values() if len(v) >= 4}:  # noqa: PLR2004
        at = text.find(v)
        while at != -1:
            spans.append((at, at + len(v)))
            at = text.find(v, at + 1)
    out: list[str] = []
    end = 0
    for lo, hi in sorted(spans):
        if lo >= end:
            out.append(text[end:lo])
            out.append("<value>")
            end = hi
        elif hi > end:
            end = hi  # overlaps the span just written: the hidden part grows, no second marker
    out.append(text[end:])
    return "".join(out)


def floor_checks(
    book: dict[str, Any],
    expected_leads: int,
    settled_before_crash: int,
    mail_per_lead: Counter[str],
    crm_pairs: list[tuple[str, str]],
    smtp_stats: dict[str, int],
    crash_exit: int | None,
    sending_at_kill: int,
    last_poll_failed: bool = False,
    poll_repeats: int = 0,
) -> list[dict[str, Any]]:
    """Floors the seven checks do not have: they excuse every `unknown` follow-up, so a run in which nothing was sent
    and nothing was stored could pass them. Each result has the shape of a check of load_tools.check_invariants.
      F1 the book holds the expected leads; at least all but the crash window ended `sent` (the window = the follow-ups
         the desk itself marked crash_while_sending, at most the desk's send workers); and at least
         `settled_before_crash` ended `sent` (the first batch had settled before the crash was armed). The window is
         also at most `sending_at_kill`, the follow-ups the book showed in state `sending` right after the first
         desk process was stopped: an `unknown` that is not one of those is not excused;
      F2 the mailboxes hold at least one mail per `sent` follow-up (counted by the header X-Send-Key, all mailboxes);
      F3 the CRM holds at least one contact per lead marked CRM-done;
      F4 the mails sent are at most leads + unknown leads, and the counter file exists (a missing file proves nothing).
         "Mails sent" is the LARGER of the desk's own counter (both processes together) and the mails counted in the
         mailboxes, so a counter that lost a count (a process killed before it wrote) cannot hide a double send;
      F5 the first desk process really stopped at the crash point: its exit code is the simulated-kill code, not None
         (it did not stop in time) and not 0 (it ended on its own). A crash that did not happen proves nothing;
      F6 the last mailbox read worked: a read that failed or ran out of time after earlier reads keeps the earlier
         counts, so a late second delivery could be missing from them (and from F4)."""
    followups = book["followups"]
    leads = len(book["leads"])
    states = Counter(s for s, _, _ in followups.values())
    sent, unknown = states["sent"], states["unknown"]
    reasons = book.get("last_errors", {})
    window = min(
        sum(1 for lid, (s, _, _) in followups.items() if s == "unknown" and reasons.get(lid) == CRASH_REASON),
        SEND_WORKERS_MAX,
        max(sending_at_kill, 0),
    )
    crm_done = sum(1 for _, d, _ in followups.values() if d == 1)
    mails = sum(mail_per_lead.values())
    desk_sent = smtp_stats.get("sent")
    sent_total = None if desk_sent is None else max(desk_sent, mails)

    def res(n: int, name: str, ok: bool, detail: str, values: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f"F{n}",
            "name": name,
            "ok": ok,
            "detail": detail,
            "offender_count": 0,
            "offenders": [],
            "values": values,
        }

    min_sent = max(settled_before_crash, expected_leads - window)
    return [
        res(
            1,
            "the expected leads exist and almost all of them ended sent",
            leads == expected_leads and sent >= min_sent,
            f"{leads} leads (expected {expected_leads}); {sent} sent, {unknown} unknown; crash window {window}; "
            f"at least {min_sent} sent",
            {
                "leads": leads,
                "expected_leads": expected_leads,
                "sent": sent,
                "unknown": unknown,
                "crash_window": window,
                "settled_before_crash": settled_before_crash,
                "min_sent": min_sent,
            },
        ),
        res(
            2,
            "the mailboxes hold at least one mail for every sent follow-up",
            mails >= sent,
            f"{mails} mails in the mailboxes for {sent} sent follow-ups",
            {"mails_in_mailbox": mails, "sent": sent},
        ),
        res(
            3,
            "the CRM holds a contact for every lead marked done",
            len(crm_pairs) >= crm_done,
            f"{len(crm_pairs)} CRM contacts with this run's lead ids for {crm_done} leads marked done "
            "(this relies on the CRM list showing a contact right after it was created: UNVERIFIED with HubSpot)",
            {"crm_contacts_with_our_ids": len(crm_pairs), "leads_crm_done": crm_done},
        ),
        res(
            4,
            "the desk sent no more mails than leads plus unknown leads",
            sent_total is not None and sent_total <= leads + unknown,
            f"the desk's mail counter says {desk_sent} sent (both processes together) and {mails} mails were counted "
            f"in the mailboxes: the larger, {sent_total}, is used; allowed at most "
            f"{leads} leads + {unknown} unknown = {leads + unknown}",
            {
                "desk_sent_total": desk_sent,
                "mails_in_mailbox": mails,
                "sent_used": sent_total,
                "leads": leads,
                "unknown": unknown,
                "allowed_max": leads + unknown,
            },
        ),
        res(
            5,
            "the first desk process really stopped at the crash point",
            crash_exit == EXIT_SIMULATED_KILL,
            f"the first desk process ended with exit code {crash_exit} "
            f"(expected {EXIT_SIMULATED_KILL}: a stop on purpose)",
            {"crash_exit_code": crash_exit, "expected": EXIT_SIMULATED_KILL},
        ),
        res(
            6,
            "the last mailbox read worked",
            not last_poll_failed,
            "the last mailbox read failed or ran out of time: the counts are those of an earlier read, so a late "
            "second delivery may be missing from the mail counts"
            if last_poll_failed
            else "the last mailbox read worked",
            {"last_poll_failed": last_poll_failed, "poll_repeats": poll_repeats},
        ),
    ]


def sending_rows(db: Path) -> int:
    """How many follow-ups the book shows in state `sending` (read right after the first desk process was stopped):
    the ones that were in flight at the kill. An unreadable book counts 0 (the later read then fails loudly)."""
    try:
        return sum(1 for s, _, _ in read_book(db, anywhere=True)["followups"].values() if s == "sending")
    except InputError:
        return 0


def unknown_allowance(sending_at_kill: int) -> int:
    """The most follow-ups that may end `unknown`: those in flight at the kill, never more than the send workers."""
    return min(max(sending_at_kill, 0), SEND_WORKERS_MAX)


def expected_keys_by_inbox(
    lead_ids: Collection[str], pr: ProviderSettings, boxes: list[ImapSettings]
) -> list[set[str]]:
    """For each counted mailbox, the lead ids whose mail is addressed to it (the same hash the sender uses): only
    those justify the slow header scan when the search misses them."""
    outbox = SmtpProviderOutbox(pr)
    by_user = {b.user.strip().lower(): n for n, b in enumerate(boxes)}
    out: list[set[str]] = [set() for _ in boxes]
    for lid in lead_ids:
        n = by_user.get(outbox.recipient_for(lid).strip().lower())
        if n is not None:
            out[n].add(lid)
    return out


def merge_counts(
    old: list[dict[str, dict[str, int]]], fresh: list[dict[str, dict[str, int]]]
) -> list[dict[str, dict[str, int]]]:
    """Per mailbox, folder and key the LARGER count: mails are not taken out of a mailbox during the run, so a poll
    without the slow scan (which may miss a key the search cannot find) never lowers what an earlier poll saw."""
    out: list[dict[str, dict[str, int]]] = []
    for n, box in enumerate(fresh):
        merged = {f: dict(keys) for f, keys in (old[n] if n < len(old) else {}).items()}
        for f, keys in box.items():
            slot = merged.setdefault(f, {})
            for k, c in keys.items():
                slot[k] = max(slot.get(k, 0), c)
        out.append(merged)
    return out


def poll_mailboxes(
    boxes: list[ImapSettings],
    lead_ids: set[str],
    expected: list[set[str]],
    wanted: int,
    wait_seconds: float,
    settle_seconds: float,
    count: Callable[..., list[dict[str, dict[str, int]]]] = counts_by_inbox,
    sleep: Callable[[float], None] = time.sleep,
    sent_ids: Collection[str] | None = None,
    stats: dict[str, int] | None = None,
) -> tuple[list[dict[str, dict[str, int]]], int, bool]:
    """(counts per mailbox, number of logins, whether the LAST poll failed). Polls until `wanted` of the `sent_ids`
    (default: all lead ids; only the follow-ups that really ended `sent` count, a failed or pending lead's mail does
    not) were seen once, then waits `settle_seconds` and polls ONCE MORE (a second delivery that arrives a little
    later is counted). The slow header scan (the fallback when the search misses a mail that was expected) runs on
    the FIRST and the LAST poll only. If the very first poll runs out of its total time it is tried once more with
    more time and the line says so. A poll that fails after an earlier poll succeeded keeps the earlier counts, and
    the returned flag is True: the caller must show it (a late duplicate delivery could be hidden). A poll that fails
    on its CONNECTION (not on the total time limit, a login, a folder or a key) is repeated once after a short pause
    before it counts as failed; `stats["poll_repeats"]` says how many repeats there were. The longer time of the
    first-read retry is used for that one poll only, so the time printed in the banner stays true."""
    per_inbox: list[dict[str, dict[str, int]]] = [{} for _ in boxes]
    sent = set(lead_ids if sent_ids is None else sent_ids)
    logins, have_full, failed, retried, final, scan = 0, False, False, False, False, True
    repeated = False  # the poll just failed on its connection and is being tried once more
    repeats = 0
    base = boxes  # the configured time limits; the doubled limit of the first-read retry is for one poll only
    end = time.monotonic() + wait_seconds
    while True:
        logins += 1
        try:
            fresh = count(boxes, "L", keys=lead_ids, expected_by_inbox=expected, scan=scan)
        except ImapTotalTimeout:
            if not have_full and not retried:
                retried = True
                print("mailbox read: the first read ran out of time; trying once more with more time")
                boxes = [replace(b, total_seconds=b.total_seconds * RETRY_TOTAL_FACTOR) for b in base]
                continue
            failed = True
            print(
                "mailbox read: the last poll hit the total time limit; the counts are those of the poll before it"
                if have_full
                else "mailbox read failed: the mailbox read took longer than its total time limit"
            )
            break
        except ImapCountError as e:
            if (
                isinstance(e, ImapConnectionError) and not repeated
            ):  # one dropped connection must not fail the last read of a run that had counted all mails
                repeated = True
                repeats += 1
                if stats is not None:
                    stats["poll_repeats"] = repeats
                print("mailbox read: a poll failed on its connection; trying that poll once more")
                sleep(REPEAT_POLL_SECONDS)
                continue
            failed = True
            print(f"mailbox read failed: {e}")
            break
        per_inbox, have_full, repeated, boxes = merge_counts(per_inbox, fresh), True, False, base
        if final:
            break
        got = {k for box in per_inbox for f in box.values() for k in f if k in sent}
        if len(got) >= wanted:
            final, scan = True, True
            sleep(settle_seconds)
        elif time.monotonic() > end or logins >= IMAP_LOGINS_MAX:
            final, scan = True, True  # out of time: one last read, with the scan, to see what the search missed
        else:
            scan = False
            sleep(MAIL_POLL_SECONDS)
    return per_inbox, logins, failed


def _readback_failed(
    a: argparse.Namespace,
    run_dir: Path,
    env: dict[str, str],
    error: CrmError,
    leads: int,
    hub_stats: dict[str, int],
) -> int:
    """The CRM read-back stopped (an error or the read-back call cap): print counts only, write a result file with the
    same note and end with EXIT_FAILED, so the person running the check knows how many contacts may still have to be
    archived by hand."""
    created = hub_stats.get("created")
    note = (
        "the CRM read-back failed: the contacts of this run were NOT counted"
        + (" and NOT archived" if a.cleanup else "")
        + ". The desk created "
        + (str(created) if created is not None else "an unknown number of")
        + " contacts in total (its own counter); up to that many may still be in HubSpot, "
        + "their lead ids start with L and are listed in the desk's book. Archive them by hand."
    )
    print(note)
    write_result(
        result_path(env, run_dir),
        {"ok": False, "note": note, "leads_in_book": leads, "hubspot_calls_by_the_desk": hub_stats},
    )
    return EXIT_FAILED


class CounterUnreadable(ValueError):
    """The desk's own count of the contacts it created is not known (no counter file, an unreadable or half-written
    one, or one without the number). Nothing may then be said about contacts left in HubSpot, so the run fails."""


def contacts_not_accounted_for(
    created: int | None, accounted: int, open_creates: int = 0, leads: int | None = None
) -> int:
    """How many contacts the desk may have created that the check did not account for. `created` is the desk's own
    counter for THIS run (contacts HubSpot answered 201 for and the desk counted), `open_creates` the creates that were
    sent and whose outcome is not known (a desk stopped hard before the count, or a timeout, a
    transport error, a 5xx: the contact may exist and no counter shows it), `leads` the leads in the book (each lead
    makes at most one contact, so the possible number can never be more than that), `accounted` the contacts the CRM
    list showed (archived or left). The possible number is `created + open_creates`, at most `leads`; what the list
    did not show of it is the answer. More shown than possible is not an error (a 409 answer is no create).
    `created` None means the counter is not known: that raises CounterUnreadable (fail closed). The check that
    compares the CRM list with the leads marked CRM-done (F3) never reads the counter, so it cannot cover this."""
    if created is None:
        raise CounterUnreadable("the number of contacts the desk created is not known")
    possible = created + max(0, open_creates)
    if leads is not None:
        possible = min(possible, leads)
    return max(0, possible - accounted)


def exit_code_of(ok: bool, written: bool, left: list[str], unseen: int, counter_known: bool) -> int:
    """0 only if every check holds, the result file was written, no listed contact was left, no created contact is
    unaccounted for and the desk's contact counter could be read. The one place the end of the run is decided."""
    return 0 if ok and written and not left and not unseen and counter_known else EXIT_FAILED


def archive_all(crm: HubspotCrm, pairs: list[tuple[str, str]]) -> tuple[int, list[str]]:
    """Archive every contact; one failure does not stop the rest. Returns (archived, contact numbers left behind)."""
    done, left = 0, []
    for _, cid in pairs:
        try:
            crm.archive(cid)
            done += 1
        except CrmError:
            left.append(cid)
    return done, left


def folders_not_found(per_inbox: list[dict[str, dict[str, int]]], inboxes: list[ImapSettings]) -> list[tuple[int, str]]:
    """(mailbox number, folder) of every configured folder the server did not have (a spam folder may be named in
    another language), or of every folder when the mailbox could not be read: those were NOT checked, and a count of 0
    there means nothing."""
    return [
        (n, f) for n, (box, s) in enumerate(zip(per_inbox, inboxes, strict=False), 1) for f in s.folders if f not in box
    ]


def check_mailbox_order(env: dict[str, str], boxes: list[ImapSettings]) -> str | None:
    """None when mailbox n is logged in as the n-th address of DESK_SMTPP_RECIPIENTS, else a fixed refusal text."""
    recipients = [x.strip().lower() for x in env["DESK_SMTPP_RECIPIENTS"].split(",") if x.strip()]
    if len(boxes) != len(recipients) or any(
        b.user.strip().lower() != r for b, r in zip(boxes, recipients, strict=True)
    ):
        return "the mailbox users REAL_IMAP_n_USER must be the addresses of DESK_SMTPP_RECIPIENTS, in the same order"
    return None


def number(name: str, env: dict[str, str], cast: Any, default: Any, *, low: Any = None, high: Any = None) -> Any:
    """A number setting; a bad or out-of-range value raises SettingRefused (a ValueError) naming the setting only (the
    one helper, lead_desk.envnum). Every call site gives its own sane `high`."""
    return env_number(env, name, cast, default, low=low, high=high)


DESK_PORT_DEFAULT = 8765  # the port both desk processes of the check share when DESK_PORT is not written


def desk_port(env: dict[str, str]) -> int:
    """DESK_PORT of the check: absent means DESK_PORT_DEFAULT; a written value must be 1 or more. A written 0 (the
    desk's own "any free port") is refused here, not quietly turned into the default: the second desk process needs the
    same port as the first, so a free-port choice cannot work for this check."""
    value: int = number("DESK_PORT", env, int, DESK_PORT_DEFAULT, low=1, high=PORT_MAX)
    return value


def positive_seconds(name: str, env: dict[str, str], default: float) -> float:
    """A time setting in seconds: a finite number above 0, else ValueError naming the setting only (checked BEFORE any
    real call is made, so a typo cannot surface after real mails were sent)."""
    value: float = number(name, env, float, default, high=REAL_SECONDS_MAX)
    if not (math.isfinite(value) and value > 0):
        raise ValueError(f"{name} must be a number of seconds above 0")
    return value


def imap_settings(env: dict[str, str]) -> list[ImapSettings]:
    """The counted mailboxes REAL_IMAP_1_*, REAL_IMAP_2_* ... (host default MAIL_IMAP_DEFAULT_HOST, a Workspace mailbox
    uses the same host). Mailbox n is the n-th address of DESK_SMTPP_RECIPIENTS."""
    out: list[ImapSettings] = []
    n = 1
    while env.get(f"REAL_IMAP_{n}_USER"):
        p = f"REAL_IMAP_{n}_"
        ca = env.get(p + "CA_FILE")
        if ca is not None and not ca.strip():  # present but blank must not mean "trust the system authorities"
            raise ValueError(f"{p}CA_FILE is empty: remove the line or name a file")
        if not env.get(p + "PASSWORD_FILE", "").strip():
            raise ValueError(f"{p}PASSWORD_FILE is required when {p}USER is set")
        folders = tuple(x.strip() for x in env.get(p + "FOLDERS", f"INBOX,{MAIL_SPAM_FOLDER}").split(",") if x.strip())
        if any(bad_folder_name(f) for f in folders):
            raise ValueError(f"{p}FOLDERS: a folder name must be plain ASCII without quotes or backslashes")
        out.append(
            ImapSettings(
                env.get(p + "HOST", MAIL_IMAP_DEFAULT_HOST),
                env[p + "USER"],
                Path(env[p + "PASSWORD_FILE"]),
                port=number(p + "PORT", env, int, 993, low=1, high=PORT_MAX),
                folders=folders,
                ssl_context=context_from_ca_file(ca, p + "CA_FILE") if ca else None,
            )
        )
        n += 1
    return out


def check_secret_files(hs: HubspotSettings, pr: ProviderSettings, inboxes: list[ImapSettings]) -> None:
    """Read every secret file the run will use, with the same reader the real call uses, BEFORE the Start question:
    a missing, empty, several-line or non-text secret is refused here (ValueError naming the SETTING, never the path or
    the content) and not after the desk has started and spend has been reserved."""
    checks: list[tuple[str, Path, str, str, bool]] = [
        ("DESK_HUBSPOT_KEY_FILE", hs.key_file, "hubspot key", "key", False),
        ("DESK_SMTPP_PASSWORD_FILE", pr.password_file, "smtp password", "password", True),
    ]
    checks += [
        (f"REAL_IMAP_{n}_PASSWORD_FILE", box.password_file, "mailbox password", "password", True)
        for n, box in enumerate(inboxes, start=1)
    ]
    for setting, path, what, kind, spaced in checks:
        check_one_secret(setting, path, what, kind, spaced)


@secret_boundary()
def check_one_secret(setting: str, path: Path, what: str, kind: str, spaced: bool = False) -> None:
    """One secret file, read with the reader the real call uses; a refusal is a ValueError naming the SETTING only."""
    try:
        read_secret_line(path, what, kind, spaced=spaced)
    except (FileRefused, OSError):
        raise ValueError(
            f"{setting}: the secret file cannot be used (missing, empty, not one line of plain text)"
        ) from None


def load_env(path: Path) -> dict[str, str]:
    """NAME=VALUE lines; blank lines and # comments skipped; one pair of quotes around a value is dropped. A name must
    be upper-case letters, digits and underscore only: a lower-case `desk_qualifier` is refused here, so it can never
    slip past the forced values (the child process may see a case-insensitive environment)."""
    out: dict[str, str] = {}
    # the settings file is named on purpose and kept outside the repository (docs/real-services.md): resolved and
    # looked up in the listings from the top of the file system, not confined to a folder (tools/pathconfine.py); the
    # paths it names (book, run folder, keys) are used as written
    config = confine_anywhere(path, what="--config")
    try:
        text = read_regular_text(config)  # a pipe or a device is refused at once, never waited for
    except FileRefused:  # not UTF-8 or over 1 MiB; a byte value and its place in the file are never named
        raise ValueError("the config file is not UTF-8 text (or is over 1 MiB): save it as plain UTF-8 text") from None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip(" \t")
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        if not sep or not CONFIG_NAME.fullmatch(name.strip(" \t")):
            raise ValueError(f"config line {n} is not NAME=VALUE with an upper-case name")  # the line, never its text
        value = value.strip(" \t")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":  # noqa: PLR2004
            value = value[1:-1]
        out[name.strip(" \t")] = value
    return out


def make_plan(tag: str, persons: int) -> dict[str, list[dict[str, Any]]]:
    """The made-up traffic, in two phases (the crash comes between them). Every item is a request the desk gets over
    HTTP: {request_id, door, kind, envelope}. Emails end in EMAIL_DOMAIN (example.com) and are never mailed."""

    def item(door: str, ref: str, email: str, name: str, kind: str, phone: str) -> dict[str, Any]:
        payload = {"name": name, "email": email, "phone": phone, "message": "Demo message, made-up person."}
        return {
            "request_id": ref,
            "door": door,
            "kind": kind,
            "scenario": "real",
            "intended_ts": epoch_now(),
            "envelope": {"source": door, "source_ref": ref, "payload": payload},
        }

    def person(i: int, door: str, suffix: str = "", kind: str = "new") -> dict[str, Any]:
        return item(
            door,
            f"{tag}-p{i}{suffix}",
            f"{tag}-p{i}@{EMAIL_DOMAIN}",
            f"Demo Person{i}",
            kind,
            f"555 01{i:02d}",
        )

    doors = ("form", "webhook")
    half = persons // 2
    a = [person(i, doors[i % 2]) for i in range(1, half + 1)]
    b = [person(i, doors[i % 2]) for i in range(half + 1, persons + 1)]
    repeats_same = [person(i, doors[i % 2], kind="repeat_same_door") for i in (1, 2)]
    repeats_other = [person(i, doors[(i + 1) % 2], "", "repeat_other_door") for i in (3, 4)]
    twin = item(  # the same human with a second address: neither the CRM nor the desk can know it
        "form",
        f"{tag}-p{half}-twin",
        f"{tag}-p{half}.second@{EMAIL_DOMAIN}",
        f"Demo Person{half}",
        "same_person_other_email",
        f"555 01{half:02d}",
    )
    return {"before": a + repeats_same + repeats_other + [twin], "after": b, "replays": repeats_same + a[:2]}


TAG_HEX_CHARS = 6  # the run tag is "r" and this many hex characters: the same shape in the banner and in the run


def new_tag() -> str:
    """The tag that starts every made-up id and address of one run. Made once per run, before the Start? banner."""
    return "r" + uuid.uuid4().hex[:TAG_HEX_CHARS]


def longest_request_bytes(live: Any, plan: dict[str, list[dict[str, Any]]]) -> int:
    """The most bytes one model request of this run can have: the request body (`request_body`, the one builder the call
    itself uses) for the question (`question_text`, the one builder the call uses) of EVERY address in the plan
    (people, repeats and the twin), with a lead id of the real length. The banner counts this number, so it is never
    below what a call can reserve."""
    lead_id = LEAD_ID_PREFIX + "f" * LEAD_ID_HEX_CHARS  # a real one is the prefix and this many hex characters
    return max(
        len(request_body(live, question_text(lead_id, normalise_email(str(it["envelope"]["payload"]["email"])))))
        for items in plan.values()
        for it in items
    )


def send_item(url: str, it: dict[str, Any]) -> dict[str, Any]:
    """Send one planned item and return its log line. The drain check (invariant 7) measures from the LAST send, so
    intended_ts is stamped HERE, when the item is really (re)sent, never at plan creation (which would count the
    settle, crash and restart waits of earlier phases against the drain ceiling)."""
    return send_with_retries(url, {**it, "intended_ts": epoch_now()})


CHILD_ENV_KEEP = ("PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "HOME")
CHILD_ENV_PREFIXES = ("DESK_", "REAL_")


def child_environment(config_env: dict[str, str]) -> dict[str, str]:
    """The WHOLE environment of the desk child process: the DESK_* and REAL_* names from the CONFIG FILE only (a stale
    DESK_QUALIFIER or DESK_HUBSPOT_BASE_URL left in the parent shell is never seen), plus the few system variables a
    program needs to start (the shell's other variables, which may hold unrelated secrets, are not passed on). A name
    is matched only when it is plain ASCII: `upper()` turns the long s (U+017F) into S and the dotless i into I, so a
    variable with such a letter in its name would otherwise pass for a system one."""
    system = {k: v for k, v in os.environ.items() if k.isascii() and k.upper() in CHILD_ENV_KEEP}
    ours = {k: v for k, v in config_env.items() if CONFIG_NAME.fullmatch(k) and k.startswith(CHILD_ENV_PREFIXES)}
    return {**system, **ours}  # a name that is not upper-case is dropped (the forced values could be shadowed)


class Desk:
    """The desk as a child process (scripts/crash_desk.py, which can be stopped on purpose at a named moment). `env` is
    the finished child environment (from child_environment): nothing else is added except PYTHONPATH."""

    def __init__(self, env: dict[str, str], run_dir: Path, port: int, label: str, tag: str) -> None:
        self.env = {**env, "PYTHONPATH": os.pathsep.join([str(REPO / "src"), str(REPO)])}
        self.port, self.label = port, label
        # the files of this desk carry the run tag: a run folder used before holds files of another run (other tag), and
        # their counters must never be added to this run's (read_counter_files takes only the files of one tag)
        if not isinstance(tag, str) or not tag:  # required: an untagged file is one the reader never looks at
            raise ValueError("the run tag must be a non-empty text")
        self.log_path = run_dir / f"desk-{tag}-{label}.log"
        self.proc: subprocess.Popen[bytes] | None = None
        self.url = f"http://127.0.0.1:{port}"

    def start(self) -> None:
        env = {
            **self.env,
            "DESK_PORT": str(self.port),
            "DESK_HUBSPOT_STATS_FILE": str(self.log_path.with_suffix(".hubspot.json")),
            "DESK_SMTPP_STATS_FILE": str(self.log_path.with_suffix(".smtp.json")),
        }
        with open_output(self.log_path, "a+b") as log:  # a pipe or a device under that name is refused
            self.proc = subprocess.Popen(  # noqa: S603
                [sys.executable, str(REPO / "scripts" / "crash_desk.py")],
                cwd=REPO,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        end = time.monotonic() + DESK_START_SECONDS
        while time.monotonic() < end:
            if self.proc.poll() is not None:
                raise RuntimeError("the desk ended while starting (see its log in the run folder)")
            try:
                self.counts()
                return
            except OSError:
                time.sleep(0.3)
        raise RuntimeError("the desk did not answer in time")

    def counts(self) -> dict[str, Any]:
        with open_http(self.url + "/counts", 5) as r:
            try:
                data: dict[str, Any] = loads_bounded(read_reply(r))
            except ValueError:  # too big (ReplyTooBig) or not JSON: the callers already handle an OSError
                raise OSError("the desk's counts reply cannot be read") from None
        return data

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(10)

    def wait_exit(self, seconds: float) -> int | None:
        try:
            return self.proc.wait(seconds) if self.proc else None
        except subprocess.TimeoutExpired:
            return None


@dataclass(frozen=True)
class CounterRead:
    """What reading the counter files of one run gave: the summed numbers, how many files were found and how many of
    them could not be read (a half-written file, a folder or a file with a value that is not a whole number)."""

    totals: dict[str, int]
    files: int
    unreadable: int


def counter_is_known(read: CounterRead) -> bool:
    """True only if at least one counter file of the run exists, none was unreadable and the sum holds a number of
    created contacts. Anything else means the desk's own count is not known. (A desk stopped hard while a create was
    open does not make the count unknown: it is counted as an open create, see contacts_not_accounted_for.)"""
    return read.files > 0 and read.unreadable == 0 and "created" in read.totals


def read_counter_files(run_dir: Path, suffix: str, tag: str) -> dict[str, int]:
    """The summed numbers only (see read_counter_files_checked for the files found and the files that failed)."""
    return read_counter_files_checked(run_dir, suffix, tag).totals


def read_counter_files_checked(run_dir: Path, suffix: str, tag: str) -> CounterRead:
    """The sum of the counter files the desks of THIS run (run tag `tag`) wrote. A file of an older run in a shared run
    folder has another tag (or none) and is not read."""
    total: Counter[str] = Counter()
    if not tag:
        raise ValueError("the run tag must not be empty")
    files = unreadable = 0
    for p in sorted(run_dir.glob(f"desk-{tag}-*{suffix}")):
        files += 1
        try:
            total.update({k: int(v) for k, v in load_json_file(p).items()})
        except (OSError, ValueError, AttributeError, TypeError):
            unreadable += 1
    return CounterRead(dict(total), files, unreadable)


def drain(desk: Desk, seconds: float) -> dict[str, Any] | None:
    end = time.monotonic() + seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < end:
        try:
            last = desk.counts()
        except OSError:
            return None
        if last["open"] == 0 and last["pending_followups"] == 0 and last["sending_followups"] == 0:
            return last
        time.sleep(POLL_SECONDS)
    return None


def result_path(env: dict[str, str], run_dir: Path) -> Path:
    """The result file: REAL_RESULT_FILE when it is set and not blank, otherwise result.json next to the database."""
    named = env.get("REAL_RESULT_FILE", "")
    return Path(named) if named.strip() else run_dir / "result.json"


def check_result_file(env: dict[str, str], db: Path) -> None:
    """Refuse a bad REAL_RESULT_FILE BEFORE anything real runs (the file is written at the very end, so a bad path
    found then would lose the result of a long run). Raises ValueError with a fixed text that names the setting only.
    Looks only, makes nothing. Bad: a NUL character, the database file itself (the two settings swapped), a pipe, a
    device or a folder, and a file whose folder does not exist (only the run folder is made) or cannot be written."""
    named = env.get("REAL_RESULT_FILE", "")
    if not named.strip():
        return  # unset: result.json in the run folder, which the run makes
    if has_control_character(named):  # a NUL, a line break, an escape: a file named a<LF>b would be made
        raise ValueError("REAL_RESULT_FILE has a bad character in it")
    out = os.path.abspath(named)
    if out == os.path.abspath(db):
        raise ValueError("REAL_RESULT_FILE must not be the database file (DESK_DB_PATH): the two settings are swapped")
    try:
        if os.path.lexists(out) and not stat.S_ISREG(os.stat(out).st_mode):
            raise ValueError(
                "REAL_RESULT_FILE must name a regular file or a new file, not a pipe, a device or a folder"
            )
        folder = os.path.dirname(out)
        if folder != os.path.abspath(db.parent) and not (
            os.path.isdir(folder) and os.access(folder, os.W_OK | os.X_OK)
        ):
            raise ValueError("REAL_RESULT_FILE: its folder does not exist or cannot be written to")
    except (OSError, ValueError, TypeError) as e:
        if isinstance(e, ValueError) and str(e).startswith("REAL_RESULT_FILE"):
            raise
        raise ValueError("REAL_RESULT_FILE cannot be used as a result file") from None


def write_result(out: Path, payload: dict[str, Any]) -> bool:
    """Write the result file; True when it was written. When it cannot be (the disk filled, the folder went away), say
    so in one line and print the whole result on the screen, so a long run's result is never lost."""
    text = json.dumps(payload, indent=2, default=str)
    try:
        with open_output(out, "w", encoding="utf-8") as f:
            f.write(text)
    except (OSError, ValueError):
        print(
            "result file: it could NOT be written (REAL_RESULT_FILE: no write access, no space or a bad path); "
            "the result follows"
        )
        print(text)
        return False
    print(f"result file: {out}")
    return True


def folder_cannot_be_made(path: str | os.PathLike[str]) -> bool:
    """True when the folder of `path` surely cannot be made or written to: the path holds a control character (NUL, line
    break), or the nearest part that exists is not a folder this process may write to (for example a read-only
    mount). Looks only: it makes nothing. False means "no reason found", not a promise: the maker still has to handle
    its own failure."""
    try:
        if has_control_character(os.fspath(path)):  # NUL, line break: such a folder would be made
            return True
        here = Path(os.path.abspath(path)).parent
        while not os.path.lexists(here) and here.parent != here:
            here = here.parent
        return not (here.is_dir() and os.access(here, os.W_OK | os.X_OK))
    except (OSError, ValueError, TypeError):
        return True


def option_problem(a: argparse.Namespace) -> str | None:
    """The one refusal line for the first typed value that cannot be used, or None. Every text is fixed: it never holds
    what was typed. Runs before anything is started, read or asked."""
    if a.dry_port_base is not None:
        if not a.dry_fakes:
            return refusal("--dry-port-base", "only for the self-test (--dry-fakes)")
        last = PORT_MAX - (DRY_PORT_COUNT - 1)
        if not 1 <= a.dry_port_base <= last:
            return refusal(
                "--dry-port-base",
                f"must be between 1 and {last} (the self-test uses {DRY_PORT_COUNT} ports in a row from it)",
            )
    if a.dry_smtp_script is not None:
        if not a.dry_fakes:
            return refusal("--dry-smtp-script", "only for the self-test (--dry-fakes)")
        from demo_only.fake_smtp_tls import SCRIPTS

        if a.dry_smtp_script not in SCRIPTS:
            return refusal("--dry-smtp-script", "is not a known behaviour; use one of: " + ", ".join(SCRIPTS))
    return None


def main(argv: list[str] | None = None) -> int:
    ap = RefusingParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, help="the settings file (outside the repository)")
    ap.add_argument("--dry-fakes", action="store_true", help="self-test: run against local fake services, no real call")
    ap.add_argument("--live-model", action="store_true", help="also use the live model (its own dollar cap)")
    ap.add_argument("--cleanup", action="store_true", help="afterwards archive the HubSpot contacts this run made")
    ap.add_argument("--assume-yes", action="store_true", help="skip the y/N question; only together with --dry-fakes")
    ap.add_argument(
        "--dry-port-base", type=int, help="with --dry-fakes: fixed ports from this one (default: ephemeral)"
    )
    ap.add_argument(
        "--dry-smtp-script",
        default=None,
        help="with --dry-fakes: behaviour of the fake mail server (ok, final_452 ...)",
    )
    a = ap.parse_args(argv)
    with contextlib.ExitStack() as stack:
        return _run(a, stack)


def _run(a: argparse.Namespace, stack: contextlib.ExitStack) -> int:
    if (problem := option_problem(a)) is not None:
        print(problem)
        return EXIT_REFUSED
    if a.assume_yes and not a.dry_fakes:
        print("refused: --assume-yes is only for the self-test (--dry-fakes); a real run always asks")
        return EXIT_REFUSED
    env: dict[str, str] = {}
    live_cap: Decimal | None = None
    tag = new_tag()  # once: the banner counts the addresses of THIS tag, and the run sends them
    try:
        if a.dry_fakes:
            if a.config is not None:
                print("note: --config is ignored with --dry-fakes (the self-test uses its own local fakes)")
            script = "ok" if a.dry_smtp_script is None else a.dry_smtp_script
            fakes = DryFakes(Path(tempfile.mkdtemp(prefix="real-dry-")), a.dry_port_base, script)
            stack.callback(fakes.close)
            env = fakes.env
        elif a.config is None:
            print("refused: give --config PATH (see scripts/real-run.env.example) or --dry-fakes")
            return EXIT_REFUSED
        else:
            env = load_env(a.config)
        missing = [n for n in REQUIRED if not env.get(n, "").strip()]
        if missing:
            print("refused: the config lacks: " + ", ".join(missing))
            return EXIT_REFUSED
        persons = number("REAL_PERSONS", env, int, DEFAULT_PERSONS, high=REAL_PERSONS_MAX)
        if persons < MIN_PERSONS:
            print(f"refused: REAL_PERSONS must be at least {MIN_PERSONS}")
            return EXIT_REFUSED
        db = Path(env["DESK_DB_PATH"])
        if db.exists():  # an old book would hold old leads: the clean-up could not tell this run's contacts apart
            raise ValueError("DESK_DB_PATH names a file that already exists: give a new database file for each run")
        run_dir = db.parent
        if folder_cannot_be_made(db):  # a NUL character or a folder that cannot be written (a read-only mount)
            print("refused: DESK_DB_PATH: the run folder cannot be made here (a bad character or no write access)")
            return EXIT_REFUSED
        env = {**env, "DESK_ADAPTERS": "demo", "DESK_CRM": "hubspot", "DESK_OUTBOX": "smtp_provider"}
        env.setdefault("DESK_SEND_TIMEOUT_SECONDS", "8")
        env.setdefault("DESK_HUBSPOT_ALLOW_ANY_BASE_URL", "no")  # only the config file can switch the host check off
        env.setdefault("DESK_LIVE_ALLOW_ANY_BASE_URL", "no")  # the same for the live model's host check
        if not a.live_model:
            env["DESK_QUALIFIER"] = "recorded"  # a config line cannot turn the paid model on without the flag
        hs = HubspotSettings.from_env(env)
        pr = ProviderSettings.from_env(env)
        read_cap = number("REAL_HUBSPOT_READBACK_MAX_CALLS", env, int, 0, high=CAP_COUNT_MAX)
        if read_cap < MIN_READBACK_CALLS:  # inside the refusal block: nothing real has been called yet
            raise ValueError(f"REAL_HUBSPOT_READBACK_MAX_CALLS must be at least {MIN_READBACK_CALLS}")
        drain_seconds = positive_seconds("REAL_DRAIN_SECONDS", env, 150.0)
        mail_wait_seconds = positive_seconds("REAL_MAIL_WAIT_SECONDS", env, 90.0)
        settle_seconds = positive_seconds("REAL_MAIL_SETTLE_SECONDS", env, MAIL_POLL_SECONDS)
        check_result_file(env, db)  # before anything real runs: the file is written at the very end
        inboxes = imap_settings(env)
        bad_order = check_mailbox_order(env, inboxes)
        if bad_order:
            print("refused: " + bad_order)
            return EXIT_REFUSED
        check_secret_files(
            hs, pr, inboxes
        )  # before the question and before any connection: a bad secret is refused now
        live_worst = Decimal(0)
        if a.live_model:
            env["DESK_QUALIFIER"] = "live_claude"
            live = Config.from_env({**env, "DESK_PORT": "0"}).live
            if live is None:
                raise ValueError("the live model settings are missing")
            # the live key is read here too, with the same reader the live call uses: before the cost lines and before
            # the question, never after the desk has started and spend is reserved
            check_one_secret("DESK_LIVE_KEY_FILE", live.key_file, "key", "key")
            live_cap = live.cap_run_usd
            q_bytes = longest_request_bytes(live, make_plan(tag, persons))  # the plan the run sends, every address
            live_worst = worst_case_usd(live, q_bytes) * MODEL_CALLS_PER_LEAD * (persons + 3) * 2
        port = desk_port(env)
    except (ValueError, OSError, ArithmeticError) as e:
        # these messages name a setting, never its value (scrub is the backstop); any other error gets a fixed text.
        # The name of the Python class is never printed (`refused: PathRefused: ...` told a reader nothing useful).
        msg = scrub(str(e), env)[:200] if isinstance(e, ValueError) else ""
        print("refused: " + (msg or "the config or a setting cannot be used (see scripts/real-run.env.example)"))
        return EXIT_REFUSED

    desks = 2  # the crash starts a second desk process, each with its own caps
    print(f"people: {persons} + a twin (same person, second address); desk processes: {desks} (one crash)")
    by_desk = hs.max_calls * desks
    print(f"worst case HubSpot calls: {by_desk} by the desk + {read_cap} read-back = {by_desk + read_cap}")
    print("(each desk process counts its own cap in memory: a restarted process starts with a fresh cap)")
    print(f"worst case mails: {pr.max_sends * desks}, all to your own inboxes ({len(pr.recipients)} configured)")
    reads = IMAP_LOGINS_MAX + POLL_EXTRA_LOGINS
    print(
        f"worst case mailbox reading: {reads} logins x {len(inboxes)} mailboxes, each at most "
        f"{inboxes[0].total_seconds:.0f} s (the first read may be tried again with twice the time)"
    )
    child_env = child_environment(env)  # the very dict both desk processes get: the banner below reads it
    live_on = child_env.get("DESK_QUALIFIER") == "live_claude"
    print(
        f"worst case model cost: US${live_worst:.4f} (per-run cap US${live_cap})"
        if live_on
        else "model: the recorded replies (no live call)"
    )
    print(f"made-up people use addresses at {EMAIL_DOMAIN}; nobody outside your own inboxes receives anything")
    if not (a.assume_yes and a.dry_fakes):
        try:
            answer = input("Start? [y/N] ").strip().lower()
        except (EOFError, OSError):  # no terminal to answer on (a pipe, a scheduled job): never read as a yes
            print("stopped, nothing was called: there is no terminal to answer the question on")
            return EXIT_STOPPED
        if answer != "y":
            print("stopped, nothing was called")
            return EXIT_STOPPED

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError):  # the pre-question look is no promise (a disk can fill or turn read-only meanwhile)
        print("refused: DESK_DB_PATH: the run folder cannot be made (no write access or no space); nothing was started")
        return EXIT_REFUSED
    plan = make_plan(tag, persons)
    # a re-send of the same request over the same door is the same logged line, so count distinct lines
    everything = plan["before"] + plan["after"] + plan["replays"]
    intended = len({(it["door"], f"{it['request_id']}|{it['kind']}") for it in everything})
    flag = run_dir / "crash.flag"
    lines: dict[tuple[str, str], dict[str, Any]] = {}
    t_start = time.monotonic()  # a duration: monotonic, a clock step cannot change it

    def send_all(desk: Desk, items: list[dict[str, Any]]) -> None:
        for it in items:
            line = send_item(desk.url + "/leads", it)
            key = (line["door"], f"{line['request_id']}|{line['kind']}")
            old = lines.get(key)
            if old is not None and line["final_status"] not in (200, 201, 202):
                continue
            lines[key] = line

    d1 = Desk(child_env, run_dir, port, "1", tag)
    d2 = Desk({**child_env}, run_dir, port, "2", tag)
    sending_at_kill = 0
    crash_exit: int | None = None
    before_leads = 0
    try:
        d1.start()
        send_all(d1, plan["before"])
        settled = drain(d1, PRE_CRASH_DRAIN_SECONDS)  # the first batch settles, so only the second can be in flight
        before_leads = persons // 2 + 1 if settled else 0  # the first half of the people plus the twin
        write_regular_text(flag, CRASH_POINT)
        send_all(d1, plan["after"])
        crash_exit = d1.wait_exit(CRASH_WAIT_SECONDS)
        d1.stop()
        sending_at_kill = sending_rows(db)  # before the second desk's reaper turns them into `unknown`
        if flag.exists():
            flag.unlink()
        d2.start()
        lost = [
            it
            for it in plan["after"] + plan["before"]
            if lines.get((it["door"], f"{it['request_id']}|{it['kind']}"), {}).get("final_status")
            not in (200, 201, 202)
        ]
        send_all(d2, lost + plan["replays"])
        idle = drain(d2, drain_seconds)
        drained_at = epoch_now()
    except RuntimeError as e:
        print(f"the run could not finish: {e}")
        d1.stop()
        d2.stop()
        return EXIT_FAILED
    finally:
        d1.stop()
        d2.stop()

    try:
        book = read_book(db, anywhere=True)
    except InputError as e:
        print(f"cannot read the desk's book: {e}")
        return EXIT_FAILED
    lead_ids = set(book["leads"])
    reqs = list(lines.values())

    crm = HubspotCrm(replace(hs, max_calls=read_cap, stats_file=None))
    try:
        crm_pairs = [(lid, cid) for lid, cid in crm.rows_with_prefix("L") if lid in lead_ids]
    except CrmError as e:  # includes the read-back call cap: say what may be left, never end in a traceback
        return _readback_failed(a, run_dir, env, e, len(lead_ids), read_counter_files(run_dir, ".hubspot.json", tag))
    crm_rows = [{"lead_id": lid} for lid, _ in crm_pairs]

    sent_ids = {lid for lid, (s, _, _) in book["followups"].items() if s == "sent"}  # only these must show up
    poll_stats: dict[str, int] = {}
    per_inbox, logins, last_poll_failed = poll_mailboxes(
        inboxes,
        lead_ids,
        expected_keys_by_inbox(sent_ids, pr, inboxes),
        len(sent_ids),
        mail_wait_seconds,
        settle_seconds,
        sent_ids=sent_ids,
        stats=poll_stats,
    )
    unchecked = folders_not_found(per_inbox, inboxes)
    if unchecked:
        print(f"could not check: {len(unchecked)} configured mailbox folder(s) do not exist on the server")
    mail_per_lead: Counter[str] = Counter()  # the sum over all mailboxes: check 3 allows one message per key in total
    mails_by_inbox: list[int] = []
    spam = 0
    for box in per_inbox:
        mails_by_inbox.append(sum(n for f in box.values() for k, n in f.items() if k in lead_ids))
        for name, f in box.items():
            for k, n in f.items():
                if k in lead_ids:
                    mail_per_lead[k] += n
                    spam += n if "spam" in name.lower() else 0
    mail_rows = [{"send_key": k} for k, n in mail_per_lead.items() for _ in range(n)]

    result = run_checks(
        reqs,
        book,
        mail_rows,
        crm_rows,
        [],
        drained_ts=drained_at if idle else None,
        max_drain_seconds=drain_seconds,
        max_failed=0,
        max_unknown=unknown_allowance(sending_at_kill),  # only follow-ups in flight at the kill may end unknown
        intended=intended,
    )
    hub_read = read_counter_files_checked(run_dir, ".hubspot.json", tag)
    hub_stats = hub_read.totals
    smtp_stats = read_counter_files(run_dir, ".smtp.json", tag)
    result["checks"] += floor_checks(
        book,
        persons + 1,
        before_leads,
        mail_per_lead,
        crm_pairs,
        smtp_stats,
        crash_exit,
        sending_at_kill,
        last_poll_failed,
        poll_stats.get("poll_repeats", 0),
    )  # +1: the twin is a lead
    result["ok"] = all(c["ok"] for c in result["checks"])
    result = mask_result(result)  # a failure table names no address
    print(render_table(result).replace("ALL 7 CHECKS HOLD", "ALL CHECKS HOLD"))
    states = Counter(s for s, _, _ in book["followups"].values())
    crm_per_lead = Counter(lid for lid, _ in crm_pairs)
    per_lead = [
        {
            "lead_id": lid,
            "state": book["followups"][lid][0],
            "crm_rows": crm_per_lead.get(lid, 0),
            "mails": mail_per_lead.get(lid, 0),
        }
        for lid in sorted(lead_ids)
    ]
    print("\nlead id          state    CRM rows  mails")
    for r in per_lead:
        print(f"{r['lead_id']:<16} {r['state']:<8} {r['crm_rows']:>8}  {r['mails']:>5}")
    summary = {
        "people_sent": persons,
        "requests_intended": intended,
        "leads_in_book": len(lead_ids),
        "followup_states": dict(states),
        "crm_contacts_with_our_ids": len(crm_pairs),
        "crm_contacts_per_lead_max": max(crm_per_lead.values(), default=0),
        "mails_in_mailbox": sum(mail_per_lead.values()),
        "mail_poll_repeats": poll_stats.get("poll_repeats", 0),  # polls repeated after a dropped connection
        "mails_per_mailbox_in_config_order": mails_by_inbox,
        "mails_in_spam_folder": spam,
        "mailbox_folders_could_not_check": len(unchecked),  # 0 = every configured folder was read
        "leads_with_more_than_one_mail": sum(1 for n in mail_per_lead.values() if n > 1),
        "hubspot_calls_by_the_desk": hub_stats,
        "smtp_by_the_desk": smtp_stats,
        "mails_sent_by_the_desk_total": smtp_stats.get("sent"),
        "mails_allowed_by_the_desk_max": len(lead_ids) + states["unknown"],
        "hubspot_calls_by_readback": crm.stats(),
        "imap_logins": logins,
        "mail_last_poll_failed": last_poll_failed,  # True: the counts are those of an earlier poll (check F6 fails)
        "desk_crash_exit_code": crash_exit,
        "desk_idle_at_end": bool(idle),
        "seconds_total": round(time.monotonic() - t_start, 1),
        "twin_expectation": "the twin (same person, other address) is a second lead and contact: a known blind spot",
    }
    print("\n" + json.dumps(summary, indent=2, sort_keys=True))
    print()
    written = write_result(result_path(env, run_dir), {"checks": result, "summary": summary, "per_lead": per_lead})
    left: list[str] = []
    accounted = len(crm_pairs)
    if a.cleanup:
        done, left = archive_all(crm, crm_pairs)
        accounted = done + len(left)
        print(f"clean-up: {done} contacts archived (only those carrying this run's lead ids)")
        if left:
            print(
                f"clean-up: {len(left)} contacts are LEFT (HubSpot contact numbers: {', '.join(left)}); archive by hand"
            )
    unseen = 0
    counter_known = counter_is_known(hub_read)
    if not counter_known:
        print(
            "the desk's HubSpot counter cannot be trusted (no file, an unreadable or half-written file, or no number "
            "of created contacts): how many contacts the desk created is unknown, so contacts may be left in HubSpot. "
            "Check HubSpot for contacts whose lead ids start with L and archive them by hand."
        )
    else:
        unseen = contacts_not_accounted_for(
            hub_stats.get("created"),
            accounted,
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    if (
        unseen
    ):  # the list did not show a contact the desk created (list lag): it was not archived and may still be there
        print(
            f"{unseen} contacts may be left in HubSpot: the desk created {hub_stats.get('created')} (and had "
            f"{hub_stats.get('create_open', 0) + hub_stats.get('create_unknown', 0)} create requests with no known "
            f"outcome), the list showed {accounted}. Their lead ids start with L and are in the desk's book; "
            "check HubSpot and archive by hand."
        )
    shutil.rmtree(run_dir / "__pycache__", ignore_errors=True)
    return exit_code_of(result["ok"], written, left, unseen, counter_known)


if __name__ == "__main__":
    sys.exit(main())
