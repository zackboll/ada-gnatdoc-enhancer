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

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

IMGPROC = 'a4d4a2edbc7cae49cf07a6d1e9f753f8d833d569'
PROPOSAL = 'docs/evidence/gnatdoc009/r1/core-destination-proposal.json'


def qualify(args):
    output = args.output.resolve(); output.mkdir(exist_ok=False, parents=True)
    consumer = args.consumer.resolve(); retained = args.retained.resolve()
    require(subprocess.check_output(['git', '-C', str(consumer), 'rev-parse', 'HEAD'],
                                    text=True).strip() == IMGPROC, 'wrong Imgproc PR head')
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
    ledger, local = oracle.census(args.native, consumer/'_site', core)
    # Proposed URL/proof annotations are downstream of the unchanged census.
    require([{k: x[k] for k in ledger[0]} for x in proposal['occurrences']] == ledger,
            'consumer-owned occurrence reconstruction differs')
    require(local == proposal['legacy_local_occurrences'], 'legacy local oracle differs')
    proof = oracle.source_native_types(core, native, Counter(x['core_identity'] for x in ledger))
    for identity, item in proof.items():
        require(all(proposal['types'][identity][k] == v for k, v in item.items()),
                'source/native declaration proof changed: '+identity)
    members = oracle.artifact_members(retained/'core-artifact.zip')
    require({n: digest(b) for n, b in members.items()} == proposal['hosted_file_sha256'],
            'reviewed hosted artifact differs')
    for item in proposal['types'].values():
        require(digest(members[item['native_page']]) == item['hosted_page_sha256'],
                'reviewed target page differs')
    source = output/'source'
    shutil.copytree(retained/'candidate-verified/source', source)
    require((source/'qualification-public/opencv-image_processing.ads').read_bytes() ==
            (consumer/'src/opencv-image_processing.ads').read_bytes(), 'consumer source differs')
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
    # Independent origin/main process: no candidate monkey-patching or HTML rewriting.
    baseline = output/'baseline'; shutil.copytree(args.native, baseline)
    program = '''import sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
c=load(Path(sys.argv[1]),'candidate.toml');p=Path(sys.argv[2]);enhance(c,p);verify(c,p)
'''
    import os
    subprocess.run([sys.executable, '-c', program, str(source), str(baseline)], check=True,
                   cwd=output, env=dict(os.environ, PYTHONPATH=str(args.baseline_src.resolve())))
    require(hashes(baseline) == outputs['default'], 'v0.1.0 default output changed')
    require(outputs['default'] == hashes(retained/'candidate-verified/first'),
            'default no longer matches PR #81 candidate bytes')
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
                  default_v010_byte_identical=True, opt_in_only_adds_target=True,
                  deterministic=True, byte_idempotent=True, counts=counts, delta=delta,
                  by_type=dict(targets), local_links_without_target=locals_seen,
                  reconciliation=reconciliation, outputs=outputs)
    (output/'qualification.json').write_text(sorted_json(report))
    print(sorted_json({k: v for k, v in report.items() if k not in ('outputs', 'reconciliation')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('consumer', 'retained', 'native', 'baseline-src', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    qualify(parser.parse_args())