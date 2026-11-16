# BN-16 price pin (step run 2026-11-06, read from the vendor page by WebFetch)
Source URL for every row: https://platform.claude.com/docs/en/about-claude/pricing
Date read: 2026-11-06. The page shows no "last updated" date of its own; the read date is the date pinned.
USD per million tokens, exact decimals as printed (base rows, standard tier):
| model (as the page names it)              | input | output | cache read | 5m write | 1h write |
| Claude Opus 5.5                           | 4     | 20     | 0.20       | 5        | 8        |
| Claude Sonnet 5.5                         | 2     | 10     | 0.10       | 2.50     | 4        |
| Claude Haiku 5.5, prompt up to 100,000    | 0.10  | 0.50   | 0.01       | 0.125    | 0.20     |
| Claude Haiku 5.5, prompt over 100,000     | 0.50  | 2.50   | 0.05       | 0.625    | 1        |
Cross-check: matches the 2026-11-04 figures in the studio rule model-choice-and-cost-follow-bible (Haiku 0.10/0.50 and 0.50/2.50, Sonnet 2/10, Opus 4/20). litellm file not used.
Notes (honest): (1) The repo itself holds no price table: prices come from config, so this pin is evidence only and nothing was written into src. "Models we price" = the three the studio rules route to. (2) Haiku has two price bands by prompt size; one config Route holds one rate pair, so a Haiku route configured at 0.10/0.50 under-prices prompts over 100,000 tokens. P4a does not change this; it is a config choice the operator must make (use the upper band for a safe bound). (3) Cache-read and cache-write prices are listed but P4a refuses non-zero cache counts instead of pricing them.
