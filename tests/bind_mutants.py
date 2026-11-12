"""The mutants of the public-bind refusal and the shared loopback check (named B1 to B39), run by the mutation runner
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


def _between(path, start, end):
    """The exact text of ``path`` from ``start`` up to and including ``end`` (read at import, so the mutant follows
    the file)."""
    text = (ROOT / path).read_text(encoding="utf-8")
    i = text.index(start)
    j = text.index(end, i) + len(end)
    return text[i:j]


_ASK = "    require_safe_bind(host, config, allow_public_bind_reason=allow_public_bind_reason)\n"
_LISTEN_ASK_FIRST = _between(BG, _ASK, "    server = _Server((address, port), handler)\n")
_LISTEN_BUILD_FIRST = _LISTEN_ASK_FIRST.replace(_ASK, "") + _ASK


def mutant(name, file, old, new, test_file, killer, expect, **kw):
    pin = test_file.removesuffix(".py") + "::" + killer
    return Mutant(
        name, file, old, new, expect, test_file=test_file, only_test=killer, pinned=pin, **kw
    )


M = [
    mutant(
        "B1 localhost is no longer loopback",
        NG,
        "if is_localhost_name(name):",
        "if False:",
        T_NG,
        "test_loopback_spellings",
        "should be loopback",
    ),
    mutant(
        "B2 casefold reads the long-s letter as s",
        NG,
        'text.lower() == "localhost"',
        'text.casefold() == "localhost"',
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B3 brackets round an IPv4 address are accepted",
        NG,
        "    if bracketed and ip.version != 6:\n        return None  # brackets belong to IPv6 only\n",
        "",
        T_NG,
        "test_everything_else_is_not_loopback",
        "should not be loopback",
    ),
    mutant(
        "B4 a scope id is accepted",
        NG,
        '    if "%" in bare:\n        return None\n',
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
        "not isinstance(text, str) or _has_leading_zero_octet(text)",
        "_has_leading_zero_octet(text)",
        T_NG,
        "test_a_non_string_is_not_loopback",
        "AttributeError",
        allow_crash=True,
        crash_type="AttributeError",
    ),
    mutant(
        "B7 the exact literal list gains the next loopback address",
        NG,
        'frozenset({LOOPBACK_V4, "localhost", "::1"})',
        'frozenset({LOOPBACK_V4, "localhost", "::1", "127.0.0.2"})',
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
        "B15 listen does not ask when the host is text",
        BG,
        "    require_safe_bind(host, config, allow_public_bind_reason=allow_public_bind_reason)\n",
        "    if not isinstance(host, str):\n        require_safe_bind(host, config)\n",
        T_BG,
        "test_listen_refuses_before_any_server_exists",
        "a server was built before the refusal",
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
    mutant(
        "B19 listen builds the server before it asks",
        BG,
        _LISTEN_ASK_FIRST,
        _LISTEN_BUILD_FIRST,
        T_BG,
        "test_listen_refuses_before_any_server_exists",
        "a server was built before the refusal",
    ),
    mutant(
        "B20 the receiver passes its own default of every address",
        RC,
        "    host: str = LOOPBACK_V4,",
        '    host: str = "0.0.0.0",',
        T_BG,
        "test_the_receiver_default_host_is_this_computer",
        "assert",
    ),
    mutant(
        "B21 the receiver does not check that the config is the approvals' own",
        RC,
        "    if approvals.config is not config:",
        "    if False:",
        T_BG,
        "test_the_receiver_refuses_a_config_that_is_not_the_one_the_approvals_were_built_with",
        "a server was built before the refusal",
    ),
    mutant(
        "B22 a reason is ignored (a public bind is refused even with it)",
        BG,
        "    if allow_public_bind_reason is None:\n        raise BindRefused(problem)\n",
        "    raise BindRefused(problem)\n",
        T_BG,
        "test_a_public_bind_needs_the_named_reason_and_the_reason_is_logged",
        "BindRefused",
        allow_crash=True,
        crash_type="BindRefused",
    ),
    mutant(
        "B23 an empty reason is accepted",
        BG,
        "    if not text:\n",
        "    if False:\n",
        T_BG,
        "test_an_empty_reason_is_refused_with_a_sentence_that_asks_for_one",
        "DID NOT RAISE",
    ),
    mutant(
        "B24 the reason is not written to the log",
        BG,
        "    _LOG.warning(",
        "    _LOG.debug(",
        T_BG,
        "test_a_public_bind_needs_the_named_reason_and_the_reason_is_logged",
        "0 == 1",
    ),
    mutant(
        "B25 tool modules are not counted",
        BG,
        '    found += [f"tools:{module}" for module in config.tool_modules]\n',
        "",
        T_BG,
        "test_each_of_tool_modules_check_modules_and_a_live_egress_host_alone_makes_a_public_bind_refused",
        "tool_modules",
    ),
    mutant(
        "B26 check modules are not counted",
        BG,
        '    found += [f"checks:{module}" for module in config.check_modules]\n',
        "",
        T_BG,
        "test_each_of_tool_modules_check_modules_and_a_live_egress_host_alone_makes_a_public_bind_refused",
        "check_modules",
    ),
    mutant(
        "B27 a live egress host is not counted",
        BG,
        "        for host in sorted(config.egress_hosts)\n        if not is_loopback_host(host)\n",
        "        for host in ()\n",
        T_BG,
        "test_each_of_tool_modules_check_modules_and_a_live_egress_host_alone_makes_a_public_bind_refused",
        "egress_hosts",
    ),
    mutant(
        "B28 a loopback egress host is counted as live",
        BG,
        "        for host in sorted(config.egress_hosts)\n        if not is_loopback_host(host)\n",
        "        for host in sorted(config.egress_hosts)\n",
        T_BG,
        "test_loopback_egress_hosts_and_empty_lists_pass",
        "== ()",
    ),
    mutant(
        "B29 a long bind text is not cut",
        BG,
        '    return bind if len(bind) <= limit else bind[:limit] + "..."',
        "    return bind",
        T_BG,
        "test_a_long_bind_text_is_cut_in_the_refusal",
        "the long bind text was not cut",
    ),
    mutant(
        "B30 a non-text bind crashes the readable-text step",
        BG,
        "    if not (isinstance(bind, str) and bind.isprintable()):",
        "    if not bind.isprintable():",
        T_BG,
        "test_a_real_service_refuses_every_public_spelling",
        "AttributeError",
        allow_crash=True,
        crash_type="AttributeError",
    ),
    mutant(
        "B31 a control character in a bind text is shown as it is",
        BG,
        "    if not (isinstance(bind, str) and bind.isprintable()):",
        "    if not isinstance(bind, str):",
        T_BG,
        "test_the_refusal_is_one_plain_sentence_with_no_value_of_the_bind_leaking_control_text",
        "evil",
    ),
    mutant(
        "B32 localhost is bound by name, not as the literal",
        BG,
        "        return LOOPBACK_V4, socket.AF_INET\n",
        '        return "localhost", socket.AF_INET\n',
        T_BG,
        "test_listen_picks_the_ipv6_family_for_an_ipv6_address_even_without_ipv6_on_this_machine",
        "wrong family or address",
    ),
    mutant(
        "B33 an IPv6 address gets an IPv4 socket",
        BG,
        "        return str(ip), socket.AF_INET6 if ip.version == 6 else socket.AF_INET\n",
        "        return str(ip), socket.AF_INET\n",
        T_BG,
        "test_listen_picks_the_ipv6_family_for_an_ipv6_address_even_without_ipv6_on_this_machine",
        "wrong family or address",
    ),
    mutant(
        "B34 a name that is not localhost is bound",
        BG,
        '    raise BindRefused(\n        f"bind {_shown(host)!r} is not an IP address',
        '    return host, socket.AF_INET\n    raise BindRefused(\n        f"bind {_shown(host)!r} is not an IP address',
        T_BG,
        "test_listen_refuses_a_name_that_is_not_localhost_even_with_stand_ins",
        "a server was built before the refusal",
    ),
    mutant(
        "B35 the address the socket got is not checked",
        BG,
        "        and not is_loopback_host(server.server_address[0])\n",
        "        and False\n",
        T_BG,
        "test_listen_checks_the_address_the_socket_really_got",
        "DID NOT RAISE",
    ),
    mutant(
        "B36 the server asks the resolver for the name of the bound address",
        BG,
        "            socketserver.TCPServer.server_bind(self)\n            host, port = self.server_address[:2]\n            self.server_name, self.server_port = str(host), port\n",
        "            ThreadingHTTPServer.server_bind(self)\n",
        T_BG,
        "test_listen_binds_the_literal_for_localhost_and_never_looks_a_name_up",
        "a name was looked up",
    ),
    mutant(
        "B37 a leading zero is left to the Python version",
        NG,
        "not isinstance(text, str) or _has_leading_zero_octet(text)",
        "not isinstance(text, str)",
        T_NG,
        "test_a_leading_zero_is_refused_by_our_own_check_not_by_the_python_version",
        "should not be loopback",
    ),
    mutant(
        "B38 the hash-chain audit kind is not pinned (moved to real)",
        TBL,
        '        ("audit", "chain"),\n    }\n)\n# Kinds refused only',
        "    }\n)\n# Kinds refused only",
        T_BG,
        "test_the_pinned_table_is_exactly_the_kinds_of_the_table_and_the_three_lists",
        "pinned class",
    ),
    mutant(
        "B39 the receiver builds its own server instead of calling listen",
        RC,
        "    return listen(config, host, port, Handler, allow_public_bind_reason=allow_public_bind_reason)",
        "    import http.server\n\n    return http.server.ThreadingHTTPServer((host, port), Handler)",
        T_BG,
        "test_only_listen_creates_a_server_socket",
        "another server socket outside listen",
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
