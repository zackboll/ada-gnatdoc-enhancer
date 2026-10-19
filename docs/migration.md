# Planned migration sequence

1. Qualify the bootstrap against **real** GNATdoc 26 output, not only the four
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
performed by this bootstrap archive.

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
