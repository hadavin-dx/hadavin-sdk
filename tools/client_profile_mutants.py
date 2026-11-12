"""Hand-made mutants for the client-profile check (made-up code only, no model calls, no spend).

What it does: it plants one small change at a time into the source of a throw-away copy of this repository
(a detached git worktree of HEAD in a temp folder, never the folder you run it from), runs the tests that should
notice, and restores the file in `finally`. A mutant is KILLED when a test FAILS. A collection or import error is
reported as ERROR and is not a kill. Each mutant is numbered by its place in the list.

How to run: `python tools/client_profile_mutants.py` from a virtual environment with the test extras. Commit your
changes first (the copy is made from HEAD). MUTANT_ONLY=1,2 picks mutants; MUTANT_PYTHON names the Python;
MUTANT_TIMEOUT_S bounds one test run in seconds. The baseline run (unmutated) covers every test file that any
mutant names, so a mutant is never judged against tests the baseline did not run. Each mutant names the test (a
regular expression that must name the test file and the test function and end at the function name or at the start
of its parameter list, so no other file's test and no longer name can match) that should kill it; "KILLED-NAMED" means that test failed.
The tests run with no cloud settings: the runner refuses to start when a cloud or model-provider variable is set in
its own environment, and gives the tests only a short list of plain variables. Exit code 0 only if every mutant was
located and killed by its named test: a mutant killed only by some other test (KILLED-OTHER) is a failure, and the
runner refuses to start when a named killer is not anchored like that (see `killer_problems`). A run of only some
mutants (MUTANT_ONLY) is marked PARTIAL RUN and exits non-zero, whatever its result.
"""

from __future__ import annotations

import asyncio
import atexit
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent.parent
PY = os.environ.get("MUTANT_PYTHON", sys.executable)
TIMEOUT_S = int(os.environ.get("MUTANT_TIMEOUT_S", "300"))
WT = Path("/nonexistent-set-by-main")
GIT = shutil.which(
    "git"
)  # one absolute path, found once; a missing git is a stated failure in main()
ONLY = {int(x) for x in os.environ.get("MUTANT_ONLY", "").split(",") if x}

CP = "tests/test_client_profile.py"
P1B = "tests/test_p1b_backends.py"
K9B = "tests/test_k5_round9b.py::test_a_live_deployment_without_the_key_does_not_start"
K10 = "tests/test_k5_round10.py::test_a_live_postgres_deployment_without_a_purge_dsn_does_not_start"

APP = "src/hadavin_sdk/app.py"
CFG = "src/hadavin_sdk/config.py"
TAB = "src/hadavin_sdk/backends/table.py"

S2_GIVEN = "_test_doubles_given(_BUILD_PARAMS, given) if live else []"
S2_SWITCH = "    if live_doubles and allow_test_doubles is True:\n"
S2_LOG = (
    "        # A client app that starts with test objects must leave a trace in the log (names only, no values).\n"
    "        _LOG.warning(\n"
)
S2_RAISE = "    elif live_doubles:\n"
GIVEN_LINE = "    given = dict(locals())\n"
S6_FLAG = '            ["made_up_data_only (for demo configs only)"] if live and self.made_up_data_only else []\n'
S6_IF = "        if not live and not self.made_up_data_only:\n"
OWN = '_OWN_REFUSAL = ("sources", "tools")\n'
LLM_LINE = '    out = [f"llm: {b.llm.kind}"] if ("llm", b.llm.kind) not in DEMO_ONLY else []\n'
DET_LINE = (
    '    out += [f"detector: {d.kind}" for d in b.detector if d.kind not in LOCAL_DETECTORS]\n'
)
CHAN_LINE = '    out += [f"channel: {b.channel.kind}"] if ("channel", b.channel.kind) not in DEMO_ONLY else []\n'
S2_MSG = "            f\"{', '.join(f'{n}=' for n in live_doubles)} replace configured parts and are for tests; \"\n"
SIG = "    timeout_s: float | None = None,\n    allow_test_doubles: bool = False,\n"
BLOCK_START = "    # Before any backend is built, so a refusal reads no secret"
BLOCK_END = '            "only from a test"\n        )\n'


