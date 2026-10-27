# GNATDOC-017 qualification record

## Independent baseline (before implementation, 2026-10-26)

Enhancer main `dd100f026e13cdd9e97b283d50130241d71bdb9d`, tree
`2873e5f7e0c200ec24a6706610d3bc0527303a7d`; fetched remote heads matched.
No existing 017 branch or PR was found. Original worktree is unchanged.
Core main `33a2a4f3b83606a5c779b8a93abeb6c91fa49a21` is independently cloned,
detached and read-only. Builds execute only in disposable copies.

Official v0.1.1 wheel downloaded from the unchanged GitHub release:
`8b896683a65623a7e7d626701a4cd68c8b89cb65792f9ffd5525bfa8cfa257ab`.
Installed non-editably into a fresh Python 3.11 environment with pinned guides
dependencies. All 579 existing tests passed (207.819s, no skips).

Core's production script completed using Alire 2.1.1, GNAT 16.1.0,
GPRbuild 26.0.1 and GNATdoc 26.0.0 (20260415), native OpenCV 4.10.0.
A separate pristine GNATdoc invocation used the same built project. Warning
comparison: zero added/removed. Independently generated source/native-bound
generic and authored qualification records enabled existing toolkit features.
Both pipelines: 195 packages, 1,293 snippets, 25 summaries, 102 summary links,
202 HTML pages. Shared publication: 207 files, 2,516 type links. Legacy:
2,755 type links. This **pre-existing link-policy difference is not a CSS
capability gap** and must not be silently repaired by this presentation task.
Shared native preservation passed for all 196 API pages. Landing page, all
five guides and separate guide CSS are byte-identical to legacy output.

Core theme SHA-256, independently read from pinned Git source and checkout:
`fa265d63e73436a6a449fd16011c3db68a5430e7fa6a98ea8eb0fd6821dca9b2`.
The default bundled CSS lacks `.landing`, `.eyebrow`, `.lead`, `.api-button`,
`.landing nav`, full summary borders/padding/headings and Core's palette and
responsive rules. These are missing **rules**, not missing navigation, guide
or instance functionality. Core and shared summaries already use the same card
class; existing intentional shared prose adds instance identity and ownership
clarification. Shared API navigation/metadata differ intentionally from legacy.

Real Chromium 156.0.8078.47, served over local HTTP with no interception,
captured computed properties for all six landing selectors at 1280/390px,
light/dark, and full-page screenshots of both sites before implementation.
Raw acquisition, source/native/output inventories, scripts, logs and PNGs are
retained outside the source archive at `/home/zboll/gnatdoc-017-evidence`.
Baseline harness attempts were retained separately: tuple-to-contract mapping,
missing copied README and read-only copied-file overwrite were harness errors,
not claimed product failures or successful qualifications.

## Disposition

`HOSTED_CI_PENDING`: local mandatory gates described below passed; exact-final-head
hosted CI must still finish successfully before independent-review readiness.
No release, tag, deployment or consumer edit is authorized. This record is not
a `READY_FOR_INDEPENDENT_REVIEW` claim. Three additional pre-existing qualified
Size links and shared navigation/prose differences require independent review,
not silent consumer adoption approval.

## Implementation qualification in progress

Thirty focused regressions were added; the full source run passed 609 tests,
zero failures/errors/skips. Defaults still select the bundled asset. Custom
mode validates both fields, exact original UTF-8 CSS/hash, lexical paths and
symlinks, loaded TOML bytes and their selected CSS identity. Only custom mode
adds `theme_source`; verification reconstructs CSS from source/configuration,
not that metadata. Rehashed output metadata cannot approve a modified asset.
The shared CSS rejection policy additionally rejects encoding directives,
controls, string-form image resources, `src()` and legacy executable filters.
No HTML/JavaScript/default-asset bytes were edited.

Two fresh Core candidate builds and idempotence passed; the only changed files
versus matching default output are CSS and presentation metadata. All 196 native
API pages, 1,293 declarations/profiles, 195 packages, 25 summary anchors and 102
summary destinations remain intact; authored output is byte-identical to legacy.

The first real-browser campaign passed all 16 site/profile combinations
(legacy/candidate × 1280/390 × light/dark × JS on/off), retaining 88 PNGs.
Computed properties match for landing/heading/eyebrow/lead/button/nav, guides,
summary cards/tables, declarations and sidebar containers. Keyboard focus,
direct native type fragments, reload/history, scrollable signatures and page
overflow were checked. No missing resources, unexpected requests or page errors.
Source-config-approved CSS bytes were fetched and hashed independently. A further
campaign exercises all 25 summaries/102 destination links and contrast.

### Source/native baseline reconciliation (not a new capability)

Separately enabling existing `generic_instances.incoming_references = true`
restores 242 instance-member references: shared 2,758 vs legacy 2,755. An
independent audit using unchanged current Core source/native oracles finds no
missing legacy type destinations; the three additional references are qualified
`OpenCV.Size` links in page
`6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html`.
There are 216 source/native-owned public type/subtype symbols (not the historical
215). Symbol parity and all 1,293 native section profiles pass. Thus the initial
239-link count deficit comprises a disabled existing 242-reference capability
and three pre-existing extra qualified links, **not a theme capability gap**.
Both incoming-default/custom builds again differ only in CSS and presentation
metadata. Current symbol/reload/history browser regressions also passed at both
widths. This does not claim identical legacy/shared navigation markup or prose.

