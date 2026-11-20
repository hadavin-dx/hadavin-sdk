"""Pattern-based redaction for logs, audit and channel text (the runtime redacts the document and every tool result with it before the model sees them).

Copied from WARDEN `src/warden/redaction.py` at PR #206 head 14fc549 (branch `redaction-bank-patterns`,
the WARDEN repository): the full pattern table, including the bank codes (BANKCODE: BSB, sort code, ABA,
CA transit/institution) and accounts (BANKACCT), and the PHONE date guard. Edits: this header,
`RedactionResult.kinds` (the slice 1 callers read the kinds found), and a PHONE guard for compact
14-digit timestamps. Placeholders are `<KIND_n>`.
The WARDEN module notes follow.

Every string is scrubbed before it can reach the model. Patterns FIND values; a final sweep then masks
the other copies of each found value - every copy of a SECRET, every standalone copy of an identifier
(see _sweep). Strings that belong together (one incident's lines, labels, errors) are redacted as ONE
text: a value found in any of them is masked in all of them (redact_many, second review 2026-09-30).
A placeholder written by the sweep can change what a pattern reads (a bank code now stands before an account; a short token
beside a known secret is long enough). So after the first sweep the table runs again over the strings the first pass or sweep
changed, and every later round runs over the strings the previous round changed (by the table or by the sweep), until a round
changes no text: a fixed point with a hard cap (`_SETTLE_ROUNDS`, 4 rounds). A call that is still changing in the last round
(or whose last round flipped `bank_near`, a bank word found only in a folded view, which puts every string back to be read once more)
is refused (RedactionError("NotSettled")), never returned half masked (G7, ORDER 020 MJ-B and fix rounds 3 and 5; see `settle`).

⚠ What this is not (audit A-C-23): nothing here can see a secret NO pattern matches. The patterns are
the control; HIGHENTROPY is their backstop. There is NO second, independent pattern pass on what leaves: the outbound
model gate (`runmap.enforce_map`) replaces the values the run's map already holds (the redactor's own final sweep, with the
gate's held-back values) and runs no pattern at all, so a value no pattern here matched and no map entry holds passes it.
(A re-scan inside redact() used the sweep's own rule and could never fire, so it was removed - second review, 2026-09-30.)
"""

from __future__ import annotations

import functools
import re
import string
import time
import unicodedata
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.guard.textnorm import SPACING_CATEGORIES, fold, fold_view

# Ordered deliberately: the greedy/most-specific patterns run before the narrow ones, otherwise a
# narrow pattern eats part of a broader secret (a UUID inside an ARN, an EMAIL inside a connection
# string) and the broader pattern then fails to match.
#
# ⛔ Every pattern with a capturing group masks group(1) — the SENSITIVE part only — keeping the
# surrounding structure (`password=<SECRET_1>`, `postgres://user:<URLCRED_N>@host`) so the model can
# still reason about the shape. A value that is nothing but placeholders (`api_key=<APIKEY_1>`) is masked
# already and left alone; one that holds a placeholder AND more (`password=<UUID_1>.more`) is masked whole and
# stored restored, so restore() gives it back in one step. Value classes used to stop at `<` instead, and left
# whatever followed a placeholder in clear (eighth review, 2026-10-01).
# A credential command-line flag: any name with `--`; with a single `-` only password/passwd, since
# `-token` or `-secret` is as often a word in a message as a flag.
_CRED_FLAG = (
    r"(?i)(?<![\w-])(?:--(?:[a-z0-9]+-){0,2}"
    r"(?:password|passwd|pass|pwd|secret|token|api-?key|access-key|secret-key|private-key|"
    r"auth-token|access-token)|-(?:password|passwd))(?![\w-])"
)
# Space between a flag and its value: a no-break space (and the other Unicode spaces) as well.
_SP = "[ \t\u00a0\u2000-\u200a\u202f\u205f\u3000]"

# Bank details (owner, 2026-10-28): a number is masked by its SHAPE next to a bank word, never by its checksum -
# a synthetic or mistyped number is masked like a real one.
# Like \b, but a snake_case, kebab-case or camelCase prefix is allowed: `payee_bsb`, `--routing-number`,
# `X-Account-Number`, `payeeBsb`, `bankRoutingNumber` (a lower-case letter, then the keyword starting upper case).
# The bank entries run after UUID, so a UUID ending `-acc123456789` is a placeholder by then.
_NOT_IN_WORD = r"(?:(?<![A-Za-z0-9])|(?-i:(?<=[a-z])(?=[A-Z])))"
# Key to value: a parenthesised qualifier (`Routing Number (ABA):`), Slack/Markdown marks (`*BSB:*`, `_Account:_`,
# a value in backticks), quotes (escaped too, as in JSON logged inside a log line: `\"bsb\":\"062-000\"`), spaces,
# an optional `is`, then `:`, `=`, `=>` or an XML `>` (with marks and an optional `#` after it), `#`, or a spaced
# dash or en dash, more spaces, at most one line break, then up to three quotes or marks.
# Possessive, so a run of spaces before a non-digit is not backtracked through (no quadratic case on a planted line).
_BANK_KV = (
    r"(?:"
    + _SP
    + r"*+\([A-Za-z /]{1,20}\))?[*_~`]*+(?:\\?[\"'])?"
    + _SP
    + r"*+(?:is"
    + _SP
    + r"++)?"
    r"(?:(?:=>|[:=>])[*_~`]*+"
    + _SP
    + r"*+#?|#|[\-–](?="
    + _SP
    + r"))?"
    + _SP
    + r"*+(?:\r?\n"
    + _SP
    + r"*+)?(?:\\?[\"'*_~`]){0,3}+"
)
_BANK_NO = (
    r"(?:[ _\-\xa0]?(?:number|num|nbr|no\.?|#|code))?"  # `number`, `_number`, `No.`, `#`, `code`
)
_BANK_SEP = r"[ \-–\xa0]"  # between digit groups: space, no-break space, hyphen, en dash (not the rarer _SP spaces)
_BANK_END = r"(?![\-–]?\d)(?![A-Za-z0-9_])"  # not part of a longer number or a word
_ACCT_WORD = r"(?:accounts?|acct\.?|acc\.?|a/c)(?:[ _\-\xa0]?(?:number|num\.?|nbr\.?|no\.?|#))?"
# The account: 6-17 digits, contiguous or dashed, or spaced as groups of four (`1234 5678`) or exactly three groups
# of three (`123 456 789`). A free space would take the next number on the line into the account (`12345678 404`).
# Never a date, at its start or inside.
_ACCT_DIGITS = (
    r"(?!\d{4}-\d\d-\d\d)(\d{4}(?:[ \xa0]\d{4}){1,3}|\d{3}(?:[ \xa0]\d{3}){2}"
    r"|\d(?:(?!-\d{4}-\d\d-\d\d)-?\d){5,16})(?![\-–]?\d)(?![A-Za-z0-9_])"
)
# Words that make a nearby account number a bank's, and the placeholders of codes already masked. Strong forms only:
# a bare `routing`, `transit` or `institution` is common in logs (request routing, AWS Transit Gateway) and the
# window is 100 characters wide. The code patterns may take a bare word, because there the digits must follow it.
_BANK_CONTEXT = re.compile(
    r"(?i)<BANKCODE_\d+>"
    r"|"
    + _NOT_IN_WORD
    + r"bank[ _\-\xa0]?accounts?(?![A-Za-z])"  # as the docs list it (CodeRabbit, PR 206)
    r"|" + _NOT_IN_WORD + r"(?:BSB|sort[ _\-\xa0]?code|ABA|RTN)(?![A-Za-z0-9])"
    r"|" + _NOT_IN_WORD + r"(?:routing[ _\-\xa0]?(?:number|num|nbr|no|#|code)"
    r"|transit[ _\-\xa0]?(?:number|num|nbr|no|#)|institution[ _\-\xa0]?(?:number|num|nbr|no|#|code)"
    r"|branch[ _\-\xa0]?(?:number|num|nbr|no|#))"
    r"(?![A-Za-z])"
)
_BANK_WINDOW = 100  # characters before the account keyword and after the number


def _bank_context(m: re.Match[str]) -> bool:
    """`bank account ...`, or a bank word or a masked bank code within _BANK_WINDOW characters of the match."""
    return (
        m.group(0)[:4].lower() == "bank"
        or _BANK_CONTEXT.search(m.string, max(0, m.start() - _BANK_WINDOW), m.end() + _BANK_WINDOW)
        is not None
    )


