"""docker/compose.yml (spec section 13): pinned images, loopback ports, n8n gets one secret by name and nothing else, the Execute Command node is excluded.
The file is read line by line (the test group has no YAML parser)."""

from __future__ import annotations

import json
import re

from conftest import ROOT
from intake import secret_store

TEXT = (ROOT / "docker" / "compose.yml").read_text(encoding="utf-8")
LINES = [ln for ln in TEXT.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def service_block(name: str) -> str:
    out, on = [], False
    for ln in LINES:
        if re.fullmatch(r"  [a-z0-9_-]+:", ln):
            on = ln.strip() == f"{name}:"
        elif on:
            out.append(ln)
    return "\n".join(out)


def list_items(block: str, key: str) -> list[str]:
    out, on = [], False
    for ln in block.splitlines():
        if re.fullmatch(r"    [a-z_]+:", ln):
            on = ln.strip() == f"{key}:"
        elif on and ln.strip().startswith("- "):
            out.append(ln.strip()[2:].strip().strip('"'))
    return out


def test_lf_only_and_ascii():
    assert "\r" not in TEXT
    TEXT.encode("ascii")


def test_two_services_only():
    assert {ln.strip()[:-1] for ln in LINES if re.fullmatch(r"  [a-z0-9_-]+:", ln)} == {"n8n", "mailpit"}


def test_images_are_pinned_by_tag_and_digest_never_latest():
    images = re.findall(r"^\s+image:\s*(\S+)\s*$", TEXT, re.M)
    assert len(images) == 2
    for img in images:
        assert not img.split("@")[0].endswith(":latest") and ":" in img.split("@")[0].rsplit("/", 1)[-1]
        assert re.search(r"@sha256:[0-9a-f]{64}$", img)
    assert "n8nio/n8n:2.46.4@" in TEXT and "axllent/mailpit:v1.33.0@" in TEXT


def test_every_published_port_is_loopback_only():
    for svc in ("n8n", "mailpit"):
        ports = list_items(service_block(svc), "ports")
        assert ports and all(p.startswith("127.0.0.1:") for p in ports), ports
    assert not re.search(r"^\s+network_mode|^\s+privileged|0\.0\.0\.0", TEXT, re.M)


def test_no_env_file_no_mount_no_secret_value():
    assert not re.search(r"^\s+(env_file|secrets|configs):", TEXT, re.M)
    # the only volume is ONE anonymous volume for n8n's own state: no host folder is mounted anywhere
    assert list_items(service_block("n8n"), "volumes") == ["/home/node/.n8n"] and not list_items(service_block("mailpit"), "volumes")
    assert not re.search(
        r"^\s+- [^\s]*[:\\/][^\s]*:[^\s]+$", "\n".join(list_items(service_block("n8n"), "volumes")), re.M
    )  # no source:target pair
    assert "docker.sock" not in TEXT


def test_n8n_gets_exactly_one_secret_by_name_with_no_value():
    env = list_items(service_block("n8n"), "environment")
    secret_like = [e for e in env if e.split("=")[0] in secret_store.NAMES or re.search(r"KEY|PASSWORD|SECRET|TOKEN", e.split("=")[0])]
    assert secret_like == ["N8N_ENCRYPTION_KEY"]  # a bare name: its value comes from --env-file, so none is written here
    assert "=" not in secret_like[0]


def test_only_the_four_node_types_are_loaded_and_the_dangerous_ones_are_also_excluded():
    env = list_items(service_block("n8n"), "environment")
    include = json.loads(next(e for e in env if e.startswith("NODES_INCLUDE=")).split("=", 1)[1])
    assert sorted(include) == sorted(
        ["n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.httpRequest", "n8n-nodes-base.if", "n8n-nodes-base.emailSend"]
    )
    exclude = json.loads(next(e for e in env if e.startswith("NODES_EXCLUDE=")).split("=", 1)[1])
    assert {"n8n-nodes-base.executeCommand", "n8n-nodes-base.localFileTrigger", "n8n-nodes-base.code"} <= set(exclude)
    assert "N8N_BLOCK_ENV_ACCESS_IN_NODE=true" in env  # a node expression cannot read the container's environment (the encryption key)


def test_telemetry_off_and_no_execution_history_is_kept():
    env = list_items(service_block("n8n"), "environment")
    for want in (
        "N8N_DIAGNOSTICS_ENABLED=false",
        "N8N_PERSONALIZATION_ENABLED=false",
        "N8N_VERSION_NOTIFICATIONS_ENABLED=false",
        "N8N_TEMPLATES_ENABLED=false",
        "N8N_COMMUNITY_PACKAGES_ENABLED=false",
        "EXECUTIONS_DATA_SAVE_ON_SUCCESS=none",  # scan replies (item names) are not stored
        "EXECUTIONS_DATA_SAVE_ON_ERROR=none",
        "EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false",
        "EXECUTIONS_DATA_PRUNE=true",
        "EXECUTIONS_DATA_MAX_AGE=24",
    ):
        assert want in env


def test_both_containers_are_hardened():
    for svc in ("n8n", "mailpit"):
        block = service_block(svc)
        assert list_items(block, "cap_drop") == ["ALL"]
        assert list_items(block, "security_opt") == ["no-new-privileges:true"]
        assert re.search(r"^    mem_limit: \d+[mg]( |$)", block, re.M) and re.search(r"^    pids_limit: \d+$", block, re.M)
        assert re.search(r"^    cpus: \d+$", block, re.M)
    assert re.search(r"^    healthcheck:", service_block("n8n"), re.M)


def test_container_names_match_the_setup_tool():
    from tools import n8n_setup

    assert f"container_name: {n8n_setup.CONTAINER}" in TEXT
    assert "container_name: intake_mailpit" in TEXT and "name: intake" in LINES


def test_both_roots_are_read_only_and_each_runs_as_a_fixed_user():
    n8n, mail = service_block("n8n"), service_block("mailpit")
    assert re.search(r'^    user: "1000:1000"$', n8n, re.M) and re.search(r'^    user: "65534:65534"$', mail, re.M)
    for block in (n8n, mail):
        assert re.search(r"^    read_only: true$", block, re.M)
    assert list_items(n8n, "tmpfs") == ["/tmp", "/home/node/.cache:uid=1000,gid=1000"]  # without the cache folder n8n stops (tried)
    assert list_items(mail, "tmpfs") == ["/tmp"]
    env = list_items(n8n, "environment")
    assert "N8N_PUBLIC_API_DISABLED=true" in env
    assert "healthz/readiness" in n8n  # the check that matches "database migrated", not the early /healthz
    assert "MP_DISABLE_VERSION_CHECK=true" in list_items(mail, "environment")


def test_docker_compose_itself_accepts_the_file():
    import os
    import shutil
    import subprocess

    import pytest

    if shutil.which("docker") is None or subprocess.run(["docker", "compose", "version"], capture_output=True, check=False).returncode != 0:
        pytest.skip("docker compose is not installed")
    env = {**os.environ, "N8N_ENCRYPTION_KEY": "encr" + "E" * 40}  # a fake value built from parts
    r = subprocess.run(
        ["docker", "compose", "-p", "intake_check", "-f", str(ROOT / "docker" / "compose.yml"), "config", "--quiet"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stderr[-400:]
