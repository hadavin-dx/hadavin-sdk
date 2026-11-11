"""The fold scan of `guard/redact.py` (P2d-1): the tests moved from core PR #50 (748849c) and the new rows of the P2d ticket.

Look-alikes, full-width forms, zero-width characters and secrets are built from parts with `chr()` or unicode escapes."""

import importlib
import random
import re

import pytest

from hadavin_sdk.guard import textnorm

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
redact = redact_mod.redact
_Redactor = redact_mod._Redactor
FOLD_NOTE = getattr(redact_mod, "FOLD_NOTE", "<no FOLD_NOTE on this head>")


KEY = "AKIA" + "IOSFODNN7EXAMPLE"


def _digits(base: int, s: str) -> str:
    return "".join(chr(base + int(c)) if c.isdigit() else c for c in s)


BENIGN_EMAIL = [  # a legitimate accented address inside a sentence of another script: ONE value to mask, the sentence to keep
    "écrire à josé@exemple.fr bientôt",
    "Contacto: señor.muñoz@correo.es para más información",
    "Bitte an jürgen.müller@beispiel.de schreiben, danke",
    "Escreva para joão.conceição@exemplo.pt hoje",
    "Napište na petr.novák@příklad.cz prosím",
    "Liên hệ nguyễn.văn@ví-dụ.vn ngay",
    "للتواصل راسلنا على josé@example.com شكرا لكم",
    "संपर्क करें josé@example.com धन्यवाद",
    "お問い合わせは" + chr(0x3000) + "josé@example.com" + chr(0x3000) + "まで",
    "联系" + chr(0x3000) + "señora@example.com" + chr(0x3000) + "谢谢",
    "ติดต่อ josé@example.com ขอบคุณ",
    "Привет, пишите на josé@example.com пожалуйста",
]


BENIGN_PLAIN = [  # no value in them at all: must come out unchanged
    "Café résumé naïve façade Zürich Ångström",
    "الطلب رقم " + _digits(0x660, "42") + " تم الشحن",
    "संस्करण " + _digits(0x966, "1") + "." + _digits(0x966, "2"),
    "订单 " + _digits(0xFF10, "123") + " 已发货",
    "السعر " + _digits(0x660, "1299") + " ريال",
    "यह एक सामान्य वाक्य है जिसमें कोई रहस्य नहीं है",
    "これは通常の文章です。秘密はありません。",
    "Ceci est une très longue phrase avec des accents éèêë àâä ôö ùûü",
    "التاريخ " + _digits(0x660, "2026") + "-" + _digits(0x660, "11") + "-" + _digits(0x660, "05"),
    "ภาษาไทยเป็นภาษาที่สวยงามมาก",
]


def _fold(t):
    return textnorm.fold(t)


SIGN_LINES = [  # lines with signs the fold changes into several characters or into non-ASCII text
    "Acme™ contact josé@example.com",  # TM
    "wait… mail josé@example.com",  # ellipsis
    "ﬁle sent to josé@example.com",  # ligature
    "area 25 m² contact josé@example.com",  # superscript digit
    "½ cup, mail josé@example.com",  # one-half sign (folds to a fraction slash: not ASCII)
    "contact josé@example.com — thanks",  # em dash
]


def test_redact_masks_a_value_hidden_behind_look_alikes_on_the_line_and_leaves_other_text_alone():
    from hadavin_sdk.guard.redact import redact

    r = redact("mail al" + chr(0x456) + "ce@example.com now")
    assert (
        "alice" not in r.text
        and "<EMAIL_1>" in r.text
        and r.mapping == {"<EMAIL_1>": "alice@example.com"}
    )  # the folded value
    r2 = redact("password=hun" + chr(0x442) + "er2xyz")
    assert "hun" not in r2.text and "<SECRET_1>" in r2.text
    assert (
        redact("caf" + chr(0xE9) + " menu").text == "caf" + chr(0xE9) + " menu"
    )  # no hit: the line is returned unchanged
    assert redact("plain ascii line").text == "plain ascii line"
    multi = redact(
        "first line"
        + chr(10)
        + "mail al"
        + chr(0x456)
        + "ce@example.com"
        + chr(10)
        + "last "
        + chr(0xE9)
    )
    assert multi.text.split(chr(10))[0] == "first line" and multi.text.endswith(
        "last " + chr(0xE9)
    )  # only the hit line changes


def test_redact_leaves_an_existing_placeholder_on_a_non_ascii_line_alone():
    from hadavin_sdk.guard.redact import redact

    r = redact("mail alice@example.com and caf" + chr(0xE9))
    assert r.text == "mail <EMAIL_1> and caf" + chr(0xE9) and list(r.mapping) == ["<EMAIL_1>"]


