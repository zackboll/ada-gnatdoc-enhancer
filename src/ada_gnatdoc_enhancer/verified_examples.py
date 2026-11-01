"""Portable compiler evidence consumption. No compiler or semantic runtime imports.

The project pin authenticates the selected input, not human review or a signature.
URLs are deliberately absent: every destination is independently reconstructed.
"""
from __future__ import annotations

import json
import re

from .inventory import direct_callables, mask_ada, normalized
from .errors import EnhancementError
from .util import digest, inside, regular, require, sorted_json

CLASSIFICATION = 'explicit-static-subprogram-call'


def fingerprint(value):
    return digest(sorted_json(value).encode('utf-8'))


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate verified mapping JSON key')
        result[key] = value
    return result


def fields(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), 'incomplete/unknown verified mapping fields')


def sha(value):
    require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'invalid verified SHA-256')


def native_identity(native):
    return {page.path.name: {'package': page.package,
                            'sections': [[s.anchor, s.name, s.code] for s in page.sections]}
            for page in native.pages.values()}


def defining_location(package, declaration):
    """Locate the defining token of an already inventoried complete declaration."""
    pattern = re.compile(r'\b(?:function|procedure)\s+(' + re.escape(declaration.name) + r')\b', re.I)
    masked = mask_ada(package.source)
    found = []
    for match in pattern.finditer(masked):
        # Inventory lines may include preceding whitespace; complete normalized
        # profile plus its recorded start selects this declaration, not its name.
        start = sum(len(line) for line in package.source.splitlines(keepends=True)[:declaration.line - 1])
        if match.start() < start or masked[start:match.start()].strip():
            continue
        offset = match.start(1)
        found.append((package.source.count('\n', 0, offset) + 1,
                      offset - package.source.rfind('\n', 0, offset)))
    require(len(found) == 1, 'nonunique public defining token')
    return found[0]


def destination_for(selected, identity, profile, config, source, symbols):
    fields(selected, {'file', 'line', 'column', 'sha256', 'kind'})
    sha(selected['sha256'])
    require(selected['kind'] == 'SubpDecl', 'unsupported canonical declaration kind')
    require(isinstance(identity, str) and isinstance(profile, str) and profile,
            'missing canonical identity/profile')
    require(type(selected['line']) is int and type(selected['column']) is int and
            selected['line'] > 0 and selected['column'] > 0, 'invalid declaration location')
    path = regular(inside(config.root, selected['file']))
    require(digest(path.read_bytes()) == selected['sha256'], 'stale selected declaration source')
    candidates = []
    for group in symbols.values():
        for target in group:
            pkg = source[target.package.lower()]
            decl = target.declaration
            # Publishing inventories may contain byte-identical public exports
            # rather than the compiler tree's private/internal source closure.
            if (pkg.path.name != path.name or digest(pkg.path.read_bytes()) != selected['sha256'] or
                    decl.kind not in {'function', 'procedure'}):
                continue
            if normalized(decl.signature) != normalized(profile):
                continue
            require(decl.signature in direct_callables(pkg), 'unsupported nested/generic public declaration')
            if defining_location(pkg, decl) != (selected['line'], selected['column']):
                continue
            require(identity == (pkg.name + '.' + decl.name).lower(), 'canonical declaration identity mismatch')
            candidates.append(target)
    require(len(candidates) == 1, 'selected declaration lacks unique public/native profile')
    return candidates[0]