# A key that names a cookie: `Cookie`, `Set-Cookie`, `X-Auth-Cookie`, `HTTP_COOKIE`, `"http_cookie"`, `cookies`.
_COOKIE_KEY = r"(?i)(?<![A-Za-z])(?:set-)?cookies?[\"'\]]*\s*"
# API key prefixes, one per vendor shape, tried in this order (regex fragments). A new shape is one more entry.
_KEY_PREFIXES = (
    r"sk-ant-",
    r"sk-",
    r"sk_live_",
    r"sk_test_",
    r"rk_live_",
    r"rk_test_",
    r"pk_live_",
    r"github_pat_",
    r"ghp_",
    r"gho_",
    r"ghu_",
    r"ghs_",
    r"ghr_",
    r"AKIA",
    r"ASIA",
    r"xox[baprs]-",
    r"glpat-",
    r"glrt-",
    r"AIza",
    r"npm_",
    r"hf_",
    r"hvs\.",
    r"hvb\.",
    r"xapp-",
)
# An ARN's resource part: letters, digits and the punctuation ARNs use. `;` `,` `=` `(` `)` `?` `&` `#` and quotes
# end it, so a credential glued to an ARN is never swallowed into the identifier (and so into a stored map).
ARN_TAIL = r"[A-Za-z0-9_\-./:*+@]"
# What the redactor FINDS: the same characters, but never through a `key=` that begins a credential. `*`, `+` and `@`
# are legal ARN characters, so `...:function:billing*token=V` is ambiguous; the identifier stops before the key and
# the key=value rule masks V. Over-redaction (an ARN segment that looks like `...token=`) is the accepted price.
_KV_WORD = r"(?:password|passwd|pwd|secret|token|api[_\-]?key|apikey|access[_\-]?key|private[_\-]?key|credential|auth)"
ARN_CHAR = r"(?:(?![\w.\-*+@]{0,40}?" + _KV_WORD + r"[\w.\-]{0,20}=)" + ARN_TAIL + ")"
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # PuTTY FIRST (hadavin-sdk edit): its value runs to the end of the text, so a PuTTY block that starts inside a PEM block must be cut before the PEM
    # pattern shortens the text; the PEM pattern then masks the rest (its unterminated form runs to the end). The other order left the lines after the PEM END in clear.
    # PuTTY: the key lines - at least one character, then up to the Private-MAC line or the end of the text.
    (
        "PRIVKEY",
        re.compile(r"Private-Lines:[ \t]*\d+[ \t]*\r?\n([\s\S](?:(?!\r?\nPrivate-MAC)[\s\S])*)"),
    ),
    # A whole PEM private key block — the highest-value secret that turns up in a misconfig dump.
    # PEM and PGP. A key cut off by a line-length limit has no END line: mask to the end.
    (
        "PRIVKEY",
        re.compile(
            r"-----BEGIN[A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----[\s\S]*?"
            r"(?:-----END[A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|\Z)"
        ),
    ),
    # Account-less (`arn:aws:s3:::bucket`) and other partitions (`aws-cn`, `aws-us-gov`) too (lock-in audit row 14).
    ("ARN", re.compile(r"arn:aws[a-z-]*:[a-z0-9\-]*:[a-z0-9\-]*:(?:\d{12})?:" + ARN_CHAR + r"+")),
    # The other clouds' resource ids name the client's project or subscription the same way (audit row 14).
    (
        "GCPRESOURCE",
        re.compile(r"\bprojects/(?:[a-z][a-z0-9-]{4,28}[a-z0-9]|\d{6,20})(?:/" + ARN_CHAR + r"+)?"),
    ),
    (
        "AZURERESOURCE",
        re.compile(
            r"/subscriptions/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            r"(?:/" + ARN_CHAR + r"+)?"
        ),
    ),
    # Three segments (a JWS) to five (a JWE, whose second may be empty): a JWE's last two parts were left in clear
    # (eighth review, 2026-10-01).
    (
        "JWT",
        re.compile(
            r"eyJ[A-Za-z0-9_\-]{1,4096}\.[A-Za-z0-9_\-]{0,4096}\.[A-Za-z0-9_\-]{1,4096}(?:\.[A-Za-z0-9_\-]{0,4096}){0,2}"
        ),
    ),
    # Vendor key prefixes: OpenAI/Anthropic (sk-), GitHub classic (ghp_/gho_/ghu_/ghs_/ghr_) and
    # fine-grained (github_pat_), AWS permanent (AKIA) and STS temporary (ASIA) access-key ids,
    # Slack (xoxb-/...), GitLab (glpat-), Google (AIza), Stripe (sk_live_/pk_live_), npm (npm_).
    # AKIA/ASIA share one shape (prefix + 16 base32); ASIA is the temporary sibling that travels
    # with a session token in AssumeRole/SSO bundles and appears bare in botocore errors.
    ("APIKEY", re.compile(r"\b(?:" + "|".join(_KEY_PREFIXES) + r")[A-Za-z0-9_\-]{8,}\b")),
    # 2026-09-27 audit: shapes that passed unredacted. SendGrid keys carry dots.
    ("APIKEY", re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}")),
    (
        "APIKEY",
        re.compile(r"\bwhsec_[A-Za-z0-9+/=_\-]{8,}"),
    ),  # Stripe webhook secrets carry + and /
    # Legacy Vault tokens: s. (service), b. (batch), r. (recovery), with a digit somewhere.
    ("APIKEY", re.compile(r"\b[sbr]\.(?=[A-Za-z]*\d)[A-Za-z0-9]{16,}\b")),
    # GCP OAuth2 access token (ya29.<long>). Masked whole and BEFORE the phone pattern, which would
    # otherwise fragment a digit-run inside it and leave the rest exposed. Cloud-neutral: GCP.
    ("GCPTOKEN", re.compile(r"\bya29\.[A-Za-z0-9._\-]{20,}")),
    # Azure Shared Access Signature: the `sig=` query parameter is the credential. Cloud-neutral: Azure.
    ("AZURESAS", re.compile(r"(?i)(?<![\w.\-])sig=([^\s&\"']{16,})")),
    # Incoming-webhook URLs carry the credential in the PATH (no key=value, no vendor prefix) — the
    # whole URL IS the secret (anyone holding it can post). Slack, Discord, MS Teams. Cloud-neutral.
    (
        "WEBHOOK",
        re.compile(
            r"(?i)https://(?:"
            r"hooks\.slack\.com/services/[A-Za-z0-9/]+"
            r"|(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]+"
            r"|[a-z0-9.\-]+\.webhook\.office\.com/webhookb2/[A-Za-z0-9@/\-]+"
            r")"
        ),
    ),
    # Credentials embedded in a URL / connection string: scheme://user:<PASSWORD>@host. Masks the
    # password (group 1). A literal `@` inside a password is only partially covered (rare — real
    # passwords are URL-encoded), and the SECRET pattern below is the backstop for `password=` forms.
    # The password runs to the LAST "@" before the host: `admin:p@ss@db` used to mask only "p" and
    # leave "ss@db" to be read as an e-mail address (revealable in Slack).
    (
        "URLCRED",
        re.compile(
            r"(?i)\b[a-z][a-z0-9+.\-]{0,31}://[^\s:/@]{0,128}:([^\s]{2,1024}?)@(?=[a-z0-9.\-]+(?::\d+)?(?:[/?#\s]|$))"
        ),
    ),
    # `@` OR its URL-encoding `%40` — a URL-encoded email (normal in HTTP access logs, the exact
    # evidence source) reads as the email to both the model and an operator, so it must be masked too.
    # Bounded (RFC 5321: local part 64, domain 255): an unbounded run is quadratic on `a.a.a.` text.
    # The address ends where its top-level domain's letters end, whatever follows (ORDER 016c): a digit or `_` glued
    # behind it (`anna.m@example.org9`, `...org_x`) used to stop the match altogether (the pattern ended in a word
    # boundary), so the whole address was shown, to the model and on the card. The glued character stays in the text.
    (
        "EMAIL",
        re.compile(
            r"(?<![A-Za-z0-9._+\-])[A-Za-z0-9._+\-]{1,254}(?:@|%40)[A-Za-z0-9.\-]{1,255}\.[A-Za-z]{2,}(?![A-Za-z])"
        ),
    ),
    # IBAN (ISO 13616): a REAL country code + 2 check digits + 11-30 alnum BBAN. Financial PII in
    # payment/refund incident logs (SEPA charge/transfer). Masked WHOLE and BEFORE ACCOUNTID/PHONE,
    # which would otherwise fragment its digit runs and leak the country+bank prefix. The prefix is
    # restricted to the SWIFT IBAN-registry country set (not any two letters) so an uppercase
    # evidence token like `AB12CDEF...` is NOT clobbered — only a genuine IBAN country prefix fires.
    (
        "IBAN",
        re.compile(
            r"\b(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
            r"|GI|GL|GR|GT|HN|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|LY|MC|MD|ME|MK|MN|MR|MT"
            r"|MU|NI|NL|NO|PK|PL|PS|PT|QA|RO|RS|RU|SA|SC|SD|SE|SI|SK|SM|SO|ST|SV|TL|TN|TR|UA|VA|VG|XK)"
            r"\d{2}[A-Za-z0-9]{11,30}\b"
        ),
    ),
    (
        "UUID",
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
        ),
    ),
    # Bank details (owner, 2026-10-28): masked by shape beside their keyword, never by checksum. After UUID (a UUID
    # can end `-aba123456789`) and before ACCOUNTID, SSN, CREDITCARD and PHONE. Codes first: a masked code is the
    # context the account pattern below looks for (_bank_context).
    (
        "BANKCODE",
        re.compile(
            r"(?i)"
            + _NOT_IN_WORD
            + r"BSB"
            + _BANK_NO
            + _BANK_KV
            + r"(\d{3}"
            + _BANK_SEP
            + r"?\d{3})"
            + _BANK_END
        ),
    ),
    (
        "BANKCODE",
        re.compile(
            r"(?i)"
            + _NOT_IN_WORD
            + r"sort[ _\-\xa0]?code"
            + _BANK_NO
            + _BANK_KV
            + r"(\d{2}"
            + _BANK_SEP
            + r"?\d{2}"
            + _BANK_SEP
            + r"?\d{2})"
            + _BANK_END
        ),
    ),
    (
        "BANKCODE",
        re.compile(
            r"(?i)"
            + _NOT_IN_WORD
            + r"(?:ABA|RTN|routing)(?:[ _\-]?[/&]?[ ]?transit)?"
            + _BANK_NO
            + _BANK_KV
            + r"(\d{9}|\d{3}"
            + _BANK_SEP
            + r"\d{3}"
            + _BANK_SEP
            + r"\d{3})"
            + _BANK_END
        ),
    ),
    (
        "BANKCODE",
        re.compile(
            r"(?i)"
            + _NOT_IN_WORD
            + r"(?:transit(?:[ \t]*+/[ \t]*+institution)?"
            + _BANK_NO
            + r"|branch[ _\-]?(?:number|num|nbr|no\.?|#))"
            + _BANK_KV
            + r"(\d{5}(?:"
            + _BANK_SEP
            + r"\d{3})?|0\d{8})"
            + _BANK_END
        ),
    ),
    (
        "BANKCODE",
        re.compile(
            r"(?i)" + _NOT_IN_WORD + r"institution" + _BANK_NO + _BANK_KV + r"(\d{3})" + _BANK_END
        ),
    ),
    # The account number: kept unless there is bank context (_mask: _bank_context, or bank_near in redact_many).
    (
        "BANKACCT",
        re.compile(
            r"(?i)" + _NOT_IN_WORD + r"(?:bank[ _\-]?)?" + _ACCT_WORD + _BANK_KV + _ACCT_DIGITS
        ),
    ),
    # The account written straight after its code, with no account keyword: `BSB 062-000 12345678`.
    (
        "BANKACCT",
        re.compile(
            r"<BANKCODE_\d+>[*_~`\"']{0,3}+"
            + _SP
            + r"*+[,;/|\-–]?"
            + _SP
            + r"*+[*_~`\"']{0,3}+"
            + _ACCT_DIGITS
        ),
    ),
    # A bare 12-digit id: an AWS account id, a GCP project number, or any 12-digit account id. The
    # label is cloud-NEUTRAL (was AWSACCT, which mislabelled a GCP project number as an AWS account
    # id on a non-AWS deployment) since WARDEN runs on any cloud.
    ("ACCOUNTID", re.compile(r"\b\d{12}\b")),
    # An EC2 private DNS name carries the address with dashes: ip-10-0-3-22(.region.compute.internal).
    ("IPV4", re.compile(r"\b(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})\b")),
    ("IPV4", re.compile(r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),  # k8s pod DNS
    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    # IPv6 — we redact IPv4, so an IPv6 address (common in dual-stack k8s pod logs) is the same
    # identifier and must be masked too. Deliberately matches ONLY real addresses: either a `::`
    # compression or a full 8 groups, so a `10:02:11` timestamp is left alone. (A MAC has its own
    # pattern below — it is a device re-identifier, so it IS masked, just not as an IPv6.)
    (
        "IPV6",
        re.compile(
            r"(?<![:.\w])(?:"
            r"(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}"
            r"|(?:[A-Fa-f0-9]{1,4}:){1,7}:(?:[A-Fa-f0-9]{1,4})?(?::[A-Fa-f0-9]{1,4}){0,6}"
            r")(?![:.\w])"
        ),
    ),
    # MAC address (colon, dash, or Cisco dotted) — a persistent device re-identifier, like an IP.
    # Six pairs, so a 3-group `10:02:11` time does not match.
    (
        "MAC",
        re.compile(
            r"(?:\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b"
            r"|\b[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\b)"
        ),
    ),
    # An internal host name (owner, 2026-10-21): a name under a private suffix - a company's own `.corp`, `.lan`,
    # `.intranet`, `.internal` (outside AWS's own `compute.internal`/`ec2.internal`, whose address part is masked above),
    # `.local`, `home.arpa`. A Kubernetes service's `.cluster.local` name is a resource WARDEN reads and acts on, kept
    # (_find skips it), as are AWS's generic suffixes.
    # `.internal` and `.local` only when the name does not go on into another dotted label or a call:
    # `jdk.internal.reflect`, `kotlin.internal.X` and `threading.local()` are code in a stack trace, the evidence
    # itself. Every other private suffix is a host whatever follows: `billing-db.prod.corp.example` (review, PR 130).
    (
        "HOSTNAME",
        re.compile(
            r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.){1,8}"
            r"(?:(?:internal|local)\b(?!\.\w|\()|(?:corp|lan|intranet|intra|localdomain|home\.arpa)\b)"
        ),
    ),
    # tenant_id=..., org_id: ..., "customer_id": "..."  — the identifiers that make logs re-identifiable
    (
        "TENANT",
        re.compile(
            r"(?i)\b(?:tenant|org|organisation|organization|customer|account|user)[_\-]?id\b[\"']?\s*[:=]\s*[\"']?([a-z0-9_\-]{3,})[\"']?"
        ),
    ),
    # A token following `Bearer ` in an Authorization header (when it is not already a JWT/API key).
    # `<>` too: a value whose start an earlier pattern masked (`Bearer <UUID_1>.rest`) is masked whole (ninth review).
    ("BEARER", re.compile(r"(?i)\bbearer\s+([a-z0-9._~+/\-<>]{12,}=*)")),
    # HTTP Basic auth: `Authorization: Basic <base64 of user:pass>` - the base64 IS the credential.
    ("BASIC", re.compile(r"(?i)\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})")),
    # National ids (owner, 2026-10-21), before CREDITCARD and PHONE, which would take their digits in part: a US Social
    # Security number (never 000, 666 or 9xx first, never 00 or 0000 in the other groups) and an Indian Aadhaar number
    # written in its 4-4-4 groups (it never starts 0 or 1; a contiguous one is ACCOUNTID's 12 digits already).
    ("SSN", re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")),
    # Not the last twelve digits of a longer grouped number: `4242 4242 4242 4242` is a card, masked whole below
    # (review, PR 130: AADHAAR took its last three groups and left the first in clear).
    ("AADHAAR", re.compile(r"(?<!\d[ \-])\b[2-9]\d{3}[ \-]\d{4}[ \-]\d{4}\b(?![ \-]\d)")),
    # An Indian PAN: five letters - the fourth names the holder's kind (P a person, C a company, ...) - four digits, a
    # letter. Upper case only, as it is issued.
    ("PAN", re.compile(r"\b[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z]\b")),
    # A street address: a house number, one to four capitalised words and a street word (English and Indian forms).
    (
        "ADDRESS",
        re.compile(
            r"\b\d{1,5}[a-zA-Z]?,?(?: [A-Z][A-Za-z]+){1,4} (?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
            r"Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl|Terrace|Highway|Hwy|Marg|Nagar|Colony)\b\.?"
        ),
    ),
    # A person's name where a pattern can see one (owner, 2026-10-21) - after a name field's key, a title or a
    # greeting. Honest limit: a name in free prose with no such marker is NOT found; no pattern can tell it from a
    # word (docs/DATA-EGRESS.md).
    (
        "NAME",
        re.compile(
            r"(?i)\b(?:full|first|last|given|family|middle|sur|display|customer|holder|cardholder|contact|"
            r"recipient|patient|employee|person)[_\- ]?name\b[\"']?\s*[:=]\s*[\"']?"
            r"([a-z][a-z.'\-]*(?: [a-z][a-z.'\-]*){0,3})"
        ),
    ),
    (
        "NAME",
        re.compile(
            r"(?i)\b(?:user[_\-]?name|login[_\-]?name)\b[\"']?\s*[:=]\s*[\"']?([\w.\-]{2,64})"
        ),
    ),
    (
        "NAME",
        re.compile(
            r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Shri|Smt|Sri)\.? ([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})"
        ),
    ),
    ("NAME", re.compile(r"\bDear ([A-Z][a-z]+(?: [A-Z][a-z]+)?)")),
    # A grouped payment-card number (4-4-4-4 with space or dash separators). Masked WHOLE and BEFORE
    # PHONE, which otherwise catches only the first 12-14 digits and leaks the final group. A
    # contiguous 16-digit card is already caught by PHONE; this closes the spaced/dashed form.
    ("CREDITCARD", re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")),
    # The negative lookahead stops an ISO-8601 date (YYYY-MM-DD, which every log line starts with)
    # being masked as a phone number — that was masking timestamps and losing evidence.
    #
    # ⛔ Two more guards, added 2026-09-25 after reports reached Slack reading
    # `node=ip-<PHONE_1>-08-21T14:12:03Z` and `wave<PHONE_1>T115746Z`:
    #   - the separator class is `[ \-]`, not `\s` - `\s` matched the NEWLINE between two log lines,
    #     so one "phone number" swallowed the end of one line and the timestamp of the next;
    #   - it may not start inside an identifier: not after a letter, digit, `_`, `-` or `.`. The
    #     digits in `ip-10-0-3-22`, `orders-db-ro-1` and `wave2-2026-...` are names, not numbers.
    # A phone number written as a phone number (`+1 415-555-0132`, `phone=4155550132`) still starts
    # at a boundary and is still masked; so is a contiguous card number, which relies on this rule.
    #   - nor may it END inside one: digits followed by a letter or `_` are the start of a name - a SHA-256 in
    #     a report or a plan hash beginning `3851007894...` was withheld as a phone number (CI, 2026-10-02).
    #   - nor may it run INTO a date: `task 4471 2026-09-11T18:09:10Z` lost its number and half its timestamp to
    #     `<PHONE_1>-11T18:09:10Z` (the 30 recorded incidents, read 2026-10-11). A phone number before a date is still
    #     masked, up to the date.
    #   - (hadavin-sdk edit) nor may it be a compact timestamp `YYYYMMDDhhmmss` (`20261030123456`): 14 digits
    #     with a valid month, day and time. Narrow on purpose: a phone written with `+` or of another length is
    #     still masked.
    (
        "PHONE",
        re.compile(
            r"(?<![\w.\-])(?!\d{4}-\d\d-\d\d)"
            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
            r"\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![\w.])"
        ),
    ),
    # password=..., secret: ..., aws_secret_access_key="...": the value after a credential-ish key.
    # Runs LAST: a value already masked whole is left alone. The bounded [\w.\-] prefix/suffix lets the sensitive word sit INSIDE a
    # compound key (`aws_secret_access_key`, `db_password`), which a `\b`-anchored form missed — the
    # AWS secret access key (the credential paired with the AKIA id) is the case that exposed it.
    # Keywords are cloud-neutral: AWS (aws_secret_access_key), Azure (AccountKey, SharedAccessKey),
    # GCP and generic (private_key, client_secret, api_key, password, token, credential).
    # Header values and client flags that carry a credential whole (2026-09-27 audit).
    (
        "SECRET",
        re.compile(r"(?i)\bauthorization[\"']?\s*[:=]\s*[\"']?(?:[a-z]+\s+)?([^\s\"']{8,})"),
    ),
    # The whole cookie value: it may hold placeholders already placed (they are stored restored, see find()).
    # Stopping at `<` left every cookie after a masked one in clear (seventh review, 2026-10-01). Any key ending
    # in cookie (`X-Auth-Cookie`, `HTTP_COOKIE`, `"http_cookie"`), then `:`, `=` or `=>`, then the value as it is
    # written: quoted (escapes kept), a list (Go's `Cookie:[...]`, every item of a Set-Cookie list), a dict, a
    # header to the end of the line, or an assignment (`cookie=sid=...; b=...`, a logfmt `cookie=x` value only)
    # - eighth and ninth reviews: a lookahead and a `\w-` boundary let Go's form and prefixed keys through.
    # A header value that is a placeholder followed by prose is a report quoting a masked cookie, not a cookie.
    (
        "SECRET",
        re.compile(
            _COOKIE_KEY
            + r"(?:=>|[:=])\s*+(?:\"((?:\\.|[^\"\\\r\n]){4,})\"|'((?:\\.|[^'\\\r\n]){4,})'"
            r"|\[([^\]\r\n]{4,})\]|\{([^}\r\n]{4,})\})"
        ),
    ),
    (
        "SECRET",
        re.compile(_COOKIE_KEY + r":\s*+(?!<[A-Z][A-Z0-9]*_\d+>(?:\s|$))[\"']?([^\r\n\"'`\]]{4,})"),
    ),
    (
        "SECRET",
        re.compile(_COOKIE_KEY + r"(?:=>|=(?!>))\s*+([^\s;,\"'\[{]+(?:;\s*[^\s;=]+=[^\s;]*)*)"),
    ),
    # A HAR entry (`{"name": "Cookie", "value": "..."}`), curl's `--cookie`/`-b`, and a cookie jar's repr.
    (
        "SECRET",
        re.compile(
            r"(?i)\"name\"\s*:\s*\"(?:set-)?cookie\"\s*,\s*\"value\"\s*:\s*\"((?:\\.|[^\"\\\r\n]){4,})\""
        ),
    ),
    (
        "SECRET",
        re.compile(
            r"(?<![\w-])(?:--cookie|-b)(?:\s+|=)(?:\"([^\"\r\n]{4,})\"|'([^'\r\n]{4,})'|([^\s\"'-][^\s\"']{3,}))"
        ),
    ),
    ("SECRET", re.compile(r"<Cookie\s+([^\s=<>]+=[^\s<>]{4,})")),
    (
        "SECRET",
        re.compile(r"\b(?:mysql|mariadb)(?:-?dump|-?admin)?\b[^\r\n]{0,1024}?\s-p([^\s\"']{3,})"),
    ),
    # A credential passed as a command-line flag. EXACT flag names (independent review 2026-09-28:
    # `--secret-name`, `--token-file`, `--token-ttl` are not credentials, and masking them removed
    # resource names from the evidence). Same line only; a value never starts with `-` or a quote.
    # `=` or whitespace before the opening quote: in JSON argv `"--password","x"` the quote right
    # after the flag is the flag's own closing quote, not the value's opening one.
    ("SECRET", re.compile(_CRED_FLAG + rf"(?:{_SP}*={_SP}*|{_SP}+)\"([^\"\n][^\"\n]{{0,255}})\"")),
    ("SECRET", re.compile(_CRED_FLAG + rf"(?:{_SP}*={_SP}*|{_SP}+)'([^'\n][^'\n]{{0,255}})'")),
    # `docker build --secret id=npmrc,src=.npmrc` names a secret; it is not one.
    (
        "SECRET",
        re.compile(_CRED_FLAG + rf"(?:=|{_SP}+(?![A-Za-z_][\w.-]*=))(?![-\"'])([^\s\"']{{3,}})"),
    ),
    (
        "SECRET",
        re.compile(
            r"(?i)\"--?(?:[a-z0-9]+-){0,2}(?:password|passwd|pass|pwd|api-?key|apikey|token|secret)"
            r"\"\s*,\s*\"([^\"]{1,256})\""
        ),
    ),
    # Client tools whose short flag carries the password (same line only).
    ("SECRET", re.compile(r"\bredis-cli\b[^\r\n]{0,1024}?[ \t]-a[ \t]+([^\s\"']{3,})")),
    ("SECRET", re.compile(r"\bsshpass[ \t]+-p[ \t]*([^\s\"']{3,})")),
    (
        "SECRET",
        re.compile(
            r"\b(?:docker[ \t]+login|mongo(?:sh)?|az[ \t]+login)\b[^\r\n]{0,1024}?[ \t]-p[ \t]+([^\s\"']{3,})"
        ),
    ),
    ("SECRET", re.compile(r"\bsqlcmd\b[^\r\n]{0,1024}?[ \t]-P[ \t]*([^\s\"']{3,})")),
    ("SECRET", re.compile(r"\bldap\w*\b[^\r\n]{0,1024}?[ \t]-w[ \t]+([^\s\"']{3,})")),
    # `-[^\Wb]*b`: the flags up to their first b, one way only - `-\w*b\w*` split a long flag word every way it could
    # (Sonar python:S8786, 2026-10-16).
    (
        "SECRET",
        re.compile(
            r"\bhtpasswd\b[^\r\n]{0,1024}?[ \t]-[^\Wb]*b\w*[ \t]+\S+[ \t]+\S+[ \t]+([^\s\"']{3,})"
        ),
    ),
    (
        "SECRET",
        re.compile(
            r"\bcurl\b[^\r\n]{0,1024}?[ \t](?:-u[ \t]*|--user(?:=|[ \t]+))[^:\s]+:([^\s\"']{3,})"
        ),
    ),
    ("SECRET", re.compile(r"(?i)\"auth\"\s*:\s*\"([^\"]{8,})\"")),
    # A quoted secret value is masked WHOLE: `password='hunter 2 x'` used to leak "2 x".
    (
        "SECRET",
        re.compile(
            r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""
        ),
    ),
    (
        "SECRET",
        re.compile(
            r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
            r"[\w.\-]{0,20}[\"']?\s*[:=]\s*'([^'][^']{0,255})'"
        ),
    ),
    (
        "SECRET",
        re.compile(
            # Leading delimiter includes ? & : so URL QUERY-PARAM credentials (?password=, &token=) and
            # the .npmrc form (//registry/:_authToken=) are caught — ubiquitous in access/CI logs.
            # The key starts where the previous character is not a key character (any separator, ASCII or
            # Unicode): an allowlist of key characters, not a list of delimiters (K5 review rounds 1-3).
            r"(?i)(?<![\w.\-?&])(?<!&amp;)[\w.\-]*"
            r"(?:password|passwd|pwd|secret|access[_\-]?key|account[_\-]?key|shared[_\-]?access[_\-]?key"
            r"|private[_\-]?key|api[_\-]?key|apikey|auth[_\-]?token|access[_\-]?token|sas[_\-]?token"
            # kubeconfig secrets: client-key-data (the private key), certificate-data.
            r"|key[_\-]?data|cert(?:ificate)?[_\-]?data"
            # session cookies are live bearer credentials: sessionid, JSESSIONID, PHPSESSID, connect.sid.
            r"|session[_\-]?id|jsessionid|phpsessid|sessid|connect\.sid"
            r"|client[_\-]?secret|credential|token|pass(?=[\"']?\s*[:=])|auth(?=[\"']?\s*[:=])"
            r"|session(?=[\"']?\s*[:=]))[\w.\-]{0,20}"
            # optional closing quote after the key so a JSON credential ("password": "x") is matched too
            r"[\"']?\s*[:=]\s*[\"']?"
            # The value: any non-separator char, OR a comma that does NOT begin a new key=value pair
            # (so a comma-bearing secret is masked WHOLE, but `k=v,k2=v2` is not gobbled).
            # Plain form: `&` is part of the value. Query form (key right after `?`, `&` or `&amp;`): `&` ends the value only
            # before a `name=value` segment, as in application/x-www-form-urlencoded. `&amp;` is one character of the value
            # in both: the approval gate writes `&name;` as `&amp;name;` before redaction.
            # The key prefix is unbounded (P1d-a): a bound let a key behind 41 or more name characters show its value.
            # A numeric HTML entity (`&#59;`, `&amp;#59;` once escaped, `&#x3b;`) is ONE character of the value, not the `&` of a query separator.
            r"((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|&amp;|[^\s\"';,]|,(?!\s*[\w.\-]+\s*[:=]))+)"
        ),
    ),
    (
        "SECRET",
        re.compile(
            r"(?i)(?:(?<=[?&])|(?<=&amp;))[\w.\-]*"
            r"(?:password|passwd|pwd|secret|access[_\-]?key|account[_\-]?key|shared[_\-]?access[_\-]?key"
            r"|private[_\-]?key|api[_\-]?key|apikey|auth[_\-]?token|access[_\-]?token|sas[_\-]?token"
            # kubeconfig secrets: client-key-data (the private key), certificate-data.
            r"|key[_\-]?data|cert(?:ificate)?[_\-]?data"
            # session cookies are live bearer credentials: sessionid, JSESSIONID, PHPSESSID, connect.sid.
            r"|session[_\-]?id|jsessionid|phpsessid|sessid|connect\.sid"
            r"|client[_\-]?secret|credential|token|pass(?=[\"']?\s*[:=])|auth(?=[\"']?\s*[:=])"
            r"|session(?=[\"']?\s*[:=]))[\w.\-]{0,20}"
            # optional closing quote after the key so a JSON credential ("password": "x") is matched too
            r"[\"']?\s*[:=]\s*[\"']?"
            r"((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|&amp;(?![^\s&#\"'=]*=)|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=])|&(?![^\s&#\"'=]*=))+)"
        ),
    ),
    # A hex key under a credential's name no pattern above lists - `ENCRYPTION_KEY=`, `hmac_key=`,
    # `signing_key:`, `DD_APP_KEY=`, `Ocp-Apim-Subscription-Key:` - 32 or more hex characters (fourth
    # review, 2026-09-30, B-N8; HIGHENTROPY below needs upper case, lower case and a digit). Only these
    # names: "any name ending in key" also took `cache_key=<sha>` and `object_key=<digest>`, and a SECRET is
    # swept from every line, so a commit sha vanished from WARDEN's own deploy record (fifth review).
    (
        "SECRET",
        re.compile(
            r"(?i)(?:^|[\s\"',;{(\[?&])[\w.\-]{0,40}?(?:encryption|encrypt|crypt|hmac|signing|"
            r"sign|secret|private|master|app|application|api|access|subscription|client|account|"
            r"auth|service|license|webhook|session|storage|shared|vault|consumer|root|data|"
            r"deploy|host|oauth|token|master|wrapping|kms|cmk|dek|kek)[_\-.]?key[\"']?\s*[:=]\s*"
            r"[\"']?([0-9a-f]{32,})(?![0-9a-z])"
        ),
    ),
    # Last: a long high-entropy run no named pattern claimed - a bare AWS secret key, one line of a
    # private key logged line by line (a pod log splits it), a base64 credential. Upper, lower AND a
    # digit, so hex digests, ids and plain words do not match.
    # It may start right after `=`: the lookbehind used to exclude it, so a secret after `blob=` (a key
    # no credential pattern names) was never masked (found 2026-09-30).
    (
        "HIGHENTROPY",
        re.compile(
            r"(?<![A-Za-z0-9+/_\-])(?=[A-Za-z0-9+/=_\-]{0,128}[A-Z])(?=[A-Za-z0-9+/=_\-]{0,128}[a-z])"
            r"(?=[A-Za-z0-9+/=_\-]{0,128}\d)[A-Za-z0-9+/_\-]{40,}={0,2}(?![A-Za-z0-9+/=_\-])"
        ),
    ),
]

