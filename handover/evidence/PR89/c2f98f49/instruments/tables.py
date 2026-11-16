import json, collections, sys
RAW = "/home/user/build/evidence-raw/PR89-c2f98f49"
OUT = "/home/user/hadavin-sdk/handover/evidence/PR89/c2f98f49"
R = json.load(open(RAW + "/leak/leak-records.json"))
forms = ["plain", "reversed", "upper", "lower", "percent_all", "percent_quote", "percent_quote_lower", "base64", "hex", "zero_width", "two_lines"]
chans = ["rows", "on_result rows", "first_lines", "exception.str", "exception.repr", "exception.args", "exception.rows", "exception.notes", "traceback text", "parent stdout", "parent stderr", "left file names", "left file contents"]
allch = sorted({c for r in R for c in r["channels_nonempty"]} | {c for r in R for c in r["hits"]})
extra = [c for c in allch if c not in chans]
L = ["# Leak probes: password form x output channel", "", f"Cases run: {len(R)} (13 made-up passwords x up to 44 child behaviours). Each cell: cases where the form was found / cases where that channel held any text. SHOWN means found at least once.", "",
     "| form of the password | " + " | ".join(chans + extra) + " |", "|---|" + "---|" * len(chans + extra)]
for f in forms:
    row = []
    for c in chans + extra:
        n = sum(1 for r in R if c in r["channels_nonempty"])
        h = sum(1 for r in R if f in r["hits"].get(c, []))
        row.append(("SHOWN" if h else "NOT SHOWN") + f" ({h}/{n})" if n else "channel empty in every case")
    L.append(f"| {f} | " + " | ".join(row) + " |")
L += ["", "Channel names: `rows` = the returned list; `on_result rows` = rows handed to the caller's callback; `first_lines` = the caller's dictionary; `exception.*` = the raised error (text, repr, args, the `rows` of a canary failure, notes); a chained cause or context would appear as `exception.cause.*` / `exception.context.*` (no such channel held text in any case: listed above only if present); `traceback text` = `traceback.format_exception` of the raised error in the calling process; `parent stdout/stderr` = everything the calling process printed; `left file names/contents` = every file and folder left in the private temp folder of the call (lock folder included).", ""]
L += ["## Per made-up password (label, length) x child behaviour: forms found anywhere", "", "| password label | length | cases | cases with any form found | child behaviours where the raw JUnit copy did not hold the forms (console-only behaviours) |", "|---|---|---|---|---|"]
for lab in dict.fromkeys(r["label"] for r in R):
    rs = [r for r in R if r["label"] == lab]
    L.append(f"| {lab} | {rs[0]['pw_len']} | {len(rs)} | {sum(1 for r in rs if r['hits'])} | {', '.join(r['mode'] for r in rs if not r['planted_forms_in_raw_junit'])} |")
L += ["", "## Child behaviours (one run_mutants call each: baseline, one mutant, one canary run)", "", "| behaviour | calls | how the calls ended (count) | pytest runs per call |", "|---|---|---|---|"]
for m in dict.fromkeys(r["mode"] for r in R):
    rs = [r for r in R if r["mode"] == m]
    L.append(f"| {m} | {len(rs)} | {dict(collections.Counter(r['exc_type'] or 'returned rows' for r in rs))} | {sorted(set(r['pytest_calls'] for r in rs))} |")
L += ["", "Both halves of a password (8 characters or longer) present somewhere in one channel, not adjacent: " + (", ".join(f"{r['case']} ({', '.join(r['halves_both_present'])})" for r in R if r["halves_both_present"]) or "none")]
open(OUT + "/leak-table.md", "w").write("\n".join(L) + "\n")

A = json.load(open(RAW + "/addr/addr-records.json"))
L = ["# Address probes", "", "`child ran` = the instrument counted a pytest run OR the child test left its marker file. Passwords in inputs are shown as `<P>`.", "",
     "| # | case | input (HADAVIN_TEST_PG_DSN) | throwaway_hosts | pass_env | result | error class | pytest runs counted | child marker files | secret found in any output | message |", "|---|---|---|---|---|---|---|---|---|---|---|"]
esc = lambda s: str(s).replace("|", "\\|").replace("\n", "<LF>").replace("\x00", "<NUL>")
for r in A:
    L.append(f"| {r['n']} | {esc(r['id'])} | `{esc(r['input'])[:120]}` | {esc(r['throwaway_hosts'])} | {esc(r['pass_env'])} | {r['outcome']} | {r['exc_type']} | {r['pytest_calls_counted']} | {r['child_marker_files']} | {', '.join(r['secret_in_any_output']) or 'none'} | {esc(r['message'])} |")
L += ["", "## Environment variable NAMES the child saw", ""]
for r in A:
    if r["n"] in (0, 96) or "parent holds" in r["id"]:
        L.append(f"- case {r['n']} ({r['id']}): {r['child_env_names']}")
open(OUT + "/address-table.md", "w").write("\n".join(L) + "\n")

K = json.load(open(RAW + "/lock/lock-records.json"))
L = ["# Lock folder probes", "", "`<BASE>` = the private work folder of the case; `tmp` = its TMPDIR. `added/changed/removed` compare a listing (type, mode, owner, size, link count) of `tmp`, `xdg`, `target` and `outside` before and after the call.", "",
     "| case | tool run as uid | XDG_RUNTIME_DIR | result | error class | pytest runs | message | added | changed | removed |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in K:
    L.append(f"| {r['case']} | {r['run_as_uid']} | {r['XDG_RUNTIME_DIR'] or '(empty text)'} | {r['outcome']} | {r['exc_type']} | {r['pytest_calls']} | {esc(r['message'])} | {esc('; '.join(f'{k}: {v}' for k, v in r['added'].items()) or 'nothing')} | {esc(r['changed'] or 'nothing')} | {r['removed'] or 'nothing'} |")
open(OUT + "/lock-table.md", "w").write("\n".join(L) + "\n")
print("tables written")
