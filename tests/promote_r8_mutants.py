"""Old-behaviour stubs for the PR #49 modules: each puts back ONE behaviour the reviews found wrong (or removes one control) and the
promoted tests must fail. Prints the failing tests per mutant. Run from the repo root with the postgres DSN set so the
store contract runs on both kinds:

    HADAVIN_TEST_PG_DSN=... uv run --all-extras --group dev --group test python tests/promote_r8_mutants.py
"""

import subprocess
import sys
from pathlib import Path

G = "src/hadavin_sdk/guard/"
IT, RC = G + "identity_text.py", G + "reply_check.py"
MEM, RSV, OB = (
    "src/hadavin_sdk/store/memory.py",
    "src/hadavin_sdk/store/reservations.py",
    "src/hadavin_sdk/actions/outbox.py",
)
SG, RF, LM, GT = (
    "src/hadavin_sdk/approvals/signed.py",
    "src/hadavin_sdk/audit/refusal.py",
    "src/hadavin_sdk/limits.py",
    "src/hadavin_sdk/approvals/gate.py",
)
PG = "src/hadavin_sdk/store/postgres.py"
EX = "src/hadavin_sdk/actions/executor.py"

MUTANTS = [
    (
        "old: spaced dot not joined",
        RC,
        '_SPACED_DOT.sub(".", text) if p.join_spaced_dots else text',
        "text",
    ),
    ("old: stop by accepts any non-ASCII text", LM, "ascii_only=True", "ascii_only=False"),
    ("old: response body not capped", EX, "        if n > limit:", "        if False:"),
    ("old: combining marks allowed in identity text", IT, '"Cs", "Mn", "Me"', '"Cs", "Me"'),
    (
        "old: look-alike letters allowed into the identity key",
        IT,
        'if lookalikes == "refuse" and any(',
        "if False and any(",
    ),
    (
        "old: recipient compared through the accent-dropping fold",
        IT,
        'return " ".join(unicodedata.normalize("NFC", raw).casefold().split())',
        "return fold(raw, casefold=True, collapse_ws=True)",
    ),
    (
        "old: allow-lists compared raw, not folded",
        RC,
        "links, hosts = p.folded(p.allowed_links), p.folded(p.allowed_hosts)",
        "links, hosts = p.allowed_links, p.allowed_hosts",
    ),
    (
        "old: non-ASCII host not flagged",
        RC,
        "            v.add(Violation.NON_ASCII_HOST)",
        "            pass",
    ),
    (
        "old: email pattern unbounded",
        RC,
        r'EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}")',
        r'EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")',
    ),
    (
        "old: domain pattern unbounded",
        RC,
        r"(?:[a-z0-9-]{1,63}\.){1,10}(?:xn--[a-z0-9-]{1,59}|[a-z]{2,24})",
        r"(?:[a-z0-9-]+\.)+[a-z]{2,}",
    ),
    ("old: no text size cap", RC, "    if len(text) > p.max_text:", "    if False:"),
    (
        "old: allowed patterns ignored by the domain scan",
        RC,
        '        no_urls = re.sub(pat, " ", no_urls, flags=re.IGNORECASE)',
        "        pass",
    ),
    ("old: punycode TLD not a host", RC, "(?:xn--[a-z0-9-]{1,59}|[a-z]{2,24})", "(?:[a-z]{2,24})"),
    (
        "old: reply to an unverified recipient accepted",
        RC,
        "    if want is None or exact_key(recipient) != want:",
        "    if False:",
    ),
    (
        "old: reservation limits not enforced",
        MEM,
        "            code = rsv.decide(n_scope, n_actor, total, res, limits)",
        "            code = None",
    ),
    (
        "old: a repeat with other content is held",
        MEM,
        "return None if rsv.same_content(held, res) else rsv.KEY_CONFLICT",
        "return None",
    ),
    (
        "old: unknown unit reads as a limit hit",
        RSV,
        "        return UNIT_UNKNOWN",
        "        return OPEN_LIMIT",
    ),
    (
        "old: amount not validated",
        RSV,
        "    if isinstance(res.amount, bool) or not isinstance(res.amount, int) or res.amount <= 0:",
        "    if False:",
    ),
    (
        "old: window ignored when counting",
        MEM,
        "r for r in self._res.values() if r.tenant == res.tenant and r.created_at >= since",
        "r for r in self._res.values() if r.tenant == res.tenant",
    ),
    (
        "old: reservations not tenant scoped",
        MEM,
        "r for r in self._res.values() if r.tenant == res.tenant and r.created_at >= since",
        "r for r in self._res.values() if r.created_at >= since",
    ),
    (
        "old: request saved even when refused",
        MEM,
        "            code = rsv.decide(n_scope, n_actor, total, res, limits)\n            if code is not None:\n                return code",
        "            code = rsv.decide(n_scope, n_actor, total, res, limits)\n            if request is not None:\n                self._approvals[request.approval_id] = request.model_copy(deep=True)\n            if code is not None:\n                return code",
    ),
    (
        "old (pg): a repeat with other content is held",
        PG,
        "return None if same else rsv.KEY_CONFLICT",
        "return None",
    ),
    (
        "old (pg): limits not enforced",
        PG,
        "                code = rsv.decide(n_scope, n_actor, int(total), res, limits)",
        "                code = None",
    ),
    (
        "old: not_applied strands the key",
        OB,
        "            if last.state is RunState.SUCCEEDED:",
        "            if last.state in (RunState.SUCCEEDED, RunState.ROLLED_BACK):",
    ),
    (
        "old: any apply error is swallowed as unknown",
        OB,
        "        res = self.processor.apply(key)",
        "        try:\n            res = self.processor.apply(key)\n        except Exception:  # noqa: BLE001\n            res = Unknown('x')",
    ),
    (
        "old: open attempt retried blindly",
        OB,
        "            if last.state is RunState.EXECUTING:",
        "            if False:",
    ),
    (
        "old: one failing key aborts the reconcile batch",
        OB,
        "            except Exception as exc:  # noqa: BLE001 - per-key isolation: record the class, go on",
        "            except KeyboardInterrupt as exc:",
    ),
    (
        "old: stale attempts never escalate",
        OB,
        "        if now - run.updated_at < escalate_after:",
        "        if True:",
    ),
    (
        "old: intent not audited before the effect",
        OB,
        '            self.audit.write_intent(_event(key, attempt, "intent", self.principal))',
        "            pass",
    ),
    (
        "old: signature encodings not pinned",
        SG,
        '_SIG = re.compile(r"[0-9a-f]{128}")',
        '_SIG = re.compile(r"\\s*[0-9a-fA-F]{128}\\s*")',
    ),
    (
        "old: key_id outside the signed body",
        SG,
        '    keys = (*schema.fields, "key_id")',
        "    keys = schema.fields",
    ),
    (
        "old: tenant not compared",
        SG,
        "        if approval[s.tenant_field] != tenant_id:",
        "        if False:",
    ),
    ("old: no expiry", SG, "        if age > max_age:", "        if False:"),
    (
        "old: no single use",
        SG,
        "        if consume is not None and not consume(approval[s.id_field]):",
        "        if False:",
    ),
    (
        "old: any algorithm accepted by the verifier",
        SG,
        "            if alg not in get_args(Alg):",
        "            if False:",
    ),
    (
        "old: refusal key written raw",
        RF,
        '"object_ref": "-" if key is None else _safe(key, _KEY),',
        '"object_ref": "-" if key is None else str(key),',
    ),
    (
        "old: refusal label lowercase only, others lost as ?",
        RF,
        '_LABEL = re.compile(r"[A-Za-z0-9_.-]{1,64}")',
        '_LABEL = re.compile(r"[a-z0-9_.-]{1,64}")',
    ),
    ("old: stop `by` written raw", LM, "            if text_ok(by, 128)", "            if True"),
    ("old: cmdlet filter takes Hadavin ids", GT, "(?!(?:run|pln|apr|evt)-[0-9a-f]{32}\\b)", ""),
]


def main() -> int:
    import os

    survivors = 0
    only = os.environ.get("ONLY")
    for name, rel, old, new in MUTANTS:
        if only and only not in name:
            continue
        p = Path(rel)
        text = p.read_text(encoding="utf-8")
        if text.count(old) != 1:
            print(f"{name}: PATTERN COUNT {text.count(old)}")
            survivors += 1
            continue
        p.write_text(text.replace(old, new), encoding="utf-8", newline="")
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=no", "-p", "no:cacheprovider", "tests/test_promote_r8.py", "tests/test_promote_r8_pg.py", "tests/contracts/test_store.py"],
                capture_output=True, text=True, check=False,
            )  # fmt: skip
        finally:
            p.write_text(text, encoding="utf-8", newline="")
        failed = [
            ln.split(" - ")[0].replace("FAILED ", "").split("::", 1)[-1]
            for ln in r.stdout.splitlines()
            if ln.startswith(("FAILED", "ERROR"))
        ]
        if not failed:
            survivors += 1
        print(
            f"{name}: {'SURVIVED' if not failed else 'CAUGHT'} | {len(failed)} failing | "
            + "; ".join(failed[:3])
        )
    print(f"mutants: {len(MUTANTS)}, not caught: {survivors}")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
