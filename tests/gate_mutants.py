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
WRITE_TEST = "tests/test_runmap_map_write.py"
GATE = "src/hadavin_sdk/guard/model_gate.py"
RUNMAP = "src/hadavin_sdk/guard/runmap.py"


def mutant(name, old, new, killer, expect, file=GATE, test=TEST, param=""):
    """`param`: the id of the first parameter of a parametrized killer, as junit writes it (`[none]`)."""
    pin = test.removesuffix(".py") + "::" + killer + param
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
    mutant("G3a the enforce step is skipped for messages",
        "                if mapping is not None:\n                    fixed = self._enforce(content, mapping)\n",
        "                if False:\n                    fixed = self._enforce(content, mapping)\n",
        "test_pin_a_known_value_in_a_message_is_replaced", "known originals replaced in messages"),
    mutant("G3e the enforce step is skipped for documents",
        "                if mapping is not None:\n                    text = document.decode",
        "                if False:\n                    text = document.decode",
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
        "    return isinstance(value, Decimal) and value.is_finite() and value >= 0\n",
        "    return isinstance(value, Decimal)\n",
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
        "                    error_code=error_code,\n                    rule_id=self._agent_id,\n",
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
        '            first = _Redactor(known, dict(getattr(mapping, "redact_cache", None) or {}))\n',
        '            first = _Redactor(known, getattr(mapping, "redact_cache", None))\n',
        "test_pin_the_callers_cache_is_never_written_even_when_the_patterns_must_be_rebuilt", "the caller's cache was written",
        file=RUNMAP, test=MAP_TEST),
    mutant("R2 the held-back sweep is dropped: a placeholder written in this pass is rewritten",
        "        elif late:\n", "        elif False:\n",
        "test_a_placeholder_inserted_in_this_pass_is_not_rewritten_by_a_later_shorter_original",
        "a placeholder inserted in this pass was rewritten",
        file=RUNMAP, test=MAP_TEST),
    mutant("R3 redact_text empties the live map before it writes it",
        "    mapping.update(current)\n    return out\n",
        "    mapping.clear()\n    mapping.update(current)\n    return out\n",
        "test_m4_redact_text_never_empties_the_map_on_the_way", "the live map was emptied during a write",
        file=RUNMAP, test=MAP_TEST),
    mutant("R3b redact_text writes a changed value for the first earlier entry",
        "    mapping.update(current)\n    return out\n",
        '    mapping.update({**current, **dict.fromkeys(list(mapping)[:1], "")})\n    return out\n',
        "test_a_write_never_removes_or_changes_an_earlier_entry_by_any_route", "an earlier entry was dropped or changed",
        file=RUNMAP, test=WRITE_TEST, param="[redact_text]"),
    mutant("R3c redact_text removes entries with pop before it writes",
        "    mapping.update(current)\n    return out\n",
        "    for key in list(mapping):\n        mapping.pop(key)\n    mapping.update(current)\n    return out\n",
        "test_a_write_never_removes_or_changes_an_earlier_entry_by_any_route", "an entry was removed during a write",
        file=RUNMAP, test=WRITE_TEST, param="[redact_text]"),
    mutant("R4 enforce_map stops after one sweep: not a fixed point (MJ2)",
        "            if out == before:\n                return out\n",
        "            return out\n",
        "test_mj2_an_identifier_glued_to_a_shorter_secret_is_replaced_too", "enforce_map is not idempotent",
        file=RUNMAP, test=MAP_TEST),
    mutant("R5 the sweep cap is dropped: a chain that never settles is returned half done",
        '    raise RedactionError("NotSettled")',
        "    return out",
        "test_mj2_a_chain_settles_within_the_cap_and_is_refused_past_it", "DID NOT RAISE",
        file=RUNMAP, test=MAP_TEST),
    mutant("R6 enforce_map applies the redaction cap, not its own (E1)",
        "        if len(text) > ENFORCE_MAX_CHARS:\n",
        "        if len(text) > defaults.MAX_REDACT_CHARS:\n",
        "test_e1_a_document_near_the_cap_of_short_values_is_not_refused_after_masking", "a document near the cap was refused",
        file=RUNMAP, test=MAP_TEST),
    mutant("R7 a value at the edge of a placeholder is not held back (E2)",
        "            if (original in tokens or _is_edge_value(original)) and _sweep(ph, original) is not None\n",
        "            if original in tokens and _sweep(ph, original) is not None\n",
        "test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass", "a placeholder was cut open",
        file=RUNMAP, test=MAP_TEST),
    mutant("R8 one original under two placeholders keeps the weaker rule (E5)",
        "        if _rules_conflict(known):\n", "        if False:\n",
        "test_e5_one_original_under_two_placeholders_follows_the_stronger_rule", "the weaker rule won",
        file=RUNMAP, test=MAP_TEST),
    mutant("R9 enforce_map has no time budget",
        "            if time.monotonic() - started > defaults.REDACT_BUDGET_S:\n                raise InputTooLarge",
        "            if False:\n                raise InputTooLarge",
        "test_m_new_1_enforce_map_has_the_redactors_time_budget", "DID NOT RAISE",
        file=RUNMAP, test=MAP_TEST),
    mutant("R10 a value the sweep never replaces is held back (m-new-1)",
        " and _sweep(ph, original) is not None\n        }\n", "\n        }\n",
        "test_m_new_1_a_map_of_many_short_values_builds_one_redactor_and_none_per_value", "a redactor was built for a value the sweep never replaces",
        file=RUNMAP, test=MAP_TEST),
    mutant("R11 the growth of one sweep has no hard bound (E1)",
        "            if len(out) > ENFORCE_MAX_OUT_CHARS:\n", "            if False:\n",
        "test_e1_a_sweep_that_grows_past_the_output_bound_is_refused", "DID NOT RAISE",
        file=RUNMAP, test=MAP_TEST),
    # --- design review: D1 to D9, E4 ---
    mutant("G9 a reservation is made before the enforce step",
        "        enforced = self._enforced(messages, documents)\n",
        "        self._meter.reserve(self._agent_id, Decimal(1), run_id=self._run_id)\n        enforced = self._enforced(messages, documents)\n",
        "test_pin_a_failing_enforce_step_means_no_call", "a reservation after a failed enforce step"),
    mutant("G10 the audit row is dropped",
        "            self._audit.write_outcome(\n", "            (lambda event: None)(\n",
        "test_pin_every_outcome_writes_exactly_one_audit_row", "an outcome without exactly one audit row"),
    mutant("G11 a gate may be wrapped by a second gate",
        "        if isinstance(llm, ModelGate | BoundGate):\n", "        if False:\n",
        "test_pin_a_gate_is_never_wrapped_twice_in_either_form", "a gate was wrapped by a second gate"),
    mutant("G12 a flagged ProviderExhausted counts as refused before response",
        "    return marked and isinstance(exc, ProviderError) and not isinstance(exc, ProviderExhausted)\n",
        "    return marked and isinstance(exc, ProviderError)\n",
        "test_pin_the_mark_counts_only_on_a_provider_error_that_is_not_exhausted", "a flagged ProviderExhausted counted"),
    mutant("G13 a flagged error that is not a ProviderError counts as refused before response",
        "    return marked and isinstance(exc, ProviderError) and not isinstance(exc, ProviderExhausted)\n",
        "    return marked and not isinstance(exc, ProviderExhausted)\n",
        "test_pin_the_mark_counts_only_on_a_provider_error_that_is_not_exhausted", "a flagged non-ProviderError counted"),
    mutant("G14 a document that is not bytes is passed on",
        "                if not isinstance(document, bytes):\n                    return None\n", "",
        "test_pin_a_document_that_is_not_bytes_means_no_call", "a document that is not bytes"),
    mutant("G15 the audit code allowlist is not enforced in _note",
        "            error_code = CODE_GATE_REFUSED  # AUDIT_CODES is enforced here, not only listed\n", "            pass\n",
        "test_e4_note_enforces_the_allowlist_a_code_outside_it_is_never_written", "a code outside the allowlist"),
    mutant("G16 a worst case that is not a finite Decimal >= 0 reaches reserve",
        "        if not usable_amount(reserved):\n", "        if False:\n",
        "test_d2_a_worst_case_that_is_not_a_finite_decimal_of_zero_or_more_is_refused_before_reserve", "DID NOT RAISE", param="[none]"),
    mutant("G17 a reservation id that is not a non-empty str is used",
        "        if not (isinstance(reservation, str) and reservation):\n", "        if False:\n",
        "test_d3_a_reservation_id_that_is_not_a_non_empty_str_means_no_call", "DID NOT RAISE", param="[17]"),
    mutant("G18 an overshoot is dropped from the ok row",
        "                code = CODE_OVERSHOOT\n", "                pass\n",
        "test_a_settle_above_the_reservation_is_passed_through", "the overshoot code is missing"),
    mutant("G19 the map is copied once per text, not once per call (D9)",
        "                mapping = runmap.snapshot(mapping)\n", "                pass\n",
        "test_d9_one_map_snapshot_and_one_redactor_per_chat_call_for_100_messages_and_a_2000_entry_map", "more than one redactor"),
    mutant("G20 the bind arguments are not checked (D5)",
        "        if not all(isinstance(value, str) for value in (agent_id, run_id, source)):\n", "        if False:\n",
        "test_d5_bind_refuses_ids_that_are_not_str_at_bind_not_later_in_a_lost_row", "DID NOT RAISE", param="[agent]"),
    mutant("G21 the audit row does not say whether the map was enforced (D1)",
        "                    decision=self._mode,\n", "                    decision=None,\n",
        "test_d1_every_audit_row_says_whether_the_map_was_enforced", "does not say whether the map was enforced"),
    # --- m-new-6: the source guard fails on each of these leaks ---
    mutant("G7f getattr(exc, 'args') in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "args", None)\n', I9, I9_SAYS),
    mutant("G7g getattr(exc, '__cause__') in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "__cause__", None)\n', I9, I9_SAYS),
    mutant("G7h sys.exception() in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "reason", None)\n            self._why = sys.exception()\n', I9, I9_SAYS),
    mutant("G7i sys.exc_info() in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "reason", None)\n            self._why = sys.exc_info()\n', I9, I9_SAYS),
    mutant("G7j sys.stderr.write in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "reason", None)\n            sys.stderr.write("failed")\n', I9, I9_SAYS),
    mutant("G7k .format on the exception in chat",
        '            reason = getattr(exc, "reason", None)\n', '            reason = getattr(exc, "reason", None)\n            self._why = "{}".format(exc)\n', I9, I9_SAYS),
    mutant("G7l open() in _enforced",
        "        mapping = self._mapping\n", '        mapping = self._mapping\n        open("/tmp/gate-leak", "w")\n', I9, I9_SAYS),
    mutant("G7m a module-level mutable container",
        'AUDIT_DOMAIN = "llm"\n', 'AUDIT_DOMAIN = "llm"\nSEEN = []\n', I9, I9_SAYS),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    for m in M:  # the search text of a mutant must be in the file exactly once (the runner replaces every copy)
        found = (ROOT / m.file).read_text(encoding="utf-8").count(m.old)
        if found != 1:
            print(
                f"mutant {m.name!r}: its search text is in {m.file} {found} times, not once",
                file=sys.stderr,
            )
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
        [TEST, MAP_TEST, WRITE_TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
