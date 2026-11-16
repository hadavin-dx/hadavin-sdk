# Changes

## Round 7k (the r7j review and the last mutants of pass 9)

* Key text: an error raised by the live model call, the CRM call or the key-file reader no longer keeps the earlier
  error as its `__context__` (it could hold request data); `raise ... from None` only hides it from the printout.
  Tested on every failure path with an echo server, injected opener errors and bad key files.
* `netconnect.py`: `localhost` answers 127.0.0.1 only (the invented `::1` made a refused `::1` replace a time-out
  error, so a run with a total time limit ended with the wrong error); when one address ends in a time-out and a
  later one is refused, the time-out is raised; a look-up thread that fails to start (or fails after it began) gives
  its place back once (the count could go to -1 and the cap drift to 9); a digit address in any form the system
  accepts (127.1, 0x7f.1, 2130706433, and a form with a leading zero, which is octal: 017 is 15) is decided by the system with
  AI_NUMERICHOST, with no thread and no cap.
* Load driver: a request that ended in a driver error counts in the exit decision: exit code 3, ONE line, the same
  count, summary key `driver_errors`; the WARNING about missing log lines is printed only for an exit-0 run (never two
  stderr lines). Stale comments and docstrings rewritten to the r7j rule.
* Tests: `tests/test_r7k_findings.py`; the 0.24 s lower bound in `test_r7g_findings.py` (failed under load) was removed;
  a test of the r7j file that pinned `127.1` as needing a look-up was changed to the new rule.

## Round 7j (the r7h review)

* `netconnect.py`: the socket is made inside the `try` (no IPv6 on the machine fails that address only); the cap on
  look-up threads reserves its place under the lock before the thread starts (never more than 8 at once, also for
  concurrent callers); an IP address in digits and `localhost` need no look-up thread and are never refused by the cap;
  one fixed text for a look-up with no address.
* Load driver: the run ends with exit code 3 and one line when any request was given up at its retry deadline or taken
  out by the stop (before: exit 0 for given-up requests). `exit_code_and_line` is the one place.
* `crm_hubspot.py`: `archive` takes ASCII digits only; a returned email with a non-ASCII letter is not the same email.

## Round 7h (host checks that change the text, the connect time per address, a cap on hung look-ups)

* A check that lower-cases before it matches now sees the text that is used: the mailbox host, the mail sender's host
  (`ProviderSettings.from_env`) and every web address setting (`split_url`) refuse non-ASCII text (the Kelvin sign
  lower-cased to `k`, so a host such as the Kelvin sign plus `api.` plus the vendor's domain passed as a vendor host); `child_environment` in
  `scripts/run_real_check.py` matches system variable names only when they are ASCII (the long s upper-cased to `S`).
* Several addresses: each address except the last gets the least of the cap, the time left and an even share of the time
  left (time left divided by the addresses not yet tried), so every address gets a turn; the last gets all the time left.
* At most `LOOKUP_HUNG_MAX` (8) name look-ups that nobody waits for run at once; a new one is refused at once with the
  same time-out text and starts no thread.

## Round 7g (name look-up errors, several addresses, a stopped run)

* Name look-up (`src/lead_desk/netconnect.py`): whatever the look-up raises (also a name the system refuses, such as a
  part of more than 63 characters or a lone surrogate) the caller gets one fixed OSError and nothing is printed to the
  error output; the helper thread can no longer end with a traceback. The mailbox host is checked when the settings are
  made (exit code 2 and one line in `scripts/run_real_check.py`).
* One connect to a host with several addresses: each address except the last gets at most
  `CONNECT_PER_ADDRESS_SECONDS`, the last gets the time left, the total limit is kept. The socket is closed on any error.
* Load driver: a request that was already retrying when the run was stopped is counted with the never-sent ones (one
  function, `stopped_count`): the run ends with exit code 3 and one line. The look for a listener goes through
  `netconnect`, so the host-name look-up is inside its 1 s.

## Round 7d (secret key before the question, mailbox connect time, load driver on a dead desk)

* `scripts/run_real_check.py` reads the live model key file (with the one secret reader) before the cost lines and
  before the Start question, like the other secret files. The model fake reads its `--key-file` the same way.
* Mailbox (IMAP) check: the total time limit also covers the TCP connect and the whole TLS handshake (a server that
  sends one handshake byte at a time can no longer stretch it). Both time settings must be finite numbers above 0 and
  at most `IMAP_SECONDS_MAX` (one hour); anything else is one fixed refusal line.
* Mail sender (SMTP): the last line of a reply, and a reply that is only the 3-digit code, now count toward the 64 KiB
  cap (the cap is accepted, one byte more is refused whole).
* HubSpot probe: for a refused call it prints the status and, when it is on a fixed list, the error category. It no
  longer prints any text of the server's message (a cut, upper-case, percent-encoded or zero-width-spaced echo of the
  token could not be found by an exact replace).
* Load driver: one look for a listener (1 s, nothing sent) before any worker starts: a closed port ends at once with one
  line and exit code 3. During a run, after 2 x threads connection errors with no answer at all, all workers stop.
* Windows scripts: `reset.ps1` uses `-LiteralPath` everywhere; `start_all.ps1` reads every setting before it starts
  anything and ends a failed start with one fixed line and exit code 4. Both were NOT run in PowerShell.
* Tests: the clean-tree guard and a test folder copy no longer trip the wall-clock and conftest checks; the portal
  stubs ignore the `?limit=` part of the path; long TMPDIR paths no longer break the socket cases.

