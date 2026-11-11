"""A child process for one test: it makes the plain test role and a schema the role owns, reports the role's name and
exits normally, so that the exit hook of `tests/fixtures/migration_role.py` runs in it."""

from __future__ import annotations


def make_the_role_and_own_a_schema(dsn: str, schema: str, names) -> None:
    import psycopg
    from psycopg import sql

    from tests.fixtures import migration_role as m

    with psycopg.connect(dsn, autocommit=True) as db:
        m.ensure_plain_role(db)
        db.execute(
            sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                sql.Identifier(schema), sql.Identifier(m.PLAIN_ROLE)
            )
        )
        db.execute(sql.SQL("CREATE TABLE {}.t (id int)").format(sql.Identifier(schema)))
    m._USED_DSNS.add(
        m._target_key(dsn)
    )  # one entry per connection target, as the helper keeps them
    names.put(m.PLAIN_ROLE)