def test_benign_multilingual_corpus_has_a_zero_false_withhold_rate():
    corpus = BENIGN_EMAIL + BENIGN_PLAIN
    withheld = [ln for ln in corpus if FOLD_NOTE in redact(ln).text]
    rate = len(withheld) / len(corpus)
    assert rate == 0.0, (
        rate,
        withheld,
    )  # FAIL-BEFORE: every accented-address line was withheld whole
    for ln in BENIGN_PLAIN:
        assert redact(ln).text == ln, ln
    for ln in BENIGN_EMAIL:
        r = redact(ln)
        assert "<EMAIL_1>" in r.text and "@" not in r.text, (ln, r.text)
        # only the value went: the words before and after it are still there, as written
        before, after = re.split(r"\S+@\S+", ln, maxsplit=1)
        assert r.text.startswith(before) and r.text.endswith(after), (ln, r.text)
        assert textnorm.fold(r.mapping["<EMAIL_1>"]).count("@") == 1


def test_native_digits_of_a_value_are_masked_in_place_not_withheld():
    ln = "card " + _digits(0x660, "4111 1111 1111 1111") + " thanks, café"
    r = redact(ln)
    assert FOLD_NOTE not in r.text and "café" in r.text and "thanks" in r.text
    assert not re.search(r"\d{4}", textnorm.fold(r.text)), r.text


def test_attacks_are_still_withheld_whole_and_never_emitted_folded():
    cyr = chr(0x410) + "KIA" + "IOSFODNN7EXAMPLE"
    fw = "<!channel>".translate({ord(c): ord(c) + 0xFEE0 for c in "<>!abcdefghijklmnopqrstuvwxyz"})
    for ln in (f"key {cyr} {fw}", f"{fw} {cyr}", "mail al" + chr(0x456) + "ce@example.com now"):
        out = redact(ln).text
        assert out.startswith(FOLD_NOTE), (ln, out)
        assert KEY not in textnorm.fold(out) and "<!" not in textnorm.fold(out)
    # a hidden value next to accented text: the look-alike makes it an attack, the whole line goes
    assert FOLD_NOTE in redact("café " + cyr).text


def test_a_lookalike_copy_of_a_value_that_also_stands_in_clear_is_still_a_hit():
    ln = f"first {KEY} then second {chr(0x410)}{KEY[1:]}"
    out = redact(ln).text
    assert KEY not in textnorm.fold(out), (
        out
    )  # FAIL-BEFORE: a set compare saw "nothing new"; the look-alike copy stayed in the text


@pytest.mark.parametrize(
    ("line", "expected", "value"),
    [
        (
            "mail josé@example.com now",
            "mail <EMAIL_1> now",
            "jose@example.com",
        ),  # a combining mark inside the value
        (
            "x ́josé@example.coḿ y",
            "x ́<EMAIL_1>́ y",
            "jose@example.com",
        ),  # marks around it stay where they were
        (
            "mail al\u200bice@example.com now",
            "mail <EMAIL_1> now",
            "alice@example.com",
        ),  # a zero-width space inside the local part
        (
            "\u200balice@example.com\u200b",
            "\u200b<EMAIL_1>\u200b",
            "alice@example.com",
        ),  # leading and trailing zero-width spaces
        (
            "mail alice@example.com end",
            "mail <EMAIL_1> end",
            "alice@example.com",
        ),  # no-break spaces
        (
            "key AKIAIOSFODNN7EXAMPLE end",
            "key <APIKEY_1> end",
            KEY,
        ),  # a Kelvin sign inside the value: masked whole
        (
            "a josé@example.com b maría@example.com c",
            "a <EMAIL_1> b <EMAIL_2> c",
            "jose@example.com",
        ),  # two values, offsets of the second
        (
            "Acme™ mail josé@example.com … done",
            "Acme™ mail <EMAIL_1> … done",
            "jose@example.com",
        ),  # signs outside the value stay
        (
            "ﬁle josé@example.com",
            "ﬁle <EMAIL_1>",
            "jose@example.com",
        ),  # a ligature outside the value
        (
            "Cookie: sid=josé@example.com; a=bé",
            "Cookie: <SECRET_1>",
            None,
        ),  # two rounds change the text, a third finds nothing
    ],
)
def test_in_place_masking_cases(line, expected, value):
    r = redact(line)
    assert r.text == expected, (line, r.text)
    assert FOLD_NOTE not in r.text
    if value:
        # the map holds the value as WRITTEN in the line (zero-width spaces, marks and all), not its folded spelling
        pattern = re.escape(expected)
        pattern = re.sub(
            r"<[A-Z]+_[0-9]+>", "(.+?)", pattern.replace("\\<", "<").replace("\\>", ">")
        )
        m = re.fullmatch(pattern, line)
        assert m, (line, expected)
        written = m.groups()
        assert written, expected
        for placeholder, original in zip(
            re.findall(r"<[A-Z]+_[0-9]+>", expected), written, strict=True
        ):
            assert r.mapping[placeholder] == original, (placeholder, r.mapping)
        assert any(w != value for w in written) or value in r.mapping.values()


