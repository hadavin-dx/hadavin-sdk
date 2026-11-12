"""The expected texts of mutants that are NOT a literal of any file of `tests` or `src` (Q8a-1 batch 20, B2): a message built at run
time (an f-string, a pytest assertion rewrite, a generated test id), so a text search cannot see it. FROZEN at batch 20: it holds
the mutants that existed then; a new mutant must give a text that is found (`tests/_mutant_check.py`), and the check fails on a
text that is not. Do not add a row to hide a new mutant."""

DYNAMIC_EXPECTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("M10a pilot dropped from the redactor's common words", "pilot is swept"),
        ("M10b demo dropped from the redactor's common words", "demo is swept"),
        ("M10c prod dropped from the redactor's common words", "prod is swept"),
        (
            "M12d clock dropped from the six keywords (app.py)",
            "a live build took the keyword clock=",
        ),
        (
            "M12d detector dropped from the six keywords (app.py)",
            "a live build took the keyword detector=",
        ),
        ("M12d llm dropped from the six keywords (app.py)", "a live build took the keyword llm="),
        (
            "M12d secrets dropped from the six keywords (app.py)",
            "a live build took the keyword secrets=",
        ),
        (
            "M12d timeout_s dropped from the six keywords (app.py)",
            "a live build took the keyword timeout_s=",
        ),
        (
            "M12f the Vault check is narrowed to the secrets kind (app.py)",
            "a static Vault token was accepted for signer",
        ),
        (
            "M12g the Vault check runs in prod only (app.py)",
            "a static Vault token was accepted for secrets (pilot",
        ),
        (
            "M12i the Vault check is widened to every sign-in but kubernetes (app.py)",
            "a Vault sign-in that is not a static token was refused (approle)",
        ),
        (
            "M12k sources= is tested for truth, not for being given (app.py)",
            "a live build took sources= ('pilot', _FalsyDict",
        ),
        (
            "M12l tools= is tested for truth, not for being given (app.py)",
            "a live build took tools= ('pilot', _FalsyDict",
        ),
        (
            "M12m the timeout_s= keyword is not checked against the timeout rule (app.py)",
            "demo took timeout_s=0",
        ),
        ("M12n the executor timeout has no upper bound (config.py)", "demo took timeout_s=inf"),
        (
            "M12o True and False count as an executor timeout (config.py)",
            "demo took timeout_s=True",
        ),
        (
            "M12p the config field of the executor timeout is not checked against the rule (config.py)",
            "the config took executor_timeout_s: 3600.1",
        ),
        (
            "M12r the executor timeout has no lower bound above 0 (config.py)",
            "demo took timeout_s=1e-09",
        ),
        (
            "M15c a validation error is shown with pydantic's own text (config.py: _validation_text)",
            "validation error for Config",
        ),
        (
            "M15e a YAML error is shown with its own text, which quotes the line (config.py)",
            "while scanning",
        ),
        ("M15n an unknown route is shown again (config.py)", "validation error for Config"),
        (
            "M15o a refused list entry of the evidence settings is shown again (config.py)",
            "validation error for Config",
        ),
        ("M16i an unknown key is shown again (errors.py)", "validation error for ActionContract"),
        (
            "M16k a library ValueError keeps its text again (config.py)",
            "validation error for Probe",
        ),
        ("M16l every ValueError counts as ours (config.py)", "validation error for Probe"),
        ("M16m no ValueError counts as ours (config.py)", "validation error for Probe"),
        ("M17b every pydantic type counts as a fixed sentence (config.py)", "Input zq-probe"),
        ("M17x the longest shown name is cut by one character (errors.py)", "xxxxxxxxxx"),
        (
            "M17z a whole-file settings error shows an unknown key again (errors.py)",
            "did not match",
        ),
        ("M18b a long run of hex digits is shown (errors.py)", "a9999999999999999999"),
        ("M18d read_configured keeps the cause again (errors.py)", "('folder'"),
        ("M18p a tool call names the host it refused again (tools.py)", "zq-probe-mk4417"),
        ("M18r a registry entry that is not a mapping is not said (registry.py)", "bad entry"),
        ("M18s a raw name put in a message is caught by the guard (app.py)", "source {name}"),
        (
            "M19a a tool manifest field name is hidden again (errors.py)",
            "invalid tool entry (<not shown>)",
        ),
        (
            "M19i the Vault sign-in refusal drops the method again (secrets_vault.py)",
            "auth mount: sign-in",
        ),
        (
            "M19l the guard sees a raw name in a call argument of a message (cli.py)",
            "tick: {agent_id}",
        ),
        ("M19n the guard sees a raw root printed in a message (secrets_file.py)", "{root}"),
        (
            "M20a the rule problems of a namespace lose the word entry in their label (kubernetes.py)",
            "namespace 1: a rule is malformed",
        ),
        (
            "M21a a cloud library error is passed on with its text (secrets_cache.py)",
            "reading a secret failed (quotes",
        ),
        ("M3 audit/local_dir dropped from DEMO_ONLY", "assert frozenset"),
        ("M3 channel/fake dropped from DEMO_ONLY", "assert frozenset"),
        ("M3 llm/fake dropped from DEMO_ONLY", "assert frozenset"),
        ("M3 secrets/env dropped from DEMO_ONLY", "assert frozenset"),
        ("M3 secrets/fake dropped from DEMO_ONLY", "assert frozenset"),
        ("M3 store/memory dropped from DEMO_ONLY", "assert frozenset"),
        ("M4c pilot leaves the live stages (deferred.py)", "pilot is live"),
        (
            "M4e the loopback switch is allowed in pilot and prod",
            "did not refuse allow_insecure_loopback",
        ),
        ("M4g every stage is relaxed (app.py: live = False)", "pilot is live"),
        ("M9a registry.py goes back to an allowlist of live stages", "registry treated"),
        ("M9b deferred.py goes back to an allowlist of live stages", "deferred treated"),
        ("M9c app.py goes back to an allowlist of live stages", "app treated"),
        ("Y4 a built-in tick step is renamed (tick.py)", "assert ['sweep'"),
        ("Z117 round 15: describe prints the status with str() (retry.py)", "'Boom zq-b15-"),
        (
            "Z129 round 15: shown_id shows an id followed by other text (errors.py)",
            "b15 case 'run-",
        ),
        ("Z13 an unknown agent id is printed again (replay.py)", "unknown agent zq-probe"),
        (
            "Z132 round 15: LISTED accepts the text of an error in a list of sentences (registry.py)",
            "append of str(orphans)",
        ),
        (
            "Z136 round 15: the validation line shows another text than the count and the title (config.py), CLASSNAMES",
            "CLASSNAMES row of config.py",
        ),
        (
            "Z15 the hint word is chosen from the text of the error, not the class (secrets_cache.py)",
            "failed (TimeoutError)",
        ),
        (
            "Z176 round 16: the debug traceback prints the text of each error (cli.py, FRAMES)",
            "cli.py:87: [message] f'{type(err).__name__} {err}'",
        ),
        (
            "Z177 round 16: a log call of the approval store names the id as written (requests.py, STOREID)",
            "[message] _LOG.warning('approval %s: channel send failed (%s); tick will resend', req.approval_id, type(exc).__name__)",
        ),
        (
            "Z178 round 16: a text field is added into a cost (evals.py, NUM)",
            "evals.py:85: [message] cost += reply.text",
        ),
        (
            "Z179 round 16: a refused anchor kind is listed as written, not through the closed list (config.py, LISTED)",
            "config.py:483: [message] refused.append(str(anchor.kind))",
        ),
        (
            "Z185 round 16: an OSError of the package shows its text through the tick (tick.py), OWNERROR check",
            "_message shows the text of PkgOs",
        ),
        (
            "Z191 round 17: init lets the first error through (hidden_input.py)",
            "still holds the refused id (init)",
        ),
        (
            "Z192 round 19: model_validate lets the first error through (hidden_input.py)",
            "model_validate: the refused text is still in the error",
        ),
        (
            "Z193 round 19: model_validate_json lets the first error through (hidden_input.py)",
            "model_validate_json: the refused text is still in the error",
        ),
        (
            "Z194 round 19: model_validate_strings lets the first error through (hidden_input.py)",
            "model_validate_strings: the refused text is still in the error",
        ),
        (
            "Z198 round 17: the audit event is a plain pydantic model again (models.py)",
            "still holds the refused id (init)",
        ),
        (
            "Z219 round 17: com0 is not a reserved name (models.py)",
            "com0 is accepted as a plain file name",
        ),
        (
            "Z220 round 17: lpt0 is not a reserved name (models.py)",
            "lpt0 is accepted as a plain file name",
        ),
        (
            "Z23 a function passed on as a value still has its parameters proven (guard)",
            "assert 0 == 1",
        ),
        (
            "Z24 a caller that passes a value not proven does not stop the proof of a parameter (guard)",
            "assert 0 == 1",
        ),
        (
            "Z265 round 19: model_validate rebuilds the error without the words of the model (hidden_input.py)",
            "('<unknown key>',)",
        ),
        ("Z40 reason LISTED: a raw kind is added to the refusals (config.py)", "refused.append of"),
        (
            "Z79 reason LISTED: a problem sentence is the text of a name (registry.py)",
            "problems.append of str(orphans)",
        ),
        (
            "Z80 reason TIME: the sum is changed, its row no longer matches (secrets_cache.py)",
            "now + self.ttl_s is not found in the module",
        ),
        (
            "Z9 the unknown-setting sentence names the key again (strict_model.py)",
            "AnthropicSettings'",
        ),
        ("Z93 any sslmode word is printed (postgres.py)", "zq-b14-ssl"),
        ("Z99 a model id with a run of 32 letters or digits is accepted (config.py)", "A1A1A1"),
        ("fix1: GRANT without ON is not refused", "('GRANT r TO s', [])"),
        ("fix1: a byte order mark is not named", "hidden character U+FEFF"),
        ("fix1: only Cc is a hidden character", "Error: []"),
        ("o100: MIGRATE_LOCK differs from the key migrate uses", "BinOp(left=C"),
        ("o100: MIGRATIONS names another folder than migrate does", "BinOp(left=A"),
        ("o100: the error is not rebuilt from its problems on copy", "and 13 more"),
        ("o100: the small run is not floored", "0.048"),
    }
)
