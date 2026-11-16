# C6 review, codebase details (egm-codebase-details), condensed copy of the inline report, 2026-11-16
Tree: scratchpad c6/tree (copy of origin/cloud/flows-audit). Everything not listed below was CONFIRMED against the files.

## Wrong claims in the report
- ":36 no K3 word": run sheet line 36 does contain K3/K3B.
- "K3/K3B only on the closing card": nine lines contain K3 (:24, :32, :36, :38, :39, :41, :47, :54, :90).
- F-025 "every 20 s": v1-superseded/mf-recovery.json:7-10 shows an Every30s trigger, a 30 s sweep with a 20 s lease.

## Nits
- N2 wording: the F-003 patch applies cleanly and was never claimed applied; its only hunk is line 4; lines :24 and :90 belong to F-007.
- The F-007 "allowed on the closing card" claim is unsupported.
- N1: differences are shallow. Qualify differs only in env names; SendMail and AlertSend differ only in address constants; only CrmUpsert differs in kind.
- N3: split it. "E-mail passed to Q.qualify" (stage_server.py:54) is confirmed. "Reaches the model" is unverifiable; PLAN-4:80 says the normalised made-up e-mail.
- F-023 cite: v2 :3 also says NOT run, and :51 repeats it.
- F-011: DB_* names exist only under handover/flows-audit (plan v5:103, 272-273, 321, 550).
