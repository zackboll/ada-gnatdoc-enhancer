# GNATDOC-008A: source-order operation identities

## Scope and baseline

This correction starts at merged GNATDOC-007,
`f52dcfe37dc2819d86e72e1c38425e5e49d914eb`, freshly fetched from
`origin/main`. Its unchanged 352-test suite passes in an isolated archive.
It does not complete consumer integration or authorize production publication.

The independent Imgproc oracle is taken unchanged from consumer PR #72 head
`f2989da6c6a593f6196d1d989be0b2d126743dc6`, with source baseline
`9ce22ae5ab70008e1147475a9e6d7baef82f1df0`. The before run reproduces
66 incorrect labels among 314 navigation entries. See the new evidence directory
`docs/evidence/gnatdoc008a/`; GNATDOC-002 through GNATDOC-007 records are not rewritten.

## Root cause and correction

The old `navigation.operation_entries()` used `len(resolved)+1`, the size of the
entire category, to number same-name native sections. This both leaked preceding
entries into the ordinal and trusted native section order. In particular,
`Get_Gaussian_Kernel`'s native sections are not in Ada source order.

`destinations.source_destinations()` now shares the existing authored-link
resolver's complete-profile reconciliation with operation navigation:

1. Discover the source-owned package inventory using `inventory.packages()`.
2. Order public declarations by their source positions, retaining the existing
   narrow, flat-package constant support used by authored links.
3. Match each declaration against exactly one section in its owning native
   package using `profiles.reconcile()` and existing qualified renderer rules.
4. Reject ambiguous matches and reused native destinations within a package.
5. Count ordinals independently for each `(package, case-insensitive name)`.
6. Retain the observed page filename and anchor; never derive or regenerate them.

Navigation labels use the source spelling, with `(N)` only for multiply declared
names. Authored `api:Name/N` links use the same mapping. Unqualified authored
names remain available only when their package owner is unique. Package-only
Core/MEL navigation bypasses operation resolution as before.

The category manifest is authoritative for *membership and presentation*, not
declaration identity or ordinals. Every source-backed public declaration must be
covered exactly once. Unknown names, repeated assignments (including case-only
duplicates), omitted packages, repeated package/category identities, invalid
slugs, wrong owners and duplicate destinations fail closed. Category blocks
retain manifest order; entries sort by case-insensitive source name and source
ordinal, matching the qualified consumer presentation. Reordering native sections
or category declaration lists cannot change labels or destinations.

This remains a conservative lexical resolver, not a general Ada semantic name
resolver. Unsupported profiles do not fall back to name-only matching. Output
manifests cannot authorize a changed source identity or incorrect navigation;
verification reconstructs the permitted output from authoritative inputs.

## Focused regression coverage

`tests/operation-fixtures/imgproc/` contains nine genuine declaration/native
excerpts: both overloads of `Bilateral_Filter`, `Filter_2D`,
`Get_Gaussian_Kernel`, and `Pyramid_Up`, plus singleton `Squared_Box_Filter`.
Observed anchors and expected labels/profiles come from the unchanged consumer
oracle. The reduction adds only a package wrapper and fixture configuration;
production Ada and native acquisitions are not edited.

`tests/test_operation_navigation.py` adds 20 tests for exact labels/fragments,
authored-link agreement, reversed native order, case-insensitive identities,
independent operations/categories/packages, category reordering and adversarial
source/profile/anchor/category/output-manifest mutations. The original 352 tests
are retained without changes.

## Reproduction and qualification

Use absolute paths for all workspace arguments. Historical acquisitions must
already exist; this task does not regenerate them. The qualification harness
reconstructs the baseline with the archived starting implementation rather than
trusting mutable old output directories.

```sh
python /absolute/checkout/scripts/qualify_operation_navigation.py \
  --history /absolute/gnatdoc007 \
  --previous /absolute/gnatdoc006/final-sites \
  --baseline-source /absolute/clean-f52dcfe-archive \
  --acquisition /absolute/gnatdoc002-acquisition \
  --imgproc-008 /absolute/gnatdoc008/exact-head \
  --pristine-008 /absolute/gnatdoc008/pristine-first \
  --workspace /absolute/new-008a-workspace \
  --output /absolute/new-008a-evidence
```

This invokes the existing full-site authored qualification on all four pinned
sites, including independent publication reconstruction, native/source integrity,
guide byte parity, two-copy determinism and byte-idempotence. It reconstructs
the exact GNATDOC-008 Imgproc publication twice, runs the unchanged navigation
oracle and independent consumer native/link/guide comparison, and executes the
unchanged consumer coverage and warning ratchets. Full source/native/ordinal/
authored-anchor proof and overload counts are recorded separately.

`scripts/check_operation_browser.py` records actual Chromium click, keyboard,
fragment and rendered-profile assertions at desktop/mobile widths, light/dark,
and JavaScript on/off. It separately records native bookmark history and API
iframe overload history: a correct direct destination is not evidence that the
existing UI tracks overload history. `scripts/check_real_browser.py` retains
the existing full native/generic/authored browser checks.

## Review and handoff

Consult `docs/evidence/gnatdoc008a/validation.json` and the open PR for exact tested
revision bindings, executed results, hosted CI and independently classified
remaining limitations. No consumer workflow, category manifest, production Ada,
Pages publication or external production Core URL is changed. Imgproc PR #72
must be updated separately only after independent review and merge of this PR,
using the new immutable merge SHA. Do not merge, tag, release or deploy as part
of this task.