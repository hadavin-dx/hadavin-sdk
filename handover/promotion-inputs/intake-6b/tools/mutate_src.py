"""Source-level mutation run: one mutant at a time, run the whole test suite, require a failure, restore the file.

Group SRC mutates the shipped code under src/ and config/ (the pipeline). Group ORACLE mutates the independent checker data/goldcheck.py and the generator: those prove the
gold set and the oracle are tested, NOT that the pipeline is.
Output: tools/mutate_src_output.txt (written by this script, committed). Usage: python tools/mutate_src.py [--only SUBSTRING] [--exclude SUBSTRING] [--skip-baseline] [--group queue]
Claim only what the output shows: a KILLED mutant means a test ASSERTION failed with the mutation (see `judge`). A mutant that makes the run crash (import
error, collection error, a non-assertion exception, a timeout, no tests) is reported as CRASH and is NOT counted as killed: a crash proves nothing about the tests.
"""

from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SRC = [
    ("src/intake/tools.py", 'if decimal_unit and "," in text:', "if False:", "kg comma quantity accepted"),
    (
        "src/intake/tools.py",
        'return "|".join(f"{len(x)}:{x}" for x in (tenant_id, customer_id, po_n))',
        'return "|".join((tenant_id, customer_id, po_n))',
        "business id loses the length prefix",
    ),
    (
        "src/intake/rules.py",
        "return len(text) > policy.max_document_chars",
        "return len(text) >= policy.max_document_chars",
        "size cap off by one",
    ),
    (
        "src/intake/rules.py",
        "    if not text.isascii():\n        return None\n    s = text.upper().strip()",
        "    s = text.upper().strip()",
        "invoice number ASCII guard removed (reviewer survivor 3)",
    ),
    (
        "src/intake/rules.py",
        'if not isinstance(lr, dict) or lr.get("allowed") is not True or lr.get("training_use") is not False:',
        'if not isinstance(lr, dict) or lr.get("allowed") is not True:',
        "live run allowed without training_use false",
    ),
    (
        "src/intake/rules.py",
        'if not isinstance(lr, dict) or lr.get("allowed") is not True or',
        'if not isinstance(lr, dict) or not lr.get("allowed") or',
        "live run allowed on a merely truthy allowed flag",
    ),
    (
        "src/intake/rules.py",
        "    return 0 <= ((today or datetime.now(UTC).date()) - checked).days <= max_age",
        "    return True",
        "live run allowed with a stale or future check date",
    ),
    (
        "src/intake/rules.py",
        "    return 0 <= ((today or datetime.now(UTC).date()) - checked).days <= max_age",
        "    return ((today or datetime.now(UTC).date()) - checked).days <= max_age",
        "live run allowed with a check date in the future",
    ),
    (
        "src/intake/rules.py",
        "    return 0 <= ((today or datetime.now(UTC).date()) - checked).days <= max_age",
        "    return 0 <= ((today or datetime.now(UTC).date()) - checked).days",
        "live run allowed with a stale check date",
    ),
    (
        "src/intake/rules.py",
        'lr = raw_policy.get("live_run") if isinstance(raw_policy, dict) else None',
        'lr = raw_policy.get("live_run")',
        "live run gate raises on a malformed policy",
    ),
    ("src/intake/rules.py", "@dataclass(frozen=True, slots=True)", "@dataclass(frozen=True)", "Policy gets a writable __dict__"),
    (
        "src/intake/rules.py",
        'MappingProxyType(dict(r["four_eyes_minor"]))',
        'dict(r["four_eyes_minor"])',
        "Policy threshold table is writable",
    ),
    (
        "src/intake/tools.py",
        "if _PO_CHARS.fullmatch(po) is None:",
        "if not po.isascii():",
        "normalise_po accepts characters the PO grammar refuses",
    ),
    ("src/intake/egress.py", "t = fold_text(body)", "t = body", "egress does not fold look-alike letters"),
    (
        "src/intake/egress.py",
        "if low in allowed or low in seen_parts:",
        "if low in allowed or any(low in s or s in low for s in seen):",
        "egress token matched by substring against the seen addresses",
    ),
    (
        "tools/mutate_src.py",
        '    if rc != 1:\n        return "CRASH"',
        '    if rc != 1:\n        return "KILLED"',
        "judge counts a crashed run as a kill",
    ),
    ("src/intake/egress.py", "not recipient.isascii() or ", "", "egress recipient ASCII check removed (reviewer survivor 4)"),
    (
        "src/intake/adapters/fake_draftstore.py",
        "return [r for t, r in self._invoices if t == tenant_id and r.supplier_id",
        "return [r for t, r in self._invoices if True and r.supplier_id",
        "processed-invoice list ignores the tenant (reviewer survivor 1)",
    ),
    (
        "src/intake/adapters/fake_ledger.py",
        "SELECT DISTINCT message_id FROM receipts WHERE tenant=?",
        "SELECT DISTINCT message_id FROM receipts WHERE 1=1 OR tenant=?",
        "ledger reconcile ignores the tenant (reviewer survivor 2)",
    ),
    (
        "src/intake/adapters/fake_draftstore.py",
        "self._versions.get((tenant_id, key), [])",
        'self._versions.get(("tenant-demo", key), [])',
        "lookup ignores the tenant",
    ),
    ("src/intake/adapters/fake_ledger.py", "if state not in TERMINAL_STATES:", "if False:", "ledger accepts any terminal state"),
    (
        "src/intake/adapters/fake_ledger.py",
        '                    self._capacity is not None\n                    and self._db.execute("SELECT COUNT(*) FROM receipts WHERE state IS NULL")',
        '                    False\n                    and self._db.execute("SELECT COUNT(*) FROM receipts WHERE state IS NULL")',
        "ledger never applies backpressure",
    ),
    (
        "src/intake/adapters/fake_ledger.py",
        "UNIQUE (tenant, message_id, raw_sha))",
        "UNIQUE (tenant, receipt_id))",
        "ledger key drops the content hash",
    ),
    ("src/intake/adapters/fake_erp.py", "if len(self._window) >= self._cap_rps:", "if False:", "ERP read-rate cap removed"),
    (
        "src/intake/adapters/fake_erp.py",
        "if self._cap_conn is not None and self._open_conn >= self._cap_conn:",
        "if False:",
        "ERP connection cap removed",
    ),
    ("src/intake/executor.py", "        if self.dry_run:", "        if False:", "executor writes in dry-run"),
    ("src/intake/executor.py", "        if self.kill_switch:", "        if False:", "kill switch ignored"),
    ("src/intake/executor.py", "if kind in FORBIDDEN or kind not in ACTION_CLASSES:", "if False:", "forbidden action classes allowed"),
    ("src/intake/executor.py", "or self._per_sender.get(bucket, 0) >= self._cap_sender:", ":", "per-sender write cap removed"),
    ("src/intake/isolation.py", "if owner_client_id != self.client_id:", "if False:", "cross-client few-shot example accepted"),
    (
        "src/intake/isolation.py",
        'return f"{self.client_id}/{kind}/{name}"',
        'return f"shared/{kind}/{name}"',
        "namespace drops the client id",
    ),
    # pure-function checks (checks.py): the pipeline's own parsers
    ("src/intake/checks.py", 'return text.lstrip("\\ufeff").replace', "return text.replace", "BOM no longer stripped"),
    (
        "src/intake/checks.py",
        '.replace("\\r\\n", "\\n").replace("\\r", "\\n")',
        '.replace("\\r\\n", "\\n")',
        "lone CR no longer a line break",
    ),
    (
        "src/intake/checks.py",
        "if _URL.search(s):\n            return False",
        "if False:\n            return False",
        "URL / email / wallet in an invoice no longer hands back",
    ),
    ("src/intake/checks.py", "if not all(c in flat for c in comps):", "if False:", "positive evidence of the on-file account not required"),
    ("src/intake/checks.py", "if any(t not in comps for t in toks):", "if False:", "foreign account-shaped tokens ignored"),
    (
        "src/intake/checks.py",
        '            prev, s = s, re.sub(r"(?<=[0-9])[^A-Z0-9]+(?=[0-9])", "", s)',
        "            prev, s = s, s",
        "digit separators are not collapsed (a single-pass variant is equivalent: the lookarounds consume nothing)",
    ),
    ("src/intake/checks.py", "t = _digits_ascii(t).casefold()", "t = t.casefold()", "non-ASCII digits not folded"),
    (
        "src/intake/checks.py",
        'if "%" in text:\n        out.append(unquote(text))',
        "if False:\n        out.append(unquote(text))",
        "percent-encoded account not decoded",
    ),
    ("src/intake/checks.py", "for blob in re.findall(", "for blob in [] and re.findall(", "base64 account not decoded"),
    ("src/intake/checks.py", "for ln in lines[tot[0] + 1 :]:", "for ln in []:", "rows after TOTAL ignored"),
    (
        "src/intake/checks.py",
        "if len(hdr) != 1 or len(tot) != 1 or tot[0] < hdr[0]:",
        "if len(hdr) < 1 or len(tot) < 1:",
        "repeated header or TOTAL tolerated",
    ),
    (
        "src/intake/checks.py",
        'if re.search(BANK["money_line_marker"], s):\n            s = re.sub(BANK["money_amount"], " ", s)',
        's = re.sub(BANK["money_amount"], " ", s)',
        "money stripped on every line (an account with cents hides)",
    ),
    (
        "src/intake/checks.py",
        'if unicodedata.category(s[0]) == "Nd":\n        return True',
        "if s[0].isascii() and s[0].isdigit():\n        return True",
        "non-ASCII digit order lines not item-like",
    ),
    (
        "src/intake/checks.py",
        "if not inv or not inv.isascii() or sup is None or po is None:",
        "if sup is None or po is None:",
        "missing or non-ASCII invoice number tolerated",
    ),
    # config
    ("config/screen_spec.json", "[^.!?;]{0,60}", ".{0,60}", "screen gap crosses sentence boundaries"),
    ("config/policy.json", '"max_document_chars": 20000', '"max_document_chars": 200000', "size cap raised"),
    ("config/bank_spec.json", '"min_long_digit_run": 6', '"min_long_digit_run": 9', "account-shaped digit run threshold raised"),
]
ORACLE = [
    (
        "demo_only/data/goldcheck.py",
        "if not all(c in flat for c in comps):",
        "if False:",
        "oracle: bank check no longer needs the on-file account",
    ),
    (
        "demo_only/data/goldcheck.py",
        'if len(text) > POLICY["max_document_chars"] and r.stop("X28"):',
        "if False:",
        "oracle: size cap removed",
    ),
    ("demo_only/data/goldcheck.py", "cum = q + prior.get(sku, 0)", "cum = q", "oracle: cumulative billing ignored"),
    ("demo_only/data/gen.py", '("S03", "INV-3-5000", "matched", 2, 4),', "", "generator: prior invoice for the D03-via-prior PO removed"),
]