# Every scanning bound above has a fallback that MASKS instead of letting the text through. A bound is a cost
# ceiling, not a place for a secret to hide: past it the rest of the line (or token) is masked whole.
#   command-line credential gap 1024  -> from the command word, the rest of the line
#   quoted credential value 255       -> the whole quoted value
#   URL password 1024                 -> the rest of the token
#   e-mail local part 254             -> the whole address
# (JWT segments of 4096 and tokens whose mix of cases comes after 128 characters are masked by the long-run
# pattern below.) Each fallback consumes what it matches, so it stays linear on repeated text.
PATTERNS.append(
    (
        "SECRET",
        re.compile(
            r"\b(?:(?:mysql|mariadb)(?:-?dump|-?admin)?|redis-cli|docker[ \t]+login|mongo(?:sh)?"
            r"|az[ \t]+login|sqlcmd|ldap\w*|htpasswd|curl)\b[^\r\n]{1024}[^\r\n]*"
        ),
    )
)
for _quote in ('"', "'"):
    PATTERNS.append(
        (
            "SECRET",
            re.compile(
                _CRED_FLAG
                + rf"(?:{_SP}*={_SP}*|{_SP}+){_quote}[^{_quote}\n]{{256}}[^{_quote}\n]*{_quote}?"
            ),
        )
    )
PATTERNS.append(
    (
        "SECRET",
        re.compile(r"(?i)\b[a-z][a-z0-9+.\-]{0,31}://[^\s:/@]{0,128}:(?=[^\s]{1025,4096}@)[^\s]*"),
    )
)
PATTERNS.append(
    (
        "EMAIL",
        re.compile(
            r"(?<![A-Za-z0-9._+\-])[A-Za-z0-9._+\-]{255,}(?:@|%40)[A-Za-z0-9.\-]{1,255}\.[A-Za-z]{2,}(?![A-Za-z])"
        ),
    )
)

# A very long run of base64-ish characters is a blob whatever its mix of cases: the lookaheads above look at
# the first 128 characters only, so a longer run is masked whole here (nothing escapes at the bound).
PATTERNS.append(
    (
        "HIGHENTROPY",
        re.compile(r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+_\-]{129,}={0,2}(?![A-Za-z0-9+/=_\-])"),
    )
)

# The bank-code patterns, for redact_many's batch-wide context (_has_bank_word).
_BANK_CODES = tuple(p for label, p in PATTERNS if label == "BANKCODE")
_UUID_SHAPE = next(p for label, p in PATTERNS if label == "UUID")
_CARD_SHAPE = next(
    p for label, p in PATTERNS if label == "CREDITCARD"
)  # _mask leaves a card to CREDITCARD

# G7 (2026-11-20, ORDERS 012 and 013, fix rounds 2 and 3): the table runs again after the sweep, to a capped fixed point. A pattern's
# result can change once placeholders stand in the text, and the sweep writes them after every pattern ran:
#   - `BSB: 062-000` on one line, `paid 062-000/12345678` on the next: the account pattern needs `<BANKCODE_n>`
#     before the digits, and on line 2 only the sweep writes it (E3);
#   - `password=V` on one line, `Bearer Vxy` on the next (a token under BEARER's 12 characters): swept to
#     `Bearer <SECRET_1>xy`, which IS 12 characters, so only a later pass masked the tail (E5; the same for BASIC,
#     `authorization:` and every value class that admits `<` and `>` and has a minimum length).
# Which patterns can change is not cheap to tell with certainty (any value class that admits `<`, any guard that reads the text
# around a match), so the whole table runs again over the strings that changed (_Redactor.settle). It is a LOOP: round after
# round until a round changes no text, at most `_SETTLE_ROUNDS` rounds, a refusal past that. A text the first pass and its
# sweep left unchanged is not scanned again (the same patterns over the same text with the same state give the same result),
# so a text with nothing to mask costs what it did.


