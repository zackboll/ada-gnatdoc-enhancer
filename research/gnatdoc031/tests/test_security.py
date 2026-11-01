"""Offline trust-boundary controls; run unchanged with python, -O and -OO.

Synthetic metadata replaces only gh API and local git identity boundaries.
Synthetic ZIP digest is pinned in both modules, never the validation routines.
No fixture record represents actual independent review.
"""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import probe
import provenance as p
import qualify_native as qn
from review_authorization import record_review


def metadata(sha):
    repository = {"id": p.REPOSITORY_ID, "full_name": p.REPOSITORY}
    artifact = {"id": p.ARTIFACT, "name": "gnatdoc-diagnostics-" + p.COMMIT,
                "digest": "sha256:" + sha,
                "url": p.API_ROOT + f"/actions/artifacts/{p.ARTIFACT}",
                "archive_download_url": p.API_ROOT + f"/actions/artifacts/{p.ARTIFACT}/zip",
                "workflow_run": {"id": p.RUN, "head_sha": p.COMMIT,
                                 "repository_id": p.REPOSITORY_ID, "head_repository_id": p.REPOSITORY_ID}}
    run = {"id": p.RUN, "head_sha": p.COMMIT, "status": "completed", "conclusion": "success",
           "event": "push", "head_branch": "main", "path": ".github/workflows/documentation.yml",
           "url": p.API_ROOT + f"/actions/runs/{p.RUN}", "repository": repository,
           "head_repository": repository.copy()}
    return artifact, run


