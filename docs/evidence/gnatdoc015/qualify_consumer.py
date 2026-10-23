#!/usr/bin/env python3
"""Read-only replay of Imgproc PR #81's independent 586-occurrence oracle.

Requires the PR's retained genuine native/source/artifact acquisition. It never
builds or changes the consumer, approves migration, or treats Pages as immutable.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import os

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

IMGPROC = 'a4d4a2edbc7cae49cf07a6d1e9f753f8d833d569'
PROPOSAL = 'docs/evidence/gnatdoc009/r1/core-destination-proposal.json'


def compare_release(old, new):
    """Only the independently specified enhancer_version transition is allowed."""
    before = hashes(old); after = hashes(new)
    require(before.keys() == after.keys(), 'output membership drift')
    changed = [n for n in before if before[n] != after[n]]
    require(changed == ['api/presentation.json'], 'unexpected release output drift')
    a = json.loads((old/'api/presentation.json').read_text())
    b = json.loads((new/'api/presentation.json').read_text())
    require(a['enhancer_version'] == '0.1.0' and b['enhancer_version'] == '0.1.1',
            'unauthorized manifest version transition')
    a['enhancer_version'] = '0.1.1'
    require(a == b, 'manifest changed beyond release version')
    require(sorted_json(a).encode() == (new/'api/presentation.json').read_bytes(),
            'noncanonical candidate manifest bytes')
    return dict(changed=changed, only_enhancer_version_transition=True)


def qualify(args):
    output = args.output.resolve(); output.mkdir(exist_ok=False, parents=True)
    consumer = args.consumer.resolve(); retained = args.retained.resolve()
    require(subprocess.check_output(['git', '-C', str(consumer), 'rev-parse', 'HEAD'],
                                    text=True).strip() == IMGPROC, 'wrong Imgproc PR head')
    require(not subprocess.check_output(['git', '-C', str(consumer), 'status', '--porcelain']),
            'dirty consumer snapshot')
    identities = json.loads((Path(__file__).parents[1]/'gnatdoc014/consumer-oracle-identities.json').read_text())
    for name, expected in identities.items():
        require(digest((consumer/name).read_bytes()) == expected, 'changed consumer oracle: '+name)
    proposal_bytes = (consumer/PROPOSAL).read_bytes()
    require(proposal_bytes == subprocess.check_output(
        ['git', '-C', str(consumer), 'show', IMGPROC+':'+PROPOSAL]), 'modified consumer evidence')
    proposal = json.loads(proposal_bytes)
    require(proposal['occurrence_count'] == 586 and len(proposal['types']) == 14,
            'wrong independent census')
    core = retained/'core-release'; native = retained/'core-native'
    require(subprocess.check_output(['git', '-C', str(core), 'rev-parse', 'HEAD'],
                                    text=True).strip() == proposal['indexed_core_revision'],
            'wrong pinned Core revision')
    require({n: digest((core/n).read_bytes()) for n in proposal['core_source_sha256']} ==
            proposal['core_source_sha256'], 'retained Core source hash mismatch')
    require(hashes(native) == proposal['core_native_sha256'], 'retained Core native hash mismatch')
    sys.path.insert(0, str(consumer/'scripts'))
    import qualify_production_core_links as oracle
    import probe_core_candidate as incoming
    ledger, local = oracle.census(args.native, args.legacy_site, core)
    # Proposed URL/proof annotations are downstream of the unchanged census.
    require([{k: x[k] for k in ledger[0]} for x in proposal['occurrences']] == ledger,
            'consumer-owned occurrence reconstruction differs')
    require(local == proposal['legacy_local_occurrences'], 'legacy local oracle differs')
    proof = oracle.source_native_types(core, native, Counter(x['core_identity'] for x in ledger))
    for identity, item in proof.items():
        require(all(proposal['types'][identity][k] == v for k, v in item.items()),
                'source/native declaration proof changed: '+identity)
    members = oracle.artifact_members(retained/'core-artifact.zip')
    require(digest((retained/'core-artifact.zip').read_bytes()) ==
            'fd328d27efc3196b5861d11c73561c2d22451e2a0fcf2b6477d7c6e0f853cc37',
            'reviewed Core artifact ZIP identity changed')
    require({n: digest(b) for n, b in members.items()} == proposal['hosted_file_sha256'],
            'reviewed hosted artifact differs')
    for item in proposal['types'].values():
        require(digest(members[item['native_page']]) == item['hosted_page_sha256'],
                'reviewed target page differs')
    source = output/'source'
    shutil.copytree(retained/'candidate-verified/source', source)
    require((source/'qualification-public/opencv-image_processing.ads').read_bytes() ==
            (consumer/'src/opencv-image_processing.ads').read_bytes(), 'consumer source differs')
    require((source/'categories.json').read_bytes() == (consumer/'docs/api-categories.json').read_bytes(),
            'consumer operation categories differ')
    default = load(source, 'candidate.toml')
    require(default.externals == {k: v['url'] for k, v in proposal['types'].items()},
            'external mapping differs from independently reviewed destinations')
    (source/'top.toml').write_text((source/'candidate.toml').read_text().replace(
        '[presentation]', '[presentation]\nexternal_type_target = "_top"'))
    top = load(source, 'top.toml')
    counts = {}; outputs = {}
    for label, config in [('default', default), ('top', top), ('top-second', top)]:
        site = output/label; shutil.copytree(args.native, site)
        counts[label] = enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); require(before == hashes(site), 'not byte-idempotent')
        outputs[label] = before
    require(outputs['top'] == outputs['top-second'], 'fresh enhancement is nondeterministic')
    # Independent official released process; no source imports or HTML rewriting.
    baseline = output/'baseline'; shutil.copytree(args.native, baseline)
    program = '''import sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
c=load(Path(sys.argv[1]),'candidate.toml');p=Path(sys.argv[2]);enhance(c,p);verify(c,p)
'''
    environment = dict(os.environ); environment.pop('PYTHONPATH', None)
    official = args.official_python.resolve()
    subprocess.run([official, '-c', program, str(source), str(baseline)], check=True,
                   cwd=output, env=environment)
    default_comparison = compare_release(baseline, output/'default')
    require(hashes(baseline) == hashes(retained/'candidate-verified/first'),
            'official release no longer matches PR #81 candidate bytes')
    merged = output/'merged-top'; shutil.copytree(args.native, merged)
    subprocess.run([sys.executable, '-c', program.replace("'candidate.toml'", "'top.toml'"),
                    str(source), str(merged)], check=True, cwd=output,
                   env=dict(environment, PYTHONPATH=str(args.baseline_src.resolve())))
    opt_in_comparison = compare_release(merged, output/'top')
    reconciliation = incoming.reconcile(args.native, output/'top', proposal)
    targets = Counter(); locals_seen = 0
    for page in (output/'top/api').glob('*.html'):
        for section in incoming.SECTION.finditer(page.read_text()):
            for link in incoming.SnippetLinks(section[3]).links:
                if link['href'].startswith('https:'):
                    require(link['target'] == '_top', 'external link did not opt in')
                    targets[link['identity']] += 1
                else:
                    require(link['target'] is None, 'local link target changed'); locals_seen += 1
    require(sum(targets.values()) == 586 and len(targets) == 14 and locals_seen == 350,
            'unexpected top/local occurrence counts')
    from qualify_released_gnatdoc import Operations, expected_operations
    operations, _ = expected_operations(args.native/'api')
    require(Operations((output/'top/api/index.html').read_text()).links == operations
            and len(operations) == 329, 'operation destination drift')
    import check_doc_coverage as coverage
    items, missing, errors = coverage.check_site(output/'top', consumer)
    require(len(items) == 1596 and not missing and not errors, 'consumer documentation coverage drift')
    cli = Path(sys.executable).parent/'gnatdoc-enhancer'
    cli_result = subprocess.run([cli, 'verify', '--source-root', source, '--config', 'top.toml',
                                 '--site', output/'top'], cwd=output, env=environment,
                                text=True, capture_output=True, check=True)
    (output/'installed-cli-verify.json').write_text(cli_result.stdout)
    require(subprocess.check_output([cli, '--version'], text=True).strip() == '0.1.1',
            'wrong installed CLI version')
    delta = sorted(n for n in outputs['top'] if outputs['top'][n] != outputs['default'][n])
    pages = [n for n in delta if n.endswith('.html')]
    require(len(pages) == 1 and delta == sorted(pages+['api/presentation.json']), 'unexpected output delta')
    for name in pages:
        require((output/'top'/name).read_bytes().replace(b' target="_top"', b'') ==
                (output/'default'/name).read_bytes(), 'opt-in changed more than target attributes')
    (output/'proposal.json').write_bytes(proposal_bytes)
    report = dict(imgproc_head=IMGPROC, core_revision=proposal['indexed_core_revision'],
                  proposal_sha256=digest(proposal_bytes), retained_native_verified=True,
                  fresh_native_generation=False, consumer_modified=False, migration_approved=False,
                  default_v010_only_manifest_version=default_comparison,
                  merged_gnatdoc014_only_manifest_version=opt_in_comparison,
                  operations=len(operations), documented=len(items),
                  installed_module=__import__('ada_gnatdoc_enhancer').__file__,
                  opt_in_only_adds_target=True,
                  deterministic=True, byte_idempotent=True, counts=counts, delta=delta,
                  by_type=dict(targets), local_links_without_target=locals_seen,
                  reconciliation=reconciliation, outputs=outputs)
    (output/'qualification.json').write_text(sorted_json(report))
    print(sorted_json({k: v for k, v in report.items() if k not in ('outputs', 'reconciliation')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('consumer', 'retained', 'native', 'baseline-src', 'official-python', 'legacy-site', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    qualify(parser.parse_args())