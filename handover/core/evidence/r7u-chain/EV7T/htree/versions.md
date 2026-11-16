# versions.md

The versions that the files of this repository pin or require. No run result is stored here, and nothing here is a claim about what any machine ran.

## Runtime
| Item | Value | How read |
|---|---|---|
| Python the Windows lock file is made for | 3.13 | `--python-version 3.13` in the header of `requirements-dev-win.txt` |
| Python required | 3.12 or newer (`requires-python`); 3.12 is the lowest version the package allows. The `tests/` folder holds 92 test files. | pyproject.toml |
| SQLite library | the one that comes with the Python in use; no version is recorded. The desk's SQL uses `ON CONFLICT ... DO UPDATE` (in `src/lead_desk/desk.py`); the code does not check the SQLite version | `sqlite3.sqlite_version` prints it |
| Runtime dependencies | none (Python standard library only) | pyproject.toml |

## n8n (demo only)
No file of this repository records the n8n version or the Node.js version that the workflows in `n8n/` were built or run with, so none is stated. n8n is not part of this repository and not a dependency of the desk. The recipe is not claimed to work on any n8n version.

## Live model step (demo only)
| Item | Value |
|---|---|
| `anthropic-version` request header (`LIVE_API_VERSION`) sent to the AI service | 2026-10-21 |

