# GNATDOC-014 qualification record

**Independent review only. No consumer migration or new release.**

Starting main and the existing published v0.1.0 tag both resolve to
`4ee95e8c95b8c7f54397a07e3e1c507783c115aa`. The working branch was created
directly from freshly fetched main. The version remains 0.1.0 solely to preserve
the default publication contract; local rebuilt archives are qualification
artifacts, not replacements for the published release.

## Evidence and reproduction

- `qualification-identities.json`: baseline/tag identity, exact changed runtime
  module and new test/browser SHA-256 values, Python and Node versions.
- `test-retention.json`: all 564 original test IDs retained, unchanged original
  test-file hashes, 12 additive tests (576 total).
- `imgproc-qualification.json`: independent unchanged consumer-owned census and
  reconciliation of all 586 external occurrences / 14 types and 350 local links,
  source/native/artifact hash validation, two-copy determinism, idempotence,
  independent base/default parity, exact attribute-only opt-in delta.
- `live-browser.json`: unintercepted live Core HTTPS, Chrome 156.0.8078.47,
  240 assertion records: 224 generated top-level mouse/keyboard navigation traces
  (14 types × 8 desktop/mobile, light/dark, JS-on/off combinations × 2 methods),
  eight default-mode iframe controls and eight network/console summaries.
  Each top trace includes exact-fragment/native-profile visibility and
  Back/Forward. Direct URL checks also execute for every type/combination.
- `live-browser-installed-wheel.json`: the same full live-browser campaign from
  a clean non-editable Python 3.13 wheel produces an identical passing report.
- `installed-consumer-matrix.json`: all six installed wheel/rebuilt-sdist
  environments (Python 3.11–3.13) reproduce the complete source consumer
  qualification report exactly, including the default/opt-in publication hashes.
- `default-publication-parity.json`: complete historical release, independent
  base and candidate equality for both Core revisions in default/symbol/incoming
  modes, MEL default/symbol output, and four synthetic profile comparisons
  (12 profiles). Full hashes include the dependent manifest and router assets.
- `default-synthetic-browser.log`: existing Core navigation and fallback driver.
- `mutation-controls.json`: additive tests reject deliberately disabled targets,
  unconditional external targets and target leakage onto local references.
- `protected-inputs.json` and `consumer-oracle-identities.json`: untouched
  assets/historical evidence and the independently reused consumer oracle hashes.
- `distribution-matrix.json`, `3.*-*-result.json`, full test logs, conformance,
  installed smoke reports, content audits and archive inventories: **all nine
  source/wheel/rebuilt-sdist environments pass 576 tests each** (5,184 executions),
  with zero skips, failures or errors. Strict Twine, dependency checks,
  compilation, source/module/asset equality and archive membership audits pass.
  No partial or superseded run counts as a passing result.
- `qualification-summary.json`: completed campaign disposition and limitations.

The complete local workspace, original attempts/logs, candidate sites and
archives are `/home/zboll/qualification/gnatdoc014/`. Retained native input is
hash-revalidated, **not freshly built/generated**. Live Pages is mutable; browser
responses must equal the independently reviewed artifact at test time. No
production dependency-manifest permission, hosting stability guarantee or consumer
policy approval is implied. Imgproc's original approval=false record is unchanged.

Reproduce the consumer/browser campaign with the commands in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/external-type-target-navigation.md`.
The distribution harness takes `--source /absolute/clean-source-snapshot` and
`--workspace /absolute/new-output`; it creates nine independent source/wheel/sdist
test environments and executes the unchanged archive auditor and installed smoke
driver. `qualify_default_outputs.py` takes `--source`, `--baseline-src`,
`--retained` (the GNATDOC-012R2 workspace), and a fresh `--output`.
`qualify_installed_consumers.py --source /absolute/enhancer --workspace
/absolute/gnatdoc014-workspace` replays all six installed consumer checks after
the distribution matrix; it expects new `installed-final-*` output directories.

Earlier test harness attempts mistakenly passed enhanced snippets to the raw
native snapshot API or tried to reuse an enhanced site under changed settings.
The native-profile/reconstruction guards correctly rejected both. Only the new
tests were corrected to use pristine input; no existing test or production guard
was weakened. An in-progress matrix using the earlier test harness was stopped
and superseded. Its logs remain local; only the final full matrix is evidence.

Evidence is collected after the qualified source snapshot; do not claim its
archives contain evidence generated later. Final-head hosted runs rebuild their
own source. Exact submitted commit/tree, push agreement and hosted statuses are
reported on the one open, non-draft enhancer PR without self-referential hashes.
No merge, auto-merge, tag, release, publication, consumer file or PR #81 change.