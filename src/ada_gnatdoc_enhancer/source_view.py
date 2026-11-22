"""Opt-in complete Ada source views, bound to source and pinned native bytes.

No output manifest authorizes source ownership, native anchors or locations.
Only the existing inventory/reconciler supplies declarations; this is not an
Ada parser. CR is serialized as a character reference to avoid HTML's newline
normalization. The code element's textContent is the original UTF-8 text.
"""
from __future__ import annotations

import html
import json
import posixpath
import re
from pathlib import Path

from .destinations import source_destinations
from .errors import EnhancementError
from .inventory import HEADER, mask_ada
from .metadata import guide_title
from .source_lexer import tokenize
from .theme import asset
from .util import digest, inside, regular, require

CSS = 'api/gnatdoc-source.css'
TOKEN_KINDS = frozenset(('keyword', 'comment', 'string', 'character',
                         'number', 'attribute', 'operator'))


def owned(root: Path, name: str) -> Path:
    path = inside(root, name)
    require(all(not p.is_symlink() for p in (path, *path.parents)),
            f'symlink source-view input: {name}')
    return regular(path)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate native source-view evidence key')
        result[key] = value
    return result


def native_evidence(root, options):
    schema = options['schema_version']
    fields = {'schema_version', 'files', 'sources'}
    if schema == 2:
        from .body_sources import MODE, path_name
        path_name(root, options['native_manifest'])
        fields |= {'mode', 'bodies'}
    raw = owned(root, options['native_manifest']).read_bytes()
    require(isinstance(options['native_manifest_sha256'], str) and
            digest(raw) == options['native_manifest_sha256'], 'native source-view evidence hash mismatch')
    try:
        data = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as error:
        raise EnhancementError('invalid native source-view evidence JSON') from error
    require(isinstance(data, dict) and set(data) == fields and
            type(data['schema_version']) is int and data['schema_version'] == schema and
            isinstance(data['files'], dict) and isinstance(data['sources'], dict),
            'invalid native source-view evidence schema')
    for name, sha in data['files'].items():
        require(isinstance(name, str) and re.fullmatch(
            r'api/(?:index\.html|[a-f0-9]{64}\.html|gnatdoc\.css)', name) and
            isinstance(sha, str) and re.fullmatch('[a-f0-9]{64}', sha),
            'invalid native source-view evidence entry')
    if schema == 1:
        for name, sha in data['sources'].items():
            owned(root, name)
            require(name.endswith('.ads') and isinstance(sha, str) and
                    re.fullmatch('[a-f0-9]{64}', sha), 'invalid source-view source evidence')
    else:
        from .util import QNAME
        require(schema == 2 and options['mode'] == data['mode'] == MODE and
                isinstance(data['bodies'], dict), 'invalid body-mode evidence schema')
        seen = set()
        for kind, extension in (('sources', '.ads'), ('bodies', '.adb')):
            packages = set()
            for name, entry in data[kind].items():
                path_name(root, name)
                owned(root, name)
                require(name.endswith(extension) and name.casefold() not in seen and
                        isinstance(entry, dict) and set(entry) == {'package', 'sha256'} and
                        isinstance(entry['package'], str) and re.fullmatch(QNAME, entry['package']) and
                        isinstance(entry['sha256'], str) and re.fullmatch('[a-f0-9]{64}', entry['sha256']),
                        'invalid or case-colliding body-mode source evidence')
                owner = entry['package'].lower()
                require(owner not in packages, 'duplicate package in body-mode evidence')
                packages.add(owner); seen.add(name.casefold())
    return data


def native_fingerprints(native):
    observed = {'api/index.html': digest(native.index.encode('utf-8')),
                'api/gnatdoc.css': digest(native.original_css)}
    observed.update({'api/' + p.path.name: digest(p.original.encode('utf-8'))
                     for p in native.pages.values()})
    return observed


def check_native(native, evidence):
    require(native_fingerprints(native) == evidence['files'],
            'native source-view identity differs from independently pinned input')


def escaped(text):
    return html.escape(text).replace('\r', '&#13;').replace('{', '&#123;').replace('}', '&#125;')


