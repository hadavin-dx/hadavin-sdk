# v7 changes (lead re-pin script and guide), 16 Nov 2026

Builder note (evidence side plus the v7 fixes the coordinator asked for). Script: `lead-repin-verify.v7.sh`. Guide: `LEAD-REPIN-VERIFY.v7.md`. The v6 script is unchanged and still the file `lead-repin-verify.sh` (sha256 in `evidence-repin7/10-sha256.txt`). I did NOT overwrite `lead-repin-verify.sh` or `LEAD-REPIN-VERIFY.md`: an attempt to copy v7 over `lead-repin-verify.sh` was refused by the permission system, and I did not work around it. The lead promotes v7 with `cp` after the review. The EGM result review is the lead's step; this builder did not run it.

## Failures and gaps first
See `evidence-repin7/00-RESULTS.md` (written last, with the raw files).

## Finding -> fix -> test (security review of v6, `review-repin6-security.md`)
| Review item | Class | Fix in v7 | New self-test cases (each fails on the v6 filter) |
|---|---|---|---|
| M1 | names inside escaped quotes, JSON key with a unicode escape | three rules (`${BQ}` = backslash + quote): escaped name with string value, with plain value, key containing a `\uXXXX` escape | 4 cases |
| M2 | password flag position and value limits | shape rule now accepts a command after `&&`, `;`, `|`, `(`, `$(`, after `NAME=value`, with a path; value may be a quoted text with spaces; extra rule for an indented `-p VALUE` continuation line. Limits stated in the guide | 7 cases |
| M3 | recognised name that does not hide | glued names (`DBPASS`, `ROOTPW`, `requirepass`, `masterauth`, `jsessionid`), XML text, value starting with `<`, `password == "x"` (not `token`), `:=` (rule placed first, because an earlier rule ate the colon), SQL `IDENTIFIED BY`, second text after a hidden one, closing bracket inside a mid-line value | 13 cases |
| M4 | git settings of the folder | `-c log.showSignature=false -c gpg.program=/bin/false -c core.hooksPath=/dev/null` added to the one git function `g()`; header and guide updated | 1 machinery case with a fake `git` that records its arguments |
| M5 | user-info forms | user part of 4 or more characters after `://`; escaped slashes; `user:pw@host` without a scheme | 4 cases |
| M6 | evidence | rerun in `evidence-repin7/` (list below) | |
| minors | Bearer with `$ ! #` and short Bearer values; `| sudo -S`, `| kinit`, `| ssh-add`; relative TMPDIR refused; time limit must be a whole number and the watchdog ends when the run is gone; two wrong comments fixed (stop keeps no masked copy; `unset ENV` scope); guide: hand commands, hash of the script, exit-code line, v4 citation marked as not re-run, longer list of what can still show | cases for Bearer, pipes, TMPDIR |
| found by me | the self-test removed `git.pid` after starting the run (a race that failed once under load, both shells) | removed before the run starts | the self-test itself |

Not done in v7 (stated, with reason): minor 4 (`kill_tree` without `ps`: the run falls back to the background process only; a /proc fallback needs a Linux-only code path and was not written in the time box); minor 8 (fixed second limits in the self-test, not widened; no large-tree timing).
