"""Print one desk setting for the start and reset scripts (scripts/reset.sh, start_all.sh, reset.ps1, start_all.ps1).

Run from the repository root with PYTHONPATH set to the source folder:
    python scripts/desk_setting.py db-path | data-dir | fakes-port | port | start-tries | start-pause
It prints the value the desk would use (the database file, its folder, the demo server's port, the desk's port), read
from the DESK_* environment variables by Config.from_env, the same code the desk itself runs. When a DESK_* value is
refused it prints the ONE line the desk prints, `the desk refuses a setting: <what is wrong>`, and ends with exit code 4
(the desk's own code for a refused setting): no Python traceback, and the text never repeats the value that was typed
(the refusal texts name the setting, not its value). `db-path` and `data-dir` also run the desk's own lead-book check
(`the desk refuses to start: ...`, same exit code 4). A wrong command line ends with a usage line and exit code 2."""

from __future__ import annotations

import sys
from collections.abc import Callable

from lead_desk.config import Config
from lead_desk.constants import EXIT_DESK_SETTING_REFUSED, START_CHECK_PAUSE_SECONDS, START_CHECK_TRIES
from lead_desk.desk import book_problem
from lead_desk.envnum import SettingRefused

EXIT_USAGE = 2
BOOK_WORDS = ("db-path", "data-dir")  # the words that name the book: a folder or pipe there is refused
ARGS = 2  # the script name and one word
WHAT: dict[str, Callable[[Config], object]] = {
    "db-path": lambda c: c.db_path,
    "data-dir": lambda c: c.db_path.parent,
    "fakes-port": lambda c: c.fakes_port,
    "port": lambda c: c.port,
    "start-tries": lambda _c: START_CHECK_TRIES,  # not a desk setting: how long start_all.sh watches the new desk
    "start-pause": lambda _c: START_CHECK_PAUSE_SECONDS,
}


def main(argv: list[str]) -> int:
    if len(argv) != ARGS or argv[1] not in WHAT:
        print("usage: python scripts/desk_setting.py " + " | ".join(WHAT))  # never echoes what was typed
        return EXIT_USAGE
    try:
        config = Config.from_env()
    except SettingRefused as e:  # the same line and exit code as the desk itself (server.main)
        print(f"the desk refuses a setting: {e}")
        return EXIT_DESK_SETTING_REFUSED
    if argv[1] in BOOK_WORDS and (problem := book_problem(config.db_path)) is not None:
        # start_all makes this folder next: a book path the desk would refuse (a part of it is a file) ends here
        print(f"the desk refuses to start: {problem}")
        return EXIT_DESK_SETTING_REFUSED
    print(WHAT[argv[1]](config))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
