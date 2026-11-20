"""Ticket G8 (glued-rest gap): the 101 probe rows, the must-keep rows, the full-stop rows, the at-rest rows and the
untrusted rows, as data. Not collected by pytest.

Every value is fake or a documentation value and is built from parts here (no literal of a full value elsewhere, as
tests/test_text_parts_together.py does). A row is
    (id, kind, shape, text, value, cls, now, after, after_g4c)
with `text`, `now`, `after` and `after_g4c` templates over `V` (`{IP1}` ...) that `case()` fills in:
    now       `redact(text).text` on the base commit (step 0, recorded on cloud/core-c a5247ac4a; `python -m tests.g8_cases`
              re-checks it and exits 1 on any difference)
    after     `redact(text).text` with G8a + G8b, G4c NOT merged
    after_g4c the same once G4c (ticket G4 v4 / v5 sections 5.2 and 5.3: the same regex text) is merged; None = same as
              `after`
    cls       closed (leaks now, not after) | changed (no leak either way, the output changes) | unchanged | limit (still
              leaks after G8: a stated limit) | g4c (closed by G4c, not by G8)
"""

from __future__ import annotations

import difflib
import re
import string
import sys

J = "".join
V = {
    "IP1": J(["192.", "0.2", ".10"]),  # RFC 5737 TEST-NET-1
    "IP2": J(["198.", "51.100", ".7"]),
    "IP3": J(["203.", "0.113", ".45"]),
    "IPD": J(["192-", "0-2", "-10"]),
    "PHONE_P": J(["+1 415-", "555-", "0132"]),  # 555 numbers
    "PHONE_P2": J(["+1 415-", "555-", "0199"]),
    "PHONE10": J(["415", "555", "0132"]),
    "PHONEUK": J(["+44 20 ", "5550 ", "1234"]),
    "IBAN_DE": J(["DE89", "3704", "0044", "0532", "0130", "00"]),  # the published example IBANs
    "IBAN_GB": J(["GB82", "WEST", "1234", "5698", "7654", "32"]),
    "PAN": J(["4242", "4242", "4242", "4242"]),  # v6: a published test card number, contiguous
    "UUID": J(["123e4567-", "e89b-12d3-", "a456-426614174000"]),  # the RFC example
    "UUID2": J(["0f8fad5b-", "d9cb-469f-", "a165-70867728950e"]),
    "HOST": J(["db-7", ".corp", ".internal"]),  # made up
    "HOST2": J(["db01", ".prod", ".corp"]),
    "HOST3": J(["nas02", ".office", ".lan"]),
    "HOST4": J(["printer7", ".local"]),
    "HOST5": J(["a.b.c", ".internal"]),
}
V["UUIDUP"] = V["UUID"].upper()
V["UUIDHEAD"] = V["UUID"][:24]

# Is G4c merged into this tree? The G4c builder sets True in the G4c commit (ticket G8 v5, section 8.1). Until then the host
# rows are checked against `after` and rows 64 and 71 are strict xfails naming G4c.
G4C_MERGED = False

