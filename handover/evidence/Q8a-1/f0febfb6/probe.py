"""EVIDENCE RUNNER probe (own script, typed from the ticket Q8a-1 and the task list). Records only.
Plants a plain lower-case word and a secret-shaped value in many places; records whether the planted text
appears in the raised message (str, args, the whole traceback chain) or in captured log records.
Output: one line per scenario, with the planted text replaced by <PLANTED>."""

import http.server
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import traceback
from pathlib import Path

import yaml

REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO))
FIX = REPO / "tests" / "fixtures"

PLAIN = "lowerplainword"
SECRETISH = "sk-" + "live-" + "Ab12Cd34Ef56Gh78Ij90Kl"  # built from parts, never printed
HEX20 = "9f" * 12  # a hex run longer than 20
AGENT40 = "a" * 40
PLANTED = {"plain": PLAIN, "secretish": SECRETISH}

rows: list[tuple[str, str, str, str]] = []  # scenario, planted, outcome, detail


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[str] = []

    def emit(self, record):
        try:
            self.records.append(record.getMessage() + " " + str(record.args))
        except Exception:  # noqa: BLE001
            self.records.append("<unformattable>")


def run(scenario: str, planted_label: str, planted: str, fn):
    cap = Capture()
    root = logging.getLogger()
    root.addHandler(cap)
    old = root.level
    root.setLevel(logging.DEBUG)
    try:
        try:
            fn()
            outcome, text = "no-exception", ""
        except BaseException as exc:  # noqa: BLE001
            text = "".join(traceback.format_exception(exc))
            outcome = type(exc).__name__
            msg = str(exc) + " " + repr(exc.args)
            in_msg = planted in msg
            in_tb = planted in text
            in_log = any(planted in r for r in cap.records)
            rows.append(
                (
                    scenario,
                    planted_label,
                    outcome,
                    f"in_message={in_msg} in_traceback_chain={in_tb} in_log={in_log} :: "
                    + str(exc).replace(planted, "<PLANTED>")[:230].replace("\n", " | "),
                )
            )
            return
        in_log = any(planted in r for r in cap.records)
        rows.append((scenario, planted_label, outcome, f"in_log={in_log}"))
    finally:
        root.removeHandler(cap)
        root.setLevel(old)


def fresh_cfg() -> Path:
    d = Path(tempfile.mkdtemp(prefix="q8probe-"))
    for name in ("config", "recorded", "inputs", "golden"):
        shutil.copytree(FIX / name, d / name, dirs_exist_ok=True)
    c = d / "config" / "config.yaml"
    c.write_text(c.read_text(encoding="utf-8").replace("{port}", "1"), encoding="utf-8")
    return d / "config"


def edit_config(cfg: Path, fn):
    p = cfg / "config.yaml"
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    fn(raw)
    p.write_text(yaml.safe_dump(raw), encoding="utf-8")


# ---------------------------------------------------------------- providers
from hadavin_sdk.actions.secrets_cache import CachedSecrets  # noqa: E402
from hadavin_sdk.actions.secrets_env import EnvSecretProvider  # noqa: E402
from hadavin_sdk.actions.secrets_file import MountedFileProvider  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="q8probe-p-"))
(tmp / "secrets").mkdir()
os.chmod(tmp / "secrets", 0o700)

