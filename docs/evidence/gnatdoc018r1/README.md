# GNATDOC-018R1 — qualification record

Disposition while qualification runs: **HOSTED_CI_PENDING**. This is not independent
review approval, consumer adoption approval, or release authorization.

## Baseline and approved requirement correction

Starting main `5b9ba766965b60eaa5e5228b5562b3cccf54c444`, tree
`2fedb97e2e446fc9fd0f7555060c3e24d1ae397e`, freshly fetched. GNATDOC-017
merged head `c82b18e468cb1ad18b108d2b62868ebdddbfd002`; merged-main workflow
40605341686 completed successfully, all six jobs. The 609-test baseline was
independently executed successfully before implementation. No overlapping PR or
remote branch existed. Official v0.1.1 tag/release assets are unchanged.

The original symbol-only URL failed the original exact-final-URL requirement:
Core intentionally canonicalizes it to package-plus-symbol. The user explicitly
superseded only that requirement in GNATDOC-018R1 and approved direct emission of:

```text
https://zackboll.github.io/opencv_core_ada/api/index.html?package=OpenCV.Core&symbol=OpenCV.Core.Mat
```

No other security or qualification requirement was waived. The original
`/home/zboll/gnatdoc-018-evidence/` observations are preserved, not relabeled as
passing assertions. Additive R1 work is under its `r1/` subdirectory. The original
26 top-level files were hash-inventoried before R1 and checked unchanged afterward.
Core source router `outer()` lines 47–56 returns without writing history when the
source-owned package/symbol already match; `requested()` lines 58–69 verifies the
symbol owner's package. These actual approved bytes justify the canonical form.

## Source/native and publisher identities

Core source: `33a2a4f3b83606a5c779b8a93abeb6c91fa49a21`.
Pages deployment `7348179998`, workflow `40433988181`, job `121960057063`.
Review artifact `12702919800`, ZIP SHA-256
`4995abbfed1ef594f8d1b31e8941cb0edfca3402a7b952f53683b1db524ddec4`.
Pages artifact `12703258126`, ZIP SHA-256
`9c79d54f4db56b841da0f29814c87fec563ff8bb8d8991f4b4ea5e2580581c80`.
Both original ZIPs were independently downloaded and rehashed during R1. Their
209 public file members agree with each other and the original qualification.
The complete expected publication inventory matched live HTTPS before browser
qualification; after-browser drift checking is a separate required gate.

Router source/deployed/review/live SHA-256:
`cba37439fa02e5b00e1f9de6648aca86ca3aaac61f2b8e01a45b8d99bf9ec497`.
The protocol fingerprint is a layout capability gate, not Ada source or deployment
authority. Reviewed project-owned records bind those separately. No publisher
code is run by enhancement. Genuine native input is retained GNATDOC-017 GNATdoc
26 acquisition, freshly hash-compared with committed acquisition evidence and
reconciled against exact deployed source; **not newly regenerated** in this task.

All 196 native API pages and declaration profiles match the published API.
The 216-entry stable index is reconstructed with the existing public-symbol
scope proof. The conservative external dependency inventory admits 211 identities
and excludes five unsupported owner-scope entries; those entries are not enabled
as external targets even if the publisher lists them. No HTML-only symbol map
confers authority and no filename/fragment is constructed from a symbol hash.

`Mat`: source `src/opencv-core.ads`, line 451, public view of
`OpenCV.Core.Mat`, exact native profile `type Mat is tagged private;\n`.
Native page `6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html`,
fragment `292b48d25d5af7f9173c36aa1336fe26305f00cc0f86b23654029fc9374ba1a2`.
Full per-type native/canonical ledger and source/native/publisher inventories are
retained in the R1 authority and pilot records, separately from output metadata.

## Implementation and executed pilot

The strict optional table selects canonical, source-spelled identities and an
independently reviewed qualification record hash. Existing direct destinations
must still match each selected declaration. Only `_top` is accepted. Ordinary
external URL grammar remains unchanged; no query-wide permission is granted.
Local/default/generic-instance behavior and bundled assets are unchanged.

