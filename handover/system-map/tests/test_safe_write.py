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
        self.assertEqual(open(os.path.join(d, "a.md.bak")).read(), "hand edit")


if __name__ == "__main__":
    unittest.main()
