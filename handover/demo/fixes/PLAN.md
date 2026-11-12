# Lane 8b (v3, orders D11 and D12): PLAN (builder). Final tree: pr-3-tests 558d37f (rebased from b29bb1f). Nothing committed or pushed.
Patch: docs-and-deps.patch = the NEW design (browser lock with Playwright only, sidebar test reads pixels inside Chromium, docs). Records: docs-and-deps-v1-own-decoder.patch (lane 8), docs-and-deps-v2-pillow-draft.patch + PLAN-v2-pillow-draft.md (D10 Pillow draft, evidence only, not shipped).

## Failures and open items FIRST
1. Full run (evidence-b4): on b29bb1f + both lock files + Playwright 1.63.0 + chromium 1243 + node, no Pillow: 2462 passed, 3 skipped in 1021 s (2465 tests), exit 0, one serial process, load average 2.5 before / 4.3 after (shared machine). It was NOT repeated on 558d37f: 558d37f differs from b29bb1f in .gitleaks.toml only (+7 lines, the sonar allowlist; `git diff --stat b29bb1f 558d37f`), so tests/test_portal_lead_pages.py, docs/tests.md, requirements files and exceptions.txt are unchanged by it; on 558d37f I re-ran only hygiene + the two sidebar tests (11 passed, 1 skipped: gitleaks absent from PATH, evidence-b7), ruff check and format.
1b. D12 gitleaks: the lead's `[[allowlists]]` on 558d37f is broken (line target) and shows 1 finding with the real gitleaks 8.30.1 in baseline and with my patch (sonar-project.properties generic-api-key; not mine). My patch adds NO new finding: hash lines of the new locks allowed, a planted made-up 64-hex in docs/ and in a file named requirements-planted.txt still reported (evidence-b6). My allowlist lines use `regexTarget = "match"` (the existing style, no ^ on a line target) and the path regex `(^|[/\\])requirements-(dev|browser)(-win)?\.txt$`. The 10a fix patch applies on top of mine (git apply --check, evidence-b8) and the scan then says "no leaks found" (evidence-b6). To keep that so I added my exceptions.txt lines at line 9-10, not next to line 24 which 10a's hunk uses. My patch applies on 558d37f only (the .gitleaks.toml hunk has 558d37f context; `git apply --check` fails on b29bb1f for that hunk, expected).
2. The brief named requirements-semgrep.in / requirements-coverage files and a documented `--exclude-newer` pattern: THEY DO NOT EXIST in b29bb1f (grep). I followed the real pattern (requirements-dev.in + Linux py3.12 lock + Windows py3.13 lock) and added `--exclude-newer` myself.
3. Hygiene failed on my first try (new file names, a time stamp in the command, and the 64-hex hash lines were reported by `test_hygiene_scan_public`); fixed in exceptions.txt, .gitleaks.toml (2 regexes), .codeant/configuration.json; date written without time. Hygiene now 9 passed, 1 skipped (gitleaks absent). The real gitleaks was NOT run, so the .gitleaks.toml edit (same regex style as before) is untested by the tool.
4. I started two pytest processes by mistake for a few minutes (a first background run survived its launcher); killed both, then ran one. Nothing else left running (checked pgrep).
5. Not measured: Windows (lock compiled, never installed); `playwright install chromium` from scratch (chromium 1243 preinstalled in /opt/pw-browsers); gitleaks; mypy on win32 (only `--platform linux`).
6. CI has no browser job: lint.yml installs only requirements-dev.txt, so no workflow uses the new locks and the two sidebar tests run in no CI. Open for the lead: add a browser job.
7. Maintenance: Dependabot covers GitHub Actions only (docs/tests.md), so requirements-browser.* get NO update PRs. Whoever bumps Playwright re-runs the generation command (in each lock's header and in versions.md) AND must install the matching chromium build; a newer Playwright with only build 1243 makes ALL browser tests skip.
8. The lead's 2329/135 and its 2462 with 2 skipped are not reconciled (docs say so: inference only, Node-missing fits, unknown OS/gitleaks/Node). Reviewer M2/M3/N4-N7 applied to docs/tests.md (counts named by commit: 2349/116 on bee6fff4 and 43110e7; 43110e7 with Playwright = 2 failed 2460 passed 3 skipped, 2462 was a would-be; "differs by +1 passed, -2 skipped"; skip counts "by reported line"; 1254 verified from the playwright 1.65.1 wheel browsers.json; the "20 seconds" claim and "newest at the time" dropped; Node and Chromium build explained in plain words; "on purpose" removed).

## The test change: old vs new, side by side (tests/test_portal_lead_pages.py, test_the_sidebar_column_is_one_colour_to_the_page_bottom_at_1100[light|dark])
OLD (published):
    import io
    from PIL import Image
    ...
    height = page.evaluate("() => document.documentElement.scrollHeight")
    assert height > 900, height
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    above, below = img.getpixel((60, 880)), img.getpixel((60, height - 40))
    assert all(abs(a - b) <= 6 for a, b in zip(above, below, strict=True)), (above, below)
NEW:
    import base64
    ... (goto, wait, height, `assert height > 900` unchanged)
    shot = "data:image/png;base64," + base64.b64encode(page.screenshot(full_page=True)).decode()
    reader = page.context.new_page()            # blank page, same browser
    try: got = reader.evaluate("""async ([src, points]) => { img = new Image(); img.src = src; await img.decode();
            canvas 2D, default settings, same size as the image; drawImage; return {size, px: points.map(getImageData(x,y,1,1).data)} }""",
                               [shot, [[60, 880], [60, height - 40]]])
    finally: reader.close()
    assert got["size"][1] > height - 40, got["size"]                    # both points inside the screenshot (old: getpixel raised IndexError; still loud)
    above, below = got["px"]
    assert above[3] == below[3] == 255, (above, below)                  # NEW extra check: opaque
    assert all(abs(a - b) <= 6 for a, b in zip(above[:3], below[:3], strict=True)), (above, below)   # same tolerance 6, same points
Nothing weakened: same two sample points, same tolerance, same height>900 guard, light and dark parametrisation and _browse(width=1100, scheme) untouched; out-of-range stays loud (explicit size assert; getImageData itself would silently return zeros, which is why the assert is there); two checks added (size, alpha).
Why a blank page from page.context.new_page(), not the open portal page: the portal page may carry a content-security rule that refuses a data: image (not checked, avoided); the blank page has none, the data: URL is same-origin-clean so the canvas is not tainted (it ran without a SecurityError); the screenshot is decoded at its own pixel size, so the portal's viewport (1100) does not scale it. The reader page is closed in `finally`.
Points thought through: colour management: canvas 2D default (sRGB, no colour space conversion for an untagged PNG); PNG from Chromium is RGB opaque (Pillow said mode RGB, size 1100x1436). Premultiplied alpha: irrelevant at alpha 255 (asserted). data: URL size: a 1100x1436 screenshot worked; Chromium data URLs up to 2 MB or more are fine in Chromium; a much taller page was not tried. Decode is async: `await img.decode()`.
Cross-check (evidence-b3, Pillow in a THROWAWAY venv /tmp/work/pilvenv, not shipped, not in any lock): same screenshot, same two points: Pillow light (246,244,254) both, dark (16,15,32) both; in-browser light [246,244,254,255] both, dark [16,15,32,255] both: identical.
Mutation (evidence-b2): tolerance made impossible (<= -1): both tests fail printing the real colours, light ([246,244,254,255],[246,244,254,255]) and dark ([16,15,32,255],[16,15,32,255]); restored (cmp with the good copy OK). Not done: reverting the sidebar CSS.

## Lock design (D11: Playwright only, NO Pillow anywhere)
requirements-browser.in: `playwright==1.63.0` only. Generated with uv 0.11.32 (/root/.local/bin/uv) on 2026-11-12:
  uv pip compile requirements-browser.in --generate-hashes --python-version 3.12 --python-platform linux --no-strip-extras --exclude-newer 2026-11-12 -c requirements-dev.txt -o requirements-browser.txt
  uv pip compile requirements-browser.in --generate-hashes --python-version 3.13 --python-platform windows --no-strip-extras --exclude-newer 2026-11-12 -c requirements-dev-win.txt -o requirements-browser-win.txt
Two files, not --universal: the repo already ships one lock per OS and Python version, so a stranger already picks by OS. --exclude-newer (my choice; the repo has none): ignores releases after that date so the command reproduces; the date is the generation day. `-c <dev lock>`: shared packages held to the dev pins.
Adds exactly (both files): playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1, typing-extensions 4.16.0 (already in the dev locks at the same pin: nothing changes). Fresh venv freeze diff: greenlet, playwright, pyee added; `pip list | grep -ic pillow` = 0; pip check clean (evidence-b1). Lint locks untouched: git diff --stat requirements-dev.txt requirements-dev-win.txt requirements-dev.in is empty (evidence-b5). Licences (metadata, evidence-b2 of the v2 draft; Pillow no longer involved): playwright Apache-2.0, greenlet MIT AND PSF-2.0, pyee MIT (classifier), typing-extensions PSF-2.0 (listed in versions.md).
Other files: exceptions.txt, .gitleaks.toml, .codeant/configuration.json (hash-line and file-name exceptions, see 3), versions.md (browser section), contract.md (line 71 sentence + the exit-4 drift fix), docs/portal.md (drift fix), docs/tests.md.
Considered, not chosen (earlier): own PNG decoder (v1, rejected D10), Pillow lock (D10, replaced by D11).

## What a stranger now does
python3.12 -m venv .venv; pip install --require-hashes -r requirements-dev.txt; pip install --require-hashes -r requirements-browser.txt; playwright install chromium (build 1243 for Playwright 1.63.0); PLAYWRIGHT_BROWSERS_PATH if not default; node on PATH; python -m pytest -q -rs. No Pillow.
