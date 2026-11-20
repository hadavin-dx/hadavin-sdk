"""The n8n outline files: what can be checked without an n8n.

An earlier version of the two workflow files was run in n8n 2.47.7 by the lead (the record is
handover/core-a/inputs/lead-evidence-n8n-1.md). The files were then changed to follow that record and
were not imported again. These tests pin what the record showed must hold: Set nodes on 3.4, a webhookId,
the signing value in a credential and nowhere else, the status read from error.status, Retry On Fail off,
the guard before the hash node and the sign node, a 502, 503, 504 or missing status leading through a Wait
back to a new timestamp and a new signature, and 400, 401, 409, 413 stopping at once.
They also pin the state check that was added after the run: a 202 or 200 answer is not the end of the workflow;
it asks again, signed anew, until the state says how the run ended, and the state names it sorts by are
loaded from the code.
They tie the signing recipe as the sign node and the README word it to ``hmac_v0``, and they list the
nodes that still hold something nobody has seen working. They do not show that n8n accepts the files.
The fake secret is built from parts.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.backends import table
from hadavin_sdk.models import OPEN_STATES, RunState
from hadavin_sdk.runtime import runs, tick
from hadavin_sdk.triggers import endpoint, worker
from tests.test_no_hardcoded_values import PATTERNS

N8N = Path(__file__).resolve().parents[2] / "n8n"
MAIN, ERROR, README = "hadavin-trigger.json", "hadavin-trigger-error.json", "README-trigger.md"
PREFIX = "n8n-nodes-base."
EVIDENCE = "handover/core-a/inputs/lead-evidence-n8n-1.md"
SEEN = "SEEN IN n8n 2.47.7:"
OPEN = "UNVERIFIED:"
NOT_REIMPORTED = "this version not re-imported"
WEBHOOK_ID = (
    "00000000-0000-4000-8000-000000000000"  # the made-up placeholder, replaced per installation
)
SET_VERSION = 3.4  # with 3, n8n 2.47.7 ignored "assignments" and reported no error
# Field names that would hold a typed-in secret, and texts that would read one from outside a credential.
SECRET_FIELDS = ("secret", "password", "passphrase", "token", "apikey", "privatekey")
SECRET_READS = ("$env", "$vars", "$secrets", "createHmac", "require(")
# The nodes whose note still names something nobody has seen working. Change this list with the notes.
OPEN_NODES = {
    MAIN: {
        "Trigger placeholder",
        "Answer caller: refused",
        "Stop: id or text missing",
        "Answer caller: taken",
        "Sign",
        "Send to Hadavin",
        "Busy and rounds left?",
        "Next round",
        "Wait before next round",
        "Stop: refused or gave up",
        "Run still going?",
        "Checks left?",
        "Next check",
        "Run ended well?",
        "Done: finished or waits for approval",
        "Stop: run did not end well",
        "Stop: still running",
    },
    ERROR: set(),
}
# What nobody has run, as the README's status part must name it.
NOT_RUN = (
    "These two files as they stand now",
    "INSIDE the full chain",
    'The two "Answer caller" nodes',
    "A manual retry of a failed execution from the n8n editor",
    "30 rounds with 60 second waits",
    "The state check after a 202 or 200 answer",
    "The real Hadavin endpoint (a stub answered)",
    "One webhook call that starts two executions",
    "n8n Cloud and queue mode",
    "n8n versions other than 2.47.7",
    "A receiver that answers 502 or 504, and a receiver that gives no answer",
)
# The busy condition, as the node must hold it: where the status is read, the statuses that mean "try again",
# and the test that counts a missing status (no HTTP answer at all) as "try again" too.
STATUS_READ = "String($json.error?.status ?? '')"
BUSY = ("502", "503", "504")
STOPS = ("400", "401", "409", "413")  # never tried again
BUSY_EXPRESSION = (
    "={{ (['502', '503', '504'].includes("
    + STATUS_READ
    + ") || !/^[1-5][0-9][0-9]$/.test("
    + STATUS_READ
    + ")) && $('Stamp time').last().json.round < 30 }}"
)
MEANING_OF_503 = "not acknowledged; send again with the same key; it may already be running"
# What the run measured for n8n's own Retry On Fail, as the README must state it.
RETRY_FACTS = (
    "3 requests, about 1 and 2 seconds apart",
    "n8n sent 5 requests, about 5 seconds apart",
    "capped at 5",
    "capped at about 5 seconds",
    "Every retry reused the same timestamp and the same signature",
    "It can never outlast a run",
    "Only the loop above can",
)
FAKE_SECRET = "fake" + "-trigger-value" * 2  # 32 characters, built from parts, never a real one
FIXED_TS = 1_800_000_000
FIXED_BODY = json.dumps({"key": "ab" * 32, "document": 'line "one"\nzwei ä'}, ensure_ascii=False)

# One phrase for each item of the README's verify list, in order.
VERIFY_ITEMS = (
    "these two files as they stand now import without error",
    "typeVersion 2 with the credential inside the full chain",
    "placeholder credential id",
    'the two "Answer caller" nodes',
    "placeholder `webhookId`",
    "reads `error.status` only",
    "runs the sign node again",
    "30 rounds with 60 second waits",
    "the real Hadavin endpoint",
    "two executions still yields one run",
    "n8n Cloud, queue mode",
    "n8n versions other than 2.47.7",
    "HTTP Request timeout timed live",
    "no answer at all",
    "editor menu for importing a file",
    "larger than 300 KB",
    "one exception to",
    "an answer 502 or 504 goes the busy way",
    "the state check after a 202 or 200",
    "the gap itself, against a real worker and a real tick",
)
# The state check. How the workflow sorts the state of an answer, taken from the code so that a renamed or a new
# state fails here: "still going" = the states the tick's stuck step ends when a run stops moving; "success" = the
# three named here; "error" = every other state a run can end in.
STATE_READ = "String($json.state ?? '')"
CHECKS_READ = "($('Stamp time').last().json.checks ?? 0)"
GOING = frozenset(tick.STUCK)
SUCCESS = frozenset({RunState.NO_ACTION, RunState.SUCCEEDED, RunState.WAITING_FOR_APPROVAL})
ENDED_BADLY = frozenset(runs.FINAL) - SUCCESS
EXAMPLE_STEPS = (
    12  # the README's worked example: an agent with max_steps 12 on the default model settings
)


def _load(name: str) -> dict[str, Any]:
    return json.loads((N8N / name).read_text(encoding="utf-8"))


def _readme() -> str:
    return (N8N / README).read_text(encoding="utf-8")


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in [k, *_strings(v)]]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def _nodes(flow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["name"]: node for node in flow["nodes"]}


def _edges(flow: dict[str, Any]) -> dict[str, list[str]]:
    """Node name -> the names it leads to, over every output."""
    return {
        source: [link["node"] for outputs in kinds.values() for links in outputs for link in links]
        for source, kinds in flow["connections"].items()
    }


def _reach(flow: dict[str, Any], start: str, without: str | None = None) -> set[str]:
    """Every node that can be reached from `start` (not counting `start`), never passing `without`."""
    edges, seen, todo = _edges(flow), set(), [start]
    while todo:
        for nxt in edges.get(todo.pop(), []):
            if nxt != without and nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen


def _one(flow: dict[str, Any], kind: str, *, connected: bool = True) -> str:
    """The name of the one node of this type that is (or is not) part of the connections."""
    wired = set(_edges(flow)) | {n for targets in _edges(flow).values() for n in targets}
    names = [
        name
        for name, node in _nodes(flow).items()
        if node["type"] == PREFIX + kind and (name in wired) == connected
    ]
    assert len(names) == 1, (kind, names)
    return names[0]


def _sign_node(flow: dict[str, Any]) -> str:
    names = [
        name
        for name, node in _nodes(flow).items()
        if node["type"] == PREFIX + "crypto" and node["parameters"].get("action") == "hmac"
    ]
    assert len(names) == 1, names
    return names[0]


def _one_stamp(flow: dict[str, Any]) -> str:
    """The one node that reads the clock."""
    names = [
        name
        for name, node in _nodes(flow).items()
        if "Date.now()" in json.dumps(node["parameters"])
    ]
    assert len(names) == 1, names
    return names[0]


def _hash_node(flow: dict[str, Any]) -> str:
    """The node that computes the key."""
    names = [
        name
        for name, node in _nodes(flow).items()
        if node["type"] == PREFIX + "crypto" and node["parameters"].get("action") == "hash"
    ]
    assert len(names) == 1, names
    return names[0]


def _params(flow: dict[str, Any]) -> list[str]:
    """Every text inside the parameters of every node (names of fields and values), notes left out."""
    return [s for node in flow["nodes"] for s in _strings(node.get("parameters", {}))]


def _typed_in_secrets(flow: dict[str, Any]) -> list[str]:
    """Places where a node holds, or reads from outside a credential, a signing value."""

    def keys(value: Any) -> list[str]:
        if isinstance(value, dict):
            return [k for key, v in value.items() for k in [key, *keys(v)]]
        if isinstance(value, list):
            return [k for v in value for k in keys(v)]
        return []

    out = []
    for node in flow["nodes"]:
        params = node.get("parameters", {})
        for key in keys(params):
            if any(word in key.lower().replace("_", "") for word in SECRET_FIELDS):
                out.append(f"{node['name']}: field {key}")
        for text in _strings(params):
            out += [f"{node['name']}: reads {word}" for word in SECRET_READS if word in text]
        if node["type"] == PREFIX + "code":
            out.append(f"{node['name']}: a Code node")
    return out


def _concat(expression: str, values: dict[str, str]) -> str:
    """Evaluate a recipe written as quoted texts and names joined by ' + ' (the only form used)."""
    out = []
    for part in expression.split(" + "):
        part = part.strip()
        if part[0] in "'\"" and part[-1] == part[0]:
            out.append(part[1:-1])
        else:
            out.append(values[part])
    return "".join(out)


def _recipe(text_expression: str, prefix_expression: str, names: dict[str, str]) -> str:
    """The signature as the given recipe words it: prefix + lowercase hex HMAC-SHA256 of the text."""
    base = _concat(text_expression, names).encode("utf-8")
    digest = hmac.new(FAKE_SECRET.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return _concat(prefix_expression, {**names, "hmac": digest})


def _code_signature() -> dict[str, str]:
    return hmac_v0.sign(FIXED_BODY.encode("utf-8"), FIXED_TS, FAKE_SECRET, endpoint.PREFIX)


def _set_problems(flow: dict[str, Any]) -> list[str]:
    """Set nodes that are not on the version that builds their fields, or that build none."""
    out = []
    for node in flow["nodes"]:
        if node["type"] != PREFIX + "set":
            continue
        version = node.get("typeVersion")
        if isinstance(version, bool) or not isinstance(version, int | float):
            out.append(f"{node['name']}: no typeVersion")
        elif version < SET_VERSION:
            out.append(f"{node['name']}: typeVersion {version} is below {SET_VERSION}")
        elif version != SET_VERSION:
            out.append(f"{node['name']}: typeVersion {version} was not the one that was run")
        if not node.get("parameters", {}).get("assignments", {}).get("assignments"):
            out.append(f"{node['name']}: builds no field")
    return out


def _webhook_problems(flow: dict[str, Any]) -> list[str]:
    """Webhook nodes without a webhookId of the UUID form, as a field of the node itself."""
    out = []
    for node in flow["nodes"]:
        if node["type"] != PREFIX + "webhook":
            continue
        value = node.get("webhookId")
        if not isinstance(value, str) or not re.fullmatch(
            r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", value
        ):
            out.append(f"{node['name']}: no webhookId")
        if "webhookId" in node.get("parameters", {}):
            out.append(f"{node['name']}: webhookId is inside the parameters")
    return out


def _busy_parts(expression: str) -> tuple[set[str], str, int]:
    """(the statuses listed as busy, the pattern a status must match to count as an HTTP status, the rounds).

    The expression has the one form of BUSY_EXPRESSION: (listed OR not an HTTP status) AND rounds left."""
    read = re.escape(STATUS_READ)
    form = re.fullmatch(
        rf"=\{{\{{ \(\[(?P<listed>[^\]]*)\]\.includes\({read}\) \|\| !/(?P<pattern>[^/]+)/\.test\({read}\)\)"
        rf" && \$\('(?P<node>[^']+)'\)\.last\(\)\.json\.round < (?P<rounds>\d+) \}}\}}",
        expression,
    )
    assert form, "the busy condition changed its form: update this test with it"
    listed = set(re.findall(r"'(\d+)'", form["listed"]))
    assert form["listed"] == ", ".join(
        f"'{s}'" for s in sorted(listed)
    )  # nothing but quoted numbers
    return listed, form["pattern"], int(form["rounds"])


def _is_busy(expression: str, status: object) -> bool:
    """What the condition's status part gives for one value of error.status (None = the field is missing)."""
    listed, pattern, _rounds = _busy_parts(expression)
    text = "" if status is None else str(status)  # String(x ?? '')
    return text in listed or re.search(pattern, text) is None


