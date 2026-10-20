# Consumer migration and toolkit upgrades

1. Qualify the installed release against **real** GNATdoc 26.0.0 output, not only the four
   synthetic fixtures. Save pristine API pages and compare all original native
   source signatures and anchors to independent snapshots.
2. Adopt Imgproc and Geometry first: convert their operation category manifests
   to the shared TOML, preserving their 0-warning/0-gap ratchets, native Core
   dependency pins and compiled guide examples. Verify external links, overloads
   and cross-package geometry references against true native declaration anchors.
3. Adopt Core, preserving 25 generic Vector/Matrix instance summaries, real
   template/member targets and the existing large package browser.
4. Adopt MEL only after the approved source-integrity policy authorizes new
   tooling. Retain 29 packages, trailing comments, the exact unrendered Health
   metadata renaming and all 1,238 source/1,237 native section identities.
5. Verify browser navigation, keyboard focus, 390px/desktop, light/dark,
   JavaScript disabled, Back/Forward and direct bookmarks in a real browser.

No consumer migrations, source-policy changes, deployment or publication are
performed by release preparation. Shared-package release is not consumer approval.
See [release compatibility](release-compatibility.md).

## Upgrade from 0.1.0.dev0

Install the reviewed non-editable wheel in a fresh environment; verify module,
distribution and CLI versions all read `0.1.0`. Keep the old environment and
published site for rollback. Regenerate pristine native output using the same
consumer-owned compiler/GNATdoc pipeline, then enhance a disposable copy. Do not
reuse the old presentation manifest: `enhancer_version` is version-bound and
release verification rejects development manifests.

Compare every native signature/destination, guide, warning, coverage,
source-integrity and deployment baseline independently. From corrected R3
development source, presentation bytes change only in the manifest version field.
From pre-R3 source, symbol-only output also changes its router and dependent
manifest: R3 clears inherited query parameters and unsupported outer fragments
before reconstructing canonical state. R2 intentionally left that defect unfixed.
Default and incoming-instance router bytes remain unchanged. Review optional symbol/instance
configuration separately with pinned source/native evidence. Adopt only through
the consumer's own reviewed PR and rollback policy.

GNATDOC-006 demonstrates the 25 Core summaries using an explicit trusted
qualification record, separate from native declarations and dependency anchors.
Existing configurations remain unchanged; adopting consumers must independently
review and opt in to that source/native record rather than copying output metadata.
See `/home/zboll/git/ada-gnatdoc-enhancer/docs/generic-instance-summaries.md`.

GNATDOC-007 adds opt-in source-backed authored compatibility without replacing
consumer workflows. Adoption must approve the authoritative input contract,
preserve original compiled-example and source-integrity gates, and separately
qualify deployment. See
`/home/zboll/git/ada-gnatdoc-enhancer/docs/authored-guides-portal-compatibility.md`.

GNATDOC-010 adds document titles, language and charset to generated pages and
requires them on author pages. Every API page and Markdown guide hash changes;
the presentation manifest schema does not. Adopting consumers must update their
pinned revision and recorded evidence in their own reviewed change. See
`/home/zboll/git/ada-gnatdoc-enhancer/docs/html-page-metadata.md`.