WP5 = [
    (
        "src/intake/exporter.py",
        "    if _engaged():  # first, so it always wins",
        "    if False:  # first, so it always wins",
        "kill switch check skipped",
    ),
    ("src/intake/exporter.py", "shown\n        return True", "shown\n        return False", "kill switch read error counts as not engaged"),
    (
        "src/intake/exporter.py",
        "    except Exception:  # fail closed",
        "    except ZeroDivisionError:  # fail closed",
        "kill switch exception handler narrowed",
    ),
    (
        "src/intake/exporter.py",
        '    if item.state != "APPROVED":\n        return ExportResult("not_approved")',
        '    if False:\n        return ExportResult("not_approved")',
        "state APPROVED check removed",
    ),
    ("src/intake/exporter.py", '    if item.state == "EXPORTED":', "    if False:", "early EXPORTED branch removed"),
    ("src/intake/exporter.py", "        if r.content_code == code:", "        if True:", "EXPORTED item always already_exported"),
    (
        "src/intake/exporter.py",
        '        if r is None:\n            return ExportResult("not_approved")',
        '        if False:\n            return ExportResult("not_approved")',
        "EXPORTED item without receipt not refused",
    ),
    (
        "src/intake/exporter.py",
        '    if item.fields is None:\n        return ExportResult("not_approvable")',
        '    if False:\n        return ExportResult("not_approvable")',
        "null fields check removed",
    ),
    (
        "src/intake/exporter.py",
        "        code = cc.content_code(item)  # recomputed",
        "        code = (workqueue.latest_decision(conn, item.uid) or item).content_code if workqueue.latest_decision(conn, item.uid) else "
        "cc.content_code(item)  # recomputed",
        "content code trusted from the decision",
    ),
    (
        "src/intake/exporter.py",
        "    if other is not None:\n        same =",
        "    if False:\n        same =",
        "row id conflict check removed",
    ),
    (
        "src/intake/exporter.py",
        '"approval_mismatch" if same else "row_id_conflict"',
        '"approval_mismatch" if True else "row_id_conflict"',
        "row id conflict reported as another code",
    ),
    (
        "src/intake/exporter.py",
        "            with workqueue.transaction(conn):\n                item = workqueue.get_in(conn, item_id)",
        "            if True:\n                item = workqueue.get_in(conn, item_id)",
        "transaction removed",
    ),
    (
        "src/intake/exporter.py",
        "_EXPORT_LOCK = threading.Lock()",
        "_EXPORT_LOCK = __import__('contextlib').nullcontext()",
        "process lock removed",
    ),
    (
        "src/intake/exporter.py",
        'return ExportResult("approval_mismatch")\n'
        "    except (sqlite3.Error, OSError) as e:\n"
        "        return ExportResult(_db_code(e))\n"
        "\n"
        "\n"
        "# ---- the file",
        "return ExportResult(EXPORTED, exported=True)\n"
        "    except (sqlite3.Error, OSError) as e:\n"
        "        return ExportResult(_db_code(e))\n"
        "\n"
        "\n"
        "# ---- the file",
        "integrity error reported as success",
    ),
    (
        "src/intake/exporter.py",
        '                    return ExportResult("not_found")',
        "                    return ExportResult(EXPORTED, exported=True)",
        "not found reported as success",
    ),
    (
        "src/intake/exporter.py",
        '                except sink_guard.BadCell:\n                    return ExportResult("not_approvable", rid)',
        '                except sink_guard.BadCell:\n                    row_json = "{}"',
        "bad cell ignored",
    ),
    ("src/intake/exporter.py", 'return "db_busy" if busy else "db_error"', 'return "db_error"', "busy database reported as error"),
    (
        "src/intake/exporter.py",
        '    if item is None or item.state != "EXPORTED" or item.fields is None:',
        "    if item is None or item.fields is None:",
        "receipt state check removed",
    ),
    (
        "src/intake/exporter.py",
        'if latest is None or latest.decision != "approve" or latest.content_code != rec.content_code:',
        "if latest is None or latest.content_code != rec.content_code:",
        "receipt decision kind not checked",
    ),
    (
        "src/intake/exporter.py",
        'if latest is None or latest.decision != "approve" or latest.content_code != rec.content_code:',
        'if latest is None or latest.decision != "approve":',
        "receipt decision code not compared",
    ),
    (
        "src/intake/exporter.py",
        "    if code is not None and code != rec.content_code:",
        "    if False:",
        "receipt recomputed code not compared",
    ),
    (
        "src/intake/exporter.py",
        "    except flagtable.UnknownFlag:\n        code = None",
        "    except flagtable.UnknownFlag:\n        return None",
        "receipt unknown flag drops the row",
    ),
    (
        "src/intake/exporter.py",
        'if stored["row_id"] != rec.row_id or stored["content_code"] != rec.content_code:',
        "if False:",
        "receipt stored ids not compared",
    ),
    (
        "src/intake/exporter.py",
        "    return have if have == want else None",
        "    return have",
        "receipt stored row not compared with the item",
    ),
    ("src/intake/exporter.py", " or set(stored) != set(sink_guard.COLUMNS)", "", "receipt column set not checked"),
    (
        "src/intake/exporter.py",
        "    return strictjson.loads(text)",
        "    return json.loads(text)",
        "stored row parsed without the strict seam (a repeated key with the same value is accepted)",
    ),
    (
        "src/intake/exporter.py",
        "    if _engaged():\n        return _Regen(FILE_KILL_SWITCH)",
        "    if False:\n        return _Regen(FILE_KILL_SWITCH)",
        "regeneration ignores the kill switch",
    ),
    (
        "src/intake/exporter.py",
        "return _Regen(FILE_SINK_LOCKED, tuple(skipped))",
        "return _Regen(FILE_WRITTEN, tuple(skipped))",
        "locked file reported as written",
    ),
    (
        "src/intake/exporter.py",
        "    except csvsink.SinkError:\n        return _Regen(FILE_SINK_ERROR, tuple(skipped))",
        "    except csvsink.SinkError:\n        return _Regen(FILE_SINK_LOCKED, tuple(skipped))",
        "sink error reported as locked",
    ),
    (
        "src/intake/exporter.py",
        'return _Regen(FILE_WRITTEN, tuple(skipped), tuple(r["row_id"] for r in good))',
        'return _Regen(FILE_WRITTEN, (), tuple(r["row_id"] for r in good))',
        "skipped receipts not reported",
    ),
    (
        "src/intake/exporter.py",
        "return self.exported and self.file in (None, FILE_WRITTEN) and not self.skipped",
        "return self.exported and self.file in (None, FILE_WRITTEN)",
        "ok ignores skipped receipts",
    ),
    (
        "src/intake/exporter.py",
        "return self.exported and self.file in (None, FILE_WRITTEN) and not self.skipped",
        "return self.exported and not self.skipped",
        "ok ignores the file status",
    ),
    (
        "src/intake/exporter.py",
        "return self.file == FILE_WRITTEN and not self.skipped and all(r.exported for r in self.results)",
        "return self.file == FILE_WRITTEN and all(r.exported for r in self.results)",
        "run ok ignores skipped receipts",
    ),
    (
        "src/intake/exporter.py",
        "return self.file == FILE_WRITTEN and not self.skipped and all(r.exported for r in self.results)",
        "return self.file == FILE_WRITTEN and not self.skipped",
        "run ok ignores refused items",
    ),
    (
        "src/intake/exporter.py",
        '            if res.code in ("kill_switch", "db_busy", "db_error"):\n                break',
        "            if False:\n                break",
        "batch does not stop on kill switch",
    ),
    (
        "src/intake/exporter.py",
        '        if _engaged():\n            return ExportRun((ExportResult("kill_switch"),), FILE_KILL_SWITCH)',
        '        if False:\n            return ExportRun((ExportResult("kill_switch"),), FILE_KILL_SWITCH)',
        "batch kill check before the loop removed",
    ),
    (
        "src/intake/exporter.py",
        "return ExportResult(res.code, res.row_id, True, None, _receipt_skipped(s, item_id))",
        "return ExportResult(res.code, res.row_id, True, None, ())",
        "already exported never checked for landing",
    ),
    (
        "src/intake/exporter.py",
        "return ExportResult(res.code, res.row_id, True, r.status, r.skipped)",
        'return ExportResult(res.code, res.row_id, True, "written", ())',
        "file status dropped from the result",
    ),
    ("src/intake/exporter.py", "        _clean_stale_tmp(path)\n        csvsink", "        csvsink", "stale temp files not cleaned"),
    ("src/intake/exporter.py", '"approved_by": decision.approver,', '"approved_by": "ap-a",', "row approver wrong"),
    ("src/intake/exporter.py", '"line_count": len(f.get("lines", ())),', '"line_count": 0,', "row line count zero"),
    (
        "src/intake/exporter.py",
        '"flags": "|".join(sorted(item.flags)),',
        '"flags": ",".join(sorted(item.flags)),',
        "row flags joined with a comma",
    ),
    ("src/intake/exporter.py", '"approved_at": decision.at,', '"approved_at": workqueue.now_utc(),', "row approved_at from the clock"),
    ("src/intake/exporter.py", '"source_sha256": item.source_sha256,', '"source_sha256": "",', "row source hash blank"),
    (
        "src/intake/exporter.py",
        "reason_ok = stored is not None and decisions.valid_reason(s, stored.reason)",
        "reason_ok = True",
        "stored reason ignored",
    ),
    (
        "src/intake/exporter.py",
        "reason_ok = stored is not None and decisions.valid_reason(s, stored.reason)",
        "reason_ok = stored is None or decisions.valid_reason(s, stored.reason)",
        "stored decision missing counts as a valid reason",
    ),
    (
        "src/intake/exporter.py",
        "        return flagtable.approval_blocker(item.flags, reason_ok)",
        "        return None",
        "approval blocker ignored",
    ),
    (
        "src/intake/exporter.py",
        '    except flagtable.UnknownFlag:\n        return "unknown_flag"',
        "    except flagtable.UnknownFlag:\n        return None",
        "unknown flag allowed",
    ),
    ("src/intake/exporter.py", "or _blocker(s, item, latest) is not None:", "or False:", "blocker result not used"),
    (
        "src/intake/exporter.py",
        "    if validators.validate_record(item.fields, s.service.currencies) or _blocker(s, item, latest) is not None:",
        "    if _blocker(s, item, latest) is not None:",
        "validators call removed",
    ),
    ("src/intake/exporter.py", "workqueue.record_export(conn, item, rid, code, row_json, item.version)", "pass", "receipt not recorded"),
    (
        "src/intake/exporter.py",
        "workqueue.record_export(conn, item, rid, code, row_json, item.version)",
        "workqueue.record_export(conn, item, rid, code, row_json, item.version + 1)",
        "receipt recorded with a wrong version",
    ),
    ("src/intake/exporter.py", "ids = [i.id for i in workqueue.approved_unexported(conn)]", "ids = []", "pending list not used"),
    (
        "src/intake/sink_guard.py",
        'TRIGGERS = frozenset("=+-@ \\t\\r\\n")',
        'TRIGGERS = frozenset("+-@ \\t\\r\\n")',
        "guard trigger character = removed",
    ),
    (
        "src/intake/sink_guard.py",
        'TRIGGERS = frozenset("=+-@ \\t\\r\\n")',
        'TRIGGERS = frozenset("=-@ \\t\\r\\n")',
        "guard trigger character + removed",
    ),
    (
        "src/intake/sink_guard.py",
        'TRIGGERS = frozenset("=+-@ \\t\\r\\n")',
        'TRIGGERS = frozenset("=+@ \\t\\r\\n")',
        "guard trigger character - removed",
    ),
    (
        "src/intake/sink_guard.py",
        'TRIGGERS = frozenset("=+-@ \\t\\r\\n")',
        'TRIGGERS = frozenset("=+- \\t\\r\\n")',
        "guard trigger character @ removed",
    ),
    (
        "src/intake/sink_guard.py",
        'TRIGGERS = frozenset("=+-@ \\t\\r\\n")',
        'TRIGGERS = frozenset("=+-@\\t\\r\\n")',
        "guard trigger character space removed",
    ),
    (
        "src/intake/sink_guard.py",
        "if raw[:1] in TRIGGERS or folded[:1] in TRIGGERS:",
        "if folded[:1] in TRIGGERS:",
        "guard raw first character not checked",
    ),
    (
        "src/intake/sink_guard.py",
        "if raw[:1] in TRIGGERS or folded[:1] in TRIGGERS:",
        "if raw[:1] in TRIGGERS:",
        "guard folded first character not checked",
    ),
    ("src/intake/sink_guard.py", "folded = fold_text(raw)", "folded = raw", "guard fold not applied"),
    ("src/intake/sink_guard.py", "raw = value.translate(_BREAKS)", "raw = value", "guard line breaks kept"),
    ("src/intake/sink_guard.py", 'if "\\x00" in value:', "if False:", "guard NUL allowed"),
    ("src/intake/sink_guard.py", 'return "\'" + raw\n    return raw', "return raw\n    return raw", "guard prefix dropped"),
    ("src/intake/sink_guard.py", "    if len(value) > MAX_CELL:", "    if False:", "guard cell cap removed"),
    ("src/intake/sink_guard.py", "    if len(value) > MAX_CELL:", "    if len(value) >= MAX_CELL:", "guard cell cap off by one"),
    (
        "src/intake/sink_guard.py",
        '        value.encode("utf-8")  # a lone surrogate cannot be written',
        "        pass",
        "guard encode check removed",
    ),
    ("src/intake/sink_guard.py", "_DIGITS.fullmatch(s)", "_DIGITS.match(s)", "guard numeric uses match"),
    ("src/intake/sink_guard.py", "return str(int(s))", "return s", "guard numeric not normalised"),
    ("src/intake/sink_guard.py", '_DIGITS = re.compile(r"[0-9]+")', '_DIGITS = re.compile(r"\\d+")', "guard unicode digits accepted"),
    (
        "src/intake/sink_guard.py",
        'NUMERIC = frozenset({"total_minor", "line_count"})',
        'NUMERIC = frozenset({"line_count"})',
        "guard total not numeric",
    ),
    (
        "src/intake/sink_guard.py",
        'if column not in COLUMNS:\n        raise BadCell("unknown column")',
        "pass",
        "guard unknown column allowed",
    ),
    (
        "src/intake/sink_guard.py",
        'if not isinstance(value, str):\n        raise BadCell(f"{column} must be text")',
        "value = str(value)",
        "guard non-text allowed",
    ),
    ("src/intake/sink_guard.py", "if set(row) != set(COLUMNS):", "if False:", "guard row key check removed"),
    (
        "src/intake/sink_guard.py",
        "return {c: guard_cell(c, row[c]) for c in COLUMNS}",
        "return {c: (row[c] if c == 'approved_by' else guard_cell(c, row[c])) for c in COLUMNS}",
        "guard row skips the approver",
    ),
    ("src/intake/csvsink.py", "quoting=csv.QUOTE_ALL", "quoting=csv.QUOTE_MINIMAL", "sink quotes only when needed"),
    ("src/intake/csvsink.py", "guarded = [guard_row(r) for r in rows]", "guarded = [dict(r) for r in rows]", "sink writes rows unguarded"),
    ("src/intake/csvsink.py", 'encoding="utf-8", newline=""', 'encoding="utf-8-sig", newline=""', "sink writes a BOM"),
    ("src/intake/csvsink.py", 'lineterminator="\\n"', 'lineterminator="\\r\\n"', "sink writes CRLF"),
    (
        "src/intake/csvsink.py",
        "os.replace(tmp, path)",
        "os.replace(path, tmp) if False else open(path, 'ab').write(tmp.read_bytes())",
        "sink appends instead of replacing",
    ),
    ("src/intake/csvsink.py", "            w.writerow(COLUMNS)\n", "", "sink header missing"),
    ("src/intake/csvsink.py", "                tmp.unlink(missing_ok=True)", "                pass", "sink temp file not removed on error"),
    ("src/intake/csvsink.py", "    except BaseException as e:", "    except Exception as e:", "sink temp file not removed on a signal"),
    (
        "src/intake/csvsink.py",
        'return getattr(e, "winerror", None) in _LOCKED_WINERRORS or e.errno in (errno.EBUSY, errno.ETXTBSY)',
        "return True",
        "every OS error reported as locked",
    ),
    (
        "src/intake/csvsink.py",
        'return getattr(e, "winerror", None) in _LOCKED_WINERRORS or e.errno in (errno.EBUSY, errno.ETXTBSY)',
        "return False",
        "no OS error reported as locked",
    ),
    ("src/intake/csvsink.py", "return len(guarded)", "return 0", "sink row count wrong"),
    ("src/intake/csvsink.py", "mode=0o700", "mode=0o777", "sink folder mode open (POSIX)"),
    ("src/intake/csvsink.py", "            os.fsync(f.fileno())\n", "", "sink file not fsynced"),
]

