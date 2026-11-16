"""Mutation runner for src/intake/mask.py (WP2c P2). Breaks one rule at a time in the real file, runs the named test of tests/test_mask_kernel.py (then the
whole file if that did not fail), and restores the file in a ``finally``.

Run from the repository root:  python tests/mutation_runner/mutate_mask.py [--only SUBSTRING]
  KILLED     name :: the named test failed        (the expected result)
  ELSEWHERE  name :: another test of the file failed (the named test is stale or weak: counts as a failure of the run)
  SURVIVED   name :: no test noticed               (a failure of the run)
  CRASH      name :: the pattern was not found     (proves nothing: fix the list)
Exit code 0 only when every mutant is KILLED.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src" / "intake" / "mask.py"
TEST = "tests/test_mask_kernel.py"

# (name, old text, new text, pytest -k expression naming the test that must kill it)
MUTANTS = [
    ("masker returns text unchanged", 'model_text = "".join(out)', "model_text = text", "bank_words or amount_with"),
    ("locator returns nothing", "if n == 0 or n > len(sk.chars):", "if True:", "bank_words or r1_unlocated"),
    (
        "end-neighbour rule removed",
        "if _outside_ok(fp_, a, -1, sk.outside) and _outside_ok(fp_, b, 1, sk.outside):",
        "if True:",
        "partial_numbers",
    ),
    (
        "gap rule widened to letters",
        "_DIGITS, None, _DIGITS, 1, True)",
        "_DIGITS, None, _DIGITS, 1, False)",
        "partial_numbers or look_alike or r1_unlocated",
    ),
    (
        "locator fold replaced by casefold only",
        'return _WS_RUN.sub(" ", t.replace("\\r\\n", "\\n").replace("\\r", "\\n"))',
        "return c.casefold()",
        "fold_matches or zero_width",
    ),
    ("R1b removed", "if any(len(p) >= 3 and p not in hidden_cands for p in pieces_of.get(cand, ())):", "if False:", "r1b"),
    ("money occurrence never recognised (R2 removed)", "m = _overlaps(money, *o)", "m = False", "amount_with_the_same_digits"),
    (
        "cut_visible skipped",
        "    for t in masked.kept_visible_texts:\n        if t:",
        "    for t in ():\n        if t:",
        "cuts_visible or cut_visible",
    ),
    (
        "rule (iv) widened: bank-context line accepted as id occurrence",
        "is_id[o] = (not lines.ctx[li]) and _id_shaped(text, *o)",
        "is_id[o] = _id_shaped(text, *o)",
        "header_inv",
    ),
    ("token with a bank word accepted as id", "and not invoicecheck.bank_word_in(text[lo:hi])", "", "glued_forms"),
    (
        "next-line rule widened to every non-blank line of three",
        "self.ctx[j] = True\n                    break",
        "self.ctx[j] = True",
        "next_three",
    ),
    ("line cap removed", 'any(len(ln) > MASK_MAX_LINE_CHARS for ln in text.split("\\n"))', "False", "line_over_cap"),
    ("mark-like check skipped (a0)", "if _MARK_LIKE.search(canonical(text)):", "if False:", "mark_like"),
    ("a2 skipped", "if det.unlocated or det.spans:", "if False:", "a2_a3"),
    (
        "a3 skipped",
        "if sorted(marks) != sorted(look) or any(m not in ok for m in marks) or len(set(marks)) != len(ok):",
        "if False:",
        "a2_a3",
    ),
    (
        "neutralise skipped",
        "return _MARK.sub(lambda m: NEUTRAL if m.group(0) in ok else m.group(0), text)",
        "return text",
        "cut_visible_and_neutralise",
    ),
    ("BodyCheck always passes", "return self._check(body)", "return None", "body_check"),
    ("BodyCheck text tie skipped", "        if not same:", "        if False:", "ties_text"),
    ("BodyCheck doc_sha tie removed", 'if data.get("doc_sha") != self._source_sha256:', "if False:", "ties_text"),
    (
        "(b) canonical-only",
        "if strict != look or any(m not in ok for m in strict):",
        "if any(m not in ok for m in strict):",
        "forged_marks",
    ),
    ("path built from AI keys", 'name = k if sub is not None else "other"', "name = k", "thousand_marks"),
    (
        "merge priority swapped",
        "kind = min(last.kind, s.kind, key=PRIORITY.index)",
        "kind = max(last.kind, s.kind, key=PRIORITY.index)",
        "merge_priority",
    ),
    (
        "spellings without base64 and hex",
        'out += [b64, base64.urlsafe_b64encode(raw).decode().rstrip("="), raw.hex(), raw.hex().upper()]',
        "pass",
        "spellings_always",
    ),
    ("field rule skipped", "if sp.kind not in _FREE_TEXT_KINDS or generic not in _FREE_TEXT_PATHS:", "if False:", "field_rule"),
    (
        "(c) recompute skipped",
        'if sig(fresh) != sig(masked) or left[0] or any(v[3] != "same" for v in items.values()):',
        "if left[0]:",
        "recompute",
    ),
    ("PHONE narrowing removed", '        return "narrowed_phone"', "        return None", "phone_needs"),
    ("call added as a phone word", "(?:tel|phone|mobile|mob|fax)(?![a-z])", "(?:tel|phone|mobile|mob|fax|call)(?![a-z])", "phone_needs"),
    ("phone word boundary removed", '_PHONE_WORD = re.compile(r"(?<![a-z])(?:tel', '_PHONE_WORD = re.compile(r"(?:tel', "phone_needs"),
    ("ph without dot or colon", "|(?<![a-z])ph[.:]", "|(?<![a-z])ph", "phone_needs"),
    ("ID narrowing removed", 'else "narrowed_id"', "else None", "id_numbers_need"),
    ("masked cap removed", "if len(model_text) > MASKED_MAX_CHARS:", "if False:", "masked_text_cap"),
    ("one mark per surface removed", "if surface not in marks:", "if True:", "one_mark_per_surface"),
    ("repr=False removed on Masked.text", "    text: str = field(repr=False)", "    text: str", "repr_holds"),
    ("BodyCheck repr shows the key", 'return "BodyCheck()"', 'return f"BodyCheck({self._key!r})"', "repr_holds"),
    (
        "from None removed",
        'raise SelfCheckFailed("mask_failed") from None\n\n\ndef issued',
        'raise SelfCheckFailed("mask_failed")\n\n\ndef issued',
        "detector_exception",
    ),
    (
        "short values searched as substrings",
        "    if len(value) < 6:\n        for sp in",
        "    if False:\n        for sp in",
        "short_values",
    ),
    ("fingerprint not keyed", "key=key, digest_size=4", "digest_size=4", "recompute_detects"),
    (
        "name reuse check removed",
        "ok = all(_DEAR_BEFORE.search(text[max(0, s - 24) : s].lower()) for s in starts)",
        "ok = True",
        "person_only",
    ),
]


def run_pytest(k: str | None) -> bool:
    cmd = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", TEST]
    if k:
        cmd += ["-k", k]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).returncode == 0  # noqa: S603


def main() -> int:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    original = SRC.read_bytes()
    text = original.decode("utf-8")
    bad = 0
    try:
        for name, old, new, k in MUTANTS:
            if only and only not in name:
                continue
            if text.count(old) != 1:
                print(f"CRASH      {name} :: pattern found {text.count(old)} times")
                bad += 1
                continue
            SRC.write_bytes(text.replace(old, new).encode("utf-8"))
            if not run_pytest(k):
                print(f"KILLED     {name} :: -k {k}")
            elif not run_pytest(None):
                print(f"ELSEWHERE  {name} :: -k {k} stayed green")
                bad += 1
            else:
                print(f"SURVIVED   {name}")
                bad += 1
    finally:
        SRC.write_bytes(original)
    print(f"restore proof: {'ok' if SRC.read_bytes() == original else 'FAILED'}; not killed by its named test: {bad} of {len(MUTANTS)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
