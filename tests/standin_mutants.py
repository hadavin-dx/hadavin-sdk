"""The mutants of the stand-in rules (named S1 to S13): the kind registry and the loopback-only rule for stand-ins.

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


def mutant(name, file, old, new, test_file, killer, expect):
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
    )


M = [
    mutant("S1 a kind with no role is no longer reported", TBL, 'if entry.role not in ("stand_in", "real")', "if False",
        REG_TEST, "test_plant_an_unclassified_kind_is_caught", "an unclassified kind was not reported"),
    mutant("S2 a misspelt role counts as a real kind", TBL, 'if entry.role not in ("stand_in", "real")', "if entry.role is None",
        REG_TEST, "test_plant_a_misspelt_role_is_caught", "a misspelt role was not reported"),
    mutant("S3 a stand-in outside DEMO_ONLY and NOT_PROD is no longer reported", TBL,
        "if (cap, kind) not in demo_only and (cap, kind) not in not_prod:", "if False:",
        REG_TEST, "test_plant_a_stand_in_a_client_stage_would_accept_is_caught", "outside DEMO_ONLY and NOT_PROD was not reported"),
    mutant("S4 a stand-in host setting with no hosts is no longer reported", TBL,
        "if named and entry.hosts is None:", "if False:",
        REG_TEST, "test_plant_a_stand_in_with_a_host_setting_and_no_hosts_is_caught", "was not reported"),
    mutant("S5 the host-like field names forget url", TBL, '(host|url|address|endpoint)', "(host|address|endpoint)",
        REG_TEST, "test_seeded_fuzz_of_role_marks_and_listings_agrees_with_the_rules", "the checker disagrees with the rules"),
    mutant("S6 the import-time guard is dropped", TBL, "assert_registry_sound(TABLE)  #", "pass  #",
        REG_TEST, "test_the_table_module_runs_the_guard_on_its_own_table_at_import", "no longer runs the registry guard"),
    mutant("S7 the guard collects no problem sentence into the error", TBL, "if problems := _unclassified(table):", "if False:",
        REG_TEST, "test_the_import_time_guard_raises_naming_the_unclassified_kind", "DID NOT RAISE"),
    mutant("S8 the stand-in host rule is never applied", CFG, 'if entry.role != "stand_in" or entry.hosts is None:', "if True:",
        HOST_TEST, "test_a_stand_in_on_another_computer_is_refused", "DID NOT RAISE"),
    mutant("S9 one loopback host is enough among several", CFG, "if all(is_loopback_host(host) for host in entry.hosts(settings)):",
        "if any(is_loopback_host(host) for host in entry.hosts(settings)):",
        HOST_TEST, "test_one_bad_host_among_several_refuses_the_kind", "DID NOT RAISE"),
    mutant("S10 the config load does not ask the stand-in rule", CFG, "if problem := stand_in_host_problem(cap, kind, settings):", "if False:",
        HOST_TEST, "test_a_stand_in_on_another_computer_is_refused", "DID NOT RAISE"),
    mutant("S11 the refusal echoes the settings", CFG, '"(localhost or a loopback address); set a loopback host, or use a real kind"',
        '"(localhost or a loopback address); set a loopback host, or use a real kind" + repr(settings)',
        HOST_TEST, "test_the_refusal_never_echoes_the_host_or_other_setting_values", "echoes a setting value"),
    mutant("S12 the kind check is inverted: real kinds are refused", CFG, 'if entry.role != "stand_in" or entry.hosts is None:',
        'if entry.role == "stand_in" or entry.hosts is None:',
        HOST_TEST, "test_a_real_kind_may_name_any_host", "a real kind was refused"),
    mutant("S13 the loopback test is a prefix match", CFG, "is_loopback_host(host) for host", 'str(host).startswith("127") for host',
        HOST_TEST, "test_the_rule_agrees_with_is_loopback_host_on_seeded_random_hosts", "the rule disagrees with is_loopback_host"),
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
