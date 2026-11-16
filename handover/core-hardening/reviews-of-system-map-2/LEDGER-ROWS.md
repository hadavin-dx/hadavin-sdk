# Ledger rows (9 columns: id, source file + finding id, severity, area, summary, status, fixing artifact, verified-by, date)
| id | source | severity | area | summary | status | fixing artifact | verified-by | date |
|---|---|---|---|---|---|---|---|---|
| SM2-01 | review-design.md D-1 / review-codebase.md C-3 | Major | system-map decisions | Dollar cap decision A not costed; limit blank; arithmetic contradicts the 1-new-lead proof | OPEN | CORRECTIONS.md Major 1 (system-map session edits SWEEP Decisions A) | - | 2026-11-16 |
| SM2-02 | D-2 / C-2 | Major | system-map decisions | Alert channel decision B contradicts itself; heartbeat channel unnamed; watcher still "laptop lead" | OPEN | CORRECTIONS.md Major 2 | - | 2026-11-16 |
| SM2-03 | D-3 / C-9 | Major | system-map rating | L2-FD-018 Blocker while values made-up; public status and gitleaks unconfirmed | OPEN | CORRECTIONS.md Major 3 | - | 2026-11-16 |
| SM2-04 | D-4 | Major | system-map proof | Independence of the proof count not checked before the video | OPEN | CORRECTIONS.md Major 4 | - | 2026-11-16 |
| SM2-05 | C-1 | Major | system-map evidence | "Shared Postgres superuser" stated as fact without evidence | OPEN | CORRECTIONS.md Major 5 | - | 2026-11-16 |
| SM2-06 | evidence-cites.tsv, C-6 | Major | system-map evidence | 85 of 154 cites point at files absent here; ci.yml:228 out of range (file 144 lines) | OWNER-ONLY | CORRECTIONS.md Major 6 (needs a laptop reader with the take files) | - | 2026-11-16 |
| SM2-07 | D-5, D-6, D-7, D-8, D-9, D-10 | Nit | system-map text | Verdict cell, double listing, missing interim mitigation and costs, superseded counts, grep wording | OPEN | CORRECTIONS.md Nits | - | 2026-11-16 |
| SM2-08 | C-4, C-5, C-7, C-8, C-10 | Nit | system-map cites | Duplicate cite, off-topic cite, state-column contradictions, thin line-7 cites, saved-copy status | OPEN | CORRECTIONS.md Nits | - | 2026-11-16 |
| SM2-09 | ORDER 012 item 2 (C-01) | Major | core config | Zero or negative route price and unbounded max_tokens accepted at load | FIXED-UNVERIFIED | patches-ready/C-01.patch (applies on b4cce5b; tests not run) | - | 2026-11-16 |
| SM2-10 | ORDER 012 item 2 (A-01) | Major | core audit | Nothing calls audit.reconcile(); failed audit write leaves no log line | FIXED-UNVERIFIED | patches-ready/A-01.patch (applies; tests not run) | - | 2026-11-16 |
| SM2-11 | ORDER 012 item 2 (G5 wording) | Nit | core docs | redact.py and gate.py text implied a G5 leak check exists | FIXED-UNVERIFIED | patches-ready/G5-wording.patch (comments only) | - | 2026-11-16 |
| SM2-12 | ORDER 012 item 2 (dead-man) | Major | core ops | No outside check that the tick still succeeds | OWNER-ONLY | patches-ready/DEAD-MAN-CHECK.md (second alert channel is a studio-head decision) | - | 2026-11-16 |
