import re, subprocess, sys, textwrap, yaml, tempfile, os
d = yaml.safe_load(open(sys.argv[1])); job = d["jobs"]["no-demo"]
run = [s for s in job["steps"] if s.get("name", "").startswith("Tests")][0]["run"]
src = re.search(r"<<'PY'\n(.*?)\n\s*PY\n?$", run, re.S).group(1)
open("gatesrc.py", "w").write(src)
OK = "938 passed, 80 skipped in 78.00s (0:01:18)"
good = ["rc=0 71 passed in 3.10s"] * 9
def mk(lines): return "\n".join(lines) + "\n"
def gate(text, skipped_budget=90, collected=None, floor=1):
    tf = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt"); tf.write(text); tf.close()
    if collected is None:
        collected = sum(int(m) for m in re.findall(r"rc=\d+ (\d+) passed", text)) + sum(int(m) for m in re.findall(r"(\d+) skipped", text))
    r = subprocess.run([sys.executable, "gatesrc.py", tf.name, str(floor), str(skipped_budget), str(collected)], capture_output=True, text=True)
    os.unlink(tf.name); return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ""
def with_last(x): return good[:8] + [x]
cases = [
 ("all good", mk(good), 0),
 ("last chunk: no tests ran", mk(with_last("rc=0 no tests ran in 0.01s")), 1),
 ("last chunk: progress line", mk(with_last("rc=0 ....s....  [ 40%]")), 1),
 ("last chunk: progress line without newline fused", mk(with_last("rc=0 ssss....ssssss")), 1),
 ("last chunk: pytest.Exit message", mk(with_last("rc=0 !!!! _pytest.outcomes.Exit: stop !!!!")), 1),
 ("last chunk: 1 error", mk(with_last("rc=1 1 error in 0.20s")), 1),
 ("last chunk: 1 failed", mk(with_last("rc=1 1 failed, 5 passed in 0.20s")), 1),
 ("last chunk: 1 failed with rc 0 (impossible but fed)", mk(with_last("rc=0 1 failed, 5 passed in 0.20s")), 1),
 ("last chunk: good summary but exit code 1", mk(with_last("rc=1 71 passed in 3.10s")), 1),
 ("last chunk: good summary but exit code 2", mk(with_last("rc=2 71 passed in 3.10s")), 1),
 ("last chunk: empty last line", mk(with_last("rc=0 ")), 1),
 ("middle chunk empty line", mk(good[:3] + ["rc=0 "] + good[4:]), 1),
 ("10 lines", mk(good + ["rc=0 71 passed in 3.10s"]), 1),
 ("8 lines", mk(good[:8]), 1),
 ("0 lines (empty file)", "", 1),
 ("blank line inserted (10 lines)", mk(good[:4] + [""] + good[4:]), 1),
 ("progress line fused with next chunk (8 lines)", mk(good[:3] + ["rc=0 ssss....rc=0 71 passed in 3.10s"] + good[5:]), 1),
 ("skipped-only chunk is fine", mk(good[:8] + ["rc=0 9 skipped in 0.10s"]), 0),
]
bad = 0
for name, text, want in cases:
    rc, last = gate(text)
    ok = (rc == 0) == (want == 0); bad += not ok
    print(f"{'ok  ' if ok else 'WRONG'} gate exit {rc} (want {want}) {name}: {last}")
rc, last = gate(mk(good), collected=640); print("count mismatch (collected 640 vs 639 reported)", rc, last); bad += rc == 0
rc, last = gate(mk(good), collected=630); print("count mismatch (collected 630 vs 639 reported)", rc, last); bad += rc == 0
rc, last = gate(mk(good[:8] + ["rc=0 60 passed, 91 skipped in 3.10s"]), skipped_budget=90); print("skip budget exceeded (91 > 90)", rc, last); bad += rc == 0
rc, last = gate(mk(good[:8] + ["rc=0 60 passed, 90 skipped in 3.10s"]), skipped_budget=90); print("skip at budget (90 <= 90) passes", rc, last); bad += rc != 0
rc, last = gate(mk(good), floor=640); print("floor not reached (639 passed < 640)", rc, last); bad += rc == 0
rc, last = gate(mk(good), floor=639); print("floor reached (639 >= 639)", rc, last); bad += rc != 0
print("WRONG VERDICTS:", bad)
