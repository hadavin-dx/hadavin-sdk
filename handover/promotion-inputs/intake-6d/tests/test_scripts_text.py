"""The two PowerShell run scripts are checked as text (they are not Python, so the AST scans skip them): pure ASCII, no read of the key file, no printing of
variables, no secret name anywhere, the order of the steps, the safety checks. Needs the demo-only folder (listed in NEEDS_DEMO_DATA)."""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from conftest import ROOT
from intake import secret_store

TOOLS = ROOT / "demo_only" / "tools"
SCRIPTS = {p.name: p.read_text(encoding="utf-8") for p in TOOLS.glob("*.ps1")}
# the only variables a message may contain: a port number, our own error text, the user name and process facts inside a file we write
ALLOWED_VARIABLES = (
    "$port",
    "$seen",
    "$n ",
    '$n"',
    "$($_.Exception.Message)",
    "$($env:USERNAME)",
    "$($svc.Id)",
    "$($svc.StartTime.ToFileTimeUtc())",
)


def code_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def scrubbed(ln: str) -> str:
    for a in ALLOWED_VARIABLES:
        ln = ln.replace(a, "")
    return ln


def test_both_scripts_exist():
    assert set(SCRIPTS) == {"run_demo.ps1", "stop_demo.ps1"}


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_ascii_lf_no_bom(name):
    raw = (TOOLS / name).read_bytes()
    raw.decode("ascii")
    assert b"\r" not in raw


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_no_key_file_no_secret_name_no_variable_printing(name):
    text = SCRIPTS[name]
    assert "secrets" not in text.lower() and "passphrase" not in text.lower()
    for n in secret_store.NAMES:
        assert n not in text
    for ln in code_lines(text):
        s = scrubbed(ln)
        assert not re.search(
            r"(Write-Output|Write-Host|Write-Verbose|Write-Debug|echo|Out-Host|Out-String)\s+(\"[^\"]*\$|[^'\";}\s]*\$)", s, re.I
        ), ln
        assert not re.search(
            r"Get-ChildItem\s+env:|\bdir\s+env:|Get-Item\s+env:|\bgci\s+env:|\bGet-Variable\b|\bstring\]::Join", s, re.I
        ), ln
        assert not re.search(r"\$env:\w*(KEY|SECRET|TOKEN|PASSWORD|PASSPHRASE)\w*\s*=", ln, re.I), ln
        assert not re.search(r"Get-Content", ln) or "$pidFile" in ln  # the only file read is the saved process id
        assert "2>$null" not in ln and "2> $null" not in ln  # failures are never hidden


def test_run_demo_order_and_settings():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    write_key = re.search(r"^\s*python tools/make_run_env\.py\s*$", text, re.M)  # the line that WRITES the key file (no --remove)
    assert write_key
    marks = [
        text.index("'intake', 'serve'"),
        text.index("healthz"),
        text.index("Remove-Item -Force -ErrorAction SilentlyContinue $envFile"),  # a stale file is deleted first
        write_key.start(),
        text.index("compose -p"),
        text.index("make_run_env.py --remove | Out-Null"),  # the first one, right after compose up,
        text.index("n8n_setup.py"),
        text.index("docker restart intake_n8n"),
    ]
    # the service answers BEFORE the key file exists; the key file is written just before docker reads it and removed right after; restart AFTER setup
    assert marks == sorted(marks) and len(set(marks)) == len(marks)
    assert "$env:INTAKE_MODEL_BACKEND = 'anthropic'" in text
    assert "--env-file $envFile" in text
    assert re.search(r"if \(-not \$env:HADAVIN_LOCAL\)[^\n]*exit 3", text)


def test_run_demo_gives_the_callers_shell_its_backend_value_back():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    assert (
        text.index("$oldBackend = $env:INTAKE_MODEL_BACKEND")
        < text.index("$env:INTAKE_MODEL_BACKEND = 'anthropic'")
        < text.index("Start-Process")
    )
    assert text.index("Start-Process") < text.index("$env:INTAKE_MODEL_BACKEND = $oldBackend")
    assert text.index("$oldBackend = $env:INTAKE_MODEL_BACKEND") < text.index(
        "try {"
    )  # captured before the try, so the finally can always use it
    fin = text.index("finally {")
    assert fin < text.index(
        "$env:INTAKE_MODEL_BACKEND = $oldBackend"
    )  # the restore sits in the finally block: an error or Ctrl+C cannot skip it
    assert "Remove-Item Env:" in text and text.index("Remove-Item Env:") > fin
    # unset before -> unset again; set before -> the old value back (an always-true condition would wipe a value the caller had)
    assert "if ($null -eq $oldBackend) { Remove-Item Env:" in text and "} else { $env:INTAKE_MODEL_BACKEND = $oldBackend }" in text


def test_stop_demo_keeps_the_process_file_and_flag_when_the_kill_failed():
    text = "\n".join(code_lines(SCRIPTS["stop_demo.ps1"]))
    rm = text.index("Remove-Item -Force -ErrorAction SilentlyContinue $pidFile")
    assert "if (-not $failed) {" in text[rm - 40 : rm] and text.index("taskkill") < rm


def test_both_scripts_say_they_were_not_run_against_the_real_service():
    for name in SCRIPTS:
        assert SCRIPTS[name].startswith("# NOT YET RUN AGAINST THE REAL SERVICE"), name


