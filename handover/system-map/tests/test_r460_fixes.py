import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import check_citations as cc
import scan_outputs as so


class R460(unittest.TestCase):
    def test_empty_citations_is_failure(self):
        d = tempfile.mkdtemp(); f = os.path.join(d, "a.md"); open(f, "w").write("no citations here")
        self.assertEqual(cc.main(d, os.path.join(d, "o.tsv"), [f]), 1)
    def test_parent_path_refused(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "r")); open(os.path.join(d, "x.py"), "w").write("some text here\n")
        self.assertEqual(cc.check(os.path.join(d, "r"), "../x.py", "1", "some text here"), "NO-FILE")
    def test_absolute_path_refused(self):
        d = tempfile.mkdtemp()
        self.assertEqual(cc.check(d, "/etc/passwd", "1", "root"), "NO-FILE")
    def test_anthropic_style_key_found(self):
        fake = "sk-" + "ant-api03-" + "A" * 30
        self.assertTrue(so.secrets("f", "k " + fake))
    def test_other_token_kinds_found(self):
        self.assertTrue(so.secrets("f", "t " + "github_pat_" + "A" * 30))
        self.assertTrue(so.secrets("f", "t " + "eyJ" + "a" * 20 + "." + "b" * 20 + "." + "c" * 20))
        self.assertTrue(so.secrets("f", "Authorization: Bearer " + "a" * 30))
    def test_json_and_patch_files_scanned_but_tools_dir_skipped(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "work"))
        os.makedirs(os.path.join(d, "flowcheck")); os.makedirs(os.path.join(d, "tools-notes")); os.makedirs(os.path.join(d, "tools"))
        bad = "k " + "sk-" + "A" * 30
        open(os.path.join(d, "flowcheck", "f.json"), "w").write(bad)
        open(os.path.join(d, "tools-notes", "n.md"), "w").write(bad)
        open(os.path.join(d, "tools", "t.py"), "w").write(bad)
        res = so.run(d)
        self.assertTrue(any("f.json" in x for x in res))
        self.assertTrue(any("tools-notes" in x for x in res))
        self.assertFalse(any(x.startswith(os.path.join("tools", "t.py")) for x in res))


if __name__ == "__main__":
    unittest.main()
