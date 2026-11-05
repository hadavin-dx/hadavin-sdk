"""Mutation runner for src/intake/invoicecheck.py (it lives under tests/ because it needs sys.modules and importlib, which the capability scan of tools/ refuses): breaks one rule at a time and checks that tests/test_invoicecheck.py or tests/test_invoicecheck_round5.py fails.

Run from the repository root:  python tests/mutation_runner/mutate_invoicecheck.py [--only SUBSTRING[,SUBSTRING...]] [--sample N] [--random K --seed S]
Prints one line per mutant with the TEST that killed it:
  KILLED     name :: first failing test           (an assertion failed under the change)
  SURVIVED   name :: pytest summary               (no test noticed the change; exit code 1)
  CRASH      name :: why                          (the changed module could not be built or the test run broke: proves nothing)
  COLLECTION name :: why                          (the test file could not be collected under the change: proves nothing)
After the loop the unchanged module is run once more (`restore proof`). Mutants run in this process: the changed source goes to a
temporary folder and is imported from there (no subprocess, no exec); the repository file is never written.
Table mutants (one confusables entry, one ISO country, one look-alike letter) are SAMPLED with --sample N (default 24 of each table);
constants that are caps above what a candidate can ever need (IBAN_KW_TOKENS) are mutated downwards only: an upward change cannot be observed.
"""

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src" / "intake" / "invoicecheck.py"
BS = chr(92)
NL = chr(10)
Q = chr(34)

UNOBSERVABLE: set[str] = {
    # a line never holds a line break (lines are split on it), and the stream copy is joined with spaces: the clause is dead
    "backstop: line break joins",
    # a phone-shaped span always has 9+ digits (PHONE_MIN_DIGITS), so `>= 8` and `> 8` agree on every reachable input
    "phone span: 8 digits -> 9",
}  # filled by build(): table entries that another layer (the shipped fold, NFKD) already maps

Mutant = tuple  # (name, [(old, new)], patch-or-None, pytest -k expression or "")

# Round-5 mutants whose code was rewritten in round 6 (the text they patch is gone); each has a replacement in round6() below.
RETIRED = frozenset(
    [
        "stream copy not scanned",
        "stream copy: per-line runs re-reported",
        "stream copy: on-file ignored",
        "stream copy: grounded ignored",
        "stream copy: ids ignored",
        "bank keyword class removed",
        "never silent: phone spans skipped next to a bank word",
        "backstop: exact match becomes substring",
        "backstop: on-file ignored",
        "backstop: grounded numbers ignored",
        "equality becomes substring",
        "bidi: finding on candidate lines removed",
        "bidi: notice removed",
        "bidi: notice without a payment line",
        "bidi: notice needs candidate (label ignored)",
        "bidi: notice needs label (candidate ignored)",
        "ids: one labelled occurrence is enough",
        "ids: explain everywhere (round 4)",
        "ids: bank word on the line allowed",
        "ids: any line labelled",
        "lexicon not used",
        "change notice removed",
        "payment line notice removed",
        "payment line notice without a label",
        "payment line notice with a candidate",
        "payment line notice needs an on-file record",
        "6-7 digits: joined run counts",
        "6-7 digits: strong class limited too",
        "phone span next to a bank word: own digits not a run",
        "notices not part of check",
        "numbers not part of check",
        "id label word invoice removed",
        "id label word inv removed",
        "id label word po removed",
        "id label word date removed",
        "id label word order removed",
        "keyword: K6 routing removed",
        "keyword: K6 swift removed",
        "keyword: K6 clearing removed",
    ]
)


# retired in round 6 batch 3: the wrapped-digits variant of unexplained_numbers was removed (the line-break-as-space copy covers it)
RETIRED = RETIRED | {"wrapped digits not joined (D12)"}


def textual(name, old, new, k=""):
    return (name, [(old, new)], None, k)


def patched(name, attr, old, new, k=""):
    def patch(mod):
        pat = getattr(mod, attr).pattern
        if old not in pat:
            raise AssertionError(f"{attr}: {old!r} not in pattern")
        setattr(mod, attr, re.compile(pat.replace(old, new, 1)))

    return (name, [], patch, k)


def custom(name, fn, k=""):
    return (name, [], fn, k)


