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

## 7. A chat answer that takes longer than about 16 minutes is treated as lost
- **What the program checks.** The program refuses the slow answer's final write and hands the chat to a person.
- **What it does not check.** It does not pull back a reply that is already being sent.
- **What a person must do, and when.** A person reads the chat when it appears in the queue for people; the client is told before the pilot.
- In plain words: If one answer takes longer than the agent's time limit (about 16 minutes with the normal model settings), the system treats that answer as lost. A person takes over that chat, and the chat history shows '[no answer was given]'. The customer may already have received that slow answer, or may still receive it shortly after, because a reply that is already being sent is not pulled back.
- Studio reference: PENDING LEAD 2(vi)/lease fence, order 39 (lease token = the existing version column).

## 8. A short database or audit fault sends every chat in progress to a person
- **What the program checks.** The program stops answering by itself in every chat whose answer was in progress during the fault.
- **What it does not check.** It does not retry the answers or give the chats back to the agent.
- **What a person must do, and when.** A person reads each handed-off chat in the queue; the client is told before the pilot.
- In plain words: If the database or the audit store fails for a moment, every chat that was being answered at that moment goes to a person, not just one.
- Studio reference: design AK-G1, crash rule 5.

## 9. The money alert card can be missing after a crash at the wrong moment
- **What the program checks.** The program pauses the chat and records the money reason before it posts the card.
- **What it does not check.** It does not guarantee the card after a crash in that moment.
- **What a person must do, and when.** A person who looks at the run record sees the money reason; the operator checks for paused chats without a card.
- In plain words: When a chat pauses because of a money limit, one alert card is posted. If the system crashes in the moment after the chat pauses, that card can be missing; the run record still shows the money reason.
- Studio reference: design AK-G1, step E7.

## 10. Deleting a person's chats is refused while one of their messages is being answered
- **What the program checks.** The program refuses the deletion with 'busy' while an answer is in progress.
- **What it does not check.** It does not delete in the middle of an answer. (Amends limit 2(vi) of the ticket.)
- **What a person must do, and when.** The caller tries again later.
- In plain words: Deleting a person's chats is refused while one of their messages is being answered. After a crash this can last up to about 16 minutes, and the caller must try again.
- Studio reference: design AK-G1, forget_user.

## 11. A message sent again under its old id can be refused after a settings change
- **What the program checks.** The program refuses a re-sent message whose stored fingerprint no longer matches.
- **What it does not check.** It does not accept the old id after such a change.
- **What a person must do, and when.** The sending app sends the message again under a new id.
- In plain words: After a change to which kinds of personal data are kept, or to the deployment's secret key, a message sent again under its old message id may be refused. The sending app must send it again under a new id.
- Studio reference: design AK-G1, text_digest.

## 12. A chat that waits longer than the retention period for a person is deleted
- **What the program checks.** The program deletes chats by age, as for every chat.
- **What it does not check.** It does not keep a chat because its 'needs a person' item is still open.
- **What a person must do, and when.** The client agrees in the contract that a person answers within the retention period.
- In plain words: A chat that waits longer than the retention period (30 days unless the client contract says otherwise) for a person is deleted with its history, even if no person has answered it yet. The client contract must require the queue's service time to be shorter than the retention period (`conversations_days`).
- Studio reference: order 39 item 2 (a)+(c); design AK-G1 NEEDS LEAD 2.

