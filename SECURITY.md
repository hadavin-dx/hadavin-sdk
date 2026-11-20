# Security

Please report a suspected vulnerability privately through GitHub: the **Security** tab of this repository,
**Report a vulnerability**. If that button is not shown, open an issue titled "Security contact request" with no
details, and a private channel will be arranged. Do not post vulnerability details publicly.

Reports are answered within 5 working days.

## What the core does and does not guarantee in pilot and prod (this round)

**Audit (stated limits).** The audit log is eventual, not instant. An event that could not be written to the audit
chain is parked in the outbox table and written by the next tick (step `audit_drain`). An event parked only in a
process's memory (the database was down for the outbox as well) is written at that process's next successful audit
write, and is lost if the process exits first. That write is not capped: after a long outage the next audit write
of a process also writes every event that process parked. Events a process could not write for a reason other than
an outage are kept in memory, counted in a warning, and lost when the process exits. An outbox row the database
refuses for such a reason is kept and fails the `audit_drain` step with a count. The eval and replay commands do not
write to the chain.

**Stop.** A stop takes effect at the next gate check; a call already in flight is not interrupted; the command-line
eval and replay paths do not read the stop state. On PostgreSQL with the grants applied (`migrate --reset-role`), the
runtime's database login can add a stop and cannot clear one; only the reset login can, and its reset is written to
the audit log first. The reset login can append audit rows (as the runtime login already can). The database owner and
a superuser are outside this guarantee. The memory store guarantees nothing. Stated limits: (1) the guarantee is about
the state stored in the database, and the store names its schema in every stop-state statement so a temporary table
cannot hide a stop; a runtime process that is itself taken over can ignore any switch, so stop the process as well.
(2) "Audited first" is done by the `limits reset` command; the database does not force it, so a person holding the
reset login can clear a stop by hand with no audit row. (3) The reset login cannot add a stop row, but it can set the
old flag ON, which is also a stop (the safe direction). (4) A reset clears the stops visible to its clear statement:
a stop committed after that statement began stays ON, and one committed between the audit row and that statement is
cleared; the command reads the state back and exits 2 while it is still ON. (5) `migrate` refuses, when it applies
grants, any other role that could clear a stop; a plain `migrate` that names no role applies and checks no grants and
leaves old ones in place, so name all roles in ONE command.

**Not guaranteed by the core this round.** In pilot and prod the approved write is performed by the client's own tool
(for example n8n or the CRM) with its own credential, not by the core. For that write the core therefore does NOT
guarantee: that the write matches the plan that was shown; that the named approver approved it; that it happened
exactly once; that the stop switch halts it; that it appears in the core's audit log. These belong to the client's
tool and its own log. Nothing in this package's texts may claim otherwise.

## Stated limits of redaction (reviewed, not bugs)

Redaction is pattern based and treats the end of a value the way the redactor's own value pattern does. Two consequences are known and stated:

- A secret value that itself contains a plain (not encoded) space, `;`, `,` or `&` (for example `password="my secret phrase"`) is masked only up to that character in pass one: its tail is shown, because by the redactor's definition the value ended there. Put such a secret in quotes handled by the pattern, or do not hand it to a tool.
- A form-encoded `;` or `&` inside a value is ambiguous: `password%3Dab%3Bzq9` can be one secret or a key and a value followed by more text. The redactor decodes it, masks what its value pattern reaches, and keeps what pass one masked whole when the decoded view would mask less; it cannot know which reading the sender meant.

Control that does not depend on these limits: a tool is not handed a secret it does not need (least privilege).
