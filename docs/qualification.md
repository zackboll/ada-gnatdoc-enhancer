# Bootstrap qualification

The bootstrap must pass:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m ada_gnatdoc_enhancer conformance --fixtures tests/fixtures
PYTHONPATH=src python -m ada_gnatdoc_enhancer --version
python -m compileall -q src
```

Four checked-in fixture roots model respectively three Core-like packages,
one Imgproc-like operation package with overloads, two Geometry-like packages,
and 29 MEL-like package names with a six-page static portal.

**These are synthetic, not the original pinned sites.** A passing result is
proof of the toolkit's exercised behavior, not full source compatibility or
GNATdoc compiler qualification. A real consumer adoption must compare pristine
and enhanced output to its independently validated source, warning/coverage and
anchor manifests, and run its own Ada/C++ regression gates.

The main suite tests deterministic duplicate invocation and negative controls
against changed type links, scripts, package destinations, unknown files,
source signatures, broken fragments, CSS and symlinks. HTML parser validation
is not equivalent to an independent assistive-technology audit.
