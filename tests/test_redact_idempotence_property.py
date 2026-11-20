"""Property tests for the redactor around core-c's G7 fix (non-builder tests, written by core-a).

G7 (ticket handover/core-c/tickets/G7-context-after-sweep.md on cloud/core-c): line 1 names a bank code, line 2
writes `<same code>/<account>`. The pattern pass masked the code on line 1, the final sweep wrote its placeholder
on line 2, and the account pattern (which needs that placeholder) had already run: one pass left the account
readable. The fix runs the two account patterns again after the sweep (`_Redactor.settle`). The same commit added
a rule to `_mask`: a value made only of ESCAPED placeholder look-alikes is not a new secret (untrusted redaction
run over its own output added a junk entry to the run map).

The ticket's invariants, numbered here in the ticket's order:
  I1  one pass gives exactly what two passes of the old path gave, for the context patterns
  I2  a second redact() / redact_text pass over the output changes neither text nor map for these shapes
  I3  text without a bank-code placeholder: byte-identical result and map to the old path
  I4  never returns a text when the context patterns can still find a value
  I5  `_sweep_copies=False` (find only) is unchanged
  I6  (follow-up) untrusted redaction over its own output adds no map entry

The properties of this file (each test names the invariant it checks):
  P1 idempotence, same map and fresh map      P5 concatenation and context (the ticket's shape, varied)
  P2 the map only grows, placeholders stable  P6 generated text with planted values of every detector kind
  P3 no placeholder is redacted or split      P7 hostile text
  P4 restore gives the text back

Overlap with core-c's own tests/test_redact_context_after_sweep.py: that file pins EXACT outputs for six named
shapes (direct, keyword, swept-elsewhere, two-codes, sort-code, no-bank), the table guard, the round bound, the
signatures and timing. Nothing of that is repeated. This file states properties instead and runs them over every
corpus the repository has, over a grid built from the ticket's failing example (7 code keywords x 15 links between
code and account x 8 separators between the two lines x 4 layouts), and over fixed-seed generated text. The only
shared ground is the ticket's own example, which is one point of that grid.

Marks. A property that fails on a redactor WITHOUT G7 and passes with it carries `needs_g7` (strict xfail when the
fix is absent, detected by `_CONTEXT_PATTERNS` / `_Redactor.settle` / `_ESCAPED_LOOKALIKE`). A property that fails
WITH the fix is a finding: strict xfail with the reason `FINDING G7-Fn`, smallest example in
handover/core-a/FINDINGS-core-c-G7-redaction.md. No property was weakened to pass.

Every sensitive-looking value is made up and built from parts or drawn from a fixed-seed generator.
"""

from __future__ import annotations

import collections
import functools
import importlib
import itertools
import json
import pathlib
import random
import re
import string

import pytest

from hadavin_sdk.guard import runmap

R = importlib.import_module("hadavin_sdk.guard.redact")  # the package re-exports a function of this name

HAS_G7 = hasattr(R, "_CONTEXT_PATTERNS") and hasattr(R._Redactor, "settle")
HAS_OWN_OUTPUT_RULE = hasattr(R, "_ESCAPED_LOOKALIKE")
_NEEDS = "needs core-c G7 fix (not on this branch yet)"
needs_g7 = pytest.mark.xfail(not HAS_G7, strict=True, reason=_NEEDS)
needs_own_output_rule = pytest.mark.xfail(not HAS_OWN_OUTPUT_RULE, strict=True, reason=_NEEDS)

F1 = (
    "FINDING G7-F1 (the ticket's own RELATED, NOT FIXED): a short token after Bearer / Basic / authorization "
    "that starts with a known secret is masked whole only by a second pass"
)
F2 = (
    "FINDING G7-F2: an identifier glued to a copy of a known secret (no separator) stays readable after one pass; "
    "the sweep masks the secret, and only a second pass then reads the identifier at its new boundary"
)
F3 = "FINDING G7-F3: a phone number directly followed by a full stop is not masked (PHONE ends with `(?![\\w.])`)"

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXTNORM = ROOT / "tests" / "fixtures" / "textnorm_corpus.json"
SEED = 20261120
LABELS = tuple(dict.fromkeys(label for label, _ in R.PATTERNS))


# --- shared helpers ----------------------------------------------------------------------------------------------


def _old_one_pass(text: str, mapping: dict[str, str] | None = None) -> tuple[str, dict[str, str]]:
    """The path `redact()` took before G7: the pattern pass, then one sweep (both are unchanged by G7)."""
    r = R._Redactor(mapping)
    return r.sweep(r.find(text)), r.mapping


def _plain(text: str, mapping: dict[str, str]) -> str:
    """Every placeholder of `mapping` put back, in one step (never expanded again)."""
    return runmap.PLACEHOLDER.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)


Passes = collections.namedtuple("Passes", "x o1 h1 o2 h2 o3 h3")


def _passes(text: str, fn=runmap.redact_text) -> Passes:
    """Three passes with ONE run map: the text and a copy of the map after each."""
    mapping = runmap.RunMap()
    o1 = fn(text, mapping)
    h1 = dict(mapping)
    o2 = fn(o1, mapping)
    h2 = dict(mapping)
    o3 = fn(o2, mapping)
    return Passes(text, o1, h1, o2, h2, o3, dict(mapping))


def _no_failures(failures: list, total: int) -> None:
    shown = "\n".join(repr(f)[:700] for f in failures[:4])
    assert not failures, f"{len(failures)} of {total} cases:\n{shown}"


def _map_problems(p: Passes) -> list[str]:
    """P2 and P3 for one case, whatever the text did: the map only grows, no entry changes, a value never gets a
    second placeholder, no stored value holds a placeholder of its own map, and the text behind the
    placeholders is the same after every pass (a placeholder that was redacted again, split or nested would
    restore to something else)."""
    problems = []
    for before, after, n in ((p.h1, p.h2, 2), (p.h2, p.h3, 3)):
        if any(after.get(k) != v for k, v in before.items()):
            problems.append(f"pass {n} lost or changed an entry")
        added = [v for k, v in after.items() if k not in before]
        if set(added) & set(before.values()) or len(set(added)) != len(added):
            problems.append(f"pass {n} gave a known value a second placeholder")
    if any(k in v for v in p.h3.values() for k in p.h3):
        problems.append("a stored value holds a placeholder of the same map")
    if not (_plain(p.o1, p.h1) == _plain(p.o2, p.h2) == _plain(p.o3, p.h3)):
        problems.append("the text behind the placeholders changed between passes")
    return problems


def _secret_placeholders(text: str) -> list[str]:
    return [m.group(0) for m in runmap.PLACEHOLDER.finditer(text) if m.group(1) in R.SECRET_KINDS]


