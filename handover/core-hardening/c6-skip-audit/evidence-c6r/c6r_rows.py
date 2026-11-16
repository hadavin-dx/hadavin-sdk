# c6r row-level edits. exec()d by build_c6r.py inside its namespace, after the c6q row edits and before the counts of section 3b are made.
WAITS = "NOT APPLIED; waits for the answer of L-SAVEERR (default no)"


def why_add(k, txt):
    g = getrow(k)
    g[COL["why"]] = g[COL["why"]].rstrip() + " " + txt
    putrow(k, g)


# ---- M-E: failed-run saving waits for the owner's yes (rows that set the failed-run setting)
for k in (53, 55, 62, 64, 66, 68):
    rset(k, "st", WAITS)
    why_add(k, "c6r: this row sets the saving of FAILED runs, which the owner's words do not cover (c6q design review M-E); it waits for the owner's yes and is not applied under 'apply all defaults'.")
# rows that mention both settings are cut back to successful runs
rsub(44, "new", "n8n saves the data of every run (the setting for successful runs and the setting for failed runs are both on), so n8n keeps the made-up name and e-mail of the contact, and everything the nodes pass on, in its own database;",
     "n8n saves the data of every successful run (the setting for successful runs is on; the setting for failed runs stays off until the owner has said yes to it), so n8n is expected to keep the made-up name and e-mail of the contact, and everything the nodes pass on, in its own database for those runs;")
rsub(51, "new", "the take saves every run,", "the take saves every successful run,")
rsub(52, "new", "With these settings n8n keeps run data for every run until its pruning removes it,", "With these settings n8n is expected to keep run data for every saved run until its pruning removes it (whether and when it does depends on the n8n version and its settings and has not been checked),")
rsub(52, "new", "saveDataSuccessExecution all, saveDataErrorExecution all and saveManualExecutions false; this is right whichever setting n8n lets win.",
     "saveDataSuccessExecution all and saveManualExecutions false (saveDataErrorExecution stays none until the owner has said yes to saving failed runs; then it is set to all as well); this is right whichever setting n8n lets win.")
rsub(50, "new", "DO reach n8n's database through the webhook request body until n8n's automatic removal of old runs (pruning) removes the run, if it ever does. For the take, saving is set to all, so n8n also keeps the data every node passes on.",
     "are expected to reach n8n's database through the webhook request body (the leak scan shows whether they do) and to stay there until n8n's automatic removal of old runs (pruning) removes the run; whether and when it does depends on the n8n version and its settings and has not been checked. For the take, saving of successful runs is set to all, so n8n also keeps the data every node passes on for those runs.")
rsub(57, "new", "for the take two of them are set to all (the owner's choice as recorded in the plan of the re-smoke; the studio lead has not yet confirmed it), so the execution list in scenes 1 and 2 shows runs",
     "for the take one of them, the one for successful runs, is set to all (the owner approved saving successful runs; the one for failed runs stays none until he says yes to it), so the execution list in scenes 1 and 2 shows the successful runs")
rset(57, "view", "Start notes: the take saves every successful run, so the execution list shows runs.")
rsub(92, "new", '"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all"', '"saveDataSuccessExecution": "all", "saveDataErrorExecution": "none"')
rset(92, "view", "Scenes 1 and 2: the generated flow files save every successful run.")
why_add(92, "c6r: only the successful-run setting changes; the failed-run setting stays none until the owner has said yes, and then this row is re-issued together with rows 62, 64, 66 and 68 (c6q design review M-E).")
rsub(23, "why", "and the take saves every run,", "and the take saves every successful run,")
rsub(14, "why", "it is true whether saving is all or none, because the request body reaches n8n's database in both cases (N8N-START.md lines 44 to 46);",
     "it is expected to be true whether saving is all or none, because the request body is expected to reach n8n's database in both cases (a relayed search of one run, not measured; the leak scan shows it; N8N-START.md lines 44 to 46);")

# ---- minors: report voice in file text
rsub(40, "new", "(read by the audit on the branch cloud/core-hardening;", "(read on the branch cloud/core-hardening;")
rsub(48, "new", "the audit read their lane3 results table (RESULTS.md, lines 89 to 92, in handover/core-hardening/c6-skip-audit/raw-lane3/ on the branch cloud/core-hardening, not on the demo branch that holds this file).",
     "their lane3 results table was read (RESULTS.md, lines 89 to 92, in handover/core-hardening/c6-skip-audit/raw-lane3/ on the branch cloud/core-hardening, not on the demo branch that holds this file).")
rsub(49, "new", "its path comes from the take's config and this audit did not find it, so the builder names it", "its path comes from the take's config, so the builder names it")

# ---- row 15 is NOT widened: the card row's time cell ("30 s EST", run sheet line 41) is a separate table cell, and no row edits a cell border
# ---- row 11 viewer cell
rset(11, "view", "Nothing on screen; the run sheet's total for the one video changes to 150 s for scenes 1 to 4 plus an estimated 40 s for the closing card (about 190 s in all, not measured; the run sheet had 30 s for the card, about 180 s in all).")

