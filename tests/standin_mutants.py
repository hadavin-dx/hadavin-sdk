"""The mutants of the stand-in rules (named S1 to S30): the kind registry and the loopback-only rule for stand-ins.

Run by the P1m runner (``tools/mutation_runner.py``) like ``tests/stage_mutants.py``, in a separate list. Each mutant
reverts ONE guard in a temp copy of the package; the named test must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/standin_mutants.py          # all mutants; exit 1 if any is not good
    python tests/standin_mutants.py S3       # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
REG_TEST = "tests/test_kind_registry.py"
HOST_TEST = "tests/test_stand_in_hosts.py"
TBL = "src/hadavin_sdk/backends/table.py"
CFG = "src/hadavin_sdk/config.py"


def mutant(name, file, old, new, test_file, killer, expect, **more):
    stem = test_file.removesuffix(".py")
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=f"{stem}::{killer}",
        **more,
    )


M = [
    # --- the registry rules (backends/table.py)
    mutant("S1 a kind with no role is no longer reported", TBL, 'if entry.role not in ("stand_in", "real")', "if False",
        REG_TEST, "test_plant_an_unclassified_kind_is_caught", "an unclassified kind was not reported"),
    mutant("S2 a misspelt role counts as a real kind", TBL, 'if entry.role not in ("stand_in", "real")', "if entry.role is None",
        REG_TEST, "test_plant_a_misspelt_role_is_caught", "a misspelt role was not reported"),
    mutant("S3 a stand-in outside DEMO_ONLY and the named exceptions is no longer reported", TBL,
        "if pair not in demo_only and not (pair in not_prod and pair in pilot_stand_ins):", "if False:",
        REG_TEST, "test_plant_a_stand_in_a_live_stage_would_accept_is_caught", "outside DEMO_ONLY was not reported"),
    mutant("S4 a stand-in listed only in NOT_PROD is accepted (it would run in a pilot)", TBL,
        "and not (pair in not_prod and pair in pilot_stand_ins)", "and not (pair in not_prod)",
        REG_TEST, "test_plant_a_stand_in_listed_only_in_not_prod_is_caught_unless_it_is_a_named_exception",
        "listed only in NOT_PROD was accepted"),
    mutant("S5 a named exception that prod does not refuse is accepted", TBL,
        "and not (pair in not_prod and pair in pilot_stand_ins)", "and not (pair in pilot_stand_ins)",
        REG_TEST, "test_plant_a_stand_in_listed_only_in_not_prod_is_caught_unless_it_is_a_named_exception",
        "an exception that prod does not refuse was accepted"),
    mutant("S6 a stand-in that declares no hosts is no longer reported", TBL, "if entry.hosts is None:", "if False:",
        REG_TEST, "test_plant_a_stand_in_that_declares_no_hosts_is_caught", "no declared hosts was not reported"),
    mutant("S7 a real kind is held to the stand-in rules", TBL, 'if entry.role != "stand_in":', "if False:",
        REG_TEST, "test_a_real_kind_needs_no_demo_only_entry_and_no_hosts", "a real kind was held to the stand-in rules"),
    mutant("S8 one mislabel: the in-memory store is marked real, so every rule skips it", TBL,
        'f"{_BUILTIN}:memory_store", role="stand_in"', 'f"{_BUILTIN}:memory_store", role="real"',
        REG_TEST, "test_the_stand_ins_are_exactly_these_seven_and_each_is_refused_by_the_stage_that_must",
        "the set of stand-in kinds changed"),
    mutant("S9 the field-name words forget dsn", TBL, '"dsn", "netloc"', '"netloc"',
        REG_TEST, "test_a_field_name_that_points_at_a_machine_is_found", "was not found: dsn"),
    mutant("S10 the whole-word list forgets base (api_base)", TBL, '"addr", "base",', '"addr",',
        REG_TEST, "test_a_field_name_that_points_at_a_machine_is_found", "was not found: api_base"),
    mutant("S11 the field name is read with its letter case (HOST)", TBL, "low = name.lower()", "low = name",
        REG_TEST, "test_a_field_name_that_points_at_a_machine_is_found", "was not found: HOST"),
    mutant("S12 a field typed as a URL is no longer found by its type", TBL, "if by_name or by_type:", "if by_name:",
        REG_TEST, "test_a_field_that_holds_a_url_or_an_address_is_found_whatever_it_is_called",
        "typed as a URL or an address was not found"),
    mutant("S13 every field whose name has a word of the list is flagged (database_name)", TBL,
        "w.lower() in _MACHINE_WORDS for w in _WORD_SPLIT.split(name)", "w.lower() in name.lower() for w in _MACHINE_WORDS",
        REG_TEST, "test_a_field_name_that_points_at_no_machine_is_not_flagged", "was flagged: database_name"),
    # --- the import guard and the first-use guard
    mutant("S14 the import-time classification guard is dropped", TBL, "_assert_classified(TABLE)  #", "pass  #",
        REG_TEST, "test_importing_the_table_with_a_kind_that_has_no_role_stops_the_import", "DID NOT RAISE"),
    mutant("S15 the classification guard collects no problem sentence", TBL, "if problems := _unclassified(table):", "if False:",
        REG_TEST, "test_importing_the_table_with_a_kind_that_has_no_role_stops_the_import", "DID NOT RAISE"),
    mutant("S16 import enforces every rule (the trap that crashed five stage mutants)", TBL,
        "if problems := _unclassified(table):", "if problems := registry_problems(table):",
        REG_TEST, "test_a_broken_listing_does_not_stop_the_import_but_fails_at_first_use",
        "a rule other than classification stopped the import"),
    mutant("S17 the first config does not run the registry rules", CFG, "        assert_registry_sound()\n", "        pass\n",
        REG_TEST, "test_a_downstream_kind_that_breaks_a_rule_is_refused_at_the_first_config", "DID NOT RAISE"),
    mutant("S18 a Backends built directly skips the registry rules", CFG, "        assert_registry_sound()\n", "        pass\n",
        REG_TEST, "test_the_same_refusal_holds_for_a_backends_built_directly", "DID NOT RAISE"),
    # --- the loopback-only rule (config.py)
    mutant("S19 the stand-in host rule is never applied", CFG, 'if entry.role != "stand_in":', "if True:",
        HOST_TEST, "test_a_stand_in_on_another_computer_is_refused", "DID NOT RAISE"),
    mutant("S20 one loopback host is enough among several", CFG, "if all(is_loopback_host(host) for host in hosts):",
        "if any(is_loopback_host(host) for host in hosts):",
        HOST_TEST, "test_one_bad_host_among_several_refuses_the_kind", "one bad host among several was accepted"),
    mutant("S21 the Backends validator does not ask the stand-in rule", CFG,
        "if problem := stand_in_host_problem(cap, settings.kind, settings):", "if False:",
        HOST_TEST, "test_a_stand_in_on_another_computer_is_refused", "DID NOT RAISE"),
    mutant("S22 a direct Backends build is not held to the rule", CFG,
        "if problem := stand_in_host_problem(cap, settings.kind, settings):", "if False:",
        HOST_TEST, "test_a_backends_built_directly_hits_the_same_rule", "DID NOT RAISE"),
    mutant("S23 the refusal echoes the settings", CFG, 'f"{where}: a stand-in kind may only be reached on this computer "',
        'f"{where}: a stand-in kind may only be reached on this computer " + repr(settings) + ""',
        HOST_TEST, "test_the_refusal_never_echoes_the_host_or_other_setting_values", "echoes a setting value"),
    mutant("S24 the kind check is inverted: real kinds are refused", CFG, 'if entry.role != "stand_in":',
        'if entry.role == "stand_in":',
        HOST_TEST, "test_a_real_kind_may_name_any_host", "a real kind was refused"),
    mutant("S25 the loopback test is a prefix match", CFG, "is_loopback_host(host) for host in hosts", 'str(host).startswith("127") for host in hosts',
        HOST_TEST, "test_the_rule_agrees_with_is_loopback_host_on_seeded_random_hosts", "the rule disagrees with is_loopback_host"),
    mutant("S26 an empty host list passes although the kind has a host setting", CFG,
        "if not hosts and names_a_machine(type(settings)):", "if False:",
        HOST_TEST, "test_a_stand_in_that_lists_no_host_but_has_a_host_setting_is_refused", "DID NOT RAISE"),
    mutant("S27 a stand-in that declares no hosts is accepted by the rule", CFG, "if entry.hosts is None:", "if False:",
        HOST_TEST, "test_a_stand_in_with_no_hosts_function_is_refused_by_the_rule_itself", "was accepted",
        ),
    mutant("S28 a hosts function that raises is not caught", CFG, "except (ValueError, TypeError, AttributeError, LookupError):", "except OSError:",
        HOST_TEST, "test_a_hosts_function_that_raises_refuses_without_echoing_the_error", "did not match"),
    mutant("S29 a kind the table does not list is a key error", CFG, "entry = TABLE.get(cap, {}).get(kind)", "entry = TABLE[cap][kind]",
        HOST_TEST, "test_a_kind_the_table_does_not_list_is_refused_not_a_key_error", "KeyError", allow_crash=True, crash_type="KeyError"),
    mutant("S30 the system address is shown in its refusal", CFG,
        '"(http only for loopback with allow_insecure_loopback)"',
        '"(http only for loopback with allow_insecure_loopback): " + system.base_url',
        HOST_TEST, "test_no_value_is_echoed_on_the_other_refusal_paths_of_the_loader", "echoes a value"),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
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
        [REG_TEST, HOST_TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
