# GNATDOC-012 release qualification

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

## Contracts

* Version: `0.1.0` in pyproject, module, installed metadata and CLI. Python
  >=3.11; qualified 3.11/3.12/3.13. SPDX Apache-2.0, LICENSE included,
  setuptools >=77 for PEP 639. No core dependencies; pinned optional guide extra.
* Preserve all 540 baseline tests and additive release contracts. Qualify source,
  installed wheel and extracted-sdist rebuilt wheel with explicit fixture paths.
* Wheel/sdist/rebuilt wheel modules and CSS/JS equal source. Check archive paths,
  dependencies, metadata, required tests/provenance and generated-file exclusions.
  Large historical evidence remains in Git; only the two small provenance JSON
  files required by tests are included in the sdist.
* Retain immutable GNATDOC-011/R1/R2 evidence. Recheck independently pinned Core
  source and pristine identities before reuse; reconstruct source/native symbols
  and all incoming occurrences using unchanged consumer-owned oracles.
* Default and symbol-only routers and publication assets stay byte-identical.
  The **only expected full-publication difference** on upgrading the version is
  `api/presentation.json`'s `enhancer_version`: `0.1.0.dev0` → `0.1.0`. Compare
  manifest bytes after that single explicit substitution, with every other byte
  unchanged. This is not a router or presentation compatibility rebaseline.
* Real Core current and 0.5.0 keep 195 packages, 215 symbols, 25 summaries,
  242 incoming references and 102 internal summary links each. Verify signatures,
  native destinations, guides, two-copy determinism and byte-idempotence.
* Run symbol/generic-instance Chromium tests and the R2 canonicalization
  regression; preserve existing mutation/fail-closed gates. Hosted reduced
  qualification is explicitly not four fresh full consumer builds.

## Boundaries

No merge, auto-merge, tag, release, PyPI/Alire publication or consumer changes.
The [consumer matrix](release-compatibility.md) is not blanket migration approval.
The [release procedure](releasing.md) is for later GNATDOC-013 authorization.
The known symbol-only canonicalization issue is deliberately left unchanged.
Unavailable campaigns must be listed explicitly in the evidence, not replaced
by synthetic results. Final disposition depends on the actual results and hosted
CI on the final submitted SHA.