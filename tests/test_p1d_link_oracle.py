"""P1d-a review M6: an independent link oracle for approval cards.

The properties in test_p1d_a_paths.py use the defanger's own regexes (`_DOMAIN`, `_DOMAIN_LAST`, `_NON_ASCII_HOST`) as the
oracle, so defanger and oracle share their blind spots (`see/evil.com`, `[evil.com]`, `evil.com-x` match none of them).
This oracle shares no code with `hadavin_sdk`: its own top-level-domain list, its own code-span reader, and a rule that
is wider than a renderer's linkifier (a host is any dotted name ending in a known suffix, found at ANY position, behind
any character, with any dot look-alike). A text that is not linkable by this rule is not linkable by a renderer.
"""

import re
import unicodedata

import pytest

from hadavin_sdk.approvals import channel

# Written here, not imported: an independent list (a superset of the plausible ones plus the internal suffixes).
_SUFFIXES = "com|org|net|io|dev|app|co|us|uk|de|fr|ru|cn|info|biz|edu|gov|ai|me|xyz|cc|tv|sh|internal|corp|local|lan|test|example"
_DOTS = ".\u3002\uff0e\uff61"  # ASCII dot and the three a URL parser maps to it (UTS 46); U+2024 and the like are not dots there
_NAME = r"[^\W_]"  # letters and digits of any script
# A host starts where no name character, dot, hyphen or slash precedes it and ends before a letter, digit, `_` or `-`:
# what markdown-it's linkifier does (checked with linkify-it-py, see the last test): `x/evil.com`, `evil.com-x` and
# `..evil.com` are not linked there, `[evil.com]` and `!!evil.com??` are.
_HOST = re.compile(
    rf"(?<![\w.\-])(?<![\w\-]/){_NAME}(?:[\w-]*{_NAME})?(?:[{re.escape(_DOTS)}]{_NAME}(?:[\w-]*{_NAME})?)*"
    rf"[{re.escape(_DOTS)}](?:{_SUFFIXES})(?![\w-])",
    re.IGNORECASE,
)


def _without_code(text: str) -> str:
    """Own reader: drop closed fences and single-line backtick pairs when every backtick is paired (else keep all)."""
    lines = text.split("\n")
    out, fence = [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            out.append(ln)
    if fence:  # an unclosed fence is not code
        return text
    kept = []
    for ln in out:
        pairs = re.sub(r"`[^`\n]+`", "", ln)
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
]


@pytest.mark.parametrize("text", NOT_HOSTS)
def test_oracle_does_not_flag_a_text_without_a_host(text):
    assert links(text) == []


# The oracle must SEE the host in the raw text of every shape whose host a renderer would read, or the table checks
# nothing. Shapes written so that the raw text has no readable host (encoded, entity, HTML-split, zero width) are
# excluded here: they are checked on the card only.
_RAW_BLIND = {"glued_underscore_before", "glued_word_after", "encoded_dot", "entity_dot", "html_tag_in_host", "fullwidth_letters", "cyrillic_lookalike",
              "greek_lookalike", "html_entity_lt", "unicode_label", "code_then_prose", "shifted_code",
              "double_backtick", "fence_then_prose", "unclosed_fence", "zero_width_in_host", "soft_hyphen_in_host"}  # fmt: skip


@pytest.mark.parametrize(("name", "text"), [s for s in SHAPES if s[0] not in _RAW_BLIND])
def test_oracle_sees_the_host_in_the_raw_shape(name, text):
    assert links(text), name


@pytest.mark.parametrize(("name", "text"), SHAPES)
def test_card_has_no_linkable_host(name, text):
    shown = channel.clean(text)
    assert links(shown) == [], f"{name}: {text!r} -> {shown!r}: {links(shown)}"
    # and a second pass over what was shown shows nothing new (a card read again)
    assert links(channel.clean(shown)) == [], f"{name} again: {shown!r}"


def test_oracle_agrees_with_a_real_linkifier():
    """The oracle against markdown-it's own linkifier (linkify-it-py), on every shape's raw text: whatever that linkifier
    links, the oracle flags (the oracle is the wider one). Skipped where linkify-it-py is not installed."""
    linkify_it = pytest.importorskip("linkify_it")
    lf = linkify_it.LinkifyIt()
    for name, text in SHAPES:
        found = [m.text for m in (lf.match(_strip_placeholders(_without_code(text))) or [])]
        if found:
            assert links(text), (
                f"{name}: linkify-it links {found} in {text!r}, the oracle sees nothing"
            )
    shown_checks = [channel.clean(t) for _, t in SHAPES]
    for (name, _), shown in zip(SHAPES, shown_checks, strict=True):
        assert not (lf.match(_strip_placeholders(_without_code(shown))) or []), f"{name}: {shown!r}"
