# Task 046: reusable Abs_Diff destinations

## Starting gate and scope

Fetched `origin/main`: `4ebb727124bed45e9f1e76a6ede0664a26ca817a`, exactly
the expected PR #45 merge. Starting worktree clean, no open PRs listed.
Complete host baseline: 1738 executed/passed, zero failed assertions and
unexpected errors. Branch: `feature/046-abs-diff-destination`.
Only binary Mat/UMat Abs_Diff destination procedures and their two C exports
are added. Functions retain independent results. No dependency, CI, release,
scalar API, mask, output-depth or N-D public arithmetic changes.

## Exact authoritative source audit

The local upstream checkouts were independently verified clean with
`git rev-parse HEAD` and `git status --porcelain`. Remote annotated tags were
peeled using `git ls-remote https://github.com/opencv/opencv.git`.
Paths/ranges are inclusive, relative to `modules/core/`.

| Tag | Exact peeled SHA | `src/arithm.cpp`: OpenCL / arithm_op / getAbsDiffTab / absdiff |
|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 481-598 / 602-879 / 909-921 / 941-946 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 467-584 / 588-867 / 897-909 / 929-934 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 467-584 / 593-907 / 979-991 / 1013-1018 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 493-610 / 623-941 / 1073-1094 / 1211-1234 |

