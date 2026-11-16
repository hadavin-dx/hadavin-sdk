#!/bin/bash
# The take check: runs the checker on the real-v5 flows only and prints what a person must read FIRST (top block), then the full checker output.
# Usage: bash take_check.sh   (from any folder).
# Exit status of this script (decided 2026-11-16, round 6):
#   0 = the checker found no definite fault AND the table file was found AND at least one SQL query was compared AND no column or table is missing. It is NOT "ready to film": see the last line.
#   1 = the checker found at least one FAIL (a definite fault in a file).
#   2 = the checker was started wrongly (bad command line, for example the table file cannot be read).
#   3 = the checker itself broke.
#   5 = (round 10d) the run WOULD have been exit 0, but an environment override is active (only allowed with the test flag TAKE_CHECK_TEST=1): it is a test run, never a take check. A take check that passes is exit 0 only with NO override.
#   4 = the checker found no FAIL, but a check this take depends on did not happen or found a mismatch: the table file demo/n8n-flows-v4/mf_leads.sql is missing, OR 0 query strings were read, OR a query uses a column or table that file does not define, OR a postgres step has no query text (its columns were not compared), OR a flow other than the recovery flow still has run saving off (the take shows the run list, so run saving must be ON: that is the case on the committed real-v5 folder until patch F-008 is applied; the take runs on the patched copy, decision Q17-4/Q18), OR the recorded accept for the recovery flow excused nothing.
# The recovery flow (exact file name mf-recovery.json, nothing else) keeps run saving off on purpose: it fires every 30 s and the one video makes no recovery claim (decision 4). It is printed as an ACCEPTED line, not a WARN. No blanket accept exists in this script.
# film-v5 is NOT FOR THE TAKE and is not checked here.
# The table definition the take needs is demo/n8n-flows-v4/mf_leads.sql (lead decision, order Q16). It is looked up at that exact path only (no search for a file of the same name elsewhere).
# Round 9 (review f8-design-r3, 4 Majors): (M1) the top block and the FINAL line print RESULT and the WARN count; the set of WARN lines is pinned in take-warns.pin (folder paths removed) and ANY change is exit 4; (M2) every flow except mf-recovery.json must have run saving exactly all / all / True (a missing settings block, a missing key or an odd word is exit 4, not only "none"/false); (M3) a key check that is ABSENT is exit 4, and when both entry flows have it the checker's F-002 content check (--patch-checks F002) runs on them; (M4) the patched copy is detected by the KeyOk node: the node:connection count 15:14 is then expected without any environment variable (12:11 for an unpatched file).
# Round 10 (review f8-r10): (B1) --write-warn-pin refuses a file that exists (so it can never overwrite the pin in use), writes only when the run has no FAIL and a RESULT line, writes AFTER the comparison, prints the difference and exits 4 when it wrote the file (a run that writes a pin is never a pass; refused = 2, checker FAIL = 1, checker broke = 3, other problems = 4 and nothing written); a person installs the pin by hand (see README). (M1) the top block and the FINAL line print an OVERRIDES line; an environment override (TAKE_CHECK_CK, TAKE_CHECK_WARN_PIN, TAKE_CHECK_FLOWS, TAKE_CHECK_DDL, TAKE_CHECK_FORM_EXPECT) is exit 4 unless the test flag TAKE_CHECK_TEST=1 is set (only selftest and run_all.sh set it); the documented way to check another folder is the option --flows DIR, which is printed. (M3/M5) the checker FAILs a listed flow that is not a regular file; the F-002 content check also asserts the reply steps and lead_key. F-008 content check (--patch-checks F008) is NOT used here: it would turn the planted run-saving cases (exit 4 by design) into exit 1; the exact run-saving check below judges F-008 instead. (M4) the pin header carries a date and the sha256 of the WARN lines; a pin that does not match its own hash is exit 4; the pinned WARN count is printed and said to stand for known defects. (N1-N4) LC_ALL=C sort, helper exit statuses checked, closing-block lines must appear once, absolute paths before the cd, one temp folder removed on exit.
# Round 10b (review f8-r10 round 2): the top block and the FINAL line print a sha256 of the four flow files; the pin header needs a "# reviewed by: NAME, DATE" line without the word PLACEHOLDER (exit 4 otherwise); --write-warn-pin writes only when the only problem is the WARN difference; the run-saving INFO line no longer promises a deletion (the take never deletes anything).
# Round 10c (review f8-r10b round 2): (Q1) the output never says a person read the pin: it prints the reviewer line (round f8-r8: without hidden characters, cut at 300), and a reviewer line that names a session or says "lead to confirm" is exit 4 ("pin not yet confirmed by the lead"), so the first exit 0 needs the lead's own line; (Q2) the flow files (the four and every other *.json in the folder) are hashed before the checker and again after the last read, a difference is exit 4, an unreadable file prints MISSING; (Q5) a checker exit status above 3 is shown and returned as 3.
# Round 10d (review f8-r10c): (A1) the pin comment no longer claims a person read each line (only the WARN lines are hashed; comment lines are not protected); (B1) the pin header carries '# flows sha256 ...' (the combined sha256 of the four flow files, as printed in the top block); a different sha is exit 4, a pin without that line is exit 4, so a changed flow with the same counts and WARNs no longer passes; (B2) the reviewer line must be 'NAME, YYYY-MM-DD' (optionally ', note'), a real date not in the future, and a name that is not a stand-in (TBD, x, claude agent, ...); (B3) with the test flag and an override a run that would pass is exit 5 (not 0), TAKE_CHECK_FLOWS together with --flows is exit 2, and the top block says where the folder name came from; (B4 is in run_all.sh); the flow_snapshot (sha256 of the flow files) is taken before any other read of them; a sha256sum failure is a problem (exit 4), never an empty hash.
# Round f8-r7 (reviews f8-r6, codebase and design angle): the reviewer-line check is now ONE rule set run by a small python helper (REVIEWER_PY below): the line must read NAME, YYYY-MM-DD[, note] with exactly one comma and one space before the date (a comma inside the name or text between the name and the date is refused); the date is real, not more than one day ahead of today (UTC) and not older than the pin's own date line; the name has at least 3 letters (any alphabet; digits and signs other than space, dot, apostrophe and hyphen are refused); a whole word of the name or the note on the list REVIEWER_WORDS_ALL (tool and model names, bot and agent words, tbd/todo/none/unknown/placeholder/session) is refused; a whole word of the name on REVIEWER_WORDS_NAME (generic stand-ins) is refused; letters of two alphabets mixed in one word (look-alike letters) are refused; a note that says the lines were not read, or will be read later, is refused. Digits are read as the letters they imitate (4 as a, 3 as e, 1 as i or l, 0 as o, 5 as s, 7 as t) and single letters joined by dots (L.L.M.) are one word. There is no search inside longer words and no joining of words: Claudette, Robotham, Bo Ta and A. I. Walker pass. The words live ONLY in this file (bash take_check.sh --reviewer-words prints them; the tests and the README are compared with that output).
# Round f8-r8 (review f8-r7, fixes per class): (M1) the reviewer-line check reads no variable of its own: "today" is an argument that only --check-reviewer-line passes (and only with the test flag); (M2/M3) ONE normalisation: hidden characters (category C, Zl, Zp, Default_Ignorable_Code_Point, combining marks not on a letter) are refused by the check and removed by safe_text with the same function; every name word needs 2 letters (an initial needs its dot); each piece between spaces is read split at non-letters AND squeezed (Cl-aude, Bo.t, Cl@ude); (M4) a look-alike table (Cyrillic, Greek, ł đ ɑ and others) is applied before matching; (M5/M6) longer lists (placeholders, roles, more bots and tools, two-word stand-ins) and s/es endings of listed bot and tool words; (m1) the digit 1 is tried as i and as l (up to 8 ones); (m2) session is a whole word like the others; (m3) more 'not read' phrases; (m4) the printed line is cut at 300 characters and says its length; (n1) dead line removed. The line goes to the helper through its input (no size limit of a command line) and is refused above 1000 characters.
# Round f8-r9 (review f8-r8): (M1) the reviewer line must carry a receipt ', pin sha256 XXXXXXXX' (first 8 hex of the WARN-lines hash), so it names one pin version; the pin writer prints it; a script cannot prove WHO read the pin (open: signed commit, Q31); (M2) any word mixing two scripts is refused, modifier letters (Lm) and look-alike letters (Armenian, Cherokee, U+0138) are folded or refused; (M3) listed-word refusals say how to write the name (initial + surname); jenkins/devin/sessions are weak words (refused only beside a role word), ai/llm only negatable or as a lone first word, two-letter CJK names and the particle y are accepted; (M4) TEST_TAKE_SCRIPT is honoured only with TEST_TAKE_DEV=1 (in the test file); the flow folder is copied once and the copy is read; hazards (BASH_ENV, LD_PRELOAD, imported functions) are named; a helper fault and a bad pin date have their own messages.
# Usage: bash take_check.sh [--flows DIR] [--write-warn-pin NEWFILE]   (NEWFILE must not exist yet; the pin in use is take-warns.pin next to this script). Helpers that run nothing else: --reviewer-words (prints the word lists), --check-reviewer-line 'LINE' [PINDATE [RECEIPT]] (prints ok or the rule that refused, exit 0 or 1, 3 when the helper itself broke; without RECEIPT no receipt is asked), --standin-name (the stand-in name run_all.sh uses) and --safe-text 'TEXT' (prints TEXT without hidden characters, cut at 300).
LC_ALL=C; export LC_ALL
# round f8-r9 (nit): ${X^} below needs bash 4; say so instead of failing with "bad substitution"
if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ]; then echo "REFUSED: this script needs bash 4 or newer (found bash ${BASH_VERSION:-unknown}); it uses the \${X^} form"; exit 2; fi
# round f8-r9 (m8): what a shell inherits from the caller and can change what this script runs. Read FIRST, before this script defines a function of its own: a function that python3, sha256sum or another command used below has been given by the caller (export -f) shows up in this list; so do the variables that make bash, the loader or python read other code.
ENVHAZ=""
for v in BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT PYTHONHOME PYTHONPATH PYTHONSTARTUP; do [ -n "${!v:-}" ] && ENVHAZ="$ENVHAZ variable $v;"; done
IMPORTED_FUNCS=$(declare -F 2>/dev/null | sed -e 's/^declare -[a-zA-Z-]* //' | tr '\n' ' ')
[ -n "${IMPORTED_FUNCS// /}" ] && ENVHAZ="$ENVHAZ shell function(s) from the caller: ${IMPORTED_FUNCS% };"
HERE=$(cd "$(dirname "$0")" && pwd)
# THE ONE PLACE THAT HOLDS THE REVIEWER WORD LISTS (round f8-r8). run_all.sh, the tests and the README ask this file (--reviewer-words, --standin-name, --check-reviewer-line, --safe-text); none keeps a copy.
REVIEWER_TESTONLY="testonly"      # the script's own test name: accepted only with the test flag AND a pin override (such a run is exit 5, never 0)
REVIEWER_STANDIN_SECOND="runall"  # second word of the stand-in name run_all.sh uses (printed by --standin-name)
REVIEWER_STANDIN_NAME="${REVIEWER_TESTONLY^} ${REVIEWER_STANDIN_SECOND^}"
# round f8-r9: ai llm llms ais moved to REVIEWER_WORDS_NEG; none todo unknown moved to the name-only list (honest notes such as "none missing" or "to-do list checked" must pass); jenkins devin sessions are in REVIEWER_WORDS_WEAK
REVIEWER_WORDS_ALL="claude claudebot anthropic opus sonnet haiku fable gpt gpts chatgpt gptbot chatbot openai codex gemini copilot llama mistral grok qwen kimi cursor deepseek agent agents assistant assistants bot bots robot robots aibot dependabot renovate github bard perplexity siri alexa cortana jarvis windsurf aider manus bing tbd placeholder session"
REVIEWER_WORDS_NAME="name nobody someone anonymous model models person xxx abc standin stand test reviewer $REVIEWER_STANDIN_SECOND dummy example sample fake code user admin lead $REVIEWER_TESTONLY firstname lastname lorem ipsum asdf qwerty xxxx noone tba tbc pending unspecified owner approver operator maintainer author team system service support root none todo unknown audit"
REVIEWER_PHRASES_NAME="john_doe jane_doe foo_bar joe_bloggs"
REVIEWER_WORDS_WEAK="jenkins devin sessions"
REVIEWER_WORDS_NEG="ai ais llm llms"
REVIEWER_NEGATORS="no not without never zero"
REVIEWER_PARTICLES="y e i o a"
REVIEWER_NOTREAD='\bpending\b|\bnot\s+(?:yet\s+|fully\s+|all\s+|really\s+|been\s+)*(?:read|reviewed|checked|looked|opened|seen|verified)\b|\bunread\b|\bunreviewed\b|\bunchecked\b|\bwill\s+(?:read|review|check)\b|\b(?:read|review|reviewed|check|checked|look|looked)\s+(?:it\s+|them\s+|these\s+|this\s+)?(?:again\s+)?later\b|^later$|\bto\s+be\s+(?:read|reviewed|checked)\b|\b(?:did|do|does|have|has|had)n'"'"'?t\s+(?:yet\s+|fully\s+|really\s+)?(?:read|review|reviewed|check|checked|look|looked|open|opened)\b|\bskimmed\s+only\b|\bonly\s+skimmed\b|\bjust\s+skimmed\b|\bwithout\s+(?:reading|reviewing|checking|looking)\b|\bno\s+time\s+to\s+(?:read|review|check)\b|\bsigning\s+only\b'
# The note may use the name-only words in normal speech (a sample, the code, the lead), so they are checked in the name only.
# Shared python code (also used by safe_text): which characters are never allowed. Refused: every control, format, unassigned, private-use and surrogate character (category C), line and paragraph separators (Zl, Zp), every Default_Ignorable_Code_Point (the Unicode list is written out below because python has no property for it), and every combining mark (Mn, Mc, Me) that does not sit on a letter. Round f8-r9 (m7): U+200C and U+200D (the zero width non-joiner and joiner that Persian, Indic and other scripts use inside real names) are accepted when they sit between two letters of a script that has no look-alike letters in Latin (so they cannot hide a Latin word); they are removed from what is shown.
IFS= read -r -d '' REVIEWER_NORM_PY <<'PYEOF' || true
import re
import sys
import unicodedata

