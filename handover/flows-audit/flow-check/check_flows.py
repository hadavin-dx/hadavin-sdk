"""Read-only structural check of generated n8n flow JSON files. Nothing is run in n8n. Standard library only.

Usage:
  check_flows.py DIR [DIR ...] [options]
Options:
  --expect FILE=NODES:CONNS     expected node and connection count of one flow file (repeatable), e.g. mf-form.json=12:11
  --expect-json PATH            same as JSON {"mf-form.json": {"nodes": 12, "connections": 11}, ...}
  --files a.json,b.json,...     exact list of *.json files each DIR must hold (default: the four mf-*.json flow files)
  --baseline DIR                directory of the unpatched flows: an IF node that already lacks the SAME branch there is only a WARN, else FAIL. CAUTION: pointing it at the folder being checked excuses EVERY IF gap in it, so do not do that for the take; use --accept-if
  --accept-if FILE=NODE:OUT[,OUT]  recorded decision (repeatable): this IF node of this file is accepted to lack exactly these outputs (0 or 1); it is a WARN and a known open problem. Any other missing branch, or a different one, is a FAIL
  --accept-no-save FILE         recorded decision (repeatable): this flow file (exact name, only a flow whose triggers are all schedule triggers, i.e. the recovery flow) may keep run saving off; printed as 'ACCEPTED: recovery flow not part of the take (decision 4)', not as a WARN. Any other flow, or a name that excuses nothing, stays a WARN
  --patch-checks F002,F008      assert the F-002 and/or F-008 patch content (names, links, settings) in the given DIRs
  --diff-base DIR --allow F002,F008 (--allow requires --patch-checks naming at least the same patches) [--diff-out FILE]
                                node-level diff DIR vs DIR (patched vs unpatched); FAIL on any change the allowed patches do not explain
  --quiet-info                  do not print the type table and the placeholder list (the credential list per flow is always printed)
  --require-webhook-auth        a webhook or form trigger without authentication is a FAIL (default: WARN-LEAD-DECISION line, exit stays 0, counted as a known open problem)
  --expect-credential KIND=NAME a node credential of this kind (for example postgres, smtp) must have exactly this name, else FAIL (repeatable)
  --block-env-access            a node that reads $env.X is a FAIL (default: WARN-LEAD-DECISION): use when the take switches off env access inside nodes
  --require-real-credential-ids a credential id or sub-workflow id that is still a placeholder is a FAIL (default: always printed as WARN, even with --quiet-info)
  --ddl FILE                    SQL file with the CREATE TABLE of the lead table: every column used in a postgres query string of the flows must exist in it, else WARN naming the missing columns. Without it the columns are NOT checked and the run says so loudly
  --fail-unverified             rules that come from memory of n8n (marked 'n8n rule UNVERIFIED') are WARN by default; this makes them FAIL
Needs Python 3.10 or newer (the script says so and exits 3 on an older one).

F8 EXTENSION (flow-check/): started from patch-apply/check_flows.py (F4 round 3), nothing removed. New checks are listed in
flow-check/REPORT.md. New options: --require-webhook-auth (webhook without authentication = FAIL, default WARN), --table (print
the error-settings table per file), --files all (every *.json in each DIR). Nothing is run in n8n.

Checks per file (FAIL = exit code 1): JSON parses; every node has name and type; no duplicate names; every connection
source and target exists; at least one trigger; every node reachable from a trigger (reachability walk over all output
types, so a node whose only incoming link comes from an orphan or from itself is unreachable); node/connection counts
equal the expected ones; onError=continueErrorOutput nodes should have a non-empty ERROR output, which is the LAST output (main[1] for most steps, main[2] for an IF step, after the rules for a switch step): a missing one is a WARN (n8n rule UNVERIFIED), a FAIL with --fail-unverified; IF nodes have both branch outputs;
every $('Name') and $node["Name"] inside an expression names a node of the same file.
Trigger = exact type n8n-nodes-base.webhook, n8n-nodes-base.executeWorkflowTrigger, n8n-nodes-base.formTrigger, n8n-nodes-base.cron, or a type
ending in 'Trigger'. respondToWebhook is NOT a trigger.
F-002 Claim is printed with a WARN (UNPROVEN until a test run in n8n): exit 0 does NOT clear F-002. A node with alwaysOutputData AND onError=continueErrorOutput is a FAIL (round 3).
WARN-LEAD-DECISION lines (webhook or form without authentication, nodes that read $env) keep exit 0 on purpose, but the closing block always prints 'OPEN LEAD DECISIONS: n webhook(s) without auth, m $env node(s)'.
Rules that come from MEMORY of n8n, not from a source in this repo (tag 'n8n rule UNVERIFIED'; WARN only unless --fail-unverified): webhook authentication values (none, basicAuth, headerAuth, jwtAuth;
form trigger: none, basicAuth), the credential kind each of them needs (httpBasicAuth, httpHeaderAuth, jwtAuth), the credential kinds of postgres, smtp and hubspot nodes, the position of the error output,
the default responseMode, and the rule that two webhooks may not share method+path or webhookId (checked across ALL folders given in one run, form triggers included).
Exit code: 0 only if no FAIL; 1 otherwise; 2 for a usage error (unknown option, missing value, unknown patch name, bad --expect); 3 when the checker itself broke or could not write its --diff-out file (never a FAIL verdict about the flows)."""

import collections
import json
import os
import re
import sys
import unicodedata

if sys.hexversion < 0x030A0000:  # Python 3.10 = 0x030A0000
    print("check_flows.py needs Python 3.10 or newer; found " + sys.version.split()[0])
    sys.exit(3)

OPTS = {
    "webhook_auth": False,
    "table": False,
    "block_env": False,
    "real_ids": False,
    "fail_unv": False,
    "cred_names": {},
    "accept_if": {},
    "accept_nosave": set(),  # flow file names whose "run saving is off" WARN is an accepted decision (--accept-no-save)
    "ddl": None,  # table name -> set of column names, from --ddl FILE
}
PARAM_PH = []  # placeholders found in node settings (not credential ids): they must be filled before import
SQL_DONE = {
    "checked": 0,
    "col_warn": 0,
    "tbl_warn": 0,
    "no_query": 0,
    "uncompared": 0,  # query strings with no readable table name (for example only a {{ }} expression): read, but nothing was compared
    "blanked": 0,  # compared query strings that contain {{ }} parts: those parts were blanked, not compared
    "same_as_sql_word": 0,  # columns of the --ddl file whose name is also an SQL word: a use of them cannot be told from the SQL word, so they are never compared
}  # queries compared with the --ddl table definition, and what that comparison found
CRED_PH = []  # credential ids and sub-workflow ids that are still placeholders (they must be replaced before import)
ENV_USE = []  # steps that read environment variables: "file node: tokens"
LEAD = {
    "webhook": 0,
    "env": 0,
}  # open lead decisions seen in this run (printed in the closing block)

FILES_DEFAULT = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
TRIGGER_EXACT = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.executeWorkflowTrigger",
    "n8n-nodes-base.formTrigger",
    "n8n-nodes-base.cron",
}
PLACEHOLDERS = [
    "PLACEHOLDER",
    "PG_CREDENTIAL_ID",
    "SMTP_CREDENTIAL_ID",
    "SUB_WORKFLOW_ID",
    "HS_CRED",
    "HUBSPOT_CREDENTIAL_ID",
    "CHANGE_ME",
    "CHANGEME",
    "REPLACE_ME",
    "TODO",
]
MAIL_KEYS = (
    "fromEmail",
    "toEmail",
    "ccEmail",
    "bccEmail",
    "replyTo",
)  # settings that must hold one e-mail address
REF = re.compile(
    r"""\$\(\s*['"`]([^'"`]+)['"`]\s*\)|\$node\[\s*['"`]([^'"`]+)['"`]\s*\]|\$items\(\s*['"`]([^'"`]+)['"`]|\$node\.([A-Za-z_][A-Za-z0-9_]*)"""
)
DYNREF = re.compile(
    r"""\$\(\s*(?:['"`][^'"`]*['"`]\s*)?[^'"`)\s]|\$node\[\s*(?:['"`][^'"`]*['"`]\s*)?[^'"`\]\s]"""
)  # a node name that is not one plain quoted text: cannot be checked statically
PREV = re.compile(r"\$prevNode\b")
STICKY = "n8n-nodes-base.stickyNote"
SCHEDULE = "n8n-nodes-base.scheduleTrigger"
KEY_COND = "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}"
WANT_CONN = {
    "Valid": {"main": [[{"node": "KeyOk", "type": "main", "index": 0}]]},
    "KeyOk": {
        "main": [
            [{"node": "Claim", "type": "main", "index": 0}],
            [{"node": "ReplyBadKey", "type": "main", "index": 0}],
        ]
    },
    "Claim": {
        "main": [
            [{"node": "Claimed", "type": "main", "index": 0}],
            [{"node": "ReplyStoreFail", "type": "main", "index": 0}],
        ]
    },
}
F002_UNPROVEN = "patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer"
ENVTOK = re.compile(
    r"\$env\s*\?\.\s*[A-Za-z0-9_]+|\$env\s*\?\.\s*\[[^\]]*\]|\$env\s*\.\s*[A-Za-z0-9_]+|\$env\s*\[[^\]]*\]|\$env\b|\bprocess\.env\b(?:\.[A-Za-z0-9_]+|\s*\[[^\]]*\])?"
)  # $env.X, $env?.X, $env["X"], bare $env, process.env.X, process.env["X"]
# every way a malformed (but parsable) flow file can make the checker's own code raise: reported as a FAIL, never a Traceback
READ_ERRORS = (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError)
# every ordinary Python error class (no blind "except Exception"); anything outside this list (for example KeyboardInterrupt) is not a checker fault
ANY_CRASH = READ_ERRORS + (
    ArithmeticError,
    LookupError,
    RuntimeError,
    NameError,
    AssertionError,
    ImportError,
    EOFError,
    UnicodeError,
    SyntaxError,
)
FAILS, WARNS, KNOWN = [], [], []
ACCEPT_USED = (
    set()
)  # (file, node) pairs of --accept-if that matched an IF node with exactly that gap
ACCEPTED_IF = []  # IF branches excused by a recorded --accept-if decision
ACCEPTED_SAVE = []  # flows whose "run saving is off" WARN is excused by a recorded --accept-no-save decision
ACCEPT_SAVE_USED = set()  # flow file names of --accept-no-save that excused a real WARN
SAVE_ACCEPT_REASON = "recovery flow not part of the take (decision 4)"
UNV = "n8n rule UNVERIFIED"  # rules about n8n itself that no source in this repo backs (from memory of n8n): WARN only; --fail-unverified makes them FAIL


