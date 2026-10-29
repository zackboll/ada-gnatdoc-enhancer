# v0.1.2 consumer compatibility and adoption boundary

GNATDOC-020 prepares, but does not publish, v0.1.2. The release retains the exact
merged GNATDOC-017/018/019 implementation. Against merged main `8527052b43af06a5fefd74428a07342022469ff3`,
only `api/presentation.json`'s `enhancer_version` may differ. Against the actual
official v0.1.1 distribution, default-router profiles additionally change
`api/gnatdoc-navigation.js` and its `output_sha256` entry. Symbol, incoming-instance
and navigation-disabled profiles permit only the version field. There is no
universal v0.1.1 byte-parity claim. New custom themes and stable external bookmarks
are compared with merged development source, not invented v0.1.1 capabilities.

Custom themes and stable external bookmarks remain opt-in, hash-bound and
source-verified. Direct fragments remain available. Without publisher JavaScript,
stable bookmarks do not promise automatic declaration selection. All upgrades
must start with pristine native GNATdoc 26.0.0 input; old v0.1.1 manifests are
version-bound and cannot be silently reused. Python 3.11–3.13, non-editable
wheel/sdist installs, Node as a test prerequisite and optional guide pins remain
unchanged. An installed toolkit does not authorize any consumer production or
Pages deployment. See [current executed gates](evidence/gnatdoc020/README.md).

## Historical v0.1.1 preparation assessment

The planned patch retains the v0.1.0 boundaries below and adds only opt-in
top-level external type navigation. Omission preserves output except for
version-bound manifest metadata. GNATDOC-014's Imgproc PR #81 evidence covers
329 declarations, 586 external occurrences / 14 Core types, 350 local links and
329 source-owned operation destinations; GNATDOC-015 must requalify the actual
installed candidate and rebuilt wheel. Historical coverage is 1,596/1,596;
retained evidence is not a fresh native generation or deployment.
See [fresh release-preparation results](evidence/gnatdoc015/README.md).
Core policy approval, authored-site parity, full consumer production browser and
security qualification, and Pages deployment remain separate. PR #81 is untouched.

Package release is not production-migration certification. Historical campaigns
remain immutable in `docs/evidence/gnatdoc002` through `gnatdoc011r3` and
`docs/evidence/gnatdoc012`; their
results apply to their exact pins, not arbitrary current consumer heads.
GNATDOC-012 changes no consumer repository or consumer-owned generator.

| Consumer | Previously completed qualification | Release assessment / first-adoption prerequisites |
| --- | --- | --- |
| OpenCV Core Ada | Native structural profiles, authored guides, 25 Vector/Matrix summaries; GNATDOC-011R1/R2 qualify current `26bf5e2e8151cb0545b928b72d3d87677543c1ae` and 0.5.0 `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`: 195 packages, 215 native symbols, 242 incoming references, 102 internal summary links; 1,282/1,268 native sections and 2,745/2,701 candidate type links respectively | Recheck retained acquisition identities and both complete publications, independent source/native audits, incoming occurrence oracle and browser routing. Preserve native symbols separately from explanatory anchors. Consumer must separately approve generator replacement, three legitimate shared `OpenCV.Size` links, guide/compiler/warning/coverage/deployment gates and rollback. |
| OpenCV Imgproc Ada | Pinned API structural qualification, source-order overload navigation/history, local and pinned external Core links, authored guides and metadata campaigns | Preserve overload ordering, exact native anchors, dependency pins, zero-warning/coverage ratchets and compiled examples. Default publication parity does not certify a new consumer head or deployment. |
| OpenCV Geometry Ada | Pinned multi-package structural and browser qualification, native declaration/type links, external Core dependencies, authored guides, subtype-base/metadata reconciliation | Keep multi-package/history behavior, external native declaration ownership and current `Contour` base link; independently qualify dependency and deployment URLs. |
| OpenCV Features Ada | Historical metadata/default-output and browser evidence only; not an established shared-package production migration | Independently pin/build source and GNATdoc 26.0.0 native output, inventory packages/declarations/overloads, review config/dependency maps and guides, establish warning/coverage/source-integrity gates, run full browser and deployment qualification before first adoption. |
| AMS GRA MEL Bridge | 29 packages, 1,238 source / 1,237 native sections; narrowly qualified Health metadata renaming exception, direct renamings/Convention omissions, 1,418 local links at the original profile pin, six HTML guides/portal; later metadata/current-package link campaigns | Preserve exact source-integrity policy and known renderer exceptions; no broad omission waiver. Revalidate guides, titles, native destinations, warning/member-coverage gates and publication policy in a separate consumer PR. |

The release campaign report distinguishes newly executed tests from historical
evidence reuse, with identity verification before reuse. Retained native output
is not a fresh Ada build or GNATdoc acquisition. Full consumer/compiler/deployment
campaigns are not replaced by reduced fixtures or the four synthetic profiles.

GNATDOC-011R3 fixes the symbol-only unknown-query/reload defect by clearing
inherited query parameters and unsupported outer fragments before reconstructing
canonical navigation state. GNATDOC-011R2 intentionally fixed only the separately
opted-in incoming-instance router. Default and incoming-instance assets retain
their approved bytes; symbol-only assets use the independently reviewed R3 bytes.
The old symbol publication is not byte-identical: its router and dependent
presentation manifest change. R3 development to corrected release changes only
the manifest version field. No consumer warning, coverage, source-integrity or
publication baseline may be silently changed for adoption.