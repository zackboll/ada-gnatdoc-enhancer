#!/usr/bin/env python3
"""Record reviewed pristine GNATdoc/source identity before opt-in publication.

The result is input evidence, not a published manifest. Keep it under source
control and independently review it with the exact GNATdoc acquisition.
"""
import argparse
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.source_view import owned
from ada_gnatdoc_enhancer.util import digest, require, site_root, sorted_json


def pin(root, config_path, site, output):
    config = load(root, config_path)
    site = site_root(site)
    require(not (site/'api/presentation.json').exists(), 'native evidence requires pristine GNATdoc input')
    native = snapshot(config, site)
    values = {'api/index.html': digest(native.index.encode('utf-8')),
              'api/gnatdoc.css': digest(native.original_css)}
    values.update({'api/'+p.path.name: digest(p.original.encode('utf-8')) for p in native.pages.values()})
    sources = {p.path.relative_to(config.root).as_posix(): digest(owned(
        config.root, p.path.relative_to(config.root).as_posix()).read_bytes())
        for p in packages(config).values()}
    raw = sorted_json(dict(schema_version=1, files=values, sources=sources)).encode()
    with output.open('xb') as stream: stream.write(raw)
    print('native_manifest_sha256 = "' + digest(raw) + '"')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    pin(a.source_root, a.config, a.site, a.output)