def fail(where, msg):
    FAILS.append(f"{where}: {msg}")
    print("FAIL", where, msg)


def warn(where, msg, known=False):
    """known=True marks a defect we already know is open (it is counted in the closing block 'Known open problems')."""
    WARNS.append(f"{where}: {msg}")
    print("WARN", where, msg)
    if known:
        KNOWN.append(f"{where}: {msg}")


def lead(where, msg):
    """An open decision for the lead or owner: its own WARN-LEAD-DECISION line, exit code unchanged, counted as a known open problem."""
    WARNS.append(f"{where}: {msg}")
    KNOWN.append(f"{where}: {msg}")
    print("WARN-LEAD-DECISION", where, msg)


def unv(where, msg):
    """A rule that comes from memory of n8n (UNVERIFIED): WARN with the tag, or FAIL with the tag under --fail-unverified."""
    if OPTS["fail_unv"]:
        fail(where, f"{msg} [{UNV}]")
    else:
        warn(where, f"{msg} [{UNV}; run with --fail-unverified to make it a FAIL]")


def final_block():
    print(
        f"OPEN LEAD DECISIONS: {LEAD['webhook']} webhook(s) without auth, {LEAD['env']} $env node(s)"
        "  (exit 0 does NOT mean authentication was checked)"
    )
    print(
        "No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): "
        "check it on the machine that films the take; run with --block-env-access to see which steps depend on it."
    )
    if ACCEPTED_IF:
        print(f"IF branches accepted by a recorded decision (--accept-if): {len(ACCEPTED_IF)}")
        for k in ACCEPTED_IF:
            print("  - " + k)
    if ACCEPTED_SAVE:
        print(
            f"Run-saving left off by a recorded decision (--accept-no-save), {SAVE_ACCEPT_REASON}: {len(ACCEPTED_SAVE)}"
        )
        for k in ACCEPTED_SAVE:
            print("  - " + k)
    if PARAM_PH:
        print(
            f"PLACEHOLDERS IN NODE SETTINGS ({len(PARAM_PH)}): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):"
        )
        for k in PARAM_PH:
            print("  - " + k)
    if CRED_PH:
        print(
            f"CREDENTIAL IDS STILL PLACEHOLDERS ({len(CRED_PH)}): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):"
        )
        for k in CRED_PH:
            print("  - " + k)
    if ENV_USE:
        print(f"STEPS THAT READ ENVIRONMENT VARIABLES ({len(ENV_USE)}):")
        for k in ENV_USE:
            print("  - " + k)
    if OPTS["ddl"] is None:
        print(
            "SQL COLUMNS NOT CHECKED: no --ddl file was given (the take needs demo/n8n-flows-v4/mf_leads.sql)."
        )
    else:
        print(
            f"SQL columns compared with the --ddl file: {SQL_DONE['checked']} query string(s) read."
        )
        print(
            f"SQL NOT COMPARED: query strings read but not compared (no table name could be read, for example only a {{{{ }}}} expression)={SQL_DONE['uncompared']}; compared query strings whose {{{{ }}}} parts were blanked={SQL_DONE['blanked']}; table-file columns named like an SQL word (never compared)={SQL_DONE['same_as_sql_word']}"
        )
        print(
            f"SQL WARNS: column WARNs={SQL_DONE['col_warn']} table WARNs={SQL_DONE['tbl_warn']} postgres steps with no query text (not compared)={SQL_DONE['no_query']}"
        )
        if SQL_DONE["checked"] == 0:
            print(
                "SQL COLUMNS NOT CHECKED: a --ddl file was given but 0 query strings were read, so NO column was compared (the checker reads only the 'query' setting of postgres steps)."
            )
    print(f"Known open problems: {len(KNOWN)}")
    for k in KNOWN:
        print("  - " + k)
    print(
        "Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); "
        "who calls a web address, whether the flow is active, and test versus production web address; "
        f"expression syntax beyond node names; secrets in a shape this scan does not list; every rule marked '{UNV}' "
        "(webhook authentication values, credential kinds, retry limits, onError values, position of the error output, default responseMode, duplicate method+path or webhookId)."
    )
    print("Passing this check does NOT mean the flows are ready to film.")


HEADER = """# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
"""


SQL_WORDS = {
    "select",
    "insert",
    "into",
    "values",
    "update",
    "set",
    "delete",
    "from",
    "where",
    "and",
    "or",
    "not",
    "in",
    "is",
    "null",
    "like",
    "between",
    "exists",
    "case",
    "when",
    "then",
    "else",
    "end",
    "on",
    "conflict",
    "do",
    "nothing",
    "returning",
    "order",
    "by",
    "group",
    "having",
    "limit",
    "offset",
    "for",
    "skip",
    "locked",
    "as",
    "join",
    "left",
    "right",
    "inner",
    "outer",
    "using",
    "distinct",
    "all",
    "any",
    "true",
    "false",
    "default",
    "asc",
    "desc",
    "union",
    "with",
    "text",
    "int",
    "integer",
    "bigint",
    "boolean",
    "timestamptz",
    "timestamp",
    "interval",
    "uuid",
    "numeric",
    "varchar",
    "date",
    "jsonb",
    "json",
}
TABLE_AFTER = {"from", "update", "into", "join"}
MAIL_SHAPE = re.compile(
    r"[^@\s,;]+@[^@\s,;]+\.[A-Za-z]{2,}"
)  # one plain e-mail address; the shape only, a filled-in wrong address still passes
PH_WORD = re.compile("|".join(re.escape(x) for x in PLACEHOLDERS))  # f8-r11 (M4): only the placeholder word itself is ever printed, never the text around it (it may be a real value)


def parse_ddl(text):
    """CREATE TABLE name( col ..., ...) -> {table: {columns}} (lower case). Comments are dropped; constraint lines are not columns."""
    text = re.sub(r"--[^\n]*", "", text)
    out = {}
    for m in re.finditer(
        r"create\s+table\s+(?:if\s+not\s+exists\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        text,
        re.IGNORECASE,
    ):
        depth, i, part, parts = 1, m.end(), "", []
        while i < len(text) and depth:
            c = text[i]
            depth += (c == "(") - (c == ")")
            if depth == 1 and c == ",":
                parts.append(part)
                part = ""
            elif depth:
                part += c
            i += 1
        parts.append(part)
        cols = set()
        for x in parts:
            w = x.split()
            if w and w[0].lower() not in (
                "primary",
                "unique",
                "check",
                "foreign",
                "constraint",
                "like",
            ):
                cols.add(w[0].strip('"').lower())
        out[m.group(1).lower()] = cols
    return out


