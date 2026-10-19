"""Authentic current-package occurrences plus explicitly synthetic adversaries."""
from dataclasses import replace
import html
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from _helper import Fixture
from ada_gnatdoc_enhancer.inventory import _one
from ada_gnatdoc_enhancer.syntax import TYPE_LINK, highlighted, linked, plain, resolve

FIXTURE = Path(__file__).parent/'real-fixtures/current-package-types'
PROVENANCE = json.loads((FIXTURE/'provenance.json').read_text())
IMAGE = 'ams.mel.ir.image'
INSTRUMENTATION = 'ams.mel.ir.instrumentation'
REQUIRED = (
    (IMAGE, 'Sensor_Inertial_State', 'Uncertainty', 'Image.Uncertainty'),
    (IMAGE, 'Sensor_Nav_State', 'Orientation', 'Image.Orientation'),
    (IMAGE, 'Sensor_Nav_State', 'Orientation_Velocity', 'Image.Orientation'),
    (IMAGE, 'Sensor_Nav_State', 'Orientation_Acceleration', 'Image.Orientation'),
    (IMAGE, 'Sensor_Nav_State', 'Coordinate_System', 'Image.Coordinate_System'),
    (IMAGE, 'Navigation_Report', 'Attitude_Rate', 'Image.Attitude_Rate'),
    (IMAGE, 'Navigation_Report', 'Position_Velocity_Covariance', 'Image.Position_Velocity_Covariance'),
    (INSTRUMENTATION, 'Instrumentation_Level_Command', 'Priority', 'Instrumentation.Priority'),
    (INSTRUMENTATION, 'Instrumentation_Report', 'Priority', 'Instrumentation.Priority'),
)


