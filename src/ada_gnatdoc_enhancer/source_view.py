"""Opt-in complete specification views, bound to source and pinned native bytes.

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
from .theme import asset
from .util import digest, inside, regular, require

CSS = 'api/gnatdoc-source.css'


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
    raw = owned(root, options['native_manifest']).read_bytes()
    require(isinstance(options['native_manifest_sha256'], str) and
            digest(raw) == options['native_manifest_sha256'], 'native source-view evidence hash mismatch')
    try:
        data = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as error:
        raise EnhancementError('invalid native source-view evidence JSON') from error
    require(isinstance(data, dict) and set(data) == {'schema_version', 'files', 'sources'} and
            type(data['schema_version']) is int and data['schema_version'] == 1 and
            isinstance(data['files'], dict) and isinstance(data['sources'], dict),
            'invalid native source-view evidence schema')
    for name, sha in data['files'].items():
        require(isinstance(name, str) and re.fullmatch(
            r'api/(?:index\.html|[a-f0-9]{64}\.html|gnatdoc\.css)', name) and
            isinstance(sha, str) and re.fullmatch('[a-f0-9]{64}', sha),
            'invalid native source-view evidence entry')
    for name, sha in data['sources'].items():
        owned(root, name)
        require(name.endswith('.ads') and isinstance(sha, str) and
                re.fullmatch('[a-f0-9]{64}', sha), 'invalid source-view source evidence')
    return data


def check_native(config, native):
    observed = {'api/index.html': digest(native.index.encode('utf-8')),
                'api/gnatdoc.css': digest(native.original_css)}
    observed.update({'api/' + p.path.name: digest(p.original.encode('utf-8'))
                     for p in native.pages.values()})
    require(observed == native_evidence(config.root, config.source_view)['files'],
            'native source-view identity differs from independently pinned input')


def escaped(text):
    return html.escape(text).replace('\r', '&#13;').replace('{', '&#123;').replace('}', '&#125;')


def render(config, name, raw):
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
    title = guide_title(name, config.project)
    css = posixpath.relpath(CSS, posixpath.dirname('api/source/' + name + '.html'))
    code = ''.join('<span class="source-line" id="L' + str(i) + '">' +
                   '<a class="source-line-number" href="#L' + str(i) +
                   '" aria-label="Line ' + str(i) + '"></a>' + escaped(line) + '</span>'
                   for i, line in enumerate(lines, 1))
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">' +
            '<meta name="viewport" content="width=device-width, initial-scale=1">' +
            '<title>' + html.escape(title) + '</title><link rel="stylesheet" href="' + css +
            '"></head><body class="source-view"><h1>' + html.escape(name) + '</h1>' +
            '<p>Complete specification, including any private section. SHA-256: <samp>' +
            digest(raw) + '</samp></p><pre class="source-code"><code>' + code +
            '</code></pre></body></html>\n').encode('utf-8'), len(lines)


def build(config, native, source):
    """Reconstruct the entire authorized source surface from trusted inputs."""
    for folder in config.sources:
        directory = inside(config.root, folder)
        require(all(not p.is_symlink() for p in (directory, *directory.parents)),
                'symlink source-view directory')
        require(all(not p.is_symlink() for p in directory.rglob('*')),
                'symlink in source-view directory')
    check_native(config, native)
    require({p.path.relative_to(config.root).as_posix(): digest(p.path.read_bytes())
             for p in source.values()} == native_evidence(config.root, config.source_view)['sources'],
            'source-view sources differ from independently pinned input')
    destinations = source_destinations(config, native, source)
    values = {CSS: asset('gnatdoc-source.css')}; records = []; links = {}; titles = {}
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
        content, count = render(config, name, raw)
        values[page] = content; titles[page] = guide_title(name, config.project)
        header = HEADER.search(mask_ada(pkg.source))
        require(header is not None and not header[1], 'private source-view ownership')
        start = re.search(r'\bpackage\b', mask_ada(pkg.source)[header.start():header.end()], re.I)
        line = pkg.source.count('\n', 0, header.start() + start.start()) + 1
        entries = [dict(kind='package', name=pkg.name, anchor=None, line=line)]
        entries.extend(dict(kind=d.declaration.kind, name=pkg.name + '.' + d.declaration.name,
                            anchor=d.section.anchor, line=d.declaration.source_line)
                       for d in destinations[key])
        require(all(1 <= e['line'] <= count for e in entries), 'invalid source declaration line')
        links[key] = entries
        records.append(dict(package=pkg.name, source=name, page=page, sha256=digest(raw),
                            lines=count, declarations=entries))
    return values, links, {'schema_version': 1, 'mode': 'public-specifications',
                           'native_evidence': config.source_view, 'files': records}, titles


def enhance_page(text, pkg, entries, source_name):
    href = 'source/' + source_name + '.html#L'
    for entry in entries:
        link = '<a class="view-source" target="_top" href="' + html.escape(href + str(entry['line']), quote=True) + '">View source</a>'
        if entry['anchor'] is None:
            marker = '<h1>' + html.escape(pkg.name) + '</h1>'
        else:
            # Anchor identity is already reconciled and pinned. Do not match a
            # declaration's name or assume native/source overload order.
            pattern = r'<h4 id=(?:"' + entry['anchor'] + r'"|' + entry['anchor'] + r')>[^<]+</h4>'
            found = re.findall(pattern, text)
            require(len(found) == 1, 'missing source-link native destination')
            marker = found[0]
        require(text.count(marker) == 1, 'ambiguous source-link insertion')
        text = text.replace(marker, marker + link, 1)
    return text