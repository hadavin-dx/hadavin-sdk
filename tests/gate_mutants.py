"""The mutants of the model gate (step F, ORDER 008), run by the P1m runner (``tools/mutation_runner.py``).

Same format as ``tests/stage_mutants.py``: each mutant reverts ONE guard of ``guard/model_gate.py`` in a temp copy of the
package; the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment of the assertion
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
PIN = "tests/test_model_gate::"
GATE = "src/hadavin_sdk/guard/model_gate.py"


def mutant(name, old, new, killer, expect):
    return Mutant(
        name, GATE, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


M = [
    mutant("G1 a refused reservation is swallowed and the client is called",
        "            self._note(RESULT_REFUSED, reason if known else CODE_RESERVE_REFUSED)\n            raise\n",
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
    mutant("G4a no settle on success",
        "            self._meter.settle(reservation, reply.cost_usd)\n", "            pass\n",
        "test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost", "settle on success"),
    mutant("G4b the worst case is settled on success, not the real cost",
        "            self._meter.settle(reservation, reply.cost_usd)\n",
        "            self._meter.settle(reservation, reserved)\n",
        "test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost", "settle on success"),
    mutant("G5 a KeyboardInterrupt is settled at the worst case",
        "        except Exception:  # may have been billed (a reply that fails to parse): hold the worst case\n",
        "        except BaseException:  # may have been billed\n",
        "test_pin_no_settle_on_keyboard_interrupt", "settled after a KeyboardInterrupt"),
    mutant("G6a a refused request is settled at the worst case, not 0",
        "            self._failed(reservation, Decimal(0), CODE_PROVIDER_ERROR)\n",
        "            self._failed(reservation, reserved, CODE_PROVIDER_ERROR)\n",
        "test_pin_the_settle_amount_after_a_client_error", "wrong settle after a client error"),
    mutant("G6b an exhausted provider is settled at 0, not the worst case",
        "            self._failed(reservation, reserved, CODE_PROVIDER_EXHAUSTED)\n",
        "            self._failed(reservation, Decimal(0), CODE_PROVIDER_EXHAUSTED)\n",
        "test_pin_the_settle_amount_after_a_client_error", "wrong settle after a client error"),
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
        [TEST],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
