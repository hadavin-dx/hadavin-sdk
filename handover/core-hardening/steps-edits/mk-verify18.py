# builds verify18.py from verify17.py: re-anchors the old checks to the round 18 text (anchored patches, each asserted once)
s = open('verify17.py', encoding='utf-8').read().replace('scratch17', 'scratch18')
def R(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, n, a[:90])
    s = s.replace(a, b)
# route: no recommendation, "No default pick"
R("'Route B', 'the assistant recommends route B', ", "'Route B', 'No default pick', ")
R("if len(re.findall(r'recommends? route B', _alln)) != 1: F('r14 recommendation sentence count %d' % len(re.findall(r'recommends? route B', _alln)))",
  "if len(re.findall(r'recommends? route B|recommended\\)', _alln)) != 0 or _alln.count('No default pick') < 1: F('r18 route recommendation sentence count %d' % len(re.findall(r'recommends? route B', _alln)))")
R("neg('r13route', 'and the assistant recommends route B.', 'and the choice is open.', 'r13 E-48 lacks the assistant recommends route B')",
  "neg('r13route', 'No default pick: the assistant does not recommend a route', 'The assistant recommends route B', 'r13 E-48 lacks No default pick')")
R("neg('r14norec', 'and the assistant recommends route B.', 'and the choice is open.', 'r14 recommendation sentence count')",
  "neg('r14norec', 'No default pick: the assistant does not recommend a route', 'The assistant recommends route B', 'r18 route recommendation sentence count')")
# E-16 / E-55 now point to the one list in key step G.2
R("if 'Item 1 starts only when ALL of these are true' not in rowtext('E-16')", "if 'Item 1 starts only when ALL the conditions of key step G.2 are true' not in rowtext('E-16')")
R("neg('r13e16', 'Item 1 starts only when ALL of these are true', 'Item 1 starts when SOME of these are true', 'r13 E-16 trigger')",
  "neg('r13e16', 'Item 1 starts only when ALL the conditions of key step G.2 are true', 'Item 1 starts when SOME of the conditions of key step G.2 are true', 'r13 E-16 trigger')")
R("for need in ('`key revoked`', '`shred done key copies`', 'home folder', '`/mnt/c`', '`..`', 'link'):", "for need in ('card step 7', 'home folder', '`/mnt/c`', '`..`', 'link'):")
R("for need in ('your items 2, 3, 4 and 5', '`shred done key copies`', '`key gone, no more decisions`', '`cut accepted`'):", "for need in ('your items 2, 3, 4, 5 and 6', '`key gone, no more decisions`', '`cut accepted`'):")
R("neg('r14e55', 'your items 2, 3, 4 and 5 done', 'your items done', 'r14 E-55 lacks', 9)", "neg('r14e55', 'each of your items 2, 3, 4, 5 and 6', 'each of your items', 'r14 E-55 lacks', 9)")
R("if 'The spots that carry the recommendation' not in txt: F('r14 ND15 spots')", "if 'The spot that would carry a recommendation' not in txt: F('r14 ND15 spots')")
R("neg('r14nd15', 'The spots that carry the recommendation, so that all change together', 'Other spots', 'r14 ND15 spots')", "neg('r14nd15', 'The spot that would carry a recommendation, if the studio lead adds one', 'Other spots', 'r14 ND15 spots')")
R("'if no session is open, go straight to key step I'", "'if no session is open or it does not ask, go straight to key step I'", 2)
R("'you have written none of these, the assistant does not start item 1'", "'you have not written ALL of these, the assistant does not start item 1 in that session'")
R("neg('r12key2', 'the one that you open at `http://localhost:5678`? If it is, revoking it breaks that n8n.\" Reply `same key`', 'the one in your n8n? If it is, revoking it breaks that n8n.\" Reply `same key`', 'r12 E-48 lacks http://localhost:5678')", "neg('r12key2', 'the one that you open at `http://localhost:5678`? If it is, revoking it breaks that n8n.\" Reply `same key`', 'the one in your n8n? If it is, revoking it breaks that n8n.\" Reply `same key`', 'r17 r12 key step F question lacks')")
R("need17('F-5 E', ks('E'),", "need17('r12 key step F question', ks('F'), 'the one that you open at `http://localhost:5678`? If it is, revoking it breaks that n8n.\" Reply `same key`')\nneed17('F-5 E', ks('E'),")
# the typed-word table is part of key step B for these checks
R("""    return '\\n'.join(ls_[st[0]:(en[0] if en else len(ls_))])
def need(""", """    _o = '\\n'.join(ls_[st[0]:(en[0] if en else len(ls_))])
    if letter == 'B':
        _ti = t48.find('Table of the typed words'); _o += ('\\n' + t48[_ti:t48.index('The assistant never opens the key file', _ti)]) if _ti >= 0 else ''
    return _o
def need(""")
# the numbered order (the card) in its new sequence
R("""for _k in ('1. You: revoke the secret key', '2. You: shred the copy of the key in the take folder', '3. You: do your items 2, 3 and 4', '4. You: do your item 5', '5. You: do your item 6', '6. You: read the list of what the assistant will remove', '7. Then the assistant does its item 1'):""",
  """for _k in ('1. You: make sure that you have confirmed', '2. You: do your items 2 and 3', '3. You: shred the copy of the key in the take folder', '4. You: do your item 4', '5. You: do your item 6', '6. You: read the list of what the assistant will remove', '7. Then the assistant does its item 1'):""")
