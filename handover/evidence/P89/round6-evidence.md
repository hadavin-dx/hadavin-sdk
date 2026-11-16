Round 6 evidence, head 14879daf5c5bf53a26c4385dc7e54e68902a1f5a
Keyword+meta tests (3.12, 3.13) and the mutant tool were run as root AND as uid 65534 (nobody) via setpriv: logs r6-kw31*.log (root), r6-kwnb31*.log and r6-mutnb.log (nobody).
7432f67d915edb3da7c0532bdf39759da6ebb21b07e6f29d8e6c99714b91fcba  tools/mutation_runner.py
54d3c01f1ba01acf25674ec65834bf206aecd1fdca0d9fd535253f9473ad2950  tests/test_mutation_runner_keywords.py
d2959eb96112bae0fa492754b7ceaa813bd81070643c5617f2825ee2f90d32d3  tests/mutation_runner_mutants.py
832b819bd21c5a08c3e5c3f70689d7c40c12efc1593aad85948e822e756612f4  tests/test_mutation_runner_meta.py
4ce19db7e7a281744ecbb6ad4a80eb98b8d7e2426d11b2ef607144cf100cbfa1  CHANGELOG.md
b5f86f5c514e8992fcc3d5c3f2a3c3261cb8332c55d172083db2e4b8816e9d00  tests/fixtures/mutation_manifest.json
mutants root: 156 of 156 good; problems: []
mutants nobody: 156 of 156 good; problems: []
fail-before 58f7d56: 25 failed, 67 passed in 32.49s
