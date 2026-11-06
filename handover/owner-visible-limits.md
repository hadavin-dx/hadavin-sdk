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

## 2. A scanned PDF with a few unreadable picture pages can be read with those pages left out
- **What the program checks.** When the kit reads a PDF, it counts the pages it could not turn into text. A document where most pages are pictures goes to a person.
- **What it does not check.** Up to 1 in 10 such pages can otherwise be left out without a person being told (in a 300-page PDF, up to 30 pages). The report shows how many pages were left out, but nothing stops the document from being used.
- **What a person must do, and when.** Before the first pilot, a person decides whether 1 page in 10 is acceptable for that client, or asks for a lower share (for example 1 page in 50), which sends more mixed documents to a person. The share is a setting and stays at 1 in 10 until it is measured on real documents.
- Studio reference: package AK2a, PENDING LEAD 9 (i), lead order 34 item 76.

## 3. A name written as several words can be cut into two passages
- **What the program checks.** Each passage cut from a document is checked for masking on its own.
- **What it does not check.** A value written as several words, such as a two-word name, can be cut into two passages. A name the system knows only as a whole may then be sent in parts, because neither part alone is recognised.
- **What a person must do, and when.** Before the first pilot, a person checks on the client's sample documents whether names are cut this way, and tells the studio if they are.
- Studio reference: package AK2a, PENDING LEAD 9 (ii), lead order 34 item 76.

## 4. After a crash, a store fault or a queue outage during an answer, the chat continues with a person
- **What the program checks.** If an answer in a chat is cut short by a crash, a fault in the data store or an outage of the queue that holds work for people, the program does not let the agent answer that chat again by itself.
- **What it does not check.** It does not try to finish the interrupted answer. A person sees the chat, not the missing answer.
- **What a person must do, and when.** When such a chat appears in the queue for people, a person reads it and answers or closes it. A client must be told before the pilot that this can happen.
- Studio reference: package AK-G1, PENDING LEAD 14 (option (a), lead order 36 item 82); PENDING LEAD 2(vii) is withdrawn.

## 5. Erasure takes priority over the evidence hold for chat content
- **What the program checks.** When a person asks to be forgotten, or the retention time of chat content ends, the program deletes that chat's stored text, masked-value maps and tool call records, even when an evidence hold names the run. The run's row and its labels stay. The deletion happens before the hold is checked.
- **What it does not check.** It does not decide whether a legal hold should override erasure. This choice has not been reviewed by counsel.
- **What a person must do, and when.** Before the first pilot, counsel reads this rule and says whether it fits the client's duties.
- Studio reference: package AK-G1, PENDING LEAD 15 (option (a), lead order 36 item 82), owner rule R98.

## 6. Documents larger than about 27 KB are refused by the model-call size limit
- **What the program checks.** Before a document goes to a model, the program checks that the whole request stays under the prompt size bound (100,000 bytes). To keep that promise it lowers the document size limit (`MAX_DOCUMENT_BYTES`) from 262,144 bytes to 27,872 bytes. A configuration may only lower this limit further, never raise it.
- **What it does not check.** Documents between about 27 KB and 256 KiB, which were accepted before, are now refused. Tool results (up to 262,144 bytes per run) can still push a call past the bound; that call then fails closed (the run stops and a person looks) instead of being sent.
- **What a person must do, and when.** Before a pilot, tell the client the size limit. A person must split or shorten a refused document, or the lead must decide to raise the prompt bound (a money and redaction decision, not a configuration change).
- Studio reference: package P4c, PENDING LEAD 25(a) (order 24) and the new PENDING LEAD 28 and 29.
