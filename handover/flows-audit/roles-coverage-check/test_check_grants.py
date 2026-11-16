"""Mutation tests for check_grants_cover_queries.py. Run: python3 -I -m unittest test_check_grants
(from this folder). Env SCRIPT=<path> runs the tests against another copy of the script."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = os.environ.get("SCRIPT", str(HERE / "check_grants_cover_queries.py"))
DOC = HERE.parent / "ROLES-PROPOSAL.md"
REAL = HERE.parent.parent / "demo" / "n8n-flows-real-v5"


def run(*args):
    p = subprocess.run([sys.executable, "-I", SCRIPT, *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.flows = self.tmp / "flows"
        shutil.copytree(REAL, self.flows)
        self.doc = self.tmp / "ROLES-PROPOSAL.md"
        shutil.copy(DOC, self.doc)

    def check(self, *extra_folders):
        return run("--roles-doc", self.doc, self.flows, *extra_folders)

    def set_query(self, flow, node, fn):
        f = self.flows / f"{flow}.json"
        d = json.loads(f.read_text())
        for n in d["nodes"]:
            if n["name"] == node:
                n["parameters"]["query"] = fn(n["parameters"]["query"])
        f.write_text(json.dumps(d))

    def edit_doc(self, old, new):
        t = self.doc.read_text()
        self.assertIn(old, t)
        self.doc.write_text(t.replace(old, new, 1))

    def assertFails(self, text, extra=()):
        rc, out = self.check(*extra)
        self.assertEqual(rc, 1, out)
        self.assertIn(text, out)
        self.assertNotIn("Traceback", out)


class Tests(Base):
    def test_baseline_passes(self):
        rc, out = self.check()
        self.assertEqual(rc, 0, out)
        self.assertIn("14 postgres nodes", out)

    def test_real_default_doc_and_both_folders(self):
        film = REAL.parent / "n8n-flows-film-v5"
        rc, out = run(REAL, film)
        self.assertEqual(rc, 0, out)

    def test_g7_table_level_grant(self):
        self.edit_doc("GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
                      "GRANT SELECT ON mf_leads TO mf_sub;")
        self.assertFails("table-level")

    def test_g7b_extra_column_grant(self):
        self.edit_doc("GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
                      "GRANT SELECT (lead_key, claim_token, state, mail_sent, email, name) ON mf_leads TO mf_sub;")
        self.assertFails("unused grant SELECT ['email', 'name'] for mf_sub")

    def test_grant_on_second_table(self):
        self.edit_doc("GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
                      "GRANT SELECT (lead_key) ON secret_other TO mf_sub;\n"
                      "GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;")
        self.assertFails("secret_other")

    def test_f3_delete(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: "DELETE FROM mf_leads WHERE lead_key=$1;")
        self.assertFails("DELETE")

    def test_f3b_truncate_and_other_kind(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: "TRUNCATE mf_leads;")
        self.assertFails("not allowed")

    def test_f3c_delete_hidden_in_second_statement(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q + " DELETE FROM mf_leads;")
        self.assertFails("DELETE")

    def test_f4_second_table(self):
        self.set_query("mf-form", "Stored", lambda q: "SELECT state FROM secret_other WHERE lead_key=$1;")
        self.assertFails("secret_other")

    def test_f4b_join_second_table(self):
        self.set_query("mf-form", "Stored",
                       lambda q: "SELECT state FROM mf_leads JOIN secret_other ON true WHERE lead_key=$1;")
        self.assertFails("secret_other")

    def test_f1_new_column_read(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q.replace("state='processing'", "email='x'", 1))
        self.assertFails("UNCOVERED")

    def test_zero_postgres_nodes(self):
        e = self.tmp / "empty"
        e.mkdir()
        (e / "mf-form.json").write_text(json.dumps({"nodes": [{"type": "n8n-nodes-base.set", "name": "x"}]}))
        self.assertFails("zero Postgres nodes", extra=(e,))

    def test_empty_folder(self):
        e = self.tmp / "empty2"
        e.mkdir()
        self.assertFails("zero Postgres nodes", extra=(e,))

    def test_nonexistent_folder(self):
        self.assertFails("folder does not exist", extra=(self.tmp / "nope",))

    def test_missing_role_clean_message(self):
        self.edit_doc("GRANT SELECT (lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts) ON mf_leads TO mf_alert;", "")
        self.edit_doc("GRANT UPDATE (alert_until, alert_token, alert_attempts, alert_sent, updated_at)                  ON mf_leads TO mf_alert;", "")
        self.assertFails("login mf_alert has no grants")

    def test_malformed_json_clean_message(self):
        (self.flows / "mf-hook.json").write_text("{bad json")
        self.assertFails("cannot read flow file")

    def test_missing_doc(self):
        self.doc.unlink()
        self.assertFails("cannot read roles document")

    def test_grant_removed_in_doc_uncovered(self):
        self.edit_doc("GRANT SELECT (lead_key, state, claim_token)", "GRANT SELECT (lead_key, state)")
        self.assertFails("UNCOVERED")

    def test_script_and_document_cannot_differ(self):
        # grants are parsed from the document: the set the script uses must equal the document's
        sys.path.insert(0, str(HERE))
        try:
            import check_grants_cover_queries as m
        finally:
            sys.path.pop(0)
        g, problems = m.parse_grants(DOC)
        self.assertEqual(problems, [])
        self.assertEqual(sorted(g), ["mf_alert", "mf_door", "mf_recover", "mf_sub"])
        self.assertEqual(g["mf_door"]["insert"], {"lead_key", "email", "name", "state", "claimed_until", "claim_token", "attempts"})
        self.assertFalse(hasattr(m, "G"), "grants must not be hardcoded in the script")


if __name__ == "__main__":
    unittest.main()