Authoritative trees: [4.1.0](https://github.com/opencv/opencv/tree/4.1.0),
[4.6.0](https://github.com/opencv/opencv/tree/4.6.0),
[4.10.0](https://github.com/opencv/opencv/tree/4.10.0),
[5.0.0](https://github.com/opencv/opencv/tree/5.0.0).
Exact declarations/documentation: `include/opencv2/core.hpp` at
4.1:1328-1349, 4.6:1376-1397, 4.10:1436-1460, 5.0:1377-1401.
These specify independent channel processing, same-size/type output, and no
CV_32S saturation guarantee (overflow can give a negative result).

| Tag | `src/arithm.simd.hpp` | `src/opencl/arithm.cl` |
|---|---|---|
| 4.1 / 4.6 | 161-177 scalar; 258-288 vector operators; bin_loader/bin_loop through dispatcher at 541 | 188-195 operation, binary kernel 447-475 |
| 4.10 | 161-177 scalar; 258-294 vectors; 334-547 loaders/loops/dispatch | 188-195 operation, binary kernel 479-507 |
| 5.0 | 128-198 loops; 236-251 operations; dispatcher at 850 | 192-199 operation, binary kernel 486-514 |

The complete relevant arithm_op paths were inspected: fast array path,
general array path, scalar branch, conversions, output create, OpenCL dispatch
and CPU fallback. checkScalar is in `src/precomp.hpp`: 4.1:273-299,
4.6:273-299, 4.10:300-326, 5.0:303-329 (InputArray at 317).

### Output creation, reuse, release and half conversion

| Tag | `src/matrix_wrap.cpp`: create / createSameSize / release | N-D Mat / UMat create |
|---|---|---|
| 4.1 | 1189-1342 / 1651-1655 / 1657-1673 | `src/matrix.cpp:318-375`, `src/umatrix.cpp:403-461` |
| 4.6 / 4.10 | 1160-1339 / 1659-1663 / 1665-1681 | `src/matrix.cpp:659-718`, `src/umatrix.cpp:653-717` |
| 5.0 | 1466-1663 / 1954-1958 / 2042-2058 | `src/matrix.cpp:1085-1144`, `src/umatrix.cpp:601-671` |

Release: 4.1 `include/opencv2/core/mat.inl.hpp:848-866,3774-3781`;
4.6/4.10 `src/matrix.cpp:547-565`, `src/umatrix.cpp:378-385`;
5.0 `src/matrix.cpp:1010-1021`, `src/umatrix.cpp:384-391`.
Mat conversion: 4.1/4.6 `src/convert.dispatch.cpp:174-225`,
4.10:248-304, 5.0:131-190. UMat convertTo was also inspected in umatrix.cpp
on 4.1/4.6 and convert.dispatch.cpp on 4.10/5.0.

OutputArray returns without replacing compatible nonempty 2-D headers;
Mat/UMat create likewise returns for matching extents/type. Thus compatible
whole storage and strided interior Regions retain data, parent and aliases.
Mismatches release only this header's reference and create operand layout;
old parent/alias references survive. No temporary-result-to-destination
assignment is used in the new exports.

## OpenCV 5 scalar-helper audit: no old-output layout hazard

4.1/4.6/4.10 binary absdiff passes getAbsDiffTab directly to arithm_op.
No old-destination-depth selector exists in these binary entry points.

5.0 adds `getAbsDiffScalarFunc(sdepth, dst.depth())` before arithm_op:
`src/arithm.cpp:1097-1155` contains the complete wrappers and selector.
The selector offers only CV_32F->CV_32F, CV_8U->CV_8U and CV_32S->32-bit
unsigned storage. `absDiffScalar32s32uWrapper` casts dst to `uint32_t*` and
calls `cv_hal_absDiffScalar32s32u`: each channel still occupies exactly four
bytes, the same as CV_32S. Unsigned interpretation is not a storage widening.
The probe asserts equal 32-bit storage sizes.

**Public matching Mat/Mat and UMat/UMat cannot invoke scalarFunc.** For
matching ordinary 2-D layouts, kinds, dimensions, sizes, type and scalar
classification match; fast path 643-663 creates source type then invokes
getAbsDiffTab (extendedFunc is null). This includes 1x1 C1, 1x4 C1 and
1x1 C4: scalar-looking does not mean scalar-operation. For matching layouts
whose continuity flags give unequal checkScalar classifications, the fast
path can be bypassed, but the general branch still has `haveScalar=false`:
neither size/dimension/channel mismatch nor MATX applies. It uses the
array iterator branch 777-857, never scalarFunc at 901-902.

**Raw callers can reach scalar handling:** e.g. a 2x257 array and a 1x1
CV_64F Mat, rejected by public compatibility but accepted natively. The
scalar branch creates array-depth output before invoking the helper; helper
selection is either null or same-width. For opaque Mat operands, absdiff's
entry-point checkScalar(..., MATX) rejects the Mat kind: scalar-first CV_64F
therefore keeps sdepth=CV_64F and selects no helper, even though arithm_op can
subsequently swap that scalar. Array-first may select the same-width helper.
An old destination with differing
depth disables the helper rather than selecting a widened write. Channel
counts are passed explicitly. This is not a Subtract/Multiply extended-width
write defect. Native HAL errors/semantics remain native, not binding policy.

**Decision: leave dense_abs_diff unchanged; add no preallocation correction.**
Matching scalar-like layouts and unusual raw scalar-compatible layouts are
probed with compatible/mismatched old depths. No storage-width mismatch was
found. No scalar public API is introduced.

## Aliasing and SIMD/tails

Native kernels load both current operands before writing the corresponding
result. 4.x vector loaders/unrolled loops/scalar tail preserve exact storage
aliases. 5.0's loop explicitly avoids rereading an already-written tail
vector when dst==src1 or dst==src2; native half loop has the same restriction.
Exact Destination=Left/Right and distinct same-layout shallow headers are
supported. Tests inspect **all 257 elements**, including tails, across UInt8,
Int16, safe Int32, Float32, Float64 and Float16. Operands may alias each other:
finite/integer A/A is zero, with independent, exact and shallow destinations.
Arbitrary partially overlapping Regions remain **unsupported**: no overlap
detection or defensive copies were added, and kernels do not promise to
preserve shifted source pixels for later iterations.

## Numeric and floating behavior

UInt8 is absolute difference, not wrapped subtraction: 10/200->190,
250/20->230, 50/80->30; C3 channels are independent. Int16 saturates
abs(-32768-0) to 32767 in vector and scalar tails. Safe Int32 numeric cases
are asserted. 4.x scalar `c_absdiff<int>` subtracts in signed int, with vector
unsigned difference reinterpreted signed; 5.0 scalar uses std::abs of signed
subtraction. C++ signed overflow / abs(INT_MIN) is not a portable numerical
contract. The local probe observes native signed overflow but does not assert
it as portable, and Ada does not attempt a correction or saturation policy.

Float32/Float64 positive/negative finite differences follow native abs(a-b).
Source floating scalar specializations use std::abs (4.x explicitly comments
that this prevents -0); SIMD uses v_absdiff. OpenCL uses fabs(a-b).
Classification tests/probe cover finite vs either infinity -> positive
infinity, equal +infinity/-infinity -> NaN, NaN vs finite and finite vs NaN ->
NaN, and NaN/NaN -> NaN including A/A aliases. Payloads are not compared.
Both signed-zero orders are zero; exact CPU matrix tests/probes check positive
zero, not a new architecture-independent bitwise contract.

## Float16: unchanged helper policy

The 4.x dispatch table's half entry is null. Production helper widens Left
and Right to Float32 Dense, computes native absdiff, and narrows into the
**actual caller Destination**. For Dense=UMat all intermediates remain UMat.
Final convertTo creates/reuses compatible half whole/Region storage. Retained
aliases/parent writes demonstrate final narrowing reuse, rather than merely
observing Is_Submatrix. On 5.0 getAbsDiffTab includes native absdiff16f, with
float32-expanded SIMD/scalar half operation and native narrowing. Procedures
are compared against functions in the same build, including classification.
No architecture-independent NaN payload/bit identity is promised.

## Empty behavior: preserve native version/order differences

Let **R** mean release Destination, retaining old Int16 C2 depth/channels;
**T(D)** means create typed-empty 2-D operand depth D, C1. Procedure starts
with nonempty 2x3 Int16 C2 and a retained shallow alias. Fresh function R
results remain default UInt8 C1, dimension count 0; T results have dims=2,
Shape=(0,0), D C1. Old aliases survive every pixel and later independent writes.

| Inputs | Mat 4.1/4.6/4.10 | Mat 5.0 | UMat all four through unchanged helper |
|---|---|---|---|
| default/default | R | R | R |
| typed/typed UInt8 | T(UInt8) | R | T(UInt8) |
| typed/typed Float32 | T(Float32) | R | T(Float32) |
| typed/typed Float16 | R | R | T(Float16) |
| default/typed UInt8 | R | R | T(UInt8) |
| typed/default UInt8 | T(UInt8) | R | T(UInt8) |

On release, tested 4.x release builds keep dims=2 and zero extents; 5.0 clears
dimensionality/Shape. 4.x matching typed empties enter fast createSameSize and
zero-size HAL. A mixed pair enters general array path with the first source's
dimensions, explaining the order difference. Half conversion releases empty
intermediates and final Destination on 4.x. 5.0 absdiff checks equal emptiness
and explicitly releases/returns before all selectors/creation.

UMat + both empty retains the existing ABI-safety bypass: 4.10 OpenCL
vector-width prediction may dereference empty storage before deciding CPU
fallback. make_empty_arithmetic_result chooses a typed operand if either is
typed; otherwise releases. This also intentionally precedes 5.0 absdiff.
Default/typed floating mixes remain rejected by the unchanged Ada depth
policy. Tests do not normalize metadata or broadly skip exceptions. Local
success is not a universal HAL success guarantee: if a hosted empty HAL fails,
the exact existing function path must be diagnosed and only narrow parity
assertions considered. No arbitrary post-native failure atomicity is claimed.

## Validation boundary and residency review

Both procedures call the unchanged Validate_Arithmetic_Compatibility(Left,
Right), exactly like the functions' validation path; Destination is not an
operand. Shape/depth/channel and N-D public failures occur before mutation
and preserve dimensions, shape, type and all destination/alias pixels.
Raw exports only reject null handles and temporary Mat destinations, then
call dense_abs_diff(left->value,right->value,destination->value), with existing
exception translation. No raw 2-D/shape/depth/channel/finiteness guards added.

The sole retained duplicate restriction is temporary Mat Destination:
Ada Temporary_View and raw temporary_external_view each reject compatible
and mismatched external/selected output views. The concrete `ABI safety:`
reason is that native release/rebind would sever the callback-scoped
capability over caller/selected storage. Tests preserve metadata, logical
pixels, selected parent pixels and external row padding for these and raw
null failures. Temporary Left or Right remains legal; ordinary output is
independent and no backing-storage capability escapes. No other public
semantic validation is duplicated in the new exports.

New UMat production code passes only native UMat handles to the existing
Dense helper. No To_Mat/To_UMat/getMat/ACCESS_READ/ACCESS_WRITE, host staging
or Mat arithmetic intermediates were added. Test transfers are setup and
observation only. Explicit OpenCL-disabled tests restore prior state on
success/exception. OpenCV CPU fallback is permitted; GPU execution is not
claimed. No SPARK-compatible computation changed; GNATprove is not applicable.

## Reproduction and evidence

Compile this probe translation unit alone: it includes the actual production
shim, not a copied helper. For 5.0 substitute opencv5 for opencv4.

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/abs_diff_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/absdiff-probe
/tmp/absdiff-probe
```

Focused suites register 29 cases, retaining all previous arithmetic tests.
Final exact committed-head complete-suite/probe results, warning/link/format
gates and hosted CI snapshot are reported with the PR, not inferred from
earlier development runs. All four local actual-helper probes passed, including
scalar-first/array-first raw native-compatible shapes, matching scalar-like
arrays, and the raw general N-D array path (not exposed by public Abs_Diff).
Int32 overflow observations were -2147483648 at vector-start/tail in each
local exact build, not a portable guarantee. No empty HAL rejection occurred
in these local builds. The host's installed AMD OpenCL compiler emitted
missing LLVM 17 header diagnostics during native kernel attempts; OpenCV
fell back and the complete suite passed. These are runtime driver diagnostics,
not C++/Ada build warnings, and are not evidence of successful GPU execution.

Test observation widens half storage before channel extraction: raw 4.x half
channel extraction is unsupported (and older builds can fault), unrelated to
Abs_Diff. No extraction workaround was added to production. An extra strict
C-header smoke check found a preexisting line-59 `struct opencv_core_scalar`
parameter-scope warning, reproduced against unchanged starting origin/main;
it is outside this task and was not repaired. Strict production C++ build and
shared `--no-undefined` linking passed.