# the tests a WP5 mutant is run against (the exporter, its history and result semantics, the pipeline wiring, the sink and its guard): `--group WP5`
WP5_TESTS = [
    "tests/test_exporter.py",
    "tests/test_exporter_history.py",
    "tests/test_pipeline_check.py",
    "tests/test_sink_guard.py",
    "tests/test_sink_scope.py",
]


# ---- group WP6: the service work package (brief-v3 15.7) ----------------------------------------------------------------------------------------------
# Package 6k starts the list with the mutants of its own additive edits; 6a to 6e append theirs (each line names its expected killer). Every pattern must
# match exactly once (`--group WP6 --check`); only assertion failures count as kills (`judge`). `--group WP6` runs the tests in WP6_TESTS: each package
# adds its test files there when it adds mutants.
WP6_TESTS = ["tests/test_wp6_kickoff.py", "tests/test_routes_have_roles.py", "tests/test_scan.py"]
_HALT_HEAD = '    p = ledger_path(s)\n    if not _exists(p):\n        return None\n    try:\n        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)\n        try:\n            '
WP6 = [
    # 6k: killed by halt_state_readonly_states
    ("src/intake/budget.py", 'return (False, "") if v == "0" else None', 'return (False, "")', "absent halted key read as not halted"),
    (
        "src/intake/budget.py",
        _HALT_HEAD + 'v = _meta(c, "halted")',
        _HALT_HEAD.replace("return None", 'return False, ""') + 'v = _meta(c, "halted")',
        "missing ledger read as not halted",
    ),
    (
        "src/intake/budget.py",
        '        return None\n    if v == "1":',
        '        return False, ""\n    if v == "1":',
        "database error read as not halted",
    ),
    # 6k: killed by total_settled_readonly_matches_ledger, page_reads_never_block_settle
    (
        "src/intake/budget.py",
        _HALT_HEAD + "return _settled_total(c)",
        _HALT_HEAD.replace("return None", "return 0") + "return _settled_total(c)",
        "missing ledger read as zero spend",
    ),
    (
        "src/intake/budget.py",
        _HALT_HEAD + "return _settled_total(c)",
        _HALT_HEAD.replace("?mode=ro", "?mode=rw") + 'c.execute("BEGIN IMMEDIATE")\n            return _settled_total(c)',
        "settled total takes a write lock",
    ),
    # 6k: killed by connect_readonly_cannot_write, connect_readonly_refuses_non_wal
    (
        "src/intake/workqueue.py",
        '+ "?mode=ro", uri=True, timeout=BUSY_TIMEOUT_S',
        '+ "?mode=rwc", uri=True, timeout=BUSY_TIMEOUT_S',
        "read-only queue connection can write",
    ),
    (
        "src/intake/workqueue.py",
        'PRAGMA journal_mode").fetchone()[0]).lower() != "wal"',
        'PRAGMA journal_mode").fetchone()[0]).lower() == "never"',
        "read-only queue connection accepts a non-WAL file",
    ),
    (
        "src/intake/workqueue.py",
        "        _check_version(conn)\n    except BaseException:\n        conn.close()\n        raise\n    return conn\n\n\ndef _precreate",
        "    except BaseException:\n        conn.close()\n        raise\n    return conn\n\n\ndef _precreate",
        "read-only queue connection skips the version check",
    ),
    # 6k: killed by known_sources_lists_every_hash
    (
        "src/intake/workqueue.py",
        '"SELECT source_sha256 FROM items"',
        "\"SELECT source_sha256 FROM items WHERE state != 'REJECTED'\"",
        "known sources skip rejected items",
    ),
    # 6k: killed by readers_use_given_conn, preview_rows_on_readonly_conn (a reader opens its own connection although it was given one)
    (
        "src/intake/workqueue.py",
        "    if conn is not None:\n        return get_in(conn, item_id_)",
        "    if False:\n        return get_in(conn, item_id_)",
        "get ignores the connection it is given",
    ),
    (
        "src/intake/workqueue.py",
        '    if state is None:\n        return _rows(conn, "SELECT * FROM items ORDER BY created_at, uid")',
        '    conn = connect(s)\n    if state is None:\n        return _rows(conn, "SELECT * FROM items ORDER BY created_at, uid")',
        "list_items ignores the connection it is given",
    ),
    (
        "src/intake/workqueue.py",
        "    if conn is None:\n        with opened(s) as own:\n            return unreadable_ids(",
        "    if True:\n        with opened(s) as own:\n            return unreadable_ids(",
        "unreadable_ids ignores the connection it is given",
    ),
    (
        "src/intake/workqueue.py",
        "    if conn is None:\n        with opened(s) as own:\n            return known_sources(",
        "    if True:\n        with opened(s) as own:\n            return known_sources(",
        "known_sources ignores the connection it is given",
    ),
    (
        "src/intake/exporter.py",
        "    out: list[PreviewRow] = []\n    for item in workqueue.approved_unexported(conn):",
        "    out: list[PreviewRow] = []\n    conn = workqueue.connect(s)\n    for item in workqueue.approved_unexported(conn):",
        "preview_rows ignores the connection it is given",
    ),
    # 6k: killed by read_log_level, blank_lookalikes_public_alias, new_codes_listed
    ("src/intake/settings.py", "    if v not in LOG_LEVELS:", "    if False:", "log level not validated"),
    (
        "src/intake/settings.py",
        'env.get("INTAKE_LOG", "") or "normal"',
        'env.get("INTAKE_LOG", "") or "verbose"',
        "log level defaults to verbose",
    ),
    (
        "src/intake/decisions.py",
        "BLANK_LOOKALIKES = _BLANK_LOOKALIKES",
        "BLANK_LOOKALIKES = frozenset(sorted(_BLANK_LOOKALIKES))",
        "blank lookalikes alias is a copy",
    ),
    ("src/intake/codes.py", '        "too_many_attempts",\n', "", "a WP6 code missing from the closed set"),
    # 6k: killed by routes_import_validation, match_is_exact_and_per_listener
    ("src/intake/routes.py", 'if r.app == "dash" and r.writes:', "if False and r.writes:", "a dashboard row may write"),
    ("src/intake/routes.py", 'and "csrf" not in r.fields:', "and False:", "a session POST may lack csrf"),
    (
        "src/intake/routes.py",
        "        if r.app != app:\n            continue",
        "        if False:\n            continue",
        "route served on the wrong listener",
    ),
    # 6b: the scan and the bounded reader (brief 8, 15.7). "[posix]" mutants change a POSIX-only branch: the Windows run skips them, the Linux run kills them
    (
        "src/intake/inbox.py",
        "path = Path(name) if dir_fd is not None else inbox / name\n    if st is None:",
        "path = inbox / name\n    if st is None:",
        "dir_fd dropped, path opened by full name [posix]",
    ),
    ("src/intake/inbox.py", "| O_NONBLOCK, dir_fd=dir_fd)", ", dir_fd=dir_fd)", "O_NONBLOCK removed [posix]"),
    ("src/intake/inbox.py", "os.O_RDONLY | O_NOFOLLOW |", "os.O_RDONLY |", "O_NOFOLLOW removed (symlink swap read) [posix]"),
    (
        "src/intake/inbox.py",
        "if st.st_nlink != 1 or not _same_file(st, st0):",
        "if st.st_nlink != 1:",
        "fstat identity check removed",
    ),
    (
        "src/intake/inbox.py",
        "if len(run.items) >= s.service.scan_max_files:",
        "if len(run.items) + run.duplicates >= s.service.scan_max_files:",
        "duplicates take a slot",
    ),
    (
        "src/intake/inbox.py",
        'if parsed.flag is None and reader.gate_decision(parsed, cfg.load_hash_list(listed_path)) == "not_on_list":',
        "if False:",
        "gate not re-checked before insert",
    ),
    (
        "src/intake/inbox.py",
        "if -FUTURE_MTIME_S <= age < s.service.scan_min_age_s:",
        "if -FUTURE_MTIME_S <= age >= s.service.scan_min_age_s:",
        "min-age flipped",
    ),
    (
        "src/intake/inbox.py",
        "if stat.S_ISDIR(st.st_mode) and not is_link:",
        "if False:",
        "subfolders examined instead of ignored",
    ),
    (
        "src/intake/inbox.py",
        "finally:" + chr(10) + "            _SCAN_LOCK.release()",
        "finally:" + chr(10) + "            pass",
        "scan lock not released",
    ),
    (
        "src/intake/inbox.py",
        "halt = budget.halt_state_readonly(s, raise_busy=True)",
        'halt = budget.halt_state_readonly(s, raise_busy=True) or (False, "")',
        "halt unreadable treated as not halted",
    ),
    ("src/intake/inbox.py", "if halt[0]:", "if False:", "halted ledger scanned anyway"),
    (
        "src/intake/inbox.py",
        "if _change_key(st) != _change_key(st0):",
        "if False:",
        "changed-during-read check removed",
    ),
    ("src/intake/inbox.py", "if st.st_nlink != 1 or not _same_file(st, st0):", "if not _same_file(st, st0):", "hard link check removed"),
    # Killed only because the refusal CODE changes (a link then falls to not_a_file instead of outside_inbox): the link is still never read, because
    # the S_ISREG check refuses it next. The O_NOFOLLOW mutant above is the one that proves the open itself does not follow a swapped-in link.
    (
        "src/intake/inbox.py",
        "if stat.S_ISLNK(st0.st_mode) or sys.platform",
        "if sys.platform",
        "symlink refusal removed from read_plain_file [posix]",
    ),
    (
        "src/intake/inbox.py",
        'if sys.platform == "win32" and st0.st_ino == 0:',
        "if False:",
        "volume without file id accepted [win]",
    ),
    ("src/intake/inbox.py", "if len(self.refused) < MAX_REFUSED:", "if True:", "refused list uncapped"),
    (
        "src/intake/inbox.py",
        "except FileNotFoundError:  # gone when looked at",
        "except ZeroDivisionError:  # gone when looked at",
        "a vanished file is refused, not skipped",
    ),
    (
        "src/intake/inbox.py",
        "chunk = read(min(_CHUNK, cap + 1 - len(out)))",
        "chunk = read(min(_CHUNK, cap - len(out)))",
        "read cap off by one: a file one byte over is cut, not refused",
    ),
    (
        "src/intake/inbox.py",
        "                        if sha in known or sha in seen:",
        "                        if sha in seen:",
        "known duplicates not skipped before the gate",
    ),
    ("src/intake/inbox.py", "run.examined += not counted", "pass", "a refused entry whose lstat failed is not counted as examined"),
    (
        "src/intake/inbox.py",
        "        raise missing from None\n    try:\n        src = dir_fd",
        "        raise\n    try:\n        src = dir_fd",
        "a missing inbox leaks a raw OSError [posix]",
    ),
    (
        "src/intake/inbox.py",
        'missing = InboxUnavailable("the inbox folder',
        'missing = ConfigError("bad_config", "the inbox folder',
        "an unavailable inbox is a plain ConfigError (6d would answer 500, or 503 for every config error)",
    ),
    (
        "src/intake/inbox.py",
        'raise InboxUnavailable("this volume has no file ids")',
        'raise ConfigError("bad_config", "this volume has no file ids")',
        "a volume without file ids is a plain ConfigError [win]",
    ),
    (
        "src/intake/inbox.py",
        "key = (st.st_size, st.st_mtime_ns)",
        "key = (st.st_size,)",
        "modification-time term dropped from the change check [win]",
    ),
    # on POSIX the change time also moves on a rewrite, so the mtime mutant above is equivalent there: it is run on Windows only
    (
        "src/intake/inbox.py",
        "key += (st.st_ctime_ns,)",
        "key += ()",
        "change-time term dropped from the change check [posix]",
    ),
    (
        "src/intake/inbox.py",
        "    if not _same_file(after, st) or _change_key(after) != _change_key(st):",
        "    if False:",
        "scan does not compare its filter lstat after the read",
    ),
    (
        "src/intake/inbox.py",
        "            except OSError:" + chr(10) + "                raise missing from None",
        "            except OSError:" + chr(10) + "                raise",
        "an unreadable inbox listing leaks a raw OSError",
    ),
    (
        "src/intake/inbox.py",
        "            raise missing\n    try:\n        dir_fd =",
        "            pass\n    try:\n        dir_fd =",
        "a junctioned inbox is scanned [win]",
    ),
    (
        "src/intake/inbox.py",
        "            (n, None, h, k) for n, h, k in extras",
        "",
        "files that wait never fill a slot freed by a refusal",
    ),
    # 6b fix batch (BL-intake-wp6-6b-003 .. 009)
    (
        "src/intake/pipeline.py",
        'parsed.source_sha256, "", s.tenant_id, stem, parsed.flag)',
        "parsed.source_sha256, parsed.text, s.tenant_id, stem, parsed.flag)",
        "a flagged too-long file stores its full text",
    ),
    ("src/intake/inbox.py", "elif self._mono() >= t_end - MIN_READ_S:", "elif False:", "scan has no deadline"),
    ("src/intake/inbox.py", "if run.reads >= MAX_READS:", "if False:", "scan has no read cap"),
    (
        "src/intake/inbox.py",
        "                    run.reads += 1" + chr(10),
        "                    pass" + chr(10),
        "skip-cache misses are not counted against the read cap",
    ),
    (
        "src/intake/inbox.py",
        "_open_and_list(inbox, self._cursor, MAX_LISTED,",
        "_open_and_list(inbox, self._cursor, 10**9,",
        "directory listing uncapped",
    ),
    ("src/intake/inbox.py", "elif self._skip_hit(", "elif False and self._skip_hit(", "known files are read again on every scan"),
    (
        "src/intake/inbox.py",
        "        if gate_hash is not None and gate_hash not in listed:",
        "        if gate_hash is not None and gate_hash not in listed and False:",
        "a remembered unlisted file ignores the made-up list that it is checked against",
    ),
    (
        "src/intake/inbox.py",
        "                self._partial = run.result()\n                self._refused = tuple(run.refused)",
        "                self._partial = None\n                self._refused = tuple(run.refused)",
        "a scan that raises keeps no partial result",
    ),
    (
        "src/intake/inbox.py",
        "            self._partial = None" + chr(10) + "            try:",
        "            pass" + chr(10) + "            try:",
        "a good scan leaves the partial result of an earlier failed scan in place",
    ),
    ("src/intake/inbox.py", "run.young += 1", "pass", "young files are not counted"),
    ("src/intake/inbox.py", "if _file_key(name, st) != expect_key:", "if False:", "a waiting file is not compared with its first look"),
    (
        "src/intake/inbox.py",
        '                    run.refuse(name, "changed_while_read")' + chr(10) + "                    return None",
        "                    return None",
        "a waiting file whose bytes changed is dropped without a refusal",
    ),
    (
        "src/intake/inbox.py",
        "                    run.examined -= 1  # it was counted as waiting",
        "                    pass  # it was counted as waiting",
        "a waiting file that vanished stays counted as examined",
    ),
    (
        "src/intake/budget.py",
        'if raise_busy and ("locked" in str(e) or "busy" in str(e)):',
        "if False:",
        "a busy ledger is reported as missing",
    ),
    (
        "src/intake/inbox.py",
        "    if e.code not in REFUSAL_CODES:" + chr(10) + "        raise e",
        "    if False:" + chr(10) + "        raise e",
        "an unexpected refusal code is relabelled",
    ),
    (
        "src/intake/inbox.py",
        "root = inbox.resolve()  # BEFORE",
        "root = inbox  # BEFORE",
        "the folder is not resolved before the link tests [win]",
    ),
    (
        "src/intake/inbox.py",
        "except (OSError, RuntimeError):",
        "except RuntimeError:",
        "a failing folder resolve leaks a raw OSError [win]",
    ),
    (
        "src/intake/cli.py",
        'if e.code == "outside_inbox":  # the reader',
        "if False:  # the reader",
        "extract shows the inbox wording for a link",
    ),
    # 6b fix batch 4 (round-3 reviews of 925e0cd)
    ("src/intake/inbox.py", "if v[-1] > now}", "if True}", "expired memory entries are never dropped"),
    ("src/intake/inbox.py", "            if n % 1024 == 0 and expired():", "            if False:", "listing ignores the deadline"),
    ("src/intake/inbox.py", "                    if cur is None or k > cur:", "                    if True:", "listing ignores the cursor"),
    ("src/intake/inbox.py", "            yield (m, e.name)", "            yield (0, e.name)", "listing is not oldest first"),
    (
        "src/intake/inbox.py",
        "                elif self._mono() >= t_end - MIN_READ_S:",
        "                elif self._mono() >= t_end:",
        "a read starts with less than the minimum time left",
    ),
    (
        "src/intake/inbox.py",
        "                                        if gate_hash is not None and (gate_hash in known_text or gate_hash in seen_text):",
        "                                        if False:",
        "variants of one text are not recognised",
    ),
    (
        "src/intake/inbox.py",
        "or (gate_hash is not None and (gate_hash in known_text or gate_hash in seen_text))",
        "",
        "remembered variants are read again",
    ),
    (
        "src/intake/inbox.py",
        "if parsed.flag is not None and not self._flag_ok(open_flagged, run):",
        "if False:",
        "hand-back items are not capped",
    ),
    ("src/intake/inbox.py", "and open_flagged + run.flagged_made < MAX_FLAGGED_OPEN", "", "queue size does not cap hand-back items"),
    (
        "src/intake/inbox.py",
        "if -FUTURE_MTIME_S <= age < s.service.scan_min_age_s:",
        "if 0 <= age < s.service.scan_min_age_s:",
        "a negative age is not young",
    ),
    ("src/intake/inbox.py", "        elif isinstance(e, PermissionError):", "        elif False:", "a sharing violation is remembered"),
    (
        "src/intake/inbox.py",
        "        if isinstance(e, ConfigError | MemoryError | RecursionError):",
        "        if isinstance(e, ConfigError):",
        "memory errors are swallowed as poison pills",
    ),
    (
        "src/intake/inbox.py",
        '                                if name.endswith((".", " ")) or not (',
        "                                if not (",
        "names ending in dot or space are accepted [posix]",
    ),
    (
        "src/intake/inbox.py",
        "                            run.examined -= counted\n                            run.vanished += 1",
        "                            run.examined -= counted",
        "a vanished name is not counted",
    ),
    ("src/intake/names.py", 'piece = "\\\\\\\\" if ch == "\\\\" else ', "piece = ", "a literal backslash is not doubled"),
    ("src/intake/names.py", "if limit is not None and size + len(piece) > limit:", "if False:", "a long name is not cut"),
    ("src/intake/inbox.py", "        if old is not None and old != key:", "        if False:", "stale same-name keys stay"),
    (
        "src/intake/inbox.py",
        "        self._skip[key] = self._skip.pop(key)  # least-recently-used",
        "        pass  # least-recently-used",
        "memory is not least-recently-used",
    ),
    (
        "src/intake/inbox.py",
        "                        elif sum(t.is_alive() for t in self._abandoned) >= MAX_ABANDONED:",
        "                        elif False:",
        "reads start while too many abandoned ones hang",
    ),
    (
        "src/intake/inbox.py",
        "                            elif name == hung_now:",
        "                            elif False:",
        "the file whose lstat hung is not refused",
    ),
    ("src/intake/inbox.py", "            if name in self._hung:", "            if False:", "a hung file is looked at again"),
    (
        "src/intake/inbox.py",
        "        if close_fd is not None:\n            os.close(close_fd)\n        raise _WorkerFailed",
        "        raise _WorkerFailed",
        "the descriptor leaks when the worker cannot start [posix]",
    ),
    (
        "src/intake/inbox.py",
        "        except OSError:\n            raise _WorkerFailed from None",
        "        except ZeroDivisionError:\n            raise _WorkerFailed from None",
        "a failing dup is a file verdict [posix]",
    ),
    (
        "src/intake/inbox.py",
        '            self._remember_refused(key, "read_timeout")\n                    run.ended = "deadline"\n                    return None',
        '            run.ended = "deadline"\n                    return None',
        "a hung second look is not remembered",
    ),
    # 6b fix batch 2 (round-2 reviews)
    (
        "src/intake/inbox.py",
        "return cls(safe_name(raw_name, MAX_NAME_SHOWN), reason)",
        "return cls(str(raw_name), reason)",
        "a refusal name keeps its control and bidirectional characters",
    ),
    ("src/intake/inbox.py", " or any(name_char_forbidden(c) for c in self.name)", "", "the Refusal constructor accepts an unsafe name"),
    (
        "src/intake/names.py",
        "    return safe_text.is_forbidden(ch, keep_whitespace=False) or any(",
        "    return safe_text.is_forbidden(ch, keep_whitespace=True) or any(",
        "names treat newline and tab as harmless",
    ),
    ("src/intake/names.py", "    (0xD800, 0xDFFF),\n", "", "lone surrogates are not escaped"),
    ("src/intake/names.py", "    (0x034F, 0x034F),\n    (0x115F, 0x1160),\n", "", "invisible and lookalike code points are not escaped"),
    ("src/intake/names.py", 'else f"\\\\U{o:08x}"', 'else f"\\\\u{o:04x}"', "code points above U+FFFF are cut to four digits"),
    (
        "src/intake/inbox.py",
        "_open_and_list(inbox, self._cursor, MAX_LISTED",
        "_open_and_list(inbox, None, MAX_LISTED",
        "the pass always starts at the top (flood of early-sorting files starves later ones)",
    ),
    (
        "src/intake/inbox.py",
        "run.unlisted = after - len(got)",
        "run.unlisted = 0",
        "entries outside the slice are not reported as remaining",
    ),
    (
        "src/intake/inbox.py",
        "self._cursor = got[wi - 1] if wi > 0 else cursor0",
        "pass",
        "an unfinished pass moves past a file that still waits for a slot",
    ),
    (
        "src/intake/inbox.py",
        "        if key[1] == 0 or key[2] == 0:",
        "        if False:",
        "memory served for a file without device or file id",
    ),
    (
        "src/intake/inbox.py",
        "    return (name, st.st_dev, st.st_ino, *_change_key(st))",
        "    return (st.st_dev, st.st_ino, *_change_key(st))",
        "the file name is not part of the memory key",
    ),
    ("src/intake/inbox.py", "elif age < -FUTURE_MTIME_S:", "elif False:", "a far-future modification time is accepted"),
    (
        "src/intake/inbox.py",
        "                    except Exception as e:  # noqa: BLE001",
        "                    except ZeroDivisionError as e:  # noqa: BLE001",
        "one poisonous file stops the whole scan",
    ),
    (
        "src/intake/inbox.py",
        "                    self._remember_refused(key, e.code)  # remembered",
        "                    pass  # remembered",
        "insert-step refusals are not remembered",
    ),
    (
        "src/intake/inbox.py",
        "                run.waiting = len(new) + len(extras)",
        "                pass",
        "an error while listing loses the waiting count",
    ),
    (
        "src/intake/inbox.py",
        "                run.examined -= counted  # the file in flight",
        "                pass  # the file in flight",
        "an error while listing keeps the in-flight file as examined",
    ),
    ("src/intake/inbox.py", 'if "v" not in box and "e" not in box:', "if False:", "a hung read is waited for without limit"),
    (
        "src/intake/inbox.py",
        "fd = os.dup(dir_fd)",
        "fd = dir_fd",
        "[posix] the abandoned reader shares the folder descriptor that the scan closes",
    ),
    (
        "src/intake/inbox.py",
        "        known = workqueue.known_sources(s, readonly=True)",
        "        known = workqueue.known_sources(s)",
        "the scan reads the queue through a read-write connection",
    ),
    (
        "src/intake/inbox.py",
        "                except Exception:  # noqa: BLE001, S110",
        "                except ZeroDivisionError:  # noqa: BLE001, S110",
        "an exception that cannot carry the partial result hides itself",
    ),
    (
        "src/intake/inbox.py",
        "run.error = safe_text.clean(e.code if isinstance(e, Refused | ConfigError) else type(e).__name__)",
        "run.error = str(getattr(e, 'code', type(e).__name__))",
        "the error text is not made safe",
    ),
    (
        "src/intake/inbox.py",
        "        if sha in known or sha in seen or (",
        "        if sha in seen or (",
        "a remembered duplicate of a stored item is read again",
    ),
    (
        "src/intake/workqueue.py",
        'return Refused("db_busy", "the queue is busy") if busy else Refused("stored_data_bad", "the queue file cannot be read")',
        'return Refused("db_busy", "the queue is busy")',
        "a damaged queue file is reported as busy",
    ),
    (
        "src/intake/cli.py",
        "data = inbox.read_plain_file(path, s.service.max_file_bytes)",
        "data = path.read_bytes()",
        "extract reads with its own unbounded reader",
    ),
]


