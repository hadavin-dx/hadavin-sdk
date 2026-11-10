"""Hand-made mutants for the client-profile check (made-up code only, no model calls, no spend).

What it does: it plants one small change at a time into the source of a throw-away copy of this repository
(a detached git worktree of HEAD in a temp folder, never the folder you run it from), runs the tests that should
notice, and restores the file in `finally`. A mutant is KILLED when a test FAILS. A collection or import error is
reported as ERROR and is not a kill.

Counts (63 mutants): ids 1-35 and 46-51 are 41 mutants re-fitted to the current code (the original mutant list
for them is not kept); ids 52-55 are 4 mutants written from one-line descriptions; ids 56-73 are 18 mutants
written later to cover the build keyword rule, the local detector list and the stage rule. Ids 36-45 are
reserved for the second pull request of this package and are not used here. 41 + 4 + 18 = 63. Never call 63
the original number.

How to run: `python tools/p6a1_mutants.py` from a virtual environment with the test extras. Commit your changes
first (the copy is made from HEAD). P6A1_ONLY=1,2 picks mutants; P6A1_PY names the Python; P6A1_TIMEOUT
bounds one test run in seconds. The baseline run (unmutated) covers every test file that any mutant names, so a
mutant is never judged against tests the baseline did not run. Each mutant names the test (a regular
expression) that should kill it; "KILLED-NAMED" means that test failed. Exit code 0 only if every mutant was
located and killed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PY = os.environ.get("P6A1_PY", sys.executable)
TIMEOUT_S = int(os.environ.get("P6A1_TIMEOUT", "300"))
WT = Path("/nonexistent-set-by-main")
GIT = shutil.which(
    "git"
)  # one absolute path, found once; a missing git is a stated failure in main()
ONLY = {int(x) for x in os.environ.get("P6A1_ONLY", "").split(",") if x}

CP = "tests/test_client_profile.py"
P1B = "tests/test_p1b_backends.py"
K9B = "tests/test_k5_round9b.py::test_a_live_deployment_without_the_key_does_not_start"
K10 = "tests/test_k5_round10.py::test_a_live_postgres_deployment_without_a_purge_dsn_does_not_start"

APP = "src/hadavin_sdk/app.py"
CFG = "src/hadavin_sdk/config.py"
TAB = "src/hadavin_sdk/backends/table.py"

S2_COND = "if live and allow_test_doubles is not True else []"
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
BLOCK_END = (
    '            "in pilot and prod pass allow_test_doubles=True only from a test"\n        )\n'
)


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


# (number, description, file to edit, mutation, test targets, expected killer regex or "")
DEF: list = []


def m(num, desc, path, mut, tests, killer=""):
    DEF.append((num, desc, path, mut, tests, killer))


for i, (pair, kill) in enumerate(
    [
        (("llm", "fake"), "p1b|demo_only_is_exactly"),
        (("channel", "fake"), "p1b|demo_only_is_exactly"),
        (("secrets", "fake"), "p1b|demo_only_is_exactly"),
        (("secrets", "env"), "secrets_env_is_refused|demo_only_is_exactly"),
        (("store", "memory"), "p1b|pilot_config_that_omits_store|demo_only_is_exactly"),
        (("audit", "local_dir"), "p1b|demo_only_is_exactly"),
    ],
    start=1,
):
    m(
        i,
        f"DEMO_ONLY loses {pair[0]}/{pair[1]}",
        TAB,
        rep(f'        ("{pair[0]}", "{pair[1]}"),\n', ""),
        [CP, P1B],
        kill,
    )

m(
    7,
    'refusal only in prod (live -> == "prod")',
    CFG,
    rep(
        "        if live:\n            refused = [",
        '        if self.environment == "prod":\n            refused = [',
    ),
    [CP, P1B],
    "secrets_env_is_refused.*pilot|pilot_config_that_omits_store|p1b",
)
m(
    8,
    "message keeps only the first refusal",
    CFG,
    rep("{', '.join(refused)}{tail}", "{refused[0]}{tail}"),
    [CP, P1B],
    "p1b|three_refusals",
)
m(
    9,
    "test-double rule check deleted",
    APP,
    rep("    if live_doubles:\n", "    if False:\n"),
    [CP],
    "each_test_double.*llm",
)
m(
    10,
    "test-double rule looks only at llm",
    APP,
    rep(
        "        _test_doubles_given(_BUILD_PARAMS, given) if live",
        '        [n for n in _test_doubles_given(_BUILD_PARAMS, given) if n == "llm"] if live',
    ),
    [CP],
    "each_test_double.*(secrets|channel|detector|clock)",
)
m(
    11,
    "allow_test_doubles default True",
    APP,
    rep(SIG, SIG.replace("False", "True")),
    [CP],
    "each_test_double",
)
m(
    12,
    "test-double rule only for prod",
    APP,
    rep(S2_COND, 'if cfg.environment == "prod" and allow_test_doubles is not True else []'),
    [CP],
    "each_test_double.*pilot",
)
m(
    13,
    "sources not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("tools",)\n'),
    [CP],
    "sources_keeps",
)
m(
    14,
    "tools not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("sources",)\n'),
    [CP],
    "tools_keeps",
)
m(
    15,
    "compare by truth value, not identity",
    APP,
    rep(
        "        and given[name] is not p.default\n",
        "        and bool(given[name]) != bool(p.default)\n",
    ),
    [CP],
    "falsy_double",
)
m(
    16,
    "check placed after secrets = secrets or make()",
    APP,
    move_block(r'^    secrets = secrets or make\("secrets", b\.secrets\)\n'),
    [CP],
    "refusal_builds_nothing_first|not_demo_is_live",
)
m(
    17,
    "check placed after platform_secrets.check",
    APP,
    move_block(r"^    platform_secrets\.check\(.*\)\n"),
    [CP],
    "refusal_builds_nothing_first",
)
m(
    18,
    "names from a fixed list of four",
    APP,
    rep(
        "        and name not in skip\n",
        '        and name not in skip\n        and name in ("secrets", "channel", "detector", "llm")\n',
    ),
    [CP],
    "each_test_double.*clock|keyword_added_later",
)
m(
    19,
    "message names only the first keyword",
    APP,
    rep(S2_MSG, '            f"{live_doubles[0]}= replace configured parts and are for tests; "\n'),
    [CP],
    "all_at_once",
)
m(
    20,
    "switch ignored",
    APP,
    rep(S2_COND, "if live else []"),
    [CP, K9B, K10],
    "switch_lets|round9b|round10",
)
m(
    21,
    "_LIVE_HOOKS gains llm",
    APP,
    rep(
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s")',
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s", "llm")',
    ),
    [CP],
    "each_test_double.*llm|live_hooks_are_exactly",
)
m(
    22,
    "_LIVE_HOOKS ignored",
    APP,
    rep(
        '    skip = {"allow_test_doubles", *_OWN_REFUSAL, *_LIVE_HOOKS}\n',
        '    skip = {"allow_test_doubles", *_OWN_REFUSAL}\n',
    ),
    [CP],
    "live_hooks_need_no_switch",
)
m(
    23,
    "door scan: keyword branch deleted",
    CP,
    rep('                if kw.arg == "allow_test_doubles":\n', "                if False:\n"),
    [CP],
    "planted_doors.*direct",
)
m(
    24,
    "door scan: keyword only in calls named build",
    CP,
    rep(
        '                if kw.arg == "allow_test_doubles":\n',
        '                if kw.arg == "allow_test_doubles" and name == "build":\n',
    ),
    [CP],
    "planted_doors.*partial",
)
m(
    25,
    "door scan: ** branch deleted",
    CP,
    rep('                if kw.arg is None and name == "build":\n', "                if False:\n"),
    [CP],
    "planted_doors.*double_star",
)
m(
    26,
    "decided-pairs check: both-sets not reported",
    CP,
    rep("        for c, k in sorted(demo_only & set(reviewed))\n", "        for c, k in []\n"),
    [CP],
    "planted_pair_in_both",
)
m(
    27,
    "decided-pairs check: empty reason not reported",
    CP,
    rep(
        "for (c, k), why in sorted(reviewed.items()) if not why.strip()]",
        "for (c, k), why in sorted(reviewed.items()) if False]",
    ),
    [CP],
    "planted_empty_reason",
)
m(
    28,
    "decided-pairs check: neither-set not reported",
    CP,
    rep(
        "        for c, k in sorted(pairs - demo_only - set(reviewed))\n",
        "        for c, k in []\n",
    ),
    [CP],
    "planted_kind_in_neither",
)
m(
    29,
    "made-up-data rule items deleted",
    CFG,
    rep(S6_IF, "        if False:\n"),
    [CP],
    "needs_the_field",
)
m(
    30,
    "made-up-data rule runs in every stage",
    CFG,
    rep(S6_IF, "        if not self.made_up_data_only:\n"),
    [CP],
    "prod_fixture_loads|no_override_passes|switch_lets",
)
m(
    31,
    "made_up_data_only default True",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: StrictBool = True"),
    [CP],
    "needs_the_field",
)
m(
    32,
    "made-up-data rule llm item checks one fixed kind",
    CFG,
    rep(LLM_LINE, '    out = [f"llm: {b.llm.kind}"] if b.llm.kind == "anthropic" else []\n'),
    [CP],
    "real_llm_kind_in_demo",
)
m(
    33,
    "made-up-data rule guardrail item dropped",
    CFG,
    rep(DET_LINE, ""),
    [CP],
    "vendor_detector|three_refusals",
)
m(
    34,
    "field ignored (refused even with it)",
    CFG,
    rep(S6_IF, "        if not live:\n"),
    [CP],
    "with_the_field_a_real_llm",
)
m(
    35,
    "made-up-data rule raised as its own error",
    CFG,
    rep(
        "        refused += sends_text_out\n",
        '        if sends_text_out:\n            raise ValueError("refused: " + ", ".join(sends_text_out))\n',
    ),
    [CP],
    "three_refusals",
)
m(46, "made-up-data rule channel item dropped", CFG, rep(CHAN_LINE, ""), [CP], "real_channel_kind")
m(
    47,
    "test-double rule live replaced by environment in (pilot, prod)",
    APP,
    rep(
        S2_COND,
        'if cfg.environment in ("pilot", "prod") and allow_test_doubles is not True else []',
    ),
    [CP],
    "not_demo_is_live",
)
m(
    48,
    "switch read by truthiness, not is True",
    APP,
    rep(S2_COND, "if live and not allow_test_doubles else []"),
    [CP],
    "only_the_value_true",
)
m(
    49,
    "made_up_data_only not refused when live",
    CFG,
    rep(S6_FLAG, "            []\n"),
    [CP],
    "refused_in_pilot_and_prod|any_environment_that_is_not_demo",
)
m(
    50,
    "made_up_data_only refused only in pilot and prod",
    CFG,
    rep(
        S6_FLAG,
        '            ["made_up_data_only (for demo configs only)"] if self.environment in ("pilot", "prod") and self.made_up_data_only else []\n',
    ),
    [CP],
    "any_environment_that_is_not_demo",
)
m(
    51,
    "made_up_data_only refused in every stage",
    CFG,
    rep(
        S6_FLAG,
        '            ["made_up_data_only (for demo configs only)"] if self.made_up_data_only else []\n',
    ),
    [CP],
    "with_the_field_a_real_llm|field_still_loads",
)
m(
    52,
    "advice tail appended for any refusal",
    CFG,
    rep(
        '                if sends_text_out\n                else ""',
        '                if refused\n                else ""',
    ),
    [CP],
    "secrets_env_is_refused|pilot_config_that_omits_store|demo_anchor_only_failure",
)
m(
    53,
    "extra keyword on build() with no sample",
    APP,
    rep(
        SIG,
        "    timeout_s: float | None = None,\n    extra_double: object = None,\n    allow_test_doubles: bool = False,\n",
    ),
    [CP],
    "has_a_sample",
)
m(
    54,
    "made_up_data_only: strict bool -> loose bool",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: bool = False"),
    [CP],
    "loose_yes",
)
m(
    55,
    "made_up_data_only: accepts None",
    CFG,
    rep(
        "    made_up_data_only: StrictBool = False",
        "    made_up_data_only: StrictBool | None = False",
    ),
    [CP],
    "not_a_bool",
)
# 56-73: written later (see the header). Each names the test that should kill it.
m(
    56,
    "[later] allow_insecure_loopback refusal dropped in live",
    CFG,
    rep(
        '            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []\n',
        "",
    ),
    [CP, P1B],
    "demo_only_kinds_refused_outside",
)
m(
    57,
    "[later] local detector list loses regex (a local check counted as sending text out)",
    TAB,
    rep('frozenset({"regex", "llm_judge"})', 'frozenset({"llm_judge"})'),
    [CP],
    "local_detector_list|demo_anchor_only_failure",
)
m(
    58,
    "[later] anchor refusals dropped",
    CFG,
    rep("        refused += _anchor_refusals(self.environment, self.backends)\n", ""),
    [CP, P1B],
    "demo_anchor_only_failure|three_refusals",
)
m(
    59,
    "[later] positional parameters counted as doubles",
    APP,
    rep("        if p.kind is p.KEYWORD_ONLY\n", "        if True\n"),
    [CP],
    "no_override_passes|live_hooks_need_no_switch|sources_keeps|tools_keeps",
)
m(
    60,
    "[later] a name missing from given is not skipped",
    APP,
    rep("        and name in given\n", ""),
    [CP],
    "keyword_added_later",
)
m(
    61,
    "[later] sources refused outside live too",
    APP,
    rep("    if sources and live:\n", "    if sources:\n"),
    [CP, P1B, "tests/test_k5_tools.py", "tests/test_k5_round5.py"],
    "scope_probe_refuses_write",
)
m(
    62,
    "[later] tools refused outside live too",
    APP,
    rep("    if tools and live:\n", "    if tools:\n"),
    [CP, P1B, "tests/test_k5_round5.py", "tests/test_k3_review_fixes.py"],
    "build_passes_tools_to_hooks",
)
m(
    63,
    "[later] hold_run_ids no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("timeout_s",)'),
    [CP],
    "live_hooks_need_no_switch.*hold_run_ids|live_hooks_are_exactly",
)
m(
    64,
    "[later] timeout_s no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("hold_run_ids",)'),
    [CP],
    "live_hooks_need_no_switch.*timeout_s|live_hooks_are_exactly",
)
m(
    65,
    "[later] DEMO_ONLY gains llm/openai_compat",
    TAB,
    rep(
        '        ("llm", "fake"),\n',
        '        ("llm", "fake"),\n        ("llm", "openai_compat"),\n',
    ),
    [CP, P1B],
    "demo_only_is_exactly|prod_fixture_loads",
)
m(
    66,
    "[later] DEMO_ONLY gains channel/slack",
    TAB,
    rep(
        '        ("channel", "fake"),\n',
        '        ("channel", "fake"),\n        ("channel", "slack"),\n',
    ),
    [CP, P1B],
    "demo_only_is_exactly|prod_fixture_loads",
)
m(
    67,
    "[later] made-up-data rule flag text loses its words",
    CFG,
    rep('"made_up_data_only (for demo configs only)"', '"made_up_data_only"'),
    [CP],
    "refused_in_pilot_and_prod",
)
m(
    68,
    "[later] test-double rule message no longer names the switch",
    APP,
    rep(
        '"in pilot and prod pass allow_test_doubles=True only from a test"\n        )\n    reg',
        '"in pilot and prod pass the switch only from a test"\n        )\n    reg',
    ),
    [CP],
    "each_test_double|all_at_once",
)
m(
    69,
    "[later] build keywords hidden from the check (secrets blanked)",
    APP,
    rep("    given = dict(locals())\n", "    given = dict(locals(), secrets=None)\n"),
    [CP],
    "each_test_double.*secrets|all_at_once",
)
m(
    70,
    "[later] app live is prod only",
    APP,
    rep(
        "    live = is_live(cfg.environment)\n    # Before",
        '    live = cfg.environment == "prod"\n    # Before',
    ),
    [CP, P1B],
    "each_test_double|all_at_once|not_demo_is_live",
)
m(
    71,
    "[later] only the first made-up-data rule item reported",
    CFG,
    rep("        refused += sends_text_out\n", "        refused += sends_text_out[:1]\n"),
    [CP],
    "three_refusals",
)
m(
    72,
    "[later] switch counted only when it is False",
    APP,
    rep(S2_COND, "if live and allow_test_doubles is False else []"),
    [CP],
    "only_the_value_true",
)
m(
    73,
    "[later] a vendor detector joins the local list",
    TAB,
    rep(
        'frozenset({"regex", "llm_judge"})',
        'frozenset({"regex", "llm_judge", "bedrock_guardrail"})',
    ),
    [CP],
    "vendor_detector|local_detector_list",
)


def BASELINE_TARGETS() -> list[str]:
    """Every test target any mutant names, once, in first-use order: a mutant is never judged against tests
    the unmutated baseline did not run."""
    seen: list[str] = []
    for *_front, tests, _killer in DEF:
        seen += [t for t in tests if t not in seen]
    return seen


def git(*a: str) -> subprocess.CompletedProcess:
    return _git_in(WT, *a)


def _sh(argv: list[str], timeout: int, cwd: Path | None = None, env: dict | None = None):
    """The one place this file starts a program. The program is git (found once, absolute) or this runner's own
    Python; every argument is this file's own text or a test path from the mutant list. No shell is used."""
    return subprocess.run(  # noqa: S603  (fixed argv, no shell; ruff cannot see through the list)
        argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False
    )


