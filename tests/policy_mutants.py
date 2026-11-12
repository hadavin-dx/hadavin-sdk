"""The mutants of the declared-permission guard (ticket Q8c, PR 1), run by ``tools/mutation_runner.py``.

Each mutant reverts ONE rule in a temp copy (of ``tools/policy_page.py``, or of the reader in
``tests/test_policy_guard.py``); the plant test in ``killer`` must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/policy_mutants.py            # all mutants; exit 1 if any is not good
    python tests/policy_mutants.py D1         # only mutants whose name contains the text
    python tests/policy_mutants.py --day 2026-12-12   # the tool's clock shows that day in every mutant run

How strong the kill check is: the first failing line must hold ``expect``. A mutant is WEAK when ``expect`` is
in none of the killer's own words, counted from the syntax tree: the message of an ``assert``, the ``match=`` of
``pytest.raises`` and the ``what`` of a ``same()`` call (a comment, a loop literal, a predicate or the ``def`` line
do not count, and pytest's own "DID NOT RAISE" does not name a call). The run prints the weak mutants. Two
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

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools import mutation_runner
from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_policy_guard.py"
PIN = "tests/test_policy_guard::"
TOOL = "tools/policy_page.py"


def _text_of(node: ast.AST | None) -> list[str]:
    """The string pieces of a message expression: a plain string, or the constant parts of an f-string."""
    return (
        [
            n.value
            for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        ]
        if node
        else []
    )


def message_texts() -> dict[str, list[str]]:
    return message_texts_of((ROOT / TEST).read_text(encoding="utf-8"))


def message_texts_of(source: str) -> dict[str, list[str]]:
    """For every function of the guard file: the texts a failing line can carry by the test's own words, read from
    the syntax tree and from nothing else: the message of an `assert`, the `match=` of `pytest.raises`, and the
    `what` of a `same()` call. A string in a comment, a loop literal, a predicate (`any("x" in p ...)`) or the
    `def` line is NOT counted: it does not appear in the failing line."""
    tree = ast.parse(source)
    out: dict[str, list[str]] = {}
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
    return out


def weak_mutants(mutants: list) -> list[tuple[str, str, str]]:
    """(name, expect, killer) of each mutant whose killer's own words (assert message, `match=` of
    `pytest.raises`, `what` of `same()`; see `message_texts`) do not hold `expect`: the first-line check then shows
    only that the killer failed, not at which line."""
    texts = message_texts()
    return [
        (m.name, m.expect, m.only_test)
        for m in mutants
        if not any(m.expect in t for t in texts.get(m.only_test, []))
    ]


def mutant(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
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
        '        found = tuple(x.strip() for x in _head_line(lines, tag).split(","))\n',
        '        found = tuple(x.strip() for x in _head_line(lines, tag).split(",")[:-1])\n',
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
        "the check command did not stop on 2026-12-12 by its own clock",
    ),
    mutant(
        "B8 the pending kinds take another decision day than their own literal",
        TEST,
        "KINDS_DECIDED = date(2026, 11, 11)\n",
        "KINDS_DECIDED = date(2026, 11, 12)\n",
        "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date",
        "the pending kinds do not all stand on the literal day 2026-11-11",
    ),
    mutant(
        "B9 the page head states a fixed review date",
        TOOL,
        '        f", or the review date\\n  {day}, whichever comes first",\n',
        '        ", or the review date\\n  2026-12-11, whichever comes first",\n',
        "test_the_page_names_the_review_day_of_the_dated_lists_and_follows_a_renewal",
        "the page head still names the review day from before the renewal",
    ),
    mutant(
        "B9 the review date is the latest of the dated lists, not the earliest",
        TOOL,
        "    return min(days) if days else None\n",
        "    return max(days) if days else None\n",
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
        "KINDS_DECIDED = date(2026, 11, 11)\n",
        "KINDS_DECIDED = pp.DECIDED\n",
        "test_the_decision_day_of_the_16_kinds_does_not_follow_the_tools_decision_day",
        "the 16 kinds follow the tool's decision day when it moves",
    ),
    mutant(
        "B10 the clock function of the date tests reads the real day",
        TEST,
        "    return pp.datetime.now(pp.UTC).date()\n\n\ndef _kinds_problems_today",
        "    return datetime.now(UTC).date()\n\n\ndef _kinds_problems_today",
        "test_the_three_date_tests_read_the_clock_function_and_go_red_after_the_review_day",
        "it reads another clock",
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
        "    return min(days) if days else None\n",
        "    return min(days)\n",
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "review_date() has no answer with both dated lists empty",
    ),
    mutant(
        "B10 the page keeps a sentence with no date for a dated entry when no day is set",
        TOOL,
        '            "No permission name or claim is waiting for a check now: the tests hold no dated entry for one.",\n',
        '            "Each of these has a dated entry in the tests (review by None) that turns the suite red.",\n',
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the page head keeps the sentence about a dated entry with no date to name",
    ),
    mutant(
        "B10 the page names a day when both dated lists are empty",
        TOOL,
        "    if day is None:\n        return (\n",
        "    if False:\n        return (\n",
        "test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report",
        "the page head does not say plainly that no review date is set",
    ),
    mutant(
        "B10 the review date ignores the claims list",
        TOOL,
        "    days = [p.review_by for p in (*PENDING_NAMES.values(), *PENDING_CLAIMS.values())]\n",
        "    days = [p.review_by for p in PENDING_NAMES.values()]\n",
        "test_with_one_dated_list_empty_the_page_names_the_review_day_of_the_other",
        "review_date() ignores the one list that has entries",
    ),
    mutant(
        "B10 --day with no value is an IndexError",
        "tests/policy_mutants.py",
        '    value = rest[i + 1] if i + 1 < len(rest) else ""\n',
        "    value = rest[i + 1]\n",
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
        "    return day - timedelta(days=1) if day == today else day\n",
        "    return day\n",
        "test_the_probe_day_is_never_the_real_day_and_is_never_after_the_review_day",
        "the probe day is the real day",
    ),
    mutant(
        "B10 the probe day is the review day itself",
        "tests/policy_mutants.py",
        "    day = review - timedelta(days=1)\n",
        "    day = review\n",
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
        "DECIDED = date(2026, 11, 11)\n",
        "DECIDED = date(2026, 11, 12)\n",
        "test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided",
        "the tool's decision day moved without this test",
    ),
    mutant(
        "B9 the 16 kinds take the tool's decision day, not a literal of their own",
        TEST,
        "KINDS_DECIDED = date(2026, 11, 11)\n",
        "KINDS_DECIDED = pp.DECIDED\n",
        "test_the_kinds_decision_day_is_a_literal_date_call_not_a_name_of_the_tools_date",
        "KINDS_DECIDED is not a literal date(...) call",
    ),
    mutant(
        "B9 a pending kind is more than 92 days from its decision",
        TEST,
        '    "llm/gemini": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),\n',
        '    "llm/gemini": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 3, 31)),\n',
        "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date",
        "a pending kind is more than 92 days from its decision to its review day",
    ),
    Mutant(
        "B9 the docs page names another review date than the dated lists",
        "docs/declared-permissions.md",
        "  2026-12-11, whichever comes first (ledger row",
        "  2026-12-12, whichever comes first (ledger row",
        "in the trigger sentence",
        test_file=TEST,
        only_test="test_the_docs_page_names_the_review_day_of_the_dated_lists_only",
        pinned=PIN + "test_the_docs_page_names_the_review_day_of_the_dated_lists_only",
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


def parse_args(argv: list[str]) -> tuple[str | None, list[str]]:
    """(the fixed day or None, the remaining words that select mutants by name). `--day` needs a value written
    `YYYY-MM-DD` that is a real day; anything else is an `ArgumentProblem`, never an IndexError."""
    rest = list(argv)
    if "--day" not in rest:
        return None, rest
    i = rest.index("--day")
    value = rest[i + 1] if i + 1 < len(rest) else ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ArgumentProblem(
            "--day needs one day written YYYY-MM-DD, for example --day 2026-12-12"
        )
    try:
        day = date.fromisoformat(value)
    except ValueError:
        raise ArgumentProblem(f"--day {value} is not a real day; write YYYY-MM-DD") from None
    del rest[i : i + 2]
    return day.isoformat(), rest


def canary_day(today: date, review: date) -> date:
    """The day the probe always runs with: the day before the review day (a day on which the whole file is green),
    or the day before that when that is the real day today; never the real day, so a dropped clock hook cannot
    hide behind a real clock that shows the same day."""
    day = review - timedelta(days=1)
    return day - timedelta(days=1) if day == today else day


def _child_env(day: str | None) -> dict[str, str]:
    env = {k: os.environ[k] for k in mutation_runner.CHILD_ENV if k in os.environ}
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT)])
    env["PYTHONNOUSERSITE"] = "1"
    if day:
        env[FIXED_DAY_VAR] = day
        env[MUTANT_RUN_VAR] = "1"
    return env


def failing_date_tests(day: str | None) -> tuple[set[str], str]:
    """Run the guard file once in this tree (the tool's clock fixed to `day` when given) and return the failing
    test names and the last output line. Read from pytest's own short summary lines `FAILED <file>::<test>`."""
    proc = subprocess.run(  # noqa: S603 - argv list, no shell
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-rf",
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
    failed = set(re.findall(rf"^FAILED {re.escape(TEST)}::(\w+)", proc.stdout, flags=re.MULTILINE))
    return failed, (proc.stdout.strip().splitlines() or [""])[-1]


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


def latest_review_day() -> date:
    from tests.test_policy_guard import PENDING_CLAIMS, PENDING_KINDS, PENDING_NAMES

    return max(
        p.review_by for d in (PENDING_KINDS, PENDING_NAMES, PENDING_CLAIMS) for p in d.values()
    )


def earliest_review_day() -> date:
    from tests.test_policy_guard import PENDING_CLAIMS, PENDING_KINDS, PENDING_NAMES

    return min(
        p.review_by for d in (PENDING_KINDS, PENDING_NAMES, PENDING_CLAIMS) for p in d.values()
    )


if __name__ == "__main__":
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
    canary = canary_day(real_today, earliest_review_day())
    # (1) the consumer probe: the day after the LATEST review day is given to the child pytest; the three date tests
    # must all be red there. They read the clock function, so they show that the fixed day reaches the tests that
    # read "today", not only the tool.
    after = latest_review_day() + timedelta(days=1)
    red, last = failing_date_tests(after.isoformat())
    if red != set(DATE_TESTS):
        print(
            f"BAD the fixed day {after} did not make exactly the three date tests red: red = {sorted(red)} ({last})"
        )
        sys.exit(1)
    print(f"probe ok: at the fixed day {after} exactly the three date tests are red: {sorted(red)}")
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
    reading, last = failing_date_tests(day)
    unexpected = reading - set(DATE_TESTS)
    if unexpected:
        print(
            f"BAD tests other than the date tests are red on {day or 'the real day'}: {sorted(unexpected)} ({last})"
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
        [TEST],
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
        f"first-line check is weak (the expect text is in no assert message, `match=` or `what=` of the killer) for {len(weak)} of {len(M)} mutants; "
        f"killer shared by more than one mutant: {sorted({k for k in (m.only_test for m in M) if [m.only_test for m in M].count(k) > 1})}"
    )
    sys.exit(1 if bad else 0)
