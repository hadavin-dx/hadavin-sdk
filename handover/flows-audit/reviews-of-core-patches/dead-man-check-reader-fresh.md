# DEAD-MAN-CHECK.md (1-481) fresh stranger read (agent abd42d8c, egm-comprehension), security path, uncapped
Saved by flows-audit, condensed. Reviewer words unverified; static; ran nothing. Read whole snapshot snap-pc51 DEAD-MAN-CHECK. NOT read: other copies, README, REVIEW.md, fix reports, A-01.patch, cited b4cce5b sources (cites unchecked). 0 Blockers, 2 Majors, 11 Minors. Held: "all is well" path (184) fail-closed (failed query exit 3; empty output fails exact match); CLOCK AHEAD (71, 79); 3x60+60=240, 3x30+60=150; `?????*` limits LIMIT_S to 4 digits; 30-900 matches D2; `timeout -k 5 60` gives 65; 128+n exits; sixteen-program list matches 135; ten settings match 121, 202-211; IST conversions (104, 476, 477); password file mode 600 in 700 tmpfs folder; no secret or handle.
M1 L172-175, 220, 222, 191: if send_alert fails on exit-72 or exit-74 paths, script writes one stderr line and still exits 72/74; only 185 can exit 75; table row for 74 says "alert: yes" no caveat; fact 3 "exit 75 means that alert failed": add "(or failed, stderr only)" to rows 72, 74; reword fact 3.
M2 D8 (33), 347: default password never expires, rotation left to DBA calendar, "no interval is set here": propose default expiry or make D8 block T2.
m3 L191, 413: fact 3 and rule 4 list silent exits inconsistently (rule 4 omits 129-143; fact 3 omits 1 and 75): one list from the table.
m4 L212 cites "line 142 of the script" for PATH check (about line 25, file line 137): refer to PD_ST loop.
m5 L53 `-v limit_s=<seconds>` unquoted (redirection if pasted): write limit_s=240; `WATCHED|||<n>` (62, 93, 108, 184, 426) and `limit_s=<n> names=<n>` (111) would pipe/redirect: add "not commands" note (90, 270, 274, 362 correctly labelled).
m6 L3 program list omits psql, sed (1c), env (1b, 1c), rmdir (291), ls (338).
m7 D9 (34), 108: 60 s interval + 120 s max run + overlapping starts refused: gap about 180 s; N=5 holds: add a sentence.
m8 L197 says only id, stat, chmod, flock run before environment scrub (155); rm (154), `stat -f` (153) and `env bash` shebang via PATH also run before.
m9 L388 vs 400-401: check 3f expects `create f` on public; on Postgres 14 and older PUBLIC holds CREATE (`t`): add "t on 14 and older until D5".
m10 L41-43: "the one line that reads `WITH w(step)...('checkpoint')),`" does not match pasted line (trailing `--` comment): say "the VALUES list".
m11 L17 "Later passes (seventeen of them)" vs passes 2-22.
m12 Undefined/forward terms: "the lead", "studio head", PUBLIC (10, 400 point to README); Block 2b, check 1d, check 2, S6/S8, facts 2/8 used (55, 56, 86, 108, 180) before defined; psql exit codes 2, 3 (53) not in exit table (defined 93-94): glossary or pointers.
m13 L87 manual one-liner has no timezone, timeout, exact-output test, hard-coded limit_s=240 (admitted); healthy output only at 104: put "healthy = exactly one line `WATCHED|||4`" after 87.
