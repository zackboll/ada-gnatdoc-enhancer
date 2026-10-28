# Stable public type and subtype bookmarks (GNATDOC-011)

## External publisher bookmarks (GNATDOC-018R1)

External bookmarks are a separate opt-in from local symbol navigation. For the
qualified Core-v1 publisher, the emitted canonical URL is:

```text
https://zackboll.github.io/opencv_core_ada/api/index.html?package=OpenCV.Core&symbol=OpenCV.Core.Mat
```

The complete URL is constructed directly from approved source spelling, with
exactly one package then one symbol and no fragment or encoding. Symbol-only
input remains a Core publisher alias, not an emitted enhancer destination.
R1 explicitly supersedes the original symbol-only final-URL acceptance criterion:
Core's independently observed router intentionally adds the source-owned package
when given the alias. Original blocker observations are preserved, not relabeled
as passing evidence. Canonical input returns early from the router's `outer()`
function and needs no History API canonicalization.

Existing native page/fragment mappings remain authority and default behavior;
selected stable mappings must resolve to the same independently reconciled public
declarations. The hash-bound record also binds complete publication bytes, source,
genuine native artifacts, Pages deployment/workflow/artifacts, symbol index and
router. Stable identity does not imply immutable hosting bytes. Legitimate updates
need independent semantic comparison and requalification against a new immutable
artifact, including full-inventory live checks, before a consumer approves new
evidence hashes. Enhancement/verification remain offline and fail closed on changed
local evidence. An explicit audit is available as
`ada_gnatdoc_enhancer.external_symbols.verify_publication(config, fetch)`.

`external_type_target = "_top"` is mandatory. With JavaScript, the top document
routes to the exact native declaration, supporting reload/fresh-tab/history.
Without JavaScript, native package navigation remains accessible but precise
automatic declaration selection is **not** supported; retain direct-fragment
mode if that is required. Toolkit support is not consumer migration approval.
See [configuration](configuration.md) for per-type selection and pristine-input
rollback. Existing local stable bookmark and generic-instance behavior is unchanged.

**GNATDOC-011R1 corrects the incoming generic-instance reference gap described in
the historical GNATDOC-011 findings below.** It does not replace Core's
production generator or authorize deployment. Final disposition and exact-head
CI are recorded on PR #13; original GNATDOC-011 evidence remains immutable.

## Symbol-only canonical URL correction (GNATDOC-011R3)

MEL DOC-010 independently reproduced the inherited symbol-only defect against
merged PR #13 (`697d4ca91dc81812e501e501c9766d9b3ec88924`): an incoming
`?package=AMS.MEL&unknown=1` fell back to the default package but retained the
unknown parameter. Clicking a genuine source-qualified `AMS.MEL.Session` type
reference reached the correct native declaration while writing
`?package=AMS.MEL&unknown=1&symbol=AMS.MEL.Session`. Reload rejected that URL
and lost the selected declaration. Unsupported outer fragments also survived.

R2 deliberately corrected only the separately opted-in incoming-instance router;
its passing CI did not certify this symbol-only transition. R3 changes only
`canonicalUrl(state)` in `assets/gnatdoc-symbol-navigation.js`: clear the entire
inherited query and outer fragment, then reconstruct the source-spelled package
and optional mutually exclusive symbol or approved native declaration parameter.
The default and generic-instance routers are unchanged. Incoming validation,
native destinations, public symbol authority and metadata are unchanged.

Input rejection and canonical output reconstruction are separate obligations:
unknown/duplicate/conflicting/encoded query inputs still fail closed, but fallback
must now emit a clean package URL so that a later valid selection survives
reload, fresh-tab restoration and Back/Forward. Valid symbol selections emit
`?package=AMS.MEL&symbol=AMS.MEL.Session`, never inherited unknown keys or outer
fragments. Native declaration hashes still require existing approved destinations;
the correction does not grant arbitrary operations or private declarations stable
symbol identities. JavaScript-disabled navigation remains native hyperlink
navigation, not a promise to interpret the outer query string.

The additive real-site regression is `tests/symbol_canonicalization.cjs`; it
requires `PLAYWRIGHT_MODULE`, `CHROME`, `DOC_URL`, `SYMBOL_ORACLE` and
`BROWSER_REPORT`. Its oracle comes from independently reconciled source/native
input, not candidate metadata. It checks the dirty-fallback transition, actual
type-reference clicks, exact declarations/scrolling, reload/fresh tabs/history,
malformed parameters, fragments, native declaration bookmarks, package switching,
delayed child loads, keyboard activation and JavaScript-disabled links across
desktop/mobile and light/dark. Packaged URL-writer tests are additive to the
existing Python suite; they do not replace real-browser qualification.

