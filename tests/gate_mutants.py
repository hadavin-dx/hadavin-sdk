"""The mutants of the model gate (step F, ORDER 008), run by the P1m runner (``tools/mutation_runner.py``).

Same format as ``tests/stage_mutants.py``: each mutant reverts ONE guard of ``guard/model_gate.py`` (G...) or of
``guard/runmap.py`` (R...: ``enforce_map`` and ``redact_text``) in a temp copy of the package; the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment of the assertion
MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/gate_mutants.py            # all mutants; exit 1 if any is not good
    python tests/gate_mutants.py G3         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_model_gate.py"
MAP_TEST = "tests/test_runmap_enforce_map.py"
GATE = "src/hadavin_sdk/guard/model_gate.py"
RUNMAP = "src/hadavin_sdk/guard/runmap.py"


def mutant(name, old, new, killer, expect, file=GATE, test=TEST):
    pin = test.removesuffix(".py") + "::" + killer
    return Mutant(name, file, old, new, expect, test_file=test, only_test=killer, pinned=pin)


I9 = "test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state"
I9_SAYS = "exception text, a logger or message text in the gate"

M = [
    # --- no call without a reservation; an enforce failure means no call ---
    mutant("G1 a refused reservation is swallowed and the client is called without a reservation",
        "            self._note(RESULT_REFUSED, reason if published else CODE_RESERVE_REFUSED)\n            raise\n",
        '            reserved, reservation = Decimal(0), "none"\n',
        "test_pin_no_client_call_without_a_reservation", "a client call without a reservation"),
    mutant("G2a a failing enforce step sends the caller's text as it is",
        "        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call\n            return None\n",
        "        except Exception:  # noqa: BLE001\n            return list(messages), documents\n",
        "test_pin_a_failing_enforce_step_means_no_call", "the client was called after a failed enforce step"),
    mutant("G2b a content that is not a str is passed on",
        "                if not isinstance(content, str):\n                    return None\n",
        "",
        "test_pin_a_content_that_is_not_a_str_means_no_call", "the client was called with a content that is not a str"),
    # --- known originals replaced, in what is really sent ---
    mutant("G3a the enforce step is skipped",
        "                if mapping is not None:\n", "                if False:\n",
        "test_t5_a_raw_value_that_is_in_the_map_is_replaced_in_document_bytes_never_sent", "known originals replaced"),
    mutant("G3b the caller's originals are sent instead of the enforced copies",
        "        messages, documents = enforced  # from here on only the enforced copies are used\n",
        "        messages, documents = list(messages), documents\n",
        "test_t5_a_raw_value_that_is_in_the_map_is_replaced_in_document_bytes_never_sent", "known originals replaced"),
    mutant("G3c the document is checked but the unchanged bytes are sent",
        '                        document = fixed.encode("utf-8")\n', "                        pass\n",
        "test_t5_a_raw_value_that_is_in_the_map_is_replaced_in_document_bytes_never_sent", "known originals replaced"),
    mutant("G3d the caller's message dict is changed in place",
        '                        message = {**message, "content": fixed}\n',
        '                        message["content"] = fixed\n',
        "test_the_callers_messages_dicts_and_documents_are_not_mutated", "the caller's objects were changed"),
    # --- the one settle rule (ORDER 011): (a) real cost ---
    mutant("G4a no settle on success",
        "            self._settle(reservation, cost, RESULT_OK, None)\n",
        "            self._note(RESULT_OK, None, reservation)\n",
        "test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost", "settle on success"),
    mutant("G4b the worst case is settled on success, not the real cost",
        "            self._settle(reservation, cost, RESULT_OK, None)\n",
        "            self._settle(reservation, reserved, RESULT_OK, None)\n",
        "test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost", "settle on success"),
    mutant("G4c a reply whose cost is not a number is settled with it",
        "    if isinstance(cost, Decimal) and cost.is_finite() and cost >= 0:\n",
        "    if isinstance(cost, Decimal):\n",
        "test_pin_a_reply_with_no_usable_cost_is_not_settled", "a reply with no usable cost was settled"),
    # --- (c) everything else: NOT settled ---
    mutant("G5 a KeyboardInterrupt is settled at the worst case",
        "            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, reservation)\n",
        "            self._settle(reservation, reserved, RESULT_FAILED, CODE_CALL_INTERRUPTED)\n",
        "test_pin_no_settle_on_keyboard_interrupt", "settled after a KeyboardInterrupt"),
    mutant("G6a an unmarked ProviderError is settled at 0 (every provider error counts as refused)",
        "            if refused_before_response(exc):  # rule (b): it cost nothing\n",
        "            if True:\n",
        "test_pin_an_unmarked_provider_error_is_not_settled", "an unmarked provider error was settled"),
    mutant("G6b the predicate says yes without the mark",
        '    marked = getattr(exc, "refused_before_response", False) is True\n',
        "    marked = True\n",
        "test_pin_an_unmarked_provider_error_is_not_settled", "an unmarked provider error was settled"),
    mutant("G6c an unmarked provider error is settled at the worst case",
        "                self._note(RESULT_FAILED, code, reservation)\n",
        "                self._settle(reservation, reserved, RESULT_FAILED, code)\n",
        "test_pin_an_unmarked_provider_error_is_not_settled", "an unmarked provider error was settled"),
    mutant("G6d a generic exception is settled",
        "            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation)\n",
        "            self._settle(reservation, reserved, RESULT_FAILED, CODE_CALL_FAILED)\n",
        "test_pin_a_generic_exception_is_not_settled", "a generic exception was settled"),
    # --- (b) marked refused before any response: settled at 0 ---
    mutant("G6e the mark is ignored: a marked refusal is not settled",
        "            if refused_before_response(exc):  # rule (b): it cost nothing\n",
        "            if False:\n",
        "test_pin_a_marked_refusal_is_settled_at_zero", "a marked refusal was not settled at 0"),
    mutant("G6f a marked refusal is settled at the worst case, not 0",
        "                self._settle(reservation, Decimal(0), RESULT_FAILED, CODE_PROVIDER_REFUSED)\n",
        "                self._settle(reservation, reserved, RESULT_FAILED, CODE_PROVIDER_REFUSED)\n",
        "test_pin_a_marked_refusal_is_settled_at_zero", "a marked refusal was not settled at 0"),
    # --- M1: the source guard can fail, on code inside method bodies ---
    mutant("G7a exception text goes into an audit row (str(exc) in chat)",
        "            self._note(RESULT_REFUSED, reason if published else CODE_RESERVE_REFUSED)\n",
        "            self._note(RESULT_REFUSED, reason if published else str(exc)[:60])\n",
        I9, I9_SAYS),
    mutant("G7b a logger in _settle",
        "            code = CODE_SETTLE_FAILED\n",
        '            code = CODE_SETTLE_FAILED\n            import logging\n\n            logging.getLogger(__name__).exception("settle failed")\n',
        I9, I9_SAYS),
    mutant("G7c the exception chain is kept in _enforced (__cause__)",
        "        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call\n            return None\n",
        "        except Exception as exc:  # noqa: BLE001\n            self._why = exc.__cause__\n            return None\n",
        I9, I9_SAYS),
    mutant("G7d message text in the raised refusal",
        "            raise UnmaskedInput  # raised outside",
        "            raise UnmaskedInput(messages)  # raised outside",
        I9, I9_SAYS),
    mutant("G7e a free field in the audit row",
        "                    error_code=error_code,\n",
        "                    error_code=error_code,\n                    decision=self._agent_id,\n",
        I9, I9_SAYS),
    # --- minors m2, m3, m4 ---
    mutant("G8a a paid call whose settle failed is written as failed",
        "            code = CODE_SETTLE_FAILED\n",
        "            code, result = CODE_SETTLE_FAILED, RESULT_FAILED\n",
        "test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok", "a paid call was written as failed"),
    mutant("G8b any reason shaped like text becomes the audit code",
        "            published = isinstance(reason, str) and reason in SPEND_REASONS\n",
        "            published = isinstance(reason, str)\n",
        "test_m4_only_the_published_reasons_become_an_audit_code", "a reason that is not published was copied"),
    # --- guard/runmap.py: the enforce step itself and the live map ---
    mutant("R1 enforce_map hands the sweep the caller's cache",
        '            cache = dict(getattr(mapping, "redact_cache", None) or {})\n            return _Redactor(known, cache).sweep(text)\n',
        '            cache = getattr(mapping, "redact_cache", None)\n            return _Redactor(known, cache).sweep(text)\n',
        "test_pin_the_callers_cache_is_never_written_even_when_the_patterns_must_be_rebuilt", "the caller's cache was written",
        file=RUNMAP, test=MAP_TEST),
    mutant("R2 the held-back sweep is dropped: a placeholder written in this pass is rewritten",
        "        if not late:\n", "        if True:\n",
        "test_a_placeholder_inserted_in_this_pass_is_not_rewritten_by_a_later_shorter_original",
        "a placeholder inserted in this pass was rewritten",
        file=RUNMAP, test=MAP_TEST),
    mutant("R3 redact_text empties the live map before it writes it",
        "    mapping.update(current)\n    return out\n",
        "    mapping.clear()\n    mapping.update(current)\n    return out\n",
        "test_m4_redact_text_never_empties_the_map_on_the_way", "the live map was emptied during a write",
        file=RUNMAP, test=MAP_TEST),
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
        [TEST, MAP_TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
