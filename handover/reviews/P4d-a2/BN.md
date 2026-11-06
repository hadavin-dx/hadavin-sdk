# Ticket errors (P4d a2/b)
- Ticket orders a2-i/b without a2-ii, yet lead/order 86 lists StoreBusy (an a2-ii item) as needed by b; StoreBusy not built here.
- round_cost_up spec leaves exponent >= -8 values unspecified; I return them unchanged (else 0 prints as 0.00000000, breaking k1b replay tests).
