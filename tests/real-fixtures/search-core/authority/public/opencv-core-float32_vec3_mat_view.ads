with OpenCV.Core.Float32_Vec3;

--  Callback-scoped Mat views over caller-owned three-channel Float32
--  (CV_32FC3) buffers. A view never copies or owns the caller's Data: the
--  temporary Mat handed to the callback aliases Data directly and is valid
--  only during the callback. Each Data entry is one complete
--  OpenCV.Core.Float32_Vec3.Vector (one pixel). The writable forms let the
--  callback modify Data through the Mat; the read-only forms pass the Mat in
--  mode and accept constant Data. Packed forms describe contiguous row-major
--  or N-D storage; strided forms add row or per-dimension strides counted in
--  complete pixels (not scalar channels or bytes). Shape, size and stride
--  violations raise OpenCV_Error before the callback is invoked. A temporary
--  view cannot be retained, shallow-copied, sliced, reshaped or used as a
--  destination; use Clone to keep independent values.

package OpenCV.Core.Float32_Vec3_Mat_View is

   --  A flat buffer of Float32_Vec3.Vector pixels supplied by the caller. Its
   --  index bounds are the caller's choice: only Data'First (the first
   --  pixel) and Data'Length (the capacity, counted in pixels) are used, and
   --  the lower bound is not exposed through the Mat.
   type Buffer_Array is
     array (Natural range <>) of OpenCV.Core.Float32_Vec3.Vector;

   --  Invokes Process with a temporary writable CV_32FC3 Mat that aliases
   --  Data.  Each Data component is one complete pixel.  Image (Row, Column)
   --  is Data (Data'First + Row * Columns + Column).  Data'Length must equal
   --  Rows * Columns; it counts pixels, not scalar channels.  Image is valid
   --  only during Process and must not be retained.  Clone is the supported
   --  way to keep an independent Mat.  The aliased formal passes Data by
   --  reference, so Image denotes caller-owned storage without copying it.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length, in pixels, must be Rows * Columns.
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

   --  Invokes Process with a temporary writable packed N-dimensional
   --  CV_32FC3 Mat that aliases Data. One Data component is one complete C3
   --  element. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) and every extent must be
   --  positive; Shape iteration order maps directly to OpenCV dimension
   --  order regardless of Shape'First. Data'Length must equal product
   --  (Shape) exactly; it counts pixels, not scalar channels. Storage is
   --  packed and continuous with the final dimension varying fastest:
   --  zero-based index (I1, .., In) is Data (Data'First + ((I1 * D2 + I2) *
   --  D3 + ..) * Dn + In). Neither Ada lower bound is exposed through the
   --  Mat. Shape => (Rows, Columns) has the same geometry as the
   --  Rows/Columns overload. No data is copied and the caller retains
   --  ownership. Callback lifetime and escape rules are identical to the
   --  Rows/Columns overload: shallow copies, Slice, and Reshape are
   --  rejected; Clone is the independent escape path. Gapped N-D storage
   --  uses With_Writable_Strided_Mat_View (Shape, Strides).
   --  @param Data The caller-owned packed buffer that Image aliases, passed
   --  by reference; its length, in pixels, must equal the product of Shape.
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

   --  Invokes Process with a temporary writable CV_32FC3 Mat that aliases
   --  Data with Row_Stride complete Float32_Vec3 pixels between logical row
   --  starts. Row_Stride counts pixels, not scalar channels and not bytes.
   --  Row_Stride must be at least Columns. Image (Row, Column) maps to
   --  Data (Data'First + Row * Row_Stride + Column). Data'Length must be at
   --  least Rows * Row_Stride, including padding pixels after the final
   --  logical row. Padding and extra trailing pixels are outside the logical
   --  Mat. No data is copied. Ownership, callback lifetime, and escape rules
   --  are identical to With_Writable_Mat_View; Clone is the safe escape path.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length, in pixels, must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in pixels, between the starts of
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
   --  CV_32FC3 Mat that aliases Data. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) with
   --  positive extents, and Strides supplies exactly one stride per
   --  dimension in the same order; neither array's index bounds matter.
   --  Strides count complete Float32_Vec3 pixels, not scalar channels and
   --  not bytes. The final stride must be 1 and each outer stride must cover
   --  its nested inner block: Strides (I) >= Strides (I + 1) * Shape (I + 1).
   --  Zero-based index (I1, .., In) is Data (Data'First + I1 * S1 + .. +
   --  In * Sn). Data'Length must be at least Shape (first) * Strides
   --  (first) pixels, including padding after the final logical outer
   --  block, which the native header covers. Extra trailing pixels are
   --  allowed and are outside the header; padding is never touched.
   --  Is_Continuous reports the actual layout. No data is copied and the
   --  caller retains ownership. Shallow copies, Slice, Reshape, and output
   --  handles are rejected; Clone is the independent escape path.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length, in pixels, must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in pixels; the final stride
   --  must be 1 and each outer stride must cover its nested inner block.
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

   --  Read-only zero-copy caller-owned views (one Data entry per vector).
   --  Aliased constant Data is accepted; geometry/capacity are exactly those
   --  of the corresponding writable overloads. Mode-in Image prevents normal
   --  Ada mutation, not OS/page writes. Shallow escape is rejected; Clone
   --  owns independent pixels and Module_Interop input is allowed.
   --  This overload views a packed row-major buffer; Data'Length must equal
   --  Rows * Columns.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length, in pixels, must be Rows * Columns.
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
   --  positive extents and Data'Length equals their product.
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

   --  Read-only view of a two-dimensional buffer with Row_Stride pixels
   --  between row starts, following the geometry and capacity rules of the
   --  writable strided overload. Padding between rows is not part of the
   --  logical Mat.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in pixels, between row starts; at least
   --  Columns.
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
   --  N-dimensional overload. Strides count complete pixels, not scalar
   --  channels and not bytes.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in pixels; the final stride
   --  must be 1 and each outer stride must cover its nested inner block.
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
end OpenCV.Core.Float32_Vec3_Mat_View;
