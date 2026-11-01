"""Evals gate: run an agent's golden set, grade by exact field match, append a green run to qualified.jsonl.

An agent with no green run for its current (model id, prompt hash, config hash) cannot start.
With ``k > 1`` every item runs k times and green needs pass^k (items passing all k runs) at the threshold.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal

from hadavin_sdk.config import ConfigError, confined
from hadavin_sdk.guard import judge, runmap
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import GateRun
from hadavin_sdk.registry import Registry
from hadavin_sdk.runtime.evidence import with_evidence
from hadavin_sdk.stats import upper_error_bound

_ASK = "Process the attached request document."
QUALIFIED = "qualified.jsonl"


def matches(got: dict, expected: dict) -> bool:
    """Subset match (K5): the action is the expected one and every expected input has the expected value; extra
    optional inputs the model added are allowed. An abstention (action None) must be an abstention."""
    if got["action"] != expected["action"]:
        return False
    want = expected.get("inputs") or {}
    return all(k in got["inputs"] and got["inputs"][k] == v for k, v in want.items())


def gate(registry: Registry, llm: LLM, agent_id: str, *, k: int = 1) -> GateRun:
    if k < 1:
        raise ConfigError(f"gate k must be at least 1, got {k}")
    cfg = registry.config
    agent = registry.agents[agent_id]
    # The golden set, its documents and judge.jsonl, hashed before the run and again after it: a file that
    # changed while the run read it was not the set it qualifies on, so the run is never green.
    golden_before = registry.golden_sha256(agent_id)
    golden_path = confined(cfg.golden_dir, f"{agent_id}.jsonl")
    golden_bytes = golden_path.read_bytes()
    cases = [json.loads(line) for line in golden_bytes.decode("utf-8").splitlines() if line.strip()]
    # What the runtime offers: a tooled agent's action tools carry the required `evidence` field.
    tooled = bool(agent.tools_allowed)
    tools = [
        {
            "name": c.id,
            "description": c.description,
            "input_schema": with_evidence(c.input_schema) if tooled else c.input_schema,
        }
        for c in (registry.contracts[a] for a in agent.scope_allowed)
    ]
    passed = run_passes = abstains = 0
    cost = Decimal(0)
    for case in cases:
        # input_ref comes from a file: confined to inputs_dir (no "../" or absolute escapes).
        doc = confined(cfg.inputs_dir, case["input_ref"]).read_bytes()
        # The model sees what the runtime sends it: the document redacted with a fresh per-run map (K5).
        doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).encode("utf-8")
        case_passes = 0
        for _ in range(k):
            reply = llm.chat(
                [{"role": "user", "content": _ASK}],
                system=registry.prompt(agent_id),
                route=agent.model_route,
                tools=tools,
                documents=[doc],
            )
            cost += reply.cost_usd
            abstains += not reply.tool_calls
            # `evidence` (K5) is a citation the runtime strips before the plan exists: never graded.
            got = (
                {
                    "action": reply.tool_calls[0].name,
                    "inputs": {
                        k: v for k, v in reply.tool_calls[0].input.items() if k != "evidence"
                    },
                }
                if reply.tool_calls
                else {"action": None, "inputs": {}}
            )
            case_passes += matches(got, case["expected"])
        run_passes += case_passes
        passed += case_passes == k  # k == 1: passed; k > 1: passed all k runs
    n = len(cases)
    pairs = n * k
    rate = run_passes / pairs if n else 0.0  # pass@1
    pass_k = passed / n if n and k > 1 else None
    score = pass_k if pass_k is not None else rate
    # An llm_judge is qualified by its own golden set on the same model client, at its own rate (design 4.3):
    # the agent's passes never hide a judge's failures, and an empty judge set qualifies nothing.
    judges_green = True
    for d in cfg.backends.detector:
        if d.kind == "llm_judge":
            path = confined(cfg.golden_dir, "judge.jsonl")
            if not path.is_file():
                raise ConfigError("llm_judge needs its golden set: golden_dir/judge.jsonl")
            ok, total = judge.qualify(judge.JudgeDetector(llm, d.route, d.threshold), path)
            judges_green = judges_green and total > 0 and ok / total >= cfg.eval_threshold
    golden_after = registry.golden_sha256(agent_id)
    run = GateRun(
        agent_id=agent_id,
        model_id=cfg.routes[agent.model_route].model_id,
        prompt_sha256=registry.prompt_sha256(agent_id),
        config_hash=registry.config_hash(agent_id),
        golden_sha256=golden_after,
        n=n,
        passed=passed,
        pass_rate=rate,
        threshold=cfg.eval_threshold,
        # The judge set above runs once per gate call, not k times.
        green=n > 0
        and score >= cfg.eval_threshold
        and judges_green
        and golden_before == golden_after,
        k=k,
        pass_k=pass_k,
        abstain_rate=abstains / pairs if n else None,
        cost_per_task_usd=cost / pairs if n else None,
        upper_error_bound=upper_error_bound(n - passed, n),
    )
    if run.green:  # append-only log: one green run per line
        path = cfg.root / QUALIFIED
        torn = path.exists() and path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n")
        with open(path, "a", encoding="utf-8") as f:
            # A torn tail (disk full mid-append) is closed off, so the new record is its own whole line.
            f.write(("\n" if torn else "") + run.model_dump_json() + "\n")
            f.flush()
            os.fsync(f.fileno())
    return run
