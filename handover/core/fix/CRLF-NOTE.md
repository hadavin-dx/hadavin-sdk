# Patches in this folder: the .gz files are the source of truth for CRLF patches

The repository setting `* text=auto eol=lf` rewrote the line endings of the plain `.patch`
files when they were committed. For every package below, the plain `core-fix-on-frozen-rXX.patch`
(and the delta files listed) in git is an LF copy and does NOT match the hash in `sha256-rXX.txt`.
The true CRLF bytes are stored gzipped (binary, never rewritten), next to them, as `...-crlf.patch.gz`.

Apply on a checkout whose scripts/*.ps1 are CRLF:

    gzip -dc core-fix-on-frozen-r7g-crlf.patch.gz > /tmp/r7g.patch
    sha256sum /tmp/r7g.patch          # must equal the CRLF line in sha256-r7g.txt, else STOP
    git apply --check /tmp/r7g.patch && git apply /tmp/r7g.patch

On an LF checkout use the plain `core-fix-on-frozen-r7g-lf.patch` (its committed bytes match its hash).
Whoever applies a patch checks the hash first. `.gitattributes` is a repo setting and is NOT changed.

See `COMMITTED-HASH-CHECK.md` for the table of every recorded hash against the committed bytes.
