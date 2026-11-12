# pdbanner-482f7dcc-codebase-r3: part 6 (mode banner, demo-only guard), head 482f7dcc, round 3, persona codebase details

Source: hand-back of the codebase reviewer (agent a188bfd8), saved by the lead (condensed). SECURITY / mode-safety path. Read-only, nothing run. Snapshot `/home/user/build/snap/pdbanner-482f7dcc`. CAVEAT: the snapshot holds only changed files; for config, tools, app, executor and guard/http the reviewer read the on-disk checkout, which may not match head (it saw `environment: dev` and `DEV_ONLY`, banner code uses `demo` and `DEMO_ONLY`). Major 1 must be re-verified against head before it is fixed. 0 Blocker, 2 Major, 7 Minor, 2 Nit.

## Major
- **1** Tool-manifest hosts are reachable but invisible to the banner (mode_banner.py:275-290, CHANGELOG "A tool module reaches only those systems, hosts and sources"). `ToolContext.fetch` (tools.py:585) checks the URL against the tool manifest's own `spec.hosts`, never `config.egress_hosts`, `systems` or `sources`; `spec_problems` (tools.py:221-228) checks only host shape and loopback/metadata names. Failing input: demo config, fake and memory backends, empty systems/egress_hosts/sources, a tool manifest `hosts: [crm.example.test]`, the function in `tool_modules`: banner is tone demo, "made up", "nothing sent", while the tool can https GET that host. Cause: `banner_from_config(config)` never sees tool manifests (registry `_load_tools`). Fix direction: take the registry's tool specs as input and count any non-loopback host, or drop the sentence and the CHANGELOG claim. Related: tool-module Python runs in-process and can open sockets itself; "the network guard refuses the rest" holds only for `ToolContext.fetch`; the sentence needs that qualifier.
- **2** Guard bypass with fullwidth/NFKC identifiers (tools/demo_only_guard.py:152-155, :316): `from ｄｅｍｏ_ｏｎｌｙ import y` imports `demo_only` (PEP 3131 NFKC) but the regex is only IGNORECASE. Same for file and folder names on the path check. Fix: NFKC-normalise each line and path segment before matching.

## Minor
- **3** `getattr` defaults fail open (mode_banner.py:281,284,287): a config lacking `systems`/`egress_hosts`/`sources` reads empty and gets the demo banner; real-Config test covers `systems` only; `ConfigLike` does not declare them. Add real-Config tests for the other two; raise when a real Config loses a field.
- **4** URL parser differs from the client's (mode_banner.py:254-260): `https://evil.example\@localhost` gives hostname `localhost`; `tools.py:560-566` already refuses backslash, whitespace, control, non-ASCII, `%`, `@`-credentials. Mirror that: such a URL counts as leaving the machine.
- **5** Loopback is not "nothing real" (port-forward, tunnel, sidecar): state the limit next to the demo sentence.
- **6** `casefold` broader than DNS (mode_banner.py:91): use `.lower()` plus an ASCII check.
- **7** Python name check is substring (`in`, :205), page script is whole-word `hasName`: make them the same rule.
- **8** Skipped binaries are never searched (guard :268): `.pyc`, `.so`, `.zip`, `.whl` with a NUL in the first 8192 bytes are skipped unread; a sourceless `.pyc` in a package dir is importable; UTF-16LE text without BOM reads as valid UTF-8 with NULs and is not matched. Byte-search them for the name or refuse those endings in product roots.
- **9** Banner computed once; systems/egress_hosts/sources are mutable inside a frozen model; document it.

## Nit
- 10 `_looks_binary` and `_scan_file` read the file twice. 11 `_check_what_is_claimed` skips empty claim strings (`c and c in said`): `BannerWords(made_up="")` disables that check silently.

## Checked and found fine (by reading)
Backends classification (unknown kind counts real); systems (non-str, None, unparseable, ValueError, userinfo tricks, `localhost.example.test`); `_is_this_machine` forms (`[::1]`, trailing dot, 127.x, 0.0.0.0, 127.1, decimal, zone id; odd forms read real); egress (empty, non-str, wildcard, port); sources (unknown kind, build failure read real); env cannot change endpoints; DEMO_ONLY kinds carry no endpoint; JS freeze, `hasName`, unhide-first read right; guard submodule and nested repo detection, text renamed .png, 8192-byte NUL rule, exact-case phrase lookarounds, non-UTF-8 gives unreadable-file hit, symlinks and missing root.

## Not checked
Nothing executed; on-disk checkout versus head; ci.yml and marker wiring; pyproject packaging; ignored files; run-time-built names; whether the fullwidth import resolves on the project's Python; test files beyond their diffs; mutant harness validity.
