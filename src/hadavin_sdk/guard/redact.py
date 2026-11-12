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

import re
import string
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.guard import hidden
from hadavin_sdk.guard.hidden import strip_sequences

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
    # A whole PEM private key block — the highest-value secret that turns up in a misconfig dump.
    # PEM and PGP. A key cut off by a line-length limit has no END line: mask to the end.
    (
        "PRIVKEY",
        re.compile(
            r"-----BEGIN[A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----[\s\S]*?"
            r"(?:-----END[A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|\Z)"
        ),
    ),
    # PuTTY: the key lines - at least one character, then up to the Private-MAC line or the end of the text.
    (
        "PRIVKEY",
        re.compile(r"Private-Lines:[ \t]*\d+[ \t]*\r?\n([\s\S](?:(?!\r?\nPrivate-MAC)[\s\S])*)"),
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


def strip_ansi(text: str) -> str:
    """Escape sequences removed; a space where a run of them stood between two word characters, so a boundary stays.
    The one reader of escape sequences is `guard.hidden` (every family of the grammar, with written rules for strings
    that never end and for control characters inside a sequence): this function keeps its name and its callers."""
    return strip_sequences(text)


# At most this many values a text may need masked by their gap pattern (a hostile text must not make the search long).
MAX_DECODED_MASKS = 256
WITHHELD_NOTE = "(details withheld)"  # what a direct caller is given when a reading cannot be masked (never the joined text)


def gap_pattern(value: str) -> re.Pattern[str]:
    """The value as the spaced reading can hold it: its characters, with ONE optional space between two neighbouring
    word characters (a run of hidden items between two word characters left exactly one space there, so no optional
    space ever competes with a character of the value: at each position there is at most one way to go on, and a search is
    linear). A value of fewer than 4 characters is matched only as a whole word, as the redactor's sweep does."""
    parts = []
    for i, c in enumerate(value):
        if i and hidden.is_word(value[i - 1]) and hidden.is_word(c):
            parts.append(" ?")
        parts.append(re.escape(c))
    body = "".join(parts)
    return re.compile(body if len(value) >= 4 else r"(?<!\w)" + body + r"(?!\w)")


_GAP = re.compile(
    r"[\s" + hidden.IGNORABLE_RE.pattern[1:-1] + "]"
)  # what may stand between the characters of a spaced-out value: any space, tab, line break or ignorable character


class _SpacedIndex:
    """The values `spaced_spans` looks for, as an Aho-Corasick automaton (Aho and Corasick 1975, "Efficient string matching: an
    aid to bibliographic search"): ONE pass over the compact text finds every value, whatever the values share. The batch 9
    index (a dictionary keyed by the first 12 characters, then `startswith` on each value of the bucket) cost the text times the
    bucket size when many values share their first 12 characters (batch 9 review, finding F6). Built once per set of values;
    `bool(index)` is False when no value is looked for."""

    __slots__ = ("_fail", "_go", "_link", "_term")

    def __init__(self, values: Iterable[str]) -> None:
        go: list[dict[str, int]] = [{}]
        term: list[str | None] = [None]
        for v in dict.fromkeys(values):
            if len(v) < defaults.SPACED_VALUE_MIN_CHARS or _GAP.search(v) is not None:
                continue  # a shorter value would match ordinary text; one that holds a space is not looked for here
            node = 0
            for c in v:
                nxt = go[node].get(c)
                if nxt is None:
                    go.append({})
                    term.append(None)
                    nxt = go[node][c] = len(go) - 1
                node = nxt
            term[node] = v
        fail = [0] * len(go)
        link = [0] * len(go)  # the nearest proper-suffix node that ends a value (0 = none)
        queue = list(go[0].values())
        # breadth first: a node's failure node is shallower, so it is done already
        for node in queue:
            for c, child in go[node].items():
                f = fail[node]
                while f and c not in go[f]:
                    f = fail[f]
                fail[child] = go[f].get(c, 0)
                link[child] = fail[child] if term[fail[child]] is not None else link[fail[child]]
                queue.append(child)
        self._go, self._fail, self._term, self._link = go, fail, term, link

    def __bool__(self) -> bool:
        return any(t is not None for t in self._term)

    def longest_ending_at_each_position(self, compact: str) -> list[tuple[int, str]]:
        """(end, value) for each position of `compact` where at least one value ends: the LONGEST such value. A shorter value
        that ends at the same place lies inside the longer one's span, and `mask_spans` drops a span inside another (rule 1), so
        the masked text is the same while the number of results stays at most one per character."""
        go, fail, term, link = self._go, self._fail, self._term, self._link
        found: list[tuple[int, str]] = []
        node = 0
        for i, c in enumerate(compact):
            while node and c not in go[node]:
                node = fail[node]
            node = go[node].get(c, 0)
            v = term[node]
            if v is None and link[node]:
                v = term[link[node]]
            if v is not None:
                found.append((i + 1, v))
        return found


_NO_SPACED = _SpacedIndex(())


def spaced_index(values: Iterable[str]) -> _SpacedIndex:
    """The values `spaced_spans` looks for (built once for many texts): a value of fewer than `SPACED_VALUE_MIN_CHARS`
    characters, or one that holds a space, is not looked for spaced out."""
    return _SpacedIndex(values)


def spaced_spans(
    text: str, values: Iterable[str], *, index: _SpacedIndex | None = None
) -> list[tuple[int, int, str]]:
    """The copies of each KNOWN value in `text` that are written with a space between characters (`A K I A ...`, a hyphen
    value too): (start, end, value) in `text`. A value is known when the run holds it (the map) or it was handed to a tool, so
    no product choice exists: with the spaces taken out of the text, the only way to hold a value of `SPACED_VALUE_MIN_CHARS`
    or more characters is to be that value. Only copies that hold at least one space are returned (a copy without a space is
    found by the plain search). The text is compacted once and searched in ONE pass by the automaton of `_SpacedIndex`: the cost
    is linear in the text plus the values, whatever the values share (batch 10, group 1: the batch 9 index was quadratic for
    values that share their first 12 characters). Where several values end at one place the longest is returned (the others lie
    inside it and the masking drops them). The positions of the compact text are mapped back to `text`. `index` is
    `spaced_index(values)` when the caller has built it once for several texts."""
    if _GAP.search(text) is None:
        return []
    index = spaced_index(values) if index is None else index
    if not index:
        return []
    pos = [i for i, c in enumerate(text) if _GAP.fullmatch(c) is None]
    compact = "".join(text[i] for i in pos)
    found: list[tuple[int, int, str]] = []
    for end, v in index.longest_ending_at_each_position(compact):
        a, b = pos[end - len(v)], pos[end - 1] + 1
        if b - a > len(v):  # a space stands inside the copy
            found.append((a, b, v))
    return found


class SpacedRunLimit(Exception):
    """A text holds more runs of spaced-out characters than `defaults.SPACED_RUN_MAX_RUNS`: the caller withholds the text (never
    skips the runs it did not read)."""


# one single character that is neither white space nor an ignorable character (a zero-width one, a variation selector ...)
_IGN = hidden.IGNORABLE_RE.pattern[1:-1]  # the body of the class: ranges only
_TOK = rf"[^\s{_IGN}]"
_SEP = rf"[\s{_IGN}]+"
# A "word character" here is a letter, a digit or a combining mark (Unicode categories L, N and M). A run of single characters may
# not stand glued to one (`ab c d e ...` is the end of a longer word, not a spaced value), but EVERY other character glued to
# its first or last character is a wrapper that is no part of the value: a code span, bold, quotes of any language (curly,
# angle, corner), a currency sign or a hash or an at sign, a slash, a backslash, a percent sign, a dash, a bracket. One category
# rule, not a list of characters (batch 11, group 1: the batch 10 list of 9 wrapper characters ended the run one token early for
# every character it did not hold, and a spaced value stayed readable). Letters exist only in planes 0 to 3 and 14: only those
# are scanned (a test derives the set over all code points and compares).
_WORD_PLANES = (range(0x32400), range(0xE0000, 0xE1000))
_IGNORABLE_CHAR = re.compile(hidden.IGNORABLE_RE.pattern)


def _word_class_body() -> str:
    spans: list[list[int]] = []
    for plane in _WORD_PLANES:
        for c in plane:
            if unicodedata.category(chr(c))[0] not in "LNM" or _IGNORABLE_CHAR.fullmatch(chr(c)):
                continue  # a gap character (variation selector, U+034F, the filler letters) is no part of a word (batch 12, issue 6)
            if spans and spans[-1][1] == c - 1:
                spans[-1][1] = c
            else:
                spans.append([c, c])
    return "".join(rf"\U{lo:08x}-\U{hi:08x}" for lo, hi in spans)


_WORD_BODY = _word_class_body()
_NOT_BEFORE = f"[{_WORD_BODY}]"  # what may NOT stand right before a run (a lookbehind)
# what may follow a run: any characters that are no word character and no separator, then a separator or the end of the text
# (never a longer word)
_RUN_AFTER = rf"(?=[^\s{_IGN}{_WORD_BODY}]*(?:[\s{_IGN}]|$))"
_SPACED_RUN = re.compile(
    rf"(?<!{_NOT_BEFORE}){_TOK}(?:{_SEP}{_TOK}){{{defaults.SPACED_RUN_MIN_TOKENS - 1},}}{_RUN_AFTER}"
)
# the same with a visible separator between alphanumeric characters (`A-K-I-A`, `A - K - I - A`, `A, K, I, A`)
_PUNCT_SEP = r"[-_.,|/:;]"
_SPACED_RUN_PUNCT = re.compile(
    rf"(?<!{_NOT_BEFORE})[A-Za-z0-9](?:[\s{_IGN}]*{_PUNCT_SEP}[\s{_IGN}]*[A-Za-z0-9]){{{defaults.SPACED_RUN_MIN_TOKENS - 1},}}{_RUN_AFTER}"
)
_TOKEN_AT = re.compile(_TOK)
_RUN_END_PUNCT = ".,;:)]\"'!?"


def _runs_of(text: str) -> list[tuple[int, int, list[str], list[int]]]:
    """(start, end, tokens, token starts) of each candidate run of single characters in `text`, both spellings of the separator."""
    found: list[tuple[int, int, list[str], list[int]]] = []
    for rx in (_SPACED_RUN, _SPACED_RUN_PUNCT):
        for m in rx.finditer(text):
            toks, starts = [], []
            for t in _TOKEN_AT.finditer(m.group()):
                if rx is _SPACED_RUN_PUNCT and t.group() in "-_.,|/:;":
                    continue
                toks.append(t.group())
                starts.append(m.start() + t.start())
            # trailing punctuation belongs to the sentence, not to the value (`A K I A ... E.`)
            while len(toks) > defaults.SPACED_RUN_MIN_TOKENS and toks[-1] in _RUN_END_PUNCT:
                toks.pop()
                starts.pop()
            if len(toks) >= defaults.SPACED_RUN_MIN_TOKENS:
                found.append((starts[0], starts[-1] + 1, toks, starts))
    return found


def spaced_unknown(
    text: str, charge: Callable[[int], None] | None = None
) -> list[tuple[int, int, str]]:
    """The runs of `SPACED_RUN_MIN_TOKENS` or more single-character tokens whose collapsed text (the separators out) the
    patterns read as a secret of a SECRET kind: (start, end, collapsed text) in `text`. The separator is any white space or
    ignorable character, one or more (two spaces, a tab, a new line, a no-break space, a zero-width character), or a visible
    `- _ . , | / : ;` between letters and digits. A run is read (1) as it stands, (2) together with the up to
    `defaults.SPACED_CONTEXT_CHARS` characters before it (`password=` + a spaced value), (3) without its first one, two or three tokens (a
    one-letter word in front: `a A K I A ...`); a value glued to its key (`key=A K I A`) starts the run. Trailing punctuation
    is not part of the run. Only values the patterns READ are found: an unknown value of no pattern's shape written with
    spaces is not (SECURITY.md). A run needs `SPACED_RUN_MIN_DISTINCT` different characters. More than
    `defaults.SPACED_RUN_MAX_RUNS` candidate runs, or more than `defaults.SPACED_READ_MAX_CHARS` characters to read in all
    (a run is long, or there are many), in one text raise `SpacedRunLimit` (the text is withheld; batch 10, group 1). CHECK-ONLY reading:
    the caller decides whether to act (`defaults.READ_SPACED_OUT_UNKNOWN`). Cost: one regular-expression pass per spelling, and
    at most `defaults.SPACED_DROP_MAX` reads of each run, all counted in characters against the budget BEFORE they run. `charge`
    (the caller's running count of the whole call, over every view) is told the characters of each read before it runs and may
    raise `SpacedRunLimit`."""
    out: list[tuple[int, int, str]] = []
    # the starts of the candidate runs counted against `SPACED_RUN_MAX_RUNS`
    counted: set[int] = set()
    work = 0  # characters the pattern reads below will scan (`defaults.SPACED_READ_MAX_CHARS`)
    for start, end, toks, starts in sorted(_runs_of(text)):
        if len(set(toks)) < defaults.SPACED_RUN_MIN_DISTINCT:
            continue
        # one run that BOTH spellings of the separator match (`A - K - I`) counts once (batch 10, group 6)
        if start not in counted:
            counted.add(start)
            if len(counted) > defaults.SPACED_RUN_MAX_RUNS:
                raise SpacedRunLimit
        for drop in range(defaults.SPACED_DROP_MAX):
            rest = toks[drop:]
            if (
                len(rest) < defaults.SPACED_RUN_MIN_TOKENS
                or len(set(rest)) < defaults.SPACED_RUN_MIN_DISTINCT
            ):
                break
            token = "".join(rest)
            context = text[max(0, start - defaults.SPACED_CONTEXT_CHARS) : start]
            # the work budget counts what the reads below will scan, BEFORE they run: the token alone, and with a context the
            # context alone and the context plus the token (`_reads_as_secret`); over the budget the text is withheld
            cost = len(token) + (2 * len(context) + len(token) if context else 0)
            work += cost
            if work > defaults.SPACED_READ_MAX_CHARS:
                raise SpacedRunLimit
            if charge is not None:
                charge(
                    cost
                )  # the call's own work count and clock (batch 11, group 5): it may raise `SpacedRunLimit`
            if _reads_as_secret(token, context):
                out.append((starts[drop], end, token))
                break
    return out


def _reads_as_secret(token: str, context: str) -> bool:
    """Do the patterns read `token` (alone, or after `context`) as a value of a SECRET kind? With context: a secret value that
    the context alone does not hold."""
    finder = _Redactor(None, None)  # not the bare `redact()`: the repo guard lists who may call it
    finder.find(token, readings=False)
    if any(_kind(ph) in SECRET_KINDS for ph in finder.mapping):
        return True
    if not context:
        return False
    alone = _Redactor(None, None)
    alone.find(context, readings=False)
    before = set(alone.mapping.values())
    both = _Redactor(None, None)
    both.find(context + token, readings=False)
    return any(
        _kind(ph) in SECRET_KINDS and v not in before and v not in context
        for ph, v in both.mapping.items()
    )


def collapse_runs(text: str, runs: list[tuple[int, int, str]]) -> str:
    """`text` with each run of `spaced_unknown` replaced by its collapsed text (the spaces out)."""
    out: list[str] = []
    at = 0
    for a, b, token in runs:
        # an underscore next to the run is a word character: glued to the collapsed value it would hide the value from the patterns'
        # word boundary (`_A K I A ... E_` italic), so a space stands between them in this view (batch 10, group 5)
        out += [
            text[at:a],
            " " if text[a - 1 : a] == "_" else "",
            token,
            " " if text[b : b + 1] == "_" else "",
        ]
        at = b
    out.append(text[at:])
    return "".join(out)


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
    _readings: bool = True,
) -> RedactionResult:
    """Scrub `text`, then prove the scrub worked.

    Passing an existing `mapping` keeps placeholders stable across many strings in one run, so the
    model still sees that two log lines refer to the same host. `near`: related texts redacted apart
    (a record's other fields) whose bank words still count as bank context here, as in redact_many.

    A text with escape sequences is read in the readings `_Redactor.find` lists (PR H): a key cut by `ESC ( B ESC [ m` is
    masked, and a value the map already holds that an escape cut in one copy (`ESC` or a C1 opener + value) returns
    `WITHHELD_NOTE`. Batch 7: a text that also holds a bell, a zero-width, a bidirectional or another ignorable character
    is read in that reading too (`runmap.canonical`'s view); two readings that mask different values return `WITHHELD_NOTE`
    (rule: `compare_readings`). A combining mark (U+0301) is NOT a hidden item: it changes the character, so a key with one
    inside is a different string and is left as written (decision d6, pinned in `tests/test_prh_b7.py`).
    """
    r = _Redactor(mapping, _cache)
    r.bank_near = any(_has_bank_word(strip_ansi(t)) for t in near)
    out = r.find(text, readings=_readings, swept=_sweep_copies)
    if _sweep_copies:  # redact_many's first pass only FINDS values; its second pass masks
        out = r.sweep(out)
    return RedactionResult(text=out, mapping=r.mapping)


