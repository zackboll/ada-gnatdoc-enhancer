# Ownership and views

[README](../README.md) · [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) · [Building and Contributing](documentation.md)

This guide is published as HTML on the documentation site and maintained as
Markdown in the source repository. The public Ada specifications are authoritative for exact profiles
and per-overload restrictions. Examples below include both complete programs
and fragments intended for the surrounding application.

## Contents

- [View examples](#view-examples)
- [Ownership, views, and zero-copy access](#ownership-views-and-zero-copy-access)
- [UMat and the Transparent API baseline](#umat-and-the-transparent-api-baseline)
- Related: [typed access matrix](typed-access-guide.md#typed-access-matrix) and
  [destination-operation contracts](core-operations-guide.md#public-api-overview)

## View examples

### Create from `Size`

```ada
Image : Mat :=
  Create
    (Dimensions   => (Width => 640, Height => 480),
     Element_Type => (Depth => Float32, Channels => 1));

Dims : constant OpenCV.Size := Image.Dimensions;
```

`OpenCV.Size.Width` maps to columns and `OpenCV.Size.Height` maps to rows.

### Create a shared Region

```ada
ROI : Mat :=
  Image.Region
    ((X      => 100,
      Y      => 50,
      Width  => 200,
      Height => 100));
```

A Region has its own `Mat` header but shares the parent's storage.
`OpenCV.Rect` origins are signed so they can represent general OpenCV rectangles,
including negative `X`/`Y`. `Mat.Region` still requires a nonnegative
zero-based ROI origin that fits inside the source.

---

### Borrow a row without copying

```ada
with OpenCV.Core.Float32_Row_Access;

procedure Inspect_Row
  (Data : aliased OpenCV.Core.Float32_Row_Access.Row_Array)
is
begin
   -- Data (0) is column 0 of the borrowed row.
   null;
end Inspect_Row;

OpenCV.Core.Float32_Row_Access.With_Read_Only_Row
  (Image   => Image,
   Row     => 0,
   Process => Inspect_Row'Access);
```

The callback is the lifetime boundary. The row directly aliases `Mat` storage
and no pixel values are copied.

### Wrap caller-owned packed storage in a temporary `Mat`

```ada
with OpenCV.Core;
with OpenCV.Core.UInt8_Access;
with OpenCV.Core.UInt8_Mat_View;

procedure External_Buffer_Example is
   Data : aliased OpenCV.Core.UInt8_Mat_View.Buffer_Array :=
     (11 => 10,
      12 => 20,
      13 => 30,
      14 => 40,
      15 => 50,
      16 => 60);

   procedure Process (Image : in out OpenCV.Core.Mat) is
   begin
      OpenCV.Core.UInt8_Access.Set
        (Image, Row => 1, Column => 0, Value => 200);
      -- Data (14) is now 200 immediately. There is no copy-back phase.
   end Process;
begin
   OpenCV.Core.UInt8_Mat_View.With_Writable_Mat_View
     (Data, Rows => 2, Columns => 3, Process => Process'Access);
end External_Buffer_Example;
```

`Data'Length` must equal `Rows * Columns`. The Ada lower bound is arbitrary.
The temporary `Mat` does not own the caller's storage.

### Wrap caller-owned packed N-D storage in a temporary `Mat`

Every `*_Mat_View` package also overloads `With_Writable_Mat_View` with a
`Shape` parameter that selects a genuine packed N-dimensional `Mat`:

```ada
with OpenCV.Core;
with OpenCV.Core.Float32_Access;
with OpenCV.Core.Float32_Mat_View;

procedure External_Volume_Example is
   Volume : aliased OpenCV.Core.Float32_Mat_View.Buffer_Array :=
     (11 .. 34 => 0.0);

   procedure Process (Image : in out OpenCV.Core.Mat) is
   begin
      --  Image.Shape = (2, 3, 4) and Image.Is_Continuous.
      OpenCV.Core.Float32_Access.Set (Image, (1, 2, 3), 1.5);
      --  Volume (34) is now 1.5 immediately.
   end Process;
begin
   OpenCV.Core.Float32_Mat_View.With_Writable_Mat_View
     (Volume, Shape => (2, 3, 4), Process => Process'Access);
end External_Volume_Example;
```

`Shape'Length` must be in `2 .. 32`, every extent must be positive, and
`Data'Length` must equal `product (Shape)` exactly. Shape iteration order is
OpenCV dimension order regardless of `Shape'First`, and neither Ada lower bound
is visible through the `Mat`. The final dimension varies fastest: for
`Shape => (D1, ..., Dn)` the zero-based index `(I1, ..., In)` is
`Data (Data'First + ((I1 * D2 + I2) * D3 + ...) * Dn + In)`, the same order used
by N-D `Get`/`Set` and N-D continuous buffer borrowing. For Vec2/Vec3/Vec4
packages one `Data` entry is one complete Mat element, so a `(2, 3, 4)` Float64
C4 view takes 24 `Vector` values, not 96 scalars. `Shape => (Rows, Columns)`
produces the same 2-D geometry as the `Rows`/`Columns` overload, which is
unchanged. Gapped N-D storage uses the strided N-D overload described below.
OpenCV 5.0's native `MatShape` capacity is 10 dimensions
(`MatShape::MAX_DIMS`). The binding rejects N-D construction, view, and
reshape requests above that native capacity with `OpenCV_Error` before
invoking the affected OpenCV constructor or reshape, so on OpenCV 5.0 an
11 .. 32 dimensional view never runs `Process`. OpenCV 4.x retains the
historic 32-dimensional limit. Public signatures are unchanged: the
compatibility restriction is enforced below the Ada API, in the C++ shim.

### Read-only caller-owned storage

The same thirty-two typed `*_Mat_View` packages also provide
`With_Read_Only_Mat_View` (packed 2-D and N-D) and
`With_Read_Only_Strided_Mat_View` (row-strided 2-D and arbitrary-strided N-D).
For example, an aliased constant may be passed without copying pixels:

```ada
with Ada.Text_IO;
with OpenCV;
with OpenCV.Core;
with OpenCV.Core.UInt8_Access;
with OpenCV.Core.UInt8_Mat_View;

procedure Inspect_Constant_Example is
   Data : aliased constant OpenCV.Core.UInt8_Mat_View.Buffer_Array :=
     (11 => 1, 12 => 2, 13 => 3, 14 => 4, 15 => 5, 16 => 6);

   procedure Inspect (Image : OpenCV.Core.Mat) is
   begin
      Ada.Text_IO.Put_Line
        (OpenCV.UInt8_Value'Image
           (OpenCV.Core.UInt8_Access.Get (Image, 1, 2)));
   end Inspect;
begin
   OpenCV.Core.UInt8_Mat_View.With_Read_Only_Mat_View
     (Data, Rows => 2, Columns => 3, Process => Inspect'Access);
end Inspect_Constant_Example;
```

Read-only views provide zero-copy input to Core algorithms and cooperating Ada
OpenCV modules via `Module_Interop.With_Input_Handle`. The callback receives
`Image` by mode `in`, so normal in-place Ada operations and output handles
requiring `in out Mat` cannot accept it. This is an Ada capability restriction,
**not** OS/page protection: the native external-data header uses OpenCV's
mutable pointer representation. The caller retains ownership; shallow escape
is rejected and `Clone` creates independent storage. Read-only views obey the
same geometry, full-stride capacity, and callback lifetime rules as writable
views. Input-only operations remain available during the callback.

### Wrap row-strided caller-owned storage

`OpenCV.Core.Float32_Mat_View` also provides a row-strided overload:

```ada
OpenCV.Core.Float32_Mat_View.With_Writable_Mat_View
  (Data                => Data,
   Rows                => 3,
   Columns             => 4,
   Row_Stride_Elements => 8,
   Process             => Process'Access);
```

Each logical row exposes the first `Columns` Float32 elements of its stride.
Padding remains outside the `Mat`. `Row_Stride_Elements` must be at least
`Columns`, and the caller retains ownership of the complete backing buffer.

`OpenCV.Core.Float64_Mat_View` provides a separately named operation whose
stride is also measured in complete Ada elements rather than bytes:

```ada
OpenCV.Core.Float64_Mat_View.With_Writable_Strided_Mat_View
  (Data       => Data,
   Rows       => 3,
   Columns    => 4,
   Row_Stride => 6,
   Process    => Process'Access);
```

`Row_Stride` is the number of `Float64_Value` elements from the start of one
logical row to the next and must be at least `Columns`. `Data'Length` must be
at least `Rows * Row_Stride`, including a complete final-row stride. A buffer
that reaches only the last logical element is rejected. Padding and extra
trailing storage are not logical Mat elements and are left untouched.

The same full-stride rule applies to the integer C1 view packages. For example,
this UInt16 buffer contains two complete six-element strides for a `2 x 4`
logical Mat. The two padding elements after each logical row remain outside the
Mat and must still exist after the final row:

```ada
with OpenCV.Core;
with OpenCV.Core.UInt16_Access;
with OpenCV.Core.UInt16_Mat_View;

procedure Padded_UInt16_Example is
   Data : aliased OpenCV.Core.UInt16_Mat_View.Buffer_Array :=
     (11 => 10, 12 => 20, 13 => 30, 14 => 40, 15 => 999, 16 => 999,
      17 => 50, 18 => 60, 19 => 70, 20 => 80, 21 => 999, 22 => 999);

   procedure Process (Image : in out OpenCV.Core.Mat) is
   begin
      OpenCV.Core.UInt16_Access.Set
        (Image, Row => 1, Column => 2, Value => 65_535);
      --  Data (19) changes immediately. Padding Data (15), Data (16),
      --  Data (21), and Data (22) remains outside the logical Mat.
   end Process;
begin
   OpenCV.Core.UInt16_Mat_View.With_Writable_Strided_Mat_View
     (Data, Rows => 2, Columns => 4, Row_Stride => 6,
      Process => Process'Access);
   --  The caller still owns Data. The temporary Mat was callback-scoped.
end Padded_UInt16_Example;
```

### Wrap gapped (strided) N-D caller-owned storage

Every `*_Mat_View` package also overloads `With_Writable_Strided_Mat_View`
with a `Shape` and a `Strides : Dimension_Stride_Array`, supplying one stride
per dimension:

```ada
with OpenCV.Core;
with OpenCV.Core.Float32_Access;
with OpenCV.Core.Float32_Mat_View;

procedure Gapped_Volume_Example is
   --  2 planes of 3 rows of 4 elements, each row padded to 6 elements and
   --  each plane padded to 20 elements: 2 * 20 = 40 elements in total.
   Volume : aliased OpenCV.Core.Float32_Mat_View.Buffer_Array :=
     (0 .. 39 => 0.0);

   procedure Process (Image : in out OpenCV.Core.Mat) is
   begin
      --  Image.Shape = (2, 3, 4); Image.Is_Continuous is False.
      OpenCV.Core.Float32_Access.Set (Image, (1, 2, 3), 1.5);
      --  Volume (1 * 20 + 2 * 6 + 3) = Volume (35) is now 1.5.
   end Process;
begin
   OpenCV.Core.Float32_Mat_View.With_Writable_Strided_Mat_View
     (Volume,
      Shape   => (2, 3, 4),
      Strides => (20, 6, 1),
      Process => Process'Access);
end Gapped_Volume_Example;
```

Strides are measured in **complete Mat elements**, never bytes. For Vec2,
Vec3, and Vec4 packages one stride unit is one complete vector element (for
example one 32-byte Float64 Vec4), not one scalar channel. For
`Shape => (D1, ..., Dn)` and `Strides => (S1, ..., Sn)` the zero-based index
`(I1, ..., In)` is `Data (Data'First + I1 * S1 + ... + In * Sn)`. The
lower bounds of `Shape`, `Strides`, and `Data` are irrelevant.

The contract is:

- `Shape'Length` in `2 .. 32` (OpenCV 5.0: at most 10, enforced by the shim)
  with positive extents, and `Strides'Length = Shape'Length`;
- the final stride is exactly `1`;
- every outer stride covers its complete nested block:
  `Strides (I) >= Strides (I + 1) * Shape (I + 1)`, so overlapping or
  backwards layouts are rejected;
- `Data'Length >= Shape (first) * Strides (first)`. OpenCV's native header
  spans the complete outer stride (`datalimit = data + size[0] * step[0]`),
  so the padding after the final logical outer block must exist. Storage that
  ends at the final logical element is rejected. Extra trailing storage beyond
  that extent is allowed and lies outside the header.

Padding is never a logical element and is never touched. `Is_Continuous`
reports the actual layout: a gapped layout is non-continuous, so whole-buffer
borrowing rejects it before its callback runs, while packed-equivalent strides
such as `(12, 4, 1)` for `(2, 3, 4)` are continuous and can be borrowed.
`Shape => (Rows, Columns)`, `Strides => (Row_Stride, 1)` has exactly the same
geometry as the 2-D row-strided overload. Ownership, callback lifetime, and
the no-escape rules are identical to the packed views; `Clone` returns
independent packed storage holding only the logical values.

### Select a lower-dimensional view by fixing dimensions

`With_Selected_View` fixes chosen source dimensions to one index and **drops**
them, while the other dimensions keep ordinary half-open ranges. The result
aliases the source; no data is copied.

```ada
with OpenCV.Core;
with OpenCV.Core.Float32_Access;

procedure Selected_Plane_Example is
   use OpenCV.Core;

   Volume : Mat :=
     Create (Shape => (2, 3, 2, 4), Element_Type => (Float32, 1));

   procedure Process (View : in out Mat) is
   begin
      --  View.Shape = (3, 4); View (J, K) is Volume (1, J, 1, K).
      OpenCV.Core.Float32_Access.Set (View, (2, 3), 1.5);
      --  Volume (1, 2, 1, 3) is now 1.5.
   end Process;
begin
   With_Selected_View
     (Volume,
      ((Kind => Fix_Index,  Index  => 1),
       (Kind => Keep_Range, Bounds => (Start => 0, Stop => 3)),
       (Kind => Fix_Index,  Index  => 1),
       (Kind => Keep_Range, Bounds => (Start => 0, Stop => 4))),
      Process'Access);
end Selected_Plane_Example;
```

There is one selector per source dimension, applied in iteration order; the
array's lower bound is irrelevant. `Keep_Range` requires
`Start < Stop <= extent`; `Fix_Index` requires `Index < extent`. The source
must be a nonempty OpenCV-owned Mat with at least three dimensions; an
ordinary `Slice` is a valid source. At least one dimension must be fixed and
at least two must be kept, so no 1-D or scalar view is produced.

The **final source dimension must be kept**. This is an OpenCV `Mat`
representation rule, not an implementation shortcut: OpenCV always uses the
element size as the step of a Mat's last dimension, so dropping the source's
final axis would leave a last axis with a larger stride that no ordinary Mat
header can describe without copying.

Retained source strides are inherited. Dropping only leading dimensions
yields a continuous view that whole-buffer borrowing accepts. Dropping a
middle dimension keeps the outer stride, so the example above is
non-continuous (rows begin eight elements apart): whole-buffer borrowing
rejects it while 2-D row borrowing works. `View` is valid only during
`Process`. It keeps the source allocation alive even if the source is rebound
inside the callback, but shallow copies, `Slice`, `Reshape`, and
`Module_Interop` output handles are rejected. `Clone` is the escape path.
Selecting from a temporary caller-buffer view is rejected; `Clone` it first.

---

## Ownership, views, and zero-copy access

`OpenCV.Core.Mat` is a tagged private Ada controlled type.

### Ordinary assignment is shallow

```ada
B := A;
```

`B` receives a distinct `cv::Mat` header sharing the same OpenCV-owned storage
with `A`. Mutations through either alias are visible through the other.

### `Clone` is deep

```ada
B := A.Clone;
```

The clone owns independent pixel storage.

### Shared-storage views

The public API includes no-copy views such as:

- `Region`
- `Row_View`
- `Column_View`
- row-range and column-range view overloads
- `Slice`
- `Reshape`, including Shape-based N-D overloads
- `Diagonal_View`

For ordinary OpenCV-owned Mats, these headers retain the shared allocation by
normal OpenCV reference counting.

`With_Selected_View` is the callback-scoped, dimension-dropping counterpart.
Its view keeps the source allocation alive for the callback and follows the
temporary-view no-escape rules; `Slice` itself is unchanged and never drops
dimensions.

### Retained ROI geometry and header adjustment

Both `Mat` and `UMat` provide `Locate_Region` and `Adjust_Region` for nonempty,
**exactly 2-D** headers, at any supported depth/channel count. `Slice` remains
the N-D view abstraction. `Region_Location` contains `Whole_Size : OpenCV.Size`
and `Offset : OpenCV.Point`: X is a zero-based column, Y a zero-based row.
Nested Regions locate against the original retained allocation, not merely
their immediate parent view. Whole_Size describes OpenCV's retained storage
geometry; it is not a parent Ada Mat, an ownership handle, or evidence that
the original parent variable is still alive. Reference-counted Region storage
remains usable after that variable finalizes.

```ada
Location : constant Region_Location := ROI.Locate_Region;
--  Move each boundary outward by one, clipping to the retained parent.
ROI.Adjust_Region (Top => 1, Bottom => 1, Left => 1, Right => 1);
```

Each argument has the strong signed type `Region_Adjustment` (32 bits).
Positive top/left moves upward/leftward, positive bottom/right downward/rightward;
negative adjustments contract inward. Native clipping permits over-large
expansion requests. After clipping, OpenCV **swaps crossed opposing boundaries**,
so extreme contraction can have a non-intuitive nonempty result. Equal endpoints
can produce an empty header, which these operations subsequently reject.
Requests whose native signed intermediates would overflow raise `OpenCV_Error`
without changing the header.
Unsafe native parent-span arithmetic or empty-result Mat pointers are likewise
rejected rather than invoking undefined native behavior.

Adjustment changes only that header, never clones or allocates pixel storage.
Shallow aliases and the parent keep independent geometry while overlapping
pixels remain shared; Clone remains independent. Ordinary whole headers can
also shrink. Continuity is recomputed, but native `Is_Submatrix` is **not**:
it can remain true after full expansion or false after whole-header shrink.
Use `Locate_Region` and `Rows`/`Columns` as authoritative geometry.

Callback-scoped caller-buffer and synthetic selected Mat views reject both
parent-geometry operations, protecting their logical storage/lifetime contract
(including row padding). UMat operates directly on its native header and
requires **no host mapping or transfer**.

### Copied row access

The UInt8, Int8, UInt16, Int16, Int32, Float16, Float32, and Float64 C1 row
packages and all twenty-four Vec2/Vec3/Vec4 row packages provide `Read_Row` /
`Write_Row` APIs. Caller arrays may use
arbitrary lower bounds; values map in iteration order to matrix columns.

These are copy-based APIs and are useful when the caller wants an ordinary Ada
array with no borrowed lifetime.

### Scoped zero-copy row borrowing

The same row-access families provide:

```text
With_Read_Only_Row
With_Writable_Row
```

The callback receives a zero-based array that directly overlays one logical
OpenCV row. Row borrowing works with non-contiguous 2-D Regions because only
the active logical row is exposed; inter-row padding is never exposed.

A shallow `Mat` lease is retained during the callback so the underlying OpenCV
allocation cannot disappear merely because another header is rebound or
finalized. Integer whole-buffer tests observe that specific allocation: it
remains live after the ordinary owners are released, and its deallocation is
observed exactly once when the lease ends. That is test instrumentation, not
a formal lifetime proof. The lease is a lifetime mechanism, not thread
synchronization.


### Scoped continuous whole-buffer borrowing

The thirty-two matching buffer-access packages provide:

```text
With_Read_Only_Buffer
With_Writable_Buffer
```

The callback receives one flat zero-based array of `Natural (Image.Total)`
elements. Nonempty Mats must be continuous (`Is_Continuous`); this applies to
ordinary 2-D Mats and to genuine N-D Mats alike. Continuous Regions and
continuous N-D `Slice` views are accepted; gapped Regions and gapped N-D
Slices are rejected before the callback runs.

Elements appear in ordinary OpenCV contiguous order: the final dimension
varies fastest. For a Mat with `Shape => (D1, D2, ..., Dn)`, zero-based index
`(I1, I2, ..., In)` is at flat offset
`((I1 * D2 + I2) * D3 + ...) * Dn + In`. For example, in a `(2, 3, 4)` Mat,
`(I, J, K)` is `Data (((I * 3) + J) * 4 + K)`. For a 2-D Mat this is the
familiar `Data (Row * Image.Columns + Column)`. One array element is always
one complete Mat element: a `(2, 3, 4)` Float64 C4 Mat yields
`Data'Length = 24` Vec4 values, not 96 scalars.
There is no per-row copy and no write-back phase. The callback lifetime bounds
the borrowed view; callers must not retain a reference or address afterward.
Float64 C1 buffer access directly overlays native CV_64F storage without
conversion. Use Float64 row access for non-contiguous 2-D Regions. Float16
C2, C3, and C4 buffer access likewise overlays native CV_16FC2/C3/C4 elements
as packed `Float16_Vec2`/`Float16_Vec3`/`Float16_Vec4` vectors without
converting through Float32.

### Caller-owned buffer -> temporary `Mat`

The thirty-two Mat-view packages provide the reverse zero-copy direction:

```text
OpenCV.Core.UInt8_Mat_View
OpenCV.Core.Int8_Mat_View
OpenCV.Core.UInt16_Mat_View
OpenCV.Core.Int16_Mat_View
OpenCV.Core.Int32_Mat_View
OpenCV.Core.Float32_Mat_View
OpenCV.Core.Float64_Mat_View
OpenCV.Core.Float16_Mat_View
OpenCV.Core.UInt8_Vec2_Mat_View
OpenCV.Core.Int8_Vec2_Mat_View
OpenCV.Core.UInt16_Vec2_Mat_View
OpenCV.Core.Int16_Vec2_Mat_View
OpenCV.Core.Int32_Vec2_Mat_View
OpenCV.Core.Float16_Vec2_Mat_View
OpenCV.Core.Float32_Vec2_Mat_View
OpenCV.Core.Float64_Vec2_Mat_View
OpenCV.Core.UInt8_Vec3_Mat_View
OpenCV.Core.Int8_Vec3_Mat_View
OpenCV.Core.UInt16_Vec3_Mat_View
OpenCV.Core.Int16_Vec3_Mat_View
OpenCV.Core.Int32_Vec3_Mat_View
OpenCV.Core.Float32_Vec3_Mat_View
OpenCV.Core.Float16_Vec3_Mat_View
OpenCV.Core.Float64_Vec3_Mat_View
OpenCV.Core.UInt8_Vec4_Mat_View
OpenCV.Core.Int8_Vec4_Mat_View
OpenCV.Core.UInt16_Vec4_Mat_View
OpenCV.Core.Int16_Vec4_Mat_View
OpenCV.Core.Int32_Vec4_Mat_View
OpenCV.Core.Float16_Vec4_Mat_View
OpenCV.Core.Float32_Vec4_Mat_View
OpenCV.Core.Float64_Vec4_Mat_View
```

`With_Writable_Mat_View` creates a callback-scoped `cv::Mat` header over the
actual caller-owned Ada array. The public buffer formal is explicitly
`aliased in out`, so the native header directly denotes the caller's storage.

Packed views are available for all thirty-two typed layouts above, both as 2-D
(`Rows`, `Columns`) and as genuine N-D (`Shape`, 2 .. 32 dimensions on
OpenCV 4.x; at most 10 on OpenCV 5.0) views.
Packed N-D views are always continuous, so the matching `*_Buffer_Access`
package can borrow the same caller storage again inside the callback without
copying. Every listed layout also supports strided storage, both as a 2-D
explicit row stride and as genuine gapped N-D storage
(`With_Writable_Strided_Mat_View (Data, Shape, Strides, Process)`), so a Mat
can represent the logical elements of padded caller-owned rows, planes, or
higher blocks without copying their padding. N-D strides are expressed in
complete Mat elements, one per dimension, and the final dimension's stride is
`1`. Except for the established Float32 2-D overload, the 2-D row-strided
views use `With_Writable_Strided_Mat_View` and measure `Row_Stride` in
complete Ada elements rather than bytes. For Vec2/Vec3/Vec4 layouts, one
element (and one stride unit) is one complete vector pixel, not one scalar
channel.

Important lifetime rule: a temporary external-buffer Mat may not create a
shallow alias that could outlive the callback. Ordinary `Mat` assignment and
no-copy view operations (including `Region`, `Slice`, and `Reshape`) are
therefore rejected for these temporary external views, whether 2-D or N-D.
This is the external-buffer lifetime policy, not a missing N-D capability.
`Clone` remains allowed because it creates independent OpenCV-owned storage
that can safely outlive the callback, and a clone can then be sliced or
reshaped normally.

The external-data `Mat` header is destroyed at callback exit, including during
exception unwinding; the caller's Ada array is never freed by OpenCV.

For a row-strided or N-D strided external view, `Is_Continuous` reflects
OpenCV's actual layout rules. A view with padding between logical elements is
non-contiguous, so operations requiring a single packed buffer must reject it;
row-based, N-D element access, and other non-contiguous-aware operations can
still be used. Strides that describe packed storage are continuous.

Caller storage must remain alive throughout the callback, and OpenCV never
owns or frees it. Row borrowing remains zero-copy and exposes exactly the
logical `Columns` elements, never padding. Whole-buffer borrowing rejects a
non-contiguous multirow strided view before invoking its callback.

---

## UMat and the Transparent API baseline

UMat-native `Bitwise_And`, `Bitwise_Or`, `Bitwise_Xor`, `Bitwise_Not`
and their masked overloads operate on stored bits (including exact Float16
bits). `Compare` and scalar-bounded `In_Range` return UInt8 C1 UMat masks;
these masks feed masked UMat operations directly, without a Mat round-trip.
Masked UMat operations require UMat masks; Mat operations still require Mat
inputs and masks. Mixed Mat/UMat operands or masks are not supported. OpenCL
is optional, and UMat does not guarantee GPU execution.
Binary bitwise operands require matching 2-D rows, columns, depth and channels;
unmasked `Bitwise_Not` also accepts N-D. Masks require matching rows and
columns, UInt8 depth and one channel. `Compare` requires compatible 2-D C1
operands; scalar `In_Range` accepts N-D with at most four channels and returns
one mask value per element. Empty `In_Range` raises `OpenCV_Error`. A typed
empty bitwise result retains its source type and 2-D shape; empty `Compare`
releases its result, as with the established Mat overload.

`OpenCV.Core.UMat` is a controlled, Core-owned `cv::UMat` header behind an
opaque C handle. Default construction yields an empty native UMat. Use
`Create_UMat (Rows, Columns, Element_Type)` or
`Create_UMat (Shape, Element_Type)` for 2-D or N-D storage. Shape arrays are
read in Ada iteration order; UMat uses the existing `Mat_Type`, `Depth_Type`,
`Channel_Count`, `Dimension_Array`, and `Mat_Size`. On OpenCV 4.1 through 4.10,
shapes may contain 2 through 32 dimensions; OpenCV 5.0's native MatShape
capacity limits both Mat and UMat to 10. UMat provides `Is_Empty`,
`Dimension_Count`, `Extent`, `Shape`, `Rows`, `Columns`, `Depth`, `Channels`,
`Element_Type`, `Total`, `Element_Size`, `Channel_Size`, `Is_Continuous`, and
`Is_Submatrix`. As for Mat, Rows and Columns reject genuine N-D arrays.

Ada assignment creates a distinct native UMat header sharing underlying
storage; finalizing either header leaves the other usable. `Clone` is an
explicit independent deep copy. `Region` and half-open N-D `Slice` are shallow
views that retain the allocation; `Copy_To` returns an independent UMat via
native UMat copy, not a Mat round-trip. `Set_To` fills complete C1 through C4
elements using `OpenCV.Scalar`. The `Convert_To` function returns an independent
native UMat conversion; its destination-taking procedure permits native storage
reuse/reallocation. Nonempty conversion retains shape and channels; see
[conversion semantics](core-operations-guide.md#conversion-and-element-wise-mathematics) for Regions,
self-conversion, and version-dependent empty metadata.

Because Ada forbids one dispatching operation on *two* unrelated tagged
types, independent host transfers live in `OpenCV.Core.Transfers`:

```ada
with OpenCV.Core.Transfers;
Device : OpenCV.Core.UMat := OpenCV.Core.Transfers.To_UMat (Host);
Copy   : OpenCV.Core.Mat  := OpenCV.Core.Transfers.To_Mat (Device);
```

Both transfers copy logical contents independently of source lifetime, even
for a non-contiguous Mat Region. They do not expose a mapped Mat view.
For typed inspection of UMat contents, transfer to an independent Mat and use
the existing Mat typed access packages. There is no direct mapped typed UMat
access or public OpenCL context/device/queue/raw pointer API in this release.

Cooperating OpenCV Ada module crates can borrow callback-scoped
`Input_UMat_Handle` and `Output_UMat_Handle` capabilities through
`OpenCV.Core.Module_Interop`. This is module implementation infrastructure,
not the normal application API: applications should use `OpenCV.Core.UMat`.
The installed `opencv_core_module_bridge.hpp` lets private module shims
resolve these capabilities to the actual borrowed `const cv::UMat *` or
`cv::UMat *` header. No Mat transfer, host representation, or `getMat()` mapping
occurs in the bridge. Modules can pass these headers directly to OpenCV
InputArray/OutputArray operations; output operations may rebind the actual
Core UMat header, and Core observes that rebinding after the callback.
Core retains ownership of the opaque wrapper and native header. Neither the
handle nor the native pointer may be saved for later use; the pointer must
not be retained or deleted after the callback/call scope. No ownership
transfer occurs. All cooperating shims must use a compatible OpenCV ABI and
installation with Core. OpenCL remains optional, and GPU execution is not
guaranteed.

All public allocations use `USAGE_DEFAULT`; host/device/shared allocation
preferences are intentionally deferred. OpenCL need not be compiled in,
available, enabled, or backed by a device: CPU fallback is required behavior,
and the test suite explicitly disables OpenCL while exercising the public
operations. **UMat enables OpenCV's Transparent API dispatch where native
operations support it. It is not a guarantee that an operation executes on a
GPU.** `Add`, `Subtract`, `Multiply`, `Divide`, `Abs_Diff`, `Minimum`,
`Maximum`, `Add_Weighted`, and `Scale_Add` accept two UMat operands and return
independent UMat results. No Mat transfer or mapping is used in these paths.
The first seven operations and `Scale_Add` require matching 2-D shape, depth,
and channels. `Add_Weighted` accepts matching N-D shape, depth, and channels,
just like its Mat overload. On OpenCV 4.x Float16 `Add_Weighted` widens UMat
operands to Float32 UMat, computes using double Alpha/Beta/Gamma, then narrows
once; OpenCV 5 uses native Float16. Float16 `Scale_Add` widens UMat operands on
all supported versions, narrows Scale to Float32 before the native Float32
kernel, then narrows the result once. SIMD/FMA rounding may vary by platform.
`Normalize`, `Sqrt`, `Exp`, `Log`, `Pow`, `Magnitude`, `Phase`,
`Cart_To_Polar`, and `Polar_To_Cart` also execute UMat-native, through shared
typed Mat/UMat helpers with no binding-side Mat temporaries or transfers.
Normalize keeps the source depth, accepts N-D, and offers L1, L2, Infinity,
and Min_Max without masks. Float16 norm normalization uses native support;
Float16 Min_Max is unsupported in OpenCV 4.x and supported in OpenCV 5.
Float16 Infinity also retains native version/backend differences (CPU 4.1/4.6
have incorrect half reduction results; 4.10/5.0 correct them). No new half
widening or normalization policy is introduced.

Both `Mat` and `UMat` offer independent results and reusable destinations:

```ada
Result := Source.Normalize (Kind => L2, Alpha => 1.0);
Source.Normalize
  (Destination => Existing,
   Kind        => L2,
   Alpha       => 1.0);
```

The procedure uses the actual native destination header. Compatible shape,
source depth, and channels reuse storage, including interior `Region` storage
still shared with its parent and existing shallow aliases. Incompatible shape
or type can reallocate; an incompatible Region may detach while old aliases
retain the original parent storage. Exact self (`Source.Normalize (Source, ...)`)
and distinct same-layout shallow aliases are supported. Arbitrarily partially
overlapping Regions are **not** guaranteed. N-D and unmasked multichannel
normalization remain supported; there is no destination depth parameter.

For L1/L2/Infinity, Alpha is the target norm, Beta is ignored, and a zero norm
uses native zero scale. Min_Max uses the sorted Alpha/Beta bounds; equal bounds
produce a constant, and constant input maps to the lower bound. Native integer
rounding/saturation and floating approximation remain unchanged.

Empty sources release destination pixels. OpenCV 4.x Mat release retains the
old destination type; OpenCV 5.0 Mat recreates the empty source type. The existing
UMat empty-storage safety helper releases ordinary empty outputs, retaining old
type metadata even on 5.0 (where release resets dimension count to zero, giving
a null `Shape`). Empty Float16 Min_Max remains native/version-sensitive
(4.x rejects; 5.0 CPU succeeds); no new empty OpenCL guarantee is introduced.
Temporary external/selected Mat views may be sources but are never mutable
normalization destinations, even when currently compatible. Pre-native null,
raw-kind, and temporary-destination rejection preserves the destination;
arbitrary failure atomicity after native execution begins is not promised.
UMat normalization introduces no binding-side host mapping/transfers. Exact-tag
source ranges and probes are recorded in
`tests/probes/normalize_destination_source_findings.md`.

Sqrt/Exp/Log require Float32 or
Float64, process channels independently, and accept N-D. Their approximation
and special-value contracts match the Mat operations. Pow rejects Float16;
floating depths accept integer and non-integer powers, while integer depths
accept only nonnegative integer powers. UInt8/Int8/UInt16/Int16 saturate;
Int32 overflow remains native and non-saturating.

All four operations also accept reusable `Mat` and `UMat` destinations:

```ada
Sqrt
  (Self        => Input,
   Destination => Existing);

Pow
  (Self        => Input,
   Power       => 2.0,
   Destination => Existing);
```

The procedure passes Existing directly as the native output: compatible whole
or Region storage is reused, including shallow Alias attachment. A shape,
depth, or channel mismatch detaches Existing; old Parents and Aliases retain
their storage. No temporary-result assignment or copy-back is used. N-D
sources and outputs are supported; use Dimension_Count and Shape rather than
Rows/Columns for their metadata.

Exact and distinct same-layout shallow source aliases retain native operation
ordering. Arbitrary partially overlapping Regions are unsupported; no overlap
copies are added. Temporary external/selected Mat sources are permitted, but
temporary Mat destinations are prohibited even when compatible. Validation
failures before native execution leave Destination unchanged; arbitrary
post-native failure atomicity is not promised.

Sqrt follows native Pow(0.5); Exp/Log and general fractional Pow retain native
approximations, HAL/backend precision and special-value limitations. There is
no portable NaN payload, signed-zero, overflow or subnormal bit contract.
Float16 remains unsupported. Integer powers retain native saturation except
for Int32 overflow, which is not promised to saturate.

Typed-empty Float32/Float64 sources are accepted by the float operations;
default-empty and integer-depth sources are rejected by their existing policy.
Pow accepts default-empty for nonnegative integer powers and typed empties
under its existing depth/power policy. Empty Pow avoids unsafe zero-element
native HAL paths. Releasing a reused destination can retain old metadata
differently from a fresh empty result; native version-specific representation
is not normalized across Mat/UMat or OpenCV versions.

UMat procedures pass cv::UMat directly; no binding-level mapping, transfers or
host staging occur. Native OpenCV may fall back to CPU, especially for N-D.
Requesting OpenCL does not establish GPU execution. Audit evidence is in
`tests/probes/unary_math_destination_source_findings.md`.

Magnitude, Phase, and Cart_To_Polar require matching 2-D Float32/Float64
operands, including channels. Angles use radians by default or `Degrees`.
`UMat_Polar_Coordinates` owns Magnitude/Angle UMat results, and
`UMat_Cartesian_Coordinates` owns X/Y UMat results; both fields are produced
failure-atomically by one native call and have independent storage. Empty
Magnitude (default or typed), or angle-only Polar_To_Cart, means unit magnitude.
Non-empty Magnitude must match Angle's 2-D layout. Typed-empty unary/vector
results retain type and shape; Normalize preserves the empty compatibility
behavior described above.
Empty-storage safety bypasses avoid native OpenCL vector-width crashes.
OpenCL is optional and the public math family is tested with it disabled;
there is no GPU-execution guarantee.

Compatibility handling includes OpenCV 4.10 UMat empty-storage safety and
legacy pre-4.10 Float64 empty-magnitude `polarToCart` behavior. OpenCL is
optional; CPU fallback is tested. Mixed Mat/UMat operands, UMat reshape,
DFT/DCT UMat overloads, callback-scoped CPU mapping, and downstream Imgproc
UMat overloads remain unsupported.
