"""Shared fixtures: every test works on a copy of the fixture config in tmp_path, never the repo."""

import os
import secrets
import shutil
from pathlib import Path

import pytest

from hadavin_sdk.models import GateRun

FIXTURES = Path(__file__).parent / "fixtures"

# Tests never reach a real AWS account: no profile, config or credential_process from the machine running
# them, only fake keys (moto and the in-process stubs answer every call). Set before any boto3 session exists.
# Nor to any other cloud or a redirected endpoint: endpoint overrides, container and web-identity credentials,
# and the Google and Azure credential variables of the machine running them.
_ISOLATED = (
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_SESSION_TOKEN",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
)
_ISOLATED_PREFIXES = (
    "AWS_ENDPOINT_URL",
    "AWS_CONTAINER_CREDENTIALS_",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "AZURE_",
)
for _name in [n for n in os.environ if n in _ISOLATED or n.startswith(_ISOLATED_PREFIXES)]:
    os.environ.pop(_name, None)
os.environ["AWS_CONFIG_FILE"] = os.devnull
os.environ["AWS_SHARED_CREDENTIALS_FILE"] = os.devnull
os.environ["AWS_ACCESS_KEY_ID"] = "AKIA" + "IOSFODNN7EXAMPLE"
os.environ["AWS_SECRET_ACCESS_KEY"] = "fake" + "-secret-key"
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"


def make_cfg(tmp_path: Path, port: int = 0) -> Path:
    for name in ("config", "recorded", "inputs", "golden"):
        shutil.copytree(FIXTURES / name, tmp_path / name, dirs_exist_ok=True)
    cfg = tmp_path / "config" / "config.yaml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("{port}", str(port)), encoding="utf-8")
    return tmp_path / "config"


def qualify(
    registry, agent_id: str = "test-agent", green: bool = True, k: int | None = None
) -> None:
    """Write a gate run for the agent's current model, prompt and config (tests before S8's evals gate).
    A tooled agent needs a k >= 3 record that passed pass^k (K3, B1), so it gets k = 3 by default."""
    agent = registry.agents[agent_id]
    k = k or (3 if agent.tools_allowed else 1)
    run = GateRun(
        agent_id=agent_id,
        model_id=registry.config.routes[agent.model_route].model_id,
        prompt_sha256=registry.prompt_sha256(agent_id),
        config_hash=registry.config_hash(agent_id),
        golden_sha256=registry.golden_sha256(agent_id),
        n=1,
        passed=1 if green else 0,
        pass_rate=1.0 if green else 0.0,
        threshold=1.0,
        green=green,
        k=k,
        pass_k=(1.0 if green else 0.0) if k > 1 else None,
    )
    (registry.config.root / "qualified.jsonl").write_text(
        run.model_dump_json() + "\n", encoding="utf-8"
    )


@pytest.fixture
def cfg_dir(tmp_path: Path) -> Path:
    return make_cfg(tmp_path)


@pytest.fixture
def fake_system():
    """fixture-records on a random port with a random token (shared with the fake secret provider)."""
    from tests.fixtures.fake_system import FakeSystem

    system = FakeSystem(token=secrets.token_hex(16)).start()
    yield system
    system.stop()


@pytest.fixture
def live_cfg_dir(tmp_path: Path, fake_system) -> Path:
    return make_cfg(tmp_path, port=fake_system.port)


@pytest.fixture(autouse=True)
def _pilot_builds_on_an_interpreter_with_other_unicode_data(request, monkeypatch):
    """Pilot and prod refuse to start on Unicode data other than the pin (``textnorm.require_pinned_unidata``). The oldest supported
    Python (3.12) carries older data, so a test of anything else that builds a pilot app would stop at that guard. Only the test
    files whose name says pilot or prod get the guard switched off here (every other test file, the textnorm ones included, runs with the
    real guard); the guard's own tests run on both interpreters."""
    import unicodedata

    from hadavin_sdk import defaults
    from hadavin_sdk.guard import textnorm

    if unicodedata.unidata_version != defaults.TEXTNORM_PINNED_UNIDATA and any(
        word in request.module.__name__.rsplit(".", 1)[-1] for word in ("pilot", "prod")
    ):
        monkeypatch.setattr(textnorm, "require_pinned_unidata", lambda *a, **k: None)
    yield
