"""Rewrite STATUS-BOARD.md from board-state.json plus live machine facts, then commit, pull --rebase, push.

Session tool of core-a (not product code). The session keeps board-state.json true; this script only renders it
and measures the machine. Run: python3 handover/core-a/tools/board.py [--no-push]
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parent.parent
BRANCH = "cloud/core-a"
LAST_PUSH = Path.home() / ".cache" / "core-a-last-push.txt"


def sh(cmd: list[str], cwd: Path = REPO, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)  # noqa: S603
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def table(head: list[str], rows: list[dict]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(h, "")).replace("|", "/").replace("\n", " ") for h in head) + " |")
    if not rows:
        out.append("| none |" + " |" * (len(head) - 1))
    return "\n".join(out)


def procs() -> list[dict]:
    _, out = sh(["ps", "-eo", "pid,etimes,args", "--no-headers"])
    rows = []
    for line in out.splitlines():
        pid, secs, args = line.split(None, 2)
        if int(pid) == os.getpid() or "board.py" in args:
            continue
        if any(k in args for k in ("pytest", "uv run", "uv sync", "ruff", "postgres", "pg_ctl", "bandit")):
            rows.append({"pid": pid, "command in short": args[:70], "started by": "core-a session or its agent",
                         "since": f"{secs}s ago", "state": "running", "reason": "matched by name in ps"})
    return rows


def main() -> int:
    st = json.loads((HERE / "board-state.json").read_text())
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text()[:8]
    if boot != st.get("boot_id_first", boot):
        st["interrupted"] = f"BOOT_ID changed {st['boot_id_first']} to {boot}: container restart, check LOST table"
    load = Path("/proc/loadavg").read_text().split()[0]
    cores = os.cpu_count()
    mem = {ln.split(":")[0]: int(ln.split()[1]) for ln in Path("/proc/meminfo").read_text().splitlines()[:5]}
    used_gb = (mem["MemTotal"] - mem["MemAvailable"]) / 1048576
    tot_gb = mem["MemTotal"] / 1048576
    _, df = sh(["df", "-h", "--output=size,used,avail,pcent", "/"])
    df = " ".join(df.splitlines()[-1].split())
    _, du = sh(["du", "-sh", str(REPO), str(Path(tempfile.gettempdir()) / "claude-0"), str(Path.home() / ".cache")])
    du = "; ".join(" ".join(x.split()) for x in du.splitlines() if "cannot" not in x)
    agents = st.get("agents", [])
    running = [a for a in agents if a.get("state") == "running"]
    items = st.get("items", [])
    open_items = [i for i in items if not str(i.get("state", "")).startswith(("DONE", "SKIPPED"))]
    pct = round(sum(int(i.get("percent", 0)) for i in items) / max(len(items), 1))
    last_push = LAST_PUSH.read_text().strip() if LAST_PUSH.exists() else "none yet"
    cap = (f"load {load} of {cores} cores (1-minute average), mem {used_gb:.1f}/{tot_gb:.1f} GB, "
           f"{len(running)} language-model agents running (light), 0 heavy test slots unless TESTS shows one")
    head = [
        f"UPDATED_UTC: {now}", "SESSION: core-a", f"ORDER: {st['order']}", f"STATE: {st['state']}",
        f"BOOT_ID: {boot}", f"ITEMS_TOTAL: {len(items)}", f"ITEMS_OPEN: {len(open_items)}", f"PERCENT: {pct}",
        f"AGENTS_RUNNING: {len(running)}", f"CAPACITY: {cap}", f"DISK: / size used free {df}; {du}",
        f"INTERRUPTED: {st.get('interrupted', 'none')}", f"FAILED: {st.get('failed', 'none')}",
        f"SESSION_RESTARTS: {st.get('session_restarts', 0)}", f"CONTAINER_RESTARTS: {st.get('container_restarts', 0)}",
        f"NEXT: {st['next']}", f"PUSHED_UTC: {last_push} (the push before this board)",
        f"NOTE: {st.get('note', 'none')}",
    ]
    body = "\n".join(head) + "\n\n" + "\n\n".join([
        "## QUEUE ITEMS\n" + table(["item", "what", "state", "percent", "evidence file", "tries", "reason"], items),
        "## AGENTS\n" + table(["id", "role", "model", "what exactly it is doing", "started UTC", "expected end",
                               "percent", "state", "review round n of cap", "retries so far", "reason"], agents),
        "## SHELLS AND PROCESSES\n" + table(["pid", "command in short", "started by", "since", "state", "reason"],
                                            procs()),
        "## TESTS\n" + table(["suite or file", "branch and SHA", "run number", "passed / failed / errors",
                              "first failing line", "state", "reason"], st.get("tests", [])),
        "## RESTARTS\n" + table(["time UTC", "kind", "what was running", "what was lost", "restarted",
                                 "still missing"], st.get("restarts", [])),
        "## LOOPS (items tried more than once)\n" + table(["item", "tries", "review rounds", "last error",
                                                           "reason it keeps failing"], st.get("loops", [])),
        "## LOST OR INTERRUPTED\n" + table(["agent", "what it was doing", "cause", "restarted? new id",
                                            "ACK by lead"], st.get("lost", [])),
        "## LEAD ACTIONS NEEDED\n" + ("\n".join(f"- {x}" for x in st.get("lead_actions", [])) or "none"),
    ]) + "\n"
    (HERE / "STATUS-BOARD.md").write_text(body)
    if "--no-push" in sys.argv:
        print(body[:600])
        return 0
    sh(["git", "add", "-u", "handover/core-a"])
    sh(["git", "add", "handover/core-a/STATUS-BOARD.md", "handover/core-a/board-state.json"])
    rc, out = sh(["git", "commit", "-q", "-m", f"board {now}"])
    for attempt in (1, 2, 3):
        rc, out = sh(["git", "pull", "--rebase", "-q", "origin", BRANCH], timeout=90)
        if rc == 0:
            rc, out = sh(["git", "push", "-q", "origin", BRANCH], timeout=90)
        if rc == 0:
            LAST_PUSH.parent.mkdir(parents=True, exist_ok=True)
            LAST_PUSH.write_text(datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
            _, sha = sh(["git", "rev-parse", "--short", "HEAD"])
            _, new = sh(["git", "log", "-3", "--format=%h %an %s", "--", "handover/core-a/ORDERS.md",
                         "handover/core-a/QUEUE.md"])
            print(f"BOARD PUSHED {now} head {sha} try {attempt}\nlatest lead commits on ORDERS/QUEUE:\n{new}")
            return 0
    print(f"BOARD PUSH FAILED after 3 tries: {out[-400:]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
