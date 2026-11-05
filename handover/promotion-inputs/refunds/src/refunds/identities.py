"""Least-privilege identity table (owner HARD RULE 2026-11-01; design review M7). Deny-all start: an action not listed for an identity is denied.

Each identity has an exact allow-list (stage 1 has NO credentials: the caller asserts a label; stage 2 gives each identity its own credential), exact allowed actions (no wildcards), a policy text and a per-action justification. `authorize` is the
stage-1 policy decision function; stage 2 binds the same table to real credentials (short-lived, passkey MFA for the human approver). The
negative tests (tests/test_identities.py) prove each identity is denied what it must not do and that no identity both approves and executes.
The model-facing tool set is `tools.REGISTRY`; `execute_approved` is not in it and no model-facing identity may call it.
"""

from __future__ import annotations

ACTIONS = (
    "read.orders",
    "read.payments",
    "read.helpdesk",
    "lookup_by_key",
    "approvals.read",
    "approvals.create_pending",
    "approvals.convert_executed",
    "check_eligibility",
    "draft_reply",
    "hand_back",
    "propose.refund",
    "propose.cancel",
    "propose.reship",
    "propose.goodwill",
    "helpdesk.create_draft",
    "helpdesk.assign",
    "helpdesk.add_note",
    "reserve",
    "release",
    "approve",
    "execute_approved",
    "payments.refund",
    "payments.credit",
    "orders.cancel",
    "orders.reship",
    "audit.append",
    "audit.read",
    "secrets.read",
    "reconcile.request",
    "schema.change",
    "permission.change",
    "credential.change",
    "bulk_delete",
    "approvals.void",
    "approvals.read_pending",
    "killswitch.operate",
    "migrate.schema",
    "ci.deploy",
    "breakglass.use",
)

_MODEL_REQUESTS = frozenset(
    {
        "read.orders",
        "read.payments",
        "read.helpdesk",
        "check_eligibility",
        "draft_reply",
        "hand_back",
        "propose.refund",
        "propose.cancel",
        "propose.reship",
        "propose.goodwill",
    }
)

