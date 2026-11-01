#!/usr/bin/env python3
"""Isolated GNAT 16 ALI identity experiment. No production imports by default.

The operator retains the manifest digest separately from mutable evidence.
Local build receipts are not signed attestations. Only static, explicit calls
to ordinary subprograms are supported. No name/ordinal/anchor-based selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

STATUSES = frozenset({
    "COMPILER_IDENTITY_CONFIRMED", "COMPILER_IDENTITY_MISMATCH",
    "COMPILER_EVIDENCE_MISSING", "COMPILER_EVIDENCE_STALE", "AMBIGUOUS",
    "UNSUPPORTED", "SOURCE_NATIVE_MISMATCH", "ANALYSIS_ERROR"})
SEMANTIC_ENV = ("PATH", "GPR_PROJECT_PATH", "ADA_PROJECT_PATH", "ADA_INCLUDE_PATH",
                "ADA_OBJECTS_PATH", "GPR_CONFIG", "GPR_RUNTIME_PATH", "ADAFLAGS",
                "CFLAGS", "CXXFLAGS", "LIBRARY_TYPE", "GCC_EXEC_PREFIX",
                "COMPILER_PATH", "CPATH", "LIBRARY_PATH")
SUFFIXES = {".ads", ".adb", ".gpr", ".adc", ".cgpr"}


class Rejected(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason
        super().__init__(reason)


def need(condition, status, reason):
    if not condition:
        raise Rejected(status, reason)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root, suffixes=None):
    root = Path(root)
    result = {}
    for p in sorted(root.rglob("*")):
        need(not p.is_symlink(), "UNSUPPORTED", "symlinks in snapshot/build")
        if p.is_file() and (suffixes is None or p.suffix in suffixes):
            result[p.relative_to(root).as_posix()] = digest(p)
    return result


def environment():
    return {k: os.environ.get(k) for k in SEMANTIC_ENV}


def project_configuration(compiler, project, root, scenarios):
    inspector = Path(compiler).resolve().with_name("gprinspect")
    run = command([inspector, "-P", project, "--all", "-r", "--display=json",
                   *["-X" + s for s in scenarios]])
    need(run["exit"] == 0, "ANALYSIS_ERROR", "project inspection failed")
    data = json.loads(run["stdout"])
    # Includes evaluated external variables (even ones absent from our fixed
    # environment list), switches and the recursively loaded project closure.
    for view in data["projects"]:
        p = Path(view["project"]["file-name"]).resolve()
        need(p.is_relative_to(root), "UNSUPPORTED", "external project closure")
    return {"inspector_sha256": digest(inspector), "projects": data["projects"],
            "tree": data.get("tree", {})}


def command(argv):
    tick = time.perf_counter()
    proc = subprocess.run(list(map(str, argv)), capture_output=True, text=True, timeout=120)
    return {"argv": list(map(str, argv)), "exit": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr,
            "seconds": time.perf_counter() - tick}


def tool_identity(compiler):
    compiler = Path(compiler).resolve()
    gcc = Path(subprocess.check_output(["which", "gcc"], text=True).strip()).resolve()
    version = command([gcc, "--version"])
    need("16.1.0" in version["stdout"].splitlines()[0], "UNSUPPORTED", "qualify GNAT 16.1.0 first")
    gnat1 = Path(subprocess.check_output([gcc, "-print-prog-name=gnat1"], text=True).strip()).resolve()
    return {"gprbuild": str(compiler), "gprbuild_sha256": digest(compiler),
            "gprbuild_version": command([compiler, "--version"])["stdout"],
            "gcc": str(gcc), "gcc_sha256": digest(gcc), "gnat1": str(gnat1),
            "gnat1_sha256": digest(gnat1), "compiler_version": version["stdout"]}


def dependencies(ali, root, runtime):
    """D-table names must identify unique snapshot files or qualified runtime."""
    candidates = {}
    for base in (root, runtime):
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in {".ads", ".adb"}:
                candidates.setdefault(p.name, []).append(p.resolve())
    result = {}
    for line in ali.read_text().splitlines():
        if not line.startswith("D "):
            continue
        name = line.split()[1]
        options = list(set(candidates.get(name, [])))
        need(len(options) == 1, "UNSUPPORTED", "nonunique/external dependency: " + name)
        p = options[0]
        result[str(p)] = digest(p)
    return result


def generate(root, project, sources, compiler, build, scenarios=()):
    """Create a new relocated build; never authenticate pre-existing outputs."""
    root, project, build = Path(root).resolve(), Path(project).resolve(), Path(build).resolve()
    need(not build.exists() and not build.is_relative_to(root), "ANALYSIS_ERROR",
         "build must be a fresh directory outside snapshot")
    need(project.is_relative_to(root), "UNSUPPORTED", "project outside snapshot")
    before = inventory(root)
    need(bool(before), "COMPILER_EVIDENCE_MISSING", "empty snapshot")
    for name in before:
        if Path(name).suffix in {".ads", ".adb"}:
            text = (root / name).read_text()
            need(text.isascii() and "\t" not in text and not re.search(
                r"\bpragma\s+Source_Reference\b", text, re.I),
                "UNSUPPORTED", "unqualified columns or source remapping")
    sources = [Path(s).resolve() for s in sources]
    need(all(s.is_relative_to(root) and s.suffix == ".adb" for s in sources),
         "UNSUPPORTED", "only snapshot Ada bodies supported")
    need(len({s.name for s in sources}) == len(sources), "AMBIGUOUS", "duplicate source basename")
    tools = tool_identity(compiler)
    configuration = project_configuration(compiler, project, root, scenarios)
    runtime = Path(subprocess.check_output([tools["gcc"], "-print-file-name=adainclude"], text=True).strip()).resolve()
    build.mkdir(parents=True, mode=0o700)
    runs = []
    for source in sources:
        argv = [compiler, "-v", "-P", project, "--root-dir=" + str(root),
                "--relocate-build-tree=" + str(build), "-p", "-c", "-u", "-f",
                *["-X" + s for s in scenarios], source.name]
        run = command(argv)
        runs.append(run)
        need(run["exit"] == 0, "ANALYSIS_ERROR", "compiler rejected source: " + run["stderr"])
        need(tools["gcc"] in run["stdout"] + run["stderr"],
             "UNSUPPORTED", "build did not report the qualified compiler driver")
    need(before == inventory(root), "COMPILER_EVIDENCE_STALE", "snapshot changed during compile")
    alis = sorted(build.rglob("*.ali"))
    need(bool(alis), "COMPILER_EVIDENCE_MISSING", "compiler produced no ALI")
    deps = {}
    for ali in alis:
        text = ali.read_text()
        need(text.startswith('V "GNAT Lib v16"\n') and "\nX " in text,
             "COMPILER_EVIDENCE_MISSING", "ALI has no qualified xrefs")
        need(not re.search(r"^A .*-(?:gnatx|gnatD|gnatU|gnatep|gnateD)", text, re.M),
             "UNSUPPORTED", "xref suppression/source rewriting option")
        need(ali.with_suffix(".o").is_file(), "COMPILER_EVIDENCE_MISSING", "missing fresh object")
        deps.update(dependencies(ali, root, runtime))
    receipt = {"schema": 1, "root": str(root), "project": str(project),
               "sources": [str(s) for s in sources], "snapshot": before,
               "tools": tools, "environment": environment(), "scenarios": list(scenarios),
               "project_configuration": configuration,
               "build": str(build), "runs": runs, "dependencies": deps,
               "artifacts": inventory(build), "alis": [p.relative_to(build).as_posix() for p in alis]}
    path = build.parent / (build.name + ".receipt.json")
    need(not path.exists(), "ANALYSIS_ERROR", "receipt already exists")
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    return path, digest(path)


ENTITY = re.compile(r"^(\d+)([A-Za-z])(\d+)([ *+])([A-Za-z][A-Za-z0-9_]*)(\S*)(?:\s+(.*))?$")
REFERENCE = re.compile(r"^(?:(\d+)\|)?(\d+)([A-Za-z<>=^])(\d+)(.*)$")


def parse_ali(text):
    """Parse exact coordinates. Unknown grammar fails closed, never skips a row.

    Keys are (dependency filename, line, visible column). Values include ALL
    references at that position, including noncalls and dispatching references.
    """
    need(text.startswith('V "GNAT Lib v16"\n') and text.endswith("\n"),
         "COMPILER_EVIDENCE_MISSING", "truncated/unqualified ALI")
    deps = [line.split()[1] for line in text.splitlines() if line.startswith("D ")]
    need(len(deps) == len(set(deps)), "AMBIGUOUS", "duplicate D filename")
    index, section, current, ref_file = {}, None, None, None

    def filename(number):
        need(0 < number <= len(deps), "COMPILER_EVIDENCE_MISSING", "bad dependency number")
        return deps[number - 1]

    for line in text.splitlines():
        if line.startswith("X "):
            parts = line.split()
            need(len(parts) == 3 and filename(int(parts[1])) == parts[2],
                 "COMPILER_EVIDENCE_MISSING", "invalid X section")
            section, current = int(parts[1]), None
            continue
        if section is None or not line:
            continue
        if line.startswith("."):
            need(current is not None, "COMPILER_EVIDENCE_MISSING", "orphan continuation")
            refs = line[1:].strip()
        else:
            m = ENTITY.fullmatch(line)
            need(m is not None, "UNSUPPORTED", "unrecognized ALI entity grammar: " + line)
            row, typ, col, level, name, metadata, refs = m.groups()
            current = {"file": filename(section), "line": int(row), "column": int(col),
                       "entity_type": typ, "metadata": metadata, "name": name}
            ref_file = section
        for token in (refs or "").split():
            m = REFERENCE.fullmatch(token)
            need(m is not None, "UNSUPPORTED", "unrecognized ALI reference: " + token)
            dep, row, typ, col, suffix = m.groups()
            if dep:
                ref_file = int(dep)
            # Generic instance suffixes change dependency state; do not guess.
            need(not suffix, "UNSUPPORTED", "generic reference suffix")
            key = (filename(ref_file), int(row), int(col))
            index.setdefault(key, []).append(dict(current, reference_type=typ))
    need(section is not None, "COMPILER_EVIDENCE_MISSING", "no X section")
    return index


class Evidence:
    """Validate hashes once, index once, then perform O(1) batch lookups.

    Snapshot/artifacts must remain immutable for the lifetime of this session.
    A new verification session rechecks all bytes. No persistent trusted cache.
    """
    def __init__(self, receipt, expected_sha256, root, project, scenarios=()):
        tick = time.perf_counter()
        receipt, root, project = Path(receipt), Path(root).resolve(), Path(project).resolve()
        need(receipt.is_file(), "COMPILER_EVIDENCE_MISSING", "missing receipt")
        need(digest(receipt) == expected_sha256, "COMPILER_EVIDENCE_STALE", "receipt digest differs from operator pin")
        self.receipt = r = json.loads(receipt.read_text())
        need(r["schema"] == 1 and r["root"] == str(root) and r["project"] == str(project),
             "COMPILER_EVIDENCE_STALE", "snapshot/project identity changed")
        need(r["scenarios"] == list(scenarios) and r["environment"] == environment(),
             "COMPILER_EVIDENCE_STALE", "project environment/scenarios changed")
        need(r["snapshot"] == inventory(root), "COMPILER_EVIDENCE_STALE", "source/configuration changed")
        need(r["tools"] == tool_identity(r["tools"]["gprbuild"]), "COMPILER_EVIDENCE_STALE", "toolchain changed")
        need(r["project_configuration"] == project_configuration(
            r["tools"]["gprbuild"], project, root, scenarios),
            "COMPILER_EVIDENCE_STALE", "evaluated project configuration changed")
        need(bool(r["runs"]) and all(x["exit"] == 0 for x in r["runs"]),
             "ANALYSIS_ERROR", "no successful compilation")
        build = Path(r["build"])
        need(build.is_dir(), "COMPILER_EVIDENCE_MISSING", "missing build directory")
        for name, sha in r["artifacts"].items():
            p = build / name
            need(p.is_file(), "COMPILER_EVIDENCE_MISSING", "missing compiler output: " + name)
            need(digest(p) == sha, "COMPILER_EVIDENCE_STALE", "compiler output modified: " + name)
        need(r["artifacts"] == inventory(build), "COMPILER_EVIDENCE_STALE", "extra compiler outputs")
        for name, sha in r["dependencies"].items():
            need(Path(name).is_file() and digest(name) == sha, "COMPILER_EVIDENCE_STALE", "dependency changed: " + name)
        self.validation_seconds = time.perf_counter() - tick
        tick = time.perf_counter()
        self.index, self.root = {}, root
        self.snapshot = r["snapshot"]
        self.by_name = {}
        for name in self.snapshot:
            self.by_name.setdefault(Path(name).name, []).append(name)
        need(bool(r["alis"]), "COMPILER_EVIDENCE_MISSING", "no ALI inventory")
        for name in r["alis"]:
            need(name in r["artifacts"], "COMPILER_EVIDENCE_MISSING", "ALI not authenticated")
            for key, values in parse_ali((build / name).read_text()).items():
                self.index.setdefault(key, []).extend(values)
        self.index_seconds = time.perf_counter() - tick

    def compare(self, occurrence, selected):
        result = {"status": "ANALYSIS_ERROR", "occurrence": occurrence,
                  "libadalang_selected": selected}
        tick = time.perf_counter()
        try:
            file = occurrence["file"]
            need(file in self.snapshot and str(self.root / file) in self.receipt["sources"],
                 "COMPILER_EVIDENCE_MISSING", "occurrence source was not compiled")
            need(self.by_name.get(Path(file).name) == [file], "AMBIGUOUS", "nonunique occurrence file")
            key = (Path(file).name, occurrence["line"], occurrence["column"])
            matches = self.index.get(key, [])
            need(bool(matches), "COMPILER_EVIDENCE_MISSING", "no exact occurrence reference")
            # Deduplicate identical records across freshly compiled units only.
            unique = {json.dumps(m, sort_keys=True): m for m in matches}
            need(len(unique) == 1, "AMBIGUOUS", "conflicting occurrence references")
            target = next(iter(unique.values()))
            need(target["reference_type"] == "s" and target["entity_type"] in {"V", "U"},
                 "UNSUPPORTED", "not an explicit static subprogram call")
            need(not any(c in target["metadata"] for c in "=[<"),
                 "UNSUPPORTED", "renaming/instance/overriding entity")
            paths = self.by_name.get(target["file"], [])
            need(len(paths) == 1, "UNSUPPORTED", "declaration is external/nonunique")
            identity = {"file": paths[0], "line": target["line"], "column": target["column"],
                        "sha256": self.snapshot[paths[0]]}
            result["compiler_selected"] = identity
            result["compiler_reference"] = target
            need(selected["kind"] in {"SubpDecl", "ExprFunction", "SubpBody"},
                 "UNSUPPORTED", "unsupported Libadalang canonical declaration form")
            need(all(selected[k] == v for k, v in identity.items()),
                 "COMPILER_IDENTITY_MISMATCH", "exact declaration identity differs")
            result["status"] = "COMPILER_IDENTITY_CONFIRMED"
        except Rejected as exc:
            result.update(status=exc.status, reason=exc.reason)
        except (KeyError, TypeError, ValueError) as exc:
            result.update(status="ANALYSIS_ERROR", reason=str(exc))
        result["lookup_seconds"] = time.perf_counter() - tick
        return result


def native_link(result, declaration, spec, root, native, qualification,
                authorization=None, reviewers=()):
    """Only invoke reviewed native reconciliation AFTER unique compiler agreement."""
    if result["status"] != "COMPILER_IDENTITY_CONFIRMED":
        return result
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gnatdoc031"))
        import probe
        probe.verify_qualification(qualification, root, native, authorization, reviewers)
        # The node passed for presentation must be the compared canonical node.
        identity = lal_identity(declaration, root)
        need(identity == result["libadalang_selected"], "SOURCE_NATIVE_MISMATCH", "native node substitution")
        status, details = probe.match_native(declaration, spec, root, native)
        need(status == "RESOLVED_AND_MATCHED", "SOURCE_NATIVE_MISMATCH", details.get("reason", status))
        result.update(native=details, hyperlink=details["hyperlink"])
    except Exception as exc:
        result.update(status="SOURCE_NATIVE_MISMATCH", reason=str(exc))
        result.pop("hyperlink", None)
    return result


def lal_identity(declaration, root):
    spec = declaration.f_subp_spec
    defining = spec.f_subp_name
    pos = defining.sloc_range.start
    p = Path(declaration.unit.filename).resolve()
    return {"file": p.relative_to(root).as_posix(), "line": pos.line, "column": pos.column,
            "sha256": digest(p), "kind": declaration.kind_name}


def lal_select(project, root, occurrence):
    """Optional adapter; the ALI parser has no access to these selections."""
    import libadalang as lal
    need(not any("\t" in p.read_text() or not p.read_text().isascii()
                 for p in root.rglob("*.ad[bs]")), "UNSUPPORTED", "tabs/non-ASCII columns require qualification")
    gpr = lal.GPRProject(str(project), print_errors=False)
    need(not gpr.errors, "ANALYSIS_ERROR", str(gpr.errors))
    context = gpr.create_context()
    unit = context.get_from_file(str(root / occurrence["file"]))
    need(not unit.diagnostics and unit.root is not None, "ANALYSIS_ERROR", "Libadalang parse failure")
    node = unit.root.lookup(lal.Sloc(occurrence["line"], occurrence["column"]))
    need(isinstance(node, lal.Name) and node.sloc_range.start.line == occurrence["line"]
         and node.sloc_range.start.column == occurrence["column"], "UNSUPPORTED", "not an exact Ada name token")
    entry = node
    while entry is not None and not entry.p_xref_entry_point:
        entry = entry.parent
    need(entry is not None and entry.p_resolve_names and not entry.p_nameres_diagnostics,
         "ANALYSIS_ERROR", "Libadalang precise name resolution failed")
    declaration = node.p_referenced_decl(imprecise_fallback=False)
    need(declaration is not None, "ANALYSIS_ERROR", "no Libadalang declaration")
    canonical = declaration.p_canonical_part(imprecise_fallback=False)
    need(canonical.kind_name in {"SubpDecl", "ExprFunction", "SubpBody"},
         "UNSUPPORTED", "instance/renaming/implicit declaration")
    return lal_identity(canonical, root), canonical, node.p_called_subp_spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("generate", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--root", type=Path, required=True)
        p.add_argument("--project", type=Path, required=True)
        p.add_argument("-X", action="append", default=[])
    gen = sub.choices["generate"]
    gen.add_argument("--source", type=Path, action="append", required=True)
    gen.add_argument("--compiler", type=Path, required=True)
    gen.add_argument("--build", type=Path, required=True)
    verify = sub.choices["verify"]
    verify.add_argument("--receipt", type=Path, required=True)
    verify.add_argument("--receipt-sha256", required=True)
    verify.add_argument("--requests", type=Path, required=True,
                        help="JSON list of {occurrence: {file,line,column}, selected: identity}")
    verify.add_argument("--native-site", type=Path)
    verify.add_argument("--qualification", type=Path)
    verify.add_argument("--review-authorization", type=Path)
    verify.add_argument("--authorized-reviewer", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.action == "generate":
            path, sha = generate(args.root, args.project, args.source, args.compiler, args.build, args.X)
            result = {"receipt": str(path), "receipt_sha256": sha}
        else:
            evidence = Evidence(args.receipt, args.receipt_sha256, args.root, args.project, args.X)
            calls = []
            for request in json.loads(args.requests.read_text()):
                call = evidence.compare(request["occurrence"], request["selected"])
                if args.native_site and call["status"] == "COMPILER_IDENTITY_CONFIRMED":
                    try:
                        _, decl, spec = lal_select(args.project.resolve(), args.root.resolve(), request["occurrence"])
                        native_link(call, decl, spec, args.root.resolve(), args.native_site.resolve(),
                                    args.qualification, args.review_authorization, args.authorized_reviewer)
                    except Exception as exc:
                        call.update(status="SOURCE_NATIVE_MISMATCH", reason=str(exc))
                calls.append(call)
            result = {"calls": calls,
                      "validation_seconds": evidence.validation_seconds,
                      "index_seconds": evidence.index_seconds}
    except Rejected as exc:
        result = {"status": exc.status, "reason": exc.reason}
    except Exception as exc:
        result = {"status": "ANALYSIS_ERROR", "reason": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2))
    return 0 if ("receipt" in result or result.get("calls") and all(
        c["status"] == "COMPILER_IDENTITY_CONFIRMED" for c in result["calls"])) else 1


if __name__ == "__main__":
    raise SystemExit(main())