def test_a_sign_inside_a_value_withholds_the_line_instead_of_masking_around_it():
    # an ellipsis or a one-half sign INSIDE the matched value is a flagged character: the whole line goes, never a half-masked value
    for ln in ("mail jose…@example.com", "mail jos½@example.com"):
        assert redact(ln).text.startswith(FOLD_NOTE), ln


def test_the_cases_that_fall_back_to_withholding_leak_nothing():
    for ln in ("mail jose…@example.com", "key " + chr(0x410) + KEY[1:] + " x"):
        out = redact(ln).text
        assert "jose" not in _fold(out) and KEY not in _fold(out), out


def test_four_rounds_that_never_converge_fall_through_to_the_withhold(monkeypatch):
    assert hasattr(_Redactor, "_apply_claims"), "hook missing on this head"
    calls = []

    def never_done(self, body, spans):
        calls.append(body)
        return body + " "

    monkeypatch.setattr(_Redactor, "_apply_claims", never_done)
    out = redact("mail josé@example.com now").text
    assert len(calls) == 4  # FAIL-BEFORE (mutant): a loop that is not capped at four rounds
    assert out.startswith(FOLD_NOTE) and "jose@example.com" not in _fold(out)


def test_the_malformed_offset_is_caught_by_a_value_in_front_of_and_behind_other_text():
    # the output must be the original text with ONLY the value replaced: every other character, accents included, in its place
    ln = "café été josé@example.com naïve über"
    assert redact(ln).text == "café été <EMAIL_1> naïve über"


def test_a_multi_line_value_that_only_the_fold_sees_is_replaced_not_left(monkeypatch):
    pat = re.compile(r"BEGINX\nKEY=([A-Z0-9]{8})")
    monkeypatch.setattr(redact_mod, "PATTERNS", [*redact_mod.PATTERNS, ("SECRET", pat)])
    text = "BEGINX\nKEY=ABCD" + chr(0x412) + "EFG\nafter café"
    out = redact(text).text
    assert "ABCD" not in _fold(out) and "EFG" not in _fold(out), (
        out
    )  # FAIL-BEFORE: the match starts on an ASCII line that nothing treated
    assert out.endswith("after café")


def test_withhold_rate_on_lines_with_signs_is_measured_and_pinned():
    withheld = [ln for ln in SIGN_LINES if FOLD_NOTE in redact(ln).text]
    # honest number: 0 of 6 since batch 3 (the one-half sign folds to a fraction slash, which is now mapped to "/" and masked around;
    # TM, ellipsis, ligature, superscript are masked in place, the em dash is not changed by the fold). With the 22 lines of the first
    # corpus: 0 of 28. A sign INSIDE a value, or a full-width slash anywhere, still withholds the line (see test_pr50_fix_batch3.py).
    assert withheld == [], withheld


def test_an_account_number_below_an_accented_or_full_width_keyword_is_masked_when_a_bank_word_stands_elsewhere():
    accent = "BSB 062-000\naccó" + "unt number 12345678"
    wide = "BSB 062-000\n" + "".join(chr(ord(c) + 0xFEE0) for c in "account") + " number 12345678"
    for text in (accent, wide):
        out = redact(text).text
        assert "12345678" not in _fold(out), out  # FAIL-BEFORE: the number stayed in clear
    assert (
        "12345678" not in redact("BSB 062-000\naccount number 12345678").text
    )  # the ASCII control case


def test_one_half_is_masked_around_but_a_full_width_slash_is_still_an_attack():
    assert (
        redact("½ cup, mail josé@example.com now").text == "½ cup, mail <EMAIL_1> now"
    )  # FAIL-BEFORE: withheld
    assert redact("mail josé@example.com ／／ x").text.startswith(FOLD_NOTE)


# ===================================================== new rows (P2d-1) =====================================================
import string
import unicodedata

from hadavin_sdk.guard import runmap

LOOKALIKES = (
    textnorm._LOOKALIKES
)  # P1a keeps the table private; the ticket's `textnorm.LOOKALIKES` does not exist (BN)
CANARY = "sk-" + string.ascii_letters + string.digits
PH = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")