def judge(rc: int, junit: str) -> str:
    """SURVIVED = the suite passed (rc 0). KILLED = rc 1, no `<error>` element, and the first recorded `<failure>` message is an assertion (`assert ...`,
    `AssertionError`, or pytest's `Failed:` such as DID NOT RAISE). CRASH = anything else that is not a pass: any other exit code (interrupted, internal
    error, usage error, no tests), a collection or setup error, a failure that is another exception type (AttributeError ...) or an unreadable report.
    (Before: every non-zero exit code counted as a kill.)"""
    if rc == 0:
        return "SURVIVED"
    if rc != 1:
        return "CRASH"
    if re.search(r"<error\b", junit):
        return "CRASH"
    m = re.search(r'<failure\b[^>]*?\bmessage="([^"]*)"', junit)
    if m is None:
        return "CRASH"
    message = html.unescape(m.group(1)).lstrip()
    return "KILLED" if message.startswith(("assert", "AssertionError", "Failed:")) else "CRASH"


TIMEOUT_S = 900


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False)  # noqa: S603, S607
    else:
        proc.kill()
    proc.communicate()


def run(group: str, muts: list, only: str | None, out: list[str], tests: tuple[str, ...] = ()) -> tuple[int, int, int, int]:
    killed = survived = skipped = crashed = 0
    for path, a, b, name in muts:
        if only and only not in name:
            continue
        full = ROOT / path
        orig = full.read_bytes().decode("utf-8")
        if a == b or a not in orig:
            line = f"SKIP     [{group}] {name}: pattern not found in {path}"
            print(line, flush=True)
            out.append(line)
            skipped += 1
            continue
        full.write_bytes(orig.replace(a, b, 1).encode("utf-8"))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                report = Path(tmp) / "junit.xml"
                cmd = ["uv", "run", "--group", "test", "pytest", "-q", "-x", "-p", "no:cacheprovider", f"--junitxml={report}", *tests]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)  # noqa: S603
                try:
                    stdout, _ = proc.communicate(timeout=TIMEOUT_S)
                    verdict = judge(proc.returncode, report.read_text(encoding="utf-8") if report.exists() else "")
                    first = next((ln for ln in stdout.splitlines() if ln.startswith(("FAILED", "ERROR"))), "")
                except subprocess.TimeoutExpired:
                    _kill_tree(proc)  # subprocess.run(timeout=) only kills uv and then hangs on the pipe held by pytest (seen on Windows)
                    verdict, first = "CRASH", "TIMEOUT"
            line = f"{verdict:<9}[{group}] {name}  {first[:110]}"
            print(line, flush=True)
            out.append(line)
            killed += verdict == "KILLED"
            survived += verdict == "SURVIVED"
            crashed += verdict == "CRASH"
        finally:
            full.write_bytes(orig.encode("utf-8"))
    return killed, survived, skipped, crashed


