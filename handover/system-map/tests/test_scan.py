import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import scan_outputs as so

GOOD = "\n".join(f"## {h}\nNONE FOUND: x" for h in so.LANE_HEADS)


class Scan(unittest.TestCase):
    def test_blank_cell(self):
        t = GOOD.replace("## Components\nNONE FOUND: x", "## Components\n| a | b |\n|---|---|\n| 1 |  |", 1)
        self.assertTrue(so.empty_fields("L", t, so.LANE_HEADS))
    def test_missing_heading(self):
        self.assertTrue(so.empty_fields("L", GOOD.replace("## Jobs", "## Other"), so.LANE_HEADS))
    def test_clean(self): self.assertEqual(so.empty_fields("L", GOOD, so.LANE_HEADS), [])
    def test_second_needed_without_exception_fails(self):
        t = "## Job: STORE\nOwner: a | e\n| copy | verdict | exception |\n|---|---|---|\n| a | OWNER | none |\n| b | NEEDED | none |\n"
        self.assertTrue(so.owner_count(t))
    def test_exception_passes(self):
        t = "## Job: STORE\nOwner: a | e\n| copy | verdict | exception |\n|---|---|---|\n| a | OWNER | none |\n| b | NEEDED | EX-1 |\n"
        self.assertEqual(so.owner_count(t), [])
    def test_secret_found_and_literal_allowed(self):
        fake = "AKIA" + "ABCDEFGHIJKLMNOP"
        self.assertTrue(so.secrets("f", "key " + fake))
        self.assertEqual(so.secrets("f", "key AKIAIOSFODNN7EXAMPLE"), [])
    def test_noreply_allowed(self): self.assertEqual(so.secrets("f", "Co-Authored-By: X <noreply@anthropic.com>"), [])
    def test_partial_flag_required(self):
        t = "## Coverage\n| path | bytes | status | note |\n|---|---|---|---|\n| a | 1 | NOT-READ | |\n"
        self.assertTrue(so.coverage("L", t))
        self.assertEqual(so.coverage("L", t + "PARTIAL"), [])
    def test_two_owner_lines_fail(self):
        self.assertTrue(so.owner_count("## Job: STORE\nOwner: a\nOwner: b\n"))
    def test_coverage_status(self):
        t = "## Coverage\n| path | bytes | status | note |\n|---|---|---|---|\n| a | 1 | MAYBE | |\n"
        self.assertTrue(so.coverage("L", t))

    def test_lowercase_and_mixed_sk_keys_found(self):
        self.assertTrue(so.secrets("f", "k=" + "sk-" + "abcdefghij" * 3))
        self.assertTrue(so.secrets("f", "k=" + "sk-" + "aB" * 12))
        self.assertTrue(so.secrets("f", "k=" + "sk-" + "proj-" + "abcdefghijklmnopqrstuvwx"))

    def test_sk_identifier_and_inside_words_not_flagged(self):
        self.assertEqual(so.secrets("f", "use " + "sk-address-required-after-v2" + " here"), [])
        self.assertEqual(so.secrets("f", "the task-assignment-requirements-for-all-users list"), [])

    def test_email_any_case_tld(self):
        for tld in (".com", ".COM", ".Com"):
            self.assertTrue(so.secrets("f", "who" + "@" + "corp" + tld), tld)
        self.assertEqual(so.secrets("f", "who" + "@" + "Example" + ".COM"), [])

    def test_run_scans_tools_tests_odd_extensions_and_skips_binary(self):
        import tempfile
        base = tempfile.mkdtemp()
        os.makedirs(os.path.join(base, "work"))
        fake = "AKIA" + "ABCDEFGHIJKLMNOP"
        for rel in ("tools/x.py", "tests/y.py", "z.cfg", "sub/noext"):
            os.makedirs(os.path.dirname(os.path.join(base, rel)), exist_ok=True)
            with open(os.path.join(base, rel), "w") as fh:
                fh.write("key " + fake + "\n")
        with open(os.path.join(base, "bin.dat"), "wb") as fh:
            fh.write(b"\0\0" + fake.encode())
        out = "\n".join(so.run(base))
        for rel in ("tools/x.py", "tests/y.py", "z.cfg", "sub/noext"):
            self.assertIn(os.path.normpath(rel), out)
        self.assertNotIn("bin.dat", out)


if __name__ == "__main__":
    unittest.main()
