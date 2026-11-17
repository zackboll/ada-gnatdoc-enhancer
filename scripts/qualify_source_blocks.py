#!/usr/bin/env python3
"""Independent MEL oracle for GNATDOC-036, never a production rendering path.

Run only with an explicitly supplied trusted consumer checkout and fresh epoch
qualification. Consumer modules execute here, never inside the enhancer API.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ada_gnatdoc_enhancer.authored import render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.source_blocks import input_inventory
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

COMMIT = '039bd4f05be969f0f224747728dfbae5305ee29b'


def qualify(consumer, baseline, workspace, official_python):
    require(not workspace.exists(), 'qualification workspace must be fresh')
    workspace.mkdir(parents=True)
    root = workspace / 'source'
    root.mkdir()
    archive = subprocess.check_output(['git', '-C', str(consumer), 'archive', COMMIT])
    subprocess.run(['tar', '-x', '-C', str(root)], input=archive, check=True)
    sys.path[:0] = [str(root / 'docs/tools'), str(root / 'scripts')]
    import authored_html_pilot as pilot
    import api_catalog
    import example_sources
    import source_epoch
    from ada_examples import References
    from build_docs_portal import manifest, package_map, regular, render as original
    from check_doc_coverage import measure
    from validate_docs import validate

    epoch = json.loads((baseline / 'epoch.json').read_bytes())
    require(epoch['candidate_commit'] == COMMIT, 'wrong consumer source epoch')
    pristine = baseline / 'pristine'
    report = measure(pristine, root)
    require(report['native'] == epoch['native'], 'independent native evidence differs')
    validate(pristine, root, report['native'])
    references = References(root, pristine, ledger=report['native'])
    # The consumer enforces official wheel origin/content. Run its audit in that
    # interpreter, never patching its tool identity check to accept a candidate.
    import os
    environment = os.environ.copy()
    environment.pop('PYTHONPATH', None)
    program = '''import sys,json
from pathlib import Path
root,baseline=map(Path,sys.argv[1:])
sys.path[:0]=[str(root/'docs/tools'),str(root/'scripts')]
import source_epoch
from check_doc_coverage import measure
from ada_examples import References
site=baseline/'pristine'
report=measure(site,root)
references=References(root,site,ledger=report['native'])
print(json.dumps(source_epoch.verify_presentation(site,root,report,references,baseline/'published',deep=True)))
'''
    audit = json.loads(subprocess.check_output([str(official_python), '-c', program, str(root), str(baseline)],
                                              env=environment, cwd=workspace))
    require(audit == epoch['publication'], 'independent full publication reconstruction differs')
    site_map = manifest(root)
    packages = package_map(pristine, root, report['native'])
    portal = {}
    for name in [site_map['home'], *(e['path'] for e in site_map['guides']), site_map['stylesheet']]:
        text = regular(root / 'docs' / name)
        value = original(text, name, site_map, packages, root, references) if name.endswith('.html') else text
        portal[name] = value.encode()
        require(portal[name] == (pristine / name).read_bytes(), 'consumer portal reconstruction differs')
    (root / 'docs/gnatdoc-native-anchors.json').write_bytes(source_epoch.canonical(report['native']))
    data = pilot.contract(root, pristine, report)
    source_bytes = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    config = pilot.bind(root, data)
    native = snapshot(config, pristine)
    # Reuse the actual pilot's 18 cases unchanged, not a list of claimed passes.
    negatives = pilot.negative_cases(root, pristine, report, references, config, native, data, source_bytes)
    require(len(negatives) == 18 and all(r['rejected'] for r in negatives.values()), 'pilot negative regression')
    data['schema_version'] = 3
    data['source_blocks'] = dict(profile='executable-ada-catalog-v1', manifest='docs/examples/manifest.json',
                                project='docs/examples/ams_mel_doc_examples.gpr', guide='guides/examples.html',
                                catalog_guide='guides/api-map.html',
                                symbol_policy='stable-public-types-and-root-constants-v1',
                                use_policy='qualified-types-and-unique-operations-v1')
    data['inputs'].update({p: digest((root / p).read_bytes()) for p in input_inventory(config, data)})
    config = pilot.bind(root, data)
    output = render(config, native)
    require(output == portal, 'nine-output source/native parity failed')
    example_sources.verify_rendered(output['guides/examples.html'].decode(), root, references)
    catalog = api_catalog.verify(output['guides/api-map.html'].decode(), root, references)
    site = workspace / 'candidate'
    shutil.copytree(pristine / 'api', site / 'api')
    enhance(config, site)
    verify(config, site)
    first = hashes(site)
    enhance(config, site)
    require(first == hashes(site), 'non-idempotent source blocks')
    second = workspace / 'repeat'
    shutil.copytree(pristine / 'api', second / 'api')
    enhance(config, second)
    require(first == hashes(second), 'nondeterministic source blocks')
    reference = baseline / 'published'
    require(set(first) == set(hashes(reference)), 'complete output inventory differs')
    differences = [name for name in first if (site / name).read_bytes() != (reference / name).read_bytes()]
    require(differences == ['api/presentation.json'], 'unapproved native output difference')
    actual = json.loads((site / differences[0]).read_bytes())
    expected = json.loads((reference / differences[0]).read_bytes())
    require(actual.pop('authored_source_blocks')['inputs'] == data['inputs'], 'missing input identity')
    portal_hashes = {n: digest(b) for n, b in portal.items()}
    require({n: v for n, v in actual['output_sha256'].items() if n in portal_hashes} == portal_hashes,
            'incorrect portal output hashes')
    actual['output_sha256'] = {n: v for n, v in actual['output_sha256'].items() if n not in portal_hashes}
    require(expected['enhancer_version'] == '0.1.5' and actual['enhancer_version'] == '0.1.7',
            'unexpected official/candidate release version')
    actual['enhancer_version'] = expected['enhancer_version']
    require(actual == expected, 'unapproved presentation metadata difference')
    evidence = dict(source_commit=COMMIT, source_tree=subprocess.check_output(
        ['git', '-C', str(consumer), 'rev-parse', COMMIT + '^{tree}'], text=True).strip(),
        portal={n: dict(identical=True, sha256=digest(b)) for n, b in portal.items()},
        pilot_adversarial=negatives, native=report['native'], catalog=catalog,
        independent_audit=audit, output_sha256=first, deterministic=True, idempotent=True,
        permitted_changed_files=differences, permitted_manifest_fields=['enhancer_version', 'authored_source_blocks', 'output_sha256'])
    (workspace / 'evidence.json').write_text(sorted_json(evidence))
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--official-python', type=Path, required=True,
                        help='interpreter with the consumer-verified official v0.1.5 wheel')
    args = parser.parse_args()
    evidence = qualify(args.consumer.absolute(), args.baseline.absolute(), args.workspace.absolute(),
                       args.official_python.absolute())
    print(json.dumps({'portal': evidence['portal'], 'pilot_adversarial': len(evidence['pilot_adversarial']),
                      'permitted_changed_files': evidence['permitted_changed_files']}, indent=2))