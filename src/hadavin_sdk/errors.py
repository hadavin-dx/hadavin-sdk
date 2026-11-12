"""Errors shared by ``config`` and ``backends``, kept here so neither has to import the other."""


class ConfigError(ValueError):
    """The client config is invalid; the process must not start."""


class SignInError(ConfigError):
    """The cloud sign-in that gives a short-lived database password failed (no credentials, no region, a refused token
    request), so no connection was tried. It is a `ConfigError` (exit 2); the message names the kind of error, never the
    SDK's own words (which can hold an account name)."""


class AppliedNotVerifiedError(Exception):
    """`migrate` committed the files but cannot say the database is as the grant map allows (ticket P3a-2, 4.2).

    It is deliberately NOT a `ConfigError`: a `ConfigError` means "refused, nothing happened" everywhere in this
    package (exit code 2 of the command line). This error means the opposite: the commit happened, or may have
    happened, and the check after it either found rights beyond the grant map or could not run. The command line
    exits with 5.

    `applied` are the versions of this run, `problems` the findings of the check (empty when it could not run),
    `statements` every statement that removes them (in the order to run them), `could_not_run` the reason when the
    check after the commit did not run ("" when it ran), `commit_unknown` true when the connection was lost while the
    commit was sent, so that the commit may or may not have happened and nothing was checked afterwards."""

    def __init__(
        self,
        message: str,
        *,
        applied=(),
        problems=(),
        statements=(),
        could_not_run: str = "",
        commit_unknown: bool = False,
    ) -> None:
        super().__init__(message)
        self.applied: list[str] = list(applied)
        self.problems: list = list(problems)
        self.statements: list[str] = list(statements)
        self.could_not_run = could_not_run
        self.commit_unknown = commit_unknown
