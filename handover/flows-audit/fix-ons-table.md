# fix-ons-table

Static fix. No cell was missing: in 7 rows (CLAIMS-TABLE.md 713-719, lanes13/claims-B.md 360-366) the verdict and the reason were joined in one cell with no `|` between them. I added the `|` at the join and kept every word. Nothing is "not recorded". Checked against the evidence file: it does not cover these rows; the source lane has the same joined text.

Not checked: whether the verdicts are right (unchanged). I did not run evidence-claims-r2.md checks.

Column check (run with `python3 -I`, 4-cell header vs each row):
CLAIMS-TABLE.md offenders 0
lanes13/claims-B.md offenders 0
(before: 7 and 7)
