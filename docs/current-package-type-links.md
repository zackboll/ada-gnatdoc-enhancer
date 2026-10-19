# GNATDOC-009B — source-verified current-package type hyperlinks

## Defect and bounded correction

The same-base comparison starts at enhancer merge
`23cf51d3765e7b3f68411e25a57f52f4c0efc7e1`, tree
`6cb4e25a99a2ae7930f62b4cc9f45cc13a37097c`. PR #10's post-merge run
39189495819 completed successfully on attempt 1. This base already includes
PR #11's ordinary-subtype correction and PR #10's final metadata/RCDATA
regressions. Neither is attributed to this change.

Before this correction, `Image.Attitude_Rate` inside `AMS.MEL.IR.Image`
remains plain: the dotted-name resolver requires a full current/ancestor owner
or an explicitly imported owner. The subtype fix adds a *candidate context*,
not relative owner resolution, and therefore does not repair these links.

The new rule supports exactly `Final_Package_Identifier.Public_Type` in that
same ordinary public package. Its only candidate is the current full package
identity plus the selector. It requires the source-owned package object,
matching full source header, public type/subtype inventory, public source type
declaration, and an existing uniquely reconciled native destination. There is
no suffix search, imported short-owner inference, or external fallback.

The existing raw-snippet extractor still supplies candidates. An additional
guard for this newly supported form rejects attribute subtype indications,
defaults, constraints, aspects, and expression-like colon contexts. A complete
qualified type spelling produces one anchor; casing, escaped text and decoded
offsets are preserved. Old fully qualified and unqualified paths are unchanged.

## Actual short-prefix proof

`Package.declarations` omits objects. The existing full-owner scope guard can
inspect `ams` instead of `image`. Neither suffices for this correction.

The new immutable-source guard masks comments, strings and character literals,
checks the ordinary public header, rejects generic contexts and public nested,
renamed, generic, task/protected or executable scopes, and scans **every token
occurrence of the actual final package identifier** in the public source. Any
bare use disqualifies this relative rule for the package, even an otherwise
harmless nondefining use. Only selected-name positions survive. Thus object,
type/subtype, subprogram, enumeration literal, formal, component and discriminant
definitions cannot hide from the guard through same-line layout, comments or
comma-separated defining-name lists. Private-part detection is not line-start
only; `private;` in a public partial view is distinguished from the private part.
The selector must also be declared in that public region. This is deliberately
more restrictive than Ada semantics, not a general semantic front end.
Derived public types are declined because inherited defining names need not
appear explicitly in this source. Partial private views with aspects are also
declined rather than mistaking `private with` for the private-part boundary.

Reference: Ada AARM 4.1.3 (selected components/expanded names: prefix denotes
a package, selector denotes a declaration visible within it) and 8.3 (direct
visibility and hiding; notably paragraphs 2–5 and the homograph hiding rules).
The supplied adaic.org URLs returned HTTP 403 during this campaign; the
published community mirror was consulted at
<https://ada-lang.io/docs/arm/AA-4/AA-4.1/> and
<https://ada-lang.io/docs/arm/AA-8/AA-8.3/>. The mirror warns its output is not
verified; this implementation claims only the conservative subset above.

## Immutable MEL authority and occurrence census

Consumer revision: actual PR #117 merge
`a5484514cfae3b7bccde078118b838fa40ce4d0e`, tree
`e8c845e0c3755eda0456094c4c86038114acc409`. Original source blobs:

| File under `ada/src` | Git blob |
|---|---|
| `ams-mel-ir-image.ads` | `a4cee5568cb010f85f4c50e3a217ffd449985459` |
| `ams-mel-ir-instrumentation.ads` | `c1413d5b889d56ff2fa05714efa82978ac200b16` |
| `ams-mel-status.ads` | `dbbac97a029b9e6b4edc9f6f022cfbe6659c41c0` |

The native ledger blob is `bcd145d95d14fb2bf75c1a250311cc5f19654a66`.
Unchanged consumer trusted-input qualification authenticates all source,
ledger, DOC-007E configuration and 39 pristine native/portal files. It is **not**
consumer acceptance of the candidate publication.

| Package | Containing declaration.component | Source mark | Line |
|---|---|---|---:|
| Image | Sensor_Inertial_State.Uncertainty | Image.Uncertainty | 98 |
| Image | Sensor_Nav_State.Orientation | Image.Orientation | 122 |
| Image | Sensor_Nav_State.Orientation_Velocity | Image.Orientation | 124 |
| Image | Sensor_Nav_State.Orientation_Acceleration | Image.Orientation | 126 |
| Image | Sensor_Nav_State.Coordinate_System | Image.Coordinate_System | 128 |
| Image | Navigation_Report.Attitude_Rate | Image.Attitude_Rate | 666 |
| Image | Navigation_Report.Position_Velocity_Covariance | Image.Position_Velocity_Covariance | 672 |
| Instrumentation | Instrumentation_Level_Command.Priority | Instrumentation.Priority | 87 |
| Instrumentation | Instrumentation_Report.Priority | Instrumentation.Priority | 98 |

Every target belongs to the same full source package. The user's two links use
native Image page
`1227ecb7e9dafa3f2bb5afc47ffd547c851f2fc8202385479135994de7b16763.html`
and anchors `000c90c6e32939281ba36b0309023f11111c09b027dfcb5acf7f6fcbde859f17`
and `05b10691e1d32ec5c7b89999581889463e7f301b8a02667d19965f88e7c1b1d6`.
No replacement anchors are generated.

Navigation_Report changes from four to six local links. The existing State,
Status.Euler, Speed and Acceleration destinations remain exact, including both
Image North_East_Down uses. Long_Float and Long_Long_Integer stay plain.

