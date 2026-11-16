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
R("""R("""[:0]+"", "") if False else None
