"""K5-core review round 9 (fresh review of head bdb1f6f). Each test names the finding it closes; most fail on that head."""

from __future__ import annotations

import sys
import time

import pytest

from hadavin_sdk.guard import runmap


def _redact_module():
    return sys.modules["hadavin_sdk.guard.redact"]


# --- B1: command-word documents are redacted in bounded time (the pattern sweep is in test_k5_perf.py) ----------------------------------------------------


@pytest.mark.parametrize(
    "word", ["curl", "mysql", "redis-cli", "sqlcmd", "ldapsearch", "htpasswd", "mongo"]
)
def test_a_document_of_repeated_command_words_is_redacted_in_bounded_time(word):
    from hadavin_sdk import defaults

    doc = (word + " ") * (defaults.MAX_DOCUMENT_BYTES // (len(word) + 1))
    t0 = time.process_time()
    runmap.redact_untrusted(doc, {})
    assert time.process_time() - t0 < 15  # the old command patterns took minutes here


# --- M1: a long local part is still masked ------------------------------------------------------------------------------------


@pytest.mark.parametrize("length", [65, 100, 254])
@pytest.mark.parametrize("at", ["@", "%40"])
def test_a_long_email_local_part_is_masked(length, at):
    local = "a1B2c3D4" * 40
    text = f"bounce to {local[:length]}{at}example.com now"
    out = runmap.redact_untrusted(text, {})
    assert local[:length] not in out and "example.com" not in out
