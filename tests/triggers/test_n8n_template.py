"""The n8n outline files: what can be checked without an n8n.

The two workflow files and their README were written from notes and were not run in n8n. These tests pin
their shape (they parse, nodes and connections line up, the guard sits before the sign node, a 503 leads
through a Wait back to a new signature), keep secrets out of them, and tie the signing recipe as the sign
node and the README word it to ``hmac_v0`` so the three cannot drift. They do not show that n8n accepts
the files. The fake secret is built from parts.
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
PLACEHOLDER = "$env.HADAVIN_TRIGGER_SECRET"
SECRET_EXPRESSION = "={{ " + PLACEHOLDER + " }}"
FAKE_SECRET = "fake" + "-trigger-value" * 2  # 32 characters, built from parts, never a real one
FIXED_TS = 1_800_000_000
FIXED_BODY = json.dumps({"key": "ab" * 32, "document": 'line "one"\nzwei ä'}, ensure_ascii=False)

# One phrase for each item of the README's verify list, in order.
VERIFY_ITEMS = (
    "byte-identical",
    "where the HMAC secret can live",
    "the Crypto node itself",
    "HTTP Request timeout",
    "Retry On Fail",
    "runs the sign node again",
    "error workflow runs only when published",
    "two executions still yields one run",
    "n8n version is pinned",
    "one exception to",
    "both files import without error",
    "Content-Length header",
    "`$env` can be read in an expression",
    "Code node's return shape",
    "the guard:",
    "the 503 loop:",
    "the loop ends after the set number of rounds",
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
def test_file_parses_and_says_it_was_not_run(name):
    flow = _load(name)
    assert "not run in n8n" in flow["name"]
    assert flow["active"] is False
    assert flow["notes"].startswith("UNVERIFIED:")


@pytest.mark.parametrize("name", [MAIN, ERROR])
def test_every_node_has_a_name_a_type_and_an_unverified_note(name):
    nodes = _load(name)["nodes"]
    assert nodes
    for node in nodes:
        assert isinstance(node.get("name"), str) and node["name"].strip(), node
        assert isinstance(node.get("type"), str) and node["type"].startswith(PREFIX), node
        # No type version or parameter name is confirmed by the n8n notes, so every node says so.
        assert node.get("notes", "").startswith("UNVERIFIED:"), node["name"]
    assert len({node["name"] for node in nodes}) == len(nodes)


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


def test_the_secret_is_only_a_placeholder_reference():
    for name in (MAIN, ERROR):
        for node in _load(name)["nodes"]:
            params = node.get("parameters", {})
            for key, value in params.items():
                if "secret" in key.lower() or "password" in key.lower():
                    assert value == SECRET_EXPRESSION, (name, node["name"], key)
            code = params.get("jsCode", "")
            if "createHmac" in code:
                assert f"const secret = {PLACEHOLDER};" in code
                assert re.search(r"createHmac\('sha256', secret\)", code)
                assert not re.search(r"secret\s*=\s*['\"`]", code)
    main = _nodes(_load(MAIN))
    assert main[_sign_node(_load(MAIN))]["parameters"]["secret"] == SECRET_EXPRESSION
    # outside the notes, the variable name appears only inside the placeholder
    for node in main.values():
        for s in _strings(node.get("parameters", {})):
            assert s.count("HADAVIN_TRIGGER_SECRET") == s.count(PLACEHOLDER)


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
    sign = _sign_node(flow)
    hashing = [name for name, node in nodes.items() if node["parameters"].get("action") == "hash"]
    assert sign in _reach(flow, guard)
    # with the guard taken out, nothing that hashes, signs or sends can be reached from the trigger
    past = _reach(flow, trigger, without=guard)
    assert past == set(), past
    assert hashing and all(name in _reach(flow, guard) for name in hashing)
    condition = json.dumps(nodes[guard]["parameters"])
    for field in ("$json.body.record_id", "$json.body.text"):
        assert f"typeof {field} === 'string'" in condition
        assert f"{field}.trim() !== ''" in condition
    # the false branch (second output) fails the execution
    true_branch, false_branch = flow["connections"][guard]["main"]
    assert [nodes[link["node"]]["type"] for link in false_branch] == [PREFIX + "stopAndError"]
    assert sign in _reach(flow, true_branch[0]["node"]) | {true_branch[0]["node"]}
    assert sign not in _reach(flow, false_branch[0]["node"])


def test_a_503_leads_through_a_wait_to_a_new_signature():
    flow = _load(MAIN)
    nodes = _nodes(flow)
    http, sign, wait = _one(flow, "httpRequest"), _sign_node(flow), _one(flow, "wait")
    assert nodes[http].get("retryOnFail") is False  # a node retry would reuse the old signature
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


def test_option_b_code_node_uses_the_same_recipe():
    flow = _load(MAIN)
    code = _nodes(flow)[_one(flow, "code", connected=False)]
    assert code.get("disabled") is True
    js = code["parameters"]["jsCode"]
    text = re.search(r"const base = (.+);", js).group(1)
    names = {"$json.ts": str(FIXED_TS), "$json.body": FIXED_BODY}
    got = _recipe(text, "'v0=' + hmac", names)
    assert got == _code_signature()[endpoint.SIGNATURE_HEADER.lower()]
    assert ".update(base, 'utf8').digest('hex')" in js


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


def test_readme_says_not_run_and_lists_every_verify_item():
    readme = _readme()
    assert "not run in n8n" in readme
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