def _old_tree_guard() -> None:
    assert hasattr(_Redactor, "_apply_claims"), "hook missing on this head"


def _single_letter_entries(allowed: str) -> list[tuple[str, str]]:
    return [(k, v) for k, v in LOOKALIKES.items() if len(v) == 1 and v.isascii() and v in allowed]


def _windows(canary: str, size: int = 12) -> list[str]:
    return [canary[i : i + size] for i in range(len(canary) - size + 1)]


def test_table_1_every_single_letter_lookalike_in_a_canary_key_is_masked():
    entries = _single_letter_entries(string.ascii_letters + string.digits)
    assert len(entries) >= 500, len(entries)
    body = CANARY[3:]
    leaks = []
    for look, letter in entries:
        spelled = "sk-" + body.replace(letter, look, 1)
        out = redact("the key " + spelled + " end").text
        folded = textnorm.fold(out)
        if any(w in folded for w in _windows(CANARY)):
            leaks.append((hex(ord(look)), letter))
    assert not leaks, (len(leaks), leaks[:5])


def test_table_2_every_single_letter_lookalike_in_an_aws_key_is_masked():
    entries = _single_letter_entries(KEY)
    assert len(entries) >= 100, len(entries)
    leaks = []
    for look, letter in entries:
        spelled = KEY.replace(letter, look, 1)
        out = redact("the key " + spelled + " end").text
        if any(w in textnorm.fold(out) for w in _windows(KEY)):
            leaks.append((hex(ord(look)), letter))
    assert not leaks, (len(leaks), leaks[:5])


def _decimal_zero_scripts() -> list[int]:
    return [
        cp for cp in range(0x20000) if chr(cp).isdecimal() and int(chr(cp)) == 0 and chr(cp) != "0"
    ]


def test_digits_1_digits_of_every_script_in_an_iban_and_a_card_leave_no_run_of_eight():
    bases = _decimal_zero_scripts()
    assert len(bases) >= 60, len(bases)
    iban = "GB82" + "WEST" + "12345698765432"
    card = "4111 1111 1111 1111"
    for base in bases:
        for text in (iban, card):
            spelled = "".join(chr(base + int(c)) if c.isdigit() else c for c in text)
            out = redact("pay " + spelled + " now").text
            digits_left = textnorm.fold(out).replace(
                " ", ""
            )  # the card is written in groups of four: no space, or no run of eight can exist
            assert not re.search(r"[0-9]{8}", digits_left), (hex(base), text, out)


def test_align_2_the_alignment_agrees_with_the_fold_or_steps_aside():
    _old_tree_guard()
    marks = [chr(cp) for cp in range(0x110000) if unicodedata.category(chr(cp)) == "Mn"]
    assert len(marks) > 1500
    for mark in marks:
        s = "e" + mark + "x"
        got = _Redactor._aligned_fold(s, float("inf"))
        assert got is None or got[0] == textnorm.fold(s).replace("⁄", "/"), hex(ord(mark))
    zwj = chr(0x200D)
    for s in (
        unicodedata.normalize("NFD", "한글 한국어"),
        "a" + zwj + "b",
        "👨" + zwj + "👩" + zwj + "👧",
        chr(0x1100) + chr(0x1161) + chr(0x11A8),
        "क" + chr(0x094D) + "ष",
    ):
        got = _Redactor._aligned_fold(s, float("inf"))
        assert got is None or got[0] == textnorm.fold(s).replace("⁄", "/"), s
    pair = chr(0x1100) + chr(
        0x1161
    )  # a decomposed Hangul syllable: fold composes it, the table cannot
    assert _Redactor._aligned_fold(pair, float("inf")) is None
    for benign in ("Café résumé naïve façade Zürich Ångström", "señor muñoz"):
        assert redact(benign).text == benign


def test_d1_1_a_fraction_slash_beside_an_accented_address_is_masked_in_place():
    slash = chr(0x2044)
    text = "mail josé@exemple.fr 1" + slash + "2 end"
    assert redact(text).text == "mail <EMAIL_1> 1" + slash + "2 end"
    assert (
        redact("mail josé@exemple.fr " + slash + " end").text == "mail <EMAIL_1> " + slash + " end"
    )


def test_ascii_1_an_ascii_text_with_no_non_ascii_value_never_enters_the_fold_scan(monkeypatch):
    assert hasattr(_Redactor, "_fold_scan"), "hook missing on this head"
    calls = []
    real = _Redactor._fold_scan
    monkeypatch.setattr(_Redactor, "_fold_scan", lambda self, t: calls.append(1) or real(self, t))
    out = redact("mail jose@exemple.fr and password: hunter2xyz").text
    assert out == "mail <EMAIL_1> and password: <SECRET_1>"
    assert calls == []
    redact("café")
    assert calls == [1]


