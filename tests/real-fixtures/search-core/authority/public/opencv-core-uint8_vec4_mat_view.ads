with OpenCV.Core.UInt8_Vec4;

--  Callback-scoped Mat views over caller-owned four-channel UInt8
--  (CV_8UC4) buffers. A view never copies or owns the caller's Data: the
--  temporary Mat handed to the callback aliases Data directly and is valid
--  only during the callback. Each Data entry is one complete
--  OpenCV.Core.UInt8_Vec4.Vector (one pixel). The writable forms let the
--  callback modify Data through the Mat; the read-only forms pass the Mat in
--  mode and accept constant Data. Packed forms describe contiguous row-major
--  or N-D storage; strided forms add row or per-dimension strides counted in
--  complete pixels (not scalar channels or bytes). Shape, size and stride
--  violations raise OpenCV_Error before the callback is invoked. A temporary
--  view cannot be retained, shallow-copied, sliced, reshaped or used as a
--  destination; use Clone to keep independent values.

package OpenCV.Core.UInt8_Vec4_Mat_View is

   --  A flat buffer of UInt8_Vec4.Vector pixels supplied by the caller. Its
   --  index bounds are the caller's choice: only Data'First (the first
   --  pixel) and Data'Length (the capacity, counted in pixels) are used, and
   --  the lower bound is not exposed through the Mat.
   type Buffer_Array is array (Natural range <>) of UInt8_Vec4.Vector;

   --  Invokes Process with a temporary writable CV_8UC4 Mat that aliases
   --  Data. Image (Row, Column) is Data (Data'First + Row * Columns +
   --  Column). Data'Length must equal Rows * Columns; it counts pixels, not
   --  scalar channels. Caller owns storage; strides count complete vectors.
   --  Shallow views cannot escape the callback; Clone creates independent
   --  storage.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be Rows * Columns pixels.
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
     (Data          : aliased in out Buffer_Array;
      Rows, Columns : Positive;
      Process       : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable packed N-dimensional CV_8UC4
   --  Mat that aliases Data. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) and every
   --  extent must be positive; Shape iteration order maps to OpenCV
   --  dimension order regardless of Shape'First. Data'Length must equal
   --  product (Shape) exactly, counted in pixels. Storage is packed and
   --  continuous with the final dimension varying fastest. Callback
   --  lifetime and escape rules match the Rows/Columns overload.
   --  @param Data The caller-owned packed buffer that Image aliases, passed
   --  by reference; its length must equal the product of Shape, in pixels.
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

   --  Invokes Process with a temporary writable CV_8UC4 Mat that aliases
   --  Data with Row_Stride complete pixels between logical row starts.
   --  Row_Stride must be at least Columns. Image (Row, Column) maps to
   --  Data (Data'First + Row * Row_Stride + Column). Data'Length must be at
   --  least Rows * Row_Stride, including padding after the final logical
   --  row. Padding is outside the logical Mat. Ownership, callback lifetime
   --  and escape rules match With_Writable_Mat_View.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Rows * Row_Stride pixels.
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
     (Data                      : aliased in out Buffer_Array;
      Rows, Columns, Row_Stride : Positive;
      Process                   :
        not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable strided N-dimensional
   --  CV_8UC4 Mat that aliases Data. Shape'Length must be in 2 .. 32
   --  (at most 10 on OpenCV 5.0) with
   --  positive extents, and Strides supplies exactly one stride per
   --  dimension in the same order. Strides count complete pixels, not scalar
   --  channels and not bytes. The final stride must be 1 and each outer
   --  stride must cover its nested inner block: Strides (I) >=
   --  Strides (I + 1) * Shape (I + 1). Data'Length must be at least
   --  Shape (first) * Strides (first) pixels. Callback lifetime and escape
   --  rules match the other overloads.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Shape (first) * Strides (first)
   --  pixels.
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in pixels (not scalar
   --  channels or bytes); the final stride must be 1 and each outer stride
   --  must cover its nested inner block.
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

   --  Mode-in callback preserves the read-only Ada capability boundary;
   --  aliased constant caller storage is accepted without copying. This
   --  overload views a packed row-major buffer; the geometry and capacity
   --  rules are those of the corresponding writable overload, so
   --  Data'Length must equal Rows * Columns.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be Rows * Columns pixels.
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

   --  Read-only view of a two-dimensional buffer with Row_Stride pixels
   --  between row starts, following the geometry and capacity rules of the
   --  writable strided overload. Padding between rows is not part of the
   --  logical Mat. The temporary Image is valid only during the callback.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Rows * Row_Stride
   --  pixels.
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
   --  channels or bytes. The temporary Image is valid only during the
   --  callback.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Shape (first) *
   --  Strides (first) pixels.
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
end OpenCV.Core.UInt8_Vec4_Mat_View;
