# fix-2 r9 reviews (saved by lane3 from the inline reports), tree 047715c5
## egm-design: 0 blocker, 1 major, 4 minor, 3 nit
M1 plan row 4 half done: no test for a book path INSIDE a file; run_real_check.py:860-865 uses path_kind, ENOTDIR counts as absent (envnum.py:48) so it is not refused; notes row 4 says it is. (CONFIRMED by lane3 reading the tree.) Fix: use envnum.env_file_problem; tests.
m1 repeat scan case-sensitive, line-based, needs a key-file word on the same line (tests/test_one_key_file_rule_r8.py:417-441).
m2 two old-code passes unlabelled (order test, no-way-round test); link half proves little; stale test ids in notes (third mode 0o700).
m3 smtp "no demo server is called" test does not run server.main: claim in contract.md/limits.md not covered.
m4 many r9 tests pin docs text only; counts mix text pins and behaviour.
Nits: ragged docstring envnum.py:117-119; folder text lost "(the lead-book file)"; "point the setting at the copy" vs --key-file flag.
Right: rule text in one place (settings.md:113-115 only); mode message plain, no path; read_secret_file sound (race, link, fd, FIFO, bounded read, fixed messages); residual risks documented (owner not checked, ACLs, device open side effects).
## egm-codebase-details: 0 blocker, 0 major, 4 minor, 5 nit
Verified: all key reads through read_secret_file (six call sites); DryFakes keys 0600; open/check order correct; refusal texts fixed, no path; BOOK_* constants gone; tests use mod.EXIT_REFUSED; twin test can fail (but does not prove real EACCES maps to unreadable); guard widening and wrapper tests present; 22 old-code passes counted correctly (18+4).
Minor: docs/settings.md:92 "the mode alone says who else can use the file" overclaims (ACLs, root); unreadable refusal rests on a root-skipped test; smtp claim only tested up to check_secret_files; lead-book test loops over a one-element tuple.
Nit: docstring wrap; RULE_WORDS case-sensitive and line-based; text always says copy even where chmod suffices (lead's choice a); run_real_check:863,865 own wording; REGRESSION GUARD marker on 3 of 22 in code.
Not checked: docs/settings.md:106 hardcodes "2 refused at the start" (changes to 8 with fix-10 at stack time: stack docs must follow).
