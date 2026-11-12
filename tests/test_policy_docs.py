"""Checks of the texts around the declared permissions that live outside the page: the CHANGELOG entry, the
README link and the CI workflow (ticket Q8c, PR 1, fix batch 1). Kept apart from tests/test_policy_guard.py
because the mutant runner copies only `src`, `tests`, `tools` and `docs` into its temp tree.
"""

from __future__ import annotations

import yaml as _yaml
from tools import policy_page as pp

from tests.test_policy_guard import ROOT, _policies, changelog_entry, kinds_sentence, stray_days


def _changelog_entry() -> str:
    """The entry for this work (the one cut of tests/test_policy_changelog.py)."""
    return changelog_entry()


def _readme_paragraph() -> str:
    lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    return next(line for line in lines if line.startswith("- **Declared permissions.**"))


def test_m1_no_text_states_the_vault_refusals_as_fact_while_no_run_is_on_record():
    assert pp.ENGINE_RUN is None, "a run is on record: change this test together with ENGINE_RUN"
    page = pp.page(ROOT)
    for name, text in (("page", page), ("CHANGELOG", _changelog_entry())):
        flat = " ".join(text.split())
        assert "refused by a real Vault server" not in flat, name
        assert "have not run yet" in flat, name
    assert page.count("These tests have not run yet: no run of them is on record.") == 3


def test_the_page_title_notes_and_engine_image_are_true():
    text = pp.page(ROOT)
    assert text.startswith("# Declared permissions per backend kind\n")
    assert pp.PAGE == "docs/declared-permissions.md"
    for name, body in (
        ("README paragraph", _readme_paragraph()),
        ("CHANGELOG entry", _changelog_entry()),
        ("page", text),
    ):
        assert "least-privilege polic" not in body.lower(), name
    assert "builder's memory" not in text and "No ticket removes this yet" not in text
    jobs = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))["jobs"]
    images = {
        job["services"]["vault"]["image"]
        for job in jobs.values()
        if "vault" in (job.get("services") or {})
    }
    assert len(images) == 1 and images.pop().startswith(pp.ENGINE_IMAGE + "@sha256:")
    for words in (
        f"one server image only: `{pp.ENGINE_IMAGE}`, licence: Business Source License 1.1",
        "The open alternative OpenBao (licence MPL-2.0)",
        "it has not yet been",
        "identity groups of the signed-in entity",
        "the wildcard verb `*`",
        "`create` on the self-review resources",
        "the namespaced Role on this page cannot grant it",
        "the code never sends the longer form. That the exact path does not also allow the longer form is a claim nobody has checked",
    ):
        assert words in " ".join(text.split()), words
    never = {(k, n.name) for k, p in _policies().items() for n in p.never}
    for entry in (
        ("secrets/vault", "{mount}/delete/*"),
        ("secrets/vault", "{mount}/undelete/*"),
        ("secrets/vault", "{mount}/subkeys/*"),
        ("signer/vault_transit", "{transit_mount}/byok-export/*"),
        ("signer/vault_transit", "{transit_mount}/keys/{key_name}/rotate"),
        ("signer/vault_transit", "{transit_mount}/keys/{key_name}/trim"),
        ("signer/vault_transit", "{transit_mount}/restore"),
        ("signer/vault_transit", "{transit_mount}/restore/*"),
    ):
        assert entry in never, entry
    data = next(n for n in _policies()["secrets/vault"].never if n.name == "{mount}/data/*")
    assert "patch" in data.capabilities


def test_m14_ci_runs_the_policy_mutants_next_to_the_stage_mutants():
    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    runs = [s.get("run", "") for s in steps]
    assert "python tests/stage_mutants.py" in runs and "python tests/policy_mutants.py" in runs
    assert (
        runs.index("python tests/policy_mutants.py")
        == runs.index("python tests/stage_mutants.py") + 1
    )


def _check_step_problem(runs: list[str]) -> str:
    """The one rule for the CI step list: `--check` is the command people run; only it uses the tool's own
    clock, so it must also run on its own in CI, right after the policy mutants. '' when the list is right."""
    if "python tools/policy_page.py --check" not in runs:
        return "ci.yml has no step `python tools/policy_page.py --check`"
    if (
        runs.index("python tools/policy_page.py --check")
        != runs.index("python tests/policy_mutants.py") + 1
    ):
        return (
            "the step `python tools/policy_page.py --check` is not right after the policy mutants"
        )
    return ""


def test_ci_runs_the_policy_page_check_right_after_the_policy_mutants():
    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    runs = [s.get("run", "") for s in steps]
    assert not _check_step_problem(runs), _check_step_problem(runs)