def compare_readings(first: set[str], second: set[str]) -> str:
    """The ONE rule that folds two readings of a text, each masked on its own (the direct `redact()` asks it; `runmap._consuming_wins`
    has its own window rule and does not call it: its call could never answer "conflict", batch 8 issue 2). `first` and `second` are the sets of VALUES each reading masked. A reading COVERS
    the other when every value the other masks stands inside (or is) a value this one masks: a reading that glued a word to
    a key finds a few digits of the key as a phone number; the reading that found the whole key covers it.
    * "same": equal sets, or each covers the other (the caller keeps the one that masks more copies);
    * "second": the second covers the first and not the other way round (it saw what the first could not read);
    * "first": the first covers the second and not the other way round;
    * "conflict": neither covers the other (an escape that took the first letter of one value in one reading and not in the
      other): the readings cannot be merged, so the caller shows nothing (`WITHHELD_NOTE`, or a refusal)."""
    if first == second:
        return "same"
    covers_first = all(any(v in w for w in second) for v in first)  # `second` covers `first`
    covers_second = all(any(v in w for w in first) for v in second)  # `first` covers `second`
    if covers_first and covers_second:
        return "same"
    if covers_first:
        return "second"
    if covers_second:
        return "first"
    return "conflict"


def _countable(suffix: str) -> bool:
    """A placeholder number the counter can take: ASCII digits, at most 18 of them. A longer one (a record can hold any text)
    would make int() refuse it past 4,300 digits, and no counter reaches it (CodeRabbit, PR 147)."""
    return suffix.isascii() and suffix.isdigit() and len(suffix) <= 18


