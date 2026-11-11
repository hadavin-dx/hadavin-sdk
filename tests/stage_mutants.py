"""The mutants of the stage rename (named M1 to M13 with letter variants; there is no M7 or M11), run by the P1m runner (``tools/mutation_runner.py``).

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
TICK = "src/hadavin_sdk/runtime/tick.py"
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


OBJECT = "test_pilot_and_prod_refuse_a_test_object_handed_to_build"
VAULT = "test_pilot_and_prod_refuse_a_static_vault_token"
TICK_TEST = "test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick"
STEPS_TEST = "test_pilot_and_prod_refuse_a_tick_whose_step_list_lacks_a_built_in_step"
TIMEOUT_TEST = "test_demo_refuses_a_timeout_that_is_out_of_range"
RAISE_VAULT = (
    "    if live and (static := _static_vault_tokens(b)):\n"
    "        # Before any backend is built: the token is never read from the environment of this process.\n"
    "        raise ConfigError(f\"environment {cfg.environment}: refused: {', '.join(static)}\")\n"
)
MAKE_SECRETS = '    if secrets is None:\n        secrets = make("secrets", b.secrets)\n'
VAULT_FIRST, SECRETS_FIRST = RAISE_VAULT + MAKE_SECRETS, MAKE_SECRETS + RAISE_VAULT


def dropped(name, expect):
    return mutant(
        f"M12d {name} dropped from the six keywords (app.py)",
        APP,
        f'            ("{name}", {name}),\n',
        "",
        OBJECT,
        expect,
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
    mutant("M12a a live build takes a test object (app.py: the refusal of the six keywords is switched off)", APP, "if live and given:", "if False:",
        OBJECT, "a live build took a test object"),
    mutant("M12b a static Vault token is allowed in pilot and prod (app.py: the check never matches)", APP,
        'isinstance(s, VaultConnection) and s.auth == "token"', "False",
        VAULT, "a static Vault token was accepted"),
    mutant("M12c the six keywords are tested for truth, not for being given (app.py)", APP, "if value is not None\n", "if value\n",
        OBJECT, "a live build took a falsy test object"),
    dropped("secrets", "a live build took the keyword secrets="), dropped("channel", "a live build took a test object"),
    dropped("detector", "a live build took the keyword detector="), dropped("llm", "a live build took the keyword llm="),
    dropped("clock", "a live build took the keyword clock="), dropped("timeout_s", "a live build took the keyword timeout_s="),
    mutant("M12f the Vault check is narrowed to the secrets kind (app.py)", APP,
        "isinstance(s, VaultConnection) and", 'type(s).__name__ == "VaultSettings" and',
        VAULT, "a static Vault token was accepted for signer"),
    mutant("M12g the Vault check runs in prod only (app.py)", APP, "if live and (static := _static_vault_tokens(b)):",
        'if cfg.environment == "prod" and (static := _static_vault_tokens(b)):',
        VAULT, "a static Vault token was accepted for secrets (pilot"),
    mutant("M12h the Vault check goes back to the two kind names (app.py)", APP,
        "isinstance(s, VaultConnection)", 's.kind in ("vault", "vault_transit")',
        VAULT, "a static Vault token was accepted for a new kind built on the Vault settings"),
    mutant("M12i the Vault check is widened to every sign-in but kubernetes (app.py)", APP,
        's.auth == "token"', 's.auth != "kubernetes"',
        VAULT, "a Vault sign-in that is not a static token was refused (approle)"),
    mutant("M12j the Vault check runs after the secrets backend is made (app.py)", APP, VAULT_FIRST, SECRETS_FIRST,
        VAULT, "a backend was made before the Vault refusal"),
    mutant("M12k sources= is tested for truth, not for being given (app.py)", APP, "if sources is not None and live:", "if sources and live:",
        "test_pilot_and_prod_refuse_sources_and_tools_handed_to_build", "a live build took sources= ('pilot', _FalsyDict"),
    mutant("M12l tools= is tested for truth, not for being given (app.py)", APP, "if tools is not None and live:", "if tools and live:",
        "test_pilot_and_prod_refuse_sources_and_tools_handed_to_build", "a live build took tools= ('pilot', _FalsyDict"),
    mutant("M12m the timeout_s= keyword is not checked against the timeout rule (app.py)", APP,
        "if timeout_s is not None and not executor_timeout_ok(timeout_s):", "if False:",
        TIMEOUT_TEST, "demo took timeout_s=0"),
    mutant("M12n the executor timeout has no upper bound (config.py)", CFG,
        "return defaults.EXECUTOR_TIMEOUT_MIN_S <= value <= defaults.EXECUTOR_TIMEOUT_MAX_S", "return defaults.EXECUTOR_TIMEOUT_MIN_S <= value",
        TIMEOUT_TEST, "demo took timeout_s=inf"),
    mutant("M12o True and False count as an executor timeout (config.py)", CFG,
        "if isinstance(value, bool) or not isinstance(value, int | float):", "if not isinstance(value, int | float):",
        TIMEOUT_TEST, "demo took timeout_s=True"),
    mutant("M12p the config field of the executor timeout is not checked against the rule (config.py)", CFG,
        "if not executor_timeout_ok(value):", "if False:",
        TIMEOUT_TEST, "the config took executor_timeout_s: 3600.1"),
    mutant("M12r the executor timeout has no lower bound above 0 (config.py)", CFG,
        "return defaults.EXECUTOR_TIMEOUT_MIN_S <= value <= defaults.EXECUTOR_TIMEOUT_MAX_S", "return 0 < value <= defaults.EXECUTOR_TIMEOUT_MAX_S",
        TIMEOUT_TEST, "demo took timeout_s=1e-09"),
    mutant("M13a run_tick's own refusal is switched off: a step list is taken, a time is still refused by the context (tick.py)", TICK,
        "if given and live:", "if False:",
        TICK_TEST, "a live tick took a step list handed to it"),
    mutant("M13b the tick refuses a handed time in demo too (tick.py)", TICK,
        "if given and live:", "if given:",
        TICK_TEST, "demo refused a time handed to the tick"),
    mutant("M13c steps dropped from the two keywords of the tick (tick.py)", TICK,
        '(("now", now), ("steps", steps))', '(("now", now),)',
        TICK_TEST, "a live tick took a step list handed to it"),
    mutant("M13d the two keywords of the tick are tested for truth (tick.py)", TICK,
        '(("now", now), ("steps", steps)) if value is not None', '(("now", now), ("steps", steps)) if value',
        TICK_TEST, "a live tick took an empty step list"),
    mutant("M13e a live tick runs without a built-in step (tick.py: the check is switched off)", TICK,
        "if live and (missing := _missing_built_in_steps()):", "if False:",
        STEPS_TEST, "a live tick ran without a built-in step"),
    mutant("M13f the built-in step check runs in demo too (tick.py)", TICK,
        "if live and (missing := _missing_built_in_steps()):", "if missing := _missing_built_in_steps():",
        STEPS_TEST, "demo did not run the list as it is"),
    mutant("M13g the built-in step check compares the count, not the names (tick.py)", TICK,
        "return [name for name in _BUILT_IN if name not in present]", "return [] if present else list(_BUILT_IN)",
        STEPS_TEST, "a live tick ran without a built-in step"),
    mutant("M13h a live tick context takes a time handed to it (tick.py)", TICK,
        "elif is_live(self.app.config.environment):", "elif False:",
        TICK_TEST, "a live tick step took a time handed to its context"),
    mutant("M13i a live tick step takes a stand-in context with a time (tick.py)", TICK,
        "if type(ctx) is not TickContext and is_live(ctx.app.config.environment):", "if False:",
        TICK_TEST, "a live tick step took a stand-in context with a time"),
    mutant("M13k a live tick step takes any object that says it is a TickContext (tick.py: isinstance again)", TICK,
        "if type(ctx) is not TickContext and is_live(ctx.app.config.environment):",
        "if not isinstance(ctx, TickContext) and is_live(ctx.app.config.environment):",
        TICK_TEST, "a live tick step took a Mock(spec=TickContext)"),
    mutant("M13l TickContext can be subclassed again (tick.py)", TICK,
        '        raise TypeError(\n            "TickContext cannot be subclassed', '        return print(\n            "TickContext cannot be subclassed',
        TICK_TEST, "a subclass of TickContext was allowed"),
    mutant("M13m a live tick runs a step list with a name used twice (tick.py: the check is switched off)", TICK,
        "if live and (repeated := _repeated_step_names()):", "if False:",
        STEPS_TEST, "a live tick ran a step list with a name used twice"),
    mutant("M13n the repeated-name check finds nothing (tick.py)", TICK,
        "        if step.name in seen and step.name not in repeated:", "        if False:",
        STEPS_TEST, "a live tick ran a step list with a name used twice"),
    mutant("M13j the tick context refuses a handed time in demo too (tick.py)", TICK,
        "elif is_live(self.app.config.environment):", "else:",
        TICK_TEST, "demo refused a time handed to the tick"),
    mutant("M9e the tick context goes back to an allowlist of live stages (tick.py)", TICK,
        "is_live(self.app.config.environment)", 'self.app.config.environment in ("pilot", "prod")',
        TICK_TEST, "the tick context treated"),
    mutant("M9f the tick step's stand-in check goes back to an allowlist of live stages (tick.py)", TICK,
        "is_live(ctx.app.config.environment)", 'ctx.app.config.environment in ("pilot", "prod")',
        TICK_TEST, "the tick step treated"),
    mutant("M9d tick.py goes back to an allowlist of live stages", TICK, "is_live(app.config.environment)",
        'app.config.environment in ("pilot", "prod")',
        TICK_TEST, "the tick treated"),
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
