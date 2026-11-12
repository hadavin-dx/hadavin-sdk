# Ticket Q8a1-CARD-FIXTURE: check the approval card against the demo repositories' own card fixture
Opened 2026-11-12 by the batch-16 builder of Q8a-1 (r15 Issue 4). Due: 2026-11-19 (UTC and IST: end of day).

What is already checked in this repository (`tests/test_guard_reasons.py`, `check_card`): the card producers (`approvals/cards.py`, `approvals/requests.py` summary) and the Slack channel code (`approvals/slack_channel.py`) put into the card, and into the body sent to Slack, only the plan fields the approver must read. A canary text is put into every other field of the plan, the gate decision and the approval request; the test fails if it shows up.

What is not checked here (this ticket): that the cards the demo repositories (intake, refunds, dealdesk, apexc) actually produce with their own plans and their own fixtures also hold no configured name beyond those plan fields. That needs each demo's card fixture, which lives in the demo repository, not in this one.
Next step: the owner's lead copies each demo's card fixture (made-up data only) into `tests/fixtures/` of this repository through a core PR, and `check_card` renders them too. Blocks: closing the card half for the demos only; it does not block the core guard.
Owner item that stays open: `REDACTED` (question q-q8a1-hide-ids).