DICP = (
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x17B4, 0x17B5),
    (0x180B, 0x180F), (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164),
    (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)
LOOKALIKE_SCRIPTS = {"LATIN", "CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE", "COPTIC", "MODIFIER"}


def script_of(ch):
    """The script of a letter: the first word of its Unicode name (LATIN, CYRILLIC, ARMENIAN, ...). Han, Hiragana, Katakana, Bopomofo and Hangul are ONE family (CJK): Japanese and Korean names mix them. A modifier letter is MODIFIER."""
    nm = unicodedata.name(ch, "?")
    w = nm.split()[0] if nm != "?" else "?"
    if w in ("CJK", "HIRAGANA", "KATAKANA", "BOPOMOFO", "HANGUL", "IDEOGRAPHIC") or w.startswith("KATAKANA") or w.startswith("HIRAGANA"):
        return "CJK"
    return w


def never_allowed(ch):
    cat = unicodedata.category(ch)
    o = ord(ch)
    return cat[0] == "C" or cat in ("Zl", "Zp") or any(a <= o <= b for a, b in DICP)


def scan(t):
    """The ONE normalisation of hidden characters: returns (t without refused characters, first refused character or None)."""
    out = []
    bad = None
    attached = False
    for i, ch in enumerate(t):
        cat = unicodedata.category(ch)
        is_mark = cat in ("Mn", "Mc", "Me")
        if ord(ch) in (0x200C, 0x200D):
            prev = out[-1] if out else ""
            nxt = t[i + 1] if i + 1 < len(t) else ""
            if prev and nxt and unicodedata.category(prev)[0] == "L" and unicodedata.category(nxt)[0] == "L" and script_of(prev) not in LOOKALIKE_SCRIPTS and script_of(nxt) not in LOOKALIKE_SCRIPTS:
                continue   # a joiner inside a word of a script without Latin look-alikes: accepted, not shown
        if never_allowed(ch) or (is_mark and not attached):
            if bad is None:
                bad = ch
            attached = False
            continue
        out.append(ch)
        if not is_mark:
            attached = cat[0] == "L"
    return "".join(out), bad


def read_stdin():
    return sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
PYEOF
IFS= read -r -d '' REVIEWER_PY <<'PYEOF' || true
try:
    pindate, testallow, words_all, words_name, phrases_name, today_s, testword, receipt, words_weak, words_neg, negators, particles, notread = sys.argv[1:14]
except ValueError:
    print("HELPER ERROR: wrong number of arguments")
    sys.exit(3)
ALL = set(words_all.split())
NAME = set(words_name.split())
WEAK = set(words_weak.split())
NEG = set(words_neg.split())
NEGATORS = set(negators.split())
PARTICLES = set(particles.split())
PHRASES = [tuple(p.split("_")) for p in phrases_name.split()]
STEMS = {w for w in ALL if len(w) >= 4}   # s / es endings are read as the listed word (Claudes, Opuses); words under 4 letters have their plural on the list themselves
LETTER = r"[^\W\d_]"
MAXLEN = 1000
APOSTROPHES = {0x2019: "'", 0x2018: "'", 0x02BC: "'", 0x02BB: "'", 0x02BD: "'", 0x02B9: "'"}   # curly and modifier apostrophes are read as the plain apostrophe (a real name such as O’Neil or Kamaʻaina must not be refused for its typography; Claʼude is then read as Cla'ude)

