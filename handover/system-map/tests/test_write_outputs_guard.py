import os, shutil, subprocess, sys, tempfile, unittest

BASE = os.path.join(os.path.dirname(__file__), "..")


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


if __name__ == "__main__":
    unittest.main()
