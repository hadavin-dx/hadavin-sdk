"""Shared helpers for the capability scans: import-alias resolution (``import x as y``, ``from x import y as z``, relative imports, star imports) and
constant folding of string concatenation. A scan of our own files, not a proof."""

from __future__ import annotations

import ast


def build_aliases(tree: ast.AST) -> tuple[dict[str, str], list[str]]:
    """Return ``(alias -> full dotted name, star-imported modules)``. A relative import resolves under the package ``intake``."""
    alias: dict[str, str] = {}
    stars: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    alias[a.asname] = a.name
                else:
                    head = a.name.split(".")[0]
                    alias[head] = head
        elif isinstance(node, ast.ImportFrom):
            base = ("intake" + ("." + node.module if node.module else "")) if node.level else (node.module or "")
            for a in node.names:
                if a.name == "*":
                    stars.append(base)
                else:
                    alias[a.asname or a.name] = f"{base}.{a.name}"
    return alias, stars


def dotted(node: ast.AST, alias: dict[str, str]) -> str | None:
    """The alias-resolved dotted name of a Name or an Attribute chain, else None."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    head = alias.get(node.id, node.id)
    return ".".join([head, *reversed(parts)])


def fold_str(node: ast.AST) -> str | None:
    """The value of a string Constant or of a concatenation of such (``"sec" + "rets"``); None otherwise."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = fold_str(node.left), fold_str(node.right)
        return a + b if a is not None and b is not None else None
    return None


def parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}


def candidate_texts(node: ast.AST) -> list[str]:
    """Strings a node may contribute to a path or name: constants (str or bytes), constant ``+`` folds, f-string literal parts with ``{}`` for the
    values, the left side of ``%``, and the constant a ``.format`` or ``.join`` is called on."""
    out: list[str] = []
    f = fold_str(node)
    if f is not None:
        out.append(f)
    if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
        out.append(node.value.decode("latin-1"))
    if isinstance(node, ast.JoinedStr):
        out.append("".join(v.value if isinstance(v, ast.Constant) else "{}" for v in node.values))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        left = fold_str(node.left)
        if left is not None:
            out.append(left)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("format", "join"):
        base = fold_str(node.func.value)
        if base is not None:
            out.append(base)
    return out


def docstring_nodes(tree: ast.AST) -> set[int]:
    """ids of the string constants that are bare expression statements (docstrings and comment-like strings)."""
    return {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