# look-alike letters (Cyrillic, Greek, Armenian, Cherokee and Latin letters that do not break down into a plain letter) read as the plain Latin letter, lower case
CONF = {
    "а": "a", "в": "b", "с": "c", "е": "e", "н": "h", "і": "i", "ј": "j", "к": "k",
    "м": "m", "о": "o", "р": "p", "ѕ": "s", "т": "t", "у": "y", "х": "x", "ԁ": "d",
    "ԛ": "q", "ԝ": "w", "ѵ": "v", "ӏ": "l",
    "α": "a", "β": "b", "γ": "y", "ε": "e", "η": "n", "ι": "i", "κ": "k", "μ": "u",
    "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x", "ω": "w", "ϲ": "c", "ϳ": "j",
    "ł": "l", "đ": "d", "ɑ": "a", "ø": "o", "ð": "d", "ħ": "h", "ı": "i", "ȷ": "j",
    "ɡ": "g", "ƒ": "f", "ɩ": "i", "ɪ": "i", "ʟ": "l", "ɴ": "n", "ʀ": "r", "ᴀ": "a",
    "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ɢ": "g", "ʜ": "h", "ᴊ": "j", "ᴋ": "k",
    "ᴍ": "m", "ᴏ": "o", "ᴘ": "p", "ᴛ": "t", "ᴜ": "u", "ᴠ": "v", "ᴡ": "w", "ʏ": "y",
    "ᴢ": "z", "ɦ": "h", "ɱ": "m", "ƙ": "k", "ƚ": "l", "ɫ": "l", "ʈ": "t", "ƭ": "t",
    "ŧ": "t", "ɨ": "i", "ʉ": "u", "ɍ": "r", "ɇ": "e", "ꜱ": "s", "ƶ": "z", "ᵽ": "p",
    "ƀ": "b", "ɓ": "b", "ɗ": "d", "ƈ": "c", "ɠ": "g", "ƴ": "y", "ʋ": "v",
    "ĸ": "k", "æ": "ae", "œ": "oe", "ß": "ss",
    # Armenian look-alikes (f8-r9: U+057D and others)
    "ս": "u", "օ": "o", "ո": "n", "ց": "g", "հ": "h", "ք": "q",
}
# Cherokee capital letters that look like Latin capitals (written as their lower case forms, which is what fold() produces)
for _k, _v in {0x13AA: "a", 0x13F4: "b", 0x13DF: "c", 0x13A0: "d", 0x13AC: "e", 0x13C0: "g", 0x13BB: "h", 0x13A5: "i", 0x13AB: "j", 0x13E6: "k", 0x13DE: "l", 0x13B7: "m", 0x13E2: "p", 0x13DA: "s", 0x13A2: "t", 0x13D9: "v", 0x13B3: "w", 0x13C3: "z", 0x13A1: "r"}.items():
    CONF[chr(_k).lower()] = _v
_LAT = re.compile(r"LATIN (?:SMALL|CAPITAL) LETTER ([A-Z])(?: WITH [A-Z ]+)?$")
_LATSC = re.compile(r"LATIN LETTER SMALL CAPITAL ([A-Z])$")
LEET = str.maketrans({"4": "a", "3": "e", "0": "o", "5": "s", "7": "t", "8": "b", "9": "g", "6": "g"})
AT = str.maketrans({"@": "a", "$": "s", "!": "i"})


def refuse(rule, text):
    print("REFUSED (rule: %s): %s" % (rule, text))
    sys.exit(1)


def fold(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if unicodedata.category(c)[0] != "M").lower()


def lat_base(c):
    """A Latin letter that does not break down by NFKD (k with a hook, small capitals, ...) read by its Unicode name as the plain letter: the class, not a hand-made list."""
    m = _LAT.match(unicodedata.name(c, "")) or _LATSC.match(unicodedata.name(c, ""))
    return m.group(1).lower() if m else None


def skel(t):
    out = []
    for c in fold(t):
        if c in CONF:
            out.append(CONF[c])
        elif ord(c) > 127 and lat_base(c):
            out.append(lat_base(c))
        else:
            out.append(c)
    return "".join(out)


def camel(t):
    """Insert a space at each lower-to-upper letter change (ClaudeCode -> Claude Code), so a joined compound is read as its parts too."""
    out = []
    for i, c in enumerate(t):
        if i and c.isupper() and t[i - 1].islower():
            out.append(" ")
        out.append(c)
    return "".join(out)


def ones_readings(s, cap=8):
    """The digit 1 is read both ways (i and l): every reading of the first 8 ones in this piece; the rest all i or all l (a listed word has at most 4 such letters, so more cannot match)."""
    idx = [i for i, c in enumerate(s) if c == "1"]
    if not idx:
        return [s]
    head, tail = idx[:cap], idx[cap:]
    out = []
    for rest in (("i", "l") if tail else ("i",)):
        for mask in range(1 << len(head)):
            chars = list(s)
            for k, i in enumerate(head):
                chars[i] = "l" if (mask >> k) & 1 else "i"
            for i in tail:
                chars[i] = rest
            out.append("".join(chars))
    return out


def dotted(x):
    return re.sub(
        r"(?<!%s)(%s(?:\.%s)+)(?!%s)" % (LETTER, LETTER, LETTER, LETTER),
        lambda m: m.group(1).replace(".", ""),
        x,
    )


def cands(t):
    """Every word a text can be read as: each space-separated piece is read split at every non-letter (single letters joined by dots; each run of letters and digits read on its own, so ones elsewhere in the text cannot change it) and squeezed (Cl-aude, Bo.t, Cl@ude); the text is read as written and with a space inserted at each lower-to-upper change (ClaudeCode)."""
    out = set()
    for variant in (t, camel(t)):
        for piece in skel(variant).split():
            for form in (piece, piece.translate(AT)):
                for tok in re.findall(r"[^\W_]+", dotted(form)):
                    for r in ones_readings(tok.translate(LEET)):
                        out.update(re.findall(r"%s+" % LETTER, r))
                for r in ones_readings(form.translate(LEET)):
                    sq = "".join(re.findall(LETTER, r))
                    if sq:
                        out.add(sq)
    return out


def ordered(t):
    return re.findall(r"%s+" % LETTER, dotted(skel(t).translate(LEET).replace("1", "i")))


def find_all(words, listed, stem=False):
    hits = []
    for w in sorted(words):
        if w in listed:
            hits.append((w, w))
        elif stem:
            for suf in ("s", "es"):
                if w.endswith(suf) and w[: -len(suf)] in STEMS:
                    hits.append((w, w[: -len(suf)]))
                    break
    return hits


def refuse_listed(hit, where, kind):
    w, base = hit
    if w == base:
        refuse("listed word %s" % base, "the %s contains the whole word '%s', which is on the list of refused %s" % (where, w, kind))
    refuse("listed word %s" % base, "the %s contains '%s', which is the listed word '%s' with an s or es ending (list of refused %s)" % (where, w, base, kind))


def mixed(t):
    """One word whose letters come from two scripts (Latin with Cyrillic, Greek, Armenian, Cherokee, a modifier letter, ...) is refused, whatever the scripts are. Han, Hiragana, Katakana and Hangul count as one script (Japanese and Korean names mix them)."""
    for w in re.findall(r"[^\W\d_]+", unicodedata.normalize("NFKD", t)):
        if len({script_of(c) for c in w}) > 1:
            return True
    return False


NOTREAD = notread

