"""The mutants of the safe reset (``src/hadavin_sdk/safe_reset.py``), run by the P1m runner (``tools/mutation_runner.py``).

They are NOT in ``tests/mutation_runner_mutants.py`` or ``tests/stage_mutants.py`` (the meta-tests of those files pin
their own lists). Same runner, same judge, a separate list. Each mutant reverts ONE guard in a temp copy of the package;
the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment of the assertion
MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/reset_mutants.py            # all mutants; exit 1 if any is not good
    python tests/reset_mutants.py M3         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_safe_reset.py"
PIN = "tests/test_safe_reset::"
SR = "src/hadavin_sdk/safe_reset.py"
CFG = "src/hadavin_sdk/config.py"


def mutant(name, file, old, new, killer, expect, **extra):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer, **extra
    )


M = [
    mutant(
        "M1 pilot and prod may be reset",
        SR,
        "if is_live(cfg.environment):",
        "if False:",
        "test_only_the_demo_stage_may_be_reset",
        "was reset",
    ),
    mutant(
        "M2 a stage name is not checked at load",
        SR,
        "if value not in STAGES:",
        "if False:",
        "test_a_value_that_is_not_a_stage_is_refused_as_a_config_error",
        "was accepted as a stage",
    ),
    mutant(
        "M3 a path is not resolved and confined",
        SR,
        "path = confined(data, name)",
        "path = data / name",
        "test_a_path_that_leaves_the_data_folder_is_refused_and_nothing_is_deleted",
        "escape was accepted",
    ),
    mutant(
        "M4 the data folder itself may be a target",
        SR,
        "if path == data:",
        "if False:",
        "test_the_data_folder_itself_is_never_a_target",
        "data folder itself was not refused",
    ),
    mutant(
        "M5 a live process does not refuse",
        SR,
        "if process_alive(int(text)):",
        "if False:",
        "test_a_live_process_in_a_pid_file_refuses_and_nothing_is_deleted",
        "a live process did not refuse",
    ),
    mutant(
        "M6 an ended but uncollected process counts as running",
        SR,
        'return _state(pid) != "Z"',
        "return True",
        "test_an_ended_but_uncollected_process_counts_as_gone",
        "was taken for a running process",
    ),
    mutant(
        "M7 pid zero is not refused by its own check",
        SR,
        " or int(text) == 0",
        "",
        "test_pid_zero_is_refused_before_any_signal_is_sent",
        "pid zero was not refused",
    ),
    mutant(
        "M8 a held lock does not refuse",
        SR,
        "if held:",
        "if False:",
        "test_a_lock_held_by_another_process_refuses",
        "a held lock did not refuse",
    ),
    mutant(
        "M9 a folder at the lock path is taken for a free lock",
        SR,
        "if not stat.S_ISREG(",
        "if False and not stat.S_ISREG(",
        "test_a_lock_that_cannot_be_tested_refuses",
        "an untestable lock did not refuse",
    ),
    mutant(
        "M10 an answering port does not refuse",
        SR,
        "if answers(port):",
        "if False:",
        "test_a_port_that_answers_refuses",
        "an answering port did not refuse",
    ),
    mutant(
        "M11 the dry run deletes",
        SR,
        "    if apply:\n        path.unlink()",
        "    if True:\n        path.unlink()",
        "test_a_dry_run_is_the_default_and_deletes_nothing",
        "the dry run deleted a file",
    ),
    mutant(
        "M12 the home folder is accepted as the data folder",
        SR,
        "or data == Path.home().resolve()",
        "or False",
        "test_a_data_folder_that_is_a_root_or_home_is_refused",
        "a home folder was accepted",
    ),
    mutant(
        "M12b a folder above the home folder is accepted as the data folder",
        SR,
        "or data in Path.home().resolve().parents",
        "or False",
        "test_a_data_folder_that_is_a_root_or_home_is_refused",
        "a folder above home was accepted",
    ),
    mutant(
        "M13 a folder is deleted as a file",
        SR,
        "            if path.is_dir():",
        "            if False:",
        "test_a_folder_is_never_deleted",
        "IsADirectoryError",
        allow_crash=True,
        crash_type="IsADirectoryError",
    ),
    mutant(
        "M14 stale pid files are left behind",
        SR,
        "        for path in (*files, *pids):\n            _remove",
        "        for path in files:\n            _remove",
        "test_a_stale_pid_file_is_cleaned_with_the_rest",
        "stale pid file was not cleaned",
    ),
    mutant(
        "M15 an unknown config key is ignored",
        SR,
        'extra="forbid"',
        'extra="ignore"',
        "test_an_unknown_config_key_refuses",
        "an unknown key was ignored",
    ),
    mutant(
        "M16 confined lets a NUL character crash",
        CFG,
        "except (ValueError, OSError, RuntimeError) as exc:",
        "except (OSError, RuntimeError) as exc:",
        "test_confined_refuses_a_nul_character_as_a_config_error",
        "ValueError",
        allow_crash=True,
        crash_type="ValueError",
    ),
    mutant(
        "M17 a pid file outside the data folder is not confined",
        SR,
        "pids = _inside(data, cfg.pid_files)",
        "pids = [data / n for n in cfg.pid_files]",
        "test_a_pid_file_path_outside_the_data_folder_is_refused",
        "a pid file path outside was not refused",
    ),
    mutant(
        "M18 a missing lock file refuses (existence test dropped)",
        SR,
        "        if not os.path.lexists(file):\n            continue\n        try:\n            held",
        "        try:\n            held",
        "test_a_free_lock_file_does_not_refuse_and_a_missing_one_is_not_created",
        "a missing lock file refused",
    ),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(any(o in m.name for o in only) for m in M):
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
