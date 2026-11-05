"""Invoice checks D06 (arithmetic), D10 (bank detail differs from the one on file), D12 (unexplained long number) and L01 (supplier not on file).

WHAT THIS IS. D10 and D12 are a defense-in-depth TEXT SCAN, not proof. They read the document text itself (model-independent) and
look for numbers that look like supplier payment details. A changed detail written in an unusual form can still pass clean. The
controls are three, and none of them is enough alone: (i) the two-person approval, (ii) the review page, which shows the details
found in the text beside the on-file ones (`bank_detail_findings`), (iii) this scan. It is not `checks.bank_clean` (that one wants
positive evidence of every on-file component; this one flags any candidate that is not an on-file component).
D10 is reject-only: a false D10 means a correct invoice is rejected and there is no override. That is the main cost of this design.
D12 is a person-must-look flag (approvable with a reason); it is on by default in `check`.
Rounds 5-7 (ledger rows BL-intake-wp3-r4/r6): direction controls give the D12 notice `bidi_control` (the raw line with the controls shown),
a payment-instruction lexicon (`PAYMENT_LEXICON`, also other languages and rails without digits), change-notice phrases, hidden or
quoted text, notices for several-line IBANs, unreadable blobs, BIC/IFSC; the invoice number, PO and date explain a number only on a
label-free line; D12 joins like D10; a hit of 6-7 digits under a bare word is the D12 notice `short_account_number` (D10 is for strong
labels, IBANs and 8+ digits); a payment line must have a value of its own (`payment_line_no_number`); every scan fails closed; a text
longer than MAX_TEXT_CHARS is refused with `text_too_large`. Every notice carries the digits (`detail`) and the raw line (`raw`).
The claims are measured on forgeries written by people who had read the code (tests/forgeries2.py is the second set): not proof.

Inputs of `check`: `fields` = a record that is valid and grounded (the pipeline guarantees it; malformed amounts give D06 and D12,
never an exception); `send_text` = exactly the string given to the model, with no fold or other change; `suppliers` = the mapping
returned by `load_suppliers` (keys NFKC-normalised, casefolded and space-collapsed; any other key raises ValueError).
`Finding.candidate` is the FOLDED form (lower case, digits only for numbers). Other modules import only the names in `__all__`.

IBAN_LENGTH: the IBAN registry (ISO 13616 / SWIFT) as published at https://www.iban.com/structure ("Data updated on 8 May 2026")
and compared entry by entry with https://en.wikipedia.org/wiki/International_Bank_Account_Number (registry release 99, Dec 2024),
both fetched 2026-11-03 UTC. Compared: the 89 countries of the registry table in both copies agree in code and length; the second
copy also lists 22 partial or experimental countries (DZ AO BJ BF CV CM CF TD KM CG CI GQ GA GW IR MG ML MA MZ NE SN TG) that are NOT
used (their numbers are only covered by D12). The official swift.com registry file answered HTTP 403 and was NOT read.

Rules (per physical line, on text that is folded, casefolded, mapped through the Unicode confusables data, with every dash code point
as `-`, every slash code point as `/`, every default-ignorable code point (zero-width, Hangul fillers, variation selectors) deleted,
every whitespace run as one space, CR/VT/FF/NEL/LS/PS as a line break; the same on decoded base64, percent and hex forms):
* Line scope. A line holds a bank keyword when a keyword stem occurs ANYWHERE in it, glued or not: sort code, routing, swift,
  clearing, konto, branch code, iban, account/acct/acc/a-c + no/num/number/nr/nbr/id/#, aba, bic, bsb, blz, ifsc, clabe, and the
  WHOLE WORDS account, acct, acc, a/c, a-c (also glued to `bank`: bankacct; or followed by `holder` or `name`), bank, banking,
  bankverbindung(en), bankleitzahl, bankgiro, bankdetail(s), bankdaten, bankinfo(rmation), bankname, banknumber, banknr, bankno, bankcode,
  `A / C`, and accounts/accts only when eight digits follow right after, one separator allowed between digits (`Accounts: 8765 4321`);
  `Accounts No` is a label. The set of spellings has no end. A word that merely contains those letters (Raccoglitori, Accenture, Bankside,
  Riverbank, Accrued, Accountant, `Accounts Payable`, `accounts@...`) is not a label; a CamelCase word is split first
  (`BankAccountNo`). Then EVERY digit run on that line, on the
  next non-blank line (within 3 lines), and on the line above when that line holds only a number, is a candidate: 6 or more digits for
  the bank-specific keywords and `account` + no/# (also on the line below), 6 for bare acc/account/acct/a-c/bank on the label line itself
  (an unbroken digit string, or a spaced one that does not start like a year), 8 for those words on the line below and for the
  payment-instruction words (beneficiary, payee, remit ...) on any line. An amount below a keyword line is
  skipped only when that line also has a total/amount word. Digits wrapped over one line break are joined when the next line starts
  with digits. In the bare and bank classes a run right after a PHONE word (tel, phone, mobile, cell, gsm, whatsapp, fax, ...; also with
  `No`/`Nr`/`Num`/`Number`) is skipped by D10 only when the digits look like a phone number. The FIRST of 0-9, + or ( decides, and nine or
  more digits are needed in all: a + (then it is a phone); a ( only as (0), (+44) or (020); a leading 0 with two or more digits in the first
  group and no one-digit group after it; or three or more groups with nine to fifteen digits, no one-digit group after the first and a last group of 4+ digits.
  One predicate serves both warnings. A phone label on the line ABOVE the number is not seen (the number is then a normal candidate).
  After `ref`, `vat`, `abn` (bank class) or `manager`, `contact`, `customer` (bare class) any run is skipped.
* Digit run. Digit blocks (hyphen or dot inside a block; a plausible calendar date is not a block) joined by ANY run of characters that
  are neither letters nor digits (at most 16 blocks) form one run. Candidates are the whole joined run and every block. A run made of
  digits and the letters o i l s b z (each piece with a digit, 4+ digits in all) is read with those letters as 0 1 1 5 8 2; BOTH the raw
  and the mapped line are scanned.
* IBAN. Country code in IBAN_LENGTH, two check digits, then the rest to the registry length; tokens are joined across any
  non-alphanumeric characters and across up to 3 wrapped lines, no keyword needed; a letters-only token of 5+ letters ends the IBAN, at most 8 letters-only
  tokens are allowed (spaced letters, Maltese style), and the candidate needs at least half of its characters to be digits (two thirds when code and check digits are separate tokens).
  After the word `iban` the digit-share rule is dropped and, if no registry IBAN fits (unknown country, truncated), the alphanumeric
  run (first token any length, then tokens of at most 4 characters, 15 to 34 characters) is the candidate, so a mismatch gives D10.
* BIC. After swift/bic (also `SWIFT address`, and the BIC may be on the next line) a token of BIC shape (4 letters, an ISO country code,
  2 alphanumerics, optional 3; spaces inside tolerated) is compared with the on-file BIC; IFSC the same; one the on-file detail lacks is a D12 notice.
* On-file components: every IBAN, every digit block of 6+ digits, every contiguous join of blocks of a run (same rules, same scan).
* D12 (`unexplained_numbers`): a run of 8+ digits (digit blocks of 3+ digits, amounts such as 12.50 left out, joined by ANY character that is neither a letter nor a digit nor a line break; the text is also read with line breaks as spaces) anywhere in the text that is not an on-file component, a date, part of
  a phone group (a phone label such as tel, phone, fax, mob, mobile or ph and the digits and punctuation right after it, up to the
  next letter, when those digits look like a phone number AND no bank or account word or `iban` sits on that line, the next line or a
  line D10 reads it for: next to such a word a phone-shaped run is never skipped silently, it is a D12), or an amount of the grounded record, or the digits of the invoice number, PO or date on lines that carry an invoice / PO / order / date word and no bank word (every occurrence). It needs no keyword, so it
  also covers countries outside the IBAN table. Measured on the 409 demo texts: see the evidence file of the work package.

Limits (written out in plain words in docs/bank-detail-checks.md):
* False D10 that cannot be removed (each is a rejection without override): a country-code lookalike that reaches an IBAN length with
  digits; any number of 8+ digits (6+ after a strong keyword such as sort code or IBAN) on a keyword line or on the line after it; a number joined after the
  quoted account (`Account No 12345678, 30 days` reads as 1234567830); CamelCase company names with Bank or Account in them
  (`RiverBank Ltd 87654321`, `BankSide`: the camel pass cannot tell them from `SupplierBank`); a percent-encoded quote of the RIGHT
  number; a look-alike spelling of the right number.
* Recall given up on purpose (these used to be labels through an in-word match and are not now; the number reaches D12 only, which needs
  a person but allows approval): `Accounts` without eight digits right after it, compound bank words in front (`Hausbank`,
  `Postbank`), `Accts` with fewer digits, a label in another language (cuenta, compte, rekening: the multilingual list belongs to the
  reader package, not to this check), and a phone-shaped number after a phone word (D10 skips it; D12 still flags it when a bank word is near).
* Evasions that remain: nested, double-encoded or wrapped blobs; a filler line (a name, a heading) between the label and the number
  (found only by D12 when the number has 8+ digits); a country missing from the IBAN table written without the word iban (D12 only);
  numbers shorter than the thresholds; an IBAN written with separate code and check tokens and mostly letters; a label more than 3
  lines above the number; a calendar-plausible number such as `Account No 12.05.2024` (read as a date); a homoglyph outside the
  Unicode data; a number in an image or a PDF; a phone label directly before a forged number
  (the phone group runs on over digits and punctuation up to the next letter, so a forged number written after a real phone number
  is skipped too, and a 8-digit number written with a leading 0 or + after a phone word is read as a phone number); digit blocks of under 3 digits with no keyword (`87 65 43 21`: quantity columns are the reason for the block
  minimum); a number split over 3 or more lines, one cell per line; digits spelled out in words; crypto wallet and payment-link
  handles; a number written after `manager`, `contact` or `customer` next to the bare words account/acc/a-c; a number that looks like
  an amount (`87654321.00` is skipped by D12 and below a keyword line); a lone short block before a number with no quantity word
  (`9 45678901` is read as part of an on-file `945678901`: D12 only).
* On-file components are broad (every block and every join): an invoice that quotes the on-file sort code as the account is clean.
The person decides every D10 and D12.
"""