def test_ascii_2_a_bank_word_on_a_non_ascii_line_widens_the_masking_on_an_ascii_line():
    _old_tree_guard()
    far = "x" * 300  # beyond the 100-character window of the ordinary bank context
    line = "acct 12345678"
    mixed = redact("bank account list café\n" + far + "\n" + line).text
    assert "12345678" not in mixed
    control = redact("bank account list cafe\n" + far + "\n" + line).text
    assert "12345678" in control


def test_ascii_3_a_block_that_starts_on_an_ascii_line_is_withheld_whole(monkeypatch):
    _old_tree_guard()
    pat = re.compile(r"BEGINX\nKEY=([A-Z0-9]{8})")
    monkeypatch.setattr(redact_mod, "PATTERNS", [*redact_mod.PATTERNS, ("SECRET", pat)])
    out = redact("first\nBEGINX\nKEY=ABCD" + chr(0x412) + "EFG\nafter café").text
    assert out.startswith("first\n" + FOLD_NOTE)
    assert "ABCD" not in textnorm.fold(out)
    assert out.endswith("after café")


def test_ascii_4_an_ascii_text_that_adds_a_key_builds_once_with_one_fold_per_non_ascii_value(
    monkeypatch,
):
    _old_tree_guard()
    folds, builds, scans = [], [], []
    real_fold, real_build, real_scan = redact_mod.fold, _Redactor._build, _Redactor._fold_scan
    monkeypatch.setattr(redact_mod, "fold", lambda t, **k: folds.append(t) or real_fold(t, **k))
    monkeypatch.setattr(
        _Redactor, "_build", lambda self: builds.append(len(folds)) or real_build(self)
    )
    monkeypatch.setattr(
        _Redactor, "_fold_scan", lambda self, t: scans.append(1) or real_scan(self, t)
    )
    m = runmap.RunMap({f"<NAME_{i}>": f"Josée Martín{i} Zürich" for i in range(1, 4)})
    runmap.redact_text("note: password: hunter2xyz", m)
    assert scans == [] and len(builds) == 1
    assert len([f for f in folds if f.startswith("Josée")]) == 3
    before = len(builds)
    runmap.redact_text("nothing new here", m)
    assert len(builds) == before  # a text that adds nothing builds nothing
    runmap.redact_text("note: token: " + "Tq7vK2" + "xLm9pZw", m)
    assert len(builds) == before + 1
    assert len([f for f in folds if f.startswith("Josée")]) >= 6


def test_sep_1_a_value_split_by_line_separators_is_masked_or_withheld_never_left():
    rng = random.Random(20261106)  # noqa: S311 - seeded test generator
    seps = [" ", "\u0085", "\u000b", "\r\n", "\r", "\n"]
    for _ in range(300):
        sep = rng.choice(seps)
        look = rng.choice([chr(0x430), chr(0x435), chr(0x43E), chr(0x2D0)])
        head = "".join(rng.choice([c, look]) if c in "aeo" else c for c in "hunter-secret-a1b2c3")
        text = f"password: {head}{sep}mail josé@exemple.fr{sep}note " + head
        out = redact(text).text
        assert "exemple.fr" not in textnorm.fold(out), (repr(text), out)
        assert textnorm.fold(head) not in textnorm.fold(out), (
            repr(text),
            out,
        )  # the password too, in every copy


def test_pem_1_a_pem_block_with_a_lookalike_on_a_later_line_leaves_no_key_line():
    body = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC"
    text = (
        "before\n"
        + "-----BEGIN "
        + "PRIVATE KEY-----"
        + "\n"
        + body
        + "\n"
        + body[:14]
        + chr(0x430)
        + body[15:]
        + "\n"
        + body
        + "\n"
        + "-----END "
        + "PRIVATE KEY-----"
        + "\nafter"
    )
    out = redact(text).text
    assert body[:14] not in textnorm.fold(out), out
    assert out.startswith("before\n") and out.endswith("after")


def test_map_1_the_map_holds_the_written_spelling():
    _old_tree_guard()
    r = redact("mail josé@exemple.fr")
    assert r.text == "mail <EMAIL_1>"
    assert r.mapping["<EMAIL_1>"] == "josé@exemple.fr"
    restored = r.restore(r.text)
    assert restored == "mail josé@exemple.fr", repr(restored)
    z = redact("password: hunt\u200ber2")
    assert z.mapping["<SECRET_1>"] == "hunt\u200ber2"
    assert "\u200b" in repr(z.restore(z.text)) or "\\u200b" in repr(z.restore(z.text))


