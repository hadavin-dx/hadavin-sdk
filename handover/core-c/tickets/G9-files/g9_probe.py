"""G9 evidence helper: wraps `_Redactor.sweep` and `_Redactor._overlaps` of the tree already on sys.path to record, per sweep call,
the passes (read-backs) and the work units at its end. `install(R)` returns the record dict; `reset()` empties it."""

from collections import Counter

STATS = {"passes": Counter(), "units": [], "refused": Counter()}


def install(R):
    if not hasattr(R._Redactor, "_overlaps") or getattr(R._Redactor.sweep, "_g9_probe", False):
        return STATS
    real_sweep, real_overlaps = R._Redactor.sweep, R._Redactor._overlaps
    current: list[list] = []

    def sweep(self, out, deadline=None):
        current.append([0, None])
        try:
            res = real_sweep(self, out, deadline)
        except Exception as e:
            STATS["refused"][str(e)] += 1
            raise
        finally:
            n, work = current.pop()
            STATS["passes"][n] += 1
            STATS["units"].append(work[0] if work else 0)
        return res

    def overlaps(self, out, deadline, work):
        if current:
            current[-1][0] += 1
            current[-1][1] = work
        return real_overlaps(self, out, deadline, work)

    sweep._g9_probe = True
    R._Redactor.sweep, R._Redactor._overlaps = sweep, overlaps
    return STATS


def reset():
    STATS["passes"].clear()
    STATS["units"].clear()
    STATS["refused"].clear()


def summary() -> str:
    return f"passes={dict(sorted(STATS['passes'].items()))} max_units={max(STATS['units'], default=0):,} refused={dict(STATS['refused'])}"
