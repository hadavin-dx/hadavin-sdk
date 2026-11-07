"""The mutants of the stage rename (named M1 to M10 with letter variants; there is no M7 or M11), run by the P1m runner (``tools/mutation_runner.py``).

They are NOT in ``tests/mutation_runner_mutants.py``: the meta-tests of that file pin its own mutants (the runner's and the
judge's) by count and by target file. Same runner, same judge, a separate list. Each mutant reverts ONE guard in a temp copy
of the package; the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment of the
assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/stage_mutants.py            # all mutants; exit 1 if any is not good
    python tests/stage_mutants.py M3         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_stage_names.py"
PIN = "tests/test_stage_names::"
CFG = "src/hadavin_sdk/config.py"
STG = "src/hadavin_sdk/stages.py"
TBL = "src/hadavin_sdk/backends/table.py"
DEFERRED = "src/hadavin_sdk/deferred.py"
REGISTRY = "src/hadavin_sdk/registry.py"
APP = "src/hadavin_sdk/app.py"
REDACT = "src/hadavin_sdk/guard/redact.py"
OLD = "d" + "ev"  # built from parts: this file is scanned by the class test it helps to check
RAISE = (
    "            raise _RenamedStage(\n"
    '                f"environment: {_OLD_STAGE} was renamed to {STAGES[0]}; write environment: {STAGES[0]} "\n'
    "                f\"(allowed values: {', '.join(STAGES)})\"\n"
    "            )"
)


def mutant(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


def pair(cap, kind):
    return mutant(
        f"M3 {cap}/{kind} dropped from DEMO_ONLY",
        TBL,
        f'        ("{cap}", "{kind}"),\n',
        "",
        "test_demo_only_is_exactly_the_six_pairs",
        "assert frozenset",
    )


M = [
    mutant("M1 the old word is accepted (mapped to demo)", CFG, RAISE, '            return "demo"',
        "test_dev_is_refused_with_the_rename", "DID NOT RAISE"),
    mutant("M2 the refusal does not name the rename", CFG, "was renamed to", "is not known to",
        "test_dev_is_refused_with_the_rename", "the refusal does not name the rename"),
    pair("llm", "fake"), pair("channel", "fake"), pair("secrets", "fake"),
    pair("secrets", "env"), pair("store", "memory"), pair("audit", "local_dir"),
    mutant("M2b pydantic's wrapper shows around the rename sentence", CFG, "    if not renamed:",
        "    if True:", "test_dev_is_refused_with_the_rename", "wrapper is visible"),
    mutant("M4a the demo-only check still tests the old word", CFG, "        if live:\n            refused = [",
        f'        if self.environment != "{OLD}":\n            refused = [', "test_demo_accepts_every_demo_only_kind", "demo config was refused"),
    mutant("M4b demo joins the live stages (registry.py: if True)", REGISTRY, "if is_live(config.environment):", "if True:",
        "test_the_stages_are_exactly_demo_pilot_prod", "demo is not live"),
    mutant("M4c pilot leaves the live stages (deferred.py)", DEFERRED, "live = is_live(cfg.environment)", 'live = cfg.environment == "prod"',
        "test_the_stages_are_exactly_demo_pilot_prod", "pilot is live"),
    mutant("M4f demo joins the live stages (deferred.py: live = True)", DEFERRED, "live = is_live(cfg.environment)", "live = True",
        "test_the_stages_are_exactly_demo_pilot_prod", "demo is not live"),
    mutant("M4g every stage is relaxed (app.py: live = False)", APP, "live = is_live(cfg.environment)", "live = False",
        "test_the_stages_are_exactly_demo_pilot_prod", "pilot is live"),
    mutant("M4h is_live becomes an allowlist of live stages", STG, "return environment != STAGES[0]", "return environment in STAGES[1:]",
        "test_the_stages_are_exactly_demo_pilot_prod", "is_live is wrong for a value that is not a stage"),
    mutant("M4i is_prod becomes False", STG, "return environment not in STAGES[:2]", "return False",
        "test_the_stages_are_exactly_demo_pilot_prod", "is_prod is wrong for a stage"),
    mutant("M4j is_prod becomes an allowlist of prod", STG, "return environment not in STAGES[:2]", "return environment == STAGES[2]",
        "test_the_stages_are_exactly_demo_pilot_prod", "is_prod is wrong for a value that is not a stage"),
    mutant("M4k the prod-only rules go back to string equality (config.py)", CFG, "    if is_prod(environment):", '    if environment == "prod":',
        "test_a_value_that_is_not_a_stage_gets_the_prod_only_rules", "no prod-only rule applied"),
    mutant("M4l the prod-only rules are switched off (config.py)", CFG, "    if is_prod(environment):", "    if False:",
        "test_a_value_that_is_not_a_stage_gets_the_prod_only_rules", "the case must be refused in prod"),
    mutant("M4m COMPLIANCE is allowed for a value that is not a stage", CFG, "environment in STAGES and is_prod(environment)", "is_prod(environment)",
        "test_a_value_that_is_not_a_stage_gets_the_prod_only_rules", "COMPLIANCE was allowed outside the three stages"),
    mutant("M4n COMPLIANCE is refused in prod too", CFG, "environment in STAGES and is_prod(environment)", "False",
        "test_a_value_that_is_not_a_stage_gets_the_prod_only_rules", "prod refused COMPLIANCE"),
    mutant("M4d the demo-only refusal is switched off", CFG, "        if live:\n            refused = [", "        if False:\n            refused = [",
        "test_pilot_and_prod_refuse_every_relaxed_kind", "DID NOT RAISE"),
    mutant("M4e the loopback switch is allowed in pilot and prod", CFG,
        'refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []',
        "refused += []", "test_pilot_and_prod_refuse_every_relaxed_kind", "did not refuse allow_insecure_loopback"),
    mutant("M5 the stage is compared by label (case and spaces tidied)", CFG, "            )\n        return value",
        "            )\n        return value.strip().lower() if isinstance(value, str) else value",
        "test_values_are_compared_exactly_never_normalised", "was accepted"),
    mutant("M5b the stage is tidied with NFKC, casefold and strip", CFG, "            )\n        return value",
        "            )\n"
        "        return __import__('unicodedata').normalize('NFKC', value).casefold().strip() if isinstance(value, str) else value",
        "test_values_are_compared_exactly_never_normalised", "was accepted"),
    mutant("M5c Dev and DEV get no rename sentence", CFG, "value.strip().casefold() == _OLD_STAGE", "value == _OLD_STAGE",
        "test_values_are_compared_exactly_never_normalised", "refused for another reason"),
    mutant("M5d the rename sentence hides the other problems in the file", CFG, '"; ".join([*(str(r) for r in renamed), *others])',
        "str(renamed[0])", "test_dev_is_refused_with_the_rename", "hidden by the rename sentence"),
    mutant("M6 the old word comes back in src", TBL, "kinds allowed only in `demo`.", f"kinds allowed only in `{OLD}`.",
        "test_the_old_stage_word_is_gone", "the old stage word is still used as a stage"),
    mutant("M6b the old word comes back in src as a quoted value", TBL, "NOT_PROD: frozenset[tuple[str, str]] = frozenset(",
        f'_STAGE_DEFAULT = "{OLD}"\nNOT_PROD: frozenset[tuple[str, str]] = frozenset(',
        "test_the_old_stage_word_is_gone", "the old stage word is still used as a stage"),
    mutant("M6c a sibling word comes back in src as a quoted value", TBL, "NOT_PROD: frozenset[tuple[str, str]] = frozenset(",
        '_STAGE_DEFAULT = "stag' + 'ing"\nNOT_PROD: frozenset[tuple[str, str]] = frozenset(',
        "test_the_old_stage_word_is_gone", "the old stage word is still used as a stage"),
    mutant("M8 a half-renamed flag: the old name stays beside the new", TBL,
        "NOT_PROD: frozenset[tuple[str, str]] = frozenset(", "DE" + "V_ONLY = DEMO_ONLY\nNOT_PROD: frozenset[tuple[str, str]] = frozenset(",
        "test_no_old_spelling_of_the_demo_only_flag_is_left", "half-renamed"),
    mutant("M9a registry.py goes back to an allowlist of live stages", REGISTRY, "is_live(config.environment)",
        'config.environment in ("pilot", "prod")',
        "test_a_value_that_is_not_a_stage_is_live_for_every_guard", "registry treated"),
    mutant("M9b deferred.py goes back to an allowlist of live stages", DEFERRED, "live = is_live(cfg.environment)",
        'live = cfg.environment in ("pilot", "prod")',
        "test_a_value_that_is_not_a_stage_is_live_for_every_guard", "deferred treated"),
    mutant("M9c app.py goes back to an allowlist of live stages", APP, "live = is_live(cfg.environment)",
        'live = cfg.environment in ("pilot", "prod")',
        "test_a_value_that_is_not_a_stage_is_live_for_every_guard", "app treated"),
    mutant("M10a pilot dropped from the redactor's common words", REDACT, '        "pilot",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "pilot is swept"),
    mutant("M10b demo dropped from the redactor's common words", REDACT, '        "demo",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "demo is swept"),
    mutant("M10c prod dropped from the redactor's common words", REDACT, '        "prod",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "prod is swept"),
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
        [TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
