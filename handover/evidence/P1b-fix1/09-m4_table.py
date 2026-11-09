import time
from hadavin_sdk import defaults
from hadavin_sdk.guard import injection
cap = defaults.TEXTNORM_MAX_CHARS
print("TEXTNORM_MAX_CHARS", cap, "INJECTION_MAX_CHARS", defaults.TEXTNORM_INJECTION_MAX_CHARS, "CHUNK", defaults.TEXTNORM_INJECTION_CHUNK_CHARS, "OVERLAP", defaults.TEXTNORM_INJECTION_OVERLAP_CHARS)
fillers = {"ascii": "ordinary words in a long log line, nothing to see here. ", "cyrillic": "обычные слова в длинной строке журнала, ничего особенного. "}
det = injection.RegexDetector(0.5)
print("filler\tmult\tchars\tflagged\treason\tseconds")
for name, f in fillers.items():
    for m in (1, 2, 4, 8, 9):
        n = m * cap
        text = (f * (n // len(f) + 1))[:n]
        t0 = time.perf_counter()
        v = injection.injection_check(det, text, "t")
        dt = time.perf_counter() - t0
        print(f"{name}\t{m}x\t{n}\t{v.flagged}\t{v.reason_code}\t{dt:.2f}")
