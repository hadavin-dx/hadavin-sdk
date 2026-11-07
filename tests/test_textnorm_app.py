"""BN-12: ``app.build`` refuses to start in pilot and prod on another Unicode data version, and does not refuse elsewhere.

The interpreter's version is stubbed (``unicodedata.unidata_version``), so the test runs on every Python. The pilot case reaches the
refusal before anything is contacted; the non-live case is a full in-memory build, which must succeed with the stub in place.
"""

import unicodedata

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import defaults
from hadavin_sdk.guard.textnorm import UnidataMismatch
from hadavin_sdk.stages import is_live
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, demo_cfg
from tests.test_k3_pilot_env import pilot_cfg

OTHER = "0.0.1"


def _prod_cfg(tmp_path):
    """A prod config that loads: prod wants its signer key from the secrets kind and an anchor with a retention the client agreed."""
    import yaml

    cfg = pilot_cfg(tmp_path, env="prod")
    path = cfg / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["signer"] = {"kind": "ed25519_local", "private_key_secret_name": "audit-key"}
    data["backends"]["anchor"] = {
        "kind": "gcs_retention_lock",
        "bucket": "contract-anchors",
        "mode": "GOVERNANCE",
        "retention_ack": True,
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return cfg


@pytest.mark.parametrize("environment", ["pilot", "prod"])
def test_the_pinned_unicode_guard_is_on_for_pilot_and_prod_configs(
    tmp_path, monkeypatch, environment
):
    """The guard is ON in ``app.build`` for both live environments: on other Unicode data the build stops with ``UnidataMismatch`` and a message in
    plain words that names the interpreter to use and why. (Fail-before: with the call removed from ``app.build`` the build goes on to other
    errors or succeeds, and this test fails by assertion.)"""
    assert OTHER != defaults.TEXTNORM_PINNED_UNIDATA
    monkeypatch.setattr(unicodedata, "unidata_version", OTHER)
    cfg = _prod_cfg(tmp_path) if environment == "prod" else pilot_cfg(tmp_path)
    assert app_mod.load_config(cfg).environment == environment
    raised = None
    try:
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS)
    except Exception as exc:  # noqa: BLE001 - the type is asserted below, so a build that stops for another reason fails by assertion
        raised = exc
    assert isinstance(raised, UnidataMismatch), (
        f"the {environment} build did not refuse for the Unicode version: {raised!r}"
    )
    message = str(raised)
    assert OTHER in message and defaults.TEXTNORM_PINNED_UNIDATA in message
    assert "Python 3.13" in message, "the message does not name the interpreter to use"
    assert "for pilot or prod" in message, (
        "the message does not say which stages need the pinned version"
    )
    assert is_live(environment)


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
    cfg = demo_cfg(tmp_path, {"restart_service": "shadow"})
    qualify(app_mod.load_registry(app_mod.load_config(cfg)))
    built = app_mod.build(cfg, ["test-agent"], secrets=SECRETS)
    assert built.runtime is not None
