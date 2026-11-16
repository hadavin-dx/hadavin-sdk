"""Self-contained: exports the committed HEAD of /home/user/build/B-Q8a2 to a fresh temp dir, mutates receiver.py there
(one mutant at a time), runs tests/test_q8a2_callback.py, removes the temp dir. Touches nothing else."""
import os, subprocess, tempfile, shutil
REPO = "/home/user/build/EV-q8a2-c19d87dc/wt"
tmp = tempfile.mkdtemp(prefix="q8a2-mut-")
subprocess.run(f"git -C {REPO} archive HEAD | tar -x -C {tmp}", shell=True, check=True)
R = tmp + "/src/hadavin_sdk/approvals/receiver.py"
src = open(R).read()
muts = {
 "m1_type_decides_handler_log": ("_LOG.error(_ERROR_LINE, _kinds(sys.exception()))","_LOG.log(logging.DEBUG if isinstance(sys.exception(), ConnectionError) else logging.ERROR, _ERROR_LINE, _kinds(sys.exception()))"),
 "m1b_handler_failure_not_logged": ("_LOG.error(_ERROR_LINE, _kinds(sys.exception()))","pass"),
 "m1c_handle_error_type_only_decides": ("logging.DEBUG if already_logged or hung_up else logging.ERROR","logging.DEBUG if hung_up else logging.ERROR"),
 "m2_flag_not_set_second_error_line": ("                    reported.flag = True\n","                    pass\n"),
 "m2b_log_after_answer_lost_on_write_timeout": ("                if failed:\n                    reported.flag = True\n                    _LOG.error(_ERROR_LINE, _kinds(sys.exception()))\n                self._answer(status, out)","                self._answer(status, out)\n                if failed:\n                    reported.flag = True\n                    _LOG.error(_ERROR_LINE, _kinds(sys.exception()))"),
 "m4a_no_cap": ("and len(kinds) < _MAX_KINDS","and True"),
 "m4b_cap_six": ("_MAX_KINDS = 5","_MAX_KINDS = 6"),
 "m4c_no_seen_set": ("id(exc) not in seen and ","True and "),
 "m4d_no_dots": ("    if exc is not None:\n        kinds.append(\"...\")","    if False:\n        kinds.append(\"...\")"),
 "m4e_hungup_context_ignored": ("exc.__context__ is None","True"),
 "m3a_isprintable_hand_range": ('c if c.isprintable() else "?"','c if not (ord(c) < 32 or ord(c) == 127 or 0x80 <= ord(c) <= 0x9F) else "?"'),
 "m3b_isprintable_c0_only": ('c if c.isprintable() else "?"','c if ord(c) >= 32 else "?"'),
 "m5_exception_arg_logged_raw": ("            args = tuple(type(a).__name__ if isinstance(a, BaseException) else a for a in args)\n","            pass\n"),
 "m6_backlog_back_to_stdlib_five": ("RECEIVER_BACKLOG  # the standard","5  # the standard"),
}
env = dict(os.environ, PYTHONPATH=tmp + "/src", UV_PROJECT_ENVIRONMENT="/home/user/build/EV-q8a2-c19d87dc/venv")
for k in ("AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","AWS_CA_BUNDLE","ANTHROPIC_BASE_URL","GH_TOKEN","GITHUB_TOKEN","CLOUDSDK_AUTH_ACCESS_TOKEN","VAULT_TOKEN","VAULT_SECRET_ID"): env.pop(k, None)
cmd = ["uv","run","--offline","--all-extras","--group","test","pytest","-q","-p","no:cacheprovider","tests/test_q8a2_callback.py","-x"]
try:
    r = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, timeout=600)
    print("baseline (unmutated):", "PASS" if r.returncode == 0 else "FAIL", r.stdout.strip().splitlines()[-1][:80], flush=True)
    import sys
    for name, (a, b) in muts.items():
        if len(sys.argv) > 1 and sys.argv[1] not in name: continue
        assert src.count(a) == 1, (name, src.count(a))
        open(R, "w").write(src.replace(a, b))
        r = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, timeout=600)
        fl = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
        print(name, "KILLED" if r.returncode else "SURVIVED", [x[:110] for x in fl[:1]], r.stdout.strip().splitlines()[-1][:60], flush=True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
