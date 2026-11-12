"""The mutants of the declared-permission guard (ticket Q8c, PR 1), run by ``tools/mutation_runner.py``.

Each mutant reverts ONE rule in a temp copy (of ``tools/policy_page.py``, or of the reader in
``tests/test_policy_guard.py``); the plant test in ``killer`` must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/policy_mutants.py            # all mutants; exit 1 if any is not good
    python tests/policy_mutants.py D1         # only mutants whose name contains the text
    python tests/policy_mutants.py --day 2026-12-12   # the tool's clock shows that day in every mutant run
    python tests/policy_mutants.py --snippets         # no run: each mutant's search text is found in its file

How strong the kill check is: the first failing line must hold ``expect``. A mutant is WEAK when ``expect`` is
in none of the killer's own words, counted from the syntax tree: the message of an ``assert``, the ``match=`` of
``pytest.raises`` and the ``what`` of a ``same()`` call (a comment, a loop literal, a predicate or the ``def`` line
do not count, and pytest's own "DID NOT RAISE" does not name a call; only DIRECT string pieces count: a text inside a
dict, a subscript, a call or a ternary is a union of texts and is not counted). The messages of the helper functions
the killer calls are counted too, so the number of weak mutants the run prints is a LOWER bound: a helper text can
carry the expect text for a killer that never reaches it. The run prints the weak mutants and
exits 1 when there is one. Two
mutants may share one killer (the run prints which).

What has NO mutant here, and why:
* the tests that need a Vault server (tests/test_policy_engine.py): a reverted rule there can only be shown on
  a real server, so their plants run in CI and nowhere else;
* "POLICY must be a pure literal": the refusal is `ast.literal_eval`'s own, and no one-line revert of it exists
  that does not run code; its three plants stay as tests;
* the Kubernetes equalities (declared operations, never-list, verb and resource per path): each is one
  assertion of a test, with no rule function to revert; the independent plants P09b and P09c showed them fire.
"""

import ast
import os
import re
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import NamedTuple

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools import mutation_runner
from tools import policy_page as pp
from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_policy_guard.py"
PIN = "tests/test_policy_guard::"
TOOL = "tools/policy_page.py"
RUN = "tests/policy_mutants.py"
NOTES_TEST = "tests/test_notes_lines_check.py"  # the killer file of the mutants of tools/notes_lines_check.py
NTOOL = "tools/notes_lines_check.py"
CH = "tests/test_policy_changelog.py"  # the pin of the kinds days; its mutants are killed by a test of the guard file


