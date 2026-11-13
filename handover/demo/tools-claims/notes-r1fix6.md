# notes-r1fix6 (builder b6): one word "the author"
Replaced (file:line | old | new):
- README.md:162 | the licence holder's own use | the author's own use
- README.md:173 | the licence holder's written permission | the author's written permission
- docs/n8n-recipe.md:8 | the licence holder's written permission (the licence holder is the person ...) | the author's written permission (the author is the person ...)  [existing parenthetical kept, no new definition line]
- docs/tests.md:30 | once their owner has switched them on | once the author has switched them on
- docs/tests.md:38 | the repository owner agreed to use them here | the author agreed to use them here
- docs/tests.md:46 | The repository owner is meant to approve | The author is meant to approve
- docs/tests.md:48 | the repository owner is meant to check | the author is meant to check
- docs/why-this-code.md:24 | the licence holder's own use; the licence holder is the person | the author's own use; the author is the person
- docs/why-this-code.md:28 | the licence holder's written permission | the author's written permission
- .github/workflows/semgrep.yml:3 | the repository owner agreed to use them here | the author agreed to use them here
- .github/workflows/sonar.yml:4 | (owner-created; | (created by the author;
- .github/workflows/sonar.yml:12 | an open owner decision | an open decision for the author
- tools/scrub_n8n_export.py:40 | the licence holder's own use | the author's own use
- tests/test_portal_wording_and_masking.py:317 | # -- owner decision 2026-11-12: | # -- the author's decision 2026-11-12:
Not found in SECURITY.md, versions.md, load_tools/README.md (no matching words; SECURITY.md already says "the author").

Left, with reason:
- LICENSE lines 2,8,11,14 "the licence holder": legal text, not in the brief's file list. Lead decides.
- requirements-semgrep.in:12 "the repository owner": file not in the list (not md/yml/py). Lead decides.
- .coderabbit.yaml:3 "the repository maintainer": config file not in the list. Lead decides.
- tools/scrub_n8n_export.py:4 "project owner": a field name of n8n exports, not the person.
- README.md:12 "business owner": the reader of the demo. README.md:169 "names of their owners": trademark owners.
- docs/n8n-recipe.md:10,18 "n8n's own owner account": n8n role, as ordered.
- docs/settings.md:72 "is the owner's responsibility": the person who runs the desk with a real relay, not the author.
- docs/hubspot-probe.md, limits.md, settings.md, contract.md, README.md:126,130, src/, tests/, scripts/: "owner" = lead owner / CRM owner / HubSpot owner record, or "ownership token": product feature, code identifiers.
- contract.md:295 "the owner's token": claim ownership token, not a person.
- tests/*.py "owner" in test names and comments (lock owner, claim owner, lead owner): not the person.
