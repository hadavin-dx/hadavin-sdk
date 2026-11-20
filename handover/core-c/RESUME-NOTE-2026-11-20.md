# RESUME NOTE of core-c, written 1735Z (owner STOP order ~23:03 IST). Supersedes the 06:40Z note (kept in git history).
Everything below was read from git at the moment of the stop. Repo /home/user/hadavin-sdk, remote hadavin-dx/hadavin-sdk. Session model: claude-sonnet-5-5 (proof at the top of handover/core-c/REPORT.md).

## The one head
cloud/core-c = 0b4db37c8. It holds everything verified: gate (NO_MAP, usd_cap, mark on ProviderExhausted, G13/G13b/G13c/G13d net, G14 per-message cache + audit_dropped, Q1 reply masking + guard/putback.py, P7 LimitsMeter), redactor (G4c/G4d host names, G7, G8, G9/G9b/G9c, G10, G12/G12b/G12c/G12d/G12e, E9, E14), docs DOCS2-DOCS6 in root SECURITY.md/CHANGELOG.md/README.md (docs review cap reached: open style items in tickets/DOCS-style-review-5.md and evidence/DOCS6-notes.md). The g2 and g3 branches are superseded (evidence/REC-notes.md).
Suites at idle on 2552bcc95 (before the later merges): non-perf 16071 passed, 2 failed (vendor string in the lead's handover/BRIEF-PREAMBLE.md; k5 recording, fixed); perf 96 passed. Whole-tree mutants on the merged head: g12 50/50, gate 158/159 (R8 equivalent); redact_mutants whole was still running at the stop (log /tmp/core-c-mut-final.log, lost if the container restarts): RE-RUN IT.

## Branches NOT merged (pushed; tips)
| branch | tip |
|---|---|
| wip/cloud-core-c/q1-reply-mask | d4add25f9 |
| wip/cloud-core-c/q2-spend | 7173d30cc |
| wip/cloud-core-c/q3-g15-net | e67ab15c4 |
| wip/cloud-core-c/p7b | 5a1be73c8 |
| wip/cloud-core-c/grants | b55d21865 |
| wip/cloud-core-c/p3-scratch | c4c554dc4 |
| wip/cloud-core-c/f-findings | 9622a6840 |
| wip/cloud-core-c/g12e | 4731c671b |
| wip/cloud-core-c/g14 | 671801bc3 |
| wip/cloud-core-c/g9c | 00c192d65 |
| wip/cloud-core-c/g13d | 64516aae8 |
| wip/cloud-core-c/g4d | 23c5ea3b6 |
| wip/cloud-core-c/docs6 | 4c061cd72 |
- q2-spend: fail-closed spend (gate side) incl. Reply.cost_verified (models.py, one line) + request for core-b; whole gate_mutants NOT RUN; needs core-b (cost_verified in adapters, usd_cap at install, attempt_costs from llm/retry.py). Merge after a fresh review and a whole gate_mutants run.
- p7b: LimitsMeter review fixes; gate_mutants whole NOT RUN (3 new mutants unchecked).
- q3-g15-net: G15 independent final net (guard/finalnet.py); status as of the stop in evidence/Q3-build-notes.md if present; otherwise unfinished.
- grants: re-pinned grant tests for core-b's head (b55d21865): base is core-b's branch, not mergeable onto cloud/core-c; core-b/core-a take it.
- p3-scratch: gate end-to-end with core-b's real store (18 pass, 2 strict xfail): scratch merge of core-b + core-c; findings in requests/for-core-b-p3-findings.md.
Merging order when resumed: q1 is already merged; then p7b, q2 (both edit model_gate.py: expect small conflicts), q3. After each: ruff, tests/test_model_gate.py + test_runmap_enforce_map.py + test_gate_mutants_picked_up.py + test_gate_install_callers.py, whole gate_mutants (only R8), fresh review of the diff.

## Open packages (next steps)
1. Q1b (Q1 review: tickets/Q1-result-review-1-codebase.md): ReplyMaskFailed is a GateRefused but the call was paid (sibling class or fix docstrings); non-str values pass raw (fix() and reply.text); BaseException in _mask_reply writes no row/settle; put_back exposure (document, apply only to approved plan fields); mask tool-call name; per-tool budget.
2. Q2/P7b/Q3 merges as above, each with a fresh egm reviewer.
3. P8 ledger (tickets/P8-flow-review-1-design.md): item 4 quarantine/drop path for a planted-value refusal (G14 did only the cache); item 5 reproduce the 256 KB scan cost at idle and pick one number; item 6 = Q3 G15; item 7 masked flag, K16 and object_ref on reserve_interrupted/reservation_invalid; fold F1-F3, E25=(a) and a promised/not-promised table into SECURITY.md (docs change).
4. P10 perf run at idle (load under 2) on the final head; also re-run the whole non-perf suite.
5. G11 opaque-token post-pass: waits for the lead decision E16. K5 closed (core-a's items).
6. Lead-owned: handover/BRIEF-PREAMBLE.md contains a vendor string that fails test_no_vendor_brand_string_is_tracked.
7. core-b actions: LimitsMeter at install, set the refusal mark in its retry layer, cost_verified, usd_cap, worst-case function (requests/for-core-b-f-install.md, for-core-b-p3-findings.md, for-core-b-spend-failclosed.md on the q2 branch).
8. Decisions kept: extract.py KEEP (DECISION-extract.md), textnorm DENY API KEEP (DECISION-textnorm-deny.md), R8 known equivalent mutant, G10/G9/G12/G13 default numbers (list in docs 1b).

## Tooling notes
Run python as PYTHONPATH=src uv run --all-extras --group test ... from any worktree under /tmp. Mutant runners copy the worktree src. Heavy runs: at most 2, load under 4; timings only at load under 2. Board script (manual push): scratchpad board/board.py + state.json under /tmp/claude-0/.../scratchpad (lost on container restart; the board file handover/core-c/STATUS-BOARD.md is in git).