def _text_of(node: ast.AST | None) -> list[str]:
    """The DIRECT string pieces of a message expression: a plain string, the constant parts of an f-string, and
    the pieces of a `+` of those. A string that sits inside a subscript, a call, a ternary or a dict (for example
    `{case: "text"}[name]`, a dict of per-case texts) is NOT counted: such an expression is a union of texts and
    the failing line carries one of them, so counting all of them would let a weak killer look strong."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [
            v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str)
        ]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _text_of(node.left) + _text_of(node.right)
    return []


def message_texts(test: str = TEST) -> dict[str, list[str]]:
    return message_texts_of((ROOT / test).read_text(encoding="utf-8"))


def message_texts_of(source: str) -> dict[str, list[str]]:
    """For every function of the guard file: the texts a failing line can carry by the test's own words, read from
    the syntax tree and from nothing else: the message of an `assert`, the `match=` of `pytest.raises`, and the
    `what` of a `same()` call. A string in a comment, a loop literal, a predicate (`any("x" in p ...)`) or the
    `def` line is NOT counted: it does not appear in the failing line."""
    tree = ast.parse(source)
    out: dict[str, list[str]] = {}
    calls: dict[str, set[str]] = {}
    for f in tree.body:
        if not isinstance(f, ast.FunctionDef):
            continue
        texts: list[str] = []
        for n in ast.walk(f):
            if isinstance(n, ast.Assert):
                texts += _text_of(n.msg)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "same":
                what = (
                    n.args[2]
                    if len(n.args) > 2
                    else next((k.value for k in n.keywords if k.arg == "what"), None)
                )
                texts += _text_of(what)
            elif (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "raises"
            ):
                for k in n.keywords:
                    if k.arg == "match":
                        texts += _text_of(k.value)
        out[f.name] = texts
        calls[f.name] = {
            n.func.id
            for n in ast.walk(f)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
    # the messages of a helper the test calls (directly or through another helper of the same file) are the test's
    # own words too: the failing line of the test is the helper's assert
    own = {name: list(texts) for name, texts in out.items()}
    for name in out:
        seen, todo = {name}, list(calls[name])
        while todo:
            callee = todo.pop()
            if callee in own and callee not in seen:
                seen.add(callee)
                out[name] += own[callee]
                todo += calls[callee]
    return out


def weak_mutants(mutants: list) -> list[tuple[str, str, str]]:
    """(name, expect, killer) of each mutant whose killer's own words (assert message, `match=` of
    `pytest.raises`, `what` of `same()`; see `message_texts`) do not hold `expect`: the first-line check then shows
    only that the killer failed, not at which line."""
    cache: dict[str, dict[str, list[str]]] = {}
    return [
        (m.name, m.expect, m.only_test)
        for m in mutants
        if not any(
            m.expect in t
            for t in cache.setdefault(m.test_file or TEST, message_texts(m.test_file or TEST)).get(
                m.only_test, []
            )
        )
    ]


def mutant(name, file, old, new, killer, expect, test_file=TEST):
    """One mutant: `file` is changed in a copy, `killer` (a function of `test_file`, the guard file unless said)
    must be the first test to fail, with `expect` in its first failing line."""
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=f"{test_file.removesuffix('.py')}::{killer}",
    )


def _date_call(day: date) -> str:
    return f"date({day.year}, {day.month}, {day.day})"


def _guard_line(pattern: str) -> tuple[str, re.Match[str]]:
    """The one line of the guard file that matches `pattern`, as it is written NOW (a renewal changes the days in it,
    so a mutant never carries a day as text of its own), and its match."""
    text = (ROOT / TEST).read_text(encoding="utf-8")
    found = list(re.finditer(pattern, text))
    if len(found) != 1:
        raise SystemExit(
            f"policy_mutants: the guard file has {len(found)} lines like {pattern!r}, expected one"
        )
    return found[0].group(0), found[0]


_DATE_ARGS = r"date\((\d+), (\d+), (\d+)\)"


def _line_days(line: str, shift: int) -> str:
    """`line` with its one `date(y, m, d)` moved by `shift` days."""
    match = re.search(_DATE_ARGS, line)
    assert match, line
    day = date(*map(int, match.groups())) + timedelta(days=shift)
    return line[: match.start()] + _date_call(day) + line[match.end() :]


KINDS_DECIDED_LINE, _ = _guard_line(r"(?m)^KINDS_DECIDED = " + _DATE_ARGS + r"\n")
GEMINI_LINE, _ = _guard_line(
    r'(?m)^    "llm/gemini": Pending\(\*_SLICE2, KINDS_DECIDED, ' + _DATE_ARGS + r"\),\n"
)
TOOL_DECIDED_LINE = f"DECIDED = {_date_call(pp.DECIDED)}\n"
_REVIEW = (
    pp.review_date()
)  # None in the end state: the docs hold no review sentence then, so that mutant is left out
_DOCS_TRIGGER = f"  {_REVIEW}, whichever comes first (ledger row" if _REVIEW else None
_DOCS_TRIGGER_OTHER = (
    f"  {_REVIEW + timedelta(days=1)}, whichever comes first (ledger row" if _REVIEW else None
)


M = [
    mutant(
        "A1 a second request or send in the Vault sending function is no longer reported",
        TEST,
        "    if len(requests) != 1 or len(sends) != 1:\n",
        "    if False:\n",
        "test_plant_a_second_send_in_the_sending_function_is_the_class_caught",
        "a second send inside `call` is not reported",
    ),
    mutant(
        "A1 any text in the Kubernetes paging query is accepted",
        TEST,
        "            if node.value not in _PAGING_TEXT:\n",
        "            if False:\n",
        "test_plant_a_bare_watch_in_the_paging_query_is_the_class_caught",
        "a bare `watch` in the paging query is not reported",
    ),
    mutant(
        "A1 a setting stored in the wrong attribute is no longer reported",
        TEST,
        "        elif stored[name] not in passed:\n",
        "        elif False:\n",
        "test_plant_a_setting_handed_to_the_wrong_parameter_is_the_class_caught",
        "a setting stored in the wrong attribute is not reported",
    ),
    mutant(
        "A1 a `.call` of the Vault client in another module is no longer reported",
        TEST,
        '                and node.attr == "call"\n',
        '                and node.attr == "no-such-name"\n',
        "test_plant_a_call_of_the_vault_client_in_another_module_is_the_class_caught",
        "a `.call` outside the declared modules is not reported",
    ),
    mutant(
        "A1 a request with no grant is no longer reported",
        TEST,
        "    for pair in sorted(set(found) - declared):\n",
        "    for pair in sorted(set()):\n",
        "test_plant_a_new_request_with_no_grant_is_caught",
        "has no grant and no",
    ),
    mutant(
        "A1 a grant whose request is gone is no longer reported",
        TEST,
        "    for pair in sorted(declared - set(found)):\n",
        "    for pair in sorted(set()):\n",
        "test_plant_a_grant_whose_request_was_deleted_is_caught",
        "makes no such call",
    ),
    mutant(
        "A1 a stale allowlist entry is no longer reported",
        TEST,
        "        for func, line, sink in sorted(shape.wrappers - seen)\n",
        "        for func, line, sink in sorted(set())\n",
        "test_plant_a_stale_allowlist_line_is_caught",
        "stale allowlist entry",
    ),
    mutant(
        "Kinds: a kind on no list is no longer reported",
        TEST,
        "        if sum(homes) == 0:\n",
        "        if sum(homes) < 0:\n",
        "test_plant_a_new_kind_on_no_list_is_caught",
        "is on no list",
    ),
    mutant(
        "A4 an unverified grant with no pending entry is no longer reported",
        TOOL,
        "        for kind, label in sorted(unverified - set(pending))\n",
        "        for kind, label in sorted(set())\n",
        "test_plant_an_unverified_grant_with_no_pending_entry_is_caught",
        "is not found in a vendor source",
    ),
    mutant(
        "A4 a source id that does not resolve is no longer reported",
        TOOL,
        "                if s not in known\n",
        "                if s is None\n",
        "test_plant_a_source_id_that_does_not_resolve_is_caught",
        "is not in the sources file",
    ),
    mutant(
        "D1 a wildcard in a permission name is accepted",
        TOOL,
        '    if not g["name"] or "*" in g["name"] or "?" in g["name"]:\n',
        '    if not g["name"]:\n',
        "test_plant_d1_a_wildcard_in_a_permission_name_is_caught",
        "must be one permission name",
    ),
    mutant(
        "D1 a wildcard resource with no bound is accepted",
        TOOL,
        ' and not g["bound"].strip():\n',
        ' and g["bound"] is None:\n',
        "test_plant_d1_a_wildcard_resource_with_no_bound_is_caught",
        "a blank `bound` on the wildcard resource of the Vault secrets grant is not reported",
    ),
    mutant(
        "D3 an empty reason is accepted",
        TOOL,
        '    if not g["reason"].strip():\n',
        '    if g["reason"] is None:\n',
        "test_plant_d3_an_empty_reason_is_caught",
        "a blank reason on the Kubernetes grant is not reported",
    ),
    mutant(
        "D5 a never action that a kind needs is accepted",
        TOOL,
        '            if n.type == "action" and (policy.platform, n.name) in names:\n',
        '            if n.type == "no such type" and (policy.platform, n.name) in names:\n',
        "test_plant_d5_a_never_action_that_another_kind_needs_is_caught",
        "never-list action",
    ),
    mutant(
        "D6 a long-lived credential with no exception is accepted",
        TOOL,
        '        elif cred["lifetime"] == "long" and not cred["exception"].strip():\n',
        '        elif cred["lifetime"] == "long" and cred["exception"] is None:\n',
        "test_plant_d6_a_long_lived_credential_with_no_exception_is_caught",
        "long-lived credential",
    ),
    mutant(
        "D7 an unknown key is accepted",
        TOOL,
        '    out = [f"{where}: unknown key {k!r}" for k in sorted(set(map(str, raw)) - allowed)]\n',
        "    out = []\n",
        "test_plant_d7_unknown_keys_platform_and_never_type_are_refused",
        "an extra top-level key `deny` of the policy is not reported",
    ),
    mutant(
        "E2 copy-ready text is offered for a kind with an unchecked grant",
        TOOL,
        "        g.verified is not None and not g.claims_unverified for g in policy.grants\n",
        "        g.id is not None for g in policy.grants\n",
        "test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim",
        "copy-ready text is offered",
    ),
    mutant(
        "E5 a value that does not match its grammar is put into the text",
        TOOL,
        '            if not re.fullmatch(grammar, part) or {".", ".."} & set(part.split("/")):\n',
        "            if part is None:\n",
        "test_an_empty_vault_prefix_is_refused_and_the_page_says_so_first",
        "an empty path_prefix is accepted into the text",
    ),
    mutant(
        "M3 a literal getattr of a sink is accepted",
        TEST,
        "            elif node.args[1].value not in shape.getattr_ok:\n",
        "            elif node.args[1].value is None:\n",
        "test_plant_p04b_an_added_request_through_getattr_with_a_literal_name_is_caught",
        "banned `getattr` of `authed`",
    ),
    mutant(
        "M3 a banned name is no longer reported",
        TEST,
        "        if name in BANNED_NAMES:\n",
        "        if name is None:\n",
        "test_plant_attrgetter_on_a_sink_is_caught",
        "banned indirect call `attrgetter`",
    ),
    mutant(
        "M3 a banned name behind an import alias is no longer reported",
        TEST,
        "                if part in BANNED_NAMES:\n",
        "                if part is None:\n",
        "test_plant_a_banned_name_that_arrives_through_an_import_alias_is_caught",
        "(imported)",
    ),
    mutant(
        "M3 an import that is not on the list is accepted",
        TEST,
        "                if entry not in shape.imports:\n",
        "                if entry is None:\n",
        "test_plant_an_import_of_another_http_library_is_caught",
        "is not on this module's import list",
    ),
    mutant(
        "M3 a raw HTTP call outside the sender is accepted",
        TEST,
        "        if name in RAW_HTTP and _name_of(func) not in shape.raw_http:\n",
        "        if name is None and _name_of(func) not in shape.raw_http:\n",
        "test_plant_a_raw_http_request_outside_the_one_sender_is_caught",
        "raw HTTP call",
    ),
    mutant(
        "M3 the opener used outside the sender is accepted",
        TEST,
        "        if node.attr == OPENER and _name_of(func) not in shape.raw_http:\n",
        "        if node.attr is None and _name_of(func) not in shape.raw_http:\n",
        "test_plant_the_http_opener_used_outside_the_one_sender_is_caught",
        "the HTTP opener",
    ),
    mutant(
        "M3 a local name is folded like a setting",
        TEST,
        '                out += "{" + value.value.id + "." + value.attr + "}"\n',
        '                out += "{" + value.attr + "}"\n',
        "test_plant_a_local_variable_named_like_a_setting_is_not_taken_for_the_setting",
        "has no grant",
    ),
    mutant(
        "M3 another module importing the Vault client is accepted",
        TEST,
        "            if names - allowed:\n",
        "            if names is None:\n",
        "test_plant_another_module_importing_the_vault_client_is_caught",
        "from the Vault client module",
    ),
    mutant(
        "M3 a query parameter at the call is accepted",
        TEST,
        "        if not equals or name not in allowed or (_HOLE in value and value != _HOLE):\n",
        "        if not equals:\n",
        "test_plant_p09a_a_kubernetes_request_with_watch_in_its_query_is_caught",
        "may carry",
    ),
    mutant(
        "M3 a query parameter written in the module is accepted",
        TEST,
        "                if name not in allowed:\n",
        "                if name is None:\n",
        "test_plant_p09a_a_kubernetes_request_with_watch_in_its_query_is_caught",
        "is written in the module",
    ),
    mutant(
        "M3 a Kubernetes path that is not the bound one is accepted",
        TEST,
        '        out.append(f"{where}: the path does not fit the one bound to `{operation}`")\n',
        "        out.append(None) if out is None else None\n",
        "test_plant_a_kubernetes_path_that_is_not_the_bound_one_is_caught",
        "the path does not fit",
    ),
    mutant(
        "M2 a Vault grant wider than its request is accepted",
        TEST,
        "        if g.resource != want:\n",
        "        if g.resource is None:\n",
        "test_plant_the_old_star_form_of_the_vault_secrets_grant_is_caught",
        "is not the path of the request",
    ),
    mutant(
        "M3 a Vault capability other than the verb's is accepted",
        TEST,
        "        if g.name != VERB_CAPABILITY.get(verb):\n",
        "        if g.name is None:\n",
        "test_plant_a_vault_capability_that_is_not_the_verbs_own_is_caught",
        "is not the one a POST request needs",
    ),
    mutant(
        "D2 a field that is no setting is accepted",
        TEST,
        "        if name not in settings.model_fields\n",
        "        if name is None\n",
        "test_plant_d2_a_field_that_is_no_setting_is_caught",
        "is not a setting of",
    ),
    mutant(
        "Dated entries: an overdue entry is no longer reported",
        TOOL,
        "        if key in live and today > p.review_by\n",
        "        if key in live and today is None\n",
        "test_plant_an_overdue_entry_says_what_to_do_and_a_date_cannot_be_moved_far",
        "no overdue entry is reported",
    ),
    mutant(
        "B12 an overdue pending kind is reported one day late",
        TOOL,
        "        if key in live and today > p.review_by\n",
        "        if key in live and today.toordinal() > p.review_by.toordinal() + 1\n",
        "test_plant_an_overdue_pending_kind_is_caught",
        "not reported as overdue",
    ),
    mutant(
        "B12 an overdue unchecked claim is reported one day late",
        TOOL,
        "        if key in live and today > p.review_by\n",
        "        if key in live and today.toordinal() > p.review_by.toordinal() + 1\n",
        "test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue",
        "not reported as overdue",
    ),
    mutant(
        "B12 an overdue name or claim of the check command is reported one day late",
        TOOL,
        "        if key in live and today > p.review_by\n",
        "        if key in live and today.toordinal() > p.review_by.toordinal() + 1\n",
        "test_the_check_command_reports_a_name_or_claim_with_no_dated_entry_and_a_stale_or_overdue_entry",
        "the entries due the day after the review day are not each reported once",
    ),
    mutant(
        "Dated entries: a date moved further than the cap is accepted",
        TOOL,
        "        if (p.review_by - p.decided).days > MAX_PENDING_DAYS\n",
        "        if (p.review_by - p.decided).days > 10**6\n",
        "test_plant_an_overdue_entry_says_what_to_do_and_a_date_cannot_be_moved_far",
        "a date may not be moved further",
    ),
    mutant(
        "m7 a control character in a text is accepted",
        TOOL,
        "        if not value.isprintable():\n",
        "        if value is None:\n",
        "test_plant_a_newline_in_a_reason_is_caught",
        "non-printing character",
    ),
    mutant(
        "m6 a key written twice is accepted",
        TOOL,
        "            if twice := sorted({str(k) for k in keys if keys.count(k) > 1}):\n",
        "            if twice := sorted(set()):\n",
        "test_plant_m6_a_key_written_twice_in_the_policy_literal_is_refused",
        "a key written twice in the policy literal is accepted",
    ),
    mutant(
        "m8 a plus wildcard with no bound is accepted",
        TOOL,
        '    wildcards = ("*", "?", "+") if platform == "vault" else ("*", "?")\n',
        '    wildcards = ("*", "?")\n',
        "test_plant_d1_a_plus_wildcard_with_no_bound_is_caught",
        "holds a wildcard",
    ),
    mutant(
        "m9 a placeholder left after filling is put into the text",
        TOOL,
        '    if re.search(r"[{}<>]", filled):\n',
        "    if filled is None:\n",
        "test_plant_m9_a_placeholder_left_after_filling_is_refused",
        "a placeholder left after filling is accepted into the text",
    ),
    mutant(
        "D4 a grant that names no call is accepted",
        TOOL,
        "        or not value\n",
        "        or value is None\n",
        "test_plant_a_grant_that_names_no_call_is_caught_with_its_message",
        "operations must be a non-empty",
    ),
    mutant(
        "Ids: a grant id used by two kinds is accepted",
        TOOL,
        "            if g.id in owner:\n",
        "            if g.id is None:\n",
        "test_plant_a_grant_id_used_by_two_kinds_is_caught",
        "is used by",
    ),
    mutant(
        "E3 a URL in verified is accepted",
        TOOL,
        "        if not _SOURCE_ID.fullmatch(s)\n",
        "        if s is None\n",
        "test_plant_a_url_in_verified_is_caught_with_its_message",
        "is not a source id",
    ),
    mutant(
        "Values: a reserved value is put into the text",
        TOOL,
        "            if why := reserved_problem(key, part):\n",
        "            if why := None:\n",
        "test_plant_the_mount_sys_is_refused",
        "a reserved value (the mount sys) is put into the text",
    ),
    mutant(
        "Values: a value longer than its limit is put into the text",
        TOOL,
        "            if len(part) > MAX_LENGTH[key]:\n",
        "            if len(part) < 0:\n",
        "test_plant_a_300_character_value_is_refused",
        "a value longer than its limit is put into the text",
    ),
    mutant(
        "m10 the command line skips the checks across kinds",
        TOOL,
        "    out += cross_problems(policies) + stray_modules(root)\n",
        "    out += []\n",
        "test_plant_m10_check_reports_each_data_problem_in_one_line_with_exit_code_1",
        "is used by secrets/vault and by",
    ),
    mutant(
        "B3 a never path is reported although its capabilities differ from the grant's",
        TOOL,
        "                if n.capabilities and g.name not in n.capabilities:\n",
        "                if False:\n",
        "test_plant_a_vault_never_path_over_a_grant_is_caught_and_a_capability_that_differs_is_not",
        "that covers no grant is reported",
    ),
    mutant(
        "B3 a Kubernetes never resource that a grant names is no longer reported",
        TOOL,
        "                if (m := _K8S_RESOURCE.fullmatch(g.resource)) and m.group(2) == n.name\n",
        "                if (m := _K8S_RESOURCE.fullmatch(g.resource)) and m.group(2) is None\n",
        "test_plant_a_kubernetes_never_resource_that_a_grant_names_is_caught",
        "that a grant names is not reported",
    ),
    mutant(
        "B3 the check across kinds no longer calls the never-list cover rule",
        TOOL,
        "        out += never_covers_grant_problems(kind, policy)\n",
        "        pass\n",
        "test_plant_the_check_across_kinds_calls_the_cover_rule",
        "does not call the never-list cover rule",
    ),
    mutant(
        "B3 copy-ready text is offered for a kind whose grant has an unchecked claim (only that clause dropped)",
        TOOL,
        "g.verified is not None and not g.claims_unverified for g in policy.grants\n",
        "g.verified is not None for g in policy.grants\n",
        "test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim",
        "copy-ready text is offered",
    ),
    mutant(
        "B3 a builder-only source id is shown without the mark",
        TOOL,
        "            if s in marks.builder_only\n",
        "            if False\n",
        "test_a_builder_only_source_is_marked_wherever_the_page_lists_it",
        "without the mark (builder only)",
    ),
    mutant(
        "B3 a grant with an unchecked claim needs no dated entry",
        TOOL,
        "        for kind, label in sorted(claimed - set(pending))\n",
        "        for kind, label in sorted(set())\n",
        "test_plant_an_unchecked_claim_with_no_pending_entry_is_caught",
        "has an unchecked claim",
    ),
    mutant(
        "B3 a claim note whose text is in no claims_unverified is accepted",
        TOOL,
        "                if not rest or rest[0] not in claims:\n",
        "                if False:\n",
        "test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught",
        "a claim note whose text is in no claims_unverified is not reported",
    ),
    mutant(
        "B3 a note that names an unknown source id is accepted",
        TOOL,
        "                    for s in rest[0]\n                    if s not in known\n",
        "                    for s in rest[0]\n                    if False\n",
        "test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught",
        "a note that names an unknown source id is not reported",
    ),
    mutant(
        "B3 a stale note class is accepted",
        TOOL,
        "        for k in sorted(set(classes) - used)\n",
        "        for k in sorted(set())\n",
        "test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught",
        "a stale class entry is not reported",
    ),
    mutant(
        "B3 an allowlisted call that stops passing its parameter gives no hint where to fix it",
        TEST,
        '                "parameter of that function. What to do: the code at that line changed; move or remove "\n'
        '                "the entry in SHAPES (`wrappers`) of tests/test_policy_guard.py"\n',
        '                "parameter of that function"\n',
        "test_plant_an_allowlisted_line_that_stops_passing_its_parameter_is_caught",
        "move or remove the entry in SHAPES",
    ),
    mutant(
        "B4 the overlap of two paths ignores a literal part against a `+` part",
        TOOL,
        '    return a == b or (b == _NOT_SLASH and a != "/")\n',
        "    return a == b\n",
        "test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught",
        "that the grant R17 covers is not reported once",
    ),
    mutant(
        "B4 the setting `path_prefix` is read as one part only",
        TOOL,
        '    return any(\n        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * k))\n        for k in range(1, most + 1)\n    )\n',
        '    return any(\n        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * k))\n        for k in range(1, 2)\n    )\n',
        "test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught",
        "that the grant R17 covers is not reported once",
    ),
    mutant(
        "B4 a last `*` in a policy path matches nothing",
        TOOL,
        "            edge(cur, _ANY, cur)\n",
        "            pass\n",
        "test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught",
        "that the grant R17 covers is not reported once",
    ),
    mutant(
        "B4 a part of the setting `path_prefix` is not ended by a slash",
        TOOL,
        '        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * k))\n',
        '        _overlap_of_forms(first.replace(_PREFIX, "+" * k), second.replace(_PREFIX, "+" * k))\n',
        "test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught",
        "that the grant R17 covers is not reported once",
    ),
    mutant(
        "B4 a never type that does not fit the platform is accepted",
        TOOL,
        '    elif n["type"] not in NEVER_TYPES_BY_PLATFORM[platform]:\n',
        "    elif False:\n",
        "test_a_never_type_that_does_not_fit_the_platform_is_refused",
        "is not refused",
    ),
    mutant(
        "B4 a reason that says it is unchecked needs no claim",
        TOOL,
        "    if said and not claims:\n",
        "    if False:\n",
        "test_a_free_or_never_reason_that_says_it_is_unchecked_must_list_the_claim",
        "with no claim listed, is not refused",
    ),
    mutant(
        "B4 a note of class sources shows no source ids",
        TOOL,
        '    return f" (sources: {ids})"\n',
        '    return ""\n',
        "test_every_note_with_a_sources_class_shows_its_source_ids_after_the_note_and_in_the_source_list",
        "does not show its source ids",
    ),
    mutant(
        "B4 the page lists no source named only by a note",
        TOOL,
        "        named |= named_source_ids(kind, policy)\n",
        "        pass\n",
        "test_every_note_with_a_sources_class_shows_its_source_ids_after_the_note_and_in_the_source_list",
        "is not in the source list",
    ),
    mutant(
        "B4 a source of which only a passage was read is marked on a row with no claim",
        TOOL,
        "            if claim and s in marks.partly_builder_only\n",
        "            if s in marks.partly_builder_only\n",
        "test_a_source_of_which_only_a_passage_was_read_is_marked_on_a_row_with_a_claim_only",
        "a row with no claim marks a source as partly builder only",
    ),
    mutant(
        "B4 a builder-only id that is no row of the sources file is accepted",
        TOOL,
        '    if unknown := sorted((set(ids["BUILDER-ONLY"]) | set(ids["PARTLY-BUILDER-ONLY"])) - known):\n',
        "    if False:\n",
        "test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line",
        "a builder-only id that is no row of the sources file is accepted",
    ),
    mutant(
        "B4 a second builder-only line in the sources file is accepted",
        TOOL,
        '    rows = [ln for ln in lines if ln.startswith(f"# {tag}:")]\n    if len(rows) != 1:\n',
        '    rows = [ln for ln in lines if ln.startswith(f"# {tag}:")]\n    if len(rows) < 1:\n',
        "test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line",
        "a second builder-only line in the sources file is accepted",
    ),
    mutant(
        "B4 the limit of a dated entry is another number in the tool",
        TOOL,
        "MAX_PENDING_DAYS = 92\n",
        "MAX_PENDING_DAYS = 400\n",
        "test_the_limit_of_a_dated_entry_is_one_number_in_the_tool",
        "not 92 days",
    ),
    mutant(
        "B4 the test file holds its own limit of a dated entry",
        TEST,
        "MAX_PENDING_DAYS = pp.MAX_PENDING_DAYS\n",
        "MAX_PENDING_DAYS = 92\n",
        "test_the_limit_of_a_dated_entry_is_one_number_in_the_tool",
        "holds its own MAX_PENDING_DAYS number",
    ),
    mutant(
        "B4 an unchecked claim of a free request needs no dated entry",
        TOOL,
        "    claimed = {(k, label) for k, label, e in entries(policies) if e.claims_unverified}\n",
        '    claimed = {(k, label) for k, label, e in entries(policies) if e.claims_unverified and not label.startswith("free:")}\n',
        "test_the_pending_claims_of_a_free_and_a_never_entry_are_watched_like_a_grant_claim",
        "the entry free:0 needs no PENDING_CLAIMS entry",
    ),
    mutant(
        "B4 an unchecked claim of a never line needs no dated entry",
        TOOL,
        "    claimed = {(k, label) for k, label, e in entries(policies) if e.claims_unverified}\n",
        '    claimed = {(k, label) for k, label, e in entries(policies) if e.claims_unverified and not label.startswith("never:")}\n',
        "test_the_pending_claims_of_a_free_and_a_never_entry_are_watched_like_a_grant_claim",
        "the entry never:create needs no PENDING_CLAIMS entry",
    ),
    mutant(
        "B4 a free-entry note may name a source its entry does not list",
        TOOL,
        "                        for s in rest[0]\n                        if s not in held\n",
        "                        for s in rest[0]\n                        if False\n",
        "test_a_sources_note_whose_free_entry_does_not_list_the_id_is_caught",
        "is not reported",
    ),
    # ---- fix batch 5 (round 5 review and evidence run)
    mutant(
        "B5 the two marks of a claim are swapped",
        TOOL,
        '    ("CLAIM-READ-BY-BUILDER", MARK_BUILDER_READ),\n    ("CLAIM-READ-BY-NOBODY", MARK_NOBODY_READ),\n',
        '    ("CLAIM-READ-BY-BUILDER", MARK_NOBODY_READ),\n    ("CLAIM-READ-BY-NOBODY", MARK_BUILDER_READ),\n',
        "test_every_claim_has_one_of_two_marks_taken_from_the_head_of_the_sources_file",
        "not exactly the + claim of R17",
    ),
    mutant(
        "B5 a claim that carries two marks is accepted",
        TOOL,
        '    if len(found) != 1:\n        raise PolicyError(\n            f"claim {text[:60]!r}',
        '    if len(found) < 1:\n        raise PolicyError(\n            f"claim {text[:60]!r}',
        "test_a_claim_with_no_mark_two_marks_or_a_stale_text_is_a_problem_and_a_bad_line_is_refused",
        "two marks pass",
    ),
    mutant(
        "B5 a start of a claim that matches no claim is accepted",
        TOOL,
        "        for x in sorted((set(marks.builder_read) | set(marks.nobody_read)) - used)\n",
        "        for x in sorted(set())\n",
        "test_a_claim_with_no_mark_two_marks_or_a_stale_text_is_a_problem_and_a_bad_line_is_refused",
        "a stale text is not reported",
    ),
    mutant(
        "B5 the claims cell shows no mark",
        TOOL,
        '    return f"{claim} ({claim_mark(claim, marks)})"\n',
        "    return claim\n",
        "test_the_page_shows_the_builder_mark_on_the_plus_claim_of_r17_and_the_nobody_mark_on_every_other_claim",
        "the claims cell shows no mark",
    ),
    mutant(
        "B5 a free request with a claim shows its partly read source as a plain checked source",
        TOOL,
        "Checked: {_checked_cell(f.verified, bool(f.claims_unverified), marks)}.",
        "Checked: {_checked_cell(f.verified, False, marks)}.",
        "test_a_free_or_never_row_with_a_claim_marks_its_partly_read_sources",
        "k8s.rules_review",
    ),
    mutant(
        "B5 a never line with a claim shows its partly read source as a plain checked source",
        TOOL,
        "{_checked_cell(n.verified, bool(n.claims_unverified), marks)} | ",
        "{_checked_cell(n.verified, False, marks)} | ",
        "test_a_free_or_never_row_with_a_claim_marks_its_partly_read_sources",
        "| action | `create` |",
    ),
    mutant(
        "B5 a reason is matched by its start, not by its exact text",
        TOOL,
        "        return [k for k in classes if k[0] == kind and k[1] == text]\n",
        "        return [k for k in classes if k[0] == kind and text.startswith(k[1])]\n",
        "test_a_reason_is_matched_by_its_exact_text_even_when_a_class_key_is_its_unique_prefix",
        "is read as the class of that prefix",
    ),
    mutant(
        "B5 a reason needs no class",
        TOOL,
        '    if text.startswith("reason:"):\n        return [k for k in classes',
        "    if False:\n        return [k for k in classes",
        "test_a_free_reason_that_says_it_creates_nothing_or_changes_nothing_has_no_class_and_is_refused",
        "classes in NOTE_CLASSES",
    ),
    mutant(
        "B5 a reason of class pending may sit on an entry that has a source",
        TOOL,
        "                if entry is None or entry.verified is not None:\n",
        "                if entry is None:\n",
        "test_a_grant_or_never_reason_with_no_class_is_refused_and_a_wrong_class_is_caught",
        "a pending class on an entry with a source is not reported",
    ),
    mutant(
        "B5 a reason of class sources may sit on an entry that names no source",
        TOOL,
        "                if not held:\n",
        "                if False:\n",
        "test_a_grant_or_never_reason_with_no_class_is_refused_and_a_wrong_class_is_caught",
        "a sources class on an entry with no source is not reported",
    ),
    mutant(
        "B5 the check command does not run the note and reason rule",
        TOOL,
        "        out += note_problems(policies, NOTE_CLASSES, known)\n",
        "        pass\n",
        "test_a_note_class_with_an_unknown_source_id_is_a_problem_of_the_check_and_the_page_raises_policy_error",
        "the check command does not report",
    ),
    mutant(
        "B5 the check command does not run the claim mark rule",
        TOOL,
        "        out += claim_mark_problems(policies, read_marks(root))\n",
        "        pass\n",
        "test_the_check_command_reports_a_claim_with_no_mark_in_the_sources_file",
        "the check command does not report",
    ),
    mutant(
        "B5 the page raises a KeyError for a source id that is not in the sources file",
        TOOL,
        "    if missing := sorted(named - set(sources)):\n",
        "    if False:\n",
        "test_a_note_class_with_an_unknown_source_id_is_a_problem_of_the_check_and_the_page_raises_policy_error",
        "not PolicyError",
    ),
    mutant(
        "B5 the page head says R17 reads only the one secret it names",
        TOOL,
        "R17 reads\n  every secret directly under the prefix (not only the one secret it names) and may also read",
        "R17 also reads\n  every older version of the one secret it names and may also read",
        "test_the_page_head_and_the_r17_cell_and_reason_state_the_same_hedged_scope",
        "the page head does not say the prefix scope",
    ),
    mutant(
        "B5 the two paths of a prefix check may hold a different number of parts for the one setting",
        TOOL,
        '        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * k))\n',
        '        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * (k + 2)))\n',
        "test_a_never_path_deeper_than_the_prefix_grant_is_not_reported_as_covering_it",
        "{mount}/data/{path_prefix}+/deeper/+",
    ),
    mutant(
        "B5 the mirror branch of the one-character rule lets a not-slash class read a slash",
        TOOL,
        '        return b != "/"\n',
        "        return True\n",
        "test_the_path_overlap_automaton_agrees_with_a_brute_force_search_on_every_small_pattern_pair",
        "differs from the brute-force answer",
    ),
    mutant(
        "B5 the lookahead that keeps `{path_prefix}` out of the one-word replacement is dropped",
        TOOL,
        '        re.sub(r"\\{(?!path_prefix\\})([a-z_]+)\\}", lambda m: m.group(1), resource),\n',
        '        re.sub(r"\\{([a-z_]+)\\}", lambda m: m.group(1), resource),\n',
        "test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught",
        "that the grant R17 covers is not reported once",
    ),
    mutant(
        "B5 a `+` reads exactly one character",
        TOOL,
        "            edge(nxt, _NOT_SLASH, nxt)\n            cur, i = nxt, i + 1\n",
        "            cur, i = nxt, i + 1\n",
        "test_the_path_prefix_setting_is_read_as_one_or_more_parts_each_ending_in_a_slash",
        "a `+` is read as one character",
    ),
    mutant(
        "B5 the two builder-only lists of the sources file head are returned in the wrong order",
        TOOL,
        '    return Marks(\n        ids["BUILDER-ONLY"],\n        ids["PARTLY-BUILDER-ONLY"],\n',
        '    return Marks(\n        ids["PARTLY-BUILDER-ONLY"],\n        ids["BUILDER-ONLY"],\n',
        "test_a_builder_only_source_is_marked_wherever_the_page_lists_it",
        "without the mark (builder only)",
    ),
    # ---- fix batch 6 (round 6 review)
    mutant(
        "B6 an empty claim text in the head of the sources file is accepted",
        TOOL,
        "        if not all(found):\n",
        "        if False:\n",
        "test_a_claim_with_no_mark_two_marks_or_a_stale_text_is_a_problem_and_a_bad_line_is_refused",
        "an empty claim text in the head of the sources file is accepted",
    ),
    mutant(
        "B6 a claim text that holds two semicolons is accepted",
        TOOL,
        '        if any(";;" in x for x in found):\n',
        "        if False:\n",
        "test_a_claim_text_that_ends_in_two_semicolons_or_repeats_is_refused",
        "is not refused",
    ),
    mutant(
        "B6 a claim text under both marks is accepted",
        TOOL,
        "    if both := sorted(set(texts[MARK_BUILDER_READ]) & set(texts[MARK_NOBODY_READ])):\n",
        "    if False:\n",
        "test_a_claim_text_under_both_marks_is_refused",
        "a text under both marks is not reported",
    ),
    mutant(
        "B6 a claim with a clause added is still matched by its start",
        TOOL,
        "if text in marks.texts(m)]\n",
        "if any(text.startswith(x) for x in marks.texts(m))]\n",
        "test_a_clause_appended_to_a_claim_is_no_longer_the_listed_claim",
        "the longer claim still has a mark",
    ),
    mutant(
        "B6 a builder-read mark on a claim of an entry that names no builder-only source is accepted",
        TOOL,
        "        if MARK_BUILDER_READ in got and not cited:\n",
        "        if False:\n",
        "test_the_marks_of_r17_and_r18_swapped_in_the_sources_file_are_reported_by_the_check",
        "a builder-read mark on R18 is not reported",
    ),
    mutant(
        "B6 an entry that names a builder-only source needs no builder-read claim",
        TOOL,
        "        if e.claims_unverified and cited and MARK_BUILDER_READ not in got:\n",
        "        if False:\n",
        "test_the_marks_of_r17_and_r18_swapped_in_the_sources_file_are_reported_by_the_check",
        "R17 with no builder-read claim is not reported",
    ),
    mutant(
        "B6 the byte-order mark is not dropped from the sources file",
        TOOL,
        '    return text.removeprefix("\\ufeff").splitlines()\n',
        "    return text.splitlines()\n",
        "test_a_byte_order_mark_is_read_the_same_by_the_row_the_id_and_the_claim_parsers",
        "is refused somewhere",
    ),
    mutant(
        "B6 the check command does not run the rule for names with no dated entry",
        TOOL,
        "        out += name_pending_problems(policies, PENDING_NAMES, today)\n",
        "        pass\n",
        "test_a_grant_whose_name_is_unchecked_with_no_pending_row_is_reported_by_the_check",
        "a name with no dated entry is not reported",
    ),
    mutant(
        "B6 the check command does not run the rule for claims with no dated entry",
        TOOL,
        "        out += claim_pending_problems(policies, PENDING_CLAIMS, today)\n",
        "        pass\n",
        "test_a_new_unchecked_claim_with_no_pending_row_is_reported_by_the_check",
        "a claim with no dated entry is not reported",
    ),
    mutant(
        "B6 a note class of a shape no rule reads is not reported",
        TOOL,
        "        if why := class_shape_problem(key, cls):\n",
        "        if False:\n",
        "test_a_malformed_note_class_is_one_problem_line_of_the_check_and_no_traceback",
        "the problem line does not name the class shape",
    ),
    mutant(
        "B6 a note class of a malformed key is read by the matching code",
        TOOL,
        "            if not _key_ok(key):\n                continue\n",
        "",
        "test_a_malformed_note_class_key_is_one_problem_line_of_the_check_and_no_traceback",
        "the check raised IndexError",
    ),
    mutant(
        "B6 a kind that could not be read gets a stale class line for each of its notes",
        TOOL,
        "        if k[0]\n        in policies",
        "        if k[0]\n        or True",
        "test_a_kind_whose_module_could_not_be_read_adds_no_stale_class_line",
        "is reported as stale class lines",
    ),
    mutant(
        "B6 the page head says R17 reads every older version flatly",
        TOOL,
        " and may also read every older version of each (not yet checked against the vendor, see the claims cell);",
        " and every older version of each;",
        "test_the_page_head_and_the_r17_cell_and_reason_state_the_same_hedged_scope",
        "does not say the older versions are only possible",
    ),
    mutant(
        "M1 the page claims a run that is not on record",
        TOOL,
        '        return "These tests have not run yet: no run of them is on record."\n',
        '        return "These tests ran."\n',
        "test_the_page_states_its_limits_and_offers_text_for_the_three_kinds",
        "have not run yet",
    ),
    mutant(
        "B7 the page takes its marks from the default root, not from the root it is given",
        TOOL,
        "    marks = read_marks(root)\n    out = [head(marks)]\n",
        "    marks = read_marks(DATA_ROOT)\n    out = [head(marks)]\n",
        "test_the_page_takes_its_marks_from_the_root_it_is_given",
        "the page does not take its marks from the root it is given",
    ),
    mutant(
        "B7 the page head lists the claims of the first mark from the wrong list",
        TOOL,
        '        f"first mark ({len(marks.builder_read)}): {quoted(marks.builder_read)}. The claim texts with the second "\n',
        '        f"first mark ({len(marks.builder_read)}): {quoted(marks.nobody_read)}. The claim texts with the second "\n',
        "test_the_page_head_lists_the_claims_of_each_mark_from_the_sources_file_not_from_prose",
        "the page head does not list the claims of each mark from the lists it is given",
    ),
    mutant(
        "B7 the last id of each id line of the sources file head is dropped",
        TOOL,
        "    return tuple(x.strip() for x in raw.split(separator))\n",
        "    return tuple(x.strip() for x in raw.split(separator)[:-1])\n",
        "test_the_builder_only_marks_are_read_from_the_head_of_the_sources_file_and_match_its_list",
        "'V-ACL', 'V-PARSE'",
    ),
    mutant(
        "B7 the write command writes the page although the dated entries are overdue",
        TOOL,
        "        if bad:\n            pass  # nothing is written or compared while the data breaks a rule\n",
        "        if False:\n            pass\n",
        "test_from_the_review_date_the_write_command_stops_and_writes_nothing",
        "wrote the page although the dated entries are overdue",
    ),
    mutant(
        "B7 the write command judges the data against a fixed day, not the day it is given",
        TOOL,
        "        bad = data_problems(today=today)\n",
        "        bad = data_problems(today=DECIDED if args.write else today)\n",
        "test_from_the_review_date_the_write_command_stops_and_writes_nothing",
        "the write command did not stop on the review date it was given",
    ),
    mutant(
        "B7 the check command judges the data against a fixed day, not the day it is given",
        TOOL,
        "        bad = data_problems(today=today)\n",
        "        bad = data_problems(today=DECIDED if args.check else today)\n",
        "test_from_the_review_date_the_check_command_stops",
        "the check command did not stop on the review date it was given",
    ),
    mutant(
        "B8 the default clock of the data check is a fixed day",
        TOOL,
        "    today = datetime.now(UTC).date() if today is None else today\n",
        "    today = DECIDED if today is None else today\n",
        "test_the_check_command_uses_the_tools_own_clock_when_no_day_is_given",
        "by its own clock (no day given)",
    ),
    mutant(
        "B8 the pending kinds take another decision day than their own literal",
        TEST,
        KINDS_DECIDED_LINE,
        _line_days(KINDS_DECIDED_LINE, 1),
        "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date",
        "the pending kinds do not all stand on the literal day",
    ),
    mutant(
        "B9 the page head states a fixed review date",
        TOOL,
        '        f", or the review date\\n  {day}, whichever comes first",\n',
        f'        ", or the review date\\n  {_REVIEW or pp.DECIDED}, whichever comes first",\n',
        "test_the_page_names_the_review_day_of_the_dated_lists_and_follows_a_renewal",
        "the page head still names the review day from before the renewal",
    ),
    mutant(
        "B9 the review date is the latest of the dated lists, not the earliest",
        TOOL,
        "    return review_day(PENDING_NAMES, PENDING_CLAIMS)\n",
        "    return review_day(PENDING_NAMES, PENDING_CLAIMS, latest=True)\n",
        "test_the_page_names_the_review_day_of_the_dated_lists_and_follows_a_renewal",
        "the page head does not name the earliest review day",
    ),
    mutant(
        "B9 the tool docstring names a day that is in no dated list",
        TOOL,
        "From\n  the day after the earliest `review_by` the dated entries",
        "From\n  the day after 2026-12-12 the dated entries",
        "test_the_tool_docstring_holds_no_literal_date",
        "the tool docstring holds a literal date",
    ),
    mutant(
        "B10 the tool docstring names a day of a dated entry",
        TOOL,
        "From\n  the day after the earliest `review_by` the dated entries",
        "From\n  the day after 2026-12-11 the dated entries",
        "test_the_tool_docstring_holds_no_literal_date",
        "the tool docstring holds a literal date",
    ),
    mutant(
        "B10 the 16 kinds follow the tool's decision day when it moves",
        TEST,
        KINDS_DECIDED_LINE,
        "KINDS_DECIDED = pp.DECIDED\n",
        "test_the_decision_day_of_the_16_kinds_does_not_follow_the_tools_decision_day",
        "the 16 kinds follow the tool's decision day when it moves",
    ),
    mutant(
        "B10 the clock function of the date tests reads the real day",
        TEST,
        "    return pp.datetime.now(pp.UTC).date()\n\n\ndef _names_claims_day",
        "    return datetime.now(UTC).date()\n\n\ndef _names_claims_day",
        "test_the_three_date_tests_read_the_clock_function_and_go_red_after_the_review_day",
        "the date tests do not read the clock function",
    ),
    mutant(
        "B10 the kinds date test reads a day written in the test",
        TEST,
        "    problems = _kinds_problems_today()\n",
        "    problems = kind_problems(all_kinds(), declared, PENDING_KINDS, NO_IDENTITY, date(2026, 11, 12))\n",
        "test_the_clock_readers_of_the_guard_file_include_the_three_date_tests",
        "a date test does not read the clock function",
    ),
    mutant(
        "B10 the names date test reads a day written in the test",
        TEST,
        "    assert _names_problems_today() == []\n",
        "    assert name_problems(_policies(), PENDING_NAMES, set(source_ids()), date(2026, 11, 12)) == []\n",
        "test_the_clock_readers_of_the_guard_file_include_the_three_date_tests",
        "a date test does not read the clock function",
    ),
    mutant(
        "B10 the claims date test reads a day written in the test",
        TEST,
        "    assert _claims_problems_today() == []\n",
        "    assert claim_problems(_policies(), PENDING_CLAIMS, date(2026, 11, 12)) == []\n",
        "test_the_clock_readers_of_the_guard_file_include_the_three_date_tests",
        "a date test does not read the clock function",
    ),
    mutant(
        "B10 the fixed day is honoured without the marker of the mutant run",
        TEST,
        '    if env.get(MUTANT_RUN_VAR) != "1":\n',
        "    if False:\n",
        "test_the_fixed_day_is_honoured_only_with_the_marker_of_the_mutant_run",
        "a day variable without the marker was honoured",
    ),
    mutant(
        "B10 review_date raises when both dated lists are empty",
        TOOL,
        "    if not days:\n        return None\n",
        "    if not days:\n        pass\n",
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "review_date() has no answer with both dated lists empty",
    ),
    mutant(
        "B10 the page keeps a sentence with no date for a dated entry when no day is set",
        TOOL,
        '            "",\n        )\n    return (\n        f", or the review date',
        '            " Each of these has a dated entry in the tests (review by None) that turns the suite red.",\n        )\n    return (\n        f", or the review date',
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the page head keeps the sentence about a dated entry with no date to name",
    ),
    mutant(
        "B10 the page names a day when both dated lists are empty",
        TOOL,
        "    if day is None:\n        return (\n",
        "    if False:\n        return (\n",
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "does not state the OpenBao trigger on its own",
    ),
    mutant(
        "B10 the review date ignores the claims list",
        TOOL,
        "    return review_day(PENDING_NAMES, PENDING_CLAIMS)\n",
        "    return review_day(PENDING_NAMES)\n",
        "test_with_one_dated_list_empty_the_page_names_the_review_day_of_the_other",
        "review_date() ignores the one list that has entries",
    ),
    mutant(
        "B10 --day with no value is an IndexError",
        "tests/policy_mutants.py",
        '        value, width = (rest[i + 1] if i + 1 < len(rest) else ""), 2\n',
        "        value, width = rest[i + 1], 2\n",
        "test_the_runner_refuses_a_day_argument_that_is_missing_or_not_a_day",
        "a --day with no real day",
    ),
    mutant(
        "B10 --day takes a text that is not written YYYY-MM-DD",
        "tests/policy_mutants.py",
        '    if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", value):\n',
        "    if False:\n",
        "test_the_runner_refuses_a_day_argument_that_is_missing_or_not_a_day",
        "a --day with no real day",
    ),
    mutant(
        "B10 the probe day can be the real day",
        "tests/policy_mutants.py",
        "    if day != today:\n        return day\n",
        "    return day\n",
        "test_the_probe_day_is_never_the_real_day_and_is_never_after_the_review_day",
        "the probe day is the real day",
    ),
    mutant(
        "B10 the probe day is the review day itself",
        "tests/policy_mutants.py",
        "    day = max((review or today) - timedelta(days=1), floor)\n",
        "    day = max(review or today, floor)\n",
        "test_the_probe_day_is_never_the_real_day_and_is_never_after_the_review_day",
        "is not before the review day",
    ),
    mutant(
        "B10 the message scan ignores the message of an assert",
        "tests/policy_mutants.py",
        "                texts += _text_of(n.msg)\n",
        "                pass\n",
        "test_the_message_scan_counts_only_assert_messages_match_and_what_texts",
        "the texts the scan counts",
    ),
    mutant(
        "B10 the message scan counts every string of the test",
        "tests/policy_mutants.py",
        "        out[f.name] = texts\n",
        "        out[f.name] = [n.value for n in ast.walk(f) if isinstance(n, ast.Constant) and isinstance(n.value, str)]\n",
        "test_the_message_scan_counts_only_assert_messages_match_and_what_texts",
        "the texts the scan counts",
    ),
    mutant(
        "B10 the message scan ignores the match text of pytest.raises",
        "tests/policy_mutants.py",
        '                    if k.arg == "match":\n',
        "                    if False:\n",
        "test_the_message_scan_counts_only_assert_messages_match_and_what_texts",
        "the texts the scan counts",
    ),
    mutant(
        "B10 the message scan ignores the what text of same()",
        "tests/policy_mutants.py",
        'n.func.id == "same":',
        'n.func.id == "nothing":',
        "test_the_message_scan_counts_only_assert_messages_match_and_what_texts",
        "the texts the scan counts",
    ),
    mutant(
        "B9 the decision day of the names and claims moves",
        TOOL,
        TOOL_DECIDED_LINE,
        _line_days(TOOL_DECIDED_LINE, 1),
        "test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided",
        "the tool's decision day moved without this test",
    ),
    mutant(
        "B9 the 16 kinds take the tool's decision day, not a literal of their own",
        TEST,
        KINDS_DECIDED_LINE,
        "KINDS_DECIDED = pp.DECIDED\n",
        "test_the_kinds_decision_day_is_a_literal_date_call_not_a_name_of_the_tools_date",
        "KINDS_DECIDED is not a literal date(...) call",
    ),
    mutant(
        "B9 a pending kind is more than 92 days from its decision",
        TEST,
        GEMINI_LINE,
        _line_days(GEMINI_LINE, 60),
        "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date",
        "a pending kind is more than 92 days from its decision to its review day",
    ),
    *(
        [
            Mutant(
                "B9 the docs page names another review date than the dated lists",
                "docs/declared-permissions.md",
                _DOCS_TRIGGER,
                _DOCS_TRIGGER_OTHER,
                "in the trigger sentence",
                test_file=TEST,
                only_test="test_the_docs_page_names_the_review_day_of_the_dated_lists_only",
                pinned=PIN + "test_the_docs_page_names_the_review_day_of_the_dated_lists_only",
            )
        ]
        if _REVIEW
        else []
    ),
    mutant(
        "D1 a `?` wildcard with no bound on the Transit grant is accepted",
        TOOL,
        '    wildcards = ("*", "?", "+") if platform == "vault" else ("*", "?")\n',
        '    wildcards = ("*", "+") if platform == "vault" else ("*", "?")\n',
        "test_plant_d1_a_wildcard_resource_with_no_bound_is_caught",
        "a wildcard resource with no bound on the Transit signing grant is not reported",
    ),
    mutant(
        "D3 a blank reason on a never-list line is accepted",
        TOOL,
        '    if not _is_text(n["reason"]) or not n["reason"].strip():\n',
        '    if not _is_text(n["reason"]):\n',
        "test_plant_d3_an_empty_reason_is_caught",
        "an empty reason on a never-list line is not reported",
    ),
    mutant(
        "D7 an unknown never type is no longer named as unknown",
        TOOL,
        '    if n["type"] not in NEVER_TYPES:\n        out.append(f"{where}: unknown never type',
        '    if False:\n        out.append(f"{where}: unknown never type',
        "test_plant_d7_unknown_keys_platform_and_never_type_are_refused",
        "a never-list type outside the list is not reported",
    ),
    mutant(
        "D7 an unknown key on a grant is accepted",
        TOOL,
        "        out += _keys(where, g, _GRANT, _GRANT) or _grant_problems(where, g, platform)\n",
        "        out += _keys(where, g, _GRANT | {'no_wire'}, _GRANT) or _grant_problems(where, g, platform)\n",
        "test_plant_d7_unknown_keys_platform_and_never_type_are_refused",
        "an extra key `no_wire` on a grant is not reported",
    ),
    mutant(
        "B11 the review day takes only the first list",
        TOOL,
        "    days = [p.review_by for pending in lists for p in pending.values()]\n",
        "    days = [p.review_by for pending in lists[:1] for p in pending.values()]\n",
        "test_the_review_day_helper_takes_each_list_from_its_own_entries_and_has_none_for_an_empty_one",
        "the earliest day over two lists",
    ),
    mutant(
        "B11 the review day ignores the latest option",
        TOOL,
        "    return max(days) if latest else min(days)\n",
        "    return min(days)\n",
        "test_the_review_day_helper_takes_each_list_from_its_own_entries_and_has_none_for_an_empty_one",
        "the latest day of a list with two days",
    ),
    mutant(
        "B11 the review day of empty lists is a date and not None",
        TOOL,
        "    if not days:\n        return None\n    return max",
        "    if not days:\n        return date.min\n    return max",
        "test_the_review_day_helper_takes_each_list_from_its_own_entries_and_has_none_for_an_empty_one",
        "the review day of an empty list",
    ),
    mutant(
        "B11 the date test rule accepts an empty list that reports an overdue line",
        TEST,
        '        if any("is overdue" in p for p in helper()):',
        "        if False:",
        "test_the_date_test_rule_finds_an_empty_list_that_reports_and_a_list_that_never_goes_red",
        "an empty list whose helper reports an overdue line was accepted",
    ),
    mutant(
        "B11 the date test rule accepts a list that never goes red",
        TEST,
        '    if not (found and all("is overdue" in p for p in found)):',
        '    if not (all("is overdue" in p for p in found)):',
        "test_the_date_test_rule_finds_an_empty_list_that_reports_and_a_list_that_never_goes_red",
        "a list with an entry whose helper never goes red was accepted",
    ),
    mutant(
        "B11 the date test rule accepts a problem that is not an overdue line",
        TEST,
        '    if not (found and all("is overdue" in p for p in found)):',
        "    if not found:",
        "test_the_date_test_rule_finds_an_empty_list_that_reports_and_a_list_that_never_goes_red",
        "a helper that is quiet on the review day and then reports a problem that is not an overdue line was accepted",
    ),
    mutant(
        "B11 the date test rule accepts a helper that is red on the review day",
        TEST,
        '    if found:\n        return [\n            f"the {name} date test reports a problem on the review day',
        '    if False:\n        return [\n            f"the {name} date test reports a problem on the review day',
        "test_the_date_test_rule_finds_an_empty_list_that_reports_and_a_list_that_never_goes_red",
        "a helper that is red on the review day itself was accepted",
    ),
    mutant(
        "B11 the kinds sentence has no form for one group of days",
        TEST,
        '    if len(groups) == 1:\n        return f"all {shown[0]}"\n',
        "",
        "test_the_kinds_sentence_is_built_for_any_number_of_day_groups",
        "one group of days",
    ),
    mutant(
        "B11 the kinds sentence names no kinds for an empty list",
        TEST,
        '        return "none of them"\n',
        '        return "all 0 of them"\n',
        "test_the_kinds_sentence_is_built_for_any_number_of_day_groups",
        "an empty list",
    ),
    mutant(
        "B11 the kinds sentence drops the middle groups",
        TEST,
        '    return ", ".join(shown[:-1]) + f" and the other',
        '    return shown[0] + f" and the other',
        "test_the_kinds_sentence_is_built_for_any_number_of_day_groups",
        "three groups of days after a renewal of some kinds",
    ),
    mutant(
        "B11 the changelog entry ends at a nested bold bullet",
        TEST,
        '        r"\\n(?:[-*+] |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        '        r"(?:[-*+] |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        "test_the_entry_cut_ends_at_a_top_level_bullet_only",
        "a nested bold bullet ended the entry early",
    ),
    mutant(
        "B11 the changelog entry never ends at the next bullet",
        TEST,
        "    end = start + 1 + stop.start() if stop else len(text)\n",
        "    end = len(text)\n",
        "test_the_entry_cut_ends_at_a_top_level_bullet_only",
        "the entry runs into the next top-level bullet",
    ),
    mutant(
        "B12 the changelog entry ends only at a bold bullet",
        TEST,
        '        r"\\n(?:[-*+] |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        '        r"\\n- \\*\\*", text[start + 1 :]\n',
        "test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file",
        "the entry runs on into a plain bullet",
    ),
    mutant(
        "B12 the changelog entry does not end at a heading",
        TEST,
        '        r"\\n(?:[-*+] |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        '        r"\\n(?:[-*+] |\\d+[.)] |(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        "test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file",
        "the entry runs on into a heading",
    ),
    mutant(
        "B12 the changelog entry does not end at a star bullet",
        TEST,
        '        r"\\n(?:[-*+] |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        '        r"\\n(?:- |\\d+[.)] |#|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))", text[start + 1 :]\n',
        "test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file",
        "the entry runs on into a star bullet",
    ),
    mutant(
        "B12 the changelog entry of the last entry in the file loses its last line",
        TEST,
        "    end = start + 1 + stop.start() if stop else len(text)\n",
        "    end = start + 1 + stop.start() if stop else len(text) - 3\n",
        "test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file",
        "the last entry of the file lost its last line",
    ),
    mutant(
        "B11 the day scan knows only the ISO form",
        TEST,
        'DAY_PATTERN = re.compile("|".join(f"(?:{f})" for f in DAY_FORMS), re.IGNORECASE)',
        'DAY_PATTERN = re.compile("|".join(f"(?:{f})" for f in DAY_FORMS[:1]), re.IGNORECASE)',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "year-month-day with slashes is not found",
    ),
    mutant(
        "B12 the message scan ignores the messages of a helper the killer calls",
        RUN,
        "                out[name] += own[callee]\n",
        "                pass\n",
        "test_the_message_scan_counts_the_messages_of_a_helper_the_killer_calls_and_only_that",
        "the texts the scan counts for a killer that calls a helper",
    ),
    mutant(
        "B12 the runner takes a --day=VALUE before the decision day",
        RUN,
        "    if day < floor:\n",
        '    if day < floor and not rest[i].startswith("--day="):\n',
        "test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day",
        "takes a --day=VALUE before the decision day (",
    ),
    mutant(
        "B12 the runner takes the first --day=VALUE of two",
        RUN,
        '    if len(marks) > 1:\n        raise ArgumentProblem("--day may be given once only")\n',
        '    if len(marks) > 1 and not rest[marks[0]].startswith("--day="):\n        raise ArgumentProblem("--day may be given once only")\n',
        "test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day",
        "takes --day twice (the first written --day=VALUE)",
    ),
    mutant(
        "B12 the runner floor is the tool's decision day, not the latest decision day of the lists",
        RUN,
        "    return max([pp.DECIDED, *(e.decided for entries in lists for e in entries.values())])\n",
        "    return pp.DECIDED\n",
        "test_the_floor_of_a_fixed_day_is_the_latest_decision_day_of_the_lists_and_the_probe_day_keeps_to_it",
        "the floor ignores a kinds list that was renewed alone",
    ),
    mutant(
        "B12 the probe day goes before the latest decision day",
        RUN,
        "    day = max((review or today) - timedelta(days=1), floor)\n",
        "    day = (review or today) - timedelta(days=1)\n",
        "test_the_floor_of_a_fixed_day_is_the_latest_decision_day_of_the_lists_and_the_probe_day_keeps_to_it",
        "the probe day is before the floor",
    ),
    mutant(
        "B12 the --day floor is the tool's decision day only",
        RUN,
        "    floor = decided_floor() if floor is None else floor\n    rest = list(argv)",
        "    floor = pp.DECIDED\n    rest = list(argv)",
        "test_the_floor_of_a_fixed_day_is_the_latest_decision_day_of_the_lists_and_the_probe_day_keeps_to_it",
        "a --day before the kinds decision day was taken",
    ),
    mutant(
        "B12 the word none is not read as an empty list",
        TOOL,
        "    if raw.strip() == EMPTY_MARKER:\n        return ()\n",
        "    if False:\n        return ()\n",
        "test_each_of_the_four_lists_may_be_the_word_none_and_an_empty_line_or_a_mixed_one_is_refused",
        " written as the word none reads as",
    ),
    mutant(
        "B12 the word none mixed with a claim text is accepted",
        TOOL,
        "        if EMPTY_MARKER in found:\n",
        "        if False:\n",
        "test_each_of_the_four_lists_may_be_the_word_none_and_an_empty_line_or_a_mixed_one_is_refused",
        " mixing the word none with a text is accepted",
    ),
    mutant(
        "B12 an empty claim line is accepted",
        TOOL,
        "        if not all(found):\n",
        "        if False:\n",
        "test_each_of_the_four_lists_may_be_the_word_none_and_an_empty_line_or_a_mixed_one_is_refused",
        "with nothing after the colon is accepted",
    ),
    mutant(
        "B12 the page head keeps the unchecked-claims text with no claim listed",
        TOOL,
        "        _WEAK_CLAIMS_BULLET if marks.builder_read or marks.nobody_read else _NO_WEAK_CLAIMS_BULLET\n",
        "        _WEAK_CLAIMS_BULLET if True else _NO_WEAK_CLAIMS_BULLET\n",
        "test_the_page_head_describes_unchecked_claims_only_while_a_claim_mark_is_listed",
        "with no claim listed the head does not say that no claim is waiting",
    ),
    mutant(
        "B12 the page head drops the unchecked-claims text when only one claim list has a text",
        TOOL,
        "        _WEAK_CLAIMS_BULLET if marks.builder_read or marks.nobody_read else _NO_WEAK_CLAIMS_BULLET\n",
        "        _WEAK_CLAIMS_BULLET if marks.builder_read else _NO_WEAK_CLAIMS_BULLET\n",
        "test_the_page_head_describes_unchecked_claims_only_while_a_claim_mark_is_listed",
        "the head drops the description of unchecked claims",
    ),
    mutant(
        "B12 the overdue message does not list what a renewal touches",
        TOOL,
        '        f"{steps}"\n',
        '        ""\n',
        "test_the_overdue_message_says_renew_all_or_none_and_lists_everything_a_renewal_or_an_emptying_touches",
        "the overdue message does not print the list of what a renewal touches",
    ),
    mutant(
        "B12 the overdue message does not say renew all or none",
        TOOL,
        '. {rule} "',
        '. "',
        "test_the_overdue_message_says_renew_all_or_none_and_lists_everything_a_renewal_or_an_emptying_touches",
        "the overdue message does not say to renew all or none",
    ),
    mutant(
        "B12 the renewal list does not name the page head sentences",
        TOOL,
        '"in `_HEAD` of this tool."',
        '"in the page head."',
        "test_the_overdue_message_says_renew_all_or_none_and_lists_everything_a_renewal_or_an_emptying_touches",
        "the renewal list does not name",
    ),
    mutant(
        "B12 the docs page body for an empty end state accepts a day",
        TEST,
        '    assert "no review date applies now" in docs and "whichever comes first" not in docs, (\n',
        '    assert "no review date applies now" in docs and "whichever comes first" in docs, (\n',
        "test_the_date_tests_branches_for_an_empty_list_run_in_the_end_state",
        "the docs page does not say that no review date applies",
    ),
    mutant(
        "B12 a renewal of only some entries leaves no entry named",
        TEST,
        "        if p.decided != decided\n",
        "        if False\n",
        "test_plant_a_renewal_of_only_some_entries_names_the_entry_that_was_not_renewed",
        "the entries left behind when only one name was renewed",
    ),
    mutant(
        "B12 notes check does not follow a from-import of a test module",
        NTOOL,
        "                out.update({a.asname or a.name: (stem, a.name) for a in n.names})\n",
        "                pass\n",
        "test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it",
        "by a test through a from-import was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not follow a module import",
        NTOOL,
        '        sub = self._file_of(\n            f"{stem}/{taken}"\n        )  # `from tests import taken`: taken is the module tests/taken.py\n        return self.module(sub) if sub else None, attr\n',
        "        return None, attr\n",
        "test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it",
        "by a test through a module import was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not follow an import as",
        NTOOL,
        "                    out[a.asname or a.name] = (stem, None)\n",
        "                    pass\n",
        "test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it",
        "by a test through an import as was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not follow a relative import",
        NTOOL,
        '    if level:\n        here = rel.split("/")[:-1]\n',
        '    if False:\n        here = rel.split("/")[:-1]\n',
        "test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it",
        "by a test through a relative import was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not read an import inside a function",
        NTOOL,
        "    for n in ast.walk(tree):\n        if isinstance(n, ast.ImportFrom):",
        '    for n in getattr(tree, "body", []):\n        if isinstance(n, ast.ImportFrom):',
        "test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it",
        "by a test through an import inside the test was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not list the tests of a changed module-level import",
        NTOOL,
        "            elif isinstance(n, (ast.Import, ast.ImportFrom)):\n                names = [_bound(a) for a in n.names]\n",
        "            elif isinstance(n, (ast.Import, ast.ImportFrom)):\n                continue\n",
        "test_a_changed_module_level_import_or_augmented_assignment_lists_the_tests_that_use_the_name",
        "a changed module-level import did not list the test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not see a changed augmented assignment",
        NTOOL,
        "            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):\n",
        "            elif isinstance(n, (ast.AnnAssign,)) and _is_declaration(n):\n",
        "test_a_changed_module_level_import_or_augmented_assignment_lists_the_tests_that_use_the_name",
        "a changed `+=` of a module-level name did not list the test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not apply an autouse fixture to every test",
        NTOOL,
        "    todo += [(mod, a) for a in mod.autouse]\n",
        "    todo += []\n",
        "test_an_autouse_fixture_that_changed_lists_every_test_of_the_file_and_another_fixture_does_not",
        "a changed autouse fixture did not list every test of the file",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check finds a marker inside another word",
        NTOOL,
        'r"\\b(?:killing mutants?|fails? on|fail-before|fails? before|plants?|controls?)\\b"',
        'r"(?:killing mutants?|fails? on|fail-before|fails? before|plants?|controls?)"',
        "test_a_marker_is_a_whole_word_and_something_to_look_up_follows_it",
        "a marker found inside another word was accepted",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check takes passes on as a reason",
        NTOOL,
        "|fails? before|plants?|controls?)\\b",
        "|fails? before|plants?|controls?|passes on)\\b",
        "test_a_marker_is_a_whole_word_and_something_to_look_up_follows_it",
        "the phrase `passes on` alone was accepted as a reason",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check needs nothing to look up after the marker",
        NTOOL,
        "    if not _IDENTIFIER.search(reason[found.end() :]):\n",
        "    if False:\n",
        "test_a_marker_is_a_whole_word_and_something_to_look_up_follows_it",
        "a reason with no mutant code, test name, file name or commit id after the marker was accepted",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check counts an identifier before the marker",
        NTOOL,
        "    if not _IDENTIFIER.search(reason[found.end() :]):\n",
        "    if not _IDENTIFIER.search(reason):\n",
        "test_a_marker_is_a_whole_word_and_something_to_look_up_follows_it",
        "an identifier before the marker was counted as one after it",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not report a fall in the mutant count",
        NTOOL,
        "    if counts is not None and counts[1] < counts[0]:\n",
        "    if False:\n",
        "test_a_new_altered_or_removed_mutant_and_a_fall_in_the_count_are_seen_in_the_mutant_files",
        "a fall in the mutant count was not reported",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not read a mutant name that holds a backtick",
        NTOOL,
        '            found is None and word == "mutant"\n',
        "            False\n",
        "test_two_mutant_names_that_hold_the_same_backticked_word_each_need_their_own_row",
        "written in one cell were not both found",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not see a change of the mutant builder",
        NTOOL,
        '    return {k: v + "|" + builder for k, v in out.items()}\n',
        "    return out\n",
        "test_a_new_altered_or_removed_mutant_and_a_fall_in_the_count_are_seen_in_the_mutant_files",
        "a change of the mutant builder did not list every mutant",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not read the mutant files",
        NTOOL,
        '_MUTANT_FILE = re.compile(r"tests/(?:policy_mutants|stage_mutants)\\.py")',
        '_MUTANT_FILE = re.compile(r"tests/no_such_file\\.py")',
        "test_a_new_altered_or_removed_mutant_and_a_fall_in_the_count_are_seen_in_the_mutant_files",
        "an altered mutant was not listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not read a conftest",
        NTOOL,
        '_CONFTEST = re.compile(\n    r"(?:tests/(?:.+/)?)?conftest\\.py"\n)',
        '_CONFTEST = re.compile(\n    r"tests/no_such_file\\.py"\n)',
        "test_a_conftest_function_and_a_fixture_file_are_units_and_a_file_outside_the_kinds_is_none",
        "a changed conftest function was not the only unit",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not read the fixture file",
        NTOOL,
        '_FIXTURE_FILE = re.compile(r"tests/fixtures/policy_sources_[^/]*\\.txt")',
        '_FIXTURE_FILE = re.compile(r"tests/fixtures/no_such_file\\.txt")',
        "test_a_conftest_function_and_a_fixture_file_are_units_and_a_file_outside_the_kinds_is_none",
        "a changed fixture file was not of the fixture kind",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check uses the base instead of the merge base",
        NTOOL,
        "    mb, head_sha = merged.stdout.strip(), sha.stdout.strip()\n",
        "    mb, head_sha = base, sha.stdout.strip()\n",
        "test_auto_diffs_from_the_merge_base_to_the_head_commit_and_reads_blobs_not_the_working_folder",
        "the merge base is",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check lets git hide a renamed file",
        NTOOL,
        '"diff", "--name-only", "--no-renames", "-z"',
        '"diff", "--name-only", "-z"',
        "test_auto_lists_both_names_of_a_renamed_test_file_so_the_old_tests_are_not_lost",
        "a renamed test file lists",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check reads a failed diff as no change",
        NTOOL,
        "    if diff.returncode != 0:\n",
        "    if False:\n",
        "test_auto_reads_a_failed_diff_or_a_missing_common_ancestor_as_a_problem_never_as_no_change",
        "a failed diff was read as a result",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check does not say a common ancestor is missing",
        NTOOL,
        "    if sha.returncode != 0 or merged.returncode != 0 or not merged.stdout.strip():\n",
        "    if False:\n",
        "test_auto_reads_a_failed_diff_or_a_missing_common_ancestor_as_a_problem_never_as_no_change",
        "no common ancestor was not one problem naming the full fetch",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 notes check reads the working folder instead of the head commit",
        NTOOL,
        '            if head is not None:\n                cache["new", rel] = _show(head, rel)\n',
        '            if False:\n                cache["new", rel] = _show(head, rel)\n',
        "test_auto_diffs_from_the_merge_base_to_the_head_commit_and_reads_blobs_not_the_working_folder",
        "the check read the working folder, not the blobs of the head commit",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B12 the day scan is case-sensitive",
        TEST,
        'DAY_PATTERN = re.compile("|".join(f"(?:{f})" for f in DAY_FORMS), re.IGNORECASE)',
        'DAY_PATTERN = re.compile("|".join(f"(?:{f})" for f in DAY_FORMS))',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "written in capital letters is not found",
    ),
    mutant(
        "B12 the day scan takes any word that starts like a month",
        TEST,
        '_MONTH_NAMES = "January|Jan|February|Feb|March|Mar|April|Apr|(?-i:May|MAY)|June|Jun|July|Jul|August|Aug|September|Sept|Sep|October|Oct|November|Nov|December|Dec"',
        '_MONTH_NAMES = "Jan[a-z]*|Feb[a-z]*|Mar[a-z]*|Apr[a-z]*|May[a-z]*|Jun[a-z]*|Jul[a-z]*|Aug[a-z]*|Sep[a-z]*|Oct[a-z]*|Nov[a-z]*|Dec[a-z]*"',
        "test_a_word_that_only_starts_like_a_month_is_not_a_day",
        "only starts like a month was found as a written day",
    ),
    mutant(
        "B12 the day scan does not know the year written with dots first",
        TEST,
        '    r"(?<!\\d)\\d{4}\\.\\d{2}\\.\\d{2}(?!\\d)",  # 2026.12.12\n',
        '    r"(?!)",\n',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "year-month-day with dots is not found",
    ),
    mutant(
        "B12 the day scan does not know a day written with numbers and the year last",
        TEST,
        '    r"(?<!\\d)\\d{1,2}[/.-]\\d{1,2}[/.-]\\d{4}(?!\\d)",  # 12/12/2026, 12.12.2026, 12-12-2026\n',
        '    r"(?!)",\n',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "day-month-year with slashes is not found",
    ),
    mutant(
        "B12 the day scan does not know a day written with hyphens and a month name",
        TEST,
        '    r"(?<!\\d)\\d{1,2}-" + _MONTHS + r"-\\d{4}(?!\\d)",  # 12-Dec-2026\n',
        '    r"(?!)",\n',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "with hyphens and a month name is not found",
    ),
    mutant(
        "B12 the day scan does not know a day written day first with a month name",
        TEST,
        '    r"(?<!\\d)\\d{1,2}(?:st|nd|rd|th)?(?: of)? "\n    + _MONTHS\n    + r"(?: \\d{4})?",  # 12 December, 12th of December, 12 Dec 2026\n',
        '    r"(?!)",\n',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "day first with a month name and a year is not found",
    ),
    mutant(
        "B12 the day scan does not know a day written month first",
        TEST,
        '    _MONTHS\n    + r" \\d{1,2}(?!\\d)(?:st|nd|rd|th)?\\b(?:,? \\d{4})?",  # Dec 12, Dec. 12, December 12th, December 12, 2026\n',
        '    r"(?!)",\n',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "month first is not found",
    ),
    mutant(
        "B12 the day scan does not know a day written day first with no year",
        TEST,
        '    + r"(?: \\d{4})?",  # 12 December',
        '    + r" \\d{4}",  # 12 December',
        "test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form",
        "day first with a month name and no year is not found",
    ),
    mutant(
        "B11 the page head names a day with both dated lists empty (OpenBao sentence)",
        TOOL,
        '"; no review date applies now, because no dated entry is waiting for a check",',
        '"; no review date applies now, because no dated entry is waiting for a check (2026-12-11)",',
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the page head names a day with both dated lists empty",
    ),
    mutant(
        "B11 the page head names a day outside the review sentences",
        TOOL,
        "in the Kubernetes source).REVIEW_ENTRY The lists",
        "in the Kubernetes source, checked 2026-11-11).REVIEW_ENTRY The lists",
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the page head names a day with both dated lists empty",
    ),
    mutant(
        "B11 the runner reads the --day=VALUE form no more",
        RUN,
        'marks = [i for i, w in enumerate(rest) if w == "--day" or w.startswith("--day=")]',
        'marks = [i for i, w in enumerate(rest) if w == "--day"]',
        "test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day",
        "the --day=VALUE form",
    ),
    mutant(
        "B11 the runner takes --day twice",
        RUN,
        '    if len(marks) > 1:\n        raise ArgumentProblem("--day may be given once only")\n',
        "",
        "test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day",
        "takes --day twice (the second written --day=VALUE)",
    ),
    mutant(
        "B11 the runner takes a day before the decision day",
        RUN,
        "    if day < floor:",
        "    if False:",
        "test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day",
        "takes a --day before the decision day (",
    ),
    mutant(
        "B11 the runner lets the last failure borrow the text of the summary",
        RUN,
        '    body = stdout.split("short test summary info")[0]',
        "    body = stdout",
        "test_the_runner_reads_the_failures_the_overdue_text_and_the_error_lines_of_a_pytest_run",
        "the last test must not borrow the text of the summary",
    ),
    mutant(
        "B11 the runner does not count ERROR lines",
        RUN,
        '    errors = len(re.findall(r"^ERROR ", stdout, flags=re.MULTILINE))',
        "    errors = 0",
        "test_the_runner_reads_the_failures_the_overdue_text_and_the_error_lines_of_a_pytest_run",
        "the number of ERROR lines of the run",
    ),
    mutant(
        "B11 the runner counts a failure with no overdue text as overdue",
        RUN,
        '    not_overdue = {t for t in failed if "is overdue" not in sections.get(t, "")}',
        "    not_overdue = set()",
        "test_the_runner_reads_the_failures_the_overdue_text_and_the_error_lines_of_a_pytest_run",
        "the failed tests with no overdue text",
    ),
    mutant(
        "B11 the runner expects red for an empty list",
        RUN,
        "for t, entries in zip(DATE_TESTS, lists, strict=True) if entries}",
        "for t, entries in zip(DATE_TESTS, lists, strict=True)}",
        "test_the_runner_expects_red_only_for_lists_with_entries_and_exits_1_for_a_weak_mutant",
        "the date tests that must be red when the names list is empty",
    ),
    mutant(
        "B11 the runner exits 0 with a weak mutant",
        RUN,
        "    return 1 if bad or weak else 0",
        "    return 1 if bad else 0",
        "test_the_runner_expects_red_only_for_lists_with_entries_and_exits_1_for_a_weak_mutant",
        "the exit code with a weak mutant",
    ),
    mutant(
        "B11 notes check reads the test id from any cell",
        NTOOL,
        're.findall(r"`([^`]+)`", cells[1]), cells[-1], cells[1], folder',
        're.findall(r"`([^`]+)`", " ".join(cells[1:])), cells[-1], cells[1], folder',
        "test_a_name_in_another_rows_reason_cell_or_another_cell_is_no_row_of_its_own",
        "an id found in another cell counted as a row",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check ignores the file cell of a row",
        NTOOL,
        "    if rel == file_cell:\n        return True\n",
        "    return True\n    if rel == file_cell:\n        return True\n",
        "test_the_same_test_name_in_two_files_needs_a_row_for_each_file",
        "a row of another file covered a test of this file",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check matches a file name that only ends alike",
        NTOOL,
        '    if not rel.endswith("/" + file_cell):\n',
        "    if not rel.endswith(file_cell):\n",
        "test_the_same_test_name_in_two_files_needs_a_row_for_each_file",
        "a file name that only ends alike",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not read async tests",
        NTOOL,
        "_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)",
        "_FUNCS = (ast.FunctionDef,)",
        "test_an_async_test_and_a_class_method_are_read_and_named_by_their_class",
        "async or method tests not read",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not read class methods",
        NTOOL,
        "        elif isinstance(n, ast.ClassDef) and _is_test_class(n):",
        "        elif False:",
        "test_an_async_test_and_a_class_method_are_read_and_named_by_their_class",
        "async or method tests not read",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not follow a helper to the next helper",
        NTOOL,
        "                todo += [(m, u) for u in m.children_of(name)]\n",
        "                todo += []\n",
        "test_a_changed_helper_constant_or_fixture_lists_each_test_that_uses_it_and_only_those",
        "a change of a helper two steps away lists",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not count a fixture parameter as a use",
        NTOOL,
        "    if isinstance(node, _FUNCS):\n        args = node.args",
        "    if False:\n        args = node.args",
        "test_a_changed_helper_constant_or_fixture_lists_each_test_that_uses_it_and_only_those",
        "a change of a fixture lists",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not see a changed constant",
        NTOOL,
        "            elif isinstance(n, ast.Assign) and _is_declaration(n):",
        "            elif False:",
        "test_a_changed_helper_constant_or_fixture_lists_each_test_that_uses_it_and_only_those",
        "a change of a constant lists",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check accepts a reason of fewer than four words",
        NTOOL,
        " or len(reason.split()) < MIN_WORDS:",
        ":",
        "test_a_reason_must_be_real_not_just_long",
        "a three-word reason was accepted",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check accepts a reason that names no mutant, run, plant or control",
        NTOOL,
        "    found = _MARKER.search(reason)\n",
        '    found = re.search("", reason)\n',
        "test_a_reason_must_be_real_not_just_long",
        "a long reason that names no mutant, run, plant or control was accepted",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not refuse a base that does not resolve",
        NTOOL,
        '    if not base_resolves(base):\n        return [f"the base commit',
        '    if False:\n        return [f"the base commit',
        "test_a_base_that_does_not_resolve_is_one_problem_and_an_option_is_no_base",
        "a base that does not exist was not refused as one problem",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not report a test that is gone",
        NTOOL,
        "        for n in gone\n    ]",
        "        for n in []\n    ]",
        "test_a_test_that_is_gone_is_a_problem_even_with_a_line",
        "a deleted test is not reported as a problem",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check with --auto finds no notes file",
        NTOOL,
        "        sorted(n for n in names if _NOTES_FILE.fullmatch(n) and _show(head_sha, n)),\n",
        "        [],\n",
        "test_auto_reads_the_changed_test_and_notes_files_and_says_when_there_are_no_notes",
        "a change with all its rows failed",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check with --auto misses a test file in a subfolder",
        NTOOL,
        '    r"tests/(?:.+/)?(?:test_[^/]*|[^/]*_test)\\.py"\n',
        '    r"tests/(?:test_[^/]*|[^/]*_test)\\.py"\n',
        "test_auto_reads_the_changed_test_and_notes_files_and_says_when_there_are_no_notes",
        "the changed test files of the change",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not say a change has no builder notes file",
        NTOOL,
        "        if bad and not notes_files:\n",
        "        if False:\n",
        "test_auto_reads_the_changed_test_and_notes_files_and_says_when_there_are_no_notes",
        "the missing notes were not said",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B12 notes check lets two mutants that hold the same backticked word share one row",
        NTOOL,
        "            for name in (*names, cell):\n",
        "            for name in (*names,):\n",
        "test_two_mutant_names_that_hold_the_same_backticked_word_each_need_their_own_row",
        "with the same backticked word were refused",
        test_file="tests/test_notes_lines_check.py",
    ),
    mutant(
        "B11 notes check does not say a change has no test file",
        NTOOL,
        '        if not files and not any(n.startswith("tests/") for n in names):\n',
        "        if False:\n",
        "test_auto_says_nothing_to_check_when_no_test_file_changed",
        "the empty change was not said",
        test_file="tests/test_notes_lines_check.py",
    ),
    # ---------------------------------------------------------------- batch 13
    mutant(
        "B13 notes check reads only the changed test files, not the tests that import a changed helper",
        NTOOL,
        '        files = sorted({*files, *(n for n in _tree(head_sha) if kind_of(n) == "test")})\n',
        "        files = sorted(files)\n",
        "test_a_change_to_a_helper_file_alone_lists_the_tests_of_the_files_that_import_it",
        "a change that touches only helper files under tests/ passed as nothing to check",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check keys a plain import of a tests module by its first part only",
        NTOOL,
        "                    out[a.asname or a.name] = (stem, None)\n",
        '                    out[a.asname or a.name.split(".")[0]] = (stem, None)\n',
        "test_a_plain_import_of_a_tests_module_is_followed_through_its_dotted_chain",
        "plain import",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check leaves module-level code out of every test of the file",
        NTOOL,
        "        self.glue = [n for n in self.tree.body if not _is_declaration(n)]\n",
        "        self.glue = []\n",
        "test_a_module_level_mark_a_class_mark_and_module_level_code_list_every_test_of_the_file",
        "module-level code that skips the file lists no test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check leaves a module-level pytestmark out of every test of the file",
        NTOOL,
        '            "pytestmark" in mod.dumps\n',
        '            "pytestmark" in mod.dumps and False\n',
        "test_a_module_level_mark_a_class_mark_and_module_level_code_list_every_test_of_the_file",
        "a changed module-level pytestmark lists",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check leaves the decorators and body of a test class out of its methods",
        NTOOL,
        "    return (*cls.decorator_list, *cls.bases, *plain, *always, *reached)\n",
        "    return (*cls.bases, *plain, *always, *reached)\n",
        "test_a_module_level_mark_a_class_mark_and_module_level_code_list_every_test_of_the_file",
        "a class decorator that skips the class lists no method",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check leaves the body statements of a test class out of its methods",
        NTOOL,
        "    return (*cls.decorator_list, *cls.bases, *plain, *always, *reached)\n",
        "    return (*cls.decorator_list, *cls.bases, *always, *reached)\n",
        "test_a_module_level_mark_a_class_mark_and_module_level_code_list_every_test_of_the_file",
        "a class-level pytestmark lists no method",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check does not make a conftest assignment a unit",
        NTOOL,
        "        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):\n",
        "        if False:\n",
        "test_a_conftest_assignment_is_a_unit_with_all_assignments_of_its_name",
        "a changed collect_ignore of a conftest is not a unit",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check takes only the first assignment of a conftest name",
        NTOOL,
        "                        and name in _assigned_names(g)\n",
        "                        and g is n\n",
        "test_a_conftest_assignment_is_a_unit_with_all_assignments_of_its_name",
        "an added `+=` of a conftest name is not part of the unit",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 notes check lets a bare file name serve a file whose name another path also has",
        NTOOL,
        '    return not any(k != rel and k.rsplit("/", 1)[-1] == file_cell for k in known)\n',
        "    return True\n",
        "test_a_bare_file_name_in_a_row_serves_only_a_file_whose_name_no_other_path_has",
        "a bare file name in a row served",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the kinds pin accepts a kind moved to another day",
        CH,
        "    if sorted((n, (d + timedelta(days=1)).isoformat()) for d, n in groups) != sorted(KINDS_GROUPS):\n",
        "    if False:\n",
        "test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it",
        "a kind moved to another day was accepted by the kinds pin",
    ),
    mutant(
        "B13 the kinds pin accepts another built sentence",
        CH,
        "    if built != KINDS_LITERAL:\n",
        "    if False:\n",
        "test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it",
        "a built sentence with another day was accepted by the kinds pin",
    ),
    mutant(
        "B13 the kinds pin accepts a changelog entry without the sentence",
        CH,
        "    if KINDS_LITERAL not in entry:\n",
        "    if False:\n",
        "test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it",
        "an entry without the sentence was accepted by the kinds pin",
    ),
    mutant(
        "B13 the overdue message of a kind carries the steps of the names and claims",
        TEST,
        "        steps=pp.KINDS_RENEWAL_STEPS,\n",
        "        steps=pp.RENEWAL_STEPS,\n",
        "test_the_overdue_message_of_the_kinds_has_its_own_rule_and_steps_and_names_only_things_that_exist",
        "does not carry the rule and the steps of the kinds list",
    ),
    mutant(
        "B13 the overdue message of a kind carries the rule of the names and claims",
        TEST,
        "        rule=pp.KINDS_RENEWAL_RULE,\n",
        "        rule=pp.RENEWAL_RULE,\n",
        "test_the_overdue_message_of_the_kinds_has_its_own_rule_and_steps_and_names_only_things_that_exist",
        "does not carry the rule and the steps of the kinds list",
    ),
    mutant(
        "B13 the renewal steps do not send a person to the mutant file",
        TOOL,
        'so nothing is edited there: run "\n    "`python tests/policy_mutants.py` and again with `--day` ',
        'so nothing is edited there: run "\n    "the mutants and again with `--day` ',
        "test_the_overdue_message_of_the_kinds_has_its_own_rule_and_steps_and_names_only_things_that_exist",
        "the renewal steps of the names and claims do not name the mutant file",
    ),
    mutant(
        "B13 a mutant row is found by a part of a cell, not by the whole cell or an exact item",
        NTOOL,
        '    return same(cell) or any(same(i) for i in cell.split(";"))\n',
        "    return name in cell\n",
        "test_a_mutant_row_serves_only_the_mutant_whose_whole_cell_or_exact_item_it_is",
        "borrowed the row of a longer name by substring",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 a reason that names a mutant that does not exist is accepted",
        NTOOL,
        "        if _looks_like_a_mutant_name(token, leads) and token not in refs.mutants:\n",
        "        if False:\n",
        "test_a_reason_must_point_at_a_test_a_log_file_and_a_mutant_that_exist",
        "a mutant, a test and a log file that do not exist were not each reported",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 a reason that names a test that does not exist is accepted",
        NTOOL,
        "        if name not in refs.tests:\n",
        "        if False:\n",
        "test_a_reason_must_point_at_a_test_a_log_file_and_a_mutant_that_exist",
        "a mutant, a test and a log file that do not exist were not each reported",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 a reason that names a log file that does not exist is accepted",
        NTOOL,
        "        if not here:\n",
        "        if False:\n",
        "test_a_reason_must_point_at_a_test_a_log_file_and_a_mutant_that_exist",
        "a mutant, a test and a log file that do not exist were not each reported",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the references of a reason are not looked up when the reason has the right form",
        NTOOL,
        "        elif refs is not None:\n",
        "        elif False:\n",
        "test_a_reason_must_point_at_a_test_a_log_file_and_a_mutant_that_exist",
        "a row naming a test that is in no test file passed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the references of a tree take every file as a log",
        NTOOL,
        '    logs = {rel for rel in tree if "/logs/" in rel}\n',
        "    logs = {rel for rel in tree if True}\n",
        "test_the_refs_of_a_tree_are_its_tests_its_mutant_names_and_the_files_of_its_logs_folders",
        "the logs of the tree are",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the references of a tree hold no mutant name",
        NTOOL,
        "            mutants.update(units[rel])\n",
        "            pass\n",
        "test_the_refs_of_a_tree_are_its_tests_its_mutant_names_and_the_files_of_its_logs_folders",
        "the mutants of the tree are",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the references of a tree leave out the names of the test files",
        NTOOL,
        '            tests.add(rel.rsplit("/", 1)[-1].removesuffix(".py"))\n',
        "            pass\n",
        "test_the_refs_of_a_tree_are_its_tests_its_mutant_names_and_the_files_of_its_logs_folders",
        "the names of its test files",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the check does not build the references of the tree",
        NTOOL,
        "    refs = _refs(tree, new_load) if cross else None\n",
        "    refs = None\n",
        "test_auto_refuses_a_row_whose_reason_names_a_test_or_a_log_file_that_is_in_no_file_of_the_commit",
        "passed `--auto`",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the automatic check does not ask for the references",
        NTOOL,
        "        bad = check(mb, notes, files, head_sha, cross=True)\n",
        "        bad = check(mb, notes, files, head_sha, cross=False)\n",
        "test_auto_refuses_a_row_whose_reason_names_a_test_or_a_log_file_that_is_in_no_file_of_the_commit",
        "passed `--auto`",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B13 the end state checks the page with a source id that is in no sources file",
        TEST,
        '    "V-POL"  # a real source id',
        '    "V-NOPE"  # a real source id',
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the REAL rules refuse the end state",
    ),
    mutant(
        "B13 the scan for a written day does not read a date call",
        TEST,
        '        if name in ("date", "datetime"):\n',
        "        if False:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day of the window was not found",
    ),
    mutant(
        "B13 the scan for a written day does not read an ISO text for fromisoformat",
        TEST,
        '        elif name == "fromisoformat" and len(call.args) == 1:\n',
        "        elif False:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day with a time written as an ISO text for `fromisoformat` was not found",
    ),
    mutant(
        "B13 the scan for a written day flags the decision day itself",
        TEST,
        "        if day is not None and (rel, fn) not in pins:\n",
        "        if day is not None and day != DECIDED and (rel, fn) not in pins:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a pin that is not named was accepted",
    ),
    mutant(
        "B13 the scan for a written day has no end of the window",
        TEST,
        "        if day is not None and (rel, fn) not in pins:\n",
        "        if day is not None and day <= DECIDED + timedelta(days=60) and (rel, fn) not in pins:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day far outside the window was not found",
    ),
    mutant(
        "B14 the scan for a written day only sees a day after the decision day",
        TEST,
        "        if day is not None and (rel, fn) not in pins:\n",
        "        if day is not None and day > DECIDED and (rel, fn) not in pins:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day before the decision day was not found",
    ),
    mutant(
        "B14 the scan for a written day accepts every function as a pin",
        TEST,
        "        if day is not None and (rel, fn) not in pins:\n",
        "        if day is not None:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a named pin was flagged",
    ),
    mutant(
        "B14 the scan for a written day does not read the keywords of a date call",
        TEST,
        "        named = {k.arg: _constant_int(k.value) for k in call.keywords if k.arg}\n",
        "        named = {}\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day written with keywords was not found",
    ),
    mutant(
        "B14 the scan for a written day does not read a sum of constants",
        TEST,
        "    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):\n",
        "    if False:\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day written as a sum of constants was not found",
    ),
    mutant(
        "B14 the scan for a written day does not read a datetime",
        TEST,
        '        if name in ("date", "datetime"):\n',
        '        if name == "date":\n',
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a datetime written with constants was not found",
    ),
    mutant(
        "B14 the scan for a written day does not read a bare ISO text",
        TEST,
        "            and _BARE_ISO_DAY.fullmatch(node.value)\n",
        "            and False\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a bare ISO day text was not found",
    ),
    mutant(
        "B14 the scan for a written day does not enter a nested function",
        TEST,
        "        for child in ast.iter_child_nodes(node):\n            visit(child, fn)\n",
        "        for child in ast.iter_child_nodes(node):\n            if fn is None or not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):\n                visit(child, fn)\n",
        "test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not",
        "a day inside a nested function was not found",
    ),
    mutant(
        "B14 the scan for a written day reads one fixed file and not every policy test file",
        TEST,
        '    files = sorted(\n        p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_policy_*.py")\n    )\n',
        '    files = ["tests/test_policy_guard.py"]\n',
        "test_no_test_writes_a_day_of_the_renewal_window_as_a_literal_inside_a_function",
        "a policy test file is missing from the day scan",
    ),
    mutant(
        "B14 the day scan does not know a two-digit year with hyphens",
        TEST,
        '    r"(?<!\\d)\\d{1,2}-\\d{1,2}-\\d{2}(?!\\d)",  # 12-12-26 (hyphens too; a version has dots)\n',
        "",
        "test_a_two_digit_year_with_hyphens_and_a_day_with_spaces_are_found_and_a_version_is_not",
        "the day form with a two-digit year and hyphens is not found",
    ),
    mutant(
        "B14 the day scan does not know a day with spaces",
        TEST,
        '    r"(?<!\\d)\\d{1,2} \\d{1,2} (?:19|20)\\d{2}(?!\\d)",  # 12 12 2026 (spaces)\n',
        "",
        "test_a_two_digit_year_with_hyphens_and_a_day_with_spaces_are_found_and_a_version_is_not",
        "the day form with spaces is not found",
    ),
    mutant(
        "B13 a test of the policy files writes a day of the renewal window as a literal",
        TEST,
        '        ("secrets/vault", "R17"): Pending("r", "t", DECIDED, DECIDED + timedelta(days=29)),\n',
        # the planted day is built from the LIVE decision day (a renewal moves it with the window; a day written
        # here would fall out of the window after a renewal and the mutant would survive)
        '        ("secrets/vault", "R17"): Pending("r", "t", DECIDED, '
        + _date_call(pp.DECIDED + timedelta(days=5))
        + "),\n",
        "test_no_test_writes_a_day_of_the_renewal_window_as_a_literal_inside_a_function",
        "a day is written in a function",
    ),
    mutant(
        "B13 the day scan does not know a day written without separators",
        TEST,
        '    r"(?<!\\d)(?:19|20)\\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01])(?!\\d)",  # 20261212\n',
        '    r"(?!)",\n',
        "test_more_written_forms_of_a_day_are_found_and_an_ordinary_word_is_not_a_day",
        "of eight digits is not found",
    ),
    mutant(
        "B13 the changelog entry does not end at a numbered item",
        TEST,
        "|\\d+[.)] |#|",
        "|#|",
        "test_the_changelog_entry_ends_at_a_numbered_item_and_at_a_horizontal_rule",
        "a numbered item",
    ),
    mutant(
        "B13 the changelog entry does not end at a horizontal rule",
        TEST,
        "|(?:-{3,}|\\*{3,}|_{3,})[ \\t]*(?:\\n|$))",
        ")",
        "test_the_changelog_entry_ends_at_a_numbered_item_and_at_a_horizontal_rule",
        "a horizontal rule",
    ),
    mutant(
        "B14 notes check does not follow a changed __test__ to the tests of the file",
        NTOOL,
        '    "__test__",\n    "setup_module",\n',
        '    "setup_module",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed __test__ listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed setup_module to the tests of the file",
        NTOOL,
        '    "setup_module",\n    "teardown_module",\n',
        '    "teardown_module",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed setup_module listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed teardown_module to the tests of the file",
        NTOOL,
        '    "teardown_module",\n    "setup_function",\n',
        '    "setup_function",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed teardown_module listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed setup_function to the tests of the file",
        NTOOL,
        '    "setup_function",\n    "teardown_function",\n',
        '    "teardown_function",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed setup_function listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed teardown_function to the tests of the file",
        NTOOL,
        '    "teardown_function",\n    "pytest_generate_tests",\n',
        '    "pytest_generate_tests",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed teardown_function listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed pytest_generate_tests to the tests of the file",
        NTOOL,
        '    "pytest_generate_tests",\n    "pytest_collection_modifyitems",\n',
        '    "pytest_collection_modifyitems",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed pytest_generate_tests listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a changed pytest_collection_modifyitems to the tests of the file",
        NTOOL,
        '    "pytest_collection_modifyitems",\n    "pytest_configure",\n',
        '    "pytest_configure",\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed pytest_collection_modifyitems listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not list a class helper method that the test reaches through self",
        NTOOL,
        "                reached.append(helpers[parts[1]])\n",
        "                pass\n",
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed helper method of a test class listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not list a changed setup method of a test class",
        NTOOL,
        '        m for m in helpers.values() if m.name.startswith(("setup", "teardown")) or _is_fixture(m)\n',
        "        m for m in helpers.values() if _is_fixture(m)\n",
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed setup_method listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not list a changed fixture of a test class",
        NTOOL,
        '        m for m in helpers.values() if m.name.startswith(("setup", "teardown")) or _is_fixture(m)\n',
        '        m for m in helpers.values() if m.name.startswith(("setup", "teardown"))\n',
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a changed autouse fixture of a test class listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check lists a class helper method that the test does not reach",
        NTOOL,
        '        m for m in helpers.values() if m.name.startswith(("setup", "teardown")) or _is_fixture(m)\n',
        "        m for m in helpers.values()\n",
        "test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on",
        "a helper method that the test does not reach listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow the value behind a constant",
        NTOOL,
        "        for value in self.values.get(name, []):\n",
        "        for value in []:\n",
        "test_a_constant_is_followed_through_the_value_behind_it",
        "a changed SKIP read by pytestmark listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not read the names of a tuple target",
        NTOOL,
        "    if isinstance(t, (ast.Tuple, ast.List)):\n        return [n for e in t.elts for n in _target_names(e)]\n",
        "    if isinstance(t, (ast.Tuple, ast.List)):\n        return []\n",
        "test_a_constant_is_followed_through_the_value_behind_it",
        "a change of a tuple target listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check reads a tuple target as module code",
        NTOOL,
        "        return all(_plain_target(e) for e in t.elts)\n",
        "        return False\n",
        "test_a_constant_is_followed_through_the_value_behind_it",
        "a change of a tuple target listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not read an annotated constant",
        NTOOL,
        "            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):\n",
        "            elif isinstance(n, ast.AugAssign) and _is_declaration(n):\n",
        "test_a_constant_is_followed_through_the_value_behind_it",
        "a change of an annotated constant listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not read a unittest.TestCase class",
        NTOOL,
        '(b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")) == "TestCase"',
        '(b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")) == "NoSuchBase"',
        "test_a_unittest_class_and_a_file_ending_in_test_are_read_like_a_test_class_and_a_test_file",
        "a changed method of a unittest.TestCase listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not read a file that ends in _test",
        NTOOL,
        '    r"tests/(?:.+/)?(?:test_[^/]*|[^/]*_test)\\.py"\n',
        '    r"tests/(?:.+/)?(?:test_[^/]*)\\.py"\n',
        "test_a_unittest_class_and_a_file_ending_in_test_are_read_like_a_test_class_and_a_test_file",
        "was not read as one",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not make the module code of a conftest a unit",
        NTOOL,
        "        out[CONFTEST_CODE] = (ast.Module(body=list(mod.glue), type_ignores=[]), ())\n",
        "        pass\n",
        "test_module_code_and_a_fixture_of_a_conftest_list_what_they_act_on",
        "a deleted `for` block of a conftest left",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check reads no module code in any file",
        NTOOL,
        "        self.glue = [n for n in self.tree.body if not _is_declaration(n)]\n",
        "        self.glue = []\n",
        "test_module_code_and_a_fixture_of_a_conftest_list_what_they_act_on",
        "a deleted `for` block of a conftest left",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not look a fixture parameter up in a conftest",
        NTOOL,
        "                for conf in reversed(self.conftests(m.rel)):\n",
        "                for conf in []:\n",
        "test_module_code_and_a_fixture_of_a_conftest_list_what_they_act_on",
        "a changed conftest fixture did not list the test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check looks a fixture up in the conftest furthest away",
        NTOOL,
        "                for conf in reversed(self.conftests(m.rel)):\n",
        "                for conf in self.conftests(m.rel):\n",
        "test_module_code_and_a_fixture_of_a_conftest_list_what_they_act_on",
        "a fixture of a conftest further away listed a test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not see a pytest option of pyproject.toml",
        NTOOL,
        '        return repr(data.get("tool", {}).get("pytest", {}))\n',
        '        return ""\n',
        "test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not",
        "a changed pytest option of pyproject.toml listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check reads a dependency change as a test change",
        NTOOL,
        '        return repr(data.get("tool", {}).get("pytest", {}))\n',
        "        return source\n",
        "test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not",
        "a changed dependency of pyproject.toml listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not see tox.ini or setup.cfg",
        NTOOL,
        '_CONFIG_FILE = re.compile(r"(?:pyproject\\.toml|pytest\\.ini|tox\\.ini|setup\\.cfg)")',
        '_CONFIG_FILE = re.compile(r"(?:pyproject\\.toml|pytest\\.ini)")',
        "test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not",
        "a changed tox.ini listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not see a data file under tests",
        NTOOL,
        '        return "data"\n',
        "        return None\n",
        "test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not",
        "a changed data file under tests listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not see the conftest at the root",
        NTOOL,
        '    r"(?:tests/(?:.+/)?)?conftest\\.py"\n',
        '    r"tests/(?:.+/)?conftest\\.py"\n',
        "test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not",
        "a changed conftest at the root listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not follow a helper of a helper",
        NTOOL,
        "                todo.append((target, member))\n",
        '                parts.append(f"|{target.rel}:{member}={target.dumps[member]}")\n',
        "test_a_helper_two_imports_away_lists_the_test_that_reaches_it_in_each_direction",
        "a helper reached through another helper listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check puts the whole text of an imported file into each test that uses it",
        NTOOL,
        "            if member and member in target.dumps:\n",
        '            if member and member in target.dumps:\n                parts.append(f"|{target.rel}={ast.dump(target.tree)}")\n',
        "test_a_new_function_that_nothing_uses_needs_no_row_and_the_one_that_a_test_uses_does",
        "a new function that nothing uses listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check accepts a unit cell that names nothing that exists",
        NTOOL,
        "    return bool(names) and all(n in units for n in names)\n",
        "    return True\n",
        "test_a_row_whose_unit_cell_names_a_mutant_or_a_test_that_exists_nowhere_is_a_problem",
        "a row naming a mutant and a row naming a test that exist nowhere gave",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not check the unit cell of a row",
        NTOOL,
        "        if not _row_names_a_unit(cell, names, refs.units[files[0]]):\n",
        "        if False:\n",
        "test_a_row_whose_unit_cell_names_a_mutant_or_a_test_that_exists_nowhere_is_a_problem",
        "a row naming a mutant and a row naming a test that exist nowhere gave",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check leaves the helper a mutant calls out of the mutant",
        NTOOL,
        "                + _reached(mod, _used(n) - set(_MUTANT_CALLS))\n",
        "",
        "test_a_helper_that_a_mutant_call_reaches_is_part_of_the_mutant",
        "a changed helper that one mutant calls listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not check a mutant name that starts like a mutant of the tree",
        NTOOL,
        "    return bool(_MUTANT_CODE.match(token)) or words[0] in leads\n",
        "    return bool(_MUTANT_CODE.match(token))\n",
        "test_a_mutant_name_without_a_code_is_checked_and_a_quote_of_a_message_is_not",
        "a mutant name without a code that exists nowhere was accepted",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not check a mutant name that carries a code",
        NTOOL,
        "    return bool(_MUTANT_CODE.match(token)) or words[0] in leads\n",
        "    return words[0] in leads\n",
        "test_a_mutant_name_without_a_code_is_checked_and_a_quote_of_a_message_is_not",
        "a mutant name with a code that no mutant has was accepted",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check reads every quote as a mutant name",
        NTOOL,
        "    return bool(_MUTANT_CODE.match(token)) or words[0] in leads\n",
        "    return True\n",
        "test_a_mutant_name_without_a_code_is_checked_and_a_quote_of_a_message_is_not",
        "a quote of a message was read as a mutant name",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not read a log written with a path",
        NTOOL,
        '        if "/" in name:  # written as a path: it must end a path of a `logs/` folder of the tree\n',
        "        if False:  # written as a path: it must end a path of a `logs/` folder of the tree\n",
        "test_a_log_is_found_in_the_folder_of_the_notes_that_names_it_or_by_the_end_of_its_path",
        "a log written with the end of its path was refused",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check takes a log of any folder for the notes of this folder",
        NTOOL,
        '            here = f"{folder}/logs/{name}" in refs.logs\n',
        '            here = any(path.rsplit("/", 1)[-1] == name for path in refs.logs)\n',
        "test_a_log_is_found_in_the_folder_of_the_notes_that_names_it_or_by_the_end_of_its_path",
        "a log of another folder served the notes of this folder",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check takes any text that ends like a path for a log path",
        NTOOL,
        '            here = any(path == name or path.endswith("/" + name) for path in refs.logs)\n',
        '            here = any(path.rsplit("/", 1)[-1] == name.rsplit("/", 1)[-1] for path in refs.logs)\n',
        "test_a_log_is_found_in_the_folder_of_the_notes_that_names_it_or_by_the_end_of_its_path",
        "a log written with a path that holds no such file was accepted",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not see a call that imports by a run-time name",
        NTOOL,
        "_dotted(n.func)[-1:] in DYNAMIC_IMPORTS",
        "_dotted(n.func)[-1:] in ()",
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "imports by a run-time name listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check ignores the module named as text in an import_module call",
        NTOOL,
        "if isinstance(a, ast.Constant) and isinstance(a.value, str)",
        "if False",
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "named as text in an import_module call listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not walk the folder of a package imported by a file that imports by a run-time name",
        NTOOL,
        '            found |= {f for f in self.files if f.startswith(folder + "/") and f.endswith(".py")}\n',
        "            found |= set()\n",
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "imports by a run-time name listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check takes every python file of the tree for the folder a run-time import reaches",
        NTOOL,
        'f.startswith(folder + "/") and f.endswith(".py")',
        'f.endswith(".py")',
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "outside every named or imported folder listed a test",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check does not count what the reached modules use",
        NTOOL,
        "                        todo.extend((other, n) for n in sorted(other.dumps))\n",
        "                        pass\n",
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "imports by a run-time name listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 notes check counts the file itself among the modules it reaches by a run-time import",
        NTOOL,
        "        found.discard(m.rel)\n",
        "",
        "test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches",
        "inside the folder it imports by a run-time name listed",
        test_file=NOTES_TEST,
    ),
    mutant(
        "B14 the day scan cuts nothing out for the allowed sentence",
        TEST,
        'flat.replace(allowed, "") if allowed else flat',
        "flat",
        "test_a_day_in_any_written_form_is_found_outside_the_one_allowed_sentence",
        "the allowed sentence alone is flagged",
    ),
    mutant(
        "B14 the sentence of the kinds days writes one group for any number of groups",
        TEST,
        '    if len(groups) == 1:\n        return f"all {shown[0]}"',
        '    if len(groups) >= 1:\n        return f"all {shown[0]}"',
        "test_a_renewal_of_some_kinds_leaves_the_changelog_rules_working",
        "three groups were not written",
    ),
]

# The probe: the fixed day given to a run must reach the child pytest of every mutant. The unmutated baseline
# of any run given a day passes only when the tool's clock shows that day (the probe test is in the file);
# this mutant shows the probe CAN fail: it drops the hook that sets the clock, so it is killed only when a
# fixed day was given to the child. It is run first, always with the canary day (never the day of the main run).
PROBE = [
    mutant(
        "PROBE the fixed day does not reach the tool's clock in the child pytest",
        TEST,
        '        monkeypatch.setattr(pp, "datetime", _fixed_clock(day))\n',
        "        pass\n",
        "test_the_day_the_tool_sees_is_the_fixed_day_the_run_was_given",
        "did not reach the tool's clock",
    )
]

# The three tests that read "today" (through `_today()` of the guard file): on a day after the review day they are
# RED by design (the reminder), on every other day green. A baseline that is red only for these three, on a day
# that is faked or past the review day, is the correct result and is named as such, not a broken tree.
DATE_TESTS = (
    "test_every_kind_is_declared_pending_or_holds_no_identity",
    "test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves",
    "test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue",
)
FIXED_DAY_VAR = "HADAVIN_POLICY_FIXED_DAY"
MUTANT_RUN_VAR = "HADAVIN_POLICY_MUTANT_RUN"  # the marker that only this runner sets (the guard file refuses the day without it)


class ArgumentProblem(ValueError):
    """A command line the runner refuses; `str()` is the one plain line that is printed (exit code 2)."""


def parse_args(argv: list[str], floor: date | None = None) -> tuple[str | None, list[str]]:
    """(the fixed day or None, the remaining words that select mutants by name). `--day` is written `--day VALUE`
    or `--day=VALUE`, at most once; the value is `YYYY-MM-DD`, a real day, and not before `floor`, the latest day
    any dated entry was decided (`decided_floor()`: no entry exists before it, so a day before it would show the
    same red tests as a day past the review day for the wrong reason). Anything else is an `ArgumentProblem`,
    never an IndexError."""
    floor = decided_floor() if floor is None else floor
    rest = list(argv)
    marks = [i for i, w in enumerate(rest) if w == "--day" or w.startswith("--day=")]
    if not marks:
        return None, rest
    if len(marks) > 1:
        raise ArgumentProblem("--day may be given once only")
    i = marks[0]
    if rest[i].startswith("--day="):
        value, width = rest[i][len("--day=") :], 1
    else:
        value, width = (rest[i + 1] if i + 1 < len(rest) else ""), 2
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ArgumentProblem(
            "--day needs one day written YYYY-MM-DD, for example --day 2026-12-12"
        )
    try:
        day = date.fromisoformat(value)
    except ValueError:
        raise ArgumentProblem(f"--day {value} is not a real day; write YYYY-MM-DD") from None
    if day < floor:
        raise ArgumentProblem(
            f"--day {value} is before {floor}, the latest day a dated entry was decided: "
            "give that day or a later one"
        )
    del rest[i : i + width]
    return day.isoformat(), rest


def decided_floor(lists: tuple[dict, dict, dict] | None = None) -> date:
    """The latest `decided` day over the three lists, and never before the tool's decision day (`pp.DECIDED`): no
    entry exists before it, so no fixed day (the probe day, or one given with `--day`) may be earlier. A renewal
    of the kinds list alone gives a later day than the tool's. `lists` is for a made-up state."""
    lists = date_lists() if lists is None else lists
    return max([pp.DECIDED, *(e.decided for entries in lists for e in entries.values())])


