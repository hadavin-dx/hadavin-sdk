# Design only: the ONE fixed pointer file for run.py (round 11, NOT implemented)

Status: design for the lead to decide. No code was written for it. The lead's yes covered "one fixed pointer file in the state
folder, written once, never read by a second tool", with no details; this page answers the seven requirements of review r10
(section "The ONE fixed pointer file") and ends with the questions only the lead can answer.

## What problem it would close (the only one)
A normal run keeps its marker (which file holds a planted change, plus the saved original) in a state folder under TMPDIR. A
later `--restore` looks in the usual places (/tmp, /var/tmp, /dev/shm, TMP, TEMP and the current TMPDIR). If the killed run had a
TMPDIR somewhere else, `--restore` does not see its marker: plain `--restore` exits 2 ("files unknown"), `--restore --sha`
compares the files with git and still works (r9 M1). So the pointer closes one gap: "the marker lives in a place nobody
searches". It closes none of the r9 findings and NOT limit (d): a person or program that can write the state folder as this user
can edit the pointer as easily as the marker. The real fix for limit (d) is the owner proposal at the end.

## The wording problem first
"In the state folder" cannot work as said: the state folder is the thing that is not found. The pointer has to live where
`--restore` looks WITHOUT knowing TMPDIR. Proposal below: a FIXED folder, `/var/tmp/hadavin-mutation-lane-<uid>/pointers/` (the
fixed state folder that is already searched), one small file per root. Question 1 asks the lead to confirm that reading.

## The seven requirements

1. Path, owner, mode, writing, links.
   - Path: `<fixed folder>/pointers/<key>.pointer.json`, where `<key>` is the same hash of the resolved root that names the marker.
     The folder `pointers/` is created with mode 700, owned by the running user, checked with the same `ensure_state` rules
     (not a link, owner is us, mode exactly 700; a wrong mode is refused, never repaired silently).
   - The file: mode 600, owned by us. Written with a temporary name in the same folder (O_CREAT|O_EXCL|O_NOFOLLOW, mode 600), data
     synced, `rename` into place, the folder synced (the same `write_state` helper the marker already uses). Never opened through
     a link (O_NOFOLLOW on the file, the folder checked with lstat first).
2. Content (no secret, no test output, no file text): a JSON object with exactly these keys, all checked on read:
   `format` (the number 1), `key` (the marker key), `root` (resolved root text), `root_dev` and `root_ino` (device and inode of
   the folder, as the marker records), `state_folder` (absolute path of the folder that holds the marker and backup),
   `written_at` (whole seconds, UTC), `writer_pid` and `writer_start_ticks` (to tell a live run from a dead one). Nothing else is
   read; an unknown key makes the file invalid.
3. Two roots at once. One file PER ROOT (named by the key), so two roots never overwrite each other. Two runs on ONE root are
   already refused by the lock, so the second one never reaches the write. "Written once" means: created by the first run that
   plants into that root, never edited; replaced only by a new run after the old file was removed by a good restore. A file that
   already exists and names ANOTHER state folder is not overwritten: the new run refuses (exit 2) and says which pointer is left.
4. Validation on read: the same checks as `ensure_state` (folder 700, ours, not a link; file regular, one name, mode 600, ours,
   size under 4 KiB), strict JSON (no duplicate keys, no extra keys), `key` equals the key computed from the root now given,
   `root` equals the resolved root now given, `state_folder` is absolute, has no `..`, is a directory we own with mode 700 and
   the right name (`hadavin-mutation-lane-<uid>`), is not a link. Any failed check: the pointer is NOT usable and is reported by
   name (never silently skipped).
5. Staleness. The pointer is removed in the same step that removes the marker (good restore, good `--discard-marker`), after
   the marker. A pointer whose state folder holds no marker is stale: `--restore` removes it and says so. Order of writing:
   pointer FIRST, marker second, so a pointer without marker is the only possible half state, and it is harmless. A pointer older
   than N days with no marker is reported (question 5).
6. Exit 3 when unreadable and a marker exists. If `--restore` finds a pointer it cannot validate, and ANY marker for this root is
   known (in a searched place), the exit is 3 (a mutant may be planted), never 0 or 2. If the pointer is unreadable and no marker
   is known anywhere, the result stays 2 (unknown), with a text that names the pointer file and says what was not checked. This is
   the same rule as for a damaged marker today (r6 M1, r7 M1).
7. Tests that fail on old code (proposed, none written; each also runs as user nobody):
   - kill a run whose TMPDIR is outside every searched place; run plain `--restore` with a different TMPDIR: restores (exit 0,
     original text back). Old code: exit 2, file still planted.
   - the same with `--restore --sha`: unchanged (exit 0), proving the pointer is not needed for the safe path (a GUARD).
   - pointer forged to name a state folder owned by someone else, a link, mode 755, or with an extra key: each refused, nothing
     written (these are GUARDS: old code has no pointer, so they pass there by design; labelled so).
   - pointer present, marker removed by hand: `--restore` removes the stale pointer, exit 2 with the text.
   - pointer unreadable (garbage) with a marker in /tmp: exit 3.
   - two roots at once: two pointers, each restore uses its own.
   - mutation check: remove the key-equality check, the owner check, the mode check, the link check, one by one; each removal
     must fail at least one test (proof the tests test the checks).

## What it does NOT change (stated so nobody over-reads it)
- A same-user forger can write a pointer, a marker and a matching backup. Plain `--restore` would still trust them (limit (d)).
- It adds one more state file that is read, so one more input an attacker can try to forge, and more code and tests to keep right.
  That is why the design reads it only to FIND a marker, then applies every existing marker check unchanged.
- It does not help when the TMPDIR folder is gone (the marker is gone too).

## Questions for the lead (exact)
1. Location: is a fixed folder under /var/tmp (already searched) acceptable, given "in the state folder" cannot be found without
   TMPDIR? Or another fixed place (for example a per-user folder under the home directory)? /var/tmp is shared, sticky and swept
   by some systems; a home folder is not.
2. "Never read by a second tool": does that mean only `run.py --restore` reads it (no shell script, no other module)? If yes, how
   does a person find the marker by hand when `run.py` is broken: is the printed text enough?
3. Which finding is it for? The only one it can close is the "TMPDIR outside the searched places" gap. If the lead meant limit (d),
   it does not help: say so now.
4. Pointer first and marker second (my proposal), or the other order? It changes which half state is possible.
5. Staleness limit N days: report only, or remove automatically?
6. Is the owner proposal below preferred instead? It closes limit (d) and the TMPDIR gap together with less code.

## Owner proposal (not implemented), ranked above the pointer by review r10
Make `--sha COMMIT` mandatory for `--restore` (plain `--restore` refused with exit 2 and a text that says how to find the commit).
Effects: no trust in the state folder at all (limit (d) closed by default); the TMPDIR gap closes too, because the files are
compared with git whatever the marker says. Cost: an operator without the commit cannot restore, and every test that uses plain
`--restore` (about 40 checks in T52-T99) needs `--sha`; the tests of the marker-only path become tests of the refusal. Smaller
alternative: keep plain `--restore` but require an explicit flag `--trust-state-folder` ("I know the folder may be forged").
I did NOT implement either: it changes the meaning of the tool for everyone and needs the owner's yes.
