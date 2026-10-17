# Task 043: reusable binary arithmetic destinations

## Starting gate

Fetched `origin/main`: `7956981a7881ce9121115f8cb65909aeb9edc439`, exactly
the expected PR #42 merge. Worktree was clean; no open PRs were listed.
Complete host baseline: 1661 executed/passed, 0 failed assertions, 0 unexpected
errors. Work starts on `feature/043-add-subtract-destination`.

## Exact authoritative source inspection

Clean local upstream trees were checked with `git describe --exact-match`,
`rev-parse HEAD`, and the upstream remote's peeled tags (`git ls-remote`).
Paths and inclusive line ranges below are relative to `modules/core/`.
Complete relevant add/subtract, arithm_op, OpenCL arithmetic, Dense create,
release and conversion implementations were read, not only API documentation.

| Exact tag | Peeled commit SHA | `src/arithm.cpp`: OpenCL / arithm_op / add-sub |
|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 481-598 / 602-879 / 881-907,925-939 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 467-584 / 588-867 / 869-895,913-927 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 467-584 / 593-907 / 909-977,995-1011 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 493-610 / 623-941 / 943-964,1008-1072,1159-1209 |

| Tag | `src/matrix_wrap.cpp`: OutputArray create / createSameSize / release | Dense N-D create: `src/matrix.cpp` / `src/umatrix.cpp` |
|---|---|---|
| 4.1.0 | 1189-1342 / 1651-1655 / 1657-1673 | 318-375 / 403-461 |
| 4.6.0 | 1160-1339 / 1659-1663 / 1665-1681 | 659-718 / 653-717 |
| 4.10.0 | 1160-1339 / 1659-1663 / 1665-1681 | 659-718 / 653-717 |
| 5.0.0 | 1466-1663 / 1954-1958 / 2042-2058 | 1085-1144 / 601-671 |

| Tag | Mat / UMat convertTo | Dense release | CPU arithmetic loops | OpenCL kernel |
|---|---|---|---|---|
| 4.1.0 | `src/convert.dispatch.cpp:174-225`; `src/umatrix.cpp:976-1039` | `include/opencv2/core/mat.inl.hpp:848-866,3774-3781` | `src/arithm.simd.hpp:115-143,330-459` | `src/opencl/arithm.cl:103-186,447-475` |
| 4.6.0 | `src/convert.dispatch.cpp:174-225`; `src/umatrix.cpp:1236-1299` | `src/matrix.cpp:547-565`; `src/umatrix.cpp:378-385` | `src/arithm.simd.hpp:115-143,330-459` | `src/opencl/arithm.cl:103-186,447-475` |
| 4.10.0 | `src/convert.dispatch.cpp:174-341` | `src/matrix.cpp:547-565`; `src/umatrix.cpp:378-385` | `src/arithm.simd.hpp:115-143,336-465` | `src/opencl/arithm.cl:103-186,479-507` |
| 5.0.0 | `src/convert.dispatch.cpp:56-246` | `src/matrix.cpp:1010-1021`; `src/umatrix.cpp:384-391` | `src/arithm.simd.hpp:128-232` | `src/opencl/arithm.cl:107-190,486-514` |

Public declarations/documentation in `include/opencv2/core.hpp`: 4.1:310-386,
4.6:324-401, 4.10:321-404, 5.0:252-335. Default mask is noArray; dtype is -1.
These describe per-channel arithmetic, in-place use, saturation, and the
explicit CV_32S exception to saturation.

