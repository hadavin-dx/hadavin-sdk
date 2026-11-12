"""EVIDENCE for PR H batch 11 (design D9: how many ordinary texts does the widened check withhold). Usage:
python clean_corpus_b11.py <tree-root> <corpus-root>. The corpus is every line of 20 or more characters of the .md, .py and .txt
files under <corpus-root> (the same root for every tree, so the numbers compare), every 7th line, cut to 60 characters, each in three
spellings: plain, with an ANSI colour code in front, and with a zero-width space after every word (made-up ordinary text, no secret
in it). Conditions: A = ordinary text with a handed-out secret that is NOT in it (nothing may be withheld); B = the same text with one
copy of the secret appended (masked, never withheld); C = B with an unterminated string opener (ESC P and one word) before the copy, so the
front-before-opener check runs; D = C with a secret made of everyday 4-letter stretches (the worst case of the check). Prints counts
only (no text, no secret)."""

import sys
from pathlib import Path

tree, corpus = sys.argv[1], sys.argv[2]
sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools  # noqa: E402

HAND = "Qx7mLp" + "-9vRtzKw2"
EVERYDAY = "ation" + "ingthe" + "ment" + "ness" + "tion"  # made-up value of common letter groups
lines = []
for f in sorted(Path(corpus).rglob("*")):
    if (
        f.is_file()
        and f.suffix in {".md", ".py", ".txt"}
        and not {".git", "__pycache__", ".venv", "venv"} & set(f.parts)
    ):
        try:
            lines += [
                ln.strip()
                for ln in f.read_text(encoding="utf-8").splitlines()
                if len(ln.strip()) >= 20
            ]
        except (UnicodeDecodeError, OSError):
            continue
lines = [ln[:60] for ln in lines[::7]]
texts = []
for ln in lines:
    texts += [ln, "\x1b[1;32m" + ln, "​ ".join(ln.split(" "))]


def withheld(o):
    return o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o


def count(make, secret):
    n = bad = 0
    for t in texts:
        n += 1
        try:
            bad += withheld(tools.prepare_output(make(t, secret), {}, 4000, [secret]))
        except Exception:  # noqa: BLE001 - counted as not shown
            bad += 1
    return n, bad


for label, make, secret in (
    ("A no copy", lambda t, s: t, HAND),
    ("B one copy", lambda t, s: t + "\n" + s, HAND),
    ("C opener + copy", lambda t, s: t + "\x1bP words\n" + s, HAND),
    ("D opener + copy, everyday secret", lambda t, s: t + "\x1bP words\n" + s, EVERYDAY),
):
    n, bad = count(make, secret)
    print(f"{label}: texts={n} withheld_or_error={bad} share={bad / n:.5f}")
print("tree", tree)
