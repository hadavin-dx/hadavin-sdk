"""P10: card-path time mutants. usage: python p10_mut.py  (copies /tmp/p10 to /tmp/m68 /tmp/m69 /tmp/m70, edits one line each, times channel.clean on the input, 65,536 characters)"""
import shutil, subprocess, pathlib, sys
M = {
 "A68": ("approvals/gate.py", '|\\\\.){0,128})\\]"', '|\\\\.)*)\\]"', "[", "["),
 "A69": ("approvals/gate.py", "for t in _MD_BLOCK.parse(text):", "for t in _MD.parse(text):", "[", "["),
 "A70": ("approvals/gate.py", "    if len(text) > _CODE_SPAN_MAX:\n        return set(range(len(lines)))\n", "", "`[", "`["),
}
for k, (f, old, new, ch, _) in M.items():
    d = pathlib.Path("/tmp/m" + k[1:]); shutil.rmtree(d, ignore_errors=True); shutil.copytree("/tmp/p10", d)
    p = d / "src/hadavin_sdk" / f; s = p.read_text(encoding="utf-8"); assert s.count(old) == 1, (k, s.count(old)); p.write_text(s.replace(old, new), encoding="utf-8")
    code = "import time\nfrom hadavin_sdk.approvals import channel\nx=%r*65536\nt=time.perf_counter(); channel.clean(x); print(%r, round(time.perf_counter()-t,1))" % (ch, k)
    r = subprocess.run(["/home/user/hadavin-sdk/.venv/bin/python", "-c", code], env={"PYTHONPATH": str(d / "src"), "PATH": "/usr/bin"}, capture_output=True, text=True, timeout=900)
    print(r.stdout.strip() or r.stderr[-200:], flush=True)
