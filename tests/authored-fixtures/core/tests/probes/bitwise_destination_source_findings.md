# Task 050: reusable Mat/UMat bitwise destinations

## Starting gate and exact sources

Fetched `origin/main`: `c01e3e90ea99e26e8bbf0d524acb5d5e1c4df6bf`
(PR #50 merge). Clean worktree, no open repository PRs. Branch:
`feature/050-bitwise-destination`. Complete host baseline: 1858 executed,
1858 passed, zero failed assertions/unexpected errors (OpenCV 4.10.0).

Reconfirmed annotated tag peeling with `git ls-remote` and inspected local
upstream checkouts whose HEADs match the following exact identities:

| Tag | Peeled SHA |
|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` |

Paths below are relative to `modules/core/`. All four headers declare
InputArray operands, OutputArray destination, optional mask=noArray(); Not has
one source. Documentation specifies machine bit representations for floating
storage and independent channels, not floating-point arithmetic.

| Tag | core.hpp And/Or/Xor/Not | arithm.cpp binary_op / exports |
|---|---|---|
| 4.1 | 1251/1278/1306/1323 | 169-342 / 374-403 |
| 4.6 | 1299/1326/1354/1371 | 151-328 / 360-389 |
| 4.10 | 1359/1386/1414/1431 | 151-328 / 360-389 |
| 5.0 | 1300/1327/1355/1372 | 151-328 / 378-407 |

## Creation and old-output-layout audit

In every tag, exports select `GET_OPTIMIZED(cv::hal::and8u/or8u/xor8u/not8u)`
and call binary_op with bitwise=true. Not supplies the source twice. CPU
execution uses byte width `CV_ELEM_SIZE(type1)` and a single byte kernel, never
a floating arithmetic table. The unmasked 2-D fast path creates source-type
output **before** OpenCL/CPU execution (4.1/4.6 use create(size,type), 4.10/5.0
use createSameSize); the general path creates it before NAryMatIterator.
No getSubExtFunc/getMulExtFunc-like old destination depth selector exists.
Mismatched type/channel output is safe after normal native creation; no
defensive preallocation, result temporary, assignment or copy-back is needed.

All 16 into exports remain thin and call the shared actual helpers on
`destination->value`. The corrective below extends only shared Mat empty
handling; ordinary nonempty dispatch is unchanged.

| Tag | matrix_wrap.cpp create/createSameSize/release | Mat/UMat N-D create |
|---|---|---|
| 4.1 | 1189-1342 / 1651-1655 / 1657-1673 | matrix.cpp:318-375 / umatrix.cpp:403-461 |
| 4.6/4.10 | 1160-1339 / 1659-1663 / 1665-1681 | matrix.cpp:659-718 / umatrix.cpp:653-717 |
| 5.0 | 1466-1663,1938 / 1954-1958 / 2042-2058 | matrix.cpp:1085-1144 / umatrix.cpp:601-671 |

Mat data/UMat u plus matching type, rank/extents permit early return. Interior
Regions retain offset/stride/storage; incompatible creation releases this
header and allocates. Refcounts keep old Parent/aliases alive. Public tests and
the helper probe verify every Region/guard pixel, unchanged Locate_Region,
reciprocal writes and independently observable shape/depth/channel detachment.

## Central masked rule

binary_op records reallocate **before** creation:

```cpp
reallocate = !_dst.sameSize(*psrc1) || _dst.type() != type1;
_dst.createSameSize(*psrc1, type1);
if (haveMask && reallocate) _dst.setTo(0.);
```

4.1: arithm.cpp:242-260; 4.6/4.10/5.0:227-245. Compatible masked destinations
are not cleared. CPU kernels compute a block into maskbuf, then getCopyMaskFunc
copies only selected elements. NAryMatIterator includes source1/source2/dst/mask
and supports non-contiguous Regions. copy.cpp copyMask_ and copyMaskGeneric test
`mask[x]`/`!mask[x]`, not ==255; generic copies the entire element-size bytes.

OpenCL arithm.cpp uses source-derived memopTypeToStr (integer representation,
even Float16/Float32/Float64); masked output is KernelArg::ReadWrite, unmasked
WriteOnly. In opencl/arithm.cl OP_AND/OR/XOR/NOT are `&`, `|`, `^`, `~`.
MASK_BINARY_OP and MASK_UNARY_OP execute PROCESS_ELEM only inside
`if (mask[mask_index])` (4.1:497/542; later tags corresponding masked KF paths).
One work item operates on all channels for a selected element. More than four
masked channels can fall back to CPU internally; binding does not stage.

Thus selected positions get result bits; unselected compatible positions keep
old bits, while unselected reallocated/function positions are zero. An all-zero
mask pins all three cases. An all-selected byte-1 mask agrees with unmasked
results. Mixed 0/1/2/127/255 masks pin nonzero selection and C3; native probe also
covers C4, Float16 Regions, wider integer and float layouts.

## Source aliases, tails and mask boundary

4.x arithm.simd.hpp op_and/or/xor/not (293-325), bin_loader/bin_loop and scalar
tails load source bits before storing the corresponding result. HAL dispatch
uses byte kernels and may use IPP before CPU SIMD fallback. 5.0 logic kernels
(253-305) explicitly avoid overlapping-tail vector replay when dst==src1/src2,
and finish in scalar code. This differs materially from weighted arithmetic:
there is no repeated Not/Xor on already-written exact-alias tail storage.
Masked CPU computes source blocks before copyMask; OpenCL reads matching source
work-item coordinates before its selected write. Exact and same-layout shallow
source aliases are supported, including mixed masks, Left/Right/Self and A=A
identities. Width 257 exercises vector/scalar tails. Partial overlap remains
unsupported; no overlap detection/copies were introduced.

Mask=Destination is only observed by the disposable probe. CPU generic/typed
mask copying and OpenCL work-item masking can appear safe for exact compatible
UInt8 C1 layout, and observed probes report parity. This does not establish a
portable HAL/accelerator guarantee across every backend. Destination aliasing
Mask is **outside the supported alias contract**, without expensive rejection
machinery. It does not weaken source alias support.

## Exact bits and dimensional policies

Public tests derive AA/CC -> 88/EE/66, Not AA -> 55 independently using modular
bit operators, not numerical arithmetic. C1/C3 and Int16/Int32 are covered.
Float16 uses Float16_From_Bits/Float16_Bits for +0/-0/1/infinity/NaN payloads
0000/8000/3C00/7C00/7E35/FE71. Expected raw bit results include a compatible
masked half Region initially 1.0, whose unselected encoding remains 3C00.
Float32/64 exact observation uses existing typed access and unchecked bit
observation in test code, never production numeric conversions. Native probe
also compares every byte to an independent byte oracle and direct-native calls.
No NaN/zero/payload normalization occurs.

Native general binary_op uses NAryMatIterator for rank >2; OpenCL admission is
rank <=2, so N-D Not can fall back internally. Genuine (2,3,5) Not is tested for
UInt8/Float16 function, compatible reuse, mismatch, shallow and exact Self
destination, rank/shape/depth/channels, and reciprocal writes. Thick binary
procedures retain Validate_Arithmetic_Compatibility (matching 2-D), masked
binary retains it plus Validate_Mask, and masked Not retains Validate_Mask.
Function/procedure N-D rejections and unchanged destinations are tested.

## Empty compatibility boundary

Existing helpers handle default-empty 0-D
sources to avoid OpenCV 5 create turning them into scalar storage followed by
getContinuousSize2D mismatched-total access. Both-empty UMat bypass remains:
4.10 ocl_binary_op can predict vector width on null typed-empty storage before
CPU fallback. Typed-empty Mat now bypasses zero-work execution too;
typed-empty UMat still follows make_empty_dense_like. A typed-empty mask is empty
to native binary_op (haveMask=false), not an N-D mask extension.

The helper probe records dims/type/every extent for every operation, source
default/typed combination, U8/half and default/typed-U8 masks, starting from
Int16 C2 destination with a retained alias whose every bit is checked. Public
tests cover accepted compatibility combinations; mixed default/typed half
binary inputs are not public-compatible. Release can retain old output type,
unlike a new function result. 4.x release retains rank-2 zero extents; 5.0
release resets rank to 0. Typed creation adopts source type and rank-2 (0,0).

| Helper path | 4.1/4.6/4.10 | 5.0 |
|---|---|---|
| Mat default/default, all operations | old type; rank2 (0,0) | old type; rank0 |
| Mat unmasked binary default/typed U8 (either order) | old type; rank2 | old type; rank0 |
| Mat typed/typed U8 or half, typed mask or no mask | source type; rank2 | source type; rank2 |
| Mat masked binary or Not default source | old type; rank2 | old type; rank0 |
| Mat masked typed source with default mask | source type; rank2 via helper | source type; rank2 via helper |
| UMat default source output release | old type; rank2 | old type; rank0 |
| UMat typed source helper create | source type; rank2 | source type; rank2 |

Unmasked UMat mixed default/typed input uses the typed operand in either order;
masked binary uses Left instead. In particular a default Left/typed Right
masked empty output releases, while its unmasked counterpart recreates U8.

Masked binary uses Left for empty representation; Not uses Self. Mixed raw
half inputs may differ from public compatibility deliberately. Probe output
logs each combination rather than requiring result metadata equal to function
metadata. Semantic consistency and old alias survival are mandatory.

### PR #51 hosted OpenCV 5/macOS ARM64 corrective

Failing reviewed head: `dcca839b54e7995f1c31b9289001df54e685e231`.
Push workflow 37254413147 reported only `Bitwise destination Mat empty`:
1875 executed, 1874 passed, zero assertions, one unexpected OpenCV error.
`and8u ==> cv_hal_and8u returned -1` at arithm.simd.hpp:852.

During investigation, a temporary isolated probe constructed matching
Left/Right typed UInt8 C1 empties (rank 2, shape (0,0), total 0), independently
calling direct `cv::bitwise_and`, actual `dense_bitwise_binary`, the
allocation-returning C export and the destination-taking C export. Each
destination started from Int16 C2 (2,257), with an observable retained Alias.
This confirmed the combination independently of the AUnit loop order.

Linux host 4.10 and exact Linux 5.0 accepted all four reviewed-head calls,
producing source-typed rank-2 (0,0) output with Alias unchanged. Hosted macOS
ARM64/OpenCV 5.0 push workflow 37255862270 compiled the isolated probe against
both the actual failing shim and corrective `17beab216ca88fd32fab4e51d6efe8899ea52e2f`.
At the failing head, direct native and actual-helper calls threw HAL and8u -1;
the destination export returned an OpenCV error after creating typed-empty
UInt8 C1 output, and the allocation export returned an error with a null
result. At the corrective head, helper and both exports succeeded with
source-typed rank-2 (0,0) metadata; direct native still threw. Old Int16 C2
Alias storage survived unchanged in every case. The complete current-head
helper probe and public suite passed, with 1875/1875 and zero assertions/errors.
Exact hosted observations are also recorded in PR #51.

The temporary `bitwise_empty_probe.cpp` and historical-head CI diagnostic
step were removed before merge; they are not permanent regression gates.
The compatibility workflow is restored exactly to its pre-diagnostic state
from `dcca839b54e7995f1c31b9289001df54e685e231` and no longer fetches or compiles
that broken historical head. Permanent regression coverage remains in the
normal current-head public tests (`bitwise_destination_tests.adb`) and actual
helper probe (`bitwise_destination_probe.cpp`), including isolated typed-empty
And plus the all-operation empty metadata/alias matrix.

Exact 5.0 arithm.cpp:169-193 admits matching typed 0x0 arrays to binary_op's
unmasked fast path, creates source-typed output, computes zero byte width, and
still invokes the byte kernel. An empty native mask has `haveMask=false`, so
it follows this same path. arithm.simd.hpp:822-829 invokes
`CALL_HAL(opname, cv_hal_##opname, ...)` before generic CPU dispatch;
and8u/or8u/xor8u instantiate it at 852-854, and Not does likewise at 860-861.
The hosted native HAL rejects zero-work and8u with -1. There is no evidence
identifying the registered backend for this particular call: no Carotene or
KleidiCV attribution is made.

The shared Mat `bitwise_empty_bypass` now handles both-empty operands with no
mask or an empty mask, preventing any zero-element byte/HAL execution for
And/Or/Xor/Not. Masked binary follows Left; Not follows Self. Unmasked
typed/typed uses `make_empty_dense_like`, rather than the releasing Mat
`make_empty_arithmetic_result` overload. Default/default and either-order
default/typed unmasked mixes still release. The metadata table above is
unchanged, including intentional old-destination versus fresh-function type
differences and OpenCV 4.x/5.0 release rank differences. This is an empty
compatibility workaround, not normalization of ordinary nonempty HAL behavior.

The UMat bypass and its null-storage ABI-safety rationale remain unchanged.
Reviewed/corrective helper probe UMat metadata logs are compared byte-for-byte
on the host and each exact Linux version. Strengthened existing registrations
assert allocation-function rank/shape/depth/channels independently from
procedure metadata, while the helper probe now treats any empty exception as
a failure and asserts every empty result's exact rank/type/extents.

## Validation-boundary review and residency

New C++ guards check only required null handles and temporary Mat capability.
No duplicated 2-D, shape/type/mask, depth/channel, Float16 or N-D policy.
The only retained duplicate is temporary Destination: the helper's concrete
ABI safety comment explains native output release/rebinding would sever the
callback-scoped external/selected-storage capability. Ada rejects it
independently. Tests exercise compatible/incompatible destinations and every
null argument across all 16 exports, unchanged metadata/pixels, selected Parent
and external padding. Ordinary input temporary sources/masks remain legal;
output is independently writable. No arbitrary post-native failure atomicity.

UMat into exports use cv::UMat source/mask/destination values only. No getMat,
To_Mat/To_UMat, ACCESS_READ/WRITE or host intermediates were added to production.
Test observation and standalone probe host copies are explicitly test-only.
OpenCL-disabled public coverage restores prior state even on exceptions.
Containers have no usable OpenCL device; host requests OpenCL but has kernel
build failures in its compiler-header runtime and falls back. No successful
GPU-execution claim. No SPARK-compatible computation changed; no proof required.

## Reproduction and verification reporting

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  $(pkg-config --cflags opencv4) tests/probes/bitwise_destination_probe.cpp \
  $(pkg-config --libs-only-L opencv4) -lopencv_core -o /tmp/bitwise-probe
/tmp/bitwise-probe
```

Use opencv5 on 5.0. Probe includes actual production translation unit. Public
and raw suites register 17 focused tests using shared operation engines, with
1875 total. Final exact review SHA, all suite counts, strict compiler/shared
link gates and hosted CI snapshot are reported in the PR and completion report.
No dependency/CI/version/publication or excluded operation changes.