def test_map_2_two_spellings_get_two_placeholders_and_restore_only_the_plain_one():
    _old_tree_guard()
    r = redact("jose@exemple.fr and josé@exemple.fr")
    assert r.text == "<EMAIL_1> and <EMAIL_2>"
    assert r.mapping == {"<EMAIL_1>": "jose@exemple.fr", "<EMAIL_2>": "josé@exemple.fr"}
    assert not hasattr(r, "alias") and not hasattr(r, "sweep_spellings")
    assert runmap.restore_text(r.text, r.mapping) == "jose@exemple.fr and <EMAIL_2>"
    # a body whose aligned text and fold disagree is withheld, never masked in place
    hangul = chr(0x1100) + chr(0x1161)
    out = redact(hangul + " mail josé@exemple.fr").text
    assert out.startswith(FOLD_NOTE), out


def test_map_3_a_value_made_by_the_fold_scan_occurs_in_the_input_unless_its_line_is_withheld():
    texts = (
        list(BENIGN_EMAIL)
        + list(BENIGN_PLAIN)
        + [
            "key " + KEY.replace("A", chr(0x410), 1) + " end",
            "mail josé@exemple.fr 1⁄2 end",
        ]
    )
    rng = random.Random(7)  # noqa: S311 - seeded test generator
    for _ in range(100):
        look = rng.choice(["\u200b", "́", chr(0x435)])
        texts.append("mail jos" + look + "e@exemple.fr end")
    for t in texts:
        r = redact(t)
        excluded = set()
        for ln in r.text.splitlines():
            if FOLD_NOTE in ln:
                excluded |= set(PH.findall(ln))
        for ph, val in r.mapping.items():
            if ph in excluded:
                continue
            assert val in t, (t, ph, val)


def test_map_4_two_occurrences_get_two_placeholders_in_both_orders():
    _old_tree_guard()
    r = redact("jose@exemple.fr josé@exemple.fr")
    assert len(set(PH.findall(r.text))) == 2 and sorted(r.mapping.values()) == sorted(
        ["jose@exemple.fr", "josé@exemple.fr"]
    )
    # two accented spellings of one folded value (precomposed and decomposed) also keep two placeholders
    two = redact("josé@exemple.fr and " + unicodedata.normalize("NFD", "josé") + "@exemple.fr")
    assert len(set(PH.findall(two.text))) == 2 and len(two.mapping) == 2, two
    r2 = redact("accent josé@exemple.fr\nthen\nclear jose@exemple.fr")
    assert len(set(PH.findall(r2.text))) == 2
    assert set(r2.mapping.values()) == {"josé@exemple.fr", "jose@exemple.fr"}
    for first, second in (
        ("jose@exemple.fr", "josé@exemple.fr"),
        ("josé@exemple.fr", "jose@exemple.fr"),
    ):
        m = runmap.RunMap()
        a = runmap.redact_text("mail " + first, m)
        b = runmap.redact_text("again " + second, m)
        assert PH.findall(a) != PH.findall(b)
        assert set(m.values()) == {"jose@exemple.fr", "josé@exemple.fr"}


def test_map_5_a_precomposed_name_is_restored_and_a_decomposed_one_stays_a_placeholder():
    pre = "customer name: José García"
    dec = "customer name: " + unicodedata.normalize("NFD", "José García")
    assert pre != dec
    for text, restorable in ((pre, True), (dec, False)):
        r = redact(text)
        assert PH.search(r.text), (text, r.text)
        back = runmap.restore_text(r.text, r.mapping)
        assert (back == text) is restorable, (repr(back), repr(text))


def test_map_6_a_clear_copy_of_the_folded_spelling_is_masked_by_the_alias_key():
    _old_tree_guard()
    cases = [
        "mail jos\u200be@exemple.fr end",
        "mail josé@exemple.fr end",
        "password: hunt\u200ber2",
        "password: Tq7v́K2xLm9pZw",
    ]
    for t in cases:
        r = redact(t)
        written = [v for v in r.mapping.values() if not v.isascii()]
        assert written, (t, r.mapping)
        for w in written:
            copy = textnorm.fold(w)
            out = redact(t + "\nlater " + copy, mapping=dict(r.mapping)).text
            later = out.split("later", 1)[1]
            assert copy not in later, (t, out)
            # An e-mail copy is plain ASCII, so a direct pass masks it under a fresh placeholder whatever the alias index does (stated limit 4
            # in the CHANGELOG): for it, "gone from the text" is all this test can show. A copy that a direct pass leaves alone (the password
            # values) can only be masked by the alias index, and it must get the placeholder the written spelling already has.
            if redact(copy).text != copy:
                continue
            held = [k for k, v in r.mapping.items() if v == w]
            assert held and any(k in later for k in held), (t, held, later)


