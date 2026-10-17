"""Hash-bound, opt-in authored publishing, not a general template engine.

The project configuration binds the qualification record. That record binds
every authoritative input and the independently acquired native destinations.
Publication metadata cannot expand any of these permissions. No consumer code
is imported or executed by this module.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from importlib.metadata import version
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from .inventory import normalized, packages
from .destinations import source_destinations
from .util import digest, inside, regular, require
from .validation import Page, css_safe

FIELDS = {'schema_version', 'home', 'stylesheet', 'guides', 'inputs',
          'native_sha256', 'site_map', 'anchors', 'groups', 'examples',
          'languages', 'source_links', 'attribution_base', 'title_suffix',
          'api_label', 'source_inventory', 'landing_example', 'ada_policy',
          'example_project', 'landing_project', 'directory_pages', 'renderer_exceptions'}


def check_html(text):
    class Strict(HTMLParser):
        def handle_starttag(self, tag, attrs):
            require(tag in {'html', 'head', 'meta', 'title', 'link', 'body', 'header', 'main',
                    'footer', 'nav', 'section', 'aside', 'div', 'span', 'p', 'a', 'ul', 'ol', 'li',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'strong', 'em', 'blockquote',
                    'hr', 'br', 'table', 'caption', 'thead', 'tbody', 'tr', 'th', 'td'},
                    'unapproved authored HTML element')
            require(all(k in {'lang', 'charset', 'name', 'content', 'rel', 'href', 'id', 'class',
                        'aria-label', 'aria-labelledby', 'aria-current', 'scope', 'tabindex',
                        'role', 'data-package-entry'} for k, _ in attrs),
                    'unapproved authored HTML attribute')
            if tag == 'link':
                require(dict(attrs).get('rel') == 'stylesheet', 'unapproved authored resource')
        handle_startendtag = handle_starttag
    parser = Strict(); parser.feed(text); parser.close()
    page = Page(text)
    require(not page.issues and len(page.ids) == len(set(page.ids)), 'unsafe authored HTML/duplicate IDs')


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate authored manifest key')
        result[key] = value
    return result


def source(config, name):
    path = inside(config.root, name)
    require(all(not p.is_symlink() for p in (path, *path.parents)),
            'symlink authoritative source')
    return regular(path).read_bytes()


def manifest(config, native):
    payload = source(config, config.guide_manifest)
    require(digest(payload) == config.guide_sha256, 'authored manifest hash mismatch')
    data = json.loads(payload, object_pairs_hook=unique)
    require(isinstance(data, dict) and set(data) == FIELDS and data['schema_version'] == 2,
            'unknown authored manifest structure')
    require(data['renderer_exceptions'] == list(config.renderer_exceptions),
            'authored renderer exception policy changed')
    require(isinstance(data['inputs'], dict) and data['inputs'], 'missing authored input hashes')
    for name, expected in data['inputs'].items():
        require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected),
                'invalid authored input hash')
        require(digest(source(config, name)) == expected, f'authored source changed: {name}')
    require(isinstance(data['guides'], list) and data['guides'], 'missing authored guides')
    ids, sources = set(), set()
    for entry in data['guides']:
        require(isinstance(entry, dict) and set(entry) ==
                {'id', 'label', 'path', 'source', 'entry_points'}, 'unknown authored guide entry')
        identity = entry['id']
        require(isinstance(identity, str) and re.fullmatch('[a-z][a-z0-9-]*', identity),
                'invalid authored guide identity')
        require(identity not in ids and entry['source'] not in sources, 'duplicate/ambiguous authored guide')
        ids.add(identity); sources.add(entry['source'])
        require(entry['path'] == f'guides/{identity}.html', 'unapproved authored guide output')
        require(isinstance(entry['label'], str) and entry['label'].strip(), 'invalid authored label')
        require(isinstance(entry['entry_points'], list) and
                all(isinstance(x, str) for x in entry['entry_points']), 'invalid API entry points')
    for key, path in (('home', 'index.html'), ('stylesheet', None)):
        value = data[key]
        require(isinstance(value, dict) and set(value) == {'source', 'path'}, 'invalid authored file mapping')
        if path:
            require(value['path'] == path, 'unapproved authored home output')
    require(data['stylesheet']['path'] in ('guides/gnatdoc-guides.css', 'assets/portal.css'),
            'unapproved authored stylesheet output')
    mapped = {data['home']['source'], data['stylesheet']['source'], *sources}
    require(len(mapped) == len(sources) + 2, 'ambiguous authored source mapping')
    require(isinstance(data['source_links'], dict), 'invalid source link mappings')
    for link, item in data['source_links'].items():
        require(isinstance(item, dict) and set(item) == {'source', 'url'}, 'invalid source reference')
        mapped.add(item['source'])
        safe_uri(item['url'], config)
    require(isinstance(data['examples'], list) and len(set(data['examples'])) == len(data['examples']),
            'duplicate/invalid example inputs')
    mapped.update(data['examples'])
    for key in ('site_map', 'anchors', 'landing_example', 'example_project', 'landing_project'):
        if data[key] is not None:
            mapped.add(data[key])
    require(mapped == set(data['inputs']), 'unapproved or missing authored input inventory')
    require(data['ada_policy'] in ('source-text', 'exact-examples'), 'unsupported Ada fence policy')
    if data['ada_policy'] == 'exact-examples':
        require(data['examples'] and data['example_project'] and data['landing_project'] and
                data['landing_example'], 'missing authoritative example build requirements')
        project = source(config, data['example_project']).decode('utf-8')
        mains = re.findall(r'"([A-Za-z0-9_]+\.adb)"', project)
        require(Counter(mains) == Counter(Path(p).name for p in data['examples']) and
                all(s in project for s in ('"-gnat2022"', '"-gnata"', '"-Werror"')),
                'examples not covered by authoritative build project')
        folders = {inside(config.root, p).parent for p in data['examples']}
        actual_examples = {p.relative_to(config.root).as_posix()
                           for folder in folders for p in folder.glob('*.adb')}
        require(actual_examples == set(data['examples']), 'extra or missing authoritative example source')
        landing = source(config, data['landing_project']).decode('utf-8')
        require(Path(data['landing_example']).name in re.findall(r'"([A-Za-z0-9_]+\.adb)"', landing),
                'landing example not covered by build project')
    observed = {'api/index.html': digest(native.index.encode()),
                'api/gnatdoc.css': digest(native.original_css)}
    observed.update({'api/' + p.path.name: digest(p.original.encode()) for p in native.pages.values()})
    require(data['native_sha256'] == observed, 'authored native destination evidence mismatch')
    require(isinstance(data['languages'], list) and len(set(data['languages'])) == len(data['languages'])
            and set(data['languages']) <= {'ada', 'sh', 'shell', 'text', ''}, 'unsupported fence policy')
    for key in ('attribution_base', 'title_suffix', 'api_label'):
        require(isinstance(data[key], str) and data[key], 'missing authored presentation identity')
    safe_uri(data['attribution_base'], config)
    if data['source_inventory'] is not None:
        folder = inside(config.root, data['source_inventory'])
        require(not folder.is_symlink(), 'symlink authored inventory')
        actual = {p.relative_to(config.root).as_posix() for p in folder.glob('*.md')}
        require(actual == sources, 'extra or missing authored guide source')
    if config.guides == 'authored-html':
        require(data['site_map'] is not None and data['anchors'] is not None and
                not data['examples'] and not data['source_links'], 'incomplete HTML portal evidence')
        approved = json.loads(source(config, data['site_map']), object_pairs_hook=unique)
        expected = {'schema_version': 1, 'home': 'index.html',
                    'stylesheet': data['stylesheet']['path'],
                    'guides': [{k: e[k] for k in ('id', 'label', 'path')} for e in data['guides']]}
        require(approved == expected, 'source-owned portal site map mismatch')
        require(isinstance(data['directory_pages'], list) and
                len(set(data['directory_pages'])) == len(data['directory_pages']) and
                'index.html' in data['directory_pages'] and
                set(data['directory_pages']) <= {'index.html', *(e['path'] for e in data['guides'])},
                'invalid portal directory page inventory')
        verify_anchors(config, data, native)
    else:
        require(data['site_map'] is None and data['anchors'] is None and not data['groups'],
                'portal-only inputs in Markdown contract')
        require(data['directory_pages'] == [], 'portal directories in Markdown contract')
        require(data['stylesheet']['path'] == 'guides/gnatdoc-guides.css', 'incorrect Markdown stylesheet path')
    return data


def safe_uri(link, config):
    require(isinstance(link, str) and link and not re.search(r'[\x00-\x20\\]', link), 'unsafe authored URL')
    # None of the qualified inputs needs URI escaping. Reject rather than
    # normalize malformed, nested, encoded traversal or encoded schemes.
    require('%' not in link, 'unqualified authored URI encoding')
    url = urlsplit(link)
    require(not url.query, 'unexpected authored URL query')
    if url.scheme or url.netloc:
        require(url.scheme == 'https' and url.netloc in config.allowed_hosts and
                not url.username and not url.password, 'unapproved authored external URL')
    else:
        require(not url.path.startswith('/') and not any(p in ('.', '..') for p in url.path.split('/')),
                'unsafe authored relative URL')
    return url


def markdown(text, languages, rewrite=None):
    from markdown_it import MarkdownIt
    require(version('markdown-it-py') == '3.0.0' and version('mdurl') == '0.1.2',
            'unqualified Markdown dependency version')
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    parser.validateLink = lambda destination: True
    parser.normalizeLink = lambda destination: destination
    tokens = parser.parse(text)
    headings, fences, level = [], [], 0
    for i, token in enumerate(tokens):
        require(token.type not in ('html_block', 'html_inline', 'image', 'code_block'),
                'unsupported raw HTML, image or indented code')
        if token.type == 'fence':
            end = token.map[1] - 1
            require(end > token.map[0] and re.fullmatch(
                r' {0,3}' + re.escape(token.markup[0]) + '{' + str(len(token.markup)) + r',}\s*',
                text.splitlines()[end]), 'unclosed Markdown fence')
            require(token.info.strip() in languages, 'unsupported code language')
            if token.info.strip() == 'ada':
                fences.append(token.content)
        if token.type == 'heading_open':
            current = int(token.tag[1:])
            require(current <= level + 1 and (current != 1 or not headings), 'invalid heading hierarchy')
            level = current
            title = ''.join(t.content for t in tokens[i + 1].children if t.type in ('text', 'code_inline'))
            identity = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
            require(identity, 'empty heading identity')
            base, suffix = identity, 0
            while identity in headings:
                suffix += 1; identity = f'{base}-{suffix}'
            headings.append(identity); token.attrSet('id', identity)
        for child in token.children or []:
            require(child.type not in ('html_inline', 'image'), 'unsupported inline markup')
            if child.type == 'link_open' and rewrite:
                child.attrSet('href', rewrite(child.attrGet('href')))
    require(headings and tokens[0].type == 'heading_open' and tokens[0].tag == 'h1',
            'guide must begin with one H1')
    rendered = parser.renderer.render(tokens, parser.options, {})
    rendered = rendered.replace('<table>', '<div class="table-scroll" tabindex="0" role="region" '
                                'aria-label="Scrollable table"><table>').replace('</table>', '</table></div>')
    return rendered, headings, fences


def api_destinations(config, native):
    """Resolve overloads in source order using unique complete profile evidence."""
    result, owners = {}, {}
    for key, destinations in source_destinations(config, native, packages(config)).items():
        result[key] = '../api/' + native.pages[key].path.name
        for destination in destinations:
            name = destination.declaration.name.lower()
            qualified = key + '.' + name
            url = '../api/' + destination.href
            result[qualified + '/' + str(destination.ordinal)] = url
            result.setdefault(qualified, url)
            owners.setdefault(name, set()).add(key)
    for name, parents in owners.items():
        if len(parents) != 1:
            continue
        parent = next(iter(parents))
        for key, value in list(result.items()):
            if key == parent + '.' + name or key.startswith(parent + '.' + name + '/'):
                result[key[len(parent) + 1:]] = value
    return result


def verify_anchors(config, data, native):
    evidence = json.loads(source(config, data['anchors']), object_pairs_hook=unique)
    require(isinstance(evidence, dict) and evidence, 'missing native anchor evidence')
    actual = {(p.package, p.path.name, s.anchor, normalized(s.code).rstrip(' ;'))
              for p in native.pages.values() for s in p.sections}
    qualified = set()
    for identity, entry in evidence.items():
        require(isinstance(entry, dict) and set(entry) == {'page', 'anchor', 'signature'},
                'invalid native anchor evidence')
        item = (identity.split(':', 1)[0], entry['page'], entry['anchor'],
                normalized(entry['signature']).rstrip(' ;'))
        require(item in actual and item not in qualified, 'swapped/incorrect native anchor evidence')
        qualified.add(item)
    require(qualified == actual, 'incomplete native anchor evidence')


def portal(text, page, data, native):
    prefix = '../' if page.startswith('guides/') else ''
    packages = {p.package: 'api/' + p.path.name for p in native.pages.values()}
    def package_link(name, directory=False):
        require(name in packages, 'unknown authored package reference')
        marker = ' data-package-entry="' + name + '"' if directory else ''
        return f'<a{marker} href="{prefix}{packages[name]}">{html.escape(name)}</a>'
    groups = data['groups']
    require(isinstance(groups, list) and groups, 'missing package groups')
    labels, members = [], []
    for group in groups:
        require(isinstance(group, dict) and set(group) == {'label', 'packages'} and
                isinstance(group['label'], str) and group['label'] and
                isinstance(group['packages'], list), 'invalid package group')
        labels.append(group['label']); members.extend(group['packages'])
    require(len(set(labels)) == len(labels) and Counter(members) == Counter(packages.keys()),
            'invalid package group inventory/cardinality')
    nav = '<nav aria-label="Documentation"><ul>'
    nav += f'<li><a href="{prefix}index.html">Home</a></li>'
    nav += ''.join(f'<li><a href="{e["path"].removeprefix("guides/") if prefix else e["path"]}">'
                   f'{html.escape(e["label"])}</a></li>' for e in data['guides'])
    nav += f'<li><a href="{prefix}api/index.html">Complete API Reference</a></li></ul></nav>'
    directory = '<section aria-label="Public package directory">'
    for group in groups:
        directory += '<h3>' + html.escape(group['label']) + '</h3><ul>'
        directory += ''.join(f'<li>{package_link(name, True)}</li>' for name in group['packages'])
        directory += '</ul>'
    directory += '</section>'
    directory_count = text.count('{{package-directory}}')
    text = text.replace('{{navigation}}', nav).replace('{{package-directory}}', directory)
    text = re.sub(r'\{\{package:([A-Za-z0-9_.]+)\}\}', lambda m: package_link(m[1]), text)
    require('{{' not in text and '}}' not in text, 'unknown/unresolved portal placeholder')
    entries = Page(text).package_entries
    if directory_count:
        require(directory_count == 1, 'duplicate portal directory')
        require(Counter(entries) == Counter((n, prefix + p) for n, p in packages.items()),
                'incomplete portal directory')
    return text


def render(config, native):
    data = manifest(config, native)
    style = source(config, data['stylesheet']['source']); css_safe(style)
    output = {data['stylesheet']['path']: style}
    home = source(config, data['home']['source']).decode('utf-8')
    texts = {e['id']: source(config, e['source']).decode('utf-8') for e in data['guides']}
    if config.guides == 'authored-html':
        for path, text in [('index.html', home), *((e['path'], texts[e['id']]) for e in data['guides'])]:
            rendered = portal(text, path, data, native)
            require(text.count('{{navigation}}') == 1, 'missing/duplicate portal navigation')
            if path in data['directory_pages']:
                require(text.count('{{package-directory}}') == 1 and
                        len(Page(rendered).package_entries) == len(native.pages), 'portal directory cardinality')
            else:
                require('{{package-directory}}' not in text, 'unapproved package directory page')
            check_html(rendered)
            output[path] = rendered.encode()
        return output
    headings = {name: markdown(text, data['languages'])[1] for name, text in texts.items()}
    api = api_destinations(config, native)
    examples = {name: source(config, name).decode('utf-8') for name in data['examples']}
    used = set()
    for entry in data['guides']:
        name = entry['id']; text = texts[name]
        require(text.splitlines()[0] == '# ' + entry['label'], 'wrong authored guide title')
        def rewrite(link):
            if link.startswith('api:'):
                key = link[4:].lower()
                require(re.fullmatch(r'[a-z][a-z0-9_.]*(?:/[1-9][0-9]*)?', key) and key in api,
                        'unknown/ambiguous authored API declaration')
                return api[key]
            if link in data['source_links']:
                item = data['source_links'][link]
                require('%' not in link and not re.search(r'[\x00-\x20\\]', link), 'unsafe source reference')
                reference = urlsplit(link)
                require(not reference.scheme and not reference.netloc and not reference.query and
                        not reference.path.startswith('/'), 'invalid source reference URL')
                target = (config.root/Path(entry['source']).parent/reference.path).resolve()
                require(target == inside(config.root, item['source']).resolve(), 'swapped source reference ownership')
                fragment = urlsplit(link).fragment
                expected = data['attribution_base'] + item['source'] + ('#' + fragment if fragment else '')
                require(item['url'] == expected, 'swapped source reference destination')
                if fragment:
                    require(fragment in markdown(source(config, item['source']).decode(), data['languages'])[1],
                            'invalid source reference fragment')
                return item['url']
            url = safe_uri(link, config)
            if url.scheme:
                return link
            target = url.path.removesuffix('.md') if url.path else name
            require((not url.path or url.path.endswith('.md')) and target in headings,
                    'unknown published guide destination')
            require(not url.fragment or url.fragment in headings[target], 'invalid guide heading fragment')
            return (target + '.html' if url.path else '') + ('#' + url.fragment if url.fragment else '')
        content, ids, fences = markdown(text, data['languages'], rewrite)
        for fence in fences:
            if data['ada_policy'] == 'exact-examples':
                owners = [p for p, value in examples.items() if value == fence]
                require(len(owners) == 1, 'Ada fence differs from unique authoritative example')
                used.update(owners)
        require(not {'main-content', 'native-api-entry-points'} & set(ids), 'reserved heading identity')
        nav = '\n'.join(f'<li><a href="{e["id"]}.html"' +
                        (' aria-current="page"' if e['id'] == name else '') +
                        f'>{html.escape(e["label"])}</a></li>' for e in data['guides'])
        entries = []
        for identity in entry['entry_points']:
            require(identity.lower() in api, 'unknown native API entry point')
            label = identity.rsplit('/', 1)[0]
            entries.append(f'<li><a href="{api[identity.lower()]}">{html.escape(label)}</a></li>')
        page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(entry['label'])} — {html.escape(data['title_suffix'])}</title>
<link rel="stylesheet" href="../api/gnatdoc-theme.css">
<link rel="stylesheet" href="gnatdoc-guides.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header><nav aria-label="Documentation"><a href="../index.html">Documentation home</a> · <a href="../api/index.html">{html.escape(data['api_label'])}</a></nav></header>
<div class="guide-layout">
<nav class="guide-nav" aria-label="Developer guides"><ul>
{nav}
</ul></nav>
<main id="main-content">
{content}
<section aria-label="Native API entry points"><h2 id="native-api-entry-points">Native API entry points</h2><ul>
{chr(10).join(entries)}
</ul></section>
<p class="guide-source"><a href="{html.escape(data['attribution_base'] + entry['source'], quote=True)}">Original Markdown source on GitHub</a></p>
</main>
</div>
</body>
</html>
'''
        output[entry['path']] = page.encode()
    require(used == set(examples), 'authoritative examples missing from guides')
    if data['landing_example']:
        code = source(config, data['landing_example']).decode().rstrip('\n')
        require(html.escape(code, quote=False) in home, 'landing example differs from authoritative source')
    output['index.html'] = home.encode()
    return output