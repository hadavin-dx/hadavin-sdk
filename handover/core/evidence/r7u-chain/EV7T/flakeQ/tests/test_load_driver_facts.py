"""Class: a machine fact that could not be read must say so, never be a silent null. The load driver reads its facts
from /proc and /sys through the one file reader (lead_desk.regfile). On Linux those files report themselves as regular
files, so the reader works on them (pinned here against a real machine); where a file is missing or cannot be read
(Windows, a locked-down container, a file over the cap) the fact holds the word `unreadable`. Made-up data only."""

from __future__ import annotations

import sys

import pytest

from lead_desk.regfile import FileRefused
from load_tools import load_driver

LINUX = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="the /proc and /sys files are a Linux thing")


@LINUX
def test_on_linux_the_proc_files_are_read_through_the_regular_file_reader() -> None:
    facts = load_driver.machine_facts()
    assert isinstance(facts["memory"]["MemTotal_kb"], int) and facts["memory"]["MemTotal_kb"] > 0, facts["memory"]
    assert isinstance(facts["memory"]["MemAvailable_kb"], int), facts["memory"]
    assert isinstance(facts["somaxconn"], int) and facts["somaxconn"] > 0, facts["somaxconn"]
    assert isinstance(facts["time_wait_count"], int) and facts["time_wait_count"] >= 0, facts["time_wait_count"]


@pytest.mark.parametrize(
    "error", [FileNotFoundError("gone"), PermissionError("no"), FileRefused("the file is too big")]
)
def test_a_fact_that_cannot_be_read_says_unreadable_and_is_never_null(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def refuse(*_a: object, **_k: object) -> str:
        raise error

    monkeypatch.setattr(load_driver, "read_regular_text", refuse)
    monkeypatch.setattr(load_driver, "iter_regular_lines", refuse)  # R7: the connection table is streamed now
    facts = load_driver.machine_facts()
    assert facts["somaxconn"] == "unreadable"
    assert facts["time_wait_count"] == "unreadable"
    assert facts["memory"] == {"MemTotal_kb": "unreadable", "MemAvailable_kb": "unreadable"}
    assert None not in (facts["somaxconn"], facts["time_wait_count"], *facts["memory"].values())


def test_a_kernel_file_with_rubbish_in_it_is_unreadable_not_a_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(load_driver, "read_regular_text", lambda *_a, **_k: "MemTotal: lots kB\n")
    facts = load_driver.machine_facts()
    assert facts["somaxconn"] == "unreadable" and facts["memory"]["MemTotal_kb"] == "unreadable"
