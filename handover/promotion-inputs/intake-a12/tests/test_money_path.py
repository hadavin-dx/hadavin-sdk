"""WP2c money path (errata 75, 77): the minimum limit is derived from the masked-text cap, the README worked example is checked against the code, the
prompt has one source. These tests use the example prices fixture; no live call, no spend."""

from __future__ import annotations

import ast
import re
import shutil
from datetime import UTC, datetime

import pytest
from model_support import fake_settings, req

from conftest import ROOT, settings_for_tests
from intake import budget, mask, prompt_file, settings
from intake.model import ExtractRequest
from intake.model_anthropic import AnthropicBackend
from intake.selfcheck_codes import SelfCheckFailed

WORST_CHARS = (chr(0x10FFFF), chr(1))  # 4 bytes per character in the live body, 6 once escaped


@pytest.fixture
def live(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path, backend="anthropic", with_ledger=True)
    shutil.copyfile(ROOT / "tests" / "fixtures" / "model" / "prices_example.json", s.prices_path)
    monkeypatch.setattr(budget, "clock", lambda: datetime(2026, 11, 4, 12, 0, tzinfo=UTC).timestamp())
    return s, AnthropicBackend(s)


def worst_bodies(backend, tier):
    return [len(backend.request_body(ExtractRequest("0" * 64, tier, model_text=c * mask.MASKED_MAX_CHARS))) for c in WORST_CHARS]


def test_masked_cap_not_below_document_cap():
    assert mask.MASKED_MAX_CHARS >= settings.read_policy_value("max_document_chars")


def test_the_minimum_limit_is_derived_from_the_masked_cap(live, monkeypatch):
    s, b = live
    want = budget.MIN_FACTOR * sum(
        budget.worst_case(budget.current_prices(s), t, max(worst_bodies(b, t)), s.model.max_tokens, s.model.overhead_tokens)
        for t in budget.TIERS
    )
    assert budget.min_limit_micro(s, b) == want
    monkeypatch.setattr(
        mask, "MASKED_MAX_CHARS", 1000
    )  # a smaller bound gives a smaller minimum: the function reads the constant at call time
    assert budget.min_limit_micro(s, b) < want


def test_readme_min_limit_numbers_match(live):
    """The worked example in README.md is the number the code computes (each figure is read from the text, then compared with the code)."""
    s, b = live
    text = re.sub(r"\s+", " ", (ROOT / "README.md").read_text(encoding="utf-8"))
    num = r"([0-9][0-9,]*)"
    m = re.search(rf"request bodies of {num} bytes \(read tier\) and {num} bytes \(fallback tier\)", text)
    assert m, "README worked example: bodies"
    bodies = [int(x.replace(",", "")) for x in m.groups()]
    m = re.search(
        rf"that is {num} and {num} micro-USD; the minimum limit is 18 x \({num} \+ {num}\) = {num} micro-USD, .* `min_limit_usd` ([0-9]+)",
        text,
    )
    assert m, "README worked example: money"
    read_w, fb_w, a, c, total, usd = (int(x.replace(",", "")) for x in m.groups())
    p = budget.current_prices(s)
    assert max(worst_bodies(b, "read")) == bodies[0] and max(worst_bodies(b, "fallback")) == bodies[1]
    assert budget.worst_case(p, "read", bodies[0], s.model.max_tokens, s.model.overhead_tokens) == read_w == a
    assert budget.worst_case(p, "fallback", bodies[1], s.model.max_tokens, s.model.overhead_tokens) == fb_w == c
    assert total == 18 * (read_w + fb_w) == budget.min_limit_micro(s, b)
    assert usd == -(-total // 1_000_000)


def test_prompt_path_single_constant():
    """Only ``prompt_file.py`` names a prompt file; ``extract`` and ``model_anthropic`` alias it."""
    from intake import extract, model_anthropic

    assert extract.PROMPT_PATH == prompt_file.PROMPT_PATH == model_anthropic._PROMPT
    assert prompt_file.PROMPT_PATH.name == "extract_v3.txt"
    for p in sorted((ROOT / "src" / "intake").glob("*.py")):
        if p.name != "prompt_file.py":
            assert "extract_v" not in p.read_text(encoding="utf-8"), p.name


PROMPTS = ROOT / "src" / "intake" / "prompts"
PROMPT_SHA = {  # the kept prompt versions are pinned byte for byte (README says so)
    "extract_v1.txt": "59ac5c94b89d1e6678f3ffdf90ec372398b78994ddce60a138e706c7a7da0714",
    "extract_v2.txt": "f3e1608a94a4749f857fc79c59587d59c335bfad3ba11c72dcf71db9816a9f63",
    "extract_v3.txt": "25d12441467ecc256cefdc36c96bda019c2b7615aa2552ae90bd297f254e9e67",
}


def test_every_kept_prompt_version_is_pinned_by_its_sha():
    import hashlib

    for name, want in PROMPT_SHA.items():
        text = (PROMPTS / name).read_text(encoding="utf-8").replace("\r\n", "\n")  # decoded, LF: an autocrlf checkout hashes the same
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == want, name


def test_prompt_v2_is_v1_plus_the_mark_sentence():
    v1 = (PROMPTS / "extract_v1.txt").read_text(encoding="utf-8")
    v2 = (PROMPTS / "extract_v2.txt").read_text(encoding="utf-8")
    assert v2.startswith(v1 + " ") and "copy the mark exactly" in v2
    assert not re.search(r"<[A-Z]+_[0-9]+>", v2), "the prompt gives no example mark"
    assert b"\r" not in (PROMPTS / "extract_v2.txt").read_bytes()


def test_prompt_v3_is_v2_plus_the_one_tool_call_sentence():
    v2 = (PROMPTS / "extract_v2.txt").read_text(encoding="utf-8")
    v3 = prompt_file.PROMPT_PATH.read_text(encoding="utf-8")
    assert v3 == v2 + "\n\nCall the record_invoice tool exactly once; do not answer in text."
    assert b"\r" not in prompt_file.PROMPT_PATH.read_bytes()


def test_prompt_file_is_a_leaf_module():
    tree = ast.parse((ROOT / "src" / "intake" / "prompt_file.py").read_text(encoding="utf-8"))
    imported = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and (n.level or n.module == "intake")]
    assert imported == []