R3 evidence belongs to `docs/evidence/gnatdoc011r3/` and the distinct external
qualification directory recorded there. Original GNATDOC-011/R1/R2 evidence and
the historical findings below remain unchanged. Complete publication comparisons
must preserve disabled/default and incoming-instance bytes; symbol-only output
may change only its script and dependent presentation-manifest hash. Source,
native profiles, type-reference occurrences, metadata, CSS and authored content
remain authoritative. This bounded correction is not a general Ada resolver,
cross-browser/accessibility certification or authorization to deploy consumers.

Release-preparation PR #14 is separate: its previous candidate/evidence does not
contain corrected router bytes. After an independently approved R3 merge it must
incorporate that merge and requalify distributions, assets and compatibility before
the initial release. In particular, its `tests/test_release.py` still pins the
old symbol-router digest; that assertion must be deliberately updated to the
independently reviewed R3 digest, not suppressed. Default and instance digest
assertions remain unchanged. R3 does not change its version, branch or release
evidence.

## Canonical URL sanitization correction (GNATDOC-011R2)

Independent review found that the incoming-reference router rejected unknown
query keys but its canonical URL writer retained them from `location.href`.
Thus `?package=OpenCV.Core&unknown=1` fell back without becoming clean, and a
later legitimate symbol or summary selection could retain the rejected key and
fail again on reload. Passing GNATDOC-011R1 CI had not exercised this transition.

The incoming-reference router now clears the query before emitting only the
approved source-spelled package and mutually exclusive native symbol or
declaration parameters. It continues clearing the hash and emits
`#instance-members-summary` only for an approved explanatory summary state.
Input rejection and destination allowlists are unchanged. Unsupported incoming
fragments do not acquire authority and are removed during canonicalization.

This correction is deliberately limited to
`src/ada_gnatdoc_enhancer/assets/gnatdoc-instance-navigation.js`. The default
router **and the symbol-only router are unchanged**. The inherited symbol-only
canonicalization issue remains technical debt: correcting it requires a
separately authorized compatibility rebaseline, not an unnoticed byte change
in this task. Symbol-only and default publication parity remain required.

`tests/instance_canonicalization.cjs` is additive real-Chromium regression
coverage over independently source/native-qualified current and 0.5.0 Core
sites. It verifies dirty input to clean fallback to valid native symbol and
actual vector/matrix incoming hyperlinks, reload and Back/Forward; duplicate,
unknown, conflicting and encoded query inputs; unsupported fragments; existing
approved declaration interpretation; package switching, rapid selection and
JavaScript-disabled native hyperlinks. The reviewed router fails this test
before the implementation change. Existing browser and Python assertions are
not removed or weakened.

Fresh corrected output identities and qualification records belong to
`docs/evidence/gnatdoc011r2/`. No original GNATDOC-011 or GNATDOC-011R1 evidence
is rewritten. Retained R1 source/pristine native acquisitions are independently
hash-checked and reused for this JavaScript-only correction; this is not claimed
as a new Ada/native acquisition. Only the opted-in published JavaScript and its
presentation-manifest digest may differ from reviewed R1 output.

## Corrective incoming-instance opt-in (GNATDOC-011R1)

```toml
[navigation]
mode = "packages"
symbol_bookmarks = true
default_package = "OpenCV.Core"

[generic_instances]
qualification = "generic-qualification.json"
sha256 = "<reviewed qualification file SHA-256>"
incoming_references = true
```

`incoming_references` is Boolean and disabled by default. It requires the
existing complete hash-qualified instance record, type linking, and the
symbol-enabled package-navigation profile. Symbol routing alone does not grant
incoming-instance link authority. Unknown keys and incomplete qualifications
remain errors. The option is deliberately not a general Ada generic resolver.

Three inventories remain distinct:

1. **215 native public types/subtypes:** eligible for stable `?symbol=` URLs;
   genuine 64-hex anchors observed in pristine native output.
2. **25 explanatory instance-reference targets:** the reviewed eight depths
   times vector lengths 2, 3, 4, plus Float32 3×3 matrix. Source instantiations,
   actuals, templates, native template members, pristine empty instance pages,
   and exact generated summaries are independently qualified on every run.
3. **25 presentation-only sections:** each uses `#instance-members-summary`,
   never a native declaration anchor or additional native declaration.

