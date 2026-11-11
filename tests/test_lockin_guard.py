"""CI lock-in guard (owner rule 2026-10-31, "no single dependency"; spec: single-dependency audit §3a-3c).

Three rules, each with plant tests that prove it fails on a planted violation:
  a. a vendor SDK is imported only inside its own kind module; open-source libraries stay in their layer;
  b. every capability has a neutral prod kind and at least two prod kinds, or a dated EXCEPTIONS entry;
  c. no vendor identifiers (names, regions, hosts, model ids, account ids) in core logic: in its strings
     (`literal_problems`) and in the names it gives to modules, functions, classes, parameters, variables and
     attributes (`identifier_problems`).
Known violations go in dated lists. A stale entry (its violation is gone) fails the test, and so does an
overdue one, so an entry cannot linger.

What rule c does not see (the limits marked [pinned] have a test, so a later change to them is deliberate):
  - any word that is not in VENDOR_WORDS: the scans know only those words [pinned];
  - inside a string, a vendor word without a boundary on BOTH sides. Before the word must come the start of the
    string or one of `/ _ . - = ? & # @ , ; ( ) +`; after it one of those, a `:`, or the end of the string. So
    free prose (`"post to Slack"`, `"x/slack y"`), a word glued in camel case (`"/slackActions"`), a word beside
    `|` (`"slack|teams"`: three command-recognising regular expressions of the approval gate use `|` beside such
    words) and a two-part name written with a separator (`"/pager-duty/hook"`) are not seen [pinned];
  - an f-string or a `+` join is reported once for the joined text and once for each constant part that hits by
    itself, so `f"/slack/{x}"` gives two lines and needs two allow entries [pinned];
  - comments and docstrings (only `approvals/receiver.py` is checked as whole text);
  - in a name, a word glued to capitals (`AWSclient`) or to other lower-case letters (`awsome`) [pinned]; a name
    that is only read (it is scanned where it is bound or imported). The reverse also holds: two neighbouring
    parts that happen to spell a word are reported (`TeamS`, `team_s`, `open_ai`) [pinned];
  - in a name, a letter of another script that looks like a Latin one (`sl\u0430ck` with a Cyrillic a) [pinned].
    Python itself folds compatibility forms such as full-width letters before the scan sees a name;
  - files that are not Python (YAML, Markdown, SQL outside the migrations rule) [pinned], and everything outside
    `src`: tests and demos are not scanned at all.
"""

import ast
import itertools
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.backends.table import DEMO_ONLY, NOT_PROD, TABLE

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = "hadavin_sdk"
TODAY = datetime.now(UTC).date()  # expiry checks fail after a review_by date, by design


@dataclass(frozen=True)
class Pending:
    """A known violation with a scheduled fix."""

    reason: str
    fix_ref: str
    decided: date
    review_by: date  # the test fails after this date


# ---------------------------------------------------------------------------------------------- rule a

BASE_OK = {"pydantic", "pydantic_settings", "yaml"}  # base dependencies, allowed anywhere
_AWS = {
    f"{PKG}.llm.bedrock",
    f"{PKG}.actions.secrets_aws",
    f"{PKG}.audit.anchor_s3",
    f"{PKG}.audit.signer_aws",
    f"{PKG}.guard.bedrock_guardrail",
    f"{PKG}.store.auth_aws",
}
_GCP = {
    f"{PKG}.llm.anthropic",  # Vertex token errors (google-auth)
    f"{PKG}.actions.secrets_gcp",
    f"{PKG}.audit.anchor_gcs",
    f"{PKG}.audit.signer_gcp",
}
_AZURE = {
    f"{PKG}.actions.secrets_azure",
    f"{PKG}.audit.anchor_azure",
    f"{PKG}.audit.signer_azure",
}
VENDOR_IMPORTS: dict[str, set[str]] = {
    "boto3": _AWS,
    "botocore": _AWS,  # the same set object
    "anthropic": {f"{PKG}.llm.anthropic"},
    "google": _GCP,
    "azure": _AZURE,
    # K5: the Kubernetes source speaks the REST API over the stdlib; no client library is allowed anywhere.
    "kubernetes": set(),
    # added with their kinds: hvac, slack_sdk, opentelemetry
}
LIBRARY_IMPORTS: dict[str, set[str]] = {  # open-source libraries kept in their layer
    "psycopg": {f"{PKG}.store.postgres", f"{PKG}.store.migrate"},
    "cryptography": {
        f"{PKG}.audit.signer",
        f"{PKG}.audit.signer_aws",
        f"{PKG}.audit.signer_gcp",
    },
    "markdown_it": {f"{PKG}.approvals.gate"},
    # added later: fastapi, authlib, webauthn (portal_api only)
}
# (top-level import, module) -> scheduled fix. Empty on main: P3b moved every vendor import into its kind.
PENDING: dict[tuple[str, str], Pending] = {}
DYNAMIC_IMPORT_OK = {
    f"{PKG}.backends.factory",
    f"{PKG}.actions.executor",
    f"{PKG}.tools",
}  # table factories; contract hooks; the tool manifest's `function` (resolved from tool_modules only)
# Vendor modules that are helpers of a kind, not TABLE factories themselves.
VENDOR_HELPERS = {f"{PKG}.store.auth_aws"}


def module_name(src: Path, path: Path) -> str:
    parts = list(path.relative_to(src).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _dynamic_target(node: ast.Call) -> tuple[bool, str | None]:
    """Is this a call to import_module / __import__, and with which constant name."""
    f = node.func
    name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
    if name not in {"import_module", "__import__"}:
        return False, None
    arg = node.args[0] if node.args else None
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return True, arg.value
    return True, None


def import_problems(
    src: Path,
    vendor: dict[str, set[str]],
    library: dict[str, set[str]],
    pending: dict[tuple[str, str], Pending],
    dynamic_ok: set[str],
    today: date,
) -> list[str]:
    out: list[str] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(src.rglob("*.py")):
        mod = module_name(src, path)
        found: list[str] = []
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    out.append(f"{mod}: relative import (use an absolute one)")
                elif node.module:
                    found.append(node.module)
            elif isinstance(node, ast.Call):
                dynamic, const = _dynamic_target(node)
                if dynamic and mod not in dynamic_ok:
                    out.append(f"{mod}: dynamic import outside DYNAMIC_IMPORT_OK")
                if const:
                    found.append(const)
        for name in found:
            top = name.split(".")[0]
            seen.add((top, mod))
            if top == "importlib" and mod not in dynamic_ok:
                out.append(f"{mod}: imports importlib (aliased dynamic imports hide from the scan)")
            allowed = (
                top in sys.stdlib_module_names
                or top == PKG
                or top in BASE_OK
                or mod in vendor.get(top, set())
                or mod in library.get(top, set())
                or (top, mod) in pending
            )
            if not allowed:
                where = (
                    "vendor SDK" if top in vendor else "library" if top in library else "unknown"
                )
                out.append(f"{mod}: imports {top} ({where}) outside its allowed modules")
    for key, p in pending.items():
        if key not in seen:
            out.append(f"PENDING {key} is fixed: delete the entry")
        if p.review_by < today:
            out.append(
                f"PENDING {key} is overdue ({p.review_by}): fix it or re-decide with a new date"
            )
    return out


def factory_modules() -> set[str]:
    return {e.factory.split(":")[0] for kinds in TABLE.values() for e in kinds.values()}


def vendor_module_problems(
    src: Path, vendor: dict[str, set[str]], factories: set[str], helpers: set[str]
) -> list[str]:
    """Every vendor module that exists is a kind (a TABLE factory module) or a declared helper of one."""
    out = []
    for mod in sorted(set().union(*vendor.values())):
        rel = Path(*mod.split("."))
        if (
            not (src / rel.with_suffix(".py")).is_file()
            and not (src / rel / "__init__.py").is_file()
        ):
            continue  # named ahead of time: skipped until it exists
        if mod not in factories | helpers:
            out.append(
                f"{mod}: imports a vendor SDK but is neither a TABLE kind nor a VENDOR_HELPER"
            )
    for mod in helpers:
        if mod not in set().union(*vendor.values()):
            out.append(f"VENDOR_HELPERS {mod} is not a vendor module: delete the entry")
    return out


def test_vendor_sdks_stay_inside_their_kind_modules():
    assert (
        import_problems(SRC, VENDOR_IMPORTS, LIBRARY_IMPORTS, PENDING, DYNAMIC_IMPORT_OK, TODAY)
        == []
    )


def test_every_table_factory_is_a_core_module():
    outside = [m for m in factory_modules() if m.split(".")[0] != PKG]
    assert outside == [], "a kind's factory must live in hadavin_sdk, never in a vendor package"


def test_a_neutral_kind_has_no_vendor_only_path():
    """neutral is hand-set; at least keep it off kinds whose module is a plain vendor SDK without an
    endpoint to point elsewhere (the S3 anchor is neutral only through `endpoint_url`)."""
    from hadavin_sdk.backends.table import S3ObjectLockSettings

    assert "endpoint_url" in S3ObjectLockSettings.model_fields
    for cap, kinds in TABLE.items():
        for kind, entry in kinds.items():
            if entry.neutral and entry.factory.split(":")[0] in set().union(
                *VENDOR_IMPORTS.values()
            ):
                assert (cap, kind) == ("anchor", "s3_object_lock"), (cap, kind)


def _source_docstring(mod: str) -> str:
    """The module docstring read from the source file: no import, so a kind that needs an optional extra
    (signer, aws, pg) is checked on a default demo install too."""
    rel = Path(*mod.split("."))
    path = SRC / rel.with_suffix(".py")
    if not path.is_file():
        path = SRC / rel / "__init__.py"
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def neutral_problems(table: dict, vendor: set[str]) -> list[str]:
    """`neutral` is hand-set, so each neutral kind must show it: its module imports no vendor SDK (the S3
    anchor is the one exception and must offer `endpoint_url`) and its module docstring states the neutral
    protocol it speaks on a `Neutral protocol:` line."""
    out = []
    for cap, kinds in table.items():
        for kind, entry in kinds.items():
            if not entry.neutral:
                continue
            mod = entry.factory.split(":")[0]
            if mod in vendor and not (
                (cap, kind) == ("anchor", "s3_object_lock")
                and "endpoint_url" in entry.settings.model_fields
            ):
                out.append(f"{cap} {kind}: neutral but module {mod} imports a vendor SDK")
            if "Neutral protocol:" not in (_source_docstring(mod)):
                out.append(f"{cap} {kind}: module {mod} states no neutral protocol")
    return out


def test_every_neutral_kind_has_evidence():
    assert neutral_problems(TABLE, set().union(*VENDOR_IMPORTS.values())) == []


def test_plant_neutral_kinds_without_evidence_are_caught():
    from hadavin_sdk.backends.table import Entry, KindSettings

    table = {
        "x": {
            "bare": Entry(KindSettings, "hadavin_sdk.config:Config", neutral=True),
            "sdk": Entry(KindSettings, "hadavin_sdk.audit.signer_aws:build", neutral=True),
        }
    }
    found = neutral_problems(table, set().union(*VENDOR_IMPORTS.values()))
    assert any("bare: module hadavin_sdk.config states no neutral" in f for f in found)
    assert any("sdk: neutral but module" in f for f in found)


def test_every_vendor_module_is_a_kind():
    assert vendor_module_problems(SRC, VENDOR_IMPORTS, factory_modules(), VENDOR_HELPERS) == []


def test_botocore_shares_the_boto3_set():
    assert VENDOR_IMPORTS["botocore"] is VENDOR_IMPORTS["boto3"]


def _plant(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / PKG / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return tmp_path


def _imports(root: Path, pending=None, today: date = date(2026, 11, 1)) -> list[str]:
    return import_problems(
        root, VENDOR_IMPORTS, LIBRARY_IMPORTS, pending or {}, DYNAMIC_IMPORT_OK, today
    )


def test_plant_vendor_sdk_in_core_module_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import boto3\n")
    assert _imports(root) == [
        f"{PKG}.runtime.x: imports boto3 (vendor SDK) outside its allowed modules"
    ]


def test_plant_lazy_vendor_import_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "def f():\n    from azure.identity import X\n")
    assert len(_imports(root)) == 1


def test_plant_unknown_third_party_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import requests\n")
    assert "requests (unknown)" in _imports(root)[0]


def test_plant_library_outside_its_layer_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import psycopg\n")
    assert "psycopg (library)" in _imports(root)[0]


def test_plant_relative_import_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "from . import y\n")
    assert "relative import" in _imports(root)[0]


