"""BN-12: ``app.build`` refuses to start in pilot and prod on another Unicode data version, and does not refuse elsewhere.

The interpreter's version is stubbed (``unicodedata.unidata_version``), so the test runs on every Python. The pilot case reaches the
refusal before anything is contacted; the non-live case is a full in-memory build, which must succeed with the stub in place.
"""

import unicodedata

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import defaults
from hadavin_sdk.guard.textnorm import UnidataMismatch
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, dev_cfg
from tests.test_k3_pilot_env import pilot_cfg

OTHER = "0.0.1"


def test_a_pilot_or_prod_build_refuses_on_another_unicode_version(tmp_path, monkeypatch):
    assert OTHER != defaults.TEXTNORM_PINNED_UNIDATA
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    cfg = pilot_cfg(tmp_path)
    raised = None
    try:
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS)
    except Exception as exc:  # noqa: BLE001 - the type is asserted below, so a build that stops for another reason fails by assertion
        raised = exc
    assert isinstance(raised, UnidataMismatch), (
        f"the build did not refuse for the Unicode version: {raised!r}"
    )
    assert OTHER in str(raised)
    # prod takes the same branch: ``live`` is ``environment in deferred.LIVE`` (a prod config needs more settings than this test builds)
    assert set(app_mod.deferred.LIVE) == {"pilot", "prod"}


def test_a_pilot_build_on_the_pinned_version_does_not_refuse_for_the_unicode_version(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(unicodedata, "unidata_version", defaults.TEXTNORM_PINNED_UNIDATA)
    cfg = pilot_cfg(tmp_path)
    try:
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS)
    except UnidataMismatch:  # pragma: no cover - the failure this test exists for
        pytest.fail("a build on the pinned Unicode version was refused for its Unicode version")
    except Exception:  # noqa: BLE001, S110 - pilot needs a database and a channel: anything else is not what this test asks
        pass


def test_a_non_live_build_runs_on_another_unicode_version(tmp_path, monkeypatch):
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    cfg = dev_cfg(tmp_path, {"restart_service": "shadow"})
    qualify(app_mod.load_registry(app_mod.load_config(cfg)))
    built = app_mod.build(cfg, ["test-agent"], secrets=SECRETS)
    assert built.runtime is not None
