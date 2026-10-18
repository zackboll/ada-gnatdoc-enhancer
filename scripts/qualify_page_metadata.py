#!/usr/bin/env python3
"""Requalify real consumer sites with GNATDOC-010 document metadata.

Starts from the reviewed GNATDOC-008B qualified workspaces (whose enhancer tree
equals main 53a3219), never mutates them, and rebuilds each pristine native
site from its hash-bound captured originals. For each consumer it enhances two
independent copies, verifies them, requires byte-idempotence, determinism,
pristine binding and native preservation, and proves that the ONLY change
from the predecessor publication is the authorized metadata: every non-API
file is byte-identical, and removing exactly the authorized metadata from
each API page yields the predecessor page byte for byte. Adversarial
mutations then run through the real verifier.
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.metadata import Document, strip_native_document
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import MANIFEST, document_titles, enhance, verify
from ada_gnatdoc_enhancer.qualification import bind_pristine, hashes, identities, preserve_native
from ada_gnatdoc_enhancer.util import digest, require, sorted_json
from ada_gnatdoc_enhancer.validation import Page, validate_files

REPOSITORY = Path(__file__).resolve().parents[1]
SITES = ('core', 'imgproc', 'geometry', 'mel', 'imgproc008')


def pristine_from(previous: Path, name: str, target: Path) -> str:
    old = previous/name/'first'
    manifest = json.loads((old/'_site'/MANIFEST).read_text())
    (target/'api').mkdir(parents=True)
    for path, text in manifest['original_api_html'].items():
        require(Path(path).parent == Path('api'), 'unexpected original path')
        (target/path).write_text(text)
    shutil.copyfile(old/'_site/api/gnatdoc.css', target/'api/gnatdoc.css')
    if name == 'imgproc008':
        require(hashes(target) == hashes(previous/name/'pristine'), 'Imgproc 008 native input mismatch')
        return '9ce22ae5ab70008e1147475a9e6d7baef82f1df0'
    spec = json.loads((REPOSITORY/f'docs/evidence/gnatdoc002/{name}-input.json').read_text())
    require(hashes(target) == spec['pristine_sha256'], 'historical native input mismatch')
    return spec['revision']


def links(site: Path) -> int:
    return sum(len(Page(p.read_text(encoding='utf-8')).links) for p in site.rglob('*.html'))


def negative(root: Path, config, titles: dict) -> dict:
    """Adversarial mutations of a verified copy; each must be rejected by verify."""
    site = root/'_site'
    page = sorted(n for n in titles if n != 'api/index.html')[0]
    other = next(n for n in sorted(titles) if n != page)
    text = (site/page).read_text()
    anchor = next(i for i in Page(text).ids if len(i) == 64)
    spec = next(iter(packages(config).values())).path
    title = html.escape(titles[page])
    cases = {
        'missing title': (site/page, text.replace('<title>' + title + '</title>', '', 1)),
        'empty title': (site/page, text.replace(title + '</title>', '</title>', 1)),
        'duplicate title': (site/page, text.replace('</title>', '</title><title>Copy</title>', 1)),
        'wrong package title': (site/page, text.replace(title, html.escape(titles[other]), 1)),
        'missing lang': (site/page, text.replace(' lang="en"', '', 1)),
        'wrong lang': (site/page, text.replace('lang="en"', 'lang="fr"', 1)),
        'conflicting charset': (site/page, text.replace('</head>', '<meta charset="iso-8859-1"></head>', 1)),
        'changed native anchor': (site/page, text.replace(anchor, '0' * 64)),
        'modified declaration code': (site/page, text.replace('<code>', '<code>-- injected\n', 1)),
        'injected script': (site/page, text.replace('</head>', '<script src="gnatdoc-navigation.js" defer></script></head>', 1)),
        'injected external URL': (site/page, text + '<a href="https://example.com/">x</a>'),
        'source modified after enhancement': (spec, spec.read_text() + '\n-- modified\n'),
    }
    manifest = json.loads((site/MANIFEST).read_text())
    manifest['output_sha256'][page] = '0' * 64
    cases['tampered presentation manifest'] = (site/MANIFEST, sorted_json(manifest))
    results = {}
    for label, (path, changed) in cases.items():
        original = path.read_bytes()
        require(changed.encode() != original, f'mutation did not change input: {label}')
        try:
            path.write_text(changed)
            try:
                verify(config, site)
            except (ValueError, OSError) as error:
                results[label] = {'rejected': True, 'reason': str(error)[:300]}
            else:
                raise ValueError(f'verifier accepted {label}')
            if path.suffix == '.html':
                # The document contract is checked independently of byte reconstruction.
                try:
                    validate_files(site, config, set(hashes(site)), titles=titles)
                except ValueError as error:
                    results[label]['independent_document_check'] = str(error)[:300]
                else:
                    results[label]['independent_document_check'] = 'not a document-metadata defect'
        finally:
            path.write_bytes(original)
    verify(config, site)
    return results


def qualify(previous: Path, name: str, workspace: Path) -> dict:
    old = previous/name/'first'
    old_hashes = hashes(old/'_site')
    pristine = workspace/name/'pristine'
    revision = pristine_from(previous, name, pristine)
    states, record = [], {'consumer_revision': revision}
    for copy in ('first', 'second'):
        root = workspace/name/copy
        shutil.copytree(old, root, ignore=shutil.ignore_patterns('_site'))
        shutil.copytree(pristine, root/'_site')
        config = load(root, 'qualification.toml')
        native = snapshot(config, pristine)
        result = enhance(config, root/'_site')
        state = hashes(root/'_site')
        record['publication'] = verify(config, root/'_site')
        enhance(config, root/'_site')
        require(hashes(root/'_site') == state, 'not byte-idempotent')
        bind_pristine(pristine, root/'_site')
        record['native_preservation'] = preserve_native(identities(pristine), root/'_site',
                                                        config=config, pristine=pristine)
        states.append(state)
    require(states[0] == states[1], 'two independent enhancements differ')
    site = workspace/name/'first/_site'
    titles = document_titles(config, native)
    changed = sorted(p for p in set(old_hashes) | set(states[0]) if old_hashes.get(p) != states[0].get(p))
    api = sorted(p for p in states[0] if p.startswith('api/') and p.endswith('.html'))
    require(set(old_hashes) == set(states[0]), 'publication inventory changed')
    require(changed == sorted(api + [MANIFEST]), f'unexpected publication changes: {changed}')
    for page in api:
        before = (old/'_site'/page).read_text(encoding='utf-8')
        after = (site/page).read_text(encoding='utf-8')
        require(strip_native_document(after, titles[page], page) == before,
                f'change beyond authorized metadata: {page}')
    documents = {p.relative_to(site).as_posix(): Document(p.read_text(encoding='utf-8'))
                 for p in site.rglob('*.html')}
    authored = sorted(p for p in documents if not p.startswith('api/'))
    record.update({
        'enhancement': {k: result[k] for k in ('files', 'html_pages', 'links')},
        'html_pages': len(documents),
        'titled_pages': sum(len(d.titles) == 1 for d in documents.values()),
        'lang_pages': sum(len(d.langs) == 1 and len(d.langs[0]) == 1 for d in documents.values()),
        'generated_titles_added': len(api), 'lang_added': len(api), 'charset_added': len(api),
        'author_pages_unchanged': len(authored),
        'author_titles': {p: documents[p].titles for p in authored},
        'api_titles': {p: titles[p] for p in api},
        'changed_files': changed, 'only_authorized_metadata': True,
        'local_links': {'predecessor': links(old/'_site'), 'current': links(site)},
        'deterministic': True, 'byte_idempotent': True, 'independent_reconstruction': True,
        'output_sha256': states[0]})
    require(record['local_links']['predecessor'] == record['local_links']['current'], 'link inventory changed')
    record['negative'] = negative(workspace/name/'first', config, titles)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True, help='GNATDOC-008B qualified workspaces')
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.workspace.exists() or args.output.exists():
        parser.error('workspace and evidence output must be new')
    args.workspace.mkdir(parents=True)
    args.output.mkdir(parents=True)
    previous = {name: hashes(args.previous/name/'first/_site') for name in SITES}
    report = {}
    for name in SITES:
        report[name] = qualify(args.previous, name, args.workspace)
        print(name, 'PASS', report[name]['html_pages'], 'pages,', report[name]['generated_titles_added'],
              'titles added', flush=True)
    require(previous == {name: hashes(args.previous/name/'first/_site') for name in SITES},
            'predecessor workspaces changed')
    (args.output/'consumer-metadata.json').write_text(sorted_json(report))


if __name__ == '__main__':
    main()
