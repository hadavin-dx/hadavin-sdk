import ast, os, re, shutil, subprocess, sys, tempfile, unittest

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "tools"))
from safe_write import adopt

PIN = {  # names of the job rows tools/write_outputs.py gives verdicts to (its PIN dict and the verdict tables CORE, FORCE, PROP, CONFLICT and the others)
    'L6-J-001': 'STORE place: Postgres table mf_leads (take claim and state table)',
    'L6-J-002': 'STORE place: n8n internal data (workflows, credentials, execution history)',
    'L6-J-003': 'STORE place: stage.journal file (model-call write-ahead guard)',
    'L6-J-004': 'STORE place: desk SQLite book (desk.sqlite3, lock file, wal, shm) with its portal',
    'L6-J-005': 'STORE place: desk money files (SpendLedger JSON-lines plus lock, live ledger, HubSpot and SMTP stats files)',
    'L6-J-006': 'STORE place: core Store kinds memory and postgres (with migrations 0001 to 0005, tool_calls, redaction_maps)',
    'L6-J-007': 'STORE place: core file stores qualified.jsonl and replay-records.jsonl',
    'L6-J-008': 'STORE place: ask-your-data demo files (query ledger, audit directory, cost meter plus lock, kill-switch flag, eval lock.json, eval run folders, recorded replies, seal files)',
    'L6-J-009': 'STORE place: ask-your-data demo Postgres databases (seed A, seed B, clean twin, login askdata_ro)',
    'L6-J-010': 'STORE place: kill-test rig (scratch Postgres on port 55432, fake CRM rows, fake journal, events.jsonl, mails.jsonl, control files, run folders)',
    'L6-J-011': 'STORE place: HubSpot (CRM) and Gmail (client systems of record)',
    'L6-J-012': 'STORE place: document and snapshot stores (pr-stack raw API JSON, patch and PR-text version chains, superseded patch series)',
    'L6-J-013': 'LOG place: n8n execution history (execution log of the take)',
    'L6-J-014': 'LOG place: mf_leads lifecycle rows (audit of the take)',
    'L6-J-016': 'LOG place: desk logs (desk.log, request-log page, receipts, desk-1.log, fakes.log)',
    'L6-J-017': 'LOG place: kill-rig run records (results.jsonl, RESULTS.md, run_all.progress, run folders, events.jsonl, mails.jsonl)',
    'L6-J-018': 'LOG place: session logs of the build process (demo REPORT.md 660 KB, ORDERS.md, APPLY-LIST.md, demo3 REPORT.md, register.md, cloud-register.md, blocker ledger rows)',
    'L6-J-020': 'LOG place: ask-your-data query ledger and audit directory (core LocalDirSink)',
    'L6-J-021': 'LOG place: core audit kinds (audit.chain, audit.local_dir, k1b audit sink, tool_calls rows)',
    'L6-J-022': 'LOG place: CI logs (GitHub Actions job logs, mutants, perf step)',
    'L6-J-023': 'LOG place: idle log files (crm.log, smtp.log, stage.log empty in all 126 run folders)',
    'L6-J-027': 'FILTER place: CRM upsert match on lead id OR e-mail',
    'L6-J-028': 'FILTER place: second entry flow mf-hook and the dead if nodes UnknownNewA, UnknownNew',
    'L6-J-029': 'FILTER place: desk same-lead filter, size and stall limits, receipts',
    'L6-J-030': 'FILTER place: ask-your-data gate, parse, validator C1, SQLSTATE policy, CLI ask path',
    'L6-J-031': 'FILTER place: core input filters (injection tripwire, judge, redaction, evidence check, egress allowlist, text cleaning in approvals/gate.py, k1b redaction)',
    'L6-J-032': 'FILTER place: core action gate and executor lookup (authorizer allow, needs approval, deny; idempotency-key lookup)',
    'L6-J-033': 'FILTER place: repo hygiene filters (secret scan and allowlists, scan_repo, hygiene test, nosemgrep form guard, pull-request hooks)',
    'L6-J-035': 'COUNTER place: stage.journal model-call count (the cap in effect: one call per lead)',
    'L6-J-036': 'COUNTER place: desk /counts endpoint, call caps and the fake outbox count',
    'L6-J-037': 'COUNTER place: ask-your-data cost meter, kill switch and eval counters (meter reserve and settle, sealed-run counter, test_runs)',
    'L6-J-038': 'COUNTER place: core Limits (daily and monthly caps, kill switch in Store) and k1b per-invocation budget',
    'L6-J-039': 'COUNTER place: test and run counts quoted as proof (full-suite totals, skip counts, case counts)',
    'L6-J-040': 'COUNTER place: heavy-job slot and agent-count limits (3, 4, 2 slots; 8 builders; no cap)',
    'L6-J-042': 'RETRY place: node retry on Qualify and CrmUpsert (3 tries each) inside the sub-workflow',
    'L6-J-043': 'RETRY place: alert claim and backoff (claim 720 s, backoff 60 s to 300 s) and the start-time clear of stale alert claims',
    'L6-J-044': 'RETRY place: desk reaper, locked-database retry, mirror busy wait (10, 60, 180, 420 s)',
    'L6-J-045': 'RETRY place: core runtime tick (approval sweep, reconcile, stuck-run rule to NEEDS_PERSON, checkpoint, purge)',
    'L6-J-046': 'RETRY place: core llm retry (bounded backoff with jitter)',
    'L6-J-047': 'RETRY place: core extract with one retry and DeadLetter (add_dead_letter in Store)',
    'L6-J-048': 'RETRY place: ask-your-data pipeline attempts and pgsource retry once, connect pause and watchdog',
    'L6-J-049': 'RETRY place: test-rig and session wait loops (queue scripts with sleep 5 loops, rescue copy loop, heartbeat loop, chunked run driver)',
    'L6-J-050': 'RETRY place: CI re-runs (weekly cron, curl download retry 5 times) and mutation runner setup (5 tries)',
    'L6-J-054': 'NOTICE place: desk follow-up mail and portal screens',
    'L6-J-056': 'NOTICE place: core approvals channel (Slack message with Approve and Reject)',
    'L6-J-057': 'NOTICE place: build-process notices (Dependabot, CodeRabbit review, prompt hook, weekly CI, heartbeat blocks, ORDERS cadence, questions-for-lead)',
    'L6-J-058': 'OTHER place: one shared Postgres credential and role for all nodes',
    'L6-J-059': 'OTHER place: review-round loops (round cap of 2 passed on documentation and test patches; severity rises with rounds)',
}


