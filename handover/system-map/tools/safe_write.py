"""Refuse to overwrite a hand-edited generated file (R460 B1). The sha of every file this tool wrote is kept in
hand-kept/.generated-hashes.json; a file whose sha differs, or that has no stored sha, is not overwritten unless force.
The registry is written atomically; a name that leaves the base folder is rejected."""
import hashlib, json, os

REG = os.path.join("hand-kept", ".generated-hashes.json")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _path(base, name):
    root = os.path.realpath(base)
    path = os.path.realpath(os.path.join(root, name))
    if os.path.commonpath([root, path]) != root or path == os.path.realpath(os.path.join(root, REG)):
        raise ValueError("safe_write: name leaves the base folder or targets the registry: %r" % name)
    return path


def _load(base):
    reg = os.path.join(base, REG)
    if not os.path.exists(reg):
        return {}
    try:
        with open(reg, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise ValueError("safe_write: %s is damaged (%s); delete it and re-run with --force" % (reg, e))


def refused(base, name, force=False):
    """True if safe_write would refuse this name (hand edit or no record)."""
    path = _path(base, name)
    if force or not os.path.exists(path):
        return False
    with open(path, encoding="utf-8", errors="replace") as fh:
        return _load(base).get(name) != _sha(fh.read())


def safe_write(base, name, text, force=False):
    """Return True if written, False if refused. With force the old text is kept as <name>.<sha8>.bak (an existing backup is never replaced)."""
    hashes = _load(base)  # a damaged registry fails here, before anything is written
    if refused(base, name, force):
        return False
    path = _path(base, name)
    if force and os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            old = fh.read()
        bak = "%s.%s.bak" % (path, _sha(old)[:8])  # one backup per distinct old text; never replaced
        if not os.path.exists(bak):
            with open(bak, "w", encoding="utf-8") as fh:
                fh.write(old)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    hashes[name] = _sha(text)
    reg = os.path.join(base, REG)
    os.makedirs(os.path.dirname(reg), exist_ok=True)
    with open(reg + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(hashes, fh, indent=1, sort_keys=True)
    os.replace(reg + ".tmp", reg)
    return True


def adopt(base, name):
    """Record the sha of the file as it is now (a hand edit becomes the new baseline); nothing else is written."""
    path = _path(base, name)
    hashes = _load(base)
    with open(path, encoding="utf-8", errors="replace") as fh:
        hashes[name] = _sha(fh.read())
    reg = os.path.join(base, REG)
    os.makedirs(os.path.dirname(reg), exist_ok=True)
    with open(reg + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(hashes, fh, indent=1, sort_keys=True)
    os.replace(reg + ".tmp", reg)
    return True
