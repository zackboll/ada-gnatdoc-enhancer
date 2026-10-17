# Task 039: dense N-D min/max source and native probe findings

## Exact authoritative sources

Inspected declarations/documentation in `modules/core/include/opencv2/core.hpp`
and implementations at the following exact tags (not moving branches):

| Tag | Peeled source commit | Implementation |
|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | `modules/core/src/minmax.cpp` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | `modules/core/src/minmax.cpp` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | `modules/core/src/minmax.dispatch.cpp`, `minmax.simd.hpp` |

Source links:
- [4.1 declaration](https://github.com/opencv/opencv/blob/4.1.0/modules/core/include/opencv2/core.hpp#L814-L838)
- [4.1 implementation](https://github.com/opencv/opencv/blob/4.1.0/modules/core/src/minmax.cpp#L757-L828)
- [4.10 declaration](https://github.com/opencv/opencv/blob/4.10.0/modules/core/include/opencv2/core.hpp#L911-L932)
- [4.10 implementation](https://github.com/opencv/opencv/blob/4.10.0/modules/core/src/minmax.cpp#L1498-L1591)
- [5.0 declaration](https://github.com/opencv/opencv/blob/5.0.0/modules/core/include/opencv2/core.hpp#L844-L866)
- [5.0 dispatcher](https://github.com/opencv/opencv/blob/5.0.0/modules/core/src/minmax.dispatch.cpp#L300-L391)
- [5.0 CPU kernels and depth table](https://github.com/opencv/opencv/blob/5.0.0/modules/core/src/minmax.simd.hpp#L20-L86)

The independent `nd_min_max_probe.cpp` prints build information and exercises
both Float32/Float64 with native optimizations disabled and enabled. It was
compiled with C++17, Wall/Wextra/Wpedantic/Werror and run in the established
Core compatibility images for exact 4.1.0, 4.10.0, and 5.0.0. This is deliberately
outside the production binding and normal AUnit suite.

## Portable public contract and native differences

All three support dense N-D logical iteration, including non-contiguous views.
Locations require C1; the native channel assertion only permits C>1 when both
index outputs and the mask are absent. `ofs2idx` walks dimensions from last to
first using modulo/division; output slots retain native shape order, not X/Y.
Mask values select whole elements, not channels. The iterator asserts equal
full shapes. 4.x requires CV_8UC1; 5.0 additionally permits 8S/Bool masks.
The Ada API deliberately remains UInt8 C1 with full dimension/extent equality.

4.1 and 4.10 depth tables contain 8U/8S/16U/16S/32S/32F/64F and a null 16F
slot. **5.0 differs:** `minmax.simd.hpp:356,379` installs native 16F dispatch
(and other new depths), while `core.hpp:855` still says 16F is unsupported.
The executable probe succeeds on a 5-D half Mat in 5.0, returning 2/2 and
all-zero coordinates; 4.x throws OpenCV assertion error -215. Ada rejects
Float16 on every version as the narrow portable policy, with no widening.
Raw ABI tests require native failure with cleared outputs on 4.x and native
success on 5.0. There is no shim depth rejection or forced 5.0 failure.

Dense reduction includes every selected logical element; sparse stored-node
semantics are irrelevant. The supplied mask may select nothing: all-zero
5-D masks return native values 0/0 and all -1 indices in the three tested
environments. The binding publishes false/false and all-zero coordinates,
retains 0/0, and still reports the source dimension count. Default empty Mat
returns native 0/0 without writing coordinate slots; typed empty returns
0/0 with -1 slots. Ada rejects both forms before calling the shim.

CPU scalar comparisons use strict < and >; vector reductions choose the smallest
index for equal updated extrema. Finite ties in the three native probes and the
seven-depth AUnit tests select the earliest logical coordinate. The public API
does not promise an ordering stronger than the linked OpenCV/backend supplies.

### OpenCV 4.10 flattened-HAL compatibility correction

OpenCV 4.10 `minmax.cpp:1518-1530` flattens continuous N-D input for HAL.
On success it executes `ofs2idx(src, minIdx[1], minIdx)` and
`ofs2idx(src, maxIdx[1], maxIdx)`. HAL locations are zero-based, while
`ofs2idx` at lines 849-867 treats zero as undefined and subtracts one from a
positive offset. Thus flattened index zero becomes an undefined location,
and each positive index is shifted to the preceding logical element.
OpenCV 5.0 `minmax.dispatch.cpp:334,336` corrects both calls with
`ofs2idx(src, minIdx[1]+1, minIdx)` and
`ofs2idx(src, maxIdx[1]+1, maxIdx)`; its flattened path also requires a
continuous or empty mask. The configured 4.10 image has no custom HAL, so
ordinary hosted success alone cannot establish behavior on HAL success.

For exactly OpenCV major 4 / minor 10, the binding clears CONTINUOUS_FLAG
on its local shallow `cv::Mat src = source->value` header for **every**
continuous source with dims>2, before computing flattened-HAL eligibility.
Native minMaxIdx therefore uses its correct iterator/IPP fallback for
unmasked input, continuous masks, and strided masks alike. This one bypass
also avoids 4.10's flattened path ignoring mask strides. No storage clone
occurs, and neither the caller's Mat header/metadata nor shared storage is
mutated. Returned coordinates are not corrected after the fact: native
remapping has already lost the distinction between undefined and flattened
index zero, and the shim cannot safely infer which native backend produced
the coordinates. Preventing entry into the defective path avoids that
ambiguity and preserves correct native fallback behavior.

5.0 retains native flattened-HAL execution and its corrected +1 remapping.
4.1/4.6 have no such N-D HAL branch and receive no compatibility adjustment.
The existing unique-extrema 5-D test explicitly asserts dimensionality and
continuity before reduction, then confirms caller/alias continuity, shape,
and values afterward. Continuous-mask and strided-mask fixtures also assert
their layouts. These exercise the binding's 4.10 bypass even when the stock
HAL would have declined; the custom-HAL correctness rationale is the exact
source difference, not a fake HAL added to the repository.

## Float32 and Float64 special values

Observed identically for both floating depths and both optimization settings
in the small 5-D probe. `origin` denotes (0,0,0,0,0); selected denotes
(1,0,0,0,0). The binding preserves all values, including zeros on a defined
side, and derives each flag from its corresponding native coordinate array.

| Input | 4.1 / 4.10 values; indices | 5.0 values; indices |
|---|---|---|
| finite 4,-2,9,3 | -2/9; correct unique coordinates | same |
| first NaN, then finite | ignores NaN; -2/9 | NaN/NaN; origin/origin |
| finite, then NaN | ignores NaN; -2/9 | -2/9 in this probe |
| NaN only, unmasked | +Inf/-Inf; origin/origin | NaN/NaN; origin/origin |
| +Inf only, unmasked | +Inf/+Inf; origin/origin | same |
| -Inf only, unmasked | -Inf/-Inf; origin/origin | same |
| selected NaN only | 0/0; undefined/undefined | NaN/NaN; selected/selected |
| selected +Inf only | 0/0; undefined/selected | +Inf/+Inf; selected/selected |
| selected -Inf only | -Inf/-Inf; selected/undefined | -Inf/-Inf; selected/selected |

4.x seeds comparisons with +/-infinity, then forces missing unmasked indices
to offset 1. If masked minidx remains zero it sets *both values* to zero,
independently of maxidx. 5.0 seeds from the first selected element, so even
NaN or infinity can establish both indices. SIMD/backend changes and longer
inputs may differ; finite behavior is the portable guarantee. No special-value
normalization, NaN filtering, or combined "found" flag is added.

## OpenCL, HAL, IPP, and arithmetic audit

OpenCL is gated by isUMat and dims<=2 on all three versions; this API passes
Mat, never UMat, so it does not map or launch OpenCL. The 4.1 image disables
OpenCL/IPP; 4.10 has OpenCL but no custom HAL; 5.0 has OpenCL and IPP HAL.
4.1 hard-disables the local IPP minmax implementation; 4.10 enables it only
with OPENCV_IPP_MINMAX. 5.0 relocates IPP to `hal/ipp/src/minmax_ipp.cpp` and
dispatches through minMaxIdxMaskStep. Historic IPP guards mention NaN/index
bugs in older IPP releases; results of arbitrary HAL/IPP implementations are
not inferred from CPU source. OpenVX is likewise backend-dependent and
limited to its accepted image types/layouts.

Inspected `matrix_iterator.cpp` independently on all three tags (same relevant
code), 4.x IPP implementation, and 5.0 IPP HAL. No speculative shape or total
limit is imposed. Existing Core limits still apply: portable 32 slots, native
5.0 MatShape capacity 10. Shim checks/selection and reasons are:

1. Null pointers/handles and capacity in 1..32, with capacity >= dims: prevent
   buffer dereference/overwrite; scalars and accepted coordinate entries are
   cleared even when another output is null. Invalid capacity does not access
   coordinate buffers. Fixed scratch arrays are private native `int[32]`,
   initialized -1, then explicitly copied to int32_t without casts of pointers.
2. 4.10 `minmax.cpp:1520` / 5.0 `minmax.dispatch.cpp:327` use
   `(int)src.total()*cn` before continuous N-D HAL dispatch. For C1, reject
   total>INT_MAX only on a still-reachable flattened-HAL path before unsafe
   backend width narrowing. Eligibility is computed after compatibility
   adjustment: false for every 4.10 N-D call, so no artificial flattened-HAL
   size limit applies there. 5.0 retains the guard when source and optional
   mask continuity permit HAL. 4.1/4.6 N-D CPU paths acquire no such limit.
3. All three pass raw mask pointers to HAL before the iterator's equal-shape
   assertion. For HAL-eligible inputs reject mismatched nonempty mask shapes:
   otherwise a smaller buffer may be read out of bounds. This is the one
   duplicated public condition, retained for this concrete memory hazard:
   2-D HAL on all supported versions, and eligible flattened N-D HAL on 5.0.
   All 4.10 N-D calls bypass flattened HAL; those and other non-HAL N-D paths
   rely on the native iterator's full-shape assertion instead.
4. The local-header 4.10 N-D compatibility bypass described above prevents
   incorrect coordinate remapping and ignored mask strides before native
   execution. It is linked-version compatibility, not public semantic
   validation. 5.0 keeps its corrected native path; inputs remain unchanged.
5. NAryMatIterator::init caps plane size at INT_MAX using int64 arithmetic.
   With C1, `(int)it.size*cn` is safe. But operator++:160 casts size_t plane
   idx to int for iterdepth>1 before pointer arithmetic. Reject only layouts
   whose actual nplanes-1 exceeds INT_MAX on this path. No blanket total cap
   is added for 4.1 or non-contiguous Mats. Offset 1 plus total must fit size_t.
6. IPP narrows source/mask steps to int (4.x minmax; 5.0 minmax_ipp.cpp:210)
   and 4.x N-D plane byte lengths to int. Guard these when IPP is enabled
   and source depth is one of its supported location-selector types
   (8U/16U/32F), before pointer arithmetic can consume a narrowed step.
7. Native coordinate narrowing is checked before publication. All outputs
   remain zero on failure, including thrown native exceptions; dimensions
   and flags are published only after every coordinate is marshalled.

Ada alone validates nonempty/C1/portable depth and the full UInt8 C1 mask
contract. The shim has no duplicated depth/channel/empty policy. Ada checks
returned dimensions, flags, and valid coordinates against actual extents,
raising OpenCV_Error instead of wrapping an impossible native coordinate.
Inputs are borrowed, no native result handle or ownership transfer exists.

## Verification and scope

The focused AUnit package registers ten tests (many table-driven cases): unique
5-D extrema; masked/zero-mask 5-D; non-contiguous source/mask Slices and packed
source with strided mask; all seven portable depths and finite ties; unmasked
and masked 2-D Point parity; public negative paths; actual dimension boundary
(32 on 4.x, 10 on 5.0) and row/column vectors; both floating depths' native
specials; raw pointer/capacity/depth/channel failures; raw undersized mask safety.
Every scalar and accepted coordinate buffer is checked after raw failures.
No public UMat/SparseMat/Imgproc API or newer-version-only N-D work is included.

The changed library code is not SPARK-mode code; GNATprove was not run for this
foreign-operation/controlled-Mat feature. Assertions, strict builds, public
tests, native probes, and cross-version executions provide the evidence here,
not formal proof of OpenCV or HAL. No extra test/proof dependency was added.