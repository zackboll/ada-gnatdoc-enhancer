#!/usr/bin/env python3
"""Independent Core source/native bookmark audit, not a publication generator.

The unchanged, pinned Core oracle establishes ownership, complete declaration
profiles and native anchors. Candidate metadata and presentation.json never
grant authority. Run only against a disposable Core checkout. This tool also
reports legacy type-reference differences; symbol parity is NOT migration
parity. The shared verifier is an additional check, not this oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
PINS = {'26bf5e2e8151cb0545b928b72d3d87677543c1ae',
        'f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'}


def require(condition, reason):
    if not condition:
        raise ValueError('independent symbol audit: '+reason)


def hashes(root):
    require(root.is_dir(), 'missing input directory')
    result = {}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), 'symlink input')
        if p.is_file():
            result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


class Index(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.symbols = []; self.default = []; self.active = False
        self.feed(text); self.close()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        require(len(values) == len(attrs), 'duplicate index attribute')
        if tag == 'div' and values.get('id') == 'type-navigation':
            require(set(values) == {'id', 'hidden', 'data-default-package'}, 'symbol metadata fields')
            self.default.append(values['data-default-package']); self.active = True
        elif self.active:
            require(tag == 'a' and set(values) == {'href', 'data-symbol'}, 'symbol metadata member')
            self.symbols.append((values['data-symbol'], values['href']))

    def handle_endtag(self, tag):
        if tag == 'div':self.active = False


def audit(core, pristine, candidate, legacy=None):
    revision = subprocess.check_output(['git', '-C', str(core), 'rev-parse', 'HEAD'], text=True).strip()
    require(revision in PINS, 'unsupported Core revision')
    require(not subprocess.check_output(['git', '-C', str(core), 'diff', 'HEAD', '--', 'src', 'scripts']),
            'modified source or oracle')
    before = hashes(pristine)
    # Import only the checked-in consumer oracle, not the candidate inventory.
    sys.path.insert(0, str(core/'scripts'))
    import link_gnatdoc_types as oracle
    from highlight_gnatdoc_ada import strip_highlighting
    sources = oracle.sources(core/'src')
    pages, targets = oracle.pages_and_targets(pristine/'api', sources)
    symbols = {}
    for identity, (filename, anchor) in sorted(targets.items()):
        owner, _, simple = identity.rpartition('.')
        declarations = [d for d in sources[owner].declarations if d['scope'].lower() == identity
                        and d['signature'].split()[0].lower() in ('type', 'subtype')]
        require(len(declarations) == 1, 'ambiguous source symbol')
        canonical_owner = re.search(r'\bpackage\s+([\w.]+)\s+is\b', sources[owner].code, re.I)[1]
        name = canonical_owner+'.'+declarations[0]['name']
        symbols[name] = filename+'#'+anchor
    index = Index((candidate/'api/index.html').read_text())
    require(index.default == ['OpenCV.Core'], 'default package authority')
    require(len(index.symbols) == len(set(n.lower() for n, _ in index.symbols)), 'duplicate symbols')
    require(dict(index.symbols) == symbols and len(index.symbols) == len(symbols),
            'forged, missing or swapped published symbol destination')
    sections = []
    for owner, (path, _, native_sections) in sorted(pages.items()):
        text = (candidate/'api'/path.name).read_text()
        require(re.findall(r'<h1>([^<]+)</h1>', text) ==
                re.findall(r'<h1>([^<]+)</h1>', path.read_text()), 'package owner changed')
        current = list(oracle.SECTION.finditer(text))
        require(len(current) == len(native_sections), 'native section count changed')
        for old, new in zip(native_sections, current):
            require((old[1], old[2]) == (new[1], new[2]), 'native declaration heading/fragment changed')
            code = oracle.plain(strip_highlighting(new[3]))
            require(code == old[3], 'native declaration profile changed')
            declaration = sources[owner].match(code)
            sections.append({'package':owner, 'page':path.name, 'anchor':old[1],
                             'name':old[2], 'source_scope':declaration['scope'],
                             'profile':html.unescape(code)})
        require('<script' not in text, 'JavaScript in native declaration page')
    manifest = json.loads((candidate/'api/presentation.json').read_text())
    native_html = {p.relative_to(pristine).as_posix():p.read_text() for p in (pristine/'api').glob('*.html')}
    require(manifest['original_api_html'] == native_html, 'forged pristine authority in manifest')
    require((candidate/'api/gnatdoc.css').read_bytes() == (pristine/'api/gnatdoc.css').read_bytes(),
            'native CSS changed')
    asset = Path(__file__).resolve().parents[1]/'src/ada_gnatdoc_enhancer/assets/gnatdoc-symbol-navigation.js'
    require((candidate/'api/gnatdoc-navigation.js').read_bytes() == asset.read_bytes(),
            'modified opt-in navigation JavaScript')
    result = {'core_revision':revision, 'public_packages':len(pages), 'native_sections':len(sections),
              'public_symbols':len(symbols), 'symbols':symbols, 'sections':sections,
              'pristine_sha256':before, 'candidate_sha256':hashes(candidate),
              'oracle_sha256':{p:hashlib.sha256((core/p).read_bytes()).hexdigest() for p in
                               ('scripts/link_gnatdoc_types.py','scripts/compare_gnatdoc_warnings.py',
                                'scripts/highlight_gnatdoc_ada.py')},
              'symbol_parity':True, 'migration_parity':False}
    if legacy:
        def links(site):
            # Legacy serializes same-document targets as #fragment; shared
            # emits page.html#fragment. Compare resolved destination identity,
            # not this non-semantic serialization difference.
            return Counter((p.name, m[2], p.name+m[1] if m[1].startswith('#') else m[1])
                           for p in (site/'api').glob('*.html')
                           for m in oracle.LINK.finditer(p.read_text()))
        original, shared = links(legacy), links(candidate)
        result['type_references'] = {'legacy':sum(original.values()), 'shared':sum(shared.values()),
            'missing':[{'page':p,'identity':n,'href':u,'count':c} for (p,n,u),c in sorted((original-shared).items())],
            'additional':[{'page':p,'identity':n,'href':u,'count':c} for (p,n,u),c in sorted((shared-original).items())]}
        result['migration_parity'] = original == shared
        guides = sorted(p.relative_to(legacy).as_posix() for p in (legacy/'guides').glob('*.html'))
        result['authored_guide_byte_parity'] = {n:(candidate/n).read_bytes() == (legacy/n).read_bytes() for n in guides}
    require(before == hashes(pristine), 'pristine input mutated during audit')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pristine', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--legacy', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'report already exists')
    report = audit(args.core.resolve(), args.pristine.resolve(), args.candidate.resolve(), args.legacy)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('core_revision','public_packages','native_sections',
                                          'public_symbols','symbol_parity','migration_parity')}))


if __name__ == '__main__':main()