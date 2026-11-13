# out-g1: public/private and GitHub-address lines (read-only, tree /tmp/review-tree)
Method: grep -nEi for public|private|github|clone|visib|fork|download|publish across README.md, SECURITY.md, versions.md, contract.md, docs/*.md, .github/workflows/*.yml, then read each hit. Nothing edited.
No file names this repo's own GitHub address (no owner/repo string, no github.com/<owner>/<repo>); a grep for such a URL found none.

| file:line | exact words | kind |
|---|---|---|
| README.md:49 | "On this repository's GitHub page press the green Code button and copy the address it shows." | clone-from-GitHub instruction (address not named; reader finds it on GitHub; assumes the page is visible to them) |
| README.md:50 | "Run `git clone <that address>`, then `cd` into the new folder." | clone instruction |
| README.md:130 | "The tests need a git clone (some tests read the list of tracked files with git)." | clone requirement |
| README.md:161 | "You may view the code, download it, run it on your own computer for evaluation and testing, and fork it on GitHub (to the extent GitHub's Terms of Service give that right)" | implies viewable and forkable (public) |
| README.md:161 | "through the GitHub profile of the organisation that publishes this repository" | implies published on GitHub (no address given) |
| SECURITY.md:9-10 | "use GitHub's private vulnerability reporting: the "Report a vulnerability" button on the Security tab of this repository, if that button is shown." | GitHub feature on this repo (works only if enabled; hedged) |
| SECURITY.md:11 | "Please do not describe the problem in a public place first." | generic public-place wording, not a claim about the repo |
| SECURITY.md:32 | "they cannot take back a secret that was already pushed to a public place" | generic, not a claim about the repo |
| docs/tests.md:34 | "checkout reads this repository from GitHub" | says repo is hosted on GitHub (no address) |
| docs/tests.md:38 | "The job log of a public repository prints the rule ids and rule messages of every finding, so anyone can read them" | public/private, conditional ("a public repository"), does not say whether this one is |
| .github/workflows/semgrep.yml:3-4 | "The job log of a public repository is public: it prints rule ids and messages (docs/tests.md, "Semgrep")." | same, conditional, comment |
| .github/workflows/sonar.yml:10-11 | "a pull request from a fork or from Dependabot never runs this job" (also line 31 comment "A pull request from a fork ... gets no repository secret") | fork handling; implies forks may exist, not a public/private claim |
| .github/workflows/lint.yml:40 | `https://github.com/gitleaks/gitleaks/releases/download/...` | GitHub address of ANOTHER project (gitleaks), not this repo |

Not hits (checked): contract.md and versions.md have no line saying public/private or telling readers to clone; their "private" hits are code words (private method, private memory book, private-app token) and docs/hubspot-probe.md, docs/limits.md, docs/real-services.md "private" are the same. README.md:51 "private Python folder" is a virtual environment. docs/settings.md:101 "public address" is the CRM provider's. docs/tests.md:34 "public Semgrep registry" is Semgrep's.
Not checked: whether the repo is actually public or private on GitHub (no network used); files outside the listed set (LICENSE, tests, src, scripts, n8n, .coderabbit.yaml, .github/dependabot.yml).
Bible R-numbers: not consulted (bible not present in this run; read-only grep task).