try:
    line = read_stdin().strip(" \t\r\n")
    if len(line) > MAXLEN:
        refuse("too long", "the line is longer than %d characters" % MAXLEN)
    line = line.translate(APOSTROPHES)
    # first the two stand-in classes that have their own message in take_check.sh (a placeholder, a session or 'lead to confirm'); read on the text WITHOUT its hidden characters, so a hidden character cannot hide them
    shown, bad = scan(line)
    shown_words = cands(shown)
    if "placeholder" in shown_words:
        refuse("listed word placeholder", "the line contains the whole word 'placeholder'")
    if "session" in shown_words:
        refuse("listed word session", "the line contains the whole word 'session'")
    if re.search(r"\blead\s+to\s+confirm\b", skel(shown)):
        refuse("lead to confirm", "the line says the lead still has to confirm it")
    if bad is not None:
        refuse("hidden character", "the line holds a control, invisible or detached combining character (U+%04X)" % ord(bad))
    line = shown   # only accepted joiners were removed
    if pindate:
        try:
            date.fromisoformat(pindate)
        except ValueError:
            refuse("bad pin date", "the pin's own '# date (UTC)' line (%s) is not a real calendar date: the fault is in the pin, not in the reviewer line" % pindate)
    i = line.find(",")
    if i < 0:
        refuse("shape", "there is no comma; the line must read NAME, YYYY-MM-DD or NAME, YYYY-MM-DD, a note")
    name, rest = line[:i], line[i:]
    m = re.fullmatch(r", (\d{4}-\d{2}-\d{2})(?:, (\S.*))?", rest, re.ASCII)
    if not m:
        refuse(
            "shape",
            "the line must read NAME, YYYY-MM-DD or NAME, YYYY-MM-DD, a note: exactly one comma and one space "
            "between the name and the date, no comma inside the name and no text between the name and the date "
            "(write 'Jane Roe', not 'Roe, Jane'; write 'John Smith Jr.' with no comma)",
        )
    ds, note = m.group(1), (m.group(2) or "")
    rm = None
    if receipt != "-":
        rm = re.fullmatch(r"pin sha256 ([0-9a-f]{8})(?:, (\S.*))?", note, re.ASCII)
        note_scan = (rm.group(2) or "") if rm else note
    else:
        note_scan = note
    if not name or not (unicodedata.category(name[0])[0] == "L"):
        refuse("name characters", "the name must start with a letter")
    for ch in name:
        if unicodedata.category(ch) == "Lm" and script_of(ch) != "CJK":
            refuse("modifier letter", "the name holds the modifier letter U+%04X; write plain letters and the plain apostrophe '" % ord(ch))
        if ch not in " .'-" and unicodedata.category(ch)[0] not in "LM":
            refuse("name characters", "the name may hold only letters, spaces, dots, apostrophes and hyphens (no digits or other signs)")
    letters = [ch for ch in name if unicodedata.category(ch)[0] == "L"]
    need = 2 if letters and all(script_of(ch) == "CJK" for ch in letters) else 3   # a name in Han, Kana or Hangul letters is often 2 characters
    if len(letters) < need:
        refuse("name too short", "the name has fewer than %d letters" % need)
    pieces = name.split()
    for k, piece in enumerate(pieces):
        n_letters = sum(1 for ch in piece if unicodedata.category(ch)[0] == "L")
        if n_letters < 2 and not re.fullmatch(r"[^\W\d_]\.", fold(piece)):
            if piece in PARTICLES and 0 < k < len(pieces) - 1 and len(pieces) >= 3:
                continue   # a lower-case particle between two name words (Ortega y Gasset, Maria e Silva)
            refuse("name word too short", "every word of the name needs at least 2 letters (a single initial must be written with a dot, as in 'Q.'; a small joining word such as y or e is accepted only between two other name words)")
    if mixed(name) or mixed(note_scan):
        refuse("mixed alphabets", "one word mixes letters of two alphabets (for example Latin letters with Cyrillic, Greek or Armenian look-alike letters)")
    nwords = cands(name)
    nwords.add("".join(re.findall(LETTER, skel(name).translate(LEET).replace("1", "i"))))   # the whole name squeezed (letters only)
    nwords.update(cands(re.sub(r"[ .'-]", "", name)))   # camelCase compounds written without spaces are read in parts too
    first = (re.findall(r"%s+" % LETTER, fold(name)) or [""])[0]
    seq = ordered(name)
    listed_all = ALL | NEG | WEAK | NAME
    others = [w for w in seq if len(w) >= 2 and w not in listed_all]   # name words that are not on any list
    hits = [h for h in find_all(nwords, ALL, stem=True) if h[0] not in WEAK]   # Sessions (a surname) is a weak word; Session stays refused
    if hits:
        refuse_listed(hits[0], "name", "words")
    for h in find_all(nwords, NEG):
        if h[0] == "ai" and seq[:1] == ["ai"] and others:
            continue   # Ai Nguyen, Ai Weiwei: ai as the FIRST word of a name that has another name word
        if h[0] not in seq and re.search(r"(?:\b[^\W\d_]\.\s*){2,}", name):
            continue   # dotted initials (L. L. M.) that only join into a listed word
        refuse_listed(h, "name", "words")
    for h in find_all(nwords, WEAK):
        if not others:
            refuse_listed(h, "name", "words that are tool names and also real names (accepted only when another name word stands with them)")
    if not (testallow == "1" and first == testword):
        hit = find_all(nwords, NAME)
        if hit:
            refuse_listed(hit[0], "name", "name words")
        for ph in PHRASES:
            for k in range(len(seq) - len(ph) + 1):
                if tuple(seq[k : k + len(ph)]) == ph:
                    refuse("listed words %s" % " ".join(ph), "the name contains the words '%s' in a row, which are on the list of refused name phrases" % " ".join(ph))
    nw = cands(note_scan)
    nseq = ordered(note_scan)
    for h in find_all(nw, ALL | WEAK, stem=True):
        refuse_listed(h, "note", "words")
    for h in find_all(nw, NEG):
        # a note may say that a tool was NOT used (no AI used): every plain occurrence must follow a negating word, and the word must be there as a plain word
        ks = [k for k, w in enumerate(nseq) if w == h[0]]
        if not ks or any(k == 0 or nseq[k - 1] not in NEGATORS for k in ks):
            refuse_listed(h, "note", "words (allowed only right after one of: %s)" % " ".join(sorted(NEGATORS)))
    if re.search(NOTREAD, skel(note_scan)):
        refuse("note says not read", "the note says the lines were not read, not checked or only skimmed (or will be read, reviewed or checked later)")
    try:
        d = date.fromisoformat(ds)
    except ValueError:
        refuse("bad date", "%s is not a real calendar date" % ds)
    today = date.fromisoformat(today_s) if today_s else datetime.now(timezone.utc).date()
    if d > today + timedelta(days=1):
        refuse("future date", "%s is more than one day ahead of today (UTC date today: %s; a person west of UTC may still be on the day before: write the UTC date)" % (ds, today.isoformat()))
    if pindate:
        if d < date.fromisoformat(pindate):
            refuse("old date", "%s is older than the pin's own '# date (UTC)' line (%s)" % (ds, pindate))
    if receipt != "-":
        if rm is None:
            refuse("receipt missing", "after the date the line must say ', pin sha256 XXXXXXXX' (the first 8 characters of the sha256 that this script prints for the WARN lines of the pin it is judging)")
        if rm.group(1) != receipt:
            refuse("receipt wrong", "the 8 characters after 'pin sha256' are not the first 8 of the sha256 of the WARN lines of THIS pin: the pin changed after the line was written, or the line was written for another pin")
except SystemExit:
    raise
except Exception as e:  # a helper fault is never a pass
    print("HELPER ERROR: %s" % type(e).__name__)
    sys.exit(3)
print("ok")
PYEOF
IFS= read -r -d '' SAFE_PY <<'PYEOF' || true
t, _ = scan(read_stdin())
if len(t) > 300:
    print("%s [cut: 300 of %d characters shown]" % (t[:300], len(t)))
else:
    print(t)