import base64
import binascii
import csv
import html
import quopri
import re
import unicodedata
from bisect import bisect_right
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import islice
from types import MappingProxyType
from typing import Literal
from urllib.parse import unquote

from .checks import _digits_ascii, fold
from .confusables_data import CONFUSABLES

__all__ = [
    "ALPHA_TOKEN_MAX",
    "ALPHA_TOKEN_STOP",
    "BACKSTOP_FLAG",
    "BACKSTOP_MIN_BLOCK",
    "BACKSTOP_MIN_DIGITS",
    "BACKSTOP_REASON",
    "HEX_MIN_BYTES",
    "IBAN_LENGTH",
    "MAX_JOIN",
    "NEXT_LINES",
    "RUN_MAX",
    "RUN_MIN",
    "THRESHOLD_BARE",
    "THRESHOLD_KEYWORD",
    "TOKEN_MAX",
    "PAYMENT_LEXICON",
    "Finding",
    "Notice",
    "SuppliersInvalid",
    "arithmetic_ok",
    "bank_detail_changed",
    "bank_detail_findings",
    "check",
    "MAX_TEXT_CHARS",
    "RAW_MAX",
    "check_reasons",
    "load_suppliers",
    "look_notices",
    "unexplained_numbers",
]

_IBAN_TABLE = (
    "AL:28 AD:24 AT:20 AZ:28 BH:22 BE:16 BA:20 BR:29 BG:22 CR:22 HR:21 CY:28 CZ:24 FO:18 GL:18 DK:18 "
    "DO:28 EE:20 EG:29 FI:18 FR:27 GE:22 DE:22 GI:23 GR:27 GT:28 HU:28 IS:26 IE:22 IL:23 IT:27 JO:30 "
    "KZ:20 XK:20 KW:30 LV:21 LB:28 LI:21 LT:20 LU:20 MK:19 MT:31 MR:27 MU:30 MD:24 MC:27 ME:22 NL:18 "
    "NO:15 PK:24 PS:29 PL:28 PT:25 QA:29 RO:24 SM:27 LC:32 ST:25 SA:24 RS:22 SK:24 SI:19 ES:24 SE:24 "
    "CH:21 TL:23 TN:24 TR:26 AE:23 GB:22 VA:22 VG:24 UA:29 SC:31 IQ:23 BY:28 SV:28 LY:25 SD:18 BI:27 "
    "DJ:27 RU:33 SO:23 NI:28 MN:20 FK:18 OM:23 YE:30 HN:28 "
)
IBAN_LENGTH: Mapping[str, int] = MappingProxyType({k: int(v) for k, v in (p.split(":") for p in _IBAN_TABLE.split())})

THRESHOLD_KEYWORD = 6  # digits needed on a line with a bank-specific keyword
THRESHOLD_BARE = 8  # digits needed on a line with only acc / account / acct / a-c / bank
MAX_JOIN = 16  # digit blocks joined into one run
NEXT_LINES = 3  # lines looked at below a keyword line for the next non-blank line
RUN_MAX, RUN_MIN, TOKEN_MAX = 34, 15, 4  # iban-keyword fallback run: characters at most / at least; token length after the first
ALPHA_TOKEN_MAX = 8  # letters-only tokens (bank codes, spaced letters) allowed inside a keyword-free IBAN
ALPHA_TOKEN_STOP = 5  # a letters-only token this long inside an IBAN ends it (a word, not a bank code)
HEX_MIN_BYTES = 8  # shortest hex blob decoded
MAX_TEXT_CHARS = 2_000_000  # longer texts are refused with the closed notice `text_too_large` (a person reads them), never scanned
RAW_MAX = 4000  # longest raw line shown to a person in full; a longer one keeps its head and lists the direction controls it holds
BACKSTOP_MIN_DIGITS = 8  # shortest unexplained run
PHONE_MIN_DIGITS, PHONE_MAX_DIGITS = 9, 15  # a phone number written with + or ( or in three or more groups has this many digits
BACKSTOP_MIN_BLOCK = 3  # D12 joins only digit blocks of this length or more (table columns and quantities such as 72 2.75 are not joined)
BACKSTOP_FLAG = "D12"  # unexplained long number: a person must look, approvable with a reason (D11 is supplier_mismatch)
BACKSTOP_REASON = "unexplained_number"
IBAN_KW_TOKENS = 40  # tokens looked at after the word iban
IBAN_KW_START = 3  # the IBAN may start at one of the first tokens after the word iban (a filler word may come first)
KW_GAP = 3  # separator characters allowed inside a keyword (`sort - code`, `account : no`)
PHONE_GAP = 3  # separator characters allowed between a phone label and its number
BIC_GAP = 6  # separator characters allowed between the label swift/bic and the code
LOOKALIKE_MIN_DIGITS = 4  # digits a run must hold before its look-alike letters (o i l s b z) are read as digits
LOOKALIKE_MIN_DIGITS_WIDE = 7  # the same for the wider letters (g q t a e): hex-like words such as `00a0` are not numbers

_LEN = {k.lower(): v for k, v in IBAN_LENGTH.items()}
_ISO = frozenset(
    "ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl bm bn bo bq br bs bt bv bw by bz ca cc cd cf cg ch ci ck "
    "cl cm cn co cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg eh er es et fi fj fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs "
    "gt gu gw gy hk hm hn hr ht hu id ie il im in io iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv "
    "ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm "
    "pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr ss st sv sx sy sz tc td tf tg th tj tk tl tm tn to tr "
    "tt tv tw tz ua ug um us uy uz va vc ve vg vi vn vu wf ws xk ye yt za zm zw".split()
)
_NOJOIN = frozenset("\n")  # characters that never join two digit blocks (every other non-alphanumeric does)
_NA = r"[^a-z0-9]"
_GAP = _NA + "{0," + str(KW_GAP) + "}"
_NUMWORD = r"(?:no|num|number|nr|nbr|id)"
_SWIFT = (  # `Swift Logistics Ltd` is a company, `SWIFT code`, `SWIFT:` and `SWIFT 123` are labels
    "(?<![a-z])swift(?![a-z])(?=" + _NA + "{0,3}(?:code|address|number|no|id)(?![a-z])|" + _NA + "{0,3}[:=]|" + _NA + "{0,3}[0-9])"
)
_CLEARING = (
    "(?<![a-z])clearing(?![a-z])(?=" + _NA + "{0,3}(?:no|nr|num|number|code|id)(?![a-z])|" + _NA + "{0,3}[:=]|" + _NA + "{0,3}[0-9])"
)
_K6 = re.compile(
    "sort" + _GAP + "code|(?<![a-z])routing|" + _SWIFT + "|" + _CLEARING + "|konto|branch" + _GAP + "code|iban"
    "|accounts?" + _GAP + _NUMWORD + "(?![a-z])|accounts?" + _GAP + "#"
    "|(?<![a-z])(?:acct|acc|a[/-]c)" + _GAP + _NUMWORD + "(?![a-z])|(?<![a-z])(?:acct|acc)" + _GAP + "#"
    "|(?<![a-z])(?:aba|bic|bsb|blz|ifsc|clabe)(?![a-z])"
)
_K8 = re.compile(
    "(?<![a-z])(?:bank)?(?:(?:account|acct|acc|a ?[/-] ?c)(?:holder|name)?|(?:accounts|accts)(?="
    + _NA
    + "{0,3}[0-9](?:"
    + _NA
    + "?[0-9]){7}))(?![a-z])"
)  # whole words (and bankacct, accountholder, a-c, A / C); `Accounts` only with eight digits right after it (one separator between digits allowed)
_KBANK = re.compile(
    "(?<![a-z])bank(?:ing|verbindung(?:en)?|leitzahl|giro|details?|daten|info(?:rmation)?|name|number|nr|no|code)?(?![a-z])"
)  # the word bank and its whole-word compounds; not Bankside, Riverbank. The set of spellings has no end: a new compound is a new miss
_PHONE_LABELS = "telephone|telefone|telefono|telefoon|telefon|whatsapp|mobile|phone|handy|cell|gsm|fax|tel|tlf|mob|ph"  # each word before its own prefixes: the phone span must not stop inside `telephone`
_PHONE_NUMWORD = (
    "(?:" + _NA + "{0," + str(PHONE_GAP) + "}(?:number|num|nr|no))?"
)  # `Tel No`, `Phone Nr` (a word like `Notes` cannot follow: the gap before the digits has no letters)
_PHONE_LOOKBACK = (
    max(len(w) for w in (_PHONE_LABELS + "|manager|contact|customer|ref|vat|abn").split("|")) + PHONE_GAP + len("number") + PHONE_GAP
)  # the longest label, a number word and the gaps: how far back a label can sit from its number
_PHONE_BANK = re.compile("(?<![a-z])(" + _PHONE_LABELS + "|ref|vat|abn)" + _PHONE_NUMWORD + _NA + "{0," + str(PHONE_GAP) + "}$")
_PHONE_BARE = re.compile(
    "(?<![a-z])(" + _PHONE_LABELS + "|manager|contact|customer)" + _PHONE_NUMWORD + _NA + "{0," + str(PHONE_GAP) + "}$"
)
_PHONE_WORDS = frozenset(_PHONE_LABELS.split("|"))  # these skip a run only when the digits look like a phone number
_PHONE_SPAN = re.compile(
    "(?<![a-z])(?:" + _PHONE_LABELS + ")" + _PHONE_NUMWORD + r"[^a-z\n,;]*"
)  # a phone label (also `Telephone No:`) and the digits and punctuation that follow it (+44 (0) 20 7946 0958)
_QTY_WORD = re.compile("(?<![a-z])(?:qty|quantity|pcs|units?|menge|stk|cant|x)(?![a-z])")
_AMOUNT_WORD = re.compile("(?<![a-z])(?:total|subtotal|amount|balance|due|price|sum|vat|tax)(?![a-z])")
_IBAN_KW = re.compile("iban")
_BIC_GAP = _NA + "{0," + str(BIC_GAP) + "}"
_BIC = re.compile(
    "(?<![a-z])(?:swift|bic)(?![a-z])(?:"
    + _BIC_GAP
    + "(?:code|number|no|address|id))?"
    + _BIC_GAP
    + "([a-z]{4}) ?([a-z]{2}) ?([a-z0-9]{2})((?:[a-z0-9]{3})?)(?![a-z0-9])"
)
_TOK = re.compile(r"[a-z0-9]+")
_GROUP = re.compile(r"[0-9]+(?:[-.][0-9]+)*")
_DATE_YMD = re.compile(r"((?:19|20)[0-9]{2})[-.]([0-9]{2})[-.]([0-9]{2})")
_DATE_DMY = re.compile(r"([0-9]{2})[-.]([0-9]{2})[-.]((?:19|20)[0-9]{2})")
_HEX = re.compile(r"(?:(?:0x|\\x)?[0-9a-fA-F]{2}[\s,:;./-]{0,2}){" + str(HEX_MIN_BYTES) + r",}")
_MONEY = re.compile(r"[0-9]+\.[0-9]{2}")
_NUMBER_ONLY = re.compile(r"[0-9][0-9 ./,-]*")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
# Look-alike letters read as digits (a run needs 4+ digits). The raw line is scanned too, so a table can only ADD candidates.
# Case is lost by casefolding, so g is read once as 9 (g, q) and once as 6 (G).
_LOOK_TABLES = (
    str.maketrans("oilsbz", "011582"),
    str.maketrans("oilsbzgqtae", "01158299743"),
    str.maketrans("g", "6"),  # capital G looks like 6; casefolding loses the case, so g is read both ways
)
_LOOKSET = frozenset("0123456789oilsbzgqtae")

