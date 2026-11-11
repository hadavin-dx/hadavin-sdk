"""One helper for tests that run `migrate` on made-up or planted files.

The released-files check (`released_problems`) knows the real released files and refuses any other; a test about the
grant check, the ledger, the recipe or the read-back uses file names the list has never seen, so it switches that one
check off for the length of the test. The tests of the check itself (`test_migrate_refuses_a_changed_released_file_
before_it_connects`, `test_the_released_check_looks_at_the_files_migrate_runs_not_at_the_folder`) never call this."""

from hadavin_sdk.store import migrate as mig


def made_up_files_are_not_released(monkeypatch) -> None:
    monkeypatch.setattr(mig, "released_problems", lambda *a, **k: [])
