"""Round 1 fixes (A1-A5, B1-B4, safe_write CRLF). Each test fails on the code before the fix.
write_outputs tests copy only the input tables (work/*.md) into a temp folder, never the whole tree."""
import glob, os, re, shutil, subprocess, sys, tempfile, unittest

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE, "tools"))
import scan_outputs as so, check_citations as cc, safe_write as sw  # noqa: E402


def workdir():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "work"))
    for f in ["merged-findings.md", "L6.md"] + [os.path.basename(p) for p in glob.glob(os.path.join(BASE, "work", "L*c.md"))]:
        shutil.copy(os.path.join(BASE, "work", f), os.path.join(d, "work", f))
    return d


def edit(d, name, fn):
    p = os.path.join(d, "work", name)
    t = open(p, encoding="utf-8", newline="").read()
    t2 = fn(t)
    assert t2 != t, "fixture edit changed nothing"
    open(p, "w", encoding="utf-8", newline="").write(t2)


def run_wo(d):
    r = subprocess.run([sys.executable, os.path.join(BASE, "tools", "write_outputs.py"), d], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def job_row(t, n):
    return re.search(r"^\| L6-J-%03d \|.*$" % n, t, re.M).group(0)


class WriteOutputsFixtures(unittest.TestCase):
    def test_baseline_runs(self):
        rc, out = run_wo(workdir())
        self.assertEqual(rc, 0, out)

    def test_a1_short_job_row_fails_with_id(self):
        d = workdir()
        edit(d, "L6.md", lambda t: t.replace(job_row(t, 3), " | ".join(job_row(t, 3).split(" | ")[:10])))
        rc, out = run_wo(d)
        self.assertNotEqual(rc, 0); self.assertIn("L6-J-003", out)

    def test_a1_duplicate_job_id_fails(self):
        d = workdir()
        edit(d, "L6.md", lambda t: t + "\n" + job_row(t, 3) + "\n")
        rc, out = run_wo(d)
        self.assertNotEqual(rc, 0); self.assertIn("L6-J-003", out)

    def test_a1_findings_row_with_wrong_cell_count_fails(self):
        d = workdir()
        edit(d, "merged-findings.md", lambda t: t + "\n| X-FD-999 | a | Major | b |\n")
        rc, out = run_wo(d)
        self.assertNotEqual(rc, 0); self.assertIn("X-FD-999", out)

    def test_b1_unknown_verdict_word_fails(self):
        d = workdir()
        edit(d, "L6.md", lambda t: t.replace("| OWNER of take state", "| BOGUS of take state", 1))
        rc, out = run_wo(d)
        self.assertNotEqual(rc, 0); self.assertIn("unknown verdict", out)

    def test_b2_needed_without_exception_stays_none_and_scan_reports_it(self):
        d = workdir()
        edit(d, "L6.md", lambda t: t.replace("NEEDED (exception L6-EX-01)", "NEEDED (no exception named)", 1))
        rc, out = run_wo(d)
        self.assertEqual(rc, 0, out)
        t = open(os.path.join(d, "ONE-PLACE-TABLE.md"), encoding="utf-8").read()
        self.assertTrue(so.owner_count(t), "scan_outputs must report a NEEDED row with no exception id")

    def test_b3_named_uses_whole_ids_not_substrings(self):
        d = workdir()
        edit(d, "merged-findings.md", lambda t: t + "\n| L6-FD-00 | ops | Blocker | A made-up blocker. | DECISION line 1 | STORE |\n")
        rc, out = run_wo(d)
        self.assertEqual(rc, 0, out)
        sweep = open(os.path.join(d, "SWEEP.md"), encoding="utf-8").read()
        self.assertRegex(sweep, r"\| L6-FD-00 \| A made-up blocker")

    def test_b4_rerate_id_missing_from_data_fails_naming_it(self):
        d = workdir()
        edit(d, "merged-findings.md", lambda t: re.sub(r"^\| L4-FD-004 \|.*\n", "", t, flags=re.M))
        rc, out = run_wo(d)
        self.assertNotEqual(rc, 0); self.assertIn("L4-FD-004", out)

    def test_a2_not_read_counts_come_from_coverage_tables(self):
        d = workdir()
        edit(d, "L1c.md", lambda t: t.replace("| NOT-READ |", "| READ |", 1))
        rc, out = run_wo(d)
        self.assertEqual(rc, 0, out)
        sweep = open(os.path.join(d, "SWEEP.md"), encoding="utf-8").read()
        self.assertIn("L1c 17", sweep); self.assertIn("(182 in total)", sweep)


class ScanFixes(unittest.TestCase):
    F = "## Findings\n| id | type | severity |\n|---|---|---|\n| a | x | Blocker (was Major: y) |\n| b | x | Major |\n| c | x | Nit |\n"
    def counts(self, row): return "## Counts\n| claim type | Blocker | Major | Nit | total |\n|---|---|---|---|---|\n" + row + "\n"

    def test_consistent(self):
        self.assertEqual(so.counts_consistent(self.F + self.counts("| all (raw rows) | 1 | 1 | 1 | 3 |")), [])

    def test_mismatch_reported(self):
        self.assertTrue(so.counts_consistent(self.F + self.counts("| all (raw rows) | 2 | 1 | 1 | 3 |")))

    def test_bad_severity_reported(self):
        t = self.F.replace("| c | x | Nit |", "| c | x | Minor |") + self.counts("| all (raw rows) | 1 | 1 | 0 | 3 |")
        self.assertTrue(any("Minor" in x for x in so.counts_consistent(t)))

    def test_missing_counts_row_reported(self):
        self.assertTrue(so.counts_consistent(self.F))

    def test_missing_job_section_reported(self):
        t = "".join("## Job: %s\nOwner: a\n" % k for k in so.KEYS if k != "RETRY")
        self.assertTrue(any("RETRY" in x for x in so.missing_jobs(t)))
        self.assertEqual(so.missing_jobs("".join("## Job: %s\nOwner: a\n" % k for k in so.KEYS)), [])

    def test_run_calls_both_checks(self):
        d = workdir()
        shutil.copy(os.path.join(BASE, "work", "L1.md"), os.path.join(d, "work", "L1.md"))
        open(os.path.join(d, "SWEEP.md"), "w").write(self.F + self.counts("| all (raw rows) | 9 | 9 | 9 | 9 |"))
        open(os.path.join(d, "ONE-PLACE-TABLE.md"), "w").write("## Job: STORE\nOwner: a\n")
        res = so.run(d)
        self.assertTrue(any("all (raw rows)" in x for x in res)); self.assertTrue(any("missing section ## Job: LOG" in x for x in res))


class PartitionSize(unittest.TestCase):
    def test_changed_size_resets_status(self):
        import partition
        root, out = tempfile.mkdtemp(), tempfile.mkdtemp()
        subprocess.check_call(["git", "init", "-q", root])
        os.makedirs(os.path.join(root, "src")); p = os.path.join(root, "src", "a.py")
        open(p, "w").write("x"); subprocess.check_call(["git", "-C", root, "add", "."])
        partition.main(root, out)
        mf = os.path.join(out, "manifest-L5b.tsv")
        txt = open(mf).read().replace("NOT-READ", "READ")
        open(mf, "w").write(txt)
        partition.main(root, out)
        self.assertIn("\tREAD\n", open(mf).read())          # same size: status kept
        open(p, "w").write("xxxxx")
        partition.main(root, out)
        self.assertIn("\t5\tNOT-READ\n", open(mf).read())   # size changed: read again


class CitationFixes(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        open(os.path.join(self.d, "a.txt"), "w", encoding="utf-8", newline="").write("a b\nTARGET LINE here\n")

    def test_split_on_newline_only(self):
        self.assertEqual(cc.check(self.d, "a.txt", 2, "TARGET LINE here"), "FOUND")

    def _main(self, texts):
        open(os.path.join(self.d, "b.txt"), "w").write("one\nTARGET LINE here\n")
        fs = []
        for i, t in enumerate(texts):
            p = os.path.join(self.d, "in%d.md" % i); open(p, "w").write(t); fs.append(p)
        return cc.main(self.d, os.path.join(self.d, "out.tsv"), fs)

    GOOD = 'b.txt:2 "TARGET LINE here"\n'

    def test_all_good_passes(self): self.assertEqual(self._main([self.GOOD]), 0)
    def test_unparsed_citation_fails(self): self.assertEqual(self._main([self.GOOD + 'b.txt:2 "TARGET LINE here\n']), 1)
    def test_short_quote_fails(self): self.assertEqual(self._main([self.GOOD + 'b.txt:2 "TARGET"\n']), 1)
    def test_file_without_citation_fails(self): self.assertEqual(self._main([self.GOOD, "no citations here\n"]), 1)


class SafeWriteCrlf(unittest.TestCase):
    def test_crlf_file_is_not_a_hand_edit(self):
        d = tempfile.mkdtemp()
        self.assertTrue(sw.safe_write(d, "f.md", "a\r\nb\r\n"))
        self.assertFalse(sw.refused(d, "f.md"))
        self.assertEqual(open(os.path.join(d, "f.md"), "rb").read(), b"a\r\nb\r\n")


if __name__ == "__main__":
    unittest.main()