The live step (the desk's call to the AI service, `--live-model` in `docs/real-services.md`) is tested only against the local demo server (`tests/test_real_check_dry.py`).

## GitHub Actions used by `.github/workflows/` (each pinned by its full commit SHA in the workflow file)
| Action | Version |
|---|---|
| `actions/checkout` | v7.0.1 |
| `actions/setup-python` | v7.1.0 |
| `github/codeql-action` (`init`, `analyze`) | v4.39.3 |
| `actions/cache` (used in `sonar.yml`) | v4.3.0 |
| `SonarSource/sonarqube-scan-action` (used in `sonar.yml`) | v8.4.0 |

The commit SHAs are in the workflow files, each with its version in a comment beside the pin; the rows above are read from those comments. Whether each tag resolves to the pinned commit, and whether the gitleaks 8.30.1 archive matches the checksum in `lint.yml`, is not checked by any file of this repository (the comment in `lint.yml` says where the checksum was copied from).

## Development tools (pinned with hashes, installed with `pip install --require-hashes`)
Direct pins live in `requirements-dev.in`. Two lock files, same versions: `requirements-dev.txt` (the authority: Linux x86_64; its header records `pip-compile` run with Python 3.12 and the command `pip-compile --allow-unsafe --generate-hashes --output-file=requirements-dev.txt --strip-extras requirements-dev.in`; the header records neither the Python patch version nor the pip-compile version, and the build tool is not itself pinned) and `requirements-dev-win.txt` (Windows, Python 3.13; made with `uv` (the header records this command but not the uv version): `uv pip compile requirements-dev.in --generate-hashes --python-version 3.13 --python-platform windows --no-strip-extras`). The only difference is `colorama` (a Windows-only transitive of pytest), which is in the Windows file and not in the Linux file. Each file is made for one operating system (the `--python-platform` setting in the Windows file's header; `colorama` only in the Windows file); installing either file on the other operating system was not tried.

| Package | Version | Used for |
|---|---|---|
| pytest | 9.2.0 | tests |
| ruff | 0.17.4 | lint and format; ruff rule groups E, F, W, I, S and PLR2004 |
| bandit | 1.9.4 | `bandit -ll -r src tools scripts -c pyproject.toml` (as in `.github/workflows/lint.yml`) |
| mypy | 2.4.1 | `mypy --platform linux` and `mypy --platform win32` (strict, `src/`, `tools/` and `scripts/hubspot_probe.py`; both as in `.github/workflows/lint.yml`) |
| iniconfig 2.3.1, pluggy 1.7.0, mypy-extensions 1.2.0, librt 0.16.0, ast-serialize 0.13.1, rich 15.0.0, markdown-it-py 4.2.0, mdurl 0.1.2, pyyaml 6.0.3 | as shown | transitive |
| packaging 26.3 | | transitive |
| pygments 2.21.0 | | transitive |
| colorama 0.4.6 | | transitive on Windows only; in `requirements-dev-win.txt`, not in the Linux lock |
| stevedore 5.9.1 | | transitive |
| typing-extensions 4.16.0 | | transitive |
| pathspec 1.1.1 | | transitive of mypy; used only as a development tool and not shipped |

### Browser tests (optional, a separate lock)
`requirements-browser.in` lists one direct pin: `playwright==1.63.0`. Two lock files made with `uv` (the files do not record the uv version; the comment in `requirements-coverage.in` names uv 0.11.32 for the coverage lock, and that the same version made these two was not checked), each with hashes and each held to the pins of the matching development lock (`-c`), so installing it after the development lock changes no development pin: `requirements-browser.txt` (`uv pip compile requirements-browser.in --generate-hashes --python-version 3.12 --python-platform linux --no-strip-extras --exclude-newer 2026-11-12 -c requirements-dev.txt -o requirements-browser.txt`) and `requirements-browser-win.txt` (the same with `--python-version 3.13 --python-platform windows`, `-c requirements-dev-win.txt` and `-o requirements-browser-win.txt`). `--exclude-newer` ignores any release uploaded after that date, so the same command should give the same lock later. Install: `pip install --require-hashes -r requirements-browser.txt` after `requirements-dev.txt`. The checks in `.github/workflows/lint.yml` do not install it (no browser job yet).

Side effect of the review-tool settings: `.codeant/configuration.json` lists both browser lock files (`requirements-browser.txt`, `requirements-browser-win.txt`) among the files its review bot skips, next to the two development locks, because their content is hash lines. So, going by that settings file, the bot's check of dependencies for known vulnerabilities no longer reads these two files; the bot itself was not run or checked here. The settings file does not skip `requirements-browser.in`, which names `playwright==1.63.0`, but that file does not name the packages that only the lock files list (greenlet and pyee; typing-extensions is also listed only in the lock files, which are skipped).

Secret-scan allowance for the browser lock files: the entry in `.gitleaks.toml` accepts a 64-character hash line only in a file named `requirements-browser.txt` or `requirements-browser-win.txt` at the repository root (`paths = ['''^requirements-browser(-win)?\.txt$''']`). The secret scan in `tests/test_hygiene.py` runs from the repository root, so the path is relative and a copy in a sub-folder is not allowed: a planted hash line in a file of that name inside a sub-folder is reported by `gitleaks`, and the second check, the pattern list minus `exceptions.txt`, which is also root-anchored, reports it as well (the test `test_exceptions_narrow` in `tests/test_hygiene.py` plants such a file in a sub-folder and expects it to be reported).

| Package | Version | Used for |
|---|---|---|
| playwright | 1.63.0 | drives the browser in the browser tests |
| greenlet 3.5.6, pyee 13.0.1 | | transitive of playwright |
| typing-extensions 4.16.0 | | transitive of pyee; the same pin as in the development lock |

Playwright's package also contains a bundled Node program (its driver) with its own third-party notices; those are not examined in this repository.

No licence scan result is stored in this repository, so no licence column is given for any package. To get one, install a lock file with `pip install --require-hashes` into a clean environment and run `pip-licenses --from=mixed` there.

## Not checked
- Windows restart on a fixed port: `SO_EXCLUSIVEADDRUSE` plus TIME_WAIT (the short wait after a connection closes; its length was not measured here) may make a restart bind fail, and the conflicting bind may raise `PermissionError` (WSAEACCES) instead of `EADDRINUSE`. The tests avoid it by using port 0 (the system picks a free port).
- The lock files were made with the hash option (`--generate-hashes` in the headers), which by the tools' documentation lists the files PyPI offered for each pinned version when the file was made; that was not re-checked here (no network). No result of a `pip install --require-hashes` of any lock file is stored in this repository. Not tested: other Linux architectures, the GitHub CI runner image.
- bandit rule B101 (it flags `assert`) on tests: tests are excluded from bandit, so it does not apply.
- gitleaks is a separate program (version and checksum pinned in `.github/workflows/lint.yml`), not part of the lock files. pre-commit and exiftool are not used.
