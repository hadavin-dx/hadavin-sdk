import os, re, shutil, subprocess, sys, tempfile, unittest

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
        """Fails if a job row used by write_outputs.py is renamed, moved or renumbered.
        PIN is a second copy of the PIN dict in tools/write_outputs.py: add new ids to both."""
        rows = {}
        with open(os.path.join(BASE, "work", "L6.md"), encoding="utf-8") as f:
            for l in f:
                m = re.match(r"\| (L6-J-\d+) \|", l)
                if m:
                    rows[m.group(1)] = [x.strip() for x in l.strip().strip("|").split(" | ")][1]
        self.assertEqual(len(PIN), 48)
        for jid, name in PIN.items():
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
        block, seen = None, {}
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
        self.assertEqual(seen.get("L6-J-001"), "STORE")
        self.assertEqual(seen.get("L6-J-015"), "LOG")
        self.assertEqual(len(seen), len(set(seen)))
        self.assertGreater(len(seen), 40)

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
        """B4-9: 'Fix plan row N' in the generated files is generated from the fix plan list, not typed in."""
        d = self._copy_sm()
        r = self._run(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = open(os.path.join(d, "SWEEP.md"), encoding="utf-8").read()
        self.assertNotIn("@FIXROW", text)
        table = {}
        sec = text[text.index("Fix plan"):]
        for m in re.finditer(r"^\| (\d+) \| [^|]*\| ([^|]*) \|", sec, re.M):
            table[m.group(1)] = m.group(2)
        for m in re.finditer(r"Fix plan row (\d+)", text):
            self.assertIn(m.group(1), table)
        self.assertIn("L6-FD-001", table.get("1", ""))
        self.assertIn("L2-FD-018", table.get("7", ""))


if __name__ == "__main__":
    unittest.main()