# ---- group QUEUE: queue, decisions, content code, database triggers (WP4) -------------------------------------------------------------------------------
# Each entry: (file, old text, new text, name, expected killer as a pytest -k expression, timing-dependent). The expected killer is run FIRST (alone, no -x); only
# if it does not kill is the whole queue test set run, and the mutant is then reported KILLED-ELSEWHERE, which fails the group (the list is stale or a test is weak).
# Before the mutants: a baseline (the queue tests unmodified must be green), an identity mutant (must be green) and a no-op mutant (a comment change must SURVIVE).
QUEUE_TESTS = (
    "tests/test_triggers.py",
    "tests/test_decisions.py",
    "tests/test_workqueue.py",
    "tests/test_content_code.py",
    "tests/test_queue_store.py",
    "tests/test_queue_hardening.py",
    "tests/test_queue_processes.py",
)
QS, WQ, DC, CC = "src/intake/queue_schema.py", "src/intake/workqueue.py", "src/intake/decisions.py", "src/intake/content_code.py"
STMT = "test_the_statement_fails_with_only_its_trigger_and_succeeds_without_it"
TRIGGER_KILLERS = {
    "intake_a_reject_only_insert": "a_insert",
    "intake_a_reject_only_update": "a_update",
    "intake_b_immutable": "b_",
    "intake_c_null_fields_insert": "c_insert",
    "intake_c_null_fields_update": "c_update",
    "intake_d_items_delete": "d_delete_item",
    "intake_d_decisions_update": "d_update_decisions",
    "intake_d_decisions_delete": "d_delete_decisions",
    "intake_d_exports_update": "d_update_exports",
    "intake_d_exports_delete": "d_delete_exports",
    "intake_d_purges_update": "d_update_purges",
    "intake_d_purges_delete": "d_delete_purges",
    "intake_d_decisions_insert_exists": "d_replace_decision",
    "intake_d_exports_insert_exists": "d_replace_export",
    "intake_d_purges_insert_exists": "d_replace_purge",
    "intake_e_exports_insert": "e_",
    "intake_f_transitions": "f_",
    "intake_g_approved_needs_decision": "g_",
    "intake_h_exported_needs_export": "h_",
    "intake_k_insert_states": "k_insert_state",
    "intake_k_insert_exists": "k_replace",
    "intake_i_decisions_item": "i_item_state or i_missing_item",
    "intake_i_decisions_code": "i_code",
    "intake_j_approve_guard": "j_flag or j_null",
    "intake_j2_approve_reason": "j2_",
    "intake_d_meta_update": "d_update_meta",
    "intake_d_meta_delete": "d_delete_meta",
}
QUEUE = [
    (
        QS,
        "    def add(name: str, when_on: str, msg: str) -> None:\n",
        "    def add(name: str, when_on: str, msg: str) -> None:\n"
        f"        if name == '{name}':\n            when_on = when_on.split(' WHEN ')[0] + ' WHEN 0'\n",
        f"disable trigger {name}",
        f"{STMT} and ({k})",
        False,
    )
    for name, k in TRIGGER_KILLERS.items()
] + [
    (QS, "guarded = \"NEW.state IN ('APPROVED', 'EXPORTED')\"", "guarded = \"NEW.state IN ('APPROVED')\"", "a: EXPORTED not guarded", "a_insert_EXPORTED or a_update_EXPORTED", False),
    (QS, 'parts.append(f"instr({col}, char(92)) > 0")', "pass", "a: backslash clause removed", "json_escape", False),
    (QS, "for c in flags.reject_only_codes():", "for c in flags.reject_only_codes()[:-1]:", "a: last reject-only code not guarded", "a_insert_APPROVED_X28", False),
    (QS, "parts.append(f\"instr({col}, '\\\"{c}\\\"') > 0\")", "parts.append(f\"instr({col}, '{c}') > 0\")", "a: match not JSON-quoted", "test_a_is_exact", False),
    (QS, "WHEN OLD.state <> 'RECEIVED' AND ({changed})", "WHEN OLD.state NOT IN ('RECEIVED', 'READY') AND ({changed})", "b: READY rows are free", "b_fields_json_READY", False),
    *[
        (QS, f'"{col}",', "", f"b: {col} not frozen", f"{STMT} and b_{col}", False)
        for col in ("source_sha256", "tenant_id", "fields_json", "flags_json", "failing_fields_json", "source_text", "model_id", "prompt_sha256", "cost_micro", "created_at", "source_name")
    ],
    (QS, "nf = \"NEW.state IN ('READY', 'APPROVED', 'EXPORTED')", "nf = \"NEW.state IN ('APPROVED', 'EXPORTED')", "c: READY allowed without fields", "c_insert_READY or c_update_READY", False),
    (QS, "nf = \"NEW.state IN ('READY', 'APPROVED', 'EXPORTED')", "nf = \"NEW.state IN ('READY', 'APPROVED')", "c: EXPORTED allowed without fields", "c_insert_EXPORTED or c_update_EXPORTED", False),
    (QS, "WHEN OLD.state IN ('APPROVED', 'EXPORTED')\", \"approved item", "WHEN OLD.state IN ('EXPORTED')\", \"approved item", "d: APPROVED item deletable", "d_delete_item_APPROVED", False),
    (QS, "WHEN OLD.state IN ('APPROVED', 'EXPORTED')\", \"approved item", "WHEN OLD.state IN ('APPROVED')\", \"approved item", "d: EXPORTED item deletable", "d_delete_item_EXPORTED", False),
    (QS, '("exports", ("seq", "row_id", "item_uid"))', '("exports", ("seq", "row_id"))', "d: export item_uid clash not detected", "d_replace_export_by_item_uid", False),
    (QS, '("exports", ("seq", "row_id", "item_uid"))', '("exports", ("seq", "item_uid"))', "d: export row_id clash not detected", "d_replace_export_by_row_id", False),
    (QS, "= 'approve:' || NEW.content_code)", "LIKE 'approve:%')", "e: content code not compared", "e_stale_code", False),
    (QS, "ORDER BY d.seq DESC LIMIT 1) \"\n        \"= 'approve:'", "ORDER BY d.seq ASC LIMIT 1) \"\n        \"= 'approve:'", "e: oldest decision instead of latest", "e_latest_is_reject", False),
    (QS, "i.uid = NEW.item_uid AND i.state = 'APPROVED' \"", "i.uid = NEW.item_uid AND i.state IN ('APPROVED', 'EXPORTED') \"", "e: EXPORTED item accepted", "e_item_state_EXPORTED", False),
    (QS, "NEW.state IN ('READY', 'NEEDS_PERSON')) \"", "NEW.state IN ('READY', 'NEEDS_PERSON', 'APPROVED')) \"", "f: RECEIVED may go to APPROVED", "f_RECEIVED_to_APPROVED", False),
    (QS, "NEW.state IN ('APPROVED', 'REJECTED')) \"", "NEW.state IN ('APPROVED', 'REJECTED', 'EXPORTED')) \"", "f: READY may go to EXPORTED", "f_READY_to_EXPORTED", False),
    (QS, "NEW.state = 'EXPORTED'))\"", "NEW.state IN ('EXPORTED', 'REJECTED')))\"", "f: APPROVED may go to REJECTED", "f_APPROVED_to_REJECTED", False),
    (QS, "'') <> 'approve'\"", "'') = 'reject'\"", "g: latest decision not compared", "g_no_decision", False),
    (QS, "WHERE d.item_uid = OLD.uid ORDER BY d.seq DESC", "WHERE d.item_uid = OLD.uid ORDER BY d.seq ASC", "g: oldest decision instead of latest", "g_latest_reject_after_approve", False),
    (QS, "WHERE d.item_uid = OLD.uid ORDER BY d.seq DESC", "WHERE 1 ORDER BY d.seq DESC", "g: any item's decision counts", "g_decision_of_another_item", False),
    (QS, "(SELECT 1 FROM exports e WHERE e.item_uid = OLD.uid)", "(SELECT 1 FROM exports e)", "h: any export row counts", "h_export_of_another_item", False),
    (QS, "WHEN NEW.state IN ('APPROVED', 'REJECTED', 'EXPORTED')\"", "WHEN NEW.state IN ('APPROVED', 'EXPORTED')\"", "k: REJECTED insert allowed", "k_insert_state_REJECTED", False),
    (QS, "x.id = NEW.id OR ", "0 OR ", "k: same id not detected", "k_replace_same_id or k_replace_by_id", False),
    (QS, "OR x.source_sha256 = NEW.source_sha256 ", "OR 0 ", "k: same hash not detected", "k_replace_same_hash", False),
    (QS, "OR (NEW.uid IS NOT NULL AND x.uid = NEW.uid))", "OR 0)", "k: same uid not detected", "k_replace_by_uid", False),
    (QS, "i.state IN ('READY', 'NEEDS_PERSON'))\",", "i.state NOT IN ('REJECTED', 'APPROVED', 'EXPORTED'))\",", "i: RECEIVED item decidable", "i_item_state_RECEIVED", False),
    (QS, "length(NEW.content_code) <> 64", "length(NEW.content_code) < 64", "i: long content code allowed", "i_code_long", False),
    (QS, "length(NEW.content_code) <> 64", "length(NEW.content_code) > 64", "i: short content code allowed", "i_code_short", False),
    (QS, " OR NEW.content_code GLOB '*[^0-9a-f]*'", "", "i: non-hex content code allowed", "i_code_nonhex or i_code_upper", False),
    (QS, 'NULL_FIELDS_OF_ITEM, " IS NULL OR (", ro_item', 'NULL_FIELDS_OF_ITEM, " IS NOT NULL OR (", ro_item', "j: approve of null fields allowed", "j_null_fields", False),
    (QS, 'NULL_FIELDS_OF_ITEM, " IS NULL OR (", ro_item, "))"', 'NULL_FIELDS_OF_ITEM, " IS NULL OR (0", "", "))"', "j: approve of reject-only item allowed", "j_flag", False),
    (WQ, 'conn.execute("BEGIN IMMEDIATE")', 'conn.execute("BEGIN")', "transaction: BEGIN instead of BEGIN IMMEDIATE", "test_a_busy_queue", False),
    (WQ, '        if conn.in_transaction:\n            conn.execute("ROLLBACK")\n', "        pass\n", "transaction: no rollback on error", "test_transaction_rolls_back", False),
    (WQ, '        yield conn\n        conn.execute("COMMIT")\n    except BaseException:', "        yield conn\n    except BaseException:", "transaction: COMMIT never issued", "test_transaction_rolls_back", False),
    (WQ, 'if "locked" in str(e) or "busy" in str(e):\n            raise Refused("db_busy"', 'if False:\n            raise Refused("db_busy"', "transaction: busy file not mapped", "db_busy", False),
    (WQ, "if dup is not None:", "if False:", "insert: duplicate not detected", "test_item_id_duplicate", False),
    (WQ, 'if conn.execute("SELECT 1 FROM items WHERE id = ?", (iid,)).fetchone() is not None:', "if False:", "insert: id collision not detected", "test_id_collision", False),
    (WQ, "    if tenant_id != s.tenant_id:", "    if False:", "insert: foreign tenant accepted", "tenant_that_is_not", False),
    (WQ, "    failing = validators.validate_record(fields, s.service.currencies)\n    if failing:", "    failing = []\n    if failing:", "set_result: record not validated", "hostile_record or turns_a_record", False),
    (WQ, "if strictjson.loads(text) != fields:", "if False:", "set_result: no strict round trip", "roundtrip_check", False),
    (WQ, "    if not callable(serve_lock_held) or serve_lock_held() is not True:", "    if False:", "recover: no serve-lock guard", "needs_the_serve_lock", False),
    (WQ, "UPDATE items SET state='NEEDS_PERSON', flags_json=?, version=version+1 WHERE state='RECEIVED'", "UPDATE items SET version=version WHERE state='NOPE' AND flags_json<>?", "recover: does nothing", "test_recover_received_after_a_real_crash", False),
    (WQ, ' or c.execute("SELECT 1 FROM exports WHERE item_uid = ?", (r["uid"],)).fetchone()', "", "purge: exports not checked", "test_purge_refuses_an_item_that_has_an_export_row", False),
    (WQ, 'PURGE_STATES = ("RECEIVED", "READY", "NEEDS_PERSON", "REJECTED")', 'PURGE_STATES = ("RECEIVED", "READY", "NEEDS_PERSON", "REJECTED", "APPROVED")', "purge: APPROVED allowed", "test_purge_refuses_approved", False),
    (WQ, '"INSERT INTO purges (item_id, item_uid, state, purged_by, at) VALUES (?, ?, ?, ?, ?)",', '"SELECT ?, ?, ?, ?, ?",', "purge: no audit row", "test_purge_writes_one_audit_row", False),
    (WQ, "not ACTOR_RE.fullmatch(who)", "False", "purge: by not validated", "purge_by_is_a_login", False),
    (WQ, '        if not conn.in_transaction:\n            raise ValueError("conn= needs', '        if False:\n            raise ValueError("conn= needs', "scope: caller without a transaction accepted", "need_a_transaction", False),
    (WQ, "    if get_export(conn, item.uid) is not None:", "    if False:", "record_export: second receipt for an item not checked", "second_receipt_by_code", False),
    (WQ, "    if export_by_row_id(conn, row_id) is not None:", "    if False:", "record_export: row id conflict not checked", "record_export_refusals", False),
    (WQ, '    if not conn.in_transaction:\n        raise ValueError("record_export', '    if False:\n        raise ValueError("record_export', "record_export: no transaction check", "need_a_transaction", False),
    (WQ, "WHERE uid=? AND version=? AND state='APPROVED'\", (item.uid, version)", "WHERE uid=? AND state='APPROVED'\", (item.uid,)", "record_export: no version compare-and-set", "record_export_refusals", False),
    (WQ, "        conn.execute(\"PRAGMA recursive_triggers=ON\")\n", "", "connect: recursive_triggers off", "test_recursive_triggers_pragma", False),
    (WQ, "        if schema != want_schema:", "        if False:", "connect: table definitions not verified", "test_connect_refuses_a_table", False),
    (WQ, "        if have_schema and have_schema.keys() != want_schema.keys():", "        if False:", "connect: dropped table rebuilt silently", "test_a_dropped_table", False),
    (WQ, "        if triggers != want_triggers:", "        if False:", "connect: triggers never recreated", "test_connect_restores", False),
    (WQ, "    if _have(conn) == (want_schema, want_triggers):\n        return\n", "    return\n", "connect: schema never verified", "test_connect_restores or test_connect_refuses", False),
    (WQ, '''name.replace('"', '""')''', "name", "connect: trigger name not quoted", "holds_a_quote", False),
    (WQ, "        if time.monotonic() > deadline:", "        if False:", "wal: no deadline", "deadline_checked", False),
    (WQ, '            if "locked" not in str(e) and "busy" not in str(e):', "            if True:", "wal: locked file not retried", "test_first_open_race or deadline_checked", True),
    (WQ, '            raise ConfigError("bad_config", "wal_unavailable: the queue file must be on a local filesystem")', "            pass", "wal: other mode not refused", "refused_at_once", False),
    (WQ, "            p.chmod(QUEUE_FILE_MODE)", "            pass", "files: not restricted", "test_queue_files_are_restricted", False),
    (WQ, "        os.close(os.open(path, os.O_CREAT | os.O_WRONLY, QUEUE_FILE_MODE))", "        pass", "files: not created before sqlite", "before_sqlite_writes", False),
    (WQ, "s.intake_home.mkdir(mode=QUEUE_DIR_MODE, parents=True", "s.intake_home.mkdir(parents=True", "files: folder not owner-only", "home_folder_is_made_owner_only", False),
    (WQ, "WHERE item_uid = ? ORDER BY seq DESC LIMIT 1", "WHERE item_uid = ? ORDER BY seq ASC LIMIT 1", "accessor: oldest decision as latest", "latest_decision_is_the_highest", False),
    (WQ, "FROM exports ORDER BY seq", "FROM exports ORDER BY seq DESC", "accessor: exports reversed", "accessors_latest_decision", False),
    (WQ, "AND uid NOT IN (SELECT item_uid FROM exports) ORDER BY created_at, uid", "ORDER BY created_at, uid", "accessor: exported items still listed", "already_has_a_receipt", False),
    (WQ, "ORDER BY created_at, uid\"\n    )\n\n\ndef exports", "ORDER BY created_at DESC, uid DESC\"\n    )\n\n\ndef exports", "accessor: unexported order reversed", "accessors_latest_decision", False),
    (WQ, "    except ValueError:\n        raise _stored(r) from None", "    except ValueError:\n        raise", "stored: bad JSON not mapped", "poisoned_row", False),
    (WQ, "        except Refused:\n            continue", "        except Refused:\n            raise", "stored: one bad row hides the rest", "poisoned_row", False),
    (WQ, "WHERE uid=? AND version=? AND state IN ('READY', 'NEEDS_PERSON')\",\n            (new_state, item.uid, version),", "WHERE uid=? AND state IN ('READY', 'NEEDS_PERSON')\",\n            (new_state, item.uid),", "decide: no version compare-and-set", "test_a_stale_version", False),
    (DC, "if content_code != cc.content_code(item):", "if False:", "decide: no content code check", "test_a_wrong_content_code", False),
    (DC, 'if item.state in ("APPROVED", "REJECTED", "EXPORTED"):', "if False:", "decide: no already_decided check", "test_a_second_decision", False),
    (DC, 'if item.state == "RECEIVED":', "if False:", "decide: RECEIVED decidable", "decide_on_a_received_item", False),
    (DC, "            if not valid_reason(s, reason):\n                raise Refused(\"invalid_reason\", \"a reject needs", "            if False:\n                raise Refused(\"invalid_reason\", \"a reject needs", "decide: reject without reason", "test_reject_needs_a_valid_reason", False),
    (DC, "if reason is not None and not valid_reason(s, reason):", "if False:", "decide: bad reason on approve ignored", "supplied_but_invalid_reason", False),
    (DC, "not workqueue.ACTOR_RE.fullmatch(approver)", "False", "decide: approver not checked", "bad_approver", False),
    (WQ, "[A-Za-z0-9][A-Za-z0-9._@-]{0,63}", "[A-Za-z0-9][A-Za-z0-9._@-]{0,127}", "login names: 128 characters allowed", "bad_approver", False),
    (DC, '    if blocker == "reject_only":\n', "    if False:\n", "approve_refusal: reject-only ignored", "every_reject_only_code", False),
    (DC, '    if blocker == "invalid_reason":\n', "    if False:\n", "approve_refusal: a flag that needs a reason is approved without one", "test_may_approve_rules or d12_needs", False),
    (DC, "flagtable.approval_blocker(item.flags, valid_reason(s, reason))", "None", "approve_refusal: approval_blocker not consulted", "every_reject_only_code", False),
    (DC, "    if item.fields is None or validators.validate_record(item.fields, s.service.currencies):", "    if False:", "approve_refusal: null fields allowed", "test_may_approve_rules", False),
    (DC, '        return Refused("not_approvable", "unknown flag")', "        blocker = None", "approve_refusal: unknown flag approvable", "test_may_approve_rules", False),
    (DC, '"So", "Zs"}', '"So", "Zs", "Mn"}', "reason: marks allowed", "test_reason_vectors", False),
    (DC, '"So", "Zs"}', '"So", "Zs", "Cf"}', "reason: format characters allowed", "test_reason_vectors", False),
    (DC, '"So", "Zs"}', '"So", "Zs", "Cc"}', "reason: control characters allowed", "test_reason_vectors", False),
    (DC, " or c in _BLANK_LOOKALIKES", "", "reason: blank lookalikes allowed", "test_reason_vectors", False),
    (DC, 'nfc = unicodedata.normalize("NFC", text)', "nfc = text", "reason: no NFC composition", "test_reason_vectors", False),
    (DC, "sum(1 for c in nfc if not c.isspace())", "len(nfc)", "reason: whitespace counts as visible", "test_reason_vectors or whitespace_does_not_count", False),
    (DC, "len(text) > s.review.reason_max_chars", "False", "reason: maximum length not applied", "test_reason_vectors", False),
    (DC, ">= s.review.reason_min_chars", ">= s.review.reason_min_chars - 1", "reason: minimum one less", "test_reason_vectors", False),
    (WQ, '    if r["text_sha256"] != text_hash(r["source_text"]):', "    if False:", "stored: text hash not verified on read", "does_not_match_its_stored_hash", False),
    (WQ, "text_hash(source_text), now_utc()),", "text_hash(''), now_utc()),", "insert: text hash not stored", "text_hash_is_stored", False),
    (QS, '"source_text", "text_sha256", "model_id"', '"source_text", "model_id"', "b: text_sha256 not frozen", f"{STMT} and b_text_sha256", False),
    (CC, '"flags": _flags(item),', '"flags": [],', "content code: flags ignored", "test_content_code_matches_fixture", False),
    (WQ, "WHERE uid=? AND state='RECEIVED'", "WHERE uid=?", "set_result: no state compare-and-set", "replayed_result", False),
    (WQ, 'if r is None or r["v"] != queue_schema.SCHEMA_VERSION:', "if False:", "connect: schema version not verified", "another_or_no_schema_version", False),
    (WQ, "        if new_file:", "        if True:", "connect: a missing version row is added to an existing file", "not_silently_added", False),
    (WQ, '        conn.execute("ROLLBACK TO apply_decision")\n', "", "apply_decision: no rollback to the savepoint", "swallows_the_refusal", False),
    (WQ, '    conn.execute("RELEASE apply_decision")\n    return Decision', "    return Decision", "apply_decision: savepoint not released", "savepoint_is_released", False),
    (DC, "if approver.casefold() in workqueue.RESERVED_ACTORS:", "if False:", "decide: reserved names allowed", "reserved_names", False),
    (DC, "if approver.casefold() in workqueue.RESERVED_ACTORS:", "if approver in workqueue.RESERVED_ACTORS:", "decide: reserved names are case-sensitive", "reserved_names", False),
    (CC, "        return sorted({str(c) for c in item.flags})", "        raise", "content code: an unknown stored flag makes the item undecidable", "unknown_stored_flag", False),
    (WQ, "COALESCE(SUM(cost_micro), 0)", "COALESCE(MAX(cost_micro), 0)", "sum_cost_micro: not a sum", "sum_cost_micro", False),
    (WQ, "        s.intake_home.chmod(QUEUE_DIR_MODE)", "        pass", "connect: an existing intake folder is not tightened", "intake_folder_with_loose_bits", False),
    (QS, "AND (NEW.reason IS NULL OR trim(NEW.reason) = '')", "AND NEW.reason IS NULL", "j2: empty or blank reason accepted", "j2_reason_empty or j2_reason_blank", False),
    (QS, "<> '[]' AND (NEW.reason", "<> '' AND (NEW.reason", "j2: an unflagged approve needs a reason", "j2_allows", False),
    (CC, '"tenant_id": item.tenant_id,', '"tenant_id": "x",', "content code: tenant ignored", "test_content_code_matches_fixture", False),
    (CC, '"source_sha256": item.source_sha256,', '"source_sha256": "0",', "content code: source hash ignored", "when_any_hashed_field_changes and source_sha256", False),
    (CC, 'lines = [_line(x) for x in f["lines"]]', 'lines = sorted(_line(x) for x in f["lines"])', "content code: line order not kept", "line_order", False),
    (CC, "invoice_key = rules.norm_invoice_no(folded_invoice, policy)", "invoice_key = None", "row_id: invoice number not normalised", "test_row_id_normalisation or row_id_vector", False),
    (CC, "folded_invoice = fold_text(invoice_no)", "folded_invoice = invoice_no", "row_id: invoice fold removed", "look_alike_invoice", False),
    (CC, "fold_text(supplier_name, casefold=True, collapse_ws=True)", "supplier_name.casefold()", "row_id: supplier fold removed", "look_alike_suppliers", False),
    (CC, 'if not isinstance(f, dict) or not isinstance(f.get("supplier_name"), str)', 'if not isinstance(f, dict) or False', "item_row_id: unusable record not handled", "never_raises_on_a_malformed", False),
]  # fmt: skip
QUEUE = [m for m in QUEUE if m[4] != "none"]
# UNOBSERVABLE through the public API, reported in a class of its own (like the WP3 group): (file, old, new, name, reason, the test that proves the other layer).
# The runner requires the mutant to SURVIVE the whole queue test set AND the proof test to pass; it is never counted as a kill.
QUEUE_UNOBSERVABLE: list[
    tuple
] = []  # none today: the set_result replay is observable (test_a_replayed_result_on_a_processed_item_is_refused)


