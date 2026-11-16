"""Fakes for the systems of record (CRM, billing, identity, secrets, clock). READ-ONLY ports: no write method exists on any port (tested); the harness
mutates the World directly to simulate events. Fakes mimic common semantics and are not a model of any real system."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field

from dealdesk import gate_rules as g
from dealdesk.errors import CrossTenantAccess, Malformed, ReadThrottled
from dealdesk.guards import RateCap, ReadLog
from dealdesk.identities import requires
from dealdesk.nameindex import NameIndex
from dealdesk.purposes import DEAL_FIELDS
from dealdesk.store import check_tenant


class FixedClock:
    """Injectable UTC clock. Nothing in the package reads the wall clock. The demo and the tests use a FIXED clock (default 2026-11-09), so dates such as
    "valid until" are relative to that fixed date, not to the real day."""

    def __init__(self, start: str = "2026-11-09T09:00:00Z") -> None:
        self._t = g.parse_ts(start)

    def now(self) -> str:
        from datetime import UTC, datetime

        return datetime.fromtimestamp(self._t, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, *, hours: float = 0, seconds: int = 0) -> None:
        self._t += int(hours * 3600) + seconds

    def today(self) -> str:
        return self.now()[:10]


@dataclass
class World:
    """One tenant's systems of record. Every record carries the tenant id and a port refuses a record that does not match (R-094)."""

    tenant_id: str
    deals: dict
    book: dict
    directory: list
    matrix: dict
    policy: dict
    exemptions: dict = field(default_factory=dict)  # account_id -> valid_until (ISO date)
    names_version: int = (
        0  # bumped by rename_account: the change token the name index is keyed on (a real CRM connector supplies its own)
    )

    def rename_account(self, account_id: str, new_name: str) -> None:
        """The one way the demo CRM changes an account name (bumps the token, so the cached name index is rebuilt)."""
        hit = [d for d in self.deals.values() if d["account_id"] == account_id]
        for d in hit:
            d["account_name"] = new_name
        self.names_version += 1

    def __post_init__(self) -> None:
        check_tenant(self.tenant_id)
        for d in self.deals.values():
            d.setdefault("tenant_id", self.tenant_id)
            if d["tenant_id"] != self.tenant_id:
                raise CrossTenantAccess("deal of another tenant in this world")
        for p in self.directory:
            p.setdefault("tenant_id", self.tenant_id)
            if p["tenant_id"] != self.tenant_id:
                raise CrossTenantAccess("person of another tenant in this world")


class ReadOnlyPorts:
    """CRM + billing + identity as ONE read-only role, with the identity check on every method (not in three places)."""

    def __init__(
        self,
        world: World,
        log: ReadLog | None = None,
        clock: FixedClock | None = None,
        rate_cap: RateCap | None = None,
        now_s=time.monotonic,
    ) -> None:
        self._w = world
        self.tenant_id = world.tenant_id
        self.log = log if log is not None else ReadLog()
        self._clock = clock
        self._cap, self._now_s = (
            rate_cap,
            now_s,
        )  # blast radius: the read-only role has a request-rate cap so the AI cannot slow production
        self._cache: dict = {}  # mutable on purpose: the object is sealed against rebinding, not against caching
        self._sealed_ports = True

    def __setattr__(self, name, value) -> None:
        if self.__dict__.get("_sealed_ports"):
            raise AttributeError("ReadOnlyPorts is sealed: " + name)
        object.__setattr__(self, name, value)

    def _read(self, who, port: str, fields: list[str], ref: str, why: str, rows: int) -> None:
        if self._cap is not None and not self._cap.allow(self._now_s()):
            raise ReadThrottled("read-only role rate cap reached")
        self.log.read(who, port, fields, ref, why, rows, self._clock.now() if self._clock else "")

    @requires("crm.read")
    def get_deal(self, who, deal_id: str) -> dict:
        d = self._w.deals.get(deal_id) if isinstance(deal_id, str) else None
        if d is None:
            raise Malformed("unknown deal")
        if d["tenant_id"] != self.tenant_id:
            raise CrossTenantAccess("deal belongs to another tenant")
        self._read(who, "crm", [f"deal.{f}" for f in DEAL_FIELDS], deal_id, "apply the written approval policy to one deal", 1)
        return {f: copy.deepcopy(d[f]) for f in DEAL_FIELDS}  # purpose limitation: notes and any other field stay in the CRM

    @requires("crm.read")
    def account_names(self, who) -> dict:
        self._read(
            who,
            "crm",
            ["deal.account_id", "deal.account_name"],
            "*",
            "quote text names scan (R-DEALDESK-088)",
            len(self._w.deals),
        )
        return {d["account_id"]: d["account_name"] for d in self._w.deals.values()}

    @requires("crm.read")
    def account_name_index(self, who) -> NameIndex:
        """The tenant's account names as an inverted index. Rebuilt only when the world's change token moved (`World.rename_account`) or the number of deals changed."""
        deals = self._w.deals
        self._read(
            who,
            "crm",
            ["deal.account_id", "deal.account_name"],
            "*",
            "quote text names scan (R-DEALDESK-088)",
            len(deals),
        )
        ver = (self._w.names_version, len(deals))
        idx = self._cache.get("names")
        if idx is None or idx[0] != ver:
            idx = (ver, NameIndex({d["account_id"]: d["account_name"] for d in deals.values()}))
            self._cache["names"] = idx
        return idx[1]

    @requires("crm.read")
    def exemption(self, who, account_id: str):
        self._read(who, "billing", ["billing.exemption"], str(account_id), "tax exemption certificate (R-DEALDESK-083)", 1)
        return self._w.exemptions.get(account_id)

    @requires("billing.read")
    def get_pricebook(self, who) -> dict:
        self._read(
            who,
            "billing",
            ["pricebook.plans", "pricebook.floor_bps", "pricebook.standard_terms"],
            "pricebook",
            "money and margin arithmetic",
            1,
        )
        return copy.deepcopy(self._w.book)

    @requires("directory.read")
    def get_person(self, who, person_id: str) -> dict | None:
        self._read(who, "identity", ["directory.person"], str(person_id), "role and employee id of one person", 1)
        for p in self._w.directory:
            if p["person_id"] == person_id and p["tenant_id"] == self.tenant_id:
                return copy.deepcopy(p)
        return None

    @requires("directory.read")
    def people_with_role(self, who, role: str) -> list[str]:
        self._read(who, "identity", ["directory.role_members"], str(role), "route an approval step", 1)
        return sorted(p["person_id"] for p in self._w.directory if p["role"] == role and p["active"])


class KeyDirectory:
    """PUBLIC keys of approvers, per person: {key_id: (alg, public key bytes)}. The engine holds nothing that can sign. Revocation = removal.
    (A client build reads the same data from the identity provider / key store; the private half stays with the approver's passkey, HSM or KMS.)"""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = check_tenant(tenant_id)
        self._k: dict[str, dict[str, tuple[str, bytes]]] = {}

    def add(self, person_id: str, key_id: str, alg: str, public_key: bytes) -> None:
        self._k.setdefault(person_id, {})[key_id] = (alg, bytes(public_key))

    def revoke(self, person_id: str, key_id: str) -> None:
        self._k.get(person_id, {}).pop(key_id, None)

    def keys_for(self, person_id: object) -> dict[str, tuple[str, bytes]]:
        return dict(self._k.get(person_id, {})) if isinstance(person_id, str) else {}
