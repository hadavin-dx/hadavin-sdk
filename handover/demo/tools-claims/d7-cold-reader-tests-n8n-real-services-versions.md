# D7 cold read: lead desk repository (EVIDENCE RUNNER, read-only, no judgement of fixes)

Reader: a freelancer who wants to ADOPT the desk. Files read top to bottom in the order given: docs/tests.md, docs/why-this-code.md, docs/n8n-recipe.md, docs/real-services.md, docs/hubspot-probe.md, versions.md. Line numbers are the file's own lines (`cat -n`). No other file was read to understand a sentence. I only listed directories and used grep to check that named files and headings exist (see "Link checks" at the end).

Studio folder: not in this container, so the bible rules were not checked.

Types: a = unclear, b = jargon or abbreviation not explained before use, c = contradiction (both places given), d = promises more than the text around it supports, e = too long to follow in one reading (about 60+ words with nested brackets).

Words never explained in these six files that block a cold reader from page one: "the desk", "keyed / blind" (tests.md:96 sends the reader to the README), "stand-in", "book", "receipt", "outbox", "CRM", "n8n", "UNKNOWN" (defined only at tests.md:146, after many earlier uses), "lock file", "CI". Listed once here, not repeated in every row.

## docs/tests.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| tests.md:3-7 | "the short summary in the README" / "the desk" (first use at 26) | b | Say once what the desk is: "the desk is the lead-handling program in this repository". |
| tests.md:7 | "installed from a lock file into the `.venv` folder" | b | "installed from a file that fixes every package version (a lock file) into a separate folder named `.venv`, so nothing else on your computer changes" |
| tests.md:9, 14 | "with the `.venv` folder switched on as in the README, "Try it"" | a | "with the `.venv` folder activated (the README, section "Try it", shows how)" |
| tests.md:19 | "The SonarQube job ... also measures how much of the code the tests run. On Linux, instead of the install line above, install the dev lock and the coverage lock ... in one pip call, as the job does; pip stops with an error if a package is pinned to two different versions" | b,e | "SonarQube is a code-quality service; one automatic check (a CI job) uses it to measure which lines the tests run. To do the same, install both lock files in one pip command; pip stops with an error if the two files pin different versions of one package." |
| tests.md:24 | "so the figure counts code that only they reach as not run" | a | "so lines that only the browser tests run are counted as not covered" |
| tests.md:26 | "The crash scene: ... write a point name (for example `D2`) into the flag file it prints, and the next time the desk reaches that point it ends at once" | a,b | "D2 is one crash point from the table under "What each promise rests on". The script prints the path of a flag file; write a point name into it and the desk stops itself the next time it reaches that point." |
| tests.md:26 | "Writing `blind` instead of `keyed` in the start command" | a | Which start command? "In the command that starts the demo mail system, `blind` instead of `keyed` starts a mail system that cannot recognise a repeated send." |
| tests.md:28 | "the `DESK_*` names, plus the extra names of the real-services script and `N8N_URL`, `N8N_API_KEY_FILE` and the `DPLD_*` names; n8n's own `N8N_PORT` ..." | b,e | "DPLD" is never explained (also at 88, `DPLD_REQUIRE_SCAN`). Split the sentence; say what DPLD stands for. |
| tests.md:30 | the whole paragraph (about 270 words, about 25 tool names) | e,b | ruff, mypy, bandit, gitleaks, CodeQL, Semgrep, Dependabot, CodeRabbit, SonarQube Cloud, "pinned by its full commit SHA", "Action", "schema check" are not explained. Use a list: "name: what it looks for". |
| tests.md:30 | "A second workflow ... `codeql.yml` ... A fourth, `semgrep.yml` ...; the third, `sonar.yml`" | a | "Four workflows (automatic checks) exist: lint.yml, codeql.yml, sonar.yml, semgrep.yml." |
| tests.md:30 | "No result of any of these is claimed here." | c | Contradicts tests.md:36 (a Semgrep run with "0 findings" is reported), tests.md:111 and versions.md:9 (test results). "No result of the SonarQube, CodeRabbit or CodeQL checks is claimed; the Semgrep result is below." |
| tests.md:30 | "`.env` files are never used: the demo needs no secrets." | c | Same paragraph names the secret `SONAR_TOKEN`; hubspot-probe.md:35 reads a secret from an environment variable; real-services.md:11 needs key files. "The demo on your computer needs no secrets and no `.env` file; the real-service scripts read secrets from files you name." |
| tests.md:30 | "and the whole test suite" (run by lint.yml) | c | Contradicts tests.md:52 and :111 (browser tests do not run in CI; "no CI run has been seen"). "the test suite without the browser tests". |
| tests.md:34 | the Semgrep paragraph (about 420 words) | e | Split: what it scans, network use, what the tests pin. |
| tests.md:34 | "no account, no token, no usage data sent" | d | Same paragraph: "no network capture was made, so this is not measured". "the workflow switches usage reporting off (`--metrics=off`); this was not measured". |
| tests.md:36 | "Why the numbers differ (79 rules and 64 files ..., 77 rules and 47 files ...) is not explained here." | a | A reader cannot tell which numbers to expect. "expect different numbers; check only that both are above zero". |
| tests.md:36 | "run 43403502735 ... head 15b8b15e" | a | A reader cannot open this run or commit; say where to find it or that it is not available. |
| tests.md:36, 82, 90 and n8n-recipe.md:8, 70 | "the project lead", "the author", "the project owner", "the repository owner", "the licence holder", "the owner" | a | One word, one person. Say once who each is, or use one word. |
| tests.md:40 | "add either folder to the command in the workflow and in the line below" | a | "the line below" is two paragraphs down (line 44). "in the run command under "Run it on your own computer"". |
| tests.md:40 | "`n8n` holds 3 JSON files ... and is only nominal" | a | "is in the command, but Semgrep is not expected to find anything in it" |
| tests.md:42 | the exit-code paragraph (about 450 words) | e | Put exit codes in a short table; move the experiments out. |
| tests.md:42 | "0 ...; 1 ...; 2 ...; 7 ...; any other non-zero code is a tool error ... 3 = ..." | a | Code 3 is listed after "any other code", so it reads as a tool error. Order the codes. |
| tests.md:42 | "The share of lines read does not predict this: it was about 0 to 100 percent in those files." | a | "How much of each file Semgrep could read did not predict whether exit 3 happened." |
| tests.md:46 | the suppression paragraph (about 330 words); "`ſ` (U+017F)", "A tab after the colon" | e,b | Give the rule in two lines (always write the rule id and a reason), then a short list of refused spellings. |
| tests.md:46 | "The `--ignore-gitleaks-allow` switch of the lint job concerns gitleaks only and has nothing to do with this." | a | Appears from nowhere; delete or introduce. |
| tests.md:46 | "The repository owner approves any suppression in the pull request." | d | Nothing shows this is enforced (compare tests.md:48 "nothing ... enforces"). "is meant to approve". |
| tests.md:48 | "so a shared package ... may have a different version in each; that is harmless" | d | No evidence for "harmless". "the author expects this to be harmless". |
| tests.md:48 | the bump paragraph (about 230 words) | e | Split: how to bump; who does it; which tool made which lock. |
| tests.md:52 | "a few in `tests/test_mode_safety.py`" | c | tests.md:80 reports 22 skips "at line 110 of `test_mode_safety.py`". Give the number. |
| tests.md:52 | "the masking promise P10 rests on them" | b | P10 is defined at line 129. "the masking promise (P10, further down)". |
| tests.md:52 | the list of seven test files in one sentence | e | Use a bullet list. |
| tests.md:54 | "Nothing else was needed in the author's runs below (no test checks this)" | a | "below" points to the run at line 74. |
| tests.md:74 | "(the Windows lock file was made but never installed)" | c | Which one? versions.md:75 says `requirements-dev-win.txt` was installed on Windows and versions.md:9 gives a Windows test run. "the Windows browser lock file". |
| tests.md:74 | the "Measured on Linux ..." paragraph (about 100 words) | e | |
| tests.md:76 | the Chromium-build bullet (about 180 words) | e | Move the build numbers to a small table. |
| tests.md:78 | whole bullet (about 260 words, commit ids bee6fff4, 43110e7, 558d37f) | e,a | The ids are "not in this repository's history", so the reader cannot use them. "earlier runs gave 2349 to 2462 passed; no logs are shipped". |
| tests.md:78 vs versions.md:9 | "2462 passed and 3 skipped (2465 tests)" vs "2462 passed, 2 skipped" (Linux, Python 3.12) | c | versions.md:9 admits it and does not resolve it. The reader cannot tell the expected skip count. |
| tests.md:79 | whole bullet (about 330 words) | e | |
| tests.md:79 vs versions.md:9 | "2516 tests" (commit 2ce1f98) vs "3883 tests collected" (this tree) | c | 1,367 more tests with no explanation (tests.md:79 explains only +51). |
| tests.md:79 vs versions.md:9 | "counted with `python -m pytest --collect-only -q`" gives a total vs "with `-q` or `-qq` the output is these per-file lines and no total" | c | One describes the command wrongly (same pytest 9.2.0 is pinned). |
| tests.md:80 | whole bullet (about 330 words); "(line 175)", "(line 488, "no node")" | e,a | Line numbers refer to files of another commit; the reader cannot use them. Keep the totals (114 passed, 113 skipped; 92 and 135 without Node). |
| tests.md:81 | "give that one command a `PATH` that does not hold the folder with Node, for example `PATH=$(dirname "$(command -v python)") python -m pytest -q -rs`" | a | "run pytest with a PATH that does not contain Node (example command), then check `command -v node` prints nothing" |
| tests.md:82 | "A count of 2329 passed and 135 skipped ...: its cause is not known" | a | Honest, but a reader cannot act. "If you see about 2329 passed and 135 skipped, Node is probably missing: run `python -m pytest -q -rs`." |
| tests.md:90 | the gitleaks measurement paragraph (about 230 words); "`hadavin-dx_`", "`generic-api-key`" | e,b | |
| tests.md:92 | the line-ending paragraph (about 600 words); "CRLF", "lone carriage return", "autocrlf", "renormalize", "the index" | e,b | Explain once "CRLF = Windows line endings"; give the two cures first, the git experiments after. |
| tests.md:92 | "Cure 2, the Python one-liner in the message" | a | The message is not shown in these files. |
| tests.md:92 | "The cures were not run on real Windows." | d | The text still offers `py -3` for Windows; say the Windows form is untested. |
| tests.md:96 | "(both mail kinds gave the same result in the tests, `tests/test_flow.py`, `EXPECT_MORE`)" | a,b | `EXPECT_MORE` is a code name. Delete or explain. |
| tests.md:101 | the A2 cell (about 140 words with nested brackets) | e | Move the explanation below the table. |
| tests.md:104 | "(a put may have started)" | b | "(a write request may already have been sent)" |
| tests.md:107 and 113 | "D1b" used in the table, defined at line 113 | b | Define it in the table row. |
| tests.md:111 | paragraph (about 120 words) | e | |
| tests.md:111 vs 30, 36 | "no CI run has been seen" vs "and the whole test suite" (30) and a CI run reported at 36 | c | Say which checks have been seen to run in CI (Semgrep: yes; Node and browser tests: no). |
| tests.md:116 and 118 | "'Tests named' means the tests exist and are named here; it is not a run result" vs column "Tests that show it" | d | Rename the column "Tests named for it". |
| tests.md:123 | P4 cell (about 150 words) | e | |
| tests.md:127 | P8 (about 190 words); "receipt number", "newest first by receipt number" | e,b | "receipt" is not defined; is it the same as "request number" (tests.md:120) and "Request id" (n8n-recipe.md:34)? One word for one thing. |
| tests.md:129 | P10 (about 400 words) | e | Split into promise, what is not masked, what is not covered. |
| tests.md:129 | "the browser tests listed in "Browser tests" below" | c | The section "Browser tests" is above (line 50). |
| tests.md:129 | "session storage" | b | "the browser keeps the choice only while the tab is open" |
| tests.md:129 | "The desk's log lines are meant to carry no email address, phone number or message" | d | The tests cover only `log.<level>(...)` calls in `src/lead_desk/*.py`; say so in the same sentence. |
| tests.md:131 | "What n8n did is reported separately below." | a | Nothing about n8n is below in this file; it is in `docs/n8n-recipe.md`, section 4. |
| tests.md:133 | "`received = new + duplicate + review + open`" | b | "open" is not defined. |
| tests.md:135 | "a book in which every follow-up ended UNKNOWN fails whatever allowance is given" | b | "book" (also why-this-code.md:21, real-services.md:20) and "allowance" are not defined. |
| tests.md:137 | "the code is deliberately broken in one known way (on the test side only)" | a | "on the test side only" cannot be understood. |
| tests.md:137 | "removes the database rule that two leads cannot share an email and the lookup" | a | "removes the database rule that stops two leads sharing an email, and the lookup that finds the first one" |
| tests.md:139-146 | "Terms for developers" lists six terms | b | The terms most needed are missing: keyed, blind, stand-in, book, receipt, follow-up, verdict. It also comes after many uses of UNKNOWN. |

