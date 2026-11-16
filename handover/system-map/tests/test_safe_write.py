import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from safe_write import safe_write


class SafeWrite(unittest.TestCase):
    def test_new_file_written_then_regenerated(self):
        d = tempfile.mkdtemp()
        self.assertTrue(safe_write(d, "A.md", "one"))
        self.assertTrue(safe_write(d, "A.md", "two"))
    def test_hand_edit_is_not_overwritten(self):
        d = tempfile.mkdtemp(); safe_write(d, "A.md", "one")
        open(os.path.join(d, "A.md"), "a").write("HAND EDIT")
        self.assertFalse(safe_write(d, "A.md", "two"))
        self.assertIn("HAND EDIT", open(os.path.join(d, "A.md")).read())
    def test_existing_file_without_record_is_not_overwritten(self):
        d = tempfile.mkdtemp(); open(os.path.join(d, "A.md"), "w").write("old")
        self.assertFalse(safe_write(d, "A.md", "new"))
    def test_force_overwrites(self):
        d = tempfile.mkdtemp(); open(os.path.join(d, "A.md"), "w").write("old")
        self.assertTrue(safe_write(d, "A.md", "new", force=True))



class SafeWriteHardening(unittest.TestCase):
    def test_name_outside_base_is_rejected(self):
        import tempfile
        d = tempfile.mkdtemp()
        for bad in ("../x.md", "/tmp/x.md", "hand-kept/.generated-hashes.json"):
            with self.assertRaises(ValueError):
                safe_write(d, bad, "x")

    def test_damaged_registry_gives_a_clear_error(self):
        import tempfile, os
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "hand-kept"))
        open(os.path.join(d, "hand-kept", ".generated-hashes.json"), "w").write("{trunc")
        with self.assertRaises(ValueError):
            safe_write(d, "a.md", "x")
        self.assertFalse(os.path.exists(os.path.join(d, "a.md")))

    def test_force_keeps_a_backup(self):
        import tempfile, os
        d = tempfile.mkdtemp()
        open(os.path.join(d, "a.md"), "w").write("hand edit")
        self.assertTrue(safe_write(d, "a.md", "new", force=True))
        baks = [f for f in os.listdir(d) if f.startswith("a.md.") and f.endswith(".bak")]
        self.assertEqual(len(baks), 1)
        self.assertEqual(open(os.path.join(d, baks[0])).read(), "hand edit")


    def test_two_forces_keep_both_hand_edits(self):
        import tempfile, os
        d = tempfile.mkdtemp()
        safe_write(d, "a.md", "gen1")
        open(os.path.join(d, "a.md"), "w").write("edit one")
        safe_write(d, "a.md", "gen2", force=True)
        open(os.path.join(d, "a.md"), "w").write("edit two")
        safe_write(d, "a.md", "gen3", force=True)
        texts = sorted(open(os.path.join(d, f)).read() for f in os.listdir(d) if f.endswith(".bak"))
        self.assertEqual(texts, ["edit one", "edit two"])

    def test_adopt_makes_hand_edit_the_baseline(self):
        import tempfile, os
        from safe_write import adopt, refused
        d = tempfile.mkdtemp()
        safe_write(d, "a.md", "gen")
        open(os.path.join(d, "a.md"), "w").write("edit")
        self.assertTrue(refused(d, "a.md"))
        adopt(d, "a.md")
        self.assertFalse(refused(d, "a.md"))
        self.assertEqual(open(os.path.join(d, "a.md")).read(), "edit")


if __name__ == "__main__":
    unittest.main()