PYEOF
REVIEWER_PY_FULL="from datetime import date, datetime, timedelta, timezone
$REVIEWER_NORM_PY
$REVIEWER_PY"
standin_allowed() { if [ "${TAKE_CHECK_TEST:-}" = 1 ] && [ -n "${TAKE_CHECK_WARN_PIN:-}" ]; then echo 1; else echo 0; fi; }   # the one place that decides whether the test stand-in name may pass: test flag AND a pin override
reviewer_ok() { # $1 = the reviewer line as written, $2 = the pin's own date, $3 = the fixed "today" (a test only; the normal take passes "" and so always uses the real UTC date), $4 = 1 when the test stand-in name is allowed, $5 = the receipt (first 8 hex of the sha256 of the pin's WARN lines) or "-" when no receipt is asked (only the helper option --check-reviewer-line without a third argument does that); sets REV_REASON and REV_RC; returns 0 for a line that passes the word check, 1 otherwise. It reads NO variable of its own: only its five arguments (round f8-r8, M1).
  local out
  out=$(printf '%s' "$1" | python3 -I -c "$REVIEWER_PY_FULL" "${2:-}" "${4:-0}" "$REVIEWER_WORDS_ALL" "$REVIEWER_WORDS_NAME" "$REVIEWER_PHRASES_NAME" "${3:-}" "$REVIEWER_TESTONLY" "${5:--}" "$REVIEWER_WORDS_WEAK" "$REVIEWER_WORDS_NEG" "$REVIEWER_NEGATORS" "$REVIEWER_PARTICLES" "$REVIEWER_NOTREAD" 2>&1); REV_RC=$?
  REV_REASON=$out
  [ "$REV_RC" -eq 0 ]
}
safe_text() { printf '%s' "$1" | python3 -I -c "$REVIEWER_NORM_PY
$SAFE_PY" 2>/dev/null || printf '(text not shown)'; }   # hidden characters removed by the same function as the check; cut at 300 characters with the length said
USAGE="usage: take_check.sh [--flows DIR] [--write-warn-pin NEWFILE]"
abspath() { case "$1" in /*) printf '%s' "$1";; *) printf '%s/%s' "$PWD" "$1";; esac; }   # before the cd below, so a relative path means what the person typed
WRITEPIN=""; FLOWSARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --write-warn-pin) [ -n "${2:-}" ] || { echo "$USAGE"; exit 2; }; WRITEPIN=$(abspath "$2"); shift 2;;
    --flows) [ -n "${2:-}" ] || { echo "$USAGE"; exit 2; }; FLOWSARG=$(abspath "$2"); shift 2;;
    --reviewer-words) echo "Words refused in the name and in the note: $REVIEWER_WORDS_ALL"; echo "Words refused in the name only: $REVIEWER_WORDS_NAME"; echo "Word pairs refused in the name only (two words in a row, an underscore stands for the space): $REVIEWER_PHRASES_NAME"; echo "Tool names that are also real names: refused in the note, and in the name unless another name word stands with them: $REVIEWER_WORDS_WEAK"; echo "Words refused in the name and in the note, except that the note may say a tool was not used (the word right before must be one of: $REVIEWER_NEGATORS): $REVIEWER_WORDS_NEG"; echo "Phrases in the note that say the lines were not read (regular expression, applied to the note in its normal form): $REVIEWER_NOTREAD"; exit 0;;
    --standin-name) echo "$REVIEWER_STANDIN_NAME"; exit 0;;   # the name run_all.sh puts in its stand-in pin (accepted only with the test flag and a pin override)
    --safe-text) safe_text "${2-}"; exit 0;;   # prints a text with the hidden characters removed and cut at 300 characters (run_all.sh uses it for the committed pin's line)
    --check-reviewer-line) [ $# -ge 2 ] || { echo "$USAGE"; exit 2; }
      # test helper: only the reviewer-line word check, nothing else runs. TAKE_CHECK_TODAY (a fixed date) is read here only, and only with the test flag, so a test cannot race UTC midnight
      today=""; [ "${TAKE_CHECK_TEST:-}" = 1 ] && today=${TAKE_CHECK_TODAY:-}
      if reviewer_ok "$2" "${3:-}" "$today" "$(standin_allowed)" "${4:--}"; then echo "$REV_REASON"; exit 0; else echo "$REV_REASON"; exit "$([ "${REV_RC:-1}" -eq 3 ] && echo 3 || echo 1)"; fi;;
    *) echo "$USAGE"; exit 2;;
  esac
done
if [ -n "$FLOWSARG" ] && [ -n "${TAKE_CHECK_FLOWS:-}" ]; then
  echo "REFUSED: the environment variable TAKE_CHECK_FLOWS and the option --flows are both set; the folder to check would be ambiguous. Give only --flows DIR (the documented way), or only the variable in a test."; exit 2
fi
OVR=()   # active environment overrides (each one changes what is checked)
for v in TAKE_CHECK_CK TAKE_CHECK_WARN_PIN TAKE_CHECK_FLOWS TAKE_CHECK_DDL TAKE_CHECK_FORM_EXPECT; do
  if [ -n "${!v:-}" ]; then
    case "$v" in TAKE_CHECK_FORM_EXPECT) OVR+=("$v=${!v}");; *) OVR+=("$v=$(abspath "${!v}")");; esac
  fi
done
[ -n "${TAKE_CHECK_CK:-}" ] && TAKE_CHECK_CK=$(abspath "$TAKE_CHECK_CK")
[ -n "${TAKE_CHECK_WARN_PIN:-}" ] && TAKE_CHECK_WARN_PIN=$(abspath "$TAKE_CHECK_WARN_PIN")
[ -n "${TAKE_CHECK_FLOWS:-}" ] && TAKE_CHECK_FLOWS=$(abspath "$TAKE_CHECK_FLOWS")
[ -n "${TAKE_CHECK_DDL:-}" ] && TAKE_CHECK_DDL=$(abspath "$TAKE_CHECK_DDL")
PIN="${TAKE_CHECK_WARN_PIN:-$HERE/take-warns.pin}"   # the expected set of WARN lines for the take (path prefix removed)
if [ -n "$WRITEPIN" ]; then
  if [ -e "$WRITEPIN" ] || [ -L "$WRITEPIN" ] || [ "$WRITEPIN" = "$PIN" ]; then
    echo "REFUSED: $WRITEPIN already exists (or is the pin in use). --write-warn-pin writes a NEW file only, so the pin in use can never be overwritten by the run that is judged against it."; exit 2
  fi
fi
cd "$HERE/../.." || exit 3   # the handover folder: paths printed below are short and relative to it
D="${TAKE_CHECK_FLOWS:-${FLOWSARG:-demo/n8n-flows-real-v5}}"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/take-check.XXXXXX") || exit 3
trap 'rm -rf -- "$TMP"' EXIT
OUT="$TMP/out"; NORM="$TMP/norm"
DDL="${TAKE_CHECK_DDL:-demo/n8n-flows-v4/mf_leads.sql}"
# round 10d: sha256 of stdin as 64 hex characters; no output and status 1 when sha256sum fails (a failure must never turn into an empty hash)
sha_stdin() { local o; o=$(sha256sum 2>/dev/null) || return 1; o=${o%% *}; case $o in *[!0-9a-f]*|"") return 1;; esac; [ ${#o} -eq 64 ] || return 1; printf '%s' "$o"; }
# round 10c (Q2): sha256 of the four flow files AND of every other *.json in the folder (this script reads all *.json there for the run-saving check), taken BEFORE the checker runs and again after the last read; a difference is exit 4. A file that is not a regular file or that sha256sum cannot read is printed as MISSING (never as an empty hash).
flow_snapshot() {   # $1 = the folder to hash (the original folder, or the private copy)
  SNAP_FOUR=""; SNAP_OTHER=""; SNAP_MISSING=0
  local f p h
  for f in mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; do
    p="$1/$f"
    if [ -f "$p" ] && h=$(sha256sum -- "$p" 2>/dev/null) && [ -n "$h" ]; then SNAP_FOUR="$SNAP_FOUR${h%% *}  $f"$'\n'
    else SNAP_FOUR="${SNAP_FOUR}MISSING  $f"$'\n'; SNAP_MISSING=1; fi
  done
  for p in "$1"/*.json; do
    [ -e "$p" ] || [ -L "$p" ] || continue
    f=${p##*/}
    case "$f" in mf-form.json|mf-hook.json|mf-recovery.json|mf-sub-crm-mail.json) continue;; esac
    if [ -f "$p" ] && h=$(sha256sum -- "$p" 2>/dev/null) && [ -n "$h" ]; then SNAP_OTHER="$SNAP_OTHER${h%% *}  $f"$'\n'
    else SNAP_OTHER="${SNAP_OTHER}MISSING  $f"$'\n'; SNAP_MISSING=1; fi
  done
}
flow_snapshot "$D"; SNAP_BEFORE="$SNAP_FOUR$SNAP_OTHER"; FLOWSHA_LINES=$SNAP_FOUR; FLOWSHA_MISSING=$SNAP_MISSING; OTHER_LINES=$SNAP_OTHER   # round 10d: taken BEFORE has_keyok and the other reads of the flow files below
# round f8-r9 (m9): READ ONCE. The folder is copied once into a private folder of this run (cp -a keeps links and folders as they are, so a listed flow that is a folder or a dangling link is still seen as one); the copy is hashed and must equal the hash taken just above; the checker and every other read below use the COPY, so every reader sees the very bytes that were hashed. The original is hashed again at the end: a write made to it during the run is still exit 4.
DC="$TMP/flows"; COPYFAIL=0; COPYDIFF=0
if [ -d "$D" ] && mkdir "$DC" && cp -a -- "$D"/. "$DC"/ 2>/dev/null; then
  flow_snapshot "$DC"; [ "$SNAP_BEFORE" = "$SNAP_FOUR$SNAP_OTHER" ] || COPYDIFF=1
else
  COPYFAIL=1; DC="$D"   # a folder that does not exist or cannot be copied: the checker is run on it as before and says what is wrong; this script adds a problem
fi
has_keyok() { python3 -I -c 'import json,sys; sys.exit(0 if any(n.get("name") == "KeyOk" for n in json.load(open(sys.argv[1], encoding="utf-8"))["nodes"]) else 1)' "$1" 2>/dev/null; }   # the node list is read as JSON (a text match would also hit a leftover connection that names KeyOk)
# node:connection count of mf-form and mf-hook, detected per file: 15:14 when the file holds the F-002 key check (it adds 3 nodes), else 12:11. TAKE_CHECK_FORM_EXPECT (test hook) overrides both.
FORMCNT_FORM="${TAKE_CHECK_FORM_EXPECT:-$(has_keyok "$DC/mf-form.json" && echo 15:14 || echo 12:11)}"
FORMCNT_HOOK="${TAKE_CHECK_FORM_EXPECT:-$(has_keyok "$DC/mf-hook.json" && echo 15:14 || echo 12:11)}"
PCOPT=(); if has_keyok "$DC/mf-form.json" && has_keyok "$DC/mf-hook.json"; then PCOPT=(--patch-checks F002); fi   # both entry flows carry the key check: also check its content (names, links, condition); only F002 here, because F-008 is judged by the exact settings check below
DDLOPT=(); [ -f "$DDL" ] && DDLOPT=(--ddl "$DDL")
python3 -I "${TAKE_CHECK_CK:-$HERE/check_flows.py}" "$DC" "${DDLOPT[@]}" "${PCOPT[@]}" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --accept-no-save mf-recovery.json \
  --expect mf-form.json="$FORMCNT_FORM" --expect mf-hook.json="$FORMCNT_HOOK" --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
  --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token \
  --quiet-info > "$OUT" 2>&1
