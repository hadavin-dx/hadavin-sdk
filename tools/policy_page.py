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
* `python tools/policy_page.py --write` writes `docs/least-privilege-policies.md`; `--check` fails when the
  committed page differs from what the data gives.

What it does not do: it does not prove that a permission name is right, and it never contacts a server.
Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = "docs/least-privilege-policies.md"

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
# Per kind: what a test does, and what no test covers. Printed on the page as written here.
COVERAGE: dict[str, tuple[str, str, str]] = {
    "secrets/vault": (
        "yes",
        (
            "a real Vault server, in CI only: the generated policy text is given to a token that holds nothing "
            "else; the read works; with the grant removed the read is refused; a read outside the prefix, a "
            "write, the metadata and destroy paths and `sys/mounts` are refused"
        ),
        "OpenBao was never run; sign-in through AppRole or Kubernetes roles; a real deployment's own mounts",
    ),
    "signer/vault_transit": (
        "yes",
        (
            "a real Vault server, in CI only: signing and reading the public key work; with either grant removed "
            "that request is refused; signing with another key, changing the key's settings, exporting it, "
            "backing it up and deleting it are refused"
        ),
        "OpenBao was never run; sign-in through AppRole or Kubernetes roles",
    ),
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

PLATFORMS = ("vault", "kubernetes_rbac")
NEVER_TYPES = ("action", "role", "path", "resource", "prose")
VAULT_CAPABILITIES = ("create", "read", "update", "patch", "delete", "list")
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
_FREE = {"operations", "reason", "note", "verified"}
_NEVER = {"type", "name", "capabilities", "reason", "verified"}
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
WHOLE_MOUNT = (
    "Read first: the `path_prefix` setting is empty by default, and with an empty prefix this kind reads "
    "every secret in the mount. Set a prefix. No copy-ready text is produced for an empty prefix."
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


@dataclass(frozen=True)
class Never:
    type: str
    name: str
    capabilities: tuple[str, ...]
    reason: str
    verified: tuple[str, ...] | None


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


def _verified(where: str, value: object) -> list[str]:
    """None, or (date, source id, ...). A source id is a key of the sources file: never a URL or a host."""
    if value is None:
        return []
    if not isinstance(value, tuple) or not _texts(value) or len(value) < 2:
        return [f"{where}: verified must be None or (date, source id, ...)"]
    if not _DATE.fullmatch(value[0]):
        return [f"{where}: verified must start with a date such as 2026-11-11"]
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
    if ("*" in g["resource"] or "?" in g["resource"]) and not g["bound"].strip():
        out.append(
            f"{where}: resource {g['resource']!r} holds a wildcard, so `bound` must say what limits it"
        )
    if not g["reason"].strip():
        out.append(f"{where}: reason is empty")
    out += _verified(where, g["verified"])
    live = g["confirmed_live"]
    if live is not None and not (_texts(live) and len(live) == 2 and _DATE.fullmatch(live[0])):
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


def _never_problems(where: str, n: dict) -> list[str]:
    out = []
    if n["type"] not in NEVER_TYPES:
        out.append(f"{where}: unknown never type {n['type']!r}")
    if not _is_text(n["name"]) or not n["name"]:
        out.append(f"{where}: name must be non-empty text")
    if not _is_text(n["reason"]) or not n["reason"].strip():
        out.append(f"{where}: reason is empty")
    caps = n.get("capabilities", ())
    if not _texts(caps) or (caps and n["type"] != "path"):
        out.append(f"{where}: capabilities is a tuple of text, on a `path` entry only")
    return out + _verified(where, n["verified"])


def problems(raw: object) -> list[str]:
    """Every data-rule problem of one evaluated POLICY literal (empty: it may be used)."""
    out = _keys("POLICY", raw, _TOP, _TOP - {"notes"})
    if out or not isinstance(raw, dict):
        return out
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
        bad = _keys(where, f, _FREE, _FREE)
        if not bad:
            bad = _operations(where, f["operations"], platform) + _verified(where, f["verified"])
            if not (_is_text(f["reason"]) and f["reason"].strip() and _is_text(f["note"])):
                bad.append(f"{where}: reason must be non-empty text and note text")
        out += bad
    for i, n in enumerate(raw["never"]):
        where = f"never entry {i}"
        out += _keys(where, n, _NEVER, _NEVER - {"capabilities"}) or _never_problems(where, n)
    if not out:
        ids = [g["id"] for g in raw["grants"]]
        out += [f"grant id {i} is used twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
        seen = [g["resource"] for g in raw["grants"]]
        if platform == "vault":
            out += [
                f"resource {r!r} is on two grants: one Vault path takes one grant"
                for r in sorted({r for r in seen if seen.count(r) > 1})
            ]
    return out


def literal(text: str, where: str = "module") -> object | None:
    """The evaluated `POLICY` literal of one module's source text, or None when the module has none."""
    found = [
        node
        for node in ast.parse(text).body
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
    try:
        return ast.literal_eval(found[0].value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise PolicyError(
            f"{where}: POLICY is not a pure literal (a call, a name or an expression is never run)"
        ) from None


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
    return parse(Path(path).read_text(encoding="utf-8"), Path(path).name)


def load_all(root: Path = ROOT) -> dict[str, Policy | None]:
    return {kind: load(root / rel) for kind, rel in KIND_MODULES.items()}


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
    return out


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
        for part in parts:
            if not re.fullmatch(grammar, part) or {".", ".."} & set(part.split("/")):
                if key == "path_prefix" and part == "":
                    raise ValueError(
                        "policy value 'path_prefix' is empty: an empty prefix means the whole mount, and "
                        "no policy text is produced for that"
                    )
                raise ValueError(f"policy value {key!r} does not match its grammar: {part!r}")
    return values


def _fill(template: str, values: dict[str, str] | None) -> str:
    if values is None:
        return template
    filled = _FIELD.sub(lambda m: values[m.group(1)], template)
    return _OPERATOR.sub(lambda m: values[m.group(1)], filled)


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


def _checked_cell(verified: tuple[str, ...] | None) -> str:
    if verified is None:
        return "not yet checked"
    return f"{verified[0]}, sources {', '.join(verified[1:])}"


def _operation(op: tuple[str, ...]) -> str:
    return "`" + " ".join(op) + "`"


def _kind_section(kind: str, rel: str, policy: Policy) -> list[str]:
    out = [f"## {kind.split('/')[1]} ({kind.split('/')[0]})", ""]
    if any("{path_prefix}" in g.resource for g in policy.grants):
        out += [WHOLE_MOUNT, ""]
    out += [f"Declared in `{rel}`.", ""]
    out += [f"- {note}" for note in policy.notes] + ([""] if policy.notes else [])
    out += [
        "| id | permission | on what | what limits a wildcard | the call it serves | why | when | name and form found in a vendor source | accepted by a real account | claims not checked |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for g in policy.grants:
        live = "no" if g.confirmed_live is None else ", ".join(g.confirmed_live)
        out.append(
            f"| {g.id} | `{g.name}` | `{_cell(g.resource)}` | {_cell(g.bound) or 'no wildcard'} | "
            f"{', '.join(_operation(op) for op in g.operations)} | {_cell(g.reason)} | "
            f"{_cell(g.applies_when) or 'always'} | {_checked_cell(g.verified)} | {live} | "
            f"{_cell('; '.join(g.claims_unverified)) or 'none'} |"
        )
    out += ["", "Requests that need no permission:", ""]
    out += [
        f"- {', '.join(_operation(op) for op in f.operations)}: {f.reason}."
        + (f" Note: {f.note}." if f.note else "")
        + f" Checked: {_checked_cell(f.verified)}."
        for f in policy.free
    ] or ["- none"]
    out += [
        "",
        "Never give this identity (each line would undo what the kind promises):",
        "",
        "| type | name | why | name found in a vendor source |",
        "|---|---|---|---|",
    ]
    for n in policy.never:
        caps = f" with {', '.join(n.capabilities)}" if n.capabilities else ""
        out.append(
            f"| {n.type} | `{_cell(n.name)}`{caps} | {_cell(n.reason)} | {_checked_cell(n.verified)} |"
        )
    out += ["", f"Credential: {policy.how} Lifetime: {policy.lifetime}."]
    if policy.exception:
        out.append(f"Exception for the long-lived case: {policy.exception}")
    code, engine, gap = COVERAGE[kind]
    out += [
        "",
        f"Tested: declared calls equal the calls written in the module: {code}. Engine: {engine}.",
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
                "No copy-ready text: at least one permission of this kind is not yet checked against the "
                "vendor's own sources."
            ),
            "",
        ]
    return out


HEAD = """\
# Least-privilege policies per backend kind

Generated by `python tools/policy_page.py --write` from the `POLICY` literal in each kind module. Do not edit by
hand: a test regenerates this page and fails when it differs.

A "kind" is one backend choice (for example `vault`). For each kind below the page lists the permissions its
code needs (one reason each), the requests that need no permission, and what the identity must never be given.

## What the tests show, and what they do not

- Three backend kinds ship a declared permission set tied to the calls their code makes: `vault` (secrets),
  `vault_transit` (signer) and `kubernetes` (source). A test reads each module and fails when a request written
  there by the listed call shapes is not declared, or when a declared request is no longer made.
- The two Vault kinds are also refused by a real Vault server, in CI only: the generated policy text is the only
  thing the test token holds, and the requests on the never-list are refused. Kubernetes is checked against the
  code's own read-only rule, not against a cluster.
- The call check is name-based. It sees requests written in the kind module in these shapes: `.call(...)`,
  `.authed(...)` and the Transit signer's `._call(...)` for Vault; `._fetch`, `._call`, `._get` and `._items`
  with a constant operation id for Kubernetes. It does not see a client object handed to another module.
- No test shows that a permission NAME is right. That comes from a separate check of the vendor's own
  documentation sources on the date shown per row (`tests/fixtures/policy_sources_2026-11-11.txt` lists them).
  The rendered vendor pages were not reachable; the documentation source files they are built from were read.
- No policy on this page has been confirmed on a real account or a real cluster ("accepted by a real account"
  says `no` everywhere).
- One process uses one identity. Give that identity the text of every kind the process runs.
- The Transit signer signs a test message at start-up, and verifying the audit trail builds the signer, so a
  process that only verifies still needs the signing permission today.
"""


def page(root: Path = ROOT) -> str:
    out = [HEAD]
    for kind, rel in KIND_MODULES.items():
        policy = load(root / rel)
        if policy is None:
            raise PolicyError(f"no POLICY in {rel}")
        out += _kind_section(kind, rel, policy)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help=f"write {PAGE}")
    mode.add_argument(
        "--check", action="store_true", help=f"fail when {PAGE} differs from the data"
    )
    args = parser.parse_args(argv)
    try:
        text = page()
    except PolicyError as exc:
        print(f"policy page: {exc}", file=sys.stderr)
        return 1
    target = ROOT / PAGE
    if args.write:
        target.write_text(text, encoding="utf-8", newline="\n")
        return 0
    if not target.is_file() or target.read_text(encoding="utf-8") != text:
        print(f"policy page: {PAGE} differs from the data; run --write and commit", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