IDENTITIES: dict[str, dict] = {
    "agent_runtime": {
        "policy": "The model's identity. Reads the three ports (scoped to the ticket's verified customer), asks for eligibility, and REQUESTS a template draft, a "
        "hand-back or a money proposal. Holds no write port, no reservation, no approval, no executor and no audit credential.",
        "allow": _MODEL_REQUESTS,
        "why": {
            "read.*": "lookups are the agent's job",
            "check_eligibility": "dry run of the pre-gate",
            "draft_reply": "requests a harness template",
            "hand_back": "requests a human",
            "propose.*": "creates a pending approval request via the gate service, never moves money",
        },
    },
    "harness": {
        "policy": "Writes helpdesk drafts, assignments and notes on behalf of requests that passed lint. Cannot read payments, reserve, approve or apply money.",
        "allow": frozenset({"read.helpdesk", "helpdesk.create_draft", "helpdesk.assign", "helpdesk.add_note"}),
        "why": {"helpdesk.*": "template drafts, queue routing, notes", "read.helpdesk": "reads the ticket it answers"},
    },
    "gate_service": {
        "policy": "Evaluates the pre-gate, reserves exposure atomically with the tier and records a pending approval. Reads the ports; its only writes are the reservation and the pending approval record. Cannot apply money or approve.",
        "allow": frozenset({"read.orders", "read.payments", "read.helpdesk", "reserve", "approvals.create_pending"}),
        "why": {
            "reserve": "atomic exposure + tier",
            "approvals.create_pending": "records the proposal",
            "read.orders": "the pre-gate reads the order",
            "read.payments": "the pre-gate reads captured and refunded amounts",
            "read.helpdesk": "the pre-gate reads the ticket and its verified sender",
        },
    },
    "approval_verifier": {
        "policy": "Checks approver authority: roster, role, signature, requester/touched/beneficiary rules, args hash. Read-only.",
        "allow": frozenset({"approvals.read", "read.helpdesk", "read.orders"}),
        "why": {
            "approvals.read": "reads the approval it checks",
            "read.helpdesk": "live touched_by across all tickets bound to the key",
            "read.orders": "beneficiary/cluster check",
        },
    },
    "approver_human": {
        "policy": "A person with a passkey. Signs an approval step; cannot execute, reserve or write audit.",
        "allow": frozenset({"approve", "approvals.read_pending"}),
        "why": {
            "approve": "the only human decision on money",
            "approvals.read_pending": "reads the pending approval it is about to sign",
        },
    },
    "executor": {
        "policy": "Applies an approved action with the business key. Looks up first. Cannot approve or reserve. In stage 1 the write gate appends its intent, applied and refused rows to the chain ON ITS BEHALF (there is no separate audit_writer process; that identity is policy-only). Reads approvals.",
        "allow": frozenset(
            {
                "approvals.read",
                "lookup_by_key",
                "execute_approved",
                "payments.refund",
                "payments.credit",
                "orders.cancel",
                "orders.reship",
                "helpdesk.add_note",
                "approvals.void",
                "approvals.convert_executed",
            }
        ),
        "why": {
            "payments.*/orders.*": "the money move",
            "lookup_by_key": "reconcile before retry",
            "helpdesk.add_note": "the follow-up write",
            "approvals.read": "reads the approval it is about to consume",
            "approvals.void": "WriteGate.void: withdraws a proposal and writes the tombstone",
            "approvals.convert_executed": "turns a held reservation into an executed amount when the apply commits",
            "execute_approved": "the one entry point, WriteGate.execute",
        },
    },
    "sweeper": {
        "policy": "Releases reservations of expired or voided approvals on a timer. Cannot apply money, approve or read customer data.",
        "allow": frozenset({"approvals.read", "release"}),
        "why": {
            "release": "dead reservations must not inflate caps",
            "approvals.read": "decides which reservations are past their TTL",
        },
    },
    "reconciler": {
        "policy": "Resolves `unknown` outcomes: looks up by key, converts to executed or releases per the settle rule; may ask the executor to re-apply the SAME key. "
        "Cannot itself move money.",
        "allow": frozenset({"approvals.read", "lookup_by_key", "approvals.convert_executed", "release", "reconcile.request"}),
        "why": {
            "lookup_by_key": "truth source",
            "reconcile.request": "same-key apply is performed by the executor, not here",
            "approvals.read": "reads the held approval it is resolving",
            "approvals.convert_executed": "records an applied outcome found by lookup",
            "release": "frees the hold of a not-applied outcome confirmed twice",
        },
    },
    "kill_switch_operator": {
        "policy": "A person (or on-call role) who flips the kill switch. Nothing else: cannot approve, execute, read customer data or change config.",
        "allow": frozenset({"killswitch.operate"}),
        "why": {"killswitch.operate": "hold all NEW applies; the switch holds, it never voids"},
    },
    "migrations": {
        "policy": "A human-run, CI-gated identity that applies reviewed schema migrations to the demo store. Not an agent; holds no money, approval or audit action.",
        "allow": frozenset({"migrate.schema"}),
        "why": {"migrate.schema": "reviewed migration files only; separate from the agent-forbidden schema.change"},
    },
    "ci_deploy": {
        "policy": "Deploys a reviewed build from CI. Cannot read customer data, move money, approve or change permissions.",
        "allow": frozenset({"ci.deploy"}),
        "why": {"ci.deploy": "ship the reviewed artefact"},
    },
    "breakglass": {
        "policy": "DORMANT. Holds no standing action; enabling it needs the owner's explicit yes, is time-boxed, logged and reviewed afterwards.",
        "allow": frozenset(),
        "why": {},
    },
    "audit_writer": {
        "policy": "Appends events to the hash chain. Append-only; a separate identity from the executor; cannot read secrets or move money.",
        "allow": frozenset({"audit.append"}),
        "why": {"audit.append": "tamper-evident chain"},
    },
    "audit_reader": {
        "policy": "Reads the chain for verification and export. Cannot append.",
        "allow": frozenset({"audit.read"}),
        "why": {"audit.read": "verify chain"},
    },
}

MODEL_FACING = frozenset({"agent_runtime"})


def authorize(identity: str, action: str) -> bool:
    """Deny-all start: unknown identity, unknown action, or an action not in the identity's allow-list is denied."""
    entry = IDENTITIES.get(identity)
    return bool(entry) and action in ACTIONS and action in entry["allow"]


def model_callable_tools() -> frozenset[str]:
    from refunds import tools

    return frozenset(t["name"] for t in tools.REGISTRY)