## Completed final-source local gates

Implementation commit `cef6010701de0ef9e3e7001c72bec8fc53de98e4`, tree
`7f3bfe28f3ffaa7600867aaf37b094b9d458c2bb`. The qualification source was a clean
`git archive` of that identity, **not** a build from a changing worktree.
Subsequent evidence-only commits must retain identical modules, assets, tests,
documentation and archive inputs; evidence is excluded from distributions.
`candidate-provenance.json` binds complete source and distribution identities.

All **nine** Python 3.11/3.12/3.13 × source/non-editable wheel/extracted-sdist
rebuilt-wheel environments passed **609 distinct tests each**, zero failures,
errors or skips. All 579 baseline test IDs remain (`test-retention.json`).
Four-profile conformance, installed CLI/assets smoke, dependency checks,
`twine check --strict`, complete archive membership/path/metadata audits and
source/wheel/sdist/rebuilt module and asset equality passed. No consumer CSS is
packaged; core runtime dependencies remain empty. Both genuine current Core
custom profiles also passed all nine installed CLI `verify` reconstructions
(`installed-core-verification.json`). An earlier worktree matrix also passed,
but final claims use the repeated clean committed-source matrix.

Official v0.1.1 / final installed candidate default publications are **exactly
byte-identical including presentation manifests**, with no version normalization.
Twenty profiles: current Core symbol/incoming; historical Core current/0.5.0
package/symbol/incoming; MEL package/symbol; authentic authored Core, Imgproc,
Geometry and MEL; four synthetic conformance profiles; authentic four-package
Features Markdown site; read-only Imgproc PR #81 operation profile (329 snippets,
350 local / 586 external links). Full per-file hashes/module identities are in
`default-parity.json`, `extra-default-parity.json` and final replay records.
The retained historical fixtures are replay evidence, not fresh Ada compilation
of all consumers. Only current Core was freshly compiled/generated here.

Fresh native generation repeated with exact byte identity; the complete legacy
production build also repeated with exact identity. Core warnings: zero, no
baseline delta. Shared custom two-copy determinism and enhancement idempotence
passed. Source/native/anchor/summary inventories are unchanged by theme selection.

`browser-full.json` records **16** real Chromium combinations, **5,492** observed
page requests, all 25 summaries and 102 summary destinations in every combination,
all five guides and independently fetched approved CSS bytes. No request
interception, stylesheet/resource failures, unexpected requests or page errors.
Computed properties match for all required supported design elements. Landing
eyebrow/lead/button contrast exceeds 4.5:1 in both palettes; focus is visible,
tables scroll in their own containers and no page overflows horizontally.
Representative legacy/candidate PNG pairs are committed; `screenshots.json`
indexes all 176 full first/final-campaign PNGs retained externally (about 202 MiB).
Mobile identifiers wrap inside their card cells as Core's original CSS specifies;
no patch to source-owned CSS or HTML was made. Source declaration overflow stays
inside scrollable code blocks. Screenshots are review aids, not the parity oracle.

`occurrences.json` independently reconciles all 242 incoming instance links at
decoded native type-mark offsets, reconstructs every summary and all template
destinations, and explains the three qualified Size additions through source
scope rather than comparing aggregate counters alone. Supplementary incoming
browser evidence records 421 real clicks across eight width/palette/JS profiles,
including all 242 source-owned occurrences in the desktop/light/JS campaign,
all 25 targets elsewhere, reload/Back/Forward and native-symbol exclusions.
An inherited favicon-intercepting first
attempt was explicitly discarded, followed by a console-classification harness
failure; neither is used as live-site proof. The accepted rerun makes no intercepted
requests (only ignores Chromium's automatic, non-publication favicon 404 console
message by its exact URL). Delayed-request synthetic race checks were excluded.

## Review/reproduction boundaries

PR: https://github.com/zackboll/ada-gnatdoc-enhancer/pull/18, non-draft, open,
unmerged, auto-merge disabled. No Core, Imgproc PR #81 or other consumer writes.
Official v0.1.1 tag/release assets preserved. Version is still 0.1.1; future
maintenance release consideration requires separate review/authorization.

Reproduce the source/distribution matrix with the retained
`qualify_distributions.py --workspace /absolute/new-workspace --source
/absolute/clean-source`. It requires the three supported Python executables,
Node.js and build tools, and fetches build/test dependencies (not runtime theme
resources). Reproduce browser qualification with the committed
`tests/custom_theme_browser.cjs`, `PLAYWRIGHT_MODULE`, `CHROME`,
`THEME_SITE_ROOT=http://127.0.0.1:8170`, `THEME_CANDIDATE=incoming-custom` and a new
`THEME_EVIDENCE` directory serving qualified legacy/candidate output directories.
Acquisition/pilot scripts retain their original absolute evidence paths; adapt
only workspace paths and independently recheck pins/hashes before replay.

No screen-reader, cross-platform or non-Chromium certification is claimed.
Source-hash equality is not evidence of compiled guide-fence examples. No live
production deployment was changed or authorized. Publication metadata remains
an unsigned check, not protection against simultaneous replacement of every
independently trusted source/configuration input. See the configuration security
and fresh-build rollback contract before consumer approval.