def _sample(items, n):
    items = list(items)
    step = max(1, len(items) // n)
    return items[::step]


def build(sample: int) -> list[Mutant]:
    import intake.invoicecheck as ic

    m: list[Mutant] = []
    # ---- normalisation classes
    m += [
        textual("dash class removed", "    t = t.translate(_DASHES)", "    pass"),
        textual("slash class removed", "    t = t.translate(_SLASHES)", "    pass"),
        textual("line-break class removed", "    t = t.translate(_BREAKS)", "    pass"),
        textual("default-ignorable deletion removed", "    t = t.translate(_DELETE)", "    pass"),
        textual("confusables before casefold removed", "    t = t.translate(_CONF)  # capitals map", "    pass  # capitals map"),
        textual(
            "confusables after casefold removed", "    t = fold(t).casefold()\n    t = t.translate(_CONF)", "    t = fold(t).casefold()"
        ),
        textual(
            "NFKD before the table removed",
            'unicodedata.normalize("NFKD", _unescape(s))  # NFKD first',
            "_unescape(s)  # NFKD first",
        ),
        textual("hand look-alike table removed", "    t = t.translate(_LOOKALIKE)", "    pass"),
        textual("upper/lower partners of confusables not added", "for v in (c.lower(), c.upper(), c.casefold()):", "for v in ():"),
        textual("capital-I override removed", '        out[cp] = "i"', "        pass"),
        textual("whitespace collapse removed", "return _WS.sub(" + Q + " " + Q + ", t)", "return t"),
        textual(
            "CR normalisation removed",
            "t = t.replace("
            + Q
            + BS
            + "r"
            + BS
            + "n"
            + Q
            + ", "
            + Q
            + BS
            + "n"
            + Q
            + ").replace("
            + Q
            + BS
            + "r"
            + Q
            + ", "
            + Q
            + BS
            + "n"
            + Q
            + ")",
            "pass",
        ),
        textual("camel split pass removed (all three)", "for text in (line, camel_line):", "for text in (line,):"),
        textual("NFKC in supplier key removed", 'unicodedata.normalize("NFKC", " ".join(name.split()))', '" ".join(name.split())'),
        textual("modifier letter counts as a letter", 'and unicodedata.category(c) != "Lm"', ""),
    ]
    # ---- join: one mutant per character of the separator set (the character stops joining digit blocks)
    seps = [
        0x2F,
        0x5C,
        0x3A,
        0x7C,
        0x2A,
        0x2B,
        0x60,
        0x27,
        0x2032,
        0x2BC,
        0x2019,
        0xB7,
        0x3B,
        0x5F,
        0x7E,
        0x5E,
        0x3D,
        0x23,
        0x40,
        0x26,
        0x21,
        0x3F,
        0x28,
        0x29,
        0x3C,
        0x3E,
        0x7B,
        0x7D,
        0x5B,
        0x5D,
        0x2C,
        0x2E,
        0x2D,
        0x20,
        0x25,
        0x24,
    ]
    for cp in seps:
        m.append(
            textual(f"sep: char U+{cp:04X} never joins", '_NOJOIN = frozenset("' + BS + 'n")', f'_NOJOIN = frozenset("{BS}n" + chr({cp}))')
        )
    # ---- backstop joiner (round 5: the D10 rule, any non-alphanumeric except a line break)
    m += [
        textual(
            "backstop: letters join",
            "return all(not _word(c) and c not in _NOJOIN for c in line[items[a][1]",
            "return all(c not in _NOJOIN for c in line[items[a][1]",
            "backstop",
        ),
        textual(
            "backstop: line break joins",
            "return all(not _word(c) and c not in _NOJOIN for c in line[items[a][1]",
            "return all(not _word(c) for c in line[items[a][1]",
            "backstop",
        ),
        textual(
            "backstop: nothing joins",
            "return all(not _word(c) and c not in _NOJOIN for c in line[items[a][1]",
            "return all(False for c in line[items[a][1]",
            "backstop",
        ),
        textual("stream copy not scanned", 'for _start, core, forms in _backstop_runs(" ".join(lines)):', "for _start, core, forms in []:"),
        textual("stream copy: per-line runs re-reported", "core not in per_line and", "True and"),
        textual("stream copy: on-file ignored", "not (forms & (comps | known | ids))", "not (forms & (known | ids))"),
        textual("stream copy: grounded ignored", "not (forms & (comps | known | ids))", "not (forms & (comps | ids))"),
        textual("stream copy: ids ignored", "not (forms & (comps | known | ids))", "not (forms & (comps | known))"),
    ]
    # ---- keyword stems
    for name, attr, old, new in [
        ("K6 sort code", "_K6", "sort[^a-z0-9]{0,3}code|", ""),
        ("K6 routing", "_K6", "|routing", ""),
        ("K6 swift", "_K6", "|swift", ""),
        ("K6 clearing", "_K6", "|clearing", ""),
        ("K6 konto", "_K6", "|konto", ""),
        ("K6 branch code", "_K6", "|branch[^a-z0-9]{0,3}code", ""),
        ("K6 iban", "_K6", "|iban", ""),
        ("K6 account + no", "_K6", "|accounts?[^a-z0-9]{0,3}(?:no|num|number|nr|nbr|id)(?![a-z])", ""),
        (
            "K6 accounts plural (no)",
            "_K6",
            "|accounts?[^a-z0-9]{0,3}(?:no|num|number|nr|nbr|id)",
            "|account[^a-z0-9]{0,3}(?:no|num|number|nr|nbr|id)",
        ),
        ("K6 accounts plural (#)", "_K6", "|accounts?[^a-z0-9]{0,3}#", "|account[^a-z0-9]{0,3}#"),
        ("K6 account #", "_K6", "|accounts?[^a-z0-9]{0,3}#", ""),
        ("K6 acct/acc/a-c + no", "_K6", "|(?<![a-z])(?:acct|acc|a[/-]c)[^a-z0-9]{0,3}(?:no|num|number|nr|nbr|id)(?![a-z])", ""),
        ("K6 acct/acc #", "_K6", "|(?<![a-z])(?:acct|acc)[^a-z0-9]{0,3}#", ""),
        ("K6 aba", "_K6", "(?:aba|", "(?:"),
        ("K6 bic", "_K6", "|bic|", "|"),
        ("K6 bsb", "_K6", "|bsb|", "|"),
        ("K6 blz", "_K6", "|blz|", "|"),
        ("K6 ifsc", "_K6", "|ifsc|", "|"),
        ("K6 clabe", "_K6", "|clabe)", ")"),
        ("K6 numword no", "_K6", "(?:no|num|number|nr|nbr|id)", "(?:num|number|nr|nbr|id)"),
        ("K6 numword num", "_K6", "(?:no|num|number|nr|nbr|id)", "(?:no|number|nr|nbr|id)"),
        ("K6 numword nr", "_K6", "(?:no|num|number|nr|nbr|id)", "(?:no|num|number|nbr|id)"),
        ("K6 numword nbr", "_K6", "(?:no|num|number|nr|nbr|id)", "(?:no|num|number|nr|id)"),
        ("K6 numword id", "_K6", "(?:no|num|number|nr|nbr|id)", "(?:no|num|number|nr|nbr)"),
        ("K6 numword right boundary", "_K6", "(?:no|num|number|nr|nbr|id)(?![a-z])|account", "(?:no|num|number|nr|nbr|id)|account"),
        ("K6 short stems left boundary added", "_K6", "(?<![a-z])(?:aba", "(?:aba"),
        ("K6 short stems right boundary removed", "_K6", "clabe)(?![a-z])", "clabe)"),
        ("K8 account word", "_K8", "(?:account|acct|acc|a ?[/-] ?c)", "(?:acct|acc|a ?[/-] ?c)"),
        ("K8 acct word", "_K8", "(?:account|acct|acc|a ?[/-] ?c)", "(?:account|acc|a ?[/-] ?c)"),
        ("K8 acc word", "_K8", "(?:account|acct|acc|a ?[/-] ?c)", "(?:account|acct|a ?[/-] ?c)"),
        ("K8 a/c word", "_K8", "account|acct|acc|a ?[/-] ?c", "account|acct|acc|a ?- ?c"),
        ("K8 a-c word", "_K8", "a ?[/-] ?c", "a ?/ ?c"),
        ("K8 A / C: space before removed", "_K8", "a ?[/-] ?c", "a[/-] ?c"),
        ("K8 A / C: space after removed", "_K8", "a ?[/-] ?c", "a ?[/-]c"),
        ("K8 bankacct prefix", "_K8", "(?:bank)?", ""),
        ("K8 holder suffix", "_K8", "(?:holder|name)?", "(?:name)?"),
        ("K8 name suffix", "_K8", "(?:holder|name)?", "(?:holder)?"),
        ("K8 accounts word", "_K8", "(?:accounts|accts)", "(?:accts)"),
        ("K8 accts word", "_K8", "(?:accounts|accts)", "(?:accounts)"),
        ("K8 accounts: digits needed", "_K8", "|(?:accounts|accts)(?=[^a-z0-9]{0,3}[0-9](?:[^a-z0-9]?[0-9]){7})", ""),
        ("K8 accounts: 8 digits -> 7", "_K8", "){7})", "){6})"),
        ("K8 accounts: 8 digits -> 9", "_K8", "){7})", "){8})"),
        ("K8 accounts: gap 3 -> 2", "_K8", "(?=[^a-z0-9]{0,3}[0-9]", "(?=[^a-z0-9]{0,2}[0-9]"),
        ("K8 accounts: gap 3 -> 4", "_K8", "(?=[^a-z0-9]{0,3}[0-9]", "(?=[^a-z0-9]{0,4}[0-9]"),
        ("K8 accounts: one separator between digits removed", "_K8", "(?:[^a-z0-9]?[0-9]){7}", "(?:[0-9]){7}"),
        ("K8 accounts: separator must exist", "_K8", "(?:[^a-z0-9]?[0-9]){7}", "(?:[^a-z0-9][0-9]){7}"),
        ("K8 left boundary", "_K8", "(?<![a-z])", ""),
        ("K8 right boundary", "_K8", "(?![a-z])", ""),
        ("K6 a-c + no", "_K6", "a[/-]c", "a/c"),
        ("KBANK bank", "_KBANK", "bank", "bxnk"),
        ("KBANK left boundary", "_KBANK", "(?<![a-z])", ""),
        (
            "KBANK suffix group removed",
            "_KBANK",
            "(?:ing|verbindung(?:en)?|leitzahl|giro|details?|daten|info(?:rmation)?|name|number|nr|no|code)?",
            "",
        ),
        ("KBANK ing", "_KBANK", "(?:ing|", "(?:"),
        ("KBANK verbindung", "_KBANK", "verbindung(?:en)?|", ""),
        ("KBANK verbindungen", "_KBANK", "verbindung(?:en)?", "verbindung"),
        ("KBANK number", "_KBANK", "|number|nr|no|code)", "|nr|no|code)"),
        ("KBANK nr", "_KBANK", "|number|nr|no|code)", "|number|no|code)"),
        ("KBANK no", "_KBANK", "|number|nr|no|code)", "|number|nr|code)"),
        ("KBANK code", "_KBANK", "|number|nr|no|code)", "|number|nr|no)"),
        ("KBANK leitzahl", "_KBANK", "leitzahl|", ""),
        ("KBANK giro", "_KBANK", "giro|", ""),
        ("KBANK detail", "_KBANK", "details?", "details"),
        ("KBANK details", "_KBANK", "details?", "detail"),
        ("KBANK daten", "_KBANK", "daten|", ""),
        ("KBANK info", "_KBANK", "info(?:rmation)?", "information"),
        ("KBANK information", "_KBANK", "info(?:rmation)?", "info"),
        ("KBANK name", "_KBANK", "|name|number|nr|no|code)", "|number|nr|no|code)"),
        ("KBANK right boundary", "_KBANK", "(?![a-z])", ""),
        ("K6 acct/acc left boundary", "_K6", "|(?<![a-z])(?:acct|acc|a[/-]c)", "|(?:acct|acc|a[/-]c)"),
        ("K6 acct/acc # left boundary", "_K6", "|(?<![a-z])(?:acct|acc)", "|(?:acct|acc)"),
    ]:
        m.append(patched(f"keyword: {name} removed", attr, old, new))
    m.append(
        textual("bank keyword class removed", "        if _KBANK.search(text) or _KPAY.search(text):", "        if _KPAY.search(text):")
    )
    m.append(textual("bare keyword class removed", "        if _K8.search(text):", "        if False:"))
    # ---- phone labels, amount words, gaps (one mutant each)
    bank_words = [
        "telephone",
        "telefone",
        "telefono",
        "telefoon",
        "telefon",
        "whatsapp",
        "mobile",
        "phone",
        "handy",
        "cell",
        "gsm",
        "fax",
        "tel",
        "tlf",
        "mob",
        "ph",
        "ref",
        "vat",
        "abn",
    ]
    labels = bank_words[:16]
    full = "(" + "|".join(labels) + "|ref|vat|abn)"
    for w in bank_words:
        rest = "|".join(x for x in bank_words if x != w)
        m.append(patched(f"phone (bank) word {w} removed", "_PHONE_BANK", full, f"({rest})"))
    bare_words = labels + ["manager", "contact", "customer"]
    fullb = "(" + "|".join(bare_words) + ")"
    for w in bare_words:
        rest = "|".join(x for x in bare_words if x != w)
        m.append(patched(f"phone (bare) word {w} removed", "_PHONE_BARE", fullb, f"({rest})"))
    for w in labels:
        rest = "|".join(x for x in labels if x != w)
        m.append(patched(f"phone span word {w} removed", "_PHONE_SPAN", "(?:" + "|".join(labels) + ")", f"(?:{rest})"))
    m.append(patched("phone span left boundary removed", "_PHONE_SPAN", "(?<![a-z])", ""))
    m.append(patched("phone span stops at no letter", "_PHONE_SPAN", "[^a-z" + BS + "n]*", "[^" + BS + "n]*"))
    m.append(patched("phone span stops at digits too", "_PHONE_SPAN", "[^a-z" + BS + "n]*", "[^a-z0-9" + BS + "n]*"))
    m.append(
        textual(
            "phone span: number must start inside it",
            "any(lo < start < hi for lo, hi, _ in spans)",
            "any(lo <= start <= hi + 1 for lo, hi, _ in spans)",
        )
    )
    m.append(
        textual(
            "backstop money amounts not skipped",
            "kind = " + Q + "break" + Q + " if _is_date(g) or _MONEY.fullmatch(g) else",
            "kind = " + Q + "break" + Q + " if _is_date(g) else",
        )
    )
    m.append(textual("backstop BACKSTOP_MIN_BLOCK -> 2", "BACKSTOP_MIN_BLOCK = 3", "BACKSTOP_MIN_BLOCK = 2"))
    m.append(textual("backstop BACKSTOP_MIN_BLOCK -> 4", "BACKSTOP_MIN_BLOCK = 3", "BACKSTOP_MIN_BLOCK = 4"))
    for attr in ("_PHONE_BANK", "_PHONE_BARE"):
        m.append(patched(f"{attr} left boundary removed", attr, "(?<![a-z])", ""))
        m.append(patched(f"{attr} gap 3 -> 2", attr, "{0,3}$", "{0,2}$"))
        m.append(patched(f"{attr} gap 3 -> 4", attr, "{0,3}$", "{0,4}$"))
    for attr in ("_PHONE_BANK", "_PHONE_BARE"):
        for w in ("number", "num", "nr", "no"):
            rest = "|".join(x for x in ("number", "num", "nr", "no") if x != w)
            m.append(patched(f"{attr} number word {w} removed", attr, "(?:number|num|nr|no)", f"(?:{rest})"))
        m.append(patched(f"{attr} number word group removed", attr, "(?:[^a-z0-9]{0,3}(?:number|num|nr|no))?", ""))
    m.append(
        textual("phone lookback: number word and gap not counted", "+ PHONE_GAP + len(" + Q + "number" + Q + ") + PHONE_GAP", "+ PHONE_GAP")
    )
    m.append(textual("phone lookback shortened", "split(" + Q + "|" + Q + ")) + PHONE_GAP", "split(" + Q + "|" + Q + "))"))
    for w in ("number", "num", "nr", "no"):
        rest = "|".join(x for x in ("number", "num", "nr", "no") if x != w)
        m.append(patched(f"phone span number word {w} removed", "_PHONE_SPAN", "(?:number|num|nr|no)", f"(?:{rest})"))
    amount = ["total", "subtotal", "amount", "balance", "due", "price", "sum", "vat", "tax"]
    for w in amount:
        rest = "|".join(x for x in amount if x != w)
        m.append(patched(f"amount word {w} removed", "_AMOUNT_WORD", "(?:" + "|".join(amount) + ")", f"(?:{rest})"))
    m.append(patched("amount word left boundary removed", "_AMOUNT_WORD", "(?<![a-z])", ""))
    m.append(patched("amount word right boundary removed", "_AMOUNT_WORD", "(?![a-z])", ""))
    m.append(patched("money: cents 2 -> 1", "_MONEY", "{2}", "{1}"))
    m.append(patched("money: cents 2 -> 3", "_MONEY", "{2}", "{3}"))
    m.append(patched("money: dot optional", "_MONEY", r"\.", r"\.?"))
    # ---- BIC parts
    for name, old, new in [
        ("bank letters 4 -> 3", "([a-z]{4}) ?([a-z]{2})", "([a-z]{3}) ?([a-z]{2})"),
        ("bank letters 4 -> 5", "([a-z]{4}) ?([a-z]{2})", "([a-z]{5}) ?([a-z]{2})"),
        ("country letters 2 -> 1", "([a-z]{2}) ?([a-z0-9]{2})", "([a-z]{1}) ?([a-z0-9]{2})"),
        ("location 2 -> 1", "([a-z0-9]{2})((?:", "([a-z0-9]{1})((?:"),
        ("branch 3 -> 2", "((?:[a-z0-9]{3})?)", "((?:[a-z0-9]{2})?)"),
        ("branch optional removed", "((?:[a-z0-9]{3})?)", "((?:[a-z0-9]{3}))"),
        ("space after bank letters not tolerated", "([a-z]{4}) ?([a-z]{2})", "([a-z]{4})([a-z]{2})"),
        ("space after country not tolerated", "([a-z]{2}) ?([a-z0-9]{2})", "([a-z]{2})([a-z0-9]{2})"),
        ("label word code", "(?:code|number|no|address|id)", "(?:number|no|address|id)"),
        ("label word number", "(?:code|number|no|address|id)", "(?:code|no|address|id)"),
        ("label word no", "(?:code|number|no|address|id)", "(?:code|number|address|id)"),
        ("label word address", "(?:code|number|no|address|id)", "(?:code|number|no|id)"),
        ("label word id", "(?:code|number|no|address|id)", "(?:code|number|no|address)"),
        ("label swift", "(?:swift|bic)", "(?:bic)"),
        ("label bic", "(?:swift|bic)", "(?:swift)"),
        ("right boundary removed", "(?![a-z0-9])", ""),
    ]:
        m.append(patched(f"BIC: {name}", "_BIC", old, new))
    for cc in _sample(sorted(ic._ISO), sample):
        m.append(custom(f"ISO country {cc} removed", lambda mod, cc=cc: setattr(mod, "_ISO", frozenset(mod._ISO - {cc})), "bic_accepts"))
    # ---- constants, both directions (caps above any need: downwards only)
    for name, old, news in [
        ("THRESHOLD_KEYWORD", "THRESHOLD_KEYWORD = 6", ["5", "7"]),
        ("THRESHOLD_BARE", "THRESHOLD_BARE = 8", ["7", "9"]),
        ("MAX_JOIN", "MAX_JOIN = 16", ["15", "17"]),
        ("NEXT_LINES", "NEXT_LINES = 3", ["2", "4"]),
        ("ALPHA_TOKEN_MAX", "ALPHA_TOKEN_MAX = 8", ["7", "9"]),
        ("ALPHA_TOKEN_STOP", "ALPHA_TOKEN_STOP = 5", ["4", "6"]),
        ("HEX_MIN_BYTES", "HEX_MIN_BYTES = 8", ["7", "9"]),
        ("BACKSTOP_MIN_DIGITS", "BACKSTOP_MIN_DIGITS = 8", ["7", "9"]),
        ("IBAN_KW_START", "IBAN_KW_START = 3", ["2", "4"]),
        ("KW_GAP", "KW_GAP = 3", ["2", "4"]),
        ("PHONE_GAP", "PHONE_GAP = 3", ["2", "4"]),
        ("BIC_GAP", "BIC_GAP = 6", ["5", "7"]),
        ("LOOKALIKE_MIN_DIGITS", "LOOKALIKE_MIN_DIGITS = 4", ["3", "5"]),
    ]:
        for n in news:
            m.append(textual(f"{name} -> {n}", old, f"{old.split('=')[0]}= {n}"))
    m.append(
        textual(
            "IBAN_KW_TOKENS -> 32 (downwards only: 33 tokens is the most a candidate can need)",
            "IBAN_KW_TOKENS = 40",
            "IBAN_KW_TOKENS = 32",
        )
    )
    for n in ("33", "35"):
        m.append(textual(f"RUN_MAX -> {n}", "RUN_MAX, RUN_MIN, TOKEN_MAX = 34, 15, 4", f"RUN_MAX, RUN_MIN, TOKEN_MAX = {n}, 15, 4"))
    for n in ("14", "16"):
        m.append(textual(f"RUN_MIN -> {n}", "RUN_MAX, RUN_MIN, TOKEN_MAX = 34, 15, 4", f"RUN_MAX, RUN_MIN, TOKEN_MAX = 34, {n}, 4"))
    for n in ("3", "5"):
        m.append(textual(f"TOKEN_MAX -> {n}", "RUN_MAX, RUN_MIN, TOKEN_MAX = 34, 15, 4", f"RUN_MAX, RUN_MIN, TOKEN_MAX = 34, 15, {n}"))
    # ---- dates: bounds and year edges
    for name, old, new in [
        ("month upper 12 -> 13", "1 <= a <= 12 and 1 <= b <= 31", "1 <= a <= 13 and 1 <= b <= 31"),
        ("month upper 12 -> 11", "1 <= a <= 12 and 1 <= b <= 31", "1 <= a <= 11 and 1 <= b <= 31"),
        ("day upper 31 -> 32", "1 <= a <= 12 and 1 <= b <= 31", "1 <= a <= 12 and 1 <= b <= 32"),
        ("day upper 31 -> 30", "1 <= a <= 12 and 1 <= b <= 31", "1 <= a <= 12 and 1 <= b <= 30"),
        ("month lower 1 -> 0", "1 <= a <= 12 and 1 <= b <= 31", "0 <= a <= 12 and 1 <= b <= 31"),
        ("day lower 1 -> 0", "1 <= a <= 12 and 1 <= b <= 31", "1 <= a <= 12 and 0 <= b <= 31"),
        ("either order: second form 31/12", "(1 <= a <= 31 and 1 <= b <= 12)", "(1 <= a <= 32 and 1 <= b <= 12)"),
        ("either order: second form 31/12 down", "(1 <= a <= 31 and 1 <= b <= 12)", "(1 <= a <= 30 and 1 <= b <= 12)"),
        ("either order: second form month 12 -> 13", "(1 <= a <= 31 and 1 <= b <= 12)", "(1 <= a <= 31 and 1 <= b <= 13)"),
        ("either order: second form month 12 -> 11", "(1 <= a <= 31 and 1 <= b <= 12)", "(1 <= a <= 31 and 1 <= b <= 11)"),
        ("either order removed", " or (1 <= a <= 31 and 1 <= b <= 12)", ""),
        ("date: any 4-digit year (ymd)", "((?:19|20)[0-9]{2})[-.]([0-9]{2})", "([0-9]{4})[-.]([0-9]{2})"),
        ("date: 18xx accepted (ymd)", "((?:19|20)[0-9]{2})[-.]([0-9]{2})", "((?:18|19|20)[0-9]{2})[-.]([0-9]{2})"),
        ("date: 21xx accepted (ymd)", "((?:19|20)[0-9]{2})[-.]([0-9]{2})", "((?:19|20|21)[0-9]{2})[-.]([0-9]{2})"),
        ("date: 19xx rejected (ymd)", "((?:19|20)[0-9]{2})[-.]([0-9]{2})", "((?:20)[0-9]{2})[-.]([0-9]{2})"),
        ("date: 20xx rejected (ymd)", "((?:19|20)[0-9]{2})[-.]([0-9]{2})", "((?:19)[0-9]{2})[-.]([0-9]{2})"),
        ("date: any 4-digit year (dmy)", "[-.]((?:19|20)[0-9]{2})", "[-.]([0-9]{4})"),
        ("date: 18xx accepted (dmy)", "[-.]((?:19|20)[0-9]{2})", "[-.]((?:18|19|20)[0-9]{2})"),
        ("date: 21xx accepted (dmy)", "[-.]((?:19|20)[0-9]{2})", "[-.]((?:19|20|21)[0-9]{2})"),
        ("date: 19xx rejected (dmy)", "[-.]((?:19|20)[0-9]{2})", "[-.]((?:20)[0-9]{2})"),
        ("date: 20xx rejected (dmy)", "[-.]((?:19|20)[0-9]{2})", "[-.]((?:19)[0-9]{2})"),
        ("dates are not skipped", "if _is_date(m.group()) or (not money_ok", "if False or (not money_ok"),
        ("money below a keyword line always skipped", "(not money_ok and _MONEY.fullmatch(m.group()))", "(_MONEY.fullmatch(m.group()))"),
        ("money skip removed", "or (not money_ok and _MONEY.fullmatch(m.group()))", ""),
    ]:
        m.append(textual(f"date edge: {name}", old, new))
    # ---- look-alike digits: one letter at a time
    for ch, dg in zip("oilsbz", "011582", strict=True):
        m.append(
            textual(
                f"look-alike letter {ch} not read",
                'str.maketrans("oilsbz", "011582")',
                'str.maketrans("' + "oilsbz".replace(ch, "") + '", "' + "011582".replace(dg, "", 1) + '")',
            )
        )
    m.append(
        textual("look-alike set lacks o", '_LOOKSET = frozenset("0123456789oilsbzgqtae")', '_LOOKSET = frozenset("0123456789ilsbzgqtae")')
    )
    m.append(textual("look-alike pieces need no digit", "set(t) <= _LOOKSET and any(c.isdigit() for c in t)", "set(t) <= _LOOKSET"))

    # ---- tables: sampled single entries
    def observable(table, cp):
        """True when removing the entry changes what the choke point returns for that character (another layer may map it too)."""
        before, saved = ic._f(chr(cp)), table.pop(cp, None)
        try:
            return ic._f(chr(cp)) != before
        finally:
            if saved is not None:
                table[cp] = saved

    for cp in _sample(sorted(ic._CONF), sample):
        name = f"confusables entry U+{cp:04X} removed"
        if not observable(ic._CONF, cp):
            UNOBSERVABLE.add(name)
        m.append(custom(name, lambda mod, cp=cp: mod._CONF.pop(cp, None), "table_walk or capital"))
    for cp in sorted(ic._LOOKALIKE):
        name = f"hand look-alike U+{cp:04X} removed"
        if not observable(ic._LOOKALIKE, cp):
            UNOBSERVABLE.add(name)
        m.append(custom(name, lambda mod, cp=cp: mod._LOOKALIKE.pop(cp, None), "table_walk"))
    for cp in ic._I_LIKE:
        m.append(
            custom(
                f"capital-I look-alike U+{cp:04X} read as l",
                lambda mod, cp=cp: mod._CONF.__setitem__(cp, "l"),
                "table_walk or capital or core_copy",
            )
        )
    for cp in _sample([c for lo, hi in ic._IGNORABLE for c in range(lo, min(hi, lo + 3) + 1)], sample):
        name = f"ignorable code point U+{cp:04X} kept"
        if not observable(ic._DELETE, cp):
            UNOBSERVABLE.add(name)
        m.append(custom(name, lambda mod, cp=cp: mod._DELETE.pop(cp, None), "ignorable"))
    for cp in sorted(ic._DASHES):
        name = f"dash code point U+{cp:04X} removed"
        if not observable(ic._DASHES, cp):
            UNOBSERVABLE.add(name)
        m.append(custom(name, lambda mod, cp=cp: mod._DASHES.pop(cp, None), "dash"))
    qty = ("qty", "quantity", "pcs", "units?", "menge", "stk", "cant", "x")
    for w in qty:
        rest = "|".join(x for x in qty if x != w)
        m.append(patched(f"quantity word {w} removed", "_QTY_WORD", "(?:" + "|".join(qty) + ")", f"(?:{rest})"))
    # ---- phone / logic
    m += [
        textual("bank-only phone exclusion removed", "if skip is not None and _skip_run(", "if False and _skip_run("),
        textual("phone words always skip (D10)", "if m.group(1) not in _PHONE_WORDS:", "if True:"),
        textual("phone shape ignored (D10)", "    return _phone_text(span.group())", "    return True"),
        textual(
            "phone text: no groups is a phone",
            "if not groups:" + NL + "        return False",
            "if not groups:" + NL + "        return True",
        ),
        textual(
            "phone text: a + or ( anywhere decides",
            "first = m.group()",
            'first = "+" if "+" in text else ("(" if "(" in text else m.group())',
        ),
        textual(
            "phone text: + is not a phone",
            'if first == "+":' + NL + "        return True",
            'if first == "+":' + NL + "        return False",
        ),
        textual("phone text: ( branch removed", 'if first == "(":', "if False:"),
        textual("phone text: (+ not accepted", "(?:" + BS + "+|0[)]|", "(?:0[)]|"),
        textual("phone text: (0) not accepted", "|0[)]|", "|"),
        textual("phone text: (nn) not accepted", "|[0-9]{2,}[)])", ")"),
        textual("phone text: (n) accepted", "[0-9]{2,}[)])", "[0-9]+[)])"),
        textual("phone text: ( rule not anchored", "return re.match(r" + Q + "[(]", "return re.search(r" + Q + "[(]"),
        textual("phone text: min digits removed", "if digits < PHONE_MIN_DIGITS:", "if False:"),
        textual("phone text: min digits 9 -> 8 (inline)", "if digits < PHONE_MIN_DIGITS:", "if digits < PHONE_MIN_DIGITS - 1:"),
        textual("phone text: one-digit groups allowed", "if any(len(g) < 2 for g in groups[1:]):", "if False:"),
        textual("phone text: all groups need two digits", "if any(len(g) < 2 for g in groups[1:]):", "if any(len(g) < 2 for g in groups):"),
        textual("phone text: leading 0 branch removed", 'if first == "0":', "if False:"),
        textual("phone text: leading 0 needs one digit group", "return len(groups[0]) >= 2", "return len(groups[0]) >= 1"),
        textual("phone text: leading 0 needs three digit group", "return len(groups[0]) >= 2", "return len(groups[0]) >= 3"),
        textual("phone text: three groups -> two", "len(groups) >= 3 and", "len(groups) >= 2 and"),
        textual("phone text: three groups -> four", "len(groups) >= 3 and", "len(groups) >= 4 and"),
        textual("phone text: max digits removed", "digits <= PHONE_MAX_DIGITS and", ""),
        textual("phone text: last group 4 -> 3", "len(groups[-1]) >= 4", "len(groups[-1]) >= 3"),
        textual("phone text: last group 4 -> 5", "len(groups[-1]) >= 4", "len(groups[-1]) >= 5"),
        textual("phone text: last group rule removed", " and len(groups[-1]) >= 4", ""),
        textual("PHONE_MIN_DIGITS 9 -> 8", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 15", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 8, 15"),
        textual("PHONE_MIN_DIGITS 9 -> 10", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 15", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 10, 15"),
        textual("PHONE_MAX_DIGITS 15 -> 14", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 15", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 14"),
        textual("PHONE_MAX_DIGITS 15 -> 16", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 15", "PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 16"),
        textual("never silent: phone spans skipped next to a bank word", "silent = not near[i] and any(", "silent = not False and any("),
        textual(
            "never silent: bank word on the line itself ignored", "        kw[i] or (i + 1 < len(kw)", "        False or (i + 1 < len(kw)"
        ),
        textual("never silent: bank word on the next line ignored", "or (i + 1 < len(kw) and kw[i + 1])", "or False"),
        textual(
            "never silent: bank word above (D10 next-line read) ignored",
            "or any(kw[k] and _next_nonblank(lines, k) == i for k in range(max(0, i - NEXT_LINES), i))",
            "or False",
        ),
        textual("never silent: any line above counts", "kw[k] and _next_nonblank(lines, k) == i for k", "kw[k] for k"),
        textual("never silent: camel pass ignored", "_kw_class(ln, cl)[0]", "_kw_class(ln, ln)[0]"),
        textual(
            "phone spans not shaped (D12)",
            "for m in _PHONE_SPAN.finditer(variant) if _phone_text(m.group())",
            "for m in _PHONE_SPAN.finditer(variant)",
        ),
        textual("comparison form: lead ignores a quantity word", " and not qty else", " else"),
        textual(
            "comparison form: lead needs no single space",
            'line[items[i - 1][1] : items[i][0]] == " " and not qty',
            "joined(i - 1, i) and not qty",
        ),
        textual("comparison form: trail needs no single space", 'line[items[j][1] : items[j + 1][0]] == " "', "joined(j, j + 1)"),
        textual("IBAN keyword-free scan does not wrap lines", "lines[i + 1 : i + 3]", "lines[i + 1 : i + 1]"),
        textual("IBAN split-token rule removed", "if strict and split and not", "if False and not"),
        textual(
            "IBAN digit share removed", "if strict and sum(c.isdigit() for c in got) <", "if False and sum(c.isdigit() for c in got) <"
        ),
        textual("IBAN split digit share equals plain", "(need * 2 // 3 if split else need // 2)", "need // 2"),
        textual("IBAN word cap removed", "(strict and words > ALPHA_TOKEN_MAX)", "False"),
        textual("IBAN word stop removed", "len(tok) >= ALPHA_TOKEN_STOP or", "False or"),
        textual("IBAN keyword starts only at the first token", "range(min(IBAN_KW_START, len(toks)))", "range(min(1, len(toks)))"),
        textual("IBAN keyword fallback removed", ") or _token_run(toks)", ")"),
        textual(
            "IBAN keyword window without next line", 'text = line + "' + BS + 'n" + (lines[nxt] if nxt is not None else "")', "text = line"
        ),
        textual("IBAN country table ignored", "if len(first) < 2 or first[:2] not in _LEN:", "if len(first) < 2:"),
        textual(
            "next non-blank line not scanned",
            "        j = _next_nonblank(lines, i)\n        if j is not None:\n            add(",
            "        j = None\n        if j is not None:\n            add(",
        ),
        textual("line above not scanned", "if i > 0 and _NUMBER_ONLY.fullmatch(lines[i - 1].strip()):", "if False:"),
        textual("line above: any text counts", "_NUMBER_ONLY.fullmatch(lines[i - 1].strip())", "lines[i - 1].strip()"),
        textual("wrapped digits not joined (D10)", "        if _wraps(lines, i):\n            add(", "        if False:\n            add("),
        textual(
            "wrapped digits not joined (D12)",
            "            if _wraps(lines, i):" + chr(10) + "                variants.add",
            "            if False:" + chr(10) + "                variants.add",
        ),
        textual("wrap needs no digit at line end", "lines[i].rstrip()[-1:].isdigit() and", "True and"),
        textual("wrap needs no digit at next line start", "and lines[i + 1].lstrip()[:1].isdigit()", ""),
        textual(
            "look-alike digits not read (D10 line)",
            "for variant in _variants(line):\n        for start",
            "for variant in {line}:\n        for start",
        ),
        textual(
            "look-alike digits not read (on-file)",
            "for variant in _variants(line):\n            for _,",
            "for variant in {line}:\n            for _,",
        ),
        textual(
            "look-alike digits not read (D12)",
            "            for variant in _variants(line):  # a number wrapped",
            "            for variant in {line}:  # a number wrapped",
        ),
        textual("hex: odd offset not tried", "for off in (0, 1):", "for off in (0,):"),
        textual(
            "hex: 0x and backslash-x not stripped",
            "re.sub(r" + Q + "0x|" + BS + BS + "x|[^0-9a-fA-F]" + Q,
            "re.sub(r" + Q + "[^0-9a-fA-F]" + Q,
        ),
        textual("hex not decoded", ", *_hex_extras(send_text)]", "]"),
        textual(
            "encodings not decoded",
            "return [send_text, *_extras(send_text), *_hex_extras(send_text)]",
            "return [send_text, *_hex_extras(send_text)]",
        ),
        textual("BIC: country check removed", "if code[4:6] in _ISO", "if True"),
        textual("BIC compare removed", "        if on_bics:", "        if False:"),
        textual(
            "BIC 8 vs 11 tolerance removed",
            "(a[:8] == b[:8] and (len(a) == 8 or len(b) == 8 or a[8:] == " + Q + "xxx" + Q + " or b[8:] == " + Q + "xxx" + Q + "))",
            "False",
        ),
        textual("backstop: exact match becomes substring", "or forms & known:", "or any(core in k for k in known):"),
        textual("backstop: on-file ignored", "if silent or forms & comps or forms & known:", "if silent or forms & known:"),
        textual("backstop: grounded numbers ignored", "if silent or forms & comps or forms & known:", "if silent or forms & comps:"),
        textual(
            "record numbers: invoice number ignored",
            'for k in ("invoice_no", "po_ref", "invoice_date"):',
            'for k in ("po_ref", "invoice_date"):',
        ),
        textual(
            "record numbers: PO ignored", 'for k in ("invoice_no", "po_ref", "invoice_date"):', 'for k in ("invoice_no", "invoice_date"):'
        ),
        textual("record numbers: date ignored", 'for k in ("invoice_no", "po_ref", "invoice_date"):', 'for k in ("invoice_no", "po_ref"):'),
        textual("record numbers: total ignored", 'known.add(str(abs(fields["total_minor"])))', "pass"),
        textual(
            "record numbers: line amounts ignored",
            'known |= {str(abs(x["amount_minor"])), str(abs(x["unit_cost_minor"]))}',
            'known |= {str(abs(x["unit_cost_minor"]))}',
        ),
        textual(
            "record numbers: unit costs ignored",
            'known |= {str(abs(x["amount_minor"])), str(abs(x["unit_cost_minor"]))}',
            'known |= {str(abs(x["amount_minor"]))}',
        ),
        textual(
            "record numbers: adjustments ignored", 'known.add(str(abs(x["amount_minor"])))\n    known.discard', "pass\n    known.discard"
        ),
        textual(
            "D12 swallows a malformed record",
            "        except Exception:  # noqa: BLE001 (a malformed record or a failed scan: a person looks)\n            flags.add(BACKSTOP_FLAG)",
            "        except Exception:  # noqa: BLE001 (a malformed record or a failed scan: a person looks)\n            pass",
        ),
        textual("D12 default off", "backstop: bool = True", "backstop: bool = False"),
        textual("components: joins removed", "                for a in range(len(blocks)):", "                for a in range(0):"),
        textual(
            "keyword line: blocks alone not candidates",
            "out += [b for b in blocks if len(b) >= thr and _plain_ok(b, variant, kind)]",
            "pass",
        ),
        textual("keyword line: joined run not a candidate", "if len(blocks) > 1 and len(whole) >= thr and", "if False and"),
        textual("arithmetic accepts bool/float", "type(x) is int", "isinstance(x, (int, float))"),
        textual("load_suppliers accepts empty component", "if not _components(row[1]):", "if False:"),
        textual("supplier key guard removed", "if any(k != _key(k) for k in suppliers):", "if False:"),
        textual(
            "equality becomes substring", "            if c not in comps:\n", "            if not any(c in k or k in c for k in comps):\n"
        ),
        textual("findings not de-duplicated", "if (c, kind) not in seen:", "if True:"),
    ]
    m += round5(ic)
    m += round6(ic)
    m += round7(ic)
    return [x for x in m if x[0] not in RETIRED and x[0] not in RETIRED2]


def round5(ic) -> list[Mutant]:
    """One mutant per new branch of round 5 (bidi, ids, lexicon, notices, streams, thresholds, IFSC/BIC, encodings, fail-closed)."""
    m: list[Mutant] = []
    mut = textual
    m += [
        # bidi
        mut("bidi: finding on candidate lines removed", "            if at & bl:", "            if False:"),
        mut(
            "bidi: lines never found", "    if not any(c in _BIDI for c in u):\n        return set()", "    if True:\n        return set()"
        ),
        mut("bidi: marker not counted", "if _MARK in ln}", "if False}"),
        mut("bidi: notice removed", "        if (at or label) and any(c in _BIDI for c in u):", "        if False:"),
        mut(
            "bidi: notice without a payment line",
            "        if (at or label) and any(c in _BIDI for c in u):",
            "        if any(c in _BIDI for c in u):",
        ),
        mut(
            "bidi: notice needs candidate (label ignored)",
            "        if (at or label) and any(c in _BIDI for c in u):",
            "        if at and any(c in _BIDI for c in u):",
        ),
        mut(
            "bidi: notice needs label (candidate ignored)",
            "        if (at or label) and any(c in _BIDI for c in u):",
            "        if label and any(c in _BIDI for c in u):",
        ),
        # ids
        mut(
            "ids: one labelled occurrence is enough",
            "if any(all(labelled[k] for k in occ[v]) for v in forms & ids):",
            "if any(any(labelled[k] for k in occ[v]) for v in forms & ids):",
        ),
        mut("ids: explain everywhere (round 4)", "if any(all(labelled[k] for k in occ[v]) for v in forms & ids):", "if forms & ids:"),
        mut(
            "ids: bank word on the line allowed",
            "labelled = [bool(_IDLABEL.search(ln)) and not _kw_class(ln, cl)[0] for",
            "labelled = [bool(_IDLABEL.search(ln)) for",
        ),
        mut(
            "ids: any line labelled",
            "labelled = [bool(_IDLABEL.search(ln)) and not",
            "labelled = [True or bool(_IDLABEL.search(ln)) and not",
        ),
        mut("ids: record ids lumped into amounts", "    known = _record_numbers(fields) - ids\n", "    known = _record_numbers(fields)\n"),
        # lexicon and notices
        mut("lexicon not used", "if _KBANK.search(text) or _KPAY.search(text):", "if _KBANK.search(text):"),
        mut("change notice removed", "        if m := _CHANGE.search(t):", "        if False:"),
        mut(
            "payment line notice removed",
            "    if on_file and not any_cand and (any_label or not PAYMENT_LINE_NEEDS_LABEL):",
            "    if False:",
        ),
        mut("payment line notice without a label", "(any_label or not PAYMENT_LINE_NEEDS_LABEL)", "(True)"),
        mut("payment line notice with a candidate", "    if on_file and not any_cand and (", "    if on_file and ("),
        mut("payment line notice needs an on-file record", "    if on_file and not any_cand and (", "    if not any_cand and ("),
        mut("stream IBAN notice removed", "        if extra := (_stream_ibans(lines) - per_line - comps):", "        if False:"),
        mut("stream IBAN: per-line ones re-reported", "_stream_ibans(lines) - per_line - comps", "_stream_ibans(lines) - comps"),
        mut("stream IBAN: on-file one re-reported", "_stream_ibans(lines) - per_line - comps", "_stream_ibans(lines) - per_line"),
        mut("opaque notice removed", "    if blobs := _opaque_blobs(send_text):", "    if False:"),
        mut("opaque: readable text counts", "if b is None or _printable_share(b) < 0.7:", "if True:"),
        mut("opaque: undecodable ignored", "if b is None or _printable_share(b) < 0.7:", "if b is not None and _printable_share(b) < 0.7:"),
        mut("opaque: share 0.7 -> 0.2", "_printable_share(b) < 0.7", "_printable_share(b) < 0.2"),
        mut("opaque: plain words count", 'if len(blob) < _OPAQUE_MIN or not (blob.endswith("=") or mixed):', "if len(blob) < _OPAQUE_MIN:"),
        mut("opaque: padding not enough", 'not (blob.endswith("=") or mixed)', "not mixed"),
        mut("opaque: min 32 -> 16", "_OPAQUE_MIN = 32", "_OPAQUE_MIN = 16"),
        mut("opaque: min 32 -> 64", "_OPAQUE_MIN = 32", "_OPAQUE_MIN = 64"),
        mut("line mismatch flag removed", '            add("line_mismatch")', "            pass"),
        mut("BIC-not-on-file notice removed", "            if not _bics(onf) and (b := _bics(t)):", "            if False:"),
        mut("IFSC-not-on-file notice removed", "            if not _ifscs(onf) and (x := _ifscs(t)):", "            if False:"),
        mut("IFSC compare removed", "        if on_ifsc:", "        if False:"),
        mut("IFSC compare: any IFSC accepted", "                if x not in on_ifsc:", "                if False:"),
        # joiner and thresholds
        mut("bare threshold stays 8", "return THRESHOLD_KEYWORD if comps else THRESHOLD_BARE", "return THRESHOLD_BARE"),
        mut("bare threshold 6 without components", "return THRESHOLD_KEYWORD if comps else THRESHOLD_BARE", "return THRESHOLD_KEYWORD"),
        mut("6-7 digits: unbroken test removed", "        or b in variant  #", "        or False  #"),
        mut("6-7 digits: unbroken test always true", "        or b in variant  #", "        or True  #"),
        mut("6-7 digits: joined run counts", ' and (len(whole) >= THRESHOLD_BARE or kind == "strong"):', ":"),
        mut("6-7 digits: block ok test removed", "if len(b) >= thr and _plain_ok(b, variant, kind)]", "if len(b) >= thr]"),
        mut("6-7 digits: strong class limited too", 'len(b) >= THRESHOLD_BARE or kind == "strong" or', "len(b) >= THRESHOLD_BARE or"),
        # phone next to a bank word
        mut(
            "phone span next to a bank word: own digits not a run",
            "if near[i]:",
            "if False:",
        ),
        mut(
            "phone span: run even when a run exists",
            "if len(sd) >= BACKSTOP_MIN_DIGITS and not any(c in sd for c in line_cores):",
            "if len(sd) >= BACKSTOP_MIN_DIGITS:",
        ),
        mut("phone span: 8 digits -> 9", "if len(sd) >= BACKSTOP_MIN_DIGITS and not any", "if len(sd) > BACKSTOP_MIN_DIGITS and not any"),
        # encodings
        mut("base64 strict again", '            d = b.decode("utf-8", errors="ignore")', '            d = b.decode("utf-8")'),
        mut("quoted-printable not decoded", "    if _QP.search(text):", "    if False:"),
        mut("unicode escapes not decoded", '    if "\\\\u" in text:', "    if False:"),
        mut("percent not decoded", '    if "%" in text:', "    if False:"),
        mut("entities resolved once", "    for _ in range(8):", "    for _ in range(1):"),
        mut("wide look-alikes need 4 digits", "LOOKALIKE_MIN_DIGITS_WIDE = 7", "LOOKALIKE_MIN_DIGITS_WIDE = 4"),
        mut("wide look-alikes need 9 digits", "LOOKALIKE_MIN_DIGITS_WIDE = 7", "LOOKALIKE_MIN_DIGITS_WIDE = 9"),
        mut("G read as 9 (g table is the wide one)", 'str.maketrans("g", "6")', 'str.maketrans("g", "9")'),
        mut("G not read as 6", 'str.maketrans("g", "6")', 'str.maketrans("g", "g")'),
        mut("wide tables dropped", "*(_digitise(line, tb, LOOKALIKE_MIN_DIGITS_WIDE) for tb in _LOOK_TABLES[1:])", ""),
        # fail closed
        mut(
            "D10 scan does not fail closed",
            "    except Exception:  # noqa: BLE001 (deliberately broad",
            "    except ZeroDivisionError:  # noqa: BLE001 (deliberately broad",
        ),
        mut(
            "D12 scan does not fail closed",
            "        except Exception:  # noqa: BLE001 (a malformed record",
            "        except KeyError:  # noqa: BLE001 (a malformed record",
        ),
        mut(
            "notices not part of check",
            "unexplained_numbers(fields, send_text, on_file) or look_notices(fields, send_text, on_file)",
            "unexplained_numbers(fields, send_text, on_file)",
        ),
        mut(
            "numbers not part of check",
            "unexplained_numbers(fields, send_text, on_file) or look_notices(fields, send_text, on_file)",
            "look_notices(fields, send_text, on_file)",
        ),
    ]
    for ch, dg in zip("gqtae", "99743", strict=True):  # each wide look-alike letter, one at a time
        m.append(
            mut(
                f"wide look-alike {ch} not read",
                'str.maketrans("oilsbzgqtae", "01158299743")',
                'str.maketrans("' + "oilsbzgqtae".replace(ch, "") + '", "' + "01158299743".replace(dg, "", 1) + '")',
            )
        )
    for cp in (0x202A, 0x202E, 0x2066, 0x2069, 0x200E, 0x200F, 0x061C, 0x2060, 0x206F):
        m.append(
            custom(f"bidi control U+{cp:04X} not in the set", lambda mod, cp=cp: setattr(mod, "_BIDI", frozenset(mod._BIDI - {chr(cp)})))
        )
    # lexicon words, one at a time (sampled)
    for i, w in enumerate(ic.PAYMENT_LEXICON):
        if i % 2 == 0:
            m.append(
                custom(
                    f"lexicon word {w[:24]!r} removed",
                    lambda mod, i=i: setattr(
                        mod,
                        "_KPAY",
                        re.compile("(?<![a-z])(?:" + "|".join(w2 for j, w2 in enumerate(mod.PAYMENT_LEXICON) if j != i) + ")(?![a-z])"),
                    ),
                    "label",
                )
            )
    m.append(patched("change notice: 'new' words removed", "_CHANGE", "(?:new|changed?", "(?:zzz|zzzz?"))
    m.append(
        custom(
            "change notice: second direction removed",
            lambda mod: setattr(mod, "_CHANGE", re.compile(mod._CHANGE.pattern.split("|(?<![a-z])(?:" + mod.CHANGE_WHAT)[0])),
        )
    )
    m.append(
        custom(
            "change notice: first direction removed",
            lambda mod: setattr(
                mod,
                "_CHANGE",
                re.compile("(?<![a-z])(?:" + mod.CHANGE_WHAT + mod._CHANGE.pattern.split("|(?<![a-z])(?:" + mod.CHANGE_WHAT, 1)[1]),
            ),
        )
    )
    for w in ("invoice", "inv", "po", "date", "order"):
        m.append(
            patched(f"id label word {w} removed", "_IDLABEL", f"(?:{w}|" if w == "invoice" else f"|{w}|", "(?:" if w == "invoice" else "|")
        )
    return m


# retired in round 7: the code they patched was rewritten (each has a replacement in round7(), with its killing test named there)
RETIRED2 = frozenset(
    [
        "phone span stops at no letter",
        "phone span stops at digits too",
        "phone span: number must start inside it",
        "look-alike digits not read (D12)",
        "hex not decoded",
        "encodings not decoded",
        "keyword line: blocks alone not candidates",
        "keyword line: joined run not a candidate",
        "bare threshold stays 8",
        "bare threshold 6 without components",
        "6-7 digits: unbroken test removed",
        "6-7 digits: unbroken test always true",
        "6-7 digits: block ok test removed",
        "ids: adjacency not required",
        "ids: one adjacent occurrence is enough",
        "ids: crossing runs count as labelled",
        "ids: cross-line test removed (all stream runs)",
        "ids: cross-line test inverted",
        "amounts: explain on payment lines too",
        "amounts: never explain",
        "D10: id skip removed",
        "D10: id skip without adjacency",
        "D10: equality becomes substring",
        "D10: ids ignored in check",
        "notices dropped from check_reasons",
        "spaced short run: year test removed",
        "spaced short run: year test inverted",
        "spaced short run: joined run year test removed",
        "spaced short run: joined run never",
        "next line threshold = label threshold",
        "next line threshold always 8",
        "lexicon-only threshold = bare",
        "YEAR_START 19 only",
        "YEAR_START 20 only",
        "payment line notice: document-wide again",
        "payment line notice: label counts as served",
        "payment line notice: served never set",
        "D10: id skip needs a seen occurrence",
    ]
)


def round6(ic) -> list[Mutant]:
    """One mutant per new branch of round 6 (C1-C5, A1-A6) and the replacements of the retired round-5 mutants."""
    mut = textual
    m: list[Mutant] = [
        # C1 / C2: identifier explanations
        mut(
            "ids: adjacency not required",
            "occ[v] = occ.get(v, True) and before is not None and _IDADJ.search(before) is not None",
            "occ[v] = True",
        ),
        mut(
            "ids: one adjacent occurrence is enough",
            "occ[v] = occ.get(v, True) and before is not None and _IDADJ.search(before) is not None",
            "occ[v] = occ.get(v, False) or (before is not None and _IDADJ.search(before) is not None)",
        ),
        mut(
            "ids: crossing runs count as labelled",
            "runs.append((-1, core, forms, False, None))",
            "runs.append((-1, core, forms, False, 'invoice '))",
        ),
        mut("ids: cross-line pass removed", "for start, core, forms, end in _backstop_runs(stream):", "for start, core, forms, end in []:"),
        mut(
            "ids: cross-line test removed (all stream runs)",
            "bisect_right(starts, start) != bisect_right(starts, max(start, end - 1))",
            "True",
        ),
        mut(
            "ids: cross-line test inverted",
            "bisect_right(starts, start) != bisect_right(starts, max(start, end - 1))",
            "bisect_right(starts, start) == bisect_right(starts, max(start, end - 1))",
        ),
        mut("ids: a run that is not explained still reported", "            if any(occ[v] for v in forms & ids):", "            if False:"),
        mut("ids: any id explains", "            if any(occ[v] for v in forms & ids):", "            if forms & ids:"),
        mut("amounts: explain on payment lines too", "if forms & known and not (i >= 0 and bad[i]):", "if forms & known:"),
        mut("amounts: never explain", "if forms & known and not (i >= 0 and bad[i]):", "if False:"),
        mut("on-file ignored by D12", "            if silent or forms & comps:", "            if silent:"),
        mut("phone silence ignores payment verbs", "silent = not near[i] and not verb[i] and any(", "silent = not near[i] and any("),
        mut("phone silence ignores bank words", "silent = not near[i] and not verb[i] and any(", "silent = not verb[i] and any("),
        mut("phone span run only next to a bank word", "                if near[i] or verb[i]:", "                if near[i]:"),
        mut("phone span run never", "                if near[i] or verb[i]:", "                if False:"),
        mut("payment verb list: into removed", "|credit|into|standing)", "|credit|standing)"),
        mut("payment verb list: standing removed", "|credit|into|standing)", "|credit|into)"),
        mut("payment verb list: settle removed", "|deposit|settle|wire|", "|deposit|wire|"),
        mut("payment verb list: pay removed", "(?:pay|pays|paid", "(?:pays|paid"),
        # D10 side
        mut("ids: standing order explains", "(?<!standing )(?<!standing-)order", "order"),
        mut("D10: id skip removed", "if c not in comps and not _id_explained(c, lines, at, ids):", "if c not in comps:"),
        mut(
            "D10: id skip without adjacency", "                    if not _IDADJ.search(v[:start][-40:]):", "                    if False:"
        ),
        mut("D10: id skip needs a seen occurrence", "    return seen\n", "    return True\n"),
        mut(
            "D10: equality becomes substring",
            "if c not in comps and not _id_explained(",
            "if not any(c in k or k in c for k in comps) and not _id_explained(",
        ),
        mut(
            "D10: ids ignored in check",
            "            if bank_detail_findings(send_text, on_file, ids):",
            "            if bank_detail_findings(send_text, on_file):",
        ),
        mut(
            "check_failed notice not emitted (D10)", 'notes.append(Notice("check_failed", "D10", NOTICE_MESSAGES["check_failed"]))', "pass"
        ),
        mut(
            "check_failed notice not emitted (D12)",
            'notes.append(Notice("check_failed", BACKSTOP_FLAG, NOTICE_MESSAGES["check_failed"]))',
            "pass",
        ),
        mut(
            "notices not part of check",
            "if unexplained_numbers(fields, send_text, on_file) or found:",
            "if unexplained_numbers(fields, send_text, on_file):",
        ),
        mut("numbers not part of check", "if unexplained_numbers(fields, send_text, on_file) or found:", "if found:"),
        mut("notices dropped from check_reasons", "            notes += found", "            pass"),
        # C3 / C4 thresholds
        mut("spaced short run: year test removed", "or not _YEAR_START.match(b)", "or True"),
        mut("spaced short run: year test inverted", "or not _YEAR_START.match(b)", "or _YEAR_START.match(b)"),
        mut(
            "spaced short run: joined run year test removed",
            'or kind == "strong" or not _YEAR_START.match(whole)):',
            'or kind == "strong" or True):',
        ),
        mut(
            "spaced short run: joined run never",
            'and (len(whole) >= THRESHOLD_BARE or kind == "strong" or not _YEAR_START.match(whole)):',
            'and (len(whole) >= THRESHOLD_BARE or kind == "strong"):',
        ),
        mut("next line threshold = label threshold", 'far = thr if kind == "strong" else THRESHOLD_BARE', "far = thr"),
        mut("next line threshold always 8", 'far = thr if kind == "strong" else THRESHOLD_BARE', "far = THRESHOLD_BARE"),
        mut("lexicon-only threshold = bare", 'return THRESHOLD_BARE, "pay"', 'return bare, "pay"'),
        mut("lexicon class removed", "        if _KPAY.search(text):", "        if False:"),
        mut("bank class removed", "        if _KBANK.search(text):", "        if False:"),
        mut("YEAR_START 19 only", '_YEAR_START = re.compile("(?:19|20)[0-9]{2}")', '_YEAR_START = re.compile("(?:19)[0-9]{2}")'),
        mut("YEAR_START 20 only", '_YEAR_START = re.compile("(?:19|20)[0-9]{2}")', '_YEAR_START = re.compile("(?:20)[0-9]{2}")'),
        # C5
        mut("bidi: notice removed", "        if (at or labels) and any(c in _BIDI for c in u):", "        if False:"),
        mut(
            "bidi: notice without a payment line",
            "        if (at or labels) and any(c in _BIDI for c in u):",
            "        if any(c in _BIDI for c in u):",
        ),
        mut(
            "bidi: notice needs a candidate",
            "        if (at or labels) and any(c in _BIDI for c in u):",
            "        if at and any(c in _BIDI for c in u):",
        ),
        mut(
            "bidi: notice needs a label",
            "        if (at or labels) and any(c in _BIDI for c in u):",
            "        if labels and any(c in _BIDI for c in u):",
        ),
        # A1 per-line notice, change notice
        mut("payment line notice removed", "            if lone:", "            if False:"),
        mut(
            "payment line notice: document-wide again",
            "lone = [i for i in labels if i not in served] if PAYMENT_LINE_NEEDS_LABEL",
            "lone = ([] if at else labels) if PAYMENT_LINE_NEEDS_LABEL",
        ),
        mut(
            "payment line notice: label counts as served",
            "                served.add(label)",
            "                served.add(label); served.update(at)",
        ),
        mut("payment line notice: served never set", "                served.add(label)", "                pass"),
        mut(
            "payment line notice needs an on-file record",
            "        if on_file:\n            if not _bics(onf)",
            "        if True:\n            if not _bics(onf)",
        ),
        mut("change notice removed", 'if m := _CHANGE.search(" ".join(lines)):', "if False:"),
        mut("change notice: lines not joined", 'if m := _CHANGE.search(" ".join(lines)):', "if m := _CHANGE.search(lines[0]):"),
        # A2 table separators
        mut("separator rows count as lines", "if _HAS_ALNUM.search(lines[j])", "if lines[j].strip()"),
        # A3 lexicon, reference words
        mut("ref/vat/abn skip short runs", 'return m.group(1) not in ("ref", "vat", "abn") or ndigits >= THRESHOLD_BARE', "return True"),
        mut(
            "ref/vat/abn skip nothing",
            'return m.group(1) not in ("ref", "vat", "abn") or ndigits >= THRESHOLD_BARE',
            "return m.group(1) not in ('ref', 'vat', 'abn')",
        ),
        mut("ref/vat/abn length 8 -> 12", "or ndigits >= THRESHOLD_BARE", "or ndigits >= 12"),
        # A4 slash dates
        mut("slash dates not masked", "    t = _SLASH_DATE.sub(_mask_date, t)", "    pass"),
        mut(
            "slash dates: any numbers masked",
            'return "x" * len(m.group()) if _ok_dm(m.group(1), m.group(2)) else m.group()',
            'return "x" * len(m.group())',
        ),
        mut("slash dates: 2-digit years not masked", "((?:19|20)?[0-9]{2})(?![0-9/])", "((?:19|20)[0-9]{2})(?![0-9/])"),
        mut("slash dates: 1-digit day not masked", "(?<![0-9/])([0-9]{1,2})/([0-9]{1,2})/", "(?<![0-9/])([0-9]{2})/([0-9]{1,2})/"),
        mut("slash dates: 1-digit month not masked", "/([0-9]{1,2})/((?:19|20)?", "/([0-9]{2})/((?:19|20)?"),
        # A5 company names
        mut(
            "swift always a label",
            '"(?<![a-z])swift(?![a-z])(?=" + _NA + "{0,3}(?:code|address|number|no|id)(?![a-z])|"',
            '"(?<![a-z])swift(?![a-z])(?=" + _NA + "{0,3}(?:code|address|number|no|id)(?![a-z])|" + "|"',
        ),
        mut(
            "clearing always a label",
            '"(?<![a-z])clearing(?![a-z])(?=" + _NA + "{0,3}(?:no|nr|num|number|code|id)(?![a-z])|"',
            '"(?<![a-z])clearing(?![a-z])(?=" + _NA + "{0,3}(?:no|nr|num|number|code|id)(?![a-z])|" + "|"',
        ),
        mut("routing stem anywhere", '"sort" + _GAP + "code|(?<![a-z])routing|"', '"sort" + _GAP + "code|routing|"'),
    ]
    for w in (
        "pesa",
        "rachunek",
        "numer",
        "payable",
        "credit",
        "mobile",
        "p/c",
        "ac",
    ):  # lexicon words added in round 6, one each
        m.append(
            custom(
                f"lexicon round 6: {w} removed",
                lambda mod, w=w: setattr(
                    mod, "_KPAY", re.compile("(?<![a-z])(?:" + "|".join(x for x in mod.PAYMENT_LEXICON if w not in x) + ")(?![a-z])")
                ),
                "a3",
            )
        )
    for w in ("different", "another", "changed", "banks?"):  # change-notice alternatives
        m.append(patched(f"change notice alternative {w} removed", "_CHANGE", w, "zzzzq"))
    return m


def round7(ic) -> list[Mutant]:
    """Mutants of round 7. Each name ends with `[killer: test name]`; the full run proves the named test (or another) kills it."""
    mut = textual
    m: list[Mutant] = [
        mut(
            "r7 ids: explained on a payment line [killer: test_b1_identifier_equal_to_the_account...]",
            "and not (kw[first] or verb[first]) and _IDADJ.search(before) is not None",
            "and _IDADJ.search(before) is not None",
        ),
        mut(
            "r7 ids: adjacency not needed [killer: test_b1_identifier_still_explains... / test_c1]",
            "and _IDADJ.search(before) is not None\n                occ[v]",
            "and True\n                occ[v]",
        ),
        mut(
            "r7 ids: one occurrence is enough [killer: test_b1_identifier_still_explains_a_label_free_line]",
            "occ[v] = occ.get(v, True) and ok",
            "occ[v] = occ.get(v, False) or ok",
        ),
        mut(
            "r7 ids: any id explains [killer: test_c1 / test_b1]",
            "            if any(occ[v] for v in forms & ids):",
            "            if forms & ids:",
        ),
        mut(
            "r7 ids D10: bad line explains [killer: test_b1 quote invoice 20260345]",
            "if _line_is_bad(v) or not _IDADJ.search(v[:start][-40:]):",
            "if not _IDADJ.search(v[:start][-40:]):",
        ),
        mut(
            "r7 ids D10: adjacency not needed [killer: test_b1_the_records_own_number_on_a_payment_line_is_exactly_d12]",
            "if _line_is_bad(v) or not _IDADJ.search(v[:start][-40:]):",
            "if _line_is_bad(v):",
        ),
        mut(
            "r7 ids D10: unseen counts as explained [killer: test_survivor_id_explained_needs_a_seen_occurrence]",
            "    return seen\n",
            "    return True\n",
        ),
        mut(
            "r7 ids: becomes D10 [killer: test_b1_the_records_own_number_on_a_payment_line_is_exactly_d12]",
            "            if c in ids:\n                if not _id_explained",
            "            if False:\n                if not _id_explained",
        ),
        mut(
            "r7 cross-line run not collected [killer: test_c2 / test_cm2]",
            "            if len(core) >= BACKSTOP_MIN_DIGITS and a != z:",
            "            if False:",
        ),
        mut("r7 cross-line test inverted [killer: test_c2]", "and a != z:", "and a == z:"),
        mut(
            "r7 cross-line run counted as labelled [killer: test_c2]",
            "runs.append((a, z, core, forms, False, None))",
            "runs.append((a, z, core, forms, False, 'invoice '))",
        ),
        mut(
            "r7 amounts explain on payment lines [killer: test_cm2_amount_does_not_launder...]",
            "if forms & known and not any(bad[k] for k in range(first, last + 1)):",
            "if forms & known:",
        ),
        mut(
            "r7 amounts: only the first line counts [killer: test_cm2 cross-line]",
            "not any(bad[k] for k in range(first, last + 1))",
            "not bad[first]",
        ),
        mut(
            "r7 amounts: never explain [killer: test_cm2 Total due]",
            "if forms & known and not any(bad[k] for k in range(first, last + 1)):",
            "if False:",
        ),
        mut("r7 above ignores verbs [killer: test_cm2 send funds to:]", "above = [any((kw[k] or verb[k]) and", "above = [any((kw[k]) and"),
        mut("r7 tax label ignored [killer: test_taxlabel_identifiers...]", "and _TAXLABEL.search(before):", "and False:"),
        mut(
            "r7 tax label on payment line [killer: test_taxlabel Bank VAT]",
            "if before is not None and first == last and not (kw[first] or verb[first]) and _TAXLABEL.search(before):",
            "if before is not None and first == last and _TAXLABEL.search(before):",
        ),
        mut(
            "r7 html views never [killer: test_b2_markup_cannot_split_a_number]",
            '    if "<" not in text or not _ANY_TAG.search(text):\n        return []',
            "    if True:\n        return []",
        ),
        mut("r7 html comments kept [killer: test_b2 comment]", '    t = _COMMENT.sub("", text)', "    t = text"),
        mut(
            "r7 hidden elements kept in the visible view [killer: test_b2 display:none]",
            'for u in (_HIDDEN_EL.sub("", t), t):',
            "for u in (t, t):",
        ),
        mut(
            "r7 block tags not line breaks [killer: test_html_views_directly]",
            '_ANY_TAG.sub("", _BLOCK_TAG.sub(chr(10), u))',
            '_ANY_TAG.sub("", _BLOCK_TAG.sub("", u))',
        ),
        mut(
            "r7 hidden notice never [killer: test_b2_hidden_elements_are_a_notice]",
            '    if _HIDDEN_EL.search(_COMMENT.sub("", send_text)):',
            "    if False:",
        ),
        mut(
            "r7 separator look-alikes ignored [killer: test_b3]",
            "t = t.translate(_SEPLIKE).translate(_DINGBAT)",
            "t = t.translate(_DINGBAT)",
        ),
        mut("r7 dingbat digits ignored [killer: test_m6]", "t = t.translate(_SEPLIKE).translate(_DINGBAT)", "t = t.translate(_SEPLIKE)"),
        mut("r7 numerals need 3 [killer: test_m6]", '{4,}")', '{3,}")'),
        mut("r7 numerals need 5 [killer: test_m6]", '{4,}")', '{5,}")'),
        mut(
            "r7 digits to ASCII late [killer: test_m2 Arabic-Indic digits]",
            "    t = _digits_ascii(t)  # every decimal digit",
            "    pass  # every decimal digit",
        ),
        mut(
            "r7 foreign lexicon not folded [killer: test_m2 languages]",
            "return w if w.isascii() else re.escape(_f(w))",
            "return w if w.isascii() else re.escape(w)",
        ),
        mut(
            "r7 non-latin rule never [killer: test_non_latin_context_needs_eight_digits]",
            "if not thr and i in nonlatin and _LONGRUN.search(line):",
            "if False:",
        ),
        mut(
            "r7 non-latin rule on every line [killer: test_non_latin_context_needs_eight_digits]",
            "if not thr and i in nonlatin and _LONGRUN.search(line):",
            "if not thr and i in nonlatin:",
        ),
        mut("r7 all hits are D10 [killer: test_m3]", "            elif c in strong or len(c) >= THRESHOLD_BARE:", "            elif True:"),
        mut(
            "r7 strong hits not D10 [killer: test_m3_strong_labels_and_eight_digits_stay_d10]",
            "            elif c in strong or len(c) >= THRESHOLD_BARE:",
            "            elif len(c) >= THRESHOLD_BARE:",
        ),
        mut(
            "r7 7 digits are D10 [killer: test_m3]",
            "            elif c in strong or len(c) >= THRESHOLD_BARE:",
            "            elif c in strong or len(c) >= 7:",
        ),
        mut(
            "r7 9 digits for D10 [killer: test_m3 Account: 87654321]",
            "            elif c in strong or len(c) >= THRESHOLD_BARE:",
            "            elif c in strong or len(c) >= 9:",
        ),
        mut(
            "r7 next line needs 8 digits [killer: test_m3 Bank: Westpac]",
            "add(_line_candidates(lines[j], thr, kind, money_ok=not _AMOUNT_WORD.search(lines[j])), sg, i, j)",
            "add(_line_candidates(lines[j], THRESHOLD_BARE, kind, money_ok=not _AMOUNT_WORD.search(lines[j])), sg, i, j)",
        ),
        mut("r7 last label is the first [killer: test_m1_cells_one_per_line]", "region = txt[max(hits) :]", "region = txt[min(hits) :]"),
        mut(
            "r7 lookahead 2 lines [killer: test_unserved_value_window]",
            "        for _ in range(3):\n            nj",
            "        for _ in range(2):\n            nj",
        ),
        mut(
            "r7 lookahead 4 lines [killer: test_unserved_value_window]",
            "        for _ in range(3):\n            nj",
            "        for _ in range(4):\n            nj",
        ),
        mut(
            "r7 table rows are values [killer: test_unserved_amount_rows]",
            "cache[j] = not _MONEY.search(lines[j]) and _has_value(lines[j])",
            "cache[j] = _has_value(lines[j])",
        ),
        mut(
            "r7 number above ignored [killer: test_unserved_value_window]",
            "        if i > 0 and lines[i - 1].strip() and _NUMBER_ONLY",
            "        if False and _NUMBER_ONLY",
        ),
        mut(
            "r7 every bank word is a label [killer: test_m1_honest_layouts]",
            "if rx in (_K8, _KBANK) and not _SHAPED.match(t, m.end()):",
            "if False:",
        ),
        mut("r7 dates are plain gaps [killer: test_cm1]", '"date" if _date_value(region) else "none"', '"none"'),
        mut(
            "r7 money rows in has_value [killer: test_unserved_amount_rows]",
            '"strong", money_ok=False)',
            '"strong", money_ok=True)',
        ),
        mut(
            "r7 K6 not a label for the notice [killer: test_unserved_amount_rows_and_shape_and_each_label_class Sort code]",
            "            for rx in (_K6, _K8, _KBANK, _KPAY):",
            "            for rx in (_K8, _KBANK, _KPAY):",
        ),
        mut(
            "r7 K8 not a label for the notice [killer: Account:]",
            "            for rx in (_K6, _K8, _KBANK, _KPAY):",
            "            for rx in (_K6, _KBANK, _KPAY):",
        ),
        mut(
            "r7 KBANK not a label for the notice [killer: Bank details:]",
            "            for rx in (_K6, _K8, _KBANK, _KPAY):",
            "            for rx in (_K6, _K8, _KPAY):",
        ),
        mut(
            "r7 KPAY not a label for the notice [killer: PayPal:]",
            "            for rx in (_K6, _K8, _KBANK, _KPAY):",
            "            for rx in (_K6, _K8, _KBANK):",
        ),
        mut("r7 quoted text ignored [killer: test_adv_m4]", 'ln.lstrip().startswith(">")', "False"),
        mut(
            "r7 size limit off by one [killer: test_size_limit_boundary]",
            "    if len(send_text) > MAX_TEXT_CHARS:",
            "    if len(send_text) >= MAX_TEXT_CHARS:",
        ),
        mut("r7 size limit never [killer: test_cm2_text_over_the_limit]", "    if len(send_text) > MAX_TEXT_CHARS:", "    if False:"),
        mut(
            "r7 raw cut at the limit [killer: test_size_limit_boundary_and_raw_limit_boundary]",
            "    if len(out) <= RAW_MAX:",
            "    if len(out) < RAW_MAX:",
        ),
        mut(
            "r7 raw always cut [killer: test_decision1_raw_lines_are_never_trimmed]",
            "    if len(out) <= RAW_MAX:",
            "    if len(out) <= 20:",
        ),
        mut(
            "r7 MIME soft break not removed [killer: test_m5]",
            '_QP = re.compile(r"=[0-9A-F]{2}|=\\r?\\n")',
            '_QP = re.compile(r"=[0-9A-F]{2}")',
        ),
        mut("r7 base64 lines not joined [killer: test_m4]", "            if j > k:", "            if False:"),
        mut("r7 GB sort code not a component [killer: test_adv_m1]", "comps.update({c[8:14], c[14:]})", "comps.update({c[14:]})"),
        mut("r7 GB account not a component [killer: test_adv_m1]", "comps.update({c[8:14], c[14:]})", "comps.update({c[8:14]})"),
        mut("r7 GB rule never [killer: test_adv_m1]", 'if c.startswith("gb") and len(c) == 22', 'if c.startswith("zz") and len(c) == 22'),
        mut(
            "r7 verb lines keep 3-digit blocks [killer: test_cm5 / test_verb_lines]",
            "2 if verb[i] else BACKSTOP_MIN_BLOCK",
            "BACKSTOP_MIN_BLOCK",
        ),
        mut(
            "r7 verb lines read 1-digit blocks [killer: test_verb_lines_read_two_digit]",
            "2 if verb[i] else BACKSTOP_MIN_BLOCK",
            "1 if verb[i] else BACKSTOP_MIN_BLOCK",
        ),
        mut(
            "r7 phone run need not be inside the span [killer: test_adv_m3]",
            "any(lo < start < hi and end <= hi for lo, hi, _ in spans)",
            "any(lo < start < hi for lo, hi, _ in spans)",
        ),
        mut("r7 phone span ignores commas [killer: test_phone_span_stops_at_the_comma]", 'r"[^a-z\\n,;]*"', 'r"[^a-z\\n]*"'),
        mut(
            "r7 unexplained notice dropped [killer: test_m7]",
            "            notes += numbers + found_notes",
            "            notes += found_notes",
        ),
        mut(
            "r7 notices dropped [killer: test_survivor_check_reasons_returns_the_notices]",
            "            notes += numbers + found_notes",
            "            notes += numbers",
        ),
        mut("r7 numbers do not raise D12 [killer: test_m7]", "            if numbers or found_notes:", "            if found_notes:"),
        mut(
            "r7 weak notices dropped [killer: test_m3]",
            "        for n in _weak if _weak is not None else _scan(send_text, on_file, ids)[1]:",
            "        for n in []:",
        ),
        mut("r7 shaped: letter after a bank word counts [killer: test_m1_honest_layouts]", 'r"\\s*(?:(?:details?', 'r"(?:(?:details?'),
        mut(
            "r7 tax: 3 letters not enough [killer: test_taxlabel VAT: GB]",
            "[a-z0-9]{1,3}[^a-z0-9]{0,3})?$",
            "[a-z0-9]{1,1}[^a-z0-9]{0,3})?$",
        ),
        mut(
            "r7 visible controls not shown [killer: test_decision1]",
            'return "".join(c if c.isprintable() else f"<U+{ord(c):04X}>" for c in txt)',
            'return "".join(c for c in txt)',
        ),
        mut("r7 payment verb: transfer removed [killer: test_survivor each verb]", "|transfer|transfers|", "|transfers|"),
        mut("r7 payment verb: payable kept [killer: test_cm2 Total payable]", "|payments|remit|", "|payments|payable|remit|"),
    ]
    for i, _w in enumerate(ic.PAYMENT_LEXICON):  # every lexicon entry, one at a time; killer: test_lexicon_has_one_sample_per_entry
        m.append(
            custom(
                f"r7 lexicon entry {i} removed [killer: test_lexicon_has_one_sample_per_entry]",
                lambda mod, i=i: setattr(
                    mod,
                    "_KPAY",
                    re.compile(
                        "(?<![a-z])(?:" + "|".join(mod._lex_entry(x) for j, x in enumerate(mod.PAYMENT_LEXICON) if j != i) + ")(?![a-z])"
                    ),
                ),
                "lexicon",
            )
        )
    for cp in (0x1C0, 0x1C1, 0x1C2, 0x1C3, 0x5C0, 0x5C3, 0x2223, 0x2502, 0x23D0, 0xFF5C):
        m.append(
            custom(
                f"r7 separator look-alike U+{cp:04X} removed [killer: test_b3_every_separator_look_alike]",
                lambda mod, cp=cp: mod._SEPLIKE.pop(cp, None),
            )
        )
    for cp in sorted(ic._DINGBAT):
        m.append(
            custom(
                f"r7 dingbat digit U+{cp:04X} removed [killer: test_m6_every_circled_digit]", lambda mod, cp=cp: mod._DINGBAT.pop(cp, None)
            )
        )
    return m


def run_pytest(k: str = "") -> tuple[int, str, str]:
    """(exit code, first failing test or error line, last summary line)."""
    for key in [key for key in sys.modules if key.startswith(("test_invoicecheck", "forgeries2"))]:
        del sys.modules[key]
    buf = io.StringIO()
    args = [
        "-q",
        "-x",
        "--tb=no",
        "-rfE",
        "-p",
        "no:cacheprovider",
        # timing tests are not logic tests: they cost 100 of the 110 seconds of a full run and no mutant is aimed at them
        "--deselect",
        "tests/test_invoicecheck.py::test_scaling_is_linear",
        "--deselect",
        "tests/test_invoicecheck_round5.py::test_large_inputs_stay_bounded",
        "--deselect",
        "tests/test_invoicecheck_round6.py::test_c5_change_notice_regex_is_fast",
        str(ROOT / "tests" / "test_invoicecheck.py"),
        str(ROOT / "tests" / "test_invoicecheck_round5.py"),
        str(ROOT / "tests" / "test_invoicecheck_round6.py"),
        str(ROOT / "tests" / "test_invoicecheck_round7.py"),
    ]
    if k:
        args[0:0] = ["-k", k]
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = pytest.main(args)
    lines = [x for x in buf.getvalue().splitlines() if x.strip()]
    first = next((x for x in lines if x.startswith(("FAILED ", "ERROR "))), "")
    return int(rc), first.split(" - ")[0], (lines[-1] if lines else "")


def install(src: str, patch) -> None:
    import intake

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "invoicecheck.py"
        path.write_text(src, encoding="utf-8", newline=chr(10))
        spec = importlib.util.spec_from_file_location("intake.invoicecheck", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["intake.invoicecheck"] = mod
        spec.loader.exec_module(mod)
    mod.__file__ = str(SRC)  # the tests scan the real source folder through ic.__file__
    if patch is not None:
        patch(mod)
    intake.invoicecheck = mod


def main(argv: list[str]) -> int:
    only = [x for x in (argv[argv.index("--only") + 1] if "--only" in argv else "").split(",") if x]
    sample = int(argv[argv.index("--sample") + 1]) if "--sample" in argv else 24
    sys.path.insert(0, str(ROOT / "src"))
    import intake  # noqa: F401

    orig = SRC.read_text(encoding="utf-8")
    install(orig, None)
    rc, first, summary = run_pytest()
    print(
        f"baseline :: rc={rc} {summary} (three timing tests are deselected: tests/test_invoicecheck.py::test_scaling_is_linear, tests/test_invoicecheck_round5.py::test_large_inputs_stay_bounded, tests/test_invoicecheck_round6.py::test_c5_change_notice_regex_is_fast)"
    )
    if rc != 0:
        return 2
    counts = {"KILLED": 0, "SURVIVED": 0, "UNOBSERVABLE": 0, "CRASH": 0, "COLLECTION": 0}
    bad = []
    chosen = build(sample)
    if "--part" in argv:  # --part I/N: every N-th mutant starting at I (run N processes side by side)
        i, n = (int(x) for x in argv[argv.index("--part") + 1].split("/"))
        chosen = chosen[i::n]
    if "--from" in argv:  # --from K: skip the first K mutants of the (partitioned) list, to resume a run
        chosen = chosen[int(argv[argv.index("--from") + 1]) :]
    if "--random" in argv:  # a random subset (seeded, so the run can be repeated)
        import random

        chosen = random.Random(int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 1).sample(
            chosen, int(argv[argv.index("--random") + 1])
        )
    for name, repl, patch, k in chosen:
        if only and not any(o in name for o in only):
            continue
        src = orig
        status, detail = "", ""
        try:
            for old, new in repl:
                if old not in src:
                    raise AssertionError(f"pattern not found: {old[:70]!r}")
                src = src.replace(old, new, 1)
            install(src, patch)
            rc, first, summary = run_pytest(k)
            if rc == 0:
                status, detail = "SURVIVED", summary
            elif rc == 1:
                status, detail = "KILLED", first or summary
            elif rc == 2:
                status, detail = "COLLECTION", first or summary
            else:
                status, detail = "CRASH", f"pytest exit {rc}: {summary}"
        except Exception as e:  # noqa: BLE001
            status, detail = "CRASH", f"{type(e).__name__}: {str(e)[:120]}"
        finally:
            install(orig, None)
        if status == "SURVIVED" and name in UNOBSERVABLE:
            status = "UNOBSERVABLE"
        counts[status] = counts.get(status, 0) + 1
        if status not in ("KILLED", "UNOBSERVABLE"):
            bad.append(name)
        print(f"{status:<10} {name} :: {detail}".encode("ascii", "backslashreplace").decode("ascii"), flush=True)
    install(orig, None)
    rc, first, summary = run_pytest()
    print(f"restore proof (unchanged module, after the loop) :: rc={rc} {summary}")
    print(f"total: {counts}; not killed: {bad}")
    return 0 if not bad and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
