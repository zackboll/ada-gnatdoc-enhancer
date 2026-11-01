#!/usr/bin/env python3
"""Extract authentic fences; experimental wrappers are NEVER authoritative."""
import argparse
import json
from pathlib import Path
import re

from probe import analyze, digest

GUIDES = ("core-operations-guide", "ownership-and-views", "typed-access-guide",
          "interop-and-compatibility", "sparse-and-persistence-guide")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compiler", required=True, type=Path)
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=False)
    reports = []
    summaries = []
    for guide in GUIDES:
        path = args.core / "docs" / (guide + ".md")
        text = path.read_text()
        blocks = list(re.finditer(r"^```ada[^\n]*\n(.*?)^```", text, re.M | re.S))
        summaries.append({"guide": guide, "sha256": digest(path), "ada_fences": len(blocks)})
        for i, match in enumerate(blocks, 1):
            original = match[1]
            # A full procedure with context clauses and its own end identifier
            # is defensible; declaration outlines and context+declare are not.
            proc = re.search(r"(?m)^procedure\s+(\w+)", original, re.I)
            ending = re.search(r"\bend\s+" + re.escape(proc[1]) + r"\s*;", original, re.I) if proc else None
            complete = bool(ending and not original[ending.end():].strip())
            record = {"guide": guide, "fence": i, "original": original,
                      "source": str(path), "start_line": text[:match.start()].count("\n") + 2,
                      "guide_sha256": digest(path), "authoritative": False}
            workspace = args.workspace / f"{guide}-{i}"
            workspace.mkdir()
            (workspace / "original.txt").write_text(original)
            if complete:
                classification = "COMPLETE_COMPILATION_UNIT"
                name = proc[1].lower()
                source = workspace / (name + ".adb")
                source.write_text(original)
                record["added_context"] = ""
            else:
                classification = ("FRAGMENT_NEEDS_MISSING_DECLARATIONS_OR_VISIBILITY"
                                  if not original.lstrip().startswith("generic")
                                  else "FRAGMENT_REQUIRES_SYNTHESIZED_CONTEXT")
                # Preserve bytes between wrapper prefix/suffix. Do not invent
                # declarations for Image, A, B, Process, Reader, etc.
                name = "fragment"
                source = workspace / "fragment.adb"
                context = "with OpenCV.Core; use OpenCV.Core;\nprocedure Fragment is\nbegin\n"
                source.write_text(context + original + "\nend Fragment;\n")
                record["added_context"] = {"prefix": context, "suffix": "\nend Fragment;\n",
                                           "declarations": [], "experimental_only": True}
            project = workspace / "example.gpr"
            project.write_text(f'with "{args.core / "opencv_core.gpr"}";\n'
                               'project Example is\n'
                               '   for Source_Dirs use (".");\n'
                               f'   for Source_Files use ("{source.name}");\n'
                               '   for Object_Dir use "obj";\n'
                               '   for Create_Missing_Dirs use "True";\n'
                               '   package Compiler is\n'
                               '      for Default_Switches ("Ada") use ("-gnat2022");\n'
                               '   end Compiler;\nend Example;\n')
            report = analyze(project, [source], args.core, compiler=args.compiler)
            record.update(classification=classification, analysis=report,
                          project=str(project), compilation_unit=str(source))
            # Complete-unit claims require the ENTIRE unit to resolve, not just
            # a handful of individually successful calls. The explicit compiler
            # gate must independently accept the unchanged complete unit.
            calls = report["calls"]
            record["candidate_reliable"] = bool(complete and calls
                and not report.get("project_diagnostics") and not report.get("missing_units")
                and not report.get("dependency_parse_diagnostics")
                and all(u.get("resolved") for u in report.get("units", []))
                and all(u.get("compiler", {}).get("exit") == 0 for u in report.get("units", []))
                and all(c.get("semantic_resolved") for c in calls))
            reports.append(record)
    result = {"guides": summaries, "examples": reports,
              "total_ada_fences": len(reports),
              "candidate_reliable_without_synthesis": sum(r["candidate_reliable"] for r in reports),
              "note": "No invented surrounding declarations establish authority for fragments; independent compiler gate is mandatory."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()