def _is_fixed_point(p: Passes) -> bool:
    return p.o2 == p.o1 and p.h2 == p.h1


def _views_free(text: str) -> bool:
    """`redact_text` returns the text as written (no decoded view, nothing cleaned, no escape code cut)."""
    return text.isascii() and not any(c in text for c in "\\%&\x1b\x00")


# --- the corpora -------------------------------------------------------------------------------------------------


def _strings(value, path: str, out: dict[str, str]) -> None:
    if isinstance(value, str):
        out[path] = value
    elif isinstance(value, dict):
        for k, v in value.items():
            _strings(k, f"{path}.key[{len(out)}]", out)
            _strings(v, f"{path}.{str(k)[:24]}", out)
    elif isinstance(value, list | tuple):
        for i, v in enumerate(value):
            _strings(v, f"{path}.{i}", out)


@functools.cache
def _corpus() -> dict[str, str]:
    """Every corpus the repository has, as name -> text. The text-normaliser corpus only where its fixture
    exists (it arrives with the normaliser; `test_the_corpora_are_loaded` says so when it is absent)."""
    from tests import test_k1b_redaction as k1b
    from tests import test_k1b_redaction_layers as layers
    from tests.demo_askdata import corpus as askdata
    from tests.warden_port import privacy_corpus

    out: dict[str, str] = {}
    for kind, texts in privacy_corpus.MASKED.items():
        for i, text in enumerate(texts):
            out[f"privacy-{kind}-{i}"] = text
    for i, text in enumerate(privacy_corpus.KEPT):
        out[f"privacy-KEPT-{i}"] = text
    for attack in askdata.ATTACKS:
        out[f"askdata-attack-{attack.name}"] = attack.sql
    for i, (_, sql) in enumerate(askdata.BENIGN):
        out[f"askdata-benign-{i}"] = sql
    if TEXTNORM.exists():
        for row in json.loads(TEXTNORM.read_text(encoding="utf-8")):
            for side in ("a", "b"):
                if isinstance(row.get(side), str):
                    out[f"textnorm-{row['id']}-{side}"] = row[side]
    _strings(k1b.PARTS, "k1b-PARTS", out)
    out["k1b-LOG_MSG"] = k1b.LOG_MSG
    for name, text in layers.SPELLINGS.items():
        out[f"k1b-layers-{name}"] = text
    out["k1b-layers-percent"] = "x %41" + layers.AWS[1:] + " y"
    out["k1b-layers-entity"] = "x &#65;" + layers.AWS[1:] + " y"
    out["k1b-layers-percent-key"] = "x password%3D" + layers.PW + " y"
    return out


@functools.cache
def _corpus_passes() -> dict[str, Passes]:
    return {name: _passes(text) for name, text in _corpus().items()}


def test_the_corpora_are_loaded():
    sizes = collections.Counter(name.split("-")[0] for name in _corpus())
    assert sizes["privacy"] >= 60 and sizes["askdata"] >= 300 and sizes["k1b"] >= 40, sizes
    if not TEXTNORM.exists():
        pytest.skip("tests/fixtures/textnorm_corpus.json is not on this branch: that corpus is not run here")
    assert sizes["textnorm"] >= 300, sizes


def test_P1_I2_corpus_a_second_pass_with_the_same_map_changes_nothing():
    """`redact_text` with one run map, and the bare `redact()` with its own map passed on."""
    failures = [(n, p.o1, p.o2) for n, p in _corpus_passes().items() if not _is_fixed_point(p)]
    for name, text in _corpus().items():
        first = R.redact(text)
        second = R.redact(first.text, mapping=first.mapping)
        if (second.text, second.mapping) != (first.text, first.mapping):
            failures.append((name, "redact()", first.text, second.text))
    _no_failures(failures, 2 * len(_corpus()))


def test_P1_corpus_a_second_pass_with_a_fresh_map_changes_nothing():
    """NOT claimed by the ticket (it speaks of the same map); it holds on every corpus entry, so it is pinned.
    A fresh map is what an independent re-scan (the outbound gate) uses: it must find nothing left to mask."""
    failures = []
    for name, p in _corpus_passes().items():
        fresh = runmap.RunMap()
        again = runmap.redact_text(p.o1, fresh)
        if again != p.o1 or dict(fresh):
            failures.append((name, p.o1, again, dict(fresh)))
    _no_failures(failures, len(_corpus()))


def test_P2_P3_corpus_the_map_only_grows_and_no_placeholder_is_redacted_again():
    failures = [(n, probs, p.o1) for n, p in _corpus_passes().items() if (probs := _map_problems(p))]
    _no_failures(failures, len(_corpus()))


def test_P4_corpus_restore_gives_the_text_back_after_one_pass_and_after_two():
    """`RedactionResult.restore` (the bare redactor's own restore) and `runmap.restore_text` (stored kinds only;
    the rest is put back here from the map to compare). `redact()` cuts terminal escape codes first, so the
    text given back is the text without them."""
    failures = []
    checked = 0
    for name, text in _corpus().items():
        first = R.redact(text)
        second = R.redact(first.text, mapping=first.mapping)
        want = R.strip_ansi(text)
        if first.restore(first.text) != want or second.restore(second.text) != want:
            failures.append((name, "RedactionResult.restore", first.text, second.text))
        p = _corpus_passes()[name]
        if not _views_free(text):
            continue  # a decoded view may be returned: fidelity is traded away there, by design
        checked += 1
        for out, held in ((p.o1, p.h1), (p.o2, p.h2)):
            restored = runmap.restore_text(out, held)
            if _plain(restored, held) != text:
                failures.append((name, "restore_text", out, restored))
            if _secret_placeholders(restored) != _secret_placeholders(out):
                failures.append((name, "a secret kind was restored", out, restored))
    assert checked >= 350
    _no_failures(failures, len(_corpus()))


def test_I3_I5_corpus_without_a_bank_code_placeholder_the_result_is_the_old_path_and_find_only_is_unchanged():
    failures = []
    for name, text in _corpus().items():
        old_text, old_map = _old_one_pass(text)
        now = R.redact(text)
        if "<BANKCODE_" not in old_text and (now.text, now.mapping) != (old_text, old_map):
            failures.append((name, "I3", old_text, now.text))
        if R.redact(text, _sweep_copies=False).text != R._Redactor(None).find(text):
            failures.append((name, "I5"))
    _no_failures(failures, len(_corpus()))


# --- P5: concatenation ------------------------------------------------------------------------------------------

PAIR_SEPARATORS = ("\n", " ", "; ", "\n\n", " | ", "\t", ", ", "\r\n", ". ")
PAIRS_PER_SEPARATOR = 400


