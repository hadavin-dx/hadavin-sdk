"""Mutants for the fixes of design/code review 8 (SoD folding, reservation flooding, signer kind, who-approved, audit of refusals, required identity,
shape limits, ledger overlap, typed lock timeout, egress bounds, config validation). (name, file, regex, replacement); the regex is searched once.

REPLACED: older mutants whose target line was rewritten in rev 9, restated against the new line (same property, same name). They overwrite by name."""

W, A, S, G = "src/refunds/writegate.py", "src/refunds/approval.py", "src/refunds/store.py", "src/refunds/guards.py"
D, SG, C, T = "src/refunds/desk.py", "src/refunds/signers.py", "src/refunds/config.py", "src/refunds/textnorm.py"

# Retired in rev 9: the code they mutated was removed because it became unreachable (the shape check now makes the body unable to raise).
# Nothing retired. (Round 15 retired "egress: text not normalised before scanning" as equivalent; review 11 asked for proof, a differential fuzz found it is NOT
# equivalent: the outer `normalise` case-folds, and 'shop.ß' only becomes a host ('shop.ss') after that; restored and killed by test_review14.)
RETIRED8: set[str] = set()

REPLACED = {
    "approval: requester may approve": (
        A,
        r"if norm\(requester\) in people or _skeleton\(requester\) in skeletons:",
        "if False:",
    ),
    "approval: requester compared without normalising": (
        A,
        r"if norm\(requester\) in people or _skeleton\(requester\) in skeletons:",
        'if requester in [s["person"] for s in steps]:',
    ),
    "approval: beneficiary may approve": (
        A,
        r"if norm\(beneficiary\) in people or _skeleton\(beneficiary\) in skeletons:",
        "if False:",
    ),
    "approval: beneficiary compared without normalising": (
        A,
        r"if norm\(beneficiary\) in people or _skeleton\(beneficiary\) in skeletons:",
        'if beneficiary in [s["person"] for s in steps]:',
    ),
    "egress: defanged hosts not folded": (
        G,
        r"clean = _defang\(normalise\(_SPACED_DOT\.sub\(\".\", normalise_keep_case\(text\)\)\)\)",
        'clean = normalise(_SPACED_DOT.sub(".", normalise_keep_case(text)))',
    ),
    "egress: text not normalised before scanning": (
        G,
        r"clean = _defang\(normalise\(_SPACED_DOT\.sub\(\".\", normalise_keep_case\(text\)\)\)\)",
        'clean = _defang(_SPACED_DOT.sub(".", normalise_keep_case(text)))',
    ),
    "limits: USD customer cap back to the hard cap": (
        C,
        r'"USD": Limits\(7500, 50000, 2500, 1500, 30000, 250000\)',
        '"USD": Limits(7500, 50000, 2500, 1500, 49999, 250000)',
    ),
    "textnorm: Hangul filler not dropped": (T, r"FILLERS = \{[^}]*\}", "FILLERS = set()"),
    "write: approval not consumed": (
        W,
        r"        self\.store\.consume_approval\(tenant, rec\[\"approval_id\"\], key, who\[\"requester\"\], approvers, req\[\"tier\"\], identity, stamp\)\n",
        "",
    ),
    "write: same key with other parameters replays (all legs)": (
        W,
        r"            return self\._refuse\(tenant, key, \"KEY_REUSED\", stamp, identity\)\n",
        '            return {"outcome": "duplicate_ignored", "code": None, "record": _rec(row)}\n',
    ),
    "store: transaction does not roll back on error": (
        S,
        r"            except BaseException:\n                self\._rollback\(\)\n",
        '            except BaseException:\n                self._db.execute("COMMIT")\n',
    ),
    "write: control and bidi characters allowed in text": (T, r"_BAD_CATS = frozenset\(\{[^}]*\}\)", "_BAD_CATS = frozenset()"),
    "write: text length not capped": (T, r"and 0 < len\(s\) <= max_len", "and len(s) > 0"),
    "write: requester/beneficiary text not checked": (
        W,
        r"        if not \(_ascii_text_ok\(req\[\"requester\"\]\) and _text_ok\(req\[\"beneficiary\"\]\)\):\n            return \"KEY_INVALID\"\n",
        "",
    ),
    "approval: MAC not checked": (
        A,
        r"if not self\._sigver\.verify\(body, a\[\"mac\"\]\):  # type: ignore\[index\]",
        "if False:",
    ),
    "approval: NFKC dropped from the person comparison": (A, r"return textnorm\.normalise\(s\)", "return s.strip().casefold()"),
    "write: identity checked only after parsing": (
        W,
        r"        if not isinstance\(identity, str\) or not any\(\n            identities\.authorize\(identity, a\) for a in ACTION_TO_IDENTITY_ACTION\.values\(\)\n        \):\n            # first: a caller that may not write learns nothing about the request\n            return self\._early\(\"IDENTITY_DENIED\", identity, request\)\n",
        "",
    ),
    "write: per-action identity check removed": (
        W,
        r"        if not identities\.authorize\(identity, ACTION_TO_IDENTITY_ACTION\[req\[\"action\"\]\]\):\n            return self\._early\(\"IDENTITY_DENIED\", identity, request\)\n",
        "",
    ),
    "write: kill switch flip does not move the ratchet": (
        W,
        r"            self\.store\.set_kill_switch\(on, identity, reason, stamp\)\n            self\.store\.set_meta\(\"last_clock\", stamp\)\n",
        "            self.store.set_kill_switch(on, identity, reason, stamp)\n",
    ),
    "write: kill switch ignores the clock rule": (
        W,
        r"            now = self\._now\(\)\n            if isinstance\(now, str\):\n                return self\._refuse\(\"-\", \"-\", now, \"-\", _label\(identity\)\)\n            stamp = now\.strftime\(FMT\)\n            self\.store\.set_kill_switch",
        '            now = None\n            stamp = "2026-10-20T12:00:00Z"\n            self.store.set_kill_switch',
    ),
    "write: kill switch flipped without a reason": (
        W,
        r"if not _reason_ok\(reason\) or not isinstance\(on, bool\):",
        "if not isinstance(on, bool):",
    ),
    "store: a failed COMMIT leaves the transaction open": (
        S,
        r"                    self\._rollback\(\)  # a failed COMMIT must not leave the connection inside a transaction\n",
        "",
    ),
    "store: reserve is not idempotent": (
        S,
        r"\"SELECT 1 FROM reservations WHERE tenant=\? AND key=\?\", \(tenant, key\)\)\.fetchone\(\):",
        '"SELECT 1 FROM reservations WHERE 0=1").fetchone():',
    ),
    "write: check and write not one transaction": (
        W,
        r"        with self\.store\.transaction\(\):\n            now = self\._now\(\)\n            if isinstance\(now, str\):\n                return self\._refuse\(tenant, key, now, \"-\", identity\)\n            return self\._decide",
        '        if True:\n            now = self._now()\n            if isinstance(now, str):\n                return self._refuse(tenant, key, now, "-", identity)\n            return self._decide',
    ),
}