# ---- shape ----


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_file_parses_and_says_this_version_was_not_imported_again(name):
    flow = _load(name)
    assert "run in n8n 2.47.7" in flow["name"] and NOT_REIMPORTED in flow["name"]
    assert flow["active"] is False
    assert flow["notes"].startswith(OPEN) and "has not been imported" in flow["notes"]
    assert EVIDENCE in flow["notes"]


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_every_node_has_a_name_a_type_and_a_note_that_says_what_was_seen(name):
    nodes = _load(name)["nodes"]
    assert nodes
    for node in nodes:
        assert isinstance(node.get("name"), str) and node["name"].strip(), node
        assert isinstance(node.get("type"), str) and node["type"].startswith(PREFIX), node
        # Every note opens with one of the two marks: seen as written, or something still open.
        assert node.get("notes", "").startswith((SEEN, OPEN)), node["name"]
    assert len({node["name"] for node in nodes}) == len(nodes)
    # The nodes that still hold something nobody has seen working are exactly the listed ones.
    still_open = {node["name"] for node in nodes if OPEN in node["notes"]}
    assert still_open == OPEN_NODES[name], still_open ^ OPEN_NODES[name]


def test_a_node_that_was_not_in_the_run_does_not_claim_it_was_seen():
    nodes = _nodes(_load(MAIN))
    added = [name for name, node in nodes.items() if node["type"] == PREFIX + "respondToWebhook"]
    assert len(added) == 2
    for name in [*added, _sign_node(_load(MAIN)), _load(MAIN)["nodes"][0]["name"]]:
        assert nodes[name]["notes"].startswith(OPEN), name
    for name in added:
        assert SEEN not in nodes[name]["notes"] and "NOT part of the run" in nodes[name]["notes"]


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_every_set_node_is_on_the_version_that_builds_its_fields(name):
    flow = _load(name)
    sets = [node for node in flow["nodes"] if node["type"] == PREFIX + "set"]
    assert len(sets) == {MAIN: 4, ERROR: 1}[name]
    assert _set_problems(flow) == []
    for node in sets:
        assert node["typeVersion"] == SET_VERSION, node["name"]
        assert node["parameters"]["assignments"]["assignments"], node["name"]
        assert "Keep typeVersion 3.4" in node["notes"], node["name"]


@pytest.mark.parametrize("name", [MAIN, ERROR])
@pytest.mark.parametrize("version", [3, 3.3, 2, 1, None])
def test_a_set_node_below_the_version_that_was_run_is_caught(name, version):
    """The negative of the test above: each Set node of a loaded copy is put on an older version in turn."""
    flow = _load(name)
    positions = [i for i, node in enumerate(flow["nodes"]) if node["type"] == PREFIX + "set"]
    assert positions
    for i in positions:
        broken = copy.deepcopy(flow)
        if version is None:
            del broken["nodes"][i]["typeVersion"]
        else:
            broken["nodes"][i]["typeVersion"] = version
        problems = _set_problems(broken)
        assert len(problems) == 1 and problems[0].startswith(flow["nodes"][i]["name"]), problems
    assert _set_problems(flow) == []  # the copies were changed, not the loaded file


def test_a_set_node_that_builds_no_field_is_caught():
    flow = _load(MAIN)
    broken = copy.deepcopy(flow)
    node = next(n for n in broken["nodes"] if n["type"] == PREFIX + "set")
    node["parameters"]["assignments"]["assignments"] = []
    assert _set_problems(broken) == [f"{node['name']}: builds no field"]


def test_the_webhook_node_has_a_webhook_id_and_the_readme_says_why():
    flow = _load(MAIN)
    webhook = _nodes(flow)[_one(flow, "webhook")]
    assert webhook is flow["nodes"][0]
    assert _webhook_problems(flow) == []
    assert webhook["webhookId"] == WEBHOOK_ID
    assert re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", webhook["webhookId"])
    assert (
        "webhookId" not in webhook["parameters"]
    )  # it is a field of the node, beside the parameters
    assert "placeholder" in webhook["notes"] and "fresh UUID" in webhook["notes"]
    readme = " ".join(_readme().split())
    assert f"`{WEBHOOK_ID}`, is a made-up placeholder" in readme
    assert "This address only works when the webhook node has a `webhookId`" in readme
    assert "`<address of your n8n>/webhook/<path>`" in readme
    assert "replace it in the JSON with a fresh UUID" in readme


