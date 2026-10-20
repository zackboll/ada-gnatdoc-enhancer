"""Additive URL-writer contracts; real-site Chromium coverage is separate."""
import json
import subprocess
import unittest
from importlib.resources import files


class SymbolCanonicalization(unittest.TestCase):
    def check_writer(self, query, state, expected):
        script = files('ada_gnatdoc_enhancer').joinpath(
            'assets/gnatdoc-symbol-navigation.js').read_text()
        # Exercise the actual packaged function, not a Python reimplementation.
        body = script.split('  function canonicalUrl(state) {', 1)[1].split(
            '\n  function targetFromUrl()', 1)[0]
        program = ('const assert=require("node:assert/strict");'
                   'const location={href:' + json.dumps('https://docs.invalid/api/index.html' + query) + '};'
                   'function canonicalUrl(state) {' + body + '\n'
                   'assert.equal(canonicalUrl(' + json.dumps(state) + ').href,' +
                   json.dumps('https://docs.invalid/api/index.html' + expected) + ');')
        result = subprocess.run(['node', '-e', program], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def regression(query, kind):
    def test(self):
        state = {'item': {'name': 'AMS.MEL'}}
        expected = '?package=AMS.MEL'
        if kind == 'symbol':
            state.update(symbol='AMS.MEL.Session', declaration='a' * 64)
            expected += '&symbol=AMS.MEL.Session'
        elif kind == 'declaration':
            state['declaration'] = 'a' * 64
            expected += '&declaration=' + 'a' * 64
        self.check_writer(query, state, expected)
    return test


for label, query in {
        'unknown': '?package=AMS.MEL&unknown=1',
        'duplicate': '?package=Other&package=AMS.MEL&symbol=Invalid&symbol=Other',
        'encoded': '?%70ackage=Other&unknown=%26symbol%3DInjected',
        'fragment': '?package=Other#instance-members-summary',
        'foreign_fragment': '?unknown=1#https://example.invalid/',
        'conflicting': '?symbol=Unknown&declaration=Unknown&package=Unknown',
}.items():
    for kind in ('package', 'symbol', 'declaration'):
        setattr(SymbolCanonicalization, 'test_' + label + '_' + kind, regression(query, kind))