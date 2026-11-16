# Review r1 of F4 (docs fix) - fallback reviewer
Reviewer: general-purpose agent that adopted agents/codebase_details.md (egm:* agent types were not registered in this session; labelled FALLBACK). Read-only, no tests run. Snapshot: handover/core/review/snap-F4/. Saved by the CORE lead from the agent's inline report (condensed, nothing added).

Verified correct (code vs new text): receipt skip (desk.py:1361-1363, schema.sql:7); probe --plan before the name check (hubspot_probe.py:300-307); HubSpot key re-read per call and BOM (crm_hubspot.py:259-268); mail password per send (smtp_provider.py:164,237); DESK_SMTP_TIMEOUT 5 frozen at import (smtp_outbox.py:79, config.py:434); SMTPP clamp (smtp_provider.py:325-329); rota keys (config.py:369,406); crash_desk needs "." on the path; load_tools defaults and flags.

Major
1. README.md:62, 79, 96 still say the repeated request "changes nothing"; the diff adds that it uses a receipt number and desk.py:1362 adds 1 to receipts.attempts. Fix: "no second lead, no second email; it only uses one receipt number and adds one to that request's attempts count".
2. load_tools/README.md:17 "It was run as written (30 requests, all seven checks held)": no test runs it; two traps: servers started with & and the driver starts at once (no readiness wait); the check reads data/desk.sqlite3, which a README "Try it" run may have filled. Fix: readiness wait, remove or separate the book, and reword to "was run once on <date>" or add a test.
3. Test gap (the surviving mutant): docs/tests.md "with no total line" is never asserted by the -qq test. Fix: assert the two phrases in TESTS_PAGE.
Minor
4. Count tests pytest.skip when the last line is not plain "N tests collected in S seconds": the count guard can silently never run (CI browser tools not checked). Fix: turn skip into failure in CI by env var, or parse the other form.
5. Failure message says only "out of date": print the new numbers.
6. Crash-script test splits on ":" and rejoins with os.pathsep: Windows form "src;." never checked; only Linux claimed.
7. Probe test: use a distinctive bad name so a leak cannot hide in common words.
8. README.md:20 wording hard to follow; "SQLite" used before explained. Suggested: "the desk writes down every arrival, including the repeat, and the numbering never goes back, so number 2 is taken by the repeat".
9. docs/tests.md:65 and README.md:130 old counts (2516) next to the new 3989: add "an earlier commit".
10. docs/limits.md:71, versions.md:9 dated pass counts: fine if each states its commit.
Nit 11. real-services.md claims (--assume-yes only with --dry-fakes, F1-F6 naming) not verified line by line.
Not checked: other sentences of docs/real-services.md, docs/settings.md lines, real-run.env.example refusal text, the 3989/97 numbers themselves (from runner evidence), CI workflow, Windows/macOS, n8n and demo_only docs for more "changes nothing" wording.