## 13. Nobody is told when a new "needs a person" item arrives
- **What the program checks.** The program keeps every item that needs a person in its queue. Its regular check, which runs on every tick (the program's repeating background run), fails loudly when an item has waited longer than the agreed service time, or when a waiting item belongs to a client set-up with no named queue readers.
- **What it does not check.** It sends no notice when a new item arrives. Until the service time has passed, nobody is told.
- **What a person must do, and when.** Before the pilot, the client names who looks at the queue and how often, and the quote says so.
- Studio reference: package AK-G15, owner-visible limit 13, `queue_watch` step; lead order 43 item 14.

## 14. Until the approvals screen exists, a person can act on a queue item only through code the studio runs
- **What the program checks.** Every action on an item (take it, give it back, close it, open it again) goes through checked code that records who did it.
- **What it does not check.** There is no screen yet. A client's own staff cannot act on an item by themselves.
- **What a person must do, and when.** Until the approvals screen is built, a studio person runs the action for the client, or the pilot waits for the screen.
- Studio reference: package AK-G15, owner-visible limit 14 (screen = ticket G14); lead order 43 item 14.

## 15. Running a message again can cost money again, and can propose an outside action again
- **What the program checks.** A person who closes an item with "run again" starts a second paid run of that message. If the earlier run may already have acted outside the program (for example sent something), the person must confirm that they saw a warning first, and the approval step for any outside action still applies. One message can be run again at most 3 times by default; the client can set this from 0 to 10, and the database refuses any number above 10.
- **What it does not check.** It does not know whether the earlier outside action really happened. It does not stop a second run within the limit.
- **What a person must do, and when.** Before the pilot, the client agrees the limit. The person who runs a message again reads the warning, and an approver checks any outside action again before it happens.
- Studio reference: package AK-G15, owner-visible limit 15; PENDING LEAD 16 (a), lead order 43 item 16 (`queue.max_reruns` default 3, range 0-10).

## 16. The queue trusts the person the screen names
- **What the program checks.** Each action records the person id the calling screen gives, and checks that this person is a current queue reader for that client.
- **What it does not check.** The queue does not log anyone in. Whoever holds the queue's database password can act as any queue person and can ignore the time limit on a taken item.
- **What a person must do, and when.** The screen must check who the person is before it calls the queue. The queue's database password is kept only in the secrets store and given to the screen alone.
- Studio reference: package AK-G15, owner-visible limit 16; lead order 43 item 14.

## 17. An item can point at content that was already deleted
- **What the program checks.** When the chat or message an item points at was deleted (because its retention time ended, or because a person asked to be forgotten), the program shows "content erased" and allows the item only to be closed.
- **What it does not check.** It does not keep the content alive for an open item. Deletion wins over the queue.
- **What a person must do, and when.** The person who sees "content erased" closes the item and, where needed, contacts the sender by another way. The client is told before the pilot.
- Studio reference: package AK-G15, owner-visible limit 17; lead order 43 item 14.

## 18. Closed queue items are kept for ever in this version
- **What the program checks.** A closed item holds ids, a reason code, times and the staff names of the people who handled it. It holds no message text.
- **What it does not check.** Nothing deletes closed items in this version.
- **What a person must do, and when.** Before any pilot, the owner decides how long closed items are kept, together with how long received-message records are kept (the lead takes this decision to the owner).
- Studio reference: package AK-G15, owner-visible limit 18; PENDING LEAD 17 (a), lead order 43 item 17; later row V4.

## 19. The check that a person sees only their own clients' items is done by our code, not by the database
- **What the program checks.** Our code and our database queries return only the items of clients for whom the person is a current queue reader. Tests try to read another client's items and must fail.
- **What it does not check.** The database itself does not filter rows per person, because one database login serves every queue person. A fault in our code could show another client's item.
- **What a person must do, and when.** Before the pilot, the client is told. If a client's security review asks for database-level filtering per person, the studio builds it first (later row V7).
- Studio reference: package AK-G15, owner-visible limit 19; PENDING LEAD 11 (a).

## 20. A closed item about a received message keeps a coded form of the sender's id, and so do the message records
- **What the program checks.** The item stores the sender's id only in a coded form made with our secret key, never in plain form. In pilot and production the key always exists; only on a developer's machine can a plain coded form without the key appear.
- **What it does not check.** Whoever holds our key and a sender's original id can match the two. The records of received messages keep the same coded id for ever in this version, so removing it from the item alone would not remove the link. After a person asks to be forgotten, a chat item still holds a conversation id that points at nothing; whether another record still links that id to the person has not been checked yet. The staff names in an item are personal data of the client's staff.
- **What a person must do, and when.** Before any pilot, the owner decides how long closed items and received-message records are kept (limit 18), and the key is held only in the secrets store.
- Studio reference: package AK-G15, owner-visible limit 20, Security notes "Personal data (rewritten, R1-ADV-7)"; PENDING LEAD 17 (a), lead order 43 item 17.

## 21. Someone who takes over the agent's own database login could plant a fake waiting item that hides a real hand-off
- **What the program checks.** The regular check counts every waiting item of a client, whoever it names as readers, and fails loudly once the fake item waits longer than the agreed service time. The client's current queue readers can see and close it.
- **What it does not check.** Until then, the real hand-off is not listed on its own. A program that never reports a hand-off at all is outside what the queue can catch.
- **What a person must do, and when.** The agent's database password is kept only in the secrets store. A person who sees an unexpected waiting item reports it to the studio as a possible break-in.
- Studio reference: package AK-G15, owner-visible limit 21 (R1-ADV-1, remaining part); lead order 43 item 14.