def _readable(value: str, redacted: str) -> int:
    """How often `value` can still be read in a redacted text (never inside a placeholder)."""
    return runmap.PLACEHOLDER.sub("\ue000", redacted).count(value)


@pytest.mark.parametrize(
    "sep",
    [pytest.param(s, marks=pytest.mark.xfail(strict=True, reason=F3)) if s == ". " else s for s in PAIR_SEPARATORS],
    ids=repr,
)
def test_P5_whatever_is_found_in_a_and_in_b_alone_is_found_in_a_then_b(sep):
    """For corpus entries a and b: no value masked in a alone or in b alone is MORE readable in the redaction of
    a + separator + b than in the two apart. (The stricter form, "the same values are in the map", is not a
    property of the redactor: a name or an address may take the next words into its value, so the map of the
    joined text can hold a longer value in place of the shorter one. That is a value masked, not a value lost.)
    Every pair of the privacy corpus, plus a fixed-seed sample over all corpora."""
    corpus = _corpus()
    names = sorted(corpus)
    rng = random.Random(f"{SEED}-pairs-{sep!r}")  # noqa: S311 - a fixed-seed test generator, not a secret
    privacy = [n for n in names if n.startswith("privacy-")]
    pairs = list(itertools.product(privacy, privacy)) if sep in ("\n", ". ") else []
    pairs += [(rng.choice(names), rng.choice(names)) for _ in range(PAIRS_PER_SEPARATOR)]
    alone = _corpus_passes()
    failures = []
    for a, b in pairs:
        mapping = runmap.RunMap()
        joined = runmap.redact_text(corpus[a] + sep + corpus[b], mapping)
        for value in {*alone[a].h1.values(), *alone[b].h1.values()}:
            if _readable(value, joined) > _readable(value, alone[a].o1) + _readable(value, alone[b].o1):
                failures.append((a, b, value, joined))
    _no_failures(failures, len(pairs))


# --- P5: the ticket's failing example, varied ---------------------------------------------------------------------

ACCOUNT = "1234" + "5678"
_BSB = "062" + "-" + "000"
_SORT = "12" + "-34-" + "56"
_ABA = "0210" + "00021"
CODE_KEYWORDS = {
    "BSB: ": _BSB,
    "BSB ": _BSB,
    "bsb=": _BSB,
    "sort code ": _SORT,
    "Sort Code: ": _SORT,
    "routing number ": _ABA,
    "ABA ": _ABA,
}
LINE_SEPARATORS = ("\n", "\r\n", "\n\n", " ", "; ", "\t", " | ", " then ")
LAYOUTS = ("code-line-first", "code-line-last", "start-and-end", "repeated")
# Between the code's copy and the account on the paying line. The account pattern that follows a code placeholder
# allows spaces and at most one of `, ; / | -` (redact.py); these are the links it claims, and before G7 the
# account stayed readable after one pass for each of them.
SWEPT_CODE_LINKS = ("/", ", ", "; ", "-", " | ", " / ", ",", "|", " ")
# An account KEYWORD between them: the keyword pattern matched before G7 too (a bank word is on the other line).
KEYWORD_LINKS = (" acct ", " account number ")
# Links the pattern does not allow: nothing claims the account is masked (it is not, before or after G7).
UNCLAIMED_LINKS = (":", "\n", "/\n", "")


def _ticket_texts(link: str):
    for (keyword, code), line, layout in itertools.product(CODE_KEYWORDS.items(), LINE_SEPARATORS, LAYOUTS):
        context, paying = keyword + code, "paid " + code + link + ACCOUNT
        yield {
            "code-line-first": context + line + paying,
            "code-line-last": paying + line + context,
            "start-and-end": paying + line + "retry queue" + line + context,
            "repeated": line.join((context, paying, paying, context)),
        }[layout]


def _g7_links(links):
    return [pytest.param(k, marks=needs_g7) if k in SWEPT_CODE_LINKS else k for k in links]


@pytest.mark.parametrize("link", _g7_links(SWEPT_CODE_LINKS + KEYWORD_LINKS), ids=repr)
def test_P5_the_account_beside_a_swept_bank_code_is_masked_in_one_pass(link):
    """The ticket's case in every layout: the code's keyword line before the paying line, after it, at the two
    ends of the text, and repeated; seven keywords, eight separators between the lines (a line break among them).
    Through `redact()`, through `redact_text` with a run map, and through `redact_many` (one string per part)."""
    failures = []
    texts = list(_ticket_texts(link))
    for text in texts:
        if ACCOUNT in R.redact(text).text:
            failures.append(("redact", text, R.redact(text).text))
        mapping = runmap.RunMap()
        if ACCOUNT in runmap.redact_text(text, mapping) or ACCOUNT not in mapping.values():
            failures.append(("redact_text", text, dict(mapping)))
    for keyword, code in CODE_KEYWORDS.items():
        for items in (
            [keyword + code, "paid " + code + link + ACCOUNT],
            ["paid " + code + link + ACCOUNT, "retry queue", keyword + code],
        ):
            outs, _ = R.redact_many(items)
            if any(ACCOUNT in out for out in outs):
                failures.append(("redact_many", items, outs))
    _no_failures(failures, 2 * len(texts) + 2 * len(CODE_KEYWORDS))


@pytest.mark.parametrize(
    "link", _g7_links(SWEPT_CODE_LINKS + KEYWORD_LINKS + UNCLAIMED_LINKS), ids=repr
)
def test_P1_I1_I2_I4_the_ticket_grid_is_a_fixed_point_and_equals_two_old_passes(link):
    """For EVERY link, claimed or not: one pass is a fixed point (I2, same map; and a fresh map finds nothing),
    it equals two passes of the old path, text and map (I1), and the map and text obey P2 and P3."""
    failures = []
    texts = list(_ticket_texts(link))
    for text in texts:
        now = R.redact(text)
        again = R.redact(now.text, mapping=now.mapping)
        if (again.text, again.mapping) != (now.text, now.mapping):
            failures.append(("I2 redact", text, now.text, again.text))
        once_text, once_map = _old_one_pass(text)
        if (now.text, now.mapping) != _old_one_pass(once_text, once_map):
            failures.append(("I1", text, now.text))
        p = _passes(text)
        if not _is_fixed_point(p) or _map_problems(p):
            failures.append(("I2 redact_text", text, p.o1, p.o2, _map_problems(p)))
        fresh = runmap.RunMap()
        if runmap.redact_text(p.o1, fresh) != p.o1 or dict(fresh):
            failures.append(("fresh map", text, p.o1, dict(fresh)))
    _no_failures(failures, len(texts))


FAR = "x " * 80  # 160 characters: wider than the 100-character bank window


