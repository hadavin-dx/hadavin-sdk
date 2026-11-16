"""demo_ctl register round 2 (result review m3): the temporary-folder allowance only in a temporary environment; --replace refuses while serve.lock is held.
Needs the demo-only folder (cut job skips this module)."""

from __future__ import annotations

import pytest

from conftest import MINI
from intake import lockfile, settings
from tools import demo_ctl


def mk(tmp_path):
    local = tmp_path / "local"
    (local / "intake").mkdir(parents=True, exist_ok=True)
    return settings.load({"HADAVIN_LOCAL": str(local), "INTAKE_MODEL_BACKEND": "fake"})


def test_a_temp_folder_is_not_registrable_when_the_environment_is_not_temporary(tmp_path, monkeypatch):
    s = mk(tmp_path)
    d = tmp_path / "attachments"  # where a mail program extracts attachments
    d.mkdir()
    (d / "real.txt").write_bytes(b"a real invoice\n")
    monkeypatch.setattr(settings, "under_temp_folder", lambda p: False)  # HADAVIN_LOCAL is the real folder
    with pytest.raises(demo_ctl.ConfigError):
        demo_ctl.register(s, d)
    assert demo_ctl.register(s, MINI) == (4, 4)  # the fixtures stay registrable


def test_replace_refuses_while_the_service_holds_its_lock(tmp_path):
    s = mk(tmp_path)
    demo_ctl.register(s, MINI)
    h = lockfile.acquire(s.intake_home / "serve.lock")
    try:
        with pytest.raises(demo_ctl.ConfigError) as e:
            demo_ctl.register(s, MINI, replace=True)
        assert "serve.lock" in e.value.text
        assert demo_ctl.register(s, MINI) == (0, 4)  # appending is allowed
    finally:
        lockfile.release(h)
    assert demo_ctl.register(s, MINI, replace=True) == (4, 4)
