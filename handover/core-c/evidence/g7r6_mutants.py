"""G7 fix round 6 mutants (scratch script kept as evidence): each mutant is applied to src/hadavin_sdk/guard/redact.py, the named tests run
(serial), the file is restored after each. M-E in `redact` (one string) has no mutant: the only string is the one that registered the union.
M-A has none either: its fail-before is the round 5 scan itself (tests run against the round 5 redact.py, evidence G7-1.md). Run from the worktree root: python handover/core-c/evidence/g7r6_mutants.py"""

import subprocess

P = "src/hadavin_sdk/guard/redact.py"
T = "tests/test_redact_settle_loop.py"
orig = open(P).read()
MUTANTS = [
    (
        "M-E redact_many: the map size is read by settle, not before the first sweep",
        "known=known), r.mapping",
        "), r.mapping",
        [
            f"{T}::test_a_union_registered_in_the_first_sweep_makes_the_first_round_sweep_every_string"
        ],
    ),
    (
        "M-D redact: no second read after a flip",
        "        r._check_deadline()\n        out = r.find(text)\n    if _sweep_copies",
        "        pass\n    if _sweep_copies",
        [f"{T}::test_redact_reads_the_text_again_when_the_flag_flipped_during_the_first_read"],
    ),
    (
        "M-E union: registration not counted",
        "end - start + work",
        "work",
        [f"{T}::test_union_registration_is_counted_and_checked"],
    ),
    (
        "unspell: the backward nodes are not pruned",
        '            del back[-1][""]\n            for depth in range(len(prefix), 0, -1):  # and the backward ones\n                if back[depth]:\n                    break\n                del back[depth - 1][prefix[depth - 1]]\n',
        '            del back[-1][""]\n',
        [f"{T}::test_registrations_and_rollbacks_leave_no_node_behind"],
    ),
]
try:
    for name, old, new, tests in MUTANTS:
        if orig.count(old) != 1:
            print(f"## mutant: {name}\nSNIPPET NOT FOUND ({orig.count(old)} times)")
            continue
        open(P, "w").write(orig.replace(old, new))
        r = subprocess.run(
            [
                "uv",
                "run",
                "--all-extras",
                "--group",
                "test",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-n",
                "0",
                *tests,
            ],
            capture_output=True,
            text=True,
        )
        lines = [
            ln
            for ln in r.stdout.splitlines()
            if ln.startswith(("FAILED", "ERROR")) or " passed" in ln or " failed" in ln
        ]
        print(f"## mutant: {name}\n" + "\n".join(lines))
finally:
    open(P, "w").write(orig)