Authoritative trees:
[4.1.0](https://github.com/opencv/opencv/tree/4.1.0/modules/core),
[4.6.0](https://github.com/opencv/opencv/tree/4.6.0/modules/core),
[4.10.0](https://github.com/opencv/opencv/tree/4.10.0/modules/core),
[5.0.0](https://github.com/opencv/opencv/tree/5.0.0/modules/core).

## Output creation and reuse

For matching unmasked same-type arrays, arithm_op calls
`_dst.createSameSize(*psrc1, type1)` before execution. The general path also
calls createSameSize. It obtains source dimensions/extents, and OutputArray's
Mat/UMat branch refers to the caller's actual header, not an independent
result. Ordinary mutable destinations do not have fixedType/fixedSize.

Mat::create returns without releasing existing nonempty storage when the
shape and packed type match. UMat::create does likewise, also preserving its
existing usage flags on 4.6/4.10/5.0 when USAGE_DEFAULT is supplied. Region
offset/stride/submatrix flags do not prohibit reuse. Neither continuity nor
unique ownership is required. Thus compatible whole and strided Region
destinations preserve their allocation and aliases. The 5.0 OutputArray
branch can return early for compatible 2-D layouts before Dense::create.

If dimensions, depth or channels differ, native create releases that header's
reference and creates output with operand shape/type. A Region detaches;
other headers keep the parent alive. Tests verify all parent guards, output
values/metadata, preserved geometry and bidirectional sharing; `Is_Submatrix`
alone is not used as proof. Sources have separate storage in Region tests.

The four exports call `dense_add_or_subtract` directly with
`destination->value`. They do not publish a temporary result via assignment,
copy or move. Allocation-returning APIs remain on their previous path.

## Exact aliases, order, and overlap boundary

CPU matching-type paths retain source order and pass both source pointers and
the destination pointer to the HAL kernels. 4.x loaders load both vectors
before storing each output vector; unrolled and scalar tails read the operands
for each element before its store. 5.0 explicitly avoids rewinding the last
SIMD vector when `dst == src1` or `dst == src2` (also in the half kernel),
using a scalar tail instead. This is important for length 257 in-place tests.
The general iterator path also recognizes identical source pointers when
converting blocks. There is no whole-output assignment preceding arithmetic.

Consequences for all four exact tags, Mat and UMat:

- Destination=Left and Destination=Right work in place.
- Subtract into Right reads old Right: `Left - old(Right)`, not reversed order
  and not a second subtraction from modified data.
- Distinct headers sharing exactly the same data/offset/shape/step/type have
  the same per-element behavior as exact native-header identity.
- Sources may be identical or distinct same-layout aliases: A+A is twice A,
  A-A is zero, with native saturation/precision. Output can share that storage.
- Arbitrary partial overlap is **unsupported**. Forward CPU traversal and
  independently scheduled OpenCL work-items can overwrite future source data.
  No blanket overlap guarantee, detection, or copy workaround is added.

AUnit verifies every element of nontrivial 257-element vectors for both
operations, both destinations, shallow aliases and aliased operands. Numerical
checks are independent of function parity, so shared helper bugs cannot make
the alias/order tests pass by corrupting both reference and actual results.

## OpenCL and CPU fallback

The OpenCL path requires dimensions <=2 and a UMat output. Vector-width
prediction and dtype conversion select the kernel; unsupported FP64, failed
kernel construction or execution return false to CPU fallback. OpenCL handles
keep the original UMat allocation/offset/stride. Binary kernel argument order
is src1, src2, dst, without restrict qualifiers. Each work-item reads both
elements in the add/subtract expression before storing its corresponding
result. Separate row-step and offset arguments support interior Regions.

CPU fallback obtains internal Mat headers after output creation and uses the
same HAL/iterator machinery as Mat. This mapping is OpenCV's implementation,
not binding-side staging. The production diff adds no getMat, ACCESS_READ/
WRITE, To_Mat, To_UMat, transfers or Mat intermediate for UMat. The existing
Float16 intermediates remain templated Dense, hence UMat for UMat calls.

The native probe explicitly disables OpenCL; AUnit also exercises explicit
UMat CPU mode with exception-safe restoration of the prior setting. Ordinary
tests allow normal OpenCV dispatch. The host AMD OpenCL compiler has the
preexisting missing `opencl-c-base.h` AST diagnostic and falls back. The exact
container matrix is CPU evidence, **not proof of execution on a usable GPU**.

## Integer and floating arithmetic

UInt8 addition saturates to 255; subtraction below zero saturates to zero.
Signed Int16 positive/negative arithmetic saturates to [-32768,32767]. Int32
does not saturate: upstream explicitly warns overflow may yield an incorrect
sign, not a new binding numerical policy. Channels are flattened into scalar
kernel width and processed independently (C3 is numerically tested). Ordinary
Float32/Float64 addition/subtraction preserves signs and operand order; tests
use the repository approximate-comparison helper.

### Old-output-depth subtraction hazard and narrow safety correction

4.1/4.6 have no extended subtraction function. 4.10 `arithm.cpp:1008` and
5.0:1206 select getSubExtFunc using `_dst.depth()` when dtype=-1, **before**
arithm_op recreates the destination. For byte operands and an old Float32
destination, getSubExtFunc (4.10:963-977; 5.0:1057-1072) selects sub8u32f or
sub8s32f. The matching-type path creates byte output, then invokes that
extended function (4.10:617-630; 5.0:648-662), which casts the output pointer
to float (4.10:923-947; 5.0:1008-1032). If implemented, it writes floats into
byte-sized output: out-of-bounds writes / wrong representation. Whether a
specific HAL returns NOT_IMPLEMENTED is not an ABI-safety guarantee.

The existing helper narrowly establishes the byte destination layout before
native subtract for nonempty 8U/8S same-type operands with old 32F output on
4.10+/5.x. This retains dtype=-1, same helper, actual destination, native
create/reallocation, and all Float16/empty policy. Empty input is excluded to
preserve native 5.0 early release and 4.x metadata. There is no public semantic
rejection here; its `ABI safety:` comment identifies the concrete overwrite.
Fresh allocation-returning outputs are 8U by default and do not select this
guard. AUnit covers the 8U/old-32F Region case; the standalone probe covers
both 8U and 8S at width 257, detachment and old-parent preservation.

## Float16: existing policy, with destination reuse

4.1/4.6/4.10 add/sub dispatch tables have a null half slot. The unchanged
`add_or_subtract_float16` widens both inputs to Float32 Dense, performs native
arithmetic, then `result32.convertTo(result, CV_16F)`. Here result is the
actual caller destination. Nonempty convertTo calls OutputArray create with
the half type, which reuses a compatible half allocation/Region. All four
probe images and public tests demonstrate alias/parent reuse at narrowing.

5.0 tables supply add16f/sub16f. Its half SIMD kernel expands to float and
packs back to half; its scalar tail computes in float too. The helper uses
native half arithmetic without a second compatibility layer. Function parity
is tested in the same build, including output aliasing either input. Exact
half bits are not promised invariant across architectures/SIMD placement.

## Empty outputs and version differences

The existing UMat safety branch handles both empty operands before OpenCL
vector-width prediction (empty UMat storage can be dereferenced otherwise).
It selects a typed operand for a default/typed mix regardless of order, calls
create(0,0,type) for typed input, or releases for default/default. No empty
semantic validation is added in the new exports.

For Mat, 4.x native arithmetic creates output from Left; default Left invokes
zero-dimensional create/release, typed Left gives typed 0x0 output. Half on
4.x widens empty inputs, and final conversion releases the output. 5.0 add
and subtract explicitly release for both empty operands before arithm_op.

Below, **F** is a fresh allocation-returning result; **D** starts nonempty
Int16 C2. Tuples are `(dimension count, depth, channels)`; 2-D empty extents
are `(0,0)`. Add/Subtract have identical observed metadata.

| Accepted operands | 4.1/4.6/4.10 Mat F / D | 5.0 Mat F / D | UMat F / D, all tags |
|---|---|---|---|
| default/default | (0,UInt8,1) / (2,Int16,2) | (0,UInt8,1) / (0,Int16,2) | F=(0,UInt8,1); D=(2,Int16,2) on 4.x, (0,Int16,2) on 5.0 |
| typed UInt8 or Float32 pair C3 | (2,input-depth,3) / same | (0,UInt8,1) / (0,Int16,2) | both (2,input-depth,3) |
| typed Float16 pair C3 | (0,UInt8,1) / (2,Int16,2) | (0,UInt8,1) / (0,Int16,2) | both (2,Float16,3) |
| default Left, typed UInt8 C1 Right | (0,UInt8,1) / (2,Int16,2) | (0,UInt8,1) / (0,Int16,2) | both (2,UInt8,1) |
| typed UInt8 C1 Left, default Right | both (2,UInt8,1) | (0,UInt8,1) / (0,Int16,2) | both (2,UInt8,1) |

Release preserves the old output type, hence F/D can differ without changing
arithmetic policy. 4.x release zeros extents without clearing dimensions in
these release builds; 5.0 clears dimensions. Old aliases keep all their pixels
and can be written independently. No cross-version normalization is added.
Public tests cover every accepted combination/order above, every old channel,
metadata, empty status and old-alias lifetime. Mixed non-UInt8/C1 types fail
existing operand compatibility and are not broadened by this task.

## Public policy, capability and failure review

Both destination procedures call the same existing
Validate_Arithmetic_Compatibility as functions. Its Rows/Columns queries
reject N-D; both function and procedure regressions verify OpenCV_Error and
unchanged destination state. No raw ABI 2-D/shape/depth/channel checks added.

New exports reject null Left/Right/Destination before dereferencing or native
mutation, retaining clear_error/exception translation. Temporary Mat output
is rejected independently by Ada Temporary_View and C++ temporary_external_view:
even compatible output handling can release/rebind the header and sever the
callback-scoped logical capability. Both exports carry that concrete
`ABI safety:` justification. External/selected views remain valid sources;
tests verify no capability escape and no source/padding mutation.

Raw and public pre-native failures preserve shape/depth/channels/every pixel,
external row padding and selected parent storage. There is no arbitrary
post-native failure-atomicity claim. No handle ownership transfer is added.

Validation-boundary review: the only repeated public restriction newly added
is temporary Mat destination rejection, required for callback capability
safety. The helper's narrow old-Float32 byte guard prevents native
out-of-bounds writes, not public rejection. Null checks are pointer safety;
Float16 and UMat-empty policy remain on the existing path. No public semantic
shape/depth/channel/2-D/saturation/empty contract is duplicated in exports.
No SPARK-compatible computation changed; no new formal-proof claim.

## Standalone probe and local evidence

`add_subtract_destination_probe.cpp` includes the production shim translation
unit to call the actual private helper, avoiding a duplicate half/empty policy.
Compile it alone, not together with a separate shim object:

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) \
  tests/probes/add_subtract_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/add-subtract-probe
/tmp/add-subtract-probe
```

Use opencv5 instead on the 5.0 image. Run from the repository root. Test-only
getMat is used for observation; it is not production UMat staging.
All four exact images passed aliases, vector/tails, Float16, Region reuse,
detachment, empty metadata and byte/old-output-depth checks. The host is
OpenCV 4.10.0. The focused addition registers 25 tests; complete precommit
host and all four exact-version suites passed 1686/1686 with zero failures
and errors. Exact final-commit reruns and head equality are recorded in the
PR/report, not inferred from these earlier checks.