# API browser declaration history (GNATDOC-008B)

## Baseline and defect

The reviewed starting `origin/main` is
`255e6453d2ec4801e804625f690a13956d62d145` (merged GNATDOC-008A).
The previous local branch was clean at
`d9bd44aa87a103c73ad935445a69f0ae4308348d`; the 008B branch starts from
the merged main commit, not that branch. The immutable baseline archive passes
372 tests. Historical evidence is not regenerated or edited.

The unchanged 008A harness reproduced 108/112 passing checks on pinned Imgproc
`9ce22ae5ab70008e1147475a9e6d7baef82f1df0`, Chromium 156.0.8078.4.
All four desktop/mobile × light/dark API history assertions failed. The old
implementation compared only package identity, omitted declaration IDs from
outer history, and replaced the iframe location. Therefore the two overload
clicks supplied no distinct outer entries; Back could leave the API browser.

The detached-frame errors in this reproduction and destroyed execution
contexts in 008A are consequences of traversing away from the outer document,
not evidence that the expected declaration was restored. The **unchanged**
112 assertions pass against the fixed asset. The extended harness additionally
waits for the exact outer URL before reacquiring the frame, then requires its
exact URL, unique native heading, and complete expected declaration profile.
This removes the stale-frame observation race without relaxing an assertion.
It uses no sleeps or arbitrary delays.

## State contract

Package-only bookmarks remain `api/index.html?package=OpenCV.Image_Processing`.
For example, the real, source-verified Filter_2D (1) deep link is:

```text
api/index.html?package=OpenCV.Image_Processing&declaration=fbd2fb812a53fcd97a2120c5d9706f73fe023cc2342c9cd73d2c864c4afc2755
```

The declaration value is an observed native ID, not a generated identity.
The outer hash remains reserved for compilation-unit/tagged-type navigation.
Unrelated query parameters are retained for backward compatibility (including
the existing full-browser bookmark assertion); they never select destinations.

At initialization, compilation-unit links establish package identity and
observed pathnames. Existing generated sidebar links establish the exact
approved `(package, native anchor)` set. No filename or anchor is hashed from
a name. No resolver, category ownership, label generation, native HTML, CSS,
authored guide, dependency manifest, or source baseline changes.

### Security and invalid-state policy

* Exactly one known package is required. Package matching retains the previous
  case-insensitive behavior; initial normalization restores its source spelling.
* Missing/unknown/duplicate packages fall back to the first approved package.
* Missing declaration means package-only state. Unknown, malformed, duplicate,
  or wrong-owner declarations fall back to the selected approved package only.
* A lowercase 64-character ID alone is insufficient: the exact page/fragment
  pair must occur in the approved map.
* Package and declaration values are identities, never URLs or HTML. Malformed
  percent encodings do not resolve to an approved identity and safely fall back.
* Only bare observed hashed filenames, optionally with observed hashed anchors,
  confer sidebar authority. Absolute URLs (even same-origin), cross-origin URLs,
  traversal, protocol-relative URLs, protocol substitution, arbitrary HTML paths,
  injected links, and mutated sidebar destinations cannot enter tracked state.
* Native-document click enhancement accepts only the same approved destinations
  using bare filenames or native `#anchor` links. Ordinary unapproved/native
  external links remain ordinary links: they are not registered as trusted state.
  This is not a sandbox for arbitrary native content and adds no new native script.
* Initial invalid URLs are canonicalized with `replaceState`. `popstate` reads
  and safely restores the validated fallback without writing either history
  method. Thus an externally constructed invalid historical URL itself is not
  rewritten during traversal; the selected/frame destination is still approved.

## Navigation and concurrency

Explicit approved selections alone push outer history, once per changed full
destination. Selecting the same package-only state or same declaration does not
push. Selecting the package while viewing a declaration intentionally returns
to its distinct package-only state. `aria-current="page"` identifies the package;
`aria-current="location"` additionally identifies the declaration.

