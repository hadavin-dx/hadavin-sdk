"""The changelog gives the days the lists of kinds start to fail as the list has them, and writes no review day of
the names and claims as text.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from tests.test_policy_guard import (
    PENDING_KINDS,
    changelog_entry,
    kinds_sentence,
    stray_days,
)

ROOT = Path(__file__).resolve().parents[1]


KINDS_GROUPS = [(7, "2026-12-12"), (9, "2027-02-01")]
KINDS_LITERAL = "7 of them from 2026-12-12 and the other 9 from 2027-02-01"


def _groups_text(groups: list[tuple[int, str]]) -> str:
    """The groups as words, built from the pin itself: '7 kinds that fail from D1 and 9 from D2'."""
    parts = [
        f"{n} kinds that fail from {d}" if i == 0 else f"{n} from {d}"
        for i, (n, d) in enumerate(groups)
    ]
    return " and ".join(parts)


def _kinds_pin_problem(pending: dict, built: str, entry: str) -> str:
    """The pin of the kinds days, for any list, built sentence and changelog entry: '' when all three agree with
    the groups and the sentence written out above. Two pins that do not follow the list: a change of either (a
    kind added or removed, a renewal of the kinds list) must change this file and the changelog together. The
    groups are compared as a set of (count, day) pairs, so the order they are listed in does not matter: after a
    renewal the group that was renewed may fall behind the other one."""
    groups = sorted(Counter(p.review_by for p in pending.values()).items())
    if sorted((n, (d + timedelta(days=1)).isoformat()) for d, n in groups) != sorted(KINDS_GROUPS):
        return (
            f"the pending kinds list no longer holds {_groups_text(KINDS_GROUPS)}: "
            "change this pin and the changelog sentence together"
        )
    if built != KINDS_LITERAL:
        return "the sentence built from the kinds list is not the one written in this pin"
    if KINDS_LITERAL not in entry:
        return "the changelog does not give the days the kinds list starts to fail"
    return ""


def test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail():
    problem = _kinds_pin_problem(PENDING_KINDS, kinds_sentence(), changelog_entry())
    assert not problem, problem


def test_plant_a_moved_or_regrouped_kinds_list_or_a_changelog_that_follows_it_is_refused():
    from dataclasses import replace

    first = next(iter(PENDING_KINDS))
    earliest = min(p.review_by for p in PENDING_KINDS.values())
    latest = max(p.review_by for p in PENDING_KINDS.values())
    moved = {
        **PENDING_KINDS,
        first: replace(PENDING_KINDS[first], review_by=earliest - timedelta(days=1)),
    }
    regrouped = {k: replace(p, review_by=latest) for k, p in PENDING_KINDS.items()}
    entry = f"text {KINDS_LITERAL} text"
    assert _kinds_pin_problem(PENDING_KINDS, KINDS_LITERAL, entry) == "", (
        "the right list was refused"
    )
    assert "no longer holds 7 kinds" in _kinds_pin_problem(moved, kinds_sentence(moved), entry), (
        "a kind moved to another day was accepted (a changelog that follows the list)"
    )
    assert "no longer holds 7 kinds" in _kinds_pin_problem(
        regrouped, kinds_sentence(regrouped), entry
    ), "a list of one group was accepted"
    assert "not the one written in this pin" in _kinds_pin_problem(
        PENDING_KINDS,
        KINDS_LITERAL[:-1] + "2",
        entry,  # the last day of the sentence moved by one
    ), "a built sentence with another day was accepted"
    assert "does not give the days" in _kinds_pin_problem(
        PENDING_KINDS, KINDS_LITERAL, "text with no sentence"
    ), "a changelog without the sentence was accepted"


def test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list():
    stray = stray_days(changelog_entry(), kinds_sentence())
    assert not stray, (
        f"the changelog entry writes a day as text that is not the kinds list's: {stray}"
    )
    assert kinds_sentence() in changelog_entry(), (
        "the changelog entry does not hold the kinds sentence built from the list"
    )
    assert "review by the earliest review date" in changelog_entry(), (
        "the changelog entry does not name the review day by rule"
    )


def test_plant_changelog_rows_that_write_a_day_are_refused():
    sentence = kinds_sentence()
    good = f"fails for {sentence}, unless renewed"
    assert stray_days(good, sentence) == [], "the allowed sentence alone is flagged"
    for said, row in (
        ("a review date", good + " (review date 2026-12-11)"),
        ("a review by day", good + " (review by 2026-12-11)"),
        ("a start day of the names list", good + " and the names list fails from 2026-12-12"),
        ("a day of another entry (a stale docstring day)", good + " the tool says 2027-03-03"),
        ("a day written with slashes", good + " and from 2026/12/12"),
        ("a day written with the month in words", good + " and from 12 December 2026"),
        ("a day written as month and number", good + " and from Dec 12"),
    ):
        assert stray_days(row, sentence), f"{said} written in the entry is not flagged"


def test_the_changelog_entry_for_the_page_names_no_review_by_day_as_text():
    # The review day of the names and claims is built by the tool (`review_date()`) and shown on the page; a day
    # written into the changelog entry would stay after a renewal. The entry says "the earliest review date".
    # (The days the kinds list starts to fail are checked above against the dated list itself.)
    entry = changelog_entry()
    stray = re.findall(r"review by \d{4}-\d{2}-\d{2}", entry)
    assert not stray, f"the changelog entry writes a review day as text: {stray}"
    assert "review by the earliest review date" in entry, (
        "the changelog entry does not name the review day by rule"
    )


def test_the_changelog_says_what_a_renewal_renews_in_the_words_of_the_code_and_not_the_old_one_list_wording():
    # the code and the guard tests require BOTH lists of names and claims to carry one `decided` day, and the 16
    # kinds a day of their own; "every entry of the same list is renewed with it" said the wrong thing
    from tools import policy_page as pp

    flat = (
        changelog_entry()
    )  # the entry of this work, whitespace folded (the renewal bullet is nested in it)
    assert pp.RENEWAL_RULE in flat, (
        "the changelog does not hold the renewal rule of the names and claims word for word"
    )
    assert pp.KINDS_RENEWAL_RULE in flat, (
        "the changelog does not hold the renewal rule of the kinds word for word"
    )
    assert "every entry of the same list is renewed with it" not in flat, (
        "the changelog still says that every entry of the same list is renewed (both lists must be)"
    )


def _renewed_kinds(new_decided: date) -> dict:
    """The kinds list after a renewal of the kinds: every kind gets the new decision day, and the kinds that fail
    first get a `review_by` 30 days after it (the others keep their day, which stays inside the 92 days)."""
    from dataclasses import replace

    first = min(p.review_by for p in PENDING_KINDS.values())
    new_review = new_decided + timedelta(days=30)
    return {
        k: replace(
            p, decided=new_decided, review_by=new_review if p.review_by == first else p.review_by
        )
        for k, p in PENDING_KINDS.items()
    }


def _kinds_groups_of(pending: dict) -> list[tuple[int, str]]:
    return sorted(
        (n, (d + timedelta(days=1)).isoformat())
        for d, n in Counter(p.review_by for p in pending.values()).items()
    )


def _renewal_edits(
    old_decided: date, new_decided: date, names_and_claims: bool = True, kinds: bool = True
) -> list[tuple[str, str, str]]:
    """The edits of a renewal, written the way the renewal lists of the tool say (the steps of RENEWAL_STEPS for
    the names and claims, the steps of KINDS_RENEWAL_STEPS for the 16 kinds), built from the LIVE days: (file, text
    now, text after). Both groups: the names and claims move to `new_decided` and a `review_by` 30 days later, the
    kinds to `new_decided` too. Only the kinds (`names_and_claims` False): the kinds list alone. The pin of the
    kinds days (`KINDS_GROUPS`, `KINDS_LITERAL`, the changelog sentence) is rewritten from the renewed list, whatever
    order its groups fall in, as step (2) and (3) of the kinds steps say."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    def call(d: date) -> str:
        return f"date({d.year}, {d.month}, {d.day})"

    new_review = new_decided + timedelta(days=30)
    old_reviews = {p.review_by for p in (*pp.PENDING_NAMES.values(), *pp.PENDING_CLAIMS.values())}
    first_kinds = min(p.review_by for p in PENDING_KINDS.values())
    guard, tool, changelog = (
        "tests/test_policy_guard.py",
        "tools/policy_page.py",
        "tests/test_policy_changelog.py",
    )
    edits: list[tuple[str, str, str]] = []
    if names_and_claims:
        edits.append((tool, f"DECIDED = {call(old_decided)}", f"DECIDED = {call(new_decided)}"))
        edits += [
            (tool, f"    {call(d)},\n", f"    {call(new_review)},\n") for d in sorted(old_reviews)
        ]
        edits.append(
            (
                guard,
                f"assert pp.DECIDED == {call(old_decided)}",
                f"assert pp.DECIDED == {call(new_decided)}",
            )
        )
    if kinds:
        edits += [
            (
                guard,
                f"KINDS_DECIDED = {call(KINDS_DECIDED)}",
                f"KINDS_DECIDED = {call(new_decided)}",
            ),
            (guard, f"{{{call(KINDS_DECIDED)}}}", f"{{{call(new_decided)}}}"),
            (guard, f'"Q8c PR 2", {call(first_kinds)})', f'"Q8c PR 2", {call(new_review)})'),
            (guard, f"on the literal day {KINDS_DECIDED}", f"on the literal day {new_decided}"),
        ]
        renewed = _renewed_kinds(new_decided)
        old_text = Path(ROOT / "tests/test_policy_changelog.py").read_text(encoding="utf-8")
        old_groups = re.search(r"^KINDS_GROUPS = .*$", old_text, re.MULTILINE)
        old_literal = re.search(r"^KINDS_LITERAL = .*$", old_text, re.MULTILINE)
        assert old_groups and old_literal, "the kinds pin lines were not found in this file"
        edits += [
            (changelog, old_groups.group(0), f"KINDS_GROUPS = {_kinds_groups_of(renewed)!r}"),
            (changelog, old_literal.group(0), f"KINDS_LITERAL = {kinds_sentence(renewed)!r}"),
        ]
    return edits


