"""Round 14 of Q8a-1: the fixes of this round at the shared places, each with a test that fails on the code of round 13
(head 918c0345). A marker that must never be shown is built from parts so that it is no secret-shaped literal."""

from __future__ import annotations

import logging
import re
from types import SimpleNamespace

import pytest


def _marker(tag: str) -> str:
    """A made-up value that is never in the code of the package and is no secret-shaped literal."""
    return "zq-b14-" + tag + "-" + "Wm4"


# ---- Issue 1: a failing detector is logged by class only (a Bedrock-shaped error with a bare guardrail id) --------------


def test_a_failing_detector_is_logged_by_class_only(caplog):
    from hadavin_sdk.guard.injection import injection_check

    text = _marker("detector")

    class Broken:
        def check(self, text_checked, source):
            raise ValueError(text)

    with caplog.at_level(logging.WARNING):
        verdict = injection_check(Broken(), "hello", "tool")
    assert verdict.flagged and verdict.reason_code == "guard_unavailable"
    shown = " ".join(r.getMessage() for r in caplog.records)
    assert "Broken" in shown and "ValueError" in shown and text not in shown


def test_the_bedrock_detector_logs_the_class_of_a_cloud_error_never_its_text(caplog):
    """The cloud error quotes the guardrail id (a bare id: no `arn:` prefix, so no pattern of the redaction would
    hide it), a role and an account. Only the class may reach the log; the verdict is still a flag."""
    from hadavin_sdk.guard.bedrock_guardrail import GuardrailDetector
    from hadavin_sdk.guard.injection import injection_check

    guardrail_id = "wk3j" + "9f0x" + "q2lm"  # a bare id
    role = "q8a1b14-role-" + "Wm4"

    class FakeClientError(Exception):
        pass

    class Client:
        def apply_guardrail(self, **kw):
            raise FakeClientError(f"AccessDenied: {role} cannot call guardrail {guardrail_id}")

    det = GuardrailDetector(Client(), guardrail_id, "1", 0.5)
    with caplog.at_level(logging.WARNING):
        verdict = injection_check(det, "ignore the rules", "tool")
    assert verdict.flagged and verdict.reason_code == "guard_unavailable"
    shown = " ".join(r.getMessage() for r in caplog.records)
    assert "GuardrailDetector" in shown and "RuntimeError" in shown
    assert guardrail_id not in shown and role not in shown and "AccessDenied" not in shown


def test_the_bedrock_error_has_no_cause_and_no_context():
    from hadavin_sdk.guard.bedrock_guardrail import GuardrailDetector

    secret = _marker("cause")

    class Client:
        def apply_guardrail(self, **kw):
            raise OSError(secret)

    with pytest.raises(RuntimeError) as raised:
        GuardrailDetector(Client(), "g", "1", 0.5).check("some text", "tool")
    assert raised.value.__cause__ is None and raised.value.__context__ is None
    assert secret not in str(raised.value) and "OSError" in str(raised.value)


_ = SimpleNamespace  # kept for the tests that follow


# ---- Issue 5: an sslmode taken from the DSN is shown only when it is one of the six libpq words ----------------------


@pytest.mark.parametrize("iam_auth", [True, False])
def test_an_odd_sslmode_inside_the_dsn_is_never_printed_in_a_refusal(iam_auth):
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.postgres import tls_mode

    odd = "zq-b14-" + "ssl" + "-Wm4"
    dsn = f"host=db.example.invalid dbname=d user=u sslmode={odd}"
    if iam_auth:
        with pytest.raises(ConfigError) as raised:
            tls_mode(dsn, iam_auth=True)
        assert odd not in str(raised.value) and "<not shown>" in str(raised.value)
    else:
        assert (
            tls_mode(dsn) == odd
        )  # passed on to libpq, which refuses it (the driver error is class-only)
    # a verified mode without a CA bundle names the mode: a real libpq word is shown
    with pytest.raises(ConfigError, match="sslmode verify-full needs"):
        tls_mode("host=db.example.invalid dbname=d user=u", sslmode="verify-full")


