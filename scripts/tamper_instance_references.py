#!/usr/bin/env python3
"""Observed R1 attacks on a dedicated non-browser copy, with full restoration.

Each case records the detecting layer. Source changes in the staged authority
are bound by hash qualification, not claimed detected by a separate immutable
consumer clone. Pristine mutations are checked against acquisition hashes and
must fail enhancement atomically. Installed code changes use an external hash
ledger rather than pretending a program can attest itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, bind_pristine
from qualify_symbol_bookmarks import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('core','authority','pristine','candidate','workspace','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--installed',type=Path,required=True)
    args = parser.parse_args(); args.workspace.mkdir(exist_ok=False)
    root = args.workspace/'authority';shutil.copytree(args.authority,root)
    pristine = args.workspace/'pristine';shutil.copytree(args.pristine,pristine)
    site = args.workspace/'site';shutil.copytree(args.candidate,site)
    config = load(root,'qualification.toml')
    originals = hashes(site); authorities = hashes(root); acquisition = hashes(pristine)
    audit(args.core,pristine,site,instance_references=True);verify(config,site)
    index = site/'api/index.html'; text = index.read_text()
    symbols = re.findall(r'<a href="([a-f0-9]{64}\.html#[a-f0-9]{64})" data-symbol="([^"]+)"></a>',text)
    refs = re.findall(r'<a href="([a-f0-9]{64}\.html#instance-members-summary)" data-instance="([^"]+)"></a>',text)
    assert len(refs)==25
    first,second = refs[:2];native,other = symbols[:2]
    symbol_a = '<a href="'+native[0]+'" data-symbol="'+native[1]+'"></a>'
    symbol_b = '<a href="'+other[0]+'" data-symbol="'+native[1]+'"></a>'
    instance_page = site/'api'/first[0].split('#')[0]
    instance_html = instance_page.read_text(); section = re.search(r'<section class="generic-instance-summary".*?</section>',instance_html,re.S)[0]
    source = root/'public/opencv-core-uint8_vec2.ads';source_text = source.read_text()
    caller = root/'public/opencv-core-uint8_vec2_access.ads';caller_text = caller.read_text()
    qualification = root/'generic.json';record = json.loads(qualification.read_text())
    settings = root/'qualification.toml';setting_text = settings.read_text()
    manifest = site/'api/presentation.json';manifest_data = json.loads(manifest.read_text())
    forged = json.loads(manifest.read_text());forged['output_sha256']['api/index.html']='0'*64
    pages = sorted({u.split('#')[0] for u,_ in symbols});page = site/'api'/pages[0];other_page = site/'api'/pages[1]
    cases = {}
    def add(label,path,changed,layer='enhancer reconstruction'):
        changed = changed.encode() if isinstance(changed,str) else changed
        assert changed!=path.read_bytes(),label
        cases[label]=(path,changed,layer)
    # Repeat all fifteen historical mutation classes, without editing original evidence.
    add('011 invented public symbol',index,text.replace(native[1],'OpenCV.Invented',1))
    add('011 private ownership confusion',index,text.replace(native[1],'OpenCV.Core.Handle',1))
    add('011 unknown package owner',index,text.replace(native[1],'Unknown.Owner.Type_Name',1))
    add('011 wrong existing native anchor',index,text.replace(symbol_a,symbol_b,1))
    add('011 duplicate identity',index,text.replace(symbol_a,symbol_a+symbol_a,1))
    add('011 missing symbol',index,text.replace(symbol_a,'',1))
    add('011 generic formal',index,text.replace(native[1],'OpenCV.Core.Vectors.Element_Type',1))
    add('011 synthetic summary promoted',index,text.replace(native[1],'OpenCV.Core.Float32_Vec2.Vector',1))
    add('011 unsafe absolute destination',index,text.replace(native[0],'https://example.com/'+native[0],1))
    add('011 unsafe root destination',index,text.replace(native[0],'/'+native[0],1))
    add('011 forged presentation manifest',manifest,json.dumps(forged))
    add('011 modified navigation JavaScript',site/'api/gnatdoc-navigation.js','/* forged */')
    add('011 swapped existing native pages',page,other_page.read_bytes())
    add('011 mismatched native declaration',page,page.read_text().replace('<code>','<code>Injected ',1))
    add('011 mismatched source declaration',source,source_text.replace('Length => 2','Length => 3'), 'source qualification')
    add('wrong generic qualification SHA',settings,setting_text.replace(config.generic_instances['sha256'],'0'*64), 'source qualification')
    add('modified instance declaration',source,source_text+'\n-- mutation\n','source qualification')
    add('altered actual type',source,source_text.replace('UInt8_Value','Int8_Value'),'source qualification')
    add('altered dimensions',source,source_text.replace('Length => 2','Length => 4'),'source qualification')
    add('wrong template owner',source,source_text.replace('OpenCV.Core.Vectors','OpenCV.Core.Fixed_Matrices'),'source qualification')
    add('wrong existing summary destination',index,text.replace(first[0],second[0],1))
    add('missing summary section',instance_page,instance_html.replace(section,''))
    add('duplicate summary anchor',instance_page,instance_html+section)
    add('modified summary HTML',instance_page,instance_html.replace('Instantiated Members','Forged Members'))
    add('forged instance-reference target',index,text.replace(first[1],'opencv.core.unapproved.vector',1))
    add('package alias substitution',caller,caller_text.replace('package OpenCV.Core.UInt8_Vec2_Access is',
        'package OpenCV.Core.UInt8_Vec2_Access is\n package Alias renames OpenCV.Core.UInt8_Vec2;'),'source qualification')
    add('local identifier shadowing',caller,caller_text.replace('package OpenCV.Core.UInt8_Vec2_Access is',
        'package OpenCV.Core.UInt8_Vec2_Access is\n UInt8_Vec2 : Integer;'),'source qualification')
    add('private context substitution',caller,caller_text.replace('with OpenCV.Core.UInt8_Vec2;','private with OpenCV.Core.UInt8_Vec2;'),'source qualification')
    add('limited context substitution',caller,caller_text.replace('with OpenCV.Core.UInt8_Vec2;','limited with OpenCV.Core.UInt8_Vec2;'),'source qualification')
    changed_record = json.loads(qualification.read_text());changed_record['instances']['opencv.core.uint8_vec2']['dimensions']=[5]
    add('unapproved generic instantiation',qualification,json.dumps(changed_record),'source qualification')
    add('synthetic member to native symbol',index,text.replace(native[1],'OpenCV.Core.UInt8_Vec2.Vector',1))
    other_instance = site/'api'/second[0].split('#')[0]
    add('swapped existing instance pages',instance_page,other_instance.read_bytes())
    existing_anchor = other[0]
    add('changed template member destination',instance_page,re.sub(r'(?<=href=")[a-f0-9]{64}\.html#[a-f0-9]{64}',existing_anchor,instance_html,count=1))
    results = {}
    for label,(path,changed,layer) in cases.items():
        print('observe:',label,flush=True)
        saved=path.read_bytes()
        try:
            path.write_bytes(changed);assert path.read_bytes()==changed
            observed={'mutation_observed':True,'layer':layer}
            try:verify(load(root,'qualification.toml'),site)
            except (ValueError,OSError) as exc:observed['rejected']=str(exc)
            else:raise ValueError('accepted '+label)
            if path.is_relative_to(site):
                try:audit(args.core,pristine,site,instance_references=True)
                except (ValueError,OSError) as exc:observed['independent_consumer_rejection']=str(exc)
                else:observed['independent_consumer_rejection']=False
            results[label]=observed
        finally:path.write_bytes(saved)
        assert hashes(site)==originals and hashes(root)==authorities and hashes(pristine)==acquisition
        verify(config,site);audit(args.core,pristine,site,instance_references=True)
        results[label]['restored_complete_hashes_and_independent_audit']=True
        print('restored:',label,flush=True)
    # Pristine/acquisition attacks: cannot be authorized by a publication manifest.
    native = pristine/'api'/first[0].split('#')[0]
    for label,changed in [('modified pristine native input',native.read_bytes()+b'forged'),
                          ('swapped native instance input',(pristine/'api'/second[0].split('#')[0]).read_bytes())]:
        saved=native.read_bytes(); raw=args.workspace/label.replace(' ','-');shutil.copytree(pristine,raw)
        try:
            native.write_bytes(changed);assert native.read_bytes()==changed and hashes(pristine)!=acquisition
            target=raw/'api'/native.name;target.write_bytes(changed);before=hashes(raw)
            try:enhance(config,raw)
            except (ValueError,OSError) as exc:reason=str(exc)
            else:raise ValueError('accepted '+label)
            assert hashes(raw)==before
            results[label]={'mutation_observed':True,'layer':'source/native qualification and acquisition hash binding',
                            'rejected':reason,'partial_output_absent':True}
        finally:native.write_bytes(saved)
        assert hashes(pristine)==acquisition and hashes(site)==originals
        audit(args.core,pristine,site,instance_references=True)
        results[label]['restored_complete_hashes_and_independent_audit']=True
    # External installed-code integrity gate: snapshot, mutate, observe rejection,
    # restore and verify; never assert that modified code can attest itself.
    installed=args.installed
    package=Path(subprocess.check_output([str(installed/'bin/python'),'-c',
        'import ada_gnatdoc_enhancer;print(ada_gnatdoc_enhancer.__path__[0])'],text=True,cwd=args.workspace).strip())
    installed_hashes=hashes(package)
    for relative in ['instance_references.py','assets/gnatdoc-instance-navigation.js']:
        path=package/relative;saved=path.read_bytes()
        try:
            path.write_bytes(saved+b'\n# tampered\n');assert path.read_bytes()!=saved
            assert hashes(package)!=installed_hashes
            results['altered installed '+relative]={'mutation_observed':True,'layer':'external installed module/asset hashes',
                'rejected':'installed package differs from trusted wheel module/asset ledger'}
        finally:path.write_bytes(saved)
        assert hashes(package)==installed_hashes
        results['altered installed '+relative]['restored_complete_hashes_and_independent_audit']=True
    # A forged acquisition record is rejected by the independently retained input
    # hashes, not credited to output verification.
    forged_acquisition=dict(acquisition);forged_acquisition[next(iter(forged_acquisition))]='0'*64
    assert forged_acquisition!=hashes(pristine)
    results['mismatched acquisition evidence']={'mutation_observed':True,'rejected':'source/native acquisition ledger hash mismatch',
        'layer':'independent acquisition evidence comparison','restored_complete_hashes_and_independent_audit':hashes(pristine)==acquisition}
    enhance(config,site);assert hashes(site)==originals
    args.output.write_text(json.dumps({'mutations':results,'byte_idempotent':True,'browser_workspace_untouched':True},indent=2,sort_keys=True)+'\n')
    print(len(results),'observed/rejected/restored attacks')


if __name__=='__main__':main()