RC=$?
if [ "$DC" != "$D" ]; then   # the checker printed the path of the private copy: show the folder the person gave
  python3 -I -c 'import sys; p, a, b = sys.argv[1:4]; t = open(p, encoding="utf-8", errors="surrogateescape").read(); open(p, "w", encoding="utf-8", errors="surrogateescape").write(t.replace(a, b))' "$OUT" "$DC" "$D" || { RC=3; echo "!!! could not rewrite the folder name in the checker output" >&2; }
fi
PROBLEMS=()   # things this script itself found wrong (each one makes the exit status 4 when the checker exited 0)
[ "$COPYFAIL" = 1 ] && PROBLEMS+=("flows folder could not be copied")
[ "$COPYDIFF" = 1 ] && PROBLEMS+=("flow files changed while they were copied")
HAZTXT="ENVIRONMENT HAZARDS: none"
if [ -n "$ENVHAZ" ]; then HAZTXT="ENVIRONMENT HAZARDS:$ENVHAZ these can change what this script runs (this script exits 4)"; PROBLEMS+=("environment hazard:$ENVHAZ"); fi
CMDTXT="Commands used (as found on PATH):"; for c in python3 sha256sum sort sed grep diff cmp date; do CMDTXT="$CMDTXT $c=$(command -v "$c" 2>/dev/null || echo NOT-FOUND)"; done
if [ ${#OVR[@]} -gt 0 ]; then
  OVRTXT="ACTIVE ENVIRONMENT OVERRIDES: ${OVR[*]}"
  if [ "${TAKE_CHECK_TEST:-}" = 1 ]; then OVRTXT="$OVRTXT (test flag TAKE_CHECK_TEST=1 is set: this is a test run, not a take check; a run that would pass exits 5, never 0)"; else OVRTXT="$OVRTXT (NOT allowed outside tests: this script exits 4)"; PROBLEMS+=("environment override(s) without the test flag"); fi
else
  OVRTXT="OVERRIDES: none"
fi
FLOWSTXT="Flows folder checked: $D"
if [ -n "$FLOWSARG" ]; then FLOWSTXT="$FLOWSTXT (given with --flows)"; elif [ -n "${TAKE_CHECK_FLOWS:-}" ]; then FLOWSTXT="$FLOWSTXT (taken from the environment variable TAKE_CHECK_FLOWS, a test override)"; else FLOWSTXT="$FLOWSTXT (the built-in default folder)"; fi
# round 10b (M-2): a sha256 of the four checked flow files, so a person can compare it with the sha written down at re-pin (a different file with the same name gives a different sha); round 10c: taken before the checker ran (see flow_snapshot above)
if FLOWSHA=$(printf '%s' "$FLOWSHA_LINES" | sha_stdin); then FLOWSHA_HEX=$FLOWSHA; else FLOWSHA="UNAVAILABLE (sha256sum failed)"; FLOWSHA_HEX=""; PROBLEMS+=("sha256sum failed (flow files)"); echo "!!! sha256sum FAILED on the flow file list: the combined sha256 of the flow files is unavailable. This script exits 4." >&2; fi
[ "$FLOWSHA_MISSING" = 1 ] && FLOWSHA="$FLOWSHA (at least one *.json file in the folder is MISSING or unreadable)"
[ "$FLOWSHA_MISSING" = 1 ] && PROBLEMS+=("a flow file is missing or unreadable")
echo "=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ==="
echo "$OVRTXT"
echo "$HAZTXT"
echo "$CMDTXT"
echo "$FLOWSTXT"
echo "sha256 of the four flow files checked (compare with the sha written down at re-pin; it is the sha256 of the four lines below, without the two leading spaces):"
echo "  combined: $FLOWSHA"
printf '%s' "$FLOWSHA_LINES" | sed 's/^/  /'
echo "  other *.json files in the folder (also read by this script, sha256 taken too): $(printf '%s' "$OTHER_LINES" | grep -c .)"
printf '%s' "$OTHER_LINES" | grep -F MISSING | sed 's/^/  /'
if [ "$RC" -ge 2 ]; then
  CKRC=$RC; [ "$RC" -ge 4 ] && RC=3   # round 10c (Q5): the checker only has 0 to 3; any other number (127 not found, 137 killed) means it broke, and 4 is reserved for this script
  echo "=== THE CHECKER DID NOT GIVE A VERDICT (its exit status is $CKRC: 2 = started wrongly, 3 = broke; any number above 3 is shown as 3 here). Nothing below says anything about the flows. ==="
  cat "$OUT"
  echo "FINAL: take_check exit status $RC. Flow files sha256 (four files, combined): $FLOWSHA. $OVRTXT. exit 0 would have meant: no definite fault in the files; NOTHING ran in n8n. The checker gave no verdict; open items: unknown."
  exit "$RC"
fi
echo "=== READ THIS BLOCK BEFORE ANYTHING ELSE ==="
echo "--- (1) The lead table and the column check ---"
cnt() { grep -c -E -- "$1" "$OUT"; }   # N3: a closing-block line must appear exactly once (a flow text that imitates it must not win by being first)
if [ ${#DDLOPT[@]} -gt 0 ] && [ "$(cnt '^SQL columns compared with the --ddl file:')" != 1 ]; then PROBLEMS+=("closing line 'SQL columns compared' not exactly once"); fi
[ "$(cnt '^RESULT: ')" -le 1 ] || PROBLEMS+=("line 'RESULT:' seen more than once")
[ "$(cnt '^Known open problems: ')" -le 1 ] || PROBLEMS+=("line 'Known open problems' seen more than once")
QN=$(sed -n 's/^SQL columns compared with the --ddl file: \([0-9][0-9]*\) query string.*/\1/p' "$OUT" | head -n 1)
UNCMP=$(sed -n 's/^SQL NOT COMPARED: query strings read but not compared[^=]*=\([0-9]*\);.*/\1/p' "$OUT" | head -n 1)
COLW=$(sed -n 's/^SQL WARNS: column WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
TBLW=$(sed -n 's/^SQL WARNS: .* table WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
NOQ=$(sed -n 's/^SQL WARNS: .*(not compared)=\([0-9]*\).*/\1/p' "$OUT" | head -n 1)
if [ ${#DDLOPT[@]} -eq 0 ]; then
  echo "!!! THE TABLE FILE IS MISSING: demo/n8n-flows-v4/mf_leads.sql was not found, so the column names in the SQL steps were NOT checked. On the older table the alert steps fail on every run and no alert is sent. This script exits 4."
  PROBLEMS+=("table file missing")
else
  echo "Table definition used for the column check: $DDL (the take needs demo/n8n-flows-v4/mf_leads.sql, with the four alert columns, not the older one in demo/n8n-flows)."
  echo "Query strings read AND compared: ${QN:-unknown}. Query strings read but NOT compared (no table name, only {{ }}): ${UNCMP:-unknown}. Column WARNs: ${COLW:-unknown}. Table WARNs: ${TBLW:-unknown}. Postgres steps with no query text (not compared): ${NOQ:-unknown}."
  if [ -z "$QN" ] || [ "$QN" -eq 0 ]; then
    echo "!!! 0 QUERY STRINGS WERE READ (or the count line is missing): NO column was compared. This script exits 4."
    PROBLEMS+=("0 queries read")
  fi
  if [ "${COLW:-1}" -gt 0 ] || [ "${TBLW:-1}" -gt 0 ] || [ "${NOQ:-1}" -gt 0 ] || [ "${UNCMP:-1}" -gt 0 ]; then
    echo "!!! A COLUMN OR TABLE IS MISSING, or a step was not compared (counts above, WARN lines further down): the alert or lead steps would fail on every run. This script exits 4."
    PROBLEMS+=("column/table WARN")
  fi
fi
echo "GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out."
echo "--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---"
grep -h -E '^mf-[a-z-]+\.json nodes=' "$OUT"
grep -h -E '^mf-[a-z-]+\.json nodes=.* saveDataSuccess=all saveDataError=all saveManual=True$' "$OUT" | sed -E 's/^(mf-[a-z-]+\.json) .*/INFO: \1 run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names. This script never deletes them; what happens to them after the take is a person'"'"'s decision./'
grep -h -E "^WARN .*run-saving settings" "$OUT" | cut -c1-260
grep -h -E "^WARN accept-no-save" "$OUT" | cut -c1-260
grep -h -E "^ACCEPTED: " "$OUT" | cut -c1-300
if grep -q -E "^WARN .*run-saving settings|^WARN accept-no-save" "$OUT"; then
  echo "!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4."
  PROBLEMS+=("run saving off")
fi
# round 9 (M2): the check above only sees the words "none" and false. Every flow except the accepted recovery flow must say exactly all / all / True (a missing settings block, a missing key or an odd word such as "off" also keeps the run list empty or undefined).
SAVEBAD=$(python3 -I - "$DC" <<'PYEOF'
import glob, json, os, sys
files = sorted(glob.glob(os.path.join(sys.argv[1], "*.json")))
if not files:
    print("no flow file found")
for p in files:
    fn = os.path.basename(p)
    if fn == "mf-recovery.json":
        continue
    try:
        st = json.load(open(p, encoding="utf-8")).get("settings")
    except (OSError, ValueError, AttributeError):
        print(f"{fn}: file or settings block unreadable")
        continue
    st = st if isinstance(st, dict) else {}
    got = (st.get("saveDataSuccessExecution"), st.get("saveDataErrorExecution"), st.get("saveManualExecutions"))
    if not (got[0] == "all" and got[1] == "all" and got[2] is True):
        print(f"{fn}: saveDataSuccessExecution={got[0]!r} saveDataErrorExecution={got[1]!r} saveManualExecutions={got[2]!r}")
PYEOF
)
SBRC=$?   # N2: a helper that crashed must not look like "nothing wrong"
if [ "$SBRC" -ne 0 ]; then echo "!!! THE RUN-SAVING HELPER FAILED (exit status $SBRC): run saving was not checked exactly. This script exits 4."; PROBLEMS+=("run-saving helper failed"); fi
if [ -n "$SAVEBAD" ]; then
  echo "!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4."
  printf '%s\n' "$SAVEBAD" | sed 's/^/    /'
  PROBLEMS+=("run saving not all/all/True")
fi
if [ -f "$DC/mf-recovery.json" ] && ! grep -q -F "ACCEPTED: recovery flow not part of the take (decision 4)" "$OUT"; then
  echo "!!! THE RECOVERY FLOW IS NOT PRINTED AS ACCEPTED (line 'ACCEPTED: recovery flow not part of the take (decision 4)' is missing): its run saving is not an excused decision. This script exits 4."
  PROBLEMS+=("recovery flow not accepted")
fi
echo "--- (3) Values that must be filled in before import: mail addresses and credential ids ---"
awk '/^(PLACEHOLDERS IN NODE SETTINGS|CREDENTIAL IDS STILL PLACEHOLDERS)/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---"
NOKEY=0
for f in mf-form.json mf-hook.json; do
  # the node list is read as JSON (a text match would also hit a leftover connection that names KeyOk)
  if has_keyok "$DC/$f"; then echo "$f: key check present (F-002 applied)"; else echo "$f: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4."; NOKEY=$((NOKEY+1)); fi
done
if [ "$NOKEY" -gt 0 ]; then echo "!!! The take needs F-002: this script exits 4 ($NOKEY entry flow(s) above have no key check)."; PROBLEMS+=("key check absent in $NOKEY entry flow(s)"); fi
# round 10c (Q2): the last read of the flow files is above; hash them again and compare with the hash taken before the checker ran
flow_snapshot "$D"; SNAP_AFTER="$SNAP_FOUR$SNAP_OTHER"; CHANGED=0
if [ "$SNAP_BEFORE" != "$SNAP_AFTER" ] || [ "$SNAP_MISSING" = 1 ]; then
  if [ "$SNAP_BEFORE" != "$SNAP_AFTER" ]; then CHANGED=1; echo "!!! A FLOW FILE CHANGED WHILE THIS CHECK RAN (sha256 before the checker differs from sha256 after the last read): the checker and this script may have read different files, so nothing here is a verdict about one file set. Run it again when nothing writes to the folder. This script exits 4."; PROBLEMS+=("flow files changed during the check"); fi
fi
echo "--- (5) Open decisions and environment variables ---"
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted)' "$OUT"
awk '/^STEPS THAT READ ENVIRONMENT VARIABLES/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked."
RESULTLINE=$(grep -h -E '^RESULT: ' "$OUT" | head -n 1)
WARNN=$(sed -n 's/^RESULT: [0-9][0-9]* FAIL, \([0-9][0-9]*\) WARN.*/\1/p' "$OUT" | head -n 1)
UNVN=$(grep -E "^WARN" "$OUT" | grep -c -F "n8n rule UNVERIFIED")
python3 -I - "$OUT" "$D" > "$NORM" <<'PYEOF'
import sys
out, d = sys.argv[1], sys.argv[2]
lines = [l.rstrip("\n").replace(d + "/", "") for l in open(out, encoding="utf-8", errors="replace") if l.startswith("WARN")]
print("\n".join(sorted(lines)))
PYEOF
NRC=$?
if [ "$NRC" -ne 0 ]; then echo "!!! THE WARN-LINE HELPER FAILED (exit status $NRC): the WARN set was not read. This script exits 4."; PROBLEMS+=("warn helper failed"); fi
grep . "$NORM" | LC_ALL=C sort > "$NORM.now"
echo "--- (6) Checker result and the WARN baseline ---"
echo "${RESULTLINE:-RESULT line missing}. WARN lines that rest on an n8n rule nobody verified: $UNVN."
PINNED=0
if [ -z "$WARNN" ]; then
  echo "!!! THE CHECKER'S RESULT LINE IS MISSING: the WARN count is unknown. This script exits 4."
  PROBLEMS+=("result line missing")
elif [ ! -f "$PIN" ]; then
  echo "!!! THE WARN BASELINE FILE IS MISSING ($PIN): a new WARN (for example a disabled node, an unwired error output) could not be seen. This script exits 4."
  PROBLEMS+=("warn pin missing")
else
  tr -d '\r' < "$PIN" > "$NORM.pincr" || { echo "!!! THE PIN COULD NOT BE READ. This script exits 4."; PROBLEMS+=("warn pin missing"); : > "$NORM.pincr"; }   # a pin saved with Windows line ends (CR LF) is read like one with plain line ends
  grep -v -E '^#' "$NORM.pincr" | grep . | LC_ALL=C sort > "$NORM.pin"
  PINNED=$(grep -c . "$NORM.pin")
  PINHASH=$(sha_stdin < "$NORM.pin") || { PINHASH="UNAVAILABLE"; PROBLEMS+=("sha256sum failed (pin)"); echo "!!! sha256sum FAILED on the pin lines: the pin hash cannot be compared. This script exits 4."; }
  HDRHASH=$(sed -n 's/^# sha256 of the WARN lines below[^:]*: \([0-9a-f]\{64\}\)$/\1/p' "$NORM.pincr" | head -n 1)
  HDRDATE=$(sed -n 's/^# date (UTC): \([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)$/\1/p' "$NORM.pincr" | head -n 1)
  HDRREV=$(sed -n 's/^# reviewed by: \(.*\)$/\1/p' "$NORM.pincr" | head -n 1)
  HDRFLOWS=$(sed -n 's/^# flows sha256 (the four flow files, combined, as printed in the top block of take_check.sh): \([0-9a-f]\{64\}\)$/\1/p' "$NORM.pincr" | head -n 1)
  HDRSAFE=$(safe_text "$HDRREV")   # the line is printed with control and hidden characters removed
  if [ -z "$HDRREV" ]; then echo "!!! THE PIN HEADER HAS NO '# reviewed by: NAME, DATE' LINE: nobody has said that a person read these WARN lines. This script exits 4."; PROBLEMS+=("pin has no reviewer line")
  elif RCPT=nohash!!; case $PINHASH in *[!0-9a-f]*|"") ;; *) RCPT=${PINHASH:0:8};; esac; reviewer_ok "$HDRREV" "$HDRDATE" "" "$(standin_allowed)" "$RCPT"; then :   # f8-r8 (M1): today is never passed in a take, so no variable can move the date rule
  else
    case $REV_REASON in
      "HELPER ERROR"*) echo "!!! THE REVIEWER-LINE HELPER BROKE ($(safe_text "$REV_REASON"), status $REV_RC): this says nothing about the person named in the pin. Run: bash take_check.sh --check-reviewer-line '' to see the helper's own message. This script exits 4."; PROBLEMS+=("reviewer helper failed");;
      "REFUSED (rule: bad pin date)"*) echo "!!! THE PIN'S OWN DATE LINE IS NOT A REAL DATE ($(safe_text "$REV_REASON")): fix the '# date (UTC): YYYY-MM-DD' line of the pin (the fault is in the pin, not in the name on the reviewed-by line). This script exits 4."; PROBLEMS+=("pin has a bad date");;
      "REFUSED (rule: listed word placeholder)"*) echo "!!! THE PIN HEADER STILL HAS THE PLACEHOLDER IN ITS 'reviewed by' LINE: the file was written by the script and no person has read it. Read every line, then replace that line. This script exits 4."; PROBLEMS+=("pin not reviewed (placeholder)");;
      "REFUSED (rule: listed word session"*|"REFUSED (rule: lead to confirm)"*) echo "!!! pin not yet confirmed by the lead: the 'reviewed by' line of the pin (as written: $HDRSAFE) names a session or says the lead still has to confirm. A session is not a person who read the WARN lines. The lead reads every WARN line and replaces that line with: # reviewed by: NAME, YYYY-MM-DD. This script exits 4."; PROBLEMS+=("pin not yet confirmed by the lead");;
      *) echo "!!! THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON'S NAME AND A DATE (as written: $HDRSAFE): Rule that fired: $(safe_text "$REV_REASON") The line must read '# reviewed by: NAME, YYYY-MM-DD, pin sha256 XXXXXXXX' (XXXXXXXX = the first 8 characters of the sha256 printed on the 'Pinned WARN lines' line of this run; optionally followed by ', a note'), with a real date (the UTC date; not more than one day ahead and not older than the pin's own date line). If a rule about a listed word fired on your real name: write your name without the listed word (an initial and the rest, for example 'A. Jones' for 'Alexa Jones', or 'Pat J.'); a lead-signed list of exact names is an open question for the lead (QUESTIONS.md, Q31). What this checks: only typing mistakes. It turns away a tool or model name, a bot or agent word or another stand-in (TBD, none, unknown, placeholder) as a whole word in the name or the note, a name under 3 letters or a name word under 2 letters, a note that says the lines were not read, not checked or only skimmed, and look-alike letters from another alphabet, hidden characters and a few stand-in words such as Owner, System or John Doe. It does NOT prove that a real person wrote or read anything: the real control is a named person reading the WARN lines of the pin and approving it. This script exits 4."; PROBLEMS+=("pin reviewer line malformed or a stand-in");;
    esac
  fi
  if [ -z "$HDRFLOWS" ]; then echo "!!! THE PIN HEADER HAS NO '# flows sha256 ...' LINE: a changed flow file with the same step counts and WARN lines would pass. This script exits 4."; PROBLEMS+=("pin has no flows sha")
  elif [ -n "$FLOWSHA_HEX" ] && [ "$HDRFLOWS" != "$FLOWSHA_HEX" ]; then echo "!!! THE FLOW FILES DO NOT MATCH THE SHA-256 WRITTEN IN THE PIN (pin $HDRFLOWS, files $FLOWSHA_HEX): a flow file differs from the one a person pinned. If the change is intended, a person reads it, writes a NEW pin (--write-warn-pin) and installs it by hand. This script exits 4."; PROBLEMS+=("flow files differ from the pinned sha"); fi
  if [ -z "$HDRDATE" ]; then echo "!!! THE PIN HEADER HAS NO DATE ('# date (UTC): YYYY-MM-DD'): nobody can tell when a person read these WARN lines. This script exits 4."; PROBLEMS+=("pin has no date"); fi
  if [ -z "$HDRHASH" ]; then echo "!!! THE PIN HEADER HAS NO SHA-256 LINE: a hand edit of the pin cannot be seen. This script exits 4."; PROBLEMS+=("pin has no hash")
  elif [ "$HDRHASH" != "$PINHASH" ]; then echo "!!! THE PIN FILE DOES NOT MATCH ITS OWN SHA-256 (header $HDRHASH, lines $PINHASH): it was edited after a person read it. This script exits 4."; PROBLEMS+=("pin hash differs"); fi
  echo "Pinned WARN lines: $PINNED (pin dated ${HDRDATE:-unknown}, sha256 ${PINHASH:0:16}...; the reviewer line must say ', pin sha256 ' and the first 8 characters of this sha256, so it names THESE lines). (this script cannot tell who really read the lines; the reviewer line is printed with control and hidden characters removed and cut at 300 characters) reviewed by (as written in the pin): ${HDRSAFE:-nobody named}"
  echo "The pinned lines stand for KNOWN DEFECTS and open decisions (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them. Only the reviewer line above says who, if anyone, read them."
  if cmp -s "$NORM.pin" "$NORM.now"; then
    echo "WARN set equals the pinned set ($(grep -c . "$NORM.now") lines in ${PIN##*/}): no new and no vanished WARN."
  else
    echo "!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a NEW pin file with: bash take_check.sh --write-warn-pin NEWFILE (the run then exits 4 on purpose; install the file by hand, see README). This script exits 4."
    diff "$NORM.pin" "$NORM.now" | grep -E '^[<>]' | sed -e 's/^> /  + /' -e 's/^< /  - /' | cut -c1-260
    PROBLEMS+=("warn set changed")
  fi