## Round 7c (one JSON reader, mail deadlines, scripts that start and stop the demo)

* Every place that reads JSON text goes through one reader, `lead_desk.jsonread.loads_bounded`. Text nested about
  30,000 levels deep (60 KB) used to end in a Python error trace, and on the model path left a reserved spend open.
  Now it is a plain refusal at each place. `tests/test_r7c_one_json_loader.py` sends such text to each place and fails
  when a file outside the reader parses JSON another way.
* Mailbox (IMAP) check: one total time limit from the first byte (the greeting, one slow line and one slow literal
  are all inside it); before it, a server that sent one byte every 0.3 s kept the call far past its limit. A mailbox
  connection refused for its TLS version gets no LOGOUT.
* Mail sender (SMTP): the cap of 64 KiB now covers the whole reply (all lines), not only an unfinished line; an SMTP
  connection refused for its TLS version is closed at once.
* `scripts/run_real_check.py` reads the HubSpot key file, the mail password file and the mailbox password files before
  it asks "Start?"; a bad secret file is refused before the question and before any connection. The settings file
  refuses a name that holds a no-break space.
* `HeadDeadline` (the time limit of the demo servers' answers): a failure to send an error answer is swallowed only when the sender has
  gone (an OS error); any other error is raised.
* The portal asks the demo server for 200 rows (`?limit=`); the size claim of the view is now computed from the longest
  possible fields and tested with that worst row (`PORTAL_VIEW_ROW_BYTES`, `PORTAL_VIEW_REPLY_MAX_BYTES`).
* `scripts/start_all.ps1` now does what `start_all.sh` does: it waits until the demo server and the desk answer, stops
  what it started and ends with exit code 3 when they do not, and refuses a log or process file that is a link, a
  folder or a device (exit 4). It has not been run on Windows; text tests pin it.
* `scripts/reset.sh` and `scripts/reset.ps1` stop a process only when its whole command line is the desk's or the demo
  server's (`<python> -m lead_desk.server`, or `<python> -m demo_only.fakes_server --outbox keyed|blind --port N`), not
  when those words appear anywhere in it.
* Test helpers: `tests/support.py` refuses more ways to start a program (`git -c`, path look-alikes, keywords that
  replace the checked command line); `tests/conftest.py` fails the run when the repository folder changed
  (`tests/tree_guard.py`).
* `docs/settings.md`: the long `bind` table row is a note below the table.

## Round 7b (the hostile-driver and mail results of round 7)

* `HeadDeadline`: one time limit for the whole head of a request (a client that drips one byte at a time is cut at the
  limit, not after the last byte).
* `RecursionError` (deeply nested JSON) is a bad request (400) at the demo servers, not a trace.
* `demo_only/burst.py` against a closed port looks for a listener for a few seconds, then ends with one line and
  exit code 3 (it used to retry for 30 s without output).
* The portal reads the made-up CRM view of a big run whole (the cap comes from `constants.py`).

## Round 7 (exit codes, bad requests, class names, the mail path)

* Script exit codes: one number per meaning (`EXIT_*` in `constants.py`); a script never ends with a bare number.
* Fake servers: a bad body or query is one fixed 400; the whole request body has one time limit
  (`FAKE_BODY_DEADLINE_SECONDS`).
* `demo_only/burst.py --url` is refused unless it is on this computer, before any name lookup.
* A stored error code never holds a Python or library class name (`lead_desk/errcode.py`); an ast test lists every use.
* Mail path: user, TLS floor, secret reading, size caps (see `tests/test_r7_mail_context.py`).
* `scripts/start_all.sh` checks that what it started owns its port (exit 3 and stops what it started otherwise).
* The file-call guard (`tests/test_file_call_guard.py`) plants 201 shapes in all (81 added in round 6, 17 in round 7;
  `len(PLANTED)`) plus the bare `.read()` of a web reply; each must be found by the ast walk.

## Round 6 (checks of a key, a TLS setting and a log, at the one shared place)

* A key or password with a non-ASCII character is refused, in the file reader and for the environment value, before
  any money is reserved (`regfile.secret_text_ok`).
* The SMTP provider checks the TLS context again when it connects; a CA file together with a ready-made context is
  refused; the mailbox user with a control character is refused.
* The n8n API key and the HubSpot probe token go through the shared key checks.
* One constant per number: the second `REPLY_MAX_BYTES` is now `SCRIPT_REPLY_MAX_BYTES` (4 MiB, for lists that can be
  longer than 1 MiB). New: `FAKE_BODY_MAX_BYTES`, `FAKE_SOCKET_TIMEOUT_SECONDS`, `LOAD_LINE_MAX_BYTES`,
  `EXIT_LOG_TOO_LONG` (4), `START_CHECK_TRIES`, `START_CHECK_PAUSE_SECONDS`.
* The three demo servers read a request body through one bounded helper (`scripts/http_guard.py`).
* `check_invariants` reads a log one line at a time and stops at the row cap with exit code 4.
* Refusal and status lines no longer print class names or typed text.
* `scripts/start_all.sh` waits for the desk with a bounded poll and ends with exit code 3 when it does not answer.
* The file-call guard test resolves aliases, `getattr` and `__import__` with literal names, and path readers
  (`tests/test_file_call_guard.py`, 81 planted shapes).
* Suppressions added in round 5 for E402 are removed in the scripts and tools (see RESULTS.md for what is left).