The iframe uses `location.replace`, deliberately avoiding extra joint iframe
history entries. Changing this to `assign` alone would not implement the state
contract. Back/Forward reads the outer URL, selects the full destination, and
replaces only the iframe location; it never pushes or normalizes outer history.

The pending target is owned only by explicit selection/restoration. Frame loads
are acknowledgements, never history writers. A stale load cannot update selected
state or outer history; while a newer target is pending it reissues only that
approved target. Same-document hash changes acknowledge matching pending state.
External/untracked loads after completion do not change tracked outer state.
An explicit approved selection can recover from a cross-origin frame using the
cross-origin-permitted `location.replace` operation. Deterministic event-double
tests force older load completions after newer selections and restorations.

Progressive enhancement remains genuine native anchors with
`target="document-content"`. JavaScript-disabled package/operation navigation,
keyboard activation, direct native bookmarks and native declaration profiles
are exercised in desktop/mobile and light/dark Chromium contexts. No inline
executable script, remote asset, or native section modification is introduced.

## Qualification and evidence

Fresh results live in `/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc008b/`.
`operation-browser-before.json` retains the original four failures;
`operation-browser-original-checks-after.json` records 112/112 using the unchanged
harness; extended runs add repeated Filter_2D and Get_Gaussian_Kernel restoration,
outer/native traces, search/reset, deep links/reload, exact keyboard history
increments, wrong-owner/duplicate/invalid state, cross-origin recovery, and
mutated sidebar URL rejection. No original check is removed or waived.

`source-native-proof.json` is independently reconstructed and equals the 008A
314-entry proof exactly. `navigation-after.json` executes the unchanged pinned
consumer oracle. `four-site-regression.json` records two-copy determinism,
byte-idempotence, independent reconstruction, native preservation and exact
publication diffs: only navigation JS and presentation hashes change.

| Site | Native sections | Local links | Offline external links |
|---|---:|---:|---:|
| Core | 1,268 | 2,459 | 0 |
| Imgproc | 314 | 326 | 549 |
| Geometry | 130 | 171 | 95 |
| MEL | 1,237 | 1,418 | 0 |

All HTML/CSS bytes match the reviewed predecessor, including 21 authored guides,
four landing pages, Core's 25 summaries/102 links and original stylesheet
identities. MEL's original 1,162-file integrity policy executes unchanged;
coverage remains 4,294/4,295 with one uncredited Health Status renderer omission.
Consumer warning/coverage ratchets execute against isolated pinned inputs.

The 392-test suite comprises all 372 baseline tests plus 20 JavaScript behavior
and adversarial scenarios. Node is test-only, as is optional local Playwright;
no runtime dependency is added. The `.cjs` event double is included in the sdist
so installed/extracted-source tests execute the installed JS, not checkout JS.
Hosted Python 3.11/3.12/3.13 and distribution jobs remain distinct from full-site
native acquisition/Chromium qualification; the latter are local checks, not
claims about hosted CI.

Setup failures are retained, not relabeled as passes: a live editable baseline
run overlapped an asset edit (one determinism failure), an exploratory copied
publication correctly rejected its stale asset manifest, the first package
build lacked the no-isolation backend, and the first consumer-oracle invocation
lacked its isolated legacy input directory. Corrected runs use an immutable
baseline archive, pristine native reconstruction, isolated package builds and
the unchanged legacy snapshot respectively.

Final tested revision, distribution results, browser counts, hosted checks and
remaining blockers are recorded in `validation.json` and the open PR. Exact-final
HEAD hosted CI must pass before a merge-ready disposition. Imgproc PR #72 stays
unchanged at `f2989da6c6a593f6196d1d989be0b2d126743dc6`; a separately reviewed
consumer integration using an immutable enhancer revision remains outside scope.
Stop at independent review: no merge, auto-merge, release, tag, or deployment.