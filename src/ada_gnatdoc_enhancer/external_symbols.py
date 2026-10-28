"""Offline, independently approved external bookmark selection.

Only the qualified Core-v1 router protocol is supported. The router fingerprint
is an implementation/layout capability gate, NOT authority for any Ada identity
or deployment. Consumer-owned hashed evidence supplies those independently.
No publisher code is executed and no network access occurs here.
"""
from __future__ import annotations

import re
import shutil
import tempfile
import tomllib
from dataclasses import replace
from pathlib import Path

from .external_types import base_url, inventory, read_json
from .util import QNAME, digest, inside, regular, require

CORE_V1_ROUTER = 'cba37439fa02e5b00e1f9de6648aca86ca3aaac61f2b8e01a45b8d99bf9ec497'


def canonical_url(base, package, symbol):
    """Construct, never normalize or decode, the source-owned canonical URL."""
    require(isinstance(package, str) and isinstance(symbol, str) and
            re.fullmatch(QNAME, package) and re.fullmatch(QNAME, symbol) and
            all(not part.endswith('_') and '__' not in part for part in symbol.split('.')) and
            symbol.rpartition('.')[0] == package,
            'invalid canonical external symbol owner/spelling')
    return base + 'index.html?package=' + package + '&symbol=' + symbol


def _pinned(root, entry):
    require(isinstance(entry, dict) and set(entry) == {'path', 'sha256'},
            'incomplete external symbol evidence reference')
    path = inside(root, entry['path'])
    require(all(not p.is_symlink() for p in (path, *path.parents)),
            'symlink external symbol evidence')
    require(digest(regular(path).read_bytes()) == entry['sha256'],
            'external symbol evidence hash mismatch')
    return path


def _provenance(root, record, spec):
    """Cross-check archived API observations, already bound by reviewed config.

    This is not a signature verifier or a claim that JSON authenticates itself.
    Acquisition and deployment observations need independent approval before
    their record hash is put into project-owned configuration.
    """
    proof = record['provenance']
    require(isinstance(proof, dict) and set(proof) == {'run', 'deployment', 'statuses', 'artifacts'},
            'incomplete publisher provenance')
    run, deployment, statuses, artifacts = (
        read_json(_pinned(root, proof[key])) for key in ('run', 'deployment', 'statuses', 'artifacts'))
    require(run.get('head_sha') == deployment.get('sha') == spec['revision'] and
            run.get('conclusion') == 'success' and run.get('status') == 'completed' and
            run.get('repository', {}).get('html_url') == spec['repository'] and
            deployment.get('environment') == 'github-pages',
            'publisher source/deployment provenance mismatch')
    require(type(deployment.get('id')) is int and deployment['id'] > 0 and
            type(run.get('id')) is int and run['id'] > 0,
            'invalid publisher deployment/workflow identity')
    repository_api = spec['repository'].replace('https://github.com/', 'https://api.github.com/repos/')
    require(deployment.get('repository_url') == repository_api and
            deployment.get('url') == repository_api + '/deployments/' + str(deployment['id']) and
            run.get('html_url') == spec['repository'] + '/actions/runs/' + str(run['id']),
            'publisher repository provenance mismatch')
    # statuses is wrapped as an object to retain strict duplicate-key parsing.
    require(any(s.get('state') == 'success' and
                s.get('log_url', '').startswith(run.get('html_url', '') + '/job/')
                and s.get('environment_url') == record['base_url'].removesuffix('api/')
                for s in statuses.get('statuses', [])), 'publisher deployment not successful for workflow')
    claims = record['artifacts']
    require(isinstance(claims, dict) and set(claims) == {'review', 'pages'},
            'missing immutable publisher artifacts')
    for kind, name in (('review', 'ada-api-' + spec['revision']), ('pages', 'github-pages')):
        claim = claims[kind]
        require(isinstance(claim, dict) and set(claim) == {'id', 'digest'}, 'invalid artifact identity')
        matches = [a for a in artifacts.get('artifacts', []) if a.get('id') == claim['id']]
        require(len(matches) == 1 and matches[0].get('name') == name and
                matches[0].get('digest') == claim['digest'] and
                isinstance(claim['digest'], str) and
                re.fullmatch('sha256:[a-f0-9]{64}', claim['digest']) and
                matches[0].get('workflow_run', {}).get('id') == run['id'] and
                matches[0].get('workflow_run', {}).get('head_sha') == spec['revision'],
                'publisher artifact provenance mismatch')


