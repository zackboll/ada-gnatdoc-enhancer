"""Pinned evidence is independently reconstructed, including wrong-valid targets."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from _helper import FIXTURES, Fixture
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.external_types import (
    base_url, destinations, inventory, read_json, verify_published,
)
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.syntax import resolve
from ada_gnatdoc_enhancer.util import digest, sorted_json

OLD='386c5360ac51f2b62e522853d94290aec4ee14a0'
NEW='f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'


class ExternalEvidence(unittest.TestCase):
    def setUp(self):
        self.fixture=Fixture('geometry');self.addCleanup(self.fixture.cleanup)
        self.root=self.fixture.root
        self.source=self.root/'dependency'
        shutil.copytree(FIXTURES/'core'/'src',self.source/'src')
        self.site=self.root/'native'
        shutil.copytree(FIXTURES/'core'/'_site',self.site)
        names=['src/'+p.name for p in (self.source/'src').glob('*.ads')]
        configuration=(FIXTURES/'core'/'project.toml').read_text().replace('["src"]','["qualification-public"]')
        self.spec={'schema_version':1,'revision':OLD,
            'repository':'https://github.com/zackboll/opencv_core_ada',
            'gnatdoc':'GNATdoc 26.0.0 (20260415)','source_sha256':hashes(self.source),
            'pristine_sha256':hashes(self.site),'public_sources':sorted(names),
            'configuration':configuration}
        self.manifest=inventory(self.spec,self.source,self.site)
        self.dep={'repository':self.spec['repository'],'revision':OLD,
            'manifest':'types.json','manifest_sha256':'','acquisition':'input.json',
            'acquisition_sha256':'','source':'dependency','site':'native',
            'base_url':'https://core.invalid/'+OLD+'/api/',
            'publication':'offline-test','types':['OpenCV.Core.Mat']}
        self.config=replace(self.fixture.config,allowed_hosts=frozenset({'core.invalid'}))
        self.save()

    def save(self):
        for name,data,key in (('types.json',self.manifest,'manifest_sha256'),
                              ('input.json',self.spec,'acquisition_sha256')):
            path=self.root/name;path.write_text(sorted_json(data))
            self.dep[key]=digest(path.read_bytes())
        self.config=replace(self.config,dependencies=(copy.deepcopy(self.dep),))

    def rejected(self):
        with self.assertRaises(ValueError):destinations(self.config)

    def test_positive_exact_native_destination(self):
        item=self.manifest['types']['opencv.core.mat']
        self.assertEqual(destinations(self.config),{'opencv.core.mat':self.dep['base_url']+item['page']+'#'+item['anchor']})

    def test_inventory_determinism(self):
        self.assertEqual(self.manifest,inventory(self.spec,self.source,self.site))

    def test_wrong_existing_declaration(self):
        wrong=self.manifest['types']['opencv.core.float32_value']
        self.manifest['types']['opencv.core.mat']['anchor']=wrong['anchor']
        self.save();self.rejected()

    def test_wrong_existing_page(self):
        self.manifest['types']['opencv.core.mat']['page']=self.manifest['types']['opencv.core.sparse.sparse_mat']['page']
        self.save();self.rejected()

    def test_wrong_fragment(self):
        self.manifest['types']['opencv.core.mat']['anchor']='0'*64
        self.save();self.rejected()

    def test_deleted_destination(self):
        target=self.manifest['types']['opencv.core.mat']
        path=self.site/'api'/target['page']
        path.write_text(path.read_text().replace(target['anchor'],'0'*64));self.rejected()

    def test_changed_source_declaration_identity(self):
        self.manifest['types']['opencv.core.mat']['source_declaration_sha256']='0'*64
        self.save();self.rejected()

    def test_imgproc_cannot_use_new_revision(self):
        self.manifest['revision']=NEW;self.spec['revision']=NEW
        self.save();self.rejected()

    def test_geometry_cannot_use_old_revision(self):
        self.dep['revision']=NEW;self.save();self.rejected()

    def test_changed_pinned_revision(self):
        self.manifest['revision']='0'*40;self.save();self.rejected()

    def test_dependency_artifact_mutated_after_qualification(self):
        destinations(self.config)
        path=self.site/'api/gnatdoc.css';path.write_bytes(path.read_bytes()+b'\n')
        self.rejected()

    def test_source_mutated_after_qualification(self):
        destinations(self.config)
        path=next((self.source/'src').glob('*.ads'));path.write_text(path.read_text()+'\n')
        self.rejected()

    def test_incorrect_package_owner(self):
        self.manifest['types']['opencv.core.mat']['package']='Other'
        self.save();self.rejected()

    def test_generic_instance_target_not_invented(self):
        self.dep['types']=['OpenCV.Core.Vectors.Vector'];self.save();self.rejected()

    def test_duplicate_case_insensitive_manifest_keys(self):
        path=self.root/'types.json';path.write_text('{"types":{},"Types":{}}')
        with self.assertRaisesRegex(ValueError,'duplicate'):read_json(path)

    def test_duplicate_type_identity_in_source(self):
        path=self.source/'src/opencv-core.ads'
        path.write_text(path.read_text().replace('end OpenCV.Core;','type MAT is private;\nend OpenCV.Core;'))
        self.spec['source_sha256']=hashes(self.source)
        with self.assertRaisesRegex(ValueError,'duplicate public type'):inventory(self.spec,self.source,self.site)

    def test_conflicting_manifests(self):
        self.config=replace(self.config,dependencies=(self.dep,self.dep));self.rejected()

    def test_conflicting_explicit_alias(self):
        self.config=replace(self.config,externals={'OpenCV.Core.Mat':'https://core.invalid/wrong#valid'})
        self.rejected()

    def test_unqualified_names_do_not_get_external_owner(self):
        pkg=next(iter(packages(self.fixture.config).values()))
        self.assertIsNone(resolve('Mat',pkg,{}, {},destinations(self.config)))

    def test_invisible_owner(self):
        pkg=next(iter(packages(self.fixture.config).values()))
        self.assertIsNone(resolve('OpenCV.Core.Mat',pkg,{}, {},destinations(self.config)))

    def test_visible_qualified_owner_and_local_precedence(self):
        pkg=replace(next(iter(packages(self.fixture.config).values())),imports=frozenset({'opencv.core'}))
        external=destinations(self.config)
        self.assertEqual(resolve('OpenCV.Core.Mat',pkg,{}, {},external),('opencv.core.mat','external'))
        self.assertEqual(resolve('OpenCV.Core.Mat',pkg,{}, {'opencv.core.mat':(Path('native'), 'id')},external),('opencv.core.mat','local'))

    def test_imported_type_owner_conflict(self):
        pkg=replace(next(iter(packages(self.fixture.config).values())),imports=frozenset({'opencv.core'}))
        self.assertIsNone(resolve('OpenCV.Core.Mat',pkg,{'opencv.core':pkg},{},destinations(self.config)))

    def test_shadowed_qualified_prefix(self):
        from ada_gnatdoc_enhancer.inventory import Declaration
        pkg=replace(next(iter(packages(self.fixture.config).values())),imports=frozenset({'opencv.core'}),
                    declarations=[Declaration('function','OpenCV','function OpenCV return Integer;',1)])
        self.assertIsNone(resolve('OpenCV.Core.Mat',pkg,{}, {},destinations(self.config)))

    def test_private_limited_alias_and_object_shadow_not_authority(self):
        original=next(iter(packages(self.fixture.config).values()))
        for text in ('private with OpenCV.Core;\npackage Consumer is end Consumer;',
                     'limited with OpenCV.Core;\npackage Consumer is end Consumer;',
                     'with OpenCV.Core;\npackage Consumer is\npackage OpenCV renames Other;\nend Consumer;',
                     'with OpenCV.Core;\npackage Consumer is\nOpenCV : Integer;\nend Consumer;'):
            pkg=replace(original,source=text,imports=frozenset({'opencv.core'}))
            with self.subTest(text=text):
                self.assertIsNone(resolve('OpenCV.Core.Mat',pkg,{}, {},destinations(self.config)))

    def test_unqualified_ambiguous_local_use_owners(self):
        pkg=replace(next(iter(packages(self.fixture.config).values())),
                    imports=frozenset({'a','b'}),uses=frozenset({'a','b'}))
        self.assertIsNone(resolve('Mat',pkg,{}, {'a.mat':(Path('a'),'a'),'b.mat':(Path('b'),'b')},destinations(self.config)))

    def test_cross_host_substitution(self):
        self.dep['base_url']=self.dep['base_url'].replace('core.invalid','attacker.invalid')
        self.save();self.rejected()

    def test_unsafe_url_variants(self):
        for value in ('http://core.invalid/a/','javascript:alert(1)',
                      'https://core.invalid/%2e%2e/', 'https://core.invalid/../',
                      'https://core.invalid/a/?q=1','https://core.invalid/a/#frag',
                      'https://core.invalid/a\\b/', 'https://user@core.invalid/a/',
                      'https://core.invalid//a/', 'https://core.invalid/a/\n'):
            with self.subTest(value=value),self.assertRaises(ValueError):base_url(value,self.config.allowed_hosts)

    def test_corrupted_manifest(self):
        (self.root/'types.json').write_text('{broken');self.rejected()

    def test_malformed_manifest_structure(self):
        self.manifest={'types':[]};self.save();self.rejected()

    def test_manifest_hash_not_self_authorizing(self):
        (self.root/'types.json').write_text('{}');self.rejected()

    def test_acquisition_hash_not_self_authorizing(self):
        (self.root/'input.json').write_text('{}');self.rejected()

    def test_production_not_enabled_by_offline_claim(self):
        self.dep['publication']='published';self.save();self.rejected()

    def test_mapping_must_pin_full_sha(self):
        self.dep['base_url']='https://core.invalid/latest/api/';self.save();self.rejected()

    def test_published_wrong_valid_artifact_rejected(self):
        def fetch(url):return url,b'<h4 id="'+b'0'*64+b'">Mat</h4>'
        with self.assertRaisesRegex(ValueError,'differs'):verify_published(self.dep['base_url'],self.manifest,self.config.allowed_hosts,fetch)

    def test_published_redirect_cross_host_rejected(self):
        def fetch(url):return url.replace('core.invalid','evil.invalid'),b'ok'
        with self.assertRaises(ValueError):verify_published(self.dep['base_url'],self.manifest,self.config.allowed_hosts,fetch)

    def test_publication_byte_verification_is_separate(self):
        def fetch(url):return url,(self.site/'api'/url.rsplit('/',1)[1]).read_bytes()
        report=verify_published(self.dep['base_url'],self.manifest,self.config.allowed_hosts,fetch)
        self.assertEqual(report['status'],'published-bytes-verified')
        self.assertEqual(self.manifest['qualification']['published_url'],'not verified')

    def test_pipeline_rechecks_dependency_after_enhancement(self):
        enhance(self.config,self.fixture.site)
        path=self.site/'api/gnatdoc.css';path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact changed'):verify(self.config,self.fixture.site)

    def test_backward_compatible_toml_extension(self):
        path=self.root/'project.toml'
        text=path.read_text()+'\n[security]\nexternal_hosts = ["core.invalid"]\n[[external_dependencies]]\n'
        text+='\n'.join(k+' = '+json.dumps(v) for k,v in self.dep.items())+'\n'
        path.write_text(text)
        self.assertEqual(destinations(load(self.root,'project.toml')),destinations(self.config))

    def test_typed_contexts_ignore_comments_and_literals(self):
        from ada_gnatdoc_enhancer.syntax import type_positions
        self.assertEqual(type_positions('-- X : OpenCV.Core.Mat\nS := "X : OpenCV.Core.Mat";'),[])

    def test_duplicate_case_insensitive_config_types(self):
        self.dep['types']=['OpenCV.Core.Mat','opencv.core.mat']
        path=self.root/'project.toml'
        path.write_text(path.read_text()+'\n[[external_dependencies]]\n'+
                        '\n'.join(k+' = '+json.dumps(v) for k,v in self.dep.items()))
        with self.assertRaisesRegex(ValueError,'duplicate'):load(self.root,'project.toml')

    def test_unsupported_acquisition_profile(self):
        self.spec['configuration']=self.spec['configuration'].replace('qualification-public','other')
        self.save();self.rejected()

    def test_missing_source_declaration_even_if_native_exists(self):
        path=self.source/'src/opencv-core.ads'
        path.write_text(path.read_text().replace('type Mat is tagged limited private;',''))
        self.spec['source_sha256']=hashes(self.source)
        self.save();self.rejected()


class AuthenticPinnedExternals(unittest.TestCase):
    """Both dependency versions execute in CI; these are REDUCED native fixtures."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gde-authentic-external-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.fixtures=Path(__file__).resolve().parent/'real-fixtures'

    def configure(self,release):
        dependency=self.fixtures/'external-core'/release
        shutil.copytree(dependency,self.root/'dependency')
        geometry=self.fixtures/'geometry'
        shutil.copytree(geometry/'source',self.root/'consumer')
        shutil.copytree(geometry/'pristine',self.root/'site')
        data=read_json(dependency/'input.json')
        text=read_json(geometry/'input.json')['configuration']
        text=text.replace('qualification-public','consumer/src').replace('docs/api-categories.json','consumer/docs/api-categories.json')
        manifest=read_json(dependency/'types.json')
        names=['OpenCV.Float32_Point','OpenCV.Float32_Value','OpenCV.Float64_Value',
               'OpenCV.Rect','OpenCV.Rotated_Rect','OpenCV.Angle_Unit']
        dep={'repository':data['repository'],'revision':data['revision'],
            'manifest':'dependency/types.json','manifest_sha256':digest((dependency/'types.json').read_bytes()),
            'acquisition':'dependency/input.json','acquisition_sha256':digest((dependency/'input.json').read_bytes()),
            'source':'dependency/source','site':'dependency/native',
            'base_url':'https://core.invalid/'+data['revision']+'/api/',
            'publication':'offline-test','types':names}
        text+='\n[security]\nexternal_hosts = ["core.invalid"]\n[[external_dependencies]]\n'
        text+='\n'.join(k+' = '+json.dumps(v) for k,v in dep.items())+'\n'
        (self.root/'project.toml').write_text(text)
        return load(self.root,'project.toml'),manifest

    def test_authentic_geometry_external_generation_idempotence(self):
        config,manifest=self.configure('0.5.0');site=self.root/'site'
        result=enhance(config,site)
        self.assertEqual(result['linked_local_types'],171)
        # Reduced root fixture intentionally lacks OpenCV.Core.Mat: 94/95.
        self.assertEqual(result['linked_external_types'],94)
        state=hashes(site);enhance(config,site);self.assertEqual(state,hashes(site))
        self.assertEqual(verify(config,site)['linked_external_types'],94)

    def test_authentic_old_root_inventory(self):
        config,manifest=self.configure('0.4.1')
        self.assertEqual(len(destinations(config)),6)
        self.assertEqual(manifest['revision'],OLD)

    def test_authentic_old_revision_cannot_satisfy_geometry_requirement(self):
        config,_=self.configure('0.4.1')
        config=replace(config,dependencies=({**config.dependencies[0],'revision':NEW},))
        with self.assertRaisesRegex(ValueError,'revision mismatch'):destinations(config)

    def test_authentic_new_revision_cannot_satisfy_imgproc_requirement(self):
        config,_=self.configure('0.5.0')
        config=replace(config,dependencies=({**config.dependencies[0],'revision':OLD},))
        with self.assertRaisesRegex(ValueError,'revision mismatch'):destinations(config)

    def test_authentic_wrong_existing_native_anchor_rejected(self):
        config,manifest=self.configure('0.5.0')
        manifest['types']['opencv.float32_value']['anchor']=manifest['types']['opencv.float64_value']['anchor']
        path=self.root/'dependency/types.json';path.write_text(sorted_json(manifest))
        config=replace(config,dependencies=({**config.dependencies[0],
                        'manifest_sha256':digest(path.read_bytes())},))
        with self.assertRaisesRegex(ValueError,'identity evidence'):destinations(config)

    def test_authentic_consumer_source_mutation_after_enhancement(self):
        config,_=self.configure('0.5.0');site=self.root/'site';enhance(config,site)
        path=next((self.root/'consumer/src').glob('*.ads'));path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'source differs'):verify(config,site)

    def test_authentic_existing_wrong_link_rejected_in_published_output(self):
        config,manifest=self.configure('0.5.0');site=self.root/'site';enhance(config,site)
        correct=manifest['types']['opencv.float32_point']['anchor']
        wrong=manifest['types']['opencv.float64_value']['anchor']
        page=next(p for p in (site/'api').glob('*.html') if correct in p.read_text())
        page.write_text(page.read_text().replace(correct,wrong,1))
        with self.assertRaisesRegex(ValueError,'published file differs'):verify(config,site)


if __name__=='__main__':unittest.main()