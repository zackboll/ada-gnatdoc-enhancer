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