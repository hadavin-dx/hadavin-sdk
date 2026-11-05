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
WP6_TESTS = [
    "tests/test_wp6_kickoff.py",
    "tests/test_routes_have_roles.py",
    "tests/test_scan.py",  # before 6d's files: the inbox mutants are killed by their own tests
    "tests/test_access.py",
    "tests/test_service_routes.py",
    "tests/test_review_http.py",
    "tests/test_serve.py",
    "tests/test_access_more.py",
    "tests/test_service_more.py",
    "tests/test_secret_store.py",
]
_HALT_HEAD = '    p = ledger_path(s)\n    if not _exists(p):\n        return None\n    try:\n        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)\n        try:\n            '
WP6 = [
    # 6k: killed by halt_state_readonly_states
    (
        "src/intake/budget.py",
        'return (False, "") if v == "0" else None',
        'return (False, "")',
        "absent halted key read as not halted (test_halt_state_readonly_states)",
    ),
    (
        "src/intake/budget.py",
        _HALT_HEAD + 'v = _meta(c, "halted")',
        _HALT_HEAD.replace("return None", 'return False, ""') + 'v = _meta(c, "halted")',
        "missing ledger read as not halted (test_halt_state_readonly_states)",
    ),
    (
        "src/intake/budget.py",
        '    except sqlite3.Error:\n        return None\n    if v == "1":',
        '    except sqlite3.Error:\n        return False, ""\n    if v == "1":',
        "database error read as not halted (test_halt_state_readonly_states)",
    ),
    # 6k: killed by total_settled_readonly_matches_ledger, page_reads_never_block_settle
    (
        "src/intake/budget.py",
        _HALT_HEAD + "return _settled_total(c)",
        _HALT_HEAD.replace("return None", "return 0") + "return _settled_total(c)",
        "missing ledger read as zero spend (test_total_settled_readonly_matches_ledger)",
    ),
    (
        "src/intake/budget.py",
        _HALT_HEAD + "return _settled_total(c)",
        _HALT_HEAD.replace("?mode=ro", "?mode=rw") + 'c.execute("BEGIN IMMEDIATE")\n            return _settled_total(c)',
        "settled total takes a write lock (test_total_settled_readonly_matches_ledger)",
    ),
    # 6k: killed by connect_readonly_cannot_write, connect_readonly_refuses_non_wal
    (
        "src/intake/workqueue.py",
        '+ "?mode=ro", uri=True, timeout=BUSY_TIMEOUT_S',
        '+ "?mode=rwc", uri=True, timeout=BUSY_TIMEOUT_S',
        "read-only queue connection can write (test_connect_readonly_cannot_write)",
    ),
    (
        "src/intake/workqueue.py",
        'PRAGMA journal_mode").fetchone()[0]).lower() != "wal"',
        'PRAGMA journal_mode").fetchone()[0]).lower() == "never"',
        "read-only queue connection accepts a non-WAL file (test_connect_readonly_refuses_non_wal)",
    ),
    (
        "src/intake/workqueue.py",
        "        _check_version(conn)\n    except BaseException:\n        conn.close()\n        raise\n    return conn\n\n\ndef _precreate",
        "    except BaseException:\n        conn.close()\n        raise\n    return conn\n\n\ndef _precreate",
        "read-only queue connection skips the version check (test_connect_readonly_cannot_write)",
    ),
    # 6k: killed by known_sources_lists_every_hash
    (
        "src/intake/workqueue.py",
        '"SELECT source_sha256 FROM items"',
        "\"SELECT source_sha256 FROM items WHERE state != 'REJECTED'\"",
        "known sources skip rejected items (test_readers_use_given_conn)",
    ),
    # 6k: killed by readers_use_given_conn, preview_rows_on_readonly_conn (a reader opens its own connection although it was given one)
    (
        "src/intake/workqueue.py",
        "    if conn is not None:\n        return get_in(conn, item_id_)",
        "    if False:\n        return get_in(conn, item_id_)",
        "get ignores the connection it is given (test_readers_use_given_conn)",
    ),
    (
        "src/intake/workqueue.py",
        '    if state is None:\n        return _rows(conn, "SELECT * FROM items ORDER BY created_at, uid")',
        '    conn = connect(s)\n    if state is None:\n        return _rows(conn, "SELECT * FROM items ORDER BY created_at, uid")',
        "list_items ignores the connection it is given (test_readers_use_given_conn)",
    ),
    (
        "src/intake/workqueue.py",
        "    if conn is None:\n        with opened(s) as own:\n            return unreadable_ids(",
        "    if True:\n        with opened(s) as own:\n            return unreadable_ids(",
        "unreadable_ids ignores the connection it is given (test_readers_use_given_conn)",
    ),
    (
        "src/intake/workqueue.py",
        "    if conn is None:\n        with opened(s) as own:\n            return known_sources(",
        "    if True:\n        with opened(s) as own:\n            return known_sources(",
        "known_sources ignores the connection it is given (test_readers_use_given_conn)",
    ),
    (
        "src/intake/exporter.py",
        "    out: list[PreviewRow] = []\n    for item in workqueue.approved_unexported(conn):",
        "    out: list[PreviewRow] = []\n    conn = workqueue.connect(s)\n    for item in workqueue.approved_unexported(conn):",
        "preview_rows ignores the connection it is given (test_preview_rows_on_readonly_conn)",
    ),
    # 6k: killed by read_log_level, blank_lookalikes_public_alias, new_codes_listed
    ("src/intake/settings.py", "    if v not in LOG_LEVELS:", "    if False:", "log level not validated (test_read_log_level)"),
    (
        "src/intake/settings.py",
        'env.get("INTAKE_LOG", "") or "normal"',
        'env.get("INTAKE_LOG", "") or "verbose"',
        "log level defaults to verbose (test_read_log_level)",
    ),
    (
        "src/intake/decisions.py",
        "BLANK_LOOKALIKES = _BLANK_LOOKALIKES",
        "BLANK_LOOKALIKES = frozenset(sorted(_BLANK_LOOKALIKES))",
        "blank lookalikes alias is a copy (test_blank_lookalikes_public_alias)",
    ),
    ("src/intake/codes.py", '        "too_many_attempts",\n', "", "a WP6 code missing from the closed set (test_new_codes_listed)"),
    # 6k: killed by routes_import_validation, match_is_exact_and_per_listener
    (
        "src/intake/routes.py",
        'if r.app == "dash" and r.writes:',
        "if False and r.writes:",
        "a dashboard row may write (test_routes_import_validation)",
    ),
    ("src/intake/routes.py", 'and "csrf" not in r.fields:', "and False:", "a session POST may lack csrf (test_routes_import_validation)"),
    (
        "src/intake/routes.py",
        "        if r.app != app:\n            continue",
        "        if False:\n            continue",
        "route served on the wrong listener (test_match_is_exact_and_per_listener)",
    ),
    # 6d (service, access): each name ends with the test that must kill it
    (
        "src/intake/access.py",
        "    return secrets.compare_digest(_digest(given), _digest(expected))",
        "    return True",
        "equal_secret returns True (equal_secret_behaviour)",
    ),
    (
        "src/intake/access.py",
        "or not given or not expected:\n        return False",
        ":\n        return False",
        "empty secret not refused before hashing (equal_secret_behaviour)",
    ),
    (
        "src/intake/access.py",
        "        return secret_store.get(login.secret_name, local=s.local)  # re-read",
        '        return globals().setdefault("_c", {}).setdefault(login.name, secret_store.get(login.secret_name, local=s.local))  # re-read',
        "passphrase cached (passphrase_match_and_reread)",
    ),
    (
        "src/intake/access.py",
        "or login.name.casefold() in workqueue.RESERVED_ACTORS or login.role not in ROLES:",
        "or login.role not in ROLES:",
        "reserved-name check removed in SessionStore.create (create_refuses_reserved_names)",
    ),
    (
        "src/intake/access.py",
        "                self._by_sid.pop(replacing, None)  # rotation",
        "                pass  # rotation",
        "old session not ended at sign-in (session_rotation_and_client_sid_never_adopted)",
    ),
    (
        "src/intake/access.py",
        "if age_over(sess.last_touch, now, LIMIT_SESSION_IDLE_S) or age_over(sess.created, now, LIMIT_SESSION_ABS_S):",
        "if age_over(sess.created, now, LIMIT_SESSION_ABS_S):",
        "idle check removed (session_idle_expiry)",
    ),
    (
        "src/intake/access.py",
        "if age_over(sess.last_touch, now, LIMIT_SESSION_IDLE_S) or age_over(sess.created, now, LIMIT_SESSION_ABS_S):",
        "if age_over(sess.last_touch, now, LIMIT_SESSION_IDLE_S):",
        "absolute check removed (session_absolute_expiry)",
    ),
    (
        "src/intake/access.py",
        "            if touch:\n                sess = replace(sess, last_touch=now)",
        "            if True:\n                sess = replace(sess, last_touch=now)",
        "poll refreshes idle (poll_does_not_refresh_idle)",
    ),
    (
        "src/intake/access.py",
        "return now.mono - start.mono > limit_s or now.wall - start.wall > limit_s or now.wall < start.wall",
        "return now.mono - start.mono > limit_s or now.wall < start.wall",
        "wall-clock age check removed (session_expires_across_sleep)",
    ),
    (
        "src/intake/access.py",
        "return now.mono - start.mono > limit_s or now.wall - start.wall > limit_s or now.wall < start.wall",
        "return now.mono - start.mono > limit_s or now.wall - start.wall > limit_s",
        "backwards wall jump accepted (wall_clock_backwards_expires)",
    ),
    (
        "src/intake/access.py",
        "            while len(self._by_id) >= LIMIT_PRE_SESSIONS:\n                del self._by_id[next(iter(self._by_id))]\n",
        "",
        "pre-session map uncapped (pre_session_map_capped_and_expires)",
    ),
    (
        "src/intake/access.py",
        "            entry = self._by_id.pop(pre_id, None)",
        "            entry = self._by_id.get(pre_id)",
        "pre-session not one use (pre_session_issue_always_new_and_one_use)",
    ),
    (
        "src/intake/access.py",
        '    return f"{name}={value}" + _attrs(max_age)',
        '    return f"{name}={value}" + _attrs(max_age).replace("; Secure", "")',
        "cookie Secure flag dropped (cookie_flags)",
    ),
    (
        "src/intake/access.py",
        'return "; Secure; HttpOnly; SameSite=Strict; Path=/"',
        'return "; Secure; SameSite=Strict; Path=/"',
        "cookie HttpOnly flag dropped (cookie_flags)",
    ),
    (
        "src/intake/access.py",
        '        and sec_fetch_site[0] == "same-origin"',
        "        and True",
        "Sec-Fetch-Site not checked (origin_rules)",
    ),
    (
        "src/intake/access.py",
        '        and origin_values[0] == f"http://{work_host}:{port}"',
        '        and origin_values[0] in (f"http://{work_host}:{port}", "null")',
        "Origin null accepted (origin_rules)",
    ),
    (
        "src/intake/access.py",
        '    return app == "token" and v.lower() == f"{_HOST_DOCKER}:{port}"',
        '    return v.lower() == f"{_HOST_DOCKER}:{port}"',
        "host.docker.internal accepted on work (host_per_listener_unit)",
    ),
    (
        "src/intake/service.py",
        '            if route.family == "session" and not access.csrf_ok(session, form.get("csrf")):\n                raise _Fail("csrf_failed")',
        '            if False:\n                raise _Fail("csrf_failed")',
        "CSRF skipped (csrf_required)",
    ),
    (
        "src/intake/service.py",
        '        if route.family == "session" and not access.allowed(route, session):\n            raise _Fail("role_denied")',
        '        if False:\n            raise _Fail("role_denied")',
        "role check skipped (viewer_refused_every_post_except_logout)",
    ),
    (
        "src/intake/service.py",
        '            if "x-hadavin-token" in by:\n                raise _Fail("token_not_allowed")',
        '            if False:\n                raise _Fail("token_not_allowed")',
        "token header allowed on work (session_route_rejects_token)",
    ),
    (
        "src/intake/service.py",
        'if method == "POST" and app == "work":\n            if not access.origin_ok(',
        "if False:\n            if not access.origin_ok(",
        "origin check skipped (bad_origin_refused)",
    ),
    (
        "src/intake/service.py",
        '("Referrer-Policy", "no-referrer" if token_app else "same-origin")',
        '("Referrer-Policy", "no-referrer")',
        "Referrer-Policy no-referrer on work HTML (referrer_policy_per_response)",
    ),
    (
        "src/intake/service.py",
        'any(c in part for c in ("\\r", "\\n", "\\x00"))',
        "False",
        "CR, LF and NUL allowed in a header (header_crlf)",
    ),
    (
        "src/intake/service.py",
        'strict_parsing=True,\n                errors="strict",',
        'strict_parsing=False,\n                errors="strict",',
        "strict_parsing dropped (form_strict_parsing_and_fields)",
    ),
    (
        "src/intake/service.py",
        "        self._drain()\n",
        "",
        "early errors and 413 sent without draining (early_errors_and_413_drain_the_body)",
    ),
    (
        "src/intake/service.py",
        '            if not cl and app == "work":',
        "            if not cl:",
        "token POST without Content-Length answered 411 (token_post_without_length_is_empty)",
    ),
    (
        "src/intake/service.py",
        '    if s.service.name_regex != "^" + routes.STEM_RE + "$":',
        "    if False:",
        "name_regex check at start removed (serve_refuses_changed_name_regex)",
    ),
    (
        "src/intake/service.py",
        "                    e[0].shutdown(socket.SHUT_RDWR)",
        "                    e[0].close()",
        "watchdog closes the socket itself (watchdog_shutdown_only)",
    ),
    (
        "src/intake/service.py",
        "        secs = (lim.scan_s if lim.scan_s is not None else lim.handle_s) if scan else lim.handle_s",
        "        secs = lim.handle_s",
        "scan bound removed (scan_gets_scan_bound_not_handle_bound)",
    ),
    (
        "src/intake/service.py",
        '        if srv.fatal.is_set():\n            raise _Fail("settle_failed")',
        '        if False:\n            raise _Fail("settle_failed")',
        "fatal flag unchecked (settle_failed_503_then_stop)",
    ),
    (
        "src/intake/service.py",
        'req.session.login_name, f["reason"]',
        'f.get("approver", req.session.login_name), f["reason"]',
        "approver taken from the form (only_service_decides_ast)",
    ),
    (
        "src/intake/service.py",
        '        ok = access.check_step_up(req.settings, req.session, req.form["passphrase"])',
        "        ok = True",
        "step-up skipped (export_step_up)",
    ),
    (
        "src/intake/service.py",
        '    if sf != ["navigate", "document"] or req.headers.get("sec-fetch-site") not in ("none", "same-origin"):\n',
        "    if False:\n",
        "GET /login issues a pre-session for a no-cors fetch (login_get_needs_navigation)",
    ),
    (
        "src/intake/service.py",
        '    if not srv.pre.redeem(access.cookie_value(req.headers.get("cookie"), access.COOKIE_PRE), form["csrf"]):',
        "    if False:",
        "login CSRF skipped (login_csrf_required)",
    ),
    (
        "src/intake/service.py",
        "    pre_id, token = req.server.pre.issue()\n    text",
        "    pre_id, token = ('A' * 43, 'B' * 43)\n    text",
        "pre-session not reissued on failure (login_retry_after_failure_works)",
    ),
    (
        "src/intake/service.py",
        '    sess = srv.sessions.create(login, replacing=access.cookie_value(req.headers.get("cookie"), access.COOKIE_SESSION))',
        "    sess = srv.sessions.create(login)",
        "old session not ended at sign-in over HTTP (session_rotation_over_http)",
    ),
    (
        "src/intake/service.py",
        "    req.server.sessions.end_all(req.session.login_name)",
        "    pass",
        "logout does not end sessions (wrong_listener_cookie_and_logout_then_old_cookie_redirects)",
    ),
    (
        "src/intake/service.py",
        'or req.headers.get("sec-fetch-site") not in ("none", "same-origin"):',
        ":",
        "login page: Sec-Fetch-Site not required (test_login_get_needs_navigation)",
    ),
    (
        "src/intake/secret_store.py",
        "        if values[0] in _read(secrets_path(local), frozenset({other_name})).get(other_name, []):",
        "        if False:",
        "webhook secret equal to the passphrase accepted (test_webhook_secret_and_passphrase_must_differ)",
    ),
    (
        "src/intake/service.py",
        'if not access.host_ok(app, by.get("host", []), srv.port, srv.hosts):',
        "if False:",
        "Host not checked (host_per_listener)",
    ),
    (
        "src/intake/service.py",
        "        if len(cl) > 1 or (cl and not _CL_RE.fullmatch(cl[0])):",
        "        if False:",
        "duplicate or malformed Content-Length accepted (content_length_strict)",
    ),
    (
        "src/intake/service.py",
        '        if "transfer-encoding" in by:',
        "        if False:",
        "Transfer-Encoding accepted (content_length_strict)",
    ),
    (
        "src/intake/service.py",
        '            if n > (LIMIT_BODY_WORK if app == "work" else LIMIT_BODY_TOKEN):',
        '            if n > (LIMIT_BODY_WORK if app == "work" else LIMIT_BODY_TOKEN) + 1:',
        "body cap off by one (content_length_strict)",
    ),
    ("src/intake/service.py", "        self.watch_start(request, self.limits.read_s)\n", "", "watchdog entry removed (request_deadline)"),
    (
        "src/intake/service.py",
        "        if not self.gate.acquire(blocking=False):",
        "        if False:",
        "connection cap removed (connection_cap_per_listener)",
    ),
    (
        "src/intake/service.py",
        '        if hit == "method":',
        "        if False:",
        "wrong method on a known path answers 404 not 405 (methods)",
    ),
    # 6b: the scan and the bounded reader (brief 8, 15.7). "[posix]" mutants change a POSIX-only branch: the Windows run skips them, the Linux run kills them
    (
        "src/intake/inbox.py",
        "except OSError:  # permission, sharing violation",
        "except ZeroDivisionError:  # permission, sharing violation",
        "per-file OSError catch removed (one locked file blocks the scan) (test_unreadable_file_blocks_nothing)",
    ),
    (
        "src/intake/inbox.py",
        "path = Path(name) if dir_fd is not None else inbox / name",
        "path = inbox / name",
        "dir_fd dropped, path opened by full name [posix] (test_inbox_dir_swap_refused)",
    ),
    (
        "src/intake/inbox.py",
        "| O_NONBLOCK, dir_fd=dir_fd)",
        ", dir_fd=dir_fd)",
        "O_NONBLOCK removed [posix] (test_fifo_swap_does_not_block)",
    ),
    (
        "src/intake/inbox.py",
        "os.O_RDONLY | O_NOFOLLOW |",
        "os.O_RDONLY |",
        "O_NOFOLLOW removed (symlink swap read) [posix] (test_symlink_swap_refused)",
    ),
    (
        "src/intake/inbox.py",
        "if st.st_nlink != 1 or not _same_file(st, st0):",
        "if st.st_nlink != 1:",
        "fstat identity check removed (test_inode_swap_refused)",
    ),
    (
        "src/intake/inbox.py",
        "if len(items) >= s.service.scan_max_files:",
        "if len(items) + duplicates >= s.service.scan_max_files:",
        "duplicates take a slot (test_three_new_files_take_two_scans)",
    ),
    (
        "src/intake/inbox.py",
        'if parsed.flag is None and reader.gate_decision(parsed, cfg.load_hash_list(listed_path)) == "not_on_list":',
        "if False:",
        "gate not re-checked before insert (test_gate_rechecked_before_insert)",
    ),
    (
        "src/intake/inbox.py",
        "< s.service.scan_min_age_s:",
        ">= s.service.scan_min_age_s:",
        "min-age flipped (test_three_new_files_take_two_scans)",
    ),
    (
        "src/intake/inbox.py",
        "if stat.S_ISDIR(st.st_mode) and not is_link:",
        "if False:",
        "subfolders examined instead of ignored (test_subfolder_ignored)",
    ),
    (
        "src/intake/inbox.py",
        "finally:" + chr(10) + "            _SCAN_LOCK.release()",
        "finally:" + chr(10) + "            pass",
        "scan lock not released (test_three_new_files_take_two_scans)",
    ),
    (
        "src/intake/inbox.py",
        "halt = budget.halt_state_readonly(s)  #",
        'halt = budget.halt_state_readonly(s) or (False, "")  #',
        "halt unreadable treated as not halted (test_spend_unreadable_refuses_scan)",
    ),
    ("src/intake/inbox.py", "if halt[0]:", "if False:", "halted ledger scanned anyway (test_halted_refused)"),
    (
        "src/intake/inbox.py",
        "if _change_key(st) != _change_key(st0):",
        "if False:",
        "changed-during-read check removed (test_file_changed_during_read_refused)",
    ),
    (
        "src/intake/inbox.py",
        "if st.st_nlink != 1 or not _same_file(st, st0):",
        "if not _same_file(st, st0):",
        "hard link check removed (test_read_plain_file_refuses_a_hard_link)",
    ),
    # Killed only because the refusal CODE changes (a link then falls to not_a_file instead of outside_inbox): the link is still never read, because
    # the S_ISREG check refuses it next. The O_NOFOLLOW mutant above is the one that proves the open itself does not follow a swapped-in link.
    (
        "src/intake/inbox.py",
        "if stat.S_ISLNK(st0.st_mode) or sys.platform",
        "if sys.platform",
        "symlink refusal removed from read_plain_file [posix] (test_read_plain_file_refuses_a_symlink)",
    ),
    (
        "src/intake/inbox.py",
        'if sys.platform == "win32" and st0.st_ino == 0:',
        "if False:",
        "volume without file id accepted [win] (test_windows_file_id_checked)",
    ),
    ("src/intake/inbox.py", "if len(refused) < MAX_REFUSED:", "if True:", "refused list uncapped (test_scan_memory_and_reply_are_bounded)"),
    (
        "src/intake/inbox.py",
        "except FileNotFoundError:  # vanished",
        "except ZeroDivisionError:  # vanished",
        "a vanished file is refused, not skipped (test_vanished_file_skipped)",
    ),
    (
        "src/intake/inbox.py",
        "chunk = read(min(_CHUNK, cap + 1 - len(out)))",
        "chunk = read(min(_CHUNK, cap - len(out)))",
        "read cap off by one: a file one byte over is cut, not refused (test_growing_file_bounded)",
    ),
    (
        "src/intake/inbox.py",
        "if sha in known or sha in seen:",
        "if sha in seen:",
        "known duplicates not skipped before the gate (test_known_duplicate_is_counted_before_the_gate)",
    ),
    (
        "src/intake/inbox.py",
        "examined += not counted  # a refused",
        "pass  # a refused",
        "a refused entry whose lstat failed is not counted as examined (test_an_entry_whose_lstat_fails_is_refused_and_counted)",
    ),
    (
        "src/intake/inbox.py",
        "            raise missing from None" + chr(10) + "        try:" + chr(10) + "            root = inbox.resolve()",
        "            raise" + chr(10) + "        try:" + chr(10) + "            root = inbox.resolve()",
        "a missing inbox leaks a raw OSError [posix] (test_missing_inbox_is_a_config_error)",
    ),
    (
        "src/intake/inbox.py",
        'missing = InboxUnavailable("the inbox folder',
        'missing = ConfigError("bad_config", "the inbox folder',
        "an unavailable inbox is a plain ConfigError (test_missing_inbox_is_a_config_error)",
    ),
    (
        "src/intake/inbox.py",
        'raise InboxUnavailable("this volume has no file ids")',
        'raise ConfigError("bad_config", "this volume has no file ids")',
        "a volume without file ids is a plain ConfigError [win] (test_windows_file_id_checked)",
    ),
    (
        "src/intake/inbox.py",
        "key = (st.st_size, st.st_mtime_ns)",
        "key = (st.st_size,)",
        "modification-time term dropped from the change check [win] (test_same_size_rewrite_with_a_new_mtime_refused)",
    ),
    # on POSIX the change time also moves on a rewrite, so the mtime mutant above is equivalent there: it is run on Windows only
    (
        "src/intake/inbox.py",
        "key += (st.st_ctime_ns,)",
        "key += ()",
        "change-time term dropped from the change check [posix] (test_rewrite_that_restores_the_mtime_refused_by_ctime)",
    ),
    (
        "src/intake/inbox.py",
        "if not _same_file(after, st) or _change_key(after) != _change_key(st):",
        "if False:",
        "scan does not compare its filter lstat after the read (test_scan_refuses_a_file_replaced_after_the_filter)",
    ),
    (
        "src/intake/inbox.py",
        "            except OSError:" + chr(10) + "                raise missing from None",
        "            except OSError:" + chr(10) + "                raise",
        "an unreadable inbox listing leaks a raw OSError (test_unreadable_inbox_listing_is_a_config_error)",
    ),
    (
        "src/intake/inbox.py",
        "            raise missing" + chr(10) + "        try:" + chr(10) + "            dir_fd =",
        "            pass" + chr(10) + "        try:" + chr(10) + "            dir_fd =",
        "a junctioned inbox is scanned [win] (test_junctioned_inbox_is_a_config_error)",
    ),
    (
        "src/intake/inbox.py",
        " + [(n, None, h) for n, h in extras]",
        "",
        "files that wait never fill a slot freed by a refusal (test_three_new_files_take_two_scans)",
    ),
    (
        "src/intake/cli.py",
        "data = inbox.read_plain_file(path, s.service.max_file_bytes)",
        "data = path.read_bytes()",
        "extract reads with its own unbounded reader (test_extract_uses_read_plain_file)",
    ),
    # 6d second pass (reviews A and B of a06e7c8)
    (
        "src/intake/service.py",
        "            self.server.fail_fatal()\n        return status_and_code(e)[1]",
        "            pass\n        return status_and_code(e)[1]",
        "[r2] fail_fatal removed in _code_of (settle_failed_from_any_handler_stops_the_service)",
    ),
    (
        "src/intake/service.py",
        '            srv.fail_fatal()\n            return _json_reply(503, {"error": "settle_failed"})',
        '            pass\n            return _json_reply(503, {"error": "settle_failed"})',
        "[r2] fail_fatal removed in the scan route (settle_failed_503_then_stop)",
    ),
    (
        "src/intake/service.py",
        "        threading.Thread(target=self.shared.stop.set, daemon=True).start()",
        "        pass",
        "[r2] fatal does not set the stop event (settle_failed_503_then_stop)",
    ),
    (
        "src/intake/service.py",
        "    return 3 if run.shared.fatal.is_set() else 0",
        "    return 0",
        "[r2] serve returns 0 after a fatal stop (settle_failed_503_then_exit_3)",
    ),
    (
        "src/intake/service.py",
        "            guessed_wrong = True\n            return page(401,",
        "            return page(401,",
        "[r2] export step-up failure not counted in the throttle (export_step_up_throttled)",
    ),
    (
        "src/intake/service.py",
        '            if not cl and app == "work":\n                raise _Fail("length_required")',
        '            if False:\n                raise _Fail("length_required")',
        "[r2] work POST without a length not refused with 411 (token_post_without_length_is_empty)",
    ),
    (
        "src/intake/service.py",
        "        left = min(self._declared, LIMIT_DRAIN)",
        "        left = self._declared",
        "[r2] drain cap removed (drain_reads_the_body_up_to_the_cap)",
    ),
    (
        "src/intake/service.py",
        'if not _VERSION_RE.fullmatch(f["version"]) or not _CONTENT_CODE_RE.fullmatch(f["content_code"]):',
        'if not _CONTENT_CODE_RE.fullmatch(f["content_code"]):',
        "[r2] version shape unchecked (decide_version_unicode_digits)",
    ),
    (
        "src/intake/service.py",
        'if not _VERSION_RE.fullmatch(f["version"]) or not _CONTENT_CODE_RE.fullmatch(f["content_code"]):',
        'if not _VERSION_RE.fullmatch(f["version"]):',
        "[r2] content code shape unchecked (decide_bad_content_code_shape)",
    ),
    (
        "src/intake/service.py",
        "touch=False)  # a refused request is not activity",
        "touch=True)  # a refused request is not activity",
        "[r2] session touched before the checks (a_refused_request_is_not_activity)",
    ),
    (
        "src/intake/service.py",
        "            self._respond_error(_Fail(self._code_of(e)), self._session_for_error())",
        "            self._respond_error(_Fail(self._code_of(e)), None)",
        "[r2] outer handler error page without the session (error_pages_of_a_signed_in_person_get_their_session)",
    ),
    (
        "src/intake/service.py",
        " or any(len(by.get(h, [])) > 1 for h in _SINGLE_VALUED):",
        ":",
        "[r2] repeated security headers read as the first value (repeated_security_headers_are_refused)",
    ),
    (
        "src/intake/service.py",
        '_FORM_CT_RE = re.compile(r"application/x-www-form-urlencoded([ \\t]*;[ \\t]*charset=utf-8)?"',
        '_FORM_CT_RE = re.compile(r"application/x-www-form-urlencoded(\\s*;\\s*charset=utf-8)?"',
        "[r2] form type accepts Unicode spaces (form_content_type_refuses_unicode_spaces)",
    ),
    (
        "src/intake/service.py",
        '        data = b""  # a reply to HEAD',
        "        pass  # a reply to HEAD",
        "[r2] HEAD gets a body (head_gets_the_headers_and_no_body)",
    ),
    (
        "src/intake/service.py",
        "            sv.wait_idle(max(0.0, end - time.monotonic()))",
        "            pass",
        "[r2] stop does not wait for requests in progress (stop_waits_for_a_request_in_progress_before_the_lock_goes)",
    ),
    (
        "src/intake/service.py",
        'raise _Fail("method_not_allowed", headers=(("Allow", ", ".join(allow)),))',
        'raise _Fail("method_not_allowed")',
        "[r2] 405 without Allow (no_reporting_endpoints_header_and_allow_on_405)",
    ),
    (
        "src/intake/access.py",
        "            self._in_flight += 1",
        "            pass",
        "[r2] no slot reserved at admit (parallel_attempts_reserve_a_slot_before_the_first_failure_is_recorded)",
    ),
    (
        "src/intake/access.py",
        "or lg.name.casefold() in seen:",
        "or lg.name in seen:",
        "[r2] duplicate login in another case accepted (logins_validation_extended)",
    ),
    (
        "src/intake/access.py",
        "    if not route.roles or TOKEN_HOLDER in route.roles:",
        "    if not route.roles:",
        "[r2] a row listing the token holder opened by a session (allowed_over_the_real_route_table)",
    ),
    (
        "src/intake/access.py",
        "    if name not in (COOKIE_SESSION, COOKIE_PRE) or not _ID_RE.fullmatch(value):",
        "    if not _ID_RE.fullmatch(value):",
        "[r2] set_cookie accepts any name (cookie_names_and_values_are_closed)",
    ),
    (
        "src/intake/access.py",
        "                del self._by_sid[k]  # expired sessions are swept, not kept until somebody looks them up",
        "                pass  # expired sessions are swept, not kept until somebody looks them up",
        "[r2] expired sessions not swept at create (expired_sessions_are_swept_at_create)",
    ),
    (
        "src/intake/access.py",
        "if v.login_name == login_name]:",
        "if True]:",
        "[r2] end_all ends other logins too (end_all_keeps_the_sessions_of_other_logins)",
    ),
    (
        "src/intake/access.py",
        "            self._in_flight = max(0, self._in_flight - 1)\n            self._trim(self._clock())",
        "            self._trim(self._clock())",
        "[r2] failed() keeps its slot (four_failures_never_throttle_and_the_fifth_does_within_the_gap)",
    ),
    (
        "src/intake/access.py",
        'compared)."""\n        with self._lock:\n            self._in_flight = max(0, self._in_flight - 1)',
        'compared)."""\n        with self._lock:\n            pass',
        "[r2] passed() keeps its slot (parallel_attempts_reserve_a_slot_before_the_first_failure_is_recorded)",
    ),
    (
        "src/intake/access.py",
        "        if age_over(st, self._clocks.stamp(), LIMIT_PRE_SESSION_S):",
        "        if self._clocks.stamp().mono - st.mono > LIMIT_PRE_SESSION_S:",
        "[r2] pre-session expiry on the monotonic clock only (pre_session_expires_on_either_clock_alone)",
    ),
    (
        "src/intake/access.py",
        "        if age_over(st, self._clocks.stamp(), LIMIT_PRE_SESSION_S):",
        "        if self._clocks.stamp().wall - st.wall > LIMIT_PRE_SESSION_S:",
        "[r2] pre-session expiry on the wall clock only (pre_session_expires_on_either_clock_alone)",
    ),
    (
        "src/intake/access.py",
        "    if not isinstance(header, str) or not header.isascii():",
        "    if not isinstance(header, str):",
        "[r2] non-ASCII Cookie header read (cookie_value_variants)",
    ),
    (
        "src/intake/access.py",
        "                len(self._failures) + self._in_flight >= THROTTLE_FAILURES\n                and self._last_checked is not None\n                and now - self._last_checked < THROTTLE_GAP_S\n",
        "                False\n",
        "throttle removed (throttle_429_no_sleep)",
    ),
    (
        "src/intake/access.py",
        "    if not route.roles or TOKEN_HOLDER in route.roles:\n        return False  # no roles = nobody; a row that lists the token holder is never opened by a session\n    if ANYONE in route.roles:\n        return True\n    if session is None or session.role not in ROLES:\n        return False\n    return session.role in route.roles",
        "    if TOKEN_HOLDER in route.roles:\n        return False\n    if ANYONE in route.roles:\n        return True\n    if session is None or session.role not in ROLES:\n        return False\n    return not route.roles or session.role in route.roles",
        "allowed true for empty roles (allowed_default_deny_and_require_role)",
    ),
    ("src/intake/service.py", 'if "upgrade" in by or any(', "if any(", "Upgrade accepted (no_upgrade)"),
    (
        "src/intake/service.py",
        "        if session is not None and route.name not in JSON_ROUTES:",
        "        if session is not None:",
        "dispatch passes touch=True for a JSON route (dispatch_touch_rule)",
    ),
    (
        "src/intake/service.py",
        "        flag.requested = True\n",
        "        threading.Event().set()\n        flag.requested = True\n",
        "[r3] signal handler takes a lock (the_signal_handler_takes_no_lock)",
    ),
    (
        "src/intake/service.py",
        "    restore = _stop_on_signals(flag)\n    try:\n        try:\n            run = start(s, hosts=hosts, limits=limits)\n",
        "    restore = []\n    try:\n        try:\n            run = start(s, hosts=hosts, limits=limits)\n            restore = _stop_on_signals(flag)\n",
        "[r3] signals installed after the start lines (the_signals_are_in_place_before_the_service_starts)",
    ),
    (
        "src/intake/service.py",
        "wanted = [signal.SIGTERM, signal.SIGINT]",
        "wanted = [signal.SIGTERM]",
        "[r3] Ctrl+C not a flag (a_process_stop_signal_ends_serve_like_ctrl_c)",
    ),
    (
        "src/intake/service.py",
        '([signal.SIGBREAK] if sys.platform == "win32" else [])',
        "[]",
        "[win] [r3] Ctrl+Break not handled (a_process_stop_signal_ends_serve_like_ctrl_c)",
    ),
    (
        "src/intake/service.py",
        "            print(line, flush=True)",
        "            print(line)",
        "[r3] start lines not flushed (every_start_line_is_flushed)",
    ),
    (
        "src/intake/service.py",
        "            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)",
        "            pass",
        "[win] [r3] listener not exclusive (a_rival_cannot_share_the_port_of_a_running_service_on_windows)",
    ),
    (
        "src/intake/service.py",
        '    log_level = s_log_level()  # INTAKE_LOG is read once, before anything is bound (a bad value is exit 3)\n    for sub in (s.intake_home / "inbox", s.intake_home / "out", s.run_dir):\n        sub.mkdir(parents=True, exist_ok=True)\n    try:\n        lock = lockfile.acquire(s.intake_home / "serve.lock")\n    except lockfile.LockHeld:\n        raise ConfigError("serve_running", "another intake serve is running") from None\n    servers: dict[str, IntakeServer] = {}\n',
        '    for sub in (s.intake_home / "inbox", s.intake_home / "out", s.run_dir):\n        sub.mkdir(parents=True, exist_ok=True)\n    try:\n        lock = lockfile.acquire(s.intake_home / "serve.lock")\n    except lockfile.LockHeld:\n        raise ConfigError("serve_running", "another intake serve is running") from None\n    servers: dict[str, IntakeServer] = {}\n    log_level = s_log_level()\n',
        "[r3] INTAKE_LOG read after the lock (intake_log_is_read_before_anything_is_bound)",
    ),
    (
        "src/intake/service.py",
        "            with self._active_lock:\n                self._active -= 1\n\n    def wait_idle",
        "            with self._active_lock:\n                self._active -= 0\n\n    def wait_idle",
        "[r3] running-handler count never goes down (an_idle_service_stops_at_once)",
    ),
    ("src/intake/service.py", '    "origin",\n', "", "[r3] repeated Origin read as the first (repeated_security_headers_are_refused)"),
    (
        "src/intake/service.py",
        '    "sec-fetch-site",\n',
        "",
        "[r3] repeated Sec-Fetch-Site read as the first (repeated_security_headers_are_refused)",
    ),
    (
        "src/intake/service.py",
        '    "sec-fetch-mode",\n',
        "",
        "[r3] repeated Sec-Fetch-Mode read as the first (repeated_security_headers_are_refused)",
    ),
    (
        "src/intake/service.py",
        '    "sec-fetch-dest",\n',
        "",
        "[r3] repeated Sec-Fetch-Dest read as the first (repeated_security_headers_are_refused)",
    ),
    (
        "src/intake/service.py",
        '    "content-type",\n)',
        ")",
        "[r3] repeated Content-Type read as the first (repeated_security_headers_are_refused)",
    ),
    (
        "src/intake/service.py",
        "        refused_total=req.server.shared.refused_total,\n",
        "",
        "[r3] refused_total not passed to the list (the_refused_total_of_the_last_scan_reaches_the_list_page)",
    ),
    (
        "src/intake/service.py",
        "    srv.shared.refused_total = result.refused_total\n",
        "",
        "[r3] refused_total not stored (the_refused_total_of_the_last_scan_reaches_the_list_page)",
    ),
    (
        "src/intake/service.py",
        "        if isinstance(e, _InboxUnavailable):",
        '        if e.code == "bad_config":',
        "[r3] every bad_config is a fixed 503 (a_missing_inbox_is_a_fixed_503_and_only_that)",
    ),
    (
        "src/intake/service.py",
        '            self.method = first_word.decode("ascii")',
        "            pass",
        "[r3] HEAD method unknown on early errors (head_gets_no_body_on_early_errors_too)",
    ),
    (
        "src/intake/access.py",
        "    expected = _expected(s, login if real else LOGINS[0])\n",
        '    expected = _expected(s, login) if real else "x"\n',
        "[r3] unknown name does not read the secret in match_login (missing_secret_is_503_for_every_name_not_only_the_real_one)",
    ),
    (
        "src/intake/access.py",
        "    if not isinstance(v, str) or len(v) > LIMIT_PASSPHRASE_CHARS:",
        "    if not isinstance(v, str):",
        "[r3] passphrase length cap removed (an_over_long_passphrase_is_refused_even_if_it_equals_the_secret)",
    ),
    (
        "src/intake/access.py",
        "if now - t <= THROTTLE_WINDOW_S]",
        "if now - t < THROTTLE_WINDOW_S]",
        "[r3] failure window shorter by one instant (the_failure_window_is_sixty_seconds)",
    ),
    (
        "src/intake/access.py",
        "        self._failures = [t for t in self._failures if now - t <= THROTTLE_WINDOW_S]",
        "        pass",
        "[r3] failures never age out (the_failure_window_is_sixty_seconds)",
    ),
    (
        "src/intake/access.py",
        "            self._trim(self._clock())\n            self._failures.append",
        "            self._failures.append",
        "[r3] failed() does not trim (failures_are_trimmed_when_recorded_too)",
    ),
    (
        "src/intake/access.py",
        " or age_over(v.created, now, LIMIT_SESSION_ABS_S)\n",
        "\n",
        "[r3] sweep ignores the absolute limit (an_old_session_is_swept_at_create_by_the_absolute_limit_too)",
    ),
    (
        "src/intake/access.py",
        "if age_over(v.last_touch, now, LIMIT_SESSION_IDLE_S) or age_over(v.created",
        "if age_over(v.created",
        "[r3] sweep ignores the idle limit (expired_sessions_are_swept_at_create)",
    ),
    (
        "src/intake/service.py",
        "wanted = [signal.SIGTERM, signal.SIGINT]",
        "wanted = [signal.SIGINT]",
        "[r3] SIGTERM not handled (a_process_stop_signal_ends_serve_like_ctrl_c)",
    ),
    (
        "src/intake/service.py",
        " or not hmac.compare_digest(current, shown):",
        ":",
        "[r3] the list is not compared before the write (an_invoice_approved_after_the_page_was_opened_is_not_written)",
    ),
    (
        "src/intake/service.py",
        " or not _PREVIEW_RE.fullmatch(shown)",
        "",
        "[r3] preview shape unchecked (a_missing_malformed_or_stale_preview_writes_nothing)",
    ),
    (
        "src/intake/service.py",
        "shown is None or ",
        "",
        "[r3] a missing preview is not refused (a_missing_malformed_or_stale_preview_writes_nothing)",
    ),
    (
        "src/intake/service.py",
        "            current = None\n        if current is None",
        "            raise\n        if current is None",
        "[r3] an unreadable list does not stop the write (a_token_that_cannot_be_computed_writes_nothing)",
    ),
    (
        "src/intake/service.py",
        "    lock = req.server.shared.work_lock\n",
        "    lock = threading.Lock()\n",
        "[r4] a decision does not take the work lock (test_an_approval_cannot_slip_into_a_running_write)",
    ),
    (
        "src/intake/service.py",
        "    lock = srv.shared.work_lock\n",
        "    lock = threading.Lock()\n",
        "[r4] the Write does not take the work lock (test_an_approval_cannot_slip_into_a_running_write)",
    ),
    (
        "src/intake/service.py",
        "        if not loopback:\n",
        "        if False:\n",
        "[r4] a non-loopback listener address is accepted (test_a_listener_address_outside_loopback_is_refused_before_anything_starts)",
    ),
    (
        "src/intake/service.py",
        "        except KeyboardInterrupt:  # a second press during a stuck start",
        "        except ZeroDivisionError:  # a second press during a stuck start",
        "[r4] an interrupt during start escapes (test_ctrl_c_twice_interrupts_a_stuck_start)",
    ),
    (
        "src/intake/service.py",
        "    return replace(_page(status, page, h), code=code)",
        "    return _page(status, page, h)",
        "[r4] sign-in refusal page has no log code (test_refused_sign_in_and_step_up_pages_log_their_code)",
    ),
    (
        "src/intake/service.py",
        '            code=kw.get("refusal_code"),\n',
        "",
        "[r4] step-up refusal page has no log code (test_refused_sign_in_and_step_up_pages_log_their_code)",
    ),
    (
        "src/intake/service.py",
        "        elif self.allow_reuse_address:\n            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)",
        "        elif False:\n            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)",
        "[posix] [r4] listener without SO_REUSEADDR (test_a_quick_restart_after_a_stop_does_not_fail_with_port_in_use)",
    ),
    (
        "src/intake/access.py",
        "        with self._lock:\n            now = self._clocks.stamp()  # under the lock (see create)\n",
        "        now = self._clocks.stamp()\n        with self._lock:\n",
        "[r4] a stamp taken before the lock in get (test_stamps_are_taken_under_the_lock)",
    ),
    (
        "src/intake/access.py",
        '        with self._lock:\n            # taken UNDER the lock: stamps of different threads are then ordered, so a fresh session is never "from the future"\n            now = self._clocks.stamp()\n            sess = Session(sid, login.name, login.role, csrf, now, now)\n',
        "        now = self._clocks.stamp()\n        with self._lock:\n            sess = Session(sid, login.name, login.role, csrf, now, now)\n",
        "[r4] a stamp taken before the lock in create (test_stamps_are_taken_under_the_lock)",
    ),
    (
        "src/intake/service.py",
        "            except KeyboardInterrupt:\n                # the second press, wherever it lands (the message, the stop): stop at once; later presses are ignored\n                run.stop(grace_s=0.0)",
        "            except KeyboardInterrupt:\n                # the second press, wherever it lands (the message, the stop): stop at once; later presses are ignored\n                raise",
        "[r5] a second Ctrl+C escapes the stop (test_a_second_ctrl_c_during_the_stop_stops_at_once)",
    ),
    (
        "src/intake/service.py",
        "        if flag.presses == 2:\n            raise KeyboardInterrupt",
        "        if False:\n            raise KeyboardInterrupt",
        "[r5] a second signal is ignored (test_a_second_signal_raises_and_the_first_only_sets_the_flag)",
    ),
    (
        "src/intake/service.py",
        "    if not lock.acquire(timeout=WORK_LOCK_WAIT_S):  # a Write is running",
        "    if not lock.acquire():  # a Write is running",
        "[r5] a decision waits for the work lock for ever (test_a_decision_and_a_write_wait_for_the_work_lock_only_briefly)",
    ),
    (
        "src/intake/service.py",
        "    if not lock.acquire(timeout=WORK_LOCK_WAIT_S):  # an approval is running",
        "    if not lock.acquire():  # an approval is running",
        "[r5] a Write waits for the work lock for ever (test_a_decision_and_a_write_wait_for_the_work_lock_only_briefly)",
    ),
    (
        "src/intake/access.py",
        "        with self._lock:\n            now = self._clocks.stamp()  # under the lock (see SessionStore.create)\n            for k in [k for k, (_, st) in",
        "        now = self._clocks.stamp()\n        with self._lock:\n            for k in [k for k, (_, st) in",
        "[r5] a stamp taken before the lock in issue (test_stamps_are_taken_under_the_lock)",
    ),
    (
        "src/intake/settings.py",
        "        return True\n    return not (isinstance(ex, dict)",
        "        return False\n    return not (isinstance(ex, dict)",
        "[r5] an unreadable kill-switch policy counts as not engaged (test_kill_switch_engaged_shown_and_closes_the_write_form)",
    ),
    (
        "src/intake/service.py",
        "            loopback = ipaddress.IPv4Address(host).is_loopback",
        "            loopback = True",
        "[r5] any listener address is accepted (test_a_listener_address_outside_loopback_is_refused_before_anything_starts)",
    ),
    (
        "src/intake/service.py",
        "        except (Refused, sqlite3.Error, OSError):",
        "        except Exception:",
        "[r5] a coding error in the token step is a 409 (test_a_coding_error_in_the_token_step_is_a_500_not_a_reload_loop)",
    ),
    (
        "src/intake/service.py",
        "        if run is not None:\n            run.stop(grace_s=0.0)",
        "        if run is not None:\n            pass",
        "[r5] a failed start leaves the listeners and the lock (test_an_interrupt_while_the_threads_start_gives_everything_back)",
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
    if message.startswith("Failed: CANNOT RUN"):  # a test that could not run (a port busy, a tool missing) says so; that is no kill
        return "CRASH"
    if re.search(
        r"raised (AttributeError|NameError|TypeError|ImportError|ModuleNotFoundError|SyntaxError|IndentationError|UnboundLocalError)",
        message,
    ):
        return "CRASH"  # a helper that turns an exception into a plain failure must not turn a CODING error into a kill
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


def _killer(name: str) -> str | None:
    """The test the mutant's name promises will kill it: the last word in parentheses, e.g. ``... (equal_secret_behaviour)``."""
    m = re.search(r"\(([A-Za-z0-9_]+)\)\s*$", name)
    return m.group(1) if m else None


def _node_ids(tests: tuple[str, ...]) -> list[str]:
    """Every collected test id of the WP6 test files (one collect-only run)."""
    rc, _junit, so = _pytest_once(tests, ["--collect-only"])
    return [ln.strip() for ln in so.splitlines() if "::" in ln]


def _ids_for(killer: str, ids: list[str]) -> list[str]:
    """The exact node ids a killer name stands for: the test function ``test_<killer>`` (or ``<killer>`` if it already starts with ``test_``), with every
    parameter. A substring is NOT enough (``export_step_up`` must not select ``export_step_up_throttled``)."""
    want = killer if killer.startswith("test_") else "test_" + killer
    return [i for i in ids if re.fullmatch(rf".*::{re.escape(want)}(\[.*\])?", i)]


def _failed_tests(junit: str) -> list[str]:
    pat = r'<testcase classname="[^"]*\.(\w+)" name="([^"]*)"[^>]*>\s*<(?:failure|error)'
    return [f"{c}::{n}" for c, n in re.findall(pat, junit)]


def _pytest_once(tests: tuple[str, ...], extra: list[str]) -> tuple[int, str, str]:
    """One pytest run for the WP6 tests. Run with ``python -B``: byte-code files are not written (a mutant and the restored file can have the same size and the same
    modification second, and a stale ``.pyc`` would then run the wrong code)."""
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "junit.xml"
        cmd = [
            "uv",
            "run",
            "--group",
            "test",
            "python",
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"--junitxml={report}",
            *extra,
            *tests,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)  # noqa: S603
        try:
            stdout, _ = proc.communicate(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            return -1, "", "TIMEOUT"
        return proc.returncode, report.read_text(encoding="utf-8") if report.exists() else "", stdout


def run_named(group: str, muts: list, only: str | None, out: list[str], tests: tuple[str, ...] = ()) -> tuple[int, int, int, int]:
    """Like ``run``, but a mutant whose name promises a killing test (``... (test_stem)``) counts as KILLED only when THAT test fails. First the named
    test alone (``-k``); if it passes, the whole set decides between KILLED-ELSEWHERE (something else failed: the name or the test is stale or weak),
    SURVIVED and CRASH. A name without a promise is judged by the whole set and shown as ``(unnamed)``. The line says which tests failed."""
    killed = survived = skipped = crashed = 0
    all_ids = _node_ids(tests)
    promised = sorted({i for _p, _a, _b, n in muts if (not only or only in n) and _killer(n) for i in _ids_for(_killer(n), all_ids)})
    if promised:  # a killer that already fails on the clean tree would "kill" every mutant it is named for
        rc0, junit0, so0 = _pytest_once(tuple(promised), [])
        if rc0 != 0:
            line = f"BASELINE [{group}] the promised killer tests are not green on the clean tree: {', '.join(_failed_tests(junit0)[:8]) or so0[-300:]}"
            print(line, flush=True)
            out.append(line)
            return 0, 0, 0, 1
        print(f"BASELINE [{group}] {len(promised)} promised killer tests are green on the clean tree", flush=True)
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
            killer = _killer(name)
            by = ""
            if killer:
                ids = _ids_for(killer, all_ids)
                rc, junit, so = _pytest_once(tuple(ids), []) if ids else (5, "", "")
                if rc == 5:
                    verdict = "NO-KILLER"  # no test has that name
                else:
                    verdict = judge(rc, junit)
                    by = ", ".join(_failed_tests(junit)[:3])
                    if verdict == "SURVIVED":
                        rc2, junit2, so2 = _pytest_once(tests, ["-x"])
                        verdict2 = judge(rc2, junit2)
                        if verdict2 == "KILLED":
                            verdict, by = "ELSEWHERE", ", ".join(_failed_tests(junit2)[:3])  # killed, but not by the test the name promises
                        elif verdict2 != "SURVIVED":
                            verdict = "CRASH"
            else:
                rc, junit, so = _pytest_once(tests, ["-x"])
                verdict = judge(rc, junit)
                by = "(unnamed) " + ", ".join(_failed_tests(junit)[:2])
            line = f"{verdict:<9}[{group}] {name}  {('by ' + by) if by else ''}"
            print(line[:300], flush=True)
            out.append(line)
            killed += verdict == "KILLED"
            survived += verdict == "SURVIVED"
            crashed += verdict in ("CRASH", "ELSEWHERE", "NO-KILLER")
        finally:
            full.write_bytes(orig.encode("utf-8"))
    return killed, survived, skipped, crashed


def check_killers(muts: list, tests: tuple[str, ...]) -> list[str]:
    """Every promised killer must be a part of the id of at least one collected test; returns the names that promise a test that does not exist."""
    ids = _node_ids(tests)
    return [
        m[3] for m in muts if not _killer(m[3]) or not _ids_for(_killer(m[3]), ids)
    ]  # a mutant without a promised test is also reported


# 6c (review pages): the killer tests are in tests/test_review_page.py
WP6 += [
    (
        "src/intake/review_page.py",
        "source_text=item.source_text if approver else None,",
        "source_text=item.source_text,",
        "viewer sees the invoice text (viewer_sees_no_invoice_text)",
    ),
    (
        "src/intake/review_page.py",
        "original if approver else None)",
        "original)",
        "viewer sees the restored bank values (test_d10_shows_candidate_and_on_file)",
    ),
    (
        "src/intake/review_page.py",
        'if approver and "D12" in item.flags',
        'if "D12" in item.flags',
        "viewer sees the D12 numbers (d12_shows_unexplained_numbers)",
    ),
    (
        "src/intake/review_page.py",
        'Run intake check.", "bad")',
        'Run intake check. " + spend.halt[1], "bad")',
        "halt reason shown (halted_banner_has_no_reason_code)",
    ),
    (
        "src/intake/review_page.py",
        "if spend is None or spend.halt is None:",
        "if spend is None:",
        "unreadable halt state read as not halted (spend_unavailable_shown)",
    ),
    (
        "src/intake/review_page.py",
        "return ui.KILL_SWITCH_ENGAGED if settings.read_kill_switch() else None",
        "return None",
        "engaged kill switch gives no banner (kill_switch_unreadable_shown_engaged)",
    ),
    (
        "src/intake/review_page.py",
        '    if session.role != routes.APPROVER:\n        raise Refused("role_denied"',
        '    if False:\n        raise Refused("role_denied"',
        "export page built for a viewer (test_viewer_sees_no_invoice_text)",
    ),
    (
        "src/intake/review_page.py",
        "conn = workqueue.connect_readonly(s)",
        "conn = workqueue.connect(s)",
        "page opens a write-capable connection (test_gets_use_readonly_connection_ast)",
    ),
    (
        "src/intake/review_page.py",
        "except Exception:  # noqa: BLE001 (per row: one bad item must not break the queue)",
        "except KeyboardInterrupt:  # noqa: BLE001",
        "one bad row breaks the list (one_bad_row_never_breaks_the_list)",
    ),
    ("src/intake/review_page.py", "_DEGRADED[kind] += 1", "pass", "degrade event not counted (one_bad_row_never_breaks_the_list)"),
    (
        "src/intake/review_page.py",
        '_LOG.warning("review page degraded: kind=%s item=%s", kind, shown)',
        "pass",
        "degrade event not logged (one_bad_row_never_breaks_the_list)",
    ),
    (
        "src/intake/review_page.py",
        "if item.state not in _WAITING:",
        "if False:",
        "approve offered on a decided item (decision_and_receipt_shown)",
    ),
    (
        "src/intake/review_page.py",
        'if r.code == "invalid_reason":',
        "if False:",
        "D06 and D12 approve needs no reason (approve_offered_when_clean_and_needs_reason_for_d06_and_d12)",
    ),
    (
        "src/intake/review_page.py",
        "kw = _common(s, item)\n    view = ui.safe_invoice_view(**kw)",
        "kw = _common(s, item)\n    view = ui.InvoiceView(**kw)",
        "one inconsistent row is dropped, not degraded (inconsistent_approve_verdict_degrades_one_row_and_is_counted)",
    ),
    ("src/intake/review_page.py", "ui.apply_query(rows, query)", "tuple(rows)", "list not in the needs-a-person-first order (list_order)"),
    (
        "src/intake/review_page.py",
        "_text(s, r.reason)) for r in refused",
        "r.reason) for r in refused",
        "refused file shown with its raw code (refused_files_panel_text)",
    ),
    (
        "src/intake/review_page.py",
        'ERROR_TEXT.get(code or "", ERROR_TEXT["internal"])',
        'ERROR_TEXT.get(code or "", code or "")',
        "unknown code shown as the code (test_refused_files_panel_text)",
    ),
    (
        "src/intake/review_page.py",
        "unreadable = list(workqueue.unreadable_ids(s, conn=conn))",
        "unreadable = []",
        "damaged items not named (unreadable_items_panel)",
    ),
    (
        "src/intake/review_page.py",
        'if "D10" in item.flags and on_file is not None:',
        "if False:",
        "D10 card not built (d10_shows_candidate_and_on_file)",
    ),
    (
        "src/intake/review_page.py",
        'whole = len(run.results) == 1 and run.results[0].code in ("kill_switch", "db_busy", "db_error")',
        "whole = False",
        "whole-export outcome labelled as an invoice (export_kill_switch_shown)",
    ),
    (
        "src/intake/review_page.py",
        'file_text = exporter.FILE_TEXT.get(run.file, ERROR_TEXT["internal"])',
        "file_text = None",
        "file status not shown after a run (export_preview_and_run_results)",
    ),
    (
        "src/intake/review_page.py",
        "may_export=kill is False and bool(rows)",
        "may_export=bool(rows)",
        "export allowed while the switch is engaged or unreadable (test_kill_switch_engaged_shown_and_closes_the_write_form)",
    ),
    (
        "src/intake/review_page.py",
        "    return sentence.format(reason_min_chars=s.review.reason_min_chars, reason_max_chars=s.review.reason_max_chars)",
        "    return sentence",
        "reason limits not filled in (invalid_reason_sentence_is_filled_from_config)",
    ),
    (
        "src/intake/review_page.py",
        ".casefold())",
        ")",
        "supplier looked up with a different key rule than the check (supplier_lookup_uses_the_check_key)",
    ),
    (
        "src/intake/review_page.py",
        "except (ValueError, TypeError):\n        # a receipt",
        "except KeyboardInterrupt:\n        # a receipt",
        "bad receipt time breaks the invoice page (bad_receipt_time_degrades_not_fails)",
    ),
    (
        "src/intake/review_page.py",
        "    except Exception:  # noqa: BLE001 (a fault in a check",
        "    except KeyboardInterrupt:  # noqa: BLE001 (a fault in a check",
        "a fault in a check hides the invoice (check_fault_is_shown_and_counted)",
    ),
    (
        "src/intake/review_page.py",
        "if scan_running or (scanner is not None and scanner.running())",
        "if scanner is not None and scanner.running()",
        "scan_running flag ignored (scan_running_banner_on_every_page)",
    ),
    (
        "src/intake/review_page.py",
        '"changed_while_read": "This file changed while it was being read; it is read again at the next scan.",\n',
        "",
        "changed_while_read shown as an internal error (changed_while_read_has_its_own_sentence_and_refused_total_is_shown)",
    ),
    (
        "src/intake/review_page.py",
        "if refused_total is not None and refused_total > len(refused):",
        "if False:",
        "refused_total not shown (changed_while_read_has_its_own_sentence_and_refused_total_is_shown)",
    ),
    (
        "src/intake/review_page.py",
        "    kill = bool(settings.read_kill_switch())",
        "    kill = False",
        "kill switch value ignored on the export page (kill_switch_engaged_shown_and_closes_the_write_form)",
    ),
    (
        "src/intake/review_page.py",
        "may_export=kill is False and bool(rows) and not degraded,",
        "may_export=kill is False and bool(rows),",
        "Write stays on with a row that could not be previewed (a_degraded_export_row_turns_write_off)",
    ),
    (
        "src/intake/review_page.py",
        "view = ui.safe_invoice_view(**kw)  # as the list",
        "view = ui.InvoiceView(**kw)  # as the list",
        "item page raises on a contradicting verdict (item_page_degrades_a_contradicting_verdict_like_the_list)",
    ),
    (
        "src/intake/review_page.py",
        "d.reason if approver else None",
        "d.reason",
        "viewer gets the reason text (viewer_never_gets_the_reason_text)",
    ),
    (
        "src/intake/review_page.py",
        "if decision is None or outcome_code != decision.decision:",
        "if decision is None:",
        "outcome banner without a matching stored decision (decision_and_receipt_shown)",
    ),
    (
        "src/intake/review_page.py",
        "unbuilt.append(item.id)",
        "unreadable.append(item.id)",
        "page faults reported as damaged stored data (one_bad_row_never_breaks_the_list)",
    ),
    (
        "src/intake/review_page.py",
        '"total_minor": total if type(total) is int else None,',
        '"total_minor": total if type(total) is int else 0,',
        "missing total shown as 0.00 (missing_total_is_not_recorded_not_zero)",
    ),
    (
        "src/intake/review_page.py",
        'return "not recorded" if v is None else str(v)',
        "return str(v)",
        "missing line value printed as None (failed_fields_are_named_and_missing_line_values_say_not_recorded)",
    ),
    (
        "src/intake/review_page.py",
        "if failed:\n        notes.append(",
        "if False:\n        notes.append(",
        "failed field names not shown (failed_fields_are_named_and_missing_line_values_say_not_recorded)",
    ),
    (
        "src/intake/review_page.py",
        'return ui.BannerView("spend_total", "Our spend counter: "',
        'return ui.BannerView("spend_total", "Spend: "',
        "spend line wording (spend_total_line_wording)",
    ),
    ("src/intake/review_page.py", "total = int(raw)", "total = 0", "export preview total lost (export_preview_and_run_results)"),
    (
        "src/intake/review_page.py",
        'ui.placeholder("BANK", n)',
        'f"bank-{n}"',
        "bank mark that ui cannot read as a chip (d10_shows_candidate_and_on_file)",
    ),
    (
        "src/intake/ui.py",
        "    return mark\n",
        "    return mark.lower()\n",
        "ui.placeholder returns a mark ui does not recognise (ui_placeholder_grammar_and_chip_words)",
    ),
    (
        "src/intake/ui.py",
        'return text("not recorded") if minor is None else money(minor, currency)',
        "return money(minor or 0, currency)",
        "ui shows a missing total as 0 (missing_total_is_not_recorded_not_zero)",
    ),
    (
        "src/intake/review_page.py",
        "refused_total: int | None,\n) -> ui.QueueView:",
        "refused_total: int | None = None,\n) -> ui.QueueView:",
        "refused_total has a default (refused_total_is_a_required_keyword)",
    ),
    (
        "src/intake/review_page.py",
        "return v if isinstance(v, str) and v.strip() else None",
        "return v if isinstance(v, str) else None",
        "empty export cell shown empty (empty_cells_in_the_export_preview_say_not_recorded)",
    ),
    (
        "src/intake/review_page.py",
        "check the list before writing.",
        "try again.",
        "export_changed sentence changed (export_page_form_sends_the_token_back_and_it_matches_the_write_path)",
    ),
    (
        "src/intake/ui.py",
        'tok=h(\'<input type="hidden" name="preview" value="{p}">\', p=v.preview_token) if v.preview_token else _mk(""),',
        'tok=_mk(""),',
        "Write form without the preview field (export_page_form_sends_the_token_back_and_it_matches_the_write_path)",
    ),
    (
        "src/intake/ui.py",
        "if self.preview_token is not None and (",
        "if False and (",
        "preview token not validated (no_token_no_write_form_and_a_viewer_never_gets_it)",
    ),
    (
        "src/intake/review_page.py",
        '"\\n".join(parts)',
        '"\\n".join([])',
        "token ignores every pending row (token_changes_with_a_second_approve_decision)",
    ),
    (
        "src/intake/review_page.py",
        "{'-' if seq is None else seq}",
        "-",
        "token ignores the latest decision (token_changes_with_a_second_decision_that_looks_identical)",
    ),
    (
        "src/intake/review_page.py",
        "json.dumps(p.row, sort_keys=True, ensure_ascii=True)",
        '""',
        "token ignores the row text a Write would store (token_changes_for_raw_duplicate_flags_even_though_the_content_code_does_not)",
    ),
    (
        "src/intake/review_page.py",
        '"refused:" + (p.refusal or "")',
        '"refused"',
        "token ignores the refusal code (two_different_refusal_codes_give_different_tokens)",
    ),
    (
        "src/intake/review_page.py",
        "token = _token_of(conn, previews)",
        "token = _token_of(conn, [])",
        "page token not made from the rows it shows (page_token_is_computed_from_the_rows_it_shows)",
    ),
    (
        "src/intake/review_page.py",
        "seq = seqs.get(p.item_id)",
        "seq = workqueue.latest_decision(conn, workqueue.get_in(conn, p.item_id).uid).seq",
        "decision seq read per row (token_costs_a_constant_number_of_statements)",
    ),
    (
        "src/intake/workqueue.py",
        "(SELECT MAX(d.seq) FROM decisions d WHERE d.item_uid = i.uid)",
        "(SELECT MIN(d.seq) FROM decisions d WHERE d.item_uid = i.uid)",
        "first decision read instead of the latest (one_query_token_still_follows_the_latest_decision)",
    ),
    (
        "src/intake/workqueue.py",
        "WHERE i.state = 'APPROVED' AND i.uid NOT IN (SELECT item_uid FROM exports) ORDER BY i.created_at, i.uid\"\n",
        "WHERE i.state = 'APPROVED' ORDER BY i.created_at, i.uid\"\n",
        "exported rows counted as pending (latest_decision_seqs_matches_the_per_row_reads_and_the_pending_order)",
    ),
]
WP6_TESTS.append("tests/test_review_page.py")


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


def wp6_plan(platform: str) -> tuple[list, str]:
    """The WP6 mutants this OS runs, and one line that reconciles the counts: all patterns = run here + left for the other OS ([posix] mutants are not run on
    Windows, [win] mutants are not run elsewhere), so Windows runs patterns minus [posix] and Linux runs patterns minus [win]."""
    win = platform == "win32"
    run = [m for m in WP6 if not (win and "[posix]" in m[3]) and not (not win and "[win]" in m[3])]
    posix_n, win_n = sum("[posix]" in m[3] for m in WP6), sum("[win]" in m[3] for m in WP6)
    other = posix_n if win else win_n
    line = f"WP6 plan: {len(WP6)} patterns, {posix_n} [posix], {win_n} [win]; this OS ({'Windows' if win else 'POSIX'}) runs {len(run)} = {len(WP6)} - {other} left for the other OS"
    return run, line


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
        wp6, plan_line = wp6_plan(sys.platform)  # POSIX-only branches are killed in the Linux run
        print(plan_line, flush=True)
        if "--check-killers" in sys.argv:  # every promised killer test exists (collect only)
            missing = check_killers(wp6, tuple(WP6_TESTS))
            print(chr(10).join(f"NO TEST FOR {n}" for n in missing) or "every promised killer test exists")
            return 1 if missing else 0
        k, sv, sk, cr = run_named("WP6", wp6, only, out, tuple(WP6_TESTS))
        out.append(
            f"WP6: killed {k}, survived {sv}, skipped {sk}, crashed {cr}. Total mutants run: {k + sv + sk + cr} of {len(wp6)} selected ({plan_line})"
        )
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
