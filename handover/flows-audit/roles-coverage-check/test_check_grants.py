"""Mutation tests for check_grants_cover_queries.py. Run, from this folder:
python3 -m unittest -v test_check_grants   (no -I: it would hide this folder from the import path).
Env SCRIPT=<path> runs the tests against another copy of the script. The script is run in this
process the way `python3 script.py ...` runs it (runpy, as __main__), output and exit code captured."""

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import runpy
import shutil
import sys
import tempfile
import traceback
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = os.environ.get("SCRIPT", str(HERE / "check_grants_cover_queries.py"))
DOC = HERE.parent / "ROLES-PROPOSAL.md"
REAL = HERE.parent.parent / "demo" / "n8n-flows-real-v5"


def run(*args):
    buf, rc = io.StringIO(), 0
    old_argv = sys.argv
    sys.argv = [SCRIPT, *map(str, args)]
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                runpy.run_path(SCRIPT, run_name="__main__")
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 1
            except (
                OSError,
                ValueError,
                LookupError,
                TypeError,
                AttributeError,
                RecursionError,
            ):  # an uncaught error is what "Traceback" in the output stands for
                buf.write(traceback.format_exc())
                rc = 1
    finally:
        sys.argv = old_argv
    return rc, buf.getvalue()


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
        self.edit_doc(
            "GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
            "GRANT SELECT ON mf_leads TO mf_sub;",
        )
        self.assertFails("table-level")

    def test_g7b_extra_column_grant(self):
        self.edit_doc(
            "GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
            "GRANT SELECT (lead_key, claim_token, state, mail_sent, email, name) ON mf_leads TO mf_sub;",
        )
        self.assertFails("unused grant SELECT ['email', 'name'] for mf_sub")

    def test_grant_on_second_table(self):
        self.edit_doc(
            "GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
            "GRANT SELECT (lead_key) ON secret_other TO mf_sub;\n"
            "GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;",
        )
        self.assertFails("secret_other")

    def test_f3_delete(self):
        self.set_query(
            "mf-sub-crm-mail", "MarkDone", lambda q: "DELETE FROM mf_leads WHERE lead_key=$1;"
        )
        self.assertFails("DELETE")

    def test_f3b_truncate_and_other_kind(self):
        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: "TRUNCATE mf_leads;")
        self.assertFails("not allowed")

    def test_f3c_delete_hidden_in_second_statement(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "SELECT state FROM mf_leads WHERE lead_key=$1; DELETE FROM mf_leads;",
        )
        self.assertFails("DELETE")

    def test_f4_second_table(self):
        self.set_query(
            "mf-form", "Stored", lambda q: "SELECT state FROM secret_other WHERE lead_key=$1;"
        )
        self.assertFails("secret_other")

    def test_f4b_join_second_table(self):
        self.set_query(
            "mf-form",
            "Stored",
            lambda q: "SELECT state FROM mf_leads JOIN secret_other ON true WHERE lead_key=$1;",
        )
        self.assertFails("secret_other")

    def test_f1_new_column_read(self):
        self.set_query(
            "mf-sub-crm-mail", "MarkDone", lambda q: q.replace("state='processing'", "email='x'", 1)
        )
        self.assertFails("UNCOVERED")

    def test_zero_postgres_nodes(self):
        e = self.tmp / "empty"
        e.mkdir()
        (e / "mf-form.json").write_text(
            json.dumps({"nodes": [{"type": "n8n-nodes-base.set", "name": "x"}]})
        )
        self.assertFails("zero Postgres nodes", extra=(e,))

    def test_empty_folder(self):
        e = self.tmp / "empty2"
        e.mkdir()
        self.assertFails("zero Postgres nodes", extra=(e,))

    def test_nonexistent_folder(self):
        self.assertFails("folder does not exist", extra=(self.tmp / "nope",))

    def test_missing_role_clean_message(self):
        self.edit_doc(
            "GRANT SELECT (lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts) ON mf_leads TO mf_alert;",
            "",
        )
        self.edit_doc(
            "GRANT UPDATE (alert_until, alert_token, alert_attempts, alert_sent, updated_at)                  ON mf_leads TO mf_alert;",
            "",
        )
        self.assertFails("login mf_alert has no grants")

    def test_malformed_json_clean_message(self):
        (self.flows / "mf-hook.json").write_text("{bad json")
        self.assertFails("cannot read flow file")

    def test_missing_doc(self):
        self.doc.unlink()
        self.assertFails("cannot read roles document")

    def test_grant_removed_in_doc_uncovered(self):
        self.edit_doc(
            "GRANT SELECT (lead_key, state, claim_token)", "GRANT SELECT (lead_key, state)"
        )
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
        self.assertEqual(
            g["mf_door"]["insert"],
            {"lead_key", "email", "name", "state", "claimed_until", "claim_token", "attempts"},
        )
        self.assertFalse(hasattr(m, "G"), "grants must not be hardcoded in the script")


