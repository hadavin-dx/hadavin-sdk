#!/usr/bin/env python3
"""Set the model of every EGM skill and agent to the studio routing table.

Upstream EGM files say `model: inherit`: the skill or agent then runs on whatever model the caller uses, so a session
started on Opus would run every reviewer on Opus. The studio routing (see handover/MODEL-ROUTING.md) is:
  Opus 5.5  : egm-brainstorm, egm-draft, egm-resolve (planning and negotiation skills)
  Sonnet 5.5: every other EGM skill (review, review-loop, drift-report, bootstrap) and every egm reviewer agent
Usage: python3 egm_model_patch.py [PLUGIN_ROOT ...]   (default: every EGM plugin folder found under ~/.claude/plugins)
It also removes the line `disable-model-invocation: true` from the skills: upstream sets it, which means only a person who
types the slash command can start a skill and the model is refused when it calls the Skill tool (this is why the cloud
session could not start egm-review-loop or egm-resolve). The studio rule is that EGM skills are called through the Skill
tool, so the flag is removed.
Run it once at the start of a session, before the first EGM call; it is idempotent. It edits only the `model:` line and that
flag in the frontmatter of skills/*/SKILL.md, agents/*.md, .claude-plugin/agents/*.md and .cursor-plugin/agents/*.md and prints every change.
"""
import re
import sys
from pathlib import Path

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
OPUS_SKILLS = {"egm-brainstorm", "egm-draft", "egm-resolve"}


def find_roots() -> list[Path]:
    base = Path.home() / ".claude" / "plugins"
    roots = {p.parent.parent.parent for p in base.rglob("skills/egm-brainstorm/SKILL.md")}
    return sorted(roots)


def wanted(path: Path) -> str:
    if path.name == "SKILL.md":
        return OPUS if path.parent.name in OPUS_SKILLS else SONNET
    return SONNET


def patch(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"(---\r?\n)(.*?)(\r?\n---)", text, re.S)
    if not m:
        return None
    front = m.group(2)
    want = wanted(path)
    if re.search(r"^model:.*$", front, re.M):
        new_front = re.sub(r"^model:.*$", f"model: {want}", front, count=1, flags=re.M)
    else:
        new_front = front + f"\nmodel: {want}"
    if path.name == "SKILL.md":
        new_front = re.sub(r"^disable-model-invocation:.*(\r?\n|$)", "", new_front, flags=re.M)
        new_front = new_front.rstrip("\r\n")
    if new_front == front:
        return None
    path.write_text(text[: m.start(2)] + new_front + text[m.end(2):], encoding="utf-8", newline="")
    return f"{path}: -> {want}"


def main() -> int:
    roots = [Path(a) for a in sys.argv[1:]] or find_roots()
    if not roots:
        print("no EGM plugin folder found; install the plugin first", file=sys.stderr)
        return 1
    changed = 0
    for root in roots:
        files = list(root.glob("skills/*/SKILL.md")) + list(root.glob("agents/*.md")) + list(root.glob(".claude-plugin/agents/*.md")) + list(root.glob(".cursor-plugin/agents/*.md"))
        for f in files:
            line = patch(f)
            if line:
                print(line)
                changed += 1
    print(f"done: {changed} file(s) changed in {len(roots)} plugin folder(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