@pytest.mark.parametrize(
    "change", ["removed", "empty", "not a UUID", "null", "moved into parameters"]
)
def test_a_webhook_node_without_a_webhook_id_is_caught(change):
    """The negative of the test above, on a changed copy of the loaded file."""
    flow = _load(MAIN)
    broken = copy.deepcopy(flow)
    node = broken["nodes"][0]
    assert node["type"] == PREFIX + "webhook"
    if change == "removed":
        del node["webhookId"]
    elif change == "empty":
        node["webhookId"] = ""
    elif change == "not a UUID":
        node["webhookId"] = "replace-me"
    elif change == "null":
        node["webhookId"] = None
    else:
        node["parameters"]["webhookId"] = node.pop("webhookId")
    problems = _webhook_problems(broken)
    assert f"{node['name']}: no webhookId" in problems, problems
    assert _webhook_problems(flow) == []


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_connections_name_only_existing_nodes(name):
    flow = _load(name)
    known = set(_nodes(flow))
    edges = _edges(flow)
    assert edges
    assert set(edges) <= known
    assert {target for targets in edges.values() for target in targets} <= known
    for kinds in flow["connections"].values():
        for outputs in kinds.values():
            for links in outputs:
                assert all(link["type"] == "main" and link["index"] == 0 for link in links)


def test_error_workflow_starts_with_an_error_trigger():
    flow = _load(ERROR)
    first = flow["nodes"][0]
    assert first["type"] == PREFIX + "errorTrigger"
    targets = {target for targets in _edges(flow).values() for target in targets}
    assert first["name"] not in targets  # nothing leads into it
    assert _reach(flow, first["name"]) == set(_nodes(flow)) - {first["name"]}


def test_main_workflow_names_an_error_workflow_placeholder():
    assert _load(MAIN)["settings"]["errorWorkflow"].startswith("REPLACE-")


# ---- no secret ----


@pytest.mark.parametrize("name", [MAIN, ERROR, README])
def test_no_string_looks_like_a_secret(name):
    text = (N8N / name).read_text(encoding="utf-8")
    strings = [text] if name == README else _strings(json.loads(text))
    for kind in ("key", "long-secret-shape", "arn"):
        found = [m.group(0)[:40] for s in strings for m in PATTERNS[kind].finditer(s)]
        assert found == [], (name, kind, found)


def test_the_scan_would_catch_a_planted_secret():
    planted = {"parameters": {"secret": "Zq9Lm2Xk" * 5}}
    assert any(PATTERNS["long-secret-shape"].search(s) for s in _strings(planted))


def test_the_sign_node_takes_its_secret_from_a_credential_and_from_nowhere_else():
    flow = _load(MAIN)
    sign = _nodes(flow)[_sign_node(flow)]
    assert sign["typeVersion"] == 2  # version 1 has a typed-in field, version 2 has none
    assert set(sign["parameters"]) == {"action", "type", "value", "dataPropertyName", "encoding"}
    assert set(sign["credentials"]) == {"crypto"}
    reference = sign["credentials"]["crypto"]
    assert set(reference) == {"id", "name"}  # a reference only: an id and a name
    assert reference["id"].startswith("REPLACE-") and reference["name"].strip()
    # no other node refers to a credential, and no node of either file holds or reads a secret itself
    others = [n["name"] for n in flow["nodes"] if "credentials" in n and n is not sign]
    assert others == []
    for name in (MAIN, ERROR):
        assert _typed_in_secrets(_load(name)) == [], name
        text = (N8N / name).read_text(encoding="utf-8")
        assert "hmacSecret" not in text and "HADAVIN_TRIGGER_SECRET" not in text, name
        assert all("credentials" not in n for n in _load(ERROR)["nodes"])


@pytest.mark.parametrize(
    "parameters",
    [
        {"secret": "={{ $json.x }}"},
        {"options": {"hmac_secret": "x"}},
        {"value": "={{ $env.SOME_NAME }}"},
        {"jsCode": "const c = require('crypto');"},
    ],
)
def test_the_typed_in_secret_check_would_catch_one(parameters):
    planted = {"nodes": [{"name": "x", "type": PREFIX + "crypto", "parameters": parameters}]}
    assert _typed_in_secrets(planted)


def test_a_code_node_is_caught_too():
    planted = {"nodes": [{"name": "x", "type": PREFIX + "code", "parameters": {}}]}
    assert _typed_in_secrets(planted) == ["x: a Code node"]


def test_readme_names_the_credential_way_and_holds_no_secret_value():
    raw = _readme()
    readme = " ".join(raw.split())
    assert "The template has ONE way" in readme
    assert "credential of the type `crypto`" in readme
    assert "`n8n import:credentials --input=<that file>`" in readme
    # the one place a value would stand holds placeholder words in angle brackets
    values = re.findall(r'"hmacSecret": "([^"]*)"', raw)
    assert values and all(re.fullmatch(r"<[A-Z-]+>", v) for v in values), values
    assert "DELETE the file" in readme
    # the other ways are named as not used, with the two settings and the two refusals as they were seen
    _head, _, other = readme.partition("Ways the template does NOT use:")
    for phrase in (
        "Never do this",
        "two non-default settings",
        "`N8N_BLOCK_ENV_ACCESS_IN_NODE=false`",
        "`NODE_FUNCTION_ALLOW_BUILTIN=crypto`",
        '"access to env vars denied"',
        "\"Module 'crypto' is disallowed\"",
    ):
        assert phrase in other, phrase


def test_the_address_is_a_placeholder():
    http = _nodes(_load(MAIN))[_one(_load(MAIN), "httpRequest")]
    assert http["parameters"]["url"] == "https://example.invalid" + endpoint.PATH
    assert http["parameters"]["method"] == endpoint.METHOD


# ---- the guard and the loop ----


def test_guard_comes_before_hashing_and_signing():
    flow = _load(MAIN)
    nodes, edges = _nodes(flow), _edges(flow)
    trigger = flow["nodes"][0]["name"]
    assert edges[trigger] and all(nodes[n]["type"] == PREFIX + "if" for n in edges[trigger])
    (guard,) = edges[trigger]
    sign, hashing = _sign_node(flow), _hash_node(flow)
    assert sign in _reach(flow, guard) and hashing in _reach(flow, guard)
    # with the guard taken out, nothing that hashes, signs or sends can be reached from the trigger
    past = _reach(flow, trigger, without=guard)
    assert past == set(), past
    # the guard is the ONLY way into the hash node, and the hash node comes before the sign node
    into_hash = [source for source, targets in edges.items() if hashing in targets]
    assert into_hash == [guard], into_hash
    assert sign in _reach(flow, hashing) and hashing not in _reach(flow, sign)
    assert (
        "String(" in nodes[hashing]["parameters"]["value"]
    )  # which is why the guard must come first
    assert "REQUIRED" in nodes[guard]["notes"]
    condition = json.dumps(nodes[guard]["parameters"])
    for field in ("$json.body.record_id", "$json.body.text"):
        assert f"typeof {field} === 'string'" in condition
        assert f"{field}.trim() !== ''" in condition
    # the false branch (second output) answers the caller with an error status, then fails the execution
    true_branch, false_branch = flow["connections"][guard]["main"]
    (refuse,) = [link["node"] for link in false_branch]
    assert nodes[refuse]["type"] == PREFIX + "respondToWebhook"
    assert 400 <= nodes[refuse]["parameters"]["options"]["responseCode"] <= 499
    assert [nodes[n]["type"] for n in edges[refuse]] == [PREFIX + "stopAndError"]
    assert _reach(flow, refuse) == set(edges[refuse])  # nothing but the stop node follows
    assert true_branch[0]["node"] == hashing
    assert sign in _reach(flow, hashing)
    assert not {sign, hashing} & _reach(flow, refuse)


def test_the_caller_is_answered_and_the_readme_says_this_was_not_run():
    flow = _load(MAIN)
    nodes, edges = _nodes(flow), _edges(flow)
    webhook = flow["nodes"][0]
    assert webhook["parameters"]["responseMode"] == "responseNode"
    answers = {n for n, node in nodes.items() if node["type"] == PREFIX + "respondToWebhook"}
    (guard,) = edges[webhook["name"]]
    true_branch, false_branch = flow["connections"][guard]["main"]
    taken = [link["node"] for link in true_branch if link["node"] in answers]
    refused = [link["node"] for link in false_branch if link["node"] in answers]
    assert len(taken) == 1 and len(refused) == 1 and set(taken + refused) == answers
    assert nodes[taken[0]]["parameters"]["options"]["responseCode"] == 202
    assert (
        edges.get(taken[0], []) == []
    )  # the answer to the caller is a side branch: nothing after it
    # it is placed above the sending chain, so that it is the first branch n8n runs (not seen in n8n)
    assert nodes[taken[0]]["position"][1] < nodes[_hash_node(flow)]["position"][1]
    for name in answers:
        assert "body" not in json.dumps(nodes[name]["parameters"]).lower()  # an empty answer
    readme = " ".join(_readme().split())
    assert "This branch was NOT run in n8n." in readme
    assert "the caller got HTTP 200 from n8n although the guard had stopped the event" in readme
    assert "It does NOT mean that Hadavin accepted it" in readme