def _has_bank_word(text: str) -> bool:
    """A strong bank word or a bank code anywhere in `text`: the context for every account in a batch. UUIDs are
    taken out first, as in find(): one can end `-aba123456789`, which is not a routing number."""
    text = _UUID_SHAPE.sub(" ", text)
    return _BANK_CONTEXT.search(text) is not None or any(p.search(text) for p in _BANK_CODES)


# Words that follow a credential key or flag in prose - "--token not set", "password: field
# required", "api_key=true", usage text "--password PASSWORD" - and are not its value. Masked, each
# was also swept from every other line ("invalidating" -> "<SECRET_1>ating", second review 2026-09-30).
# A password that IS one of these words is not protected by redaction anyway.
_NOT_A_VALUE = frozenset(
    {
        "not",
        "set",
        "unset",
        "flag",
        "flags",
        "argument",
        "arguments",
        "option",
        "options",
        "is",
        "was",
        "are",
        "be",
        "required",
        "missing",
        "invalid",
        "field",
        "value",
        "values",
        "must",
        "should",
        "true",
        "false",
        "null",
        "none",
        "nil",
        "empty",
        "provided",
        "given",
        "supplied",
        "expired",
        "rejected",
        "denied",
        "incorrect",
        "wrong",
        "deprecated",
        "changed",
        "rotated",
        "reset",
        "found",
        "specified",
        "configured",
        "needed",
        "ok",
        "yes",
        "no",
        "on",
        "off",
        "enabled",
        "disabled",
        "password",
        "passwd",
        "pass",
        "pwd",
        "secret",
        "secrets",
        "token",
        "tokens",
        "key",
        "apikey",
        "api_key",
        "credential",
        "credentials",
        "redacted",
        "hidden",
        "masked",
        "file",
        "env",
        "stdin",
        "absent",
    }
)
# A value written as a word in angle brackets is a tool saying there is none: Go's `<nil>`, kubectl's `<none>` and
# `<set to the key ...>` (ninth review: since values may hold `<`, each was a secret swept from every line).
_SAYS_NONE = re.compile(r"<[a-z][a-z -]*>?")


# The pieces of a compound value (`_gh_sess=...; theme=dark`, `<uuid>.<secret>`): one with a letter and a digit is
# swept on its own too - masked only as the whole, the same secret echoed alone elsewhere stayed in clear (ninth).
def _secret_shaped(piece: str) -> bool:
    """Upper, lower and a digit, or 20+ characters of letters and digits: a session id or a key, not a region
    (`ap-south-2`) or a name an earlier pattern took in (an ARN after `secret:` swept the region everywhere)."""
    has = [
        any(c.isupper() for c in piece),
        any(c.islower() for c in piece),
        any(c.isdigit() for c in piece),
    ]
    return all(has) or (len(piece) >= 20 and has[2] and (has[0] or has[1]))


# Names under these suffixes are WARDEN's to read and act on, or AWS's generic ones: not an internal host to mask.
_KEPT_HOST = re.compile(
    r"(?i)(?:\.cluster\.local|^(?:[a-z]{2}(?:-[a-z]+)+-\d\.)?(?:compute|ec2)\.internal)$"
)

_PIECE = re.compile(r"[^\s;,&=.:\"'\[\]{}<>]{8,}")

# A placeholder token, captured so `re.split` keeps it as its own segment: `<LABEL_123>`.
_LABELS = tuple(dict.fromkeys(label for label, _ in PATTERNS))
_PLACEHOLDER = re.compile(r"(<[A-Z][A-Z0-9]*_\d+>)")
# Own output (G7 + fix round 1; E9(2) restricted to SECRET tokens): a SECRET value made of nothing but SECRET tokens this
# redactor wrote. One anchored shape: a token is a genuine `<SECRET_n>` or an ESCAPED look-alike as
# `runmap.escape_placeholders` writes one (`<SECRET_1>` becomes U+2039 `SECRET_1` U+203A), ASCII digits only (`runmap._LOOKALIKE`
# uses `\d`, so a look-alike with a non-ASCII digit is escaped there but NEVER exempt here: the redactor writes ASCII digits),
# separated by spaces, tabs, `;` or `,`; optionally the value ends in a SECRET opening cut off by `tools.error_reason`'s length
# cut (`<SECRET_1`, `<SECRET_`, `<SECRET`, `<SEC`, `<S`). The whole value must match: any other character, a mixed form, a token of
# another kind (`<EMAIL_1>`, `‹IPV4_1›`, `<EMA`) or a glued secret is masked whole.
# Why SECRET only: the purpose is that a tool's error text, redacted twice (a throwaway map, then the run's), makes no junk map
# entry for the escaped `password=‹SECRET_1›` the first pass wrote. A real credential spelled like another kind's token
# (`password=‹EMAIL_1› host`, `password=<EMA`) is masked (README K43, decision 7: only `‹SECRET_n›` is exempt).
# TRADE-OFF, accepted (core-c's default, option (a) of the E9 result review; the lead may order (b), an exemption on the tools
# path only): the first pass writes the tokens of OTHER kinds after a key too (EMAIL, IPV4, APIKEY, JWT, URLCRED, HIGHENTROPY
# and PHONE run before the SECRET key=value pattern, so `token=<JWT_1>`, `api_key=<APIKEY_1>`, `password=<EMAIL_1>`). After
# `escape_placeholders` their escaped spelling is a SECRET value and is masked (the same for a typed `password=‹JWT_1›`; a value of
# GENUINE placeholders of any kind, `password=<EMAIL_1>`, is left as typed by the older rule in `_decide`, no entry): ONE junk map entry per distinct escaped token
# (`<SECRET_n>` = `‹JWT_1›`), also for a cut-off opening of another kind (`password=<EMA`). That is accepted, to close the hole
# where a real credential spelled like another kind's token stayed in clear. Tests: tests/test_redact_own_output*.py.
# STATED LIMIT (fail open, by design): a SECRET value made ONLY of SECRET tokens, or of a cut-off start of one (`<S`, `<SE` ...
# `<SECRET_12`: a real 2-character password `<S` or a 4-character `<SEC`), or of genuine placeholders of any kind (the older rule
# in `_decide`: `password=<EMAIL_1> <IPV4_1>`), gets no map entry and stays as typed, whoever wrote it.
_OWN_TOKEN = r"(?:<SECRET_[0-9]+>|\u2039SECRET_[0-9]+\u203a)"  # noqa: S105  (a regex, not a credential)
_OWN_OUTPUT = re.compile(
    rf"[ \t;,]*(?:{_OWN_TOKEN}[ \t;,]*)*(?:<SECRET_[0-9]*|<(?:SECRET|SECRE|SECR|SEC|SE|S))?"
)
# A terminal escape sequence (colour, cursor, title): not text, and glued to a key it hid the key from every pattern
# that needs a word boundary - `ESC[1mAKIA...` read as `mAKIA...` (ninth review, 2026-10-01).
_ANSI = re.compile(
    r"(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|\x1b[@-Z\\-_]"
)


def strip_ansi(text: str) -> str:
    """Escape sequences removed; a space where one stood between two word characters, so a boundary stays."""

    def cut(m: re.Match[str]) -> str:
        s, e = m.start(), m.end()
        glued = (
            s > 0
            and e < len(text)
            and (text[s - 1].isalnum() or text[s - 1] == "_")
            and (text[e].isalnum() or text[e] == "_")
        )
        return " " if glued else ""

    return _ANSI.sub(cut, text) if "\x1b" in text or "\x9b" in text else text


@dataclass
class RedactionResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> original
    # How many times the redactor changed the text of this call: one per value masked by a pattern or masked in place by the fold scan,
    # one per copy replaced by the sweep, one per line (or block of lines) withheld. 0 means the redactor masked nothing and withheld nothing (removed ANSI sequences are not counted). The count
    # of placeholders and the map cannot tell that: a withheld line swallows the placeholders it held and gains one per hit (review
    # finding cb-1-1). The masks of a fold round that was rolled back are not counted.
    actions: int = 0

    @property
    def size(self) -> int:
        return len(self.mapping)

    @property
    def kinds(self) -> list[str]:
        """The kinds found, in first-seen order (hadavin-sdk edit)."""
        return list(dict.fromkeys(_kind(p) for p in self.mapping))

    def restore(self, text: str) -> str:
        """Put the real values back, for display to an operator who is entitled to see them."""
        for placeholder, original in self.mapping.items():
            text = text.replace(placeholder, original)
        return text


def redact(
    text: str,
    *,
    mapping: dict[str, str] | None = None,
    near: tuple[str, ...] = (),
    _sweep_copies: bool = True,
    _cache: dict | None = None,
    _deadline: float | None = None,
) -> RedactionResult:
    """Scrub `text`, then prove the scrub worked.

    Passing an existing `mapping` keeps placeholders stable across many strings in one run, so the
    model still sees that two log lines refer to the same host. `near`: related texts redacted apart
    (a record's other fields) whose bank words still count as bank context here, as in redact_many.
    """
    r = _Redactor(mapping, _cache, _deadline)
    r.bank_near = any(_has_bank_word(strip_ansi(t)) for t in near)
    out = r.find(text)
    # No second read after a `bank_near` flip (round 7; round 6 had one as a safety net, which also counted `actions` twice): the flag is read
    # only by `_decide`, and within one `find` every `_decide` call (`_mask_ex` of the patterns, `_folded_line`) comes after the fold scan has
    # set the flag (its `_line_hits` and `_dry_hits` never call `_decide`), so the one text read already had the context. Pinned by
    # tests/test_redact_settle_loop.py (every `_decide` call of a `find` sees the flag as it is when that `find` ends; 288 spelling x order
    # combinations lose no account). `redact_many` still re-reads the strings read BEFORE the flip: they were read without it.
    if _sweep_copies:  # redact_many's first pass only FINDS values; its second pass masks
        known = len(
            r.mapping
        )  # before the first sweep: a union it registers must count as growth (round 6, design M-E)
        out = r.settle([text], [r.sweep(out, r._deadline)], known=known)[0]
    return RedactionResult(text=out, mapping=r.mapping, actions=r.actions)


def _countable(suffix: str) -> bool:
    """A placeholder number the counter can take: ASCII digits, at most 18 of them. A longer one (a record can hold any text)
    would make int() refuse it past 4,300 digits, and no counter reaches it (CodeRabbit, PR 147)."""
    return suffix.isascii() and suffix.isdigit() and len(suffix) <= 18


# `_Redactor._sub_glued`: a character no e-mail address holds, and the most characters of one token it copies.
_NOT_ADDRESS = re.compile(r"[^A-Za-z0-9._+\-@%]")
_GLUED_WINDOW = 4096

# patterns whose match depends on what stands around them, or on placeholders already placed: they take a full round whatever the scan found
_CONTEXT_LABELS = frozenset({"BANKACCT", "BANKCODE"})
MAX_FOLD_ROUNDS = 4  # rounds of in-place masking per line before the line is withheld
FOLD_NOTE = "[line withheld: look-alike text hid a protected value]"  # fixed text: the folded line is never emitted


_TYPED_PUNCT = frozenset({"-", "'", '"'})
_TYPED_CATEGORIES = frozenset({"Pd", "Pi", "Pf"})  # dashes, opening and closing quotes


@functools.lru_cache(maxsize=65536)
def _char_class(ch: str) -> tuple[str, int] | None:
    """What the fold does to ONE non-ASCII-printable character: (its folded text, 1 if it is a look-alike or sign that must not sit inside a
    masked value else 0), or ``None`` when the fold does something a legitimate text does not (see ``_Redactor._aligned_fold``). Written
    for fold4 on P2d-1 and adapted to fold5 in two places, both because fold5 maps punctuation (gap 4): a dash or a typographic quote
    is its ASCII form with flag 0, and a fraction sign is known by the U+2044 of its decomposition."""
    f = fold(ch)
    flag = 0
    # the fold (fold5, gap 4) writes the fraction slash as "/" itself, so a sign that holds one is known by its decomposition, not by its fold
    src = unicodedata.normalize("NFKD", ch)
    if f == ch or f == "":
        pass
    elif ch.isspace():
        if f != " ":
            return None
    elif unicodedata.category(ch) == "Nd":
        if not (len(f) == 1 and f.isascii() and f.isdigit()):
            return None
    elif (
        f in _TYPED_PUNCT
        and (unicodedata.category(ch) in _TYPED_CATEGORIES or ch == "\u2212")
        and unicodedata.normalize("NFKC", ch) == ch
    ):
        # a dash, the minus sign or a typographic quote, which the fold (fold5, gap 4) reads as ASCII `-`, `'` or `"`: ordinary typography,
        # one character for one, so a value beside or around it is masked in the line as written (like a digit of another script). A
        # full-width or small form (U+FF0D, U+FE63) is a compatibility character and is refused below, as before.
        pass
    elif len(f) == 1 and f.isalpha():
        nfd = unicodedata.normalize("NFD", ch)
        if nfd[0] == f and all(unicodedata.category(c) == "Mn" for c in nfd[1:]):
            flag = (
                0 if f.isascii() else 1
            )  # a letter that lost its accent or mark (e -> e, the Japanese de -> te)
        elif f.isascii() and ch.isalpha() and unicodedata.normalize("NFKC", ch) == ch:
            flag = 1  # a look-alike letter of another script
        else:
            return None  # a full-width or compatibility letter: live ASCII after the fold
    elif f.isascii() and all(c.isalnum() or c == "." or (c == "/" and "\u2044" in src) for c in f):
        # a fraction slash (U+2044, itself or in a one-half sign) is a plain slash here (the fold already writes it as "/"); any other
        # character that folds to "/" is refused
        flag = 1  # a sign that spells letters, digits or dots (an ellipsis, TM, a ligature, a superscript digit): masked around, never inside
    else:
        return None
    return f, flag


_HIDDEN_ASCII = re.compile(
    "[\x00-\x08\x0e-\x1b\x7f]"
)  # ASCII control characters the fold drops (white space is a separator, not hidden)


def _plain(text: str) -> bool:
    """True for a text the fold leaves alone: ASCII with no control character in it. A control character inside a value hides it as well as any
    non-ASCII mark does (``sk-`` + ten letters + DEL + ten letters), so such a line takes the fold scan too."""
    return text.isascii() and _HIDDEN_ASCII.search(text) is None


_PRIMARY_VIEW = (False, True)  # (marks dropped, U+0345 read as an iota): what ``fold`` returns
_IOTA_MARK = "\u0345"


@functools.lru_cache(maxsize=65536)
def _mark_flags(ch: str) -> tuple[bool, bool]:
    """(is a spacing mark, modifier letter or modifier symbol: the characters the marks-dropped views remove, ASCII ``^`` and the backtick
    too (both are category Sk); has a U+0345 in its NFKD form, as U+0345 itself and U+037A do). Per character, so a line costs its distinct characters."""
    return unicodedata.category(ch) in SPACING_CATEGORIES, _IOTA_MARK in unicodedata.normalize(
        "NFKD", ch
    )