@needs_g7
@pytest.mark.parametrize("keyword", sorted(CODE_KEYWORDS), ids=repr)
def test_P5_an_account_keyword_whose_only_bank_context_is_a_swept_code(keyword):
    """The mirror shape: `acct <digits>` counts only with bank context, and the only context near it is the
    code's swept copy. Context word before the account and after it, at the start and at the end of the text."""
    code = CODE_KEYWORDS[keyword]
    failures = []
    for text in (
        f"{keyword}{code}\n{FAR}\nref {code} acct {ACCOUNT}",
        f"ref {code} acct {ACCOUNT}\n{FAR}\n{keyword}{code}",
        f"acct {ACCOUNT} ref {code}\n{FAR}\n{keyword}{code}",
        f"{keyword}{code}\n{FAR}\nacct {ACCOUNT} ref {code}\n{FAR}\nacct {ACCOUNT} ref {code}",
    ):
        p = _passes(text)
        if ACCOUNT in p.o1 or not _is_fixed_point(p):
            failures.append((text[:40], p.o1[-60:], p.o2[-60:]))
    _no_failures(failures, 4)


@needs_g7
def test_P5_the_second_text_of_a_run_and_the_look_alike_spellings_of_the_paying_line():
    """The run map already holds the code (found in an earlier text); and the paying line written with a
    zero-width space inside the code or full-width digits in the account (found in the canonical view)."""
    for keyword, code in CODE_KEYWORDS.items():
        mapping = runmap.RunMap()
        runmap.redact_text(keyword + code, mapping)
        out = runmap.redact_text(f"paid {code}/{ACCOUNT}", mapping)
        assert ACCOUNT not in out and ACCOUNT in mapping.values(), (keyword, out)
        held = dict(mapping)
        assert runmap.redact_text(out, mapping) == out and dict(mapping) == held
    wide = "".join(chr(0xFF10 + int(d)) for d in ACCOUNT)
    for text in (
        f"BSB: {_BSB}\npaid {_BSB[:3]}\u200b{_BSB[3:]}/{ACCOUNT}",
        f"BSB: {_BSB}\npaid {_BSB}/{wide}",
    ):
        p = _passes(text)
        assert ACCOUNT not in runmap.canonical(p.o1), p.o1
        assert _is_fixed_point(p), (p.o1, p.o2)


# --- P6: generated text ------------------------------------------------------------------------------------------

LOW, UP, DIG = string.ascii_lowercase, string.ascii_uppercase, string.digits
HEX = "0123456789abcdef"
# Filler: plain lower-case words no detector keys on. They must all survive redaction.
WORDS = (
    "checkout timeout retry upstream latency queue worker deploy rollback cache probe shard replica gateway "
    "handler drained slow warm green stale batch cursor window signal paused"
).split()
FIRST = ("Asha", "Ravi", "Meera", "Tomas", "Ines", "Kofi")
LAST = ("Verma", "Okoro", "Lindqvist", "Sato", "Moreau", "Haddad")


def _pick(rng, alphabet: str, n: int) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def _mixed(rng, n: int) -> str:
    body = [rng.choice(UP), rng.choice(LOW), rng.choice(DIG)]
    body += [rng.choice(LOW + UP + DIG) for _ in range(n - 3)]
    rng.shuffle(body)
    return "".join(body)


def _uuid(rng) -> str:
    h = _pick(rng, HEX, 32)
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def _card(rng) -> str:
    digits = [4] + [rng.randrange(10) for _ in range(14)]
    total = 0
    for i, d in enumerate(reversed(digits)):
        d = d * 2 if i % 2 == 0 else d
        total += d - 9 if d > 9 else d
    number = "".join(map(str, [*digits, (10 - total % 10) % 10]))
    return " ".join(number[i : i + 4] for i in range(0, 16, 4))


def _code(rng) -> str:
    return _pick(rng, DIG, 3) + "-" + _pick(rng, DIG, 3)


def _plant_privkey(rng):
    body = "\n".join(_mixed(rng, 48) for _ in range(2))
    frame = "RSA " + "PRIVATE" + " KEY-----"
    return f"-----BEGIN {frame}\n{body}\n-----END {frame}", [body]


def _plant_bankacct(rng):
    code, account = _code(rng), _pick(rng, "123456789", 1) + _pick(rng, DIG, 7)
    return f"BSB {code} account {account}", [code, account]


def _plant_urlcred(rng):
    password = _mixed(rng, 14)
    return f"postgres://svc:{password}@db.shop.example:5432/app", [password]


def _one(prefix, make):
    """A planter: (rng) -> (the text to plant, the values that must not be readable afterwards)."""

    def plant(rng):
        value = make(rng)
        lead = rng.choice(prefix) if isinstance(prefix, tuple) else prefix
        return lead + value, [value]

    return plant


