# Task 045: reusable Divide destinations

## Starting gate and scope

Fetched `origin/main`: `e5883e14ed5e4d5dd393ebcc5a03b3b14d099ca3`, exactly
the expected PR #44 merge. Worktree clean; no open PRs listed. Complete host
baseline: 1711 executed/passed, zero failed assertions/unexpected errors.
Branch: `feature/045-divide-destination`. This change is binary elementwise
Divide only, scale 1.0, preserved operand depth. No reciprocal/scalar forms,
output-depth option, denominator restriction, dependencies or CI changes.

## Exact authoritative source audit

Fresh upstream clones were checked with `git describe --exact-match`,
`git rev-parse HEAD`, `git status --porcelain`, and remote peeled tags from
`git ls-remote https://github.com/opencv/opencv.git`. All were clean.
Paths/ranges below are inclusive and relative to `modules/core/`.

| Exact tag | Peeled SHA | `src/arithm.cpp`: OpenCL / arithm_op / getDivTab / binary divide |
|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 481-598 / 602-879 / 974-984 / 1009-1015 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 467-584 / 588-867 / 962-972 / 995-1001 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 467-584 / 593-907 / 1094-1104 / 1129-1135 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 493-610 / 623-941 / 1311-1322 / 1348-1361 |

Authoritative trees: [4.1.0](https://github.com/opencv/opencv/tree/4.1.0),
[4.6.0](https://github.com/opencv/opencv/tree/4.6.0),
[4.10.0](https://github.com/opencv/opencv/tree/4.10.0),
[5.0.0](https://github.com/opencv/opencv/tree/5.0.0).

| Tag | `src/arithm.simd.hpp`: conversion / division / relevant loop | `src/opencl/arithm.cl` |
|---|---|---|
| 4.1.0 | 194-208 / 1553-1663 / scalar_loader and scalar_loop | 229-258, kernel load/store |
| 4.6.0 | 194-208 / 1553-1663 / scalar_loader and scalar_loop | 229-258, kernel load/store |
| 4.10.0 | 194-208 / 1564-1678 / 1263-1308 and preceding loaders | 229-258, kernel load/store |
| 5.0.0 | 513-710, 715-813, dispatcher at 915 | 233-261, kernel load/store |

| Tag | `src/matrix_wrap.cpp`: OutputArray create / createSameSize / release | Mat / UMat N-D create |
|---|---|---|
| 4.1.0 | 1189-1342 / 1651-1655 / 1657-1673 | `src/matrix.cpp:318-375`, `src/umatrix.cpp:403-461` |
| 4.6.0 | 1160-1339 / 1659-1663 / 1665-1681 | `src/matrix.cpp:659-718`, `src/umatrix.cpp:653-717` |
| 4.10.0 | 1160-1339 / 1659-1663 / 1665-1681 | `src/matrix.cpp:659-718`, `src/umatrix.cpp:653-717` |
| 5.0.0 | 1466-1663 / 1954-1958 / 2042-2058 | `src/matrix.cpp:1085-1144`, `src/umatrix.cpp:601-671` |

Release: 4.1 `include/opencv2/core/mat.inl.hpp:848-866,3774-3781`;
4.6/4.10 `src/matrix.cpp:547-565`, `src/umatrix.cpp:378-385`;
5.0 `src/matrix.cpp:1010-1021`, `src/umatrix.cpp:384-391`.
Conversion/create paths relevant to half narrowing: 4.1/4.6
`src/convert.dispatch.cpp:174-225` and UMat convertTo in `src/umatrix.cpp`;
4.10 `src/convert.dispatch.cpp:248-341`; 5.0:131-246.
`include/opencv2/core.hpp`: 4.1:413-439, 4.6:428-454, 4.10:434-463,
5.0:365-394. These exact divide declarations/documentation
confirms scale=1, dtype=-1, independent channels, integer zero for zero divisor,
and regular floating division (Inf/NaN). Exact tag declarations match that
binary signature. No overflow contract is introduced for Int32.

## Negative finding: no old-output selector

**There is no getDivExtFunc in any of the four exact tags.** Binary divide
passes getDivTab() directly to arithm_op, with no extendedFunc argument and
no kernel selected from `dtype < 0 ? dst.depth() : dtype` before creation.
The same-type fast path creates operand-type output before calling the table
entry indexed by operand depth. The general path resolves dtype from operand
type when dtype=-1, creates output, then selects working-depth conversion and
division kernels. OpenCL reads the type of the already-created destination.

Subtract/Multiply's old destination-width selectors are not applicable.
No analogous defect was demonstrated by this source review or actual-helper
whole/Region/ordinary mismatch/alias probes. **No preallocation guard or new
compatibility code was added. dense_divide and divide_float16 are unchanged.**
The exports call dense_divide(left->value, right->value, destination->value),
not cv::divide directly, and do not form/reassign a temporary quotient.

## Creation, reuse, ordering and overlap

OutputArray forwards create to the actual Mat/UMat header. A compatible
nonempty allocation returns without release, including an interior Region
with its retained parent stride/offset. Mismatched shape, depth or channels
release/recreate that header. Existing shallow aliases and Parent retain the
old allocation by reference counting. Whole reuse tests verify all quotient
pixels, alias observation and writes in both directions. Region tests check
every inside/outside pixel, retained Locate_Region/shape, and subsequent writes
through both headers into Parent. Ordinary mismatches are tested independently.

CPU loaders read both inputs before storing the corresponding results. The
4.x loops consume disjoint forward vector blocks, then unrolled/scalar tails.
5.0's SIMD loop explicitly avoids reloading an overlapping last block when
dst == src1 or dst == src2 (8/16/32/64/half macros); it uses scalar tails instead.
OpenCL's per-element/vector processing reads numerator and denominator into
work values before storedst. Unsupported OpenCL paths return false and native
arithm_op maps/falls back internally; that is not binding-side staging.

257-element public tests and actual-helper probes verify exact Destination=Left,
Destination=Right (old Left / old Right), and distinct same-layout aliases of
either, for integer, Float32, Float64 and Float16. Tests also use A/A with
independent, exact-self and shallow destinations. Nonzero finite A/A is one;
zeros are deliberately tested: integer 0/0 is zero, Float32/64 0/0 is NaN,
half matches the existing function. **No arbitrary partial Region overlap
support is claimed.**

## Integer conversion and zero denominators

4.x integer op_div_scale returns zero on a zero denominator; vector pre()
selects zero before integer packing. Nonzero values use floating computation
then saturate_cast / v_round, not integer truncation. 5.0 iscalar_div and
ivec_div likewise choose zero, followed by native conversion/packing.
OpenCL OP_DIV_SCALE uses a zero-denominator select for integer output and
convertToDT; `src/ocl.cpp` emits rounded `_rte` conversions (4.10:7071).
`include/opencv2/core/saturate.hpp` uses cvRound for UInt8/Int16/Int32 floating
conversion; `fast_math.hpp` uses SSE rounding or lrint/lrintf. Under ordinary
round-to-nearest environment, ties use nearest-even, not Ada integer `/`.

Pinned suite/probe values: **7/2=4, 5/2=2, -7/2=-4**; signed negative
denominators produce the corresponding negative quotient. UInt8, Int16 and
safe-range Int32 cover positive/negative/zero cases and 257-element SIMD/tails.
C3 checks every channel separately, including a zero divisor channel. No
Int32 overflow-policy assertion or binding-side numeric division is added.

## Floating special values and Float16

Float32/64 CPU operations use ordinary floating / or v_div, with no integer
zero select. OpenCL FP output also lacks that select. Tests classify every
element of repeated 1/+0, -1/+0, 0/0, 9/2, 1/-0 and -1/-0 using existing
Float32/64 classification APIs: +Inf, -Inf, NaN, 4.5, -Inf, +Inf respectively
on the tested builds. No infinity/NaN normalization or NaN payload identity.

4.x getDivTab has no half kernel. The existing templated helper converts both
Dense operands to Float32, divides, and converts result32 directly into the
actual CV_16F destination. All Dense temporaries remain UMat for UMat calls.
Native convertTo calls create and therefore reuses compatible half whole/
Region storage; retained aliases, Parent guard checks and later writes prove
the final narrowing reaches that storage rather than rebinding to a temporary.
5.0 getDivTab includes div16f; native half loops expand to Float32 and pack
back to half, retaining float zero semantics. Basic reuse isolates nonzero
denominators. Signed finite/nonintegral Region output, either operand/self/
shallow destinations, A/A zero, and zero-special-value parity against the
existing function are tested in the same build. Float16 classification/sign
parity is required, not a new cross-platform zero/NaN bit-pattern contract.

## Empty version boundary (existing helper unchanged)

Default/mixed compatibility and every two-empty UMat call follow the existing
dense_compatible_empty_mix / make_empty_arithmetic_result paths. Mat typed/typed
ordinary 4.x divides enter arithm_op, create typed output and invoke native HAL.
4.x half conversion releases empties. **5.0 binary cv::divide asserts equal
empty state and releases immediately when both are empty** (1348-1361), before
arithm_op/HAL. Thus Multiply's 5.0 typed-empty HAL finding must not be copied.

Start Destination nonempty Int16 C2, retain Alias. Let R mean release (retains
old Int16/C2); T mean typed create (takes typed operand depth/channels):

| Accepted operands | Mat 4.1/4.6/4.10 | Mat 5.0 | UMat all four |
|---|---|---|---|
| default/default | R | R | R |
| typed/typed UInt8 or Float32 | T | R | T |
| typed/typed Float16 | R | R | T |
| default/typed UInt8 | R | R | T |
| typed/default UInt8 | R | R | T |

R on the tested release 4.x builds leaves two zeroed extents; R on 5.0 clears
dimensions/Shape. T has dimensions=2, Shape=(0,0). Fresh function R results
have default UInt8 C1, dimensions=0; fresh T results match operand metadata.
Default/typed Float32/Float16 is not accepted by the unchanged Ada operand
depth policy. Typed/typed tests use C3 as well as the probe's C1. Old aliases
retain every old pixel and survive later writes independently of empty output.

All local configurations succeeded for these accepted empties. This is **not
a universal native empty-success promise**: HAL/platform behavior can differ.
Tests attempt both APIs independently and require success/error parity. Only
the source-identified 4.x typed/typed ordinary Mat division CALL_HAL rejection
is eligible: OpenCV_Error must name `HAL implementation div` and a return code.
Unrelated errors fail; no broad exception skipping. An observed hosted rejection
still requires exact HAL/platform diagnosis, not immediate normalization or a
new helper workaround. No such rejection was observed locally. Post-native
failure atomicity is not claimed.

## Public validation, ABI safety and UMat residency review

Both procedures call the same unchanged Validate_Arithmetic_Compatibility as
the functions. Matching 2-D operand policy remains intact, including rejection
of N-D by both APIs. Destination is not validated as an operand. Public shape/
depth/channel/N-D failures preserve every destination pixel and metadata.
No raw ABI dimension/type/channel/shape/denominator-value check was added.
Null guards protect handle dereferencing; exception translation is unchanged.

The only retained duplicate restriction is temporary Mat Destination rejection:
Ada Temporary_View and C++ temporary_external_view independently prevent
release/rebinding from severing the callback-scoped logical capability over
external/synthetic selected storage. The new export's `ABI safety:` comment
states that concrete reason. Compatible/incompatible temporary destinations
are rejected; temporary Left and Right are legal, with ordered quotient checks,
no capability escape, and unchanged view/parent/padding. Raw null/temporary
failures inspect dimensions, shape, depth/channels and every old pixel, selected
parent and external padding. No other public semantic policy is duplicated.

New production UMat code only calls dense_divide on actual UMat handles. No
To_Mat/To_UMat/getMat/ACCESS_READ/ACCESS_WRITE/host staging/Mat intermediates
were added. Test transfers are setup/observation only. Explicit OpenCL-disabled
AUnit evidence restores prior state on success and exceptions. OpenCV may
choose CPU fallback; GPU execution is not claimed.
No SPARK-compatible computation changed; GNATprove is not applicable.

## Reproducing the isolated actual-helper probe

Compile only this TU, since it includes the production shim. Replace opencv4
with opencv5 for the exact 5.0 image. No copied numeric implementation or
invented old-width safety correction is part of the probe.

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/divide_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/divide-probe
/tmp/divide-probe
```

Development host and four exact-version complete suites passed 1738/1738,
zero failed assertions/unexpected errors; 27 focused Divide cases registered.
Final exact committed-head results, remote/PR equality and hosted CI snapshot
are recorded in the PR/report rather than inferred from development runs.