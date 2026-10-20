# GNATDOC-011R3 qualification evidence

Starting upstream merge: `697d4ca91dc81812e501e501c9766d9b3ec88924`.
The correction is limited to the symbol-only URL writer. Default and instance
routers, input rejection, source/native authority and historical evidence are
unchanged. `qualification-summary.json` records completed local gates; it does
not claim hosted checks before a Git commit exists. Exact tested local, fetched
remote and PR heads and final hosted conclusions are recorded in the external
final handoff and on the PR after publishing, avoiding a self-referential commit.

Complete external workspace:
`/home/zboll/qualification/gnatdoc011r3/`.
Final handoff: `/home/zboll/qualification/gnatdoc011r3/FINAL-HANDOFF.md`.
Screenshots, retained publications, rebuilt distributions, negative-first logs,
all malformed-query traces and initial harness failures are preserved there.

The original defective merge was observed before production edits: unknown query
state survives fallback and a real MEL Session link, then loses Session on reload;
unsupported outer fragments survive too. The additive Chromium regression fails
against that merge. The 18 packaged URL-writer tests likewise fail against the
original implementation and pass against the correction.

Real-site inputs are independently hash-checked retained Ada/native acquisitions,
not claimed to be freshly acquired GNATdoc output. MEL baseline is
`36ecb1e63c24df855d6f6e85f8245e16fc9d8d53`; Core source revisions are
`26bf5e2e8151cb0545b928b72d3d87677543c1ae` and
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`.
Complete source/native inventories, full publication maps and occurrence ledgers
are retained, not merely counts or candidate-generated authority.

## Reproduction

The real browser suite `tests/symbol_canonicalization.cjs` takes an independently
derived `SYMBOL_ORACLE`, `DOC_URL`, `PLAYWRIGHT_MODULE`, `CHROME` and
`BROWSER_REPORT`; optional `SCREENSHOT_DIR` preserves screenshots.
The retained external orchestration scripts are included for audit/reproduction
on this workstation. Their absolute paths are intentional evidence provenance,
not runtime/package requirements. They are not portable installed CLI commands.

`run_browser.py` serves disposable sites on loopback only. The new suite checks
actual source-linked native declaration text/scrolling, fallback/output keys,
reload/fresh tabs/history, malformed queries, fragments, delayed loads, keyboard,
repeated selection and JavaScript-disabled hyperlinks. Existing suites are not
rewritten. The full generic navigation suite runs with incoming-instance routing
enabled because it requires genuine incoming vector/matrix links; running that
suite on symbol-only output was an initial harness-profile error, preserved
externally. No instance links were invented to satisfy it.

Other retained harness failures include selecting an unapproved native operation
anchor for the approved-declaration test, trying to use the narrow consumer's
flat-scope helper for all owners, and passing a package directory where the
existing mutator requires a venv root. Only external orchestration/oracle choices
were corrected; no production authority or assertion was weakened. The narrow
flat-scope issue belongs to the separately retained DOC-010 inventory derivation,
not a new R3 source change. Original and superseded logs remain external.

## Integrity and release boundary

`evidence-sha256.json` maps every other file in this directory to SHA-256.
The external final manifest additionally binds this committed directory, final
Git identities, hosted run records and external negative/screenshot evidence.
An evidence ledger is not a signature or a substitute for independent review.

PR #14 remains untouched at `d8d73eb677952ce83a8188b8c20a7c032580409e`.
Its old symbol-router digest assertion must be deliberately updated after the
corrective merge, followed by new release qualification. Previous release
artifacts were not tested with R3 bytes. No merge, tag, release, package publish,
MEL change, DOC-010 resumption or documentation deployment is authorized here.