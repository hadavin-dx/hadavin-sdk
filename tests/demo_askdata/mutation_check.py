"""Mutation evidence for PR 43 rounds 8 and 9: break one fix at a time and show that its test fails.

Run from anywhere:  python tests/demo_askdata/mutation_check.py [name-fragment ...]

Each row temporarily rewrites one source line, runs the test file that guards it, restores the file in a `finally`,
and prints KILLED (the tests failed, good), SURVIVED (they still passed: a gap) or ANCHOR MISSING (the source line moved:
update this table). It edits files in the working tree, so run it on a clean checkout and not while other tests run.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = "demos/ask-your-data/askdata/"
R8 = "tests/demo_askdata/test_demo_gaps_r8.py"
R9 = "tests/demo_askdata/test_demo_gaps_r9.py"
LIT = "tests/demo_askdata/test_demo_literals.py"
LLM = "tests/test_llm_attempts.py"
R10 = "tests/demo_askdata/test_demo_gaps_r10.py"
PIPE = "tests/demo_askdata/test_pipeline.py"
# (name, file, old text, new text, test file that must fail)
MUTATIONS = [
    (
        "r8 M1 identical set allowed",
        A + "sealed.py",
        'if data["files_sha"] in seen_sets:',
        'if False and data["files_sha"] in seen_sets:',
        R8,
    ),
    (
        "r8 M3 sealed-named folder not checked",
        A + "evalcli.py",
        'if m and m.group(1) != "dev":',
        "if False and m:",
        R8,
    ),
    (
        "r8 M6 old lock recorded before the move",
        A + "sealed.py",
        "os.replace(lock_path(self.eval_dir), moved)\n                old = moved",
        "old = moved\n                os.replace(lock_path(self.eval_dir), moved)",
        R8,
    ),
    (
        "r8 m4 vanished results still complete",
        A + "sealed.py",
        'status = "unverified"  # the caller wrote',
        'status = "complete"  # the caller wrote',
        R8,
    ),
    (
        "r8 m6 chain rewrite not retried",
        A + "evalset.py",
        "        except PermissionError:\n            if attempt",
        "        except FileNotFoundError:\n            if attempt",
        R8,
    ),
    (
        "r8 m9 rekey signed by the new key",
        A + "sealed.py",
        "            signing_key=self.chain.old_keys[-1],\n        )\n        write_lock(",
        "        )\n        write_lock(",
        R8,
    ),
    (
        "r8 M7 reservation priced in characters",
        A + "pipeline.py",
        'len(messages[0]["content"].encode())',
        'len(messages[0]["content"])',
        R8,
    ),
    (
        "r8 R368 second settle not a no-op",
        A + "meter.py",
        "return  # already settled (or never reserved)",
        "pass  # already settled (or never reserved)",
        R8,
    ),
    (
        "r8 m10 statement-timeout cap 999s",
        "demos/ask-your-data/db/roles.sql",
        "ro_statement_timeout' ~ '^[1-9][0-9]{0,2}s$'",
        "ro_statement_timeout' ~ '^[1-9][0-9]{0,4}s$'",
        R8,
    ),
    (
        "r8 M5 parse failures not an unusable answer",
        "src/hadavin_sdk/llm/common.py",
        '    except Exception as exc:  # noqa: BLE001\n        raise UnusableAnswer(f"unusable answer',
        '    except ZeroDivisionError as exc:  # noqa: BLE001\n        raise UnusableAnswer(f"unusable answer',
        LLM,
    ),
    (
        "r8 m11 allowlist counted as a set",
        LIT,
        "return sorted((Counter(found) - Counter(allowed)).elements())",
        "return sorted(set(found) - set(allowed))",
        LIT,
    ),
    (
        "r9 M1a failed freeze leaves the new chain",
        A + "sealed.py",
        "                else:\n                    self.path.unlink(missing_ok=True)",
        "                else:\n                    pass",
        R9,
    ),
    (
        "r9 M1b failed append not truncated",
        A + "sealed.py",
        "                        f.truncate(size)",
        "                        pass",
        R9,
    ),
    (
        "r9 M2a lost branch raises for any surviving file",
        A + "sealed.py",
        "if bad := _mismatched(\n                rec, folder\n            ):",
        "if bad := ([n for n in ('report.json', 'report.md', 'results.jsonl') if (folder / n).exists()] if problem else []):",
        R9,
    ),
    (
        "r9 M2b lost branch never raises",
        A + "sealed.py",
        "if bad := _mismatched(\n                rec, folder\n            ):",
        "if False:",
        R9,
    ),
    (
        "r9 M3a meter read not retried",
        A + "meter.py",
        "            except PermissionError:\n                if attempt == RUNTIME.lock_replace_attempts - 1:\n                    raise",
        "            except FileNotFoundError:\n                if attempt == RUNTIME.lock_replace_attempts - 1:\n                    raise",
        R9,
    ),
    (
        "r9 M3b meter write not retried",
        A + "meter.py",
        "replace_with_retry(tmp, self.path)",
        "os.replace(tmp, self.path)",
        R9,
    ),
    (
        "r9 M3c snapshot takes no lock",
        A + "meter.py",
        "        with self._locked():  # a reader never sees (or collides with) a half-finished replace\n            d = self._read()",
        "        if True:\n            d = self._read()",
        R9,
    ),
    (
        "r9 m6 chain reader raises a raw UnicodeDecodeError",
        A + "sealed.py",
        "        except ValueError:  # UnicodeDecodeError",
        "        except ZeroDivisionError:  # UnicodeDecodeError",
        R9,
    ),
    (
        "r9 m7 temp file leaked",
        A + "evalset.py",
        "        tmp.unlink(missing_ok=True)  # a failed write (disk full) leaves no temp file behind",
        "        pass",
        R9,
    ),
    (
        "r9 m8a settle trusts the caller's reserved",
        A + "meter.py",
        '                    reserved = _dec(opened.pop(rid)["amount"], "open.amount")',
        "                    opened.pop(rid)",
        R9,
    ),
    (
        "r9 m8b settle accepts a non-finite number",
        A + "meter.py",
        "            if not v.is_finite() or v < 0:",
        "            if v < 0:",
        R9,
    ),
    (
        "r9 m9 overage after clear-open dropped",
        A + "meter.py",
        'elif rid in d.get(\n                    "cleared", {}\n                ):',
        "elif False:",
        R9,
    ),
    (
        "r9 m10 provider usage not validated",
        "src/hadavin_sdk/llm/common.py",
        '        _check_usage(getattr(out, "tokens", None))',
        "        pass",
        LLM,
    ),
    (
        "r9 m11 ledger cost short after Ctrl-C",
        A + "pipeline.py",
        "                run.cost += worst  # the ledger line must show what the meter now says",
        "                pass",
        R9,
    ),
    (
        "r9 m5 large-object revoke removed",
        "demos/ask-your-data/db/roles.sql",
        "REVOKE EXECUTE ON FUNCTION pg_catalog.lo_creat(integer) FROM PUBLIC;",
        "-- removed",
        R9,
    ),
    ("r9 M4a NUL stripping off", LIT, '    raw = raw.replace(b"\\0", b"")', "    pass", LIT),
    (
        "r9 M4b tracked work/ skipped",
        LIT,
        "if rel.parts[0] in SKIP_TOP and p not in tracked:",
        "if rel.parts[0] in SKIP_TOP:",
        LIT,
    ),
    (
        "r9 M4c private-key pattern broken",
        LIT,
        'r"-----BEGIN [A-Z ]*PRIVATE KEY-----"',
        'r"-----BEGIN [A-Z ]*PRIVATE KEYZ-----"',
        LIT,
    ),
    (
        "r9 M4d URL-password pattern broken",
        LIT,
        "[^\\s/:@'\\\"]+:[^\\s/@'\\\"]{3,}@",
        "[^\\s/:@'\\\"]+:[^\\s/@'\\\"]{3,}@@",
        LIT,
    ),
    (
        "r9 M4e region match case-sensitive",
        LIT,
        'rf"(?i:\\b(us|eu|ap|sa|ca|me|af|il|mx|cn)',
        'rf"(?:\\b(us|eu|ap|sa|ca|me|af|il|mx|cn)',
        LIT,
    ),
    (
        "r9 m12 import aliases ignored",
        LIT,
        'last = aliases.get(full.rsplit(".", 1)[-1], full.rsplit(".", 1)[-1])',
        'last = full.rsplit(".", 1)[-1]',
        LIT,
    ),
    (
        "r10 M4a first-request refusal loses attempts",
        "src/hadavin_sdk/llm/retry.py",
        "        except ProviderError as err:\n            err.attempts = attempt\n            raise",
        "        except ProviderError as err:\n            raise",
        R10,
    ),
    (
        "r10 M4b refusal attempts reset to 1",
        "src/hadavin_sdk/llm/retry.py",
        "refused.attempts = attempt",
        "refused.attempts = 1",
        R10,
    ),
    (
        "r10 M4c exhaustion attempts reset to 1",
        "src/hadavin_sdk/llm/retry.py",
        "spent.attempts = attempt",
        "spent.attempts = 1",
        R10,
    ),
    (
        "r10 M4d unusable answer billed as refusal",
        "demos/ask-your-data/askdata/meter.py",
        "refused=known and not isinstance(err, ProviderExhausted | UnusableAnswer),",
        "refused=known,",
        R10,
    ),
    (
        "r10 M4e attempts ignored when charging",
        "demos/ask-your-data/askdata/meter.py",
        'sent=getattr(err, "attempts", 1) if known else default_attempts,',
        "sent=1,",
        R10,
    ),
    (
        "r10 M4f billed_usd ignored when charging",
        "demos/ask-your-data/askdata/meter.py",
        'billed=Decimal(getattr(err, "billed_usd", 0)),',
        "billed=Decimal(0),",
        R10,
    ),
    (
        "r10 M4g non-provider error charged one request",
        "demos/ask-your-data/askdata/meter.py",
        "else default_attempts,",
        "else 1,",
        R10,
    ),
    (
        "r10 M4h pipeline stops using error_cost",
        "demos/ask-your-data/askdata/pipeline.py",
        "cost = error_cost(err, per_try, worst, self.s.llm_max_attempts)",
        "cost = Decimal(0)",
        PIPE,
    ),
    (
        "r10 m1a negative reply cost not clamped",
        "demos/ask-your-data/askdata/meter.py",
        "return max(Decimal(0), reply_cost) + per_attempt",
        "return reply_cost + per_attempt",
        R10,
    ),
    (
        "r10 m1b non-finite reply cost accepted",
        "demos/ask-your-data/askdata/meter.py",
        "if not reply_cost.is_finite():",
        "if False:",
        R10,
    ),
    (
        "r10 m1c Money accepts NaN and negatives",
        "src/hadavin_sdk/config.py",
        "if not v.is_finite() or v < 0:  # NaN",
        "if False:  # NaN",
        R10,
    ),
    (
        "r10 m3 malformed chain entry not a LockError",
        "demos/ask-your-data/askdata/sealed.py",
        "except (KeyError, TypeError) as err:",
        "except ZeroDivisionError as err:",
        R10,
    ),
    (
        "r10 m6a unicode digits accepted",
        "demos/ask-your-data/askdata/meter.py",
        "if not text.isascii():",
        "if False:",
        R10,
    ),
    (
        "r10 m6b huge exponent accepted",
        "demos/ask-your-data/askdata/meter.py",
        "out.adjusted() > _DEFAULT.max_amount_exponent",
        "False",
        R10,
    ),
    (
        "r10 m7a bool accepted as a count",
        "demos/ask-your-data/askdata/settings.py",
        "Field(2, ge=0, strict=True)",
        "Field(2, ge=0)",
        R10,
    ),
    (
        "r10 m7b billed_usd untyped int",
        "src/hadavin_sdk/llm/protocol.py",
        "billed_usd: Decimal = Decimal(0)",
        "billed_usd = 0",
        R10,
    ),
]


def run_one(name: str, rel: str, old: str, new: str, tests: str) -> tuple[str, str]:
    path = ROOT / rel
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8")
    old, new = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
    if old not in text:
        return name, "ANCHOR MISSING"
    path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
    try:
        done = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            ["uv", "run", "--all-extras", "--group", "test", "pytest", "-q", "-x", tests],  # noqa: S607
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        last = (done.stdout.strip().splitlines() or ["?"])[-1]
        return name, f"{'KILLED' if done.returncode else 'SURVIVED'} | {last}"
    finally:
        path.write_bytes(raw)


def main(argv: list[str]) -> int:
    rows = [run_one(*m) for m in MUTATIONS if not argv or any(frag in m[0] for frag in argv)]
    for name, verdict in rows:
        print(f"{name} | {verdict}")
    return 0 if all(v.startswith("KILLED") for _, v in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
