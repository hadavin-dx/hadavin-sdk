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
TENANT_TEST = "tests/test_tenant_ids.py"
TENANT_PIN = "tests/test_tenant_ids::"
CFG = "src/hadavin_sdk/config.py"
STG = "src/hadavin_sdk/stages.py"
TBL = "src/hadavin_sdk/backends/table.py"
DEFERRED = "src/hadavin_sdk/deferred.py"
REGISTRY = "src/hadavin_sdk/registry.py"
APP = "src/hadavin_sdk/app.py"
REDACT = "src/hadavin_sdk/guard/redact.py"
COMMON = "src/hadavin_sdk/commonwords.py"
FURTHER = (
    "te" + "st",
    "develop" + "ment",
    "pro" + "duction",
)  # built from parts: the scan reads this file
SW_OLD = 'STAGE_WORDS = (*STAGES, "{}", "{}", "{}")'.format(*FURTHER)
SW_DROP = f'STAGE_WORDS = (*STAGES, "{FURTHER[0]}", "{FURTHER[2]}")'
SW_ADD = 'STAGE_WORDS = (*STAGES, "{}", "{}", "{}", "uat")'.format(*FURTHER)
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


def tenant(name, file, old, new, killer, expect):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=TENANT_TEST,
        only_test=killer,
        pinned=TENANT_PIN + killer,
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
    mutant("M4a the demo-only check still tests the old word", CFG, "if is_live(self.environment):",
        f'if self.environment != "{OLD}":', "test_demo_accepts_every_demo_only_kind", "demo config was refused"),
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
    mutant("M4d the demo-only refusal is switched off", CFG, "if is_live(self.environment):", "if False:",
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
    mutant("M10a pilot dropped from the redactor's common words", COMMON, '        "pilot",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "pilot is swept"),
    mutant("M10b demo dropped from the redactor's common words", COMMON, '        "demo",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "demo is swept"),
    mutant("M10c prod dropped from the redactor's common words", COMMON, '        "prod",\n', "",
        "test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names", "prod is swept"),
    tenant("T1 the id fold does not case-fold", STG, "kept.casefold().strip()", "kept.strip()",
        "test_an_id_spelled_like_a_stage_is_refused", "was not read as a stage name"),
    tenant("T2 the id fold does not cut white space", STG, "kept.casefold().strip()", "kept.casefold()",
        "test_an_id_spelled_like_a_stage_is_refused", "was not read as a stage name"),
    tenant("T3 the id fold does not apply NFKC", STG, 'unicodedata.normalize("NFKC", value)', "value",
        "test_an_id_spelled_like_a_stage_is_refused", "was not read as a stage name"),
    tenant("T4 the id fold keeps invisible format characters", STG, 'unicodedata.category(c) != "Cf"', "True",
        "test_an_id_spelled_like_a_stage_is_refused", "was not read as a stage name"),
    tenant("T5 pilot is not a stage name for an id", STG, "fold_name(value) in STAGES", "fold_name(value) in (STAGES[0], STAGES[2])",
        "test_an_id_spelled_like_a_stage_is_refused", "was not read as a stage name"),
    tenant("T6 the stage-word refusal is off (the common-word one still refuses, with another sentence)", STG, "        if folded in STAGE_WORDS:\n", "        if False:\n",
        "test_an_id_spelled_like_a_stage_is_refused", "without the stage-word sentence"),
    tenant("T6b the id check refuses nothing", STG, "        folded = fold_name(value)\n", '        folded = ""\n',
        "test_an_id_spelled_like_a_stage_is_refused", "was accepted as a tenant id"),
    tenant("T7 the stage predicate reads a word that merely contains a stage name", STG, "fold_name(value) in STAGES", "any(s in fold_name(value) for s in STAGES)",
        "test_an_id_that_is_not_a_refused_word_is_accepted_unchanged", "was read as a stage name"),
    tenant("T7b the id check refuses a word that merely contains a refused word", STG, "        if folded in REFUSED_ID_WORDS:\n", "        if any(w in folded for w in REFUSED_ID_WORDS):\n",
        "test_an_id_that_is_not_a_refused_word_is_accepted_unchanged", "although it is an ordinary word"),
    tenant("T8 an id that is not a string is accepted", STG, '    raise ValueError(f"{label} must be a string")\n', "    return value\n",
        "test_an_id_that_is_not_a_string_is_refused_with_a_value_error", "although it is not a string"),
    tenant("T9 the stage-word refusal echoes the value", STG, 'f"{label} may not be a stage word (', 'f"{label} {value} may not be a stage word (',
        "test_the_refusal_names_the_stage_words_and_the_fold_and_does_not_echo_the_value", "the refusal echoes the value"),
    tenant("T10 the tenant type does not call the check", CFG, "AfterValidator(check_tenant_id)", "AfterValidator(lambda v: v)",
        "test_the_config_type_refuses_a_stage_word_with_a_validation_error", "the config type accepted"),
    tenant("T10b the org id type does not call the check", CFG, 'OrgId = Annotated[str, AfterValidator(partial(check_id, label="an org id"))]',
        "OrgId = Annotated[str, AfterValidator(lambda v: v)]",
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "DID NOT RAISE"),
    tenant("T11 the id fold composes differently from the redactor (NFKD, not NFKC)", STG, 'unicodedata.normalize("NFKC", value)', 'unicodedata.normalize("NFKD", value)',
        "test_the_fold_is_the_redactors_canonical_form_then_casefolded_then_cut", "differs from the redactor"),
    tenant("T12 the walk accepts a field of any type", TENANT_TEST, "                elif not is_id_type(node.annotation):\n", "                elif False:\n",
        "test_the_walk_sees_each_kind_of_unchecked_id", "missed a field of the wrong type"),
    tenant("T13 the walk ignores function and lambda parameters", TENANT_TEST, "        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):", "        if False:",
        "test_the_walk_sees_each_kind_of_unchecked_id", "missed an unchecked parameter"),
    tenant("T14 an id field planted in src escapes the walk", "src/hadavin_sdk/identity.py", "    id: str\n", "    id: str\n    tenant_id: str = \"\"\n",
        "test_every_id_field_in_the_package_goes_through_the_check", "is not an id type"),
    tenant("T15 is_stage_name loses its isinstance test", STG, "    return isinstance(value, str) and fold_name(value) in STAGES", "    return fold_name(value) in STAGES",
        "test_an_id_that_is_not_a_string_is_refused_with_a_value_error", "is_stage_name raises on a non-string"),
    tenant("T15b the walk matches the annotation as a substring", TENANT_TEST, "        return _last_name(ann) in ID_TYPES\n", '        return "TenantId" in ast.unparse(ann)\n',
        "test_the_walk_sees_each_kind_of_unchecked_id", "the walk accepted the annotation"),
    tenant("T16 the parameter-body check is dropped", TENANT_TEST, "                    and not calls_check_on(node, arg.arg)\n", "                    and False\n",
        "test_the_walk_sees_each_kind_of_unchecked_id", "missed an unchecked parameter"),
    tenant("T16b redact.py keeps a copy of the word list", REDACT, "_COMMON = COMMON_WORDS\n", "_COMMON = frozenset(set(COMMON_WORDS))\n",
        "test_the_redactor_and_the_id_check_use_one_word_list", "the redactor has a list of its own"),
    tenant("T17 the common-word refusal is off", STG, "        if folded in REFUSED_ID_WORDS:\n", "        if False:\n",
        "test_every_common_word_is_refused_as_an_id_in_every_spelling", "was accepted as an id"),
    tenant("T18 the common-word refusal echoes the value", STG, 'f"{label} may not be a common word that the redactor', 'f"{label} {value} may not be a common word that the redactor',
        "test_the_refusal_names_the_stage_words_and_the_fold_and_does_not_echo_the_value", "the refusal echoes the value"),
    tenant("T19 a further stage word is dropped from STAGE_WORDS", STG, SW_OLD, SW_DROP,
        "test_the_further_stage_words_are_refused_as_ids", "was accepted as a tenant id"),
    tenant("T20 STAGE_WORDS gets a word the stage scan does not know", STG, SW_OLD, SW_ADD,
        "test_the_stage_words_are_the_stages_and_the_words_the_stage_scan_looks_for", "differ from the stage scan"),
    tenant("T21 the customer id type carries the wrong label", CFG, 'partial(check_id, label="a customer id")', 'partial(check_id, label="a user id")',
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "the error does not start with"),
    tenant("T21b the account id type carries the wrong label", CFG, 'partial(check_id, label="an account id")', 'partial(check_id, label="a customer id")',
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "the error does not start with"),
    tenant("T21c the user id type carries the wrong label", CFG, 'partial(check_id, label="a user id")', 'partial(check_id, label="an account id")',
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "the error does not start with"),
    tenant("T21d the account id type is not checked at all", CFG, 'AccountId = Annotated[str, AfterValidator(partial(check_id, label="an account id"))]', "AccountId = str",
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "DID NOT RAISE"),
    tenant("T21e the user id type is not checked at all", CFG, 'UserId = Annotated[str, AfterValidator(partial(check_id, label="a user id"))]', "UserId = str",
        "test_each_other_id_type_refuses_a_common_word_and_a_stage_word", "DID NOT RAISE"),
    tenant("T28 the common word default is dropped from commonwords.py", COMMON, '        "default",\n', "",
        "test_the_refused_words_are_exactly_these_twenty_nine", "differ from the expected list"),
    tenant("T28b the common word admin is dropped from commonwords.py", COMMON, '        "admin",\n', "",
        "test_the_refused_words_are_exactly_these_twenty_nine", "differ from the expected list"),
    tenant("T28c a word is added to commonwords.py", COMMON, '        "default",\n', '        "default",\n        "staging2",\n',
        "test_the_refused_words_are_exactly_these_twenty_nine", "differ from the expected list"),
    tenant("T23 the walk accepts a check on another parameter", TENANT_TEST, "isinstance(a, ast.Name) and a.id == param for a in args", "isinstance(a, ast.Name) for a in args",
        "test_the_walk_sees_each_kind_of_unchecked_id", "accepted a check on another parameter"),
    tenant("T24 the walk ignores attribute assignments", TENANT_TEST, "                    and isinstance(target, ast.Attribute)\n", "                    and False\n",
        "test_the_walk_sees_each_kind_of_unchecked_id", "missed an attribute assignment"),
    tenant("T25 the walk ignores class-level assignments", TENANT_TEST, "                        and target.id not in ID_TYPES\n", "                        and False\n",
        "test_the_walk_sees_each_kind_of_unchecked_id", "missed an assigned field"),
    tenant("T26 the walk does not require a _Strict base", TENANT_TEST, '        if holds and "_Strict" not in', '        if False and "_Strict" not in',
        "test_the_walk_sees_each_kind_of_unchecked_id", "accepted a model that echoes input"),
    mutant("T27 the exemption budget collapses duplicate rows", "tests/test_stage_names.py", "    return collections.Counter((f, line) for f, line, _ in rows)\n",
        "    return collections.Counter({(f, line) for f, line, _ in rows})\n",
        "test_a_duplicate_row_excuses_exactly_two_real_occurrences", "no duplicate rows"),
    mutant("T27b the stale check compares entries, not counts", "tests/test_stage_names.py", "    if used != budget:\n", "    if set(used) != set(budget):\n",
        "test_the_stale_check_sees_a_spare_duplicate_row_and_a_missing_row", "a spare duplicate row went unseen"),
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
        [TEST, TENANT_TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
