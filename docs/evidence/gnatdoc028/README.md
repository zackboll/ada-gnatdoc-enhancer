# GNATDOC-028 — v0.1.4 preparation (not published)

## Scope and authorities

One release-preparation PR only. No tag, release, package publication, consumer
modification, deployment or merge is authorized. All candidate provenance uses
`publication_authorized = false`. Public assets must later be rebuilt and
qualified from the exact approved merged-main commit/tree.

Fresh fetch verified base `6c448f6bcd99ca47fd9b54444cb26d91f71fdc13`, tree
`d0766f709db2623a9b1ed3f1f1a9f292f8cf2804`, equal to reviewed PR #24 head
`fc1eb1d434b02c3792c79d9059b2635afd233782` tree. Published v0.1.3 is commit
`ce117aedc7eeb8c45aafc07dea9357166caadf0d`, tree
`e87c8500165c119753843f71e34868b7133523d1`; freshly downloaded wheel, sdist,
provenance and checksum-file bytes match all four independently approved hashes.

`version-authorities.json` classifies every base-tree 0.1.3 occurrence. Current
metadata, module, archive/provenance audits, CLI/installed assertions and release
contracts advance to 0.1.4. Negative controls reject 0.1.3. Historical evidence,
published assets, 012/013 comparator/tests and official baseline CI pins remain
unchanged. Documentation describes preparation, never publication.

## Qualification contract

The new `compare_release_013_014.py` permits only exact serialized manifest
version replacement. Every other file and byte, including search index, router,
CSS, guides, native identities and API destinations, must match. Historical
012/013 acceptance is neither replaced nor weakened. Feature-on additions are
scoped CSS and source-preserving authored/landing markup; native pages, existing
CSS and search bytes remain untouched. Create/Clone overloads and unsupported
semantic inference remain deliberately unlinked.

Keep historical Core 195 packages / 215 symbols / 1,047 operations / five guides
= 1,462 records separate from current Core 195 / 216 / 1,071 / five = 1,487.
Current consumer pin: `9bf0cb7311bf5b02344ddb99ee2379744c24e99b`, tree
`e4b97f79449b46a0ebd993095d08ee76286146a1`. Its approved native acquisition is
revalidated against its hash-bound authored manifest; public staging mirrors its
pinned `stage_gnatdoc_sources.py` (exact src/*.ads, excluding separate internal
project). No consumer repository is written. Reuse of qualified native bytes is
not a fresh Ada/compiler/GNATdoc build or deployment certification.

## Results and final-head record

Executed qualification:

| Python | Source | Installed wheel | Rebuilt sdist wheel |
| --- | ---: | ---: | ---: |
| 3.11 | 703 passed | 703 passed | 703 passed |
| 3.12 | 703 passed | 703 passed | 703 passed |
| 3.13 | 703 passed | 703 passed | 703 passed |

**6,327 tests; zero failures, errors or skips.** Full discovery includes original
and new release, lexer/resolver, rehashed forged-link/markup, archive/path/symlink,
search/browser-security mutation tests. All nine environments run CLI/version,
compile and four-profile conformance; installed environments run outside source.
Strict Twine, complete archive inventories, module/assets, RECORD hashes/sizes,
SPDX/license/Python/dependency metadata and rebuilt-wheel content audits pass.
`core-only.txt` and conformance prove operation without Markdown installed; guide
extras remain markdown-it-py==3.0.0 and mdurl==0.1.2.

All five authored fixture official differentials pass (Core 207 files, Core search
209, Imgproc 13, Geometry 14, MEL 42), with only manifest version changed.
Four complete historical real-site differentials independently revalidate retained
source/native hashes and native preservation: Core 195 packages/1,268 sections,
Imgproc 1/314, Geometry 2/130, MEL 29/1,237 plus its one narrow approved exception.
These are pinned acquisitions, not new consumer compiler/deployment campaigns.
All 21 authentic authored guides retain reference byte parity through the suite.

Current Core source/native comparison independently passes 1,487 records with
source/native-approved destinations. Both feature-off and feature-on search-index
bytes equal official-wheel output. Native API/CSS/router bytes remain unchanged;
feature-on adds only assets/gnatdoc-examples.css and changes homepage, five guides
and dependent manifest. Independent feature-on reconstruction and idempotence pass.
Historical Core still preserves all 1,462 records and index bytes.

Chromium passes the original **24 feature-on cases and 24 feature-off screenshot
comparisons**, plus the same 24+24 against current Core. Both use 1280×900/390×900,
light/dark, JavaScript on/off, exact decoded code, real selection/clipboard, native
link keyboard focus/navigation/unique declaration anchors, mobile overflow and
zero runtime errors/external requests. Eight supplemental synthetic browser cases
cover all seven token categories, including character literals absent from the
selected authentic guide pages; they do not substitute for authentic controls.
Historical and current search Chromium each pass all three router variants,
queries/overloads, navigation/reload/back/forward, JS-disabled fallback, seven
index and three rehashed-index mutation controls with no runtime/external errors.
Four real-site browsers pass 48 checks each. Legacy visibility/history passes
244 controls with zero failures across 24 desktop/mobile/theme/JS contexts;
screenshots are committed; large traces remain locally retained with exact
hashes in local-browser-trace-inventory.json (not durable hosted artifacts).
Synthetic pageshow is not claimed as actual
bfcache proof. Operation/profile/Geometry browser qualification passes another
144 controls; its structured source/profile/history results are retained.

Build source is immutable commit `ea8ca4aed76676a4e1e9bfa4f1993285158a811b`,
tree `9eb78e7bc26d4e820cf4affcfdfae988a6eacb61`. Candidate files are retained under
`candidates/`, with exact hashes in `candidate-SHA256SUMS` and member/source
identities in `candidate-provenance.json`. Compression bytes differ from the
rebuilt wheel; complete installed content matches. Provenance is qualification,
not publication authorization. Later evidence-only changes do not change tested
runtime/scripts/tests/packaging inputs; `post-test-source-integrity.json` checks
that boundary. Final public archives must be rebuilt from approved merged main.

Merged-main CI run 41220092687 completed successfully with all eight jobs on the
verified predecessor commit, including both browser jobs; full log and API records
are retained. **Disposition at evidence commit: HOSTED_CI_PENDING** until its own
exact-head hosted qualification completes; the PR is the final status record.

Incomplete merged-main CI is
`MAIN_CI_PENDING`; no prior PR-head run substitutes for merged-main success.
The PR body records final HEAD/tree and exact-head hosted CI separately to avoid
self-referential provenance. Build-source identities identify actual immutable
snapshots, never a guessed final evidence commit. Failed mandatory gates block
readiness; no skip or failure waiver is authorized.
