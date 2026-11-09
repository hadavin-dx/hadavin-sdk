# P1d rev10 / P1d-learn rev3 / P1d-gate rev3, round 10 readiness. NOT READY: 3 Blocker, 5 Major. (Reviewer ran nothing.)
B1 Card-path rows depending on ESC/BS/CR (H11-kv,H12a-d-kv,H13-kv,H14-kv,H15c-kv,H16*-kv,C05-kv,C06-kv,SUM-1..5; mutants M20b,M51,M4): card entry runs neutralise before pass one (runmap.py:441-443; gate.py:125-136 strips 0x00-08,0B-1F,7F-9F), `_finish(ctx,r,shown)` builds residue views only from dropped(shown), r unused (P1d.md:131-135). Specify which text each view family is built from, per entry.
B2 P1d-learn B1-URLCRED (:83) cannot be fb: pass one masks `Pa**ss1234**` whole (redact.py:229); cannot kill M68c (only B1-EMAIL can).
B3 P1d-learn B1-SECRET (:81): SECRET class [^\s"';,&] includes `*` and the glued PV, so base masks it; redesign with PV separated by an excluded char. M68b killers: B1-AKIA, B1-EMAIL.
M1 fb leak oracle undefined for B1-EMAIL (:82) and H14 (:74,:110): name the oracle string (base output `anna.m**@<HOSTNAME_1>**`; H14 base shows 19/20).
M2 L-H25 on model entry (:79,:11,:31): base masks whole (SECRET class includes ESC); form in b1 must be delete_carriers(o); say card-only?
M3 fail-before harness gaps: junit has no marker values; how branch tests/p1d_api.py/fixtures reach base worktree; gate fb tests fail with DID NOT RAISE (no NEW_SURFACE prefix); class vocabulary vs table labels; marker registration string (pyproject.toml:87-90, no --strict-markers).
M4 `runmap.redact` is the function not the module (runmap.py:25): gate :45 monkeypatch target wrong; learn :32,:44 same. State import form and target.
M5 test_k5_fixes2 rewrite incomplete: max_document_bytes default fixed 30000; set evidence.max_document_bytes too (test line 99).
M6 H29b entry card vs M4 killer "model entry (no joined pass)": add model-entry variant or fix killer.
Minors: P1d:247 still lists card_withheld_text(inputs=); `_withhold` signature (:111/:114 vs :134-150); leaks() short-key definition; p1d_api imports textnorm lazily; backspace at text start; ORDER 180 (1) vs (2) H28a-b location unconfirmed.
Holds: s6 _request fix, tampered-plan test, M68/M76-M80 killers, gate hooks app.py:83,93, merge order.
Not checked: P1b textnorm, sanitise_text paths, H29b tag handling, probe rows, mutant counts, BS-0..4.