def highlighted_lines(text):
    """One display-only lexical pass; tokens never cross a line wrapper.

    Validate the lexer partition before serialization, not just its joined text.
    Only fixed lexical classes and escaped source may enter the generated HTML.
    """
    lines = [[]]; cursor = 0
    for token in tokenize(text):
        require(token.start == cursor and token.end > token.start and
                token.text == text[token.start:token.end] and
                token.kind in TOKEN_KINDS | {'space', 'identifier', 'plain'},
                'invalid source-view token partition')
        cursor = token.end
        for i, piece in enumerate(token.text.split('\n')):
            if i:
                lines[-1].append('\n'); lines.append([])
            if piece:
                value = escaped(piece)
                if token.kind in TOKEN_KINDS:
                    value = '<span class="ada-' + token.kind + '">' + value + '</span>'
                lines[-1].append(value)
    require(cursor == len(text), 'incomplete source-view token partition')
    if not text or text.endswith('\n'):
        lines.pop()
    return [''.join(line) for line in lines]


def render(config, name, raw, *, navigation=''):
    try:
        text = raw.decode('utf-8')
    except UnicodeError as error:
        raise EnhancementError('source view requires valid UTF-8') from error
    require('\x00' not in text and '\r' not in text.replace('\r\n', ''),
            'source view does not support NUL or bare CR')
    # Split only on LF, not Unicode separators, and do not invent an empty line
    # after a terminal newline. Each real line retains its exact terminator.
    lines = text.split('\n') if text else []
    if text:
        lines = [part + '\n' for part in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    lines = highlighted_lines(text) if config.highlight else [escaped(line) for line in lines]
    title = guide_title(name, config.project)
    css = posixpath.relpath(CSS, posixpath.dirname('api/source/' + name + '.html'))
    code = ''.join('<span class="source-line" id="L' + str(i) + '">' +
                   '<a class="source-line-number" href="#L' + str(i) +
                   '" aria-label="Line ' + str(i) + '"></a>' + line + '</span>'
                   for i, line in enumerate(lines, 1))
    label = ('Complete implementation body, including private helpers.' if name.endswith('.adb') else
             'Complete specification, including any private section.')
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">' +
            '<meta name="viewport" content="width=device-width, initial-scale=1">' +
            '<title>' + html.escape(title) + '</title><link rel="stylesheet" href="' + css +
            '"></head><body class="source-view"><h1>' + html.escape(name) + '</h1>' +
            '<p>' + label + ' SHA-256: <samp>' + digest(raw) + '</samp></p>' +
            navigation + '<pre class="source-code"><code>' + code +
            '</code></pre></body></html>\n').encode('utf-8'), len(lines)