def test_plant_aliased_dynamic_import_is_caught(tmp_path):
    root = _plant(
        tmp_path, "runtime/x.py", "from importlib import import_module as im\nim('boto3')\n"
    )
    assert any("imports importlib" in p for p in _imports(root))


def test_plant_dynamic_import_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import importlib\nimportlib.import_module('boto3')\n")
    problems = _imports(root)
    assert any("dynamic import" in p for p in problems)
    assert any("imports boto3" in p for p in problems)  # the constant is also checked as an import


def test_plant_dunder_import_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "__import__(name)\n")
    assert any("dynamic import" in p for p in _imports(root))


def test_an_allowed_vendor_module_and_dynamic_hook_pass(tmp_path):
    _plant(tmp_path, "llm/bedrock.py", "import boto3\nfrom botocore.config import Config\n")
    root = _plant(tmp_path, "actions/executor.py", "import importlib\nimportlib.import_module(x)\n")
    assert _imports(root) == []


def test_plant_stale_pending_entry_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import json\n")
    entry = Pending("r", "P0", date(2026, 10, 31), date(2026, 11, 30))
    problems = _imports(root, {("boto3", f"{PKG}.runtime.x"): entry})
    assert problems == [f"PENDING ('boto3', '{PKG}.runtime.x') is fixed: delete the entry"]


