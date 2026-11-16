# A4 review round 1, lens: concurrency, resources, lifecycle (egm-codebase-details, snapshot A4-r1)
Saved from the reviewer's inline report. Code reading only: no shell, no tests run.
Sound: deadline covers request line, headers and body (all reads go through _DeadlineReader.readinto); dribbler bounded 10 s + 10 s; no pipelining (close_connection); Expect/chunked bounded; drain and finish bounded (~2 s extra); slot accounting has no leak or double release by reading; accept loop cannot be stalled by the 503; no DB lock or portal slot held by a stalled sender; 408 path attributes pre-set; follow-up not skipped by the swallowed write.
Findings
- M1 (Major) `_refuse_busy` (server.py ~152-164) writes the 503 and closes without reading: a client that already sent its request gets a reset instead of the 503 (the problem finish() documents). Test passes only because its 4th socket sends nothing. Fix: short bounded drain before close; test where the refused client sends a full request and must read 503.
- M2 (Major) the 64 cap is a new refusal point not load-tested; fuzz evidence is pre-S1; 503 from the cap is indistinguishable from the desk's 503; 64 slow senders re-opening every 10 s still starve everyone (no per-peer limit).
- M3 (Major) the socket timeout left by the last read governs the reply write: a request finishing 0.2 s before the deadline gives the reply a 0.2 s write timeout; with the swallowed OSError this is a silent truncated reply (lead already committed). Fix: settimeout(self.timeout) after each successful read or before writing.
- M4 (Major/Nit) `_resolve` (server.py ~514) lacks a TimeoutError handler: slow body there logs "handler failed: TimeoutError" and answers 500. Untested.
- N5 `_send_bytes` swallows every OSError silently incl. write timeouts: log/count a lost reply; swallow only reset/pipe family.
- N6 thread-start failure: slot released, but client gets a silent close, not 503.
- N7 Windows: read-side ConnectionResetError in readinto not handled; busy-path RST more likely there.
- N8 stop() does not join handler threads.
Evidence not supported: "known-red test fails identically on clean base" (no output; it exercises the changed swallow path, deselected in the final run); test_f14 deselected without reason; "no leak path" not load-tested; fuzz pre-S1 and its Not-tested list excludes keep-alive/pipelining/slow-body on GET.
