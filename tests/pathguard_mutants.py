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
B3 = "tests/test_pathguard_batch3.py"
HF = "src/hadavin_sdk/hashing.py"
SF = "src/hadavin_sdk/actions/secrets_file.py"


def mutant(name, file, old, new, killer, expect, test_file=TEST, **kw):
    # a parametrized killer: the failing id carries ``[param]``, so the exact-id pin is dropped and ``only_test`` (the whole
    # function name, every parameter) is the pin
    pin = kw.pop("pinned", None)
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
        + killer
        if pin is None
        else pin,
        **kw,
    )


PATHCALL = '__import__("pathlib").Path'
SITES = "tests/test_pathguard_sites.py"


def site(name, file, old, new, killer, expect="DID NOT RAISE", test_file=SITES, **kw):
    """One converted call site: the guard call replaced by the old unguarded behaviour."""
    return mutant(name, file, old, new, killer, expect, test_file, **kw)


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
        '    if len(text.encode("utf-8", errors="surrogatepass")) > MAX_PATH_BYTES:',
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
        "R8 a path that leaves the base is accepted (join and inside share the tail)",
        PG,
        "    if not real.is_relative_to(root):",
        "    if False:",
        "test_r8_a_link_out_of_the_base_is_refused",
        "R8 not refused",
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
        '    if (kind == "file" and not real.is_file()) or (kind == "dir" and not real.is_dir()):',
        "    if False:",
        "test_r11_the_wrong_type_is_refused",
        "file wanted, folder found",
    ),
    mutant(
        "R11b a file named as a folder is accepted",
        PG,
        '"not a file" if kind == "file" else "not a folder"',
        '"not a file"',
        "test_r11_the_wrong_type_is_refused",
        "R11 text for a file named as a folder is wrong",
    ),
    mutant(
        "X1 the temp file is not created exclusively (O_EXCL)",
        AT,
        "    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL\n",
        "    flags = os.O_WRONLY | os.O_CREAT\n",
        "test_atomic_write_creates_its_temp_file_exclusively",
        "DID NOT RAISE",
    ),
    mutant(
        "X2 the temp file is not removed after a failed rename",
        AT,
        "        os.replace(tmp, final)\n    except OSError as exc:\n        tmp.unlink(missing_ok=True)\n",
        "        os.replace(tmp, final)\n    except OSError as exc:\n",
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
        "test_pin_confined_keeps_its_pinned_wording_for_a_dotdot_and_for_a_link",
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
        "    _check_text(str(base), what)\n    return _within(_resolve(",
        "    return _within(_resolve(",
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
        '    if _CONTROL.search(text):\n        raise _refuse("R4", what, "contains a control character")\n    if len(text.encode',
        "    if len(text.encode",
        "test_the_nul_is_refused_even_when_resolve_would_not_raise",
        "DID NOT RAISE",
        SITES,
    ),
    mutant(
        "R4g the C1 and invisible characters are not in the control set",
        PG,
        '    + "".join(f"{re.escape(chr(lo))}-{re.escape(chr(hi))}" for _, lo, hi in CONTROL_RANGES)',
        '    + "".join(f"{re.escape(chr(lo))}-{re.escape(chr(hi))}" for _, lo, hi in CONTROL_RANGES[:1])',
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
        '    try:\n        root = pathguard.operator_dir(root, what="bundles folder")\n    except pathguard.PathRefused as exc:\n        raise pathguard.mapped(\n            exc, R10="bundles folder does not exist", R11="bundles folder does not exist"\n        ) from None\n',
        "    root = " + PATHCALL + "(root)\n",
        "test_site_bundle_load_bundles_refuses_a_nul_folder_and_maps_missing",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
    ),
    site(
        "S-score outputs folder is not guarded",
        "src/hadavin_sdk/k1b/score.py",
        '    try:\n        return pathguard.operator_dir(out, what="outputs folder")\n    except pathguard.PathRefused as exc:\n        raise pathguard.mapped(\n            exc, R10="outputs folder does not exist", R11="outputs folder does not exist"\n        ) from None\n',
        "    return " + PATHCALL + "(out)\n",
        "test_site_score_outputs_folder_nul_and_missing",
    ),
    site(
        "S-score _check_layout does not re-check its folder",
        "src/hadavin_sdk/k1b/score.py",
        '    out = pathguard.operator_dir(outputs_dir(out), what="outputs folder")\n    names',
        "    out = " + PATHCALL + "(out)\n    names",
        "test_site_score_check_layout_rechecks_its_own_folder",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
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
        "test_site_replay_output_folder_nul_is_refused",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
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
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
    ),
    site(
        "S-signer public key file is not guarded",
        "src/hadavin_sdk/audit/signer.py",
        '    real = pathguard.operator_file(path, what="public key file")',
        "    real = " + PATHCALL + "(path)",
        "test_site_signer_key_file_nul_and_missing",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
    ),
    site(
        "S-local_dir root is not guarded",
        "src/hadavin_sdk/audit/local_dir.py",
        '        self.root = pathguard.operator_dir(root, what="audit folder", must_exist=False)',
        "        self.root = " + PATHCALL + "(root)",
        "test_site_local_dir_root_nul_and_event_id",
        "DID NOT RAISE",
    ),
    # note: this guard is reachable only by the monkeypatched batch3 test (a real event id cannot be a device name)
    site(
        "S-local_dir outbox final name is not joined through the guard",
        "src/hadavin_sdk/audit/local_dir.py",
        '                final = pathguard.join(\n                    self.outbox, f"{event.event_id}.json", what="audit outbox file"\n                )',
        '                final = self.outbox / f"{event.event_id}.json"',
        "test_local_dir_outbox_fallback_refuses_a_device_name_as_the_event_id",
        "device name reached",
        test_file=B3,
    ),
    site(
        "S-vault jwt path is not guarded",
        "src/hadavin_sdk/actions/secrets_vault.py",
        '                jwt_file = pathguard.operator_file(\n                    settings.jwt_path, what="vault sign-in token file", must_exist=False\n                )',
        '                jwt_file = __import__("pathlib").Path(settings.jwt_path)',
        "test_vault_kubernetes_token_path_with_a_nul_is_a_config_error",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
    ),
    site(
        "S-config root is not guarded",
        "src/hadavin_sdk/config.py",
        '        root = pathguard.operator_dir(root, what="config folder", must_exist=False)',
        "        root = " + PATHCALL + "(root)",
        "test_site_config_root_nul",
        "must be set",
        allow_crash=True,
        crash_type="ConfigError",
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
        "    outputs = outputs_dir(\n        args.outputs\n    )",
        "    outputs = (\n        args.outputs\n    )",
        "test_score_with_a_nul_in_the_outputs_path_is_refused_with_exit_2",
        "assert 'outputs folder",
    ),
]