fi
if [ -n "$WRITEPIN" ]; then
  # B1: written only after the comparison above, only when the checker found no FAIL and gave a RESULT line, into a file that did not exist; the run never counts as a pass
  BLOCKING=""   # round 10b (M-3): only the WARN difference (and a missing or unreadable OLD pin, which a new pin replaces) may be present; any other problem means the folder is not the take folder, so its WARN set is not worth pinning
  for pr in "${PROBLEMS[@]}"; do
    case "$pr" in "warn set changed"|"warn pin missing"|"pin has no date"|"pin has no hash"|"pin hash differs"|"pin has no reviewer line"|"pin not reviewed (placeholder)"|"pin not yet confirmed by the lead"|"pin reviewer line malformed or a stand-in"|"pin has no flows sha"|"flow files differ from the pinned sha") ;; *) BLOCKING="$BLOCKING [$pr]";; esac
  done
  if [ "$RC" -ne 0 ] || [ -z "$WARNN" ]; then
    echo "!!! NO PIN WRITTEN: the checker found a FAIL or gave no RESULT line, so this WARN set is not worth pinning. The exit status is printed in the FINAL line (the status of the checker, or 4 when that was 0)."
    PROBLEMS+=("pin not written")
  elif [ -n "$BLOCKING" ]; then
    echo "!!! NO PIN WRITTEN: this run has other problems besides a changed WARN set:$BLOCKING. Fix them first (for example apply the patches, put the table file in place, remove environment overrides). This script exits 4."
    PROBLEMS+=("pin not written")
  else
    DATE=$(date -u +%Y-%m-%d)
    NEWHASH=$(sha_stdin < "$NORM.now") || NEWHASH=""
    if [ -z "$NEWHASH" ] || [ -z "$FLOWSHA_HEX" ]; then
      echo "!!! COULD NOT WRITE $WRITEPIN: sha256sum failed, so the header hashes cannot be made. This script exits 4."
      PROBLEMS+=("pin not written")
    elif ( set -C; { echo "# expected WARN lines of the take check (folder path removed, sorted). WRITTEN BY take_check.sh --write-warn-pin AND NOT YET READ BY A PERSON: this file is not valid until a person reads every line and replaces the next line."; echo "# reviewed by: PLACEHOLDER-a person must read every WARN line below, then replace this whole line with: # reviewed by: NAME, YYYY-MM-DD, pin sha256 XXXXXXXX (XXXXXXXX = the first 8 characters of the sha256 on the next-but-one line)"; echo "# date (UTC): $DATE"; echo "# flows sha256 (the four flow files, combined, as printed in the top block of take_check.sh): $FLOWSHA_HEX"; echo "# sha256 of the WARN lines below (LC_ALL=C sort, one per line): $NEWHASH"; cat "$NORM.now"; } > "$WRITEPIN" ) 2>/dev/null; then
      echo "NEW PIN WRITTEN to $WRITEPIN ($(grep -c . "$NORM.now") lines). It is NOT in use. Difference against the pin in use (+ new, - gone):"
      diff "$NORM.pin" "$NORM.now" 2>/dev/null | grep -E '^[<>]' | sed -e 's/^> /  + /' -e 's/^< /  - /' | cut -c1-260
      echo "Receipt for the reviewer line: pin sha256 ${NEWHASH:0:8} . A person must read every line, replace the PLACEHOLDER line in its header with their name, date and that receipt, in the form NAME, YYYY-MM-DD, pin sha256 ${NEWHASH:0:8} (until then the script exits 4 on it), then install it by hand (cp NEWFILE take-warns.pin next to this script) and commit it. This run exits 4: writing a pin is never a pass."
      PROBLEMS+=("new pin written, not installed")
    else
      echo "!!! COULD NOT WRITE $WRITEPIN (it appeared meanwhile or the folder cannot be written). This script exits 4."
      PROBLEMS+=("pin not written")
    fi
  fi
