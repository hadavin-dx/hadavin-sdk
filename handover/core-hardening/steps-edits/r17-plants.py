    # ---- round 17 negative controls (each must fail the new check; the first 22 are the runner's pins m18..m60 and B03..B10)
    _pl = {'m18 D.4 appendix ref': ('appendix K-D', 'appendix K-E'), 'm34 word list': ('`key revoked`, `key not revoked`, `key gone, no more decisions`, `shred done key copies`', '`key revoked`, `key not revoked`, `shred done key copies`'),
           'm37 window end': ('The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST', 'The spending window ends 10 minutes later, at 18:19 UTC = 23:49 IST'),
           'm40 not sure': ('Reply `yes`, `no, other things use it` or `not sure`', 'Reply `yes` or `no, other things use it`'),
           'm41 only yes': ('Only `yes` together with `different key` means', 'Only `yes` means'),
           'm43 stop looking': ('`ok flow rehearsal`, `please stop looking`, `you may look again`', '`ok flow rehearsal`, `you may look again`'),
           'm45 C': ('unless at least 30 minutes remain after you have answered', 'unless at least 2 minutes remain after you have answered'),
           'm45 H': ('only if at least 30 minutes remain before', 'only if at least 20 minutes remain before'),
           'm48 G': ('Do not shred part (a) while a take is running (the model stage reads that copy); wait until the take has stopped. ', ''),
           'm51 why': ('Security F2 of round 15: input line 112', 'Security F2'),
           'm53 unverified': ('is not proven (UNVERIFIED)', 'is proven'),
           'm54 typed': ('Only your own typed messages count (key step B)', 'Messages count (key step B)'),
           'm60 card 1': ('on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest', 'on Mon 23 Nov 2026 it is at 18:29 UTC = 23:59 IST at the latest'),
           'B03 no space': ('no `..`, no space, no quote sign', 'no `..`, no quote sign'),
           'B04 ten minutes': ('the 10 minutes between are only for the shred', 'the 20 minutes between are only for the shred'),
           'B05 step 21 heading': ('### Step 21. Watch the cut by Mon 23 Nov 2026 18:19 UTC = 23:49 IST', '### Step 21. Watch the cut by Mon 23 Nov 2026 18:21 UTC = 23:51 IST'),
           'B08 never opens': ('The assistant never opens the key file (this is a procedure, not enforced by a program).', ''),
           'B09 default': ('no reply counts as `another take`', 'no reply counts as `no more takes`'),
           'B10 forced revoke': ('tell the assistant at once and revoke the key at that time anyway (key step I)', 'tell the assistant at once and wait for the take'),
           'r17 key gone one word': ('so after it you do not type `key revoked` again', 'so after it you type `key revoked` again'),
           'r17 D.5 key gone': ('and then write `key gone, no more decisions`: that one message', 'and then write `key revoked`: that one message')}
    for _k, (_o, _n) in _pl.items():
        neg('r17pin-' + _k.split()[0] + _k.split()[1][:3], _o, _n, 'r17 ', 9)
    neg('r17order-card', '4. You: do your item 5, the retire check.\n', '', 'r17 F-1 the seven steps')
    neg('r17order-e16', '(4) do your item 5, the retire check; ', '', 'r17 F-1 the seven steps', 9)
    neg('r17start-e55', 'you have read the list of what the assistant will remove; and `start clean-up`.', 'you have read the list; and `start clean-up`.', 'r17 F-1 start sentence')
    neg('r17oldwords', '`shred done other files` (or', '`shred done 2` (or', 'r17 F-8 old words')
    neg('r17more', 'or reply `another take`."', 'or reply `more takes`."', 'r17 F-8 old words')
    neg('r17abs', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take (see /ho' + 'me/user/x/notes).', 'r17 absolute path')
    neg('r17ord-code', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take. ORD: 5.', 'r17 internal code')
    neg('r17dec-code', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take. DEC: 5.', 'r17 internal code')
    neg('r17row-e48', 'The owner reads key steps A to K in step 22 item 3 of his sheet.', 'The owner reads key steps A to K in row E-48.', 'r17 internal code')
    neg('r17n1', 'I accept that until I revoke the secret key for the model it can spend', 'I accept that it can spend', 'r17 N1 ND16')
    neg('r17alarm3', 'if a take is running, let it finish (key step K), then revoke the key at once', 'stop everything else and do key step I now', 'r17 F-3 C')
    neg('r17routeb', 'Route A is the safer one for keeping secrets safe;', 'Route B is fine;', 'r17 F-2 route B price')
    neg('r17appx', 'This appendix is the last page of the same sheet', 'This appendix is a separate file', 'r17 F-2 appendix landing')
    neg('r17thirty', 'Make no new key now unless at least 30 minutes remain', 'Make no new key now unless at least 20 minutes remain', 'r17 F-4')
    neg('r17last', 'by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'by Mon 23 Nov 2026 18:20 UTC = 23:50 IST at the latest (the last time to revoke)', 'r17 last time to revoke is wrong')
