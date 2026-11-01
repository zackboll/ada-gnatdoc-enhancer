# Core operations guide

## Native runtime identity

`OpenCV.Core.Native_Version_String` and
`OpenCV.Core.Native_Build_Information` return independently owned Ada Strings
queried from the linked native OpenCV implementation, not the Ada crate version
or consumer header macros. Build information preserves multiline, build-specific
text without parsing. See the [runtime identity contract and example](native-runtime-identity.md)
for ownership, errors, capacity limits, and pinned four-version source findings.

## Mat/scalar modes (CORE-FIN-01)

`Add`, `Subtract`, `Multiply` and `Divide` accept `(Self : Mat; Value : Scalar)`
with owned-result and actual caller-owned destination forms. `Subtract_From
(Value, Self)` means **Value - Self**; `Divide_Into (Value, Self)` means
**Value / Self**. `Compare (Self, Value : Float64_Value, Kind)` supports all six
relations, returning/writing UInt8 C1 zero/255 without first narrowing Value.

The bounded input is nonempty exactly 2-D, UInt8/Int8/UInt16/Int16/Int32/
Float32/Float64; arithmetic C1..C4, Compare C1. Float16, C5+, comparison C2+,
N-D and default/typed-empty sources raise OpenCV_Error before mutation.
`Scalar.Component_0` applies to channel 0, etc. `Make_Scalar (5.0)` leaves the
other components zero: coefficients are **not repeated**. Uniform C4 requires
all four components explicitly.

Native conversion/rounding and saturation apply. Int32 overflow is not portable
mathematical arithmetic. Add/subtract/reverse-subtract coefficients must be
finite and have absolute value at most INT32_MAX; integer multiply/divide uses
the same coefficient bound. Floating multiply/divide permit NaN/Inf; source
floating pixels retain native special-value behavior. Compare coefficients must
be finite, but fractional and out-of-integer-range values are passed as double
and handled natively. No cross-version/SIMD bit, NaN payload or signed-zero
guarantee is made.

For **all five integer result depths**, `Divide` rejects any active zero scalar
denominator, and `Divide_Into` rejects any zero Mat denominator component.
Both function and destination forms raise `OpenCV_Error` before native execution
and leave source/destination storage and sharing unchanged. Every logical row
and channel is inspected, including non-contiguous Regions; padding is not part
of the denominator. Nonzero denominators remain valid. Floating zero division
retains native behavior. No signed-minimum-to-zero mapping is performed.
This conservative policy avoids nonportable native Inf/NaN-to-integer paths;
the raw ABI has the corresponding conversion-safety checks. See the
[source findings](../tests/probes/scalar_modes_source_findings.md).

Functions return independent storage. Procedures pass the actual native output:
compatible whole/Region storage and shallow aliases are retained; mismatch
detaches and keeps old parents/aliases alive. Exact/same-layout arithmetic
source aliases are supported. Compare overlap requires identical-layout UInt8
C1; depth-changing exact aliases and any other possible overlap are rejected.
The conservative byte-span check may reject apparently disjoint Regions in a
shared allocation. No general partial-overlap support or hidden copy is added.
Scoped external/selected inputs are allowed; temporary destinations are rejected.
Pre-native rejection preserves values; arbitrary native failure has no rollback
guarantee. No UMat, masks, N-D, mixed-depth or selectable-dtype modes are added.

Compile-tested example in `tests/probes/scalar_modes_example.adb`
and `tests/probes/scalar_modes_example.gpr`:

```ada
Image.Set_To (Make_Scalar (8.0));
Add (Image, Make_Scalar (2.0), Shifted);
Compare (Shifted, 9.5, Greater_Than, Mask);
```

The native implementation and probe identities for 4.1.0/4.6.0/4.10.0/5.0.0
are recorded in the focused source findings, not the unmerged audit snapshots.

[README](../README.md) · [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) · [Building and Contributing](documentation.md)

This guide is published as HTML on the documentation site and maintained as
Markdown in the source repository. The public Ada specifications are authoritative for exact profiles
and per-overload restrictions. Examples below include both complete programs
and fragments intended for the surrounding application.

## Contents

