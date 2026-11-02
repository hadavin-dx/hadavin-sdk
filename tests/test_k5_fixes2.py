"""Fixes for the second code review of PR #42 (egm/bhovix-core/pr42/review-code-2.md): M-A the cap is on the work (views),
m-1 the reason a document is refused, m-2 one bound, m-3/m-7 NAT64, m-4 the lookup permit, m-5 suffix grammar, m-8 nested
identifier flags, m-9 evals message, and the migration ledger refusing a database that applied the old file name."""

from __future__ import annotations

import ipaddress
import threading
import time

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults, evals
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import RunState as S
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store import migrate as mig
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

BS = chr(92)

# --- M-A: the cap is on the work, not only on the input -------------------------------------------------------------------------------


def test_the_reviewers_input_is_refused_fast():
    """87,000 U+FDFA is under the input cap but its NFKC view is 1.5 million characters: it took 23.9 s before."""
    t0 = time.perf_counter()
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_untrusted("ﷺ" * 87000, {})
    assert time.perf_counter() - t0 < 3.0


def test_nothing_is_normalised_or_neutralised_before_the_size_check():
    def work_done(_s):
        raise AssertionError("neutralise ran before the size check")

    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text("ﷺ" * 87000, {}, neutralise=work_done)


def test_an_escape_that_decodes_to_an_expanding_character_is_refused_fast():
    text = (
        BS + "ufdfa"
    ) * 40000  # 240,000 characters of escape; the unescaped view is 720,000 after NFKC
    assert len(text) < defaults.MAX_REDACT_CHARS
    t0 = time.perf_counter()
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(text, {})
    assert time.perf_counter() - t0 < 3.0


def test_a_view_over_the_cap_is_refused_whatever_the_cap_is(monkeypatch):
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", 1000)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text("ﷺ" * 60, {})  # 60 characters in, 1,080 in the view
    assert runmap.redact_text("ﷺ" * 50, {})  # 900: fine


def test_neutralising_cannot_push_the_text_over_the_cap(monkeypatch):
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", 100)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text("a" * 60, {}, neutralise=lambda s: s * 2)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(
            "é" * 60, {}, neutralise=lambda s: s * 2
        )  # a non-ASCII text goes the estimate path


def test_a_view_that_neutralising_expands_is_refused(monkeypatch):
    """The second pass neutralises each view too: a view that grows past the cap there is refused."""
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", 100)

    def grow_views_only(s: str) -> str:
        return s * 3 if s.isascii() and s.startswith("v") else s

    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text(
            "vｖ" * 20, {}, neutralise=grow_views_only
        )  # the view (NFKC of the full-width v) starts with v


def test_input_too_large_is_a_redaction_error_with_its_own_name():
    assert issubclass(runmap.InputTooLarge, runmap.RedactionError)
    with pytest.raises(runmap.InputTooLarge, match="InputTooLarge"):
        runmap.redact_value({"k": "x" * (defaults.MAX_REDACT_CHARS + 1)}, {})


# --- m-1: the reason a document is refused ----------------------------------------------------------------------------------------------


def test_a_document_whose_views_are_over_the_cap_is_document_too_large(tmp_path):
    rt, _cards = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"noaction": True}]))
    doc = ("ﷺ" * 87000).encode("utf-8")  # 261,000 bytes: under max_document_bytes
    assert len(doc) <= rt._evidence.max_document_bytes
    run = handle(rt, document=doc)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "document_too_large")


# --- m-2: one bound for the configured document size and the redactor -----------------------------------------------------------------


def test_max_document_bytes_cannot_exceed_what_the_redactor_takes(tmp_path):
    too_big = k5_cfg(
        tmp_path, config={"evidence": {"max_document_bytes": defaults.MAX_REDACT_CHARS + 1}}
    )
    with pytest.raises((ConfigError, ValidationError)):
        load_config(too_big)
    ok = k5_cfg(
        tmp_path / "ok", config={"evidence": {"max_document_bytes": defaults.MAX_REDACT_CHARS}}
    )
    assert load_config(ok).evidence.max_document_bytes == defaults.MAX_REDACT_CHARS


