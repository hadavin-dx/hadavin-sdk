"""Agent registry: loads agents, principals, chains and action contracts, and checks them together.

Every cross-file problem fails at start-up with ``ConfigError``.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import ExitStack
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hadavin_sdk import deferred
from hadavin_sdk.actions.contract import ActionContract, schema_problems
from hadavin_sdk.config import Config, ConfigError, Money, config_error_text, confined, load_yaml
from hadavin_sdk.errors import (
    digest_prefix,
    list_configured,
    loaded_ids,
    read_configured,
    shown_name,
)
from hadavin_sdk.guard.judge import PROMPT_SHA256 as JUDGE_PROMPT_SHA256
from hadavin_sdk.identity import Principal
from hadavin_sdk.models import ChainStep, sha256_hex
from hadavin_sdk.stages import is_live
from hadavin_sdk.tools import (
    ToolSpec,
    module_sha256,
    parse_manifest,
    read_operations,
    spec_problems,
)


class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    daily: Money
    monthly: Money


class AgentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    status: Literal["draft", "live", "retired"]
    data_class: Literal["public", "internal", "confidential", "restricted"]
    model_route: str
    prompt_file: str
    scope_allowed: list[str]
    tools_allowed: list[str] = []
    max_steps: int = Field(gt=0)
    budget_usd: Budget
    # Per-action autonomy. None only in demo (the slice-1 gate path). Not part of config_hash: promotion changes
    # only this, so a flip never un-qualifies the agent. `act` parses so the load check can name its phase.
    levels: dict[str, Literal["shadow", "suggest", "act"]] | None = None
    max_run_usd: Money | None = (
        None  # per-run cost cap; required in pilot and prod (enforced in K5)
    )


class Chain(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    steps: list[ChainStep]


@dataclass(frozen=True)
class Registry:
    config: Config
    agents: dict[str, AgentRecord]
    principals: dict[str, Principal]
    chains: dict[str, Chain]
    contracts: dict[str, ActionContract]
    # agent id -> tool name -> manifest entry (`tools/<agent>.yaml`, K5). An agent with tools_allowed and no
    # manifest uses the callables handed to `app.build(tools=...)` (replay and tests).
    tools: dict[str, dict[str, ToolSpec]] = dc_field(default_factory=dict)

    def _prompt_path(self, agent_id: str):
        return confined(self.config.root, self.agents[agent_id].prompt_file)

    def prompt(self, agent_id: str) -> str:
        return read_configured(self._prompt_path(agent_id), "an agent's prompt_file")

    def prompt_sha256(self, agent_id: str) -> str:
        data = read_configured(self._prompt_path(agent_id), "an agent's prompt_file", binary=True)
        return hashlib.sha256(data).hexdigest()

    def golden_path(self, agent_id: str):
        return confined(self.config.golden_dir, f"{agent_id}.jsonl")

    def golden_sha256(self, agent_id: str) -> str:
        data = read_configured(
            self.golden_path(agent_id),
            "a golden set file (golden_dir)",
            binary=True,
            missing_ok=True,
        )
        if data is None:
            return ""
        # The documents the cases point at decide pass/fail too: a changed input un-qualifies. A bad line or
        # a missing document is left to the gate and the start-up check (`_check_golden_refs`).
        for line in data.decode("utf-8", "replace").splitlines():
            try:
                ref = confined(self.config.inputs_dir, json.loads(line)["input_ref"])
            except (ValueError, KeyError, TypeError, ConfigError):
                continue
            doc = read_configured(
                ref, "a golden input document (inputs_dir)", binary=True, missing_ok=True
            )
            data += b"\0" + (doc or b"")
        if any(d.kind == "llm_judge" for d in self.config.backends.detector):
            judge = read_configured(
                self.config.golden_dir / "judge.jsonl",
                "judge.jsonl (golden_dir)",
                binary=True,
                missing_ok=True,
            )
            if judge is not None:
                data += b"\0" + judge  # a weakened judge set un-qualifies too
        return hashlib.sha256(data).hexdigest()

    def config_hash(self, agent_id: str) -> str:
        """What the agent was qualified on. `exclude_defaults`: from this version on, adding an optional field
        with a default never un-qualifies existing agents. The llm backend kind is included, so a backend swap
        with the same model id needs a new gate run.

        Upgrade note (slice 2 P1a): this version changes the hash itself, so every agent needs ONE new gate run
        (`hadavin-sdk gate <agent>`) before the runtime starts it again; see CHANGELOG.md."""
        agent = self.agents[agent_id]
        llm = self.config.backends.llm

        def dump(model) -> dict:
            return model.model_dump(
                mode="json", exclude_defaults=True, exclude={"levels"} if model is agent else None
            )

        # An llm_judge screens this agent's input: its prompt, route and threshold are qualified too.
        judges = [
            {
                "prompt_sha256": JUDGE_PROMPT_SHA256,
                "route": dump(self.config.routes[d.route]),
                "threshold": str(d.threshold),  # canonical_json refuses floats
            }
            for d in self.config.backends.detector
            if d.kind == "llm_judge"
        ]

        return sha256_hex(
            {
                "agent": dump(agent),
                "route": dump(self.config.routes[agent.model_route]),
                "actions": [dump(self.contracts[a]) for a in sorted(agent.scope_allowed)],
                "llm_backend": llm.kind,
                # Where and how the model runs (design 4.3); keys only when set, so `fake` agents keep their hash.
                **{
                    f"llm_{k}": getattr(llm, k)
                    for k in (
                        "platform",
                        "base_url",
                        "resource",
                        "region",
                        "project_id",
                        "max_completion_tokens",
                    )
                    if getattr(llm, k, None)
                },
                **({"judges": judges} if judges else {}),
                # A re-pinned tool module is different code: the agent needs a new qualification.
                **(
                    {"tool_pins": dict(sorted(pins.items()))}
                    if (pins := self.config.tool_module_hashes)
                    else {}
                ),
                # The read tools the agent investigates with (K5): a changed tool needs a new qualification.
                # Only when a manifest exists, so agents without one keep their hash.
                **(
                    {"tools": [dump(t) for _, t in sorted(self.tools[agent_id].items())]}
                    if self.tools.get(agent_id)
                    else {}
                ),
                # The bar the gate run passed: raising it must not leave an old green run standing. Only when not
                # the default 1.0, so agents gated at the default keep their hash.
                **(
                    {"eval_threshold": str(self.config.eval_threshold)}
                    if self.config.eval_threshold < 1.0  # at most 1.0 (config); no float equality
                    else {}
                ),
            }
        )

    def tools_for(self, agent_id: str, available: set[str]) -> list[str]:
        """Non-action tools the loop may offer: only those listed. Empty list means none."""
        return sorted(set(self.agents[agent_id].tools_allowed) & available)


def _yaml(path, what: str) -> object:
    """One YAML file of the configuration folder, or None if it is not there (not: "there but cannot be read": a
    folder, a loop of links, no permission, not UTF-8 text is `ConfigError`, never an empty file). Every read of such a
    file goes through here: `what` is a fixed label written in code, a YAML error leaves `load_yaml` as a value-free
    `ConfigError`."""
    text = read_configured(path, what, missing_ok=True)
    if text is None:
        return None
    try:
        return load_yaml(text)
    except ConfigError:
        raise
    except (ValueError, TypeError) as exc:
        raise ConfigError(config_error_text(exc)) from None


def _by_id(items: list, model: type, where: str) -> dict:
    """Validated entries keyed by id; a duplicate id fails (a later entry must never shadow an earlier one)."""
    out: dict = {}
    for number, raw in enumerate(items or [], start=1):
        if not isinstance(raw, dict):
            raise ConfigError(f"{where}: entry {number} is not a mapping")
        obj = model(**raw)
        if obj.id in out:
            raise ConfigError(f"{where}: duplicate id in entry {number}")
        out[obj.id] = obj
    return out


def _nested_identifier(sub: dict[str, Any]) -> bool:
    """True if `identifier` appears anywhere inside this input's schema other than as its own top-level flag."""

    def walk(node: Any) -> bool:
        if isinstance(node, dict):
            return isinstance(node.get("identifier"), bool) or any(walk(v) for v in node.values())
        if isinstance(node, list):
            return any(walk(v) for v in node)
        return False

    return any(walk(v) for k, v in sub.items() if k != "identifier")


