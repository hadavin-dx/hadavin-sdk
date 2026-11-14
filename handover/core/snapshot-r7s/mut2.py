"""Mutant runner for r7s (adapted from out/R7Q/mut.py). ONE runner per tree copy.
usage: python mut2.py <set> [ids...]   set = R (mutants of r7r, copy out/R7S/mutR) or S (mutants of r7s, copy out/R7S/mutS)
Each mutant: one exact text replaced (must occur once), tests run under unshare -n with the lo_up driver, the file is
restored from the pristine tree afterwards and compared byte for byte. KILLED = pytest exit 1."""

import filecmp
import os
import shutil
import subprocess
import sys

R = "/home/user/build/rr6/"
O = R + "out/R7S/"
SET = sys.argv[1]
M = O + ("mutR/" if SET == "R" else "mutS/")
S = R + ("tree-R7R/" if SET == "R" else "tree-R7S/")
TMP = O + "tmp-mut" + SET
os.makedirs(TMP, exist_ok=True)
T7Q = "tests/test_r7q_findings.py"
T7S = "tests/test_r7s_findings.py"
GUARD = "tests/test_file_call_guard.py"
RR = "scripts/run_real_check.py"
BR = "demo_only/bad_request.py"
IC = "src/lead_desk/imap_count.py"
SUP = "tests/support.py"
N1 = "tests/test_r7n_findings.py"
CALLS = '    (\n        "demo_only/bad_request.py",\n        "ThreadingHTTPServer",\n    ): "the base class of QuietServer, which every fake extends; each fake\'s factory refuses a non-loopback host",\n'
Q8 = "q8"
muts_R = [
    ("Q13", RR, 'q_bytes = longest_request_bytes(live, make_plan(tag, persons))',
     'q_bytes = len(request_body(live, question_text("L000000000000", f"x@{EMAIL_DOMAIN}")))', [(T7Q, "q1")]),
    ("Q14", RR, 'q_bytes = longest_request_bytes(live, make_plan(tag, persons))',
     'q_bytes = longest_request_bytes(live, make_plan(new_tag(), persons))', [(T7Q, "q2")]),
    ("Q19", RR, '    tag = new_tag()  # once', '    tag = "rfixed1"  # once', [(T7Q, "q2")]),
    ("mutA", GUARD, CALLS, "", [(GUARD, None)]),
    ("mutB", BR, "from typing import Any\n", 'from typing import Any\n\n\ndef _planted():\n    import os\n    return os.listdir(".")\n', [(GUARD, None)]),
    ("X1", IC, '        raise ImapConnectionError("the mailbox could not be read") from None',
     '        raise ImapConnectionError("the mailbox could not be read" + str(e)) from None', [(T7Q, "q9")]),
    ("X1ctx", IC, '        raise ImapConnectionError("the mailbox could not be read") from None',
     '        raise ImapConnectionError("the mailbox could not be read")', [(T7Q, "q9")]),
]
muts_S = [
    # s1: QuietServer
    ("S01", BR, "if not isinstance(host, str) or not is_loopback_host(host):", "if not isinstance(host, str):", [(T7S, "s1")]),
    ("S02", BR, "if not isinstance(host, str) or not is_loopback_host(host):", "if False:", [(T7S, "s1")]),
    ("S03", BR, "if not isinstance(host, str) or not is_loopback_host(host):", "if isinstance(host, str) and not is_loopback_host(host):", [(T7S, "s1")]),
    ("S04", BR, "        super().__init__(server_address, request_handler_class, bind_and_activate)\n", "        pass\n", [(T7S, "s1")]),
    ("S05", BR, "        host = server_address[0] if isinstance(server_address, tuple) and server_address else None\n        if not isinstance(host, str) or not is_loopback_host(host):  # fails closed: anything unreadable is refused\n            raise ValueError(LOOPBACK_HOST_TEXT)\n        super().__init__(server_address, request_handler_class, bind_and_activate)\n",
     "        super().__init__(server_address, request_handler_class, bind_and_activate)\n        host = server_address[0] if isinstance(server_address, tuple) and server_address else None\n        if not isinstance(host, str) or not is_loopback_host(host):\n            raise ValueError(LOOPBACK_HOST_TEXT)\n", [(T7S, "s1_the_refusal_comes")]),
    ("S06", BR, 'raise ValueError(LOOPBACK_HOST_TEXT)', 'raise ValueError("no")', [(T7S, "s1")]),
    ("S07", BR, "if not isinstance(host, str) or not is_loopback_host(host):", "if not isinstance(host, str) or host == \".\".join([\"0\"] * 4):", [(T7S, "s1")]),
    # s1b: the guard
    ("S08", GUARD, '    "demo_only.bad_request.QuietServer",  # r7s: the server class of every fake; a use outside the listed files is new\n', "", [(T7S, "s1b"), (GUARD, None)]),
    # s3: counter
    ("S09", RR, "return max(0, (created or 0) - accounted)", "return max(0, accounted - (created or 0))", [(T7S, "s3c")]),
    ("S10", RR, "return max(0, (created or 0) - accounted)", "return 0", [(T7S, "s3c")]),
    ("S11", RR, "return max(0, (created or 0) - accounted)", "return max(0, (created or 0) - accounted - 1)", [(T7S, "s3c")]),
    ("S12", RR, "return max(0, (created or 0) - accounted)", "return max(0, (created or 0) - accounted) or max(0, accounted - (created or 0))", [(T7S, "s3c")]),
    ("S13", RR, "    return 0 if ok and written and not left and not unseen else EXIT_FAILED", "    return 0 if ok and written and not left else EXIT_FAILED", [(T7S, "s3e")]),
    ("S14", RR, '    for p in sorted(run_dir.glob(f"desk-{tag}-*{suffix}")):', '    for p in sorted(run_dir.glob(f"desk-*{suffix}")):', [(T7S, "s3b")]),
    ("S15", RR, 'self.log_path = run_dir / (f"desk-{tag}-{label}.log" if tag else f"desk-{label}.log")', 'self.log_path = run_dir / f"desk-{label}.log"', [(T7S, "s3b")]),
    ("S16", RR, "        accounted = done + len(left)\n", "        accounted = done\n", [(T7S, "s3_a_contact_left_by")]),
    ("S17", RR, "    accounted = len(crm_pairs)\n    if a.cleanup:", "    accounted = 0\n    if a.cleanup:", [(T7S, "s3_a_created or s3_nothing")]),
    ("S18", RR, 'hub_stats = read_counter_files(run_dir, ".hubspot.json", tag)\n    smtp_stats', 'hub_stats = read_counter_files(run_dir, ".hubspot.json", "r")\n    smtp_stats', [(T7S, "s3_a_created")]),
    ("S19", RR, "        unseen\n    ):  # the list did not", "        False\n    ):  # the list did not", [(T7S, "s3_a_created")]),
    # s6: openssl
    ("S20", SUP, "    if os.environ.get(REQUIRE_SCAN_ENV):\n        pytest.fail(", "    if False:\n        pytest.fail(", [(T7S, "s6")]),
    ("S21", SUP, "pytest.fail(f\"{text}", "pytest.skip(f\"{text}", [(T7S, "s6")]),
    ("S22", SUP, "    pytest.skip(text)\n", "    pytest.fail(text)\n", [(T7S, "s6")]),
    ("S23", N1, "    if made is None:\n        skip_or_fail_without_openssl()\n    return made", "    if made is None:\n        pytest.skip(\"the openssl program is not installed, so no test certificate can be made\")\n    return made", [(T7S, "s6_no_test_file")]),
    # q9: context
    ("X1ctx", IC, '        raise ImapConnectionError("the mailbox could not be read") from None', '        raise ImapConnectionError("the mailbox could not be read")', [(T7Q, "q9")]),
    ("S24", IC, '        raise ImapConnectionError("the mailbox could not be read") from None', '        raise ImapConnectionError("the mailbox could not be read")', [(T7Q, "q9")]),
]
muts = muts_R if SET == "R" else muts_S
only = sys.argv[2:]
out = open(O + f"mut-results-{SET}{os.environ.get("MUTSUF","")}.tsv", "a")
for mid, f, old, new, runs in muts:
    if only and mid not in only:
        continue
    p = M + f
    s = open(p, encoding="utf-8").read()
    if s.count(old) != 1:
        out.write(f"{mid}\tNOT-APPLIED count={s.count(old)}\n")
        out.flush()
        continue
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
    try:
        for tfile, k in runs:
            env = dict(os.environ, PYTHONPATH=M + "src", PYTHONDONTWRITEBYTECODE="1", TMPDIR=TMP,
                       PATH=R + "bin:" + os.environ["PATH"], GITLEAKS_BIN=R + "bin/gitleaks", DPLD_REQUIRE_SCAN="1", DPLD_REQUIRE_DEMO="1")
            cmd = ["unshare", "-n", "python", R + "src-v6/drivers/lo_up-q4g.py", R + "venv-br/bin/python", "-m", "pytest", "-q",
                   "-p", "no:cacheprovider", "-x"] + (["-k", k] if k else []) + [tfile]
            r = subprocess.run(cmd, cwd=M, env=env, capture_output=True, text=True, timeout=900)
            tail = r.stdout.strip().splitlines()[-1:]
            res = "KILLED" if r.returncode == 1 else ("SURVIVED" if r.returncode == 0 else "ERR rc=%d" % r.returncode)
            open(O + f"mutraw-{SET}-{mid}-{os.path.basename(tfile)}.txt", "w").write(r.stdout[-3000:])
            out.write(f"{mid}\t{tfile}\t{k}\t{res}\t{tail}\n")
            out.flush()
            if res == "KILLED":
                break
    finally:
        shutil.copyfile(S + f, p)
        same = filecmp.cmp(S + f, p, shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n")
        out.flush()