for lab, val in PLANTED.items():
    run("env get(unset name)", lab, val, lambda v=val: EnvSecretProvider("Q8P_", {}).get(v))
    run("mounted_file get(missing name)", lab, val, lambda v=val: MountedFileProvider(tmp / "secrets").get(v))
    run("mounted_file get(escape ../name)", lab, val, lambda v=val: MountedFileProvider(tmp / "secrets").get("../" + v))
    run("mounted_file get(absolute name)", lab, val, lambda v=val: MountedFileProvider(tmp / "secrets").get("/" + v))

    class Empty(CachedSecrets):
        def _fetch(self, name):
            return ""

    class Boom(CachedSecrets):
        def _fetch(self, name):
            raise RuntimeError("backend failure for " + name)

    run("cache get(empty value)", lab, val, lambda v=val: Empty().get(v))
    run("cache get(fetch raises, message holds name: ARTIFICIAL)", lab, val, lambda v=val: Boom().get(v))

    try:
        import boto3  # noqa: F401
        from botocore.exceptions import ClientError

        from hadavin_sdk.actions.secrets_aws import SecretsManagerProvider

        class AwsFake:
            def __init__(self, code):
                self.code = code

            def get_secret_value(self, SecretId):
                raise ClientError({"Error": {"Code": self.code, "Message": "denied"}}, "GetSecretValue")

        class AwsBinary:
            def get_secret_value(self, SecretId):
                return {"SecretBinary": b"x"}

        run("aws get(ResourceNotFound)", lab, val, lambda v=val: SecretsManagerProvider(AwsFake("ResourceNotFoundException")).get(v))
        run("aws get(AccessDenied raw error)", lab, val, lambda v=val: SecretsManagerProvider(AwsFake("AccessDeniedException")).get(v))
        run("aws get(binary)", lab, val, lambda v=val: SecretsManagerProvider(AwsBinary()).get(v))
    except Exception as e:  # noqa: BLE001
        rows.append(("aws provider import", lab, "SKIPPED", type(e).__name__))

    try:
        from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

        from hadavin_sdk.actions.secrets_azure import AzureKeyVaultProvider

        class AzFake:
            def __init__(self, exc):
                self.exc = exc

            def get_secret(self, name):
                raise self.exc

        run("azure get(invalid name chars)", lab, val, lambda v=val: AzureKeyVaultProvider(AzFake(ResourceNotFoundError("x"))).get(v + "_/!"))
        run("azure get(not found)", lab, val, lambda v=val: AzureKeyVaultProvider(AzFake(ResourceNotFoundError("x"))).get(v.replace("_", "")))
        run("azure get(other http error)", lab, val, lambda v=val: AzureKeyVaultProvider(AzFake(HttpResponseError("denied"))).get(v.replace("_", "")))
    except Exception as e:  # noqa: BLE001
        rows.append(("azure provider import", lab, "SKIPPED", type(e).__name__))

    try:
        from google.api_core.exceptions import Forbidden, NotFound

        from hadavin_sdk.actions.secrets_gcp import GcpSecretManagerProvider

        class GcpFake:
            def __init__(self, exc):
                self.exc = exc

            def access_secret_version(self, **kw):
                raise self.exc

        run("gcp get(invalid name chars)", lab, val, lambda v=val: GcpSecretManagerProvider(GcpFake(NotFound("x")), "proj").get(v + "/!"))
        run("gcp get(not found)", lab, val, lambda v=val: GcpSecretManagerProvider(GcpFake(NotFound("x")), "proj").get(v))
        run("gcp get(forbidden raw error)", lab, val, lambda v=val: GcpSecretManagerProvider(GcpFake(Forbidden("denied")), "proj").get(v))
    except Exception as e:  # noqa: BLE001
        rows.append(("gcp provider import", lab, "SKIPPED", type(e).__name__))

# vault against a tiny local server (loopback http is allowed by the code)
from hadavin_sdk.actions.secrets_vault import VaultProvider  # noqa: E402

