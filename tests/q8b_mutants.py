"""The mutants of ticket Q8b (two masking leaks: a half-masked value under a credential key, and card text that hid an
e-mail address from the redactor), run by the P1m runner (``tools/mutation_runner.py``).

Same shape as ``tests/stage_mutants.py``: each mutant reverts ONE guard in a temp copy of the package; the test named in
``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment of the assertion MESSAGE). A
mutant whose ``old`` text is not found in the built code is a failure of this gate. Not collected by pytest. Run from
the repo root:

    python tests/q8b_mutants.py            # all mutants; exit 1 if any is not good
    python tests/q8b_mutants.py M3         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
CASE_TESTS = "test_q8b_credential_keys.py"
CARD_TESTS = "test_q8b_card_text.py"
RANDOM_TESTS = "test_q8b_random.py"
RED = "k1b/redaction.py"
CHANNEL = "approvals/channel.py"
GATE = "approvals/gate.py"
REDACT = "guard/redact.py"
RUNMAP = "guard/runmap.py"
REQUESTS = "approvals/requests.py"
GLUED_TESTS = "test_q8b_glued_and_whole_values.py"
SLACK = "approvals/slack_channel.py"
BATCH = "test_q8b_batch2.py"
BATCH3 = "test_q8b_batch3.py"
BATCH4 = "test_q8b_batch4.py"
BATCH6 = "test_q8b_batch6.py"
BATCH7 = "test_q8b_batch7.py"
BATCH8 = "test_q8b_batch8.py"
LINES8 = "test_q8b_batch8_lines.py"
BATCH9 = "test_q8b_batch9.py"
B10 = "test_q8b_batch10.py"
B11 = "test_q8b_batch11.py"
K5R11 = "test_k5_round11.py"
K5PROD = "test_k5_producers.py"
META = "test_mutation_runner_meta.py"
# What the mutation copy holds besides src: a test reads CHANGELOG.md from the repo root (tests/test_q8b_batch3.py checks this list).
EXTRA_DIRS = ("tests", "tools", "demos", "docs")
EXTRA_FILES = ("CHANGELOG.md", ".gitleaks.toml")
CARDS = "approvals/cards.py"
RUNMAP = "guard/runmap.py"


def mutant(name, file, old, new, test_file, killer, expect):
    return Mutant(
        name,
        "src/hadavin_sdk/" + file,
        old,
        new,
        expect,
        test_file="tests/" + test_file,
        only_test=killer.split("[")[0],
        pinned=f"tests/{test_file.removesuffix('.py')}::{killer}",
    )


def test_file_mutant(name, file, old, new, test_file, killer, expect):
    """A mutant of a file under tests/ (a test helper or corpus, not product code): the same pin and rules as `mutant`."""
    return Mutant(
        name, file, old, new, expect,
        test_file="tests/" + test_file,
        only_test=killer.split("[")[0],
        pinned=f"tests/{test_file.removesuffix('.py')}::{killer}",
    )  # fmt: skip


M = [
    mutant("M1 changed counts as masked", RED,
        "        if _ONLY_PLACEHOLDERS.fullmatch(part):\n            return part\n",
        "        if part != text:\n            return part\n",
        CASE_TESTS, "test_s1_a_partly_masked_result_is_refused", "a partly masked value was accepted"),
    mutant("M2 prefix match", RED, "_ONLY_PLACEHOLDERS.fullmatch(part)", "_ONLY_PLACEHOLDERS.match(part)",
        CASE_TESTS, "test_s2_text_after_the_placeholder_is_refused", "text after the placeholder was accepted"),
    mutant("M3 result without key accepted", RED,
        '        if not masked.startswith(k + "="):\n            continue\n        part = masked[len(k) + 1 :]\n',
        '        part = masked[len(k) + 1 :] if masked.startswith(k + "=") else masked\n',
        CASE_TESTS, "test_s3_a_result_without_its_key_is_refused", "a result without its key was accepted"),
    mutant("M4 quote check (ii) removed", RED,
        "        if quote:\n            if len(part) < 2 or part[0] != quote or part[-1] != quote:\n"
        "                continue\n            part = part[1:-1]\n",
        "        if quote and len(part) >= 2 and part[0] == quote and part[-1] == quote:\n"
        "            part = part[1:-1]\n",
        CASE_TESTS, "test_s7_a_quoted_attempt_without_quotes_is_refused", "without its quotes was accepted"),
    mutant("M5 one placeholder only", RED,
        '_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")',
        '_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})")',
        CASE_TESTS, "test_s4_two_placeholders_are_accepted", "two placeholders were refused"),
    mutant("M6 not-plain under the real key", RED,
        "    return [(FALLBACK_KEY, quote)] if quote else []", "    return [(key, quote)] if quote else []",
        CASE_TESTS, "test_s6_what_is_written_to_the_redactor", "written under its real key"),
    mutant('M7 plain is a denylist', RED, '    if all(c in _PLAIN_CHARS for c in text):', '    if not any(c.isspace() or c in ";&,\\"\'" for c in text):',
        BATCH, 'test_a_value_with_a_control_character_is_never_written_unquoted', 'written unquoted'),
    mutant("M8 length cap removed", RED,
        "    if not text or len(text) > MAX_SPELLING_CHARS:", "    if not text or False:",
        CASE_TESTS, "test_s6_what_is_written_to_the_redactor", "an over-long spelling was tried"),
    mutant("M9 Secret flag dropped", RED,
        "        return _walk_dict(obj, f, sens, budget, _is_secret(obj))", "        return _walk_dict(obj, f, sens, budget, False)",
        CASE_TESTS, "test_n2_a_secret_entry_is_masked_where_repeated", "readable in the log line"),
    mutant("M10 first spelling returned in a Secret", RED,
        "        if not in_secret:\n            return result\n", "        return result\n",
        CASE_TESTS, "test_n2_decoded_copy_of_a_base64_entry", "readable in the log line"),
    mutant("M11 spec not looked into", RED,
        '        elif secret and k == "spec" and isinstance(v, dict):\n'
        "            out[_key(k, f)] = _walk_dict(v, f, sens, budget, True)\n",
        "",
        CASE_TESTS, "test_n2_f5c_secret_data_under_spec", "readable in the log line"),
    mutant("M12 8-character rule removed", RED,
        "    if not credential and (\n", "    if False and (\n",
        CASE_TESTS, "test_g7_common_words_of_a_secret_stay_readable", "a common word was replaced"),
    mutant("M12b only the length test of the 8-character rule removed", RED,
        "len(text) < MIN_REGISTER_CHARS or text.isdigit()", "False or text.isdigit()",
        CASE_TESTS, "test_g7_common_words_of_a_secret_stay_readable", "a common word was replaced"),
    mutant("M13 value-shape gate always true", RED,
        "_setting_key(key) and _setting_value(obj):", "_setting_key(key) and True:",
        CASE_TESTS, "test_n1_a_value_under_a_setting_key_is_masked", "a value under a setting key was shown"),
    mutant('M14 glued endings removed', RED, r'''            or _glued_ending(w)
''', r'''''',
        CASE_TESTS, 'test_t1_the_key_rule', 'the key rule changed'),
    mutant("M15 env value only when a string", RED,
        "        if k in value_keys:",
        "        if k in value_keys and isinstance(v, str):",
        CASE_TESTS, "test_n1_a_number_in_a_named_entry", "part of the value is readable"),
    mutant("M16 list items lose the key", RED,
        "        return [_walk(v, f, key, sens, budget) for v in obj]",
        "        return [_walk(v, f, key, secret_data, budget) for v in obj]",
        CASE_TESTS, "test_n1_a_list_under_a_setting_key", "a value under a setting key was shown"),
    mutant("M17 hook brackets again", CHANNEL, 'sanitise_text(_WHITE_SPACE_CONTROLS.sub(" ", text), defang=False)', 'sanitise_text(_WHITE_SPACE_CONTROLS.sub(" ", text), defang=True)',
        CARD_TESTS, "test_n4_an_address_outside_code", "an identifier is readable on the card"),
    mutant("M18 last step removed", CHANNEL,
        "    return defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))",
        "    return runmap.redact_text(text, mapping, neutralise=_neutralise)",
        CARD_TESTS, "test_n6_f6b_a_domain_outside_code_is_bracketed", "a bare domain is outside code"),
    mutant("M19 plain dot rule removed", GATE, '_ANY_NAME_DOT.sub("[.]", part)', "part",
        CARD_TESTS, "test_n6_a_domain_after_a_placeholder", "a bare domain is outside code"),
    mutant("M20 mention step removed", GATE,
        '    return _MENTION.sub(r"at-\\1", line)\n\n\ndef _defang_outside_code', "    return line\n\n\ndef _defang_outside_code",
        CARD_TESTS, "test_n6_f6c_no_mention_is_created", "a mention was created"),
    mutant("M20b mention step only outside inline code", GATE,
        "    line = _outside_code(line, lambda p: _bracket_dots(_fold_dots(p)))\n",
        "    return _outside_code(\n"
        '        line, lambda p: _MENTION.sub(r"at-\\1", _bracket_dots(_fold_dots(p)))\n    )\n',
        CARD_TESTS, "test_n6_f6c_no_mention_is_created", "a mention was created"),
    mutant("M21 brackets inside a closed fence", GATE,
        "line if i in code else _last_step_line(line)", "line if False else _last_step_line(line)",
        CARD_TESTS, "test_g12_code_stays_code", "a fence body was changed"),
    mutant("M11b a Secret's data that is not a map is not masked", RED,
        '        elif secret and k in ("data", "stringData"):\n', '        elif False:\n',
        CASE_TESTS, "test_n1_a_secret_whose_data_is_not_a_map", "part of the value is readable"),
    mutant("M23 Slack path skips the last step", SLACK,
        "        shown = redact_for_people(withheld, _seeded(withheld))",
        '        shown = runmap.redact_text(withheld, seeded, neutralise=clean.__globals__["_neutralise"])',
        CARD_TESTS, "test_n8_only_one_function_feeds_a_card", "a card path skips redact_for_people"),
    mutant("M24 e-mail guard removed", REDACT,
        '{1,254}(?:@|%40)" + _GUARDED_DOMAIN', '{1,254}(?:@|%40)" + _EMAIL_DOMAIN',
        BATCH, "test_a_key_glued_to_an_address_of_any_length_keeps_its_value_masked", "glued to a key is readable"),
    mutant("M26 address read without any key guard", REDACT,
        '    + _NOT_GLUED_KEY\n    + r"[A-Za-z0-9.\\-]){1,255}\\.(?:"\n    + _NOT_GLUED_KEY\n    + r"[A-Za-z]){2,}(?:\\b|(?="\n    + GLUED_KEY\n    + "))"', '    + r"[A-Za-z0-9.\\-]){1,255}\\.(?:"\n    + r"[A-Za-z]){2,}\\b"',
        BATCH, "test_a_key_glued_to_an_address_of_any_length_keeps_its_value_masked", "glued to a key is readable"),
    mutant('M27 Authorization boundary back', REDACT, r'''r"(?i)authorization[\"']?\s*[:=]\s*[\"']?(?:[a-z]+"''', r'''r"(?i)\bauthorization[\"']?\s*[:=]\s*[\"']?(?:[a-z]+"''',
        GLUED_TESTS, 'test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote', 'glued to a credential key is readable'),
    mutant("M28 ARN guard case-sensitive", REDACT, '    r"(?:(?i:(?![\\w.\\-*+@]{0,"', '    r"(?:(?:(?![\\w.\\-*+@]{0,"',
        GLUED_TESTS, "test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote", "glued to a credential key is readable"),
    mutant("M29 ARN guard ignores a quote", REDACT, r'''(?:=|[\"']\s*[:=])))"''', r'''(?:=)))"''',
        GLUED_TESTS, "test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote", "glued to a credential key is readable"),
    mutant("M30 words after a value not masked", REDACT,
        'r"(?:[ \\t]+(?!"', 'r"(?:(?!)[ \\t]+(?!"',
        GLUED_TESTS, "test_r2_a_value_with_spaces_is_masked_whole_on_a_card", "a value with spaces is readable"),
    mutant("M31 words after the value ignore the next key", REDACT, '"|" + _KEY_STOP + ")"', '")"',
        BATCH, "test_a_card_keeps_flags_and_words_after_a_masked_value", "user=bob"),
    mutant("M32 only name is a name", RED, 'k.lower() in ("name", "key")]', 'k.lower() == "name"]',
        GLUED_TESTS, "test_r3_an_entry_with_a_name_and_a_key_is_named_by_either", "shows its value"),
    mutant("M33 kind compared in one case", RED, "kind.casefold() == \"secret\"", "kind == \"Secret\"",
        GLUED_TESTS, "test_r4_kind_secret_in_lower_case_is_a_secret", "a Secret in lower case is shown"),
    mutant("M34 budget not shared by nested texts", RED, "        self.left = MAX_REGISTERED_ENTRIES\n", "        self.left = 10**9\n",
        GLUED_TESTS, "test_r4_the_budget_of_a_secret_counts_nested_texts", "the budget of a Secret was passed"),
    mutant("M35 Turkish and long-s letters not folded", RED, "_FOLD = str.maketrans({", "_FOLD = str.maketrans({}) if True else str.maketrans({",
        GLUED_TESTS, "test_r6_a_key_with_a_letter_the_older_rule_read_as_ascii_is_still_a_key", "letter case folding"),
    mutant("M36 token count words ignored (before)", RED, "and before not in COUNT_WORDS_BEFORE_TOKENS", "",
        GLUED_TESTS, "test_r8_a_count_of_tokens_is_not_a_credential", "token count is masked"),
    mutant("M37 token count words ignored (after)", RED, "and after not in COUNT_WORDS_AFTER_TOKENS", "",
        GLUED_TESTS, "test_r8_a_count_of_tokens_is_not_a_credential", "token count is masked"),
    mutant("M38 label not shown", REQUESTS, "    system = target_label(plan, target_labels)", "    system = plan.target.system",
        GLUED_TESTS, "test_r9_a_host_name_target_is_masked_and_a_label_is_shown", "label is not shown"),
    mutant("M39 label not passed to the card", REQUESTS, "summary(plan, self.detector, self.target_labels)", "summary(plan, self.detector)",
        GLUED_TESTS, "test_r9_the_label_reaches_the_request_card", "label does not reach"),
    mutant("M41 all-digit texts registered", RED, "text.isdigit() or _ONE_LOWER_WORD", "_ONE_LOWER_WORD",
        GLUED_TESTS, "test_r4_a_number_or_one_word_in_a_secret_is_not_registered", "was registered"),
    mutant("M42 one lower-case word registered", RED, " or _ONE_LOWER_WORD.fullmatch(text)", "",
        CASE_TESTS, "test_g7_common_words_of_a_secret_stay_readable", "common word was replaced"),
    mutant("M44 dot after a placeholder not bracketed", GATE, "(?<=[^\\W_]|>)\\.(?=[^\\W\\d_]{2})", "(?<=[^\\W_])\\.(?=[^\\W\\d_]{2})",
        CARD_TESTS, "test_n6_a_domain_after_a_placeholder", "bare domain is outside code"),
    mutant("M45 wide dots not folded", GATE, "    return _WIDE_DOTS.sub(\".\", part)", "    return part",
        CARD_TESTS, "test_n6_f6b_a_domain_outside_code_is_bracketed", "bare domain is outside code"),
    mutant('M46 key rule bounded by a prefix again', REDACT, r'''r"(?i)(?:" + KEY_WORDS + r")" + KEY_TAIL +''', r'''r"(?i)(?<![\w.\-])[\w.\-]{0,40}(?:" + KEY_WORDS + r")" + KEY_TAIL +''',
        BATCH, 'test_a_key_glued_to_a_long_identifier_keeps_its_value_masked', 'behind a'),
    mutant('M47 link not stopped at a key', GATE, '(?:(?!" + GLUED_KEY + r")[^\\s)>\\]\'\\"`])*",', '(?:[^\\s)>\\]\'\\"`])*",',
        BATCH, 'test_a_link_glued_to_a_credential_key_keeps_the_value_masked', 'card:'),
    mutant('M48 address link not stopped at a key', GATE, '(?:(?!" + GLUED_KEY + r")\\S)*")', '(?:\\S)*")',
        BATCH, 'test_an_address_link_glued_to_a_credential_key_keeps_the_value_masked', 'correct'),
    mutant("M49 Bearer does not read a key", REDACT, 'r"(?i)\\bbearer\\s+(" + _KEYED_VALUE + r"|', 'r"(?i)\\bbearer\\s+(',
        BATCH, "test_a_credential_key_after_a_bearer_word_is_masked_whole", "after Bearer is readable"),
    mutant("M50 plan line cleaned with the text", REQUESTS, '    return f"{text} Plan {plan.hash()[:12]}."', '    return f"{text}"',
        BATCH, "test_the_plan_line_survives_a_masked_value_at_the_end_of_the_text", "agent-ops asks"),
    mutant("M51 shadow card shows no label", CARDS, "on {target_label(plan, target_labels)}", "on {plan.target.system}",
        BATCH, "test_the_shadow_card_shows_the_target_label", "does not show the label"),
    mutant("M52 flag value without its words", REDACT, 'rf"(?:=(?![-\\"\'])([^\\s\\"\']{{3,}}{_VALUE_TAIL})|', 'rf"(?:=(?![-\\"\'])([^\\s\\"\']{{3,}})|',
        BATCH, "test_a_flag_with_a_value_that_has_spaces_is_masked_whole", "a word of a flag value"),
    mutant('M22 joined pass starts empty', CHANNEL, '        joined_map = runmap.RunMap({**_seeded(joined), **mapping})', '        joined_map = _seeded(joined)',
        BATCH3, 'test_i4_the_tag_stripped_view_starts_from_the_first_views_masks', 'readable in the returned text'),
    mutant('M53 decoded value keeps the seed mark', RUNMAP, '        original = original.replace("\\0seed", "")\n', '',
        BATCH3, 'test_i4_a_decoded_value_that_holds_a_shown_placeholder_is_one_masked_value', 'stayed readable'),
    mutant('M54 double-quote rule has its own key list', REDACT, r'''+ QUOTED_KEY_WORDS
            + r")"
            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"]''', r'''+ "password|token"
            + r")"
            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"]''',
        BATCH4, 'test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked', 'a bare prefix key stayed readable'),
    mutant('M55 single-quote rule has its own key list', REDACT, r'''+ QUOTED_KEY_WORDS + r")" + KEY_TAIL + r"[\"']?\s*[:=]\s*'([^']''', r'''+ "password|token" + r")" + KEY_TAIL + r"[\"']?\s*[:=]\s*'([^']''',
        BATCH4, 'test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked', 'a bare prefix key stayed readable'),
    mutant('M56 tool phrase not recognised', REDACT, '(_says_no_value(original) or _SAYS_NONE.fullmatch(original))', '(_SAYS_NONE.fullmatch(original))',
        BATCH3, 'test_i1_a_tool_phrase_after_a_key_is_kept_on_every_path', 'a tool phrase was masked'),
    mutant('M57 one known word makes a phrase a tool phrase', REDACT, 'return all(w in _NOT_A_VALUE or w in _PROSE_WORDS for w in words)', 'return any(w in _NOT_A_VALUE or w in _PROSE_WORDS for w in words)',
        BATCH3, 'test_i1_one_unknown_word_makes_the_phrase_a_value', 'stayed readable'),
    mutant('M59 qualifier must be the whole word', RED, 'before.endswith(KEY_QUALIFIERS)', 'before in KEY_QUALIFIERS',
        BATCH3, 'test_i3_every_credential_key_is_masked_on_the_walk_card_and_log_paths', 'left readable in a record'),
    mutant('M61 shown placeholder read as a token', REDACT, 'if _SHOWN_PLACEHOLDER.search(original) and not re.search(', 'if False and not re.search(',
        BATCH3, 'test_i6_a_second_pass_changes_nothing_but_the_escape_of_shown_placeholders', 'changed the output'),
    mutant('M62 single-letter flag does not stop a value', REDACT, '|-[A-Za-z](?![A-Za-z0-9])', '',
        BATCH3, 'test_i7_a_flag_or_a_key_ends_the_value', 'expected'),
    mutant('M63 a time counts as a key', REDACT, '_KEY_STOP = r"[A-Za-z_][\\w.\\-]*[', '_KEY_STOP = r"[\\w.\\-]+[',
        BATCH3, 'test_i7_later_words_of_a_value_are_masked_with_it', 'stayed readable'),
    mutant('M58 bare ending rule dropped', RED, r'''            or (w.endswith(BARE_ENDINGS) and w not in ORDINARY_WORDS)
''', '',
        BATCH4, 'test_j2_a_key_with_any_word_in_front_is_masked_in_a_record_and_as_text', 'is shown as written in a record'),
    mutant('M60 ordinary words ignored', RED, 'or (w.endswith(BARE_ENDINGS) and w not in ORDINARY_WORDS)', 'or (w.endswith(BARE_ENDINGS))',
        BATCH4, 'test_j2_ordinary_words_stay_readable_in_a_record', 'an ordinary word is taken for a credential key'),
    mutant('M64 quoted rules lose the bare prefixes', REDACT, r'''QUOTED_KEY_WORDS = (
    KEY_WORDS
    + "|"
    + _not_after_ordinary_word("pass")
    + "pass|"
    + _not_after_ordinary_word("session")
    + "session|authorization"
)''', 'QUOTED_KEY_WORDS = KEY_WORDS',
        BATCH4, 'test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked', 'a bare prefix key stayed readable'),
    mutant('M65 a new key is dropped from the one list', REDACT, r'''    _guarded_key("pass", "code"), _guarded_key("pass", "key"), ''', r'''    _guarded_key("pass", "key"), ''',
        BATCH4, 'test_j1_the_d1_keys_are_masked_in_every_style_on_every_path', 'stayed readable'),
    mutant('M66 allow-list of words in front is back', RED, 'or (w.endswith(BARE_ENDINGS) and w not in ORDINARY_WORDS)',
        'or (w.endswith(BARE_ENDINGS) and w[:-4] in ("db", "user", "admin", "root", "api", "mysql"))',
        BATCH4, 'test_j2_a_key_with_any_word_in_front_is_masked_in_a_record_and_as_text', 'is shown as written in a record'),
    mutant('M67 the key list is not read by the key rule', REDACT, r'''            + QUOTED_KEY_WORDS
            + r")"
            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''', r'''            + "password|token"
            + r")"
            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''',
        BATCH4, 'test_j1_every_credential_of_the_corpus_is_masked_in_every_style_on_every_path', 'left a value readable'),
    mutant('M68 card second view only for the five assignment kinds', CHANNEL, 'and m.group(1) in runmap.SECRET_KINDS',
        'and m.group(1) in {"SECRET", "APIKEY", "BEARER", "BASIC", "URLCRED"}',
        BATCH4, 'test_j5_a_secret_split_by_a_tag_is_masked_on_a_card', 'a secret split by a tag is readable'),
    mutant('M69 a semicolon always ends an unquoted value', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=[^\s\"';,&])(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M70 a semicolon in front of a key does not end the value', REDACT, r'''|;(?=[^\s\"';,&])(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''|;(?=[^\s\"';,&]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value', "expected 'Password=<SECRET_1>;Server=db1'"),
    mutant('M71 flag prefix joined by hyphens only', REDACT, r'''    + r"|(?:[a-z0-9]+[_\-]){0,"''', r'''    + r"|(?:[a-z0-9]+\-){0,"''',
        BATCH4, 'test_j4_a_flag_with_an_underscore_or_a_hyphen_masks_its_value', 'a flag value is readable'),
    mutant('M72 flag words are a hand list', REDACT, r'''[a for a in KEY_ALTERNATIVES if "(?=" not in a and a not in _EXACT_FLAG_KEYS]
    + list(FLAG_ONLY_WORDS)''', r'''[r"password", r"passwd", r"pwd", r"secret", r"token", r"api[_\-]?key", "pass"]''',
        BATCH4, 'test_j4_every_spelling_of_the_key_list_is_a_flag', 'a flag of the key list is not masked'),
    mutant('M73 cookie rule takes a session cookie key', REDACT, '_COOKIE_ASSIGN_KEY = r"(?i)(?<!session[_\\-])" + _COOKIE_KEY_BODY', '_COOKIE_ASSIGN_KEY = r"(?i)" + _COOKIE_KEY_BODY',
        BATCH4, 'test_j1_a_cookie_key_with_a_session_word_in_front_masks_a_value_with_spaces', 'a word of the cookie value is readable'),
    mutant('M74 link scheme read inside a word', GATE, r'''(?<![\w+.\-])(?:https?|mailto|data|''', r'''\b(?:https?|mailto|data|''',
        BATCH4, 'test_j1_a_credential_key_ending_in_a_link_scheme_word_keeps_its_value_masked_after_a_colon', 'a key ending in a link scheme word'),
    mutant('M75 new walk endings dropped', RED, r'''    "passcode", "passkey", "passvalue", "sessionkey", "sessioncookie", "sessionvalue", "authvalue", "bearervalue",
''', '',
        BATCH4, 'test_j1_the_d1_keys_are_masked_in_every_style_on_every_path', 'stayed readable'),
    mutant('M76 session cookie rule loses the jar pairs', REDACT, '    + "+(?:"\n    + _JAR_PAIR\n    + "|[ \\t]+(?!"', '    + "+(?:"\n    + "|[ \\t]+(?!"',
        BATCH4, 'test_j1_a_session_cookie_keeps_its_whole_jar_masked', 'a pair of the cookie jar is readable'),
    mutant('M77 cookie assignment rule loses the jar pairs', REDACT, r'''([^\s;,\"'\[{][^\s;,\"']*(?:;\s*[^\s;=]+=[^\s;]*|;[^\s;,\"'=]+(?![^\s;,\"']*=))*)"
        ),
    ),
    # `session_cookie=`''', r'''([^\s;,\"'\[{][^\s;,\"']*(?:;[^\s;,\"'=]+(?![^\s;,\"']*=))*)"
        ),
    ),
    # `session_cookie=`''',
        BATCH4, 'test_j1_every_cookie_key_the_older_cookie_rule_masked_is_still_masked_with_its_jar', 'the older cookie rule masks it and this one does not'),
    mutant('M78 a placeholder ends a value even before a value character', REDACT, '    + r")_\\d+>)+(?!"\n    + _VALUE_CHAR\n    + ")|"\n    + _VALUE_CHAR\n    + "+"\n    + _VALUE_TAIL', '    + r")_\\d+>)+(?![^\\s\\"\';,&])|"\n    + _VALUE_CHAR\n    + "+"\n    + _VALUE_TAIL',
        BATCH4, 'test_j1_every_key_the_older_rule_masked_is_still_masked', 'the older rule masks it and this one does not'),
    mutant('M79 a quoted value is masked only up to its first space', REDACT, r'''            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''', r'''            + KEY_TAIL
            + r"[\"']?\s*[:=]\s*\"([^\"\s]+)[^\"]*\""''',
        BATCH4, 'test_j1_every_key_the_older_rule_masked_is_still_masked', 'the older rule masks it and this one does not'),
    mutant('M80 authorization is no bare prefix of the quoted rules', REDACT, r'''    + "session|authorization"
)''', r'''    + "session"
)''',
        BATCH4, 'test_j1_a_quoted_value_after_authorization_is_masked_whole', 'a word of the quoted value is readable'),
    mutant('M81 flags lose the glued ending branch', REDACT, '    + "|".join(BARE_ENDINGS)\n', '    + "zzqx"\n',
        BATCH4, 'test_j4_a_flag_with_a_word_glued_in_front_of_pass_or_auth_masks_its_value', 'a flag value is readable'),
    mutant('M82 oauth is an ordinary word again', REDACT, '"bandpass", "obsession"', '"bandpass", "oauth", "obsession"',
        BATCH4, 'test_j2_oauth_is_a_credential_key_in_a_record_as_it_is_in_text', 'oauth is on the ordinary-word list'),
    mutant('M83 a word with a digit in front ends a value after a semicolon', REDACT, r'''(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''(?![\w.\-]+[\"']?\s*[:=]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M84 a word with a digit in front ends a value after a comma', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=''', r'''|,(?!\s*[\w.\-]+\s*[:=])|;(?=''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M85 a flag name is read through the rest of its word', REDACT, r'''|-(?:password|passwd))(?![\w-])"''', r'''|-(?:password|passwd))[\w-]*"''',
        BATCH4, 'test_j4_names_that_are_no_credential_stay_readable', 'a name that is no credential was masked'),
    mutant('M86 a comma always ends an unquoted value', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=''', r'''|;(?=''',
        BATCH4, 'test_j6_the_comma_pin_matches_the_code', 'a comma ended the value'),
    mutant('M87 a bearer key is not a key', REDACT, '_bare_word("auth"), _bare_word("session"), _bare_word("bearer"),', '_bare_word("auth"), _bare_word("session"),',
        BATCH4, 'test_j6_the_whole_line_after_a_bearer_key_is_masked', 'a word after a bearer key is readable'),
    mutant('M88 a session cookie value stops at an ampersand', REDACT, '_COOKIE_VALUE_CHAR = r"(?:" + _VALUE_CHAR + "|&)"', '_COOKIE_VALUE_CHAR = r"(?:" + _VALUE_CHAR + ")"',
        BATCH6, 'test_k1_a_session_cookie_value_keeps_the_part_after_an_ampersand_masked', 'the part after the ampersand is readable'),
    mutant('M89 the cookie rule stops at a bracket again', REDACT, r"""([^\s;,\"'\[{][^\s;,\"']*(?:;""", r"""([^\s;,\"'\[{]+(?:;""",
        BATCH6, 'test_k1_a_cookie_key_value_with_a_bracket_after_its_first_character_is_masked_whole', 'a bracket ended the cookie value'),
    mutant('M90 the record walk keeps its own ordinary words', RED, r'''    ORDINARY_WORDS,
    is_count_run,
    is_ordinary_pair,
)''', r'''    is_count_run,
    is_ordinary_pair,
)
ORDINARY_WORDS = frozenset(["bypass"])''',
        BATCH6, 'test_d6_the_record_walk_reads_the_one_list_of_ordinary_words_and_endings', 'the record walk keeps its own list of ordinary words'),
    mutant('M91 a glued flag is read through an ordinary word', REDACT, '    + _FLAG_NOT_ORDINARY\n    + "(?:[a-z0-9]{0,40}(?:"', '    + "(?:[a-z0-9]{0,40}(?:"',
        BATCH6, 'test_d6_a_flag_with_an_ordinary_word_stays_readable', 'an ordinary word was masked as a flag'),
    mutant('M92 the bare words are no flag names', REDACT, r'''    "bearer",
    "credentials",
)''', r'''    "credentials",
)''',
        BATCH6, 'test_d6_a_flag_with_a_word_glued_in_front_masks_its_value_like_the_record_key', 'a glued flag value is readable'),
    # ---- batch 7 (round 7): digits behind a credential word, plurals, cookie keys, authorization schemes, ordinary words ----
    mutant('M93 a bare credential word takes no digits behind it', REDACT, r'''return guard + word + r"(?=[0-9]*[\"']?\s*[:=])"''', r'''return guard + word + r"(?=[\"']?\s*[:=])"''',
        BATCH7, 'test_b7_1_a_credential_word_with_digits_behind_it_is_masked_on_every_path_and_form', 'a value behind a credential key with digits is readable'),
    mutant('M94 a flag name takes no digits behind it', REDACT, r'''    + _PLURAL_TOKENS
    + "))[0-9]*"
''', r'''    + _PLURAL_TOKENS
    + "))"
''',
        BATCH7, 'test_b7_1_a_credential_word_with_digits_behind_it_is_masked_on_every_path_and_form', 'a value behind a credential key with digits is readable'),
    mutant('M95 a flag word takes no plural s', REDACT, '    + ")(?:s(?<!tokens))?|[a-z0-9]{0,40}(?:"\n', '    + ")|[a-z0-9]{0,40}(?:"\n',
        BATCH7, 'test_b7_2_a_plural_credential_flag_masks_its_value_on_every_path', 'a plural credential key leaves a value readable'),
    mutant('M96 a plural tokens flag after a non-count word is no flag', REDACT, r'''    + ")|"
    + _PLURAL_TOKENS
    + "))[0-9]*"
''', r'''    + ")))[0-9]*"
''',
        BATCH7, 'test_b7_2_the_plural_rule_follows_the_record_walk_for_tokens_after_a_non_count_word', 'a plural tokens flag after a non-count word is readable'),
    mutant('M97 a count word before tokens is no exception', REDACT, r'''    + _COUNT_BEFORE_TOKENS
    + "tokens|(?!"''', r'''    + "tokens|(?!"''',
        BATCH7, 'test_b7_2_a_count_of_tokens_stays_readable_as_a_flag', 'a count of tokens was masked as a flag'),
    mutant('M98 a plural of the word token is read as a flag word', REDACT, '    + ")(?:s(?<!tokens))?|[a-z0-9]{0,40}(?:"\n', '    + ")(?:s)?|[a-z0-9]{0,40}(?:"\n',
        BATCH7, 'test_b7_2_a_count_of_tokens_stays_readable_as_a_flag', 'a count of tokens was masked as a flag'),
    mutant('M99 cookie is no credential word of the record walk', RED, '        "cookie",\n        "cookies",\n    ]\n)\nGLUED_ENDINGS', '    ]\n)\nGLUED_ENDINGS',
        BATCH7, 'test_b7_3_a_record_key_named_for_a_cookie_is_masked_whatever_its_letter_case', 'a cookie record key is not sensitive'),
    mutant('M100 cookie is no exact flag word', REDACT, r'''FLAG_EXACT_WORDS = (r"(?:set[_\-])?cookie", r"session[_\-]?cookie")''', r'''FLAG_EXACT_WORDS = (r"session[_\-]?cookie",)''',
        BATCH7, 'test_b7_3_a_cookie_key_in_text_is_masked_on_every_path_in_every_letter_case', 'a cookie key in text leaves a value readable'),
    mutant('M101 the cookie flag rule reads one letter case', REDACT, r'''(?:(?i:--(?:"''', r'''(?:(?:--(?:"''',
        BATCH7, 'test_b7_3_a_cookie_key_in_text_is_masked_on_every_path_in_every_letter_case', 'a cookie key in text leaves a value readable'),
    mutant('M102 a word glued behind a semicolon is no part of a cookie value', REDACT, '|;[^\\s;,\\"\'=]+(?![^\\s;,\\"\']*=))*)"', ')*)"',
        BATCH7, 'test_b7_3_a_cookie_value_split_by_a_semicolon_with_no_space_is_one_secret', 'Qw8tail'),
    mutant('M103 a Digest header is no credential', REDACT, r'''|[\"']?digest(?:"''', r'''|[\"']?digest(?!)(?:"''',
        BATCH7, 'test_b7_4_a_digest_header_is_masked_to_the_end_of_the_line', 'a Digest header value is readable'),
    mutant('M104 a scheme word after a credential flag is no part of the value', REDACT, '(?![-\\"\'])({_AUTH_SCHEME_WORD}?[^\\s\\"\']{{3,}}))"', '(?![-\\"\'])([^\\s\\"\']{{3,}}))"',
        BATCH8, 'test_b8_4_the_generic_flag_takes_a_scheme_word_with_its_token', 'the scheme word is not masked with its token'),
    mutant('M105 a bare credential word has no ordinary-word guard', REDACT, '    guard = _not_after_ordinary_word(word) if word in BARE_ENDINGS else ""', '    guard = ""',
        BATCH7, 'test_b7_5_an_ordinary_word_stays_readable_in_every_form_on_every_path', 'an ordinary word was masked'),
    mutant('M106 the quoted rules have no ordinary-word guard on pass', REDACT, '    + _not_after_ordinary_word("pass")\n    + "pass|"', '    + "pass|"',
        BATCH7, 'test_b7_5_every_ordinary_word_of_the_one_list_is_readable_as_key_value_and_quoted', 'an ordinary word was masked as key value'),
    mutant('M107 an ordinary word need not start a word', REDACT, '        r"(?<!(?<![a-z0-9])" + w[: -len(ending)] + ")"', '        r"(?<!" + w[: -len(ending)] + ")"',
        BATCH7, 'test_b7_5_the_ordinary_word_must_start_a_word_to_stay_readable', 'an ordinary word glued behind letters is no ordinary word'),
    mutant('M108 a flag has two prefix words at most', REDACT, r'''FLAG_PREFIX_WORDS = 6''', r'''FLAG_PREFIX_WORDS = 2''',
        BATCH7, 'test_b7_6_a_flag_with_three_prefix_words_masks_its_value', 'a flag with three prefix words is readable'),
    mutant('M109 an ordinary flag word with digits is a credential flag', REDACT, '(?![a-z]|[0-9]+[a-z])', '(?![a-z0-9])',
        BATCH7, 'test_b7_5_an_ordinary_word_stays_readable_in_every_form_on_every_path', 'an ordinary word was masked'),
    mutant('M110 the record walk keeps its own count words', RED, r'''    COUNT_WORDS_BEFORE_TOKENS,
    ORDINARY_WORDS,
    is_count_run,
    is_ordinary_pair,
)''', r'''    ORDINARY_WORDS,
    is_count_run,
    is_ordinary_pair,
)
COUNT_WORDS_BEFORE_TOKENS = frozenset(["max"])''',
        BATCH7, 'test_b7_2_the_record_walk_reads_the_one_list_of_count_words', 'the record walk keeps its own list of count words'),
    # ---- batch 7, Issue 11: the two path-hygiene tests pass on old src because the fix lives in tests/; each gets a mutant that puts the fault back ----
    test_file_mutant('M111 the copy target has a fixed name again', 'tests/demo_askdata/corpus.py', 'f"askdata_p2_copy_{uuid.uuid4().hex}.csv"', '"askdata_p2_copy.csv"',
        BATCH6, 'test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file', 'the copy target has the fixed name again'),
    test_file_mutant('M112 the copy target sits in a fixed shared folder', 'tests/demo_askdata/corpus.py', 'Path(tempfile.gettempdir()) / f"askdata_p2_copy_', 'Path("/' + 'tmp/") / f"askdata_p2_copy_',
        BATCH6, 'test_no_test_names_a_fixed_path_in_the_shared_temporary_folder', 'a fixed shared-temporary path'),
    # ---- batch 7, Issue 11: controls of the batch-7 tests that also pass on 8e8ccbef get a mutant that breaks the thing they guard ----
    mutant('M113 a bare credential word takes letters and digits behind it', REDACT, r'''return guard + word + r"(?=[0-9]*[\"']?\s*[:=])"''', r'''return guard + word + r"(?=[a-z0-9]*[\"']?\s*[:=])"''',
        BATCH7, 'test_b7_1_digits_in_the_middle_or_a_digit_only_neighbour_do_not_make_a_key', 'was masked on the card but not by the record walk'),
    mutant('M114 the ordinary word need not start a word (a real key turns readable)', REDACT, '        r"(?<!(?<![a-z0-9])" + w[: -len(ending)] + ")"', '        r"(?<!" + w[: -len(ending)] + ")"',
        BATCH7, 'test_b7_5_a_real_credential_key_never_turns_readable_because_of_the_ordinary_list', 'a credential key became readable'),
    test_file_mutant('M115 the CHANGELOG says any number of letters glued in front', 'CHANGELOG.md', 'up to 40 letters or digits glued in front', 'any letters or digits glued in front',
        BATCH7, 'test_b7_6_the_changelog_says_how_many_letters_may_be_glued_in_front', 'up to 40 letters or digits glued in front'),
    # ---- batch 8 (round 8): one mutant per new branch and fix ----
    mutant('M116 a plural tokens glued to a word is no flag', REDACT, r'''    + "tokens|(?!"
    + _COUNT_RUN
    + "tokens)[a-z0-9]{1,40}tokens)"''', r'''    + "tokens)"''',
        BATCH8, 'test_b8_1_a_plural_tokens_flag_after_a_glued_or_camel_case_word_is_masked_on_every_path', 'a plural tokens flag after a glued or camelCase word is readable'),
    mutant('M117 a glued count of tokens is a credential flag', REDACT, r'''    + "tokens|(?!"
    + _COUNT_RUN
    + "tokens)[a-z0-9]{1,40}tokens)"''', r'''    + "tokens|[a-z0-9]{1,40}tokens)"''',
        BATCH8, 'test_b8_1_a_count_of_tokens_stays_readable_as_a_flag_and_as_a_record_key', 'a count of tokens was masked as a flag'),
    mutant('M118 the record walk reads a glued plural tokens as a count', RED, r'''            and not is_count_run(w[: -len("tokens")])''', r'''            and False''',
        BATCH8, 'test_b8_1_a_plural_tokens_flag_after_a_glued_or_camel_case_word_is_masked_on_every_path', 'the record walk does not mask'),
    mutant('M119 a cookie flag may have prefix words and a plural', REDACT, r'''FLAG_EXACT_WORDS = (r"(?:set[_\-])?cookie", r"session[_\-]?cookie")''', r'''FLAG_EXACT_WORDS = (r"(?:[a-z0-9]+[_\-])*cookies?", r"session[_\-]?cookie")''',
        BATCH8, 'test_b8_2_a_switch_or_a_file_flag_of_the_cookie_family_leaves_the_next_word_readable', 'a cookie switch or file flag masked the next word'),
    mutant('M120 a bare credential word has no ordinary-word look-behind (card)', REDACT, r'''    guard = _not_after_ordinary_word(word) if word in BARE_ENDINGS else ""''', r'''    guard = ""''',
        B10, 'test_b10_6_an_ordinary_word_alone_or_with_a_second_word_of_no_family_stays_readable[bandpass]', 'an ordinary name was masked'),
    mutant('M121 the record walk skips a glued ending behind an ordinary word', RED, r'''    return w.endswith(GLUED_ENDINGS)''', r'''    return w.endswith(GLUED_ENDINGS) and not any(w.startswith(o) for o in ORDINARY_WORDS)''',
        B10, 'test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form[bandpass]', 'the record walk shows the key'),
    mutant('M122 the scheme word and its token after --authorization are no rule', REDACT, r'''(?![-\"'])([A-Za-z]+{_SP}+(?:{_QUOTED_TEXT}''', r'''(?![-\"'])(?!)([A-Za-z]+{_SP}+(?:{_QUOTED_TEXT}''',
        BATCH8, 'test_b8_4_any_scheme_word_and_its_token_are_masked_after_the_authorization_and_bearer_flags', 'a token after a scheme word is readable'),
    mutant('M123 a Digest value after --authorization is no rule', REDACT, r'''rf"{_SP}+(?:(digest{_SP}+{_DIGEST_WORD}''', r'''rf"{_SP}+(?!)(?:(digest{_SP}+{_DIGEST_WORD}''',
        BATCH8, 'test_b8_4_a_digest_value_after_the_flag_is_masked_up_to_the_next_flag_or_the_end_of_the_line', 'a Digest value after the flag is readable'),
    mutant('M124 a flag has three prefix words at most', REDACT, r'''FLAG_PREFIX_WORDS = 6''', r'''FLAG_PREFIX_WORDS = 3''',
        BATCH8, 'test_b8_5_a_flag_with_up_to_six_words_in_front_masks_its_value_and_a_seventh_word_is_the_stated_limit', 'a flag with up to six words in front is readable'),
    mutant('M125 the words in front of a flag have no bound', REDACT, r'''    + r"|(?:[a-z0-9]+[_\-]){0,"
    + str(FLAG_PREFIX_WORDS)
    + "}"''', r'''    + r"|(?:[a-z0-9]+[_\-])*"''',
        BATCH8, 'test_b8_5_a_flag_with_up_to_six_words_in_front_masks_its_value_and_a_seventh_word_is_the_stated_limit', 'the flag rule reads more than six words in front'),
    mutant('M126 a quoted Digest header runs to the end of the line', REDACT, r'''(?:\"digest"''', r'''(?:\"digest(?!)"''',
        BATCH8, 'test_b8_7_a_quoted_digest_header_is_masked_to_its_closing_quote_and_the_json_stays_whole', 'the JSON structure after a quoted Digest value was masked'),
    mutant('M127 a bare credential word takes at most nine digits (text)', REDACT, r'''return guard + word + r"(?=[0-9]*[\"']?\s*[:=])"''', r'''return guard + word + r"(?=[0-9]{0,9}[\"']?\s*[:=])"''',
        BATCH8, 'test_b8_8_nine_ten_and_forty_digits_behind_a_bare_credential_word_are_masked_like_the_record_key', 'a bare word with many digits leaves a value readable'),
    mutant('M128 a flag word takes at most nine digits', REDACT, r'''    + _PLURAL_TOKENS
    + "))[0-9]*"
''', r'''    + _PLURAL_TOKENS
    + "))[0-9]{0,9}"
''',
        BATCH8, 'test_b8_8_nine_ten_and_forty_digits_behind_a_bare_credential_word_are_masked_like_the_record_key', 'a bare word with many digits leaves a value readable'),
    mutant('M129 a line break does not end a Digest header value', REDACT, r'''+ r"[ \t]++)([^\r\n]{8,}+"''', r'''+ r"[ \t]*+)([^\r\n]{8,}+"''',
        BATCH8, 'test_b8_10_a_line_break_ends_a_digest_header_and_a_scheme_word', 'a line break after Digest does not end the header value'),
        mutant('M130 a line break is no gap for the Basic rule', REDACT, r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{8,}={0,2})"''', r'''r"(?i)\bbasic[ \t]+([a-z0-9+/<>_]{8,}={0,2})"''',
        B10, 'test_b10_1_the_basic_rule_alone_masks_a_bare_wrapped_value_of_8_to_15_characters', 'a short wrapped Basic value is readable'),
    mutant('M131 a cookie word key in text has no more words', REDACT, r'''r"(?<![A-Za-z])(?:set-)?cookies?[0-9]*+(?:(?:[_.\-]|(?-i:(?=[A-Z])))[A-Za-z0-9]+(?:[_.\-][A-Za-z0-9]+){0,5})?"''', r'''r"(?<![A-Za-z])(?:set-)?cookies?[0-9]*+"''',
        BATCH8, 'test_b8_12_a_key_with_the_word_cookie_and_more_words_is_masked_in_text_as_the_record_walk_masks_it', 'a cookie word key leaves a value readable in text'),
    mutant('M132 the ordinary look-behind of a bare word need not start a word (a real key turns readable)', REDACT, r'''r"(?<!(?<![a-z0-9])" + w[: -len(ending)] + ")"''', r'''r"(?<!" + w[: -len(ending)] + ")"''',
        B10, 'test_b10_6_an_ordinary_word_must_start_a_word_to_stay_readable_so_xcompass_key_is_a_key_as_before', 'an ordinary word that does not start a word'),
    mutant('M158 the curl cookie flag does not take the session spelling', REDACT, r'''FLAG_EXACT_WORDS = (r"(?:set[_\-])?cookie", r"session[_\-]?cookie")''', r'''FLAG_EXACT_WORDS = (r"(?:set[_\-])?cookie",)''',
        BATCH8, 'test_b8_2_the_cookie_flag_with_its_exact_name_still_masks_its_value', 'an exact cookie flag leaves its value readable'),
    # M145, M150 and M151 were never assigned in batch 8 (no mutant has those numbers; the controls file reads the table, not the numbers).
    # ---- batch 8, Issue 13: one planted fault for each K5 round 11 / producers / runner control that passed on old code ----
    mutant('M133 a card text is redacted with no neutralising hook', CHANNEL, r'''runmap.redact_text(text, mapping, neutralise=_neutralise)''', r'''runmap.redact_text(text, mapping)''',
        K5R11, 'test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook', 'a card text is redacted with no neutralise hook'),
    mutant('M134 a card sanitiser is called outside the card files', "guard/judge.py", r'''        text = runmap.redact_text(text, {})
        reply = self.llm.chat(''', r'''        text = sanitise_text(runmap.redact_text(text, {}))
        reply = self.llm.chat(''',
        K5R11, 'test_only_clean_and_the_slack_block_call_the_card_sanitisers', 'guard/judge.py:'),
    mutant('M135 an aliased import of the bare redactor', CHANNEL, r'''def _neutralise(text: str) -> str:
    return withhold_commands''', r'''from ..guard.redact import redact as _bare


def _neutralise(text: str) -> str:
    return withhold_commands''',
        K5R11, 'test_the_bare_redactor_ban_also_catches_an_aliased_import', 'approvals/channel.py:'),
    test_file_mutant('M136 the hook check no longer sees a hook that is None', 'tests/test_k5_round11.py', r'''        return isinstance(n.args[2], ast.Constant) and n.args[2].value is None''', r'''        return False''',
        K5R11, 'test_the_hook_check_itself_catches_a_missing_none_and_an_alias', 'the hook check does not see a hook that is None (positional)'),
    mutant('M137 a module that calls a model is not registered', CHANNEL, r'''def _neutralise(text: str) -> str:
    return withhold_commands''', r'''def _neutralise(text: str) -> str:
    _planted_llm.chat(text)
    return withhold_commands''',
        K5PROD, 'test_every_module_that_calls_a_model_is_registered', 'unregistered model caller'),
    mutant('M138 a message is cut before it is redacted', CHANNEL, r'''def _neutralise(text: str) -> str:
    return withhold_commands''', r'''def _neutralise(text: str) -> str:
    _cut = str(text)[:5]
    return withhold_commands''',
        K5PROD, 'test_no_message_is_cut_with_a_slice_before_it_is_redacted', 'a message is cut with a slice before it is redacted'),
    mutant('M139 a producer cuts a head slice before it redacts', CHANNEL, r'''    text = text.replace("\x00", "")
    mapping = _seeded(text)''', r'''    text = text.replace("\x00", "")
    _head = text[:5]
    mapping = _seeded(text)''',
        K5PROD, 'test_in_producer_functions_a_head_slice_only_follows_a_redaction', 'approval card text'),
    test_file_mutant('M140 the gitleaks header chain allows a fourth header', '.gitleaks.toml', r'''-----BEGIN [A-Z ]*PRIVATE KEY-----",\s*"){0,2}-----BEGIN''', r'''-----BEGIN [A-Z ]*PRIVATE KEY-----",\s*"){0,3}-----BEGIN''',
        K5R11, 'test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer', 're.Match object'),
    mutant('M141 the stored call record keeps the raw argument', "runtime/agent_loop.py", r'''inputs=runmap.redact_value(call.input, rmap),''', r'''inputs=call.input,''',
        K5R11, 'test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[assignment]', 'hunter2'),
    test_file_mutant('M142 the runner script exits 1 when no mutant is selected', 'tests/mutation_runner_mutants.py', r'''        sys.exit(2)''', r'''        sys.exit(1)''',
        META, 'test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant', 'the mutants script exits 1 (not 2)'),
    mutant('M143 planted fault for a control: clean: line 44 returns the tag-stripped text unmasked (approvals/channel.py)', CHANNEL, r'''            return alt''', r'''            return joined''',
        K5R11, 'test_a_plain_secret_and_a_markup_split_one_are_both_masked', "AssertionError: api_key=AAAA"),
    mutant('M144 planted fault for a control: clean: returns the original text with its tags, unmasked (approvals/channel.py)', CHANNEL, r'''            return alt''', r'''            return text''',
        K5R11, 'test_a_second_markup_split_secret_of_the_same_kind_is_masked', "AssertionError: api_key=AAAA"),

    mutant('M146 planted fault for a control: _keep_earlier_masks: the swap puts the decoded value back (guard/runmap.py)', RUNMAP, r'''            view = view.replace(decoded, ph)''', r'''            view = view.replace(decoded, decoded)''',
        K5R11, 'test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole', "AssertionError: assert 'x=1' not in 'password"),
    mutant('M147 planted fault for a control: if at line 43 negated (approvals/channel.py)', CHANNEL, r'''        if _secret_originals(joined_map) - _secret_originals(mapping):''', r'''        if not (_secret_originals(joined_map) - _secret_originals(mapping)):''',
        K5R11, 'test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header', "AssertionError: assert ' for user x and more'"),
    mutant('M148 planted fault for a control: __init__: line 391 deleted (guard/runmap.py)', RUNMAP, r'''        super().__init__(*args, **kwargs)''', r'''        pass''',
        K5R11, 'test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number', 'AssertionError: assert (2 == 1)'),
    mutant('M149 planted fault for a control: safe_head: line 543 returns None (guard/runmap.py)', RUNMAP, r'''        return redact_bounded(text, {} if mapping is None else mapping)[0][:limit]''', r'''        return None''',
        K5PROD, 'test_every_redaction_function_reaches_the_one_choke_point[safe_head]', 'AssertionError: safe_head does not reach reda'),


    mutant('M152 planted fault for a control: _clean_line: line 298 deleted (approvals/gate.py)', GATE, r'''        line = _MDLINK.sub(r"\1 [link removed]", line)''', r'''        pass''',
        K5R11, 'test_markdown_cannot_be_formed_around_a_placeholder', 'AssertionError: see [a](<IPV4_1>) and <IPV4_2'),
    mutant('M153 planted fault for a control: _decoded_masks: line 454 deleted (guard/runmap.py)', RUNMAP, r'''            out.append((ph, decoded))''', r'''            pass''',
        K5R11, 'test_more_pairable_values_than_the_bound_are_refused_not_skipped', 'Failed: DID NOT RAISE InputTooLarge'),
    mutant('M154 planted fault for a control: _keep_earlier_masks: line 463 deleted (guard/runmap.py)', RUNMAP, r'''            view = view.replace(decoded, ph)''', r'''            pass''',
        K5R11, 'test_pass_one_masks_survive_the_swap_for_every_value_terminator[%26]', "AssertionError: ('%26', 'password=<SECRET_3>&"),
    mutant('M155 planted fault for a control: hex_unescape: line 131 deleted (guard/runmap.py)', RUNMAP, r'''        text = _PCT_U.sub(lambda m: chr(int(m.group(1), 16)), text)''', r'''        pass''',
        K5R11, 'test_percent_u_and_brace_unicode_escapes_are_decoded', "AssertionError: assert '%u0041' == 'A'"),
    mutant('M156 planted fault for a control: redact_text: line 493 deleted (guard/runmap.py)', RUNMAP, r'''            text = fits_after_nfkc(neutralise(text))''', r'''            pass''',
        K5R11, 'test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return', 'AssertionError: assert 1 >= 2'),
    mutant('M157 planted fault for a control: redact_text: line 528 deleted (guard/runmap.py)', RUNMAP, r'''    mapping.update(current)''', r'''    pass''',
        K5R11, 'test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks', 'AssertionError: head'),
    # ---- batch 9: one planted fault for each new branch (rounds 9, Issues 1, 4, 5, 6) ----
    mutant('M160 a line break is no gap after a scheme word', REDACT, r'''_SCHEME_GAP = r"\s++"''', r'''_SCHEME_GAP = r"[^\S\r\n]++"''',
        B10, 'test_b10_1_a_wrapped_authorization_token_of_8_or_more_characters_is_masked_after_any_line_break[Basic]', 'leaves a token of 8 or more characters readable'),
    mutant('M161 the Basic rule needs a token of 16 characters, not 8', REDACT, r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{8,}={0,2})"''', r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{16,}={0,2})"''',
        B10, 'test_b10_1_the_basic_rule_alone_masks_a_bare_wrapped_value_of_8_to_15_characters', 'a short wrapped Basic value is readable'),
    mutant('M162 the generic Authorization rule needs a token of 16 characters, not 8', REDACT, r'''            + r"|[^\s\"']{8,})"''', r'''            + r"|[^\s\"']{16,})"''',
        B10, 'test_b10_1_a_wrapped_authorization_token_of_8_or_more_characters_is_masked_after_any_line_break[Basic]', 'leaves a token of 8 or more characters readable'),
    mutant('M163 a Digest header does not go on over folded lines', REDACT, r'''            + _DIGEST_FOLDS
            + "))"''', r'''            + "))"''',
        B10, 'test_b10_2_a_digest_header_folded_over_three_lines_is_masked_whole[\\n]', 'a folded Digest header leaves a hash readable'),
    mutant('M164 a Digest header goes on over a line that does not start with a space or a tab', REDACT, r'''_DIGEST_FOLDS = r"(?:" + _LINE_BREAK + r"[ \t]++[^\r\n]*+)*+"''', r'''_DIGEST_FOLDS = r"(?:" + _LINE_BREAK + r"[ \t]*+[^\r\n]*+)*+"''',
        B10, 'test_b10_2_a_digest_header_ends_at_the_first_line_that_does_not_start_with_a_space_or_a_tab', 'a Digest header goes on over a line that does not start'),
    mutant('M165 the Basic rule has no wrapped gap (the batch 8 text)', REDACT, r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{8,}={0,2})"''', r'''r"(?i)\bbasic[ \t]+([a-z0-9+/<>_]{8,}={0,2})"''',
        BATCH9, 'test_b9_1_the_basic_rule_alone_masks_a_bare_wrapped_value_as_main_did', 'curl -H Basic'),
    mutant('M166 the generic Authorization rule has the batch 8 gap', REDACT, r'''[\"']?(?:[a-z]+"
            + _SCHEME_GAP''', r'''[\"']?(?:[a-z]+"
            + r"[ \t]+"''',
        BATCH9, 'test_b9_1_every_shape_that_main_masked_is_masked_now_a_differential_against_the_main_rules', 'main masked'),
    mutant('M167 the record walk does not read an ordinary word and its second word as a credential', RED, r'''            or is_ordinary_pair(before, w)''', r'''            or False''',
        B10, 'test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form[bandpass]', 'the record walk shows the key'),
        mutant('M168 a flag with an ordinary word and a second word of its family is no flag', REDACT, r'''        w
        + r"(?![a-z]|[0-9]+[a-z])(?![_\-](?:"
        + "|".join(ordinary_second_words(w))
        + r")(?![a-z0-9]))"''', r'''        w + r"(?![a-z]|[0-9]+[a-z])"''',
        B10, 'test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form[bandpass]', 'an ordinary word and a second word of its family is readable'),
    mutant('M169 a protection-bypass key is no text rule', REDACT, r'''    r"protection[_\-]?bypass",
''', r'''''',
        BATCH9, 'test_b9_6_a_bypass_name_that_holds_a_secret_is_masked_in_every_form_on_every_path[x-vercel-protection-bypass]', 'protection-bypass'),
    mutant('M170 the record walk does not read protection and bypass as one name', RED, r'''        ("protection", "bypass"),
    }''', r'''    }''',
        BATCH9, 'test_b9_6_a_bypass_name_that_holds_a_secret_is_masked_in_every_form_on_every_path[x-vercel-protection-bypass]', 'protection-bypass'),
    mutant('M171 the glued ending of a bypass name is skipped as an ordinary word', RED, r'''    return w.endswith(GLUED_ENDINGS)''', r'''    return w.endswith(GLUED_ENDINGS) and not w.startswith("bypass")''',
        BATCH9, 'test_b9_6_the_second_words_of_a_bypass_name_are_the_pass_pairs_read_from_one_list', 'a bypass name with the second word'),
    mutant('M172 a key tail reads at most 20 digits', REDACT, r'''KEY_TAIL = r"[0-9]*+[\w.\-]{0,20}"''', r'''KEY_TAIL = r"[0-9]{0,20}+[\w.\-]{0,20}"''',
        BATCH9, 'test_b9_4_any_run_of_digits_after_a_key_word_still_masks_the_value_as_text_and_as_a_record_key[200-pass]', 'a value is readable'),
    mutant('M173 a cookie word takes no digits', REDACT, r'''cookies?[0-9]*+(?:(?:[_.\-]''', r'''cookies?(?:(?:[_.\-]''',
        BATCH9, 'test_b9_4_a_cookie_word_with_digits_is_a_key_as_text_and_as_a_record_key[cookie2]', 'cookie2'),
    mutant('M174 the authorization flag has its own bound of three words', REDACT, r'''    r"(?i)(?<![\w-])--(?:[a-z0-9]+[_\-]){0,"
    + str(FLAG_PREFIX_WORDS)
    + r"}(?:authorization|bearer)''', r'''    r"(?i)(?<![\w-])--(?:[a-z0-9]+[_\-]){0,"
    + "3"
    + r"}(?:authorization|bearer)''',
        BATCH9, 'test_b9_5_the_authorization_flag_reads_the_same_bound_as_the_other_flags', 'the authorization flag has its own bound of prefix words'),
    mutant('M175 the curl cookie rule keeps its own flag names', REDACT, r'''            + "|".join(FLAG_EXACT_WORDS)
            + r"))|-b)''', r'''            + "cookie"
            + r"))|-b)''',
        BATCH9, 'test_b9_5_the_cookie_flag_names_of_curl_and_of_the_generic_flag_rule_are_one_table', 'a cookie flag name of the table leaves its value readable'),
    mutant('M176 a white-space control on a card is not turned into a space', CHANNEL, r'''sanitise_text(_WHITE_SPACE_CONTROLS.sub(" ", text), defang=False)''', r'''sanitise_text(text, defang=False)''',
        BATCH9, 'test_b9_1_a_white_space_control_inside_an_encoded_header_does_not_join_the_scheme_word_to_its_token[%0b]', 'a control inside an encoded header leaves the token readable'),
    mutant('M177 every credential flag takes a scheme word and its token', REDACT, r'''            _AUTH_FLAG
            + rf"{_SP}+(?![-\"'])([A-Za-z]+{_SP}+(?:{_QUOTED_TEXT}''', r'''            _CRED_FLAG
            + rf"{_SP}+(?![-\"'])([A-Za-z]+{_SP}+(?:{_QUOTED_TEXT}''',
        BATCH9, 'test_b9_5_a_flag_other_than_the_authorization_flags_keeps_the_one_word_rule[password]', 'a flag other than the authorization flags takes a scheme word'),
    mutant('M178 a cookie key needs no boundary in front of the word', REDACT, r'''r"(?<![A-Za-z])(?:set-)?cookies?[0-9]*+(?:(?:[_.\-]''', r'''r"(?:set-)?cookies?[0-9]*+(?:(?:[_.\-]''',
        BATCH8, 'test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk', 'mycookie was masked as text'),
    # ---- batch 10: one planted fault for each new branch (round 10, Issues 1, 2, 6) ----
    mutant('M179 the second words of an ordinary word are those of the pass pairs only', REDACT, r'''if word.endswith(bare))''', r'''if bare == "pass")''',
        B10, 'test_b10_6_every_ordinary_word_has_the_second_words_of_its_family_from_the_one_table', 'are not those of its bare word'),
    mutant('M180 the record walk does not read a key in capitals with cookie and more letters', RED, r'''    if _CAPITALS_COOKIE.search(key):
        return True
''', r'''''',
        B10, 'test_b10_6_the_text_rule_and_the_record_walk_agree_for_a_cookie_word_and_one_more_word', 'the text rule and the record walk disagree'),
    mutant('M181 a guarded pair needs its separator in the card rule', REDACT, r'''    return bare + r"[_\-]?" + second''', r'''    return bare + r"[_\-]" + second''',
        B10, 'test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form[bandpass]', 'an ordinary word and a second word of its family is readable'),
    mutant('M182 an ordinary word and a second word of its family is read as a pair only for pass words', REDACT, r'''    return second in ordinary_second_words(first)''', r'''    return second in ordinary_second_words(first) and first.endswith("pass")''',
        B10, 'test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form[obsession]', 'the record walk shows the key'),
    # ---- batch 10: the stated-cost pins and the controls of batch 9 get a killing mutant (round 10, Issue 4) ----
    mutant('M183 the Basic rule takes a token of 4 characters, not 8 (a short first word after a scheme word is masked)', REDACT, r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{8,}={0,2})"''', r'''r"(?i)\bbasic" + _SCHEME_GAP + r"([a-z0-9+/<>_]{4,}={0,2})"''',
        BATCH9, 'test_b9_1_a_prose_line_after_a_scheme_word_stays_readable_when_its_first_word_is_short', 'a line after the scheme word was masked'),
    mutant('M184 the generic Authorization value takes the rest of the line (the second word is masked)', REDACT, r'''            + r"|[^\s\"']{8,})"''', r'''            + r"|[^\"']{8,})"''',
        BATCH9, 'test_b9_2_authorization_with_an_equals_sign_masks_the_first_word_and_shows_the_second', 'the second word after authorization= is not shown'),
    mutant('M186 a cookie key needs no boundary in front of the word (the fault of M178, killed by the digits pin)', REDACT, r'''r"(?<![A-Za-z])(?:set-)?cookies?[0-9]*+(?:(?:[_.\-]''', r'''r"(?:set-)?cookies?[0-9]*+(?:(?:[_.\-]''',
        BATCH9, 'test_b9_4_a_word_that_only_holds_cookie_and_digits_inside_is_no_key', 'was masked as text'),
    mutant('M187 the record walk does not read a key in capitals with cookie and more letters (the fault of M180, killed by the pinned cost)', RED, r'''    if _CAPITALS_COOKIE.search(key):
        return True
''', r'''''',
        BATCH9, 'test_b9_8_a_cookie_jar_name_in_capitals_is_masked_and_in_lower_case_it_is_not', 'the record walk shows COOKIEJAR'),
    # ---- batch 11: the continuation lines of a folded header (round 11, Issue 8) ----
    mutant('M188 the run of folded lines stops after three lines', REDACT, r'''_FOLD_LINES = r"(?:" + _LINE_BREAK + r"[ \t]++[^\r\n]*+)++"''', r'''_FOLD_LINES = r"(?:" + _LINE_BREAK + r"[ \t]++[^\r\n]*+){1,3}+"''',
        B11, 'test_b11_8_the_fold_run_has_no_upper_bound_so_an_indented_block_after_the_header_is_masked_the_stated_cost', 'the fold run has an upper bound'),
    mutant('M189 the folded-header rule does not read Bearer', REDACT, r'''_AUTH_SCHEME_NAMES = "|".join(AUTH_SCHEMES)''', r'''_AUTH_SCHEME_NAMES = "|".join(a for a in AUTH_SCHEMES if a != "Bearer")''',
        B11, 'test_b11_8_the_folded_lines_of_a_header_are_masked_for_every_scheme_and_header_name[Bearer]', 'a folded Bearer header leaves its next lines readable'),
    mutant('M190 the folded-header rule reads the Authorization name only, no credential key', REDACT, r'''r"(?i)(?:authorization|(?:"''', r'''r"(?i)(?:authorization|(?:(?!)"''',
        B11, 'test_b11_8_the_folded_lines_of_a_header_are_masked_for_every_scheme_and_header_name[Token]', 'a folded Token header leaves its next lines readable'),
    mutant('M191 the first line of a folded header is read to its end (quadratic on a line of repeated headers)', REDACT, r'''            + r"++\S*+"''', r'''            + r"++[^\r\n]*+"''',
        B11, 'test_b11_8_a_line_of_repeated_headers_is_read_in_linear_time', 'a line of repeated headers is not read in linear time'),
    mutant('M192 a scheme word and a line break is no gap for a credential key', REDACT, r'''r")\s++([^\s\"']{8,}+(?:"''', r'''r")[ \t]++([^\s\"']{8,}+(?:"''',
        B11, 'test_b11_8_a_credential_key_a_scheme_word_a_break_with_no_indent_and_the_token[Bearer]', 'a token after Bearer and a line break is readable'),
    mutant('M193 the token behind a scheme word and a line break needs one character, not 8', REDACT, r'''r")\s++([^\s\"']{8,}+(?:"''', r'''r")\s++([^\s\"']{1,}+(?:"''',
        B11, 'test_b11_8_after_a_scheme_word_and_a_break_a_first_word_of_fewer_than_8_characters_is_shown_the_stated_cost[Bearer]', 'the first word of fewer than 8 characters was masked'),
    mutant('M194 a scheme word at the end of its line and an unindented token line are not read before the folds', REDACT, r'''r"(?![ \t])\S++"''', r'''r"(?![\s\S])\S++"''',
        B11, 'test_b11_8_fuzz_a_credential_wrapped_over_folds_is_never_left_readable', 'a folded credential is readable'),
    mutant('M195 the folded-header rule does not read Digest (a short first line)', REDACT, r'''_AUTH_SCHEME_NAMES = "|".join(AUTH_SCHEMES)''', r'''_AUTH_SCHEME_NAMES = "|".join(a for a in AUTH_SCHEMES if a != "Digest")''',
        B11, 'test_b11_8_the_digest_header_folded_after_a_first_line_of_fewer_than_8_characters', 'a folded Digest response is readable'),
    mutant('M196 the token behind a scheme word ends at a colon', REDACT, r'''r")\s++([^\s\"']{8,}+(?:"''', r'''r")\s++([\w.\-]{8,}+(?:"''',
        B11, 'test_b11_8_a_token_with_a_colon_after_a_scheme_word_on_the_same_line_is_masked[ApiKey]', 'a token with a colon is readable'),
    mutant('M197 a folded line needs no indent (the next header line is masked too)', REDACT, r'''_FOLD_LINES = r"(?:" + _LINE_BREAK + r"[ \t]++[^\r\n]*+)++"''', r'''_FOLD_LINES = r"(?:" + _LINE_BREAK + r"[ \t]*+[^\r\n]*+)++"''',
        B11, 'test_b11_8_a_line_that_does_not_start_with_a_space_or_a_tab_ends_the_header[Bearer]', 'a line with no indent after the folds was masked'),
]  # fmt: skip


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
        [
            "tests/" + CASE_TESTS,
            "tests/" + CARD_TESTS,
            "tests/" + RANDOM_TESTS,
            "tests/" + GLUED_TESTS,
            "tests/" + BATCH,
            "tests/" + BATCH3,
            "tests/" + BATCH4,
            "tests/" + BATCH6,
            "tests/" + BATCH7,
            "tests/" + BATCH8,
            "tests/" + BATCH9,
            "tests/" + B10,
            "tests/" + B11,
            "tests/" + LINES8,
            "tests/" + K5R11,
            "tests/" + K5PROD,
            "tests/" + META,
        ],
        extra_dirs=EXTRA_DIRS,
        extra_files=EXTRA_FILES,
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
