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

## GNATDOC-001 checkout qualification

### Provenance and repository state

The task began with an existing, clean clone, not an empty repository. Both
local and hosted `main` were at
`903edb4c1ed2d8cc7b564862d5b828661e49d021` (`initial bootstrap commit`). No
placeholder commit, reinitialization, or history rewrite was appropriate.
`feature/001-qualify-bootstrap` was created from that published baseline. The
PR reviews qualification changes; the original bootstrap was already on main.
The PR description records the final tested commit and hosted CI results.

The authoritative archive was located at
`/home/zboll/Downloads/ada-gnatdoc-enhancer-bootstrap.zip`, SHA-256:

```text
b2a171fb1b7a460724c24c195692d4e1831bb4fdc91323f81ca167a6353bcf97
```

All **170 archive files matched the initial checkout byte-for-byte**, preserving
the archive root structure after removing its enclosing directory:

| Area | Archive files |
| --- | ---: |
| Root metadata, license, README, packaging and Makefile | 8 |
| GitHub Actions | 1 |
| Architecture/configuration/compatibility/provenance/import documentation | 7 |
| Example profiles | 4 |
| Fixture generator and optional browser checks | 2 |
| Python implementation, adapters and CSS/JavaScript | 23 |
| Tests, synthetic Ada/native HTML, guides and manifests | 102 |
| Generated `build/lib` copies | 23 |

The 147 non-build files were already tracked. The archive's 23 generated
`build/lib` copies were present but ignored by its existing `.gitignore`;
they are not a second authoritative implementation and remain generated output.
No archive content was independently recreated. No consumer repositories changed.

### Defects reproduced and corrected

1. **Symlink escape/write-through:** resolving the site before checking it hid
   symlink roots/ancestors. Copying a symlinked `api` directory into staging
   allowed generation to modify its external target before validation rejected
   it. Regressions reproduced the external mutation. Enhancement and verification
   now reject symlink paths, symlink descendants and nonregular output nodes
   before staging or reading the publication manifest.
2. **Malformed presentation manifest:** JSON null, numbers and arrays containing
   objects could raise uncaught `TypeError`. Validate the top-level object shape
   explicitly; malformed input now produces CLI status 2 without a traceback.
3. **Checkout-dependent test:** four-profile testing implicitly searched for
   fixtures beside the installed module. Pass the test-owned fixture directory
   explicitly so the identical suite can validate an installed wheel.
4. **Incomplete source distribution:** setuptools included test modules but
   omitted their helper and fixtures. `MANIFEST.in` now includes the full test
   inputs, scripts, examples, workflow and contributor/architecture documentation.
   A wheel rebuilt from the sdist passes the suite against the extracted inputs.

No parser redesign, removed tests, weakened assertions or suppressed failures
were required. Sixteen new deterministic regression methods cover preservation,
repeat execution, injection counts, unknown/ambiguous/unresolved types, real
subtype anchors, malformed/missing input, nested site placement and output bounds.

### Commands and observed results

Local execution used Linux and **Python 3.13.5**. Commands below were run from
`/home/zboll/git/ada-gnatdoc-enhancer` unless a different directory is shown.
Build requirements were installed in disposable virtual environments; runtime
enhancement and conformance used no network access.

```sh
# Before changes: 45 tests passed; all four synthetic profiles passed.
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m ada_gnatdoc_enhancer conformance --fixtures tests/fixtures

# Editable installation, final tests, compilation and distributions.
python3 -m venv .venv
.venv/bin/python -m pip install -e . build
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m build

# Clean wheel installation; execution outside the checkout and without PYTHONPATH.
python3 -m venv /tmp/gnatdoc-001-wheel-env
/tmp/gnatdoc-001-wheel-env/bin/python -m pip install --no-deps dist/*.whl
cd /tmp
env -u PYTHONPATH /tmp/gnatdoc-001-wheel-env/bin/gnatdoc-enhancer --help
env -u PYTHONPATH /tmp/gnatdoc-001-wheel-env/bin/python /home/zboll/git/ada-gnatdoc-enhancer/scripts/test_installed.py --fixtures /home/zboll/git/ada-gnatdoc-enhancer/tests/fixtures
env -u PYTHONPATH /tmp/gnatdoc-001-wheel-env/bin/python -m unittest discover -s /home/zboll/git/ada-gnatdoc-enhancer/tests -v
```

