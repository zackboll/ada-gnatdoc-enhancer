# Auditable v0.1.0 release procedure (GNATDOC-013 only)

GNATDOC-012 prepares a PR, not a tag, release, merge or registry publication.
This procedure requires independent approval after review. There is no automatic
publishing workflow; ordinary PR CI has read-only repository permissions.

## Source and hosted qualification

1. Review existing PR #14's GNATDOC-012R2 reconciliation against merged R3 main
   `524b7610e21e9a7b87e8e0761580ed59a3b0295c` (reviewed tree
   `90288aa10b7cc18989f595f8195d4c431129596f`), and confirm its ancestry.
   The original release head `d8d73eb677952ce83a8188b8c20a7c032580409e`
   predates R3; its 543-test evidence and artifact hashes are superseded, not
   authorization for the corrected candidate. Use the new source/artifact identities
   in `docs/evidence/gnatdoc012r2/`, never the historical GNATDOC-012 hashes.
   Record the final reviewed PR head **and tree** using `git rev-parse HEAD HEAD^{tree}`.
   Read [qualification evidence](release-0.1.0-qualification.md), hashes and
   [consumer boundaries](release-compatibility.md). Do not infer consumer adoption.
2. Require successful Python 3.11/3.12/3.13, installed wheel, extracted-sdist
   rebuilt-wheel and archive-audit jobs on that exact final SHA, not an earlier
   head. Record workflow URLs, run IDs, head SHA and conclusions. Download the
   retained CI artifacts. Verify their uploaded hashes independently.
3. After approved merge, record the exact merge/source commit and tree. If merge
   changes the reviewed tree, requalify it. Build from a clean detached checkout
   or `git archive` of that exact commit, never an editable developer worktree.
   Compare all inputs to the reviewed tree. Record Python, build frontend,
   backend versions and full build/install/test logs.

## Build and independently qualify

4. Run `python -m build --wheel --sdist --outdir /absolute/path/to/candidate`
   from the clean source. Expected release names:
   * `ada_gnatdoc_enhancer-0.1.0-py3-none-any.whl`
   * `ada_gnatdoc_enhancer-0.1.0.tar.gz`
   Use `python -m twine check --strict` for metadata/rendering validation.
5. For each Python 3.11, 3.12 and 3.13, create fresh isolated source, wheel and
   rebuilt-wheel qualification environments. Provide Node.js explicitly for the
   packaged JavaScript writer regressions; it is not a core runtime dependency.
   Require 564 distinct tests (561 retained plus three malformed-wheel regression
   contracts) with zero failures, errors or unexpected skips.
   Install the wheel non-editably in
   one. Extract the sdist, build a new wheel **from that extraction**, and
   install it non-editably in the other. Install the pinned guide extra in both.
   With `PYTHONPATH` unset and working directory outside the checkout, run CLI
   help/version, `scripts/test_installed.py`, the complete shipped test suite
   and four-profile conformance for each installation. Verify optional dependency
   versions, installed module paths, native preservation, mutation tests and
   real Core/browser campaigns or explicitly reviewed pinned evidence reuse.
6. Run `scripts/check_distributions.py --source /absolute/source --wheel
   /absolute/candidate.whl --sdist /absolute/candidate.tar.gz --rebuilt
   /absolute/rebuilt.whl`. Retain its module/asset identities and archive inventory.
   Core has no runtime dependencies; `guides` pins markdown-it-py 3.0.0 and mdurl
   0.1.2. LICENSE must be included with SPDX Apache-2.0 metadata. CLI, module,
   source metadata and installed metadata must all report `0.1.0`.
7. Hash the exact upload artifacts with SHA-256 and write `SHA256SUMS`. Record
   filenames, byte sizes, source commit/tree and audit output in a release
   Candidate hashes in GNATDOC-012R2 identify those candidate files;
   rebuilding for a merged commit requires **new** hashes. Compressed archives
   are not promised byte-identical across builds. Compare installed modules and
   assets independently; never substitute one archive's hash for another.

## Authorized tag and GitHub release

8. Only with explicit GNATDOC-013 authorization, create an annotated `v0.1.0`
   tag at the qualified source commit (sign if the approved policy requires it).
   Record the tag-object SHA, peeled commit and tree. Confirm
   `git rev-parse v0.1.0^{commit} v0.1.0^{tree}` matches the reviewed identities;
   validate annotation/version and signature if signed. Stop if a tag already
   exists with a different identity. Never move, replace or force-push a tag.
9. Publish a GitHub release against that verified tag, uploading the exact wheel,
   sdist, `SHA256SUMS` and source/qualification manifest. Release notes must link
   evidence, supported GNATdoc/Python versions, optional dependencies, known
   R3 symbol-only canonicalization correction, migration instructions and exclusions.
   Do not publish PyPI or Alire as part of this procedure.
10. Download the **published** artifacts to another clean directory, verify hashes
    and tag/source identities, and repeat non-editable wheel/sdist installations,
    `--help`, `--version` and installed smoke/conformance from outside the source.
    Record URLs and logs. If a published defect is found, follow the approved
    incident/yank/superseding-release policy; do not silently replace release bits.

## Mandatory stop conditions

Stop for dirty/unreviewed source; superseding work; version mismatch; failed or
missing exact-SHA hosted CI; missing/tampered artifacts or evidence; archive
identity/content drift; unexpected dependency/path/build products; any failed
test, byte-parity, source/native inventory/destination or determinism gate; an
unavailable real campaign represented as reproduced; unauthorized consumer or
router changes; unapproved known limitations; or tag/source mismatch. Retain
logs and report `CORRECTIVE_WORK_REQUIRED` (or `HOSTED_CI_PENDING` when only CI
is outstanding). Never treat green synthetic conformance as full-site proof.

Any future release automation needs an explicitly authorized release event and
trusted reviewed source. Untrusted PR execution must never obtain publication
credentials or publish artifacts as releases.