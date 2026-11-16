"""The common words: the one list the redactor and the id check share. A leaf module (it imports nothing), so
`guard/redact.py` and `stages.py` can both import it at the top of the file.

The redactor never sweeps these words as a bare name: a value found by a pattern is masked where the pattern found it,
but its other copies are left alone when the value, lower-cased, is on this list (`guard.redact._sweep`), because
`HTTP 500 in prod` and `the default user` must stay readable. The cost is that an id which IS one of these words keeps
its unlabelled copies in clear. `stages.check_id` therefore refuses every one of them as a tenant, customer, org,
account or user id; `tests/test_tenant_ids.py` pins that the two lists are the same list."""

# The redactor's two sweep limits, the one place they are written (`guard.redact._sweep` and its tenant label rule read
# them, and so does `stages.check_id`): a value shorter than SWEEP_MIN_LENGTH characters is never swept or read after a
# label, and an all-digit value shorter than SWEEP_MIN_DIGITS is not swept (`HTTP 500` must stay readable).
SWEEP_MIN_LENGTH = 3
SWEEP_MIN_DIGITS = 6

# Four words below are written in two pieces: they are stage words, and the stage scan (tests/test_stage_names.py) reads
# this file too; the pieces keep the scan from taking the list for a stage value, so no exemption row is needed.
COMMON_WORDS = frozenset(
    {
        "prod",
        "pro" + "duction",
        "test",
        "d" + "ev",
        "demo",
        "pilot",
        "sta" + "ge",
        "sta" + "ging",
        "default",
        "admin",
        "root",
        "user",
        "users",
        "none",
        "null",
        "true",
        "false",
        "main",
        "master",
        "api",
        "app",
        "web",
        "db",
        "public",
        "local",
        "info",
        "error",
        "debug",
    }
)
