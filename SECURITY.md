# Security

Please report a suspected vulnerability privately through GitHub: the **Security** tab of this repository,
**Report a vulnerability**. If that button is not shown, open an issue titled "Security contact request" with no
details, and a private channel will be arranged. Do not post vulnerability details publicly.

Reports are answered within 5 working days.

## Stated limits of redaction (reviewed, not bugs)

Redaction is pattern based and treats the end of a value the way the redactor's own value pattern does. Two consequences are known and stated:

- A secret value that itself contains a plain (not encoded) space, `;`, `,` or `&` (for example `password="my secret phrase"`) is masked only up to that character in pass one: its tail is shown, because by the redactor's definition the value ended there. Put such a secret in quotes handled by the pattern, or do not hand it to a tool.
- A form-encoded `;` or `&` inside a value is ambiguous: `password%3Dab%3Bzq9` can be one secret or a key and a value followed by more text. The redactor decodes it, masks what its value pattern reaches, and keeps what pass one masked whole when the decoded view would mask less; it cannot know which reading the sender meant.

Control that does not depend on these limits: a tool is not handed a secret it does not need (least privilege).

## Hidden characters and escape sequences (pull request H)

Redaction reads text after taking out the control characters and terminal escape sequences a reader does not see, so a secret that a colour code cuts is masked like the uncut secret. This does not imitate a terminal (a backspace overstrike or a carriage-return overwrite is not played), so `AKIA` + `X` + backspace + the rest of a key is not read as the whole key. A key or value with a tab, form feed, line separator or line break inside it is masked only up to that character; a word glued in front of a cut value is not split off; look-alike letters and base64, hex or quoted-printable spellings of pattern-shaped values are not masked. A value that main removed only because it stood in the body of an escape string that never ends (`ESC ]` + text, with no end mark) is now kept as text and is masked only if the plain value would be masked. A text that needs more than the counted number of passes (`defaults.MAX_REDACT_PASSES`), that cannot be read within the time budget, or whose two readings of a cut escape sequence cannot be merged, is refused, not shown. The pinned test rows are in `tests/fixtures/prh_regressions.json` (`NOT_PROMISED` in `tests/test_prh_regressions.py` names each one and its reason).
