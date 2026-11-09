# L2e: recheck of the first campaign (run 1) with the new checker

Command, once per folder (each folder was COPIED first to a temporary place; the saved folders under /home/user/build/campaign were not touched):

    PYTHONPATH=src:. python -m live_l2.recheck <copy of the scenario folder> --json <file>

Exit codes: 0 all seven checks hold and no run fault; 1 a check or run fault failed; 3 checks hold but the data cannot show everything (RERUN).
The first campaign stored no bounds in summary.json, so every folder was judged with TODAY's catalogue bounds (the BOUNDS line says so) and the
expectations rebuilt from the events the run logged. 23 folders: the 20 scenarios and the three `rerun240-*` folders (run 1 re-runs with a longer drain wait).

| Folder | Exit | Checks that fail (offender count) | Run faults | What the old data cannot show (RERUN) |
|---|---|---|---|---|
| burst-10 | 0 | none | none | none |
| burst-1000 | 0 | none | none | none |
| burst-200 | 0 | none | none | none |
| catcher-down | 0 | none | none | none |
| catcher-drop-after-data | 0 | none | none | none |
| catcher-slow | 1 | 2 (94), 3 (1), 5 (93), 7 (1) | the desk never drained | catcher mode was `slow 3` against a 5 s send timeout |
| crash-A | 0 | none | none | none |
| crash-A2 | 0 | none | none | none |
| crash-B | 0 | none | none | none |
| crash-D1 | 0 | none | none | none |
| crash-D2 | 0 | none | none | none |
| dupmix-30pct | 1 | 5 (35) | none | no arrival lines: a second call after an answer cannot be told from a race |
| model-429 | 3 | none | none | no arrival lines: a second call after an answer cannot be told from a race |
| model-5xx | 3 | none | none | no arrival lines: a second call after an answer cannot be told from a race |
| model-flaps | 3 | none | none | no arrival lines: timeout calls may be undercounted; no arrival lines: a second call after an answer cannot be told from a race |
| model-malformed | 3 | none | none | no arrival lines: a second call after an answer cannot be told from a race |
| model-refusal | 3 | none | none | no arrival lines: a second call after an answer cannot be told from a race |
| model-slow | 1 | 2 (170), 3 (170), 5 (170), 7 (1) | the desk never drained | none |
| model-timeout | 1 | 2 (200), 5 (75), 7 (1) | the desk never drained | no arrival lines: timeout calls may be undercounted; no arrival lines: a second call after an answer cannot be told from a race |
| rate-20x60 | 0 | none | none | none |
| rerun240-catcher-slow | 1 | 2 (57), 3 (1), 5 (56), 7 (1) | the desk never drained | catcher mode was `slow 3` against a 5 s send timeout |
| rerun240-model-slow | 1 | 2 (132), 3 (132), 5 (132), 7 (1) | the desk never drained | none |
| rerun240-model-timeout | 1 | 2 (200), 5 (42), 7 (1) | the desk never drained | no arrival lines: timeout calls may be undercounted; no arrival lines: a second call after an answer cannot be told from a race |

## What this shows (read in this order)

1. **Six folders stay red, and they were red in run 1 too** (`model-slow`, `model-timeout`, `catcher-slow` and their three `rerun240-*` copies; `dupmix-30pct` is separate, below). In these the desk never drained: the drain marker is `null`, follow-ups stayed `pending`/`sending`, so checks 2, 7 (and 5 and 3 as a result: leads never asked, no `unknown` ever reached) fail. The old summary already says `checks_exit: 1` and `drain_seconds_after_load: null`. The new checker does not make these worse; it adds the evidence faults that follow from the undrained book. They are real: run 1 never proved these three scenarios, and no recheck can change that. A rerun with the fixed catcher mode (`catcher-slow` needs a catcher wait longer than the send timeout; the saved mode was `slow 3` against a 5 s timeout) is needed.
2. **`dupmix-30pct` (exit 1, check 5, 35 leads).** Under model mode `ok` the bound is ONE call per lead. The old log shows 879 calls for 840 leads: 31 leads were asked twice and 4 three times. Run 1 passed this with the old global bound 3. Whether the desk re-asked the model after it had an answer, or two copies of the same request raced and both asked before the label was stored, cannot be told from this log (it has no `arrival` lines, so the new `asked again after an answer` rule is deliberately NOT judged on it, and the folder carries a RERUN reason). The bound violation itself stands. This is a finding for the desk owner or a rerun with the new fake model, not something to explain away here.
3. **Five model scenarios exit 3** (`model-429`, `-5xx`, `-malformed`, `-refusal`, `-flaps`): every check holds with the saved data, but each lead was called up to 5 times and the log cannot say whether any call came after an answer (none could have: the model never answered). Rerun to know.
4. **Eleven folders exit 0**: the three bursts, the rate run, the five crash runs, `catcher-down`, `catcher-drop-after-data`. The new rules (sent leads have a finished CRM step, every message goes to the lead's own address, failed follow-ups have a reason, the intended request list, the evidence that the catcher was down or hung up) hold on the data. Caveat: the folders have no `intended_list` in the facts file, so check 1 compared by count and distinct ids only (the detail line says so); crash folders have no arrival lines, so a double model call after an answer was not judged (no lead had more than one call there).
5. **`catcher-down`**: 3 follow-ups ended `failed` (ceiling 160 derived from the 15 s outage at 10 per second); no message was recorded inside the down window; leads submitted in the healthy windows were all `sent`.

## Not checked

* The three `rerun240-*` folders have the same shape as their originals and the same verdicts.
* No folder was re-run (the brief forbids touching the live campaign); all verdicts are about the saved data.
* The bounds are today's catalogue, not the ones run 1 was judged by (run 1 used one global bound). A run from now on stores its own bounds.