NEW = [
    # ---- code M1: the SoD comparison folds what the scanners fold; look-alike text is refused outright
    ("r8 sod: combining marks allowed in requester/beneficiary", T, r"\"Cs\", \"Mn\", \"Me\"", '"Cs", "Me"'),
    ("r8 sod: invisible filler letters allowed", T, r" or ch in FILLERS", ""),
    ("r8 sod: exotic spaces allowed", T, r" or \(ch != \" \" and unicodedata\.category\(ch\) == \"Zs\"\)", ""),
    ("r8 sod: text that folds to nothing allowed", T, r"        and normalise\(s\) != \"\"\n", ""),
    # ---- code M2 / design M1: the flooding caps live in the store and the desk feeds the pre-gate from it
    (
        "r8 flood: reserve ignores both pending caps and the share",
        S,
        r"if pending_cap_decision\(open_cluster, open_sender\) or not unapproved_share_ok\(held, amount_minor, currency\):",
        "if False:",
    ),
    ("r8 flood: reserve ignores the unapproved share", S, r" or not unapproved_share_ok\(held, amount_minor, currency\)", ""),
    ("r8 flood: reserve ignores the pending caps", S, r"if pending_cap_decision\(open_cluster, open_sender\) or", "if"),
    (
        "r8 flood: expired reservations still count for the cluster",
        S,
        r"\(tenant, since, cid, exclude_key\)",
        "(tenant, '0', cid, exclude_key)",
    ),
    (
        "r8 flood: sender count not tenant scoped",
        S,
        r"SELECT COUNT\(\*\) AS n FROM reservations WHERE tenant=\? AND created_at>=\? AND sender=\?",
        "SELECT COUNT(*) AS n FROM reservations WHERE ?<>'' AND created_at>=? AND sender=?",
    ),
    ("r8 flood: a key counts against itself", D, r"exclude_key=key", "exclude_key=''"),
    (
        "r8 flood: desk does not feed the pre-gate from the store",
        D,
        r"_merge_state\(case\.get\(\"port_state\", \{\}\), state, r\[\"currency\"\]\)",
        'case.get("port_state", {})',
    ),
    (
        "r8 flood: desk ignores the store's cap answer",
        D,
        r"return d if code is None else gate\.Decision\(deny_code=code, rule_id=config\.DENY_RULE\[code\]\)",
        "return d",
    ),
    (
        "r8 flood: void without an identity check",
        W,
        r"if not isinstance\(identity, str\) or not identities\.authorize\(identity, \"approvals\.void\"\):",
        "if False:",
    ),
    ("r8 flood: void reason not checked", W, r" and _reason_ok\(reason\)\)", ")"),
    (
        "r8 flood: void releases nothing",
        S,
        r"return db\.execute\(\"DELETE FROM reservations WHERE tenant=\? AND key=\?\", \(tenant, key\)\)\.rowcount",
        "return 0",
    ),
    # ---- code M3 / design M4: signer kind, read-only directory, no extra approval fields
    (
        "r8 signer: ed25519 verifier accepts any signature",
        SG,
        r"            self\._pub\.verify\(bytes\.fromhex\(sig\), body\)\n",
        "            pass\n",
    ),
    ("r8 signer: ed25519 verifier claims it can mint", SG, r"can_mint = False  # holds the public key only", "can_mint = True"),
    ("r8 signer: unknown kind falls through", SG, r"    if kind not in KINDS:", "    if False:"),
    (
        "r8 signer: verifier directory is writable",
        A,
        r"self\.directory = MappingProxyType\(directory\) if isinstance\(directory, dict\) else directory",
        "self.directory = directory",
    ),
    (
        "r8 signer: extra approval fields accepted",
        A,
        r"set\(a\) != \{\*FIELDS, \"mac\"\}",
        'not all(f in a for f in (*FIELDS, "mac"))',
    ),
    ("r8 signer: non-ASCII signature reaches the verifier", A, r"            and a\[\"mac\"\]\.isascii\(\)[^\n]*\n", ""),
    # ---- design M2: who approved; every refusal audited
    (
        "r8 who: approvers not persisted",
        W,
        r"approvers = \[\{\"person\": norm\(s\[\"person\"\]\), \"role\": s\[\"role\"\]\} for s in approval\[\"steps\"\]\]",
        "approvers = []",
    ),
    ("r8 who: requester not persisted", W, r"\"requester\": norm\(req\[\"requester\"\]\),", '"requester": "",'),
    ("r8 who: executing identity not persisted", W, r"\"executed_by\": identity,", '"executed_by": "",'),
    ("r8 who: who_approved not tenant scoped", S, r"WHERE a\.tenant=\? AND a\.key=\?", "WHERE ?<>'' AND a.key=?"),
    (
        "r8 audit: early refusals (identity, shape) not audited",
        W,
        r"    def _early\(self, code: str, identity: object, request: object\) -> dict:\n",
        "    def _early(self, code: str, identity: object, request: object) -> dict:\n        return _deny(code)\n",
    ),
    (
        "r8 audit: kill-switch hold not audited",
        W,
        r"            self\.store\.audit\(tenant, \"refused\", \{\"key\": key, \"code\": \"KILL_SWITCH\", \"identity\": identity\}, stamp\)\n",
        "",
    ),
    (
        "r8 audit: reused key not audited",
        W,
        r"            return self\._refuse\(tenant, key, \"KEY_REUSED\", stamp, identity\)\n",
        '            return _deny("KEY_REUSED")\n',
    ),
    (
        "r8 audit: clock refusal not audited",
        W,
        r"                return self\._refuse\(tenant, key, now, \"-\", identity\)\n",
        "                return _deny(now)\n",
    ),
    (
        "r8 audit: refusal rows lose the identity label",
        W,
        r"\{\"key\": key, \"code\": code, \"identity\": _label\(identity\)\}",
        '{"key": key, "code": code, "identity": "?"}',
    ),
    (
        "r8 audit: sweep refusal not audited",
        W,
        r"        if not isinstance\(identity, str\) or not identities\.authorize\(identity, \"release\"\):\n            return self\._early\(\"IDENTITY_DENIED\", identity, \{\}\)\n",
        '        if not isinstance(identity, str) or not identities.authorize(identity, "release"):\n            return _deny("IDENTITY_DENIED")\n',
    ),
    # ---- code m1 m2 m7 m8 m11 and the ledger
    (
        "r8 shape: identity defaults to the executor",
        W,
        r"identity: object = None, dry_run",
        'identity: object = "executor", dry_run',
    ),
    ("r8 shape: duplicate cluster entries accepted", W, r"            and len\(set\(cluster\)\) == len\(cluster\)\n", ""),
    ("r8 shape: signed request text not equal to the amount", W, r"basis\[\"request\"\] != req\[\"amount_minor\"\]", "False"),
    (
        "r8 ledger: shipping excluded from the overlap check",
        W,
        r"        lines = set\(req\[\"line_ids\"\]\)\n",
        '        lines = set(req["line_ids"]) - {"shipping"}\n',
    ),
    (
        "r8 lock: busy store raises instead of a typed deny",
        W,
        r"        except StoreBusy:\n            # [^\n]*\n            return _deny\(\"STORE_BUSY\"\)",
        "        except StoreBusy:\n            raise",
    ),
    ("r8 lock: busy store surfaces the driver error", S, r"raise StoreBusy\(str\(e\)\) from e", "raise"),
    (
        "r8 lock: a failing rollback masks the original error",
        S,
        r"        with contextlib\.suppress\(sqlite3\.Error\):\n            self\._db\.execute\(\"ROLLBACK\"\)",
        '        self._db.execute("ROLLBACK")',
    ),
    # ---- egress
    (
        "r8 egress: non-text input raises",
        G,
        r"    if not isinstance\(text, str\) or not isinstance\(recipient, str\):",
        "    if False:",
    ),
    ("r8 egress: oversized text is scanned", G, r"    if len\(text\) > EGRESS_MAX_TEXT:", "    if False:"),
    ("r8 egress: domain pattern unbounded", G, r"\(\?:\[\\w-\]\{1,63\}\\\.\)\{1,10\}", r"(?:[\w-]+\.)+"),
    (
        "r8 egress: email pattern unbounded",
        G,
        r"EMAIL = re\.compile\(r\"\[\\w\.\+-\]\{1,64\}@\[\\w-\]\{1,63\}\(\?:\\\.\[\\w-\]\{1,63\}\)\{1,8\}\"\)",
        r'EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")',
    ),
    ("r8 egress: space before the dot not folded", G, r"\|\(\?<=\\w\) \\\.\(\?=\[a-z\]\{2,\}\)", ""),
    # ---- config validation, store contract
    (
        "r8 config: tier ordering not validated",
        C,
        r"lim\.one_approver_max <= lim\.customer_30d_cap < lim\.hard_cap <= lim\.store_day_cap",
        "True",
    ),
    ("r8 config: goodwill ordering not validated", C, r"lim\.goodwill_amount <= lim\.goodwill_cap <= lim\.hard_cap", "True"),
    ("r8 config: bool accepted as a limit", C, r"isinstance\(v, bool\) or ", ""),
    (
        "r8 store: approvals not unique per tenant and id",
        S,
        r"PRIMARY KEY \(tenant, approval_id\)\);\nCREATE TABLE IF NOT EXISTS reservations",
        "executed_by2 TEXT);\nCREATE TABLE IF NOT EXISTS reservations",
    ),
    # ---- rev 9 (evidence 9): verifier-level refusal, ASCII staff ids, spaced dot, default signer, labelled audit
    (
        "r9 sod: the verifier trusts names without text_ok",
        A,
        r"        if not \(textnorm\.text_ok\(requester, TEXT_MAX\) and textnorm\.text_ok\(beneficiary, TEXT_MAX\)\) or not all\(\n            textnorm\.text_ok\(s\[\"person\"\], TEXT_MAX\) for s in steps\n        \):\n            return \"KEY_INVALID\"[^\n]*\n",
        "",
    ),
    (
        "r9 sod: a requester may hold non-ASCII letters",
        W,
        r"_ascii_text_ok\(req\[\"requester\"\]\)",
        '_text_ok(req["requester"])',
    ),
    (
        "r9 sod: an operator reason may hold non-ASCII letters",
        W,
        r"return _ascii_text_ok\(reason\) and len\(str\(reason\)\) >= REASON_MIN",
        "return _text_ok(reason) and len(str(reason)) >= REASON_MIN",
    ),
    (
        "r9 egress: a spaced dot is not joined",
        G,
        r"normalise\(_SPACED_DOT\.sub\(\".\", normalise_keep_case\(text\)\)\)",
        "normalise(normalise_keep_case(text))",
    ),
    ("r9 signer: the default signer is hmac", A, r"make_signer\(default_kind\(\)\)", "HmacSigner(key)"),
    (
        "r9 audit: the signer kind is not written into the applied row",
        W,
        r"            \"signer\": self\.approvals\.signer_kind,\n",
        "",
    ),
    # ---- round 11 (review 9): look-alike beneficiary, tombstone, typed busy on every writer, fail-closed signer, spaced dot, derived window, seam
    (
        "r11 sod: beneficiary skeleton compare removed",
        A,
        r"if norm\(beneficiary\) in people or _skeleton\(beneficiary\) in skeletons:",
        "if norm(beneficiary) in people:",
    ),
    (
        "r11 sod: requester skeleton compare removed",
        A,
        r"if norm\(requester\) in people or _skeleton\(requester\) in skeletons:",
        "if norm(requester) in people:",
    ),
    (
        "r11 sod: mixed-script beneficiary allowed",
        W,
        r"        if textnorm\.mixed_script\(req\[\"beneficiary\"\]\):",
        "        if False:",
    ),
    ("r11 sod: non-ASCII approver names allowed", A, r"if not all\(s\[\"person\"\]\.isascii\(\) for s in steps\):", "if False:"),
    (
        "r11 void: the tombstone is not written",
        W,
        r"            self\.store\.void_key\(tenant_id, key, reason, identity, now\.strftime\(FMT\)\)\n",
        "",
    ),
    ("r11 void: the tombstone is not read", W, r"if self\.store\.is_voided\(tenant, key\):", "if False:"),
    (
        "r11 void: the tombstone ignores the tenant",
        S,
        r"\"SELECT 1 FROM voided WHERE tenant=\? AND key=\?\"",
        "\"SELECT 1 FROM voided WHERE ?<>'' AND key=?\"",
    ),
    ("r11 void: any string is a key", W, r"isinstance\(key, str\) and _KEY64\.fullmatch\(key\)", "isinstance(key, str)"),
    ("r11 void: no reason floor", W, r" and len\(str\(reason\)\) >= REASON_MIN", ""),
    ("r11 busy: set_kill_switch can raise", W, r"    @_typed_busy\n    def set_kill_switch", "    def set_kill_switch"),
    ("r11 busy: void can raise", W, r"    @_typed_busy\n    def void", "    def void"),
    ("r11 busy: sweep can raise", W, r"    @_typed_busy\n    def sweep", "    def sweep"),
    ("r11 signer: silent HMAC fallback", SG, r"        raise SignerNotConfigured\(", "        return 'hmac' or ("),
    ("r11 signer: a short HMAC key is accepted", SG, r"len\(key\) < 16", "len(key) < 0"),
    (
        "r11 egress: the join needs a plain space",
        G,
        r"\(\?<=\[a-z0-9\]\)\\\.\\s\+\(\?=\[a-z\]\{2,\}\)",
        r"(?<=[a-z0-9])\\. (?=[a-z]{2,})",
    ),
    (
        "r11 egress: join before normalise",
        G,
        r"normalise\(_SPACED_DOT\.sub\(\".\", normalise_keep_case\(text\)\)\)",
        'normalise(_SPACED_DOT.sub(".", text))',
    ),
    ("r11 store: a runaway at is accepted", S, r"        if seen and at_dt >", "        if False and at_dt >"),
    (
        "r11 store: the window is not derived",
        S,
        r"return \(at_dt - timedelta\(seconds=APPROVAL_TTL_S\)\)\.strftime\(\"%Y-%m-%dT%H:%M:%SZ\"\)",
        'return "2000-01-01T00:00:00Z"',
    ),
    ("r11 desk: the recorded and store reservations are both counted", D, r"if r\[\"request_ref\"\] not in seen", "if True"),
    (
        "r11 seam: the derived window is not checked",
        "src/refunds/core_seam.py",
        r"    if since != created_at - timedelta\(seconds=config\.APPROVAL_TTL_S\):",
        "    if False:",
    ),
    ("r11 seam: other limits are accepted", "src/refunds/core_seam.py", r" or unit_caps != share", ""),
    (
        "r11 seam: codes are not translated",
        "src/refunds/core_seam.py",
        r"return CODE_MAP\.get\(code, code\) if code else None",
        "return code",
    ),
]
