# Hostile-reader review of /tmp/e18-312/README.md (read-only; no tests run; no network)

Overall: the README is heavily hedged and mostly honest. No prices, client names, partners or "production ready" claims. No "we/our" (it uses "the author"). Findings below.

## Table (line | quote | class | suggested fix)

| line | quote | class | suggested fix |
|---|---|---|---|
| 10 | "in the tests of this repository ... the desk never sent a second email" | claim backed only by tests I did not run | keep, but name the test file/command that shows it |
| 14 | "read through by the author. No review record is kept" | honest, but "read through" is vague | say "read by the author; no independent review" |
| 108 | "All ten were simulated by an exception ... D2 also tried with a real process kill" | claim relies on docs/limits.md | verify limits.md has the kill-test output; link it |
| 113 | "may remember a send key for a shorter or longer time" | fine (hedged) | none |
| 116 | "No penetration test was done." | honest | none |
| 139 | "The first question of the project was whether n8n on its own handles duplicates" | implies a comparison with n8n-only but none shown (README says so); reader may infer n8n is worse | delete sentence or move to docs; state plainly "not tested" |
| 163 | "for the author's own use" | tools shipped with no explanation | say they are not needed to run the demo |
| 174 | "The author may record and publish demo videos" | unexplained licence term, could read as a promise | clarify or remove |
| 8 | "revenue-operations person ... or n8n freelancer" | audience wording suggests marketing | acceptable; optional trim |
| 7 | "It is not software to install for your business." | good disclaimer | none |

No prices, clients, partners, "production ready" (only "not claimed", line 11 and 114), and no "we/our" found.

## (2) Sentences needing outside knowledge
| line | quote | fix |
|---|---|---|
| 8 | "(it gives each lead a label, hot, warm or cold)" | fine; but "AI step" never defined before line 8; add "an AI model decides" |
| 29 | "such a request goes to review; see `contract.md`" | "review" explained only at line 36; reorder or say "waits for a person" |
| 43 | "Reaper" | metaphor; first use says "background job" so OK. Define in one clause earlier since line 22 says "background pass" |
| 31 | "RecordedQualifier" | code name; fine but add "(the AI step stand-in)" |
| 42 | "Crash point ... `A`, `C0`, `D2`, `N1`" | letters meaningless without docs/tests.md; the "ten" are never listed in the README |
| 74 | "Set-ExecutionPolicy -Scope Process RemoteSigned" | explained in the same line; fine |
| 117 | "developer tools" / "Host and Origin check" (151) | "Host and Origin check" unexplained (web security jargon); add one phrase |
| 120 | "item 5" | refers to docs/limits.md numbering; fine |
| 126 | "Approval mode ... DESK_LATER_MODE" | "later request" is used before defined (135 defines it) |
| 131 | "hs_lead_status", "lead rotation, scoring rule, sequence" | HubSpot jargon, partly explained by "in HubSpot"; acceptable |
| 133 | "loopback address" | explained in the same sentence; fine |
| 143 | "hash mismatch", "lock file" | pip jargon; one-clause explanation suggested |
| 155 | "`versions.md`", "`contract.md`" | files exist in repo root (checked with ls) |
| 166 | "Playwright", "CodeQL-style checks" (checks not named) | "checks configured to run on pull requests" vague; name them or point to docs/tests.md (done) |
| 12 | "n8n" first use (line 12) is defined only at line 33 | add "(a workflow tool)" at line 12 |
| 5 | "webhook" first use (line 5) explained at 44 | ok, README says "explained below" |

## (3) Lines saying the repo is public or telling you to clone from GitHub
Line numbers: 50, 51, 2 (via 51 "git clone"), 143 ("need a git clone"), 174 ("fork it on GitHub"), 174 ("GitHub profile of the organisation that publishes this repository"), 9 of SECURITY.md (GitHub reference; not README). 
README lines: **50, 51, 143, 174** (also 166 "pull requests and pushes to main" implies a hosted repo).

## (4) Person names / e-mails other than the role contact line in SECURITY.md
- README.md: no person name and no e-mail address found (grep for "@" matched nothing in README).
- SECURITY.md line 9 holds "sales@hadavin.com" (the role contact; allowed). It also names the studio "hadavin" in the address; README line 174 only says "the address in SECURITY.md".
- Possible concern: SECURITY.md line 9 describes it as "reaches the author"; a sales@ mailbox on the studio domain links the repo to the studio (not a person name). Not a violation, noted.
- README names only vendors (HubSpot, Gmail, Google, n8n, Anthropic) at line 170.

## Not checked
I did not run any command from the README, did not open docs/*, contract.md, LICENSE or the tests, so every claim marked "backed by tests" is unverified. Only README.md, the ls of the repo root and a grep of SECURITY.md were read.

Rules cited: R-numbers not looked up (task is read-only reader; bible folder not available in /tmp/work). EGM skipped: read-only review. Files changed: only /tmp/work/d/out-v6.md. No head SHA (not a git repo).
