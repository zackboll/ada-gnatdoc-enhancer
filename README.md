# Ada GNATdoc Enhancer

GNATDOC-002 pinned real-site qualification, authentic regression provenance,
observed compatibility failures and reproduction commands are documented in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/real-site-qualification.md`.
No consumer is currently certified fully adoption-ready.

GNATDOC-004 now passes structural qualification for **all four pinned native API
sites**, including MEL's source-verified renaming and two record Convention
omissions. See
`/home/zboll/git/ada-gnatdoc-enhancer/docs/mel-profile-compatibility.md`
for exact proof boundaries, unchanged consumer gates and independent evidence.

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
They exercise distinct source structures; production integration is a later task.

## Quick start

Requires Python 3.11 or newer; CI qualifies Python 3.11, 3.12 and 3.13 on Linux.
From a local checkout (no published release is required):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/gnatdoc-enhancer --version
.venv/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
```

For a non-editable installation, use `python -m pip install .`, or install a
locally built wheel as described under **Validation and distributions** below.
The core package has no runtime dependencies. Optional Markdown guides require
`python -m pip install '.[guides]'`.

Given a consumer repository that has already generated `_site/api/index.html`,
`_site/api/gnatdoc.css` and GNATdoc's SHA-256-named package pages:

```sh
gnatdoc-enhancer inventory --source-root . --config docs/gnatdoc-enhance.toml --site _site
gnatdoc-enhancer enhance --source-root . --config docs/gnatdoc-enhance.toml --site _site
gnatdoc-enhancer verify --source-root . --config docs/gnatdoc-enhance.toml --site _site
```

`enhance --dry-run` builds and verifies a temporary site without changing the
consumer. Enhancement of an already qualified site is byte-idempotent.

`--source-root` names the project containing Ada sources and configuration;
`--config` is relative to that root. `--site` defaults to `_site` under the
source root (an absolute path is also accepted). It is an **existing output
directory**, modified in place, not a separate input/output pair: keep a copy
of pristine GNATdoc output if needed. Native pages must be directly under
`api/`, even when the site itself is deeply nested. Arbitrarily nested package
page layouts are not supported. Symlinks in the site path or output tree are
rejected. Unapproved files fail qualification rather than being deleted.
For relative `--site` paths this includes symlinks in the supplied
`--source-root`; canonicalizing the project for source/configuration identity
does not bypass output-path validation. An explicitly supplied absolute site
is checked on its own path, independently of how the sources were located.

Try the bundled synthetic input without changing the checked-in fixture:

```sh
cp -R tests/fixtures/core /tmp/gnatdoc-core-example
gnatdoc-enhancer enhance --source-root /tmp/gnatdoc-core-example --config project.toml
gnatdoc-enhancer verify --source-root /tmp/gnatdoc-core-example --config project.toml
```

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

For GNATdoc 26.0.0 expression-function and abbreviated-enumeration support,
see [source-verified declaration profiles](docs/declaration-profile-compatibility.md).
Core/Imgproc/Geometry pass pinned full native API structural qualification;
MEL advances beyond its enum blocker but retains other inventory mismatches.
These results are not full production-adoption certification.

This tool expects the verified GNATdoc 26.0.0 native HTML shape. Unknown output
fails; it does not attempt permissive best-effort conversion. It is not a full
Ada semantic front end. In particular, complex nested scopes, arbitrary generic
instantiations and imported dependency type identities need explicit adapters
and conformance qualification. `coverage` currently reports declaration-level
presence, **not** the comprehensive member/prose coverage gates in MEL or Imgproc.

Published presentation manifests are not adversarial signed attestations; branch
CI and project-owned configuration still require independent code review.
The exact-source baselines remain in their owning repositories.

## Validation and distributions

After installing the package, run the same core checks as GitHub Actions:

```sh
python -m unittest discover -s tests -v
gnatdoc-enhancer conformance --fixtures tests/fixtures
python -m compileall -q src
gnatdoc-enhancer --help
python -m pip install build
python -m build
```

`python -m build` creates a wheel and source distribution in `dist/`. Verify
wheel execution in a fresh environment, without an editable install:

```sh
python -m venv /tmp/gnatdoc-wheel-env
/tmp/gnatdoc-wheel-env/bin/python -m pip install --no-deps dist/*.whl
env -u PYTHONPATH /tmp/gnatdoc-wheel-env/bin/python scripts/test_installed.py --fixtures tests/fixtures
```

The smoke check runs the installed CLI from a temporary working directory,
qualifies all four profiles, checks bundled CSS/JavaScript, enhances and verifies
the MEL synthetic site twice, and compares output hashes. Fixtures are test
inputs, not installed wheel resources: always provide `--fixtures` when running
installed conformance outside a source checkout. The source distribution includes
the fixtures and test helpers for repeatable source qualification.

Optional Chromium checks (not a cross-browser or accessibility certification):

```sh
python -m pip install playwright
python -m playwright install chromium
python scripts/test_browser.py
```

Automated browser coverage currently exercises the Core synthetic profile only.
Other browsers and complete real-site parity remain unqualified.

See [compatibility](docs/compatibility.md), [architecture](docs/architecture.md),
[contributing](CONTRIBUTING.md), [migration](docs/migration.md), and
[qualification](docs/qualification.md).

## Roadmap

- GDE-001: Source-aware shared toolkit and four offline profiles (**this bootstrap**).
- GDE-002: Full pinned-site conformance and production-independent semantic linking.
- GDE-003: First consumer migrations with exact snapshot parity.
- GDE-004: Optional expanded GNATdoc versions and generic-instance adapters.

No tags, releases, package publication, consumer repository changes or
production-site assertions are included in this bootstrap.

## Import into GitHub

See [repository import instructions](docs/repository-import.md) for the original
archive procedure. Never reinitialize or replace history in an existing repository.