# ---- the lists that decide what counts as a payment instruction (ONE place: extend here, not in the code below)
_SEP = "[^a-z0-9]{0,3}"
PAYMENT_LEXICON = (  # a whole-word label on a line makes it a payment line (folded text: lower case, no accents)
    "beneficiary", "beneficiario", "beneficiaire", "begunstigde", "begunstigter", "empfanger", "payee",
    "pay" + _SEP + "to", "pay" + _SEP + "into", "remit", "remittance", "payments?" + _SEP + "to",
    "transfer" + _SEP + "funds" + _SEP + "to", "deposit" + _SEP + "to", "payable" + _SEP + "to", "credit" + _SEP + "to",
    "m" + _SEP + "pesa", "mobile" + _SEP + "money",
    "numer" + _SEP + "konta", "rachunek", "\u8d26\u53f7", "\u53e3\u5ea7", "p/c", "ac" + _SEP + "count", "wire" + _SEP + "to", "wire" + _SEP + "transfer",
    "payment" + _SEP + "(?:details?|instructions?|info|information|coordinates)",
    "upi", "vpa", "pix", "zelle", "payid", "paypal", "venmo", "cashapp",
    "cuenta", "compte", "conto", "conta", "agencia", "hesap", "rib",
    "datos" + _SEP + "bancarios", "coordonnees" + _SEP + "bancaires", "dati" + _SEP + "bancari",
    "transfer" + _SEP + "to", "[a-z]*rekening[a-z]*", "[a-z]*zahlungsempfanger[a-z]*",
    "bitcoin", "btc", "usdt", "usdc", "ethereum", "eth", "wallet", "crypto", "binance", "revolut", "wise", "payoneer", "alipay", "wechat",
    "payment" + _SEP + "link", "pay" + _SEP + "online",
    "\u0916\u093e\u0924\u093e", "\u062d\u0633\u0627\u0628",
    "\u5e10\u53f7", "\u8cec\u865f", "\u8d26\u6237", "\u5e33\u6236", "\u0441\u0447\u0451\u0442", "\u0441\u0447\u0435\u0442",
    "\uacc4\uc88c", "\u0e1a\u0e31\u0e0d\u0e0a\u0e35", "\u03bb\u03bf\u03b3\u03b1\u03c1\u03b9\u03b1\u03c3\u03bc\u03bf\u03c2",
)  # fmt: skip
CHANGE_NEW = (
    "new|changed?|changing|updated?|revised?|modified|amended|replacement|different|alternat(?:e|ive)|nouveau|nouvelle|nuevo|nueva|nuovo|nuova|neue[sn]?|cambio|cambiado|cambiados|change|modifie|modifies|ont"
    + _SEP
    + "change|han"
    + _SEP
    + "cambiado|geandert|nova|novo"
)
CHANGE_WHAT = "bank|banking|account|payment|wire|remittance|iban|cuenta|compte|konto|conto|bancarios?|bancaires?|bancari|bankverbindung|bankdaten|coordonnees|datos|dati|rib"
CHANGE_THING = "details?|information|info|instructions?|number|accounts?|coordinates|coordonnees|datos|dati|verbindung|data|cuenta|compte|conto|konto|bancarios|bancaires|bancari"
_PAYVERB = re.compile(
    "(?<![a-z])(?:pay|pays|paid|paying|payment|payments|remit|remittance|transfer|transfers|send|sent|deposit|settle|wire|credit|into|standing)(?![a-z])"
)  # a line with a payment verb never explains a number as a reference or reads a phone-shaped number as a phone
_TAXLABEL = re.compile(
    "(?<![a-z])(?:abn|acn|vat|gst|tax"
    + _SEP
    + "id|tin|ein|utr|siret|siren|nif|cif|uen|company"
    + _SEP
    + "(?:no|number|reg)|reg"
    + _SEP
    + "(?:no|number))"
    + _SEP
    + "(?:no|nr|number|id)?"
    + _SEP
    + "(?:[a-z0-9]{1,3}[^a-z0-9]{0,3})?$"
)  # the text right before a number ends with a tax or company registration label: the number is an identifier, not an account
_IDADJ = re.compile(
    "(?<![a-z])(?:invoice|inv|po|purchase"
    + _SEP
    + "order|(?<!standing )(?<!standing-)order|date|dated|datum|rechnung|factura|facture|fattura)(?:"
    + _SEP
    + "(?:no|nr|num|number|id))?[^a-z0-9]{0,3}$"
)  # the text right BEFORE a number ends with one of these: the number is labelled as an invoice / PO / order / date number
_KPAY: re.Pattern  # compiled after `_f` (non-Latin entries are folded with the same function as the text)
_CHANGE = re.compile(
    "(?<![a-z])(?:"
    + CHANGE_NEW
    + ")(?![a-z])[^\n]{0,40}?(?<![a-z])(?:"
    + CHANGE_WHAT
    + ")(?![a-z])[^\n]{0,24}?(?<![a-z])(?:"
    + CHANGE_THING
    + ")(?![a-z])"
    "|(?<![a-z])(?:"
    + CHANGE_WHAT
    + ")(?![a-z])[^\n]{0,24}?(?<![a-z])(?:"
    + CHANGE_THING
    + ")(?![a-z])[^\n]{0,30}?(?<![a-z])(?:"
    + CHANGE_NEW
    + ")(?![a-z])"
    "|(?<![a-z])(?:new|different|another|alternat(?:e|ive))[^a-z0-9]{1,3}(?:bank|banking|account|iban)(?![a-z])"
    "|(?<![a-z])banks?(?![a-z])[^\n]{0,20}?(?<![a-z])(?:has|have|had)[^a-z]{1,3}(?:changed|moved)(?![a-z])"
    "|(?<![a-z])changed[^a-z]{1,3}banks(?![a-z])"
)  # "new bank details", "our bank details have changed", "different account", "we have changed banks", "datos bancarios han cambiado"
# Bidirectional and invisible format controls: the scan reads the LOGICAL order, a person reads the VISUAL order. Their presence
# near a payment detail is itself a warning (D10 on the candidate lines, D12 anywhere in a document that has a payment line).
_BIDI = frozenset(chr(c) for c in (*range(0x202A, 0x202F), *range(0x2060, 0x2070), 0x200E, 0x200F, 0x061C))
_MARK = chr(0xE000)  # private-use marker that stands for a bidi control while lines are counted
_IFSC = re.compile("(?<![a-z])ifsc(?![a-z])(?:" + _NA + "{0,6}(?:code|no|number))?" + _NA + "{0,6}([a-z]{4}) ?(0[a-z0-9]{6})(?![a-z0-9])")
_OPAQUE_MIN = 32  # a base64-shaped token this long that decodes to non-text is a payload nobody can read

# ---- normalisation tables (class-level: every member of a class is handled at one choke point, _f)
# Unicode general category Pd (dash punctuation) as of Unicode 15.1 plus the minus sign; an explicit list, so the result does not
# depend on the Python version (a test reports any dash code point the running Python knows that is missing here).
_PD = (
    0x2D, 0x58A, 0x5BE, 0x1400, 0x1806, 0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2E17, 0x2E1A, 0x2E3A, 0x2E3B, 0x2E40,
    0x2E5D, 0x301C, 0x3030, 0x30A0, 0xFE31, 0xFE32, 0xFE58, 0xFE63, 0xFF0D, 0x10EAD, 0x2212,
)  # fmt: skip
_DASHES = {c: "-" for c in _PD}
_SLASHES = {0x2044: "/", 0x2215: "/", 0x29F8: "/", 0xFF0F: "/", 0x2571: "/"}
_BREAKS = {c: "\n" for c in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x85, 0x2028, 0x2029)}
# Default_Ignorable_Code_Point (zero-width, Hangul fillers, variation selectors, invisible formatting, tags)
_IGNORABLE = (
    (0xAD, 0xAD), (0x34F, 0x34F), (0x61C, 0x61C), (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180F), (0x200B, 0x200F),
    (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A), (0xE0000, 0xE001F), (0xE007F, 0xE0FFF),
)  # fmt: skip
_DELETE = {
    c: None for lo, hi in _IGNORABLE for c in range(lo, hi + 1)
}  # E0020-E007E (tag letters) are left to fold, which turns them into ASCII
# Look-alikes the Unicode data does not map directly (chains): Cyrillic soft sign / ghe, Latin small capitals
_LOOKALIKE = {
    **{ord(k): v for k, v in zip("\u044c\u0433", "br", strict=True)},
    **{
        ord(k): v
        for k, v in zip(
            "\u1d00\u0299\u1d04\u1d05\u1d07\ua730\u0262\u029c\u026a\u1d0a\u1d0b\u029f\u1d0d\u0274\u1d0f\u1d18\u0280\ua731\u1d1b\u1d1c\u1d20\u1d21\u028f\u1d22",
            "abcdefghijklmnoprstuvwyz",
            strict=True,
        )
    },
}