# --- m-3 / m-7: NAT64, stated as the code does it, and the local-use prefix tested directly ------------------------------------------


class _NotFlaggedReserved(ipaddress.IPv6Address):
    """An address the stdlib does not call reserved (Python 3.12 may not), so only OUR rule can refuse it."""

    @property
    def is_reserved(self):
        return False

    @property
    def is_private(self):
        return False


@pytest.mark.parametrize(
    "ip",
    [
        "64:ff9b::a9fe:a9fe",  # 169.254.169.254 inside NAT64
        "64:ff9b::7f00:1",  # loopback inside NAT64
        "64:ff9b::a00:1",  # 10.0.0.1 inside NAT64: refused too, the whole prefix is
        "64:ff9b::5db8:d822",  # a public address inside NAT64
    ],
)
def test_nat64_is_refused_whole(ip):
    assert http_guard._refused(ipaddress.ip_address(ip))
    assert http_guard._refused(_NotFlaggedReserved(ip))  # by our rule, not the stdlib's flags


def test_the_local_use_nat64_prefix_is_refused_by_our_rule_not_the_stdlibs():
    ip = _NotFlaggedReserved("64:ff9b:1::5db8:d822")
    assert ip in http_guard._NAT64_LOCAL
    assert ipaddress.ip_network("64:ff9b:1::/48") == http_guard._NAT64_LOCAL
    assert http_guard._refused(ip)


# --- m-4: the lookup permit comes back when the thread cannot start ----------------------------------------------------------------


def test_the_permit_is_returned_if_the_thread_cannot_start(monkeypatch):
    def refuse_to_start(self):
        raise RuntimeError("cannot start a new thread")

    with monkeypatch.context() as m:
        m.setattr(threading.Thread, "start", refuse_to_start)
        for _ in range(http_guard.MAX_STUCK_LOOKUPS + 3):  # more tries than permits
            with pytest.raises(RuntimeError, match="cannot start"):
                http_guard._resolve("a.example.test", 443)
    for _ in range(http_guard.MAX_STUCK_LOOKUPS):  # every permit is still there
        assert http_guard._STUCK.acquire(blocking=False)
    for _ in range(http_guard.MAX_STUCK_LOOKUPS):
        http_guard._STUCK.release()


# --- m-5: the suffix grammar's cost is bounded -------------------------------------------------------------------------------------------


def test_adjacent_variable_repeats_are_refused():
    bad = "[a]{0,64}[a]{0,64}[a]{0,64}[a]{0,64}-"
    assert "variable-length" in (tools_mod.suffix_problem(bad) or "")
    assert tools_mod.suffix_problem("[a]{1,9}[b]{1,9}-") is None  # two are fine
    assert (
        tools_mod.suffix_problem("-[0-9a-f]{5,10}-[a-z0-9]{5}-[a-z0-9]{5}") is None
    )  # fixed repeats are free


def test_the_worst_allowed_suffix_is_fast_on_a_hostile_name():
    """Two overlapping variable repeats of 64 on a name that never matches: polynomial, and measured."""
    from hadavin_sdk.runtime import evidence

    suffix = "[a]{1,64}[a]{1,64}-"
    assert tools_mod.suffix_problem(suffix) is None
    t0 = time.perf_counter()
    for _ in range(20):
        evidence.contains("pod-" + "a" * 5000, "pod", suffix=suffix)
    assert time.perf_counter() - t0 < 5.0


# --- m-8: an identifier flag below the top level would be silently ignored ----------------------------------------------------------