class EvidenceFixture:
    def __init__(self, root):
        self.root = root
        self.checkout = root / "checkout"
        (self.checkout / "src").mkdir(parents=True)
        (self.checkout / "src/p.ads").write_text("package P is end P;\n")
        self.zip_path = root / "input.zip"
        self.output = root / "extraction"
        self.entries = [("obj/docs/git-identities.txt", p.COMMIT + "\n" + p.TREE + "\n"),
                        ("obj/docs/native/api/a.html", "native\n")]

    def acquire(self, entries=None, mutate_metadata=None, git_values=None, output=None, corrupt=False):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
                for name, data in entries if entries is not None else self.entries:
                    archive.writestr(name, data)
        if corrupt:
            data = self.zip_path.read_bytes().replace(b"native\n", b"broken\n", 1)
            self.zip_path.write_bytes(data)
        sha = p.digest(self.zip_path)
        artifact, run = metadata(sha)
        if mutate_metadata:
            mutate_metadata(artifact, run)

        def api(endpoint):
            if endpoint == f"actions/artifacts/{p.ARTIFACT}":
                return json.dumps(artifact).encode()
            if endpoint == f"actions/runs/{p.RUN}":
                return json.dumps(run).encode()
            raise RuntimeError("unexpected network request: " + endpoint)

        values = {("rev-parse", "HEAD"): p.COMMIT, ("rev-parse", "HEAD^{tree}"): p.TREE,
                  ("status", "--porcelain", "--untracked-files=all", "--ignored"): ""}
        values.update(git_values or {})
        with patch.object(qn, "SHA256", sha), patch.object(p, "SHA256", sha), \
                patch.object(qn, "api", side_effect=api), \
                patch.object(qn, "git", side_effect=lambda checkout, *args: values[args]):
            qualification = qn.acquire(self.checkout, self.zip_path, output or self.output)
        # Runtime verification below also needs the synthetic digest pin.
        self.sha = sha
        return qualification

    def approval(self, qualification):
        output = self.root / "test-only-approval.json"
        with patch.object(p, "SHA256", self.sha):
            record_review(qualification, self.checkout, self.output / "native", output,
                          "TEST-ONLY-reviewer", "Synthetic contract control, NOT independent review")
        return output

    def verify(self, qualification, approval=None, reviewers=("TEST-ONLY-reviewer",)):
        with patch.object(p, "SHA256", self.sha):
            return probe.verify_qualification(qualification, self.checkout, self.output / "native",
                                              approval, reviewers)


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = EvidenceFixture(self.root)

    def reject(self, **kwargs):
        with self.assertRaises((ValueError, zipfile.BadZipFile, KeyError)):
            self.fixture.acquire(**kwargs)
        self.assertFalse(self.fixture.output.exists(), "failed acquisition retained usable evidence")
        self.assertFalse((self.root / "escaped").exists())

    def test_wrong_metadata_digest(self):
        self.reject(mutate_metadata=lambda a, r: a.update(digest="sha256:" + "0" * 64))

    def test_wrong_zip_digest(self):
        # Metadata/expected pin remains correct; retained ZIP bytes differ.
        real = hashlib.sha256
        with patch.object(qn.hashlib, "sha256", wraps=hashlib.sha256) as sha:
            # First hash defines controlled expected digest; second is acquisition.
            sha.side_effect = lambda data: real(data if sha.call_count == 1 else data + b"changed")
            self.reject()

    def test_commit_tree_and_checkout_cleanliness(self):
        cases = [dict(mutate_metadata=lambda a, r: r.update(head_sha="0" * 40)),
                 dict(git_values={("rev-parse", "HEAD"): "0" * 40}),
                 dict(git_values={("rev-parse", "HEAD^{tree}"): "0" * 40}),
                 dict(git_values={("status", "--porcelain", "--untracked-files=all", "--ignored"): "?? untracked"}),
                 dict(git_values={("status", "--porcelain", "--untracked-files=all", "--ignored"): "!! ignored"}),
                 dict(entries=[(self.fixture.entries[0][0], "0" * 40 + "\n" + p.TREE), self.fixture.entries[1]]),
                 dict(entries=[(self.fixture.entries[0][0], p.COMMIT + "\n" + "0" * 40), self.fixture.entries[1]])]
        for case in cases:
            with self.subTest(case=case):
                self.reject(**case)

    def test_duplicate_and_normalized_conflicts(self):
        for name in ("obj/docs/native/api/a.html", "obj/docs/native/api/A.HTML",
                     "obj/docs/native/api/a.html/child"):
            with self.subTest(name=name):
                self.reject(entries=self.fixture.entries + [(name, "conflict")])

    def test_traversal_absolute_and_noncanonical_paths(self):
        for name in ("obj/docs/native/../../escaped", "/escaped", "C:/escaped",
                     "obj/docs/native/api/../escaped", "obj/docs/native/api//escaped",
                     "obj/docs/native/api//",
                     "obj/docs/native/./escaped", "obj\\docs\\native\\escaped",
                     "elsewhere/../../escaped"):
            with self.subTest(name=name):
                self.reject(entries=self.fixture.entries + [(name, "escape")])

    def test_unsafe_archive_member_types(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK, stat.S_IFBLK):
            member = zipfile.ZipInfo("obj/docs/native/unsafe")
            member.create_system = 3
            member.external_attr = (kind | 0o777) << 16
            with self.subTest(kind=kind):
                self.reject(entries=self.fixture.entries + [(member, "../../escaped")])

    def test_zip_integrity(self):
        self.reject(corrupt=True)

    def test_unsafe_or_escaping_destination(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.root / "link"
        link.symlink_to(outside, target_is_directory=True)
        for output in (Path("relative"), self.root / ".." / "escaped", link / "escaped", link, outside):
            with self.subTest(output=output):
                self.reject(output=output)
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_and_inconsistent_authenticated_metadata(self):
        mutations = [lambda a, r: a.clear(), lambda a, r: r.clear(),
                     lambda a, r: a.update(id=0), lambda a, r: a["workflow_run"].update(id=0),
                     lambda a, r: r.update(id=0), lambda a, r: r.update(status="in_progress"),
                     lambda a, r: r.update(conclusion="failure"), lambda a, r: r.update(event="pull_request"),
                     lambda a, r: a.update(name="other"), lambda a, r: r["repository"].update(id=0),
                     lambda a, r: r.update(url="https://untrusted.example"),
                     lambda a, r: r.pop("repository")]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.reject(mutate_metadata=mutation)

    def test_valid_acquisition_never_authorizes(self):
        qualification = self.fixture.acquire()
        q = json.loads(qualification.read_text())
        self.assertEqual(q["state"], "VERIFIED")
        self.assertTrue(q["acquired"] and q["verified"])
        self.assertNotIn("reviewed", q)
        with self.assertRaisesRegex(ValueError, "missing explicit review"):
            self.fixture.verify(qualification)
        self.assertFalse(any("approval" in f.name for f in self.fixture.output.iterdir()))

    def test_explicit_test_only_approval_and_unauthorized_reviewer(self):
        qualification = self.fixture.acquire()
        approval = self.fixture.approval(qualification)
        self.fixture.verify(qualification, approval)
        with self.assertRaisesRegex(ValueError, "unauthorised"):
            self.fixture.verify(qualification, approval, ())
        with self.assertRaisesRegex(ValueError, "unauthorised"):
            self.fixture.verify(qualification, approval, ("someone-else",))

    def test_approval_for_other_manifest_and_stale_binding(self):
        qualification = self.fixture.acquire()
        approval = self.fixture.approval(qualification)
        qualification.write_text(qualification.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            self.fixture.verify(qualification, approval)
        other = self.root / "other.json"
        q = json.loads(qualification.read_text())
        q["another_manifest"] = True
        other.write_text(json.dumps(q))
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            self.fixture.verify(other, approval)
        # Even copying the manifest digest cannot hide an immutable-input
        # binding mismatch in the separately recorded review.
        record = json.loads(approval.read_text())
        record["qualification_sha256"] = p.digest(other)
        record["inputs_sha256"] = "0" * 64
        approval.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            self.fixture.verify(other, approval)

    def test_changed_native_source_and_rehashed_evidence(self):
        qualification = self.fixture.acquire()
        approval = self.fixture.approval(qualification)
        for path in (self.fixture.checkout / "src/p.ads", self.fixture.output / "native/api/a.html"):
            original = path.read_bytes()
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "snapshot mismatch|native inventory"):
                self.fixture.verify(qualification, approval)
            path.write_bytes(original)
        q = json.loads(qualification.read_text())
        (self.fixture.output / "native/api/a.html").write_text("new native")
        q["native"] = p.inventory(self.fixture.output / "native", p.NATIVE_PATTERNS)
        qualification.write_text(json.dumps(q))
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            self.fixture.verify(qualification, approval)

    def test_symlinked_evidence_rejected(self):
        qualification = self.fixture.acquire()
        approval = self.fixture.approval(qualification)
        outside = self.root / "elsewhere.html"
        outside.write_text("native\n")
        page = self.fixture.output / "native/api/a.html"
        page.unlink()
        page.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.fixture.verify(qualification, approval)

    def test_missing_extra_and_changed_non_api_evidence(self):
        qualification = self.fixture.acquire(entries=self.fixture.entries + [("obj/docs/native/style.css", "css")])
        approval = self.fixture.approval(qualification)
        page = self.fixture.output / "native/style.css"
        for operation in ("remove", "change", "extra"):
            with self.subTest(operation=operation):
                page.write_text("css")
                extra = page.parent / "extra.css"
                if operation == "remove":
                    page.unlink()
                elif operation == "change":
                    page.write_text("changed")
                else:
                    extra.write_text("extra")
                with self.assertRaisesRegex(ValueError, "native inventory"):
                    self.fixture.verify(qualification, approval)
                if extra.exists():
                    extra.unlink()

    def test_manifest_removed_on_extraction_failure(self):
        original = Path.open

        def fail(path, *args, **kwargs):
            if path.name == "a.html" and args == ("xb",):
                raise OSError("controlled extraction failure")
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", fail), self.assertRaisesRegex(OSError, "controlled"):
            self.fixture.acquire()
        self.assertFalse(self.fixture.output.exists())


if __name__ == "__main__":
    unittest.main()