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


def _checkout_is_full(steps: list[dict]) -> bool:
    """True when the step that checks the code out in this job fetches the whole history."""
    boxes = [s for s in steps if str(s.get("uses", "")).startswith("actions/checkout@")]
    return len(boxes) == 1 and str(boxes[0].get("with", {}).get("fetch-depth")) == "0"


def _notes_step_problem(steps: list[dict]) -> str:
    """The one rule for the CI step of the notes check: on pull requests only, it runs
    `tools/notes_lines_check.py --auto "$BASE_SHA" --head "$HEAD_SHA"` with the base and the head commit id of the
    pull request (never the head before the push, never the merge commit), and the job's checkout has the whole
    history (without it there is no common ancestor). '' when the step is right."""
    found = [s for s in steps if "tools/notes_lines_check.py" in s.get("run", "")]
    if len(found) != 1:
        return f"ci.yml has {len(found)} steps that run tools/notes_lines_check.py, not one"
    step = found[0]
    run = step["run"]
    if 'python tools/notes_lines_check.py --auto "$BASE_SHA" --head "$HEAD_SHA"' not in run:
        return "the notes step does not run `--auto` with the base in BASE_SHA and the head in HEAD_SHA"
    if step.get("if") != "github.event_name == 'pull_request'":
        return "the notes step is not limited to pull requests"
    env = step.get("env", {})
    if str(env.get("BASE_SHA", "")).strip() != "${{ github.event.pull_request.base.sha }}":
        return "the notes step does not take the base from the base of the pull request"
    if str(env.get("HEAD_SHA", "")).strip() != "${{ github.event.pull_request.head.sha }}":
        return "the notes step does not take the head from the head commit id of the pull request"
    if "github.event.before" in run or "github.event.before" in str(env):
        return "the notes step reads the head before the push: it must check the whole pull request"
    if not _checkout_is_full(steps):
        return "the job's checkout does not fetch the whole history (fetch-depth 0)"
    return ""


def test_ci_runs_the_builder_notes_check_on_pull_requests_with_the_base_fetched():
    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    assert not _notes_step_problem(steps), _notes_step_problem(steps)


def test_plant_a_ci_notes_step_that_is_missing_unfetched_unlimited_or_on_the_wrong_base_is_refused():
    checkout = {"uses": "actions/checkout@abc", "with": {"fetch-depth": 0}}
    good = {
        "if": "github.event_name == 'pull_request'",
        "env": {
            "BASE_SHA": "${{ github.event.pull_request.base.sha }}",
            "HEAD_SHA": "${{ github.event.pull_request.head.sha }}",
        },
        "run": 'python tools/notes_lines_check.py --auto "$BASE_SHA" --head "$HEAD_SHA"',
    }
    assert _notes_step_problem([checkout, good]) == ""
    assert "not one" in _notes_step_problem([checkout])
    assert "not one" in _notes_step_problem([checkout, good, good])
    assert "`--auto`" in _notes_step_problem(
        [checkout, {**good, "run": "python tools/notes_lines_check.py"}]
    )
    assert "`--auto`" in _notes_step_problem(
        [checkout, {**good, "run": 'python tools/notes_lines_check.py --auto "$BASE_SHA"'}]
    )
    assert "pull requests" in _notes_step_problem(
        [checkout, {k: v for k, v in good.items() if k != "if"}]
    )
    assert "base of the pull request" in _notes_step_problem(
        [checkout, {**good, "env": {**good["env"], "BASE_SHA": "${{ github.event.before }}"}}]
    )
    assert "head commit id" in _notes_step_problem(
        [checkout, {**good, "env": {**good["env"], "HEAD_SHA": "${{ github.sha }}"}}]
    )
    assert "whole history" in _notes_step_problem(
        [{"uses": "actions/checkout@abc", "with": {"fetch-depth": 1}}, good]
    )
    assert "whole history" in _notes_step_problem([{"uses": "actions/checkout@abc"}, good])
    assert "before the push" in _notes_step_problem(
        [checkout, {**good, "run": good["run"] + "  # github.event.before"}]
    )


def test_the_notes_check_on_a_made_up_merge_commit_reads_the_pull_request_head_not_the_merge(
    tmp_path, monkeypatch, capsys
):
    """The runner checks out a merge commit; the step must work from the pull request head commit and the common
    ancestor. Rebuild that shape in a made-up repository and run the command line the workflow step holds (read
    from ci.yml, with its two environment values filled in), so a change of the step changes this test's input."""
    import shlex

    from tools import notes_lines_check as nlc

    from tests.test_notes_lines_check import _rev

    steps = _yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]["check"]["steps"]
    (step,) = [s for s in steps if "tools/notes_lines_check.py" in s.get("run", "")]
    monkeypatch.chdir(tmp_path)
    _rev(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_one.py").write_text("def test_a():\n    assert 1\n", encoding="utf-8")
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "base")
    base_sha = _rev(tmp_path, "rev-parse", "HEAD")
    _rev(tmp_path, "checkout", "-q", "-b", "pr")
    (tmp_path / "tests/test_one.py").write_text(
        "def test_a():\n    assert 1\n\n\ndef test_new():\n    assert 2\n", encoding="utf-8"
    )
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "pr head")
    head_sha = _rev(tmp_path, "rev-parse", "HEAD")
    _rev(tmp_path, "checkout", "-q", "main")
    (tmp_path / "other.txt").write_text("main moved on\n", encoding="utf-8")
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "main moves")
    _rev(tmp_path, "merge", "-q", "--no-ff", "-m", "merge", "pr")  # the checked-out merge commit
    words = shlex.split(step["run"].strip())
    assert words[:2] == ["python", "tools/notes_lines_check.py"], f"the step runs {words[:2]}"
    argv = [{"$BASE_SHA": base_sha, "$HEAD_SHA": head_sha}.get(w, w) for w in words[2:]]
    assert nlc.main(argv) == 1, (
        "the pull request's new test has no row but the check passed on the merge shape"
    )
    out = capsys.readouterr().out
    assert "test_new" in out, f"the new test was not named: {out}"
    assert "test_a" not in out.replace("test_new", ""), (
        "a test the pull request did not change was asked for"
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