def canary_day(today: date, review: date | None, floor: date | None = None) -> date:
    """The day the probe always runs with: the day before the review day (a day on which the whole file is green),
    or the day before that when that is the real day today; never the real day, so a dropped clock hook cannot
    hide behind a real clock that shows the same day; never before `floor` (the latest decision day: see
    `decided_floor`), so the day before a review day that comes soon after a renewal is not a day before every
    entry existed (when the day before is the floor itself and is today, the day after it is used). With no
    review day at all (every dated list empty) the day before today."""
    floor = decided_floor() if floor is None else floor
    day = max((review or today) - timedelta(days=1), floor)
    if day != today:
        return day
    earlier = day - timedelta(days=1)
    return earlier if earlier >= floor else day + timedelta(days=1)


def _child_env(day: str | None) -> dict[str, str]:
    env = {k: os.environ[k] for k in mutation_runner.CHILD_ENV if k in os.environ}
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT)])
    env["PYTHONNOUSERSITE"] = "1"
    if day:
        env[FIXED_DAY_VAR] = day
        env[MUTANT_RUN_VAR] = "1"
    return env


class Reading(NamedTuple):
    """One pytest run of the guard file: `failed` = the tests that failed; `not_overdue` = those of them whose
    failure text does not say "is overdue" (red for another reason); `errors` = the number of `ERROR` lines
    (collection or set-up errors); `last` = the last output line."""

    failed: set[str]
    not_overdue: set[str]
    errors: int
    last: str


