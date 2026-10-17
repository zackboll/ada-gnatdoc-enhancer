"""Source inventory, exact schema, name-resolution and malformed-source gates."""
import unittest
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages, mask_ada, normalized
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.syntax import resolve, type_positions, highlighted, plain, linked

from _helper import Fixture

class ConfigInventory(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture('core');self.addCleanup(self.fx.cleanup)

    def test_package_discovery_real_header_and_private_exclusion(self):
        found=packages(self.fx.config)
        self.assertEqual(len(found),3)
        self.assertEqual(set(found['opencv.core'].public_types), {'mat','float32_value'})
        self.assertTrue(found['opencv.core.sparse'].imports.issuperset({'opencv.core'}))
        extra=self.fx.root/'src'/'hidden.ads'
        extra.write_text('private package Demo.Hidden is\nend Demo.Hidden;\n')
        self.assertEqual(len(packages(self.fx.config)),3)

    def test_literal_and_comment_normalization(self):
        one=normalized('function N (S : String := "Ada""Text") return Natural;')
        two=normalized('function N (S : String := "AdaOther") return Natural;')
        self.assertNotEqual(one,two)
        self.assertEqual(normalized('-- comment\nFunction N return T;'),normalized('function   N   return T;'))
        text='-- package Fictitious is\npackage Demo is\n S : String := "-- not a comment";\nend Demo;'
        masked=mask_ada(text)
        self.assertNotIn('Fictitious',masked)
        self.assertNotIn('comment',masked)
        self.assertIn('package Demo is',masked)

    def test_unknown_config_option_fails(self):
        p=self.fx.root/'project.toml'
        p.write_text(p.read_text()+'\nunsupported = true\n')
        with self.assertRaisesRegex(EnhancementError,'unsupported presentation keys'):
            load(self.fx.root,'project.toml')

    def test_version_gating(self):
        p=self.fx.root/'project.toml'
        p.write_text(p.read_text().replace('version = "26.0.0"','version = "27.0.0"'))
        with self.assertRaisesRegex(EnhancementError,'unsupported GNATdoc HTML'):
            load(self.fx.root,'project.toml')

    def test_expected_packages_detects_unknown_source(self):
        p=self.fx.root/'src/new.ads';p.write_text('package New is\nend New;\n')
        with self.assertRaisesRegex(EnhancementError,'public package inventory mismatch'):
            packages(self.fx.config)

    def test_symlink_source_rejected(self):
        p=self.fx.root/'src/new.ads';p.symlink_to(self.fx.root/'src/opencv-core.ads')
        with self.assertRaisesRegex(EnhancementError,'symlink Ada source'):
            packages(self.fx.config)

    def test_link_visibility_and_resolution(self):
        source=packages(self.fx.config)
        native=snapshot(self.fx.config,self.fx.site)
        targets=verified_types(native,source)
        target=resolve('OpenCV.Core.Mat',source['opencv.core.sparse'],source,targets,{})
        self.assertEqual(target,('opencv.core.mat','local'))
        self.assertIsNone(resolve('Other.Mat',source['opencv.core.sparse'],source,targets,{}))
        self.assertIsNone(resolve('Unknown',source['opencv.core'],source,targets,{}))
        self.assertEqual(resolve('Mat',source['opencv.core.sparse'],source,targets,{}),('opencv.core.mat','local'))

    def test_type_marks_only(self):
        hits=type_positions('function F (A : in out Mat; B : Natural) return Mat;')
        self.assertEqual([x[2] for x in hits],['Mat','Mat'])
        self.assertEqual(type_positions('function F (Count : Natural := 10) return Boolean;'),[])

    def test_highlighted_escaped_source_roundtrips(self):
        code='function R (X : Natural := 16#F0#; S : String := "a""b") return T; -- end'
        before=plain(code)
        after=highlighted(code)
        self.assertIn('ada-keyword',after)
        self.assertIn('ada-number',after)
        self.assertIn('ada-string',after)
        self.assertIn('ada-comment',after)
        self.assertEqual(before,plain(after))

    def test_native_profile_is_not_only_name_matching(self):
        src=packages(self.fx.config)
        site=snapshot(self.fx.config,self.fx.site)
        page=site.pages['opencv.core'].path
        raw=page.read_text()
        page.write_text(raw.replace('Convert (Source : Mat) return Mat','Convert (Source : Natural) return Mat'))
        with self.assertRaisesRegex(EnhancementError,'native declaration profile unmatched'):
            snapshot(self.fx.config,self.fx.site)

    def test_native_wrong_existing_destination(self):
        native=snapshot(self.fx.config,self.fx.site)
        page=native.pages['opencv.core'].path.name
        other=native.pages['opencv.core.sparse'].path.name
        index=self.fx.site/'api/index.html'
        raw=index.read_text()
        index.write_text(raw.replace(page,'XXX',1).replace(other,page,1).replace('XXX',other,1))
        with self.assertRaisesRegex(EnhancementError,'native navigation package destinations mismatch'):
            snapshot(self.fx.config,self.fx.site)

if __name__=='__main__':unittest.main()
