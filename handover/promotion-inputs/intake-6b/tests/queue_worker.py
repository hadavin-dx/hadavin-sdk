"""A worker process for the cross-process queue tests (not a test module). Usage: ``python queue_worker.py <start_epoch> <op> [args...]``; the
HADAVIN_LOCAL and INTAKE_MODEL_BACKEND variables come from the environment. It waits for the start time, runs one operation and prints one word."""

from __future__ import annotations

import hashlib
import os
import sys
import time

from intake import decisions, settings, workqueue
from intake.codes import Refused


def main(argv: list[str]) -> int:
    start, op, args = float(argv[0]), argv[1], argv[2:]
    s = settings.load()
    time.sleep(max(0.0, start - time.time()))
    try:
        if op == "connect":
            workqueue.connect(s).close()
            print("ok")
        elif op == "insert":
            r = workqueue.insert_received(s, args[1] + ".txt", args[0], "text", s.tenant_id, args[1])
            print("item" if isinstance(r, workqueue.Item) else "dup")
        elif op == "decide":
            decisions.decide(s, args[0], args[1], "ap-a", "checked against the order", args[2], int(args[3]))
            print("ok")
        elif op == "purge":
            workqueue.purge(s, args[0])
            print("ok")
        elif op == "die_in_transaction":
            conn = workqueue.connect(s)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'reject', 'ap-a', 'x', ?, 'z')",
                (int(args[0]), hashlib.sha256(b"x").hexdigest()),
            )
            conn.execute("UPDATE items SET state='REJECTED', version=version+1 WHERE uid=?", (int(args[0]),))
            print("in_transaction", flush=True)
            os._exit(9)  # no commit, no rollback, no close
        else:
            print("bad_op")
            return 3
    except Refused as e:
        print(e.code)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
