# GNATDOC-020 — v0.1.2 release preparation

Preparation only; no publication or consumer approval. Initial disposition:
**HOSTED_CI_PENDING**. This is an in-progress gate record, not a readiness claim.

Starting main was freshly fetched and exactly equals
`8527052b43af06a5fefd74428a07342022469ff3`, tree
`6a63cef9f131e08069d8a4a01329e80e2cf7f634`. Required feature merges
`5b9ba766965b60eaa5e5228b5562b3cccf54c444`,
`036bdd6587b93e8f6108d8b960c8c9ba8d747e78`, and that main commit are ancestors.
Merged-main workflow [40628001480](https://github.com/zackboll/ada-gnatdoc-enhancer/actions/runs/40628001480)
completed successfully, all six Python 3.11–3.13 source/wheel jobs. No overlapping
020 branch/PR existed. Independent worktree:
`/home/zboll/git/ada-gnatdoc-enhancer-020`; raw logs and original archives:
`/home/zboll/qualifications/gnatdoc020/`. Historical worktrees/evidence are untouched.

Actual official v0.1.1 wheel, sdist, provenance and SHA256SUMS were downloaded
fresh from the public release. All three checksum entries passed. The wheel was
installed non-editably in a new independent environment and CLI reports 0.1.1.
This is a separate output authority from merged development main. Imgproc PR #81
was refreshed read-only: head `d4c30f12353ac8e7f70709ff12843445ad0de563`.

The candidate includes the exact merged custom-theme, external stable-bookmark
and default-restoration features. Only the package version changes in runtime
source. GNATDOC-019 default JavaScript SHA-256 remains
`e32e0a9fcbccffbe94268ff933905e5616a52d4d89969c52e7d539acdb102522`.
Official v0.1.1 default SHA-256 is
`b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd`.
Symbol and incoming-instance routers remain unchanged. New release controls
reject old metadata/manifests, audit wheel RECORD hashes/sizes and classify every
changed output file/manifest field. No historical fixture is globally rewritten.

## Required independent gates

- Retain all 653 predecessor test IDs; pass all nine environments plus new tests,
  installed smoke/assets, four-profile conformance, complete archive/provenance.
- At least 26 complete compatibility profiles plus opt-ins. Merged main permits
  only manifest version; official default additionally permits the approved router
  and its manifest hash. Custom themes/stable external links use merged source.
- Authentic Core/Imgproc/Geometry/MEL/Features, compiled examples, guides,
  warning/coverage/source/native ratchets, deterministic/idempotent output.
- Core computed-style pilot and desktop/mobile × light/dark × JS on/off browsers;
  external direct/top/stable/mixed policies, source-owned native profiles and exact
  default restoration. Real history and synthetic pageshow are distinct, no BFCache claim.
- Fresh deployed Core source/workflow/review/Pages artifacts, complete inventory,
  original native profiles, approved router/index, HTTPS bodies pre/post browsers.
- Exact-final-head six hosted jobs, three artifact-ID downloads, GitHub ZIP digests,
  internal checksums, source/tree/member/RECORD/installed/rebuilt-content audits.

Unexecuted gates are pending, not inherited passes from GNATDOC-017/018/019.
Final commit/tree, run IDs, artifact IDs/hashes and actual gate outcomes are recorded
additively and in the open PR, avoiding self-referential claims inside a commit.

## Security and adoption boundaries

Python 3.11–3.13, GNATdoc HTML 26.0.0, Apache-2.0, no core runtime dependency;
optional guides pin markdown-it-py 3.0.0 and mdurl 0.1.2. Node is a test prerequisite.
Custom CSS requires paired approved source path/hash, exact bytes and unsafe CSS/
resource/path rejection. Stable external links require explicit hash-bound opt-in,
source/native/publisher evidence, canonical package-plus-symbol URLs and `_top`.
Native direct fragments remain authority and JS-disabled selection remains available.
Without publisher JavaScript stable links promise native navigation, not automatic
declaration selection. Core-v1 fingerprint is not relaxed for HTTP success.
Ordinary enhancement/verification remains offline. No new runtime feature is allowed.

Upgrade only by regenerating from pristine native input; v0.1.1 manifests cannot
be silently reused. Package installation does not approve consumer production or
Pages deployment. Publication requires the separate approved procedure in
[`docs/releasing.md`](../../releasing.md). No v0.1.2 tag or draft release is created.