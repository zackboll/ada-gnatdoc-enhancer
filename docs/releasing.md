# Auditable v0.1.2 preparation and later publication

## Maintainer-led release governance (current repository policy)

This is a maintainer-operated project. The repository maintainer makes PR merge,
qualification-exception and release decisions, subject to actual GitHub branch
rules and any applicable external obligations. A PR comment or maintainer merge
action is a sufficient decision record; separate release-authority appointments,
signed declarations, approval dossiers, repeated permission requests, and a
mandatory independent human reviewer are **not** repository requirements.
Technical peer review is welcome, but is not an additional gate unless required
by an applicable external commitment or GitHub rule. An agent's report is
evidence, not a human review or an assertion that the maintainer approved it.

**Do not remove objective technical gates:** required CI, regression/security
checks, version/source provenance, archive and installed-content audits, browser
compatibility where applicable, and checksums remain mandatory. Failed or
unexplained tests or content mismatches block the change. For documentation-only
edits, record source/runtime input identity and run required exact-head CI;
repeat expensive functional campaigns only if relevant inputs or contracts changed.
A maintainer may merge after these requirements and applicable GitHub rules pass;
no extra READY_FOR_INDEPENDENT_REVIEW or multi-role approval ceremony is needed.

### Expired hosted publisher artifact policy

A GitHub Actions artifact can expire under retention settings. Expiration is an
evidence-availability issue, not proof of a compatibility defect. If an expired
published-site artifact cannot be freshly retrieved, a maintainer may accept
**documented alternative evidence** for that acquisition requirement, provided
it includes all of the following:

1. Source/build/artifact/deploy provenance from original authenticated run logs
   and deployment records, with immutable revision and recorded digest identities.
