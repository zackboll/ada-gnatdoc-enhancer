"""Complete retained MEL input, independent flat-source oracle, not count authority."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.search import records
from ada_gnatdoc_enhancer.util import digest

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT/'tests/real-fixtures/search-mel'
spec = importlib.util.spec_from_file_location('search_scope_qualification', ROOT/'scripts/qualify_search_scopes.py')
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class CompleteMEL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected, cls.excluded, _ = qualification.oracle(REAL/'authority', REAL/'pristine')
        cls.config = load(REAL/'authority', 'docs/gnatdoc-enhance.toml')
        cls.actual = records(cls.config, snapshot(cls.config, REAL/'pristine'), {})

    def test_all_fixture_bytes_pinned(self):
        provenance = json.loads((REAL/'provenance.json').read_text())
        for name, sha in provenance['files'].items():
            self.assertEqual(digest((REAL/name).read_bytes()), sha, name)

    def test_complete_eligible_inventory_and_exact_signatures(self):
        expected = {r['href']:r for r in self.expected}
        actual = {r['href']:r for r in self.actual}
        self.assertEqual(len(actual), len(self.actual))
        self.assertEqual(set(expected), set(actual))
        for href, record in expected.items():
            self.assertEqual((actual[href]['name'], actual[href]['kind']), (record['name'], record['kind']))
            if record['signature']:
                self.assertIn(' '.join(record['signature'].split()), actual[href]['text'])
        self.assertTrue(self.excluded)
        self.assertFalse({r['href'] for r in self.excluded if 'href' in r} & set(actual))

    def test_exact_before_after_without_existing_record_changes(self):
        before = {r['href']:r for r in json.loads((REAL/'before.json').read_text())}
        after = {r['href']:r for r in self.actual}
        self.assertTrue(set(before) <= set(after))
        self.assertEqual({h:after[h] for h in before}, before)
        added = [r for h,r in after.items() if h not in before]
        self.assertEqual(Counter(r['name'].rsplit('.',1)[0] for r in added), {
            'AMS.MEL.Status':157, 'AMS.MEL.IR.Channel':68, 'AMS.MEL.IR.C2':51,
            'AMS.MEL.IR.Health_Status.Metadata':47, 'AMS.MEL.IR.Calibration_Configuration':19,
            'AMS.MEL.IR.NUC':5, 'AMS.MEL.IR.Discovery':1})

    def test_two_independent_complete_outputs(self):
        from argparse import Namespace
        with tempfile.TemporaryDirectory() as folder:
            qualification.run(Namespace(source_root=REAL/'authority', native=REAL/'pristine',
                before=REAL/'before.json', output=Path(folder)/'qualification', browser=False))