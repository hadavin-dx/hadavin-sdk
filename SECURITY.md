# Security

Please report a suspected vulnerability privately through GitHub: the **Security** tab of this repository,
**Report a vulnerability**. If that button is not shown, open an issue titled "Security contact request" with no
details, and a private channel will be arranged. Do not post vulnerability details publicly.

Reports are answered within 5 working days.

## Stated limits of redaction (reviewed, not bugs)

Redaction is pattern based and treats the end of a value the way the redactor's own value pattern does. Two consequences are known and stated:

- A secret value that itself contains a plain (not encoded) space, `;`, `,` or `&` (for example `password="my secret phrase"`) is masked only up to that character in pass one: its tail is shown, because by the redactor's definition the value ended there. Put such a secret in quotes handled by the pattern, or do not hand it to a tool.
- A form-encoded `;` or `&` inside a value is ambiguous: `password%3Dab%3Bzq9` can be one secret or a key and a value followed by more text. The redactor decodes it, masks what its value pattern reaches, and keeps what pass one masked whole when the decoded view would mask less; it cannot know which reading the sender meant.
- Base64. A value written only in base64 is masked whole as ENCODED by the redactor's decoded view, when it is standard or URL-safe, padded or not, UTF-8 or UTF-16, wrapped in lines of one length of 16 characters or more (any width), and up to three levels deep.
  - A wrapped block whose lines are all 40 characters or more is usually masked line by line as a high-entropy value already, and stays so. A blob on a line next to a line that is not base64 (a closing word, a hex digest) is read line by line, and without that line.
  - An ENCODED value is never stored or restored. A secret found inside it is also masked where it is written plainly elsewhere in the same run.
  - Not found: a blob glued to other base64 characters, split across fields or across lines with a prefix; a blob written between `<` and `>` that looks like a marker (all capitals, or ending in `_` and digits); base32; hex; lines wrapped under 16 characters.
  - The decoded view is made for what tools and people write; text shaped on purpose can pass it.
  - A text with more than 2,000 distinct decodable base64 values is refused, and a card with such a text is not posted. A document built to make the redactor's compound-value scan too long is refused as a whole.
  - A very long masked value (an ENCODED blob of tens of kilobytes) is held in memory by every check built from the run's map, about 0.5 KB per character.
- Host names.
  - A private host name (under `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `home.arpa`, or ending in `.internal` / `.local`, also with a hyphenated rest such as `.corp-prod`) is masked whole.
  - A single host label after `host`/`hostname` that ends in two digits or in a hyphen and a digit is masked, and so is every later standalone copy of it in the run. That includes a non-host word of that shape (`py311`) and a cross-compile triple. CPU and platform names (`x86_64`, `x64`, `arm64`, `win32`, the 32- and 64-bit names of riscv, mips, sparc, ia, loongarch, wasm, arm, aarch and ppc, and `s390`) are not masked; the list is closed.
  - A label with one trailing digit (`web1`) is not masked. A dotted name with no private suffix is not masked.
  - `.svc` short names, `.cluster.local` and AWS's own names are kept on purpose. A private name that goes on into `.svc.cluster.local` (`db01.corp.example.svc.cluster.local`) is kept whole, as before.
  - A Java package under a private suffix (`com.acme.corp.billing.Service`) is masked whole.
- A bare number with no label is not masked, by decision; the shapes that are masked are listed in the module docstring of `guard/redact.py`.

Control that does not depend on these limits: a tool is not handed a secret it does not need (least privilege).
