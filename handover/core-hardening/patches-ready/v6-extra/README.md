# FIX-id-vs-command-withheld.patch (C7b fix, pass 2 version)

What it does: stops the approval card showing `[command withheld (G4)]` instead of a Hadavin id (`<prefix>-<32 hex digits>`) when the first digits of the id happen to spell `ec2` plus one of a-f (1 id in about 10,900). One change in `src/hadavin_sdk/approvals/gate.py` (a lookahead in the cloud-cmdlet rule) and one new test file `tests/test_g4_ids_not_withheld.py` (23 tests).

sha256 of the patch (pass 2, replaces the pass 1 patch `e0386066...`):
`12e4be6f42e2f47ae254276cdcf27b1cb31b50d5fa40a1adcedde4acfeb6b9ce` (also in `FIX-id-vs-command-withheld.patch.sha256`).

Check and apply, from the root of a clean tree at base b4cce5b, or one with the v3 patches or the v5 patches already applied:

    cd v6-extra && sha256sum -c FIX-id-vs-command-withheld.patch.sha256 && cd -
    patch -p1 --dry-run -r - --no-backup-if-mismatch < <path>/v6-extra/FIX-id-vs-command-withheld.patch
    patch -p1 -r - --no-backup-if-mismatch < <path>/v6-extra/FIX-id-vs-command-withheld.patch

`-r -` and `--no-backup-if-mismatch` stop `patch` leaving `.orig` and `.rej` files. Needs the lead's independent result review (security path, no round cap). Evidence: `../v6-extra/raw-c7b-fix2/` and `../v3/REPORT-c7b-fix2.md`... see `REPORT-c7b-fix2.md` in this folder's parent for the path actually used.
