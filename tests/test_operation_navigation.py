"""Source-order navigation: authentic excerpts and explicitly synthetic mutations."""
import copy
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ada_gnatdoc_enhancer.authored import api_destinations
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.navigation import operation_entries
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.util import digest
from _helper import Fixture

FIXTURE = Path(__file__).parent/'operation-fixtures/imgproc'


class OperationNavigation(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)/'imgproc'; shutil.copytree(FIXTURE, self.root)
        self.config = load(self.root, 'project.toml')
        self.native = snapshot(self.config, self.root/'native')
        self.page = next(iter(self.native.pages.values()))
        self.expected = json.loads((self.root/'expected.json').read_text())
        self.categories = json.loads((self.root/'categories.json').read_text())

    def write_categories(self):
        (self.root/'categories.json').write_text(json.dumps(self.categories))

    def entries(self):
        return [item for *_, items in operation_entries(self.config, self.native) for item in items]

    def reject(self):
        with self.assertRaises(EnhancementError):
            self.entries()

    def test_authentic_labels_exact_fragments_and_profiles(self):
        self.assertEqual(self.entries(), [(e['label'], e['href']) for e in self.expected])
        # A singleton after eight overload entries must remain unnumbered.
        self.assertEqual(self.entries()[-1][0], 'Squared_Box_Filter')
        api = api_destinations(self.config, self.native)
        for label, href in self.entries():
            name, _, suffix = label.partition(' (')
            ordinal = suffix.rstrip(')') if suffix else '1'
            self.assertEqual(api[name.lower()+'/'+ordinal], '../api/'+href)

    def test_reverse_native_sections_preserves_all_identities(self):
        self.page.sections.reverse()
        self.test_authentic_labels_exact_fragments_and_profiles()

    def test_case_insensitive_identity(self):
        for i, section in enumerate(self.page.sections):
            self.page.sections[i] = replace(section, name=section.name.swapcase())
        self.categories['categories'][0]['declarations'] = [
            n.swapcase() for n in self.categories['categories'][0]['declarations']]
        self.write_categories(); self.test_authentic_labels_exact_fragments_and_profiles()

    def test_category_display_reordering_and_independent_operation_ordinals(self):
        names = self.categories['categories'][0]['declarations']
        self.categories['categories'] = [
            {'id': 'second', 'title': 'Second', 'declarations': names[2:]},
            {'id': 'first', 'title': 'First', 'declarations': names[:2]}]
        self.write_categories()
        before = dict(self.entries())
        self.categories['categories'].reverse()
        for c in self.categories['categories']: c['declarations'].reverse()
        self.write_categories()
        self.assertEqual(dict(self.entries()), before)
        self.assertEqual(before, {e['label']: e['href'] for e in self.expected})

    def test_duplicate_spelling_in_distinct_packages(self):
        # Synthetic second owner uses the same profiles but its own observed page.
        source = self.root/'source/other.ads'
        source.write_text((self.root/'source/opencv-image_processing.ads').read_text().replace(
            'OpenCV.Image_Processing', 'Other'))
        self.config = replace(self.config, expected_packages=())
        other = copy.deepcopy(self.page); other.package = 'Other'; other.path = other.path.with_name('a'*64+'.html')
        self.native.pages['other'] = other
        categories = self.categories['categories']
        self.categories = {'version': 1, 'packages': [
            {'package': 'OpenCV.Image_Processing', 'categories': categories},
            {'package': 'Other', 'categories': [{**categories[0], 'id': 'other'}]}]}
        self.write_categories()
        groups = operation_entries(self.config, self.native)
        self.assertEqual([label for label, _ in groups[0][3]], [label for label, _ in groups[1][3]])
        self.assertTrue(all(href.startswith('a'*64) for _, href in groups[1][3]))

    def test_two_source_declarations_same_anchor(self):
        path = self.root/'source/opencv-image_processing.ads'
        text = path.read_text()
        signature = next(d.signature for p in packages(self.config).values()
                         for d in p.declarations if d.name == 'Pyramid_Up')
        self.assertIn(signature, text)
        path.write_text(text.replace('end OpenCV.Image_Processing;', signature+'\nend OpenCV.Image_Processing;'))
        self.reject()

    def test_multiple_compatible_native_anchors(self):
        self.page.sections.append(replace(self.page.sections[0], anchor='f'*64)); self.reject()

    def test_duplicate_native_destination(self):
        self.page.sections[1] = replace(self.page.sections[1], anchor=self.page.sections[0].anchor)
        self.reject()

    def test_changed_parameter_type(self):
        path = self.root/'source/opencv-image_processing.ads'
        path.write_text(path.read_text().replace('Sigma_Color : OpenCV.Float64_Value', 'Sigma_Color : Integer'))
        self.reject()

    def test_changed_parameter_mode(self):
        path = self.root/'source/opencv-image_processing.ads'
        path.write_text(path.read_text().replace('Destination : in out', 'Destination : out'))
        self.reject()

    def test_changed_default(self):
        path = self.root/'source/opencv-image_processing.ads'
        path.write_text(path.read_text().replace(':= Float64_Kernel', ':= Float32_Kernel'))
        self.reject()

    def test_missing_overloaded_declaration(self):
        self.page.sections.pop(); self.reject()

    def test_unowned_native_section_revision_mismatch(self):
        self.page.sections.append(replace(self.page.sections[0], name='Unexpected', anchor='f'*64))
        self.reject()

    def test_duplicate_category_assignment(self):
        self.categories['categories'].append({'id': 'extra', 'title': 'Extra', 'declarations': ['FILTER_2D']})
        self.write_categories(); self.reject()

    def test_omitted_category_assignment(self):
        self.categories['categories'][0]['declarations'].pop(); self.write_categories(); self.reject()

    def test_unknown_category_operation(self):
        self.categories['categories'][0]['declarations'].append('Not_An_Operation')
        self.write_categories(); self.reject()

    def test_duplicate_category_id(self):
        self.categories['categories'].append({**self.categories['categories'][0]})
        self.write_categories(); self.reject()

    def test_invalid_category_ids(self):
        for value in ('', 'UPPER', '../escape', 1, None):
            with self.subTest(value=value):
                self.categories['categories'][0]['id'] = value
                self.write_categories(); self.reject()

    def test_swapped_package_ownership(self):
        fx = Fixture('geometry'); self.addCleanup(fx.cleanup)
        path = fx.root/'docs/api-categories.json'; data = json.loads(path.read_text())
        a, b = data['packages']; a['categories'], b['categories'] = b['categories'], a['categories']
        path.write_text(json.dumps(data))
        with self.assertRaises(EnhancementError):
            operation_entries(fx.config, snapshot(fx.config, fx.site))

    def test_wrong_existing_destination_and_rewritten_output_manifest(self):
        fx = Fixture('imgproc'); self.addCleanup(fx.cleanup); enhance(fx.config, fx.site)
        index = fx.site/'api/index.html'; text = index.read_text()
        from ada_gnatdoc_enhancer.validation import Page
        links = [h for h in Page(text).links if '#' in h and '.html' in h]
        self.assertGreater(len(links), 1)
        text = text.replace(links[0], links[-1], 1); index.write_text(text)
        manifest = fx.site/'api/presentation.json'; data = json.loads(manifest.read_text())
        # Output metadata is not authority, even when supplied with a new hash.
        data.setdefault('output_sha256', {})['api/index.html'] = digest(text.encode())
        manifest.write_text(json.dumps(data))
        with self.assertRaises(EnhancementError): verify(fx.config, fx.site)


if __name__ == '__main__': unittest.main()