The source/editable and installed-wheel suites each passed **61 tests, zero
failures/errors/skips**. Both distributions built successfully:
`ada_gnatdoc_enhancer-0.1.0.dev0-py3-none-any.whl` and
`ada_gnatdoc_enhancer-0.1.0.dev0.tar.gz`. The wheel imported from the clean
environment's `site-packages`, not the checkout. Installed smoke checks passed
CLI help, all four profiles, the three bundled assets, Ada highlighting, type
links, search markup, and unchanged source/configuration files. MEL enhancement
and verification produced **42 files, 37 HTML pages, 29 packages, 10 declaration
snippets and 7 linked type references**; the second invocation changed no bytes.

Source-distribution qualification also passed:

```sh
cd /home/zboll/git/ada-gnatdoc-enhancer
/tmp/gnatdoc-001-wheel-env/bin/python -m pip wheel --no-deps --wheel-dir /tmp/gnatdoc-001-sdist-wheel dist/*.tar.gz
mkdir -p /tmp/gnatdoc-001-sdist-source
tar -xzf dist/ada_gnatdoc_enhancer-0.1.0.dev0.tar.gz -C /tmp/gnatdoc-001-sdist-source
python3 -m venv /tmp/gnatdoc-001-sdist-env
/tmp/gnatdoc-001-sdist-env/bin/python -m pip install --no-deps /tmp/gnatdoc-001-sdist-wheel/*.whl
cd /tmp/gnatdoc-001-sdist-source/ada_gnatdoc_enhancer-0.1.0.dev0
env -u PYTHONPATH /tmp/gnatdoc-001-sdist-env/bin/python -m unittest discover -s tests -v
env -u PYTHONPATH /tmp/gnatdoc-001-sdist-env/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
```

Result: rebuilt wheel installed successfully; **61 tests passed**, and all four
extracted synthetic profiles passed. The build emitted existing setuptools
license-table/classifier deprecation warnings, not build errors. Updating the
license metadata/backend minimum can be done separately before release.

### Four-profile results

| Requested profile | Fixture | Packages | HTML pages | Linked types | Deterministic / idempotent |
| --- | --- | ---: | ---: | ---: | --- |
| `opencv_core_ada` | `core` | 3 | 4 | 4 | Pass / pass |
| `opencv_imgproc_ada` | `imgproc` | 1 | 2 | 6 | Pass / pass |
| `opencv_geometry_ada` | `geometry` | 2 | 3 | 5 | Pass / pass |
| `ams-gra-mel-bridge` | `mel` | 29 | 37 | 7 | Pass / pass |

Conformance reconstructs and validates exact output, source declarations,
navigation destinations, relative resources, local links and declaration
fragments. Tests additionally check original declaration text/native CSS and
passive unknown elements, unresolved and ambiguous references, subtype links,
duplicate scripts/styles and deeply nested **site locations**. All package pages
must still be directly in `api/`; arbitrary package-page subdirectories are not
supported or qualified. Unsafe unknown active elements are rejected, not preserved.

### Browser and CI scope

The existing optional browser check was actually run:

```sh
cd /home/zboll/git/ada-gnatdoc-enhancer
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/test_browser.py
node --check src/ada_gnatdoc_enhancer/assets/gnatdoc-navigation.js
git diff --check
```

Chromium passed for **Core only**, widths 1280/390, light/dark schemes,
search/clear, package selection, query bookmarks, back navigation, iframe
highlighting/type links, horizontal overflow and JavaScript-disabled native
navigation. This is not Firefox/WebKit, assistive-technology or real-site testing.

GitHub Actions retains the Python 3.11/3.12/3.13 test/conformance matrix and now
builds wheel **and** sdist, qualifies installed-wheel execution outside checkout,
runs the full suite against the wheel, rebuilds from sdist, and qualifies the
extracted sdist tests and fixtures. Hosted status must be checked on the PR's
exact head SHA; a local pass alone does not establish hosted CI success.

### Readiness for Task 002

This establishes a reproducible bootstrap baseline for independent review and
subsequent pinned-real-site qualification. It is **not production adoption**.
Task 002 still needs complete pristine real-site inventories/anchor parity,
consumer-owned compiler/warning/member-coverage gates, semantic edge cases,
broader browser/accessibility evidence and independent review of exceptions.
The filesystem checks assume the caller does not concurrently replace paths;
they are not a sandbox against an adversarial concurrent writer. No deployments,
releases, tags, consumer migrations or merges are part of this qualification.

## GNATDOC-001-R1: CLI symlink-ancestor policy

Starting from PR #1 head `12de1e30a79109fa9e1688f8d76913f81b63f69d`, the
original **61 tests passed**, but an independent disposable Core fixture
confirmed a CLI bypass. With a sibling `alias` symlink to the fixture's project
root, the direct pipeline rejected `alias/_site`, while:

