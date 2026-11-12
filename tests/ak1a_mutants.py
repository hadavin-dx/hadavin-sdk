"""The mutants of the pipeline step contract (AK1-a): M-A1 to M-A19, M-A21 and M-A22 of the AK1 ticket, and M-A23 on, which
are extra mutants for code items the ticket's list does not name (each has its own killer). M-A20 belongs to AK1-b.

Run by the P1m runner (``tools/mutation_runner.py``), like ``tests/stage_mutants.py``. Each mutant reverts or breaks ONE guard
in a temp copy of the package; the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a
fragment of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/ak1a_mutants.py            # all mutants; exit 1 if any is not good
    python tests/ak1a_mutants.py M-A7       # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_pipeline_step_contract.py"
STEP = "src/hadavin_sdk/pipeline/step.py"

_SRC = (ROOT / STEP).read_text("utf-8")


def mutant(name, old, new, killer, expect, **more):
    assert _SRC.count(old) == 1, f"{name}: the text to change must occur exactly once"
    return Mutant(name, STEP, old, new, expect, test_file=TEST, only_test=killer, **more)


def _reordered_intent():
    """M-A9: the same code, with the intent block moved to after the step has run."""
    i = _SRC.index("    try:\n        audit.write_intent(")
    j = _SRC.index("    def write_outcome(")
    k = _SRC.index("    try:\n        out = step.run(inp)")
    end = _SRC.index("    if not _acceptable(inp, out):")
    return _SRC[i:end], _SRC[j:k] + _SRC[k:end] + _SRC[i:j]


_A9_OLD, _A9_NEW = _reordered_intent()

DONE_OUT = "StepOutput(inp.item_id, inp.tenant, inp.readers, Outcome.DONE, None, None, inp.run_id, inp.agent_id)"
LEAD = "    except Exception as exc:  # noqa: BLE001 - a step may raise anything; each class maps to one closed reason"
INTENT = "    except Exception as exc:  # noqa: BLE001 - any failure to write the intent stops the step (fail closed)"
S5 = "test_s5_an_output_that_changes_identity_or_widens_is_a_step_error_with_no_body"
S5B = "test_s5_a_record_built_around_the_constructor_is_refused_by_the_runner"
S4 = "test_s4_a_reason_outside_its_outcome_is_refused"
S10 = "test_s10_audit_order_on_the_recording_sink"
S10F = "test_s10_a_failed_intent_means_the_step_is_never_called"
S7 = "test_s7_stop_requests_propagate_unchanged_after_a_best_effort_outcome"
S9 = "test_s9_no_text_in_repr_str_format_or_log"
S2 = "test_s2_readers_refuse_the_bad_and_accept_the_limits"
S1 = "test_s1_tenant_pattern_accepts_and_refuses"
S6 = "test_s6_ordinary_exceptions_end_in_step_error_and_leave_no_text"
ARGS = "test_the_input_refuses_a_wrong_type_everywhere"

M = [
    mutant("M-A1 readers subset check removed", "            and out.readers <= inp.readers\n", "", S5, "reader not in input"),
    mutant("M-A2 an exception from step.run gives done", "        out = _failed(inp, _reason_for(exc))", f"        out = {DONE_OUT}", S6, "assert"),
    mutant("M-A3 done accepts a reason", "        if reason is not None:\n", "        if False:\n", S4, "DID NOT RAISE"),
    mutant("M-A4 tenant check uses re.search", "_TENANT.fullmatch(value)", "_TENANT.search(value)", S1, "DID NOT RAISE"),
    mutant("M-A5 tenant_key uses the plain / join", '        key += f"/{len(part)}:{part}"', '        key += "/" + part', "test_s8_the_two_ambiguous_tuples_differ", "tenant-a/x/y"),
    mutant("M-A6 __repr__ includes the body", 'f"content_sha256={self.content_sha256!r})"', 'f"content_sha256={self.content_sha256!r}, body={self.body!r})"', S9, "canary-"),
    mutant("M-A7 KeyboardInterrupt turned into an output", LEAD, LEAD.replace("(Exception)", "").replace("except Exception as exc:", "except (Exception, KeyboardInterrupt) as exc:"), S7, "DID NOT RAISE"),
    mutant("M-A8 outcome event skipped on needs_person", "    write_outcome(out.outcome, out.reason, len(out.readers))\n    return out", "    if out.outcome is not Outcome.NEEDS_PERSON:\n        write_outcome(out.outcome, out.reason, len(out.readers))\n    return out", S10, "assert"),
    Mutant("M-A9 intent event written after step.run", STEP, _A9_OLD, _A9_NEW, "the intent event must exist before the step runs", test_file=TEST, only_test=S10),
    mutant("M-A10 REASONS check removed", "    if type(reason) is not str or reason not in REASONS[outcome]:\n", "    if False:\n", S4, "DID NOT RAISE"),
    mutant("M-A11 empty readers accepted", "    if not 1 <= len(value) <= defaults.PIPELINE_MAX_READERS:", "    if not 0 <= len(value) <= defaults.PIPELINE_MAX_READERS:", S2, "DID NOT RAISE"),
    mutant("M-A12 output tenant not compared", "            and out.tenant == inp.tenant\n", "", S5, "other tenant"),
    mutant("M-A13 item_id checked with re.search", "_ITEM_ID.fullmatch(value)", "_ITEM_ID.search(value)", "test_s12_item_ids", "DID NOT RAISE"),
    mutant("M-A14 run_id and agent_id equality removed", "            and out.run_id == inp.run_id\n            and out.agent_id == inp.agent_id\n", "", S5, "other run id"),
    mutant("M-A15 the step runs after a failed intent write", '        log.warning("step %s: intent not written (%s)", name, type(exc).__name__)\n        return _failed(inp, "audit_unavailable")', '        log.warning("step %s: intent not written (%s)", name, type(exc).__name__)', S10F, "1 == 0"),
    mutant("M-A16 REASON_BY_ERROR takes the last match", "    for cls in type(exc).__mro__:", "    for cls in reversed(type(exc).__mro__):", "test_s13_the_first_class_of_the_mro_found_in_the_table_wins", "policy"),
    mutant("M-A17 AuditUnavailable on the intent propagates", INTENT, INTENT.replace("except Exception as exc:", "except ZeroDivisionError as exc:"), S10F, "down", allow_crash=True, crash_type="AuditUnavailable"),
    mutant("M-A18 unreadable missing from the needs_person reasons", '                "unreadable",\n', "", "test_s4_the_reason_sets_are_exactly_the_ticket_sets", "frozenset("),
    mutant("M-A19 GeneratorExit turned into an output", LEAD, LEAD.replace("except Exception as exc:", "except (Exception, GeneratorExit) as exc:"), S7, "DID NOT RAISE"),
    mutant("M-A21 content_sha256 uses models.sha256_hex", '        return hashlib.sha256(\n            self.body if type(self.body) is bytes else self.body.encode("utf-8")\n        ).hexdigest()', "        from hadavin_sdk.models import sha256_hex\n\n        return sha256_hex(self.body)", "test_s14_content_hash_and_strict_utf8", "TypeError", allow_crash=True, crash_type="TypeError"),
    mutant("M-A22 the constructor's UTF-8 check removed", '    try:\n        body.encode("utf-8")\n    except UnicodeEncodeError:\n        raise ValueError("body: not valid UTF-8") from None\n', "    return\n", "test_s14_content_hash_and_strict_utf8", "DID NOT RAISE"),
    # --- extra mutants (code items the ticket's list does not name) ---
    mutant("M-A23 output item_id not compared", "            out.item_id == inp.item_id\n            and ", "            True\n            and ", S5, "other item"),
    mutant("M-A24 output record not checked again by the runner", "        StepOutput.__post_init__(out)\n", "", S5B, "assert"),
    mutant("M-A25 a StepOutput subclass is accepted", "        if type(out) is not StepOutput:\n            return False\n", "", S5B, "assert"),
    mutant("M-A26 no outcome event on a stop request", '        write_outcome(Outcome.NEEDS_PERSON, "step_error", len(inp.readers))\n', "", S7, "assert"),
    mutant("M-A27 tenant_key does not check the tenant", "    check_tenant(tenant)\n    key = ", "    key = ", "test_s1_the_constructor_and_tenant_key_refuse_a_bad_tenant_without_echoing_it", "DID NOT RAISE"),
    mutant("M-A28 tenant_key part length not checked", "type(part) is not str or not 1 <= len(part) <= defaults.PIPELINE_KEY_PART_MAX_CHARS", "type(part) is not str", "test_s8_a_bad_part_is_refused_without_echoing_it", "DID NOT RAISE"),
    mutant("M-A29 readers may be a plain set", '    if type(value) is not frozenset:\n        raise ValueError("readers: must be a frozenset of names")\n', "", S2, "DID NOT RAISE"),
    mutant("M-A30 a reader name is not checked", '        if type(reader) is not str or _READER.fullmatch(reader) is None:\n            raise ValueError("readers: a name is outside the allowed shape")\n', "        pass\n", S2, "DID NOT RAISE"),
    mutant("M-A31 a body of another type is accepted", '    if type(body) is not str:\n        raise TypeError("body: must be str or bytes")\n', "", ARGS, "AttributeError", allow_crash=True, crash_type="AttributeError"),
    mutant("M-A32 labels may hold unprintable characters", "        or not value.isprintable()\n", "", ARGS, "DID NOT RAISE"),
    mutant("M-A33 the principal is not checked", '    _check_label("principal", principal)\n', "", "test_run_step_refuses_bad_arguments_before_any_event", "DID NOT RAISE"),
    mutant("M-A34 the step name is not checked", '    if type(name) is not str or _STEP_NAME.fullmatch(name) is None:\n        raise ValueError("step.name: not a step name")\n', "", "test_run_step_refuses_bad_arguments_before_any_event", "DID NOT RAISE"),
    mutant("M-A35 a body is allowed on a needs_person output", "            if self.outcome is not Outcome.DONE:\n", "            if False:\n", "test_s4_the_outcome_must_be_an_outcome_and_only_done_carries_a_body", "DID NOT RAISE"),
    mutant("M-A36 the outcome need not be an Outcome", "        if type(self.outcome) is not Outcome:\n", "        if False:\n", "test_s4_the_outcome_must_be_an_outcome_and_only_done_carries_a_body", "no attribute 'value'", allow_crash=True, crash_type="AttributeError"),
    mutant("M-A37 the intent event holds no input hash", "                inputs_hash=inp.content_sha256,\n", "", S10, "None == '2cf24dba"),
    mutant("M-A38 the outcome event always says done", "                    decision=outcome.value,\n", '                    decision="done",\n', S10, "('done', 'low_quality')"),
    mutant("M-A39 the output repr shows the body", "has_body={self.body is not None})\"", "body={self.body!r})\"", S9, "canary-"),
    mutant("M-A40 the input repr shows the reader names", "readers={len(self.readers)}, \"\n            f\"content_sha256", "readers={sorted(self.readers)}, \"\n            f\"content_sha256", S9, "canary-"),
    mutant("M-A41 the log carries the exception text", '        log.warning("step %s raised %s", name, type(exc).__name__)', '        log.warning("step %s raised %s", name, exc)', S6, "canary-"),
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
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