# ---------------------------------------------------------------------------------------------------------------------
# Batch 3 rows (SONAR-PATH): one row per range of R4, per part of R6 and R7, per call of the text check, per converted site
# and per refusal added to ``atomic_write``. ``b3`` rows run only a named test of ``tests/test_pathguard_batch3.py``.
# ---------------------------------------------------------------------------------------------------------------------
RANGES = (
    ("C0 controls and NUL", 0x0000, 0x001F),
    ("DEL and C1 controls", 0x007F, 0x009F),
    ("soft hyphen", 0x00AD, 0x00AD),
    ("combining grapheme joiner", 0x034F, 0x034F),
    ("Arabic letter mark", 0x061C, 0x061C),
    ("Hangul fillers", 0x115F, 0x1160),
    ("Khmer inherent vowels", 0x17B4, 0x17B5),
    ("Mongolian vowel separator", 0x180E, 0x180E),
    ("zero-width and direction marks", 0x200B, 0x200F),
    ("line and paragraph separators and bidirectional embeddings", 0x2028, 0x202E),
    ("word joiner, invisible operators, isolates and deprecated format characters", 0x2060, 0x206F),
    ("braille blank", 0x2800, 0x2800),
    ("Hangul filler", 0x3164, 0x3164),
    ("variation selectors", 0xFE00, 0xFE0F),
    ("byte order mark", 0xFEFF, 0xFEFF),
    ("halfwidth Hangul filler", 0xFFA0, 0xFFA0),
    ("interlinear annotation", 0xFFF9, 0xFFFB),
    ("musical symbol format characters", 0x1D173, 0x1D17A),
    ("tag characters", 0xE0000, 0xE007F),
    ("variation selectors supplement", 0xE0100, 0xE01EF),
)


B4 = "tests/test_pathguard_batch4.py"


def b4(name, file, old, new, killer, expect="DID NOT RAISE", test_file=B4, **kw):
    return mutant(name, file, old, new, killer, expect, test_file, **kw)


def b3(name, file, old, new, killer, expect="DID NOT RAISE", test_file=B3, **kw):
    return mutant(name, file, old, new, killer, expect, test_file, **kw)


def _range_rows():
    rows = []
    for i, (label, lo, hi) in enumerate(RANGES):
        line = f'    ("{label}", 0x{lo:04X}, 0x{hi:04X}),\n'
        killer = f"test_pin_r4_range_{i:02d}"
        rows.append(b3(f"R4-{i:02d} the range is dropped: {label}", PG, line, "", killer))
        if hi > lo:
            rows.append(
                b3(
                    f"R4-{i:02d} the range ends one early: {label}",
                    PG,
                    line,
                    f'    ("{label}", 0x{lo:04X}, 0x{hi - 1:04X}),\n',
                    killer,
                )
            )
            rows.append(
                b3(
                    f"R4-{i:02d} the range starts one late: {label}",
                    PG,
                    line,
                    f'    ("{label}", 0x{lo + 1:04X}, 0x{hi:04X}),\n',
                    killer,
                )
            )
    return rows