## docs/why-this-code.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| why-this-code.md:3-4 vs 5-6 | "try the ready-made tool first, use the Python standard library second, write own code last" vs "(1) a workflow tool with no code (n8n), (2) the standard library, (3) a free library or program, (4) own code" | c | A free library is third in one order and ahead of the standard library in the other. Give one order. |
| why-this-code.md:5-6 vs 7 | "The order of tools tried" vs ""Not checked" means that tools were not compared" | d | The order is stated as followed, but rows 18 and 22 say no tool was checked. "the order the author aimed for". |
| why-this-code.md:14-15 vs 5-6 | rows "Tried first: Python's `sqlite3`", "Python's `http.server`" | c | The stated order puts n8n first, but these rows start at the standard library with no word on n8n. |
| why-this-code.md:7 | "Terms (atomic insert, UNIQUE key, test doubles, Host and Origin check, CRM dump, UNKNOWN) are explained in the README ... and in `docs/tests.md`" | a | Terms used in this file and in neither list: stand-in, outbox, book, idempotency, adapter, banner, bind rule, demo-tools gate. |
| why-this-code.md:7 and 9 | ""Not checked" means ..." and "Only n8n was compared ..." | a | The same warning twice in a few lines. |
| why-this-code.md:13 | the first table row (about 190 words) | e | |
| why-this-code.md:13 | "n8n alone, four patterns" | a | The four patterns are in n8n-recipe.md section 2 (lines 56-63); name that place. |
| why-this-code.md:13 | "no idempotency or outbox library, queue or other tool was compared" | b | "idempotency" (repeating an action has the same effect as doing it once) and "outbox" are not explained. |
| why-this-code.md:13 | "No n8n-only result is stated here" then "Result: Own code ... this is the part the demo is about" | d | The reader is led to think n8n alone failed; the cell says no result exists. "n8n alone was not shown to fail or to work". |
| why-this-code.md:13 vs tests.md:101, 123 | "a crash at each named point of the desk is tested in `tests/test_crash_points.py`" | c | tests.md:123 puts the stop-at-each-point tests in `tests/test_flow.py`; tests.md:101 says the `test_crash_points.py` kill test ends "a small helper process ... not the desk". |
| why-this-code.md:18 | "Two kinds of mail system (...) are the point of the test" | a | "The two mail-system stand-ins differ on purpose: one refuses a repeated send, one does not, and the tests check both." |
| why-this-code.md:19 | the "Real adapters" row (about 190 words) | e | |
| why-this-code.md:19 | "they are kept so the checks of the guarantee could be repeated with real services later" | d | "repeated" says it was done before; real-services.md:5-7 says never. "the guarantee" is not named. "so the checks could be run against real services later". |
| why-this-code.md:19 | "ask a system that cannot recognise a repeat only once" | a | "send to a mail system that cannot recognise a repeated send only once" |
| why-this-code.md:20 | "another tool could replace it if it writes the log format in `load_tools/README.md`" | d | Not tried; "might replace it". |
| why-this-code.md:21 | "Seven checks" / "the desk's own book" | b | The seven checks are not listed in these files (tests.md:135 names three). |
| why-this-code.md:24 | "for the licence holder's own use" | b | Who is the licence holder? See also n8n-recipe.md:8. |
| why-this-code.md:28 | the paragraph (about 430 words) | e | Make the six steps a numbered list. |
| why-this-code.md:28 | "closed lists", "`OUTBOX_STAND_INS`", "loopback-only bind rule", "demo-tools gate", "banner" | b | Not explained in these files. |
| why-this-code.md:28 vs 19 | "The desk talks to three things through three interfaces" vs a row listing four adapters (HubSpot, SMTP, IMAP counting, live model) | a | IMAP counting fits none of the three interfaces; say where it plugs in. |
| why-this-code.md:28 vs n8n-recipe.md:8 | steps "(1) write a module ... (6) ..." as instructions to adopt | c | n8n-recipe.md:8 says anything beyond importing the workflows unmodified needs the licence holder's written permission and that the licence covers scripts too. I did not open `LICENSE`; the reader needs one sentence saying whether adding a CRM kind is allowed. |
| why-this-code.md:28 vs versions.md:26 | "ships exactly one real CRM kind (HubSpot) and one real AI kind (`live_claude`)" | d | The AI kind "has only been run against the local stand-in server" (versions.md:26); the HubSpot adapter itself was not run on a real account (why-this-code.md:19). "ships adapters for one CRM and one AI service; both were run only against stand-ins". |