R("neg('r16F4a', '4. You: do your item 5, the retire check.', '0. You: do your item 5, the retire check.', 'r16 F4 the numbered order')",
  "neg('r16F4a', '4. You: do your item 4 (save the screenshots) and your item 5, the retire check.', '0. You: do your item 4 (save the screenshots) and your item 5, the retire check.', 'r16 F4 the numbered order')")
# r17 F-1: one order in ONE place (the card); E-16 and E-55 point to it; one start sentence in G.2
R("""_P17 = ['revoke the secret key for the model (key step I) and write `key revoked`',
        'shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`',
        'do your items 2, 3 and 4 (item 2: revoke both app passwords; item 3: delete both HubSpot apps; item 4: save the screenshots)',
        'do your item 5, the retire check',""",
  """_P17 = ['make sure that you have confirmed your last take with `yes, no more takes` (key step D.3), then revoke the secret key for the model (key step I) and write `key revoked`',
        'do your items 2 and 3, the quick web revokes, each only after the identification check of step 22 item 3',
        'shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`',
        'do your item 4 (save the screenshots) and your item 5, the retire check',""")
R("""for _lab, _tx in (('card', _card17), ('E-16', newtxt['E-16']), ('E-55', newtxt['E-55'])):
    _ps = [_tx.find(p_) for p_ in _P17]""", """for _lab, _tx in (('card', _card17),):
    _ps = [_tx.find(p_) for p_ in _P17]""")
R("""for _lab, _tx in (('G.2', _G17), ('E-16', newtxt['E-16']), ('E-55', newtxt['E-55'])):
    need17('F-1 start sentence in ' + _lab, _tx, _START17)""", """need17('F-1 start sentence in G.2', _G17, _START17)
for _lab in ('E-16', 'E-55'):
    need17('F-1 pointer in ' + _lab, newtxt[_lab], 'Item 1 starts only when ALL the conditions of key step G.2 are true (the list is there, once)', 'the seven steps printed there')
    absent17('F-1 no copy of the list in ' + _lab, newtxt[_lab], 'Item 1 starts only when ALL of these are true', '`shred done other files` (or')""")
R("'items 2 and 3', 'items 2 to 5',", "'items 2 to 5',")
R("'card step 2 (shred the copies of the key)'", "'then card step 2 (the app passwords and the HubSpot apps', 'only then card step 3 (the shred of the key copies'")
R("'r. Round 17 additions of the builder, to confirm:'", "'r. Round 17 and round 18 additions of the builder, to confirm:'", 1)
R("""'`key revoked`, `key not revoked`, `key gone, no more decisions`, `shred done key copies`'),""", """'| `key gone, no more decisions` | the key is gone AND there are no more takes AND the cut is final'),""")
R("""'`ok flow rehearsal`, `please stop looking`, `you may look again`'),""", """'| `please stop looking` | you are about to type a secret: the assistant stops looking and answers `not looking`'),""")
R("""'on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest'),""", """'if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway'),""")
R("""'the 10 minutes between are only for the shred of the key copies'),""", """'the 10 minutes between go first to the key (card step 1)'),""")
R("""'m34 word list': ('`key revoked`, `key not revoked`, `key gone, no more decisions`, `shred done key copies`', '`key revoked`, `key not revoked`, `shred done key copies`'),""",
  """'m34 word list': ('the key is gone AND there are no more takes AND the cut is final', 'the key is gone AND there are no more takes'),""")
R("""'m43 stop looking': ('`ok flow rehearsal`, `please stop looking`, `you may look again`', '`ok flow rehearsal`, `you may look again`'),""",
  """'m43 stop looking': ('the assistant stops looking and answers `not looking`', 'the assistant keeps looking'),""")
R("""'m60 card 1': ('on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest', 'on Mon 23 Nov 2026 it is at 18:29 UTC = 23:59 IST at the latest'),""",
  """'m60 card 1': ('if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway', 'if you have not typed `yes, no more takes` by 18:29 UTC = 23:59 IST, revoke the key at that time anyway'),""")
R("""'B04 ten minutes': ('the 10 minutes between are only for the shred', 'the 20 minutes between are only for the shred'),""",
  """'B04 ten minutes': ('the 10 minutes between go first to the key (card step 1)', 'the 20 minutes between go first to the key (card step 1)'),""")
R("need('E-16', newtxt['E-16'], 'Only messages that you type yourself count', '`start clean-up`', '`yes, no more takes`')", "need('E-16', newtxt['E-16'], 'Only messages that you type yourself count', 'each as a message that you typed yourself', 'card step 7')")
R("need('E-55', newtxt['E-55'], '`yes, no more takes`', '`start clean-up`')", "need('E-55', newtxt['E-55'], '`yes, no more takes`', 'the card of item 3 (the seven steps printed there)')")
sec = open('r18-section.py', encoding='utf-8').read()
R("# ================= negative controls (each check must fail on a planted defect) =================", sec + "# ================= negative controls (each check must fail on a planted defect) =================")
pl = open('r18-plants.py', encoding='utf-8').read()
R("print('FAILURES', fail)", pl + "print('FAILURES', fail)")
open('verify18.py', 'w', encoding='utf-8').write(s)
print('verify18.py written', len(s.split('\n')), 'lines')
