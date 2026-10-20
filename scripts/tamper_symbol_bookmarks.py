#!/usr/bin/env python3
"""Observe real-site mutations, reject, restore and independently rehash each.

Run only in the GNATDOC-011 disposable workspace. Reports which independent
oracle and/or shared reconstruction rejected the observed mutation. Does not
silently credit the oracle for a production-verifier-only rejection.
"""
import argparse
import json
from pathlib import Path
import re

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from qualify_symbol_bookmarks import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('core','authority','pristine','candidate','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); config = load(args.authority,'qualification.toml')
    assert not args.output.exists()
    baseline = audit(args.core,args.pristine,args.candidate)
    before = hashes(args.candidate); inputs = hashes(args.pristine)
    index = args.candidate/'api/index.html'; text = index.read_text()
    links = re.findall(r'<a href="([a-f0-9]{64}\.html#[a-f0-9]{64})" data-symbol="([^"]+)"></a>',text)
    first, second = links[0], links[1]
    assert first != second
    a = '<a href="'+first[0]+'" data-symbol="'+first[1]+'"></a>'
    b = '<a href="'+second[0]+'" data-symbol="'+first[1]+'"></a>'
    manifest = args.candidate/'api/presentation.json'; data = json.loads(manifest.read_text())
    data['output_sha256']['api/index.html'] = '0'*64
    cases = {
        'invented public symbol':(index,text.replace(first[1],'OpenCV.Invented',1)),
        'private ownership confusion':(index,text.replace(first[1],'OpenCV.Core.Handle',1)),
        'unknown package owner':(index,text.replace(first[1],'Unknown.Owner.Type_Name',1)),
        'wrong existing native anchor':(index,text.replace(a,b,1)),
        'duplicate identity':(index,text.replace(a,a+a,1)),
        'missing symbol':(index,text.replace(a,'',1)),
        'generic formal':(index,text.replace(first[1],'OpenCV.Core.Vectors.Element_Type',1)),
        'synthetic summary':(index,text.replace(first[1],'OpenCV.Core.Float32_Vec2.Vector',1)),
        'unsafe absolute destination':(index,text.replace(first[0],'https://example.com/'+first[0],1)),
        'unsafe root destination':(index,text.replace(first[0],'/'+first[0],1)),
        'forged presentation manifest':(manifest,json.dumps(data)),
        'modified navigation JavaScript':(args.candidate/'api/gnatdoc-navigation.js','/* forged */'),
    }
    pages = sorted({x[0].split('#')[0] for x in links})
    page = args.candidate/'api'/pages[0]; other = args.candidate/'api'/pages[1]
    cases['swapped existing native pages'] = (page,other.read_text())
    profile = page.read_text()
    cases['mismatched native declaration'] = (page,profile.replace('<code>','<code>Injected ',1))
    source = sorted((args.authority/'public').glob('*.ads'))[0]
    cases['mismatched source declaration'] = (source,source.read_text().replace('type ','type Invented_',1))
    assert cases['mismatched source declaration'][1] != source.read_text()
    results = {}
    for label,(path,changed) in cases.items():
        saved = path.read_bytes(); assert saved != changed.encode(), label
        try:
            path.write_text(changed); assert path.read_bytes() == changed.encode()
            result = {'mutation_observed':True}
            try:verify(config,args.candidate)
            except (ValueError,OSError) as exc:result['shared_rejected'] = str(exc)
            else:raise ValueError('shared verifier accepted '+label)
            try:audit(args.core,args.pristine,args.candidate)
            except (ValueError,OSError) as exc:result['independent_rejected'] = str(exc)
            else:result['independent_rejected'] = False
            results[label] = result
        finally:path.write_bytes(saved)
        assert hashes(args.candidate) == before
        assert hashes(args.pristine) == inputs
        verify(config,args.candidate); restored = audit(args.core,args.pristine,args.candidate)
        assert restored['candidate_sha256'] == baseline['candidate_sha256']
        results[label]['restored_hashes_and_independent_audit'] = True
    enhance(config,args.candidate); assert hashes(args.candidate) == before
    args.output.write_text(json.dumps({'mutations':results,'byte_idempotent':True},indent=2,sort_keys=True)+'\n')
    print(len(results),'observed/rejected/restored')


if __name__ == '__main__':main()