STATE = {"status": 404, "body": b"{}"}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(STATE["status"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(STATE["body"])

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
addr = f"http://127.0.0.1:{srv.server_address[1]}"
for lab, val in PLANTED.items():
    def vp():
        return VaultProvider(addr, lambda p: "t", ttl_s=0)

    run("vault get(invalid name chars)", lab, val, lambda v=val: vp().get(v + "/!"))
    STATE.update(status=404, body=b"{}")
    run("vault get(404)", lab, val, lambda v=val: vp().get(v))
    STATE.update(status=500, body=b"{}")
    run("vault get(500)", lab, val, lambda v=val: vp().get(v))
    STATE.update(status=200, body=json.dumps({"data": {"data": {"other": "x"}}}).encode())
    run("vault get(200 no field)", lab, val, lambda v=val: vp().get(v))
    STATE.update(status=200, body=b"<html>" + val.encode() + b"</html>")
    run("vault get(200 html body holding the planted text)", lab, val, lambda v=val: vp().get(v))
srv.shutdown()

# ---------------------------------------------------------------- config level
from hadavin_sdk import app as app_mod  # noqa: E402
from hadavin_sdk.config import load_config  # noqa: E402
from hadavin_sdk.registry import load_registry  # noqa: E402

class SP:
    """demo secrets stand-in: the real mounted_file miss for the planted name, a made-up token for the rest"""

    def __init__(self, planted):
        self.planted = planted
        self.empty = MountedFileProvider(tmp / "secrets")

    def get(self, name):
        if name == self.planted:
            return self.empty.get(name)
        return "made-up-token"


class L:
    def chat(self, *a, **k):
        raise AssertionError("llm reached")


for lab, val in PLANTED.items():
    # private_key_secret_name
    def pk(v=val):
        cfg = fresh_cfg()
        edit_config(cfg, lambda r: r["backends"].update(signer={"kind": "ed25519_local", "private_key_secret_name": v}))
        load_config(cfg)
        app_mod.build(cfg, ["test-agent"], secrets=SP(v), llm=L())

    run("config signer private_key_secret_name (load_config then build, demo)", lab, val, pk)

    def pk_both(v=val):
        cfg = fresh_cfg()
        edit_config(cfg, lambda r: r["backends"].update(signer={"kind": "ed25519_local", "private_key_secret_name": v, "private_key_path": "x.pem"}))
        load_config(cfg)

    run("config signer private_key_secret_name + private_key_path (both set)", lab, val, pk_both)

    def pk_badtype(v=val):
        cfg = fresh_cfg()
        edit_config(cfg, lambda r: r["backends"].update(signer={"kind": "ed25519_local", "private_key_secret_name": v, "bogus_field": v}))
        load_config(cfg)

    run("config signer unknown field holding value", lab, val, pk_badtype)

    # mounted_file dir
    def mdir(v=val):
        cfg = fresh_cfg()
        edit_config(cfg, lambda r: r["backends"].update(secrets={"kind": "mounted_file", "dir": v}))
        load_config(cfg)
        app_mod.build(cfg, ["test-agent"])

    run("config secrets mounted_file dir (load_config then build)", lab, val, mdir)

    def mdir_ttl(v=val):
        cfg = fresh_cfg()
        edit_config(cfg, lambda r: r["backends"].update(secrets={"kind": "mounted_file", "dir": "x", "ttl_s": v}))
        load_config(cfg)

    run("config secrets mounted_file ttl_s holding value", lab, val, mdir_ttl)

    # secret-name field in each secret provider kind (settings carry a name-ish field?)
    for kind, extra in (
        ("aws_secrets_manager", {"region": val}),
        ("azure_key_vault", {"vault_url": val}),
        ("gcp_secret_manager", {"project_id": val}),
        ("vault", {"address": val}),
        ("env", {"prefix": val}),
    ):
        def kk(kind=kind, extra=extra):
            cfg = fresh_cfg()
            edit_config(cfg, lambda r: r["backends"].update(secrets={"kind": kind, **extra}))
            load_config(cfg)

        run(f"config secrets kind={kind} field holding value (load_config)", lab, val, kk)

    # golden case id and input_ref
    def golden(v=val):
        cfg = fresh_cfg()
        g = cfg.parent / "golden" / "test-agent.jsonl"
        g.write_text(json.dumps({"id": v, "input_ref": v + ".txt", "expected": {"action": "x", "inputs": {}}}) + "\n", encoding="utf-8")
        from hadavin_sdk import evals

        evals.gate(load_registry(load_config(cfg)), L(), "test-agent")

    run("golden case id and input_ref (load_registry then evals.gate, demo)", lab, val, golden)

    def golden_traversal(v=val):
        cfg = fresh_cfg()
        g = cfg.parent / "golden" / "test-agent.jsonl"
        g.write_text(json.dumps({"id": v, "input_ref": "../" + v, "expected": {"action": "x", "inputs": {}}}) + "\n", encoding="utf-8")
        from hadavin_sdk import evals

        evals.gate(load_registry(load_config(cfg)), L(), "test-agent")

    run("golden input_ref escaping inputs_dir", lab, val, golden_traversal)

    # executor function reference outside check_modules
    for key in ("verify_check", "rollback"):
        def ex(v=val, key=key):
            cfg = fresh_cfg()
            p = cfg / "actions" / "send_email.yaml"
            d = yaml.safe_load(p.read_text(encoding="utf-8"))
            d[key] = v + ":fn"
            p.write_text(yaml.safe_dump(d), encoding="utf-8")
            load_registry(load_config(cfg))

        run(f"action {key} function reference outside check_modules", lab, val, ex)

    def ex_mod_only(v=val):
        cfg = fresh_cfg()
        p = cfg / "actions" / "send_email.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        d["verify_check"] = "tests.fixtures.checks:" + v
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        load_registry(load_config(cfg))

    run("action verify_check module ok, function name = planted value", lab, val, ex_mod_only)

# agent ids (40-char, hex-run) with a deliberate error elsewhere in the agent
for label, aid in (("40-char agent id", AGENT40), ("hex-run agent id", "run-" + HEX20), ("secret-shaped agent id", SECRETISH)):
    def ag(aid=aid):
        cfg = fresh_cfg()
        p = cfg / "agents.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        d[0]["id"] = aid
        d[0]["model_route"] = "no-such-route"
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        load_registry(load_config(cfg))

    run(f"{label}, error in agent (unknown route)", "id", aid, ag)

    def ag2(aid=aid):
        cfg = fresh_cfg()
        p = cfg / "agents.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        d[0]["id"] = aid
        d[0]["scope_allowed"] = ["no_such_action"]
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        load_registry(load_config(cfg))

    run(f"{label}, error in agent (unknown action in scope)", "id", aid, ag2)

    def ag3(aid=aid):
        cfg = fresh_cfg()
        p = cfg / "agents.yaml"
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        d.append({**d[0], "id": aid})
        d.append({**d[0], "id": aid})
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        load_registry(load_config(cfg))

    run(f"{label}, duplicate agent id", "id", aid, ag3)

# tool manifest: field name shows, value does not
from hadavin_sdk.tools import parse_manifest  # noqa: E402

base = {
    "name": "t1",
    "function": "m:f",
    "description": "d",
    "input_schema": {"type": "object"},
    "side_effect": "none",
}
for label, patch in (
    ("max_output_bytes: 0", {"max_output_bytes": 0}),
    ("max_output_bytes: planted text", {"max_output_bytes": SECRETISH}),
    ("unknown key named like a secret", {SECRETISH: 1}),
    ("side_effect planted", {"side_effect": SECRETISH}),
):
    def pm(patch=patch):
        parse_manifest([{**base, **patch}], "tools/test-agent.yaml")

    run(f"tool manifest {label}", "secretish", SECRETISH, pm)

width = max(len(r[0]) for r in rows)
for s, lab, out, det in rows:
    print(f"{s:<{width}} | {lab:<9} | {out:<22} | {det}")
n_leak = sum(1 for r in rows if "True" in r[3].split("::")[0])
print(f"\nSCENARIOS={len(rows)} LEAKS(planted text found in message/traceback/log)={n_leak}")
