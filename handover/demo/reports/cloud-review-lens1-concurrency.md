# cloud-review lens 1 (concurrency), fix5 535c43e, reviewer a2b9a9b0 (read-only, nothing run, findings are hypotheses until a test reproduces them)
Summary of findings (full text kept in the session; N1-N11):
- N1 MAJOR in-flight limit is a BoundedSemaphore (desk.py:186, 613): barging, old waiters starve past 5 s -> explains 65/124 busy. Fix: FIFO counting hand-off.
- N2 MAJOR follow-up drives (about 8 gated writes each) are not limited by the in-flight permit and share the FIFO write queue; later request writes time out. Fix: count drives against a permit or two lanes (request writes first).
- N3 MAJOR a busy answer inside _after_claim burns one of 5 auto tries and records internal:OperationalError. Fix: on is_busy leave row for reaper / refund the try.
- N4 hypothesis: direct hand-off + GIL slows gate throughput. Measure.
- N5 MAJOR per-op waits far above 5 s: GateTimeout retried 3x with a new tail ticket each time (15-30 s per write, 50-90 s per process()). Fix: one deadline per request; no re-queue on retry.
- N6 MAJOR reaper grace (send_timeout + 15 s) shorter than worst-case result-write time (30 s): double handling window. Fix: touch updated_at before result write or derive grace from real bound.
- N7 minor reaper drives sequentially, head-of-line block on busy row, stop_background join 10 s.
- N8 minor FairGate not safe against BaseException inside acquire (ticket stays in deque).
- N9 minor schema writes bypass the gate.
- N10 minor nested acquire from a hook deadlocks 5 s.
- N11 minor 503 with open receipt (contract.md:15,85 accept) vs ORDER 202 'no open receipts after 503': decide the requirement wording.
Sound: FairGate wakeups/timeouts, claim CAS, attempts token, same-receipt decide serialisation, no wait cycle, DML all in _write, lockfile.