_I_LIKE = (
    0x196,
    0x399,
    0x406,
    0x4C0,
    0x2C92,
    0xA7AE,
    0x10CA5,
)  # capital I look-alikes (Greek Iota, Cyrillic I, ...) that the Unicode data maps to l


def _merged_confusables() -> dict[int, str]:
    """The Unicode table plus the lower-case and upper-case partner of every entry (a capital such as Greek Nu must map before it is lower-cased)."""
    out = dict(CONFUSABLES)
    # the Unicode data reads these capital-I look-alikes as l; the core copy and this scan read them as i
    for cp in _I_LIKE:
        out[cp] = "i"
    for cp, target in out.copy().items():
        c = chr(cp)
        for v in (c.lower(), c.upper(), c.casefold()):
            if len(v) == 1 and ord(v) > 127 and ord(v) not in out:
                out[ord(v)] = target
    return out


_CONF = _merged_confusables()
_WS = re.compile(r"[^\S\n]+")


class SuppliersInvalid(Exception):  # noqa: N818 (name fixed by the spec)
    pass


@dataclass(frozen=True)
class Finding:
    """One D10 reason. kind `number`/`bic`/`ifsc`: `candidate` (folded: digits, IBAN, BIC or IFSC found in the text) is not among
    `components` of the on-file detail. `raw` is the text line as written (controls shown as <U+XXXX>, never cut), next to the folded form."""

    candidate: str
    kind: Literal["number", "bic", "ifsc"]
    on_file: str  # the on-file detail as stored
    components: tuple[str, ...]
    raw: str = ""


@dataclass(frozen=True)
class Notice:
    """One person-must-look reason (flag D12, approvable with a reason; `flag` could be D10 for a future reject-only notice).
    `raw` is the text line as written, direction controls shown as <U+XXXX>, never cut (see RAW_MAX); `detail` is the number or phrase found."""

    code: str
    flag: str
    message: str  # plain words, for the review page
    raw: str = ""
    detail: str = ""


NOTICE_MESSAGES = {
    "bidi_control": "The text contains direction-control characters near payment details; what you read may differ from what was checked.",
    "change_notice": "The text says that bank or payment details are new or have changed.",
    "payment_line_no_number": "The text has a payment line (bank or payment words) but no payment number could be read from it, and nothing matches the details on file.",
    "iban_spans_lines": "An IBAN is written across three or more lines; it is not the one on file.",
    "hidden_text": "The text hides content (comments or invisible elements); a person must read what is really shown.",
    "date_as_account": "A date stands where an account number belongs; it may be an account number written as a date.",
    "short_account_number": "A number of 6 or 7 digits stands after a bank or payment word and is not on file; it may be an account number.",
    "id_on_payment_line": "The invoice number, order number or date is repeated on a payment line; it may be an account number.",
    "unexplained_number": "A long number that nothing explains (not a date, an amount, an invoice or order number or a number on file).",
    "text_too_large": "The text is longer than the limit this check reads; a person must read it.",
    "quoted_payment_details": "Payment details appear in quoted (earlier) text; they may be old details.",
    "opaque_blob": "The text contains a long encoded block that could not be read as text.",
    "line_mismatch": "The text could not be split into the same lines in two readings; a person must read it.",
    "bic_not_on_file": "The invoice names a bank code (BIC) and the details on file have none.",
    "ifsc_not_on_file": "The invoice names an IFSC code and the details on file have none.",
    "check_failed": "The check itself failed on this text; a person must read it.",
}


def _key(name: str) -> str:
    return unicodedata.normalize("NFKC", " ".join(name.split())).casefold()


def _unescape(s: str) -> str:
    """The ONE place where HTML entities are resolved: repeated until nothing changes (`&amp;amp;#10;` is a line break), at most 8 times."""
    for _ in range(8):
        u = html.unescape(s)
        if u == s:
            return s
        s = u
    return s


_SLASH_DATE = re.compile(r"(?<![0-9/])([0-9]{1,2})/([0-9]{1,2})/((?:19|20)?[0-9]{2})(?![0-9/])")


def _mask_date(m: re.Match) -> str:
    """A slash date (15/12/2026, 5/11/26, either order) is not a number: its characters become x so no digit run can span it."""
    return "x" * len(m.group()) if _ok_dm(m.group(1), m.group(2)) else m.group()


def _f(s: str) -> str:
    """Choke point: every comparison (text, extras, on-file) goes through this one normalisation."""
    t = unicodedata.normalize("NFKD", _unescape(s))  # NFKD first: fullwidth digits become ASCII
    t = _digits_ascii(t)  # every decimal digit to ASCII BEFORE the confusables: Arabic-Indic 7, 5, 1 would otherwise become v, o, l
    t = t.translate(_SEPLIKE).translate(_DINGBAT)  # letters that look like a bar or bang; circled digits NFKD leaves alone
    t = _CJKNUM.sub(lambda m: m.group().translate(_CJKDIGIT), t)  # 4 or more Chinese numerals in a row are a number
    t = t.translate(_DELETE)  # default-ignorable code points (zero-width, Hangul fillers, ...)
    t = t.translate(_CONF)  # capitals map before they are lower-cased (Greek Nu)
    t = fold(t).casefold()
    t = t.translate(_CONF)
    t = t.translate(_LOOKALIKE)
    t = t.translate(_DASHES)
    t = t.translate(_SLASHES)
    t = _SLASH_DATE.sub(_mask_date, t)
    t = t.translate(_BREAKS)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    return _WS.sub(" ", t)


_SEPLIKE = {
    c: "|" for c in (0x1C0, 0x1C1, 0x1C2, 0x1C3, 0x5C0, 0x5C3, 0x2223, 0x2502, 0x23D0, 0xFF5C)
}  # letters and symbols that look like a separator
_DINGBAT = {
    **{c: str(c - 0x2775) for c in range(0x2776, 0x277F)},
    0x277F: "10",
    **{c: str(c - 0x277F) for c in range(0x2780, 0x2789)},
    0x2789: "10",
    **{c: str(c - 0x2789) for c in range(0x278A, 0x2793)},
    0x2793: "10",
}  # negative and sans-serif circled digits (U+2776-2793): NFKD does not turn them into digits
_CJKDIGIT = str.maketrans("\u3007\u96f6\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d", "00123456789")
_CJKNUM = re.compile("[\u3007\u96f6\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d]{4,}")


def _lex_entry(w: str) -> str:
    """A lexicon entry as a regex over folded text: plain ASCII entries as written, others folded with `_f` (so Hindi, Arabic, Thai ... match the folded text)."""
    return w if w.isascii() else re.escape(_f(w))


_KPAY = re.compile("(?<![a-z])(?:" + "|".join(_lex_entry(w) for w in PAYMENT_LEXICON) + ")(?![a-z])")


def _camel(s: str) -> str:
    """The original with CamelCase words split (`BankAccountNo` -> `Bank Account No`), accents and entities resolved."""
    n = unicodedata.normalize("NFKD", _unescape(s)).translate(_DELETE).translate(_CONF)
    n = "".join(c for c in n if unicodedata.category(c) not in ("Cf", "Mn", "Me"))
    return _CAMEL.sub(" ", n)


