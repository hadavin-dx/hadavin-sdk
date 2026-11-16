#!/bin/bash
# v10: bash copy-test-v10.sh. Same one-line paste as the plan step 4b (snippet-run-v10.sh checks the line equals the plan text). Made-up files only, in a mktemp dir.
S=$(mktemp -d); trap 'rm -rf "$S"' EXIT
copy_line() { if [ -e "$OUT_COPY" ] || [ -L "$OUT_COPY" ]; then echo "OUT_COPY exists: STOP, nothing copied"; else COPY_OK=0; if mkdir "$OUT_COPY"; then COPY_OK=1; for f in "$OUT" "$OUT".attempt*; do [ -e "$f" ] || continue; cp "$f" "$OUT_COPY/" && cmp "$f" "$OUT_COPY/$(basename "$f")" || COPY_OK=0; done; fi; if [ "$COPY_OK" = 1 ]; then echo "copy ok: $(ls "$OUT_COPY" | wc -l) files"; else echo "COPY FAILED: STOP"; fi; fi; }
OUT=$S/list.tsv; OUT_COPY=$S/safe
printf 'k-a\t1\nk-b\t2\n' > $OUT; printf 'k-c\t3\n' > $OUT.attempt1; printf 'k-d\t4\n' > $OUT.attempt2
echo "=== 1 OUT plus two attempt files: all three copied (expected: copy ok: 3 files)"; copy_line; ls $OUT_COPY
for f in list.tsv list.tsv.attempt1 list.tsv.attempt2; do cmp $S/$f $OUT_COPY/$f && echo "same: $f"; done
echo "=== 2 second run refuses"; copy_line
echo "=== 3 OUT only, no attempt files (expected: copy ok: 1 files)"; OUT=$S/only.tsv; OUT_COPY=$S/safe2; printf 'k-x\t1\n' > $OUT; copy_line
echo "=== 4 copy folder cannot be made (parent missing): must not print copy ok"; OUT_COPY=$S/nope/dir; copy_line
echo "=== 5 a copy fails half way (a fake cp that fails for the attempt file): must print COPY FAILED"
FK=$S/fakecp; mkdir $FK; printf '#!/bin/sh\ncase "$1" in *attempt*) exit 1;; esac\nexec /bin/cp "$@"\n' > $FK/cp; chmod +x $FK/cp
OUT=$S/half.tsv; OUT_COPY=$S/safe3; printf 'k-y\t1\n' > $OUT; printf 'k-z\t2\n' > $OUT.attempt1; PATH=$FK:$PATH copy_line
echo "=== 6 after the failure the same line refuses (copy folder exists): the lead removes the half copy by hand and reruns"; copy_line