PLAIN = {  # the 11 rows tools/write_outputs.py registers without a verdict table (its PLAIN dict)
    'L6-J-015': 'LOG place: process output files (n8n.out, stage stderr, take-script result.json, notices)',
    'L6-J-019': 'LOG place: lane3 evidence reports and raw logs (about 90 reports, raw/, progress notes, REPORT archive)',
    'L6-J-024': 'FILTER place: Claim insert ON CONFLICT on mf_leads (the dedupe)',
    'L6-J-025': 'FILTER place: shape check (Valid node regex) and review state',
    'L6-J-026': 'FILTER place: stage.journal repeat guard (one model call per lead key)',
    'L6-J-034': 'COUNTER place: independent count rule (one new, nine duplicate, one e-mail, one CRM row)',
    'L6-J-041': 'RETRY place: mf-recovery sweep (every 30 s, lease 120 s, at most 3 attempts, marks failed or unknown)',
    'L6-J-051': 'NOTICE place: alert mail for unknown or failed leads (AlertSend in mf-recovery)',
    'L6-J-052': 'NOTICE place: lead intake mail inside the sub-workflow',
    'L6-J-053': 'NOTICE place: proof screens for the video (n8n executions, mf_leads rows, HubSpot, Gmail)',
    'L6-J-055': 'NOTICE place: refusal and start-question messages of the desk and real-run scripts',
}


