# CRLF patches in this folder (read before applying)

The repository setting `* text=auto eol=lf` rewrites line endings of text files, so the files
`core-fix-on-frozen-r7f.patch` and `core-fix-on-frozen-r7g.patch` in this folder were turned into
LF copies when committed (for r7g they are now byte-identical to the `-lf` patch; the sha256 file
lists the original CRLF hash, which no longer matches those two files).

The real CRLF patches are stored gzip-compressed (binary, not rewritten):

    gzip -dc core-fix-on-frozen-r7g-crlf.patch.gz > core-fix-on-frozen-r7g.patch   # sha256 d819e6a0...
    gzip -dc core-fix-on-frozen-r7f-crlf.patch.gz > core-fix-on-frozen-r7f.patch   # sha256 7041492f...

Use the CRLF patch for checkouts whose scripts/*.ps1 have CRLF line endings, the `-lf` patch for LF checkouts.
Check the result against `sha256-r7g.txt` / `sha256-r7f.txt`.