@pytest.mark.parametrize(
    "mode", ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
)
def test_each_libpq_sslmode_word_is_shown_as_it_is(mode):
    from hadavin_sdk.store.postgres import _shown_mode

    assert _shown_mode(mode) == mode


# ---- Issue 8 (a): a provider error code is ONE short code; a sentence is dropped -------------------------------------------


def test_a_sentence_in_a_provider_error_detail_is_dropped_by_describe():
    from hadavin_sdk.llm.retry import describe

    class Boom(Exception):
        status_code = 429

    sentence = (
        "your key " + _marker("detail") + " ran out of quota"
    )  # 80 characters or fewer, with spaces
    assert describe(Boom("q"), lambda e: sentence) == "Boom 429"
    # Round 15: at most 32 characters, and never a run of 32 letters or digits (the shape of a key)
    assert describe(Boom("q"), lambda e: "x" * 33) == "Boom 429"
    assert describe(Boom("q"), lambda e: "x" * 32) == "Boom 429"
    assert describe(Boom("q"), lambda e: "x" * 31) == "Boom 429 " + "x" * 31
    assert describe(Boom("q"), lambda e: "x-" * 16) == "Boom 429 " + "x-" * 16
    assert (
        describe(Boom("q"), lambda e: "403 AccessDeniedException")
        == "Boom 429 403 AccessDeniedException"
    )
    assert describe(Boom("q"), lambda e: "4030 Code") == "Boom 429"
    assert describe(Boom("q"), lambda e: "rate_limit") == "Boom 429 rate_limit"


# ---- Issue 8 (b): a refused host is shown only when it looks like a host --------------------------------------------------


@pytest.mark.parametrize(
    ("host", "shown"),
    [
        ("api.example.invalid", "api.example.invalid"),
        ("localhost", "localhost"),
        ("10.0.0.5", "10.0.0.5"),
        ("::1", "::1"),
        ("deadbeef" * 8, "?"),  # a lower-case hex key: host-name characters only, no dot
        ("zq-b14-hyphenated-key-without-a-dot", "?"),
        ("two words", "?"),
        ("", "?"),
    ],
)
def test_a_refused_host_without_a_dot_that_is_no_address_is_not_shown(host, shown):
    from hadavin_sdk.guard.egress import EgressRefused, egress_check

    with pytest.raises(EgressRefused) as raised:
        egress_check(host, frozenset({"other.example.invalid"}))
    assert str(raised.value) == f"host not in egress.yaml: {shown}"


# ---- Issue 8 (c): the three Vault status sites that print a status say `?` for a text status ------------------------------


def _vault(**kw):
    from hadavin_sdk.actions.secrets_vault import VaultProvider

    return VaultProvider("https://vault.example.invalid", lambda p: "t", **kw)


class _Answer:
    def __init__(self, status, raw):
        self.status, self._raw = status, raw

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._raw


@pytest.mark.parametrize("raw", [b"<html>not json</html>", b"[1, 2]"])
def test_a_vault_answer_with_a_text_status_and_a_wrong_body_says_no_text(raw):
    from hadavin_sdk.actions.secrets_vault import VaultError

    text = _marker("status")
    p = _vault()
    p._opener = SimpleNamespace(open=lambda req, timeout=None: _Answer(text, raw))
    with pytest.raises(VaultError) as raised:
        p.call("GET", "secret/data/x")
    assert text not in str(raised.value) and "answered ?" in str(raised.value)


def test_a_vault_secret_read_with_a_text_status_says_no_text():
    from hadavin_sdk.actions.secrets_vault import VaultError

    text = _marker("fetch")
    p = _vault()
    p.authed = lambda *a, **k: (text, {})
    with pytest.raises(VaultError) as raised:
        p._fetch("name")
    assert text not in str(raised.value) and "answered ?" in str(raised.value)


# ---- Issue 8 (d): status_text never lets an int subclass print its own text -------------------------------------------------


def test_status_text_of_an_int_subclass_prints_the_number():
    from hadavin_sdk.errors import status_text

    text = _marker("subclass")

    class Sneaky(int):
        def __str__(self):
            return text

        def __repr__(self):
            return text

    assert status_text(Sneaky(404)) == "404"