# Settings that point a test at a cloud account or a model provider. The runner refuses to start when one is set in
# its own environment, and a test run gets only PLAIN_ENV (so no such setting, and no proxy, reaches a test).
# Prefixes and where each vendor documents them (from the vendors' SDK and CLI documentation; not re-fetched when
# this list was last changed):
#   AWS_ (AWS SDKs and CLI environment variables: AWS_ACCESS_KEY_ID, AWS_PROFILE, ...), BOTO_ (boto's BOTO_CONFIG
#   and BOTO_PATH), AZURE_ (Azure SDK EnvironmentCredential: AZURE_CLIENT_ID, AZURE_TENANT_ID, ...), ARM_ (the
#   Azure Resource Manager variables ARM_CLIENT_ID and others read by Terraform's azurerm provider), MSI_ and
#   IDENTITY_ (the managed-identity endpoints MSI_ENDPOINT, MSI_SECRET, IDENTITY_ENDPOINT, IDENTITY_HEADER of Azure
#   App Service and Functions), GOOGLE_ (Application Default Credentials: GOOGLE_APPLICATION_CREDENTIALS), GCLOUD_
#   and GCP_ (project settings such as GCLOUD_PROJECT), CLOUDSDK_ (the gcloud CLI), OCI_ (the Oracle Cloud SDK and
#   CLI), VAULT_ (VAULT_ADDR, VAULT_TOKEN), and one prefix for each model provider the repository has a kind for.
CLOUD_PREFIXES = (
    "AWS_",
    "BOTO_",
    "AZURE_",
    "ARM_",
    "MSI_",
    "IDENTITY_",
    "GOOGLE_",
    "GCLOUD_",
    "GCP_",
    "CLOUDSDK_",
    "OCI_",
    "VAULT_",
    "SLACK_",
    "CLOUDFLARE_",
    "PG",
    "ANTHROPIC_",
    "OPENAI_",
    "GEMINI_",
    "MISTRAL_",
    "COHERE_",
    "HADAVIN_TEST_",
)
# Also refused: SLACK_ (bot tokens), CLOUDFLARE_ (API tokens), PG (libpq: PGHOST, PGPASSWORD, PGSERVICE, ...) and, by
# exact name, DATABASE_URL and KUBECONFIG.
# What this does not do: it does not block the network (the tests run on this machine's network, so a cloud metadata
# address is reachable), and it does not hide credential files outside HOME (a file read by its absolute path).
# HOME is not passed: the SDKs also read credential files under it (~/.aws, ~/.azure, ~/.config/gcloud). A test
# run gets a new empty folder as HOME instead.
CLOUD_NAMES = ("DATABASE_URL", "KUBECONFIG")
PLAIN_ENV = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT")
_EMPTY_HOME: list[str] = []


def empty_home() -> str:
    """One empty temporary folder, made on first use and removed when the runner exits."""
    if not _EMPTY_HOME:
        folder = tempfile.mkdtemp(prefix="client-profile-mutants-home-")
        atexit.register(shutil.rmtree, folder, True)
        _EMPTY_HOME.append(folder)
    return _EMPTY_HOME[0]


def cloud_variables() -> list[str]:
    """Names (never values) of the variables in this process's environment that carry a cloud setting."""
    return sorted(
        k for k in os.environ if k.upper().startswith(CLOUD_PREFIXES) or k.upper() in CLOUD_NAMES
    )


def clean_env(**extra: str) -> dict[str, str]:
    """The environment a test run gets: PLAIN_ENV from this process, an empty HOME, plus `extra`."""
    env = {k: os.environ[k] for k in PLAIN_ENV if k in os.environ}
    # Linux and macOS read HOME; Windows reads USERPROFILE (and ignores HOME): both name the empty folder.
    env["HOME"] = env["USERPROFILE"] = empty_home()
    # One copy of the repository serves every mutant. Python keeps a compiled file when the source's size and
    # modification second are unchanged, so two same-size mutants planted in the same second could run the first
    # one's code. No compiled files are written, so there is nothing stale to read.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return env


class NotLocated(Exception):
    pass


def rep(old: str, new: str):
    def f(text: str) -> str:
        n = text.count(old)
        if n != 1:
            raise NotLocated(f"original text occurs {n} times (need exactly 1): {old[:70]!r}")
        return text.replace(old, new)

    return f


def move_block(anchor_re: str):
    """Cut the test-double rule block and paste it after the single line that matches anchor_re."""

    def f(text: str) -> str:
        if text.count(BLOCK_START) != 1 or text.count(BLOCK_END) != 1:
            raise NotLocated("test-double rule block start/end not found exactly once")
        a = text.index(BLOCK_START)
        b = text.index(BLOCK_END) + len(BLOCK_END)
        block = text[a:b]
        rest = text[:a] + text[b:]
        ms = list(re.finditer(anchor_re, rest, re.MULTILINE))
        if len(ms) != 1:
            raise NotLocated(f"anchor {anchor_re!r} occurs {len(ms)} times (need exactly 1)")
        e = ms[0].end()
        return rest[:e] + block + rest[e:]

    return f


# (number given in order, description, file to edit, mutation, test targets, expected killer regex or "")
DEF: list = []


def m(desc, path, mut, tests, killer=""):
    """Add a mutant; its number is its place in the list, so numbers never collide or leave gaps."""
    DEF.append((len(DEF) + 1, desc, path, mut, tests, killer))


_KILLER = re.compile(r"tests/\w+\.py::\w+(\$|\\\[.*)")


def _outside_groups(text: str) -> str:
    """`text` with every (...) group removed, innermost first."""
    while (shorter := re.sub(r"\([^()]*\)", "", text)) != text:
        text = shorter
    return text


def _killer_is_anchored(killer: str) -> bool:
    """A file path, then a test name, then the end (`$`) or the start of a parameter list (`\\[`), and no `|`
    outside a (...) group: so no other file's test and no longer test name can match, and no second branch."""
    return bool(_KILLER.fullmatch(killer)) and "|" not in _outside_groups(killer)


def killer_problems(rows=None) -> list[str]:
    """Killer regexes that are not anchored on the file and on the end of the test name. A killer is matched
    against the failing test's id (`tests/<file>.py::<name>[<parameters>]`)."""
    return [
        f"mutant {row[0]}: {row[5]!r}"
        for row in (DEF if rows is None else rows)
        if row[5] and not _killer_is_anchored(row[5])
    ]