# One planter per detector kind of the pattern table (`test_P6_there_is_a_planter_for_every_detector_kind`).
PLANTERS = {
    "PRIVKEY": _plant_privkey,
    "ARN": _one("role ", lambda r: f"arn:aws:iam::{_pick(r, DIG, 12)}:role/{r.choice(WORDS)}-admin"),
    "GCPRESOURCE": _one(
        "at ",
        lambda r: f"projects/{_pick(r, LOW, 6)}-{_pick(r, DIG, 4)}/zones/z1/instances/vm{_pick(r, DIG, 3)}",
    ),
    "AZURERESOURCE": _one(
        "scope ", lambda r: f"/subscriptions/{_uuid(r)}/resourceGroups/rg{_pick(r, DIG, 3)}"
    ),
    "JWT": _one("jwt ", lambda r: f"eyJ{_mixed(r, 18)}.eyJ{_mixed(r, 16)}.{_mixed(r, 30)}"),
    "APIKEY": _one(
        "key ", lambda r: r.choice(("ghp_", "AK" + "IA", "glpat-", "hf_")) + _pick(r, UP + DIG, 20)
    ),
    "GCPTOKEN": _one("tok ", lambda r: "ya29." + _mixed(r, 30)),
    "AZURESAS": _one("sv=2020&sig=", lambda r: _mixed(r, 24)),
    "WEBHOOK": _one(
        "post ",
        lambda r: "https://hooks.slack.com/services/T"
        + f"{_pick(r, UP + DIG, 8)}/B{_pick(r, UP + DIG, 8)}/{_mixed(r, 20)}",
    ),
    "URLCRED": _plant_urlcred,
    "EMAIL": _one("mail ", lambda r: f"{r.choice(WORDS)}{_pick(r, DIG, 3)}@corp.example"),
    "IBAN": _one("iban ", lambda r: "GB" + _pick(r, DIG, 2) + _pick(r, UP, 4) + _pick(r, DIG, 14)),
    "UUID": _one("req ", _uuid),
    "BANKCODE": _one(("BSB ", "BSB: ", "bsb="), _code),
    "BANKACCT": _plant_bankacct,
    "ACCOUNTID": _one("owner ", lambda r: _pick(r, "123456789", 1) + _pick(r, DIG, 11)),
    "IPV4": _one("src=", lambda r: "10." + ".".join(str(r.randrange(1, 255)) for _ in range(3))),
    "IPV6": _one("from ", lambda r: f"2001:db8::{_pick(r, HEX, 4)}:{_pick(r, HEX[1:], 4)}"),
    "MAC": _one("eth0 ", lambda r: ":".join(_pick(r, HEX, 2) for _ in range(6))),
    "HOSTNAME": _one("db at ", lambda r: f"{r.choice(WORDS)}-{_pick(r, DIG, 2)}.prod.corp"),
    "TENANT": _one("tenant_id=", lambda r: f"{_pick(r, LOW, 5)}-{_pick(r, DIG, 3)}"),
    "BEARER": _one("Bearer ", lambda r: _mixed(r, 24)),
    "BASIC": _one("Basic ", lambda r: _mixed(r, 20)),
    "SSN": _one(
        "ssn ",
        lambda r: f"{_pick(r, '1234567', 3)}-{_pick(r, '123456789', 2)}-{_pick(r, '123456789', 4)}",
    ),
    "AADHAAR": _one(
        "aadhaar ",
        lambda r: f"{_pick(r, '23456789', 1)}{_pick(r, DIG, 3)} {_pick(r, DIG, 4)} {_pick(r, DIG, 4)}",
    ),
    "PAN": _one(
        "pan ", lambda r: _pick(r, UP, 3) + "P" + _pick(r, UP, 1) + _pick(r, DIG, 4) + _pick(r, UP, 1)
    ),
    "ADDRESS": _one("ships to ", lambda r: f"{r.randrange(1, 300)} {r.choice(LAST)} Street"),
    "NAME": _one(
        ("full_name=", "Dear ", "assigned to Dr. "), lambda r: f"{r.choice(FIRST)} {r.choice(LAST)}"
    ),
    "CREDITCARD": _one("card ", _card),
    "PHONE": _one("call ", lambda r: "+1 415 555 " + _pick(r, DIG, 4)),
    "SECRET": _one(("password=", "client_secret: ", "api_key="), lambda r: _mixed(r, 12)),
    "HIGHENTROPY": _one("blob ", lambda r: _mixed(r, 44)),
}


def _fullwidth(text: str) -> str:
    return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in text)


def _vary(rng, label: str, planted: str, value: str) -> str:
    """One spelling the text normaliser undoes, or a change of case in the words before the value. The
    title-and-salutation NAME patterns (`Dr.`, `Dear`) are case-sensitive by their regex: their case is kept."""
    at = planted.find(value)
    how = rng.choice(("fullwidth", "one-fullwidth", "zero-width", "upper", "swapcase"))
    if how == "fullwidth":
        return planted.replace(value, _fullwidth(value))
    if how == "one-fullwidth":
        i = rng.randrange(len(value))
        return planted.replace(value, value[:i] + _fullwidth(value[i]) + value[i + 1 :])
    if how == "zero-width":
        i = rng.randrange(1, len(value))
        mark = rng.choice("\u200b\u200d\u2060\ufeff\u200f")
        return planted.replace(value, value[:i] + mark + value[i:])
    if label == "NAME" and not planted.startswith("full_name="):
        return planted
    lead = planted[:at]
    return (lead.upper() if how == "upper" else lead.swapcase()) + planted[at:]


SEPARATORS = (" ", "\n", "; ", ", ", " | ", "\t", " - ", "\n\n", "\r\n")
# After `full_name=First Last` the NAME pattern takes up to three more words (its `{0,3}`, any case): a stated
# behaviour of that detector. Filler after such a name is therefore set off by a separator that ends the name.
ENDS_A_NAME = tuple(s for s in SEPARATORS if s not in (" ", "\t", " - "))
GENERATED_CASES = 2500

Case = collections.namedtuple("Case", "text values filler labels")


@functools.cache
def _generated() -> tuple[Case, ...]:
    rng = random.Random(f"{SEED}-planted")  # noqa: S311 - a fixed-seed test generator, not a secret
    labels = list(PLANTERS)
    cases = []
    for n in range(GENERATED_CASES):
        parts: list[str] = []
        values: list[str] = []
        filler: list[str] = []
        planted_labels = []
        for k in range(rng.randrange(1, 5)):
            # every kind in turn first, then at random: each kind is planted at least 78 times
            label = labels[n % len(labels)] if k == 0 else rng.choice(labels)
            planted, found = PLANTERS[label](rng)
            if rng.random() < 0.25:
                planted = _vary(rng, label, planted, found[-1])
            words = [rng.choice(WORDS) for _ in range(rng.randrange(0, 4))]
            filler += words
            if words:
                parts += [" ".join(words), rng.choice(SEPARATORS)]
            parts.append(planted)
            if rng.random() < 0.2:  # the same value again, on its own
                parts += [rng.choice(ENDS_A_NAME), found[-1]]
            parts.append(rng.choice(ENDS_A_NAME if label == "NAME" else SEPARATORS))
            values += found
            planted_labels.append(label)
        tail = [rng.choice(WORDS) for _ in range(rng.randrange(1, 3))]
        filler += tail
        cases.append(Case("".join(parts) + " ".join(tail), values, filler, planted_labels))
    return tuple(cases)


@functools.cache
def _generated_passes() -> tuple[Passes, ...]:
    return tuple(_passes(case.text) for case in _generated())


def test_P6_there_is_a_planter_for_every_detector_kind_and_each_plants_its_kind():
    """The kinds are read from the pattern table: a new detector kind without a planter fails here."""
    assert set(PLANTERS) == set(LABELS)
    rng = random.Random(f"{SEED}-kinds")  # noqa: S311 - a fixed-seed test generator, not a secret
    for label, plant in PLANTERS.items():
        for _ in range(25):
            planted, values = plant(rng)
            result = R.redact(planted)
            assert label in result.kinds, (label, planted, result.text)
            assert not any(v in result.text for v in values), (label, planted, result.text)
    planted_kinds = collections.Counter(label for case in _generated() for label in case.labels)
    assert set(planted_kinds) == set(LABELS) and min(planted_kinds.values()) >= GENERATED_CASES // 32


def test_P6_every_planted_value_is_gone_after_one_pass():
    """Not in the output as written, and not in its canonical form (look-alike spellings undone)."""
    failures = []
    for case, p in zip(_generated(), _generated_passes(), strict=True):
        seen = runmap.canonical(p.o1)
        gone = [v for v in case.values if v in p.o1 or v in seen]
        if gone:
            failures.append((case.labels, gone, case.text, p.o1))
    _no_failures(failures, GENERATED_CASES)


