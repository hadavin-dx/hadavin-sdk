# QUESTIONS from core-b
1. (2026-11-20 05:22 UTC / 10:52 IST) Board cron refused twice by the cloud session's permission check (ESCALATIONS.md E1). Tried: CronCreate "* * * * *" before and after the owner's GO. Recommended answer: accept a board at the end of every tool batch; or the owner allows scheduled tasks for this session in its settings.
2. (2026-11-20 05:22 UTC / 10:52 IST) inputs/lead-baselines-SUMMARY.md lists 1 failed test on core/P2a-1 and on core/P4a but not which one. Tried: nothing (lead runs baselines). Recommended: lead adds the failing test id and whether main fails the same way.
3. (2026-11-20 05:22 UTC / 10:52 IST) Step A: build on wip/cloud-core-b/A as soon as the ticket exists, with no extra GO? Recommended: yes (ORDER 004 item 5).
4. (2026-11-20 05:22 UTC / 10:52 IST) May my one lane run use the container's own PostgreSQL 16.15 (no Docker) for T1 and the store contract, as an extra signal? Recommended: yes.
5. (2026-11-20 UTC) ORDER 020 M1, release command: I numbered the new migration 0008 (0008_release_expired_spend.sql: the release function and the closed_at index); highest existing was 0007, no other branch carries a 0008. Please confirm 0008 (or give the number) before it is released: its sha256 goes into tests/fixtures/migrations_released.json only when you release it. Recommended answer: confirm 0008.