Independent enhancement/verification recheck local source/native inventories,
deployment/workflow/artifact observations, publication/router bytes and the full
symbol index. Rehashed generated output cannot authorize a changed destination.
External stable mode adds only its selected hrefs and version-bound integrity
metadata. No network call occurs unless an explicit publication audit is invoked.

The first complete source suite passed **630 tests** (609 retained + 21 new), no
failures/errors/skips. Subsequent hardening and the frozen source/distribution
matrix require their own final results. New tests cover wrong-valid symbols and
native anchors, owner/case/private/generic confusion, forged index, changed router,
source/evidence/deployment/artifact mutation, encoded/duplicate/extra query keys,
fragments, host/scheme/credentials/port substitution, rehashed output and injected
attributes, mixed policy, no implicit network, and default/idempotent behavior.

Read-only Imgproc PR #81 refreshed head
`d4c30f12353ac8e7f70709ff12843445ad0de563`, spec SHA-256
`bcbae1a5aa3fe0cabfcf09086a9923cc87c7c43e07cbc7ceb348e7246f9b67fb`.
All three modes use identical retained genuine pristine native input:

1. Freshly installed official v0.1.1 wheel.
2. Candidate with external bookmarks disabled.
3. Candidate selecting all 14 independently verified Core identities.

Modes 1/2 are byte-identical, including manifests and bundled assets. Mode 3
changes only exact approved hrefs on one package page and corresponding
qualification/output-hash metadata. A fourth mixed-policy mode selects only one
identity. All modes reconcile each of **586 occurrences / 14 types**, exact
identity/decoded offsets/label/destination, **350 local links**, **329 native
declarations** and **1,596 documented elements**. Legacy local count 348 plus two
previously source-qualified shared additions is preserved, not normalized away.
Fresh stable generation is deterministic and enhancement is byte-idempotent.
Pilot source: `scripts/qualify_external_symbols.py`; complete records:
`/home/zboll/gnatdoc-018-evidence/r1/pilot-final/`.

## Completed additive qualification

Implementation commit `e31315122e8d6462591312728fa1f903733b6fed`, tree
`06fcc68a31e91c274b53c08255f0408ddd20520d`. A frozen source copy matched all
implementation modules, assets, tests and scripts. All nine Python 3.11–3.13
source/canonical-wheel/rebuilt-sdist environments passed 630 distinct tests each:
**5,670 executions**, zero failures/errors/skips. Four-profile conformance,
installed CLI/assets, dependency checks, strict Twine, complete archive inventories
and source/member audits pass. Fresh independently built wheel member bytes match
across Python versions. The one canonical wheel hash installed on all versions is
`6c8c9d3e9f7b89748e07306a519132c1d70b6c3a961f5fc5ad42621117914ba5`.
Distribution results and complete inventories accompany this record. These are
candidate qualification artifacts, not official v0.1.1 release replacements.

All **20** GNATDOC-017 default profiles were freshly generated in separate
official-v0.1.1, exact merged-main and candidate processes. Every output byte
matches, including presentation manifests and bundled assets, without version or
hash normalization. Profiles include authentic current/0.5.0 Core package/symbol/
incoming modes, MEL, all four authored and synthetic profiles, Features and
refreshed Imgproc. `default-parity.json` retains complete inventories.

Installed canonical-wheel Imgproc output matches every source-pilot mode byte.
The complete compact occurrence ledger retains identity, label, decoded span,
source/native profile hashes and approved URL per occurrence. Five real Imgproc
output mutations (wrong-existing symbol, owner, duplicate key, fragment and HTML
attribute injection) are rejected even after rehashing the output manifest;
restored publication bytes exactly match and independently verify.