def load_suppliers(path) -> Mapping[str, str]:
    """suppliers.csv (header supplier_name,bank_detail, UTF-8) -> {NFKC, casefolded, space-collapsed name: bank_detail}."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        raise SuppliersInvalid(f"unreadable: {type(e).__name__}") from None
    if not rows or [c.strip() for c in rows[0]] != ["supplier_name", "bank_detail"]:
        raise SuppliersInvalid("bad header")
    out: dict[str, str] = {}
    for n, row in enumerate(rows[1:], 2):
        if not row:
            continue
        if len(row) != 2 or not _key(row[0]):
            raise SuppliersInvalid(f"bad row {n}")
        k = _key(row[0])
        if k in out:
            raise SuppliersInvalid(f"duplicate supplier row {n}")
        if not _components(row[1]):
            raise SuppliersInvalid(f"row {n}: bank detail has no IBAN and no 6-digit number")
        out[k] = row[1]
    return out


def _ok_dm(a: str, b: str) -> bool:
    a, b = int(a), int(b)
    return (1 <= a <= 12 and 1 <= b <= 31) or (1 <= a <= 31 and 1 <= b <= 12)


def _is_date(g: str) -> bool:
    if m := _DATE_YMD.fullmatch(g):
        return _ok_dm(m.group(2), m.group(3))
    if m := _DATE_DMY.fullmatch(g):
        return _ok_dm(m.group(1), m.group(2))
    return False


def _word(c: str) -> bool:
    """A letter or digit (a modifier letter such as U+02BC is punctuation here)."""
    return c.isalnum() and unicodedata.category(c) != "Lm"


def _digits(g: str) -> str:
    return g.replace("-", "").replace(".", "")


def _runs(line: str, joiners: frozenset | None = None, money_ok: bool = True) -> list[tuple[int, list[str]]]:
    """Digit runs: blocks (dates excluded) joined by any characters that are neither letters nor digits (or only by `joiners`)."""
    runs: list[tuple[int, list[str]]] = []
    prev_end = -1
    for m in _GROUP.finditer(line):
        if _is_date(m.group()) or (not money_ok and _MONEY.fullmatch(m.group())):
            prev_end = -1
            continue
        gap = line[prev_end : m.start()] if prev_end >= 0 else None
        ok = gap is not None and bool(runs) and len(runs[-1][1]) < MAX_JOIN
        ok = ok and all(not _word(c) and c not in _NOJOIN and (joiners is None or c in joiners) for c in gap)
        if ok:
            runs[-1][1].append(_digits(m.group()))
        else:
            runs.append((m.start(), [_digits(m.group())]))
        prev_end = m.end()
    return runs


def _variants(line: str) -> set[str]:
    """The line itself and the line with look-alike letters read as digits (one reading per table)."""
    return {line, _digitise(line, _LOOK_TABLES[0]), *(_digitise(line, tb, LOOKALIKE_MIN_DIGITS_WIDE) for tb in _LOOK_TABLES[1:])}


def _digitise(line: str, table: dict = _LOOK_TABLES[0], min_digits: int = LOOKALIKE_MIN_DIGITS) -> str:
    """Letters in a run of pieces made only of digits and look-alike letters are read as digits (the run needs 4+ digits)."""
    pieces: list[list[re.Match]] = []
    cur: list[re.Match] = []
    for m in _TOK.finditer(line):
        t = m.group()
        if set(t) <= _LOOKSET and any(c.isdigit() for c in t):
            if cur and "\n" not in line[cur[-1].end() : m.start()]:
                cur.append(m)
            else:
                pieces.append(cur)
                cur = [m]
        else:
            pieces.append(cur)
            cur = []
    pieces.append(cur)
    out, last = [], 0
    for run in pieces:
        text = "".join(m.group() for m in run)
        if run and sum(c.isdigit() for c in text) >= min_digits:
            for m in run:
                out.append(line[last : m.start()])
                out.append(m.group().translate(table))
                last = m.end()
    out.append(line[last:])
    return "".join(out)


def _phone_text(text: str) -> bool:
    """Digits written like a phone number. `text` is a phone label, its number word and the digits and punctuation after it.

    The FIRST of 0-9, + or ( in the text decides (a sign or bracket after the number does not count). Nine or more digits are needed in
    all. A + then makes a phone; a ( only as `(0)`, `(+44)` or `(020)` (two or more digits). A leading 0 makes a phone with two or more
    digits in its first group and no one-digit group after it (`020 7946 0958`, `07911 123456`; not `0 87654321`, `0123 4567`).
    Otherwise three or more groups, nine to fifteen digits, no one-digit group after the first and a last group of four or more digits
    (`212 555 0123`, `1 800 555 0199`; not `87 65 43 21`, `87654321 1 2`, `8765 4321 00`, `123 456 789`)."""
    m = re.search("[0-9+(]", text)
    if m is None:
        return False
    groups = re.findall("[0-9]+", text)
    if not groups:
        return False
    digits = sum(len(g) for g in groups)
    if digits < PHONE_MIN_DIGITS:
        return False
    first = m.group()
    if first == "+":
        return True
    if first == "(":
        return re.match(r"[(](?:\+|0[)]|[0-9]{2,}[)])", text[m.start() :]) is not None
    if any(len(g) < 2 for g in groups[1:]):
        return False
    if first == "0":
        return len(groups[0]) >= 2
    return len(groups) >= 3 and digits <= PHONE_MAX_DIGITS and len(groups[-1]) >= 4


def _skip_run(pat: re.Pattern, variant: str, start: int, ndigits: int = 99) -> bool:
    """A label right before the run explains it: reference and contact words (ref, vat, abn only for 8+ digits), phone words only for a phone-shaped number."""
    m = pat.search(variant, max(0, start - _PHONE_LOOKBACK), start)
    if m is None:
        return False
    if m.group(1) not in _PHONE_WORDS:
        return m.group(1) not in ("ref", "vat", "abn") or ndigits >= THRESHOLD_BARE
    span = _PHONE_SPAN.match(variant, m.start(1))
    return _phone_text(span.group())  # the span always matches: it starts at the same phone word


def _line_candidates(line: str, thr: int, kind: str, money_ok: bool = True) -> list[str]:
    skip = {"bank": _PHONE_BANK, "pay": _PHONE_BANK, "bare": _PHONE_BARE}.get(kind)
    out: list[str] = []
    for variant in _variants(line):
        for start, blocks in _runs(variant, None, money_ok):
            whole = "".join(blocks)
            if skip is not None and _skip_run(skip, variant, start, len(whole)):
                continue
            out += [b for b in blocks if len(b) >= thr]
            if len(blocks) > 1 and len(whole) >= thr:
                out.append(whole)
    return out


def _iban_core(toks: list[str], s: int, strict: bool) -> str | None:
    """An IBAN that starts at toks[s] (code and check digits may sit in different tokens), or None."""
    first = toks[s]
    if len(first) < 2 or first[:2] not in _LEN:
        return None
    split = len(first) == 2  # code and check digits in separate tokens: only a two-digit token may follow (`No 12 Elm`, not `No 1234`)
    if strict and split and not (len(toks) > s + 1 and len(toks[s + 1]) == 2 and toks[s + 1].isdigit()):
        return None
    need = _LEN[first[:2]]
    got = ""
    words = 0
    for tok in toks[s : s + need + 1]:
        if got and tok.isalpha():
            words += 1
            if len(tok) >= ALPHA_TOKEN_STOP or (strict and words > ALPHA_TOKEN_MAX):
                return None
        got += tok
        if len(got) >= need:
            break
    got = got[:need]
    if len(got) < need or not got[2:4].isdigit():
        return None
    if strict and sum(c.isdigit() for c in got) < (need * 2 // 3 if split else need // 2):
        return None
    return got


def _ibans(lines: list[str], i: int) -> list[str]:
    """Keyword-free scan: tokens of this line and the next two lines, joined across any non-alphanumerics."""
    own = _TOK.findall(lines[i])
    if not own:
        return []
    toks = own + [t for x in lines[i + 1 : i + 3] for t in _TOK.findall(x)]
    out = []
    for t in range(len(own)):
        if (c := _iban_core(toks, t, True)) is not None:
            out.append(c)
    return out


_HAS_ALNUM = re.compile(r"[^\W_]")


def _next_nonblank(lines: list[str], i: int) -> int | None:
    return next(
        (j for j in range(i + 1, min(len(lines), i + 1 + NEXT_LINES)) if _HAS_ALNUM.search(lines[j])), None
    )  # a table separator row `|---|` is blank


def _token_run(toks: list[str]) -> str | None:
    """Fallback after the word iban: first token any length, then tokens of at most TOKEN_MAX characters; RUN_MIN to RUN_MAX characters."""
    got = ""
    for tok in toks:
        if got and len(tok) > TOKEN_MAX:
            break
        got += tok
        if len(got) >= RUN_MAX:
            break
    got = got[:RUN_MAX]
    return got if len(got) >= RUN_MIN else None


def _iban_keyword(lines: list[str], i: int) -> list[str]:
    line = lines[i]
    out: list[str] = []
    ks = list(_IBAN_KW.finditer(line))
    if not ks:
        return out
    nxt = _next_nonblank(lines, i)
    text = line + "\n" + (lines[nxt] if nxt is not None else "")  # an IBAN may wrap onto the next non-blank line
    for k in ks:
        toks = [m.group() for m in islice(_TOK.finditer(text, k.end()), IBAN_KW_TOKENS)]
        if not toks:
            continue
        c = next((x for s in range(min(IBAN_KW_START, len(toks))) if (x := _iban_core(toks, s, False))), None) or _token_run(toks)
        if c:
            out.append(c)
    return out


def _bic_eq(a: str, b: str) -> bool:
    return a == b or (a[:8] == b[:8] and (len(a) == 8 or len(b) == 8 or a[8:] == "xxx" or b[8:] == "xxx"))


def _wraps(lines: list[str], i: int) -> bool:
    """Digits wrapped over one line break: this line ends with a digit and the next one starts with one."""
    return i + 1 < len(lines) and lines[i].rstrip()[-1:].isdigit() and lines[i + 1].lstrip()[:1].isdigit()


def _components(on_file: str) -> set[str]:
    comps: set[str] = set()
    lines = _f(on_file).split("\n")
    for i, line in enumerate(lines):
        comps.update(_ibans(lines, i))
        comps.update(_iban_keyword(lines, i))
        for variant in _variants(line):
            for _, blocks in _runs(variant):
                for a in range(len(blocks)):
                    got = ""
                    for b in range(a, len(blocks)):
                        got += blocks[b]
                        if len(got) >= THRESHOLD_KEYWORD:
                            comps.add(got)
    for c in list(comps):  # a UK IBAN holds the sort code and the account number a UK invoice may quote instead of it
        if c.startswith("gb") and len(c) == 22 and c[8:].isdigit():
            comps.update({c[8:14], c[14:]})
    return comps


def _bics(text: str) -> list[str]:
    """BIC tokens after swift/bic; spaces inside the code are tolerated (`DEUT DE FF`)."""
    out = []
    for m in _BIC.finditer(text):
        code = "".join(g for g in m.groups() if g)
        if code[4:6] in _ISO:
            out.append(code)
    return out


def _ifscs(text: str) -> list[str]:
    return ["".join(m.groups()) for m in _IFSC.finditer(text)]


_NONLATIN = re.compile("[^\\x00-\\u024f\\W\\d_]")  # a letter outside the Latin script
_LONGRUN = re.compile("[0-9](?:[^a-z0-9\\n]{0,2}[0-9]){7}")  # eight digits, one or two separators allowed between them


def _kw_class(line: str, camel_line: str, bare: int = THRESHOLD_BARE) -> tuple[int, str]:
    """(threshold, kind) for a line: threshold 0 when it holds no bank keyword; kind is strong, bare, bank or pay. Every kind reads
    numbers from 6 digits (`bare` is kept for old callers and ignored); whether a hit is a rejection (D10) or a person-must-look
    (D12) is decided by `kind` and the length: strong keywords and 8+ digits reject, 6-7 digits under other words are D12."""
    for text in (line, camel_line):
        if _K6.search(text):
            return THRESHOLD_KEYWORD, "strong"
    for text in (line, camel_line):
        if _K8.search(text):
            return THRESHOLD_KEYWORD, "bare"
    for text in (line, camel_line):
        if _KBANK.search(text):
            return THRESHOLD_KEYWORD, "bank"
    for text in (line, camel_line):
        if _KPAY.search(text):
            return THRESHOLD_KEYWORD, "pay"
    return 0, ""


def _candidates_at(
    t: str, tc: str, bare: int = THRESHOLD_BARE, strong: set[str] | None = None, nonlatin: frozenset[int] = frozenset()
) -> dict[str, set[int]]:
    """Every candidate (6+ digits near a label, or an IBAN) with the set of line numbers it was read from. `strong` (out) receives the
    candidates that were read under a strong keyword or are IBANs: those are a rejection when they differ from the details on file,
    the others only when they have 8 or more digits."""
    lines = t.split("\n")
    clines = tc.split("\n")
    if len(clines) != len(lines):  # the caller raises a `line_mismatch` notice; here the plain lines stand in
        clines = lines
    out: dict[str, set[int]] = {}

    def add(cs: list[str], is_strong: bool, *at: int) -> None:
        for c in cs:
            out.setdefault(c, set()).update(at)
            if is_strong and strong is not None:
                strong.add(c)

    for i, line in enumerate(lines):
        add(_ibans(lines, i), True, i, i + 1, i + 2)
        add(_iban_keyword(lines, i), True, *range(i, i + 1 + NEXT_LINES))
        thr, kind = _kw_class(line, clines[i])
        if not thr and i in nonlatin and _LONGRUN.search(line):
            thr, kind = THRESHOLD_KEYWORD, "pay"  # a label in a script this check has no word for: any 8+ digit run is a candidate
        if not thr:
            continue
        sg = kind == "strong"
        add(_line_candidates(line, thr, kind), sg, i)
        if _wraps(lines, i):
            add(_line_candidates(line + " " + lines[i + 1].strip(), thr, kind), sg, i, i + 1)
        if i > 0 and _NUMBER_ONLY.fullmatch(lines[i - 1].strip()):
            add(_line_candidates(lines[i - 1], thr, "strong"), sg, i, i - 1)  # the number sits on the line above its label
        j = _next_nonblank(lines, i)
        if j is not None:
            add(_line_candidates(lines[j], thr, kind, money_ok=not _AMOUNT_WORD.search(lines[j])), sg, i, j)
    return out


def _nonlatin_lines(raw_lines: list[str]) -> frozenset[int]:
    """Numbers of the lines that hold a letter outside the Latin script (judged on the raw line: folding turns Greek and Cyrillic into Latin look-alikes)."""
    return frozenset(i for i, ln in enumerate(raw_lines) if _NONLATIN.search(ln))


def _candidates(t: str, tc: str, bare: int = THRESHOLD_BARE) -> list[str]:
    return list(_candidates_at(t, tc))


def _hex_extras(text: str) -> list[str]:
    out = []
    for m in _HEX.finditer(text):
        h = re.sub(r"0x|\\x|[^0-9a-fA-F]", "", m.group())
        for off in (0, 1):  # the blob may start on an odd nibble
            body = h[off : len(h) - ((len(h) - off) % 2)]
            try:
                out.append(bytes.fromhex(body).decode("utf-8", errors="ignore"))
            except ValueError:
                pass
    return out


_B64 = re.compile(r"[A-Za-z0-9+/_-]{16,}={0,2}")
_UESC = re.compile(r"\\u([0-9a-fA-F]{4})")
_QP = re.compile(r"=[0-9A-F]{2}|=\r?\n")
_B64LINE = re.compile(r"[A-Za-z0-9+/_-]{16,}={0,2}")


def _b64_bytes(blob: str) -> bytes | None:
    try:
        return base64.urlsafe_b64decode((blob + "=" * (-len(blob) % 4)).replace("+", "-").replace("/", "_"))
    except (binascii.Error, ValueError):
        return None


def _printable_share(b: bytes) -> float:
    txt = b.decode("utf-8", errors="ignore")
    return sum(c.isprintable() or c in "\r\n\t" for c in txt) / max(1, len(b))


def _opaque_blobs(text: str) -> list[str]:
    """Long base64-shaped tokens (mixed case with a digit, or padded) that do not decode to readable text."""
    out = []
    for m in _B64.finditer(text):
        blob = m.group()
        mixed = any(c.isdigit() for c in blob) and any(c.isupper() for c in blob) and any(c.islower() for c in blob)
        if len(blob) < _OPAQUE_MIN or not (blob.endswith("=") or mixed):
            continue
        b = _b64_bytes(blob.rstrip("="))
        if b is None or _printable_share(b) < 0.7:
            out.append(blob)
    return out


def _extras(text: str) -> list[str]:
    """Forms decoded from the text: base64 (lenient: undecodable bytes are dropped, like the hex form), percent, quoted-printable, \\uXXXX."""
    out = []
    for blob in _B64.findall(text):
        b = _b64_bytes(blob.rstrip("="))
        if b:
            d = b.decode("utf-8", errors="ignore")
            if d:
                out.append(d)
    if "%" in text:
        out.append(unquote(text))
    lines = text.splitlines()
    k = 0
    while k < len(lines):  # base64 wrapped over lines (76 characters, or any width): decode the concatenation of consecutive lines too
        if _B64LINE.fullmatch(lines[k].strip()):
            j = k
            while j + 1 < len(lines) and _B64LINE.fullmatch(lines[j + 1].strip()):
                j += 1
            if j > k:
                b = _b64_bytes("".join(x.strip() for x in lines[k : j + 1]).rstrip("="))
                if b:
                    out.append(b.decode("utf-8", errors="ignore"))
            k = j + 1
        else:
            k += 1
    if _QP.search(text):
        out.append(quopri.decodestring(text.encode("utf-8", errors="ignore")).decode("utf-8", errors="ignore"))
    if "\\u" in text:
        out.append(_UESC.sub(lambda m: chr(int(m.group(1), 16)), text))
    return out


_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HIDE_STYLE = r"(?:display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?![0-9.])|opacity\s*:\s*0(?![0-9.]))"
_HIDDEN_EL = re.compile(
    r"<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(?:\bhidden\b|style\s*=\s*[\"'][^\"']*" + _HIDE_STYLE + r"[^\"']*[\"'])[^>]*>.*?</\1\s*>", re.S | re.I
)
_BLOCK_TAG = re.compile(r"</?(?:br|p|div|tr|td|th|li|ul|ol|table|h[1-6]|section|article|header|footer|blockquote|pre)\b[^>]*>", re.I)
_ANY_TAG = re.compile(r"<[a-zA-Z/!][^>]{0,2000}>")


def _html_views(text: str) -> list[str]:
    """The text as a person sees it when it is HTML: comments, hidden elements and tags removed (block tags become line breaks), and
    the same with the hidden elements kept. Empty when the text holds no markup."""
    if "<" not in text or not _ANY_TAG.search(text):
        return []
    t = _COMMENT.sub("", text)
    views = []
    for u in (_HIDDEN_EL.sub("", t), t):
        v = _ANY_TAG.sub("", _BLOCK_TAG.sub(chr(10), u))
        if v != text and v not in views:
            views.append(v)
    return views


def _bodies(send_text: str) -> list[str]:
    return [send_text, *_extras(send_text), *_hex_extras(send_text), *_html_views(send_text)]


def _raw_lines(u: str) -> list[str]:
    return u.translate(_BREAKS).replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _show(raw_lines: list[str], at: set[int], memo: dict[str, str] | None = None) -> str:
    """The raw line(s) a candidate was read from, with invisible and direction characters shown as <U+XXXX>. Never cut below RAW_MAX
    characters; a longer line keeps its head and names every direction control it holds."""
    rows = [raw_lines[i] for i in sorted(at) if 0 <= i < len(raw_lines) and raw_lines[i].strip()]
    return _visible_controls(" / ".join(r.strip() for r in rows[:2]), memo)


def _vis(txt: str) -> str:
    return "".join(c if c.isprintable() else f"<U+{ord(c):04X}>" for c in txt)


def _visible_controls(txt: str, memo: dict[str, str] | None = None) -> str:
    """`txt` with invisible and direction characters shown as <U+XXXX>. A text of RAW_MAX characters or fewer is shown whole. A longer
    one keeps its head and names EVERY control it holds (found with a set of its characters, so the cost is linear and, being cached,
    paid once per line however many numbers the line holds: callers pass a `memo` dict of their own, there is no module cache)."""
    if memo is not None and txt in memo:
        return memo[txt]
    memo_out = _visible_controls_uncached(txt)
    if memo is not None:
        memo[txt] = memo_out
    return memo_out


def _visible_controls_uncached(txt: str) -> str:
    if len(txt) <= RAW_MAX:
        out = _vis(txt)
        if len(out) <= RAW_MAX:
            return out
        txt = txt[:RAW_MAX]
        return (
            _vis(txt) + f" [shortened; controls: {', '.join(sorted(f'U+{ord(c):04X}' for c in set(txt) if not c.isprintable())) or 'none'}]"
        )
    ctl = sorted(f"U+{ord(c):04X}" for c in set(txt) if not c.isprintable())
    return _vis(txt[:RAW_MAX]) + f" [+{len(txt) - RAW_MAX} characters; controls: {', '.join(ctl) or 'none'}]"


def _bidi_lines(u: str) -> set[int]:
    """Numbers of the lines that hold a bidirectional or invisible format control (counted on the folded lines)."""
    if not any(c in _BIDI for c in u):
        return set()
    marked = "".join(_MARK if c in _BIDI else c for c in u)
    return {i for i, ln in enumerate(_f(marked).split("\n")) if _MARK in ln}


def _line_is_bad(line: str) -> bool:
    """A bank keyword, a payment verb or a payment-instruction word sits on the line."""
    return bool(_kw_class(line, line)[0]) or bool(_PAYVERB.search(line))


def _id_explained(c: str, lines: list[str], at: set[int], ids: frozenset[str]) -> bool:
    """True when `c` is a digit string of the record (invoice number, PO, date) and EVERY place it appears on the candidate's lines is
    written right after an invoice / PO / order / date word on a line with no bank keyword, payment verb or payment-instruction word."""
    if c not in ids:
        return False
    seen = False
    for i in at:
        if not 0 <= i < len(lines):
            continue
        for v in _variants(lines[i]):
            for start, blocks in _runs(v):
                if c in blocks or "".join(blocks) == c:
                    seen = True
                    if _line_is_bad(v) or not _IDADJ.search(v[:start][-40:]):
                        return False
    return seen


def _scan(send_text: str, on_file: str, ids: frozenset[str] = frozenset()) -> tuple[list[Finding], list[Notice]]:
    """(D10 findings, D12 notices for weak candidates). A candidate that is not a component of `on_file` is a D10 finding when it was
    read under a strong keyword, is an IBAN, or has 8 or more digits; a 6-7 digit hit under another word is the notice
    `short_account_number`; one equal to the record's invoice number, PO or date is the notice `id_on_payment_line` (never D10: an
    honest invoice may repeat its own number)."""
    comps = _components(on_file)
    onf = _f(on_file)
    on_bics, on_ifsc = _bics(onf), _ifscs(onf)
    shown = tuple(sorted(comps))
    memo: dict[str, str] = {}
    found: list[Finding] = []
    weak: list[Notice] = []
    seen: set[tuple[str, str]] = set()

    def add(c: str, kind: str, raw: str) -> None:
        if (c, kind) not in seen:
            seen.add((c, kind))
            found.append(Finding(c, kind, on_file, shown, raw))  # type: ignore[arg-type]

    def add_weak(code: str, c: str, raw: str) -> None:
        if (c, code) not in seen:
            seen.add((c, code))
            weak.append(Notice(code, BACKSTOP_FLAG, NOTICE_MESSAGES[code], raw, c))

    for body in _bodies(send_text):
        u = _unescape(body)
        t, tc = _f(u), _f(_camel(u))
        lines = t.split("\n")
        rl = _raw_lines(u)
        strong: set[str] = set()
        for c, at in _candidates_at(t, tc, THRESHOLD_BARE, strong, _nonlatin_lines(rl)).items():
            if c in comps:
                continue
            if c in ids:
                if not _id_explained(c, lines, at, ids):
                    add_weak("id_on_payment_line", c, _show(rl, at, memo))
            elif c in strong or len(c) >= THRESHOLD_BARE:
                add(c, "number", _show(rl, at, memo))
            else:
                add_weak("short_account_number", c, _show(rl, at, memo))
        if on_bics:
            for b in _bics(t):
                if not any(_bic_eq(b, o) for o in on_bics):
                    add(b, "bic", "")
        if on_ifsc:
            for x in _ifscs(t):
                if x not in on_ifsc:
                    add(x, "ifsc", "")
    return found, weak


def bank_detail_findings(send_text: str, on_file: str, ids: frozenset[str] = frozenset()) -> list[Finding]:
    """The D10 findings of `_scan`: candidates (also in decoded base64, percent, hex, quoted-printable and HTML-text forms) that are not
    components of `on_file`, plus an IFSC or BIC that differs from the one on file."""
    return _scan(send_text, on_file, ids)[0]


def bank_detail_changed(send_text: str, on_file: str, ids: frozenset[str] = frozenset()) -> bool:
    """True when `bank_detail_findings` finds anything; ANY failure of the scan also gives True (fails closed, reject-only like D10)."""
    try:
        return bool(bank_detail_findings(send_text, on_file, ids))
    except Exception:  # noqa: BLE001 (deliberately broad: a scan that cannot run must never read as clean)
        return True


def _record_ids(fields: Mapping) -> set[str]:
    """Digits of the invoice number, PO and date of the record (model-extracted: NOT proof by themselves)."""
    ids: set[str] = set()
    for k in ("invoice_no", "po_ref", "invoice_date"):
        if fields.get(k) is not None:
            ids.add(re.sub(r"[^0-9]", "", str(fields[k])))
    ids.discard("")
    return ids


def _record_numbers(fields: Mapping) -> set[str]:
    """Digit strings of the grounded record that explain a number in the text (exact match only). Raises on a malformed record."""
    known = _record_ids(fields)
    known.add(str(abs(fields["total_minor"])))
    for x in fields["lines"]:
        known |= {str(abs(x["amount_minor"])), str(abs(x["unit_cost_minor"]))}
    for x in fields["adjustments"]:
        known.add(str(abs(x["amount_minor"])))
    known.discard("")
    return known


def _backstop_runs(line: str, min_block: int = BACKSTOP_MIN_BLOCK) -> list[tuple[int, str, set[str], int]]:
    """D12 runs: (start, core digits, comparison forms). The core joins blocks of BACKSTOP_MIN_BLOCK+ digits across ANY characters
    that are neither letters nor digits (the same rule as D10; amounts and dates break it); a short block (under that length) right
    next to the core at either end does not make a run on its own but is added to the comparison forms, so `4567 8901 2` is compared
    as 456789012 as well as 45678901. A quantity word keeps a short block in front out of the forms."""
    items = []
    for m in _GROUP.finditer(line):
        g = m.group()
        d = _digits(g)
        kind = "break" if _is_date(g) or _MONEY.fullmatch(g) else ("short" if len(d) < min_block else "long")
        items.append((m.start(), m.end(), d, kind))

    def joined(a: int, b: int) -> bool:
        return all(not _word(c) and c not in _NOJOIN for c in line[items[a][1] : items[b][0]])

    qty = bool(_QTY_WORD.search(line))  # a quantity before a number is not part of it
    out: list[tuple[int, str, set[str], int]] = []
    i = 0
    while i < len(items):
        if items[i][3] != "long":
            i += 1
            continue
        j = i
        while j + 1 < len(items) and j - i + 1 < MAX_JOIN and items[j + 1][3] == "long" and joined(j, j + 1):
            j += 1
        core = "".join(items[k][2] for k in range(i, j + 1))
        lead = items[i - 1][2] if i > 0 and items[i - 1][3] == "short" and line[items[i - 1][1] : items[i][0]] == " " and not qty else ""
        trail = items[j + 1][2] if j + 1 < len(items) and items[j + 1][3] == "short" and line[items[j][1] : items[j + 1][0]] == " " else ""
        out.append((items[i][0], core, {core, lead + core, core + trail, lead + core + trail}, items[j][1]))
        i = j + 1
    return out


def _bank_near(lines: list[str], clines: list[str]) -> list[bool]:
    """Per line: does a bank or account word (or `iban`, or a payment-instruction word) sit on it, on the next line, or on a line above it that D10 reads this line for?"""
    kw = [bool(_kw_class(ln, cl)[0]) for ln, cl in zip(lines, clines, strict=True)]  # `iban` is one of the keywords
    return [
        kw[i] or (i + 1 < len(kw) and kw[i + 1]) or any(kw[k] and _next_nonblank(lines, k) == i for k in range(max(0, i - NEXT_LINES), i))
        for i in range(len(lines))
    ]


def _unexplained(fields: Mapping, send_text: str, on_file: str | None = None) -> list[tuple[str, str]]:
    """Keyword-free backstop (D12): (digits, raw line) of the runs of BACKSTOP_MIN_DIGITS+ digits that nothing explains. Raises
    KeyError/TypeError on a malformed record.

    The invoice number, PO and date of the record explain a run only when EVERY occurrence of those digits is written right after an
    invoice / PO / order / date word on a line that holds no bank keyword, payment verb or payment-instruction word (the record is
    model-extracted: an attacker prints the account digits as the invoice number). Amounts grounded by the arithmetic check explain a
    run only when no line it spans is a payment line (a bank keyword, a payment verb, or the line right below a label). A copy of the
    text with line breaks read as spaces is scanned too; a run that crosses a line break is one more occurrence, judged like any other."""
    comps = _components(on_file) if on_file else set()
    ids = _record_ids(fields)
    known = _record_numbers(fields) - ids
    out: list[tuple[str, str]] = []
    vis_memo: dict[str, str] = {}
    for body in _bodies(send_text):
        u = _unescape(body)
        rl = _raw_lines(u)
        lines = _f(u).split(chr(10))
        clines = _f(_camel(u)).split(chr(10))
        if len(clines) != len(lines):
            clines = lines
        n = len(lines)
        kw = [bool(_kw_class(ln, cl)[0]) for ln, cl in zip(lines, clines, strict=True)]
        verb = [bool(_PAYVERB.search(ln)) for ln in lines]
        near = _bank_near(lines, clines)
        above = [any((kw[k] or verb[k]) and _next_nonblank(lines, k) == i for k in range(max(0, i - NEXT_LINES), i)) for i in range(n)]
        bad = [kw[i] or verb[i] or above[i] for i in range(n)]
        # run: (first line, last line, core, forms, silenced by a phone span, text before the run or None when it crosses lines)
        runs: list[tuple[int, int, str, set[str], bool, str | None]] = []
        for i, line in enumerate(lines):
            for variant in _variants(line):
                spans = [(m.start(), m.end(), m.group()) for m in _PHONE_SPAN.finditer(variant) if _phone_text(m.group())]
                line_cores = []
                for start, core, forms, end in _backstop_runs(variant, 2 if verb[i] else BACKSTOP_MIN_BLOCK):
                    if len(core) < BACKSTOP_MIN_DIGITS:
                        continue
                    silent = not near[i] and not verb[i] and any(lo < start < hi and end <= hi for lo, hi, _ in spans)
                    runs.append((i, i, core, forms, silent, variant[:start][-40:]))
                    line_cores.append(core)
                # a phone-shaped span next to a bank word or a payment verb is never silent: its own digits form a run
                if near[i] or verb[i]:
                    for _, _, txt in spans:
                        sd = "".join(re.findall("[0-9]+", txt))
                        if len(sd) >= BACKSTOP_MIN_DIGITS and not any(c in sd for c in line_cores):
                            runs.append((i, i, sd, {sd}, False, None))
        stream = " ".join(lines)
        starts = [0]
        for ln in lines[:-1]:
            starts.append(starts[-1] + len(ln) + 1)
        for start, core, forms, end in _backstop_runs(stream):
            a, z = bisect_right(starts, start) - 1, bisect_right(starts, max(start, end - 1)) - 1
            if len(core) >= BACKSTOP_MIN_DIGITS and a != z:
                runs.append((a, z, core, forms, False, None))  # crosses a line break: only the stream copy sees it
        occ: dict[str, bool] = {}
        for first, last, _core, forms, _silent, before in runs:
            for v in forms & ids:
                ok = before is not None and first == last and not (kw[first] or verb[first]) and _IDADJ.search(before) is not None
                occ[v] = occ.get(v, True) and ok
        for first, last, core, forms, silent, before in runs:
            if silent or forms & comps:
                continue
            if before is not None and first == last and not (kw[first] or verb[first]) and _TAXLABEL.search(before):
                continue  # `ABN 51 824 753 556`, `VAT: GB123456789012` on a line that is not a payment line
            if forms & known and not any(bad[k] for k in range(first, last + 1)):
                continue
            if any(occ[v] for v in forms & ids):
                continue
            raw = rl[first] if first == last and first < len(rl) else " / ".join(x.strip() for x in rl[first : last + 1])
            out.append((core, _visible_controls(raw.strip(), vis_memo)))
    return list(dict.fromkeys(out))


def unexplained_numbers(fields: Mapping, send_text: str, on_file: str | None = None) -> list[str]:
    """The digits of `_unexplained` (D12 backstop), without their lines."""
    return list(dict.fromkeys(c for c, _ in _unexplained(fields, send_text, on_file)))


def _int(x) -> bool:
    return type(x) is int


def arithmetic_ok(fields: Mapping) -> bool:
    """False for any wrong sum and for any malformed value (bool, float, None, missing key): the item then gets D06."""
    try:
        lines, adjustments, total = fields["lines"], fields["adjustments"], fields["total_minor"]
        amounts = []
        for ln in lines:
            q, u, a = ln["qty"], ln["unit_cost_minor"], ln["amount_minor"]
            if not (_int(q) and _int(u) and _int(a)) or a != q * u:
                return False
            amounts.append(a)
        adj = [x["amount_minor"] for x in adjustments]
        return _int(total) and all(_int(x) for x in adj) and total == sum(amounts) + sum(adj)
    except (KeyError, TypeError):
        return False


def _stream_ibans(lines: list[str]) -> set[str]:
    """IBANs found when the lines are read as one stream (an IBAN written over three or more lines)."""
    return set(_ibans([" ".join(lines)], 0))


_SHAPED = re.compile(
    r"\s*(?:(?:details?|information|info|accounts?|number|no|nr|name|holder|instructions?|coordinates)\s*)*(?:[^\sa-z]|x{6}|$)"
)  # after a bank or account word (and words like `details`): anything but a letter (a colon, number, bracket ...), a masked date, or the line end
_DATEISH = re.compile("x{6,}")  # what `_f` leaves of a slash date


def _has_value(text: str) -> bool:
    """The text carries a payment value: a number of 6+ digits or an IBAN."""
    # amounts (14.96) break a run: a table row is not a value
    return bool(_line_candidates(text, THRESHOLD_KEYWORD, "strong", money_ok=False)) or bool(_ibans([text], 0))


def _date_value(text: str) -> bool:
    return bool(_DATEISH.search(text)) or any(_is_date(m.group()) for m in _GROUP.finditer(text))


def _unserved(lines: list[str], clines: list[str]) -> list[tuple[int, str]]:
    """Label lines whose LAST label has no value: (line number, "none" or "date"). The value of a label is what follows it on its
    line up to the next label, or - when nothing follows - a number of 6+ digits or an IBAN in the next three non-blank lines, or a
    number alone on the line above. A genuine value of ANOTHER label on the same line does not serve it. A bank or account word
    counts as a label only when a colon, number sign, hyphen, digit or the line end follows it (`Payment by bank transfer` is prose)."""
    out: list[tuple[int, str]] = []
    cache: dict[int, bool] = {}

    def valued(j: int) -> bool:
        if j not in cache:
            cache[j] = not _MONEY.search(lines[j]) and _has_value(lines[j])  # a line with an amount is a table row, not a value
        return cache[j]

    for i, (ln, cl) in enumerate(zip(lines, clines, strict=True)):
        txt, hits = ln, []
        for t in (ln, cl):
            hits = []
            for rx in (_K6, _K8, _KBANK, _KPAY):
                for m in rx.finditer(t):
                    if rx in (_K8, _KBANK) and not _SHAPED.match(t, m.end()):
                        continue
                    hits.append(m.end())
            if hits:
                txt = t
                break
        if not hits:
            continue
        region = txt[max(hits) :]
        # the last label: its value is what follows it, so the end of the LAST match is the start of its region
        if _has_value(region):
            continue
        if i > 0 and lines[i - 1].strip() and _NUMBER_ONLY.fullmatch(lines[i - 1].strip()) and _has_value(lines[i - 1]):
            continue
        j, found = i, False
        for _ in range(3):
            nj = _next_nonblank(lines, j)
            if nj is None:
                break
            j = nj
            if valued(j):
                found = True
                break
        if not found:
            out.append((i, "date" if _date_value(region) else "none"))
    return out


def look_notices(fields: Mapping, send_text: str, on_file: str | None = None, _weak: list[Notice] | None = None) -> list[Notice]:
    """Person-must-look reasons (all D12) that are not an unexplained number: direction controls near payment details, hidden or
    quoted text, a text that says the bank details are new, a payment line whose own label has no value or whose value is a date, an
    IBAN over several lines, an unreadable encoded block, lines that do not line up, a BIC or IFSC that the details on file do not
    have, a 6-7 digit number under a bare word, the record's own number repeated on a payment line."""
    out: list[Notice] = []

    def add(code: str, raw: str = "", detail: str = "") -> None:
        if all((n.code, n.detail) != (code, detail) for n in out):
            out.append(Notice(code, BACKSTOP_FLAG, NOTICE_MESSAGES[code], raw, detail))

    comps = _components(on_file) if on_file else set()
    onf = _f(on_file) if on_file else ""
    if _HIDDEN_EL.search(_COMMENT.sub("", send_text)):
        add("hidden_text", _visible_controls(_HIDDEN_EL.search(_COMMENT.sub("", send_text)).group()[:RAW_MAX]))
    for body in _bodies(send_text):
        u = _unescape(body)
        t, tc = _f(u), _f(_camel(u))
        lines, clines = t.split("\n"), tc.split("\n")
        if len(clines) != len(lines):
            add("line_mismatch")
            clines = lines
        at = _candidates_at(t, tc, nonlatin=_nonlatin_lines(_raw_lines(u)))
        labels = any(_kw_class(ln, cl)[0] for ln, cl in zip(lines, clines, strict=True))
        rl = _raw_lines(u)
        if (at or labels) and any(c in _BIDI for c in u):
            add("bidi_control", _show(rl, _bidi_lines(u)))
        if m := _CHANGE.search(" ".join(lines)):
            add("change_notice", m.group(), m.group())
        per_line = {c for i in range(len(lines)) for c in _ibans(lines, i)} | {
            c for i in range(len(lines)) for c in _iban_keyword(lines, i)
        }
        if extra := (_stream_ibans(lines) - per_line - comps):
            add("iban_spans_lines", sorted(extra)[0], sorted(extra)[0])
        quoted = [ln.lstrip()[1:] for ln in rl if ln.lstrip().startswith(">")]
        if quoted and _candidates_at(_f(chr(10).join(quoted)), _f(_camel(chr(10).join(quoted)))):
            add("quoted_payment_details", _show(quoted, set(range(len(quoted)))))
        if on_file:
            if not _bics(onf) and (b := _bics(t)):
                add("bic_not_on_file", b[0], b[0])
            if not _ifscs(onf) and (x := _ifscs(t)):
                add("ifsc_not_on_file", x[0], x[0])
            for i, kind in _unserved(lines, clines):
                add("date_as_account" if kind == "date" else "payment_line_no_number", _show(rl, {i}), lines[i][:80])
    if blobs := _opaque_blobs(send_text):
        add("opaque_blob", blobs[0][:80], blobs[0][:80])
    if on_file:
        try:
            ids = frozenset(_record_ids(fields))
        except (AttributeError, TypeError):
            ids = frozenset()
        for n in _weak if _weak is not None else _scan(send_text, on_file, ids)[1]:
            add(n.code, n.raw, n.detail)
    return out


def check_reasons(
    fields: Mapping, send_text: str, suppliers: Mapping[str, str], *, backstop: bool = True
) -> tuple[list[str], list[Notice]]:
    """(flags, notices) for a valid, grounded record. Flags are sorted and unique; `send_text` is exactly the string given to the model
    (no fold). `suppliers` comes from load_suppliers. D12 (BACKSTOP_FLAG) is on by default; a malformed record also gets D12.
    Every scan fails closed: if it cannot run, the reject-only D10 (first scan) or D12 (the others) is raised together with the
    notice `check_failed`. A text longer than MAX_TEXT_CHARS is not scanned: D12 and the notice `text_too_large`."""
    if any(k != _key(k) for k in suppliers):
        raise ValueError("suppliers must be keyed by NFKC, casefolded, space-collapsed names (use load_suppliers)")
    flags: set[str] = set()
    notes: list[Notice] = []
    if not arithmetic_ok(fields):
        flags.add("D06")
    name = fields.get("supplier_name") if isinstance(fields, Mapping) else None
    on_file = suppliers.get(_key(name)) if isinstance(name, str) else None
    if len(send_text) > MAX_TEXT_CHARS:
        if on_file is None:
            flags.add("L01")
        flags.add(BACKSTOP_FLAG)
        return sorted(flags), [Notice("text_too_large", BACKSTOP_FLAG, NOTICE_MESSAGES["text_too_large"], "", str(len(send_text)))]
    weak: list[Notice] | None = None
    if on_file is None:
        flags.add("L01")
    else:
        try:
            ids = frozenset(_record_ids(fields))
        except (AttributeError, TypeError):
            ids = frozenset()
        try:
            found, weak = _scan(send_text, on_file, ids)
            if found:
                flags.add("D10")
        except Exception:  # noqa: BLE001 (deliberately broad: a scan that cannot run must never read as clean)
            flags.add("D10")
            notes.append(Notice("check_failed", "D10", NOTICE_MESSAGES["check_failed"]))
    if backstop:
        try:
            found_notes = look_notices(fields, send_text, on_file, weak)
            numbers = [
                Notice("unexplained_number", BACKSTOP_FLAG, NOTICE_MESSAGES["unexplained_number"], raw, c)
                for c, raw in _unexplained(fields, send_text, on_file)
            ]
            if numbers or found_notes:
                flags.add(BACKSTOP_FLAG)
            notes += numbers + found_notes
        except Exception:  # noqa: BLE001 (a malformed record or a failed scan: a person looks)
            flags.add(BACKSTOP_FLAG)
            notes.append(Notice("check_failed", BACKSTOP_FLAG, NOTICE_MESSAGES["check_failed"]))
    return sorted(flags), notes


def check(fields: Mapping, send_text: str, suppliers: Mapping[str, str], *, backstop: bool = True) -> list[str]:
    """Flags only; see `check_reasons`."""
    return check_reasons(fields, send_text, suppliers, backstop=backstop)[0]
