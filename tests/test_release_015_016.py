"""Fail-closed current release differential; historical comparators stay intact."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('release_015_016', SCRIPTS / 'compare_release_015_016.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class Release015016Contracts(unittest.TestCase):
    def publications(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        old, new = (Path(temp.name) / n for n in ('old', 'new'))
        for root, version in ((old, '0.1.5'), (new, '0.1.6')):
            (root / 'api').mkdir(parents=True)
            (root / 'api/index.html').write_bytes(b'unchanged shell')
            (root / 'api/presentation.json').write_text(json.dumps(
                dict(enhancer_version=version, output_sha256={}, native=['unchanged'])))
        return old, new

    def test_version_only_preserves_every_other_byte(self):
        result = audit.compare(*self.publications())
        self.assertEqual(result['changed_files'], ['api/presentation.json'])
        self.assertTrue(result['all_other_bytes_equal'])

    def test_reject_unexplained_differences_even_with_rehashed_manifest(self):
        for mutation in ('extra', 'missing', 'native', 'router', 'css', 'format', 'symlink',
                         'manifest', 'wrong-version', 'search-without-source', 'rehash'):
            with self.subTest(mutation=mutation):
                old, new = self.publications()
                manifest = new / 'api/presentation.json'
                data = json.loads(manifest.read_bytes())
                if mutation == 'extra': (new / 'extra').write_bytes(b'new')
                if mutation == 'missing': (new / 'api/index.html').unlink()
                if mutation in ('native', 'rehash'): (new / 'api/index.html').write_bytes(b'forged')
                if mutation in ('router', 'css'):
                    for root in (old, new):
                        (root / ('api/runtime.' + mutation)).write_bytes(str(root).encode())
                if mutation == 'symlink': (new / 'alias').symlink_to(new / 'api/index.html')
                if mutation == 'manifest': data['native'] = []
                if mutation == 'wrong-version': data['enhancer_version'] = '0.1.5'
                if mutation == 'search-without-source':
                    for root in (old, new):
                        (root / audit.INDEX).write_text(json.dumps({'records': [str(root)]}))
                if mutation == 'rehash': data['output_sha256']['api/index.html'] = audit.digest(b'forged')
                manifest.write_text(json.dumps(data, indent=2) if mutation == 'format' else json.dumps(data))
                with self.assertRaises(ValueError): audit.compare(old, new)

    def test_root_alias_is_rejected(self):
        old, new = self.publications()
        alias = new.parent / 'alias'
        alias.symlink_to(new, target_is_directory=True)
        with self.assertRaises(ValueError): audit.compare(old, alias)

    def test_search_authority_is_exact_not_just_count_and_hash(self):
        record = dict(kind='operation', href='page.html#anchor', name='P.Call', label='P.Call', text='')
        payload = audit.sorted_json(dict(schema_version=1, records=[record])).encode()
        shell = audit.authority([record], payload)
        self.assertEqual(audit.AUTHORITY.fullmatch(shell)[0], shell)
        self.assertIn('data-count="1"', shell)
        self.assertIn(audit.digest(payload), shell)
        self.assertIn('target="document-content"', shell)

    def test_source_backed_search_additions_and_forged_records(self):
        from dataclasses import replace
        from ada_gnatdoc_enhancer.errors import EnhancementError
        from ada_gnatdoc_enhancer.pipeline import enhance
        from _helper import Fixture
        fx = Fixture()
        self.addCleanup(fx.cleanup)
        config = replace(fx.config, search=True)
        enhance(config, fx.site)
        new = fx.site
        old = new.parent / 'official-shaped-synthetic'
        shutil.copytree(new, old)
        # Synthetic predecessor omits one real declaration; this tests the
        # comparator, not official-release acquisition (separate integration).
        data = json.loads((old / audit.INDEX).read_bytes())
        removed = next(r for r in data['records'] if r['kind'] == 'symbol')
        data['records'].remove(removed)
        payload = audit.sorted_json(data).encode()
        (old / audit.INDEX).write_bytes(payload)
        shell = (old / audit.SHELL).read_text()
        (old / audit.SHELL).write_text(audit.AUTHORITY.sub(
            lambda _: audit.authority(data['records'], payload), shell))
        manifest = json.loads((old / audit.MANIFEST).read_bytes())
        manifest['enhancer_version'] = '0.1.5'
        for name in (audit.INDEX, audit.SHELL):
            manifest['output_sha256'][name] = audit.digest((old / name).read_bytes())
        (old / audit.MANIFEST).write_text(audit.sorted_json(manifest))
        result = audit.compare(old, new, config=config)
        self.assertEqual(result['added_records'], [removed])
        self.assertEqual(result['added_declarations'], 1)
        # An attacker may reseal all output hashes, but cannot manufacture
        # source/native authority. Existing search adversarial tests cover all
        # private/nested/formal shapes as well as runtime allowlist resealing.
        for field, value in (('href', 'page.html#invented'), ('text', 'forged signature'),
                             ('name', 'Private.Invented'), ('kind', 'guide')):
            with self.subTest(field=field):
                path = new / audit.INDEX
                original = path.read_bytes()
                candidate = json.loads(original)
                candidate['records'].append(dict(removed, **{field: value}))
                path.write_text(audit.sorted_json(candidate))
                with self.assertRaises((ValueError, EnhancementError)):
                    audit.compare(old, new, config=config)
                path.write_bytes(original)
        # Even a fully resealed index/shell/manifest cannot authorize an invented
        # declaration. This specifically exercises reconstruction, not a stale
        # digest rejection.
        index_path = new / audit.INDEX
        data = json.loads(index_path.read_bytes())
        data['records'].append(dict(removed, href='page.html#invented', name='Private.Invented'))
        data['records'].sort(key=lambda r: (r['name'].lower(), r['kind']))
        payload = audit.sorted_json(data).encode()
        index_path.write_bytes(payload)
        shell_path = new / audit.SHELL
        shell_path.write_text(audit.AUTHORITY.sub(
            lambda _: audit.authority(data['records'], payload), shell_path.read_text()))
        manifest = json.loads((new / audit.MANIFEST).read_bytes())
        for name in (audit.INDEX, audit.SHELL):
            manifest['output_sha256'][name] = audit.digest((new / name).read_bytes())
        (new / audit.MANIFEST).write_text(audit.sorted_json(manifest))
        with self.assertRaises((ValueError, EnhancementError)):
            audit.compare(old, new, config=config)