## docs/n8n-recipe.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| n8n-recipe.md:3 | "the desk" and "n8n" first use | b | One line: "n8n is a workflow tool; the desk is this repository's lead program." |
| n8n-recipe.md:4-5 | "The workflows ... were run against the desk on 2026-11-09, on one computer, in a real n8n (...) through its REST interface; lines say "checked" where that run showed it (...)" (about 75 words) | e,b | "REST interface" = "its web programming interface". Split in two. |
| n8n-recipe.md:5 | "the `proof` workflow" before it is named | a | Line 74 says `proof` is "Lead Desk: Duplicate Test (10 at once)". Say it at first use. |
| n8n-recipe.md:8 | "the licence holder's written permission" | b | Who? Name the person or the file. |
| n8n-recipe.md:10 vs 21, 82 | "Use no real credentials, no n8n licence key" vs "The runs used its free community licence" / "free registered n8n community licence" | c | A free community licence is a key you register for. Say whether to enter one. |
| n8n-recipe.md:10 vs 21 | "no real e-mail address in n8n" vs "Use your own business e-mail in YOUR n8n only" | c | n8n needs an owner account (21). "the account e-mail may be yours; the leads and mail addresses in the workflows are made up". |
| n8n-recipe.md:10-12 | "n8n creates its own web-address id for each webhook node when you import or activate, and the webhook keeps the same address ..., because the path is kept in the file (it is a plain word, not an id)" (about 70 words) | a,e | "n8n gives each webhook an internal id on import, but the web address you call stays `/webhook/desk-form`, because the file fixes that path." |
| n8n-recipe.md:13 | "After the import you only have to switch the workflow on" | d | Line 70 adds more steps for `proof` (delete the old copy first); "only" is too strong. |
| n8n-recipe.md:26 | the Docker / Host bullet (about 120 words); "`Host` name", "403 `forbidden_host`" | e,b | |
| n8n-recipe.md:34-36 | "n8n's own execution id was not tried" (said three times) and "it is expected to change on a re-run, which was not checked, so it is not used" | a,d | A reason that rests on an unchecked expectation. "The workflows use the id in the body because it was checked to work; n8n's execution id was not tried." |
| n8n-recipe.md:34 | "Request id" ("Request number" on the portal screens) | b | Also `submission_id`, `message_id`, `source_ref`, "receipt number" (tests.md:127). One name. |
| n8n-recipe.md:44 | "Its timeout is well above the desk's default send timeout of 5 seconds, so a slow answer ends the call in n8n later than in the desk, and a 400 or a 413 showed red in n8n" (about 70 words) | a,e | The n8n timeout value is not given; the desk's "send timeout" is not explained; two unrelated facts in one sentence. |
| n8n-recipe.md:46 | "the HTTP status did not" / "even where the desk said 201 or 202" | a | "n8n returned 200 to the caller even when the desk returned 201 or 202; read the verdict in the reply body". |
| n8n-recipe.md:52-53 | "5. ... shows 202 `review` ... 6. ... shows red (400, 413)" | a | Red in n8n, but the caller gets 500 (lines 46, 77); say which status the caller sees. |
| n8n-recipe.md:54 | step 7 (about 200 words) | e | |
| n8n-recipe.md:54 | "the node's other option ("Never Error") would hide the red mark" | d | Not tried; "was not tried". |
| n8n-recipe.md:56-63 | "(c) a Data Table upsert on the email column, where equal created and updated times mean the row is new" | a,b | "dedupe", "upsert", "Data Table" unexplained. "a row whose created time equals its updated time was just inserted". |
| n8n-recipe.md:58 | "The demo servers ran in blind counting mode" | b | "blind" (tests.md:96 sends to the README). |
| n8n-recipe.md:58 vs 56 | "These workflows are not shipped and no result ... is claimed" vs "ran in blind counting mode" | a | "ran" says runs took place; why-this-code.md:13 says "tried once". "were tried once, no result is claimed". |
| n8n-recipe.md:67-68 vs 46, 52 | "n8n's executions list showed success for a duplicate caller that was answered with an error" | c | Lines 46 and 52 say a duplicate gets 200 with verdict `duplicate`, not an error; line 77 says desk refusals show as an n8n error. Which error? |
| n8n-recipe.md:70 | the `proof` paragraph (about 430 words) | e | Split: result seen; rule changed; what to do once; what a MISMATCH means. |
| n8n-recipe.md:70 | "What the owner should run once" | a | The reader is not the owner. "To check the new rule yourself, do this once". |
| n8n-recipe.md:70 | "(nine requests that got no answer with a verdict ... used to be able to print PASS)" | a | "if any of the ten requests got no verdict, the old rule could still print PASS". |
| n8n-recipe.md:70 | "the line `result` ... the step "Wait for the desk to finish" from the last step" | a | Names the reader has not seen; "the `result` field of the last step". |
| n8n-recipe.md:74 | ""`docs/n8n-recipe.md` describes them"" | a | This file is `docs/n8n-recipe.md`; it points to itself. |
| n8n-recipe.md:76 vs 77 | "n8n answered 200 whenever the desk answered" vs "If the desk answers 400 ... or 413, the caller gets HTTP 500" | c | A 400 is also an answer. "whenever the desk answered successfully". |
| n8n-recipe.md:78 | "For longer outages raise the number of tries or the wait." | d | Advice not tried. |
| n8n-recipe.md:79, 80 | same facts as lines 70 and 10-13 (ten within one second; import ignores `active`) | a | Repeats; shorten. |

