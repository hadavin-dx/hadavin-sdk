import os, shutil, subprocess, sys, tempfile, unittest

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "tools"))
from safe_write import adopt


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


if __name__ == "__main__":
    unittest.main()
