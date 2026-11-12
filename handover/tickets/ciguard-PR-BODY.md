Branches named `wip/cloud-*` are handover lane refs. They carry the same handover notes as `core/cloud-handover` and never merge into main. The "Stale gitleaks ignore entries" step in the security job listed 611 to 681 of those notes as if they were stray files, so every pull request failed. The step now treats `wip/cloud-*` like `core/cloud-handover` (history range and the "branch contains this commit" check).

The guard still protects every other branch: a branch with any other name that carries a file under `handover/(evidence|reviews|tickets)/` still fails. A new second check reads the history of the checked-out head with nothing subtracted, so a pull request built on lane commits cannot hide them behind a lane ref.

New tests run the real step text from `ci.yml` in throwaway git repositories (lane branch passes, `core/other` and look-alike names fail, head built on a lane commit fails). Run against the old `ci.yml`, 6 of them fail.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac
