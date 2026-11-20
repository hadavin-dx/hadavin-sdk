"""P1d-a review M6: an independent link oracle for approval cards.

The properties in test_p1d_a_paths.py use the defanger's own regexes (`_DOMAIN`, `_DOMAIN_LAST`, `_NON_ASCII_HOST`) as the
oracle, so defanger and oracle share their blind spots (`see/evil.com`, `[evil.com]`, `evil.com-x` match none of them).
This oracle shares no code with `hadavin_sdk`: its own top-level-domain list, its own code-span reader, and a rule that
is wider than a renderer's linkifier (a host is any dotted name ending in a suffix of its own list, touching no letter or
digit on either side, with any dot look-alike; `_`, `-`, `/` and `.` save nothing). The remaining limits are in
handover/core-c/evidence/G2-p1d-a.md (round 3).
"""

import os
import re
import sys
import unicodedata

import pytest

from hadavin_sdk.approvals import channel, gate

# Written here, not imported: an independent list (a superset of the plausible ones plus the internal suffixes).
_SUFFIXES = "com|org|net|io|dev|app|co|us|uk|de|fr|ru|cn|info|biz|edu|gov|ai|me|xyz|cc|tv|sh|zip|digital|internal|corp|local|lan|test|example"
_DOTS = ".\u3002\uff0e\uff61"  # ASCII dot and the three a URL parser maps to it (UTS 46); U+2024 and the like are not dots there
_ALNUM = r"[^\W_]"  # letters and digits of any script
_LABEL = rf"{_ALNUM}(?:[\w-]*{_ALNUM})?"
# A host is a run of dotted labels ending in a suffix from the list above, with NO boundary rule of the defanger's: it
# only must not touch a letter or digit on either side (`xevil.com` and `evil.comx` are other names). `_`, `-`, `/` and
# `.` are not boundaries that save a host: a Slack or markdown-it renderer may link `x/evil.com`, `evil.com-x`,
# `..evil.com` and `_evil.com_` (emphasis is parsed first and leaves `evil.com` in a text token), and a fail-closed
# check assumes it does. The stated limit of this oracle: the suffix list is its own and finite, see the evidence file.
_HOST = re.compile(
    rf"(?<!{_ALNUM})(?:{_LABEL}[{re.escape(_DOTS)}])+(?:{_SUFFIXES})(?!{_ALNUM})",
    re.IGNORECASE,
)
_FENCE_OPEN = re.compile(r"^(?:[ ]{0,3}(?:>[ ]?|[-*+][ ]+|\d{1,9}[.)][ ]+))*[ ]{0,3}(`{3,})[^`]*$")


