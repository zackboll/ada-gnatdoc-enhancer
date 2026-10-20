# Changelog

## 0.1.0 — release candidate (GNATDOC-012; not yet published)

- Consolidate merged GNATDOC-001–011: fail-closed source/native qualification,
  navigation, highlighting, conservative local/external type links, 25 optional
  generic summaries, authored guides/portals, subtype/current-package links,
  page metadata and native-symbol bookmarks.
- Include R1's separately authorized 242 incoming instance references and R2's
  incoming-router canonical query reconstruction.
- Preserve default and symbol-only routers, including the documented outstanding
  symbol-only canonicalization issue; no compatibility rebaseline.
- Synchronize module, distribution and CLI versions; adopt SPDX Apache-2.0
  metadata with LICENSE; preserve Python >=3.11, optional guide pins and the
  dependency-free core.
- Independently qualify wheel and extracted-sdist rebuilt wheel; keep complete
  test inputs without bundling large historical evidence.
- Document consumer boundaries, upgrades, release stop conditions and the later
  GNATDOC-013 procedure. No tagging, publication or consumer adoption.

## Historical pre-release entries

## Unreleased — GNATDOC-009B

- Link exact two-identifier current-package public type/subtype marks with
  source-owned native destinations and conservative actual-short-prefix
  shadowing checks. No external fallback or arbitrary short-owner inference.
  Add authentic nine-occurrence MEL regressions and independent qualification.

## Unreleased — GNATDOC-010

- Source-verified document metadata: every generated API page gets `lang="en"`,
  an explicit head, a UTF-8 charset and a title from its verified package (or
  `API Reference`) and the project name; Markdown guides get their site-map
  label as title, which must equal the H1. Author pages must carry their own
  metadata. See `docs/html-page-metadata.md`.
- Reconciled with GNATDOC-009A ordinary subtype-base links (merged `main`
  `426f388`); the combined behavior is requalified on every real consumer,
  including the current Geometry `Contour` → Core `OpenCV.Point_Array` link.

## 0.1.0.dev0 — bootstrap

- Packaging, CLI, offline enhancement and verification, source inventories, presentation assets.
- Four sample project profiles and offline regression fixtures.
- No compatibility or distribution release claimed.