def test_plant_overdue_pending_entry_is_caught(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import boto3\n")
    entry = Pending("r", "P0", date(2026, 10, 1), date(2026, 10, 15))
    problems = _imports(root, {("boto3", f"{PKG}.runtime.x"): entry})
    assert len(problems) == 1 and "overdue" in problems[0]


def test_a_live_pending_entry_allows_its_import(tmp_path):
    root = _plant(tmp_path, "runtime/x.py", "import boto3\n")
    entry = Pending("r", "P0", date(2026, 10, 31), date(2026, 11, 30))
    assert _imports(root, {("boto3", f"{PKG}.runtime.x"): entry}) == []


def test_plant_vendor_module_that_is_not_a_kind_is_caught(tmp_path):
    root = _plant(tmp_path, "llm/bedrock.py", "import boto3\n")
    problems = vendor_module_problems(root, VENDOR_IMPORTS, set(), VENDOR_HELPERS)
    assert any("neither a TABLE kind nor a VENDOR_HELPER" in p for p in problems)


def test_plant_stale_vendor_helper_is_caught(tmp_path):
    problems = vendor_module_problems(tmp_path, VENDOR_IMPORTS, set(), {f"{PKG}.runtime.x"})
    assert problems == [f"VENDOR_HELPERS {PKG}.runtime.x is not a vendor module: delete the entry"]


# ---------------------------------------------------------------------------------------------- rule b

NULL_KINDS = {("signer", "none"), ("anchor", "none")}  # never count as a prod kind


@dataclass(frozen=True)
class ExceptionEntry:
    status: str  # "accepted" (a reasoned permanent exception) or "pending" (a scheduled fix)
    reason: str
    trigger: str  # what ends it, or the fix ref
    decided: date
    review_by: date


EXCEPTIONS: dict[str, ExceptionEntry] = {
    "store": ExceptionEntry(
        "accepted",
        "PostgreSQL: open source, on every cloud and on-prem; the Store Protocol is the seam",
        "a client who refuses Postgres (SQLite kind)",
        date(2026, 10, 31),
        date(2027, 4, 30),
    ),
    "audit": ExceptionEntry(
        "accepted",
        "chain is our own code on the store; the signer and anchor are the pluggable parts",
        "none",
        date(2026, 10, 31),
        date(2027, 4, 30),
    ),
    "channel": ExceptionEntry(
        "accepted",
        "Slack is the only interactive approval kind in the pilot (owner, design v5 11.6)",
        "first client without Slack (Teams or email-link kind, Phase 2)",
        date(2026, 10, 31),
        date(2027, 1, 31),
    ),
    "sources": ExceptionEntry(
        "accepted",
        "Kubernetes (open source, runs on every cloud and on-prem) is the only read-source kind built; the "
        "Source Protocol and the sources.kinds registry are the seam",
        "K5-ITO: first client that needs a second source kind",
        date(2026, 11, 11),
        date(2027, 4, 30),
    ),
}


@dataclass(frozen=True)
class _E:
    neutral: bool = False


def _source_kinds() -> dict:
    """The live read-source registry, imported here and not at the top of this file: a later source kind whose
    module needs an optional extra must not stop the whole guard from being collected."""
    from hadavin_sdk.sources.kinds import KINDS

    return KINDS


def source_table(kinds=None) -> dict[str, dict[str, _E]]:
    """The read-source registry (`sources.kinds.KINDS`) as one more capability for rule b. A source kind has no
    hand-set `neutral` flag: it counts as neutral when the module of its settings states a `Neutral protocol:`
    line (the evidence `neutral_problems` asks of a table kind) and neither that module nor the module of its
    `build` function is a vendor module."""
    kinds = _source_kinds() if kinds is None else kinds
    return {
        "sources": {
            name: _E(
                "Neutral protocol:" in _source_docstring(kind.settings.__module__)
                and kind.settings.__module__ not in VENDOR_MODULES
                and kind.build.__module__ not in VENDOR_MODULES
            )
            for name, kind in kinds.items()
        }
    }


def coverage_table(kinds=None) -> dict:
    """The kind table plus the read-source registry: what rule b is held against."""
    assert "sources" not in TABLE, "the kind table gained a 'sources' capability: drop the adapter"
    return {**TABLE, **source_table(kinds)}


def coverage_problems(
    table, demo_only, not_prod, null_kinds, exceptions: dict[str, ExceptionEntry], today: date
) -> list[str]:
    out = []
    for cap, kinds in table.items():
        prod = {k: e for k, e in kinds.items() if (cap, k) not in demo_only | not_prod | null_kinds}
        ok = any(e.neutral for e in prod.values()) and len(prod) >= 2
        if not ok and cap not in exceptions:
            out.append(
                f"{cap}: needs a neutral prod kind and >= 2 prod kinds, or an EXCEPTIONS entry"
            )
        if ok and cap in exceptions:
            out.append(f"{cap}: passes now, delete its EXCEPTIONS entry")
    for name, ex in exceptions.items():
        if name not in table:
            out.append(f"{name}: exception names no capability: delete the entry")
        if not ex.reason or not ex.trigger:
            out.append(f"{name}: exception needs a reason and a trigger")
        if ex.review_by < today:
            out.append(f"{name}: exception overdue (review_by {ex.review_by})")
    return out


def test_every_capability_has_a_neutral_prod_kind_and_two_prod_kinds():
    # A new source kind changes what the `sources` exception says: re-read that entry, then widen this set.
    assert set(_source_kinds()) == {"kubernetes"}, (
        "the read-source registry changed (or a test left a kind registered): re-read the `sources` exception"
    )
    assert (
        coverage_problems(coverage_table(), DEMO_ONLY, NOT_PROD, NULL_KINDS, EXCEPTIONS, TODAY)
        == []
    )


def test_the_source_registry_needs_its_exception_entry():
    without = {name: ex for name, ex in EXCEPTIONS.items() if name != "sources"}
    assert coverage_problems(coverage_table(), DEMO_ONLY, NOT_PROD, NULL_KINDS, without, TODAY) == [
        "sources: needs a neutral prod kind and >= 2 prod kinds, or an EXCEPTIONS entry"
    ]
    # and the entry cannot stay if the adapter is dropped
    assert coverage_problems(TABLE, DEMO_ONLY, NOT_PROD, NULL_KINDS, EXCEPTIONS, TODAY) == [
        "sources: exception names no capability: delete the entry"
    ]


def _source_kind_in(settings_module: str, build_module: str | None = None) -> SimpleNamespace:
    """A stand-in source kind: its settings class lives in `settings_module`, its build function in
    `build_module` (the same module when not given)."""

    def build(settings, fetch):
        return None

    build.__module__ = build_module or settings_module
    settings = type("PlantedSettings", (), {"__module__": settings_module})
    return SimpleNamespace(settings=settings, build=build)


def test_a_source_kind_is_neutral_only_with_the_docstring_line_and_outside_the_vendor_modules():
    assert source_table()["sources"] == {"kubernetes": _E(True)}
    neutral, vendor = f"{PKG}.sources.kubernetes", f"{PKG}.audit.anchor_s3"
    assert "Neutral protocol:" in _source_docstring(vendor) and vendor in VENDOR_MODULES
    planted = source_table(
        {
            "ok": _source_kind_in(neutral),
            "no_line": _source_kind_in(f"{PKG}.config"),  # its docstring states no neutral protocol
            "vendor": _source_kind_in(vendor),  # states the line, but is a vendor module
            "vendor_build": _source_kind_in(neutral, vendor),  # neutral settings, vendor build
        }
    )["sources"]
    assert planted == {
        "ok": _E(True),
        "no_line": _E(False),
        "vendor": _E(False),
        "vendor_build": _E(False),
    }


def test_plant_a_second_source_kind_makes_the_sources_exception_stale():
    real = _source_kinds()["kubernetes"]
    problems = coverage_problems(
        coverage_table({"kubernetes": real, "second": real}),
        DEMO_ONLY,
        NOT_PROD,
        NULL_KINDS,
        EXCEPTIONS,
        TODAY,
    )
    assert problems == ["sources: passes now, delete its EXCEPTIONS entry"]
    # two kinds of which none is neutral still need the entry
    vendor_only = {k: _source_kind_in(f"{PKG}.audit.anchor_s3") for k in ("a", "b")}
    without = {name: ex for name, ex in EXCEPTIONS.items() if name != "sources"}
    assert coverage_problems(
        coverage_table(vendor_only), DEMO_ONLY, NOT_PROD, NULL_KINDS, without, TODAY
    ) == ["sources: needs a neutral prod kind and >= 2 prod kinds, or an EXCEPTIONS entry"]


def test_the_anchor_is_a_capability_with_a_prod_kind_besides_s3():
    assert {k for k in TABLE["anchor"] if k != "none"} >= {"s3_object_lock", "azure_immutable_blob"}


def _cov(table, exceptions=None, demo_only=frozenset(), today=date(2026, 11, 1)) -> list[str]:
    return coverage_problems(table, demo_only, NOT_PROD, NULL_KINDS, exceptions or {}, today)


def test_plant_one_vendor_kind_without_an_entry_is_caught():
    assert len(_cov({"x": {"aws": _E()}})) == 1


def test_plant_only_neutral_kind_being_demo_only_is_caught():
    table = {"x": {"mem": _E(True), "aws": _E(), "gcp": _E()}}
    assert len(_cov(table, demo_only=frozenset({("x", "mem")}))) == 1


def test_plant_a_capability_counting_only_none_is_caught():
    table = {"signer": {"none": _E(True), "aws": _E()}}
    assert len(_cov(table)) == 1


def test_plant_two_vendor_kinds_with_no_neutral_one_is_caught():
    assert len(_cov({"x": {"aws": _E(), "gcp": _E()}})) == 1


def test_two_kinds_with_one_neutral_pass():
    assert _cov({"x": {"vault": _E(True), "aws": _E()}}) == []


def test_plant_stale_exception_is_caught():
    ex = {"x": ExceptionEntry("pending", "r", "t", date(2026, 10, 1), date(2026, 12, 1))}
    assert _cov({"x": {"vault": _E(True), "aws": _E()}}, ex) == [
        "x: passes now, delete its EXCEPTIONS entry"
    ]


def test_plant_overdue_exception_is_caught():
    ex = {"x": ExceptionEntry("accepted", "r", "t", date(2026, 10, 1), date(2026, 10, 15))}
    problems = _cov({"x": {"aws": _E()}}, ex)
    assert len(problems) == 1 and "overdue" in problems[0]


def test_plant_exception_for_a_missing_capability_is_caught():
    ex = {"gone": ExceptionEntry("accepted", "r", "t", date(2026, 10, 1), date(2027, 1, 1))}
    assert len(_cov({}, ex)) == 1


def test_plant_exception_without_a_reason_is_caught():
    ex = {"x": ExceptionEntry("accepted", "", "t", date(2026, 10, 1), date(2027, 1, 1))}
    assert any("needs a reason" in p for p in _cov({"x": {"aws": _E()}}, ex))


# ---------------------------------------------------------------------------------------------- rule c

VENDOR_MODULES = {
    # the vendor SDK modules (rule a's sets), plus vendor modules built on the standard library only
    *set().union(*VENDOR_IMPORTS.values()),
    f"{PKG}.llm.gemini",
    f"{PKG}.llm.anthropic",
    f"{PKG}.approvals.slack",
    f"{PKG}.approvals.slack_channel",
    f"{PKG}.guard.redact",  # detects vendor secrets by design
}
# (module, literal) -> why this literal may stay in an otherwise neutral module. Stale entries fail.
LITERAL_OK: dict[tuple[str, str], str] = {
    (
        f"{PKG}.approvals.gate",
        "aws",
    ): "G4 command shape: one of many programs (tests/test_g4_parity.py)",
    (f"{PKG}.approvals.gate", "s3"): "G4 read-only shape: `aws s3 ls` (tests/test_g4_parity.py)",
    (f"{PKG}.config", "slack"): "the retired slice 1 config key, refused with its new place",
    (
        f"{PKG}.llm.openai_compat",
        r"^(?:gpt-[\w.-]+|o\d[\w.-]*|chatgpt-[\w.-]+)$",
    ): "the OpenAI protocol's own moving aliases; this kind exists to speak that protocol",
    (
        f"{PKG}.guard.producers",
        "guard/bedrock_guardrail.py",
    ): "the redaction registry must list every module that sends text to a model or a vendor screen, by file "
    "path; data read by tests/test_k5_producers.py, not a call into the vendor module",
    (
        f"{PKG}.llm.openai_compat",
        "openai_compat",
    ): "the kind's own name in error messages; the name of an open wire format that several servers speak "
    "(Neutral protocol line of llm/openai_compat.py; neutral=True in backends/table.py)",
    (
        f"{PKG}.approvals.gate",
        "gcloud",
    ): "G4 command shape: one of many programs (tests/test_g4_parity.py); same exception as 'aws' above",
    (
        f"{PKG}.tools",
        "metadata.google.internal",
    ): "a cloud metadata host name the fetch guard refuses: naming it is the control (tests/test_http_metadata.py)",
    (
        f"{PKG}.tools",
        ".metadata.google.internal",
    ): "the same refused metadata host, as a suffix of longer names",
    (
        f"{PKG}.backends.table",
        "gcs_retention_lock",
    ): "the kind's own name in its settings class",
}
# (module, name) -> why this name may hold a vendor word in an otherwise neutral module. Stale entries fail. An
# entry covers every binding of that name in that module, whatever binds it (a def, a variable, an import). A
# module's own name has a key of its own, (module, "module:<segment>"), for each segment of its dotted name that
# holds a vendor word (so a package folder `aws/` needs one entry in each module under it); such an entry does
# not allow a variable of the same name.
IDENTIFIER_OK: dict[tuple[str, str], str] = {
    (
        f"{PKG}.approvals.gate",
        "_AWS_READ_PREFIXES",
    ): "G4 command shape: the read-verb prefixes of the aws program only; same exception as LITERAL_OK "
    "(approvals.gate, 'aws') (tests/test_g4_parity.py)",
    (
        f"{PKG}.backends.table",
        "OpenAICompatSettings",
    ): "settings class of the neutral openai_compat kind: an open wire format, not one vendor's service",
    (
        f"{PKG}.backends.table",
        "GcsRetentionLockSettings",
    ): "settings class of the gcs_retention_lock anchor kind, declared in the kind table like the other vendor "
    "kinds; kept out of the skipped names so that the strings inside it stay scanned",
    (
        f"{PKG}.llm.openai_compat",
        "OpenAICompatLLM",
    ): "class of the neutral openai_compat kind (open wire format)",
    (
        f"{PKG}.llm.openai_compat",
        "module:openai_compat",
    ): "module of the neutral openai_compat kind (open wire format); renaming the kind would break every config "
    "that says kind: openai_compat",
    (
        f"{PKG}.store.postgres",
        "auth_aws",
    ): "lazy import of the declared VENDOR_HELPER for IAM database sign-in",
}
_TABLE_MODULE = f"{PKG}.backends.table"
_TABLE_VENDOR_NAME = re.compile(
    r"^_?(aws|bedrock|anthropic|gemini|s3|slack|gcp|azure|vertex)", re.IGNORECASE
)
# The top-level classes and functions of backends.table (the kind table, where vendor kinds are declared) that are
# skipped with everything inside them: by the string scan through the prefix pattern above, by the name scan through
# this set. test_the_table_skip_is_the_pinned_set holds the two equal, so the prefix pattern cannot match a new
# thing in the table file without an edit here.
TABLE_VENDOR_NAMES = frozenset(
    {
        "AnthropicSettings",
        "BedrockSettings",
        "GeminiSettings",
        "AwsSecretsManagerSettings",
        "S3ObjectLockSettings",
        "AzureImmutableBlobSettings",
        "AwsKmsSettings",
        "AzureKeyVaultKeySettings",
        "GcpKmsSettings",
        "AzureKeyVaultSettings",
        "GcpSecretManagerSettings",
        "SlackSettings",
        "_aws_host",
        "_aws",
        "_vertex_host",
        "_anthropic_hosts",
        "_s3_anchor_hosts",
    }
)
# The word list shared by the first two PATTERNS entries and the name scan. The first 15 words are the list this
# guard always had; the rest were added with the name scan (Q8a-2). Those scans know only these words. The
# "vendor header" entry, `_SQL_LITERAL` and `_TABLE_VENDOR_NAME` keep their own shorter lists.
VENDOR_WORDS = (
    "slack",
    "teams",
    "aws",
    "azure",
    "gcp",
    "github",
    "gitlab",
    "bedrock",
    "anthropic",
    "vertex",
    "gemini",
    "openai",
    "kms",
    "s3",
    "foundry",
    "google",
    "gcs",
    "gcloud",
    "amazon",
    "microsoft",
    "alibaba",
    "oracle",
    "digitalocean",
    "openstack",
    "cloudwatch",
    "pagerduty",
)
_W = "|".join(VENDOR_WORDS)
# What may stand beside a vendor word in a path, a key, a query string, an address or a list. `|` is left out:
# on main it adds three hits, all regular expressions of the approval gate that recognise commands.
_SEP = "/_.=?&#@,;()+-"
PATTERNS = {
    "bare vendor name": rf"^({_W})(:|$)",
    # A string that holds one vendor word matches at most one of these first two entries.
    "vendor word in a path or key": rf"[{_SEP}]({_W})([:{_SEP}]|$)|^({_W})[{_SEP}]",
    "vendor header": r"x-(slack|amz|goog|ms)-",
    "ARN": r"\barn:aws[a-z-]*:",
    "AWS region": r"\b(us|eu|ap|sa|ca|me|af|il|mx|cn)(-gov|-iso[a-z]*)?-"
    r"(north|south|east|west|central|northeast|northwest|southeast|southwest)-\d\b",
    "GCP region": r"\b(us|europe|asia|australia|northamerica|southamerica|me|africa)-[a-z]+\d\b",
    "Azure region": r"\b(eastus|westus|southcentralus|northcentralus|westcentralus|westeurope"
    r"|northeurope|centralindia|southindia|southeastasia|eastasia|uksouth|ukwest|japaneast|japanwest"
    r"|australiaeast|canadacentral|canadaeast|brazilsouth|germanywestcentral|swedencentral"
    r"|koreacentral|francecentral|uaenorth|norwayeast|switzerlandnorth|southafricanorth)\d?\b",
    "model id": r"\b(claude|gpt-|gemini-|llama|mistral|qwen|deepseek|anthropic\.|us\.anthropic\."
    r"|amazon\.(nova|titan)|cohere\.|meta\.llama)|\bo[134](-mini|-pro)?\b",
    "account id": r"\b\d{12}\b",
    "host": r"(amazonaws\.com(\.cn)?|aws\.amazon\.com|azure\.com|(azure|windows)\.net|googleapis\.com"
    r"|cloud\.google\.com|slack\.com|github\.com|anthropic\.com|openai\.com)\b",
}
_SQL_LITERAL = re.compile(
    r"'(slack|teams|github|gitlab|aws|azure|gcp|bedrock|anthropic|kms|s3)'", re.IGNORECASE
)


def _docstrings(tree: ast.AST) -> set[int]:
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            first = n.body[0] if n.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def _skipped_table_nodes(tree: ast.Module) -> set[int]:
    """In backends.table: vendor-named settings classes and helpers, and the TABLE itself, name vendors."""
    skipped: set[int] = set()
    for top in tree.body:
        named = isinstance(
            top, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ) and _TABLE_VENDOR_NAME.match(top.name)
        table = isinstance(top, ast.AnnAssign | ast.Assign) and "TABLE" in ast.unparse(top)[:12]
        if named or table:
            skipped |= {id(n) for n in ast.walk(top)}
    return skipped


def _fold(node: ast.AST) -> str | None:
    """The text a node builds when it is only constants: a str or bytes constant, `a + b` of such, or an
    f-string (the non-constant parts become `{}`). Anything else: None."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value
        if isinstance(node.value, bytes):
            return node.value.decode("latin-1")
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        # A non-constant side becomes `{}`, like an f-string, so `'arn:aws:s3:::' + bucket` is still scanned.
        left, right = _fold(node.left), _fold(node.right)
        return (left if left is not None else "{}") + (right if right is not None else "{}")
    if isinstance(node, ast.JoinedStr):
        # A constant `{"east"}` inside an f-string is folded, so f'us-{"east"}-1' reads as us-east-1.
        return "".join(
            (_fold(v.value) or "{}")
            if isinstance(v, ast.FormattedValue)
            and v.conversion == -1
            and v.format_spec is None
            and isinstance(v.value, ast.Constant)
            else (v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else "{}")
            for v in node.values
        )
    return None


def literal_problems(
    src: Path, vendor_modules: set[str], literal_ok: dict[tuple[str, str], str]
) -> list[str]:
    """Every str or bytes constant, every constant `+` join and every f-string is checked against PATTERNS
    (so `b'x-amz-date'`, `'us-east' + '-1'` and `f'slack:{x}'` are caught as well as plain strings)."""
    out: list[str] = []
    used: set[tuple[str, str]] = set()
    for path in sorted(src.rglob("*.py")):
        mod = module_name(src, path)
        if mod in vendor_modules:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        skip = _docstrings(tree) | (_skipped_table_nodes(tree) if mod == _TABLE_MODULE else set())
        for n in ast.walk(tree):
            if id(n) in skip or not isinstance(n, ast.Constant | ast.BinOp | ast.JoinedStr):
                continue
            text = _fold(n)
            if text is None:
                continue
            for label, pattern in PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    if (mod, text) in literal_ok:
                        used.add((mod, text))
                    else:
                        out.append(f"{mod}:{n.lineno}: {label} in {text[:50]!r}")
    out += [
        f"LITERAL_OK {k[0]} {k[1][:30]!r} is gone: delete the entry"
        for k in literal_ok
        if k not in used
    ]
    return out


MODULE_NAME_KEY = (
    "module:"  # IDENTIFIER_OK key prefix for a module's own name (never a valid identifier)
)
_CAMEL = re.compile(r"[A-Z]+(?![a-z])\d*|[A-Z]?[a-z]+\d*|\d+")
_WORD_SET = frozenset(VENDOR_WORDS)
_DIGITS = "0123456789"


def name_parts(name: str) -> set[str]:
    """Snake parts (split on `_`), the camel parts of each snake part, each pair of neighbouring camel parts
    joined (so GitHub -> github, GitLab -> gitlab, OpenAI/OpenAi -> openai) and each pair of neighbouring snake
    parts joined (so pager_duty -> pagerduty, open_ai -> openai). All lower case."""
    snakes = [s for s in name.split("_") if s]
    out = [a.lower() + b.lower() for a, b in itertools.pairwise(snakes)]
    for snake in snakes:
        out.append(snake.lower())
        camel = [c.lower() for c in _CAMEL.findall(snake)]
        out += camel
        out += [a + b for a, b in itertools.pairwise(camel)]
    return set(out)


def vendor_words_in(name: str) -> list[str]:
    """The vendor words a name holds, sorted: a part that EQUALS a word, or equals one once its trailing digits
    are removed (`slack2_url`, `aws1`). A part that is itself a listed word (`s3`) is never stripped."""
    found = set()
    for part in name_parts(name):
        if part in _WORD_SET:
            found.add(part)
        elif part.rstrip(_DIGITS) in _WORD_SET:
            found.add(part.rstrip(_DIGITS))
    return sorted(found)


# Node types whose bound name is their `name` field.
_NAMED = (
    ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.ExceptHandler
    | ast.MatchAs
    | ast.MatchStar
    | ast.TypeVar
    | ast.ParamSpec
    | ast.TypeVarTuple
)


def _path_segments(dotted: str) -> list[str]:
    """The segments of an imported module path, without the package's own name in first place."""
    segments = [seg for seg in dotted.split(".") if seg]
    return segments[1:] if segments[:1] == [PKG] else segments


def _bound_names(tree: ast.AST, skip: set[int]) -> list[tuple[int, str]]:
    """(line, name) of every name a module binds or passes by keyword: functions, classes, parameters, assignment
    and loop targets, attributes that are assigned, imported names, `except ... as`, `match` captures, type
    parameters, and keyword names at call sites. Also every segment of the module path of an import (the package's
    own first segment left out), so `from <package>.approvals.slack import X` is seen although it binds only `X`."""
    out: list[tuple[int, str | None]] = []
    for n in ast.walk(tree):
        if id(n) in skip:
            continue
        if isinstance(n, _NAMED):
            out.append((n.lineno, n.name))
        elif isinstance(n, ast.arg | ast.keyword):
            out.append((n.lineno, n.arg))
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.append((n.lineno, n.id))
        elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
            out.append((n.lineno, n.attr))
        elif isinstance(n, ast.Import):
            for a in n.names:
                out += [(a.lineno, a.asname), *((a.lineno, seg) for seg in _path_segments(a.name))]
        elif isinstance(n, ast.ImportFrom):
            out += [(n.lineno, seg) for seg in _path_segments(n.module or "")]
            out += [(a.lineno, a.asname or a.name) for a in n.names]
        elif isinstance(n, ast.MatchMapping):
            out.append((n.lineno, n.rest))
    return [(line, name) for line, name in out if name]


def identifier_problems(
    src: Path,
    vendor_modules: set[str],
    identifier_ok: dict[tuple[str, str], str],
    table_names: frozenset[str],
) -> list[str]:
    """A vendor word in a name that shared code gives to something: one line per (name occurrence, word). The
    module's own name comes first (each segment after the package, reported at line 1), then the names it binds,
    sorted by (line, name, word). In `backends.table` a top-level class or function listed in `table_names` is
    skipped with everything inside it."""
    out: list[str] = []
    used: set[tuple[str, str]] = set()
    for path in sorted(src.rglob("*.py")):
        mod = module_name(src, path)
        if mod in vendor_modules:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        skip: set[int] = set()
        if mod == _TABLE_MODULE:
            for top in tree.body:
                named = isinstance(top, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
                if named and top.name in table_names:
                    skip |= {id(n) for n in ast.walk(top)}
        own = {(1, seg, w) for seg in mod.split(".")[1:] for w in vendor_words_in(seg)}
        bound = {
            (ln, name, w) for ln, name in _bound_names(tree, skip) for w in vendor_words_in(name)
        }
        # A module's own name has its own key, so allowing it never allows a variable of the same name.
        keyed = [(f"{MODULE_NAME_KEY}{seg}", (1, seg, w)) for _, seg, w in sorted(own)]
        keyed += [(name, (ln, name, w)) for ln, name, w in sorted(bound)]
        lines: dict[str, None] = {}
        for key, (line, name, word) in keyed:
            if (mod, key) in identifier_ok:
                used.add((mod, key))
            else:
                lines[f"{mod}:{line}: vendor word {word!r} in the name {name!r}"] = None
        out += lines
    out += [
        f"IDENTIFIER_OK {k[0]} {k[1]!r} is gone: delete the entry"
        for k in identifier_ok
        if k not in used
    ]
    return out


def sql_problems(folder: Path) -> list[str]:
    out = []
    for path in sorted(folder.glob("*.sql")):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        text = re.sub(r"--[^\n]*", "", text)
        for m in _SQL_LITERAL.finditer(text):
            out.append(f"{path.name}: vendor literal {m.group(0)}")
        for label, pattern in PATTERNS.items():
            if label != "bare vendor name" and re.search(pattern, text, re.IGNORECASE):
                out.append(f"{path.name}: {label}")
    return out


def test_core_logic_names_no_vendor():
    assert literal_problems(SRC, VENDOR_MODULES, LITERAL_OK) == []


def test_core_names_no_vendor_in_identifiers():
    assert identifier_problems(SRC, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES) == []


def _top_level_table_names() -> list[str]:
    tree = ast.parse((SRC / PKG / "backends" / "table.py").read_text(encoding="utf-8"))
    return [
        top.name
        for top in tree.body
        if isinstance(top, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def test_the_table_skip_is_the_pinned_set():
    """The prefix pattern that decides which parts of the kind table the string scan skips matches exactly the
    pinned names, so the skip cannot grow without an edit to TABLE_VENDOR_NAMES."""
    matched = {name for name in _top_level_table_names() if _TABLE_VENDOR_NAME.match(name)}
    assert matched == TABLE_VENDOR_NAMES


_WHOLE_WORD = re.compile(rf"(?<![A-Za-z0-9])({_W})(?![A-Za-z0-9])", re.IGNORECASE)
_RECEIVER = Path(PKG) / "approvals" / "receiver.py"


def test_the_receiver_file_names_no_vendor_anywhere():
    """The approval receiver serves every channel kind, so it is held to more than the scans: no vendor word in
    its code, comments or docstrings."""
    text = (SRC / _RECEIVER).read_text(encoding="utf-8")
    assert [m.group(0) for m in _WHOLE_WORD.finditer(text)] == []


def test_the_word_list_covers_the_list_of_the_http_metadata_test():
    """Two tests keep a vendor word list; the other one must stay a subset of this one."""
    from tests.test_http_metadata import VENDOR_WORDS as other

    listed = re.search(r"\)\(([a-z0-9|]+)\)\(", other.pattern)  # the one group of alternatives
    assert listed is not None, other.pattern
    words = set(listed.group(1).split("|"))
    assert len(words) >= 15
    assert words <= set(VENDOR_WORDS), sorted(words - set(VENDOR_WORDS))


def test_no_vendor_literal_in_migrations():
    folder = SRC / PKG / "store" / "migrations"
    assert list(folder.glob("*.sql")), "no migrations found: the scan would check nothing"
    assert sql_problems(folder) == []


def test_every_named_vendor_module_exists():
    missing = [
        m for m in VENDOR_MODULES if not (SRC / Path(*m.split(".")).with_suffix(".py")).is_file()
    ]
    assert missing == []


def _lit(tmp_path: Path, rel: str, text: str, ok=None) -> list[str]:
    root = _plant(tmp_path, rel, text)
    return literal_problems(root, VENDOR_MODULES, ok or {})


def test_plant_region_constant_is_caught(tmp_path):
    assert "AWS region" in _lit(tmp_path, "runtime/x.py", "R = 'us-east-1'\n")[0]


def test_plant_arn_is_caught(tmp_path):
    assert "ARN" in _lit(tmp_path, "runtime/x.py", "A = 'arn:aws:s3:::b'\n")[0]


def test_plant_slack_id_fstring_is_caught(tmp_path):
    assert (
        "bare vendor name"
        in _lit(tmp_path, "approvals/x.py", "def f(x):\n    return f'slack:{x}'\n")[0]
    )


def test_plant_amz_header_is_caught(tmp_path):
    assert "vendor header" in _lit(tmp_path, "runtime/x.py", "H = 'x-amz-date'\n")[0]


def test_plant_model_id_host_and_account_are_caught(tmp_path):
    text = (
        "M = 'claude-sonnet-4'\nH = 'https://x.googleapis.com'\nN = '123456789012'\nG = 'eastus2'\n"
    )
    assert len(_lit(tmp_path, "runtime/x.py", text)) == 4


def test_plant_bytes_constant_is_caught(tmp_path):
    assert "vendor header" in _lit(tmp_path, "runtime/x.py", "H = b'x-amz-date'\n")[0]


def test_plant_constant_concatenation_is_caught(tmp_path):
    text = "R = 'us-east' + '-1'\nA = 'arn:' + 'aws:s3:::b'\n"
    found = _lit(tmp_path, "runtime/x.py", text)
    assert any("AWS region" in f for f in found) and any("ARN" in f for f in found)


def test_plant_split_fstring_is_caught(tmp_path):
    text = "def f(n):\n    return f'arn:aws:s3:::{n}'\n"
    assert any("ARN" in f for f in _lit(tmp_path, "runtime/x.py", text))


def test_plant_bytes_plus_bytes_is_caught(tmp_path):
    found = _lit(tmp_path, "runtime/x.py", "H = b'x-amz-' + b'date'\n")
    assert any("vendor header" in f for f in found)


def test_plant_constant_inside_fstring_is_folded_and_caught(tmp_path):
    text = "R = f'us-{" + chr(34) + "east" + chr(34) + "}-1'" + chr(10)
    assert "AWS region" in _lit(tmp_path, "runtime/x.py", text)[0]
    assert (
        _lit(tmp_path, "runtime/x.py", "def f(x):" + chr(10) + "    return f'a-{x}-b'" + chr(10))
        == []
    )


def test_non_constant_concatenation_is_not_a_false_alarm(tmp_path):
    assert _lit(tmp_path, "runtime/x.py", "def f(a):\n    return a + '-x'\n") == []


def test_a_docstring_and_a_vendor_module_are_not_flagged(tmp_path):
    _plant(tmp_path, "llm/gemini.py", "H = 'x-goog-api-key'\n")
    assert _lit(tmp_path, "runtime/x.py", '"""Talks to slack.com."""\nX = 1\n') == []


def test_plant_stale_literal_allowance_is_caught(tmp_path):
    problems = _lit(tmp_path, "runtime/x.py", "X = 1\n", {(f"{PKG}.runtime.x", "aws"): "why"})
    assert len(problems) == 1 and "is gone" in problems[0]


def test_a_listed_literal_is_allowed(tmp_path):
    assert _lit(tmp_path, "runtime/x.py", "X = 'aws'\n", {(f"{PKG}.runtime.x", "aws"): "why"}) == []


def test_plant_sql_check_with_a_vendor_literal_is_caught(tmp_path):
    (tmp_path / "0009.sql").write_text(
        "ALTER TABLE t ADD CHECK (lower(channel) IN ('slack', 'csv'));\n", encoding="utf-8"
    )
    assert sql_problems(tmp_path) == ["0009.sql: vendor literal 'slack'"]


def test_a_vendor_name_in_a_sql_comment_is_not_flagged(tmp_path):
    (tmp_path / "0009.sql").write_text(
        "-- 'slack' is one channel\n/* 'aws' */\nSELECT 1;\n", encoding="utf-8"
    )
    assert sql_problems(tmp_path) == []


# ---- rule c, the string pattern for paths and keys (Q8a-2)

_PATH_OR_KEY = "vendor word in a path or key"
_BARE = "bare vendor name"


def _labels_by_line(problems: list[str]) -> dict[int, list[str]]:
    """line number -> the labels of the problem lines reported there."""
    out: dict[int, list[str]] = {}
    for problem in problems:
        m = re.match(r"[\w.]+:(\d+): (.+?) in '", problem)
        assert m, problem
        out.setdefault(int(m.group(1)), []).append(m.group(2))
    return out


@pytest.mark.parametrize(
    "text",
    [
        "/slack/actions",
        "aws_region",
        "x.azure.example",
        "s3-bucket",
        "q?team=slack&x=1",
        "ops@pagerduty",
        "#github",
    ],
)
def test_plant_vendor_word_in_a_path_or_key_is_caught(tmp_path, text):
    found = _lit(tmp_path, "runtime/x.py", f"X = {text!r}\n")
    assert found == [f"{PKG}.runtime.x:1: {_PATH_OR_KEY} in {text!r}"]


def test_a_bare_vendor_word_gives_one_line_and_a_word_that_only_contains_one_gives_none(tmp_path):
    assert _lit(tmp_path, "runtime/x.py", "X = 'aws'\n") == [f"{PKG}.runtime.x:1: {_BARE} in 'aws'"]
    assert _lit(tmp_path, "runtime/x.py", "X = 'laws_of_teamsters'\n") == []


UNSEEN_STRINGS = [
    "/slackActions",  # glued in camel case
    "post to Slack now",  # free prose
    "x/slack y",  # a boundary before the word, none after it
    "slack|teams",  # `|` is not a separator
    "/pager-duty/hook",  # a two-part name written with a separator
    "/datadog/api",  # a word that is not in the list
    "datadog_key",
]


@pytest.mark.parametrize("text", UNSEEN_STRINGS)
def test_the_stated_limits_of_the_string_pattern(tmp_path, text):
    """Pinned so a later change is deliberate: what the string pattern does not see."""
    assert _lit(tmp_path, "runtime/x.py", f"X = {text!r}\n") == []


@pytest.mark.parametrize("text", ["slack,teams", "(aws)", "aws+kms", "/slack;v=1", "f(gcp)"])
def test_plant_vendor_word_beside_a_list_separator_is_caught(tmp_path, text):
    found = _lit(tmp_path, "runtime/x.py", f"X = {text!r}\n")
    assert found == [f"{PKG}.runtime.x:1: {_PATH_OR_KEY} in {text!r}"]


def test_an_fstring_or_a_join_is_reported_for_the_joined_text_and_for_each_part_that_hits(tmp_path):
    """Pinned: the scan walks a joined text and its constant parts as separate nodes."""
    assert _lit(tmp_path, "runtime/x.py", "def f(y):\n    return f'/slack/{y}'\n") == [
        f"{PKG}.runtime.x:2: {_PATH_OR_KEY} in '/slack/{{}}'",
        f"{PKG}.runtime.x:2: {_PATH_OR_KEY} in '/slack/'",
    ]
    # `{}` stands for the part that is not a constant, and is no boundary: only the constant part hits here
    assert _lit(tmp_path, "runtime/x.py", "def f(tail):\n    return '/slack' + tail\n") == [
        f"{PKG}.runtime.x:2: {_PATH_OR_KEY} in '/slack'"
    ]


def test_a_file_that_is_not_python_is_not_scanned(tmp_path):
    """Pinned: a vendor word in a YAML or Markdown file under the package is not seen by either scan."""
    _plant(tmp_path, "runtime/x.py", "X = 1\n")
    _plant(tmp_path, "runtime/slack_hook.yaml", "request_url: /slack/actions\naws_region: x\n")
    _plant(tmp_path, "runtime/notes.md", "post to /slack/actions\n")
    assert literal_problems(tmp_path, VENDOR_MODULES, {}) == []
    assert identifier_problems(tmp_path, VENDOR_MODULES, {}, frozenset()) == []


def test_plant_a_vendor_literal_inside_the_gcs_settings_class_is_caught(tmp_path):
    """The class is allowed by name only: a host, a region or a path put into it is reported like anywhere else.
    The vendor-named neighbours that the prefix pattern matches are skipped whole."""
    source = (
        "class GcsRetentionLockSettings:\n"
        "    kind = 'gcs_retention_lock'\n"
        "    endpoint = 'https://storage.googleapis.com'\n"
        "    region = 'us-east-1'\n"
        "class S3ObjectLockSettings:\n"
        "    endpoint = 'https://s3.amazonaws.com'\n"
    )
    ok = {(_TABLE_MODULE, "gcs_retention_lock"): "why"}
    assert _lit(tmp_path, "backends/table.py", source, ok) == [
        f"{_TABLE_MODULE}:3: host in 'https://storage.googleapis.com'",
        f"{_TABLE_MODULE}:4: AWS region in 'us-east-1'",
    ]
    assert not _TABLE_VENDOR_NAME.match("GcsRetentionLockSettings")
    names_ok = {(_TABLE_MODULE, "GcsRetentionLockSettings"): "why"}
    source += "    gcs_bucket = 1\nclass GcsRetentionLockSettings2:\n    gcs_bucket = 2\n"
    assert _ident(
        tmp_path, "backends/table.py", source, names_ok, frozenset({"S3ObjectLockSettings"})
    ) == [
        f"{_TABLE_MODULE}:8: vendor word 'gcs' in the name 'GcsRetentionLockSettings2'",
        f"{_TABLE_MODULE}:9: vendor word 'gcs' in the name 'gcs_bucket'",
    ]


def test_property_every_word_beside_every_separator_gives_exactly_one_path_or_key_line(tmp_path):
    cases = [
        text
        for word in VENDOR_WORDS
        for sep in _SEP
        for text in (f"{word}{sep}q", f"q{sep}{word}{sep}q", f"q{sep}{word}")
    ]
    assert len(cases) == len(VENDOR_WORDS) * len(_SEP) * 3
    source = "".join(f"X = {text!r}\n" for text in cases)
    labels = _labels_by_line(_lit(tmp_path, "runtime/x.py", source))
    for line, text in enumerate(cases, 1):
        # another entry (a model id, a vendor header) may report the same string too; these two are counted
        got = labels.get(line, [])
        assert (got.count(_PATH_OR_KEY), got.count(_BARE)) == (1, 0), text
    bare = "".join(f"X = {word!r}\n" for word in VENDOR_WORDS)
    labels = _labels_by_line(_lit(tmp_path, "runtime/x.py", bare))
    for line, word in enumerate(VENDOR_WORDS, 1):
        assert labels.get(line) == [_BARE], word


# ---- rule c, names (Q8a-2)


def _ident(tmp_path: Path, rel: str, text: str, ok=None, table_names=frozenset()) -> list[str]:
    root = _plant(tmp_path, rel, text)
    return identifier_problems(root, VENDOR_MODULES, ok or {}, table_names)


def _hit(mod: str, line: int, word: str, name: str) -> str:
    return f"{PKG}.{mod}:{line}: vendor word {word!r} in the name {name!r}"


@pytest.mark.parametrize(
    ("source", "line", "word", "name"),
    [
        ("def post_to_slack():\n    pass\n", 1, "slack", "post_to_slack"),
        ("async def aws_call():\n    pass\n", 1, "aws", "aws_call"),
        ("class GitHubClient:\n    pass\n", 1, "github", "GitHubClient"),
        ("def f(azure_key):\n    pass\n", 1, "azure", "azure_key"),
        ("def f(*, gcp_zone=1):\n    pass\n", 1, "gcp", "gcp_zone"),
        ("f = lambda bedrock_id: 1\n", 1, "bedrock", "bedrock_id"),
        (
            "class C:\n    def __init__(self):\n        self.slack_url = 1\n",
            3,
            "slack",
            "slack_url",
        ),
        ("class C:\n    kms_key: str\n", 2, "kms", "kms_key"),
        ("X = 1\nOPENAI_BASE = X\n", 2, "openai", "OPENAI_BASE"),
        ("for gemini_part in ():\n    pass\n", 1, "gemini", "gemini_part"),
        ("with open(__file__) as s3_file:\n    pass\n", 1, "s3", "s3_file"),
        ("X = [1 for vertex_i in ()]\n", 1, "vertex", "vertex_i"),
        ("if (teams_n := 1):\n    pass\n", 1, "teams", "teams_n"),
        ("import json as openai\n", 1, "openai", "openai"),
        ("import gitlab.v4.objects\n", 1, "gitlab", "gitlab"),
        ("from x import (\n    a,\n    slack_helper,\n)\n", 3, "slack", "slack_helper"),
        ("from x import a as anthropic_a\n", 1, "anthropic", "anthropic_a"),
        ("try:\n    pass\nexcept Exception as aws_error:\n    pass\n", 3, "aws", "aws_error"),
        ("match 1:\n    case azure_value:\n        pass\n", 2, "azure", "azure_value"),
        ("match [1]:\n    case [*foundry_rest]:\n        pass\n", 2, "foundry", "foundry_rest"),
        ("match {}:\n    case {**gcs_rest}:\n        pass\n", 2, "gcs", "gcs_rest"),
        ("def f[SlackT](x):\n    pass\n", 1, "slack", "SlackT"),
        ("class C[*AwsTs]:\n    pass\n", 1, "aws", "AwsTs"),
        ("def f[**KmsP](x):\n    pass\n", 1, "kms", "KmsP"),
        ("type OracleRow = int\n", 1, "oracle", "OracleRow"),
        ("def f(**kw):\n    pass\n\n\nf(google_project=1)\n", 5, "google", "google_project"),
        ("slack2_url = 1\n", 1, "slack", "slack2_url"),
        ("aws1 = 1\n", 1, "aws", "aws1"),
        ("my_s3 = 1\n", 1, "s3", "my_s3"),
    ],
)
def test_plant_vendor_word_in_a_bound_name_is_caught(tmp_path, source, line, word, name):
    assert _ident(tmp_path, "runtime/x.py", source) == [_hit("runtime.x", line, word, name)]


def test_plant_vendor_word_in_a_module_or_package_name_is_caught(tmp_path):
    assert _ident(tmp_path, "approvals/slack_helpers.py", "X = 1\n") == [
        _hit("approvals.slack_helpers", 1, "slack", "slack_helpers")
    ]
    assert _ident(tmp_path / "pkg", "aws/x.py", "X = 1\n") == [_hit("aws.x", 1, "aws", "aws")]
    # a vendor module is not scanned, by its name or by its content
    assert _ident(tmp_path / "vendor", "approvals/slack_channel.py", "slack_x = 1\n") == []


def test_a_word_that_only_contains_a_vendor_word_is_not_a_name_hit(tmp_path):
    assert _ident(tmp_path, "runtime/x.py", "awsome = laws = teamster = xs3y = kmsx = 1\n") == []
    # a name that is only read is scanned where it is bound, not here
    assert (
        _ident(tmp_path, "runtime/x.py", "def f(a):\n    return a.slack_url + len(a.aws)\n") == []
    )


def test_the_stated_limits_of_the_name_scan(tmp_path):
    """Pinned so a later change is deliberate: a word glued to capitals and a word that is not listed are not
    seen; two neighbouring parts that happen to spell a listed word are reported."""
    assert _ident(tmp_path, "runtime/x.py", "AWSclient = datadog_key = DatadogClient = 1\n") == []
    assert _ident(tmp_path, "runtime/x.py", "TeamS = 1\nteam_s = 2\n") == [
        _hit("runtime.x", 1, "teams", "TeamS"),
        _hit("runtime.x", 2, "teams", "team_s"),
    ]


def test_a_lookalike_letter_is_a_stated_limit_and_a_full_width_one_is_folded_by_python(tmp_path):
    """Pinned: a Cyrillic letter in place of a Latin one hides a word from the name scan (no table of look-alike
    letters is kept). A full-width spelling does not: Python normalises identifiers (NFKC) when it parses."""
    assert _ident(tmp_path, "runtime/x.py", "sl\u0430ck_url = 1\n") == []
    assert _ident(tmp_path, "runtime/x.py", "\uff53\uff4c\uff41\uff43\uff4b_url = 1\n") == [
        _hit("runtime.x", 1, "slack", "slack_url")
    ]


def test_a_vendor_sdk_import_under_a_glued_alias_is_refused_by_the_import_rule(tmp_path):
    """`import boto3 as awsclient`: the alias hides the word from the name scan (glued to other letters, a stated
    limit) and `boto3` is not a listed word, so it is rule a that fails it in shared code."""
    source = "import boto3 as awsclient\n"
    assert _ident(tmp_path, "runtime/x.py", source) == []
    assert _imports(tmp_path) == [
        f"{PKG}.runtime.x: imports boto3 (vendor SDK) outside its allowed modules"
    ]


@pytest.mark.parametrize(
    ("name", "word"),
    [
        ("pager_duty_key", "pagerduty"),
        ("cloud_watch_ns", "cloudwatch"),
        ("open_ai_key", "openai"),
        ("git_hub_token", "github"),
        ("digital_ocean_x", "digitalocean"),
        ("GIT_LAB_URL", "gitlab"),
        ("my_Pager_Duty", "pagerduty"),
    ],
)
def test_plant_a_two_part_vendor_name_written_in_snake_case_is_caught(tmp_path, name, word):
    assert _ident(tmp_path, "runtime/x.py", f"{name} = 1\n") == [_hit("runtime.x", 1, word, name)]


@pytest.mark.parametrize(
    ("source", "name"),
    [
        (f"from {PKG}.approvals.slack import HEADER_PREFIX\n", "slack"),
        (f"import {PKG}.approvals.slack_channel as chat\n", "slack_channel"),
        (f"import {PKG}.approvals.slack\n", "slack"),
        (f"def f():\n    from {PKG}.llm import common, gemini\n", "gemini"),
        ("from vendorkit.aws_tools.core import client\n", "aws_tools"),
    ],
)
def test_plant_vendor_word_in_the_module_path_of_an_import_is_caught(tmp_path, source, name):
    """A neutral module that imports a vendor module is tied to it even when the name it binds is neutral."""
    line = source.count("\n")
    word = vendor_words_in(name)[0]
    assert _ident(tmp_path, "runtime/x.py", source) == [_hit("runtime.x", line, word, name)]


def test_the_package_name_itself_and_a_neutral_import_path_are_not_hits(tmp_path):
    source = f"import {PKG}.approvals.channel\nfrom {PKG}.store import protocol\nimport os.path\n"
    assert _ident(tmp_path, "runtime/x.py", source) == []


def test_a_module_name_allowance_does_not_allow_a_variable_of_that_name(tmp_path):
    mod = f"{PKG}.runtime.slack_x"
    ok = {(mod, f"{MODULE_NAME_KEY}slack_x"): "why"}
    assert _ident(tmp_path, "runtime/slack_x.py", "X = 1\n", ok) == []
    assert _ident(tmp_path, "runtime/slack_x.py", "slack_x = 1\n", ok) == [
        _hit("runtime.slack_x", 1, "slack", "slack_x")
    ]
    # and a name allowance does not allow the module's own name
    assert _ident(tmp_path, "runtime/slack_x.py", "slack_x = 1\n", {(mod, "slack_x"): "why"}) == [
        _hit("runtime.slack_x", 1, "slack", "slack_x")
    ]
    # a stale module-name entry is reported with its key
    assert _ident(
        tmp_path / "o", "runtime/y.py", "X = 1\n", {(f"{PKG}.runtime.y", "module:y"): "w"}
    ) == [f"IDENTIFIER_OK {PKG}.runtime.y 'module:y' is gone: delete the entry"]


def test_name_hits_are_one_per_occurrence_and_word_in_a_fixed_order(tmp_path):
    source = (
        "import os\n"
        "class AwsKmsThing:\n"  # two words in one name: two lines, words sorted
        "    pass\n"
        "slack_b = slack_a = 1\n"  # two names on one line: sorted by name
        "slack_a, slack_a = 1, 2\n"  # the same name twice on one line: one line
        "slack_a = 3\n"  # the same name on another line: its own line
    )
    assert _ident(tmp_path, "runtime/gcp_x.py", source) == [
        _hit("runtime.gcp_x", 1, "gcp", "gcp_x"),  # the module's own name first
        _hit("runtime.gcp_x", 2, "aws", "AwsKmsThing"),
        _hit("runtime.gcp_x", 2, "kms", "AwsKmsThing"),
        _hit("runtime.gcp_x", 4, "slack", "slack_a"),
        _hit("runtime.gcp_x", 4, "slack", "slack_b"),
        _hit("runtime.gcp_x", 5, "slack", "slack_a"),
        _hit("runtime.gcp_x", 6, "slack", "slack_a"),
    ]


def test_a_listed_name_is_allowed_and_a_stale_entry_is_caught(tmp_path):
    ok = {(f"{PKG}.runtime.x", "slack_a"): "why"}
    assert _ident(tmp_path, "runtime/x.py", "slack_a = 1\nslack_b = 2\n", ok) == [
        _hit("runtime.x", 2, "slack", "slack_b")
    ]
    assert _ident(tmp_path, "runtime/x.py", "X = 1\n", ok) == [
        f"IDENTIFIER_OK {PKG}.runtime.x 'slack_a' is gone: delete the entry"
    ]
    # the entry is for its module only
    assert len(_ident(tmp_path, "runtime/y.py", "slack_a = 1\n", ok)) == 2


def test_the_table_skip_covers_listed_top_level_names_only(tmp_path):
    source = (
        "class SlackSettings:\n"
        "    slack_token: str = ''\n"
        "def _aws():\n"
        "    aws_x = 1\n"
        "class Other:\n"
        "    class SlackSettings:\n"  # nested: not a top-level name of the table
        "        pass\n"
        "    gcp_y = 1\n"
    )
    names = frozenset({"SlackSettings", "_aws"})
    assert _ident(tmp_path, "backends/table.py", source, table_names=names) == [
        _hit("backends.table", 6, "slack", "SlackSettings"),
        _hit("backends.table", 8, "gcp", "gcp_y"),
    ]
    # the same names in any other module are not skipped
    assert len(_ident(tmp_path / "other", "runtime/x.py", source, table_names=names)) == 6


def test_property_every_word_is_seen_in_snake_and_camel_names_and_not_inside_a_longer_word(
    tmp_path,
):
    forms = [
        (lambda w: f"x_{w}_y", True),
        (lambda w: f"{w.upper()}_X", True),
        (lambda w: f"{w.capitalize()}Client", True),
        (lambda w: f"my{w.capitalize()}", True),
        (lambda w: f"x{w}y", False),
    ]
    names = [(form(word), word, hit) for word in VENDOR_WORDS for form, hit in forms]
    source = "".join(f"{name} = 1\n" for name, _, _ in names)
    found = _ident(tmp_path, "runtime/x.py", source)
    expected = [
        _hit("runtime.x", line, word, name)
        for line, (name, word, hit) in enumerate(names, 1)
        if hit
    ]
    assert found == expected


# ---- rule c, each new allow entry is needed and exact; a plant in the real receiver (Q8a-2)

_OPENAI_ALIAS_REGEX = r"^(?:gpt-[\w.-]+|o\d[\w.-]*|chatgpt-[\w.-]+)$"
# Every LITERAL_OK entry -> the labels of the problem lines it covers (one per place the string stands).
_LITERAL_OK_LABELS = {
    (f"{PKG}.approvals.gate", "aws"): [_BARE, _BARE],
    (f"{PKG}.approvals.gate", "s3"): [_BARE],
    (f"{PKG}.config", "slack"): [_BARE],
    (f"{PKG}.llm.openai_compat", _OPENAI_ALIAS_REGEX): ["model id"],
    (f"{PKG}.guard.producers", "guard/bedrock_guardrail.py"): [_PATH_OR_KEY, _PATH_OR_KEY],
    (f"{PKG}.llm.openai_compat", "openai_compat"): [_PATH_OR_KEY],
    (f"{PKG}.approvals.gate", "gcloud"): [_BARE],
    (f"{PKG}.tools", "metadata.google.internal"): [_PATH_OR_KEY],
    (f"{PKG}.tools", ".metadata.google.internal"): [_PATH_OR_KEY],
    (f"{PKG}.backends.table", "gcs_retention_lock"): [_PATH_OR_KEY],
}
_IDENTIFIER_OK_WORDS = {
    (f"{PKG}.approvals.gate", "_AWS_READ_PREFIXES"): "aws",
    (f"{PKG}.backends.table", "OpenAICompatSettings"): "openai",
    (f"{PKG}.backends.table", "GcsRetentionLockSettings"): "gcs",
    (f"{PKG}.llm.openai_compat", "OpenAICompatLLM"): "openai",
    (f"{PKG}.llm.openai_compat", "module:openai_compat"): "openai",
    (f"{PKG}.store.postgres", "auth_aws"): "aws",
}


def _without_lines(problems: list[str]) -> list[str]:
    return [re.sub(r":\d+: ", ": ", problem) for problem in problems]


def test_every_allowance_is_checked_by_a_removal_test():
    assert set(_LITERAL_OK_LABELS) == set(LITERAL_OK)
    assert set(_IDENTIFIER_OK_WORDS) == set(IDENTIFIER_OK)


@pytest.mark.parametrize(
    "key", sorted(_LITERAL_OK_LABELS), ids=lambda key: f"{key[0]}:{key[1][:30]}"
)
def test_each_literal_allowance_covers_exactly_its_own_hits(key):
    rest = {k: v for k, v in LITERAL_OK.items() if k != key}
    mod, text = key
    assert _without_lines(literal_problems(SRC, VENDOR_MODULES, rest)) == [
        f"{mod}: {label} in {text[:50]!r}" for label in _LITERAL_OK_LABELS[key]
    ]


@pytest.mark.parametrize("key", sorted(_IDENTIFIER_OK_WORDS))
def test_each_name_allowance_covers_exactly_its_own_hit(key):
    rest = {k: v for k, v in IDENTIFIER_OK.items() if k != key}
    mod, name = key[0], key[1].removeprefix(MODULE_NAME_KEY)
    found = identifier_problems(SRC, VENDOR_MODULES, rest, TABLE_VENDOR_NAMES)
    assert _without_lines(found) == [
        f"{mod}: vendor word {_IDENTIFIER_OK_WORDS[key]!r} in the name {name!r}"
    ]


def test_removing_one_name_from_the_pinned_table_set_reports_that_name():
    for name in sorted(TABLE_VENDOR_NAMES):
        found = identifier_problems(SRC, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES - {name})
        assert any(f"in the name {name!r}" in line for line in found), name


def test_a_vendor_path_or_name_planted_in_the_real_receiver_is_caught(tmp_path):
    """A copy of the real tree with one vendor path and one vendor name appended to the receiver: each scan
    reports its line. The real tree is never written."""
    shutil.copytree(SRC / PKG, tmp_path / PKG, ignore=shutil.ignore_patterns("__pycache__"))
    assert literal_problems(tmp_path, VENDOR_MODULES, LITERAL_OK) == []
    assert identifier_problems(tmp_path, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES) == []
    planted = tmp_path / _RECEIVER
    before = planted.read_text(encoding="utf-8")
    assert _WHOLE_WORD.search(before) is None
    lines = before.count("\n")
    planted.write_text(
        before + 'PATH = "/slack/actions"\n\n\ndef handle_slack_action(): ...\n', encoding="utf-8"
    )
    mod = f"{PKG}.approvals.receiver"
    assert literal_problems(tmp_path, VENDOR_MODULES, LITERAL_OK) == [
        f"{mod}:{lines + 1}: {_PATH_OR_KEY} in '/slack/actions'"
    ]
    assert identifier_problems(tmp_path, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES) == [
        f"{mod}:{lines + 4}: vendor word 'slack' in the name 'handle_slack_action'"
    ]
    assert {m.group(0) for m in _WHOLE_WORD.finditer(planted.read_text(encoding="utf-8"))} == {
        "slack"
    }
    assert _WHOLE_WORD.search((SRC / _RECEIVER).read_text(encoding="utf-8")) is None


# ------------------------------------------------------------------- the test environment and anchors


def test_the_test_environment_holds_no_cloud_credential_variables():
    import os

    from tests.conftest import _ISOLATED, _ISOLATED_PREFIXES

    assert {"AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_PROFILE"} <= set(_ISOLATED)
    assert {"AWS_ENDPOINT_URL", "AZURE_", "GOOGLE_APPLICATION_CREDENTIALS"} <= set(
        _ISOLATED_PREFIXES
    )
    leaked = [n for n in os.environ if n in _ISOLATED or n.startswith(_ISOLATED_PREFIXES)]
    assert leaked == []


def test_a_file_suffix_is_not_a_model_id_but_a_bedrock_llama_id_is(tmp_path):
    assert _lit(tmp_path, "runtime/x.py", "S = '.meta.json'\n") == []
    assert "model id" in _lit(tmp_path, "runtime/x.py", "M = 'meta.llama3-70b'\n")[0]


def test_plant_vendor_sdk_in_the_tools_module_is_caught(tmp_path):
    root = _plant(tmp_path, "tools.py", "import boto3" + chr(10))
    assert _imports(root) == [
        f"{PKG}.tools: imports boto3 (vendor SDK) outside its allowed modules"
    ]


def test_plant_kubernetes_client_library_is_caught(tmp_path):
    root = _plant(tmp_path, "sources/kubernetes.py", "from kubernetes import client" + chr(10))
    assert _imports(root) == [
        f"{PKG}.sources.kubernetes: imports kubernetes (vendor SDK) outside its allowed modules"
    ]


def test_k5_tools_and_sources_use_the_standard_library_and_pydantic_only():
    """The read path (tools, sources) holds no vendor SDK and no library: a source is a protocol, an adapter
    speaks its source's own protocol over the standard library."""
    allowed = set(sys.stdlib_module_names) | BASE_OK | {PKG}
    mods = [SRC / PKG / "tools.py", *sorted((SRC / PKG / "sources").rglob("*.py"))]
    assert len(mods) >= 3
    for path in mods:
        tops = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                tops |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                tops.add(node.module.split(".")[0])
        assert tops <= allowed, (path.name, sorted(tops - allowed))
