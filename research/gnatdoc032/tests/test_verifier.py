"""Offline parser/authority tests and opt-in authentic compiler integration."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import verifier as v

ALI = '''V "GNAT Lib v16"
D p.ads 20261031000000 aaaaaaaa p%s
D main.adb 20261031000000 bbbbbbbb main%b
X 1 p.ads
2V13*Pick{integer} 2|4s9 5s9
3V13*Pick{integer} 2|6s9
X 2 main.adb
1U11*Main 1b11 8t5
'''


class ParserTests(unittest.TestCase):
    def evidence(self, text=ALI):
        e = v.Evidence.__new__(v.Evidence)
        e.index = v.parse_ali(text)
        e.root = Path('/snapshot')
        e.snapshot = {'p.ads': 'a' * 64, 'main.adb': 'b' * 64}
        e.by_name = {'p.ads': ['p.ads'], 'main.adb': ['main.adb']}
        e.receipt = {'sources': ['/snapshot/main.adb']}
        return e

    def request(self, line=4, declaration=2):
        return ({'file': 'main.adb', 'line': line, 'column': 9},
                {'file': 'p.ads', 'line': declaration, 'column': 13,
                 'sha256': 'a' * 64, 'kind': 'SubpDecl'})

    def test_exact_static_call(self):
        result = self.evidence().compare(*self.request())
        self.assertEqual(result['status'], 'COMPILER_IDENTITY_CONFIRMED')
        self.assertEqual(result['compiler_selected']['line'], 2)
        self.assertNotIn('hyperlink', result)

    def test_same_name_different_positions(self):
        self.assertEqual(self.evidence().compare(*self.request(6, 3))['status'], 'COMPILER_IDENTITY_CONFIRMED')
        self.assertEqual(self.evidence().compare(*self.request(6, 2))['status'], 'COMPILER_IDENTITY_MISMATCH')

    def test_wrong_identity_never_invokes_native(self):
        result = self.evidence().compare(*self.request(4, 3))
        self.assertEqual(result['status'], 'COMPILER_IDENTITY_MISMATCH')
        # Native arguments are deliberately invalid; mismatches return BEFORE
        # importing/reconciling or reading any native input.
        self.assertEqual(v.native_link(result, None, None, None, None, None), result)
        self.assertNotIn('hyperlink', result)

    def test_each_identity_coordinate_and_hash(self):
        for field, value in [('line', 3), ('column', 12), ('file', 'else.ads'), ('sha256', '0' * 64)]:
            call, selected = self.request()
            selected[field] = value
            self.assertEqual(self.evidence().compare(call, selected)['status'], 'COMPILER_IDENTITY_MISMATCH')

    def test_missing_exact_occurrence(self):
        call, selected = self.request()
        call['column'] += 1
        self.assertEqual(self.evidence().compare(call, selected)['status'], 'COMPILER_EVIDENCE_MISSING')

    def test_conflicting_records(self):
        text = ALI.replace('2|6s9', '2|4s9')
        self.assertEqual(self.evidence(text).compare(*self.request())['status'], 'AMBIGUOUS')

    def test_identical_duplicate_evidence(self):
        e = self.evidence()
        e.index[('main.adb', 4, 9)] *= 2
        self.assertEqual(e.compare(*self.request())['status'], 'COMPILER_IDENTITY_CONFIRMED')

    def test_dispatching_and_noncall(self):
        for code in ['R', 'r', 'i', 'b']:
            e = self.evidence(ALI.replace('4s9', '4' + code + '9'))
            self.assertEqual(e.compare(*self.request())['status'], 'UNSUPPORTED')

    def test_instance_renaming_overriding(self):
        for meta in ['[1|8]', '=2:19', '<1|2o13>']:
            e = self.evidence(ALI.replace('2V13*Pick{integer}', '2V13*Pick' + meta + '{integer}'))
            self.assertEqual(e.compare(*self.request())['status'], 'UNSUPPORTED')

    def test_unsupported_lal_form(self):
        call, selected = self.request()
        selected['kind'] = 'GenericSubpInstantiation'
        self.assertEqual(self.evidence().compare(call, selected)['status'], 'UNSUPPORTED')

    def test_continuation_and_file_state(self):
        text = ALI.replace('2|4s9 5s9', '2|4s9\n. 5s9')
        self.assertEqual(self.evidence(text).compare(*self.request(5))['status'], 'COMPILER_IDENTITY_CONFIRMED')

    def test_malformed_and_truncated(self):
        for text in [ALI[:-1], ALI.replace('X 1 p.ads', 'X 1 other.ads'),
                     ALI.replace('2|4s9', '99|4s9'), ALI.replace('2|4s9', 'corrupt')]:
            with self.assertRaises(v.Rejected):
                v.parse_ali(text)

    def test_generic_suffix_rejected_not_silently_dropped(self):
        with self.assertRaisesRegex(v.Rejected, 'generic reference suffix'):
            v.parse_ali(ALI.replace('2|4s9', '2|4s9[1|8]'))

    def test_operator_grammar_not_approximated(self):
        with self.assertRaises(v.Rejected):
            v.parse_ali(ALI.replace('Pick', '"+"'))

    def test_missing_or_rewritten_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            with self.assertRaises(v.Rejected) as missing:
                v.Evidence(path, '0' * 64, Path(directory), path)
            self.assertEqual(missing.exception.status, 'COMPILER_EVIDENCE_MISSING')
            path.write_text('{}')
            with self.assertRaises(v.Rejected) as stale:
                v.Evidence(path, '0' * 64, Path(directory), path)
            self.assertEqual(stale.exception.status, 'COMPILER_EVIDENCE_STALE')

    def test_duplicate_basename_fail_closed(self):
        e = self.evidence()
        e.by_name['main.adb'].append('other/main.adb')
        self.assertEqual(e.compare(*self.request())['status'], 'AMBIGUOUS')

    def test_missing_selected_field_is_analysis_error(self):
        call, selected = self.request()
        del selected['line']
        self.assertEqual(self.evidence().compare(call, selected)['status'], 'ANALYSIS_ERROR')


@unittest.skipUnless(os.environ.get('GNATDOC032_INTEGRATION_ARGS'),
                     'private GNAT/LAL/Core/native integration arguments required')
class AuthenticIntegration(unittest.TestCase):
    def test_real_controls(self):
        args = json.loads(os.environ['GNATDOC032_INTEGRATION_ARGS'])
        with tempfile.TemporaryDirectory() as directory:
            proc = subprocess.run([sys.executable, *(['-O'] if sys.flags.optimize else []),
                                   str(HERE / 'controls.py'), '--workspace', directory + '/run', *args],
                                  capture_output=True, text=True, timeout=120)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((Path(directory) / 'run/results.json').read_text())
            self.assertEqual(report['disposition'], 'PROTOTYPE_SUCCESS')
            self.assertEqual(len(report['positive']), 16)
            self.assertEqual(len(report['unsupported']), 3)
            self.assertEqual(report['skipped'], [])


if __name__ == '__main__':
    unittest.main()