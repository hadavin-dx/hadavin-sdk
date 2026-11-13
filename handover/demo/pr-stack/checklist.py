"""Build the carry-over checklist from the saved API JSON and the read-only clone (no network)."""
import json, re, subprocess, sys, collections

D = "/tmp/demo-push/handover/demo/pr-stack"
REPO = "/tmp/work/ab-base"
FINAL = "2db392650e8b7ced5db7f66ca48b1c058bf5891c"


def git(*a):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, errors="replace")
    return r.returncode, r.stdout


def show(commit, path):
    rc, out = git("show", f"{commit}:{path}")
    return out.splitlines() if rc == 0 else None


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def gist(c):
    b = c["body"] or ""
    u = c["user"]["login"]
    sev = ""
    if u.startswith("deepsource"):
        m = re.search(r"</picture>(.*?)</h3>", b, re.S)
        g = strip_html(m.group(1)) if m else strip_html(b)
        m2 = re.search(r"severity_indicator_(\w+)\.svg", b)
        sev = m2.group(1) if m2 else ""
    elif u.startswith("codeant"):
        m = re.search(r"\*\*Suggestion:\*\*\s*(.+)", b)
        g = m.group(1) if m else next((l for l in b.splitlines() if l.strip()), "")
        m2 = re.search(r"Assessment:\*\*\s*\S+\s*`(\w+)`", b)
        sev = m2.group(1) if m2 else ""
    else:
        m = re.search(r"##\s*(.+)", b)
        g = m.group(1) if m else b.splitlines()[0]
        sev = "code-scanning"
    g = re.sub(r"[|\n\r]", " ", strip_html(g)).replace("`", "'")
    return g[:100], sev


rows = []
stats = collections.Counter()
for n in (1, 2, 3, 4):
    pr = json.load(open(f"{D}/raw-pull-{n}.json"))
    for c in json.load(open(f"{D}/raw-pulls-{n}-comments.json")):
        if c.get("in_reply_to_id"):
            stats[(n, "reply")] += 1
            continue
        path = c["path"]
        oline = c.get("original_line") or c.get("line")
        ocommit = c.get("original_commit_id") or c.get("commit_id")
        src = show(ocommit, path) or show(c["commit_id"], path)
        text = src[oline - 1].strip() if src and oline and oline <= len(src) else None
        fin = show(FINAL, path)
        if fin is None:
            status = "FILE-GONE"
        elif text is None:
            status = "UNKNOWN (original line not readable)"
        elif not text:
            status = "BLANK-LINE (cannot match)"
        else:
            hits = [i + 1 for i, l in enumerate(fin) if l.strip() == text]
            if oline in hits:
                status = f"SAME line {oline}"
            elif hits:
                status = "MOVED to " + ",".join(map(str, hits[:3])) + ("..." if len(hits) > 3 else "")
            else:
                status = "CHANGED (text gone)"
        outdated = "yes" if c.get("position") is None else "no"
        addressed = "yes" if re.search(r"addressed|resolved in|fixed in", c["body"] or "", re.I) else ""
        g, sev = gist(c)
        kind = status.split()[0]
        stats[(n, c["user"]["login"], kind)] += 1
        rows.append((n, c["id"], c["user"]["login"].replace("[bot]", ""), sev, f"{path}:{oline}", g, status, outdated, addressed))

with open(f"{D}/evidence-ab-checklist-stats.txt", "w") as f:
    f.write("$ python3 -I checklist.py  (PR, author, final-tree status) -> count\n")
    for k, v in sorted(stats.items(), key=str):
        f.write(f"{k} {v}\n")
    tot = collections.Counter(r[6].split()[0] for r in rows)
    f.write(f"TOTAL rows {len(rows)}: {dict(tot)}\n")
    f.write(f"outdated(position null): {sum(1 for r in rows if r[7]=='yes')}\n")
    f.write(f"body says addressed/resolved/fixed: {sum(1 for r in rows if r[8])}\n")

out = [
    "# Carry-over checklist: inline bot review comments on pull requests #1 to #4",
    "",
    "Generated from the public GitHub API (saved as raw-pulls-N-comments.json, fetched 2026-11-13) and a read-only clone at "
    "pr-3-tests 2db3926. Script: python3 -I checklist.py (no network).",
    "",
    "Read this first:",
    "- 'Open' here means every top-level inline comment. The public REST API does not say whether a thread is resolved "
    "(that needs the GraphQL API with a token; the token in this session was invalid). So none is known to be resolved; the lead "
    "ticks them off by hand.",
    "- 'Final tree' says whether the exact line the bot pointed at (read at the commit it reviewed) is still in the final tree "
    "2db3926: SAME line N = same text at the same line; MOVED = same text, other line; CHANGED = the file exists but that line "
    "text is gone (probably fixed or rewritten: check); FILE-GONE = the file is not in the final tree.",
    "- No human wrote an inline review comment on any of the four pull requests (all authors are bots).",
    "- Gists are the first 100 characters of the bot's own title, not a judgement of whether the finding is right.",
    "",
    "| done | PR | comment id | bot | severity | file:line (as reviewed) | gist (first 100 chars) | final tree 2db3926 |",
    "|---|---|---|---|---|---|---|---|",
]
for r in rows:
    out.append(f"| [ ] | #{r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` | {r[5]} | {r[6]} |")
open(f"{D}/CARRY-OVER-CHECKLIST.md", "w").write("\n".join(out) + "\n")
print(open(f"{D}/evidence-ab-checklist-stats.txt").read())