# ---- masked_body_within_worst_case: documents built to make a mark longer than the value it hides -----------------------------------------------
def _worst_ok(live, model_text):
    s, b = live
    p = budget.current_prices(s)
    for tier in budget.TIERS:
        body = b.request_body(ExtractRequest("0" * 64, tier, model_text=model_text))
        assert len(body) <= max(worst_bodies(b, tier))
        assert budget.worst_case(p, tier, len(body), s.model.max_tokens, s.model.overhead_tokens) <= budget.worst_case(
            p, tier, max(worst_bodies(b, tier)), s.model.max_tokens, s.model.overhead_tokens
        )


def _held_back(doc: str):
    try:
        mask.mask(doc, b"k" * 32)
    except SelfCheckFailed as e:
        return e.code
    return None


def test_masked_body_within_worst_case_one_char_quoted_secret():
    """A one-character quoted secret repeated as separate words: each 1-character hiding span would become a 10-character mark, so the model text would
    pass 40,000 characters; the document is held back before any body is built (no body, no call, cost 0)."""
    doc = ("pwd='a'\n" + ("a " * 990 + "\n") * 10)[:20000]
    assert len(doc) > 19000 and max(len(x) for x in doc.split("\n")) < mask.MASK_MAX_LINE_CHARS
    assert _held_back(doc) == "mask_too_large"


def test_masked_body_within_worst_case_many_short_values():
    """About 90 distinct short hidden values repeated up to the 20,000-character limit: the marks are longer than the values, so it is held back."""
    values = [f"v{i:02d}" for i in range(90)]
    doc = ("pwd='" + "' pwd='".join(values) + "'\n" + "\n".join(" ".join(values) for _ in range(54)))[:20000]
    assert len(doc) > 19000
    assert _held_back(doc) == "mask_too_large"


def test_masked_body_within_worst_case_sort_code_document(live):
    """A document that is accepted: its real body, for both tiers, is no larger than the worst-case body the minimum limit is built from."""
    doc = ("Sort code 20-00-00\n" * 1000)[:20000]
    m = mask.mask(doc, b"k" * 32)
    assert 20000 < len(m.text) <= mask.MASKED_MAX_CHARS
    _worst_ok(live, m.text)


def test_a_model_text_at_the_cap_is_inside_the_worst_case_body(live):
    """No kernel needed: a model text of exactly the cap, in each worst-case character, fits; the bound is the cap itself."""
    for c in WORST_CHARS:
        _worst_ok(live, c * mask.MASKED_MAX_CHARS)


def test_the_fake_backend_minimum_is_larger_and_needs_a_patch_for_a_small_cap(tmp_path):
    """The fake body escapes non-ASCII (12 bytes per U+10FFFF against 4 live), so its minimum is above the live one: a test with a SMALL fake cap must
    monkeypatch ``budget.min_limit_micro`` (builder rule, errata 75.1)."""
    s = fake_settings(tmp_path)
    from intake.model_fake import FakeBackend

    fake = len(FakeBackend(s).request_body(req(chr(0x10FFFF) * mask.MASKED_MAX_CHARS)))
    assert fake > 4 * mask.MASKED_MAX_CHARS * 2