def test_plant_a_ci_step_list_without_or_with_a_moved_check_step_is_refused():
    # No mutant can edit ci.yml (the mutant runner copies only src, tests, tools and docs), so the rule is a
    # function and this test feeds it the two wrong lists.
    mutants, check = "python tests/policy_mutants.py", "python tools/policy_page.py --check"
    assert _check_step_problem(["a", mutants, check, "b"]) == ""
    assert "has no step" in _check_step_problem(["a", mutants, "b"])
    assert "not right after" in _check_step_problem([check, "a", mutants])
    assert "not right after" in _check_step_problem([mutants, "a", check])


def _notes_step_problem(steps: list[dict]) -> str:
    """The one rule for the CI step of the notes check: it runs `tools/notes_lines_check.py --auto "$BASE_SHA"`, on
    pull requests only, with the base taken from the head before the push (or the base of the pull request), and
    the base is fetched first. '' when the step is right."""
    found = [s for s in steps if "tools/notes_lines_check.py" in s.get("run", "")]
    if len(found) != 1:
        return f"ci.yml has {len(found)} steps that run tools/notes_lines_check.py, not one"
    step = found[0]
    run = step["run"]
    if 'python tools/notes_lines_check.py --auto "$BASE_SHA"' not in run:
        return "the notes step does not run `--auto` with the base in BASE_SHA"
    if "git fetch" not in run or run.index("git fetch") > run.index("notes_lines_check"):
        return "the notes step does not fetch the base before it runs the check"
    if step.get("if") != "github.event_name == 'pull_request'":
        return "the notes step is not limited to pull requests"
    base = str(step.get("env", {}).get("BASE_SHA", ""))
    if "github.event.before" not in base or "github.event.pull_request.base.sha" not in base:
        return "the notes step does not take the base from the head before the push, then the pull request base"
    return ""


def test_ci_runs_the_builder_notes_check_on_pull_requests_with_the_base_fetched():
    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    assert not _notes_step_problem(steps), _notes_step_problem(steps)


def test_plant_a_ci_notes_step_that_is_missing_unfetched_unlimited_or_on_the_wrong_base_is_refused():
    good = {
        "if": "github.event_name == 'pull_request'",
        "env": {"BASE_SHA": "${{ github.event.before || github.event.pull_request.base.sha }}"},
        "run": 'git fetch --no-tags --depth=1 origin "$BASE_SHA"\n'
        'python tools/notes_lines_check.py --auto "$BASE_SHA"',
    }
    assert _notes_step_problem([good]) == ""
    assert "not one" in _notes_step_problem([])
    assert "not one" in _notes_step_problem([good, good])
    assert "`--auto`" in _notes_step_problem([{**good, "run": "python tools/notes_lines_check.py"}])
    assert "fetch the base" in _notes_step_problem(
        [{**good, "run": 'python tools/notes_lines_check.py --auto "$BASE_SHA"'}]
    )
    assert "pull requests" in _notes_step_problem([{k: v for k, v in good.items() if k != "if"}])
    assert "take the base" in _notes_step_problem(
        [{**good, "env": {"BASE_SHA": "${{ github.event.pull_request.base.sha }}"}}]
    )


def _date_guard_sentence_problem(flat: str) -> str:
    """The changelog sentences about the date guard: it starts the day after the earliest `review_by`, it is a
    reminder, and it writes no day as text but the kinds list's own (read from the list). '' when they hold."""
    if "fail from the day after the earliest `review_by`" not in flat:
        return "the changelog entry does not say the date guard starts the day after the earliest review_by"
    if "is a reminder, not a check that anyone re-read the names" not in flat:
        return "the changelog entry does not say the date guard is a reminder"
    if stray_days(flat, kinds_sentence()):
        return "the changelog entry hard-codes a day (not the kinds list's)"
    return ""


def test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder():
    flat = " ".join(_changelog_entry().split())
    assert not _date_guard_sentence_problem(flat), _date_guard_sentence_problem(flat)


def test_plant_a_changelog_entry_that_loses_the_reminder_sentence_or_fixes_a_day_is_refused():
    # CHANGELOG.md is outside the mutant runner's temp tree, so the rule is a function fed three wrong texts.
    good = (
        "fail from the day after the earliest `review_by` and "
        f"is a reminder, not a check that anyone re-read the names, and {kinds_sentence()}"
    )
    assert _date_guard_sentence_problem(good) == ""
    assert "starts the day after" in _date_guard_sentence_problem(good.replace("the earliest", "a"))
    assert "is a reminder" in _date_guard_sentence_problem(good.replace("is a reminder", "is"))
    assert "hard-codes" in _date_guard_sentence_problem(good + " and from 2026-12-12 on")


def test_the_changelog_says_seven_rows_are_abbreviated_and_the_openbao_release_is_not_pinned():
    flat = " ".join(_changelog_entry().split())
    assert "seven rows carry a 7-character abbreviated id" in flat
    assert "OpenBao claims are not tied to one release" in flat
