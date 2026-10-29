"""Additive malformed-wheel controls for the release archive reader."""
import importlib.util
import base64
import hashlib
from pathlib import Path
import stat
import io
import tarfile
import tempfile
import unittest
from unittest.mock import patch
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


class ReleaseArchiveIdentity(unittest.TestCase):
    def sdist(self, names, kind=tarfile.REGTYPE):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name)/'candidate.tar.gz'
        with tarfile.open(path, 'w:gz') as archive:
            for name in names:
                member = tarfile.TarInfo(name)
                member.type = kind
                if kind == tarfile.REGTYPE:
                    member.size = 7
                    archive.addfile(member, io.BytesIO(b'content'))
                else:
                    archive.addfile(member)
        return path

    def test_sdist_rejects_unauthorized_versions_and_paths(self):
        for name in ('ada_gnatdoc_enhancer-0.1.0/module.py', '/absolute',
                     'ada_gnatdoc_enhancer-0.1.1/module.py',
                     'ada_gnatdoc_enhancer-0.1.2/../escape'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unsafe sdist path'):
                audit.sdist_files(self.sdist([name]))
        name = 'ada_gnatdoc_enhancer-0.1.2/module.py'
        self.assertEqual(audit.sdist_files(self.sdist([name])), {'module.py': b'content'})

    def test_sdist_rejects_nonregular_and_duplicate_members(self):
        name = 'ada_gnatdoc_enhancer-0.1.2/module.py'
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE,
                     tarfile.CHRTYPE, tarfile.BLKTYPE):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'nonregular sdist member'):
                audit.sdist_files(self.sdist([name], kind))
        with self.assertRaisesRegex(ValueError, 'duplicate sdist members'):
            audit.sdist_files(self.sdist([name, name]))

    def test_source_cannot_authorize_its_own_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source/'pyproject.toml').write_text('[project]\nversion = "0.1.0"\n')
            with self.assertRaisesRegex(ValueError, 'wrong source version'):
                audit.audit(source, source/'absent.whl', source/'absent.tar.gz', source/'rebuilt.whl')

    def test_previous_release_source_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source/'pyproject.toml').write_text('[project]\nversion = "0.1.1"\n')
            with self.assertRaisesRegex(ValueError, 'wrong source version'):
                audit.audit(source, source/'absent.whl', source/'absent.tar.gz', source/'rebuilt.whl')

    def test_previous_release_wheel_metadata_is_rejected_even_when_renamed(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source/'pyproject.toml').write_text('[project]\nversion = "0.1.2"\n')
            wheel = source/'ada_gnatdoc_enhancer-0.1.2-py3-none-any.whl'
            sdist = source/'ada_gnatdoc_enhancer-0.1.2.tar.gz'
            content = {'ada_gnatdoc_enhancer-0.1.2.dist-info/METADATA':
                       b'Name: ada-gnatdoc-enhancer\nVersion: 0.1.1\n'}
            with patch.object(audit, 'wheel_files', return_value=content), \
                 patch.object(audit, 'sdist_files', return_value={}):
                with self.assertRaisesRegex(ValueError, 'metadata version mismatch'):
                    audit.audit(source, wheel, sdist, wheel)


class WheelRecordContracts(unittest.TestCase):
    def content(self):
        digest = base64.urlsafe_b64encode(hashlib.sha256(b'content').digest()).rstrip(b'=').decode()
        return {'module.py': b'content', 'package.dist-info/RECORD':
                ('module.py,sha256='+digest+',7\npackage.dist-info/RECORD,,\n').encode()}

    def test_complete_record_hashes_and_sizes_are_verified(self):
        audit.verify_record(self.content(), 'package.dist-info/')

    def test_changed_content_or_record_is_rejected(self):
        for mutation in ('bytes', 'size', 'missing', 'duplicate', 'self', 'malformed'):
            with self.subTest(mutation=mutation):
                content = self.content()
                key = 'package.dist-info/RECORD'
                if mutation == 'bytes':content['module.py'] = b'changed'
                if mutation == 'size':content[key] = content[key].replace(b',7\n', b',8\n')
                if mutation == 'missing':content[key] = b'package.dist-info/RECORD,,\n'
                if mutation == 'duplicate':content[key] += b'module.py,,\n'
                if mutation == 'self':content[key] = content[key].replace(b'RECORD,,', b'RECORD,sha256=bad,0')
                if mutation == 'malformed':content[key] = b'module.py\n'
                with self.assertRaises(ValueError):audit.verify_record(content, 'package.dist-info/')