## docs/real-services.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| real-services.md:3 | "The steps above use only the demo stand-ins." | a | This file starts here; there are no "steps above". "The README steps ...". |
| real-services.md:3 | "demo stand-ins" | b | "stand-in" is not explained in these files. |
| real-services.md:5 | "This script is a reference that has been run only against the demo stand-ins ... and never against a real service" | a | "reference" is unclear. "This script was run only against stand-ins; it has never been run against a real service." |
| real-services.md:5 vs 7 | the same statement twice in two paragraphs | a | Say once. |
| real-services.md:7 | "until a run is recorded in this file, treat the real-service behaviour as untested, including what the code assumes about HubSpot (...)" (about 80 words) | e | |
| real-services.md:9 | "runs the same desk against a real CRM ... then COUNTS what really happened. Only the INPUT is made up: about 12 invented people at the address ending `example.com` (...)" | a,e | Capitals add no meaning. "about 12 invented people with addresses ending in `@example.com`". The paragraph is about 140 words. |
| real-services.md:9 vs hubspot-probe.md:66-68 | "a real CRM may refuse `.test` addresses" vs "an address ending in `.test` was refused with a 400" | c | One says may, the other says was. Use the observed fact in both. |
| real-services.md:9 | "worst-case number of calls, mails and dollars" | a | Dollars of what? Only `--live-model` spends money (line 14). |
| real-services.md:11 vs hubspot-probe.md:4, 48 | "a CRM service key with contacts read and write only" vs "the owner list was refused (403 `MISSING_SCOPES`) until the token also had the owners read scope" | c | If the desk's HubSpot code reads owners, "contacts read and write only" is not enough. Check and say. |
| real-services.md:11 vs hubspot-probe.md:33 | "CRM service key" vs "private-app token" vs "token" | a | One name for one thing. |
| real-services.md:12 | "1a. **Before turning lead stages on ... (required):**" | a,b | A required step numbered "1a"; "lead stages" is never explained; "CRM admin" is not defined. |
| real-services.md:13 | step 2 (about 170 words, three levels of brackets) | e | |
| real-services.md:13 vs hubspot-probe.md:13 | "`hadavin_lead_id`" vs "`dpld_tag`" | a | Two different contact properties in two scripts; say why. "dpld" is never explained. |
| real-services.md:14 | "`--live-model` (a real AI model, its own dollar cap in the `DESK_LIVE_*` names)" | a,b | "the dollar limit is set in the settings whose names start `DESK_LIVE_`". |
| real-services.md:16 | the "It sends new people ..." paragraph (about 230 words) | e | |
| real-services.md:16 | "repeats through the same door and the other door" | a | "sends the same lead again through the same intake (web form or e-mail) and through the other intake". |
| real-services.md:16 | "one person with two different addresses (a CRM that only compares email addresses sees two different people, so it cannot catch that; the desk also treats them as two leads, and the check list names them as "two-leads" ...)" | a | If both treat them as two leads, what does the check show? Say what it proves. |
| real-services.md:16 | "stops the desk hard once after the load started" | b | "load" and "hard stop" are not defined. "stops the desk process abruptly once while requests are being sent". |
| real-services.md:16 | "at different providers (for example one Gmail and one Google Workspace mailbox" | c | Gmail and Google Workspace are both Google; the example does not match "different providers". |
| real-services.md:16 | "by the header `X-Send-Key`" | b | "a header the desk adds to each mail so that a repeated send can be recognised". |
| real-services.md:16 | "prints only counts and a pass/fail table ..., plus a per-lead table" | a | Line 20 says failure tables mask e-mail addresses, so the output is more than "only counts". |
| real-services.md:18 | "no spam-folder, SPF or DKIM claim" | b | SPF and DKIM are sender checks for e-mail; explain or drop. |
| real-services.md:18 | "recorded `unknown` on purpose" | b | Written UNKNOWN elsewhere (tests.md:146). Same word, same spelling. |
| real-services.md:20 | the exit-code paragraph (about 230 words) | e | |
| real-services.md:20 vs 16 | "the first desk process really stopped at the crash point" | a | Line 16 says "stops the desk hard once"; use one word for it. |
| real-services.md:20 | "no test follows the key on a real network connection to HubSpot (the redirect test ... checks only that ...)" | a | "no test checks over a real connection that the key is sent only to HubSpot". |
| real-services.md:22 | the "Where the files may be" paragraph (about 230 words) | e | |
| real-services.md:22 | "links are followed" | a | "a symbolic link is replaced by the file it points to". |
| real-services.md:22 | "`--config <(command)`" | b | Shell process substitution; explain or drop. |
| real-services.md:22 | "it is found by looking the name up in the folder listings from the top of the disk (or the network share)" | a | |