def test_run_demo_checks_before_it_starts_and_cleans_up_after_a_failure():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    assert "Get-NetTCPConnection -State Listen -LocalPort $port" in text and "$port = 8750" in text  # port must be free
    assert "-match 'intake\\s+serve'" in text and "Name -like 'python*'" in text  # an earlier service is recognised by its command line
    assert text.index("Find-DemoService") < text.index("Remove-Item -Force $pidFile")  # never delete the process file before looking at it
    assert "HasExited" in text and "serve.err" in text  # fails loudly when the service died (missing key, stop switch)
    assert re.search(r"finally \{[^}]*make_run_env\.py --remove[^}]*\}", text, re.S)  # the key file never stays after a failure
    assert re.search(r"if \(\$started\) \{[^}]*stop_demo\.ps1", text, re.S)  # a failed start stops what was started
    assert "demo_running.txt" in text  # the flag that makes `reset` refuse while the demo runs


def test_run_demo_restricts_the_run_folder_to_the_current_user():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    assert 'icacls $runDir /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)F"' in text
    assert text.index("icacls") < text.index("make_run_env.py")  # the folder is locked down before the key file is written


def test_stop_demo_checks_the_process_before_stopping_and_reports_failures():
    text = SCRIPTS["stop_demo.ps1"]
    assert (
        "intake\\s+serve" in text and "Name -like 'python*'" in text and "StartTime.ToFileTimeUtc()" in text
    )  # name alone is never enough
    assert "taskkill /PID $id /T /F" in text and "Stop-Process" not in text  # the whole process tree of the one verified process
    assert "$failed = $true" in text and "if ($failed) { exit 1 }" in text and code_lines(text)[-1] == "exit 0"
    assert "n8n.env" in text and "demo_running.txt" in text
    assert "docker rm -f -v $n" in text and "$LASTEXITCODE -ne 0" in text


@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell not available")
@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_script_parses(name):
    cmd = (
        "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('"
        + str(TOOLS / name)
        + "',[ref]$null,[ref]$e); exit $e.Count"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=60, check=False)
    assert r.returncode == 0, r.stdout[-200:]


def test_health_wait_sends_no_token_and_counts_any_http_answer_as_up():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    assert "/healthz" in text and "X-Hadavin-Token" not in text and "-Headers" not in text  # the script never holds a token
    assert (
        "if ($_.Exception.Response) { $alive = $true; $seen = [int]$_.Exception.Response.StatusCode }" in text
    )  # 401, 503 ... all mean "it is up"
    assert 'Write-Output "step service answers (HTTP status $seen)"' in text  # the status seen is printed


def test_the_run_folder_lock_down_is_checked():
    text = "\n".join(code_lines(SCRIPTS["run_demo.ps1"]))
    i = text.index("icacls $runDir")
    assert "if ($LASTEXITCODE -ne 0)" in text[i : i + 400] and "exit 3" in text[i : i + 400]
    assert "while Docker starts" in SCRIPTS["run_demo.ps1"]  # the key file lives that long, not just a few seconds


def test_a_busy_port_is_named_in_the_compose_error():
    assert "port 5678, 8025 or 1025" in SCRIPTS["run_demo.ps1"]


def test_stop_demo_without_a_local_folder_says_so_and_fails():
    text = "\n".join(code_lines(SCRIPTS["stop_demo.ps1"]))
    i = text.index("HADAVIN_LOCAL is not set, so the service was not checked")
    block = text[i : text.index("}", i)]  # the rest of the else block that prints the note
    assert "$failed = $true" in block  # the all-clear is impossible: the script ends with exit 1


def test_both_scripts_guard_an_empty_process_file():
    for name in ("run_demo.ps1", "stop_demo.ps1"):
        text = "\n".join(code_lines(SCRIPTS[name]))
        assert "$pidText = Get-Content $pidFile -TotalCount 1" in text and "if ($pidText)" in text, name


def test_the_printed_review_address_is_the_one_the_service_listens_on():
    text = SCRIPTS["run_demo.ps1"]
    # planned layout (errata 51b/52): 127.0.0.1 = access-code routes only, 127.0.0.11 = the work app (sign-in, review), 127.0.0.12 = dashboards
    assert "review page http://127.0.0.11:8750/login" in text
    assert "127.0.0.1:8750/login" not in text and "127.0.0.12" not in text
    assert "http://127.0.0.1:$port/healthz" in text  # the health wait stays on the access-code listener


@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell not available")
@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell not available")
def test_the_health_wait_snippet_treats_any_http_answer_as_alive_and_no_answer_as_not():
    """Runs the script's own try/catch lines against a local server that answers 401, 503, 500 and 200, and against a closed port."""
    import socket
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    text = SCRIPTS["run_demo.ps1"]
    lines = [ln.strip() for ln in text.splitlines()]
    i = next(k for k, ln in enumerate(lines) if ln.startswith("try { Invoke-WebRequest") and "/healthz" in ln)
    snippet = lines[i] + " " + lines[i + 1]  # the try line and the catch line

    def run(port):
        cmd = f'$port = {port}; $alive = $false; $seen = 0; {snippet}; "alive=$alive seen=$seen"'
        return subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=60, check=False).stdout

    for status in (401, 503, 500, 200):

        class H(BaseHTTPRequestHandler):
            code = status

            def do_GET(self):
                self.send_response(self.code)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            out = run(srv.server_address[1])
        finally:
            srv.shutdown()
        assert f"alive=True seen={status}" in out, (status, out)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        closed = s.getsockname()[1]
    assert "alive=False" in run(closed)  # nothing listens: not alive