def test_fold_note_1_the_note_is_the_fixed_text():
    assert (
        getattr(redact_mod, "FOLD_NOTE", None)
        == "[line withheld: look-alike text hid a protected value]"
    )
    assert redact("mail josé@exemple.fr ／／ x").text.startswith(
        "[line withheld: look-alike text hid a protected value]"
    )


def _tagged(text: str) -> str:
    return "".join(chr(0xE0000 + ord(c)) for c in text)


def _tag_leak(text: str, key: str) -> bool:
    decoded = "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0020 <= ord(c) <= 0xE007E)
    return key[:12] in decoded


@pytest.mark.xfail(
    strict=True,
    reason="open hole GAP-1: closed by P2d-2 (a pass here means it is closed: remove this mark)",
)
def test_gap_1_tag_characters_hide_a_key_open_hole():
    text = "the note " + _tagged(KEY) + " end"
    assert _tag_leak(text, KEY)
    assert not _tag_leak(redact(text).text, KEY)


def test_gap_1_the_tagged_key_reads_as_the_key():
    assert _tag_leak("the note " + _tagged(KEY) + " end", KEY)


@pytest.mark.parametrize(("cp", "letter"), [(0x1CCD6, "A"), (0x113D4, "l"), (0x16EB6, "b")])
def test_p1b_1_an_unassigned_code_point_in_place_of_a_letter_is_masked_on_this_unicode_build(
    cp, letter
):
    ch = chr(cp)
    if unicodedata.category(ch) != "Cn":
        pytest.skip("assigned on this Unicode build")
    spelled = "sk-" + CANARY[3:].replace(letter, ch, 1)
    text = "the key " + spelled + " end"
    assert ch in text
    assert ch not in redact(text).text


def test_ctrl_1_the_outcome_helper_sees_a_masked_key_and_a_leaked_one():
    plain = redact("the key " + CANARY + " end").text
    assert not any(w in plain for w in _windows(CANARY)) and PH.search(plain)
    one = "sk-" + CANARY[3:].replace("a", chr(0x430), 1)
    out = redact("the key " + one + " end").text
    assert not any(w in out for w in _windows(CANARY)) and PH.search(out)
    assert any(
        w in "the key " + CANARY for w in _windows(CANARY)
    )  # the helper sees a leak when there is one


V13 = "Tq7vK2x" + "La9pZw"  # a made-up secret of 13 characters, built from parts for the tests


def _context_text(copy: str) -> str:
    return "password: " + V13 + "\nfiller one\nfiller two\nfiller three\n" + copy


@pytest.mark.xfail(
    strict=True,
    reason="open hole VARIANT-1(a): closed by P2d-2 (a pass here means it is closed: remove this mark)",
)
def test_variant_1_a_bare_redact_zwsp_copy_open_hole():
    copy = V13[:7] + chr(0x200B) + V13[7:]
    assert copy.replace(chr(0x200B), "") == V13
    assert copy not in redact(_context_text(copy)).text


def test_variant_1_b_redact_text_masks_a_zwsp_and_a_full_width_copy_with_one_placeholder():
    wide = "".join(chr(0xFF00 + ord(c) - 0x20) if c.isascii() and c.isalnum() else c for c in V13)
    for copy in (V13[:7] + chr(0x200B) + V13[7:], wide):
        m = runmap.RunMap()
        out = runmap.redact_text(_context_text(copy), m)
        assert V13 not in textnorm.fold(out) and copy not in out, out
        assert len(m) == 1, m
        assert out.rstrip().endswith(next(iter(m)))


@pytest.mark.xfail(
    strict=True,
    reason="open hole VARIANT-1(c): closed by P2d-2 (a pass here means it is closed: remove this mark)",
)
def test_variant_1_c_redact_text_lookalike_copy_open_hole():
    copy = V13.replace("a", chr(0x430))
    assert copy != V13
    m = runmap.RunMap()
    assert copy not in runmap.redact_text(_context_text(copy), m)


def test_restore_1_a_withheld_line_placeholder_is_restorable():
    text = "mail josé@example.com ／／ x"
    r = redact(text)
    assert r.text.startswith(FOLD_NOTE)
    assert runmap.restore_text(r.text, r.mapping) != r.text, (
        "the placeholder is not restorable on this head"
    )


