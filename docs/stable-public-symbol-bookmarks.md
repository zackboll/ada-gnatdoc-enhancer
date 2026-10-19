# Stable public type and subtype bookmarks (GNATDOC-011)

**Disposition: PARTIAL_SYMBOL_COMPATIBILITY. Not a Core production migration
certificate.** The opt-in router qualifies genuine public bookmarks at two Core
revisions. Core's legacy generic-instance *incoming type references* are not yet
preserved by the shared pipeline. Do not replace Core's production generator
with this candidate. No consumer or hosted documentation is changed here.

## Explicit opt-in

```toml
[navigation]
mode = "packages"
symbol_bookmarks = true
default_package = "OpenCV.Core"
```

The default is disabled. `default_package` without the option, a non-Boolean
option, missing default, categories, operations/none navigation, unknown keys,
and a default lacking public source/native package authority are rejected.
The source inventory must agree with the native compilation-unit list. Package
spelling is canonicalized from source. There is no implicit Core-specific
default in the shared implementation.

When disabled, the existing packaged `gnatdoc-navigation.js` is unchanged:
SHA-256 `b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd`.
The opt-in packaged asset is `gnatdoc-symbol-navigation.js`; only that profile
publishes its bytes under the existing `api/gnatdoc-navigation.js` filename.
No native declaration page receives JavaScript. Other consumers need not
change their approved assets, configuration, or publication bytes.

## URL contract

Examples: `?symbol=OpenCV.Rect`, `?symbol=OpenCV.Size`,
`?symbol=OpenCV.Angle_Unit`, `?symbol=OpenCV.Point_Array`,
`?symbol=OpenCV.Core.Mat`, `?symbol=OpenCV.Float64_Value`.

Input is a fully qualified Ada type/subtype identity, matched case-insensitively.
The canonical URL includes the source-spelled package and symbol. A matching
package is accepted. Unknown/private/unqualified/subprogram identities,
conflicting owners, duplicate parameters, unknown query keys, encoded/escaped
query aliases, and simultaneous `symbol` and `declaration` fail closed to the
configured default package. In the Core profile that fallback is `OpenCV.Core`.
Percent-encoded spellings (even an encoded letter), plus signs and backslashes
are deliberately unsupported: these Ada identities require no URL escapes.

Package and approved declaration bookmarks remain supported. An approved
declaration fragment identifying a public type canonicalizes to its stable
symbol; other existing approved declarations retain the declaration parameter.
Selecting another package clears the symbol. Search does not navigate. Existing
shared labels remain **Search documentation**, **N results**, and **No matching
documentation.** Core legacy labels are **Search packages**, **N packages**,
and **No matching packages.** This is an explicit presentation difference, not
a weakened assertion about Core's original scripts.

## Authority and exclusions

`symbols.py` builds a separate, narrow inventory over existing source/native
destination reconciliation. Source owns the fully qualified identity, owner,
kind, spelling, public scope, and declaration profile. Native input supplies
only observed filenames, fragments, and reconciled signatures. Destination and
identity uniqueness are required. No hash filename or anchor is constructed.

Hidden metadata contains only a verified default package and empty links with
canonical `data-symbol` identities. The verifier reconstructs those bytes. The
separate qualification oracle reads pristine input and the unchanged pinned
Core source/native auditor, then compares every published symbol, package,
native declaration heading, fragment, and profile. It checks pristine binding
and exact router asset bytes without trusting presentation hashes as authority.

Excluded: declarations in private parts, private library units, internal owners,
formal generic types, nested/unsupported scopes, constants, subprograms,
aliases without real declarations, and generic-instance synthetic members.
Public private **views**, such as `OpenCV.Core.Mat`, are public destinations;
their private completions are not. Genuine public template members such as
`OpenCV.Core.Vectors.Vector` are eligible. An instance-summary pseudo-member
such as `OpenCV.Core.Float32_Vec2.Vector` is not a native symbol destination.

## History and browser behavior

