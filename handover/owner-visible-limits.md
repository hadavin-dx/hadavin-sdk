# Limits the owner should know about before any pilot

This file lists, in plain words, what the core program does NOT protect against. The lead shows it to the owner before any pilot with real client data (lead order 24 item 39).

How to add an entry: append one entry per limit at the end, numbered. Each entry says what can go wrong, what the program checks, what it does not check, and what a person must do, and when. Write for a reader who has never seen the code. Put the studio reference (package and decision) on the last line of the entry. Do not edit another author's entry; add a new one if it changes.

## 1. A password or a person's name typed into a configuration file can appear in an error message on the screen

Added 2026-11-06 about 04:00 UTC (09:30 IST).

- **What can go wrong.** When a configuration file is wrong, the program stops and prints a short message that our own code writes. Most of these messages name a file, a setting or the name of a secret, so that the person running the program can fix the problem. If someone types a password, a web address that contains a login, or a person's name into a place where the program expects a name or a path, that value can appear in the message on the screen.
- **What the program checks.** The message must be one line of plain letters, digits and punctuation. A message that breaks this rule is replaced by a short coded line that holds no typed value.
- **What it does not check.** It cannot tell a password or a person's name from an ordinary name. A wrong value that looks like an ordinary name passes.
- **What a person must do, and when.** Before the first pilot with real client data, a person re-reads every such message in the code and checks that none of them can print a password, a login or a person's name. If one can, it is rewritten to fixed words before the pilot.
- Studio reference: package P5b3, its decision 19 (option (a)), lead order 24 item 39, follow-up row P5b3-V1.
