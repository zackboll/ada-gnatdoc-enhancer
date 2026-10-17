# Task 047: reusable minimum/maximum destinations — source findings

## Starting gate

- Fetched `origin/main`: `4da9d35ea21e1b2efe96296243ea668b488c6326`.
- Worktree initially clean; `gh pr list --state open` returned no PRs.
- Branch: `feature/047-min-max-destination`, based on that main SHA.
- Complete host baseline: 1767 executed, 1767 passed, zero failed assertions
  and unexpected errors. Host pkg-config OpenCV: 4.10.0.
- An initial special-value alias parity gate exposed the native 5.0 divergence
  below. The user authorized the narrow contract correction: independent outputs
  retain function parity; exact/shallow aliases retain native floating-special
  behavior, while ordinary finite/integer correctness remains mandatory.
- Implementation adds only the requested four public overloads and C exports.
  No dependency, CI, version, release, scalar API or N-D policy changes.

## Exact source identities

Reconfirmed with remote `git ls-remote https://github.com/opencv/opencv.git`
annotated tag peeling and clean local upstream checkouts at identical HEADs.

| Tag | Peeled SHA |
|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` |

All paths below are relative to `modules/core/`. Audited declarations:
`include/opencv2/core.hpp` Mat/UMat min/max overloads at 4.1:1427-1452,
4.6:1475-1500, 4.10:1538-1563, 5.0:1479-1504. These are selection operations,
with separate channel processing and output shape/type following the arrays.

| Tag | `src/arithm.cpp`: OpenCL / binary_op / tables / min-max exports |
|---|---|
| 4.1 | 89-165 / 169-342 / 344-370 / 406-449 |
| 4.6 | 71-147 / 151-328 / 330-356 / 392-435 |
| 4.10 | 71-147 / 151-328 / 330-356 / 392-435 |
| 5.0 | 71-147 / 151-328 / 330-374 / 410-453 |

## Binary, scalar and old-output-layout findings

All exact tags dispatch cv::min/max to binary_op with getMinTab/getMaxTab,
no mask, and OCL_OP_MIN/MAX. Matching 2-D Mat/Mat or UMat/UMat shapes/types
enter the fast array/array branch, even for 1x1 C1, 1x4 C1 and 1x1 C4.
This happens before scalar detection.

Fast output creation is `create(sz1,type1)` on 4.1/4.6 and
`createSameSize(*psrc1,type1)` on 4.10/5.0. The general iterator and scalar
branches also call createSameSize with the array operand type before accessing
output storage. Scalar-first raw inputs are swapped to put the array first;
the scalar is converted/unrolled to that array's type. CPU table dispatch uses
source depth, never the old destination depth. OpenCL sets dstDepth=srcdepth
and receives an already-created destination before width prediction.

No equivalent of old-destination getSubExtFunc/getMulExtFunc exists here.
Probe mismatch cases with old 8U C1, 16S C2 and 64F C4 outputs, and raw
array/scalar and scalar/array calls, completed across all four versions.
There is no evidence of an old-output write-width hazard. **dense_min_max
remains unchanged**; defensive preallocation is not justified.

OutputArray create/release and Mat/UMat create paths were inspected:

| Tag | `src/matrix_wrap.cpp`: create / createSameSize / release | Mat / UMat create |
|---|---|---|
| 4.1 | 1189-1342 / 1651-1655 / 1657-1673 | `src/matrix.cpp:318-375`, `src/umatrix.cpp:403-461` |
| 4.6 / 4.10 | 1160-1339 / 1659-1663 / 1665-1681 | `src/matrix.cpp:659-718`, `src/umatrix.cpp:653-717` |
| 5.0 | 1466-1663 / 1954-1958 / 2042-2058 | `src/matrix.cpp:1085-1144`, `src/umatrix.cpp:601-671` |

Matching nonempty outputs return without releasing/replacing storage, including
compatible Regions. Mismatches release only that header's reference, preserving
old shallow aliases. No partial-overlap support is inferred.

## Native floating alias behavior and corrected contract

The actual private helper probe compiled against all four exact-version images
with C++17, Wall/Wextra/Wpedantic/Werror. It uses OpenCL-disabled Mat and UMat,
with useOptimized both false and true, and 257-element floating vectors.

4.1, 4.6 and 4.10: zero special-value alias parity failures in the exercised
matrix. 5.0: **384 failed alias/pair/depth/backend/optimization combinations**.
These are classification or zero-sign failures, not NaN payload differences.
They occur for both operations, Float32/Float64/Float16, Mat/UMat CPU, into Left,
into Right, and distinct exact-layout shallow aliases of either input.

Concrete 5.0 minimum example (identical observations for maximum):

```
Left:  257 Float32 quiet NaNs
Right: 257 Float32 values 3
independent result: first=3, tail=3
actual Destination=Left: first=3, tail=NaN
```

For finite Left=3 and Right=NaN, the independent result tail is NaN, while
the exact-alias tail is 3. Infinity-only cases agree in the exercised matrix.

Signed-zero example on 5.0:

```
Left: +0; Right: -0
independent minimum/maximum tail: -0
exact-alias minimum/maximum tail: +0
```

Reversing the operands reverses the selected zero signs. Both signs are
numerically zero, but required same-build zero-sign parity fails.

### Exact source explanation

4.x `src/arithm.simd.hpp:145-159` implements scalar c_min/c_max via std::min/max;
vector op_min/op_max at 238-254 uses v_min/v_max. 4.x vector loops process
full blocks then scalar tails (4.1/4.6:415-455, 4.10:421-461), without 5.0's
alias-dependent final-vector backtracking.

5.0 `src/arithm.simd.hpp:128-154`:

```
if (x + simd_width > width) {
    if (((x == 0) | (dst == src1) | (dst == src2)) != 0)
        break;
    x = width - simd_width;
}
```

An independent output processes its end with a backed-up SIMD block; exact
alias output breaks and uses scalar std::min/max at 150-151. Native half has
the same branch at 156-182, with float expansion/packing. Instantiations at
233-234 select std::min/max and v_min/v_max. On this x86 CPU, SSE v_min/max
uses _mm_min/max_ps/pd (`include/opencv2/core/hal/intrin_sse.hpp:1106-1109`),
which selects the second operand on unordered/equal comparisons; std::min/max
selects the first. Disabling optional optimized dispatch does not remove
baseline SIMD, as the actual probe demonstrates.

The original universal existing-function alias parity requirement cannot hold
with unchanged direct-native execution on this supported 5.0 build. Under the
user-approved correction, independent output parity remains mandatory while
exact/shallow aliases preserve native floating-special selection. No helper
patch, temporary-result assignment, NaN normalization, optimization toggle,
preallocation workaround or exception skip has been introduced.

### Operand order and portability

The premise that NaN-versus-finite always yields NaN is not universal. In the
4.10 CPU probe Float32/half independent min/max has NaN/3 -> 3 at vector start
and NaN at scalar tail; 3/NaN -> NaN at vector start and 3 at scalar tail.
5.0 independent results use SIMD selection at the tail too. Float64 behavior
also depends on native dispatch. Neither operation is IEEE fmin/fmax, and
neither full IEEE/bitwise commutativity nor unconditional NaN propagation is
supported by these sources/probes.

OpenCL `src/opencl/arithm.cl` uses min/max directly: 4.x:209-213,
5.0:213-217. It is a separate backend portability boundary; no successful
GPU execution is claimed. The blocking CPU counterexample alone is sufficient.

## Float16 and empty policy

The existing helper widens both operands to Float32 Dense on 4.x and narrows
the arithmetic result into the actual half output; native 5.0 tables include
min16f/max16f. Compatible whole/Region reuse and ordinary finite exact aliases
passed the probe on all versions. 5.0 floating-special aliases encounter the
native scalar-tail divergence above; the existing helper is not changed.

The helper's compatible-empty mix guard and UMat both-empty guard remain intact.
All accepted default/default, typed/typed 8U/32F/16F and default/typed 8U in
either order completed with nonempty 16S C2 initial outputs. Native metadata
is logged by the probe, without normalization. No empty HAL rejection occurred
in these local runs. AUnit pins destination rank/extents/depth/channels and
old-alias survival, including native release's retained old output type.

With a nonempty Int16 C2 old Mat destination, default/default and either
default/typed UInt8 mix release output: rank 2, shape 0x0 on 4.x; rank 0 on
5.0, retaining old Int16 C2 type. Typed/typed UInt8 and Float32 create rank-2
0x0 outputs of operand type on every version. Typed/typed Float16 releases
on 4.x (the empty widened intermediates cause final convertTo release), but
5.0 native half creates rank-2 0x0 Float16 C1. An independent function result
has default UInt8 C1/rank-0 metadata when released, not the old destination's
retained type. These differences are documented, not normalized.
UMat default/default releases similarly; every typed pair or accepted mix
uses the existing helper's typed rank-2 0x0 operand representation. Both
operations share these rules. The explicit old alias remains live/writable.

## Reproduction and current verification boundary

### ARM64 Numbers observation correction

Review head `b5c6e6e40609cf3f345ceaca8476426ad0b7d4b9` failed the four
Maximum Numbers/OpenCL-disabled registrations on Ubuntu and macOS ARM64.
The disabled cases repeat Numbers; this was not an OpenCL-specific defect.
The failing value is Int32 C3, channel 1, first row/column: the test's
Float64 observation was **2147483648**, expected **2147483647**.

A temporary standalone diagnostic isolated Scalar construction, typed storage,
direct-native fresh/reused selection, and conversion for observation. AArch64
cross-compiled probes under QEMU with Debian and Ubuntu 24.04 OpenCV 4.6.0 found:

- Scalar-built raw sources are already exactly
  `(-2147483648, 2147483647, -7)` and `(9, -9, 12)` at every element.
- Exact typed construction stores those same values, with no fixture change
  to the intended inputs. Mat/UMat transfers preserve the raw integers.
- Independent integer selection and direct-native fresh/reused Mat/UMat
  minimum/maximum agree exactly with optimizations both enabled and disabled.
- Widening either Scalar-built or exact-typed Int32 data to Float64 changes
  INT_MAX to 2147483648 on this backend. Native Maximum's raw channel 1 is
  still 2147483647; only its widened observation is wrong.

This is a test observation defect, not a Scalar construction or max-kernel
defect. Authoritative 4.6.0 `hal/intrin_neon.hpp:2230-2237` implements
`v_cvt_f64(v_int32x4)`/`v_cvt_f64_high` through `vcvt_f32_s32` followed by
`vcvt_f64_f32`; 5.0.0 retains that path at lines 2617-2624. Float32 cannot
represent INT_MAX exactly. The conversion loop in 4.6.0
`src/convert.simd.hpp:102-128` selects these SIMD conversions for wide data.
The x86_64 host probe preserves INT_MAX when widening. Minimum never selects
INT_MAX in this fixture, explaining the Maximum-only failure pattern.

Numbers retains the original Scalar/Set_To construction, and verifies both
complete stored Int32 sources through typed access before arithmetic. It checks
allocation-returning results, reused Destination and retained aliases through
exact Int32 reads and integer Min/Max expectations using Int32_Value'First/Last.
Fresh/reused/alias parity also compares typed integers. No native Float64
conversion participates in Int32 correctness assertions. Other depth fixtures
and floating-special behavior are unchanged. There are no tolerances or
architecture-dependent expected values, and no production changes.

Temporary diagnostic probes are not promoted into repository artifacts; their
observations are evidence for the test correction, not a conversion contract.

```
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/min_max_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/minmax-probe
/tmp/minmax-probe
```

Use opencv5 for 5.0. The probe strictly compares actual-helper aliases to
separately constructed direct-native alias results. Fresh/alias special parity
differences are logged as observations under the corrected contract, not hidden.
Initial diagnostic logs: `/tmp/task047-audit-{4.1,4.6,4.10,5.0}.log` (5.0's
original parity gate failed). Final-head validation is reported with the PR.

## Public tests and architectural review

The shared Mat/UMat engine is parameterized by operation, registering clear
Minimum/Maximum cases for whole/Region reuse, separate shape/depth/channel
detachment, Left/Right/shallow/A-A 257-element aliases, exact UInt8 C3 selection,
signed Int16/Int32 extrema, Float32/64 finite values and Float16 finite extrema,
specials/order/alias/tail, accepted empties, failures/N-D, scalar-like arrays,
and exception-safe OpenCL-disabled runs. Shared external/selected temporary and
raw Mat/UMat cases exercise both operations. Test observation widens half before
channel extraction because raw 4.x half extraction is unsupported.

Floating-special tests cover 257 elements, both NaN/finite orders, both infinity
orders/signs, NaN/NaN, equal infinities, both zero orders, C1/C3, fresh outputs,
Left/Right/shallow aliases and A/A. Fresh outputs use the unchanged function.
Alias outputs use a test-only direct OpenCV oracle on separate cloned native
storage with exactly the requested alias layout and same backend. It never
calls the new exports. The 4.x half oracle uses the established Float32 model;
5.0 uses native half. NaN payload identity is not asserted. Ordinary alias
values are additionally checked against independently derived Ada selection.

All procedures call unchanged Validate_Arithmetic_Compatibility(Left,Right).
Destination is not an operand. N-D remains rejected only by thick Ada.
Raw exports only check null pointers and temporary Mat output capability,
and retain exception translation. Pre-native raw failures preserve dimensions,
shape/type, every pixel, selected parent pixels and external padding.
No post-native failure atomicity is claimed.

The only retained duplicate restriction is temporary Mat Destination:
Ada Temporary_View and raw temporary_external_view both reject it because
native output creation can release/rebind the header and sever the callback-
scoped capability over external/selected storage. Each new C++ guard carries
that concrete ABI-safety explanation. No operand semantic validation is
duplicated in the C++ exports. Existing empty compatibility guards are unchanged.

New UMat production code passes native UMat directly to dense_min_max, with
UMat Dense Float16 intermediates. No To_Mat/To_UMat/getMat/ACCESS_READ/WRITE,
host staging or Mat arithmetic intermediary is added to production. Test-only
host transfers and oracle clones are setup/observation, not binding behavior.
OpenCV controls execution/fallback; no GPU execution is claimed. No SPARK-
compatible computation changed, so GNATprove is not applicable.