M += _range_rows()
M += [
    b3(
        "R6a a trailing dot is accepted",
        PG,
        '    if name[-1] in ". ":',
        '    if name[-1] in " ":',
        "test_pin_r6_a_trailing_dot_is_refused",
    ),
    b3(
        "R6b a trailing space is accepted",
        PG,
        '    if name[-1] in ". ":',
        '    if name[-1] in ".":',
        "test_pin_r6_a_trailing_space_is_refused",
    ),
    b3(
        "R7c the part before the LAST dot decides, not the first",
        PG,
        '    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:',
        '    if name.rsplit(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:',
        "test_pin_r7_the_part_before_the_first_dot_decides",
    ),
    b3(
        "R7d spaces before the dot hide a device name",
        PG,
        '    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:',
        '    if name.split(".", 1)[0].upper() in _DEVICE_NAMES:',
        "test_pin_r7_spaces_before_the_dot_do_not_hide_a_device_name",
    ),
    b3(
        "R5c join does not check the base text",
        PG,
        "    _check_text(str(base), what)\n    root = _resolve(Path(base), what, strict=False)\n    return _within(root, root.joinpath",
        "    root = _resolve(Path(base), what, strict=False)\n    return _within(root, root.joinpath",
        "test_pin_r5_join_refuses_a_wide_base_text_that_resolves_short",
        "DID NOT RAISE",
    ),
    b3(
        "R5d join does not check the joined path",
        PG,
        "    _check_text(str(path), what)\n    real = _resolve(path, what, strict=must_exist)",
        "    real = _resolve(path, what, strict=must_exist)",
        "test_pin_r5_join_refuses_a_long_joined_path_when_base_and_names_are_short",
    ),
    b3(
        "R5e inside does not check the base text",
        PG,
        "    _check_text(str(base), what)\n    return _within(_resolve(",
        "    return _within(_resolve(",
        "test_pin_r5_inside_refuses_a_long_base_text",
        "DID NOT RAISE",
    ),
    b3(
        "R5f inside does not check the path text (shared tail)",
        PG,
        "    _check_text(str(path), what)\n    real = _resolve(path, what, strict=must_exist)",
        "    real = _resolve(path, what, strict=must_exist)",
        "test_pin_r5_inside_refuses_a_long_path_text",
        "DID NOT RAISE",
    ),
    b3(
        "R5g the operator check does not check the text",
        PG,
        "    _check_text(str(path), what)\n    real = _resolve(Path(path), what, strict=must_exist)",
        "    real = _resolve(Path(path), what, strict=must_exist)",
        "test_pin_r5_operator_dir_refuses_a_long_text",
        "DID NOT RAISE",
    ),
    b3(
        "R5h operator_text does not check the text",
        PG,
        "    _check_text(str(path), what)\n\n\ndef operator_dir",
        "    pass\n\n\ndef operator_dir",
        "test_pin_r5_operator_text_refuses_a_long_text",
    ),
    b3(
        "R5i the text check does not check the length",
        PG,
        '    if len(text.encode("utf-8", errors="surrogatepass")) > MAX_PATH_BYTES:\n        raise _refuse("R5", what, "too long")\n\n\ndef _within',
        "\n\ndef _within",
        "test_pin_r5_operator_text_refuses_a_long_text",
    ),
    b3(
        "R10b a RuntimeError from resolve (a symlink loop on 3.12) escapes",
        PG,
        "_RESOLVE_ERRORS = (OSError, RuntimeError, ValueError)",
        "_RESOLVE_ERRORS = (OSError, ValueError)",
        "test_pin_r10_a_runtime_error_from_resolve_is_refused_as_r10",
        "Symlink loop",
        allow_crash=True,
        crash_type="RuntimeError",
    ),
    b3(
        "R11c an existing file is accepted as a folder when it need not exist",
        PG,
        "    if must_exist or real.exists():",
        "    if must_exist:",
        "test_pin_r11_an_existing_file_is_refused_as_a_folder_even_when_it_need_not_exist",
    ),
    b3(
        "U1 mapped never turns a rule into the plain message",
        PG,
        "    return ConfigError(words[exc.rule]) if exc.rule in words else exc",
        "    return exc",
        "test_mapped_turns_only_the_listed_rules_into_one_plain_message",
        "AssertionError",
    ),
    b3(
        "X7 a folder is replaced, not refused",
        AT,
        '    if final.is_dir():  # a folder is never replaced; the text must not hold the path\n        raise pathguard.PathRefused("R13", "output file: a folder is not replaced")\n',
        "",
        "test_atomic_write_onto_a_folder_is_a_refusal_with_no_path_in_the_text",
        "IsADirectoryError",
        allow_crash=True,
        crash_type="IsADirectoryError",
    ),
    b3(
        "X8 a taken temp name raises the raw OS error",
        AT,
        '        raise pathguard.PathRefused("R13", "temp file: the name is already in use") from None',
        "        raise",
        "test_atomic_write_with_a_taken_temp_name_leaves_the_existing_file_untouched",
        "FileExistsError",
        allow_crash=True,
        crash_type="FileExistsError",
    ),
    b3(
        "X9 the temp path is not checked",
        AT,
        '    tmp = pathguard.join(final.parent, f".{name}.{secrets.token_hex(8)}.tmp", what="temp file")',
        '    tmp = final.parent / f".{name}.{secrets.token_hex(8)}.tmp"',
        "test_atomic_write_checks_the_temp_path_length_not_only_the_final_one",
    ),
    b3(
        "X10 the temp file stays when fdopen is interrupted",
        AT,
        "    except BaseException:\n        os.close(fd)",
        "    except Exception:\n        os.close(fd)",
        "test_atomic_write_removes_its_temp_file_when_fdopen_is_interrupted",
        ".tmp",
    ),
    b3(
        "X11 the temp file stays when the rename is interrupted",
        AT,
        "    except BaseException:\n        tmp.unlink(missing_ok=True)\n        raise\n\n\ndef _without_path",
        "    except Exception:\n        tmp.unlink(missing_ok=True)\n        raise\n\n\ndef _without_path",
        "test_atomic_write_removes_its_temp_file_when_the_rename_is_interrupted",
        ".tmp",
    ),
    b3(
        "X12 the file is not flushed to disk before the rename",
        AT,
        "            os.fsync(f.fileno())\n",
        "            pass\n",
        "test_atomic_write_flushes_the_file_to_disk_before_the_rename",
        "assert 0 == 1",
    ),
    # converted sites (one row each; every killer uses a character the OS accepts, or a link out, so a lost guard shows)
    b3(
        "S-score _read_json reads an unguarded name",
        "src/hadavin_sdk/k1b/score.py",
        '        path = pathguard.join(base, *names, what="output file", must_exist=True, kind="file")',
        "        path = base.joinpath(*names)",
        "test_site_score_read_json_refuses_a_file_name_with_a_control_character",
    ),
    b3(
        "S-score _recorded_digest reads an unguarded name",
        "src/hadavin_sdk/k1b/score.py",
        '        target = pathguard.join(\n            out, "outputs.sha256", what="replay digest file", must_exist=True, kind="file"\n        )',
        '        target = out / "outputs.sha256"',
        "test_site_score_recorded_digest_does_not_read_a_file_behind_a_link",
        "0000",
    ),
    b3(
        "S-score load_answers is not guarded",
        "src/hadavin_sdk/k1b/score.py",
        '        real = pathguard.operator_file(path, what="answers file")\n        raw = real.read_bytes()',
        "        raw = " + PATHCALL + "(path).read_bytes()",
        "test_site_score_answers_file_with_a_control_character_in_its_name_is_refused",
    ),
    b3(
        "S-score the run folder join is not guarded",
        "src/hadavin_sdk/k1b/score.py",
        '        rdir = pathguard.join(out, f"run{i}", what="run folder", must_exist=True, kind="dir")\n        meta =',
        '        rdir = out / f"run{i}"\n        meta =',
        "test_site_score_run_folder_join_refuses_a_link_out_when_the_layout_check_is_skipped",
    ),
    b3(
        "S-replay the output folder is not guarded",
        "src/hadavin_sdk/k1b/replay.py",
        '    try:\n        out = pathguard.operator_dir(out, what="replay output folder", must_exist=False)\n    except pathguard.PathRefused as exc:  # it exists and is a file\n        raise pathguard.mapped(exc, R11="replay output folder exists and is not empty") from None\n',
        "    out = " + PATHCALL + "(out)\n",
        "test_replay_with_a_control_character_in_the_output_folder_is_refused_and_writes_nothing",
        "assert not",
    ),
    b3(
        "S-replay a file as the output folder is not mapped to the plain message",
        "src/hadavin_sdk/k1b/replay.py",
        '        raise pathguard.mapped(exc, R11="replay output folder exists and is not empty") from None',
        "        raise",
        "test_pin_replay_into_an_existing_file_says_the_folder_is_not_usable_in_one_wording",
        "AssertionError",
    ),
    b3(
        "S-replay the marker is not written into an empty folder",
        "src/hadavin_sdk/k1b/replay.py",
        '    if out.is_dir():\n        atomic_write(out, "FAILED.txt"',
        '    if out.is_dir() and any(out.iterdir()):\n        atomic_write(out, "FAILED.txt"',
        "test_a_failed_replay_writes_the_marker_even_into_an_empty_folder",
        "assert False",
    ),
    b3(
        "S-replay the marker error replaces the original error",
        "src/hadavin_sdk/k1b/replay.py",
        '                exc.add_note(f"FAILED.txt was not written ({type(second).__name__})")\n',
        "                raise second\n",
        "test_a_marker_that_cannot_be_written_never_replaces_the_original_error",
        "boom",
        allow_crash=True,
        crash_type="RuntimeError",
    ),
    b3(
        "S-replay the run folder is not checked again before a write",
        "src/hadavin_sdk/k1b/replay.py",
        '    return pathguard.join(out, f"run{run_index}", what="run folder", must_exist=True, kind="dir")',
        '    return out / f"run{run_index}"',
        "test_a_run_folder_swapped_for_a_link_mid_run_stops_the_next_write",
        "case-001.js",
    ),
    b3(
        "S-replay outputs_files lists a run folder through an unguarded join",
        "src/hadavin_sdk/k1b/replay.py",
        '        rdir = pathguard.join(out, run.name, what="run folder", must_exist=True)',
        "        rdir = out / run.name",
        "test_site_outputs_files_refuses_a_missing_folder_a_control_character_and_a_link",
    ),
    b3(
        "S-bundle _load_json reads an unguarded name",
        "src/hadavin_sdk/k1b/bundle.py",
        '        target = pathguard.join(\n            root, *rel.split("/"), what="bundle file", must_exist=True, kind="file"\n        )',
        '        target = root.joinpath(*rel.split("/"))',
        "test_site_bundle_load_json_and_text_refuse_a_file_name_with_a_control_character",
    ),
    b3(
        "S-bundle _text reads an unguarded name",
        "src/hadavin_sdk/k1b/bundle.py",
        '        target = pathguard.join(\n            path, *rel.split("/"), what="bundle file", must_exist=True, kind="file"\n        )\n        return target',
        '        target = path.joinpath(*rel.split("/"))\n        return target',
        "test_site_bundle_load_json_and_text_refuse_a_file_name_with_a_control_character",
    ),
    b3(
        "S-causelist _load reads an unguarded name",
        "src/hadavin_sdk/k1b/causelist.py",
        '        path = pathguard.join(directory, name, what="cause list file", must_exist=True, kind="file")',
        "        path = directory / name",
        "test_pin_site_causelist_file_that_is_a_link_out_is_refused",
        "DID NOT RAISE",
    ),
    b3(
        "S-causelist errors keep their chain (bad JSON)",
        "src/hadavin_sdk/k1b/causelist.py",
        '        raise ConfigError(f"cause list: {name} is missing or not valid JSON") from None',
        '        raise ConfigError(f"cause list: {name} is missing or not valid JSON") from exc',
        "test_causelist_errors_carry_no_chain_for_bad_json_and_bad_characters",
        "JSONDecodeError",
        allow_crash=True,
        crash_type="JSONDecodeError",
    ),
    b3(
        "S-bundle errors keep their chain (bad log line)",
        "src/hadavin_sdk/k1b/bundle.py",
        '                except (ValueError, RecursionError):\n                    raise _fail(case, f"{rel} has a line that is not valid JSON") from None',
        '                except (ValueError, RecursionError) as exc:\n                    raise _fail(case, f"{rel} has a line that is not valid JSON") from exc',
        "test_bundle_errors_carry_no_chain_for_a_bad_log_line_and_a_bad_character",
        "chained",
    ),
    b3(
        "S-cli the report folder join is not guarded",
        "src/hadavin_sdk/cli.py",
        '    report_dir = pathguard.join(outputs, REPORT_DIR, what="score report folder")',
        "    report_dir = outputs / REPORT_DIR",
        "test_score_refuses_a_report_folder_that_is_a_link_out_of_the_outputs_folder",
        "the score command went through the link",
    ),
    b3(
        "S-config golden_dir and inputs_dir are not guarded",
        CFG,
        "                raw[key] = pathguard.operator_dir(root / raw[key], what=key, must_exist=False)",
        "                raw[key] = str(root / raw[key])",
        "test_site_config_folder_setting_with_a_control_character_is_refused",
        pinned="",
    ),
    b3(
        "S-config confined does not delegate to pathguard",
        CFG,
        '        return pathguard.inside(base, Path(base) / relative, what="path")',
        "        return (Path(base) / relative).resolve()",
        "test_site_config_confined_delegates_to_pathguard_and_keeps_its_wording",
    ),
    b3(
        "S-signer key_path message holds the resolved key folder",
        "src/hadavin_sdk/audit/signer.py",
        '"the key file is outside the key folder: key files are kept only there "',
        'f"{path} is outside {folder}: key files are kept only there "',
        "test_signer_key_path_refusal_text_holds_no_path",
        "CANARY",
    ),
    b3(
        "S-signer key_path symlink message holds the path",
        "src/hadavin_sdk/audit/signer.py",
        'raise ValueError("the key file is a symlink: a key file is never used through one")',
        'raise ValueError(f"{path} is a symlink: a key file is never used through one")',
        "test_signer_key_path_refusal_text_holds_no_path",
        "CANARY",
    ),
    b3(
        "S-signer key_path makes the folder before it checks the shape",
        "src/hadavin_sdk/audit/signer.py",
        '    pathguard.operator_text(folder, what="key folder")\n    pathguard.operator_text(target, what="key file")\n    folder.mkdir(mode=0o700, parents=True, exist_ok=True)',
        '    folder.mkdir(mode=0o700, parents=True, exist_ok=True)\n    pathguard.operator_text(folder, what="key folder")\n    pathguard.operator_text(target, what="key file")',
        "test_signer_key_path_checks_the_shape_before_it_makes_any_folder",
        "embedded null",
        allow_crash=True,
        crash_type="ValueError",
    ),
    b3(
        "S-local_dir a refused outcome is kept in memory",
        "src/hadavin_sdk/audit/local_dir.py",
        "            self.refused_events += 1\n",
        "            self.refused_events += 1\n            self._pending.append(event)\n",
        "test_local_dir_counts_a_refused_outcome_warns_once_and_keeps_nothing",
        "retried",
    ),
    b3(
        "S-local_dir the refused event id is printed",
        "src/hadavin_sdk/audit/local_dir.py",
        '            raise AuditUnavailable(f"intent: event id refused ({exc.rule})") from None',
        '            raise AuditUnavailable(f"intent {event.event_id!r}: refused ({exc.rule})") from None',
        "test_local_dir_refuses_an_event_id_that_is_not_one_plain_file_name",
        "printed",
        pinned="",
    ),
    b3(
        "S-local_dir reconcile crashes on a corrupt folder that is a link out",
        "src/hadavin_sdk/audit/local_dir.py",
        "                except (pathguard.PathRefused, OSError):\n                    pass\n",
        "                except OSError:\n                    pass\n",
        "test_local_dir_reconcile_leaves_a_corrupt_file_when_the_corrupt_folder_is_a_link_out",
        "ValidationError",
        allow_crash=True,
        crash_type="ValidationError",
    ),
    b3(
        "S-hashing the folder is not guarded",
        "src/hadavin_sdk/hashing.py",
        '    try:\n        base = pathguard.operator_dir(root, what="hash folder")\n    except pathguard.PathRefused as exc:\n        raise pathguard.mapped(\n            exc, R10="hash folder does not exist", R11="hash folder does not exist"\n        ) from None\n',
        "    base = Path(root)\n",
        "test_the_hash_folder_is_checked_and_a_missing_one_has_one_plain_message",
        "DID NOT RAISE",
    ),
    b3(
        "S-secrets_file the folder is not guarded",
        "src/hadavin_sdk/actions/secrets_file.py",
        '        root = pathguard.operator_dir(settings.dir, what="secrets folder")',
        "        root = Path(settings.dir)",
        "test_secrets_folder_is_checked_when_the_provider_is_built",
        "DID NOT RAISE",
    ),
    b3(
        "S-fake_llm the recording folder is not guarded",
        "src/hadavin_sdk/llm/fake.py",
        '        self.recorded_dir = pathguard.operator_dir(\n            recorded_dir, what="recording folder", must_exist=False\n        )',
        "        self.recorded_dir = " + PATHCALL + "(recorded_dir)",
        "test_fake_llm_recording_folder_and_names_go_through_pathguard",
    ),
    b3(
        "S-judge qualify does not check the golden file",
        "src/hadavin_sdk/guard/judge.py",
        '    golden = pathguard.operator_file(golden, what="judge golden file")\n',
        "",
        "test_judge_qualify_checks_the_golden_file_path",
        "No such file",
        allow_crash=True,
        crash_type="FileNotFoundError",
    ),
    b3(
        "S-tools the module name is not checked before a path is built",
        "src/hadavin_sdk/tools.py",
        "    if not all(p.isidentifier() for p in parts):",
        "    if False:",
        "test_pin_tool_module_names_are_checked_before_any_path_is_built",
    ),
    b3(
        "S-config a folder setting that is not text is not explained",
        CFG,
        "                if not isinstance(raw[key], str):\n",
        "                if False:\n",
        "test_site_config_folder_setting_that_is_not_text_says_so_plainly",
        "AssertionError",
        pinned="",
    ),
    b3(
        "H the suppression check is case-sensitive",
        B3,
        '    lowered = text.lower()\n    return [f"{name}: {t}" for t in tokens if t in lowered]',
        '    lowered = text\n    return [f"{name}: {t}" for t in tokens if t in lowered]',
        "test_pin_the_suppression_check_finds_every_spelling_in_a_seeded_line",
        "AssertionError",
    ),
    b4(
        "S-hashing a file name is not confined (the escape wording)",
        HF,
        "        found = confined(base, rel)\n",
        "        found = base / rel\n",
        "test_pin_hash_files_keeps_the_escape_wording_for_a_missing_file_outside_the_folder",
        "wrong wording",
    ),
    b4(
        "S-hashing the strict last check is removed",
        HF,
        '            path = pathguard.inside(base, found, what="hash file", must_exist=True, kind="file")',
        "            path = found",
        "test_pin_hash_files_says_not_a_file_for_a_missing_name_and_a_folder",
        "wrong wording",
    ),
    b4(
        "S-hashing the last check holds the data-name rules (full join, not inside)",
        HF,
        '            path = pathguard.inside(base, found, what="hash file", must_exist=True, kind="file")',
        '            path = pathguard.join(base, *found.relative_to(base).parts, what="hash file", must_exist=True, kind="file")',
        "test_pin_hash_files_reads_a_name_the_caller_chose_even_with_a_colon_or_device_name",
        "wrong wording",
    ),
    b4(
        "S-secrets_file a secret name is not confined (the escape wording)",
        SF,
        "        found = confined(self.root, name)\n",
        "        found = self.root / name\n",
        "test_pin_secrets_file_keeps_the_escape_wording_for_a_missing_name_outside_the_folder",
        "wrong wording",
    ),
    b4(
        "S-secrets_file the strict last check is removed",
        SF,
        '            path = pathguard.inside(\n                self.root, found, what="mounted secret", must_exist=True, kind="file"\n            )',
        "            path = found",
        "test_secrets_file_says_not_found_and_not_a_regular_file",
        "wrong wording",
    ),
    b4(
        "S-secrets_file the last check holds the data-name rules (full join, not inside)",
        SF,
        '            path = pathguard.inside(\n                self.root, found, what="mounted secret", must_exist=True, kind="file"\n            )',
        '            path = pathguard.join(self.root, *found.relative_to(self.root.resolve()).parts, what="mounted secret", must_exist=True, kind="file")',
        "test_pin_secrets_file_reads_a_secret_name_the_operator_chose",
        "wrong wording",
    ),
    b4(
        "S-local_dir the second join into corrupt is removed",
        "src/hadavin_sdk/audit/local_dir.py",
        'os.replace(path, pathguard.join(corrupt, listed, what="audit outbox file"))',
        "os.replace(path, corrupt / listed)",
        "test_local_dir_reconcile_leaves_a_corrupt_file_when_its_name_in_corrupt_is_a_link",
        "moved over a link",
    ),
    b4(
        "S-local_dir a link in the outbox is unlinked through its target",
        "src/hadavin_sdk/audit/local_dir.py",
        '            if path != pathguard.join(self.outbox, what="audit outbox folder") / listed:\n                continue',
        "            pass",
        "test_control_local_dir_reconcile_does_not_follow_a_link_to_another_file_in_the_outbox",
        "followed a link",
    ),
    b4(
        "S-signer the containment call is removed",
        "src/hadavin_sdk/audit/signer.py",
        '        real = pathguard.inside(\n            folder, target.parent.resolve(strict=True) / target.name, what="key file"\n        )',
        "        real = target.parent.resolve(strict=True) / target.name",
        "test_signer_key_path_refuses_a_parent_link_that_resolves_to_a_folder_with_a_control_character",
        "DID NOT RAISE",
    ),
    b4(
        "S-bundle the manifest join is removed",
        "src/hadavin_sdk/k1b/bundle.py",
        '        man_path = pathguard.join(path, "manifest.json", what="bundle file")',
        '        man_path = path / "manifest.json"',
        "test_bundle_manifest_that_is_a_link_out_is_refused_with_the_pathguard_wording",
        "Regex pattern did not match",
    ),
    b4(
        "S-bundle the bundle folder is not checked",
        "src/hadavin_sdk/k1b/bundle.py",
        '        path = pathguard.operator_dir(path, what="bundle folder")',
        "        path = path",
        "test_bundle_folder_under_a_parent_with_a_control_character_is_refused",
        "wrong wording",
    ),
    b4(
        "S-bundle the listed name is not checked",
        "src/hadavin_sdk/k1b/bundle.py",
        '        pathguard.component(p.name, what="bundle folder")',
        "        p.name",
        "test_bundles_folder_entry_with_a_reserved_name_is_refused_as_a_path_refusal",
        "wrong wording",
    ),
    b4(
        "S-score the layout check joins without pathguard",
        "src/hadavin_sdk/k1b/score.py",
        '        rdir = pathguard.join(out, f"run{i}", what="run folder", must_exist=True, kind="dir")\n        files = ',
        '        rdir = out / f"run{i}"\n        files = ',
        "test_score_check_layout_refuses_a_run_folder_that_is_a_link_out",
        "DID NOT RAISE",
    ),
    b4(
        "S-replay the marker folder is not checked",
        "src/hadavin_sdk/k1b/replay.py",
        '        out = pathguard.operator_dir(out_arg, what="replay output folder", must_exist=False)\n    except pathguard.PathRefused:\n        return',
        "        out = Path(out_arg)\n    except pathguard.PathRefused:\n        return",
        "test_replay_mark_failed_writes_nothing_into_a_folder_with_a_control_character",
        "marking raised",
    ),
    b4(
        "S-replay an interrupt while marking is not named",
        "src/hadavin_sdk/k1b/replay.py",
        "            except (KeyboardInterrupt, MemoryError) as stop:",
        "            except KeyboardInterrupt as stop:",
        "test_replay_keeps_the_first_error_and_names_it_when_marking_is_interrupted",
        "carries no note",
    ),
    b4(
        "S-replay a marking failure is not turned into a note",
        "src/hadavin_sdk/k1b/replay.py",
        '                exc.add_note(f"FAILED.txt was not written ({type(second).__name__})")',
        "                pass",
        "test_replay_marking_failure_leaves_the_first_error_with_a_note",
        "carries no note",
    ),
    b4(
        "S-fake the recording name is not joined through pathguard",
        "src/hadavin_sdk/llm/fake.py",
        '        path = pathguard.join(self.recorded_dir, f"{digest}-{attempt}.json", what="recording")',
        '        path = self.recorded_dir / f"{digest}-{attempt}.json"',
        "test_fake_llm_refuses_a_recording_name_that_is_a_link_out",
        "wrong wording",
    ),
    b4(
        "X-atomic the file is made for the group and world too",
        AT,
        "os.open(tmp, flags, 0o600)",
        "os.open(tmp, flags, 0o666)",
        "test_atomic_write_creates_its_file_for_the_owner_only",
        "assert",
    ),
    b4(
        "X-atomic an error of the open keeps the path",
        AT,
        "        raise _without_path(exc) from None\n    try:\n        f = os.fdopen",
        "        raise\n    try:\n        f = os.fdopen",
        "test_atomic_write_errors_carry_no_path",
        "assert",
    ),
    b4(
        "X-atomic an error of the rename keeps the path",
        AT,
        "        tmp.unlink(missing_ok=True)\n        raise _without_path(exc) from None\n    except BaseException:",
        "        tmp.unlink(missing_ok=True)\n        raise\n    except BaseException:",
        "test_atomic_write_rename_error_carries_no_path",
        "assert",
    ),
    b4(
        "R5j the whole-path limit counts characters, not bytes",
        PG,
        'len(text.encode("utf-8", errors="surrogatepass")) > MAX_PATH_BYTES:\n        raise _refuse("R5", what, "too long")\n\n\ndef _within',
        'len(text) > MAX_PATH_BYTES:\n        raise _refuse("R5", what, "too long")\n\n\ndef _within',
        "test_r5_the_whole_path_limit_counts_bytes_not_characters",
        "DID NOT RAISE",
        test_file=B3,
    ),
    b4(
        "H-hashing a read error keeps its chain",
        HF,
        '            raise ConfigError(f"cannot read: {rel}") from None',
        '            raise ConfigError(f"cannot read: {rel}")',
        "test_hash_files_read_error_is_raised_without_a_chain",
        "assert",
    ),
    b4(
        "H-signer the resolved key path is printed",
        "src/hadavin_sdk/audit/signer.py",
        "source, pem = str(settings.private_key_path), path.read_bytes()",
        "source, pem = str(path), path.read_bytes()",
        "test_pin_build_local_signer_error_prints_the_key_path_as_typed",
        "resolved path",
    ),
]