def test_a_busy_answer_leads_through_a_wait_to_a_new_timestamp_and_a_new_signature():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    http, sign, wait = _one(flow, "httpRequest"), _sign_node(flow), _one(flow, "wait")
    assert nodes[http].get("retryOnFail") is False  # a node retry would reuse the old signature
    assert "maxTries" not in nodes[http] and "waitBetweenTries" not in nodes[http]
    assert nodes[http].get("onError") == "continueErrorOutput"
    ok_out, error_out = flow["connections"][http]["main"]
    (decide,) = [link["node"] for link in error_out]
    assert nodes[decide]["type"] == PREFIX + "if"
    (rule,) = nodes[decide]["parameters"]["conditions"]["conditions"]
    assert rule["operator"] == {"type": "boolean", "operation": "true", "singleValue": True}
    _listed, _pattern, rounds = _busy_parts(rule["leftValue"])
    assert 1 <= rounds <= 1000  # a bounded number of rounds
    again, give_up = flow["connections"][decide]["main"]
    # the stop branch leads to the stop node and to nothing else: no way from a stop back into the loop
    assert _reach(flow, give_up[0]["node"]) == set()
    assert len(again) == 1 and len(give_up) == 1
    assert [nodes[link["node"]]["type"] for link in give_up] == [PREFIX + "stopAndError"]
    after_again = _reach(flow, again[0]["node"]) | {again[0]["node"]}
    assert wait in after_again
    # after the wait: a new timestamp, then the sign node, then the send again
    after_wait = _reach(flow, wait)
    stamp = [
        name
        for name in after_wait
        if "Date.now()" in json.dumps(nodes[name]["parameters"]) and name != http
    ]
    assert len(stamp) == 1
    assert sign in _reach(flow, stamp[0]) and http in _reach(flow, sign)
    assert stamp[0] in _reach(flow, wait, without=sign)  # the stamp is passed BEFORE signing
    assert _reach(flow, wait, without=stamp[0]) == set()  # no way round the new timestamp
    assert _reach(flow, wait, without=sign) & {http} == set()  # no way round the new signature
    # the body is built once, before the loop, and no node inside the loop rebuilds it
    builders = [
        n for n, node in nodes.items() if "JSON.stringify" in json.dumps(node["parameters"])
    ]
    assert len(builders) == 1 and builders[0] not in after_wait
    # the success output leads to the state check and to nothing else (see the state-check tests below)
    assert [nodes[link["node"]]["type"] for link in ok_out] == [PREFIX + "if"]


def test_the_retry_path_never_reuses_a_timestamp_or_a_signature():
    flow = _load(MAIN)
    nodes, edges = _nodes(flow), _edges(flow)
    http, sign = _one(flow, "httpRequest"), _sign_node(flow)
    decide = flow["connections"][http]["main"][1][0]["node"]
    again = flow["connections"][decide]["main"][0][0]["node"]
    (stamp,) = [n for n, node in nodes.items() if "Date.now()" in json.dumps(node["parameters"])]
    # every way into the send node goes through the sign node, and every way into that through the stamp
    assert [source for source, targets in edges.items() if http in targets] == [sign]
    assert [source for source, targets in edges.items() if sign in targets] == [stamp]
    # from the busy branch the send node is reached only by passing the stamp node and then the sign node
    assert http in _reach(flow, again)
    assert http not in _reach(flow, again, without=stamp)
    assert http not in _reach(flow, again, without=sign)
    assert sign not in _reach(flow, again, without=stamp)
    # the stamp node writes ts from the clock at that moment, and nothing else writes or carries ts over
    stamp_fields = {
        a["name"]: a["value"] for a in nodes[stamp]["parameters"]["assignments"]["assignments"]
    }
    assert stamp_fields == {"ts": "={{ Math.floor(Date.now() / 1000).toString() }}"}
    assert nodes[sign]["parameters"]["dataPropertyName"] == "hmac"
    on_the_way = (_reach(flow, again, without=stamp) | {again}) - {stamp}
    assert on_the_way  # the nodes between the busy branch and the stamp node
    for name in on_the_way:
        node = nodes[name]
        if node["type"] == PREFIX + "set":
            # a Set node on the way drops the old ts and the old signature: it keeps named fields only
            assert node["parameters"]["includeOtherFields"] is False, name
            built = {a["name"] for a in node["parameters"]["assignments"]["assignments"]}
            assert built == {"body", "round", "checks"}, (name, built)
        texts = json.dumps(node["parameters"])
        assert "ts" not in re.findall(r"\.json\.(\w+)", texts), name  # no old timestamp is read
        assert "hmac" not in texts and "Date.now" not in texts, name
    # the key cannot change between rounds: the body comes from the node that built it once
    (next_round,) = [n for n in on_the_way if nodes[n]["type"] == PREFIX + "set"]
    carried = {
        a["name"]: a["value"] for a in nodes[next_round]["parameters"]["assignments"]["assignments"]
    }
    (builder,) = [
        n for n, node in nodes.items() if "JSON.stringify" in json.dumps(node["parameters"])
    ]
    assert carried["body"] == f"={{{{ $('{builder}').first().json.body }}}}"
    assert carried["round"] == f"={{{{ $('{stamp}').last().json.round + 1 }}}}"
    # only the send headers read ts and the signature
    readers = [
        n
        for n, node in nodes.items()
        if "$json.ts" in json.dumps(node["parameters"])
        or "$json.hmac" in json.dumps(node["parameters"])
    ]
    assert sorted(readers) == sorted([sign, http])


def test_the_busy_condition_names_502_503_504_and_counts_a_missing_status_as_busy():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    decide = flow["connections"][_one(flow, "httpRequest")]["main"][1][0]["node"]
    (rule,) = nodes[decide]["parameters"]["conditions"]["conditions"]
    expression = rule["leftValue"]
    assert expression == BUSY_EXPRESSION
    listed, _pattern, rounds = _busy_parts(expression)
    assert listed == set(BUSY) and rounds == 30
    assert f"$('{_one_stamp(flow)}')" in expression
    # the statuses that mean "the worker is busy, restarting or draining": tried again, as number or as text
    for status in BUSY:
        assert _is_busy(expression, int(status)) and _is_busy(expression, status), status
    # no HTTP status at all: the field is missing, empty, or holds something that is not a status
    for status in (None, "", "ECONNREFUSED", "ETIMEDOUT", "ECONNRESET", 0):
        assert _is_busy(expression, status), status
    # refusals are never tried again: the four named ones, every other 4xx, and the other 5xx
    for status in (
        *STOPS,
        "404",
        "405",
        "414",
        "431",
        "422",
        "429",
        "500",
        "501",
        "505",
        "200",
        "301",
    ):
        assert not _is_busy(expression, int(status)), status
        assert status not in listed
        assert f"'{status}'" not in expression
    for status in range(400, 500):
        assert not _is_busy(expression, status), status
    # the statuses the endpoint itself can answer: only 503 is tried again
    assert {s for s in endpoint.STATUS_TEXT if _is_busy(expression, s)} == {503}
    assert worker.NO_ACK[0] == 503 and worker.CONFLICT[0] == 409
    # the part about a missing status is marked as not seen, in the node and in the README
    note = nodes[decide]["notes"]
    assert note.startswith(OPEN)
    for phrase in (
        "counts a MISSING status as busy",
        "is NOT known",
        "The lead runs one more n8n evidence step",
        "502 and 504 were never sent by the stub",
        "400, 401, 409, 413 and any other 4xx are never tried again",
    ):
        assert phrase in note, phrase
    stop = nodes[flow["connections"][decide]["main"][1][0]["node"]]
    assert MEANING_OF_503 in stop["parameters"]["errorMessage"]
    assert "NOT accepted" not in stop["parameters"]["errorMessage"]


@pytest.mark.parametrize(
    "broken",
    [
        BUSY_EXPRESSION.replace("'502', '503', '504'", "'503'"),  # the state before: 503 only
        BUSY_EXPRESSION.replace("'502', '503', '504'", "'502', '503'"),
        BUSY_EXPRESSION.replace("'502', '503', '504'", "'401', '502', '503', '504'"),
        BUSY_EXPRESSION.replace("'502', '503', '504'", "'413', '502', '503', '504'"),
        BUSY_EXPRESSION.replace(
            "[1-5][0-9][0-9]", "[5][0-9][0-9]"
        ),  # every 4xx would count as busy
        BUSY_EXPRESSION.replace("^[1-5][0-9][0-9]$", "^.*$"),  # a missing status would be a stop
    ],
)
def test_the_busy_check_would_catch_a_wrong_condition(broken):
    listed, _pattern, _rounds = _busy_parts(broken)
    good = (
        listed == set(BUSY)
        and _is_busy(broken, None)
        and all(_is_busy(broken, int(s)) for s in BUSY)
        and not any(_is_busy(broken, int(s)) for s in STOPS)
    )
    assert not good


