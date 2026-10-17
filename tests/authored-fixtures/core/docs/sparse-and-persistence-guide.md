# Sparse matrices and persistence

[README](../README.md) · [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) · [Building and Contributing](documentation.md)

This guide is published as HTML on the documentation site and maintained as
Markdown in the source repository. The public Ada specifications are authoritative for exact profiles
and per-overload restrictions. Examples below include both complete programs
and fragments intended for the surrounding application.

## Contents

- [Sparse matrices](#sparse-matrices)
- [Persistence](#persistence)
- [Formats and backends](#formats-and-backends)
- [Nested mappings and sequences](#nested-mappings-and-sequences)
- [Type policy and edge conditions](#type-policy-and-edge-conditions)
- Related: [dense typed access](typed-access-guide.md) and [ownership](ownership-and-views.md)

## Sparse matrices

`OpenCV.Core.Sparse.Sparse_Mat` is a controlled, pointer-free wrapper around
`cv::SparseMat`. A default instance is unallocated (dimension count and stored
node count zero, null `Shape`). `Clear` is a no-op on it; operations needing a
shape or type raise `OpenCV_Error`. `Create` takes 2..32 strictly positive
extents (any Ada array lower bound); `Clear` removes nodes but retains shape
and type. Ordinary assignment makes a separate native header sharing the
reference-counted node storage; `Clone` makes independent node storage.

`Contains` checks node existence and `Erase` removes a node. The
`Stored_Element_Count` is OpenCV's `nzcount()`: the number of stored hash-table
nodes, **not** the count of mathematically nonzero values. Setting a zero with
any typed `Set` creates a node; `Contains` then returns True and the count
increases. Missing typed `Get` returns zero. All access uses full N-D index
arrays and validates each extent. Direct typed node access covers all eight
depths in C1, C2, C3, and C4 (32 layouts) through `Sparse.UInt8_Access` /
`UInt8_Vec2_Access` / `UInt8_Vec3_Access` / `UInt8_Vec4_Access` and the matching
`Int8`, `UInt16`, `Int16`, `Int32`, `Float16`, `Float32`, and `Float64`
packages. One `Vec2`, `Vec3`, or `Vec4` is one complete SparseMat element;
components are channels `0 .. N-1` with no RGB, XY, or complex meaning.
Float16 components use exact `Float16_Bits`/`Float16_From_Bits` binary16
encodings, including signed zero and NaN payload bits.

Each of these 32 typed access packages also provides callback-scoped,
read-only `For_Each_Stored`:

```ada
OpenCV.Core.Sparse.UInt8_Access.For_Each_Stored (Image, Visit'Access);
--  Visit (Indices : Index_Array; Value : UInt8_Value)
```

It calls `Visit` once per **stored hash node**, including explicitly stored
numeric zero; missing positions (whose `Get` would return zero) are not
visited. An allocated sparse matrix with no nodes calls it zero times;
unallocated or wrong-depth/wrong-channel matrices raise `OpenCV_Error`
before the
callback. Each copied index vector has Ada bounds `1 .. Dimension_Count`,
with zero-based coordinate values. Values are copied, not borrowed; Float16
preserves exact binary16 encodings, including signed zero and NaN payloads.
Native hash-table traversal determines the **unspecified order**: never rely
on callback order. No native iterator, node, or pointer escapes the callback.
Do not structurally mutate the source or any shallow alias (for example with
`Set`, `Erase`, or `Clear`) while traversal is active: such changes can
invalidate native traversal. Iterator ownership preserves storage lifetime,
but provides no thread synchronization. Callback exceptions propagate
unchanged after iterator cleanup.

`From_Dense` copies complete elements of an owned nonempty dense Mat,
including non-contiguous Regions and multi-channel Mats; it does not share
dense pixels. Native construction omits elements only when **every byte of the
entire element is zero**. In particular, negative IEEE zero may be stored,
NaNs are stored, and any nonzero byte in a C3 element stores the whole C3
element. `To_Dense` independently copies stored nodes and fills missing
positions with zero, preserving shape, depth, and channels. Sparse matrices
support 32 dimensions, but on OpenCV 5 `To_Dense` rejects more than the linked
native dense Mat capacity (`MatShape::MAX_DIMS`, 10 in supported 5.0); on
OpenCV 4.x the dense capacity remains 32. No public node pointers or
iterators are exposed.

`Convert_To` is native `SparseMat::convertTo` into an independent sparse
matrix. Shape and channel count stay the same; only the depth changes. OpenCV
walks stored nodes, so a missing coordinate stays missing and an explicitly
stored zero stays a stored node. Each component becomes
`saturate_cast (source * Scale)`. There is no offset. A scale that maps a
stored value to zero still leaves that node stored. `Scale => 1.0` uses
OpenCV's unscaled conversion.

```ada
Scaled := Source.Convert_To (OpenCV.Core.Float32, Scale => 2.0);
```

The numeric `To_Dense` overload is the native sparse-to-dense conversion, not
plain `To_Dense` followed by dense `Convert_To`:

```ada
Dense :=
  Source.To_Dense (OpenCV.Core.Float32, Scale => 2.0, Offset => 5.0);
```

A stored component becomes `saturate_cast (source * Scale + Offset)`. A
missing element is initialized with OpenCV `Scalar(Offset)`: channel 0
receives `Offset` and channels 1..3 receive 0, because `cv::Scalar` has one
value and three zeros. Both results own independent storage and leave the
source unchanged. The same OpenCV 5 dense-dimension capacity rule as plain
`To_Dense` applies; sparse-to-sparse conversion still accepts the full 32
dimensions.

Float16 is not a supported numeric source or destination. OpenCV 4.1.0,
4.10.0, and 5.0.0 leave every `CV_16F` entry null in the sparse
`getConvertElem` / `getConvertScaleElem` tables, and this binding does not
invent a Float32 fallback. `Convert_To` and numeric `To_Dense` raise
`OpenCV_Error` before the ABI call. Exact-bit Float16 `Get`/`Set` and plain
`To_Dense` are unchanged. The other seven depths convert in every
source/destination direction, using OpenCV saturation.

`Norm` and `Normalize` use the existing `Norm_Kind` (`L1`, `L2`, `Infinity`)
and require an allocated Float32 or Float64 matrix with exactly one channel.
Integer depths, Float16, and every multi-channel layout are rejected before
the ABI call. `Min_Max` normalization is deliberately unavailable: shifting
the implicit sparse zero would materialize nodes and change sparse semantics.

```ada
Magnitude := Values.Norm (OpenCV.Core.L2);
Unit      := Values.Normalize (Target_Norm => 1.0, Kind => OpenCV.Core.L2);
```

Both operations consider stored nodes only. A missing coordinate contributes
zero and is not created. An explicitly stored zero contributes zero to the
norm and remains a stored node. `Norm` does not modify the matrix and returns
`0.0` when an allocated matrix has no stored nodes. `L1` is the sum of
absolute stored values, `L2` is the square root of the sum of their squares,
and `Infinity` is the maximum absolute stored value.

`Normalize` returns an independent matrix with the same shape, depth, channel
count, and stored-node coordinates. OpenCV scales every stored value by
`Target_Norm / Norm` when that norm exceeds `DBL_EPSILON`. Otherwise the scale
is `0.0`: stored values become zero, stored nodes remain stored, and an empty
allocated matrix stays empty. A negative `Target_Norm` is supported and
reverses the sign of every stored value. The source is unchanged. Because no
dense `Mat` is constructed, both 5-D and 32-D sparse matrices are accepted.

`Min_Max_Loc` uses the same allocated Float32 or Float64 single-channel
restriction. It returns a `Sparse_Extrema` value whose `Has_Minimum` and
`Has_Maximum` flags are independent:

```ada
Extrema := Values.Min_Max_Loc;
--  Extrema.Has_Minimum, Has_Maximum, Minimum, Maximum
--  Minimum_Location (1 .. Extrema.Dimensions)
--  Maximum_Location (1 .. Extrema.Dimensions)
```

Only stored nodes participate. A missing coordinate is not a candidate and is
not created. An explicitly stored zero is a candidate, and negative zero
compares equal to positive zero. Comparisons are strict, so equal extrema keep
the earliest node in OpenCV's hash traversal. That traversal order is
unspecified and is not insertion order. NaN never replaces a finite extremum.

Each flag is True only when native OpenCV wrote that location. Empty storage
and a NaN-only matrix establish neither side. Positive infinity, and a stored
Float32 `FLT_MAX` or Float64 `DBL_MAX`, establish only the maximum. Negative
infinity, and a stored `-FLT_MAX` or `-DBL_MAX`, establish only the minimum.
A side that was not established returns `0.0` and an all-zero location. The
native initialization sentinels are not exposed as public extrema.

On an established side, each location is a fixed 32-coordinate array; only
`1 .. Dimensions` is meaningful, and those coordinates are zero-based. The
source is not modified. Because no dense `Mat` is constructed, both 5-D and
32-D sparse matrices are accepted.

## Persistence

Persistence is provided by:

```ada
OpenCV.Core.Persistence
```

through a limited controlled `File_Storage` abstraction over `cv::FileStorage`.

### Formats and backends

Supported formats:

```text
XML
YAML
JSON
```

Disk `Open` selects the format from the filename extension:

```text
.xml
.yml
.yaml
.json
```

Memory writers select the format explicitly with `Create_Memory`; memory
readers use `Open_Memory`, letting OpenCV detect the serialized format.

### Supported values

Named and sequence values currently include:

- `Mat`
- `Integer`
- `Long_Float`
- `String`

### Nested mappings and sequences

The current persistence API supports hierarchy without exposing `FileNode`.

Writing:

- named and unnamed `Begin_Map`
- named and unnamed `Begin_Sequence`
- `End_Structure`
- named `Write`
- sequence `Append`

Reading:

- named/indexed `Enter_Map`
- named/indexed `Enter_Sequence`
- `Leave_Structure`
- `Sequence_Length`
- `Map_Length` and zero-based `Map_Key` (root or entered map)
- named/indexed `Kind` for structural node categories
- named/indexed `Read_Mat`
- named/indexed `Read_Integer`
- named/indexed `Read_Real`
- named/indexed `Read_String`

Example:

```ada
with OpenCV.Core.Persistence;

declare
   package P renames OpenCV.Core.Persistence;
   Storage : P.File_Storage := P.Create_Memory (P.JSON);
begin
   Storage.Begin_Map ("Camera");
   Storage.Write ("Name", "Front Camera");

   Storage.Begin_Sequence ("Distortion");
   Storage.Append (0.1);
   Storage.Append (-0.05);
   Storage.Append (0.001);
   Storage.End_Structure;

   Storage.End_Structure;

   declare
      Text : constant String := Storage.Close_And_Get_Text;
   begin
      null;
   end;
end;
```

The implicit FileStorage root is a mapping. Hierarchy is navigated by the
controlled `File_Storage` object itself; no public `FileNode` lifetime is
exposed.

For an open read-only storage, keys at the root or entered mapping are returned
as independent Ada strings in OpenCV's mapping iteration order, not sorted.
When the current node is a mapping with no entries, `Map_Length` returns zero;
map enumeration in a sequence context is invalid. For example:

```ada
Count := Reader.Map_Length;
if Count > 0 then
   for I in 0 .. Count - 1 loop
      Put_Line (Reader.Map_Key (I));
   end loop;
end if;
```

`Node_Kind` describes the **OpenCV FileNode structure**, not the type of an
arbitrary serialized OpenCV object. A persisted 2-D or N-D `Mat` is a mapping
(`opencv-matrix` or `opencv-nd-matrix`), so `Kind ("Matrix")` returns
`Mapping_Node`, not a separate Mat kind. Use `Read_Mat` when Mat conversion is
intended. Named `Kind` works at the root or in an entered map; indexed `Kind`
works in an entered sequence. Both leave navigation unchanged. For example:

```ada
declare
   Count : constant Natural := Reader.Map_Length;
begin
   if Count > 0 then
      for I in 0 .. Count - 1 loop
         declare
            Key : constant String := Reader.Map_Key (I);
         begin
            case Reader.Kind (Key) is
               when P.Integer_Node  => Put_Line (Key & ": integer");
               when P.Real_Node     => Put_Line (Key & ": real");
               when P.String_Node   => Put_Line (Key & ": string");
               when P.Sequence_Node => Put_Line (Key & ": sequence");
               when P.Mapping_Node  => Put_Line (Key & ": mapping");
            end case;
         end;
      end loop;
   end if;
end;
```

### Type policy and edge conditions

The API avoids surprising lossy conversions:

```text
integer node -> Read_Integer    allowed
real node    -> Read_Integer    rejected

real node    -> Read_Real       allowed
integer node -> Read_Real       allowed by widening

string node  -> Read_String     allowed
other node   -> Read_String     rejected
```

Missing nodes raise `OpenCV_Error`; stored zero, empty string, empty Mat, and
empty sequence remain distinguishable from absence. Empty mapping preservation
depends on OpenCV and the persistence format; when OpenCV parses a node as a
mapping with no entries, `Map_Length` reports zero.

Integer writes use OpenCV's signed 32-bit file node. The binding currently
supports the write range:

```text
-2_147_483_647 .. 2_147_483_647
```

The signed 32-bit minimum is rejected rather than entering an unsafe native
integer-formatting path present in affected supported releases.

Embedded NUL is rejected in filenames, node names, String values, and memory
input because those paths cross NUL-terminated native interfaces.
