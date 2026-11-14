# Hygiene findings (poison rule audit, read-only)

Scope: every file under handover/demo/ except n8n-table-screen/ and the generated flow folders (n8n-flows, n8n-flows-v3, n8n-flows-v4 and their film/real variants). 2400 files in scope, 2006 text files scanned (394 images skipped). Nothing was edited, deleted or committed. This is the only file created.

Counts are MATCHING LINES (a line with several hits counts once), found with ripgrep and line numbers. Patterns:
- (a) a run of 40 or more letters or digits
- (b) a link, or a host name (common top-level endings, plus the word for the local machine name)
- (c) the numeric LOOPBACK address, IPv4 or IPv6 form, or the all-zero bind address
- (d) secret-shaped or address-shaped text: key prefixes, private-key headers, e-mail shapes, "password/token/key = value" shapes

## Totals

| Rule | Lines | Files | Mostly made of |
|---|---|---|---|
| (a) 40+ run | 19334 | 248 | 18041 pip hash-lock lines (64-char digests) inside patches; the rest are full commit ids, tree ids, patch digests, filler like a long row of one letter in test names |
| (b) link / host | 12395 | 477 | raw API dumps in pr-stack (about 7000), tool-output logs, patches carrying docs |
| (c) LOOPBACK numeric | 2405 | 327 | code and test logs (needed to run) plus prose in notes, reviews and doc patches |
| (d) secret / address shaped | 3325 | 368 | about 1450 are Python decorator lines matched as e-mail shapes (false positive); the rest are reserved example addresses |

No real credential was found: no cloud key ids beyond the documented dummy example, no token prefixes, no private-key headers, no JWTs. The one cloud-key-shaped string is the vendor's published dummy sample, in tools-claims/brief-r1fix2.md.

## Counts per top-level folder (a / b / c / d lines)

| Folder | a | b | c | d |
|---|---|---|---|---|
| semgrep | 15691 | 15 | 0 | 66 |
| top-level files (REPORT.md, ORDERS.md, patch at top, etc.) | 1044 | 73 | 32 | 15 |
| fixes | 1100 | 11 | 8 | 0 |
| pr-stack | 629 | 7066 | 84 | 157 |
| coverage | 402 | 13 | 0 | 0 |
| triage | 136 | 1101 | 349 | 341 |
| integration | 49 | 1349 | 429 | 508 |
| real-run | 28 | 941 | 505 | 828 |
| claims-fix | 63 | 468 | 274 | 218 |
| sonar | 49 | 458 | 231 | 440 |
| tools-claims | 15 | 338 | 140 | 130 |
| n8n-rerun | 6 | 117 | 29 | 257 |
| speed | 37 | 4 | 0 | 2 |
| pr-text | 9 | 30 | 1 | 0 |
| followup | 0 | 45 | 38 | 76 |
| xss | 9 | 6 | 6 | 67 |
| outsider + outsider2 | 10 | 101 | 98 | 41 |
| n8n-tests | 1 | 86 | 14 | 12 |
| layout | 21 | 20 | 14 | 38 |
| clean-machine | 6 | 30 | 14 | 11 |
| skips | 6 | 8 | 0 | 43 |
| stranger | 0 | 36 | 14 | 24 |
| hang | 5 | 24 | 65 | 1 |
| harness-patched | 0 | 24 | 33 | 1 |
| gitleaks | 9 | 5 | 0 | 2 |
| merge-ready | 5 | 1 | 0 | 26 |
| n8n-mainframe | 2 | 2 | 12 | 18 |
| claims-audit | 1 | 19 | 12 | 3 |
| reuse, drift, scans | 1 | 4 | 3 | 0 |

## Classification summary (by class, not line by line)

