--  Callback-scoped Mat views over caller-owned single-channel UInt8
--  (CV_8UC1) buffers. A view never copies or owns the caller's Data: the
--  temporary Mat handed to the callback aliases Data directly and is valid
--  only during the callback. The writable forms let the callback modify
--  Data through the Mat; the read-only forms pass the Mat in mode and accept
--  constant Data. Packed forms describe contiguous row-major or N-D storage;
--  strided forms add row or per-dimension strides counted in complete
--  UInt8 elements (not bytes). Shape, size and stride violations raise
--  OpenCV_Error before the callback is invoked. A temporary view cannot be
--  retained, shallow-copied, sliced, reshaped or used as a destination; use
--  Clone to keep independent values.

package OpenCV.Core.UInt8_Mat_View is

   --  A flat buffer of UInt8_Value elements supplied by the caller. Its index
   --  bounds are the caller's choice: only Data'First (the first element)
   --  and Data'Length (the capacity) are used, and the lower bound is not
   --  exposed through the Mat.
   type Buffer_Array is array (Natural range <>) of UInt8_Value;

   --  Invokes Process with a temporary writable Mat that aliases Data.
   --  Image (0, 0) is Data (Data'First) and row-major element Image
   --  (Row, Column) is Data (Data'First + Row * Columns + Column).
   --  Data'Length must equal Rows * Columns. The Ada lower bound is
   --  not exposed through the Mat. Image is valid only during Process
   --  and must not be retained. Ordinary shallow copies and views are
   --  rejected because they would share the caller-owned buffer after
   --  Process returns. Clone is the supported way to keep an
   --  independent Mat. Writes through Image immediately modify Data,
   --  and writes through Data immediately affect Image. The temporary
   --  cv::Mat header does not own Data and does not copy it. The aliased
   --  formal passes Data by reference, so Image denotes caller-owned storage.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be Rows * Columns.
   --  @param Rows Positive row count of Image, within the native signed
   --  32-bit range.
   --  @param Columns Positive column count of Image, within the native
   --  signed 32-bit range.
   --  @param Process Callback that receives the temporary writable Image. It
   --  is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when
   --  Data'Length differs from Rows * Columns or a dimension exceeds the
   --  native range.
   procedure With_Writable_Mat_View
     (Data    : aliased in out Buffer_Array;
      Rows    : Positive;
      Columns : Positive;
      Process : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable packed N-dimensional CV_8UC1
   --  Mat that aliases Data. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) and every
   --  extent must be positive; Shape iteration order maps directly to
   --  OpenCV dimension order regardless of Shape'First. Data'Length must
   --  equal product (Shape) exactly. Storage is packed and continuous with
   --  the final dimension varying fastest: zero-based index (I1, .., In)
   --  is Data (Data'First + ((I1 * D2 + I2) * D3 + ..) * Dn + In). Neither
   --  Ada lower bound is exposed through the Mat. Shape => (Rows, Columns)
   --  has the same geometry as the Rows/Columns overload. No data is
   --  copied and the caller retains ownership. Callback lifetime and escape
   --  rules are identical to the Rows/Columns overload: shallow copies,
   --  Slice, and Reshape are rejected; Clone is the independent escape path.
   --  Gapped N-D storage uses With_Writable_Strided_Mat_View (Shape,
   --  Strides).
   --  @param Data The caller-owned packed buffer that Image aliases, passed
   --  by reference; its length must equal the product of Shape.
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0), in OpenCV dimension order.
   --  @param Process Callback that receives the temporary writable Image. It
   --  is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Shape
   --  has fewer than 2 or more than 32 dimensions (more than 10 on OpenCV
   --  5.0), more dimensions than the linked OpenCV supports, an extent is
   --  zero, or Data'Length differs from the product of Shape.
   procedure With_Writable_Mat_View
     (Data    : aliased in out Buffer_Array;
      Shape   : Dimension_Array;
      Process : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable CV_8UC1 Mat that aliases
   --  Data with Row_Stride UInt8 elements between logical row starts.
   --  Row_Stride must be at least Columns. Image (Row, Column) maps to
   --  Data (Data'First + Row * Row_Stride + Column). Data'Length must be at
   --  least Rows * Row_Stride, including padding after the final logical row.
   --  Padding and extra trailing storage are outside the logical Mat.
   --  No data is copied. Ownership, callback lifetime, and escape rules are
   --  identical to With_Writable_Mat_View; Clone is the safe escape path.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in UInt8 elements, between the starts of
   --  consecutive rows; at least Columns.
   --  @param Process Callback that receives the temporary writable Image. It
   --  is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when
   --  Row_Stride is less than Columns, Data is shorter than Rows *
   --  Row_Stride, or a dimension exceeds the native range.
   procedure With_Writable_Strided_Mat_View
     (Data       : aliased in out Buffer_Array;
      Rows       : Positive;
      Columns    : Positive;
      Row_Stride : Positive;
      Process    : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable strided N-dimensional
   --  CV_8UC1 Mat that aliases Data. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) with
   --  positive extents, and Strides supplies exactly one stride per
   --  dimension in the same order; neither array's index bounds matter.
   --  Strides count complete UInt8 elements, not bytes. The final stride
   --  must be 1 and each outer stride must cover its nested inner block:
   --  Strides (I) >= Strides (I + 1) * Shape (I + 1), so layouts never
   --  overlap or run backwards. Zero-based index (I1, .., In) is
   --  Data (Data'First + I1 * S1 + .. + In * Sn). Data'Length must be at
   --  least Shape (first) * Strides (first): the complete outer stride,
   --  including padding after the final logical outer block, is part of the
   --  native header and must exist. Extra trailing storage is allowed and is
   --  outside the header; padding is never a logical element and is not
   --  touched. Is_Continuous reports the actual layout, so packed-equivalent
   --  strides are continuous. No data is copied and the caller retains
   --  ownership. Callback lifetime and escape rules match the other
   --  overloads: shallow copies, Slice, Reshape, and output handles are
   --  rejected; Clone is the independent escape path and holds only the
   --  logical values.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Shape (first) * Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in UInt8 elements (not bytes);
   --  the final stride must be 1 and each outer stride must cover its nested
   --  inner block.
   --  @param Process Callback that receives the temporary writable Image. It
   --  is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Shape
   --  or Strides violates the rules above, Shape has more dimensions than
   --  the linked OpenCV supports, the two arrays differ in length, or Data
   --  is too short.
   procedure With_Writable_Strided_Mat_View
     (Data    : aliased in out Buffer_Array;
      Shape   : Dimension_Array;
      Strides : Dimension_Stride_Array;
      Process : not null access procedure (Image : in out Mat));

   --  Read-only caller-owned zero-copy views. Data may be an aliased constant.
   --  Geometry, capacity, element order, and bounds follow the corresponding
   --  writable overloads above (including complete final-stride padding).
   --  Mode-in Image cannot be passed to normal mutating Ada APIs. Memory is
   --  not OS-protected. Shallow escape is rejected; Clone is independent.
   --  Module_Interop input handles and input-only Core operations are allowed.
   --  This overload views a packed row-major buffer; Data'Length must equal
   --  Rows * Columns.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be Rows * Columns.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Process Callback that receives the temporary read-only Image.
   --  It is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when
   --  Data'Length differs from Rows * Columns or a dimension exceeds the
   --  native range.
   procedure With_Read_Only_Mat_View
     (Data          : aliased Buffer_Array;
      Rows, Columns : Positive;
      Process       : not null access procedure (Image : Mat));

   --  Read-only view of a packed N-dimensional buffer, with the geometry
   --  rules of the writable N-dimensional overload: Shape has 2 to 32
   --  (at most 10 on OpenCV 5.0)
   --  positive extents and Data'Length equals their product. The temporary
   --  Image is valid only during the callback.
   --  @param Data The caller-owned packed buffer that Image aliases; it may
   --  be an aliased constant.
   --  @param Shape Extent of each dimension, in OpenCV dimension order.
   --  @param Process Callback that receives the temporary read-only Image.
   --  It is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Shape
   --  is invalid, has more dimensions than the linked OpenCV supports, or
   --  Data'Length differs from the product of Shape.
   procedure With_Read_Only_Mat_View
     (Data    : aliased Buffer_Array;
      Shape   : Dimension_Array;
      Process : not null access procedure (Image : Mat));

   --  Read-only view of a two-dimensional buffer with Row_Stride UInt8
   --  elements between row starts, following the geometry and capacity rules
   --  of the writable strided overload. Padding between rows is not part of
   --  the logical Mat. The temporary Image is valid only during the callback.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in UInt8 elements, between row starts; at
   --  least Columns.
   --  @param Process Callback that receives the temporary read-only Image.
   --  It is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when
   --  Row_Stride is less than Columns, Data is too short, or a dimension
   --  exceeds the native range.
   procedure With_Read_Only_Strided_Mat_View
     (Data                      : aliased Buffer_Array;
      Rows, Columns, Row_Stride : Positive;
      Process                   : not null access procedure (Image : Mat));

   --  Read-only view of a strided N-dimensional buffer, following the
   --  geometry, stride and capacity rules of the writable strided
   --  N-dimensional overload. Strides count complete UInt8 elements, not
   --  bytes. The temporary Image is valid only during the callback.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in UInt8 elements; the final
   --  stride must be 1 and each outer stride must cover its nested inner
   --  block.
   --  @param Process Callback that receives the temporary read-only Image.
   --  It is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Shape
   --  or Strides violates the rules above, Shape has more dimensions than
   --  the linked OpenCV supports, or Data is too short.
   procedure With_Read_Only_Strided_Mat_View
     (Data    : aliased Buffer_Array;
      Shape   : Dimension_Array;
      Strides : Dimension_Stride_Array;
      Process : not null access procedure (Image : Mat));
end OpenCV.Core.UInt8_Mat_View;
