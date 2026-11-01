# GNATDOC-035 — v0.1.5 release preparation

This is candidate qualification, not publication authority. The maintainer-led
policy in `/docs/releasing.md` applies. No merge, tag, GitHub Release, deployment,
PyPI/Alire upload or consumer repository modification is authorized here.

## Starting identities and official baseline

Freshly fetched main has not advanced from the supplied identity:

* commit `4be96483ef0d38ac78669e18b4910d0f711c5d86`
* tree `b0338f6467c9740e7c1d8b90cdee3d37fa2ce50e`
* predecessor: merged PR #29, GNATDOC-034
* required exact-main workflow: `41340729620` (not predecessor PR-head checks)

`official-v014.json` records independently retrieved GitHub release metadata,
asset sizes/digests, and verification of all four official assets. All checksum
entries, every archived wheel/sdist member, and all 2,902 provenance source-file
records were checked. Official tag/provenance commit is
`2200eb0e95e769a70d3d38a6c8b7facce8205924`, tree
`a0c1038b8332c3ff040b678d393f2871e7d5eeb4`.

`version-occurrences.json` classifies the complete tracked pre-edit 0.1.4 search.
Historical evidence, archives, research observations, comparators and older
comparison tests remain intact. Current module/CLI/package/archive/provenance
authorities and active contracts advance to 0.1.5. Previous-release rejection
tests retain 0.1.3 controls and additionally reject 0.1.4.

## Qualification and auditable candidate identity

The PR delivery record is the final authority for the final commit/tree,
changed-file inventory, exact-head hosted run IDs, completed test counts/skips,
candidate sizes and SHA-256 digests. This avoids embedding a commit's own hash in
itself. Candidate archives are built from an immutable Git export, audited with
`/scripts/check_distributions.py` and bound to independently supplied commit/tree
by `/scripts/record_candidate_provenance.py`. Candidate `release-provenance.json`
always retains `publication_authorized = false`.

The explicit `/scripts/compare_release_014_015.py` permits only the exact version
field in serialized presentation bytes. `/scripts/qualify_release_014_015.py`
reconstructs Core, Imgproc, Geometry, MEL and Core search from pinned inputs with
the independently installed official wheel, including existing highlighting and
navigation/theme profiles. Historical 1,462-record Core is not relabelled as
current 1,487-record Core. Compiler-backed production controls retain all five
original guides and 38 Ada fences, four exact native call anchors and two lexical
Mat links; incomplete mixed fragments remain conservative. The additive release
test strips only authenticated call anchors and requires all remaining render
bytes to equal verification-disabled rendering exactly.

Local complete logs, private compiler receipts, source exports, browser traces,
screenshots and candidate archives are retained in `/tmp/gnatdoc035`; private
build inputs remain outside the repository. The delivery record distinguishes
new execution from retained native GNATdoc 26 acquisition reuse. Private tests
not executed must be reported as skips, never passes. Initial environment/setup
failures are retained in logs and superseded only by successful corrected runs.
Unresolved technical failures mean `CORRECTIVE_WORK_REQUIRED`; incomplete hosted
checks mean `HOSTED_CI_PENDING`; only all required gates passed permit
`READY_FOR_MAINTAINER_REVIEW`.

## Candidate release notes and limitations

* Compiler-verified static overload hyperlinks authenticate GNAT ALI selection,
  Libadalang declaration coordinates, public source profiles and native anchors.
* Mixed source-text guides and the original Core homepage are supported without
  rewriting the consumer's five guides. Mat Create 1130, Clone 1242 (not UMat),
  Rows 3661 and Columns 3669 are the production controls.
* Verification defaults off. Existing highlighting, guides, themes, search and
  navigation retain official v0.1.4 bytes apart from version presentation metadata.
* Installed publishing remains compiler-free, with zero mandatory dependencies;
  optional `markdown-it-py==3.0.0` and `mdurl==0.1.2` pins remain stable.
* Generation is a source-checkout operation requiring the documented private
  GNAT 16.1.0, GPRbuild 26, Libadalang 26 and GNATdoc 26 build environment. It is
  not advertised as a standalone wheel entry point.
* Generic/renaming/dispatching calls, implicit/inherited/local declarations,
  operators, unsupported ALI forms, non-ASCII/tab/CRLF columns, automatic fragment
  compilation and computed/inherited/conditional GPR coverage remain unsupported.

After maintainer merge, final public v0.1.5 assets must be regenerated and fully
qualified from the exact approved merged-main commit/tree. Consumer adoption in
`opencv_core_ada` is separate work; its five existing guides need no rewrite.