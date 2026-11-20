"""G7 fix round 6: count the units of work of `_Redactor._spelled_sweep` on the honest shapes and the hostile one (scratch script kept as evidence).

Run: uv run --all-extras --group test python handover/core-c/evidence/g7r6_units.py
The units are read by bisection of `defaults.SPELLED_MAX_WORK` (the scan refuses past it, checked every 1,024 units, so exact to 1,024).
Every credential is made up and built from parts.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from hadavin_sdk import defaults  # noqa: E402
import importlib  # noqa: E402

from hadavin_sdk.guard.runmap import InputTooLarge  # noqa: E402

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

JWT = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ1c2VyMSJ9" + "." + "c2lnbmF0dXJlMTIzNDU2Nzg5"
SIG64 = ("sig" + "AbCdEfGh") * 8  # 88 characters; sliced below
CAP = defaults.MAX_REDACT_CHARS


def jar_log(lines: int, sig: int = 64) -> tuple[str, str]:
    """(registered text, probe of copies): Cookie headers that GROW by one 4-character cookie at the FRONT per line, every one ending in the
    same signed suffix of `sig` characters after the session token. The probe is the same lines as the first sweep leaves other copies."""
    suffix = "~" + SIG64[:sig]
    rows = []
    for k in range(1, lines + 1):
        cookies = ";".join(
            f"a{(k - j) % 10}=1" for j in range(k)
        )  # the newest cookie FIRST: line k's prefix ends with line k-1's
        rows.append(f"Cookie: {cookies}; sid={JWT}{suffix}")
    text = "\n".join(rows)
    return text, text.replace(JWT, "<JWT_1>")


def units(r: "R._Redactor", probe: str) -> tuple[int, float]:
    """(units of work of one `_spelled_sweep` of `probe`, seconds of thread CPU of the run at the true limit-free scan)."""
    held = defaults.SPELLED_MAX_WORK
    try:
        defaults.SPELLED_MAX_WORK = 10**12
        t0 = time.thread_time()
        r._spelled_sweep(probe, None)
        took = time.thread_time() - t0
        lo, hi = 0, 10**9
        while hi - lo > 1024:
            mid = (lo + hi) // 2
            defaults.SPELLED_MAX_WORK = mid
            try:
                r._spelled_sweep(probe, None)
                hi = mid
            except InputTooLarge:
                lo = mid
        return hi, took
    finally:
        defaults.SPELLED_MAX_WORK = held


def cookie_copies(lines: int) -> tuple[str, str]:
    """Round 5's honest worst case: a Cookie header preceded by other cookies of another length on every line (300 prefix lengths)."""
    rows = [f"Cookie: _ga=GA1.2{'x' * k}; theme=dark; sid={JWT}" for k in range(lines)]
    text = "\n".join(rows)
    return text, "\n".join(r.replace(JWT, "<JWT_1>") for r in rows) * 5


def signed_ids(lines: int) -> tuple[str, str]:
    value = "0b5d2c1e-7f3a-4c9d-8e21-5a6b7c8d9e0f"
    rows = [f"password={value}.sig{n}" for n in range(lines)]
    return "\n".join(rows), "\n".join(f"copy <UUID_1>.sig{k % lines}" for k in range(8000))


def grid(prefixes: int, suffixes: int) -> tuple[str, str]:
    forms = "\n".join(
        f"password={'a' * k}<SECRET_1>{'Z' * m}"
        for k in range(1, prefixes + 1)
        for m in range(1, suffixes + 1)
    )
    block = "a" * prefixes + "<SECRET_1>" + "Z" * suffixes + "\n"
    return forms, block * (CAP // len(block))


def report(label: str, registered: str, probe: str, seed: dict[str, str] | None = None) -> None:
    probe = probe[:CAP]
    r = R._Redactor(seed)
    r.find(registered)
    r.sweep("")
    n, took = units(r, probe)
    print(
        f"{label}: registered={len(registered)} probe={len(probe)} forms={len(r._spelled_at)} "
        f"units={n} ({n / defaults.SPELLED_MAX_WORK:.1%} of the limit) scan_s={took:.4f} us_per_unit={took / max(n, 1) * 1e6:.3f}"
    )


def refusal_timing(
    label: str, registered: str, probe: str, seed: dict[str, str] | None = None
) -> None:
    """Seconds of thread CPU until the scan REFUSES at the real limit (what a hostile text costs before it is refused)."""
    r = R._Redactor(seed)
    r.find(registered)
    r.sweep("")
    t0 = time.thread_time()
    try:
        r._spelled_sweep(probe[:CAP], None)
        print(f"{label}: not refused")
    except InputTooLarge as e:
        print(
            f"{label}: refused ({e}) after {time.thread_time() - t0:.3f} s at the limit {defaults.SPELLED_MAX_WORK:,}"
        )


def memory() -> None:
    """Registry memory of ONE compound value of 200,000 characters with a leading placeholder (the generic SECRET class has no length cap)."""
    import tracemalloc

    value = "q" * 200_000
    r = R._Redactor({"<SECRET_1>": "ab" + "9x"})
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    r._place("SECRET", "ab9x" + value, "<SECRET_1>" + value)
    used = tracemalloc.get_traced_memory()[0] - before
    tracemalloc.stop()
    nodes = 0
    stack = [r._spelled["<SECRET_1>"][1]]
    while stack:
        node = stack.pop()
        nodes += 1
        stack.extend(v for k, v in node.items() if k and isinstance(v, dict))
    print(
        f"registry memory: one 200,000-character compound value: {used / 1e6:.1f} MB traced, about {nodes:,} trie nodes"
    )


def main() -> None:
    print(f"SPELLED_MAX_WORK = {defaults.SPELLED_MAX_WORK:,}")
    for lines, sig in ((330, 64), (275, 128)):
        text, probe = jar_log(lines, sig)
        report(f"jar lines={lines} suffix={sig}", text, probe)
    report("round 5 honest A (300 prefix lengths)", *cookie_copies(300))
    report("round 5 honest B (300 signed ids)", *signed_ids(300), seed=None)
    forms, probe = grid(70, 40)
    report("hostile grid 70 x 40", forms, probe, {"<SECRET_1>": "ab" + "9x"})
    refusal_timing("hostile grid 70 x 40", forms, probe, {"<SECRET_1>": "ab" + "9x"})
    if hasattr(R._Redactor, "_refuse_late_overlap"):
        memory()


if __name__ == "__main__":
    main()
