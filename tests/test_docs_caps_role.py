"""The operator docs say what the code does about the caps role (fix round 1 of lead-b-migrate): five roles, a caps
login of its own for `limits set-cap`, `sync-caps` and `check-caps`, a reset login that runs no money function, and
the audit rights that are still wider than needed. A stale line sends an operator to a deploy order that breaks the
caps (the cap commands refuse the reset secret), so each line is pinned here. No database needed."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _text(name: str) -> str:
    return " ".join((ROOT / name).read_text(encoding="utf-8").split())


RUNBOOK, CHANGELOG, README, SECURITY = (
    _text(n) for n in ("docs/stop-state-runbook.md", "CHANGELOG.md", "README.md", "SECURITY.md")
)


def test_the_runbook_names_the_caps_login_for_the_cap_commands():
    assert "only the caps login (`migrate --caps-role`) can write a cap" in RUNBOOK
    assert "only the reset login can write a cap" not in RUNBOOK
    assert "`backends.store.caps_credential_ref`" in RUNBOOK
    assert "Commands (all under the caps login" in RUNBOOK
    assert "Commands (all under the reset login" not in RUNBOOK
    assert "Provision a reset login (every PostgreSQL deployment needs one now" not in RUNBOOK


def test_the_runbook_setup_names_five_roles_and_the_caps_flag():
    step2 = RUNBOOK[RUNBOOK.index("2. Run `hadavin-sdk migrate") :][:900]
    assert "--caps-role <caps>" in step2 and "five roles" in step2
    assert "four roles" not in RUNBOOK
    assert "REFUSED" in step2  # a reset role without a caps role


def test_the_release_section_names_the_caps_role_in_its_migrate_command():
    assert "--reset-role X --caps-role C --release-role Y" in RUNBOOK


def test_the_changelog_deploy_order_uses_the_caps_ref_not_the_reset_ref_for_sync_caps():
    step = CHANGELOG[CHANGELOG.index("Deploy order: stop the tick") :][:600]
    assert "--caps-role" in step and "backends.store.caps_credential_ref" in step
    assert not re.search(
        r"set `backends.store.reset_credential_ref`; `hadavin-sdk limits sync-caps", step
    )
    assert "written only under the reset login" not in CHANGELOG
    assert "written only under the caps login" in CHANGELOG


def test_readme_and_security_say_who_sets_caps_and_that_reset_runs_no_money_function():
    for doc in (README, SECURITY):
        assert "--caps-role" in doc and "caps_credential_ref" in doc
        assert "reset" in doc and "no money function" in doc


def test_readme_and_security_say_plainly_that_two_audit_rights_are_still_too_wide():
    for doc in (README, SECURITY):
        assert "audit_outbox" in doc and "audit_checkpoints" in doc
        assert re.search(r"still wider than (they )?need", doc, re.IGNORECASE)
    assert (
        "It does not enforce (1)" not in SECURITY
    )  # migrate refuses an owning or owner-member login now
