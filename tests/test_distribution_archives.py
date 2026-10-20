"""Additive malformed-wheel controls for the release archive reader."""
import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile


spec = importlib.util.spec_from_file_location(
    'release_archive_audit', Path(__file__).resolve().parents[1]/'scripts/check_distributions.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class WheelArchiveContracts(unittest.TestCase):
    def wheel(self, name, mode=0):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name)/'candidate.whl'
        member = zipfile.ZipInfo(name)
        member.create_system = 3
        member.external_attr = mode << 16
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(member, b'content')
        return path

    def test_nonregular_members_rejected(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFSOCK):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, 'nonregular wheel member'):
                    audit.wheel_files(self.wheel('package.dist-info/link', kind | 0o777))

    def test_unsafe_and_duplicate_members_rejected(self):
        for name in ('/absolute', '../escape', 'package/../../escape'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, 'unsafe wheel path'):
                    audit.wheel_files(self.wheel(name))
        path = self.wheel('duplicate')
        with self.assertWarns(UserWarning):
            with zipfile.ZipFile(path, 'a') as archive:
                archive.writestr('duplicate', b'other')
        with self.assertRaisesRegex(ValueError, 'duplicate wheel members'):
            audit.wheel_files(path)

    def test_regular_and_untyped_members_accepted(self):
        for mode in (0, 0o600, stat.S_IFREG | 0o644):
            with self.subTest(mode=mode):
                self.assertEqual(audit.wheel_files(self.wheel('package/module.py', mode)),
                                 {'package/module.py': b'content'})
        self.assertEqual(audit.wheel_files(self.wheel('package/', stat.S_IFDIR | 0o755)), {})
        with self.assertRaisesRegex(ValueError, 'invalid wheel directory'):
            audit.wheel_files(self.wheel('not-a-directory', stat.S_IFDIR | 0o755))