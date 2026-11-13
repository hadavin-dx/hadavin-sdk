# If a take stalls or fails

Plain words. Only what the repository's scripts and docs say is stated as fact (named in brackets). Everything else is marked **UNVERIFIED**: I looked in the demo repository (`docs/`, `scripts/`) and in the read-only handover files and did not find it. Do not rely on an UNVERIFIED line before the owner confirms it.

## What the repository says (for the real-services run, `scripts/run_real_check.py`)
1. **The first thing the run does** is print the worst case (HubSpot calls, mails, dollars) and ask y/N. Exit code 1 means it stopped before calling anything: you did not answer `y`, or there was no terminal. Nothing was called, nothing to clean (`docs/settings.md`).
2. **Exit code 2** means it refused at the start (a missing or bad setting). Nothing was called. Fix the setting named in the message and start again. A new run needs a NEW database file name: the file named by `DESK_DB_PATH` must not exist yet (`docs/real-services.md`, `docs/settings.md`).
3. **Exit code 3** means the run could not finish, a check failed, the book could not be read, or (with `--cleanup`) some contacts could not be archived. The result is also written to a JSON file (the line "result file: ..." says where).
4. **Contacts left behind.** Without `--cleanup` the contacts stay in HubSpot (that is the exit code's meaning, `docs/settings.md`). With `--cleanup` the run archives only the contacts that carry this run's lead ids; if some are left it prints "clean-up: N contacts are LEFT" with their HubSpot contact numbers, and you archive them by hand. If the HubSpot read-back itself fails, it prints how many contacts the desk created ("up to that many may still be in HubSpot"; their lead ids start with L) and again you archive them by hand.
5. **After a failed take, never reuse the old database file.** The clean-up relies on a book that holds only this run's leads (`scripts/run_real_check.py`, first lines).
6. **Safe self-test with no real service:** `python scripts/run_real_check.py --dry-fakes` (`docs/real-services.md`).
7. **Caps.** Each run has hard caps set in the config: HubSpot calls (`DESK_HUBSPOT_MAX_CALLS`, `REAL_HUBSPOT_READBACK_MAX_CALLS`) and mails (`DESK_SMTPP_MAX_SENDS`) (`scripts/run_real_check.py`).
8. **If the take stalls** (no output for a long time): the repository does not give a "wait this long" rule. The desk's own waits are settings (`REAL_DRAIN_SECONDS` default 150, `REAL_MAIL_WAIT_SECONDS` default 90); a stall longer than those is not described. Stopping the run by hand and then archiving the contacts as in item 4 is the only safe reading I can offer (SUGGESTION, not stated in the repository).

## UNVERIFIED (named in the order, not found in the repository or the handover files I may read)
- **`end.flag`**: what it is, who writes it, when it ends a take. Not found anywhere.
- **"Retire check"**: what is retired, and how to check it. Not found.
- **"The 5-take limit"**: where the limit is counted and what happens at take 5. Not found. The repository has caps on calls and mails per run, not a count of takes.
- **"Credits end 23 Nov"**: which credits (a service plan, an API budget, a video tool?). Not found in any file I may read.
- **What "a take" is in the scripts**: the orders speak of "take scripts" and "take mode"; those scripts are not in the demo repository I can read (it has `run_real_check.py`, `run_live_check.py` and the demo start scripts only).
- Any step that cleans up the owner's own mailboxes after a failed take (the run counts mails by a header and reads no body; it does not delete mails).

## To get these confirmed
The owner or the lead pastes the take script's own help text or its notes; I then replace each UNVERIFIED line with what that text says.