# fmt: off
ROWS = [
    (1, 'ipv4', 'control: spaces', 'from {IP1} ok', 'IP1', 'unchanged', 'from <IPV4_1> ok', 'from <IPV4_1> ok', None),
    (2, 'ipv4', 'letter after', 'from {IP1}a ok', 'IP1', 'closed', 'from {IP1}a ok', 'from <IPV4_1>a ok', None),
    (3, 'ipv4', 'word after', 'from {IP1}abc ok', 'IP1', 'closed', 'from {IP1}abc ok', 'from <IPV4_1>abc ok', None),
    (4, 'ipv4', '_x after', 'from {IP1}_x ok', 'IP1', 'closed', 'from {IP1}_x ok', 'from <IPV4_1>_x ok', None),
    (5, 'ipv4', '_ after', 'from {IP1}_ ok', 'IP1', 'closed', 'from {IP1}_ ok', 'from <IPV4_1>_ ok', None),
    (6, 'ipv4', 'digit after', 'from {IP1}9 ok', 'IP1', 'unchanged', 'from <IPV4_1> ok', 'from <IPV4_1> ok', None),
    (7, 'ipv4', 'letter before', 'from x{IP1} ok', 'IP1', 'closed', 'from x{IP1} ok', 'from x<IPV4_1> ok', None),
    (8, 'ipv4', 'word before (ip)', 'from ip{IP1} ok', 'IP1', 'closed', 'from ip{IP1} ok', 'from ip<IPV4_1> ok', None),
    (9, 'ipv4', '_ before', 'from node_{IP1} ok', 'IP1', 'closed', 'from node_{IP1} ok', 'from node_<IPV4_1> ok', None),
    (10, 'ipv4', 'digit before', 'from 7{IP1} ok', 'IP1', 'limit', 'from 7{IP1} ok', 'from 7{IP1} ok', None),
    (11, 'ipv4', 'both sides letters', 'from x{IP1}y ok', 'IP1', 'closed', 'from x{IP1}y ok', 'from x<IPV4_1>y ok', None),
    (12, 'ipv4', 'both sides _', 'from eth0_{IP1}_up ok', 'IP1', 'closed', 'from eth0_{IP1}_up ok', 'from eth0_<IPV4_1>_up ok', None),
    (13, 'ipv4', 'two glued IPs', 'from {IP1}{IP2} ok', 'IP1', 'limit', 'from {IP1}{IP2} ok', 'from {IP1}{IP2} ok', None),
    (14, 'ipv4', 'glued to UUID', 'from {UUID}{IP1} ok', 'IP1', 'closed', 'from {UUID}{IP1} ok', 'from <UUID_1><IPV4_1> ok', None),
    (15, 'ipv4', 'letter after + clean copy', 'from {IP1} and {IP1}a ok', 'IP1', 'closed', 'from <IPV4_1> and {IP1}a ok', 'from <IPV4_1> and <IPV4_1>a ok', None),
    (16, 'ipv4', 'after = with letter', 'src={IP3}x dst', 'IP3', 'closed', 'src={IP3}x dst', 'src=<IPV4_1>x dst', None),
    (17, 'phone', 'control: spaces', 'call {PHONE_P} now', 'PHONE_P', 'unchanged', 'call <PHONE_1> now', 'call <PHONE_1> now', None),
    (18, 'phone', 'letter after', 'call {PHONE_P}a now', 'PHONE_P', 'closed', 'call {PHONE_P}a now', 'call <PHONE_1>a now', None),
    (19, 'phone', '_x after', 'call {PHONE_P}_x now', 'PHONE_P', 'closed', 'call {PHONE_P}_x now', 'call <PHONE_1>_x now', None),
    (20, 'phone', '_ after', 'call {PHONE_P}_ now', 'PHONE_P', 'closed', 'call {PHONE_P}_ now', 'call <PHONE_1>_ now', None),
    (21, 'phone', 'letter before', 'call x{PHONE_P} now', 'PHONE_P', 'changed', 'call x+<PHONE_1> now', 'call x<PHONE_1> now', None),
    (22, 'phone', '_ before', 'call tel_{PHONE_P} now', 'PHONE_P', 'changed', 'call tel_+<PHONE_1> now', 'call tel_<PHONE_1> now', None),
    (23, 'phone', 'both sides', 'call x{PHONE_P}y now', 'PHONE_P', 'closed', 'call x{PHONE_P}y now', 'call x<PHONE_1>y now', None),
    (24, 'phone', 'clean copy + glued copy', 'call {PHONE_P} or {PHONE_P}a now', 'PHONE_P', 'closed', 'call <PHONE_1> or {PHONE_P}a now', 'call <PHONE_1> or <PHONE_1>a now', None),
    (25, 'phone', 'contiguous, letter after', 'call {PHONE10}a now', 'PHONE10', 'limit', 'call {PHONE10}a now', 'call {PHONE10}a now', None),
    (26, 'phone', 'contiguous, _x after', 'call {PHONE10}_x now', 'PHONE10', 'closed', 'call {PHONE10}_x now', 'call <PHONE_1>_x now', None),
    (27, 'phone', 'contiguous, letter before', 'call x{PHONE10} now', 'PHONE10', 'limit', 'call x{PHONE10} now', 'call x{PHONE10} now', None),
    (28, 'phone', 'contiguous, word before', 'call tel{PHONE10} now', 'PHONE10', 'closed', 'call tel{PHONE10} now', 'call tel<PHONE_1> now', None),
    (29, 'phone', 'contiguous, _ before', 'call tel_{PHONE10} now', 'PHONE10', 'closed', 'call tel_{PHONE10} now', 'call tel_<PHONE_1> now', None),
    (30, 'phone', 'contiguous, both _', 'call id_{PHONE10}_x now', 'PHONE10', 'closed', 'call id_{PHONE10}_x now', 'call id_<PHONE_1>_x now', None),
    (31, 'phone', 'contiguous, clean copy + glued', 'phone={PHONE10} then x{PHONE10} now', 'PHONE10', 'closed', 'phone=<PHONE_1> then x{PHONE10} now', 'phone=<PHONE_1> then x<PHONE_1> now', None),
    (32, 'phone', 'spaced UK, letter after', 'call {PHONEUK}a now', 'PHONEUK', 'closed', 'call <PHONE_1> 1234a now', 'call <PHONE_1>a now', None),
    (33, 'iban', 'control', 'pay {IBAN_DE} now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (34, 'iban', 'letter after (absorbed: alnum BBAN)', 'pay {IBAN_DE}a now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (35, 'iban', 'digit after', 'pay {IBAN_DE}9 now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (36, 'iban', '_x after', 'pay {IBAN_DE}_x now', 'IBAN_DE', 'closed', 'pay {IBAN_DE}_x now', 'pay <IBAN_1>_x now', None),
    (37, 'iban', '_ after', 'pay {IBAN_DE}_ now', 'IBAN_DE', 'closed', 'pay {IBAN_DE}_ now', 'pay <IBAN_1>_ now', None),
    (38, 'iban', 'letter before', 'pay x{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay x{IBAN_DE} now', 'pay x{IBAN_DE} now', None),
    (39, 'iban', 'word before', 'pay iban{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay iban{IBAN_DE} now', 'pay iban{IBAN_DE} now', None),
    (40, 'iban', 'digit before', 'pay 7{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay 7{IBAN_DE} now', 'pay 7{IBAN_DE} now', None),
    (41, 'iban', '_ before', 'pay iban_{IBAN_DE} now', 'IBAN_DE', 'closed', 'pay iban_{IBAN_DE} now', 'pay iban_<IBAN_1> now', None),
    (42, 'iban', 'both _', 'pay to_{IBAN_DE}_x now', 'IBAN_DE', 'closed', 'pay to_{IBAN_DE}_x now', 'pay to_<IBAN_1>_x now', None),
    (43, 'iban', 'clean copy + _x copy', 'pay {IBAN_DE} or {IBAN_DE}_x now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> or <IBAN_1>_x now', 'pay <IBAN_1> or <IBAN_1>_x now', None),
    (44, 'iban', 'GB, _x after', 'pay {IBAN_GB}_x now', 'IBAN_GB', 'closed', 'pay {IBAN_GB}_x now', 'pay <IBAN_1>_x now', None),
    (45, 'iban', 'GB, letter before', 'pay x{IBAN_GB} now', 'IBAN_GB', 'limit', 'pay x{IBAN_GB} now', 'pay x{IBAN_GB} now', None),
    (46, 'uuid', 'control', 'id {UUID} ok', 'UUID', 'unchanged', 'id <UUID_1> ok', 'id <UUID_1> ok', None),
    (47, 'uuid', 'digit after', 'id {UUID}9 ok', 'UUID', 'closed', 'id {UUID}9 ok', 'id <UUID_1>9 ok', None),
    (48, 'uuid', 'hex letter after', 'id {UUID}a ok', 'UUID', 'closed', 'id {UUID}a ok', 'id <UUID_1>a ok', None),
    (49, 'uuid', 'non-hex letter after', 'id {UUID}x ok', 'UUID', 'closed', 'id {UUID}x ok', 'id <UUID_1>x ok', None),
    (50, 'uuid', '_x after', 'id {UUID}_x ok', 'UUID', 'closed', 'id {UUID}_x ok', 'id <UUID_1>_x ok', None),
    (51, 'uuid', '_0 after (k8s)', 'id _default_{UUID}_0 ok', 'UUID', 'closed', 'id _default_{UUID}_0 ok', 'id _default_<UUID_1>_0 ok', None),
    (52, 'uuid', 'letter before (non-hex)', 'id x{UUID} ok', 'UUID', 'closed', 'id x{UUIDHEAD}<ACCOUNTID_1> ok', 'id x<UUID_1> ok', None),
    (53, 'uuid', 'hex letter before', 'id a{UUID} ok', 'UUID', 'closed', 'id a{UUIDHEAD}<ACCOUNTID_1> ok', 'id a<UUID_1> ok', None),
    (54, 'uuid', 'digit before', 'id 7{UUID} ok', 'UUID', 'closed', 'id 7{UUIDHEAD}<ACCOUNTID_1> ok', 'id 7<UUID_1> ok', None),
    (55, 'uuid', '_ before', 'id pod_{UUID} ok', 'UUID', 'closed', 'id pod_{UUIDHEAD}<ACCOUNTID_1> ok', 'id pod_<UUID_1> ok', None),
    (56, 'uuid', 'both letters', 'id x{UUID}y ok', 'UUID', 'closed', 'id x{UUID}y ok', 'id x<UUID_1>y ok', None),
    (57, 'uuid', 'upper, _x after', 'id {UUIDUP}_x ok', 'UUIDUP', 'closed', 'id {UUIDUP}_x ok', 'id <UUID_1>_x ok', None),
    (58, 'uuid', 'clean copy + glued copy', 'id {UUID} then {UUID}x ok', 'UUID', 'closed', 'id <UUID_1> then {UUID}x ok', 'id <UUID_1> then <UUID_1>x ok', None),
    (59, 'host', 'control', 'x {HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (60, 'host', 'digit after', 'x {HOST}9 y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internal9 y', 'x <HOSTNAME_1>.internal9 y', 'x <HOSTNAME_1> y'),
    (61, 'host', 'letter after', 'x {HOST}a y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internala y', 'x <HOSTNAME_1>.internala y', 'x <HOSTNAME_1> y'),
    (62, 'host', '_x after', 'x {HOST}_x y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internal_x y', 'x <HOSTNAME_1>.internal_x y', 'x <HOSTNAME_1> y'),
    (63, 'host', 'letter before', 'x z{HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (64, 'host', '_ before', 'x svc_{HOST} y', 'HOST', 'g4c', 'x svc_db-<HOSTNAME_1> y', 'x svc_db-<HOSTNAME_1> y', 'x <HOSTNAME_1> y'),
    (65, 'host', 'digit before', 'x 9{HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (66, 'host', 'clean copy + glued', 'x {HOST} then {HOST}a y', 'HOST', 'unchanged', 'x <HOSTNAME_1> then <HOSTNAME_2>.internala y', 'x <HOSTNAME_1> then <HOSTNAME_2>.internala y', 'x <HOSTNAME_1> then <HOSTNAME_2> y'),
    (67, 'host', 'ends at corp, letter after', 'x {HOST2}a y', 'HOST2', 'limit', 'x {HOST2}a y', 'x {HOST2}a y', None),
    (68, 'host', 'ends at corp, digit after', 'x {HOST2}9 y', 'HOST2', 'limit', 'x {HOST2}9 y', 'x {HOST2}9 y', None),
    (69, 'host', 'ends at corp, _x after', 'x {HOST2}_x y', 'HOST2', 'limit', 'x {HOST2}_x y', 'x {HOST2}_x y', None),
    (70, 'host', 'lan, letter after', 'x {HOST3}x y', 'HOST3', 'limit', 'x {HOST3}x y', 'x {HOST3}x y', None),
    (71, 'host', 'lan, _ before', 'x vm_{HOST3} y', 'HOST3', 'g4c', 'x vm_nas02.<HOSTNAME_1> y', 'x vm_nas02.<HOSTNAME_1> y', 'x <HOSTNAME_1> y'),
    (72, 'ipv4', 'dashed EC2 name, letter after', 'node ip-{IPD}a ready', 'IPD', 'closed', 'node ip-{IPD}a ready', 'node ip-<IPV4_1>a ready', None),
    (73, 'ipv4', 'dashed EC2 name, _x after', 'node ip-{IPD}_x ready', 'IPD', 'closed', 'node ip-{IPD}_x ready', 'node ip-<IPV4_1>_x ready', None),
    (74, 'ipv4', 'letter between two IPs', 'from {IP1}x{IP2} ok', 'IP1', 'closed', 'from {IP1}x{IP2} ok', 'from <IPV4_1>x<IPV4_2> ok', None),
    (75, 'phone', 'two formatted phones glued', 'call {PHONE_P}{PHONE_P2} now', 'PHONE_P', 'changed', 'call <PHONE_1>+<PHONE_2> now', 'call <PHONE_1><PHONE_2> now', None),
    (76, 'iban', 'two IBANs glued', 'pay {IBAN_DE}{IBAN_GB} now', 'IBAN_DE', 'limit', 'pay {IBAN_DE}{IBAN_GB} now', 'pay {IBAN_DE}{IBAN_GB} now', None),
    (77, 'uuid', 'two UUIDs glued', 'id {UUID}{UUID2} ok', 'UUID', 'closed', 'id {UUID}{UUID2} ok', 'id <UUID_1><UUID_2> ok', None),
    (78, 'host', 'bare .local, digit after', 'x {HOST4}9 y', 'HOST4', 'limit', 'x {HOST4}9 y', 'x {HOST4}9 y', None),
    (79, 'host', 'bare .local, _x after', 'x {HOST4}_x y', 'HOST4', 'limit', 'x {HOST4}_x y', 'x {HOST4}_x y', None),
    (80, 'host', 'bare .internal, letter after', 'x {HOST5}x y', 'HOST5', 'limit', 'x {HOST5}x y', 'x {HOST5}x y', None),
    # v3 (G8-review-2 F4): the dashed forms glued BEFORE the address
    (81, 'ipv4', 'dashed EC2 name, _ before', 'node host_ip-{IPD} up', 'IPD', 'closed', 'node host_ip-{IPD} up', 'node host_ip-<IPV4_1> up', None),
    (82, 'ipv4', 'dashed EC2 name (ec2), _ before', 'node my_ec2-{IPD} up', 'IPD', 'closed', 'node my_ec2-{IPD} up', 'node my_ec2-<IPV4_1> up', None),
    (83, 'ipv4', 'pod DNS, _ before', 'pod_{IPD}.ns.pod up', 'IPD', 'closed', 'pod_{IPD}.ns.pod up', 'pod_<IPV4_1>.ns.pod up', None),
    (84, 'ipv4', 'pod DNS, letter before', 'x{IPD}.ns.pod up', 'IPD', 'closed', 'x{IPD}.ns.pod up', 'x<IPV4_1>.ns.pod up', None),
    (85, 'ipv4', 'dashed EC2 name, letter before ip-', 'node xip-{IPD} up', 'IPD', 'limit', 'node xip-{IPD} up', 'node xip-{IPD} up', None),
    (86, 'ipv4', 'pod DNS, digit before', '7{IPD}.ns.pod up', 'IPD', 'limit', '7{IPD}.ns.pod up', '7{IPD}.ns.pod up', None),
    # v4 (G8-review-3-codebase M1): `_` beside an IBAN counts only in a short word context, so these two stay (limit L4)
    (87, 'iban', 'snake_case key, _ before', 'pay acct_iban_{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay acct_iban_{IBAN_DE} now', 'pay acct_iban_{IBAN_DE} now', None),
    (88, 'iban', '_ + 9 letters after', 'pay {IBAN_DE}_reference now', 'IBAN_DE', 'limit', 'pay {IBAN_DE}_reference now', 'pay {IBAN_DE}_reference now', None),
    # v5 (G8-review-4-design M1): realistic file, path and key shapes outside the short-word context (limit L4)
    (89, 'iban', 'file name: iban_ + _date after', 'pay iban_{IBAN_DE}_2026-11-20 now', 'IBAN_DE', 'limit', 'pay iban_{IBAN_DE}_2026-11-20 now', 'pay iban_{IBAN_DE}_2026-11-20 now', None),
    (90, 'iban', 'two _ segments after', 'pay {IBAN_DE}_a_b now', 'IBAN_DE', 'limit', 'pay {IBAN_DE}_a_b now', 'pay {IBAN_DE}_a_b now', None),
    (91, 'iban', 'path: / before, _x after', 'pay dir/{IBAN_DE}_x now', 'IBAN_DE', 'limit', 'pay dir/{IBAN_DE}_x now', 'pay dir/{IBAN_DE}_x now', None),
    (92, 'iban', 'dashed key: - before, _x after', 'pay acct-{IBAN_DE}_x now', 'IBAN_DE', 'limit', 'pay acct-{IBAN_DE}_x now', 'pay acct-{IBAN_DE}_x now', None),
    # v6 (G8-review-5-design N2): more `_` shapes outside the short-word context (limit L4)
    (93, 'iban', 'word of 11 letters + _ before', 'pay beneficiary_{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay beneficiary_{IBAN_DE} now', 'pay beneficiary_{IBAN_DE} now', None),
    (94, 'iban', 'word of 9 letters + _ before', 'pay recipient_{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay recipient_{IBAN_DE} now', 'pay recipient_{IBAN_DE} now', None),
    (95, 'iban', 'dashed key + iban_ before', 'pay customer-iban_{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay customer-iban_{IBAN_DE} now', 'pay customer-iban_{IBAN_DE} now', None),
    (96, 'iban', 'double _ before', 'pay iban__{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay iban__{IBAN_DE} now', 'pay iban__{IBAN_DE} now', None),
    # v6 (G8-review-5-design M2): a contiguous card number glued to a letter (limit L14: the PHONE entries refuse a letter)
    (97, 'card', 'contiguous, letter before', 'pay x{PAN} now', 'PAN', 'limit', 'pay x{PAN} now', 'pay x{PAN} now', None),
    (98, 'card', 'contiguous, letter after', 'pay {PAN}x now', 'PAN', 'limit', 'pay {PAN}x now', 'pay {PAN}x now', None),
    (99, 'card', 'contiguous, word before', 'pay card{PAN} now', 'PAN', 'limit', 'pay card{PAN} now', 'pay card{PAN} now', None),
    # v6 (G8-review-5-design N4): a phone word inside a longer word (limit L3: entry 8 refuses a letter before the word)
    (100, 'phone', 'contiguous, telephone before', 'call telephone{PHONE10} now', 'PHONE10', 'limit', 'call telephone{PHONE10} now', 'call telephone{PHONE10} now', None),
    (101, 'phone', 'contiguous, cellphone before', 'call cellphone{PHONE10} now', 'PHONE10', 'limit', 'call cellphone{PHONE10} now', 'call cellphone{PHONE10} now', None),
]
# fmt: on

PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
HOST_SUFFIX_LABELS = ("corp", "internal", "local", "lan", "intranet", "prod", "office")
LEAK_RUN = {"ipv4": 7, "iban": 8, "uuid": 8}  # phone: 4 digits; host: see leak()


def fill(template: str | None) -> str | None:
    return None if template is None else template.format(**V)


def case(row: tuple) -> dict:
    rid, kind, shape, text, value, cls, now, after, after_g4c = row
    after = fill(after)
    return {
        "id": rid,
        "kind": kind,
        "shape": shape,
        "text": fill(text),
        "value": V[value],
        "cls": cls,
        "now": fill(now),
        "after": after,
        "expected": fill(after_g4c) if (G4C_MERGED and after_g4c) else after,
    }


CASES = [case(r) for r in ROWS]
BY_ID = {c["id"]: c for c in CASES}


def _lcs(a: str, b: str) -> int:
    return (
        difflib.SequenceMatcher(None, a, b, autojunk=False)
        .find_longest_match(0, len(a), 0, len(b))
        .size
    )


def _digits(s: str) -> str:
    return re.sub(r"[ \-]", "", s)


def leak(kind: str, value: str, out: str) -> bool:
    """The G8 leak rule: is `value` (of probe kind `kind`) still readable in `out` outside the placeholders?
    ipv4: 7 characters of the value in a row; iban, uuid: 8; phone and card (v6): 4 digits in a row once spaces and
    hyphens are taken out of both (a leading `+` of the value ignored); host: any label of the name other than HOST_SUFFIX_LABELS, or 2 or more
    leading characters of such a label directly before a placeholder (`svc_db-<HOSTNAME_1>`)."""
    rest = PLACEHOLDER.sub("|", out)
    if kind == "host":
        labels = [x for x in value.lower().split(".") if x not in HOST_SUFFIX_LABELS]
        low = rest.lower()
        if any(x in low for x in labels):
            return True
        return any((x[:k] + "|") in low for x in labels for k in range(2, len(x)))
    if value in rest:
        return True
    if kind in ("phone", "card"):  # v6: card rows 97-99
        return _lcs(_digits(value).lstrip("+"), _digits(rest)) >= 4
    return _lcs(value, rest) >= LEAK_RUN[kind]


SHA = J(["3851007894", "abcdef0123456789abcdef0123456789abcdef0123456789abcd"])
P10 = V["PHONE10"]
SSN = J(["123", "-45-", "6789"])
CARD = J(["4242 ", "4242 ", "4242 ", "4242"])
ALNUM = string.ascii_uppercase + string.ascii_lowercase + string.digits
# G8-review-2 F1: an IBAN-shaped tail (`a` + `DE89` + 18 letters or digits) at the end of an opaque token.
F1_TAIL = J(["a", "DE89", "Xq7Lm2Pw9Rt4Ys6Vb3"])
# G8-review-3-codebase M1: the same IBAN shape set off by `_` (a base64url character) or by `-` and `_` inside a token.
F1_MID = F1_TAIL[1:]


def opaque(n: int) -> str:
    """n characters of a made-up token with upper case, lower case and digits (no IBAN or other shape inside)."""
    return J(ALNUM[(7 * i + 3) % 62] for i in range(n))


# (id, text, now, after, verdict); None = the text itself. verdict: kept (nothing masked, before and after) | same (masked
# today, G8 does not change it, or changes only what the note says) | over-mask L-Dn (accepted by that decision) | closed (a
# real value newly masked). K1-K28 are v1's table; K29-K74 the reviewers' examples and the drafter's v2 traces; K75-K80 v3's
# (G8-review-2 F1 and F6); K81-K84 v4's (G8-review-3-codebase N4 and M1). The opaque tokens of K75-K77 and K83-K84 are
# built here (`opaque()`), not written out.
MUST_KEEP = [
    ("K1", "release v1.2.3.4 shipped", None, None, "kept (L-D1)"),
    ("K2", "node-v18.19.1.2 build", None, None, "kept (L-D1)"),
    ("K3", "dotted date 2026.11.20.10 ok", None, None, "kept (L1)"),
    ("K4", "oid 1.3.6.1.4.1 ok", "oid <IPV4_1>.4.1 ok", "oid <IPV4_1>.4.1 ok", "same"),
    ("K5", "sha " + SHA, None, None, "kept"),
    ("K6", "commit " + P10 + "abcdef ok", None, None, "kept (L3)"),
    ("K7", "build" + P10 + " ok", None, None, "kept (L3)"),
    ("K8", "img sha256_" + SHA[:16], None, None, "kept"),
    ("K9", "wave2-2026-09-11T14:12:03Z", None, None, "kept"),
    ("K10", "orders-db-ro-1 up", None, None, "kept"),
    ("K11", "build-1234-5678-90 ok", None, None, "kept"),
    ("K12", "job-415-555-0132 ok", None, None, "kept"),
    ("K13", "pod web-5d8f9c7b6-x2x7q", None, None, "kept"),
    ("K14", "x86_64-linux-gnu", None, None, "kept"),
    ("K15", "eth0_up", None, None, "kept"),
    ("K16", "run_20261120101112_x ok", None, None, "kept"),
    ("K17", "self.local_cache = 1", None, None, "kept"),
    ("K18", "obj.internal_state", None, None, "kept"),
    ("K19", "nltk.corpus.reader", None, None, "kept"),
    ("K20", "acme.corporate.site", None, None, "kept"),
    ("K21", "ctx.local9", None, None, "kept"),
    ("K22", "vlan10.lan2 ok", None, None, "kept"),
    ("K23", "token AB12CDEFGHIJKLMNOPQ ok", None, None, "kept"),
    ("K24", "req ReqIdDE12345678901234 ok", None, None, "kept (L-D2)"),
    ("K25", "tag xDE00ABCDEFGHIJK ok", None, None, "kept (L-D2)"),
    ("K26", "ts 1732095071000_x", None, "ts <PHONE_1>_x", "over-mask L-D10"),
    (
        "K27",
        "uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe",
        None,
        "uuid-ish <UUID_1>cafe",
        "over-mask L-D4",
    ),
    ("K28", "id " + V["UUID"].replace("-", "") + " ok", None, None, "kept"),
    ("K29", "eth0 1500 9000", None, None, "kept"),
    ("K30", "ipv4 1500 1600", None, None, "kept"),
    ("K31", "vlan10 2001 2002", None, None, "kept"),
    ("K32", "node1 8080 9090", None, None, "kept"),
    ("K33", "PO12-3456-7890", None, None, "kept"),
    (
        "K34",
        "rtt 120 118 131 125ms",
        "rtt <PHONE_1> 125ms",
        "rtt <PHONE_1> 125ms",
        "same (L-D9: 3 of 4 masked today)",
    ),
    ("K35", "backup_20-11-2026 done", None, None, "kept"),
    ("K36", "x" + CARD, "x4242 <PHONE_1>", "x<CREDITCARD_1>", "closed (L-D12)"),
    ("K37", "INV2026-0042-1234", None, None, "kept"),
    ("K38", "ISBN978-3-16-148410-0", None, None, "kept"),
    ("K39", "sha256-" + SHA[:16], None, None, "kept"),
    ("K40", "mac00-11-22-33-44-55", None, None, "kept"),
    ("K41", "ref hunter" + SSN, None, None, "kept (L-D11)"),
    (
        "K42",
        "password=hunter\nref hunter" + SSN,
        "password=<SECRET_1>\nref <SECRET_1><SSN_1>",
        "password=<SECRET_1>\nref <SECRET_1><SSN_1>",
        "same (the G7 boundary-class pin)",
    ),
    ("K43", "python3.11.4.1", None, "python<IPV4_1>", "over-mask L-D8"),
    ("K44", "python3.11.2.1", None, "python<IPV4_1>", "over-mask L-D8"),
    ("K45", "jdk1.8.0.292", None, "jdk<IPV4_1>", "over-mask L-D8"),
    ("K46", "node18.19.1.2", None, "node<IPV4_1>", "over-mask L-D8"),
    ("K47", "libssl1.2.3.4", None, "libssl<IPV4_1>", "over-mask L-D8"),
    ("K48", "rev1.2.3.4", None, "rev<IPV4_1>", "over-mask L-D8"),
    ("K49", "libc6_2.36.0.1_amd64.deb", None, "libc6_<IPV4_1>_amd64.deb", "over-mask L-D8"),
    ("K50", "nginx_1.18.0.1-1_amd64.deb", None, "nginx_<IPV4_1>-1_amd64.deb", "over-mask L-D8"),
    ("K51", "1.0.0.0a2", None, "<IPV4_1>a2", "over-mask L-D8"),
    ("K52", "2.0.1.0b3", None, "<IPV4_1>b3", "over-mask L-D8"),
    ("K53", "1.2.3.4rc1", None, "<IPV4_1>rc1", "over-mask L-D8"),
    ("K54", "order_1234567890", None, "order_<PHONE_1>", "over-mask L-D10"),
    ("K55", "user_1234567890", None, "user_<PHONE_1>", "over-mask L-D10"),
    ("K56", "ts_1732095071", None, "ts_<PHONE_1>", "over-mask L-D10"),
    ("K57", "epoch_1732095071", None, "epoch_<PHONE_1>", "over-mask L-D10"),
    ("K58", "trace_1732095071000", None, "trace_<PHONE_1>", "over-mask L-D10"),
    ("K59", "snap_2026112010", None, "snap_<PHONE_1>", "over-mask L-D10"),
    (
        "K60",
        "b64url Zm9vYmFy_1234567890_YmF6",
        None,
        "b64url Zm9vYmFy_<PHONE_1>_YmF6",
        "over-mask L-D10",
    ),
    ("K61", "id_123456789012345678 ok", None, None, "kept"),
    ("K62", "ts+1000000000", "ts+<PHONE_1>", "ts<PHONE_1>", "same (the + moves inside)"),
    ("K63", "now+3600000000", "now+<PHONE_1>", "now<PHONE_1>", "same (the + moves inside)"),
    ("K64", "<TENANT_" + P10 + ">", None, None, "kept"),
    (
        "K65",
        "call " + P10 + " or " + V["PHONE_P"],
        "call <PHONE_1> or <PHONE_2>",
        "call <PHONE_2> or <PHONE_1>",
        "same (numbering changes)",
    ),
    ("K66", "blob aGVsbG8+aDE12abcdefghijk/x", None, None, "kept (L-D2)"),
    (
        "K67",
        "known 1.2.3.4 and v1.2.3.4",
        "known <IPV4_1> and v1.2.3.4",
        "known <IPV4_1> and v1.2.3.4",
        "same (L-D1)",
    ),
    ("K68", "rev 2-" + SHA[:16], None, None, "kept"),
    ("K69", "color #415555 and #0a0b0c", None, None, "kept"),
    ("K70", "sizes 1024 2048 4096ms", None, None, "kept (L-D9)"),
    (
        "K71",
        "took 100 200 300 400ms",
        "took <PHONE_1> 400ms",
        "took <PHONE_1> 400ms",
        "same (L-D9: 3 of 4 masked today)",
    ),
    (
        "K72",
        "call 415-555-0132x123",
        None,
        None,
        "kept (L-D9: an extension glued to a number without + stays readable)",
    ),
    ("K73", "ssn " + SSN + "a", None, None, "kept (L-D11: a stated limit, not a choice)"),
    ("K74", "card " + CARD + "x", "card <PHONE_1> 4242x", "card <CREDITCARD_1>x", "closed (L-D12)"),
    (
        "K75",
        "key " + opaque(37) + F1_TAIL + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D2: F1, 60 characters)",
    ),
    (
        "K76",
        "key " + opaque(117) + F1_TAIL + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D2: F1, 140)",
    ),
    (
        "K77",
        "Authorization: Bearer " + opaque(37) + F1_TAIL + " end",
        "Authorization: Bearer <BEARER_1> end",
        "Authorization: Bearer <BEARER_1> end",
        "same (L-D2: F1, BEARER)",
    ),
    ("K78", "+123-45-6789x", None, "<PHONE_1>x", "over-mask L-D11 (stored as PHONE)"),
    ("K79", "x+" + SSN, "x+<SSN_1>", "x+<SSN_1>", "same (the SSN entry runs first)"),
    (
        "K80",
        "card_" + CARD.replace(" ", "-") + "_x",
        None,
        "card_<CREDITCARD_1>_x",
        "closed (L-D12)",
    ),
    # v4 (G8-review-3-codebase N4): a date right after `+` is not a phone number (PHONE entry 6's date guard).
    ("K81", "x+2026-11-20T10:00:00Z", None, None, "kept (N4)"),
    ("K82", "t+2026-11-20 1012 ok", None, None, "kept (N4)"),
    # v4 (G8-review-3-codebase M1): an IBAN shape inside a base64url token: after `_` and before `-` (K83), after `-` and
    # before `_` (K84). Both are whole HIGHENTROPY tokens on the base and must stay so.
    (
        "K83",
        "key " + opaque(20) + "_" + F1_MID + "-" + opaque(17) + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D15: M1, `_` before and `-` after, 61 characters)",
    ),
    (
        "K84",
        "key " + opaque(20) + "-" + F1_MID + "_" + opaque(5) + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D15: M1, `-` before and `_` after, 49 characters)",
    ),
]
# Found on the way, NOT glued (stated limit L7): a phone number before a full stop is not masked, or only in part.
# (id, text, now, after); None = the text itself. F1-F3: unchanged by G8. v5 (G8-review-4-design N2): F4, a spaced `+`
# number glued to a letter before a full stop: the main entry masks its head on the base and `1234.` stays readable; G8's
# entry 6 takes the `+` inside, the last group stays readable (as on the base).
FULL_STOP = [
    ("F1", "call 415-555-0132.", None, None),
    ("F2", "call " + P10 + ".", None, None),
    ("F3", "call " + V["PHONE_P"] + ".", None, None),
    ("F4", "call x" + V["PHONEUK"] + ".", "call x+<PHONE_1> 1234.", "call x<PHONE_1> 1234."),
]
# At rest (G8-review-2 F6): (id, text, now, after): each side is (text, sorted map items, sorted storable items) of
# `redact(text)` and `runmap.storable(mapping)`. AT1-AT3: a piece of a secret with a stored kind's shape is registered under
# that kind and is storable (limit L11; AT4 shows the base does the same for a piece set off by `-`). AT5, AT6: IBAN in
# `runmap._SECRET_PATTERNS` (the start now accepts `_`): an ARN that holds `_DE89...` is no longer storable, a tenant is split.
IP1, IBAN = V["IP1"], V["IBAN_DE"]
AT_REST = [
    (
        "AT1",
        "password=hunter" + IP1 + "x",
        ("password=<SECRET_1>", [("<SECRET_1>", "hunter" + IP1 + "x")], []),
        (
            "password=<SECRET_1>",
            [("<IPV4_1>", IP1), ("<SECRET_1>", "hunter" + IP1 + "x")],
            [("<IPV4_1>", IP1)],
        ),
    ),
    (
        "AT2",
        "password=hunter_" + P10,
        ("password=<SECRET_1>", [("<SECRET_1>", "hunter_" + P10)], []),
        (
            "password=<SECRET_1>",
            [("<PHONE_1>", P10), ("<SECRET_1>", "hunter_" + P10)],
            [("<PHONE_1>", P10)],
        ),
    ),
    (
        "AT3",
        "token=x+1" + P10 + "y",
        ("token=<SECRET_1>", [("<SECRET_1>", "x+1" + P10 + "y")], []),
        (
            "token=<SECRET_1>",
            [("<PHONE_1>", "+1" + P10), ("<SECRET_1>", "x+1" + P10 + "y")],
            [("<PHONE_1>", "+1" + P10)],
        ),
    ),
    (
        "AT4",
        "password=a-" + IP1 + "-b",
        (
            "password=<SECRET_1>",
            [("<IPV4_1>", IP1), ("<SECRET_1>", "a-" + IP1 + "-b")],
            [("<IPV4_1>", IP1)],
        ),
        None,
    ),
    (
        "AT5",
        "arn:aws:s3:::bucket_" + IBAN,
        (
            "<ARN_1>",
            [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)],
            [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)],
        ),
        ("<ARN_1>", [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)], []),
    ),
    (
        "AT6",
        "tenant_id=acme_" + IBAN,
        (
            "tenant_id=<TENANT_1>",
            [("<TENANT_1>", "acme_" + IBAN)],
            [("<TENANT_1>", "acme_" + IBAN)],
        ),
        (
            "tenant_id=<TENANT_1><IBAN_1>",
            [("<IBAN_1>", IBAN), ("<TENANT_1>", "acme_")],
            [("<TENANT_1>", "acme_")],
        ),
    ),
    # v4 (G8-review-3-codebase N1): L-D12's over-mask: an order number in card groups glued to letters is masked as
    # CREDITCARD (a SECRET kind: in the map, never storable, so not restorable after the run).
    (
        "AT7",
        "ORD" + J(["1234-", "5678-", "9012-", "3456"]),
        ("ORD" + J(["1234-", "5678-", "9012-", "3456"]), [], []),
        ("ORD<CREDITCARD_1>", [("<CREDITCARD_1>", J(["1234-", "5678-", "9012-", "3456"]))], []),
    ),
    # v6 (G8-review-5-design M2): a contiguous card number beside `_` is masked by PHONE entry 7 and STORED as PHONE (AT8);
    # the base already stores a clean contiguous card number as PHONE (AT9, unchanged by G8).
    (
        "AT8",
        "card_" + V["PAN"],
        ("card_" + V["PAN"], [], []),
        ("card_<PHONE_1>", [("<PHONE_1>", V["PAN"])], [("<PHONE_1>", V["PAN"])]),
    ),
    (
        "AT9",
        "card " + V["PAN"],
        ("card <PHONE_1>", [("<PHONE_1>", V["PAN"])], [("<PHONE_1>", V["PAN"])]),
        None,
    ),
]
# v4 (G8-review-3-codebase M2): (id, call, text, expected): `redact_untrusted` escapes a placeholder-shaped literal to
# `‹KIND_n›`; the escaped literal is text, and its number is not a phone number (PHONE entry 7 refuses `›` after).
UNTRUSTED = [
    ("U1", "redact_untrusted", "<TENANT_" + P10 + ">", "‹TENANT_" + P10 + "›"),
    ("U2", "redact_text", "‹TENANT_" + P10 + "›", "‹TENANT_" + P10 + "›"),
]


