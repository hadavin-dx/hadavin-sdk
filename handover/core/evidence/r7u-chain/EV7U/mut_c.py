"""ONE runner, one mutant at a time. Each mutant: replace one text in one file of tree-R7U-C, run the tests, restore the
original bytes, verify byte-equal (sha256), record KILLED (pytest rc != 0) or SURVIVED."""
import hashlib, subprocess, sys, pathlib, time
T = pathlib.Path("/home/user/build/rr6/out/EV7U/mutC")
RUN = "/home/user/build/rr6/out/EV7U/run-c.sh"
TESTS = ["tests/test_r7u_c_findings.py", "tests/test_r7t_findings.py", "-k", "c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12"]
L = "src/lead_desk/loopback.py"
B = "demo_only/bad_request.py"
M = [
 ("L01 accept non-loopback", L, "if not isinstance(host, str) or not is_loopback_host(host):", "if not isinstance(host, str):"),
 ("L02 drop isinstance str check", L, "if not isinstance(host, str) or not is_loopback_host(host):", "if not is_loopback_host(host):"),
 ("L03 refuse nothing at all", L, "if not isinstance(host, str) or not is_loopback_host(host):", "if False:"),
 ("L04 refuse everything", L, "if not isinstance(host, str) or not is_loopback_host(host):", "if True:"),
 ("L05 localhost spelling case sensitive", L, 'if name.lower() == "localhost":', 'if name == "localhost":'),
 ("L06 localhost prefix", L, 'if name.lower() == "localhost":', 'if name.lower().startswith("localhost"):'),
 ("L07 empty string loopback", L, 'if name.lower() == "localhost":', 'if name.lower() in ("localhost", ""):'),
 ("L08 wildcard loopback", L, "return ip.is_loopback", "return ip.is_loopback or ip.is_unspecified"),
 ("L09 any private loopback", L, "return ip.is_loopback", "return ip.is_loopback or ip.is_private"),
 ("L10 scope id allowed", L, '"%" in bare', 'False'),
 ("L11 half bracket allowed", L, '"[" in bare or "]" in bare or "%" in bare', '"%" in bare'),
 ("L12 mapped v4 not unwrapped", L, "        ip = ip.ipv4_mapped  # the same answer", "        pass  # the same answer"),
 ("L13 invalid text is loopback", L, "    except ValueError:\n        return False\n    if isinstance", "    except ValueError:\n        return True\n    if isinstance"),
 ("L14 text constant changed", L, 'LOOPBACK_HOST_TEXT = "must be this computer: localhost or 127.0.0.1"', 'LOOPBACK_HOST_TEXT = "refused"'),
 ("L15 returns constant not host", L, "        raise ValueError(LOOPBACK_HOST_TEXT)\n    return host", "        raise ValueError(LOOPBACK_HOST_TEXT)\n    return 'localhost'"),
 ("L16 heavy import in light module", L, "import ipaddress\n", "import ipaddress\nimport lead_desk.constants\n"),
 ("R01 re-export replaced by copy", B, "from lead_desk.loopback import require_loopback_host  # the one refusal lives in a light file; handed on from here",
    "def require_loopback_host(host):\n    return host"),
 ("R02 config no longer shares the rule", "src/lead_desk/config.py", "from lead_desk.loopback import is_loopback_host\n", "def is_loopback_host(name):\n    return True\n"),
 ("R03 refusing_args own text", "tools/refusing_args.py", "    from lead_desk.loopback import LOOPBACK_HOST_TEXT  # the one text: the rule's own file\nexcept ImportError", "    LOOPBACK_HOST_TEXT = 'x'\nexcept ImportError"),
 ("R04 fake_imap skips refusal", "demo_only/fake_imap.py", "        require_loopback_host(host)  # before", "        pass  # before"),
 ("R05 fake_smtp skips refusal", "demo_only/fake_smtp_tls.py", "        require_loopback_host(host)  # before", "        pass  # before"),
 ("R06 fake_imap imports heavy", "demo_only/fake_imap.py", "from lead_desk.loopback import require_loopback_host\n", "from demo_only.bad_request import require_loopback_host\n"),
 ("S01 settle forgets the outcome", "src/lead_desk/crm_hubspot.py", "            if outcome is not None:\n                self._n[outcome] += 1\n            self._n[\"create_open\"] -= 1", "            self._n[\"create_open\"] -= 1"),
 ("S02 settle forgets to close open", "src/lead_desk/crm_hubspot.py", "            self._n[\"create_open\"] -= 1\n            write_stats(self.s.stats_file, self._n)\n\n    @secret_boundary(CrmError", "            write_stats(self.s.stats_file, self._n)\n\n    @secret_boundary(CrmError"),
 ("S03 open not written before request", "src/lead_desk/crm_hubspot.py", "                    self._n[\"create_open\"] += 1\n                    try:", "                    try:"),
 ("S04 201 without id is created", "src/lead_desk/crm_hubspot.py", 'isinstance(reply.body, dict) and reply.body.get("id"):', "True:"),
 ("S05 unknown outcome counted as none", "src/lead_desk/crm_hubspot.py", '        except Exception:  # 5xx, 408 or an unclear 2xx: the contact MAY exist\n            self._settle_create("create_unknown")', '        except Exception:  # 5xx, 408 or an unclear 2xx: the contact MAY exist\n            self._settle_create(None)'),
]
only = sys.argv[1:]
out = open("/home/user/build/rr6/out/EV7U/mut-results-C.txt", "a")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for name, f, old, new in M:
    if only and name.split()[0] not in only: continue
    p = T / f
    orig = p.read_bytes(); h0 = sha(p)
    s = orig.decode()
    if s.count(old) != 1:
        out.write(f"{name}: NOT APPLIED (old text count {s.count(old)})\n"); out.flush(); continue
    try:
        p.write_bytes(s.replace(old, new).encode())
        t0 = time.time()
        r = subprocess.run([RUN, str(T), "-x", *TESTS], capture_output=True, text=True, timeout=900)
        tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED")][:2]
        verdict = "KILLED" if r.returncode != 0 else "SURVIVED"
    finally:
        p.write_bytes(orig)
    ok = sha(p) == h0
    out.write(f"{name}: {verdict} rc={r.returncode} restored_equal={ok} {int(time.time()-t0)}s {tail}\n"); out.flush()
    if not ok: sys.exit("restore failed")
