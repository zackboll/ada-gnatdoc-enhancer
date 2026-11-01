"""Offline fail-closed tests plus opt-in REAL Python/native semantic controls."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH))
import probe
from test_security import EvidenceFixture
from review_authorization import record_review
from provenance import NATIVE_PATTERNS


class QualificationTests(unittest.TestCase):
    def test_missing_and_modified_inventories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = EvidenceFixture(root)
            path = fixture.acquire()
            approval = fixture.approval(path)
            fixture.verify(path, approval)
            (fixture.output / "native/api/a.html").write_text("wrong anchor\n")
            with self.assertRaisesRegex(ValueError, "native inventory"):
                fixture.verify(path, approval)
            (fixture.output / "native/api/a.html").write_text("native\n")
            (fixture.checkout / "src/p.ads").write_text("package Unrelated is end Unrelated;\n")
            with self.assertRaisesRegex(ValueError, "snapshot mismatch"):
                fixture.verify(path, approval)

    def test_unreviewed_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "q.json"
            path.write_text('{"schema": 1, "reviewed": false}')
            with self.assertRaisesRegex(ValueError, "not explicitly verified"):
                probe.verify_qualification(path, path.parent, path.parent)


@unittest.skipUnless(importlib.util.find_spec("libadalang"), "private Libadalang environment required")
class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixtures = self.root / "fixtures"
        shutil.copytree(RESEARCH / "fixtures", self.fixtures)

    def analyze(self, source, expressions, project="fixtures.gpr"):
        return probe.analyze(self.fixtures / project, [self.fixtures / source],
                             self.fixtures, expressions=expressions, compiler=shutil.which("gprbuild"))

    def test_exact_overloads(self):
        # Expected declarations are fixed independent source lines, NOT output
        # copied from the resolver or first-candidate expectations.
        expected = {
            "M.Clone": (4, "Overloads.Mat"), "U.Clone": (5, "Overloads.UMat"),
            "Pick (1)": (6, "Standard.Integer"), "Pick (\"two\")": (7, "Standard.Integer"),
            "Count (1)": (8, "Standard.Integer"), "Count (1, 2)": (9, "Standard.Integer"),
            'Named (Right => "x", Left => 1)': (10, "Standard.Integer"),
            'Named (Right => 1, Left => "x")': (11, "Standard.Integer"),
            "Defaulted (1)": (12, "Standard.Integer"),
            "Overloads.Pick (3)": (6, "Standard.Integer"),
            "Renamed (5)": (19, "Standard.Integer"),
        }
        report = self.analyze("valid.adb", list(expected))
        self.assertFalse(report["project_diagnostics"])
        self.assertFalse(report["missing_units"])
        self.assertEqual(len(report["calls"]), len(expected), report)
        for call in report["calls"]:
            text = call["expression"]["text"]
            line, typ = expected[text]
            self.assertTrue(call.get("semantic_resolved"), call)
            self.assertEqual(Path(call["selected_declaration"]["file"]).name, "overloads.ads")
            self.assertEqual(call["selected_declaration"]["span"]["start"][0], line, call)
            self.assertEqual(call["expression_type"].lower(), typ.lower())
            self.assertNotIn("hyperlink", call)

    def test_return_context_visibility_shadowing_generics(self):
        report = self.analyze("valid.adb", ["Result", "Pick (True)", "Pick (7)", "Int_Identity (4)"])
        calls = report["calls"]
        results = [c for c in calls if c["expression"]["text"] == "Result"]
        self.assertEqual({c["selected_declaration"]["span"]["start"][0] for c in results}, {14, 15})
        for call in calls:
            self.assertTrue(call.get("semantic_resolved"), call)
            self.assertNotIn("hyperlink", call)
        by_text = {c["expression"]["text"]: c for c in calls}
        self.assertEqual(Path(by_text["Pick (True)"]["selected_declaration"]["file"]).name, "other.ads")
        self.assertEqual(Path(by_text["Pick (7)"]["selected_declaration"]["file"]).name, "valid.adb")
        self.assertEqual(by_text["Int_Identity (4)"]["called_profile"], "function Identity (Value : Item) return Item")

    def test_invalid_ambiguous_and_missing_context_never_link(self):
        for source, expression in [("invalid.adb", "Pick (False)"), ("ambiguous.adb", "Pick (1)"),
                                   ("default_ambiguous.adb", "Select_Value (1)")]:
            report = self.analyze(source, [expression])
            self.assertTrue(report["calls"])
            for call in report["calls"]:
                self.assertNotEqual(call["status"], "RESOLVED_AND_MATCHED", call)
                self.assertNotIn("hyperlink", call)
                self.assertFalse(call.get("semantic_resolved"), call)
        report = self.analyze("valid.adb", ["M.Clone"], "missing.gpr")
        self.assertEqual(report["status"], "MISSING_CONTEXT", report)
        self.assertFalse(report["calls"])


@unittest.skipUnless(os.environ.get("GNATDOC031_CORE"), "explicit qualified Core environment required")
class CoreTests(unittest.TestCase):
    def setUp(self):
        # Ephemeral TEST-ONLY record exercises the authorization contract. This
        # is NOT an approval of PR #26 or a claim of independent human review.
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.approval = Path(self.temp.name) / "test-only-approval.json"
        record_review(Path(os.environ["GNATDOC031_QUALIFICATION"]),
                      Path(os.environ["GNATDOC031_CORE"]), Path(os.environ["GNATDOC031_NATIVE"]),
                      self.approval, "TEST-ONLY-reviewer", "Positive contract fixture, not independent review")
        self.review = {"authorization": self.approval, "authorized_reviewers": ("TEST-ONLY-reviewer",)}

    def test_no_compiler_cannot_authorize_link(self):
        root = Path(os.environ["GNATDOC031_CORE"])
        unapproved = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                                  Path(os.environ["GNATDOC031_NATIVE"]),
                                  Path(os.environ["GNATDOC031_QUALIFICATION"]), ["Image.Clone"],
                                  compiler=shutil.which("gprbuild"))
        self.assertEqual(unapproved["calls"][0]["status"], "SOURCE_NATIVE_MISMATCH")
        self.assertIn("missing explicit review", unapproved["calls"][0]["reason"])
        self.assertNotIn("hyperlink", unapproved["calls"][0])
        if os.environ.get("GNATDOC031_CONTROL_OUTPUT"):
            (Path(os.environ["GNATDOC031_CONTROL_OUTPUT"]) / "acquired-unapproved-core.json").write_text(
                json.dumps(unapproved, indent=2) + "\n")
        report = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                               Path(os.environ["GNATDOC031_NATIVE"]),
                               Path(os.environ["GNATDOC031_QUALIFICATION"]), ["Image.Clone"], **self.review)
        self.assertEqual(report["calls"][0]["status"], "MISSING_CONTEXT")
        self.assertNotIn("hyperlink", report["calls"][0])

    def test_core_and_tampered_native(self):
        root = Path(os.environ["GNATDOC031_CORE"])
        native = Path(os.environ["GNATDOC031_NATIVE"])
        qualification = Path(os.environ["GNATDOC031_QUALIFICATION"])
        expressions = ["Create (2, 3, (Depth => UInt8, Channels => 1))", "Image.Clone"]
        report = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                               native, qualification, expressions, compiler=shutil.which("gprbuild"), **self.review)
        self.assertEqual(len(report["calls"]), 2)
        for call, expected in zip(report["calls"], ["Create", "Clone"]):
            self.assertEqual(call["status"], "RESOLVED_AND_MATCHED", call)
            self.assertEqual(call["competing_declarations"], 0)
            self.assertIn(expected.lower(), call["called_profile"].lower())
            self.assertEqual(call["expression_type"].lower(), "opencv.core.mat")
        self.assertIn("Self : Mat", report["calls"][1]["called_profile"])
        self.assertNotIn("UMat", report["calls"][1]["called_profile"])
        if os.environ.get("GNATDOC031_CONTROL_OUTPUT"):
            report["authorization_scope"] = "Ephemeral TEST-ONLY record; NOT independent review approval"
            (Path(os.environ["GNATDOC031_CONTROL_OUTPUT"]) / "test-only-approved-core.json").write_text(
                json.dumps(report, indent=2) + "\n")
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "native"
            shutil.copytree(native, changed)
            link = report["calls"][1]["hyperlink"]
            filename, anchor = link.split("#")
            page = changed / filename
            page.write_text(page.read_text().replace(anchor, "0" * 64))
            rejected = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                                     changed, qualification, expressions, compiler=shutil.which("gprbuild"), **self.review)
            for call in rejected["calls"]:
                self.assertEqual(call["status"], "SOURCE_NATIVE_MISMATCH", call)
                self.assertNotIn("hyperlink", call)
            # Rehashing modified evidence cannot reuse the old approval.
            page.write_text(page.read_text().replace("function Clone (Self : Mat) return Mat",
                                                    "function Clone (Self : UMat) return UMat"))
            q = json.loads(qualification.read_text())
            q["native"] = probe.inventory(changed, NATIVE_PATTERNS)
            rebound = Path(directory) / "rebound.json"
            rebound.write_text(json.dumps(q))
            rejected = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                                     changed, rebound, ["Image.Clone"], compiler=shutil.which("gprbuild"), **self.review)
            call = rejected["calls"][0]
            self.assertEqual(call["status"], "SOURCE_NATIVE_MISMATCH", call)
            self.assertNotIn("hyperlink", call)
            self.assertIn("stale or mismatched", call["reason"])
            # Separately exercise reconciliation with a NEW ephemeral test-only
            # record: even fresh fixture approval cannot authorize a bad profile.
            test_approval = Path(directory) / "test-only-rebound-approval.json"
            record_review(rebound, root, changed, test_approval, "TEST-ONLY-reviewer",
                          "Adversarial profile fixture, not independent review")
            rejected = probe.analyze(root / "docs/example.gpr", [root / "docs/example.adb"], root,
                                     changed, rebound, ["Image.Clone"], compiler=shutil.which("gprbuild"),
                                     authorization=test_approval, authorized_reviewers=("TEST-ONLY-reviewer",))
            self.assertEqual(rejected["calls"][0]["status"], "SOURCE_NATIVE_MISMATCH")
            self.assertNotIn("hyperlink", rejected["calls"][0])


if __name__ == "__main__":
    unittest.main()