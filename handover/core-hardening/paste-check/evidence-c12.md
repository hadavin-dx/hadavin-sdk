# evidence-c12 (raw outputs only; nothing else was run)
$ bash -n on all 45 bash blocks: 0 bad (see run above; re-run below)
45 blocks 0 syntax errors
$ sha256sum
ede7e96e2f4d6737cb6baf59720bd3108dad346f5252f0d2fa8a476c8a844849  LEAD-CHECKLIST-v5.md
da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca  LEAD-FILL-list-v5.md
da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca  LEAD-FILL-list-v5.rev11.md
$ cmp fill vs rev11
identical
$ grep -n -o "kill exit=3(\[^0-9\]|\$)" checklist
287:kill exit=3([^0-9]|$)
$ grep -c "GONE-FAIL|kill exit=3" (old pattern)
0
$ grep -n -o "head=\$PIN\|C4 mismatch\|return \$e\|aside\" command" ...
69:git grep failed
69:return $e;
249:head=$PIN
249:C4 mismatch
$ diff line counts
   352 LEAD-CHECKLIST-v5.md
   350 LEAD-CHECKLIST-v5.rev11.md
   702 total
38
