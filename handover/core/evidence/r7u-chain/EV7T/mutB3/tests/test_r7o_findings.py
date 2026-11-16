"""Round 7O: tests for the mutants of mail-path pass 12 (on r7m) that survived the big set, plus the reviewer rows.
Made-up data only, loopback only; keys are built from parts; no real model, no real mail, no spend.
Header table: finding, mutant, what the test pins, why it matters, result on a copy of r7n (FAILS = new behaviour,
fails before the fix; PIN = pure pin of code that was already right, passes by design; a mutant planted on r7o is
killed by it, see R7O-RESULTS.md).

  finding | mutant  | what is pinned                                                       | on r7n
  ------- | ------- | -------------------------------------------------------------------- | ------
  o1      | M9-79   | the live "worst case model cost" of the Start? banner is the cost    | PIN
          | O01-O03 | of one call x calls per lead x (people + 3) x 2 desk processes (the  |
          |         | crash restart); exactly twice the one-process figure                 |
          |         | why: money, the owner decides from this number                       |
  o2      | M9-74   | clean-up that leaves a contact behind says LEFT and ends with        | PIN
          | O04     | EXIT_FAILED; a clean-up that leaves none ends with 0                 |
  o3      | M10-J13 | bytes that are not UTF-8 are refused by read_regular_text and        | PIN
          | O05     | load_json_file, never decoded with a replacement character           |
  o4      | M10-J09 | a leading byte-order mark is accepted ON PURPOSE and dropped by the  | FAILS
          | O06,O07 | text reader, the JSON loader, the two crash-flag readers and the     | (U+FEFF kept,
          |         | config reader; a second mark or one in the middle is kept            | BOM+JSON refused)
  o5      | M9-56   | a login part (user@) in the HubSpot base address is refused, the     | PIN
          | O08     | plain loopback form and the https vendor form                        |
  o6      | M10-J02 | JsonTooDeep hides the RecursionError (from None)                     | PIN
          | O09     |                                                                      |
  o7      | M9-82   | REAL_HUBSPOT_READBACK_MAX_CALLS: the minimum is accepted, one below  | PIN
          | O10     | is refused (the pass-12 text said REAL_DRAIN_SECONDS: that setting   |
          |         | has no minimum above 0; the minimum 5 belongs to the read-back cap)  |
"""

from __future__ import annotations

import os
import re
import sys
import traceback
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_real_check as rrc  # noqa: E402

from lead_desk.adapters import CrmError  # noqa: E402
from lead_desk.crm_hubspot import HubspotSettings, SettingRefused  # noqa: E402
from lead_desk.hooks import ALL_HOOK_POINTS, FlagFileHooks  # noqa: E402
from lead_desk.jsonread import JsonTooDeep, loads_bounded  # noqa: E402
from lead_desk.regfile import FileRefused, load_json_file, read_regular_text  # noqa: E402
from lead_desk.trace import WINDOWS, CrashWindows  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_real_check_dry import _valid_config  # noqa: E402

BOM = b"\xef\xbb\xbf"


# -- o1: the live cost line of the banner -------------------------------------------------------------------------


def _live_settings(tmp_path: Path) -> dict[str, str]:
    (tmp_path / "k").write_text("made-up-key-for-tests-only\n", encoding="utf-8")
    return {
        "DESK_LIVE_MODEL": "model-x",
        "DESK_LIVE_KEY_FILE": str(tmp_path / "k"),
        "DESK_LIVE_PRICE_IN_PER_MTOK": "1",
        "DESK_LIVE_PRICE_OUT_PER_MTOK": "5",
        "DESK_LIVE_PRICE_DATE": "2026-01-01",
        "DESK_LIVE_CAP_RUN_USD": "1.25",
        "DESK_LIVE_CAP_TOTAL_USD": "3",
        "DESK_LIVE_LEDGER_PATH": str(tmp_path / "ledger"),
        "DESK_LIVE_RUN_ID": "r1",
    }


