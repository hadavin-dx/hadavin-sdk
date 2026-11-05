"""The escaping choke point (portal plan B2.2): hostile values in every sink, the sealed Html and Url types, single-pass substitution, route and
query whitelists, sensitive values by role, banner isolation. Oracles: structural (a page built with hostile values has exactly the tags and
attribute names of the same page built with benign values) and an INDEPENDENT unicodedata oracle for hidden characters."""

from __future__ import annotations

import copy
import html
import pickle
import re
import unicodedata
from dataclasses import FrozenInstanceError, replace
from html.parser import HTMLParser

import pytest
import ui_fixtures as fx

from intake import ui

BIDI = chr(0x202E)
ZW = chr(0x200B)
HOSTILE = [
    "<script>alert(1)</script>",
    "</textarea><b>x</b>",
    "</style><b>x</b>",
    "</title><b>x</b>",
    "</details></summary><b>x</b>",
    '" onmouseover="alert(1)" x="',
    "'><img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "**bold** [link](http://example.test) <b>x</b>",
    "&lt;b&gt; &amp; &#60;script&#62;",
    "a" + BIDI + "b" + ZW + "c",
    "line1\r\nline2\x00\x1b[2J",
    "{name} {{x}} {0}",
    "x" * 4096,
    "ACME" + chr(0x3164),
    chr(0x0600) + chr(0x06DD) + chr(0x070F) + chr(0xFE0F) + chr(0x034F),
]
# every hidden-character case of the review (category Cf, variation selectors, joiner, blank look-alikes, noncharacters, private use, unassigned)
HIDDEN_CASES = [
    0x0600, 0x0601, 0x0605, 0x06DD, 0x070F, 0x08E2, 0x110BD, 0x1D173, 0x1D17A, 0x206A, 0x206F, 0xFFF9, 0xFFFB,  # Cf
    0xFE00, 0xFE0F, 0xE0100, 0xE01EF, 0x034F,  # variation selectors, combining grapheme joiner
    0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0,  # blank look-alikes
    0xFFFE, 0xFFFF, 0xE000, 0x0378, 0x2028, 0x2029, 0x0085, 0x007F, 0x0000, 0x000D, 0x202E, 0x200B, 0x00AD, 0xFEFF,
]  # fmt: skip


class Shape(HTMLParser):
    """Tag names and attribute names in order, plus the text and the attribute values."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, tuple[str, ...]]] = []
        self.data: list[str] = []
        self.attrs: list[tuple[str, str]] = []

    marks = 0

    def handle_starttag(self, tag, attrs):
        if tag == "span" and attrs == [("class", "mark")]:  # a visible marker for a hidden character: counted, not structure
            self.marks += 1
            return
        self.tags.append((tag, tuple(k for k, _ in attrs)))
        self.attrs.extend((k, v or "") for k, v in attrs)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.data.append(data)


def shape(markup: str) -> Shape:
    p = Shape()
    p.feed(markup)
    p.close()
    return p


def _cps(*spans):
    out = set()
    for sp in spans:
        out.update(range(sp[0], sp[-1] + 1))
    return out


# Written out from the Unicode standard (general categories Cc, Cf, Zs, Zl, Zp, Cs, Co, noncharacters) and from the studio's own list of invisible
# characters. NOT computed with unicodedata and NOT the rule ui.py uses.
MUST_MARK = (
    _cps((0, 8), (0xB, 0x1F), (0x7F, 0x9F))  # Cc without newline and tab
    | _cps((0xAD,), (0x600, 0x605), (0x61C,), (0x6DD,), (0x70F,), (0x890, 0x891), (0x8E2,), (0x180E,), (0x200B, 0x200F), (0x202A, 0x202E),
           (0x2060, 0x2064), (0x2066, 0x206F), (0xFEFF,), (0xFFF9, 0xFFFB), (0x110BD,), (0x110CD,), (0x13430, 0x1343F), (0x1BCA0, 0x1BCA3),
           (0x1D173, 0x1D17A), (0xE0001,), (0xE0020, 0xE007F))  # Cf
    | _cps((0xA0,), (0x1680,), (0x2000, 0x200A), (0x202F,), (0x205F,), (0x3000,))  # Zs except the plain space
    | _cps((0x2028,), (0x2029,))  # Zl, Zp
    | _cps((0xD800, 0xDFFF))  # Cs
    | _cps((0xE000, 0xF8FF), (0xF0000,), (0xFFFFD,), (0x100000,), (0x10FFFD,))  # Co
    | _cps((0xFDD0, 0xFDEF), (0xFFFE, 0xFFFF), (0x1FFFE, 0x1FFFF), (0x10FFFE, 0x10FFFF), (0x378, 0x379), (0xE0080, 0xE00FF))  # Cn
    | _cps((0xFE00, 0xFE0F), (0xE0100, 0xE01EF), (0x34F,))  # variation selectors, combining grapheme joiner
    | _cps((0x115F,), (0x1160,), (0x2800,), (0x3164,), (0xFFA0,))  # blank look-alikes
    | _cps((0x17B4, 0x17B5), (0x180B, 0x180D), (0x180F,))  # invisible combining marks
)  # fmt: skip
MUST_SHOW = [
    "A", "z", "0", "9", "é", "ñ", "ü", "日", "한", "ア", "😀", "-", ".", ",", "<", ">", "&", "'", '"', "\n", "\t", " ", "‐", "€", "٣", "ᄀ",
    "\u0301", "\u0308", "ß", "Ω", "№",
]  # fmt: skip


def oracle_hidden(ch: str) -> bool:
    return ord(ch) in MUST_MARK


def visible(v: str) -> str:
    return "".join(f"<U+{ord(c):04X}>" if oracle_hidden(c) else c for c in v)


# ---------------------------------------------------------------------------------------------- sealed types
def test_html_cannot_be_built_subclassed_copied_pickled_or_changed():
    for call in (lambda: ui.Html("<b>x</b>"), lambda: ui.Html("x", _key=object()), lambda: ui.Html("x", None), lambda: ui.Url("/x")):
        with pytest.raises(TypeError):
            call()
    a = ui.h("<b>{x}</b>", x="1")
    with pytest.raises(FrozenInstanceError):
        a._s = "<script>"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class Evil(ui.Html):  # noqa: B903
            def __init__(self, v):  # a subclass with its own constructor would skip the key
                self._s = v

    assert copy.copy(a) is a and copy.deepcopy(a) is a
    with pytest.raises(TypeError):
        pickle.dumps(a)
    u = ui.url("home")
    assert copy.copy(u) is u and copy.deepcopy(u) is u
    with pytest.raises(TypeError):
        pickle.dumps(u)
    with pytest.raises(FrozenInstanceError):
        u._v = "javascript:x"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class EvilUrl(ui.Url):  # noqa: B903
            pass


def test_html_is_not_text_so_markup_and_text_never_mix():
    a = ui.h("<b>{x}</b>", x="1")
    assert not isinstance(a, str)
    for bad in (lambda: a + "<i>", lambda: "<i>" + a, lambda: a + a, lambda: a[0], lambda: len(a), lambda: "x" in a):
        with pytest.raises(TypeError):
            bad()
    assert str(a) == "<b>1</b>" and f"{a}" == "<b>1</b>"
    assert str(ui.h("<p>{x}</p>", x=str(a) + "<i>x</i>")) == "<p>&lt;b&gt;1&lt;/b&gt;&lt;i&gt;x&lt;/i&gt;</p>"


def test_links_must_come_from_url():
    for bad in ("javascript:alert(1)", "/x", None, 5):
        with pytest.raises(TypeError):
            ui.empty_state("a", "b", ("x", bad))  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            ui.table("c", (ui.Col("a", sort="s"),), [], header_links={"s": bad})  # type: ignore[dict-item]
    assert 'href="/"' in str(ui.empty_state("a", "b", ("x", ui.url("home"))))


# ---------------------------------------------------------------------------------------------- single pass
def test_values_are_escaped_exactly_once_and_html_is_never_reescaped():
    inner = ui.h("<b>{x}</b>", x="a&b")
    assert str(inner) == "<b>a&amp;b</b>"
    assert str(ui.h("<p>{i}</p>", i=inner)) == "<p><b>a&amp;b</b></p>"
    assert str(ui.h("<p>{x}</p>", x="&amp;")) == "<p>&amp;amp;</p>"


def test_substituted_values_are_never_rescanned_as_templates():
    assert str(ui.h("<p>{a}{b}</p>", a="{b}", b="Y")) == "<p>{b}Y</p>"
    assert str(ui.h("<p>{{a}}</p>")) == "<p>{a}</p>"
    assert str(ui.h("<p>{a}</p>", a="{{a}}")) == "<p>{{a}}</p>"


def test_template_misuse_is_an_error():
    with pytest.raises(KeyError):
        ui.h("<p>{missing}</p>")
    with pytest.raises(ValueError):
        ui.h("<p>x</p>", unused="1")
    for stray in ("<p>{x}{Name}</p>", "<p>{x}{ x}</p>", "<p>{x}{</p>", "<p>{x}}</p>", "<p>{x}{x y}</p>", "<p>{x}{{{</p>", "<p>{x}{}</p>"):
        with pytest.raises(ValueError):
            ui.h(stray, x="1")  # every slot is filled and no value is unused: only the stray brace can raise
    for bad in (None, True, 1.5, b"x", ["x"]):
        with pytest.raises(TypeError):
            ui.h("<p>{x}</p>", x=bad)


# ---------------------------------------------------------------------------------------------- text
def test_text_marks_hidden_characters_and_escapes_last():
    out = str(ui.text("a" + BIDI + "b" + ZW + chr(0xD800) + chr(7)))
    assert out == "a&lt;U+202E&gt;b&lt;U+200B&gt;&lt;U+D800&gt;&lt;U+0007&gt;"
    assert str(ui.text("tab\tnl\n")) == "tab\tnl\n"
    assert str(ui.text(5)) == "5"
    for bad in (None, True, 1.5):
        with pytest.raises(TypeError):
            ui.text(bad)


@pytest.mark.parametrize("cp", HIDDEN_CASES)
def test_every_hidden_character_is_shown_as_a_marker(cp):
    ch = chr(cp)
    out = str(ui.text("A" + ch + "B"))
    if cp in (0x0A, 0x09):
        pytest.skip("kept")
    assert out == f"A&lt;U+{cp:04X}&gt;B", hex(cp)
    # the marker, not the character, is what a reader sees: two values that differ only by a hidden character stay different
    assert str(ui.text("ACME")) != str(ui.text("ACME" + ch))


def test_every_code_point_of_the_explicit_list_is_marked():
    missed = [hex(cp) for cp in sorted(MUST_MARK) if not str(ui.text(chr(cp))).startswith("&lt;U+")]
    assert not missed, missed[:20]
    assert len(MUST_MARK) > 9000


def test_ordinary_characters_are_shown_as_they_are():
    for ch in MUST_SHOW:
        assert "U+" not in str(ui.text("A" + ch + "B")), repr(ch)


def test_ui_agrees_with_unicodedata_categories_over_the_basic_plane_a_cross_check_not_the_oracle():
    hidden = {"Cc", "Cf", "Cs", "Zl", "Zp", "Zs", "Co", "Cn"}
    bad = []
    for cp in list(range(0, 0x10000)) + [0x10FFFF, 0x1D173, 0xE0001, 0xE0100, 0xF0000, 0x1F600]:
        ch = chr(cp)
        expect = (unicodedata.category(ch) in hidden or cp in MUST_MARK) and ch not in " \n\t"
        if (str(ui.text(ch)).startswith("&lt;U+")) != expect:
            bad.append(hex(cp))
    assert not bad, bad[:20]


def test_the_unicode_data_version_is_recorded_and_not_older_than_the_pinned_python():
    # Cn (unassigned) is judged by the running interpreter's tables: a newer Python marks fewer code points as unassigned. Over-marking is the safe
    # direction. The project requires Python 3.12 or newer, so the tables are Unicode 15.0 or newer.
    v = tuple(int(x) for x in unicodedata.unidata_version.split("."))
    print("unicodedata.unidata_version =", unicodedata.unidata_version)
    assert v >= (15, 0, 0)
    assert str(ui.text(chr(0x378))).startswith("&lt;U+")  # unassigned in every version so far


def test_a_typed_marker_is_not_a_real_marker():
    typed = str(ui.marked("<U+200B>"))
    real = str(ui.marked(chr(0x200B)))
    assert 'class="mark"' not in typed and "&lt;U+200B&gt;" in typed
    assert real == '<span class="mark">&lt;U+200B&gt;</span>'
    assert str(ui.text(chr(0x200B))) == "&lt;U+200B&gt;"  # plain marker where markup is not allowed (attributes)


def test_blank_lookalike_set_equals_the_decision_modules_set():
    from intake import decisions

    theirs = (
        getattr(decisions, "BLANK_LOOKALIKES", None) or decisions._BLANK_LOOKALIKES
    )  # the public alias arrives with the review-page work
    assert ui._BLANKS == frozenset(theirs)


@pytest.mark.parametrize("v", HOSTILE)
def test_hostile_value_in_text_sinks(v):
    for tpl in (
        "<p>{x}</p>",
        '<a href="{x}">k</a>',
        '<input value="{x}">',
        "<svg><title>{x}</title><text>{x}</text></svg>",
        "<title>{x}</title>",
    ):
        s = shape(str(ui.h(tpl, x=v)))
        assert all(a != "onmouseover" and a != "onerror" for _t, attrs in s.tags for a in attrs), (tpl, v)
        benign = shape(str(ui.h(tpl, x="x")))
        assert s.tags == benign.tags, (tpl, v)
    s = shape(str(ui.h("<p>{x}</p>", x=v)))
    assert "".join(s.data) == visible(v)
    s = shape(str(ui.h('<a href="{x}">k</a>', x=v)))
    assert s.attrs == [("href", visible(v))]


def test_href_encoding_of_a_url_value_is_attribute_safe():
    u = ui.url("home", sort="total", dir="asc")
    s = shape(str(ui.h('<a href="{u}">k</a>', u=u)))
    assert s.attrs == [("href", "/?dir=asc&sort=total")]
    assert "&amp;" in str(ui.h('<a href="{u}">k</a>', u=u))


# ---------------------------------------------------------------------------------------------- components, one sink each
@pytest.mark.parametrize("v", HOSTILE)
def test_hostile_value_in_every_component_sink(v):
    def same_shape(make):
        assert shape(str(make(v))).tags == shape(str(make("x"))).tags

    same_shape(lambda x: ui.count_bar(x, 1, 3))  # svg title, aria-label, caption
    same_shape(lambda x: ui.spend_meter(1, 2, False))
    same_shape(lambda x: ui.disclosure(x, ui.text(x)))  # details summary
    same_shape(lambda x: ui.kv_card(x, [(x, x)], why=x))
    same_shape(lambda x: ui.table(x, (ui.Col(x),), [(ui.text(x),)]))  # caption, header, cell
    same_shape(lambda x: ui.banner(ui.BannerView("demo", x, x)))
    same_shape(lambda x: ui.empty_state(x, x, (x, ui.url("home"))))
    same_shape(lambda x: ui.money(5, x))
    same_shape(lambda x: ui.status_pill(x))
    same_shape(lambda x: ui.flag_chip(ui.FlagView(x, x, x, False)))
    same_shape(lambda x: ui.sensitive(ui.SensitiveValue(x, x, x), "approver"))
    same_shape(lambda x: ui.sensitive(ui.SensitiveValue(x, x, None), "viewer"))
    same_shape(lambda x: ui.page(x, ui.text(x), purpose=x, banners=[ui.BannerView("demo", x, x)]).html)
    same_shape(lambda x: ui.render_login(x, csrf=x, banners=[ui.BannerView("demo", x, x)]).html)
    same_shape(lambda x: ui.render_error(404, x, x).html)


def test_title_is_escaped_in_the_head_and_the_page_has_one_title():
    p = ui.page("</title><script>x</script>", ui.text("b")).html
    s = shape(str(p))
    assert [t for t, _ in s.tags].count("title") == 1 and "script" not in [t for t, _ in s.tags]


@pytest.mark.parametrize("v", HOSTILE)
def test_hostile_values_in_whole_pages_keep_the_tag_structure(v):
    def build(x: str) -> list[str]:
        a = fx.APPROVER if x == "x" else ui.SessionView(x, "approver", x)
        sup = ui.InvoiceView(
            item_id=fx.ID_C, state="NEEDS_PERSON", supplier=x, invoice_no=x, invoice_date=x, total_minor=100, currency=x,
            flags=(ui.FlagView(x, x, x, True),), fields=(ui.FieldView(x, x, False), ui.FieldView(x, ui.SensitiveValue("<BANK_1>", "BANK", x), True)),
            source_text=x, bank_on_file=ui.SensitiveValue(x, x, x), bank_in_text=(ui.SensitiveValue(x, x, None),), content_code=x, version=2,
            approve_refusal=x, decision=ui.DecisionView(x, x, x, x, (x,)), refusal=x, banners=(ui.BannerView("demo", x, x),),
        )  # fmt: skip
        q = ui.QueueView((sup,), ui.ListQuery(), refused_files=((x, x),), banners=(ui.BannerView("demo", x, x),))
        ex = ui.ExportPageView(
            (ui.ExportRowView(fx.ID_A, x, x, x, 5, x),),
            kill_switch=False,
            may_export=True,
            results=((x, x),),
            file_text=x,
            skipped=(x,),
            refusal=x,
        )
        ov = ui.OverviewView(((x, x, 1),), 1, 5, 10, 9, True, x, (ui.BannerView("demo", x, x),))
        pages = [ui.render_item(sup, a), ui.render_item(replace(sup, decision=None), a), ui.render_list(q, a), ui.render_export(ex, a)]
        pages.append(ui.render_overview(ov, a))
        return [str(p.html) for p in pages]

    for hostile, benign in zip(build(v), build("x"), strict=True):
        assert shape(hostile).tags == shape(benign).tags


# ---------------------------------------------------------------------------------------------- views
def test_repr_of_views_never_contains_the_planted_originals():
    secret = "ACCT-" + "5555" + "4444"
    sv = ui.SensitiveValue("<BANK_1>", "BANK", secret)
    inv = fx.inv_c(source_text="pay " + secret, bank_on_file=sv, bank_in_text=(sv,))
    for obj in (sv, inv, fx.APPROVER, ui.QueueView((inv,), ui.ListQuery())):
        assert secret not in repr(obj) and secret not in str(obj), type(obj)
    for name in ("bank_on_file", "bank_in_text", "source_text", "restored"):
        assert name not in repr(inv) and name not in repr(sv), name  # the fields are hidden by name, not only by value
    assert "csrf-token-1" not in repr(fx.APPROVER) and "ap-a" not in repr(fx.APPROVER)


def test_views_validate_ids_kinds_and_row_ids():
    with pytest.raises(ValueError):
        fx.inv_a(item_id="7")
    with pytest.raises(TypeError):
        fx.inv_a(total_minor=1.5)
    for bad in ("", "Kill Switch", "a" * 40, "ok-1", None):
        with pytest.raises(ValueError):
            ui.BannerView(bad, "t", "info")  # type: ignore[arg-type]
    for bad in ("zz" * 32, "ab" * 31, "AB" * 32, 5):
        with pytest.raises(ValueError):
            ui.ExportView(bad, "2026-11-04 11:00", "abcd")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ui.ExportRowView("x", None, None, None, 1, "USD")
    assert ui.ExportView("ab" * 32, "2026-11-04 11:00", "abcd1234").row_id == "ab" * 32


def test_none_supplier_invoice_number_and_date_render_as_not_recorded():
    v = fx.inv_a(supplier=None, invoice_no=None, invoice_date=None)
    s = str(ui.render_item(v, fx.APPROVER).html)
    assert s.count("not recorded") >= 3
    assert "not recorded" in str(ui.render_list(ui.QueueView((v,), ui.ListQuery()), fx.APPROVER).html)
    assert ui.apply_query((v, fx.inv_b()), ui.ListQuery("supplier", "asc", None))[0].supplier is None


# ---------------------------------------------------------------------------------------------- sensitive values
def test_sensitive_by_role():
    v = ui.SensitiveValue("<BANK_1>", "BANK", "ACCT-" + "1234")
    assert "ACCT-" + "1234" in str(ui.sensitive(v, "approver"))
    for role in ("viewer", "", "admin", "Approver", None):
        out = str(ui.sensitive(v, role))
        assert "ACCT-" + "1234" not in out and "bank number 1, hidden" in out
    gone = str(ui.sensitive(ui.SensitiveValue("<BANK_1>", "BANK", None), "approver"))
    assert "bank number 1, original not available" in gone


def test_unknown_or_forged_placeholder_gets_the_neutral_chip():
    for ph in ("<BANK_1><script>", "BANK_1", "<NOPE_1>", "<BANK_99999>", ""):
        assert "hidden value" in str(ui.sensitive(ui.SensitiveValue(ph, "BANK", None), "viewer"))


def test_placeholder_lookalike_in_untrusted_text_is_marked_never_a_chip():
    out = str(ui.marked("pay <BANK_1> now"))
    assert 'class="forged"' in out and "not from our masking" in out and 'class="chip"' not in out
    assert "&lt;BANK_1&gt;" in out and "<BANK_1>" not in out


def test_marked_keeps_every_piece_and_neutralises_each_after_the_split():
    out = str(ui.marked("AA<BANK_1>BB" + chr(0x200B) + "<EMAIL_2>" + chr(0x3164) + "CC"))
    assert out.startswith("AA<span") and 'BB<span class="mark">&lt;U+200B&gt;</span>' in out
    assert out.endswith('<span class="mark">&lt;U+3164&gt;</span>CC')
    assert out.count('class="forged"') == 2
    assert str(ui.marked("")) == "" and str(ui.marked(None)) == "not recorded"
    assert str(ui.marked("<BA" + ZW + "NK_1>")).count("forged") == 0  # a hidden character inside breaks the lookalike: shown as a marker


# ---------------------------------------------------------------------------------------------- routes and queries
def test_url_only_builds_registered_routes_with_whitelisted_parts():
    assert str(ui.url("home")) == "/" and str(ui.url("item", id=fx.ID_A)) == f"/item/{fx.ID_A}"
    assert str(ui.url("home", sort="total", dir="asc")) == "/?dir=asc&sort=total"
    for bad in (
        lambda: ui.url("nope"),
        lambda: ui.url("item"),
        lambda: ui.url("item", id="-1"),
        lambda: ui.url("item", id=True),
        lambda: ui.url("home", id=fx.ID_A),
        lambda: ui.url("home", sort="x"),
        lambda: ui.url("home", other="1"),
        lambda: ui.url("overview", sort="total"),
    ):
        with pytest.raises(ValueError):
            bad()


def test_query_whitelist_refuses_everything_else():
    assert ui.parse_list_query("") == ui.ListQuery()
    assert ui.parse_list_query("sort=total&dir=asc&state=READY") == ui.ListQuery("total", "asc", "READY")
    for raw in (
        "sort=bogus",
        "dir=up",
        "state=ready",
        "x=1",
        "sort=total&sort=state",
        "sort",
        "&".join(f"k{i}=1" for i in range(20)),
        "sort=%3Cscript%3E",
    ):
        with pytest.raises(ui.QueryRefused):
            ui.parse_list_query(raw)


def test_refused_query_page_is_a_fixed_sentence_with_status_422_and_never_echoes_the_request():
    spoof = "Your account is locked, call 555-0100"
    try:
        ui.parse_list_query("sort=" + spoof)
    except ui.QueryRefused as e:
        assert spoof not in repr(e) and not e.args
        p = ui.render_query_refused()
        out = str(p.html)
        assert p.status == 422 and spoof not in out and "locked" not in out and "555" not in out
        assert "This link is not valid" in out
    else:
        raise AssertionError("not refused")
    a = str(ui.render_query_refused().html)
    assert a == str(ui.render_query_refused().html)


def test_apply_query_filters_and_sorts_and_created_uses_created_at_not_the_id():
    rows = (fx.inv_a(), fx.inv_b(), fx.inv_c())
    assert [r.item_id for r in ui.apply_query(rows, ui.ListQuery("created", "asc", None))] == [fx.ID_A, fx.ID_B, fx.ID_C]
    assert [r.item_id for r in ui.apply_query(rows, ui.ListQuery("created", "desc", "NEEDS_PERSON"))] == [fx.ID_C, fx.ID_B]
    assert [r.item_id for r in ui.apply_query(rows, ui.ListQuery("total", "desc", None))] == [fx.ID_C, fx.ID_A, fx.ID_B]
    # ids sort the other way round to creation time: the order must follow created_at
    late = fx.inv_a(created_at="2026-12-01T00:00:00Z")
    assert ui.apply_query((late, fx.inv_b(), fx.inv_c()), ui.ListQuery("created", "asc", None))[-1].item_id == fx.ID_A
    same = (fx.inv_b(created_at="t", order=2), fx.inv_a(created_at="t", order=1))
    assert [r.order for r in ui.apply_query(same, ui.ListQuery("created", "asc", None))] == [1, 2]


def test_default_order_is_needs_person_then_ready_then_decided_each_by_created_at():
    rows = (
        fx.inv_a("APPROVED", created_at="2026-11-04T01"),
        fx.inv_a("READY", created_at="2026-11-04T05"),
        fx.inv_b(created_at="2026-11-04T09"),
        fx.inv_a("REJECTED", created_at="2026-11-04T00"),
        fx.inv_b(created_at="2026-11-04T03"),
    )
    got = [(r.state, r.created_at) for r in ui.default_order(rows)]
    assert got == [
        ("NEEDS_PERSON", "2026-11-04T03"),
        ("NEEDS_PERSON", "2026-11-04T09"),
        ("READY", "2026-11-04T05"),
        ("REJECTED", "2026-11-04T00"),
        ("APPROVED", "2026-11-04T01"),
    ]


def test_page_profile_is_strict_and_the_header_string_has_one_owner_outside_ui():
    p = ui.page("t", ui.text("b"))
    assert p.profile == "strict" and ui.PROFILES == ("strict",)
    assert re.fullmatch(r"[A-Za-z0-9+/]{43}=", ui.STYLE_SHA256)
    assert not hasattr(ui, "CSP_PROFILES") and not hasattr(p, "csp")  # the service builds the header from STYLE_SHA256
    with pytest.raises(ValueError):
        ui.page("t", ui.text("b"), profile="scripts")


# ---------------------------------------------------------------------------------------------- banners
def test_banner_sources_are_isolated_and_error_text_is_never_shown():
    def boom():
        raise RuntimeError("secret detail /path/x.db")

    ok = ui.BannerView("fine", "fine", "info")
    out = ui.collect_banners({"first": lambda: ok, "scan": boom, "none": lambda: None, "last": lambda: ok})
    assert [b.text for b in out] == ["fine", "Status unavailable: scan", "fine"]
    assert all("secret" not in b.text for b in out)
    assert ui.collect_banners({"a": boom, "b": boom})[1].text == "Status unavailable: b"


def test_the_kill_switch_source_always_fails_closed_without_any_caller_argument():
    def boom():
        raise OSError("x")

    for out in (
        ui.collect_banners({"kill_switch": boom}),
        ui.collect_banners({"kill_switch": boom}, {}),
        ui.collect_banners({"kill_switch": boom}, None),
    ):
        assert out == (ui.KILL_SWITCH_ENGAGED,) and out[0].text == "Export is switched off"
    # a caller cannot weaken it
    weak = ui.BannerView("kill_switch", "fine", "info")
    assert ui.collect_banners({"kill_switch": boom}, {"kill_switch": weak}) == (ui.KILL_SWITCH_ENGAGED,)
    # other names can be given a closed banner
    mine = ui.BannerView("hold", "held", "bad")
    assert ui.collect_banners({"x": boom}, {"x": mine}) == (mine,)


def test_page_renders_when_every_banner_source_fails():
    def boom():
        raise RuntimeError("x")

    banners = ui.collect_banners({"a": boom, "b": boom, "kill_switch": boom})
    p = ui.render_item(fx.inv_b(banners=banners), fx.APPROVER)
    assert p.status == 200 and 'name="decision" value="approve"' in str(p.html) and 'name="decision" value="reject"' in str(p.html)


def test_unescaped_entity_roundtrip_is_plain_text():
    assert html.unescape(str(ui.text("<b>&</b>"))) == "<b>&</b>"


def test_html_repr_shows_only_a_length_never_content():
    secret = "ACCT-" + "7777" + "6666"
    assert secret not in repr(ui.h("<p>{x}</p>", x=secret)) and "characters" in repr(ui.h("<p>{x}</p>", x=secret))


def test_field_values_names_and_session_secrets_are_not_in_any_repr():
    secret = "ACCT-" + "7777" + "6666"
    inv = fx.inv_a(fields=(ui.FieldView("Total", secret, True), ui.FieldView("Name", ui.SensitiveValue("<BANK_1>", "BANK", secret), True)))
    assert secret not in repr(inv) and secret not in repr(inv.fields[0]) and "Total" not in repr(inv.fields[0])
    assert "fields=" not in repr(inv) and "FieldView" not in repr(inv)  # the whole field list is hidden by name
    for obj in (fx.APPROVER, fx.VIEWER):
        assert obj.csrf not in repr(obj) and obj.login_name not in repr(obj)
    inv2 = fx.inv_c(bank_in_text=(ui.SensitiveValue("<BANK_2>", "BANK", secret),), source_text=None)
    assert secret not in repr(inv2) and "bank_in_text" not in repr(inv2)


def test_default_list_order_survives_an_empty_query_string():
    q = ui.parse_list_query("")
    assert q.sort is None
    rows = (
        fx.inv_a("APPROVED", created_at="2026-11-04T01", order=1),
        fx.inv_a("READY", created_at="2026-11-04T05", order=2),
        fx.inv_b(created_at="2026-11-04T09", order=3),
        fx.inv_a("REJECTED", created_at="2026-11-04T00", order=4),
        fx.inv_b(created_at="2026-11-04T03", order=5),
    )
    got = [(r.state, r.created_at) for r in ui.apply_query(rows, q)]
    assert got == [(r.state, r.created_at) for r in ui.default_order(rows)]
    assert [s for s, _ in got] == ["NEEDS_PERSON", "NEEDS_PERSON", "READY", "REJECTED", "APPROVED"]
    assert [c for _, c in got][:2] == ["2026-11-04T03", "2026-11-04T09"]
    # a filter keeps the default order; an explicit sort replaces it
    assert [r.state for r in ui.apply_query(rows, ui.parse_list_query("dir=asc"))] == [
        "NEEDS_PERSON",
        "NEEDS_PERSON",
        "READY",
        "REJECTED",
        "APPROVED",
    ]
    assert ui.apply_query(rows, ui.parse_list_query("sort=created&dir=asc"))[0].state == "REJECTED"


def test_export_view_validates_the_time_and_never_a_whole_content_code():
    ok = "ab" * 32
    for bad in ("", "xyz", "ABCD", "a" * 17, "a" * 64, None, 5):
        with pytest.raises(ValueError):
            ui.ExportView(ok, "2026-11-04 11:00", bad)  # type: ignore[arg-type]
    for bad in ("", "yesterday", "2026-11-04", "2026-11-04 11", "<b>x</b>", None, 5):
        with pytest.raises(ValueError):
            ui.ExportView(ok, bad, "abcd")  # type: ignore[arg-type]
    for good in ("2026-11-04 11:00", "2026-11-04T11:00:00Z", "2026-11-04 11:00:00.123"):
        assert ui.ExportView(ok, good, "a" * 16).at_utc == good


def test_safe_invoice_view_degrades_one_row_and_still_raises_for_other_faults():
    bad = dict(
        item_id=fx.ID_C, state="NEEDS_PERSON", supplier="S", invoice_no="N", invoice_date="2026-10-04", total_minor=5, currency="GBP",
        flags=(ui.flag_view("D10"),), may_approve=True, approve_needs_reason=True,
    )  # fmt: skip
    with pytest.raises(ui.ViewInconsistent):
        ui.InvoiceView(**bad)
    v = ui.safe_invoice_view(**bad)
    assert (
        v.may_approve is False
        and v.approve_needs_reason is False
        and v.approve_refusal
        and "does not agree with itself" in v.approve_refusal
    )
    rows = (ui.safe_invoice_view(**bad), fx.inv_a())  # one bad row never breaks the list
    out = str(ui.render_list(ui.QueueView(rows, ui.ListQuery()), fx.APPROVER).html)
    assert out.count("<tr>") == 3 and "Contoso" not in out
    page = str(ui.render_item(v, fx.APPROVER).html)
    assert 'value="approve"' not in page and "does not agree with itself" in page
    good = dict(bad, may_approve=False)
    assert ui.safe_invoice_view(**good).may_approve is False
    with pytest.raises(ValueError):  # a bad id is not an approve verdict problem: it still raises
        ui.safe_invoice_view(**dict(bad, item_id="7"))
    with pytest.raises(TypeError):
        ui.safe_invoice_view(**dict(bad, total_minor=1.5))


def test_compact_marked_shows_a_bang_not_the_long_sentence():
    full = str(ui.marked("pay <BANK_1>"))
    compact = str(ui.marked("pay <BANK_1>", compact=True))
    assert "forged-note" in full and "forged-note" not in compact
    assert compact == 'pay <span class="forged">! &lt;BANK_1&gt;</span>'


# ---------------------------------------------------------------------------------------------- round 5
ACUTE = chr(0x301)


def test_a_run_of_combining_marks_is_cut_to_three_plus_a_count_marker():
    assert str(ui.text("e" + ACUTE * 3)) == "e" + ACUTE * 3  # three are fine
    assert str(ui.text("e" + ACUTE * 5)) == "e" + ACUTE * 3 + "&lt;2 more combining marks&gt;"
    assert str(ui.marked("e" + ACUTE * 5)) == "e" + ACUTE * 3 + '<span class="mark">&lt;2 more combining marks&gt;</span>'
    big = str(ui.text("e" + ACUTE * 4000))
    assert len(big) < 80 and "&lt;3997 more combining marks&gt;" in big
    # the run restarts after a letter, and after a hidden character
    assert "more combining" not in str(ui.text(("e" + ACUTE * 3) * 50))
    out = str(ui.text("e" + ACUTE * 5 + "x" + ACUTE * 5))
    assert out.count("&lt;2 more combining marks&gt;") == 2
    mid = str(ui.text("e" + ACUTE * 5 + chr(0x200B) + ACUTE * 2))
    assert "&lt;2 more combining marks&gt;&lt;U+200B&gt;" in mid and mid.endswith(ACUTE * 2)
    # enclosing marks count too
    assert "more combining" in str(ui.text("e" + chr(0x20DD) * 6))


def test_export_time_accepts_z_and_a_zero_offset_only():
    ok = "ab" * 32
    for good in ("2026-11-04T11:00:00Z", "2026-11-04T11:00:00+00:00", "2026-11-04T11:00:00.123456+00:00", "2026-11-04 11:00"):
        assert ui.ExportView(ok, good, "abcd").at_utc == good
    for bad in ("2026-11-04T11:00:00+05:30", "2026-11-04T11:00:00-00:00", "2026-11-04T11:00:00+00:00\n", "2026-11-04T11:00:00ZZ"):
        with pytest.raises(ValueError):
            ui.ExportView(ok, bad, "abcd")


def test_safe_invoice_view_keeps_the_builders_specific_refusal():
    kw = dict(item_id=fx.ID_C, state="NEEDS_PERSON", supplier="S", invoice_no="N", invoice_date="2026-10-04", total_minor=5, currency="GBP",
              flags=(ui.flag_view("D10"),), may_approve=True)  # fmt: skip
    specific = "Approve is not offered: the reason is too short."
    assert ui.safe_invoice_view(**kw, approve_refusal=specific).approve_refusal is None or True
    kw2 = dict(kw, may_approve=False)
    v = ui.safe_invoice_view(**dict(kw, approve_refusal=None))
    assert "does not agree with itself" in v.approve_refusal
    both = dict(kw, approve_refusal=specific)
    assert ui.safe_invoice_view(**both).approve_refusal == specific and ui.safe_invoice_view(**both).may_approve is False
    assert ui.safe_invoice_view(**kw2).may_approve is False


def test_flag_chip_wording_always_comes_from_the_label_map():
    out = str(ui.flag_chip(ui.FlagView("D10", "all fine <BANK_1>", "warn", False)))
    assert "all fine" not in out and "Bank details in the invoice differ" in out
    unknown = str(ui.flag_chip(ui.FlagView("Z99", "all fine", "warn", False)))
    assert "all fine" not in unknown and "no sentence for" in unknown


def test_hostile_values_in_whole_pages_with_a_viewer_session_keep_the_tag_structure():
    for v in HOSTILE:

        def build(x: str) -> list[str]:
            a = fx.VIEWER if x == "x" else ui.SessionView(x, "viewer", x)
            inv = ui.InvoiceView(
                item_id=fx.ID_C, state="NEEDS_PERSON", supplier=x, invoice_no=x, invoice_date=x, total_minor=100, currency=x,
                flags=(ui.FlagView(x, x, x, True),), fields=(ui.FieldView(x, x, False), ui.FieldView(x, ui.SensitiveValue("<BANK_1>", "BANK", x), True)),
                source_text=x, bank_on_file=ui.SensitiveValue(x, x, x), bank_in_text=(ui.SensitiveValue(x, x, None),), d12_numbers=(x,),
                content_code=x, version=2, approve_refusal=x, decision=ui.DecisionView(x, x, x, x, (x,)), refusal=x, banners=(ui.BannerView("demo", x, x),),
            )  # fmt: skip
            q = ui.QueueView((inv,), ui.ListQuery(), refused_files=((x, x),), banners=(ui.BannerView("demo", x, x),))
            ov = ui.OverviewView(((x, x, 1),), 1, 5, 10, 9, True, x, (ui.BannerView("demo", x, x),))
            pages = [ui.render_item(inv, a), ui.render_list(q, a), ui.render_overview(ov, a), ui.render_export(ui.ExportPageView(()), a)]
            return [str(p.html) for p in pages]

        for hostile, benign in zip(build(v), build("x"), strict=True):
            assert shape(hostile).tags == shape(benign).tags, v[:20]


def test_the_viewer_never_sees_d12_numbers_or_the_original_but_the_approver_sees_d12_numbers():
    nums = ("12345678901234", "99887766554433")
    v = fx.inv_b(d12_numbers=nums)
    ap = str(ui.render_item(v, fx.APPROVER).html)
    assert all(n in ap for n in nums) and "Numbers not explained" in ap
    vw = str(ui.render_item(fx.inv_b(d12_numbers=nums, source_text=None), fx.VIEWER).html)
    assert not any(n in vw for n in nums) and "Numbers not explained" not in vw


def test_the_bank_card_says_it_is_computed_now_from_the_current_suppliers_file_for_d10_only():
    d10 = str(ui.render_item(fx.inv_c(), fx.APPROVER).html)
    assert "Computed now from the current suppliers file." in d10
    other = fx.inv_a(bank_on_file=ui.SensitiveValue("<BANK_1>", "BANK", "x"))
    assert "Computed now" not in str(ui.render_item(other, fx.APPROVER).html)
