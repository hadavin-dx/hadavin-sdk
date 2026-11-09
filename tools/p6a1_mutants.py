#!/usr/bin/env python3
"""P6a-1 hand mutants for PR 72 (branch core/P6a). Made-up code only, no model calls, no spend.

Honest origin: the first runner (and its mutants 56-72) was never saved. Mutants 1-35, 46-51 come from the
records (re-fitted to the current code); 52-55 are read from a one-line description; 56-72 and 73 are INVENTED
to reach the recorded count and to cover the detector allow-list. Say "45 from records + 18 new = 63"; never
call 63 the original number. Each mutant is planted in a throw-away detached git worktree (never in the working
tree you run this from), the named tests run, and the file is restored in `finally`.

HOW IT RUNS: `python tools/p6a1_mutants.py` from a venv with the test extras. It creates a detached worktree of
HEAD in a temp folder, points PYTHONPATH at its src, runs a green baseline, then every mutant (P6A1_ONLY=1,2
to pick some). Killed means a test FAILED; a collection or import error is reported as ERROR and is not a kill.
Exit code 0 only if every mutant was located and killed. Mutants 56 and up have no named killer: any failing
test counts. Commit your changes before running (the worktree is made from HEAD).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PY = os.environ.get("P6A1_PY", sys.executable)
TIMEOUT_S = int(os.environ.get("P6A1_TIMEOUT", "300"))
WT = Path("/nonexistent-set-by-main")
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
    """Cut the S2 block and paste it after the single line that matches anchor_re."""

    def f(text: str) -> str:
        if text.count(BLOCK_START) != 1 or text.count(BLOCK_END) != 1:
            raise NotLocated("S2 block start/end not found exactly once")
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
        (("llm", "fake"), "p1b|t2a"),
        (("channel", "fake"), "p1b|t2a"),
        (("secrets", "fake"), "p1b|t2a"),
        (("secrets", "env"), "t1a|t2a"),
        (("store", "memory"), "p1b|t1d|t2a"),
        (("audit", "local_dir"), "p1b|t2a"),
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
    "t1a.*pilot|t1d|p1b",
)
m(
    8,
    "message keeps only the first refusal",
    CFG,
    rep("{', '.join(refused)}{tail}", "{refused[0]}{tail}"),
    [CP, P1B],
    "p1b|t7d",
)
m(9, "S2 check deleted", APP, rep("    if live_doubles:\n", "    if False:\n"), [CP], "t5b.*llm")
m(
    10,
    "S2 looks only at llm",
    APP,
    rep(
        "        _test_doubles_given(_BUILD_PARAMS, given) if live",
        '        [n for n in _test_doubles_given(_BUILD_PARAMS, given) if n == "llm"] if live',
    ),
    [CP],
    "t5b.*(secrets|channel|detector|clock)",
)
m(11, "allow_test_doubles default True", APP, rep(SIG, SIG.replace("False", "True")), [CP], "t5b")
m(
    12,
    "S2 only for prod",
    APP,
    rep(S2_COND, 'if cfg.environment == "prod" and allow_test_doubles is not True else []'),
    [CP],
    "t5b.*pilot",
)
m(
    13,
    "sources not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("tools",)\n'),
    [CP],
    "t5f",
)
m(
    14,
    "tools not excluded from the rule",
    APP,
    rep(OWN, '_OWN_REFUSAL = ("sources",)\n'),
    [CP],
    "t5h",
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
    "t5i",
)
m(
    16,
    "check placed after secrets = secrets or make()",
    APP,
    move_block(r'^    secrets = secrets or make\("secrets", b\.secrets\)\n'),
    [CP],
    "t5j|t5q",
)
m(
    17,
    "check placed after platform_secrets.check",
    APP,
    move_block(r"^    platform_secrets\.check\(.*\)\n"),
    [CP],
    "t5j",
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
    "t5b.*clock|t5l",
)
m(
    19,
    "message names only the first keyword",
    APP,
    rep(S2_MSG, '            f"{live_doubles[0]}= replace configured parts and are for tests; "\n'),
    [CP],
    "t5c",
)
m(20, "switch ignored", APP, rep(S2_COND, "if live else []"), [CP, K9B, K10], "t5n|round9b|round10")
m(
    21,
    "_LIVE_HOOKS gains llm",
    APP,
    rep(
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s")',
        '_LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s", "llm")',
    ),
    [CP],
    "t5b.*llm|t5p",
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
    "t5o",
)
m(
    23,
    "T5g checker: keyword branch deleted",
    CP,
    rep('                if kw.arg == "allow_test_doubles":\n', "                if False:\n"),
    [CP],
    "t5g_planted.*direct",
)
m(
    24,
    "T5g checker: keyword only in calls named build",
    CP,
    rep(
        '                if kw.arg == "allow_test_doubles":\n',
        '                if kw.arg == "allow_test_doubles" and name == "build":\n',
    ),
    [CP],
    "t5g_planted.*partial",
)
m(
    25,
    "T5g checker: ** branch deleted",
    CP,
    rep('                if kw.arg is None and name == "build":\n', "                if False:\n"),
    [CP],
    "t5g_planted.*double_star",
)
m(
    26,
    "T2 check: both-sets not reported",
    CP,
    rep("        for c, k in sorted(demo_only & set(reviewed))\n", "        for c, k in []\n"),
    [CP],
    "t2c.*both",
)
m(
    27,
    "T2 check: empty reason not reported",
    CP,
    rep(
        "for (c, k), why in sorted(reviewed.items()) if not why.strip()]",
        "for (c, k), why in sorted(reviewed.items()) if False]",
    ),
    [CP],
    "t2c.*empty",
)
m(
    28,
    "T2 check: neither-set not reported",
    CP,
    rep(
        "        for c, k in sorted(pairs - demo_only - set(reviewed))\n",
        "        for c, k in []\n",
    ),
    [CP],
    "t2c.*neither",
)
m(29, "S6 items deleted", CFG, rep(S6_IF, "        if False:\n"), [CP], "t7a")
m(
    30,
    "S6 runs in every stage",
    CFG,
    rep(S6_IF, "        if not self.made_up_data_only:\n"),
    [CP],
    "t0|t5m|t5n",
)
m(
    31,
    "made_up_data_only default True",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: StrictBool = True"),
    [CP],
    "t7a",
)
m(
    32,
    "S6 llm item checks one fixed kind",
    CFG,
    rep(LLM_LINE, '    out = [f"llm: {b.llm.kind}"] if b.llm.kind == "anthropic" else []\n'),
    [CP],
    "t7a_a_real_llm",
)
m(33, "S6 guardrail item dropped", CFG, rep(DET_LINE, ""), [CP], "t7a2|t7d")
m(
    34,
    "field ignored (refused even with it)",
    CFG,
    rep(S6_IF, "        if not live:\n"),
    [CP],
    "t7b",
)
m(
    35,
    "S6 raised as its own error",
    CFG,
    rep(
        "        refused += sends_text_out\n",
        '        if sends_text_out:\n            raise ValueError("refused: " + ", ".join(sends_text_out))\n',
    ),
    [CP],
    "t7d",
)
m(46, "S6 channel item dropped", CFG, rep(CHAN_LINE, ""), [CP], "t7a3")
m(
    47,
    "S2 live replaced by environment in (pilot, prod)",
    APP,
    rep(
        S2_COND,
        'if cfg.environment in ("pilot", "prod") and allow_test_doubles is not True else []',
    ),
    [CP],
    "t5q",
)
m(
    48,
    "switch read by truthiness, not is True",
    APP,
    rep(S2_COND, "if live and not allow_test_doubles else []"),
    [CP],
    "t5r",
)
m(
    49,
    "made_up_data_only not refused when live",
    CFG,
    rep(S6_FLAG, "            []\n"),
    [CP],
    "t7e|t7f",
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
    "t7f",
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
    "t7b|t7g",
)
m(
    52,
    "advice tail appended for any refusal (R2-01)",
    CFG,
    rep(
        '                if sends_text_out\n                else ""',
        '                if refused\n                else ""',
    ),
    [CP],
    "t1a|t1d|t1e",
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
    "t5s",
)
m(
    54,
    "made_up_data_only: strict bool -> loose bool",
    CFG,
    rep("    made_up_data_only: StrictBool = False", "    made_up_data_only: bool = False"),
    [CP],
    "t7h",
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
    "t7i",
)
# 56-72: INVENTED to reach the recorded total of 62 (see header). No named killer.
m(
    56,
    "[invented] allow_insecure_loopback refusal dropped in live",
    CFG,
    rep(
        '            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []\n',
        "",
    ),
    [CP, P1B],
)
m(
    57,
    "[invented] local detector list loses regex (a local check counted as sending text out)",
    TAB,
    rep('frozenset({"regex", "llm_judge"})', 'frozenset({"llm_judge"})'),
    [CP],
)
m(
    58,
    "[invented] anchor refusals dropped",
    CFG,
    rep("        refused += _anchor_refusals(self.environment, self.backends)\n", ""),
    [CP, P1B],
)
m(
    59,
    "[invented] positional parameters counted as doubles",
    APP,
    rep("        if p.kind is p.KEYWORD_ONLY\n", "        if True\n"),
    [CP],
)
m(
    60,
    "[invented] a name missing from given is not skipped",
    APP,
    rep("        and name in given\n", ""),
    [CP],
)
m(
    61,
    "[invented] sources refused outside live too",
    APP,
    rep("    if sources and live:\n", "    if sources:\n"),
    [CP, P1B, "tests/test_k5_tools.py", "tests/test_k5_round5.py"],
)
m(
    62,
    "[invented] tools refused outside live too",
    APP,
    rep("    if tools and live:\n", "    if tools:\n"),
    [CP, P1B, "tests/test_k5_round5.py", "tests/test_k3_review_fixes.py"],
)
m(
    63,
    "[invented] hold_run_ids no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("timeout_s",)'),
    [CP],
)
m(
    64,
    "[invented] timeout_s no longer a live hook",
    APP,
    rep('("hold_run_ids", "timeout_s")', '("hold_run_ids",)'),
    [CP],
)
m(
    65,
    "[invented] DEMO_ONLY gains llm/openai_compat",
    TAB,
    rep(
        '        ("llm", "fake"),\n',
        '        ("llm", "fake"),\n        ("llm", "openai_compat"),\n',
    ),
    [CP, P1B],
)
m(
    66,
    "[invented] DEMO_ONLY gains channel/slack",
    TAB,
    rep(
        '        ("channel", "fake"),\n',
        '        ("channel", "fake"),\n        ("channel", "slack"),\n',
    ),
    [CP, P1B],
)
m(
    67,
    "[invented] S6 flag text loses its words",
    CFG,
    rep('"made_up_data_only (for demo configs only)"', '"made_up_data_only"'),
    [CP],
)
m(
    68,
    "[invented] S2 message no longer names the switch",
    APP,
    rep(
        '"in pilot and prod pass allow_test_doubles=True only from a test"\n        )\n    reg',
        '"in pilot and prod pass the switch only from a test"\n        )\n    reg',
    ),
    [CP],
)
m(
    69,
    "[invented] build keywords hidden from the check (secrets blanked)",
    APP,
    rep("    given = dict(locals())\n", "    given = dict(locals(), secrets=None)\n"),
    [CP],
)
m(
    70,
    "[invented] app live is prod only",
    APP,
    rep(
        "    live = is_live(cfg.environment)\n    # Before",
        '    live = cfg.environment == "prod"\n    # Before',
    ),
    [CP, P1B],
)
m(
    71,
    "[invented] only the first S6 item reported",
    CFG,
    rep("        refused += sends_text_out\n", "        refused += sends_text_out[:1]\n"),
    [CP],
)
m(
    73,
    "[new] a vendor detector joins the local list",
    TAB,
    rep(
        'frozenset({"regex", "llm_judge"})',
        'frozenset({"regex", "llm_judge", "bedrock_guardrail"})',
    ),
    [CP],
    "t7a2|t7a4",
)
m(
    72,
    "[invented] switch counted only when it is False",
    APP,
    rep(S2_COND, "if live and allow_test_doubles is False else []"),
    [CP],
)


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(WT), *a], capture_output=True, text=True, timeout=60)


def run_tests(targets: list[str], x: bool) -> tuple[str, list[str], list[str], str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(WT / "src")
    env.pop("HADAVIN_TEST_PG_DSN", None)  # these tests need no Postgres; keeps the run local
    cmd = [PY, "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider", "--no-header", "-rfE"]
    if x:
        cmd.append("-x")
    try:
        p = subprocess.run(cmd, cwd=WT, env=env, capture_output=True, text=True, timeout=TIMEOUT_S)
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
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="p6a1-mutants-"))
    WT = tmp / "wt"
    made = subprocess.run(
        ["git", "-C", str(HERE), "worktree", "add", "--detach", str(WT), "HEAD"],
        capture_output=True,
        text=True,
    )
    if made.returncode:
        print("cannot make the throw-away worktree:", made.stderr)
        return 3
    try:
        return _run()
    finally:
        subprocess.run(
            ["git", "-C", str(HERE), "worktree", "remove", "--force", str(WT)], capture_output=True
        )
        shutil.rmtree(tmp, ignore_errors=True)


def _run() -> int:
    chk = subprocess.run(
        [PY, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"],
        cwd=WT,
        env={**os.environ, "PYTHONPATH": str(WT / "src")},
        capture_output=True,
        text=True,
    )
    if not chk.stdout.strip().startswith(str(WT)):
        print("hadavin_sdk does not resolve into the copy:", chk.stdout, chk.stderr)
        return 3
    if git("status", "--porcelain").stdout.strip():
        print("copy is not clean before start:\n" + git("status", "--porcelain").stdout)
        return 3
    print(f"head {git('rev-parse', 'HEAD').stdout.strip()}  copy {WT}  python {PY}")
    base, _bf, _be, btail = run_tests([CP, P1B, K9B, K10], x=False)
    print(f"baseline (unmutated) {base}: {btail}")
    if base != "PASS":
        print("baseline is not green; mutant results would mean nothing")
        return 3
    rows = []
    t0 = time.time()
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
        f"({time.time() - t0:.0f}s)"
    )
    for r in surv + bad + other:
        print("  not clean:", r[0], r[4], r[1], r[5])
    print("final git status:", repr(git("status", "--porcelain").stdout))
    ok = bool(rows) and killed == len(rows) == n_pl and not surv and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
