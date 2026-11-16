"""Round 7P: the gaps the reviewer found in r7o (made-up data only, loopback only, no spend). Every row is a PIN: the
source was already right on r7o and the test kills the named mutant (planted on a copy of r7p; see R7P-RESULTS.md).

  m1   regfile.read_regular_text, iter_regular_lines: `from None` dropped. The not-UTF-8 refusal must hide the decode
       error (its text names a byte value and a place; its .object holds the whole file). The key reader is a sibling.
  m2   crm_hubspot: `or parts.password` dropped. A password without a user name in the base address is refused.
  d1   run_real_check: REAL_DRAIN_SECONDS / REAL_MAIL_WAIT_SECONDS upper bound x10. One day is accepted, 86400.5 not.
  d2   run_real_check: call-site default 150.0 -> 151.0. With the setting absent the call site asks for 150.0.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_real_check as rrc  # noqa: E402

from lead_desk.crm_hubspot import HubspotSettings, SettingRefused  # noqa: E402
from lead_desk.regfile import (  # noqa: E402
    FileRefused,
    iter_regular_lines,
    load_json_file,
    read_regular_text,
    read_secret_line,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_real_check_dry import _valid_config  # noqa: E402

# -- m1: the not-UTF-8 refusal hides the decode error ---------------------------------------------------------------


@pytest.mark.parametrize(
    "read",
    [
        read_regular_text,
        load_json_file,
        lambda p: list(iter_regular_lines(p, 100, 100)),  # sibling, same class
        lambda p: read_secret_line(p, "key", "key"),  # sibling, same class: the bytes may be a key
    ],
    ids=["text", "json", "lines", "secret"],
)
def test_the_not_utf_8_refusal_hides_the_decode_error_behind_it(tmp_path: Path, read: Callable[[Path], Any]) -> None:
    p = tmp_path / "f.bin"
    p.write_bytes(b"\xff")
    with pytest.raises(FileRefused) as caught:
        read(p)
    e = caught.value
    assert e.__suppress_context__ is True and e.__cause__ is None
    shown = "".join(traceback.format_exception(e))
    assert "codec" not in shown and "position" not in shown


# -- m2: a login part with a password and no user name -------------------------------------------------------------


@pytest.mark.parametrize(
    "base",
    [
        "https://" + ":" + "pw" + "@" + "api." + "hubapi" + ".com",
        "http://" + ":" + "pw" + "@127.0.0.1:9",
    ],
)
def test_a_password_without_a_user_name_in_the_hubspot_base_address_is_refused(base: str) -> None:
    with pytest.raises(SettingRefused, match="no query, fragment or login"):
        HubspotSettings(key_file=Path("k"), max_calls=5, base_url=base)


# -- d1, d2: REAL_DRAIN_SECONDS and REAL_MAIL_WAIT_SECONDS ---------------------------------------------------------


@pytest.mark.parametrize("name", ["REAL_DRAIN_SECONDS", "REAL_MAIL_WAIT_SECONDS"])
def test_a_time_setting_holds_one_day_at_most(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert rrc.REAL_SECONDS_MAX == 86_400.0
    cfg = _valid_config(tmp_path, **{name: "86400"})
    assert rrc.main(["--config", str(cfg)]) == rrc.EXIT_STOPPED  # the highest value reaches the question
    assert "refused" not in capsys.readouterr().out
    cfg = _valid_config(tmp_path, **{name: "86400.5"})
    assert rrc.main(["--config", str(cfg)]) == rrc.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "refused" in out and name in out and "Start?" not in out


def test_the_drain_time_the_main_function_asks_for_without_a_setting_is_150_seconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    asked: list[tuple[str, float]] = []
    real = rrc.positive_seconds

    def spy(name: str, env: dict[str, str], default: float) -> float:
        asked.append((name, default))
        return real(name, env, default)

    monkeypatch.setattr(rrc, "positive_seconds", spy)
    cfg = _valid_config(tmp_path)
    assert "REAL_DRAIN_SECONDS" not in cfg.read_text(encoding="utf-8")
    assert rrc.main(["--config", str(cfg)]) == rrc.EXIT_STOPPED
    assert ("REAL_DRAIN_SECONDS", 150.0) in asked
