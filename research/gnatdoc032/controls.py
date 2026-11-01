#!/usr/bin/env python3
"""Reproduce real compiler/LAL controls, retained receipts and measured costs.

Run in the private Libadalang runtime. A new --workspace is mandatory.
No review approval is created; native positive controls use an explicitly
TEST-ONLY record removed with the temporary directory, never real authority.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import verifier as v

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "gnatdoc031"
sys.path.insert(0, str(OLD))
import probe
from provenance import verified_inputs
from review_authorization import record_review

CORE_COMMIT = "dbdb410c0d86b640271733d7b999ede5a5f92267"
CORE_TREE = "5bcbe86967fea4f718aab96a348fcaef5e8cfe8a"


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def occurrence(file, line, column):
    return dict(file=file, line=line, column=column)


def run_case(evidence, root, project, call, expected):
    selected, declaration, spec = v.lal_select(project, root, call)
    check((selected["file"], selected["line"], selected["column"]) == expected,
          "independent expected location differs: " + str(selected))
    result = evidence.compare(call, selected)
    check(result["status"] == "COMPILER_IDENTITY_CONFIRMED", str(result))
    result["profile"] = declaration.text
    result["independent_expected"] = dict(file=expected[0], line=expected[1], column=expected[2])
    return result, declaration, spec


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--compiler", type=Path, required=True)
    p.add_argument("--core-checkout", type=Path, required=True)
    p.add_argument("--core-config", type=Path, required=True)
    p.add_argument("--native-site", type=Path, required=True)
    p.add_argument("--qualification", type=Path, required=True)
    args = p.parse_args()
    work = args.workspace.resolve()
    check(not work.exists(), "workspace must be new")
    work.mkdir(mode=0o700, parents=True)
    fixtures = work / "fixtures"
    shutil.copytree(OLD / "fixtures", fixtures)
    shutil.copy2(HERE / "fixtures/dispatch.adb", fixtures / "dispatch.adb")
    report = {"schema": 1, "disposition": "PROTOTYPE_LIMITATION",
              "delivery_status": "HOSTED_CI_PENDING", "positive": [], "negative": [],
              "unsupported": [], "measurements": {}, "skipped": [],
              "trust": "local operator-pinned build receipts; not signed attestations; no review granted"}
    compiler = args.compiler.resolve()
    project = fixtures / "fixtures.gpr"
    receipt, sha = v.generate(fixtures, project, [fixtures / "valid.adb", fixtures / "dispatch.adb"],
                             compiler, work / "fixture-build")
    ev = v.Evidence(receipt, sha, fixtures, project)
    report["fixture_receipt"] = dict(path=str(receipt), sha256=sha)
    # Independently fixed defining-name positions from authenticated 031 fixture.
    cases = [(6, 18, "overloads.ads", 4, 13), (7, 19, "overloads.ads", 5, 13),
             (8, 19, "overloads.ads", 6, 13), (9, 19, "overloads.ads", 7, 13),
             (10, 19, "overloads.ads", 8, 13), (11, 19, "overloads.ads", 9, 13),
             (12, 19, "overloads.ads", 10, 13), (13, 19, "overloads.ads", 11, 13),
             (14, 19, "overloads.ads", 12, 13), (15, 19, "overloads.ads", 14, 13),
             (16, 18, "overloads.ads", 15, 13), (17, 29, "overloads.ads", 6, 13),
             (18, 19, "other.ads", 2, 13), (25, 29, "valid.adb", 24, 16)]
    for line, col, file, row, dc in cases:
        result, _, _ = run_case(ev, fixtures, project, occurrence("valid.adb", line, col), (file, row, dc))
        report["positive"].append(result)
    # Critical adversarial control: same valid compiled source, same authentic
    # evidence, plausible but deliberately wrong LAL overload in same file.
    good = report["positive"][2]
    wrong = copy.deepcopy(good["libadalang_selected"])
    wrong["line"] = 7
    mismatch = ev.compare(good["occurrence"], wrong)
    check(mismatch["status"] == "COMPILER_IDENTITY_MISMATCH" and "hyperlink" not in mismatch, str(mismatch))
    mismatch["control"] = "wrong-LAL-overload-with-valid-compiler-evidence"
    report["negative"].append(mismatch)
    for call in [occurrence("valid.adb", 20, 19), occurrence("valid.adb", 21, 19),
                 occurrence("dispatch.adb", 10, 27)]:
        # For unsupported forms, a supplied identity cannot make them supported.
        observed = ev.compare(call, wrong)
        check(observed["status"] == "UNSUPPORTED", str(observed))
        observed["adapter_observation"] = None
        try:
            observed["adapter_observation"] = v.lal_select(project, fixtures, call)[0]
        except Exception as exc:
            observed["adapter_observation"] = str(exc)
        report["unsupported"].append(observed)
    missing = ev.compare(occurrence("valid.adb", 8, 20), wrong)
    check(missing["status"] == "COMPILER_EVIDENCE_MISSING", str(missing))
    report["negative"].append(dict(missing, control="adjacent-not-exact-column"))
    # Preserve all 031 invalid/ambiguous compiler negatives and raw LAL findings.
    report["predecessor_negatives"] = []
    for name in ("invalid.adb", "ambiguous.adb", "default_ambiguous.adb"):
        run = v.command([compiler, "-P", project, "--root-dir=" + str(fixtures),
                         "--relocate-build-tree=" + str(work / (name + ".build")), "-p", "-c", "-u", name])
        check(run["exit"] != 0, "031 negative unexpectedly compiled: " + name)
        raw = probe.analyze(project, [fixtures / name], fixtures)
        check(not any("hyperlink" in c for c in raw["calls"]), "031 negative linked")
        report["predecessor_negatives"].append(dict(source=name, compiler=run, raw_libadalang=raw))

    def rejected(label, expected, receipt_path=receipt, pin=sha, scenarios=()):
        try:
            v.Evidence(receipt_path, pin, fixtures, project, scenarios)
        except v.Rejected as exc:
            check(exc.status == expected, f"{label}: {exc.status}: {exc}")
            report["negative"].append(dict(control=label, status=exc.status, reason=exc.reason))
        else:
            raise RuntimeError("accepted bad evidence: " + label)

    ali = next((work / "fixture-build").rglob("valid.ali"))
    original = ali.read_bytes()
    ali.unlink()
    rejected("missing-ALI", "COMPILER_EVIDENCE_MISSING")
    ali.write_bytes(original[:len(original) // 2])
    rejected("truncated-ALI", "COMPILER_EVIDENCE_STALE")
    ali.write_bytes(original.replace(b"8s19", b"9s19"))
    rejected("tampered-ALI", "COMPILER_EVIDENCE_STALE")
    ali.write_bytes(original)
    extra = ali.with_name("conflicting.ali")
    extra.write_bytes(original.replace(b"8s19", b"9s19"))
    rejected("extra-conflicting-ALI", "COMPILER_EVIDENCE_STALE")
    extra.unlink()
    source = fixtures / "valid.adb"
    text = source.read_bytes()
    source.write_bytes(text + b"\n-- stale snapshot\n")
    rejected("source-change", "COMPILER_EVIDENCE_STALE")
    source.write_bytes(text)
    extra_input = fixtures / "preprocessor-input.txt"
    extra_input.write_text("untracked configuration input\n")
    rejected("added-non-Ada-snapshot-input", "COMPILER_EVIDENCE_STALE")
    extra_input.unlink()
    text = project.read_bytes()
    project.write_bytes(text + b"\n-- project change\n")
    rejected("project-change", "COMPILER_EVIDENCE_STALE")
    project.write_bytes(text)
    rejected("scenario-change", "COMPILER_EVIDENCE_STALE", scenarios=("MODE=other",))
    with tempfile.TemporaryDirectory() as tmp:
        changed = Path(tmp) / "receipt.json"
        altered = json.loads(receipt.read_text())
        altered["runs"][0]["exit"] = 1
        save(changed, altered)
        rejected("receipt-rewrite-with-original-pin", "COMPILER_EVIDENCE_STALE", changed)
    # Conflict parser test with a syntactically valid second declaration row.
    idx = v.parse_ali(original.decode().replace("7V13*Pick{integer} 27|9s19",
                                              "7V13*Pick{integer} 27|8s19"))
    check(len(idx[("valid.adb", 8, 19)]) == 2, "conflict not indexed")
    previous = ev.index
    ev.index = idx
    conflict = ev.compare(good["occurrence"], good["libadalang_selected"])
    check(conflict["status"] == "AMBIGUOUS", str(conflict))
    report["negative"].append(dict(conflict, control="syntactically-valid-conflicting-records-parser-boundary"))
    ev.index = previous
    # Project evaluation also catches external variables not on a fixed list.
    text = project.read_text()
    project.write_text(text.replace("project Fixtures is", 'project Fixtures is\n   Mode := external ("GNATDOC032_MODE", "a");'))
    external_receipt, external_sha = v.generate(fixtures, project, [source], compiler, work / "external-build")
    old_mode = os.environ.get("GNATDOC032_MODE")
    try:
        os.environ["GNATDOC032_MODE"] = "b"
        rejected("arbitrary-project-external-change", "COMPILER_EVIDENCE_STALE", external_receipt, external_sha)
    finally:
        if old_mode is None:
            os.environ.pop("GNATDOC032_MODE", None)
        else:
            os.environ["GNATDOC032_MODE"] = old_mode
        project.write_text(text)

    # A legal compile with suppressed xrefs is not usable identity evidence.
    text = project.read_text()
    project.write_text(text.replace('"-gnat2022", "-gnata"', '"-gnat2022", "-gnata", "-gnatx"'))
    try:
        v.generate(fixtures, project, [source], compiler, work / "suppressed-build")
    except v.Rejected as exc:
        check(exc.status == "COMPILER_EVIDENCE_MISSING", str(exc))
        report["negative"].append(dict(control="successful-compile-xrefs-suppressed",
                                       status=exc.status, reason=exc.reason))
    else:
        raise RuntimeError("accepted suppressed compiler xrefs")
    finally:
        project.write_text(text)

    core = work / "core"
    checkout = args.core_checkout.resolve()
    check(subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip() == CORE_COMMIT, "Core commit differs")
    check(subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD^{tree}"], text=True).strip() == CORE_TREE, "Core tree differs")
    check(not subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain", "--ignored"], text=True).strip(), "Core checkout is dirty")
    core.mkdir()
    archive = subprocess.check_output(["git", "-C", str(checkout), "archive", CORE_COMMIT])
    subprocess.run(["tar", "-x", "-C", str(core)], input=archive, check=True)
    shutil.copytree(args.core_config, core / "config", dirs_exist_ok=True)
    tracked = subprocess.check_output(["git", "-C", str(checkout), "ls-files", "-z"]).decode().split("\0")
    hashes = {f: v.digest(checkout / f) for f in tracked if f}
    check(all(v.digest(core / f) == sha for f, sha in hashes.items()), "Core export differs")
    q = verified_inputs(args.qualification, core, args.native_site)
    report["core_provenance"] = dict(commit=CORE_COMMIT, tree=CORE_TREE, tracked=hashes,
                                     qualification_sha256=v.digest(args.qualification), provenance=q["provenance"])
    core_project = core / "docs/example.gpr"
    cr, cs = v.generate(core, core_project, [core / "docs/example.adb"], compiler, work / "core-build")
    ce = v.Evidence(cr, cs, core, core_project)
    report["core_receipt"] = dict(path=str(cr), sha256=cs)
    report["native_controls"] = []
    with tempfile.TemporaryDirectory() as tmp:
        approval = Path(tmp) / "TEST-ONLY.json"
        record_review(args.qualification, core, args.native_site, approval, "TEST-ONLY-reviewer",
                      "Ephemeral contract simulation, NOT independent review or approval")
        for line, col, decl in [(5, 28, 1130), (6, 34, 1242)]:
            result, node, spec = run_case(ce, core, core_project, occurrence("docs/example.adb", line, col),
                                          ("src/opencv-core.ads", decl, 13))
            report["positive"].append(copy.deepcopy(result))
            unapproved = v.native_link(copy.deepcopy(result), node, spec, core, args.native_site, args.qualification)
            check(unapproved["status"] == "SOURCE_NATIVE_MISMATCH" and "hyperlink" not in unapproved, str(unapproved))
            report["native_controls"].append(dict(unapproved, control="acquired-but-unreviewed"))
            linked = v.native_link(copy.deepcopy(result), node, spec, core, args.native_site,
                                   args.qualification, approval, ("TEST-ONLY-reviewer",))
            check(linked["status"] == "COMPILER_IDENTITY_CONFIRMED" and "hyperlink" in linked, str(linked))
            linked["authorization_scope"] = "TEST-ONLY ephemeral simulation; NOT independent review"
            report["native_controls"].append(linked)
            if line == 6:
                wrong_core = copy.deepcopy(result["libadalang_selected"])
                wrong_core["line"] = 512  # Real, wrong UMat Clone declaration.
                bad = ce.compare(result["occurrence"], wrong_core)
                v.native_link(bad, node, spec, core, args.native_site, args.qualification, approval, ("TEST-ONLY-reviewer",))
                check(bad["status"] == "COMPILER_IDENTITY_MISMATCH" and "hyperlink" not in bad, str(bad))
                report["negative"].append(dict(bad, control="wrong-Core-UMat-Clone-valid-evidence"))
                changed = Path(tmp) / "native"
                shutil.copytree(args.native_site, changed)
                page = changed / linked["hyperlink"].split("#")[0]
                page.write_text(page.read_text().replace("function Clone (Self : Mat) return Mat",
                                                        "function Clone (Self : UMat) return UMat"))
                bad_native = v.native_link(copy.deepcopy(result), node, spec, core, changed,
                                          args.qualification, approval, ("TEST-ONLY-reviewer",))
                check(bad_native["status"] == "SOURCE_NATIVE_MISMATCH" and "hyperlink" not in bad_native, str(bad_native))
                report["native_controls"].append(dict(bad_native, control="native-profile-tamper"))
    # Reuse one index across many occurrences. Compare clean versus no-change
    # incremental compilation; never issue a fresh trust receipt for old outputs.
    for name, evidence, rec in [("fixtures", ev, receipt), ("core", ce, cr)]:
        r = json.loads(rec.read_text())
        argv = r["runs"][0]["argv"]
        # Never mutate the authenticated build while measuring. Seed a separate
        # disposable tree, warm it after adversarial source mtime changes, then
        # measure a truly no-change second invocation.
        measured_build = work / (name + "-incremental")
        shutil.copytree(r["build"], measured_build)
        incremental_argv = ["--relocate-build-tree=" + str(measured_build)
                            if s.startswith("--relocate-build-tree=") else s
                            for s in argv if s != "-f"]
        warmup = v.command(incremental_argv)
        check(warmup["exit"] == 0, "incremental warmup failed")
        incremental = v.command(incremental_argv)
        check(incremental["exit"] == 0, "incremental failed")
        target = report["positive"][0 if name == "fixtures" else -1]
        lookup = []
        for _ in range(10000):
            result = evidence.compare(target["occurrence"], target["libadalang_selected"])
            check(result["status"] == "COMPILER_IDENTITY_CONFIRMED", str(result))
            lookup.append(result["lookup_seconds"])
        report["measurements"][name] = dict(
            clean_compile_seconds=sum(x["seconds"] for x in r["runs"]),
            incremental=incremental, incremental_warmup=warmup, validation_seconds=evidence.validation_seconds,
            parse_index_seconds=evidence.index_seconds,
            lookup_median_seconds=statistics.median(lookup), lookup_max_seconds=max(lookup),
            lookups=10000, artifact_bytes=sum((Path(r["build"]) / f).stat().st_size for f in r["artifacts"]),
            ali_sha256={f: r["artifacts"][f] for f in r["alis"]})
        # A fresh lightweight monitor avoids counting the LAL parent's high
        # inherited RSS as compiler usage. Linux ru_maxrss units are KiB.
        isolated_argv = ["--relocate-build-tree=" + str(work / (name + "-memory"))
                         if s.startswith("--relocate-build-tree=") else s for s in argv]
        monitor = '''import json,resource,subprocess,sys,time
t=time.perf_counter()
p=subprocess.run(json.loads(sys.argv[1]),capture_output=True,text=True)
print(json.dumps(dict(exit=p.returncode,seconds=time.perf_counter()-t,
peak_children_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
stdout=p.stdout,stderr=p.stderr)))
'''
        measured = subprocess.check_output([sys.executable, "-c", monitor, json.dumps(isolated_argv)], text=True)
        report["measurements"][name]["isolated_compiler"] = json.loads(measured)
        check(report["measurements"][name]["isolated_compiler"]["exit"] == 0, "memory run failed")
        # Prove that the exercised original receipt still verifies at delivery.
        v.Evidence(rec, v.digest(rec), Path(r["root"]), Path(r["project"]))
    report["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["children_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    report["disposition"] = "PROTOTYPE_SUCCESS"
    report["decision"] = "Separate compiler-verified mapping generator; narrow static-call support, optional private analysis dependencies"
    check(all(c["status"] in v.STATUSES and ("hyperlink" not in c or c["status"] == "COMPILER_IDENTITY_CONFIRMED")
              for group in ("positive", "negative", "native_controls", "unsupported") for c in report[group]), "invalid result authority")
    save(work / "results.json", report)
    print(json.dumps({"results": str(work / "results.json"), "disposition": report["disposition"],
                      "positive": len(report["positive"]), "negative": len(report["negative"]),
                      "unsupported": len(report["unsupported"]), "measurements": report["measurements"]}, indent=2))


if __name__ == "__main__":
    main()