def qualifier():
    path = Path(__file__).resolve().parents[1]/'scripts/qualify_current_package_type_links.py'
    spec = importlib.util.spec_from_file_location('current_package_oracle',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CurrentPackageTypes(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.config = self.fx.config
        self.source = {}
        self.targets = {}
        for key, data in PROVENANCE['packages'].items():
            self.source[key] = _one(FIXTURE/data['reduced_source'])
            for d in data['entries']:
                self.targets[key+'.'+d['name'].lower()] = (Path(d['page']), d['anchor'])
        self.pkg = self.source[IMAGE]

    def render(self, code, pkg=None, targets=None, config=None):
        pkg = pkg or self.pkg
        source = {**self.source, pkg.name.lower(): pkg}
        raw = html.escape(code, quote=False)
        return linked(raw, pkg, source, None,
                      self.targets if targets is None else targets,
                      config or self.config)[0]

    def synthetic(self, declarations='', key=IMAGE):
        path = self.fx.root/'synthetic.ads'
        path.write_text('package '+key+' is\n'
                        'type Attitude_Rate is range 0 .. 9;\n'+declarations+
                        '\nend '+key+';')
        return _one(path)

    def entry(self, key, name):
        return next(d for d in PROVENANCE['packages'][key]['entries'] if d['name'] == name)

    def test_nine_authentic_occurrences(self):
        for key, declaration, component, spelling in REQUIRED:
            with self.subTest(declaration=declaration, component=component):
                entry = self.entry(key, declaration)
                result = self.render(entry['native'], self.source[key])
                matches = [m for m in TYPE_LINK.finditer(result) if m[3] == spelling]
                expected = sum(1 for k, d, _, s in REQUIRED if (k,d,s)==(key,declaration,spelling))
                self.assertEqual(len(matches), expected)
                destination = self.targets[key+'.'+spelling.split('.')[1].lower()]
                self.assertTrue(all(m[1] == destination[0].name+'#'+destination[1] for m in matches))
                self.assertEqual(plain(result), entry['native'])

    def test_complete_navigation_report_six_links(self):
        code = self.entry(IMAGE, 'Navigation_Report')['native']
        links = TYPE_LINK.findall(self.render(code))
        expected = ['position_solution_state', 'ams.mel.status.euler', 'attitude_rate',
                    'north_east_down', 'north_east_down', 'position_velocity_covariance']
        self.assertEqual([identity for _,identity,_ in links],
                         [n if '.' in n else IMAGE+'.'+n for n in expected])
        self.assertNotIn('Long_Float', [s for _,_,s in links])
        self.assertNotIn('Long_Long_Integer', [s for _,_,s in links])
        page = '1227ecb7e9dafa3f2bb5afc47ffd547c851f2fc8202385479135994de7b16763.html'
        self.assertEqual(links[2][0], page+'#000c90c6e32939281ba36b0309023f11111c09b027dfcb5acf7f6fcbde859f17')
        self.assertEqual(links[5][0], page+'#05b10691e1d32ec5c7b89999581889463e7f301b8a02667d19965f88e7c1b1d6')

    def test_case_preserved(self):
        code = 'X : iMaGe.aTtItUdE_RaTe;'
        link = TYPE_LINK.findall(self.render(code))
        self.assertEqual(link[0][1:], (IMAGE+'.attitude_rate', 'iMaGe.aTtItUdE_RaTe'))
        self.assertEqual(plain(self.render(code)), code)

    def test_formal_parameter(self):
        code = 'procedure Read (X, Y : in out Image.Attitude_Rate);'
        self.assertEqual(len(TYPE_LINK.findall(self.render(code))), 1)

    def test_comments_and_whitespace(self):
        code = 'X : -- Image : Integer; is not authority\n Image.Attitude_Rate;'
        pkg = self.synthetic('-- Image : Integer;\n S : String := "Image, X : Integer";\n C : Character := \'.\';')
        result = self.render(code, pkg)
        self.assertEqual(len(TYPE_LINK.findall(result)), 1)
        self.assertEqual(plain(result), code)

    def test_entity_encoded_dot(self):
        raw = 'X : Image&#46;Attitude_Rate;'
        result, count = linked(raw, self.pkg, self.source, None, self.targets, self.config)
        self.assertEqual(count, 1)
        self.assertEqual(TYPE_LINK.findall(result)[0][2], 'Image&#46;Attitude_Rate')
        self.assertEqual(plain(highlighted(result)), html.unescape(raw))

    def test_distinct_full_package_identities(self):
        pkg = self.synthetic(key='Other.Image')
        targets = {**self.targets, 'other.image.attitude_rate': (Path('other.html'), 'other-anchor')}
        result = self.render('X : Image.Attitude_Rate;', pkg, targets)
        self.assertEqual(TYPE_LINK.findall(result),
                         [('other.html#other-anchor', 'other.image.attitude_rate', 'Image.Attitude_Rate')])

    def test_external_mapping_cannot_override_local(self):
        config = replace(self.config, externals={'image.attitude_rate': 'https://wrong.invalid/#wrong',
                                                IMAGE+'.attitude_rate': 'https://wrong.invalid/#wrong'})
        self.assertEqual(self.render('X : Image.Attitude_Rate;', config=config),
                         self.render('X : Image.Attitude_Rate;'))

    def test_unknown_private_non_type_and_unreconciled(self):
        for name in ('Unknown', 'Private_Only', 'Read', 'Attitude_Rate'):
            with self.subTest(name=name):
                pkg = self.synthetic('procedure Read;\nprivate\n type Private_Only is range 1 .. 2;')
                self.assertNotIn('type-reference', self.render('X : Image.'+name+';',pkg,{}))

    def test_target_from_another_package_is_not_authority(self):
        targets = {'wrong.image.attitude_rate': self.targets[IMAGE+'.attitude_rate']}
        self.assertNotIn('type-reference', self.render('X : Image.Attitude_Rate;',targets=targets))

    def test_mismatched_source_identity(self):
        pkg = replace(self.pkg, source=self.pkg.source.replace('package AMS.MEL.IR.Image', 'package Wrong.Image'))
        self.assertNotIn('type-reference', self.render('X : Image.Attitude_Rate;',pkg))

    def test_missing_source_owner(self):
        self.assertIsNone(resolve('Image.Attitude_Rate',self.pkg,{},self.targets,{}))

    def test_actual_short_prefix_shadowing_all_defining_contexts(self):
        definitions = [
            'Image : Integer;', 'X, Image : Integer;', 'X : Integer; Image : Integer;',
            'X, -- not a boundary\n Image : Integer;',
            'type Image is range 0 .. 1;', 'subtype Image is Integer;',
            'procedure Image;', 'function Image return Integer;',
            'type E is (First, Image, Last);',
            'procedure Read (Image : Integer; X : Integer);',
            'procedure Read (X, Image : Integer);',
            'type R is record Image : Integer; end record;',
            'type R is record X, Image : Integer; end record;',
            'type R (X, Image : Integer) is null record;',
        ]
        for definition in definitions:
            with self.subTest(definition=definition):
                pkg = self.synthetic(definition)
                self.assertNotIn('type-reference', self.render('X : Image.Attitude_Rate;',pkg))

    def test_unsupported_scopes(self):
        for definition in ('package Nested is end Nested;', 'package Alias renames Other;',
                           'package Instance is new Other;', 'generic type T is private;',
                           'task Worker;', 'protected Lock is end Lock;',
                           'function F return Integer is (1); begin null;'):
            with self.subTest(definition=definition):
                self.assertNotIn('type-reference', self.render('X : Image.Attitude_Rate;',self.synthetic(definition)))

    def test_generic_and_renamed_library_headers(self):
        for source in ('generic\n type T is private;\npackage AMS.MEL.IR.Image is\nend AMS.MEL.IR.Image;',
                       'package AMS.MEL.IR.Image renames Other;'):
            pkg = replace(self.pkg, source=source)
            self.assertNotIn('type-reference', self.render('X : Image.Attitude_Rate;',pkg))

    def test_partial_ancestor_sibling_and_alias_not_added(self):
        for spelling in ('IR.Image.Attitude_Rate', 'MEL.IR.Image.Attitude_Rate',
                         'Status.Euler', 'Other.Attitude_Rate', 'Image.Attitude_Rate.More'):
            with self.subTest(spelling=spelling):
                self.assertNotIn('type-reference', self.render('X : '+spelling+';'))

    def test_defining_expression_default_constraint_attribute_not_added(self):
        for code in ('Image.Attitude_Rate := X;', 'X := Image.Attitude_Rate;',
                     'X : Integer := Image.Attitude_Rate;',
                     'X : Integer range Image.Attitude_Rate .. 9;',
                     "X : Image.Attitude_Rate'Base;", 'X : Integer := (for all V : Image.Attitude_Rate => True);',
                     'X : Integer := F (Image.Attitude_Rate);'):
            with self.subTest(code=code):
                self.assertNotIn('type-reference', self.render(code))

    def test_literals_comments_and_no_partial_tokens(self):
        for code in ('-- X : Image.Attitude_Rate;', 'X : String := "X : Image.Attitude_Rate";',
                     "X : Character := '.'; -- : Image.Attitude_Rate", 'X : Image.Attitude_Rate_Extra;'):
            with self.subTest(code=code):
                result = self.render(code)
                self.assertNotIn('type-reference', result)
                self.assertEqual(plain(highlighted(result)), code)

    def test_full_and_unqualified_existing_behavior(self):
        for spelling in ('Attitude_Rate', 'AMS.MEL.IR.Image.Attitude_Rate'):
            self.assertEqual(TYPE_LINK.findall(self.render('X : '+spelling+';'))[0][1], IMAGE+'.attitude_rate')

    def test_private_library_package_source_declined(self):
        pkg = replace(self.pkg,source=self.pkg.source.replace('package AMS.MEL.IR.Image','private package AMS.MEL.IR.Image',1))
        self.assertNotIn('type-reference',self.render('X : Image.Attitude_Rate;',pkg))

    def test_no_external_fallback_for_missing_local_target(self):
        config = replace(self.config,externals={'image.attitude_rate':'https://wrong.invalid/#wrong'})
        self.assertNotIn('type-reference',self.render('X : Image.Attitude_Rate;',targets={},config=config))

    def test_same_line_private_part_cannot_authorize_private_target(self):
        pkg = self.synthetic('private type Hidden is range 0 .. 9; Image : Integer;')
        self.assertNotIn('type-reference',self.render('X : Image.Hidden;',pkg,{}))

    def test_partial_private_view_aspect_cannot_conceal_later_shadow(self):
        pkg = self.synthetic('type View is private with Size => 8; Image : Integer;')
        self.assertNotIn('type-reference',self.render('X : Image.Attitude_Rate;',pkg))

    def test_implicit_inherited_definitions_conservatively_declined(self):
        pkg = self.synthetic('type Derived is new Other.Enum_With_Image_Literal;')
        self.assertNotIn('type-reference',self.render('X : Image.Attitude_Rate;',pkg))

    def test_authentic_native_source_spelling_and_provenance(self):
        for key,data in PROVENANCE['packages'].items():
            self.assertEqual(len(data['git_blob']),40)
            for entry in data['entries']:
                with self.subTest(package=key,name=entry['name']):
                    # GNATdoc may project an enum/record but these retained
                    # snippets are complete exact type declarations.
                    normalize = lambda s:' '.join(s.split())
                    self.assertEqual(normalize(entry['declaration']),normalize(entry['native']))
                    self.assertEqual(entry['source_end']-entry['source_start'],len(entry['declaration']))


class IndependentOccurrenceMutations(unittest.TestCase):
    """Explicit synthetic markup; expectations predate candidate output."""
    def setUp(self):
        self.q = qualifier()
        self.text = 'X : Image.Attitude_Rate;'
        entry = next(e for e in PROVENANCE['packages'][IMAGE]['entries'] if e['name']=='Attitude_Rate')
        self.href = entry['page']+'#'+entry['anchor']
        self.identity = IMAGE+'.attitude_rate'
        self.expected = [{'start':4,'end':23,'identity':self.identity,'href':self.href}]
        self.raw = 'X : <a class="type-reference" href="'+self.href+'" data-type="'+self.identity+'">Image.Attitude_Rate</a>;'

    def reject(self, raw):
        with self.assertRaisesRegex(ValueError,'independent audit'):
            self.q.check_snippet(raw,self.text,self.expected)

    def test_correct_occurrence(self):
        self.assertEqual(self.q.check_snippet(self.raw,self.text,self.expected),self.text)

    def test_wrong_existing_anchor(self):
        other = PROVENANCE['packages'][IMAGE]['entries'][0]
        self.reject(self.raw.replace(self.href,other['page']+'#'+other['anchor']))

    def test_wrong_existing_page(self):
        other = PROVENANCE['packages'][INSTRUMENTATION]['entries'][0]
        self.reject(self.raw.replace(self.href,other['page']+'#'+other['anchor']))

    def test_consistently_forged_identity_href(self):
        other = PROVENANCE['packages'][IMAGE]['entries'][0]
        self.reject(self.raw.replace(self.identity,IMAGE+'.'+other['name'].lower()).replace(self.href,other['page']+'#'+other['anchor']))

    def test_updated_manifest_hash_cannot_grant_authority(self):
        wrong = self.raw.replace(self.href,self.href.replace('#','#wrong'))
        forged_manifest = {'output_sha256':{'page.html':self.q.sha(wrong.encode())},'counts':{'linked_types':1}}
        self.assertEqual(forged_manifest['output_sha256']['page.html'],self.q.sha(wrong.encode()))
        self.reject(wrong)  # manifest is intentionally not an oracle argument

    def test_required_link_removed(self):
        self.reject(self.text)

    def test_extra_unsupported_link(self):
        self.reject(self.raw.replace('X :','<a class="type-reference" href="'+self.href+'" data-type="'+self.identity+'">X</a> :'))

    def test_previously_qualified_destination_changed(self):
        text = 'X : North_East_Down;'
        old = next(e for e in PROVENANCE['packages'][IMAGE]['entries'] if e['name']=='North_East_Down')
        expected = [{'start':4,'end':19,'identity':IMAGE+'.north_east_down','href':old['page']+'#'+old['anchor']}]
        wrong = 'X : <a class="type-reference" href="'+self.href+'" data-type="'+IMAGE+'.north_east_down">North_East_Down</a>;'
        with self.assertRaises(ValueError):self.q.check_snippet(wrong,text,expected)

    def test_partial_token_link(self):
        self.reject(self.raw.replace('Image.Attitude_Rate</a>','Image</a>.Attitude_Rate'))

    def test_changed_visible_text(self):
        self.reject(self.raw.replace('Image.Attitude_Rate</a>','image.Attitude_Rate</a>'))


if __name__ == '__main__':
    unittest.main()