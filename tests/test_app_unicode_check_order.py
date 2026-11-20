"""The Unicode start-up check runs before any backend is built (G1 fix round 1, finding M8).

`build` promises that a refusal comes "before any backend is built": reads no secret, opens no connection. The pinned-Unicode check
used to run after `make("secrets", ...)` and `load_registry`."""

import unicodedata

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.textnorm import UnidataMismatch
from hadavin_sdk.guard.textnorm import require_pinned_unidata as _REAL_CHECK
from tests.test_k3_pilot_env import pilot_cfg


def test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made(
    tmp_path, monkeypatch
):
    # the suite's fixture may have switched the check off (an interpreter with other Unicode data): put the real one back
    monkeypatch.setattr(textnorm, "require_pinned_unidata", _REAL_CHECK)
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "15.1.0")
    monkeypatch.setattr(unicodedata, "unidata_version", "9.9.9")
    made: list[object] = []

    def recording_make(*args, **kwargs):
        made.append(args)
        raise AssertionError("a backend was built before the Unicode check")

    monkeypatch.setattr(app_mod, "make", recording_make)
    with pytest.raises(UnidataMismatch):
        app_mod.build(pilot_cfg(tmp_path), ["ito-agent"])
    assert made == []
