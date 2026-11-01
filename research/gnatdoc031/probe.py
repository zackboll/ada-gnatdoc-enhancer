#!/usr/bin/env python3
"""Research-only, precise Libadalang probe; never imported by the enhancer.

No unresolved or unqualified result is permitted to carry a hyperlink.
Native qualification is an explicit reviewed, hash-bound input, not a URL map.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

STATUSES = frozenset({"RESOLVED_AND_MATCHED", "SEMANTICALLY_UNRESOLVED",
                      "AMBIGUOUS", "SOURCE_NATIVE_MISMATCH", "MISSING_CONTEXT",
                      "ANALYSIS_ERROR"})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root, patterns):
    return {p.relative_to(root).as_posix(): digest(p)
            for pattern in patterns for p in sorted(root.glob(pattern)) if p.is_file()}


def verify_qualification(qualification, source_root, native):
    """Verify complete inventories, including extra/missing source/native files."""
    q = json.loads(Path(qualification).read_text())
    if q.get("schema") != 1 or not q.get("reviewed") or not q.get("provenance"):
        raise ValueError("native acquisition is not explicitly qualified")
    if inventory(source_root, ["src/**/*.ads", "src/**/*.adb"]) != q["sources"]:
        raise ValueError("source/native snapshot mismatch")
    if inventory(native, ["api/*"]) != q["native"]:
        raise ValueError("native inventory mismatch")
    return q


def location(node):
    span = node.sloc_range
    return {"file": str(Path(node.unit.filename).resolve()),
            "span": {"start": [span.start.line, span.start.column],
                     "end": [span.end.line, span.end.column]},
            "kind": node.kind_name, "text": node.text,
            "sha256": digest(node.unit.filename)}


def match_native(declaration, spec, source_root, native):
    # Read-only reuse of established lexical PRESENTATION equivalences. They
    # never select an overload: selection has already happened in Libadalang.
    from ada_gnatdoc_enhancer.inventory import _one, direct_callables, normalized
    from ada_gnatdoc_enhancer.native_html import HEADING, SECTION
    from ada_gnatdoc_enhancer.profiles import reconcile

    path = Path(declaration.unit.filename).resolve()
    try:
        path.relative_to(source_root / "src")
    except ValueError:
        return "MISSING_CONTEXT", {"reason": "not an owned public source declaration"}
    if path.suffix != ".ads" or declaration.kind_name != "SubpDecl":
        return "MISSING_CONTEXT", {"reason": "generic/renaming/body mapping is not supported"}
    package = _one(path)
    if package is None:
        return "MISSING_CONTEXT", {"reason": "private or unsupported package"}
    # The selected declaration must itself be present in the public source
    # inventory with its COMPLETE profile. No name-only or ordinal selection.
    owned = [d for d in package.declarations
             if normalized(d.signature) == normalized(declaration.text)]
    if len(owned) != 1:
        return "MISSING_CONTEXT", {"reason": "no unique canonical public declaration"}
    parent = declaration.p_semantic_parent
    if parent is None or parent.kind_name != "PackageDecl":
        return "MISSING_CONTEXT", {"reason": "local/nested declaration"}
    if parent.p_fully_qualified_name.lower() != package.name.lower():
        return "MISSING_CONTEXT", {"reason": "semantic/public owner mismatch"}
    pages = []
    for page in sorted((native / "api").glob("*.html")):
        text = page.read_text()
        headings = HEADING.findall(text)
        if len(headings) == 1 and html.unescape(headings[0]).lower() == package.name.lower():
            pages.append((page, text))
    if len(pages) != 1:
        return "SOURCE_NATIVE_MISMATCH", {"reason": "no unique observed owning package page"}
    page, text = pages[0]
    sections = [(m[1] or m[2], html.unescape(m[3]), html.unescape(m[4]))
                for m in SECTION.finditer(text)]
    callables = direct_callables(package)
    found = [s for s in sections if reconcile(owned[0].signature, s[2], callables)]
    if len(found) != 1:
        return ("AMBIGUOUS" if len(found) > 1 else "SOURCE_NATIVE_MISMATCH"), {
            "reason": "complete profile lacks unique observed native section", "matches": len(found)}
    anchor, name, code = found[0]
    if sum(s[0] == anchor for s in sections) != 1:
        return "AMBIGUOUS", {"reason": "duplicate native anchor"}
    competitors = [d for d in package.declarations
                   if reconcile(d.signature, code, callables)]
    if len(competitors) != 1:
        return "AMBIGUOUS", {"reason": "competing public declaration"}
    return "RESOLVED_AND_MATCHED", {
        "package": package.name, "profile": owned[0].signature,
        "native_profile": code, "native_sha256": digest(page),
        "competing_declarations": len(competitors) - 1,
        "hyperlink": page.relative_to(native).as_posix() + "#" + anchor}


class Events:
    def __init__(self):
        self.missing = []
        self.parsing = []

    def unit_requested_callback(self, context, name, from_unit, found, is_not_found_error):
        if not found and is_not_found_error:
            self.missing.append({"unit": name, "from": from_unit.filename if from_unit else None})

    def unit_parsed_callback(self, context, unit, reparsed):
        self.parsing.extend({"file": unit.filename, "diagnostic": str(d)} for d in unit.diagnostics)


def compiler_check(project, source, source_root, compiler):
    """Force compile the unchanged unit, relocating ALL outputs privately.

    Libadalang 26 precise properties demonstrably select a declaration for
    compiler-ambiguous calls. Compiler acceptance is therefore mandatory for
    authority, not an optional corroboration. No bind/link/run is needed here.
    """
    with tempfile.TemporaryDirectory(prefix="gnatdoc031-compiler-") as directory:
        root = Path(os.path.commonpath([source_root, project.parent, source.parent]))
        argv = [str(compiler), "-P", str(project), "--root-dir=" + str(root),
                "--relocate-build-tree=" + directory, "-p", "-c", "-u", "-f", source.name]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        return {"argv": argv, "exit": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}


def analyze(project, sources, source_root, native=None, qualification=None, expressions=(), compiler=None):
    start = time.perf_counter()
    import libadalang as lal
    imported = time.perf_counter()
    events = Events()
    report = {"schema": 1, "project": str(project), "project_sha256": digest(project),
              "project_configuration": inventory(source_root, ["**/*.gpr", "**/*.adc"]),
              "python": sys.version, "libadalang_module": lal.__file__,
              "environment": {k: os.environ.get(k) for k in
                              ("PATH", "LD_LIBRARY_PATH", "GPR_PROJECT_PATH", "PYTHONPATH")},
              "project_diagnostics": [], "calls": [], "timings_seconds": {"import": imported - start}}
    qualification_error = None
    if native is not None:
        try:
            q = verify_qualification(qualification, source_root, native)
            report["qualification_sha256"] = digest(qualification)
            report["provenance"] = q["provenance"]
        except Exception as exc:
            qualification_error = str(exc)
    loaded = time.perf_counter()
    try:
        gpr = lal.GPRProject(str(project), print_errors=False)
        report["project_diagnostics"] = gpr.errors
        context = gpr.create_context(event_handler=events)
    except Exception as exc:
        report.update(status="MISSING_CONTEXT", error=f"{type(exc).__name__}: {exc}")
        return report
    report["timings_seconds"]["project_load_and_context"] = time.perf_counter() - loaded
    project_sources = {str(Path(p).resolve()) for p in gpr.source_files() if Path(p).is_file()}
    report["project_sources"] = {p: digest(p) for p in sorted(project_sources)}
    report["units"] = []
    for source in sources:
        parsed = time.perf_counter()
        unit = context.get_from_file(str(source))
        report["timings_seconds"].setdefault("parse", {})[str(source)] = time.perf_counter() - parsed
        diagnostics = [str(d) for d in unit.diagnostics]
        unit_record = {"source": str(source), "parse_diagnostics": diagnostics,
                       "semantic_diagnostics": [], "in_project": str(source) in project_sources}
        report["units"].append(unit_record)
        if compiler:
            tick = time.perf_counter()
            unit_record["compiler"] = compiler_check(project, source, source_root, compiler)
            unit_record["compiler_seconds"] = time.perf_counter() - tick
        if unit.root is None:
            report["calls"].append({"source": str(source), "status": "ANALYSIS_ERROR",
                                    "parse_diagnostics": diagnostics})
            continue
        # Resolve all actual semantic entry points, including declarations with
        # no call. A successful selected call cannot qualify a broken unit.
        semantic_start = time.perf_counter()
        unit_record["resolved"] = not diagnostics and unit_record["in_project"]
        for entry in unit.root.findall(lambda n: n.p_xref_entry_point):
            try:
                if not entry.p_resolve_names:
                    unit_record["resolved"] = False
                    unit_record["semantic_diagnostics"].extend(str(d) for d in entry.p_nameres_diagnostics)
            except lal.PropertyError as exc:
                unit_record["resolved"] = False
                unit_record["semantic_diagnostics"].append(str(exc))
        unit_record["semantic_preflight_seconds"] = time.perf_counter() - semantic_start
        # Name covers both CallExpr and the parameterless prefixed DottedName.
        # Exact-text requests avoid choosing an arbitrary descendant by name.
        nodes = [n for n in unit.root.findall(lal.Name)
                 if n.text in expressions] if expressions else []
        if not expressions:
            for node in unit.root.findall(lal.Name):
                try:
                    if node.p_is_call:
                        nodes.append(node)
                except lal.PropertyError:
                    continue
        for expr in expressions:
            if not any(n.text == expr for n in nodes):
                report["calls"].append({"expression": expr, "source": str(source),
                                        "status": "MISSING_CONTEXT", "reason": "exact expression not found"})
        for node in nodes:
            result = {"expression": location(node), "status": "SEMANTICALLY_UNRESOLVED",
                      "parse_diagnostics": diagnostics, "semantic_diagnostics": [],
                      "properties": ["p_referenced_decl(imprecise_fallback=False)",
                                     "p_called_subp_spec", "p_expression_type",
                                     "p_referenced_defining_name(imprecise_fallback=False)"]}
            tick = time.perf_counter()
            try:
                entry = node
                while entry is not None and not entry.p_xref_entry_point:
                    entry = entry.parent
                if entry is None:
                    raise ValueError("no semantic entry point")
                resolved = entry.p_resolve_names
                result["semantic_diagnostics"] = [str(d) for d in entry.p_nameres_diagnostics]
                decl = node.p_referenced_decl(imprecise_fallback=False)
                spec = node.p_called_subp_spec
                defining = node.p_referenced_defining_name(imprecise_fallback=False)
                typ = node.p_expression_type
                result["resolution_seconds"] = time.perf_counter() - tick
                if decl is not None:
                    result["selected_declaration"] = location(decl)
                    result["selected_qualified_name"] = decl.p_fully_qualified_name
                result["called_profile"] = spec.text if spec is not None else None
                result["defining_name"] = location(defining) if defining is not None else None
                result["expression_type"] = typ.p_fully_qualified_name if typ is not None else None
                hot = time.perf_counter()
                for _ in range(20):
                    node.p_referenced_decl(imprecise_fallback=False)
                    node.p_called_subp_spec
                    node.p_expression_type
                    node.p_referenced_defining_name(imprecise_fallback=False)
                result["reused_context_query_seconds_mean"] = (time.perf_counter() - hot) / 20
                if not resolved or result["semantic_diagnostics"] or decl is None or spec is None or defining is None:
                    result["reason"] = "precise resolution incomplete"
                elif (not unit_record["resolved"] or events.parsing or events.missing
                      or report["project_diagnostics"]):
                    result.update(status="MISSING_CONTEXT", reason="project/unit diagnostics or missing dependencies")
                elif compiler and unit_record["compiler"]["exit"]:
                    result.update(status="SEMANTICALLY_UNRESOLVED",
                                  reason="independent compiler rejected unit; Libadalang selection is not authoritative",
                                  raw_libadalang_resolved=True)
                elif qualification_error:
                    result.update(status="SOURCE_NATIVE_MISMATCH", reason=qualification_error)
                elif native is None:
                    result["reason"] = "semantic resolution succeeded; no qualified native destination supplied"
                    result["semantic_resolved"] = True
                elif not compiler:
                    result.update(status="MISSING_CONTEXT", raw_libadalang_resolved=True,
                                  reason="independent compiler validity gate is required before linking")
                else:
                    canonical = decl.p_canonical_part(imprecise_fallback=False)
                    result["canonical_declaration"] = location(canonical)
                    tick = time.perf_counter()
                    status, evidence = match_native(canonical, spec, source_root, native)
                    result.update(evidence, status=status, semantic_resolved=True,
                                  reconciliation_seconds=time.perf_counter() - tick)
            except Exception as exc:
                result.update(error=f"{type(exc).__name__}: {exc}")
                if not isinstance(exc, lal.PropertyError):
                    result["status"] = "ANALYSIS_ERROR"
            report["calls"].append(result)
    report["missing_units"] = events.missing
    report["dependency_parse_diagnostics"] = events.parsing
    # Later lazy unit requests can invalidate earlier results: fail closed for
    # the complete batch rather than retaining an earlier authoritative link.
    if (events.missing or events.parsing or report["project_diagnostics"]
            or any(not u.get("resolved") for u in report["units"])):
        for call in report["calls"]:
            call.pop("hyperlink", None)
            call["status"] = "MISSING_CONTEXT"
    report["timings_seconds"]["total"] = time.perf_counter() - start
    report["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for call in report["calls"]:
        assert call["status"] in STATUSES
        assert "hyperlink" not in call or call["status"] == "RESOLVED_AND_MATCHED"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--source", required=True, action="append", type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-site", type=Path)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--expression", action="append", default=[])
    parser.add_argument("--compiler", type=Path,
                        help="explicit qualified gprbuild; mandatory for authoritative mappings")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.project.resolve(), [p.resolve() for p in args.source],
                         args.source_root.resolve(), args.native_site.resolve() if args.native_site else None,
                         args.qualification, args.expression, args.compiler)
    except Exception as exc:
        result = {"status": "ANALYSIS_ERROR", "error": f"{type(exc).__name__}: {exc}"}
    result["authority_contract"] = (
        "Only RESOLVED_AND_MATCHED hyperlinks are authoritative; raw Libadalang selections "
        "can be wrong on compiler-ambiguous Ada. Compiler validity and native qualification required.")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 1 if result.get("status") in ("ANALYSIS_ERROR", "MISSING_CONTEXT") else 0


if __name__ == "__main__":
    raise SystemExit(main())