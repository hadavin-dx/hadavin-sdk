# fix-review4 (2026-11-16): round 4 of REVIEW.md applied
Source: reviews/round-12z-findings.md, section "REVIEW.md round 4". Backup: scratchpad bak-rev4/REVIEW.md. Static work; no patch or patched tree on disk (every patched-copy cite stays unchecked).

Checked in the files first (src, opened by me):
- M1 confirmed: demos/ask-your-data/askdata/meter.py:48-57 (price multiplied at :53-56); askdata/config.py:39-44 RouteCfg plain Decimal; :64-69 builds core Route from it; never load_config. Consequence: choke point on Route, but a zero price is legal for the fake kind (k1b/replay.py:88), so open design choice. Stale lines "Demos were not grepped" and "no demos folder" replaced.
- M2 PARTLY NOT CONFIRMED: agent_loop.py:485-486 and limits.py:17-18 are in handle (model-call path), not on_decided (agent_loop.py:799). Execute path traced: reads, limits.blocked (read only), audit writes, runs UPDATE (transition, touch), client hooks (not read). No add_spend, no plans write found. Full tick write list now in the X-2 row; stated as complete only for repository code.
- M3 confirmed: audit reconcile() defined only at chain.py:232, local_dir.py:126, protocol.py:27; no caller in src; tick.py:85 is the approvals step. Live consequence written in the effective-count paragraph.
- Minor: step-name note added to A-7. Nits: Money type (C-1 row), model_copy at tests/test_k1b_replay.py:381-382 (C-4 row), X-1 marked moot (ceiling cut).
Not checked: client hooks, approvals/gate.py, demo config files and prices, guard/injection.py:77, Postgres, any patch file.
