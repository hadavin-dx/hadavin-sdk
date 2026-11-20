"""Scratch mutants of src/hadavin_sdk/guard/redact.py (in the worktree; the file is restored after each). Prints the raw pytest tail of each."""
import subprocess, sys, shutil
P = "src/hadavin_sdk/guard/redact.py"
orig = open(P).read()
T = "tests/test_redact_settle_loop.py"
MUTANTS = [
 ("N3a settle: the round deadline check removed",
  "            self._check_deadline()\n            known = len(self.mapping)", "            known = len(self.mapping)",
  [f"{T}::test_settle_refuses_before_a_round_when_the_deadline_is_spent_and_never_calls_find"]),
 ("N3b sweep: the segment check removed",
  "                deadline is not None and (free - 1) % 32 == 0 and (self._finders or self._slow)", "                False",
  [f"{T}::test_the_deadline_trips_at_the_segment_check_of_a_segment_with_no_known_value", f"{T}::test_the_segment_check_reads_the_clock_at_the_first_free_segment_then_every_32nd", f"{T}::test_a_text_that_starts_with_a_placeholder_trips_the_segment_check"]),
 ("N3c sweep: the old cadence `i % 64 == 0` (an empty first segment skipped before it)",
  "            free += 1\n            if (\n                deadline is not None and (free - 1) % 32 == 0", "            free += 1\n            if (\n                deadline is not None and i % 64 == 0",
  [f"{T}::test_the_segment_check_reads_the_clock_at_the_first_free_segment_then_every_32nd", f"{T}::test_a_text_that_starts_with_a_placeholder_trips_the_segment_check"]),
 ("N4 scan: `work` counts only the tokens that have a form",
  "        for m in _PLACEHOLDER.finditer(out):\n            work += 1\n            if work >= _SPELL_CHECK_EVERY:", "        for m in _PLACEHOLDER.finditer(out):\n            work += 1 if m.group(1) in self._spelled else 0\n            if work >= _SPELL_CHECK_EVERY:",
  [f"{T}::test_the_token_check_cadence_counts_tokens_with_no_form_too", f"{T}::test_the_spelled_scan_checks_the_deadline_for_a_token_that_has_no_form"]),
 ("M3 redact_many: re-read every string on a flip, unchecked (round 4 behaviour)",
  "        for n in range(flipped_at + 1):\n            r._check_deadline()\n            found[n] = r.find(items[n])", "        found = [r.find(item) for item in items]",
  [f"{T}::test_redact_many_checks_the_deadline_between_the_two_reads_when_bank_near_flips", f"{T}::test_redact_many_re_reads_only_the_strings_read_before_the_flip"]),
 ("N9 scan: quadratic (every token compares every registered form)",
  "            node = self._spelled.get(m.group(1))\n            if node is None:\n                continue\n            at, after, back",
  "            node = self._spelled.get(m.group(1))\n            for _o in list(self._spelled_at.values()):\n                _f = _PLACEHOLDER.search(_o)\n                if _f and out.startswith(_o, m.start() - _f.start()):\n                    pass\n            if node is None:\n                continue\n            at, after, back",
  [f"{T}::test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses", f"{T}::test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered", f"{T}::test_hostile_forms_with_500_distinct_prefix_lengths_are_scanned_in_linear_time"]),
]
for name, old, new, tests in MUTANTS:
    assert orig.count(old) == 1, name
    open(P, "w").write(orig.replace(old, new))
    try:
        r = subprocess.run(["uv", "run", "--all-extras", "--group", "test", "pytest", "-q", "-p", "no:cacheprovider", "-n", "0", *tests], capture_output=True, text=True)
        tail = "\n".join(l for l in r.stdout.splitlines() if l.startswith(("FAILED", "ERROR")) or " passed" in l or " failed" in l)
        print(f"## mutant: {name}\n{tail}\n")
    finally:
        open(P, "w").write(orig)
