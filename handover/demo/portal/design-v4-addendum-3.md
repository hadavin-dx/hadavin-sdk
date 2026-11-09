# Addendum 3 to design-v4: on-screen fake-data wording (lead, owner decision 2026-11-09, supersedes design-v4 Section 8.2 first on-screen sentence only)

**Why.** The owner rejected the red banner and the plain counters page as not looking like a real product ("cheap looks"). The honesty goal of the old sentence stays: a viewer must see, from the first second of every scene, that the data and systems are made up.

**Old text (8.2).** On screen from second 0, in every scene: "FAKE CRM - FAKE EMAIL - RECORDED AI REPLIES - MADE-UP LEADS", shown with three counters by `scripts/show_counters.py`.

**New text (after the comprehension review, saved in review-addendum3-comprehension.md; rev 2).**
1. Top-bar line, from second 0 in every scene where the portal is visible, supplied by the demo extension (`demo_only`), never by product files; shown unless the server says `simulated: false` (if unsure, the line stays on screen): "Demo: made-up leads. CRM and email are fake. AI replies are pre-written. Nothing here is sent to real customers or real systems."
2. Scene 1 (n8n fills most of the screen): the first caption, in the first 2 seconds: "Made-up leads. Fake CRM, fake email, pre-written AI replies. Nothing reaches real customers." The portal half still shows the top-bar line.
3. Tile labels: "Leads in the lead book", "Emails in the fake outbox", "Duplicates caught (made-up leads)", "Leads in the fake CRM" (say "posts" if the CRM is the blind one), "AI calls (pre-written replies, no live AI)". The three named counters are `kpi-leads`, `kpi-outbox`, `kpi-duplicates`; the AI counter is `kpi-ai-calls`.
4. Not said: "Nothing leaves this computer", and any sentence that names "the desk" without defining it for the viewer. n8n, shown in the same video, may send its own usage data to n8n; the claim covers customers, CRM and email only.
5. Supersedes design-v4 Section 8.2 first on-screen sentence AND the `scripts/show_counters.py` display for the final video (the script stays as a fallback). The README line "no video exists" refers to the n8n measurements only; say so.
6. Minimum legibility of the top-bar line: at least 13 px at 1920 wide with text contrast of at least 4.5:1 in light and dark.

**Check.** Video frame check at second 0, 2 and 10 of each scene: the facts are readable at 1080p. Reviewer-judged.
