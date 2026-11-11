"""The common words: the one list the redactor and the id check share. A leaf module (it imports nothing), so
`guard/redact.py` and `stages.py` can both import it at the top of the file.

The redactor never sweeps these words as a bare name: a value found by a pattern is masked where the pattern found it,
but its other copies are left alone when the value, lower-cased, is on this list (`guard.redact._sweep`), because
`HTTP 500 in prod` and `the default user` must stay readable. The cost is that an id which IS one of these words keeps
its unlabelled copies in clear. `stages.check_id` therefore refuses every one of them as a tenant, customer, org,
account or user id; `tests/test_tenant_ids.py` pins that the two lists are the same list."""

COMMON_WORDS = frozenset(
    {
        "prod",
        "production",
        "test",
        "dev",
        "demo",
        "pilot",
        "stage",
        "staging",
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