For example, `UInt8_Vec2.Vector` requires an ordinary exact import of
`OpenCV.Core.UInt8_Vec2` and its owner in the caller's lexical ancestor chain.
Fully named `OpenCV.Core.Float32_Matx3x3.Matrix` also requires the exact ordinary
import. A suffix match, package alias, private/limited import, local shadow,
generic formal, nested scope, or unsupported visibility cannot grant this new
authority. Only reconciled complete source/native declarations and existing
type-mark positions are considered; the new resolver rejects expression,
default, comment, string and aspect contexts. The final component mark of a
complete array declaration is supported after balanced index constraints.
Native type recognition, including GNATDOC-009B, is otherwise unchanged.

The existing default **and symbol-only** JavaScript assets remain byte-identical.
Only this new opt-in publishes `gnatdoc-instance-navigation.js` under the
existing `api/gnatdoc-navigation.js` name. Separately labelled hidden
`data-instance` metadata confers summary navigation authority; it is not added
to `data-symbol`. A summary click owns one outer history entry, canonically
`?package=<source-spelled instance>#instance-members-summary`. This presentation
fragment is accepted only for an allowlisted instance package; it cannot make
an arbitrary iframe destination. No symbol or declaration query is invented.
Reload/Back/Forward restore the approved explanatory section. A request such
as `?symbol=OpenCV.Core.UInt8_Vec2.Vector` still fails to `OpenCV.Core`.

### Revision-specific reconciliation

| Core source | Native sections | Native symbols | Legacy references | Corrected shared | Restored instance references |
|---|---:|---:|---:|---:|---:|
| `26bf5e2e8151cb0545b928b72d3d87677543c1ae` | 1,282 | 215 | 2,742 | **2,745** | **242** |
| `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` | 1,268 | 215 | 2,698 | **2,701** | **242** |

Both revisions were freshly built and generated independently. Both retain
195 public packages, 25 summaries, all 102 summary-internal links, and five
byte-identical authored guides. All original legacy links are preserved at their
exact declaration/type-mark positions and observed destinations. The original
121 grouped current-Core rows reconcile exactly to 242 individual occurrences.

The three additional `OpenCV.Size` references are independently approved, not
suppressed to force aggregate equality:

* `OpenCV.Core.Create (Dimensions : Size; Element_Type : Mat_Type) return Mat`
* `OpenCV.Core.Dimensions (Self : Mat) return Size`
* `OpenCV.Core.Region_Location.Whole_Size : Size`

`OpenCV.Size` is a real public ancestor-visible record type. The legacy
scanner's deliberately conservative `Source.members` also treats the deeper
record component `OpenCV.Rotated_Rect.Size` as a package-level blocker. That
component is not a package-visible homograph. The three actual type marks,
complete source declarations, lines, offsets, native profiles and destination
proofs are recorded in `docs/evidence/gnatdoc011r1/Size-disposition.json`.

### Corrective qualification boundaries

The new occurrence oracle uses the unchanged pinned Core source/native scanner
and genuine legacy publication, not shared target tables or published manifests
as authority. It records every exact source/native token span, enclosing
declaration, import, instantiation, actual, dimensions, template, native source
page, summary destination and historical/new URL. It reconstructs exact summary
HTML separately from the shared renderer. Existing shared explanatory labels
(instance name and the Ada-array assignment clarification) and ASCII entity
serialization are explicitly accounted for, not mistaken for extra links.

The exhaustive Chromium runner clicks every one of the 242 occurrences in each
revision, then repeats all 25 destinations at desktop/mobile, light/dark, with
JavaScript enabled and disabled. It checks exact source declarations and
type-mark spans, destination ownership, table actuals/dimensions, visible summary,
absence of native declarations and symbol promotion, and all 102 summary-internal
destinations. History, reload, package switching, foreign frames, rapid selections
and delayed responses are exercised separately. Symbol and package suites remain
independent gates.

Original Core browser suites run unchanged against original legacy output. The
shared equivalent copies change only the documented search label/status text,
not assertions. Core 0.5.0 predates the standalone symbol and cross-origin test
files; their current behavioral equivalents run against its candidate rather
than being misreported as historical 0.5.0 scripts.

All original 516 tests are retained; 24 additive tests bring the suite to **540**.
Default byte comparison also covers Core with symbol routing but without the
new incoming-reference option. Mutation runs use a dedicated copy, never the
browser workspace. Installed code/asset tampering is detected by an external
hash ledger, not by asking modified code to attest itself. Acquisition hashes
and enhancement atomicity are checked separately from output reconstruction.
Fresh evidence, failures/retries, browser traces, distribution and mutation
results are under `docs/evidence/gnatdoc011r1/`. Passing synthetic or installed
tests do not stand in for the real-Core ledgers or browser campaigns.

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

## Original GNATDOC-011 findings (historical, before R1)

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