# evidence-f8-r7 (raw)
## 1
Mon Nov 16 13:26:40 UTC 2026
e32408c3c
8c87bbac42fc57bd  take_check.sh
6c6f13f39eee2130  test_take_check.sh
## 2
bash -n take_check.sh exit=0
bash -n test_take_check.sh exit=0
## 3
exit=0
0
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 311 of 311 cases as expected, 0 not as expected
## 4
Words refused in the name and in the note: claude claudebot anthropic opus sonnet haiku fable gpt gpts chatgpt gptbot chatbot openai codex gemini copilot llama mistral grok qwen kimi devin cursor deepseek agent agents assistant assistants bot bots robot robots ai aibot llm llms tbd todo none unknown placeholder session sessions
Words refused in the name only: name nobody someone anonymous model models person xxx abc standin stand test reviewer runall dummy example sample fake code user admin lead testonly
exit=0

## 3 note: scratch patched folder built from run_all.sh steps (git apply F-002 then F-008, build_mainframe.py real); test output: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r7/t3.txt; FAIL lines: 0

diff exit=0
## 5
--- INPUT: Pat,Claude Bot, 2026-11-16
REFUSED (rule: shape): the line must read NAME, YYYY-MM-DD or NAME, YYYY-MM-DD, a note: exactly one comma and one space between the name and the date, no comma inside the name and no text between the name and the date (write 'Jane Roe', not 'Roe, Jane'; write 'John Smith Jr.' with no comma)
exit=1
--- INPUT: Pat Smith, 2026-11-16, not yet read
REFUSED (rule: note says not read): the note says the lines were not read (or will be read later)
exit=1
--- INPUT: Cl4ude Smith, 2026-11-16
REFUSED (rule: name characters): the name may hold only letters, spaces, dots, apostrophes and hyphens (no digits or other signs)
exit=1
--- INPUT: José Müller, 2026-11-16
ok
exit=0
--- INPUT: Claude Monet, 2026-11-16
REFUSED (rule: listed word claude): the name contains the whole word 'claude', which is on the list of refused words
exit=1
--- INPUT: Pat Smith, 2026-11-16
ok
exit=0
--- INPUT: Pat Smith, 2099-01-01
REFUSED (rule: future date): 2099-01-01 is more than one day ahead of today (UTC)
exit=1
--- INPUT: Pat[31m Smith, 2026-11-16
REFUSED (rule: hidden character): the line holds a control or invisible character (U+001B)
exit=1
--- INPUT: Pat Smith,2026-11-16
REFUSED (rule: shape): the line must read NAME, YYYY-MM-DD or NAME, YYYY-MM-DD, a note: exactly one comma and one space between the name and the date, no comma inside the name and no text between the name and the date (write 'Jane Roe', not 'Roe, Jane'; write 'John Smith Jr.' with no comma)
exit=1

## 6
--- python3 -I tools/check_secrets.py
PASS 0 hits in 1840 files
exit=0
--- python3 tools/check_refs.py
PASS 5168 references
exit=0
--- ruff check .
All checks passed!
exit=0
--- ruff format --check .
556 files already formatted
exit=0

## run_all.sh (no network per its header; writes raw/ and selftest-output)
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
run_all exit=0

## 7 git status after restore
 M handover/flows-audit/flow-check/evidence-f8-r7.md
A  handover/flows-audit/flow-check/review-f8-r7-findings.md