@pytest.mark.xfail(
    strict=True,
    reason="open hole L5: closed by the P5c marker (a pass here means it is closed: remove this mark)",
)
def test_restore_2_a_withheld_line_does_not_restore_a_value_the_input_did_not_hold():
    text = "mail josé@example.com ／／ x"
    r = redact(text)
    assert "jose@example.com" not in runmap.restore_text(r.text, r.mapping)


def test_sweep_1_a_clear_copy_after_a_written_variant_gets_the_same_placeholder():
    _old_tree_guard()
    r = redact("password: hunt\u200ber2\nlater hunter2")
    assert r.text == "password: <SECRET_1>\nlater <SECRET_1>"
    assert r.mapping["<SECRET_1>"] == "hunt\u200ber2"
    back = redact("password: hunter2\nlater password: hunt\u200ber2\nand hunt\u200ber2 again")
    assert "hunter2" not in textnorm.fold(back.text) and "hunt" not in back.text.replace(
        "password", ""
    )
    mixed = redact("password: AbCd\u200bEfGh\nlater AbCdEfGh")
    assert mixed.text == "password: <SECRET_1>\nlater <SECRET_1>", mixed


def test_sweep_3_the_pieces_of_a_written_variant_are_swept_like_the_plain_value():
    _old_tree_guard()
    plain = redact('password="Tq7vK2xLa9 Zw3mP4rY8n"\nlater Tq7vK2xLa9 and Zw3mP4rY8n').text
    var = redact('password="Tq7vK2x\u200bLa9 Zw3mP4rY8n"\nlater Tq7vK2xLa9 and Zw3mP4rY8n').text
    assert "Tq7vK2xLa9" not in var and "Zw3mP4rY8n" not in var
    assert PH.sub("<P>", var) == PH.sub("<P>", plain)


def test_sweep_6_an_alias_key_that_is_a_prefix_of_a_longer_stored_value_raises_nothing():
    _old_tree_guard()
    longer = "hunter2longer"
    m = {"<SECRET_1>": longer}
    r = redact("password: hunt\u200ber2\nlater " + longer + " and hunter2 end", mapping=m)
    assert longer not in r.text and "hunter2" not in r.text, r.text
    assert "<SECRET_1>" in r.text


def test_reg_1a_a_discarded_round_leaves_no_orphan_placeholder():
    _old_tree_guard()
    hidden = KEY.replace("A", chr(0x410), 1)
    r = redact("mail josé@exemple.fr key " + hidden)
    held = set(PH.findall(r.text))
    assert set(r.mapping) == held, (r.text, r.mapping)
    assert "josé@exemple.fr" not in r.mapping.values()


def test_reg_1b_non_converging_rounds_leave_no_orphan_placeholder(monkeypatch):
    _old_tree_guard()
    real = _Redactor._apply_claims

    def wrapper(self, body, spans):
        return real(self, body, spans) + "x"

    monkeypatch.setattr(_Redactor, "_apply_claims", wrapper)
    line = "mail josé@exemple.fr end"
    r = redact(line)
    assert r.text.startswith(FOLD_NOTE)
    assert set(r.mapping) == set(PH.findall(r.text)), (r.text, r.mapping)
    assert list(r.mapping) == ["<EMAIL_1>"], r.mapping
    monkeypatch.undo()
    assert list(redact(line).mapping) == ["<EMAIL_1>"]


def test_view_2_what_a_view_does_to_the_output():
    # a new value only the percent-escape view reveals: the map grows by one and the view's text is the output
    m = runmap.RunMap()
    out = runmap.redact_text("password%3Dhunter2xyz", m)
    assert "hunter2xyz" not in out and len(m) >= 1, (out, m)
    # the `_held` case: stage 2 adds no map entry, yet the view replaces the output because it holds more placeholders
    copy = V13[:7] + chr(0x200B) + V13[7:]
    text = _context_text(copy)
    stage1 = dict(redact(text).mapping)
    m2 = runmap.RunMap()
    out2 = runmap.redact_text(text, m2)
    assert dict(m2) == stage1
    assert copy not in out2 and out2.rstrip().endswith(next(iter(m2))), out2
    # control: a ZWSP-split secret: the view mints a second placeholder with the canonical spelling
    m3 = runmap.RunMap()
    out3 = runmap.redact_text("password: hunt\u200ber2", m3)
    assert "hunt" not in out3 and "er2" not in out3.replace("<SECRET_", ""), out3
    assert set(m3.values()) >= {"hunt\u200ber2", "hunter2"}, m3


def test_text_before_a_masked_value_is_kept_once_between_two_in_place_masks():
    _old_tree_guard()
    r = redact("a josé@example.com b maría@example.com c")
    assert r.text == "a <EMAIL_1> b <EMAIL_2> c", r.text