def test_P1_I2_generated_one_pass_is_a_fixed_point_with_the_same_map_and_with_a_fresh_map():
    """Same map: claimed by the ticket for its shapes, and true of every generated text whose values stand apart
    (a separator on each side). Fresh map: not claimed; it holds here too, so it is pinned."""
    failures = []
    for case, p in zip(_generated(), _generated_passes(), strict=True):
        if not _is_fixed_point(p) or p.o3 != p.o2 or p.h3 != p.h2:
            failures.append(("same map", case.text, p.o1, p.o2))
        fresh = runmap.RunMap()
        if runmap.redact_text(p.o1, fresh) != p.o1 or dict(fresh):
            failures.append(("fresh map", case.text, p.o1, dict(fresh)))
        first = R.redact(case.text)
        second = R.redact(first.text, mapping=first.mapping)
        if (second.text, second.mapping) != (first.text, first.mapping):
            failures.append(("redact()", case.text, first.text, second.text))
    _no_failures(failures, 3 * GENERATED_CASES)


def test_P2_P3_generated_the_map_only_grows_and_no_placeholder_is_redacted_again():
    failures = [
        (probs, p.x, p.o1, p.o2) for p in _generated_passes() if (probs := _map_problems(p))
    ]
    _no_failures(failures, GENERATED_CASES)


def test_P4_P6_generated_nothing_but_the_sensitive_values_is_taken_and_restore_gives_the_text_back():
    """Every filler word is still in the output, as often as it was written. For a text `redact_text` returns
    as written (ASCII, no escapes), putting the map back gives the input exactly, after one pass and after two:
    nothing was eaten that the map does not hold. The bare redactor's own `restore` gives every text back."""
    failures = []
    exact = 0
    for case, p in zip(_generated(), _generated_passes(), strict=True):
        left = collections.Counter(
            re.findall(r"[a-z0-9]+", runmap.PLACEHOLDER.sub(" ", runmap.canonical(p.o1)))
        )
        eaten = [w for w, n in collections.Counter(case.filler).items() if left[w] < n]
        if eaten:
            failures.append(("filler eaten", eaten, case.text, p.o1))
        if _views_free(case.text):
            exact += 1
            for out, held in ((p.o1, p.h1), (p.o2, p.h2)):
                if _plain(runmap.restore_text(out, held), held) != case.text:
                    failures.append(("restore_text", case.text, out))
        first = R.redact(case.text)
        second = R.redact(first.text, mapping=first.mapping)
        if first.restore(first.text) != case.text or second.restore(second.text) != case.text:
            failures.append(("RedactionResult.restore", case.text, first.text))
    assert exact >= GENERATED_CASES // 4
    _no_failures(failures, GENERATED_CASES)


def test_I3_generated_without_a_bank_code_placeholder_the_result_is_the_old_path():
    failures = []
    checked = 0
    for case in _generated():
        old_text, old_map = _old_one_pass(case.text)
        if "<BANKCODE_" in old_text:
            continue
        checked += 1
        now = R.redact(case.text)
        if (now.text, now.mapping) != (old_text, old_map):
            failures.append((case.text, old_text, now.text))
    assert checked >= GENERATED_CASES // 2
    _no_failures(failures, checked)


# --- P6: bank text with no separators guaranteed -----------------------------------------------------------------

BANK_FUZZ_CASES = 4000
_FUZZ_CODES = (_BSB, "033" + "-" + "111", _SORT)
_FUZZ_ACCOUNTS = (ACCOUNT, "8765" + "4321", "5555" + "6666", "1234-" + "5678")
_FUZZ_KEYWORDS = ("BSB: ", "BSB ", "sort code ", "bsb=", "Bsb: ")
_FUZZ_TOKENS = (
    "paid ", "ref ", "acct ", "account ", "/", ", ", " ", "\n", "; ", "-", "|", "x", "A", "_", ".", "refund ",
    "x " * 60, "\r\n", "<BANKCODE_1>", "<BANKCODE_7>", "bank account ",
)  # fmt: skip


@functools.cache
def _bank_fuzz() -> tuple[tuple[str, object, object], ...]:
    """Bank codes, account numbers, their keywords, links, glue and typed code placeholders in random order:
    (text, first pass, second pass with the first pass's map), or the error in place of a pass."""
    rng = random.Random(f"{SEED}-bank")  # noqa: S311 - a fixed-seed test generator, not a secret
    rows = []
    for _ in range(BANK_FUZZ_CASES):
        parts = []
        for _ in range(rng.randrange(3, 14)):
            k = rng.random()
            if k < 0.2:
                parts.append(rng.choice(_FUZZ_KEYWORDS) + rng.choice(_FUZZ_CODES))
            elif k < 0.4:
                parts.append(rng.choice(_FUZZ_CODES))
            elif k < 0.65:
                parts.append(rng.choice(_FUZZ_ACCOUNTS))
            else:
                parts.append(rng.choice(_FUZZ_TOKENS))
        text = "".join(parts)
        try:
            first = R.redact(text)
            second = R.redact(first.text, mapping=first.mapping)
        except RuntimeError as exc:
            first = second = exc
        rows.append((text, first, second))
    return tuple(rows)


def test_I4_bank_fuzz_the_redactor_never_gives_up_at_the_round_bound():
    """The ticket: one round does the work and the bound of four is slack. No text of the fuzz reaches it (a raise
    would be fail-closed and allowed by I4, but it would mean a text nobody can send)."""
    raised = [(text, repr(first)) for text, first, _ in _bank_fuzz() if isinstance(first, Exception)]
    _no_failures(raised, BANK_FUZZ_CASES)


@needs_g7
def test_P1_I2_I4_bank_fuzz_a_second_pass_finds_no_account_the_first_pass_left():
    """After one pass no account is left for a second pass to find: the second pass adds no BANKACCT entry and
    writes no further BANKACCT placeholder, and the context patterns themselves find nothing in the output."""
    failures = []
    for text, first, second in _bank_fuzz():
        new = [k for k in second.mapping if k not in first.mapping and R.kind_of(k) == "BANKACCT"]
        if new or second.text.count("<BANKACCT_") != first.text.count("<BANKACCT_"):
            failures.append((text, first.text, second.text))
        probe = R._Redactor(first.mapping)
        if probe._find_context(first.text) != first.text:
            failures.append(("context patterns still match", text, first.text))
    _no_failures(failures, BANK_FUZZ_CASES)


