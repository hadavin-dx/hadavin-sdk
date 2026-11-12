"""Reads each backend kind's declared permission set and writes the page operators copy from.

A "kind" is one backend choice (for example `vault`). A kind module may hold one literal named `POLICY`: the
permissions ("grants") its code needs, one reason per grant, the requests that need no permission, and a short
never-list (permissions that would undo what the kind promises).

What this file does:
* `load(path)` reads the module's SOURCE text and evaluates only the `POLICY` literal with `ast.literal_eval`.
  Nothing is imported and nothing is run. A module with no `POLICY` gives None. A `POLICY` that is not a pure
  literal, or that breaks a data rule, is refused with `PolicyError`.
* `render_vault` and `render_kubernetes` turn a policy into text for the platform (Vault policy text; one
  Kubernetes Role and RoleBinding per namespace). A value put into a template must fully match its grammar,
  else the renderer refuses; it never escapes.
* `python tools/policy_page.py --write` writes `docs/declared-permissions.md`; `--check` fails, with one line
  per problem and exit code 1, when a data rule is broken or the committed page differs from what the data
  gives. `--check` runs `data_problems`: the rules of each literal, the rules across kinds, every source id
  resolves in the sources file, no module outside `KIND_MODULES` holds a `POLICY`, every note and reason has
  one class (`NOTE_CLASSES`, whose own shape is checked too), every claim has one mark by full-text equality
  with the head of the sources file, the builder-read mark rules, and the dated lists of unchecked names
  (`PENDING_NAMES`) and unchecked claims (`PENDING_CLAIMS`). The builder-read mark rules: the mark stands only
  on a claim of an entry that names a source only the builder has read; an entry that names such a source and
  has ANY claim needs one builder-read claim, so a new claim with no reader added to such an entry makes
  `--check` ask for a builder-read one; the mark must be on the claim the builder really read, and no code
  can check that. The dated-list rules: an entry that is missing, stale, overdue (past `review_by`), too far
  out (`review_by` more than `MAX_PENDING_DAYS` after `decided`) or decided in the future is a problem. From
  2026-12-12 the dated entries are overdue, so `--write` and `--check` both stop until the dates are renewed.

What it does not do: it does not prove that a permission name is right, and it never contacts a server. Some
checks need this package imported or a server running and so live only in the tests (tests/test_policy_guard.py
and tests/test_policy_engine.py), not in `--check`: the call shape (the requests written in a module equal the
declared ones), the import lists of the kind modules, the sending-function and paging-query rules, the rule that
only the declared modules use the Vault client, the Kubernetes equalities (never-list, verb and resource per
path), the placeholder check (every placeholder is a real setting of the kind), the engine tests, and the list
of kinds with no declared set yet (`PENDING_KINDS`, which stays in the tests). Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT  # where the kind modules and the sources file are read from
PAGE = "docs/declared-permissions.md"
SOURCES = "tests/fixtures/policy_sources_2026-11-11.txt"
# The Vault server tests (tests/test_policy_engine.py) run only where a real server is given: the CI service.
# None: no run of them is on record, and the page says so. Set to (date, where the run can be read) only
# after a CI run showed them as passed, not skipped.
ENGINE_RUN: tuple[str, str] | None = None
# The one server image those tests run against (.github/workflows/ci.yml; a test compares) and its licence
# as noted in src/hadavin_sdk/actions/secrets_vault.py.
ENGINE_IMAGE = "hashicorp/vault:2.2.0"
ENGINE_LICENCE = "Business Source License 1.1 (source-available, not open source)"
# Per Vault kind: the requests the server tests send with the runtime token and expect to be refused (403).
# tests/test_policy_engine.py fails when its request lists differ from these, so the page states what is sent.
REFUSALS: dict[str, tuple[str, ...]] = {
    "secrets/vault": (
        "read two levels below the prefix",
        "read outside the prefix",
        "write under the prefix",
        "delete under the prefix",
        "read the metadata path",
        "destroy a version",
        "read the server's mounts",
    ),
    "signer/vault_transit": (
        "sign with another key",
        "sign through the longer path that ends in a hash name",
        "change the key's settings",
        "export the key",
        "back the key up",
        "read the server's mounts",
        "delete the key",
    ),
}

# kind ("family/name") -> the module that holds its POLICY literal.
KIND_MODULES: dict[str, str] = {
    "secrets/vault": "src/hadavin_sdk/actions/secrets_vault.py",
    "signer/vault_transit": "src/hadavin_sdk/audit/signer_vault.py",
    "source/kubernetes": "src/hadavin_sdk/sources/kubernetes.py",
}
# Kinds that sign in to an outside system and have no POLICY yet. tests/test_policy_guard.py holds the dated
# entry for each (reason, ticket, review date) and fails when this tuple and that list differ.
NOT_YET_DECLARED: tuple[str, ...] = (
    "secrets/aws_secrets_manager",
    "secrets/azure_key_vault",
    "secrets/gcp_secret_manager",
    "signer/aws_kms",
    "signer/azure_key_vault_key",
    "signer/gcp_kms",
    "anchor/s3_object_lock",
    "anchor/azure_immutable_blob",
    "anchor/gcs_retention_lock",
    "store/postgres",
    "llm/anthropic",
    "llm/bedrock",
    "llm/openai_compat",
    "llm/gemini",
    "detector/bedrock_guardrail",
    "channel/slack",
)
# Per kind: (do the declared calls equal the written ones, what the engine check is, what no test covers).
# For the two Vault kinds the engine text is built by `engine_text` from REFUSALS and ENGINE_RUN.
_VAULT_GAP = (
    "the open alternative OpenBao (not yet run); sign-in through AppRole or Kubernetes roles, where the role "
    "and identity groups can add policies; any never-list line that is not among the requests named above"
)
COVERAGE: dict[str, tuple[str, str, str]] = {
    "secrets/vault": ("yes", "", _VAULT_GAP + "; a real deployment's own mounts"),
    "signer/vault_transit": ("yes", "", _VAULT_GAP),
    "source/kubernetes": (
        "yes",
        (
            "no cluster in any test. The generated Role is given to the kind's own read-only rule (the function "
            "that judges a real cluster's answer at every start-up), which finds no problem in it and does find "
            "one when a write verb, `pods/exec` or a read of `secrets` is added"
        ),
        (
            "whether the three rules are enough on a real cluster; clusters that changed the default right of "
            "every signed-in identity to ask what it may do"
        ),
    ),
}


def engine_state() -> str:
    """One sentence: have the Vault server tests run? Never claims a run that is not on record."""
    if ENGINE_RUN is None:
        return "These tests have not run yet: no run of them is on record."
    return f"Last recorded run: {ENGINE_RUN[0]}, {ENGINE_RUN[1]}."


def engine_text(kind: str) -> str:
    if kind not in REFUSALS:
        return COVERAGE[kind][1]
    return (
        f"checked by tests that run against a real Vault server in CI only (image `{ENGINE_IMAGE}`). "
        f"{engine_state()} What those tests check: a token that holds only the generated policy text can "
        "make the kind's own requests; with one grant removed, the request that grant serves is answered "
        "403 (refused); and each of these requests is answered 403: " + "; ".join(REFUSALS[kind])
    )


PLATFORMS = ("vault", "kubernetes_rbac")
NEVER_TYPES = ("action", "role", "path", "resource", "prose")
# The never-list types each platform may use. A line typed for the other platform would be rendered on the page
# and read by no cover rule, so it is refused.
NEVER_TYPES_BY_PLATFORM = {
    "vault": ("role", "path"),
    "kubernetes_rbac": ("role", "action", "resource"),
}
# The longest time a dated entry (a pending name, claim or kind) may stand before a person decides again. The
# tests read it from here, so there is one number.
MAX_PENDING_DAYS = 92
# A phrase list, not proof: words that say a statement of fact has no vendor source or was never checked. A
# `reason` or `note` that holds one of them must also list the statement under `claims_unverified`. This is only
# an extra tripwire. The closed rule is `NOTE_CLASSES`: every note and every reason must have a class, and a
# reason or note with no class is refused whatever words it uses.
UNCHECKED_WORDING = re.compile(
    r"not found in a vendor source|nobody has checked|not been checked|not yet checked|unchecked|unverified",
    re.IGNORECASE,
)
VAULT_CAPABILITIES = ("create", "read", "update", "patch", "delete", "list")
VAULT_NEVER_CAPABILITIES = (*VAULT_CAPABILITIES, "sudo")
# Vault policy paths (sources V-POL, V-ACL, V-PARSE): `*` is a wildcard only as the LAST character (it then
# matches everything below, any depth); `+` stands for exactly ONE whole path segment; `+*` is refused by the
# server. A setting whose value always ends in `/` may stand right before a `+`.
VAULT_WILDCARDS = ("*", "+")
ENDS_IN_SLASH = ("path_prefix",)
_TOP = {"platform", "credential", "grants", "free", "never", "notes"}
_GRANT = {
    "id",
    "name",
    "resource",
    "bound",
    "operations",
    "applies_when",
    "reason",
    "verified",
    "confirmed_live",
    "claims_unverified",
}
_FREE = {"operations", "reason", "note", "verified", "claims_unverified"}
_NEVER = {"type", "name", "capabilities", "reason", "verified", "claims_unverified"}
_CREDENTIAL = {"how", "lifetime", "exception"}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SOURCE_ID = re.compile(r"[A-Z][A-Z0-9]*(-[A-Z0-9]+)*")  # a key of the sources file, never a URL
_ID = re.compile(r"R\d{2}")
_FIELD = re.compile(r"\{([a-z_]+)\}")
_OPERATOR = re.compile(r"<([A-Z_]+)>")
_K8S_RESOURCE = re.compile(r"([a-z0-9.-]+)/([a-z]+(?:/[a-z]+)?) in \{namespaces\}")

# Grammar per value. A value must FULLY match. Each row copies a pattern of the settings model or the kind
# module; tests/test_policy_guard.py compares the copies with the originals.
_LABEL = r"[a-z0-9]([a-z0-9.\-]*[a-z0-9])?"
GRAMMAR: dict[str, str] = {
    "mount": r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*",  # backends/table.py `_PATH`
    "transit_mount": r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*",  # backends/table.py `_PATH`
    "path_prefix": r"([A-Za-z0-9_.-]+/)+",  # the setting's pattern, and NOT empty
    "key_name": r"[A-Za-z0-9_.-]+",  # VaultTransitSettings.key_name
    "namespaces": _LABEL,  # sources/kubernetes.py `_NS`; each name of the comma-joined list
    # The three names below are chosen by the operator. Their grammar is this file's own (the namespace
    # grammar reused); it was not checked against the Kubernetes pages.
    "ROLE_NAME": _LABEL,
    "SERVICE_ACCOUNT": _LABEL,
    "SERVICE_ACCOUNT_NAMESPACE": _LABEL,
}
KUBERNETES_OPERATOR_VALUES = ("ROLE_NAME", "SERVICE_ACCOUNT", "SERVICE_ACCOUNT_NAMESPACE")
# A value can pass its character grammar and still name a privileged or reserved thing. Such a value can
# never be right for this identity, so no text is produced for it (refused, not warned about).
# Vault: a mount whose first part is one of the server's own top-level paths.
RESERVED_MOUNTS = ("sys", "auth", "identity", "cubbyhole")
# Kubernetes: the cluster's own namespaces (`kube-` prefix); role names that are, or look like, the built-in
# roles; the ServiceAccount `default`, which every pod of a namespace gets when none is named, so it is not
# one identity per function.
RESERVED_NAMESPACE_PREFIX = "kube-"
RESERVED_ROLE_NAMES = ("cluster-admin", "admin", "edit", "view")
RESERVED_ROLE_PREFIX = "system"
RESERVED_SERVICE_ACCOUNTS = ("default",)
# Longest value per placeholder. Kubernetes: 63 for a namespace name and 253 for the other names, FROM
# MEMORY (the names page is not among the pinned sources). Vault: no limit was found in the pinned sources;
# 255 is this file's own bound.
MAX_LENGTH: dict[str, int] = {
    "mount": 255,
    "transit_mount": 255,
    "path_prefix": 255,
    "key_name": 255,
    "namespaces": 63,
    "ROLE_NAME": 253,
    "SERVICE_ACCOUNT": 253,
    "SERVICE_ACCOUNT_NAMESPACE": 63,
}


def reserved_problem(key: str, part: str) -> str | None:
    """Why this value, though well-formed, is refused; None when it is not reserved."""
    if key in ("mount", "transit_mount") and part.split("/")[0] in RESERVED_MOUNTS:
        return (
            f"starts with Vault's own path {part.split('/')[0]!r}, which is never a secrets mount"
        )
    if key in ("namespaces", "SERVICE_ACCOUNT_NAMESPACE") and part.startswith(
        RESERVED_NAMESPACE_PREFIX
    ):
        return "is one of the cluster's own namespaces (`kube-` prefix)"
    if key == "ROLE_NAME" and (
        part in RESERVED_ROLE_NAMES or part.startswith(RESERVED_ROLE_PREFIX)
    ):
        return "is, or looks like, a built-in role name"
    if key == "SERVICE_ACCOUNT" and part in RESERVED_SERVICE_ACCOUNTS:
        return "is the ServiceAccount every pod gets by default, not an identity of its own"
    return None


WHOLE_MOUNT = (
    "Read first: the `path_prefix` setting is empty by default, and with an empty prefix this kind can read "
    "every secret at the top level of the mount. Set a prefix. No copy-ready text is produced for an empty "
    "prefix."
)


class PolicyError(ValueError):
    """The POLICY literal is not a pure literal or breaks a data rule."""


@dataclass(frozen=True)
class Grant:
    id: str
    name: str
    resource: str
    bound: str
    operations: tuple[tuple[str, ...], ...]
    applies_when: str
    reason: str
    verified: (
        tuple[str, ...] | None
    )  # (date, source id, ...): name and resource form found in a vendor source
    confirmed_live: tuple[str, str] | None  # (date, masked account): accepted by a real account
    claims_unverified: tuple[str, ...]


@dataclass(frozen=True)
class Free:
    operations: tuple[tuple[str, ...], ...]
    reason: str
    note: str
    verified: tuple[str, ...] | None
    claims_unverified: tuple[str, ...] = ()


@dataclass(frozen=True)
class Never:
    type: str
    name: str
    capabilities: tuple[str, ...]
    reason: str
    verified: tuple[str, ...] | None
    claims_unverified: tuple[str, ...] = ()


@dataclass(frozen=True)
class Policy:
    platform: str
    how: str
    lifetime: str
    exception: str
    grants: tuple[Grant, ...]
    free: tuple[Free, ...]
    never: tuple[Never, ...]
    notes: tuple[str, ...]

    def operations(self) -> set[tuple[str, ...]]:
        """Every request the kind declares: the calls behind its grants plus the free ones."""
        return {op for entry in (*self.grants, *self.free) for op in entry.operations}


# ------------------------------------------------------------------------------------------------ load


def _is_text(value: object) -> bool:
    return isinstance(value, str)


def _texts(value: object) -> bool:
    return isinstance(value, tuple) and all(isinstance(x, str) for x in value)


def _keys(where: str, raw: object, allowed: set[str], required: set[str]) -> list[str]:
    if not isinstance(raw, dict):
        return [f"{where}: must be a dict"]
    out = [f"{where}: unknown key {k!r}" for k in sorted(set(map(str, raw)) - allowed)]
    return out + [f"{where}: missing key {k!r}" for k in sorted(required - set(raw))]


def _is_date(text: str) -> bool:
    """A real calendar date written YYYY-MM-DD (9999-99-99 is not one)."""
    if not _DATE.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _unprintable(where: str, value: object) -> Iterator[str]:
    """Where a text anywhere in the literal holds a control or other non-printing character (a newline, a
    tab, a line separator). Such a character would end a comment in the rendered text, and what follows it
    would be read by the platform as policy that no rule here ever saw."""
    if isinstance(value, str):
        if not value.isprintable():
            yield where
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _unprintable(f"{where}.{key}" if isinstance(key, str) else where, key)
            yield from _unprintable(f"{where}.{key}", item)
    elif isinstance(value, tuple | list):
        for i, item in enumerate(value):
            yield from _unprintable(f"{where}[{i}]", item)


def _vault_path_problems(where: str, resource: str) -> list[str]:
    """The wildcard forms the Vault server itself accepts (see VAULT_WILDCARDS)."""
    out = []
    if "*" in resource[:-1]:
        out.append(
            f"{where}: resource {resource!r}: `*` is a Vault wildcard only as the last character"
        )
    if "+*" in resource:
        out.append(f"{where}: resource {resource!r}: Vault refuses `+*`")
    for found in re.finditer(r"\+", resource):
        before, after = resource[: found.start()], resource[found.end() :]
        field = re.search(r"\{([a-z_]+)\}$", before)
        whole = (
            before == "" or before.endswith("/") or (field and field.group(1) in ENDS_IN_SLASH)
        ) and (after == "" or after.startswith("/"))
        if not whole:
            out.append(
                f"{where}: resource {resource!r}: `+` must be one whole path segment (Vault matches it "
                "only so)"
            )
    return out


def _verified(where: str, value: object) -> list[str]:
    """None, or (date, source id, ...). A source id is a key of the sources file: never a URL or a host."""
    if value is None:
        return []
    if not isinstance(value, tuple) or not _texts(value) or len(value) < 2:
        return [f"{where}: verified must be None or (date, source id, ...)"]
    if not _is_date(value[0]):
        return [f"{where}: verified must start with a real date such as 2026-11-11"]
    return [
        f"{where}: verified source {s!r} is not a source id (a URL or host is never written here)"
        for s in value[1:]
        if not _SOURCE_ID.fullmatch(s)
    ]


def _operations(where: str, value: object, platform: str) -> list[str]:
    arity = 2 if platform == "vault" else 1
    if (
        not isinstance(value, tuple)
        or not value
        or not all(_texts(op) and len(op) == arity and all(op) for op in value)
    ):
        return [
            (
                f"{where}: operations must be a non-empty tuple of {arity}-part tuples of text: every grant "
                "names the call it serves"
            )
        ]
    return []


def _grant_problems(where: str, g: dict, platform: str) -> list[str]:
    out = _operations(where, g["operations"], platform)
    for key in ("id", "name", "resource", "bound", "applies_when", "reason"):
        if not _is_text(g[key]):
            return [*out, f"{where}: {key} must be text"]
    if not _ID.fullmatch(g["id"]):
        out.append(f"{where}: id {g['id']!r} must look like R17")
    if not g["name"] or "*" in g["name"] or "?" in g["name"]:
        out.append(f"{where}: name {g['name']!r} must be one permission name with no * or ?")
    if not g["resource"]:
        out.append(f"{where}: resource is empty")
    wildcards = ("*", "?", "+") if platform == "vault" else ("*", "?")
    if any(w in g["resource"] for w in wildcards) and not g["bound"].strip():
        out.append(
            f"{where}: resource {g['resource']!r} holds a wildcard, so `bound` must say what limits it"
        )
    if platform == "vault":
        out += _vault_path_problems(where, g["resource"])
    for name in _FIELD.findall(g["resource"]) + _OPERATOR.findall(g["resource"]):
        if name not in GRAMMAR:
            out.append(
                f"{where}: placeholder {name!r} in the resource has no grammar, so it is refused"
            )
    if re.search(r"[{}<>]", _OPERATOR.sub("", _FIELD.sub("", g["resource"]))):
        out.append(
            f"{where}: resource {g['resource']!r} holds a brace or an angle bracket that is not a "
            "`{setting}` or `<NAME>` placeholder; it would stay in the rendered text unfilled"
        )
    if not g["reason"].strip():
        out.append(f"{where}: reason is empty")
    out += _verified(where, g["verified"])
    live = g["confirmed_live"]
    if live is not None and not (_texts(live) and len(live) == 2 and _is_date(live[0])):
        out.append(f"{where}: confirmed_live must be None or (date, masked account)")
    if not _texts(g["claims_unverified"]):
        out.append(f"{where}: claims_unverified must be a tuple of text")
    if platform == "vault" and g["name"] not in VAULT_CAPABILITIES:
        out.append(f"{where}: {g['name']!r} is not a Vault capability a grant may hold")
    if platform == "kubernetes_rbac" and not _K8S_RESOURCE.fullmatch(g["resource"]):
        out.append(
            f"{where}: resource {g['resource']!r} must read '<group>/<resource> in {{namespaces}}' "
            "(the group `core` stands for the unnamed core group)"
        )
    return out


def _claims_problems(where: str, entry: dict) -> list[str]:
    """`claims_unverified` of a free or never entry (optional) and the wording rule: a reason or note that says a
    statement is unchecked must list that statement there."""
    claims = entry.get("claims_unverified", ())
    if not _texts(claims) or not all(c.strip() for c in claims):
        return [f"{where}: claims_unverified must be a tuple of non-empty text"]
    said = [
        k
        for k in ("reason", "note")
        if _is_text(entry.get(k)) and UNCHECKED_WORDING.search(entry[k])
    ]
    if said and not claims:
        return [
            (
                f"{where}: {said[0]} says a statement is not checked or has no vendor source, so that "
                "statement must be listed in claims_unverified (the page shows it and a dated entry in the "
                "tests watches it)"
            )
        ]
    return []


def _never_problems(where: str, n: dict, platform: str) -> list[str]:
    out = _claims_problems(where, n)
    if n["type"] not in NEVER_TYPES:
        out.append(f"{where}: unknown never type {n['type']!r}")
    elif n["type"] not in NEVER_TYPES_BY_PLATFORM[platform]:
        out.append(
            f"{where}: never type {n['type']!r} does not fit platform {platform!r} (allowed: "
            f"{', '.join(NEVER_TYPES_BY_PLATFORM[platform])}); no cover rule would read it"
        )
    if not _is_text(n["name"]) or not n["name"]:
        out.append(f"{where}: name must be non-empty text")
    if not _is_text(n["reason"]) or not n["reason"].strip():
        out.append(f"{where}: reason is empty")
    caps = n.get("capabilities", ())
    if not _texts(caps) or (caps and n["type"] != "path"):
        out.append(f"{where}: capabilities is a tuple of text, on a `path` entry only")
    elif unknown := sorted(set(caps) - set(VAULT_NEVER_CAPABILITIES)):
        out.append(f"{where}: {unknown[0]!r} is not a Vault capability")
    return out + _verified(where, n["verified"])


def problems(raw: object) -> list[str]:
    """Every data-rule problem of one evaluated POLICY literal (empty: it may be used)."""
    out = _keys("POLICY", raw, _TOP, _TOP - {"notes"})
    if out or not isinstance(raw, dict):
        return out
    if bad := sorted(set(_unprintable("POLICY", raw))):
        return [
            f"{where}: holds a control or other non-printing character (a newline, a tab); it would be "
            "copied into the rendered policy text"
            for where in bad
        ]
    platform = raw["platform"]
    if platform not in PLATFORMS:
        return [f"POLICY: unknown platform {platform!r}"]
    cred = raw["credential"]
    out += _keys("credential", cred, _CREDENTIAL, _CREDENTIAL)
    if not out:
        if not all(_is_text(cred[k]) for k in _CREDENTIAL) or not cred["how"].strip():
            out.append("credential: how, lifetime and exception must be text, and how not empty")
        elif cred["lifetime"] not in ("short", "long"):
            out.append(f"credential: lifetime {cred['lifetime']!r} must be short or long")
        elif cred["lifetime"] == "long" and not cred["exception"].strip():
            out.append(
                "credential: a long-lived credential needs `exception`: why, and what removes it"
            )
    for key in ("grants", "free", "never"):
        if not isinstance(raw[key], tuple):
            out.append(f"POLICY: {key} must be a tuple")
    if not _texts(raw.get("notes", ())):
        out.append("POLICY: notes must be a tuple of text")
    if out:
        return out
    for i, g in enumerate(raw["grants"]):
        where = f"grant {g.get('id', i) if isinstance(g, dict) else i}"
        out += _keys(where, g, _GRANT, _GRANT) or _grant_problems(where, g, platform)
    for i, f in enumerate(raw["free"]):
        where = f"free entry {i}"
        bad = _keys(where, f, _FREE, _FREE - {"claims_unverified"})
        if not bad:
            bad = _operations(where, f["operations"], platform) + _verified(where, f["verified"])
            if not (_is_text(f["reason"]) and f["reason"].strip() and _is_text(f["note"])):
                bad.append(f"{where}: reason must be non-empty text and note text")
            bad += _claims_problems(where, f)
        out += bad
    for i, n in enumerate(raw["never"]):
        where = f"never entry {i}"
        out += _keys(
            where, n, _NEVER, _NEVER - {"capabilities", "claims_unverified"}
        ) or _never_problems(where, n, platform)
    if not out:
        ids = [g["id"] for g in raw["grants"]]
        out += [f"grant id {i} is used twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
        seen = [g["resource"] for g in raw["grants"]]
        if platform == "vault":
            out += [
                f"resource {r!r} is on two grants: one Vault path takes one grant"
                for r in sorted({r for r in seen if seen.count(r) > 1})
            ]
        claimed = [op for entry in (*raw["grants"], *raw["free"]) for op in entry["operations"]]
        out += [
            f"request {op!r} is claimed twice: one request is served by one grant or one free entry"
            for op in sorted({op for op in claimed if claimed.count(op) > 1})
        ]
    return out


def literal(text: str, where: str = "module") -> object | None:
    """The evaluated `POLICY` literal of one module's source text, or None when the module has none."""
    try:
        body = ast.parse(text).body
    except SyntaxError as exc:
        raise PolicyError(f"{where}: is not valid Python (line {exc.lineno})") from None
    found = [
        node
        for node in body
        if isinstance(node, ast.Assign | ast.AnnAssign)
        and any(
            isinstance(t, ast.Name) and t.id == "POLICY"
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    if not found:
        return None
    if len(found) > 1 or found[0].value is None:
        raise PolicyError(f"{where}: POLICY must be assigned exactly once")
    for node in ast.walk(found[0].value):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            if twice := sorted({str(k) for k in keys if keys.count(k) > 1}):
                raise PolicyError(
                    f"{where}: key {twice[0]!r} is written twice in one dict of POLICY (line {node.lineno}); "
                    "Python would silently keep the later one"
                )
    try:
        value = ast.literal_eval(found[0].value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise PolicyError(
            f"{where}: POLICY is not a pure literal (a call, a name or an expression is never run)"
        ) from None
    if not isinstance(value, dict):
        raise PolicyError(f"{where}: POLICY must be a dict (found {type(value).__name__})")
    return value


def parse(text: str, where: str = "module") -> Policy | None:
    raw = literal(text, where)
    if raw is None:
        return None
    bad = problems(raw)
    if bad or not isinstance(raw, dict):
        raise PolicyError(f"{where}: " + "; ".join(bad))
    cred = raw["credential"]
    return Policy(
        platform=raw["platform"],
        how=cred["how"],
        lifetime=cred["lifetime"],
        exception=cred["exception"],
        grants=tuple(Grant(**g) for g in raw["grants"]),
        free=tuple(Free(**f) for f in raw["free"]),
        never=tuple(Never(**{"capabilities": (), **n}) for n in raw["never"]),
        notes=tuple(raw.get("notes", ())),
    )


def load(path: Path) -> Policy | None:
    """The POLICY of the module at `path`, read from its source text. None: the module declares none."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PolicyError(f"{Path(path).name}: cannot be read ({type(exc).__name__})") from None
    return parse(text, Path(path).name)


def load_all(root: Path | None = None) -> dict[str, Policy | None]:
    root = DATA_ROOT if root is None else root
    return {kind: load(root / rel) for kind, rel in KIND_MODULES.items()}


def stray_modules(root: Path) -> list[str]:
    """A `POLICY` in a module that KIND_MODULES does not name is read by nothing: report it."""
    known, out = set(KIND_MODULES.values()), []
    for path in sorted((root / "src").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel in known:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            holds = "POLICY" in text and literal(text, rel) is not None
        except PolicyError:
            holds = True
        except (OSError, UnicodeDecodeError):
            holds = False
        if holds:
            out.append(f"{rel}: holds a POLICY but is not in KIND_MODULES, so no check reads it")
    return out


def head_lines(root: Path) -> list[str]:
    """The lines of the sources file. The ONE place the file is read for every parser (the rows, the lists of
    builder-only ids and the claim marks): a leading byte-order mark is dropped here, once, so all three accept
    or refuse the same file."""
    try:
        text = (root / SOURCES).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PolicyError(f"{SOURCES}: cannot be read ({type(exc).__name__})") from None
    return text.removeprefix("\ufeff").splitlines()


def source_ids(root: Path) -> dict[str, tuple[str, str, str, str]]:
    """id -> (url, commit, sha256, note) from the sources file. Every row is pinned: the commit is written
    in the URL, never a branch name. PolicyError names the first bad row."""
    return _source_rows(head_lines(root))


def _source_rows(lines: list[str]) -> dict[str, tuple[str, str, str, str]]:
    out: dict[str, tuple[str, str, str, str]] = {}
    for n, line in enumerate(lines, 1):
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(" | ")]
        where = f"{SOURCES}:{n}"
        if len(parts) != 5:
            raise PolicyError(f"{where}: a row has five columns: id | url | commit | sha256 | note")
        key, url, commit, digest, note = parts
        if not _SOURCE_ID.fullmatch(key) or key in out:
            raise PolicyError(f"{where}: id {key!r} is not a source id or is used twice")
        if not re.fullmatch(r"[0-9a-f]{7,40}", commit) or f"/{commit}/" not in url:
            raise PolicyError(
                f"{where}: {key} is not pinned: the commit column must be a commit id that is written in "
                "the URL (a branch name moves)"
            )
        if not url.startswith("https://") or not re.fullmatch(r"[0-9a-f]{64}", digest) or not note:
            raise PolicyError(f"{where}: {key} needs an https URL, a sha256 and a note")
        out[key] = (url, commit, digest, note)
    return out


def source_problems(policies: dict[str, Policy], known: set[str]) -> list[str]:
    """Every source id named in a `verified` field resolves in the sources file."""
    out = []
    for kind, policy in policies.items():
        entries = [(f"grant {g.id}", g.verified) for g in policy.grants]
        entries += [(f"free entry {i}", f.verified) for i, f in enumerate(policy.free)]
        entries += [(f"never {n.name}", n.verified) for n in policy.never]
        for where, verified in entries:
            out += [
                f"{kind} {where}: source id {s} is not in the sources file"
                for s in (verified or ())[1:]
                if s not in known
            ]
    return out


@dataclass(frozen=True)
class Pending:
    """A dated entry: something not yet done, with the day it was decided and the day it is looked at again."""

    reason: str
    fix_ref: str
    decided: date
    review_by: date  # the check fails after this date


DECIDED = date(2026, 11, 11)
_ROLE_NAMES = Pending(
    "the built-in role name was not among the names the evidence runner looked for",
    "an evidence run that finds the name in source K-SRC, then set `verified` and delete this entry",
    DECIDED,
    date(2026, 12, 11),
)
_BUILDER_ONLY = Pending(
    "the path was read in the vendor source by the builder of a fix only, not by an evidence runner",
    "an evidence run that finds the path in the listed sources, then set `verified` and delete this entry",
    DECIDED,
    date(2026, 12, 11),
)
# (kind, entry) -> a name not yet found in a vendor source by the evidence runner. The entry is a grant id,
# `free:<n>` or `never:<name>`. All six grants are found (the claims of R17, R18, R20 to R22 are separate: see
# `claims_unverified`); three built-in role names of the Kubernetes never-list are not, and three never-list
# paths were read by the builder of a fix only. Moved here from the tests so that `--check` runs the rule.
PENDING_NAMES: dict[tuple[str, str], Pending] = {
    ("secrets/vault", "never:{mount}/undelete/*"): _BUILDER_ONLY,
    ("secrets/vault", "never:{mount}/subkeys/*"): _BUILDER_ONLY,
    ("signer/vault_transit", "never:{transit_mount}/byok-export/*"): _BUILDER_ONLY,
    ("source/kubernetes", "never:cluster-admin"): _ROLE_NAMES,
    ("source/kubernetes", "never:admin"): _ROLE_NAMES,
    ("source/kubernetes", "never:edit"): _ROLE_NAMES,
}
_CLAIM_PENDING = Pending(
    "the statement about server or API behaviour is not checked by an evidence runner",
    "an evidence run that reads the sources named in the fixture header, then set `claims_unverified` to () and "
    "delete this entry",
    DECIDED,
    date(2026, 12, 11),
)
# (kind, grant id | `free:<n>` | `never:<name>`) -> a statement about how the vendor's server or API behaves that
# nobody but the builder of a fix has read, or that nobody has checked. Every entry with a `claims_unverified`
# needs one; the check goes red on the review date if the claim is still unread.
PENDING_CLAIMS: dict[tuple[str, str], Pending] = {
    ("secrets/vault", "R17"): _CLAIM_PENDING,
    ("signer/vault_transit", "R18"): _CLAIM_PENDING,
    ("source/kubernetes", "R20"): _CLAIM_PENDING,
    ("source/kubernetes", "R21"): _CLAIM_PENDING,
    ("source/kubernetes", "R22"): _CLAIM_PENDING,
    ("source/kubernetes", "free:0"): _CLAIM_PENDING,
    ("source/kubernetes", "never:create"): _CLAIM_PENDING,
}


def pending_problems(label: str, pending: dict, live: set, today: date) -> list[str]:
    """The one rule for every dated list: an entry whose subject is fixed or gone is stale; an entry past its
    `review_by` is overdue; a `review_by` more than MAX_PENDING_DAYS after `decided` is refused; a `decided` in
    the future is refused."""
    out = [
        f"{label} {key} is fixed or gone: delete the entry" for key in pending if key not in live
    ]
    out += [
        f"{label} {key} is overdue (review_by {p.review_by}): {p.fix_ref}. What to do: finish that work "
        "and delete the entry; or, if it cannot be finished now, decide again: set `decided` to the day "
        f"of the new decision and `review_by` to at most {MAX_PENDING_DAYS} days after it"
        for key, p in pending.items()
        if key in live and today > p.review_by
    ]
    out += [
        f"{label} {key}: review_by {p.review_by} is more than {MAX_PENDING_DAYS} days after the decision "
        f"of {p.decided}: a date may not be moved further than that"
        for key, p in pending.items()
        if (p.review_by - p.decided).days > MAX_PENDING_DAYS
    ]
    return out + [
        f"{label} {key}: decided {p.decided} is in the future"
        for key, p in pending.items()
        if p.decided > today
    ]


def entries(policies: dict[str, Policy]) -> Iterator[tuple[str, str, Grant | Free | Never]]:
    """(kind, entry label, entry): a grant is labelled by its id, a free request `free:<n>`, a never-list line
    `never:<name>`."""
    for kind, p in policies.items():
        yield from ((kind, g.id, g) for g in p.grants)
        yield from ((kind, f"free:{i}", f) for i, f in enumerate(p.free))
        yield from ((kind, f"never:{n.name}", n) for n in p.never)


def name_pending_problems(
    policies: dict[str, Policy], pending: dict[tuple[str, str], Pending], today: date
) -> list[str]:
    """ONE rule: an entry (a grant, a free request, a never-list line) with `verified = None` fails unless its
    (kind, entry) has a dated PENDING_NAMES entry."""
    unverified = {(k, label) for k, label, e in entries(policies) if e.verified is None}
    out = [
        f"{kind} {label}: the name is not found in a vendor source (verified is None) and has no "
        "PENDING_NAMES entry"
        for kind, label in sorted(unverified - set(pending))
    ]
    return out + pending_problems("PENDING_NAMES", pending, unverified, today)


def claim_pending_problems(
    policies: dict[str, Policy], pending: dict[tuple[str, str], Pending], today: date
) -> list[str]:
    """ONE rule: an entry with an unchecked claim (`claims_unverified`) fails unless its (kind, entry) has a dated
    PENDING_CLAIMS entry; an entry for one with no such claim is stale."""
    claimed = {(k, label) for k, label, e in entries(policies) if e.claims_unverified}
    out = [
        f"{kind} {label}: has an unchecked claim (claims_unverified) and no PENDING_CLAIMS entry"
        for kind, label in sorted(claimed - set(pending))
    ]
    return out + pending_problems("PENDING_CLAIMS", pending, claimed, today)


def data_problems(root: Path | None = None, today: date | None = None) -> list[str]:
    """Every data problem `--check` reports, one line each (empty: the page may be written): each literal's
    own rules, the rules across kinds, modules that hold a POLICY nobody reads, source ids, the rule of every
    note and reason, the claim marks, and the dated lists (PENDING_NAMES, PENDING_CLAIMS: a name or claim with
    no dated entry, a stale or overdue entry). `today` defaults to the current UTC date."""
    root = DATA_ROOT if root is None else root
    today = datetime.now(UTC).date() if today is None else today
    out, policies = [], {}
    for kind, rel in KIND_MODULES.items():
        try:
            policy = load(root / rel)
        except PolicyError as exc:
            out.append(str(exc))
            continue
        if policy is None:
            out.append(f"no POLICY in {rel}")
        else:
            policies[kind] = policy
    out += cross_problems(policies) + stray_modules(root)
    if set(policies) == set(
        KIND_MODULES
    ):  # a kind that could not be read is reported once, by its own line
        out += name_pending_problems(policies, PENDING_NAMES, today)
        out += claim_pending_problems(policies, PENDING_CLAIMS, today)
    try:
        known = set(source_ids(root))
        out += source_problems(policies, known)
        out += note_problems(policies, NOTE_CLASSES, known)
        out += claim_mark_problems(policies, read_marks(root))
    except PolicyError as exc:
        out.append(str(exc))
    return out


def cross_problems(policies: dict[str, Policy]) -> list[str]:
    """Rules across kinds: a grant id names one grant; nothing one kind needs is on another kind's
    never-list as an `action` (one process holds several kinds, so that would break a deployment)."""
    out, owner = [], {}
    for kind, policy in policies.items():
        for g in policy.grants:
            if g.id in owner:
                out.append(f"grant id {g.id} is used by {owner[g.id]} and by {kind}")
            owner[g.id] = kind
    names = {(p.platform, g.name): kind for kind, p in policies.items() for g in p.grants}
    for kind, policy in policies.items():
        for n in policy.never:
            if n.type == "action" and (policy.platform, n.name) in names:
                out.append(
                    f"{kind}: never-list action {n.name!r} is a permission that "
                    f"{names[(policy.platform, n.name)]} needs"
                )
        out += never_covers_grant_problems(kind, policy)
    return out


# A Vault policy path as a small automaton, so that two paths are compared by whether ONE concrete path fits
# both (a real overlap), not by one sample string each. Characters: a literal, `+` (one or more characters that
# are not `/`) and a last `*` (any characters, also none). The setting `{path_prefix}` is ONE value in a
# deployment (one or more parts, each ending in `/`; GRAMMAR["path_prefix"]), so both paths are given the SAME
# number of parts for it, tried from 1 upward (`vault_paths_overlap`); the characters of its parts are not
# required to be equal in both, so a never line is flagged when it MAY overlap (the safe side). Every other
# `{setting}` and `<NAME>` stays one fixed word (its own name) the same way in both paths, so equal placeholders
# stay equal. Source: V-POL, V-ACL (the matching rule); the automaton is this file's own reading of it.
_ANY, _NOT_SLASH = "any", "not-slash"
_PREFIX = "{path_prefix}"


def _vault_form(resource: str) -> str:
    """A grant or never-list path with every `{field}` (but `{path_prefix}`) and `<NAME>` replaced by one fixed
    word, the field's own name, the same way in both lists."""
    return _OPERATOR.sub(
        lambda m: m.group(1),
        re.sub(r"\{(?!path_prefix\})([a-z_]+)\}", lambda m: m.group(1), resource),
    )


def _vault_automaton(path: str) -> tuple[dict[int, list[tuple[str, int]]], int]:
    """(moves per state, final state) of one policy path in `_vault_form` with no `{path_prefix}` left."""
    moves: dict[int, list[tuple[str, int]]] = {}
    count = 0

    def new() -> int:
        nonlocal count
        count += 1
        return count

    def edge(src: int, cls: str, dst: int) -> None:
        moves.setdefault(src, []).append((cls, dst))

    cur, i = 0, 0
    while i < len(path):
        if path[i] == "+":
            nxt = new()
            edge(cur, _NOT_SLASH, nxt)
            edge(nxt, _NOT_SLASH, nxt)
            cur, i = nxt, i + 1
        elif path[i] == "*" and i == len(path) - 1:
            edge(cur, _ANY, cur)
            i += 1
        else:
            nxt = new()
            edge(cur, path[i], nxt)
            cur, i = nxt, i + 1
    return moves, cur


def _both_take(a: str, b: str) -> bool:
    """Can one character be read by both edge classes (a literal, `not-slash` or `any`)?"""
    if _ANY in (a, b):
        return True
    if a == _NOT_SLASH:
        return b != "/"
    return a == b or (b == _NOT_SLASH and a != "/")


def _overlap_of_forms(first: str, second: str) -> bool:
    """True when some concrete path fits two policy paths that hold no `{path_prefix}`."""
    one, end_one = _vault_automaton(first)
    two, end_two = _vault_automaton(second)
    seen, todo = {(0, 0)}, [(0, 0)]
    while todo:
        p, q = todo.pop()
        if (p, q) == (end_one, end_two):
            return True
        for cls_one, nxt_one in one.get(p, ()):
            for cls_two, nxt_two in two.get(q, ()):
                if _both_take(cls_one, cls_two) and (nxt_one, nxt_two) not in seen:
                    seen.add((nxt_one, nxt_two))
                    todo.append((nxt_one, nxt_two))
    return False


def vault_paths_overlap(first: str, second: str) -> bool:
    """True when some concrete path is allowed by both policy paths (each given in `_vault_form`). A
    `{path_prefix}` in either is one value of `k` parts (each part `+/`), the same `k` in both, for k from 1 up to
    the number of slashes of the two paths plus one (a longer prefix cannot fit the other path, and a path with a
    last `*` that fits at a longer prefix also fits at a shorter one)."""
    if _PREFIX not in first and _PREFIX not in second:
        return _overlap_of_forms(first, second)
    most = first.count("/") + second.count("/") + 1
    return any(
        _overlap_of_forms(first.replace(_PREFIX, "+/" * k), second.replace(_PREFIX, "+/" * k))
        for k in range(1, most + 1)
    )


def never_covers_grant_problems(kind: str, policy: Policy) -> list[str]:
    """No never-list line may cover a grant of its own kind: the same resource AND a capability the line
    forbids (a line with no capabilities forbids all). Vault: the two path patterns overlap (a real overlap of
    the two patterns, `vault_paths_overlap`; two kinds are never compared with each other, as each kind has its
    own identity). Kubernetes: a `resource` line names the grant's resource. (A `action` line against a grant
    verb is checked above, across kinds and within one.)"""
    out = []
    for n in policy.never:
        if policy.platform == "vault" and n.type == "path":
            for g in policy.grants:
                if n.capabilities and g.name not in n.capabilities:
                    continue
                if vault_paths_overlap(_vault_form(n.name), _vault_form(g.resource)):
                    out.append(_covers(kind, n, g))
        elif policy.platform == "kubernetes_rbac" and n.type == "resource":
            out += [
                _covers(kind, n, g)
                for g in policy.grants
                if (m := _K8S_RESOURCE.fullmatch(g.resource)) and m.group(2) == n.name
            ]
    return out


def _covers(kind: str, n: Never, g: Grant) -> str:
    caps = f" with {', '.join(n.capabilities)}" if n.capabilities else ""
    return (
        f"{kind}: never-list {n.type} {n.name!r}{caps} covers the resource and capability of grant {g.id} "
        f"({g.name} on {g.resource!r}): the page would give and forbid the same right"
    )


# ---------------------------------------------------------------------------------------------- render


def placeholders(policy: Policy) -> list[str]:
    """Every `{field}` (a setting of the kind) and `<NAME>` (filled in by the operator) the rendered text
    of this policy needs."""
    found: list[str] = []
    for g in policy.grants:
        found += _FIELD.findall(g.resource) + _OPERATOR.findall(g.resource)
    if policy.platform == "kubernetes_rbac":
        found += KUBERNETES_OPERATOR_VALUES
    return list(dict.fromkeys(found))


def _checked(policy: Policy, values: dict[str, str]) -> dict[str, str]:
    """`values` when every needed key is present and fully matches its grammar; else ValueError naming the
    key. Nothing is escaped or repaired."""
    need = placeholders(policy)
    for key in need:
        if key not in values:
            raise ValueError(f"policy value {key!r} is missing")
    for key in values:
        if key not in need:
            raise ValueError(f"policy value {key!r} is not used by this kind")
    for key in need:
        value, grammar = values[key], GRAMMAR.get(key)
        if grammar is None:
            raise ValueError(f"policy value {key!r} has no grammar, so it is refused")
        text = (
            value if isinstance(value, str) else ""
        )  # anything that is not text fails the grammar
        parts = text.split(",") if key == "namespaces" else [text]
        if len(set(parts)) != len(parts):
            raise ValueError(f"policy value {key!r} names the same namespace twice")
        for part in parts:
            if not re.fullmatch(grammar, part) or {".", ".."} & set(part.split("/")):
                if key == "path_prefix" and value == "":
                    raise ValueError(
                        "policy value 'path_prefix' is empty: an empty prefix means the whole mount, and "
                        "no policy text is produced for that"
                    )
                raise ValueError(f"policy value {key!r} does not match its grammar: {part!r}")
            if len(part) > MAX_LENGTH[key]:
                raise ValueError(
                    f"policy value {key!r} is longer than {MAX_LENGTH[key]} characters"
                )
            if why := reserved_problem(key, part):
                raise ValueError(f"policy value {key!r} is refused: {part!r} {why}")
    return values


def _fill(template: str, values: dict[str, str] | None) -> str:
    if values is None:
        return template
    filled = _FIELD.sub(lambda m: values[m.group(1)], template)
    filled = _OPERATOR.sub(lambda m: values[m.group(1)], filled)
    if re.search(r"[{}<>]", filled):
        raise ValueError(f"a placeholder is left unfilled in {filled!r}: no text is produced")
    return filled


def render_vault(policy: Policy, values: dict[str, str] | None = None) -> str:
    """Vault policy text: one `path` block per grant. `values=None` is page mode: `{field}` and `<NAME>`
    stay as written. With `values`, every placeholder must be present and fully match its grammar."""
    if policy.platform != "vault":
        raise ValueError("render_vault takes a policy of platform vault")
    if values is not None:
        values = _checked(policy, values)
    blocks = []
    for g in policy.grants:
        if g.name not in VAULT_CAPABILITIES:
            raise ValueError(f"{g.id}: {g.name!r} is not a Vault capability")
        path = _fill(g.resource, values)
        if values is not None and (
            "*" in path[:-1] or any("+" in part and part != "+" for part in path.split("/"))
        ):
            raise ValueError(
                f"{g.id}: {path!r} holds a wildcard in a place where Vault does not read one"
            )
        blocks.append(
            f"# {g.id}: {g.reason}\npath {json.dumps(path)} {{\n  capabilities = [{json.dumps(g.name)}]\n}}\n"
        )
    return "\n".join(blocks)


def kubernetes_rules(policy: Policy) -> list[dict[str, list[str]]]:
    """The `rules` of the Role: one rule per grant (API group, resource, verb), nothing merged."""
    if policy.platform != "kubernetes_rbac":
        raise ValueError("kubernetes_rules takes a policy of platform kubernetes_rbac")
    rules = []
    for g in policy.grants:
        match = _K8S_RESOURCE.fullmatch(g.resource)
        if match is None:
            raise ValueError(
                f"{g.id}: resource {g.resource!r} is not '<group>/<resource> in {{namespaces}}'"
            )
        group = "" if match.group(1) == "core" else match.group(1)
        rules.append({"apiGroups": [group], "resources": [match.group(2)], "verbs": [g.name]})
    return rules


def render_kubernetes(policy: Policy, values: dict[str, str] | None = None) -> str:
    """One namespaced Role and one RoleBinding per namespace, never a ClusterRole. `values=None` is page
    mode (placeholders stay). With `values`, `namespaces` is a comma-joined list and every placeholder must
    be present and fully match its grammar."""
    rules = kubernetes_rules(policy)
    if values is None:
        namespaces, v = ["{namespaces}"], {k: f"<{k}>" for k in KUBERNETES_OPERATOR_VALUES}
    else:
        v = _checked(policy, values)
        namespaces = v["namespaces"].split(",")
    docs = []
    for ns in namespaces:
        lines = [
            "apiVersion: rbac.authorization.k8s.io/v1",
            "kind: Role",
            "metadata:",
            f"  name: {json.dumps(v['ROLE_NAME'])}",
            f"  namespace: {json.dumps(ns)}",
            "rules:",
        ]
        for g, rule in zip(policy.grants, rules, strict=True):
            lines += [
                f"  # {g.id}: {g.reason}",
                f"  - apiGroups: {json.dumps(rule['apiGroups'])}",
                f"    resources: {json.dumps(rule['resources'])}",
                f"    verbs: {json.dumps(rule['verbs'])}",
            ]
        docs.append("\n".join(lines) + "\n")
        docs.append(
            "\n".join(
                [
                    "apiVersion: rbac.authorization.k8s.io/v1",
                    "kind: RoleBinding",
                    "metadata:",
                    f"  name: {json.dumps(v['ROLE_NAME'])}",
                    f"  namespace: {json.dumps(ns)}",
                    "subjects:",
                    "  - kind: ServiceAccount",
                    f"    name: {json.dumps(v['SERVICE_ACCOUNT'])}",
                    f"    namespace: {json.dumps(v['SERVICE_ACCOUNT_NAMESPACE'])}",
                    "roleRef:",
                    "  apiGroup: rbac.authorization.k8s.io",
                    "  kind: Role",
                    f"  name: {json.dumps(v['ROLE_NAME'])}",
                ]
            )
            + "\n"
        )
    return "---\n".join(docs)


RENDERERS = {"vault": ("hcl", render_vault), "kubernetes_rbac": ("yaml", render_kubernetes)}

# ------------------------------------------------------------------------------------------------ page


def copy_ready(policy: Policy) -> bool:
    """May this kind's text be offered for copying? Only when every grant's name and resource form were
    found in a vendor source (`verified` is set) and no grant carries an unverified claim."""
    return bool(policy.grants) and all(
        g.verified is not None and not g.claims_unverified for g in policy.grants
    )


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


# The two marks of a claim that nobody has checked against the vendor. Which claim gets which mark is written in
# the head of the sources file (the one place, read by `read_marks`), never in this tool.
MARK_BUILDER_READ = "builder read the passage"
MARK_NOBODY_READ = "nobody has read the passage"
_CLAIM_LINES = (
    ("CLAIM-READ-BY-BUILDER", MARK_BUILDER_READ),
    ("CLAIM-READ-BY-NOBODY", MARK_NOBODY_READ),
)
_CLAIM_SEPARATOR = " ;; "


@dataclass(frozen=True)
class Marks:
    """What the head of the sources file says about who read what, read once from one root.

    `builder_only`: sources only the builder of a fix has read. `partly_builder_only`: sources of which a passage
    behind a claim is marked on the page (the mark is in the claims cell of the same row). `builder_read` and
    `nobody_read`: the FULL texts of the claims (`claims_unverified`) that carry each mark; a claim matches only
    its exact full text, never its start."""

    builder_only: tuple[str, ...]
    partly_builder_only: tuple[str, ...]
    builder_read: tuple[str, ...]
    nobody_read: tuple[str, ...]

    def texts(self, mark: str) -> tuple[str, ...]:
        return self.builder_read if mark == MARK_BUILDER_READ else self.nobody_read


def _head_line(lines: list[str], tag: str) -> str:
    rows = [ln for ln in lines if ln.startswith(f"# {tag}:")]
    if len(rows) != 1:
        raise PolicyError(f"{SOURCES}: needs exactly one line starting `# {tag}:`")
    return rows[0].split(":", 1)[1]


def read_marks(root: Path) -> Marks:
    """The four lists of the head of the sources file (`# BUILDER-ONLY:`, `# PARTLY-BUILDER-ONLY:`,
    `# CLAIM-READ-BY-BUILDER:`, `# CLAIM-READ-BY-NOBODY:`), read from ONE place with ONE set of refusals (a
    missing or repeated line, an empty item, an id that is no row of the file, a claim text that holds `;;`, a
    text twice or under both marks). Nothing is read until this is called, so a malformed head is a problem the
    check reports, not a traceback at import. A test compares the id lines with the head's list of what a
    later evidence runner must re-read."""
    lines = head_lines(root)
    ids: dict[str, tuple[str, ...]] = {}
    for tag in ("BUILDER-ONLY", "PARTLY-BUILDER-ONLY"):
        found = tuple(x.strip() for x in _head_line(lines, tag).split(","))
        if not all(_SOURCE_ID.fullmatch(x) for x in found):
            raise PolicyError(f"{SOURCES}: the `# {tag}:` line must list source ids")
        ids[tag] = found
    known = set(_source_rows(lines))
    if unknown := sorted((set(ids["BUILDER-ONLY"]) | set(ids["PARTLY-BUILDER-ONLY"])) - known):
        raise PolicyError(f"{SOURCES}: builder-only id {unknown[0]} is not a row of the file")
    texts: dict[str, tuple[str, ...]] = {}
    for tag, mark in _CLAIM_LINES:
        found = tuple(x.strip() for x in _head_line(lines, tag).split(_CLAIM_SEPARATOR))
        if not all(found):
            raise PolicyError(f"{SOURCES}: the `# {tag}:` line holds an empty claim text")
        if any(";;" in x for x in found):
            raise PolicyError(
                f"{SOURCES}: the `# {tag}:` line holds `;;` inside a claim text (the separator is a space, "
                "two semicolons and a space)"
            )
        if len(set(found)) != len(found):
            raise PolicyError(f"{SOURCES}: the `# {tag}:` line holds a claim text twice")
        texts[mark] = found
    if both := sorted(set(texts[MARK_BUILDER_READ]) & set(texts[MARK_NOBODY_READ])):
        raise PolicyError(f"{SOURCES}: the claim text {both[0][:60]!r} is under both marks")
    return Marks(
        ids["BUILDER-ONLY"],
        ids["PARTLY-BUILDER-ONLY"],
        texts[MARK_BUILDER_READ],
        texts[MARK_NOBODY_READ],
    )


def claim_mark(text: str, marks: Marks | None = None) -> str:
    """The one mark of a claim text: `MARK_BUILDER_READ` or `MARK_NOBODY_READ`. The whole text must equal a
    listed text. A claim that equals no listed text, or texts of both marks, is refused (PolicyError): nothing is
    shown as read by default."""
    marks = read_marks(DATA_ROOT) if marks is None else marks
    found = [m for m in (MARK_BUILDER_READ, MARK_NOBODY_READ) if text in marks.texts(m)]
    if len(found) != 1:
        raise PolicyError(
            f"claim {text[:60]!r} has {len(found)} marks in the head of {SOURCES}, needs exactly one"
        )
    return found[0]


def claim_mark_problems(policies: dict[str, Policy], marks: Marks) -> list[str]:
    """Every claim has one mark by full-text equality; the builder-read mark stands only on an entry that names a
    source only the builder has read. The rule applies to EVERY claim of such an entry: an entry that names a
    builder-only source and has any claim needs one builder-read claim (a mark moved to a claim of an entry
    that names no such source is refused). Moving the mark between two claims of ONE such entry is not caught
    here: the mark must name the claim the builder really read, and only the pinned test catches that for R17.
    Every listed text belongs to a claim (a stale text is refused)."""
    out, used = [], set()
    for kind, label, e in entries(policies):
        got = []
        for claim in e.claims_unverified:
            try:
                got.append(claim_mark(claim, marks))
            except PolicyError as exc:
                out.append(f"{kind}: {exc}")
            used.add(claim)
        cited = sorted(set((e.verified or ())[1:]) & set(marks.builder_only))
        if MARK_BUILDER_READ in got and not cited:
            out.append(
                f"{kind} {label}: a claim is marked {MARK_BUILDER_READ!r}, but the entry names none of the "
                f"sources only the builder has read ({', '.join(marks.builder_only)}): the mark is on the wrong claim"
            )
        if e.claims_unverified and cited and MARK_BUILDER_READ not in got:
            out.append(
                f"{kind} {label}: names {', '.join(cited)}, which only the builder has read, but none of its "
                f"claims is marked {MARK_BUILDER_READ!r}"
            )
    if set(policies) != set(KIND_MODULES):
        return out  # a kind whose module could not be read is reported once, by its own problem
    return out + [
        f"{SOURCES}: the claim text {x!r} matches no claim: delete it"
        for x in sorted((set(marks.builder_read) | set(marks.nobody_read)) - used)
    ]


def _claim_text(claim: str, marks: Marks | None = None) -> str:
    return f"{claim} ({claim_mark(claim, marks)})"


def _checked_cell(
    verified: tuple[str, ...] | None, claim: bool = False, marks: Marks | None = None
) -> str:
    """`claim`: the entry carries an unchecked claim, so a source of which only a passage was read says that the
    passage behind the claim is shown in the claims text of the same entry."""
    if verified is None:
        return "not yet checked"
    marks = read_marks(DATA_ROOT) if marks is None else marks
    ids = ", ".join(
        s
        + (
            " (builder only)"
            if s in marks.builder_only
            else " (the passage behind the claim: see claims)"
            if claim and s in marks.partly_builder_only
            else ""
        )
        for s in verified[1:]
    )
    return f"{verified[0]}, sources {ids}"


# One class per note of a kind (and per note of a free request, written `free:<start of the note>`): `code` says
# what THIS code does; `sources` states something about the vendor's server or API and names the source ids that
# were read (the page prints them after the note); `claim` states something nobody has checked, as a fragment of
# a `claims_unverified` text. The class is a label a person chooses: the tests cannot know that a `sources`
# note is true, only that its ids exist and are printed.
NOTE_CLASSES: dict[tuple[str, str], tuple] = {
    ("secrets/vault", "Create the token or the sign-in role"): (
        "sources",
        ("V-TOK", "V-APPROLE", "V-K8S"),
    ),
    ("secrets/vault", "In the call column"): ("code",),
    ("signer/vault_transit", "The sign-in request of this kind"): ("code",),
    ("signer/vault_transit", "In the call column"): ("code",),
    ("signer/vault_transit", "Vault's sign path has"): (
        "claim",
        "the exact path R18 does not also allow",
    ),
    ("signer/vault_transit", "In plain words: Vault calls signing"): ("sources", ("V-TR", "B-TR")),
    ("signer/vault_transit", "The signer signs a test message"): ("code",),
    ("signer/vault_transit", "Create the token or the sign-in role"): (
        "sources",
        ("V-TOK", "V-APPROLE", "V-K8S"),
    ),
    ("source/kubernetes", "One Role and one RoleBinding"): ("code",),
    ("source/kubernetes", "At every start-up the kind asks"): ("code",),
    ("source/kubernetes", "The requests carry these query parameters"): (
        "claim",
        "do not change the verb",
    ),
    ("source/kubernetes", "free:a default cluster gives every"): (
        "sources",
        ("K-RBAC", "K-SRC", "K-SSRR"),
    ),
    # The `reason` of every grant, free request and never-list line, written out in full (a reason matches only
    # its exact text, so a reworded reason has no class until a person decides). Classes: `code` (what this
    # kind's code asks for, held by the call check); `sources` (a statement about the vendor, backed by the source
    # ids in `verified` of the SAME entry, at least one); `claim` (a fragment of a text of the entry's own
    # `claims_unverified`); `pending` (a statement about the vendor with no source yet: the entry's `verified`
    # is None and the page says "not yet checked").
    (
        "secrets/vault",
        "reason:reads one named secret; the right also covers every secret directly under the prefix; it may also cover every older version of each (not yet checked against the vendor, see the claims cell)",
    ): ("claim", "also serves a request for an older version"),
    (
        "secrets/vault",
        "reason:the sign-in request of auth `approle` and `kubernetes` carries no token; auth `token` sends no sign-in request",
    ): ("sources",),
    ("secrets/vault", "reason:the built-in policy that may do everything"): ("sources",),
    ("secrets/vault", "reason:the server's own settings: mounts, policies, audit devices"): (
        "sources",
    ),
    ("secrets/vault", "reason:the reader could replace, change or remove what it reads"): (
        "sources",
    ),
    ("secrets/vault", "reason:marks versions of a secret as deleted"): ("sources",),
    ("secrets/vault", "reason:brings deleted versions of a secret back"): ("pending",),
    (
        "secrets/vault",
        "reason:shows the field names inside secrets this kind was not asked to read",
    ): ("pending",),
    ("secrets/vault", "reason:lists every secret name and can delete every version of a secret"): (
        "sources",
    ),
    ("secrets/vault", "reason:removes versions of a secret for good"): ("sources",),
    ("signer/vault_transit", "reason:signs each audit checkpoint and the start-up test message"): (
        "code",
    ),
    ("signer/vault_transit", "reason:reads the pinned version's public key and the key type"): (
        "code",
    ),
    ("signer/vault_transit", "reason:the built-in policy that may do everything"): ("sources",),
    ("signer/vault_transit", "reason:the server's own settings: mounts, policies, audit devices"): (
        "sources",
    ),
    ("signer/vault_transit", "reason:deletes the key that signs the audit trail"): ("sources",),
    ("signer/vault_transit", "reason:can allow the key to be deleted or exported"): ("sources",),
    ("signer/vault_transit", "reason:copies the private key out"): ("sources",),
    ("signer/vault_transit", "reason:copies the private key out, wrapped for another system"): (
        "pending",
    ),
    (
        "signer/vault_transit",
        "reason:makes a new key version, so new signatures no longer match the pinned version",
    ): ("sources",),
    ("signer/vault_transit", "reason:removes old key versions for good"): ("sources",),
    ("signer/vault_transit", "reason:replaces a key with one from a backup"): ("sources",),
    ("signer/vault_transit", "reason:replaces the named key with one from a backup"): ("sources",),
    ("signer/vault_transit", "reason:copies the private key out as a backup"): ("sources",),
    ("source/kubernetes", "reason:reads deployments, their rollout revision and images"): ("code",),
    ("source/kubernetes", "reason:reads events in the time window"): ("code",),
    ("source/kubernetes", "reason:reads one pod's log lines"): ("code",),
    (
        "source/kubernetes",
        "reason:asks the cluster what this identity may do; the start-up check treats it as harmless (that it changes nothing in the cluster was not found in a vendor source)",
    ): ("claim", "changes nothing in the cluster"),
    ("source/kubernetes", "reason:a built-in role that may write"): ("pending",),
    (
        "source/kubernetes",
        "reason:a write verb: this source only reads. One exception, the same one the start-up check makes: `create` on the self-review resources (`selfsubjectrulesreviews`, `selfsubjectaccessreviews`, `selfsubjectreviews`), which the start-up check treats as harmless; that these three requests write nothing was not found in a vendor source",
    ): ("claim", "writes nothing"),
    ("source/kubernetes", "reason:a write verb: this source only reads"): ("sources",),
    ("source/kubernetes", "reason:lets the identity widen its own rights"): ("sources",),
    ("source/kubernetes", "reason:lets the identity act as another one"): ("sources",),
    ("source/kubernetes", "reason:opens a shell or a tunnel into a workload"): ("sources",),
    ("source/kubernetes", "reason:reading a secret reveals its value"): ("sources",),
}


def _class_keys(
    kind: str, text: str, classes: dict[tuple[str, str], tuple]
) -> list[tuple[str, str]]:
    """The keys of `classes` that name this note: a note by the start of its text, a reason (`reason:` and the
    full text) only by its exact text. A note never starts with `reason:`, so no `reason:` key can be the start of
    one and the second branch needs no test for it."""
    if text.startswith("reason:"):
        return [k for k in classes if k[0] == kind and k[1] == text]
    return [k for k in classes if k[0] == kind and text.startswith(k[1])]


def note_class(kind: str, text: str) -> tuple | None:
    """The one class of a note, or None when it has none (or more than one)."""
    keys = _class_keys(kind, text, NOTE_CLASSES)
    return NOTE_CLASSES[keys[0]] if len(keys) == 1 else None


def _note_items(policy: Policy) -> list[tuple[str, Grant | Free | Never | None]]:
    """(text, entry) for every note of a kind (entry None), every free-request note and every reason."""
    items: list[tuple[str, Grant | Free | Never | None]] = [(n, None) for n in policy.notes]
    items += [(f"free:{f.note}", f) for f in policy.free if f.note]
    items += [(f"reason:{e.reason}", e) for e in (*policy.grants, *policy.free, *policy.never)]
    return items


_CLASS_HOWS = ("code", "sources", "claim", "pending")


def _key_ok(key: object) -> bool:
    return isinstance(key, tuple) and len(key) == 2 and all(isinstance(x, str) for x in key)


def class_shape_problem(key: object, cls: object) -> str | None:
    """Why one `NOTE_CLASSES` entry has a shape no rule can read, or None. A key is (kind, start of the note); a class is a
    non-empty tuple whose first item is one of `_CLASS_HOWS`: `code` and `pending` stand alone, `claim` holds one
    non-empty text (a fragment of a claim), `sources` holds nothing (the ids are in `verified` of the entry) or a tuple
    of source ids (text)."""
    if not _key_ok(key):
        return "its key is not a tuple of two texts (kind, note)"
    if not isinstance(cls, tuple) or not cls:
        return "its class is not a non-empty tuple"
    how, *rest = cls
    if how not in _CLASS_HOWS:
        return f"its class {how!r} is not one of {', '.join(_CLASS_HOWS)}"
    if how in ("code", "pending") and rest:
        return f"its class {how} takes nothing after the name"
    if how == "claim" and not (len(rest) == 1 and isinstance(rest[0], str) and rest[0].strip()):
        return "its class claim needs exactly one non-empty text (a fragment of a claim)"
    if how == "sources" and not (
        not rest
        or (
            len(rest) == 1
            and isinstance(rest[0], tuple)
            and all(isinstance(x, str) for x in rest[0])
        )
    ):
        return "its class sources needs nothing or one tuple of source ids (texts)"
    return None


def readable_classes(classes: dict, out: list[str]) -> tuple[dict, set]:
    """(the entries whose KEY has the shape the matching code reads, the keys among them whose CLASS has no shape any
    rule can read). One problem line in `out` for every entry of either kind; neither kind makes a rule crash."""
    keyed, bad = {}, set()
    for key, cls in classes.items():
        if why := class_shape_problem(key, cls):
            out.append(f"NOTE_CLASSES entry {key!r}: {why}")
            if not _key_ok(key):
                continue
            bad.add(key)
        keyed[key] = cls
    return keyed, bad


def note_problems(
    policies: dict[str, Policy], classes: dict[tuple[str, str], tuple], known: set[str]
) -> list[str]:
    """The closed rule for every statement of fact: each note, free-request note and reason has exactly one class
    (see `NOTE_CLASSES`), the class is consistent with its entry (source ids exist and are in the entry's
    `verified`; a claim fragment is in the entry's own `claims_unverified`; `pending` only with no source), and
    no class entry is stale. `known`: the source ids of the sources file."""
    out, used = [], set()
    classes, shapeless = readable_classes(classes, out)
    for kind, policy in policies.items():
        kind_claims = " ".join(
            c for e in (*policy.grants, *policy.free, *policy.never) for c in e.claims_unverified
        )
        for text, entry in _note_items(policy):
            keys = _class_keys(kind, text, classes)
            if len(keys) != 1:
                out.append(
                    f"{kind}: note {text[:50]!r} has {len(keys)} classes in NOTE_CLASSES, needs one"
                )
                continue
            used.add(keys[0])
            if keys[0] in shapeless:
                continue  # reported once, by its own shape problem
            how, *rest = classes[keys[0]]
            claims = kind_claims if entry is None else " ".join(entry.claims_unverified)
            held = (entry.verified or ())[1:] if entry is not None else ()
            where = f"{kind}: note {text[:50]!r}"
            if how == "claim":
                if not rest or rest[0] not in claims:
                    out.append(f"{where} is a claim, but no claims_unverified holds {rest[:1]}")
            elif how == "sources" and rest:
                out += [
                    f"{where} names source {s}, which is not in the sources file"
                    for s in rest[0]
                    if s not in known
                ]
                if not rest[0]:
                    out.append(f"{where} is class sources with no source id")
                if entry is not None:
                    out += [
                        f"{where} names source {s}, which is not in `verified` of the same entry"
                        for s in rest[0]
                        if s not in held
                    ]
            elif how == "sources":
                # a reason: the sources are the ones in `verified` of its own entry
                if not held:
                    out.append(f"{where} is class sources, but its entry names no source")
                out += [
                    f"{where} names source {s}, which is not in the sources file"
                    for s in held
                    if s not in known
                ]
            elif how == "pending":
                if entry is None or entry.verified is not None:
                    out.append(f"{where} is class pending, but its entry has `verified` set")
            elif how != "code":
                out.append(f"{where} has an unknown class {how!r}")
    return out + [
        f"NOTE_CLASSES entry {k} matches no note: delete it"
        for k in sorted(set(classes) - used)
        if k[0]
        in policies  # a kind whose module could not be read is reported once, by its own problem
    ]


def _sources_suffix(kind: str, text: str, marks: Marks) -> str:
    cls = note_class(kind, text)
    if not cls or cls[0] != "sources" or len(cls) < 2:
        return ""
    ids = ", ".join(s + (" (builder only)" if s in marks.builder_only else "") for s in cls[1])
    return f" (sources: {ids})"


def _operation(op: tuple[str, ...]) -> str:
    return "`" + " ".join(op) + "`"


def _kind_section(kind: str, rel: str, policy: Policy, marks: Marks) -> list[str]:
    out = [f"## {kind.split('/')[1]} ({kind.split('/')[0]})", ""]
    if any("{path_prefix}" in g.resource for g in policy.grants):
        out += [WHOLE_MOUNT, ""]
    out += [f"Declared in `{rel}`.", ""]
    out += [f"- {note}{_sources_suffix(kind, note, marks)}" for note in policy.notes] + (
        [""] if policy.notes else []
    )
    out += [
        "| id | permission | on what | what limits a wildcard | the call it serves | why | when | name and form found in a vendor source | accepted by a real account | claims not checked |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for g in policy.grants:
        live = "no" if g.confirmed_live is None else ", ".join(g.confirmed_live)
        out.append(
            f"| {g.id} | `{g.name}` | `{_cell(g.resource)}` | {_cell(g.bound) or 'no wildcard'} | "
            f"{', '.join(_operation(op) for op in g.operations)} | {_cell(g.reason)} | "
            f"{_cell(g.applies_when) or 'always'} | {_checked_cell(g.verified, bool(g.claims_unverified), marks)} | {live} | "
            f"{_cell('; '.join(_claim_text(c, marks) for c in g.claims_unverified)) or 'none'} |"
        )
    out += ["", "Requests that need no permission:", ""]
    out += [
        f"- {', '.join(_operation(op) for op in f.operations)}: {f.reason}."
        + (f" Note: {f.note}{_sources_suffix(kind, 'free:' + f.note, marks)}." if f.note else "")
        + f" Checked: {_checked_cell(f.verified, bool(f.claims_unverified), marks)}."
        + (
            f" Claims not checked: {'; '.join(_claim_text(c, marks) for c in f.claims_unverified)}."
            if f.claims_unverified
            else ""
        )
        for f in policy.free
    ] or ["- none"]
    out += [
        "",
        "Never give this identity (each line would undo what the kind promises):",
        "",
        "| type | name | why | name found in a vendor source | claims not checked |",
        "|---|---|---|---|---|",
    ]
    for n in policy.never:
        caps = f" with {', '.join(n.capabilities)}" if n.capabilities else ""
        out.append(
            f"| {n.type} | `{_cell(n.name)}`{caps} | {_cell(n.reason)} | {_checked_cell(n.verified, bool(n.claims_unverified), marks)} | "
            f"{_cell('; '.join(_claim_text(c, marks) for c in n.claims_unverified)) or 'none'} |"
        )
    out += ["", f"Credential: {policy.how} Lifetime: {policy.lifetime}."]
    if policy.exception:
        out.append(f"Exception for the long-lived case: {policy.exception}")
    code, _, gap = COVERAGE[kind]
    out += [
        "",
        f"Tested: declared calls equal the calls written in the module: {code}. Engine: {engine_text(kind)}.",
        f"Not covered by any test: {gap}.",
        "",
    ]
    language, render = RENDERERS[policy.platform]
    if copy_ready(policy):
        out += [
            (
                "Copy-ready text (replace every `{setting}` with this deployment's setting and every `<NAME>` "
                "with your own name):"
            ),
            "",
            f"```{language}",
            render(policy).rstrip("\n"),
            "```",
            "",
        ]
    else:
        out += [
            (
                "No copy-ready text: at least one permission or claim of this kind is not yet checked against the "
                "vendor's own sources."
            ),
            "",
        ]
    return out


def head(marks: Marks | None = None) -> str:
    """The page head. The sentence about which claim carries which mark is built from the lists in the head of
    the sources file (the claim texts in full), never written here."""
    marks = read_marks(DATA_ROOT) if marks is None else marks

    def quoted(texts: tuple[str, ...]) -> str:
        return "; ".join(f'"{t}"' for t in texts)

    listed = (
        "Every claim on this page carries one of the two marks, shown after the claim. The claim texts with the "
        f"first mark ({len(marks.builder_read)}): {quoted(marks.builder_read)}. The claim texts with the second "
        f"mark ({len(marks.nobody_read)}; one text can stand on more than one permission): "
        f"{quoted(marks.nobody_read)}."
    )
    return _HEAD.replace("ENGINE_STATE", engine_state()).replace("CLAIM_MARKS_TEXT", listed)


_HEAD = f"""\
# Declared permissions per backend kind

Generated by `python tools/policy_page.py --write` from the `POLICY` literal in each kind module. Do not edit by
hand: a test regenerates this page and fails when it differs.

A "kind" is one backend choice (for example `vault`). For each kind below the page lists the permissions its
code needs (one reason each), the requests that need no permission, and what the identity must never be given.

## What the tests show, and what they do not

- Three backend kinds ship a declared permission set tied to the calls their code makes: `vault` (secrets),
  `vault_transit` (signer) and `kubernetes` (source). A test reads each module and fails when a request written
  there by the listed call shapes is not declared, or when a declared request is no longer made.
- For the two Vault kinds there are also tests that give the generated policy text to a real Vault server and
  check that it refuses the requests named per kind below. They run in CI only. ENGINE_STATE Until a run is
  on record, read every "refused" on this page as what those tests check, not as something already seen.
  Kubernetes is checked against the code's own read-only rule, not against a cluster.
- Those server tests run against one server image only: `{ENGINE_IMAGE}`, licence: {ENGINE_LICENCE}.
  The open alternative OpenBao (licence MPL-2.0) serves the same API by its own statement; it has not yet been
  run by these tests. Trigger to run them against OpenBao: a deployment chooses OpenBao, or the review date
  2026-12-11, whichever comes first (ledger row BL-core-q8c1-openbao).
- The test token holds the generated policy and nothing else. That does not represent sign-in through an
  AppRole or a Kubernetes role: there the role's own settings and the identity groups of the signed-in entity
  can add further policies, and the token then may do more than this page lists. Check the role.
- The call check is name-based. It sees requests written in the kind module in these shapes: `.call(...)`,
  `.authed(...)` and the Transit signer's `._call(...)` for Vault; `._fetch`, `._call`, `._get` and `._items`
  with a constant operation id for Kubernetes. Indirect ways to reach those calls (`getattr`, a new import, a
  raw HTTP call outside the one sending function, another module importing the Vault client) are refused by
  listed rules, not by proof: a way to send a request that no rule lists is not seen.
- Some permissions allow more than their reason says. Reading the reason alone would understate them: R17 reads
  every secret directly under the prefix (not only the one secret it names) and may also read every older version of each (not yet checked against the vendor, see the claims cell); R20 returns whole Deployment objects (including any setting
  values in them); R21 returns all events of a namespace, not a time window; R22 reads the log of every pod in a
  configured namespace. The "what limits a wildcard" cell of each says so and why the right cannot be narrower:
  Kubernetes rights cannot be limited by time or by a query, and a pod name list cannot be written in advance.
  What the code asks for is narrower than what the identity is allowed; the difference is in the cluster's or
  Vault's rules, not in this kind.
- A never-list line is compared with the grants of its own kind: a Vault path with each grant path by whether one
  concrete path fits both (a real overlap, including `+` and a last `*` on both sides and a `{{path_prefix}}` of any
  number of parts, the same number on both sides because the setting has one value in a deployment), a Kubernetes resource by name. Two limits: kinds are not compared with each other, because
  each kind has its own identity (a deployment that runs two Vault kinds on one mount name gets two identities);
  and the values of the settings are not known here, so `{{path_prefix}}` is taken as every value its pattern
  allows, but any other setting (the mount, the key name) is taken as one fixed word: a never line that writes
  a literal word where a grant has such a setting, for example `other/data/*` against `{{mount}}/data/...`, is
  not compared by value.
- No test shows that a permission NAME is right. That comes from a separate check of the vendor's own
  documentation and source files on the date shown per row (`tests/fixtures/policy_sources_2026-11-11.txt`
  lists them, each pinned to a commit id written in its URL). Seven of the rows (the Vault documentation)
  carry a 7-character abbreviated commit id, not the full 40 characters, and the OpenBao documentation rows
  sit at a commit whose OpenBao release was not looked up, so the OpenBao claims are not tied to one release.
  The rendered vendor pages were not reachable; the files they are built from were read.
- Some claims are weaker than that. They are statements about how the vendor's server or API behaves that
  nobody has checked against the vendor's own text. The page lists each under "claims not checked" and, for that
  reason, gives no copy-ready text for any of the three kinds. Each claim carries one of two marks, taken from
  the head of the sources file: "builder read the passage" (the builder of a fix read the vendor passage behind
  the claim; no evidence runner has re-read it) or "nobody has read the passage" (nobody has found a vendor
  passage for it). CLAIM_MARKS_TEXT A source id marked "(builder only)" was read by the builder of a fix only; one marked "(the
  passage behind the claim: see claims)" was read by an evidence runner for the permission name, while the
  passage behind the claim in that row has the mark shown in the claims cell. The same builder-only reading
  stands behind the never-list lines `undelete`, `subkeys` and `byok-export`; they show "not yet checked", as do
  the three Kubernetes role names `cluster-admin`, `admin` and `edit` (no evidence runner looked for those names
  in the Kubernetes source). Each of these has a dated entry in the tests (review by 2026-12-11) that turns the
  suite red if nobody re-reads it by then. The lists of marked ids and claims are read from the head of the
  sources file, not written in this tool.
- Two links the call check does not follow. First, the map from an object attribute to the setting it holds
  (`self.mount` holds the setting `mount`) is written by hand in the test; a test reads each `build` function
  and checks that the setting is stored in that attribute, but nothing follows the value beyond that. Second,
  the Kubernetes check that a namespace is one of the configured ones is found by a test only as a line of
  code, not by running it against a cluster. Inside the one sending function of the Vault client, a test pins
  the single request construction (address, path and verb) and the single send; it does not read the rest.
- When values are filled into the text, a value that names a reserved thing is refused, not warned about: a
  Vault mount whose first part is `sys`, `auth`, `identity` or `cubbyhole` (so `sysdata` is accepted); a namespace that starts with `kube-`;
  a role name `cluster-admin`, `admin`, `edit`, `view` or one that starts with `system`; the ServiceAccount
  `default`; the same namespace twice. A mount with a slash in it (a nested mount) is accepted. Length limits:
  63 characters for a namespace and 253 for the other Kubernetes names, from memory (not found in the pinned
  sources); 255 for the Vault values, this tool's own bound. The page itself is not filled in by a command:
  an operator who replaces the placeholders by hand gets none of these refusals.
- No policy on this page has been confirmed on a real account or a real cluster ("accepted by a real account"
  says `no` everywhere).
- One process uses one identity. Give that identity the text of every kind the process runs.
- How to read the tables. "permission": the right the identity is given (`read`, `update`, `list`, `get`).
  "on what": the path or resource that right covers; `+` stands for exactly one path part. "what limits a
  wildcard": how far a `+` or `*` reaches. "the call it serves": the request in the code that needs the right;
  `{{self.mount}}` and the like are settings, named in the notes of the kind. "name and form found in a vendor
  source": the date and the source ids (listed in the sources file) where the vendor's own text shows this
  name and spelling; "not yet checked" means no such reading was confirmed. "accepted by a real account":
  whether a real account took the permission; `no` everywhere. "claims not checked": statements in the row that
  nobody has checked against the vendor, each with the mark of who read the passage behind it.
- Vault calls signing `update` and calls reading `read`. For the signer (`vault_transit`) `update` stores
  nothing: it lets the identity ask for a signature, and no key or secret is changed. That is why "no write
  rights" and `update` do not contradict each other there.
- The Transit signer signs a test message at start-up, and verifying the audit trail builds the signer, so a
  process that only verifies still needs the signing permission today.
"""


def named_source_ids(kind: str, policy: Policy) -> set[str]:
    """Every source id the page prints for one kind: in a `verified` field or after a `sources` note."""
    ids = {s for e in (*policy.grants, *policy.free, *policy.never) for s in (e.verified or ())[1:]}
    for text in (*policy.notes, *(f"free:{f.note}" for f in policy.free if f.note)):
        cls = note_class(kind, text)
        if cls and cls[0] == "sources" and len(cls) > 1:
            ids |= set(cls[1])
    return ids


def page(root: Path | None = None) -> str:
    root = DATA_ROOT if root is None else root
    marks = read_marks(root)
    out = [head(marks)]
    named: set[str] = set()
    for kind, rel in KIND_MODULES.items():
        policy = load(root / rel)
        if policy is None:
            raise PolicyError(f"no POLICY in {rel}")
        out += _kind_section(kind, rel, policy, marks)
        named |= named_source_ids(kind, policy)
    sources = source_ids(root)
    if missing := sorted(named - set(sources)):
        raise PolicyError(f"the page names source {missing[0]}, which is not in the sources file")
    out += [
        "## Sources named on this page",
        "",
        (
            "Each id below is a row of `tests/fixtures/policy_sources_2026-11-11.txt` (the file lists the full "
            "link, the commit and a hash of the file for each):"
        ),
        "",
        *[
            f"- {sid}{' (builder only)' if sid in marks.builder_only else ''}: {sources[sid][3]} "
            f"(commit {sources[sid][1][:7]})"
            for sid in sorted(named)
        ],
        "",
    ]
    out += [
        "## Kinds with no declared policy yet",
        "",
        (
            f"These {len(NOT_YET_DECLARED)} kinds sign in to an outside system and have no declared permission "
            "set on this page. Nothing here may be read as covering them:"
        ),
        "",
        *[f"- `{k.split('/')[1]}` ({k.split('/')[0]})" for k in NOT_YET_DECLARED],
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    """Run `--write` or `--check`. `today` (default: the current UTC date) is for the tests: the dated lists
    are judged against it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help=f"write {PAGE}")
    mode.add_argument(
        "--check", action="store_true", help=f"fail when {PAGE} differs from the data"
    )
    args = parser.parse_args(argv)
    try:
        bad = data_problems(today=today)
        text = "" if bad else page()
    except (PolicyError, ValueError, OSError) as exc:
        bad = [f"{type(exc).__name__}: {exc}"]
    target = ROOT / PAGE
    try:
        if bad:
            pass  # nothing is written or compared while the data breaks a rule
        elif args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        elif not target.is_file() or target.read_text(encoding="utf-8") != text:
            bad = [f"{PAGE} differs from the data; run --write and commit"]
    except (OSError, UnicodeDecodeError) as exc:
        bad = [f"{PAGE}: {type(exc).__name__}"]
    for line in bad:
        print("policy page: " + " ".join(str(line).split()), file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
