"""Explicit synthetic authority tests; live publisher acceptance is separate."""
import json
from pathlib import Path
import shutil
import unittest
from dataclasses import replace
from unittest.mock import patch

from _helper import Fixture, FIXTURES
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.external_symbols import canonical_url, qualified, verify_publication
from ada_gnatdoc_enhancer.external_types import destinations
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json, local_link


class ExternalSymbols(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture('core'); self.addCleanup(self.fx.cleanup)
        self.root = self.fx.root
        shutil.copytree(FIXTURES/'core/src', self.root/'publisher/src')
        shutil.copytree(FIXTURES/'core/_site', self.root/'native')
        shutil.copytree(self.root/'native', self.root/'published')
        router = Path(__file__).parent/'real-fixtures/external-symbols/core-router-v1.js'
        shutil.copyfile(router, self.root/'publisher/router.js')
        shutil.copyfile(router, self.root/'published/api/gnatdoc-navigation.js')
        config = load(self.root, 'project.toml')
        from ada_gnatdoc_enhancer.native_html import snapshot
        from ada_gnatdoc_enhancer.symbols import public_symbols
        symbols = sorted(public_symbols(replace(config, symbol_bookmarks=True, default_package='OpenCV.Core'),
                                        snapshot(config, self.root/'native')), key=lambda x: x[0].lower())
        index = self.root/'published/api/index.html'
        self.metadata = '<div id="type-navigation" hidden>'+''.join(
            f'<a href="{d.href}" data-symbol="{n}"></a>' for n, d in symbols)+'</div>'
        index.write_text(index.read_text()+self.metadata)
        self.base = 'https://core.invalid/api/'
        self.direct = {n.lower(): self.base+d.href for n, d in symbols}
        revision = 'a'*40
        spec = dict(schema_version=1, repository='https://github.com/Example/Publisher', revision=revision,
                    gnatdoc='GNATdoc 26.0.0 (20260415)', source_sha256=hashes(self.root/'publisher'),
                    pristine_sha256=hashes(self.root/'native'),
                    public_sources=sorted('src/'+p.name for p in (self.root/'publisher/src').glob('*.ads')),
                    configuration='schema_version=1\nproject="Publisher"\n[sources]\ndirectories=["qualification-public"]\n')
        self.write('input.json', spec)
        run = dict(id=12, head_sha=revision, conclusion='success', status='completed',
                   repository=dict(html_url=spec['repository']), html_url=spec['repository']+'/actions/runs/12')
        self.write('run.json', run)
        self.write('deployment.json', dict(id=23, sha=revision, environment='github-pages',
            repository_url='https://api.github.com/repos/Example/Publisher',
            url='https://api.github.com/repos/Example/Publisher/deployments/23'))
        self.write('statuses.json', dict(statuses=[dict(state='success', log_url=run['html_url']+'/job/45',
            environment_url='https://core.invalid/')]))
        artifacts = [dict(id=i, digest='sha256:'+'b'*64, name=n,
                          workflow_run=dict(id=12, head_sha=revision))
                     for i, n in [(34, 'ada-api-'+revision), (35, 'github-pages')]]
        self.write('artifacts.json', dict(artifacts=artifacts))
        self.record = dict(schema_version=1, profile='core-symbol-router-v1', base_url=self.base,
            acquisition=self.pin('input.json'), source='publisher', native='native', publication='published',
            publication_sha256=hashes(self.root/'published'), router_source='router.js',
            provenance={k:self.pin(k+'.json') for k in ('run','deployment','statuses','artifacts')},
            artifacts={k:dict(id=i,digest='sha256:'+'b'*64) for k,i in [('review',34),('pages',35)]})
        self.config = replace(config, externals=self.direct, allowed_hosts=frozenset({'core.invalid'}),
                              external_type_target='_top')
        self.save()

    def write(self, name, value):
        (self.root/name).write_text(sorted_json(value))

    def pin(self, name):
        return dict(path=name, sha256=digest((self.root/name).read_bytes()))

    def save(self, names=None):
        self.write('record.json', self.record)
        options = dict(qualification='record.json',sha256=self.pin('record.json')['sha256'],
                       types=names or ['OpenCV.Core.Mat'])
        self.config = replace(self.config, external_symbol_bookmarks=options)

    def reject(self):
        with self.assertRaises((ValueError, OSError)): destinations(self.config)

    def test_exact_source_canonical_url_and_mixed_selection(self):
        urls = destinations(self.config)
        self.assertEqual(urls['opencv.core.mat'], self.base+'index.html?package=OpenCV.Core&symbol=OpenCV.Core.Mat')
        self.assertEqual(urls['opencv.core.float32_value'], self.direct['opencv.core.float32_value'])

    def test_ordinary_external_query_grammar_unchanged(self):
        p=self.root/'project.toml'
        p.write_text(p.read_text()+'\n[security]\nexternal_hosts=["core.invalid"]\n[external_types]\n"OpenCV.Core.Mat"="'+canonical_url(self.base,'OpenCV.Core','OpenCV.Core.Mat')+'"\n')
        with self.assertRaises(ValueError):load(self.root,'project.toml')

    def test_opt_in_configuration_and_top_requirement(self):
        p=self.root/'project.toml';text=p.read_text()
        suffix='\n[external_symbol_bookmarks]\nqualification="record.json"\nsha256="'+self.pin('record.json')['sha256']+'"\ntypes=["OpenCV.Core.Mat"]\n'
        p.write_text(text+suffix)
        with self.assertRaisesRegex(ValueError,'_top'):load(self.root,'project.toml')
        p.write_text(text+'\nexternal_type_target="_top"\n'+suffix)
        self.assertEqual(load(self.root,'project.toml').external_symbol_bookmarks['types'],['OpenCV.Core.Mat'])
        for bad in ('types=[]', 'types=["OpenCV.Core.Mat","opencv.core.mat"]', 'unknown=true'):
            p.write_text(text+'\nexternal_type_target="_top"\n'+suffix.replace('types=["OpenCV.Core.Mat"]',bad))
            with self.assertRaises(ValueError):load(self.root,'project.toml')

    def test_unqualified_private_generic_wrong_package_and_case(self):
        for name in ('Mat','opencv.core.mat','OpenCV.Other.Mat','OpenCV.Core.Hidden','OpenCV.Core.Vectors.Vector','OpenCV.Core.Element_Type'):
            self.save([name]);self.reject()

    def test_wrong_but_existing_native_destination(self):
        direct=dict(self.direct);direct['opencv.core.mat']=direct['opencv.core.float32_value']
        self.config=replace(self.config,externals=direct);self.reject()

    def test_missing_direct_authority(self):
        self.config=replace(self.config,externals={});self.reject()

    def test_missing_and_changed_qualification(self):
        p=self.root/'record.json';original=p.read_bytes()
        p.unlink();p.symlink_to(self.root/'input.json');self.reject();p.unlink();p.write_bytes(original)
        (self.root/'record.json').write_text('{}');self.reject()
        (self.root/'record.json').unlink();self.reject()

    def test_changed_source_hash(self):
        p=self.root/'publisher/src/opencv-core.ads';p.write_text(p.read_text()+'\n');self.reject()

    def test_missing_source_hash(self):
        spec=json.loads((self.root/'input.json').read_text());spec['source_sha256'].pop('src/opencv-core.ads')
        self.write('input.json',spec);self.record['acquisition']=self.pin('input.json');self.save();self.reject()

    def test_changed_native_fragment(self):
        p=next(p for p in (self.root/'native/api').glob('*.html') if 'Mat</h4>' in p.read_text())
        p.write_text(p.read_text()+' ');self.reject()

    def test_forged_symbol_index_even_when_publication_rehashed(self):
        p=self.root/'published/api/index.html';p.write_text(p.read_text().replace('data-symbol="OpenCV.Core.Mat"','data-symbol="OpenCV.Other.Mat"'))
        self.record['publication_sha256']=hashes(self.root/'published');self.save();self.reject()

    def test_wrong_valid_symbol_mapping_even_when_rehashed(self):
        p=self.root/'published/api/index.html';text=p.read_text();a=self.direct['opencv.core.mat'].removeprefix(self.base);b=self.direct['opencv.core.float32_value'].removeprefix(self.base)
        p.write_text(text.replace(f'href="{a}" data-symbol="OpenCV.Core.Mat"',f'href="{b}" data-symbol="OpenCV.Core.Mat"'))
        self.record['publication_sha256']=hashes(self.root/'published');self.save();self.reject()

    def test_changed_router_even_when_source_and_publication_rehashed(self):
        for name in ('publisher/router.js','published/api/gnatdoc-navigation.js'):
            p=self.root/name;p.write_text(p.read_text()+'\n')
        spec=json.loads((self.root/'input.json').read_text());spec['source_sha256']=hashes(self.root/'publisher');self.write('input.json',spec)
        self.record['acquisition']=self.pin('input.json');self.record['publication_sha256']=hashes(self.root/'published');self.save();self.reject()

    def test_provenance_source_deployment_artifact_mismatch(self):
        for name,key,value in [('run','head_sha','c'*40),('deployment','sha','c'*40),('deployment','environment','preview')]:
            with self.subTest(name=name,key=key):
                p=self.root/(name+'.json');original=p.read_bytes();data=json.loads(original);data[key]=value;self.write(p.name,data)
                self.record['provenance'][name]=self.pin(p.name);self.save();self.reject()
                p.write_bytes(original);self.record['provenance'][name]=self.pin(p.name)
        p=self.root/'artifacts.json';data=json.loads(p.read_bytes());data['artifacts'][0]['workflow_run']['head_sha']='c'*40
        self.write(p.name,data);self.record['provenance']['artifacts']=self.pin(p.name);self.save();self.reject()

    def test_unsupported_layout(self):
        self.record['profile']='unknown';self.save();self.reject()

    def test_base_url_security(self):
        for base in ('http://core.invalid/api/','https://evil.invalid/api/','https://u@core.invalid/api/',
                     'https://core.invalid:443/api/','https://core.invalid/%61pi/',
                     'https://core.invalid/../api/','https://core.invalid/api/?x=1','https://core.invalid/api/#x'):
            self.record['base_url']=base;self.save();self.reject()

    def test_canonical_url_rejects_injection_and_owner_substitution(self):
        for package,symbol in [('OpenCV.Other','OpenCV.Core.Mat'),('OpenCV.Core','OpenCV.Core.Mat&x=1'),
                               ('OpenCV.Core','OpenCV.Core.%4dat'),('OpenCV.Core','OpenCV.Core.Mat#x'),
                               ('OpenCV.Core','OpenCV.Core.Mat" onclick="evil')]:
            with self.assertRaises(ValueError):canonical_url(self.base,package,symbol)

    def test_only_exact_qualified_queries_pass_link_validation(self):
        url=destinations(self.config)['opencv.core.mat'];site=self.fx.site
        for bad in (url+'&x=1',url+'&symbol=OpenCV.Core.Mat',url+'&package=OpenCV.Core',url+'#x',
                    url.replace('Mat','%4Dat'),url.replace('package=','%70ackage='),
                    url.replace('?package=OpenCV.Core&symbol=','?symbol='),url.lower()):
            with self.assertRaises(ValueError):local_link(site/'api/index.html',site,bad,external=self.config.allowed_hosts,exact_external_symbols=frozenset({url}))
            if bad != url.lower():
                with self.assertRaises(ValueError):local_link(site/'api/index.html',site,bad,external=self.config.allowed_hosts,exact_external_symbols=frozenset({bad}))
        self.assertEqual(local_link(site/'api/index.html',site,url,external=self.config.allowed_hosts,exact_external_symbols=frozenset({url})),(None,''))

    def test_explicit_network_audit_all_files_and_redirect_drift(self):
        def fetch(url):return url,(self.root/'published'/url.removeprefix('https://core.invalid/')).read_bytes()
        self.assertEqual(len(verify_publication(self.config,fetch)),len(self.record['publication_sha256']))
        for wrong in (lambda u:('https://evil.invalid/',b''),lambda u:(u,b'changed')):
            with self.assertRaises(ValueError):verify_publication(self.config,wrong)

    def test_no_implicit_network_and_no_default_output_change(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            destinations(self.config)
        a=self.root/'one';b=self.root/'two';shutil.copytree(self.fx.site,a);shutil.copytree(self.fx.site,b)
        enhance(self.fx.config,a);enhance(replace(self.fx.config,external_symbol_bookmarks={}),b)
        self.assertEqual(hashes(a),hashes(b))

    def test_rendering_idempotence_and_rehashed_wrong_output(self):
        # Consumer public native identity is not modified; only its referenced
        # external type is opted in. The Imgproc synthetic fixture references Mat.
        consumer=Fixture('imgproc');self.addCleanup(consumer.cleanup)
        source=consumer.root/'src/opencv-image_processing.ads'
        source.write_text('with OpenCV.Core;\n'+source.read_text().replace('Source : Threshold_Mode','Source : OpenCV.Core.Mat'))
        for p in (consumer.site/'api').glob('*.html'):
            if 'Source : Threshold_Mode' in p.read_text():
                p.write_text(p.read_text().replace('Source : Threshold_Mode','Source : OpenCV.Core.Mat'))
        c=replace(self.config,sources=consumer.config.sources,expected_packages=consumer.config.expected_packages,
                  navigation=consumer.config.navigation,category_file='categories.json')
        shutil.copyfile(consumer.root/'docs/api-categories.json',self.root/'categories.json')
        shutil.rmtree(self.root/'src');shutil.copytree(consumer.root/'src',self.root/'src')
        enhance(c,consumer.site);verify(c,consumer.site);state=hashes(consumer.site)
        enhance(c,consumer.site);self.assertEqual(state,hashes(consumer.site))
        page=next(p for p in (consumer.site/'api').glob('*.html') if '?package=' in p.read_text())
        self.assertIn('data-type="opencv.core.mat" target="_top"',page.read_text())
        original=page.read_text();manifest=consumer.site/'api/presentation.json';data=json.loads(manifest.read_text())
        for change in ('&amp;symbol=OpenCV.Core.Float32_Value','&amp;symbol=OpenCV.Other.Mat',
                       '&amp;symbol=OpenCV.Core.Mat&amp;x=1'):
            page.write_text(original.replace('&amp;symbol=OpenCV.Core.Mat',change))
            data['output_sha256'][page.relative_to(consumer.site).as_posix()]=digest(page.read_bytes());manifest.write_text(sorted_json(data))
            with self.assertRaises(ValueError):verify(c,consumer.site)
        for attribute in (' target="_blank"',' target="_top" onclick="evil()"',' target="_top" target="_top"',''):
            page.write_text(original.replace(' target="_top"',attribute,1))
            data['output_sha256'][page.relative_to(consumer.site).as_posix()]=digest(page.read_bytes());manifest.write_text(sorted_json(data))
            with self.assertRaises(ValueError):verify(c,consumer.site)