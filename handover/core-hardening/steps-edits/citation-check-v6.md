# C4b v6 citation check (condensed copy), 2026-11-16. No wrong date, weekday, time, count or exit code found; sums and Nov 2026 weekdays checked by hand (16 Mon, 18 Wed, 23 Mon, 25 Wed; 18:29Z=23:59 IST; 18:14:40Z=23:44:40 IST).
To correct in v7:
- F1 "US$180 of the US$189 testing budget": figures come from the scope sheet and FACTS (not the plan); "testing budget" wording is in neither.
- F2 L197: v6 forbids any retry before the lead says so; v3 line 98 allowed one retry. Stricter, but a changed rule not listed in v6-CHANGES.
- F3 Step 0: the 7 calls are tag-property check, owners, create, patch owner, patch lead status, read-back, delete; v6 lists 6 (omits the property check); read-back only runs if a write passed; fallback delete may use the 8th call. Source is an evidence-folder copy of hubspot_probe.py, not proven current.
- F4 exit 0 only if every line PASS or SKIPPED: a delete line "NOT NEEDED (nothing was created)" gives exit 1 without a FAIL; v6 silent.
- F6 "word plus 4 digits likely" and F7 TAKE_TAG in run settings file, F8 "rehearsal" (no input names a rehearsal; maps to the loopback re-smoke), F9 "possibly no mail" for unknown: author inferences, mark as such.
- F10 "rules 1 to 7" but 8 rules.
Not checked: current hubspot_probe.py, memory files, click paths, current prompts at code head, failed-login exit code vs run_real_check_n8n.py.
