# Ada GNATdoc Enhancer

**Offline, source-backed GNATdoc HTML enhancement for Ada documentation websites.**

A development-stage Python CLI that adds an accessible light/dark theme, Ada
syntax highlighting, conservatively linked type references, searchable package
navigation, declaration/category browsing, and optional guide pages to a
**previously generated GNATdoc 26.0.0 site**. It also validates exact site file
inventories, source/public-package identities, local destinations, publication
safety and determinism. The original GNATdoc CSS is preserved.

This is a **0.1.0.dev0 bootstrap**, not a published Python/Alire package or a
claim of four complete production-site migrations. The checked-in four
conformance profiles contain **explicitly synthetic GNATdoc HTML fixtures**.
They exercise distinct source structures; full site acceptance is a later task.

## Quick start

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/gnatdoc-enhancer --version
.venv/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
```

Given a consumer repository that has already generated `_site/api/index.html`,
`_site/api/gnatdoc.css` and GNATdoc's SHA-256-named package pages:

```sh
gnatdoc-enhancer inventory --source-root . --config docs/gnatdoc-enhance.toml --site _site
gnatdoc-enhancer enhance --source-root . --config docs/gnatdoc-enhance.toml --site _site
gnatdoc-enhancer verify --source-root . --config docs/gnatdoc-enhance.toml --site _site
```

`enhance --dry-run` builds and verifies a temporary site without changing the
consumer. Enhancement of an already qualified site is byte-idempotent.

The tool **does not compile Ada, execute GNATdoc, fetch dependencies, publish to
GitHub Pages or modify a Git repository**. Keep each consumer's compiler,
GNATdoc version, warnings, native source-integrity and coverage gates in its
own CI workflow. The publication checker is a supplement, not a substitute.

## Shared features

- Responsive local CSS with light/dark palettes, accessible focus and scrolling code.
- Source-backed type positions and conservative visibility/shadowing resolution.
  Ambiguous and unsupported references remain unlinked.
- Syntax highlighting that preserves escaped declaration text and type anchors.
- Ordinary package sidebar, optional operation categories, local searchable
  navigation and query-parameter package bookmarks. Native links still work
  with JavaScript disabled; no code scripts run in declaration pages.
- Strict authored HTML portal with verified package links; optional Markdown
  guides via pinned `markdown-it-py==3.0.0` / `mdurl==0.1.2`.
- Original native HTML captured and protected by deterministic, independently
  reconstructed presentation expectations; no guesses about hashed page names.
- Source inventory, stable-warning comparison, and declaration-level coverage
  reporting (not a full replacement for the consumer's member-level ratchet).

## Project configuration

See [configuration](docs/configuration.md) and four commented starting profiles
in `examples/profiles/`. Profiles are **examples** and must be reconciled with
actual consumer sources/anchors before use. A profile cannot authorize
unrecognized GNATdoc HTML, missing declarations or invalid links.

For a working end-to-end example (including raw input HTML), see
`tests/fixtures/core`, `tests/fixtures/imgproc`, `tests/fixtures/geometry`
and `tests/fixtures/mel`.

## Source projects and attribution

The package consolidates design and selected implementation patterns from:

- [OpenCV Core Ada](https://github.com/zackboll/opencv_core_ada)
- [OpenCV Imgproc Ada](https://github.com/zackboll/opencv_imgproc_ada)
- [OpenCV Geometry Ada](https://github.com/zackboll/opencv_geometry_ada)
- [AMS GRA MEL Bridge](https://github.com/zackboll/ams-gra-mel-bridge)

All are Apache-2.0. See the [pinned source matrix](docs/source-implementation-matrix.md)
for exact reviewed commits, script roles, reusable parts, and known divergences.
Original Ada interfaces, native libraries and generated sites are **not vendored**.

## Safety and limitations

This tool expects the verified GNATdoc 26.0.0 native HTML shape. Unknown output
fails; it does not attempt permissive best-effort conversion. It is not a full
Ada semantic front end. In particular, complex nested scopes, arbitrary generic
instantiations and imported dependency type identities need explicit adapters
and conformance qualification. `coverage` currently reports declaration-level
presence, **not** the comprehensive member/prose coverage gates in MEL or Imgproc.

Published presentation manifests are not adversarial signed attestations; branch
CI and project-owned configuration still require independent code review.
The exact-source baselines remain in their owning repositories.

Run unit tests:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

See [compatibility](docs/compatibility.md), [architecture](docs/architecture.md),
[migration](docs/migration.md), and [qualification](docs/qualification.md).

## Roadmap

- GDE-001: Source-aware shared toolkit and four offline profiles (**this bootstrap**).
- GDE-002: Full pinned-site conformance and production-independent semantic linking.
- GDE-003: First consumer migrations with exact snapshot parity.
- GDE-004: Optional expanded GNATdoc versions and generic-instance adapters.

No tags, releases, package publication, consumer repository changes or
production-site assertions are included in this bootstrap.

## Import into GitHub

For the already-created empty destination repository, follow
[repository import instructions](docs/repository-import.md). The ZIP itself
performs no pushes or merges.
