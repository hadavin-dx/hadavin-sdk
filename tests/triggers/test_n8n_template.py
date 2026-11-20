"""The n8n outline files: what can be checked without an n8n.

An earlier version of the two workflow files was run in n8n 2.47.7 by the lead (the record is
handover/core-a/inputs/lead-evidence-n8n-1.md). The files were then changed to follow that record and
were not imported again. These tests pin what the record showed must hold: Set nodes on 3.4, a webhookId,
the signing value in a credential and nowhere else, the status read from error.status, Retry On Fail off,
the guard before the hash node and the sign node, a 503 leading through a Wait back to a new signature.
They tie the signing recipe as the sign node and the README word it to ``hmac_v0``, and they list the
nodes that still hold something nobody has seen working. They do not show that n8n accepts the files.
The fake secret is built from parts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.models import OPEN_STATES, RunState
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
        "Wait before next round",
        "Check state (optional)",
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
    "The real Hadavin endpoint (a stub answered)",
    "One webhook call that starts two executions",
    "n8n Cloud and queue mode",
    "n8n versions other than 2.47.7",
)
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
    sets = [node for node in _load(name)["nodes"] if node["type"] == PREFIX + "set"]
    assert len(sets) == {MAIN: 3, ERROR: 1}[name]
    for node in sets:
        assert node["typeVersion"] == SET_VERSION, node["name"]
        assert node["parameters"]["assignments"]["assignments"], node["name"]
        assert "Keep typeVersion 3.4" in node["notes"], node["name"]


def test_the_webhook_node_has_a_webhook_id_and_the_readme_says_why():
    flow = _load(MAIN)
    webhook = _nodes(flow)[_one(flow, "webhook")]
    assert webhook is flow["nodes"][0]
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


def test_a_503_leads_through_a_wait_to_a_new_signature():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    http, sign, wait = _one(flow, "httpRequest"), _sign_node(flow), _one(flow, "wait")
    assert nodes[http].get("retryOnFail") is False  # a node retry would reuse the old signature
    assert "maxTries" not in nodes[http] and "waitBetweenTries" not in nodes[http]
    assert nodes[http].get("onError") == "continueErrorOutput"
    ok_out, error_out = flow["connections"][http]["main"]
    (decide,) = [link["node"] for link in error_out]
    assert nodes[decide]["type"] == PREFIX + "if"
    condition = json.dumps(nodes[decide]["parameters"])
    assert "'503'" in condition
    rounds = re.search(r"\.round < (\d+)", condition)
    assert rounds and 1 <= int(rounds.group(1)) <= 1000  # a bounded number of rounds
    again, give_up = flow["connections"][decide]["main"]
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
    # the success output does not lead back into the loop
    assert http not in _reach(flow, ok_out[0]["node"])


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
        assert "String($json.error?.status ?? '') === '503'" in text
        assert re.findall(r"\$json\.error\??\.(\w+)", text) == ["status"]


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
    for code in endpoint.STATUS_TEXT:
        assert re.search(rf"(\| |Also: |; ){code}\b", readme), code
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
        "The event was NOT accepted",
        "NUL character",
        "The tick must run next to the worker",
    ):
        assert phrase in readme, phrase
    # Words that are not allowed as stage names, built from parts: the repo's stage-name scan reads this file.
    banned = (" d" + "ev ", "stag" + "ing", "produc" + "tion")
    for word in banned:
        assert word not in readme.lower(), word
