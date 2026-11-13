from pathlib import Path
class PathRefused(Exception): pass
def confine(p, what=""): print("FOREIGN confine used"); return Path(p)
def confine_existing(p, what=""): print("FOREIGN confine_existing used"); return Path(p)
def confine_anywhere(p, what=""): return Path(p)
def readonly_sqlite_uri(p): return "foreign"