def test_a_nested_identifier_flag_is_refused_at_load(tmp_path):
    nested = {
        "input_schema": {
            "type": "object",
            "required": ["target"],
            "additionalProperties": False,
            "properties": {
                "target": {
                    "type": "object",
                    "identifier": False,
                    "properties": {"host": {"type": "string", "identifier": True}},
                }
            },
        }
    }
    cfg = k5_cfg(tmp_path, action=nested)
    with pytest.raises(ConfigError, match="below the top level"):
        load_registry(load_config(cfg))


def test_a_top_level_flag_and_a_property_named_identifier_are_fine(tmp_path):
    ok = {
        "input_schema": {
            "type": "object",
            "required": ["host"],
            "additionalProperties": False,
            "properties": {
                "host": {"type": "string", "identifier": True, "pattern": "[a-z]{1,9}"},
                "meta": {
                    "type": "object",
                    "identifier": False,
                    "properties": {"identifier": {"type": "string"}},
                },
            },
        }
    }
    load_registry(load_config(k5_cfg(tmp_path, action=ok)))


# --- m-9: an eval input the redactor refuses says which one -------------------------------------------------------------------------------


def test_a_golden_input_over_the_cap_is_a_config_error_naming_it(live_cfg_dir):
    cfg = load_config(live_cfg_dir)
    for path in cfg.inputs_dir.iterdir():
        path.write_bytes(b"x" * (defaults.MAX_REDACT_CHARS + 10))
    reg = load_registry(cfg)

    class Never:
        def chat(self, *a, **k):
            raise AssertionError("the model must not be reached")

    with pytest.raises(ConfigError, match="cannot be redacted"):
        evals.gate(reg, Never(), "test-agent")


# --- merge condition 4: a database that applied the old file name is refused, not silently migrated ---------------------------------------


def _folder(tmp_path, names):
    """The real migrations' SQL (so the grant map still matches the tables) under the renamed file names:
    0005_reservations stands in for #49's file (empty), 0006_evidence is today's 0005_evidence."""
    folder = tmp_path / "migrations"
    folder.mkdir(parents=True)
    for n in names:
        real = mig.MIGRATIONS / (n if n[:4] <= "0004" else "0005_evidence.sql")
        body = "-- empty" if n == "0005_reservations.sql" else real.read_text(encoding="utf-8")
        (folder / n).write_text(body, encoding="utf-8")
    return mig._migration_files(folder)


_REAL = sorted(p.name for p in mig.MIGRATIONS.glob("*.sql"))
RENAMED = [*_REAL[:4], "0005_reservations.sql", "0006_evidence.sql"]


def test_the_renamed_tree_is_a_valid_ledger_and_two_files_with_one_number_are_not(tmp_path):
    assert mig.check_ledger(_folder(tmp_path, RENAMED)) == []
    clash = _folder(tmp_path / "x", [*RENAMED[:4], "0005_reservations.sql", "0005_evidence.sql"])
    assert mig.check_ledger(clash) == ["two migrations are numbered 0005"]


def test_a_database_that_applied_the_old_name_is_refused_and_nothing_is_applied(
    tmp_path, monkeypatch
):
    pytest.importorskip("psycopg")
    from tests.contracts.kinds.store_postgres import pg_schema

    files = _folder(tmp_path, RENAMED)
    gen = pg_schema(migrated=False)
    dsn = next(gen)
    try:
        import psycopg

        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(
                "CREATE TABLE schema_migrations "
                "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            db.execute("INSERT INTO schema_migrations (version) VALUES ('0005_evidence')")
        monkeypatch.setattr(mig, "_migration_files", lambda: files)
        with pytest.raises(ConfigError, match="0005_evidence") as err:
            mig.migrate(dsn)
        assert "by hand" in str(err.value)  # the repair path is in the message
        assert "0006_evidence" not in str(err.value)  # generic: no file name of ours is hard-coded
        with psycopg.connect(dsn) as db:
            rows = [r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()]
        assert rows == ["0005_evidence"]  # the refusal applied nothing
    finally:
        gen.close()
