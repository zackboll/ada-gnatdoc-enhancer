# Pinned source-implementation matrix

Four Apache-2.0 projects were reviewed at these Git commit identities. Files
listed here are **reference sources**, not vendored copies; this project's
standalone implementation consolidates the shared behavior and carries the
same Apache-2.0 license. Native code, tool binaries, vendor trees and generated
production sites were not imported.

| Source | Reviewed commit | Representative upstream modules |
| --- | --- | --- |
| `zackboll/opencv_core_ada` | `c5545eee815431568495c6c76af83df56cf5c3dd` | `scripts/install_gnatdoc_theme.py`, `highlight_gnatdoc_ada.py`, `link_gnatdoc_types.py`, `enhance_gnatdoc_instances.py`, `enhance_gnatdoc_navigation.py`, `render_gnatdoc_guides.py`, `compare_gnatdoc_warnings.py`, `validate_docs.py` |
| `zackboll/opencv_imgproc_ada` | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` | Same presentation path, plus `check_doc_coverage.py`, operation categories and compiled guide fixtures |
| `zackboll/opencv_geometry_ada` | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` | Multi-package and external-Core source resolution, category browser, coverage/warning ratchets |
| `zackboll/ams-gra-mel-bridge` | `6065129aba5dee89e70b61e05a9e1c9b2c3061c0` | `build_docs_portal.py`, `validate_docs.py`, `gnatdoc_inventory.py`, `gnatdoc_coverage_model.py`, `check_doc_coverage.py`, warning classifier and source-integrity policy |

## Extracted foundations

- `theme.py` / bundled CSS: deterministic one-point theme insertion with native GNATdoc CSS retained.
- `syntax.py`: Ada lexer and conservative type-linker; text round-trip and link-integrity invariants.
- `native_html.py` / `inventory.py`: public source inventory and observed native identity reconciliation.
- `navigation.py` / bundled JS: searchable, bookmarkable package shell and operation categories.
- `guides.py`: strict static HTML portal and optional pinned CommonMark path.
- `warnings.py`: initial stable warning identity model; **not yet equivalent** to each consumer's full warning classifier.
- `coverage.py`: initial declaration presence check; MEL's 4,294-element source/renderer identity model remains external.
- `pipeline.py` / `validation.py`: offline deterministic HTML enhancement, expected output reconstruction and asset/link checks.

## Differences intentionally retained

1. Core's 25 Vector/Matrix instantiation summaries have complex template/member
   and shadowing rules. A generic-instance expansion module is **deferred**, not
   replaced with fabricated native anchors.
2. Imgproc's single huge package needs declaration categories and overloads.
   Geometry's two packages need package-qualified operation categories.
3. MEL's 29 public packages, trailing comments and one GNATdoc 26 package
   renaming omission require explicit consumer-owned coverage/exception guards.
   The bootstrap does not declare that omission covered.
4. External OpenCV Core type targets must be an exact, independently qualified
   dependency-site manifest; never compute remote native filenames.
5. Each consumer's documentation compiler invocation, generated artifacts,
   source-integrity approval policy and warning/coverage baselines remain local.

The checked-in GNATdoc test pages are **synthetic reconstructions** of the
observed serialization, not byte captures of these source commits. They must
not be used to assert complete production-site equivalence.