# ---- Issue 8 (e): every strict model of the package hides an unknown key ----------------------------------------------------


def _all_strict_models():
    """Every `pydantic.BaseModel` subclass defined in a module under `hadavin_sdk` with `extra="forbid"`. A module that
    cannot be imported (an extra that is not installed) is listed in `NOT_IMPORTED` with the reason."""
    import importlib
    import pkgutil

    import pydantic

    import hadavin_sdk

    found, skipped = {}, []
    for info in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
        try:
            mod = importlib.import_module(info.name)
        except ImportError:
            skipped.append(info.name)
            continue
        for obj in vars(mod).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, pydantic.BaseModel)
                and obj.__module__ == mod.__name__
                and obj.model_config.get("extra") == "forbid"
            ):
                found[f"{obj.__module__}.{obj.__name__}"] = obj
    return found, skipped


_ALL, _SKIPPED = _all_strict_models()


def test_the_walk_over_the_package_finds_the_strict_models_and_skips_nothing():
    assert len(_ALL) >= 9
    assert _SKIPPED == [], f"modules that could not be imported (an extra is missing?): {_SKIPPED}"


@pytest.mark.parametrize("name", sorted(_ALL))
def test_every_strict_model_of_the_package_hides_an_unknown_key_in_its_error_text(name):
    from pydantic import ValidationError

    from hadavin_sdk.config import config_error_text

    marker = _marker("key")
    try:
        _ALL[name].model_validate({marker: marker})
    except ValidationError as exc:
        assert marker not in config_error_text(exc), name
    else:
        pytest.fail(f"{name} accepted an unknown key")


# ---- Issue 8 (g): a bundle folder name typed on the command line is shown only through `shown_name` -------------------------


def test_a_bundle_folder_name_that_is_a_sentence_is_not_printed(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle

    name = "My Case " + _marker("folder") + " now"
    (tmp_path / name).mkdir()
    with pytest.raises(BundleError) as raised:
        load_bundle(tmp_path / name)
    assert _marker("folder") not in str(raised.value) and "<not shown>" in str(raised.value)


def test_a_bundle_folder_name_that_is_word_like_is_shown(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle

    (tmp_path / "case-xyz").mkdir()
    with pytest.raises(BundleError, match="bundle case-xyz: folder name must look like case-001"):
        load_bundle(tmp_path / "case-xyz")


# ---- Issue 8 (h): the model id pattern, over many generated values ---------------------------------------------------------


def test_a_model_id_refuses_a_long_run_and_keeps_every_real_shape():
    from pydantic import ValidationError

    from hadavin_sdk.config import Route

    base = {"input_usd_per_mtok": "1", "output_usd_per_mtok": "1", "max_tokens": 10}

    def accepted(text: str) -> bool:
        try:
            Route(model_id=text, **base)
        except ValidationError:
            return False
        return True

    real = (
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "us.anthropic.claude-sonnet-5-5-v1:0",
        "claude-opus-5-5@20260101",
        "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-x-v1:0",
    )
    assert all(accepted(ok) for ok in real)
    token = "A1" * 16  # 32 letters and digits in one run: key-shaped
    for bad in (token, "x-" + token, token + "-x", "sk-" + token, "a" * 128, "a" * 129):
        assert not accepted(bad), bad
    # a key cut into pieces of 31 by separators passes: said in the comment of `Route`
    assert accepted(("a" * 31 + "-") * 3 + "b")
    alphabet = "aZ09-._:@/ ?=\n"
    state = 11
    for _ in range(3000):
        state = (state * 1103515245 + 12345) % 2**31
        text = "".join(
            alphabet[(state >> (i % 20) + i) % len(alphabet)] for i in range(1 + state % 140)
        )
        expect = (
            0 < len(text) <= 128
            and text[0].isalnum()
            and all(c.isalnum() or c in "._:@/-" for c in text)
            and re.search(r"[A-Za-z0-9]{32}", text) is None
        )
        assert accepted(text) == expect, text


# --- Issue 2: the tick module, by its tree --------------------------------------------------------------------------


def _tick_tree():
    import ast
    from pathlib import Path

    from hadavin_sdk.runtime import tick

    path = Path(tick.__file__)
    text = path.read_text(encoding="utf-8")
    return text, ast.parse(text)


def test_tick_has_no_broad_handler_no_suppression_comment_and_a_reason_above_each_swallow_site():
    """By the tree and the token stream, not by a search of the text: no handler of `Exception`, `BaseException` or a bare
    `except`; no comment that switches a lint rule off (found with `tokenize`, so a comment inside a string is not one); and
    each `Failed(...)` or `suppress(Exception)` site has a comment that starts with `# why:` on a line above it."""
    import ast
    import io
    import tokenize

    text, tree = _tick_tree()
    broad = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.ExceptHandler)
        and (
            n.type is None
            or any(
                getattr(t, "id", getattr(t, "attr", "")) in {"Exception", "BaseException"}
                for t in (n.type.elts if isinstance(n.type, ast.Tuple) else [n.type])
            )
        )
    ]
    assert broad == [], f"broad handlers at lines {broad}"
    comments = {
        t.start[0]: t.string
        for t in tokenize.generate_tokens(io.StringIO(text).readline)
        if t.type == tokenize.COMMENT
    }
    switched_off = {
        n: c for n, c in comments.items() if re.search(r"noqa|type:\s*ignore|pragma", c)
    }
    assert switched_off == {}, switched_off
    lines = text.splitlines()
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = getattr(n.func, "id", getattr(n.func, "attr", ""))
            if name == "Failed" or (name == "suppress" and "Exception" in ast.unparse(n)):
                sites.append(n.lineno)
    assert len(sites) >= 6, (
        f"the scan found only {len(sites)} swallow sites: it no longer sees them"
    )
    for line in sites:
        above = [
            lines[i].strip() for i in range(max(0, line - 4), line)
        ]  # the three lines above, and the line itself
        same = lines[line - 1]
        assert any(a.startswith("# why:") for a in above) or "# why:" in same, (
            f"tick.py:{line} has no `# why:` reason above it"
        )