def qualified(config):
    """Rebuild full source/native symbols, then compare the publisher index."""
    from .config import load
    from .native_html import snapshot
    from .qualification import Identities, hashes, identities
    from .symbols import public_symbols

    options = config.external_symbol_bookmarks
    require(config.external_type_target == '_top', 'external symbol bookmarks require target _top')
    require(isinstance(options, dict) and set(options) == {'qualification', 'sha256', 'types'},
            'incomplete external symbol bookmark configuration')
    record = read_json(_pinned(config.root, {'path': options['qualification'], 'sha256': options['sha256']}))
    fields = {'schema_version', 'profile', 'base_url', 'acquisition', 'source', 'native',
              'publication', 'publication_sha256', 'router_source', 'provenance', 'artifacts'}
    require(set(record) == fields and record['schema_version'] == 1 and
            record['profile'] == 'core-symbol-router-v1', 'unsupported external publisher layout')
    base = base_url(record['base_url'], config.allowed_hosts)
    require(base.endswith('/api/'), 'publisher base must name the qualified API directory')
    spec = read_json(_pinned(config.root, record['acquisition']))
    require(not tomllib.loads(spec['configuration']).get('external_symbol_bookmarks'),
            'publisher acquisition cannot import external bookmarks')
    _provenance(config.root, record, spec)
    source = inside(config.root, record['source'])
    native = inside(config.root, record['native'])
    publication = inside(config.root, record['publication'])
    require(isinstance(record['publication_sha256'], dict) and record['publication_sha256'] and
            all(isinstance(sha, str) and re.fullmatch('[a-f0-9]{64}', sha)
                for sha in record['publication_sha256'].values()), 'invalid publisher file inventory')
    # Reuse the existing full dependency reconciliation; its output is NOT used
    # to invent unsupported members. public_symbols adds the stricter scope proof.
    exported = inventory(spec, source, native)
    require(hashes(publication) == record['publication_sha256'], 'qualified publisher bytes changed')
    router = regular(inside(source, record['router_source']))
    require(record['router_source'] in spec['source_sha256'] and
            digest(router.read_bytes()) == CORE_V1_ROUTER and
            (publication/'api/gnatdoc-navigation.js').read_bytes() == router.read_bytes(),
            'unqualified or changed publisher router')
    before, after = identities(native), identities(publication)
    require(before.keys() == after.keys(), 'publisher native page inventory changed')
    for name in before:
        require(all(before[name][k] == after[name][k] for k in ('package', 'declarations', 'signatures')),
                'publisher native declaration/profile changed')
    with tempfile.TemporaryDirectory(prefix='gde-external-symbols-') as temp:
        root = Path(temp)
        for name in spec['public_sources']:
            target = inside(root/'qualification-public', name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(regular(inside(source, name)), target)
        (root/'profile.toml').write_text(spec['configuration'], encoding='utf-8')
        profile = load(root, 'profile.toml')
        observed = snapshot(profile, native)
        # default_package is only needed by the local metadata generator; it
        # confers no authority on external package or type selection.
        profile = replace(profile, symbol_bookmarks=True,
                          default_package=next(iter(observed.pages.values())).package)
        symbols = sorted(public_symbols(profile, observed), key=lambda item: item[0].lower())
        entries = ''.join('<a href="' + d.href + '" data-symbol="' + n + '"></a>' for n, d in symbols)
        expected = '<div id="type-navigation" hidden>' + entries + '</div>'
        index = regular(publication/'api/index.html').read_text(encoding='utf-8')
        require(Identities(index).ids.count('type-navigation') == 1 and expected in index,
                'publisher symbol index differs from source/native inventory')
        return {n: {'package': n.rpartition('.')[0], 'stable': canonical_url(base, n.rpartition('.')[0], n),
                    'native': base + d.href} for n, d in symbols if n.lower() in exported['types']}


def select(config, direct):
    options = config.external_symbol_bookmarks
    names = options.get('types')
    require(isinstance(names, (list, tuple)) and names and all(isinstance(n, str) for n in names) and
            len({n.lower() for n in names}) == len(names), 'empty/duplicate external symbol selection')
    symbols = qualified(config)
    result = dict(direct)
    for name in names:
        require(name in symbols, 'external symbol lacks canonical public source identity')
        item = symbols[name]
        require(direct.get(name.lower()) == item['native'],
                'external stable/native destination identity mismatch')
        result[name.lower()] = item['stable']
    return result


def verify_publication(config, fetch):
    """Explicit network audit only; compare the COMPLETE approved inventory.

    fetch(url) must return (final_url, bytes); redirect substitutions fail closed.
    Mutable hosting still requires fresh independent review when it changes.
    """
    qualified(config)
    options = config.external_symbol_bookmarks
    record = read_json(_pinned(config.root, {'path': options['qualification'], 'sha256': options['sha256']}))
    base = record['base_url'].removesuffix('api/')
    checked = {}
    for name, sha in sorted(record['publication_sha256'].items()):
        inside(config.root, name)
        url = base + name
        final, content = fetch(url)
        require(final == url and digest(content) == sha, 'live publisher changed or redirected')
        checked[url] = sha
    return checked