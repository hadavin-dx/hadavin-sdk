# REVIEW.md 408-449 round 47c stranger read (egm-comprehension), security path. Saved by flows-audit, condensed; unverified; static. NOT read: 450-550, anything before 408. 1 "Blocker", 10 Majors.
B1 L423,425,429-433,443-444: gating words (criterion (1)-(8), "the chain of Decision 1", "block of Decision 1") not defined in range. (Reader's own count of 10 YES / 14 NO matches the flags.)
M2 L408 "none is closed by this file" vs L413 "Closed: test_store.py:237 read (see X-6)".
M3 OL-10 L432: ssh-keygen missing, needs machine with OpenSSH, no owner/date; hold-gating item with default "none".
M4 OL-15 L437: default restates the question; no date.
M5 OL-11 L433: default vs RECOMMENDED for pilot unclear; gates NO yet "can change what is on the chain".
M6 OL-22 L444: unread defaults "stand"; contradicts L421 "a default is never a yes"; undefined terms.
M7 OL-3/OL-4 L425-426 both labelled Z14, two different questions.
M8 OL-18 L440 time "with OL-3 and OL-4" which have different due times; gating unclear.
M9 OL-7 L429 vs L449 order and Decision 26 date (dependency cannot be met on schedule).
M10 OL-19/OL-21 L441/443: today-due builder name; no time.
M11 OL-24 L446: "first four items" not identified; overlaps OL-23/OL-8; "10 of 24" may understate.
Minors: L409 "41 cases" ambiguity (41 vs 42); undefined heavy lane, evidence runner, facts reviewer (L409-410; commit id line not printed); OL-1 mixed gate counting; L416 "directly below"; L449 no cycle found.