def load_registry(config: Config) -> Registry:
    root = config.root
    try:
        raw_agents = _yaml(root / "agents.yaml", "agents.yaml")
        raw_actions = [
            _yaml(p, "a file in actions/")
            for p in list_configured(root / "actions", "the actions/ folder", ".yaml")
        ]
    except ConfigError:
        raise
    except yaml.YAMLError as exc:
        raise ConfigError(config_error_text(exc)) from None
    if early := [
        *(p for a in raw_agents or [] for p in deferred.key_problems("agents.yaml", a)),
        *(p for a in raw_actions for p in deferred.key_problems("actions/", a)),
    ]:
        raise ConfigError("; ".join(early))
    try:
        agents = _by_id(raw_agents, AgentRecord, "agents.yaml")
        principals = _by_id(
            _yaml(root / "principals.yaml", "principals.yaml"), Principal, "principals.yaml"
        )
        chains = _by_id(_yaml(root / "chains.yaml", "chains.yaml"), Chain, "chains.yaml")
        contracts = _by_id(raw_actions, ActionContract, "actions/")
    except ConfigError:
        raise
    except (ValidationError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ConfigError(config_error_text(exc)) from None
    # Names shown in an error text: the ids this loader has read (D-2322); a reference that matched nothing is not one.
    with loaded_ids(
        agents,
        principals,
        chains,
        contracts,
        config.routes,
        config.systems,
        config.sources,
        config.tool_modules,
        *(_input_names(c) for c in contracts.values()),
    ):
        problems = _cross_check(config, agents, chains, contracts) + _principal_problems(
            principals, chains, contracts
        )
        if problems:
            raise ConfigError("; ".join(problems))
        tools = _load_tools(config, agents, contracts)
        reg = Registry(config, agents, principals, chains, contracts, tools)
        if problems := deferred.check(reg):
            raise ConfigError("; ".join(problems))
        return reg


def _input_names(contract: ActionContract) -> list[str]:
    """The names of an action's declared inputs: defined in its own file, so they are loaded names."""
    return [
        n for n in ((contract.input_schema or {}).get("properties") or {}) if isinstance(n, str)
    ]


def _load_tools(config: Config, agents: dict, contracts: dict) -> dict[str, dict[str, ToolSpec]]:
    """Read `tools/<agent>.yaml` for every agent and check each entry (K5). Every problem fails at start-up."""
    # Pins first, and fatal at once: nothing below may import a tool module that is unpinned or does not match.
    if pin_problems := _module_pin_problems(config):
        raise ConfigError("; ".join(pin_problems))
    folder = config.root / "tools"
    problems: list[str] = []
    found: dict[str, dict[str, ToolSpec]] = {}
    if folder.is_dir():
        orphans = [
            p for p in list_configured(folder, "the tools/ folder", ".yaml") if p.stem not in agents
        ]
        if orphans:  # a file name is a value from the folder: counted, never quoted
            problems.append(f"tools/: {len(orphans)} manifest file(s) match no agent id")
    read_ops: set[str] | None = None
    with ExitStack() as stack:
        for agent_id, agent in agents.items():
            path = folder / f"{agent_id}.yaml"
            where = f"tools/{shown_name(agent_id)}.yaml"
            raw_manifest = _yaml(path, f"{where} (an agent's tool manifest)")
            if (
                raw_manifest is None
            ):  # no such file (a folder or an unreadable file is already a ConfigError above)
                continue
            specs = parse_manifest(raw_manifest, where)
            stack.enter_context(
                loaded_ids(sp.name for sp in specs)
            )  # the manifest's own tool names
            if specs and read_ops is None:
                read_ops = read_operations(config.tool_modules, config.tool_module_hashes)
            found[agent_id] = {}
            # With a manifest the manifest is the whole list of tools: an entry of `tools_allowed` with no tool in it would
            # silently never be offered (a typo that narrows the agent). Named by position, never quoted.
            # An empty manifest names no tool and so never narrows `tools_allowed` (checked only `if specs`).
            problems += [
                f"{where}: tools_allowed entry {i} has no tool in this manifest"
                for i, allowed in enumerate(agent.tools_allowed)
                if specs and allowed not in {sp.name for sp in specs}
            ]
            problems += [  # grounding checks declared inputs only, so a tooled agent's contracts must be closed
                f"{where}: action {shown_name(action)} must set `additionalProperties: false` on its input_schema "
                "(an agent with tools cannot have undeclared inputs)"
                for action in agent.scope_allowed
                if action in contracts
                and (contracts[action].input_schema or {}).get("additionalProperties") is not False
            ]
            for spec in specs:
                found[agent_id][spec.name] = spec
                problems += [
                    f"{where}: {p}"
                    for p in spec_problems(
                        spec, config.tool_modules, config.evidence.cluster_suffixes
                    )
                ]
                problems += [
                    f"{where}: tool {shown_name(spec.name)}: {p}"
                    for p in schema_problems(spec.input_schema)
                ]
                if spec.ca_file and (why := _ca_problem(config, spec.ca_file)):
                    problems.append(f"{where}: tool {shown_name(spec.name)}: {why}")
                if spec.name not in agent.tools_allowed:
                    problems.append(
                        f"{where}: tool {shown_name(spec.name)} is not in the agent's tools_allowed"
                    )
                for (
                    action
                ) in agent.scope_allowed:  # every string input says whether it must be grounded
                    if action not in contracts:
                        continue  # reported where the agent's scope is checked
                    props = (contracts[action].input_schema or {}).get("properties") or {}
                    # Grounding is a string match. A string input says true or false; any other kind of input
                    # (integer, array, object) cannot be grounded, so it must say `identifier: false` outright
                    # instead of silently skipping the check; a boolean carries no name to ground.
                    problems += [
                        f"{where}: action {shown_name(action)} input {shown_name(pname)} must say `identifier: true` or `identifier: false`"
                        for pname, sub in props.items()
                        if isinstance(sub, dict)
                        and sub.get("type") != "boolean"
                        and "identifier" not in sub
                    ]
                if spec.name in contracts:
                    problems.append(
                        f"{where}: tool {shown_name(spec.name)} has the id of an action contract"
                    )
                problems += [
                    f"{where}: tool {shown_name(spec.name)}: operations entry {i} is not on the read list of tool_modules"
                    for i, op in enumerate(spec.operations)
                    if op not in (read_ops or set())
                ]
                problems += [  # a POST read (a review, a query body) is named in the config, not only in tool code
                    f"{where}: tool {shown_name(spec.name)}: operations entry {i} is bound to {read_ops[op][0]}; "
                    "list it in evidence.post_read_operations to allow it"
                    for i, op in enumerate(spec.operations)
                    if read_ops
                    and op in read_ops
                    and read_ops[op][0] != "GET"
                    and op not in config.evidence.post_read_operations
                ]
    if problems:
        raise ConfigError("; ".join(problems))
    return found


def _module_pin_problems(config: Config) -> list[str]:
    """Tool modules are code with the process's rights: in pilot and prod each one is pinned by the SHA-256 of
    its source file (`tool_module_hashes`), and a pin that is listed must match."""
    out = []
    for module in config.tool_modules:
        pin = config.tool_module_hashes.get(module)
        if pin is None:
            if is_live(config.environment):
                out.append(
                    f"tool module {shown_name(module)} has no tool_module_hashes pin (required in pilot and prod)"
                )
            continue
        try:
            actual = module_sha256(module)  # reads files, imports nothing
        except ConfigError as exc:
            out.append(str(exc))
            continue
        if actual != pin:
            out.append(
                f"tool module {shown_name(module)}: its source hash is {digest_prefix(actual)}, the pin says {digest_prefix(pin)}"
            )
    return out


def _principal_problems(principals: dict, chains: dict, contracts: dict) -> list[str]:
    """Every reference in `principals.yaml` and `chains.yaml` must name something that exists. Each of these would
    otherwise be a typo that no one sees at load: a right that names no action (that principal is refused, silently),
    an `approver_of` that names no chain, an approver who is not a person (nobody could approve, or a service
    identity would be one). A value is named by its position, never quoted."""
    out = []
    for p in principals.values():
        name = shown_name(p.id)
        out += [
            f"principal {name}: rights entry {i} names no action"
            for i, right in enumerate(p.rights)
            if right not in contracts
        ]
        out += [
            f"principal {name}: approver_of entry {i} names no chain"
            for i, chain in enumerate(p.approver_of)
            if chain not in chains
        ]
    # A chain that some principal names in `approver_of` is linked to people: its approver_ids must be persons. A chain no
    # principal names keeps channel-native approver ids (for example a Slack user id): they are checked by the channel
    # and the decision, never by principals.yaml (the behaviour before this change).
    linked = {chain for p in principals.values() for chain in p.approver_of}
    for c in chains.values():
        if c.id not in linked:
            continue
        for i, step in enumerate(c.steps):
            out += [
                f"chain {shown_name(c.id)} step {i}: approver_ids entry {j} is not a person in principals.yaml"
                for j, who in enumerate(step.approver_ids)
                if who not in principals or principals[who].kind != "person"
            ]
    return out


def _is_config_file(config: Config, relative: str) -> bool:
    """True if `relative` is a file under the configuration folder; a name too long for the file system is the same
    refusal as one that escapes (ConfigError), never a bare OSError."""
    path = confined(config.root, relative)
    try:
        return path.is_file()
    except (OSError, ValueError):
        raise ConfigError("path cannot be resolved") from None


def _ca_problem(config: Config, ca_file: object) -> str | None:
    """None if `ca_file` is a file under the configuration folder, else a fixed sentence (the same rule as an agent's
    `prompt_file`): found at load, so a missing or oversized path never reaches a file open at build time."""
    try:
        if not _is_config_file(config, str(ca_file)):
            return "ca_file is not a file in the config folder"
    except ConfigError:
        return "ca_file escapes the config folder or cannot be resolved"
    return None


def _cross_check(config, agents, chains, contracts) -> list[str]:
    out = []
    for name, source in config.sources.items():
        if source.ca_file is not None and (why := _ca_problem(config, source.ca_file)):
            out.append(f"source {shown_name(name)}: {why}")
    for a in agents.values():
        if a.model_route not in config.routes:
            out.append(f"agent {shown_name(a.id)}: model_route is not one of the configured routes")
        out += [  # a value that matched nothing may be a pasted secret: named by its position, never quoted
            f"agent {shown_name(a.id)}: scope_allowed entry {i} has no contract"
            for i, x in enumerate(a.scope_allowed)
            if x not in contracts
        ]
        try:
            if not _is_config_file(config, a.prompt_file):
                out.append(f"agent {shown_name(a.id)}: prompt_file missing")
        except ConfigError:
            out.append(f"agent {shown_name(a.id)}: prompt_file escapes the config folder")
    for c in chains.values():
        if not c.steps:
            out.append(f"chain {shown_name(c.id)}: no steps")
        for i, s in enumerate(c.steps):
            if not s.approver_ids or s.timeout_s <= 0:
                out.append(f"chain {shown_name(c.id)} step {i}: needs approvers and timeout_s > 0")
    for c in contracts.values():
        out += [f"action {shown_name(c.id)}: {p}" for p in schema_problems(c.input_schema)]
        props = (c.input_schema or {}).get("properties") or {}
        if "key" in props:
            out.append(
                f"action {shown_name(c.id)}: input 'key' is reserved for the idempotency key"
            )
        # Grounding reads the TOP-LEVEL inputs only (evidence.identifier_inputs): an `identifier` flag deeper in an
        # object or array would be silently ignored, for every agent, tooled or not. Refused (flag the top-level
        # input, or say `identifier: false` on it). Fail closed: any boolean `identifier` below the top level counts.
        out += [
            f"action {shown_name(c.id)}: input {shown_name(n)} has an `identifier` flag below the top level, which grounding does not read"
            for n, sub in props.items()
            if isinstance(sub, dict) and _nested_identifier(sub)
        ]
        http = c.executor if c.executor.kind == "http" else None
        for op in filter(None, [http and http.operation, http and http.lookup_operation]):
            for field in re.findall(r"{(\w+)}", op):
                if field != "key" and "pattern" not in props.get(field, {}):
                    out.append(
                        f"action {shown_name(c.id)}: path field {shown_name(field)} needs a pattern in input_schema"
                    )
        if c.chain_id is not None and c.chain_id not in chains:
            out.append(f"action {shown_name(c.id)}: chain_id names no chain")
        for field_name in ("verify_check", "rollback"):
            ref = getattr(c, field_name)
            if ref and (":" not in ref or ref.split(":", 1)[0] not in config.check_modules):
                out.append(f"action {shown_name(c.id)}: {field_name} is outside check_modules")
        if http is not None and c.target_system not in config.systems:
            out.append(f"action {shown_name(c.id)}: target_system names no configured system")
    return out
