"""The mutants of the public-bind refusal and the shared loopback check (named B1 to B18), run by the mutation runner
(``tools/mutation_runner.py``), in the same way as ``tests/stage_mutants.py``. Each mutant reverts ONE guard in a temp
copy of the package; the test in ``killer`` must fail first, and its first failing line must hold ``expect`` (a fragment
of the assertion MESSAGE). Not collected by pytest. Run from the repo root:

    python tests/bind_mutants.py            # all mutants; exit 1 if any is not good
    python tests/bind_mutants.py B7         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
NG = "src/hadavin_sdk/netguard.py"
BG = "src/hadavin_sdk/bindguard.py"
RC = "src/hadavin_sdk/approvals/receiver.py"
TBL = "src/hadavin_sdk/backends/table.py"
HTTP = "src/hadavin_sdk/guard/http.py"
T_NG = "tests/test_netguard.py"
T_BG = "tests/test_bindguard.py"
T_SITES = "tests/test_loopback_sites.py"


def mutant(name, file, old, new, test_file, killer, expect, **kw):
    pin = test_file.removesuffix(".py") + "::" + killer
    return Mutant(
        name, file, old, new, expect, test_file=test_file, only_test=killer, pinned=pin, **kw
    )


M = [
    mutant(
        "B1 localhost is no longer loopback",
        NG,
        'if name.lower() == "localhost":',
        "if False:",
        T_NG,
        "test_loopback_spellings",
        "should be loopback",
    ),
    mutant(
        "B2 casefold reads the long-s letter as s",
        NG,
        'name.lower() == "localhost"',
        'name.casefold() == "localhost"',
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B3 brackets round an IPv4 address are accepted",
        NG,
        "    if bracketed and ip.version != 6:\n        return False  # brackets belong to IPv6 only\n",
        "",
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B4 a scope id is accepted",
        NG,
        ' or "%" in bare',
        "",
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B5 any mapped address counts as loopback",
        NG,
        "        ip = ip.ipv4_mapped\n",
        "        return True\n",
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B6 a non-text value is not refused (it crashes)",
        NG,
        "    if not isinstance(name, str):\n        return False\n",
        "",
        T_NG,
        "test_a_non_string_is_not_loopback",
        "AttributeError",
        allow_crash=True,
        crash_type="AttributeError",
    ),
    mutant(
        "B7 the exact literal list gains the next loopback address",
        NG,
        'frozenset({"127.0.0.1", "localhost", "::1"})',
        'frozenset({"127.0.0.1", "localhost", "::1", "127.0.0.2"})',
        T_NG,
        "test_the_literal_list_stays_exact",
        "the literal list changed",
    ),
    mutant(
        "B8 every table kind counts as real (the stand-in list is ignored)",
        BG,
        "if (cap, s.kind) not in stand_ins",
        "if True",
        T_BG,
        "test_the_fixture_config_holds_only_stand_ins",
        "== ()",
    ),
    mutant(
        "B9 the in-process kinds are counted as real",
        BG,
        "DEMO_ONLY | NOT_PROD | IN_PROCESS",
        "DEMO_ONLY | NOT_PROD",
        T_BG,
        "test_the_fixture_config_holds_only_stand_ins",
        "== ()",
    ),
    mutant(
        "B10 a system on this computer is real without the allow switch",
        BG,
        "            config.allow_insecure_loopback\n            and parts.scheme",
        "            parts.scheme",
        T_BG,
        "test_a_system_counts_unless_it_is_plain_http_on_this_computer_and_allowed",
        "System(base_url=",
    ),
    mutant(
        "B11 a configured source is not counted",
        BG,
        'found += [f"source {name}" for name in config.sources]\n',
        "",
        T_BG,
        "test_a_configured_source_is_a_real_service",
        "('source cluster',)",
    ),
    mutant(
        "B12 a public bind is allowed with a real service",
        BG,
        "if not real or is_loopback_host(bind):",
        "if True:",
        T_BG,
        "test_a_real_service_refuses_every_public_spelling",
        "accepted with",
    ),
    mutant(
        "B13 only the exact literal counts as the loopback bind",
        BG,
        "or is_loopback_host(bind)",
        "or is_loopback_literal(bind)",
        T_BG,
        "test_a_real_service_accepts_every_loopback_spelling",
        "refused",
    ),
    mutant(
        "B14 require_safe_bind does not raise",
        BG,
        "        raise BindRefused(problem)",
        "        return",
        T_BG,
        "test_a_real_service_refuses_every_public_spelling",
        "DID NOT RAISE",
    ),
    mutant(
        "B15 the receiver does not ask before it listens",
        RC,
        "        require_safe_bind(host, config)",
        "        pass",
        T_BG,
        "test_the_receiver_refuses_a_public_bind_with_a_real_service_before_it_listens",
        "a listening socket was opened",
    ),
    mutant(
        "B16 a kind that reaches a service is listed as in-process",
        TBL,
        '        ("audit", "chain"),\n    }\n)\n# Kinds refused only',
        '        ("audit", "chain"),\n        ("store", "postgres"),\n    }\n)\n# Kinds refused only',
        T_BG,
        "test_in_process_is_exactly_these_five_pairs_and_each_is_a_kind_of_the_table",
        "the in-process list changed",
    ),
    mutant(
        "B17 the HTTP guard keeps its own copy of the loopback list",
        HTTP,
        "LOOPBACK = LOOPBACK_LITERALS  # the one list lives in netguard",
        'LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})',
        T_BG,
        "test_no_module_keeps_its_own_loopback_list",
        "a copy of the loopback list",
    ),
    mutant(
        "B18 the HTTP guard list is widened",
        HTTP,
        "LOOPBACK = LOOPBACK_LITERALS  # the one list lives in netguard",
        "LOOPBACK = LOOPBACK_LITERALS | {'127.0.0.2'}",
        T_SITES,
        "test_the_http_guard_and_the_model_client_share_the_one_list",
        "assert frozenset",
    ),
]


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
        [T_BG, T_NG, T_SITES],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
