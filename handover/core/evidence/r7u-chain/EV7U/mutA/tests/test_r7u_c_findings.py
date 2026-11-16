"""Round 7U, builder C: the loopback rule in one light module (review m6), the two docstrings (n1, n2) and three tests
the r7t review named as missing (a settle that raises, two puts at the same time, a 201 without an id). Made-up data
only, loopback only; no sleep, no real kill, no spend.

Before/after on the r7t sources: see out/R7U-C/RESULTS-C.md. FAILS = fails on r7t. PIN = r7t was already right; the
test passes on both and says so.

  c1  the loopback rule lives in src/lead_desk/loopback.py (stdlib only); one object everywhere (m6): FAILS
  c2  a fresh interpreter with only that folder on the path imports it, it refuses, nothing heavy loads (m6): FAILS
  c3  the two raw-socket fakes import nothing heavy (m6): FAILS
  c4  the module text says this computer by design, no promise of a listener (m8, doc check): FAILS
  c5  a put whose settle raises leaves the create open, the safe side: PIN
  c6  two puts at the same time: create_open == 2 on disk before either request leaves: PIN
  c7  a 201 without an id is counted create_unknown: PIN
  n1  run_stats text says what t10 really checks (doc check): FAILS
  n2  crm_hubspot text names the create counters, the refusal and the settle rule (doc check): FAILS
"""

from __future__ import annotations

import ast
import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest
from support import REPO, run_python

LIGHT = REPO / "src" / "lead_desk" / "loopback.py"
HEAVY_PREFIXES = ("lead_desk", "scripts", "tools", "demo_only")


def _stats(path: Path) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))


ALL_INTERFACES = ".".join(["0"] * 4)


def _fresh(tmp_path: Path, code: str) -> Any:
    """A fresh interpreter in isolated mode (-I): no environment path, no current folder on the path. The text runs
    from a file in the test's own folder (the repository's helper refuses a `-c` text)."""
    script = tmp_path / "fresh.py"
    script.write_text(code, encoding="utf-8")
    return run_python(["-I", str(script)], env=dict(os.environ), timeout=60)


# -- c1: one light module, one source of truth ------------------------------------------------------------------------


def test_c1_the_light_module_imports_only_the_standard_library() -> None:
    tree = ast.parse(LIGHT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert names <= {"__future__", "ipaddress"}, names


def test_c1_there_is_one_rule_one_refusal_and_one_text() -> None:
    from demo_only import bad_request
    from lead_desk import config, loopback
    from tools import refusing_args

    assert config.is_loopback_host is loopback.is_loopback_host
    assert bad_request.require_loopback_host is loopback.require_loopback_host
    assert refusing_args.LOOPBACK_HOST_TEXT is loopback.LOOPBACK_HOST_TEXT
    assert loopback.require_loopback_host("localhost") == "localhost"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        5,
        b"127.0.0.1",
        "",
        " ",
        ALL_INTERFACES,
        "::",
        "[::]",
        "example." + "com",
        "[::",
        "::1%eth0",
        "[[::1]]",
        "[::1",
        "::1]",
    ],
)
def test_c1_the_light_refusal_refuses_what_is_not_this_computer(bad: Any) -> None:
    from lead_desk import loopback

    with pytest.raises(ValueError, match=loopback.LOOPBACK_HOST_TEXT):
        loopback.require_loopback_host(bad)


@pytest.mark.parametrize("host", ["LOCALHOST", "localhost", "127.0.0.1", "[::1]", "::1", "::ffff:127.0.0.1"])
def test_c1_the_light_refusal_accepts_each_loopback_spelling(host: str) -> None:
    from lead_desk import loopback

    assert loopback.require_loopback_host(host) == host
    assert loopback.is_loopback_host(host) is True


def test_c1_pin_the_refusal_text_is_the_fixed_line_the_scripts_show() -> None:
    """PIN of a literal: every other test reads the text from the constant, so a changed wording would pass them."""
    from lead_desk import loopback

    assert loopback.LOOPBACK_HOST_TEXT == "must be this computer: localhost or 127.0.0.1"


# -- c2: the module alone, in a fresh interpreter ---------------------------------------------------------------------


def test_c2_the_module_alone_on_the_path_imports_and_refuses_and_loads_nothing_heavy(tmp_path: Path) -> None:
    """`-I` drops the environment path and the current folder; only the folder of the module is put on the path."""
    code = (
        "import sys\n"
        f"sys.path[:0] = [{str(LIGHT.parent)!r}]\n"
        "import loopback\n"
        "assert loopback.require_loopback_host('127.0.0.1') == '127.0.0.1'\n"
        f"for bad in ({ALL_INTERFACES!r}, '', None, 7):\n"
        "    try:\n"
        "        loopback.require_loopback_host(bad)\n"
        "    except ValueError:\n"
        "        continue\n"
        "    raise SystemExit('accepted ' + repr(bad))\n"
        f"heavy = sorted(m for m in sys.modules if m.split('.')[0] in {HEAVY_PREFIXES!r})\n"
        "print('HEAVY=' + ','.join(heavy))\n"
        "print('OK')\n"
    )
    done = _fresh(tmp_path, code)
    assert done.returncode == 0, done.stderr[-1500:] + done.stdout[-500:]
    assert "HEAVY=\n" in done.stdout and "OK" in done.stdout, done.stdout


