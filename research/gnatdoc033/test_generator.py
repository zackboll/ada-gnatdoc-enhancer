"""Real opt-in generator tests, kept outside installed compiler-free runtime.

GNATDOC033_COMPILER enables actual fresh builds, LAL and retained native inputs.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generate_verified_examples', REPO / 'scripts/generate_verified_examples.py')
generator = importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)


@unittest.skipUnless(os.environ.get('GNATDOC033_COMPILER'), 'qualified GNAT/LAL environment required')
class Generator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name); self.root = self.work / 'source'
        fixture = REPO / 'tests/verified-fixtures/overloads'
        self.root.mkdir()
        data = json.loads((fixture / 'mapping.json').read_text())
        for name in data['inputs']:
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixture / name, target)
        self.presentation = self.work / 'presentation'
        shutil.copytree(fixture / 'public', self.presentation / 'public')
        shutil.copytree(fixture / 'native', self.work / 'native')
        # The retained complete source context, no invented wrapper declarations.
        self.compiler = Path(os.environ['GNATDOC033_COMPILER'])
        self.presentation.joinpath('generator.toml').write_text('schema_version = 1\nproject = "test"\n[sources]\ndirectories = ["public"]\n')

    def generate(self, name):
        return generator.generate(self.root, self.root / 'fixtures.gpr', [self.root / 'valid.adb'],
                                  self.compiler, self.work / name, 'generator.toml', self.work / 'native',
                                  presentation_root=self.presentation)

    def test_fresh_compilation_once_and_deterministic_portable_output(self):
        with patch.object(generator.v, 'generate', wraps=generator.v.generate) as compile_units:
            first = self.generate('one')
        self.assertEqual(compile_units.call_count, 1)
        receipt = json.loads((self.work / 'one.receipt.json').read_text())
        self.assertEqual(len(receipt['runs']), 1)
        for path in self.root.rglob('*'):
            if path.is_file(): os.utime(path, (1700000000, 1700000000))
        relocated = self.work / 'relocated-source'
        self.root.rename(relocated); self.root = relocated
        second = self.generate('two')
        self.assertEqual(first, second)
        self.assertEqual(len(first['mappings']), 12)
        self.assertNotIn(str(self.work), json.dumps(first))
        self.assertTrue(all(m['compiler_selected'] == {k: v for k, v in m['selected'].items() if k != 'kind'}
                            for m in first['mappings']))

    def test_wrong_overload_injection_never_emits_mapping(self):
        select = generator.v.SelectionSession.select
        def wrong(session, occurrence):
            selected, declaration, profile = select(session, occurrence)
            if occurrence['line'] == 6:
                selected = copy.deepcopy(selected); selected['line'] = 5
            return selected, declaration, profile
        with patch.object(generator.v.SelectionSession, 'select', wrong):
            result = self.generate('wrong')
        self.assertEqual(len(result['mappings']), 11)
        rejected = next(s for s in result['skipped'] if s['line'] == 6)
        self.assertEqual(rejected['status'], 'COMPILER_IDENTITY_MISMATCH')
        self.assertNotIn(6, [m['occurrence']['line'] for m in result['mappings']])

    def test_unsupported_canonical_form_never_emits_mapping(self):
        select = generator.v.SelectionSession.select
        def unsupported(session, occurrence):
            selected, declaration, profile = select(session, occurrence)
            if occurrence['line'] == 6:
                selected = copy.deepcopy(selected); selected['kind'] = 'GenericSubpInstantiation'
            return selected, declaration, profile
        with patch.object(generator.v.SelectionSession, 'select', unsupported):
            result = self.generate('unsupported')
        self.assertEqual(next(s for s in result['skipped'] if s['line'] == 6)['status'], 'UNSUPPORTED')

    def test_snapshot_mutation_during_selection_rejected(self):
        select = generator.v.SelectionSession.select
        def mutate(session, occurrence):
            result = select(session, occurrence)
            if occurrence['line'] == 6:
                p = self.root / 'fixtures.gpr'; p.write_text(p.read_text() + '\n-- changed\n')
            return result
        with patch.object(generator.v.SelectionSession, 'select', mutate):
            with self.assertRaisesRegex(generator.v.Rejected, 'snapshot changed'):
                self.generate('stale')


if __name__ == '__main__': unittest.main()