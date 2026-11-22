#!/usr/bin/env python3
"""Record reviewed pristine GNATdoc/source identity before opt-in publication.

The result is input evidence, not a published manifest. Keep it under source
control and independently review it with the exact GNATdoc acquisition.
"""
import argparse
from dataclasses import replace
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.source_view import native_fingerprints, owned
from ada_gnatdoc_enhancer.util import digest, require, site_root, sorted_json


def pin(root, config_path, site, output, schema_version=1):
    config = load(root, config_path)
    site = site_root(site)
    require(not (site/'api/presentation.json').exists(), 'native evidence requires pristine GNATdoc input')
    require(schema_version in (1, 2), 'unsupported source evidence schema')
    if schema_version == 2:
        require(not config.source_view, 'pin with a configuration without [source_view]')
        from ada_gnatdoc_enhancer.body_sources import MODE, body_evidence, inventory, path_name
        require(all(not p.is_symlink() for p in (root.absolute(), *root.absolute().parents)),
                'symlink source-view root')
        require(output.absolute().is_relative_to(config.root) and not output.resolve().is_relative_to(site),
                'schema-2 evidence must be source-owned and outside the publication')
        path_name(config.root, output.absolute().relative_to(config.root).as_posix())
        require(all(not p.is_symlink() for p in output.absolute().parents), 'symlink evidence output path')
        config = replace(config, source_view={'schema_version': 2})
    native = snapshot(config, site)
    values = native_fingerprints(native)
    source = packages(config)
    data = dict(schema_version=schema_version, files=values)
    if schema_version == 2:
        from ada_gnatdoc_enhancer.metadata import check_native_input
        for name, text in [('api/index.html', native.index), *[
                ('api/' + p.path.name, p.original) for p in native.pages.values()]]:
            check_native_input(text, name)
        require(set(values) == {p.relative_to(site).as_posix() for p in (site/'api').rglob('*')
                               if p.is_file()}, 'unexpected pristine native API inventory')
        specs, bodies, _ = inventory(config, source)
        data.update(mode=MODE, sources=specs, bodies=body_evidence(source, bodies))
    else:
        data['sources'] = {p.path.relative_to(config.root).as_posix(): digest(owned(
            config.root, p.path.relative_to(config.root).as_posix()).read_bytes())
            for p in source.values()}
    raw = sorted_json(data).encode()
    with output.open('xb') as stream: stream.write(raw)
    print('native_manifest_sha256 = "' + digest(raw) + '"')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--schema-version', type=int, choices=(1, 2), default=1)
    a = p.parse_args()
    pin(a.source_root, a.config, a.site, a.output, a.schema_version)