class VerifiedExamples:
    def __init__(self, config, native, source, symbols, authoritative):
        try:
            self._load(config, native, source, symbols, authoritative)
        except (KeyError, TypeError, ValueError, UnicodeError, OSError) as exc:
            raise EnhancementError('invalid verified mapping: ' + str(exc)) from exc

    def _load(self, config, native, source, symbols, authoritative):
        from .authored import source as read_source
        setting = config.verified_examples
        payload = read_source(config, setting['mapping'])
        require(digest(payload) == setting['sha256'], 'verified mapping pin mismatch')
        data = json.loads(payload, object_pairs_hook=unique)
        fields(data, {'schema_version', 'inputs', 'native_sha256', 'provenance', 'mappings', 'skipped'})
        require(type(data['schema_version']) is int and data['schema_version'] == 1, 'unsupported verified mapping schema')
        require(isinstance(data['inputs'], dict) and data['inputs'], 'missing compiler project inputs')
        for name, expected in data['inputs'].items():
            sha(expected)
            require(digest(read_source(config, name)) == expected, 'stale compiler project/source input: ' + name)
        sha(data['native_sha256'])
        require(fingerprint(native_identity(native)) == data['native_sha256'], 'changed verified native anchors/profiles')
        fields(data['provenance'], {'compiler', 'libadalang', 'project', 'evidence', 'ali'})
        for value in data['provenance'].values():
            sha(value)
        require(isinstance(data['mappings'], list) and isinstance(data['skipped'], list), 'invalid verified records')
        self.examples, self.links = {}, {}
        require(authoritative is not None, 'verified mappings need authoritative example inventory')
        evidence = fingerprint(data['provenance'])
        for mapping in data['mappings']:
            fields(mapping, {'schema_version', 'source', 'occurrence', 'selected', 'compiler_selected', 'identity', 'profile',
                             'classification', 'evidence_sha256'})
            require(type(mapping['schema_version']) is int and mapping['schema_version'] == 1 and
                    mapping['classification'] == CLASSIFICATION, 'unsupported verified call classification')
            require(mapping['evidence_sha256'] == evidence, 'inconsistent compiler evidence fingerprint')
            example = mapping['source']
            fields(example, {'file', 'sha256'})
            name = example['file']
            require(isinstance(name, str), 'invalid example source path')
            require(name in authoritative and name in data['inputs'], 'unowned/uncompiled example identity')
            raw = read_source(config, name)
            require(digest(raw) == example['sha256'] == data['inputs'][name], 'stale complete example source')
            text = raw.decode('utf-8')
            require(text.isascii() and '\t' not in text and '\r' not in text, 'unqualified example columns')
            self.examples[name] = text
            occurrence = mapping['occurrence']
            fields(occurrence, {'line', 'column', 'start', 'end', 'text'})
            line, column, start, end = (occurrence[k] for k in ('line', 'column', 'start', 'end'))
            require(all(type(v) is int for v in (line, column, start, end)) and
                    line > 0 and column > 0 and 0 <= start < end <= len(text), 'invalid exact call span')
            require(text[start:end] == occurrence['text'] and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', text[start:end]),
                    'call span is not an exact callee token')
            require(mask_ada(text)[start:end] == text[start:end] and
                    (not start or not re.match(r'[A-Za-z0-9_]', text[start - 1])) and
                    (end == len(text) or not re.match(r'[A-Za-z0-9_]', text[end])), 'call span cuts a token')
            require(text.count('\n', 0, start) + 1 == line and
                    start - text.rfind('\n', 0, start) == column, 'call coordinates differ from exact span')
            fields(mapping['selected'], {'file', 'line', 'column', 'sha256', 'kind'})
            fields(mapping['compiler_selected'], {'file', 'line', 'column', 'sha256'})
            require(mapping['compiler_selected'] == {k: v for k, v in mapping['selected'].items() if k != 'kind'},
                    'compiler/Libadalang declaration identity mismatch')
            require(mapping['selected']['file'] in data['inputs'] and
                    mapping['selected']['sha256'] == data['inputs'][mapping['selected']['file']],
                    'selected declaration not bound to compiler snapshot')
            target = destination_for(mapping['selected'], mapping['identity'], mapping['profile'], config, source, symbols)
            require(text[start:end].lower() == target.declaration.name.lower(), 'callee spelling differs from declaration')
            links = self.links.setdefault(name, [])
            require(not any(start < b and a < end for a, b, _ in links), 'duplicate/conflicting verified spans')
            links.append((start, end, target.href))
        for skipped in data['skipped']:
            fields(skipped, {'source', 'line', 'column', 'status', 'reason'})
            require(all(isinstance(skipped[k], str) and skipped[k] for k in ('source', 'status', 'reason')),
                    'incomplete skipped-call reason')
            require(type(skipped['line']) is int and skipped['line'] > 0 and
                    type(skipped['column']) is int and skipped['column'] > 0, 'invalid skipped-call coordinates')

    def positions(self, text, source):
        if source not in self.examples:
            return []
        require(text == self.examples[source], 'verified fence differs from complete authoritative source')
        return sorted(self.links[source])