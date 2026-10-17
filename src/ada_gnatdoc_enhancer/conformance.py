"""Offline reference-profile validation; no consumer clone/build/network access."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .config import load
from .pipeline import enhance,verify
from .util import digest,require

PROFILES=('core','imgproc','geometry','mel')


def tree_hashes(path):
    return {x.relative_to(path).as_posix():digest(x.read_bytes())
            for x in path.rglob('*') if x.is_file()}


def run(fixtures:Path|None=None):
    fixture_root=fixtures or Path(__file__).resolve().parents[2]/'tests/fixtures'
    fixture_root=fixture_root.resolve()
    results={}
    for profile in PROFILES:
        directory=fixture_root/profile
        require(directory.is_dir(),f"missing offline fixture {profile}: {directory}")
        with tempfile.TemporaryDirectory(prefix='gnatdoc-conformance-') as tmp:
            base=Path(tmp)
            states=[]
            for ix in ('first','second'):
                target=base/ix
                shutil.copytree(directory,target)
                config=load(target,'project.toml')
                result=enhance(config,target/'_site')
                confirmed=verify(config,target/'_site')
                require(result['public_packages']==confirmed['public_packages'],
                        'fixture counts changed between enhancement and validation')
                before=tree_hashes(target/'_site')
                enhance(config,target/'_site')
                require(before==tree_hashes(target/'_site'),f"idempotence failure: {profile}")
                states.append(before)
            require(states[0]==states[1],f"nondeterministic output: {profile}")
            results[profile]={'packages':result['public_packages'],
                              'linked_types':result['linked_types'],
                              'html_pages':result['html_pages'],
                              'deterministic':True,'idempotent':True,
                              'fixture':'synthetic native GNATdoc 26; NOT complete pinned site'}
    return {'profiles':results,'fully_pinned_consumer_sites':'not qualified in bootstrap'}
