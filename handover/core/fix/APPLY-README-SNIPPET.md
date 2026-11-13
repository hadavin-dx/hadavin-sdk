<!-- Paste into handover/core/fix/README.md. Written for the r6 patches; for r7 replace "r6" by "r7", the file count (84) and the test count (59) by the numbers that `sh apply_matrix.sh` prints for r7 ("files touched", "pytest ... passed"). Every command below is exactly what apply_matrix.sh ran in its table (cells a-crlf-plain, b-crlf-plain, c-lf-plain, and the *-iwsfix cells). Not tried on a real Windows machine. -->

## How to put the patch on the demo folder

**What this is.** A patch is a text file that lists changes to many files. The command `git apply` reads it and makes those changes in the folder you are standing in. The change itself is the same for everyone. Only one thing differs: how the end of each line is stored in your copy of the demo folder. Windows writes two invisible marks at the end of a line ("CRLF"); Linux and macOS write one ("LF"). Two small files, `scripts/reset.ps1` and `scripts/start_all.ps1` (the Windows helper scripts), keep the Windows style, so the patch must match the style of your copy. That is why there are two patch files.

**Step 1. Find out which style your copy has.** Open a terminal in the top folder of the demo (the folder that contains `scripts` and `tests`). On Windows use "Git Bash". Run:

```
for f in scripts/reset.ps1 scripts/start_all.ps1; do echo "$f lines=$(wc -l < $f) lines-with-CR=$(grep -c "$(printf '\r')" $f)"; done
```

- If the two numbers on each line are the same (for example `lines=53 lines-with-CR=53`), your copy has the Windows style. This is what you get from a zip download, from `git archive`, and from a normal `git clone` (on Windows, Linux or macOS alike: the repository itself says that `.ps1` files use the Windows style). **Use `core-fix-on-frozen-r6.patch`.**
- If `lines-with-CR` is 0 on both lines, something has already converted your files to the Linux style (some editors and some copy tools do this). **Use `core-fix-on-frozen-r6-lf.patch`.**
- Any other numbers mean the file is half and half. Stop and ask; do not apply.

**Step 2. Check, then apply.** Put the patch file in the top folder of the demo and run the two commands below with your file name. The first command only checks and changes nothing. If it prints nothing and you get no error, run the second.

```
git apply --check core-fix-on-frozen-r6.patch
git apply core-fix-on-frozen-r6.patch
```

(For the Linux-style copy write `core-fix-on-frozen-r6-lf.patch` instead.) You do not need a git repository for this; a plain unpacked folder works.

**Step 3. Check the result.**

1. Count changed files. In a git clone, `git add -N . && git diff --numstat | wc -l` must print **84**. (In an unpacked folder without `.git` there is nothing to compare; use the next two checks.)
2. Run the line check from step 1 again. The two numbers on each line must still be the same (Windows-style copy) or `lines-with-CR` must still be 0 (Linux-style copy). A half-and-half file means the apply went wrong; start again from a fresh copy.
3. Run the small test file for the scripts: `python -m pytest -q tests/test_reset_scripts.py`. It must end with **59 passed**.

**If step 2 says "patch does not apply" and names `scripts/reset.ps1` or `scripts/start_all.ps1`.** You took the wrong patch file for your style (step 1), or a tool changed your line ends in between. First try the other patch file. If that also fails, use this slower route, which tells git to ignore line-end differences and then repairs the two scripts. Use the first repair line for a Windows-style copy and the second for a Linux-style copy (the same fix was tested on every combination of copy style and patch file):

```
git apply --check --ignore-whitespace core-fix-on-frozen-r6.patch
git apply --ignore-whitespace core-fix-on-frozen-r6.patch
sed -i 's/\r*$/\r/' scripts/reset.ps1 scripts/start_all.ps1      # Windows-style copy: make every line end in CRLF
sed -i 's/\r$//' scripts/reset.ps1 scripts/start_all.ps1         # Linux-style copy: make every line end in LF
```

Run only the one `sed` line that matches your copy. Then do step 3.

**Do not** use `git apply --ignore-whitespace` alone with the wrong patch file: it reports success but leaves the two scripts half CRLF and half LF (the line check in step 3 shows it). With the right patch file it is not needed.
**Do not** use `patch -p1` instead of `git apply`: it worked only with the matching patch file and failed with the other one, so it adds nothing.

**What was tested and what was not.** The script `apply_matrix.sh` tried every combination of three copy styles (plain archive, git clone with `core.autocrlf=true`, archive converted to Linux style), two patch files and four ways of applying, on Linux, and checked: the exit code, the line ends of both scripts, the first line of both scripts, the number of changed files, and that the file contents are identical once line ends are ignored. The recommended commands above passed in all three styles. Windows itself (PowerShell, a Windows build of git) was not available and is not tested.
