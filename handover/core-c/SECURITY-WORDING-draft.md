# SECURITY and README wording for steps F and G: DRAFT for the lead (core-c, 2026-11-20)

Rule followed: never claim more than the evidence shows; each positive sentence enters with the step that makes it true (plan-v4-final B3). SECURITY.md and README are not TEXT's files except the fold's own entries: this is text for the lead or SPINE to place.

## Masked model input (after step F install and step G)
"Values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor." (lead wording, ORDER 007)

What this does NOT promise (each is pinned by a named test; the list is checked against the code by the gate fix agent and may still change):
1. It is not "nothing secret can reach a model". The patterns catch the named kinds only; a secret no pattern matches is not seen anywhere.
2. The gate replaces only values already in the run's map. It does not look for new values.
3. Not replaced by the gate even when known: values shorter than 3 characters, digit strings shorter than 6, common words, and identifier-kind values that touch a letter or digit (`xabc1234` when `abc1234` is known).
4. A known value written in an encoded or look-alike spelling passes the gate. The fold scan (step G3, at the producers) is the control for look-alike spellings; base64 is covered only after part G4.
5. Two known values that overlap in the text (`abcd` and `cdef` in `abcdef`) can leave a tail of one of them.
6. A key and a value that are each clean but match a pattern once joined into one JSON string are not touched.
7. System prompts and tool schemas are operator text: never masked, never checked.
8. With no run map (eval and replay command lines, the judge with its own map) the gate does no replacement at all.
9. The vendor guardrail call (Bedrock) does not go through the gate.

## Redactor (step G)
- Look-alike and hidden-character spellings of a value are found by folding the text before the pattern pass (G1, G3). A line that cannot be masked in place is withheld whole with a fixed note.
- One pass is enough for a bank account beside a bank code only after part G7 (before it, a second pass was needed: found 2026-11-20).
- `redact_untrusted` must not be applied to its own output with its hook: it escapes genuine placeholders. Caller list: tickets/G7-context-after-sweep.md (being written). Status today: UNVERIFIED that no caller does it.
- A bare number with no label (`ref 55556666 paid`) is not masked, by decision.
- A non-private host name with no host key in front of it (`db01.acme.example`) is not masked.

## Requirement
Pilot and prod need a Python whose Unicode data is 15.1.0 (Python 3.13). On another version the start-up check refuses to start. Python 3.12 carries 15.0.0 (measured in this box).

## Capped spend at the gate (wording for SPINE's guarantee sentence; the money logic is theirs)
The gate makes no model call without a reservation. It settles the real cost when a reply came back, settles 0 only when the adapter marks the error as refused before any response (the mark does not exist yet: requests/2-refused-before-response.md), and otherwise does not settle: the reserved worst case stays booked until the store sweep closes it.

---
## REVISION 2 (06:25 UTC), after the gate review fixes (f16d48e) and G7 for the whole class (4864984). Where this differs from the list above, this wins.

### Gate: corrections to the stated limits (checked against the redactor's sweep rule by the fix agent)
- Limit 3 above was too wide. Correct wording: "Not replaced by the gate even when known: values shorter than 3 characters; all-digit values shorter than 6; common words (`prod`, `admin` and the like); and, for identifier kinds only, a copy that a letter or digit touches. A value of a SECRET kind with 4 or more characters is replaced in every copy, also inside a longer word."
- New: "A reply whose cost is missing, negative or not a number is returned, and its reservation is not settled: the reserved worst case stays booked."
- New: "A failed call keeps its worst-case reservation booked until the store sweep closes it (about an hour), because the model adapters do not yet say whether a request was refused before any response." (requests/2-refused-before-response.md; this sentence goes away when core-b adds the mark)
- Fixed, no longer a limit: a known value that happened to be a piece of a placeholder token was rewritten into it; found and fixed in the review round.

### Redactor after G7 (from tickets/G7-context-after-sweep.md, "For SECURITY wording")
- "Redaction is at most two pattern passes and two sweeps per call, not a fixed point. A value that would need a third pass stays readable after one call. Known shape: a chain where a value found only by the second pass is itself the context of another (a bank code glued to a secret, then the account after that code elsewhere). Such text has to be planted on purpose." Pinned as a strict expected failure.
- "When a longer credential is found only because a shorter known secret inside it was masked first, other copies of the longer one elsewhere keep the part after the shorter secret readable (`<SECRET_1>tail`)." Pinned as a strict expected failure.
- "A value made only of escaped placeholder look-alikes (`‹KIND_n›`) is never treated as a credential." So a credential spelled exactly like that is not masked.
- "A tool error text is redacted twice (once with a throw-away map, once with the run's map): its placeholders reach the model escaped, not numbered in the run's map."
- Replaces the line "One pass is enough ... only after part G7": G7 is built; one pass masks a bank account beside its code and a token tail after a known secret.
- Cost, measured: about 2 times the redaction time on text with matches (100,000 characters: 0.206 s before, 0.484 s after), unchanged on text with none.

### Approval cards after P1d-a (G2), pending the lead's answer on the channel.py commit
- "On every approval text path the redactor runs before addresses are defanged; `[.]` is written last." (27 path tests)
- Not fixed, QUESTIONS 15: an e-mail address with a digit or underscore glued behind it (`anna.m@example.org9`) is masked neither for the model nor on the card.

### Honest note on the evidence behind these sentences
The idempotence property test covers 1,835 existing hostile and fuzz inputs; none of the older inputs ever held the class G7 fixes, so the proof of the fix is 8 new shapes, and both remaining limits came from 5 hand-built chains, not from a corpus. The chain search was not exhaustive.
