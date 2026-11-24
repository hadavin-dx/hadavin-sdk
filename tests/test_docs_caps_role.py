"""The operator docs say what the code does about the caps role (fix round 1 of lead-b-migrate): five roles, a caps
login of its own for `limits set-cap`, `sync-caps` and `check-caps`, a reset login that runs no money function, and
the audit rights that are still wider than needed. A stale line sends an operator to a deploy order that breaks the
caps (the cap commands refuse the reset secret), so each line is pinned here. No database needed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

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


_LOGIN = {
    "runtime": "the runtime login",
    "caps": "the caps login",
    "reset": "the reset login",
    "purge": "the purge login",
    "release": "the release login",
    "portal": "the portal login",
}


def _holders(function: str) -> list[str]:
    """Who may EXECUTE the function, read from the grant table in the code (FUNCTION_GRANTS), in a fixed order."""
    import dataclasses

    pytest.importorskip(
        "psycopg", reason="the grant table lives in store/migrate.py (hadavin-sdk[pg])"
    )
    from hadavin_sdk.store.migrate import FUNCTION_GRANTS

    (grant,) = [g for sig, g in FUNCTION_GRANTS.items() if sig.startswith(function + "(")]
    held = [f.name for f in dataclasses.fields(grant) if getattr(grant, f.name)]
    return [_LOGIN[k] for k in _LOGIN if k in held]


def test_the_readme_sentence_on_the_cap_functions_is_what_the_grant_table_says():
    """MAJOR-1 / NIT-4: the sentence is BUILT from FUNCTION_GRANTS, so a README that names another set of logins
    (round 1 said the caps login alone runs both functions) fails, and so does a grant change without a README change."""
    setters, readers = _holders("hadavin_set_cap"), _holders("hadavin_cap_matches")
    assert len(setters) == 1
    only = setters[0].replace("the ", "Only the ", 1)
    # one clause, from its first word to the second function: a list of logins that is only PART of the README's
    # list (the table lost a login and the README did not) must not match
    assert (
        f"{only} can run the function `hadavin_set_cap`; {' and '.join(readers)} can run "
        "`hadavin_cap_matches` (read-only"
    ) in README
    for login in set(_LOGIN.values()) - set(setters):
        assert f"{login} can run the function `hadavin_set_cap`" not in README
    assert (
        "and the functions `hadavin_set_cap` and `hadavin_cap_matches`" not in README
    )  # the round-1 sentence


def test_no_operator_text_sends_the_cap_commands_to_the_reset_login():
    """MINOR-2: command-line help, the module text, the tick message and the migration comment name the caps login."""
    src = ROOT / "src" / "hadavin_sdk"
    for rel in (
        "cli.py",
        "runtime/tick.py",
        "store/protocol.py",
        "store/migrations/0011_money_definer.sql",
    ):
        text = " ".join((src / rel).read_text(encoding="utf-8").split())
        assert "reset login, audited" not in text, rel
        assert "under the reset login" not in text, rel
        assert "the reset login runs it" not in text, rel
    cli_text = (src / "cli.py").read_text(encoding="utf-8")
    assert "[--caps-role C]" in cli_text
    for command in ("limits set-cap", "limits sync-caps", "limits check-caps"):
        assert command in cli_text.split('"""')[1], (
            command
        )  # the module docstring lists the command
    assert "written only under the reset login" not in README + SECURITY


def test_the_migrate_docstring_says_the_library_accepts_a_reset_role_without_a_caps_role():
    pytest.importorskip("psycopg", reason="store/migrate.py needs hadavin-sdk[pg]")
    from hadavin_sdk.store.migrate import migrate

    doc = " ".join(migrate.__doc__.split())
    assert "ACCEPTS a `reset_role` without a `caps_role`" in doc and "`caps_role`" in doc
    assert "the command line refuses that pair" in doc


def test_readme_and_security_say_plainly_that_two_audit_rights_are_still_too_wide():
    for doc in (README, SECURITY):
        assert "audit_outbox" in doc and "audit_checkpoints" in doc
        assert re.search(r"still wider than (they )?need", doc, re.IGNORECASE)
    assert (
        "It does not enforce (1)" not in SECURITY
    )  # migrate refuses an owning or owner-member login now


# --- review round 3 of lead-b-migrate (combined branch) -----------------------------------------------------------


def test_no_repo_doc_points_into_the_handover_folder():
    """MINOR 4: a reader of the shipped docs is never sent to a working file of the build."""
    docs = [ROOT / n for n in ("README.md", "SECURITY.md", "CHANGELOG.md")] + sorted(
        (ROOT / "docs").glob("*.md")
    )
    for path in docs:
        assert "handover/" not in path.read_text(encoding="utf-8"), path.name


def test_the_changelog_says_which_migrations_are_unreleased_and_what_to_do_about_the_0011_draft():
    """MINOR 4 and MINOR 3: 0008 to 0011 (0007 is released: migrate refuses a changed 0007), and the two commands."""
    assert (
        "0008 to 0011 are unreleased" in CHANGELOG
        and "0007 to 0011 are unreleased" not in CHANGELOG
    )
    line = CHANGELOG[CHANGELOG.index("0008 to 0011 are unreleased") :][:900]
    assert "docs/migration-checksums.md" in line and "hadavin_expired_holds(integer)" in line
    assert (
        "--reset-draft 0011_money_definer" in line
        and "--accept-changed-draft 0011_money_definer" in line
    )


def test_every_doc_says_only_a_superuser_revokes_a_creators_admin_option():
    """MINOR 1: the fix that works on a managed database service is named in all four."""
    for doc in (RUNBOOK, CHANGELOG, README, SECURITY):
        assert re.search(r"only a superuser can (take it away|revoke)", doc, re.IGNORECASE)
        assert "login that owns the tables" in doc
    assert "FROM <creator>` as a role that may" not in RUNBOOK


def test_the_role_lists_name_all_six_roles_and_the_command_text_lists_the_draft_flags():
    """NIT 1, 2, 3, 5 of review round 3."""
    pytest.importorskip("psycopg", reason="store/migrate.py needs hadavin-sdk[pg]")
    import inspect

    from hadavin_sdk import cli
    from hadavin_sdk.store import migrate as migrate_mod

    src = " ".join(inspect.getsource(migrate_mod).split())
    assert "purge and reset roles in ONE" not in src
    assert (
        src.count("runtime, portal, purge, reset, release and caps roles in ONE migrate command")
        == 2
    )
    cli_src = inspect.getsource(cli)
    for flag in (
        "--runtime-role",
        "--portal-role",
        "--purge-role",
        "--reset-role",
        "--release-role",
        "--caps-role",
    ):
        assert flag in cli_src[cli_src.index("refused: no role is named") :][:400], flag
    usage = cli.__doc__
    assert (
        "[--accept-changed-draft V ...] [--reset-draft V]" in usage
        and "[--validate-constraints]" in usage
    )
    assert (
        "the reset, release or caps ref" in RUNBOOK
    )  # NIT 2: the start refusal covers the caps ref too
    assert "grant the reset role to itself (for example" not in RUNBOOK  # NIT 5: any named role
    assert (
        "grant ANY named role to itself" in RUNBOOK
        and "cannot grant ANY named role to itself" in src
    )
