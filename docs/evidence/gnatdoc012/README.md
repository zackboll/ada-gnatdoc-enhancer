# GNATDOC-012 evidence interpretation

Candidate source commit: `508c2bf1feb3087242496f0925964f400b551f4c`.
Candidate source tree: `5ca72a7e2f242d9a9f5deec642d45e0f2d2490f6`.
Starting main: `697d4ca91dc81812e501e501c9766d9b3ec88924`.

`baseline-inventory.json` records baseline/PR verification and metadata review.
`content-audit.json`, `distribution-members.json` and
`installed-content-identities.json` record complete archive and installed content
identities, dependencies and artifact hashes. The separately built compressed
wheel archives differ in SHA-256; their modules/assets match source exactly.
`distribution-audit-negative-controls.json` observes and rejects five malformed
wheel controls (missing/changed assets, unexpected runtime dependency, absolute
metadata path, generated file). `/tmp` examples in README metadata are intentional
documentation, not workstation metadata headers. Strict Twine validation passes.

The build used a clean `git archive` snapshot, not ignored checkout build copies.
The initial audit incorrectly interpreted documented `/tmp` examples in the
README body as build-machine metadata. Commit `508c2bf` narrows that check to
metadata headers; an absolute-path header negative control still fails. Final
candidate artifacts were rebuilt and all checks rerun after that correction.
The older hosted run on `d60cf1a` is superseded, not readiness evidence.

## Campaigns

* `baseline-540-tests.log`: unchanged starting suite, 540 passing tests.
* `wheel-3.*-tests.log`, `sdist-3.*-tests.log`: 543 tests per installed
  distribution per supported Python, outside checkout, no editable installation.
* `source-3.13-tests.log`: complete candidate-source suite.
* Six smoke JSON files: CLI help/version, all four conformance profiles,
  enhancement, verify, safety rejection, assets, determinism/idempotence.
* `core-only-*`: CLI and four synthetic profiles with no guide dependencies.
* `compileall.json`: source syntax checked on all three supported Pythons.
* `retained-input-verification.json`: both real Core acquisitions verified before
  reuse: 392 source-file hashes and 197 pristine-file hashes per revision, plus
  exact Git pins and clean consumer source/oracle paths. No new Ada build or
  GNATdoc generation is claimed. Consumer repositories are read-only inputs.
* `core-*-native-audit-summary.json`, `core-*-occurrence-summary.json` and
  `real-core-results.json`: fresh unchanged-consumer independent oracles, exact
  R1 occurrence-ledger equality, native signatures/destinations, source/guide
  preservation, two-copy determinism and byte-idempotence. Full occurrence
  details are already preserved unchanged in GNATDOC-011R1; do not duplicate them.
* `sdist-core-*-verify.json`: rebuilt-sdist installation verifies both full sites.
* `parity-input-identity-verification.json`: starting implementation reconstructs
  the six retained input profiles to exactly the approved R2 hash inventories.
  A later MEL stored publication had three stale bytes/hashes relative to R2;
  it was **not** trusted as the comparison oracle. Its retained pristine and
  configuration reconstruct exactly to R2 before reuse.
* `default-symbol-only-parity.json`: complete candidate publication comparison
  against separately imported starting implementation. The only normalization
  is `enhancer_version` in the manifest; every other byte is preserved.
* `core-*-symbol_bookmarks.*`: 144 native-symbol browser traces per revision.
* `core-*-instance_references.*`: 421 traces per revision, including actual clicks
  on all 242 incoming occurrences plus representative width/theme/JS variations.
* `core-*-instance_canonicalization.*`: additive R2 regression, 216 traces per
  revision, malformed/duplicate/conflicting query and hash inputs, clean fallback,
  valid symbols/summaries, reload/history and native JavaScript-disabled links.
* `tamper.*`: observed real-site/source/qualification/installed-code mutations,
  rejection and complete restoration; the JSON identifies each detecting layer.
* `historical-evidence-sha256.json`: 154 unchanged GNATDOC-011/R1/R2 evidence files.
* `toolchain.json`: Python/build/backend/renderer/browser-related provenance.
* `qualification-summary.json`: machine-readable gates and honest exclusions.

The orchestration scripts in this directory record exact local invocations and
absolute retained-input locations for audit. They are evidence, not portable
public CLI commands or runtime dependencies. Use shipped scripts and independently
acquired pinned inputs on another machine; do not assume these local paths exist.

## Source/CI identity and exclusions

Local candidate artifact hashes identify the source commit above, before evidence
was written. Later evidence-only commits do not change package/build/test inputs;
that relationship is checked and recorded. Hosted CI on the **final submitted
head** separately builds, audits and qualifies its own exact artifacts, retained
as per-Python workflow artifacts. Final SHA/tree and hosted URLs/conclusions are
recorded on PR #14, avoiding a self-referential source hash inside its own commit.

No full fresh four-consumer Ada/native-generation, deployment, comprehensive
coverage/source-policy migration, non-Chromium or accessibility campaign is
claimed. Other consumers use exact retained output/structural evidence, not
new migration certificates. Symbol-only URL canonicalization debt remains;
default and symbol-only routers are byte-identical to the starting source.
No consumer changes, tag, release, registry publication, merge or auto-merge.