#!/usr/bin/env python3
"""Opt-in GNAT 16.1.0/LAL 26 mapping generator; not an installed entry point.

Run from a source checkout in the qualified private compiler environment.
Fresh ALIs are generated once per unit. No review authorization is required.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import replace
import importlib.metadata
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/gnatdoc032'))
import verifier as v

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.util import sorted_json
from ada_gnatdoc_enhancer.verified_examples import (CLASSIFICATION, destination_for,
                                                   fingerprint, native_identity)


def generate(root, project, sources, compiler, build, config_path, native_site, scenarios=(), presentation_root=None):
    root, project = root.resolve(), project.resolve()
    sources = sorted({s.resolve() for s in sources})
    config = replace(load(presentation_root or root, config_path), verified_examples={})
    source = packages(config)
    native = snapshot(config, native_site)
    symbols = defaultdict(list)
    for destinations in source_destinations(config, native, source).values():
        for target in destinations:
            symbols[target.package.lower() + '.' + target.declaration.name.lower()].append(target)
    receipt, pin = v.generate(root, project, sources, compiler, build, scenarios)
    evidence = v.Evidence(receipt, pin, root, project, scenarios)
    session = v.SelectionSession(project, root, scenarios)
    r = evidence.receipt
    # No absolute host paths or timings in portable output. Retain the local
    # pinned receipt alongside ALIs for full forensic reproduction.
    tools = {k: val for k, val in r['tools'].items() if k.endswith('_sha256') or k.endswith('_version')}
    project_inputs = {Path(k).relative_to(root).as_posix(): val for k, val in r['dependencies'].items()
                      if Path(k).is_relative_to(root)}
    project_inputs.update({k: val for k, val in r['snapshot'].items() if Path(k).suffix in {'.gpr', '.adc', '.cgpr'}})
    project_inputs.update({s.relative_to(root).as_posix(): v.digest(s) for s in sources})
    def portable(value):
        if isinstance(value, dict):
            return {k: portable(val) for k, val in value.items()}
        if isinstance(value, list):
            return [portable(val) for val in value]
        if isinstance(value, str):
            return value.replace(str(root), '$SOURCE').replace(str(build.resolve()), '$BUILD')
        return value
    import libadalang as lal
    # Raw ALI/object bytes embed source mtimes and sometimes build paths. Retain
    # those exact hashes in the local receipt, but fingerprint the parsed ALI
    # evidence for portable output so identical source bytes remain reproducible
    # after copying/checking out on another machine.
    ali_evidence = [[list(key), sorted({json.dumps(record, sort_keys=True) for record in records})]
                    for key, records in sorted(evidence.index.items())]
    provenance = {
        'compiler': fingerprint(tools),
        'libadalang': fingerprint({'version': importlib.metadata.version('libadalang'),
                                  'binding_sha256': v.digest(lal.__file__)}),
        'project': fingerprint({'inputs': project_inputs, 'scenarios': list(scenarios),
                                'configuration': portable(r['project_configuration'])}),
        'evidence': fingerprint({'snapshot': r['snapshot'], 'ali': ali_evidence,
                                  'dependencies': sorted(r['dependencies'].values())}),
        'ali': fingerprint(ali_evidence)}
    result = dict(schema_version=1, inputs=project_inputs, native_sha256=fingerprint(native_identity(native)),
                  provenance=provenance, mappings=[], skipped=[])
    for path in sources:
        name = path.relative_to(root).as_posix()
        text = path.read_bytes().decode('utf-8')
        # Enumerate compiler call references, not lexically inferred candidates.
        # Nonstatic subprogram references are retained as explicit skips too.
        keys = sorted(key for key, records in evidence.index.items() if key[0] == path.name and
                      any(rec['entity_type'] in {'V', 'U'} and rec['reference_type'] not in {'b', 'c', 't'}
                          for rec in records))
        for _, line, column in keys:
            occurrence = dict(file=name, line=line, column=column)
            try:
                selected, declaration, spec = session.select(occurrence)
                compared = evidence.compare(occurrence, selected)
                v.need(compared['status'] == 'COMPILER_IDENTITY_CONFIRMED', compared['status'],
                       compared.get('reason', 'compiler identity not confirmed'))
                v.need(spec is not None and declaration.kind_name == 'SubpDecl', 'UNSUPPORTED',
                       'only ordinary public subprogram declarations supported')
                identity = declaration.p_fully_qualified_name.lower()
                profile = declaration.text
                destination_for(selected, identity, profile, replace(config, root=root), source, symbols)
                start = sum(len(s) for s in text.splitlines(keepends=True)[:line - 1]) + column - 1
                token = re.match(r'[A-Za-z][A-Za-z0-9_]*', text[start:])
                v.need(token is not None, 'UNSUPPORTED', 'no exact callee token')
                result['mappings'].append(dict(schema_version=1, source=dict(file=name, sha256=v.digest(path)),
                    occurrence=dict(line=line, column=column, start=start, end=start + len(token[0]), text=token[0]),
                    selected=selected, compiler_selected=compared['compiler_selected'],
                    identity=identity, profile=profile, classification=CLASSIFICATION,
                    evidence_sha256=fingerprint(provenance)))
            except Exception as exc:
                result['skipped'].append(dict(source=name, line=line, column=column,
                    status=getattr(exc, 'status', 'SOURCE_NATIVE_MISMATCH'), reason=str(exc)))
    # Detect edits during semantic/native processing too, not just compilation.
    v.need(r['snapshot'] == v.inventory(root), 'COMPILER_EVIDENCE_STALE', 'snapshot changed during mapping')
    v.need(result['native_sha256'] == fingerprint(native_identity(snapshot(config, native_site))),
           'SOURCE_NATIVE_MISMATCH', 'native snapshot changed during mapping')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'project', 'compiler', 'build', 'native-site', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--config', required=True, help='project-owned enhancer configuration relative to root')
    parser.add_argument('--presentation-root', type=Path, help='optional separate public-source publishing inventory')
    parser.add_argument('-X', action='append', default=[])
    args = parser.parse_args()
    try:
        result = generate(args.root, args.project, args.source, args.compiler, args.build,
                          args.config, args.native_site, args.X, args.presentation_root)
        v.need(not args.output.resolve().is_relative_to(args.root.resolve()), 'UNSUPPORTED',
               'output must be outside immutable compiler snapshot')
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(sorted_json(result))
        print(json.dumps({'output_sha256': v.digest(args.output), 'mappings': len(result['mappings']),
                          'skipped': len(result['skipped'])}))
        return 0
    except Exception as exc:
        print(json.dumps({'status': getattr(exc, 'status', 'ANALYSIS_ERROR'), 'reason': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())