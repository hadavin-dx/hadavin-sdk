"""Demo-data gate. The synthetic cases, generators and recorded replies live in the demo-data folder at the repo root; a client repository has that folder
deleted (the cut test). Test modules that need it are not collected when it is absent, and the run header says so; every other test still runs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_only"
NEEDS_DEMO_DATA = [
    "test_contract.py",
    "test_data.py",
    "test_demo_tools.py",
    "test_demo_tools_hardening.py",
    "test_demo_tools_round2.py",
    "test_faults.py",
    "test_inbound_isolation.py",
    "test_port_no_write.py",
    "test_review4.py",
    "test_review5.py",
    "test_demo_ctl.py",
    "test_scripts_text.py",
    "test_rules.py",
    "test_layouts.py",
    "test_eval_harness.py",
    "test_segregation_purpose.py",
]
collect_ignore = [] if DEMO.is_dir() else list(NEEDS_DEMO_DATA)


def pytest_report_header(config):
    if collect_ignore:
        return f"demo-data folder absent (cut test): {len(collect_ignore)} test modules that need demo data are NOT collected"
    return None


@pytest.fixture(autouse=True)
def _demo_data_env(monkeypatch):
    if DEMO.is_dir():
        monkeypatch.setenv("INTAKE_DEMO_DATA", str(DEMO))


# ---- helpers for the intake service tests -------------------------------------------------------------------------------------------------------
MINI = ROOT / "tests" / "fixtures" / "mini"
CAP_SENTENCE = "The most the whole demo project may spend is US$100."
CONSENT_SENTENCE = "YES: send made-up invoices to the Anthropic AI service."


def key_file(s):
    """The key file of a Settings object (a helper: Settings itself does not carry the path)."""
    from intake import secret_store

    return secret_store.secrets_path(s.local)


def fake_secret_values() -> dict[str, str]:
    """Fake values for the five secret names, built from parts (no literal key shape appears in a tracked file)."""
    return {
        "ANTHROPIC_API_KEY": "sk" + "-" + "test" + "A" * 30,
        "HADAVIN_WEBHOOK_SECRET": "hook" + "W" * 40,
        "HADAVIN_APPROVER_PASSPHRASE": "pass" + "P" * 30,
        "N8N_ENCRYPTION_KEY": "encr" + "E" * 40,
        "N8N_BASIC_AUTH_PASSWORD": "owner" + "O" * 30,
    }


def mini_hashes() -> list[str]:
    """sha256 of the normalised send_text of the four mini invoices (what the data gate lists)."""
    import hashlib

    from intake.reader import normalise_for_model

    return sorted(hashlib.sha256(normalise_for_model(p.read_bytes()).encode("utf-8")).hexdigest() for p in sorted(MINI.glob("*.txt")))


def settings_for_tests(tmp_path, backend: str = "fake", with_api_key: bool = True, with_ledger: bool = False):
    """Settings for a test: a TEMPORARY ``HADAVIN_LOCAL`` holding non-zero test prices, the owner's consent and cap sentence (US$100), the mini
    hashes on the made-up list and the five fake secrets. No committed file holds prices, so tests that need them use this helper."""
    import json
    from datetime import UTC, datetime
    from pathlib import Path

    from intake import settings

    local = Path(tmp_path) / "local"
    home = local / "intake"
    (home / "inbox").mkdir(parents=True, exist_ok=True)
    (home / "out").mkdir(exist_ok=True)
    prices = {
        "prices_micro_usd_per_million_tokens": {
            "read": {"in": 1_000_000, "out": 5_000_000},
            "fallback": {"in": 3_000_000, "out": 15_000_000},
        },
        "model_ids": {"read": "claude-haiku-5-5", "fallback": "claude-sonnet-5-5"},
        "prices_as_of": datetime.now(UTC).date().isoformat(),
        "anthropic_version": "test-version",
    }
    (home / "prices.json").write_text(json.dumps(prices), encoding="utf-8")
    (home / "owner_sentence.txt").write_text(CONSENT_SENTENCE + " " + CAP_SENTENCE + "\n", encoding="utf-8")
    (home / "synthetic_hashes.txt").write_text("\n".join(mini_hashes()) + "\n", encoding="utf-8")
    (home / "suppliers.csv").write_bytes((MINI / "suppliers.csv").read_bytes())
    key_dir = local / "secrets"
    key_dir.mkdir(parents=True, exist_ok=True)
    vals = fake_secret_values()
    if not with_api_key:
        vals.pop("ANTHROPIC_API_KEY")
    (key_dir / "secrets.env").write_text("".join(f"{k}={v}\n" for k, v in vals.items()), encoding="utf-8", newline="\n")
    if sys.platform != "win32":  # owner-only, as the real files are: `intake check` fails group/other bits on POSIX
        key_dir.chmod(0o700)
        (key_dir / "secrets.env").chmod(0o600)
    s = settings.load({"HADAVIN_LOCAL": str(local), "INTAKE_MODEL_BACKEND": backend})
    if (
        with_ledger
    ):  # WP1: the spend ledger (``intake init``); a live-backend test also records a provider limit with ``budget.confirm_limit``
        from intake import budget

        budget.init(s)
    return s


@pytest.fixture
def intake_settings(tmp_path):
    return settings_for_tests(tmp_path)


@pytest.fixture(autouse=True)
def _reset_queue_clock():
    """The queue clock is a module seam (errata 41c): a test that fixes it must never leak the fixed time into the next test."""
    yield
    from intake import workqueue

    workqueue.reset_clock()
