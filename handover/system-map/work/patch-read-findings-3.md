# Fresh reader on work/RUNBOOK-V4.3-PATCH.md, 16 Nov (agent afa85100f4fa94f38). Counts (98 + 42 = 140; 33 OD) and 25 old-text rows PASS; master sentence 11 times PASS.
Q1 MAJOR line 211 (P84, READY): the New text says "latest planned start 17:30Z (23:00 IST): by 14:30Z (20:00 IST)" but the row's own Note says the notice names the LAUNCH, latest launch about 17:25Z, message due 14:25Z. Fix: change the New text to 17:25Z / 14:25Z (and IST) with the word launch, or set the row to WAITING-ON-CODE (r41); keep counts in step if the status changes (READY 15 -> 14, WAITING-ON-CODE 46 -> 47) in the table, counts paragraph, title and every place that repeats them.
Q2 NIT lines 197, 198, 212 (P70, P71, P85): New text says bare "must start by 17:30Z" / "latest start is 17:30Z": add "run start" in the New text, not only in the Note.
Q3 NIT lines 261-264 (OD-27, OD-28): question text says "latest start" for 17:40Z and 17:30Z: add launch or run start.
Q4 NIT line 3 and 9: add "(run start)" to the 17:30Z in the summary.
Q5 NIT lines 21, 124, 125, 129, 364: status definitions are at line 55, not 54.
Q6 NIT line 154: heading quote says "you delete them by a filtered list" vs master sentence "the owner deletes them"; keep only if it is a quoted heading from v4.2/lead text; state in the row that it is a deliberate variant (the page's reader is the owner).
Q7 NOTE 17:40Z: the file nowhere says it is the hard latest RUN START; it says "accepted start up to 17:40Z ... launch or run start UNVERIFIED". Add one sentence in the glossary entry: hard latest run start per the lead's figure 17:40Z, UNVERIFIED whether launch or run start.
Not checked by the reader: old text of P05, P07, P28-P55, P59-P62, P63+ ; any New text against its source; IST arithmetic; lines 164-189, 225-235, 269-289.
