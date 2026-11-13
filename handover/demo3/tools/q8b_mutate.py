"""Q8b mutation runner (adapted from q8_mutate.py): one exact-text change per mutant, private worktree only."""
import subprocess, os, sys, datetime, json
WT = "/home/user/work/q8b-base"
LOG = "/home/user/work/q8b-logs"
PY = "/home/user/work/final-venv/bin/python"
PROG = "/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q8b.txt"
env = dict(os.environ, TMPDIR="/home/user/work/q8b-tmp", PYTHONPATH="src:.")
I, D = "src/lead_desk/identity.py", "src/lead_desk/desk.py"
MAIN = ["tests/test_flow.py","tests/test_claim_ownership.py","tests/test_claim_checks_and_crm_mode.py","tests/test_ai_after_claim.py",
        "tests/test_input_edge_cases.py","tests/test_mutants.py","tests/test_mutants_more.py","tests/test_sonar_p2_choke_points.py","tests/test_followup_edge_cases.py"]
WIDE = ["tests/test_http.py","tests/test_desk_edge_cases.py","tests/test_desk_http_edge_cases.py"]
M = [
 ("I01", I, 's.strip().lower()', 's.lower()'),
 ("I02", I, 's.strip().lower()', 's.strip()'),
 ("I03", I, 'return s.strip().lower()', 'return s.strip().casefold()'),
 ("I04", I, 'return s.strip().lower()', 'return unicodedata.normalize("NFKC", s.strip().lower())'),
 ("I05", I, 'return not any(not c.isascii() and any(x.isascii() for x in c.lower()) for c in e)', 'return True'),
 ("I06", I, 'and len(e) <= EMAIL_MAX\n', 'and len(e) < EMAIL_MAX\n'),
 ("I07", I, 'and len(normalise_email(e)) <= EMAIL_MAX', 'and True'),
 ("I08", I, 'and _EMAIL_RE.fullmatch(e) is not None', 'and True'),
 ("I09", I, 'and not e.endswith(".")', 'and True'),
 ("I10", I, 'and not any(unicodedata.category(c).startswith("C") for c in e)', 'and True'),
 ("I11", I, 'if limit is not None and len(t) > limit:', 'if limit is not None and len(t) >= limit:'),
 ("I12", I, 'if limit is not None and len(t) > limit:', 'if limit is not None and len(v) > limit:'),
 ("I13", I, 't = v.strip()\n', 't = v\n'),
 ("I14", I, 'vals[field] = t or None', 'vals[field] = t'),
 ("I15", I, 'if field != "email" and has_invisible_format(v, field == "message"):', 'if field != "email" and has_invisible_format(v, True):'),
 ("I16", I, 'if has_control_char(v, _CONTROL_OK_IN_MESSAGE if field == "message" else frozenset()):', 'if has_control_char(v, _CONTROL_OK_IN_MESSAGE):'),
 ("I17", I, 'missing = [f for f in ("name", "email") if vals[f] is None]', 'missing = [f for f in ("name",) if vals[f] is None]'),
 ("I18", I, '        b = _collapse(new.get(f))\n        if b and b != _collapse(stored.get(f)):', '        b = _collapse(new.get(f))\n        if b != _collapse(stored.get(f)):'),
 ("I19", I, 'return re.sub(" +", " ", (s or "").strip())', 'return (s or "").strip()'),
 ("I20", I, 'if not encodable(v):', 'if False:'),
 ("C01", D, 'existing = self._lookup_email_key(conn, chk.email_key)', 'existing = self._lookup_email_key(conn, chk.email)'),
 ("C02", D, 'if existing is not None:\n                    row = conn.execute(', 'if False:\n                    row = conn.execute('),
 ("C03", D, 'if rec["outcome"] is not None:  # another request or a restart finished it: nothing to write\n                return rec, False', 'if False:\n                return rec, False'),
 ("C04", D, '"UPDATE receipts SET outcome=\'duplicate\', outcome_lead_id=?, differing_fields=?, decided_at=?"', '"UPDATE receipts SET outcome=\'new\', outcome_lead_id=?, differing_fields=?, decided_at=?"'),
 ("C05", D, '" ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts + 1"', '" ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts"'),
 ("C06", D, 'return int(found[0]), found[1] == 1', 'return int(found[0]), found[1] != 1'),
 ("C07", D, 'matches = rec["payload"] == canon', 'matches = True'),
 ("C08", D, 'elif not matches:\n                self._note_payload_conflict(rid)', 'elif matches:\n                self._note_payload_conflict(rid)'),
 ("C09", D, '            if rec["outcome"] is not None:\n                return self._verdict_reply(rec, True, matches)\n            rec, decided_here', '            rec, decided_here'),
 ("C10", D, 'if not decided_here:\n                return self._verdict_reply(rec, True, matches)', 'if False:\n                return self._verdict_reply(rec, True, matches)'),
 ("C11", D, 'return self._verdict_reply(rec, False, None)\n        except Exception', 'return self._verdict_reply(rec, True, None)\n        except Exception'),
 ("C12", D, 'if not replayed:\n                drive = rec["outcome_lead_id"]', 'if replayed:\n                drive = rec["outcome_lead_id"]'),
 ("C13", D, '" WHERE lead_id=? AND state = \'pending\'"', '" WHERE lead_id=?"'),
 ("C14", D, '" WHERE lead_id=? AND state IN (\'pending\',\'failed\')"', '" WHERE lead_id=? AND state IN (\'pending\',\'failed\',\'sending\')"'),
 ("C15", D, 'if conn.execute(sql, (self._now(), lead_id)).rowcount != 1:', 'if conn.execute(sql, (self._now(), lead_id)).rowcount < 1:'),
 ("C16", D, 'self._local.token = (lead_id, int(got[0]))  # the ownership token', 'self._local.token = (lead_id, int(got[0]) + 1)  # the ownership token'),
 ("C17", D, 'return False\n                got = conn.execute("SELECT attempts FROM followups WHERE lead_id=?", (lead_id,)).fetchone()', 'return True\n                got = conn.execute("SELECT attempts FROM followups WHERE lead_id=?", (lead_id,)).fetchone()'),
 ("C18", D, 'auto_attempts=CASE WHEN state=\'failed\' THEN 1 ELSE auto_attempts+1 END, updated_at=?"\n        " WHERE lead_id=? AND state = \'pending\'"', 'auto_attempts=auto_attempts+1, updated_at=?"\n        " WHERE lead_id=? AND state = \'pending\'"'),
 ("C19", D, 'if held is not None and held[0] == lead_id:', 'if held is not None:'),
 ("C20", D, 'return "pending" if self._auto_attempts(lead_id) < SEND_MAX_ATTEMPTS else "failed"', 'return "pending" if self._auto_attempts(lead_id) <= SEND_MAX_ATTEMPTS else "failed"'),
]
only = sys.argv[1:]
def now():
    n = datetime.datetime.now(datetime.timezone.utc); i = n + datetime.timedelta(hours=5, minutes=30)
    return f"UTC {n:%Y-%m-%d %H:%M:%S} | IST {i:%Y-%m-%d %H:%M:%S}"