RENEWED_TREES = ("src", "tests", "tools", "docs", ".github")  # the folders a renewed copy holds
RENEWED_FILES = ("CHANGELOG.md", "pyproject.toml", "README.md")  # and the files at its root
GIT = shutil.which("git") or "git"  # the git of this machine, found once
NOT_EDITED = (
    "tests/policy_mutants.py",
)  # a file the steps name only to say that nothing is edited there


def _steps_of(mode: str) -> str:
    """The printed steps a renewal of `mode` follows ('both' groups, the 'names' and claims alone, the 'kinds'
    alone), up to the emptying steps (the emptying is not a renewal)."""
    from tools import policy_page as pp

    names = pp.RENEWAL_STEPS.split("An emptying also touches")[0]
    return {
        "both": names + pp.KINDS_RENEWAL_STEPS,
        "names": names,
        "kinds": pp.KINDS_RENEWAL_STEPS,
    }[mode]


def _commit_the_copy(copy: Path, message: str) -> str:
    """A commit of the whole copy (a throwaway repository inside the temporary folder); its id."""
    env = {
        **{k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")},
        "GIT_AUTHOR_NAME": "renewal plant",
        "GIT_AUTHOR_EMAIL": "plant@example.invalid",
        "GIT_COMMITTER_NAME": "renewal plant",
        "GIT_COMMITTER_EMAIL": "plant@example.invalid",
    }
    if not (copy / ".git").exists():
        subprocess.run(  # noqa: S603
            [GIT, "init", "-q", "-b", "base"], cwd=copy, env=env, capture_output=True, check=True
        )
    for args in (["add", "-A"], ["commit", "-q", "-m", message]):
        done = subprocess.run(  # noqa: S603  (fixed git argv, a temporary copy, no shell)
            [GIT, *args], cwd=copy, env=env, capture_output=True, text=True, check=False
        )
        assert done.returncode == 0, f"git {args[0]} failed in the copy: {done.stderr[-400:]}"
    head = subprocess.run(  # noqa: S603
        [GIT, "rev-parse", "HEAD"], cwd=copy, env=env, capture_output=True, text=True, check=False
    )
    return head.stdout.strip()


def _make_renewed_copy(
    copy: Path, mode: str, old_decided: date, new_decided: date, commit_base: bool = False
) -> tuple[list[str], str]:
    """Copy the repository into `copy` and apply the edits of the printed steps of `mode`: (the files edited, the
    commit of the copy before the first edit when `commit_base` is set, else ''). A renewal with no edit at all is
    refused here: a plant with nothing to apply would pass whatever the steps say."""
    root = Path(__file__).resolve().parents[1]
    copy.mkdir(parents=True, exist_ok=True)
    for name in RENEWED_TREES:
        shutil.copytree(
            root / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
    for name in RENEWED_FILES:
        shutil.copy(root / name, copy / name)
    base = _commit_the_copy(copy, "the repository before the renewal") if commit_base else ""
    edits = _renewal_edits(
        old_decided, new_decided, mode in ("both", "names"), mode in ("both", "kinds")
    )
    assert edits, "the renewal has no edit at all: a plant with nothing to apply passes vacuously"
    edited: set[str] = set()
    for rel, old, new in edits:
        text = (copy / rel).read_text(encoding="utf-8")
        assert old in text, f"the renewal step does not apply: {old!r} is not in {rel}"
        (copy / rel).write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        edited.add(rel)
    # the changelog sentence that gives the days the kinds fail (CHANGELOG.md; the text may wrap)
    if mode != "names":
        words = re.escape(kinds_sentence()).replace("\\ ", r"\s+")
        text = (copy / "CHANGELOG.md").read_text(encoding="utf-8")
        moved, n = re.subn(words, kinds_sentence(_renewed_kinds(new_decided)), text)
        assert n == 1, "the changelog sentence of the kinds days was not found exactly once"
        (copy / "CHANGELOG.md").write_text(moved, encoding="utf-8", newline="\n")
        edited.add("CHANGELOG.md")
    return sorted(edited), base


def _day_in(copy: Path, rel: str, name: str) -> date:
    """The day a copy writes as `name = date(Y, M, D)` in the file `rel`."""
    text = (copy / rel).read_text(encoding="utf-8")
    found = re.findall(rf"^{name} = date\((\d+), (\d+), (\d+)\)", text, re.MULTILINE)
    assert len(found) == 1, f"{rel} has {len(found)} lines `{name} = date(...)`, expected one"
    return date(*map(int, found[0]))


def _renew_and_check(mode: str, old_decided: date, new_decided: date, full_mutants: bool) -> None:
    from tests.test_policy_renewal_copy import (
        _assert_the_copy_follows_the_steps,
        _rows_for_the_renewal,
    )

    """Renew a temporary copy of the repository by the printed steps (`mode` 'both' groups or 'kinds' only) and
    check it on the new decision day and on the day after: the fast checks of the copy against the printed steps,
    the page check, the notes check of CI on the renewed copy (rows generated from its own lines), the policy
    tests, the search texts of the mutants, a sample of the mutants that build their days from the live lists,
    and, when `full_mutants` is set, the whole mutant list."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "renewed"
        edited, base = _make_renewed_copy(copy, mode, old_decided, new_decided, commit_base=True)
        _assert_the_copy_follows_the_steps(copy, mode, edited, new_decided)
        base_env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}

        def run(day: date, *args: str) -> subprocess.CompletedProcess:
            env = dict(
                base_env,
                PYTHONPATH=os.pathsep.join([str(copy / "src"), str(copy)]),
                PYTHONNOUSERSITE="1",
                PYTHONDONTWRITEBYTECODE="1",
                HADAVIN_POLICY_FIXED_DAY=str(day),
                HADAVIN_POLICY_MUTANT_RUN="1",
            )
            return subprocess.run(  # noqa: S603  (argv list of this test, a temporary copy, no shell)
                [sys.executable, *args],
                cwd=copy,
                env=env,
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )

        def page(day: date, what: str) -> subprocess.CompletedProcess:
            return run(
                day,
                "-c",
                "import sys; from datetime import date; from tools import policy_page as p; "
                f"sys.exit(p.main(['{what}'], today=date.fromisoformat('{day}')))",
            )

        write = page(new_decided, "--write")
        assert write.returncode == 0, f"the page was not rewritten: {write.stderr[-600:]}"
        docs = [f for f in sorted((ROOT / "docs").rglob("*")) if f.is_file()]
        assert any((copy / f.relative_to(ROOT)).read_bytes() != f.read_bytes() for f in docs), (
            f"step (4): `--write` left every file of docs/ as it was in the {mode} copy"
        )
        for day in (new_decided, new_decided + timedelta(days=1)):
            check = page(day, "--check")
            assert check.returncode == 0, (
                f"after the {mode} renewal the page check is red on {day}: "
                f"{(check.stdout + check.stderr)[-800:]}"
            )
        notes_env = {**base_env, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
        asked = _rows_for_the_renewal(copy, base, notes_env)
        print(f"renewal plant ({mode}): the notes check asked for {asked} rows")
        tests = run(
            new_decided,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "tests/test_policy_guard.py",
            "tests/test_policy_changelog.py",
            "tests/test_policy_docs.py",
            "tests/test_notes_lines_check.py",
            "--deselect",
            "tests/test_policy_changelog.py::test_plant_a_full_renewal_done_as_the_overdue_messages_list_it_keeps_the_tests_the_page_and_the_mutants_green",
            "--deselect",
            "tests/test_policy_changelog.py::test_plant_a_renewal_of_the_kinds_list_alone_keeps_the_tests_the_page_and_the_mutants_green",
            "--deselect",
            "tests/test_policy_changelog.py::test_plant_a_renewal_of_the_names_and_claims_alone_keeps_the_tests_the_page_and_the_mutants_green",
        )
        assert tests.returncode == 0, (
            f"after the {mode} renewal the tests are red: {tests.stdout[-1500:]}"
        )
        snippets = run(new_decided, "tests/policy_mutants.py", "--snippets")
        assert snippets.returncode == 0, (
            f"a mutant text no longer matches: {snippets.stdout[-800:]}"
        )
        for day in (new_decided, new_decided + timedelta(days=1)):
            picked = () if full_mutants else ("B8", "B9")
            mutants = run(day, "tests/policy_mutants.py", "--day", str(day), *picked)
            assert mutants.returncode == 0, (
                f"after the {mode} renewal the mutants are not all killed on {day}: "
                f"{mutants.stdout[-1500:]}"
            )


FULL_RENEWAL_ENV = (
    "HADAVIN_POLICY_FULL_RENEWAL_RUN"  # set to 1: the plants run the WHOLE mutant list, twice each
)


def test_plant_a_full_renewal_done_as_the_overdue_messages_list_it_keeps_the_tests_the_page_and_the_mutants_green():
    """The renewal of both dated groups on a temporary copy, by the lists of the overdue messages and nothing else,
    done once on the tree as it is (also on a tree that was renewed before: the pin of the kinds days does not
    depend on the order of the groups). On the new decision day and on the day after it the copy must pass: the
    page check, the guard, changelog, docs and notes tests, the search texts of the mutants and the mutants B8 and
    B9 (all mutants when `HADAVIN_POLICY_FULL_RENEWAL_RUN` is 1, as the rehearsal does). The steps the lists name and
    this plant are the same steps; a step that is missing from the list shows here as a red test of the copy."""
    from tests.test_policy_guard import pp

    _renew_and_check(
        "both", pp.DECIDED, pp.DECIDED + timedelta(days=31), os.environ.get(FULL_RENEWAL_ENV) == "1"
    )


def test_plant_a_renewal_of_the_kinds_list_alone_keeps_the_tests_the_page_and_the_mutants_green():
    """The same for a renewal of the 16 kinds alone (the names and claims keep their day): done 20 days after the
    last decision day of the kinds, a day on which the names and claims are still inside their window."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    _renew_and_check(
        "kinds",
        pp.DECIDED,
        KINDS_DECIDED + timedelta(days=20),
        os.environ.get(FULL_RENEWAL_ENV) == "1",
    )


def test_plant_a_renewal_of_the_names_and_claims_alone_keeps_the_tests_the_page_and_the_mutants_green():
    """The same for a renewal of the names and claims alone (the 16 kinds keep their day), done 20 days after the
    last decision day of the names and claims."""
    from tests.test_policy_guard import pp

    _renew_and_check(
        "names",
        pp.DECIDED,
        pp.DECIDED + timedelta(days=20),
        os.environ.get(FULL_RENEWAL_ENV) == "1",
    )
