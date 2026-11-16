"""Refuse to overwrite a hand-edited generated file (R460 B1). The sha of every file this tool wrote is kept in
hand-kept/.generated-hashes.json; a file whose sha differs, or that has no stored sha, is not overwritten unless force."""
import hashlib, json, os


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_write(base, name, text, force=False):
    """Return True if written, False if refused."""
    path = os.path.join(base, name)
    reg = os.path.join(base, "hand-kept", ".generated-hashes.json")
    hashes = json.load(open(reg)) if os.path.exists(reg) else {}
    if os.path.exists(path) and not force:
        cur = _sha(open(path, encoding="utf-8", errors="replace").read())
        if hashes.get(name) != cur:
            return False
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.makedirs(os.path.dirname(reg), exist_ok=True)
    hashes[name] = _sha(text)
    json.dump(hashes, open(reg, "w"), indent=1, sort_keys=True)
    return True
