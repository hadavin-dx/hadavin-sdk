# Probe v3 (PR #8) and writes2 (PR #9): Sonar result mapped by FUNCTION (session lead, 06:15Z)

Source: the lead's raw lists in ORDERS.md (06:10Z). Lines shifted by the probe patch: I applied probe-ab-v3.patch and probe-ab-v3-writes2-full.patch on db54e13 and read the sink line of every open line (so the mapping below is read from the code, not guessed).

| # | function (base line) | shape | PR #8 (v3) | PR #9 (writes2) |
|---|---|---|---|---|
| 1 | check_invariants.read_jsonl (63) | helper `confine_existing`, env roots, returns a (root, relative) pair | VANISHED | VANISHED |
| 2 | check_invariants.read_crm (82) | INLINE guard, `Path(real).read_text` | **STAYED** (open at 112: `json.loads(Path(real).read_text(...))`) | **STAYED** (112) |
| 3 | check_invariants.read_book (96) S8706 | UNTOUCHED control | open (126) as expected | open (126) |
| 4 | check_invariants._intended (597) | helper `confine` (existing or NEW name via dict table) | VANISHED | VANISHED |
| 5 | check_invariants._facts_say_live (605) | helper `confine_existing_fixed` (constant roots, no env read) | VANISHED | VANISHED |
| 6 | check_invariants._drain_marker (614) | NAME-ONLY (basename joined onto a constant folder) | VANISHED | VANISHED |
| 7 | load_driver.run facts_path write (366) | v3: helper `confine`, DICT table for the new name; writes2: INLINE guard + `Path(real_facts).write_text` | VANISHED | **STAYED** (open at 379: `Path(real_facts).write_text(...)`) |
| 8 | load_driver.run log write (377) | helper `confine_iter`, ITERATION over a constant | VANISHED | VANISHED |
| 9 | scrub.main read (178) | helper `confine_existing` (sys.argv family replicate of #1) | VANISHED | VANISHED |
| 10 | scrub.main write (179) | v3: INLINE guard + `Path(real).write_text`; writes2: helper | **STAYED** (open at 198: `Path(real).write_text(...)`) | VANISHED |
| 11 | n8n_api.main import (192) | INLINE guard, `Path(real).read_text` (sys.argv family) | **STAYED** (open at 206) | **STAYED** (206) |
| 12 | run_real_check.load_env (645) | UNTOUCHED control | open as expected | open as expected |
| 13 | NEW `_probe_index_read` (index helper, no returned pair, own internals) | no issue appeared | no issue | no issue |
| 14 | NEW `_probe_control` (equality allow-list, then use) | no issue appeared | no issue | no issue |
| (feed.py:49 S8703) | untouched | open as expected (control, not a path issue) | open | open |

No new issue appeared in tools/pathconfine.py or at any helper's internal call (M4 rule: the sink did NOT move): so a vanished site is a real clear, not a sink moved into the helper.

## Reading, pair by pair (the note's rules)
- **T (#13 vs #1):** both gone: the shared (root, relative) tuple is NOT the cause; the helper shape is accepted for reads.
- **A (#1 vs #4):** both gone: ONE combined helper (existing or new-name branch) is fine for reads.
- **B (#1 vs #5):** both gone: the ENVIRONMENT read (LEAD_DESK_PATH_ROOTS) is NOT a cause: keep it.
- **C (#7 vs #8):** both gone: the dict table and the iteration are BOTH accepted for new output names (take the dict form: simpler).
- **E (#1 vs #2):** #1 gone, #2 STAYED: **the HELPER is accepted, the INLINE guard (realpath + commonpath + raise + Path(real).read_text) is NOT**, for reads. (n8n_api #11 inline stayed in the sys.argv family too: consistent.)
- **D / writes2 (#7 swapped to inline, #10 swapped to helper):** inline write STAYED (#10 in v3, #7 in writes2); helper write VANISHED (#7 in v3, #10 in writes2): **the same law for WRITES: helper accepted, inline refused; the swap on the same site flips the result: the cleanest evidence in the probe.**
- **F (#6 name-only):** vanished too: a name-only contract is accepted, but it is NOT needed (the helper already clears everything it was applied to).
- **Replicates:** #9 (helper, sys.argv) agrees with #1; #11 and #10 (inline, sys.argv) agree with #2 and #7 (inline): source kind (argparse vs sys.argv) does not matter; no disagreement.
- **Positive control #14:** no issue appeared (an equality allow-list is accepted OR not analysed; the negative controls prove the engine ran).
- **Controls #3, #12, feed 49:** open as expected in both: the run is VALID (no control vanished).

## P3 FINAL design (smallest shape that clears the most sites)
Use the HELPER at EVERY site (reads and writes). Do NOT use the inline guard anywhere. The simplest accepted helper (probe #1/#4/#7's `confine` family: listing-based lookup returning the listing's own path, environment roots allowed, dict-table new-name rebuild) is enough: no need for the index variant, the iteration variant, the constant-roots variant or the name-only contract. That clears 10 of the 13 baseline sites with evidence (63, 597, 605, 614, 366, 377, 178, 179 by helper; 82 and 192 are the inline ones the final design MOVES to the helper, same shape as the proven ones: expected to clear, not yet measured at those two sites).
## Sites that stay open or are NOT measured by the probe
- check_invariants.read_book S8706 (126): untouched control in both probes: NOT measured: final design = confine the book path with the helper and build the read-only URI from the helper's return value (the shape proven for reads); expected to clear; measured only by the final patch.
- run_real_check.load_env S8707 (645): untouched control: NOT measured: the `--config` site needs the helper in an `anywhere` mode (the documented real run keeps the config outside the repo): the final design implements `anywhere` as the same listing lookup started at the filesystem root (os.path.splitroot), returning the listing's own path, with NO fallback to the raw argument and no containment test (this also closes the Windows UNC/mapped-drive Major of the P3 v3 review): same helper shape, expected to clear; measured only by the final patch.
- feed.py:49 S8703 (not a path issue): P2's OPTIONAL feed patch (drops `--url`): odds ~75% (judgement).
Anything still open after the final patch is for YOUR ruling (suppress with a reason in the Sonar UI, no code comment): the candidates are only those three sites.