for pair, kill in (
    (("llm", "fake"), "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$"),
    (("channel", "fake"), "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$"),
    (("secrets", "fake"), "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$"),
    (
        ("secrets", "env"),
        r"tests/test_client_profile.py::test_secrets_env_is_refused_in_a_client_profile\[",
    ),
    (
        ("store", "memory"),
        "tests/test_client_profile.py::test_a_pilot_config_that_omits_store_is_refused$",
    ),
    (
        ("audit", "local_dir"),
        "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$",
    ),
):
    m(
        f"DEMO_ONLY loses {pair[0]}/{pair[1]}",
        TAB,
        rep(f'        ("{pair[0]}", "{pair[1]}"),\n', ""),
        [CP, P1B],
        kill,
    )

m(
    'refusal only in prod (live -> == "prod")',
    CFG,
    rep(
        "        if live:\n            refused = [",
        '        if self.environment == "prod":\n            refused = [',
    ),
    [CP, P1B],
    "tests/test_client_profile.py::test_secrets_env_is_refused_in_a_client_profile\\[pilot\\]",
)
m(
    "message keeps only the first refusal",
    CFG,
    rep("{', '.join(refused)}{tail}", "{refused[0]}{tail}"),
    [CP, P1B],
    "tests/test_client_profile.py::test_three_refusals_come_in_one_error$",
)
m(
    "test-double rule check deleted",
    APP,
    rep(S2_RAISE, "    elif False:\n"),
    [CP],
    r"tests/test_client_profile.py::test_each_test_double_is_refused_alone\[",
)
m(
    "test-double rule looks only at llm",
    APP,
    rep(
        S2_GIVEN,
        '[n for n in _test_doubles_given(_BUILD_PARAMS, given) if n == "llm"] if live else []',
    ),
    [CP],
    "tests/test_client_profile.py::test_each_test_double_is_refused_alone\\[(channel|secrets|detector|clock)-",
)
m(
    "allow_test_doubles default True",
    APP,
    rep(SIG, SIG.replace("False", "True")),
    [CP],
    r"tests/test_client_profile.py::test_each_test_double_is_refused_alone\[",
)
m(
    "test-double rule only for prod",
    APP,
    rep(S2_GIVEN, '_test_doubles_given(_BUILD_PARAMS, given) if cfg.environment == "prod" else []'),
    [CP],
    "tests/test_client_profile.py::test_each_test_double_is_refused_alone\\[[a-z_]+-pilot\\]",
)
m(
    "sources not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("tools",)\n'),
    [CP],
    "tests/test_client_profile.py::test_sources_keeps_its_own_refusal$",
)
m(
    "tools not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("sources",)\n'),
    [CP],
    "tests/test_client_profile.py::test_tools_keeps_its_own_refusal$",
)
m(
    "compare by truth value, not identity",
    APP,
    rep(
        "        and given[name] is not p.default\n",
        "        and bool(given[name]) != bool(p.default)\n",
    ),
    [CP],
    "tests/test_client_profile.py::test_a_falsy_double_is_refused$",
)
m(
    "check placed after secrets = secrets or make()",
    APP,
    move_block(r'^    secrets = secrets or make\("secrets", b\.secrets\)\n'),
    [CP],
    "tests/test_client_profile.py::test_a_refusal_builds_nothing_first$",
)
m(
    "check placed after platform_secrets.check",
    APP,
    move_block(r"^    platform_secrets\.check\(.*\)\n"),
    [CP],
    "tests/test_client_profile.py::test_a_refusal_builds_nothing_first$",
)
m(
    "names from a fixed list of four",
    APP,
    rep(
        "        and name not in skip\n",
        '        and name not in skip\n        and name in ("secrets", "channel", "detector", "llm")\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_a_keyword_added_later_is_refused_by_default$",
)
m(
    "message names only the first keyword",
    APP,
    rep(S2_MSG, '            f"{live_doubles[0]}= replace configured parts and are for tests; "\n'),
    [CP],
    "tests/test_client_profile.py::test_all_at_once_names_all_in_signature_order$",
)
m(
    "switch ignored",
    APP,
    rep(S2_SWITCH, "    if False:\n"),
    [CP, K9B, K10],
    "tests/test_client_profile.py::test_the_switch_lets_a_test_double_through$",
)
m(
    "_LIVE_HOOKS gains llm",
    APP,
    rep(
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s")',
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s", "llm")',
    ),
    [CP],
    "tests/test_client_profile.py::test_each_test_double_is_refused_alone\\[llm-",
)
m(
    "_LIVE_HOOKS ignored",
    APP,
    rep(
        '    skip = {"allow_test_doubles", *_OWN_REFUSAL, *_LIVE_HOOKS}\n',
        '    skip = {"allow_test_doubles", *_OWN_REFUSAL}\n',
    ),
    [CP],
    r"tests/test_client_profile.py::test_the_live_hooks_need_no_switch\[",
)
m(
    "door scan: keyword branch deleted",
    CP,
    rep('                if kw.arg == "allow_test_doubles":\n', "                if False:\n"),
    [CP],
    "tests/test_client_profile.py::test_planted_doors_are_reported\\[direct\\]",
)
m(
    "door scan: keyword only in calls named build",
    CP,
    rep(
        '                if kw.arg == "allow_test_doubles":\n',
        '                if kw.arg == "allow_test_doubles" and name == "build":\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_planted_doors_are_reported\\[partial\\]",
)
m(
    "door scan: ** branch deleted",
    CP,
    rep('                if kw.arg is None and name == "build":\n', "                if False:\n"),
    [CP],
    "tests/test_client_profile.py::test_planted_doors_are_reported\\[double_star\\]",
)
m(
    "decided-pairs check: both-sets not reported",
    CP,
    rep("        for c, k in sorted(demo_only & set(reviewed))\n", "        for c, k in []\n"),
    [CP],
    "tests/test_client_profile.py::test_planted_pair_in_both_sets_is_reported$",
)
m(
    "decided-pairs check: empty reason not reported",
    CP,
    rep(
        "for (c, k), why in sorted(reviewed.items()) if not why.strip()]",
        "for (c, k), why in sorted(reviewed.items()) if False]",
    ),
    [CP],
    "tests/test_client_profile.py::test_planted_empty_reason_is_reported$",
)
m(
    "decided-pairs check: neither-set not reported",
    CP,
    rep(
        "        for c, k in sorted(pairs - demo_only - set(reviewed))\n",
        "        for c, k in []\n",
    ),
    [CP],
    "tests/test_client_profile.py::test_planted_kind_in_neither_set_is_reported$",
)
m(
    "made-up-data rule items deleted",
    CFG,
    rep(S6_IF, "        if False:\n"),
    [CP],
    "tests/test_client_profile.py::test_a_real_llm_kind_in_demo_needs_the_field\\[",
)
m(
    "made-up-data rule runs in every stage",
    CFG,
    rep(S6_IF, "        if not self.made_up_data_only:\n"),
    [CP],
    "tests/test_client_profile.py::test_the_prod_fixture_loads$",
)
m(
    "made_up_data_only default True",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: StrictBool = True"),
    [CP],
    "tests/test_client_profile.py::test_a_real_llm_kind_in_demo_needs_the_field\\[",
)
m(
    "made-up-data rule llm item checks one fixed kind",
    CFG,
    rep(LLM_LINE, '    out = [f"llm: {b.llm.kind}"] if b.llm.kind == "anthropic" else []\n'),
    [CP],
    "tests/test_client_profile.py::test_a_real_llm_kind_in_demo_needs_the_field\\[",
)
m(
    "made-up-data rule guardrail item dropped",
    CFG,
    rep(DET_LINE, ""),
    [CP],
    "tests/test_client_profile.py::test_the_vendor_detector_in_demo_needs_the_field$",
)
m(
    "field ignored (refused even with it)",
    CFG,
    rep(S6_IF, "        if not live:\n"),
    [CP],
    "tests/test_client_profile.py::test_with_the_field_a_real_llm_kind_loads_in_demo$",
)
m(
    "made-up-data rule raised as its own error",
    CFG,
    rep(
        "        refused += sends_text_out\n",
        '        if sends_text_out:\n            raise ValueError("refused: " + ", ".join(sends_text_out))\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_three_refusals_come_in_one_error$",
)
m(
    "made-up-data rule channel item dropped",
    CFG,
    rep(CHAN_LINE, ""),
    [CP],
    "tests/test_client_profile.py::test_a_real_channel_kind_in_demo_needs_the_field$",
)
m(
    "test-double rule live replaced by environment in (pilot, prod)",
    APP,
    rep(
        S2_GIVEN,
        '_test_doubles_given(_BUILD_PARAMS, given) if cfg.environment in ("pilot", "prod") else []',
    ),
    [CP],
    "tests/test_client_profile.py::test_any_environment_that_is_not_demo_is_live\\[",
)
m(
    "the switch leaves no log line",
    APP,
    rep(S2_LOG, S2_LOG.replace("warning", "debug")),
    [CP],
    "tests/test_client_profile.py::test_the_switch_leaves_a_log_line_naming_the_keywords$",
)
m(
    "keyword snapshot taken after another statement",
    APP,
    rep(GIVEN_LINE, "    _first = 0\n" + GIVEN_LINE),
    [CP],
    "tests/test_client_profile.py::test_the_keyword_snapshot_is_the_first_statement_of_build$",
)
m(
    "switch read by truthiness, not is True",
    APP,
    rep(S2_SWITCH, "    if live_doubles and allow_test_doubles:\n"),
    [CP],
    "tests/test_client_profile.py::test_only_the_value_true_is_the_switch\\[",
)
m(
    "made_up_data_only not refused when live",
    CFG,
    rep(S6_FLAG, "            []\n"),
    [CP],
    "tests/test_client_profile.py::test_the_field_is_refused_in_pilot_and_prod$",
)
m(
    "made_up_data_only refused only in pilot and prod",
    CFG,
    rep(
        S6_FLAG,
        '            ["made_up_data_only (for demo configs only)"] if self.environment in ("pilot", "prod") and self.made_up_data_only else []\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_the_field_is_refused_in_any_environment_that_is_not_demo\\[",
)
m(
    "made_up_data_only refused in every stage",
    CFG,
    rep(
        S6_FLAG,
        '            ["made_up_data_only (for demo configs only)"] if self.made_up_data_only else []\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_with_the_field_a_real_llm_kind_loads_in_demo$",
)
m(
    "advice tail appended for any refusal",
    CFG,
    rep(
        '                if sends_text_out\n                else ""',
        '                if refused\n                else ""',
    ),
    [CP],
    "tests/test_client_profile.py::test_a_demo_anchor_only_failure_does_not_advise_the_field$",
)
m(
    "extra keyword on build() with no sample",
    APP,
    rep(
        SIG,
        "    timeout_s: float | None = None,\n    extra_double: object = None,\n    allow_test_doubles: bool = False,\n",
    ),
    [CP],
    "tests/test_client_profile.py::test_every_refused_keyword_has_a_sample$",
)
m(
    "made_up_data_only: strict bool -> loose bool",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: bool = False"),
    [CP],
    "tests/test_client_profile.py::test_a_loose_yes_does_not_switch_the_field_on\\[",
)
m(
    "made_up_data_only: accepts None",
    CFG,
    rep(
        "    made_up_data_only: StrictBool = False",
        "    made_up_data_only: StrictBool | None = False",
    ),
    [CP],
    "tests/test_client_profile.py::test_a_value_that_is_not_a_bool_is_refused_at_load\\[",
)
m(
    "allow_insecure_loopback refusal dropped in live",
    CFG,
    rep(
        '            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []\n',
        "",
    ),
    [CP, P1B],
    r"tests/test_p1b_backends.py::test_demo_only_kinds_refused_outside_demo\[",
)
m(
    "local detector list loses regex (a local check counted as sending text out)",
    TAB,
    rep('frozenset({"regex", "llm_judge"})', 'frozenset({"llm_judge"})'),
    [CP],
    "tests/test_client_profile.py::test_the_local_detector_list_is_exactly_regex_and_llm_judge$",
)
m(
    "anchor refusals dropped",
    CFG,
    rep("        refused += _anchor_refusals(self.environment, self.backends)\n", ""),
    [CP, P1B],
    "tests/test_client_profile.py::test_a_demo_anchor_only_failure_does_not_advise_the_field$",
)
m(
    "positional parameters counted as doubles",
    APP,
    rep("        if p.kind is p.KEYWORD_ONLY\n", "        if True\n"),
    [CP],
    "tests/test_client_profile.py::test_no_override_passes_the_check\\[",
)
m(
    "a name missing from given is not skipped",
    APP,
    rep("        and name in given\n", ""),
    [CP],
    "tests/test_client_profile.py::test_a_keyword_added_later_is_refused_by_default$",
)
m(
    "sources refused outside live too",
    APP,
    rep("    if sources and live:\n", "    if sources:\n"),
    [CP, P1B, "tests/test_k5_tools.py", "tests/test_k5_round5.py"],
    "tests/test_k5_tools.py::test_k5_scope_probe_refuses_write$",
)
m(
    "tools refused outside live too",
    APP,
    rep("    if tools and live:\n", "    if tools:\n"),
    [CP, P1B, "tests/test_k5_round5.py", "tests/test_k3_review_fixes.py"],
    "tests/test_k3_review_fixes.py::test_k3_build_passes_tools_to_hooks$",
)
m(
    "hold_run_ids no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("timeout_s",)'),
    [CP],
    "tests/test_client_profile.py::test_the_live_hooks_need_no_switch\\[hold_run_ids\\]",
)
m(
    "timeout_s no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("hold_run_ids",)'),
    [CP],
    "tests/test_client_profile.py::test_the_live_hooks_need_no_switch\\[timeout_s\\]",
)
m(
    "DEMO_ONLY gains llm/openai_compat",
    TAB,
    rep(
        '        ("llm", "fake"),\n',
        '        ("llm", "fake"),\n        ("llm", "openai_compat"),\n',
    ),
    [CP, P1B],
    "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$",
)
m(
    "DEMO_ONLY gains channel/slack",
    TAB,
    rep(
        '        ("channel", "fake"),\n',
        '        ("channel", "fake"),\n        ("channel", "slack"),\n',
    ),
    [CP, P1B],
    "tests/test_client_profile.py::test_demo_only_is_exactly_the_six_pairs$",
)
m(
    "made-up-data rule flag text loses its words",
    CFG,
    rep('"made_up_data_only (for demo configs only)"', '"made_up_data_only"'),
    [CP],
    "tests/test_client_profile.py::test_the_field_is_refused_in_pilot_and_prod$",
)
m(
    "test-double rule message no longer names the switch",
    APP,
    rep(
        '"in every environment other than demo (pilot and prod included) pass allow_test_doubles=True "\n            "only from a test"\n        )\n    reg',
        '"in every environment other than demo (pilot and prod included) pass the switch "\n            "only from a test"\n        )\n    reg',
    ),
    [CP],
    r"tests/test_client_profile.py::test_each_test_double_is_refused_alone\[",
)
m(
    "build keywords hidden from the check (secrets blanked)",
    APP,
    rep("    given = dict(locals())\n", "    given = dict(locals(), secrets=None)\n"),
    [CP],
    "tests/test_client_profile.py::test_each_test_double_is_refused_alone\\[secrets-",
)
m(
    "app live is prod only",
    APP,
    rep(
        "    live = is_live(cfg.environment)\n    # Before",
        '    live = cfg.environment == "prod"\n    # Before',
    ),
    [CP, P1B],
    "tests/test_client_profile.py::test_each_test_double_is_refused_alone\\[[a-z_]+-pilot\\]",
)
m(
    "only the first made-up-data rule item reported",
    CFG,
    rep("        refused += sends_text_out\n", "        refused += sends_text_out[:1]\n"),
    [CP],
    "tests/test_client_profile.py::test_three_refusals_come_in_one_error$",
)
m(
    "switch counted only when it is False",
    APP,
    rep(S2_SWITCH, "    if live_doubles and allow_test_doubles is not False:\n"),
    [CP],
    "tests/test_client_profile.py::test_only_the_value_true_is_the_switch\\[",
)
m(
    "a vendor detector joins the local list",
    TAB,
    rep(
        'frozenset({"regex", "llm_judge"})',
        'frozenset({"regex", "llm_judge", "bedrock_guardrail"})',
    ),
    [CP],
    "tests/test_client_profile.py::test_the_vendor_detector_in_demo_needs_the_field$",
)

TOOL = "tools/client_profile_mutants.py"
# The runner's own rules (the tests run in the copy and read the copy's runner file).
m(
    "runner: compiled files are written again",
    TOOL,
    rep('    env["PYTHONDONTWRITEBYTECODE"] = "1"\n', ""),
    [CP],
    "tests/test_client_profile.py::test_two_same_size_mutants_in_one_second_do_not_run_each_others_code$",
)
m(
    "runner: the tests get the whole environment",
    TOOL,
    rep(
        "    env = {k: os.environ[k] for k in PLAIN_ENV if k in os.environ}\n",
        "    env = dict(os.environ)\n",
    ),
    [CP],
    "tests/test_client_profile.py::test_the_mutant_runner_gives_the_tests_only_plain_variables$",
)
m(
    "runner: AWS_ is not a cloud prefix",
    TOOL,
    rep('    "AWS_",\n', ""),
    [CP],
    r"tests/test_client_profile.py::test_the_mutant_runner_refuses_to_start_with_a_cloud_setting\[AWS_ACCESS_KEY_ID\]",
)
m(
    "runner: numbers leave a gap",
    TOOL,
    rep(
        "DEF.append((len(DEF) "
        + "+ 1, desc",  # split, so this line does not hold the text it looks for
        "DEF.append((len(DEF) " + "+ 2, desc",
    ),
    [CP],
    "tests/test_client_profile.py::test_the_mutant_numbers_are_one_to_n_without_gaps_or_repeats$",
)

m(
    "runner: a kill by another test counts as a kill",
    TOOL,
    rep(
        'r[4] not in ("KILLED", ' + '"KILLED-NAMED")]',  # split, so this file holds the text once
        'r[4] not in ("KILLED", "KILLED-NAMED", "KILLED-OTHER")]',
    ),
    [CP],
    r"tests/test_client_profile.py::test_only_a_kill_by_the_named_test_makes_the_run_pass\[KILLED-OTHER\]",
)
m(
    "runner: an unanchored killer passes the check",
    TOOL,
    rep("        if row[5] and not _killer_is_anchored(row[5])\n", "        if False and row[5]\n"),
    [CP],
    "tests/test_client_profile.py::test_a_killer_must_name_its_file_and_end_at_the_test_name$",
)
m(
    "runner: an unanchored killer does not stop the start",
    TOOL,
    rep("    if unanchored:\n", "    if False and unanchored:\n"),
    [CP],
    "tests/test_client_profile.py::test_the_mutant_runner_refuses_to_start_with_an_unanchored_killer$",
)
m(
    "runner: the tests get the real HOME",
    TOOL,
    rep(
        '    env["HOME"] = env["USERPROFILE"] = empty_home()\n',
        '    env["HOME"] = env["USERPROFILE"] = os.environ.get("HOME", "")\n',
    ),
    [CP],
    "tests/test_client_profile.py::test_the_mutant_runner_gives_the_tests_an_empty_home$",
)
for prefix, sample in (
    ("ARM_", "ARM_CLIENT_ID"),
    ("MSI_", "MSI_ENDPOINT"),
    ("IDENTITY_", "IDENTITY_ENDPOINT"),
    ("BOTO_", "BOTO_CONFIG"),
    ("GCLOUD_", "GCLOUD_PROJECT"),
    ("OCI_", "OCI_CLI_PROFILE"),
):
    m(
        f"runner: {prefix} is not a cloud prefix",
        TOOL,
        rep(f'    "{prefix}",\n', ""),
        [CP],
        f"tests/test_client_profile.py::test_the_mutant_runner_refuses_to_start_with_a_cloud_setting\\[{sample}\\]",
    )
for command in ("gate", "replay", "score"):
    m(
        f"command line: {command} skips the config check",
        "src/hadavin_sdk/cli.py",
        rep(
            '    cfg = load_config()\n    if args.cmd == "migrate":',
            f'    cfg = None if args.cmd == "{command}" else load_config()\n    if args.cmd == "migrate":',
        ),
        [CP],
        f"tests/test_client_profile.py::test_the_command_line_refuses_a_demo_config_that_sends_text_out\\[{command}\\]",
    )

m(
    "runner: a second branch in a killer passes the check",
    TOOL,
    rep(
        '    return bool(_KILLER.fullmatch(killer)) and "|" not in _outside_groups(killer)\n',
        "    return bool(_KILLER.fullmatch(killer))\n",
    ),
    [CP],
    "tests/test_client_profile.py::test_a_killer_must_name_its_file_and_end_at_the_test_name$",
)
m(
    "runner: a killer needs no file name",
    TOOL,
    rep('r"tests/\\w+\\.py::\\w+', 'r"(tests/\\w+\\.py)?::\\w+'),
    [CP],
    "tests/test_client_profile.py::test_a_killer_must_name_its_file_and_end_at_the_test_name$",
)
m(
    "runner: a partial run counts as a pass",
    TOOL,
    rep("    complete = expected is None or len(rows) == expected\n", "    complete = True\n"),
    [CP],
    "tests/test_client_profile.py::test_a_run_of_only_some_mutants_is_never_a_pass$",
)
m(
    "runner: Windows home folder is passed through",
    TOOL,
    rep(
        '    env["HOME"] = env["USERPROFILE"] = empty_home()\n', '    env["HOME"] = empty_home()\n'
    ),
    [CP],
    "tests/test_client_profile.py::test_the_mutant_runner_gives_the_tests_an_empty_home$",
)
for prefix, sample in (
    ("SLACK_", "SLACK_BOT_TOKEN"),
    ("CLOUDFLARE_", "CLOUDFLARE_API_TOKEN"),
    ("PG", "PGPASSWORD"),
):
    m(
        f"runner: {prefix} is not a cloud prefix",
        TOOL,
        rep(f'    "{prefix}",\n', ""),
        [CP],
        f"tests/test_client_profile.py::test_the_mutant_runner_refuses_to_start_with_a_cloud_setting\\[{sample}\\]",
    )
m(
    "runner: DATABASE_URL and KUBECONFIG are not cloud names",
    TOOL,
    # the text is split so that this file holds it once
    rep("CLOUD_NAMES = " + '("DATABASE_URL", "KUBECONFIG")', "CLOUD_NAMES = ()"),
    [CP],
    r"tests/test_client_profile.py::test_the_mutant_runner_refuses_to_start_with_a_cloud_setting\[DATABASE_URL\]",
)

m(
    "refusal text names only pilot and prod again",
    APP,
    rep(
        '"in every environment other than demo (pilot and prod included) pass allow_test_doubles=True "',
        '"in pilot and prod pass allow_test_doubles=True "',
    ),
    [CP],
    "tests/test_client_profile.py::test_the_refusal_text_is_true_for_every_value_that_reaches_it$",
)
m(
    "build params snapshot taken from another function",
    APP,
    rep(
        "_BUILD_PARAMS = inspect.signature(build).parameters",
        "_BUILD_PARAMS = inspect.signature(_test_doubles_given).parameters",
    ),
    [CP],
    "tests/test_client_profile.py::test_the_build_params_snapshot_is_the_signature_of_build$",
)
m(
    "test-double rule runs in demo too",
    APP,
    rep(S2_GIVEN, "_test_doubles_given(_BUILD_PARAMS, given)"),
    [CP],
    "tests/test_client_profile.py::test_demo_ignores_the_switch_and_the_doubles\\[",
)


def BASELINE_TARGETS() -> list[str]:
    """Every test target any mutant names, once, in first-use order: a mutant is never judged against tests
    the unmutated baseline did not run."""
    seen: list[str] = []
    for *_front, tests, _killer in DEF:
        seen += [t for t in tests if t not in seen]
    return seen


def git(*a: str) -> SimpleNamespace:
    return _git_in(WT, *a)


async def _exec(argv: list[str], cwd: Path | None, env: dict | None, timeout: int):
    proc = await asyncio.create_subprocess_exec(
        *argv, cwd=cwd, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return SimpleNamespace(
        returncode=proc.returncode,
        stdout=out.decode("utf-8", "replace"),
        stderr=err.decode("utf-8", "replace"),
    )


def _sh(argv: list[str], timeout: int, cwd: Path | None = None, env: dict | None = None):
    """The one place this file starts a program. The program is git (found once, absolute) or this runner's own
    Python; every argument is this file's own text or a test path from the mutant list. No shell is used.
    Raises TimeoutError when the program runs longer than `timeout` seconds (it is killed first)."""
    return asyncio.run(_exec(argv, cwd, env, timeout))


def _git_in(folder: Path, *a: str) -> SimpleNamespace:
    if GIT is None:
        raise RuntimeError("git is not on PATH: this runner needs it to make the throw-away copy")
    return _sh([GIT, "-C", str(folder), *a], timeout=60)


def run_tests(targets: list[str], x: bool) -> tuple[str, list[str], list[str], str]:
    env = clean_env(
        PYTHONPATH=str(WT / "src")
    )  # these tests need no Postgres or cloud; the run stays local
    cmd = [PY, "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider", "--no-header", "-rfE"]
    if x:
        cmd.append("-x")
    try:
        p = _sh(cmd, timeout=TIMEOUT_S, cwd=WT, env=env)
    except TimeoutError:
        return "TIMEOUT", [], [], ""
    out = p.stdout + p.stderr
    failed = re.findall(r"^FAILED (\S+)", out, re.MULTILINE)
    errors = re.findall(r"^ERROR (\S+)", out, re.MULTILINE)
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    return ("PASS" if p.returncode == 0 else "FAIL"), failed, errors, tail


def short(node: str) -> str:
    return (
        node.replace("tests/", "")
        .replace("test_client_profile.py", "cp")
        .replace("test_p1b_backends.py", "p1b")
    )


def main() -> int:
    global WT
    if GIT is None:
        print("git is not on PATH: this runner needs it to make the throw-away copy")
        return 3
    unanchored = killer_problems()
    if unanchored:
        print("refusing to start: killer regexes not anchored at the end:", "; ".join(unanchored))
        return 3
    set_here = cloud_variables()
    if set_here:
        print(
            "refusing to start: cloud or model-provider settings are set here:", ", ".join(set_here)
        )
        print("unset them (names only are shown) and run again")
        return 3
    tmp = Path(tempfile.mkdtemp(prefix="client-profile-mutants-"))
    WT = tmp / "wt"
    made = _git_in(HERE, "worktree", "add", "--detach", str(WT), "HEAD")
    if made.returncode:
        print("cannot make the throw-away worktree:", made.stderr)
        return 3
    try:
        return _run()
    finally:
        _git_in(HERE, "worktree", "remove", "--force", str(WT))
        shutil.rmtree(tmp, ignore_errors=True)


def verdict(rows: list, expected: int | None = None) -> tuple[bool, list]:
    """(ok, rows that are not clean). Only a kill by the named test (or by any test, when no killer is named) is
    clean. KILLED-OTHER, SURVIVED, ERROR, NOT-LOCATED, TIMEOUT and RESTORE-FAILED are all failures, and so is a run
    that did not cover all `expected` mutants (a partial run is never a pass)."""
    not_clean = [r for r in rows if r[4] not in ("KILLED", "KILLED-NAMED")]
    planted = sum(1 for r in rows if r[2] == "yes")
    complete = expected is None or len(rows) == expected
    return bool(rows) and not not_clean and planted == len(rows) and complete, not_clean


def _run() -> int:
    chk = _sh(
        [PY, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"],
        timeout=60,
        cwd=WT,
        env=clean_env(PYTHONPATH=str(WT / "src")),
    )
    if not chk.stdout.strip().startswith(str(WT)):
        print("hadavin_sdk does not resolve into the copy:", chk.stdout, chk.stderr)
        return 3
    if git("status", "--porcelain").stdout.strip():
        print("copy is not clean before start:\n" + git("status", "--porcelain").stdout)
        return 3
    print(f"head {git('rev-parse', 'HEAD').stdout.strip()}  copy {WT}  python {PY}")
    base, _bf, _be, btail = run_tests(BASELINE_TARGETS(), x=False)
    print(f"baseline (unmutated) {base}: {btail}")
    if base != "PASS":
        print("baseline is not green; mutant results would mean nothing")
        return 3
    rows = []
    started = time.time()
    for num, desc, path, mut, tests, killer in DEF:
        if ONLY and num not in ONLY:
            continue
        f = WT / path
        orig = f.read_text(encoding="utf-8")
        planted, killed_by, status, extra = "no", "-", "NOT-LOCATED", ""
        try:
            try:
                new = mut(orig)
            except NotLocated as e:
                extra = str(e)
                new = None
            if new is not None:
                if new == orig:
                    status, extra = "NOT-LOCATED", "mutation changes nothing"
                else:
                    f.write_text(new, encoding="utf-8")
                    planted = "yes"
                    res, failed, errors, tail = run_tests(tests, x=True)
                    if res == "TIMEOUT":
                        status, extra = "TIMEOUT", f"over {TIMEOUT_S}s"
                    elif res == "PASS":
                        status, killed_by = "SURVIVED", "-"
                    elif failed:
                        killed_by = short(failed[0])
                        if not killer:
                            status = "KILLED"
                        elif re.match(killer, failed[0]):
                            status = "KILLED-NAMED"
                        else:  # first failure is not the named one: look at all failures
                            _, allf, _, _ = run_tests(tests, x=False)
                            named = [t for t in allf if re.match(killer, t)]
                            status = "KILLED-NAMED" if named else "KILLED-OTHER"
                            if named:
                                killed_by += f" (+named {short(named[0])})"
                    else:
                        status, killed_by = "ERROR", (short(errors[0]) if errors else tail[:60])
                        extra = "collection/import error is not a kill"
        finally:
            f.write_text(orig, encoding="utf-8")
            git("checkout", "--", path)
            dirty = git("diff").stdout.strip() or git("status", "--porcelain").stdout.strip()
        if dirty:
            print(f"!!! copy is dirty after mutant {num}; stopping\n{dirty[:500]}")
            rows.append((num, desc, planted, killed_by, "RESTORE-FAILED", extra))
            break
        rows.append((num, desc, planted, killed_by, status, extra))
        print(
            f"{num:>3} | {planted:<3} | {status:<12} | {killed_by[:80]} | {desc}"
            + (f"  [{extra}]" if extra else ""),
            flush=True,
        )
    print("\nmutant | planted | killed-by | status")
    for num, _desc, planted, kb, status, extra in rows:
        print(f"{num} | {planted} | {kb} | {status}" + (f" | {extra}" if extra else ""))
    n_pl = sum(1 for r in rows if r[2] == "yes")
    named = [r for r in rows if r[4] == "KILLED-NAMED"]
    plain = [r for r in rows if r[4] == "KILLED"]
    other = [r for r in rows if r[4] == "KILLED-OTHER"]
    surv = [r for r in rows if r[4] == "SURVIVED"]
    ok, not_clean = verdict(rows, len(DEF))
    partial = len(rows) != len(DEF)
    print(
        f"\nTOTAL mutants {len(rows)}  planted {n_pl}  KILLED by the named test {len(named) + len(plain)} "
        f"(named {len(named)}, no named killer {len(plain)})  killed only by another test {len(other)}  "
        f"SURVIVED {len(surv)}  other problems {len(not_clean) - len(surv) - len(other)}  "
        f"({time.time() - started:.0f}s)"
        + (f"  PARTIAL RUN: {len(rows)} of {len(DEF)}, exit 1" if partial else "")
    )
    for r in not_clean:
        print("  not clean:", r[0], r[4], r[1], r[5])
    print("final git status:", repr(git("status", "--porcelain").stdout))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
