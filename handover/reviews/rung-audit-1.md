# Rung audit 1 (lead order 54): summary of the five parts

Assembled 2026-11-06 by the cloud session from the five audit agents' parts (`rung-audit-1-part-A.md` to `-E.md`, same folder). Read-only audit: no ticket edited, no code, no test. Rungs: 1 studio code, 2 the client's tool, 3 no-code/low-code (n8n), 4 MCP server, 5 maintained library or standard tool, 6 new model feature, 7 our code. Each part has the full per-ticket tables (component | must do | rung | evidence | what only our code gives | verdict) and its own UNVERIFIED list; this page only collects the summary rows. The core safety chain (P1m, P1a, P1b, P3a, P4d, P2a-1, P2d-1, P2d-2, P4a) was not audited, as ordered.

## Honest headline
The owner's suspicion (code-first even where no-code fits) is mostly NOT confirmed for the unbuilt tickets: nearly every remaining component is one of the guarantees order 54 itself lists as justifying code (no lost or double-applied message, exact-decimal money, masking before the model, audit tamper-evidence, evals that gate, tenant and least-privilege rules). The real cuts are small. Where the kit was already cut to config, the cut had been done in the tickets (AK-G2 sends e-mail, folders, queues and schedules through the client's tool or n8n; AK-G15 already cut notices, the client-tool mirror and the person's screen).
Total of the proposed cuts: roughly 10 to 18 agent-hours of builds, against a kit of several hundred (estimates by the part authors from row and mutant counts, NOT measured). Treat the total as an order of magnitude.