def read_run(stdout: str) -> Reading:
    """Read pytest's output: the `FAILED <file>::<test>` and `ERROR` lines of the short summary, and for each
    failed test the text of its own section (the `____ name ____` header up to the next one)."""
    failed = set(re.findall(rf"^FAILED {re.escape(TEST)}::(\w+)", stdout, flags=re.MULTILINE))
    errors = len(re.findall(r"^ERROR ", stdout, flags=re.MULTILINE))
    # the summary lists every failure: it is not part of the section of the last failed test
    body = stdout.split("short test summary info")[0]
    parts = re.split(r"^_+ (\S+) _+$", body, flags=re.MULTILINE)
    sections = dict(zip(parts[1::2], parts[2::2], strict=False))
    not_overdue = {t for t in failed if "is overdue" not in sections.get(t, "")}
    return Reading(failed, not_overdue, errors, (stdout.strip().splitlines() or [""])[-1])


def failing_date_tests(day: str | None) -> Reading:
    """Run the guard file once in this tree (the tool's clock fixed to `day` when given) and read the result."""
    proc = subprocess.run(  # noqa: S603 - argv list, no shell
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-rfE",
            "--tb=short",
            "--no-header",
            TEST,
        ],
        cwd=ROOT,
        env=_child_env(day),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    return read_run(proc.stdout)