The outer URL owns history entries; frame navigation uses location replacement.
Frame loads acknowledge selections and never write history. Superseded loads
cannot change the selected state. Native tracked type-reference clicks use the
same allowlist as direct queries. Restoration and pageshow re-scroll the exact
native declaration after checking both current selection and loaded frame URL.
Same-document fragment clicks, reloads, fresh tabs, Back/Forward, delayed loads,
rapid selection, stale scroll offsets, and foreign frames are exercised.

Native package/tagged links remain usable with JavaScript disabled. Stable
query routing itself requires JavaScript; no fake static query handler is claimed.

## Fresh real-Core findings

| Source revision | Public packages | Native sections | Public symbols |
|---|---:|---:|---:|
| current `26bf5e2e8151cb0545b928b72d3d87677543c1ae` | 195 | 1,282 | 215 |
| 0.5.0 `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` | 195 | 1,268 | 215 |

The fourteen additional current sections are the function/procedure pairs for
scalar `Add`, `Subtract`, `Multiply`, `Divide`, `Subtract_From`, `Divide_Into`,
and `Compare` from Core PR #90. No old native heading/fragment disappeared and
no public symbol destination changed. The second revision was built from its
own sources with its own native output, not current-main anchors.

Alire 2.1.1, GNAT 16.1.0, GPRbuild Alire 26.0.1 (binary banner 26.0.0),
GNATdoc 26.0.0 (20260415), markdown-it-py 3.0.0 and mdurl 0.1.2 were used.
Both production library builds succeeded before native acquisition. The default
PATH GNATdoc 27.0w was detected and not used for qualification.

The unchanged original current-Core generator and all three original navigation,
symbol, and cross-origin Chromium suites pass. A negative-first real Chromium
comparison shows the base shared router selecting `OpenCV` with no target for
`?symbol=OpenCV.Core.Mat`, while legacy Core selects the native `Mat` heading.

The candidate preserves all 1,282 native sections, 25 approved instance
summaries, 102 summary links and five authored guides. However, legacy Core has
2,742 type references versus the shared candidate's 2,503. The exact delta is:

* 240 missing incoming links to 24 vector summaries (10 per instance).
* Two missing incoming links to the matrix summary.
* Three additional source-verified `OpenCV.Size` links in shared output.

This is an existing shared-pipeline capability gap, not missing native symbols.
The router does not invent native instance declarations to hide it. Full old
generic-reference click parity and a complete Core migration certificate remain
blocked. These differences are recorded as such, never as passing equivalence.
Core 0.5.0 bookmark compatibility does not authorize hosted version-pinned URLs
or imply old documentation is published.

## Evidence and reproduction

Fresh records live under `docs/evidence/gnatdoc011/`. Historical campaign evidence
is not rewritten. Work occurred in an isolated shared worktree and disposable
Core clones; active original worktrees were not overwritten. Retained consumer
inputs were only read for exact default-output comparisons, not represented as
fresh acquisitions of those consumers.

Qualification tooling:

* `scripts/qualify_symbol_bookmarks.py`: independent pinned Core source/native
  reconstruction, native preservation, guide parity, and legacy link delta.
* `scripts/tamper_symbol_bookmarks.py`: observed real-site mutations followed by
  rejection, restoration, complete hash comparison and independent re-audit.
* `scripts/compare_default_symbol_outputs.py`: complete regenerated publication
  comparison against separately imported exact base code.
* `tests/symbol_bookmarks.cjs`: independent Chromium checks using an oracle
  ledger, not the candidate's symbol metadata.

The browser runner requires `PLAYWRIGHT_MODULE`, `CHROME`, `DOC_URL`,
`SYMBOL_LEDGER` (the recorded unchanged-Core target ledger), and `BROWSER_REPORT`.
Serve only disposable generated sites locally; no deployment is needed.
The Python suite retains all 506 baseline tests and adds 10 tests. Real-site
qualification, browser traces, default byte parity and distribution results are
separate evidence, not inferred from those synthetic tests. Hosted CI results
belong to the exact final PR head; green CI alone cannot resolve the migration
gap above. Stop at independent review; do not merge or enable auto-merge.