## docs/hubspot-probe.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| hubspot-probe.md:3-4 | "does a free HubSpot account accept the API writes the desk needs" | d | Line 31 says the probe does not test the desk's combined owner-plus-status call. "the two separate writes the desk makes in one combined call". |
| hubspot-probe.md:3 | "A one-shot script" | a | It was run three times (line 4). "A small script that makes a few API calls and deletes its test contact". |
| hubspot-probe.md:4 | the "Result:" paragraph (about 190 words) | e | |
| hubspot-probe.md:4 vs 11, 22 | "Each run used 6 or 7 of the 8 calls" | c | Lines 11 and 22 say the normal path is 7. Why 6? (Probably the first run, where the owner list failed.) Say. |
| hubspot-probe.md:4 | "`MISSING_SCOPES`", "private-app token" | b | Explain: a token created in HubSpot's "private apps" settings. |
| hubspot-probe.md:7-8 | "any workflow or sequence on the account that reacts to a new contact or a new owner can fire" | b | "automation" (real-services.md:12) vs "workflow or sequence": one word. |
| hubspot-probe.md:13 | "(it is only set when it does)" | a | What is set? The script is never said to set `dpld_tag`; "dpld" is unexplained. |
| hubspot-probe.md:23-25 | "the normal steps may use at most 7 calls, so the 8th call is always kept for the permanent delete. The normal path uses 7, which leaves 1 spare: that spare pays for the archive-delete fallback or one retry." | c,e | The delete is step 7, so "8th call kept for the permanent delete" and "1 spare" cannot both be true. Use a table: step, calls. |
| hubspot-probe.md:25-28 | "Worst case is exactly 8 calls" with "If any step needed a retry, the fallback delete has no call left" | a | "after a retry, if the permanent delete is refused, the contact stays and a WARNING names it". |
| hubspot-probe.md:33 | "after you have agreed to the 7 calls" with `--yes-spend-calls 7` | d | The worst case is 8 calls (lines 11, 28). The reader agrees to 7 and may spend 8. |
| hubspot-probe.md:33-36 | the "Run (after you ..." sentence (about 85 words) | e | |
| hubspot-probe.md:41-43 | "(the list is what the script calls; HubSpot's own page ... was not readable in full ..., so the exact scope names are UNVERIFIED ...; the runs showed ...)" | e | |
| hubspot-probe.md:45-47 | "HubSpot answers 403 and the script reads that as "property absent" and skips it, which is harmless" | d | A missing scope is read as "absent"; the text does not show it is harmless. Line 4 shows the owners call fails on the same kind of 403. |
| hubspot-probe.md:49 | "the permanent (privacy) delete" | b | Called "permanent delete" (19), "(privacy) delete" (49), "gdpr-delete" (62). GDPR is not explained. One name. |
| hubspot-probe.md:66-68 | "must end in a real domain such as `example.com`" | c | real-services.md:9 calls it "the reserved example domain". `example.com` is not a real company domain. |
| hubspot-probe.md:70-73 | "UNVERIFIED (...)" paragraph also states what the runs showed ("`OPEN` was accepted ... answered 204") | a | Verified facts sit inside the UNVERIFIED paragraph; move them up to line 66. |
| hubspot-probe.md:71-72 | "a third-party page says it may be added to a block list, which is harmless for a random address" | d | Hearsay plus a claim of harmlessness. "may be added to a block list; the author thinks this does not matter for a made-up address". |
| hubspot-probe.md:75-77 | "Sources (names only)" | a | A reader cannot find the pages; give web addresses or say none are given. |