def _pytest(tests: tuple[str, ...], k: str | None = None) -> tuple[str, list[str], str]:
    """Run pytest (no -x) on `tests` (optionally `-k k`); return (judge verdict, ids of the tests that failed, first FAILED line)."""
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "junit.xml"
        cmd = ["uv", "run", "--all-extras", "--group", "test", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={report}", *tests]
        if k:
            cmd += ["-k", k]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)  # noqa: S603
        try:
            stdout, _ = proc.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            return "CRASH", [], "TIMEOUT"
        junit = report.read_text(encoding="utf-8") if report.exists() else ""
        verdict = judge(proc.returncode, junit)
        pat = re.compile(r'<testcase classname="([^"]*)" name="([^"]*)"[^>]*>\s*<failure')
        failed = [f"{c.split('.')[-1]}::{html.unescape(n)}" for c, n in pat.findall(junit)]
        first = next((ln for ln in stdout.splitlines() if ln.startswith(("FAILED", "ERROR"))), "")
        return verdict, failed, first


def _queue_one(label: str, path: str, old: str, new: str, k: str, flaky: bool, out: list[str]) -> str:
    full = ROOT / path
    orig = full.read_bytes().decode("utf-8")
    if old == new:
        line = f"SKIP     [QUEUE] {label}: the mutant text equals the original (not a mutant)"
        print(line, flush=True)
        out.append(line)
        return "SKIP"
    if orig.count(old) != 1:
        line = f"SKIP     [QUEUE] {label}: pattern occurs {orig.count(old)} times in {path}"
        print(line, flush=True)
        out.append(line)
        return "SKIP"
    mutated = orig.replace(old, new, 1)
    assert mutated != orig, label  # the mutation really changes the file
    full.write_bytes(mutated.encode("utf-8"))
    try:
        verdicts = []
        for _ in range(3 if flaky else 1):  # a timing-dependent mutant must be killed every time
            verdict, failed, first = _pytest(QUEUE_TESTS, k)  # the expected killer first, alone
            elsewhere = ""
            if verdict == "SURVIVED":
                v2, failed2, first = _pytest(QUEUE_TESTS)  # then everything: a kill here is not the expected one
                verdict = "KILLED-ELSEWHERE" if v2 == "KILLED" else v2
                failed = failed2
                elsewhere = f" expected {k!r}"
            verdicts.append((verdict, failed, first, elsewhere))
        bad = [v for v in verdicts if v[0] != "KILLED"]
        verdict, failed, first, elsewhere = (bad or verdicts)[0]
        by = (failed[0] if failed else first)[:90]
        line = f"{verdict:<9}[QUEUE] {label}  by {by} ({len(failed)} failing){elsewhere}{' x3' if flaky else ''}"
    finally:
        full.write_bytes(orig.encode("utf-8"))
    print(line, flush=True)
    out.append(line)
    return verdict


