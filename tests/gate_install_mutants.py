"""Mutants of step F-install (the model gate installed in every place that calls a model): M1 to M4 and M6 to M12 of
the ticket's section 11 as corrected by the review rounds (M5 dropped: the store adds the run cost, F-store's mutant 20
covers it), named by TEXT and not by line, plus the extras the test writer added (M13 and up). Run by the P1m runner
(``tools/mutation_runner.py``).

Each mutant reverts ONE install guard in a temp copy of the package; the pinned test must be the one that fails first, and
its first failing line must hold ``expect`` (a fragment of the assertion MESSAGE). The killers are in
``tests/test_model_gate_install.py`` and ``tests/contracts/test_meter.py`` (they define their own fixtures, because the
runner uses --noconftest). No database is needed. Not collected by pytest. Run from the repo root:

    uv run --all-extras --group test python tests/gate_install_mutants.py          # all; exit 1 if any is not good
    uv run --all-extras --group test python tests/gate_install_mutants.py M8       # only names that hold the text

The unmutated baseline must be green. While core-c's gate audits a usd_cap refusal as reserve_refused (its SPEND_REASONS
lacks usd_cap), test_the_gate_audits_each_of_the_six_published_reasons_as_the_error_code[usd_cap] fails and the runner
refuses to start: fix the gate (or xfail that one case) first.

Equivalent mutants: none known. A mutant that survives is a hole in the tests, never an excuse.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
INSTALL = "tests/test_model_gate_install.py"
METER = "tests/contracts/test_meter.py"
LOOP = "src/hadavin_sdk/runtime/agent_loop.py"
LIMITS = "src/hadavin_sdk/limits.py"
COMMON = "src/hadavin_sdk/llm/common.py"
INJECTION = "src/hadavin_sdk/guard/injection.py"
EVALS = "src/hadavin_sdk/evals.py"
K1B = "src/hadavin_sdk/k1b/loop.py"
MEMORY = "src/hadavin_sdk/store/memory.py"
SITE = "test_a_meter_refusal_ends_the_run_by_the_mapping_at_every_site"
WRONG = "wrong ending"
ESCAPED = "the refusal escaped handle and stranded"


def mutant(name, file, old, new, killer, expect, *, test_file=INSTALL, pin=None):
    stem = test_file.removesuffix(".py")
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=f"{stem}::{pin or killer}",
    )


M = [
    mutant("M1 the bind line removed in handle (the chat goes to the raw client)", LOOP,
        "reply = self._bound_llm(run, rmap).chat(", "reply = self.llm.chat(",
        "test_n1_one_run_books_spend_run_cost_and_one_audit_row", "was not reserved on the meter"),
    mutant("M2 _screen uses the raw detector", LOOP,
        "return injection_check(self._bound_detector(run), text, source)",
        "return injection_check(self.detector, text, source)",
        "test_n2_a_judge_in_the_run_settles_twice_into_the_run_cost", "must each settle once in the run"),
    mutant("M3 _shadow passes self.detector", LOOP,
        "detector=self._bound_detector(run)", "detector=self.detector",
        "test_n3_the_shadow_card_judge_is_charged_to_the_runs_agent", "shadow-card judge call was not booked"),
    mutant("M4a the old run-cost line is restored (run cost counted twice)", LOOP,
        "            if reply.stop_reason in (\n",
        "            self.store.add_cost(run.run_id, reply.cost_usd)\n            if reply.stop_reason in (\n",
        "test_n1_one_run_books_spend_run_cost_and_one_audit_row", "run cost is not the sum of the settles"),
    mutant("M4b the old day-spend line is restored (spend counted twice)", LOOP,
        "            if reply.stop_reason in (\n",
        "            self.store.add_spend(run.agent_id, run.created_at.date(), reply.cost_usd)\n"
        "            if reply.stop_reason in (\n",
        "test_n1_one_run_books_spend_run_cost_and_one_audit_row", "day spend is not the settled cost"),
    mutant("M6a forfeit does not turn an open hold into spend", LIMITS,
        'row[2] = "forfeited"', 'row[2] = "open"',
        "test_e6_a_late_settle_after_forfeit_raises_the_booked_amount_only_above_the_worst_case",
        "a late settle lowered a forfeited hold"),
    mutant("M6b forfeit does not close the run id", LIMITS,
        "self._closed.add(run_id)", "pass",
        "test_e6_forfeit_closes_its_run_id_and_no_other", "DID NOT RAISE"),
    mutant("M7 spent ignores holds", LIMITS,
        "return sum((row[1] for row in self._rows.values()), Decimal(0))",
        'return sum((row[1] for row in self._rows.values() if row[2] != "open"), Decimal(0))',
        "test_e8_holds_count_toward_the_limit", "DID NOT RAISE"),
    mutant("M8 the Budget lock is removed", LIMITS,
        "self._lock = threading.Lock()", 'self._lock = __import__("contextlib").nullcontext()',
        "test_e8_twenty_threads_on_one_budget_never_pass_the_limit", "the budget was passed"),
    mutant("M9 the evals.gate wrap is removed (the raw client is called)", EVALS,
        'llm = llm.bind(f"eval:{agent_id}", new_id("eval"))',
        "llm = llm._llm if isinstance(llm, ModelGate) else llm",
        "test_n4_evals_with_max_usd_stops_at_the_cap", "DID NOT RAISE"),
    mutant("M10 the replay detector is not bound", K1B,
        "bound = bind_detector(detector, wrap, agent_id, case_run_id)", "bound = detector",
        "test_n5_a_judge_call_in_replay_is_booked_on_the_same_budget",
        "the replay judge call was not booked"),
    mutant("M11a the refusal except is removed at the chat call (run stranded)", LOOP,
        "except (SpendRefused, GateRefused) as exc:  # no call was made",
        "except ZeroDivisionError as exc:  # no call was made",
        "test_h6_reserve_raising_store_unavailable_ends_needs_person_never_working", ESCAPED),
    mutant("M11b the refusal except is removed at the document screen", LOOP,
        'verdict = self._screen(run, safe_text, "document")\n        except (SpendRefused, GateRefused) as exc:',
        'verdict = self._screen(run, safe_text, "document")\n        except ZeroDivisionError as exc:',
        SITE, ESCAPED, pin=SITE + "[document-a_reason_nobody_published]"),
    mutant("M11c the refusal except is removed at the tool-result screen", LOOP,
        'verdict = self._screen(run, out.text, f"tool:{call.name}")\n                except (SpendRefused, GateRefused) as exc:',
        'verdict = self._screen(run, out.text, f"tool:{call.name}")\n                except ZeroDivisionError as exc:',
        SITE, "the refusal escaped handle and stranded the tool-result", pin=SITE + "[tool-a_reason_nobody_published]"),
    mutant("M11d a refusal in the shadow judge ends as an undelivered card, not by the mapping", LOOP,
        "# no card: the refusal is not a verdict on the text\n            return self._refused(run, exc, cited)",
        "# no card: the refusal is not a verdict on the text\n            card = None",
        SITE, WRONG, pin=SITE + "[shadow-a_reason_nobody_published]"),
    mutant("M12a Budget.settle is not idempotent", LIMITS,
        'if state != "settled":', "if True:",
        "test_p3_settle_twice_the_first_wins_and_the_repeat_returns_the_first_result",
        "a repeat did not return the first result", test_file=METER,
        pin="test_p3_settle_twice_the_first_wins_and_the_repeat_returns_the_first_result[budget]"),
    mutant("M12b the memory store settle is not idempotent (Limits)", MEMORY,
        'if row.status == "settled":', "if False:",
        "test_p3_settle_twice_the_first_wins_and_the_repeat_returns_the_first_result",
        "a repeat did not return the first result", test_file=METER,
        pin="test_p3_settle_twice_the_first_wins_and_the_repeat_returns_the_first_result[limits]"),
    mutant("M13 the unknown-route fallback is removed", COMMON,
        "for r in ([known] if known is not None else routes.values())", "for r in [known]",
        "test_an_unknown_route_name_is_priced_at_the_largest_worst_case",
        "an unknown route name was refused"),
    mutant("M14 the re-raise in injection_check is removed (a refusal becomes a flag)", INJECTION,
        "if isinstance(exc, SpendRefused | GateRefused):", "if False:",
        "test_injection_check_raises_a_refusal_and_flags_any_other_error", "DID NOT RAISE"),
    mutant("M15a _refused maps daily_budget to the monthly code", LOOP,
        '"daily_budget": (S.NEEDS_PERSON, "limits.daily_budget"),',
        '"daily_budget": (S.NEEDS_PERSON, "limits.monthly_budget"),',
        SITE, WRONG, pin=SITE + "[document-daily_budget]"),
    mutant("M15b _refused maps kill_switch to NEEDS_PERSON", LOOP,
        '"kill_switch": (S.STOPPED, "kill_switch"),',
        '"kill_switch": (S.NEEDS_PERSON, "kill_switch"),',
        SITE, WRONG, pin=SITE + "[document-kill_switch]"),
    mutant("M15c _refused maps an unknown reason to gate_error", LOOP,
        '(S.NEEDS_PERSON, "limits_unavailable"))', '(S.NEEDS_PERSON, "gate_error"))',
        SITE, WRONG, pin=SITE + "[document-a_reason_nobody_published]"),
    mutant("M16 the run's live map is not handed to the gate", LOOP,
        "bind(run.agent_id, run.run_id, mapping=mapping)", "bind(run.agent_id, run.run_id)",
        "test_e3_a_model_gate_in_rt_llm_is_used_as_it_is", "live map is not handed to the gate"),
    mutant("M17 evals in pilot and prod no longer needs a cap", EVALS,
        "if is_live(cfg.environment):", "if False:",
        "test_e7_evals_in_pilot_without_max_usd_is_a_config_error", "DID NOT RAISE"),
    mutant("M18 the requests multiplier is dropped from the worst case", COMMON,
        "requests = attempts if type(attempts) is int and attempts >= 1 else 1", "requests = 1",
        "test_worst_case_for_multiplies_by_the_requests", "assert Decimal",
        pin="test_worst_case_for_multiplies_by_the_requests[3-None-3]"),
    mutant("M19 the output schema is counted once, not twice", COMMON,
        "size += 2 * _json_bytes(output_schema)", "size += _json_bytes(output_schema)",
        "test_worst_case_counts_system_messages_tools_documents_and_schema_twice",
        "the schema is counted twice"),
    mutant("M20 replay does not forfeit the case at its end", K1B,
        "budget.forfeit(case_run_id)", "pass",
        "test_replay_the_budget_is_forfeited_per_case_whatever_the_ending", "DID NOT RAISE"),
    mutant("M21 a replay cap hit is an abort, not a capped case", K1B,
        'if exc.reason == "usd_cap":', "if False:",
        "test_replay_a_refused_chat_ends_the_case_without_raising", "assert (",
        pin="test_replay_a_refused_chat_ends_the_case_without_raising[<lambda>-capped-usd_cap-capped]"),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [INSTALL, METER],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