def _is_spacing(ch: str) -> bool:
    return _mark_flags(ch)[0]


def _view_specs(line: str) -> tuple[tuple[bool, bool], ...]:
    """The views of ``line`` that can differ from the primary one (``fold``), as (marks dropped, iota) pairs: with a U+0345 (also one that NFKD
    makes from U+037A) the view that drops it, with a spacing mark, modifier letter or modifier symbol the views of the text without them.
    A scan MUST look through all of them (textnorm, "MARKS AND SCANS"): a mark inserted into a protected value hides it from ``fold`` alone.
    A plain line (ASCII, no control character) has none: its characters are read as written."""
    if _plain(line):
        return ()
    flags = [_mark_flags(c) for c in set(line)]
    has_marks = any(f[0] for f in flags)
    has_iota = any(f[1] for f in flags)
    specs = [(False, False)] if has_iota else []
    if has_marks:
        specs.append((True, True))
        if has_iota:
            specs.append((True, False))
    return tuple(specs)


def _alias_keys(value: str) -> tuple[str, ...]:
    """The folded spellings that key the alias index: every view of the value (a clear copy of a value written with a mark inside must be masked)."""
    keys = [fold(value)]
    keys += [fold_view(value, marks_dropped=m, iota=i) for m, i in _view_specs(value)]
    return tuple(dict.fromkeys(keys))


