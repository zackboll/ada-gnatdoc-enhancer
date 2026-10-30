# GNATDOC-024 — v0.1.3 preparation qualification

This is release preparation only. No merge, tag, publication, deployment or
consumer migration is authorized. Final public assets must be regenerated and
audited from the eventual approved merged-main source, not assumed identical
to preparation builds.

## Source and independent baseline

Fresh GitHub fetch established main
`60e871fd4362c5fc66de5cd02a5a2bc5cc2b3e32`, tree
`ca9c3b0194dd55b673b31681e0701e7cf1d3ff24`. PR #22 head
`27341756f9a14eb7e566791e1a947bd6c8ef5dee` has that same tree; its base
`d7636cc50154ebb5535c699d2bed6406ebc92e62` is an ancestor. The required main
run is [40995880331](https://github.com/zackboll/ada-gnatdoc-enhancer/actions/runs/40995880331).
All seven jobs, including `search-browser`, must succeed; pending is not ready.

Official v0.1.2 wheel, sdist, provenance and SHA256SUMS were independently
downloaded from the GitHub release into a new directory and their published
SHA-256 checks verified. Historical v0.1.2 records and assets remain unchanged.

## Executed qualification records

**Local qualification: passed. Disposition at evidence commit:
`HOSTED_CI_PENDING` until final-head hosted CI completes.** The PR is the final
exact-head status record; this evidence cannot include its own commit hash.

The merged-main run completed successfully: all seven jobs and all their steps
passed. Complete main logs are retained as `main-hosted.log.gz`, with API job,
check-run and status records beside this file. No unexplained failures,
cancellations or incomplete main checks remain. Main was freshly re-fetched
without advancement; no v0.1.3 tag or release existed during qualification.

Machine-readable records alongside this document report actual completed
results, immutable build commit/tree and artifact hashes. Local raw logs and
disposable environments are rooted at `/tmp/gnatdoc024`; retained summaries are
not claims of fresh consumer compilation, acquisition or deployment. The final
PR records its own commit/tree and exact-head hosted CI separately to avoid
self-referential provenance.

The release adds three fail-closed output-classification tests, bringing full
discovery to **676 tests**. The nine-environment target is therefore **6,084**:
Python 3.11/3.12/3.13 × source/canonical wheel/rebuilt-sdist wheel. Mandatory
gates include no skipped tests, installed metadata/CLI/module/presentation
identity, complete shipped fixtures/tests, strict Twine, wheel RECORD hashes and
sizes, archive inventories/path/symlink safety and source/module/asset parity.

All nine environments passed **676/676 tests**, totaling **6,084**, with no
skips. `matrix.json` records results; compressed full logs retain individual
test outcomes, installed CLI/module versions and conformance/smoke results.
`content-audit.json` verifies strict archive inventories, metadata, bundled
JavaScript/CSS, wheel RECORD hashes/sizes and rebuilt-wheel content equality.
`candidate-provenance.json` binds every tracked source blob and archive member
to build commit `0439319c4dc21e17e313cf86a9a95657ae3a90f4`, tree
`8a5209bedc8bb5d7b25a5b038aa4d7063766832b`. Strict Twine passed for both archives.

`baseline-acquisition.json` records fresh official v0.1.2 acquisition, published
SHA256SUMS verification and verification of every wheel/sdist member against
the independently downloaded public provenance. `compatibility.json` records
eight complete old/new comparisons: three authentic Core router variants,
four real native sites and navigation-disabled output. `real-input-identities.json`
records revalidated original acquisition source/native hashes and consumer pins.

`search-publication.json` records independent regenerated search inventories,
native oracle/preservation, custom theme hashes and idempotence for all three
routers. `browser-search.json` passes all required queries and interactions,
seven corrupt/forged/missing index cases, three rehashed cases, no-JavaScript
fallback, zero external requests and zero runtime errors. Fresh retained desktop
light/mobile dark/guide screenshots were inspected for legibility and layout.
The four `*-real-browser.json` files each pass 48 checks (192 total).
`legacy-history-browser.json` passes 244 checks and retains 268 scrolling/history
traces. `operation-browser-with-geometry.json` passes all 144 operation/history
checks, including the multi-package Geometry extension. The synthetic browser
suite also passes both widths/themes and JavaScript-disabled fallback.

Two harness invocations initially stopped before browser checks because their
Git identity collection ran in an archive-only directory. Both were rerun
unchanged from a detached worktree at the immutable build commit and passed.
This was a working-directory correction, not a waived gate or product fix.
An in-progress GitHub log download returned 404; completed main logs were later
downloaded successfully. `qualification.json` records these resolved attempts.

## Output compatibility classification

Without `[search]`, complete regenerated output may change only the version and
the exact `Search documentation` → `Filter navigation links` API index label,
plus `output_sha256.api/index.html`. The three legacy routers retain their
bytes; no search index or stylesheet is published. Navigation-disabled output
is version-only. Every other file, manifest field and hash must match.

Opt-in search adds `api/gnatdoc-search-index.json` and `api/gnatdoc-search.css`,
composes the selected router and changes shell authorization/manifest metadata.
Independent source/native reconstruction, deterministic repeated generation,
idempotence and custom-theme byte preservation qualify those changes, not the
default-output comparator. The authentic full Core index must contain 195
packages, 215 types/subtypes, 1,047 operations and five guides (1,462 records).

The Chromium campaign covers all three router configurations, required queries,
distinct overloads and native scrolling, canonical links/history/reload/fresh
tabs, guides, keyboard, 1280/390 layouts, both themes, corrupt/missing/rehashed
caches, forged destinations/foreign frames and JavaScript-disabled native access.
It requires zero remote requests and runtime errors. Python source/native,
private/internal exclusion and mutation controls remain mandatory.

## Boundaries and disposition

Search needs explicit opt-in, static HTTP(S), JavaScript and Web Crypto SHA-256
(HTTPS or localhost); it has the scopes and bounds in
[documentation-search.md](../../documentation-search.md). Native navigation
remains available if JavaScript is disabled or cache checks fail. Linux Chromium
qualification is not cross-browser/accessibility certification. Retained pinned
native sites do not certify arbitrary new consumer revisions or fresh GNATdoc
generation. No new approval ceremony supplements the maintainer-led policy.

Use `READY_FOR_MAINTAINER_REVIEW` only after every required local and hosted gate
passes. Otherwise report `HOSTED_CI_PENDING` or `CORRECTIVE_WORK_REQUIRED`.