## versions.md

| file:line | exact words (short) | type | suggested plain words |
|---|---|---|---|
| versions.md:3 | "on a Windows computer (Python and the Windows lock file) and, for the test suite and the development lock file, a Linux container (see the lines below)" | a,e | "Python was run on one Windows computer and the tests on a Linux container." |
| versions.md:9 | the "Python required" cell (about 480 words) | e | Move run results to their own table with columns: commit, system, passed, skipped. |
| versions.md:9 | "no test failed on either" | d | The same cell says later edits are not covered; put that limit in the same sentence. |
| versions.md:9 vs tests.md:78 | "2462 passed, 2 skipped" vs "2462 passed and 3 skipped" | c | See the tests.md row for line 78. |
| versions.md:9 vs tests.md:79 | "3883" tests vs "2516" tests | c | 1,367 tests unexplained. |
| versions.md:9 | "`tests/test_workflow_run_flags.py: 10` (that is its last line)" | a | "the last line looks like `tests/test_workflow_run_flags.py: 10`" |
| versions.md:9 | "the tree of public main f3c39cf8 with the documentation changes applied" and "the commit that holds this file" | a | Two ways to name the commit; which is the reader's? |
| versions.md:10 | "SQLite library 3.49.1 in the author's run" | a | Which machine? Line 75 gives SQLite 3.46.1 for the Linux container. |
| versions.md:16 | "regular mode (no queue)" | b | "n8n's single-process mode" |
| versions.md:19 | "Not checked: that anyone else's n8n install matches these numbers ;" | a | Stray space before the semicolon. |
| versions.md:24 | "`anthropic-version` request header (`LIVE_API_VERSION`)" and "The live step" | b | Name the vendor service and say what "the live step" is (the desk's call to the AI service, real-services.md:14). |
| versions.md:37 | the SHA-check paragraph (about 110 words) | e | |
| versions.md:40 | the lock-file paragraph (about 280 words); "the build tool is not itself pinned" | e,a | Which build tool? "pip-compile and uv are not pinned". |
| versions.md:40 | "The only difference is `colorama`" (again in the table at line 51 and in contract.md) | a | Said three times. |
| versions.md:45 | "rules E, F, W, I, S, PLR2004" | b | Say these are ruff rule groups, or drop. |
| versions.md:54 | "MPL-2.0 is file-level copyleft, not GPL, AGPL, SSPL or BUSL" | b | "a licence that only requires changes to its own files to be shared" |
| versions.md:57 | the browser-lock paragraph (about 270 words) | e | |
| versions.md:57 | "`--exclude-newer` ignores any release uploaded after that date, so the same command gives the same lock later" | d | Not shown; "should give". |
| versions.md:59 vs tests.md:30 | "`.codeant/configuration.json` ... the bot's check" | b,c | "codeant" and "the bot" are never introduced; tests.md:30 names only CodeRabbit and SonarQube Cloud as "two review services", yet a third tool (CodeAnt) appears. |
| versions.md:61 | the secret-scan paragraph (about 220 words); raw `paths = [...]` pattern | e,b | |
| versions.md:69-71 | the licence-scan paragraphs (about 270 words) | e | |
| versions.md:74 | "`SO_EXCLUSIVEADDRUSE` ... `PermissionError` (WSAEACCES) instead of `EADDRINUSE`" | b | Only TIME_WAIT is explained. "On Windows, restarting on a fixed port may fail for a short time; tests use port 0 (the system picks a free port)." |
| versions.md:75 | the lock-file "Not checked" bullet (about 130 words) | e | |
| versions.md:76 | "bandit B101 on tests: tests are excluded from bandit, so not relevant." | a,b | Sits under "Not checked" yet says "not relevant"; "B101" is unexplained. |
| versions.md:77 | "pre-commit and exiftool are not used." | a | Why mentioned? |

## Link checks (existence only)

Present: all six files, docs/limits.md, docs/settings.md, docs/portal.md, contract.md ("Quality commands" at contract.md:71), README.md (heading "Words used here" at README.md:26), SECURITY.md, load_tools/README.md, scripts hubspot_probe.py, run_real_check.py, crash_desk.py, n8n_api.py, real-run.env.example, n8n/desk-form.json, desk-webhook.json, proof.json, .github/workflows codeql, lint, semgrep, sonar, .github/dependabot.yml, .codeant/, .gitleaks.toml, patterns.txt, exceptions.txt (34 lines, matches tests.md:92), docs/limits.md headings "Counters and database rules" and "Which CRM stage things the desk touches" and the text "Rules of the desk's records". All test files named in the rows above exist (test_crash_points, test_flow, test_http, test_hubspot_probe, test_real_check_dry, test_path_confinement, test_nosemgrep_form, test_except_clause_hierarchy, test_n8n_proof_result, test_hygiene, test_gitleaks_exceptions, test_gitleaks_semgrep_lock, test_mode_safety, test_portal_mode, test_portal_log_poll, test_codeant_demo_only, test_lead_crm_copy, test_load_tools, test_smtp_provider, test_crm_hubspot, test_reminder_email, test_input_edge_cases).
Not checked: tests/test_migration_triggers.py, `LICENSE` text, requirements-* headers, the n8n 3-tries/1-second values (only `"retryOnFail": true` at n8n/desk-form.json:103 was seen).
Arithmetic in the text re-added and correct: 2349+116=2465; 2460+2+3=2465; 2513+3=2516; 2329+135=2464; 114+113=227=92+135; 22=1+2+19; 22+28+60+3=113; 16 min 33 s = 993 s; 19 and 18 pinned packages match the versions.md table.

## Counts (rows can carry two types, so letter totals exceed row totals)

| file | rows | a | b | c | d | e |
|---|---|---|---|---|---|---|
| docs/tests.md | 66 | 23 | 18 | 10 | 6 | 20 |
| docs/why-this-code.md | 22 | 6 | 4 | 4 | 5 | 3 |
| docs/n8n-recipe.md | 28 | 13 | 7 | 4 | 4 | 6 |
| docs/real-services.md | 30 | 16 | 8 | 3 | 0 | 6 |
| docs/hubspot-probe.md | 18 | 5 | 3 | 3 | 4 | 4 |
| versions.md | 25 | 9 | 8 | 3 | 2 | 8 |
| total | 189 | 72 | 48 | 27 | 21 | 47 |

Not every long sentence is listed once per sentence: where one paragraph is too long, it is one "e" row for the paragraph. Several paragraphs (tests.md:34, 42, 46, 92; n8n-recipe.md:70; versions.md:9) are 300 to 600 words each.

## The 10 worst sentences

1. why-this-code.md:3-6 against itself: two different tool orders in the same paragraph (standard library second, or free library third).
2. n8n-recipe.md:10 against n8n-recipe.md:21 and 82: "no n8n licence key" and "no real e-mail address" against "free community licence" and "use your own business e-mail". A first-time reader cannot start n8n by following both.
3. hubspot-probe.md:23-25: "the 8th call is always kept for the permanent delete. The normal path uses 7, which leaves 1 spare". The delete is already one of the 7; the budget is stated two ways.
4. tests.md:30: "No result of any of these is claimed here." Results are reported at tests.md:36 and in versions.md:9; the same paragraph is about 270 words with about 25 unexplained tool names.
5. why-this-code.md:13 against tests.md:101 and 123: says crashes at each point are tested in `tests/test_crash_points.py`; tests.md says the stop-at-each-point tests are in `tests/test_flow.py` and that the `test_crash_points.py` kill test stops a helper, not the desk.
6. tests.md:78 and versions.md:9 (and tests.md:79 against versions.md:9): the same Linux run is 3 skipped in one file and 2 skipped in the other, and 2516 tests become 3883 with no explanation. The reader cannot tell what a good run looks like.
7. real-services.md:3: "The steps above use only the demo stand-ins." The file starts at that heading, so there are no steps above, and "stand-in" is never explained.
8. n8n-recipe.md:70: one paragraph of about 430 words (result seen, rule changed, what "the owner should run once", what MISMATCH means) with nested brackets, addressed to "the owner" rather than the reader.
9. tests.md:129 P10: about 400 words, says the tests are "listed in "Browser tests" below" (that section is above), and the log promise says "meant to carry no email address" while the tests cover only some log calls.
10. real-services.md:16: "one person with two different addresses (a CRM that only compares email addresses sees two different people, so it cannot catch that; the desk also treats them as two leads ...)" and "different providers (for example one Gmail and one Google Workspace mailbox". The first does not say what the check proves; the second example is one provider.

Not done, by the brief: no lint, no pytest, no network, no agents, no fixes. No process was started.
