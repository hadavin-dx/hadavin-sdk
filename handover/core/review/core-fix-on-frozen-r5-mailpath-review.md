# R5 secrets / TLS / mail path review, pass 3 (FALLBACK general-purpose a aee26a5b; PARTIAL; condensed by core lead)
Not finished: mutation run 12 of 27 judged (box load ~110 on 4 cores); fail-on-old-code only shown as collection ImportError (no behavioural proof); file-replaced-during-read not raced (read-only: one bounded read(4097) on the open handle); audit/desk logs not probed; ran as root (permission-denied via setpriv uid 65534). Suite on new tree: 280 passed.
Probed OK: FIFO/symlink-to-FIFO/dev-zero/socket/dir/NUL/5000-char/surrogate names all refused <5 s with fixed text; 10 MB and sparse 1 TB refused; secret content shapes agree across SMTP/IMAP/HubSpot/live key except F1; real loopback handshakes (pinned CA ok, other CA refused, hostname mismatch refused, named CA replaces system store, CERT_NONE contexts refused at construction (SMTP) / before connect (IMAP)); run_live_check bad key -> one line rc 2, no ledger, 0 connections; no path/secret/traceback in outputs.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| F1 | MAJOR (money path) | regfile.py ~92-96 | non-spaced reader accepts non-ASCII key; LiveQualifier writes a reserve line to the ledger and only then fails at header encode: cap consumed, never settled | require secret.isascii() both modes; test: refused before reserve, ledger empty |
| F2 | Minor-Major | smtp_provider.py:184-186,275-279 | ssl context checked only in __init__; weakened afterwards it is used (password sent to wrong-name server); IMAP re-checks each call | call require_verifying in _wrap on the context used |
| F3 | Minor | smtp_provider.py:188 | ssl_context plus ca_file: ca_file silently ignored | refuse the combination |
| F4 | Minor | scripts/n8n_api.py:106-128 | own divergent key reader (BOM refused, 5-char key accepted) | use read_secret_line |
| F5 | Minor (read-only) | scripts/hubspot_probe.py:325-330 | env token checked only for empty/CR/LF/space | shared check_secret_text |
| F6 | Minor (read-only) | imap_count.py ~60 | user name not validated at library level (imaplib 3.12.3 refused CRLF) | reject control chars in settings class |
| F7 | Info | tls_trust.py ~84 | cert_store_stats guard dead code; mutant survived | keep or delete |
| F8 | Low test gap | tls_trust.require_verifying | verify_mode check mutant survived; CERT_OPTIONAL + check_hostname=True untested | add test |
| F9 | Info | | IMAP CA failure class ImapConnectionError (harmless) | none |
Survived mutants: no cert_store guard; require_verifying verify_mode test; unbounded secret read (4 KB bound not tested directly). Unjudged: 15 mutants incl. blank-CA SMTP/IMAP, no require_verifying SMTP/IMAP, live ordering, IMAP default-unverified.
