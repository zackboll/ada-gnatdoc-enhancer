#!/usr/bin/env python3
"""Requalify real consumer sites with GNATDOC-010 document metadata.

Starts from the reviewed GNATDOC-008B qualified workspaces, never mutates them,
and rebuilds each pristine native site from its hash-bound captured originals.
The predecessor publication is regenerated from that pristine input by the
merged base enhancer installed separately (``--baseline-python``), so it
carries every reviewed base behavior, including GNATDOC-009A subtype-base
links; the base CLI must verify it. The delta from the historical 008B
publication to that predecessor must be exactly the recorded GNATDOC-009A
four-site delta. The current Geometry source that motivated GNATDOC-009A
(``--geometry-*``) is requalified the same way, with its verified Core
``OpenCV.Point_Array`` destination.

For each consumer it enhances two independent copies, verifies them, requires
byte-idempotence, determinism, pristine binding and native preservation, and
proves that the ONLY change from the predecessor publication is the authorized
metadata: every non-API file is byte-identical, and removing exactly the
authorized metadata from each API page yields the predecessor page byte for
byte. Adversarial mutations then run through the real verifier.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
from collections import Counter
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
SUBTYPE_EVIDENCE = REPOSITORY/'docs/evidence/gnatdoc009a/four-site.json'
GEOMETRY_SOURCE = '8690927853ffa74729206d8997b09046ad3d2246'
GEOMETRY_REPORT_SHA256 = '135204cc2702dcef99076f2350a290d5bfab908c09bb38818d367ad3b210ab28'
GEOMETRY_PAGE = 'api/4f90dae6ae3d13b7eca2073a4084d7aafc29ca4b1a5df10de478124a1cd77135.html'
POINT_ARRAY = ('subtype</span> Contour <span class="ada-keyword">is</span> <a class="type-reference" '
               'href="https://core.invalid/f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f/api/'
               'ea2ebcbc108269c77d7c6d44d2dabdfb5f6d0179ad5622b1be3cbceaee5c44aa.html'
               '#da696e09a1f1b297516365244e16533e23cca626f26df4bb3f727a64beb697b0" '
               'data-type="opencv.point_array">OpenCV.Point_Array</a>')


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


def external(site: Path) -> Counter:
    return Counter(link for p in site.rglob('*.html') for link in Page(p.read_text(encoding='utf-8')).links
                   if '://' in link)


def base_publication(python: str, inputs: Path, pristine: Path, root: Path) -> Path:
    """Predecessor publication: the separately installed base CLI enhances and verifies the pristine site."""
    shutil.copytree(inputs, root, ignore=shutil.ignore_patterns('_site', '__pycache__'))
    shutil.copytree(pristine, root/'_site')
    environment = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    for command in ('enhance', 'verify'):
        subprocess.run([python, '-I', '-m', 'ada_gnatdoc_enhancer', command, '--source-root', str(root),
                        '--config', 'qualification.toml', '--site', str(root/'_site')],
                       check=True, cwd=root, env=environment, stdout=subprocess.DEVNULL)
    return root/'_site'


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


def qualify(name: str, inputs: Path, pristine: Path, revision: str, python: str, workspace: Path) -> dict:
    old = base_publication(python, inputs, pristine, workspace/name/'predecessor')
    old_hashes = hashes(old)
    states, record = [], {'consumer_revision': revision}
    for copy in ('first', 'second'):
        root = workspace/name/copy
        shutil.copytree(inputs, root, ignore=shutil.ignore_patterns('_site', '__pycache__'))
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
        before = (old/page).read_text(encoding='utf-8')
        after = (site/page).read_text(encoding='utf-8')
        require(strip_native_document(after, titles[page], page) == before,
                f'change beyond authorized metadata: {page}')
    require((site/'api/gnatdoc.css').read_bytes() == (pristine/'api/gnatdoc.css').read_bytes(),
            'native stylesheet changed')
    documents = {p.relative_to(site).as_posix(): Document(p.read_text(encoding='utf-8'))
                 for p in site.rglob('*.html')}
    authored = sorted(p for p in documents if not p.startswith('api/'))
    record.update({
        'predecessor': 'base CLI enhance+verify of the same pristine input',
        'enhancement': {k: result[k] for k in ('files', 'html_pages', 'links')},
        'html_pages': len(documents),
        'titled_pages': sum(len(d.titles) == 1 for d in documents.values()),
        'lang_pages': sum(len(d.langs) == 1 and len(d.langs[0]) == 1 for d in documents.values()),
        'charset_pages': sum(len(d.charsets) == 1 for d in documents.values()),
        'generated_titles_added': len(api), 'lang_added': len(api), 'charset_added': len(api),
        'author_pages_unchanged': len(authored),
        'author_titles': {p: documents[p].titles for p in authored},
        'api_titles': {p: titles[p] for p in api},
        'changed_files': changed, 'only_authorized_metadata': True, 'native_css_unchanged': True,
        'local_links': {'predecessor': links(old), 'current': links(site)},
        'external_links': {'predecessor': sum(external(old).values()), 'current': sum(external(site).values()),
                           'identical': external(old) == external(site)},
        'deterministic': True, 'byte_idempotent': True, 'independent_reconstruction': True,
        'output_sha256': states[0]})
    require(record['local_links']['predecessor'] == record['local_links']['current'], 'link inventory changed')
    require(record['external_links']['identical'], 'external link inventory changed')
    require(record['titled_pages'] == record['lang_pages'] == record['charset_pages'] == len(documents),
            'page without title, language or charset')
    record['negative'] = negative(workspace/name/'first', config, titles)
    return record


def subtype_links(historical: Path, name: str, workspace: Path) -> dict:
    """The 008B -> base delta must be exactly the reviewed GNATDOC-009A delta, kept by the metadata."""
    old, base, site = historical/'_site', workspace/name/'predecessor/_site', workspace/name/'first/_site'
    before, after = hashes(old), hashes(base)
    delta = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    record = {'files_changed_by_base': delta}
    evidence = json.loads(SUBTYPE_EVIDENCE.read_text()).get(name)
    if evidence is not None:
        require(delta == evidence['changed_files'], 'base subtype delta differs from GNATDOC-009A evidence')
        occurrences = []
        for occurrence in evidence['added_occurrences']:
            page = next(p for p in delta if p.startswith('api/') and p.endswith('.html'))
            reference = f'<a class="type-reference" href="{html.escape(occurrence["href"])}"'
            counts = {k: (root/page).read_text(encoding='utf-8').count(reference)
                      for k, root in (('historical', old), ('base', base), ('combined', site))}
            require(counts['base'] == counts['combined'] > counts['historical'], 'subtype link not preserved')
            occurrences.append({'declaration': occurrence['declaration'], 'identity': occurrence['identity'],
                                'href': occurrence['href'], 'page': page, 'reference_counts': counts})
        record.update({'matches_gnatdoc009a_evidence': True, 'occurrences': occurrences})
    return record


def current_geometry(args, workspace: Path) -> dict:
    """The current Geometry source and its reviewed Core 0.5.0 Point_Array destination."""
    report = args.geometry_consumer/'docs/evidence/gnatdoc009/report.json'
    require(digest(report.read_bytes()) == GEOMETRY_REPORT_SHA256, 'Geometry acquisition authority changed')
    original = json.loads(report.read_text())
    inputs = args.geometry_inputs
    require(hashes(args.geometry_pristine) == original['pristine_sha256'] and
            digest((inputs/'qualification.toml').read_bytes()) == original['configuration_sha256'],
            'Geometry acquisition/configuration substitution')
    config = load(inputs, 'qualification.toml')
    for pkg in packages(config).values():
        relative = pkg.path.relative_to(inputs/'qualification-public').as_posix()
        expected = subprocess.check_output(['git', '-C', str(args.geometry_consumer), 'show',
                                            GEOMETRY_SOURCE + ':' + relative])
        require(pkg.path.read_bytes() == expected, 'current Geometry source substitution')
    record = qualify('geometry-current', inputs, args.geometry_pristine, GEOMETRY_SOURCE,
                     args.baseline_python, workspace)
    site = workspace/'geometry-current/first/_site'
    counts = {k: (root/GEOMETRY_PAGE).read_text(encoding='utf-8').count(POINT_ARRAY)
              for k, root in (('base', workspace/'geometry-current/predecessor/_site'), ('combined', site))}
    require(counts == {'base': 1, 'combined': 1}, f'Point_Array subtype destination changed: {counts}')
    record['subtype_links'] = {'declaration': 'Contour', 'identity': 'opencv.point_array', 'page': GEOMETRY_PAGE,
                               'reference': POINT_ARRAY, 'reference_counts': counts,
                               'publication': 'offline-test (core.invalid); not production hosting'}
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True, help='GNATDOC-008B qualified workspaces')
    parser.add_argument('--baseline-python', required=True,
                        help='Python with the merged base enhancer installed (not this checkout)')
    parser.add_argument('--geometry-consumer', type=Path, required=True, help='Geometry clone (read only)')
    parser.add_argument('--geometry-inputs', type=Path, required=True)
    parser.add_argument('--geometry-pristine', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.workspace.exists() or args.output.exists():
        parser.error('workspace and evidence output must be new')
    args.workspace.mkdir(parents=True)
    args.output.mkdir(parents=True)
    previous = {name: hashes(args.previous/name/'first/_site') for name in SITES}
    inputs = hashes(args.geometry_inputs), hashes(args.geometry_pristine)
    report = {}
    for name in SITES:
        pristine = args.workspace/name/'pristine'
        revision = pristine_from(args.previous, name, pristine)
        report[name] = qualify(name, args.previous/name/'first', pristine, revision,
                               args.baseline_python, args.workspace)
        report[name]['subtype_links'] = subtype_links(args.previous/name/'first', name, args.workspace)
        print(name, 'PASS', report[name]['html_pages'], 'pages,', report[name]['generated_titles_added'],
              'titles added', flush=True)
    report['geometry-current'] = current_geometry(args, args.workspace)
    print('geometry-current PASS', report['geometry-current']['html_pages'], 'pages,',
          report['geometry-current']['generated_titles_added'], 'titles added', flush=True)
    require(previous == {name: hashes(args.previous/name/'first/_site') for name in SITES},
            'predecessor workspaces changed')
    require(inputs == (hashes(args.geometry_inputs), hashes(args.geometry_pristine)), 'Geometry inputs changed')
    (args.output/'consumer-metadata.json').write_text(sorted_json(report))


if __name__ == '__main__':
    main()
