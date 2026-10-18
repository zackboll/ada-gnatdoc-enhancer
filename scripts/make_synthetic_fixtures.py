#!/usr/bin/env python3
"""Regenerate compact *synthetic* GNATdoc 26 fixtures for four adapter shapes.

Package names and semantics are informed by pinned Apache-2.0 consumer code.
HTML filenames and anchors here are deliberately generated synthetic values,
NOT claims about production GNATdoc output or full-site conformance.
"""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/'tests/fixtures'

MEL=['AMS','AMS.MEL','AMS.MEL.Status','AMS.MEL.IR','AMS.MEL.IR.Channel','AMS.MEL.IR.Image','AMS.MEL.IR.Image.Metadata',
'AMS.MEL.IR.C2','AMS.MEL.IR.C2.Common','AMS.MEL.IR.C2.Metadata','AMS.MEL.IR.Health_Status',
'AMS.MEL.IR.Health_Status.Metadata','AMS.MEL.IR.Instrumentation','AMS.MEL.IR.Instrumentation.Metadata',
'AMS.MEL.IR.Track','AMS.MEL.IR.Track.Metadata','AMS.MEL.IR.Track.Updates','AMS.MEL.IR.Track.System_Data',
'AMS.MEL.RF','AMS.MEL.RF.Product_Rx','AMS.MEL.RF.Admin','AMS.MEL.RF.C2',
'AMS.MEL.RF.C2.Element_Groups','AMS.MEL.RF.C2.Data_Pipes','AMS.MEL.RF.C2.Interval_Status',
'AMS.MEL.RF.C2.Virtual_Aperture_Notifications','AMS.MEL.RF.C2.Virtual_Aperture_Queries',
'AMS.MEL.RF.C2.Local_Functions','AMS.MEL.RF.C2.Transmit_Power']

DATA={
'core':{
 'packages':{'OpenCV.Core':['type Mat is tagged limited private;', 'type Float32_Value is digits 6;',
                               'function Convert (Source : Mat) return Mat;'],
             'OpenCV.Core.Sparse':['type Sparse_Mat is limited private;',
                                    'function Convert (Source : OpenCV.Core.Mat) return Sparse_Mat;'],
             'OpenCV.Core.Vectors':[]},
 'mode':'packages','style':'leading'},
'imgproc':{
 'packages':{'OpenCV.Image_Processing':['type Threshold_Mode is (Binary, Binary_Inverted);',
                    'function Apply_Threshold (Source : Threshold_Mode) return Threshold_Mode;',
                    'function Match_Template (Source : Threshold_Mode) return Threshold_Mode;',
                    'function Match_Template (Source : Threshold_Mode; Scale : Natural) return Threshold_Mode;']},
 'mode':'operations','style':'leading'},
'geometry':{
 'packages':{'OpenCV.Geometry':['type Point_2D is record X, Y : Long_Float; end record;',
                               'function Transform (Value : Point_2D) return Point_2D;',
                               'type Float32_Point_Array is array (Positive range <>) of Point_2D;'],
             'OpenCV.Geometry.Subdiv2D':['type Subdivision is tagged limited private;',
                                        'function Locate (Point : OpenCV.Geometry.Point_2D) return Subdivision;']},
 'mode':'operations','style':'leading'},
'mel':{
 'packages':{name:[] for name in MEL},
 'mode':'packages','style':'trailing'}
}
DATA['mel']['packages'].update({
 'AMS.MEL':['type Provider_Version is private;', 'function API_Version (Value : Provider_Version) return Natural;'],
 'AMS.MEL.IR':['type Image_Stream is limited private;', 'function Is_Open (Object : Image_Stream) return Boolean;'],
 'AMS.MEL.IR.Image':['type Full_Frame is private;',
   'function Receive (Object : AMS.MEL.IR.Image_Stream; Timeout_Milliseconds : Natural := 0) return Full_Frame;'],
 'AMS.MEL.RF.C2':['type Virtual_Aperture is tagged limited private;',
   'function Is_Open (Object : Virtual_Aperture) return Boolean;'],
 'AMS.MEL.RF.C2.Virtual_Aperture_Queries':['type Status_Kind is (None, Operational, Degraded, Failed);',
   'function Query_Status (Object : AMS.MEL.RF.C2.Virtual_Aperture) return Status_Kind;']})

CATEGORIES={
'imgproc':{'version':1,'categories':[{'id':'thresholding','title':'Thresholding','declarations':['Apply_Threshold','Threshold_Mode']},
                                      {'id':'matching','title':'Template matching','declarations':['Match_Template']}]},
'geometry':{'version':1,'packages':[{'package':'OpenCV.Geometry','categories':[{'id':'geometry','title':'Transforms and points',
                            'declarations':['Point_2D','Transform','Float32_Point_Array']}]},
                    {'package':'OpenCV.Geometry.Subdiv2D','categories':[{'id':'subdiv','title':'Subdivision',
                            'declarations':['Subdivision','Locate']}]}]}}

def tag(x):return hashlib.sha256(('SYNTHETIC GNATDOC 26 '+x).encode()).hexdigest()

def h4(decl):
    text=decl.strip().rstrip(';')
    name=text.split()[1]
    name=name.split('(')[0]
    return (f'<h4 id={tag(decl)}>{html.escape(name)}</h4>'
            f'<pre class=ada-code-snippet><code>{html.escape(text,quote=False)}\n</code></pre>')

def safe_name(name):return name.lower().replace('.','-')+'.ads'

