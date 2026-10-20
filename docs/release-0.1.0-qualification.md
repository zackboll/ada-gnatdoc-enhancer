# GNATDOC-012R2 corrected release qualification

## Corrective candidate

Existing PR #14 started at `d8d73eb677952ce83a8188b8c20a7c032580409e`.
Fetched main `524b7610e21e9a7b87e8e0761580ed59a3b0295c` contains the
independently reviewed R3 implementation `61d9b4981646259b2ef957be2f5aecde9b5d0d2a`,
tree `90288aa10b7cc18989f595f8195d4c431129596f`. Both identities were verified
before a normal two-parent merge. There were no conflicts. No router was edited
during reconciliation; only the obsolete release fingerprint expectation changed.

The distinct corrective record is `docs/evidence/gnatdoc012r2/`. Its source,
artifact, matrix, consumer, browser, mutation and exact-head hosted identities
supersede the original release qualification. Uncompleted gates must be recorded
as such; this document alone does not claim successful qualification.

## Historical original release preparation (superseded)

Starting main: `697d4ca91dc81812e501e501c9766d9b3ec88924`, fetched and verified
before changes. PR #13 is merged at that commit, including R2 implementation
`22eaeb928dedd72e5972db41b63f7f1dfbd432af`. No open superseding PR was present.
The tracked working tree was clean; ignored old builds were not release inputs.
Branch: `release/012-initial-0.1.0-qualification`.

The exact candidate source and final submitted head/tree, artifact SHA-256
inventory, local results and hosted run URLs are recorded in the GNATDOC-012
evidence and PR. Evidence commits are necessarily later than the source commit
whose artifacts they describe; final-head CI rebuilds and reaudits its own exact
source. Do not claim an archive includes evidence written after its build.

## Corrected contracts

* Version: `0.1.0` in pyproject, module, installed metadata and CLI. Python
  >=3.11; qualified 3.11/3.12/3.13. SPDX Apache-2.0, LICENSE included,
  setuptools >=77 for PEP 639. No core dependencies; pinned optional guide extra.
* Preserve 540 R2 tests, 18 R3 additions and three release tests: 561 distinct
  tests retained, plus three additive archive-reader tests (564 total). A new
  negative control demonstrated that the original auditor accepted wheel symlink
  entries; the audit now rejects nonregular members and unsafe/duplicate paths.
  No existing test was weakened. Require no skips, failures or errors. Provide Node.js explicitly as
  a test-tool prerequisite, not a core dependency. Qualify source,
  installed wheel and extracted-sdist rebuilt wheel with explicit fixture paths.
* Wheel/sdist/rebuilt wheel modules and CSS/JS equal source. Check archive paths,
  dependencies, metadata, required tests/provenance and generated-file exclusions.
  Large historical evidence remains in Git; only the two small provenance JSON
  files required by tests are included in the sdist.
* Retain immutable GNATDOC-011/R1/R2/R3 and original GNATDOC-012 evidence. Recheck independently pinned Core
  source and pristine identities before reuse; reconstruct source/native symbols
  and all incoming occurrences using unchanged consumer-owned oracles.
* Default and incoming-instance routers stay byte-identical. Corrected symbol-only
  bytes match R3 SHA-256 `233cf43211a711d0d64dfba2815bc2d9cc887720faed0ca38f464bc6d29e145f`.
  R3 clears inherited query parameters and unsupported outer fragments before
  reconstructing canonical navigation. R2 intentionally did not fix this defect.
  From actual merged R3 development source, the only publication difference is
  `api/presentation.json`'s `enhancer_version`: `0.1.0.dev0` → `0.1.0`. Compare
  manifest bytes after that single explicit substitution, with every other byte
  unchanged. Compared with the old pre-R3 release, symbol-only output also changes
  its approved router and dependent manifest. Do not claim old/corrected symbol
  publications are byte-identical or use candidate manifests as authorization.
* Real Core current and 0.5.0 keep 195 packages, 215 symbols, 25 summaries,
  242 incoming references and 102 internal summary links each. Verify signatures,
  native destinations, guides, two-copy determinism and byte-idempotence.
* Run symbol/generic-instance Chromium tests, R2 canonicalization and the R3
  416-trace regression on MEL and both Core revisions; preserve existing
  mutation/fail-closed gates. Hosted reduced
  qualification is explicitly not four fresh full consumer builds.

## Boundaries

No merge, auto-merge, tag, release, PyPI/Alire publication or consumer changes.
The [consumer matrix](release-compatibility.md) is not blanket migration approval.
The [release procedure](releasing.md) is for later GNATDOC-013 authorization.
Historical R1/R2 and original release evidence does not qualify the corrected router.
Unavailable campaigns must be listed explicitly in the evidence, not replaced
by synthetic results. Final disposition depends on the actual results and hosted
CI on the final submitted SHA.