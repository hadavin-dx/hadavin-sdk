# README-r7u-SNIPPET.md (builder C, n5): what the lead replaces or deletes on disk in handover/

Nothing below was applied by the builder (handover/ is not edited by builders). Line numbers were read on 2026-11-14 on
the files as they are in /home/user/hadavin-sdk/handover. Grep facts are stated so the lead can see what exists.

## 1. handover/core/fix/README.md line 31 (superseded, and wrong for the current patches): DELETE the whole line

Exact line 31 now:

    Apply note: on a CRLF checkout use `git apply --ignore-whitespace` and then rewrite `scripts/reset.ps1` and `scripts/start_all.ps1` to all-CRLF (the patch is LF); a plain `git apply` fails on those two files.

Why delete: the r7t text (README-r7t-SNIPPET.md, last paragraph) says the opposite on purpose: "Do not use
`--ignore-whitespace` on its own: it reports success and can leave the two scripts half CRLF and half LF." The old
line 31 is the r6 advice. Replace it with one line that points at the current how-to:

    Apply note: for the current patches use the how-to "How to put the r7u patch on the demo folder" below (two patch files, one for Windows-style and one for Linux-style line ends); do not use `--ignore-whitespace` on its own.

(If the lead pastes README-r7t-SNIPPET.md, or its r7u successor, into this file, the replacement line can be dropped
and line 31 simply deleted.)

## 2. handover/core/fix/APPLY-README-SNIPPET.md (the r6 paste text): DELETE the whole file

It is the r6 snippet (46 lines; line 1 is a comment "Written for the r6 patches"). It is superseded by
README-r7s-SNIPPET.md and README-r7t-SNIPPET.md, which in turn are superseded by the r7u snippet. Two superseded
copies stay as history in git; none should be left in the folder a reader opens. Also delete
handover/core/fix/README-r7s-SNIPPET.md (44 lines, "for the r7s patches") once the r7t or r7u text is pasted into
README.md. Nothing else points at these files (grep "APPLY-README" in handover/core/fix/README.md: no hit).

## 3. The false F3 sentence ("no counter: check F3 already fails that run")

What exists on disk (grep -rn "check F3 already fails"):
  - handover/core/fix/R7S-RESULTS.md: NO such sentence (the line the r7t note names is not there; nothing to replace).
  - handover/core/snapshot-r7s/files/scripts/run_real_check.py:602 and .../tests/test_r7s_findings.py:155 and
    snapshot-r7s/delta-r7r-to-r7s.diff lines 46 and 671: frozen copies of the r7s code. Do NOT edit them (a snapshot
    that is edited is no longer the snapshot); the r7t and r7u snapshots hold the corrected code.
  - handover/core/review/review-r7s-lead-saved.md line 3: the review QUOTES the false text to report it. Leave it.
  - handover/core/fix/R7T-RESULTS.md lines 140 and 167 and snapshot-r7t/R7T-RESULTS.md (same lines): they quote the old
    test line as the OLD column and describe the correction. Leave line 140. Line 167: replace the clause "the lead
    replaces the sentence in R7S-RESULTS.md with: ..." by the sentence below, because there is no sentence to replace.

Replacement for line 167 (section 9, second bullet of R7T-RESULTS.md), whole bullet:

    - The false F3 text: it lived only in the r7s code docstring and test comment (`run_real_check.py` and `test_r7s_findings.py` of r7s), not in R7S-RESULTS.md; both are corrected in r7t. The true rule is: a counter that is not known is not "nothing missing": check F3 never reads the counter, so r7t fails the run itself.

(r7u changes the rule again where builder A owns it: the saved result file names counter_known and unseen. That text
is A's, not this file's.)