class _Redactor:
    """One placeholder namespace (map, reverse map, counters) shared by every text of one call."""

    def __init__(self, mapping: dict[str, str] | None, cache: dict | None = None) -> None:
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
        self._rules: dict[str, tuple[int, str, Any]] = {}
        self._finders: list[tuple[re.Pattern[str], dict[str, list[str]]]] = []
        self._slow: list[str] = []  # values checked one by one: nested too deep for the finder
        self._ordered: list[tuple[str, str]] = []
        self._spaced: _SpacedIndex | None = (
            None  # the automaton of the known secrets, built when a sweep first needs it
        )
        self.bank_near = False  # redact_many: a bank word in some string of the batch
        if cache and cache.get("map") == self.mapping:  # nothing new since the last build: skip it
            self._ordered, self._rules, self._finders, self._slow = cache["state"]
            self._spaced = cache.get(
                "spaced"
            )  # built once per map version, like the finders (batch 11, group 5)
            self._built_for = len(self.mapping)

    def _patterns(self, text: str) -> str:
        for label, pattern in PATTERNS:
            text = pattern.sub(lambda m, label=label: self._mask(m, label), text)
        return text

    def find(self, text: str, readings: bool = True, swept: bool = True) -> str:
        """Every value the patterns find, replaced by its placeholder. The one choke point of every caller of `redact` and
        `redact_many`, so the escape sequences in `text` are read here (PR H), in two readings:

        * the *joined* reading (sequences removed, nothing left in their place): values are FOUND in it;
        * the *spaced* reading (one space where a sequence stood between two word characters): the text the reader is
          given, so values the joined reading found are MASKED in it, by their gap pattern;
        * the same two readings when every sequence takes its final byte (`ESC ( B`): used when they mask more values
          (batch 6: a key cut by `ESC ( B ESC [ m` is masked, it used to stay readable);
        * a value the map held before this call that the character reading or the consuming reading shows more often than
          the joined reading (an ESC took the first letter of one copy) cannot be masked there: `WITHHELD_NOTE`;

        A value found in the joined reading that the spaced reading cannot show whole (or more than `MAX_DECODED_MASKS` of
        them) fails closed: `WITHHELD_NOTE` is returned, never the joined text (it has lost the word boundaries the
        sequences made, so a key glued to the word before it would read as part of that word). Inside `redact_text` no
        escape sequence is left, so this is reached only by a direct caller of `redact()` or `redact_many()`."""
        if not readings:  # `runmap` calls with text it has already read (no sequence left): one reading, as before
            return self._patterns(text)
        joined, spaced = hidden.sequence_readings(text)
        # every other reading of this text that can differ: only when it holds a sequence opener (ESC or a C1 opener, not only
        # ESC: batch 7), or a hidden item the sequence reader leaves (a bell, a zero-width or a bidirectional character)
        has_seq = hidden.SEQ_ANY.search(text) is not None
        # as `runmap.canonical` does: ignorable characters do not count
        plain_text = hidden.IGNORABLE_RE.sub("", text)
        fj, fs = hidden.strip(plain_text)
        if not has_seq and plain_text == text and hidden.ANY.search(text) is None:
            return (
                self._patterns(spaced) if joined == spaced else self._find_readings(joined, spaced)
            )
        known = [v for v in self.mapping.values() if len(v) >= 4 and not v.startswith("\0seed")]
        out = self._patterns(spaced) if joined == spaced else self._find_readings(joined, spaced)
        # the first reading refused the text (too many values to pair): no other reading may replace it
        if out == WITHHELD_NOTE:
            return WITHHELD_NOTE
        verdict = out
        # the readings, each masked on its own, are folded by ONE rule (`compare_readings`; `runmap._consuming_wins`
        # has its own window rule): the one that masks more values wins when it masks every value the other masks; two
        # readings that mask different values, or a tie with different values, are not merged: `WITHHELD_NOTE`
        folded: list[tuple[str, str]] = []
        if has_seq:
            # the consuming reading (a sequence takes its final byte, a letter too: `ESC ( B ESC [ m` is what `tput sgr0` writes)
            cj, cs = hidden.strip_consuming(plain_text)
            if (cj, cs) != (joined, spaced):
                folded.append((cj, cs))
        # the SOFT readings: the keeping reading (an ESC that opens no sequence takes nothing after it: `ESC` + a key keeps its
        # first letter, which the grammar's reading eats as a C1 function), and the character reading when the text holds no
        # sequence body for it to show (`hidden.leaves_text`: `U+009B` + a key). Neither shows a body. They are folded by the
        # same rule, except that a CONFLICT is not a refusal: the grammar's output stays unless a stretch of a value the soft
        # reading masks still stands in it (an ordinary text with `ESC M` in it is not withheld for the letter it kept)
        chars_j, chars_s = hidden.characters_readings(
            text
        )  # computed once; the soft rule below reads it too
        soft: list[tuple[str, str]] = []
        if has_seq:
            kj, ks = hidden.strip_keeping(plain_text)
            if (kj, ks) != (joined, spaced) and (kj, ks) not in folded:
                soft.append((kj, ks))
        if not hidden.leaves_text(text):
            cj_, cs_ = (
                (chars_j, chars_s) if plain_text is text else hidden.characters_readings(plain_text)
            )
            if (
                (cj_, cs_) != (joined, spaced)
                and (cj_, cs_) not in folded
                and (cj_, cs_) not in soft
            ):
                soft.append((cj_, cs_))
        folded += soft
        if (
            (plain_text != text or hidden.ANY.search(text) is not None)
            and (fj, fs) != (joined, spaced)
            and (fj, fs) not in folded
        ):
            folded.append((fj, fs))
        # the character reading (every hidden character deleted on its own, no sequence read as one): a string sequence a bell
        # or a line end does not close (`U+0090` ... `BEL`) swallows the rest of the line in the grammar's reading, and a key
        # cut by it shows only its front there (batch 7 resume). It is a CHECK, never the result: a value only it can read
        # withholds the text; a text with no open string sequence is not read in it (a closed one is `ESC [ 0 m`: ordinary).
        open_string = hidden.has_open_string(text)
        check_only = (
            (chars_j, chars_s)
            if open_string and (chars_j, chars_s) not in [(joined, spaced), *folded]
            else None
        )
        if check_only is not None:
            folded.append(check_only)
        by_any: set[str] = set()  # the values every reading masked (read once the choice is made)
        for rj, rs in folded:
            alt = self._patterns(rs) if rj == rs else self._find_readings(rj, rs)
            if alt == WITHHELD_NOTE:
                return WITHHELD_NOTE
            by_any |= self._held_values(alt)
            choice = compare_readings(self._held_values(verdict), self._held_values(alt))
            if choice == "conflict" and (rj, rs) in soft:
                if self._stands_in(self._held_values(alt), verdict):
                    return WITHHELD_NOTE
                continue
            if choice == "conflict":
                return WITHHELD_NOTE
            if (rj, rs) == check_only:
                # the character reading holds a value the grammar's reading cannot read (an unterminated string sequence
                # blanked it) and shows the text that reading removed: its output is never the result. The grammar's output
                # is kept when no stretch of 4 characters of that value stands in it (the value sat only inside the removed
                # body, which is not shown); a front of the value that stands before the opener (`AKIA` + opener + the rest)
                # withholds the text (narrowed from "always withhold", batch 9, group 3).
                # Batch 10, group 5: the same test whatever the two readings mask ("same" and "first" too) and for a value of a
                # SECRET kind that the grammar's reading masks in another copy too: a plain copy of the value elsewhere in the text
                # made the difference empty, so the front standing before the opener was kept
                held_alt, held_verdict = self._held_values(alt), self._held_values(verdict)
                seen_by_both = {
                    v
                    for v in held_alt & held_verdict
                    if _kind(self.reverse.get(v, "")) in SECRET_KINDS
                }
                if self._stands_in((held_alt - held_verdict) | seen_by_both, verdict, 4):
                    return WITHHELD_NOTE
                continue  # a check only: the character reading's output shows removed text and is never the result
            if choice == "second" or (
                choice == "same"
                and len(_PLACEHOLDER.findall(alt)) > len(_PLACEHOLDER.findall(verdict))
            ):
                verdict = alt
        # a value the map already held that another reading shows more often than the grammar's reading (an ESC that takes
        # the letter after it cut one copy: `ESC` + value) is not masked in either output: nothing is shown
        others = (chars_j, *(r[0] for r in folded), fj)
        if any(r.count(v) > joined.count(v) for v in known for r in others):
            return WITHHELD_NOTE
        # a value ANY reading masked must not stand in the output: two readings can each mask a different copy of one value
        # (`ESC ( B` + `1.2.3.4` next to `1.2` + `ESC .` + `3.4`: the grammar's reading masks the second copy, the consuming
        # reading the first), and neither output holds both (class: a copy the chosen reading could not read, PR H batch 9)
        # (batch 10, group 4: only a copy the sweep that follows would NOT mask counts. `swept` is False for a caller that does not
        # sweep. A bare second copy of a secret (`login hunter2 failed`) is masked by the sweep, so it is not a reason to withhold)
        masked_by_any = self._held_values(verdict) | by_any
        if any(self._copy_stays(v, verdict, swept) for v in masked_by_any if len(v) >= 4):
            return WITHHELD_NOTE
        return verdict

    def _copy_stays(self, value: str, shown: str, swept: bool) -> bool:
        """Does a copy of `value` stand in `shown` that the sweep (`_sweep`, `_occurrences`) will not mask? With no sweep every
        copy stays."""
        if value not in shown:
            return False
        if not swept:
            return True
        # the rule of the placeholder the sweep itself uses for this value (`_build`: the first one in the map order that has a
        # rule), not the last one of the reverse map: a value held under two placeholders of different kinds is swept by one
        # of them only (batch 11, group 6)
        if self._built_for != len(self.mapping):
            self._build()
        entry = self._rules.get(value)
        if entry is None:
            return True
        _, ph, rule = entry
        every = rule is _EVERY_COPY
        return len(_occurrences(shown, value, ph, True)) > len(
            _occurrences(shown, value, ph, every)
        )

    @staticmethod
    def _stands_in(values: set[str], shown: str, width: int = 8) -> bool:
        """Does a stretch of `width` characters of any of `values` stand in `shown`? Linear in the text for each value. A value
        shorter than `width` has no such stretch; the final guard of `find` (a whole value of 4 or more characters that any reading
        masked) covers it (batch 9, group 8)."""
        return any(v[i : i + width] in shown for v in values for i in range(len(v) - width + 1))

    def _held_values(self, shown: str) -> set[str]:
        """The values whose placeholders stand in `shown` (the readings are compared by what they mask)."""
        return {self.mapping[ph] for ph in _PLACEHOLDER.findall(shown) if ph in self.mapping}

    def _find_readings(self, joined: str, spaced: str) -> str:
        found = self._patterns(joined)
        held = {
            ph
            for ph in dict.fromkeys(_PLACEHOLDER.findall(found))
            if ph in self.mapping and found.count(ph) > joined.count(ph)
        }
        needed = [
            self.mapping[ph]
            for ph in held
            if not self.mapping[ph].startswith("\0seed")
            and (
                self.mapping[ph] not in spaced
                # a value that stands whole in one place and cut in another (`AK` + `ESC I` + `AIOS...` next to a plain copy):
                # the sweep masks the whole copy only, so the cut one is needed too (counted per copy, not per value, as
                # `runmap._redact_stripped` does; class: a cut copy beside a plain one, PR H batch 8 issue 3)
                or spaced.count(self.mapping[ph]) < joined.count(self.mapping[ph])
            )
        ]
        if len(needed) > MAX_DECODED_MASKS:
            return WITHHELD_NOTE
        spans: list[tuple[int, int, str]] = []
        for ph in held:
            if self.mapping[ph] in needed:
                matches = list(gap_pattern(self.mapping[ph]).finditer(spaced))
                if not matches:
                    return WITHHELD_NOTE
                spans.extend((m.start(), m.end(), ph) for m in matches)
        masked = mask_spans(spaced, spans, self.mapping, _redactor=self) if spans else spaced
        return self._patterns(masked)

    def _mask(self, m: re.Match[str], label: str) -> str:
        """One match of `label`'s pattern, its value replaced by its placeholder (a new one when it is new)."""
        # group(1) exists for TENANT, where only the value is sensitive, not the key name.
        # The first group that took part: a pattern may offer the value in several written forms.
        original = next((g for g in m.groups() if g is not None), m.group(0))
        if label == "SECRET" and (
            original.lower().strip(".,;:)(<>") in _NOT_A_VALUE or _SAYS_NONE.fullmatch(original)
        ):
            return m.group(0)
        if label == "HOSTNAME" and _KEPT_HOST.search(
            original
        ):  # a name WARDEN reads and acts on, or AWS's own
            return m.group(0)
        # An account is a bank's only beside a bank word; a grouped card number is left to CREDITCARD (a secret).
        if label == "BANKACCT" and (
            _CARD_SHAPE.fullmatch(original) or not (self.bank_near or _bank_context(m))
        ):
            return m.group(0)
        # A value holding placeholders already placed (`Cookie: a=<JWT_1>; sid=...`) is stored restored,
        # so restore() gives the original back in one step; one that is nothing but placeholders is
        # masked already (seventh review: excluding `<` instead left the cookies after it in clear).
        full = _PLACEHOLDER.sub(lambda p: self.mapping.get(p.group(1), p.group(1)), original)
        # By its shape, not the map: the gate re-scans with a fresh one, and took `Cookie: <SECRET_1>` for a
        # new secret - every report quoting a masked cookie was withheld (eighth review, 2026-10-01).
        if _PLACEHOLDER.search(original) and not re.search(
            r"[A-Za-z0-9]", _PLACEHOLDER.sub("", original)
        ):
            return m.group(0)
        placeholder = (
            self.reverse[full] if full in self.reverse else self._place(label, full, original)
        )
        return m.group(0).replace(original, placeholder)

    def _place(self, label: str, full: str, original: str) -> str:
        """A new placeholder for `full`; for a secret kind, one too for each secret-shaped piece of it."""
        self.counters[label] += 1
        placeholder = f"<{label}_{self.counters[label]}>"
        self.mapping[placeholder] = full
        self.reverse[full] = placeholder
        for piece in (
            _PIECE.findall(_PLACEHOLDER.sub(" ", original)) if label in SECRET_KINDS else ()
        ):
            if piece != full and piece not in self.reverse and _secret_shaped(piece):
                self.counters[label] += 1
                self.mapping[f"<{label}_{self.counters[label]}>"] = piece
                self.reverse[piece] = f"<{label}_{self.counters[label]}>"
        return placeholder

    def _build(self) -> None:
        self._ordered = sorted(self.mapping.items(), key=lambda kv: -len(kv[1]))
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
        self._spaced = None  # a new map version: the automaton is built again when a sweep needs it
        if self._cache is not None:
            self._cache["map"] = dict(self.mapping)
            self._cache["state"] = (self._ordered, self._rules, self._finders, self._slow)
            self._cache.pop("spaced", None)

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
        if self._spaced is None and _GAP.search(out):
            self._spaced = spaced_index(self._secret_values())
            if self._cache is not None and self._cache.get("map") == self.mapping:
                self._cache["spaced"] = self._spaced
        spaced_index_ = self._spaced if self._spaced is not None else _NO_SPACED
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
            # Every copy of every value is a span on the segment AS IT STANDS; one pass then puts the placeholders
            # in (`mask_spans`). Replacing one value after another let the first replacement cut the second value and
            # left a piece of it readable when two values overlapped (PR H, W0).
            spans: list[tuple[int, int, str]] = []
            for original, placeholder, rule in todo:
                spans.extend(_occurrences(segment, original, placeholder, rule is _EVERY_COPY))
            # the copies of a known secret written with a space between its characters (`spaced_spans`)
            spans += [
                (a, b, ph)
                for a, b, v in spaced_spans(segment, (), index=spaced_index_)
                for ph in [self.reverse[v]]
            ]
            if spans:
                parts[i] = mask_spans(segment, spans, self.mapping, _redactor=self)
        return "".join(parts)

    def _secret_values(self) -> list[str]:
        """The values of a secret kind the map holds that are long enough to be looked for spaced out (every copy of them is
        swept, so a spaced copy is swept too)."""
        return [
            v
            for ph, v in self.mapping.items()
            if not v.startswith("\0seed")
            and _kind(ph) in SECRET_KINDS
            and len(v) >= defaults.SPACED_VALUE_MIN_CHARS
            and self.reverse.get(v) == ph
        ]


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


