#!/usr/bin/env python3
"""Observational cold/warm semantic timings; NEVER an authoritative mapping."""
import argparse
import json
from pathlib import Path
import resource
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = {"authority": False, "cold_process_not_cold_os_cache": True, "calls": []}
    start = time.perf_counter()
    import libadalang as lal
    imported = time.perf_counter()
    standalone = lal.AnalysisContext()
    initialized = time.perf_counter()
    project = lal.GPRProject(str(args.core / "docs/example.gpr"), print_errors=False)
    context = project.create_context()
    loaded = time.perf_counter()
    unit = context.get_from_file(str(args.core / "docs/example.adb"))
    parsed = time.perf_counter()
    for text in ["Create (2, 3, (Depth => UInt8, Channels => 1))", "Image.Clone"]:
        nodes = [n for n in unit.root.findall(lal.Name) if n.text == text]
        assert len(nodes) == 1
        node = nodes[0]
        tick = time.perf_counter()
        declaration = node.p_referenced_decl(imprecise_fallback=False)
        spec = node.p_called_subp_spec
        typ = node.p_expression_type
        defining = node.p_referenced_defining_name(imprecise_fallback=False)
        first = time.perf_counter() - tick
        tick = time.perf_counter()
        for _ in range(100):
            node.p_referenced_decl(imprecise_fallback=False)
            node.p_called_subp_spec
            node.p_expression_type
            node.p_referenced_defining_name(imprecise_fallback=False)
        result["calls"].append({"expression": text, "first_query_seconds": first,
                                "warm_query_seconds_mean": (time.perf_counter() - tick) / 100,
                                "kind": node.kind_name, "profile": spec.text})
    tick = time.perf_counter()
    assert context.get_from_file(str(args.core / "docs/example.adb")) == unit
    result.update(import_seconds=imported-start, initialization_seconds=initialized-imported,
                  project_loading_seconds=loaded-initialized, parsing_seconds=parsed-loaded,
                  reused_unit_seconds=time.perf_counter()-tick,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  project_diagnostics=project.errors,
                  parse_diagnostics=[str(d) for d in unit.diagnostics])
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()