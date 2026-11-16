# Checkpoint repin9
(start) Lead order 18:44Z noted: no chmod outside lead-repin/ or /tmp copy; /home and repo are 750 root (stat printed). Plan: patch v9 via a python patch script; rules F1-F6,F10-F12; guide generated from script.

## 18:58 UTC checkpoint (v9 about 45 min in)
Lead order 18:55Z noted: heavy jobs (self-test, plants 20+) only via `sh handover/core-hardening/heavy-slot.sh <cmd>`, serial, one at a time. Load at this note: 6.48 7.26 5.89 (4 cores). Slot wait so far: none used yet (the first full self-test, 2018 passed / 1 failed, ran before the order, plain `dash`, about 8 min under load).
Done: v9 script patched (F1 bare names anywhere, F2 camel flags, F3 next-line value, F4 comparisons, F5 JSON pairs both orders, F6 fold of full-width and look-alike characters, F10 tolerance of the control-byte notice, F11 unset list + `command unset` + bash tests, pin/seed/sig/login/Terraform/k8s data). Start check 1982 cases pass. 53 new case labels; 14 do not fail on the v8 filter (regressions, listed in evidence-repin9/).
Failed: the new bash --posix xtrace machinery test (my test too strict: bash itself traces `set +x +v` once).
Next: fix that test, set SELFTEST_PLANNED, guide, plants on delivered file, signals, uid 65534 from /tmp copy.