# Mutants that cannot be killed, each with the argument (one line). A test below checks that the text still exists in the
# source, so a row cannot outlive the code it describes. Not run by the runner (it cannot produce a kill).
M += [
    b4(
        "S-atomic the output name is not joined through pathguard",
        AT,
        '    final = pathguard.join(base, name, what="output file")',
        "    final = base / name",
        "test_atomic_write_refuses_a_data_name_with_a_colon_or_a_device_name",
        "wrong wording",
    ),
    b4(
        "S-signer the key file is not checked",
        "src/hadavin_sdk/audit/signer.py",
        '            path = pathguard.operator_file(settings.private_key_path, what="signer key file")',
        "            path = Path(settings.private_key_path)",
        "test_build_local_refuses_a_key_path_with_a_control_character_as_a_path_refusal",
        "wrong wording",
    ),
    b4(
        "S-local_dir the object name is not joined through pathguard",
        "src/hadavin_sdk/audit/local_dir.py",
        '        return pathguard.join(self.objects, key, what="audit object")',
        "        return self.objects / key",
        "test_local_dir_object_names_are_joined_through_pathguard",
        "wrong wording",
    ),
]

EQUIVALENT = [
    (
        "k1b/bundle.py",
        'target = pathguard.join(\n            path, *rel.split("/"), what="bundle file", must_exist=True, kind="file"\n        )\n        if not isinstance(digest, str)',
        "rel was matched against the allowed file layout just above (a fixed set of plain names) and every file in the folder is checked for a link by the rglob scan that runs after the manifest read but before any file part is parsed; the hash read here sees the same file, and a manifest of this shape lists only names that pass the layout.",
    ),
    (
        "k1b/replay.py",
        'rdir = pathguard.join(out, f"run{run_index}", what="run folder")',
        "``out`` was refused unless empty or new and was made by this call just before, and the name is ``run`` plus digits; no link can exist in it, and the write steps join the run folder again strictly (``_run_dir``) before each file.",
    ),
    (
        "k1b/atomic.py",
        'flags |= getattr(os, "O_NOFOLLOW", 0)',
        "O_EXCL already makes os.open fail on any existing name, a link included, so O_NOFOLLOW on a name that was just created adds no refusal.",
    ),
    (
        "k1b/atomic.py",
        'getattr(os, "O_BINARY", 0)',
        "O_BINARY is 0 on every system except Windows, so the flag cannot change a Linux or macOS run; the Windows effect (no newline translation) cannot be run here.",
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
