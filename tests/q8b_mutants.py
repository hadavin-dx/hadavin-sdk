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
REQUESTS = "approvals/requests.py"
GLUED_TESTS = "test_q8b_glued_and_whole_values.py"
SLACK = "approvals/slack_channel.py"
BATCH = "test_q8b_batch2.py"
BATCH3 = "test_q8b_batch3.py"
BATCH4 = "test_q8b_batch4.py"
# What the mutation copy holds besides src: a test reads CHANGELOG.md from the repo root (tests/test_q8b_batch3.py checks this list).
EXTRA_DIRS = ("tests", "tools", "demos", "docs")
EXTRA_FILES = ("CHANGELOG.md",)
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
        only_test=killer,
        pinned=f"tests/{test_file.removesuffix('.py')}::{killer}",
    )


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
    mutant("M14 glued endings removed", RED, " or w.endswith(GLUED_ENDINGS)", "",
        CASE_TESTS, "test_t1_the_key_rule", "the key rule changed"),
    mutant("M15 env value only when a string", RED,
        "        if k in value_keys:",
        "        if k in value_keys and isinstance(v, str):",
        CASE_TESTS, "test_n1_a_number_in_a_named_entry", "part of the value is readable"),
    mutant("M16 list items lose the key", RED,
        "        return [_walk(v, f, key, sens, budget) for v in obj]",
        "        return [_walk(v, f, key, secret_data, budget) for v in obj]",
        CASE_TESTS, "test_n1_a_list_under_a_setting_key", "a value under a setting key was shown"),
    mutant("M17 hook brackets again", CHANNEL, "sanitise_text(text, defang=False)", "sanitise_text(text, defang=True)",
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
    mutant("M27 Authorization boundary back", REDACT, 'r"(?i)authorization[\\"\']?\\s*[:=]', 'r"(?i)\\bauthorization[\\"\']?\\s*[:=]',
        GLUED_TESTS, "test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote", "glued to a credential key is readable"),
    mutant("M28 ARN guard case-sensitive", REDACT, '    r"(?:(?i:(?![\\w.\\-*+@]{0,"', '    r"(?:(?:(?![\\w.\\-*+@]{0,"',
        GLUED_TESTS, "test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote", "glued to a credential key is readable"),
    mutant("M29 ARN guard ignores a quote", REDACT, '[\\w.\\-]{0,20}(?:=|[\\"\']\\s*[:=])))"', '[\\w.\\-]{0,20}(?:=)))"',
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
    mutant('M46 key rule bounded by a prefix again', REDACT, 'r"(?i)(?:" + KEY_WORDS + r")[\\w.\\-]{0,20}"', 'r"(?i)(?<![\\w.\\-])[\\w.\\-]{0,40}(?:" + KEY_WORDS + r")[\\w.\\-]{0,20}"',
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
    mutant('M54 double-quote rule has its own key list', REDACT, '(?:" + QUOTED_KEY_WORDS + r")"\n            r"[\\w.\\-]{0,20}[\\"\']?\\s*[:=]\\s*\\"([^\\"]', '(?:password|token)"\n            r"[\\w.\\-]{0,20}[\\"\']?\\s*[:=]\\s*\\"([^\\"]',
        BATCH4, 'test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked', 'a bare prefix key stayed readable'),
    mutant('M55 single-quote rule has its own key list', REDACT, '(?:" + QUOTED_KEY_WORDS + r")"\n            r"[\\w.\\-]{0,20}[\\"\']?\\s*[:=]\\s*\'([^\']', '(?:password|token)"\n            r"[\\w.\\-]{0,20}[\\"\']?\\s*[:=]\\s*\'([^\']',
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
    mutant('M64 quoted rules lose the bare prefixes', REDACT, 'QUOTED_KEY_WORDS = KEY_WORDS + "|pass|session|authorization"', 'QUOTED_KEY_WORDS = KEY_WORDS',
        BATCH4, 'test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked', 'a bare prefix key stayed readable'),
    mutant('M65 a new key is dropped from the one list', REDACT, 'r"pass[_\\-]?code", ', '',
        BATCH4, 'test_j1_the_d1_keys_are_masked_in_every_style_on_every_path', 'stayed readable'),
    mutant('M66 allow-list of words in front is back', RED, 'or (w.endswith(BARE_ENDINGS) and w not in ORDINARY_WORDS)',
        'or (w.endswith(BARE_ENDINGS) and w[:-4] in ("db", "user", "admin", "root", "api", "mysql"))',
        BATCH4, 'test_j2_a_key_with_any_word_in_front_is_masked_in_a_record_and_as_text', 'is shown as written in a record'),
    mutant('M67 the key list is not read by the key rule', REDACT, r'''            r"(?i)(?:" + QUOTED_KEY_WORDS + r")"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''', r'''            r"(?i)(?:password|token)"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''',
        BATCH4, 'test_j1_every_credential_of_the_corpus_is_masked_in_every_style_on_every_path', 'left a value readable'),
    mutant('M68 card second view only for the five assignment kinds', CHANNEL, 'and m.group(1) in runmap.SECRET_KINDS',
        'and m.group(1) in {"SECRET", "APIKEY", "BEARER", "BASIC", "URLCRED"}',
        BATCH4, 'test_j5_a_secret_split_by_a_tag_is_masked_on_a_card', 'a secret split by a tag is readable'),
    mutant('M69 a semicolon always ends an unquoted value', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=[^\s\"';,&])(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M70 a semicolon in front of a key does not end the value', REDACT, r'''|;(?=[^\s\"';,&])(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''|;(?=[^\s\"';,&]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value', "expected 'Password=<SECRET_1>;Server=db1'"),
    mutant('M71 flag prefix joined by hyphens only', REDACT, r'''FLAG_NAME = r"(?:[a-z0-9]+[_\-]){0,2}(?:" + FLAG_WORDS + ")"''', r'''FLAG_NAME = r"(?:[a-z0-9]+\-){0,2}(?:" + FLAG_WORDS + ")"''',
        BATCH4, 'test_j4_a_flag_with_an_underscore_or_a_hyphen_masks_its_value', 'a flag value is readable'),
    mutant('M72 flag words are a hand list', REDACT, r'''[a for a in KEY_ALTERNATIVES if "(?=" not in a] + list(FLAG_ONLY_WORDS)''',
        r'''[r"password", r"passwd", r"pwd", r"secret", r"token", r"api[_\-]?key", "pass"]''',
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
    mutant('M77 cookie assignment rule loses the jar pairs', REDACT, r'''([^\s;,\"'\[{]+(?:;\s*[^\s;=]+=[^\s;]*)*)"
        ),
    ),
    # `session_cookie=`''', r'''([^\s;,\"'\[{]+)"
        ),
    ),
    # `session_cookie=`''',
        BATCH4, 'test_j1_every_cookie_key_the_older_cookie_rule_masked_is_still_masked_with_its_jar', 'the older cookie rule masks it and this one does not'),
    mutant('M78 a placeholder ends a value even before a value character', REDACT, '    + r")_\\d+>)+(?!"\n    + _VALUE_CHAR\n    + ")|"\n    + _VALUE_CHAR\n    + "+"\n    + _VALUE_TAIL', '    + r")_\\d+>)+(?![^\\s\\"\';,&])|"\n    + _VALUE_CHAR\n    + "+"\n    + _VALUE_TAIL',
        BATCH4, 'test_j1_every_key_the_older_rule_masked_is_still_masked', 'the older rule masks it and this one does not'),
    mutant('M79 a quoted value is masked only up to its first space', REDACT, r'''(?:" + QUOTED_KEY_WORDS + r")"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""''', r'''(?:" + QUOTED_KEY_WORDS + r")"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"\s]+)[^\"]*\""''',
        BATCH4, 'test_j1_every_key_the_older_rule_masked_is_still_masked', 'the older rule masks it and this one does not'),
    mutant('M80 authorization is no bare prefix of the quoted rules', REDACT, 'QUOTED_KEY_WORDS = KEY_WORDS + "|pass|session|authorization"', 'QUOTED_KEY_WORDS = KEY_WORDS + "|pass|session"',
        BATCH4, 'test_j1_a_quoted_value_after_authorization_is_masked_whole', 'a word of the quoted value is readable'),
    mutant('M81 flags lose the glued names', REDACT, '    "newpass",\n    "oldpass",\n    "postgresauth",\n    "authorization",\n', '',
        BATCH4, 'test_j4_a_flag_with_a_word_glued_in_front_of_pass_or_auth_masks_its_value', 'a flag value is readable'),
    mutant('M82 oauth is an ordinary word again', RED, '"bandpass", "obsession"', '"bandpass", "oauth", "obsession"',
        BATCH4, 'test_j2_oauth_is_a_credential_key_in_a_record_as_it_is_in_text', 'oauth is on the ordinary-word list'),
    mutant('M83 a word with a digit in front ends a value after a semicolon', REDACT, r'''(?![A-Za-z_][\w.\-]*[\"']?\s*[:=]))"''', r'''(?![\w.\-]+[\"']?\s*[:=]))"''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M84 a word with a digit in front ends a value after a comma', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=''', r'''|,(?!\s*[\w.\-]+\s*[:=])|;(?=''',
        BATCH4, 'test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value', 'the part after the `;` is readable'),
    mutant('M85 a flag name is read through the rest of its word', REDACT, r'''|-(?:password|passwd))(?![\w-])"''', r'''|-(?:password|passwd))[\w-]*"''',
        BATCH4, 'test_j4_names_that_are_no_credential_stay_readable', 'a name that is no credential was masked'),
    mutant('M86 a comma always ends an unquoted value', REDACT, r'''|,(?!\s*[A-Za-z_][\w.\-]*\s*[:=])|;(?=''', r'''|;(?=''',
        BATCH4, 'test_j6_the_comma_pin_matches_the_code', 'a comma ended the value'),
    mutant('M87 a bearer key is not a key', REDACT, 'r"auth(?=[\\"\']?\\s*[:=])", r"session(?=[\\"\']?\\s*[:=])", r"bearer(?=[\\"\']?\\s*[:=])",', 'r"auth(?=[\\"\']?\\s*[:=])", r"session(?=[\\"\']?\\s*[:=])",',
        BATCH4, 'test_j6_the_whole_line_after_a_bearer_key_is_masked', 'a word after a bearer key is readable'),
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