def clock_readers() -> set[str]:
    """Names of the functions of the guard file that read the clock function `_today`, directly or through a helper
    of the same file (an AST read, not a text search)."""
    tree = ast.parse((ROOT / TEST).read_text(encoding="utf-8"))
    funcs = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    uses = {
        name: {n.id for n in ast.walk(f) if isinstance(n, ast.Name)} for name, f in funcs.items()
    }
    readers = {name for name, used in uses.items() if "_today" in used and name != "_today"}
    while True:
        more = {name for name, used in uses.items() if used & readers and name not in readers}
        if not more:
            return readers
        readers |= more


def date_lists() -> tuple[dict, dict, dict]:
    """The three dated lists the date tests read, in the order of `DATE_TESTS`: kinds, names, claims."""
    from tests.test_policy_guard import PENDING_CLAIMS, PENDING_KINDS, PENDING_NAMES

    return PENDING_KINDS, PENDING_NAMES, PENDING_CLAIMS


def review_days() -> tuple[date | None, date | None]:
    """(earliest, latest) `review_by` over the three lists, by the tool's one helper; `None` when all are empty."""
    lists = date_lists()
    return pp.review_day(*lists), pp.review_day(*lists, latest=True)


def expected_red(lists: tuple[dict, dict, dict] | None = None) -> set[str]:
    """The date tests that must be red after every review day: the test of each list that has entries (a test of an
    empty list has nothing to report and stays green). `lists` is for a made-up state; none means the real ones."""
    lists = date_lists() if lists is None else lists
    return {t for t, entries in zip(DATE_TESTS, lists, strict=True) if entries}


