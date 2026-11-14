"""Versioned, source-owned authored blocks; no consumer code is evaluated.

Hashes bind inputs, not authority: declarations and destinations are recomputed
from the public source/native pair. Git-export provenance is independently
verified by the consumer, as for the existing authored contract.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import PurePosixPath

from .authored import check_html, source, unique
from .inventory import packages
from .source_lexer import annotate
from .symbols import public_symbols
from .util import inside, require

FIELDS = {'profile', 'manifest', 'project', 'guide', 'catalog_guide', 'symbol_policy', 'use_policy'}
ENTRY = {'id', 'title', 'purpose', 'main', 'support', 'provider_family', 'mock_library',
         'guide', 'packages', 'cases', 'executable'}
CASE = {'id', 'configuration', 'provider', 'exit', 'expected'}
SCOPES = ('stable', 'additional', 'operation')
TITLES = ('Public types and subtypes', 'Additional types used by examples', 'Operations used in examples')
IDS = ('public-symbol-index', 'additional-example-types', 'example-usage-index')
TOKEN = re.compile(r'\{\{(?:example:[^{}]*|public-symbol-index|example-usage-index)\}\}')


def token_context(text, expected):
    """Tokens are standalone text nodes, never comments, attributes or code."""
    class Context(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.stack, self.tokens = [], []

        def handle_starttag(self, tag, attrs):
            if tag not in {'meta', 'link', 'br', 'hr'}:
                self.stack.append((tag, dict(attrs)))

        def handle_endtag(self, tag):
            require(self.stack and self.stack[-1][0] == tag, 'malformed source block guide nesting')
            self.stack.pop()

        def handle_startendtag(self, tag, attrs):
            require(tag in {'meta', 'link', 'br', 'hr'}, 'noncanonical source block guide element')

        def handle_data(self, value):
            tokens = TOKEN.findall(value)
            if not tokens:
                return
            require(not TOKEN.sub('', value).strip() and
                    any(tag == 'main' for tag, _ in self.stack), 'source token outside main text context')
            for token in tokens:
                if token.startswith('{{example:'):
                    require(self.stack[-1] == ('section', {'id': token[10:-2]}),
                            'source token outside owning section')
                else:
                    require(self.stack[-1][0] == 'main', 'catalog token outside main context')
            self.tokens.extend(tokens)
    parser = Context(); parser.feed(text); parser.close()
    require(not parser.stack and Counter(parser.tokens) == Counter(expected),
            'source token hidden in attribute, comment or unsupported context')


def identity(value):
    return isinstance(value, str) and re.fullmatch('[a-z][a-z0-9-]*', value)


def input_inventory(config, data):
    block = data['source_blocks']
    require(isinstance(block, dict) and set(block) == FIELDS and
            block['profile'] == 'executable-ada-catalog-v1' and
            block['symbol_policy'] == 'stable-public-types-and-root-constants-v1' and
            block['use_policy'] == 'qualified-types-and-unique-operations-v1',
            'unsupported source block contract')
    require(all(isinstance(block[k], str) and re.fullmatch(r'[a-zA-Z0-9_/-]+\.' + suffix, block[k])
                and '..' not in block[k].split('/') for k, suffix in
                (('manifest', 'json'), ('project', 'gpr'))) and
            PurePosixPath(block['manifest']).parent == PurePosixPath(block['project']).parent,
            'unsafe or mismatched source block input paths')
    guides = {e['path'] for e in data['guides']}
    require(block['guide'] in guides and block['catalog_guide'] in guides and
            block['guide'] != block['catalog_guide'], 'invalid source block guide ownership')
    require(config.symbol_bookmarks, 'source catalog requires stable public symbol policy')
    manifest = json.loads(source(config, block['manifest']), object_pairs_hook=unique)
    require(isinstance(manifest, dict) and set(manifest) == {'schema_version', 'examples'} and
            manifest['schema_version'] == 1 and isinstance(manifest['examples'], list) and
            manifest['examples'], 'invalid executable example manifest')
    base = PurePosixPath(block['manifest']).parent
    public_sources = packages(config)
    names, mains, ids, cases = set(), [], [], []
    for entry in manifest['examples']:
        require(isinstance(entry, dict) and set(entry) == ENTRY and identity(entry['id']),
                'invalid executable example fields')
        ids.append(entry['id'])
        require(all(isinstance(entry[k], str) and entry[k] for k in
                    ('title', 'purpose', 'provider_family', 'mock_library', 'executable')) and
                entry['guide'] == block['guide'] + '#' + entry['id'] and
                isinstance(entry['support'], list) and len(set(entry['support'])) == len(entry['support']) and
                isinstance(entry['packages'], list) and entry['packages'] and
                set(entry['packages']) <= {p.name for p in public_sources.values()},
                'incorrect example identity or ownership')
        for name in [entry['main'], *entry['support']]:
            require(isinstance(name, str) and re.fullmatch(r'src/[a-z][a-z0-9_]*\.(adb|ads)', name),
                    'invalid executable source identity')
            names.add((base / name).as_posix())
        require(entry['main'].endswith('.adb') and entry['main'] not in entry['support'] and
                entry['executable'] == PurePosixPath(entry['main']).stem,
                'executable/main disagreement')
        mains.append(entry['main'])
        require(isinstance(entry['cases'], list) and entry['cases'], 'missing declarative run cases')
        for case in entry['cases']:
            require(isinstance(case, dict) and set(case) == CASE and identity(case['id']) and
                    isinstance(case['configuration'], str) and case['configuration'] and
                    case['provider'] in ('normal', 'missing') and type(case['exit']) is int and
                    case['exit'] in (0, 1) and isinstance(case['expected'], list) and case['expected'] and
                    all(isinstance(v, str) and v for v in case['expected']), 'invalid declarative run case')
            cases.append(case['id'])
    require(len(ids) == len(set(ids)) and len(mains) == len(set(mains)) and
            len(cases) == len(set(cases)) and
            not set(mains) & {s for e in manifest['examples'] for s in e['support']},
            'duplicate or ambiguous example ownership')
    # Only literal GPR lists confer source ownership. No GPR evaluation occurs.
    project = re.sub(r'--[^\n]*', '', source(config, block['project']).decode('utf-8'))
    require(not re.search(r'\b(extends|case|Source_Files|Excluded_Source_Files|Source_List_File|'
                          r'Excluded_Source_List_File|Locally_Removed_Files)\b', project, re.I),
            'unsupported example project')
    def values(attribute):
        matches = re.findall(r'\bfor\s+' + attribute + r'\s+use\s*\(([^;]*)\)\s*;', project, re.I)
        require(len(matches) == 1 and re.fullmatch(r'\s*"[^"\n]+"(?:\s*,\s*"[^"\n]+")*\s*', matches[0]),
                'nonliteral or ambiguous GPR source identity')
        return re.findall(r'"([^"\n]+)"', matches[0])
    require(Counter(values('Main')) == Counter(PurePosixPath(m).name for m in mains),
            'manifest/GPR main disagreement')
    directories = values('Source_Dirs')
    require(len(directories) == len(set(directories)) and all(
            re.fullmatch(r'[a-z][a-z0-9_/-]*', d) and '..' not in d.split('/') for d in directories),
            'unsafe or duplicate GPR source directory')
    actual = set()
    for directory in directories:
        folder = inside(config.root, (PurePosixPath(block['project']).parent / directory).as_posix())
        require(not any(p.is_symlink() for p in (folder, *folder.parents)) and folder.is_dir(),
                'invalid GPR source directory')
        for path in folder.iterdir():
            name = path.relative_to(config.root).as_posix()
            source(config, name)
            require(name not in actual, 'ambiguous GPR source ownership')
            actual.add(name)
    require(actual == names, 'unlisted or missing executable source')
    # Bind public source bytes too, rather than relying on output-side metadata.
    return names | {block['manifest'], block['project']} | {
        p.path.relative_to(config.root).as_posix() for p in public_sources.values()}


class Blocks:
    def __init__(self, config, data, native):
        from .source_references import References
        self.config, self.data, self.native = config, data, native
        self.block = data['source_blocks']
        self.base = PurePosixPath(self.block['manifest']).parent
        self.entries = json.loads(source(config, self.block['manifest']), object_pairs_hook=unique)['examples']
        self.references = References(config, native)
        self.rows = self.catalog()
        self.generated = {}
        self.generated[self.block['guide']] = {
            '{{example:' + e['id'] + '}}': self.example(e) for e in self.entries}
        self.generated[self.block['catalog_guide']] = {
            '{{public-symbol-index}}': self.catalog_html(('stable',)),
            '{{example-usage-index}}': self.catalog_html(('additional', 'operation'))}

    def listing(self, name):
        value = source(self.config, (self.base / name).as_posix()).decode('utf-8')
        return ('<p>Complete canonical source: <code>' + html.escape((self.base / name).as_posix()) +
                '</code></p><pre><code data-example-source="' + html.escape(name) + '">' +
                annotate(value, self.references.occurrences(value, name)) + '</code></pre>')

    def example(self, entry):
        output = self.listing(entry['main'])
        for name in entry['support']:
            output += '<details><summary>Supporting source: ' + html.escape(name) + '</summary>'
            output += self.listing(name) + '</details>'
        output += '<h3>Run cases (from repository root)</h3>'
        for case in entry['cases']:
            output += '<p>Mock configuration: <code>' + html.escape(case['configuration']) + '</code></p>'
            output += '<pre><code>sh ' + self.base.as_posix() + '/run.sh ' + case['id'] + '</code></pre>'
            output += '<p>Expected process exit: ' + str(case['exit']) + '; observable output:</p>'
            output += '<pre>' + html.escape('\n'.join(case['expected'])) + '</pre>'
        return output

    def catalog(self):
        stable = public_symbols(self.config, self.native)
        rows, uses, declarations = {}, {}, {}
        for entry in self.entries:
            for name in [entry['main'], *entry['support']]:
                value = source(self.config, (self.base / name).as_posix()).decode('utf-8')
                for record in self.references.occurrences(value, name):
                    if record['context'] not in ('type-mark', 'unique-operation'):
                        continue
                    dest = record['declaration']
                    key = record['identity']
                    declarations[key] = dest
                    uses.setdefault(key, set()).add(entry['id'])
        for canonical, dest in stable:
            rows[canonical.lower()] = (canonical, dest, 'stable')
        for key, dest in declarations.items():
            rows.setdefault(key, (dest.package + '.' + dest.declaration.name, dest,
                                  'additional' if dest.declaration.kind in ('type', 'subtype') else 'operation'))
        groups = {p.lower(): i for i, g in enumerate(self.data['groups']) for p in g['packages']}
        result = []
        for key, (canonical, dest, scope) in rows.items():
            result.append(dict(canonical=canonical, dest=dest, scope=scope,
                               examples=[e for e in self.entries if e['id'] in uses.get(key, set())]))
        result.sort(key=lambda r: (SCOPES.index(r['scope']), groups[r['dest'].package.lower()],
                                  r['dest'].package.lower(), r['dest'].declaration.line, r['canonical'].lower()))
        require(len({r['dest'].href for r in result}) == len(result), 'duplicate catalog destination')
        return result

    def catalog_html(self, scopes):
        output = ''
        for scope in scopes:
            i = SCOPES.index(scope)
            output += '<section id="' + IDS[i] + '"><h2>' + TITLES[i] + '</h2>'
            for group in self.data['groups']:
                rows = [r for r in self.rows if r['scope'] == scope and r['dest'].package in group['packages']]
                if not rows:
                    continue
                output += '<h3>' + html.escape(group['label']) + '</h3>'
                for owner in sorted({r['dest'].package for r in rows}, key=str.lower):
                    output += '<h4><code>' + html.escape(owner) + '</code></h4><ul>'
                    for row in rows:
                        dest = row['dest']
                        if dest.package != owner:
                            continue
                        kind = dest.declaration.kind
                        output += ('<li data-catalog-entry="' + html.escape(row['canonical'], quote=True) +
                                   '" data-kind="' + kind + '" data-scope="' + scope + '">')
                        output += ('<a href="../api/' + dest.href + '"><code>' + html.escape(row['canonical']) +
                                   '</code></a> — ' + kind.capitalize() + '.')
                        if row['examples']:
                            output += ' Used in: ' + ', '.join('<a href="' + e['guide'].removeprefix('guides/') +
                                      '">' + html.escape(e['title']) + '</a>' for e in row['examples']) + '.'
                        else:
                            output += ' No verified example use.'
                        output += '</li>'
                    output += '</ul>'
            output += '</section>'
        return output

    def expand(self, text, page):
        expected = self.generated.get(page, {})
        tokens = TOKEN.findall(text)
        require(Counter(tokens) == Counter(expected.keys()), 'missing, duplicate or misplaced source block token')
        # Source cannot forge even syntactically valid generated annotations.
        check_html(text)
        token_context(text, expected.keys())
        for entry in self.entries if page == self.block['guide'] else ():
            section = re.search(r'<section id="' + re.escape(entry['id']) + r'">(.*?)</section>', text, re.S)
            require(section is not None and section[1].count('{{example:' + entry['id'] + '}}') == 1 and
                    all('{{package:' + p + '}}' in section[1] for p in entry['packages']),
                    'wrong example section ownership')
        for token, block in expected.items():
            text = text.replace(token, block)
        return text

    def check(self, text, page):
        # Remove only exact independently generated blocks once, then apply the
        # unchanged schema-2 allowlist to everything authored by the consumer.
        for block in self.generated.get(page, {}).values():
            require(text.count(block) == 1, 'altered or duplicated source/catalog block')
            text = text.replace(block, '', 1)
        check_html(text)