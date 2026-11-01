with Ada.Finalization;
with Interfaces;
private with OpenCV.Internal.C_API;

--  Core module matrix abstractions and operations. This package declares
--  Mat and UMat, which are controlled native-resource abstractions rather
--  than ordinary value-only arrays, together with the matrix-specific types
--  (element depth, channel count, shapes, regions and result records) and
--  the Core operations that use them. Shared geometry and scalar values such
--  as Point, Size, Rect and Scalar are declared in the parent package
--  OpenCV. Native OpenCV compatibility spans the versions supported by this
--  repository; the package does not promise identical implementation details
--  across them. Input validation, alias restrictions and exception behavior
--  are defined by the contract of each operation.

package OpenCV.Core is

   --  Per-channel storage representation of Mat and UMat elements. Depth
   --  describes how each channel value is stored; it is not a value-range,
   --  saturation or rounding policy, which belong to the operation that
   --  converts or writes the values. The channel count is separate (see
   --  Mat_Type).
   --  @enum UInt8 Unsigned 8-bit integer channel values.
   --  @enum Int8 Signed 8-bit integer channel values.
   --  @enum UInt16 Unsigned 16-bit integer channel values.
   --  @enum Int16 Signed 16-bit integer channel values.
   --  @enum Int32 Signed 32-bit integer channel values.
   --  @enum Float32 IEEE binary32 floating-point channel values.
   --  @enum Float64 IEEE binary64 floating-point channel values.
   --  @enum Float16 IEEE binary16 channel values, exposed as Float16_Value
   --  bit patterns. Operation support for this depth is operation-specific.
   type Depth_Type is
     (UInt8, Int8, UInt16, Int16, Int32, Float32, Float64, Float16);

   --  Norm reduced by Mat.Norm over the selected elements into a single
   --  Long_Float. Compare Normalize_Kind, which selects a normalization
   --  target instead.
   --  @enum L1 Sum of the absolute values of the selected scalar components.
   --  @enum L2 Euclidean norm: square root of the sum of the squared selected
   --  scalar components.
   --  @enum Infinity Largest absolute value among the selected scalar
   --  components.
   type Norm_Kind is (L1, L2, Infinity);

   --  Native binary reduction cell size for UInt8 single-channel descriptors.
   --  No numeric selector mask or relative mode is provided for binary norms.
   --  @enum One_Bit Count set bits (or differing bits for a pair).
   --  @enum Two_Bits Count nonzero adjacent two-bit cells. A cell 11 counts
   --  once, not twice; this is not One_Bit divided by two.
   type Binary_Norm_Kind is (One_Bit, Two_Bits);

   --  Min_Max is a normalization mode rather than a Mat.Norm reduction kind.
   --  @enum L1 Scale so that the L1 norm equals the requested target value.
   --  @enum L2 Scale so that the L2 norm equals the requested target value.
   --  @enum Infinity Scale so that the infinity norm equals the requested
   --  target value.
   --  @enum Min_Max Map the data range onto the requested lower and upper
   --  bounds instead of targeting a norm.
   type Normalize_Kind is (L1, L2, Infinity, Min_Max);

   --  Element-wise relation applied by Compare, read as Left relation Right.
   --  @enum Equal True where Left equals Right.
   --  @enum Not_Equal True where Left differs from Right.
   --  @enum Less_Than True where Left is strictly less than Right.
   --  @enum Less_Or_Equal True where Left is less than or equal to Right.
   --  @enum Greater_Than True where Left is strictly greater than Right.
   --  @enum Greater_Or_Equal True where Left is greater than or equal to
   --  Right.
   type Comparison_Kind is
     (Equal,
      Not_Equal,
      Less_Than,
      Less_Or_Equal,
      Greater_Than,
      Greater_Or_Equal);

   --  Mirror direction applied by Flip.
   --  @enum Vertical Reverses the order of the rows.
   --  @enum Horizontal Reverses the order of the columns.
   --  @enum Both_Axes Reverses both the row order and the column order.
   type Flip_Kind is (Vertical, Horizontal, Both_Axes);

   --  Rotation applied by Rotate. Quarter turns exchange rows and columns.
   --  @enum Clockwise_90 Quarter turn clockwise.
   --  @enum Half_Turn Rotation by 180 degrees, preserving the dimensions.
   --  @enum Counterclockwise_90 Quarter turn counterclockwise.
   type Rotation_Kind is (Clockwise_90, Half_Turn, Counterclockwise_90);

   --  Direction in which Reduce and the Arg_ operations combine values.
   --  @enum Across_Rows Combines the rows of each column, producing a
   --  result with one row.
   --  @enum Across_Columns Combines the columns of each row, producing a
   --  result with one column.
   type Reduction_Axis is (Across_Rows, Across_Columns);

   --  Combining rule applied by Reduce, independently in each channel.
   --  @enum Sum Adds the combined values.
   --  @enum Average Arithmetic mean of the combined values.
   --  @enum Maximum Largest of the combined values.
   --  @enum Minimum Smallest of the combined values.
   --  @enum Sum_Of_Squares Adds the squares of the combined values.
   type Reduction_Kind is (Sum, Average, Maximum, Minimum, Sum_Of_Squares);

   --  Selects which equal extremum is reported by Arg_Minimum and Arg_Maximum.
   --  @enum First_Occurrence Reports the first equal extremum along the
   --  reduced axis, which is the lowest index.
   --  @enum Last_Occurrence Reports the last equal extremum along the
   --  reduced axis, which is the highest index.
   type Extremum_Occurrence is (First_Occurrence, Last_Occurrence);

   --  Sort axis names describe the values being ordered, not a reduction.
   --  Each_Row sorts the columns of every row independently, left to right.
   --  Each_Column sorts the rows of every column independently, top to bottom.
   --  @enum Each_Row Orders the values within each row.
   --  @enum Each_Column Orders the values within each column.
   type Sort_Axis is (Each_Row, Each_Column);

   --  Ordering direction used by Sort.
   --  @enum Ascending Smallest value first.
   --  @enum Descending Largest value first.
   type Sort_Order is (Ascending, Descending);

   --  Selects the uncentered transposed-product orientation. There is
   --  no default; the caller must choose which square product is
   --  intended.
   --  @enum Transpose_Times_Self Product of the transpose of Self with
   --  Self; the result has one row and column per column of Self.
   --  @enum Self_Times_Transpose Product of Self with its transpose; the
   --  result has one row and column per row of Self.
   type Transposed_Product_Order is
     (Transpose_Times_Self, Self_Times_Transpose);

   --  Identifies which triangle of a square Mat is authoritative when
   --  completing symmetry in place. Upper_Triangle copies the upper
   --  triangle onto the lower triangle. Lower_Triangle copies the lower
   --  triangle onto the upper triangle.
   --  @enum Upper_Triangle The upper triangle is authoritative and is
   --  reflected onto the lower triangle.
   --  @enum Lower_Triangle The lower triangle is authoritative and is
   --  reflected onto the upper triangle.
   type Symmetry_Source is (Upper_Triangle, Lower_Triangle);

   --  Interprets a 2-D sample matrix for Covariance. Samples_Are_Rows
   --  treats each row as one observation. Samples_Are_Columns treats
   --  each column as one observation.
   --  @enum Samples_Are_Rows Each row is one observation and each column
   --  is one feature.
   --  @enum Samples_Are_Columns Each column is one observation and each
   --  row is one feature.
   type Sample_Orientation is (Samples_Are_Rows, Samples_Are_Columns);

   --  Selects whether Covariance divides the accumulation by the
   --  sample count N. Unscaled leaves the raw accumulation.
   --  By_Sample_Count applies OpenCV's COVAR_SCALE factor 1/N. This
   --  is not unbiased covariance and is not 1/(N - 1).
   --  @enum Unscaled The raw centered accumulation is returned without
   --  division.
   --  @enum By_Sample_Count The accumulation is multiplied by 1/N, where N
   --  is the number of samples. This is not the 1/(N - 1) estimator.
   type Covariance_Scaling is (Unscaled, By_Sample_Count);

   --  Selects ordinary complex spectrum multiplication or
   --  multiplication by the conjugate of the right-hand spectrum.
   --  Ordinary products participate in frequency-domain convolution.
   --  Conjugate-right products participate in frequency-domain
   --  correlation. This operation performs only spectral
   --  multiplication; inverse transformation and any required
   --  padding or cropping remain caller operations.
   --  @enum Ordinary_Spectrum_Product Multiplies corresponding elements as
   --  complex numbers without conjugation, as used for convolution.
   --  @enum Conjugate_Right_Spectrum_Product Multiplies each left element
   --  by the complex conjugate of the corresponding right element, as used
   --  for correlation.
   type Spectrum_Multiplication_Kind is
     (Ordinary_Spectrum_Product, Conjugate_Right_Spectrum_Product);

   --  Number of channels per matrix element. This counts channels, not
   --  bytes; the byte size of an element also depends on the depth.
   type Channel_Count is new Interfaces.Integer_32 range 1 .. 512;

   --  Nonnegative size or count. The consuming operation determines whether
   --  a value counts elements, bytes, or another quantity.
   type Mat_Size is
     new Interfaces.Integer_64 range 0 .. Interfaces.Integer_64'Last;

   --  Positive moves a boundary outward; negative moves it inward.
   type Region_Adjustment is new Interfaces.Integer_32;

   --  Retained allocation geometry, not an owning parent object. Offset is
   --  zero-based (X = column, Y = row), including for nested Regions.
   --  This record describes geometry and offsets only; it does not identify
   --  the native allocation.
   --  @field Whole_Size Extent of the original allocation that contains the
   --  Region.
   --  @field Offset Zero-based location of the Region's first element within
   --  that allocation.
   type Region_Location is record
      Whole_Size : Size;
      Offset     : Point;
   end record;

   --  A border interpolation either selects a zero-based source coordinate or
   --  indicates that an out-of-range Constant_Border coordinate has no donor.
   --  Consumers must test Uses_Constant before reading Index; Index exists
   --  only when Uses_Constant is False.
   --  @field Uses_Constant True when no source coordinate is available and
   --  the caller must supply the constant border value instead.
   --  @field Index Zero-based source coordinate. Present only when
   --  Uses_Constant is False.
   type Border_Interpolation_Result (Uses_Constant : Boolean := False) is
   record
      case Uses_Constant is
         when False =>
            Index : Size_Coordinate;

         when True =>
            null;
      end case;
   end record;

   --  A zero-based half-open index interval: Start <= index < Stop.
   --  @field Start Zero-based first index included in the interval.
   --  @field Stop Zero-based bound one past the last included index; the
   --  index Stop itself is excluded.
   type Index_Range is record
      Start : Size_Coordinate := 0;
      Stop  : Size_Coordinate := 0;
   end record;

   --  N-dimensional Mat shape. Iteration order maps directly to OpenCV
   --  dimensions regardless of the array's index bounds.
   type Dimension_Array is array (Positive range <>) of Size_Coordinate;
   --  Per-dimension strides for strided caller-owned N-D Mat views. One
   --  stride is supplied for each Mat dimension, in the same iteration order
   --  as the matching Dimension_Array; the array's index bounds are
   --  irrelevant. Strides count COMPLETE Mat elements, never bytes: for
   --  C2/C3/C4 layouts one stride unit is one complete Vec2/Vec3/Vec4
   --  element, not one scalar channel. The final dimension's stride must be
   --  exactly 1. For Shape (D1, .., Dn) and Strides (S1, .., Sn), zero-based
   --  index (I1, .., In) denotes Data (Data'First + I1 * S1 + .. + In * Sn).
   --  For example, Shape => (2, 3, 4) with Strides => (20, 6, 1) maps
   --  (I, J, K) to Data (Data'First + I * 20 + J * 6 + K).
   type Dimension_Stride_Array is array (Positive range <>) of Positive;
   --  Zero-based N-dimensional Mat indices. Iteration order maps directly
   --  to OpenCV dimensions regardless of the array's index bounds.
   type Index_Array is array (Positive range <>) of Size_Coordinate;
   --  N-dimensional Mat index ranges. Iteration order maps directly to
   --  OpenCV dimensions regardless of the array's index bounds.
   type Index_Range_Array is array (Positive range <>) of Index_Range;

   --  Per-dimension selector for With_Selected_View. Keep_Range retains the
   --  dimension restricted to the half-open interval Bounds; Fix_Index
   --  selects the single zero-based Index and drops the dimension from the
   --  result.
   --  @enum Keep_Range The dimension is retained, restricted to a range.
   --  @enum Fix_Index A single index is selected and the dimension is
   --  removed, so the result has one fewer dimension.
   type Dimension_Selection_Kind is (Keep_Range, Fix_Index);

   --  Selector for one source dimension. Kind determines which variant
   --  component exists; a value never holds both Bounds and Index.
   --  @field Kind Selects the variant: Keep_Range or Fix_Index.
   --  @field Bounds Zero-based half-open interval retained for the
   --  dimension. Present only when Kind is Keep_Range.
   --  @field Index Zero-based index selected for the dimension, which is
   --  then removed from the result. Present only when Kind is Fix_Index.
   type Dimension_Selection (Kind : Dimension_Selection_Kind := Keep_Range) is
   record
      case Kind is
         when Keep_Range =>
            Bounds : Index_Range;

         when Fix_Index =>
            Index : Size_Coordinate;
      end case;
   end record;

   --  One selector per source dimension. Iteration order maps directly to
   --  source dimensions regardless of the array's index bounds.
   type Dimension_Selection_Array is
     array (Positive range <>) of Dimension_Selection;

   --  Exact IEEE-754 binary16 encoding used by OpenCV CV_16F. This is
   --  the stored 16-bit pattern, not Short_Float, Float, Integer_16, or
   --  a numeric Unsigned_16 value. Classification inspects the binary16
   --  fields directly: bit 15 is the sign, bits 14 .. 10 are the
   --  exponent, and bits 9 .. 0 are the fraction. Is_Negative reports
   --  the stored sign bit, so it is True for -0, negative finites,
   --  -Infinity, and negative NaNs. NaN payloads, signed zeros,
   --  infinities, and subnormals retain their exact bits.
   --  Float16_From_Bits / Float16_Bits copy that encoding. To_Float16 /
   --  To_Float32 convert numerically between binary16 and binary32.
   --  OpenCV.Core.Float16_Access stores and loads the exact encoding.
   type Float16_Value is private;

   --  Reinterprets a 16-bit pattern as a Float16_Value without numeric
   --  conversion. Every pattern is accepted, including NaN payloads, signed
   --  zeros, infinities, and subnormals, and is retained exactly.
   --  @param Bits The IEEE-754 binary16 bit pattern.
   --  @return The Float16_Value holding exactly those bits.
   function Float16_From_Bits
     (Bits : Interfaces.Unsigned_16) return Float16_Value;

   --  Returns the exact stored binary16 bit pattern of Value. This is not a
   --  numeric conversion; use To_Float32 for the numeric value.
   --  @param Value The Float16_Value to inspect.
   --  @return The stored 16-bit pattern.
   function Float16_Bits (Value : Float16_Value) return Interfaces.Unsigned_16;

   --  Reports whether Value is a NaN: exponent bits all one and a nonzero
   --  fraction. The NaN sign and payload are not considered.
   --  @param Value The Float16_Value to classify.
   --  @return True when Value is a NaN.
   function Is_NaN (Value : Float16_Value) return Boolean;

   --  Reports whether Value is positive or negative infinity: exponent bits
   --  all one and a zero fraction.
   --  @param Value The Float16_Value to classify.
   --  @return True when Value is an infinity of either sign.
   function Is_Infinite (Value : Float16_Value) return Boolean;

   --  Reports whether Value is neither an infinity nor a NaN. Zeros and
   --  subnormals are finite.
   --  @param Value The Float16_Value to classify.
   --  @return True when the exponent bits are not all one.
   function Is_Finite (Value : Float16_Value) return Boolean;

   --  Reports whether Value is subnormal: exponent bits all zero and a
   --  nonzero fraction. Positive and negative zero are not subnormal.
   --  @param Value The Float16_Value to classify.
   --  @return True when Value is a nonzero subnormal of either sign.
   function Is_Subnormal (Value : Float16_Value) return Boolean;

   --  Reports whether Value is positive or negative zero.
   --  @param Value The Float16_Value to classify.
   --  @return True when the exponent and fraction bits are all zero.
   function Is_Zero (Value : Float16_Value) return Boolean;

   --  Reports the stored sign bit. It is True for negative zero, negative
   --  finite values, negative infinity, and NaNs with the sign bit set.
   --  @param Value The Float16_Value to inspect.
   --  @return True when bit 15 is set.
   function Is_Negative (Value : Float16_Value) return Boolean;

   --  Converts IEEE binary32 to binary16 using round-to-nearest,
   --  ties-to-even. Finite overflow produces signed infinity. Values
   --  below the normal binary16 range may become subnormal or zero.
   --  Signed zeros, infinities, and the NaN sign bit are preserved.
   --  NaN conversion copies the most significant payload bits that fit
   --  in the binary16 fraction and forces a nonzero fraction so NaN
   --  remains NaN. Payload width shrinks, so NaN encodings are not
   --  required to round-trip exactly through Float32. This is numeric
   --  conversion, not Float16_From_Bits.
   --  @param Value The binary32 value to convert.
   --  @return The nearest binary16 value under the stated rounding rule.
   function To_Float16 (Value : Float32_Value) return Float16_Value;

   --  Expands binary16 to binary32 exactly for every finite Float16
   --  value. Signed zeros and infinities retain their sign. NaNs remain
   --  NaNs, with the binary16 payload placed in the most significant
   --  bits of the binary32 fraction. This is numeric conversion, not
   --  Float16_Bits.
   --  @param Value The binary16 value to convert.
   --  @return The equal binary32 value.
   function To_Float32 (Value : Float16_Value) return Float32_Value;

   --  Runtime element format of a Mat or UMat.
   --  @field Depth Storage depth of each channel value of an element.
   --  @field Channels Number of channels in each matrix element.
   type Mat_Type is record
      Depth    : Depth_Type;
      Channels : Channel_Count;
   end record;

   --  Extrema and their 2-D locations, as returned by Min_Max_Loc. The
   --  producing operation defines how masks, empty inputs and equal extrema
   --  are handled.
   --  @field Minimum Smallest value found.
   --  @field Maximum Largest value found.
   --  @field Minimum_Location Location of the minimum, with X the column
   --  and Y the row, zero-based.
   --  @field Maximum_Location Location of the maximum, with X the column
   --  and Y the row, zero-based.
   type Min_Max_Result is record
      Minimum          : Long_Float;
      Maximum          : Long_Float;
      Minimum_Location : Point;
      Maximum_Location : Point;
   end record;

   --  Extrema and N-dimensional locations, as returned by Min_Max_Indices.
   --  Each Has_ flag independently reports whether the corresponding value
   --  and location are meaningful. When a flag is False, treat that side's
   --  value and location as absent; the default zero contents are not an
   --  extremum. Locations are zero-based and ordered like the dimensions of
   --  the source Mat.
   --  @field Has_Minimum True when Minimum and Minimum_Location are
   --  meaningful.
   --  @field Has_Maximum True when Maximum and Maximum_Location are
   --  meaningful.
   --  @field Minimum Smallest value found. Meaningful only when Has_Minimum
   --  is True.
   --  @field Maximum Largest value found. Meaningful only when Has_Maximum
   --  is True.
   --  @field Minimum_Location Zero-based index of the minimum in each
   --  dimension. Meaningful only when Has_Minimum is True, and then only for
   --  entries 1 .. Dimensions. The array has fixed capacity 32.
   --  @field Maximum_Location Zero-based index of the maximum in each
   --  dimension. Meaningful only when Has_Maximum is True, and then only for
   --  entries 1 .. Dimensions. The array has fixed capacity 32.
   --  @field Dimensions Number of source dimensions, which is how many
   --  leading entries of each location array are meaningful.
   type ND_Min_Max_Result is record
      Has_Minimum      : Boolean := False;
      Has_Maximum      : Boolean := False;
      Minimum          : Long_Float := 0.0;
      Maximum          : Long_Float := 0.0;
      Minimum_Location : Index_Array (1 .. 32) := (others => 0);
      Maximum_Location : Index_Array (1 .. 32) := (others => 0);
      Dimensions       : Natural := 0;
   end record;

   --  Per-channel statistics returned by Mean_Std_Dev. The estimator and
   --  the treatment of masks and empty inputs are defined by that
   --  operation.
   --  @field Mean Mean value of each channel, in the corresponding Scalar
   --  component.
   --  @field Standard_Deviation Standard deviation of each channel, in the
   --  corresponding Scalar component.
   type Mean_Std_Dev_Result is record
      Mean               : Scalar;
      Standard_Deviation : Scalar;
   end record;

   --  Discriminated result of Check_Range. First_Invalid is present only
   --  when Valid is False. Point.X is the column and Point.Y is the row.
   --  Consumers must test Valid before reading First_Invalid.
   --  @field Valid True when no invalid element was found.
   --  @field First_Invalid Zero-based location of the first invalid element
   --  in row-major order, with X the column and Y the row. Present only when
   --  Valid is False.
   type Range_Check_Result (Valid : Boolean := True) is record
      case Valid is
         when True =>
            null;

         when False =>
            First_Invalid : Point;
      end case;
   end record;

   --  Runtime-typed matrix backed by a native OpenCV cv::Mat. Each Mat
   --  object is a controlled header that owns its native resource and
   --  releases it on finalization. Ada assignment is shallow: the target
   --  gets its own independent header while the underlying data remains
   --  shared and reference counted, so a distinct header does not imply
   --  distinct storage. Clone makes an explicit deep copy with independent
   --  storage. Regions and other views may share the underlying allocation.
   --  Mutating operations and destination procedures have operation-specific
   --  alias and storage-reuse restrictions, and operations are not generally
   --  transactional on failure. Behavior of an empty Mat can vary between
   --  OpenCV versions.
   type Mat is tagged private;

   --  Runtime-typed matrix backed by native OpenCV UMat storage. It follows
   --  the same controlled-header ownership model as Mat: assignment is
   --  shallow and shares data through separate headers, while Clone makes an
   --  explicit deep copy. UMat uses native OpenCV UMat storage semantics;
   --  OpenCL acceleration is optional and is not guaranteed to be active.
   --  Views and mutating or destination operations have operation-specific
   --  alias and storage-reuse restrictions, and empty-header behavior can
   --  vary between OpenCV versions.
   type UMat is tagged private;

   --  Creates a typed two-dimensional UMat with the requested number of rows
   --  and columns. The element type fixes both the depth and the channel
   --  count of every element. Allocation uses native OpenCV UMat storage
   --  with USAGE_DEFAULT; OpenCL is optional, so the UMat is not guaranteed
   --  to be resident on a GPU or to execute through OpenCL. A zero Rows or
   --  Columns yields a typed, zero-extent UMat that still reports two
   --  dimensions, which is distinct from a default UMat header. Element
   --  contents are not promised to be initialized. Assignment retains shared
   --  storage via distinct native headers; Clone copies data.
   --  @param Rows Number of rows, at most the native signed 32-bit limit.
   --  @param Columns Number of columns, at most the native signed 32-bit
   --  limit.
   --  @param Element_Type Depth and channel count of each element.
   --  @return A new UMat that owns its own header and storage.
   function Create_UMat
     (Rows, Columns : Natural; Element_Type : Mat_Type) return UMat
   with Pre => Rows <= 2_147_483_647 and then Columns <= 2_147_483_647;

   --  Creates a typed N-dimensional UMat. Shape is read in iteration order,
   --  independent of its index bounds: the first element is the extent of
   --  native dimension 0, and so on. Two to 32 nonzero extents; OpenCV 5
   --  accepts at most 10 dimensions. A shape that violates the Ada-checked
   --  count or nonzero-extent limits raises OpenCV_Error. As for the 2-D
   --  overload, native UMat storage is used and active OpenCL execution is
   --  not guaranteed.
   --  @param Shape Extent of each dimension, in native dimension order.
   --  @param Element_Type Depth and channel count of each element.
   --  @return A new UMat that owns its own header and storage.
   function Create_UMat
     (Shape : Dimension_Array; Element_Type : Mat_Type) return UMat;

   --  Returns an independent deep copy of Self's elements. Unlike Ada
   --  assignment, which shares storage through a distinct header, the result
   --  does not share storage with Self. The metadata of a clone of an empty
   --  UMat follows the installed OpenCV release.
   --  @param Self The UMat to copy.
   --  @return A new UMat with independent storage.
   function Clone (Self : UMat) return UMat;

   --  Copies Self into a newly allocated UMat using native copyTo. This is
   --  the only UMat Copy_To form: unlike Mat, there is no caller-owned
   --  destination or masked procedure, so the Mat and UMat Copy_To overload
   --  sets are not symmetrical. The result owns independent storage.
   --  @param Self The UMat to copy.
   --  @return A new UMat holding a copy of Self's elements.
   function Copy_To (Self : UMat) return UMat;

   --  Converts Self to the requested depth into a new UMat, computing
   --  Scale * Self + Offset for every element. The channel count and shape
   --  are preserved and the result owns independent storage. Conversion
   --  follows native OpenCV rules, and a failure reported by OpenCV is raised
   --  as OpenCV_Error. Empty-source metadata follows the installed OpenCV
   --  version.
   --  @param Self The source UMat.
   --  @param Depth Depth of the result.
   --  @param Scale Factor applied to each source value before Offset.
   --  @param Offset Value added after scaling.
   --  @return A new UMat of the requested depth.
   function Convert_To
     (Self   : UMat;
      Depth  : Depth_Type;
      Scale  : Long_Float := 1.0;
      Offset : Long_Float := 0.0) return UMat;

   --  Converts into the actual native destination, reusing matching storage
   --  or reallocating mismatched storage. Compatible Regions retain parent
   --  sharing; incompatible Regions may detach. Exact self is supported,
   --  but arbitrary partially overlapping views are not supported.
   --  Empty-source metadata follows the installed OpenCV version. A failure
   --  after native conversion starts need not leave Destination unchanged.
   --  @param Self The source UMat.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @param Depth Depth of the converted elements.
   --  @param Scale Factor applied to each source value before Offset.
   --  @param Offset Value added after scaling.
   procedure Convert_To
     (Self        : UMat;
      Destination : in out UMat;
      Depth       : Depth_Type;
      Scale       : Long_Float := 1.0;
      Offset      : Long_Float := 0.0);

   --  Sets every element of Self in place to Value. Self keeps its shape,
   --  depth and channel count; Scalar component N initializes channel N.
   --  Self must have at most four channels, otherwise OpenCV_Error is
   --  raised, as it is for any failure reported by OpenCV. Writes go
   --  through Self's header, so every other header sharing Self's storage
   --  observes the change.
   --  @param Self The UMat to fill.
   --  @param Value Per-channel fill value; component N is used for channel N.
   procedure Set_To (Self : in out UMat; Value : Scalar);

   --  Creates a distinct UMat header sharing Self's storage for a 2-D region
   --  of interest; no elements are copied and only native UMat headers are
   --  used, without host mapping. Self must be nonempty and exactly 2-D.
   --  Area uses zero-based coordinates: X and Y must be nonnegative, the
   --  origin must lie inside Self, Width and Height must be positive, and the
   --  whole rectangle must fit inside Self. Otherwise OpenCV_Error is raised.
   --  The shared storage persists while any header refers to it.
   --  @param Self The UMat containing the region.
   --  @param Area Zero-based rectangle selecting the region.
   --  @return A new UMat header that may share Self's allocation.
   function Region (Self : UMat; Area : Rect) return UMat;

   --  Returns the geometry of the allocation retained by Self's region
   --  header: the whole allocation's extent and Self's zero-based offset in
   --  it. The result is geometry only and is not an allocation identity:
   --  two unrelated UMats can report identical values. Self must be nonempty
   --  and exactly 2-D, otherwise OpenCV_Error is raised.
   --  @param Self The UMat to locate.
   --  @return Whole-allocation size and Self's offset within it.
   function Locate_Region (Self : UMat) return Region_Location;

   --  Header-only adjustment with the same clipping/crossing semantics as
   --  Mat below. Positive adjustments move a boundary outward and negative
   --  adjustments move it inward, within the retained parent allocation. No
   --  elements are copied, and other shallow headers keep their independent
   --  geometry. Is_Submatrix is not a reliable indicator of the adjusted
   --  geometry. Self must be nonempty and exactly 2-D, otherwise OpenCV_Error
   --  is raised; native failures are also raised as OpenCV_Error, and the
   --  header is not promised to be unchanged for every native failure.
   --  @param Self The UMat header to adjust.
   --  @param Top Adjustment of the top boundary.
   --  @param Bottom Adjustment of the bottom boundary.
   --  @param Left Adjustment of the left boundary.
   --  @param Right Adjustment of the right boundary.
   procedure Adjust_Region
     (Self : in out UMat; Top, Bottom, Left, Right : Region_Adjustment);

   --  Creates a distinct UMat header sharing Self's storage for an
   --  N-dimensional slice. Exactly one half-open Index_Range is required per
   --  source dimension, applied in iteration order regardless of the array's
   --  index bounds. Every range must be nonempty (Start < Stop) and Stop must
   --  not exceed that dimension's extent, otherwise OpenCV_Error is raised.
   --  Depth, channel count and dimension count are retained, and each extent
   --  becomes Stop - Start. The slice is not necessarily contiguous.
   --  @param Self The UMat to slice.
   --  @param Ranges One zero-based half-open range per source dimension.
   --  @return A new UMat header that may share Self's allocation.
   function Slice (Self : UMat; Ranges : Index_Range_Array) return UMat;

   --  Reports whether Self has no elements, as defined by native UMat empty.
   --  A default header is empty, but an empty result is not necessarily a
   --  default header: a typed zero-extent UMat is also empty.
   --  @param Self The UMat to inspect.
   --  @return True when the UMat is empty.
   function Is_Empty (Self : UMat) return Boolean;

   --  Reports whether Self's current layout is continuous, with no gaps
   --  between rows. A region or slice that shares a larger allocation need
   --  not be continuous.
   --  @param Self The UMat to inspect.
   --  @return True when the native layout is continuous.
   function Is_Continuous (Self : UMat) return Boolean;

   --  Reports the native UMat submatrix flag. After Adjust_Region the flag
   --  is not authoritative current geometry; use Locate_Region for the
   --  retained allocation geometry.
   --  @param Self The UMat to inspect.
   --  @return The native submatrix flag.
   function Is_Submatrix (Self : UMat) return Boolean;

   --  Returns the native number of dimensions. A default UMat reports 0,
   --  while a typed 2-D UMat, including a zero-extent one, reports 2.
   --  @param Self The UMat to inspect.
   --  @return The dimension count.
   function Dimension_Count (Self : UMat) return Natural;

   --  Returns the extent of a 1-based axis. Axis 1 is native dimension 0.
   --  Raises OpenCV_Error when Axis is greater than Dimension_Count.
   --  @param Self The UMat to inspect.
   --  @param Axis One-based dimension, in 1 .. Dimension_Count.
   --  @return The extent of that dimension.
   function Extent (Self : UMat; Axis : Positive) return Size_Coordinate;

   --  Returns every extent in native dimension order, indexed 1 ..
   --  Dimension_Count. A UMat with no dimensions returns a null array. A 2-D
   --  UMat returns (Rows, Columns); an N-D UMat returns every axis extent.
   --  @param Self The UMat to inspect.
   --  @return The extents of all dimensions.
   function Shape (Self : UMat) return Dimension_Array;

   --  Returns the row count of a 2-D UMat. Raises OpenCV_Error when native
   --  OpenCV reports no row count because Self has more than two dimensions,
   --  so Rows alone does not describe an N-D shape; use Shape for that.
   --  @param Self The UMat to inspect.
   --  @return The number of rows.
   function Rows (Self : UMat) return Natural;

   --  Returns the column count of a 2-D UMat. Raises OpenCV_Error when native
   --  OpenCV reports no column count because Self has more than two
   --  dimensions, so Columns alone does not describe an N-D shape; use Shape
   --  for that.
   --  @param Self The UMat to inspect.
   --  @return The number of columns.
   function Columns (Self : UMat) return Natural;

   --  Returns the depth of each channel value. Depth is independent of the
   --  channel count, which Channels reports.
   --  @param Self The UMat to inspect.
   --  @return The element depth.
   function Depth (Self : UMat) return Depth_Type;

   --  Returns the number of channels in each element. This counts channels,
   --  not bytes; Element_Size gives the byte size of a complete element.
   --  @param Self The UMat to inspect.
   --  @return The channel count.
   function Channels (Self : UMat) return Channel_Count;

   --  Returns Self's runtime element type, composed from Depth and Channels.
   --  @param Self The UMat to inspect.
   --  @return The depth and channel count of each element.
   function Element_Type (Self : UMat) return Mat_Type;

   --  Returns the native total: the number of matrix elements. A
   --  multi-channel element counts once, and the value is not a byte count.
   --  @param Self The UMat to inspect.
   --  @return The number of elements.
   function Total (Self : UMat) return Mat_Size;

   --  Returns the size in bytes of one complete element, including all of its
   --  channels (native elemSize).
   --  @param Self The UMat to inspect.
   --  @return The byte size of one element.
   function Element_Size (Self : UMat) return Mat_Size;

   --  Returns the size in bytes of one channel of an element (native
   --  elemSize1), as opposed to the complete element size.
   --  @param Self The UMat to inspect.
   --  @return The byte size of one channel.
   function Channel_Size (Self : UMat) return Mat_Size;

   --  OpenCV 4.10 cv::RNG Multiply-With-Carry state. This deterministic
   --  pseudorandom generator is caller-owned rather than thread-local. Its
   --  complete state is 64 bits, so assignment copies the current sequence
   --  position and the copies subsequently advance independently. A default
   --  generator has state 16#FFFF_FFFF#; seed zero selects that same state.
   type Random_Number_Generator is private;

   --  Draws OpenCV 4.10 cv::RNG::next's raw Unsigned_32 result from the
   --  caller-owned Generator. Advances exactly one MWC step. This is
   --  deterministic pseudorandom data, not cryptographic randomness. It does
   --  not alter OpenCV's thread-local default RNG and composes with explicit
   --  Fill_Uniform, Fill_Normal, and Shuffle calls.
   --  @param Generator The generator to advance.
   --  @param Value The raw 32-bit result of the step.
   procedure Next_Random
     (Generator : in out Random_Number_Generator;
      Value     : out Interfaces.Unsigned_32);

   --  Draws OpenCV 4.10's Float64 uniform value from caller-owned Generator.
   --  Finite ordered bounds are required. For distinct bounds, the result is
   --  in [Lower_Bound, Upper_Bound); equal bounds return that bound. Both
   --  forms consume exactly two MWC Next steps. This deterministic operation
   --  is not cryptographic, does not alter OpenCV's thread-local default RNG,
   --  and composes with explicit Fill_Uniform, Fill_Normal, and Shuffle calls.
   --  @param Generator The generator to advance.
   --  @param Lower_Bound Finite inclusive lower bound.
   --  @param Upper_Bound Finite upper bound, not less than Lower_Bound; it is
   --  excluded from the result unless equal to Lower_Bound.
   --  @param Value The drawn value.
   --  @exception OpenCV_Error Raised when a bound is not finite or the
   --  bounds are not ordered.
   procedure Uniform_Random
     (Generator   : in out Random_Number_Generator;
      Lower_Bound : Long_Float;
      Upper_Bound : Long_Float;
      Value       : out Long_Float);

   --  Selects OpenCV's random or Arthur--Vassilvitskii k-means++ center
   --  initialization. Both choices consume OpenCV's global RNG. Cluster
   --  numbers, including their order in Centers, have no semantic meaning.
   --  @enum Random_Centers Initial centers are chosen randomly from the
   --  samples.
   --  @enum Plus_Plus_Centers Initial centers are chosen by the k-means++
   --  procedure.
   type K_Means_Initialization is (Random_Centers, Plus_Plus_Centers);

   --  OpenCV 4.10 k-means always uses both count and epsilon termination.
   --  Its effective iteration count is constrained to 2 .. 100, so this type
   --  prevents the silent clamping performed by the native implementation.
   type K_Means_Iteration_Count is range 2 .. 100;

   --  Termination criteria for K_Means. Iteration of an attempt ends when the
   --  iteration limit is reached or when the cluster centers move by less
   --  than Epsilon, whichever happens first.
   --  @field Maximum_Iterations Maximum number of iterations, in 2 .. 100.
   --  @field Epsilon Center-movement threshold that ends iteration early.
   type K_Means_Criteria is record
      Maximum_Iterations : K_Means_Iteration_Count := 100;
      Epsilon            : Long_Float := 1.0E-4;
   end record;

   --  Independently owned K_Means outputs. Labels is N x 1 Int32 C1, and
   --  Centers is Cluster_Count x feature-dimension Float32 C1. Compactness is
   --  sum_i ||sample_i - center[labels_i]||**2.
   --  @field Labels Zero-based cluster index assigned to each sample.
   --  @field Centers One cluster center per row.
   --  @field Compactness Sum of squared distances from each sample to its
   --  assigned center.
   type K_Means_Result is record
      Labels      : Mat;
      Centers     : Mat;
      Compactness : Long_Float;
   end record;

   --  Distance measure used by K_Nearest_Neighbors. Float32 inputs support
   --  the L1, L2, and squared L2 measures; UInt8 inputs additionally support
   --  both Hamming measures.
   --  @enum L1_Distance Sum of absolute coordinate differences.
   --  @enum L2_Distance Euclidean distance.
   --  @enum Squared_L2_Distance Squared Euclidean distance, without the
   --  square root.
   --  @enum Hamming_Distance Number of differing bits between UInt8 rows.
   --  @enum Hamming_2_Distance OpenCV's Hamming2 measure, which counts
   --  differing bits in 2-bit groups (a group counts once if either of its
   --  bits differs).
   type Batch_Distance_Kind is
     (L1_Distance,
      L2_Distance,
      Squared_L2_Distance,
      Hamming_Distance,
      Hamming_2_Distance);

   --  Independently owned K-nearest-neighbor outputs. Indices is Int32 C1
   --  and contains zero-based rows of the candidate Mat.
   --  @field Distances Distance from each query row to each of its nearest
   --  candidates, nearest first.
   --  @field Indices Zero-based candidate row of each corresponding entry of
   --  Distances.
   type Nearest_Neighbor_Result is record
      Distances : Mat;
      Indices   : Mat;
   end record;

   --  Independent polar outputs of Cart_To_Polar. Magnitude is
   --  sqrt (X**2 + Y**2). Angle is the corresponding OpenCV fast phase
   --  of (X, Y). Each component has normal Mat controlled ownership and
   --  is independent of the source Mats and of the other component.
   --  @field Magnitude Per-element vector length.
   --  @field Angle Per-element angle, in the unit requested from the
   --  producing operation.
   type Polar_Coordinates is record
      Magnitude : Mat;
      Angle     : Mat;
   end record;

   --  Independent Cartesian outputs of Polar_To_Cart. X is
   --  Magnitude * cos (Angle) and Y is Magnitude * sin (Angle).
   --  Each component has normal Mat controlled ownership and
   --  is independent of the source Mats and of the other component.
   --  @field X Per-element horizontal component.
   --  @field Y Per-element vertical component.
   type Cartesian_Coordinates is record
      X : Mat;
      Y : Mat;
   end record;

   --  Independently owned outputs of Covariance. Covariance is the
   --  normal feature covariance matrix. Mean is the corresponding
   --  per-feature average computed by OpenCV. Each field has normal
   --  Mat controlled ownership and is independent of Self and of the
   --  other field.
   --  @field Covariance The feature covariance matrix.
   --  @field Mean The per-feature average computed by OpenCV.
   type Covariance_Result is record
      Covariance : Mat;
      Mean       : Mat;
   end record;

   --  Independently owned outputs of Eigen_Decomposition and
   --  Non_Symmetric_Eigen_Decomposition. Eigenvalues is the N x 1
   --  column of eigenvalues. Eigenvectors is the N x N matrix of
   --  corresponding eigenvectors stored by row. Each field has normal
   --  Mat controlled ownership and is independent of Self and of the
   --  other field.
   --  @field Eigenvalues N x 1 column of eigenvalues.
   --  @field Eigenvectors N x N matrix whose rows are the eigenvectors that
   --  correspond to the eigenvalues.
   type Eigen_Decomposition_Result is record
      Eigenvalues  : Mat;
      Eigenvectors : Mat;
   end record;

   --  Independently owned outputs of Principal_Component_Analysis.
   --  Mean is the per-feature average. Eigenvalues is the K x 1
   --  column of principal variances in descending order.
   --  Eigenvectors stores one feature-space principal direction per
   --  row so that row i corresponds to eigenvalue i. Each field has
   --  normal Mat controlled ownership and is independent of Self and
   --  of the other fields.
   --  @field Mean Per-feature average.
   --  @field Eigenvalues K x 1 column of principal variances, in descending
   --  order.
   --  @field Eigenvectors One principal direction per row; row i
   --  corresponds to eigenvalue i.
   type Principal_Component_Analysis_Result is record
      Mean         : Mat;
      Eigenvalues  : Mat;
      Eigenvectors : Mat;
   end record;

   --  Independently owned outputs of Linear_Discriminant_Analysis.
   --  Eigenvalues is the K x 1 column of discriminant eigenvalues in
   --  descending order. Eigenvectors is D x K, with each discriminant
   --  direction stored in a column corresponding to the eigenvalue in
   --  that column. The fields have normal Mat controlled ownership and
   --  are independent of the input Mats and of each other.
   --  @field Eigenvalues K x 1 column of discriminant eigenvalues, in
   --  descending order.
   --  @field Eigenvectors D x K matrix; each column is the discriminant
   --  direction for the eigenvalue in the same column position.
   type Linear_Discriminant_Analysis_Result is record
      Eigenvalues  : Mat;
      Eigenvectors : Mat;
   end record;

   --  Independently owned outputs of Singular_Value_Decomposition.
   --  Singular_Values is the R x 1 column of nonnegative singular
   --  values in descending order, where R = min (Rows, Columns).
   --  U is the Rows x R matrix of left singular vectors stored as
   --  columns. V_Transpose is the R x Columns matrix of transposed
   --  right singular vectors. Each field has normal Mat controlled
   --  ownership and is independent of Self and of the other fields.
   --  @field Singular_Values R x 1 column of nonnegative singular values in
   --  descending order.
   --  @field U Rows x R matrix of left singular vectors stored as columns.
   --  @field V_Transpose R x Columns matrix of transposed right singular
   --  vectors.
   type Singular_Value_Decomposition_Result is record
      Singular_Values : Mat;
      U               : Mat;
      V_Transpose     : Mat;
   end record;

   --  Discriminated result of Invert. Inverse is present only when
   --  Invertible is True. Inverse has normal Mat controlled ownership
   --  and independent storage. A singular matrix yields Invertible
   --  False rather than a zero-filled placeholder inverse.
   --  @field Invertible True when the matrix was invertible and Inverse is
   --  present.
   --  @field Inverse The inverse matrix. Present only when Invertible is
   --  True.
   type Inversion_Result (Invertible : Boolean := False) is record
      case Invertible is
         when True =>
            Inverse : Mat;

         when False =>
            null;
      end case;
   end record;

   --  Discriminated result of Solve. Solution is present only when
   --  Solved is True. Solution has normal Mat controlled ownership
   --  and independent storage. A singular coefficient matrix yields
   --  Solved False rather than a zero-filled placeholder solution.
   --  @field Solved True when the system was solved and Solution is present.
   --  @field Solution The solution matrix. Present only when Solved is True.
   type Solve_Result (Solved : Boolean := False) is record
      case Solved is
         when True =>
            Solution : Mat;

         when False =>
            null;
      end case;
   end record;

   --  Status of a continuous linear-program maximization. Numerical_Loss means
   --  OpenCV lost a feasible solution through floating-point arithmetic.
   --  @enum Unique_Optimum The optimum exists and is unique.
   --  @enum Multiple_Optima Several optima exist; one arbitrary optimum is
   --  reported.
   --  @enum Unbounded The objective can grow without bound.
   --  @enum Infeasible No point satisfies the constraints.
   --  @enum Numerical_Loss OpenCV reported SOLVELP_LOST after losing a
   --  feasible solution through floating-point arithmetic.
   type Linear_Program_Status is
     (Unique_Optimum, Multiple_Optima, Unbounded, Infeasible, Numerical_Loss);

   --  Unique_Optimum and Multiple_Optima contain one independently owned
   --  solution. The remaining statuses deliberately expose no candidate Mat.
   --  @field Status Outcome of the optimization; selects the variant.
   --  @field Solution N x 1 Float64 optimum. Present only for
   --  Unique_Optimum and Multiple_Optima.
   type Linear_Program_Result (Status : Linear_Program_Status := Infeasible) is
   record
      case Status is
         when Unique_Optimum | Multiple_Optima =>
            Solution : Mat;

         when Unbounded | Infeasible | Numerical_Loss =>
            null;
      end case;
   end record;

   --  Solves the least-squares problem A * X ~= B using OpenCV 4.10
   --  cv::solve with DECOMP_SVD. Unlike Solve, which is the LU API for
   --  ordinary square systems, Self (A) may be square or overdetermined:
   --  M = A.Rows must be at least N = A.Columns. Underdetermined systems
   --  are rejected because OpenCV 4.10 cv::solve rejects M < N even for
   --  DECOMP_SVD. Right_Hand_Side (B) must have M rows and may have K >= 1
   --  columns. The independently owned Float32 or Float64 C1 result has
   --  shape N x K. A and B must be non-empty, single-channel, Float32 or
   --  Float64, and have the same depth. Rank-deficient A is accepted and
   --  receives a least-squares/pseudo-solution from OpenCV's SVD path and
   --  internal singular-value threshold. That solution is not uniquely
   --  specified: when infinitely many exact solutions exist, the particular
   --  vector may differ across architectures and OpenCV versions, and is
   --  not guaranteed to be the Moore-Penrose minimum-norm result. Inputs
   --  are unchanged, the result owns independent storage, and
   --  non-contiguous Regions are supported. Numerical rounding and SVD
   --  singular-value thresholding apply.
   --  @param Self The coefficient matrix A, with at least as many rows as
   --  columns.
   --  @param Right_Hand_Side The matrix B, with one row per row of Self.
   --  @return The N x K least-squares solution, in independent storage.
   --  @exception OpenCV_Error Raised when an operand violates the stated
   --  shape, depth or channel requirements or OpenCV reports a failure.
   function Solve_Least_Squares (Self : Mat; Right_Hand_Side : Mat) return Mat;

   --  Solves a continuous linear program using OpenCV 4.10 simplex: maximize
   --  c * x subject to A * x <= b and x >= 0. Objective is a non-empty C1
   --  Float32 or Float64 1 x N or N x 1 vector (N >= 1). Constraints is a
   --  non-empty C1 Float32 or Float64 M x (N + 1) Mat (M >= 1), with A in its
   --  first N columns and b in its last column. Input depths may differ, but
   --  every coefficient must be finite. Constraint_Tolerance is finite and
   --  nonnegative. On OpenCV 4.8+ it is passed as constr_eps. OpenCV 4.6
   --  accepts only 0.0 and the 1.0E-12 default; any other tolerance raises
   --  OpenCV_Error. Numerical_Loss is produced only when the linked OpenCV
   --  reports SOLVELP_LOST. Unique_Optimum and Multiple_Optima contain one
   --  arbitrary optimum as an independently owned N x 1 Float64 C1 Solution;
   --  Unbounded, Infeasible, and Numerical_Loss contain no Solution. Inputs
   --  are unchanged and non-contiguous Regions are supported. This is
   --  maximization only; a caller may negate c when its minimization fits
   --  this formulation.
   --  @param Objective The objective coefficient vector c.
   --  @param Constraints The matrix [A | b] of inequality constraints.
   --  @param Constraint_Tolerance Finite nonnegative constraint tolerance.
   --  @return The solver status, and the optimum when one is reported.
   --  @exception OpenCV_Error Raised when an operand or tolerance is invalid
   --  or OpenCV reports a failure.
   function Solve_Linear_Program
     (Objective            : Mat;
      Constraints          : Mat;
      Constraint_Tolerance : Long_Float := 1.0E-12)
      return Linear_Program_Result;

   --  OpenCV cv::solveCubic's reported real-root count: infinitely many
   --  roots, no real roots, or one, two, or three reported real roots.
   --  For repeated-root polynomials the count is not an architecture-
   --  independent number of mathematically distinct roots; OpenCV may
   --  return a duplicate repeated root as an extra reported value.
   --  @enum Infinitely_Many_Roots OpenCV reports infinitely many roots.
   --  @enum No_Real_Roots No real root is reported.
   --  @enum One_Real_Root One real root is reported.
   --  @enum Two_Real_Roots Two real roots are reported.
   --  @enum Three_Real_Roots Three real roots are reported.
   type Cubic_Root_Status is
     (Infinitely_Many_Roots,
      No_Real_Roots,
      One_Real_Root,
      Two_Real_Roots,
      Three_Real_Roots);

   --  Discriminated result of Solve_Cubic. Roots exists only when Status
   --  denotes a finite positive count of reported real roots. It is an
   --  independently owned 3 x 1 single-channel Mat with the coefficient
   --  depth; only its leading one, two, or three entries selected by Status
   --  are valid to inspect. OpenCV does not guarantee root ordering, and
   --  repeated-root cases may include duplicate values.
   --  @field Status Reported real-root count; selects the variant.
   --  @field Roots 3 x 1 Mat whose leading entries, as counted by Status,
   --  hold the reported roots. Present only for a finite positive count.
   type Cubic_Solution_Result (Status : Cubic_Root_Status := No_Real_Roots) is
   record
      case Status is
         when One_Real_Root | Two_Real_Roots | Three_Real_Roots =>
            Roots : Mat;

         when Infinitely_Many_Roots | No_Real_Roots =>
            null;
      end case;
   end record;

   --  Result of Solve_Polynomial. Roots is an independently owned effective-
   --  degree x 1 C2 Mat. Trailing high-order coefficients whose converted
   --  Float64 components' absolute-value sum is at most OpenCV 4.10's
   --  DBL_EPSILON are trimmed; OpenCV's original-degree padding rows are not
   --  exposed.
   --  @field Roots The roots as complex values in C2 elements, one per row.
   --  @field Maximum_Correction The value returned by cv::solvePoly: the
   --  largest difference between successive root estimates.
   type Polynomial_Solution_Result is record
      Roots              : Mat;
      Maximum_Correction : Long_Float;
   end record;

   --  A zero-based, owning sequence of Mats. An empty result has the null
   --  range 1 .. 0. Each element has normal Mat controlled ownership and
   --  shallow-copy assignment semantics.
   type Mat_Array is array (Natural range <>) of Mat;

   --  Selects where a Channel_Route obtains the value for its destination
   --  channel.
   --  @enum From_Source The value is copied from a channel of a source Mat.
   --  @enum Zero_Fill The destination channel is set to zero and no source
   --  channel is named.
   type Channel_Source_Kind is (From_Source, Zero_Fill);

   --  Source_Index and Destination_Index are the actual indices of Sources
   --  and Destinations, respectively. Channel indices are zero-based within
   --  their selected Mat. Zero_Fill writes zero to the destination channel.
   --  @field Source_Kind Selects the variant: From_Source or Zero_Fill.
   --  @field Destination_Index Index, within the destination collection, of
   --  the Mat that receives the value.
   --  @field Destination_Channel Zero-based channel of that destination Mat
   --  that receives the value.
   --  @field Source_Index Index, within the source collection, of the Mat
   --  that supplies the value. Present only when Source_Kind is From_Source.
   --  @field Source_Channel Zero-based channel of that source Mat that
   --  supplies the value. Present only when Source_Kind is From_Source.
   type Channel_Route (Source_Kind : Channel_Source_Kind := From_Source) is
   record
      Destination_Index   : Natural;
      Destination_Channel : Natural;
      case Source_Kind is
         when From_Source =>
            Source_Index   : Natural;
            Source_Channel : Natural;

         when Zero_Fill =>
            null;
      end case;
   end record;

   --  An ordered list of channel routes. Routes are applied in a single
   --  Mix_Channels call; no two routes may target the same destination
   --  channel.
   type Channel_Route_Array is array (Natural range <>) of Channel_Route;

   --  Creates a typed two-dimensional Mat with Rows rows and Columns columns.
   --  Element_Type fixes the depth and channel count of every element, so the
   --  storage is Rows * Columns elements of that type. A zero Rows or Columns
   --  produces a typed, zero-extent Mat that reports two dimensions; this is
   --  distinct from a default Mat header, which is untyped and reports none.
   --  The metadata of empty constructions is not promised to be identical
   --  across OpenCV releases. Element contents are not promised to be
   --  initialized.
   --  @param Rows Number of rows, at most the native signed 32-bit limit.
   --  @param Columns Number of columns, at most the native signed 32-bit
   --  limit.
   --  @param Element_Type Depth and channel count of each element.
   --  @return A new Mat that owns its own header and storage.
   function Create
     (Rows, Columns : Natural; Element_Type : Mat_Type) return Mat
   with Pre => Rows <= 2_147_483_647 and then Columns <= 2_147_483_647;

   --  Creates a typed two-dimensional Mat from a Size. Height gives the row
   --  count and Width the column count, so this is Create (Dimensions.Height,
   --  Dimensions.Width, Element_Type). A zero extent produces a typed,
   --  zero-extent Mat rather than a default header.
   --  @param Dimensions Width (columns) and Height (rows) of the Mat.
   --  @param Element_Type Depth and channel count of each element.
   --  @return A new Mat that owns its own header and storage.
   function Create (Dimensions : Size; Element_Type : Mat_Type) return Mat;

   --  Creates a genuine N-dimensional Mat. Dimension order follows Ada
   --  iteration order. At least two dimensions are required because OpenCV
   --  promotes a 1-D request to 2-D. Each extent must be nonzero, and the
   --  dimension count must not exceed OpenCV's 32-dimension limit. When the
   --  linked OpenCV has a smaller native Mat capacity (10 on OpenCV 5.0),
   --  longer shapes raise OpenCV_Error before native construction. The
   --  result is owned by the caller's Mat and shares storage only through
   --  later shallow copies.
   --  @param Shape Extent of each dimension, in native dimension order
   --  regardless of the array's index bounds.
   --  @param Element_Type Depth and channel count of each element.
   --  @return A new N-dimensional Mat that owns its own storage.
   function Create
     (Shape : Dimension_Array; Element_Type : Mat_Type) return Mat;

   --  Creates an independent square matrix with Diagonal on its main diagonal
   --  and zero in every off-diagonal element. Diagonal must be a row or column
   --  vector. The result preserves Diagonal's depth and channel count.
   --  @param Diagonal Row or column vector supplying the diagonal elements.
   --  @return A new square Mat with independent storage.
   --  @exception OpenCV_Error Raised when Diagonal is not a row or column
   --  vector or OpenCV reports a failure.
   function Diagonal_Matrix (Diagonal : Mat) return Mat;

   --  Creates a distinct 2-D Mat header sharing Self's storage with a new
   --  channel count and the same number of rows. Depth and the total scalar
   --  count (Rows * Columns * Channels) are preserved, so Columns is derived.
   --  No elements are copied. The reshape is rejected with OpenCV_Error when
   --  the new channel count does not preserve the scalar count with the
   --  existing row count, when the derived column count would exceed the
   --  signed 32-bit limit, or when native reshape rejects the layout.
   --  @param Self The Mat to reinterpret.
   --  @param Channels Channel count of the result.
   --  @return A new header sharing Self's storage.
   function Reshape (Self : Mat; Channels : Channel_Count) return Mat;

   --  Creates a distinct 2-D Mat header sharing Self's storage with a new
   --  channel count and row count. Depth and the total scalar count are
   --  preserved, so Columns is derived. No elements are copied. Raises
   --  OpenCV_Error when Channels and Rows do not preserve the total scalar
   --  count, when the derived column count would exceed the signed 32-bit
   --  limit, or when native reshape rejects the layout.
   --  @param Self The Mat to reinterpret.
   --  @param Channels Channel count of the result.
   --  @param Rows Positive row count of the result.
   --  @return A new header sharing Self's storage.
   function Reshape
     (Self : Mat; Channels : Channel_Count; Rows : Positive) return Mat;

   --  Creates a distinct Mat header sharing Self's storage for the requested
   --  shape. Iteration order of Shape maps directly to OpenCV dimensions
   --  regardless of Shape'First. The Shape-only overload preserves
   --  Self.Channels. The explicit Channels overload changes the channel count
   --  while reshaping. Depth is unchanged and no pixel storage is copied.
   --  Self must be nonempty and continuous. Shape'Length must be in 2 .. 32
   --  (and, on OpenCV 5.0, not exceed its native 10-dimension Mat capacity;
   --  longer shapes raise OpenCV_Error before native reshape),
   --  and every extent must be positive: a zero extent is invalid rather than
   --  an OpenCV preserve-dimension sentinel. The target scalar count,
   --  product (Shape) * requested Channels, must equal Self.Total *
   --  Self.Channels exactly.
   --  @param Self The nonempty, continuous Mat to reinterpret.
   --  @param Shape New extent of each dimension, in native dimension order.
   --  @return A new header sharing Self's storage, with Self's channel count.
   function Reshape (Self : Mat; Shape : Dimension_Array) return Mat;

   --  Shape-and-Channels form of the N-dimensional Reshape above: the result
   --  has the extents in Shape and the explicit channel count Channels,
   --  with the same preconditions and failure behavior.
   --  @param Self The nonempty, continuous Mat to reinterpret.
   --  @param Channels Channel count of the result.
   --  @param Shape New extent of each dimension, in native dimension order.
   --  @return A new header sharing Self's storage.
   function Reshape
     (Self : Mat; Channels : Channel_Count; Shape : Dimension_Array)
      return Mat;

   --  Creates a distinct single-column Mat header sharing Self's storage for
   --  the selected diagonal. Offset zero selects the main diagonal; positive
   --  offsets select diagonals above it (Offset 1 starts at row 0, column 1),
   --  and negative offsets select diagonals below it (Offset -1 starts at row
   --  1, column 0). Offset must select at least one element.
   --  @param Self The Mat whose diagonal is viewed.
   --  @param Offset Zero-based diagonal selector: zero for the main diagonal,
   --  positive above it, negative below it.
   --  @return A new single-column header sharing Self's storage.
   --  @exception OpenCV_Error Raised when Offset selects no element or
   --  OpenCV reports a failure.
   function Diagonal_View
     (Self : Mat; Offset : Point_Coordinate := 0) return Mat;

   --  Returns an independent deep copy of Self's elements. Unlike Ada
   --  assignment, which creates a distinct header over shared storage, the
   --  result owns separate storage, so later changes to either Mat do not
   --  affect the other. Cloning a Region or other view copies only the
   --  elements it selects. The metadata of a clone of an empty Mat follows
   --  the installed OpenCV release.
   --  @param Self The Mat to copy.
   --  @return A new Mat with independent storage.
   function Clone (Self : Mat) return Mat;

   --  Clusters Float32 samples with OpenCV 4.10 cv::kmeans. Samples must be a
   --  non-empty 2-D Mat with at least one channel. For Rows = 1, each column
   --  is a sample and the feature dimension is Channels. Otherwise, each row
   --  is a sample and the feature dimension is Columns * Channels. Thus N x D
   --  Float32 C1, N x 1 Float32 Cn, and 1 x N Float32 Cn are supported.
   --  Cluster_Count must not exceed the resulting sample count. Non-contiguous
   --  Regions are supported and Samples is unchanged. Epsilon must be finite
   --  and nonnegative. Initialization applies to every attempt. Attempts
   --  defaults to 3. KMEANS_USE_INITIAL_LABELS is provided by the distinct
   --  overload below.
   --  @param Samples The Float32 samples to cluster.
   --  @param Cluster_Count Number of clusters, at most the sample count.
   --  @param Criteria Termination criteria of each attempt.
   --  @param Attempts Number of independent attempts; the attempt with the
   --  lowest compactness is returned.
   --  @param Initialization Center initialization used by every attempt.
   --  @return Labels, centers and compactness, in independent storage.
   --  @exception OpenCV_Error Raised when an operand or criterion is invalid
   --  or OpenCV reports a failure.
   function K_Means
     (Samples        : Mat;
      Cluster_Count  : Positive;
      Criteria       : K_Means_Criteria :=
        (Maximum_Iterations => 100, Epsilon => 1.0E-4);
      Attempts       : Positive := 3;
      Initialization : K_Means_Initialization := Plus_Plus_Centers)
      return K_Means_Result;

   --  Refines an initial partition using OpenCV 4.10 cv::kmeans. Samples has
   --  the same contract as the no-label overload. Initial_Labels must be a
   --  non-empty Int32 C1 row or column vector containing exactly one
   --  zero-based
   --  label in 0 .. Cluster_Count - 1 for every logical sample. Labels may be
   --  N x 1 or 1 x N, where N follows Samples' sample-count rule. The input is
   --  unchanged, including when it is a non-contiguous Region. OpenCV repairs
   --  initially empty clusters. Attempt 1 starts from Initial_Labels. Attempts
   --  defaults to 1; when it exceeds 1, later attempts use
   --  Subsequent_Initialization and the returned result has the lowest
   --  compactness of all attempts, so its labels may be from a later attempt.
   --  Set_Random_Seed makes those later randomized attempts reproducible
   --  on the calling thread.
   --  @param Samples The Float32 samples to cluster.
   --  @param Cluster_Count Number of clusters, at most the sample count.
   --  @param Initial_Labels Initial zero-based cluster label of every sample.
   --  @param Criteria Termination criteria of each attempt.
   --  @param Attempts Number of attempts; the first starts from
   --  Initial_Labels.
   --  @param Subsequent_Initialization Center initialization used by
   --  attempts after the first.
   --  @return Labels, centers and compactness, in independent storage.
   --  @exception OpenCV_Error Raised when an operand or criterion is invalid
   --  or OpenCV reports a failure.
   function K_Means
     (Samples                   : Mat;
      Cluster_Count             : Positive;
      Initial_Labels            : Mat;
      Criteria                  : K_Means_Criteria :=
        (Maximum_Iterations => 100, Epsilon => 1.0E-4);
      Attempts                  : Positive := 1;
      Subsequent_Initialization : K_Means_Initialization := Plus_Plus_Centers)
      return K_Means_Result;

   --  Returns Neighbor_Count nearest candidate row-vectors for each query row.
   --  Queries and Candidates are non-empty, single-channel UInt8 or Float32
   --  Mats with equal column counts; their row counts may differ. Each row is
   --  one vector, so channels are not folded into its width. Neighbor_Count
   --  must not exceed Candidates.Rows. Float32 supports L1, L2, and squared
   --  L2; UInt8 additionally supports Hamming and Hamming2. Distances is
   --  Queries.Rows x Neighbor_Count C1: Float32 except Int32 for Hamming and
   --  Hamming2. Indices has the same shape and is Int32 C1. Rows are returned
   --  nearest-first; ordering of exact ties is OpenCV-defined. Results own
   --  independent storage, inputs are unchanged, and non-contiguous Regions
   --  are supported. Masks, update, crosscheck, and all-pairs mode are not
   --  exposed.
   --  @param Queries Rows to search for.
   --  @param Candidates Rows to search among.
   --  @param Neighbor_Count Number of neighbors returned per query row, at
   --  most Candidates.Rows.
   --  @param Kind Distance measure.
   --  @return Distances and zero-based candidate indices, in independent
   --  storage.
   --  @exception OpenCV_Error Raised when an operand or Kind is unsupported
   --  or OpenCV reports a failure.
   function K_Nearest_Neighbors
     (Queries        : Mat;
      Candidates     : Mat;
      Neighbor_Count : Positive;
      Kind           : Batch_Distance_Kind := L2_Distance)
      return Nearest_Neighbor_Result;

   --  Returns an independent Mat whose rows and columns are swapped. Element
   --  depth and channel count are preserved, including for multi-channel Mats.
   --  Empty Mats produce an empty result. Non-contiguous Regions are accepted.
   --  @param Self The Mat to transpose.
   --  @return A new Mat with independent storage.
   function Transpose (Self : Mat) return Mat;

   --  Returns an independent Mat with the same dimensions and element type as
   --  Self. Vertical reverses row order, Horizontal reverses column order,
   --  and Both_Axes reverses both. Empty Mats produce an empty result.
   --  Non-contiguous Regions are accepted.
   --  @param Self The Mat to flip.
   --  @param Kind Axis or axes to reverse.
   --  @return A new Mat with independent storage.
   function Flip (Self : Mat; Kind : Flip_Kind) return Mat;

   --  Returns an independent Mat with Self's rows, columns, depth, and
   --  channel count. Each_Row independently sorts the values across the
   --  columns of every row, left to right. Each_Column independently sorts
   --  the values down the rows of every column, top to bottom. Ascending is
   --  the default order and Each_Row is the default axis. Self must be
   --  single-channel. Supported depths are UInt8, Int8, UInt16, Int16,
   --  Int32, Float32, and Float64. Float16 is rejected because OpenCV 4.10
   --  has no sort implementation for it. Self is not modified. The result
   --  owns independent storage, including when Self is a non-contiguous
   --  Region. Continuity is not required. A default empty Mat and typed 0x0
   --  Mats of a supported depth produce an empty result that preserves the
   --  source shape, depth, and channel count. Typed empty Float16 is
   --  rejected. Equal values are sorted correctly, but their relative order
   --  is not guaranteed. NaN ordering is not part of the public contract.
   --  @param Self The single-channel Mat to sort.
   --  @param Axis Whether each row or each column is sorted independently.
   --  @param Order Ascending or descending order.
   --  @return A new Mat of Self's shape and element type holding the sorted
   --  values.
   --  @exception OpenCV_Error Raised for an unsupported depth, a
   --  multi-channel Mat, or an OpenCV failure.
   function Sort
     (Self  : Mat;
      Axis  : Sort_Axis := Each_Row;
      Order : Sort_Order := Ascending) return Mat;

   --  Returns an independent Int32 single-channel Mat of Self's rows and
   --  columns containing zero-based indices, not the sorted values. Each_Row
   --  independently orders the columns of every row and stores the original
   --  column indices. Each_Column independently orders the rows of every
   --  column and stores the original row indices. Ascending is the default
   --  order and Each_Row is the default axis. Self is not modified. Self must
   --  be single-channel. Supported source depths are UInt8, Int8, UInt16,
   --  Int16, Int32, Float32, and Float64. Float16 is rejected because
   --  OpenCV 4.10 has no sortIdx implementation for it. Continuity is not
   --  required. The result owns independent storage, including when Self is a
   --  non-contiguous Region; Region indices are relative to that Region
   --  rather than to its parent. Equal values produce a valid permutation
   --  that would sort those values, but their relative order is not stable
   --  or otherwise guaranteed. NaN ordering is not part of the public
   --  contract. A default empty Mat and typed 0x0 Mats of a supported depth
   --  raise OpenCV_Error because OpenCV 4.10's sortIdx implementation asserts
   --  that source and destination data pointers differ, and empty Mats share
   --  a null data pointer. Typed empty Float16 is rejected before the ABI.
   --  @param Self The single-channel Mat to order.
   --  @param Axis Whether each row or each column is ordered independently.
   --  @param Order Ascending or descending order.
   --  @return A new Int32 Mat of zero-based indices into Self.
   --  @exception OpenCV_Error Raised for an unsupported depth, a
   --  multi-channel Mat, an empty Mat, or an OpenCV failure.
   function Sort_Indices
     (Self  : Mat;
      Axis  : Sort_Axis := Each_Row;
      Order : Sort_Order := Ascending) return Mat;

   --  Returns an independent Mat with a border of the requested thickness.
   --  Constant uses Value; other border kinds extrapolate source pixels.
   --  When Self is a Region, Isolated is false by default so OpenCV may use
   --  pixels from its parent Mat. Isolated true restricts extrapolation to the
   --  Region boundaries. Empty Mats produce an empty result when every border
   --  is zero.
   --  @param Self The source Mat.
   --  @param Top Rows added above Self.
   --  @param Bottom Rows added below Self.
   --  @param Left Columns added left of Self.
   --  @param Right Columns added right of Self.
   --  @param Kind Border extrapolation mode.
   --  @param Value Border color used by Constant_Border.
   --  @param Isolated When True, extrapolation never reads outside Self's
   --  Region boundaries.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV rejects the operands.
   function Copy_Make_Border
     (Self     : Mat;
      Top      : Natural;
      Bottom   : Natural;
      Left     : Natural;
      Right    : Natural;
      Kind     : Border_Kind;
      Value    : Scalar := (others => 0.0);
      Isolated : Boolean := False) return Mat;

   --  Maps a zero-based one-dimensional Position to a source coordinate for a
   --  source Length. Length must be positive. In-range coordinates map to
   --  themselves. Replicate clamps, Reflect repeats the edge, Reflect_101
   --  does not repeat the edge, and Wrap is periodic. An out-of-range
   --  Constant_Border coordinate has no donor and returns Uses_Constant True;
   --  OpenCV's -1 sentinel is not exposed. This computes only a coordinate;
   --  it neither reads a Mat nor copies pixels. Extreme coordinates that would
   --  overflow OpenCV 4.10 signed arithmetic raise OpenCV_Error.
   --  @param Position Zero-based coordinate, possibly outside 0 .. Length - 1.
   --  @param Length Positive extent of the source axis.
   --  @param Kind Border extrapolation mode.
   --  @return The zero-based donor coordinate, or Uses_Constant True when
   --  none exists.
   function Border_Interpolate
     (Position : Point_Coordinate; Length : Positive; Kind : Border_Kind)
      return Border_Interpolation_Result;

   --  Separates Self into one independent single-channel Mat per channel.
   --  Results use channel indices 0 .. Self.Channels - 1, preserve Self's
   --  depth and dimensions, and do not share pixel storage with Self. Empty
   --  Mats return an empty Mat_Array. Single-channel Mats return one deep
   --  copy.
   --  Non-contiguous Regions and all supported Mat depths are accepted.
   --  @param Self The Mat to separate.
   --  @return One new single-channel Mat per channel of Self.
   function Split (Self : Mat) return Mat_Array;

   --  Returns an independent single-channel Mat containing the zero-based
   --  Channel of Self. Channel must be in 0 .. Self.Channels - 1. The result
   --  preserves Self's depth and dimensions, and does not share pixel storage
   --  with Self. Non-contiguous Regions and all supported Mat depths are
   --  accepted. An empty Mat accepts channel 0 and returns an empty,
   --  single-channel UInt8 Mat, matching OpenCV semantics.
   --  @param Self The Mat to read.
   --  @param Channel Zero-based channel to extract.
   --  @return A new single-channel Mat with independent storage.
   --  @exception OpenCV_Error Raised when Channel is out of range.
   function Extract_Channel (Self : Mat; Channel : Natural) return Mat;

   --  Copies the single channel in Source into the zero-based Channel of Self.
   --  Source and Self must have identical dimensions and depth; Channel must
   --  be in 0 .. Self.Channels - 1. Self is modified in place, preserving its
   --  dimensions and element type. Non-contiguous Regions are accepted and
   --  retain normal shared-storage view semantics. Empty UInt8 single-channel
   --  Mats accept channel 0 as a no-op, matching OpenCV semantics.
   --  @param Self The Mat modified in place.
   --  @param Source The single-channel Mat to copy from.
   --  @param Channel Zero-based channel of Self that receives Source.
   --  @exception OpenCV_Error Raised when the dimensions or depths differ,
   --  Source is not single-channel, or Channel is out of range.
   procedure Insert_Channel
     (Self : in out Mat; Source : Mat; Channel : Natural);

   --  Copies or zero-fills the specified channels into preallocated
   --  Destinations. Mat indices in Routes directly index the supplied arrays;
   --  their lower bounds need not be zero. All source and destination Mats
   --  must have identical dimensions and depth. A destination channel may
   --  occur in at most one route. Routes are applied in array iteration order.
   --  An empty Routes array is a no-op.
   --  @param Sources Mats read by From_Source routes.
   --  @param Destinations Preallocated Mats whose channels are written.
   --  @param Routes Channel copies and zero fills to perform.
   --  @exception OpenCV_Error Raised when the Mats differ in dimensions or
   --  depth, an index is out of range, or two routes target the same
   --  destination channel.
   procedure Mix_Channels
     (Sources      : Mat_Array;
      Destinations : in out Mat_Array;
      Routes       : Channel_Route_Array);

   --  Concatenates the channels of every non-empty input Mat, in array
   --  iteration order, into an independent Mat. Inputs may themselves be
   --  multi-channel, but must have identical dimensions and depth. The input
   --  array must not be empty and the total channel count must not exceed 512.
   --  @param Channels The Mats whose channels are concatenated.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when Channels is empty, the Mats differ
   --  in dimensions or depth, or the channel total exceeds 512.
   function Merge (Channels : Mat_Array) return Mat;

   --  Copies Self into Destination, allocating or reallocating Destination to
   --  Self's shape and element type when necessary. Destination may be a
   --  compatible view. Exact self-copy is supported; partially overlapping
   --  source and destination storage is not supported by OpenCV. Compatible
   --  Destination storage is reused, including through a Region that shares
   --  its parent; a mismatched Destination is reallocated and may detach
   --  from any parent. An empty Self follows the installed OpenCV release. A
   --  failed native copy is not promised to leave Destination unchanged.
   --  @param Self The source Mat.
   --  @param Destination The caller-owned Mat that receives the elements.
   procedure Copy_To (Self : Mat; Destination : in out Mat);

   --  Copies elements selected by Mask into Destination. Mask uses the common
   --  mask contract (UInt8, one channel, same shape as Self). Any nonzero mask
   --  value selects the complete element, including every channel. Unselected
   --  elements retain their values in a compatible Destination; if Destination
   --  is allocated or reallocated, they are initialized to zero. A Mask that
   --  violates the contract raises OpenCV_Error before the native copy. A
   --  failed native copy is not promised to leave Destination unchanged.
   --  @param Self The source Mat.
   --  @param Destination The caller-owned Mat that receives selected elements.
   --  @param Mask UInt8 single-channel Mat with Self's shape; nonzero entries
   --  select elements to copy.
   procedure Copy_To (Self : Mat; Destination : in out Mat; Mask : Mat);

   --  Converts Self to the requested depth into a new Mat, computing the
   --  native saturating Scale * Self + Offset for every element. Nonempty
   --  results preserve the source shape and channel count and own independent
   --  storage. Because the result is new, source/destination aliasing does
   --  not apply. Empty metadata follows OpenCV.
   --  @param Self The source Mat.
   --  @param Depth Depth of the result.
   --  @param Scale Factor applied to each source value before Offset.
   --  @param Offset Value added after scaling.
   --  @return A new Mat of the requested depth.
   function Convert_To
     (Self   : Mat;
      Depth  : Depth_Type;
      Scale  : Long_Float := 1.0;
      Offset : Long_Float := 0.0) return Mat;

   --  Reuses a compatible destination's storage, including parent sharing
   --  through a Region; native reallocation may detach incompatible Regions.
   --  Nonempty results preserve source shape/channels and use the native
   --  saturating Scale * Self + Offset conversion. Exact self is supported;
   --  arbitrary partial overlap is not. Temporary external/selected views
   --  are allowed as sources, but rejected as destinations. Empty metadata
   --  follows OpenCV. Exceptions after native conversion starts need not
   --  leave Destination unchanged.
   --  @param Self The source Mat.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @param Depth Depth of the converted elements.
   --  @param Scale Factor applied to each source value before Offset.
   --  @param Offset Value added after scaling.
   procedure Convert_To
     (Self        : Mat;
      Destination : in out Mat;
      Depth       : Depth_Type;
      Scale       : Long_Float := 1.0;
      Offset      : Long_Float := 0.0);
   --  Returns an independent UInt8 Mat with Self's shape and channel count.
   --  Each channel is converted as saturate_cast<UInt8>
   --  (abs (Self * Scale + Offset)).
   --  @param Self The source Mat.
   --  @param Scale Factor applied to each source value.
   --  @param Offset Value added after scaling.
   --  @return A new UInt8 Mat with independent storage.
   function Convert_Scale_Abs
     (Self : Mat; Scale : Long_Float := 1.0; Offset : Long_Float := 0.0)
      return Mat;

   --  Applies a 256-entry lookup table to an 8-bit source. Self must have
   --  UInt8 or Int8 depth. Table must contain exactly 256 continuous
   --  elements and either one channel or the same channel count as Self.
   --  The result has Self's shape and channel count and Table's depth, and
   --  owns independent storage. Int8 sources are indexed by their stored
   --  8-bit pattern (0 .. 255), matching OpenCV 4.10.0. Float16 tables and
   --  16-bit sources are not supported. A 0x0 8-bit source produces a 0x0
   --  result; a default empty Mat is rejected by OpenCV.
   --  @param Self The UInt8 or Int8 source Mat.
   --  @param Table The 256-entry lookup table.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported depth, a table of
   --  the wrong size, continuity or channel count, or an empty source.
   function Apply_LUT (Self : Mat; Table : Mat) return Mat;

   --  Returns an independent Mat with Self's shape, depth, and channel count.
   --  Self must be Float32 or Float64. Each channel is processed independently
   --  by cv::sqrt. On OpenCV 4.10 the 0.5-power HAL path uses std::sqrt, so
   --  negative finite values and -Infinity become NaN, +Infinity stays
   --  +Infinity, and a typed 0x0 source stays empty. A default empty Mat and
   --  non-floating depths are rejected.
   --  @param Self The Float32 or Float64 source.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, or an OpenCV failure.
   function Sqrt (Self : Mat) return Mat;

   --  Destination form of Sqrt, with the same source policy and numerical
   --  behavior. The result is written to the actual native Destination:
   --  compatible whole or Region storage is reused (including through a
   --  Region that shares its parent) and mismatched storage is reallocated
   --  and may detach. Exact and shallow source aliases are native; partial
   --  overlap is unsupported. A temporary view cannot be a Destination,
   --  although temporary sources are valid. A failure after the native call
   --  begins is not promised to leave Destination unchanged.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, a temporary-view Destination, or an OpenCV
   --  failure.
   procedure Sqrt (Self : Mat; Destination : in out Mat);

   --  Returns an independent Mat with Self's shape, depth, and channel count.
   --  Self must be Float32 or Float64. Each channel is processed independently
   --  by cv::exp. On OpenCV 4.10 the implementation is approximate (about
   --  7e-6 relative error for Float32 and less than 1e-10 for Float64) and
   --  may convert denormalized outputs to zero. Special values such as NaN
   --  and Infinity are not handled. A typed 0x0 source stays empty. A default
   --  empty Mat and non-floating depths are rejected.
   --  @param Self The Float32 or Float64 source.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, or an OpenCV failure.
   function Exp (Self : Mat) return Mat;

   --  Destination form of Exp, with the same source policy and numerical
   --  behavior. Destination storage follows the rules of the Sqrt
   --  Destination form: compatible storage is reused, mismatched storage may
   --  detach, partial overlap is unsupported, a temporary view cannot be a
   --  Destination, and a failure after the native call begins is not
   --  promised to leave Destination unchanged.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, a temporary-view Destination, or an OpenCV
   --  failure.
   procedure Exp (Self : Mat; Destination : in out Mat);

   --  Returns an independent Mat with Self's shape, depth, and channel count.
   --  Self must be Float32 or Float64. Each channel is processed independently
   --  by cv::log (natural logarithm). On OpenCV 4.10 the implementation is
   --  approximate. Output on zero, negative, and special values such as NaN
   --  and Infinity is undefined. A typed 0x0 source stays empty. A default
   --  empty Mat and non-floating depths are rejected.
   --  @param Self The Float32 or Float64 source.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, or an OpenCV failure.
   function Log (Self : Mat) return Mat;

   --  Destination form of Log, with the same source policy and numerical
   --  behavior. Destination storage follows the rules of the Sqrt
   --  Destination form: compatible storage is reused, mismatched storage may
   --  detach, partial overlap is unsupported, a temporary view cannot be a
   --  Destination, and a failure after the native call begins is not
   --  promised to leave Destination unchanged.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for a default empty Mat, a
   --  non-floating depth, a temporary-view Destination, or an OpenCV
   --  failure.
   procedure Log (Self : Mat; Destination : in out Mat);

   --  Returns an independent Mat with Self's shape, depth, and channel count.
   --  Each channel is processed independently by cv::pow. When Power is an
   --  integer, source signs are preserved (src(I) ** Power). When Power is
   --  not an integer, OpenCV documents abs (src(I)) ** Power and Self must
   --  be Float32 or Float64; on OpenCV 4.10 the general non-integer CPU path
   --  yields NaN for negative finite values. Nonnegative integer Power also
   --  supports UInt8, Int8, UInt16, Int16, and Int32. UInt8, Int8, UInt16,
   --  and Int16 results saturate; Int32 overflow is not saturated. Negative
   --  integer powers are accepted only for Float32 and Float64. Powers 0, 1,
   --  and 2 use specialized integer paths. Powers 0.5 and -0.5 use specialized
   --  square-root and inverse-square-root paths and require Float32 or
   --  Float64. Float16 is not supported. Special values such as NaN and
   --  Infinity are not handled. A typed 0x0 source stays empty. A default
   --  empty Mat is accepted for a nonnegative integer Power and rejected
   --  otherwise.
   --  @param Self The source Mat.
   --  @param Power The exponent.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when Self's depth or the default-empty
   --  state is unsupported for Power, or OpenCV reports a failure.
   function Pow (Self : Mat; Power : Long_Float) return Mat;

   --  Destination form of Pow, with the same source policy and numerical
   --  behavior. The result is written to the actual native Destination:
   --  compatible whole or Region storage is reused and mismatched storage is
   --  reallocated and may detach. N-dimensional Mats are supported. Exact and
   --  shallow source aliases are native; partial overlap is unsupported. A
   --  temporary view cannot be a Destination, although temporary sources are
   --  valid. A failure after the native call begins is not promised to leave
   --  Destination unchanged.
   --  @param Self The source Mat.
   --  @param Power The exponent.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised when Self's depth or the default-empty
   --  state is unsupported for Power, a temporary-view Destination is
   --  supplied, or OpenCV reports a failure.
   procedure Pow (Self : Mat; Power : Long_Float; Destination : in out Mat);

   --  Returns an independent Mat with X's shape, depth, and channel count.
   --  X and Y must be Float32 or Float64 with identical dimensions, depth,
   --  and channel count. Each channel is processed independently by
   --  cv::magnitude as sqrt (X**2 + Y**2). A typed 0x0 pair stays empty. A
   --  default empty Mat, mismatched shape or type, and non-floating depths
   --  including Float16 are rejected.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vector component matching X in dimensions, depth, and
   --  channel count.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, or an OpenCV failure.
   function Magnitude (X, Y : Mat) return Mat;

   --  Destination form of Magnitude, with the same source policy. The result
   --  is written directly into compatible whole or Region storage;
   --  mismatched storage is reallocated and may detach. Exact and shallow
   --  source aliases are supported, partial overlap is not. A temporary view
   --  cannot be a Destination. A failure after the native call begins is not
   --  promised to leave Destination unchanged.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vector component matching X in dimensions, depth, and
   --  channel count.
   --  @param Destination The caller-owned Mat that receives the magnitudes.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, a temporary-view Destination, or an
   --  OpenCV failure.
   procedure Magnitude (X, Y : Mat; Destination : in out Mat);

   --  Returns an independent Mat with X's shape, depth, and channel count.
   --  X and Y are the Cartesian components of 2D vectors. They must be
   --  Float32 or Float64 with identical dimensions, depth, and channel
   --  count. Each channel is processed independently by cv::phase as
   --  atan2 (Y, X). Units selects radians by default or degrees. OpenCV
   --  documents about 0.3 degrees of angle estimation accuracy; the native
   --  approximation does not guarantee a strict half-open full-turn range.
   --  When both X and Y are zero, the angle is 0.
   --  A typed 0x0 pair stays empty. A default empty Mat, mismatched
   --  shape or type, and non-floating depths including Float16 are
   --  rejected.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @return A new Mat of angles with independent storage.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, or an OpenCV failure.
   function Phase (X, Y : Mat; Units : Angle_Unit := Radians) return Mat;

   --  Destination form of Phase, using the same native fast-angle
   --  computation and the destination, alias, and temporary-view rules of
   --  the Magnitude Destination form.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Destination The caller-owned Mat that receives the angles.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, a temporary-view Destination, or an
   --  OpenCV failure.
   procedure Phase
     (X, Y : Mat; Destination : in out Mat; Units : Angle_Unit := Radians);

   --  Returns independently owned Magnitude and Angle Mats with X's shape,
   --  depth, and channel count. X and Y are the Cartesian components of 2D
   --  vectors. They must be Float32 or Float64 with identical dimensions,
   --  depth, and channel count. Each channel is processed independently by
   --  a single cv::cartToPolar call. Magnitude is sqrt (X**2 + Y**2). Angle
   --  uses the same OpenCV fast-angle semantics as Phase. Units selects
   --  radians by default or degrees. OpenCV documents angles measured from
   --  0 to 2*Pi or 0 to 360 degrees, with about 0.3 degrees of angle
   --  estimation accuracy; the approximation does not guarantee a
   --  mathematically strict half-open range. When both X and Y are zero,
   --  Magnitude and Angle are 0. A typed 0x0 pair stays empty. A default
   --  empty Mat, mismatched shape or type, and non-floating depths
   --  including Float16 are rejected.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @return Independently owned magnitude and angle Mats.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, or an OpenCV failure.
   function Cart_To_Polar
     (X, Y : Mat; Units : Angle_Unit := Radians) return Polar_Coordinates;

   --  Writes both caller-owned destinations in one native transform.
   --  Compatible whole or Region storage is reused; each mismatched output
   --  detaches independently. Outputs must be distinct native objects and
   --  must not be exactly either source. Distinct headers with overlapping
   --  storage are unsupported. Temporary Mat views cannot be outputs.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Magnitude The caller-owned Mat that receives the magnitudes.
   --  @param Angle The caller-owned Mat that receives the angles.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Mat, mismatched
   --  operands, an unsupported depth, an unsupported output alias or
   --  temporary view, or an OpenCV failure.
   procedure Cart_To_Polar
     (X, Y             : Mat;
      Magnitude, Angle : in out Mat;
      Units            : Angle_Unit := Radians);

   --  Groups the two caller-owned destinations. Each field independently owns
   --  its Mat header; the record is not a transactional update and does not
   --  change native alias rules. Compatible storage is reused and mismatched
   --  storage may detach or reallocate independently. Validation and the
   --  native transform are the same as the individual-destination procedure.
   --  @param X Cartesian X component. Float32 or Float64, matching Y.
   --  @param Y Cartesian Y component. Same dimensions, depth, and channels
   --  as X.
   --  @param Destination Caller-owned Magnitude and Angle fields. Each field
   --  independently reuses compatible storage or detaches when mismatched.
   --  @param Units Angle unit: radians by default, or degrees.
   procedure Cart_To_Polar
     (X, Y        : Mat;
      Destination : in out Polar_Coordinates;
      Units       : Angle_Unit := Radians);

   --  Returns independently owned X and Y Mats with Angle's shape, depth,
   --  and channel count. Angle is the authoritative operand and must be
   --  Float32 or Float64. When Magnitude is non-empty, it must have the
   --  same dimensions, depth, and channel count as Angle. An empty
   --  Magnitude, or the one-argument overload, means unit magnitude for
   --  every Angle element. Each channel is processed independently by a
   --  single cv::polarToCart call. X is Magnitude * cos (Angle) and Y is
   --  Magnitude * sin (Angle). Units selects radians by default or
   --  degrees. OpenCV documents relative coordinate accuracy of about
   --  1e-6. There is no required Angle range. A typed 0x0 Angle stays
   --  empty. A default empty Angle is rejected. Float16 and other
   --  non-floating Angle depths are rejected.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty to
   --  mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @return Independently owned X and Y Mats.
   --  @exception OpenCV_Error Raised for a default empty Angle, mismatched
   --  operands, an unsupported depth, or an OpenCV failure.
   function Polar_To_Cart
     (Magnitude, Angle : Mat; Units : Angle_Unit := Radians)
      return Cartesian_Coordinates;

   --  Angle-only form of Polar_To_Cart: every Angle element has unit
   --  magnitude, so the results are the cosine and sine of Angle. Operand
   --  rules and failure behavior match the two-operand function.
   --  @param Angle Polar angle. Float32 or Float64.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @return Independently owned X and Y Mats.
   --  @exception OpenCV_Error Raised for a default empty Angle, an
   --  unsupported depth, or an OpenCV failure.
   function Polar_To_Cart
     (Angle : Mat; Units : Angle_Unit := Radians) return Cartesian_Coordinates;

   --  Writes the Cartesian components into caller-owned X and Y in one
   --  native transform. Compatible whole or Region storage is reused; each
   --  mismatched output detaches independently. Outputs must be distinct
   --  native objects and must not be exactly any source. Distinct headers
   --  with overlapping storage are unsupported. Temporary Mat views cannot
   --  be outputs. An empty Magnitude means unit magnitude.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty to
   --  mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param X The caller-owned Mat that receives Magnitude * cos (Angle).
   --  @param Y The caller-owned Mat that receives Magnitude * sin (Angle).
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Angle, mismatched
   --  operands, an unsupported depth, an unsupported output alias or
   --  temporary view, or an OpenCV failure.
   procedure Polar_To_Cart
     (Magnitude, Angle : Mat;
      X, Y             : in out Mat;
      Units            : Angle_Unit := Radians);

   --  Angle-only destination form of Polar_To_Cart: every Angle element has
   --  unit magnitude. Destination, alias, and temporary-view rules match the
   --  two-operand procedure.
   --  @param Angle Polar angle. Float32 or Float64.
   --  @param X The caller-owned Mat that receives cos (Angle).
   --  @param Y The caller-owned Mat that receives sin (Angle).
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Angle, an
   --  unsupported depth, an unsupported output alias or temporary view, or
   --  an OpenCV failure.
   procedure Polar_To_Cart
     (Angle : Mat; X, Y : in out Mat; Units : Angle_Unit := Radians);

   --  Groups the two caller-owned destinations. Each field independently owns
   --  its Mat header; the record is not a transactional update and does not
   --  change native alias rules. Compatible storage is reused and mismatched
   --  storage may detach or reallocate independently. Empty Magnitude, and
   --  the angle-only overload, still mean unit magnitude. Validation and the
   --  native transform are the same as the individual-destination procedures.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty
   --  to mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Destination Caller-owned X and Y fields. Each field independently
   --  reuses compatible storage or detaches when mismatched.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   procedure Polar_To_Cart
     (Magnitude, Angle : Mat;
      Destination      : in out Cartesian_Coordinates;
      Units            : Angle_Unit := Radians);
   --  Angle-only record destination. Empty magnitude is implied, so every
   --  Angle element has unit magnitude. Each Destination field independently
   --  owns its Mat header; the record is not a transactional update.
   --  Compatible whole or Region storage is reused; mismatched storage may
   --  detach. The pre-4.10 Float64 correction writes compatible Region
   --  storage, and empty-magnitude N-D Angle support follows the function.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Destination Caller-owned X and Y fields written as cosine and
   --  sine of Angle. Compatible storage is reused independently per field.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   procedure Polar_To_Cart
     (Angle       : Mat;
      Destination : in out Cartesian_Coordinates;
      Units       : Angle_Unit := Radians);
   --  Returns an independently owned full-complex Discrete Fourier
   --  Transform of Self using OpenCV 4.10 cv::dft. This is not DCT,
   --  a packed CCS spectrum, a batched DFT_ROWS transform, or an
   --  in-place procedure. Self must be a non-empty 2-D Float32 or
   --  Float64 Mat with 1 or 2 channels. A 1 x N row, an N x 1
   --  column, and an ordinary M x N matrix are all transformed as
   --  2-D arrays of those dimensions; OpenCV's 1-D path is used
   --  only when the shape itself is a single row or column.
   --  Single-channel real input uses DFT_COMPLEX_OUTPUT so the
   --  result is an explicit C2 spectrum of the same rows, columns,
   --  and floating depth: channel 0 is the real part and channel 1
   --  is the imaginary part. Packed CCS output is not part of this
   --  API. Two-channel input is already complex and is transformed
   --  in place of that representation, returning C2 of the same
   --  shape and depth. Other channel counts are rejected rather
   --  than reinterpreted as complex. The forward transform is
   --  unscaled. Continuity is not required; non-contiguous Regions
   --  are supported. Self is unchanged. The result owns independent
   --  storage. Very large matrices whose dimensions would cause
   --  OpenCV 4.10's internal signed DFT arithmetic to overflow are
   --  rejected with OpenCV_Error. Rows * Columns must fit signed
   --  32-bit, and each transformed dimension must fit that same
   --  limit after multiplication by the full-complex element size
   --  (8 bytes for Float32, 16 bytes for Float64).
   --  @param Self The real or complex spatial-domain Mat.
   --  @return A new C2 Mat holding the unscaled complex spectrum.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Discrete_Fourier_Transform (Self : Mat) return Mat;

   --  Returns an independently owned normalized inverse Discrete
   --  Fourier Transform of a full-complex spectrum using OpenCV
   --  4.10 cv::dft with DFT_INVERSE and DFT_SCALE. Self must be a
   --  non-empty 2-D Float32 or Float64 Mat with exactly 2 channels.
   --  Channel 0 is the real part and channel 1 is the imaginary
   --  part. The result has Self's rows, columns, depth, and 2
   --  channels. DFT_SCALE is always applied so that
   --  Inverse_Discrete_Fourier_Transform
   --  (Discrete_Fourier_Transform (Source)) approximately
   --  reproduces Source rather than Source * Rows * Columns.
   --  OpenCV's unscaled inverse is not the default Ada behavior.
   --  Continuity is not required; non-contiguous Regions are
   --  supported. Self is unchanged. The result owns independent
   --  storage. Very large matrices whose dimensions would cause
   --  OpenCV 4.10's internal signed DFT arithmetic to overflow are
   --  rejected with OpenCV_Error. Rows * Columns must fit signed
   --  32-bit, and each transformed dimension must fit that same
   --  limit after multiplication by the full-complex element size
   --  (8 bytes for Float32, 16 bytes for Float64).
   --  @param Self The full-complex C2 spectrum.
   --  @return A new C2 Mat holding the normalized inverse transform.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Inverse_Discrete_Fourier_Transform (Self : Mat) return Mat;

   --  Returns an independently owned real inverse Discrete Fourier
   --  Transform of a full-complex spectrum using OpenCV 4.10
   --  cv::dft with DFT_INVERSE, DFT_SCALE, and DFT_REAL_OUTPUT.
   --  Self must be a non-empty 2-D Float32 or Float64 Mat with
   --  exactly 2 channels. The result has Self's rows, columns, and
   --  depth, and 1 channel. This is the natural inverse of
   --  Discrete_Fourier_Transform when the original source was real.
   --  DFT_REAL_OUTPUT assumes the input complex spectrum has the
   --  conjugate symmetry required for a real spatial-domain result.
   --  OpenCV 4.10 does not verify that symmetry, and this binding
   --  does not invent a numerical tolerance. A spectrum obtained
   --  from a real forward transform satisfies the assumption. A
   --  malformed arbitrary C2 input is a caller-precondition
   --  violation rather than a rejected argument, analogous to the
   --  symmetric-eigen policy. Continuity is not required;
   --  non-contiguous Regions are supported. Self is unchanged. The
   --  result owns independent storage. Very large matrices whose
   --  dimensions would cause OpenCV 4.10's internal signed DFT
   --  arithmetic to overflow are rejected with OpenCV_Error. Rows
   --  * Columns must fit signed 32-bit, and each transformed
   --  dimension must fit that same limit after multiplication by
   --  the full-complex element size (8 bytes for Float32, 16 bytes
   --  for Float64).
   --  @param Self The full-complex C2 spectrum, assumed conjugate-symmetric.
   --  @return A new C1 Mat holding the normalized real inverse transform.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Inverse_Real_Discrete_Fourier_Transform (Self : Mat) return Mat;

   --  Returns OpenCV's native packed CCS representation of the unscaled
   --  forward DFT. Self must be a non-empty Float32 or Float64 C1 Mat. A
   --  1 x N row, an N x 1 column, and an ordinary M x N Mat are supported,
   --  including odd positive dimensions and non-contiguous Regions. The
   --  result is an opaque spectral Mat with Self's rows, columns, depth, and
   --  one channel; callers need not interpret its OpenCV-defined physical
   --  layout to pass it to Inverse_Packed_Discrete_Fourier_Transform. Self is
   --  unchanged and the result owns independent storage. The same DFT
   --  signed-arithmetic safety limits documented above apply.
   --  @param Self The real C1 spatial-domain Mat.
   --  @return A new C1 Mat holding the packed CCS spectrum.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Packed_Discrete_Fourier_Transform (Self : Mat) return Mat;

   --  Returns the normalized real C1 inverse of an OpenCV packed CCS Mat.
   --  Self must be a non-empty Float32 or Float64 C1 packed spectrum, normally
   --  produced by Packed_Discrete_Fourier_Transform. OpenCV cv::dft is called
   --  with DFT_INVERSE, DFT_SCALE, and DFT_REAL_OUTPUT. The result preserves
   --  rows, columns, and depth, owns independent storage, and approximately
   --  reproduces the original real source. Self is unchanged. The packed
   --  layout remains opaque and the same DFT arithmetic-safety limits apply.
   --  @param Self The packed CCS C1 spectrum.
   --  @return A new C1 Mat holding the normalized real inverse.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Inverse_Packed_Discrete_Fourier_Transform (Self : Mat) return Mat;

   --  Returns a full-complex DFT in which every row is transformed as an
   --  independent 1-D signal using cv::dft with DFT_ROWS. Self must satisfy
   --  the same depth, channel, non-empty, and size requirements as
   --  Discrete_Fourier_Transform. Float32 or Float64 C1 input returns C2;
   --  C2 input remains C2. Rows and columns are preserved. Continuity is not
   --  required, Self is unchanged, and the result owns independent storage.
   --  @param Self The Float32 or Float64 C1 or C2 Mat whose rows are signals.
   --  @return A new C2 Mat holding one complex spectrum per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Discrete_Fourier_Transform_Rows (Self : Mat) return Mat;

   --  Returns the normalized row-wise inverse of a full-complex C2 spectrum
   --  using DFT_ROWS, DFT_INVERSE, and DFT_SCALE. Each row is inverted and
   --  scaled independently by its column count. The result remains C2 and
   --  preserves Self's rows, columns, and Float32 or Float64 depth.
   --  @param Self The full-complex C2 Mat whose rows are spectra.
   --  @return A new C2 Mat holding one normalized inverse per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, or an OpenCV failure.
   function Inverse_Discrete_Fourier_Transform_Rows (Self : Mat) return Mat;

   --  Returns the normalized C1 real row-wise inverse of a full-complex C2
   --  spectrum using DFT_ROWS, DFT_INVERSE, DFT_SCALE, and DFT_REAL_OUTPUT.
   --  Every row is independently inverted. As with the ordinary real inverse,
   --  each input row is expected to have conjugate symmetry. The result owns
   --  independent storage and preserves rows, columns, and floating depth.
   --  @param Self The full-complex C2 Mat whose rows are conjugate-symmetric
   --  spectra.
   --  @return A new C1 Mat holding one normalized real signal per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, or an OpenCV failure.
   function Inverse_Real_Discrete_Fourier_Transform_Rows
     (Self : Mat) return Mat;

   --  Returns one independently transformed packed CCS spectrum per row using
   --  DFT_ROWS without DFT_COMPLEX_OUTPUT. Self must be a non-empty, exactly
   --  2-D Float32 or Float64 C1 Mat. For an M x N Mat, rows are a batch
   --  dimension: the result contains M independent length-N transforms, not
   --  one 2-D transform. Rows, columns, depth, and the single channel are
   --  preserved; odd row counts and odd positive row lengths are supported.
   --  Continuity is not required, Self is unchanged, and the result owns
   --  independent storage. The same DFT arithmetic-safety limits apply.
   --  @param Self The real C1 Mat whose rows are signals.
   --  @return A new C1 Mat holding one packed CCS spectrum per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, a size beyond the stated limits, or an OpenCV failure.
   function Packed_Discrete_Fourier_Transform_Rows (Self : Mat) return Mat;

   --  Returns the normalized C1 real inverse of every packed CCS row using
   --  DFT_ROWS, DFT_INVERSE, DFT_SCALE, and DFT_REAL_OUTPUT. Self has the same
   --  structural and type requirements as
   --  Packed_Discrete_Fourier_Transform_Rows and is intended to contain packed
   --  row spectra such as those returned by that operation. The binding does
   --  not inspect CCS contents or numerical validity. Each row is
   --  reconstructed independently. Shape and depth are preserved, Self is
   --  unchanged, and the result owns independent storage.
   --  @param Self The C1 Mat whose rows are packed CCS spectra.
   --  @return A new C1 Mat holding one normalized real signal per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth or
   --  channel count, or an OpenCV failure.
   function Inverse_Packed_Discrete_Fourier_Transform_Rows
     (Self : Mat) return Mat;

   --  Returns an independently owned Discrete Cosine Transform of
   --  Self using OpenCV 4.10 cv::dct. This is not DFT, a packed CCS
   --  spectrum, a batched DCT_ROWS transform, or an in-place
   --  procedure. Self must be a non-empty 2-D Float32 or Float64 Mat
   --  with exactly one channel. OpenCV 4.10 treats 1 x 1 as an
   --  identity DCT. A 1 x N row or an N x 1 column with N > 1 is
   --  transformed as a 1-D vector and requires N even. An ordinary
   --  M x N matrix with M > 1 and N > 1 is transformed as 2-D and
   --  requires both M and N even. Odd transformed dimensions greater
   --  than one are rejected rather than padded. The result has Self's
   --  rows, columns, floating depth, and one channel. OpenCV's DCT
   --  uses its documented orthonormal cosine-transform convention, so
   --  Inverse_Discrete_Cosine_Transform
   --  (Discrete_Cosine_Transform (Source)) approximately reproduces
   --  Source without a caller scale factor. Continuity is not
   --  required; non-contiguous Regions are supported. Self is
   --  unchanged. The result owns independent storage. Very large
   --  matrices whose transformed dimensions would cause OpenCV
   --  4.10's internal signed DCT work-buffer arithmetic to overflow
   --  are rejected with OpenCV_Error. Each transformed dimension
   --  must fit signed 32-bit after multiplication by the complex
   --  element size used by the DCT DFT path (8 bytes for Float32,
   --  16 bytes for Float64).
   --  @param Self The real C1 Mat to transform.
   --  @return A new C1 Mat holding the DCT.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth, channel
   --  count or odd transformed dimension, a size beyond the stated limits,
   --  or an OpenCV failure.
   function Discrete_Cosine_Transform (Self : Mat) return Mat;

   --  Returns an independently owned inverse Discrete Cosine
   --  Transform of Self using OpenCV 4.10 cv::dct with DCT_INVERSE.
   --  Self must be a non-empty 2-D Float32 or Float64 Mat with
   --  exactly one channel and the same transform geometry as
   --  Discrete_Cosine_Transform, including the 1 x 1 identity case.
   --  The result has Self's rows, columns, floating depth, and one
   --  channel. Continuity is not required; non-contiguous Regions
   --  are supported. Self is unchanged. The result owns independent
   --  storage. Very large matrices whose transformed dimensions
   --  would cause OpenCV 4.10's internal signed DCT work-buffer
   --  arithmetic to overflow are rejected with OpenCV_Error.
   --  @param Self The C1 DCT coefficients to invert.
   --  @return A new C1 Mat holding the inverse DCT.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth, channel
   --  count or odd transformed dimension, a size beyond the stated limits,
   --  or an OpenCV failure.
   function Inverse_Discrete_Cosine_Transform (Self : Mat) return Mat;

   --  Returns an independently owned DCT in which every row is transformed
   --  as an independent 1-D signal using cv::dct with DCT_ROWS. Self must be
   --  a non-empty 2-D Float32 or Float64 Mat with exactly one channel. The
   --  transformed row length (Columns) must be 1 or even; Rows is only the
   --  number of independent signals and may be odd. Rows, columns, depth, and
   --  channel count are preserved. Non-contiguous Regions are supported and
   --  Self is unchanged.
   --  @param Self The real C1 Mat whose rows are signals.
   --  @return A new C1 Mat holding one DCT per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth,
   --  channel count or odd row length, or an OpenCV failure.
   function Discrete_Cosine_Transform_Rows (Self : Mat) return Mat;

   --  Returns the independently owned row-wise inverse DCT using DCT_ROWS
   --  and DCT_INVERSE. Each row is independently inverse-transformed using
   --  OpenCV's orthonormal convention, so no additional scaling is applied.
   --  Input requirements and result metadata match
   --  Discrete_Cosine_Transform_Rows.
   --  @param Self The C1 Mat whose rows are DCT coefficients.
   --  @return A new C1 Mat holding one inverse DCT per row.
   --  @exception OpenCV_Error Raised for an unsupported shape, depth,
   --  channel count or odd row length, or an OpenCV failure.
   function Inverse_Discrete_Cosine_Transform_Rows (Self : Mat) return Mat;

   --  Returns an independently owned per-element product of two
   --  full-complex spectra using OpenCV 4.10 cv::mulSpectrums.
   --  Left and Right must be non-empty 2-D Float32 or Float64 Mats
   --  with exactly 2 channels, identical rows, identical columns,
   --  and identical depth. Channel 0 is the real part and channel 1
   --  is the imaginary part. Packed CCS C1 spectra are rejected
   --  even though OpenCV itself accepts them. Kind selects ordinary
   --  complex multiplication or multiplication by the conjugate of
   --  Right. Ordinary products participate in frequency-domain
   --  convolution; conjugate-right products participate in
   --  frequency-domain correlation. This operation does not
   --  transform, pad, scale, or invert; those remain caller
   --  operations. DFT_ROWS is not part of this API. Continuity is
   --  not required; non-contiguous Regions are supported. Left and
   --  Right are unchanged. The result has the same rows, columns,
   --  depth, and two channels, and owns independent storage.
   --  @param Left The first full-complex C2 spectrum.
   --  @param Right The second full-complex C2 spectrum, matching Left.
   --  @param Kind Ordinary or conjugate-right multiplication.
   --  @return A new C2 Mat holding the per-element product.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Multiply_Spectra
     (Left  : Mat;
      Right : Mat;
      Kind  : Spectrum_Multiplication_Kind := Ordinary_Spectrum_Product)
      return Mat;
   --  Returns an independently owned packed CCS C1 spectrum product using
   --  cv::mulSpectrums. Left and Right must be non-empty 2-D Float32 or
   --  Float64 Mats with exactly one channel, identical rows and columns, and
   --  identical depth. They are intended to contain OpenCV packed CCS spectra,
   --  such as results from Packed_Discrete_Fourier_Transform; this
   --  representation precondition is not checked numerically. Kind selects an
   --  ordinary product or multiplication by the conjugate of Right. The
   --  operation uses neither DFT_ROWS nor an inverse transform, and does not
   --  pad or crop. Non-contiguous Regions are supported. Both operands remain
   --  unchanged; the result preserves their shape and depth and remains C1.
   --  @param Left The first packed CCS C1 spectrum.
   --  @param Right The second packed CCS C1 spectrum, matching Left.
   --  @param Kind Ordinary or conjugate-right multiplication.
   --  @return A new C1 Mat holding the packed product.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Multiply_Packed_Spectra
     (Left  : Mat;
      Right : Mat;
      Kind  : Spectrum_Multiplication_Kind := Ordinary_Spectrum_Product)
      return Mat;
   --  Returns an independently owned row-wise packed CCS C1 spectrum product
   --  using cv::mulSpectrums with DFT_ROWS. Each row is interpreted as an
   --  independent spectrum for a real signal of length Columns. Left and Right
   --  must be non-empty 2-D Float32 or Float64 C1 Mats with identical rows,
   --  columns, and depth. They are intended to come from operations such as
   --  Packed_Discrete_Fourier_Transform_Rows; packed contents, conjugate
   --  symmetry, and numerical validity cannot be checked by this API. Kind
   --  selects ordinary multiplication or multiplication by the conjugate of
   --  Right. No inverse transform, scaling, padding, or cropping is performed.
   --  Non-contiguous Regions are supported. Both operands remain unchanged;
   --  the result preserves shape and depth, remains C1, and owns independent
   --  storage.
   --  @param Left The first Mat whose rows are packed CCS spectra.
   --  @param Right The second Mat of packed row spectra, matching Left.
   --  @param Kind Ordinary or conjugate-right multiplication.
   --  @return A new C1 Mat holding the row-wise packed products.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Multiply_Packed_Spectra_Rows
     (Left  : Mat;
      Right : Mat;
      Kind  : Spectrum_Multiplication_Kind := Ordinary_Spectrum_Product)
      return Mat;

   --  Returns the smallest OpenCV-efficient DFT length N >=
   --  Minimum_Size using OpenCV 4.10 cv::getOptimalDFTSize. Efficient
   --  sizes are products of powers of 2, 3, and 5. This only selects
   --  an efficient length; it does not allocate a Mat or guarantee
   --  that Discrete_Fourier_Transform will accept a matrix of that
   --  size under the separate OpenCV 4.10 DFT signed-arithmetic
   --  safety limits. A request too close to INT_MAX raises
   --  OpenCV_Error because OpenCV returns a negative sentinel.
   --  @param Minimum_Size The smallest acceptable transform length.
   --  @return The smallest efficient length not less than Minimum_Size.
   --  @exception OpenCV_Error Raised when no valid length can be returned.
   function Optimal_DFT_Size (Minimum_Size : Positive) return Positive;

   --  Returns OpenCV 4.10's recommended efficient even DCT length
   --  N1 >= Minimum_Size using the documented relationship
   --  2 * Optimal_DFT_Size (ceil (Minimum_Size / 2)). The helper
   --  does not allocate or transform a Mat. It returns 2 for
   --  Minimum_Size = 1 even though OpenCV 4.10 supports a 1 x 1
   --  DCT as an identity; this function follows OpenCV's
   --  performance-sizing formula rather than reporting the
   --  minimum executable DCT size. The returned length does not
   --  imply that a Mat of that size passes the separate
   --  Float32/Float64 DCT arithmetic-safety limits.
   --  @param Minimum_Size The smallest acceptable transform length.
   --  @return The recommended even length not less than Minimum_Size.
   --  @exception OpenCV_Error Raised when no valid length can be returned.
   function Optimal_DCT_Size (Minimum_Size : Positive) return Positive;

   --  Returns an independent Mat with Self's shape and element type.  For L1,
   --  L2, and Infinity, Alpha is the target norm and Beta is ignored.  For
   --  Min_Max, Alpha and Beta specify the destination range bounds.
   --  @param Self The source Mat.
   --  @param Kind Norm to target, or Min_Max to map onto a range.
   --  @param Alpha Target norm, or lower bound for Min_Max.
   --  @param Beta Upper bound for Min_Max; ignored for the norm kinds.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV rejects the operands.
   function Normalize
     (Self  : Mat;
      Kind  : Normalize_Kind := L2;
      Alpha : Long_Float := 1.0;
      Beta  : Long_Float := 0.0) return Mat;

   --  Same normalization semantics, using Destination's actual native header.
   --  Compatible whole/Region storage is reused; incompatible storage may be
   --  reallocated (a Region then detaches). Supports N-D, exact self, and
   --  distinct same-layout shallow aliases, not arbitrary partial overlap.
   --  Temporary Mat views cannot be destinations, even when compatible.
   --  Empty metadata and Float16 results retain native/version-specific
   --  behavior. Native failures need not preserve Destination.
   --  @param Self The source Mat.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @param Kind Norm to target, or Min_Max to map onto a range.
   --  @param Alpha Target norm, or lower bound for Min_Max.
   --  @param Beta Upper bound for Min_Max; ignored for the norm kinds.
   --  @exception OpenCV_Error Raised for a temporary-view Destination or
   --  when OpenCV rejects the operands.
   procedure Normalize
     (Self        : Mat;
      Destination : in out Mat;
      Kind        : Normalize_Kind := L2;
      Alpha       : Long_Float := 1.0;
      Beta        : Long_Float := 0.0);

   --  Adds channel-ordered Value to Self using native scalar arithmetic.
   --  Requires nonempty exactly 2-D C1..C4 storage, UInt8, Int8, UInt16,
   --  Int16, Int32, Float32 or Float64. Float16 is rejected. Scalar components
   --  are not repeated: Make_Scalar (5.0) leaves channels 1..3 zero.
   --  Native work-depth conversion, rounding and saturation apply;
   --  Int32 overflow is not portable mathematical arithmetic. Coefficients
   --  must be finite; see the operations guide for conversion limits.
   --  @param Self Source Mat, including a valid strided Region or scoped view.
   --  @param Value Component 0 applies to channel 0, and so on.
   --  @return Independently owned Mat with Self's shape and element type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Add (Self : Mat; Value : Scalar) return Mat;

   --  Writes Self + Value into the actual caller-owned Destination. Compatible
   --  Region storage is reused; mismatches detach, retaining old aliases.
   --  Exact and same-layout shallow aliases are supported. Other possibly
   --  overlapping byte spans are rejected conservatively before mutation.
   --  Temporary external/selected outputs are rejected; scoped inputs
   --  are allowed. Preflight failures preserve Destination, but arbitrary
   --  native failures do not promise rollback. Input rules match scalar Add.
   --  @param Self Source Mat.
   --  @param Value Channel-ordered scalar, not implicitly repeated.
   --  @param Destination Caller-owned Mat receiving Self + Value.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Add (Self : Mat; Value : Scalar; Destination : in out Mat);

   --  Returns Self - Value with the input and numerical rules of scalar Add.
   --  @param Self Source Mat.
   --  @param Value Channel-ordered subtrahend.
   --  @return Independent Mat preserving Self's shape and type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Subtract (Self : Mat; Value : Scalar) return Mat;

   --  Writes Self - Value under scalar Add's destination/alias rules.
   --  @param Self Source Mat.
   --  @param Value Channel-ordered subtrahend.
   --  @param Destination Caller-owned Mat receiving Self - Value.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Subtract (Self : Mat; Value : Scalar; Destination : in out Mat);

   --  Returns Self * Value; input/ownership rules match scalar Add.
   --  Native multiplication uses its own working-depth conversion, not scalar
   --  pre-rounding to Self's type. Floating multiply/divide permit nonfinite
   --  coefficients; integer coefficients must be finite and within Int32 max.
   --  @param Self Source Mat.
   --  @param Value Channel-ordered factors.
   --  @return Independent Mat preserving Self's shape and type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Multiply (Self : Mat; Value : Scalar) return Mat;

   --  Writes Self * Value under scalar Add's destination/alias rules.
   --  @param Self Source Mat.
   --  @param Value Channel-ordered factors.
   --  @param Destination Caller-owned Mat receiving the products.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Multiply (Self : Mat; Value : Scalar; Destination : in out Mat);

   --  Returns Self / Value, channel by channel. Input rules match scalar Add.
   --  For all five integer depths, every active scalar denominator must be
   --  nonzero; otherwise OpenCV_Error is raised before native execution,
   --  preserving source and destination storage. Floating zeros and
   --  nonfinite source values retain native version/backend behavior; no NaN
   --  payload, signed-zero or cross-version bit guarantee is made.
   --  @param Self Source numerator Mat.
   --  @param Value Channel-ordered denominators; nonzero for integer results.
   --  @return Independent Mat preserving Self's shape and type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Divide (Self : Mat; Value : Scalar) return Mat;

   --  Writes Self / Value under scalar Add's destination/alias rules.
   --  Integer zero denominators are rejected before any destination mutation.
   --  @param Self Source numerator Mat.
   --  @param Value Channel-ordered denominators.
   --  @param Destination Caller-owned Mat receiving the quotients.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Divide (Self : Mat; Value : Scalar; Destination : in out Mat);

   --  Reverse subtraction: returns Value - Self, not Self - Value.
   --  Input, numeric and ownership rules match scalar Add.
   --  @param Value Channel-ordered minuend.
   --  @param Self Source subtrahend Mat.
   --  @return Independent Mat preserving Self's shape and type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Subtract_From (Value : Scalar; Self : Mat) return Mat;

   --  Writes Value - Self under scalar Add's destination/alias rules.
   --  @param Value Channel-ordered minuend.
   --  @param Self Source subtrahend Mat.
   --  @param Destination Caller-owned Mat receiving Value - Self.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Subtract_From
     (Value : Scalar; Self : Mat; Destination : in out Mat);

   --  Reverse division: returns Value / Self, not Self / Value.
   --  Input/ownership rules match scalar Add. For all five integer depths,
   --  any zero denominator component anywhere in Self raises OpenCV_Error
   --  before native execution. Every channel and logical Region row is
   --  inspected; rejection preserves source and destination storage.
   --  Floating zero/nonfinite behavior follows native Divide.
   --  @param Value Channel-ordered numerators.
   --  @param Self Source denominator Mat.
   --  @return Independent Mat preserving Self's shape and type.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Divide_Into (Value : Scalar; Self : Mat) return Mat;

   --  Writes Value / Self under scalar Add's destination/alias rules.
   --  Integer zero Mat components are rejected before destination mutation.
   --  @param Value Channel-ordered numerators.
   --  @param Self Source denominator Mat.
   --  @param Destination Caller-owned Mat receiving Value / Self.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Divide_Into
     (Value : Scalar; Self : Mat; Destination : in out Mat);

   --  Compares Self relation Value without narrowing Value to Self's depth.
   --  Requires nonempty exactly 2-D C1, one of the seven scalar Add depths.
   --  Fractional and out-of-integer-range finite values retain native compare
   --  behavior. Value must be finite. Nonfinite source pixels remain native.
   --  @param Self Single-channel source Mat.
   --  @param Value Finite Float64 comparison value.
   --  @param Kind Relation read as Self relation Value.
   --  @return Independent UInt8 C1 Mat containing only zero or 255.
   --  @exception OpenCV_Error Raised for unsupported input or native failure.
   function Compare
     (Self : Mat; Value : Float64_Value; Kind : Comparison_Kind) return Mat;

   --  Writes the scalar comparison mask into the actual Destination.
   --  Reuse/detachment/temporary rules match scalar Add. Overlapping inputs
   --  are allowed only for identical-layout UInt8 C1 source/destination;
   --  other overlap, including depth-changing exact alias, is rejected.
   --  @param Self Single-channel source Mat.
   --  @param Value Finite Float64 comparison value, not prematurely narrowed.
   --  @param Kind Relation read as Self relation Value.
   --  @param Destination Caller-owned Mat receiving the UInt8 C1 mask.
   --  @exception OpenCV_Error Raised for unsupported input/alias or failure.
   procedure Compare
     (Self        : Mat;
      Value       : Float64_Value;
      Kind        : Comparison_Kind;
      Destination : in out Mat);

   --  Adds corresponding elements of two Mats. Both operands must have
   --  identical 2-D shape and element type. The result owns independent
   --  storage and preserves that element type; saturation and overflow
   --  follow native OpenCV arithmetic for the depth.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Add (Left, Right : Mat) return Mat;

   --  Subtracts Right from Left element by element. Operand and result
   --  rules match the Add function.
   --  @param Left The minuend.
   --  @param Right The subtrahend, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Subtract (Left, Right : Mat) return Mat;

   --  Multiplies corresponding elements. Operand and result rules match the
   --  Add function.
   --  @param Left The first factor.
   --  @param Right The second factor, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Multiply (Left, Right : Mat) return Mat;

   --  Divides Left by Right element by element. Operand and result rules
   --  match the Add function; zero denominators follow native OpenCV
   --  behavior.
   --  @param Left The dividend.
   --  @param Right The divisor, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Divide (Left, Right : Mat) return Mat;

   --  Computes the absolute difference of corresponding elements. Operand
   --  and result rules match the Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Abs_Diff (Left, Right : Mat) return Mat;

   --  Selects the smaller of corresponding elements. Operand and result
   --  rules match the Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Minimum (Left, Right : Mat) return Mat;

   --  Selects the larger of corresponding elements. Operand and result rules
   --  match the Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Maximum (Left, Right : Mat) return Mat;

   --  UMat form of the Mat Add function: adds corresponding elements with
   --  native UMat arithmetic. Operands must have identical 2-D shape, depth,
   --  and channels. The result is a new UMat with independent storage.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Add (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Subtract function. Operand and result rules match
   --  the UMat Add function.
   --  @param Left The minuend.
   --  @param Right The subtrahend, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Subtract (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Multiply function. Operand and result rules match
   --  the UMat Add function.
   --  @param Left The first factor.
   --  @param Right The second factor, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Multiply (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Divide function. Operand and result rules match
   --  the UMat Add function; zero denominators follow native OpenCV
   --  behavior.
   --  @param Left The dividend.
   --  @param Right The divisor, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Divide (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Abs_Diff function. Operand and result rules match
   --  the UMat Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Abs_Diff (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Minimum function. Operand and result rules match
   --  the UMat Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Minimum (Left, Right : UMat) return UMat;

   --  UMat form of the Mat Maximum function. Operand and result rules match
   --  the UMat Add function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Maximum (Left, Right : UMat) return UMat;

   --  Destination form of Add. The operands have matching 2-D shape and
   --  element type; Destination is not an operand. Compatible whole or
   --  Region storage is reused, preserving aliases and parent sharing, while
   --  a shape, depth, or channel mismatch may reallocate and detach a
   --  Region. Destination may be Left, Right, or a same-layout shallow alias
   --  of either, and the operands may alias each other; arbitrary partial
   --  overlap is unsupported. Temporary Mat views are allowed as sources but
   --  never as Destination. Validation before the native call leaves
   --  Destination unchanged, but native failures need not. Empty metadata
   --  retains native and version-specific behavior. Float16 follows the
   --  function policy (Float32 widening on OpenCV 4.x, native on 5.x).
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the sum.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Add (Left, Right : Mat; Destination : in out Mat);

   --  Destination form of Subtract. Destination, alias, and failure rules
   --  match the Mat Add destination form.
   --  @param Left The minuend.
   --  @param Right The subtrahend, matching Left.
   --  @param Destination The caller-owned Mat that receives the difference.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Subtract (Left, Right : Mat; Destination : in out Mat);

   --  UMat destination form of Add. The rules of the Mat Add destination form
   --  apply to native UMat storage; OpenCV controls execution and any
   --  internal fallback.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the sum.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Add (Left, Right : UMat; Destination : in out UMat);

   --  UMat destination form of Subtract. Destination, alias, and failure
   --  rules match the UMat Add destination form.
   --  @param Left The minuend.
   --  @param Right The subtrahend, matching Left.
   --  @param Destination The caller-owned UMat that receives the difference.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Subtract (Left, Right : UMat; Destination : in out UMat);

   --  Destination form of Multiply: elementwise products under the
   --  destination rules of the Mat Add destination form. UInt8 and Int16
   --  results saturate; Int32 overflow is not promised to saturate.
   --  @param Left The first factor.
   --  @param Right The second factor, matching Left.
   --  @param Destination The caller-owned Mat that receives the products.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Multiply (Left, Right : Mat; Destination : in out Mat);

   --  UMat destination form of Multiply, under the rules of the Mat
   --  Multiply destination form.
   --  @param Left The first factor.
   --  @param Right The second factor, matching Left.
   --  @param Destination The caller-owned UMat that receives the products.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Multiply (Left, Right : UMat; Destination : in out UMat);

   --  Destination form of Divide under the destination rules of the Mat Add
   --  destination form. The quotient is computed from the original Left and
   --  Right values even when Destination is Right. Zero denominators follow
   --  OpenCV: integer zero, or floating infinity or NaN; Float16 retains the
   --  function's native policy.
   --  @param Left The dividend.
   --  @param Right The divisor, matching Left.
   --  @param Destination The caller-owned Mat that receives the quotients.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Divide (Left, Right : Mat; Destination : in out Mat);

   --  UMat destination form of Divide, under the rules of the Mat Divide
   --  destination form.
   --  @param Left The dividend.
   --  @param Right The divisor, matching Left.
   --  @param Destination The caller-owned UMat that receives the quotients.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Divide (Left, Right : UMat; Destination : in out UMat);

   --  Destination form of Abs_Diff under the destination rules of the Mat Add
   --  destination form, computing native elementwise abs (Left - Right).
   --  UInt8 does not wrap; Int16 saturates; Int32 overflow is not saturated.
   --  Nonfinite floating results remain native, without NaN payload promises.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the differences.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Abs_Diff (Left, Right : Mat; Destination : in out Mat);

   --  UMat destination form of Abs_Diff, under the rules of the Mat Abs_Diff
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the differences.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Abs_Diff (Left, Right : UMat; Destination : in out UMat);

   --  Destination form of Minimum under the destination rules of the Mat Add
   --  destination form, with direct element selection and no saturation.
   --  Independent destinations match the function. Exact or shallow aliases
   --  retain native SIMD and tail selection, so floating NaN classification
   --  and signed-zero selection can differ from a fresh result; this is not
   --  IEEE fmin.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the minima.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Minimum (Left, Right : Mat; Destination : in out Mat);

   --  Destination form of Maximum, under the rules of the Mat Minimum
   --  destination form; the selection is not IEEE fmax.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the maxima.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Maximum (Left, Right : Mat; Destination : in out Mat);

   --  UMat destination form of Minimum, under the rules of the Mat Minimum
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the minima.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Minimum (Left, Right : UMat; Destination : in out UMat);

   --  UMat destination form of Maximum, under the rules of the Mat Minimum
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the maxima.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Maximum (Left, Right : UMat; Destination : in out UMat);

   --  Returns an independent Mat with the compatible operands' shape and
   --  element type. Float16 Add_Weighted uses native CV_16F cv::addWeighted
   --  on OpenCV 5.0. On supported OpenCV 4.x releases, operands are widened
   --  to Float32, OpenCV's optimized Float32 addWeighted is executed, and
   --  the result is narrowed to Float16. OpenCV may use SIMD or fused
   --  multiply-add depending on architecture and CPU dispatch; exact Float16
   --  bit patterns are not guaranteed to be independent of OpenCV version,
   --  architecture, SIMD dispatch, or vector-tail placement. Scale_Add has
   --  no native CV_16F kernel through OpenCV 5.0, so it uses Float32
   --  compatibility on every supported version.
   --  @param Left The first operand.
   --  @param Alpha Weight applied to Left.
   --  @param Right The second operand, matching Left.
   --  @param Beta Weight applied to Right.
   --  @param Gamma Scalar added to the weighted sum.
   --  @return A new Mat holding Left * Alpha + Right * Beta + Gamma.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Add_Weighted
     (Left  : Mat;
      Alpha : Long_Float;
      Right : Mat;
      Beta  : Long_Float;
      Gamma : Long_Float := 0.0) return Mat;

   --  Returns an independent Mat with Self's shape and element type.
   --  Each element is Self * Scale + Right. Depths below Float32 use
   --  OpenCV's addWeighted path: UInt8, Int8, UInt16, and Int16 saturate;
   --  Int32 does not. Float32 and Float64 use the dedicated scaleAdd kernels.
   --  On every supported OpenCV version, Float16 Scale_Add widens its inputs
   --  exactly to Float32, narrows Scale to Float32, executes OpenCV's
   --  optimized Float32 scaleAdd, and narrows the result once to Float16.
   --  Supported OpenCV 4.1 through 5.0 releases do not expose a CV_16F
   --  scaleAdd kernel. OpenCV may use SIMD or fused multiply-add depending
   --  on architecture and CPU dispatch; exact Float16 bit patterns are not
   --  guaranteed to be independent of architecture, SIMD dispatch, or
   --  vector-tail placement.
   --  Both operands must have identical 2D shape and element type.
   --  @param Self The Mat that is scaled.
   --  @param Scale Factor applied to Self.
   --  @param Right The Mat added after scaling, matching Self.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Scale_Add (Self : Mat; Scale : Long_Float; Right : Mat) return Mat;

   --  UMat form of Add_Weighted. The result remains UMat-native. Operands
   --  must have matching N-dimensional shape, depth, and channels. Float16
   --  uses the same version-dependent widening and coefficient rounding as
   --  the Mat function.
   --  @param Left The first operand.
   --  @param Alpha Weight applied to Left.
   --  @param Right The second operand, matching Left.
   --  @param Beta Weight applied to Right.
   --  @param Gamma Scalar added to the weighted sum.
   --  @return A new UMat holding Left * Alpha + Right * Beta + Gamma.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Add_Weighted
     (Left  : UMat;
      Alpha : Long_Float;
      Right : UMat;
      Beta  : Long_Float;
      Gamma : Long_Float := 0.0) return UMat;

   --  UMat form of Scale_Add. The result remains UMat-native. Operands retain
   --  the 2-D shape and element-type policy of the Mat function, with the
   --  same Float16 widening and rounding behavior.
   --  @param Self The UMat that is scaled.
   --  @param Scale Factor applied to Self.
   --  @param Right The UMat added after scaling, matching Self.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Scale_Add
     (Self : UMat; Scale : Long_Float; Right : UMat) return UMat;

   --  Destination form of Add_Weighted, writing directly into caller storage
   --  under the numerical policy of the function. Compatible whole or Region
   --  destinations retain storage and shallow aliases; mismatched
   --  destinations detach or reallocate to the source shape and type. The
   --  sources may be N-dimensional. Exact and same-layout shallow source
   --  aliases are supported, arbitrary partially overlapping Regions are
   --  not, and native SIMD, fused multiply-add and tail handling can give
   --  floating aliases different rounding from independent results.
   --  Temporary Mat views may be sources but not destinations. Coefficients
   --  are not validated or normalized; native precision applies.
   --  @param Left The first operand.
   --  @param Alpha Weight applied to Left.
   --  @param Right The second operand, matching Left.
   --  @param Beta Weight applied to Right.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @param Gamma Scalar added to the weighted sum.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Add_Weighted
     (Left        : Mat;
      Alpha       : Long_Float;
      Right       : Mat;
      Beta        : Long_Float;
      Destination : in out Mat;
      Gamma       : Long_Float := 0.0);

   --  Destination form of Scale_Add under the destination, alias, and
   --  rounding rules of the Mat Add_Weighted destination form. Operands
   --  remain two-dimensional.
   --  @param Self The Mat that is scaled.
   --  @param Scale Factor applied to Self.
   --  @param Right The Mat added after scaling, matching Self.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Scale_Add
     (Self : Mat; Scale : Long_Float; Right : Mat; Destination : in out Mat);

   --  UMat destination form of Add_Weighted, under the rules of the Mat
   --  Add_Weighted destination form and native UMat storage.
   --  @param Left The first operand.
   --  @param Alpha Weight applied to Left.
   --  @param Right The second operand, matching Left.
   --  @param Beta Weight applied to Right.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @param Gamma Scalar added to the weighted sum.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Add_Weighted
     (Left        : UMat;
      Alpha       : Long_Float;
      Right       : UMat;
      Beta        : Long_Float;
      Destination : in out UMat;
      Gamma       : Long_Float := 0.0);

   --  UMat destination form of Scale_Add, under the rules of the Mat
   --  Scale_Add destination form and native UMat storage.
   --  @param Self The UMat that is scaled.
   --  @param Scale Factor applied to Self.
   --  @param Right The UMat added after scaling, matching Self.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Scale_Add
     (Self        : UMat;
      Scale       : Long_Float;
      Right       : UMat;
      Destination : in out UMat);

   --  All UMat operands and masks stay UMat-native. Bitwise operations use
   --  stored bits, including exact Float16 bits. Binary operands have matching
   --  2-D shape and element type; masks are UInt8 C1 of matching 2-D size.
   --  Computes the bitwise AND of corresponding elements. Floating storage,
   --  including Float16, is operated on as stored bits. Operands must have
   --  matching 2-D shape and element type.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_And (Left, Right : UMat) return UMat;

   --  Masked bitwise AND. Elements selected by a nonzero Mask value (the
   --  complete element, all channels) receive Left and Right; the others are
   --  zero in the new UMat. Mask is UInt8 C1 with the operands' 2-D size.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_And (Left, Right, Mask : UMat) return UMat;

   --  Computes the bitwise OR of corresponding elements, with the operand
   --  rules of the unmasked Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_Or (Left, Right : UMat) return UMat;

   --  Masked bitwise OR, with the mask rules of the masked Bitwise_And
   --  function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_Or (Left, Right, Mask : UMat) return UMat;

   --  Computes the bitwise exclusive OR of corresponding elements, with the
   --  operand rules of the unmasked Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_Xor (Left, Right : UMat) return UMat;

   --  Masked bitwise exclusive OR, with the mask rules of the masked
   --  Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_Xor (Left, Right, Mask : UMat) return UMat;

   --  Inverts every stored bit of Self, including the bits of floating
   --  storage. Unmasked inversion supports N-dimensional UMats.
   --  @param Self The source UMat.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   function Bitwise_Not (Self : UMat) return UMat;

   --  Masked bitwise NOT. Elements selected by a nonzero Mask value (the
   --  complete element, all channels) are inverted; the others are zero in
   --  the new UMat. Mask is UInt8 C1 with Self's 2-D size.
   --  @param Self The source UMat.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when Mask is mismatched or OpenCV
   --  reports a failure.
   function Bitwise_Not (Self, Mask : UMat) return UMat;

   --  Destination form of Bitwise_And. Compatible whole or Region storage is
   --  reused; a mismatch detaches this header. Floating storage is operated
   --  on as bits. Exact and same-layout source aliases are supported;
   --  arbitrary partial overlap is outside the contract. Operands retain the
   --  2-D policy of the function. Execution remains UMat-native.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Bitwise_And (Left, Right : UMat; Destination : in out UMat);

   --  Masked destination form of Bitwise_And. A nonzero Mask value selects
   --  the entire element (all channels). An unselected element keeps its
   --  value in a compatible existing Destination, and is zero after native
   --  reallocation. Destination aliasing Mask is outside the contract.
   --  Other rules match the unmasked destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, or an
   --  OpenCV failure.
   procedure Bitwise_And (Left, Right, Mask : UMat; Destination : in out UMat);

   --  Destination form of Bitwise_Or, with the rules of the Bitwise_And
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Bitwise_Or (Left, Right : UMat; Destination : in out UMat);

   --  Masked destination form of Bitwise_Or, with the rules of the masked
   --  Bitwise_And destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, or an
   --  OpenCV failure.
   procedure Bitwise_Or (Left, Right, Mask : UMat; Destination : in out UMat);

   --  Destination form of Bitwise_Xor, with the rules of the Bitwise_And
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or an OpenCV
   --  failure.
   procedure Bitwise_Xor (Left, Right : UMat; Destination : in out UMat);

   --  Masked destination form of Bitwise_Xor, with the rules of the masked
   --  Bitwise_And destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, or an
   --  OpenCV failure.
   procedure Bitwise_Xor (Left, Right, Mask : UMat; Destination : in out UMat);

   --  Destination form of Bitwise_Not, with the storage and alias rules of
   --  the Bitwise_And destination form. Unmasked inversion supports
   --  N-dimensional UMats.
   --  @param Self The source UMat.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   procedure Bitwise_Not (Self : UMat; Destination : in out UMat);

   --  Masked destination form of Bitwise_Not, with the mask rules of the
   --  masked Bitwise_And destination form. Masked inversion retains the
   --  2-D policy.
   --  @param Self The source UMat.
   --  @param Mask UInt8 single-channel selector of matching size.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised when Mask is mismatched or OpenCV
   --  reports a failure.
   procedure Bitwise_Not (Self, Mask : UMat; Destination : in out UMat);

   --  Tests each element against inclusive per-channel bounds and returns a
   --  UInt8 C1 mask: an element is set only when every channel lies within
   --  its Lower and Upper components. Supports N-dimensional UMats with at
   --  most four channels. A Float16 source requires OpenCV 5.0 or later.
   --  @param Self The UMat to test.
   --  @param Lower Inclusive per-channel lower bounds.
   --  @param Upper Inclusive per-channel upper bounds.
   --  @return A new UInt8 C1 mask UMat.
   --  @exception OpenCV_Error Raised for an empty UMat, more than four
   --  channels, an unsupported depth, or an OpenCV failure.
   function In_Range (Self : UMat; Lower, Upper : Scalar) return UMat;

   --  Compares corresponding elements of two single-channel UMats and
   --  returns a UInt8 C1 mask. Operands have matching 2-D shape.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Kind Relation tested, read as Left relation Right.
   --  @return A new UInt8 C1 mask UMat.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Compare (Left, Right : UMat; Kind : Comparison_Kind) return UMat;

   --  Destination form of Compare. The UInt8 C1 output reuses compatible
   --  whole or Region storage; mismatches detach Destination. Exact aliases
   --  that would change depth are rejected for ABI safety, while UInt8 C1
   --  exact and distinct shallow aliases are supported. Other partial
   --  overlap is outside the contract. If both operands are empty,
   --  Destination is released. Execution remains UMat-native, including
   --  OpenCV's internal CPU fallback.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Kind Relation tested, read as Left relation Right.
   --  @param Destination The caller-owned UMat that receives the mask.
   --  @exception OpenCV_Error Raised for mismatched operands, a rejected
   --  alias, or an OpenCV failure.
   procedure Compare
     (Left, Right : UMat; Kind : Comparison_Kind; Destination : in out UMat);

   --  Destination form of In_Range. The UInt8 C1 output reuses compatible
   --  whole or Region storage; mismatches detach Destination. An exact
   --  source and Destination alias is rejected for ABI safety, and other
   --  shared-storage aliases are outside the contract. An empty UMat is
   --  rejected. Other rules match the function.
   --  @param Self The UMat to test.
   --  @param Lower Inclusive per-channel lower bounds.
   --  @param Upper Inclusive per-channel upper bounds.
   --  @param Destination The caller-owned UMat that receives the mask.
   --  @exception OpenCV_Error Raised for an empty UMat, an exact alias, an
   --  unsupported channel count or depth, or an OpenCV failure.
   procedure In_Range
     (Self : UMat; Lower : Scalar; Upper : Scalar; Destination : in out UMat);

   --  UMat-native normalization retains destination depth and accepts N-D.
   --  Native Float16 normalization support depends on Kind/OpenCV version.
   --  @param Self The source UMat.
   --  @param Kind Norm to target, or Min_Max to map onto a range.
   --  @param Alpha Target norm, or lower bound for Min_Max.
   --  @param Beta Upper bound for Min_Max; ignored for the norm kinds.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV rejects the operands.
   function Normalize
     (Self  : UMat;
      Kind  : Normalize_Kind := L2;
      Alpha : Long_Float := 1.0;
      Beta  : Long_Float := 0.0) return UMat;

   --  UMat-native destination reuse, with the Mat procedure's alias/reallocate
   --  contract and the existing UMat empty-storage compatibility handling.
   --  @param Self The source UMat.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @param Kind Norm to target, or Min_Max to map onto a range.
   --  @param Alpha Target norm, or lower bound for Min_Max.
   --  @param Beta Upper bound for Min_Max; ignored for the norm kinds.
   --  @exception OpenCV_Error Raised when OpenCV rejects the operands.
   procedure Normalize
     (Self        : UMat;
      Destination : in out UMat;
      Kind        : Normalize_Kind := L2;
      Alpha       : Long_Float := 1.0;
      Beta        : Long_Float := 0.0);

   --  Square root with the numerical contract of the Mat Sqrt function.
   --  Requires Float32 or Float64 (Float16 is rejected), supports
   --  N-dimensional UMats, and processes channels independently.
   --  @param Self The Float32 or Float64 source.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   function Sqrt (Self : UMat) return UMat;

   --  Exponential with the numerical contract of the Mat Exp function.
   --  Requires Float32 or Float64 (Float16 is rejected), supports
   --  N-dimensional UMats, and processes channels independently.
   --  @param Self The Float32 or Float64 source.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   function Exp (Self : UMat) return UMat;

   --  Natural logarithm with the numerical contract of the Mat Log function.
   --  Requires Float32 or Float64 (Float16 is rejected), supports
   --  N-dimensional UMats, and processes channels independently.
   --  @param Self The Float32 or Float64 source.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   function Log (Self : UMat) return UMat;

   --  Power with the numerical contract of the Mat Pow function. Supports
   --  N-dimensional UMats and processes channels independently. Integer
   --  storage is accepted for nonnegative integer powers, retaining native
   --  saturation and overflow behavior. Float16 is rejected.
   --  @param Self The source UMat.
   --  @param Power The exponent.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported depth or exponent
   --  combination, or an OpenCV failure.
   function Pow (Self : UMat; Power : Long_Float) return UMat;

   --  UMat destination form of Sqrt. Native UMat destinations follow the
   --  reuse and alias boundaries of the Mat Sqrt destination form. No
   --  binding-level host staging is performed, including for N-dimensional
   --  storage.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   procedure Sqrt (Self : UMat; Destination : in out UMat);

   --  UMat destination form of Exp, under the rules of the UMat Sqrt
   --  destination form.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   procedure Exp (Self : UMat; Destination : in out UMat);

   --  UMat destination form of Log, under the rules of the UMat Sqrt
   --  destination form.
   --  @param Self The Float32 or Float64 source.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   procedure Log (Self : UMat; Destination : in out UMat);

   --  UMat destination form of Pow, under the rules of the UMat Sqrt
   --  destination form.
   --  @param Self The source UMat.
   --  @param Power The exponent.
   --  @param Destination The caller-owned UMat that receives the result.
   --  @exception OpenCV_Error Raised for an unsupported depth or exponent
   --  combination, or an OpenCV failure.
   procedure Pow (Self : UMat; Power : Long_Float; Destination : in out UMat);

   --  UMat form of Magnitude: sqrt (X**2 + Y**2) computed natively without
   --  binding-level host staging. X and Y are matching 2-D Float32 or
   --  Float64 UMats; channels are computed independently.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @return A new UMat with independent storage.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands
   --  or an OpenCV failure.
   function Magnitude (X, Y : UMat) return UMat;

   --  UMat destination form of Magnitude. Native UMat destination reuse,
   --  without binding-level host staging, follows the rules of the Mat
   --  Magnitude destination form.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Destination The caller-owned UMat that receives the magnitudes.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands
   --  or an OpenCV failure.
   procedure Magnitude (X, Y : UMat; Destination : in out UMat);

   --  UMat form of Phase, using matching 2-D Float32 or Float64 sources and
   --  the native angle units and storage semantics of the Mat function.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @return A new UMat of angles with independent storage.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands
   --  or an OpenCV failure.
   function Phase (X, Y : UMat; Units : Angle_Unit := Radians) return UMat;

   --  UMat destination form of Phase. Native UMat destination reuse, without
   --  binding-level host staging, follows the rules of the Mat Phase
   --  destination form.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Destination The caller-owned UMat that receives the angles.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands
   --  or an OpenCV failure.
   procedure Phase
     (X, Y : UMat; Destination : in out UMat; Units : Angle_Unit := Radians);

   --  Independent polar outputs of the UMat Cart_To_Polar. Each field owns
   --  its own result header and storage, and one native call produces both
   --  fields. Angle accuracy follows the Mat Phase contract.
   --  @field Magnitude Per-element vector length.
   --  @field Angle Per-element angle, in the unit requested from the
   --  producing operation.
   type UMat_Polar_Coordinates is record
      Magnitude : UMat;
      Angle     : UMat;
   end record;

   --  Independent Cartesian outputs of the UMat Polar_To_Cart. Each field
   --  owns its own result header and storage.
   --  @field X Per-element horizontal component.
   --  @field Y Per-element vertical component.
   type UMat_Cartesian_Coordinates is record
      X : UMat;
      Y : UMat;
   end record;

   --  UMat form of Cart_To_Polar. One native call produces both results,
   --  with the operand rules and angle accuracy of the Mat function.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Units Angle unit of the result: radians by default, or degrees.
   --  @return Independently owned magnitude and angle UMats.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands
   --  or an OpenCV failure.
   function Cart_To_Polar
     (X, Y : UMat; Units : Angle_Unit := Radians)
      return UMat_Polar_Coordinates;

   --  UMat destination form of Cart_To_Polar with individual destinations,
   --  under the paired destination and alias rules of the Mat form, without
   --  host staging: outputs must be distinct native objects, not exactly
   --  either source, and overlapping storage is unsupported.
   --  @param X Float32 or Float64 horizontal component.
   --  @param Y Vertical component matching X in dimensions, depth, and
   --  channel count.
   --  @param Magnitude The caller-owned UMat that receives the magnitudes.
   --  @param Angle The caller-owned UMat that receives the angles.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for mismatched or unsupported operands,
   --  an unsupported output alias, or an OpenCV failure.
   procedure Cart_To_Polar
     (X, Y             : UMat;
      Magnitude, Angle : in out UMat;
      Units            : Angle_Unit := Radians);

   --  Groups the two caller-owned destinations. Each field independently owns
   --  its UMat header; the record is not a transactional update and does not
   --  change native alias rules. Compatible storage is reused and mismatched
   --  storage may detach or reallocate independently. Validation and the
   --  native transform are the same as the individual-destination procedure.
   --  @param X Cartesian X component. Float32 or Float64, matching Y.
   --  @param Y Cartesian Y component. Same dimensions, depth, and channels
   --  as X.
   --  @param Destination Caller-owned Magnitude and Angle fields. Each field
   --  independently reuses compatible UMat storage or detaches when
   --  mismatched.
   --  @param Units Angle unit: radians by default, or degrees.
   procedure Cart_To_Polar
     (X, Y        : UMat;
      Destination : in out UMat_Polar_Coordinates;
      Units       : Angle_Unit := Radians);
   --  Same paired destination/alias rules as Mat, without host staging.
   --  Angle is authoritative. Empty Magnitude (default or typed), or the
   --  angle-only overload, means unit magnitude. Non-empty Magnitude must
   --  match Angle's 2-D shape, Float32/Float64 depth, and channels.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty to
   --  mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @return Independently owned X and Y UMats.
   --  @exception OpenCV_Error Raised for a default empty Angle, mismatched
   --  operands, an unsupported depth, or an OpenCV failure.
   function Polar_To_Cart
     (Magnitude, Angle : UMat; Units : Angle_Unit := Radians)
      return UMat_Cartesian_Coordinates;

   --  Angle-only UMat form of Polar_To_Cart: every Angle element has unit
   --  magnitude, so the results are the cosine and sine of Angle.
   --  @param Angle Polar angle. Float32 or Float64.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @return Independently owned X and Y UMats.
   --  @exception OpenCV_Error Raised for a default empty Angle, an
   --  unsupported depth, or an OpenCV failure.
   function Polar_To_Cart
     (Angle : UMat; Units : Angle_Unit := Radians)
      return UMat_Cartesian_Coordinates;

   --  UMat destination form of Polar_To_Cart with individual destinations,
   --  under the paired destination and alias rules of the Mat form: outputs
   --  must be distinct native objects, not exactly any source, and
   --  overlapping storage is unsupported.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty to
   --  mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param X The caller-owned UMat that receives Magnitude * cos (Angle).
   --  @param Y The caller-owned UMat that receives Magnitude * sin (Angle).
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Angle, mismatched
   --  operands, an unsupported depth or output alias, or an OpenCV failure.
   procedure Polar_To_Cart
     (Magnitude, Angle : UMat;
      X, Y             : in out UMat;
      Units            : Angle_Unit := Radians);

   --  Angle-only UMat destination form of Polar_To_Cart: every Angle element
   --  has unit magnitude. Destination and alias rules match the two-operand
   --  UMat procedure.
   --  @param Angle Polar angle. Float32 or Float64.
   --  @param X The caller-owned UMat that receives cos (Angle).
   --  @param Y The caller-owned UMat that receives sin (Angle).
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   --  @exception OpenCV_Error Raised for a default empty Angle, an
   --  unsupported depth or output alias, or an OpenCV failure.
   procedure Polar_To_Cart
     (Angle : UMat; X, Y : in out UMat; Units : Angle_Unit := Radians);

   --  Groups the two caller-owned destinations. Each field independently owns
   --  its UMat header; the record is not a transactional update and does not
   --  change native alias rules. Compatible storage is reused and mismatched
   --  storage may detach or reallocate independently. Empty Magnitude, and
   --  the angle-only overload, still mean unit magnitude. Validation and the
   --  native transform are the same as the individual-destination procedures.
   --  @param Magnitude Non-empty polar magnitude matching Angle, or empty
   --  to mean unit magnitude for every Angle element.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Destination Caller-owned X and Y fields. Each field independently
   --  reuses compatible UMat storage or detaches when mismatched.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   procedure Polar_To_Cart
     (Magnitude, Angle : UMat;
      Destination      : in out UMat_Cartesian_Coordinates;
      Units            : Angle_Unit := Radians);
   --  Angle-only UMat record destination. Empty magnitude is implied, so
   --  every Angle element has unit magnitude. Native UMat residency and the
   --  existing typed-empty and pre-4.10 Float64 helper behavior are
   --  preserved.
   --  Each Destination field independently owns its header.
   --  @param Angle Authoritative polar angle. Float32 or Float64.
   --  @param Destination Caller-owned X and Y fields written as cosine and
   --  sine of Angle. Compatible UMat storage is reused independently
   --  per field.
   --  @param Units Angle unit of Angle: radians by default, or degrees.
   procedure Polar_To_Cart
     (Angle       : UMat;
      Destination : in out UMat_Cartesian_Coordinates;
      Units       : Angle_Unit := Radians);

   --  Computes the bitwise AND of corresponding elements, operating on
   --  stored bits (floating storage, including Float16, is not converted).
   --  Operands must have matching shape and element type. The result owns
   --  independent storage.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_And (Left, Right : Mat) return Mat;

   --  Masked bitwise AND. A nonzero Mask value selects the complete element
   --  (all channels); unselected elements are zero in the new Mat. Mask is
   --  UInt8 C1 with the operands' shape.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_And (Left, Right, Mask : Mat) return Mat;

   --  Computes the bitwise OR of corresponding elements, with the operand
   --  rules of the unmasked Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_Or (Left, Right : Mat) return Mat;

   --  Masked bitwise OR, with the mask rules of the masked Bitwise_And
   --  function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_Or (Left, Right, Mask : Mat) return Mat;

   --  Computes the bitwise exclusive OR of corresponding elements, with the
   --  operand rules of the unmasked Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  OpenCV reports a failure.
   function Bitwise_Xor (Left, Right : Mat) return Mat;

   --  Masked bitwise exclusive OR, with the mask rules of the masked
   --  Bitwise_And function.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the operands or Mask are
   --  mismatched or OpenCV reports a failure.
   function Bitwise_Xor (Left, Right, Mask : Mat) return Mat;

   --  Inverts every stored bit of Self, including the bits of floating
   --  storage. Unmasked inversion supports N-dimensional Mats.
   --  @param Self The source Mat.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   function Bitwise_Not (Self : Mat) return Mat;

   --  Masked bitwise NOT. A nonzero Mask value selects the complete element
   --  (all channels) for inversion; unselected elements are zero in the new
   --  Mat. Mask is UInt8 C1 with Self's shape.
   --  @param Self The source Mat.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when Mask is mismatched or OpenCV
   --  reports a failure.
   function Bitwise_Not (Self, Mask : Mat) return Mat;

   --  Destination form of Bitwise_And with the reuse, mask,
   --  bit-representation, dimensional and alias contracts of the UMat
   --  procedures above: compatible whole or Region storage is reused, a
   --  mismatch detaches, exact and same-layout source aliases are supported
   --  and arbitrary partial overlap is not. Temporary external or selected
   --  Mat views are legal inputs but cannot be Destination, because output
   --  creation may rebind their callback-scoped storage capability.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_And (Left, Right : Mat; Destination : in out Mat);

   --  Masked destination form of Bitwise_And, under the rules of the Mat
   --  Bitwise_And destination form. A nonzero Mask value selects the whole
   --  element; an unselected element keeps its value in a compatible
   --  existing Destination and is zero after native reallocation.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_And (Left, Right, Mask : Mat; Destination : in out Mat);

   --  Destination form of Bitwise_Or, under the rules of the Mat Bitwise_And
   --  destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_Or (Left, Right : Mat; Destination : in out Mat);

   --  Masked destination form of Bitwise_Or, under the rules of the masked
   --  Mat Bitwise_And destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_Or (Left, Right, Mask : Mat; Destination : in out Mat);

   --  Destination form of Bitwise_Xor, under the rules of the Mat
   --  Bitwise_And destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_Xor (Left, Right : Mat; Destination : in out Mat);

   --  Masked destination form of Bitwise_Xor, under the rules of the masked
   --  Mat Bitwise_And destination form.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for mismatched operands or Mask, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_Xor (Left, Right, Mask : Mat; Destination : in out Mat);

   --  Destination form of Bitwise_Not, under the rules of the Mat
   --  Bitwise_And destination form. Unmasked inversion supports
   --  N-dimensional Mats.
   --  @param Self The source Mat.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for a temporary-view Destination or an
   --  OpenCV failure.
   procedure Bitwise_Not (Self : Mat; Destination : in out Mat);

   --  Masked destination form of Bitwise_Not, under the rules of the masked
   --  Mat Bitwise_And destination form.
   --  @param Self The source Mat.
   --  @param Mask UInt8 single-channel selector of matching shape.
   --  @param Destination The caller-owned Mat that receives the result.
   --  @exception OpenCV_Error Raised for a mismatched Mask, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Bitwise_Not (Self, Mask : Mat; Destination : in out Mat);

   --  Tests each element against inclusive per-channel bounds and returns a
   --  UInt8 C1 mask: an element is set only when every channel lies within
   --  its Lower and Upper components. Supports N-dimensional Mats with at
   --  most four channels. Float16 requires OpenCV 5.0 or later.
   --  @param Self The Mat to test.
   --  @param Lower Inclusive per-channel lower bounds.
   --  @param Upper Inclusive per-channel upper bounds.
   --  @return A new UInt8 C1 mask Mat.
   --  @exception OpenCV_Error Raised for an empty Mat, more than four
   --  channels, an unsupported depth, or an OpenCV failure.
   function In_Range (Self : Mat; Lower, Upper : Scalar) return Mat;

   --  Returns an independent Mat rotated by Kind.  90-degree rotations
   --  exchange rows and columns; a half turn preserves dimensions and every
   --  variant preserves element depth and channel count.
   --  @param Self The Mat to rotate.
   --  @param Kind Rotation to apply.
   --  @return A new Mat with independent storage.
   function Rotate (Self : Mat; Kind : Rotation_Kind) return Mat;

   --  Returns an independent Mat tiled vertically Row_Repetitions times and
   --  horizontally Column_Repetitions times. Element depth and channel count
   --  are preserved. Empty Mats produce an empty result.
   --  @param Self The Mat to tile.
   --  @param Row_Repetitions Number of vertical repetitions.
   --  @param Column_Repetitions Number of horizontal repetitions.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the tiled size is not supported
   --  or OpenCV reports a failure.
   function Repeat
     (Self : Mat; Row_Repetitions : Positive; Column_Repetitions : Positive)
      return Mat;

   --  Concatenates Sources left to right into an independent Mat. Inputs must
   --  have identical row counts and complete element types. Their column
   --  counts may differ. An empty input array produces an empty Mat; empty
   --  individual Mats are accepted when they satisfy the same requirements.
   --  @param Sources The Mats to join, in left-to-right order.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the row counts or element types
   --  differ.
   function HConcat (Sources : Mat_Array) return Mat;

   --  Concatenates Sources top to bottom into an independent Mat. Inputs must
   --  have identical column counts and complete element types. Their row
   --  counts may differ. An empty input array produces an empty Mat; empty
   --  individual Mats are accepted when they satisfy the same requirements.
   --  @param Sources The Mats to join, in top-to-bottom order.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the column counts or element types
   --  differ.
   function VConcat (Sources : Mat_Array) return Mat;

   --  Both operands must be single-channel with identical rows, columns, and
   --  depth.  The result is an independent UInt8 single-channel mask with 255
   --  where the comparison is true and 0 otherwise, suitable for masked ops.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Kind Relation tested, read as Left relation Right.
   --  @return A new UInt8 C1 mask Mat.
   --  @exception OpenCV_Error Raised when the operands are mismatched or
   --  multi-channel, or OpenCV reports a failure.
   function Compare (Left, Right : Mat; Kind : Comparison_Kind) return Mat;

   --  Destination form of Compare. The UInt8 C1 output reuses compatible
   --  whole or Region storage; mismatches detach Destination. Operands retain
   --  the C1 matching 2-D policy of the function. Exact and same-layout
   --  shallow source aliases are supported; other partial overlap is outside
   --  the contract. If both operands are empty, Destination is released.
   --  Temporary inputs are legal, but a temporary Destination is rejected.
   --  @param Left The first operand.
   --  @param Right The second operand, matching Left.
   --  @param Kind Relation tested, read as Left relation Right.
   --  @param Destination The caller-owned Mat that receives the mask.
   --  @exception OpenCV_Error Raised for mismatched operands, a
   --  temporary-view Destination, or an OpenCV failure.
   procedure Compare
     (Left, Right : Mat; Kind : Comparison_Kind; Destination : in out Mat);

   --  Destination form of In_Range. The UInt8 C1 output reuses compatible
   --  whole or Region storage; mismatches detach Destination. Source and
   --  Destination aliasing is outside the contract. An empty Mat is rejected.
   --  Temporary inputs are legal, but a temporary Destination is rejected.
   --  Other rules match the function.
   --  @param Self The Mat to test.
   --  @param Lower Inclusive per-channel lower bounds.
   --  @param Upper Inclusive per-channel upper bounds.
   --  @param Destination The caller-owned Mat that receives the mask.
   --  @exception OpenCV_Error Raised for an empty Mat, a temporary-view
   --  Destination, an unsupported channel count or depth, or an OpenCV
   --  failure.
   procedure In_Range
     (Self : Mat; Lower : Scalar; Upper : Scalar; Destination : in out Mat);

   --  Reports whether Self has no elements, as defined by native Mat empty.
   --  A default header is empty, but an empty result is not necessarily
   --  equivalent to a default header: a typed zero-extent Mat is also empty
   --  and retains its type. Empty-Mat metadata can vary between OpenCV
   --  releases.
   --  @param Self The Mat to inspect.
   --  @return True when the Mat is empty.
   function Is_Empty (Self : Mat) return Boolean;

   --  Returns the row count of a 2-D Mat. Raises OpenCV_Error when native
   --  OpenCV reports no row count because Self has more than two dimensions,
   --  so Rows alone does not describe an N-dimensional shape; use Shape or
   --  Extent for that.
   --  @param Self The Mat to inspect.
   --  @return The number of rows.
   function Rows (Self : Mat) return Natural;

   --  Returns the column count of a 2-D Mat. Raises OpenCV_Error when native
   --  OpenCV reports no column count because Self has more than two
   --  dimensions, so Columns alone does not describe an N-dimensional shape;
   --  use Shape or Extent for that.
   --  @param Self The Mat to inspect.
   --  @return The number of columns.
   function Columns (Self : Mat) return Natural;

   --  Returns every extent in Mat dimension order, indexed 1 ..
   --  Dimension_Count. A default Mat with Dimension_Count = 0 returns a null
   --  Dimension_Array. A typed empty 0 x 0 2-D Mat returns two zero extents.
   --  A normal 2-D Mat returns (1 => Rows, 2 => Columns). A genuine N-D Mat
   --  returns Extent for every axis rather than Rows or Columns. Dimensions
   --  remains the 2-D Size view.
   --  @param Self The Mat to inspect.
   --  @return The extents of all dimensions, in native dimension order.
   function Shape (Self : Mat) return Dimension_Array;

   --  Returns OpenCV's Mat.dims. A genuine default empty Mat reports 0. A
   --  typed 2-D Mat, including Create (0, 0, ...), reports 2.
   --  @param Self The Mat to inspect.
   --  @return The number of dimensions.
   function Dimension_Count (Self : Mat) return Natural;

   --  Returns the extent of 1-based Axis. Axis 1 is OpenCV dimension 0.
   --  Raises OpenCV_Error when Axis is greater than Dimension_Count.
   --  @param Self The Mat to inspect.
   --  @param Axis One-based dimension, in 1 .. Dimension_Count.
   --  @return The extent of that dimension.
   function Extent (Self : Mat; Axis : Positive) return Size_Coordinate;

   --  Returns the 2-D size of Self, composed from the established column and
   --  row queries: Width = Columns, Height = Rows. This operation exists only
   --  for Mat; UMat has no Dimensions function. Like Rows and Columns, it
   --  raises OpenCV_Error for an N-dimensional Mat, so use Shape there.
   --  @param Self The Mat to inspect.
   --  @return Width (columns) and Height (rows).
   function Dimensions (Self : Mat) return Size;

   --  Returns the number of channels in each element. This counts channels,
   --  not bytes; Element_Size gives the byte size of a complete element.
   --  @param Self The Mat to inspect.
   --  @return The channel count.
   function Channels (Self : Mat) return Channel_Count;

   --  Returns the depth of each channel value. Depth is independent of the
   --  channel count, which Channels reports.
   --  @param Self The Mat to inspect.
   --  @return The element depth.
   function Depth (Self : Mat) return Depth_Type;

   --  Returns the native total: the number of matrix elements. A
   --  multi-channel element counts once, and the value is neither a scalar
   --  count nor a byte count.
   --  @param Self The Mat to inspect.
   --  @return The number of elements.
   function Total (Self : Mat) return Mat_Size;

   --  Returns the size in bytes of one complete element, including all of its
   --  channels (native elemSize).
   --  @param Self The Mat to inspect.
   --  @return The byte size of one element.
   function Element_Size (Self : Mat) return Mat_Size;

   --  Returns the size in bytes of one channel of an element (native
   --  elemSize1), as opposed to the complete element size.
   --  @param Self The Mat to inspect.
   --  @return The byte size of one channel.
   function Channel_Size (Self : Mat) return Mat_Size;

   --  Reports whether Self's current layout is continuous, with no gaps
   --  between rows. A Region or slice that shares a larger allocation need
   --  not be continuous. This describes layout, not allocation identity.
   --  @param Self The Mat to inspect.
   --  @return True when the native layout is continuous.
   function Is_Continuous (Self : Mat) return Boolean;

   --  Reports the native Mat submatrix flag. After Adjust_Region the flag is
   --  not recomputed, so it is not authoritative current geometry; use
   --  Locate_Region for the retained allocation geometry.
   --  @param Self The Mat to inspect.
   --  @return The native submatrix flag.
   function Is_Submatrix (Self : Mat) return Boolean;

   --  Creates a distinct Mat header sharing Self's storage for a 2-D ROI.
   --  Rect origins are signed, but a Mat ROI still requires a nonnegative
   --  zero-based origin that lies entirely inside Self. Width and Height
   --  must be positive. Pixels are not deep-copied; the returned header may
   --  share Self's allocation, which persists while any header refers to it.
   --  An invalid Area raises OpenCV_Error. This is a native Region, distinct
   --  from a callback-scoped temporary external Mat view.
   --  @param Self The Mat containing the region.
   --  @param Area Zero-based rectangle selecting the region.
   --  @return A new Mat header that may share Self's allocation.
   function Region (Self : Mat; Area : Rect) return Mat;

   --  Requires a nonempty, exactly 2-D, non-temporary Mat. Describes the
   --  retained original allocation even after the parent variable finalizes.
   --  The result is geometry only and is not an allocation identity: two
   --  unrelated Mats can report identical extents and offsets. Otherwise
   --  OpenCV_Error is raised.
   --  @param Self The Mat to locate.
   --  @return Whole-allocation size and Self's offset within it.
   function Locate_Region (Self : Mat) return Region_Location;

   --  Changes only Self's header, never copies pixels. Positive adjustments
   --  expand and negative adjustments contract; boundaries clip to the parent.
   --  Crossed boundaries are swapped after clipping, as in native OpenCV,
   --  rather than necessarily producing an empty region. Equal boundaries
   --  can produce an empty header, which cannot subsequently be located or
   --  adjusted. Native signed-int overflow raises OpenCV_Error without change.
   --  Unsafe native parent arithmetic or empty-result pointers are likewise
   --  rejected without change.
   --  Whole headers are supported. Continuity is updated; Is_Submatrix is
   --  NOT recomputed and is not authoritative current geometry.
   --  Requires a nonempty, exactly 2-D, non-temporary Mat. Other shallow
   --  headers over the same allocation keep their independent geometry.
   --  Failures are not promised to be transactional beyond the guarantees
   --  stated above.
   --  @param Self The Mat header to adjust.
   --  @param Top Adjustment of the top boundary.
   --  @param Bottom Adjustment of the bottom boundary.
   --  @param Left Adjustment of the left boundary.
   --  @param Right Adjustment of the right boundary.
   procedure Adjust_Region
     (Self : in out Mat; Top, Bottom, Left, Right : Region_Adjustment);

   --  Creates a distinct Mat header sharing Self's storage for one row. No
   --  elements are copied; writes through either header are visible through
   --  the other, and the shared storage persists while any header refers to
   --  it.
   --  @param Self The Mat containing the row.
   --  @param Row Zero-based row index, less than Self.Rows.
   --  @return A new single-row header sharing Self's storage.
   --  @exception OpenCV_Error Raised when Row is outside Self.
   function Row_View (Self : Mat; Row : Size_Coordinate) return Mat;

   --  Creates a distinct Mat header sharing Self's storage for a contiguous
   --  range of rows. Index_Range uses its direct half-open [Start, Stop)
   --  representation, so Stop is the first row excluded. No elements are
   --  copied.
   --  @param Self The Mat containing the rows.
   --  @param Rows Zero-based half-open row range, with Start not greater than
   --  Stop and Stop not greater than Self.Rows.
   --  @return A new header sharing Self's storage.
   --  @exception OpenCV_Error Raised when Rows is inverted or extends past
   --  Self.
   function Row_View (Self : Mat; Rows : Index_Range) return Mat;

   --  Creates a distinct Mat header sharing Self's storage for one column.
   --  No elements are copied; the result is generally not continuous.
   --  @param Self The Mat containing the column.
   --  @param Column Zero-based column index, less than Self.Columns.
   --  @return A new single-column header sharing Self's storage.
   --  @exception OpenCV_Error Raised when Column is outside Self.
   function Column_View (Self : Mat; Column : Size_Coordinate) return Mat;

   --  Creates a distinct Mat header sharing Self's storage for a range of
   --  columns. Index_Range uses its direct half-open [Start, Stop)
   --  representation, so Stop is the first column excluded. No elements are
   --  copied; the result is generally not continuous.
   --  @param Self The Mat containing the columns.
   --  @param Columns Zero-based half-open column range, with Start not
   --  greater than Stop and Stop not greater than Self.Columns.
   --  @return A new header sharing Self's storage.
   --  @exception OpenCV_Error Raised when Columns is inverted or extends
   --  past Self.
   function Column_View (Self : Mat; Columns : Index_Range) return Mat;

   --  Creates a distinct Mat header sharing Self's storage for the selected
   --  N-dimensional half-open ranges. Exactly one range is required for every
   --  dimension. Iteration order maps to OpenCV dimensions regardless of the
   --  array's index bounds. Empty ranges (Start = Stop) are rejected because
   --  OpenCV's N-D range constructor does not accept them consistently from
   --  4.1 through 5.0. The result keeps Self's depth, channel count, and
   --  dimension count; each extent becomes Stop - Start. The slice is not
   --  necessarily contiguous.
   --  @param Self The Mat to slice.
   --  @param Ranges One zero-based half-open range per source dimension.
   --  @return A new Mat header that may share Self's allocation.
   function Slice (Self : Mat; Ranges : Index_Range_Array) return Mat;

   --  Invokes Process with a zero-copy, callback-scoped view of Self that
   --  fixes selected dimensions to one index and DROPS them from the result,
   --  while other dimensions keep ordinary half-open ranges. Exactly one
   --  selector is required for every source dimension, in iteration order;
   --  the array's index bounds are irrelevant.
   --
   --  Keep_Range retains its dimension restricted to Bounds, which must
   --  satisfy Start < Stop <= that source extent (empty ranges are
   --  rejected). Fix_Index requires Index < that source extent and removes
   --  the dimension. The result has one dimension per Keep_Range, in source
   --  order, with extent Stop - Start. Self's depth and channel count are
   --  preserved; one element of a C2/C3/C4 Mat remains one complete vector.
   --
   --  For example, a source of Shape (2, 3, 2, 4) with selections
   --  (Fix_Index 1, Keep_Range [0, 3), Fix_Index 1, Keep_Range [0, 4))
   --  yields a View of Shape (3, 4) whose coordinate (J, K) is source
   --  coordinate (1, J, 1, K).
   --
   --  Requirements, each raising OpenCV_Error before Process is invoked:
   --  Self is nonempty with at least three dimensions; at least one
   --  dimension is fixed; at least two dimensions are kept, so the View has
   --  at least two dimensions (no 1-D or scalar View is produced, and a
   --  one-dimensional result is never promoted to 1 x N or N x 1); and the
   --  FINAL source dimension is kept. The final-dimension rule is an OpenCV
   --  Mat representation requirement, not an implementation shortcut:
   --  OpenCV always uses elemSize() as the step of a Mat's last dimension,
   --  so if the source's final axis were dropped the new last axis would
   --  generally have a larger stride that no ordinary Mat header can
   --  describe without copying.
   --
   --  View shares Self's storage; no data is copied. Writes through View
   --  immediately modify Self and writes through Self are immediately
   --  visible through View. Retained source strides are inherited, so View
   --  may be continuous (for example when only leading dimensions are
   --  dropped) or gapped (dropping a middle dimension keeps the outer
   --  stride). Is_Continuous reports the actual layout, and whole-buffer
   --  borrowing rejects a gapped View while 2-D row borrowing still works.
   --
   --  View is valid only during Process. It keeps Self's allocation alive
   --  for the callback even if Self is rebound or finalized, but it is a
   --  temporary view: shallow copies, Slice, Reshape, and Module_Interop
   --  output handles are rejected. Clone is the escape path and returns
   --  independent storage. Self must not itself be a temporary caller-buffer
   --  Mat view; Clone it first to select from owned storage. Exceptions
   --  raised by Process propagate unchanged, and writes completed through
   --  View before the exception remain visible in Self.
   --  @param Self The Mat to select from; it must not be a temporary
   --  caller-buffer view.
   --  @param Selections One selector per source dimension, in iteration
   --  order.
   --  @param Process Callback that receives the temporary View. The View is
   --  valid only during the call and must not be retained, copied, sliced,
   --  reshaped, or passed to Module_Interop.
   --  @exception OpenCV_Error Raised before Process is invoked when a
   --  selection requirement is violated.
   procedure With_Selected_View
     (Self       : in out Mat;
      Selections : Dimension_Selection_Array;
      Process    : not null access procedure (View : in out Mat));

   --  Sets the calling thread's OpenCV default RNG state. Reseeding that
   --  thread with the same Seed restarts its sequence. Fill_Uniform,
   --  Fill_Normal, and every other OpenCV operation that uses the default RNG
   --  (including K_Means when it consumes that RNG) advance this state. A call
   --  from another thread controls that other thread's independent RNG.
   --  @param Seed The new state seed for the calling thread's default RNG.
   procedure Set_Random_Seed (Seed : Interfaces.Integer_32);

   --  Creates a caller-owned OpenCV 4.10 cv::RNG state. Seed zero maps to the
   --  default state 16#FFFF_FFFF#, matching cv::RNG (uint64).
   --  @param Seed The 64-bit initial state; zero selects 16#FFFF_FFFF#.
   --  @return A new generator, independent of OpenCV's default RNG.
   function Make_Random_Number_Generator
     (Seed : Interfaces.Unsigned_64 := 16#FFFF_FFFF#)
      return Random_Number_Generator;

   --  Restarts Generator at Seed without changing OpenCV's calling-thread
   --  default RNG. Seed zero maps to the default state 16#FFFF_FFFF#.
   --  @param Generator The generator to restart.
   --  @param Seed The 64-bit state; zero selects 16#FFFF_FFFF#.
   procedure Reseed
     (Generator : in out Random_Number_Generator;
      Seed      : Interfaces.Unsigned_64);

   --  Sets every element of Self in place to Value. Self keeps its shape,
   --  depth and channel count; Scalar component N initializes channel N.
   --  Writes go through Self's header, so every header sharing Self's
   --  storage (including a parent of a Region) observes the change.
   --  @param Self The Mat to fill.
   --  @param Value Per-channel fill value; component N is used for channel N.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   procedure Set_To (Self : in out Mat; Value : Scalar);

   --  Sets elements selected by Mask to Value. Mask uses the common mask
   --  contract (UInt8, one channel, same shape as Self). Any nonzero mask
   --  value selects the complete element, including every channel. Elements
   --  not selected by Mask are unchanged.
   --  @param Self The Mat to modify.
   --  @param Value Per-channel fill value; component N is used for channel N.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @exception OpenCV_Error Raised when Mask violates the mask contract or
   --  OpenCV reports a failure.
   procedure Set_To (Self : in out Mat; Value : Scalar; Mask : Mat);

   --  Fills Self in place from OpenCV's default RNG. Each channel uses its
   --  corresponding Scalar bound; generated values are lower-inclusive and
   --  upper-exclusive. Self must be non-empty and have 1 .. 4 channels.
   --  UInt8, Int8, UInt16, Int16, Int32, Float32, Float64, and Float16 are
   --  supported. Non-contiguous Regions are supported and remain Regions.
   --  @param Self The non-empty Mat to fill.
   --  @param Lower_Bound Per-channel inclusive lower bound.
   --  @param Upper_Bound Per-channel exclusive upper bound.
   --  @exception OpenCV_Error Raised for an empty Mat, an unsupported depth
   --  or channel count, or an OpenCV failure.
   procedure Fill_Uniform
     (Self : in out Mat; Lower_Bound, Upper_Bound : Scalar);

   --  As above, using and advancing the supplied caller-owned Generator
   --  instead of the calling thread's default RNG.
   --  @param Self The non-empty Mat to fill.
   --  @param Generator The generator that supplies and records the sequence.
   --  @param Lower_Bound Per-channel inclusive lower bound.
   --  @param Upper_Bound Per-channel exclusive upper bound.
   --  @exception OpenCV_Error Raised for an empty Mat, an unsupported depth
   --  or channel count, or an OpenCV failure.
   procedure Fill_Uniform
     (Self        : in out Mat;
      Generator   : in out Random_Number_Generator;
      Lower_Bound : Scalar;
      Upper_Bound : Scalar);
   --  Fills Self in place from OpenCV's default RNG using one Mean and
   --  Standard_Deviation per channel (the diagonal/vector form only). Self
   --  must be non-empty, have 1 .. 4 channels, and have depth UInt8, Int8,
   --  UInt16, Int16, Int32, Float32, or Float64. Integer results use OpenCV's
   --  saturating conversion/clipping. Float16 is unsupported. Non-contiguous
   --  Regions are supported and remain Regions.
   --  @param Self The non-empty Mat to fill.
   --  @param Mean Per-channel mean.
   --  @param Standard_Deviation Per-channel standard deviation.
   --  @exception OpenCV_Error Raised for an empty Mat, an unsupported depth
   --  or channel count, or an OpenCV failure.
   procedure Fill_Normal
     (Self : in out Mat; Mean : Scalar; Standard_Deviation : Scalar);

   --  As above, using and advancing the supplied caller-owned Generator
   --  instead of the calling thread's default RNG.
   --  @param Self The non-empty Mat to fill.
   --  @param Generator The generator that supplies and records the sequence.
   --  @param Mean Per-channel mean.
   --  @param Standard_Deviation Per-channel standard deviation.
   --  @exception OpenCV_Error Raised for an empty Mat, an unsupported depth
   --  or channel count, or an OpenCV failure.
   procedure Fill_Normal
     (Self               : in out Mat;
      Generator          : in out Random_Number_Generator;
      Mean               : Scalar;
      Standard_Deviation : Scalar);
   --  Randomly permutes Self in place using the calling thread's OpenCV
   --  default RNG, which advances. Set_Random_Seed makes it reproducible
   --  on that thread. Self must be a non-empty 2-D row or column vector.
   --  Complete Mat elements are moved as units, so multi-channel elements keep
   --  their channels together. Valid non-contiguous vector Regions are
   --  supported and retain their shared storage. OpenCV 4.10 supports complete
   --  element sizes of only 1, 2, 3, 4, 6, 8, 12, 16, 24, and 32 bytes.
   --  The order may remain unchanged by chance. Iteration_Factor is not
   --  exposed because OpenCV 4.10's randShuffle implementation ignores it.
   --  @param Self The row or column vector to permute.
   --  @exception OpenCV_Error Raised for an empty Mat, a Mat that is not a
   --  2-D vector, an unsupported element size, or an OpenCV failure.
   procedure Shuffle (Self : in out Mat);

   --  As above, using and advancing the supplied caller-owned Generator
   --  instead of the calling thread's default RNG.
   --  @param Self The row or column vector to permute.
   --  @param Generator The generator that supplies and records the sequence.
   --  @exception OpenCV_Error Raised for an empty Mat, a Mat that is not a
   --  2-D vector, an unsupported element size, or an OpenCV failure.
   procedure Shuffle
     (Self : in out Mat; Generator : in out Random_Number_Generator);

   --  Returns the per-channel sum of every element of Self, computed by
   --  native cv::sum. Scalar holds at most four components, so Mats with more
   --  channels are outside the representable result.
   --  @param Self The Mat to total.
   --  @return A Scalar whose component N is the sum of channel N.
   --  @exception OpenCV_Error Raised when OpenCV rejects Self.
   function Sum (Self : Mat) return Scalar;

   --  Returns the per-channel sum of Self's main diagonal. Rectangular and
   --  empty Mats are accepted. Self must have at most four channels, matching
   --  Scalar's complete representation. Float16 Mats are not supported by
   --  OpenCV's trace implementation. Non-contiguous views are accepted.
   --  @param Self The Mat whose diagonal is summed.
   --  @return A Scalar whose component N is the diagonal sum of channel N.
   --  @exception OpenCV_Error Raised for more than four channels, a Float16
   --  Mat, or an OpenCV failure.
   function Trace (Self : Mat) return Scalar;

   --  Returns the determinant of a non-empty square single-channel Mat as
   --  Long_Float. Self must be Float32 or Float64. 1x1 through 3x3 use
   --  OpenCV's direct formulas; larger matrices use OpenCV LU factorization
   --  with partial pivoting. Singular matrices return 0. Self is not
   --  modified. Non-contiguous Regions are supported. Empty Mats are
   --  rejected, including typed 0x0 matrices. Exact floating-point
   --  arithmetic is not promised for arbitrary matrices.
   --  @param Self The non-empty square single-channel Float32 or Float64 Mat.
   --  @return The determinant, or 0 for a singular matrix.
   --  @exception OpenCV_Error Raised for an empty, non-square or unsupported
   --  Self, or an OpenCV failure.
   function Determinant (Self : Mat) return Long_Float;

   --  Performs ordinary matrix inversion using OpenCV 4.10 DECOMP_LU.
   --  Self must be a non-empty square single-channel Float32 or Float64
   --  Mat. 1x1 through 3x3 use OpenCV's direct paths; larger matrices
   --  use OpenCV LU factorization. A non-singular matrix returns
   --  Invertible True and an Inverse with Self's depth and dimensions
   --  and independently owned storage. A singular matrix returns
   --  Invertible False and does not raise OpenCV_Error. Self is never
   --  modified. Non-contiguous Regions are supported. Empty Mats,
   --  including typed 0x0 matrices, rectangular Mats, multi-channel
   --  Mats, and unsupported depths are rejected. Numerical rounding is
   --  inherent in floating-point inversion.
   --  @param Self The non-empty square single-channel Float32 or Float64 Mat.
   --  @return Invertible True with the Inverse, or Invertible False for a
   --  singular matrix.
   --  @exception OpenCV_Error Raised for an empty, non-square or unsupported
   --  Self, or an OpenCV failure.
   function Invert (Self : Mat) return Inversion_Result;

   --  Solves A * X = B using OpenCV 4.10 DECOMP_LU only. Self is the
   --  coefficient matrix A and must be a non-empty square single-channel
   --  Float32 or Float64 Mat. Right_Hand_Side is B and must be a
   --  non-empty single-channel Mat with Self's depth and row count.
   --  B may contain one or more columns. A unique solution returns
   --  Solved True and a Solution of shape Self.Columns x
   --  Right_Hand_Side.Columns with the same floating depth and
   --  independently owned storage. A singular A returns Solved False
   --  and does not raise OpenCV_Error; no Solution Mat is exposed.
   --  Both inputs remain unchanged. Non-contiguous Regions are
   --  accepted. This is not a least-squares or pseudo-solution API.
   --  Numerical rounding is inherent in floating-point solution.
   --  @param Self The square coefficient matrix A.
   --  @param Right_Hand_Side The matrix B, with one row per row of Self.
   --  @return Solved True with the Solution, or Solved False for a singular
   --  A.
   --  @exception OpenCV_Error Raised when an operand violates the stated
   --  shape, depth or channel requirements or OpenCV reports a failure.
   function Solve (Self : Mat; Right_Hand_Side : Mat) return Solve_Result;

   --  Finds real roots with OpenCV 4.10 cv::solveCubic, unlike Solve
   --  which solves a linear system. Coefficients must be a non-empty,
   --  single-channel Float32 or Float64 vector of shape 1 x 3, 3 x 1, 1 x 4,
   --  or 4 x 1. Three coefficients represent x**3 + A*x**2 + B*x + C = 0;
   --  four represent A*x**3 + B*x**2 + C*x + D = 0. A zero leading A in the
   --  four-coefficient form is valid and reduces the equation to quadratic,
   --  linear, or constant. Status is OpenCV's reported root count rather
   --  than a guaranteed count of mathematically distinct roots; repeated-
   --  root polynomials may report a duplicate value. Roots is present only
   --  for a finite positive count, is independently owned, has the
   --  coefficient depth, and has only the Status-selected leading entries
   --  valid to inspect. Root ordering is not guaranteed. Coefficients are
   --  unchanged, and non-contiguous Regions are accepted.
   --  @param Coefficients The 3- or 4-element coefficient vector.
   --  @return The reported root count and, for a finite positive count, the
   --  roots.
   --  @exception OpenCV_Error Raised when Coefficients violates the stated
   --  shape, channel or depth requirements or OpenCV reports a failure.
   function Solve_Cubic (Coefficients : Mat) return Cubic_Solution_Result;

   --  Finds the complex roots of a polynomial with OpenCV cv::solvePoly.
   --  Coefficients is a non-empty row or column vector of at least two
   --  Float32 or Float64 coefficients with one channel (real) or two channels
   --  (real and imaginary parts), holding the constant term first so that
   --  coefficient I multiplies x**I. Trailing high-order coefficients whose
   --  absolute-value sum is at most DBL_EPSILON are discarded to find the
   --  effective degree. A constant or identically-zero polynomial is
   --  rejected. The roots are returned in an independently owned effective-
   --  degree x 1 C2 Mat, and Coefficients is unchanged.
   --  @param Coefficients The polynomial coefficient vector.
   --  @param Maximum_Iterations Iteration limit passed to OpenCV, at most the
   --  signed 32-bit range.
   --  @return The roots and the maximum correction reported by OpenCV.
   --  @exception OpenCV_Error Raised for an empty or non-vector
   --  Coefficients, an unsupported depth or channel count, fewer than two
   --  coefficients, a constant or zero polynomial, a degree beyond OpenCV's
   --  safe range, or an OpenCV failure.
   function Solve_Polynomial
     (Coefficients : Mat; Maximum_Iterations : Positive := 300)
      return Polynomial_Solution_Result;
   --  Returns the scalar dot product of Self and Other as Long_Float,
   --  corresponding to OpenCV 4.10 cv::Mat::dot's double. This is the
   --  sum of every corresponding spatial-element and channel product.
   --  It is not algebraic Matrix_Multiply, not element-wise Multiply,
   --  and not a complex or Hermitian inner product. Self and Other
   --  must both be non-empty and must share identical Rows, Columns,
   --  Depth, and channel count. A 1x3 C1 Mat and a 3x1 C1 Mat are
   --  incompatible; shapes are not flattened. Supported depths are
   --  UInt8, Int8, UInt16, Int16, Int32, Float32, and Float64.
   --  Float16 is rejected. Multi-channel Mats are supported; every
   --  corresponding channel component is included. Two-channel values
   --  are ordinary scalar channels, unlike Matrix_Multiply which
   --  treats Float32/Float64 C2 as OpenCV complex matrices. Empty
   --  Mats, including typed 0x0 operands, are rejected. Continuity
   --  is not required; non-contiguous Regions are supported. Inputs
   --  are unchanged. Exact SIMD accumulation order and
   --  architecture-identical floating results are not promised.
   --  @param Self The first operand.
   --  @param Other The second operand, matching Self in shape and type.
   --  @return The sum of all corresponding element-channel products.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Dot_Product (Self : Mat; Other : Mat) return Long_Float;

   --  Returns the scalar Mahalanobis distance of Self and Other as
   --  Long_Float, corresponding to OpenCV 4.10 cv::Mahalanobis's
   --  double. This is the weighted distance
   --  sqrt ((Self - Other)' * Inverse_Covariance * (Self - Other)).
   --  Self and Other are mathematical one-dimensional vectors: non-empty
   --  single-channel Float32 or Float64 row (1 x N) or column (N x 1)
   --  Mats with identical shape and complete type. A 1xN row and an Nx1
   --  column of the same length are incompatible; shapes are not
   --  flattened. An arbitrary M x N matrix is rejected even when
   --  OpenCV's implementation would treat width*height*channels as a
   --  vector. Inverse_Covariance must be a non-empty single-channel Mat
   --  with the same depth as the vectors and exactly N x N. Empty Mats,
   --  including typed empty vectors, integer depths, Float16, and
   --  multi-channel operands are rejected. Continuity is not required;
   --  non-contiguous Regions are supported. Inputs are unchanged.
   --  @param Self The first vector.
   --  @param Other The second vector, matching Self in shape and type.
   --  @param Inverse_Covariance The N x N inverse covariance matrix.
   --  @return The Mahalanobis distance.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Mahalanobis_Distance
     (Self : Mat; Other : Mat; Inverse_Covariance : Mat) return Long_Float;

   --  Returns the three-dimensional vector cross product Self x Other
   --  using OpenCV 4.10 cv::Mat::cross. This is not element-wise
   --  Multiply and not algebraic Matrix_Multiply. Operand order
   --  matters: reversing the operands negates the result. Self and
   --  Other must both be non-empty and must share identical Rows,
   --  Columns, Depth, and channel count. Each operand must be one
   --  three-component vector in exactly one of these representations:
   --  3x1 C1, 1x3 C1, or 1x1 C3. A 3x1 C1 Mat and a 1x3 C1 Mat are
   --  incompatible; shapes are not flattened. Unusual combinations
   --  that happen to contain three scalars, including 3x1 C3, are
   --  rejected. Supported depths are Float32 and Float64. Integer
   --  depths and Float16 are rejected. Empty Mats, including typed
   --  empty vectors, are rejected. Continuity is not required;
   --  non-contiguous Regions are supported. Inputs are unchanged.
   --  The independently owned result has Self's Rows, Columns, Depth,
   --  and channel count.
   --  @param Self The first three-component vector.
   --  @param Other The second three-component vector, matching Self.
   --  @return A new Mat holding Self x Other, with independent storage.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Cross_Product (Self : Mat; Other : Mat) return Mat;

   --  Performs algebraic matrix multiplication Result = Left * Right
   --  using OpenCV 4.10 cv::gemm. This is not the existing element-wise
   --  Multiply. Left.Columns must equal Right.Rows; the independently
   --  owned result has shape Left.Rows x Right.Columns and the same
   --  complete element type as both operands. Operands need not be
   --  square. Both operands must be non-empty and must share an
   --  identical complete element type of Float32 or Float64 with one
   --  channel (real) or two channels (complex). Two-channel values use
   --  OpenCV complex multiplication, with channel 0 as the real part
   --  and channel 1 as the imaginary part. Unsupported depths and
   --  other channel counts are rejected. Continuity is not required;
   --  non-contiguous Regions are supported. Inputs are unchanged.
   --  @param Left The left factor.
   --  @param Right The right factor, with Right.Rows = Left.Columns.
   --  @return The product, with independent storage.
   --  @exception OpenCV_Error Raised for empty, incompatible or unsupported
   --  operands, or an OpenCV failure.
   function Matrix_Multiply (Left, Right : Mat) return Mat;

   --  Computes Result = Product_Scale * Left * Right + Addend_Scale *
   --  Addend using OpenCV 4.10 cv::gemm. This is algebraic matrix
   --  multiplication followed by matrix addition. It is not the
   --  existing element-wise Multiply, Scale_Add, or Add_Weighted.
   --  Left.Columns must equal Right.Rows; Addend must have the exact
   --  product shape Left.Rows x Right.Columns. The independently owned
   --  result has that shape and the same complete element type as all
   --  three operands. Operands need not be square. All three operands
   --  must be non-empty and must share an identical complete element
   --  type of Float32 or Float64 with one channel (real) or two
   --  channels (complex). Two-channel values use OpenCV complex
   --  arithmetic, with channel 0 as the real part and channel 1 as the
   --  imaginary part. Product_Scale and Addend_Scale are real scalar
   --  weights. Addend is validated even when Addend_Scale is 0.0. No
   --  transpose behavior is part of this API. Unsupported depths and
   --  other channel counts are rejected. Continuity is not required;
   --  non-contiguous Regions are supported. Inputs are unchanged.
   --  Float32 scaling follows OpenCV's Float32 numerical behavior.
   --  @param Left The left factor.
   --  @param Right The right factor, with Right.Rows = Left.Columns.
   --  @param Addend The matrix added to the scaled product, with shape
   --  Left.Rows x Right.Columns.
   --  @param Product_Scale Real weight applied to Left * Right.
   --  @param Addend_Scale Real weight applied to Addend.
   --  @return The result, with independent storage.
   --  @exception OpenCV_Error Raised for empty, incompatible or unsupported
   --  operands, or an OpenCV failure.
   function Matrix_Multiply_Add
     (Left, Right   : Mat;
      Addend        : Mat;
      Product_Scale : Long_Float := 1.0;
      Addend_Scale  : Long_Float := 1.0) return Mat;

   --  Computes the uncentered transposed product of Self using
   --  OpenCV 4.10 cv::mulTransposed with no Delta. Transpose_Times_Self
   --  computes Scale * Self'T * Self and yields a Self.Columns x
   --  Self.Columns result. Self_Times_Transpose computes Scale * Self
   --  * Self'T and yields a Self.Rows x Self.Rows result. Order has no
   --  default. Self must be non-empty and single-channel. Supported
   --  source depths are UInt8, UInt16, Int16, Float32, and Float64.
   --  Int8, Int32, Float16, and multi-channel Mats are rejected.
   --  Automatic output depth follows the OpenCV 4.10 implementation,
   --  not the documentation's dtype=-1 claim: Float64 sources produce
   --  Float64 and every other supported source produces Float32.
   --  Explicit Output_Depth may be Float32 or Float64. Float64 source
   --  with Float32 output is rejected because OpenCV 4.10 has no such
   --  kernel. Scale is applied to the complete product and may be
   --  positive, zero, negative, or fractional. The result is
   --  symmetric, owns independent storage, and does not modify Self.
   --  Continuity is not required; non-contiguous Regions are
   --  supported. Delta/centering is not part of this API.
   --  @param Self The source Mat.
   --  @param Order Whether Self'T * Self or Self * Self'T is computed.
   --  @param Scale Factor applied to the complete product.
   --  @return A new symmetric Mat with automatic output depth.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self or an
   --  OpenCV failure.
   function Transposed_Product
     (Self : Mat; Order : Transposed_Product_Order; Scale : Long_Float := 1.0)
      return Mat;

   --  Uncentered transposed product with an explicit result depth. The
   --  source rules, scale rules and result shape match the automatic-depth
   --  overload; Output_Depth must be Float32 or Float64, and a Float64 source
   --  cannot produce Float32 output.
   --  @param Self The source Mat.
   --  @param Order Whether Self'T * Self or Self * Self'T is computed.
   --  @param Output_Depth Depth of the result, Float32 or Float64.
   --  @param Scale Factor applied to the complete product.
   --  @return A new symmetric Mat of depth Output_Depth.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, an
   --  unsupported Output_Depth, or an OpenCV failure.
   function Transposed_Product
     (Self         : Mat;
      Order        : Transposed_Product_Order;
      Output_Depth : Depth_Type;
      Scale        : Long_Float := 1.0) return Mat;

   --  Computes the centered transposed product of Self using
   --  OpenCV 4.10 cv::mulTransposed with a required non-empty Offset
   --  (OpenCV's delta). Offset is subtracted, with OpenCV
   --  broadcasting, before the product. Transpose_Times_Self computes
   --  Scale * (Self - Offset)'T * (Self - Offset) and yields a
   --  Self.Columns x Self.Columns result. Self_Times_Transpose
   --  computes Scale * (Self - Offset) * (Self - Offset)'T and yields
   --  a Self.Rows x Self.Rows result. Order has no default. Offset
   --  must be non-empty; a default empty Mat or typed 0x0 Mat is
   --  rejected rather than treated as the uncentered form. Accepted
   --  Offset shapes for Self M x N are M x N, 1 x N, M x 1, and 1 x 1.
   --  Self and Offset must each be single-channel. Self keeps the
   --  uncentered source-depth contract: UInt8, UInt16, Int16,
   --  Float32, or Float64. Offset may be UInt8, Int8, UInt16, Int16,
   --  Int32, Float32, or Float64; Float16 Offset is rejected. OpenCV
   --  converts Offset to the effective computation depth. Automatic
   --  output is Float64 when Self or Offset is Float64 and Float32
   --  otherwise. Explicit Float32 rejects Float64 Self or Offset so
   --  the returned Mat is actually Float32. Explicit Float64 accepts
   --  every supported Self/Offset combination. Scale is applied to the
   --  completed centered product. Continuity is not required.
   --  Inputs remain unchanged. The result owns independent storage.
   --  This is a general centered transposed product; covariance
   --  construction is one use, not the only meaning. The formal is
   --  named Offset because Ada reserves Delta.
   --  @param Self The source Mat.
   --  @param Offset The non-empty Mat subtracted from Self before the
   --  product, broadcast by OpenCV.
   --  @param Order Whether the transposed-times-self or self-times-transposed
   --  form is computed.
   --  @param Scale Factor applied to the completed centered product.
   --  @return A new symmetric Mat with automatic output depth.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self or
   --  Offset, an incompatible Offset shape, or an OpenCV failure.
   function Transposed_Product
     (Self   : Mat;
      Offset : Mat;
      Order  : Transposed_Product_Order;
      Scale  : Long_Float := 1.0) return Mat;

   --  Centered transposed product with an explicit result depth. The source,
   --  Offset, scale and result-shape rules match the automatic-depth
   --  centered overload. An explicit Float32 depth rejects a Float64 Self or
   --  Offset; an explicit Float64 depth accepts every supported combination.
   --  @param Self The source Mat.
   --  @param Offset The non-empty Mat subtracted from Self before the
   --  product, broadcast by OpenCV.
   --  @param Order Whether the transposed-times-self or self-times-transposed
   --  form is computed.
   --  @param Output_Depth Depth of the result, Float32 or Float64.
   --  @param Scale Factor applied to the completed centered product.
   --  @return A new symmetric Mat of depth Output_Depth.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self or
   --  Offset, an incompatible Offset shape, an unsupported Output_Depth, or
   --  an OpenCV failure.
   function Transposed_Product
     (Self         : Mat;
      Offset       : Mat;
      Order        : Transposed_Product_Order;
      Output_Depth : Depth_Type;
      Scale        : Long_Float := 1.0) return Mat;

   --  Calculates the normal feature covariance matrix and mean of
   --  Self using OpenCV 4.10 cv::calcCovarMatrix. Self is a 2-D
   --  single-channel sample matrix. Samples_Are_Rows, the default,
   --  treats an M x N Mat as M samples of N features: Mean is 1 x N
   --  and Covariance is N x N. Samples_Are_Columns treats an M x N
   --  Mat as N samples of M features: Mean is M x 1 and Covariance
   --  is M x M. The scrambled/sample-space covariance form is not
   --  part of this API. OpenCV always computes Mean; a caller-
   --  supplied average is not accepted. Unscaled returns the raw
   --  centered accumulation. By_Sample_Count, the default, divides
   --  that accumulation by the selected sample count N. That factor
   --  is 1/N, matching OpenCV COVAR_SCALE; it is not 1/(N - 1) and
   --  is not unbiased sample covariance. Self must be non-empty and
   --  Float32 or Float64. The selected orientation must contain at
   --  least one sample. Multi-channel Mats, integer depths, and
   --  Float16 are rejected. Output Covariance and Mean preserve
   --  Self's floating-point depth and are independently owned. The
   --  caller does not preallocate either output. Continuity is not
   --  required; non-contiguous Regions are supported. Self is
   --  unchanged.
   --  @param Self The 2-D single-channel Float32 or Float64 sample matrix.
   --  @param Orientation Whether samples are the rows or the columns of Self.
   --  @param Scaling Whether the accumulation is left raw or divided by the
   --  sample count.
   --  @return The covariance matrix and the mean, in independent storage.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, no
   --  samples in the chosen orientation, or an OpenCV failure.
   function Covariance
     (Self        : Mat;
      Orientation : Sample_Orientation := Samples_Are_Rows;
      Scaling     : Covariance_Scaling := By_Sample_Count)
      return Covariance_Result;

   --  Decomposes a real symmetric matrix using OpenCV 4.10 cv::eigen.
   --  Self must be a non-empty square single-channel Float32 or
   --  Float64 Mat that represents a real symmetric matrix. This is
   --  not PCA, SVD, or a non-symmetric eigen solver. OpenCV 4.10
   --  does not validate symmetry and defines no symmetry
   --  tolerance. Its symmetric eigensolver backends assume
   --  self-adjoint input rather than comparing Self with its
   --  transpose. A non-symmetric input is therefore a
   --  caller-precondition violation and may produce misleading
   --  output rather than a rejection. This binding does not invent a
   --  floating-point symmetry check. Multi-channel Mats, integer
   --  depths, and Float16 are rejected. The matrix dimension N must
   --  not exceed 8_460. OpenCV 4.10's fallback symmetric eigensolver
   --  computes an internal iteration bound using signed integer
   --  arithmetic that is not safe for larger dimensions. Outputs
   --  preserve Self's floating-point depth. For an N x N source,
   --  Eigenvalues is N x 1 with values stored from largest to
   --  smallest, and Eigenvectors is N x N with one eigenvector per
   --  row so that row i corresponds
   --  to eigenvalue i. Eigenvector sign is mathematically arbitrary:
   --  v and -v represent the same eigenvector. Both OpenCV 4.10
   --  backends produce orthonormal eigenvectors; a repeated
   --  eigenspace does not have a unique basis. Continuity is not
   --  required; non-contiguous Regions are supported. Self is
   --  unchanged. Both outputs are independently owned. The caller
   --  does not preallocate either output. A valid matrix satisfying

   --  this contract yields a populated result. An OpenCV numerical
   --  failure (cv::eigen returning false) raises OpenCV_Error rather
   --  than exposing a Boolean.
   --  @param Self The real symmetric matrix; symmetry is a caller
   --  precondition that is not checked.
   --  @return Eigenvalues (largest first) and the corresponding eigenvectors
   --  stored by row.
   --  @exception OpenCV_Error Raised for an empty, non-square or unsupported
   --  Self, a dimension above 8_460, or a numerical failure in OpenCV.
   function Eigen_Decomposition (Self : Mat) return Eigen_Decomposition_Result;

   --  Computes the real non-symmetric eigendecomposition using OpenCV 4.10
   --  cv::eigenNonSymmetric. Self must be a non-empty square Float32 or
   --  Float64 single-channel Mat with dimension at most 2_147_483. Unlike
   --  Eigen_Decomposition, symmetry is not required. All eigenvalues must be
   --  real; this is an OpenCV caller precondition, and this binding does not
   --  invent a numerical complex-eigenvalue detector. Eigenvalues are ordered
   --  from largest to smallest, and each corresponding eigenvector is stored
   --  in a row. Eigenvector sign is arbitrary, and repeated eigenspaces need
   --  not have unique bases. Non-contiguous Regions are supported. Self is
   --  unchanged; both result Mats are independently owned and independent of
   --  Self and each other.
   --  @param Self The real square matrix, whose eigenvalues must all be real.
   --  @return Eigenvalues (largest first) and the corresponding eigenvectors
   --  stored by row.
   --  @exception OpenCV_Error Raised for an empty, non-square or unsupported
   --  Self, an oversized dimension, or an OpenCV failure.
   function Non_Symmetric_Eigen_Decomposition
     (Self : Mat) return Eigen_Decomposition_Result;

   --  Computes a supervised Linear Discriminant Analysis basis using OpenCV
   --  4.10 cv::LDA. Samples is an N x D row-aligned matrix: each row is one
   --  observation and each column is one feature. Samples must be non-empty,
   --  single-channel, Float32 or Float64, and finite. Labels must be a
   --  non-empty Int32 C1 row (1 x N) or column (N x 1) vector. Arbitrary
   --  signed Int32 label values are accepted, but at least two distinct
   --  classes are required. Inputs are unchanged and non-contiguous Regions
   --  are supported.
   --
   --  The result is always Float64: Eigenvalues is K x 1 and Eigenvectors is
   --  D x K, with discriminant directions stored by column, so Samples *
   --  Eigenvectors projects row-aligned samples. Eigenvalues are descending;
   --  eigenvector signs are arbitrary. The automatic count is
   --  K = min (class count - 1, D). The explicit overload requires Components
   --  not exceed that value. This computes a discriminant subspace, not a
   --  classifier, and does not add projection or reconstruction wrappers.
   --  Singular or ill-conditioned within-class scatter can yield degenerate
   --  numerical results under OpenCV 4.10. OpenCV warns to stdout when N < D;
   --  this binding preserves that native behavior rather than rejecting it.
   --  D must not exceed 8460 because OpenCV 4.10's internal LDA eigensolver
   --  can use either a non-symmetric path or the symmetric cv::eigen fallback;
   --  this signed-arithmetic safety limit covers both paths.
   --  @param Samples The N x D matrix of observations, one per row.
   --  @param Labels Int32 C1 row or column vector holding the class label of
   --  each observation.
   --  @return Discriminant eigenvalues and eigenvectors, using the automatic
   --  component count.
   --  @exception OpenCV_Error Raised for empty or unsupported operands,
   --  fewer than two classes, a feature count above 8460, or an OpenCV
   --  failure.
   function Linear_Discriminant_Analysis
     (Samples : Mat; Labels : Mat) return Linear_Discriminant_Analysis_Result;

   --  Explicit-component form of Linear_Discriminant_Analysis. Components must
   --  not exceed the automatic count min (class count - 1, D); other rules
   --  match the automatic overload.
   --  @param Samples The N x D matrix of observations, one per row.
   --  @param Labels Int32 C1 row or column vector holding the class label of
   --  each observation.
   --  @param Components Number of discriminant directions to retain.
   --  @return Discriminant eigenvalues and eigenvectors with K = Components.
   --  @exception OpenCV_Error Raised for empty or unsupported operands,
   --  fewer than two classes, too many Components, a feature count above
   --  8460, or an OpenCV failure.
   function Linear_Discriminant_Analysis
     (Samples : Mat; Labels : Mat; Components : Positive)
      return Linear_Discriminant_Analysis_Result;

   --  Projects row-aligned samples through an already computed LDA basis;
   --  this does not recompute Linear_Discriminant_Analysis. If W is
   --  Basis.Eigenvectors, this converts Self to W's precision and computes
   --  Self * W. There is no centering. Self is N x D, where each row is a
   --  sample, and W is D x K with directions stored by column; the
   --  independently owned result is N x K. Self must be non-empty,
   --  single-channel Float32 or Float64 with at least one row and D columns.
   --  Basis.Eigenvectors must be non-empty Float64 C1 D x K with D >= 1,
   --  K >= 1, and K <= D. Basis.Eigenvalues is unused. Binding-produced LDA
   --  bases therefore produce Float64 C1 results. Continuity is not required;
   --  non-contiguous Regions are supported. Self and Basis are unchanged.
   --  The result owns independent storage. Finite sample and basis values are
   --  a caller precondition; this binding does not replace NaN or Infinity.
   --  @param Self The N x D samples to project, one per row.
   --  @param Basis A previously computed LDA result; only Eigenvectors is
   --  used.
   --  @return The N x K projected coordinates.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function LDA_Project
     (Self : Mat; Basis : Linear_Discriminant_Analysis_Result) return Mat;

   --  Reconstructs row-aligned feature-space values from LDA coordinates;
   --  this does not recompute Linear_Discriminant_Analysis. If W is
   --  Basis.Eigenvectors, this converts Self to W's precision and computes
   --  Self * W^T. There is no mean restoration. Self is N x K projected
   --  coordinates and W is D x K; the independently owned result is N x D.
   --  This is not an inverse transform: LDA eigenvectors are not guaranteed
   --  orthonormal, so LDA_Reconstruct (LDA_Project (X, Basis), Basis) is
   --  not guaranteed to reproduce X. Self must be non-empty, single-channel
   --  Float32 or Float64 with at least one row and K columns.
   --  Basis.Eigenvectors must be non-empty Float64 C1 D x K with D >= 1,
   --  K >= 1, and K <= D. Basis.Eigenvalues is unused. Binding-produced LDA
   --  bases therefore produce Float64 C1 results. Continuity is not required;
   --  non-contiguous Regions are supported. Self and Basis are unchanged.
   --  The result owns independent storage. Finite coordinate and basis
   --  values are a caller precondition; this binding does not replace NaN
   --  or Infinity.
   --  @param Self The N x K projected coordinates, one sample per row.
   --  @param Basis A previously computed LDA result; only Eigenvectors is
   --  used.
   --  @return The N x D reconstructed feature-space values.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function LDA_Reconstruct
     (Self : Mat; Basis : Linear_Discriminant_Analysis_Result) return Mat;

   --  Computes the default compact/economy SVD of Self using OpenCV
   --  4.10 cv::SVD::compute with flags = 0. This is not PCA, a
   --  symmetric eigen solver, or a full-size SVD. Self is treated as
   --  the mathematical matrix A exactly as stored; no orientation
   --  parameter is required. The decomposition satisfies
   --  A ~= U * diag (Singular_Values) * V_Transpose subject to
   --  ordinary floating-point rounding. Let R = min (Rows, Columns).
   --  Singular_Values is R x 1, U is Rows x R, and V_Transpose is
   --  R x Columns. Those compact shapes apply to tall, square, and
   --  wide matrices. Singular values are nonnegative and sorted from
   --  largest to smallest. Self must be a non-empty single-channel
   --  Float32 or Float64 Mat. Multi-channel Mats, integer depths, and
   --  Float16 are rejected. Square shape, full rank, and
   --  nonsingularity are not required. Rank-deficient matrices and
   --  zero singular values are valid. Singular-vector signs are
   --  arbitrary: corresponding columns of U and rows of V_Transpose
   --  may simultaneously change sign. A repeated or zero singular
   --  value does not have a unique basis within its singular
   --  subspace. Outputs preserve Self's floating-point depth and are
   --  independently owned. The caller does not preallocate any
   --  output. Continuity is not required; non-contiguous Regions are
   --  supported. Self is unchanged.
   --  @param Self The non-empty single-channel Float32 or Float64 matrix.
   --  @return Singular values, U, and V_Transpose in compact form.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self or an
   --  OpenCV failure.
   function Singular_Value_Decomposition
     (Self : Mat) return Singular_Value_Decomposition_Result;

   --  Solves A * X ~= Right_Hand_Side from an already computed
   --  compact SVD basis using OpenCV 4.10 cv::SVD::backSubst. This
   --  does not recompute the SVD, does not reconstruct A, and does
   --  not expose cv::SVD. The mathematical operation is
   --  X ~= V * diag (W)^+ * U^T * Right_Hand_Side, where the
   --  reciprocal of sufficiently small singular values is omitted
   --  according to OpenCV 4.10's internal threshold. There is no
   --  caller-configurable tolerance. For a full-rank square system
   --  this behaves like solving A * X = B. For an overdetermined
   --  system (M > N) it returns the SVD least-squares solution. For
   --  an underdetermined system (M < N) it returns the SVD
   --  minimum-norm solution. Rank-deficient bases are accepted;
   --  near-zero singular directions are discarded by OpenCV rather
   --  than rejected here. Basis is a publicly constructible record,
   --  so its compact structure is validated before the ABI. Let
   --  M = Basis.U.Rows, N = Basis.V_Transpose.Columns, and
   --  R = Basis.Singular_Values.Rows. Singular_Values must be a
   --  non-empty single-channel Float32 or Float64 R x 1 column with
   --  R >= 1. U must be a non-empty single-channel Mat of the same
   --  depth and shape M x R with M >= 1. V_Transpose must be a
   --  non-empty single-channel Mat of the same depth and shape
   --  R x N with N >= 1. The compact identity R = min (M, N) is
   --  required; FULL_UV layouts are rejected. Right_Hand_Side must
   --  be a non-empty single-channel Mat of the same depth, M rows,
   --  and K >= 1 columns. Empty RHS is rejected; this is not a
   --  pseudoinverse API. Depths are not converted: Float32 Basis
   --  plus Float32 RHS yields a Float32 result, and Float64 Basis
   --  plus Float64 RHS yields a Float64 result. The independently
   --  owned result has shape N x K. The products N * K and M * R
   --  must not exceed 2_147_483_647 because OpenCV 4.10 forms
   --  destination and U element addresses with signed int index
   --  arithmetic. Continuity is not required; ordinary
   --  non-contiguous Regions are supported subject to OpenCV 4.10's
   --  signed-index limits on inherited physical row strides. Basis
   --  fields and Right_Hand_Side are unchanged.
   --  @param Basis A compact SVD result describing A.
   --  @param Right_Hand_Side The matrix B, with M rows.
   --  @return The N x K solution, in independent storage.
   --  @exception OpenCV_Error Raised for a malformed Basis, a mismatched or
   --  empty Right_Hand_Side, a product beyond the stated limit, or an OpenCV
   --  failure.
   function SVD_Back_Substitute
     (Basis : Singular_Value_Decomposition_Result; Right_Hand_Side : Mat)
      return Mat;

   --  Returns the Moore-Penrose pseudoinverse of Self using compact
   --  OpenCV 4.10 SVD and empty-RHS SVD back substitution. This is
   --  not Invert, Solve, or a caller-tunable rank decision. Self of
   --  shape M x N yields an independently owned N x M result with
   --  Self's floating depth and one channel. Self must be a
   --  non-empty single-channel Float32 or Float64 Mat. Multi-channel
   --  Mats, integer depths, and Float16 are rejected. Square,
   --  tall, and wide shapes are supported. Full rank and
   --  nonsingularity are not required. Rank-deficient matrices and
   --  the zero matrix are valid. Numerical rank follows OpenCV
   --  4.10's SVD back-substitution threshold; there is no caller
   --  tolerance. For a square nonsingular matrix the result agrees
   --  numerically with Invert.Inverse subject to ordinary
   --  floating-point rounding. Continuity is not required;
   --  non-contiguous Regions are supported. The product
   --  Self.Rows * Self.Columns must not exceed 2_147_483_647
   --  because OpenCV 4.10 forms the packed N x M destination
   --  address with signed int index arithmetic. Self is unchanged.
   --  @param Self The non-empty single-channel Float32 or Float64 matrix.
   --  @return The N x M pseudoinverse, in independent storage.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, a
   --  size beyond the stated limit, or an OpenCV failure.
   function Pseudo_Inverse (Self : Mat) return Mat;

   --  Returns the reciprocal 2-norm condition number of Self:
   --  sigma_min / sigma_max. Singular values come from OpenCV 4.10
   --  SVD. Compact rank is R = min (Rows, Columns), so the values
   --  are sigma_1 >= ... >= sigma_R >= 0 and the result is
   --  sigma_R / sigma_1 when sigma_1 > 0. A result of 1.0 means
   --  well / perfectly conditioned. Values approaching 0 indicate
   --  ill conditioning. If the largest singular value is exactly 0,
   --  the result is 0.0 rather than 0 / 0. Singular and zero
   --  matrices are valid and return 0.0 when the smallest singular
   --  value is zero. Square, tall, and wide matrices are supported.
   --  Self must be a non-empty single-channel Float32 or Float64
   --  Mat. Multi-channel Mats, integer depths, and Float16 are
   --  rejected. Computation uses singular values only; U and
   --  V_Transpose are not required. The result is scale invariant
   --  subject to floating-point representability and rounding:
   --  rcond (c * A) = rcond (A) for nonzero scalar c. This is the
   --  ratio of the singular values OpenCV actually computes, not
   --  the pseudoinverse / SVD back-substitution numerical-rank
   --  threshold and not cv::invert (DECOMP_SVD)'s scale-dependent
   --  return metric. There is no caller tolerance. Continuity is
   --  not required; non-contiguous Regions are supported. Self is
   --  unchanged. Ordinary floating-point rounding applies.
   --  @param Self The non-empty single-channel Float32 or Float64 matrix.
   --  @return sigma_min / sigma_max, or 0.0 when sigma_max is zero.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self or an
   --  OpenCV failure.
   function Reciprocal_Condition_Number (Self : Mat) return Long_Float;

   --  Returns an independently owned unit-length N x 1 vector minimizing
   --  ||Self * X|| for an M x N source, directly using OpenCV 4.10
   --  cv::SVD::solveZ. This is an SVD null/minimum-residual vector, not an
   --  ordinary linear-system solution. For a nontrivial null space it is a
   --  null-space direction and Self * X is approximately zero; otherwise it
   --  is the right singular vector for the smallest singular value. Its sign
   --  is arbitrary. Self must be non-empty Float32 or Float64 C1; square,
   --  tall, and wide Mats are accepted, including non-contiguous Regions.
   --  Wide Mats use OpenCV's internal FULL_UV behavior to obtain the complete
   --  right-singular basis. Otherwise valid inputs are rejected when OpenCV
   --  4.10's internal SVD temporary-workspace arithmetic would overflow the
   --  host allocation size. Self is unchanged, and there is no caller
   --  tolerance.
   --  @param Self The non-empty Float32 or Float64 C1 matrix.
   --  @return A new N x 1 unit vector with independent storage.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, a
   --  workspace size beyond the stated limit, or an OpenCV failure.
   function SVD_Solve_Zero (Self : Mat) return Mat;

   --  Computes the PCA basis of Self using OpenCV 4.10 cv::PCA.
   --  Self is a 2-D single-channel sample matrix. Samples_Are_Rows,
   --  the default, treats an M x N Mat as M samples of N features:
   --  Mean is 1 x N. Samples_Are_Columns treats an M x N Mat as N
   --  samples of M features: Mean is M x 1. Available component
   --  count K_all is min (sample count, feature count). The
   --  no-Components overload retains every OpenCV PCA component, so
   --  K = K_all. That is the number OpenCV computes, not necessarily
   --  the numerical rank, and zero-variance components may be
   --  present. The Components overload requests exactly that many
   --  leading components: 1 <= Components <= K_all. Excess requests
   --  raise OpenCV_Error rather than silently clamping. The
   --  Retained_Variance overload asks OpenCV 4.10 to choose K from a
   --  variance fraction: 0.95 means 95 percent, not 95.0. Valid
   --  values satisfy 0.0 < Retained_Variance <= 1.0; NaN is
   --  rejected. OpenCV 4.10 computes the full eigenvalue set, then
   --  retains rowRange(0, L) after breaking at the first cumulative
   --  energy that is strictly greater than Retained_Variance. The
   --  component that first exceeded the threshold is therefore not
   --  included, so the returned basis is not guaranteed in every
   --  case to represent at least the requested fraction. This is
   --  OpenCV 4.10 behavior. Retained_Variance = 1.0 cannot satisfy
   --  energy > 1.0 for ordinary positive-total-variance input, so
   --  OpenCV retains every available component. The overload always
   --  keeps at least two components and therefore requires
   --  Available_Components >= 2. A one-component source is rejected
   --  here because OpenCV 4.10's retained-variance implementation
   --  would then attempt rowRange(0, 2) on a one-row eigen result.
   --  The all-components and Components overloads continue to
   --  support one-component PCA. Zero-total-variance input can
   --  produce 0/0 in OpenCV's cumulative-energy ratio and is outside
   --  this binding's stronger public numerical guarantees. For K
   --  retained components, Eigenvalues is K x 1 in descending order
   --  and Eigenvectors is K x Feature_Count with one principal
   --  direction per row. Eigenvector sign is mathematically
   --  arbitrary: v and -v represent the same direction. OpenCV PCA
   --  uses scaled covariance with the population-style 1/N
   --  convention (COVAR_SCALE), not unbiased 1/(N - 1). When
   --  feature count exceeds sample count, OpenCV may compute a
   --  smaller sample-space covariance internally; the public result
   --  is always expressed in feature space. Rank-deficient data and
   --  zero eigenvalues are allowed. Self must be non-empty and
   --  Float32 or Float64. Multi-channel Mats, integer depths, and
   --  Float16 are rejected. Sample count and feature count must both
   --  be nonzero. Available component count must not exceed 8_460
   --  because OpenCV 4.10's fallback symmetric eigensolver computes
   --  an internal iteration bound using signed integer arithmetic
   --  that is not safe for larger covariance dimensions. This limit
   --  applies even when Components is 1, because OpenCV computes the
   --  full covariance eigen decomposition before truncating.
   --  Outputs preserve Self's floating-point depth and are
   --  independently owned. The caller does not preallocate any
   --  output. Continuity is not required; non-contiguous Regions are
   --  supported. Self is unchanged. Finite sample values are a
   --  caller precondition: this binding does not replace NaN or
   --  Infinity, and OpenCV's eigen path is not specified for
   --  non-finite input.
   --  @param Self The 2-D single-channel Float32 or Float64 sample matrix.
   --  @param Orientation Whether samples are the rows or the columns of Self.
   --  @return The mean, eigenvalues and eigenvectors retaining every
   --  available component.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, a
   --  component count above 8_460, or an OpenCV failure.
   function Principal_Component_Analysis
     (Self : Mat; Orientation : Sample_Orientation := Samples_Are_Rows)
      return Principal_Component_Analysis_Result;

   --  Explicit-component form of Principal_Component_Analysis: retains
   --  exactly the requested number of leading components, which must lie in
   --  1 .. K_all as described above. Excess requests raise OpenCV_Error
   --  rather than being clamped.
   --  @param Self The 2-D single-channel Float32 or Float64 sample matrix.
   --  @param Components Number of leading components to retain.
   --  @param Orientation Whether samples are the rows or the columns of Self.
   --  @return The mean, eigenvalues and eigenvectors with K = Components.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, an
   --  out-of-range Components, a component count above 8_460, or an OpenCV
   --  failure.
   function Principal_Component_Analysis
     (Self        : Mat;
      Components  : Positive;
      Orientation : Sample_Orientation := Samples_Are_Rows)
      return Principal_Component_Analysis_Result;

   --  Retained-variance form of Principal_Component_Analysis: OpenCV chooses
   --  K from the variance fraction as described above, always keeping at
   --  least two components, so at least two components must be available.
   --  @param Self The 2-D single-channel Float32 or Float64 sample matrix.
   --  @param Retained_Variance Fraction in (0.0, 1.0]; 0.95 means 95 percent.
   --  @param Orientation Whether samples are the rows or the columns of Self.
   --  @return The mean, eigenvalues and eigenvectors for the chosen K.
   --  @exception OpenCV_Error Raised for an empty or unsupported Self, an
   --  invalid Retained_Variance, fewer than two available components, a
   --  component count above 8_460, or an OpenCV failure.
   function Principal_Component_Analysis
     (Self              : Mat;
      Retained_Variance : Long_Float;
      Orientation       : Sample_Orientation := Samples_Are_Rows)
      return Principal_Component_Analysis_Result;

   --  Projects Self onto an already computed PCA basis. This does
   --  not recompute Principal_Component_Analysis. Self is a 2-D
   --  single-channel sample matrix of new or existing observations.
   --  Orientation must match the layout used to produce Basis and
   --  is not inferred from Basis.Mean: a one-feature column mean is
   --  1 x 1 and is therefore ambiguous. Samples_Are_Rows, the
   --  default, requires Basis.Mean = 1 x F and Self = S x F, and
   --  returns S x K. Samples_Are_Columns requires Basis.Mean =
   --  F x 1 and Self = F x S, and returns K x S. K is
   --  Basis.Eigenvectors.Rows and F is Basis.Eigenvectors.Columns.
   --  Self must be non-empty and Float32 or Float64. Multi-channel
   --  Mats, integer depths, and Float16 are rejected. Self's
   --  floating-point depth may differ from Basis.Mean; OpenCV
   --  converts the samples to the basis precision internally. The
   --  independently owned result has Basis.Mean.Depth. Basis.Mean
   --  must be non-empty, single-channel, and Float32 or Float64.
   --  Basis.Eigenvectors must be non-empty, single-channel, the
   --  same depth as Basis.Mean, and K x F with 1 <= K <= F.
   --  Basis.Eigenvalues is not used. Continuity is not required;
   --  non-contiguous Regions are supported. Self and Basis are
   --  unchanged. Finite sample values are a caller precondition:
   --  this binding does not replace NaN or Infinity.
   --  @param Self The observations to project.
   --  @param Basis A previously computed PCA result; Eigenvalues is unused.
   --  @param Orientation Whether samples are the rows or the columns of Self;
   --  it must match the layout that produced Basis.
   --  @return The projected coordinates, S x K or K x S.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function PCA_Project
     (Self        : Mat;
      Basis       : Principal_Component_Analysis_Result;
      Orientation : Sample_Orientation := Samples_Are_Rows) return Mat;

   --  Reconstructs feature-space samples from principal-component
   --  coordinates using an already computed PCA basis. This does
   --  not recompute Principal_Component_Analysis. Self is a 2-D
   --  single-channel coordinate matrix. Orientation must match the
   --  layout used to produce Basis and is not inferred from
   --  Basis.Mean: a one-feature column mean is 1 x 1 and is
   --  therefore ambiguous. Samples_Are_Rows, the default, requires
   --  Basis.Mean = 1 x F and Self = S x K, and returns S x F.
   --  Samples_Are_Columns requires Basis.Mean = F x 1 and Self =
   --  K x S, and returns F x S. K is Basis.Eigenvectors.Rows and
   --  F is Basis.Eigenvectors.Columns. Self must be non-empty and
   --  Float32 or Float64. Multi-channel Mats, integer depths, and
   --  Float16 are rejected. Self's floating-point depth may differ
   --  from Basis.Mean; OpenCV converts the coordinates to the
   --  basis precision internally. The independently owned result
   --  has Basis.Mean.Depth. Basis.Mean and Basis.Eigenvectors must
   --  satisfy the same structural contract as PCA_Project.
   --  Basis.Eigenvalues is not used. Continuity is not required;
   --  non-contiguous Regions are supported. Self and Basis are
   --  unchanged. Finite coordinate values are a caller
   --  precondition: this binding does not replace NaN or Infinity.
   --  @param Self The principal-component coordinates.
   --  @param Basis A previously computed PCA result; Eigenvalues is unused.
   --  @param Orientation Whether samples are the rows or the columns of Self;
   --  it must match the layout that produced Basis.
   --  @return The reconstructed feature-space samples, S x F or F x S.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function PCA_Back_Project
     (Self        : Mat;
      Basis       : Principal_Component_Analysis_Result;
      Orientation : Sample_Orientation := Samples_Are_Rows) return Mat;

   --  Interprets each Self element as its channel vector and applies
   --  OpenCV 4.10 cv::transform. This is a per-element channel/vector
   --  transform at the same spatial location; it does not geometrically
   --  move pixels. Coefficients.Rows determines the result channel
   --  count. An M x N coefficient Mat, where N is Self.Channels,
   --  performs the linear transform Result(I) = Coefficients * Self(I).
   --  An M x (N+1) coefficient Mat performs the affine transform
   --  Result(I) = Coefficients * [Self(I); 1], so the final column is
   --  additive bias. The result preserves Self's rows, columns, and
   --  depth. Self must be non-empty, at most two-dimensional, and have
   --  1 to 4 channels. Result channels may be 1 to 512. Supported
   --  source depths are UInt8, Int8, UInt16, Int16, Int32, Float32, and
   --  Float64. Float16 is rejected because OpenCV 4.10 has no
   --  TransformFunc for CV_16F. Coefficients must be a non-empty
   --  single-channel Float32 or Float64 Mat with at least one and at
   --  most 512 rows and either Self.Channels or Self.Channels + 1
   --  columns. Integer coefficient Mats are rejected. OpenCV internally
   --  represents coefficients as Float32 for UInt8, Int8, UInt16,
   --  Int16, and Float32 sources, and as Float64 for Int32 and Float64
   --  sources; a Float64 coefficient Mat used with a Float32 source is
   --  therefore converted internally to Float32, and a Float32
   --  coefficient Mat used with Int32 or Float64 Self is converted
   --  internally to Float64. Integer output conversion follows OpenCV's
   --  native saturate_cast / rounding rules. Continuity is not
   --  required; non-contiguous Regions are supported for both Self and
   --  Coefficients. Inputs are unchanged. The result owns independent
   --  storage.
   --  @param Self The source Mat whose elements are channel vectors.
   --  @param Coefficients The M x N linear or M x (N + 1) affine matrix.
   --  @return A new Mat with M channels and independent storage.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Transform (Self : Mat; Coefficients : Mat) return Mat;

   --  Interprets each Self element as a 2D or 3D vector and applies
   --  OpenCV 4.10 cv::perspectiveTransform. This transforms vector
   --  coordinates at each Mat element. It does not spatially resample,
   --  warp, interpolate, or move pixels in an image; that operation is
   --  imgproc warpPerspective. Self must be a non-empty Float32 or
   --  Float64 Mat with at most two dimensions and exactly 2 or 3
   --  channels. C1, C4 and larger, and every non-floating depth
   --  including Float16, are rejected. Transform_Matrix must be a
   --  non-empty single-channel Float32 or Float64 Mat with at most two
   --  dimensions. A C2 source requires a 3x3 matrix. A C3 source
   --  requires a 4x4 matrix. Other matrix sizes, including the internal
   --  OpenCV C3-to-C2 3x4 path, are not part of this API. The result
   --  preserves Self's rows, columns, depth, and channels. OpenCV
   --  performs the homogeneous division. When abs(w) <= FLT_EPSILON,
   --  OpenCV 4.10 writes a zero vector; the same FLT_EPSILON threshold
   --  is used for Float32 and Float64 sources. OpenCV converts a
   --  non-continuous or non-Float64 matrix to an internal Float64
   --  coefficient buffer; this binding does not pre-convert it.
   --  Continuity is not required; non-contiguous Regions are supported
   --  for both Self and Transform_Matrix. Inputs are unchanged. The
   --  result owns independent storage.
   --  Float32 C2, Float64 C2, Float32 C3, and Float64 C3 results can be
   --  inspected directly via their corresponding Vec2/Vec3_Access packages.
   --  @param Self The Float32 or Float64 Mat of 2D or 3D vectors.
   --  @param Transform_Matrix The 3x3 (C2) or 4x4 (C3) matrix.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for empty, mismatched or unsupported
   --  operands, or an OpenCV failure.
   function Perspective_Transform
     (Self : Mat; Transform_Matrix : Mat) return Mat;

   --  Reduces a two-dimensional Mat independently in every channel.
   --  Across_Rows produces one row; Across_Columns produces one column. The
   --  result owns independent storage and, without an Output_Depth, uses
   --  Self's depth.
   --  @param Self The two-dimensional Mat to reduce.
   --  @param Axis Direction of the reduction.
   --  @param Kind Reduction to apply.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported operand or an OpenCV
   --  failure.
   function Reduce
     (Self : Mat; Axis : Reduction_Axis; Kind : Reduction_Kind) return Mat;

   --  Reduces as the overload above, with an explicit result depth. Maximum
   --  and Minimum require Output_Depth to equal Self.Depth.
   --  @param Self The two-dimensional Mat to reduce.
   --  @param Axis Direction of the reduction.
   --  @param Kind Reduction to apply.
   --  @param Output_Depth Depth of the result.
   --  @return A new Mat of depth Output_Depth with independent storage.
   --  @exception OpenCV_Error Raised for an unsupported operand or depth
   --  combination, or an OpenCV failure.
   function Reduce
     (Self         : Mat;
      Axis         : Reduction_Axis;
      Kind         : Reduction_Kind;
      Output_Depth : Depth_Type) return Mat;
   --  Returns independently owned CV_32SC1 index Mats. Indices are zero-based
   --  along Axis: Across_Rows produces 1 x Self.Columns row indices, while
   --  Across_Columns produces Self.Rows x 1 column indices. Self must be
   --  non-empty and single-channel; supported depths are UInt8, Int8, UInt16,
   --  Int16, Int32, Float32, and Float64. Float16 is not dispatched by the
   --  OpenCV 4.10 implementation. Equal
   --  extrema select the first or last occurrence as requested. Non-contiguous
   --  Regions are supported, Self is unchanged, and results do not share its
   --  storage. OpenCV leaves behavior unspecified when Float32 or Float64 NaN
   --  values participate in the reduction.
   --  @param Self The non-empty single-channel Mat to search.
   --  @param Axis Direction of the reduction.
   --  @param Occurrence Whether the first or last equal extremum is chosen.
   --  @return A new Int32 C1 Mat of zero-based indices of the minima.
   --  @exception OpenCV_Error Raised for an empty, multi-channel or
   --  unsupported-depth Self, or an OpenCV failure.
   function Arg_Minimum
     (Self       : Mat;
      Axis       : Reduction_Axis;
      Occurrence : Extremum_Occurrence := First_Occurrence) return Mat;

   --  Maximum counterpart of Arg_Minimum, with the same shape, depth,
   --  occurrence and NaN rules.
   --  @param Self The non-empty single-channel Mat to search.
   --  @param Axis Direction of the reduction.
   --  @param Occurrence Whether the first or last equal extremum is chosen.
   --  @return A new Int32 C1 Mat of zero-based indices of the maxima.
   --  @exception OpenCV_Error Raised for an empty, multi-channel or
   --  unsupported-depth Self, or an OpenCV failure.
   function Arg_Maximum
     (Self       : Mat;
      Axis       : Reduction_Axis;
      Occurrence : Extremum_Occurrence := First_Occurrence) return Mat;

   --  Mean and Mean_Std_Dev operate independently on each channel and
   --  support one through four channels, matching Scalar's complete
   --  representation. Mean returns a zero Scalar for an empty Mat;
   --  Mean_Std_Dev rejects one.
   --  @param Self The Mat to average.
   --  @return A Scalar whose component N is the mean of channel N.
   --  @exception OpenCV_Error Raised for more than four channels or an
   --  OpenCV failure.
   function Mean (Self : Mat) return Scalar;

   --  Mean of Self elements selected by Mask. Mask uses the common mask
   --  contract (UInt8, one channel, same shape as Self). Any nonzero mask
   --  value selects the element. An all-zero mask returns a zero Scalar.
   --  Empty Self/Mask follow OpenCV mean semantics (zero Scalar).
   --  @param Self The Mat to average.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @return A Scalar whose component N is the mean of channel N.
   --  @exception OpenCV_Error Raised for more than four channels, a Mask
   --  that violates the mask contract, or an OpenCV failure.
   function Mean (Self, Mask : Mat) return Scalar;

   --  Per-channel mean and population standard deviation of every element of
   --  Self. Self must have one through four channels and must not be empty.
   --  @param Self The non-empty Mat to summarize.
   --  @return The per-channel mean and standard deviation.
   --  @exception OpenCV_Error Raised for an empty Mat, more than four
   --  channels, or an OpenCV failure.
   function Mean_Std_Dev (Self : Mat) return Mean_Std_Dev_Result;

   --  Per-channel mean and population standard deviation of Self elements
   --  selected by Mask. Mask uses the common mask contract. Any nonzero mask
   --  value selects the element. An all-zero mask returns zero mean and
   --  standard-deviation Scalars. Empty Self/Mask is rejected.
   --  @param Self The non-empty Mat to summarize.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @return The per-channel mean and standard deviation.
   --  @exception OpenCV_Error Raised for an empty Mat, more than four
   --  channels, a Mask that violates the mask contract, or an OpenCV
   --  failure.
   function Mean_Std_Dev (Self, Mask : Mat) return Mean_Std_Dev_Result;

   --  Computes the requested norm over every element of Self, as a single
   --  Long_Float across all channels.
   --  @param Self The Mat to measure.
   --  @param Kind L1, L2 or infinity norm.
   --  @return The norm of Self.
   --  @exception OpenCV_Error Raised when OpenCV rejects Self.
   function Norm (Self : Mat; Kind : Norm_Kind := L2) return Long_Float;

   --  Computes the requested norm over elements selected by Mask. Mask uses
   --  the common mask contract (UInt8, one channel, same shape as Self). Any
   --  nonzero mask value selects every scalar component of the element. Empty
   --  Self/Mask and all-zero masks return zero according to OpenCV semantics.
   --  @param Self The Mat to measure.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @param Kind L1, L2 or infinity norm.
   --  @return The norm of the selected elements.
   --  @exception OpenCV_Error Raised for a Mask that violates the mask
   --  contract or an OpenCV failure.
   function Norm
     (Self : Mat; Mask : Mat; Kind : Norm_Kind := L2) return Long_Float;

   --  Native two-input numerical norm across all channels. Left and Right
   --  must have identical native dimensionality, complete shape, depth and
   --  channels. Supports UInt8, Int8, UInt16, Int16, Float32 and Float64 only;
   --  Int32 and Float16 are rejected, even when empty. Callers may explicitly
   --  Convert_To (Float64). Matching N-D and noncontiguous views are accepted.
   --  Total * Channels must not exceed 268_435_455 (INT32_MAX / 8), with
   --  checked preflight arithmetic; native row strides must fit signed int.
   --  Compatible default-empty or typed-empty operands return zero, after
   --  checking all shape/type contracts. Inputs and shallow aliases are not
   --  modified. No difference Mat or implicit whole-matrix conversion is used.
   --  Relative passes NORM_RELATIVE to OpenCV: the generic implementation
   --  divides by Right's norm plus DBL_EPSILON, including zero/near-zero
   --  Right.
   --  Native backends may differ in precision and relative implementation.
   --  Float32 intermediates can round/overflow before the C double result;
   --  NaN/Infinity behavior is native-defined, not filtered or normalized.
   --  @param Left First numeric operand.
   --  @param Right Second operand and relative reference.
   --  @param Kind L1, L2 or infinity norm.
   --  @param Relative Request native relative normalization.
   --  @return Native C double result converted to Long_Float.
   --  @exception OpenCV_Error Invalid input, unsafe count/stride or native
   --  failure. Nonfinite native results are not validation errors.
   function Difference_Norm
     (Left, Right : Mat; Kind : Norm_Kind := L2; Relative : Boolean := False)
      return Long_Float;

   --  Masked Difference_Norm with the same numeric, count, empty and
   --  exception contract. Mask must be UInt8 C1 with the complete native
   --  shape of Left. Every nonzero mask value selects the entire logical
   --  element and every channel, without scaling; zero excludes it.
   --  Noncontiguous/N-D masks and borrowed aliases are accepted. An all-zero
   --  mask returns zero for absolute norms of finite operands. Relative
   --  empty selection is backend-defined: IPP can return NaN, while the
   --  generic Right-norm-plus-epsilon path returns zero. Preserve that result.
   --  @param Left First numeric operand.
   --  @param Right Second numeric operand and relative reference.
   --  @param Mask Numeric selector, not a Hamming bit mask.
   --  @param Kind L1, L2 or infinity norm.
   --  @param Relative Request native relative normalization.
   --  @return Native masked C double result converted to Long_Float.
   --  @exception OpenCV_Error Invalid operands/mask, count/stride or native
   --  failure. Native nonfinite behavior is preserved.
   function Difference_Norm
     (Left, Right : Mat;
      Mask        : Mat;
      Kind        : Norm_Kind := L2;
      Relative    : Boolean := False) return Long_Float;

   --  Direct native NORM_L2SQR reduction, not the square of Mat.Norm.
   --  Supports the six numeric depths, layouts, count/stride bounds and
   --  nonfinite behavior documented for Difference_Norm. Int32/Float16 are
   --  rejected; compatible empty input returns zero after type validation.
   --  @param Self Numeric source; all channels contribute.
   --  @return Native squared-L2 result converted from C double.
   --  @exception OpenCV_Error Unsupported depth, unsafe count/stride or native
   --  failure. No automatic conversion or finite-result guarantee is made.
   function Squared_L2_Norm (Self : Mat) return Long_Float;

   --  Direct masked NORM_L2SQR with Squared_L2_Norm's numeric/count/empty
   --  contract and Difference_Norm's numeric mask contract. Nonzero mask
   --  values select all channels without scaling. Native rounding and
   --  nonfinite behavior are preserved; finite all-zero selection gives zero.
   --  @param Self Numeric source, including N-D/noncontiguous views.
   --  @param Mask UInt8 C1 selector with Self's complete native shape.
   --  @return Native masked squared-L2 result converted from C double.
   --  @exception OpenCV_Error Invalid source/mask, count/stride or native
   --  failure.
   function Squared_L2_Norm (Self, Mask : Mat) return Long_Float;

   --  Direct native two-input NORM_L2SQR. Same shape, six supported depths,
   --  channels, count/stride, empty and nonfinite contracts as
   --  Difference_Norm.
   --  No saturated subtraction, temporary difference or L2 squaring in Ada.
   --  @param Left First numeric operand.
   --  @param Right Matching numeric operand.
   --  @return Native squared difference norm converted from C double.
   --  @exception OpenCV_Error Invalid operands, count/stride or native
   --  failure.
   function Squared_L2_Difference_Norm (Left, Right : Mat) return Long_Float;

   --  Masked direct native two-input NORM_L2SQR. Same numeric/count/empty
   --  and nonfinite contracts as Difference_Norm. Mask is a complete-shape
   --  UInt8 C1 numeric selector; each nonzero byte selects all channels.
   --  @param Left First numeric operand.
   --  @param Right Matching numeric operand.
   --  @param Mask Numeric element selector, never a bitwise mask.
   --  @return Native masked squared difference norm converted from C double.
   --  @exception OpenCV_Error Invalid operands/mask, count/stride or native
   --  failure.
   function Squared_L2_Difference_Norm
     (Left, Right, Mask : Mat) return Long_Float;

   --  Native Hamming/Hamming2 count of UInt8 C1 storage. One_Bit counts set
   --  bits, Two_Bits counts nonzero two-bit cells (11 counts once). No mask,
   --  relative mode or byte conversion. N-D/noncontiguous views are accepted.
   --  Total bytes must not exceed INT32_MAX/8 for One_Bit (268_435_455),
   --  INT32_MAX/4 for Two_Bits (536_870_911); row strides must fit signed int.
   --  Default-empty and UInt8 C1 typed-empty inputs return zero after type
   --  validation. Inputs/aliases are unchanged; the bounded count is exact.
   --  @param Self UInt8 single-channel source.
   --  @param Kind Strong binary cell-size selector.
   --  @return Exact native bit/cell count converted from C double.
   --  @exception OpenCV_Error Invalid type/selector, unsafe count/stride or
   --  native failure.
   function Hamming_Norm
     (Self : Mat; Kind : Binary_Norm_Kind := One_Bit) return Long_Float;

   --  Native binary distance with Hamming_Norm's type/count/empty contract.
   --  Left and Right must have identical complete native shape and UInt8 C1
   --  type, including when empty. One_Bit counts differing bits; Two_Bits
   --  counts nonzero XOR two-bit cells. Inputs and shallow aliases are
   --  unchanged.
   --  The distinct name preserves Batch_Distance_Kind.Hamming_Distance calls.
   --  @param Left First UInt8 C1 descriptor or N-D/strided byte array.
   --  @param Right Matching UInt8 C1 operand.
   --  @param Kind Strong binary cell-size selector.
   --  @return Exact native bit/cell distance converted from C double.
   --  @exception OpenCV_Error Invalid operands/selector, unsafe count/stride
   --  or native failure. Masks and relative binary distances are not exposed.
   function Hamming_Pairwise_Norm
     (Left, Right : Mat; Kind : Binary_Norm_Kind := One_Bit) return Long_Float;

   --  Computes OpenCV 4.10 cv::PSNR in decibels over every scalar channel
   --  component. Left and Right must be non-empty and have identical rows,
   --  columns, depth, and channel count. All public Mat depths, including
   --  Float16, and all channel counts are supported. Continuity is not
   --  required, so matching non-contiguous Regions are accepted. Peak_Value,
   --  OpenCV's R parameter, defaults to 255.0 and must be positive, finite,
   --  and representable as a C double. OpenCV computes
   --    20 * log10 (Peak_Value / (RMSE + DBL_EPSILON));
   --  consequently identical inputs return a large finite value rather than
   --  infinity. Inputs are unchanged. OpenCV itself would produce non-finite
   --  results for zero, negative, or non-finite peak values; this Ada API
   --  rejects those values.
   --  @param Left The first Mat.
   --  @param Right The second Mat, matching Left in size, depth and channels.
   --  @param Peak_Value Maximum possible value, positive and finite.
   --  @return The PSNR in decibels.
   --  @exception OpenCV_Error Raised for empty or mismatched operands, an
   --  invalid Peak_Value, or an OpenCV failure.
   function Peak_Signal_To_Noise_Ratio
     (Left : Mat; Right : Mat; Peak_Value : Long_Float := 255.0)
      return Long_Float;

   --  Finds the minimum and maximum of a single-channel Mat and their 2-D
   --  locations. Point.X is the column and Point.Y is the row, zero-based.
   --  @param Self The single-channel Mat to search.
   --  @return The extrema and their locations.
   --  @exception OpenCV_Error Raised when OpenCV rejects Self.
   function Min_Max_Loc (Self : Mat) return Min_Max_Result;

   --  Finds extrema among Self elements selected by Mask. Mask uses the
   --  common mask contract. Any nonzero mask value selects the element. An
   --  all-zero mask returns zero extrema and (-1, -1) locations. Point.X is
   --  the column and Point.Y is the row.
   --  @param Self The single-channel Mat to search.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @return The extrema and their locations among selected elements.
   --  @exception OpenCV_Error Raised for a Mask that violates the mask
   --  contract or an OpenCV failure.
   function Min_Max_Loc (Self, Mask : Mat) return Min_Max_Result;

   --  Dense extrema in Shape/Extent/Index_Array/Slice dimension order.
   --  Self must be non-empty, C1, and UInt8, Int8, UInt16, Int16, Int32,
   --  Float32, or Float64; Float16 is rejected on every supported version.
   --  Coordinates are zero-based and relative to Self, including Slices.
   --  For 2-D, entry 1 is row and entry 2 is column, unlike Min_Max_Loc's
   --  Point (X => column, Y => row). Dimensions = Self.Dimension_Count;
   --  only 1 .. Dimensions are meaningful, with unused entries zero.
   --  Each Has flag independently reports a native defined location; an
   --  undefined side has zero coordinates. Finite values are portable;
   --  NaN/Infinity values and location validity follow linked OpenCV and
   --  can differ by version/backend. Inputs and shallow aliases are unchanged.
   --  Every logical dense element participates, unlike Sparse_Extrema's
   --  stored-node-only reduction. Non-contiguous N-D input is supported.
   --  @param Self The non-empty single-channel Mat to search.
   --  @return The extrema and their zero-based N-dimensional locations.
   --  @exception OpenCV_Error Raised for an empty, multi-channel or
   --  unsupported-depth Self, or an OpenCV failure.
   function Min_Max_Indices (Self : Mat) return ND_Min_Max_Result;

   --  Mask must be UInt8 C1 with identical dimension count and every extent.
   --  Any nonzero mask element selects the corresponding complete element.
   --  An all-zero mask returns zero values/locations and both Has flags False.
   --  Other rules match the unmasked overload.
   --  @param Self The non-empty single-channel Mat to search.
   --  @param Mask UInt8 single-channel selector with Self's shape.
   --  @return The extrema and locations among selected elements.
   --  @exception OpenCV_Error Raised for an unsupported Self, a Mask that
   --  violates the mask contract, or an OpenCV failure.
   function Min_Max_Indices (Self : Mat; Mask : Mat) return ND_Min_Max_Result;

   --  Counts nonzero scalar elements. Supports single-channel Mats of any
   --  supported depth (including Float16). Rejects multi-channel Mats.
   --  Non-contiguous views are supported. Empty Mat returns 0.
   --  @param Self The single-channel Mat to scan.
   --  @return The number of nonzero elements.
   --  @exception OpenCV_Error Raised for a multi-channel Mat.
   function Count_Non_Zero (Self : Mat) return Mat_Size;

   --  Returns true if a single-channel Mat contains at least one nonzero
   --  element. Supports non-contiguous views. Rejects multi-channel Mats.
   --  Empty Mat returns false.
   --  @param Self The single-channel Mat to scan.
   --  @return True when at least one element is nonzero.
   --  @exception OpenCV_Error Raised for a multi-channel Mat.
   function Has_Non_Zero (Self : Mat) return Boolean;

   --  Returns locations of all nonzero elements in row-major order. Point.X
   --  is the column and Point.Y is the row. Supports 2-D, single-channel Mats
   --  with UInt8, Int8, UInt16, Int16, Int32, Float32, or Float64 depth;
   --  Float16 and multi-channel Mats are rejected. Empty and all-zero Mats
   --  return an empty Point_Array. Locations for a Region are relative to that
   --  Region rather than to its parent Mat.
   --  @param Self The 2-D single-channel Mat to scan.
   --  @return The zero-based locations of all nonzero elements.
   --  @exception OpenCV_Error Raised for a multi-channel, Float16 or
   --  otherwise unsupported Mat.
   function Find_Non_Zero (Self : Mat) return Point_Array;

   --  Checks every scalar channel value of Self. The no-bound overload
   --  uses OpenCV 4.10's default range check: NaN and +/- Infinity are
   --  invalid, and floating-point values are subject to OpenCV's default
   --  finite extrema. The positive maximum finite endpoint is excluded
   --  by the half-open upper bound. The bounded overload passes Minimum
   --  and Maximum through to OpenCV. Float32 and Float64 use the
   --  requested half-open [Minimum, Maximum) interval. Integer depths
   --  convert those floating bounds to effective integer limits with
   --  OpenCV's floor/ceil behavior before checking, so a value may be
   --  accepted even when it is not mathematically inside
   --  [Minimum, Maximum). First_Invalid.X is the column and
   --  First_Invalid.Y is the row of the first invalid element in
   --  row-major order. Multi-channel Mats are checked channel-by-channel;
   --  the reported Point identifies the element, not a channel. Supports
   --  UInt8, Int8, UInt16, Int16, Int32, Float32, and Float64. Float16 is
   --  not supported by OpenCV 4.10. Empty Mats, including a default empty
   --  Mat and typed 0x0 Mats, are valid when they contain no elements.
   --  Non-contiguous Regions are accepted; First_Invalid is relative to
   --  Self. Does not modify Self.
   --  @param Self The Mat to check.
   --  @return Valid True, or the location of the first invalid element.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   function Check_Range (Self : Mat) return Range_Check_Result;

   --  Bounded form of Check_Range: values must lie in the half-open interval
   --  [Minimum, Maximum), subject to the integer-depth conversion described
   --  above.
   --  @param Self The Mat to check.
   --  @param Minimum Inclusive lower bound.
   --  @param Maximum Exclusive upper bound.
   --  @return Valid True, or the location of the first invalid element.
   --  @exception OpenCV_Error Raised for an unsupported depth or an OpenCV
   --  failure.
   function Check_Range
     (Self : Mat; Minimum : Long_Float; Maximum : Long_Float)
      return Range_Check_Result;

   --  Replaces every NaN scalar channel value of Self in place. Only
   --  Float32 Mats are accepted; UInt8, Int8, UInt16, Int16, Int32,
   --  Float16, and Float64 are rejected. Multi-channel values are
   --  processed channel-by-channel. The default replacement is 0.0.
   --  Finite values and +/- Infinity are left unchanged, so a Mat that
   --  still contains Infinity is not necessarily valid according to
   --  Check_Range. The replacement is converted to Float32 before it
   --  is stored; NaN and infinite replacements are stored as that
   --  Float32 representation. Non-contiguous Regions are accepted and
   --  mutate their parent/shared storage. A normal shallow Mat alias
   --  observes the same mutation. A typed 0x0 Float32 Mat is a no-op
   --  that preserves its depth and channel count. A default empty Mat
   --  is rejected because its depth is not Float32.
   --  @param Self The Float32 Mat modified in place.
   --  @param Value Replacement stored for each NaN, converted to Float32.
   --  @exception OpenCV_Error Raised for a non-Float32 Mat.
   procedure Patch_NaNs (Self : in out Mat; Value : Float32_Value := 0.0);

   --  Completes Self into a symmetric square Mat in place. Source names
   --  the authoritative triangle. Upper_Triangle, the default, preserves
   --  the diagonal and upper triangle and copies each upper-triangle
   --  element onto its reflected lower-triangle location. That mapping
   --  is OpenCV 4.10 lowerToUpper=false. Lower_Triangle preserves the
   --  diagonal and lower triangle and copies each lower-triangle element
   --  onto its reflected upper-triangle location. Self must be square
   --  and Float32 or Float64. Any valid channel count is accepted
   --  because OpenCV copies each complete element with elemSize().
   --  Dimensions, depth, and channel count are unchanged. Continuity is
   --  not required. Non-contiguous Regions are supported and mutate the
   --  corresponding parent pixels around the Region's own diagonal. A
   --  normal shallow Mat alias observes the same mutation. Clone remains
   --  independent. A typed 0x0 Float32 or Float64 Mat is a no-op that
   --  preserves its depth and channel count. A default empty Mat is
   --  rejected because its depth is not Float32 or Float64. This
   --  procedure does not allocate a replacement Mat.
   --  @param Self The square Float32 or Float64 Mat modified in place.
   --  @param Source The triangle that is authoritative and is reflected.
   --  @exception OpenCV_Error Raised for a non-square Mat or an unsupported
   --  depth.
   procedure Complete_Symmetry
     (Self : in out Mat; Source : Symmetry_Source := Upper_Triangle);

   --  Initializes Self in place as a scaled identity. Self is modified
   --  directly; this procedure does not allocate a replacement Mat.
   --  Self need not be square. Every off-diagonal element becomes zero
   --  and each main-diagonal element becomes Value converted by
   --  OpenCV's Scalar conversion. The diagonal length is
   --  min (Rows, Columns). The default Value is (1.0, 0.0, 0.0, 0.0),
   --  matching cv::Scalar (1); it does not replicate 1 to every
   --  channel. For a multi-channel Mat the Scalar components map to
   --  the corresponding channels. All eight public depths are
   --  accepted, including Float16. Channel count must be 1 through 4;
   --  more than four channels are rejected because OpenCV's Scalar
   --  conversion path only represents four destination channels.
   --  Dimensions, depth, and channel count are unchanged. Continuity
   --  is not required. Non-contiguous Regions are supported and mutate
   --  the corresponding parent pixels around the Region's own
   --  diagonal. A normal shallow Mat alias observes the same
   --  mutation. Clone remains independent. A default empty Mat and
   --  typed 0x0 Mats are no-ops that preserve their metadata.
   --  @param Self The Mat modified in place.
   --  @param Value Diagonal value; component N initializes channel N.
   --  @exception OpenCV_Error Raised for a Mat with more than four channels.
   procedure Set_Identity
     (Self  : in out Mat;
      Value : Scalar := (Component_0 => 1.0, others => 0.0));

   --  Version text queried on each call from the linked native OpenCV runtime,
   --  not the Ada crate version or consumer headers. The returned String owns
   --  its bytes independently of later queries and native object lifetimes.
   --  Raises OpenCV_Error on native failure, inconsistent counts, or a payload
   --  exceeding Natural'Last - 1 bytes. Allocation may raise Storage_Error.
   --  @return Owned version bytes from the linked native library.
   --  @exception OpenCV_Error Native failure or invalid/oversized text result.
   function Native_Version_String return String;

   --  Full build-specific native configuration text, queried on every call.
   --  The independently owned String preserves all bytes, including newlines
   --  and non-ASCII content; it excludes the ABI terminating NUL. No fixed
   --  format or cross-build equality is promised. Same errors and capacity
   --  limit as Native_Version_String.
   --  @return Independently owned full native build information, without NUL.
   --  @exception OpenCV_Error Native failure or invalid/oversized text result.
   function Native_Build_Information return String;
private

   type Float16_Value is record
      Bits : Interfaces.Unsigned_16 := 0;
   end record
   with Size => 16, Object_Size => 16, Alignment => 2, Convention => C;

   type Random_Number_Generator is record
      State : Interfaces.Unsigned_64 := 16#FFFF_FFFF#;
   end record;

   type Mat is new Ada.Finalization.Controlled with record
      Handle         : OpenCV.Internal.C_API.Mat_Handle :=
        OpenCV.Internal.C_API.Null_Mat_Handle;
      Temporary_View : Boolean := False;
   end record;

   type UMat is new Ada.Finalization.Controlled with record
      Handle : OpenCV.Internal.C_API.UMat_Handle :=
        OpenCV.Internal.C_API.Null_UMat_Handle;
   end record;

   --  Controlled initialization: gives the UMat a default empty native
   --  header.
   --  @param Self The UMat being initialized.
   overriding
   procedure Initialize (Self : in out UMat);

   --  Controlled assignment hook: replaces the copied handle with a new
   --  native header that shares the same reference-counted storage, so
   --  assignment is shallow.
   --  @param Self The UMat that has just been assigned.
   overriding
   procedure Adjust (Self : in out UMat);

   --  Controlled finalization: releases the native header owned by the UMat.
   --  Storage is freed when the last header referring to it is released.
   --  @param Self The UMat being finalized.
   overriding
   procedure Finalize (Self : in out UMat);

   --  Controlled initialization: gives the Mat a default empty native
   --  header.
   --  @param Self The Mat being initialized.
   overriding
   procedure Initialize (Self : in out Mat);

   --  Controlled assignment hook: replaces the copied handle with a new
   --  native header that shares the same reference-counted storage, so
   --  assignment is shallow.
   --  @param Self The Mat that has just been assigned.
   overriding
   procedure Adjust (Self : in out Mat);

   --  Controlled finalization: releases the native header owned by the Mat.
   --  Storage is freed when the last header referring to it is released.
   --  @param Self The Mat being finalized.
   overriding
   procedure Finalize (Self : in out Mat);

end OpenCV.Core;