@pytest.mark.parametrize("persons", [8, 9, 15])
def test_the_live_cost_line_counts_every_call_of_every_person_and_both_desk_processes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, persons: int
) -> None:
    one_call = Decimal("0.01")  # a known cost of one call: the banner arithmetic is what is pinned here
    monkeypatch.setattr(rrc, "worst_case_usd", lambda _live, _bytes: one_call)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    cfg = _valid_config(tmp_path, REAL_PERSONS=str(persons), **_live_settings(tmp_path))
    assert rrc.main(["--config", str(cfg), "--live-model"]) == rrc.EXIT_STOPPED
    out = capsys.readouterr().out
    shown = re.search(r"worst case model cost: US\$([0-9.]+) ", out)
    assert shown, out
    one_process = one_call * rrc.MODEL_CALLS_PER_LEAD * (persons + 3)  # people + twin + two spare calls per process
    assert Decimal(shown.group(1)) == (one_process * 2).quantize(Decimal("0.0001"))  # the crash restarts the desk
    assert Decimal(shown.group(1)) == Decimal(f"{one_process * 2:.4f}") != Decimal(f"{one_process:.4f}")
    assert "desk processes: 2" in out  # the factor 2 on the line above is the one this line prints


# -- o2: a contact left behind after the clean-up ------------------------------------------------------------------


def _flaky_crm(fail_first: bool) -> type:
    class Flaky(rrc.HubspotCrm):
        tried = 0

        def archive(self, cid: str) -> None:
            type(self).tried += 1
            if fail_first and type(self).tried == 1:
                raise CrmError("made-up refusal")
            super().archive(cid)

    return Flaky


def test_a_contact_left_after_the_clean_up_is_said_and_ends_with_the_failed_exit_code(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _flaky_crm(True))
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "contacts are LEFT" in out and "archive by hand" in out
    assert "result file: " in out  # every check held and the result was written: only the left contact fails the run
    assert code == rrc.EXIT_FAILED, out[-1500:]


def test_a_clean_up_that_leaves_nothing_ends_with_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _flaky_crm(False))
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "LEFT" not in out and "contacts archived" in out
    assert code == 0, out[-1500:]


# -- o3, o4: the text readers --------------------------------------------------------------------------------------


@pytest.mark.parametrize("raw", [b'{"a":"x\xffy"}', b"\xff", b'{"a":"\xc3"}', b"\xed\xa0\x80"])
def test_bytes_that_are_not_utf_8_are_refused_never_decoded_with_a_replacement(tmp_path: Path, raw: bytes) -> None:
    p = tmp_path / "f.json"
    p.write_bytes(raw)
    with pytest.raises(FileRefused, match="the file is not UTF-8 text"):
        read_regular_text(p)
    with pytest.raises(FileRefused, match="the file is not UTF-8 text"):
        load_json_file(p)


