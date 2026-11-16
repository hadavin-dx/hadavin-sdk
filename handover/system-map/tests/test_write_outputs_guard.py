import os, re, shutil, subprocess, sys, tempfile, unittest

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "tools"))
from safe_write import adopt

PIN = {  # names of the job rows tools/write_outputs.py gives verdicts to (id sets at its lines 123-168)
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
        PIN is a second copy of the id sets in tools/write_outputs.py lines 123-168: add new ids there too."""
        rows = {}
        with open(os.path.join(BASE, "work", "L6.md"), encoding="utf-8") as f:
            for l in f:
                m = re.match(r"\| (L6-J-\d+) \|", l)
                if m:
                    rows[m.group(1)] = [x.strip() for x in l.strip().strip("|").split(" | ")][1]
        self.assertEqual(len(PIN), 47)
        for jid, name in PIN.items():
            self.assertIn(jid, rows, "work/L6.md has no job row %s" % jid)
            self.assertEqual(rows[jid], name, "job %s was renamed or moved; re-check the id sets in tools/write_outputs.py lines 123-168" % jid)


if __name__ == "__main__":
    unittest.main()