@needs_g7
def test_P1_bank_fuzz_whatever_else_a_second_pass_changes_is_not_an_account():
    """The full fixed point over the same fuzz, kept apart from the account property above so a finding in
    another kind cannot hide an account regression: every case whose second pass changes anything is listed,
    and the only kinds a second pass may add are the ones finding G7-F2 names (a digit run glued to a swept
    phone number read as AADHAAR, and the like), never BANKACCT or BANKCODE."""
    stray = []
    for text, first, second in _bank_fuzz():
        added = {R.kind_of(k) for k in second.mapping if k not in first.mapping}
        if added & {"BANKACCT", "BANKCODE"}:
            stray.append((text, first.text, second.text))
    _no_failures(stray, BANK_FUZZ_CASES)


# --- P6: glued values (finding G7-F2) ----------------------------------------------------------------------------

GLUE_FUZZ_CASES = 3000
_GLUE = ("", "-", ".", "/", "_", "+", "=", ":", " ", "\n", ", ", "; ", "x", "7")


@functools.cache
def _glue_fuzz() -> tuple[tuple[str, object, object], ...]:
    """Planted values and their bare copies joined by random glue, the empty string included."""
    rng = random.Random(f"{SEED}-glue")  # noqa: S311 - a fixed-seed test generator, not a secret
    labels = list(PLANTERS)
    rows = []
    for _ in range(GLUE_FUZZ_CASES):
        pool = [PLANTERS[rng.choice(labels)](rng) for _ in range(rng.randrange(1, 4))]
        parts = []
        for _ in range(rng.randrange(2, 7)):
            planted, values = rng.choice(pool)
            k = rng.random()
            parts.append(planted if k < 0.5 else rng.choice(values) if k < 0.9 else rng.choice(WORDS))
            parts.append(rng.choice(_GLUE))
        text = "".join(parts)
        first = R.redact(text)
        rows.append((text, first, R.redact(first.text, mapping=first.mapping)))
    return tuple(rows)


def test_P2_P3_P4_glue_fuzz_the_map_only_grows_and_the_text_behind_the_placeholders_never_changes():
    """Even where a second pass masks more (finding G7-F2), it must not damage what the first pass did: no entry
    lost or changed, no value given a second placeholder, no stored value that holds a placeholder, and
    `restore` gives the input back after one pass and after two."""
    failures = []
    for text, first, second in _glue_fuzz():
        problems = []
        if any(second.mapping.get(k) != v for k, v in first.mapping.items()):
            problems.append("an entry was lost or changed")
        added = [v for k, v in second.mapping.items() if k not in first.mapping]
        if set(added) & set(first.mapping.values()):
            problems.append("a known value got a second placeholder")
        if any(k in v for v in second.mapping.values() for k in second.mapping):
            problems.append("a stored value holds a placeholder")
        if not (_plain(first.text, first.mapping) == _plain(second.text, second.mapping) == text):
            problems.append("the text behind the placeholders changed")
        if first.restore(first.text) != text or second.restore(second.text) != text:
            problems.append("restore does not give the text back")
        if problems:
            failures.append((problems, text, first.text, second.text))
    _no_failures(failures, GLUE_FUZZ_CASES)


@pytest.mark.xfail(strict=True, reason=F2)
def test_P1_glue_fuzz_one_pass_is_a_fixed_point():
    failures = [
        (text, first.text, second.text)
        for text, first, second in _glue_fuzz()
        if (second.text, second.mapping) != (first.text, first.mapping)
    ]
    _no_failures(failures, GLUE_FUZZ_CASES)


_PW = "Zq7" + "pLm2xQ9"
_GLUED = {
    "SSN": ("ssn ", "161" + "-19-" + "4556"),
    "IPV4": ("src ", "10.77" + ".122.17"),
    "EMAIL": ("", "ops17" + "@" + "corp.example"),
    "MAC": ("", "77:4e:f9" + ":4e:9c:62"),
    "PHONE": ("call ", "+1 415 555 " + "0142"),
}


@pytest.mark.xfail(strict=True, reason=F2)
@pytest.mark.parametrize("kind", sorted(_GLUED))
def test_P1_an_identifier_glued_to_a_copy_of_a_known_secret_is_masked_in_one_pass(kind):
    """Smallest form: `password=<V>` on line 1; on line 2 an identifier with <V> glued to its end. One pass
    gives `ssn 161-19-4556<SECRET_1>` (the identifier readable); a second pass masks it."""
    lead, value = _GLUED[kind]
    result = R.redact(f"password={_PW}\n{lead}{value}{_PW}")
    assert value not in result.text


@pytest.mark.xfail(strict=True, reason=F2)
def test_P1_a_tenant_id_after_a_glued_copy_of_a_known_secret_is_masked_in_one_pass():
    result = R.redact(f"password={_PW}\n{_PW}tenant_id=acme-42")
    assert "acme-42" not in result.text


@pytest.mark.xfail(strict=True, reason=F1)
@pytest.mark.parametrize("scheme", ["Bearer ", "Basic ", "authorization: "])
def test_P1_a_short_token_that_starts_with_a_known_secret_is_a_fixed_point(scheme):
    """The ticket lists this as RELATED, NOT FIXED: `password=V` then `Bearer V+xy` gives `Bearer <SECRET_1>+xy`
    after one pass (the two-character tail readable) and one placeholder after two."""
    short = _PW[:8]
    first = R.redact(f"password={short}\n{scheme}{short}+xy")
    second = R.redact(first.text, mapping=first.mapping)
    assert (second.text, second.mapping) == (first.text, first.mapping)


@pytest.mark.xfail(strict=True, reason=F3)
@pytest.mark.parametrize("text", ["call {}.", "call {}. Thanks", "phone={}.", "rang {}.\nno answer"])
def test_P5_a_phone_number_at_the_end_of_a_sentence_is_masked(text):
    """Found by the concatenation property (separator `. `). The same number followed by a comma, a space or
    the end of the text is masked."""
    phone = "+1 415 555 " + "0142" if "=" not in text else "4155550" + "142"
    assert phone not in R.redact(text.format(phone)).text


# --- P7: hostile text --------------------------------------------------------------------------------------------

