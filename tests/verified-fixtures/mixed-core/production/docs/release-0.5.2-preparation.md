# CORE-REL-007: opencv_core 0.5.2 source-release preparation

**Source-release candidate only; not tagged, published or indexed.** This phase
ends at independent review of an open, non-draft source PR. Merge, immutable
tagging, public-archive qualification, Alire publisher verification and a new
community-index PR require a subsequent authorized phase. No auto-merge.

## Starting identities and preservation

Remote state was refreshed on **2026-10-20 UTC** (the execution host's clock).
The checkout initially held PR #92's corrective head; the isolated branch
`release/0.5.2-preparation` starts from the fetched `origin/main`, not that local
branch. The worktree was clean before switching.

| Input | Git identity |
| --- | --- |
| Verified main / merged PR #92 | `2267853c089b4fcbc2c7496ae97f862db9dd1234` |
| Starting main tree | `afbb64c10f90f95b0aad7a46254dccffc6139f67` |
| Starting `alire.toml` blob (0.5.1) | `249b9cedcf16fb4cbbc1537cf8044b19c539f7a2` |
| Existing annotated 0.5.1 tag object | `4190bb68c0b089475db4fb385349bc6d2a62cb31` |
| Existing 0.5.1 source commit | `64d8a60b59acfe4334045280e430c4774b5cad89` |
| PR #92 reviewed head | `995be0a3e64af97d0ef93f1c06d5e291bf52ff9a` |
| User-qualified cross-install implementation | `84ab4f2125dd5a18f9801babde8b79b30a4c8827` |
| Production `src/` tree, main and qualified implementation | `a3309942109e47b34ee4fa69015f41e762059071` |
| Production `cpp/` tree, main and qualified implementation | `b159adffb50193740b46cf3b36705d09d9eb74aa` |
| Root `opencv_core.gpr` blob, both | `b7487818265649322a2651339122136fcc24aa32` |
| Root `opencv_core_shim.gpr` blob, both | `e21b92c6a81b1593aac03e76f3f0aeab489eced8` |

PR #92 is MERGED at the starting main SHA. There is no 0.5.2 tag at inspection.
The 0.5.1 source tag is preserved unchanged; the GitHub Release API returned
404 for a separate 0.5.1 Release object. This does not invalidate the source tag.

Live `alire-project/alire-index`, branch `stable-1.4.0`, contains versions
0.1.0, 0.2.0, 0.3.0, 0.4.0, 0.4.1 and **0.5.0**, not 0.5.2. The accepted 0.5.0
manifest blob is `f8c36d850718e1f08a4bfcb4c2f33534cc450762`.
[0.5.1 index PR #2243](https://github.com/alire-project/alire-index/pull/2243)
is OPEN at `eb816dad96569ba052f424888e5c8a5db2f76a2e`; it is separate and must
remain unchanged. No historical indexed manifest is edited by this release.
Index availability is determined by acceptance, not by a local candidate.

## Auditable changelog since 0.5.1

The comparison base is the peeled source tag above, not the older 0.5.0 index
entry. `git log 0.5.1..2267853` identifies three merged feature groups:

### Actual public API additions — PR #90

Fourteen declarations were added to `OpenCV.Core`: one allocating function and
one destination procedure for each of scalar `Add`, `Subtract`, `Multiply`,
`Divide`, `Subtract_From`, `Divide_Into`, and `Compare`. Arithmetic takes an
`OpenCV.Scalar`; comparison takes `Float64_Value` and `Comparison_Kind`.

Arithmetic is deliberately bounded to nonempty exactly 2-D, C1–C4, seven
depths (UInt8, Int8, UInt16, Int16, Int32, Float32, Float64; not Float16).
Comparison is C1 with an independent UInt8 mask. Scalars are channel-ordered,
not implicitly repeated. Native numerical conversion/rounding/saturation,
finite/range restrictions and integer zero-denominator rejection are
operation-specific. Destinations reuse compatible storage, detach mismatches,
permit documented exact/same-layout aliases and conservatively reject unsafe
partial overlap and temporary outputs. Preflight preserves destinations;
arbitrary native failure does not promise rollback. See the authoritative
specifications and [operations guide](core-operations-guide.md).

The entire public-specification delta is the 141 added lines in
`src/opencv-core.ads`; no existing public declaration was removed or changed.
The private thin ABI gained five C imports and the shim gained the matching
implementation. Twelve additional registered AUnit cases bring the suite from
2,025 to **2,037**. Scalar native-oracle, rounding, zero-denominator, alias and
sanitizer corrections were merged within this feature, not invented by release
preparation. Preserve the distinct R1/R2/R3 qualification reports.

### Build/install improvements — PR #92

- `scripts/cross_install_core.sh`: explicit AArch64 SDK inputs, automatic
  GPRconfig bootstrap and delegation to the existing isolated build/install.
- `scripts/cross_build_core.sh`: clean exact-HEAD Git exports or explicitly
  selected unpacked sources without enclosing-repository discovery; prefix
  selection, recursive Core/shim installation and durable installed config.
- `scripts/configure_cross_opencv.sh`, `scripts/cross_elf.sh`: retain target,
  runtime, compiler, sysroot, OpenCV and archive-member isolation controls.
- `tests/qualify_cross_install.sh`: fresh installed-only consumer after temporary
  workspace removal, compiler/archive traces, ELF64/AArch64 and no deployment
  RPATH/RUNPATH; no target execution.
- Eleven cross-install controls extend the existing 45 cross-configuration
  controls. [Cross-install guide](cross-install-core.md) and README discovery.

No additional public Ada API or algorithms were introduced by PR #92.

### Audit, scope and qualification documentation — PR #89 and correction

Pinned upstream header/census evidence, offline integrity validation, a bounded
portable scope, independent feature backlog and CI were added. Exhaustive API
discovery/coverage acceptance remains **COVERAGE_AUDIT_BLOCKED** by design;
`--allow-incomplete` validates committed evidence, not completeness. The PR #92
correction repairs 51 inherited source-anchor coordinates and their dependent
pin/tests without changing classifications or relaxing acceptance. Do not
regenerate or weaken this audit to obtain a release pass.

### Release-preparation delta

Only the root manifest version, active README/changelog/status documentation,
this record, cross-install evidence status and the pinned-consumer version
assertion change. Production Ada/C++, private ABI, GPR/build implementation,
dependency constraints, platform/system-package conditions, pre-build and test
actions are preserved. The historical 0.5.1 preparation report is not rewritten.
No public semantic validation is duplicated in the C++ shim by this release
preparation; the shim is untouched relative to starting main.

## Versioning and compatibility review

The requested version remains **0.5.2**, not silently 0.6.0. This is an
experimental pre-1.0 release with additive APIs, not a tooling-only stable-API
patch. SemVer's major-zero development status does not promise a frozen public
API; the repository's backlog reserves semantic-versioning policy freeze for
1.0. No binding repository rule requiring a minor bump for these additions was
found. Independent review must explicitly consider this rationale. If a
contrary release policy is demonstrated, resolve it before publication rather
than retagging or silently changing the version.

Existing source declarations, shared-root types, ownership/shallow assignment,
deep cloning, exception policy and supported OpenCV 4.1–5.0 range are retained.
New overloads can affect unusual Ada client overload resolution (for example,
unconstrained subprogram references or unqualified overloaded expressions);
explicit type/package qualification may be needed. Recompile consumers with
the matching compiler/runtime: Ada ALIs and native C++ libraries are not a
cross-toolchain binary-compatibility promise. New bounded scalar behavior is
not a change to existing Mat/Mat overloads and does not imply UMat parity,
Float16 arithmetic, general broadcasting or exhaustive Core coverage.

## Proprietary qualification provenance and byte-identity boundary

The user reports successful GNAT Pro **25.0w / GCC 12.3.1**, target
`aarch64-linux-gnu`, Yocto **Scarthgap**, OpenCV **4.9.0** cross-install on
implementation `84ab4f2`. The
[PR #92 R1 provenance comment](https://github.com/zackboll/opencv_core_ada/pull/92#issuecomment-6281591577)
records carry-forward to `995be0a` with no production or cross-install input
changes. This release uses that reported evidence, not a new local proprietary
run; the supplied SDK is not available in the release agent's environment.

Compare the exact candidate against the full qualified SHA using:

```sh
git diff --exit-code 84ab4f2125dd5a18f9801babde8b79b30a4c8827 HEAD -- \
  src cpp '*.gpr' scripts/configure_opencv.sh \
  scripts/configure_cross_opencv.sh scripts/cross_build_core.sh \
  scripts/cross_install_core.sh scripts/cross_elf.sh \
  scripts/validate_cross_target.sh scripts/build_module_bridge_probe.sh \
  tests/qualify_cross_install.sh tests/fixtures/cross-reference \
  tests/installed_mat_consumer.adb tests/gnat12/installed_ada.gpr
```

Require exit zero and retain the complete object inventory with qualification
evidence. The implementation/configuration scripts above and all GPR files,
production sources and consumer inputs are byte-identical. The manifest is
**not** byte-identical: its sole change is 0.5.1 to 0.5.2. Cross-build scripts
hash/record the manifest for provenance but do not interpret its version or
invoke Alire; they emit the same target configuration from unchanged SDK/profile
inputs. The only changed script is the unrelated native pinned-consumer version
assertion. Documentation changes do not enter cross compilation.

Accordingly, carry forward only automatic GPRconfig bootstrap, production
Core/shim cross-build, recursive install, durable installed configuration,
clean external-consumer cross-link, ELF64/AArch64 identity and absence of
inappropriate RPATH/RUNPATH for the identical vendor profile. This is not a
freshly generated 0.5.2 binary, target AUnit run, new SDK support claim or
independent reproduction of private logs. Any implementation/input drift
requires fresh vendor qualification before passing that gate.

The GNAT Pro **25.2 / GCC 13.3.1** QEMU campaign has separate evidence in
[the historical AUnit report](adacore25-scarthgap-core-aunit.md) and
[scalar R3 full-system sanitizer report](core-fin-01-r3-target-sanitizers.md).
Do not label those results as the user's 25.0w profile or as a fresh release
candidate run. **Target hardware execution remains NOT TESTED.**

## Exact-commit qualification protocol

The commit containing this record cannot contain its own SHA or archive hash.
Record the final candidate commit/tree/manifest blob, tested/pushed/PR head,
commands, exit codes, logs and archive hashes externally and in the source PR
after committing. Do not add an untested follow-up merely to embed a self SHA.
Any corrective commit requires renewed affected checks at its new head.

Use clean `git archive` exports and fresh source/build/evidence directories,
outside the repository. Reuse installed tools/pristine dependencies, never old
objects, ALIs, libraries or test executables. Select a fresh TMPDIR on the
larger filesystem because host `/tmp` has limited free inodes. Local baseline:
Alire 2.1.1, selected GNAT 16.1.0/GPRbuild 26.0.1, native OpenCV 4.10.0.

Required local checks:

1. Native `alr -n build` and root `alr -n test` actions; complete registered Core
   AUnit suite, **2,037 pass**, zero failures/unexpected errors. Retain normal
   warning/profile policies; no persisted diagnostic profile overrides.
2. `python3 scripts/audit_core_api.py --allow-incomplete`, portable-scope check,
   evidence-validator negative tests, and discovery fixtures with the pinned
   parser dependencies. Default exhaustive acceptance is expected to reject
   incomplete evidence; it is not a passed completeness audit.
3. Cross-configuration/install, module-bridge, GNAT Pro evidence-parser and
   external-shim installation controls. These are synthetic, not vendor runs.
4. Installed and relocated standalone Ada and mixed Ada/C++ consumers with
   execution/ELF resolution. Native Debian-12 `.406`-specific checks belong in
   their Debian CI environment, not this OpenCV `.410` host.
5. Pinned clean Alire consumer (explicitly not an unpinned index test), shell
   syntax and `git diff --check`. No Ada changed; formatting/proof is not needed
   for a metadata/documentation-only delta.

Required hosted candidate gates: Core API audit evidence (established incomplete
policy), Cross configuration controls, GNAT 12 native and AArch64 aggregate
source-unit controls, GNAT 12 native production, OpenCV Compatibility
4.1/4.6/4.10/5.0 and applicable consumer/platform jobs, and Ada API Documentation
build. Inspect actual checked-out source identities: a PR merge-ref check is
not automatically evidence for a different source head. Do not count pending,
cancelled, failing or policy-skipped jobs as passes. Under current policy,
Windows/MSYS2 and MacPorts run only on main pushes/manual dispatches; PR skips
remain SKIPPED. Documentation deployment is likewise not a PR gate.

Starting-main successful runs observed at initial inspection: cross controls
39357969825, GNAT12 aggregate 39357969977, audit 39357969964, native production
39357970083 and documentation 39357969853. Compatibility run 39357969911 was
still running (Windows/MacPorts); these are baseline evidence, not candidate
qualification. Final exact-candidate results must be reported in the PR.

## Candidate archive validation

Create a clean Git tar archive of the exact committed candidate, retaining its
inventory, commit/tree identities, SHA256/SHA512 and extraction checks outside
the repository. Verify root `alire.toml` (0.5.2), `opencv_core.gpr`,
`opencv_core_shim.gpr`, production Ada/internal sources, C++ shim/header/module
bridge, native/cross configuration scripts, cross-build/install/qualification
scripts, `docs/cross-install-core.md`, tests/fixtures, metadata/docs and
Apache-2.0 `LICENSE` are included.

Reject private SDK/compiler payloads, credentials, local qualification logs,
generated objects/ALIs/archives/executables, Alire state and caches. Inspect
tracked contents, not only filename patterns. Extract into a new `.git`-free
tree and run the cross-configuration/install controls there, including explicit
`--source-root` handling and no enclosing-repository discovery. Native and
consumer builds must also start from fresh exports. This qualifies a local
Git archive only, **not an immutable published GitHub asset**.

## Independent-review stop and publication handoff

Open one non-draft source PR against `main`, titled:

**Release opencv_core 0.5.2 — GNAT Pro AArch64 cross-install and accumulated Core updates**

Report exact local/pushed/PR source identities and all check results. Use
`READY_FOR_INDEPENDENT_REVIEW` only after every applicable mandatory gate
passes; otherwise identify `HOSTED_CI_PENDING`, `VENDOR_QUALIFICATION_REQUIRED`
or `RELEASE_GATE_BLOCKED` with a concrete reason. Leave the source PR open and
unmerged, auto-merge disabled. No tag, GitHub Release, publisher or index PR
belongs in this phase.

After explicit user authorization and source merge, refresh/reconcile actual
main content, run required post-merge qualification, verify manifest 0.5.2,
create an annotated immutable `0.5.2` tag on the approved source commit and
qualify the publicly downloadable archive. Then use normal Alire publisher
build/test verification, never `--skip-build`, against that exact public commit:

```sh
alr -n publish --skip-submit git+https://github.com/zackboll/opencv_core_ada.git <APPROVED_0_5_2_COMMIT>
```

Generate, do not approximate, `index/op/opencv_core/opencv_core-0.5.2.toml`;
validate the official manifest/index, isolated candidate-only resolution and a
fresh unpinned consumer before submitting separately to `stable-1.4.0`.
Preserve 0.5.1 PR #2243 and all historical manifests. No amend, force-push,
automatic merge or claim of index availability before acceptance.