def build(config, native, source):
    """Reconstruct the entire authorized source surface from trusted inputs."""
    evidence = native_evidence(config.root, config.source_view)
    schema = evidence['schema_version']
    check_native(native, evidence)
    if schema == 2:
        from .body_sources import body_evidence, inventory
        from .body_destinations import reconcile
        specs, bodies, units = inventory(config, source)
        require(specs == evidence['sources'], 'specifications differ from independently pinned input')
        require(body_evidence(source, bodies) == evidence['bodies'],
                'package bodies differ from independently pinned input')
    else:
        for folder in config.sources:
            directory = inside(config.root, folder)
            require(all(not p.is_symlink() for p in (directory, *directory.parents)),
                    'symlink source-view directory')
            require(all(not p.is_symlink() for p in directory.rglob('*')),
                    'symlink in source-view directory')
        require({p.path.relative_to(config.root).as_posix(): digest(p.path.read_bytes())
                 for p in source.values()} == evidence['sources'],
                'source-view sources differ from independently pinned input')
    destinations = source_destinations(config, native, source)
    values = {CSS: asset('gnatdoc-source.css')}; records = []; links = {}; titles = {}; body_records = []
    for key, pkg in sorted(source.items()):
        name = pkg.path.relative_to(config.root).as_posix()
        require(re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', name),
                'unsupported source-view path characters')
        require(pkg.path.suffix == '.ads' and any(
            pkg.path.is_relative_to(config.root / folder) for folder in config.sources),
            'unsupported source-view ownership')
        raw = owned(config.root, name).read_bytes()
        require(raw.decode('utf-8').replace('\r\n', '\n') == pkg.source,
                'source changed while constructing source view')
        page = 'api/source/' + name + '.html'
        inside(config.root, page)
        require(page not in values, 'duplicate source-page destination')
        header = HEADER.search(mask_ada(pkg.source))
        require(header is not None and not header[1], 'private source-view ownership')
        start = re.search(r'\bpackage\b', mask_ada(pkg.source)[header.start():header.end()], re.I)
        line = pkg.source.count('\n', 0, header.start() + start.start()) + 1
        entries = [dict(kind='package', name=pkg.name, anchor=None, line=line)]
        entries.extend(dict(kind=d.declaration.kind, name=pkg.name + '.' + d.declaration.name,
                            anchor=d.section.anchor, line=d.declaration.source_line)
                       for d in destinations[key])
        navigation = ''
        if schema == 2:
            require(digest(raw) == specs[name]['sha256'], 'source changed after body-mode inventory')
            body = bodies.get(key)
            if body:
                entries[0].update(body_source=body.name, body_line=body.unit.line)
            matches = reconcile(pkg, destinations[key], units[key], body.unit if body else None, units)
            for entry in entries[1:]:
                if entry['anchor'] not in matches:
                    continue
                line_match, reason = matches[entry['anchor']]
                if reason is None:
                    entry.update(body_source=body.name, body_line=line_match)
                else:
                    entry['body_omission'] = reason
            if body:
                body_page = 'api/source/' + body.name + '.html'
                require(body_page not in values, 'duplicate body view destination')
                paired = [entry for entry in entries if 'body_line' in entry]
                navigation = source_navigation(page, body_page, paired)
                body_nav = source_navigation(body_page, page, paired, reverse=True)
                content, body_count = render(config, body.name, body.raw, navigation=body_nav)
                require(all(1 <= entry['body_line'] <= body_count for entry in paired),
                        'body destination does not denote a line')
                values[body_page] = content; titles[body_page] = guide_title(body.name, config.project)
                body_records.append(dict(package=pkg.name, source=body.name, page=body_page,
                                         sha256=digest(body.raw), lines=body_count, specification=page))
        content, count = render(config, name, raw, navigation=navigation)
        values[page] = content; titles[page] = guide_title(name, config.project)
        require(all(1 <= e['line'] <= count for e in entries), 'invalid source declaration line')
        links[key] = entries
        records.append(dict(package=pkg.name, source=name, page=page, sha256=digest(raw),
                            lines=count, declarations=entries))
    identity = {'schema_version': schema, 'mode': config.source_view['mode'],
                'native_evidence': config.source_view, 'files': records}
    if schema == 2:
        identity['bodies'] = body_records
    return values, links, identity, titles


def anchor(href, label, *, native=False):
    attrs = ' class="view-source" target="_top"' if native else ''
    return '<a' + attrs + ' href="' + html.escape(href, quote=True) + '">' + html.escape(label) + '</a>'


def source_navigation(page, other, entries, *, reverse=False):
    target = posixpath.relpath(other, posixpath.dirname(page)) + '#L'
    local_key, remote_key = ('body_line', 'line') if reverse else ('line', 'body_line')
    label = 'View specification' if reverse else 'View body'
    result = ['<nav aria-label="Ada source correspondence"><p>',
              anchor(target + str(entries[0][remote_key]), label), '</p>']
    if len(entries) > 1:
        result.append('<details><summary>Corresponding operations</summary><ul>')
        for e in sorted(entries[1:], key=lambda e: e[local_key]):
            line, remote = e[local_key], e[remote_key]
            result.extend(('<li>', anchor('#L' + str(line), e['name'] + ' (line ' + str(line) + ')'),
                           ' — ', anchor(target + str(remote), label + ' at line ' + str(remote)), '</li>'))
        result.append('</ul></details>')
    result.append('</nav>')
    return ''.join(result)


def enhance_page(text, pkg, entries, source_name, *, schema=1, restore=False):
    for entry in entries:
        link = anchor('source/' + source_name + '.html#L' + str(entry['line']),
                      'View specification' if schema == 2 else 'View source', native=True)
        if 'body_line' in entry:
            link += ' ' + anchor('source/' + entry['body_source'] + '.html#L' + str(entry['body_line']),
                                 'View body', native=True)
        if entry['anchor'] is None:
            marker = '<h1>' + html.escape(pkg.name) + '</h1>'
        else:
            # Anchor identity is already reconciled and pinned. Do not match a
            # declaration's name or assume native/source overload order.
            pattern = r'<h4 id=(?:"' + entry['anchor'] + r'"|' + entry['anchor'] + r')>[^<]+</h4>'
            found = re.findall(pattern, text)
            require(len(found) == 1, 'missing source-link native destination')
            marker = found[0]
        old, new = (marker + link, marker) if restore else (marker, marker + link)
        require(text.count(old) == 1, 'ambiguous source-link insertion or restoration')
        text = text.replace(old, new, 1)
    return text