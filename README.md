# Ada GNATdoc Enhancer

## v0.1.4 preparation: opt-in Ada examples (not published)

GNATDOC-027 adds static Ada fence and exact-source landing-example highlighting,
with optional conservative source/native-verified API links. It is disabled by
default. Feature-off output differs from official v0.1.3 only in the
version-bound presentation manifest. See [configuration and limitations](docs/ada-examples.md).
Preparation archives are not public release assets; publication is not authorized.

Offline full-documentation search is available through the versioned opt-in
`[search]` configuration. See [documentation search](docs/documentation-search.md)
for coverage, authority, bounds, and qualification. Existing consumers retain
navigation-link filtering unless explicitly opted in.

**Offline, source-verified enhancement of GNATdoc 26.0.0 HTML sites.**

The published **v0.1.3 baseline** incorporates opt-in consumer-owned custom themes
(GNATDOC-017), opt-in stable external symbol bookmarks (GNATDOC-018), and default
declaration visibility restoration after browser history traversal (GNATDOC-019).
and GNATDOC-023 opt-in documentation search. Python **3.11, 3.12 and 3.13** are supported on Linux. The core
has **no runtime dependencies** and needs neither Ada nor GNATdoc at installation.

## Install a standalone distribution

For candidate qualification, build from the exact reviewed source commit with
`python -m build` and verify its archive audit and SHA-256 inventory. The examples
below name candidate artifacts, not an already published v0.1.2 release. Never
replace official v0.1.1 assets. See the [publication gates](docs/releasing.md).

```sh
python3 -m venv /tmp/enhancer-env
/tmp/enhancer-env/bin/python -m pip install /path/to/ada_gnatdoc_enhancer-0.1.2-py3-none-any.whl
/tmp/enhancer-env/bin/gnatdoc-enhancer --version
/tmp/enhancer-env/bin/gnatdoc-enhancer --help
# Alternative: standalone sdist (requires the build backend).
/tmp/enhancer-env/bin/python -m pip install /path/to/ada_gnatdoc_enhancer-0.1.2.tar.gz
```

Optional Markdown guides require the `guides` extra: install the wheel as
`'/path/to/ada_gnatdoc_enhancer-0.1.2-py3-none-any.whl[guides]'` or preinstall
`markdown-it-py==3.0.0` and `mdurl==0.1.2`. For offline use, provision those
wheels and the sdist build requirements in advance, then use `--no-index` and
`--find-links`. The renderer is optional; it is not bundled into the wheel.

## Configure and run

