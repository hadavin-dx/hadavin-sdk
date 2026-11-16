"""Builds verify16.py from verify15.py (paths relative to this file). Each replacement must match exactly once."""
import os
H = os.path.dirname(os.path.abspath(__file__)) + '/'
s = open(H + 'verify15.py', encoding='utf-8').read()
errs = []
def R(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: errs.append((c, n, old[:70])); return
    s = s.replace(old, new)
R("scratch15", "scratch16", 1) if s.count("scratch15") == 1 else R("scratch15", "scratch16", s.count("scratch15"))
R("if len(rows) != 59: F('rows != 59')", "if len(rows) != 60: F('rows != 60')")
R("range(1, 62)", "range(1, 63)")
R("E-01 to E-61 without", "E-01 to E-62 without")
R("list('abcdefghijklmnop')", "list('abcdefghijklmnopq')")
R("txt = open(E, encoding='utf-8').read()\n", "txt = open(E, encoding='utf-8').read()\ntry:\n    _ai = txt.index('\\n## Appendix K'); APPX_TEXT = txt[_ai: txt.index('\\n## ', _ai + 5)]\nexcept ValueError:\n    APPX_TEXT = ''\n")
R("t48 = pairs['E-48']['new'][0]", "t48 = pairs['E-48']['new'][0] + APPX_TEXT", 2)
R("t48n = newtxt['E-48']", "t48n = newtxt['E-48'] + APPX_TEXT")
R("'fewer than 20 minutes remain'", "'at least 20 minutes remain'")
R("'only after you have confirmed `no more takes`' not in rowtext('E-16')", "'You must have confirmed `no more takes`' not in rowtext('E-16')")
R("_alln.count('You choose the route by ONE message: write `route A` or `route B`') != 1", "_alln.count('Write `route A` or `route B` once, before your last take') != 1")
R("'Your `key revoked` then counts as `no more takes`', 'in route B the words `no more takes` count only after `cut accepted`', 'Cost of A:', 'Cost of B:', 'Benefit of B:'", "'Your `key revoked` then counts as `yes, no more takes`', 'Route B, before `cut accepted`', 'Route A:', 'a retake', 'the key and its copy'")
R("'`shred done`', '`shred not done`', 'ends the path to the copy'", "'`shred done 1`', '`shred not done 1`'")
R("if 'A new key lives only inside the program that uses it' not in part(t48n, '3g')", "if 'A new key lives only inside the program that uses it' not in APPX_TEXT")
R("if '(or after `key revoked` at the last time to revoke)' not in part(t48n, '3d')", "if 'a `key revoked` that counts under key step D.5' not in part(t48n, '3d') and 'after a `key revoked` that counts under key step D.5' not in t48n")
R("for need in ('`key revoked`', '`shred done`', 'home folder'", "for need in ('`key revoked`', '`shred done 1`', 'home folder'")
R("for need in ('your items 2 to 6', '`shred done`', 'counts as `no more takes`', '`cut accepted`')", "for need in ('items 2 to 6', '`shred done 1`', 'counts as the confirmation', '`cut accepted`')")
R("'4 minutes 40 seconds before the last time to revoke' not in t12n or 'a take that lasts 4 minutes longer' not in t12n", "'3 minutes 40 seconds before the last time to revoke' not in t12n or 'is still running at 18:19 UTC = 23:49 IST' not in t12n")
R("'Set two alarms' not in t12n", "'Set three alarms' not in t12n")
R("if '4 minutes 40 seconds' not in txt[txt.index('**latest start we plan**'):][:700]", "if '3 minutes 40 seconds' not in txt[txt.index('**latest start we plan**'):][:900]")
R("'`key revoked` is also only your own report'", "'`key gone, no more decisions`'")
R("'your own list of every file in which you saved a copy of the secret key for the model')", "'your own list of every file in which you saved a secret')")
R("'The latest start we plan is 18:00 UTC = 23:30 IST on any day', '18:14:20 UTC = 23:44:20 IST', '4 minutes 40 seconds before the last time to revoke'", "'The latest start we plan is 18:00 UTC = 23:30 IST on any day', '18:15:20 UTC = 23:45:20 IST', '3 minutes 40 seconds before the last time to revoke'")
R("if (_rev - _end).seconds != 280", "if (_rev - _end).seconds != 280")  # r15 arithmetic is replaced below
R("need('E-48 C', _C, 'In route B,", "need('E-48 C', _C + APPX_TEXT, 'In route B,")
R("'must be the key of app 2')", "'should be the key of app 2')")
R("'`shred done` means that EVERY file of (a), (b) and (c) is shredded'", "'`shred done 1` means that EVERY file of (a) and (b) is shredded'")
open(H + 'verify16.py', 'w', encoding='utf-8').write(s)
print('errors', errs)