ACCEPTABLE (needed to run):
- Pip hash-lock lines in semgrep/*.patch (about 920 lines in each of about 18 patch files), fixes/, coverage/, speed/xdist-overlay-hashes.txt: the lock file needs the full digest to install.
- speed/run-demo-linux.sh:14 pinned tool digest, and sonar/nodemo-min-v2/nodemo-min-v2.patch:29: pinned download digest.
- Numeric LOOPBACK in code that needs it to run: harness-patched/lib.py.patched (lines 12, 66, 91, 113, 194), harness-patched/api.py.patched:5, harness-patched/apply_port_patch.py (16 to 26), n8n-mainframe/mf.py:11, xss/post_leads.py:22, xss/post_more.py:4, xss/run_browser.py:4, xss/overflow_probe.py:8, real-run/make_synthetic_config-q4f.py:26 (and the v6 copy), real-run/v6/drivers/run-dry-checks.sh (many lines), sonar/evidence-p2v21-bindprobe.py:17, sonar/evidence-p2optgaps-driver-fmut.py:13. About 80 code lines in all outside pr-stack and n8n folders. Test-input addresses inside evidence logs and test parameters (invalid ports, userinfo tricks, mixed-case hosts) are the same class: they are the test data.
- Clone and download lines in speed/run-sdk-linux.sh:8, speed/run-demo-linux.sh:10 and :15 (links needed by the script; they name the owner organisation, so decide whether the script itself is ever published).

FALSE POSITIVE:
- Python decorator lines matched as e-mail shapes (about 1450 lines, rule d), in patches and test logs.
- Reserved example hosts and addresses (the example, example-test and invalid names): hundreds of lines in test logs and patches.
- Filler runs: long rows of one repeated letter in test names (integration/*fullsuite*, outsider*/, tools-claims/c8/c-q.txt, xss/03-outbox.json, xss/05-browser-results.json, xss/07-outbox-subjects.txt, skips/evidence-q5-*). They are padding, not data.
- The key-like string in tools-claims/brief-r1fix2.md (vendor's published dummy sample).
- Words such as the task-name strings starting with "sk-" in real-run/results.tsv and real-run/run-dry-checks.sh (task ids, not keys).
- Long identifier in sonar/REVIEW-p2-fresh.md (a camel-case function name, 50 characters).
- Python attribute names that end like a host-name ending (a thread-local object and similar).
- Commit-trailer co-author address of the vendor's no-reply mailbox (about 92 lines, mostly in patches): public no-reply, low risk, listed for completeness.

MUST FIX before publishing (anything a viewer or publisher could see): details below.

## MUST FIX, detail (capped; classes with representative file:line)

1. pr-stack/raw-*.json (30 files, raw API dumps of the three or four PRs, their reviews and comments). About 7000 link lines (pr-stack/raw-pulls-4-comments.json alone has 4380 lines with links, 435 with 40+ runs), avatar links, user profile links, full commit ids, bot-comment text. Example lines: raw-pulls-4-comments.json (any of its 4380 link lines), raw-issues-3-comments.json, raw-pull-1.json to raw-pull-4.json (about 142 link lines each). Fix: do not publish this folder, or replace with a scrubbed summary.
2. triage/codeant-comments-lead.txt (98 link lines, 50 lines with 40+ runs, includes a third-party storage-bucket host in line 7) and triage/deepsource-comments-lead.txt (96 link lines, many badge and static-asset links). Third-party bot text pasted verbatim. Fix: summarise in own words, or exclude from publishing.
3. pr-text PR bodies (the text a publisher pastes): pr-text/github-current/pr2-body.md:63, pr3-body.md:63, pr4-body.md:62 hold a dashboard link from the review bot; every PR body, current and proposed, ends with the attribution link line (for example pr-text/github-current/pr2-body.md:9, pr-text/semgrep-pr-body-v6.md:187, pr-text/proposed/pr4-user-description-v5.md:98); pr-text/semgrep-pr-body-v2.md:7, -v4.md:9, -v5.md:9, -v6.md:9 each carry a full 64-char patch digest in the opening lines; pr-text/semgrep-pr-claims.md:3, :62, :80, :125, :130 carry full digests; pr-text/REVIEW-MAP-PR4.md:69 spells the numeric LOOPBACK address in prose. Note: the attribution link lines are mandated by the session instructions, so decide whether the poison rule or the attribution rule wins; the rest should be shortened (abbreviated digest) or reworded to the words LOOPBACK address.
4. REPORT.md (120 lines with 40+ runs, 17 lines with the numeric LOOPBACK address, 5 lines naming the studio domain). Examples: REPORT.md:1631 and :1650 (full commit, tree and patch ids), :1669 and :2189 (role address and full digest), :1894 (link). ORDERS.md:404 and :494 name the role contact address and the studio domain. Fix: abbreviate ids to 7 to 12 characters, replace the address and domain with a placeholder word.
5. Patches that carry public docs text: claims-fix/claims-all-on-f3c39cf8.patch (43 lines naming the studio domain or role address, 96 numeric LOOPBACK lines, 24 lines with 40+ runs, for example line 510 and 511 for the README studio sentence) and the per-commit copies in claims-fix/claims-series/0004, 0005, 0010 to 0019; clean-machine/0001, 0004, 0005, 0006 (docs patches with the studio domain and numeric LOOPBACK in README prose). Whether the studio domain and the role address stay is an owner decision already recorded in ORDERS.md; the numeric LOOPBACK in prose lines of these patches should become the words LOOPBACK address.

Further MUST FIX, lower priority:
- Prose (not code) uses of the numeric LOOPBACK address in notes and reviews: REPORT.md (17), real-run/REVIEW-start-prompt-fresh.md (7), claims-audit/part4-docs-settings-portal.md (6), N8N-ENV-PROBE.md (6), tools-claims/e7-adopter-dry-run.md (5), sonar/REVIEW-p2-fresh.md (5), triage/REVIEW-codeant2-sec.md (4), tools-claims/ver11-readme-commands-run.md (4), tools-claims/d10-command-output-sweep.md (4), real-run/DRY-RUN-CHECKS.md (4), claims-audit/part6-other-docs-workflows.md (4), plus about 25 more notes with 1 to 3 each (167 lines across 79 .md files in all).
- Full commit and tree ids in notes: merge-ready/evidence-m2-4-apply-and-clean-tree.txt:1, evidence-m3-4-apply-and-clean-tree.txt:1, evidence-m3-3-gates.txt:1, merge-ready/evidence-b3-5-sonar-v2-mutants-gates.txt:13 and :15 (full action pin), sonar/REVIEW-nodemo-optional-v4-partial.md:25, speed/SHA256SUMS (8 lines), integration/INT-1.md (5 lines), gitleaks/evidence-lead-provenance.txt (5 lines).
- Evidence logs holding the local working paths of the machine (33 files mention the demo-push or home-directory path): not in the four classes, but a viewer sees them.
- Evidence logs with long link lists: integration/evidence-int2b-*-fullsuite.txt and evidence-int3-*-SINGLE-PROCESS-full.txt (about 260 link lines and 75 numeric LOOPBACK lines each, all test data: reclassify as ACCEPTABLE if these logs are never published).

## What I did NOT check

- n8n-table-screen/ and all generated flow folders (excluded by instruction).
- The 394 image files (screenshots in xss/ and elsewhere): text inside images, image metadata.
- File names and folder names themselves, and file modification data.
- Binary and compiled files (a few compiled Python cache files showed up in rule d counts; not inspected).
- Obfuscated or split strings (for example a host name built by joining pieces, as in sonar/evidence-p2v21-bindprobe.py:17), encoded text (base64 shorter than 40 characters, percent-encoded or escaped forms), and secrets shorter than 40 characters with no known prefix.
- Hosts with endings not in my list (only com, org, net, io, dev, ai, local, internal, app, co, plus the local machine name were searched; other endings and bare IP addresses other than LOOPBACK were not searched).
- I did not open every hit: classification is by pattern and by sampling each class and each of the largest files, not by reading all 19000-plus lines. Counts are exact for the patterns; the class labels for the long tail are inferred.
- Semantic leaks with no pattern (personal names in prose, employer names, plan-tier or money wording, customer data in test fixtures). One note only: a person's full name is reported in tools-claims/e6-public-text-safety-sweep.md as living in a licence file outside this folder.
- Git history, other folders outside handover/demo/, and whether any given file is really going to be published.
