"""workflows/WF1.json wiring (spec section 13): n8n is the scheduler and notifier only. JSON loads, node types are the four allowed, the HTTP node URL is
pinned, no token value, the hosts are the two expected, the If branches go where they should."""

from __future__ import annotations

import json
import re

from conftest import ROOT, fake_secret_values

PATH = ROOT / "workflows" / "WF1.json"
RAW = PATH.read_bytes()
WF = json.loads(RAW)
ALLOWED = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.if",
    "n8n-nodes-base.emailSend",
}


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def by_type(t):
    return [n for n in WF["nodes"] if n["type"] == t]


def test_file_is_lf_only_ascii_and_loads():
    assert b"\r" not in RAW
    RAW.decode("ascii")


def test_node_types_are_exactly_the_four_allowed_and_no_code_node():
    assert {n["type"] for n in WF["nodes"]} == ALLOWED and len(WF["nodes"]) == 4
    assert not any("code" in n["type"].lower() or "execute" in n["type"].lower() for n in WF["nodes"])


def test_http_node_url_is_pinned_exactly():
    (http,) = by_type("n8n-nodes-base.httpRequest")
    assert http["parameters"]["url"] == "http://host.docker.internal:8750/events/scan"
    assert http["parameters"]["method"] == "POST"


def test_http_node_waits_300_seconds_and_does_not_fail_on_a_busy_200():
    (http,) = by_type("n8n-nodes-base.httpRequest")
    assert http["parameters"]["options"]["timeout"] == 300000  # worst scan is 120 s (settings test), so 300 s leaves room
    assert http["parameters"]["options"]["response"]["response"]["neverError"] is True


def test_schedule_is_30_seconds():
    (sch,) = by_type("n8n-nodes-base.scheduleTrigger")
    assert sch["parameters"]["rule"]["interval"] == [{"field": "seconds", "secondsInterval": 30}]


def test_only_the_scan_url_is_named():
    hosts = set()
    for s in strings(WF):
        hosts |= set(re.findall(r"https?://([^/\s\"']+)", s))
    assert hosts == {"host.docker.internal:8750"}
    assert "mailpit" not in json.dumps(WF)  # the SMTP host lives in the credential created by n8n_setup, not in the workflow


def test_no_token_value_in_workflow():
    blob = json.dumps(WF)
    for v in fake_secret_values().values():
        assert v not in blob
    for n in WF["nodes"]:
        for c in n.get("credentials", {}).values():
            assert set(c) == {"id", "name"} and c["id"] == ""  # referenced by name; the id is filled in by n8n_setup
    assert not re.search(r"\$env|\$secrets|X-Hadavin-Token", blob)
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", blob)


def test_credentials_referenced_by_name():
    (http,) = by_type("n8n-nodes-base.httpRequest")
    (mail,) = by_type("n8n-nodes-base.emailSend")
    assert http["credentials"] == {"httpHeaderAuth": {"id": "", "name": "intake-token"}}
    assert mail["credentials"] == {"smtp": {"id": "", "name": "intake-smtp"}}


def test_if_true_branch_sends_mail_and_false_branch_does_nothing():
    c = WF["connections"]
    assert c["Any new items"]["main"][0] == [{"node": "Notify approver", "type": "main", "index": 0}]
    assert c["Any new items"]["main"][1] == []
    assert "Notify approver" not in c  # the mail node ends the flow
    (iff,) = by_type("n8n-nodes-base.if")
    assert iff["parameters"]["conditions"]["conditions"][0]["leftValue"] == "={{ $json.new && $json.new.length > 0 }}"


def test_mail_addresses_and_subject():
    (mail,) = by_type("n8n-nodes-base.emailSend")
    p = mail["parameters"]
    assert p["fromEmail"] == "intake@intake.example.com" and p["toEmail"] == "approver@approver.example.com"
    assert p["subject"] == "={{ $json.new.length }} new invoice(s) need a person"
    assert "$json.new[" not in json.dumps(p)  # the mail carries a count only, no invoice data


def test_flow_is_a_straight_line_from_the_trigger():
    c = WF["connections"]
    assert c["Every 30 seconds"]["main"][0][0]["node"] == "Scan inbox"
    assert c["Scan inbox"]["main"][0][0]["node"] == "Any new items"


def test_http_node_does_not_follow_redirects():
    (http,) = by_type("n8n-nodes-base.httpRequest")
    assert http["parameters"]["options"]["redirect"] == {
        "redirect": {"followRedirects": False}
    }  # the token header must never travel to another address


def test_mail_node_tries_three_times_and_no_other_node_retries():
    (mail,) = by_type("n8n-nodes-base.emailSend")
    assert (mail["retryOnFail"], mail["maxTries"], mail["waitBetweenTries"]) == (True, 3, 5000)
    assert not any(n.get("retryOnFail") for n in WF["nodes"] if n is not mail)  # a repeated scan call could hide a busy or failing service


def test_no_node_continues_after_an_error_silently():
    assert not any(n.get("continueOnFail") or n.get("onError") for n in WF["nodes"])
