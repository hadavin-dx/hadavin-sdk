# L4c key-shape check (16 Nov 2026), updated 16:45Z by the lead's scan

Result: the scan was run by the lead (not by this lane), after the owner said "scan yes" in chat. Counts only; the lead read no text (work/LEAD-ANSWERS.md answer 8 update, 16:45Z). Earlier version of this page (NOT CHECKED): work/L4c-key-shape-check-history-3.md.

Seven files (all under `handover/demo/real-run/`, which is in `work/OWNER-ONLY.txt`; this lane still did not open them):
- sk-ant keys: 0 in all seven.
- generic sk- keys: 0 in all seven.
- HubSpot pat- keys: 0 in all seven.
- AWS AKIA keys: 0 in all seven.
- Loose patterns hit a few ordinary tokens: git-style hex ids in 1 file (REVIEW-real-run-v6), a few 16-letter words in 2 files. No mixed letter-and-digit key-like token in any file.

Decision (lead, answer 8): no key or secret needs changing on this evidence. The login-key choice is closed. The digest lines stay visible (answer 1: delete is not needed).

Limits (UNVERIFIED, stated by the lead): these are pattern counts, not a read; an app password written as ordinary words with spaces could slip past; the lead did not open the files.
