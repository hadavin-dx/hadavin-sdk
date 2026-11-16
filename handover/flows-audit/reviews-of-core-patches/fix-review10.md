# fix-review10 (round 10 of REVIEW.md; static, nothing run, nothing committed)

Findings: section G of reviews/round-16z-findings.md (reviewer words, unverified; each item opened by me in src, tests and the demo before editing). Backup of the file before this round: scratchpad bak-rev10.md and pre-fix10.md. EGM skipped: fixer role.

## What the reviewer got wrong or only half right (first)
- M1, detail: the reviewer wrote that a junk checkpoint row ABOVE the head "does not suppress signing of heads below it". On the current code that is false: `signed_through()` is MAX(seq) (chain.py:290-293), so a row above the head makes chain.py:307 return without signing. It becomes true only after fix (ii). The main point of M1 (head-seq case cannot work without a schema change) is correct and confirmed. REVIEW.md X-5 (f) now says both.
- M1, detail: "fix (ii) needs the public key or a verify routine inside the writer": a writer that holds a signer has `signer.public_key()` (chain.py:352 uses it); only a writer built with `signer=None` (the drain) lacks it. Written as such.
- M3: the reviewer left open what `execute` does when `audit.events()` raises. Opened: agent_loop.py:844-854 catches Exception and moves the run to NEEDS_PERSON with reason `audit_unavailable`, so it is a fail-closed stop with a misleading reason, not a crash. Written in X-5 (c)(iii).
- M2: confirmed from migrate.py:47-59 (one runtime grant map; three roles only, `migrate.py:286-288`, `:298-303`). The kill-switch writer in code is the operator command (cli.py:383-408, limits.py:45/51); the agent loop only reads it (agent_loop.py:252, :817). Spend only ever adds (postgres.py:416-431). `approval_decisions` is written only by the receiver path (postgres.py:337-345, requests.py:170). Not checked, and said so: whether a deployment uses one DSN, and whether the receiver is a separate process.

## Changes in REVIEW.md
- M1: X-5 (f) fix (ii) and its test reworded: (1) head-seq case needs a schema change (new migration 0006, key (seq, hash), ON CONFLICT (seq, hash)); `_check_anchors` (chain.py:443) builds `{seq: (head, signature)}` and assumes one row per seq; stays OPEN until the lead picks the schema change. (2) Achievable test: junk row above the head; three assertions that fail on current code; limit stated (the junk seq is later blocked when the chain reaches it).
- M2: decided a NEW row X-6 (Major, PROPOSE FIX): the one runtime role serves agent, tick and approval receiver. Rights cited, fix with three identities (agent, operator, receiver), who holds each credential, a trigger refusing a lowered spend, five negative tests. X-2's sentence about the receiver identity corrected (true in code, not in the database). Counts updated everywhere (rows 25, Major 11, PROPOSE FIX 23; live Majors 3, effective count 4 or 5 after G5, 3 or 4 before; choices four to five), Counts section pasted output replaced after running the script.
- M3: X-5 (c)(iii): unparseable-body read denial via `ChainAudit.events()` (chain.py:279-286) and agent_loop.py:847; per-row guard fix for events() and reconcile() (chain.py:243) and tests that fail on the current code.
- local_dir stated as DEMO_ONLY (backends/table.py:593-601) and refused when live (config.py:394-397) in the single-dependency section and the A-3 corrupt/ note; weight lowered.
- Cites fixed: fake.py:54 (was :52); common.py:171 (was :172); anchor call chain.py:318-319 (signing is :309); cli.py print and return 0 at :396-397, unreachable-store exit 4 at :370-374, :383-388 is the docstring; local_dir.py glob :141 (was :140); evalcli.py:148 ConfigError is the demo's askdata.config.ConfigError (config.py:21, imported evalcli.py:24), not hadavin_sdk.errors.
- Imprecise statements: X-5 (j) "no database role" corrected (test_capabilities.py:45 and :59 run on chain_postgres with the owner DSN, audit_chain.py:128-138); chain kind is in-memory SQLite or Postgres, no file SQLite (chain.py:523-543, 102-105), memory chain loses events at exit (k1b/audit_sink.py:21-23); drain rights (g) now column grant SELECT (seq, hash, event_id) + INSERT (confirmed: `_append` reads only event_id, seq, hash, chain.py:185 and :187; precedent Grant.purge_cols); header numbering made consistent; "to any/every role" trigger wording changed to "runtime, portal and purge roles" (owner or superuser can disable).
- Not checked section extended.

## Checks (from handover/flows-audit, real exit codes)
- python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md: rc 0; rows 25, Nit 10, Major 11, Minor 4; PROPOSE FIX 23, DECLINE 2.
- python3 -I tools/check_secrets.py: rc 0 (PASS 0 hits in 1796 files).
- python3 tools/check_refs.py: rc 0 (PASS 5154 references).
- ruff check .: rc 0.
- ruff format --check reviews-of-core-patches .: rc 0 (512 files already formatted).

Nothing run against Postgres or the patches; nothing committed.
