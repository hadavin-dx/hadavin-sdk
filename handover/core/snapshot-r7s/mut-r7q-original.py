import subprocess, shutil, sys, os, filecmp
R = '/home/user/build/rr6/'; O = R + 'out/R7Q/'; M = O + 'mut/'; S = R + 'tree-R7Q/'
T7Q = 'tests/test_r7q_findings.py'; N1 = 'tests/test_r7n_findings.py'; T7P = 'tests/test_r7p_findings.py'
NK = 'n1_a_refused or middle or imaplib or secret_file or scrub_error'
SC = 'src/lead_desk/scrub.py'; IC = 'src/lead_desk/imap_count.py'; RR = 'scripts/run_real_check.py'
BR = 'demo_only/bad_request.py'; K7 = 'tests/test_r7k_findings.py'
RUN = RR
muts = [
    # reviewer mutants (r7n review), run against the r7p tests that rewrote _EchoImap, plus the r7n/r7q set
    ('X1', IC, '        raise ImapConnectionError("the mailbox could not be read") from None',
     '        raise ImapConnectionError("the mailbox could not be read" + str(e)) from None', [(T7Q, 'q9'), (N1, NK)]),
    ('X1a', IC, '            raise ImapCountError("the mailbox could not be read") from None  # not repeated',
     '            raise ImapCountError("the mailbox could not be read" + str(e)) from None  # not repeated', [(N1, None)]),
    ('X2', IC, '    except imaplib.IMAP4.error:\n        raise ImapCountError("the mailbox could not be read") from None',
     '    except imaplib.IMAP4.error as e:\n        raise ImapCountError("the mailbox could not be read" + str(e)) from None', [(T7P, None), (N1, NK)]),
    ('R05', SC, '    return type(e).__module__.split(".", maxsplit=1)[0] == PACKAGE', '    return True', [(T7P, None), (N1, NK)]),
    ('I01', IC, '@secret_boundary(ImapCountError, "the mailbox could not be read")  # the server', '@secret_boundary()  # the server', [(T7P, None), (N1, NK)]),
    # guard and helper mutants
    ('G01', N1, 'for top in ("src/lead_desk", "scripts", "load_tools", "tools")', 'for top in ("src/lead_desk", "load_tools", "tools")', [(T7Q, 'q7')]),
    ('G02', N1, 'for top in ("src/lead_desk", "scripts", "load_tools", "tools")', 'for top in ("src/lead_desk/scrub.py",)', [(T7Q, 'q7')]),
    ('G03', N1, '.rglob("*.py")', '.glob("*.py")', [(T7Q, 'q7')]),
    ('R08', SC, ' or not isinstance(e, Exception)', '', [(T7Q, 'q5 or q4')]),
    ('K01', K7, '    for name in ("_STOP", "_ANSWERED", "_ERRORS", "_STOP_LIMIT"):\n        monkeypatch.setattr(load_driver, name, getattr(load_driver, name))\n', '', [(T7Q, 'q6')]),
    # own mutants: scrub.py
    ('Q01', SC, ' or isinstance(e, MemoryError)', '', [(T7Q, 'q4 or q5')]),
    ('Q02', SC, ' or isinstance(e, MemoryError) or _ours(e)', ' or isinstance(e, MemoryError) or True', [(T7Q, 'q4 or q5'), (N1, NK)]),
    # run_real_check.py
    ('Q10', RR, '    return max(\n        len(request_body', '    return min(\n        len(request_body', [(T7Q, 'q1')]),
    ('Q11', RR, 'lead_id = LEAD_ID_PREFIX + "f" * LEAD_ID_HEX_CHARS', 'lead_id = LEAD_ID_PREFIX + "f"', [(T7Q, 'q1')]),
    ('Q12', RR, 'question_text(lead_id, normalise_email(str(it["envelope"]["payload"]["email"])))', 'question_text(lead_id, str(it["envelope"]["payload"]["email"]))', [(T7Q, 'q1')]),
    ('Q13', RR, 'q_bytes = longest_request_bytes(live, make_plan(tag, persons))', 'q_bytes = len(request_body(live, question_text("L000000000000", f"x@{EMAIL_DOMAIN}")))', [(T7Q, 'q1')]),
    ('Q14', RR, 'q_bytes = longest_request_bytes(live, make_plan(tag, persons))', 'q_bytes = longest_request_bytes(live, make_plan(new_tag(), persons))', [(T7Q, 'q2')]),
    ('Q15', RR, 'for items in plan.values()\n        for it in items', 'for items in [plan["after"]]\n        for it in items', [(T7Q, 'q1')]),
    ('Q16', RR, 'uuid.uuid4().hex[:TAG_HEX_CHARS]', 'uuid.uuid4().hex[: TAG_HEX_CHARS + 1]', [(T7Q, 'q2')]),
    ('Q17', RR, 'MODEL_CALLS_PER_LEAD = MODEL_CALLS_PER_LEAD_MAX', 'MODEL_CALLS_PER_LEAD = 2', [(T7Q, 'q3')]),
    ('Q18', RR, '* MODEL_CALLS_PER_LEAD * (persons + 3) * 2', '* MODEL_CALLS_PER_LEAD * (persons + 3)', [(T7Q, 'q1 or q3'), ('tests/test_r7o_findings.py', 'cost_line')]),
    ('Q19', RR, '    tag = new_tag()  # once', '    tag = "rfixed1"  # once', [(T7Q, 'q2')]),
    # demo_only/bad_request.py
    ('Q20', BR, '        if isinstance(sys.exception(), CLIENT_GONE):\n            return\n', '        return\n', [(T7Q, 'q8')]),
    ('Q21', BR, 'if isinstance(sys.exception(), CLIENT_GONE):', 'if False:', [(T7Q, 'q8')]),
    ('Q22', BR, 'CLIENT_GONE = (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, TimeoutError)', 'CLIENT_GONE = (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)', [(T7Q, 'q8')]),
    ('Q23', BR, 'CLIENT_GONE = (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, TimeoutError)', 'CLIENT_GONE = (OSError,)', [(T7Q, 'q8')]),
    ('Q24', BR, '    daemon_threads = True\n\n    def handle_error', '    daemon_threads = False\n\n    def handle_error', [(T7Q, 'q8')]),
    ('Q25', BR, '        super().handle_error(request, client_address)', '        return', [(T7Q, 'q8')]),
]
only = sys.argv[1:]
out = open(O + 'mut-results.tsv', 'a')
for mid, f, old, new, runs in muts:
    if only and mid not in only:
        continue
    p = M + f
    s = open(p, encoding='utf-8').read()
    if s.count(old) != 1:
        out.write(f'{mid}\tNOT-APPLIED count={s.count(old)}\n'); out.flush(); continue
    open(p, 'w', encoding='utf-8').write(s.replace(old, new))
    try:
        for tfile, k in runs:
            env = dict(os.environ, PYTHONPATH=M + 'src', PYTHONDONTWRITEBYTECODE='1', TMPDIR=O + 'tmp2')
            cmd = ['unshare', '-n', 'python', R + 'src-v6/drivers/lo_up-q4g.py', R + 'venv-br/bin/python', '-m', 'pytest', '-q',
                   '-p', 'no:cacheprovider', '-x'] + (['-k', k] if k else []) + [tfile]
            r = subprocess.run(cmd, cwd=M, env=env, capture_output=True, text=True, timeout=900)
            tail = r.stdout.strip().splitlines()[-1:]
            res = 'KILLED' if r.returncode == 1 else ('SURVIVED' if r.returncode == 0 else 'ERR rc=%d' % r.returncode)
            open(O + f'mutraw-{mid}-{os.path.basename(tfile)}.txt', 'w').write(r.stdout[-3000:])
            out.write(f'{mid}\t{tfile}\t{res}\t{tail}\n'); out.flush()
            if res == 'KILLED':
                break
    finally:
        shutil.copyfile(S + f, p)
        same = filecmp.cmp(S + f, p, shallow=False)
        out.write(f'{mid}\trestored-byte-equal={same}\n'); out.flush()
