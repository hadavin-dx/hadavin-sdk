# Watch checklist for the ONE final watch of the video (about 60 seconds of looking)

Plain words. Source of each fact: the scripts and docs in the demo repository (named in brackets). A line marked SUGGESTION is my advice, not something the repository states.

**What the real-services run is meant to show on screen** (`scripts/run_real_check.py`, `docs/real-services.md`): only counts and a pass/fail table. It is built never to print a key, an e-mail address or a message text. If you see one, that is a defect: stop and do not publish.

## Look for these, in this order
1. **A real e-mail address.** Made-up people use the ending `@example.com` and are labelled. The docs say nobody outside your own inboxes receives anything (docs/real-services.md), so your own inbox addresses are the real ones that must not show. Anything with a real-looking name or company before the `@`, or a provider ending (gmail, outlook and the like), is a stop. SUGGESTION: also check the browser tab, the window title and any mail-program list behind the terminal.
2. **API key or password text.** Key files are named by path only in the config; the script prints no key. A long run of random letters and digits anywhere on screen is a stop. Also look at the config file if it is ever opened on camera: it holds paths of key files, never keys, but the paths themselves show folder names (SUGGESTION: do not open it on camera).
3. **HubSpot names.** The run reads and archives contacts by a lead id (starting with `L`) and the contact property `hadavin_lead_id`. If the HubSpot page shows any contact, company, owner or portal name that is not made up, that is a stop. A real run prints "HubSpot contact numbers" only if some contacts were left behind. SUGGESTION: do not show the HubSpot page at all.
4. **Anything not made up.** Names, companies, phone numbers, deals, subject lines. Everything on screen should be one of the made-up demo people. If you doubt a name, treat it as real.
5. **Folder and user names in paths.** Terminal prompts and the result-file line ("result file: ...") show a folder path; a folder under a personal name is a stop. SUGGESTION: record in a neutral folder.
6. **Clip edges.** Look at the first 3 seconds and the last 3 seconds: a half-typed command, a password prompt, a notification pop-up, a stray window, the previous take's output scrolled at the top. SUGGESTION from me, not from the repository.
7. **The "y/N" question.** The real run first prints the worst case of calls, mails and dollars and asks y/N (`scripts/run_real_check.py`). The answer is the author's own decision; it must not be edited out in a way that hides the worst-case line (SUGGESTION).

## Result
- All seven clean: publish.
- Any stop: do not publish that take; see FAILED-TAKE-NOTE.md.

## UNVERIFIED (not found in the repository)
- Any rule about the length of the clip, the video editor, the platform's own checks, or the author's private list of words (the orders say the automatic scanner and the private word list were cut).
