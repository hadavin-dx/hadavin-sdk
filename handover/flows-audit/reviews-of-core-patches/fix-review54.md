# fix-review54: fixes to REVIEW.md after design review r54 (review-md-reader-r54.md): M1, m1 to m8
Only REVIEW.md (edits inside existing lines; line count still 975) and this file were written. Static work: nothing was built or run beyond the checks at the end. Every change is PROPOSAL text for the patch author, UNVERIFIED, not seen by a reviewer.

## Failures and uncertainty first
1. The new refusal phrases and the 33 new tests (bm) to (cs) are the audit's own wording and design, not taken from a source file. No append program exists; all log-host tests are CONDITIONAL (as test (t)).
2. M1 fix has a stated gap: on a host handed no matching file (ii) the case 4 re-run (check 4.10) cannot run; it then rests on the log host's refusal. A replaced or administered log host, or a thief of both keys, still gets through there. Written as remaining weakness (vi) of part (8), not hidden. Needs the lead or a second holder/second log (OL-20); not closable by text.
3. Counts are by hand plus a python check of the letter list (97 letters, in order, no gap) and the sums (97+47=144; 39+144=183). The 11 START/CONTINUE tests were not recounted by script; the 33 new tests are all refusals by construction.
4. Reviewer's other files and Z2/Z3/Z5-Z17 text were not re-read in full; only Z2 (line 645) and Z17 (line 660) sentences about case 4 were found by grep and aligned.
5. Other files outside REVIEW.md that may cite 111/150 or "Z1 64" were not searched beyond a grep under flows-audit (only REVIEW.md matched, and it keeps those as labelled history).

## LEAD DECIDES (both with AUDIT PROPOSAL default)
- r54 M1: log host runs the Z2 comparison itself plus the case 4 re-run (default), or only the re-run. Due 2026-11-18 12:00Z (17:30 IST). Default: both.
- r54 m6: may an override also start the drain and the signer. Due 2026-11-18 12:00Z (17:30 IST). Default: no.

## Per finding
- M1 (line 628, 635, 640-642): log host now COMPUTES the signature record itself, checks previous-file hash, runs the pinned Z2 classifier and refuses a loosening or succession without two distinct keys ('log host: loosening needs both keys'); case 4 gets check 4.10 (Z2 re-run when a matching file (ii) is handed in, phrase 'loosening not signed by both keys'); (8)(iv) squatting now says only a tightening (B) can be squatted; weakness (vi) added; Z2 (645) and Z17 (660) sentences aligned. Tests (bm) (bn) (bo) (bp).
- m1: tests for every listed rule: lower generation (bq), lower revocation (br), unknown type (bs), start counter (bt), delete (bu), overwrite (bv), other client secret (bw), other host secret (bx), override counter above L (by, split out of bk), reset above log (bz), reset reused nonce (ca), reset other host (cb), light profile (cc to cg), general else (ch), case 5 counter field tested before hash (ci), key separation as tables (cj to cm), plus (cs) seed missing field.
- m2: part (5) 'TWO KEYS ARE NOT TWO PEOPLE' (never call it two-person control; defences hold only while both keys are not stolen); RECORD RESET header says two keys, one person.
- m3: (k) kept as a pointer to (ad); count rule: 97 lettered entries, 96 distinct events; runs higher (a, e twice; tables x, av, cj and others).
- m4: own phrase per cause: (d) 'log host: counter is not exactly one higher'; (aw) 'log host: signature does not verify'; (ay) 'log host: seed needs both signatures'; missing field moved to (cs).
- m5: fixed purpose labels (purpose:override, first-release, seed, record-reset, release), checked before signatures; cross-use tests (cn) to (cq).
- m6: override starts ACT only; drain, signer and operator RESET refused ('override is not allowed for this process kind', test (cr)); part (7) kind (ii) sentence cross-refers; LEAD DECIDES above.
- m7: decision 6 moved into the first sitting row with 2; decision 19 moved to the second sitting with 18; the ANSWER IN THIS ORDER text changed to match.
- m8: part (6) says 'only while the log is intact and not replaced'; part (2) says plainly that no append program exists; light profile paragraph says the state-file check binds nothing on a wiped host.

## How counted
New letters bm..bz (14) and ca..cs (19) = 33, all refusals. Z1: 64 + 33 = 97 = 26+26+26+19; refusals 53 + 33 = 86; starts 11; 86 + 11 = 97. Z block 111 + 33 = 144 (97 + 5+3+2+8+13+3+3+1+2+3+1+1+2 = 144). All: 39 + 144 = 183. Distinct events one lower (143, 182). Updated in line 626 (header), 644, 692 (BATCH 54 FIGURES added before batch 53 history) and 829 (list of recounts).

## Invariants checked (commands run)
- `sed -n 5p REVIEW.md | sha256sum`: prefix e6db355c (unchanged). Line 77: prefix a3ab18f0 (unchanged; not touched).
- `python3 -I reviews-of-core-patches/count_review.py` run from reviews-of-core-patches: rows 28, Major 4, Minor 13, Nit 11, PROPOSE FIX 25, DECLINE 3.
- 40-hex ids in REVIEW.md: 0.
- `python3 -I tools/check_refs.py`: PASS 5190 references; check_names: PASS 655 rows; check_secrets: PASS 0 hits in 2994 files; check_counts: PASS 52 files / 655 nodes; `ruff format --check .`: 1119 files already formatted.
- Backup of the earlier REVIEW.md: scratchpad REVIEW.md.bak (not in the repository).
