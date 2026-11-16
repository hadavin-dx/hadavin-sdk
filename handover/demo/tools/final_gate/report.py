"""Write the final-gate report from stages.jsonl + meta.json. Records only; no verdicts beyond each tool's own exit code.
usage: report.py WORKDIR OUTFILE"""
import json, os, sys
w, out = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(w, "meta.json")))
recs = [json.loads(l) for l in open(os.path.join(w, "stages.jsonl"))] if os.path.exists(os.path.join(w, "stages.jsonl")) else []
last = {}
for r in recs: last[(r["stage"], r["name"])] = r   # a re-run of a stage replaces its older line
recs = sorted(last.values(), key=lambda r: (r["stage"], r["name"]))
NAMES = {0: "Set-up (unpack, own venv, hook patch)", 1: "Lint, types, security scan, schema check", 2: "Full pytest, repeated", 3: "Four concurrency tests, repeated",
         4: "Hostile matrix, single runner", 5: "Load (same lead, different leads) and kill -9 rounds"}
def text(p):
    try: return open(p, errors="replace").read()
    except OSError: return "(raw file missing)"
L = []
L.append(f"# Final gate report: {meta['tarball_name']}  ({meta['mode']} mode)\n")
L.append("This file records commands, exit codes and the tools' own output, word for word. It makes no pass/fail judgement of its own.\n")
L.append("## Header\n")
for k in ["tarball", "tarball_sha256", "tree", "workdir", "host", "cores", "python", "venv", "started_utc", "mode", "server_py_hooks"]:
    L.append(f"- {k}: `{meta.get(k)}`")
L.append("\n**Edit applied to the UNPACKED COPY only (never to the tarball):** the `server.py` hook edits from CONTRACT-DELTA.md "
         "(\"server.py hooks\": catch LockHeldError and OSError, `start_background()` before `startup()`, `stop_background()` first in `finally`). "
         f"Result of the patch step: `{meta.get('server_py_hooks')}`.\n")
L.append("Stage order is fixed and one thing runs at a time; free ports are picked per step. Exit code 124 here means the step hit its time limit and was stopped by this script.\n")
for st in sorted(NAMES):
    rs = [r for r in recs if r["stage"] == st]
    L.append(f"## Stage {st}: {NAMES[st]}\n")
    if not rs: L.append("NOT RUN in this invocation.\n"); continue
    L.append("| step | exit | seconds | limit s | raw file |\n|---|---|---|---|---|")
    for r in rs: L.append(f"| {r['name']} | {r['exit']}{' (timed out)' if r['timed_out'] else ''} | {r['seconds']} | {r['timeout_limit']} | `{r['raw']}` |")
    L.append("")
    for r in rs:
        L.append(f"### {r['name']}\n\nCommand: `{r['cmd']}`  (cwd `{r.get('cwd')}`)  exit code: {r['exit']}\n")
        if r.get("note"): L.append(f"Run summary: {r['note']}\n")
        t = text(r["raw"]); lines = t.splitlines()
        if st == 2:
            fl = [x for x in lines if x.startswith("FAILED") or x.startswith("ERROR")]
            L.append("Last line (verbatim):\n```\n" + (lines[-1] if lines else "") + "\n```")
            L.append("FAILED/ERROR lines (verbatim, all):\n```\n" + ("\n".join(fl) if fl else "(none)") + "\n```\n")
        elif st == 3:
            c = [x for x in lines if x.startswith("COUNTS")]
            L.append("```\n" + "\n".join(c) + "\n```")
            L.append(f"Output of failing runs is in the raw file ({len([x for x in lines if x.startswith('=== run')])} failing run(s) recorded).\n")
        elif st in (5,):
            L.append("```\n" + t.rstrip() + "\n```\n")
        else:
            tail = lines[-40:]
            L.append(("(last 40 lines, verbatim; whole output in raw file)\n" if len(lines) > 40 else "(whole output, verbatim)\n") + "```\n" + "\n".join(tail) + "\n```\n")
L.append("## Other raw files\n")
for f in sorted(os.listdir(w)):
    if f.endswith(".jsonl") and f != "stages.jsonl": L.append(f"- `{os.path.join(w, f)}` ({sum(1 for _ in open(os.path.join(w, f)))} lines)")
L.append("- `" + os.path.join(w, "stages.jsonl") + "` (one JSON line per step: command, cwd, exit, seconds)")
open(out, "w").write("\n".join(L) + "\n")
print("report written:", out)
