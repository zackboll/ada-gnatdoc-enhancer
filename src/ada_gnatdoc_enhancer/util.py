"""Deterministic parsing, filesystem, and hashing helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .errors import EnhancementError

PAGE_NAME = re.compile(r"[0-9a-f]{64}\.html\Z")
IDENT = r"[A-Za-z][A-Za-z0-9_]*"
QNAME = IDENT + r"(?:\." + IDENT + r")*"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EnhancementError(reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path) -> Path:
    require(not path.is_symlink() and path.is_file(), f"missing/nonregular file: {path}")
    return path


def inside(base: Path, name: str) -> Path:
    """Allow only unencoded, canonical, relative paths within a named root."""
    require(isinstance(name, str) and bool(name), "empty or invalid file path")
    require(not any(x in name for x in ("\\", "%", "\x00", "?", "#")), "unapproved path encoding")
    require(not name.startswith("/") and not name.endswith("/"), f"absolute/directory path: {name}")
    parts = Path(name).parts
    require(parts and all(x not in (".", "..", "") for x in parts), f"traversal path: {name}")
    root = base.resolve()
    target = base.joinpath(*parts)
    require(target.resolve().is_relative_to(root), f"path leaves root: {name}")
    return target


def sorted_json(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def local_link(page: Path, site: Path, link: str, *, external: frozenset[str] = frozenset(),
               exact_external_fragments: frozenset[str] = frozenset()):
    require(isinstance(link, str) and bool(link), "empty URL")
    require(not re.search(r"[\x00-\x20\\]", link), f"unsafe URL whitespace/backslash: {link}")
    uri = urlsplit(link)
    if uri.scheme or uri.netloc:
        require(uri.scheme == "https" and uri.netloc in external and not uri.username and not uri.password
                and not uri.query and (not uri.fragment or link in exact_external_fragments),
                f"unapproved external URL: {link}")
        return None, ""
    require(not uri.query and not uri.path.startswith("/") and not uri.path.startswith("//"),
            f"unsafe local link: {link}")
    unescaped = unquote(uri.path)
    require("%" not in unescaped and "\\" not in unescaped, f"double-encoded/backslash URL: {link}")
    target = (page.parent / unescaped).resolve() if unescaped else page.resolve()
    require(target.is_relative_to(site.resolve()), f"URL escapes site: {link}")
    require(target.is_file() and not target.is_symlink(), f"missing local target: {link}")
    return target, unquote(uri.fragment)