@pytest.mark.parametrize(
    "module",
    [
        "azure.core.exceptions",
        "google.api_core.exceptions",
        "hvac.exceptions",
        "botocore.exceptions",
    ],
)
def test_tick_message_withholds_the_text_of_an_error_of_a_library_whatever_the_library(module):
    """The text of an error is shown only for a class that hadavin_sdk defines (and whose bases are builtins or
    hadavin_sdk): a class from any other package, however it is named, gets the fixed sentence."""
    from hadavin_sdk.runtime import tick

    marker = "zq-tick-" + "Kx7" + "-marker"
    for base in (Exception, ValueError, RuntimeError, KeyError):
        lib = type("ServiceError", (base,), {"__module__": module})
        assert marker not in tick._message(lib(marker)), module
        assert tick._message(lib(marker)) == "(details withheld)"
        sub = type(
            "Narrower", (lib,), {"__module__": "hadavin_sdk.fake_sub"}
        )  # a subclass of a library class
        assert marker not in tick._message(sub(marker)), (
            "a hadavin class with a library base shows the text"
        )
    own = tick.ConfigError(marker)
    assert tick._message(own) == marker  # the package's own sentence is shown (cut and redacted)


def test_each_logs_the_class_of_a_lost_race_at_debug_and_never_its_text(caplog):
    """The one debug line of the lost race: the label and the class, no text of the error. It is kept because a worker
    that loses a race to another worker is normal and an operator who looks for a missed item needs to see it."""
    from hadavin_sdk.runtime import tick

    marker = "zq-race-" + "Kx7" + "-marker"

    def fn(item: int) -> None:
        raise tick.StaleState(marker)

    with caplog.at_level(logging.DEBUG, logger=tick._LOG.name):
        tick._each([1], fn, "step label")
    seen = [r for r in caplog.records if "skipped" in r.getMessage()]
    assert len(seen) == 1 and "StaleState" in seen[0].getMessage()
    assert marker not in caplog.text
