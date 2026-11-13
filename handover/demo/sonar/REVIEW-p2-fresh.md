# rv9 - fresh review of sonar-p2-regex-http-bug.patch (base db54e13)

Reviewer: fresh, independent, shell. No pushes, no network writes, made-up data only. Scratch: /tmp/work/rv9-1 (clone, venv, scripts).
Bible not readable here (studio folder absent): R-numbers cited from the preamble text only (rules 5, 6, 7, 8, 12, 19, 20). EGM: I am the reviewer, not a builder.

## 1. What failed or is not as claimed (read first)

MAJOR 1 - two of the four S8786 (regex) issues will most likely NOT clear: scripts/run_real_check.py:116 and tools/scrub_n8n_export.py:102.
 Evidence (read from public source, not measured; see section 7 for why I could not run it):
 - The rule is SuperLinearRegexCheck (python-checks) on RedosFinder (sonar-analyzer-commons). It reports only BacktrackingType.ALWAYS_QUADRATIC.
 - run_real_check._ADDRESS (new): `(?<!..)[^\s,;:<>"']+@[^\s,;<>"']+`. Both repetitions are open-ended and NOT possessive, and BOTH classes contain "@"
   (the author kept the overlap, NOTES item 5). RedosVisitor.checkForOverlappingRepetitions adds ALWAYS_QUADRATIC when the first repetition's class
   intersects what follows and the second repetition's class (rep1 ∩ rep2 is non-empty, "@" is in both). The look-behind does not matter to this test.
   It is also used with `.sub` (partial match), so overlapsWithImplicitMatchAlls applies as well (see next point).
 - scrub MAIL (new): leading `(?<![\w.%+-])[\w.%+-]++`. overlapsWithImplicitMatchAlls(tree) = isUsedForPartialMatch && canReachWithoutConsumingInputNorCrossingBoundaries(start, tree).
   Only BoundaryTree (^ $ \b \A ...) stops that walk; LookAroundTree.successors() = [inner, continuation] so the repetition after a look-behind is reachable. The
   function has NO isPossessive test (addIfNonPossessive only decides what is remembered for later pairs). The OLD pattern had the same look-behind and was flagged at
   baseline (issues-pr4-0253.json line 102), so the look-behind plainly does not help, and the possessive change does not touch this code path. MAIL.sub is the only use -> PARTIAL.
 - Fix I verified for equivalence and speed (not for Sonar): put ONE mandatory character before the repetition so the repetition is not reachable without consuming input, and take "@" out of the run_real_check local class after that first char:
     _ADDRESS = (?<![^\s,;:<>"'])[^\s,;:<>"'][^\s,;:<>"'@]*@[^\s,;<>"']+
     MAIL     = (?<![\w.%+-])[\w.%+-][\w.%+-]*+[@＠](?!(?:(?!ALLOWED)[\w-]++\.)*+ALLOWED)[\w.-]++    (ALLOWED = the author's _ALLOWED_END)
   Result with my own script (/tmp/work/rv9-1/s/alt.py): all strings up to length 7 over an 8-symbol alphabet + 600 000 random token strings: 0 differences in .sub output (and match spans for MAIL) against the OLD patterns; 64 000 chars: 3 ms, 128 000 chars: 7 ms.
 - Same logic says identity PLAIN (new) and _EMAIL_RE (new) clear (section 5).

MAJOR 2 (consequence): the NOTES claim "11 of 11 in my scope" is not supported; my honest estimate is 7 likely, 2 likely not, 2 unknown (table in section 5). The patch's own caveats 4, 5, 7 were right to worry.

No test failures, no regression found in any of the behaviour areas below.

## 2. Apply and tooling (measured)
- Fresh clone at db54e13 (`git log` = "sonar.yml: valid YAML ..."). `git apply --check` + apply of P2: OK. All three patches in orders p1 p3 p2, p2 p1 p3, p3 p2 p1: all apply cleanly (git apply, no rejects).
- P2 only: `ruff check` clean, `ruff format --check` 148 files clean, `mypy` (linux) and `mypy --platform win32` clean (27 files), bandit -ll: 0 medium, 0 high (9 low).
- All three applied (order p3 p2 p1): ruff, format (150 files), mypy linux and win32 clean (28 files).
- Tests, P2 only (venv from requirements-dev.txt; the repo has no uv "test" group, same deviation as the author): tests/test_sonar_p2_choke_points, test_bind_refusals, test_ledger_and_bind_retry, test_server_stop_guard, test_mirror_gate, test_hygiene, test_real_check_dry, test_scrub_n8n_export, test_env_numbers, test_smtp_outbox, test_reminder_email, test_followup_edge_cases, test_portal_api, test_mutation_guards, test_http_guard, test_codeant_hygiene, test_lead_step_route: 1181 passed, 3 skipped, 189 s. (Honest slip: an earlier attempt failed only because my own `pip install -e` left an egg-info under src/ that test_hygiene rejects; I removed it. I also ran a `git stash` for a few seconds in that clone while that run was in progress, after collection; the run still passed; the bind/real-bind comparison below was done separately.)
- Tests with all three patches: test_sonar_p2_choke_points, test_path_confinement, test_hygiene, test_workflow_files_parse, test_lead_step_route, test_followup_edge_cases, test_portal_api: 347 passed, 3 skipped, 124 s. Full suite NOT run (as instructed).

## 3. Regex equivalence and ReDoS timing (my own corpus)
Old patterns were read from `git show db54e13:` (not copied from the author). Script: /tmp/work/rv9-1/s/fz.py, fz2.py.
- Corpus: exhaustive up to length 6 over a 10-symbol alphabet incl. quote, tab, parenthesis, full-width at-sign, percent, hyphen; exhaustive up to length 4 over 15 tokens (x, @, ., example, .com, .test, hyphen, é, +, no-break space, comma, colon, <, >, space); 400 000 random strings of up to 12 tokens from ~40 tokens (unicode 日本語, ß, quoted local, plus-tags, angle brackets, trailing dots, CR/LF/NUL, EXAMPLE.COM); 30 realistic addresses (unicode, plus-tag, quoted form, trailing dots, `<a@b.c>`, 300+300 char parts, 1000 labels, "Name <x@y.z>, other@x.org;third@y.z", mailto: with query). 1 565 382 cases x 4 patterns: 0 differences (run_real_check .sub, PLAIN fullmatch, EMAIL fullmatch, MAIL .sub).
- Extra 1 500 000 random structured domain strings for MAIL (example/.com/.test/invalid/-/_/＠/é...), compared on .sub AND on every match span: 0 differences.
- Hand proofs (agree with fuzz): PLAIN old = "an @ at index 1..n-2 of a string of class chars"; new = first char, non-@ run, first @, 1+ chars: same language. EMAIL old = "domain has a dot with a char before and after"; new = first char, non-dot run, first dot, 1+ chars: same language.
- ReDoS timing (ms, one run each; old not run at 64 000):
  | pattern, input | old 1k / 4k / 16k | new 1k / 4k / 16k / 64k |
  | run_real_check "a"*n | 4.0 / 70 / 1199 | 0.03 / 0.12 / 0.47 / 1.9 |
  | run_real_check "a."*n/2 | 4.3 / 68 / 1210 | 0.03 / 0.13 / 0.46 / 2.2 |
  | PLAIN "a@"*n/2+"\n" | 3.7 / 53 / 899 | 0.02 / 0.06 / 0.20 / 0.78 |
  | EMAIL "a@"+"b."*n/2+"@" | 3.2 / 51 / 882 | 0.01 / 0.06 / 0.20 / 0.86 |
  | EMAIL "x@a."+" " (pattern a@b.) | 6.6 / 108 / 1702 | 0.01 / 0.06 / 0.19 / 0.83 |
  | MAIL (6 shapes: a*, a@a.a.., a@example.example.., a@(example.com.)*-, a.a.@a.a., a%a%..) | 0.0-0.1 / 0.1-0.3 / 0.3-1.0 | 0.02-0.04 / 0.06-0.13 / 0.27-0.57 / 1.1-2.2 |
  Confirms the author: the old MAIL is NOT slow on any input I tried; the new one is not slower. So the MAIL rewrite is a static-analysis change with no measured runtime benefit.

## 4. New choke points
### feed.checked_url (scripts/feed.py) - /tmp/work/rv9-1/s/feed_t.py, 60 inputs
Measured results:
- Refused: `http://127.0.0.1@evil.test:8765/leads`, `http://127.0.0.1:8765@evil.test/leads`, `http://127.0.0.1:pw@evil.test:80/leads`, `http://user:pw@127.0.0.1:8765/leads`, `http://evil.test@127.0.0.1:8765/leads`, `http://127.0.0.1\@evil.test...`, ftp/file/scheme-less/`//host`/`http:127.0.0.1...`, query, fragment, `;params`, `/other`, `/../leads`, `//leads`, `/%6Ceads`, `/leads/`, trailing-dot hosts (`localhost.`, `127.0.0.1.`), long IPv6 forms (`[0:0:0:0:0:0:0:1]`, `[::ffff:127.0.0.1]`, `[::1%25lo]`), `127.1`, `2130706433`, `0x7f.0.0.1`, `127.0.0.2`, `0.0.0.0`, unicode look-alike host, port 65536, -1, +80, full-width digits, empty port, no port, empty string, `http://`, `http://:8765/leads`, CRLF-injected text.
- Accepted and rebuilt as scheme://trusted-host:port/leads: `http://127.0.0.1:8765` (no path), `LOCALHOST` (rebuilt lower case), `[::1]:8765`, `https://...`, `HTTP://...`, own-host name in any case (desk.example, DESK.example).
- Nit: accepted although odd: `http://:@127.0.0.1:8765/leads` (empty user and password), `http://127.0.0.1\t:8765/leads` (urlsplit drops the tab), trailing newline, port 0. All are harmless because the request address is rebuilt from the trusted host, int port and fixed path; they are not a bypass.
- Nit: a refused address ends in a Python traceback (ValueError, exit 1), not a one-line message. The old code also gave a traceback for a bad host (URLError), so it is not worse, but rule 14 (wording) would prefer a clean exit 2.
Documented usage: README Linux/Windows blocks, docs/settings.md, docs/limits.md (burst uses demo_only.burst, not feed.py) - none documents `--url` for feed.py (grep). Real end-to-end run of the README flow on ports 28765/28766 with scripts/start_all.sh keyed: `feed.py --source form --index 1` -> 201 new; again -> 201 replayed true; `--source webhook --index 1 --url http://localhost:28765/leads` -> 200 duplicate; `--url http://127.0.0.1:28765` (no path) -> 201; /counts received 3, new 2, duplicate 1; `--url http://127.0.0.1@evil.test:28765/leads` -> refused. Log line "desk listening on http://127.0.0.1:28765" unchanged. reset.sh stopped both processes (no pkill).
Behaviour changes for undocumented `--url` use: a URL without a port, with a trailing slash or `/leads/`, a non-own non-loopback host (a remote desk), `127.0.0.2`, long-form IPv6, or trailing-dot host now fails; before, anything urllib could open was sent. No documented command uses these. Worth one line in docs/settings.md (feed.py section) saying `--url` is restricted; the patch adds none.

### urls.desk_origin / DESK_SCHEME
`desk_origin(h, p)` = f"{scheme}://{h}:{p}": identical text to the old f-strings in config.fakes_url, server Origin check, serve_in_thread, "desk listening" line (tests pass; README flow shows same text). The docstring names Config.public_bind_problem (config.py:465) and Config.problem (config.py:517 refuses non-loopback fakes_host): both exist and say what the docstring says.

### _ExclusiveBind (server.py)
- MRO now: _Server, _ExclusiveBind, ThreadingHTTPServer, ThreadingMixIn, HTTPServer, TCPServer, BaseServer, object. So `super().server_bind()` inside _ExclusiveBind goes to HTTPServer.server_bind (which sets server_name/server_port) - confirmed: server_name "localhost", server_port set, on both old and new code.
- Real bind on Linux (/tmp/work/rv9-1/s/bind.py, old and new code give identical output): second listener on a port that is listening -> EADDRINUSE; rebind right after close -> OK (allow_reuse_address True); rebind while the old connection is in TIME_WAIT -> OK. Shutdown/reuse semantics unchanged.
- Faked win32 path: the new test records the setsockopt(SOL_SOCKET, SO_EXCLUSIVEADDRUSE, 1) call and checks it runs before the HTTP bind; mutants (remove call, set it on Linux too, wrong MRO, skip HTTPServer.server_bind by calling TCPServer directly) are all killed. test_desk_http_edge_cases.py:1178 (existing win32 fake) and test_bind_refusals/test_ledger_and_bind_retry pass.
- Source check of the S5332 rule for this line: checkServerCallFromSuper fires on `super().server_bind()`/`serve_forever` only when the ENCLOSING class's bases are http.server.HTTPServer or ThreadingHTTPServer. _ExclusiveBind(socketserver.TCPServer) is neither; _Server has no super().server_bind/serve_forever call left (grep). So the finding at server.py:492 should clear. This is a restructure to satisfy the analyzer (the author says so; I agree it is honest).

### _StageMove (desk.py) read line by line
Old: list `moved`; in `attempt`: after UPDATE, `moved.clear()`, append True when rc==1 and state=="sent" and _mark_contacted; after _finish_update `if moved:` clear the mirror slot.
New: object `stage` with bool; `attempt` sets False at its start, then `stage.moved = rc == 1 and state == "sent" and self._mark_contacted(...)`; `if stage.moved:`. Same short-circuit, same value on every path where the old code reached `moved.clear()`. One difference, in the new code's favour: if a LATER try raises before the old `moved.clear()` line (busy) after an EARLIER try had set the flag, the old code could still free the mirror slot although the final result was "stayed locked, nothing recorded"; the new code reports no move. Rare, safe direction; the patch comment states it. `_mark_contacted` returns bool (mypy clean).
Tests: new stage tests pass old and new except the structure test. Mutants: "never moved", "ignore _mark_contacted", "always clear slot" killed. SURVIVED: (a) removing the reset line `stage.moved = False` - no test makes a later try raise after an earlier one set the flag; (b) dropping `rc == 1` - no test has rc 0 with a sent result and a movable stage. Nit: add those two tests (they are about unreachable-in-practice edges, but the reset line has a comment claiming a guarantee that nothing checks).

## 5. S5332 claim and honest per-issue ratings
S5332 claim checked at SonarSource/sonar-python master (ClearTextProtocolsCheck.java) and sonar-analyzer-commons master (appsec/CleartextProtocolFilter.java): CONFIRMED. The check reads each STRING_ELEMENT (skipped in likely test files); `unsafeProtocol` flags a value that starts with a clear-text scheme prefix unless `CleartextProtocolFilter.isSafeWithoutTls(value)`; SAFE_HOSTS exempts `localhost`, `127.x`, `[::1]`, link-local metadata, `*.svc.cluster.local`, `.test`/example domains, single-label hosts - checked against the literal text, so `f"http://{host}:{port}"` (host is "{host}") is NOT exempt, while `"http://127.0.0.1:5679"` is. The new `f"{DESK_SCHEME}://{host}:{port}"` element text does not start with `http://`, so nothing fires. Caveat: I read master; the analyzer version SonarCloud ran is unknown (the loopback exemption is recent). No other string in src/scripts/tools starts with a non-loopback `http://` (grep); demo_only is excluded in sonar-project.properties; load_tools has none.

| issue | my rating | why |
|---|---|---|
| S8786 identity.py:14 PLAIN | likely clears (~80%) | anchored; first rep `[^..@]*` cannot take "@", so rep1 ∩ continuation is empty; no UNKNOWN/PARTIAL implicit match-all (starts with ^) |
| S8786 identity.py:15 EMAIL | likely clears (~80%) | FULL match (fullmatch used in the file); pairs (local, domain-start-class, no-dot run, domain tail) are separated by "@" and "\." which are outside the preceding classes |
| S8786 run_real_check.py:116 | likely NOT (~85%) | see Major 1: both repetitions contain "@" and are non-possessive; and leading repetition under .sub |
| S8786 scrub_n8n_export.py:102 | likely NOT (~75%) | see Major 1: leading possessive repetition on a partial-match regex still counts; old had the same look-behind and was flagged |
| S5332 config.py:447 | clears (~90%) | f-string no longer starts with the scheme; master source |
| S5332 server.py:733 | clears (~90%) | same |
| S5332 server.py:1035 | clears (~90%) | same |
| S5332 feed.py:65 | clears (~90%) | same |
| S5332 server.py:492 | likely clears (~85%) | enclosing class bases no longer HTTPServer/ThreadingHTTPServer. Residual risk: `server.serve_forever()` (server.py:1033, 1202) is a different branch of the same check (FQN socketserver.BaseServer.serve_forever, receiver instance of HTTPServer). It was not flagged at baseline; _Server now has two bases, which could change how the v1 symbol resolves. I cannot measure it. |
| pythonbugs:S2583 desk.py:2092 | uncertain, lean clears (~65%) | closed-source engine; the old shape was a list filled by a closure; the new shape is an attribute written by a closure on a captured object. A field-insensitive engine would not claim "always false"; one that tracks a class attribute default (`moved: bool = False`) might. A fully robust alternative: make `attempt` return the move flag (or a tuple) through _locked_retry instead of a captured object. |
| pythonsecurity:S8703 feed.py:49 | uncertain (~50%) | closed-source taint engine; I can only say the request address is now rebuilt from constants plus int(port). Risk: `scheme` comes from `SCHEMES.get(<tainted scheme>)` and `trusted` from `next(h for h in (...) if h... == host)`; engines often keep taint through a lookup whose key is tainted. Safer shape: choose from constants by comparison (`scheme = DESK_SCHEME if s == DESK_SCHEME else "https"`), no tainted value used as a key, and have post() not take the address at all (host/port from Config) as the author's own fallback says. |
Summary: 11 targets -> 7 likely clear (2 regex + 5 S5332... counting S5332 x5 as 5), 2 likely not (the two regexes), 2 unknown (S2583, S8703). I.e. 2 + 5 = 7 likely, 2 likely not, 2 uncertain.

## 6. Mutants (28 run in a copy, /tmp/work/rv9-1/s/mut.py + one manual)
Killed: email old regex; plain old regex; address without look-behind; email dot-first; plain "@" in rest; mail guard removed; mail full-width "@" removed (manual, with test_scrub_n8n_export); scheme -> https; feed: any host, ignore userinfo, ignore path, ignore query/fragment, no check in post(), extra scheme ftp, raw hostname instead of trusted, ; bind: no setsockopt, set on Linux too, wrong MRO, skip HTTPServer.server_bind; stage: ignore _mark_contacted, never moved, always clear slot; desk_origin drops the port.
Survived (4): (1) MAIL local part back to non-possessive greedy: an equivalent mutant (same matches, no measurable time difference) - the possessive quantifiers have no test and no runtime effect; (2) feed host compare case-sensitive: equivalent unless own host has capitals (urlsplit already lower-cases); Nit: add a test with an upper-case own host; (3) stage reset line removed; (4) stage `rc == 1` dropped (see section 4).

## 7. What I could not do
- Run Sonar or the real analyzer. I downloaded the sonar-regex-parsing jar and wrote a small harness to run RedosFinder on all old and new patterns; the sandbox permission layer refused to compile/run the downloaded jar, so I did not. All Sonar statements are from reading the public sources (RedosFinder, RegexReachabilityChecker, LookAroundTree, SuperLinearRegexCheck, RedosMatchTypeHelper, ClearTextProtocolsCheck, CleartextProtocolFilter). The lead can run the one-file harness in /tmp/work/rv9-1/sp/h/Redos.java with /tmp/work/rv9-1/sp/pats.tsv (pattern list, one per line) if they trust the jar, or just look at the SonarCloud PR result.
- S2583 and S8703 are closed-source rules (rule text not public); ratings are judgement.
- Windows: only the faked win32 path on Linux plus mypy win32. Full suite, CodeQL, CodeRabbit: not run.
- Tokens: not measured.

## 8. Files
Report: /tmp/work/rv9-report.md. Patch reviewed: /tmp/demo-lead/handover/demo/sonar/sonar-p2-regex-http-bug.patch. Scratch scripts: /tmp/work/rv9-1/s/{fz.py,fz2.py,tm.py,feed_t.py,bind.py,mut.py,alt.py,dump.py}, logs /tmp/work/rv9-1/{pytest1.log,mut.log}. Head reviewed: db54e13 + P2 (untracked: src/lead_desk/urls.py, tests/test_sonar_p2_choke_points.py).