def sh(cmd, log, t=300):
    with open(log, "w") as fh:
        try: return subprocess.run(cmd, cwd=WT, env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=t).returncode
        except subprocess.TimeoutExpired: return "TIMEOUT"
def failed(log):
    for l in open(log, errors="replace"):
        if l.startswith("FAILED") or l.startswith("ERROR"): return l.strip()[:200]
    return ""
def run(files, log, bt):
    return sh(["timeout","300",PY,"-m","pytest","-q","-x","-p","no:cacheprovider","--tb=no",f"--basetemp=/home/user/work/q8b-tmp/{bt}",*files], log, 320)
res = []; cache = {}
for k, (mid, F, old, new) in enumerate(M):
    if only and mid not in only: continue
    orig = cache.setdefault(F, open(f"{WT}/{F}").read())
    assert orig.count(old) == 1, (mid, orig.count(old))
    open(f"{WT}/{F}", "w").write(orig.replace(old, new))
    try:
        imp = sh([PY, "-c", "import lead_desk.identity, lead_desk.desk"], f"{LOG}/{mid}-import.log", 60)
        if imp != 0: r = dict(id=mid, result="INVALID", by="does not import")
        else:
            rc = run(MAIN, f"{LOG}/{mid}-main.log", "bt")
            by = failed(f"{LOG}/{mid}-main.log")
            r = dict(id=mid, result="KILLED" if rc == 1 else ("SURVIVED" if rc == 0 else f"RC={rc}"), by=by)
            if rc == 0:
                rc2 = run(WIDE, f"{LOG}/{mid}-wide.log", "bt2")
                r["wide"] = "killed: " + failed(f"{LOG}/{mid}-wide.log") if rc2 == 1 else ("passed" if rc2 == 0 else f"RC={rc2}")
    finally:
        subprocess.run(["git", "-C", WT, "checkout", "--", F])
    r["file"], r["old"], r["new"] = F, old, new
    res.append(r)
    with open(f"{LOG}/results.jsonl", "a") as fh: fh.write(json.dumps(r) + "\n")
    if len(res) % 5 == 0:
        with open(PROG, "a") as fh: fh.write(f"{now()} | {len(res)} mutants done, last {mid} {r['result']}\n")
