# Task 041: native conversion destinations

## Exact source review

The local upstream checkouts were verified against the exact tags/peeled SHAs.
Paths below are relative to `modules/core/`; complete conversion bodies and
the relevant Mat/UMat branches of OutputArray creation/release were inspected.

| Tag | Peeled SHA | Mat / UMat declarations (`include/opencv2/core/mat.hpp`) | Mat / UMat conversion bodies | Mat / UMat N-D create bodies |
|---|---|---|---|---|
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 1212-1225 / 2442-2443 | src/convert.dispatch.cpp:174-225 / src/umatrix.cpp:976-1039 | src/matrix.cpp:318-375 / src/umatrix.cpp:403-461 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 1234-1247 / 2473-2474 | src/convert.dispatch.cpp:174-225 / src/umatrix.cpp:1236-1299 | src/matrix.cpp:659-718 / src/umatrix.cpp:653-717 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 1235-1248 / 2495-2496 | src/convert.dispatch.cpp:248-303 / 305-341 | src/matrix.cpp:659-718 / src/umatrix.cpp:653-717 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 1478-1491 / 2847-2848 | src/convert.dispatch.cpp:131-207 / 209-246 | src/matrix.cpp:1085-1144 / src/umatrix.cpp:601-671 |

Authoritative trees: [4.1.0](https://github.com/opencv/opencv/tree/4.1.0/modules/core),
[4.6.0](https://github.com/opencv/opencv/tree/4.6.0/modules/core),
[4.10.0](https://github.com/opencv/opencv/tree/4.10.0/modules/core),
[5.0.0](https://github.com/opencv/opencv/tree/5.0.0/modules/core).

`src/matrix_wrap.cpp` creation/release paths inspected: 4.1:1189-1342,
1657-1673; 4.6 and 4.10:1160-1339,1665-1681; 5.0:1466-1663,2042-2058.
The no-scaling/same-depth copy paths were also inspected in `src/copy.cpp`
and `src/umatrix.cpp`. Numeric loops in `src/convert.simd.hpp` and
`src/convert_scale.simd.hpp` apply saturate_cast and explicitly avoid repeated
SIMD tail processing when the source and destination addresses coincide.

## Documented contract

All four Mat declarations document `saturate_cast(alpha * source + beta)`,
preservation of source channels, and reallocation of improperly sized/typed
destinations. UMat declares the same signature/defaults and references
cvConvertScale. Mat create documentation promises no allocation for an already
matching size/type. Partial overlap is explicitly unsupported by copyTo,
which convertTo uses for identity conversion; there is no general promise of
partial-overlap support for numeric conversion. The binding makes none.

## Implementation findings

* **4.1 / 4.6 Mat:** empty releases output; otherwise constructs the target type
  from depth plus source channels, uses copyTo for identity, retains `Mat src =
  *this` **before** destination create, and uses row strides or NAryMatIterator.
* **4.1 / 4.6 UMat:** identity calls copyTo. OpenCL retains `UMat src = *this`
  before create. CPU fallback retains another UMat reference explicitly to
  resolve issue 8693 (`src == dst`), then delegates to Mat conversion. There is
  no initial empty check; copyTo or the Mat fallback releases empty output.
* **4.10:** shared OpenCL conversion checks device FP16/FP64 support. Both Mat
  and UMat explicitly release empty output. Mat retains its source before
  N-D create; UMat retains its source before fallback. Numeric iteration and
  channel preservation otherwise match the older versions.
* **5.0:** nonempty behavior remains equivalent; Mat adds HAL dispatch and
  MatShape/allowTransposed plumbing. The binding's ordinary mutable Mat/UMat
  destinations have no fixed size/type and use genuine 2-D or N-D extents.

In every tag, matching create returns without releasing allocation, including
strided Region headers. OutputArray creates through the **actual object**, not
through an independently allocated replacement. Nonmatching create releases,
resets header flags/offset, and allocates: a formerly shared Region detaches.
Row/plane iteration honors source/destination strides; only selected Region
pixels are touched. Later UMat N-D create additionally checks usage flags; the
binding uses USAGE_DEFAULT consistently. 4.1 N-D create assigns requested usage
flags; its inline 2-D create can return on matching geometry/type/storage
without a usage check. Later tags retain existing flags when the request is
USAGE_DEFAULT. The 2-D delegators were inspected too: 4.1 mat.inl.hpp:825-838,
3752-3765; 4.6/4.10 matrix.cpp:527-539, umatrix.cpp:361-370; 5.0
matrix.cpp:923-935, umatrix.cpp:360-370.

Exact self conversion is supported by the retained source reference in every
tag, including depth-changing conversion. Matching shallow aliases are safe
for exact same-layout in-place scaling; depth-changing conversion detaches the
destination while the other header retains old storage/type. Arbitrary partial
overlap is not covered by this conclusion.

N-D is common: Mat uses NAryMatIterator; UMat delegates to that native path
when OpenCL's 2-D path does not apply. The binding must not insert transfers or
mapping. OpenCV itself may map/fall back; native UMat does not guarantee GPU
execution or zero host access inside OpenCV.

## Empty compatibility difference (not normalized)

The isolated `convert_destination_probe.cpp` was compiled with warnings as
errors and run on all four exact compatibility images, OpenCL disabled, for
default/typed Float32 C3 sources, scale 1/2, and an Int16 C2 destination:

| Tag | Mat result | UMat result |
|---|---|---|
| 4.1.0 / 4.6.0 / 4.10.0 | empty, 2-D 0x0, **Int16 C2** (destination metadata retained) | same |
| 5.0.0 | empty, 2-D 0x0, **UInt8 C1** default source / **UInt8 C3** typed source | empty, 2-D 0x0, **UInt8 C1** for both |

5.0 Mat releases then creates from requested depth plus source channels.
5.0 UMat releases then creates from `type_ >= 0 ? type_ : type()` directly:
the depth-only argument encodes one channel on this empty path. This is an
upstream implementation exception to documented channel preservation. We
preserve it, as does the unchanged return-value binding. Empty exact-self
metadata can also depend on release mutating the source header; no uniform
empty metadata or post-native exception-atomicity promise is made.

## ABI and lifetime boundary

New exports use actual destination headers, never temporary-result assignment,
clone, or binding-side staging. Null handles and unrecognized depth identifiers
fail before native mutation. The existing depth identifier mapper is reused,
including Float16; no widening fallback or finite-value restriction is added.

Both Ada Temporary_View and raw temporary_external_view forbid a temporary
destination even when presently compatible: conversion may release/rebind the
header, severing its logical capability over callback/caller storage. The raw
guard independently protects that boundary. Read-only temporary sources remain
valid, with no alias escape or host copy added. Pre-native validation failures
leave destination geometry, type, sharing, and pixels unchanged. Native
exceptions are translated, but arbitrary post-native failures need not leave
the destination unchanged.

## Validation-boundary / residency review

The only public condition repeated at the raw boundary is temporary Mat
destination rejection: releasing/rebinding severs the callback-scoped logical
capability over caller/selected storage. Its `ABI safety:` comment records this
reason. Null checks are ABI pointer safety; depth identifier mapping is raw ABI
representation validation (the public enumeration cannot represent invalid
identifiers). No shape, emptiness, channel, type compatibility, finite numeric,
or overlap policy is duplicated in the shim. Native destination create owns
reuse/reallocation behavior. No postcondition check or staging is added.

The complete production diff adds no getMat, ACCESS_READ/WRITE, To_Mat, To_UMat,
mapping, or transfers. UMat calls `source->value.convertTo(destination->value,
native_depth, scale, offset)` directly. Test transfers only observe results.

The 28 new registered AUnit cases include parent/guard and bidirectional alias
evidence, size/type Region detachment, source lifetime independence, real N-D
reuse, version-specific empty metadata, SIMD-tail exact self, shallow aliases,
source Regions, Float16, external/selected source permission and destination
rejection, and raw null/depth/temporary failures preserving geometry and pixels.
No production pointer accessor is added. No SPARK-compatible computation is
changed: the new Ada bodies are controlled-wrapper foreign calls and a Boolean
capability check, so no new formal-proof claim is made.