def fixture(name,data):
    root=BASE/name;src=root/'src';api=root/'_site/api';src.mkdir(parents=True,exist_ok=True);api.mkdir(parents=True,exist_ok=True)
    pages={}
    for package,decls in data['packages'].items():
        path=src/safe_name(package)
        # These declarations deliberately exercise only a subset of real APIs.
        parents=package.rpartition('.')[0]
        context=f'with {parents};\n' if parents and parents in data['packages'] else ''
        if package=='OpenCV.Core.Sparse': context='with OpenCV.Core;\n'
        if package=='OpenCV.Geometry.Subdiv2D':context='with OpenCV.Geometry;\n'
        if package=='AMS.MEL.IR.Image': context='with AMS.MEL.IR;\n'
        if package=='AMS.MEL.RF.C2.Virtual_Aperture_Queries':context='with AMS.MEL.RF.C2;\n'
        if package=='AMS.MEL.IR.Health_Status.Metadata':
            decls_for_source=decls+['package Status renames AMS.MEL.Status;']
        else:decls_for_source=decls
        body=context+f'package {package} is\n'+'\n'.join(f'   {decl}' for decl in decls_for_source)+f'\nend {package};\n'
        path.write_text(body)
        filename=tag(package)+'.html'
        text=(f'<!DOCTYPE html><html><link rel=stylesheet href=gnatdoc.css><body class=content><h1>{package}</h1>'
              f'<h2>Description</h2><p>Synthetic fixture for {package}</p>'+''.join(map(h4,decls))+'</body></html>\n')
        (api/filename).write_text(text)
        pages[package]=filename
    start='<!DOCTYPE html>\n<html class=main>\n<link rel=stylesheet href=gnatdoc.css><body class=main><div class=side-navigation><ul class=tab-bar><li class=tab><a href=#compilation-units>Compilation Units</a><li class=tab><a href=#tagged-types>Tagged Types</a></ul><div class=content-column><h2 id=compilation-units>Compilation Units</h2><ul>'
    nav=''.join(f'<li><a href={filename} target=document-content>{package}</a>' for package,filename in sorted(pages.items()))
    end='</ul><h2 id=tagged-types>Tagged types</h2><ul></ul></div></div><div class=document-content><iframe name=document-content></iframe></div>'
    (api/'index.html').write_text(start+nav+end+'\n')
    (api/'gnatdoc.css').write_text('/* Synthetic native GNATdoc stylesheet. */\n')
    cfg=['schema_version = 1',f'project = "{name.title()} synthetic conformance"',
         *(['renderer_exceptions = ["AMS.MEL.IR.Health_Status.Metadata.Status"]'] if name=='mel' else []),
         '[gnatdoc]','version = "26.0.0"','[sources]','directories = ["src"]',
         f'comment_style = "{data["style"]}"',
         'packages = [']
    cfg.extend('  '+json.dumps(n)+',' for n in data['packages'])
    cfg.extend([']','[navigation]',f'mode = "{data["mode"]}"'])
    if data['mode']=='operations':
        (root/'docs').mkdir(exist_ok=True)
        (root/'docs/api-categories.json').write_text(json.dumps(CATEGORIES[name],indent=2)+'\n')
        cfg.append('categories = "docs/api-categories.json"')
    cfg.extend(['[presentation]','theme = true','syntax_highlighting = true','type_links = true'])
    if name=='mel':
        cfg.extend(['[guides]','mode = "html"','manifest = "docs/site-map.json"'])
        guides=[{'id':i,'label':label,'path':'guides/'+i+'.html'} for i,label in [
            ('getting-started','Getting Started'),('architecture','Architecture'),
            ('ir-workflows','IR Workflows'),('rf-workflows','RF Workflows'),
            ('ownership-and-errors','Ownership and Errors'),('api-map','API Map')]]
        docs=root/'docs'; (docs/'guides').mkdir(parents=True,exist_ok=True)
        man={'schema_version':1,'home':'index.html','stylesheet':'assets/gnatdoc-guides.css','guides':guides}
        (docs/'site-map.json').write_text(json.dumps(man,indent=2)+'\n')
        (docs/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<title>AMS MEL synthetic fixture portal</title>'
           '<link rel="stylesheet" href="assets/gnatdoc-guides.css"></head><body>'
           '<a class="skip" href="#main">Skip to content</a><header>{{navigation}}</header>'
           '<main id="main"><h1>AMS MEL synthetic fixture portal</h1>{{package-directory}}'
           '<p>See {{package:AMS.MEL.IR}}.</p></main></body></html>\n')
        for g in guides:
            (docs/g['path']).write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<title>'+g['label']+' — AMS MEL synthetic fixture</title>'
            '<link rel="stylesheet" href="../assets/gnatdoc-guides.css"></head><body>'
            '<a class="skip" href="#main">Skip to content</a><header>{{navigation}}</header>'
            '<main id="main"><h1>'+g['label']+'</h1><p>Reference {{package:AMS.MEL.RF.C2}}.</p>'
            +('{{package-directory}}' if g['id']=='api-map' else '')+'</main></body></html>\n')
    (root/'project.toml').write_text('\n'.join(cfg)+'\n')
    (root/'PROVENANCE.md').write_text(
        '# Synthetic GNATdoc conformance fixture\n\n'
        'All GNATdoc output, page hashes and anchors in this fixture are SYNTHETIC,\n'
        'generated by scripts/make_synthetic_fixtures.py to reproduce the observed\n'
        'GNATdoc 26 HTML structure. They are not snapshots of a real GNATdoc run.\n'
        'Package names and selected APIs reflect the source repositories reviewed\n'
        'at the pinned SHAs in docs/source-implementation-matrix.md; simplified\n'
        'declarations are not authoritative source or ABI contracts.\n'
        'Full consumer-site qualification remains a separate adoption gate.\n')

for name,data in DATA.items():fixture(name,data)
print('Generated synthetic fixtures:', ', '.join(DATA))