def _without_code(text: str) -> str:
    """Own reader, CommonMark's rules: a fence is at most 3 spaces of indent (after any quote or list marker) and
    closes on a line of at least as many backticks and nothing else; a backslash-escaped backtick is no code marker;
    closed fences and single-line backtick pairs are dropped when every backtick is paired (else keep all)."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        m = _FENCE_OPEN.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        closer = re.compile(rf"^(?:[ ]{{0,3}}>[ ]?)*[ ]{{0,3}}`{{{len(m.group(1))},}}[ \t]*$")
        j = next((k for k in range(i + 1, len(lines)) if closer.match(lines[k])), None)
        if j is None:  # an unclosed fence is not code here: read everything
            return text
        i = j + 1
    kept = []
    for ln in out:
        plain = ln.replace("\\`", " ")
        pairs = re.sub(r"`[^`\n]+`", "", plain)
        if "`" in pairs:
            return "\n".join(
                out
            )  # unpaired backtick: a renderer may pair differently; read everything
        kept.append(pairs)
    return "\n".join(kept)


def _strip_placeholders(text: str) -> str:
    return re.sub(r"<[A-Z][A-Z0-9]*_\d+>", "PH", text)


def links(text: str) -> list[str]:
    """Hosts a lenient linkifier could make clickable in `text` (as shown, `[.]` is the defang and is not a dot)."""
    shown = unicodedata.normalize("NFKC", _strip_placeholders(_without_code(text)))
    shown = shown.replace("\u200b", "")
    return [m.group(0) for m in _HOST.finditer(shown)]


def _h(*labels: str) -> str:
    return ".".join(labels)


EVIL = _h("evil", "com")
DEEP = _h("db01", "corp", "example", "com")
PUB = _h("docs", "example", "com")

# (name, text). Every row holds a host in some shape; the card must show no linkable host.
SHAPES = [
    ("plain", f"open {EVIL} now"),
    ("plain_deep", f"open {DEEP} now"),
    ("sentence_end", f"see {PUB}."),
    ("comma", f"{EVIL}, {PUB}; {DEEP}:"),
    ("bracketed", f"[{EVIL}]"),
    ("paren", f"({EVIL})"),
    ("quoted", f"\"{EVIL}\" and '{PUB}'"),
    ("md_link", f"[click]({'https://' + EVIL})"),
    ("md_link_bare_target", f"[{EVIL}](//{PUB})"),
    ("md_link_text_is_host", f"[{PUB}](x)"),
    ("md_ref", f"[a][1]\n\n[1]: {'https://' + EVIL}"),
    ("md_image", f"![{EVIL}]({PUB})"),
    ("angle", f"<{'https://' + EVIL}> and <{PUB}>"),
    ("angle_mail", f"<{'mailto:' + 'a@' + EVIL}>"),
    ("slack_link", f"<{'https://' + EVIL}|{PUB}>"),
    ("scheme_http", "see " + "http" + "s://" + PUB + "/a?b=c"),
    ("scheme_relative", f"//{EVIL}/x"),
    ("mixed_case", "Visit " + "EVIL" + "." + "CoM" + " or " + "Docs.Example.COM"),
    ("upper_scheme", "HTTP" + "S://" + "EVIL." + "COM"),
    ("encoded_dot", "see " + "evil%2" + "Ecom"),
    ("entity_dot", "see " + "evil&#46;" + "com" + " " + "evil&period;" + "com"),
    ("glued_word_before", f"visit{EVIL}"),
    ("glued_word_after", f"{EVIL}now"),
    ("glued_underscore_after", f"{PUB}_x"),
    ("glued_underscore_before", f"_{PUB}_"),
    ("glued_digit", f"{PUB}9 and 9{PUB}"),
    ("emphasis", f"*{EVIL}* **{PUB}** _{DEEP}_ ~~{EVIL}~~"),
    ("punct_run", f"!!{EVIL}?? ,,{PUB}.. ;;{DEEP},,"),
    ("bracket_before", f"[{EVIL}] [{PUB}]x ([{DEEP}])"),
    ("colon_port", f"{EVIL}:8080/path"),
    ("userinfo", f"user@{EVIL}"),
    ("two_hosts_glued", f"{EVIL}{PUB}"),
    ("fullwidth_dots", "see " + "evil" + "\uff0e" + "com"),
    ("ideographic_dot", "see " + "evil" + "\u3002" + "com"),
    ("halfwidth_dot", "see " + "evil" + "\uff61" + "com"),
    ("fullwidth_letters", "see " + "\uff45\uff56\uff49\uff4c" + ".com"),
    ("cyrillic_lookalike", "see " + "\u0435vil" + "." + "com"),
    ("greek_lookalike", "see " + "\u03b5vil" + "." + "org"),
    ("unicode_label", "see " + "\u4f8b\u3048" + "." + "com"),
    ("zero_width_in_host", "see " + "ev\u200bil" + "." + "com"),
    ("soft_hyphen_in_host", "see " + "ev\u00adil" + "." + "com"),
    ("html_tag_in_host", "see " + "ev<b>il" + "." + "com"),
    ("newline_after", f"{EVIL}\nnext"),
    ("tab_separated", f"a\t{EVIL}\tb"),
    ("html_entity_lt", f"&lt;{EVIL}&gt;"),
    ("code_then_prose", f"`{EVIL}` and {PUB}"),
    ("shifted_code", f"a ` b\n`{EVIL}` {PUB}"),
    ("double_backtick", f"``{EVIL}`` {PUB}"),
    ("fence_then_prose", f"```\n{EVIL}\n```\n{PUB}"),
    ("unclosed_fence", f"```\n{EVIL}\n{PUB}"),
    ("table_cell", f"| {EVIL} | {PUB} |"),
    ("list_item", f"- {EVIL}\n* {PUB}\n1. {DEEP}"),
    ("heading", f"# {EVIL}"),
    ("blockquote", f"> {EVIL}"),
    ("subdomain_numeric", "see " + "10." + "evil" + "." + "com"),
    ("hyphen_label", "see " + "my-evil-site" + "." + "io"),
    ("trailing_slash_only", f"{EVIL}/"),
    ("query_only", f"?u={EVIL}&v={PUB}"),
    ("slash_before", f"x/{EVIL}"),
    ("slash_before_word", f"see/{EVIL}"),
    ("hyphen_after", f"{EVIL}-x"),
    ("double_dot_before", f"..{EVIL}"),
    ("triple_dot_before", f"...{EVIL}"),
    ("underscores_around", f"_{EVIL}_"),
    ("residue_defanged_label_then_underscore", "docs[.]example" + ".com_x"),
    ("suffix_sh", "run " + "get" + "." + "sh" + " now"),
    ("suffix_zip", "grab " + "evil" + "." + "zip"),
    ("suffix_digital", "see " + "evil" + "." + "digital"),
    ("fence_indented_four", f"    ```\n{EVIL}\n    ```"),
    ("escaped_backticks", f"\\`{EVIL}\\`"),
    ("after_email_placeholder", "a@" + "example" + "." + "org" + " then " + EVIL),
]

# Texts that hold no host: the oracle must not flag them (otherwise it would pass everything by flagging everything).
NOT_HOSTS = [
    "v1.2 and 3.14",
    "file.txt and notes.md",
    "see e.g. this and i.e. that",
    "version 2.0.1",
    "Dr. Smith",
    "end of sentence.Next one",
    "evil.comx",
    "x.commerce",
    "a.b",
    "no dots here",
    "src/app.py and docs/readme.txt",
    "a[0].b and [1] and x[.]y",
    "evil[.]com and docs[.]example[.]com",
]


@pytest.mark.parametrize("text", NOT_HOSTS)
def test_oracle_does_not_flag_a_text_without_a_host(text):
    assert links(text) == []


# The oracle must SEE the host in the raw text of every shape whose host a renderer would read, or the table checks
# nothing. Shapes written so that the raw text has no readable host (encoded, entity, HTML-split, zero width) are
# excluded here: they are checked on the card only.
_RAW_BLIND = {"glued_word_after", "encoded_dot", "entity_dot", "html_tag_in_host", "fullwidth_letters", "cyrillic_lookalike",
              "greek_lookalike", "html_entity_lt", "unicode_label", "zero_width_in_host", "soft_hyphen_in_host"}  # fmt: skip


@pytest.mark.parametrize(("name", "text"), [s for s in SHAPES if s[0] not in _RAW_BLIND])
def test_oracle_sees_the_host_in_the_raw_shape(name, text):
    assert links(text), name


@pytest.mark.parametrize(("name", "text"), SHAPES)
def test_card_has_no_linkable_host(name, text):
    shown = channel.clean(text)
    assert links(shown) == [], f"{name}: {text!r} -> {shown!r}: {links(shown)}"
    # and a second pass over what was shown shows nothing new (a card read again)
    assert links(channel.clean(shown)) == [], f"{name} again: {shown!r}"


def _linkifier():
    """linkify-it-py (a dev dependency; markdown-it's linkifier, NOT the channel's renderer, not Slack). Where it is
    missing the test skips locally, and FAILS when the environment variable HADAVIN_REQUIRE_LINKIFY is set (a skip would hide that the
    agreement was never checked)."""
    try:
        import linkify_it
    except ImportError:
        if os.environ.get("HADAVIN_REQUIRE_LINKIFY"):
            pytest.fail("linkify-it-py is missing and HADAVIN_REQUIRE_LINKIFY is set")
        pytest.skip(
            "linkify-it-py not installed (not declared in pyproject.toml yet: see QUESTIONS.md 16)"
        )
    return linkify_it.LinkifyIt()


def test_oracle_agrees_with_linkify_it_py():
    """The oracle against linkify-it-py on every shape's raw text: whatever that linkifier links, the oracle flags (the
    oracle is the wider one); and it links nothing on a shown card. One recorded run: evidence/G2-p1d-a.md."""
    lf = _linkifier()
    for name, text in SHAPES:
        found = [m.text for m in (lf.match(_strip_placeholders(_without_code(text))) or [])]
        if found:
            assert links(text), (
                f"{name}: linkify-it links {found} in {text!r}, the oracle sees nothing"
            )
    for name, text in SHAPES:
        shown = channel.clean(text)
        assert not (lf.match(_strip_placeholders(_without_code(shown))) or []), f"{name}: {shown!r}"


def test_agreement_test_fails_when_the_linkifier_is_required_and_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "linkify_it", None)  # `import linkify_it` raises ImportError
    monkeypatch.setenv("HADAVIN_REQUIRE_LINKIFY", "true")
    with pytest.raises(pytest.fail.Exception):
        _linkifier()
    monkeypatch.delenv("HADAVIN_REQUIRE_LINKIFY")
    with pytest.raises(pytest.skip.Exception):
        _linkifier()


# The oracle's own code reader (CommonMark): a 4-space-indented line is no fence, an escaped backtick no code marker.
@pytest.mark.parametrize(
    ("text", "seen"),
    [
        (f"```\n{EVIL}\n```", False),
        (f"   ```\n{EVIL}\n   ```", False),
        (f"    ```\n{EVIL}\n    ```", True),
        (f"> ```\n> {EVIL}\n> ```", False),
        (f"- ```\n  {EVIL}\n  ```", False),
        (f"````\n{EVIL}\n```\n{PUB}\n````", False),
        (f"\\`{EVIL}\\`", True),
        (f"`{EVIL}`", False),
    ],
)
def test_oracle_code_reader_follows_commonmark(text, seen):
    assert bool(links(text)) is seen


# The honest-text side of the defanger. Bracket rule: `[` before a host no longer saves it, `a[0].b`, `[1]`, `x[.]y`
# have no host in them. The stated cost of dropping `.`, `/` and `-` from the boundaries: a path whose file name ends in
# a letters-only extension (`src/app.py`) is defanged like `file.txt` already was, and `undefang_text` recovers it.
def test_honest_text_is_unchanged_by_the_bracket_rule():
    for text in ("a[0].b", "[1]", "see [1] and [2]", "v1.2 and 3.14", "version 2.0.1", "Dr. Smith"):
        assert gate.defang_text(text) == text
    assert gate.defang_text("x[.]y") == "x.y"  # the old gate's dot, read back; `y` is no suffix


def test_bracketed_file_name_is_defanged_and_recovered():
    shown = gate.defang_text("[draft.md] and [config.yaml]")
    assert shown == "[draft[.]md] and [config[.]yaml]"
    assert gate.undefang_text(shown) == "[draft.md] and [config.yaml]"


def test_paths_and_file_names_are_over_defanged_and_recovered():
    for plain, shown in (
        ("src/app.py", "src/app[.]py"),
        ("see docs/readme.txt", "see docs/readme[.]txt"),
        ("file.txt", "file[.]txt"),
    ):
        assert gate.defang_text(plain) == shown
        assert gate.undefang_text(shown) == plain


def test_bracketed_non_ascii_host_is_defanged_like_an_unbracketed_one():
    host = "\u00e9." + "x1"  # `_DOMAIN` finds no suffix here, only the non-ASCII rule does
    assert gate.defang_text(host) == "\u00e9[.]x1"
    assert gate.defang_text(f"[{host}]") == "[\u00e9[.]x1]"
