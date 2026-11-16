import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import scan_outputs as so

GOOD = "\n".join(f"## {h}\nNONE FOUND: x" for h in so.LANE_HEADS)


class Scan(unittest.TestCase):
    def test_blank_cell(self):
        t = GOOD.replace("NONE FOUND: x", "| a | b |\n|---|---|\n| 1 |  |", 1)
        self.assertTrue(so.empty_fields("L", t, so.LANE_HEADS))
    def test_missing_heading(self):
        self.assertTrue(so.empty_fields("L", GOOD.replace("## Jobs", "## Other"), so.LANE_HEADS))
    def test_clean(self): self.assertEqual(so.empty_fields("L", GOOD, so.LANE_HEADS), [])
    def test_second_needed_without_exception_fails(self):
        t = "## Job: STORE\nOwner: a | e | exception: none\n| copy | verdict | exception |\n|---|---|---|\n| b | NEEDED | none |\n"
        self.assertTrue(so.owner_count(t))
    def test_exception_passes(self):
        t = "## Job: STORE\nOwner: a | e | exception: none\n| copy | verdict | exception |\n|---|---|---|\n| b | NEEDED | EX-1 |\n"
        self.assertEqual(so.owner_count(t), [])
    def test_secret_found_and_literal_allowed(self):
        fake = "AKIA" + "ABCDEFGHIJKLMNOP"
        self.assertTrue(so.secrets("f", "key " + fake))
        self.assertEqual(so.secrets("f", "key AKIAIOSFODNN7EXAMPLE"), [])
    def test_coverage_status(self):
        t = "## Coverage\n| path | bytes | status | note |\n|---|---|---|---|\n| a | 1 | MAYBE | |\n"
        self.assertTrue(so.coverage("L", t))


if __name__ == "__main__":
    unittest.main()