Fresh Core custom-theme/incoming output exactly matches the qualified GNATDOC-017
publication: 195 packages, 1,293 native snippets, 25 summaries/102 summary links,
2,758 linked types. The real custom-theme browser campaign passes all 16 paired
legacy/candidate width/palette/JS combinations with no reported problems.
The exhaustive incoming campaign records 421 real clicks, all 242 occurrences
in desktop/light/JS and all 25 summary targets throughout all eight profiles.
Fresh local symbol canonicalization/negative/history/keyboard/JS-disabled browser
regressions also pass. Their resource-delay interception is confined to the
existing local-only regression, not used as live publisher evidence.

## Qualification limitations and remaining gates

The complete live external campaign now passes all eight width/palette/JS
profiles and 14 types: **560 checks**, mouse/keyboard direct+stable activation,
top-level exact canonical URL, independently owned complete native profiles,
declaration visibility/scrolling, reload/fresh tabs, Back/Forward, symbol-only
alias, JS-disabled fallback and unchanged native fragments. CDP top-frame
same-document events confirm canonical entry requires no History API rewrite.
The browser uses no interception or patched publisher code. BFCache is disabled
for this campaign, so this is history restoration qualification, not a BFCache
certification. Of **5,921** response checks, **5,824** hashes came from browser
bodies; **97** discarded CDP bodies were independently re-fetched from exact live
HTTPS URLs without redirects and explicitly labeled as separate audits, not
misrepresented as browser response bytes. No 304-body substitution is counted
as browser bytes. Final per-profile runs all pass; failed earlier attempts remain
recorded as failed. Full-inventory checks before and after the campaign match
all 209 approved publication members. A repeated final inventory/deployment check
detects drift separately from navigation. Immutable inventories do not claim to
enumerate arbitrary extra server paths.

The rebuilt-sdist wheel also repeats the complete Imgproc pilot with all output
bytes equal to source/canonical wheel. Final-head hosted CI and independently
downloaded candidate auditing remain pending. No readiness is claimed from
earlier baseline results. Initial pilot substring rollback compared a `Mat`
URL prefix inside `Mat_Array`; this harness bug was fixed by matching complete
href attributes. Failed pilot records remain retained.

Initial browser campaigns failed while reading Chromium-discarded response bodies
during history/frame replacement, not as passing feature evidence. The final
driver must separately label any explicit live HTTPS audit used when CDP cannot
provide an obsolete response body; it may not claim those bytes came from the
browser response. No interception, synthetic publisher response, or patched
publisher JavaScript is allowed. An early distribution campaign mixed changing
source tests with an earlier wheel; it is superseded by an isolated frozen-source
campaign, not normalized into passing results. Failed local-symbol harness attempts
used an incomplete oracle and a non-sidebar callable as an approved native query;
the passing rerun uses an independently verified public symbol destination, as the
existing local router contract requires.

## PR and reproduction

PR **#19**: https://github.com/zackboll/ada-gnatdoc-enhancer/pull/19, non-draft,
open, unmerged, auto-merge disabled. Implementation qualification is distinct from
final-head hosted CI and candidate artifacts. No review approval is granted here.

Retained qualification procedures use absolute paths in
`/home/zboll/gnatdoc-018-evidence/r1/`; adapt workspace paths only and recheck pins
before replay. `scripts/qualify_external_symbols.py` accepts explicit source,
authority/native, official interpreter and fresh output arguments.
`tests/external_symbols_browser.cjs` accepts `PLAYWRIGHT_MODULE`, `CHROME`,
`GNATDOC018_WORKSPACE`, `GNATDOC018_REPORT` and optional `GNATDOC018_PROFILE`
(`1280-light-jstrue`, etc.) for independent profile processes. Its oracle is the
source/native-qualified pilot ledger, not generated presentation metadata.

JavaScript-disabled stable mode promises genuine native navigation only; exact
selection stays a direct-fragment capability. No Core/Imgproc repository, PR #81,
deployment, version, tag, release, PyPI or Alire publication is modified. Stop at
one open non-draft PR with auto-merge disabled and independent review outstanding.