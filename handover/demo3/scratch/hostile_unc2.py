import sys, ntpath
repo = sys.argv[1]; sys.path.insert(0, repo); sys.path.insert(1, repo + "/src")
import tools.pathconfine as pc
for t in [r"\\?\unc\host\share\x", "\\\\?\\\\UNC\\host\\share", "//?/UNC/host/share/x", "//./C:/x", r"\??\UNC\host\share\x", "\\\\host/share/x", "/\\/host/x", "//", "\\\\", "", "\x00", "a\x00b"]:
    try: print(repr(t), "->", pc.readonly_sqlite_uri(t, ntpath))
    except BaseException as e: print(repr(t), "-> EXC", type(e).__name__, e)
print("== read_book (check_invariants) on Linux")
from load_tools import check_invariants as ci
import os
for t in [r"\\host\share\x.db", "//host/share/x.db", r"\\?\UNC\host\share\x.db", "\\/host/share/x.db", 123, None, b"x", "\x00"]:
    try: print(repr(t), "->", ci.read_book(t))
    except BaseException as e: print(repr(t), "-> EXC", type(e).__name__, e)
