# Task 044: reusable Multiply destinations

## Starting gate

Fetched `origin/main`: `6d201dc5db2b7eb3bb80b5da4b375f611e577c3d`, the
expected PR #43 merge. Clean worktree; no open PRs listed. Complete host
baseline: 1686 executed/passed, zero failed assertions/unexpected errors.
Branch: `feature/044-multiply-destination`. Scope is Multiply only.

## Exact authoritative sources

Clean upstream checkouts were verified with `git describe --exact-match`,
`git rev-parse HEAD`, `git status --porcelain`, and the remote peeled tags
from `git ls-remote https://github.com/opencv/opencv.git`. Inclusive line
ranges below are relative to `modules/core/` in these exact commits:

| Tag | Peeled SHA | `src/arithm.cpp`: OpenCL / arithm_op / multiply |
|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 481-598 / 602-879 / 1000-1007 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 467-584 / 588-867 / 986-993 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 467-584 / 593-907 / 1118-1127 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 493-610 / 623-941 / 1337-1346 |

Authoritative trees: [4.1.0](https://github.com/opencv/opencv/tree/4.1.0),
[4.6.0](https://github.com/opencv/opencv/tree/4.6.0),
[4.10.0](https://github.com/opencv/opencv/tree/4.10.0),
[5.0.0](https://github.com/opencv/opencv/tree/5.0.0).

| Tag | OutputArray create / createSameSize / release (`src/matrix_wrap.cpp`) | Mat / UMat N-D create (`src/matrix.cpp` / `src/umatrix.cpp`) |
|---|---|---|
| 4.1.0 | 1189-1342 / 1651-1655 / 1657-1673 | 318-375 / 403-461 |
| 4.6.0 | 1160-1339 / 1659-1663 / 1665-1681 | 659-718 / 653-717 |
| 4.10.0 | 1160-1339 / 1659-1663 / 1665-1681 | 659-718 / 653-717 |
| 5.0.0 | 1466-1663 / 1954-1958 / 2042-2058 | 1085-1144 / 601-671 |

| Tag | Mat / UMat convertTo | Mat / UMat release | CPU multiply and SIMD/tails |
|---|---|---|---|
| 4.1.0 | `src/convert.dispatch.cpp:174-225`; `src/umatrix.cpp:976-1039` | `include/opencv2/core/mat.inl.hpp:848-866,3774-3781` | `src/arithm.simd.hpp:179-192,330-459,1414-1550` |
| 4.6.0 | `src/convert.dispatch.cpp:174-225`; `src/umatrix.cpp:1236-1299` | `src/matrix.cpp:547-565`; `src/umatrix.cpp:378-385` | `src/arithm.simd.hpp:179-192,330-459,1414-1550` |
| 4.10.0 | `src/convert.dispatch.cpp:248-341` | `src/matrix.cpp:547-565`; `src/umatrix.cpp:378-385` | `src/arithm.simd.hpp:179-192,336-465,1424-1562` |
| 5.0.0 | `src/convert.dispatch.cpp:131-246` | `src/matrix.cpp:1010-1021`; `src/umatrix.cpp:384-391` | `src/arithm.simd.hpp:513-710` |

Public declarations: `include/opencv2/core.hpp`: 4.1:387-411,
4.6:402-426, 4.10:407-432, 5.0:338-363. Defaults are scale=1, dtype=-1;
output has operand size/type. Products saturate except CV_32S, for which
overflow/sign behavior is not promised. No binding overflow policy is added.

## Old destination depth: concrete write-width hazard

4.1 and 4.6 have **no getMulExtFunc** or extended multiply wrappers. Their
multiply directly calls arithm_op using getMulTab; same-type dtype=-1 output
is created with operand type before ordinary byte kernels are chosen.

4.10 `src/arithm.cpp:1034-1064` and 5.0:1250-1280 define:

- mul8u16uWrapper casts dst to `ushort*` (4.10:1040, 5.0:1256).
- mul8s16sWrapper casts dst to `short*` (4.10:1056, 5.0:1272).

getMulExtFunc (4.10:1078-1092, 5.0:1295-1309) selects exactly:
UInt8/UInt8/UInt16 or Int8/Int8/Int16. multiply evaluates
`dtype < 0 ? dst.depth() : dtype` **before** calling arithm_op
(4.10:1123-1126, 5.0:1342-1345).

The matching fast path creates operand-type output at 4.10:617 / 5.0:648,
then executes extendedFunc at 625-626 / 656-657. With dtype=-1 the old word
destination can therefore select two-byte writes into one-byte storage.
The general array iterator similarly creates output at 721 / 750 and tries
extendedFunc before conversion at 790-791 / 819-820, with direct dptr on the
unmasked path and byte-sized pointer increments. This is not limited to the
continuous fast path. Platform HAL returning NOT_IMPLEMENTED happens to
avoid the write, but is **not** an ABI-safety argument.

Both pairs require correction. The helper now uses native Dense::create
before cv::multiply, only on 4.10+/5.x, only for nonempty Left and same packed
operand types, and only for UInt8+old UInt16 or Int8+old Int16. The correction
creates operand shape/type so getMulExtFunc sees byte depth and returns null.
There is no 2-D guard, no public-policy rejection, no unconditional allocation,
no changed dtype, no temporary result assignment. Empty branches are unchanged.
Fresh allocation-returning results start UInt8 C1, so neither pair applies.
Compatible destinations, half arithmetic, and other old depths are unaffected.
Native create detaches incompatible Region headers; old aliases/parent keep
the reference-counted allocation. The `ABI safety:` comment names the concrete
ushort/short write-width mismatch and possible out-of-bounds writes.

The standalone probe includes the actual production shim and link-wraps its
cv::multiply call. Its wrapper checks the **actual pre-native destination**,
not the final result after OpenCV's create. Against the uncorrected helper on
host 4.10 it rejected UInt8/old UInt16 before unsafe execution. With correction
it checks byte shape/type and absence of both hazardous selector pairs; four
audited calls cover Mat and UMat, UInt8 and Int8. It then delegates to native
multiply and verifies all 2x257 saturated products, detached Region/old alias,
every old parent pixel, and independent later writes. Thus safety does not
depend on whether the installed HAL implements either extended function.

The starting-shim audit mode was also run on all four exact versions. On 4.10
and 5.0 it observed both UInt8/old UInt16 and Int8/old Int16 pairs at the native
call for both Mat and UMat and intercepted execution. On 4.1 and 4.6 it records
the source-established absence of an extended selector. No out-of-bounds native
write was deliberately executed. The positive host probe additionally passed
AddressSanitizer/UndefinedBehaviorSanitizer with leak detection; the installed
OpenCV library itself is not sanitizer-instrumented.

## Reuse, exact aliasing, and execution paths

Matching unmasked same-type operands use createSameSize with operand type.
The general path resolves dtype=-1 to input type, then uses the same creation
mechanism. OutputArray refers to the caller's actual mutable Mat/UMat header;
neither fixedType nor fixedSize applies. Dense::create early-returns on equal
nonempty layout/type, including strided Region storage, without releasing it.
Mismatch releases only the output header and creates independent storage.

Exact Destination=Left/Right requires no creation because shape/type already
match. The CPU kernels load both input elements/vector blocks before storing
the corresponding output. 4.x bin_loop advances forward and uses scalar tails;
5.0 explicitly avoids reprocessing an overlapping vector tail when dst equals
either source (arithm.simd.hpp:537-540,576-579,612-615,645-648,678-681).
Distinct shallow headers sharing identical layout/storage have the same data
pointers and semantics. Operands may also share storage: A*A works with an
independent output, exact in-place output, or same-layout shallow output.
Tests inspect every one of 257 elements, including nontrivial signed values,
UInt8/Int16 saturation, Float32/Float64/Float16. This supports **exact/same-layout
aliasing only**; no arbitrary partially overlapping Region guarantee exists.

The OpenCL attempt follows output creation in fast and general paths.
ocl_arithm_op obtains destination type after create, predicts vector width,
sets ReadOnly source and WriteOnly unmasked output kernel arguments, and
delegates or returns false to native CPU fallback. `src/opencl/arithm.cl`:
4.1/4.6:103-227,447-475; 4.10:103-227,479-507; 5.0:107-231,486-514.
OP_MUL reads both same-index operands before storing; offsets/strides are
passed separately, preserving compatible Regions. No binding-side getMat,
ACCESS_READ/WRITE, transfers, host staging, or Mat arithmetic intermediates
are introduced. Float16 Dense intermediates for UMat remain UMat. OpenCV's
own getMat fallback is internal library behavior, not a residency guarantee.
The explicit CPU test disables/restores OpenCL and repeats the focused cases.
The compatibility images have no usable OpenCL device; GPU execution is not
claimed. Host OpenCL compiler diagnostics can fall back successfully to CPU.

## Float16

4.x getMulTab ends at mul64f, with no half kernel. Existing helper widens both
Dense operands to Float32, multiplies at scale=1/dtype=-1, and narrows once
into the actual destination. convertTo creates output through OutputArray;
compatible half whole/Region storage is reused. Sources are widened before
final output writes, so exact/same-layout aliases remain safe. 5.0 getMulTab
contains mul16f (arithm.cpp:1282-1293) and the helper uses native half multiply.
Procedure/function parity in the same build, bidirectional alias writes, and
Region parent survival establish actual half reuse, not just submatrix flags.
No new half policy or cross-architecture/SIMD bit-identity promise is added.

## Empty representations (observed, not normalized)

Default/typed mixes accepted by current Ada validation have UInt8 C1 types;
other mixed types/channels fail validation. Both operand orders are tested.
Typed/typed tests cover UInt8, Float32, Float16 C3; default/default is UInt8 C1.
F is fresh function result, D starts nonempty Int16 C2 with retained alias.
Tuple below is (dimensions, depth, channels). 2-D empty Shape is (0,0), 0-D
empty Shape is the null array. All results are Is_Empty.

| Operands | Mat 4.1/4.6/4.10 F / D | Mat 5.0 F / D | UMat all versions F / D |
|---|---|---|---|
| default/default | (0,UInt8,1) / (2,Int16,2) | (0,UInt8,1) / (0,Int16,2) | F=(0,UInt8,1); D=(2,Int16,2) on 4.x, (0,Int16,2) on 5.0 |
| typed UInt8 or Float32 pair C3 | both (2,input-depth,3) | both (2,input-depth,3) | both (2,input-depth,3) |
| typed Float16 pair C3 | (0,UInt8,1) / (2,Int16,2) | both (2,Float16,3) | both (2,Float16,3) |
| default/typed UInt8 C1, either order | (0,UInt8,1) / (2,Int16,2) | (0,UInt8,1) / (0,Int16,2) | both (2,UInt8,1) |

Unlike Add/Subtract, dense_multiply handles both default/typed Mat orders by
release. Typed Mat multiplication (except 4.x half conversion) uses native
create rather than the 5.0 Add/Subtract empty-release shortcut. Old destination
type metadata survives release. 4.x release zeros extents but retains dimension
count in these release builds; 5.0 clears dimensions. Every old alias pixel,
including second channel, survives and remains independently writable.
The existing helper avoids default-empty 5.0 output scalar/totals mismatch and
typed-empty UMat OpenCL vector prediction; no empty policy was modified here.

### Hosted ARM64 HAL finding and corrective test

The first review head `cb45a1d6951d0d0426586b7baf38f937e8a2b21d` passed
all five local suites, but push run 37171086579 and PR run 37171089018 each
reported 1710/1711 on macOS ARM64/Homebrew OpenCV 5.0.0. The **existing
allocation-returning function** rejected typed-empty UInt8 Mat through
`arithm.simd.hpp:914`: `kleidicv_mul8u_with_fallback returned -1`. No procedure
had yet been attempted. Other hosted enabled jobs succeeded.

The exact 5.0 source's matching fast path creates typed-empty output before
calling mul8u with empty/null data. `arithm.simd.hpp:880-914` dispatches through
CALL_HAL before CPU loops; a HAL error other than NOT_IMPLEMENTED becomes
cv::Exception rather than a fallback. The tag's `hal/kleidicv/kleidicv.cmake`
pins KleidiCV 26.03, archive hash `b85a745bfe0e87e67e30be9533eb6b24`.
Raw Web retrieval hit a JavaScript challenge, but a native Git checkout of
tag 26.03 succeeded at `b1dbf474b8685b97a64d03e828b359fbdc050d1f`.
`adapters/opencv/kleidicv_hal.h:586-602` maps scale=1 mul8u to saturating
multiply; lines 201-203 map every non-OK status to CV_HAL_ERROR_UNKNOWN.
`kleidicv/src/arithmetics/multiply_neon.cpp:66-84` and `multiply_sc.h:47-64`
check all pointers before image dimensions/loops. The byte specialization
`kleidicv/include/kleidicv/utils.h:388-405` rejects nullptr regardless of
height. Thus empty null pointers yield the observed HAL error before memory
access, not an out-of-bounds write. No safety reason justifies changing the
existing helper's native empty policy.

The table above describes successful local configurations, **not** a universal
empty-success contract. Production empty handling is unchanged. The corrective
test attempts both function and procedure independently, requires success/error
parity, and accepts only the observed OpenCV_Error for typed UInt8 Mat on 5.0
with the named KleidiCV HAL/return diagnostic. It still checks typed-empty
destination shape/depth/channels after native creation, every old alias pixel,
and independent later writes, and continues the other depth/order cases.
Other exceptions fail the test. No broad catch/skip or helper normalization was
introduced; native post-failure destination preservation remains unpromised.

## Public validation / capability boundary review

Both procedures invoke the unchanged Validate_Arithmetic_Compatibility used
by the functions. Rows/Columns reject N-D; regressions verify both overloads
raise OpenCV_Error and preserve every destination pixel and metadata. Destination
is not included in operand validation. No raw shape/depth/channel/2-D/saturation
policy checks were added. Pre-native null checks protect handle dereferencing;
exception containment/translation is unchanged. No post-native failure atomicity
promise or ownership transfer was introduced.

The retained duplicate restriction is temporary Mat destination rejection:
Ada Temporary_View and C++ temporary_external_view independently prohibit
release/rebinding from severing the callback-scoped logical capability over
external/synthetic selected storage. The new export has an `ABI safety:` comment
with that reason. Compatible and incompatible temporary outputs are rejected;
temporary Left and Right remain permitted, with ordinary independent output
and unchanged view/parent/padding. Raw null and temporary pre-native failures
verify dimensions, shape, depth, channels, every pixel, selected parent and
external padding. The old-depth helper condition is a memory-layout correction,
not public semantic validation; no other public policy is duplicated.
No SPARK-compatible computation changed, so GNATprove is not applicable.

## Reproducing the isolated probe

Run from repository root; compile only this translation unit, since it includes
the shim. Use opencv5 in place of opencv4 for the 5.0 image. GNU ld --wrap
observes the native call boundary without modifying the upstream library.

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/multiply_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core \
  -Wl,--wrap=_ZN2cv8multiplyERKNS_11_InputArrayES2_RKNS_12_OutputArrayEdi \
  -o /tmp/multiply-destination-probe
/tmp/multiply-destination-probe
```

All four exact images passed old-depth, alias/vector/tail, half, Region and
empty probes. Complete development suites on host and all four exact versions
passed 1711/1711 with zero failures/errors. The focused suite registers 25
behavioral cases. Final exact
commit suite/probe results and local/remote/PR head equality are recorded in
the PR/report, not inferred from earlier development runs.

For the negative layout experiment, compile the same probe against the starting
shim (from the recorded starting commit) and pass `--audit-old-layout`. This
intercepts and reports both signed/unsigned old-word layouts without executing
the potentially unsafe native call. The corrected helper must fail this negative
experiment because its native-call depth is already byte; the normal probe is
the positive safety/reuse test. This optional audit mode never belongs in the
production binding.