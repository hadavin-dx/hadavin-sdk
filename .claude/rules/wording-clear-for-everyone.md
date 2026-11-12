---
name: wording-clear-for-everyone
description: "Owner 2026-11-03 HARD RULE: every word we write (owner replies, docs, demos, client text, agent briefs) must be precise and understandable by any technical or non-technical reader; no ambiguous labels"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-03T16:12:11.469Z
---

Owner 2026-11-03: wording is very important; unclear words cause confusion and readers may think wrongly. From now on always prefer perfect wording that anyone, technical or not, can understand.

**Trigger:** the owner read "bank-detail change" in the Apexc pitch and thought we were selling to banks. It meant a supplier's bank account details printed on an invoice. The label itself caused the wrong reading.

**Rules (apply to owner replies, plans, READMEs, demo text, client text, LinkedIn, error messages, agent briefs and reports):**
1. Say what the thing IS in plain words the first time; use a name only after it is explained. Example: "changed supplier payment details (the bank account on an invoice)", never a bare "bank-detail" or "D10".
2. One word, one meaning, everywhere. If a word could be read two ways (bank, account, approval, window, gate, receipt, queue), add the missing noun or rename it.
3. Say who does what to whom. Avoid passive and vague claims ("is handled", "is secured"); say what we check, what we do not check, and what a person must do.
4. No jargon, internal codes or abbreviations in owner-facing or client-facing text unless explained in the same sentence (invariant names, WP numbers, ledger ids, R-numbers go in the studio notes, not in the message to the owner or in client text).
5. Short sentences, concrete examples, numbers with units; times in UTC and IST.
6. Never claim more than the evidence shows; plain limits beat clever wording (see [[honest-tamper-evidence-claims]], [[bible-before-answering]]).
7. Before sending any owner-facing or client-facing text, re-read it as a person who has never seen the project: would they understand it and could they misread it? If yes, rewrite.

**Terms to use from now on:** "supplier payment details" (not "bank detail" or "bank change" alone); "approval by two different people" (not "two-person approval" without explanation); "a person must look" (not "NEEDS_PERSON" in prose); "the list of made-up files" (not "hash list"); "our own code decides" vs "a ready-made tool does it" (not "rung 3").

**How to apply:** also appended as rule 14 of `templates\agents\BRIEF-PREAMBLE.md` so every agent follows it; existing docs are cleaned when touched (Apexc plan, Intake README, owner sheet, demo scripts, website copy). Related: [[async-first-client-comms]], [[owner-solo-ai-studio]].
