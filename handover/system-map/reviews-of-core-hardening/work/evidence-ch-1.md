# evidence-ch-1 (raw output, no judgement)
## (a) check_citations
Checker classes (from its source): FOUND, LINE-DRIFT (quote within 5 lines), MISMATCH (quote not found, includes line out of range), NO-FILE. It does NOT separate 'line out of range' from MISMATCH. Its regex is path:line "quote" (quote 6-120 chars), path taken as written (a bare file name, not resolved by search).
Command 1: python3 -I /home/user/hadavin-sdk/handover/system-map/tools/check_citations.py SNAP /home/user/hadavin-sdk/handover/system-map/reviews-of-core-hardening/work/cites-AUDIT.tsv CH/AUDIT-FINDINGS.md
{'NO-FILE': 19, 'MISMATCH': 7, 'LINE-DRIFT': 4, 'FOUND': 6} total 36
rc=1
Command 2: same for CH/MASTER-MAP.md -> cites-MAP.tsv
{} total 0
rc=0
Counts AUDIT (cut -f4 | sort | uniq -c): total 36, FOUND 6, LINE-DRIFT 4, MISMATCH 7, NO-FILE 19. MAP: total 0 cites matched (MASTER-MAP.md has no  path:line "quote"  cites; its cites are bare path:line).
Non-FOUND cites (file, cited path, line, status; the tsv has no finding id column; the tsv is at cites-AUDIT.tsv, row order = order in file):
AUDIT-FINDINGS.md	gate.py	63	NO-FILE
AUDIT-FINDINGS.md	tests/warden_port/test_gate.py	1	MISMATCH
AUDIT-FINDINGS.md	approvals/receiver.py	5	NO-FILE
AUDIT-FINDINGS.md	guard/egress.py	1	NO-FILE
AUDIT-FINDINGS.md	backends/factory.py	62	NO-FILE
AUDIT-FINDINGS.md	signer.py	64	NO-FILE
AUDIT-FINDINGS.md	tick.py	22	NO-FILE
AUDIT-FINDINGS.md	store/migrate.py	50	NO-FILE
AUDIT-FINDINGS.md	loop.py	41	NO-FILE
AUDIT-FINDINGS.md	evals.py	3	NO-FILE
AUDIT-FINDINGS.md	limits.py	1	NO-FILE
AUDIT-FINDINGS.md	README	91	NO-FILE
AUDIT-FINDINGS.md	handover/BRIEF-PREAMBLE-studio-2026-11-06.md	17	MISMATCH
AUDIT-FINDINGS.md	handover/demo/portal/portal-design-v2.md	234	MISMATCH
AUDIT-FINDINGS.md	.claude/rules/subagent-preamble-and-hooks.md	3	LINE-DRIFT
AUDIT-FINDINGS.md	CLAUDE.md	6	MISMATCH
AUDIT-FINDINGS.md	CHANGELOG.md	20	MISMATCH
AUDIT-FINDINGS.md	handover/CLOUD-RESUME-2026-11-06.md	12	LINE-DRIFT
AUDIT-FINDINGS.md	MACHINE-PROFILE-cloud.md	11	NO-FILE
AUDIT-FINDINGS.md	CLOUD-AUTONOMOUS-PROMPT.md	29	NO-FILE
AUDIT-FINDINGS.md	handover/CLOUD-RESUME-2026-11-06.md	3	LINE-DRIFT
AUDIT-FINDINGS.md	-2026-11-07.md	1	NO-FILE
AUDIT-FINDINGS.md	CLOUD-RESUME.md	1	NO-FILE
AUDIT-FINDINGS.md	-2026-11-09.md	2	NO-FILE
AUDIT-FINDINGS.md	-2026-11-11.md	1	NO-FILE
AUDIT-FINDINGS.md	handover/CLOUD-RESUME-2026-11-06.md	25	LINE-DRIFT
AUDIT-FINDINGS.md	CLOUD-EGM-SETUP-2026-11-12.md	6	NO-FILE
AUDIT-FINDINGS.md	registry.py	50	NO-FILE
AUDIT-FINDINGS.md	README.md	35	MISMATCH
AUDIT-FINDINGS.md	CLAUDE.md	23	MISMATCH
## (b) claims without evidence
Finding lines found: 150 (grep -E '^\*{0,2}(A|B|C|D1|D2|D3|X)-[0-9]+ \| '). Lanes A,B use bold '**A-01 | Sev |'; lanes C,D1,D2,D3,X use plain 'C-03 | Sev |' (one line per finding, table style).
Measure 1: line has any path:line (regex [\w./-]+\.\w+:\d+), by severity:
Blocker any=N 1
Blocker any=Y 4
Major any=N 13
Major any=Y 67
Nit any=N 12
Nit any=Y 53
ids with NO path:line at all:
B-01(Blocker) B-02(Major) B-03(Major) B-04(Major) B-05(Major) B-06(Major) B-07(Major) B-08(Major) B-09(Major) B-10(Major) B-11(Major) B-12(Nit) B-13(Nit) B-14(Nit) B-15(Nit) B-16(Nit) B-17(Nit) B-18(Nit) B-19(Nit) B-20(Nit) B-21(Nit) B-22(Major) D2-18(Major) D2-19(Nit) D2-21(Major) D3-22(Nit) 
Measure 2: line has checker-style path:line "quote" on the same line, by severity:
Blocker cite=N 4
Blocker cite=Y 1
Major cite=N 63
Major cite=Y 17
Nit cite=N 60
Nit cite=Y 5
ids with no checker-style cite:
A-01 A-03 A-04 A-07 A-08 A-09 A-10 A-11 A-12 A-13 A-14 A-15 A-16 A-17 A-18 A-20 A-21 A-22 A-23 A-24 A-25 B-01 B-02 B-03 B-04 B-05 B-06 B-07 B-08 B-09 B-10 B-11 B-12 B-13 B-14 B-15 B-16 B-17 B-18 B-19 B-20 B-21 B-22 C-01 C-02 C-04 C-06 C-07 C-08 C-09 C-10 C-11 C-12 C-13 C-14 C-15 C-16 C-17 C-18 C-19 C-20 C-21 C-23 C-24 C-25 C-26 D1-01 D1-02 D1-03 D1-04 D1-05 D1-06 D1-07 D1-08 D1-09 D1-10 D1-11 D1-12 D2-01 D2-02 D2-03 D2-04 D2-05 D2-06 D2-07 D2-08 D2-09 D2-10 D2-11 D2-12 D2-13 D2-14 D2-15 D2-16 D2-17 D2-18 D2-19 D2-20 D2-22 D2-23 D2-24 D3-02 D3-04 D3-06 D3-08 D3-11 D3-13 D3-15 D3-17 D3-18 D3-19 D3-21 D3-22 D3-23 D3-24 X-02 X-03 X-06 X-07 X-08 X-09 X-10 X-12 X-13 X-14 X-15 X-16 
MASTER-MAP.md: 800 lines; table rows starting '|' 473; rows starting '| M-' 190 (grep -E '^\| *(M-|[A-Z]+[0-9]*-)'); table rows with no path:line (regex above) 183; lines with a path:line "quote" 0.
Lines with verified|passed|done|confirmed and no backtick on the line (first 60):
AUDIT-FINDINGS.md: 2 9 14 17 20 21 25 29 43 56 69 84 103 136 139 223 246 313 331 339 345 445 450 453 455 456 479 482 485 486 490 521 525 527 528 535 541 584 586 
MASTER-MAP.md: 10 22 90 127 147 181 197 275 280 293 298 303 305 315 333 351 361 377 544 546 562 564 575 668 
## (c) lane x severity (grep -c on '^\*{0,2}<lane>-[0-9]+ \| <Sev>'), counted | target table
lane Blocker/Major/Nit counted: A 2/8/15; B 1/11/10; C 1/15/10; D1 0/3/9; D2 1/17/6; D3 0/12/13; X 0/14/2; total 5/80/65
target section 2 table:
## 2. Counts (builder claims, unverified; not de-duplicated by class)
| lane | Blocker | Major | Nit |
|---|---|---|---|
| A | 2 | 8 | 15 |
| B | 1 | 11 | 10 |
| C | 1 | 15 | 10 |
| D1 | 0 | 3 | 9 |
| D2 | 1 | 17 | 6 |
| D3 | 0 | 12 | 13 |
| X (findings that cross lanes) | 0 | 14 | 2 |
| total | 5 | 80 | 65 |
## (d) src files differing b4cce5b..HEAD (git diff --name-only, rc=0, 22 files). Matches by grep -F on path relative to src/hadavin_sdk/ (basename matches can include same-named files in other folders, e.g. app.py, config.py); AUDIT shows id@line or Lline for lines not starting with an id; MAP shows line numbers
src/hadavin_sdk/actions/contract.py | AUDIT: X-01@552  | MAP: 17 
src/hadavin_sdk/actions/secrets_env.py | AUDIT: X-01@552  | MAP: 23 610 705 
src/hadavin_sdk/actions/secrets_vault.py | AUDIT: C-11@395 X-09@568  | MAP: 26 611 634 719 
src/hadavin_sdk/app.py | AUDIT: L6 A-03@152 L216 L224 L226 L228 L273 L274 L276 C-23@419 C-24@421 L431 L433 L435 L537 X-04@558 X-06@562 X-08@566  | MAP: 18 33 39 120 134 138 146 188 189 208 214 262 298 299 586 590 598 599 602 609 618 705 713 774 789 797 
src/hadavin_sdk/approvals/gate.py | AUDIT: A-02@151 A-10@159 L188 D1-09@452 D2-15@478 X-05@560 X-11@572  | MAP: 30 118 470 650 651 652 750 
src/hadavin_sdk/audit/signer.py | AUDIT: X-01@552  | MAP: 41 507 606 607 745 
src/hadavin_sdk/backends/table.py | AUDIT: A-24@173 L177 L185 L294 L350 L355 C-03@379 C-09@391 C-11@395 C-12@397 C-16@405 L428 D1-02@445 L456 X-01@552 X-09@568  | MAP: 132 135 267 344 413 414 577 578 584 603 606 610 611 719 723 731 785 
src/hadavin_sdk/config.py | AUDIT: L54 L62 L96 L103 A-19@168 L294 L298 C-01@375 C-09@391 C-11@395 L433 L435 D1-01@444 D2-02@465 D2-09@472 D2-16@479 D2-17@480 D2-19@482 L488 D3-08@513 L537 X-01@552 X-09@568 X-10@570  | MAP: 12 79 135 136 208 244 264 305 436 438 441 510 524 527 530 575 606 613 651 706 719 733 734 748 797 
src/hadavin_sdk/defaults.py | AUDIT: L96 A-21@170 C-09@391 C-10@393 C-11@395 L435 D3-06@509 D3-08@513 D3-09@515 X-01@552 X-09@568  | MAP: 52 104 113 278 304 510 681 748 767 774 
src/hadavin_sdk/deferred.py | AUDIT: L6 L96 A-03@152 L354 C-08@389  | MAP: 17 18 136 183 203 274 351 581 618 
src/hadavin_sdk/guard/http.py | AUDIT: A-14@163 A-23@172 L215 C-11@395 X-09@568  | MAP: 26 48 293 629 680 719 747 
src/hadavin_sdk/guard/redact.py | AUDIT: L22 L142 A-02@151 A-11@160 L188 L333 D1-09@452 X-05@560 X-11@572 X-13@576  | MAP: 11 51 141 514 526 650 726 728 752 
src/hadavin_sdk/guard/runmap.py | AUDIT: L143 L188 X-05@560  | MAP: 11 52 446 587 650 651 699 
src/hadavin_sdk/models.py | AUDIT: L78 L245 C-01@375 C-17@407 L434 D2-05@468 X-10@570  | MAP: 102 115 247 285 689 722 734 
src/hadavin_sdk/registry.py | AUDIT: L95 L96 L294 L336 X-01@552 X-13@576  | MAP: 63 64 136 145 689 697 734 
src/hadavin_sdk/runtime/agent_loop.py | AUDIT: A-03@152 L238 C-02@377 C-05@383 C-06@385 C-07@387 X-01@552 X-02@554 X-07@564 X-10@570 X-16@582  | MAP: 146 182 580 651 689 690 691 715 716 722 725 756 
src/hadavin_sdk/stages.py | AUDIT:  | MAP: 
src/hadavin_sdk/store/migration_numbers.py | AUDIT:  | MAP: 
src/hadavin_sdk/store/postgres.py | AUDIT: L287 L310 L353  | MAP: 150 152 583 598 612 638 678 
src/hadavin_sdk/testing/__init__.py | AUDIT:  | MAP: 
src/hadavin_sdk/testing/mutation.py | AUDIT:  | MAP: 
src/hadavin_sdk/tools.py | AUDIT: L22 L96 L98 A-06@155 A-14@163 L188 L212 L215 L305 L352 L363 C-10@393 C-11@395 C-15@403 L435 L456 D3-09@515 X-01@552 X-04@558 X-09@568  | MAP: 18 47 48 100 149 162 210 216 241 275 300 301 303 326 351 355 373 379 406 625 629 651 655 656 698 729 783 
