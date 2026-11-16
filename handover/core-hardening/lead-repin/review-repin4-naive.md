# Re-pin guide v4: naive reader pass (condensed copy of the inline report), 2026-11-16
Verdict: NO. An outside reader could not decide pass or stop without guessing. Nothing was checked against the real program.
## Blockers (6)
1. No pass/stop rule anywhere. "Expected shape" says what to look for; "pass" is never defined; "stop" appears only as defaults like "no run".
2. "Not shown: the lead decides", but the reader is the lead; no output maps to YES/NO for G1.
3. Two sources conflict on whether a delete path exists; guide says "I cannot tell" and gives no criterion; hits on delet/remov/clean also match harmless words.
4. Q27 c needs MODEL_DIR, empty by default; hand-paste commands for the model side have no path; reader not told the model folder is absent from this checkout.
5. Hand-typed commands use guessed `scripts/...` paths; a wrong path gives zero hits, and nothing says how to tell wrong path from true zero.
6. Tested only on a made-up folder as root; no instruction for when real output differs.
## Majors (8)
7 Terms used before explained or with two meanings (final head, G/Q/R codes, take, model program, stage, window, marker, lease, decision 2, block, work folder). 8 Work folder location and delete step unclear; no next action for exit 2, 3, 4, 129-143. 9 `qs_37` test has no command; MODEL_SETTINGS read could print a settings file. 10 Masking is a safety net: short secrets under 24 chars with unknown names are not hidden; no "review before pasting" and no destination. 11 "299 passed" cites evidence not in scope. 12 Q25/Q27 "shown" reading is the builder's own. 13 GNU sed need unclear; WSL/macOS untested. 14 Block table rows are not commands and give no expected output.
## Nits: version labels blur (v4 vs v2/v5/v21); timezone of reader clock unsaid; masked-names paragraph too long; canary not shown as a stop signal in a quick start; no 3-step quick start at the top.
## Trust risks: exit 0 read as success; grep hit counted as "shown"; zero hits can mean wrong word, unreadable file, file deeper than 4 parts, or skipped tests folder; masking can hide a needed value or leak a short one.
Rule cited: preamble wording rules. Next step: v5 fix pass (batch with the security design review and the evidence runner when they land).
