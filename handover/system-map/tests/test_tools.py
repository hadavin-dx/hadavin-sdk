import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import check_citations as cc, partition as pt


class Cit(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, "a.txt"), "w") as f:
            f.write("one\n  hello world line  \nthree\n" + "x\n" * 10 + "far target\n")
        with open(os.path.join(self.d, "b.bin"), "wb") as f:
            f.write(b"\xff\xfe\x00 hello world\n")

    def test_found(self): self.assertEqual(cc.check(self.d, "a.txt", 2, "hello world"), "FOUND")
    def test_missing_file(self): self.assertEqual(cc.check(self.d, "zz.txt", 1, "hello world"), "NO-FILE")
    def test_drift(self): self.assertEqual(cc.check(self.d, "a.txt", 4, "hello world"), "LINE-DRIFT")
    def test_mismatch(self): self.assertEqual(cc.check(self.d, "a.txt", 2, "not there"), "MISMATCH")
    def test_far_is_mismatch(self): self.assertEqual(cc.check(self.d, "a.txt", 1, "far target"), "MISMATCH")
    def test_binary_no_crash(self): self.assertEqual(cc.check(self.d, "b.bin", 1, "hello world"), "FOUND")


class Part(unittest.TestCase):
    def test_no_rule_none(self): self.assertEqual(pt.lanes_for("handover/unknown/x"), set())
    def test_one_lane(self):
        for p, lane in [("src/a.py", "L5"), ("handover/README.md", "L1"), ("handover/demo3/REPORT.md", "L2"),
                        ("handover/demo3/evidence/x.md", "L3"), ("handover/demo/sonar/x", "L4"),
                        ("handover/demo/pr-text/x", "L1"), ("handover/demo/REPORT.md", "L1")]:
            self.assertEqual(pt.lanes_for(p), {lane}, p)
    def test_double_detected(self):
        lanes, problems = pt.partition(["handover/unknown/x"])
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