fi
echo "=== end of top block; full checker output follows ==="
cat "$OUT"
KNOWN=$(sed -n 's/^Known open problems: \([0-9][0-9]*\).*/\1/p' "$OUT" | head -n 1)
OPEN=$(( ${KNOWN:-0} + 1 + ${#PROBLEMS[@]} ))   # the checker's own count, the psql gate (always a person's step), what this script found wrong (a missing key check is one of those)
if [ "$RC" -eq 0 ] && [ ${#PROBLEMS[@]} -gt 0 ]; then RC=4; fi
if [ "$CHANGED" = 1 ] && [ "$RC" -le 1 ]; then RC=4; fi   # a FAIL read from files that changed mid-run is not a trustworthy 1 either
if [ "$RC" -eq 0 ] && [ ${#OVR[@]} -gt 0 ]; then RC=5; fi   # round 10d (B3): a would-be pass with an override is a test run, never exit 0
echo "Open items counted: checker known open problems ${KNOWN:-0} + psql gate 1 + problems of this script ${#PROBLEMS[@]} (entry flows without the key check: $NOKEY, counted inside the problems)."
echo "FINAL: take_check exit status $RC. Flow files sha256 (four files, combined): $FLOWSHA. ${RESULTLINE:-RESULT line missing}. $PINNED pinned WARN lines stand for known defects that are not fixed. $OVRTXT. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: $OPEN. The reviewer line is text; not verified. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed, 5 = a test run with an override that would have passed.) This is not a pass for filming."
exit $RC
