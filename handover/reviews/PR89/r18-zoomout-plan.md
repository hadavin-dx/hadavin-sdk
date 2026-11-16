# PR89 D-002 plan review, egm:egm-zoom-out (Fable 5.2), read-only. Verdict: do NOT build D-002 as written.
P1 Major: database-name marker refuses the CI address postgresql://postgres@localhost:5432/postgres (ci.yml 86/93) -> change CI in same PR or drop marker; loopback is not proof of "throwaway" (tunnels/proxies).
P2 Major: boolean allow_remote_address is a wildcard; container CI reaches DB as host "postgres"/"db" -> exact host allowlist throwaway_hosts=(...), default loopback literals + socket.
P3 Major: M3 must reuse the strict grammar _address_parts (extended to return parts), fail closed on "unparsed" when pass_env set; key allowlist for key=value form; both host and hostaddr must be allowed (libpq hostaddr / service= / ?host= overrides).
P4 Major: k-gram pass is still a denylist and will not converge. Primary fix instead: when secrets non-empty, OUTPUT PROJECTION at _row + skip messages + baseline error: first_lines = exception class identifier + fixed word for expect match + caller's expect; test id = path + function, [param] replaced by fixed word; existing _masked unchanged as second layer; fuzz test: no 4-char slice of a secret in any output field outside caller's expect.
P5 Major (if k-gram kept): 6-grams of the CI value shred "postgres"/"localhost"/test ids.
P6 Major: M1/M4 (never-run mutants, full suite) need an evidence run on db0d9eb first.
P7 Major: r18-codebase m4 (masked first line in baseline error) adds a new free-text site -> under pass_env only _run_end(base_rc) + class name; split batch: evidence, M2+M3, minors; pins once at end.
P8 Minor: ladder line; do not reuse guard.runmap.redact_text (pattern-based, RedactionError, 6 s budget, couples stdlib-only copied tool to product). P9-P11 nits.
Not checked by reviewer: nothing executed; libpq claims from knowledge; most of the test file.