def _git_in(folder: Path, *a: str) -> subprocess.CompletedProcess:
    if GIT is None:
        raise RuntimeError("git is not on PATH: this runner needs it to make the throw-away copy")
    return _sh([GIT, "-C", str(folder), *a], timeout=60)


def run_tests(targets: list[str], x: bool) -> tuple[str, list[str], list[str], str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(WT / "src")
    env.pop("HADAVIN_TEST_PG_DSN", None)  # these tests need no Postgres; keeps the run local
    cmd = [PY, "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider", "--no-header", "-rfE"]
    if x:
        cmd.append("-x")
    try:
        p = _sh(cmd, timeout=TIMEOUT_S, cwd=WT, env=env)
    except subprocess.TimeoutExpired:
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
    tmp = Path(tempfile.mkdtemp(prefix="p6a1-mutants-"))
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


def _run() -> int:
    chk = _sh(
        [PY, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"],
        timeout=60,
        cwd=WT,
        env={**os.environ, "PYTHONPATH": str(WT / "src")},
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
    prod_fixture_loads = time.time()
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
                        elif re.search(killer, failed[0]):
                            status = "KILLED-NAMED"
                        else:  # first failure is not the named one: look at all failures
                            _, allf, _, _ = run_tests(tests, x=False)
                            named = [t for t in allf if re.search(killer, t)]
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
    bad = [r for r in rows if r[4] not in ("KILLED", "KILLED-NAMED", "KILLED-OTHER", "SURVIVED")]
    killed = len(named) + len(plain) + len(other)
    print(
        f"\nTOTAL mutants {len(rows)}  planted {n_pl}  KILLED {killed} (named {len(named)}, no named killer "
        f"{len(plain)}, killed by another test {len(other)})  SURVIVED {len(surv)}  other problems {len(bad)}  "
        f"({time.time() - prod_fixture_loads:.0f}s)"
    )
    for r in surv + bad + other:
        print("  not clean:", r[0], r[4], r[1], r[5])
    print("final git status:", repr(git("status", "--porcelain").stdout))
    ok = bool(rows) and killed == len(rows) == n_pl and not surv and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