class _Redactor:
    """One placeholder namespace (map, reverse map, counters) shared by every text of one call."""

    def __init__(
        self,
        mapping: dict[str, str] | None,
        cache: dict | None = None,
        deadline: float | None = None,
    ) -> None:
        # the time.thread_time() value (CPU seconds of the calling thread, so load from other threads cannot change the outcome) the folded scan must finish by; runmap passes ONE deadline for a text and all its views
        self._deadline = deadline
        self._scan_deadline = float("inf")
        # the changes this redactor made to its texts (see RedactionResult.actions)
        self.actions = 0
        self._journal_actions = 0  # `actions` when the journal of the line in progress was opened
        self._cache = (
            cache  # a run's built finders, reused while its map is unchanged (see runmap.RunMap)
        )
        self.mapping = dict(mapping or {})
        self.reverse = {v: k for k, v in self.mapping.items()}
        self.counters: dict[str, int] = dict.fromkeys(_LABELS, 0)
        for k in self.mapping:
            kind = _kind(k)
            if kind in self.counters:
                # After the highest number given, not only the count: a map with `<EMAIL_5>` alone must not hand out
                # `<EMAIL_5>` again (CodeRabbit, PR 147). For a map numbered 1..n, as the pipeline's are, it is n.
                suffix = k.strip("<>").rsplit("_", 1)[-1]
                self.counters[kind] = max(
                    self.counters[kind] + 1, int(suffix) if _countable(suffix) else 0
                )
        self._built_for = -1
        self._build_deadline: float | None = None  # set by `sweep` for the build it triggers
        self.alias: dict[
            str, str
        ] = {}  # folded spelling -> placeholder, for written slices that differ from their fold (internal)
        self._journal: list[tuple[str, str, str | None]] | None = (
            None  # registrations of the line in progress
        )
        self._rules: dict[str, tuple[int, str, Any]] = {}
        self._finders: list[tuple[re.Pattern[str], dict[str, list[str]]]] = []
        self._slow: list[str] = []  # values checked one by one: nested too deep for the finder
        self._ordered: list[tuple[str, str]] = []
        self.bank_near = False  # redact_many: a bank word in some string of the batch
        # A secret compound value written with a placeholder in it (`<SECRET_1>xy`, as the first sweep left it): swept as a literal
        # before the placeholder split (see `sweep`), so another copy the first sweep already cut is not left with its tail.
        # Indexed by the FIRST placeholder token the written form holds -> TWO tries: a BACKWARD one of what stands BEFORE the token in
        # the form (its prefix, stored reversed, so the scan reads the text backwards from the token; a node that ends a registered prefix
        # holds key "" -> [prefix id, forms using it]) and ONE forward trie of everything that stands AFTER the token, all forms together
        # (a terminal, key "", holds {prefix id: (placeholder, full value)}). The scan of a token reads the text backwards once, collecting
        # the ids of the prefixes that match, and then forwards ONCE through the suffix trie, at each terminal looking up the matched ids: the
        # cost of a token is the matched prefix length plus the suffix length plus the entries met at the terminals (P + S, not P x S: a
        # cookie jar that grows by one cookie per line, every line ending in the same signed suffix, matches one prefix more per line and
        # walks the suffix once, not once per prefix). The total work of a scan is counted and bounded (`defaults.SPELLED_MAX_WORK`) and
        # the deadline is read in it. A rolled-back registration deletes its form (`_unspell`). MEMORY: the tries hold one dict (about 185
        # bytes, measured: evidence G7-1.md "G7 fix round 7") per character of every registered written form (prefix and suffix) that is
        # not already a node; the characters held are COUNTED per call (`_spelled_chars`, charged in `_spell`, which every registration
        # passes: `find` through `_place`, the union of an overlap through `_place_union` -> `_place`) and the call is REFUSED
        # (`InputTooLarge("SpelledMemoryTooMuch")`, nothing stored by the refused registration) past `defaults.SPELLED_MAX_CHARS`;
        # a registration is never skipped (that would fail open). The registry lives as long as the `_Redactor` (one call). `_spelled_at`
        # holds, per placeholder, the written form's token, its prefix (a reversed COPY) and suffix (a slice COPY; the full value is the
        # SAME object as in `mapping` and in the terminal): a second copy of each written form, not counted in `_spelled_chars`.
        self._spelled: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
        self._spelled_at: dict[
            str, tuple[str, str, str, int]
        ] = {}  # placeholder -> (token, prefix reversed, suffix, prefix id)
        self._next_prefix_id = 0
        self._spelled_chars = 0  # trie nodes (characters of written forms) held now; refused past `defaults.SPELLED_MAX_CHARS`
        if cache and cache.get("map") == self.mapping:  # nothing new since the last build: skip it
            self._ordered, self._rules, self._finders, self._slow, self.alias = cache["state"]
            self._built_for = len(self.mapping)

    def find(self, text: str) -> str:
        out = strip_ansi(text)
        if type(out) is not str:
            out = str.__add__(out, "")  # an exact str: `fold` refuses a subclass as NotText
        if not _plain(out):
            # The folded scan runs FIRST, on the text as written: a direct pass first could mask only the ASCII tail of a value hidden behind
            # look-alike letters (``al<look-alike>ce@example.com`` -> ``al<look-alike><EMAIL_1>``) and leave its head in the text.
            out = self._fold_scan(out)
        for label, pattern in PATTERNS:
            if label == "EMAIL":
                out = self._sub_glued(pattern, label, out)
            else:
                out = pattern.sub(lambda m, label=label: self._mask(m, label), out)
        return out

    def settle(self, originals: list[str], swept: list[str], known: int | None = None) -> list[str]:
        """The pattern passes after the first sweep, to a fixed point with a hard cap (G7; ORDER 020 MJ-B; fix round 3).

        `swept`: one call's strings after find() and sweep(), `originals` the strings they were made from. A ROUND is:
        the whole table over every string in `todo`; if that found a NEW value (the map grew) every string is swept
        once more (the value's other copies go), else only the strings the table changed are swept (a placeholder
        written beside text can complete a spelled form). `todo` for the next round is the UNION of the strings the
        table changed and the strings the sweep changed in the round just run, because a placeholder written where
        a value stood can change what a pattern reads, and so can a rewrite through a value the map already held.
        Round 1 starts from the strings the first pass or its sweep changed. The loop ends when a round changes no text
        (no map growth is possible then): a real fixed point of "table, then sweep" over the call's strings, not "the
        map stopped growing".

        Acceptance rule, exactly: the call is settled when some round r with 1 <= r <= `_SETTLE_ROUNDS` (4) changes no
        text. So a chain whose last change is made in round 3 is accepted (round 4 confirms); a chain that still changes a
        text in round 4 is refused (`RedactionError("NotSettled")`, nothing is shown), because no round has read that
        text since (or a flip no round has read since). The cap is a fail-closed margin over the measured depth (tests/test_redact_settle_loop.py), not a
        derived bound. A text that needs no more passes pays nothing extra: the confirming round runs over the strings
        the previous round changed, and a clean text, or one whose second pass finds nothing, ends in round 1.

        `known`: the size of the map read by the caller BEFORE its first sweep (`redact`, `redact_many`): the first round compares the map with
        it, so an entry the first sweep registered (a union of overlapping forms, `_place_union`) counts as growth and every string is swept once
        more; without it the size is read at the start of the round. From round 2 on the loop does the same itself (round 7): it records the map
        size before the sweep loop of EVERY round, and if the sweeps grew the map every string is put in `todo` and the next round sweeps every
        string (NotSettled stays the cap).

        A `bank_near` flip (a bank word found in a folded view while a round read a string) puts EVERY string back in `todo`: the strings
        that no round changed were read without that context. So a round after a flip runs over every string, and a flip in the LAST round
        leaves `todo` full: the call is refused as NotSettled even when no text changed (no round has read the strings since the flip). The
        flip happens at most once per call (the flag only goes False -> True).

        Time: the call's deadline (CPU clock of the creating thread) is checked before every round and inside every sweep and
        `_build` of the round; `redact` and `redact_many` pass the same deadline into the FIRST sweep (InputTooLarge, never a skipped
        pass: that would fail open). NOT checked: a pattern pass (`find`) over a string, and the loop over the strings of one round, so
        a call can overrun the budget by pass 1 (every string) or by the pass of the round in progress, plus the one `str.replace` or
        finder pass of a sweep that was running. The bound the tests enforce (tests/test_redact_settle_loop.py T4) is the budget plus
        twice the measured unit (one pass and one sweep of the biggest text) plus 0.5 s: looser than that claim, and it is what is
        checked. A machine slow enough that pass 1 alone exceeds the budget refuses the text (InputTooLarge) at the first check
        after it, fail closed; defaults.py has the figures. `redact_text` is a SERIES of such calls (the text, then its views) against one
        absolute deadline: its worst case is the budget + one pass + one sweep + 0.5 s per view, on the CPU clock of the thread only (a thread
        that waits for the GIL or a lock does not advance it): a wall-clock guard at the call is the caller's (core-b)."""
        cur = list(swept)
        todo = {
            i for i, (o, t) in enumerate(zip(originals, cur, strict=True)) if t != strip_ansi(o)
        }
        for _ in range(_SETTLE_ROUNDS):
            if not todo:
                return cur
            self._check_deadline()
            # the map size to compare with after the table ran: the size read BEFORE the sweeps that came before it (the caller's, before the
            # first sweep, in round 1; the previous round's own, in the next ones), so an entry a sweep registered (a union) counts as growth
            # and every string is swept again; the size now when nothing came before
            before = len(self.mapping) if known is None else known
            near_before = self.bank_near
            changed: set[int] = set()
            for i in sorted(todo):
                text = self.find(cur[i])
                if text != cur[i]:
                    cur[i] = text
                    changed.add(i)
            scope = range(len(cur)) if len(self.mapping) != before else sorted(changed)
            # structural (round 7): the map size before the sweeps of EVERY round, not only the first
            known = len(self.mapping)
            for i in scope:
                text = self.sweep(cur[i], self._deadline)
                if text != cur[i]:
                    cur[i] = text
                    changed.add(i)
            todo = changed
            if len(self.mapping) != known:
                # a sweep registered an entry (a union of overlapping forms): the strings swept before it never saw it, so every string is
                # read again and, next round, swept again (`known` is the size before these sweeps: the map is bigger than that then)
                todo = set(range(len(cur)))
            if self.bank_near != near_before:
                # the fold scan of a string found a bank word in a folded view during this round: every string is read again
                # (a pass depends on the text AND on `bank_near`, so "unchanged" no longer means "read")
                todo = set(range(len(cur)))
        if todo:
            from hadavin_sdk.guard.runmap import RedactionError  # runmap imports this module

            raise RedactionError("NotSettled")
        return cur

    def _check_deadline(self) -> None:
        if self._deadline is not None:
            self._over_budget(self._deadline)

    def _sub_glued(self, pattern: re.Pattern[str], label: str, text: str) -> str:
        """`pattern.sub`, and a match may also start exactly where the masked one before it ended.

        Two addresses written without a space (`a.b@x.orga.b@x.org`): the first match takes the start of the second
        address as the end of its domain, and the pattern's look-behind then refuses the rest (`.b@x.org`), because
        the character before it is a name character. That rest was shown, and a second pass over the masked text
        masked it (the character before it is then the `>` of a placeholder): one pass was no fixed point. Here
        the rest is tried at once, as that second pass would read it: on a copy of the token that starts there
        (the token and the character that ends it, at most `_GLUED_WINDOW` characters; the search for its end is bounded as well)."""
        parts: list[str] = []
        last, behind_masked = 0, False
        while True:
            m = None
            if behind_masked:
                # the search is bounded too (review M1): an unbounded one rescanned to the end of the token for every match
                stop = _NOT_ADDRESS.search(text, last, last + _GLUED_WINDOW)
                end = min(stop.end() if stop else len(text), last + _GLUED_WINDOW)
                m = pattern.match(text[last:end])
            if m is not None:
                start, end = last, last + m.end()
            else:
                m = pattern.search(text, last)
                if m is None:
                    break
                start, end = m.start(), m.end()
            shown = self._mask(m, label)
            parts += (text[last:start], shown)
            last = end
            behind_masked = shown != m.group(0) and shown.endswith(">")
        parts.append(text[last:])
        return "".join(parts)

    @staticmethod
    def _over_budget(deadline: float) -> None:
        """Fail closed (``InputTooLarge``) when the folded scan is past its deadline; checked per pattern, per line, per round and per 4096
        characters of the alignment."""
        if time.thread_time() > deadline:
            from hadavin_sdk.guard.runmap import InputTooLarge  # runmap imports this module

            raise InputTooLarge("InputTooLarge")

    @staticmethod
    def _dry_hits(text: str) -> Counter[str]:
        """What the patterns would match in ``text`` (counted after the fold, copies counted: a look-alike copy of a value that also
        appears in clear is a second hit), without registering any placeholder."""
        found: Counter[str] = Counter()

        def note(m: re.Match[str]) -> str:
            found[fold(m.group(0))] += 1
            return "\0"

        for _label, pattern in PATTERNS:
            text = pattern.sub(note, text)
        return found

    def _line_hits(
        self, text: str, starts: list[int], started: float
    ) -> tuple[dict[int, Counter[tuple[str, str]]], dict[int, int], dict[int, set[int]]]:
        """Per line (the line holding the start of the match): the (pattern, folded value) of every match, and for a match that runs over
        several lines the last line it reaches. One pass of each pattern over the whole text, not one run of every pattern per line."""
        per: dict[int, Counter[tuple[str, str]]] = {}
        reach: dict[int, int] = {}
        which: dict[int, set[int]] = {}
        for n, (label, pattern) in enumerate(PATTERNS):
            self._over_budget(started)
            for m in pattern.finditer(text):
                line = bisect_right(starts, m.start()) - 1
                per.setdefault(line, Counter())[(label, fold(m.group(0)))] += 1
                which.setdefault(line, set()).add(n)
                last = bisect_right(starts, max(m.end() - 1, m.start())) - 1
                if last > line:
                    reach[line] = max(reach.get(line, line), last)
        return per, reach, which

    def _fold_scan(self, text: str) -> str:
        """The fold pass over a text with non-ASCII characters. A cheap whole-text scan first finds the lines whose FOLDED form holds a match
        the line itself does not (one pattern pass over the text and one over its folded form, matches counted per line); only those lines
        get the exact per-line treatment of ``_folded_line``. Many short non-ASCII lines (``é`` x 130,000) therefore cost two passes, not
        two pattern runs per line. The work is bounded by ``defaults.REDACT_BUDGET_S`` (``InputTooLarge``, checked inside the passes): the
        call's ``_deadline`` when there is one, else a FRESH allowance of that budget for THIS call of ``find`` (a ``redact`` or ``redact_many``
        made with no ``_deadline`` restarts it on every ``find``, the rounds of ``settle`` included, so such a call has no total bound)."""
        started = (
            self._deadline
            if self._deadline is not None
            else time.thread_time() + defaults.REDACT_BUDGET_S
        )
        self._scan_deadline = started
        lines = text.splitlines(keepends=True)
        specs_of = [_view_specs(ln) for ln in lines]
        all_specs = list(dict.fromkeys(sp for one in specs_of for sp in one))
        views: dict[tuple[bool, bool], list[str]] = {_PRIMARY_VIEW: []}
        for ln in lines:
            if _plain(ln):
                views[_PRIMARY_VIEW].append(ln)
            else:
                body = ln.rstrip("\r\n")
                views[_PRIMARY_VIEW].append(fold(body) + ln[len(body) :])
        for (
            spec
        ) in all_specs:  # a line without this view's characters reads the same in the primary view
            views[spec] = [
                (
                    fold_view(ln.rstrip("\r\n"), marks_dropped=spec[0], iota=spec[1])
                    + ln[len(ln.rstrip("\r\n")) :]
                )
                if spec in one
                else views[_PRIMARY_VIEW][n]
                for n, (ln, one) in enumerate(zip(lines, specs_of, strict=True))
            ]
        self._over_budget(started)

        def starts_of(group: list[str]) -> list[int]:
            starts, at = [], 0
            for ln in group:
                starts.append(at)
                at += len(ln)
            return starts

        direct, _, _ = self._line_hits(text, starts_of(lines), started)
        folded: dict[int, Counter[tuple[str, str]]] = {}
        reach: dict[int, int] = {}
        which: dict[int, set[int]] = {}
        for group in views.values():
            joined = "".join(group)
            per, rch, wh = self._line_hits(joined, starts_of(group), started)
            for i, c in per.items():
                folded.setdefault(i, Counter()).update(
                    c
                )  # the lines' hits of every view (a hit in two views counts twice: only the excess over the direct hits matters, never less)
            for i, r in rch.items():
                reach[i] = max(reach.get(i, i), r)
            for i, w in wh.items():
                which.setdefault(i, set()).update(w)
            if _has_bank_word(joined):
                # a bank word anywhere in the FOLDED text counts as bank context for every line treated here (over-masking is the safe side):
                # without this, an account number below a keyword spelled with an accent or full-width letters stayed in clear
                self.bank_near = True
        suspects = {i for i, c in folded.items() if c - direct.get(i, Counter())}
        if not suspects:
            return text
        out = []
        skip_to = -1
        for i, ln in enumerate(lines):
            if i <= skip_to:
                continue  # inside a multi-line value already replaced
            if i in suspects:
                self._over_budget(started)
                if reach.get(i, i) > i:
                    # a fold-only value that runs over several lines (a PEM block with a look-alike inside): the lines it covers are
                    # replaced together by the note and the placeholders of its hits, folded text never emitted. A second multi-line value
                    # that STARTS inside the block and runs past its end extends it (the block grows to the last line any of them reaches).
                    end, j = reach[i], i
                    while j < end:
                        j += 1
                        end = max(end, reach.get(j, j))
                    blocks = list(dict.fromkeys("".join(g[i : end + 1]) for g in views.values()))
                    last = lines[end]
                    eol = last[
                        len(last.rstrip("\r\n")) :
                    ]  # the line end the block really has (none at the end of the text)
                    out.append(self._withhold(blocks, "".join(lines[i : end + 1]), eol))
                    skip_to = end
                    continue
                ln = self._folded_line(ln, which.get(i))
            out.append(ln)
        return "".join(out)

    @staticmethod
    def _aligned_fold(
        body: str, deadline: float, spec: tuple[bool, bool] = _PRIMARY_VIEW
    ) -> tuple[str, list[int], bytearray] | None:
        """``fold(body)``, the index in ``body`` of every character it keeps, and a flag per kept character that marks a LOOK-ALIKE LETTER
        (a letter of another script that the fold turns into an ASCII letter, as in ordinary Cyrillic or Arabic words). Returned when the fold
        only does what a legitimate text can contain: decimal digits of another script to ASCII digits (Arabic-Indic, Devanagari, full-width
        ...), an accented Latin letter to its base letter, a Unicode space to a space, a look-alike letter (flagged), and dropping of marks,
        format and control characters. ``None`` when any character is folded in another way (a full-width or compatibility letter or
        punctuation mark that becomes live ASCII, a symbol): such a line is an attack signal and ``_folded_line`` withholds it whole."""
        marks, iota = spec
        parts, where, alike = [], [], bytearray()
        for i, ch in enumerate(body):
            if not i & 4095:
                _Redactor._over_budget(deadline)
            if marks and _is_spacing(ch):
                continue  # this view is the text without its spacing marks, modifier letters and modifier symbols
            if " " <= ch <= "~":
                parts.append(ch)
                where.append(i)
                alike.append(0)
                continue
            cls = _char_class(ch)
            if cls is None:
                return None
            f, flag = cls
            if not iota:  # the spelling that drops a subscript iota: a letter with one (U+1FB3) is its base letter alone, not base letter + "i"
                own = fold_view(ch, marks_dropped=marks, iota=False)
                if own != f and own.isascii():
                    f = own
            if f:
                parts.append(f)
                where.extend([i] * len(f))
                alike.extend([flag] * len(f))
        text = "".join(parts)
        whole = fold_view(body, marks_dropped=marks, iota=iota)
        return (text, where, alike) if text == whole else None

    def _mask_in_place(
        self,
        body: str,
        folded: str,
        where: list[int],
        alike: bytearray,
        only: set[int] | None = None,
        marks: bool = False,
    ) -> str | None:
        """Mask the matches found in ``folded`` inside ``body`` itself: the output is ``body`` with each matched value replaced by its
        placeholder; every other character stays as written, and no folded text is ever emitted. ``None`` when a masked value contains a
        look-alike letter: that is a value HIDDEN behind look-alikes (an attack), not an ordinary word of another script next to it."""
        taken = bytearray(len(folded))
        claims: list[tuple[int, int, str, str]] = []
        for n, (label, pattern) in enumerate(PATTERNS):
            if only is not None and n not in only and label not in _CONTEXT_LABELS:
                continue  # a pattern that matched nowhere in this line's folded text (the whole-text scan said so)
            for m in pattern.finditer(folded):
                if any(taken[m.start() : m.end()]):
                    continue  # overlaps a value masked by an earlier pattern; the next round sees it
                original = self._decide(m, label)  # the decision only: nothing is registered yet
                if not original:
                    continue
                group = m.group(0)
                i = group.find(original)
                while i >= 0:
                    s = m.start() + i
                    claims.append((s, s + len(original), label, original))
                    taken[s : s + len(original)] = b"\x01" * len(original)
                    i = group.find(original, i + len(original))
        if any(any(alike[s:e]) for s, e, _, _ in claims):
            return None  # discarded before anything is registered: no orphan placeholder
        out, prev = [], 0
        for s, e, label, _ in sorted(claims):
            start, stop = where[s], where[e - 1] + 1
            if marks:
                # This view has no spacing marks, modifier letters or modifier symbols, so a value that begins or ends beside some would be cut short
                # and the mark left in clear. Take in the run of them on both sides (never into a value already replaced).
                while start > prev and _is_spacing(body[start - 1]):
                    start -= 1
                while stop < len(body) and _is_spacing(body[stop]):
                    stop += 1
            written = body[start:stop]  # the value as it stands in the line
            out += [body[prev:start], self._register_written(label, written)]
            prev = stop
        return "".join(out) + body[prev:] if claims else body

    def _register_written(self, label: str, written: str) -> str:
        """The placeholder of a value masked in place: found by its WRITTEN spelling (two spellings of one folded value get two
        placeholders), a new one when it is new, whose map value is the written slice. The alias index learns the folded spelling."""
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), written)
        placeholder = (
            self.reverse[full] if full in self.reverse else self._place(label, full, written)
        )
        self.actions += 1
        if not _plain(full):
            for key in _alias_keys(full):
                if key and key != full and key not in self.alias:
                    self.alias[key] = placeholder
                    if self._journal is not None:
                        self._journal.append(("alias", key, None))
        return placeholder

    def _folded_line(self, line: str, only: set[int] | None = None) -> str:
        """Fail-closed fold: a value hidden behind look-alike letters, another script's digits, accents or invisible characters does not
        match the patterns above. For a line with non-ASCII text, run the patterns again on its FOLDED form (``textnorm.fold``), BEFORE the
        direct patterns run; a hit is a match the line itself does not give (copies are counted, so a look-alike copy of a value that also
        stands in clear is a hit).

        * If the fold only turns other scripts' digits into ASCII digits, accented Latin letters into their base letters, Unicode spaces into
          spaces, look-alike letters of other scripts into ASCII letters (ordinary Cyrillic or Arabic words) or drops marks and invisible
          characters (``_aligned_fold``), and no matched value contains a look-alike letter, only the matched VALUES are replaced by their
          placeholders, in the line as written (``josé@example.com`` becomes ``<EMAIL_1>`` and the rest of the line stays). This repeats
          (at most 4 rounds) until the fold finds nothing more; a line that still hits then is withheld.
        * Otherwise (a value written with look-alike letters, or a full-width or compatibility character: the signals of an attack) the
          WHOLE LINE is replaced by
          ``FOLD_NOTE`` plus the placeholders of the hits, and the folded text is NEVER emitted: the fold turns full-width and look-alike
          characters into live ASCII (a mention, a link, a command, a fence), and a caller that neutralises text before calling ``redact``
          last (``approvals.channel.clean``) would send that live text to a person. The map holds the WRITTEN slice for an in-place mask and the folded spelling for a withheld line, so ``restore`` gives the written
          value back for the first and the folded value for the second (open hole, closed by the redactor marker of a later package).

        A line with no hit is returned unchanged."""
        if _plain(line):
            return line
        body = line.rstrip("\r\n")
        eol = line[len(body) :]
        cur = body
        counters = self._open_journal()
        try:
            # each round is ONE sweep of the patterns over the folded text; a round that changes nothing ends the loop
            for _ in range(MAX_FOLD_ROUNDS):
                self._over_budget(self._scan_deadline)
                changed = failed = False
                for spec in (
                    *reversed(_view_specs(cur)),
                    _PRIMARY_VIEW,
                ):  # every view; the marks-dropped ones first, so a value split by a mark is cut whole, not at the mark
                    # one view of a long line can take a large share of the budget: look at the clock per view
                    self._over_budget(self._scan_deadline)
                    aligned = self._aligned_fold(cur, self._scan_deadline, spec)
                    new = (
                        None
                        if aligned is None
                        else self._mask_in_place(cur, *aligned, only=only, marks=spec[0])
                    )
                    if new is None:
                        failed = True  # not an ordinary fold, or a value hidden behind look-alikes: withhold below
                        break
                    if new != cur:
                        cur, changed = new, True
                if failed:
                    break
                if not changed:
                    self._journal = None  # the in-place masks stand: keep their registrations
                    return cur + eol if cur != body else line  # nothing (more) to mask in place
        except BaseException:
            self._rollback(counters)
            raise
        # the line is withheld or left as it is: the registrations of its in-place rounds are discarded
        self._rollback(counters)
        folded = [
            fold(body),
            *(fold_view(body, marks_dropped=m, iota=i) for m, i in _view_specs(body)),
        ]
        direct = self._dry_hits(body)
        if not any(self._dry_hits(f) - direct for f in folded):
            return line  # no view finds anything the direct patterns do not (``‹IPV4_2›`` only folds to ``<IPV4_2>``): the direct pass handles it
        return self._withhold(folded, line, eol)

    def _open_journal(self) -> dict[str, int]:
        """Start recording the registrations of one line (placeholders, alias keys), with the counters as they were."""
        self._journal = []
        self._journal_actions = self.actions
        return dict(self.counters)

    def _rollback(self, counters: dict[str, int]) -> None:
        """Undo the registrations recorded since `_open_journal`: no placeholder of a discarded or withheld round stays in the map."""
        journal, self._journal = self._journal or [], None
        for kind, a, b in reversed(journal):
            if kind == "alias":
                self.alias.pop(a, None)
            else:
                self.mapping.pop(a, None)
                if self.reverse.get(b) == a:
                    del self.reverse[b]
                self._unspell(
                    a
                )  # the journal holds the placeholder: its written form goes with it, no ghost is left to revive
        self.counters = counters
        # the masks of the discarded rounds changed no text that is kept
        self.actions = self._journal_actions

    def _withhold(self, views: list[str], line: str, eol: str = "") -> str:
        """The fixed note plus the placeholders of the hits found in any of the ``views`` (the folded texts, never emitted); ``line`` (what
        stands there) when the patterns mask nothing. ``eol`` is the line end to write: none by default, the caller passes the one it cut."""
        hits: list[str] = []

        def mask(m: re.Match[str], label: str) -> str:
            masked = self._mask(m, label)
            if masked != m.group(0):
                hits.append(masked)
            return masked

        for cur in views:
            for label, pattern in PATTERNS:
                cur = pattern.sub(lambda m, label=label: mask(m, label), cur)
        # one for the withheld line (or block), beside one per hit counted by `_mask`
        self.actions += bool(hits)
        return f"{FOLD_NOTE} {' '.join(dict.fromkeys(hits))}{eol}" if hits else line

    def _mask(self, m: re.Match[str], label: str) -> str:
        """One match of `label`'s pattern, its value replaced by its placeholder (a new one when it is new). Registers the
        FOLDED spelling: used by the direct pass and by `_withhold` (the written spelling of a withheld line cannot be located)."""
        res = self._mask_ex(m, label)
        if res is None:
            return m.group(0)
        self.actions += 1
        return m.group(0).replace(*res)

    def _decide(self, m: re.Match[str], label: str) -> str | None:
        """Is this match a hit? The sensitive value, or ``None`` when the match is left alone. Registers nothing."""
        # group(1) exists for TENANT, where only the value is sensitive, not the key name.
        # The first group that took part: a pattern may offer the value in several written forms.
        original = next((g for g in m.groups() if g is not None), m.group(0))
        if label == "SECRET" and (
            original.lower().strip(".,;:)(<>") in _NOT_A_VALUE or _SAYS_NONE.fullmatch(original)
        ):
            return None
        if label == "HOSTNAME" and _KEPT_HOST.search(
            original
        ):  # a name WARDEN reads and acts on, or AWS's own
            return None
        # An account is a bank's only beside a bank word; a grouped card number is left to CREDITCARD (a secret).
        if label == "BANKACCT" and (
            _CARD_SHAPE.fullmatch(original) or not (self.bank_near or _bank_context(m))
        ):
            return None
        # A value holding placeholders already placed (`Cookie: a=<JWT_1>; sid=...`) is stored restored,
        # so restore() gives the original back in one step; one that is nothing but placeholders is
        # masked already (seventh review: excluding `<` instead left the cookies after it in clear).
        # By its shape, not the map: the gate re-scans with a fresh one, and took `Cookie: <SECRET_1>` for a
        # new secret - every report quoting a masked cookie was withheld (eighth review, 2026-10-01).
        if _PLACEHOLDER.search(original) and not re.search(
            r"[A-Za-z0-9]", _PLACEHOLDER.sub("", original)
        ):
            return None
        # Nor is a SECRET value of this redactor's own output alone (G7, ORDER 012; hardened in fix round 1): untrusted
        # redaction run over its own output (a tool's error text is redacted with a throwaway map, then with the
        # run's) escapes the first pass's placeholders, and `password=` before the escaped token made it a new secret:
        # a junk entry in the run's map. The shape is `_OWN_OUTPUT`, matched whole; no entry is made.
        if label == "SECRET" and original.strip(" \t;,") and _OWN_OUTPUT.fullmatch(original):
            return None
        return original

    def _mask_ex(self, m: re.Match[str], label: str) -> tuple[str, str] | None:
        """``_mask`` without the replacing: (the sensitive value, its placeholder), or ``None`` when the match is left alone."""
        original = self._decide(m, label)
        if original is None:
            return None
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), original)
        placeholder = (
            self.reverse[full] if full in self.reverse else self._place(label, full, original)
        )
        return original, placeholder

    def _place(self, label: str, full: str, original: str) -> str:
        """A new placeholder for `full`; for a secret kind, one too for each secret-shaped piece of it."""
        self.counters[label] += 1
        placeholder = f"<{label}_{self.counters[label]}>"
        self.mapping[placeholder] = full
        self.reverse[full] = placeholder
        first = _PLACEHOLDER.search(original) if label in SECRET_KINDS else None
        if first is not None and original != full and len(full) >= 4:
            self._spell(original, first, placeholder, full)
        if self._journal is not None:
            self._journal.append(("map", placeholder, full))
        for piece in (
            _PIECE.findall(_PLACEHOLDER.sub(" ", original)) if label in SECRET_KINDS else ()
        ):
            if piece != full and piece not in self.reverse and _secret_shaped(piece):
                self.counters[label] += 1
                self.mapping[f"<{label}_{self.counters[label]}>"] = piece
                self.reverse[piece] = f"<{label}_{self.counters[label]}>"
                if self._journal is not None:
                    self._journal.append(("map", f"<{label}_{self.counters[label]}>", piece))
        return placeholder

    def _spell(self, original: str, first: re.Match[str], placeholder: str, full: str) -> None:
        """Register the written form `original` for `placeholder`; `first` is the first placeholder token in it (`_place` found it:
        `original` differs from `full`, so it holds one the map resolves).

        MEMORY (round 7): the characters this registration adds to the tries (a node per character not already there, prefix and suffix) are
        counted per call (`self._spelled_chars`; a rolled-back registration gives its nodes back) and refused, BEFORE anything is stored,
        past `defaults.SPELLED_MAX_CHARS` (`InputTooLarge("SpelledMemoryTooMuch")`): the registration is never skipped (that would fail
        open), the call is refused. Every registration passes here: `find` (`_place`) and the union of an overlap (`_place_union` -> `_place`)."""
        token = first.group(1)
        prefix = original[: first.start()][::-1]  # read backwards from the token
        suffix = original[first.end() :]
        roots = self._spelled.get(token) or ({}, {})
        added = _new_nodes(roots[0], prefix) + _new_nodes(roots[1], suffix)
        if self._spelled_chars + added > defaults.SPELLED_MAX_CHARS:
            from hadavin_sdk.guard.runmap import InputTooLarge  # runmap imports this module

            raise InputTooLarge("SpelledMemoryTooMuch")
        self._spelled_chars += added
        back_root, fwd_root = self._spelled.setdefault(token, roots)
        node = back_root
        for ch in prefix:
            node = node.setdefault(ch, {})
        entry = node.get("")
        if entry is None:
            entry = node[""] = [self._next_prefix_id, 0]  # [prefix id, forms that use this prefix]
            self._next_prefix_id += 1
        ahead = fwd_root
        for ch in suffix:
            ahead = ahead.setdefault(ch, {})
        terminals = ahead.setdefault("", {})
        if (
            entry[0] in terminals
        ):  # the same (prefix, suffix) again (a reissue after a rollback) replaces the form: one form, counted once
            self._spelled_at.pop(terminals[entry[0]][0], None)
        else:
            entry[1] += 1
        terminals[entry[0]] = (placeholder, full)
        self._spelled_at[placeholder] = (token, prefix, suffix, entry[0])

    def _unspell(self, placeholder: str) -> None:
        """Delete the written form registered for `placeholder` (a rolled-back registration), and the trie nodes only it used. Every
        registration is made whole by `_spell`, so its paths exist; a placeholder with no written form is simply not in `_spelled_at`."""
        at = self._spelled_at.pop(placeholder, None)
        if at is None:
            return
        token, prefix, suffix, pid = at
        back_root, fwd_root = self._spelled[token]
        back = [back_root]
        for ch in prefix:
            back.append(back[-1][ch])
        ahead = [fwd_root]
        for ch in suffix:
            ahead.append(ahead[-1][ch])
        terminals = ahead[-1][""]
        del terminals[pid]
        if not terminals:
            del ahead[-1][""]
            for depth in range(len(suffix), 0, -1):  # prune the forward nodes that hold nothing now
                if ahead[depth]:
                    break
                del ahead[depth - 1][suffix[depth - 1]]
                self._spelled_chars -= 1
        entry = back[-1][""]
        entry[1] -= 1
        if entry[1] == 0:
            del back[-1][""]
            for depth in range(len(prefix), 0, -1):  # and the backward ones
                if back[depth]:
                    break
                del back[depth - 1][prefix[depth - 1]]
                self._spelled_chars -= 1
        if not back_root and not fwd_root:
            del self._spelled[token]

    def _spelled_sweep(self, out: str, deadline: float | None) -> str:
        """Replace the written forms of compound secrets (`<SECRET_1>xy`) by their placeholder.

        THE RULE: every form that matches in full somewhere in `out` is a candidate (start, end); at one start the longest form is the
        candidate. The candidates are taken leftmost first. A candidate that begins inside one already taken and ends inside it as well is
        covered, and nothing is done. One that begins inside and ENDS BEYOND it (an overlap: `xyz<SECRET_1>` and `<SECRET_1>ab` over
        `xyz<SECRET_1>ab`) fails closed: the span of the whole run of overlapping candidates is registered, on the spot, as an entry of its
        own (a compound value `xyz` + V + `ab`, `_place_union`) and replaced by that placeholder, so no part of it stays readable.
        What is NOT covered (two OPEN limits, both stated, both pinned in tests/test_redact_settle_loop.py, escalation E10 in ESCALATIONS.md; a plan review
        of a fixed-point loop for (1) is separate):
        (1) an overlap that is only complete in a LATER round, when the first form was already swept and replaced by its placeholder before the
        second form was registered (the text is then `xyz<BEARER_1>` and the second form `xyz<SECRET_1>` no longer matches it). The part of the later form that the earlier
        placeholder swallowed (its literal prefix or tail, `xyz`) stays readable in the call's result.
        (2) two compound VALUES that overlap as RAW text (V+`ab` and `xyz`+V, a raw copy `xyz`+V+`ab`): the literal sweep, which runs after this
        scan, replaces the longest value first (`xyz`+V) and the rule of the other no longer matches what is left, so `ab` stays readable. This is
        older than G7, is not limited to compound values (any two stored values that overlap are cut the same way, `abcdefgh` and `efghijkl`) and
        has no detector.
        "No part of it stays readable" holds only for written forms that overlap inside ONE sweep; with (1) and (2) open, that is the claim.

        Cost: a token of the text walks its prefix trie backwards (as far as the text matches a registered prefix), collecting the ids of the
        prefixes that matched, and, when one did, walks the ONE suffix trie of the token forwards (as far as the text matches a registered
        suffix) and looks the matched prefix ids up at each terminal it meets: P + S + the entries met, not P x S. Every step counts one
        unit of work, a token counts one, and so does every entry looked at in a terminal. The scan REFUSES
        (`InputTooLarge("SpelledWorkTooMuch")`) a text that needs more than `defaults.SPELLED_MAX_WORK` units, and reads the deadline (when
        given) every `_SPELL_CHECK_EVERY` units, a token with no form counting one, so a text of tokens with no forms is checked too. The
        limit is read at the same points as the deadline, so the work done when it refuses can pass the limit by the units counted since the last
        reading (under `_SPELL_CHECK_EVERY`) plus the one terminal lookup in progress, whose cost (up to `len(matched)` entries, not 1,024) is added after
        the lookup is made. The work of registering
        the union of an overlap (`_place_union`) is counted too, one unit per character of the union."""
        if not self._spelled:
            return out
        found: list[tuple[int, int, str]] = []
        limit = defaults.SPELLED_MAX_WORK
        work = _SPELL_CHECK_EVERY  # the first token is checked ...
        done = -_SPELL_CHECK_EVERY  # ... and that first reading is not work done
        n = len(out)
        for m in _PLACEHOLDER.finditer(out):
            work += 1
            if work >= _SPELL_CHECK_EVERY:
                done += work
                work = 0
                if done > limit:
                    self._work_refused()
                if deadline is not None:
                    self._over_budget(deadline)
            tries = self._spelled.get(m.group(1))
            if tries is None:
                continue
            node, fwd_root = tries
            at, after, back = m.start(), m.end(), 0
            matched: dict[int, int] = {}  # prefix id -> the characters of that prefix
            while True:
                entry = node.get("")
                if entry is not None:
                    matched[entry[0]] = back
                k = at - back - 1
                if k < 0:
                    break
                work += 1
                if work >= _SPELL_CHECK_EVERY:
                    done += work
                    work = 0
                    if done > limit:
                        self._work_refused()
                    if deadline is not None:
                        self._over_budget(deadline)
                if (node := node.get(out[k])) is None:
                    break
                back += 1
            if not matched:
                continue
            cur, i = fwd_root, after
            best: dict[
                int, tuple[int, str]
            ] = {}  # prefix id -> (end, placeholder) of the longest form met
            while True:
                work += 1
                if work >= _SPELL_CHECK_EVERY:
                    done += work
                    work = 0
                    if done > limit:
                        self._work_refused()
                    if deadline is not None:
                        self._over_budget(deadline)
                terminals = cur.get("")
                if terminals is not None:
                    # look the smaller side up in the larger; every entry looked at is a unit
                    if len(matched) <= len(terminals):
                        hits = [(pid, terminals[pid]) for pid in matched if pid in terminals]
                        cost = len(matched)
                    else:
                        hits = [(pid, t) for pid, t in terminals.items() if pid in matched]
                        cost = len(terminals)
                    work += cost
                    if work >= _SPELL_CHECK_EVERY:
                        done += work
                        work = 0
                        if done > limit:
                            self._work_refused()
                        if deadline is not None:
                            self._over_budget(deadline)
                    for pid, term in hits:
                        # defence in depth (kept, pinned by a test that edits the map): a form whose placeholder no longer maps to its value is not applied
                        if self.mapping.get(term[0]) == term[1]:
                            best[pid] = (i, term[0])
                if i >= n or (cur := cur.get(out[i])) is None:
                    break
                i += 1
            for pid, (end, placeholder) in best.items():
                found.append((at - matched[pid], end, placeholder))
        if not found:
            return out
        found.sort(key=lambda c: (c[0], -c[1]))
        spans: list[list] = []  # [start, end, placeholder, overlapped]
        for start, end, placeholder in found:
            if spans and start < spans[-1][1]:
                if (
                    end > spans[-1][1]
                ):  # begins inside the span and ends beyond it: the run is one span
                    spans[-1][1], spans[-1][3] = end, True
                continue
            spans.append([start, end, placeholder, False])
        pieces: list[str] = []
        last = 0
        for start, end, placeholder, overlapped in spans:
            if overlapped:
                done += (
                    end - start + work
                )  # registering the union reads and stores its text: one unit per character
                work = 0
                if done > limit:
                    self._work_refused()
                if deadline is not None:
                    self._over_budget(deadline)
                placeholder = self._place_union(out[start:end], placeholder)
            pieces += (out[last:start], placeholder)
            last = end
            self.actions += 1
        pieces.append(out[last:])
        return "".join(pieces)

    @staticmethod
    def _work_refused() -> None:
        from hadavin_sdk.guard.runmap import InputTooLarge  # runmap imports this module

        raise InputTooLarge("SpelledWorkTooMuch")

    def _place_union(self, union: str, first: str) -> str:
        """The placeholder of an overlap of written forms: `union` is the text of the whole run (`xyz<SECRET_1>ab`), registered as a compound
        value of its own (its restored text is the value, its kind the kind of the first form's) unless that value has a placeholder already."""
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), union)
        if full in self.reverse:
            return self.reverse[full]
        return self._place(_kind(first), full, union)

    def _build(self) -> None:
        # the deadline of the sweep that triggered the build (`sweep` sets it), else the call's own, as before
        deadline = self._deadline if self._build_deadline is None else self._build_deadline
        # the alias index: the folded spelling of every stored value that is not ASCII and differs from its fold; its keys
        # become sweep rules too, so a clear copy of a masked written variant is masked (one fold per stored value)
        alias: dict[str, str] = {}
        for placeholder, original in self.mapping.items():
            if _plain(original):
                continue
            if deadline is not None:
                self._over_budget(deadline)
            for key in _alias_keys(original):
                if key and key != original:
                    alias.setdefault(key, placeholder)
        self.alias = alias
        stored = set(self.mapping.values())
        self._ordered = sorted(
            [*self.mapping.items(), *((ph, k) for k, ph in alias.items() if k not in stored)],
            key=lambda kv: -len(kv[1]),
        )
        self._rules = {}
        for n, (placeholder, original) in enumerate(self._ordered):
            if deadline is not None and n % 512 == 0:
                self._over_budget(deadline)
            rule = _sweep(placeholder, original)
            if rule is not None and original not in self._rules:
                self._rules[original] = (n, placeholder, rule)
        # Values nested deeper than _MAX_NESTING (a planted chain like `aaaaZ`, `aaaaaZ`, ...) would nest one
        # finder's groups past the recursion limit. They are split into groups, round-robin in sorted order,
        # until every group is shallow enough for a finder of its own: checking them one by one against every
        # segment was quadratic - a comb of 8,008 values within the log caps took 126-144 s a pass (fifth
        # review, 2026-10-01). Only if no split works are they checked one by one.
        trie = _trie(self._rules)
        deep = {w for w in self._rules if _nesting(trie, w) > _MAX_NESTING}
        fast = [w for w in self._rules if w not in deep]
        split = _split(sorted(deep)) if deep else []
        self._slow = [] if split is not None else sorted(deep)
        # Each finder reports one value per position, the longest of its group. A shorter value starting at the
        # same position is always a prefix of it, and it must be checked too: when the longer one is an
        # identifier that is not standalone there, it is not replaced, and a shorter SECRET inside it stayed in
        # clear (fifth review, 2026-10-01). Read off each group's trie: the values ending along each path.
        self._finders = []
        try:
            for group in [g for g in [fast, *(split or [])] if g]:
                group_trie = _trie(group)
                self._finders.append(
                    (
                        _compile_uncached("(?=(" + _trie_regex(group_trie) + "))"),
                        {w: _prefixes(group_trie, w) for w in group},
                    )
                )
        except (RecursionError, re.error, OverflowError):
            self._finders, self._slow = [], list(self._rules)  # the exact per-value loop
        self._built_for = len(self.mapping)
        if self._cache is not None:
            self._cache["map"] = dict(self.mapping)
            self._cache["state"] = (
                self._ordered,
                self._rules,
                self._finders,
                self._slow,
                self.alias,
            )

    def sweep(self, out: str, deadline: float | None = None) -> str:
        # Final literal sweep. The patterns FIND values; this masks the copies a regex boundary missed,
        # by the rule in _sweep: every copy of a secret, every standalone copy of an identifier. Real
        # example from a live cluster: a Kubernetes "failed to reserve container name" event embeds the pod
        # UID inside `..._default_<uid>_0`, where the trailing `b_` is not a `\b` boundary, so the `(uid)`
        # copy was masked and the `_0`-suffixed copy was not.
        #
        # ⛔ The sweep must NOT run inside placeholders already placed. If a TENANT value happens to be
        # the literal `UUID_1`, a naive sweep rewrites the neighbouring `<UUID_1>` to `<<TENANT_1>>` -
        # no leak, but two distinct secrets collapse to one label and restore() breaks. So the text is
        # split on placeholder tokens and only the segments BETWEEN them are swept. Longest originals
        # first, so a value that is a substring of another does not corrupt the longer replacement.
        #
        # Which values occur in a segment is found by ONE trie-shaped regex over all of them, built once
        # per map: testing every value against every segment was quadratic - 217 s for 2,000 lines of
        # 22,500 distinct values (fourth review, 2026-09-30).
        # `deadline` (default None: unchecked): a time.thread_time() value, the clock of `_deadline` (CPU time of the thread that
        # made this redactor; see defaults.REDACT_BUDGET_S). `redact`, `redact_many` and `_Redactor.settle` pass the call's own to
        # EVERY sweep, the first included. Checked in `_build`, every `_SPELL_CHECK_EVERY` units of work of the spelled-form scan
        # (a token of the text or a step of a trie walk, tokens with no form counted), every 32nd free segment (only when the map holds a value to look for) and before each value
        # replaced (InputTooLarge, nothing returned). A single `str.replace` or one finder pass over one segment is not interrupted.
        if self._built_for != len(self.mapping):
            self._build_deadline = deadline
            try:
                self._build()
            finally:
                self._build_deadline = None
        # A compound secret found late (`Bearer <SECRET_1>xy` stored as V+xy): the first sweep already cut its other copies to
        # `<SECRET_1>xy`, which the whole value no longer matches. Its placeholder-spelled form goes first, as a literal on the
        # text before it is split at the placeholders (dz-2, cb-M4).
        out = self._spelled_sweep(out, deadline)
        parts = _PLACEHOLDER.split(
            out
        )  # even indices = free text, odd indices = whole placeholders
        free = 0  # free (non-empty) segments seen: the first is checked, then every 32nd, however many segments the text has
        for i in range(0, len(parts), 2):
            segment = parts[i]
            if not segment:
                continue
            free += 1
            if (
                deadline is not None and (free - 1) % 32 == 0 and (self._finders or self._slow)
            ):  # a text of 100,000 placeholders has 100,000 segments; with no value to look for there is no work to bound
                self._over_budget(deadline)
            present = {w for w in self._slow if w in segment}
            for finder, prefixes in self._finders:
                found = {m.group(1) for m in finder.finditer(segment)}
                present |= found.union(*(prefixes.get(w, ()) for w in found))
            todo = sorted((self._rules[o] for o in present if o in self._rules), key=lambda r: r[0])
            todo = [(self._ordered[n][1], ph, rule) for n, ph, rule in todo]
            for original, placeholder, rule in todo:
                if deadline is not None:
                    self._over_budget(deadline)
                if original not in segment:
                    continue
                before = segment.count(placeholder)
                if rule is _EVERY_COPY:
                    segment = segment.replace(original, placeholder)
                else:
                    segment = _replace_standalone(segment, original, placeholder)
                self.actions += segment.count(placeholder) - before  # one per copy replaced
            parts[i] = segment
        return "".join(parts)


