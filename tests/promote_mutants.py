"""Reverts one guard at a time in a temp copy of the package and runs the promoted-controls tests; every mutant must be KILLED
by the intended test (`hadavin_sdk.testing.mutation.judge`). Not collected by pytest. Run from the repo root:

    uv run python tests/promote_mutants.py            # all mutants
    uv run python tests/promote_mutants.py textnorm   # only mutants whose name contains the text
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from hadavin_sdk.testing.mutation import Verdict, first_failure, judge

ROOT = Path(__file__).resolve().parents[1]
SRC = "src/hadavin_sdk/"
TEST = "tests/test_promote_apexc_review8.py"
C, R, A = SRC + "runtime/control.py", SRC + "runtime/rowstore.py", SRC + "audit/capped.py"
N, E, M, G = (
    SRC + "guard/textnorm.py",
    SRC + "guard/egress_text.py",
    SRC + "testing/mutation.py",
    SRC + "approvals/gate.py",
)

# name, file, old, new, expected fragment of the failing test id
MUTANTS = [
    (
        "control: frozen dict accepts edits",
        C,
        "__setitem__ = __delitem__ = update = pop = popitem = clear = setdefault = __ior__ = _refuse",
        "__ior__ = _refuse",
        "test_frozen_views_refuse",
    ),
    (
        "control: frozen dict allows __init__ re-entry",
        C,
        'class FrozenDict(dict):\n    __slots__ = ("_sealed",)\n\n    def __init__(self, data: Any = ()) -> None:\n        if getattr(self, "_sealed", False):',
        'class FrozenDict(dict):\n    __slots__ = ("_sealed",)\n\n    def __init__(self, data: Any = ()) -> None:\n        if False:',
        "test_frozen_views_refuse",
    ),
    (
        "control: frozen list accepts edits",
        C,
        "sort = reverse = __iadd__ = __imul__ = _refuse",
        "pass",
        "test_frozen_views_refuse",
    ),
    (
        "control: sets stay mutable",
        C,
        "return frozenset(freeze(v) for v in o)",
        "return set(freeze(v) for v in o)",
        "test_frozen_views_refuse",
    ),
    (
        "control: unknown mutable types are accepted",
        C,
        'raise TypeError(f"cannot freeze a {type(o).__name__}: only JSON-shaped values and sets")',
        "return o",
        "test_freeze_copies_deeply",
    ),
    (
        "control: freeze shares the caller's objects",
        C,
        "d = FrozenDict.__new__(FrozenDict)\n        dict.__init__(d, {k: freeze(v) for k, v in o.items()})",
        "d = FrozenDict.__new__(FrozenDict)\n        dict.__init__(d, o)",
        "test_freeze_copies_deeply",
    ),
    (
        "control: swap does not count versions",
        C,
        "self._view.version + 1",
        "self._view.version",
        "test_the_holder_gives_one_consistent_pair",
    ),
    (
        "control: effect ignores an engaged gate",
        C,
        'if self._on:\n                raise EffectBlocked("stop gate engaged")',
        'if False:\n                raise EffectBlocked("stop gate engaged")',
        "test_a_port_that_checks_outside",
    ),
    (
        "control: engage does not wait for effects in flight",
        C,
        "drained = self._cond.wait_for(lambda: self._inflight == 0, timeout=timeout)",
        "drained = True",
        "test_engage_waits_for_effects_in_flight",
    ),
    (
        "control: blocked ignores the durable switch",
        C,
        "return bool(self._store is not None and self._store.get_kill_switch().on)",
        "return False",
        "test_the_gate_is_not_the_stored_kill_switch",
    ),
    (
        "control: engage does not write the durable switch",
        C,
        "self._store.set_kill_switch(KillSwitch(on=True, by=_label(by)))",
        "pass",
        "test_the_gate_is_not_the_stored_kill_switch",
    ),
    (
        "control: one failing undo stops the sweep",
        C,
        "except Exception as e:  # noqa: BLE001 - per-item choke point",
        "except ZeroDivisionError as e:",
        "test_one_failing_undo",
    ),
    (
        "control: an interrupt loses the partial result",
        C,
        'res.results.append((item, "interrupted"))',
        "pass",
        "test_one_failing_undo",
    ),
    (
        "control: the free-text label is stored raw",
        C,
        'return who if isinstance(who, str) and _LABEL.fullmatch(who) else "?"',
        "return who",
        "test_one_failing_undo",
    ),
    (
        "rowstore: audit after the insert",
        R,
        "            append(kind, key=key)  # audit before the write; raises -> nothing is inserted\n            with self._lock:\n                self._rows[key] = clean",
        "            with self._lock:\n                self._rows[key] = clean\n            append(kind, key=key)",
        "test_the_row_store_meets_the_contract",
    ),
    (
        "rowstore: a row is not validated before the audit",
        R,
        "clean = copy_row(row)  # validate and copy first",
        "clean = row",
        "test_a_bad_row_fails_before_the_audit",
    ),
    (
        "rowstore: int keys are accepted",
        R,
        "type(k) is str and json_keys_ok(v)",
        "json_keys_ok(v)",
        "test_a_bad_row_fails_before_the_audit",
    ),
    (
        "rowstore: NaN is accepted",
        R,
        "allow_nan=False",
        "allow_nan=True",
        "test_a_bad_row_fails_before_the_audit",
    ),
    (
        "rowstore: a key is not reserved during its audit",
        R,
        "if key in self._rows or key in self._pending:",
        "if key in self._rows:",
        "test_an_audit_callback_can_read_the_store",
    ),
    (
        "rowstore: get returns the live row",
        R,
        "return copy_row(self._rows[key])",
        "return self._rows[key]",
        "test_the_row_store_meets_the_contract",
    ),
    (
        "rowstore: snapshot returns the live rows",
        R,
        "return {k: copy_row(v) for k, v in self._rows.items()}",
        "return dict(self._rows)",
        "test_the_row_store_meets_the_contract",
    ),
    (
        "capped: the cap is not enforced",
        A,
        "over, need_marker = n > self._cap, n > self._cap and not marked",
        "over, need_marker = False, False",
        "test_capped_audit_is_per_tenant",
    ),
    (
        "capped: tenants share one counter",
        A,
        "self._n.get((tenant, kind), (bucket, 0, False))",
        'self._n.get(("*", kind), (bucket, 0, False))',
        "test_capped_audit_is_per_tenant",
    ),
    (
        "capped: a new bucket does not reset",
        A,
        "if b != bucket:\n                b, n, marked = bucket, 0, False",
        "if False:\n                b, n, marked = bucket, 0, False",
        "test_capped_audit_is_per_tenant",
    ),
    (
        "capped: a failed marker is never retried",
        A,
        'self._append("audit_suppressed", tenant=tenant, suppressed_kind=kind, bucket=bucket)',
        'self._n[(tenant, kind)] = (bucket, self._n[(tenant, kind)][1], True)\n                self._append("audit_suppressed", tenant=tenant, suppressed_kind=kind, bucket=bucket)',
        "test_capped_audit_retries",
    ),
    (
        "textnorm: combining marks are kept",
        N,
        '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs"}',
        '{"Cc", "Cf", "Me", "Zl", "Zp", "Co", "Cs"}',
        "test_fold_is_stable",
    ),
    (
        "textnorm: look-alikes are not folded",
        N,
        ".translate(_digit_table()).translate(_TABLE)",
        ".translate(_digit_table())",
        "test_fold_covers_the_listed",
    ),
    (
        "textnorm: other scripts' digits are not folded",
        N,
        ".translate(_digit_table())",
        "",
        "test_fold_covers_the_listed",
    ),
    (
        "textnorm: Armenian and dotless i are missing",
        N,
        '((0x131, 0x130), "iI"),  # dotless i, dotted capital I',
        "",
        "test_fold_covers_the_listed",
    ),
    (
        "egress_text: the length is not bounded first",
        E,
        "if len(text) > policy.max_len:",
        "if False:",
        "test_short_protected_values_raise",
    ),
    (
        "egress_text: a short protected value is accepted",
        E,
        "if len(k) < policy.min_protected_len:",
        "if False:",
        "test_short_protected_values_raise",
    ),
    (
        "egress_text: side-by-side exempt tokens pass",
        E,
        "or _MARK_RUN.search(t)",
        "",
        "test_exempt_tokens_are_not_a_free_pass",
    ),
    (
        "egress_text: exempt tokens are uncapped",
        E,
        "t.count(_MARK) > policy.max_exempt_tokens",
        "False",
        "test_exempt_tokens_are_not_a_free_pass",
    ),
    (
        "egress_text: amounts need no currency",
        E,
        "(_AMOUNT_ANCHORED if policy.amounts_need_currency else _AMOUNT_ANY)",
        "_AMOUNT_ANY",
        "test_exempt_tokens_are_not_a_free_pass",
    ),
    (
        "egress_text: digit-like letters are not counted",
        E,
        "elif ch in _DIGITISH and chained:",
        "elif False:",
        "test_digit_like_letters_count",
    ),
    (
        "egress_text: the digit budget is off by one",
        E,
        "if _digitish_count(t) >= policy.max_digits:",
        "if _digitish_count(t) > policy.max_digits:",
        "test_digit_budget_beats",
    ),
    (
        "egress_text: an allowed reference needs no boundary",
        E,
        'r"(?<![A-Za-z0-9])" + re.escape(fa) + r"(?![A-Za-z0-9])"',
        "re.escape(fa)",
        "test_allowed_references_need_a_boundary",
    ),
    (
        "egress_text: an allowed reference is case-sensitive",
        E,
        "flags=re.IGNORECASE",
        "flags=0",
        "test_allowed_references_need_a_boundary",
    ),
    (
        "textnorm: digit-like letters S B Z G Q are not mapped",
        N,
        '"OILSBZGQ", "01158269"',
        '"OIL", "011"',
        "test_a_protected_number_is_found",
    ),
    (
        "egress_text: a protected number is not found through junk",
        E,
        "any(kd in s for s in sq_digits)",
        "False",
        "test_a_protected_number_is_found",
    ),
    (
        "egress_text: an allowed value that folds to nothing hides everything",
        E,
        "if fa:",
        "if True:",
        "test_allowed_references_need_a_boundary",
    ),
    (
        "egress_text: protected values are not checked",
        E,
        "for k in keys:  # the most specific finding first",
        "for k in []:",
        "test_what_passes_and_the_full_homoglyph_fold",
    ),
    (
        "egress_text: thresholds are not validated",
        E,
        'raise ValueError("max_digits must be an int in 1..64")',
        "pass",
        "test_thresholds_come_from_a_validated_policy",
    ),
    (
        "mutation: an exception line counts as a kill",
        M,
        "return Verdict.KILLED if _ASSERTION.search(first_line.strip()) else Verdict.CRASH",
        "return Verdict.KILLED",
        "test_mutation_judge_verdicts",
    ),
    (
        "mutation: crash markers are ignored",
        M,
        "for m in crash_markers:",
        "for m in ():",
        "test_mutation_judge_verdicts",
    ),
    (
        "gate: views skip the shared fold",
        G,
        "textnorm.fold(v) for v in views",
        "v for v in views",
        "test_gate_views_use_the_shared_fold",
    ),
]


def run(cwd: Path) -> tuple[int, str]:
    env = dict(os.environ, PYTHONPATH=str(cwd / "src"))
    r = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", TEST],
        cwd=cwd, env=env, capture_output=True, text=True, check=False,
    )  # fmt: skip
    return r.returncode, r.stdout


def main(only: list[str]) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="promote_mutants_"))
    bad = []
    try:
        for name, f, old, new, expect in MUTANTS:
            if only and not any(o in name for o in only):
                continue
            shutil.rmtree(tmp, ignore_errors=True)
            (tmp / "tests").mkdir(parents=True)
            shutil.copytree(ROOT / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy(ROOT / TEST, tmp / TEST)
            shutil.copytree(
                ROOT / "tests" / "fixtures", tmp / "tests" / "fixtures", dirs_exist_ok=True
            )
            p = tmp / f
            t = p.read_text(encoding="utf-8")
            if old not in t:
                print(f"SNIPPET NOT FOUND  {name}")
                bad.append(name)
                continue
            p.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
            rc, out = run(tmp)
            _, first = first_failure(out)
            test_id = ", ".join(
                ln.removeprefix("FAILED ").split(" - ")[0]
                for ln in out.splitlines()
                if ln.startswith("FAILED ")
            )
            v = judge(rc, test_id, first, expect=expect)
            print(f"{v:12} {name}  [{test_id.split('::')[-1][:60]}] {first[:70]}")
            if v not in (Verdict.KILLED, Verdict.CRASH):
                bad.append(name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(MUTANTS) - len(bad) if not only else 'partial'} not-bad; problems: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