def exit_code(bad: list, weak: list) -> int:
    """1 when a mutant is not good or the first-line check is weak for any mutant; else 0."""
    return 1 if bad or weak else 0


def snippet_problems(mutants: list, root: Path = ROOT) -> list[str]:
    """One line for each mutant whose search text is not found in its file: such a mutant cannot change
    anything, and the run would stop on it (a text found more than once is changed everywhere). After a renewal this shows at once, with no mutant run, which text still
    carries an old day."""
    out = []
    for m in mutants:
        path = root / m.file
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        n = text.count(m.old)
        if n == 0:
            out.append(f"{m.name}: its search text is not found in {m.file}")
    return out


if __name__ == "__main__":
    if sys.argv[1:] == ["--snippets"]:  # no mutant is run: only the search texts are looked up
        found = snippet_problems(M)
        print("\n".join(found) if found else f"all {len(M)} search texts are found")
        sys.exit(1 if found else 0)
    try:
        day, only = parse_args(sys.argv[1:])
    except ArgumentProblem as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    if only and not any(any(o in m.name for o in only) for m in M):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}
    weak = weak_mutants(M)

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    real_today = datetime.now(UTC).date()
    earliest, latest = review_days()
    canary = canary_day(real_today, earliest)
    # (1) the consumer probe: the day after the LATEST review day is given to the child pytest; the date test of
    # every list that has entries must be red there (and no other test), each with "is overdue" in its failure
    # text. They read the clock function, so they show that the fixed day reaches the tests that read "today",
    # not only the tool. With every dated list empty there is no review day: nothing can go red, and that is said.
    if latest is None:
        print("probe skipped: every dated list is empty, so no date test can go red on any day")
    else:
        after = latest + timedelta(days=1)
        run = failing_date_tests(after.isoformat())
        if run.failed != expected_red() or run.not_overdue or run.errors:
            print(
                f"BAD the fixed day {after} did not make exactly the date tests of the non-empty lists red "
                f"with an overdue text: red = {sorted(run.failed)}, red without 'is overdue' = "
                f"{sorted(run.not_overdue)}, errors = {run.errors} ({run.last})"
            )
            sys.exit(1)
        print(
            f"probe ok: at the fixed day {after} exactly the date tests of the non-empty lists are red, "
            f"each with an overdue text: {sorted(run.failed)}"
        )
    # (2) the clock-hook probe mutant, always with the canary day (a green day that is not today)
    mutation_runner.CHILD_FIXED_ENV[FIXED_DAY_VAR] = canary.isoformat()
    mutation_runner.CHILD_FIXED_ENV[MUTANT_RUN_VAR] = "1"
    probe = run_mutants(
        ROOT, PROBE, [TEST], extra_dirs=("tests", "tools", "docs"), first_lines=first_lines
    )
    if not all(g for _, _, _, g in probe):
        print(f"BAD the fixed day {canary} did not reach the child pytest: {probe}")
        sys.exit(1)
    print(
        f"probe ok: the fixed day {canary} reached the tool's clock in the child pytest (probe mutant killed)"
    )
    # (3) the baseline reading of the main run: which tests are red on the day of this run, and is that right?
    run = failing_date_tests(day)
    reading, last = run.failed, run.last
    unexpected = reading - set(DATE_TESTS)
    if unexpected or run.not_overdue or run.errors:
        print(
            f"BAD on {day or 'the real day'}: tests other than the date tests are red: {sorted(unexpected)}; "
            f"red without 'is overdue' in the failure text: {sorted(run.not_overdue)}; "
            f"ERROR lines: {run.errors} ({last})"
        )
        sys.exit(1)
    skipped_names: set[str] = set()
    if reading and day is None:
        print(
            f"RED BASELINE on the real day {real_today}: {sorted(reading)}. This is the date reminder, not a broken tree: "
            "renew or finish the dated entries (what to do is in the failure text of the tests). No mutant was run."
        )
        sys.exit(1)
    if reading:
        print(
            f"RED BASELINE at the fixed day {day}, as it must be: exactly these date tests report an overdue entry: "
            f"{sorted(reading)}. That is the reminder working on a faked day, not a broken tree. The mutants run "
            "with those three tests left out of the child run (deselected there only; they stay in the repository)."
        )
        skipped_names = set(reading)
        mutation_runner.CHILD_FIXED_ENV["PYTEST_ADDOPTS"] = " ".join(
            f"--deselect {TEST}::{name}" for name in sorted(reading)
        )
    mutation_runner.CHILD_FIXED_ENV.pop(FIXED_DAY_VAR, None)
    mutation_runner.CHILD_FIXED_ENV.pop(MUTANT_RUN_VAR, None)
    if day:
        mutation_runner.CHILD_FIXED_ENV[FIXED_DAY_VAR] = day
        mutation_runner.CHILD_FIXED_ENV[MUTANT_RUN_VAR] = "1"
        print(f"every mutant below runs with the tool's clock fixed to {day}")
    runnable = [m for m in M if m.only_test not in skipped_names]
    for m in M:
        if m.only_test in skipped_names:
            print(f"not run at {day}: {m.name} (its killer is a date test that is red on that day)")
    res = run_mutants(
        ROOT,
        runnable,
        [TEST, NOTES_TEST],
        extra_dirs=("tests", "tools", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    readers = clock_readers()
    date_killed = [m.name for m in M if m.only_test in readers or m.only_test in DATE_TESTS]
    print(
        f"mutants killed ONLY by a test that reads the clock function (a result that can change with the day): "
        f"{len(date_killed)} of {len(M)}" + (f": {date_killed}" if date_killed else "")
    )
    for w_name, w_expect, w_killer in weak:
        print(f"WEAK {w_name} | expect: {w_expect!r} | killer: {w_killer}")
    print(
        f"first-line check is weak (the expect text is in no assert message, `match=` or `what=` of the killer or of a helper it calls: the count of weak mutants is a LOWER bound, because a helper text can carry the expect text for a killer that never reaches it) for {len(weak)} of {len(M)} mutants (exit 1 when any); "
        f"killer shared by more than one mutant: {sorted({k for k in (m.only_test for m in M) if [m.only_test for m in M].count(k) > 1})}"
    )
    sys.exit(exit_code(bad, weak))