def test_a_condition_of_another_form_is_refused_by_the_check():
    with pytest.raises(AssertionError):
        _busy_parts(
            "={{ String($json.error?.status ?? '') === '503' && $('Stamp time').last().json.round < 30 }}"
        )


def test_the_loop_span_is_longer_than_one_signature_lives():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    wait = nodes[_one(flow, "wait")]["parameters"]
    assert wait["unit"] == "seconds"
    decide = flow["connections"][_one(flow, "httpRequest")]["main"][1][0]["node"]
    rounds = int(re.search(r"\.round < (\d+)", json.dumps(nodes[decide]["parameters"])).group(1))
    assert rounds * wait["amount"] > hmac_v0.MAX_AGE_S  # which is why each round signs anew
    assert f"{wait['amount']} seconds and {rounds} rounds" in _readme()


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_the_status_is_read_from_error_status_and_nowhere_else(name):
    flow = _load(name)
    texts = _params(flow)
    assert not [t for t in texts if "httpcode" in t.lower()]  # no such field on the failed item
    assert not [t for t in texts if "statusCode" in t]
    reads = [t for t in texts if "$json.error" in t or "'503'" in t]
    assert len(reads) == {MAIN: 1, ERROR: 0}[name]
    for text in reads:
        assert text.count(STATUS_READ) == 2  # once for the list, once for the missing-status test
        assert set(re.findall(r"\$json\.error\??\.(\w+)", text)) == {"status"}
        assert text.count("$json.error") == 2


def test_readme_says_where_the_status_is_and_gives_the_retry_numbers_of_the_run():
    readme = " ".join(_readme().split())
    assert "in the field `error.status`" in readme
    assert "There is no field `error.httpCode`." in readme
    _head, _, part = readme.partition("### Why n8n's own Retry On Fail stays off")
    part = part.partition("## ")[0]
    assert part, "the Retry On Fail part is gone"
    assert "It is OFF in this workflow and must stay off for the 503 case" in part
    for fact in RETRY_FACTS:
        assert fact in part, fact


def test_readme_setup_list_says_the_error_workflow_must_be_published():
    _head, _, part = _readme().partition("## Set-up")
    part = part.partition("\n## ")[0]
    numbers = re.findall(r"^(\d+)\. ", part, re.MULTILINE)
    assert numbers == [str(i) for i in range(1, len(numbers) + 1)] and len(numbers) >= 5
    steps = [" ".join(s.split()) for s in re.split(r"^\d+\. ", part, flags=re.MULTILINE)[1:]]
    publish = [s for s in steps if "The error workflow must be PUBLISHED (active)" in s]
    assert len(publish) == 1
    assert "does nothing" in publish[0] and "nobody was told" in publish[0]
    assert "Every step is required." in part
    assert any("credential" in s for s in steps) and any("webhookId" in s for s in steps)
    error_trigger = _load(ERROR)["nodes"][0]
    assert "ONLY while it was published" in error_trigger["notes"]


# ---- the signing recipe: sign node, README and hmac_v0 agree ----


def test_sign_node_recipe_gives_the_signature_of_hmac_v0():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    sign = nodes[_sign_node(flow)]["parameters"]
    assert (sign["type"], sign["encoding"], sign["dataPropertyName"]) == ("SHA256", "hex", "hmac")
    text = re.fullmatch(r"=\{\{ (.+) \}\}", sign["value"]).group(1)
    headers = {
        h["name"]: h["value"]
        for h in nodes[_one(flow, "httpRequest")]["parameters"]["headerParameters"]["parameters"]
    }
    assert set(headers) == {endpoint.TIMESTAMP_HEADER, endpoint.SIGNATURE_HEADER}
    assert headers[endpoint.TIMESTAMP_HEADER] == "={{ $json.ts }}"
    prefix = re.fullmatch(r"=\{\{ (.+) \}\}", headers[endpoint.SIGNATURE_HEADER]).group(1)
    names = {"$json.ts": str(FIXED_TS), "$json.body": FIXED_BODY}
    got = _recipe(text, prefix.replace("$json.hmac", "hmac"), names)
    assert got == _code_signature()[endpoint.SIGNATURE_HEADER.lower()]
    assert nodes[_one(flow, "httpRequest")]["parameters"]["body"] == "={{ $json.body }}"


def test_readme_recipe_gives_the_signature_of_hmac_v0():
    readme = _readme()
    line = re.search(
        r"^3\. `signature` = `(?P<prefix>\"v0=\")` \+ HMAC-SHA256\(secret, `(?P<text>[^`]+)`\) "
        r"written as lowercase hex\.$",
        readme,
        re.MULTILINE,
    )
    assert line, "the README's step 3 changed its wording: update this test with it"
    names = {"ts": str(FIXED_TS), "body": FIXED_BODY}
    got = _recipe(line["text"], line["prefix"] + " + hmac", names)
    code = _code_signature()
    assert got == code[endpoint.SIGNATURE_HEADER.lower()]
    assert code[endpoint.TIMESTAMP_HEADER.lower()] == str(FIXED_TS)
    assert got == got.lower() and len(got) == len("v0=") + 64
    assert (
        f"`{endpoint.TIMESTAMP_HEADER}: <ts>` and `{endpoint.SIGNATURE_HEADER}: <signature>`"
        in readme
    )
    assert f"`{endpoint.METHOD} {endpoint.PATH}`" in readme
    assert f"more than {hmac_v0.MAX_AGE_S} seconds away" in readme
    # a signed request built this way is accepted by the code's own check
    headers = {endpoint.TIMESTAMP_HEADER: str(FIXED_TS), endpoint.SIGNATURE_HEADER: got}
    body = FIXED_BODY.encode("utf-8")
    assert hmac_v0.verify(headers, body, FIXED_TS, FAKE_SECRET, endpoint.PREFIX)
    assert endpoint.parse_body(body)[0] == "ab" * 32


# ---- the README states what the code does ----


def test_readme_status_says_what_was_run_what_was_not_and_lists_every_verify_item():
    readme = _readme()
    flat = " ".join(readme.split())
    # the status stands at the very top: the first paragraph after the title
    status = " ".join(readme.split("\n\n")[1].split())
    assert status.startswith(
        "**Status: an earlier version of these two files was run in n8n 2.47.7"
    )
    assert f"`{EVIDENCE}`" in status
    assert "have NOT been imported or run in any n8n since" in status
    assert "Nobody has run this exact version." in status
    assert "not run in n8n" not in flat.replace("NOT run in n8n", "")  # the old status line is gone
    _head, _, listed = flat.partition("NOT run by anybody")
    listed = listed.partition("Words used here")[0]
    for phrase in NOT_RUN:
        assert phrase in listed, phrase
    seen = flat.partition("Run by the lead in n8n 2.47.7")[2].partition("NOT run by anybody")[0]
    assert re.findall(r"(?<!\d)(\d)\. ", seen)[:8] == [str(i) for i in range(1, 9)]
    _head, _, tail = readme.partition("## VERIFY ON A REAL n8n BEFORE ANY CLIENT USE")
    assert tail, "the verify list is gone"
    items = re.findall(r"^(\d+)\. NOT VERIFIED", tail, re.MULTILINE)
    assert items == [str(i) for i in range(1, len(VERIFY_ITEMS) + 1)]
    entries = re.split(r"^\d+\. NOT VERIFIED", tail, flags=re.MULTILINE)[1:]
    for phrase, entry in zip(VERIFY_ITEMS, entries, strict=True):
        assert phrase in " ".join(entry.split()), phrase


def test_readme_lists_the_states_a_200_can_carry_as_the_code_has_them():
    readme = " ".join(_readme().split())
    still_open = re.search(r"still open, more will happen: ([A-Z_, ]+)\.", readme).group(1)
    at_rest = re.search(r"nothing more will happen on its own: ([A-Z_, ]+)\.", readme).group(1)
    answered_200 = set(RunState) - worker.IN_PROGRESS
    assert {RunState(s) for s in still_open.split(", ")} == set(OPEN_STATES) - worker.IN_PROGRESS
    assert {RunState(s) for s in at_rest.split(", ")} == answered_200 - set(OPEN_STATES)
    assert "This does NOT mean the run has ended" in readme
    assert "state is RECEIVED or WORKING" in readme
    assert {s.value for s in worker.IN_PROGRESS} == {"RECEIVED", "WORKING"}


