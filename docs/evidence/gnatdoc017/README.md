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

Implementation and remaining gates pending. No release, tag, deployment or
consumer edit is authorized. This record is not a readiness claim.

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