def _occurrences(
    segment: str, original: str, placeholder: str, every_copy: bool
) -> list[tuple[int, int, str]]:
    """Every span of `segment` that holds `original` (overlapping copies included): anywhere for a secret, only where
    no ASCII letter or digit touches it for an identifier. Judged on `segment` as it stands. A plain scan: a compiled
    pattern (or an lru_cache of one) keyed by the identifier would keep one client's values in process memory, shared
    with every other client (R371), and `re` caches compiled patterns itself."""
    out: list[tuple[int, int, str]] = []
    n = len(original)
    if not n:
        return out
    j = segment.find(original)
    while j >= 0:
        if every_copy or not (segment[j - 1 : j] in _ALNUM or segment[j + n : j + n + 1] in _ALNUM):
            out.append((j, j + n, placeholder))
        j = segment.find(original, j + 1)
    return out


def mask_spans(
    text: str,
    spans: Iterable[tuple[int, int, str]],
    mapping: dict[str, str],
    *,
    _redactor: _Redactor | None = None,
) -> str:
    """One rule for every place that puts known values back as placeholders (the redactor's sweep, the decoded views of
    `runmap`, the gap patterns of the stripped reading): `spans` are `(start, end, placeholder)` found on `text` as it
    stands, in priority order (the earlier one wins a tie).

    1. A span that lies inside another kept span is dropped (a nested value: the longer one wins).
    2. A chain of spans that partially overlap (each starts before the previous ends) is ONE merged span.
    3. A merged span of one span gets that span's placeholder; of two or more, ONE placeholder issued for the merged text
       through the redactor's own numbering (kind of the longest member, the leftmost on a tie), or the placeholder the
       map already holds for that exact text, so `restore` gives back exactly the text that was there. Issued entries are
       written into `mapping`.

    Class fixed: values replaced one after another, so the first replacement broke the second value and a piece of it
    stayed readable (partial overlap, equal length, mixed spelling domains)."""
    ordered = sorted(enumerate(spans), key=lambda t: (t[1][0], -t[1][1], t[0]))
    groups: list[list[tuple[int, int, str]]] = []
    reach = -1
    for _, span in ordered:
        start, end, _ph = span
        if groups and start < reach:
            if end > reach:  # not inside the furthest-reaching kept span: it extends the chain
                groups[-1].append(span)
                reach = end
            continue
        groups.append([span])
        reach = end
    if not groups:
        return text
    out: list[str] = []
    pos = 0
    redactor = _redactor
    for members in groups:
        start, end = members[0][0], max(m[1] for m in members)
        out.append(text[pos:start])
        if len(members) == 1:
            out.append(members[0][2])
        else:
            merged = text[start:end]
            if redactor is None:
                redactor = _Redactor(mapping)
            held = redactor.reverse.get(merged)
            if held is None:
                longest = max(members, key=lambda m: (m[1] - m[0], -m[0]))
                label = _kind(longest[2])
                if label not in redactor.counters:
                    label = "SECRET"
                held = redactor._place(label, merged, merged)
            out.append(held)
        pos = end
    out.append(text[pos:])
    if redactor is not None and redactor.mapping is not mapping:
        mapping.update(redactor.mapping)
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