def test_readme_numbers_are_the_code_numbers():
    from hadavin_sdk import defaults

    readme = " ".join(_readme().split())
    assert worker.MAX_RUNNING == 1 and "its default is 1" in readme
    assert f"`ack_wait_s` (default {worker.ACK_WAIT_S:g} seconds)" in readme
    assert f"at most {defaults.MAX_DOCUMENT_BYTES} bytes" in readme
    assert f"{2 * defaults.MAX_DOCUMENT_BYTES} bytes" in readme
    assert f"{8 * defaults.MAX_DOCUMENT_BYTES} as the highest" in readme
    assert f"At least {endpoint.MIN_SECRET_CHARS} characters" in readme
    assert f"up to {endpoint.MAX_SENDERS} senders with 2 secrets each" in readme
    assert f"up to {2 * endpoint.MAX_SENDERS} signatures" in readme
    assert f"port {worker.PORT}" in readme and f"`{worker.LOOPBACK}`" in readme
    assert "1 to 128 characters" in readme and endpoint.KEY_RE.pattern.endswith("{1,128}")
    answers = readme.partition("## What the template does on each answer")[2]
    answers = answers.partition("### A restart of the worker")[0]
    for code in endpoint.STATUS_TEXT:
        assert re.search(rf"(?<![0-9]){code}(?![0-9])", answers), code
    # a control character is 6 bytes in JSON, a quote 2: the README's "six times" and "2 bytes"
    assert len(json.dumps("\x01")) - 2 == 6 and len(json.dumps('"')) - 2 == 2


def test_readme_names_the_stated_limits():
    readme = " ".join(_readme().split())
    for phrase in (
        "ONE run at a time",
        "is not queued",
        "LONGER than its longest run",
        "NEVER the same value as the approvals secret",
        "read the whole request before passing it on",
        "cap the number of connections",
        "end TLS",
        "every old key gives a NEW run id",
        "answers 200 with state NEEDS_PERSON",
        'reason "interrupted"',
        "must be sent with a NEW key",
        MEANING_OF_503,
        "NUL character",
        "The tick must run next to the worker",
    ):
        assert phrase in readme, phrase
    # the three limits of the round-2 review, each as one numbered item of the list of stated limits
    limits = readme.partition("## Stated limits")[2].partition("## VERIFY ON A REAL n8n")[0]
    items = re.split(r"(?<![0-9])(?=\d+\. [A-Z])", limits)
    for must_hold in (
        (
            "A cap on connections and a deadline per request are the reverse proxy's job.",
            "The worker has neither.",
        ),
        (
            "Set the process supervisor's stop grace period LONGER than the longest run, or runs in flight "
            + "at a restart end with a person.",
            "SIGTERM",
        ),
        (
            "There is no fairness among waiting requests: a later request can be served before an earlier one.",
            "No request is ever acknowledged without a stored run.",
        ),
    ):
        holders = [item for item in items if all(phrase in item for phrase in must_hold)]
        assert len(holders) == 1, must_hold
        assert re.match(r"\d+\. ", holders[0]), must_hold
    # the sentences the review named as out of date are gone
    for stale in (
        "the worker does not check that it does",
        "no test sends such a document",
        "This was not tested on a real connection",
        "was not checked. Remove NUL",
        "The event was NOT accepted",
        "Nothing was accepted",
        "Nothing is stored for that second event",
    ):
        assert stale not in readme, stale
    assert f"good tick of the last {worker.TICK_MAX_AGE_S:g} seconds" in readme
    assert f"up to {worker.CLOSE_WAIT_S:g} seconds" in readme


def test_readme_has_the_answer_table_in_plain_words():
    raw = _readme()
    part = raw.partition("## What the template does on each answer")[2]
    part = part.partition("\n### ")[0]
    assert part, "the answer table is gone"
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in part.splitlines()
        if line.startswith("|")
    ]
    assert rows[0] == ["Answer", "What it means", "What the template does"]
    table = {row[0]: row for row in rows[2:]}
    assert list(table) == [
        "202 or 200",
        "400",
        "401",
        "409",
        "413",
        "502, 503 or 504",
        "no answer",
    ]
    assert all(len(row) == 3 and all(row) for row in table.values())
    for status in STOPS:
        does = table[status][2]
        assert does.startswith("STOP: no retry, straight to the error workflow."), status
    for name in ("502, 503 or 504", "no answer"):
        assert table[name][2].startswith("BUSY"), name
    busy = table["502, 503 or 504"]
    assert "503 comes from the worker" in busy[1] and MEANING_OF_503 in busy[1]
    assert "SAME key, a NEW timestamp and a NEW signature" in busy[2]
    assert "At most 30 rounds" in busy[2] and "then the error workflow" in busy[2]
    assert "refused, timed out or was reset" in table["no answer"][1]
    assert table["202 or 200"][2].startswith(
        'NOT the end. Goes on to the state check "Run still going?"'
    )
    flat = " ".join(part.split())
    assert 'UNVERIFIED: the "no answer" row and the 502 and 504 part of the row above it.' in flat
    assert "is NOT known" in flat and "The lead runs one more n8n evidence step" in flat
    assert "every other 4xx" in flat


def test_readme_words_503_one_way_and_says_why_a_restart_must_not_reach_the_error_workflow():
    raw = _readme()
    readme = " ".join(raw.split())
    assert f"What 503 means: {MEANING_OF_503}." in readme
    assert readme.count(MEANING_OF_503) >= 3
    # no sentence says that a 503 means nothing was taken or stored
    for sentence in re.split(r"(?<=[.!?]) ", readme):
        if "503" in sentence:
            for claim in (
                "NOT accepted",
                "nothing was accepted",
                "Nothing was accepted",
                "holds nothing",
            ):
                assert claim not in sentence, sentence
    part = raw.partition("### A restart of the worker must not land events in the error workflow")[
        2
    ]
    part = " ".join(part.partition("\n## ")[0].split())
    assert part, "the restart part is gone"
    for phrase in (
        "On the stop signal (SIGTERM) the worker drains",
        "closes its port at once",
        "starts no new run",
        "only then exits",
        "502 or 504 from the reverse proxy",
        "a refused connection or a timeout with no proxy",
        "So all of them count as busy",
        "the key stays the same",
    ):
        assert phrase in part, phrase
    # Words that are not allowed as stage names, built from parts: the repo's stage-name scan reads this file.
    banned = (" d" + "ev ", "stag" + "ing", "produc" + "tion")
    for word in banned:
        assert word not in readme.lower(), word


# ---- the state check: a 202 or 200 is not the end ----


def _state_list(expression: str) -> set[str]:
    """The state names of the one list in an expression of the form [..].includes(<the state of the answer>)."""
    found = re.findall(r"\[([^\]]*)\]\.includes\(" + re.escape(STATE_READ) + r"\)", expression)
    assert len(found) == 1, expression
    names = re.findall(r"'([A-Z_]+)'", found[0])
    assert found[0] == ", ".join(f"'{n}'" for n in names)  # nothing but quoted names
    assert len(set(names)) == len(names)
    return set(names)


def _check_nodes(flow: dict[str, Any]) -> SimpleNamespace:
    """The nodes of the state check, found by following the connections from the send node's first output."""
    nodes, links = _nodes(flow), flow["connections"]
    http = _one(flow, "httpRequest")
    (check,) = [link["node"] for link in links[http]["main"][0]]
    (left,), (verdict,) = ([link["node"] for link in out] for out in links[check]["main"])
    (again,), (too_long,) = ([link["node"] for link in out] for out in links[left]["main"])
    (done,), (bad,) = ([link["node"] for link in out] for out in links[verdict]["main"])
    for name in (check, left, verdict):
        assert nodes[name]["type"] == PREFIX + "if", name
        (rule,) = nodes[name]["parameters"]["conditions"]["conditions"]
        assert rule["operator"] == {"type": "boolean", "operation": "true", "singleValue": True}
    return SimpleNamespace(
        http=http,
        check=check,
        left=left,
        verdict=verdict,
        again=again,
        too_long=too_long,
        done=done,
        bad=bad,
    )


def _rule(flow: dict[str, Any], name: str) -> str:
    return _nodes(flow)[name]["parameters"]["conditions"]["conditions"][0]["leftValue"]