PGT = "n8n-nodes-base.postgres"
GOOD = {
    "mf_door": "n8n-publish-pg-door",
    "mf_sub": "n8n-publish-pg-sub",
    "mf_recover": "n8n-publish-pg-recover",
    "mf_alert": "n8n-publish-pg-alert",
}


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
        self.add_node(
            "mf-form",
            {
                "name": "Sneaky",
                "type": "n8n-nodes-base.code",
                "parameters": {"jsCode": "const q = 'DELETE FROM mf_leads';"},
            },
        )
        self.assertFails("Sneaky")

    def test_f6b_mysql_type_node(self):
        self.add_node(
            "mf-form", {"name": "M", "type": "n8n-nodes-base.mySql", "parameters": {"query": "x"}}
        )
        self.assertFails("database node type")

    def test_f6c_postgres_tool_node(self):
        self.add_node(
            "mf-form", {"name": "T", "type": "n8n-nodes-base.postgresTool", "parameters": {}}
        )
        self.assertFails("database node type")

    def test_f6d_sql_text_in_set_node(self):
        self.add_node(
            "mf-form",
            {
                "name": "S",
                "type": "n8n-nodes-base.set",
                "parameters": {
                    "values": {"string": [{"name": "q", "value": "DROP TABLE mf_leads"}]}
                },
            },
        )
        self.assertFails("SQL-like text")

    def test_f6e_innocent_node_text_not_flagged(self):
        self.add_node(
            "mf-form",
            {
                "name": "Ok",
                "type": "n8n-nodes-base.set",
                "parameters": {
                    "values": {"string": [{"name": "a", "value": "please update your details"}]}
                },
            },
        )
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    # I4c: one file with no Postgres node while the others keep theirs
    def test_i4c_file_without_postgres_node(self):
        self.edit_nodes(
            "mf-hook", lambda ns: ns.__setitem__(slice(None), [n for n in ns if n["type"] != PGT])
        )
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

        spec = importlib.util.spec_from_file_location("chk", HERE / "check_grants_cover_queries.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for flow in m.EXPECTED_FLOWS:

            def setc(ns, flow=flow):
                for n in ns:
                    if n["type"] == PGT:
                        login = m.NODE_LOGIN.get((flow, n["name"])) or m.SUB
                        n["credentials"] = {
                            "postgres": {"id": "x", "name": mapping.get(login, "wrong")}
                        }

            self.edit_nodes(flow, setc)

    def test_s3_old_shared_credential_rejected(self):
        rc, out = run("--roles-doc", self.doc, "--require-new-credentials", self.flows)
        self.assertEqual(rc, 1, out)
        self.assertIn("still uses the old shared credential", out)

    def test_s3_correct_credentials_pass(self):
        self.creds(GOOD)
        rc, out = run("--roles-doc", self.doc, "--require-new-credentials", self.flows)
        self.assertEqual(rc, 0, out)

    def test_s3_wrong_credential_for_login(self):
        self.creds(dict(GOOD, mf_sub="n8n-publish-pg-door"))
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
        self.set_query(
            "mf-sub-crm-mail", "MarkDone", lambda q: q.replace("RETURNING lead_key", "RETURNING *")
        )
        self.assertFails("SELECT * / RETURNING *")

    def test_s4_insert_without_column_list(self):
        self.set_query(
            "mf-form", "Claim", lambda q: "INSERT INTO mf_leads VALUES ($1,$2,$3,'x',now(),'t',0);"
        )
        self.assertFails("INSERT without a column list")

    def test_s4_update_from(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "UPDATE mf_leads SET state='done' FROM mf_leads WHERE lead_key=$1;",
        )
        self.assertFails("UPDATE ... FROM")

    def test_s4_cte_write(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: (
                "UPDATE mf_leads SET state='done' WHERE lead_key IN "
                "(WITH d AS (DELETE FROM mf_leads RETURNING lead_key) SELECT lead_key FROM d);"
            ),
        )
        self.assertFails("WITH (CTE) not allowed")

    def test_s4_copy(self):
        self.set_query("mf-form", "Stored", lambda q: "COPY mf_leads TO '/tmp/x';")
        self.assertFails("COPY")

    # S5
    def test_s5_uppercase_column_is_read(self):
        self.set_query(
            "mf-sub-crm-mail", "MarkDone", lambda q: q.replace("state='processing'", "EMAIL='x'", 1)
        )
        self.assertFails("UNCOVERED")

    def test_s5_mixed_case_write(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: q.replace("SET state='done'", "SET Name='z', state='done'", 1),
        )
        self.assertFails("UNCOVERED [('UPDATE', 'name')]")

    def test_s5_quoted_name(self):
        self.set_query(
            "mf-form", "Stored", lambda q: 'SELECT state FROM "mf_leads" WHERE lead_key=$1;'
        )
        self.assertFails("quoted name")


class Round5(Base):
    """Round 5: malformed shapes, text outside the query, disabled nodes, size limit, string literals."""

    def put(self, flow, fn):
        f = self.flows / f"{flow}.json"
        d = json.loads(f.read_text())
        d = fn(d)
        f.write_text(json.dumps(d))

    def pg(self, d, name="Stored"):
        return next(n for n in d["nodes"] if n["type"] == PGT and n["name"] == name)

    def assertClean(self, text):
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertNotIn("Traceback", out)
        self.assertIn(text, out)

    # (2) malformed shapes: each must be rc=1 with one clean message, no traceback
    SHAPES = (
        ("nodes_null", lambda d: dict(d, nodes=None), "'nodes' is null"),
        ("nodes_string", lambda d: dict(d, nodes="abc"), "'nodes' is str"),
        ("nodes_object", lambda d: dict(d, nodes={"a": 1}), "'nodes' is dict"),
        ("nodes_number", lambda d: dict(d, nodes=5), "'nodes' is int"),
        (
            "nodes_missing",
            lambda d: {k: v for k, v in d.items() if k != "nodes"},
            "'nodes' is null",
        ),
        ("top_list", lambda d: [d], "top level is list"),
        ("top_null", lambda d: None, "top level is null"),
        ("node_string", lambda d: dict(d, nodes=d["nodes"] + ["x"]), "is str, expected an object"),
        ("node_null", lambda d: dict(d, nodes=d["nodes"] + [None]), "is null, expected an object"),
        ("node_list", lambda d: dict(d, nodes=d["nodes"] + [[1]]), "is list, expected an object"),
    )

    def test_malformed_shapes_clean(self):
        for label, fn, text in self.SHAPES:
            with self.subTest(label):
                self.put("mf-hook", fn)
                self.assertClean(text)
                shutil.copy(REAL / "mf-hook.json", self.flows / "mf-hook.json")

    NODE_SHAPES = (
        ("parameters_string", "parameters", "abc", "'parameters' is str"),
        ("parameters_list", "parameters", [1], "'parameters' is list"),
        ("name_list", "name", ["a"], "'name' is list, expected text"),
        ("name_number", "name", 7, "'name' is int, expected text"),
        ("type_number", "type", 7, "'type' is int, expected text"),
        ("credentials_string", "credentials", "abc", "'credentials' is str"),
        (
            "credentials_postgres_string",
            "credentials",
            {"postgres": "abc"},
            "credentials.postgres is str",
        ),
    )

    def test_malformed_node_fields_clean(self):
        for label, key, value, text in self.NODE_SHAPES:
            with self.subTest(label):

                def edit(d, key=key, value=value):
                    self.pg(d)[key] = value
                    return d

                self.put("mf-form", edit)
                self.assertClean(text)
                shutil.copy(REAL / "mf-form.json", self.flows / "mf-form.json")

    def test_deeply_nested_json_clean(self):
        (self.flows / "mf-hook.json").write_text("[" * 100000 + "]" * 100000)
        self.assertClean("cannot read flow file")

    def test_non_utf8_file_clean(self):
        (self.flows / "mf-hook.json").write_bytes(b"\xff\xfe{")
        self.assertClean("cannot read flow file")

    # (3) SQL text outside the query field of a Postgres node
    def test_sql_in_postgres_node_notes(self):
        self.put("mf-form", lambda d: self.pg(d).update(notes="DELETE FROM mf_leads") or d)
        self.assertClean("notes or another parameter of a Postgres node")

    def test_sql_in_postgres_other_parameter(self):
        self.put(
            "mf-form",
            lambda d: (
                self.pg(d)["parameters"].update(options={"queryReplacement": "DROP TABLE mf_leads"})
                or d
            ),
        )
        self.assertClean("notes or another parameter of a Postgres node")

    def test_plain_notes_on_postgres_node_not_flagged(self):
        self.put("mf-form", lambda d: self.pg(d).update(notes="claims the lead once") or d)
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    # (4) disabled nodes
    def test_disabled_postgres_node_flagged(self):
        self.put("mf-form", lambda d: self.pg(d).update(disabled=True) or d)
        self.assertClean("node is disabled")

    def test_disabled_text_value_flagged(self):
        self.put("mf-form", lambda d: self.pg(d).update(disabled="true") or d)
        self.assertClean("node is disabled")

    def test_disabled_false_not_flagged(self):
        self.put("mf-form", lambda d: self.pg(d).update(disabled=False) or d)
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    def test_disabled_node_with_bad_query_still_read(self):
        def edit(d):
            n = self.pg(d)
            n["disabled"] = True
            n["parameters"]["query"] = "DROP TABLE mf_leads;"
            return d

        self.put("mf-form", edit)
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("node is disabled", out)
        self.assertIn("'drop' not allowed", out)

    # (5) size limit
    def test_big_flow_file_refused_unread(self):
        f = self.flows / "mf-hook.json"
        d = json.loads(f.read_text())
        d["pad"] = "x" * (5 * 1024 * 1024 + 10)
        f.write_text(json.dumps(d))
        self.assertClean("over the 5242880 byte limit")

    def test_flow_file_just_under_limit_read(self):
        f = self.flows / "mf-hook.json"
        d = json.loads(f.read_text())
        d["pad"] = "x" * (4 * 1024 * 1024)
        f.write_text(json.dumps(d))
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    def test_big_roles_document_refused(self):
        self.doc.write_text(self.doc.read_text() + "\n" + "x" * (5 * 1024 * 1024 + 10))
        self.assertFails("over the 5242880 byte limit")

    # (6) forbidden words inside string literals, dollar quotes, unbalanced quotes
    def test_delete_inside_string_literal_flagged(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "UPDATE mf_leads SET state='DELETE FROM mf_leads' WHERE lead_key=$1;",
        )
        self.assertFails("forbidden keyword DELETE inside a string literal")

    def test_drop_inside_escaped_literal_flagged(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "UPDATE mf_leads SET state='it''s a drop table' WHERE lead_key=$1;",
        )
        self.assertFails("forbidden keyword DROP inside a string literal")

    def test_harmless_literal_not_flagged(self):
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    def test_dollar_quote_flagged(self):
        self.set_query(
            "mf-form", "Stored", lambda q: "SELECT state FROM mf_leads WHERE lead_key=$$x$$;"
        )
        self.assertFails("dollar-quoted string not allowed")

    def test_unbalanced_quote_flagged(self):
        self.set_query(
            "mf-form", "Stored", lambda q: "SELECT state FROM mf_leads WHERE lead_key='x;"
        )
        self.assertFails("unbalanced single quote")

    # round 6: tests that kill three surviving mutants, and the table-name case decision
    def load_script(self):
        spec = importlib.util.spec_from_file_location("check_under_test", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_main_safety_net_unexpected_error_is_one_clean_line(self):
        """An unexpected error type inside run() ends as one FAIL line, rc=1, no traceback.
        Each type the net names is forced, so the test does not depend on the stack size."""
        mod = self.load_script()
        for exc in (OSError, ValueError, LookupError, TypeError, AttributeError, RecursionError):

            def boom(*_a, _exc=exc, **_k):
                raise _exc("made-up failure")

            buf = io.StringIO()
            with (
                mock.patch.object(mod, "run", boom),
                contextlib.redirect_stdout(buf),
                contextlib.redirect_stderr(buf),
            ):
                rc = mod.main(["--roles-doc", str(self.doc), str(self.flows)])
            out = buf.getvalue()
            self.assertEqual(rc, 1, out)
            self.assertEqual(len(out.strip().splitlines()), 1, out)
            self.assertTrue(out.startswith("FAIL internal error while checking"), out)
            self.assertIn(exc.__name__, out)
            self.assertNotIn("Traceback", out)

    def test_real_input_overflowing_the_stack_is_clean(self):
        """A very deeply nested parameter can overflow the stack inside the check (the exact depth
        depends on the interpreter, so a range is tried): never a traceback, and at least one depth
        must reach the safety net."""
        seen_internal = False
        base = json.loads((self.flows / "mf-form.json").read_text())
        for depth in range(900, 1001, 5):
            x = "s"
            for _ in range(depth):
                x = [x]
            node = {"name": "deep", "type": "n8n-nodes-base.set", "parameters": {"v": x}}
            (self.flows / "mf-form.json").write_text(
                json.dumps(dict(base, nodes=[*base["nodes"], node]))
            )
            rc, out = self.check()
            self.assertNotIn("Traceback", out)
            if rc == 1:
                fails = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
                self.assertEqual(len(fails), 1, out)
                seen_internal = seen_internal or "internal error" in out
        self.assertTrue(seen_internal, "no depth reached the safety net on this interpreter")

    def test_literal_starting_with_escaped_quote_is_one_literal(self):
        # The text after SET state= is ONE literal that holds: 'drop table
        # A parser that ignores the doubled quote sees an empty literal, a bare DROP and a lone quote.
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "UPDATE mf_leads SET state='''drop table' WHERE lead_key=$1;",
        )
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("forbidden keyword DROP inside a string literal", out)
        self.assertNotIn("unbalanced", out)
        self.assertNotIn("Traceback", out)

    def test_literal_starting_with_escaped_quote_harmless_is_balanced(self):
        self.set_query(
            "mf-sub-crm-mail",
            "MarkDone",
            lambda q: "UPDATE mf_leads SET state='''ok' WHERE lead_key=$1;",
        )
        rc, out = self.check()
        self.assertNotIn("unbalanced", out)
        self.assertNotIn("inside a string literal", out)
        self.assertNotIn("Traceback", out)

    def add_note_node(self, notes):
        node = {
            "name": "Note holder",
            "type": "n8n-nodes-base.set",
            "parameters": {},
            "notes": notes,
        }
        self.put("mf-form", lambda d: dict(d, nodes=[*d["nodes"], node]))

    def test_sql_in_notes_of_non_postgres_node(self):
        self.add_note_node("SELECT email FROM mf_leads")
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("SQL-like text in a 'n8n-nodes-base.set' node", out)
        self.assertIn("Note holder", out)

    def test_plain_notes_on_non_postgres_node_not_flagged(self):
        self.add_note_node("sets the greeting")
        rc, out = self.check()
        self.assertEqual(rc, 0, out)

    def test_uppercase_table_name_is_the_same_table_by_decision(self):
        """Decision (round 6): MF_LEADS passes. Postgres folds an unquoted name to lower case, so
        MF_LEADS and mf_leads are the same table; names are compared in lower case on purpose.
        A quoted "MF_LEADS" would be a different table and is refused (quoted names not allowed)."""
        self.set_query(
            "mf-form", "Stored", lambda q: "SELECT state FROM MF_LEADS WHERE lead_key=$1;"
        )
        rc, out = self.check()
        self.assertNotIn("touches table", out)
        self.assertNotIn("Traceback", out)
        self.set_query(
            "mf-form", "Stored", lambda q: 'SELECT state FROM "MF_LEADS" WHERE lead_key=$1;'
        )
        self.assertFails("quoted name not allowed")

    # (7) the README command
    def test_readme_unittest_command_has_no_dash_i(self):
        text = (HERE / "README.md").read_text()
        self.assertIn("python3 -m unittest -v test_check_grants", text)
        self.assertNotIn("-I -m unittest", text)


if __name__ == "__main__":
    unittest.main()
