# run.py r13 builder hand-back (condensed copy of the inline report), 2026-11-16 19:50Z
Files: run.r13.py, safety-tests.r13.sh, evidence-r13/, checkpoint-r13.md. Builder evidence only; no independent review yet.
## Failed / not done first
- Over the 60-minute box (18:26 to 19:50). After the relay it changed code again and ran the full suite twice.
- Lead decisions NOT built: start-up signal window, limit (d) (--sha mandatory), pointer file, launcher split.
- No mutation proof for the guard "--raw is / or a top-level folder" (a mutant would write into / and /tmp); covered only by T101a2 passing on r13.
- Plain --restore now clears group-write too (0664 comes back 0644 with a NOTE); plain --restore still writes execute and read bits from a forged marker (limit d).
- Child does not vouch for the file: a hostile git first on PATH at start is trusted (docstring says so).
- Builder's reading of "refuse --raw outside the state folder": refuse "." and ".." parts and fewer than two path levels.
- Slips: full run 1 failed T39 as root (1 of 476, apostrophe in the new NOTE text); mutants identity-to-name and clamp-others-only first survived, now killed; one full run stopped by itself.
- Leftovers: /tmp/chd.* (3, one holds a symlink to /), 3 toy files in / from the r12 evidence run (lead to delete), own /tmp/r13n.
- Not checked: signals as nobody, idle machine (load 3.5 to 9), independent evidence, hostile git first on PATH.
## Evidence (builder)
Full suite final head via heavy-slot: root 0 of 476 failed, uid 65534 0 of 121. New tests T100a, T101a, T101a2, T101b, T101c, T98e2, T99h fail on r12. 7 mutants killed (raw-no-toplevel not run). Controls N0-N10: 17 rows each as root and nobody, same exits. ruff check and format clean, 0 noqa, bash -n ok. Banned scan 0.
