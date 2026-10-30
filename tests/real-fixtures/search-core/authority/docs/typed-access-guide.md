# Typed access guide

[README](../README.md) · [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) · [Building and Contributing](documentation.md)

This guide is published as HTML on the documentation site and maintained as
Markdown in the source repository. The public Ada specifications are authoritative for exact profiles
and per-overload restrictions. Examples below include both complete programs
and fragments intended for the surrounding application.

## Contents

- [Shared value types](#shared-value-types)
- [Typed access matrix](#typed-access-matrix)
- Related: [borrowed and external views](ownership-and-views.md) and
  [sparse typed access](sparse-and-persistence-guide.md#sparse-matrices)

## Shared value types

`OpenCV` owns the shared public values used across Core and later module
crates. The `opencv_core` crate still distributes the parent package.
`OpenCV.Core` continues to own `Mat` and matrix-specific abstractions.

Shared root types include numeric value subtypes (`OpenCV.UInt8_Value`,
`OpenCV.Int8_Value`, `OpenCV.UInt16_Value`, `OpenCV.Int16_Value`,
`OpenCV.Int32_Value`, `OpenCV.Float32_Value`, `OpenCV.Float64_Value`),
integer coordinates
and geometry (`OpenCV.Point_Coordinate`, `OpenCV.Size_Coordinate`,
`OpenCV.Point`, `OpenCV.Point_Array`, `OpenCV.Point_3D`,
`OpenCV.Point_3D_Array`, `OpenCV.Size`, `OpenCV.Rect`),
floating-point geometry (`OpenCV.Float32_Point`, `OpenCV.Float32_Point_3D`,
`OpenCV.Float32_Point_3D_Array`, `OpenCV.Float32_Size`,
`OpenCV.Rotated_Rect`), the shared scalar (`OpenCV.Scalar`,
`OpenCV.Make_Scalar`), and shared options (`OpenCV.Border_Kind` with
literals such as `OpenCV.Reflect_101`, and `OpenCV.Angle_Unit`).

The 3-D point families are ordinary Ada values with signed 32-bit integer
or binary32 coordinates, all defaulting to zero. Their arrays preserve
arbitrary `Natural` bounds, including null ranges. Binary32 values may
represent NaN and infinities; each consuming operation defines its own
finiteness policy. Root ownership follows native OpenCV's Core `Point3`
value concept, allowing Geometry, Calib3D, and future 3-D module bindings
to reuse these shared coordinates rather than redeclare them. These
additive types are included in the prepared `0.5.0` candidate, not the latest
indexed `0.4.1` release. Candidate preparation is not Alire publication.

The earlier relocation of existing values to the root was source-breaking.
Callers that previously wrote
`OpenCV.Core.Point` or `OpenCV.Core.Make_Scalar` must update
qualification and visibility to the root `OpenCV` package. Clients that
use `"="` or other operators on those values need `with OpenCV;` so the
operators are visible. Core does not keep compatibility aliases for the
moved names.

Representative spellings:

| Old | New |
| --- | --- |
| `OpenCV.Core.Point` | `OpenCV.Point` |
| `OpenCV.Core.Point_Coordinate` | `OpenCV.Point_Coordinate` |
| `OpenCV.Core.Size` | `OpenCV.Size` |
| `OpenCV.Core.Rect` | `OpenCV.Rect` |
| `OpenCV.Core.Scalar` | `OpenCV.Scalar` |
| `OpenCV.Core.Make_Scalar` | `OpenCV.Make_Scalar` |
| `OpenCV.Core.Point_Array` | `OpenCV.Point_Array` |
| `OpenCV.Core.Reflect_101` | `OpenCV.Reflect_101` |

---

## Typed access matrix

Direct typed access covers thirty-two layouts: every supported depth in
C1/C2/C3/C4:

| Layout | 2-D Get/Set | N-D Get/Set | Classification | Copied row | Borrowed row | Continuous buffer borrow | Packed caller buffer -> `Mat` | Strided caller buffer -> `Mat` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UInt8 C1 | `UInt8_Access` | `UInt8_Access` | — | `UInt8_Row_Access` | `UInt8_Row_Access` | `UInt8_Buffer_Access` | `UInt8_Mat_View` | `UInt8_Mat_View` |
| Int8 C1 | `Int8_Access` | `Int8_Access` | — | `Int8_Row_Access` | `Int8_Row_Access` | `Int8_Buffer_Access` | `Int8_Mat_View` | `Int8_Mat_View` |
| UInt16 C1 | `UInt16_Access` | `UInt16_Access` | — | `UInt16_Row_Access` | `UInt16_Row_Access` | `UInt16_Buffer_Access` | `UInt16_Mat_View` | `UInt16_Mat_View` |
| Int16 C1 | `Int16_Access` | `Int16_Access` | — | `Int16_Row_Access` | `Int16_Row_Access` | `Int16_Buffer_Access` | `Int16_Mat_View` | `Int16_Mat_View` |
| Int32 C1 | `Int32_Access` | `Int32_Access` | — | `Int32_Row_Access` | `Int32_Row_Access` | `Int32_Buffer_Access` | `Int32_Mat_View` | `Int32_Mat_View` |
| Float16 C1 | `Float16_Access` | `Float16_Access` | `Float16_Value` helpers | `Float16_Row_Access` | `Float16_Row_Access` | `Float16_Buffer_Access` | `Float16_Mat_View` | `Float16_Mat_View` |
| Float32 C1 | `Float32_Access` | `Float32_Access` | — | `Float32_Row_Access` | `Float32_Row_Access` | `Float32_Buffer_Access` | `Float32_Mat_View` | `Float32_Mat_View` |
| Float64 C1 | `Float64_Access` | `Float64_Access` | `Float64_Access` | `Float64_Row_Access` | `Float64_Row_Access` | `Float64_Buffer_Access` | `Float64_Mat_View` | `Float64_Mat_View` |
| UInt8 C2 | `UInt8_Vec2_Access` | `UInt8_Vec2_Access` | — | `UInt8_Vec2_Row_Access` | `UInt8_Vec2_Row_Access` | `UInt8_Vec2_Buffer_Access` | `UInt8_Vec2_Mat_View` | `UInt8_Vec2_Mat_View` |
| Int8 C2 | `Int8_Vec2_Access` | `Int8_Vec2_Access` | — | `Int8_Vec2_Row_Access` | `Int8_Vec2_Row_Access` | `Int8_Vec2_Buffer_Access` | `Int8_Vec2_Mat_View` | `Int8_Vec2_Mat_View` |
| UInt16 C2 | `UInt16_Vec2_Access` | `UInt16_Vec2_Access` | — | `UInt16_Vec2_Row_Access` | `UInt16_Vec2_Row_Access` | `UInt16_Vec2_Buffer_Access` | `UInt16_Vec2_Mat_View` | `UInt16_Vec2_Mat_View` |
| Int16 C2 | `Int16_Vec2_Access` | `Int16_Vec2_Access` | — | `Int16_Vec2_Row_Access` | `Int16_Vec2_Row_Access` | `Int16_Vec2_Buffer_Access` | `Int16_Vec2_Mat_View` | `Int16_Vec2_Mat_View` |
| Int32 C2 | `Int32_Vec2_Access` | `Int32_Vec2_Access` | — | `Int32_Vec2_Row_Access` | `Int32_Vec2_Row_Access` | `Int32_Vec2_Buffer_Access` | `Int32_Vec2_Mat_View` | `Int32_Vec2_Mat_View` |
| Float16 C2 | `Float16_Vec2_Access` | `Float16_Vec2_Access` | — | `Float16_Vec2_Row_Access` | `Float16_Vec2_Row_Access` | `Float16_Vec2_Buffer_Access` | `Float16_Vec2_Mat_View` | `Float16_Vec2_Mat_View` |
| Float32 C2 | `Float32_Vec2_Access` | `Float32_Vec2_Access` | — | `Float32_Vec2_Row_Access` | `Float32_Vec2_Row_Access` | `Float32_Vec2_Buffer_Access` | `Float32_Vec2_Mat_View` | `Float32_Vec2_Mat_View` |
| Float64 C2 | `Float64_Vec2_Access` | `Float64_Vec2_Access` | — | `Float64_Vec2_Row_Access` | `Float64_Vec2_Row_Access` | `Float64_Vec2_Buffer_Access` | `Float64_Vec2_Mat_View` | `Float64_Vec2_Mat_View` |
| UInt8 C3 | `UInt8_Vec3_Access` | `UInt8_Vec3_Access` | — | `UInt8_Vec3_Row_Access` | `UInt8_Vec3_Row_Access` | `UInt8_Vec3_Buffer_Access` | `UInt8_Vec3_Mat_View` | `UInt8_Vec3_Mat_View` |
| Int8 C3 | `Int8_Vec3_Access` | `Int8_Vec3_Access` | — | `Int8_Vec3_Row_Access` | `Int8_Vec3_Row_Access` | `Int8_Vec3_Buffer_Access` | `Int8_Vec3_Mat_View` | `Int8_Vec3_Mat_View` |
| UInt16 C3 | `UInt16_Vec3_Access` | `UInt16_Vec3_Access` | — | `UInt16_Vec3_Row_Access` | `UInt16_Vec3_Row_Access` | `UInt16_Vec3_Buffer_Access` | `UInt16_Vec3_Mat_View` | `UInt16_Vec3_Mat_View` |
| Int16 C3 | `Int16_Vec3_Access` | `Int16_Vec3_Access` | — | `Int16_Vec3_Row_Access` | `Int16_Vec3_Row_Access` | `Int16_Vec3_Buffer_Access` | `Int16_Vec3_Mat_View` | `Int16_Vec3_Mat_View` |
| Int32 C3 | `Int32_Vec3_Access` | `Int32_Vec3_Access` | — | `Int32_Vec3_Row_Access` | `Int32_Vec3_Row_Access` | `Int32_Vec3_Buffer_Access` | `Int32_Vec3_Mat_View` | `Int32_Vec3_Mat_View` |
| Float16 C3 | `Float16_Vec3_Access` | `Float16_Vec3_Access` | — | `Float16_Vec3_Row_Access` | `Float16_Vec3_Row_Access` | `Float16_Vec3_Buffer_Access` | `Float16_Vec3_Mat_View` | `Float16_Vec3_Mat_View` |
| Float32 C3 | `Float32_Vec3_Access` | `Float32_Vec3_Access` | — | `Float32_Vec3_Row_Access` | `Float32_Vec3_Row_Access` | `Float32_Vec3_Buffer_Access` | `Float32_Vec3_Mat_View` | `Float32_Vec3_Mat_View` |
| Float64 C3 | `Float64_Vec3_Access` | `Float64_Vec3_Access` | — | `Float64_Vec3_Row_Access` | `Float64_Vec3_Row_Access` | `Float64_Vec3_Buffer_Access` | `Float64_Vec3_Mat_View` | `Float64_Vec3_Mat_View` |
| UInt8 C4 | `UInt8_Vec4_Access` | `UInt8_Vec4_Access` | — | `UInt8_Vec4_Row_Access` | `UInt8_Vec4_Row_Access` | `UInt8_Vec4_Buffer_Access` | `UInt8_Vec4_Mat_View` | `UInt8_Vec4_Mat_View` |
| Int8 C4 | `Int8_Vec4_Access` | `Int8_Vec4_Access` | — | `Int8_Vec4_Row_Access` | `Int8_Vec4_Row_Access` | `Int8_Vec4_Buffer_Access` | `Int8_Vec4_Mat_View` | `Int8_Vec4_Mat_View` |
| UInt16 C4 | `UInt16_Vec4_Access` | `UInt16_Vec4_Access` | — | `UInt16_Vec4_Row_Access` | `UInt16_Vec4_Row_Access` | `UInt16_Vec4_Buffer_Access` | `UInt16_Vec4_Mat_View` | `UInt16_Vec4_Mat_View` |
| Int16 C4 | `Int16_Vec4_Access` | `Int16_Vec4_Access` | — | `Int16_Vec4_Row_Access` | `Int16_Vec4_Row_Access` | `Int16_Vec4_Buffer_Access` | `Int16_Vec4_Mat_View` | `Int16_Vec4_Mat_View` |
| Int32 C4 | `Int32_Vec4_Access` | `Int32_Vec4_Access` | — | `Int32_Vec4_Row_Access` | `Int32_Vec4_Row_Access` | `Int32_Vec4_Buffer_Access` | `Int32_Vec4_Mat_View` | `Int32_Vec4_Mat_View` |
| Float16 C4 | `Float16_Vec4_Access` | `Float16_Vec4_Access` | — | `Float16_Vec4_Row_Access` | `Float16_Vec4_Row_Access` | `Float16_Vec4_Buffer_Access` | `Float16_Vec4_Mat_View` | `Float16_Vec4_Mat_View` |
| Float32 C4 | `Float32_Vec4_Access` | `Float32_Vec4_Access` | — | `Float32_Vec4_Row_Access` | `Float32_Vec4_Row_Access` | `Float32_Vec4_Buffer_Access` | `Float32_Vec4_Mat_View` | `Float32_Vec4_Mat_View` |
| Float64 C4 | `Float64_Vec4_Access` | `Float64_Vec4_Access` | — | `Float64_Vec4_Row_Access` | `Float64_Vec4_Row_Access` | `Float64_Vec4_Buffer_Access` | `Float64_Vec4_Mat_View` | `Float64_Vec4_Mat_View` |

The **Continuous buffer borrow** column applies to every continuous Mat of the
listed layout, including genuine N-D Mats and continuous N-D `Slice` views.
The flat array uses OpenCV element order with the final dimension varying
fastest (see "Scoped continuous whole-buffer borrowing" above). The
**Packed caller buffer -> `Mat`** column likewise covers both 2-D and genuine
packed N-D caller storage in that same element order. **Strided caller buffer
-> `Mat`** covers both 2-D row strides and genuine N-D element strides
(`Dimension_Stride_Array`, one complete-element stride per dimension, final
stride `1`). The row columns remain 2-D concepts.

For UInt8, UInt16, Int16, Int32, Float16, Float32 and Float64 Vec2 APIs, **one
vector is one complete two-channel Mat element**. Components are indexed 0 and 1; the vector
packages attach no semantic meaning to either channel. All seven depths support
2-D and N-D Get/Set,
copied and borrowed 2-D rows, continuous 2-D or N-D whole-buffer borrowing, and
packed or strided 2-D/N-D caller-owned views. Strides count complete Vec2
elements, not scalar channels. Borrowed references must not escape
callbacks.
UInt8 C2 elements occupy 2 bytes (scalar alignment 1); UInt16, Int16, and
Float16 C2 elements occupy 4 bytes (scalar alignment 2); Int32 and Float32 C2
elements occupy 8 bytes (scalar alignment 4); Float64 C2 elements
occupy 16 bytes. The predefined semantic-neutral value
types include `OpenCV.Core.UInt8_Vec2`, `OpenCV.Core.UInt16_Vec2`,
`OpenCV.Core.Int16_Vec2`, `OpenCV.Core.Int32_Vec2`, and
`OpenCV.Core.Float16_Vec2`, with component indices `0 .. 1`. UInt8, UInt16,
Int16, Int32, Float16, Float32, and Float64 each have complete C1/C2/C3/C4
typed and zero-copy access, and so does Int8 (see below): every supported
depth is complete. The 32 layouts include 24 vector layouts, with 24 vector
row packages and 32 buffer-access and 32 Mat-view packages.

For Vec3 APIs, **one Ada vector is one complete OpenCV element/pixel**, not one
scalar channel:

- UInt8 Vec3: 24 bits / 3 bytes per element, native alignment 1;
- UInt16 Vec3: 48 bits / 6 bytes per element, native alignment 2;
- Int16 Vec3: 48 bits / 6 bytes per element, native alignment 2;
- Int32 Vec3: 96 bits / 12 bytes per element, native alignment 4;
- Float16 Vec3: 48 bits / 6 bytes per element, native scalar alignment 2;
- Float32 Vec3: 96 bits / 12 bytes per element, native scalar alignment 4;
- Float64 Vec3: 192 bits / 24 bytes per element, native scalar alignment 8.

The predefined Vec3 packages are component-oriented and do not impose RGB,
BGR, XYZ, or any other semantic channel interpretation. All seven predefined
Vec3 layouts support 2-D Row/Column Get/Set and N-D `Index_Array` Get/Set.
One vector remains one complete OpenCV element. `Float16_Vec3` is an exact
three-component binary16 pixel type: indices `0 .. 2` are OpenCV channel
indices, not RGB or BGR names.

`UInt8_Vec4`, `UInt16_Vec4`, `Int16_Vec4`, `Int32_Vec4`, `Float16_Vec4`,
`Float32_Vec4`, and `Float64_Vec4` provide semantic-neutral components `0 .. 3`:
one Vec4 is one complete four-channel Mat element, not a single scalar.
No package assigns RGBA, BGRA, or XYZW meanings to channels. Each has
2-D/N-D Get/Set, copied and callback-scoped borrowed 2-D rows, continuous
whole-buffer borrowing, packed 2-D/N-D caller-owned views, and row-strided
2-D caller-owned views. Row strides count complete Vec4 elements, including
final-row padding.
UInt8 C4 elements occupy 4 bytes; UInt16, Int16, and Float16 C4 elements occupy
8 bytes (scalar alignment 2);
Int32 C4 elements occupy 16 bytes (native scalar alignment 4);
Float32 C4 elements occupy 16 bytes;
Float64 C4 elements occupy 32 bytes.
Float32 and Float64 now have complete typed C1/C2/C3/C4 families.

`UInt16_Access` provides scalar 2-D and N-D Get/Set for single-channel `CV_16U`
Mats. `UInt16_Row_Access` adds copied and callback-scoped zero-copy row access
for 2-D C1 Mats, including non-contiguous Regions. `UInt16_Buffer_Access` adds
continuous whole-buffer borrowing, and `UInt16_Mat_View` adds packed and
row-strided callback-scoped caller-owned views.

`OpenCV.Core.Int16_Vec2`, `Int16_Vec3`, and `Int16_Vec4` use
`OpenCV.Int16_Value` components in the full `-32768 .. 32767` signed domain.
Indexes are respectively `0 .. 1`, `0 .. 2`, and `0 .. 3`, with no semantic
channel names. One vector is one complete `CV_16S` Mat element (4, 6, or
8 bytes; native scalar alignment 2). Each width has matching `_Access`,
`_Row_Access`, `_Buffer_Access`, and `_Mat_View` packages: 2-D/N-D Get/Set,
copied and leased zero-copy 2-D rows, continuous whole-buffer borrowing,
and writable/read-only packed or strided 2-D/N-D caller-owned views. Strides
count complete vector elements. A Region row can be borrowed despite gaps;
non-contiguous whole buffers are rejected. Caller storage remains owned by
the caller, shallow Mat escape is forbidden, and Clone can escape independently.

`OpenCV.Core.Int32_Vec2`, `Int32_Vec3`, and `Int32_Vec4` model OpenCV
`cv::Vec2i`, `cv::Vec3i`, and `cv::Vec4i` as semantic-neutral complete Mat
elements. They preserve the exact `OpenCV.Int32_Value` signed 32-bit domain,
with component indices `0 .. 1`, `0 .. 2`, and `0 .. 3`. Elements occupy
8, 12, and 16 bytes respectively, with 4-byte native scalar alignment.
Each width has matching `_Access`, `_Row_Access`, `_Buffer_Access`, and
`_Mat_View` packages, including 2-D and N-D access, copied/borrowed rows,
continuous whole-buffer borrowing, and read-only/writable packed and strided
2-D/N-D caller-owned views. Strides count complete vectors, not channels.
The stable C ABI uses `int32_t` records and row buffers; OpenCV stores native
`int` vectors. The shim proves identical signed ranges and converts components
explicitly without assuming C++ type identity or aliasing the representations.

`Int8_Access` provides scalar 2-D and N-D Get/Set for single-channel `CV_8S`
Mats. `Int8_Row_Access` adds copied and callback-scoped zero-copy row access
for 2-D C1 Mats, including non-contiguous Regions. `Int8_Buffer_Access` adds
continuous whole-buffer borrowing, and `Int8_Mat_View` adds packed and
row-strided callback-scoped caller-owned views. All paths preserve the exact
signed 8-bit domain, `-128 .. 127`, without unsigned or floating-point
intermediates.

`OpenCV.Core.Int8_Vec2`, `Int8_Vec3`, and `Int8_Vec4` complete the signed
8-bit family: Int8 now has full C1/C2/C3/C4 typed and zero-copy coverage, so
every supported depth (UInt8, Int8, UInt16, Int16, Int32, Float16, Float32,
Float64) is complete for C1 through C4. Components are `OpenCV.Int8_Value`
in the exact signed `-128 .. 127` domain, indexed `0 .. 1`, `0 .. 2`, and
`0 .. 3` as OpenCV channel order with no XY, RGB, or other semantic meaning.
One vector is one complete `CV_8SC2`/`CV_8SC3`/`CV_8SC4` Mat element:
C2 = 2 bytes, C3 = 3 bytes, C4 = 4 bytes, native alignment 1. Each width has
matching `_Access` (2-D and N-D Get/Set), `_Row_Access` (copied rows and
callback-scoped zero-copy leased rows), `_Buffer_Access` (continuous 2-D/N-D
whole-buffer borrowing), and `_Mat_View` (writable and read-only packed and
strided 2-D/N-D caller-owned views; strides count complete vectors, not
scalar channels) packages. OpenCV defines no named signed-8 vector alias:
`Vec2b`/`Vec3b`/`Vec4b` are unsigned `Vec<uchar, N>` and are never used for
these layouts. Native storage is `cv::Vec<schar, N>`, where OpenCV's `schar`
is `signed char` in 4.1/4.10 and `int8_t` in 5.0; the stable C ABI uses
`opencv_core_int8_vec2`/`_vec3`/`_vec4` records and `int8_t` row buffers.
The shim statically proves that `schar` and `int8_t` cover exactly the same
one-byte signed domain (without requiring C++ type identity) and converts
every component explicitly; ABI buffers are never aliased as native vectors.

`Int16_Access` provides scalar 2-D and N-D Get/Set for single-channel `CV_16S`
Mats. `Int16_Row_Access` adds copied and callback-scoped zero-copy row access
for 2-D C1 Mats, including non-contiguous Regions. `Int16_Buffer_Access` adds
continuous whole-buffer borrowing, and `Int16_Mat_View` adds packed and
row-strided callback-scoped caller-owned views.

`Int32_Access` provides scalar 2-D and N-D Get/Set for single-channel `CV_32S`
Mats. `Int32_Row_Access` adds copied and callback-scoped zero-copy row access,
`Int32_Buffer_Access` adds continuous whole-buffer borrowing, and
`Int32_Mat_View` adds packed and row-strided callback-scoped caller-owned views.
All paths preserve exact signed 32-bit values without floating-point
intermediates.

`Float16_Access` provides scalar 2-D and N-D Get/Set for single-channel
`CV_16F` Mats. Access is bit-preserving: every binary16 encoding, including
signed zeros, subnormals, infinities, and NaN payloads, round-trips through
`Float16_From_Bits` / `Float16_Bits`. `Float16_Row_Access` adds copied and
callback-scoped zero-copy row access for 2-D C1 Mats, including
non-contiguous Regions, and likewise preserves exact binary16 object bits
without converting through Float32. `Float16_Buffer_Access` adds
callback-scoped zero-copy whole-buffer borrowing for continuous 2-D or N-D C1
Mats. Non-contiguous Regions still require row access. `Float16_Mat_View`
adds callback-scoped packed and row-strided caller-owned CV_16FC1 storage.
Packed views overlay a contiguous Ada array. Row-strided views use
`With_Writable_Strided_Mat_View` so a 2-D `Row_Stride` can skip padding
between logical rows; the `Shape`/`Strides` overload adds gapped N-D storage.
The caller owns the backing storage, OpenCV does not free it, and it must
remain alive for the callback lifetime. The main C1 FP16 data plane is now complete:
exact value representation, Float32 conversion, scalar access, row access,
continuous-buffer borrowing, packed external views, and strided external
views. `Add`, `Subtract`, `Multiply`, `Divide`, `Abs_Diff`, `Minimum`, and
`Maximum` additionally support Float16 with native OpenCV 5.x arithmetic and
an internal Float32 compatibility path on OpenCV 4.x. This does not add broad OpenCV 4.x FP16
algorithm coverage.
`Float16_Vec3` / `Float16_Vec3_Access` add exact-bit 2-D and N-D Get/Set for
ordinary three-channel `CV_16FC3` Mats. N-D `Index_Array` access addresses one
complete six-byte pixel and preserves every binary16 component encoding. `Float16_Vec3_Row_Access` adds copied and
callback-scoped zero-copy row access for 2-D C3 Mats, including non-contiguous
Regions, and likewise preserves exact binary16 component bits without converting
through Float32. `Float16_Vec3_Buffer_Access` adds callback-scoped zero-copy
whole-buffer borrowing for continuous 2-D or N-D C3 Mats. `Float16_Vec3_Mat_View` adds
callback-scoped packed and row-strided caller-owned CV_16FC3 storage. Packed
views overlay a contiguous Ada array of `Float16_Vec3.Vector` pixels.
Row-strided views use `With_Writable_Strided_Mat_View` so a 2-D `Row_Stride`
measured in complete C3 pixels can skip padding between logical rows. The main
C3 FP16 storage/access data plane is now complete: exact-bit pixel Get/Set,
copied rows, borrowed zero-copy rows, continuous whole-buffer borrowing, packed
caller-owned Mat views, and row-strided caller-owned Mat views. `Add`,
`Subtract`, `Multiply`, and `Divide` support Float16 C3 with the same
native-or-fallback policy as C1. This does not add broad OpenCV 4.x FP16 algorithm coverage. Component 0, 1,
and 2 correspond to OpenCV channels 0, 1, and 2; Core does not assign RGB or
BGR meaning.

`Float16_Vec2` and `Float16_Vec4` complete the Float16 family: Float16 now has
full C1/C2/C3/C4 typed and zero-copy coverage. Each component is a
`Float16_Value`, i.e. the exact stored IEEE-754 binary16 encoding, indexed
`0 .. 1` or `0 .. 3` as OpenCV channel order with no real/imaginary, XY, RGB,
or RGBA meaning. One vector is one complete Mat element: C2 = 4 bytes,
C3 = 6 bytes, C4 = 8 bytes, with native storage alignment 2. Each width has
`_Access` (exact-bit 2-D and N-D Get/Set), `_Row_Access` (copied rows and
callback-scoped zero-copy leased rows), `_Buffer_Access` (continuous 2-D/N-D
whole-buffer borrowing), and `_Mat_View` (writable and read-only packed and
strided 2-D/N-D caller-owned views; strides count complete vectors, not
scalar channels). Signed zeros, subnormals, infinities, and signaling or
quiet NaN payloads are never converted or canonicalized. The stable C ABI
uses `opencv_core_float16_vec2`/`opencv_core_float16_vec4` records and
`uint16_t` row buffers carrying raw binary16 bit patterns. The shim copies
exactly 4 or 8 bytes of untyped Mat storage; it never names a C++ half type
or half-vector alias. OpenCV 4.1, 4.10, and 5.0 define no such alias in
`matx.hpp` (only `Vec2b`/`s`/`w`/`i`/`f`/`d` and friends), and the public half
type itself is spelled differently across releases (`cv::float16_t` versus
`cv::hfloat`), so the binding relies only on the stable `CV_16FC2`/`CV_16FC4`
storage representation. The existing channel-agnostic Float16 arithmetic
path accepts C2/C4 operands (`Add` and `Multiply` are regression-tested with
exact finite values); no new arithmetic API was added, and `Transform` still
rejects Float16 sources.

`Float64_Access` provides scalar 2-D and N-D Get/Set plus non-finite value
classification. `Float64_Row_Access` adds copied and callback-scoped zero-copy
row access for 2-D C1 Mats, including non-contiguous Regions.
`Float64_Buffer_Access` adds callback-scoped zero-copy whole-buffer borrowing
for continuous 2-D or N-D Mats. `Float64_Mat_View` adds callback-scoped packed and
row-strided caller-owned CV_64FC1 storage. Packed views overlay a contiguous
Ada array. Row-strided views use `With_Writable_Strided_Mat_View` so a 2-D
`Row_Stride` can skip padding between logical rows; the `Shape`/`Strides`
overload adds gapped N-D storage. The caller owns the backing storage, OpenCV
does not free it, and it must remain alive for the callback lifetime.

Generic pure-Ada value abstractions are also provided:

```ada
generic
   type Element_Type is private;
   Length : Positive;
package OpenCV.Core.Vectors;
```

and:

```ada
generic
   type Element_Type is private;
   Row_Count : Positive;
   Column_Count : Positive;
package OpenCV.Core.Fixed_Matrices;
```

A predefined Float32 3x3 fixed matrix and copy conversions to/from `Mat` are
included. C++ `cv::Matx` objects do not cross the ABI.
