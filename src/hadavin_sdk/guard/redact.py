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

⚠ What this is not (audit A-C-23): nothing here can see a secret NO pattern matches. The patterns are
the control; HIGHENTROPY is their backstop; the outbound gate's G5 re-runs them, independently, on
everything that leaves. (A re-scan inside redact() used the sweep's own rule and could never fire, so
it was removed - second review, 2026-09-30.)
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
from hadavin_sdk.guard.textnorm import SPACING_CATEGORIES, fold_view

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
    (
        "EMAIL",
        re.compile(
            r"(?<![A-Za-z0-9._+\-])[A-Za-z0-9._+\-]{1,254}(?:@|%40)[A-Za-z0-9.\-]{1,255}\.[A-Za-z]{2,}\b"
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
            r"(?i)(?<![\w.\-])[\w.\-]{0,40}"
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
            # (so a comma-bearing secret is masked WHOLE, but `k=v,k2=v2` is not gobbled). `&` stops a
            # URL query-param value at the next parameter. Char-by-char, so no catastrophic backtracking.
            # A numeric HTML entity (`&#59;`, `&amp;#59;` once escaped, `&#x3b;`) is ONE character of the value, not the `&` of a query separator:
            # an entity-encoded `;` or `&` must not end the value early and leave its tail shown.
            r"((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)"
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
            r"(?<![A-Za-z0-9._+\-])[A-Za-z0-9._+\-]{255,}(?:@|%40)[A-Za-z0-9.\-]{1,255}\.[A-Za-z]{2,}\b"
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
        if glued and e - s == 2 and text[s + 1].isalpha():
            return m.group(
                0
            )  # ESC or U+009B with ONE letter: that letter may belong to a key cut by the control (the fold drops the control)
        return " " if glued else ""

    return _ANSI.sub(cut, text) if "\x1b" in text or "\x9b" in text else text


@dataclass
class RedactionResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> original

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
    if _sweep_copies:  # redact_many's first pass only FINDS values; its second pass masks
        out = r.sweep(out)
    return RedactionResult(text=out, mapping=r.mapping)


def _countable(suffix: str) -> bool:
    """A placeholder number the counter can take: ASCII digits, at most 18 of them. A longer one (a record can hold any text)
    would make int() refuse it past 4,300 digits, and no counter reaches it (CodeRabbit, PR 147)."""
    return suffix.isascii() and suffix.isdigit() and len(suffix) <= 18


# patterns whose match depends on what stands around them, or on placeholders already placed: they take a full round whatever the scan found
_CONTEXT_LABELS = frozenset({"BANKACCT", "BANKCODE"})
MAX_FOLD_ROUNDS = 4  # rounds of in-place masking per line before the line is withheld
FOLD_NOTE = "[line withheld: look-alike text hid a protected value]"  # fixed text: the folded line is never emitted


@functools.lru_cache(maxsize=65536)
def _char_class(ch: str) -> tuple[str, int] | None:
    """What the fold does to ONE non-ASCII-printable character: (its folded text, 1 if it is a look-alike or sign that must not sit inside a
    masked value else 0), or ``None`` when the fold does something a legitimate text does not (see ``_Redactor._aligned_fold``)."""
    f = fold_view(ch)
    flag = 0
    if ch == "\u2044":
        return "/", 1  # a fraction slash spells a slash: masked around, never inside (SL-D)
    if f == ch or f == "":
        pass
    elif ch.isspace():
        if f != " ":
            return None
    elif unicodedata.category(ch) == "Nd":
        if not (len(f) == 1 and f.isascii() and f.isdigit()):
            return None
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
    elif (g := f.replace("\u2044", "/")).isascii() and all(
        c.isalnum() or c == "." or (c == "/" and "\u2044" in f) for c in g
    ):
        f = g  # a fraction slash (U+2044, as in a one-half sign) is a plain slash here; any other character that folds to "/" is refused
        flag = 1  # a sign that spells letters, digits or dots (an ellipsis, TM, a ligature, a superscript digit): masked around, never inside
    else:
        return None
    return f, flag


_HIDDEN_ASCII = re.compile(
    "[\x00-\x08\x0e-\x1b\x7f]|[\t\x0b\x0c\x1c-\x1f]"
)  # ASCII control characters the fold drops, and a white-space-like one (see _JOIN_CTLS) ANYWHERE: whatever stands beside it, a secret may be cut by it
# The white-space-like control characters the fold reads as a space: tab, vertical tab, form feed, U+001C to U+001F and NEL (U+0085). A reader sees
# a separator, so a key cut by one is two words; but a key in the text is a key whatever a character inside it looks like, so the views that
# drop spacing marks drop these too, and a fixed-shape value found that way is masked whole, with the control characters inside it. (A new line
# and a carriage return are line ends, not read this way.)
_JOIN_CTLS = "\t\x0b\x0c\x1c\x1d\x1e\x1f\x85"
JOIN_RE = re.compile("[" + _JOIN_CTLS + "]")
_LINES = re.compile(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+")


# GAP: the character that stands in a gap-tolerant view for one run of HIDDEN items (white-space-like control characters, escape sequences,
# spacing marks and modifier letters of a marks view, characters the fold drops). It is a private-use character, so it is no word character and
# no white space: a word boundary next to it holds. The patterns of such a view are the ordinary patterns rewritten (``_tolerant``) so that
# every item they read may be followed by any number of GAPs: a secret is found with any number of hidden items of any kind inside it, and
# each EDGE of a match decides for itself whether it is a boundary (a gap beside the edge counts as the space it may stand for).
GAP = "\ue000"
_JOIN_RUN = re.compile("[" + _JOIN_CTLS + "]+")


_fold_char = fold_view  # the fold of ONE character, for the view code (a name of its own: callers count the folds of whole values)


@functools.lru_cache(maxsize=65536)
def _is_dropped(ch: str) -> bool:
    """True for a character the fold removes without a trace (zero-width and format characters, ASCII controls other than the white-space-like
    ones): in a gap-tolerant view it is a gap."""
    return not (" " <= ch <= "~") and ch not in _JOIN_CTLS and _fold_char(ch) == ""


def _gap_spans(text: str, read: int, marks: bool) -> list[tuple[int, int]]:
    """The runs of hidden items of ``text`` as (start, stop), merged when they touch. ``read`` 1: every white-space-like control character,
    every whole escape sequence and every character the fold drops; ``read`` 2: the same, except that the LAST character of an escape
    sequence is a real character (the letter of ``AKIAIOS<ESC>[FODNN7...`` may be the key's own); with ``marks`` the spacing marks, modifier
    letters and modifier symbols too."""
    spans: list[tuple[int, int]] = [m.span() for m in _JOIN_RUN.finditer(text)]
    if "\x1b" in text or "\x9b" in text:
        for m in _ANSI.finditer(text):
            s, e = m.span()
            if read == 2:
                if (
                    text[s] == "\x1b" and text[s + 1 : s + 2] == "]"
                ):  # a title string: only its frame goes, its text is read
                    spans.append((s, s + 2))
                    if text[e - 1] == "\x07":
                        spans.append((e - 1, e))
                else:
                    spans.append((s, e - 1))
            else:
                spans.append((s, e))
    if not text.isascii() or not text.isprintable():
        for i, ch in enumerate(text):
            if _is_dropped(ch) or (marks and unicodedata.category(ch) in SPACING_CATEGORIES):
                spans.append((i, i + 1))
    spans = [sp for sp in spans if sp[0] < sp[1]]
    spans.sort()
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _view(text: str, marks: bool, iota: bool, read: int = 0) -> str:
    """One view of ``text`` (``fold_view``). ``read`` 0: as written (the views that drop spacing marks drop the white-space-like control
    characters first). ``read`` 1 or 2: the gap-tolerant view, every run of hidden items (``_gap_spans``) is one ``GAP`` between the folded
    pieces of text on both sides of it."""
    if not read:
        return fold_view(JOIN_RE.sub("", text) if marks else text, marks_dropped=marks, iota=iota)
    parts, prev = [], 0
    for s, e in _gap_spans(text, read, marks):
        parts.append(fold_view(text[prev:s], marks_dropped=marks, iota=iota))
        parts.append(GAP)
        prev = e
    parts.append(fold_view(text[prev:], marks_dropped=marks, iota=iota))
    return "".join(parts)


def _plain(text: str) -> bool:
    """True for a text the fold leaves alone: ASCII with no control character in it. A control character inside a value hides it as well as any
    non-ASCII mark does (``sk-`` + ten letters + DEL + ten letters), so such a line takes the fold scan too."""
    return text.isascii() and _HIDDEN_ASCII.search(text) is None


_PRIMARY_VIEW = (
    False,
    True,
    0,
)  # (marks dropped, U+0345 read as an iota, how escape sequences are read): what ``fold`` returns
_IOTA_MARK = "\u0345"


@functools.lru_cache(maxsize=65536)
def _mark_flags(ch: str) -> tuple[bool, bool]:
    """(is a spacing mark, modifier letter or modifier symbol: the characters the marks-dropped views remove, ASCII ``^`` and the backtick
    too (both are category Sk); has a U+0345 in its NFKD form, as U+0345 itself and U+037A do). Per character, so a line costs its distinct characters."""
    return unicodedata.category(
        ch
    ) in SPACING_CATEGORIES or ch in _JOIN_CTLS, _IOTA_MARK in unicodedata.normalize("NFKD", ch)


def _is_edge_mark(ch: str) -> bool:
    """A spacing mark, modifier letter or modifier symbol (not a control character): the characters a masked value takes with it at its edge."""
    return unicodedata.category(ch) in SPACING_CATEGORIES


def _is_spacing(ch: str) -> bool:
    return _mark_flags(ch)[0]


def _view_specs(line: str) -> tuple[tuple[bool, bool, int], ...]:
    """The views of ``line`` that can differ from the primary one (``fold``), as (marks dropped, iota, read) triples. A scan MUST look through
    all of them (textnorm, "MARKS AND SCANS"): a mark inserted into a protected value hides it from ``fold`` alone. ``read`` 0 is the text as
    written; 1 and 2 are the gap-tolerant views (``GAP``): ONE view holds every hidden item of the line (white-space-like controls, escape
    sequences, characters the fold drops, and with ``marks`` the spacing marks), however many there are and in whatever order, and the
    patterns decide the boundary of each edge of a match themselves. Two readings exist only for a line with an escape sequence (2: its last
    character is a real one). A plain line (ASCII, no control character) has no view: its characters are read as written."""
    if _plain(line):
        return ()
    chars = set(line)
    flags = {c: _mark_flags(c) for c in chars}
    has_iota = any(f[1] for f in flags.values())
    real_marks = any(f[0] and c not in _JOIN_CTLS for c, f in flags.items())
    ansi = _ANSI.search(line) is not None
    has_gap = ansi or any(c in _JOIN_CTLS or _is_dropped(c) for c in chars)
    reads = (1, 2) if ansi else (1,)
    specs: list[tuple[bool, bool, int]] = []
    if has_iota:
        specs += [(False, False, r) for r in (reads if has_gap else (0,))]
    if has_gap:
        specs += [(False, True, r) for r in reads]
    if real_marks:
        specs += [(True, True, r) for r in reads]
        if has_iota:
            specs += [(True, False, r) for r in reads]
    return tuple(dict.fromkeys(specs))


def _alias_keys(value: str) -> tuple[str, ...]:
    """The folded spellings that key the alias index: every view of the value (a clear copy of a value written with a mark inside must be masked)."""
    keys = [fold_view(value)]
    keys += [_view(value, *spec).replace(GAP, "") for spec in _view_specs(value)]
    return tuple(dict.fromkeys(keys))


def _reads_gap(op: Any, av: Any, state: Any) -> bool:
    """True when the single parse item ``(op, av)`` would match the ``GAP`` character (compiled and tried once, so the answer is the regex
    engine's own, flags included)."""
    from re import _compiler as comp
    from re import _parser as sp

    return comp.compile(sp.SubPattern(state, [(op, av)]), state.flags).match(GAP) is not None  # type: ignore[arg-type]


def _tolerate(items: Any, state: Any) -> list[Any]:
    """The parse of a pattern with every item it reads made to accept any number of ``GAP`` after it. An item never takes a GAP itself (a
    guard in front of it), so a GAP is read in exactly one way and the match stays linear. Boundary assertions (``\\b``, ``^``, look-behinds)
    are left alone: they see the GAP, a non-word non-space character, where the hidden items stand; look-aheads are rewritten like the rest."""
    from re import _constants as c  # the parser's own names; the repo runs on Python 3.12 and later
    from re import _parser as sp

    def sub(data: Any) -> Any:
        return sp.SubPattern(state, data)

    gap = (c.LITERAL, ord(GAP))
    out: list[Any] = []
    for op, av in items:
        if op in (c.LITERAL, c.NOT_LITERAL, c.IN, c.ANY):
            # The guard is only needed where the item itself could read a GAP (``.``, ``[^x]``, ``\\W``); a literal or a plain set cannot, and
            # without a guard the compiled pattern keeps its literal prefix, which is what lets the scan skip along a long text.
            guard = [(c.ASSERT_NOT, (1, sub([gap])))] if _reads_gap(op, av, state) else []
            out.append(
                (
                    c.SUBPATTERN,
                    (
                        None,
                        0,
                        0,
                        sub([*guard, (op, av), (c.MAX_REPEAT, (0, c.MAXREPEAT, sub([gap])))]),
                    ),
                )
            )
        elif op in (c.MAX_REPEAT, c.MIN_REPEAT, c.POSSESSIVE_REPEAT):
            lo, hi, body = av
            one = list(body)
            if (
                op == c.MAX_REPEAT
                and lo <= 1
                and hi == c.MAXREPEAT
                and len(one) == 1
                and one[0][0] in (c.LITERAL, c.IN)
                and not _reads_gap(one[0][0], one[0][1], state)
            ):
                # ``X+`` / ``X*`` with a GAP allowed after each X, written so the engine keeps its fast loop over X: ``X+(?:GAP+X+)*GAP*``
                # (the same strings; every GAP-run starts with a GAP, so no string can be read two ways and the match stays linear)
                run = sub([(c.MAX_REPEAT, (1, c.MAXREPEAT, sub(one)))])
                more = sub(
                    [
                        (
                            c.MAX_REPEAT,
                            (
                                0,
                                c.MAXREPEAT,
                                sub([(c.MAX_REPEAT, (1, c.MAXREPEAT, sub([gap]))), *run]),
                            ),
                        )
                    ]
                )
                whole = [*run, *more, (c.MAX_REPEAT, (0, c.MAXREPEAT, sub([gap])))]
                out.append(
                    (c.SUBPATTERN, (None, 0, 0, sub(whole)))
                    if lo == 1
                    else (c.MAX_REPEAT, (0, 1, sub([(c.SUBPATTERN, (None, 0, 0, sub(whole)))])))
                )
            else:
                out.append((op, (lo, hi, sub(_tolerate(body, state)))))
        elif op == c.SUBPATTERN:
            group, add, delete, body = av
            out.append((op, (group, add, delete, sub(_tolerate(body, state)))))
        elif op == c.ATOMIC_GROUP:
            out.append((op, sub(_tolerate(av, state))))
        elif op == c.BRANCH:
            out.append((op, (av[0], [sub(_tolerate(b, state)) for b in av[1]])))
        elif op in (c.ASSERT, c.ASSERT_NOT) and av[0] > 0:
            out.append((op, (av[0], sub(_tolerate(av[1], state)))))
        else:
            out.append((op, av))
    return out


def _tolerant(pattern: re.Pattern[str]) -> re.Pattern[str]:
    """``pattern`` rewritten for the gap-tolerant views (see ``GAP``)."""
    from re import _compiler as comp
    from re import _parser as sp

    parsed = sp.parse(pattern.pattern, pattern.flags)
    return comp.compile(
        sp.SubPattern(parsed.state, _tolerate(parsed.data, parsed.state)), pattern.flags
    )  # type: ignore[arg-type]


@functools.lru_cache(maxsize=1)
def _tolerant_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """The gap-tolerant twin of ``PATTERNS`` (same order, same labels and groups)."""
    return tuple((label, _tolerant(p)) for label, p in PATTERNS)


def _patterns_for(text: str) -> Any:
    """The patterns to run on ``text``: the gap-tolerant ones when it holds a GAP, the ordinary ones otherwise."""
    return _tolerant_patterns() if GAP in text else PATTERNS


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
        if cache and cache.get("map") == self.mapping:  # nothing new since the last build: skip it
            self._ordered, self._rules, self._finders, self._slow, self.alias = cache["state"]
            self._built_for = len(self.mapping)

    def find(self, text: str) -> str:
        out = text
        if type(out) is not str:
            out = str.__add__(out, "")  # an exact str: `fold` refuses a subclass as NotText
        if not _plain(out):
            # The folded scan runs FIRST, on the text as written: a direct pass first could mask only the ASCII tail of a value hidden behind
            # look-alike letters (``al<look-alike>ce@example.com`` -> ``al<look-alike><EMAIL_1>``) and leave its head in the text.
            out = self._fold_scan(out)
        # An escape sequence is read by the folded scan above (inside the one gap-tolerant view, whatever else is hidden beside it); only then are
        # the ones left removed, so the direct patterns see a word boundary where one stood. A placeholder is never cut: ``ESC`` or U+009B in
        # front of ``<APIKEY_1>`` would otherwise take its first letters for the rest of a sequence.
        if "\x1b" in out or "\x9b" in out:
            out = "".join(strip_ansi(part) for part in _PLACEHOLDER.split(out))
        for label, pattern in PATTERNS:
            out = pattern.sub(lambda m, label=label: self._mask(m, label), out)
        return out

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
            found[fold_view(m.group(0).replace(GAP, ""))] += 1
            return "\0"

        for _label, pattern in _patterns_for(text):
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
        for n, (label, pattern) in enumerate(_patterns_for(text)):
            self._over_budget(started)
            for m in pattern.finditer(text):
                line = bisect_right(starts, m.start()) - 1
                per.setdefault(line, Counter())[
                    (label, fold_view(m.group(0).replace(GAP, "")))
                ] += 1
                which.setdefault(line, set()).add(n)
                last = bisect_right(starts, max(m.end() - 1, m.start())) - 1
                if last > line:
                    reach[line] = max(reach.get(line, line), last)
        self._over_budget(started)
        return per, reach, which

    def _fold_scan(self, text: str) -> str:
        """The fold pass over a text with non-ASCII characters. A cheap whole-text scan first finds the lines whose FOLDED form holds a match
        the line itself does not (one pattern pass over the text and one over its folded form, matches counted per line); only those lines
        get the exact per-line treatment of ``_folded_line``. Many short non-ASCII lines (``é`` x 130,000) therefore cost two passes, not
        two pattern runs per line. The work is bounded by ``defaults.REDACT_BUDGET_S`` (``InputTooLarge``, checked inside the passes)."""
        started = (
            self._deadline
            if self._deadline is not None
            else time.thread_time() + defaults.REDACT_BUDGET_S
        )
        self._scan_deadline = started
        lines = _LINES.findall(
            text
        )  # lines end at \n, \r\n or \r only: ``splitlines`` also cuts at a vertical tab, form feed, U+001C to U+001E and NEL, inside a key
        specs_of = [_view_specs(ln) for ln in lines]
        all_specs = list(dict.fromkeys(sp for one in specs_of for sp in one))
        views: dict[tuple[bool, bool, int], list[str]] = {_PRIMARY_VIEW: []}
        for ln in lines:
            if _plain(ln):
                views[_PRIMARY_VIEW].append(ln)
            else:
                body = ln.rstrip("\r\n")
                views[_PRIMARY_VIEW].append(fold_view(body) + ln[len(body) :])
        for (
            spec
        ) in all_specs:  # a line without this view's characters reads the same in the primary view
            views[spec] = [
                (_view(ln.rstrip("\r\n"), *spec) + ln[len(ln.rstrip("\r\n")) :])
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
        body: str, deadline: float, spec: tuple[bool, bool, int | tuple[int, ...]] = _PRIMARY_VIEW
    ) -> tuple[str, list[int], bytearray] | None:
        """``fold_view(body)``, the index in ``body`` of every character it keeps, and a flag per kept character that marks a LOOK-ALIKE LETTER
        (a letter of another script that the fold turns into an ASCII letter, as in ordinary Cyrillic or Arabic words). Returned when the fold
        only does what a legitimate text can contain: decimal digits of another script to ASCII digits (Arabic-Indic, Devanagari, full-width
        ...), an accented Latin letter to its base letter, a Unicode space to a space, a look-alike letter (flagged), and dropping of marks,
        format and control characters. ``None`` when any character is folded in another way (a full-width or compatibility letter or
        punctuation mark that becomes live ASCII, a symbol): such a line is an attack signal and ``_folded_line`` withholds it whole."""
        marks, iota, read = spec
        gaps = _gap_spans(body, read, marks) if read else []
        parts, where, alike = [], [], bytearray()
        g, i, n, check = 0, 0, len(body), 0
        while i < n:
            if i >= check:
                _Redactor._over_budget(deadline)
                check = i + 4096
            if (
                g < len(gaps) and gaps[g][0] == i
            ):  # a run of hidden items: ONE gap, whatever it holds
                parts.append(GAP)
                where.append(i)
                alike.append(0)
                i = gaps[g][1]
                g += 1
                continue
            ch = body[i]
            i += 1
            if marks and not read and _is_spacing(ch):
                continue  # this view is the text without its spacing marks, modifier letters and modifier symbols
            if " " <= ch <= "~":
                parts.append(ch)
                where.append(i - 1)
                alike.append(0)
                continue
            cls = _char_class(ch)
            if cls is None:
                return None
            f, flag = cls
            if not iota:  # the spelling that drops a subscript iota: a letter with one (U+1FB3) is its base letter alone, not base letter + "i"
                own = fold_view(ch, marks_dropped=marks, iota=False).replace("\u2044", "/")
                if own != f and own.isascii():
                    f = own
            if f:
                parts.append(f)
                where.extend([i - 1] * len(f))
                alike.extend([flag] * len(f))
        text = "".join(parts)
        whole = _view(body, marks, iota, read).replace("\u2044", "/")
        return (text, where, alike) if text == whole else None

    def _mask_in_place(
        self,
        body: str,
        folded: str,
        where: list[int],
        alike: bytearray,
        only: set[int] | None = None,
        marks: bool = False,
    ) -> list[tuple[int, int, str, bool]]:
        """The matches found in ``folded`` as (start, stop, label, hidden) in ``body`` itself (the characters the view dropped inside a value
        are inside its span); nothing is registered. ``hidden`` is true when the matched value contains a look-alike letter: that is a value
        HIDDEN behind look-alikes (an attack), not an ordinary word of another script next to it, unless another view finds the whole of it."""
        taken = bytearray(len(folded))
        claims: list[tuple[int, int, str, str]] = []
        for n, (label, pattern) in enumerate(_patterns_for(folded)):
            if only is not None and n not in only and label not in _CONTEXT_LABELS:
                continue  # a pattern that matched nowhere in this line's folded text (the whole-text scan said so)
            self._over_budget(self._scan_deadline)
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
                    # a GAP the match took in at its end is not part of the value: the hidden items beside it stay in the text (a match
                    # never begins with one: every item has a guard in front of it)
                    hi = s + len(original)
                    while hi > s and folded[hi - 1] == GAP:
                        hi -= 1
                    if hi > s:  # a value of nothing but hidden items is no value
                        claims.append((s, hi, label, original))
                    taken[s : s + len(original)] = b"\x01" * len(original)
                    i = group.find(original, i + len(original))
        spans = []
        for s, e, label, _ in sorted(claims):
            hidden = any(alike[s:e])
            start, stop = where[s], where[e - 1] + 1
            if marks:
                # This view has no spacing marks, modifier letters or modifier symbols, so a value that begins or ends beside some would be cut short
                # and the mark left in clear. Take in the run of them on both sides.
                while start > 0 and _is_edge_mark(body[start - 1]):
                    start -= 1
                while stop < len(body) and _is_edge_mark(body[stop]):
                    stop += 1
            spans.append((start, stop, label, hidden))
        return spans

    def _apply_claims(self, body: str, spans: list[tuple[int, int, str, bool]]) -> str:
        """``body`` with every span replaced by its placeholder. Spans that touch or overlap (the same value found in two views, or a piece
        of it found in one view and the whole of it in another) are ONE value: the union, under the label of the longest of them."""
        merged: list[list[Any]] = []
        for start, stop, label, _ in sorted(spans):
            if merged and start < merged[-1][1]:
                if stop - start > merged[-1][3]:
                    merged[-1][2], merged[-1][3] = label, stop - start
                merged[-1][1] = max(merged[-1][1], stop)
            else:
                merged.append([start, stop, label, stop - start])
        out, prev = [], 0
        for start, stop, label, _ in merged:
            out += [body[prev:start], self._register_written(label, body[start:stop])]
            prev = stop
        return "".join(out) + body[prev:] if merged else body

    def _register_written(self, label: str, written: str) -> str:
        """The placeholder of a value masked in place: found by its WRITTEN spelling (two spellings of one folded value get two
        placeholders), a new one when it is new, whose map value is the written slice. The alias index learns the folded spelling."""
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), written)
        placeholder = (
            self.reverse[full] if full in self.reverse else self._place(label, full, written)
        )
        if not _plain(full):
            for key in _alias_keys(full):
                self._over_budget(self._scan_deadline)
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
                odd = False
                spans: list[tuple[int, int, str, bool]] = []
                for spec in (
                    *_view_specs(cur),
                    _PRIMARY_VIEW,
                ):  # every view finds its matches in the SAME text; they are applied together below (a piece found in one view and the whole of the value in another are one value)
                    # one view of a long line can take a large share of the budget: look at the clock per view
                    self._over_budget(self._scan_deadline)
                    aligned = self._aligned_fold(cur, self._scan_deadline, spec)
                    if aligned is None:
                        odd = True  # not an ordinary fold: judged again after this round's masks (the value may be cut out whole by another view)
                        continue
                    spans += self._mask_in_place(cur, *aligned, only=only, marks=spec[0])
                whole = [(a, b) for a, b, _, hidden in spans if not hidden]
                if any(
                    hidden and not any(c <= a and b <= d for c, d in whole)
                    for a, b, _, hidden in spans
                ):
                    break  # a value hidden behind look-alikes that no other view reads whole: withhold below
                new = self._apply_claims(cur, [x for x in spans if not x[3]])
                changed = new != cur
                cur = new
                if odd and not changed:
                    break  # a view that is not an ordinary fold and no mask to make it one: withhold below
                if not changed:
                    self._journal = None  # the in-place masks stand: keep their registrations
                    return cur + eol if cur != body else line  # nothing (more) to mask in place
        except BaseException:
            self._rollback(counters)
            raise
        # the line is withheld or left as it is: the registrations of its in-place rounds are discarded
        self._rollback(counters)
        folded = [
            fold_view(body),
            *(_view(body, *spec) for spec in _view_specs(body)),
        ]
        direct = self._dry_hits(body)
        new_hit = False
        for f in folded:
            self._over_budget(self._scan_deadline)
            if self._dry_hits(f) - direct:
                new_hit = True
                break
        if not new_hit:
            return line  # no view finds anything the direct patterns do not (``‹IPV4_2›`` only folds to ``<IPV4_2>``): the direct pass handles it
        return self._withhold(folded, line, eol)

    def _open_journal(self) -> dict[str, int]:
        """Start recording the registrations of one line (placeholders, alias keys), with the counters as they were."""
        self._journal = []
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
        self.counters = counters

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
            for label, pattern in _patterns_for(cur):
                self._over_budget(self._scan_deadline)
                cur = pattern.sub(lambda m, label=label: mask(m, label), cur)
        return f"{FOLD_NOTE} {' '.join(dict.fromkeys(hits))}{eol}" if hits else line

    def _mask(self, m: re.Match[str], label: str) -> str:
        """One match of `label`'s pattern, its value replaced by its placeholder (a new one when it is new). Registers the
        FOLDED spelling: used by the direct pass and by `_withhold` (the written spelling of a withheld line cannot be located)."""
        res = self._mask_ex(m, label)
        return m.group(0) if res is None else m.group(0).replace(*res)

    def _decide(self, m: re.Match[str], label: str) -> str | None:
        """Is this match a hit? The sensitive value, or ``None`` when the match is left alone. Registers nothing."""
        # group(1) exists for TENANT, where only the value is sensitive, not the key name.
        # The first group that took part: a pattern may offer the value in several written forms.
        original = next((g for g in m.groups() if g is not None), m.group(0))
        clean = original.replace(
            GAP, ""
        )  # the value as the checks below read it; ``original`` keeps its GAPs (it is found again in the match)
        if label == "SECRET" and (
            clean.lower().strip(".,;:)(<>") in _NOT_A_VALUE or _SAYS_NONE.fullmatch(clean)
        ):
            return None
        if label == "HOSTNAME" and _KEPT_HOST.search(
            clean
        ):  # a name WARDEN reads and acts on, or AWS's own
            return None
        # An account is a bank's only beside a bank word; a grouped card number is left to CREDITCARD (a secret).
        if label == "BANKACCT" and (
            _CARD_SHAPE.fullmatch(clean) or not (self.bank_near or _bank_context(m))
        ):
            return None
        # A value holding placeholders already placed (`Cookie: a=<JWT_1>; sid=...`) is stored restored,
        # so restore() gives the original back in one step; one that is nothing but placeholders is
        # masked already (seventh review: excluding `<` instead left the cookies after it in clear).
        # By its shape, not the map: the gate re-scans with a fresh one, and took `Cookie: <SECRET_1>` for a
        # new secret - every report quoting a masked cookie was withheld (eighth review, 2026-10-01).
        if _PLACEHOLDER.search(clean) and not re.search(
            r"[A-Za-z0-9]", _PLACEHOLDER.sub("", clean)
        ):
            return None
        return original

    def _mask_ex(self, m: re.Match[str], label: str) -> tuple[str, str] | None:
        """``_mask`` without the replacing: (the sensitive value, its placeholder), or ``None`` when the match is left alone."""
        original = self._decide(m, label)
        if original is None:
            return None
        clean = original.replace(GAP, "")  # what is registered never holds a GAP
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), clean)
        placeholder = (
            self.reverse[full] if full in self.reverse else self._place(label, full, clean)
        )
        return original, placeholder

    def _place(self, label: str, full: str, original: str) -> str:
        """A new placeholder for `full`; for a secret kind, one too for each secret-shaped piece of it."""
        self.counters[label] += 1
        placeholder = f"<{label}_{self.counters[label]}>"
        self.mapping[placeholder] = full
        self.reverse[full] = placeholder
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

    def _build(self) -> None:
        # the alias index: the folded spelling of every stored value that is not ASCII and differs from its fold; its keys
        # become sweep rules too, so a clear copy of a masked written variant is masked (one fold per stored value)
        alias: dict[str, str] = {}
        for placeholder, original in self.mapping.items():
            if _plain(original):
                continue
            if self._deadline is not None:
                self._over_budget(self._deadline)
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

    def sweep(self, out: str) -> str:
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
        if self._built_for != len(self.mapping):
            self._build()
        parts = _PLACEHOLDER.split(
            out
        )  # even indices = free text, odd indices = whole placeholders
        for i in range(0, len(parts), 2):
            segment = parts[i]
            if not segment:
                continue
            present = {w for w in self._slow if w in segment}
            for finder, prefixes in self._finders:
                found = {m.group(1) for m in finder.finditer(segment)}
                present |= found.union(*(prefixes.get(w, ()) for w in found))
            todo = sorted((self._rules[o] for o in present if o in self._rules), key=lambda r: r[0])
            todo = [(self._ordered[n][1], ph, rule) for n, ph, rule in todo]
            for original, placeholder, rule in todo:
                if original not in segment:
                    continue
                if rule is _EVERY_COPY:
                    segment = segment.replace(original, placeholder)
                else:
                    segment = _replace_standalone(segment, original, placeholder)
            parts[i] = segment
        return "".join(parts)


_MAX_NESTING = 200


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
    items: list[str], mapping: dict[str, str] | None = None, *, near: tuple[str, ...] = ()
) -> tuple[list[str], dict[str, str]]:
    """Redact several strings as ONE text, with one placeholder namespace: a value found in any of them
    is masked in all of them. One pass left a secret found in a later line in clear in the earlier
    ones (second review, 2026-09-30); the first pass now only finds, the second masks.
    `near`: texts not redacted here whose bank words still count as bank context (a discussion's evidence)."""
    r = _Redactor(mapping)
    r.bank_near = any(_has_bank_word(strip_ansi(t)) for t in (*items, *near))
    found = [r.find(item) for item in items]
    return [r.sweep(text) for text in found], r.mapping
