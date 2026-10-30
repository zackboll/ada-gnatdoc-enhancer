# Task 049: reusable weighted destinations

## Starting gate and exact identities

Fetched origin/main at `2c363bca9df2ddf82e50eaa59e2505061d9e4ce5` (PR #48).
Clean worktree, no open PRs, branch `feature/049-weighted-destination`.
Host OpenCV 4.10.0 baseline: 1817 registered/executed/passed, zero failures/errors.
No historical PR #47 reconciliation commit was incorporated; version remains
0.5.0-dev. No dependency, CI, publication or scope expansion.

Reconfirmed annotated tag peeling with `git ls-remote` and inspected existing
local upstream checkouts at exactly these HEADs:

| Tag | Peeled SHA |
|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` |

Paths below are relative to `modules/core/`. Public declarations in
`include/opencv2/core.hpp`: 4.1:447-492, 4.6:462-507, 4.10:471-516,
5.0:402-443, including the accompanying DAXPY/SAXPY documentation.
Signatures accept double coefficients, OutputArray and (weighted only) dtype=-1.
Weighted channels are independent, index I is N-D, CV_32S does not saturate.

| Tag | arithm.cpp weighted table/export | matmul.dispatch.cpp OpenCL / CPU scaleAdd |
|---|---|---|
| 4.1 | 1032-1052 | 562-610 / 615-656 |
| 4.6 | 1022-1042 | 587-628 / 640-681 |
| 4.10 | 1156-1176 | 587-628 / 640-681 |
| 5.0 | 1388-1428 | 587-628 / 640-681 |

Inspected `arithm_op` fast/general paths and `ocl_arithm_op` in every tag.
4.10 representative ranges: 467-584 / 593-633 / 689-746; 5.0 corresponding
create sites 648 and 750. Weighted uses getAddWeightedTab, muldiv=true, and
double scalars[3], **not an extended function selected by old destination depth**.
Fast output creation precedes table access and OpenCL width prediction; general
N-D output creation precedes conversion/NAryMatIterator and uses source dtype.
CPU tables select source/work depth. Old output type is not a write-width selector.

Scale_Add creates output using operand type before CPU getScaleAddFunc and before
OpenCL predictOptimalVectorWidthMax. Integer CPU paths delegate to addWeighted
with explicit source depth. 5.0 changed its native non-F32/F64 branch, but the
binding intercepts half before that branch. No old-layout hazard was found.
Probe incompatible 8UC1, 16SC2, 64FC4 outputs passed on all exact versions.
**Both dense_add_weighted and dense_scale_add remain unchanged.** No defensive
preallocation, hidden output temporary, assignment, move or copy-back was added.

## Output creation, Regions and ownership

| Tag | matrix_wrap.cpp create / createSameSize / release | Mat / UMat create |
|---|---|---|
| 4.1 | 1189-1342 / 1651-1655 / 1657-1673 | matrix.cpp:318-375 / umatrix.cpp:403-461 |
| 4.6/4.10 | 1160-1339 / 1659-1663 / 1665-1681 | matrix.cpp:659-718 / umatrix.cpp:653-717 |
| 5.0 | 1466-1663,1938 / 1954-1958 / 2042-2058 | matrix.cpp:1085-1144 / umatrix.cpp:601-671 |

Create returns early for existing data with identical dimensions/extents/type.
This includes non-contiguous interior Regions; strides/offsets stay attached.
Incompatible create releases this header, then allocates; shallow old headers
keep the old allocation/Parent. Mat/UMat reference counts govern storage lifetime.
Release preserves flags/type; on 4.x a previously 2-D header retains zero 2-D
extents, while 5.0 release resets rank to zero. No ownership handle is exchanged
by into exports. Allocation functions remain unchanged and independently owned.

## Coefficient precision, SIMD and alias boundary

Audited `arithm.simd.hpp` in every tag: 4.1/4.6 weighted loops 1741-1809;
4.10 1721-1829, dual-source scalar_loop 1264-1308; 5.0 scaled macros 522-814,
especially Float32 630-662 and init_addw_f32/f64 719-758.
Audited `matmul.simd.hpp`: 4.1/4.6 scaleAdd_32f/64f around 1934-1974,
4.10:1935-1974, 5.0:2461-2500.

| Generic CPU weighted fallback output | Coefficients / work |
|---|---|
| UInt8, Int16 | Float32 weights/work, native rounded saturating output |
| Int32 | double weights/work; HAL can preempt this; no saturation promise |
| Float32 4.x | double weights/scalar evaluation; SIMD broadcasts float weights |
| Float32 5.0 | Float32 weights/work on scalar and SIMD paths |
| Float64 | double weights/work |
| Float16 4.x | exact widen to F32, native weighted F32, narrow once |
| Float16 5.0 | native half, init_addw_f32 weights/work |

OpenCL `arithm.cpp` converts userdata coefficients to float at wdepth=CV_32F
(4.1:530, 4.6/4.10:516, 5.0:542). Fast weighted work is at least F32, so
UMat integer execution can round large exact integer values. CPU Int32 and
OpenCL-enabled UMat need not produce identical large-integer answers.
The tests observe exact storage with Int32_Access and demand function/procedure/
direct-native parity for the large precision witness on every backend, including
the exception-safe OpenCL-disabled run. A separate Float32-exact Int32 witness
requires the independently derived mathematical answer. No Float64 conversion
observes either Int32 witness. OpenCL is not the only precision-changing backend.

Scale_Add F32 narrows Scale to float before CPU kernel dispatch, F64 retains
double. Integer CPU path uses weighted policy; OpenCL uses max(depth,F32) work.
Half explicitly narrows Scale to Float32 on **every supported version**.

Audited `src/opencl/arithm.cl`: all 4.x OP_ADDW:291-298, OP_SCALE_ADD:364-371;
5.0:295 onward / 371 onward. Floating paths use nested fma for weighted and fma
for scale-add. SIMD CPU weighted uses nested v_fma; scalar expression association
can differ. Scale-add vectors use v_muladd; scalar tails use multiply then add
(compiler contraction may apply). No binding-controlled precision normalization.

The actual-helper probe runs width 257, finite near-boundary values, NaN,
infinities, +/-zero, special coefficients and optimized dispatch off/on for
Mat/UMat, F32/F64/F16, fresh/exact Left/exact Right/shallow Left/shallow Right.
Exact direct-native alias oracle parity is required in every case.
OpenCL is disabled **after each setUseOptimized toggle**, since that toggle can
re-enable OpenCL eligibility. CPU dispatch observations are not accidentally
mixed with OpenCL. OpenCL-disabled does NOT force the generic scalar/double CPU
fallback: CPU HAL/platform backends may still execute. Prior local x86 Linux
CPU probes observed 200000002 through typed storage; native OpenCL can produce
200000000. Neither observation is a universal CPU precision contract.

### Corrective investigation: macOS ARM64 native Int32 precision

At review head `b75a6c4f0e4c662d4619e0ad1b0f0f996a6e4811`, push run
37243386166/job 111556401012 and PR run 37243388888/job 111556408233 each
executed 1858 tests: 1853 passed, 5 assertions failed, zero unexpected errors.
Homebrew OpenCV was 5.0.0_7 arm64_tahoe. Exact stored procedure result was
200000000 rather than the test's generic-path expectation 200000002, for both
operations, Mat/UMat, and the explicitly OpenCL-disabled UMat run.

Exact 5.0 `arithm.simd.hpp:887-919` dispatcher invokes CALL_HAL before
CV_CPU_DISPATCH. The generic CV_32S no-SIMD double fallback at 803 therefore
does not establish a universal CPU precision guarantee. Exact 5.0
`matmul.dispatch.cpp:650-653` delegates integer Scale_Add to addWeighted,
explaining why a shared weighted backend can affect both operations; both are
nevertheless independently verified against their functions and native oracle.

An authoritative candidate path exists in exact 5.0
`hal/carotene/hal/tegra_hal.hpp:804-805` (cv_hal_addWeighted32s mapping) and
`hal/carotene/src/add_weighted.cpp:98-140`: wAdd<s32> stores Float32 coefficients,
converts vector operands with vcvt[q]_f32_s32, and also evaluates scalar operands
with Float32 coefficients. This can round 100000001 to 100000000 before scaling.
The original affected job did not report cv::getBuildInformation or an active
HAL identity, so this is source evidence of a possible path, NOT an attribution
of the observed result to Carotene or KleidiCV. Conservatively this is a native
macOS ARM64/OpenCV 5 CPU-backend precision difference pending exact native parity.

The corrective adds a mandatory source/function/procedure/retained-alias/
separately constructed Raw_ABI.Native_Expected(Alias_Mode=0) gate. Source is
checked exactly as +/-100000001 and zero Right; each result uses Int32_Access.
Exact Left/Right and shallow Left/Right destinations additionally require their
direct-native same-alias result. Mat and UMat, ordinary and OpenCL-disabled,
run both operations separately. Diagnostics log all exact stored observations
and report build information once when the native result differs from 200000002.
Any parity discrepancy remains a failure, not an accepted alternative or skip.

The independent mathematical example +/-1000000 scaled by 2 must equal
+/-2000000 exactly on all backends. The coefficient-rounding Int32 witness
also uses function/direct-native parity rather than selecting an expected value
by OS, architecture or OpenCL state. Existing small integer/C3/alias exactness
and the approved Float32 width-257 alias/FMA boundary are unchanged. No production
helper, export, coefficient passing, policy, ownership or Float16 code changes.
Final hosted parity and build-information evidence are recorded in PR #50.
Local corrective tests confirm exact source 100000001 and identical
function/procedure/retained-alias/direct-native 200000002 for Mat and
OpenCL-disabled UMat on x86 Linux (host and exact-version CPU environments).
Host ordinary OpenCL-enabled UMat independently confirms 200000000 in all four
observations for each operation. These are observed values, not conditional
expected answers. The registration count remains 1858.

Observed 4.1/4.6/4.10: zero fresh/alias differences. Observed 5.0: 16 F32 weighted
finite differences (Mat/UMat, all four alias layouts), with near-boundary Alpha
1.00000006 and -0.0. 5.0 Float32 scaled-op macros back up to width-simd_width
for a fresh last vector but break to scalar tail when dst equals either source.
Scalar association and nested FMA differ. No F64/F16/scale-add fresh/alias
differences were observed with these fixtures. Independent outputs still require
strict same-build function parity; alias results require exact native same-alias
parity and independent ordinary numerical correctness, not fresh bit identity.
The documented boundary does not promise NaN payloads, universal zero signs,
cross-architecture bits or fused/non-fused equivalence.

Exact/same-layout aliases read each source before the corresponding write.
Tests cover asymmetric Alpha=2,Beta=-3,Gamma=5 and Scale=2.5, every element at
width 257, operands aliasing each other, independent/A/A/shallow A destinations,
saturation-sensitive cases, C3 and half. Arbitrary partially overlapping Regions
remain unsupported, with no overlap detection or implicit copy-back.

## Half and UMat

The unchanged helpers define half compatibility. Weighted 4.x widens both
Dense operands to Float32 and narrows native result once; 5.0 uses native half.
Scale-add always widens Dense operands, explicitly narrows Scale to F32,
executes native F32 scale-add and narrows once. Compatible whole/Region/N-D
weighted destinations and scale-add whole/Regions retain their storage through
the final convertTo; Alias and later reciprocal writes prove attachment.
For UMat, every Dense temporary remains UMat. New production exports contain no
getMat, To_Mat/To_UMat, access flags, host staging or Mat arithmetic intermediates.
Tests transfer only for setup/observation. OpenCV may choose CPU fallback; no GPU
success is claimed. OpenCL-disabled coverage restores state even on exceptions.

## Empty behavior

Public weighted validation compares rank/extents/depth/channels; default/default
and typed/typed are accepted, all default/typed mixes reject (even UInt8).
Scale-add uses the unchanged 2-D validation (Rows/Columns reject N-D), accepts
default/default, typed/typed, and UInt8 default/typed in either order. Mixed
Float32/Float16 reject element-type compatibility. No new raw semantic guards.

Destination begins Int16 C2 with retained Alias. `release` below retains that
old type but drops pixels; function release starts UInt8 C1 rank zero. `create`
adopts operand type. Old Alias pixels always survive unchanged.

| Operation / family | 4.x | 5.0 |
|---|---|---|
| weighted Mat default/default | release, rank 2 | release, rank 0 |
| weighted Mat typed/typed U8/F32 | create source type, rank 2 | release, rank 0 |
| weighted Mat typed/typed half | release, rank 2 | release, rank 0 |
| scaled Mat default/default U8 | release, rank 2 | explicit U8 create, rank 2 |
| scaled Mat typed/typed U8/F32 | create source type, rank 2 | create source type, rank 2 |
| scaled Mat typed/typed half | release, rank 2 | release, rank 0 |
| scaled Mat default/typed U8 | release, rank 2 | explicit U8 create, rank 2 |
| scaled Mat typed/default U8 | create U8, rank 2 | create U8, rank 2 |
| both UMat default/default | helper release, rank 2 | helper release, rank 0 |
| both UMat typed/typed (all three depths) | helper create source type, rank 2 | same |
| scaled UMat UInt8 mixed (both orders) | helper create U8, rank 2 | same |

No version/order normalization was added. Probe raw mixed half cases can differ
from public policy, intentionally. No broad native HAL skip was added.

## Failure/capability and validation review

Four exports reject null source/destination pointers, translate all exceptions,
and call the corresponding existing helper on destination->value. They do not
duplicate rank, shape, depth, channels, coefficients, saturation or mode policy.
Ada validates sources only, then independently rejects Destination.Temporary_View.

The only retained duplicate restriction is temporary Mat Destination. Each raw
temporary_external_view guard has a concrete ABI-safety comment: native output
creation can release/rebind the header, severing the callback-scoped external/
selected-storage capability. Compatible and mismatched temporary destinations
are rejected independently in Ada/raw ABI. Null/capability failures preserve
rank, extents/Shape, type, every pixel, selected Parent and external padding.
Temporary Left/Right remain permitted and backing storage is unchanged; no
capability escapes. No arbitrary post-native failure atomicity is claimed.
An additional 4-D Parent fixes its first axis to yield a temporary selected
3-D source, testing weighted Left and Right independently with unequal weights.
The matching N-D temporary destination is independently rejected.
No SPARK-compatible computation changed; GNATprove is not applicable.

## Reproduction

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/weighted_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/weighted-probe
/tmp/weighted-probe
```

Use opencv5 for 5.0. Probe logs numerical divergence rather than disguising it.
The shared public/raw AUnit suites register 41 focused cases (1858 total with
the 1817 baseline). Special coefficients are tested through raw/native C++ to
avoid test build -gnatVa rejecting nonfinite Long_Float before binding entry;
the production API adds no coefficient restriction. Nonfinite matrix values
are covered through public APIs, classifying without invalid Ada conversions.
Final exact review SHA and suite/build/link/probe results are reported in the PR.