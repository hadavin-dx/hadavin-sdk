"""Mechanical style checks T1 to T10 (portal plan B5.4) on ui_tokens.css and on the rendered fixture pages. They measure only what a test can:
corner radii, resting shadows, heading weight, contrast, number alignment, light/dark parity, status words, headings and labels, focus and hover
states. Calm, hierarchy and spacing are judged by reviewers, not here."""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
import ui_fixtures as fx

from intake import ui

CSS_PATH = Path(ui.__file__).with_name("ui_tokens.css")
CSS = re.sub(r"/\*.*?\*/", "", CSS_PATH.read_text(encoding="utf-8"), flags=re.DOTALL)
PAGES = fx.pages()


# ---------------------------------------------------------------------------------------------- a tiny CSS reader
def _blocks(css: str, media: str | None = None) -> list[tuple[str, dict[str, str], str | None]]:
    out, i = [], 0
    while i < len(css):
        j = css.find("{", i)
        if j < 0:
            break
        sel, depth, k = css[i:j].strip(), 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        body = css[j + 1 : k - 1]
        if sel.startswith("@media"):
            out += _blocks(body, sel)
        elif not sel.startswith("@"):
            decls = {}
            for d in body.split(";"):
                if ":" in d:
                    p, _, v = d.partition(":")
                    decls[p.strip()] = v.strip()
            out.append((sel, decls, media))
        i = k
    return out


BLOCKS = _blocks(CSS)
LIGHT = next(d for s, d, m in BLOCKS if s == ":root" and m is None and "--bg" in d)
DARK = {**LIGHT, **next(d for s, d, m in BLOCKS if s == ":root" and m and "dark" in m)}


def _resolve(value: str, tokens: dict[str, str]) -> str:
    for _ in range(5):
        value = re.sub(r"var\((--[a-z0-9-]+)\)", lambda m: tokens[m.group(1)], value)
    return value