```sh
gnatdoc-enhancer enhance --source-root /tmp/<isolated-fixture>/alias --config project.toml --site _site
```

exited **0**, modified all four native HTML pages and added
`api/gnatdoc-theme.css`, `api/gnatdoc-navigation.js` and `api/presentation.json`.
This contradicted the README policy rejecting symlinks in the output path.
The reproduction used a temporary copy, never the checked-in fixture or a
consumer site.

`cli.run()` resolved the project root before constructing relative site paths,
so `site_root()` could no longer see the alias. The CLI now retains an unresolved
absolute project path (`Path.cwd() / args.source_root`) for constructing relative
output paths. Configuration loading and source identities still use its resolved
root. Explicit absolute site paths remain independent and are passed unchanged
to the pipeline. **`site_root()` and the filesystem architecture are unchanged.**

Nine new subprocess CLI regressions cover explicit/default relative sites,
relative source-root aliases, source-root ancestors, absolute and relative site
aliases, dry-run/verification rejection, ordinary relative/absolute paths, and
canonical source identity through an alias with a legitimate absolute output.
Five tests failed against the prior implementation. After correction all nine
pass; every rejected-path assertion checks status **2**, no traceback, empty
stdout and unchanged project file hashes. The installed-wheel smoke script also
checks the originally reported invocation via the published console entry point.

Local Linux / Python 3.13.5 requalification commands and results:

```sh
cd /home/zboll/git/ada-gnatdoc-enhancer
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m build --outdir /tmp/gnatdoc-r1-dist
python3 -m venv /tmp/gnatdoc-r1-wheel-env
/tmp/gnatdoc-r1-wheel-env/bin/python -m pip install --no-deps /tmp/gnatdoc-r1-dist/*.whl
cd /tmp
env -u PYTHONPATH /tmp/gnatdoc-r1-wheel-env/bin/gnatdoc-enhancer --help
env -u PYTHONPATH /tmp/gnatdoc-r1-wheel-env/bin/python /home/zboll/git/ada-gnatdoc-enhancer/scripts/test_installed.py --fixtures /home/zboll/git/ada-gnatdoc-enhancer/tests/fixtures
env -u PYTHONPATH /tmp/gnatdoc-r1-wheel-env/bin/python -m unittest discover -s /home/zboll/git/ada-gnatdoc-enhancer/tests -v
/tmp/gnatdoc-r1-wheel-env/bin/python -m pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/gnatdoc-r1-sdist-wheel /tmp/gnatdoc-r1-dist/*.tar.gz
mkdir -p /tmp/gnatdoc-r1-sdist-source
tar -xzf /tmp/gnatdoc-r1-dist/ada_gnatdoc_enhancer-0.1.0.dev0.tar.gz -C /tmp/gnatdoc-r1-sdist-source
python3 -m venv /tmp/gnatdoc-r1-sdist-env
/tmp/gnatdoc-r1-sdist-env/bin/python -m pip install --no-deps /tmp/gnatdoc-r1-sdist-wheel/*.whl
cd /tmp/gnatdoc-r1-sdist-source/ada_gnatdoc_enhancer-0.1.0.dev0
env -u PYTHONPATH /tmp/gnatdoc-r1-sdist-env/bin/python -m unittest discover -s tests -v
env -u PYTHONPATH /tmp/gnatdoc-r1-sdist-env/bin/gnatdoc-enhancer conformance --fixtures tests/fixtures
env -u PYTHONPATH /tmp/gnatdoc-r1-sdist-env/bin/python scripts/test_installed.py --fixtures tests/fixtures
```

- **70/70 tests passed** from source, against the clean wheel outside checkout,
  and from extracted sdist against its rebuilt wheel: no failures/errors/skips.
- Wheel and sdist built; rebuilt-sdist wheel installed. Both installed smoke
  checks passed CLI help, alias rejection without writes, assets, enhancement,
  verification, idempotence and all four synthetic profiles.
- Four-profile package/HTML/type-link counts remain respectively Core 3/4/4,
  Imgproc 1/2/6, Geometry 2/3/5, MEL 29/37/7; deterministic and idempotent.
- Existing optional Chromium Core checks passed again; all prior real-site,
  browser and concurrent-writer limitations remain unchanged.

The existing CI automatically includes the new regressions in its Python
3.11/3.12/3.13 matrix, installed-wheel suite and extracted-sdist suite. PR #1's
R1 update records the exact new tested head and hosted results. No new PR,
filesystem-policy relaxation, history rewrite or production adoption is involved.
