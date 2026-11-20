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
