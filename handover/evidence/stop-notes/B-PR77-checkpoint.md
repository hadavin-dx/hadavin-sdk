# B-PR77 checkpoint (write 2)
done: F1-F4 fixed in guard/runmap.py (is_hidden, canonical, _refuse_forgery, UTS46 dots view, _view_covers); perf tweak in redact._tolerate; F5/F6 reverted (moved to ticket Q8b); tests/test_redact_hidden_forms.py (196 pass); new killers marks_30..33; mutants file re-pointed (+H1-H8, -W3 W5 W39 equivalent); CHANGELOG rewritten (COST_ placeholders pending).
next: mutant run result (/tmp/claude-0/pr77/mut2.log), cost numbers, full suite once, ruff/bandit, gitleaks, commit, push.
blockers: none. uncommitted.
# final: head 97fd2028; full suite 2 guard failures fixed after (runner revert), not re-run in full
