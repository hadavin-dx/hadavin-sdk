### .py files (ast.dump after stripping docstring statements; comments never appear in an AST)

| file | identical |
|---|---|
| `load_tools/catcher.py` | yes |
| `scripts/check_schema.py` | yes |
| `scripts/hubspot_probe.py` | yes |
| `src/lead_desk/constants.py` | yes |
| `src/lead_desk/db.py` | yes |
| `src/lead_desk/desk.py` | yes |
| `src/lead_desk/gate.py` | yes |
| `src/lead_desk/imap_count.py` | yes |
| `src/lead_desk/live_claude.py` | yes |
| `src/lead_desk/loader.py` | yes |
| `src/lead_desk/run_stats.py` | yes |
| `src/lead_desk/trace.py` | yes |
| `tests/test_input_edge_cases.py` | NO (expected: code-fix-v1 changes one assertion) |

### .yml files (yaml.safe_load before/after)

| file | equal |
|---|---|
| `.github/workflows/codeql.yml` | yes |
| `.github/workflows/lint.yml` | yes |
| `.github/workflows/semgrep.yml` | yes |
| `.github/workflows/sonar.yml` | yes |

other non-md files changed: ['scripts/start_all.ps1']
md files changed: 12
