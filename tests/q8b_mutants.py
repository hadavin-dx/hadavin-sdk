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
CARDS = "approvals/cards.py"


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
        '_VALUE_TAIL = r"(?:[ \\t]+(?!--?[A-Za-z]|', '_VALUE_TAIL = r"(?:(?!)[ \\t]+(?!--?[A-Za-z]|',
        GLUED_TESTS, "test_r2_a_value_with_spaces_is_masked_whole_on_a_card", "a value with spaces is readable"),
    mutant("M31 words after the value ignore the next key", REDACT, '|[\\w.\\-]+[\\"\']?\\s*[:=])" + _VALUE_CHAR', ')" + _VALUE_CHAR',
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
    mutant("M40 sharedaccess pair removed", RED, '            "sharedaccess",\n', '',
        GLUED_TESTS, "test_r7_every_key_of_the_redactor_is_a_key_of_the_case_rule", "differs from the redactor"),
    mutant("M41 all-digit texts registered", RED, "text.isdigit() or _ONE_LOWER_WORD", "_ONE_LOWER_WORD",
        GLUED_TESTS, "test_r4_a_number_or_one_word_in_a_secret_is_not_registered", "was registered"),
    mutant("M42 one lower-case word registered", RED, " or _ONE_LOWER_WORD.fullmatch(text)", "",
        CASE_TESTS, "test_g7_common_words_of_a_secret_stay_readable", "common word was replaced"),
    mutant("M44 dot after a placeholder not bracketed", GATE, "(?<=[^\\W_]|>)\\.(?=[^\\W\\d_]{2})", "(?<=[^\\W_])\\.(?=[^\\W\\d_]{2})",
        CARD_TESTS, "test_n6_a_domain_after_a_placeholder", "bare domain is outside code"),
    mutant("M45 wide dots not folded", GATE, "    return _WIDE_DOTS.sub(\".\", part)", "    return part",
        CARD_TESTS, "test_n6_f6b_a_domain_outside_code_is_bracketed", "bare domain is outside code"),
    mutant('M46 key rule bounded by a prefix again', REDACT, 'r"(?i)(?:" + "|".join(KEY_ALTERNATIVES) + r")[\\w.\\-]{0,20}"', 'r"(?i)(?<![\\w.\\-])[\\w.\\-]{0,40}(?:" + "|".join(KEY_ALTERNATIVES) + r")[\\w.\\-]{0,20}"',
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
        ],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
