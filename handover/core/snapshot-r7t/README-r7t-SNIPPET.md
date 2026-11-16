<!-- Paste into handover/core/fix/README.md for the r7t patches. Every number below comes from out/R7T/apply-matrix-r7t.txt and the test run named in R7T-RESULTS.md. Not tried on a real Windows machine. -->

## How to put the r7t patch on the demo folder (replaces the r6 text)

**What this is.** A patch is a text file that lists changes to many files; `git apply` makes those changes in the folder you stand in. The change is the same for everyone. One thing differs: how the end of each line is stored in two Windows helper scripts, `scripts/reset.ps1` and `scripts/start_all.ps1`. Windows style ends a line with two invisible marks (CRLF); Linux and macOS use one (LF). In the demo folder these two files keep the Windows style, so there are two patch files and you pick by the style of your copy.

**Step 1. Find out which style your two scripts have.** In the top folder of the demo (the one that holds `scripts` and `tests`; on Windows use Git Bash) run:

```
for f in scripts/reset.ps1 scripts/start_all.ps1; do echo "$f lines=$(wc -l < $f) lines-with-CR=$(grep -c "$(printf '\r')" $f)"; done
```

- Both lines show the same two numbers (for example `lines=84 lines-with-CR=84`): Windows style. This is what a zip download, `git archive` and a normal `git clone` give. **Use the CRLF patch.**
- `lines-with-CR=0` on both: Linux style (a tool already converted them). **Use the LF patch, and only on a copy whose two scripts are already LF.** If you have a Windows-style copy and want to use the LF patch, convert the two scripts first: `sed -i 's/\r$//' scripts/reset.ps1 scripts/start_all.ps1`. The LF patch does not apply to Windows-style scripts.
- Any other numbers: the files are half and half. Stop and ask; do not apply.

**Step 2. Check the file, then apply.**

| patch file (r7t) | for | sha256 |
|---|---|---|
| `core-fix-on-frozen-r7t-crlf.patch` | scripts in Windows style (CRLF) | `c39c3680c4ab44c48f0d75f8d99ea29ee5b040b9f5e8333ad0b0349dd2b85843` |
| `core-fix-on-frozen-r7t-lf.patch` | scripts in Linux style (LF) | `5a4ad881a8f138768667138eea5af78aea647515a9fe385b0cd03015b0c78299` |
| `core-fix-r7s-to-r7t-delta.patch` | a folder that already holds the r7s tree (12 files) | `d67bc302b5dbbb2007ff0dbbc70b96f8c0aa36edeb6d319958d6ac20bc743c20` |

Compare the hash first: `sha256sum <file>`. If it differs, stop (in the git repository the plain `.patch` files are rewritten to LF; the CRLF bytes are the `.gz` copy, see `CRLF-NOTE.md`: unpack it, then check the hash). Then, with the patch in the top folder:

```
git apply --check core-fix-on-frozen-r7t-crlf.patch
git apply core-fix-on-frozen-r7t-crlf.patch
```

(For an LF copy write `core-fix-on-frozen-r7t-lf.patch`.) The first command changes nothing; run the second only if the first printed nothing. A plain unpacked folder works; no git repository is needed.

**Step 3. Check the result (line endings first).**

1. Run the Step 1 line check again. The two numbers must still be the same on both lines (Windows-style copy) or `lines-with-CR` must still be 0 (Linux-style copy). Half and half means the apply went wrong: start again from a fresh copy.
2. Count changed files. In a git clone, `git add -N . && git diff --numstat | wc -l` must print **167**.
3. Run `python -m pytest -q tests/test_reset_scripts.py`. It must end with **67 passed**.

**If `git apply` names `scripts/reset.ps1` or `scripts/start_all.ps1`.** You took the wrong patch file for your style, or a tool changed the line ends in between. Take the other file, after converting the scripts as in Step 1 if it is the LF patch. Do not use `--ignore-whitespace` on its own: it reports success and can leave the two scripts half CRLF and half LF.

**What this text replaces.** Line 31 of `handover/core/fix/README.md` ("on a CRLF checkout use `git apply --ignore-whitespace` and then rewrite ... to all-CRLF (the patch is LF)") and the whole of `handover/core/fix/APPLY-README-SNIPPET.md` (r6 text, with 84 files and 59 tests; the r7s text of 166 files is replaced too) are superseded by this text. The r7t CRLF patch applies to a CRLF copy as it is.

**Tested and not tested.** `apply_matrix.sh` (output `apply-matrix-r7t.txt`) applied the real r7t patches to three Linux folders made from the frozen tree: two with CRLF scripts (CRLF patch) and one with scripts converted to LF by `sed` (LF patch). Result: exit code 0 each time; after the apply the CRLF folders held 84 of 84 and 101 of 101 lines with CR and equalled the r7t tree byte for byte; the LF folder held 0 CR and differed from the r7t tree only in those two scripts' line ends. Not tested: Windows itself (PowerShell, a Windows build of git).