## Independent output and regression qualification

The new oracle does not import `resolve`, call `type_positions`, or trust
candidate manifests/counters. It uses the unchanged pinned consumer declaration
inventory/native ledger, independent token contexts and source alignment, and
an explicit source-owned nine-occurrence census. Its short-scope proof is a
separate token walk. The production consumer auditor is neither modified nor
monkeypatched; its current acceptance boundary remains deferred.

Two fresh baseline/candidate publications establish **1,419 → 1,428** local
type links, **2,966 → 2,975** complete references, zero external type links,
42 files / 37 HTML pages / 29 packages. Only Image, Instrumentation and
`api/presentation.json` change; the other 39 complete files are byte-identical.
All prior occurrences and destinations are checked against independent source
expectations, not merely retained because the candidate says so.

Complete expected enhanced pages are reconstructed from baseline bytes and the
nine independent occurrences. Each new anchor absorbs its old highlighted dot
span. The three identical Orientation spellings are accounted for separately.
Exact pristine entity restoration is checked separately from complete enhanced
page and UTF-8 presentation-manifest reconstruction. Types-off control compares
complete publications. Fresh-copy determinism, enhanced idempotence and dry-run
input/output preservation are separate checks.

Retained pinned full Core (`c5545eee815431568495c6c76af83df56cf5c3dd`),
Imgproc (`9ce22ae5ab70008e1147475a9e6d7baef82f1df0`) and Geometry
(`fa81e5140cbebf2aa41397a40c08ba194a5f6f73`) have independently empty eligible
short-prefix censuses and complete baseline/candidate publication equality.
This is fresh full real-site qualification, distinct from synthetic and reduced
hosted fixtures. It is not a new native/Ada compiler qualification campaign.

The 471 retained tests (including all 23 subtype-base regressions and final
metadata/RCDATA cases) remain unchanged. This task adds 35 distinct tests:
25 source/rendering regressions and 10 independent-oracle controls, of which
nine reject mutations. Full discovery totals **506**, not the sum of repeated
focused/distribution executions. Real-publication mutations additionally reject
wrong existing anchors/pages, consistently forged identities/destinations,
updated output hashes, missing/extra links and changed prior destinations.

The unchanged workflow qualifies Python 3.11/3.12/3.13, clean non-editable wheels,
sdist-rebuilt wheels, installed assets, synthetic conformance and authentic
reduced CLI fixtures. Actual final frozen-tree local/distribution/browser and
final-head hosted results, fingerprints and checkout identities are recorded in
the PR and external handoff; this document cannot contain its own commit hash.
The existing manifest already ships all new Python/JSON/Ada/Markdown files;
no packaging/dependency/version policy changes are needed.

## Reproduction and evidence

Use absolute fresh external destinations; the harness rejects existing or
overlapping workspace paths. Install the baseline and proposed frozen tree
non-editably in separate environments, then run:

```sh
/absolute/candidate-env/bin/python /absolute/enhancer/scripts/qualify_current_package_type_links.py \
  --source-root /absolute/pinned-mel-input --pristine /absolute/authenticated-pristine \
  --workspace /absolute/fresh-external-audit \
  --baseline-python /absolute/base-env/bin/python \
  --candidate-python /absolute/candidate-env/bin/python
/absolute/browser-env/bin/python /absolute/enhancer/scripts/qualify_current_package_browser.py \
  --workspace /absolute/fresh-external-audit --output /absolute/fresh-external-browser
```

The browser harness uses authenticated candidate bytes with Chromium across
root/project-prefix hosting, desktop/mobile, light/dark, JavaScript on/off.
It exercises all nine new occurrences and the four retained Navigation_Report
links, actual destination content/fragments, reload, Back/Forward, keyboard
focus, mobile scrolling, native literal coloring and console errors. Ordinary
non-sidebar links retain the existing outer-history boundary. Pristine MEL
declarations contain no comment/character tokens; synthetic regression tests
exercise those lexical classes. No cross-browser or comprehensive accessibility
certification is claimed.

Bulky logs/sites/distributions/screenshots and complete ledgers stay at
`/home/zboll/git/ada-gnatdoc-enhancer-009b-evidence/r1`.
Compact source/native occurrence evidence is under `docs/evidence/gnatdoc009b`.
All development failures remain external: initial whole-portal CLI rejection
(existing API-only composition procedure required); a reduced fixture initially
omitting the original Status context clause; oracle subtype eligibility omitted
the old flat-scope guard; repeated Orientation punctuation reconstruction needed
occurrence counting; manifest serialization needed `ensure_ascii=False`; and a
browser coloring assertion initially sampled Image for string tokens that occur
only on other authentic pages. A fresh Python-version run detected import-created
bytecode cache files in the isolated input tree; the harness now disables bytecode
writes before reading consumer inventory. Timed-out foreground attempts are incomplete,
not passing executions; completed fresh background executions are recorded.

## Limitations and deferred consumer work

No arbitrary shortened ancestors/siblings, imported short names, aliases,
renamings, generic instances, ambiguous/nested scopes, expressions or external
fallback are newly supported. `IR.Channel.View` and alias-dependent
`Status.MFA_Status` are not expanded by this task. Conservative whole-public-unit
bare-name rejection may decline semantically safe occurrences.

This upstream remedy is **proposed for independent review**, not production
adoption. MEL's repository and production pin
`53a321915da2c5a02a54581040673b61f8595b25` remain unchanged. Its independent
auditor also needs separately reviewed treatment for these short owners and the
already merged subtype/metadata behavior. Consumer integration is the next
separate task only after this upstream PR is independently reviewed and merged.
No merge, auto-merge, rebase, force-push, tag, release or deployment is authorized.