def sql_use(query):
    """(tables, words) used by one query text: words = names that are neither SQL words, functions, parameters nor text values."""
    q = re.sub(r"\{\{.*?\}\}", " ", query.lstrip("="), flags=re.DOTALL)
    q = re.sub(r"\$([A-Za-z_]*)\$.*?\$\1\$", " ", q, flags=re.DOTALL)  # f8-r11 (M4): dollar-quoted text ($$...$$, $tag$...$tag$) is a text value, like '...'
    q = re.sub(r"'(?:[^']|'')*'", " ", q)
    q = re.sub(r"--[^\n]*", " ", q)
    q = re.sub(r"\$\d+|::\s*[A-Za-z_][A-Za-z0-9_]*", " ", q)
    toks = list(re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", q))
    tables, words = set(), set()
    prev = ""
    for m in toks:
        w = m.group(0).lower()
        nxt = q[m.end() :].lstrip()[:1]
        if prev in TABLE_AFTER and w not in SQL_WORDS:
            tables.add(w)
        elif w not in SQL_WORDS and nxt != "(":
            words.add(w)
        prev = w
    return tables, words


def sql_check(n, tag):
    """Every column named in a postgres query must exist in the table definition given with --ddl (names are read from the text, not run)."""
    ddl = OPTS["ddl"]
    if ddl is None:
        return
    prm = n.get("parameters")
    qs = [x for k, x in (prm or {}).items() if k == "query" and isinstance(x, str)]
    if not qs:
        SQL_DONE["no_query"] += 1
        warn(
            tag,
            f"node {n['name']}: this postgres step has no query text (table or column mode?), so its columns were NOT compared with the --ddl file",
            known=True,
        )
    for q in qs:
        tables, words = sql_use(q)
        if not tables:
            SQL_DONE["uncompared"] += 1
            warn(
                tag,
                f"node {n['name']}: the query text names no table that could be read (only {{{{ }}}} expressions or no FROM/UPDATE/INTO/JOIN), so its columns were NOT compared with the --ddl file",
                known=True,
            )
            continue
        SQL_DONE["checked"] += 1
        if "{{" in q:
            SQL_DONE["blanked"] += 1
        known = set().union(*[ddl[t] for t in tables if t in ddl]) if tables else set()
        absent = sorted(t for t in tables if t not in ddl)
        miss = sorted(w for w in words if w not in known and w not in tables)
        if absent:
            SQL_DONE["tbl_warn"] += 1
            warn(
                tag,
                f"node {n['name']}: the query uses table(s) {absent} that the --ddl file does not define",
                known=True,
            )
        if miss and not absent:
            SQL_DONE["col_warn"] += 1
            warn(
                tag,
                f"node {n['name']}: the query uses column(s) {miss} that the --ddl file does not define; in n8n this step would fail on every run",
                known=True,
            )


def is_trigger(t):
    return t in TRIGGER_EXACT or t.endswith("Trigger")


def fold_name(name):
    """Node name as compared for duplicates: case-folded, accents and width folded (NFKD without marks), spaces squeezed."""
    t = unicodedata.normalize("NFKD", name.strip())
    t = "".join(c for c in t if unicodedata.category(c)[0] != "M").casefold()
    return re.sub(r"\s+", " ", t)


def mixes_alphabets(name):
    """True when one word holds letters of two alphabets (the first word of each letter's Unicode name: LATIN, CYRILLIC, GREEK, ...)."""
    for w in re.findall(r"[^\W\d_]+", unicodedata.normalize("NFKD", name)):
        if len({unicodedata.name(c, "?").split()[0] for c in w if unicodedata.category(c)[0] == "L"}) > 1:
            return True
    return False


def mail_fields(o):
    """(key, text value) of every setting named in MAIL_KEYS, at any depth of a node's parameters (dicts and lists)."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in MAIL_KEYS and isinstance(v, str):
                yield k, v
            else:
                yield from mail_fields(v)
    elif isinstance(o, list):
        for v in o:
            yield from mail_fields(v)


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


class DupKey(Exception):
    pass


def _no_dups(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise DupKey(min({k for k in keys if keys.count(k) > 1}))
    return dict(pairs)


def load(path, tag):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=_no_dups)
    except DupKey as e:
        fail(
            tag,
            f"parse failure: duplicate JSON key {str(e)!r} (n8n keeps only the last one, so the file says two different things)",
        )
        return None
    except UnicodeDecodeError:
        fail(
            tag,
            "parse failure UnicodeDecodeError: the file is unreadable (it is not valid UTF-8 text)",
        )
        return None
    except (OSError, ValueError, RecursionError) as e:
        fail(tag, f"parse failure {type(e).__name__}: the file is unreadable or not valid JSON")
        return None


def targets_of(outs):
    for typ, lists in (outs or {}).items():
        for idx, lst in enumerate(lists):
            for c in lst or []:
                yield typ, idx, c.get("node")


def shape_ok(d, tag):
    """FAIL (not a traceback) when the JSON is not the n8n shape this checker reads. True = safe to read further."""
    if not isinstance(d, dict):
        fail(tag, "top level is not a JSON object")
        return False
    nodes, conns, ok = d.get("nodes"), d.get("connections", {}), True
    if not isinstance(nodes, list):
        fail(tag, "no nodes list")
        return False
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            fail(tag, f"node at index {i} is not an object")
            ok = False
        elif (
            not isinstance(n.get("name"), str)
            or not n.get("name")
            or not isinstance(n.get("type"), str)
            or not n.get("type")
        ):
            fail(tag, f"node at index {i} lacks a text name or type")
            ok = False
        elif "parameters" in n and not isinstance(n["parameters"], dict):
            fail(tag, "node {}: parameters is not an object".format(n["name"]))
            ok = False
    if "settings" in d and not isinstance(d["settings"], dict):
        fail(tag, "settings is not an object")
        ok = False
    for n in nodes:
        if (
            isinstance(n, dict)
            and n.get("type") in ("n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger")
            and "webhookId" in n
            and not isinstance(n["webhookId"], str)
        ):
            fail(tag, "node {}: webhookId is not text".format(n.get("name")))
            ok = False
    if not isinstance(conns, dict):
        fail(tag, "connections is not an object")
        return False
    for src, outs in conns.items():
        if not isinstance(outs, dict):
            fail(tag, f"connections of {src!r} are not an object")
            ok = False
            continue
        for typ, lists in outs.items():
            if not isinstance(lists, list):
                fail(tag, f"connections of {src!r}: {typ!r} is not a list")
                ok = False
                continue
            for lst in lists:
                if lst is None:
                    continue
                if not isinstance(lst, list):
                    fail(tag, f"connections of {src!r}: an output is not a list")
                    ok = False
                    continue
                for c in lst:
                    if not isinstance(c, dict) or not isinstance(c.get("node"), str):
                        fail(tag, f"connections of {src!r}: a link has no text 'node'")
                        ok = False
    return ok


# ---------------- F8 additions ----------------
ONERROR_OK = {None, "stopWorkflow", "continueRegularOutput", "continueErrorOutput"}
EXTERNAL = ("postgres", "httpRequest", "hubspot", "emailSend", "executeWorkflow")
CRED_KIND = {
    "postgres": ("postgres",),
    "emailSend": ("smtp",),
    "hubspot": ("hubspotAppToken", "hubspotApi", "hubspotOAuth2Api"),
}  # credential kind(s) n8n expects on these node types (n8n rule UNVERIFIED: from memory of n8n)
WEBHOOK_AUTH = {
    "basicAuth": "httpBasicAuth",
    "headerAuth": "httpHeaderAuth",
    "jwtAuth": "jwtAuth",
}  # n8n webhook node: authentication value -> credential kind (none = no credential). n8n rule UNVERIFIED: from memory of n8n
FORM_AUTH = {
    "basicAuth": "httpBasicAuth"
}  # n8n form trigger: only none or basicAuth (n8n rule UNVERIFIED: from memory of n8n)
CRED_TYPES = ("postgres", "emailSend", "hubspot")  # these always need an attached credential
# secret shapes are built from parts so this file holds no secret-looking literal (the one allowed literal is the AWS example key)
AWS_EXAMPLE = "AKIA" + "IOSFODNN7EXAMPLE"
SECRET_RX = [
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("sk- style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key block", re.compile("-----" + "BEGIN [A-Z ]*PRIVATE KEY")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")),
    ("password inside a URL", re.compile(r"://[^/\s:@{}]+:[^/\s:@{}]{3,}@")),
    ("literal Bearer value", re.compile(r"Bearer\s+(?![{$=])[A-Za-z0-9._~+/-]{12,}")),
]
SECRET_KEY_ENDS = (
    "password",
    "passwd",
    "passphrase",
    "pwd",
    "secret",
    "secretkey",
    "token",
    "apikey",
    "authorization",
    "privatekey",
    "accesskey",
    "clientsecret",
    "signingkey",
    "signkey",
    "sharedkey",
    "encryptionkey",
    "sessionkey",
)
SECRET_MIN_LEN = 1  # f8-r11 (M3): a short value (even 3 characters) under a secret-looking key is still a literal secret; only an empty value is skipped
EXPR_BLOCK = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
OK_WORDS = {"bearer", "basic", "token"}


SECRET_LAST_WORDS = ("pass", "pwd", "passwd", "password", "passphrase", "secret", "token", "apikey", "key")


def key_is_secretish(k):
    kk = re.sub(r"[-_\s]", "", str(k)).lower()
    if kk == "pass" or kk.endswith(SECRET_KEY_ENDS):
        return True
    # f8-r11 (M3): the LAST WORD of a camelCase / snake_case key (smtpPass, db_pass, userPwd) names a secret; 'bypass' or 'compass' is one word and stays clean
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", re.sub(r"[-_\s]+", " ", str(k)).replace(" ", "_").replace("_", " "))
    return len(words) > 1 and words[-1].lower() in SECRET_LAST_WORDS[:-1]


def value_is_safe(v):
    """A value is safe only when it is a reference to $env/$credentials/$secrets/$vars/$json/$('..') (alone or after Bearer/Basic) or one of the repo placeholder tokens, exactly."""
    if v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "":
        return True
    body = v.removeprefix("=")
    blocks = EXPR_BLOCK.findall(body)
    if not blocks or not all(
        re.match(r"\s*\$(env|credentials|secrets|vars|json|node|\(|items)", b) for b in blocks
    ):
        return False
    for b in blocks:  # a quoted text of 6+ characters inside the expression (other than a node or variable name in $('..') or [".."]) is a literal value
        b2 = re.sub(
            r"""\$\(\s*['"][^'"]*['"]\s*\)|\[\s*['"][^'"]*['"]\s*\]|\$items\(\s*['"][^'"]*['"]""",
            " ",
            b,
        )
        if re.search(r"""['"`][^'"`]{6,}['"`]""", b2):
            return False
    rest = EXPR_BLOCK.sub(" ", body)
    return all(w.lower() in OK_WORDS for w in re.findall(r"[A-Za-z0-9+/_-]{6,}", rest))


def kv_items(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from kv_items(v, path + "." + str(k))
            if isinstance(v, str):
                yield str(k), v, path + "." + str(k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, dict) and "name" in v and isinstance(v.get("value"), str):
                yield str(v["name"]), v["value"], "{}[{}]".format(path, v["name"])
            yield from kv_items(v, f"{path}[{i}]")


def secret_scan(n, tag):
    hits = []
    for s in strings(n):
        s2 = s.replace(AWS_EXAMPLE, "")
        for label, rx in SECRET_RX:
            if rx.search(s2):
                hits.append(label)
    for k, v, _p in kv_items(n):  # f8-r11 (F3): the credentials block is scanned too (a secret written beside the credential id and name)
        if (
            key_is_secretish(k)
            and len(v) >= SECRET_MIN_LEN
            and not value_is_safe(v)
            and str(k).lower() not in ("authentication", "genericauthtype", "nodecredentialtype")
        ):
            hits.append(f"literal value under key {k!r}")
    for h in sorted(set(hits)):
        fail(
            tag,
            "node {}: secret-looking value ({}); keep secrets in n8n credentials or $env".format(
                n["name"], h
            ),
        )


def secret_scan_top(d, tag):
    """Top-level keys other than nodes/connections (pinData, staticData, meta, name, settings ...)."""
    top = {k: v for k, v in d.items() if k not in ("nodes", "connections")}
    hits = set()
    for s in strings(top):
        for label, rx in SECRET_RX:
            if rx.search(s.replace(AWS_EXAMPLE, "")):
                hits.add(label)
    for k, v, _p in kv_items(top):
        if key_is_secretish(k) and len(v) >= SECRET_MIN_LEN and not value_is_safe(v):
            hits.add(f"literal value under key {k!r}")
    for h in sorted(hits):
        fail(tag, f"top-level data (not a node): secret-looking value ({h})")


ENTRY_FLOWS = (
    "mf-form.json",
    "mf-hook.json",
)  # the two flows that a caller posts to and that must answer through respondToWebhook steps


def webhook_paths(n, nodes, adj, tag):
    """Every path from a responseNode webhook must end in respondToWebhook. Walk is stopped at respond nodes."""
    prm = n.get("parameters") or {}
    mode = prm.get("responseMode", "onReceived")
    if "responseMode" not in prm:
        unv(
            tag,
            f"webhook {n['name']} sets no responseMode: this check assumes n8n answers at once (onReceived), which is from memory of n8n, so the reply path was not checked",
        )
    if "responseMode" in prm and mode != "responseNode" and tag.rsplit("/", 1)[-1] in ENTRY_FLOWS:
        fail(
            tag,
            f"webhook {n['name']} sets responseMode={mode!r} on an entry flow: the take needs the answer sent by a respondToWebhook step (responseNode), so the caller would get an answer from n8n at once and the reply steps would not be used",
        )
    if mode != "responseNode":
        print(
            "  [{}] webhook {} responseMode={} (n8n answers by itself, no respondToWebhook needed)".format(
                tag, n["name"], mode
            )
        )
        return
    byname = {x["name"]: x for x in nodes}
    isresp = lambda x: (
        byname[x]["type"] == "n8n-nodes-base.respondToWebhook"
        and byname[x].get("disabled") is not True
    )  # a disabled reply node sends nothing
    seen, stack, bare = {n["name"]}, [n["name"]], []
    while stack:
        x = stack.pop()
        if isresp(x):
            continue
        nxt = [t for t in adj.get(x, ()) if t in byname]
        if not nxt and x != n["name"]:
            bare.append(x)
        for t in nxt:
            if t not in seen:
                seen.add(t)
                stack.append(t)
    if not nxt_any(n["name"], adj):
        bare.append(n["name"])
    resp = [x for x in seen if isresp(x)]
    if bare:
        fail(
            tag,
            "webhook {} (responseNode): path(s) end WITHOUT respondToWebhook at {}".format(
                n["name"], sorted(bare)
            ),
        )
    if not resp:
        fail(tag, "webhook {} (responseNode): no respondToWebhook reachable".format(n["name"]))
    risky = sorted(
        x
        for x in seen
        if not isresp(x)
        and byname[x]["type"].split(".")[-1] in EXTERNAL + ("code", "function")
        and byname[x].get("disabled") is not True
        and byname[x].get("onError") in (None, "", "stopWorkflow")
    )
    if risky:
        warn(
            tag,
            "webhook {}: REPLY GAP: if {} fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)".format(
                n["name"], risky
            ),
            known=True,
        )
    print(
        f"  [{tag}] webhook {n['name']}: {len(resp)} respondToWebhook node(s) reachable {sorted(resp)}; "
        f"paths without a reply: {sorted(bare) or 'none'}"
    )


def nxt_any(x, adj):
    return bool(adj.get(x))


def extra_checks(d, tag, nodes, adj, trig, sticky):
    byname = {x["name"]: x for x in nodes}
    conns = d.get("connections", {})
    # shape of connections, trigger inputs, sticky notes
    for src, outs in conns.items():
        if not isinstance(outs, dict) or any(
            not isinstance(l, list) or any(l2 is not None and not isinstance(l2, list) for l2 in l)
            for l in outs.values()
        ):
            fail(tag, f"connections of {src!r} are not {{type: [[{{node,type,index}}]]}}")
            continue
        if src in sticky:
            fail(tag, f"sticky note {src!r} has a connection")
        for lists in outs.values():
            for lst in lists:
                for c in lst or []:
                    if (
                        not isinstance(c, dict)
                        or not isinstance(c.get("index"), int)
                        or c.get("index") < 0
                        or not c.get("type")
                    ):
                        fail(
                            tag,
                            "connection {} -> {} lacks a valid type/index".format(
                                src, c.get("node") if isinstance(c, dict) else c
                            ),
                        )
                    elif c.get("node") in trig:
                        fail(
                            tag,
                            "incoming link {} -> {} into a trigger node (a trigger has no input)".format(
                                src, c["node"]
                            ),
                        )
    real = [n for n in nodes if n["type"] != STICKY]
    if sticky:
        print(f"  [{tag}] sticky notes: {len(sticky)} {sorted(sticky)}")
    if not real:
        fail(tag, "sticky-note-only file: no executable node")
    elif not [n for n in real if n["name"] not in trig]:
        fail(tag, "file holds only trigger and sticky notes: nothing to run")
    for n in nodes:
        if n["type"] == STICKY:
            secret_scan(n, tag)
    secret_scan_top(d, tag)
    ids = [n["id"] for n in nodes if "id" in n]
    di = sorted(k for k, v in collections.Counter(ids).items() if v > 1)
    if di:
        fail(tag, f"duplicate node ids {di}")
    norm = collections.defaultdict(set)
    for n in nodes:
        norm[fold_name(n["name"])].add(n["name"])
    near = sorted(k for k, v in norm.items() if len(v) > 1)
    if near:
        fail(tag, f"names that differ only by case, spaces, accents or width {near}")
    for n in nodes:
        if mixes_alphabets(n["name"]):  # f8-r11 (M5): a node name with Latin and Cyrillic/Greek/Armenian letters in ONE word looks like another name
            fail(tag, f"node name {n['name']!r} mixes letters of two alphabets in one word (a look-alike of another name)")
    # per node settings
    noretry, silent, phs, pph = [], [], [], []
    for n in real:
        nm, short = n["name"], n["type"].split(".")[-1]
        pos = n.get("position")
        if not (
            isinstance(pos, list)
            and len(pos) == 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in pos)
        ):
            fail(tag, f"node {nm} lacks position [x, y]")
        if not isinstance(n.get("typeVersion"), (int, float)) or isinstance(
            n.get("typeVersion"), bool
        ):
            fail(tag, f"node {nm} lacks a numeric typeVersion")
        if n.get("onError") not in ONERROR_OK:
            unv(
                tag,
                "node {} onError={!r} is not one of stopWorkflow, continueRegularOutput, continueErrorOutput (value list from memory of the n8n UI, no source in this repo)".format(
                    nm, n.get("onError")
                ),
            )
        if "retryOnFail" in n and not isinstance(n["retryOnFail"], bool):
            fail(tag, "node {} retryOnFail={!r} is not a boolean".format(nm, n["retryOnFail"]))
        if n.get("retryOnFail"):
            mt, wb = n.get("maxTries", 3), n.get("waitBetweenTries", 1000)
            if not isinstance(mt, int) or isinstance(mt, bool) or not 2 <= mt <= 5:
                unv(
                    tag,
                    f"node {nm} maxTries={mt!r} (2 to 5 is the n8n screen limit, not a proven import rule)",
                )
            if not isinstance(wb, int) or isinstance(wb, bool) or not 0 <= wb <= 5000:
                unv(
                    tag,
                    f"node {nm} waitBetweenTries={wb!r} (0 to 5000 ms is the n8n screen limit, not a proven import rule)",
                )
        elif "maxTries" in n or "waitBetweenTries" in n:
            warn(
                tag,
                f"node {nm} sets maxTries/waitBetweenTries but retryOnFail is not true (ignored by n8n)",
            )
        if "alwaysOutputData" in n and not isinstance(n["alwaysOutputData"], bool):
            fail(
                tag,
                "node {} alwaysOutputData={!r} is not a boolean".format(nm, n["alwaysOutputData"]),
            )
        if n.get("alwaysOutputData") is True and n.get("onError") == "continueErrorOutput":
            fail(
                tag,
                f"node {nm} has alwaysOutputData together with continueErrorOutput: a failure may then go down the normal output as an empty result instead of the failure output (work order 017 F8: failures must reach the FAILED line; what n8n really does is NOT proven until a test run in n8n)",
            )
        if n.get("onError") == "continueRegularOutput" and short in EXTERNAL:
            silent.append(nm)
        if short in EXTERNAL and not n.get("retryOnFail"):
            noretry.append(nm)
        if n.get("disabled") is True and short in EXTERNAL:
            fail(
                tag,
                f"node {nm} ({short}) is an external-call node and is disabled: n8n passes data through it and it sends and writes nothing, so the flow would look fine and do no work (round 9, review f8-design-r3 M1)",
            )
        elif n.get("disabled") is True:
            warn(
                tag,
                f"node {nm} is disabled (n8n passes data through it; it sends and writes nothing)",
            )
        # credentials
        cr = n.get("credentials")
        need = short in CRED_TYPES or (
            short == "httpRequest"
            and (n.get("parameters") or {}).get("authentication") not in (None, "none", "")
        )
        if need and (not isinstance(cr, dict) or not cr):
            fail(tag, f"node {nm} ({short}) has no credentials block")
        for k, v in (cr or {}).items():
            if not isinstance(v, dict) or not str(v.get("name") or "").strip():
                fail(tag, f"node {nm} credential {k!r} has no name")
            elif not str(v.get("id") or "").strip():
                fail(
                    tag,
                    "node {} credential {!r} has no id (name {!r})".format(nm, k, v.get("name")),
                )
            elif k in OPTS["cred_names"] and v.get("name") != OPTS["cred_names"][k]:
                fail(
                    tag,
                    "node {} credential {!r} has name {!r}, expected {!r} (--expect-credential)".format(
                        nm, k, v.get("name"), OPTS["cred_names"][k]
                    ),
                )
        if (
            short in CRED_KIND
            and isinstance(cr, dict)
            and cr
            and not set(CRED_KIND[short]) & set(cr)
        ):
            unv(
                tag,
                "node {} ({}) credential kind(s) {} do not include the expected kind {}".format(
                    nm, short, sorted(cr), " or ".join(repr(k) for k in CRED_KIND[short])
                ),
            )
        for k, v in (cr or {}).items():
            idv = str((v or {}).get("id") or "") if isinstance(v, dict) else ""
            if idv and any(p in idv for p in PLACEHOLDERS):
                phw = PH_WORD.search(idv).group(0)  # f8-r11 (M4): the placeholder word only, never the rest of the id
                phs.append(f"{nm} credential {k} id {phw}")
                CRED_PH.append(f"{tag} node {nm} credential {k} id: {phw}")
        wf = (
            (n.get("parameters") or {}).get("workflowId")
            if isinstance(n.get("parameters"), dict)
            else None
        )
        for wv in list(strings(wf)) if wf is not None else []:
            if any(p in wv for p in PLACEHOLDERS):
                phw = PH_WORD.search(wv).group(0)  # f8-r11 (M4)
                phs.append(f"{nm} sub-workflow id {phw}")
                CRED_PH.append(f"{tag} node {nm} sub-workflow id: {phw}")
        secret_scan(n, tag)
        prm_ = n.get("parameters")
        if isinstance(prm_, dict):
            for k_, v_ in prm_.items():
                if k_ != "workflowId":
                    for s_ in strings(v_):
                        for w_ in PH_WORD.findall(s_):
                            PARAM_PH.append(f"{tag} node {nm} setting {k_!r}: {w_}")
                            pph.append(f"{nm} {k_}: {w_}")
            for k_, v_ in mail_fields(prm_):  # f8-r11 (M5): at any depth (parameters.options.ccEmail, replyTo, ...), not only the top level
                if (
                    not v_.startswith("=")
                    and not MAIL_SHAPE.fullmatch(v_.strip())
                    and not PH_WORD.search(v_)
                ):
                    PARAM_PH.append(
                        f"{tag} node {nm} setting {k_!r}: not shaped like an address (the value is never printed)"
                    )
                    pph.append(
                        f"{nm} {k_}: not shaped like an address (the value is never printed)"
                    )
        if short == "postgres":
            sql_check(n, tag)
        envs = sorted({e for s_ in strings(n.get("parameters", {})) for e in ENVTOK.findall(s_)})
        if envs:
            ENV_USE.append(f"{tag} node {nm}: {', '.join(envs)}")
            msg = "node {} reads {}; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: {}) this node stops working".format(
                nm, ", ".join(envs), UNV
            )
            if OPTS["block_env"]:
                fail(tag, msg)
            else:
                LEAD["env"] += 1
                lead(tag, msg + " [run with --block-env-access to make it a FAIL]")
        if n["type"] in ("n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger"):
            isw = n["type"] == "n8n-nodes-base.webhook"
            what = "webhook" if isw else "form trigger"
            table = WEBHOOK_AUTH if isw else FORM_AUTH
            au = (n.get("parameters") or {}).get("authentication", "none")
            if au in ("none", None, ""):
                msg = (
                    f"webhook {nm} has no authentication (anyone who knows the address can post)"
                    if isw
                    else f"form trigger {nm} has no authentication setting (anyone who knows the form address can submit; the n8n parameter name is itself {UNV})"
                )
                LEAD["webhook"] += 1
                if OPTS["webhook_auth"]:
                    fail(tag, msg)
                else:
                    lead(
                        tag,
                        msg
                        + " [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]",
                    )
            elif au not in table:
                unv(
                    tag,
                    "{} {} authentication={!r} is not one n8n accepts here (allowed: none, {})".format(
                        what, nm, au, ", ".join(sorted(table))
                    ),
                )
            elif not isinstance(cr, dict) or not cr:
                unv(
                    tag,
                    f"{what} {nm} says authentication={au!r} but the node has no credentials block (the password is not attached)",
                )
            elif table[au] not in cr:
                unv(
                    tag,
                    f"{what} {nm} authentication={au!r} needs a credential of kind {table[au]!r} but the node has {sorted(cr)}",
                )
            if isw:
                if n.get("disabled") is True:
                    print(f"  [{tag}] webhook {nm} is disabled: no reply check")
                else:
                    webhook_paths(n, nodes, adj, tag)
    if phs:
        msg = (
            f"{len(phs)} id(s) are still placeholders and must be replaced in n8n before import: "
            + "; ".join(sorted(phs))
        )
        if OPTS["real_ids"]:
            fail(tag, msg + " (--require-real-credential-ids)")
        else:
            warn(
                tag,
                msg + " [run with --require-real-credential-ids to make this a FAIL]",
                known=True,
            )
    if pph:
        msg = (
            f"{len(pph)} value(s) in node settings are still placeholders; these must be filled before import: "
            + "; ".join(sorted(set(pph)))
        )
        if OPTS["real_ids"]:
            fail(tag, msg + " (--require-real-credential-ids)")
        else:
            warn(
                tag,
                msg + " [run with --require-real-credential-ids to make this a FAIL]",
                known=True,
            )
    if noretry:
        warn(tag, f"external-call nodes without retryOnFail: {sorted(noretry)}")
    if silent:
        warn(
            tag,
            f"external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): {sorted(silent)}",
        )
    # references: upstream check (a node that is not upstream may not have run when the expression reads it)
    anc = {}
    rev = collections.defaultdict(set)
    for a, ts in adj.items():
        for t in ts:
            rev[t].add(a)

    def ancestors(x):
        if x in anc:
            return anc[x]
        out, st = set(), [x]
        while st:
            for p in rev.get(st.pop(), ()):
                if p not in out:
                    out.add(p)
                    st.append(p)
        anc[x] = out
        return out

    for n in real:
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                if (
                    ref in byname
                    and ref != n["name"]
                    and ref not in ancestors(n["name"])
                    and not (n["type"].endswith("Trigger"))
                ):
                    warn(
                        tag,
                        "node {} reads $('{}') which is not upstream of it (it may not have run)".format(
                            n["name"], ref
                        ),
                    )
                if ref == n["name"]:
                    warn(tag, "node {} reads its own output $('{}')".format(n["name"], ref))
    # a mail/CRM write whose own error, or an earlier external call's error, is swallowed (same idea as system-map M1; write = emailSend, hubspot, or httpRequest with a method other than GET)
    for n in real:
        short = n["type"].split(".")[-1]
        if short in ("emailSend", "hubspot") or (
            short == "httpRequest"
            and str((n.get("parameters") or {}).get("method", "GET")).upper() != "GET"
        ):
            up = sorted(
                x
                for x in ancestors(n["name"])
                if x in byname
                and byname[x]["type"].split(".")[-1] in EXTERNAL
                and byname[x].get("onError") == "continueRegularOutput"
            )
            if n.get("onError") == "continueRegularOutput":
                warn(tag, "write node {} continues on error".format(n["name"]))
            if up:
                warn(
                    tag,
                    "write node {} has upstream external call(s) that continue on error: {}".format(
                        n["name"], up
                    ),
                )
    if OPTS["table"]:
        print(f"  error settings [{tag}]:")
        print(f"    {'node':<18} {'type':<18} {'onError':<22} {'retry':<10} alwaysOutputData")
        for n in nodes:
            retry = (
                f"x{n.get('maxTries', 3)}/{n.get('waitBetweenTries', 1000)}ms"
                if n.get("retryOnFail")
                else "no"
            )
            print(
                f"    {n['name']:<18} {n['type'].split('.')[-1]:<18} "
                f"{n.get('onError') or '(default stop)':<22} {retry:<10} "
                f"{'yes' if n.get('alwaysOutputData') else 'no'}"
            )


def _read_json_or_none(p):
    """The file as parsed JSON, or None when it cannot be read or parsed (load() already reports that as a FAIL)."""
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, RecursionError):
        return None


def _addr(n):
    """The path text of a webhook or form trigger, normalised; None when there is none (a missing or non-text path cannot be compared)."""
    pr = n.get("parameters") if isinstance(n.get("parameters"), dict) else {}
    pth = pr.get("path")
    if not isinstance(pth, str) or not pth.strip().strip("/"):
        return None
    return pth.strip().strip("/").lower()


def cross_file(dr, files, seen):
    """Webhooks and form triggers must not share method+path (form: path) or webhookId. `seen` is kept across ALL folders of one run."""
    for fn in files:
        d = _read_json_or_none(os.path.join(dr, fn))
        if d is None:
            continue
        where = f"{dr}/{fn}"
        for n in (
            d.get("nodes", []) if isinstance(d, dict) and isinstance(d.get("nodes"), list) else []
        ):
            if not isinstance(n, dict) or n.get("type") not in (
                "n8n-nodes-base.webhook",
                "n8n-nodes-base.formTrigger",
            ):
                continue
            isw = n["type"] == "n8n-nodes-base.webhook"
            pr = n.get("parameters") if isinstance(n.get("parameters"), dict) else {}
            pth = _addr(n)
            if not isinstance(n.get("parameters"), dict):
                pass  # a wrong shape is reported by shape_ok
            elif pth is None:
                unv(
                    where,
                    f"{'webhook' if isw else 'form trigger'} {n.get('name')} has no usable path (missing, empty or not text), so a clash of web addresses cannot be checked for it (n8n may use the webhookId instead)",
                )
            else:
                key = (str(pr.get("httpMethod", "GET")).upper(), pth) if isw else ("FORM", pth)
                if key in seen:
                    unv(
                        dr,
                        f"two {'webhooks' if isw else 'form triggers'} share {'method+path' if isw else 'path'} {key}: {seen[key]} and {where}",
                    )
                else:
                    seen[key] = where
            wid = n.get("webhookId")
            if isinstance(wid, str) and wid:
                if ("id", wid) in seen:
                    unv(
                        dr,
                        f"two webhooks share webhookId {wid!r} (webhook or form trigger): {seen[('id', wid)]} and {where}",
                    )
                else:
                    seen[("id", wid)] = where


def check_flow(d, tag, expect, baseline_d):
    if not shape_ok(d, tag):
        return
    nodes = d["nodes"]
    names = [n["name"] for n in nodes]
    nameset = set(names)
    dups = sorted(k for k, v in collections.Counter(names).items() if v > 1)
    if dups:
        fail(tag, f"duplicate names {dups}")
    conns = d.get("connections", {})
    ncon = 0
    adj = collections.defaultdict(set)
    incoming = set()
    for src, outs in conns.items():
        if src not in nameset:
            fail(tag, f"connection source {src!r} is not a node")
        for _typ, _idx, t in targets_of(outs):
            ncon += 1
            if t not in nameset:
                fail(tag, f"dangling target {t!r} from {src!r}")
            else:
                adj[src].add(t)
                incoming.add(t)
    trig_all = [n["name"] for n in nodes if is_trigger(n["type"])]
    trig = [n["name"] for n in nodes if is_trigger(n["type"]) and n.get("disabled") is not True]
    if not trig:
        fail(tag, "no enabled trigger node in file")
    seen, stack = set(trig), list(trig)
    while stack:
        for t in adj[stack.pop()]:
            if t not in seen:
                seen.add(t)
                stack.append(t)
    sticky = {n["name"] for n in nodes if n["type"] == STICKY}
    orphans = sorted(
        n for n in names if n not in incoming and n not in trig_all and n not in sticky
    )
    unreach = sorted(n for n in names if n not in seen and n not in sticky and n not in trig_all)
    if orphans:
        fail(tag, f"orphan nodes (no incoming link, not a trigger) {orphans}")
    if unreach:
        fail(tag, f"unreachable from any trigger {unreach}")
    if expect:
        if "nodes" in expect and len(nodes) != expect["nodes"]:
            fail(tag, f"node count {len(nodes)} != expected {expect['nodes']}")
        if "connections" in expect and ncon != expect["connections"]:
            fail(tag, f"connection count {ncon} != expected {expect['connections']}")
    extra_checks(d, tag, nodes, adj, trig_all, sticky)
    st_ = d.get("settings")
    if isinstance(st_, dict):
        off = [
            k
            for k in ("saveDataSuccessExecution", "saveDataErrorExecution")
            if st_.get(k) == "none"
        ]
        if st_.get("saveManualExecutions") is False:
            off.append("saveManualExecutions")
        fname_ = tag.rsplit("/", 1)[-1]
        trig_types = {n["type"] for n in nodes if is_trigger(n["type"])}
        if off and fname_ in OPTS["accept_nosave"] and trig_types == {SCHEDULE}:
            ACCEPT_SAVE_USED.add(fname_)
            ACCEPTED_SAVE.append(f"{tag}: {off}")
            print(
                f"ACCEPTED: {SAVE_ACCEPT_REASON}: {tag} keeps run-saving settings {off} off on purpose "
                "(the lead says it fires every 30 s, which this check did not read from the file; saved runs would pile up with lead keys and e-mails; the one video makes no recovery claim)"
            )
        elif off:
            if fname_ in OPTS["accept_nosave"]:
                warn(
                    tag,
                    "--accept-no-save names this file but it is not a flow that only has a schedule trigger, so the accept is refused here (only the recovery flow may keep saving off)",
                    known=True,
                )
            warn(
                tag,
                f"this flow's run-saving settings {off} are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened",
                known=True,
            )
    base_nodes = {n.get("name"): n for n in (baseline_d or {}).get("nodes", [])}
    base_conns = (baseline_d or {}).get("connections", {})
    for n in nodes:
        outs = conns.get(n["name"], {}).get("main", [])

        def has(i, outs=outs):
            return i < len(outs) and bool(outs[i])

        # how many normal outputs the node has (None = cannot tell)
        pr = n.get("parameters") or {}
        if n["type"] == "n8n-nodes-base.if":
            normal = 2
        elif n["type"] == "n8n-nodes-base.filter":
            normal = 1
        elif n["type"] == "n8n-nodes-base.switch":
            rules = (
                (pr.get("rules") or {}).get("values") or (pr.get("rules") or {}).get("rules") or []
            )
            normal = (
                len(rules)
                + (1 if (pr.get("options") or {}).get("fallbackOutput") == "extra" else 0)
                or None
            )
        else:
            normal = 1
        if n.get("onError") == "continueErrorOutput":
            if normal is None:
                unv(tag, "node {}: cannot tell which output is its error output".format(n["name"]))
            elif not has(normal):
                unv(
                    tag,
                    f"node {n['name']} has onError=continueErrorOutput but its error output main[{normal}]"
                    " (the last output) is missing or has no target",
                )
        if n["type"] == "n8n-nodes-base.if":
            miss = [i for i in (0, 1) if not has(i)]
            if miss:
                bo = base_conns.get(n["name"], {}).get("main", [])
                base_missing = (
                    n["name"] in base_nodes
                    and [i for i in (0, 1) if not (i < len(bo) and bo[i])] == miss
                )
                accepted = OPTS["accept_if"].get((tag.rsplit("/", 1)[-1], n["name"])) == miss
                text = "IF node {} lacks output(s) {}{} (project rule: every IF branch leads somewhere)".format(
                    n["name"],
                    miss,
                    " (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert)"
                    if accepted
                    else " (baseline already lacks the same)"
                    if base_missing
                    else "",
                )
                if accepted:
                    ACCEPT_USED.add((tag.rsplit("/", 1)[-1], n["name"]))
                    ACCEPTED_IF.append(f"{tag}: IF node {n['name']} output(s) {miss}")
                    warn(tag, text, known=True)
                elif base_missing:
                    warn(tag, text)
                else:
                    fail(tag, text)
        elif n["type"] == "n8n-nodes-base.switch":
            if not normal:
                warn(tag, "switch node {}: cannot tell its output count".format(n["name"]))
            else:
                miss = [i for i in range(normal) if not has(i)]
                if miss:
                    warn(
                        tag,
                        "SWITCH node {} has unwired output(s) {} (legal in n8n, items on them stop silently)".format(
                            n["name"], miss
                        ),
                    )
    for n in nodes:
        if n["type"] == STICKY:
            continue  # note text is prose, not an expression
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                if ref not in nameset:
                    fail(
                        tag,
                        "node {}: expression refers to $('{}') which is not a node of this file".format(
                            n["name"], ref
                        ),
                    )
            if PREV.search(s):
                warn(
                    tag, "node {} uses $prevNode (cannot be resolved statically)".format(n["name"])
                )
            if DYNREF.search(s):
                warn(
                    tag,
                    "node {} reads a node by a computed name (not one plain quoted text); the name cannot be checked".format(
                        n["name"]
                    ),
                )
    return {"nodes": len(nodes), "connections": ncon, "triggers": trig}


def info(d, tag):
    tc = collections.Counter((n.get("type"), n.get("typeVersion")) for n in d.get("nodes", []))
    print("  types:", "; ".join(f"{t} v{v} x{c}" for (t, v), c in sorted(tc.items(), key=str)))
    raw = json.dumps(d)
    where = collections.defaultdict(set)
    for n in d.get("nodes", []):
        s = json.dumps(n)
        for p in PLACEHOLDERS:
            if p in s:
                where[p].add(n.get("name"))
        for e in ENVTOK.findall(s):
            where[e].add(n.get("name"))
    for k in sorted(where):
        print(
            f"  placeholder/env {k:<34} count={len(re.findall(re.escape(k), raw))} nodes={sorted(where[k])}"
        )
    if not where:
        print("  placeholder/env: none")


def creds(d):
    cr = [
        (n.get("name"), k, (v or {}).get("name"), (v or {}).get("id"))
        for n in d.get("nodes", [])
        for k, v in (n.get("credentials") or {}).items()
        if isinstance(v, dict)
    ]
    print(
        "  credentials (node, kind, name, id): "
        + ("; ".join("{} {} {} {}".format(*c) for c in cr) if cr else "none")
    )


def deep_diff(a, b, path=""):
    """Paths (no values) where a and b differ. Lists of dicts that carry 'name' are aligned by name."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = path + "." + k if path else k
            if k not in a:
                out.append(p + " (added)")
            elif k not in b:
                out.append(p + " (removed)")
            else:
                out += deep_diff(a[k], b[k], p)
    elif isinstance(a, list) and isinstance(b, list):
        if all(isinstance(x, dict) and "name" in x for x in a + b) and (a or b):
            da, db = {x["name"]: x for x in a}, {x["name"]: x for x in b}
            for k in sorted(set(da) | set(db)):
                p = f"{path}[{k}]"
                if k not in da:
                    out.append(p + " (added)")
                elif k not in db:
                    out.append(p + " (removed)")
                else:
                    out += deep_diff(da[k], db[k], p)
        elif len(a) != len(b):
            out.append(f"{path} (list length {len(a)} -> {len(b)})")
        else:
            for i, (x, y) in enumerate(zip(a, b, strict=False)):
                out += deep_diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(path)
    return out


def get(d, name):
    return next((n for n in d["nodes"] if n["name"] == name), None)


def patch_checks(d, fname, which, tag):
    form = fname in ("mf-form.json", "mf-hook.json")
    main = lambda nm: d["connections"].get(nm, {}).get("main", [])
    tg = lambda nm, i: sorted(c["node"] for c in (main(nm)[i] if i < len(main(nm)) else []))
    if "F002" in which:
        new = ["KeyOk", "ReplyBadKey", "ReplyStoreFail"]
        if not form:
            for nm in new:
                if get(d, nm):
                    fail(tag, f"F-002 node {nm} must exist only in mf-form and mf-hook")
        else:
            for nm in new:
                if not get(d, nm):
                    fail(tag, f"F-002 node {nm} missing")
            if all(get(d, nm) for nm in new):
                links = [
                    ("Valid", 0, ["KeyOk"]),
                    ("KeyOk", 0, ["Claim"]),
                    ("KeyOk", 1, ["ReplyBadKey"]),
                    ("Claim", 0, ["Claimed"]),
                    ("Claim", 1, ["ReplyStoreFail"]),
                ]
                for s, i, want in links:
                    if tg(s, i) != want:
                        fail(tag, f"F-002 link {s} out{i} -> {tg(s, i)} expected {want}")
                for nm, want in WANT_CONN.items():
                    if d["connections"].get(nm) != want:
                        fail(
                            tag,
                            "F-002 connection structure of {} is {} expected {}".format(
                                nm, json.dumps(d["connections"].get(nm)), json.dumps(want)
                            ),
                        )
                cl = get(d, "Claim")
                if cl.get("onError") != "continueErrorOutput":
                    fail(tag, "Claim onError is {!r}".format(cl.get("onError")))
                print(
                    "  [{}] Claim alwaysOutputData={!r} onError={!r}".format(
                        fname, cl.get("alwaysOutputData"), cl.get("onError")
                    )
                )
                warn(tag, F002_UNPROVEN, known=True)
                conds = get(d, "KeyOk")["parameters"].get("conditions", {}).get("conditions") or []
                print(f"  [{fname}] KeyOk IF condition: {json.dumps(conds)}")
                if (
                    len(conds) != 1
                    or conds[0].get("leftValue") != KEY_COND
                    or conds[0].get("operator")
                    != {"type": "boolean", "operation": "true", "singleValue": True}
                ):
                    fail(
                        tag,
                        f"F-002 KeyOk condition is not the expected string {KEY_COND!r} with boolean-true operator",
                    )
                for nm, code in (("ReplyBadKey", 422), ("ReplyStoreFail", 503)):
                    if get(d, nm)["type"] != "n8n-nodes-base.respondToWebhook":
                        fail(
                            tag,
                            f"F-002 {nm} is of type {get(d, nm)['type']!r}, expected n8n-nodes-base.respondToWebhook (a step of another type sends no answer)",
                        )
                    p = get(d, nm)["parameters"]
                    print(
                        "  [{}] {} status={} body={}".format(
                            fname,
                            nm,
                            p.get("options", {}).get("responseCode"),
                            p.get("responseBody"),
                        )
                    )
                    if p.get("options", {}).get("responseCode") != code:
                        fail(
                            tag,
                            f"F-002 {nm} responseCode is {p.get('options', {}).get('responseCode')!r} expected {code}",
                        )
                if "$('Valid')" not in str(
                    get(d, "ReplyStoreFail")["parameters"].get("responseBody")
                ):
                    fail(tag, "F-002 ReplyStoreFail body lacks the $('Valid') reference")
                lk = [
                    a.get("value")
                    for a in (
                        ((get(d, "Valid") or {}).get("parameters") or {}).get("assignments") or {}
                    ).get("assignments", [])
                    if a.get("name") == "lead_key"
                ]
                print(f"  [{fname}] Valid lead_key assignment: {lk}")
                if len(lk) != 1 or not isinstance(lk[0], str) or not lk[0].strip():
                    fail(
                        tag,
                        f"F-002 Valid must set lead_key exactly once with a non-empty value, found {len(lk)} assignment(s)",
                    )
    if "F008" in which:
        want = "none" if fname == "mf-recovery.json" else "all"
        s = d.get("settings", {})
        for k in ("saveDataSuccessExecution", "saveDataErrorExecution"):
            if s.get(k) != want:
                fail(tag, f"F-008 {k} is {s.get(k)!r} expected {want!r}")
        want_manual = fname != "mf-recovery.json"
        if s.get("saveManualExecutions") is not want_manual:
            fail(
                tag,
                f"F-008 saveManualExecutions is {s.get('saveManualExecutions')!r} expected {want_manual!r}",
            )


ALLOW_NODES = {  # allowed changes by patch: (flow files, node, changed path prefixes or None for added)
    "F002": [
        (("mf-form.json", "mf-hook.json"), "KeyOk", None),
        (("mf-form.json", "mf-hook.json"), "ReplyBadKey", None),
        (("mf-form.json", "mf-hook.json"), "ReplyStoreFail", None),
        (
            ("mf-form.json", "mf-hook.json"),
            "Valid",
            ("parameters.assignments.assignments[lead_key].value",),
        ),
        (("mf-form.json", "mf-hook.json"), "Claim", ("onError", "alwaysOutputData")),
    ]
}
ALLOW_CONN = {"F002": ("Valid", "KeyOk", "Claim")}
ALLOW_SETTINGS = {
    "F008": {
        "mf-form.json": (
            "saveDataSuccessExecution",
            "saveDataErrorExecution",
            "saveManualExecutions",
        ),
        "mf-hook.json": (
            "saveDataSuccessExecution",
            "saveDataErrorExecution",
            "saveManualExecutions",
        ),
        "mf-sub-crm-mail.json": (
            "saveDataSuccessExecution",
            "saveDataErrorExecution",
            "saveManualExecutions",
        ),
    }
}


def node_diff(base, patched, fname, allow, tag, out):
    bn = {n["name"]: n for n in base["nodes"]}
    pn = {n["name"]: n for n in patched["nodes"]}
    allowed = [r for a in allow for r in ALLOW_NODES.get(a, []) if fname in r[0]]
    allow_added = {r[1] for r in allowed if r[2] is None}
    allow_changed = {r[1]: r[2] for r in allowed if r[2] is not None}
    out.append(f"== {tag} ==")
    for nm in sorted(set(pn) - set(bn)):
        out.append("  node ADDED   {} ({} v{})".format(nm, pn[nm]["type"], pn[nm]["typeVersion"]))
        if nm not in allow_added:
            fail(tag, f"unexplained added node {nm}")
    for nm in sorted(set(bn) - set(pn)):
        out.append(f"  node REMOVED {nm}")
        fail(tag, f"unexplained removed node {nm}")
    for nm in sorted(set(bn) & set(pn)):
        ch = deep_diff(bn[nm], pn[nm])
        if ch:
            out.append("  node CHANGED {}: {}".format(nm, ", ".join(ch)))
            pref = allow_changed.get(nm)
            for c in ch:
                if pref is None or c.split(" (")[0] not in pref:
                    fail(tag, f"unexplained change in node {nm} at {c}")
    bc, pc = base.get("connections", {}), patched.get("connections", {})
    for src in sorted(set(bc) | set(pc)):
        if bc.get(src) != pc.get(src):
            out.append(f"  connections CHANGED for source {src}")
            if not any(
                src in ALLOW_CONN.get(a, ()) and fname in ("mf-form.json", "mf-hook.json")
                for a in allow
            ):
                fail(tag, f"unexplained connection change for source {src}")
    bs, ps = base.get("settings", {}), patched.get("settings", {})
    for k in sorted(set(bs) | set(ps)):
        if bs.get(k) != ps.get(k):
            out.append(f"  settings CHANGED {k}: {bs.get(k)!r} -> {ps.get(k)!r}")
            if not any(k in ALLOW_SETTINGS.get(a, {}).get(fname, ()) for a in allow):
                fail(tag, f"unexplained settings change {k}")
    for k in sorted(set(base) | set(patched)):
        if k not in ("nodes", "connections", "settings") and base.get(k) != patched.get(k):
            out.append(f"  top-level key {k} CHANGED")
            fail(tag, f"unexplained top-level change {k}")


def main(argv):
    dirs, expect, files, baseline, pc, diffbase, allow, diffout, quiet = (
        [],
        {},
        FILES_DEFAULT,
        None,
        set(),
        None,
        [],
        None,
        False,
    )
    i = 0
    while i < len(argv):
        a = argv[i]

        def val(a=a):
            nonlocal i
            i += 1
            if i >= len(argv):
                raise IndexError(a)
            return argv[i]

        try:
            if a == "--expect":
                try:
                    k, v = val().split("=", 1)
                    n, c = v.split(":")
                    expect[k] = {"nodes": int(n), "connections": int(c)}
                except ValueError:
                    print("usage error: bad --expect value, want FILE=NODES:CONNS")
                    return 2
            elif a == "--expect-json":
                try:
                    with open(val(), encoding="utf-8") as fh:
                        ej = json.load(fh)
                    if not isinstance(ej, dict):
                        raise TypeError("not an object")
                    expect.update(ej)
                except (OSError, ValueError, TypeError, AttributeError):
                    print("usage error: bad --expect-json file")
                    return 2
            elif a == "--expect-credential":
                try:
                    k, v = val().split("=", 1)
                except ValueError:
                    print(
                        "usage error: bad --expect-credential value, want KIND=NAME (for example postgres=my-credential)"
                    )
                    return 2
                OPTS["cred_names"][k] = v
            elif a == "--files":
                files = val().split(",")  # "all" = every *.json of each DIR
            elif a == "--baseline":
                baseline = val()
            elif a == "--patch-checks":
                pc = {x for x in val().split(",") if x}
            elif a == "--diff-base":
                diffbase = val()
            elif a == "--allow":
                allow = [x for x in val().split(",") if x]
            elif a == "--diff-out":
                diffout = val()
            elif a == "--quiet-info":
                quiet = True
            elif a == "--require-webhook-auth":
                OPTS["webhook_auth"] = True
            elif a == "--table":
                OPTS["table"] = True
            elif a == "--block-env-access":
                OPTS["block_env"] = True
            elif a == "--require-real-credential-ids":
                OPTS["real_ids"] = True
            elif a == "--fail-unverified":
                OPTS["fail_unv"] = True
            elif a == "--ddl":
                try:
                    with open(val(), encoding="utf-8") as fh:
                        OPTS["ddl"] = parse_ddl(fh.read())
                except (OSError, ValueError):
                    print(
                        "usage error: --ddl file cannot be read (missing, or not valid UTF-8 text)"
                    )
                    return 2
                if not OPTS["ddl"]:
                    print("usage error: --ddl file holds no CREATE TABLE definition")
                    return 2
                amb = sorted({c for cols in OPTS["ddl"].values() for c in cols} & SQL_WORDS)
                SQL_DONE["same_as_sql_word"] = len(amb)
                if amb:
                    warn(
                        "sql",
                        f"the --ddl file has column(s) {amb} named like an SQL word: a use of them in a query cannot be told from the SQL word, so they are never compared",
                        known=True,
                    )
            elif a == "--accept-no-save":
                nm_ = val()
                if not nm_.endswith(".json") or "/" in nm_ or "\\" in nm_:
                    print(
                        "usage error: bad --accept-no-save value, want one exact flow file name like mf-recovery.json"
                    )
                    return 2
                OPTS["accept_nosave"].add(nm_)
            elif a == "--accept-if":
                try:
                    fl, rest = val().split("=", 1)
                    nd, outs = rest.rsplit(":", 1)
                    idx = sorted({int(x) for x in outs.split(",")})
                    if not fl or not nd or not set(idx) <= {0, 1}:
                        raise ValueError(rest)
                    OPTS["accept_if"][(fl, nd)] = idx
                except ValueError:
                    print(
                        "usage error: bad --accept-if value, want FILE=NODE:OUT[,OUT] with OUT 0 or 1"
                    )
                    return 2
            elif a.startswith("--"):
                print("usage error: unknown option", a)
                return 2
            else:
                dirs.append(a)
        except IndexError:
            print(f"usage error: option {a} needs a value")
            return 2
        i += 1
    if not dirs:
        print(__doc__)
        return 2
    for k, v in expect.items():
        if files != ["all"] and k not in files:
            print(f"usage error: --expect: unknown file key {k!r} (known: {sorted(files)})")
            return 2
        if not isinstance(v, dict) or set(v) - {"nodes", "connections"}:
            print(f"usage error: --expect: bad entry for {k!r}: {v!r}")
            return 2
    if pc - {"F002", "F008"}:
        print(
            "usage error: unknown --patch-checks name(s) {} (known: F002, F008)".format(
                sorted(pc - {"F002", "F008"})
            )
        )
        return 2
    if set(allow) - {"F002", "F008"}:
        print(
            "usage error: unknown --allow name(s) {} (known: F002, F008)".format(
                sorted(set(allow) - {"F002", "F008"})
            )
        )
        return 2
    if allow and not set(allow) <= pc:
        print(
            "usage error: --allow {} needs --patch-checks to name the same patches (got {})".format(
                ",".join(allow), ",".join(sorted(pc)) or "none"
            )
        )
        return 2
    if files == [""] or not files or any(not f.endswith(".json") for f in files if f != "all"):
        print("usage error: --files wants 'all' or a comma list of *.json names")
        return 2
    diffsum = []
    seen_addr = {}  # web addresses and webhook ids across ALL folders of this run
    print(HEADER, end="")
    for dr in dirs:
        print(f"### {dr}")
        if not os.path.isdir(dr):
            fail(dr, "not a directory")
            continue
        have = sorted(x for x in os.listdir(dr) if x.endswith(".json"))
        dfiles = have if files == ["all"] else files
        if files == ["all"] and not have:
            fail(dr, "--files all: this folder holds no *.json file, so nothing was checked")
            continue
        if have != sorted(dfiles):
            fail(dr, f"file list {have} != expected {sorted(dfiles)}")
            for xf in have:
                if (
                    xf not in dfiles
                ):  # an extra file is not checked as a flow, but say so when it cannot even be read
                    try:
                        with open(os.path.join(dr, xf), encoding="utf-8") as fh:
                            json.load(fh)
                    except (OSError, ValueError, RecursionError) as e:
                        fail(
                            f"{dr}/{xf}",
                            f"extra file is unreadable or not valid JSON ({type(e).__name__}); it is not one of the expected flow files",
                        )
        for fn in dfiles:
            p = os.path.join(dr, fn)
            tag = f"{dr}/{fn}"
            if not os.path.isfile(p):
                if (
                    fn in have
                ):  # a missing file is already a FAIL through the file list above; this is the entry that exists but is no regular file
                    fail(
                        tag,
                        "this listed flow is not a regular file (a folder or a dangling link), so it was NOT checked",
                    )
                continue
            d = load(p, tag)
            if d is None:
                continue
            bd = (
                load(os.path.join(baseline, fn), "baseline/" + fn)
                if baseline and os.path.isfile(os.path.join(baseline, fn))
                else None
            )
            try:
                r = check_flow(d, tag, expect.get(fn), bd)
            except READ_ERRORS as e:
                fail(
                    tag,
                    f"checker could not read this file ({type(e).__name__}: {e}); treat the file as broken",
                )
                continue
            if r:
                st = d.get("settings", {})
                print(
                    f"{fn} nodes={r['nodes']} connections={r['connections']} triggers={r['triggers']} "
                    f"saveDataSuccess={st.get('saveDataSuccessExecution')} saveDataError={st.get('saveDataErrorExecution')} saveManual={st.get('saveManualExecutions')}"
                )
            if not r:
                continue
            try:
                creds(d)
                if not quiet:
                    info(d, tag)
                if pc:
                    patch_checks(d, fn, pc, tag)
                if diffbase:
                    bd2 = load(os.path.join(diffbase, fn), "diff-base/" + fn)
                    if bd2 and shape_ok(bd2, "diff-base/" + fn):
                        node_diff(bd2, d, fn, allow, tag, diffsum)
            except READ_ERRORS as e:
                fail(tag, f"checker could not finish this file ({type(e).__name__}: {e})")
        try:
            cross_file(dr, dfiles, seen_addr)
        except READ_ERRORS as e:
            fail(dr, f"cross-file check could not finish ({type(e).__name__}: {e})")
    if diffbase:
        text = "\n".join(diffsum) + "\n"
        print(text)
        if diffout:
            try:
                with open(diffout, "w", encoding="utf-8") as fh:
                    fh.write(
                        "# node-level diff, unpatched generator output vs patched (paths only, no values)\n"
                        f"# allowed patches: {','.join(allow) or 'none'}\n{text}"
                    )
            except OSError as e:
                print(
                    f"INTERNAL ERROR (exit 3): could not write --diff-out file: {type(e).__name__}"
                )
                return 3
    for fl_, nd_ in sorted(set(OPTS["accept_if"]) - ACCEPT_USED):
        warn(
            "accept-if",
            f"--accept-if {fl_}={nd_} matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)",
            known=True,
        )
    for nm_ in sorted(OPTS["accept_nosave"] - ACCEPT_SAVE_USED):
        warn(
            "accept-no-save",
            f"--accept-no-save {nm_} excused nothing: that flow was not found, or its run-saving settings are not off, or it is not a schedule-only flow, so this decision does nothing (file name wrong, or the settings changed)",
            known=True,
        )
    if OPTS["ddl"] is None:
        warn(
            "sql",
            "no --ddl file was given: the columns used in the SQL queries were NOT compared with any table definition; pass --ddl FILE (the take needs demo/n8n-flows-v4/mf_leads.sql, the table with the alert columns)",
            known=True,
        )
    print(f"RESULT: {len(FAILS)} FAIL, {len(WARNS)} WARN")
    final_block()
    return 1 if FAILS else 0


def entry(argv):
    """main(), but a crash of the checker itself is reported as exit 3 (never as exit 1, which means 'a FAIL about the flows')."""
    try:
        return main(argv)
    except ANY_CRASH as e:  # any other crash is also "the checker broke", never exit 1 (exit 1 means a FAIL about the flows)
        print(f"INTERNAL ERROR (exit 3): the checker itself broke: {type(e).__name__}: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(entry(sys.argv[1:]))
