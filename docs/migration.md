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

## Upgrade from 0.1.1 to the 0.1.2 candidate

Use a fresh isolated environment and the non-editable candidate wheel or a wheel
rebuilt from its independently audited sdist. Require project, module, installed
distribution, CLI and generated manifest versions to agree on `0.1.2`.

Regenerate from **pristine native GNATdoc 26.0.0 input**. Previously enhanced
v0.1.1 sites and their version-bound presentation manifests cannot be silently
reused. Keep the old environment and publication for rollback. Relative to
official v0.1.1, default navigation intentionally changes its JavaScript and
manifest runtime hash as well as `enhancer_version`; symbol, incoming-instance
and navigation-disabled profiles change only the version field. Relative to
merged GNATDOC-019 development source, only that field may differ in any profile.

Custom themes require paired source-root-relative `theme_css_source` and exact
`theme_css_sha256`, with the existing CSS/resource restrictions. Omission keeps
the bundled theme. Stable external bookmarks require explicit hash-bound
`[external_symbol_bookmarks]`, source/native/publisher approval and `_top`.
Direct-fragment mappings remain authority and remain available. Stable URLs use
canonical package-plus-symbol queries; without publisher JavaScript, automatic
declaration selection is not guaranteed. No network is used by ordinary enhancement
or verification. Do not relax the Core-v1 router fingerprint to accept HTTP success.

Requalify native declarations, guides, compiled examples, source integrity,
warning/coverage ratchets, custom styles and real browser/history behavior in a
separately reviewed consumer change. Toolkit installation is not production or
Pages approval. Synthetic `pageshow` checks are not BFCache certification.

## Historical upgrade from 0.1.0 to 0.1.1

Install the independently reviewed non-editable 0.1.1 wheel or rebuilt sdist wheel
in a new environment. Require module, distribution, CLI and regenerated manifest
versions to equal `0.1.1`. Regenerate from equivalent pristine native input; old
version-bound presentation manifests are intentionally rejected. With the new
option omitted, only the manifest version may differ from the official v0.1.0
output. Keep the old installation/site for rollback.

To opt in, add `external_type_target = "_top"` under `[presentation]`. Only
already source-verified, host-authorized external type links receive the target;
local and generic-instance links do not. No script or asset migration is needed.
Imgproc must separately approve Core policy, authored-site parity, its full
production browser/security campaign and Pages deployment in its own PR #81.
Toolkit preparation neither modifies that PR nor authorizes publication.

## Historical upgrade from 0.1.0.dev0 to 0.1.0

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