def test_c3_the_two_raw_socket_fakes_import_no_heavy_module(tmp_path: Path) -> None:
    heavy = ("lead_desk.config", "scripts.http_guard", "tools.refusing_args", "lead_desk.constants", "lead_desk.envnum")
    code = (
        "import sys\n"
        f"sys.path[:0] = [{str(REPO / 'src')!r}, {str(REPO)!r}]\n"
        "import demo_only.fake_imap, demo_only.fake_smtp_tls\n"
        f"print('HEAVY=' + ','.join(m for m in {list(heavy)!r} if m in sys.modules))\n"
        "print('LIGHT=' + str('lead_desk.loopback' in sys.modules))\n"
    )
    done = _fresh(tmp_path, code)
    assert done.returncode == 0, done.stderr[-1500:]
    assert "HEAVY=\n" in done.stdout and "LIGHT=True" in done.stdout, done.stdout


def test_c3_the_fakes_still_refuse_a_host_that_is_not_this_computer(tmp_path: Path) -> None:
    from demo_only.fake_imap import FakeImap
    from demo_only.fake_smtp_tls import FakeSmtp
    from lead_desk.loopback import LOOPBACK_HOST_TEXT

    for make in (
        lambda h: FakeImap(tmp_path / "c", tmp_path / "k", h, {}),
        lambda h: FakeSmtp(tmp_path / "c", tmp_path / "k", h),
    ):
        with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
            make(ALL_INTERFACES)


# -- c4: the text says what the rule is (a doc check; it fails on r7t because the module does not exist) ------------


def test_c4_the_module_text_says_this_computer_by_design_and_promises_no_listener() -> None:
    text = LIGHT.read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(text)) or ""
    assert "by design" in doc and "LOCALHOST" in doc and "does not" in doc and "listen" in doc, doc


# -- c5-c7: gaps the review named in the r7t tests --------------------------------------------------------------------


def _rig(tmp_path: Path) -> Any:
    from test_crm_hubspot import Rig

    return Rig(tmp_path)


def test_c5_pin_a_put_whose_settle_raises_leaves_the_create_open_which_is_the_safe_side(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC

    from lead_desk.crm_hubspot import HubspotCrm

    rig = _rig(tmp_path)
    try:
        stats = tmp_path / "desk-rabcdef-1.hubspot.json"
        crm = rig.crm(stats_file=stats)

        def boom(self: Any, outcome: str | None) -> None:
            raise RuntimeError("settle failed")

        monkeypatch.setattr(HubspotCrm, "_settle_create", boom)
        with pytest.raises(RuntimeError, match="settle failed"):
            crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["created"], written["create_open"]) == (0, 1), written  # reported as possible, not hidden
        assert len(rig.state.contacts) == 1  # and the contact is really there: the open create is not an over-count
    finally:
        rig.stop()


def test_c6_pin_two_puts_at_the_same_time_are_two_open_creates_before_either_request_leaves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC

    from lead_desk.crm_hubspot import HubspotCrm

    rig = _rig(tmp_path)
    try:
        stats = tmp_path / "desk-rabcdef-2.hubspot.json"
        crm = rig.crm(stats_file=stats)
        entered = threading.Barrier(3, timeout=20)  # the two requests and this test
        go = threading.Event()
        real = HubspotCrm._once

        def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
            entered.wait()  # both creates were written as open before either request leaves
            assert go.wait(20)
            return real(self, method, path, obj, deadline, key)

        monkeypatch.setattr(HubspotCrm, "_once", once)
        errors: list[BaseException] = []

        def put(n: int) -> None:
            try:
                crm.put(f"L-{n}", {**REC, "email": f"p{n}@example.test"})
            except Exception as e:  # handed to the test thread
                errors.append(e)

        threads = [threading.Thread(target=put, args=(n,)) for n in (1, 2)]
        for t in threads:
            t.start()
        try:
            entered.wait()
            assert _stats(stats)["create_open"] == 2, _stats(stats)
        finally:
            go.set()
            for t in threads:
                t.join(20)
        assert not errors, errors
        done = _stats(stats)
        assert (done["created"], done["create_open"]) == (2, 0), done
    finally:
        rig.stop()


def test_c7_pin_a_201_without_an_id_is_an_unknown_create(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_crm_hubspot import REC

    from lead_desk.crm_hubspot import CrmError, HubspotCrm, _Reply

    rig = _rig(tmp_path)
    try:
        stats = tmp_path / "desk-rabcdef-3.hubspot.json"
        crm = rig.crm(stats_file=stats)
        real = HubspotCrm._once

        def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
            real(self, method, path, obj, deadline, key)  # the stand-in made the contact
            return _Reply(201, {}, None)  # and answered 201 with no id

        monkeypatch.setattr(HubspotCrm, "_once", once)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["created"], written["create_open"], written["create_unknown"]) == (0, 0, 1), written
        assert len(rig.state.contacts) == 1
    finally:
        rig.stop()


# -- n1, n2: the two texts (doc checks) -------------------------------------------------------------------------------


def test_n1_the_counters_file_text_does_not_say_no_test_checks_atomicity() -> None:
    from lead_desk import run_stats

    doc = " ".join((run_stats.__doc__ or "").split())
    assert "no test checks atomicity" not in doc, doc
    for word in ("write_stats_strict", "create_open", "t10", "What no test does"):
        assert word in doc, word


def test_n2_the_hubspot_text_names_the_create_counters_the_refusal_and_the_settle_rule() -> None:
    from lead_desk import crm_hubspot

    doc = " ".join((crm_hubspot.__doc__ or "").split())
    for word in ("create_open", "create_unknown", "CrmCounterUnwritable", "settle"):
        assert word in doc, word