2. Fresh verification of available original-run corroborating artifacts (keeping
   each artifact's identity distinct); never relabel a review ZIP as a Pages ZIP.
3. Fresh live HTTPS body/hash verification of the complete approved published-file
   inventory, before and after applicable browser checks, plus source/router/native
   contract and deployment identity verification.
4. A complete record of missing historical evidence, observed limitations and
   any unclassified differences. Cached bytes are not a fresh GitHub download.

If the provenance or published-content parity cannot be established, **stop**.
The maintainer records a concise, scope-specific acceptance or rejection in the
PR; no reconstruction of an unattested historical runner, special release-authority
appointment, or second approval dossier is required. This alternative **does not**
establish reacquisition of the expired artifact. It does not waive any other
technical gate or imply permission to publish.

## GNATDOC-020: preparation only

GNATDOC-020 is a preparation PR, not a publication event. While it remains
under review, do not tag, publish, deploy, or migrate consumers. The maintainer
may merge it when the technical gates above, applicable GitHub requirements and
any documented publisher-alternative review are satisfied. Never add publishing
credentials to a PR workflow. Historical evidence and prior blocker reports
remain preserved under
[`docs/evidence/gnatdoc020/`](evidence/gnatdoc020/README.md).

Require the freshly fetched starting main commit
`8527052b43af06a5fefd74428a07342022469ff3`, tree
`6a63cef9f131e08069d8a4a01329e80e2cf7f634`, the three feature merge ancestors,
and successful merged-main workflow `40628001480`, all six mandatory jobs.
If main advances, reconcile without rewriting published preparation history.
Run exact-head CI and repeat affected qualification when relevant technical
inputs change. Preserve historical feature evidence.

All active authorities must say `0.1.2`: project/module/distribution/CLI,
wheel METADATA and dist-info, sdist root/PKG-INFO/egg-info, generated manifests,
auditor and provenance. Keep Python >=3.11 (3.11/3.12/3.13), GNATdoc HTML 26.0.0,
Apache-2.0, dependency-free core, `py3-none-any`, optional
`markdown-it-py==3.0.0` and `mdurl==0.1.2`. Node is a test prerequisite only.

Retain all 653 predecessor test identities and run the complete suite in all
nine Python × source/canonical-wheel/rebuilt-sdist-wheel environments, zero
failures/errors/unexpected skips. Installed campaigns use isolated non-editable
environments outside the checkout, unset `PYTHONPATH`, verify imports and versions,
all bundled bytes, four conformance profiles, source/native and mutation controls.
Build from a clean immutable Git snapshot, audit archive safety before extraction,
rebuild from that independently extracted sdist, verify full member identities,
wheel RECORD hashes/sizes, license/entry point/dependencies and Git source inventory.
Keep original/rebuilt archives, logs, tool versions, SHA-256 and provenance.

Independently compare at least 26 complete profiles and relevant opt-ins against
both merged GNATDOC-019 and actual publicly downloaded v0.1.1. Use
`scripts/compare_release_outputs.py`: merged-main permits only `enhancer_version`;
official default-router profiles additionally permit the approved navigation
asset and its manifest hash. Other official profiles permit only the version.
Custom themes and external stable bookmarks are merged-source comparisons, not
official-v0.1.1 capabilities. Unclassified differences block preparation.

Requalify pinned authentic consumer inputs, refreshed Imgproc PR #81, source/native
declarations, exact external destinations, 25 Core summaries/102 links/242 incoming
references, guides, compiled examples, warning/coverage ratchets, determinism,
idempotence and Chromium matrix. Custom-theme computed style parity, stable/direct/
mixed/_top external policies and default-router real Back/Forward are independent
gates. Synthetic `pageshow` is not BFCache certification. Freshly determine the actual Core deployment, not main: source/workflow,
available original-run artifact identities, complete 209-member authority
reconciliation, approved Core-v1 router, source/native profiles, symbol index,
and HTTPS bodies/origin/redirect policy before and after browsers. An expired
Pages artifact may use the documented alternative-evidence policy above.
Changed referenced contracts require explicit technical reconciliation and a
maintainer disposition; they are not cleared by a policy exception.

The exact final pushed head must pass all six source/wheel hosted jobs. Download
all three candidates by immutable artifact ID; verify GitHub ZIP digest, internal
SHA256SUMS, head/tree provenance, archive members, RECORD, installed modules/assets
and independently rebuilt-sdist contents. Evidence-only commits require proving
distribution inputs unchanged **and** exact-final-head hosted/archive reruns.
Report `READY_FOR_MAINTAINER_REVIEW` when the applicable technical gates pass;
otherwise record the precise pending/blocked disposition and unexecuted gates
honestly. Independent human approval is optional unless independently required
by a GitHub rule or external obligation.

## Post-merge v0.1.2 GitHub release (maintainer-initiated)

1. Require maintainer review and merge of GNATDOC-020, respecting GitHub-required
   checks and approvals. Record the reviewed PR head/tree and actual merged source
   commit/tree. Merging alone does not authorize publication.
2. Require successful exact-merged-main hosted CI, all six jobs, and independently
   inspect its artifacts. Earlier PR-head success is not merged-main success.
3. Rebuild from a clean immutable snapshot of that exact approved merged source:
   `python -m build --wheel --sdist`, then `python -m twine check --strict dist/*`.
   Produce `ada_gnatdoc_enhancer-0.1.2-py3-none-any.whl` and
   `ada_gnatdoc_enhancer-0.1.2.tar.gz` and retain the full regular-file Git inventory.
4. Complete archive, nine-environment installed-package, two-baseline compatibility,
   authentic consumer/security and real-browser qualification again. Rebuild the
   wheel from audited extracted sdist and compare complete members, not compressed
   archive hashes. No unclassified difference or missing gate is permitted.
5. Run `scripts/record_candidate_provenance.py` with maintainer-confirmed
   `--expected-source-commit` and `--expected-source-tree`, explicit repository,
   source, wheel, sdist and rebuilt paths. Prepare final `release-provenance.json`;
   its `publication_authorized: false` records that the audit itself is not approval.
   Keep the subsequent publication authorization separately. Do not infer source
   approval from candidate contents or self-assert final identities inside a commit.
6. Prepare exactly four public assets: wheel, sdist, `release-provenance.json`,
   and `SHA256SUMS` covering the other three. Generate **new** hashes for the exact
   final bytes. Never carry preparation hashes forward if merged source identity
   changes. Retain rebuilt archives and audit logs separately as qualification inputs.
7. The maintainer verifies final source, qualification and all four asset identities
   and explicitly authorizes publication before creating an annotated `v0.1.2`
   tag. No separate approval-role ceremony is required. Stop on an existing
   conflicting tag; never move or replace tags or v0.1.1 assets.
8. Verify annotation, tag-object SHA, peeled commit and source tree with
   `git cat-file -t v0.1.2` and
   `git rev-parse v0.1.2 v0.1.2^{commit} v0.1.2^{tree}`; verify signatures if required.
9. Only then publish the GitHub release with **exactly** the four qualified assets.
   Release notes must explain opt-ins, default-router change, pristine regeneration,
   version-bound manifests, JS-disabled stable limitations and adoption boundaries.
10. Independently download all four public assets, verify checksums and tag/source,
    and freshly install wheel and sdist non-editably in isolated environments outside
    source. Verify CLI/module/distribution, bundled content, complete tests and
    conformance. Record URLs and logs. Do not silently replace defective release bits.

PyPI and Alire remain explicitly out of scope. Toolkit release does not approve
consumer production adoption or Pages deployment. Missing exact-source CI,
source/archive drift, changed publisher contract, failed tests or browsers,
unapproved differences, credentials in PR workflows or incomplete evidence are
mandatory stop conditions, not waivers.

## Historical v0.1.1 publication procedure (GNATDOC-015)

The historical steps below describe earlier release tasks, not additional
current-repository approval roles. The maintainer-led governance above applies
to current and future release decisions; historic published evidence is unchanged.

GNATDOC-015 authorizes release preparation only. Leave its PR open, non-draft,
unmerged and with auto-merge disabled. The following publication steps require a
**subsequent explicitly authorized task**. No PyPI or Alire publication is
authorized. Never add publishing credentials to a PR workflow.

1. Require independent approval and merge of GNATDOC-015. Record the reviewed
   final PR head/tree and the actual merged-main commit/tree. Reconcile changes
   since starting main `5ac7be66d23169dba7f9d13187a3eec5c8caee3c`, tree
   `fd6c94ed68e0e9e70e48e0b8ac6e26952e9d4f10`.
2. Require all six Python 3.11–3.13 source/wheel jobs on the **exact merged-main
   commit**, not a previous PR run. Retain run URLs, SHA, jobs and conclusions;
   download CI artifacts and inspect actual content/digests.
3. Build official distributions from a clean checkout or `git archive` of that
   exact approved merged source. Inventory source bytes against its Git tree.
   Record Python patch versions, pip, build, setuptools (including isolated build
   backends), twine, Node.js, Playwright and browser versions and complete logs.
   Run `python -m build --wheel --sdist --outdir /absolute/candidate`, producing
   exactly `ada_gnatdoc_enhancer-0.1.1-py3-none-any.whl` and
   `ada_gnatdoc_enhancer-0.1.1.tar.gz`; run `python -m twine check --strict` on both.
4. Independently audit complete archive membership and paths before extraction:
   reject symlinks, hardlinks, devices, FIFOs, sockets, duplicates and traversal.
   Extract the sdist, rebuild its wheel and run `scripts/check_distributions.py`
   with `--source`, `--wheel`, `--sdist` and `--rebuilt` absolute paths. Require
   exact source/module/CSS/JavaScript identity, complete tests/fixtures including
   GNATDOC-014, and exclusion of generated products/large historical evidence.
   Keep Python `>=3.11`, Apache-2.0, dependency-free core and the optional guides
   pins unchanged. Compare complete content, not compressed archive bytes.
5. Independently requalify all nine Python 3.11/3.12/3.13 × source/canonical
   wheel/rebuilt-sdist environments. Require all 576 retained tests plus added
   release tests, zero failures/errors/skips, security/mutation, native identity,
   generic-instance and authored-guide controls. Install both wheels non-editably;
   run outside the source checkout with `PYTHONPATH` unset. Run installed smoke,
   CLI help/version, bundled assets, dependency checks and four-profile conformance.
   Independently require source, wheel/sdist/rebuilt metadata, sdist directory,
   installed module/distribution, CLI and manifest versions all equal `0.1.1`.
6. Reconstruct default output using the **original official v0.1.0 installation**
   and equivalent pristine native inputs. Permit only `enhancer_version` changing
   to 0.1.1 in presentation metadata; no other output, native declaration, anchor,
   link, rendered source, default navigation or asset drift. Compare opt-in output
   with verified merged GNATDOC-014: exactly 586 `_top` attributes and unchanged
   destinations, apart from that same manifest-version transition.
7. Recheck read-only Imgproc PR #81 source/native/Core identities. Qualify both
   actual installed official and rebuilt wheels: 329 declarations and source-owned
   operation destinations, 586 external occurrences / 14 types, 350 local links,
   1,596/1,596 documented elements, two-copy determinism, idempotence and installed
   CLI `verify`. Execute fresh live Core HTTPS browser campaigns, 224 top-level
   traces each: exact visible declaration, direct fragments, mouse/keyboard,
   Back/Forward, JS on/off, desktop/mobile and light/dark. Recheck hosted bytes and
   deployment identity; Pages is mutable. Explicitly distinguish historical
   native evidence reuse from freshly executed checks. Do not modify PR #81;
   Core policy approval, authored-site parity, full consumer production browser/
   security qualification and deployment remain separate consumer gates.
8. Prepare `release-provenance.json` with approved source commit/tree, full source
   inventory, archive SHA-256 hashes/sizes, content inventories, toolchains,
   qualification results and hosted links. Authorize identities from approved
   source/review records, not an archive's own claims. Rebuild and requalify after
   any final source/evidence change; preparation hashes do not authorize merged
   release artifacts. Avoid self-referential commit/hash claims. Hash the exact
   wheel, sdist and provenance JSON in `SHA256SUMS`; record the checksum file's
   digest independently in the handoff.
9. Only after explicit release authorization and all gates, create **one annotated
   `v0.1.1` tag** at the approved source commit. Verify annotation/tag-object SHA,
   peeled commit and tree with `git cat-file -t v0.1.1` and
   `git rev-parse v0.1.1 v0.1.1^{commit} v0.1.1^{tree}`; verify signatures if policy
   requires them. Stop on a conflicting existing tag; never move/force-push tags.
10. Publish exactly the qualified wheel, sdist, `release-provenance.json` and
    `SHA256SUMS` on the GitHub release for that tag, not the rebuilt test wheel.
    Notes must explain opt-in/default behavior and consumer/publication boundaries.
11. Download all four public assets into a fresh directory. Independently verify
    hashes, sizes, tag/source identities and content inventories. Smoke-test public
    wheel and public sdist installations non-editably outside the checkout with
    `PYTHONPATH` unset: CLI/version, assets, verify and conformance. Record URLs/logs.
12. Preserve existing v0.1.0 tag/assets unchanged and recheck their identities.
    Never silently replace published bits; use the approved incident procedure.

Stop on dirty/unreviewed/superseded source, failed or missing exact-SHA CI,
archive/content/version drift, unexpected dependencies/assets, any failed
test/parity/source/native/browser gate, unavailable fresh execution represented as
completed, or unauthorized consumer/publication changes. Report
`HOSTED_CI_PENDING` if only CI remains; otherwise `CORRECTIVE_WORK_REQUIRED` with
the actual blocker. `READY_FOR_INDEPENDENT_REVIEW` requires every preparation
gate, not permission to publish.

## Historical v0.1.0 procedure (GNATDOC-013; retained, not current instructions)

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