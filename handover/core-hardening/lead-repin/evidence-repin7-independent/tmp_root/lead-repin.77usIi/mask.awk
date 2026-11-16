# mask.awk: second masking stage.  -v CUT=240  cut lines longer than CUT characters and say so (0 = never cut).
# What it hides that the sed stage cannot know by name:
#  A  opaque strings: any run of 24 or more letters, digits and + / _ - that holds a letter and a digit
#     (base64, hex, tokens), unless it is a plain lowercase snake_case or kebab-case name, a CamelCase
#     name, or a git or file checksum line this script prints itself. A UUID is hidden.
#  B  mixed words: 12 or more letters and digits in a row with an upper case letter, a lower case letter
#     and a digit that are not a CamelCase name (Vq7Lm2Xp9Rt4 style) are hidden anywhere, also in prose.
#  C  secret-named JSON / YAML containers:  "api_keys": [ ... ]  and  "credentials": { ... }  are hidden up
#     to the matching closing bracket, on the same line or over following lines (at most 100 lines).
#  D  pretty-printed pairs:  "name": "X_TOKEN"  on one line and  "value": "..."  on a nearby line (before
#     or after, same object) hide the value;  - name: API_TOKEN / value: abc  likewise.
#  E  control byte 0x01 (a mark of the sed stage) is removed.
function isid_camel(t,   tmp, n, g, i) {
  if (t !~ /[A-Z]/) return 0
  tmp = t; gsub(/[0-9]+/, " ", tmp)
  n = split(tmp, g, " ")
  for (i = 1; i <= n; i++) if (g[i] !~ /^[a-z]*([A-Z][a-z][a-z]+)*$/) return 0
  return 1
}
function is_uuid(t) {
  return (length(t) == 36 && t ~ /^[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+$/)
}
function snake_name(t,   n, p, i, d) {
  if (t ~ /[A-Z+\/]/ || t !~ /[_-]/) return 0
  n = split(t, p, /[_-]/); d = 0
  for (i = 1; i <= n; i++) { if (length(p[i]) > 14) return 0; if (p[i] ~ /[0-9]/) d++ }
  return (d <= 2)
}
# blob: 1 = hide, 0 = keep, -1 = split at slashes and judge the pieces
function blob(tok,   n, c) {
  n = length(tok)
  if (n < 16) return 0
  if (tok !~ /[0-9]/ || tok !~ /[A-Za-z]/) return 0
  if (n < 24) return (tok ~ /^[0-9a-fA-F]+$/) ? 1 : 0     # 16 to 23 characters: hidden only when all hex (hex keys, short hashes of keys)
  if (tok ~ /\//) {
    c = substr(tok, 1, 1)
    if (c == "/" || c == "." || c == "~") return -1
    if (tok ~ /[A-Z]/ && tok ~ /[a-z]/) return 1     # v6: from 24 characters (v5: 32): a mixed-case secret with slashes is hidden
    return -1
  }
  if (tok ~ /\./ && length(tok) >= 24 && tok ~ /[A-Z]/ && tok ~ /[a-z]/) return dotted_secret(tok)   # every piece a plain name: kept
  if (is_uuid(tok)) return 1
  if (snake_name(tok)) return 0
  if (tok !~ /[-_+]/ && isid_camel(tok)) return 0
  return 1
}
# dotted_secret: a token with dots (a.b.c, 24 or more characters, upper and lower case and a digit) is hidden whole when
# one of its pieces is not a plain name (plain = lower case word, CamelCase name, digits, 3 characters or fewer)
function dotted_secret(tok,   n, p, i, x) {
  if (length(tok) < 24 || tok !~ /[A-Z]/ || tok !~ /[a-z]/ || tok !~ /[0-9]/) return 0
  n = split(tok, p, ".")
  for (i = 1; i <= n; i++) {
    x = p[i]
    if (length(x) <= 3 || x ~ /^[0-9]+$/ || x ~ /^[a-z0-9_-]+$/) continue
    if (isid_camel(x) || x ~ /^[A-Z]?[a-z]+([A-Z][a-z]+)*[0-9]*$/) continue
    return 1
  }
  return 0
}
function shape(tok,   out, st, ln, r) {
  out = ""
  while (match(tok, /[A-Za-z0-9]+/)) {
    st = RSTART; ln = RLENGTH; r = substr(tok, st, ln)
    out = out substr(tok, 1, st - 1)
    if (ln >= 12 && r ~ /[A-Z]/ && r ~ /[a-z]/ && r ~ /[0-9]/ && !isid_camel(r)) out = out "<masked-token>"; else out = out r
    tok = substr(tok, st + ln)
  }
  return out tok
}
function piece(tok,   r, n, parts, i, o) {
  r = blob(tok)
  if (r == 1) return "<masked-blob>"
  if (r == -1) {
    n = split(tok, parts, "/"); o = ""
    for (i = 1; i <= n; i++) o = o (i > 1 ? "/" : "") piece(parts[i])
    return o
  }
  if (tok ~ /\./ && tok !~ /\//) {
    n = split(tok, parts, "."); o = ""
    for (i = 1; i <= n; i++) o = o (i > 1 ? "." : "") piece_nodot(parts[i])
    return o
  }
  return shape(tok)
}
function piece_nodot(tok,   r) {
  r = blob(tok)
  if (r == 1) return "<masked-blob>"
  return shape(tok)
}
function genmask(s,   out, st, ln, tok, tail) {
  out = ""
  while (match(s, /[A-Za-z0-9+\/_.-]+/)) {
    st = RSTART; ln = RLENGTH; tok = substr(s, st, ln)
    tail = ""
    while (length(tok) > 1 && substr(tok, length(tok), 1) == ".") { tail = tail "."; tok = substr(tok, 1, length(tok) - 1) }
    out = out substr(s, 1, st - 1) piece(tok) tail
    s = substr(s, st + ln)
  }
  return out s
}
# camel_split: put a space before each upper case letter that follows a lower case letter or a digit (accessToken -> access Token)
function camel_split(k,   i, n, c, p, o) {
  o = ""; n = length(k); p = ""
  for (i = 1; i <= n; i++) {
    c = substr(k, i, 1)
    if (c ~ /[A-Z]/ && p ~ /[a-z0-9]/) o = o " "
    o = o c; p = c
  }
  return o
}
# secret_name: ONE general rule. A name is secret when a STRONG word (secret, password, passwd, passphrase, credential,
# token, apikey) is anywhere in it, or it holds a WEAK whole word (key, pass, pat, auth, cookie, session, signature, hmac,
# dsn, webhook, salt, otp, cert, ...) alone or followed by value / string / data / text / hash / bytes / material, or a
# word ends in key, token, secret, password, pwd or credential. Token counters (max_tokens ...) and tokenizer are not secret.
function secret_name(k,   n, w, i, x, joined) {
  k = camel_split(k)
  k = tolower(k)
  gsub(/0/, "o", k)    # passw0rd, s3cret style spellings: a zero is read as the letter o
  gsub(/[^a-z0-9]+/, " ", k)
  n = split(k, w, " ")
  joined = ""
  for (i = 1; i <= n; i++) {
    x = w[i]
    if (x ~ /^(max|num|total|prompt|completion|input|output|cached|reserved)tokens$/) continue
    if (x == "tokens" && i > 1 && w[i - 1] ~ /^(max|num|n|total|prompt|completion|input|output|cached|reserved|cache)$/) continue
    if (x ~ /^tokeniz|^tokenis/) continue
    joined = joined x
    if (x in SW) return 1
    if (x ~ /^(db|root|admin|user|mysql|pg|redis|master|ssh|smtp|mail|ldap|sql|wifi|wpa|sys|login)(pass|pw|pwd)$/) return 1
    if (x ~ /(key|keys|token|tokens|secret|secrets|password|passwords|passwd|passwds|pwd|credential|credentials)$/) return 1
    if (x ~ /^(key|keys|pass|pwd|pw|pat|auth|cookie|cookies|session|sessions|signature|hmac|dsn|webhook|salt|otp|cert|certs)(value|string|data|text|hash|bytes|material|id|url|uri|name|code|list|file|path|ring|store)$/) return 1
  }
  if (joined ~ /(secret|passw(or)?d|passphrase|credential|token|apikey|requirepass|masterauth|jsessionid|phpsessid)/) return 1
  return 0
}
# find the bracket that closes a container; CD/CQ keep the depth and quote when the line ends first
function find_close(s, i, depth, inq,   c, n) {
  n = length(s)
  for (; i <= n; i++) {
    c = substr(s, i, 1)
    if (inq != "") {
      if (c == "\\") { i++; continue }
      if (c == inq) inq = ""
      continue
    }
    if (c == "\"" || c == "'") { inq = c; continue }
    if (c == "[" || c == "{") depth++
    else if (c == "]" || c == "}") { depth--; if (depth == 0) { CD = 0; CQ = ""; return i } }
  }
  CD = depth; CQ = inq
  return 0
}
function hide_containers(s,   out, key, kk, open, j, st, ln) {
  out = ""
  if (CD > 0) {
    # a secret container that is still open: hide every line until it closes (or a "--" separator or the end of the
    # input). It never prints the rest raw, however many lines it takes (fail closed).
    j = find_close(s, 1, CD, CQ)
    if (j == 0) return "<masked>"
    return "<masked>" substr(s, j)
  }
  while (match(s, /(["'][^"']*["']|[A-Za-z0-9_.-]+)[ \t]*:[ \t]*[[{]/)) {
    st = RSTART; ln = RLENGTH
    key = substr(s, st, ln)
    sub(/[ \t]*:[ \t]*[[{]$/, "", key)
    kk = key; gsub(/["']/, "", kk)
    open = st + ln - 1
    out = out substr(s, 1, open)
    if (secret_name(kk)) {
      j = find_close(s, open + 1, 1, "")
      out = out "<masked>"
      if (j == 0) return out
      s = substr(s, j)
    } else {
      s = substr(s, open + 1)
    }
  }
  return out s
}
function is_nameline(b,   t, v) {
  t = tolower(b)
  if (t !~ /^[ \t]*(- +)?[{,]?[ \t]*["']?(name|key|var|variable|env|envvar|header|field)["']?[ \t]*:/) return 0
  v = b; sub(/^[^:]*:/, "", v); sub(/^[ \t"']+/, "", v); sub(/[]}, \t"']+$/, "", v)
  if (v == "") return 0
  if (v == "<masked>") return 1
  if (v ~ /[^A-Za-z0-9_. -]/) return 0
  return secret_name(v)
}
function is_valueline(b) {
  return (tolower(b) ~ /^[ \t]*(- +)?[{,]?[ \t]*["']?(value|val|secret|content|data|string|text)["']?[ \t]*:/)
}
function mask_after_colon(b,   p, head, rest, c, q, i, n, ch, j) {
  p = index(b, ":")
  head = substr(b, 1, p); rest = substr(b, p + 1)
  sub(/^[ \t]*/, "", rest)
  c = substr(rest, 1, 1)
  if (c == "[" || c == "{") {
    j = find_close(rest, 2, 1, "")
    if (j == 0) return head " <masked>"
    return head " <masked>" substr(rest, j + 1)
  }
  if (c == "\"" || c == "'") {
    q = c; n = length(rest)
    for (i = 2; i <= n; i++) { ch = substr(rest, i, 1); if (ch == "\\") { i++; continue }; if (ch == q) break }
    return head " <masked>" substr(rest, i + 1)
  }
  match(rest, /^[^]},]*/)
  return head " <masked>" substr(rest, RLENGTH + 1)
}
# yaml_continue: a line that names a secret as a YAML key keeps hiding the lines under it that are indented deeper
# (a multi-line quoted or plain value, or a block value whose header the sed stage did not see)
function indent_of(b,   t) { t = b; sub(/^[ \t]*/, "", t); return length(b) - length(t) }
function yaml_continue(b,   t, ind, nm) {
  if (b ~ /^[ \t]*$/) return b
  ind = indent_of(b)
  if (YIND >= 0) {
    if (ind > YIND) return "<masked>"
    YIND = -1
  }
  t = b
  while (match(t, /^[ \t]*- +/)) t = substr(t, RLENGTH + 1)
  if (match(t, /^[ \t]*["']?[A-Za-z0-9_.-]+["']?[ \t]*:/)) {
    nm = substr(t, 1, RLENGTH)
    sub(/^[ \t]*["']?/, "", nm); sub(/["']?[ \t]*:$/, "", nm)
    if (secret_name(nm)) YIND = length(b) - length(t) + indent_of(t)
  }
  return b
}

# ---------------------------------------------------------------- pre-stage (-v MODE=pre), runs BEFORE the sed stage
#  P1  length guard: a line longer than MAXL characters is cut to MAXL before the sed stage sees it (bounded time); the
#      true length is added as  \005 LENGTH \005  at the end, and a line is appended to the file CF (a count for the summary).
#  P2  a name that holds a byte outside plain ASCII (a zero-width space inside  pass<ZWSP>word, a look-alike letter, a
#      non-English name) followed by  =  or  :  is renamed NONASCII_NAME_SECRET, so the sed stage hides its value (fail closed).
#  P3  a secret-named assignment that opens a bracket it does not close on the line  NAME = (  [  {  $(  , or that ends in a
#      backslash: every following line is hidden until the brackets close (or the backslash chain ends, or a "--" separator, or
#      the end of the input). It never prints the rest raw, however many lines it takes (fail closed).
function ml_scan(s,   i, n, c, pc) {
  n = length(s)
  for (i = 1; i <= n; i++) {
    c = substr(s, i, 1)
    if (ML_Q != "") { if (c == "\\") { i++; continue } ; if (c == ML_Q) ML_Q = ""; continue }
    if (c == "\"" || c == "'") { ML_Q = c; continue }
    if (c == "#") { pc = (i > 1) ? substr(s, i - 1, 1) : " "; if (pc ~ /[ \t]/) break; continue }
    if (c == "(" || c == "[" || c == "{") ML_D++
    else if (c == ")" || c == "]" || c == "}") { ML_D--; if (ML_D <= 0) { ML_D = 0; ML_Q = ""; return } }
  }
}
function nonascii_names(s,   out, st, ln, m) {
  out = ""
  while (match(s, /[A-Za-z0-9_.\200-\377-]*[\200-\377][A-Za-z0-9_.\200-\377-]*["' \t]*[=:]/)) {
    st = RSTART; ln = RLENGTH; m = substr(s, st, ln)
    match(m, /["' \t]*[=:]$/)
    out = out substr(s, 1, st - 1) "NONASCII_NAME_SECRET" substr(m, RSTART)
    s = substr(s, st + ln)
  }
  return out s
}
function ml_start(b,   m, nm, rest, sec, t, tk) {
  sec = 0; rest = b
  if (match(b, /^[ \t]*((export|set|local|declare|readonly|var|let|const)[ \t]+(-[A-Za-z]+[ \t]+)?)?((self|this)\.)?["']?[]A-Za-z0-9_.[-]+["']?\]?[ \t]*(\+?=|:=)[ \t]*/)) {
    m = substr(b, 1, RLENGTH); rest = substr(b, RLENGTH + 1)
    nm = m
    sub(/[ \t]*(\+?=|:=)[ \t]*$/, "", nm)
    sub(/^[ \t]*((export|set|local|declare|readonly|var|let|const)[ \t]+(-[A-Za-z]+[ \t]+)?)?((self|this)\.)?/, "", nm)
    gsub(/["'\]]/, "", nm)
    sec = secret_name(nm)
  }
  if (sec && rest ~ /\\[ \t]*$/) { MLBS = 1; return }
  ML_D = 0; ML_Q = ""
  ml_scan(b)
  if (ML_D <= 0) { ML_D = 0; ML_Q = ""; return }
  if (!sec) {
    # the line opens a bracket it does not close: it is hidden onward when ANY name before an = or : on it is a secret name
    t = b
    while (match(t, /[A-Za-z0-9_.-]+["' \t]*[=:]/)) {
      tk = substr(t, RSTART, RLENGTH); sub(/["' \t]*[=:]$/, "", tk)
      rest = substr(t, RSTART + RLENGTH)
      # NAME: [ or NAME: {  is a container the awk stage already tracks to its closing bracket: leave it to that stage
      if (secret_name(tk) && !(substr(t, RSTART + RLENGTH - 1, 1) == ":" && rest ~ /^[ \t]*[[{]/)) { sec = 1; break }
      t = rest
    }
  }
  if (!sec) { ML_D = 0; ML_Q = "" }
}
function pre_line(   t, pfx, body, hid) {
  PRE_N++
  n0 = length($0)
  t = $0
  if (n0 > MAXL) { t = substr(t, 1, MAXL); if (CF != "") { print n0 >> CF; close(CF) } }
  pfx = ""; body = t
  if (match(t, /^(([^:]+[:-])?[0-9]+[-:])/)) { pfx = substr(t, 1, RLENGTH); body = substr(t, RLENGTH + 1) }
  if (body == "--") { ML_D = 0; ML_Q = ""; MLBS = 0 }
  hid = 0
  if (MLBS) { MLBS = (body ~ /\\[ \t]*$/); hid = 1 }
  else if (ML_D > 0) { ml_scan(body); hid = 1 }
  if (hid) body = "<masked>"
  else {
    if (body ~ /[\200-\377]/) body = nonascii_names(body)
    ml_start(body)
  }
  t = pfx body
  if (n0 > MAXL) t = t "\005" n0 "\005"
  print t
}
function emit(k,   o, n) {
  o = PFXS[k] BODYS[k]
  n = LEN[k]
  if (CUT > 0 && (length(o) > CUT || n > WIN)) {
    if (n <= WIN) n = length(o)
    if (ATL[k]) n = "at least " n
    o = substr(o, 1, CUT) " ...[CUT: this line has " n " characters; the rest is not shown]"
  }
  print o
}
BEGIN {
  nsw = split("key keys token tokens secret secrets password passwords passwd passwds passphrase passphrases pass pwd pw pws psw pswd pat credential credentials authorization auth bearer private apikey apikeys cookie cookies session sessions signature signatures hmac dsn webhook webhooks salt otp cert certs certificate certificates", sw, " ")
  for (i = 1; i <= nsw; i++) SW[sw[i]] = 1
  WIN = (CUT > 0) ? CUT + 360 : 100000
  head = 1; tail = 0; pend = 0; CD = 0; CQ = ""; YIND = -1
  ML_D = 0; ML_Q = ""; MLBS = 0
}
MODE == "pre" { pre_line(); next }
{
  line = $0
  gsub(/\001/, "", line)
  nmark = 0
  if (match(line, /\005[0-9]+\005$/)) { nmark = substr(line, RSTART + 1, RLENGTH - 2) + 0; line = substr(line, 1, RSTART - 1) }
  n0 = length(line); atl = 0
  if (nmark > n0) n0 = nmark
  else if (MAXL > 0 && n0 >= MAXL) atl = 1
  if (n0 > WIN) line = substr(line, 1, WIN)
  pfx = ""; body = line
  if (match(line, /^(([^:]+[:-])?[0-9]+[-:])/)) {
    pfx = substr(line, 1, RLENGTH); body = substr(line, RLENGTH + 1)
    if (pfx !~ /^[0-9]+[-:]$/) pfx = genmask(pfx)   # a long prefix may have swallowed text: it is masked too (path pieces stay readable)
  }
  keep = 0
  # a checksum line that THIS script printed itself (R00) stays readable: it must equal, character for character, a line
  # the script wrote to the file OKF. A line that only LOOKS like a checksum line (a hex string and two spaces, from a
  # searched file) is not in that file and is masked like any other text.
  if (OKF != "" && pfx == "" && (body ~ /^[0-9a-f]+  / || body ~ /^HEAD: [0-9a-f]+$/)) {
    while ((getline okl < OKF) > 0) if (okl == body) { keep = 1; break }
    close(OKF)
  }
  if (body == "--") { CD = 0; CQ = ""; YIND = -1 }
  if (!keep) {
    body = yaml_continue(body)
    body = hide_containers(body)
    namel = is_nameline(body)
    if (pend > 0) {
      if (is_valueline(body)) { body = mask_after_colon(body); pend = 0 } else pend--
    }
    if (namel) {
      pend = 3
      for (k = tail; k >= head && k >= tail - 2; k--) {
        if (is_valueline(BODYS[k])) { BODYS[k] = mask_after_colon(BODYS[k]); break }
        if (BODYS[k] ~ /[{}]/) break
      }
    }
    body = genmask(body)
  }
  tail++; PFXS[tail] = pfx; BODYS[tail] = body; LEN[tail] = n0; ATL[tail] = atl
  while (tail - head >= 3) { emit(head); delete PFXS[head]; delete BODYS[head]; delete LEN[head]; delete ATL[head]; head++ }
}
END {
  if (MODE == "pre") exit
  while (head <= tail) { emit(head); delete PFXS[head]; delete BODYS[head]; delete LEN[head]; delete ATL[head]; head++ }
}
