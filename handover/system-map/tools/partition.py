"""Assign every file to exactly one lane (PLAN-002 section 3) and write manifests.
Usage: python3 tools/partition.py <repo_root> <out_dir>   (exit 1 on REMAINDER or double assignment)"""
import os, subprocess, sys

RULES = [  # (lane, prefix or exact path); first match wins; checked for double match separately
    ("L1", "handover/demo/ORDERS.md"), ("L1", "handover/demo/REPORT.md"),
    ("L1", "handover/demo/APPLY-LIST.md"), ("L1", "handover/demo/semgrep-pr-diff-lead.patch"),
    *[("L1", f"handover/demo/{d}/") for d in
      ("pr-text", "pr-stack", "followup", "merge-ready", "speed", "reuse", "drift")],
    ("L2", "handover/demo3/kill/"),
    ("L3", "handover/demo3/evidence/"), ("L3", "handover/demo3/tools/"), ("L3", "handover/demo3/scratch/"),
]


def lanes_for(path):
    hits = {lane for lane, p in RULES if path == p or (p.endswith("/") and path.startswith(p))}
    parts = path.split("/")
    if len(parts) == 2 and parts[0] == "handover" and parts[1].endswith(".md"):
        hits.add("L1")
    if path.startswith("handover/tools/"):
        hits.add("L1")
    if path.startswith("handover/demo3/") and path.count("/") == 2 and path.endswith(".md"):
        hits.add("L2")
    if path.startswith("handover/demo/") and not hits:
        hits.add("L4")  # remainder of handover/demo, by design
    if not path.startswith("handover/"):
        hits.add("L5")
    return hits


def list_files(root):
    out = subprocess.check_output(["git", "-C", root, "ls-files"], text=True).splitlines()
    return [p for p in out if not p.startswith("handover/system-map/")]


def partition(files):
    lanes, problems = {}, []
    for f in files:
        h = lanes_for(f)
        if len(h) != 1:
            problems.append((f, sorted(h)))
        else:
            lanes.setdefault(next(iter(h)), []).append(f)
    return lanes, problems


def main(root, out):
    files = list_files(root)
    lanes, problems = partition(files)
    os.makedirs(out, exist_ok=True)
    for lane, fs in sorted(lanes.items()):
        with open(os.path.join(out, f"manifest-{lane}.tsv"), "w") as fh:
            for f in fs:
                size = os.path.getsize(os.path.join(root, f)) if os.path.exists(os.path.join(root, f)) else -1
                fh.write(f"{f}\t{size}\tNOT-READ\n")
    total = sum(len(v) for v in lanes.values())
    print({k: len(v) for k, v in sorted(lanes.items())}, "total", total, "of", len(files),
          "problems", len(problems))
    for f, h in problems[:20]:
        print("PROBLEM", f, h)
    return 1 if problems or total != len(files) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