- [Reusable paired polar destinations](#reusable-paired-polar-destinations)
- [Public API overview](#public-api-overview)
- [Conversion and element-wise mathematics](#conversion-and-element-wise-mathematics)
- [Arithmetic](#arithmetic), [masks](#masks-and-selection) and [bitwise operations](#bitwise-operations)
- [Linear algebra and decomposition](#linear-algebra-and-decomposition)
- [Spectral transforms](#spectral-transforms)
- [Random numbers, clustering, and nearest neighbors](#random-numbers-clustering-and-nearest-neighbors)
- Related: [ownership and overlap context](ownership-and-views.md)

## Reusable paired polar destinations

The allocation-returning polar functions remain available. Six procedure
overloads write two actual caller-owned destinations, for both `Mat` and
`UMat`, including angle-only `Polar_To_Cart`:

```ada
Cart_To_Polar
  (X         => Horizontal,
   Y         => Vertical,
   Magnitude => Existing_Magnitude,
   Angle     => Existing_Angle,
   Units     => Radians);

Polar_To_Cart
  (Magnitude => Existing_Magnitude,
   Angle     => Existing_Angle,
   X         => Horizontal,
   Y         => Vertical,
   Units     => Radians);

Polar_To_Cart (Existing_Angle, Horizontal, Vertical, Degrees);
```

Each transform uses the existing single native transform helper, not separate
Magnitude/Phase or trigonometric operations. Compatible whole outputs and
Regions keep their storage and shallow aliases. Each output with mismatched
shape, depth, or channels detaches independently; old Parents and retained
aliases remain alive. Cart_To_Polar follows X's layout; Polar_To_Cart follows
Angle's. Destination layout need not be prevalidated or preallocated.

Both outputs must be distinct native objects, and neither may be exactly
either source. These portable identity restrictions are checked before native
execution on every supported version. Input/input identity remains permitted.
Distinct headers sharing overlapping storage and arbitrary partial Region
overlap are unsupported. Disjoint output Regions of one Parent are supported:
distinct headers retain their offsets and row steps, and writes to either
output do not affect the other or the intervening guards. This does not permit
source/output storage overlap or partially overlapping output Regions.
Temporary external or selected Mat views are permitted as sources under the
existing validators, but prohibited in either output position. Preflight
rejection preserves both outputs; native exceptions do not promise two-output
rollback. No hidden source/output copies support forbidden aliases.

Empty Magnitude (default or typed) means unit magnitude. The angle-only
procedure forwards a default-empty Magnitude to the two-input procedure.
The existing pre-4.10 Float64 correction still performs native Float32
coordinates followed by numeric Float64 conversion into the destinations.
Cart_To_Polar retains matching Float32/Float64 2-D inputs. Polar_To_Cart
retains its existing N-D Angle support with empty Magnitude and its matching
2-D policy for nonempty Magnitude. Default-empty Angle is rejected;
typed-empty Angle remains accepted. Empty outputs follow the shared helpers'
native metadata behavior, with direct UMat observation rather than transfers.

Radians remain default; Degrees is explicit. Fast angles retain approximately
0.3-degree accuracy and do not imply a strict half-open turn interval.
Coordinates retain native approximations, not libc bit-pattern guarantees.
UMat production inputs and outputs remain UMat, without new host staging;
OpenCL availability and actual kernel execution depend on the native runtime.

## Public API overview

The following is a practical overview of the current public surface. Exact
shape, depth, channel, continuity, and numerical restrictions are documented on
the Ada declarations and covered by tests.

### Core types

Major public abstractions include:

- `OpenCV.Core.Mat`, `Mat_Type`, `Depth_Type`, `Channel_Count`, `Mat_Size`
- `OpenCV.Size`, `OpenCV.Point`, `OpenCV.Point_Array`, `OpenCV.Rect`, `OpenCV.Scalar`
- `OpenCV.Point_3D`, `OpenCV.Point_3D_Array`, `OpenCV.Float32_Point_3D`,
  `OpenCV.Float32_Point_3D_Array`
- `Index_Range`, `Index_Range_Array`
- `Float16_Value`
- `Mat_Array`
- `Random_Number_Generator`
- `Min_Max_Result`, `Mean_Std_Dev_Result`, `Range_Check_Result`
- `Inversion_Result`, `Solve_Result`, `Linear_Program_Result`
- `Polar_Coordinates`, `Cartesian_Coordinates`
- `Covariance_Result`, `Eigen_Decomposition_Result`
- `Principal_Component_Analysis_Result`
- `Linear_Discriminant_Analysis_Result`
- `Singular_Value_Decomposition_Result`
- `K_Means_Result`, `Nearest_Neighbor_Result`
- cubic and polynomial solution result types
- channel routing records and arrays.

The public depth enumeration contains:

```text
UInt8
Int8
UInt16
Int16
Int32
Float32
Float64
Float16
```

`Float16_Value` is a private 16-bit type for the exact IEEE-754 binary16
encoding used by OpenCV `CV_16F`. `Float16_From_Bits` / `Float16_Bits` preserve
every pattern, including signed zeros, subnormals, infinities, and NaN
payloads. Classification helpers inspect those stored bits. `To_Float16` /
`To_Float32` convert numerically between binary16 and binary32 using
round-to-nearest, ties-to-even. `OpenCV.Core.Float16_Access` provides scalar
C1 2-D and N-D Get/Set that store and load the exact encoding. Copied row
access, borrowed row access, whole-buffer borrowing, and packed or row-strided
external Mat views are available for Float16 C1, C2, C3, and C4. `Add`, `Subtract`,
`Multiply`, `Divide`, `Abs_Diff`, `Minimum`, `Maximum`, `Add_Weighted`, and
`Scale_Add` accept Float16 Mats
and return Float16; they use native OpenCV FP16 arithmetic where the supported
OpenCV version implements a conforming operation and an internal Float32
compatibility path otherwise. Storage
and access bit preservation is distinct from arithmetic numeric semantics.
This does not imply broad Float16 coverage of every Core algorithm.

### Creation, shape, metadata, and views

Creation and structure:

- `Create`
- `Clone`
- `Copy_To`
- masked `Copy_To`
- `Region`
- `Row_View`
- `Column_View`
- range views
- `Slice`
- `With_Selected_View` (callback-scoped dimension-dropping N-D selection)
- `Reshape`, including the existing 2-D overloads and Shape-based N-D overloads
- `Diagonal_View`
- `Diagonal_Matrix`

Metadata:

- `Is_Empty`
- `Rows`
- `Columns`
- `Dimensions`
- `Dimension_Count`
- `Extent`
- `Shape`
- `Channels`
- `Depth`
- `Total`
- `Element_Size`
- `Channel_Size`
- `Is_Continuous`
- `Is_Submatrix`

`Index_Range` is half-open:

```text
Start <= index < Stop
```

Continuous genuine N-D Mats, including continuous N-D `Slice` views, can also
be borrowed as one flat typed array through every `*_Buffer_Access` package;
the final dimension varies fastest. A gapped Slice (for example one that
restricts a middle axis while keeping several outer blocks) is rejected
before the callback runs.

`Dimensions` is the 2-D `Size` view: width is `Columns` and height is `Rows`.
`Shape` is the all-dimensional counterpart. It returns every extent in Mat
dimension order, indexed `1 .. Dimension_Count`. A default Mat returns a null
array. A typed empty `0 x 0` Mat returns two zero extents. A normal 2-D Mat
returns `(Rows, Columns)`. A genuine N-D Mat reports `Extent` for every axis
rather than `Rows` or `Columns`.

Shape-based reshape creates another header over the same storage:

```ada
Volume := Image.Reshape (Shape => (2, 3, 4));
Pixels := Scalars.Reshape (Channels => 3, Shape => (2, 2, 3));
```

The `Dimension_Array` is read in Ada iteration order, regardless of its lower
bound. Every target extent must be nonzero: this API does not expose OpenCV's
zero-sentinel "preserve this dimension" convention. The target dimension count
must be `2 .. 32` (on OpenCV 5.0, at most its native 10-dimension capacity;
longer targets raise `OpenCV_Error` before native reshape). The scalar count,
including channels, must stay identical,
and depth is unchanged. Shape-based reshape requires continuous storage. The
result shares storage; `Clone` creates independent storage. The existing
`Reshape (Channels)` and `Reshape (Channels, Rows)` overloads are unchanged.

### Conversion and element-wise mathematics

Mat and UMat provide both return-value and destination-taking conversions:

```ada
Result := Source.Convert_To
  (Depth => OpenCV.Core.UInt8, Scale => 2.0, Offset => 3.0);
Source.Convert_To
  (Destination => Existing, Depth => OpenCV.Core.UInt8,
   Scale => 2.0, Offset => 3.0);
```

The function returns independent storage. The procedure converts directly into
`Existing`'s native header: compatible shape/type permits allocation reuse;
incompatible shape/type triggers native reallocation. Nonempty results keep the
source shape and channel count, selecting only the destination depth, and use
OpenCV's `saturate_cast<Depth>(Source * Scale + Offset)` semantics. Genuine N-D
arrays are supported, and Float16 follows the existing native conversion policy.

A compatible destination `Region` remains attached to its original parent:
conversion modifies only the selected pixels, visible through the parent and
other shallow aliases, leaving surrounding guard pixels untouched. This is
verified by parent/alias pixel tests, not inferred from `Is_Submatrix`. If native
reallocation is required, an incompatible Region can detach; its old parent and
other headers keep their original allocation and pixels. Exact self-conversion,
including a depth change, is supported. Same-layout shallow aliases follow
native sharing; arbitrary partially overlapping views are not supported.

Temporary callback-scoped external/selected Mat views are permitted as sources,
but rejected as destinations with `OpenCV_Error`, independently enforced by the
raw ABI. Null handles, invalid raw depth identifiers, and temporary destinations
are rejected before native mutation and leave existing destination data/header
unchanged. No failure-atomicity guarantee is made for exceptions after native
conversion begins. UMat conversion uses native UMat destinations without any
binding-side host mapping or staging; OpenCV may itself choose CPU fallback.

Empty sources produce empty destinations, but metadata deliberately follows
the installed OpenCV: 4.1/4.6/4.10 release storage while retaining destination
type metadata; 5.0 recreates empty metadata. In 5.0 Mat retains source channels,
whereas the native empty UMat depth-only path creates one channel. See
[`tests/probes/convert_destination_source_findings.md`](../tests/probes/convert_destination_source_findings.md)
for exact-tag source references and the isolated probe results.

Conversion/mapping:

- `Convert_To`
- `Convert_Scale_Abs`
- `Apply_LUT`
- `Normalize`

Element-wise mathematics and coordinate conversion:

- `Sqrt`
- `Exp`
- `Log`
- `Pow`
- `Magnitude`
- `Phase`
- `Cart_To_Polar`
- `Polar_To_Cart`

### Reusable Magnitude and Phase destinations

Both Mat and UMat retain their allocation-returning functions and also accept
an actual caller-owned output:

```ada
Magnitude
  (X           => Horizontal,
   Y           => Vertical,
   Destination => Existing);

Phase
  (X           => Horizontal,
   Y           => Vertical,
   Destination => Existing,
   Units       => Degrees);
```

Compatible whole and Region destinations retain their storage and geometry;
shallow aliases observe the writes. A mismatched shape, depth, or channel count
detaches the destination through native output creation, leaving old Parent
storage and retained aliases intact. No temporary result/copy-back is used.

Sources must have matching 2-D layout, Float32 or Float64 depth, and channel
count. Channels are computed independently. Genuine N-D and default-empty
sources are rejected before destination mutation. Matching typed-empty sources
retain existing native Mat empty behavior and the source-typed UMat empty
compatibility helper; empty metadata is not a universal cross-version release
contract. Query UMat metadata directly rather than through an empty transfer.

Magnitude preserves native `sqrt(X*X + Y*Y)` precision/overflow behavior.
Phase computes native `atan2(Y, X)` angles with approximately 0.3-degree
accuracy; omitted units mean Radians. Degrees may be selected explicitly.
Use angular wraparound distance near the full-turn boundary rather than a
strict half-open interval or exact mathematical bit comparisons. Special
floating values retain native backend behavior, without normalization.

Exact X/Y destination aliases and distinct shallow source aliases are
supported, including X=Y. Arbitrarily partially overlapping Regions are not
supported. Temporary external/selected Mat sources are legal, but temporary
Mat destinations are prohibited because native output creation can release or
rebind callback-scoped storage. UMat stays native at the binding boundary;
OpenCV may choose CPU fallback without binding-level host staging.

### Arithmetic

Explicit Mat/Mat operations include:

- `Add`
- `Subtract`
- `Multiply` — element-wise
- `Divide` — element-wise
- `Abs_Diff`
- `Minimum`
- `Maximum`
- `Add_Weighted`
- `Scale_Add`

`Mat` and `UMat` support both allocation-returning and destination-taking
`Add` / `Subtract` / `Multiply` / `Divide` / `Abs_Diff` / `Minimum` / `Maximum`
forms. All require matching **2-D**
operands (shape, depth, and channels); Destination does not participate in
validation.

```ada
Result := Add (A, B);
Result := Subtract (A, B);
Result := Multiply (A, B);
Result := Divide (A, B);
Result := Abs_Diff (A, B);
Low  := Minimum (A, B);
High := Maximum (A, B);

Add
  (Left        => A,
   Right       => B,
   Destination => Existing);
Subtract
  (Left        => A,
   Right       => B,
   Destination => Existing);
Multiply
  (Left        => A,
   Right       => B,
   Destination => Existing);
Divide
  (Left        => A,
   Right       => B,
   Destination => Existing);
Abs_Diff
  (Left        => A,
   Right       => B,
   Destination => Existing);
```

Functions retain their independent-result contract. Procedures pass the
caller's actual native destination header to arithmetic, reusing compatible
whole storage or an interior `Region`: its parent/geometry and preexisting
shallow aliases remain attached, and outside parent pixels remain unchanged.
An incompatible shape, depth, or channel count permits native reallocation;
a Region may detach while its old aliases/parent retain their storage.

Destination may be Left or Right, or a distinct same-layout shallow alias of
either, including order-sensitive `Subtract (A, B, B)` computing `A - old(B)`.
Operands may themselves share the same layout/storage: `A + A`, `A - A`, and
`A * A` retain native numeric semantics. Arbitrarily partially overlapping Regions
are **not supported**. Temporary external/selected Mat views are allowed as
sources, but never as destinations, even with compatible shape/type.
Operand/capability validation occurs before mutation; arbitrary post-native
failure atomicity is not promised. Integer saturation remains native (UInt8
and Int16 saturate; Int32 does not saturate and overflow may change sign).

Float16 follows the existing function policy: Float32 widening on OpenCV 4.x,
native half arithmetic on 5.x. The 4.x final narrowing writes into the actual
destination and can reuse compatible half whole/Region storage. No extra half
compatibility layer or cross-architecture bitwise guarantee is introduced.
UMat arithmetic remains UMat-native at the binding boundary; OpenCV chooses
OpenCL execution or CPU fallback, not necessarily GPU residency/execution.

Reusable elementwise extrema are available for both Mat and UMat:

```ada
Minimum
  (Left        => A,
   Right       => B,
   Destination => Existing_Low);

Maximum
  (Left        => A,
   Right       => B,
   Destination => Existing_High);
```

These pass the actual native Destination to the unchanged `dense_min_max`
helper. Compatible whole/Region storage is reused, preserving shallow aliases
and parent geometry; shape/depth/channel mismatches can reallocate/detach the
destination without changing the old parent or its aliases. Destination may be
Left or Right or an exact same-layout shallow alias of either; operands may
alias each other. Arbitrary partially overlapping Regions are unsupported.
The public contract remains matching **2-D** operands, with Destination excluded
from operand validation. Temporary external/selected Mat views remain valid
sources but cannot be destinations. Pre-native rejection preserves Destination;
arbitrary post-native failure atomicity is not promised.

Integer extrema are direct, channel-independent element selection, without
arithmetic overflow or saturation (including Int16 and Int32 extrema). Ordinary
finite values retain numerical correctness in place. Floating NaN and
signed-zero selection follows native OpenCV, **not IEEE `fmin`/`fmax`**: neither
unconditional NaN propagation nor bitwise commutativity/payload identity is
promised. Independent destinations match the allocation-returning functions.
Exact/shallow aliases instead retain native aliased-output behavior. In OpenCV
5.0, fresh outputs can use a final SIMD block where exact aliases use a scalar
tail; this can change NaN classification or zero sign at affected tail positions.
This is native behavior, not a binding-created discrepancy or a memory-safety
defect. The tested 4.1/4.6/4.10 CPU builds retained fresh/alias parity in these
cases; that observation is not imposed on other versions/backends/architectures.

Float16 policy is unchanged: 4.x widens both operands to Float32 Dense and
narrows into the actual half Destination (reusing compatible whole/Region
storage); 5.0 uses native half min/max, including its native alias/tail boundary.
No normalization, copy-back or defensive preallocation is added. UMat remains
native at the binding boundary, including Dense half intermediates; OpenCV may
fall back internally to CPU, and GPU execution is not guaranteed. Empty output
metadata remains native/version-specific. The existing helper avoids the known
default-empty Mat and typed-empty UMat/OpenCL hazards. See
[`tests/probes/min_max_destination_source_findings.md`](../tests/probes/min_max_destination_source_findings.md)
for the exact four-version source audit and actual-helper evidence.

`Abs_Diff` passes the actual destination to the unchanged `dense_abs_diff`
helper. Compatible whole/Region storage is reused; mismatched shape, depth or
channels may detach/reallocate without changing the old parent or aliases.
Destination may be Left or Right, including distinct same-layout shallow
aliases; arbitrary partially overlapping Regions are unsupported. Public
operands remain matching **2-D** arrays, not scalars or N-D arithmetic.
UInt8 differences do not wrap (`10` vs `200` gives `190`), channels are
independent, and Int16 saturates (`-32768` vs `0` gives `32767`). Int32 overflow
has no saturation guarantee and may yield negative native values; the binding
does not normalize it. Ordinary finite/integer `Abs_Diff (A, A)` is zero, but
equal infinities and NaNs produce native NaNs. Finite vs either infinity gives
positive infinity; NaN operands propagate NaN classification, without payload
preservation promises. Signed-zero pairs produced positive zero in the exact
four-version CPU matrix; no stronger architecture-independent bit contract is
introduced. Float16 policy is unchanged (4.x Float32 widening/final narrowing
into the actual destination; 5.0 native half), and UMat stays native at the
binding boundary. Typed/default Mat empty order differs on 4.x, whereas 5.0
Mat releases early; the established UMat typed-empty compatibility path remains
unchanged. OpenCV 5's same-width scalar helper cannot introduce an old-output
write-width mismatch here, so no preallocation correction was added. See
[`tests/probes/abs_diff_destination_source_findings.md`](../tests/probes/abs_diff_destination_source_findings.md)
for exact-tag paths, empty metadata, alias boundaries, and actual-helper probes.

`Divide` passes the actual destination to the unchanged division compatibility
helper. `Divide (A, B, A)` and `Divide (A, B, B)` are supported: the latter still
computes **old Left / old Right**, including exact-layout shallow aliases.
Partial overlap is unsupported. Scale remains 1.0 and output preserves operand
depth. Zero denominators are **not invalid**: native integer storage returns
zero; Float32/Float64 preserve infinity/NaN, including the denominator zero sign
where native execution preserves it. Integer quotients use OpenCV conversion/
rounding, not Ada integer `/` (for example UInt8 `7 / 2 = 4`). `A / A` is one
only for ordinary nonzero finite inputs: integer `0 / 0` is zero and ordinary
floating `0 / 0` is NaN. Float16 policy is unchanged and procedure results match
the existing function under the same build; no NaN payload guarantee is added.
OpenCV 5.0 typed-empty Mat division releases the destination, unlike ordinary
4.x typed-empty Mat creation; the existing UMat empty helper remains unchanged.
No Divide old-destination-depth selector or preallocation correction exists.
See [`tests/probes/divide_destination_source_findings.md`](../tests/probes/divide_destination_source_findings.md)
for the four exact-tag source audit, empty metadata, and actual-helper probe.

Accepted empty operands release destination storage or create typed-empty
headers through the established native/helper path. Old aliases keep their
allocation. Release retains the old destination depth/channels, unlike a
fresh return-value result; 4.x release retains zeroed dimensional extents,
whereas 5.0 clears dimensionality. Typed-empty UMat outputs retain operand
type/2-D shape through the existing helper; typed-empty Mat outputs differ
between 4.x and 5.0. See the exact-version table and source/probe evidence in
[`tests/probes/add_subtract_destination_source_findings.md`](../tests/probes/add_subtract_destination_source_findings.md).

`Multiply` uses the existing multiplication helper with the actual destination,
including its empty and Float16 compatibility paths. Exact `Multiply (A, B, A)`
and `Multiply (A, B, B)`, same-layout shallow aliases of either operand, and
`Multiply (A, A, A)` are supported; arbitrary partial Region overlap is not.
UInt8 products saturate (`20 * 20 = 255`), signed Int16 products saturate at both
limits, and Int32 retains OpenCV's non-saturating contract; no binding overflow
policy is added. Scale remains 1.0 and output depth remains the operand depth.
Multiply's typed-empty Mat path retains operand type/2-D shape except Float16
on 4.x (release); typed-empty UMat retains operand metadata. Default/mixed Mat
empties release output, whereas mixed UMat empties take the typed operand's
metadata. Release preserves old destination depth/channels and old aliases;
the released shape is zeroed 2-D on 4.x and dimensionless on 5.0.
Native HAL configuration can also reject typed-empty Mat multiplication:
OpenCV 5.0's KleidiCV `mul8u` does so on macOS ARM64. Both forms preserve the
translated `OpenCV_Error`; the procedure may have created typed-empty output
before that native failure. No cross-platform empty normalization is added.
The helper narrowly corrects the old UInt16/Int16 destination layout before
byte multiplication on OpenCV 4.10+/5.x, preventing an extended HAL kernel from
writing 16-bit values into recreated byte storage. Compatible destinations,
fresh results, and empty operands are unaffected. See
[`tests/probes/multiply_destination_source_findings.md`](../tests/probes/multiply_destination_source_findings.md)
for the exact four-version source audit, native-call layout probe, and empty
metadata table. No guaranteed GPU execution or cross-platform Float16 bit
identity is implied.

`Add`, `Subtract`, `Multiply`, `Divide`, `Abs_Diff`, `Minimum`, and `Maximum`
accept Float16 operands with the same shape, depth, and channel-count
compatibility rules as the other public depths. The result is always Float16;
the public result type does not change on older OpenCV releases. Finite results
for `Add`, `Subtract`, `Multiply`, `Divide`, and `Abs_Diff` are defined as

```text
To_Float16 (To_Float32 (Left) +/- To_Float32 (Right))
To_Float16 (To_Float32 (Left) * To_Float32 (Right))
To_Float16 (To_Float32 (Left) / To_Float32 (Right))
To_Float16 (abs (To_Float32 (Left) - To_Float32 (Right)))
```

with a nonzero finite denominator required for Divide. OpenCV 5.x native
`CV_16F` paths for these operations are used only while they satisfy this
established Float32-to-Float16 result model. OpenCV 4.1, 4.6, and 4.10 expose
Float16 storage and `convertTo` but do not implement these arithmetic kernels,
so the binding widens internally to Float32, performs the operation, and
narrows back to Float16. That fallback exists only for compatibility.

### Reusable weighted arithmetic destinations

### Reusable comparison and scalar-range masks

Both `Mat` and `UMat` retain their allocation-returning `Compare` and
scalar-bounded `In_Range` functions and also provide reusable destinations:

```ada
Compare
  (Left        => A,
   Right       => B,
   Kind        => Greater_Than,
   Destination => Mask);

In_Range
  (Self        => Image,
   Lower       => Make_Scalar (10.0, 20.0, 30.0),
   Upper       => Make_Scalar (50.0, 60.0, 70.0),
   Destination => Mask);
```

Successful nonempty outputs always have source shape and **UInt8 C1** type,
with bytes exactly **0 or 255**. Compatible whole outputs and interior Regions
reuse storage: retained shallow aliases and the Parent see mask writes, and
later writes remain reciprocal. Shape, depth or channel mismatches cause native
reallocation/detachment of Destination only; the old Parent and aliases retain
their old storage. The binding passes the actual native Destination, without
hidden preallocation, temporary output/copy-back or overlap copies.

Compare retains its existing **single-channel**, identical Rows/Columns/Depth
policy and all six comparison kinds. Genuine N-D operands are rejected through
the existing Rows/Columns validation before Destination mutation. Scalar-bounded
In_Range accepts at most four source channels and supports genuine **N-D**
sources, including `(2, 3, 5)` Mat/UMat. Both bounds are inclusive. An element is
selected only when **every** source channel satisfies its own scalar bounds.
Bounds undergo native source-depth conversion: for example, integer sources
with bounds 1.2 and 2.8 use rounded bounds 1 and 3, not mathematical ceiling and
floor. Floating comparisons, NaN, infinities and signed zero follow the same-build
native/function behavior; no replacement NaN policy is imposed.
For example, some native CPU builds produce different NaN `Not_Equal` bytes
in vector lanes and the scalar tail; masks still contain only exact 0/255.

For both functions and procedures, **Float16 requires OpenCV 5.0 or newer**.
On supported OpenCV 4.x, shared production helpers reject Float16 with a
controlled OpenCV/Ada error before native output creation, because the CPU
dispatch tables lack half kernels and some paths call a null function pointer.
This applies regardless of OpenCL availability and preserves Destination on
that failure. OpenCV 5 uses native half kernels. There is no Float32 compatibility
conversion or binding-level host staging.

Mat Compare supports exact Left/Right destinations and same-layout shallow
aliases. UMat Compare supports UInt8 C1 exact aliases and distinct same-layout
shallow aliases; **exact depth-changing UMat source/Destination aliases are
rejected for ABI safety** before native execution, raising `OpenCV_Error` and
preserving both sources and retained aliases. Native CPU mapping ownership
assertions and OpenCL source-acquisition order make those cases unsafe.
**Exact UMat In_Range Self/Destination aliases are rejected for ABI safety**
regardless of OpenCL state. Other shared-storage In_Range aliases, and Mat
In_Range source/Destination aliases, remain outside the supported contract;
Mat behavior is unchanged. Only native object/header address identity is checked,
not UMatData/refcounts or generalized shared-storage overlap. Arbitrary
partially overlapping Regions are unsupported for both operations. Use a
separate output when these restrictions apply; no overlap detection is added.

Compatible both-empty Compare operands release Destination. Release metadata
follows native OpenCV and the old output, rather than a fresh function result:
4.x retains rank with zero extents; 5.0 clears rank/shape. Old depth/channels
remain, and old aliases survive. Empty In_Range raises `OpenCV_Error` and leaves
Destination unchanged. Temporary external/selected Mat inputs are legal, but
temporary Destinations are rejected independently in Ada and the raw ABI,
even when their layout already matches. Null/enum/capability rejection is
pre-native; arbitrary failures after native execution starts are not promised
atomic. UMat paths stay UMat-native at the boundary; OpenCV can internally fall
back to CPU (including N-D iteration). OpenCL enabled is not proof of GPU
execution. See [exact source and helper findings](../tests/probes/mask_destination_source_findings.md).

Both Mat and UMat retain allocation-returning weighted functions with
independent result storage, and also provide direct destination procedures:

```ada
Weighted := Add_Weighted (Left, 0.75, Right, 0.25, Gamma => 2.0);
Add_Weighted
  (Left        => Left,
   Alpha       => 0.75,
   Right       => Right,
   Beta        => 0.25,
   Destination => Existing,
   Gamma       => 2.0);

Scaled := Scale_Add (A, 1.5, B);
Scale_Add
  (Self        => A,
   Scale       => 1.5,
   Right       => B,
   Destination => Existing);
```

Gamma stays last/defaulted. `Add_Weighted` accepts identical N-D source shape,
depth and channels; `Scale_Add` intentionally requires matching 2-D sources.
Destination is not an operand: incompatible shape, depth or channels reallocate
or detach it. Compatible whole storage and interior Regions are reused, including
the final Float16 compatibility narrowing, so retained aliases see writes and
Regions stay attached to their Parent. Old aliases retain old storage after
detachment. Exact Left/Self/Right and distinct same-layout shallow aliases are
supported, using the old operand values. Operands may share storage with each
other. Arbitrary partially overlapping Regions are **unsupported**; there is no
overlap detection or hidden temporary-result/copy-back.

Independent compatible output follows the allocation-returning function's
same-build numerical contract. Floating alias rounding follows direct native
execution: specifically, OpenCV 5.0 weighted Float32 kernels can use an overlapping
SIMD last block for fresh output but a scalar tail for aliases, exposing FMA/order
rounding differences at width 257. This does not relax ordinary integer exactness
or floating numerical correctness. NaN payload identity, universal signed-zero
identity, cross-architecture bits and fused/non-fused equivalence are not promised.

Coefficients are passed as double without added finiteness checks. Generic CPU
weighted UInt8/Int16 kernels narrow coefficients to Float32; the generic Int32
fallback uses double work/coefficient precision, but a platform HAL can preempt
that fallback with different native precision. On 4.x weighted Float32 CPU
scalar tails use double coefficients while SIMD lanes use Float32;
5.0 narrows Float32 coefficients on both
paths. Float64 retains double. OpenCL arithmetic narrows scalars whenever its work
depth is Float32 (including integer weighted work); double work retains double.
Scale_Add narrows Scale for Float32, retains double for Float64, and delegates
integer CPU arithmetic to addWeighted. UInt8 and Int16 saturate; Int32 has **no
overflow/saturation promise**. OpenCL Float32 work and platform CPU backends can
round large Int32 values differently from the generic double fallback. Native
backend behavior is authoritative for function and destination forms, rather
than normalized by the binding. Disabling OpenCL does not force generic CPU
execution or disable CPU HALs. Exact integer observations use typed access,
not Float64 conversion; portable exact mathematics is tested separately from
deliberately precision-sensitive large-integer native parity.

Temporary external/selected Mat views may be sources, but cannot be Destination:
native output creation/rebinding could sever their callback-scoped capability.
Source-validation and raw null/capability failures preserve output; arbitrary
post-native failure atomicity is not promised. Empty output metadata follows the
existing helper, version and argument order, not normalization: weighted mixed
default/typed empties are rejected by rank validation, whereas scale-add accepts
the compatible UInt8 mixes. UMat stays UMat-native at the binding boundary,
including Float16 intermediates; OpenCV may fall back to CPU. No GPU execution is
claimed. See [exact source and probe findings](../tests/probes/weighted_destination_source_findings.md).

`Add_Weighted` accepts Float16 operands with the same shape, depth, and
channel-count compatibility rules as the other public depths. Its result is
always Float16. On OpenCV 4.1, 4.6, and 4.10, the binding widens Float16
operands to Float32, executes OpenCV's optimized Float32 `addWeighted` with
the public `double` coefficients, and narrows once to Float16. On OpenCV 5.0,
the binding uses native `CV_16F` `addWeighted` with those same public `double`
coefficients. The optimized paths may use SIMD, fused multiply-add, differing
vector widths, and scalar tails, so exact Float16 result bits may differ
between OpenCV versions and platforms. NaN payload identity and signed-zero
identity are not promised.

For `Scale_Add`, OpenCV 4.1 through 5.0 expose dedicated CPU `scaleAdd`
kernels only for Float32 and Float64, not Float16. Float16 `Scale_Add` is
implemented by widening the operands to Float32, narrowing Scale to Float32,
executing OpenCV's optimized Float32 `scaleAdd` operation, and narrowing the
result back to Float16. Unlike `Add_Weighted`, this path preserves OpenCV's
optimized SIMD and fused-multiply-add execution rather than imposing
binding-controlled rounding. Numerical results therefore follow the OpenCV
Float32 execution path and may exhibit platform- or SIMD-dependent last-bit
differences after conversion to Float16. Exact Float16 bits are not promised
to be independent of architecture, SIMD dispatch, or scalar-tail placement.
This compatibility path is used across OpenCV 4.1-5.0 because those supported
versions do not expose a `CV_16F` `scaleAdd` kernel. `Scale_Add` remains
intentionally 2-D.
For finite numerically unequal operands, `Minimum` and `Maximum` select the
smaller or larger binary16 operand exactly. Their signed-zero, infinity, and
NaN behavior follows the established Float32 `cv::min` / `cv::max` semantics
through the compatibility model; they are not advertised as IEEE `fmin` or
`fmax`. OpenCV 5.x uses native Float16 min/max only while it conforms to that
model. This is an arithmetic semantic policy, distinct from Float16 storage and
typed access, which preserve exact binary16 object bits including NaN payloads.
Arithmetic does not promise NaN-payload preservation; it preserves numeric and
classification behavior. This does not imply broad Float16 support for other
Core algorithms.

Algebraic multiplication is deliberately separate as `Matrix_Multiply`.

### Masks and selection

Mask production and selection include:

- `In_Range`
- `Compare`
- `Count_Non_Zero`
- `Has_Non_Zero`
- `Find_Non_Zero`

Masked consumers include:

- `Copy_To`
- `Set_To`
- bitwise operations
- `Mean`
- `Mean_Std_Dev`
- `Norm`
- `Min_Max_Loc`

The common mask model is a same-shape UInt8 C1 Mat; any nonzero mask value
selects the complete source element.

### Bitwise operations

Available masked/unmasked families include:

- `Bitwise_And`
- `Bitwise_Or`
- `Bitwise_Xor`
- `Bitwise_Not`

OpenCV's stored-bit interpretation is preserved for floating-point Mats.

All four families also provide masked and unmasked reusable destination
procedures for both `Mat` and `UMat`. Existing functions still allocate
independent results:

```ada
Bitwise_Xor
  (Left        => A,
   Right       => B,
   Destination => Existing);
Bitwise_And
  (Left        => A,
   Right       => B,
   Mask        => Selection,
   Destination => Existing);
```

**Masked reuse preserves unselected values.** With a compatible masked
Destination, `mask == 0` preserves the exact old Destination element. If native
output creation reallocates Destination, OpenCV initializes the new masked
output to zero, so `mask == 0` produces zero there. This is intentionally not
normalized to the allocation-returning function. An all-zero mask leaves a
compatible destination unchanged, but produces zeros after reallocation and
in the allocation-returning function. Every nonzero mask byte selects: `1`,
`2`, `127`, and `255` all select the whole element, including all C3/C4 channels.

Compatible whole matrices and Regions retain their storage, geometry and
shallow aliases. Shape, depth or channel mismatches detach only Destination's
header; the old Parent and aliases survive. Exact source/destination aliases
and distinct shallow headers with the same storage/layout are supported for
Left, Right and Not's Self, including masks; selected elements use old source
bits and unselected elements retain old destination bits. Arbitrarily partially
overlapping Regions are unsupported. Destination aliasing Mask is outside the
supported alias contract; there are no overlap detection or hidden copies.

Floating storage is treated as raw bits, including Float16 binary16 zeros,
infinities and NaN payloads; this is not floating arithmetic. Unmasked Not
retains genuine N-D capability. Binary And/Or/Xor retain matching 2-D operands;
masked operations retain the existing matching 2-D UInt8 C1 mask boundary.
Temporary external/selected Mat views are legal sources/masks, but never
destinations, even if compatible. Ada validation and raw pre-native rejection
leave destination unchanged; arbitrary post-native failure atomicity is not
promised. Empty results preserve the existing helper/version representation
boundary: release may retain the old destination type and (4.x) zero extents,
while 5.0 release resets rank. Function and destination empty metadata need not
be identical. UMat operations remain native at the binding boundary, without
Mat mapping or staging; OpenCV itself may fall back to CPU.

See [exact source and helper-probe findings](../tests/probes/bitwise_destination_source_findings.md).

### Channel manipulation

Current channel operations include:

- `Split`
- `Merge`
- `Extract_Channel`
- `Insert_Channel`
- `Mix_Channels`
- `Channel_Route`
- explicit zero-fill routing

Collection APIs respect Ada array iteration order instead of assuming lower
bound zero.

### Layout, rearrangement, and borders

Implemented operations include:

- `Transpose`
- `Flip`
- `Rotate`
- `Repeat`
- `HConcat`
- `VConcat`
- `Diagonal_View`
- `Diagonal_Matrix`
- `Copy_Make_Border`
- `Border_Interpolate`

Border modes use strong Ada values rather than exposing OpenCV integer flags.
`Border_Interpolate` returns an Ada discriminated result for constant-border
coordinates instead of exposing OpenCV's `-1` sentinel.

### Sorting, reductions, and statistics

Sorting:

- `Sort`
- `Sort_Indices`

Scalar/statistical operations include:

- `Sum`
- `Trace`
- `Mean`
- `Mean_Std_Dev`
- `Norm`
- `Min_Max_Loc`
- `Count_Non_Zero`
- `Has_Non_Zero`
- `Find_Non_Zero`
- `Dot_Product`
- `Mahalanobis_Distance`
- `Covariance`
- `Peak_Signal_To_Noise_Ratio`

`Min_Max_Loc` remains the 2-D Point-based API (`X = column`, `Y = row`).
`Min_Max_Indices` adds dense N-D extrema for non-empty C1 Mats of depth UInt8,
Int8, UInt16, Int16, Int32, Float32, or Float64; Float16 is unsupported in the
portable Ada API. Its `ND_Min_Max_Result` holds independent `Has_Minimum` and
`Has_Maximum` flags and 32-entry locations. Coordinates are zero-based in
`Shape` / `Extent` / `Index_Array` / `Slice` dimension order: for 2-D, entry 1
is row and entry 2 is column. `Dimensions = Self.Dimension_Count`; only
`1 .. Dimensions` location entries are meaningful, and unused entries are zero.
Non-contiguous N-D Slices are supported with coordinates relative to the Slice.

The masked overload requires UInt8 C1 and equality of the **entire N-D shape**;
any nonzero mask element selects its corresponding dense element. An all-zero
mask returns zero values/locations with both flags false. Unlike sparse extrema,
all logical dense elements selected by the mask participate. Inputs and shallow
aliases remain unchanged. Ordinary finite extrema are the portable guarantee;
NaN/Infinity values and index validity follow native version/backend behavior,
not mathematical normalization. See the
[exact-version research note](../tests/probes/nd_min_max_source_findings.md).

Axis reduction:

- `Reduce` with Sum, Average, Maximum, Minimum, and Sum of Squares
- explicit output-depth overloads
- `Arg_Minimum`
- `Arg_Maximum`
- first/last equal-extremum selection through `Extremum_Occurrence`

Range/non-finite operations:

- `Check_Range`
- bounded `Check_Range`
- `Patch_NaNs`

### In-place initialization and symmetry

- `Set_To`
- `Set_Identity`
- `Complete_Symmetry`

### Per-element transforms

- `Transform`
- `Perspective_Transform`

`Perspective_Transform` outputs can be inspected directly with
`Float32_Vec2_Access` for Float32 C2, `Float64_Vec2_Access` for Float64 C2,
`Float32_Vec3_Access` for Float32 C3, and `Float64_Vec3_Access` for Float64 C3.
`Transform` C4 outputs can be inspected directly with `UInt8_Vec4_Access`,
`UInt16_Vec4_Access`, `Int32_Vec4_Access`, `Float32_Vec4_Access`, or `Float64_Vec4_Access`, without splitting channels or
narrowing Float64.

These transform channel vectors stored at each element. They are not image
resampling/warping operations; those belong in an `imgproc` binding.

### Polynomial and optimization helpers

The current Core slice also includes:

- `Solve_Cubic`
- `Solve_Polynomial`
- `Solve_Linear_Program`

These APIs use Ada result types to represent mathematically meaningful status
rather than exposing raw OpenCV integer return conventions.

---

## Linear algebra and decomposition

Dense linear-algebra coverage is substantial.

### Basic algebra

- `Trace`
- `Determinant`
- LU `Invert`
- LU `Solve`
- `Solve_Least_Squares` using SVD
- `Dot_Product`
- `Cross_Product`
- `Mahalanobis_Distance`
- `Matrix_Multiply`
- `Matrix_Multiply_Add`
- centered and uncentered `Transposed_Product`
- `Set_Identity`
- `Complete_Symmetry`

`Multiply` remains element-wise. `Matrix_Multiply` is algebraic multiplication.

### Covariance and eigen decomposition

- `Covariance`
- symmetric `Eigen_Decomposition`
- `Non_Symmetric_Eigen_Decomposition`

The symmetric API requires a caller-supplied real symmetric matrix. The
non-symmetric API follows OpenCV's real-eigenvalue assumptions rather than
inventing complex-eigenvalue behavior.

### PCA

- `Principal_Component_Analysis`
- explicit component-count selection
- retained-variance selection
- `PCA_Project`
- `PCA_Back_Project`

Both row-oriented and column-oriented sample layouts are represented explicitly
through `Sample_Orientation`.

### LDA

- `Linear_Discriminant_Analysis`
- explicit component-count overload
- `LDA_Project`
- `LDA_Reconstruct`

LDA uses a dedicated result record and keeps OpenCV's basis representation
behind an Ada-friendly API.

### SVD family

- compact `Singular_Value_Decomposition`
- `SVD_Back_Substitute`
- `SVD_Solve_Zero`
- `Pseudo_Inverse`
- `Reciprocal_Condition_Number`

### LU versus SVD APIs

`Invert` and `Solve` deliberately remain LU-specific. Least-squares and
rank-deficient SVD pseudo-solutions, SVD back substitution, pseudoinverse,
condition number, and null-space solving are separate explicit APIs instead of
being hidden behind a C++ decomposition flag. Rank-deficient
`Solve_Least_Squares` is a residual-minimizing `cv::solve(DECOMP_SVD)` result,
not a uniquely specified Moore-Penrose minimum-norm vector.

---

## Spectral transforms

The current spectral slice includes full-complex and packed real-input DFT
support, plus orthonormal DCT support:

- `Discrete_Fourier_Transform`
- `Inverse_Discrete_Fourier_Transform`
- `Inverse_Real_Discrete_Fourier_Transform`
- `Packed_Discrete_Fourier_Transform`
- `Inverse_Packed_Discrete_Fourier_Transform`
- `Discrete_Fourier_Transform_Rows`
- `Inverse_Discrete_Fourier_Transform_Rows`
- `Inverse_Real_Discrete_Fourier_Transform_Rows`
- `Packed_Discrete_Fourier_Transform_Rows`
- `Inverse_Packed_Discrete_Fourier_Transform_Rows`
- `Discrete_Cosine_Transform`
- `Inverse_Discrete_Cosine_Transform`
- `Discrete_Cosine_Transform_Rows`
- `Inverse_Discrete_Cosine_Transform_Rows`
- `Multiply_Spectra`
- `Multiply_Packed_Spectra`
- `Multiply_Packed_Spectra_Rows`
- `Optimal_DFT_Size`

Four forward Fourier forms are available: ordinary full-complex, ordinary
packed CCS, row-wise full-complex, and row-wise packed CCS.
`Discrete_Fourier_Transform` returns a full two-channel (`C2`) complex spectrum.
Use `Float32_Vec2_Access` or `Float64_Vec2_Access` to inspect full-complex
spectra: for these spectral APIs, component 0 is real and component 1 is
imaginary. Vec2 values outside this context remain semantic-neutral.
For real (`C1`) input, `Packed_Discrete_Fourier_Transform` returns OpenCV's
native same-shape, same-depth packed CCS (`C1`) spectrum. The `_Rows` forms
perform each row as an independent 1-D transform. In particular,
`Packed_Discrete_Fourier_Transform_Rows` returns a same-shape C1 Mat containing
one independent packed CCS representation per row, rather than an ordinary 2-D
spectrum. The packed representation is opaque and its physical storage layout
follows OpenCV. All inverse paths are scaled, so a forward/inverse round trip
approximately recovers the source without an extra caller scale factor.
`Inverse_Real_Discrete_Fourier_Transform` provides the real-output path for
The corresponding `_Rows` operations use `DFT_ROWS` to transform every row as
an independent 1-D signal. Full-complex C2 and packed CCS C1 row spectra have
distinct inverse operations.
The corresponding row-wise DCT operations use `DCT_ROWS` and OpenCV's
orthonormal inverse convention. Only the row length must be one or even; the
number of independent rows may be odd.

`Multiply_Spectra` operates on full-complex C2 spectra interpreted as one
spectrum. `Multiply_Packed_Spectra` operates on packed CCS C1 spectra using
ordinary non-row-wise spectrum geometry. `Multiply_Packed_Spectra_Rows`
expects packed CCS C1 input containing one independent spectrum per row, such
as output from `Packed_Discrete_Fourier_Transform_Rows`, and uses `DFT_ROWS`.
These operations distinguish ordinary multiplication from conjugate-right
multiplication with `Spectrum_Multiplication_Kind`.

Spectrum multiplication does not automatically perform forward or inverse
transforms, scale, pad, crop, or construct a complete convolution or
correlation pipeline. Callers are responsible for those operations and for
deciding whether their padding and geometry represent circular or linear
convolution or correlation. Packed spectrum division, CCS-bin accessors,
representation conversion, and in-place transforms are not yet exposed.

---

## Random numbers, clustering, and nearest neighbors

### RNG

The API supports both OpenCV's thread-local default RNG and caller-owned RNG
state:

- `Set_Random_Seed`
- `Make_Random_Number_Generator`
- `Next_Random`
- `Uniform_Random`
- `Fill_Uniform`
- `Fill_Normal`
- `Shuffle`

`Fill_Uniform`, `Fill_Normal`, and `Shuffle` have overloads using an explicit
caller-owned generator, allowing deterministic sequences without mutating the
calling thread's default OpenCV RNG state.

The RNG is deterministic pseudorandom state, not a cryptographic RNG.

### K-means

`K_Means` supports:

- random centers;
- k-means++ centers;
- configurable count+epsilon criteria;
- multiple attempts;
- an overload using caller-supplied initial labels.

The result record contains independently owned labels, centers, and compactness.

### K-nearest neighbors / batch distance

`K_Nearest_Neighbors` exposes a focused nearest-neighbor slice over OpenCV
batch-distance behavior. Supported distance kinds include:

- L1
- L2
- squared L2
- Hamming
- Hamming2

The result contains independent distance and zero-based candidate-index Mats.
