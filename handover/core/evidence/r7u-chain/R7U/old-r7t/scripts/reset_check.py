"""Run by reset.sh and reset.ps1 AFTER they stopped the desk and BEFORE they delete anything. Exit 0 = nothing uses the
lead book: no process holds its lock file and nothing answers on the desk's or the demo server's port. Exit 3 = a
process still holds the database or the lock file cannot be tested, 4 = something still answers on a port OR the
lead book path is one the desk would refuse (a pipe, a device, a folder, a name with a control character: the same
check as the desk, `lead_desk.desk.book_problem`; the two 4s are told apart by the line printed), 2 = a desk setting is
wrong (the desk's own refusal text; nothing is deleted). These numbers belong to the reset scripts and are pinned by
tests/test_reset_scripts.py; the names are in lead_desk.constants (EXIT_RESET_*).
Prints nothing on exit 0; on a refusal (2, 3 or 4) it prints one line, no values."""

from __future__ import annotations

import socket
import sys

from lead_desk import lockfile
from lead_desk.config import Config
from lead_desk.constants import EXIT_REFUSED, EXIT_RESET_DESK_RUNNING, EXIT_RESET_PORT_OR_BOOK
from lead_desk.desk import book_problem
from lead_desk.envnum import SettingRefused

LOOPBACK = "127.0.0.1"
CONNECT_SECONDS = 1.0


def answers(port: int) -> bool:
    try:
        with socket.create_connection((LOOPBACK, port), timeout=CONNECT_SECONDS):
            return True
    except OSError:
        return False


def main() -> int:
    try:
        config = Config.from_env()
    except SettingRefused as e:  # a bad DESK_* value: a plain refusal (exit 2), and reset.sh stops before it deletes
        print(f"refused: {e}; nothing was deleted")
        return EXIT_REFUSED
    if (problem := book_problem(config.db_path)) is not None:  # the desk's own check: a pipe there must never be read
        print(f"refused: the lead book path cannot be used ({problem}); nothing was deleted")
        return EXIT_RESET_PORT_OR_BOOK
    # only "there is no lock file" means that nothing holds the book; a lock file that cannot be tested is a refusal,
    # and a refused run must not create the file (acquire would)
    try:
        has_lock_file: bool | None = lockfile.lock_path(config.db_path).exists()
    except OSError:  # an unreadable folder: exists() raises instead of answering
        has_lock_file = None
    if has_lock_file is None:
        print("refused: the data folder cannot be looked at, so it is not known whether the desk runs; nothing deleted")
        return EXIT_RESET_DESK_RUNNING
    if has_lock_file:
        try:
            lockfile.acquire(config.db_path).close()
        except lockfile.LockHeldError:
            print("refused: a process still holds the database (the desk is running); nothing was deleted")
            return EXIT_RESET_DESK_RUNNING
        except lockfile.LockUnavailableError:
            print(
                "refused: the lock file of the database cannot be tested, so it is not known whether the desk runs; "
                "nothing was deleted"
            )
            return EXIT_RESET_DESK_RUNNING
    for port in (config.port, config.fakes_port):
        if port and answers(port):
            print(f"refused: something still answers on port {port}; nothing was deleted")
            return EXIT_RESET_PORT_OR_BOOK
    return 0


if __name__ == "__main__":
    sys.exit(main())
