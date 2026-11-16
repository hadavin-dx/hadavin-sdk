# B-PRH-b5 repro of Issue 1 (run 2026-11-12 UTC, script B-PRH-b5-scratch/repro.py)
HAND = a made-up handed-out secret built from parts; KEY = AKIAIOSFODNN7EXAMPLE. Head d08ec151 (tree head) vs origin/main 2a8c2aac.

## head d08ec151 (BEFORE the fix)
tree: head
chars input 'a \x1bTr0ub4dor-3xyzQ ; user\x07AKIAIOSFODNN7EXAMPLE'
chars prepare_output 'a <SECRET_REDACTED> ; userAKIAIOSFODNN7EXAMPLE'
chars error_reason    'ValueError: a <SECRET_REDACTED> ; userAKIAIOSFODNN7EXAMPLE'
chars KEY readable in prepare_output: True  error_reason: True
consuming input 'a Tr0ub4dor\x1b(B\x1b[m-3xyzQ ; user\x07AKIAIOSFODNN7EXAMPLE'
consuming prepare_output 'a <SECRET_REDACTED> ; userAKIAIOSFODNN7EXAMPLE'
consuming error_reason    'ValueError: a <SECRET_REDACTED> ; userAKIAIOSFODNN7EXAMPLE'
consuming KEY readable in prepare_output: True  error_reason: True

## origin/main 2a8c2aac
tree: main
chars input 'a \x1bTr0ub4dor-3xyzQ ; user\x07AKIAIOSFODNN7EXAMPLE'
chars prepare_output 'a \x1b<SECRET_REDACTED> ; user\x07<APIKEY_1>'
chars error_reason    'ValueError: a \x1b<SECRET_REDACTED> ; user\x07<APIKEY_1>'
chars KEY readable in prepare_output: False  error_reason: False
consuming input 'a Tr0ub4dor\x1b(B\x1b[m-3xyzQ ; user\x07AKIAIOSFODNN7EXAMPLE'
consuming prepare_output 'a Tr0ub4dor\x1b(B-3xyzQ ; user\x07<APIKEY_1>'
consuming error_reason    'ValueError: a Tr0ub4dor\x1b(B-3xyzQ ; user\x07<APIKEY_1>'
consuming KEY readable in prepare_output: False  error_reason: False

Result: on head the key is readable on both paths in both variants; main masks it (main still leaks half of HAND in the consuming variant: that is the old bug PR H fixes).
