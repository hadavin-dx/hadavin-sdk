"""The mutants of the declared-permission guard (ticket Q8c, PR 1), run by ``tools/mutation_runner.py``.

Each mutant reverts ONE rule in a temp copy (of ``tools/policy_page.py``, or of the reader in
``tests/test_policy_guard.py``); the plant test in ``killer`` must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/policy_mutants.py            # all mutants; exit 1 if any is not good
    python tests/policy_mutants.py D1         # only mutants whose name contains the text

How strong the kill check is: the first failing line must hold ``expect``. Where the killer asserts through
``same()`` (the run prints how many mutants), that line already holds the expected text, so the check shows only
that the test failed at an assertion, not at which one. Those mutants are WEAK: a revert that makes some other
``same()`` of the same test fail counts as killed. Two mutants may share one killer (the run prints which). The
four mutants for the fix-batch-2 rules use killers with their own message and are not weak.

What has NO mutant here, and why:
* the tests that need a Vault server (tests/test_policy_engine.py): a reverted rule there can only be shown on
  a real server, so their plants run in CI and nowhere else;
* "POLICY must be a pure literal": the refusal is `ast.literal_eval`'s own, and no one-line revert of it exists
  that does not run code; its three plants stay as tests;
* the Kubernetes equalities (declared operations, never-list, verb and resource per path): each is one
  assertion of a test, with no rule function to revert; the independent plants P09b and P09c showed them fire.
"""

import ast
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_policy_guard.py"
PIN = "tests/test_policy_guard::"
TOOL = "tools/policy_page.py"


def _killers_using_same() -> set[str]:
    """Names of the killer tests that assert through `same()`. `same()` writes the EXPECTED text into its
    failure message, and `expect` is a fragment of that text, so for these killers the first-line check only
    shows that the test failed at an assertion, not which one: any failing `same()` in that test passes it."""
    tree = ast.parse((ROOT / TEST).read_text(encoding="utf-8"))
    return {
        f.name
        for f in tree.body
        if isinstance(f, ast.FunctionDef)
        and any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "same"
            for n in ast.walk(f)
        )
    }


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
        TEST,
        "        for kind, gid in sorted(unverified - set(pending))\n",
        "        for kind, gid in sorted(set())\n",
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
        "holds a wildcard",
    ),
    mutant(
        "D3 an empty reason is accepted",
        TOOL,
        '    if not g["reason"].strip():\n',
        '    if g["reason"] is None:\n',
        "test_plant_d3_an_empty_reason_is_caught",
        "reason is empty",
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
        "unknown key",
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
        "DID NOT RAISE",
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
        TEST,
        "        if key in live and today > p.review_by\n",
        "        if key in live and today is None\n",
        "test_plant_an_overdue_entry_says_what_to_do_and_a_date_cannot_be_moved_far",
        "no overdue entry is reported",
    ),
    mutant(
        "Dated entries: a date moved further than the cap is accepted",
        TEST,
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
        "DID NOT RAISE",
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
        "DID NOT RAISE",
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
        "DID NOT RAISE",
    ),
    mutant(
        "Values: a value longer than its limit is put into the text",
        TOOL,
        "            if len(part) > MAX_LENGTH[key]:\n",
        "            if len(part) < 0:\n",
        "test_plant_a_300_character_value_is_refused",
        "DID NOT RAISE",
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
        "            if s in BUILDER_ONLY_SOURCES\n",
        "            if False\n",
        "test_a_builder_only_source_is_marked_wherever_the_page_lists_it",
        "without the mark (builder only)",
    ),
    mutant(
        "B3 a grant with an unchecked claim needs no dated entry",
        TEST,
        "        for kind, gid in sorted(claimed - set(pending))\n",
        "        for kind, gid in sorted(set())\n",
        "test_plant_an_unchecked_claim_with_no_pending_entry_is_caught",
        "has an unchecked claim",
    ),
    mutant(
        "B3 a claim note whose text is in no claims_unverified is accepted",
        TEST,
        '            if how == "claim" and rest[0] not in claims:\n',
        "            if False:\n",
        "test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught",
        "a claim note whose text is in no claims_unverified is not reported",
    ),
    mutant(
        "B3 a note that names an unknown source id is accepted",
        TEST,
        "                    if s not in known\n",
        "                    if False\n",
        "test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught",
        "a note that names an unknown source id is not reported",
    ),
    mutant(
        "B3 a stale note class is accepted",
        TEST,
        "    return out + [\n"
        '        f"NOTE_CLASSES entry {k} matches no note: delete it" for k in sorted(set(classes) - used)\n'
        "    ]\n",
        "    return out\n",
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
        "            edge(after, _NOT_SLASH, part)  # a further part\n",
        "            pass\n",
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
        '            edge(part, "/", after)\n',
        "            edge(part, _NOT_SLASH, after)\n",
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
        "            if claim and s in PARTLY_BUILDER_ONLY_SOURCES\n",
        "            if s in PARTLY_BUILDER_ONLY_SOURCES\n",
        "test_a_source_of_which_only_a_passage_was_read_is_marked_on_a_row_with_a_claim_only",
        "a row with no claim marks a source as partly builder only",
    ),
    mutant(
        "B4 a builder-only id that is no row of the sources file is accepted",
        TOOL,
        '    if unknown := sorted((set(found["BUILDER-ONLY"]) | set(found["PARTLY-BUILDER-ONLY"])) - known):\n',
        "    if False:\n",
        "test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line",
        "DID NOT RAISE",
    ),
    mutant(
        "B4 a second builder-only line in the sources file is accepted",
        TOOL,
        "        if len(rows) != 1:\n",
        "        if len(rows) < 1:\n",
        "test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line",
        "DID NOT RAISE",
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
        TEST,
        '        out |= {(k, f"free:{i}") for i, f in enumerate(p.free) if f.claims_unverified}\n',
        "        pass\n",
        "test_the_pending_claims_of_a_free_and_a_never_entry_are_watched_like_a_grant_claim",
        "needs no PENDING_CLAIMS entry",
    ),
    mutant(
        "B4 a free-entry note may name a source its entry does not list",
        TEST,
        "                        if s not in (entry.verified or ())[1:]\n",
        "                        if False\n",
        "test_a_sources_note_whose_free_entry_does_not_list_the_id_is_caught",
        "is not reported",
    ),
    mutant(
        "M1 the page claims a run that is not on record",
        TOOL,
        '        return "These tests have not run yet: no run of them is on record."\n',
        '        return "These tests ran."\n',
        "test_the_page_states_its_limits_and_offers_text_for_the_three_kinds",
        "have not run yet",
    ),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(any(o in m.name for o in only) for m in M):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}
    weak_killers = _killers_using_same()
    weak = [m.name for m in M if m.only_test in weak_killers]

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests", "tools", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    print(
        f"first-line check is weak (killer asserts through same()) for {len(weak)} of {len(M)} mutants; "
        f"killer shared by more than one mutant: {sorted({k for k in (m.only_test for m in M) if [m.only_test for m in M].count(k) > 1})}"
    )
    sys.exit(1 if bad else 0)