## Summary table
| ticket | cut? | agent-time saved (estimate) | risk | part |
|---|---|---|---|---|
| AK-G16 | partial, small: -b2 rights check becomes a runbook table; lint L11 to kube-linter; env half of L6 folded into L18; L12 dropped (BN-34: no migrate Job); image template a static file. NOT the Python renderer (Helm/Kustomize bring back YAML text templating, R2-ADV-9) | 2.5-4 h of an estimated 25-35 h | a client without kube-linter lets a pod with no resource limits pass (reliability); rights list unchecked until V1 | A |
| AK-G2 | partial, very small: reuse AK-G16-d's `door_app` + stdlib wsgiref instead of its own dev server; B2's request generator to k6. Main cut already made in the ticket. GAP (not a cut): no multi-hour soak and no 3x-peak test (R370) | 1-2 h | the dev-server cut only works if AK-G2-b merges after AK-G16-d; B1 (faults between commit and reply) stays code | A |
| AK-G15 | partial, later rows only (V1, V5, V11, V13); v1 build: none | 0 now; 4-8 h later | a notice or mirror that copies text breaks the no-text rule; re-run money path, closed-state trigger and roles stay code | B |
| AK-G1 | partial, later rows only (V1 server-side compaction, V8 chat adapter); v1 build: none | 0 now; 2-4 h later | compaction is a beta feature of one provider, so our summariser stays as the alternative; summary must be masked before storing | B |
| AK0 | partial: D3 chunker (provisional); D12 stays code (ranx last release 2025-08-07 fails AK0's own 12-month rule) | 1-2 h in AK2a (close to a wash) | worse clause cuts; one more dependency; a value split across two chunks passes masking in both halves | B |
| AK1 | none | 0 (import-linter would cover about 2 of 16 lint rows) | n/a | C |
| AK2a | partial: AK2a-2 child-process runner for hostile PDFs becomes a no-network parser container (docling-serve MIT, or pypdf in our image) + thin client | 3-5 h minus about 1 h container work (15 of 51 rows, 29 of 95 mutants; uncapped security review path) | one more service; if ever started with networking the "no outbound path" claim is false (4 test ideas named) | C |
| AK4a | none | 0 (pytest capture covers under 80%: misses loggers that do not propagate) | n/a | C |
| P4b1 | none | 0 (gateway tested by the lead 2026-11-06: no reserve-before / settle-after per run) | n/a | E |
| P4b2 | none (pg_cron swap optional, not recommended) | 0 (at most 0.5 h) | second SQL path | E |
| P4c | none for core (cutting P4c-1 would save 3-5 h but R368 needs it; test idea: kill between writing run state and sending) | 0 | lost message after a crash | E |
| P5b1, P5b2, P5b3, P5b4 | none (the "provider adapter" suspect does not hold: none builds adapters, retries or failover; retries exist in `llm/retry.py`, vendor SDK retries are off on purpose because P4b2 books every attempt) | 0 | a Semgrep rule would cover about 40% of P5b2 and add a CI tool | D |
| P5b5 | partial: checker rules 3 (traceback import) and 4 (basicConfig) to ruff banned-api config | 1-2 h | ruff misses `__import__("traceback")` (run on ruff 0.16.9; repo pins 0.17.1) and cannot say "only inside run_case" | D |
| P5c, P6a, P6b1 | none | 0 | n/a | D |
| P6b2 | none (hybrid optional, not recommended) | 0 to 1 h | ruff covers about 55-65% of the env lint (`getattr(os, "environ")` not flagged) | D |
| P8a | none (no core code; Renovate costs more than one bump) | 0 | n/a | E |
| P8b | partial: drop the T2 awk checker and about 21 planted faults (T3 already runs ledger_check.py on the laptop) | 1.5-3 h | a bad ledger row is caught one round trip later; no safety guarantee involved | E |

## Cross-ticket notes
- Part D idea, not a cut: five tickets each specify their own source-code scanner; one shared scanner could save 2-4 h. Lead's call.
- Part B: G14 (the screen where a person acts) is outside all audited tickets and is the largest human-side surface; it has no ticket and no rung table. Say if you want one (the UI itself is built by the lead from the studio portal kit).
- Part C: a cloud knowledge-base service could chunk, embed and retrieve only text we have already masked; uploading raw PDFs would skip our masking, so it cannot be the default. Embedding, vector store and retrieval are in AK2b, AK2c, AK4b, not audited here.

## What this audit could NOT check (read before trusting any cut)
- Web access: only github.com and pypi.org resolved from this session. Documentation hosts for n8n, kube-linter, Kyverno, Docling, import-linter, LiteLLM, PagerDuty, Renovate, Astral and Semgrep did not resolve. Tool facts therefore come from GitHub pages, pypi.org JSON, search snippets, or running the tool on made-up files (part D). Counts of UNVERIFIED items: A 14, B 12, C 10, D 11, E 9 (56 in all).
- The most important single unverified fact: whether n8n stores a webhook request before it answers (decides how much of the AK-G2 front door a no-code tool could carry).
- Agent-time numbers are estimates from row and mutant counts, not measurements.
- Order 54 item 4's rule ("a higher rung covering 80 percent or more gets cut unless the ticket proves a guarantee gap with a test idea") was applied by each author; where a part kept code it names the guarantee, and some name the test idea (P4c, AK2a, AK-G16).
- No cut was applied. The AK-G2, AK-G15 and AK-G16 builds have not started and will not start until you have read this page.

## Part F: retrospective (P1m mutation runner, P1a textnorm), added after order 56
Source: `reviews/rung-audit-1-part-F.md` (commit a9c091d; no independent review; 13 items UNVERIFIED, GitHub API returned 403 so maintenance rests on PyPI release dates).
- P1m: mutmut and cosmic-ray alone are not enough (both count a crash as "killed"; mutmut cannot run a named hand-written mutant); nobody tried them in the ticket. Verdict: the 107-line kill-reason judge and the runner are KEEP-CODE. Lesson: about a third of the runner and its review rounds went to a developer tool that R448's guarantee list does not name.
- P1a: unicodedata plus the official look-alike file via our generator is already the right rung; no library gives the repeat-safe, case-symmetric keys, the U+0345 rule, the length cap and the pinned Unicode version. One improvement finding: `has_mixed_script` misses Runic and Tamil mixes; fix by generating Unicode script data with the existing generator, not by adopting confusable_homoglyphs (last release 2024-01-30).
- Not proven either way: whether a ready-made tool covers 80 percent of the P1m runner (none of the 21 P1m or 55 P1a mutants were run through either tool).