# ---- row 6 (rehearsal list)
rsub(6, "new", "unless the owner has confirmed that. (The search", "unless the owner has confirmed that. The made-up e-mail domain and the name marker by which the sheet tells the owner to find leftover contacts must be exactly the ones the studio lead writes in item 11 of the list \"Risks the owner must see\"; if they differ, or the sheet names none, no deletion instruction is given and the sheet is corrected first. (The search")
rsub(6, "new", "This item applies as soon as the four real-v5 flow files, or n8n's two settings, save every run;", "This item applies as soon as the four real-v5 flow files, or n8n's saving settings, save runs;")
rsub(6, "new", "From then on n8n saves every run, so a secret", "From then on n8n saves runs (successful runs, and failed runs too if the owner has said yes to that), so a secret")
rsub(6, "new", '"leak scan for saved runs passed: pass lines met on the loopback stand-ins"', '"leak scan for saved runs passed on the loopback stand-ins: every pass line of the section \'T7b for the take\' in the start notes N8N-START.md is met"')
rsub(6, "new", "each read from the file or store that holds the keys and handed to the search without ever being printed or saved;",
     "each read from the key store and handed to the search through a pattern file that exists only in memory or through standard input, never on a command line (a command line shows in the list of running programs and in the shell history) and never saved to disk;")
rsub(6, "new", "Any hit in a store other than n8n's own database stops the take; a hit inside n8n's own database is written down and the studio lead decides in writing whether the take goes on.",
     "Any hit for a made-up name or address in a store other than n8n's own database stops the take; a hit for a made-up name or address inside n8n's own database is written down and the studio lead decides in writing whether the take goes on. ANY hit for a real key value, in any store including n8n's own database, means: the studio lead cancels or replaces that key at once with its provider, treats every run made with it as compromised, and the take does not start until the new key and a clean scan are written under this item.")
rsub(6, "new", "tells the owner and decides in writing how n8n's database is removed. Until", "tells the owner and decides in writing how n8n's database is removed. This third scan also searches for the real key values, in the same way as in item 15 (deleting may only mark runs, so a real key could still sit in the database); a hit for a real key value means the same as in item 15: cancel or replace the key and treat the runs as compromised. Until")
rsub(6, "new", "turns saving off again (both n8n settings and the flow-file settings back to none)", "turns saving off again (every n8n saving setting that was turned on and the flow-file settings back to none)")
why_add(6, "c6r changes (c6q design review M-D, minors; c6q naive review): item 15 says how the real key reaches the search (a pattern file in memory or standard input from the key store, never a command line, never saved to disk) and what a hit for a real key means (cancel or replace the key, treat the runs as compromised); item 16 repeats the real-key search because deleting may only mark runs; item 12 checks that the sheet's made-up domain and marker equal the ones of the risks list item 11 before any deletion instruction; item 14 points to the pass lines by name instead of saying 'pass lines met'; the saving wording no longer says that failed runs are saved (they wait for the owner's yes).")

# ---- row 8 (risks list)
rsub(8, "new", "STOP: no take on Mon 23 Nov 2026 (the target take is Wed 18 Nov 2026; the latest start on Mon 23 Nov is 18:04 UTC = 23:34 IST, a plan fact of the studio lead that moves if the seconds the take program needs, which he reads at the re-pin, differ; the owner cancels the key by 18:19 UTC = 23:49 IST)",
     "STOP for any take on Mon 23 Nov 2026 (the owner has not yet said what (a), (b) and (c) must show, so this sheet applies the strictest reading: all three; this sentence does not block the target take on Wed 18 Nov 2026, which is blocked only by the entries of this list that are not yet written; the latest start on Mon 23 Nov is 18:04 UTC = 23:34 IST, a plan fact of the studio lead that moves if the seconds the take program needs, which he reads at the re-pin, differ; the owner cancels the key by 18:19 UTC = 23:49 IST, 15 minutes after the latest start, so the studio lead writes the run length of the take program here at the re-pin and a run longer than 15 minutes is not started that day)")
rsub(8, "new", "If the closing card or the scene 3 caption says that a second send is never processed again, one rehearsal repeat sent more than 45 seconds after the first is also written here and its reply shows the repeat flag true; if it says the claim holds only within 45 seconds of the first send, item 13 of the rehearsal list applies. There is no exit:",
     "Whenever card line 1 or the scene 3 caption carries the plain statement that a second send is processed once (it does under the default), one rehearsal repeat sent more than 45 seconds after the first send is also written here, and its reply shows the repeat flag true, so that the statement without a time limit is tested and not assumed; if the card or the caption says instead that the claim holds only within 45 seconds of the first send, item 13 of the rehearsal list applies as well. APPROVAL: card line 1 and the scene 3 caption are not filmed until the studio lead has written here 'lease wording approved' with the date and time in UTC and IST; this is his own decision about the words 'processed once' beside a crash scene, because a contact whose first run crashed is claimed again by the recovery flow, up to three tries in total. There is no exit:")
rsub(8, "why", "row 6 adds items 11 to 14 to the REHEARSAL LIST (line 71)", "row 6 adds items 11 to 16 to the REHEARSAL LIST (line 71)")
why_add(8, "c6r changes (c6q design review M-A, M-C, minors; c6q naive review): item 12 now gates card line 1 and the scene 3 caption on the studio lead's written approval of the lease wording (his gate G12, LRN:33, OPEN) and makes the repeat sent more than 45 seconds after the first send mandatory whenever line 1 or the caption carries the plain statement (before, only when the card said a second send is never processed again, which the default does, but nothing then tested it); item 11 says that the reading of Q27 (a), (b), (c) as 'no take on Mon 23 Nov unless all three are shown' is the strictest reading applied until the owner has spoken (ORD:232 keeps Q27 OWNER-OPEN), says that the sentence does not block Wed 18 Nov, and asks for the run length of the take program because 18:04 UTC (23:34 IST) is 15 minutes before the 18:19 UTC (23:49 IST) cancel time.")

why_add(11, "c6r: the card row's own Time cell on run sheet line 41 still says '30 s EST' and no row edits it, because an edit of that cell would need a text that contains a table border; the studio lead changes that cell to '40 s EST' by hand when he applies this row, or says that he does not (the run sheet's total in lines 44 to 46 is what this row changes). It is listed as a lead question under L-CARDLEN.")
