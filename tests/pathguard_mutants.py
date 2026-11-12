"""Mutants of ``pathguard`` and ``atomic_write`` (one reverted rule each), run by the P1m runner (``tools/mutation_runner.py``).

Form of ``tests/stage_mutants.py``: each mutant reverts ONE guard in a temp copy of the package; the test in ``killer`` must
fail first (and be the only test run), and its first failing line must hold ``expect`` (a fragment of the assertion MESSAGE).
One mutant per rule R1 to R11 of ``pathguard`` (R4, R5, R8 and R11 have a second one for their second place), plus one for each of
``O_EXCL``, the temp-file removal, the ``component`` call on every name and the ``.tmp`` suffix, the random temp name and the
kept "escapes" wording of ``config.confined``. Not collected by pytest. Run from the repo root:

    python tests/pathguard_mutants.py            # all mutants; exit 1 if any is not good
    python tests/pathguard_mutants.py R7         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_pathguard.py"
PIN = "tests/test_pathguard::"
PG = "src/hadavin_sdk/pathguard.py"
AT = "src/hadavin_sdk/k1b/atomic.py"
CFG = "src/hadavin_sdk/config.py"


def mutant(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


SEP = 'if "/" in name or "\\\\" in name:'
M = [
    mutant(
        "R1 empty and dot names accepted",
        PG,
        '    if name in ("", ".", ".."):',
        "    if name in ():",
        "test_r1_empty_and_dot_names_are_refused",
        "R1 not refused",
    ),
    mutant(
        "R2 a separator is accepted",
        PG,
        "    " + SEP,
        "    if False:",
        "test_r2_a_separator_is_refused_on_every_os",
        "R2 not refused",
    ),
    mutant(
        "R3 a colon is accepted",
        PG,
        '    if ":" in name:',
        "    if False:",
        "test_r3_a_colon_is_refused_on_every_os",
        "R3 not refused",
    ),
    mutant(
        "R4a a control character in a name is accepted",
        PG,
        "    if _CONTROL.search(name):",
        "    if False:",
        "test_r4_a_control_character_is_refused_in_a_name",
        "R4 not refused",
    ),
    mutant(
        "R4b a control character in an operator path is accepted",
        PG,
        "    if _CONTROL.search(text):",
        "    if False:",
        "test_r4_a_control_character_is_refused_in_an_operator_path",
        "R4 not refused",
    ),
    mutant(
        "R5a a name over 255 bytes is accepted",
        PG,
        '    if len(name.encode("utf-8", errors="surrogatepass")) > MAX_COMPONENT_BYTES:',
        "    if False:",
        "test_r5_a_name_over_255_utf8_bytes_is_refused",
        "R5 not refused",
    ),
    mutant(
        "R5b a path over 4096 characters is accepted",
        PG,
        "    if len(text) > MAX_PATH_CHARS:",
        "    if False:",
        "test_r5_a_path_over_4096_characters_is_refused",
        "R5 not refused",
    ),
    mutant(
        "R6 a trailing dot or space is accepted",
        PG,
        '    if name[-1] in ". ":',
        "    if False:",
        "test_r6_a_trailing_dot_or_space_is_refused",
        "R6 not refused",
    ),
    mutant(
        "R7a a device name is accepted",
        PG,
        '    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:',
        "    if False:",
        "test_r7_a_reserved_device_name_is_refused",
        "R7 not refused",
    ),
    mutant(
        "R7b the superscript COM and LPT forms are accepted",
        PG,
        '"0123456789\\u00b9\\u00b2\\u00b3"',
        '"0123456789"',
        "test_r7_a_reserved_device_name_is_refused",
        "R7 not refused",
    ),
    mutant(
        "R8a join accepts a path that leaves the base",
        PG,
        "    real = _resolve(candidate, what, strict=must_exist)\n    if not real.is_relative_to(root):",
        "    real = _resolve(candidate, what, strict=must_exist)\n    if False:",
        "test_r8_a_link_out_of_the_base_is_refused",
        "R8 not refused (join",
    ),
    mutant(
        "R8b inside accepts a path that leaves the base",
        PG,
        "    real = _resolve(Path(path), what, strict=must_exist)\n    if not real.is_relative_to(root):",
        "    real = _resolve(Path(path), what, strict=must_exist)\n    if False:",
        "test_r8_a_link_out_of_the_base_is_refused",
        "R8 not refused (inside",
    ),
    mutant(
        "R9 a rooted or UNC backslash name is accepted",
        PG,
        "    " + SEP,
        '    if "/" in name:',
        "test_r9_absolute_drive_rooted_and_unc_names_are_refused",
        "not refused (rooted",
    ),
    mutant(
        "R10 a NUL in a path is not turned into a refusal",
        PG,
        "_RESOLVE_ERRORS = (OSError, RuntimeError, ValueError)",
        "_RESOLVE_ERRORS = (OSError, RuntimeError)",
        "test_r10_a_path_that_cannot_be_resolved_is_refused",
        "R10 not refused",
    ),
    mutant(
        "R11a a folder named as a file is accepted",
        PG,
        '    if kind == "file" and not path.is_file():',
        "    if False:",
        "test_r11_the_wrong_type_is_refused",
        "R11 not refused (file wanted",
    ),
    mutant(
        "R11b a file named as a folder is accepted",
        PG,
        '    if kind == "dir" and not path.is_dir():',
        "    if False:",
        "test_r11_the_wrong_type_is_refused",
        "R11 not refused (folder wanted",
    ),
    mutant(
        "X1 the temp file is not created exclusively (O_EXCL)",
        AT,
        "    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL\n",
        "    flags = os.O_WRONLY | os.O_CREAT\n",
        "test_atomic_write_creates_its_temp_file_exclusively",
        "O_EXCL missing",
    ),
    mutant(
        "X2 the temp file is not removed after a failed rename",
        AT,
        "        os.replace(tmp, final)\n    except BaseException:\n        tmp.unlink(missing_ok=True)\n        raise\n",
        "        os.replace(tmp, final)\n    except BaseException:\n        raise\n",
        "test_atomic_write_removes_its_temp_file_when_the_rename_fails",
        "left after a failed rename",
    ),
    mutant(
        "X3 join does not check each name (the component call)",
        PG,
        "    for name in names:\n        _check_name(name, what)\n    root = _resolve(Path(base), what, strict=False)\n    candidate",
        "    root = _resolve(Path(base), what, strict=False)\n    candidate",
        "test_join_applies_component_to_every_name",
        "component not applied",
    ),
    mutant(
        "X4 the temp name loses its .tmp suffix",
        AT,
        '.{secrets.token_hex(8)}.tmp"',
        '.{secrets.token_hex(8)}.part"',
        "test_atomic_write_temp_name_keeps_the_tmp_suffix",
        "lost its .tmp suffix",
    ),
    mutant(
        "X5 the temp name is the same every time",
        AT,
        "{secrets.token_hex(8)}",
        "{'0' * 16}",
        "test_atomic_write_temp_name_is_random_and_not_chosen_by_the_caller",
        "same twice",
    ),
    mutant(
        "X6 config.confined loses its pinned word escapes",
        CFG,
        'f"path escapes its folder: {relative}"',
        'f"path leaves its folder: {relative}"',
        "test_confined_keeps_its_pinned_wording_for_a_dotdot_and_for_a_link",
        "did not match",
    ),
]


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
