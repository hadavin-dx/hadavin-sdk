import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import merge


class Merge(unittest.TestCase):
    def test_kind(self):
        self.assertEqual(merge.kind_of("L2-WK-001"), "WK")
        self.assertEqual(merge.kind_of("L5ac-S-004"), "S")
        self.assertIsNone(merge.kind_of("nonsense"))

    def test_parse_and_merge(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "work"))
        with open(os.path.join(d, "work", "L1.md"), "w") as f:
            f.write("## Stores\n| id | name |\n|---|---|\n| L1-S-001 | x |\n## Findings\n"
                    "| id | claim type | severity | evidence | conflicts with | job key |\n|---|---|---|---|---|---|\n"
                    "| L1-FD-001 | dead | Nit | e | none | STORE |\n| L1-FD-002 | dead | Blocker | e | none | STORE |\n")
        merge.main(d)
        self.assertIn("L1-S-001", open(os.path.join(d, "MASTER-MAP.md")).read())
        fl = open(os.path.join(d, "work", "merged-findings.md")).read()
        self.assertLess(fl.index("L1-FD-002"), fl.index("L1-FD-001"))  # Blocker sorts first

    def test_hand_kept_additions_survive(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "work"))
        os.makedirs(os.path.join(d, "hand-kept"))
        with open(os.path.join(d, "work", "L1.md"), "w") as f:
            f.write("## Stores\n| id | name |\n|---|---|\n| L1-S-001 | x |\n")
        with open(os.path.join(d, "hand-kept", "MAP-ADDITIONS.md"), "w") as f:
            f.write("\n## Additions after the sweep (hand-kept)\nKEEP-ME-123\n")
        merge.main(d)
        merge.main(d)  # a second run must give the same result
        out = open(os.path.join(d, "MASTER-MAP.md")).read()
        self.assertEqual(out.count("KEEP-ME-123"), 1)


if __name__ == "__main__":
    unittest.main()
