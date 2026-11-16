"""The one place every shared fact of the v31 package is written. Sources use {{name}}; build-v31.py fills them in.
Every number below is computed from the first lines (integers where money is concerned). Nothing else may state these facts."""
from decimal import Decimal as Dc
import datetime as dt
TOK_IN, TOK_OUT, P_IN_C, P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3      # tokens, US cents per million tokens, calls
LEDGER_C = 1240; BALANCE_C = 18900; NEED_S = 860; Y, RL, FP, MG = 5, 15, 10, 10
DAY = dt.date(2026, 11, 18); DEADLINE = dt.datetime(2026, 11, 23, 18, 29); POSTBY = dt.datetime(2026, 11, 25, 15, 0)
IST = dt.timedelta(hours=5, minutes=30)
def usd(c): return '%d.%02d' % (c // 100, c % 100)
price_c_x = TOK_IN * P_IN_C + TOK_OUT * P_OUT_C           # cents x 1e6 per call
assert price_c_x % 10000 == 0
PRICE_C = price_c_x // 1000000 if price_c_x % 1000000 == 0 else None
price_cents = Dc(price_c_x) / Dc(1000000)                  # 27 cents
assert price_cents == 27
TOTAL_C = int(price_cents) * CEIL; LIMIT_C = LEDGER_C + TOTAL_C
def t(d): return d.strftime('%H:%M')
def pair(d, secs=False):
    f = '%H:%M:%S' if secs else '%H:%M'
    return '%s UTC = %s IST' % (d.strftime(f), (d + IST).strftime(f))
LS = dt.datetime.combine(DAY, dt.time(11, 30)); LF = LS + dt.timedelta(minutes=Y + RL + FP); CB = LF + dt.timedelta(minutes=MG)
EK = dt.datetime.combine(DAY, dt.time(10, 30))
OKB = dt.datetime.combine(DAY, dt.time(16, 0))                # latest time to cancel the older key in B (run day); must be well before 18:14 UTC
assert OKB.time() < dt.time(18, 14)
assert CB < OKB, 'B: the older-key time must come after cancel-by'  # the run is over before the B cancel time
LAST = DEADLINE - dt.timedelta(seconds=NEED_S)
CAP = DEADLINE - dt.timedelta(minutes=Y + RL + FP + MG + 10)
D23_CB = DEADLINE - dt.timedelta(minutes=10)
LS23 = dt.datetime(2026, 11, 23, 18, 4)      # lead ORDER L-23NOV: latest start on Mon 23 Nov (derivation asked in v31-OPEN-FOR-LEAD)
RV23 = dt.datetime(2026, 11, 23, 18, 19)     # key revoked by this time even if a take runs (L-23NOV)
assert -(-NEED_S // 60) <= RL
SEVENBACK = EK - dt.timedelta(hours=168)         # the 7-day rule: the older key's last use must be before this (A)
BS = dt.datetime(2026, 11, 22, 18, 9)          # deadline reminder (owner action through Sun 22 Nov): revoke time 18:19 UTC minus 10 minutes
assert SEVENBACK.strftime('%a') == 'Wed' and BS.strftime('%a') == 'Sun' and BS + dt.timedelta(minutes=10) < RV23
GAP_MAX = 60                                      # latest start minus earliest key time, at most (minutes)
assert (LS - EK).seconds // 60 <= GAP_MAX
PH = {'mkc': 'model key cancelled', 'nokey': 'no key was made', 'cf': 'cancel failed', 'tp': 'time passed', 'rs': 'run started',
      'cd': 'contacts deleted <number>', 'apr': 'app passwords revoked', 'hsr': 'HubSpot apps revoked', 'dmd': 'demo mails deleted <number>',
      'acc': 'accepted', 'posted': 'posted', 'dec': 'I decline', 'ksf': 'key save failed, cancelled, new run name <name>',
      'older': 'I cancel the older key <its name>, nothing else I know uses it',
      'older711': 'I cancel the older key <its name> now, the yes covers it',
      'req': 'send the numbers message for run <run name>',
      'msg': 'got a message that says <in words>, is it yours'}
F = {
 'price': '0.%02d' % int(price_cents), 'total': usd(TOTAL_C), 'limit': usd(LIMIT_C), 'limit_cents': str(LIMIT_C), 'ledger': usd(LEDGER_C),
 'balance': usd(BALANCE_C), 'need_s': str(NEED_S), 'need_min': '%.2f' % (NEED_S / 60), 'rl': str(RL), 'y': str(Y), 'fp': str(FP), 'mg': str(MG),
 'sum': str(Y + RL + FP), 'ceil': str(CEIL), 'tok_in': str(TOK_IN), 'tok_out': str(TOK_OUT), 'p_in': usd(P_IN_C), 'p_out': usd(P_OUT_C),
 'p_in_c': str(P_IN_C), 'p_out_c': str(P_OUT_C),
 'day': DAY.strftime('%a %d %b %Y'), 'day_date': DAY.strftime('%a %b %d'), 'dl_full': '2026-11-23 ' + pair(DEADLINE), 'dl': pair(DEADLINE), 'dl_day': 'Mon 23 Nov 2026', 'dl_iso': '2026-11-23T18:29:00Z', 'dl_sp': '2026-11-23 18:29 UTC',
 'ek': pair(EK), 'okb': pair(OKB), 'ls': pair(LS), 'lf': pair(LF), 'cb': pair(CB), 'last': pair(LAST, True), 'cap': t(CAP), 'cap_x': '%d minutes' % (Y + RL + FP + MG + 10),
 'd23cb': pair(D23_CB), 'ls23': pair(LS23), 'rv23': pair(RV23), 'last_label': 'the program\'s refusal limit: ' + pair(LAST, True), 'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST', 'ls_t': t(LS), 'lf_t': t(LF), 'cb_t': t(CB),
 'sevenback': SEVENBACK.strftime('%a %d %b %Y ') + pair(SEVENBACK), 'bs': BS.strftime('%a %d %b %Y ') + pair(BS), 'bs_t': pair(BS), 'gap_max': str(GAP_MAX),
 'think': '20', 'ps_t': '11:08:07', 'set_t': '11:06:55', 'key_t': '11:07:30',
}
for k, v in PH.items(): F['ph_' + k] = v