def _lum(hexcolor: str) -> float:
    c = [int(hexcolor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------------------------------------- T1 to T4 on the CSS
def test_t1_border_radii_come_only_from_the_three_sizes():
    seen = 0
    for sel, d, _m in BLOCKS:
        for prop, val in d.items():
            if "radius" in prop and not prop.startswith("--"):
                seen += 1
                assert set(_resolve(val, LIGHT).split()) <= {"8px", "16px", "999px"}, (sel, prop, val)
    assert seen >= 8
    assert {LIGHT["--radius-control"], LIGHT["--radius-card"], LIGHT["--radius-pill"]} == {"8px", "16px", "999px"}


def test_t2_no_shadow_on_resting_elements():
    assert "box-shadow" not in CSS or all((":hover" in s or ":focus-visible" in s) for s, d, _m in BLOCKS if "box-shadow" in d)
    assert not any("shadow" in k for k in LIGHT), "no shadow tokens"


def test_t3_headings_use_weight_400():
    assert LIGHT["--fw-heading"] == "400"
    heads = [(s, d) for s, d, _m in BLOCKS if re.search(r"(^|[\s,>])h[1-4]\s*$", s.split(",")[-1].strip()) or s.startswith("h1")]
    assert heads
    for s, d in heads:
        if "font-weight" in d:
            assert _resolve(d["font-weight"], LIGHT) == "400", s
    others = [(s, d) for s, d, _m in BLOCKS if re.search(r"(^|\s)(strong|b)\b", s)]
    assert not others


PAIRS = [
    ("--ink", "--bg"), ("--ink", "--surface"), ("--ink", "--surface-2"), ("--ink-2", "--bg"), ("--ink-2", "--surface"), ("--ink-2", "--surface-2"),
    ("--ink-3", "--bg"), ("--ink-3", "--surface"), ("--ink-3", "--surface-2"), ("--accent-ink", "--bg"), ("--accent-ink", "--surface"),
    ("--accent-ink", "--accent-wash"), ("--ok-ink", "--ok-wash"), ("--warn-ink", "--warn-wash"), ("--bad-ink", "--bad-wash"),
    ("--neutral-ink", "--neutral-wash"), ("--btn-ink", "--btn-bg"), ("--btn-ink", "--btn-bg-hover"), ("--bad-ink", "--bg"), ("--ok-ink", "--bg"),
    ("--warn-ink", "--bg"), ("--ink", "--accent-wash"),
]  # fmt: skip
UI_PARTS = [
    ("--control-border", "--bg"),
    ("--control-border", "--surface"),
    ("--accent", "--bg"),
    ("--accent", "--surface"),
    ("--ink-3", "--surface"),
]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_t4_contrast_by_the_wcag_formula(theme):
    t = LIGHT if theme == "light" else DARK
    for fg, bg in PAIRS:
        assert contrast(t[fg], t[bg]) >= 4.5, (theme, fg, bg, round(contrast(t[fg], t[bg]), 2))
    for fg, bg in UI_PARTS:
        assert contrast(t[fg], t[bg]) >= 3.0, (theme, fg, bg, round(contrast(t[fg], t[bg]), 2))


def test_t4_the_formula_is_right():
    assert round(contrast("#000000", "#FFFFFF"), 1) == 21.0 and round(contrast("#777777", "#FFFFFF"), 2) == 4.48


def test_t6_dark_has_no_pure_black_and_the_same_token_set_as_light():
    dark_block = next(d for s, d, m in BLOCKS if s == ":root" and m and "dark" in m)
    assert not re.search(r"#0{3}(0{3})?\b|\bblack\b|rgb\(0,? ?0,? ?0\)", " ".join(dark_block.values()), re.I)
    light_only_colours = {k for k, v in LIGHT.items() if v.startswith("#")} - set(dark_block)
    assert not light_only_colours, light_only_colours
    assert set(dark_block) - set(LIGHT) == set()
    for t in (LIGHT, DARK):
        assert not re.search(r"#0{6}\b", " ".join(t.values()))


def test_t6_one_markup_for_both_themes_so_the_same_information_in_light_and_dark():
    s = str(PAGES["04-item-d10-approver"].html)
    assert "prefers-color-scheme: dark" in s and s.count("<html") == 1 and "data-theme" not in s


def test_theme_follows_the_system_only():
    assert "prefers-color-scheme: dark" in CSS and "[data-theme" not in CSS and "cookie" not in CSS.lower()


def test_font_is_the_system_stack_and_no_font_is_fetched():
    assert LIGHT["--font-sans"].startswith("system-ui") and "@font-face" not in CSS and "url(" not in CSS and "@import" not in CSS


# ---------------------------------------------------------------------------------------------- T9, T10 on the CSS
def _selectors() -> list[str]:
    return [p.strip() for s, _d, _m in BLOCKS for p in s.split(",")]


def test_t9_visible_focus_styles_for_links_buttons_summaries_and_row_links():
    sel = _selectors()
    for base in ("a", "button", "summary", ".row-link", "input", "textarea"):
        assert any(s.endswith(":focus-visible") and re.search(rf"(^|[\s,]){re.escape(base)}:focus-visible$", s) for s in sel), base
    ring = next(d for s, d, _m in BLOCKS if "a:focus-visible" in s)
    assert "outline" in ring and "none" not in ring["outline"]
    assert not any(d.get("outline") in ("none", "0") for _s, d, _m in BLOCKS)


def test_t10_hover_and_open_states_exist_for_interactive_components():
    sel = _selectors()
    for base in ("a", "button", "tbody tr", "summary", ".btn", ".row-link"):
        assert any(
            s.endswith(":hover") and (s == base + ":hover" or s.endswith(" " + base + ":hover") or s.endswith("," + base + ":hover"))
            for s in sel
        ), base
    assert any(s.startswith("details[open]") for s in sel)
    assert any("prefers-reduced-motion" in (m or "") for _s, _d, m in BLOCKS)


# ---------------------------------------------------------------------------------------------- T5, T7, T8 on the rendered pages
class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.h1 = 0
        self.pills: list[str] = []
        self.th_no_scope = 0
        self.fields: list[tuple[str, dict, bool]] = []  # (tag, attrs, inside label)
        self.cells: list[tuple[int, dict, str]] = []  # (column, attrs, text)
        self.heads: list[dict] = []
        self.col = 0
        self.cur_text: list[str] = []
        self.cur_pill: list[str] | None = None
        self.in_td = False
        self.ids: list[str] = []
        self.landmarks: set[str] = set()
        self.html_lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append(tag)
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag in ("main", "nav", "aside", "header"):
            self.landmarks.add(tag)
        if tag == "h1":
            self.h1 += 1
        if tag == "th":
            self.heads.append(a)
            if a.get("scope") != "col":
                self.th_no_scope += 1
        if tag == "tr":
            self.col = 0
        if tag == "td":
            self.in_td, self.cur_text, self.cur_attrs = True, [], a
        if tag in ("input", "textarea") and a.get("type") != "hidden":
            self.fields.append((tag, a, "label" in self.stack or "aria-label" in a))
        if "id" in a:
            self.ids.append(a["id"])
        if a.get("class", "").startswith("pill") or " pill" in " " + a.get("class", ""):
            self.cur_pill = []

    def handle_endtag(self, tag):
        if tag == "td":
            self.cells.append((self.col, self.cur_attrs, "".join(self.cur_text).strip()))
            self.col += 1
            self.in_td = False
        if tag == "span" and self.cur_pill is not None:
            self.pills.append("".join(self.cur_pill).strip())
            self.cur_pill = None
        while self.stack and self.stack.pop() != tag:
            pass

    def handle_data(self, data):
        if self.in_td:
            self.cur_text.append(data)
        if self.cur_pill is not None:
            self.cur_pill.append(data)


def dom(name: str) -> Dom:
    d = Dom()
    d.feed(str(PAGES[name].html))
    d.close()
    return d


@pytest.mark.parametrize("name", sorted(PAGES))
def test_t8_one_h1_labelled_fields_table_header_scope_landmarks_and_language(name):
    d = dom(name)
    assert d.h1 == 1 and d.th_no_scope == 0 and d.html_lang == "en"
    assert all(labelled for _t, _a, labelled in d.fields), name
    assert "main" in d.landmarks
    if name != "01-login":
        assert {"nav", "aside", "header"} <= d.landmarks
    assert len(d.ids) == len(set(d.ids))
    assert 'class="skip" href="#main"' in str(PAGES[name].html) and 'id="main"' in str(PAGES[name].html)


@pytest.mark.parametrize("name", sorted(PAGES))
def test_t7_every_status_pill_carries_a_word(name):
    d = dom(name)
    for p in d.pills:
        assert re.search(r"[A-Za-z]{3,}", p), (name, p)
    assert re.search(r"\.pill::before\s*\{[^}]*content", CSS), "the dot is decoration only; the word is in the text"


def test_t5_money_cells_are_numeric_class_with_a_currency_code_and_headers_match():
    money = re.compile(r"^-?[0-9][0-9,]*(\.[0-9]{2})? [A-Z]{3}$")
    for name in ("02-list-after-scan", "08-list-after-decisions", "09-export-preview"):
        d = dom(name)
        heads_num = [i for i, a in enumerate(d.heads) if "num" in a.get("class", "")]
        assert heads_num, name
        for col, attrs, txt in d.cells:
            if col in heads_num:
                assert attrs.get("class") == "num" and money.match(txt), (name, col, txt)
            else:
                assert "num" not in attrs.get("class", ""), (name, col, txt)
    assert re.search(r"\.num\s*\{[^}]*text-align:\s*right[^}]*tabular-nums", CSS)


def test_t5_a_money_cell_never_comes_from_a_float():
    for bad in (1.5, "12", None, True):
        with pytest.raises(TypeError):
            ui.money(bad, "USD")  # type: ignore[arg-type]


def test_rail_marks_the_current_page_and_no_other():
    s = str(PAGES["11-overview"].html).split("</style>", 1)[1]
    assert s.count('aria-current="page"') == 1 and '<a href="/overview" aria-current="page">' in s


def test_overflow_is_handled_by_css_not_by_cutting_text():
    assert re.search(r"\.clip\s*\{[^}]*text-overflow:\s*ellipsis", CSS)
    long = fx.inv_a(supplier="S" * 500)
    assert "S" * 500 in str(ui.render_list(ui.QueueView((long,), ui.ListQuery()), fx.APPROVER).html)


# ---------------------------------------------------------------------------------------------- token drift (set INTAKE_TOKEN_SOURCE)
SHARED = ["--bg", "--surface", "--surface-2", "--border", "--border-strong", "--ink", "--ink-2", "--ink-3", "--btn-bg", "--btn-bg-hover", "--btn-ink",
          "--accent", "--accent-ink", "--accent-wash", "--accent-2"]  # fmt: skip


@pytest.mark.skipif(
    not os.environ.get("INTAKE_TOKEN_SOURCE"), reason="INTAKE_TOKEN_SOURCE (the website style file at the pinned commit) is not set"
)
def test_shared_tokens_equal_the_website_source_in_both_themes():
    src = _blocks(re.sub(r"/\*.*?\*/", "", Path(os.environ["INTAKE_TOKEN_SOURCE"]).read_text(encoding="utf-8"), flags=re.DOTALL))
    web_light = next(d for s, d, _m in src if s.startswith(":root") and "--bg" in d and "light" in s)
    web_dark = next(d for s, d, _m in src if "dark" in s and "--bg" in d)
    for k in SHARED:
        assert LIGHT[k].lower() == web_light[k].lower(), ("light", k)
        assert DARK[k].lower() == web_dark[k].lower(), ("dark", k)
    for k in ("--fw-heading", "--fw-ui", "--radius-control", "--radius-card", "--radius-pill"):
        assert LIGHT[k] == next(d for s, d, _m in src if s == ":root" and k in d)[k], k


def test_shared_tokens_are_present_in_both_themes_even_without_the_source():
    for k in SHARED:
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", LIGHT[k]) and re.fullmatch(r"#[0-9A-Fa-f]{6}", DARK[k]), k


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_bar_tracks_are_visible_against_the_card_in_both_themes(theme):
    tok = LIGHT if theme == "light" else DARK
    tracks = [d["fill"] for s, d, _m in BLOCKS if s in (".meter .track", ".bars .track")]
    assert tracks == ["var(--border-strong)", "var(--border-strong)"]
    assert contrast(tok["--border-strong"], tok["--surface"]) >= 1.4, (theme, contrast(tok["--border-strong"], tok["--surface"]))


def test_filter_chips_are_light_pills_not_buttons_and_nothing_overrides_them():
    rules = [(s, d) for s, d, _m in BLOCKS if re.search(r"(^|[\s,])\.filter($|[\s:\[,])", s)]
    base = next(d for s, d in rules if s == ".filter")
    assert base["border-radius"] == "var(--radius-pill)" and base["padding"] == "2px 12px" and "font-weight" not in base
    # no other rule sets padding or border on a.filter or on every anchor with a higher weight
    for s, d, _m in BLOCKS:
        if s != ".filter" and re.search(r"\bfilter\b", s):
            assert "padding" not in d, s
    out = str(PAGES["02-list-after-scan"].html)
    assert 'class="filter"' in out and 'class="btn" href="/?state' not in out


# ---------------------------------------------------------------------------------------------- long and stacked-mark names (MJ3)
def _decls(selector: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for s, d, _m in BLOCKS:
        if selector in [p.strip() for p in s.split(",")]:
            out.update(d)
    return out


def _class_tags(markup: str) -> dict[str, set[str]]:
    """For every class used on an element of the page: the tag names that carry it."""
    found: dict[str, set[str]] = {}
    for m in re.finditer(r'<([a-z0-9]+)[^>]*\bclass="([^"]+)"', markup.split("</style>", 1)[1]):
        for cls in m.group(2).split():
            found.setdefault(cls, set()).add(m.group(1))
    return found


def test_clip_works_on_the_element_that_carries_it_computed_from_the_css_structure():
    clip = _decls(".clip")
    # an inline element ignores max-width, height and overflow: the rule must make it a box, or the 500-character name widens the table
    tags = set().union(*(_class_tags(str(p.html)).get("clip", set()) for p in PAGES.values()))
    assert tags and tags <= {"a", "span"}, "the clip class is carried by inline elements: the rule must change their display"
    assert clip["display"] in ("inline-block", "block") and clip["vertical-align"] == "bottom"
    assert clip["overflow"] == "hidden" and clip["white-space"] == "nowrap" and clip["text-overflow"] == "ellipsis"
    assert re.fullmatch(r"[0-9.]+ch", clip["max-width"]) and re.fullmatch(r"[0-9.]+em", clip["height"]) and clip["line-height"] == "1.6"
    # the cells that hold it clip too, so a stack of combining marks cannot spill into the row above or below
    for sel in ("td", "dd"):
        d = _decls(sel)
        assert d.get("overflow") == "hidden" and d.get("overflow-wrap") == "anywhere", sel
    # every table cell and every definition value the pages produce is covered by those selectors
    allt = set().union(*(set(re.findall(r"<(td|dd)[ >]", str(p.html).split("</style>", 1)[1])) for p in PAGES.values()))
    assert allt == {"td", "dd"}


ZALGO = "N" + "".join(chr(0x300 + i) for i in range(60)) + "ame" + "".join(chr(0x316 + i) for i in range(40))


def test_hostile_names_keep_the_state_and_flag_cells_in_the_same_row():
    long_ = "S" * 500
    rows = (
        fx.inv_c(supplier=long_, invoice_no="I" * 500),
        fx.inv_b(supplier=ZALGO, invoice_no=ZALGO),
    )
    out = str(ui.render_list(ui.QueueView(rows, ui.ListQuery()), fx.APPROVER).html).split("</style>", 1)[1]
    trs = re.findall(r"<tr>(.*?)</tr>", out.split("<tbody>", 1)[1])
    assert len(trs) == 2
    for tr in trs:
        cells = re.findall(r"<td[ >].*?</td>", tr)
        assert len(cells) == 6 and "pill" in cells[4] and "tag" in cells[5]
        assert re.search(r'class="(row-link )?clip"', cells[0])
    assert "D10" in trs[0] and "D06" in trs[1]


def test_marker_style_exists_and_uses_a_tone_pair_that_passes_contrast():
    mark = _decls(".mark")
    assert mark["background"] == "var(--warn-wash)" and mark["color"] == "var(--warn-ink)"


def test_skip_link_is_hidden_until_focused_and_then_shown():
    base, focus = _decls(".skip"), _decls(".skip:focus-visible")
    assert base["position"] == "absolute" and base["left"] == "-9999px" and "display" not in base
    assert focus["left"] == "8px" and focus["top"] == "8px" and int(focus["z-index"]) > 0
    first = str(PAGES["02-list-after-scan"].html).split("</style>", 1)[1]
    assert first.index('class="skip"') < first.index("<nav") and 'href="#main"' in first and 'id="main"' in first


def test_a_very_long_title_wraps_instead_of_widening_the_page():
    assert _decls("h1").get("overflow-wrap") == "anywhere" and _decls(".top > div:first-child").get("min-width") == "0"


def test_the_title_is_a_clipping_box_so_stacked_marks_cannot_paint_over_banners_and_the_shell():
    h1 = _decls("h1")
    assert h1["overflow"] == "hidden" and h1["overflow-wrap"] == "anywhere" and h1["padding-block"] == ".12em"
    assert _decls("h1")["line-height"] == "1.25"
    # the only untrusted headings are the page title; every page has exactly one h1 inside the clipping rule's reach
    for p in PAGES.values():
        assert str(p.html).split("</style>", 1)[1].count("<h1>") == 1


def test_wide_buttons_may_wrap_on_a_narrow_screen_but_the_sign_out_button_never_wraps():
    narrow = [d for s, d, m in BLOCKS if m and "max-width: 860px" in m and s == "form .primary, form .danger"]
    assert narrow and narrow[0]["white-space"] == "normal" and narrow[0]["max-width"] == "100%"
    assert _decls("button")["white-space"] == "nowrap" and _decls(".btn")["white-space"] == "nowrap"


def test_narrow_screens_wrap_the_header_scroll_the_table_box_and_move_state_and_flags_into_the_first_cell():
    rules: dict[str, dict[str, str]] = {}
    for sel, d, m in BLOCKS:
        if m and "max-width: 860px" in m:
            rules.setdefault(sel, {}).update(d)
    assert (
        rules[".top"]["flex-wrap"] == "wrap"
        and rules[".content"]["padding"].startswith("16px")
        and rules[".rail nav"]["flex-wrap"] == "wrap"
    )
    assert rules[".table-wrap"]["overflow-x"] == "auto" and "table" not in rules
    assert rules[".meta"]["display"] == "none" and rules[".narrow-meta"]["display"] == "block"
    base = [d for sel, d, m in BLOCKS if sel == ".narrow-meta" and m is None]
    assert base and base[0]["display"] == "none"  # hidden on wide screens, where the State and Flags columns show


def test_the_header_banners_and_helper_lines_clip_stacked_marks_and_wrap():
    for sel in (".who", ".banner", ".why"):
        d = _decls(sel)
        assert d.get("overflow") == "hidden" and d.get("overflow-wrap") == "anywhere", sel


def test_the_title_box_has_a_second_layer_a_maximum_height():
    h1 = _decls("h1")
    assert h1["max-height"] == "4.3em" and h1["overflow"] == "hidden"
    assert "table-wrap:focus-visible" in CSS
