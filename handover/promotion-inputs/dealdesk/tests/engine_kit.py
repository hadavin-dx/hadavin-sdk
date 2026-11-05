"""Builders for the engine tests: a tenant world from the committed synthetic data, approver devices (Ed25519 private keys live HERE, on the approver
side; the engine only ever gets the public halves) and helpers to sign decisions."""

import copy
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dealdesk import canon
from dealdesk.core_copy.approvals_signed import issue
from dealdesk.desk import APPROVAL_SCHEMA, Desk
from dealdesk.executor import Executor
from dealdesk.signing import LocalSigner
from dealdesk.store import TenantStore
from dealdesk.world import FixedClock, KeyDirectory, World

D = Path(__file__).resolve().parent.parent
MATRIX = json.loads((D / "config/approval_matrix.json").read_text(encoding="utf-8"))
POLICY = json.loads((D / "config/desk_policy.json").read_text(encoding="utf-8"))
BOOK = json.loads((D / "tests/fixtures/pricebook.json").read_text(encoding="utf-8"))
DIRECTORY = json.loads((D / "tests/fixtures/directory.json").read_text(encoding="utf-8"))
CRM = json.loads((D / "tests/fixtures/crm.json").read_text(encoding="utf-8"))
STD = {"discount_bps": 0, "term_years": 1, "billing": "annual_prepay", "payment_terms_days": 30, "sla_tier": "standard"}
LANE_OF = {r: lane for lane, roles in MATRIX["lanes"].items() for r in roles}
START = "2026-11-09T09:00:00Z"


def mk_deal(
    deal_id,
    account_id,
    name,
    *,
    owner="p-ae-01",
    plan="business",
    ccy="USD",
    seats=40,
    tier="strategic",
    rtype="new",
    arr="0",
    region=None,
):
    return {
        "deal_id": deal_id, "account_id": account_id, "account_name": name, "owner_rep": owner, "currency": ccy, "customer_tier": tier,
        "request_type": rtype, "plan": plan, "seats": seats, "arr_minor": arr, "price_book_version": BOOK["version"], "notes": "n",
        "tax_region": region or POLICY["tax"]["default_region"][ccy],
    }  # fmt: skip


class Kit:
    def __init__(self, tenant="t-a", deals=None, base_crm=False, entropy_seed=1, policy_edit=None, desk_kw=None):
        self.tenant = tenant
        self.clock = FixedClock(START)
        crm = copy.deepcopy(CRM) if base_crm else []
        self.world = World(tenant, {d["deal_id"]: d for d in [*crm, *(deals or [])]}, copy.deepcopy(BOOK), copy.deepcopy(DIRECTORY),
                           copy.deepcopy(MATRIX), copy.deepcopy(POLICY))  # fmt: skip
        if policy_edit:
            policy_edit(self.world.policy)
        self.keys = KeyDirectory(tenant)  # PUBLIC keys: all the engine has
        self.devices: dict[tuple[str, str], LocalSigner] = {}  # PRIVATE keys: the approvers' side, never passed to the engine
        self.store = TenantStore(tenant)
        self._n = entropy_seed * 1000
        self._desk_kw = desk_kw or {}
        self.restart()

    def restart(self):
        """A process restart with the CURRENT config in the world (the engine freezes its own copy at construction)."""
        self.desk = Desk(self.world, self.store, self.clock, self.keys, entropy=self._entropy, **self._desk_kw)
        self.ex = Executor(self.desk)

    def _entropy(self):
        self._n += 1
        return self._n.to_bytes(16, "big")

    def device(self, person, kid="k1", register=True):
        """The approver's signing device. Registering publishes only the PUBLIC key to the engine's key directory."""
        if (person, kid) not in self.devices:
            seed = hashlib.sha256(
                f"{self.tenant}/{person}/{kid}".encode()
            ).digest()  # deterministic test keys: identical runs, identical stores
            sg = LocalSigner(Ed25519PrivateKey.from_private_bytes(seed))
            self.devices[(person, kid)] = sg
            if register:
                self.keys.add(person, sg.key_id, sg.alg, sg.public_key())
        return self.devices[(person, kid)]

    def person(self, role, i=1):
        return f"p-{ {'sales_manager': 'sm', 'regional_vp': 'rvp', 'cro': 'cro', 'finance_controller': 'fc', 'cfo': 'cfo', 'legal_counsel': 'lc', 'general_counsel': 'gc', 'account_executive': 'ae'}[role] }-{i:02d}"

    def propose(self, deal_id, terms=None, clauses=None, owner=None, **kw):
        deal = self.world.deals[deal_id]
        return self.desk.propose("agent_runtime", owner or deal["owner_rep"], deal_id, {**STD, **(terms or {})}, clauses, **kw)

    def open_approval(self, qid):
        q = self.store.get("quotes", qid)
        for aid in reversed(q["approvals"]):
            a = self.store.get("approvals", aid)
            if a["state"] == "open":
                return a
        return None

    def signed(self, approval, approver, decision="approve", kid="k1", register=True, **over):
        """A core-format signed approval. Fields in `over` replace the honest ones BEFORE signing (the approver signed something else); args_hash is
        recomputed unless given."""
        f = {
            k: approval[k]
            for k in ("approval_id", "deal_id", "terms_hash", "quote_hash", "snapshot_hash", "lane", "min_role", "epoch")
        }
        f.update(
            tenant_id=self.tenant,
            requested_at=approval["request_ts"],
            approver_id=approver,
            decision=decision,
            ts=self.clock.now(),
        )
        f.update(over)
        if "args_hash" not in over:
            f["args_hash"] = canon.decision_args_hash(f)
        return issue(self.device(approver, kid, register), {k: f[k] for k in canon.APPROVAL_FIELDS}, APPROVAL_SCHEMA)

    def decide(self, approval, approver, decision="approve", identity=None, auth_person="same", **over):
        role = next((p["role"] for p in self.world.directory if p["person_id"] == approver), "account_executive")
        who = identity or "approver_" + LANE_OF.get(role, "commercial")
        person = approver if auth_person == "same" else auth_person
        kid = over.pop("kid", "k1")
        register = over.pop("register", kid == "k1")
        return self.desk.record_decision(
            who, self.signed(approval, approver, decision, kid=kid, register=register, **over), person
        )

    def approve_all(self, qid, who_by_lane):
        """Approve every step in order with the given {lane: person_id}."""
        out = []
        while (a := self.open_approval(qid)) is not None:
            out.append(self.decide(a, who_by_lane[a["lane"]]))
        return out
