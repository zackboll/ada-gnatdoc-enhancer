# GNATDOC-009A: ordinary subtype-base type links

## Status and identities

This is a shared-tool correction, not a consumer integration or publication
migration. Geometry PR #48 and its original blocked evidence remain unchanged.
The starting shared main is `53a321915da2c5a02a54581040673b61f8595b25`, the
two-parent merge of GNATDOC-008B (PR #9). The isolated installed baseline passed
all **392 tests** before implementation and reproduced the missing occurrence.
The implementation revision is `588bc837484d338af7d2e90fcdc6df63f37f4c57`;
subsequent evidence/harness commits do not alter the runtime implementation.
Final exact-head hosted results belong to PR #11 and its qualification record.

| Input | Immutable identity |
| --- | --- |
| Geometry source | `8690927853ffa74729206d8997b09046ad3d2246` |
| Unchanged Geometry blocked PR | `12e6b8549dd1859aab1526be9bf778e0da60d7f0` |
| Core 0.5.0 source/native dependency | `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` |
| Documentation-only Core router fixture, **not** dependency | `ccc2190f9bf0712d65a2b9d2983cde7ce68b4bae` |
| Historical Core consumer | `c5545eee815431568495c6c76af83df56cf5c3dd` |
| Historical Imgproc consumer | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` |
| Historical Geometry consumer | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` |
| Historical MEL consumer | `6065129aba5dee89e70b61e05a9e1c9b2c3061c0` |

## Narrow correction

The baseline returned `[]` for the real declaration at Geometry source line 76:

```ada
subtype Contour is OpenCV.Point_Array;
```

It now returns exactly `[(19, 37, "OpenCV.Point_Array")]`. A separate
`SUBTYPE_BASE` pattern is anchored at the beginning of a declaration snippet
and requires `subtype Identifier is Qualified_Name`, followed by a semicolon,
constraint parenthesis or `range`. `mask_ada` preserves character offsets while
masking comments, strings and character literals. The existing generic
`TYPE_MARK` pattern is **unchanged**: arbitrary `is Identifier` is not authorized.

The matcher discovers only a candidate. `linked` continues to call `resolve`
with source-owned types, local precedence and explicit external identities.
New subtype-base candidates also reuse the existing flat public-scope guard,
including for local types, so nested/aliased/executable scopes cannot gain new
authority merely because a snippet starts with `subtype`.

Unsupported null exclusions and attribute subtype indications remain unguessed.
Constraints and default values do not become new typed contexts. Ordinary
derived types retain their previous behavior. No native filenames or anchors
are computed from Ada names. Resolver, dependency, inventory, native-profile,
publication-integrity, highlighting and operation-history implementations are
unchanged.

## Independent Core destination proof

The actual Core 0.5.0 public `src/opencv.ads` declares `Point_Array` at line 81:

```ada
type Point_Array is array (Natural range <>) of Point;
```

Its actual native page and fragment, independently reconciled against that
complete source declaration, are:

```text
ea2ebcbc108269c77d7c6d44d2dabdfb5f6d0179ad5622b1be3cbceaee5c44aa.html
#da696e09a1f1b297516365244e16533e23cca626f26df4bb3f727a64beb697b0
```

The corrected full Geometry reference targets exactly:

```text
https://core.invalid/f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f/api/ea2ebcbc108269c77d7c6d44d2dabdfb5f6d0179ad5622b1be3cbceaee5c44aa.html#da696e09a1f1b297516365244e16533e23cca626f26df4bb3f727a64beb697b0
```

This is exclusively `offline-test`; it is **not** evidence of production HTTPS
hosting. The legacy symbol-router contract is compared by qualified source
identity and verified declaration destination, not URL string equality.

## Regression tests and reduced-fixture coverage

`tests/test_subtype_bases.py` adds **23 tests**. Positive cases cover exact
offsets, qualified external/local targets, line breaks, comments, scalar/array
constraints, two aliases of one real type, case-insensitive source spelling,
HTML entities, highlighting, preserved text and byte reconstruction after link
removal. The constrained scalar test uses the actual UInt8 declaration anchor,
not the Point_Array destination.

Negatives cover unrelated `type`, `record`, `range`, package and assignment
syntax; comments and literals; defaults; predefined types; missing owners;
private/limited context; aliases, nested scopes and prefix shadows; ambiguous
imports; non-type shadowing; dependency source/native/revision substitution;
wrong-but-existing native targets; consumer source identity changes; and forged
output metadata. Mutations assert they occurred before checking rejection.

The historical authentic reduced Geometry test remains **unchanged** at its
six-type allowlist and **94 external links**. The separate `AuthenticContour`
regression explicitly adds `OpenCV.Point_Array`, checks real Core source/native
ownership, and observes **95** external links in that reduced fixture (it lacks
`OpenCV.Core.Mat`). Omitting Point_Array leaves Contour unlinked. This is not a
silent historical baseline rewrite.

## Current Geometry: independent 267-occurrence ledger

The new harness imports PR #48's byte-verified, unchanged independent HTML
occurrence parser and source-backed navigation oracle. It reads the original
ledger under its literal SHA-256 and records new evidence only in this repo.
PR #48's original 262/4/1 ledger is never overwritten.

| Classification | Baseline | Corrected |
| --- | ---: | ---: |
| Equivalent source-backed references | 262 | **263** |
| Legitimate shared-only typed constants | 4 | **4** |
| Missing source-backed references | 1 | **0** |
| Total classified occurrences | 267 | **267** |
| Shared local links | 171 | **171** |
| Shared external Core links | 95 | **96** |

The four local additions (`Identity_Affine_Transform`,
`Identity_Perspective_Transform`, `No_Edge`, `No_Vertex`) remain. All 130
two-package navigation labels, categories, order and native destinations match
the unchanged consumer oracle. Coverage remains **452/452**.

## Four-site newly supported occurrence audit

All original source/native inventories are rechecked against unchanged
GNATDOC-002 authority. Previous publication is reconstructed by the isolated
baseline package before comparison. Every added occurrence must belong to an
actual ordinary source subtype and an independently reconciled type owner.

| Site | Native sections | Local links before/after | External before/after |
| --- | ---: | ---: | ---: |
| Core | 1,268 | 2,459 / 2,459 | 0 / 0 |
| Imgproc | 314 | 326 / **333** | 549 / **551** |
| Historical Geometry, unchanged allowlist | 130 | 171 / 171 | 95 / 95 |
| MEL | 1,237 | 1,418 / **1,419** | 0 / 0 |
| Current Geometry, separately approved Point_Array | 130 | 171 / 171 | 95 / **96** |

New Imgproc local references:

- `Affine_Mapping_Direction` → `Warp_Mapping_Direction`
- `Derivative_Kernel_Depth` → `Gaussian_Kernel_Depth`
- `Filter_Depth` → `Derivative_Depth`
- `Gabor_Kernel_Depth` → `Gaussian_Kernel_Depth`
- `YUV420_Planar_Layout` → `YUV420_Layout`
- `YUV420_Semiplanar_Layout` → `YUV420_Layout`
- `YUV422_Color_Output` → `YUV420_Color_Output`

New Imgproc external references use its **existing Core 0.4.1** authority:
`Contour` → `OpenCV.Point_Array`, and
`Flood_Fill_Mask_Value` → `OpenCV.UInt8_Value`. No Core version substitution.

The one MEL addition is
`AMS.MEL.IR.Image.Metadata.Navigation_Response` →
`AMS.MEL.IR.Image.Navigation_Response`. Its actual parent record/profile and
native anchor are retained in the occurrence audit. Core has no additions.
Historical Geometry cannot gain the external link without Point_Array in its
reviewed allowlist; only the separate current-Geometry config grants that.

No links disappear. Removing only the added hyperlinks and restoring their
previous lexical presentation reproduces original page bytes. All unaffected
files remain byte-identical, including navigation JS/indexes, the four landing
pages, **21 guides**, approved guide stylesheets, Core's **25 summaries and 102
explanatory links**, and MEL's original integrity-policy inputs. Only affected
native package pages and corresponding `presentation.json` change.

## Full publication and browser qualification

The real-site harness performs dry-run immutability, two-copy enhancement,
independent publication reconstruction, native text/anchor preservation,
byte-idempotence, deterministic inventories and exact output-file inventory.
It records original and corrected hashes rather than allowing output metadata
to approve altered source/native identities. The current Geometry config/native
inputs are additionally bound to PR #48's original report hashes.

Full Geometry tampering runs serially and observes seven rejected cases:
source type identity, wrong valid Core anchor, changed Core native bytes,
forged native profile in metadata, forged output hash, router-fixture revision
substitution, and atomic failure without partial output. Each mutation is
restored and publication is independently reverified before browser execution.

The Chromium harness clicks the single Contour base link, verifies exact
`data-type`, URL and target fragment, serves only approved `core.invalid`
requests from independently hash-verified Core 0.5.0 native bytes, checks the
real `Point_Array` heading/profile, reloads, and uses Back/Forward. All four
desktop/390px × JavaScript enabled/disabled cases pass. No stub, redirect or
synthetic target page is used. Original Geometry symbol-router tests remain
separate and unchanged.

### Investigation failures retained as limitations of exploratory runs

- The first new scalar offset assertion was off by one; corrected from 22–40
  to the actual 23–41. Fresh focused/full tests replace that failed evidence.
- The first audit baseline subprocess inherited candidate `PYTHONPATH`; the
  harness now removes it, and fresh isolated runs use the installed baseline.
- The byte audit initially did not restore punctuation highlighting when
  removing links; it now restores the pre-existing lexical markup. Production
  highlighting was not changed.
- An exploratory current-Geometry determinism check overlapped an accidentally
  early tamper run and rejected the mutation. That current-Geometry result was
  discarded. A fresh workspace passed generation before serial tampering and
  browsers; no overlapping result is credited as deterministic publication.

## Distribution, hosted boundary and reproduction

The installed wheel and extracted-sdist/rebuilt-wheel run the entire **415-test**
suite, including the original 392 and 23 new regressions. Four-profile synthetic
conformance and authentic reduced fixtures are separate from the heavyweight
local full-source/native audit and Chromium test. The unchanged hosted workflow
tests Python 3.11, 3.12 and 3.13 plus distribution installation; it does **not**
build full real consumers. Consult the final PR check record for exact-head
hosted results, not a local pass or an earlier commit.

Local harness invocations (absolute workspace paths are examples):

```sh
/tmp/gnatdoc009a-tools/bin/python /home/zboll/git/ada-gnatdoc-enhancer-009a/scripts/qualify_subtype_bases.py \
  --previous /tmp/gnatdoc008b/final-qualified --workspace /tmp/gnatdoc009a-complete \
  --consumer /home/zboll/git/opencv/geometry-gnatdoc009 \
  --geometry-inputs /tmp/gnatdoc009-type-gate-final/inputs \
  --geometry-pristine /tmp/gnatdoc009-pristine-first \
  --geometry-baseline /tmp/gnatdoc009-type-gate-final/shadow-1 \
  --baseline-python /tmp/gnatdoc009-tools/bin/python
# Wait for success before mutations; wait for restoration before browsers.
/tmp/gnatdoc009a-tools/bin/python /home/zboll/git/ada-gnatdoc-enhancer-009a/scripts/qualify_subtype_tampering.py \
  --workspace /tmp/gnatdoc009a-geometry-clean
/tmp/gnatdoc009a-tools/bin/python /home/zboll/git/ada-gnatdoc-enhancer-009a/scripts/qualify_subtype_browser.py \
  --workspace /tmp/gnatdoc009a-geometry-clean --output /tmp/gnatdoc009a-clean-browser.json
```

Generated sites and build trees stay outside source control. Compact JSON and
test transcripts are under `docs/evidence/gnatdoc009a/`; historical GNATDOC-002
through GNATDOC-008B records remain unchanged. Geometry still needs its own
reviewed merged-pin authority transition and the unfinished GNATDOC-009 runner,
PR-only shadow CI, full browser/adversarial matrix, and independent review.
This fix grants no deployment, production Core URL or release permission.