_MAX_NESTING = 200
# The most rounds (a pattern pass over the strings the previous round changed, then a sweep) `_Redactor.settle` makes after the first
# sweep. A call is settled when some round within the cap changes no text, so the last CHANGING round that is accepted is round 3 (round
# 4 confirms). A margin that fails closed, not a derived bound: over the generated compositions of 4 to 8 lines with a pre-seeded map
# (tests/test_redact_settle_loop.py; the test records the distribution with `record_property` (junit xml), it does not print it; a real run is in handover/core-c/evidence/G7-1.md)
# the most rounds run were 3 (a chain of three needs 3: two that change and one that confirms); a chain that changes a text in
# round 4 is refused (RedactionError("NotSettled")).
_SETTLE_ROUNDS = 4
# The scan of the written forms (`_spelled_sweep`) checks its deadline every this many units of work (a placeholder token of the text, or one step of a trie walk).
_SPELL_CHECK_EVERY = 1024


def _new_nodes(root: dict[str, Any], chars: str) -> int:
    """The nodes a walk of `chars` from `root` would add to a trie: the characters after the first one with no node (nothing is stored)."""
    node = root
    for i, ch in enumerate(chars):
        nxt = node.get(ch)
        if nxt is None:
            return len(chars) - i
        node = nxt
    return 0


