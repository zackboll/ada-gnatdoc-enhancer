"""Conservative source-block use resolution, not Ada overload inference.

Adapted from MEL Bridge docs/tools/ada_examples.py at
039bd4f05be969f0f224747728dfbae5305ee29b (Apache-2.0).
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from .destinations import source_destinations
from .inventory import HEADER, TYPE, SUBPROGRAM, mask_ada, packages, visible_prefix
from .source_lexer import tokenize, chains


def direct_lines(package):
    """Do not promote nested members via the historical lexical inventory.

    Only direct public declarations can authorize source-block associations.
    Nested package/task/protected scopes are masked, including generic formals.
    Renamings/instances terminate at their semicolon and do not open a scope.
    """
    header = HEADER.search(mask_ada(package.source))
    public = visible_prefix(package.source, header.end())
    tokens = [t for t in tokenize(public) if t.kind not in {'space', 'comment'}]
    words = [t.text.lower() for t in tokens]
    blocked, scopes, pending = [], [], None
    for i, word in enumerate(words):
        if word == 'generic' and not scopes:
            pending = tokens[i].start
        if word in {'package', 'task', 'protected'} and (not i or words[i - 1] != 'end'):
            j = i + 1
            if j < len(words) and words[j] in {'body', 'type'}:
                j += 1
            if j >= len(words):
                continue
            stop = next((k for k in range(j, len(words)) if words[k] in {'is', 'renames', ';'}), len(words))
            if stop < len(words) and words[stop] == 'is' and words[stop + 1:stop + 2] != ['new']:
                scopes.append((words[j], pending if pending is not None else tokens[i].start))
                pending = None
        if word == 'end' and scopes and words[i + 1:i + 2] == [scopes[-1][0]]:
            _, start = scopes.pop()
            blocked.append((start, tokens[i + 1].end))
    if scopes:
        blocked.extend((start, len(public)) for _, start in scopes)
    if pending is not None:
        blocked.append((pending, len(public)))
    masked = mask_ada(public)
    boundary = re.search(r'\bprivate\b(?!\s*;)', masked, re.I)
    limit = boundary.start() if boundary else len(public)
    return {package.source.count('\n', 0, header.end() + m.start()) + 1
            for pattern in (TYPE, SUBPROGRAM) for m in pattern.finditer(masked)
            if m.start() < limit and not any(a <= m.start() < b for a, b in blocked)}


class References:
    def __init__(self, config, native):
        source = packages(config)
        self.root_name = config.default_package.split('.')[0].lower()
        self.packages = {key: '../api/' + p.path.name for key, p in native.pages.items()}
        self.package_sources = {key: p.path.relative_to(config.root).as_posix() for key, p in source.items()}
        self.declarations = defaultdict(list)
        for owner, destinations in source_destinations(config, native, source).items():
            admitted = direct_lines(source[owner])
            for destination in destinations:
                if destination.declaration.line not in admitted:
                    continue
                key = owner + '.' + destination.declaration.name.lower()
                self.declarations[key].append(destination)

    def occurrences(self, text, name):
        tokens = [t for t in tokenize(text) if t.kind not in {"space", "comment"}]
        words = [t.text.lower() for t in tokens]
        imports, packages, aliases = set(), [], {}
        # Only ordinary context clauses before the compilation unit header.
        cursor = 0
        while cursor < len(tokens) and words[cursor] == "with":
            end = cursor + 1
            while end < len(tokens) and words[end] != ";":
                end += 1
            for start, stop, spelling in chains(tokens, cursor + 1, end):
                if start == cursor + 1 and stop == end:
                    imports.add(spelling)
                    if spelling in self.packages:
                        packages.append((start, stop, spelling))
            cursor = end + 1
        # Conservatively require one ordinary unit, no generic/separate scope.
        if words[cursor:cursor + 1] not in (["procedure"], ["package"], ["function"]):
            return []
        # Unit-level aliases only: an initial sequence of renamings/use clauses.
        # Stop at every other declaration, never scan into a nested package.
        header_end = next((i for i in range(cursor, len(words)) if words[i] == "is"), len(words))
        i = header_end + 1
        while i < len(words):
            if words[i] == "use":
                i = next((j + 1 for j in range(i, len(words)) if words[j] == ";"), len(words))
                continue
            if not (words[i] == "package" and i + 3 < len(tokens)
                    and tokens[i + 1].kind == "identifier" and words[i + 2] == "renames"):
                break
            end = next((j for j in range(i + 3, len(words)) if words[j] == ";"), len(words))
            found = list(chains(tokens, i + 3, end))
            if len(found) == 1 and found[0][:2] == (i + 3, end):
                owner = found[0][2]
                alias = words[i + 1]
                if owner in imports and owner in self.packages:
                    aliases.setdefault(alias, []).append((i + 1, end, owner))
            i = end + 1

        def unshadowed(word, definition=None):
            # Every other standalone occurrence may define/shadow this prefix.
            # Includes parameters, comma lists, loops, labels, nested packages,
            # objects and aliases. No partial scope inference is attempted.
            return all(i == definition or (i > 0 and words[i - 1] == ".") or
                       (i + 1 < len(words) and words[i + 1] == "."
                        and (i == 0 or words[i - 1] != "."))
                       for i, w in enumerate(words) if w == word)

        aliases = {alias: entries[0] for alias, entries in aliases.items()
                   if len(entries) == 1 and unshadowed(alias, entries[0][0])}
        direct = unshadowed(self.root_name)
        if not direct:
            aliases = {}
        output = []

        def record(start, stop, identity, context, href, declaration=None, alias=None, qualification=None):
            first, last = tokens[start], tokens[stop - 1]
            if any(t.kind in {"comment", "string", "character"}
                   for t in tokenize(text[first.start:last.end])):
                return
            owner = identity if context == "context-package" else identity.rpartition(".")[0]
            output.append({"source": name, "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                           "start": first.start, "end": last.end,
                           "line": text[:first.start].count("\n") + 1,
                           "visible": text[first.start:last.end], "context": context,
                           "identity": identity, "href": href,
                           "package_source": self.package_sources[owner],
                           "declaration": declaration, "alias": alias,
                           "qualification": qualification})

        if direct:
            for start, stop, owner in packages:
                record(start, stop, owner, "context-package", self.packages[owner])
        for start, stop, spelling in chains(tokens, cursor, len(tokens)):
            parts = spelling.split(".")
            alias = None
            if parts[0] in aliases and len(parts) == 2:
                definition, after, owner = aliases[parts[0]]
                if start <= after:
                    continue
                alias = {"name": parts[0], "start": tokens[definition].start,
                         "end": tokens[after].end, "owner": owner}
            elif parts[0] == self.root_name and direct and len(parts) >= 2:
                owner = ".".join(parts[:-1])
                if not any(p == owner or p.startswith(owner + ".") for p in imports):
                    continue
            else:
                continue
            identity = owner + "." + parts[-1]
            candidates = self.declarations.get(identity, [])
            if len(candidates) != 1:
                continue  # No guessed overloads, even if one looks plausible.
            entry = candidates[0]
            kind = entry.declaration.kind
            before = start - 1
            while before >= 0 and words[before] in {"constant", "aliased", "in", "out", "not", "null", "access"}:
                before -= 1
            type_context = (before >= 0 and words[before] in {":", "return"}
                            or words[max(0, start - 2):start] == ["use", "type"])
            if kind in {"type", "subtype"} and type_context:
                context = "type-mark"
            elif kind in {"function", "procedure"} and stop < len(words) and words[stop] == "(":
                context = "unique-operation"
            else:
                continue
            record(stop - 1, stop, identity, context,
                   "../api/" + entry.href, entry, alias,
                   {"start": tokens[start].start, "end": tokens[stop - 1].end,
                    "visible": text[tokens[start].start:tokens[stop - 1].end]})
        return sorted(output, key=lambda r: r["start"])