def tool_literal(name, base=BASE):
    """Reads one top-level literal (dict or set) such as PIN, PLAIN or FINGERPRINT out of tools/write_outputs.py without running the tool."""
    tree = ast.parse(open(os.path.join(base, "tools", "write_outputs.py"), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return ast.literal_eval(node.value)
    raise AssertionError("tools/write_outputs.py has no top-level %s literal" % name)


class WriteOutputsGuard(unittest.TestCase):
    def test_hand_edited_sweep_is_not_overwritten(self):
        d = os.path.join(tempfile.mkdtemp(), "sm")
        shutil.copytree(BASE, d, ignore=shutil.ignore_patterns(".git", "__pycache__", "archive"))
        gen = os.path.join(d, "hand-kept", ".generated-hashes.json")
        if os.path.exists(gen):
            os.remove(gen)
        marker = "HAND-EDIT-MARKER-91"
        with open(os.path.join(d, "SWEEP.md"), "a") as f:
            f.write("\n" + marker + "\n")
        r = subprocess.run([sys.executable, os.path.join(d, "tools", "write_outputs.py"), d],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REFUSED", r.stdout + r.stderr)
        self.assertIn(marker, open(os.path.join(d, "SWEEP.md")).read())

    def test_only_one_place_table_edited_leaves_sweep_unchanged(self):
        d = os.path.join(tempfile.mkdtemp(), "sm")
        shutil.copytree(BASE, d, ignore=shutil.ignore_patterns(".git", "__pycache__", "archive"))
        run = lambda *a: subprocess.run([sys.executable, os.path.join(d, "tools", "write_outputs.py"), d, *a], capture_output=True, text=True)
        self.assertEqual(run("--force").returncode, 0)  # valid registry for both files
        sweep, table = os.path.join(d, "SWEEP.md"), os.path.join(d, "ONE-PLACE-TABLE.md")
        marker = "STALE-MARKER-93"
        self.assertNotIn(marker, open(sweep).read())
        # control: an adopted file carrying the marker IS regenerated, so the marker can detect a rewrite
        with open(sweep, "a") as f:
            f.write("\n" + marker + "\n")
        adopt(d, "SWEEP.md")
        self.assertEqual(run().returncode, 0)
        self.assertNotIn(marker, open(sweep).read())
        # real check: SWEEP.md is adopted and carries the marker, ONE-PLACE-TABLE.md is hand-edited
        with open(sweep, "a") as f:
            f.write("\n" + marker + "\n")
        adopt(d, "SWEEP.md")
        with open(table, "a") as f:
            f.write("\nHAND-EDIT-92\n")
        r = run()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REFUSED: ONE-PLACE-TABLE.md", r.stdout + r.stderr)
        self.assertIn(marker, open(sweep).read())  # SWEEP.md was not rewritten
        self.assertIn("HAND-EDIT-92", open(table).read())

    def test_job_ids_used_by_write_outputs_still_name_the_same_jobs(self):
        """Fails if a job row used by write_outputs.py is renamed, moved or renumbered, or if the test's own copy of PIN or PLAIN
        differs from the dicts in tools/write_outputs.py (R2-4): the copies here are read against the tool source, so a name changed
        in only one place fails."""
        rows = {}
        with open(os.path.join(BASE, "work", "L6.md"), encoding="utf-8") as f:
            for l in f:
                m = re.match(r"\| (L6-J-\d+) \|", l)
                if m:
                    rows[m.group(1)] = [x.strip() for x in l.strip().strip("|").split(" | ")][1]
        self.assertEqual(len(PIN), 48)
        self.assertEqual(len(PLAIN), 11)
        self.assertEqual(tool_literal("PIN"), PIN, "PIN here differs from PIN in tools/write_outputs.py")
        self.assertEqual(tool_literal("PLAIN"), PLAIN, "PLAIN here differs from PLAIN in tools/write_outputs.py")
        self.assertFalse(set(PIN) & set(PLAIN))
        self.assertEqual(set(PIN) | set(PLAIN), set(rows), "a row of work/L6.md is in neither PIN nor PLAIN, or the reverse")
        for jid, name in {**PIN, **PLAIN}.items():
            self.assertIn(jid, rows, "work/L6.md has no job row %s" % jid)
            self.assertEqual(rows[jid], name, "job %s was renamed or moved; re-check the PIN dict and the verdict tables in tools/write_outputs.py" % jid)


    def _copy_sm(self):
        d = os.path.join(tempfile.mkdtemp(), "sm")
        shutil.copytree(BASE, d, ignore=shutil.ignore_patterns(".git", "__pycache__", "archive"))
        gen = os.path.join(d, "hand-kept", ".generated-hashes.json")
        if os.path.exists(gen):
            os.remove(gen)
        old = os.environ.get("WRITE_OUTPUTS_TOOL_UNDER_TEST")  # optional: run these tests against another copy of the tool (old-code proof)
        if old:
            shutil.copy(old, os.path.join(d, "tools", "write_outputs.py"))
        return d

    def _run(self, d):
        return subprocess.run([sys.executable, os.path.join(d, "tools", "write_outputs.py"), d, "--force"], capture_output=True, text=True)

    def _edit_l6(self, d, fn):
        path = os.path.join(d, "work", "L6.md")
        lines = open(path, encoding="utf-8").read().split("\n")
        open(path, "w", encoding="utf-8").write("\n".join(fn(lines)))

    def test_every_row_sits_in_the_block_its_pinned_name_says(self):
        """B3/B4-8: each job row in ONE-PLACE-TABLE.md sits under the block named by its own first word; L6-J-001 (a STORE row)
        is under the STORE block, L6-J-015 (a LOG row) under the LOG block, and no row is lost or doubled."""
        d = self._copy_sm()
        r = self._run(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        block, seen, ids = None, {}, []
        for line in open(os.path.join(d, "ONE-PLACE-TABLE.md"), encoding="utf-8"):
            m = re.match(r"## Job: (\w+)", line)
            if m:
                block = m.group(1)
            elif line.startswith("## Appendix"):
                block = None
            rm = re.match(r"\| (L6-J-\d+) \| (\w+) place:", line)
            if rm and block:
                self.assertEqual(rm.group(2), block, "row sits in the wrong block: " + line[:80])
                seen[rm.group(1)] = block
                ids.append(rm.group(1))
        self.assertEqual(seen.get("L6-J-001"), "STORE")
        self.assertEqual(seen.get("L6-J-015"), "LOG")
        self.assertEqual(len(ids), len(set(ids)), "a row appears twice in ONE-PLACE-TABLE.md")
        self.assertEqual(len(ids), 49, "expected the 49 job rows that sit in blocks (59 rows minus the build-process appendix)")

    def test_line_order_does_not_change_the_output(self):
        """B3/B4-2: moving a job row to another line in work/L6.md (ids travel with their content) must not change any output."""
        d = self._copy_sm()
        before = self._run(d)
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        want = open(os.path.join(d, "ONE-PLACE-TABLE.md"), encoding="utf-8").read()
        def swap(lines):
            idx = [i for i, l in enumerate(lines) if l.startswith("| L6-J-")]
            a, b = idx[7], idx[30]
            lines[a], lines[b] = lines[b], lines[a]
            return lines
        self._edit_l6(d, swap)
        r = self._run(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(open(os.path.join(d, "ONE-PLACE-TABLE.md"), encoding="utf-8").read(), want)

    def test_renumbered_rows_are_an_error_naming_the_row(self):
        """B4-1: if two rows swap ids (their content stays), verdict tables would give each verdict to the wrong row; the tool must stop."""
        d = self._copy_sm()
        path = os.path.join(d, "work", "L6.md")
        text = open(path, encoding="utf-8").read()
        text = text.replace("| L6-J-001 |", "| L6-J-TMP |").replace("| L6-J-015 |", "| L6-J-001 |").replace("| L6-J-TMP |", "| L6-J-015 |")
        open(path, "w", encoding="utf-8").write(text)
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("differs from the pinned name", out)
        self.assertIn("L6-J-001", out)
        self.assertIn("L6-J-015", out)

    def test_stale_row_id_is_an_error_not_a_silent_no_op(self):
        """B3: a verdict table that names a row id which is not in work/L6.md must stop the tool with the id named (last row deleted)."""
        d = self._copy_sm()
        self._edit_l6(d, lambda lines: [l for l in lines if not l.startswith("| L6-J-059 |")])
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("missing from work/L6.md", out)
        self.assertIn("L6-J-059", out)

    def test_mid_row_deletion_is_an_error_naming_the_row(self):
        """B4-3/B4-4: deleting a row from the middle (a table row 030, and the special-case row 043) must stop the tool and name that row."""
        for jid in ("L6-J-030", "L6-J-043"):
            with self.subTest(row=jid):
                d = self._copy_sm()
                self._edit_l6(d, lambda lines: [l for l in lines if not l.startswith("| %s |" % jid)])
                r = self._run(d)
                out = r.stdout + r.stderr
                self.assertNotEqual(r.returncode, 0, out)
                self.assertIn("missing from work/L6.md", out)
                self.assertIn(jid, out)
                self.assertNotIn("Traceback", out)

    def test_new_unregistered_row_is_an_error_naming_the_row(self):
        """B4-5: a row id that is in no registered set (a new row 060) must stop the tool, not be accepted silently."""
        d = self._copy_sm()
        def add(lines):
            last = max(i for i, l in enumerate(lines) if l.startswith("| L6-J-059 |"))
            lines.insert(last + 1, lines[last].replace("| L6-J-059 |", "| L6-J-060 |", 1))
            return lines
        self._edit_l6(d, add)
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("in no registered set", out)
        self.assertIn("L6-J-060", out)

    def test_fix_plan_row_numbers_in_the_text_match_the_fix_plan(self):
        """B4-9, R2-1: every '@FIXROW:<finding id>@' token written in tools/write_outputs.py comes out as the number of the Fix plan row whose
        'finding ids' cell holds that finding id. The number is checked at the sentence the token sits in, not against fixed numbers."""
        d = self._copy_sm()
        r = self._run(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        texts = {n: open(os.path.join(d, n), encoding="utf-8").read() for n in ("SWEEP.md", "ONE-PLACE-TABLE.md")}
        for n, t in texts.items():  # R2-7: no unresolved token in either file
            self.assertNotIn("@FIXROW", t, n)
        sweep = texts["SWEEP.md"]
        sec = sweep[sweep.index("\n## Fix plan\n"):]  # R2-6: the heading, not the first mention of the words
        table = {}
        for m in re.finditer(r"^\| (\d+) \| [^|]*\| ([^|]*) \|", sec, re.M):
            table[m.group(1)] = m.group(2)
        self.assertGreaterEqual(len(table), 11)
        for n, t in texts.items():
            for m in re.finditer(r"Fix plan rows? (\d+)", t):
                self.assertIn(m.group(1), table, "%s names a Fix plan row that does not exist" % n)
        src = open(os.path.join(BASE, "tools", "write_outputs.py"), encoding="utf-8").read()
        tokens = [(m.group(1), src[src.rfind("\n", 0, m.start()) + 1:m.start()][-45:]) for m in re.finditer(r"@FIXROW:([A-Za-z0-9-]+)@", src)]
        self.assertEqual(sorted({t[0] for t in tokens}), ["L2-FD-018", "L6-FD-001", "L6-FD-003"])
        for fid, before in tokens:
            self.assertTrue(before.endswith("Fix plan row "), before)
            found = [(n, m.group(1)) for n, t in texts.items() for m in re.finditer(re.escape(before) + r"(\d+)", t)]
            self.assertTrue(found, "the sentence for %s was not found in the generated files: %r" % (fid, before))
            for n, num in found:
                self.assertIn(fid, re.split(r"[,\s]+", table.get(num, "")),
                              "%s: 'Fix plan row %s' was written for %s but row %s holds %r" % (n, num, fid, num, table.get(num)))

    def test_fix_plan_row_check_sees_an_off_by_one(self):
        """R2-1 proof inside the suite: a copy of the tool with the row number shifted by one (enumerate(fixrows, 1) changed to 2 in _fixno) still
        exits 0, but the number it writes points at a row that does not hold the finding; this is what the check above detects."""
        d = self._copy_sm()
        tool = os.path.join(d, "tools", "write_outputs.py")
        text = open(tool, encoding="utf-8").read()
        bad = text.replace("for i, r in enumerate(fixrows, 1) if m.group(1)", "for i, r in enumerate(fixrows, 2) if m.group(1)")
        self.assertNotEqual(bad, text, "the _fixno line changed; update this mutation")
        open(tool, "w", encoding="utf-8").write(bad)
        r = self._run(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sweep = open(os.path.join(d, "SWEEP.md"), encoding="utf-8").read()
        sec = sweep[sweep.index("\n## Fix plan\n"):]
        table = {m.group(1): m.group(2) for m in re.finditer(r"^\| (\d+) \| [^|]*\| ([^|]*) \|", sec, re.M)}
        m = re.search(r"masking check first \(Fix plan row (\d+)\)", sweep)
        self.assertIsNotNone(m)
        self.assertNotIn("L6-FD-001", re.split(r"[,\s]+", table.get(m.group(1), "")))

    # ---- R2-2: re-ratings, notes, type changes and duplicate marks are pinned to the text of the finding they were written for
    def _edit_findings(self, d, fn):
        path = os.path.join(d, "work", "merged-findings.md")
        lines = open(path, encoding="utf-8").read().split("\n")
        open(path, "w", encoding="utf-8").write("\n".join(fn(lines)))

    def test_fingerprints_cover_exactly_the_keyed_findings(self):
        """R2-2: FINGERPRINT has one entry per id named in RERATE, NOTE, RETYPE or DEDUP (read from the tool source), each a text of at most 40 characters."""
        keyed = set(tool_literal("RERATE")) | set(tool_literal("NOTE")) | set(tool_literal("DEDUP")) | set(tool_literal("RETYPE"))
        fp = tool_literal("FINGERPRINT")
        self.assertEqual(set(fp), keyed)
        self.assertEqual(len(fp), 18)
        for k, v in fp.items():
            self.assertTrue(0 < len(v) <= 40, k)

    def test_reworded_finding_under_a_keyed_id_is_an_error_naming_the_id(self):
        """R2-2: if the evidence text under an id that has a re-rating or note changes (lanes renumbered, merge.py run again), the tool stops and names the id."""
        d = self._copy_sm()
        self._edit_findings(d, lambda lines: [l.replace("| When the mail server is slow", "| When the mail server is fast", 1) if l.startswith("| L2-FD-008 |") else l for l in lines])
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("L2-FD-008", out)
        self.assertIn("no longer starts with the text", out)
        self.assertNotIn("Traceback", out)

    def test_swapped_finding_ids_are_an_error_naming_an_id(self):
        """R2-2: two keyed findings swap ids (their text stays); the notes would land on the wrong finding with exit 0 before; now the tool stops."""
        d = self._copy_sm()
        def swap(lines):
            return [l.replace("| L2-FD-008 |", "| L6-TMP |", 1).replace("| L6-FD-005 |", "| L2-FD-008 |", 1).replace("| L6-TMP |", "| L6-FD-005 |", 1)
                    if l.startswith(("| L2-FD-008 |", "| L6-FD-005 |")) else l for l in lines]
        self._edit_findings(d, swap)
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("L2-FD-008", out)
        self.assertIn("no longer starts with the text", out)

    def test_every_keyed_finding_text_change_is_caught(self):
        """R2-2: for each keyed id, changing the first character of its evidence text stops the tool and names that id."""
        for fid in sorted(tool_literal("FINGERPRINT")):
            with self.subTest(finding=fid):
                d = self._copy_sm()
                def change(lines):
                    out = []
                    for l in lines:
                        if l.startswith("| %s |" % fid):
                            c = l.split(" | ")
                            c[3] = "X" + c[3][1:]
                            l = " | ".join(c)
                        out.append(l)
                    return out
                self._edit_findings(d, change)
                r = self._run(d)
                out = r.stdout + r.stderr
                self.assertNotEqual(r.returncode, 0, out)
                self.assertIn(fid, out)

    def test_new_keyed_id_without_a_fingerprint_is_an_error_naming_the_id(self):
        """R2-2: adding an id to DEDUP without a fingerprint stops the tool and names the id."""
        d = self._copy_sm()
        tool = os.path.join(d, "tools", "write_outputs.py")
        text = open(tool, encoding="utf-8").read()
        new = text.replace('DEDUP = {"L6-FD-001",', 'DEDUP = {"L2-FD-004", "L6-FD-001",', 1)
        self.assertNotEqual(new, text, "the DEDUP line changed; update this test")
        open(tool, "w", encoding="utf-8").write(new)
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("L2-FD-004", out)
        self.assertIn("FINGERPRINT", out)

    def test_renamed_row_message_gives_the_full_names_and_the_first_difference(self):
        """R2-5: the renaming error prints the whole pinned and actual name and the position of the first difference, not names cut at 50 characters."""
        d = self._copy_sm()
        path = os.path.join(d, "work", "L6.md")
        text = open(path, encoding="utf-8").read()
        old = "mf-recovery sweep (every 30 s, lease 120 s"
        self.assertIn(old, text)
        open(path, "w", encoding="utf-8").write(text.replace(old, "mf-recovery sweep (every 31 s, lease 120 s", 1))
        r = self._run(d)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("L6-J-041", out)
        self.assertIn(PLAIN["L6-J-041"], out)  # the full pinned name, over 100 characters
        self.assertIn("every 31 s", out)  # the actual name
        self.assertIn("first difference at character %d" % (PLAIN["L6-J-041"].index("30 s") + 1), out)  # "3" is shared, the "0" differs


if __name__ == "__main__":
    unittest.main()
