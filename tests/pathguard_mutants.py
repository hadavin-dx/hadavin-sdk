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


def mutant(name, file, old, new, killer, expect, test_file=TEST):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=test_file.removesuffix(".py").replace("/", ".").replace("tests.", "tests/", 1)
        + "::"
        + killer,
    )


PATHCALL = '__import__("pathlib").Path'
SITES = "tests/test_pathguard_sites.py"


def site(name, file, old, new, killer, expect="DID NOT RAISE", test_file=SITES):
    """One converted call site: the guard call replaced by the old unguarded behaviour."""
    return mutant(name, file, old, new, killer, expect, test_file)


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
        "test_r10_a_value_error_from_resolve_is_refused_as_r10",
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
        "    for name in names:\n        _check_name(name, what)\n    _check_text(str(base), what)",
        "    _check_text(str(base), what)",
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
    mutant(
        "R12 a Windows-invalid character in a name is accepted",
        PG,
        "    if _WINDOWS_INVALID.search(name):",
        "    if False:",
        "test_windows_invalid_characters_are_refused_in_a_name_r12",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "R4c join does not check a control character in the base",
        PG,
        "    for name in names:\n        _check_name(name, what)\n    _check_text(str(base), what)\n",
        "    for name in names:\n        _check_name(name, what)\n",
        "test_a_control_character_in_the_base_is_refused_not_only_in_the_names",
        "wrong rule",
        SITES,
    ),
    mutant(
        "R4d inside does not check a control character in the base",
        PG,
        "    _check_text(str(base), what)\n    _check_text(str(path), what)\n    root",
        "    _check_text(str(path), what)\n    root",
        "test_inside_checks_the_base_text_too",
        "wrong rule",
        SITES,
    ),
    mutant(
        "R4e operator_text checks nothing",
        PG,
        "    _check_text(str(path), what)\n\n\ndef operator_dir",
        "    pass\n\n\ndef operator_dir",
        "test_operator_text_refuses_a_control_character",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "R4f the explicit control check does not rely on resolve (3.13)",
        PG,
        '    if _CONTROL.search(text):\n        raise _refuse("R4", what, "contains a control character")\n    _check_length',
        "    _check_length",
        "test_the_nul_is_refused_even_when_resolve_would_not_raise",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "R4g the C1 and invisible characters are not in the control set",
        PG,
        'r"[\\x00-\\x1f\\x7f-\\x9f\\u061c\\u200b-\\u200f\\u2028-\\u202e\\u2066-\\u2069\\ufeff]"',
        'r"[\\x00-\\x1f]"',
        "test_every_public_function_refuses_a_control_character_explicitly",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "R-pickle PathRefused loses its rule through pickle",
        PG,
        "        return (PathRefused, (self.rule, str(self)))",
        "        return (ConfigError, (str(self),))",
        "test_pathrefused_keeps_its_rule_through_copy_and_pickle",
        "a copy lost its class",
        SITES,
    ),
    mutant(
        "G atomic_write replaces an existing symlink as the final name",
        AT,
        "    if os.path.islink(Path(base) / name):",
        "    if False:",
        "test_atomic_write_refuses_a_symlink_name_even_when_its_target_is_inside_the_folder",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "G2 atomic_write uses its own limit, not the shared one",
        AT,
        "> pathguard.MAX_WRITE_NAME_BYTES:",
        "> pathguard.MAX_COMPONENT_BYTES:",
        "test_atomic_write_refuses_the_longest_name_plus_one",
        "assert",
        SITES,
    ),
    site(
        "S-bundle the case-id length is not checked at load",
        "src/hadavin_sdk/k1b/bundle.py",
        '    if len(f"{case}.json".encode()) > pathguard.MAX_WRITE_NAME_BYTES:',
        "    if False:",
        "test_site_bundle_load_bundle_refuses_a_long_case_id_at_load",
        "Regex pattern did not match",
    ),
    site(
        "S-bundles load_bundles folder is not guarded",
        "src/hadavin_sdk/k1b/bundle.py",
        '        root = pathguard.operator_dir(root, what="bundles folder")',
        "        root = " + PATHCALL + "(root)",
        "test_site_bundle_load_bundles_refuses_a_nul_folder_and_maps_missing",
        "not refused",
    ),
    site(
        "S-score outputs folder is not guarded",
        "src/hadavin_sdk/k1b/score.py",
        '        return pathguard.operator_dir(out, what="outputs folder")',
        "        return " + PATHCALL + "(out)",
        "test_site_score_outputs_folder_nul_and_missing",
    ),
    site(
        "S-score _check_layout does not re-check its folder",
        "src/hadavin_sdk/k1b/score.py",
        '    out = pathguard.operator_dir(_outputs_dir(out), what="outputs folder")\n    names',
        "    out = " + PATHCALL + "(out)\n    names",
        "test_site_score_check_layout_rechecks_its_own_folder",
        "not refused",
    ),
    site(
        "S-causelist folder is not guarded",
        "src/hadavin_sdk/k1b/causelist.py",
        '        directory = pathguard.operator_dir(directory, what="cause list folder")',
        "        directory = " + PATHCALL + "(directory)",
        "test_site_causelist_folder_nul_gives_the_one_wording",
        "Regex pattern did not match",
    ),
    site(
        "S-replay outputs_files folder is not guarded",
        "src/hadavin_sdk/k1b/replay.py",
        '    out = pathguard.operator_dir(out, what="outputs folder")\n    found',
        "    out = " + PATHCALL + "(out)\n    found",
        "test_site_replay_output_folder_nul_is_refused_and_writes_nothing",
        "not refused",
    ),
    site(
        "S-replay FAILED.txt is not written after output exists",
        "src/hadavin_sdk/k1b/replay.py",
        "        if progress.output_created:",
        "        if False:",
        "test_a_path_refusal_after_output_exists_still_leaves_failed_txt",
        "no FAILED.txt marker",
    ),
    site(
        "S-replay the output-created flag is never set",
        "src/hadavin_sdk/k1b/replay.py",
        "        progress.output_created = True",
        "        progress.output_created = False",
        "test_a_path_refusal_after_output_exists_still_leaves_failed_txt",
        "no FAILED.txt marker",
    ),
    site(
        "S-signer private key file is not guarded",
        "src/hadavin_sdk/audit/signer.py",
        '    real = pathguard.operator_file(path, what="private key file")',
        "    real = " + PATHCALL + "(path)",
        "test_site_signer_key_file_nul_and_missing",
        "not refused",
    ),
    site(
        "S-signer public key file is not guarded",
        "src/hadavin_sdk/audit/signer.py",
        '    real = pathguard.operator_file(path, what="public key file")',
        "    real = " + PATHCALL + "(path)",
        "test_site_signer_key_file_nul_and_missing",
        "not refused",
    ),
    site(
        "S-local_dir root is not guarded",
        "src/hadavin_sdk/audit/local_dir.py",
        '        self.root = pathguard.operator_dir(root, what="audit folder", must_exist=False)',
        "        self.root = " + PATHCALL + "(root)",
        "test_site_local_dir_root_nul_and_event_id",
        "DID NOT RAISE",
    ),
    site(
        "S-local_dir outbox final name is not joined through the guard",
        "src/hadavin_sdk/audit/local_dir.py",
        '                final = pathguard.join(\n                    self.outbox, f"{event.event_id}.json", what="audit outbox file"\n                )',
        '                final = self.outbox / f"{event.event_id}.json"',
        "test_site_local_dir_outbox_refuses_a_device_name_as_the_event_id",
        "outbox",
    ),
    site(
        "S-vault jwt path is not guarded",
        "src/hadavin_sdk/actions/secrets_vault.py",
        '                jwt_file = pathguard.operator_file(\n                    settings.jwt_path, what="vault sign-in token file", must_exist=False\n                )',
        '                jwt_file = __import__("pathlib").Path(settings.jwt_path)',
        "test_vault_kubernetes_token_path_with_a_nul_is_a_config_error",
        "not refused",
    ),
    site(
        "S-config root is not guarded",
        "src/hadavin_sdk/config.py",
        '        root = pathguard.operator_dir(root, what="config folder", must_exist=False)',
        "        root = " + PATHCALL + "(root)",
        "test_site_config_root_and_golden_dir_nul",
        "not refused",
    ),
    site(
        "S-cli --config is not guarded",
        "src/hadavin_sdk/cli.py",
        '            pathguard.operator_dir(args.config, what="config folder", must_exist=False)',
        "            args.config",
        "test_site_cli_config_flag_nul_is_refused",
        "assert 3 == 2",
    ),
    site(
        "S-cli score outputs is not guarded",
        "src/hadavin_sdk/cli.py",
        '        outputs = pathguard.operator_dir(args.outputs, what="outputs folder")',
        "        outputs = args.outputs",
        "test_score_with_a_nul_in_the_outputs_path_is_refused_with_exit_2",
        "assert 'outputs folder",
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
        sorted({TEST} | {m.test_file for m in M}),
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
