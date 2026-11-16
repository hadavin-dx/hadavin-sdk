"""Texts for build_c6q.py (kept apart so the build script stays readable). Plain data; no file is read or written here."""

def wc(s):
    return len(s.split())

C1 = "A lead sent twice with the same id is processed once."
S1 = "We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim."
R2 = ("The 45 seconds is a setting called the lease. It only sets when a second program, checking every 30 seconds, may claim a stopped contact again. "
      "A second send of the same contact is not processed again, whenever it arrives.")
L2 = ("When the system cannot tell whether a contact was fully handled, it sends an alert, a warning mail that asks a person to look. "
      "We make no statement about how quickly an alert mail arrives.")
L3 = "The made-up name and e-mail address sent to n8n may stay in n8n's own database; we did not measure for how long."
L4 = "Not tested: other mailboxes, other customer-record systems, alerts sent as chat messages, other lease settings. One machine, made-up people, our own runs."
# option (b), shorter card
B_L1_NONE = C1
B_L2 = "When the system cannot tell if a contact was handled, it sends an alert, a warning mail asking a person to look. We say nothing about how fast it arrives."
B_L3 = "The made-up name and e-mail address may stay in n8n's database; we did not measure for how long."
B_L4 = "Not tested: other mailboxes, other systems, chat alerts, other lease settings. One machine, made-up people."
CAP_NONE = "a lead sent twice with the same id is processed once"
CAP_R1 = "a lead sent twice with the same id is processed once (claimed only when the second send comes within 45 seconds of the first)"
CAP_R2 = "a lead sent twice with the same id is processed once (the 45 seconds is a setting called the lease, not a limit on repeats)"


def secs(words):
    return words / 150 * 60


def budget(words):
    s = secs(words)
    b = int(s // 5) * 5
    if b < s - 1e-9:
        b += 5
    return b


def table():
    """rows: (lease answer, length, words, seconds text, budget, total)"""
    a_rest = wc(L2) + wc(L3) + wc(L4)
    b_rest = wc(B_L2) + wc(B_L3) + wc(B_L4)
    l1 = {"none": wc(C1), "1": wc(C1) + wc(S1), "2": wc(C1) + wc(R2)}
    rows = []
    for k in ("none", "1", "2"):
        for ln, rest in (("(a)", a_rest), ("(b)", b_rest)):
            w = l1[k] + rest
            rows.append((k, ln, w, "%.1f" % secs(w), budget(w), 150 + budget(w)))
    return rows


if __name__ == "__main__":
    print(wc(C1), wc(S1), wc(R2), wc(L2), wc(L3), wc(L4), wc(B_L2), wc(B_L3), wc(B_L4))
    for r in table():
        print(r)
