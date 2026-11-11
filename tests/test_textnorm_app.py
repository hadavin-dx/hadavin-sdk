"""BN-12: ``app.build`` refuses to start in pilot and prod on another Unicode data version, and does not refuse elsewhere.

The interpreter's version is stubbed (``unicodedata.unidata_version``), so the test runs on every Python. The pilot case reaches the
refusal before anything is contacted; the non-live case is a full in-memory build, which must succeed with the stub in place.
"""

import unicodedata

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.textnorm import UnidataMismatch
from hadavin_sdk.stages import is_live
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, demo_cfg
from tests.test_k3_pilot_env import pilot_cfg

OTHER = "0.0.1"


def test_a_pilot_or_prod_build_refuses_on_another_unicode_version(tmp_path, monkeypatch):
    assert OTHER != defaults.TEXTNORM_PINNED_UNIDATA
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    cfg = pilot_cfg(tmp_path)
    raised = None
    try:
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS)
    except UnidataMismatch as exc:
        raised = exc
    assert isinstance(raised, UnidataMismatch), (
        f"the build did not refuse for the Unicode version: {raised!r}"
    )
    assert OTHER in str(raised)
    # prod takes the same branch: ``live`` is ``is_live(environment)`` (a prod config needs more settings than this test builds)
    assert is_live("pilot") and is_live("prod") and not is_live("demo")


def test_a_pilot_build_on_the_pinned_version_calls_the_guard_and_is_not_refused_by_it(
    tmp_path, monkeypatch
):
    """The guard really runs (a spy counts the call) and, on the pinned version, lets the build go on: whatever stops it later is not
    the Unicode guard. (Before this fix the test passed even if the guard was never called.)"""
    from hadavin_sdk.guard import textnorm

    monkeypatch.setattr(unicodedata, "unidata_version", defaults.TEXTNORM_PINNED_UNIDATA)
    real = textnorm.require_pinned_unidata
    calls = []

    def spy():
        calls.append(1)
        return real()

    monkeypatch.setattr(textnorm, "require_pinned_unidata", spy)
    cfg = pilot_cfg(tmp_path)
    try:
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS)
    except UnidataMismatch:  # pragma: no cover - the failure this test exists for
        pytest.fail("a build on the pinned Unicode version was refused for its Unicode version")
    except ConfigError:
        pass  # pilot needs a database secret this test does not provide; that stop is not what this test asks
    assert calls == [1], f"the guard was called {len(calls)} times, not once"


def test_the_unicode_guard_runs_before_the_registry_or_any_secret_store_is_touched(
    tmp_path, monkeypatch
):
    """``build`` checks the Unicode data first: with other data, nothing after the config is read and no secret store is made."""
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    touched = []

    def touch(*_a, **_k):
        touched.append(1)
        raise RuntimeError("touched")

    monkeypatch.setattr(app_mod, "load_registry", touch)
    monkeypatch.setattr(app_mod, "make", touch)
    with pytest.raises(UnidataMismatch):
        app_mod.build(
            pilot_cfg(tmp_path), ["ito-agent"]
        )  # no secrets argument: the secret store would be built
    assert touched == [], "the registry or a secret store was touched before the Unicode guard"


def test_the_conftest_switch_is_off_in_the_textnorm_tests():
    """``tests/conftest.py`` replaces the guard for the tests of other things on an interpreter with other Unicode data; here it must
    be the real function, or the two tests above would test nothing."""
    from hadavin_sdk.guard import textnorm

    assert textnorm.require_pinned_unidata.__module__ == textnorm.__name__
    assert textnorm.require_pinned_unidata.__name__ == "require_pinned_unidata"


def test_a_non_live_build_runs_on_another_unicode_version(tmp_path, monkeypatch):
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    cfg = demo_cfg(tmp_path, {"restart_service": "shadow"})
    qualify(app_mod.load_registry(app_mod.load_config(cfg)))
    built = app_mod.build(cfg, ["test-agent"], secrets=SECRETS)
    assert built.runtime is not None