External type links remain exact native page/fragment URLs by default, including
precise JavaScript-disabled selection. An independently approved Core publisher
record can opt selected types into canonical package-plus-symbol bookmarks,
requiring `external_type_target = "_top"`. Stable routing needs publisher
JavaScript; without it, genuine native navigation remains available but automatic
declaration selection is not promised. See
[external bookmarks](docs/stable-public-symbol-bookmarks.md#external-publisher-bookmarks-gnatdoc-018r1).
This capability is not approval to migrate any consumer.

First build the consumer with its approved Ada toolchain and generate native
HTML with **GNATdoc 26.0.0**. Configure source directories, site layout,
navigation and security in reviewed TOML; see the four example profiles and
[configuration contract](docs/configuration.md).

```sh
gnatdoc-enhancer inventory --source-root /path/to/consumer --config docs/gnatdoc-enhance.toml --site /path/to/output
gnatdoc-enhancer enhance --dry-run --source-root /path/to/consumer --config docs/gnatdoc-enhance.toml --site /path/to/output
gnatdoc-enhancer enhance --source-root /path/to/consumer --config docs/gnatdoc-enhance.toml --site /path/to/output
gnatdoc-enhancer verify --source-root /path/to/consumer --config docs/gnatdoc-enhance.toml --site /path/to/output
```

`--config` is relative to `--source-root`. Absolute site paths are independent;
relative site paths are rooted at the supplied project path. Symlink roots,
aliases and descendants are rejected. Dry-run stages and verifies output without
changing the consumer. Qualified enhancement is deterministic and byte-idempotent.

## Capabilities

* Default-router restoration: an exact URL/fragment can select a
  declaration that is outside the iframe viewport. Matching load/hash completion,
  Back/Forward and `pageshow` now reveal only the source/native-approved target,
  with deferred callbacks invalidated by newer selections. No global scroll policy,
  package-only scroll reset, or URL-policy redesign is introduced. See
  [declaration history](docs/api-navigation-history.md#gnatdoc-019-default-declaration-visibility).
  The default JavaScript publication hash changes and requires consumer
  requalification; no released v0.1.1 asset is replaced.

* Opt-in custom themes: paired `[presentation].theme_css_source` and
  `theme_css_sha256` publish an independently approved consumer stylesheet at
  the existing theme path. Source/configuration are rechecked by `verify`;
  unsafe resources and encoding fail closed, never sanitized. Omission preserves
  the bundled theme bytes. No landing HTML, guide CSS, native CSS or navigation
  rewrite is needed. See [syntax, real Core example and rollback](docs/configuration.md).

* Light/dark presentation, preserved native CSS, Ada highlighting, searchable
  packages, source-order operation/overload navigation, declaration/category
  browsing, direct links and browser history.
* Conservative source/native-qualified local, subtype-base, current-package
  and explicitly pinned external Core type links; no guessed destinations.
* Opt-in `[presentation] external_type_target = "_top"` lets authorized external
  type links leave the iframe. Omission preserves default navigation; local and
  generic-instance links, JavaScript and CSS are unchanged. See
  [the navigation contract](docs/external-type-target-navigation.md).
* Optional hash-bound authored Markdown/HTML guides and portals, with verified
  titles, language and charset metadata.
* Optional source-qualified summaries of the 25 supported Core Vector/Matrix
  instances. Explanatory summaries never become fabricated native members.
* Optional stable native type/subtype bookmarks and separately opted-in incoming
  generic-instance routing: 215 native symbols and 242 references to 25 summaries
  in each independently pinned Core qualification.
* Exact inventories, source signatures, native destination preservation, local
  link checks, publication reconstruction, mutation rejection and conformance.

See [symbol and instance routing](docs/stable-public-symbol-bookmarks.md),
[generic summaries](docs/generic-instance-summaries.md),
[authored content](docs/authored-guides-portal-compatibility.md),
[type links](docs/current-package-type-links.md), and
[metadata](docs/html-page-metadata.md) for opt-ins and bounded grammars.

## Security, limitations and release boundaries

Unknown GNATdoc shapes, ambiguous source/native identities, unapproved paths,
unsafe HTML/URLs, unexpected files and modified publication bytes fail closed.
Core enhancement makes no network requests. Source/configuration and pinned
qualification inputs need independent review; presentation manifests are not
signed adversarial attestations. The parser is not a complete Ada semantic front
end. Unsupported scopes, instantiations and renderer shapes are rejected rather
than acquiring guessed authority. Other GNATdoc versions are unsupported.

**Corrected symbol-only canonical URLs:** GNATDOC-011R3 clears inherited query
parameters and unsupported outer fragments before reconstructing approved package,
symbol or declaration state. A valid selection after a rejected dirty query now
survives reload. R2 intentionally fixed only the incoming-instance router; its
historical evidence does not qualify R3. Default and incoming-instance router
bytes were unchanged by R3; v0.1.2 intentionally changes the default router for
GNATDOC-019. See [symbol routing](docs/stable-public-symbol-bookmarks.md).

The toolkit does **not** replace Ada compilation, GNATdoc generation,
source-integrity verification, comprehensive member/prose coverage checks,
warning ratchets, compiled guide examples or deployment qualification.
`coverage` is declaration-level reporting, not a substitute for consumer gates.
MEL's approved renderer exceptions remain narrowly source-verified, not waived.
Linux/Chromium evidence is not cross-browser, cross-platform or complete
accessibility certification. Shared-package releasability is **not** a blanket
production-migration certificate for any consumer.

## Qualification and upgrading

The sdist includes the complete Python tests, four synthetic profiles, authentic
reduced fixtures, browser runners and the small provenance records required by
tests. The wheel contains implementation modules, CSS/JS, license and metadata,
not consumer sites or tests. Large historical evidence remains unchanged in Git,
not bundled into release archives.

```sh
# From an extracted sdist, using a non-editably installed distribution:
# Provide Node.js explicitly as a test prerequisite (not a core dependency).
python -m unittest discover -s tests -v
gnatdoc-enhancer conformance --fixtures tests/fixtures
python scripts/test_installed.py --fixtures tests/fixtures
```

Synthetic conformance never substitutes for independently pinned real sites.
Historical campaigns remain under `docs/evidence/`; current release results and
source/artifact identities are described in
[v0.1.4 preparation evidence](docs/evidence/gnatdoc028/README.md). Historical
[v0.1.3 preparation evidence](docs/evidence/gnatdoc024/README.md),
[v0.1.2 preparation evidence](docs/evidence/gnatdoc020/README.md),
[v0.1.1 evidence](docs/evidence/gnatdoc015/README.md) and the original
[v0.1.0 qualification](docs/release-0.1.0-qualification.md) remains historical.

For upgrades, regenerate from pristine native output: the version-bound
presentation manifest changes from `0.1.3` to `0.1.4`, so do not carry an
old manifest into release verification. Recheck source, native, warning,
coverage, guide and browser baselines in a separate consumer PR. See
[migration](docs/migration.md), the [consumer matrix](docs/release-compatibility.md),
and the [auditable release procedure](docs/releasing.md).

Full offline documentation search remains an explicit opt-in. Without `[search]`,
the existing navigation-link filter and native routing remain. The v0.1.3 label
**Filter navigation links** and all search assets remain byte-identical when the
new example options are off. See [search configuration, browser requirements
and scope](docs/documentation-search.md). No consumer migration is automatic.

Historical bootstrap provenance remains in [qualification](docs/qualification.md)
and [repository import](docs/repository-import.md). Do not reinitialize history.