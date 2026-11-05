import hashlib

from jagrat import quarantine
from jagrat.knowledge import default_knowledge_base
from jagrat.models import ActionKind

SIX = {a.value for a in ActionKind}
EIGHT = {
    "DISK-FULL-001",
    "DB-POOL-001",
    "DB-SLOW-001",
    "RATE-429-001",
    "REPLICA-LAG-001",
    "RETRY-STORM-001",
    "METASTABLE-001",
    "CROSSAZ-001",
}
REASON_PHRASES = [
    "out of memory",
    "oom-kill",
    "killed process",
    "throttl",
    "cpu pressure",
    "secret not found",
    "couldn't find key",
    "connection pool",
    "too many connections",
    "pool exhausted",
]
# sha256 of "\n".join(quarantine.phrases()) computed from the reference signatures plus the unchanged base phrases
PHRASES_SHA256 = "2744fce37bee615d4f905b33e34c4d60f955c3c6f8ead516390f0a4d2e26c363"


def test_default_knowledge_base_loads_and_every_suggested_action_is_one_of_the_six():
    kb = default_knowledge_base()
    assert kb.signatures
    for sig in kb.signatures:
        assert sig.suggested_actions, sig.id
        assert {a.kind.value for a in sig.suggested_actions} <= SIX, sig.id


def test_the_eight_signatures_keep_their_ids_and_a_retained_action():
    sigs = {s.id: s for s in default_knowledge_base().signatures}
    assert EIGHT <= set(sigs)
    assert [a.kind.value for a in sigs["DISK-FULL-001"].suggested_actions] == ["escalate_to_human"]
    assert "terminate_connections" in {a.kind.value for a in sigs["DB-POOL-001"].suggested_actions}


def test_phrases_are_unchanged_by_the_action_trim():
    ph = quarantine.phrases()
    assert hashlib.sha256("\n".join(ph).encode()).hexdigest() == PHRASES_SHA256
    for p in REASON_PHRASES:
        assert p in ph, p