def keep_case(row: tuple) -> dict:
    kid, text, now, after, verdict = row
    return {
        "id": kid,
        "text": text,
        "now": text if now is None else now,
        "after": text if after is None else after,
        "verdict": verdict,
    }


KEEP = [keep_case(r) for r in MUST_KEEP]


if (
    __name__ == "__main__"
):  # step 0: on the base commit every `now` must hold (exit 1 otherwise); the output is the record
    from hadavin_sdk.guard.redact import redact

    bad = 0
    for c in CASES:
        got = redact(c["text"]).text
        bad += got != c["now"]
        print(("ok  " if got == c["now"] else "BAD ") + f"row {c['id']}: {got!r}")
    for k in KEEP + [keep_case((f, t, now, after, "L7")) for f, t, now, after in FULL_STOP]:
        got = redact(k["text"]).text
        bad += got != k["now"]
        print(("ok  " if got == k["now"] else "BAD ") + f"{k['id']}: {got!r}")
    from hadavin_sdk.guard.runmap import storable

    for aid, text, now, _after in AT_REST:
        r = redact(text)
        got = (r.text, sorted(r.mapping.items()), sorted(storable(dict(r.mapping)).items()))
        bad += got != now
        print(("ok  " if got == now else "BAD ") + f"{aid}: {got!r}")
    from hadavin_sdk.guard import runmap

    for uid, call, text, want in UNTRUSTED:
        m = runmap.RunMap()
        got = (getattr(runmap, call)(text, m), dict(m))
        bad += got != (want, {})
        print(("ok  " if got == (want, {}) else "BAD ") + f"{uid}: {got!r}")
    print(f"{bad} differ", file=sys.stderr)
    sys.exit(1 if bad else 0)
