"""Assign every file to exactly one lane (PLAN-002 section 3) and write manifests.
Usage: python3 tools/partition.py <repo_root> <out_dir>   (exit 1 on REMAINDER or double assignment)"""
import hashlib, os, subprocess, sys

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
        hits.add("L5b" if path.startswith(("src/", "tests/")) else "L5a")
    return hits


def list_files(root):
    out = [x for x in subprocess.check_output(["git", "-C", root, "ls-files", "-z"]).decode("utf-8", "surrogateescape").split("\0") if x]
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
        mp = os.path.join(out, f"manifest-{lane}.tsv")
        status = {}
        if os.path.exists(mp):  # keep the read status already recorded, but only for a file whose size is unchanged
            for line in open(mp, encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                if len(c) == 4:  # file, size, status, sha256 of the content when the status was recorded
                    status[c[0]] = (c[1], c[2], c[3])
        with open(mp, "w", encoding="utf-8") as fh:
            for f in fs:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp) if os.path.isfile(fp) else -1
                digest = hashlib.sha256(open(fp, "rb").read()).hexdigest() if os.path.isfile(fp) else "missing"
                old = status.get(f)
                # keep READ only if size AND content hash are unchanged; a missing file is never kept
                keep = old[1] if old and old[0] == str(size) and old[2] == digest and digest != "missing" else "NOT-READ"
                fh.write(f"{f}\t{size}\t{keep}\t{digest}\n")
    total = sum(len(v) for v in lanes.values())
    print({k: len(v) for k, v in sorted(lanes.items())}, "total", total, "of", len(files),
          "problems", len(problems))
    for f, h in problems[:20]:
        print("PROBLEM", f, h)
    return 1 if problems or total != len(files) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