def test_a_leading_byte_order_mark_is_dropped_by_the_text_reader_and_the_json_loader(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    p.write_bytes(BOM + b'{"a": 1}')
    assert load_json_file(p) == {"a": 1}
    assert read_regular_text(p) == '{"a": 1}'
    assert not read_regular_text(p).startswith("\ufeff")


def test_only_one_leading_mark_is_dropped_a_second_or_a_middle_one_is_kept_and_is_not_json(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    p.write_bytes(BOM + BOM + b"{}")
    assert read_regular_text(p) == "\ufeff{}"
    with pytest.raises(FileRefused, match="not JSON"):
        load_json_file(p)
    p.write_bytes(b'{"a":' + BOM + b"1}")
    with pytest.raises(FileRefused, match="not JSON"):
        load_json_file(p)
    p.write_bytes(b'["' + BOM + b'"]')  # a mark inside a string is data, not a mark in front of the text
    assert load_json_file(p) == ["\ufeff"]


class _Crashed(BaseException):
    """Stands for os._exit in the flag readers."""


def _record_exit(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    seen: list[int] = []

    def fake_exit(code: int) -> None:
        seen.append(code)
        raise _Crashed

    monkeypatch.setattr(os, "_exit", fake_exit)
    return seen


def test_a_flag_file_saved_with_a_byte_order_mark_is_read_as_the_point_name_by_both_flag_readers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    point, window = sorted(ALL_HOOK_POINTS)[0], sorted(WINDOWS)[0]
    seen = _record_exit(monkeypatch)
    flag = tmp_path / "flag"
    flag.write_bytes(BOM + point.encode() + b"\r\n")
    with pytest.raises(_Crashed):
        FlagFileHooks(flag).crash_point(point, None)
    assert len(seen) == 1 and not flag.exists()  # one-shot: the flag is taken
    flag.write_bytes(BOM + window.encode() + b"\n")
    with pytest.raises(_Crashed):
        CrashWindows(flag).hit(window)
    assert len(seen) == 2 and not flag.exists()
    flag.write_bytes(BOM + BOM + point.encode())  # a second mark makes it another name: no crash, flag kept
    FlagFileHooks(flag).crash_point(point, None)
    CrashWindows(flag).hit(window)
    assert len(seen) == 2 and flag.exists()
    capsys.readouterr()


def test_a_config_file_saved_with_a_byte_order_mark_reads_like_one_without(tmp_path: Path) -> None:
    plain = tmp_path / "plain.env"
    marked = tmp_path / "marked.env"
    plain.write_bytes(b"DESK_DB_PATH=x\nREAL_PERSONS=9\n")
    marked.write_bytes(BOM + b"DESK_DB_PATH=x\nREAL_PERSONS=9\n")
    assert rrc.load_env(marked) == rrc.load_env(plain) == {"DESK_DB_PATH": "x", "REAL_PERSONS": "9"}


# -- o5: a login part in the HubSpot address -----------------------------------------------------------------------


def _hub(base: str) -> HubspotSettings:
    return HubspotSettings(key_file=Path("k"), max_calls=5, base_url=base)


@pytest.mark.parametrize(
    "base",
    [
        "http://" + "someuser" + "@127.0.0.1:9",
        "https://" + "someuser" + "@" + "api." + "hubapi" + ".com",
        "https://" + "someuser" + ":" + "pw" + "@" + "api." + "hubapi" + ".com",
    ],
)
def test_a_login_part_in_the_hubspot_base_address_is_refused(base: str) -> None:
    with pytest.raises(SettingRefused, match="no query, fragment or login"):
        _hub(base)


# -- o6: the deep-nesting error hides its cause --------------------------------------------------------------------


def test_too_deep_json_raises_one_fixed_error_without_the_recursion_error_behind_it() -> None:
    with pytest.raises(JsonTooDeep) as caught:
        loads_bounded("[" * 30000)
    e = caught.value
    assert e.__suppress_context__ is True and e.__cause__ is None
    assert "RecursionError" not in "".join(traceback.format_exception(e))
    assert str(e) == "nested too deeply"


# -- o7: the minimum of the read-back cap --------------------------------------------------------------------------


def test_the_minimum_readback_cap_is_accepted_and_one_below_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    minimum = rrc.MIN_READBACK_CALLS
    assert minimum == 5
    cfg = _valid_config(tmp_path, REAL_HUBSPOT_READBACK_MAX_CALLS=str(minimum))
    assert rrc.main(["--config", str(cfg)]) == rrc.EXIT_STOPPED  # got as far as the question
    assert "refused" not in capsys.readouterr().out
    cfg = _valid_config(tmp_path, REAL_HUBSPOT_READBACK_MAX_CALLS=str(minimum - 1))
    assert rrc.main(["--config", str(cfg)]) == rrc.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "READBACK_MAX_CALLS must be at least 5" in out