_EMAIL = "ops17" + "@" + "corp.example"
_IP = "10.4" + ".12.9"
_BASE = f"login password={_PW} from {_IP} mail {_EMAIL}"
_NUL, _ZW, _ZWJ, _BOM, _RLM, _RLO = chr(0), "\u200b", "\u200d", "\ufeff", "\u200f", "\u202e"
HOSTILE = {
    "nul-in-secret": f"password={_PW[:4]}{_NUL}{_PW[4:]} mail {_EMAIL}",
    "nul-in-key": f"pass{_NUL}word={_PW} mail {_EMAIL}",
    "controls-around": "".join(chr(i) for i in range(1, 32)) + _BASE + chr(127),
    "controls-between": f"password={_PW}\x01\x02 from\x1f{_IP}\x7f mail\x0b{_EMAIL}",
    "escape-codes": f"\x1b[1mpassword={_PW}\x1b[0m mail {_EMAIL}",
    "long-letters": "a" * 50_000 + " " + _BASE,
    "long-digits": "7" * 20_000 + " " + _BASE,
    "long-mixed": "Ab3" * 10_000 + " " + _BASE,
    "long-angle-brackets": "<" * 5_000 + _BASE + ">" * 5_000,
    "long-run-of-placeholders": "<SECRET_1>" * 3_000 + _BASE,
    "typed-secret-placeholder": f"<SECRET_1> {_BASE} <SECRET_1>",
    "typed-email-placeholder": f"<EMAIL_1> {_BASE} <EMAIL_1>",
    "typed-ip-placeholder": f"see <IPV4_1> then {_BASE}",
    "typed-lower-case": f"<email_1> <Ipv4_1> {_BASE}",
    "typed-nested": f"<<SECRET_1>_2> <<EMAIL_1>> <EMAIL_<EMAIL_1>> {_BASE}",
    "typed-unclosed": f"<SECRET_1 <EMAIL_1 EMAIL_1> {_BASE}",
    "typed-huge-number": f"<SECRET_{'9' * 30}> <EMAIL_{'9' * 19}> {_BASE}",
    "typed-unknown-kind": f"<NOTAKIND_1> <X_0> {_BASE}",
    "typed-escaped": f"\u2039SECRET_1\u203a \u2039EMAIL_1\u203a {_BASE}",
    "typed-as-a-value": f"password=<SECRET_1> token=<EMAIL_1> {_BASE}",
    "typed-escaped-as-a-value": f"password=\u2039SECRET_1\u203a {_BASE}",
    "typed-bank-code-then-digits": f"<BANKCODE_1>/{ACCOUNT} {_BASE}",
    "typed-with-zero-width": f"<SEC{_ZW}RET_1> <EMAIL{_ZWJ}_1> {_BASE}",
    "typed-full-width": "\uff1cEMAIL_1\uff1e " + _BASE,
    "typed-encoded": f"&lt;EMAIL_1&gt; %3CIPV4_1%3E \\u003cEMAIL_1\\u003e {_BASE}",
    "right-to-left-in-values": f"password={_PW[:4]}{_RLM}{_PW[4:]} mail {_EMAIL[:3]}{_RLO}{_EMAIL[3:]}",
    "right-to-left-around": f"{_RLO}password={_PW}{_RLM} from {_RLM}{_IP}{_RLO} mail {_EMAIL}",
    "zero-width-in-values": (
        f"password={_PW[:3]}{_ZW}{_PW[3:]} from {_IP[:4]}{_ZWJ}{_IP[4:]} mail {_EMAIL[:5]}{_BOM}{_EMAIL[5:]}"
    ),
    "zero-width-in-key": f"pass{_ZW}word={_PW} mail {_EMAIL}",
}
_REAL = (_PW, _EMAIL, _IP)


def _nothing_real_is_readable(*texts: str) -> None:
    for text in texts:
        seen = runmap.canonical(text)
        assert not [v for v in _REAL if v in text or v in seen], text[-300:]


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_P7_untrusted_text_first_pass_masks_and_a_typed_placeholder_restores_to_nothing(name):
    """`redact_untrusted` (text from outside). The real values are gone; every genuine placeholder in the output
    is one the run issued (a typed look-alike, in any spelling, is never left looking genuine); and restoring
    puts each real value back exactly as often as the input held it: a user who types `<EMAIL_1>` does not get
    the run's e-mail address written into their sentence."""
    text = HOSTILE[name]
    mapping = runmap.RunMap()
    out = runmap.redact_untrusted(text, mapping)
    _nothing_real_is_readable(out)
    orphans = [m.group(0) for m in runmap.PLACEHOLDER.finditer(out) if m.group(0) not in mapping]
    assert not orphans, (orphans[:3], out[-300:])
    restored = runmap.restore_text(out, mapping)
    written = runmap.canonical(runmap._clean(text))
    for value in (_EMAIL, _IP):  # the stored kinds; a secret kind is never restored
        assert restored.count(value) == written.count(value), (value, restored[-300:])
    assert _PW not in restored


@needs_own_output_rule
@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_P7_I6_untrusted_text_a_second_pass_adds_no_map_entry_and_a_third_changes_nothing(name):
    """`redact_untrusted` over its own output escapes the run's placeholders (by design: to that hook they are
    typed text), so the TEXT of pass two differs from pass one. What must hold: the map is unchanged (before the
    rule, `password=` before the escaped token made a junk secret), nothing real becomes readable, and from
    pass two on the text is a fixed point."""
    p = _passes(HOSTILE[name], runmap.redact_untrusted)
    assert p.h2 == p.h1, {k: v for k, v in p.h2.items() if k not in p.h1}
    assert (p.o3, p.h3) == (p.o2, p.h2)
    _nothing_real_is_readable(p.o2, p.o3)


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_P7_P1_P2_P3_model_written_text_is_a_fixed_point_and_no_placeholder_is_corrupted(name):
    """`redact_text` (model-written text: a placeholder in it is meant to be one, so a typed one is kept and
    restores; that is the stated design and is not asserted against here). One pass masks the real values and is
    a fixed point with the same map; the map obeys P2 and P3."""
    p = _passes(HOSTILE[name])
    _nothing_real_is_readable(p.o1)
    assert _is_fixed_point(p), (p.o1[-200:], p.o2[-200:])
    assert not _map_problems(p)


def test_P7_a_typed_placeholder_never_takes_the_place_of_a_real_one_issued_later():
    """A document types `<EMAIL_1>` before the run has issued any placeholder; a later text of the same run holds
    a real address. The typed token was escaped, so the real `<EMAIL_1>` is the only one, in both orders, and a
    second pass over either output adds nothing to the map."""
    for texts in (("quote <EMAIL_1> end", f"mail {_EMAIL}"), (f"mail {_EMAIL}", "quote <EMAIL_1> end")):
        mapping = runmap.RunMap()
        outs = [runmap.redact_untrusted(t, mapping) for t in texts]
        assert dict(mapping) == {"<EMAIL_1>": _EMAIL}
        assert sum(out.count("<EMAIL_1>") for out in outs) == 1
        assert sum(runmap.restore_text(out, mapping).count(_EMAIL) for out in outs) == 1
        held = dict(mapping)
        for out in outs:
            runmap.redact_untrusted(out, mapping)
        assert dict(mapping) == held