def run_queue(only: str | None, out: list[str], exclude: str | None = None, skip_baseline: bool = False) -> int:
    """Baseline first: the queue tests must pass unmodified, an identity mutant must pass and a no-op mutant (a comment) must SURVIVE; then every mutant."""
    small = ("tests/test_triggers.py", "tests/test_content_code.py")
    if not skip_baseline:
        v, failed, first = _pytest(QUEUE_TESTS)
        out.append(f"BASELINE [QUEUE] unmodified queue tests: {'green' if v == 'SURVIVED' else 'NOT GREEN ' + first}")
        print(out[-1], flush=True)
        if v != "SURVIVED":
            return 1
        qs = ROOT / QS
        orig = qs.read_bytes().decode("utf-8")
        try:
            for label, text in (("identity mutant", orig), ("no-op mutant (a comment)", orig + "\n# no-op mutant\n")):
                qs.write_bytes(text.encode("utf-8"))
                v, failed, first = _pytest(small)
                ok = v == "SURVIVED"
                out.append(f"BASELINE [QUEUE] {label}: {'green (survived, as it must)' if ok else 'FAILED ' + first}")
                print(out[-1], flush=True)
                if not ok:
                    return 1
        finally:
            qs.write_bytes(orig.encode("utf-8"))
    counts: dict[str, int] = {}
    for label, path, old, new, k, flaky in ((m[3], m[0], m[1], m[2], m[4], m[5]) for m in QUEUE):
        if (only and only not in label) or (exclude and exclude in label):
            continue
        r = _queue_one(label, path, old, new, k, flaky, out)
        counts[r] = counts.get(r, 0) + 1
    for label, path, old, new, reason, proof in ((m[3], m[0], m[1], m[2], m[4], m[5]) for m in QUEUE_UNOBSERVABLE):
        if (only and only not in label) or (exclude and exclude in label):
            continue
        full = ROOT / path
        orig = full.read_bytes().decode("utf-8")
        if orig.count(old) != 1:
            counts["SKIP"] = counts.get("SKIP", 0) + 1
            continue
        full.write_bytes(orig.replace(old, new, 1).encode("utf-8"))
        try:
            v_all, _, first = _pytest(QUEUE_TESTS)
            v_proof, _, first_p = _pytest(QUEUE_TESTS, proof)
        finally:
            full.write_bytes(orig.encode("utf-8"))
        ok = v_all == "SURVIVED" and v_proof == "SURVIVED"
        line = f"{'UNOBSERVABLE' if ok else 'UNOBSERVABLE-BROKEN':<9}[QUEUE] {label}: {reason}; mutant survives the queue tests {v_all == 'SURVIVED'}, proof test {proof} green {v_proof == 'SURVIVED'}"
        print(line, flush=True)
        out.append(line)
        counts["UNOBSERVABLE" if ok else "UNOBSERVABLE-BROKEN"] = counts.get("UNOBSERVABLE" if ok else "UNOBSERVABLE-BROKEN", 0) + 1
    out.append("QUEUE: " + ", ".join(f"{k.lower()} {n}" for k, n in sorted(counts.items())) + f" (mutants run {sum(counts.values())}).")
    print(out[-1])
    return 0 if set(counts) <= {"KILLED", "UNOBSERVABLE"} else 1