def _compile_uncached(pattern: str) -> re.Pattern[str]:
    """Compile a pattern built from a run's values WITHOUT putting it in `re`'s process-wide cache (R371: one
    client's identifiers must not sit in memory shared with every other client). `re.purge()` would clear the
    cache of every other pattern too and make each later `re.sub` recompile."""
    try:
        from re import _compiler  # private, present since Python 3.11

        return _compiler.compile(pattern, 0)
    except (ImportError, AttributeError):  # pragma: no cover - a Python without the private module
        compiled = re.compile(pattern)
        re.purge()
        return compiled


def _trie(words) -> dict[str, dict]:
    root: dict[str, dict] = {}
    for w in words:
        node = root
        for ch in w:
            node = node.setdefault(ch, {})
        node[""] = {}
    return root


def _nesting(root: dict[str, dict], word: str) -> int:
    """How many groups the finder would nest along `word`: its branching or ending nodes."""
    depth, node = 0, root
    for ch in word:
        node = node[ch]
        depth += len(node) > 1 or "" in node
    return depth


def _split(words: list[str]) -> list[list[str]] | None:
    """`words` in 2, 4, ... 64 round-robin groups, each nested no deeper than _MAX_NESTING; None if none works.
    Sorted first, so values that are prefixes of each other land in different groups."""
    groups = 2
    while groups <= 64:
        buckets = [words[i::groups] for i in range(groups)]
        if all(_nesting(t, w) <= _MAX_NESTING for b in buckets if b for t in [_trie(b)] for w in b):
            return buckets
        groups *= 2
    return None


def _prefixes(root: dict[str, dict], word: str) -> list[str]:
    """The other values of the trie that are prefixes of `word`."""
    out, node = [], root
    for i, ch in enumerate(word[:-1]):
        node = node[ch]
        if "" in node:
            out.append(word[: i + 1])
    return out


def _trie_regex(root: dict[str, dict]) -> str:
    """One regex matching any word of the trie at a position, longest first (greedy)."""

    def build(node: dict[str, dict]) -> str:
        alts = []
        for ch in sorted(k for k in node if k):
            chars, child = [ch], node[ch]
            while len(child) == 1 and "" not in child:  # a chain with no branch: one literal
                ((nxt, child),) = child.items()
                chars.append(nxt)
            alts.append(re.escape("".join(chars)) + build(child))
        if not alts:
            return ""
        body = alts[0] if len(alts) == 1 else "(?:" + "|".join(alts) + ")"
        return "(?:" + body + ")?" if "" in node else body

    return build(root)


# ⛔ Audit A-C-4: the sweep replaced every copy of every found value, so a TENANT `user_id=500` turned
# every HTTP 500 in the text into <TENANT_1>. The first fix (length thresholds) let SHORT SECRETS
# survive in other lines - URL-encoded, glued, repeated - and made the leak check vacuous
# (independent review, 2026-09-28). The rule now depends on what the value is:
#   - a SECRET (a key, token, password, credential): every copy, anywhere, from 4 characters. A
#     secret must never survive; rewriting a stray substring is the lesser harm.
#   - an IDENTIFIER (tenant, IP, email, account id, ...): every copy that stands as its own token.
#     All-digit values under 6 characters ("500") and common words ("prod", "admin") are not swept:
#     the pattern still masks every occurrence it matches, and a bare "500" elsewhere is a status
#     code far more often than the tenant.
SECRET_KINDS = frozenset(
    {
        "PRIVKEY",
        "JWT",
        "APIKEY",
        "GCPTOKEN",
        "AZURESAS",
        "WEBHOOK",
        "URLCRED",
        "BEARER",
        "BASIC",
        "SECRET",
        "HIGHENTROPY",
        "IBAN",
        "CREDITCARD",
    }
)
_COMMON = frozenset(
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


def _kind(placeholder: str) -> str:
    return placeholder.strip("<>").rsplit("_", 1)[0]


kind_of = _kind  # the public name (guard/runmap.py uses it)


# Every copy, anywhere: plain str.replace, which is what the escaped regex did.
_EVERY_COPY = object()
# Every standalone copy: the pattern is compiled when the value is found in a segment, not for every value.
_STANDALONE = object()


def _sweep(placeholder: str, original: str):
    """How the copies of `original` are swept: every copy (_EVERY_COPY), every standalone copy (a
    compiled pattern), or not at all (None)."""
    if len(original) < 3:
        return None
    if _kind(placeholder) in SECRET_KINDS and len(original) >= 4:
        # Every copy, whatever it looks like. An exemption for "plain words and assignments" (932d515)
        # left real secrets in clear - a base64 key ending in `==`, a passphrase, a letters-only
        # password - and the gate passed them (fourth review, 2026-09-30). Known limit, open (audit
        # B-N4 row): a log writer who plants `password=<word>` masks that word in every line, WARDEN's
        # own reads included. A secret or an identifier must never stay in clear, so that limit is
        # handled by escalating, not by leaving copies unmasked.
        return _EVERY_COPY
    if (original.isdigit() and len(original) < 6) or original.lower() in _COMMON:
        return None
    return _STANDALONE


_ALNUM = frozenset(string.ascii_letters + string.digits)


def _replace_standalone(segment: str, original: str, placeholder: str) -> str:
    """Replace `original` where no ASCII letter or digit touches it. A plain scan: a compiled pattern (or an
    lru_cache of one) keyed by the identifier would keep one client's values in process memory, shared with every
    other client (R371), and `re` caches compiled patterns itself."""
    out: list[str] = []
    i, n = 0, len(original)
    while n:
        j = segment.find(original, i)
        if j < 0:
            break
        before, after = segment[j - 1 : j], segment[j + n : j + n + 1]
        if before in _ALNUM or after in _ALNUM:
            out.append(segment[i : j + 1])
            i = j + 1
            continue
        out += [segment[i:j], placeholder]
        i = j + n
    out.append(segment[i:])
    return "".join(out)


def redact_many(
    items: list[str],
    mapping: dict[str, str] | None = None,
    *,
    near: tuple[str, ...] = (),
    _deadline: float | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Redact several strings as ONE text, with one placeholder namespace: a value found in any of them
    is masked in all of them. One pass left a secret found in a later line in clear in the earlier
    ones (second review, 2026-09-30); the first pass now only finds, the sweep masks, then `_Redactor.settle` runs the
    table again over the strings the sweep changed, to a fixed point with a hard cap (RedactionError past it; see `settle`).
    `near`: texts not redacted here whose bank words still count as bank context (a discussion's evidence).
    `_deadline`: as for `redact` (CPU clock; InputTooLarge past it). A `bank_near` flip during the first reading (a bank word found only
    in a folded view of string n) re-reads the strings before n only (n itself was read with the flag set), each after a deadline check; the strings after n were read with the flag set."""
    r = _Redactor(mapping, None, _deadline)
    r.bank_near = any(_has_bank_word(strip_ansi(t)) for t in (*items, *near))
    near_before = r.bank_near
    found: list[str] = []
    flipped_at: int | None = None
    for n, item in enumerate(items):
        found.append(r.find(item))
        if flipped_at is None and r.bank_near != near_before:
            flipped_at = n
    if flipped_at is not None:
        # `_fold_scan` found a bank word only in a FOLDED view while string `flipped_at` was read: the strings read before it
        # were read without the batch's bank context (that one itself was not: the flag is set before any decision). Read THOSE again (the placeholders the first reading made are reused); the strings
        # after it were read with the flag set. The deadline is read before every one of the reads (`find` itself is not interrupted), so
        # the flip costs at most one more string pass past the budget, not a second pass over every string.
        # not `flipped_at` itself: its `find` set the flag before any decision (see `redact`)
        for n in range(flipped_at):
            r._check_deadline()
            found[n] = r.find(items[n])
    known = len(
        r.mapping
    )  # before the first sweep: a union it registers must count as growth (round 6, design M-E)
    return r.settle(items, [r.sweep(text, r._deadline) for text in found], known=known), r.mapping
