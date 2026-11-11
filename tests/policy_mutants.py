"""The mutants of the declared-permission guard (ticket Q8c, PR 1), run by ``tools/mutation_runner.py``.

Each mutant reverts ONE rule in a temp copy (of ``tools/policy_page.py``, or of the reader in
``tests/test_policy_guard.py``); the plant test in ``killer`` must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/policy_mutants.py            # all mutants; exit 1 if any is not good
    python tests/policy_mutants.py D1         # only mutants whose name contains the text

What has NO mutant here, and why:
* the tests that need a Vault server (tests/test_policy_engine.py): a reverted rule there can only be shown on
  a real server, so their plants run in CI and nowhere else;
* "POLICY must be a pure literal": the refusal is `ast.literal_eval`'s own, and no one-line revert of it exists
  that does not run code; its three plants stay as tests;
* the Kubernetes equalities (declared operations, never-list, verb and resource per path): each is one
  assertion of a test, with no rule function to revert; the independent plants P09b and P09c showed them fire.
"""

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


def mutant(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


M = [
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
    sys.exit(1 if bad else 0)