def _state_check_problems(flow: dict[str, Any]) -> list[str]:
    """Ways in which an acknowledged request (2xx) could reach a good end without the state check."""
    nodes, edges, links = _nodes(flow), _edges(flow), flow["connections"]
    http = _one(flow, "httpRequest")
    out: list[str] = []
    first = [link["node"] for link in links[http]["main"][0]]
    if len(first) != 1 or nodes[first[0]]["type"] != PREFIX + "if":
        return [f"the send node's first output leads to {first}, not to one state check"]
    check = first[0]
    try:
        going = _state_list(_rule(flow, check))
    except (AssertionError, KeyError, IndexError):
        return [f"{check} does not test the state of the answer"]
    if going != {s.value for s in GOING}:
        out.append(f"{check} tests {sorted(going)}")
    outputs = links.get(check, {}).get("main", [])
    if len(outputs) != 2 or any(len(o) != 1 for o in outputs):
        return [*out, f"{check} does not have one node on each output"]
    still, verdict = outputs[0][0]["node"], outputs[1][0]["node"]
    # A good end: a node after the send node from which nothing follows and which does not fail the execution.
    after = _reach(flow, http)
    ends = {n for n in after if not edges.get(n) and nodes[n]["type"] != PREFIX + "stopAndError"}
    if len(ends) != 1:
        out.append(f"good ends after the send node: {sorted(ends)}")
    for end in sorted(ends):
        if end in _reach(flow, http, without=check):
            out.append(f"{end} can be reached without {check}")
        if end in _reach(flow, http, without=verdict):
            out.append(f"{end} can be reached without {verdict}")
        if end in _reach(flow, still, without=http) | {still}:
            out.append(f"{end} can be reached from the still-going branch without a new send")
        if [source for source, targets in edges.items() if end in targets] != [verdict]:
            out.append(f"{end} has another way in than {verdict}")
        if [link["node"] for link in links.get(verdict, {}).get("main", [[]])[0]] != [end]:
            out.append(f"{end} is not the true branch of {verdict}")
        if end in _reach(flow, flow["nodes"][0]["name"], without=http):
            out.append(f"{end} can be reached without sending")
    if nodes[verdict]["type"] != PREFIX + "if":
        out.append(f"{verdict} is not a condition")
    elif [source for source, targets in edges.items() if verdict in targets] != [check]:
        out.append(f"{verdict} has another way in than {check}")
    else:
        try:
            good = _state_list(_rule(flow, verdict))
        except (AssertionError, KeyError, IndexError):
            good = set()
        if good != {s.value for s in SUCCESS}:
            out.append(f"{verdict} takes {sorted(good)} as a success")
    return out


def test_the_three_groups_of_states_cover_every_state_of_the_code():
    assert GOING | SUCCESS | ENDED_BADLY == set(RunState)
    assert not GOING & SUCCESS and not GOING & ENDED_BADLY and not SUCCESS & ENDED_BADLY
    # "still going" holds the two states answered 202 and is every open state but the wait for an approval
    assert worker.IN_PROGRESS <= GOING
    assert GOING == set(OPEN_STATES) - {RunState.WAITING_FOR_APPROVAL}
    assert SUCCESS - set(OPEN_STATES) <= runs.FINAL
    assert RunState.NEEDS_PERSON in ENDED_BADLY and RunState.STOPPED in ENDED_BADLY
    assert set(tick.STUCK.values()) >= {"interrupted"}
    assert "FAILED" not in {s.value for s in RunState}  # the README says there is no such state


def test_the_workflow_sorts_the_states_exactly_as_the_code_names_them():
    flow = _load(MAIN)
    nodes, c = _nodes(flow), _check_nodes(flow)
    assert _rule(flow, c.check) == "={{ " + _list_text(GOING) + ".includes(" + STATE_READ + ") }}"
    assert (
        _rule(flow, c.verdict) == "={{ " + _list_text(SUCCESS) + ".includes(" + STATE_READ + ") }}"
    )
    assert _state_list(_rule(flow, c.check)) == {s.value for s in GOING}
    assert _state_list(_rule(flow, c.verdict)) == {s.value for s in SUCCESS}
    message = nodes[c.bad]["parameters"]["errorMessage"]
    assert nodes[c.bad]["type"] == PREFIX + "stopAndError"
    assert _state_list(message) == {s.value for s in ENDED_BADLY}
    # every state name written anywhere in the parameters of the workflow is a state of the code
    written = {w for text in _params(flow) for w in re.findall(r"'([A-Z][A-Z_]{3,})'", text)}
    assert written == {s.value for s in RunState}, written ^ {s.value for s in RunState}
    # the message names the state, says that the answer holds no reason, and holds nothing of the request
    assert "'the run ended in state ' + " + STATE_READ in message
    assert "The answer holds no reason" in message and "NEW key" in message
    assert (
        "the answer held no state that this workflow knows" in message
    )  # unknown state: fails too
    for word in ("$json.body", "$json.ts", "$json.hmac", "document", "$('Build request')"):
        assert word not in message, word
    for name in (c.check, c.verdict):
        assert "REQUIRED" in nodes[c.check]["notes"]
        assert nodes[name]["notes"].startswith(OPEN), name


def _list_text(states: frozenset[RunState]) -> str:
    """The list as the workflow writes it: in the order of the code's enum."""
    return "[" + ", ".join(f"'{s.value}'" for s in RunState if s in states) + "]"


def test_no_acknowledged_request_reaches_a_good_end_without_the_state_check():
    flow = _load(MAIN)
    nodes, c = _nodes(flow), _check_nodes(flow)
    assert _state_check_problems(flow) == []
    # the two other ends of the check fail the execution, and nothing follows them
    for name in (c.bad, c.too_long):
        assert nodes[name]["type"] == PREFIX + "stopAndError" and _reach(flow, name) == set(), name
    assert nodes[c.done]["type"] == PREFIX + "noOp" and _reach(flow, c.done) == set()
    # every node after the send node's first output is part of the check, or of the loop back to the send
    assert c.done not in _reach(flow, c.http, without=c.check)
    assert "optional" not in " ".join(nodes).lower()  # no node says the check may be left out
    assert "taken by the workflow, not done" in nodes["Answer caller: taken"]["notes"]


@pytest.mark.parametrize(
    "change",
    [
        "send straight to the good end",
        "send to the good end beside the check",
        "still going leads to the good end",
        "checks used up leads to the good end",
        "verdict outputs swapped",
        "still going taken as a success",
        "a failed state taken as a success",
        "one still-going state left out",
        "a second good end after the check",
    ],
)
def test_a_way_round_the_state_check_is_caught(change):
    flow = _load(MAIN)
    c = _check_nodes(flow)
    broken = copy.deepcopy(flow)
    links, nodes = broken["connections"], _nodes(broken)
    to = lambda name: {"node": name, "type": "main", "index": 0}
    if change == "send straight to the good end":
        links[c.http]["main"][0] = [to(c.done)]
    elif change == "send to the good end beside the check":
        links[c.http]["main"][0].append(to(c.done))
    elif change == "still going leads to the good end":
        links[c.check]["main"][0] = [to(c.done)]
    elif change == "checks used up leads to the good end":
        links[c.left]["main"][1] = [to(c.done)]
    elif change == "verdict outputs swapped":
        links[c.verdict]["main"].reverse()
    elif change == "still going taken as a success":
        links[c.check]["main"].reverse()
    elif change == "a failed state taken as a success":
        rule = nodes[c.verdict]["parameters"]["conditions"]["conditions"][0]
        rule["leftValue"] = rule["leftValue"].replace("'NO_ACTION'", "'NO_ACTION', 'NEEDS_PERSON'")
    elif change == "one still-going state left out":
        rule = nodes[c.check]["parameters"]["conditions"]["conditions"][0]
        rule["leftValue"] = rule["leftValue"].replace(", 'VERIFYING'", "")
    else:
        broken["nodes"].append({"name": "x", "type": PREFIX + "noOp", "parameters": {}})
        links[c.verdict]["main"][1] = [to("x")]
    assert _state_check_problems(broken), change
    assert _state_check_problems(flow) == []


def test_every_state_check_round_waits_and_signs_again_with_the_same_body():
    flow = _load(MAIN)
    nodes, edges, c = _nodes(flow), _edges(flow), _check_nodes(flow)
    stamp, sign, wait = _one_stamp(flow), _sign_node(flow), _one(flow, "wait")
    # from "still going" the send node is reached again, and only through the wait, the stamp and the sign node
    assert c.http in _reach(flow, c.left)
    for must_pass in (c.again, wait, stamp, sign):
        assert c.http not in _reach(flow, c.left, without=must_pass), must_pass
    assert edges[c.again] == [wait] and edges[wait] == [stamp] and edges[stamp] == [sign]
    assert sorted(s for s, targets in edges.items() if wait in targets) == sorted(
        [
            c.again,
            flow["connections"][flow["connections"][c.http]["main"][1][0]["node"]]["main"][0][0][
                "node"
            ],
        ]
    )
    # the node that prepares the next question: the same body, the round count kept, the check count plus one
    again = nodes[c.again]
    assert again["type"] == PREFIX + "set" and again["parameters"]["includeOtherFields"] is False
    (builder,) = [
        n for n, node in nodes.items() if "JSON.stringify" in json.dumps(node["parameters"])
    ]
    fields = {a["name"]: a["value"] for a in again["parameters"]["assignments"]["assignments"]}
    assert fields == {
        "body": f"={{{{ $('{builder}').first().json.body }}}}",
        "round": f"={{{{ $('{stamp}').last().json.round }}}}",
        "checks": "={{ " + CHECKS_READ + " + 1 }}",
    }
    assert f"$('{stamp}')" in CHECKS_READ
    # nothing between the answer and the stamp node reads the clock, an old timestamp or an old signature
    for name in (c.check, c.left, c.again, wait):
        texts = json.dumps(nodes[name]["parameters"])
        assert "ts" not in re.findall(r"\.json\.(\w+)", texts), name
        assert "hmac" not in texts and "Date.now" not in texts and "JSON.stringify" not in texts, (
            name
        )


