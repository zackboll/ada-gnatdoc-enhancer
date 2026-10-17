with Ada.Finalization;
private with OpenCV.Internal.C_API;

package OpenCV.Core.Sparse is
   --  Runtime-typed sparse N-dimensional matrix backed by a native OpenCV
   --  cv::SparseMat. Unlike a dense Mat, only explicitly stored elements (the
   --  nodes) occupy memory and are visited by the reductions here; a missing
   --  coordinate is not the same as a stored zero, although both read as
   --  zero through the typed Get operations. Each Sparse_Mat object is a
   --  controlled header that owns its native resource. Ada assignment is
   --  shallow: the target receives its own header while the nodes stay shared
   --  and reference counted, so a write through one header is visible
   --  through the other. Clone makes an explicit deep copy. A default
   --  Sparse_Mat is unallocated: it reports zero dimensions and most
   --  operations reject it with OpenCV_Error. Sparse_Mat has no Region or
   --  view operations and is not interchangeable with Mat or UMat.
   type Sparse_Mat is tagged private;

   --  Creates an allocated sparse matrix with no stored nodes. Shape is read
   --  in iteration order, independent of its index bounds: the first element
   --  is the extent of native dimension 0. Between 2 and 32 dimensions are
   --  required, and every extent must be positive. Element_Type fixes the
   --  depth and channel count of every stored element. Every coordinate is
   --  initially missing, and the matrix owns its storage independently.
   --  @param Shape Extent of each dimension, in native dimension order.
   --  @param Element_Type Depth and channel count of each stored element.
   --  @return A new, empty, allocated Sparse_Mat.
   --  @exception OpenCV_Error Raised when Shape has fewer than 2 or more
   --  than 32 dimensions, an extent is zero, or OpenCV rejects the shape.
   function Create
     (Shape : Dimension_Array; Element_Type : Mat_Type) return Sparse_Mat;

   --  Converts a dense Mat into an independent Sparse_Mat of the same shape,
   --  depth and channel count. Only elements that are not entirely zero are
   --  stored; an element is omitted when all of its stored bytes are zero,
   --  so a Float16 negative zero (16#8000#) and a NaN are stored. A
   --  multi-channel element is stored as a whole when any channel is
   --  nonzero. The result does not share storage with Source, and later
   --  changes to either do not affect the other. Non-contiguous Regions are
   --  accepted.
   --  @param Source The nonempty dense Mat to convert.
   --  @return A new Sparse_Mat holding the nonzero elements of Source.
   --  @exception OpenCV_Error Raised when Source is empty or OpenCV reports
   --  a failure.
   function From_Dense (Source : Mat) return Sparse_Mat;

   --  Converts Self into an independent dense Mat of the same shape, depth
   --  and channel count. Stored nodes are copied and every missing
   --  coordinate is zero. Self is unchanged and the result owns independent
   --  storage. The conversion is rejected when the dimension count exceeds
   --  the native dense Mat capacity (10 on OpenCV 5.0).
   --  @param Self The allocated Sparse_Mat to expand.
   --  @return A new dense Mat with independent storage.
   --  @exception OpenCV_Error Raised when Self is unallocated, has too many
   --  dimensions for a dense Mat, or OpenCV reports a failure.
   function To_Dense (Self : Sparse_Mat) return Mat;

   --  Native SparseMat::convertTo into an independent Sparse_Mat. Shape and
   --  channel count are preserved. Only stored nodes are converted, including
   --  an explicitly stored zero; missing coordinates stay missing. Each stored
   --  component becomes saturate_cast (source * Scale) at Depth. There is no
   --  offset. Scale 1.0 uses OpenCV's unscaled conversion. Float16 is not a
   --  supported source or destination: OpenCV 4.1 through 5.0 leave both
   --  directions null in the sparse conversion tables, and this binding does
   --  not substitute a Float32 fallback. Float16 Get/Set bit preservation is
   --  unchanged.
   --  @param Self The allocated Sparse_Mat to convert.
   --  @param Depth Depth of the stored components of the result.
   --  @param Scale Factor applied to each stored component before
   --  saturation.
   --  @return A new Sparse_Mat with independent storage.
   --  @exception OpenCV_Error Raised when Self is unallocated, either depth
   --  is Float16, or OpenCV reports a failure.
   function Convert_To
     (Self : Sparse_Mat; Depth : Depth_Type; Scale : Long_Float := 1.0)
      return Sparse_Mat;

   --  Native SparseMat::convertTo into an independent dense Mat. Shape and
   --  channel count are preserved. A stored component becomes
   --  saturate_cast (source * Scale + Offset). A missing element is
   --  initialized with OpenCV Scalar (Offset): channel 0 receives Offset and
   --  every later channel receives 0, because Scalar supplies one value and
   --  three zeros. Float16 source and destination depths are rejected for the
   --  same OpenCV 4.1-5.0 table gap as Convert_To. On OpenCV 5, dimension
   --  counts above the native dense Mat capacity are rejected before
   --  conversion.
   --  @param Self The allocated Sparse_Mat to expand.
   --  @param Depth Depth of the dense result.
   --  @param Scale Factor applied to each stored component.
   --  @param Offset Value added to each stored component, and used to
   --  initialize channel 0 of every missing element.
   --  @return A new dense Mat with independent storage.
   --  @exception OpenCV_Error Raised when Self is unallocated, either depth
   --  is Float16, the dimension count exceeds the dense Mat capacity, or
   --  OpenCV reports a failure.
   function To_Dense
     (Self   : Sparse_Mat;
      Depth  : Depth_Type;
      Scale  : Long_Float := 1.0;
      Offset : Long_Float := 0.0) return Mat;
   --  Native sparse cv::norm over stored nodes only. Missing coordinates
   --  contribute zero and are not created. An explicitly stored zero
   --  contributes zero and remains a node. The matrix is not modified.
   --  Requires an allocated Float32 or Float64 matrix with exactly one
   --  channel. An allocated matrix with no stored nodes returns 0.0.
   --  L1 is the sum of absolute stored values, L2 is the square root of the
   --  sum of their squares, and Infinity is the maximum absolute stored
   --  value. Multi-channel, integer, and Float16 layouts are rejected
   --  before the ABI call. Min_Max is not a sparse norm.
   --  @param Self The allocated single-channel Float32 or Float64 matrix.
   --  @param Kind L1, L2 or infinity norm.
   --  @return The norm of the stored nodes.
   --  @exception OpenCV_Error Raised for an unallocated, multi-channel,
   --  integer or Float16 layout, or an OpenCV failure.
   function Norm (Self : Sparse_Mat; Kind : Norm_Kind := L2) return Long_Float;

   --  Native sparse cv::normalize into an independent Sparse_Mat. Shape,
   --  depth, channel count, and stored-node coordinates are preserved,
   --  including explicitly stored zeros. Values are scaled by
   --  Target_Norm / Norm when that norm exceeds OpenCV's DBL_EPSILON;
   --  otherwise the scale is 0.0 and every stored value becomes zero while
   --  its node remains stored. An allocated matrix with no nodes stays
   --  empty. A negative Target_Norm is native and deterministic: it reverses
   --  the sign of every stored value. The source is unchanged. The same
   --  Float32/Float64 single-channel restriction as Norm applies. Min_Max
   --  normalization is unavailable because shifting implicit zeros would
   --  change sparse semantics.
   --  @param Self The allocated single-channel Float32 or Float64 matrix.
   --  @param Target_Norm Norm the stored values are scaled to.
   --  @param Kind L1, L2 or infinity norm.
   --  @return A new Sparse_Mat with independent storage.
   --  @exception OpenCV_Error Raised for an unallocated, multi-channel,
   --  integer or Float16 layout, or an OpenCV failure.
   function Normalize
     (Self        : Sparse_Mat;
      Target_Norm : Long_Float := 1.0;
      Kind        : Norm_Kind := L2) return Sparse_Mat;
   --  Native sparse cv::minMaxLoc over stored nodes only. Requires an
   --  allocated Float32 or Float64 matrix with exactly one channel. Missing
   --  coordinates do not participate and are not created. An explicitly
   --  stored zero is a candidate. Comparisons use strict < and >, so the
   --  earliest node in OpenCV's hash traversal that holds an equal extremum
   --  is reported. That order is unspecified and is not insertion order.
   --  Negative zero compares equal to positive zero. NaN never replaces a
   --  finite extremum. Has_Minimum and Has_Maximum are independent: each is
   --  True only when native OpenCV wrote that location. Empty storage and a
   --  NaN-only matrix establish neither. Positive infinity and a stored
   --  Float32 FLT_MAX or Float64 DBL_MAX establish only the maximum, because
   --  neither is strictly less than OpenCV's initial minimum. Negative
   --  infinity and a stored -FLT_MAX or -DBL_MAX establish only the minimum.
   --  A side that was not established returns 0.0 and an all-zero location;
   --  the native initialization sentinels are not public extrema. Each
   --  location is a fixed 32-coordinate array; only elements 1 .. Dimensions
   --  are meaningful, and those values are the zero-based OpenCV coordinates.
   --  The matrix is not modified. Integer, Float16, multi-channel, and
   --  unallocated layouts are rejected before the ABI call. Min_Max
   --  normalization remains unavailable.
   --  @field Has_Minimum True when Minimum and Minimum_Location were written
   --  by native OpenCV.
   --  @field Has_Maximum True when Maximum and Maximum_Location were written
   --  by native OpenCV.
   --  @field Minimum Smallest stored value found. Meaningful only when
   --  Has_Minimum is True.
   --  @field Maximum Largest stored value found. Meaningful only when
   --  Has_Maximum is True.
   --  @field Minimum_Location Zero-based coordinates of the minimum, in
   --  entries 1 .. Dimensions; remaining entries are zero. Meaningful only
   --  when Has_Minimum is True. The array has fixed capacity 32.
   --  @field Maximum_Location Zero-based coordinates of the maximum, in
   --  entries 1 .. Dimensions; remaining entries are zero. Meaningful only
   --  when Has_Maximum is True. The array has fixed capacity 32.
   --  @field Dimensions Number of matrix dimensions, which is how many
   --  leading entries of each location array are meaningful.
   type Sparse_Extrema is record
      Has_Minimum      : Boolean := False;
      Has_Maximum      : Boolean := False;
      Minimum          : Long_Float := 0.0;
      Maximum          : Long_Float := 0.0;
      Minimum_Location : Index_Array (1 .. 32) := (others => 0);
      Maximum_Location : Index_Array (1 .. 32) := (others => 0);
      Dimensions       : Natural := 0;
   end record;

   --  Finds the extrema among the stored nodes of Self; the full contract,
   --  including ties, NaN, infinities and unestablished sides, is described
   --  with Sparse_Extrema. Only stored nodes participate: missing
   --  coordinates are not created, and an explicitly stored zero is a
   --  candidate. Self is not modified.
   --  @param Self The allocated single-channel Float32 or Float64 matrix.
   --  @return The extrema and their zero-based coordinates.
   --  @exception OpenCV_Error Raised for an unallocated, multi-channel,
   --  integer or Float16 layout, or an OpenCV failure.
   function Min_Max_Loc (Self : Sparse_Mat) return Sparse_Extrema;

   --  Returns an independent deep copy of Self. Unlike Ada assignment, which
   --  shares the nodes through a distinct header, the result owns separate
   --  storage, so later writes to either matrix do not affect the other.
   --  @param Self The Sparse_Mat to copy.
   --  @return A new Sparse_Mat with independent storage.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   function Clone (Self : Sparse_Mat) return Sparse_Mat;

   --  Removes every stored node while keeping the shape and element type, so
   --  every coordinate becomes missing and an allocated Sparse_Mat stays
   --  allocated. Clearing a default (unallocated) Sparse_Mat is accepted and
   --  leaves it unallocated. Other headers that share Self's nodes through
   --  assignment observe the cleared matrix as well; a Clone is unaffected.
   --  @param Self The Sparse_Mat to clear.
   --  @exception OpenCV_Error Raised when OpenCV reports a failure.
   procedure Clear (Self : in out Sparse_Mat);

   --  Reports whether Self has a shape and element type. A default
   --  Sparse_Mat is unallocated; one from Create or From_Dense is allocated
   --  even when it holds no nodes, and stays allocated after Clear.
   --  @param Self The Sparse_Mat to inspect.
   --  @return True when Self reports at least one dimension.
   function Is_Allocated (Self : Sparse_Mat) return Boolean;

   --  Returns the native number of dimensions: 0 for an unallocated
   --  Sparse_Mat, otherwise between 2 and 32.
   --  @param Self The Sparse_Mat to inspect.
   --  @return The dimension count.
   function Dimension_Count (Self : Sparse_Mat) return Natural;

   --  Returns every extent in native dimension order, indexed 1 ..
   --  Dimension_Count. An unallocated Sparse_Mat returns a null array.
   --  @param Self The Sparse_Mat to inspect.
   --  @return The extents of all dimensions.
   function Shape (Self : Sparse_Mat) return Dimension_Array;

   --  Returns the extent of a 1-based axis. Axis 1 is native dimension 0.
   --  @param Self The allocated Sparse_Mat to inspect.
   --  @param Axis One-based dimension, in 1 .. Dimension_Count.
   --  @return The extent of that dimension.
   --  @exception OpenCV_Error Raised when Self is unallocated or Axis is
   --  greater than Dimension_Count.
   function Extent (Self : Sparse_Mat; Axis : Positive) return Size_Coordinate;

   --  Returns the depth of each channel value. Depth is independent of the
   --  channel count, which Channels reports.
   --  @param Self The allocated Sparse_Mat to inspect.
   --  @return The element depth.
   --  @exception OpenCV_Error Raised when Self is unallocated.
   function Depth (Self : Sparse_Mat) return Depth_Type;

   --  Returns the number of channels in each stored element. This counts
   --  channels, not bytes.
   --  @param Self The allocated Sparse_Mat to inspect.
   --  @return The channel count.
   --  @exception OpenCV_Error Raised when Self is unallocated.
   function Channels (Self : Sparse_Mat) return Channel_Count;

   --  Returns the size in bytes of one complete stored element, including
   --  all of its channels (native elemSize).
   --  @param Self The allocated Sparse_Mat to inspect.
   --  @return The byte size of one element.
   --  @exception OpenCV_Error Raised when Self is unallocated.
   function Element_Size (Self : Sparse_Mat) return Mat_Size;

   --  Returns the size in bytes of one channel of a stored element (native
   --  elemSize1), as opposed to the complete element size.
   --  @param Self The allocated Sparse_Mat to inspect.
   --  @return The byte size of one channel.
   --  @exception OpenCV_Error Raised when Self is unallocated.
   function Channel_Size (Self : Sparse_Mat) return Mat_Size;

   --  Returns the number of stored nodes (native nzcount). A stored zero
   --  counts, a missing coordinate does not, and the value is not the
   --  product of the extents. An unallocated Sparse_Mat reports 0.
   --  @param Self The Sparse_Mat to inspect.
   --  @return The number of stored nodes.
   function Stored_Element_Count (Self : Sparse_Mat) return Mat_Size;

   --  Reports whether a node is stored at the given coordinates, without
   --  creating one. A stored zero is contained; a missing coordinate is not.
   --  @param Self The allocated Sparse_Mat to query.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return True when a node is stored at Indices.
   --  @exception OpenCV_Error Raised when Self is unallocated, Indices does
   --  not have exactly Dimension_Count entries, or an index is out of
   --  bounds.
   function Contains (Self : Sparse_Mat; Indices : Index_Array) return Boolean;

   --  Removes the node stored at the given coordinates, if any, so the
   --  coordinate becomes missing. Erasing a missing coordinate is not an
   --  error. Shared headers observe the removal.
   --  @param Self The allocated Sparse_Mat to modify.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @exception OpenCV_Error Raised when Self is unallocated, Indices does
   --  not have exactly Dimension_Count entries, or an index is out of
   --  bounds.
   procedure Erase (Self : in out Sparse_Mat; Indices : Index_Array);

private
   type Sparse_Mat is new Ada.Finalization.Controlled with record
      Handle : OpenCV.Internal.C_API.Sparse_Mat_Handle :=
        OpenCV.Internal.C_API.Null_Sparse_Mat_Handle;
   end record;
   --  Controlled initialization: gives the Sparse_Mat a default,
   --  unallocated native header.
   --  @param Self The Sparse_Mat being initialized.
   overriding
   procedure Initialize (Self : in out Sparse_Mat);

   --  Controlled assignment hook: replaces the copied handle with a new
   --  native header that shares the same reference-counted nodes, so
   --  assignment is shallow.
   --  @param Self The Sparse_Mat that has just been assigned.
   overriding
   procedure Adjust (Self : in out Sparse_Mat);

   --  Controlled finalization: releases the native header owned by Self.
   --  The nodes are freed when the last header referring to them is released.
   --  @param Self The Sparse_Mat being finalized.
   overriding
   procedure Finalize (Self : in out Sparse_Mat);

   --  Requires an allocated matrix and exactly one in-bounds index per
   --  dimension. Used by the typed access packages before touching a node.
   --  @param Self The matrix being indexed.
   --  @param Indices The coordinates to validate.
   --  @exception OpenCV_Error Raised when Self is unallocated, Indices has
   --  the wrong length, or an index is out of bounds.
   procedure Check_Indices (Self : Sparse_Mat; Indices : Index_Array);

   --  Require an allocated matrix whose runtime depth and channel count
   --  both match the typed access package exactly, after validating
   --  Indices as Check_Indices does.
   --  @param Self The matrix being accessed.
   --  @param Indices The coordinates to validate.
   --  @param Expected The depth required by the typed access package.
   --  @param Expected_Channels The channel count required by the package.
   --  @exception OpenCV_Error Raised when the indices or element layout do
   --  not match.
   procedure Check_Layout
     (Self              : Sparse_Mat;
      Indices           : Index_Array;
      Expected          : Depth_Type;
      Expected_Channels : Channel_Count := 1);

   --  Layout-only form of Check_Layout: requires an allocated matrix whose
   --  runtime depth and channel count match exactly, without checking
   --  indices.
   --  @param Self The matrix being accessed.
   --  @param Expected The depth required by the typed access package.
   --  @param Expected_Channels The channel count required by the package.
   --  @exception OpenCV_Error Raised when Self is unallocated or its
   --  element layout does not match.
   procedure Check_Layout
     (Self              : Sparse_Mat;
      Expected          : Depth_Type;
      Expected_Channels : Channel_Count := 1);

   --  Converts zero-based Ada indices to the native 32-bit coordinate array,
   --  in the same dimension order. No bounds check is performed here.
   --  @param Indices The coordinates to convert.
   --  @return The native coordinate array, indexed from 0.
   function C_Indices
     (Indices : Index_Array) return OpenCV.Internal.C_API.C_Int32_Array;

   --  Raises OpenCV_Error, with the native diagnostic appended to Operation,
   --  when Status is not success.
   --  @param Status The result of a native call.
   --  @param Operation Description of the operation, used in the message.
   --  @exception OpenCV_Error Raised when Status reports a failure.
   procedure Check (Status : OpenCV.Internal.C_API.Status; Operation : String);
end OpenCV.Core.Sparse;
