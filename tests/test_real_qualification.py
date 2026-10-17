"""Authentic reduced inputs are regressions, never full-site certificates."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ada_gnatdoc_enhancer.cli import run as cli_run
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import last_semicolon, mask_ada, normalized
from ada_gnatdoc_enhancer.native_html import SECTION
from ada_gnatdoc_enhancer.pipeline import MANIFEST, verify
from ada_gnatdoc_enhancer.qualification import (
    bind_pristine, hashes, identities, preserve_native, run,
)
from ada_gnatdoc_enhancer.syntax import highlighted, plain
from ada_gnatdoc_enhancer.util import digest

FIXTURES=Path(__file__).resolve().parent/'real-fixtures'


class AuthenticExcerpts(unittest.TestCase):
    def setUp(self):
        self.items=json.loads((FIXTURES/'excerpts.json').read_text())

    def test_immutable_excerpt_provenance(self):
        self.assertEqual({x['profile'] for x in self.items},{'core','imgproc','geometry','mel'})
        for item in self.items:
            self.assertRegex(item['revision'],r'^[0-9a-f]{40}$')
            self.assertEqual(digest(item['native_excerpt'].encode()),item['native_excerpt_sha256'])
            self.assertIsNotNone(SECTION.fullmatch(item['native_excerpt']))

    def test_native_greater_than_round_trip(self):
        item=next(x for x in self.items if x['name']=='Convexity_Defect_Array')
        raw=SECTION.fullmatch(item['native_excerpt'])[4]
        self.assertIn('&lt;>',raw)
        self.assertEqual(plain(highlighted(raw)),plain(raw))
        self.assertIn('ada-keyword',highlighted(raw))

    def test_trailing_record_aspect(self):
        item=next(x for x in self.items if x['name']=='Complex_I8')
        signature=item['source_signature']
        self.assertIn('Convention',signature)
        self.assertEqual(last_semicolon(mask_ada(signature),0),len(signature))
        raw=SECTION.fullmatch(item['native_excerpt'])[4]
        self.assertEqual(plain(highlighted(raw)),plain(raw))

    def test_literal_greater_than_does_not_authorize_html(self):
        with self.assertRaisesRegex(ValueError,'HTML tags'):plain('<img src=x>')

    def test_known_abbreviated_enumerations_remain_gaps(self):
        for item in self.items:
            if item['name'] not in ('Color_Conversion','Cannot_Comply'):continue
            raw=SECTION.fullmatch(item['native_excerpt'])[4]
            self.assertIn('…',raw)
            self.assertNotEqual(normalized(raw),normalized(item['source_signature']))

    def test_expression_function_remains_explicit_gap(self):
        item=next(x for x in self.items if x['name']=='Make_Scalar')
        self.assertIn(' is (',normalized(item['source_signature']))
        self.assertNotIn(' is (',normalized(SECTION.fullmatch(item['native_excerpt'])[4]))


class PinnedQualification(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gde-real-regression-')
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.input=self.base/'input'
        shutil.copytree(FIXTURES/'geometry',self.input)
        self.spec=self.input/'input.json'
        self.source=self.input/'source';self.site=self.input/'pristine'

    def qualify(self,name='qualification'):
        return run(self.spec,self.source,self.site,self.base/name)

    def test_authentic_geometry_structural_regression(self):
        before=hashes(self.site)
        result=self.qualify()
        self.assertEqual(result['structural_result'],'pass')
        self.assertEqual(result['checks']['native_integrity']['declarations'],130)
        self.assertEqual(result['checks']['enhancement']['linked_types'],171)
        self.assertTrue(result['checks']['determinism'])
        self.assertTrue(result['checks']['idempotence'])
        self.assertEqual(set(result['checks']['negative_integrity']),{'anchor','link','asset','source'})
        self.assertTrue(all(x['rejected'] for x in result['checks']['negative_integrity'].values()))
        self.assertEqual(before,hashes(self.site))
        self.assertNotEqual(result['full_site_compatibility'],'qualified')

    def test_wrong_revision_rejected(self):
        data=json.loads(self.spec.read_text());data['revision']='main'
        self.spec.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'immutable'):self.qualify()

    def test_qualification_cli_relative_site_belongs_to_source_root(self):
        # Only path-contract testing here: deliberately fail pin validation so
        # an incorrect cwd-relative path gives a different diagnostic.
        shutil.copytree(self.site,self.source/'native')
        path=self.source/'native/api/gnatdoc.css';path.write_text('changed')
        args=SimpleNamespace(command='qualify',spec=self.spec,source_root=self.source,
                             site=Path('native'),workspace=self.base/'out')
        with self.assertRaisesRegex(ValueError,'site hashes mismatch'):cli_run(args)

    def test_source_directory_symlink_rejected(self):
        original=self.source/'src';original.rename(self.source/'real-src')
        original.symlink_to('real-src',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.qualify()

    def test_nested_workspace_symlink_rejected(self):
        (self.base/'redirect').symlink_to(self.base,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink workspace'):
            run(self.spec,self.source,self.site,self.base/'redirect/output')

    def test_tampered_source_rejected(self):
        path=next((self.source/'src').glob('*.ads'));path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'source mismatch'):self.qualify()

    def test_extra_ada_source_rejected(self):
        (self.source/'extra.ads').write_text('package Extra is end Extra;')
        with self.assertRaisesRegex(ValueError,'unpinned Ada'):self.qualify()

    def test_tampered_pristine_rejected(self):
        (self.site/'api/gnatdoc.css').write_text('altered')
        with self.assertRaisesRegex(ValueError,'site hashes mismatch'):self.qualify()

    def test_symlink_input_rejected(self):
        link=self.base/'linked';link.symlink_to(self.site,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):run(self.spec,self.source,link,self.base/'out')

    def test_existing_workspace_rejected(self):
        with self.assertRaisesRegex(ValueError,'workspace must be new'):
            run(self.spec,self.source,self.site,self.input)

    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlaps'):
            run(self.spec,self.source,self.site,self.source/'output')

    def test_independent_identity_check_rejects_text_change(self):
        original=identities(self.site)
        page=next(p for p in (self.site/'api').glob('*.html') if p.name!='index.html')
        text=page.read_text();page.write_text(text.replace('<code>','<code>changed ',1))
        with self.assertRaisesRegex(ValueError,'signatures changed'):preserve_native(original,self.site)

    def test_external_authority_rejects_manifest_native_rewrite(self):
        self.qualify()
        root=self.base/'qualification/first';site=root/'_site'
        manifest=site/MANIFEST;data=json.loads(manifest.read_text())
        name=next(n for n in data['original_api_html'] if n!='api/index.html')
        data['original_api_html'][name]+='<!-- changed captured authority -->'
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'pristine authority'):bind_pristine(self.site,site)

    def test_inventory_failure_is_machine_readable(self):
        data=json.loads(self.spec.read_text())
        data['configuration']=data['configuration'].replace('OpenCV.Geometry.Subdiv2D','Wrong.Unit')
        self.spec.write_text(json.dumps(data))
        result=self.qualify()
        self.assertEqual(result['structural_result'],'fail')
        self.assertEqual(result['failure']['phase'],'inventory')
        self.assertTrue((self.base/'qualification/report.json').exists())


if __name__=='__main__':unittest.main()