def test_the_state_check_rounds_are_bounded_and_outlast_the_stuck_limit_plus_one_tick_gap():
    flow = _load(MAIN)
    nodes, c = _nodes(flow), _check_nodes(flow)
    form = re.fullmatch(r"=\{\{ " + re.escape(CHECKS_READ) + r" < (\d+) \}\}", _rule(flow, c.left))
    assert form, "the count condition changed its form: update this test with it"
    checks = int(form.group(1))
    assert 1 <= checks <= 1000
    # the count goes up by one in every check round and is carried, never set back, over a busy round
    busy = flow["connections"][c.http]["main"][1][0]["node"]
    next_round = nodes[flow["connections"][busy]["main"][0][0]["node"]]
    carried = {
        a["name"]: a["value"] for a in next_round["parameters"]["assignments"]["assignments"]
    }
    assert carried["checks"] == "={{ " + CHECKS_READ[1:-1] + " }}"
    writers = [
        name
        for name, node in nodes.items()
        if any(
            a["name"] == "checks"
            for a in node["parameters"].get("assignments", {}).get("assignments", [])
        )
    ]
    assert sorted(writers) == sorted([c.again, next_round["name"]])
    # the busy rounds are bounded too, and a check round does not hand out new ones
    _listed, _pattern, rounds = _busy_parts(_rule(flow, busy))
    assert 1 <= rounds <= 1000
    # the span of the checks against the code's own numbers, for the README's example agent
    wait = nodes[_one(flow, "wait")]["parameters"]
    assert wait["unit"] == "seconds" and 0 < wait["amount"] <= 60  # a wait above 65 s was never run
    llm = SimpleNamespace(
        call_timeout_s=table.AnthropicSettings.model_fields["call_timeout_s"].default,
        max_attempts=table.AnthropicSettings.model_fields["max_attempts"].default,
    )
    app = SimpleNamespace(
        config=SimpleNamespace(backends=SimpleNamespace(llm=llm)),
        registry=SimpleNamespace(agents={"a": SimpleNamespace(max_steps=EXAMPLE_STEPS)}),
    )
    stuck = tick.stuck_after_s(app, "a")
    assert stuck == EXAMPLE_STEPS * llm.call_timeout_s * llm.max_attempts + 60
    span, limit = checks * wait["amount"], stuck + tick.TICK_SLACK_S
    assert span > limit
    minutes = span // 60
    message = nodes[c.too_long]["parameters"]["errorMessage"]
    assert f"still shown as running after {checks} checks, about {minutes} minutes" in message
    assert "=" not in message[:2]  # a fixed text
    readme = " ".join(_readme().split())
    part = readme.partition("### The numbers")[2].partition("### Three limits")[0]
    assert part, "the numbers part is gone"
    for phrase in (
        "`stuck_after_s` in `src/hadavin_sdk/runtime/tick.py`",
        "`max_steps` times `call_timeout_s` times `max_attempts`, plus 60 seconds",
        f"the defaults {llm.call_timeout_s:g} seconds and {llm.max_attempts}",
        f"{tick.TICK_SLACK_S} seconds as the longest gap (`TICK_SLACK_S`",
        (
            f"`max_steps` {EXAMPLE_STEPS} on the defaults: {EXAMPLE_STEPS} x {llm.call_timeout_s:g} x "
            f"{llm.max_attempts} + 60 = {stuck:g} seconds"
        ),
        f"{limit:g} seconds",
        f"a wait of {wait['amount']} seconds",
        f"{checks} checks",
        f"{span} seconds ({minutes} minutes)",
        "checks times wait must be LONGER than that client's stuck limit plus one tick gap",
    ):
        assert phrase in part, phrase
    # the three other examples of the README: the smallest whole number of checks that is NOT enough
    for steps, not_enough in re.findall(r"`max_steps` (\d+) (?:needs )?more than (\d+)", part):
        need = int(steps) * llm.call_timeout_s * llm.max_attempts + 60 + tick.TICK_SLACK_S
        assert int(not_enough) * wait["amount"] <= need < (int(not_enough) + 1) * wait["amount"], (
            steps
        )
    assert len(re.findall(r"`max_steps` (\d+) (?:needs )?more than (\d+)", part)) == 3


def test_readme_says_why_a_202_is_not_the_end_and_has_a_row_for_every_state():
    raw = _readme()
    section = raw.partition("\n## A 202 is not the end\n")[2].partition("\n## ")[0]
    assert section, "the section is gone"
    flat = " ".join(section.split())
    assert "The state check is a REQUIRED part of the main workflow, not an extra." in flat
    # the sequence of four steps
    why = section.partition("### Why")[2].partition("\n### ")[0]
    steps = [" ".join(s.split()) for s in re.split(r"^\d+\. ", why, flags=re.MULTILINE)[1:]]
    assert len(steps) == 4
    for step, phrases in zip(
        steps,
        (
            ("stores the run", "the worker process dies", "no acknowledgement"),
            ("tries again", "answers 202", "no work is going on anywhere"),
            ("finishes as a success", "Nothing tries again after a 2xx"),
            ("the tick", 'NEEDS_PERSON with the reason "interrupted"', "NO message to a person"),
        ),
        strict=True,
    ):
        for phrase in phrases:
            assert phrase in step, phrase
    assert "shows a success, the work was never done, and nobody is told" in flat
    assert "killed during a restart" in flat
    # the table: one row for each state of the code, sorted the way the workflow sorts it
    table_part = section.partition("### The states")[2].partition("\n### ")[0]
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in table_part.splitlines()
        if line.startswith("|")
    ]
    assert rows[0] == ["State", "What it means in plain words", "What the template does"]
    by_state = {row[0]: row for row in rows[2:]}
    assert len(by_state) == len(rows) - 2  # no state twice
    assert set(by_state) == {s.value for s in RunState}
    assert all(len(row) == 3 and all(row) for row in by_state.values())
    for group, opening in ((GOING, "STILL GOING:"), (SUCCESS, "SUCCESS:"), (ENDED_BADLY, "ERROR:")):
        for state in group:
            assert by_state[state.value][2].startswith(opening), state
    assert "There is no state named FAILED in the code" in flat
    assert "The answer holds no reason" in flat
    assert "fails closed" in flat
    assert "UNVERIFIED: all of this section's n8n side." in flat
    # the nodes the section names exist
    names = set(_nodes(_load(MAIN)))
    for name in re.findall(r'"([^"]+)"', flat):
        if name[0].isupper() and (
            "?" in name or name.startswith(("Stop:", "Done:", "Next ", "Wait "))
        ):
            assert name in names, name
    # the caller's early answer is worded plainly
    whole = " ".join(raw.split())
    assert 'the caller\'s 202 means "taken by the workflow", not "done"' in whole
    assert "Check state (optional)" not in whole


def test_readme_states_the_three_limits_of_the_state_check():
    raw = _readme()
    section = raw.partition("\n## A 202 is not the end\n")[2].partition("\n## ")[0]
    part = section.partition("### Three limits")[2]
    items = [" ".join(s.split()) for s in re.split(r"^\d+\. ", part, flags=re.MULTILINE)[1:]]
    assert len(items) == 3
    for item, phrases in zip(
        items,
        (
            (
                "Until the tick has run, a dead run looks alive.",
                "RECEIVED or WORKING",
                "up to the stuck limit plus one tick gap to notice",
            ),
            (
                "The worker itself tells no person about an interrupted run.",
                "This template's error workflow is the only notice today.",
            ),
            (
                "set the process supervisor's stop grace period longer than the longest run",
                "forced kill",
                'ends as "interrupted"',
                "its key is never run again",
                "a NEW key is needed to redo the work",
            ),
        ),
        strict=True,
    ):
        for phrase in phrases:
            assert phrase in item, phrase
    # the first two are in the list of stated limits too, the third is there as limit 11 (pinned above)
    limits = " ".join(
        raw.partition("## Stated limits")[2].partition("## VERIFY ON A REAL n8n")[0].split()
    )
    assert "A dead run looks alive until the tick has run." in limits
    assert "The worker tells no person about an interrupted run." in limits
    assert "a NEW key is needed to redo the work" in limits
    # the error workflow's note names what lands there now
    notify = _load(ERROR)["nodes"][-1]["notes"]
    assert "a run that ended in a state that is not a success" in notify
    assert "ONLY notice a person gets today" in notify
    for state in ENDED_BADLY:
        assert state.value in notify, state
