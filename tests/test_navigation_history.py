"""Execute the installed JavaScript asset against deterministic DOM/event doubles.

Node is a test-only tool already available on the hosted Ubuntu runners. Actual
Chromium/profile qualification remains in the separate real-site harness.
"""
import subprocess
import unittest
from importlib.resources import files
from pathlib import Path


class NavigationHistory(unittest.TestCase):
    pass


def regression(scenario):
    def test(self):
        asset = files('ada_gnatdoc_enhancer').joinpath('assets/gnatdoc-navigation.js')
        result = subprocess.run(['node', str(Path(__file__).with_name('navigation_history.cjs')),
                                 str(asset), scenario], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    return test


for scenario in ('package', 'deep', 'unknown_package', 'unknown_declaration', 'wrong_package',
                 'duplicate_package', 'duplicate_declaration', 'malformed', 'injection',
                 'malformed_fragment', 'history', 'same_selection', 'stale_load', 'invalid_pop',
                 'external_frame', 'unqualified_frame', 'native_click', 'search',
                 'outer_fragment', 'bad_links'):
    setattr(NavigationHistory, 'test_' + scenario, regression(scenario))