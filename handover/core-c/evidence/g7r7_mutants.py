"""G7 fix round 7 mutants (scratch script kept as evidence).

REQUIRES the worktree (repo) root as the current directory: it edits src/hadavin_sdk/guard/redact.py IN PLACE, runs the named tests serially with
`uv run`, and restores the file in a `finally` (not after a SIGKILL: check `git diff` if it was killed). A mutant whose snippet is not found exactly
once is reported and skipped. Run: python handover/core-c/evidence/g7r7_mutants.py
"""

import subprocess
import sys
from pathlib import Path

P = "src/hadavin_sdk/guard/redact.py"
T = "tests/test_redact_settle_loop.py"
if not Path(P).is_file():
    sys.exit("run this from the repository (worktree) root")
orig = Path(P).read_text()
# (name, [(old, new), ...], tests); each `old` must occur exactly once
MUTANTS = [
    (
        "memory: the registration is not charged",
        [("        self._spelled_chars += added\n", "")],
        [
            f"{T}::test_a_text_that_registers_about_a_million_characters_of_forms_is_refused_in_bounded_time_and_memory",
            f"{T}::test_the_counter_is_the_number_of_trie_nodes_after_registrations_and_rollbacks",
        ],
    ),
    (
        "memory: a rolled-back registration gives its forward nodes back no more",
        [
            (
                "                del ahead[depth - 1][suffix[depth - 1]]\n                self._spelled_chars -= 1",
                "                del ahead[depth - 1][suffix[depth - 1]]",
            )
        ],
        [f"{T}::test_the_counter_is_the_number_of_trie_nodes_after_registrations_and_rollbacks"],
    ),
    (
        "memory: the limit is not read (a registration is skipped past it instead of refused: fail open)",
        [
            (
                '            raise InputTooLarge("SpelledMemoryTooMuch")\n',
                "            return\n",
            )
        ],
        [
            f"{T}::test_a_text_that_registers_about_a_million_characters_of_forms_is_refused_in_bounded_time_and_memory",
            f"{T}::test_the_memory_limit_also_stops_the_union_of_an_overlap",
        ],
    ),
    (
        "growth: recorded before the sweeps of round 1 only",
        [
            (
                "            known = len(self.mapping)\n            for i in scope:",
                "            known = None\n            for i in scope:",
            )
        ],
        [f"{T}::test_a_union_registered_by_a_sweep_of_a_later_round_puts_every_string_back"],
    ),
    (
        "terminal lookup: always iterate `matched`",
        [
            (
                "                    if len(matched) <= len(terminals):",
                "                    if True:",
            )
        ],
        [
            f"{T}::test_many_matched_prefixes_and_a_one_entry_terminal_cost_the_one_entry_not_the_prefixes"
        ],
    ),
    (
        "bank flag: written AFTER the lines were decided (deferred to the end of the fold scan)",
        [
            (
                "                self.bank_near = True\n        suspects = {",
                "                flagged = True\n        suspects = {",
            ),
            (
                "        direct, _, _ = self._line_hits(text, starts_of(lines), started)\n",
                "        flagged = False\n        direct, _, _ = self._line_hits(text, starts_of(lines), started)\n",
            ),
            (
                '        return "".join(out)\n\n    @staticmethod\n    def _aligned_fold',
                '        self.bank_near = self.bank_near or flagged\n        return "".join(out)\n\n    @staticmethod\n    def _aligned_fold',
            ),
        ],
        [f"{T}::test_every_decision_of_a_find_sees_the_flag_as_it_is_when_that_find_ends"],
    ),
    (
        "redact_many: re-read the flipped string itself too (range(flipped_at + 1))",
        [("        for n in range(flipped_at):", "        for n in range(flipped_at + 1):")],
        [f"{T}::test_redact_many_re_reads_only_the_strings_read_before_the_flip"],
    ),
    (
        "M-E in redact(): known=None (the map size read by settle, after the first sweep)",
        [
            (
                "    out = r.settle([text], [r.sweep(out, r._deadline)], known=known)[0]",
                "    out = r.settle([text], [r.sweep(out, r._deadline)], known=None)[0]",
            )
        ],
        [T, "tests/test_redact_context_after_sweep.py", "tests/test_redact_idempotent_property.py"],
    ),
]
try:
    for name, edits, tests in MUTANTS:
        if sys.argv[1:] and not any(a in name for a in sys.argv[1:]):
            continue  # optional: names (substrings) of the mutants to run
        text, ok = orig, True
        for old, new in edits:
            if text.count(old) != 1:
                print(
                    f"## mutant: {name}\nSNIPPET NOT FOUND ({text.count(old)} times): {old[:60]!r}"
                )
                ok = False
                break
            text = text.replace(old, new)
        if not ok:
            continue
        Path(P).write_text(text)
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
                "-m",
                "not perf",
                "-x",
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
    Path(P).write_text(orig)
