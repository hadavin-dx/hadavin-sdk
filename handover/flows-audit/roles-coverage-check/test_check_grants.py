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


PGT = "n8n-nodes-base.postgres"


class Round4(Base):
    """Round 4: nodes the first versions did not read, and the review items S1 to S5."""

    def flow(self, name):
        f = self.flows / f"{name}.json"
        return f, json.loads(f.read_text())

    def add_node(self, flow, node):
        f, d = self.flow(flow)
        d["nodes"].append(node)
        f.write_text(json.dumps(d))

    def edit_nodes(self, flow, fn):
        f, d = self.flow(flow)
        fn(d["nodes"])
        f.write_text(json.dumps(d))

    # F6a-d: SQL or database access in a node that is not the checked Postgres node
    def test_f6a_sql_in_code_node(self):
        self.add_node("mf-form", {"name": "Sneaky", "type": "n8n-nodes-base.code",
                                  "parameters": {"jsCode": "const q = 'DELETE FROM mf_leads';"}})
        self.assertFails("Sneaky")

    def test_f6b_mysql_type_node(self):
        self.add_node("mf-form", {"name": "M", "type": "n8n-nodes-base.mySql", "parameters": {"query": "x"}})
        self.assertFails("database node type")

    def test_f6c_postgres_tool_node(self):
        self.add_node("mf-form", {"name": "T", "type": "n8n-nodes-base.postgresTool", "parameters": {}})
        self.assertFails("database node type")

    def test_f6d_sql_text_in_set_node(self):
        self.add_node("mf-form", {"name": "S", "type": "n8n-nodes-base.set",
                                  "parameters": {"values": {"string": [{"name": "q", "value": "DROP TABLE mf_leads"}]}}})
        self.assertFails("SQL-like text")

    def test_f6e_innocent_node_text_not_flagged(self):
        self.add_node("mf-form", {"name": "Ok", "type": "n8n-nodes-base.set",
                                  "parameters": {"values": {"string": [{"name": "a", "value": "please update your details"}]}}})
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    # I4c: one file with no Postgres node while the others keep theirs
    def test_i4c_file_without_postgres_node(self):
        self.edit_nodes("mf-hook", lambda ns: ns.__setitem__(slice(None), [n for n in ns if n["type"] != PGT]))
        self.assertFails("mf-hook: this file has zero Postgres nodes")

    # S1
    def test_s1_no_folder_given(self):
        rc, out = run("--roles-doc", self.doc)
        self.assertEqual(rc, 1, out)
        self.assertIn("no flow folder given", out)

    def test_s1_wrong_folder_missing_file(self):
        (self.flows / "mf-recovery.json").unlink()
        self.assertFails("flow files are")

    def test_s1_wrong_node_count(self):
        def drop_one(ns):
            for i, n in enumerate(ns):
                if n["type"] == PGT and n["name"] == "Stored":
                    del ns[i]
                    return
        self.edit_nodes("mf-form", drop_one)
        self.assertFails("13 postgres nodes, expected 14")

    # S2
    def test_s2_operation_not_execute_query(self):
        def op(ns):
            for n in ns:
                if n["type"] == PGT and n["name"] == "Stored":
                    n["parameters"]["operation"] = "deleteTable"
        self.edit_nodes("mf-form", op)
        self.assertFails("only executeQuery is checked")

    def test_s2_expression_query(self):
        self.set_query("mf-form", "Stored", lambda q: "=" + q)
        self.assertFails("n8n expression")

    def test_s2_missing_operation(self):
        def op(ns):
            for n in ns:
                if n["type"] == PGT and n["name"] == "Stored":
                    del n["parameters"]["operation"]
        self.edit_nodes("mf-form", op)
        self.assertFails("only executeQuery is checked")

    # S3
    def creds(self, mapping):
        """Point every Postgres node at the credential for its login."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("chk", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for flow in m.EXPECTED_FLOWS:
            def setc(ns, flow=flow):
                for n in ns:
                    if n["type"] == PGT:
                        login = m.NODE_LOGIN.get((flow, n["name"])) or m.SUB
                        n["credentials"] = {"postgres": {"id": "x", "name": mapping.get(login, "wrong")}}
            self.edit_nodes(flow, setc)

    GOOD = {"mf_door": "n8n-publish-pg-door", "mf_sub": "n8n-publish-pg-sub",
            "mf_recover": "n8n-publish-pg-recover", "mf_alert": "n8n-publish-pg-alert"}

    def test_s3_old_shared_credential_rejected(self):
        rc, out = run("--roles-doc", self.doc, "--require-new-credentials", self.flows)
        self.assertEqual(rc, 1, out)
        self.assertIn("still uses the old shared credential", out)

    def test_s3_correct_credentials_pass(self):
        self.creds(self.GOOD)
        rc, out = run("--roles-doc", self.doc, "--require-new-credentials", self.flows)
        self.assertEqual(rc, 0, out)

    def test_s3_wrong_credential_for_login(self):
        self.creds(dict(self.GOOD, mf_sub="n8n-publish-pg-door"))
        rc, out = run("--roles-doc", self.doc, "--require-new-credentials", self.flows)
        self.assertEqual(rc, 1, out)
        self.assertIn("is not 'n8n-publish-pg-sub'", out)

    def test_s3_missing_credential(self):
        def nocred(ns):
            for n in ns:
                if n["type"] == PGT and n["name"] == "Stored":
                    n.pop("credentials")
        self.edit_nodes("mf-form", nocred)
        self.assertFails("no postgres credential")

    # S4
    def test_s4_select_star(self):
        self.set_query("mf-form", "Stored", lambda q: "SELECT * FROM mf_leads WHERE lead_key=$1;")
        self.assertFails("SELECT *")

    def test_s4_returning_star(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q.replace("RETURNING lead_key", "RETURNING *"))
        self.assertFails("SELECT * / RETURNING *")

    def test_s4_insert_without_column_list(self):
        self.set_query("mf-form", "Claim", lambda q: "INSERT INTO mf_leads VALUES ($1,$2,$3,'x',now(),'t',0);")
        self.assertFails("INSERT without a column list")

    def test_s4_update_from(self):
        self.set_query("mf-sub-crm-mail", "MarkDone",
                       lambda q: "UPDATE mf_leads SET state='done' FROM mf_leads WHERE lead_key=$1;")
        self.assertFails("UPDATE ... FROM")

    def test_s4_cte_write(self):
        self.set_query("mf-sub-crm-mail", "MarkDone",
                       lambda q: "UPDATE mf_leads SET state='done' WHERE lead_key IN "
                                 "(WITH d AS (DELETE FROM mf_leads RETURNING lead_key) SELECT lead_key FROM d);")
        self.assertFails("WITH (CTE) not allowed")

    def test_s4_copy(self):
        self.set_query("mf-form", "Stored", lambda q: "COPY mf_leads TO '/tmp/x';")
        self.assertFails("COPY")

    # S5
    def test_s5_uppercase_column_is_read(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q.replace("state='processing'", "EMAIL='x'", 1))
        self.assertFails("UNCOVERED")

    def test_s5_mixed_case_write(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q.replace("SET state='done'", "SET Name='z', state='done'", 1))
        self.assertFails("UNCOVERED [('UPDATE', 'name')]")

    def test_s5_quoted_name(self):
        self.set_query("mf-form", "Stored", lambda q: 'SELECT state FROM "mf_leads" WHERE lead_key=$1;')
        self.assertFails("quoted name")


if __name__ == "__main__":
    unittest.main()
