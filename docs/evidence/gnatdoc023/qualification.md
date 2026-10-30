# GNATDOC-023 qualification

Starting `origin/main` was independently fetched and verified as
`d7636cc50154ebb5535c699d2bed6406ebc92e62`. Branch:
`feature/023-documentation-search`. No release asset, consumer configuration,
tag, deployment, or backend service is changed.

## Original negative reproduction

The actual public-download v0.1.2 wheel, installed outside the checkout, rebuilt
the source/native-bound Core documentation. The exact original browser output
is retained in `original-failing-reproduction.json`, with before screenshots.

| Query | Released behavior | New Core behavior |
| --- | --- | --- |
| `Sparse` | 35 sidebar labels | 162 name/signature/text matches, packages first |
| `Mat` | 38 sidebar labels including tagged types | 1,201 matches; exact public `OpenCV.Core.Mat` ranks first |
| `Create` | No matching documentation | 70 matches, including three qualified Core overloads |
| `Clone` | No matching documentation | 101 matches including public operations |
| `OpenCV.Core.Mat` | One existing tagged-type link | Nine matches, exact verified public type first |
| `ownership` | No matching documentation | 65 matches; Ownership and views guide first |
| unknown | No matching documentation | Explicit no-results status; no navigation mutation |

Root cause: all three legacy scripts only compare search text against existing
sidebar-link labels. They do not read Ada declarations or guide content. No
additional released-runtime exception was observed in Chromium. `Mat` and the
qualified type were not falsely recorded as failing on this actual site: native
tagged-type links already make them partially discoverable.

The original 661 tests pass unchanged. Twelve additive search tests cover
explicit configuration, deterministic reconstruction, inventory opt-in,
private/internal/unsupported-scope exclusion, independently retained native
destinations, overloads, guide coverage, corrupt/missing/duplicate/forged indexes,
and rehashed publication metadata. Complete current Python discovery contains
673 tests. Python 3.11/3.12 full runs initially passed 672 before the final
additive rehashed-shell test; their final dedicated 12-test search runs also
pass. Python 3.13 complete discovery passes all 673. Hosted matrix repeats
complete discovery against the submitted head.

## Actual-site and browser evidence

`browser-search.json` is the dedicated Chromium run over the complete pinned
Core source/native fixture, using the existing Core custom theme, with all
three router variants at 1280/390 widths in light/dark themes. It passes:

* all required queries, partial/mixed-case queries, rapid changes, unknown and
  malicious input, clear/empty-query behavior, keyboard and focus;
* distinct `Create` overload URLs, type and operation native anchors, package
  links, declaration scrolling, canonical reload/Back/Forward/fresh tabs;
* guide top-level navigation, foreign-frame recovery, invalid native queries,
  modified result destinations, no horizontal overflow;
* seven missing/corrupt/forged cache cases plus three rehashed cache cases;
* no external requests, no browser runtime errors, no-JavaScript native access.

The index has 1,462 records: 195 packages, 215 types/subtypes, 1,047 operations,
five guides. Serialized size is 1,711,768 bytes. Match counts include descriptive
matches, not just API names; only the first 50 ranked results are rendered.
Exact source names rank above descriptive text. Each indexed declaration is
checked against the retained independent Core source/native destination oracle.

`compatibility.json` records complete independent reconstruction, determinism,
idempotence, and preservation of native content for Core, Geometry, Imgproc and
MEL. No search opt-in is added to those consumer configurations. Their only
output delta is the accurate legacy filter label and corresponding manifest
hash. The unchanged three legacy JavaScript variants retain exact bytes.

The four `*-real-browser.json` files each pass all 48 predecessor real-browser
checks. `legacy-history-browser.json` records 244 predecessor checks with zero
failures; the raw 268 geometry/history traces are retained outside the checkout.
`operation-browser.json` records 144 passing operation/overload/history checks.
The legacy synthetic browser suite also passes both widths/themes and native
JavaScript-disabled access. These tests are retained, not replaced by search.

Before/after screenshots include the exact same Core custom theme at desktop
light and mobile dark widths. Manual inspection confirmed readable result
labels, signatures, borders, visible focus, and no horizontal overflow. Mobile
results receive additional height only while search is active; clear restores
the unchanged ordinary layout. Homepage, API pages and native navigation are
not redesigned.

## Package and compatibility boundaries

`content-audit.json` records successful wheel/sdist/rebuilt-wheel content and
RECORD auditing. Strict Twine metadata validation and installed wheel/sdist CLI,
bundled assets, four-profile conformance, idempotence and verification pass.
All package builds are local candidate artifacts outside the checkout's
published-release assets. Existing package version metadata remains 0.1.2;
this branch is unreleased and is not an overwrite of published v0.1.2.

Full search requires `[search] schema_version = 1, mode = "documentation"`.
Without it, no search index/stylesheet or new router composition is published.
Version-one bounds and exclusions are documented in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/documentation-search.md`.
Unsupported generic-instance members with no native anchors, nested scopes,
constants/operators and external dependency API identities are not invented.
Static HTTP(S) operation is supported; arbitrary `file:` origins are not.

Raw local logs, candidate artifacts, retained screenshots and scratch workspaces
are under `/home/zboll/qualifications/gnatdoc023`. Hosted CI is a separate gate:
do not interpret local passing evidence as a hosted success claim. Final PR
handoff records the exact commit/tree and hosted head status separately.