def main() -> int:
    os.chdir(ROOT)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    out: list[str] = []
    target = ROOT / "tools" / "mutate_src_output.txt"
    if "--group" in sys.argv and sys.argv[sys.argv.index("--group") + 1] == "WP5":  # only the WP5 mutants, only the WP5 tests
        if "--check" in sys.argv:  # only verify that every pattern still matches exactly once
            stale = [m[3] for m in WP5 if (ROOT / m[0]).read_bytes().decode("utf-8").count(m[1]) != 1]
            print(chr(10).join(f"STALE {n}" for n in stale) or f"all {len(WP5)} WP5 patterns match once")
            return 1 if stale else 0
        k, sv, sk, cr = run("WP5", WP5, only, out, tuple(WP5_TESTS))
        out.append(f"WP5: killed {k}, survived {sv}, skipped {sk}, crashed {cr}.")
        print(out[-1])
        if not only:
            (ROOT / "tools" / "mutate_wp5_output.txt").write_text(chr(10).join(out) + chr(10), encoding="utf-8")
        return 1 if (sv or sk or cr) else 0
    if "--group" in sys.argv and sys.argv[sys.argv.index("--group") + 1] == "WP6":  # only the WP6 mutants, only the WP6 tests
        if "--check" in sys.argv:  # only verify that every pattern still matches exactly once
            stale = [m[3] for m in WP6 if (ROOT / m[0]).read_bytes().decode("utf-8").count(m[1]) != 1]
            print(chr(10).join(f"STALE {n}" for n in stale) or f"all {len(WP6)} WP6 patterns match once")
            return 1 if stale else 0
        wp6 = [
            m for m in WP6 if not (sys.platform == "win32" and "[posix]" in m[3]) and not (sys.platform != "win32" and "[win]" in m[3])
        ]  # POSIX-only branches are killed in the Linux run
        k, sv, sk, cr = run("WP6", wp6, only, out, tuple(WP6_TESTS))
        out.append(f"WP6: killed {k}, survived {sv}, skipped {sk}, crashed {cr}.")
        print(out[-1])  # the raw lines go into the evidence file of the run; no output file is committed for this group
        return 1 if (sv or sk or cr) else 0
    if "--group" in sys.argv and sys.argv[sys.argv.index("--group") + 1] == "queue":
        if "--check" in sys.argv:  # only verify that every pattern still matches exactly once
            stale = [m[3] for m in (*QUEUE, *QUEUE_UNOBSERVABLE) if (ROOT / m[0]).read_bytes().decode("utf-8").count(m[1]) != 1]
            print(chr(10).join(f"STALE {n}" for n in stale) or f"all {len(QUEUE)} queue patterns match once")
            return 1 if stale else 0
        exclude = sys.argv[sys.argv.index("--exclude") + 1] if "--exclude" in sys.argv else None
        rc = run_queue(only, out, exclude, "--skip-baseline" in sys.argv)
        if not only and not exclude:  # replace only the [QUEUE] lines of the committed output
            keep = [
                ln
                for ln in (target.read_text(encoding="utf-8").splitlines() if target.exists() else [])
                if "[QUEUE]" not in ln and not ln.startswith("QUEUE:")
            ]
            target.write_text("\n".join([*keep, *out]) + "\n", encoding="utf-8")
        return rc
    k1, s1, x1, c1 = run("SRC", SRC, only, out)
    k2, s2, x2, c2 = run("ORACLE", ORACLE, only, out)
    out.append(
        f"SRC: killed {k1}, survived {s1}, skipped {x1}, crashed {c1}. ORACLE/generator: killed {k2}, survived {s2}, skipped {x2}, crashed {c2}."
    )
    print(out[-1])
    if not only:
        keep = [
            ln
            for ln in (target.read_text(encoding="utf-8").splitlines() if target.exists() else [])
            if "[QUEUE]" in ln or ln.startswith("QUEUE:")
        ]
        target.write_text("\n".join([*out, *keep]) + "\n", encoding="utf-8")
    return 1 if (s1 or s2 or x1 or x2 or c1 or c2) else 0


if __name__ == "__main__":
    raise SystemExit(main())
