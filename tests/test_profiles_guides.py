"""Distinct reference profiles, operation categories, guides and warnings."""
import json
import unittest
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.conformance import run
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.navigation import operation_entries
from ada_gnatdoc_enhancer.warnings import identities,compare
from ada_gnatdoc_enhancer.coverage import report
from _helper import FIXTURES, Fixture

class Profiles(unittest.TestCase):
    def test_four_synthetic_reference_shapes(self):
        r=run(FIXTURES)
        self.assertEqual({k:v['packages'] for k,v in r['profiles'].items()},
                         {'core':3,'imgproc':1,'geometry':2,'mel':29})
        self.assertEqual(r['fully_pinned_consumer_sites'],'not qualified in bootstrap')

    def test_imgproc_overload_navigation(self):
        fx=Fixture('imgproc');self.addCleanup(fx.cleanup)
        ops=operation_entries(fx.config,snapshot(fx.config,fx.site))
        self.assertEqual(len(ops),2)
        self.assertEqual(len(ops[1][3]),2)
        enhance(fx.config,fx.site)
        text=(fx.site/'api/index.html').read_text()
        self.assertIn('Browse operations',text)
        self.assertEqual(verify(fx.config,fx.site)['public_packages'],1)

    def test_geometry_multi_package_categories(self):
        fx=Fixture('geometry');self.addCleanup(fx.cleanup)
        r=enhance(fx.config,fx.site)
        self.assertEqual(r['public_packages'],2)
        self.assertEqual(len(operation_entries(fx.config,snapshot_raw(fx))),2)

    def test_invalid_category_name_rejected(self):
        fx=Fixture('imgproc');self.addCleanup(fx.cleanup)
        f=fx.root/'docs/api-categories.json'
        data=json.loads(f.read_text());data['categories'][0]['declarations'][0]='Missing_Action'
        f.write_text(json.dumps(data))
        with self.assertRaisesRegex(EnhancementError,'unresolved operation'):
            enhance(fx.config,fx.site)

    def test_mel_portal_29_packages_and_six_guides(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        r=enhance(fx.config,fx.site)
        self.assertEqual(r['public_packages'],29)
        self.assertEqual(r['html_pages'],37)
        self.assertEqual(len(list((fx.site/'guides').glob('*.html'))),6)
        index=(fx.site/'index.html').read_text()
        self.assertEqual(index.count('data-package-entry='),29)
        self.assertEqual(verify(fx.config,fx.site)['html_pages'],37)

    def test_mel_missing_guide_rejected(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        (fx.root/'docs/guides/api-map.html').unlink()
        with self.assertRaisesRegex(EnhancementError,'missing/nonregular file'):
            enhance(fx.config,fx.site)

    def test_mel_unknown_placeholder_rejected(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        p=fx.root/'docs/index.html';p.write_text(p.read_text()+'{{unknown}}')
        with self.assertRaisesRegex(EnhancementError,'unresolved guide substitution'):
            enhance(fx.config,fx.site)

    def test_missing_renderer_exception_fails(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        p=fx.root/'project.toml';p.write_text(p.read_text()+
            '\nrenderer_exceptions = ["Some.Unknown.Exception"]\n')
        with self.assertRaises(EnhancementError):load(fx.root,'project.toml')

    def test_warning_identity_and_ratchet(self):
        fx=Fixture('core');self.addCleanup(fx.cleanup)
        value=identities('opencv-core.ads:3:4: warning: example warning',packages(fx.config))
        self.assertEqual(len(value),1)
        self.assertEqual(compare(value,value)['added'],[])
        with self.assertRaisesRegex(EnhancementError,'new documentation warnings'):
            compare(value,[])
        with self.assertRaisesRegex(EnhancementError,'fixed documentation warnings'):
            compare([],value)
        with self.assertRaisesRegex(EnhancementError,'unsupported GNATdoc warning format'):
            identities('warning: invalid',packages(fx.config))

    def test_basic_coverage_reports_not_member_claims(self):
        fx=Fixture('core');self.addCleanup(fx.cleanup)
        result=report(packages(fx.config),snapshot(fx.config,fx.site))
        self.assertEqual(result['elements'],5)
        self.assertEqual(result['rendered'],5)
        self.assertIn('not full member',result['level'])


def snapshot_raw(fx):
    # Use a sibling raw fixture when the original was just enhanced.
    from _helper import FIXTURES
    other=Fixture('geometry')
    try:return snapshot(other.config,other.site)
    finally:other.cleanup()

if __name__=='__main__':unittest.main()
