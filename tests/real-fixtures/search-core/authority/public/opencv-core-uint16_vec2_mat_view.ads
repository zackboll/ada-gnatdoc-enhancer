with OpenCV.Core.UInt16_Vec2;

--  Callback-scoped Mat views over caller-owned two-channel UInt16 (CV_16UC2)
--  buffers. Each buffer entry is one complete two-channel pixel. A view never
--  copies or owns the caller's Data: the temporary Mat handed to the callback
--  aliases Data directly and is valid only during the callback. The writable
--  forms let the callback modify Data through the Mat; the read-only forms
--  pass the Mat in mode and accept constant Data. Packed forms describe
--  contiguous row-major or N-D storage; strided forms add row or
--  per-dimension strides counted in complete pixels (not bytes or scalar
--  channel values). Shape, size and stride violations raise OpenCV_Error
--  before the callback is invoked. A temporary view cannot be retained or
--  shallow-copied; use Clone to keep independent values.

package OpenCV.Core.UInt16_Vec2_Mat_View is

   --  A flat buffer of UInt16_Vec2.Vector elements supplied by the caller.
   --  Only Data'First (the first element) and Data'Length (the capacity, in
   --  complete pixels) are used.
   type Buffer_Array is array (Natural range <>) of UInt16_Vec2.Vector;

   --  Strides count complete vectors. Shallow escape is prohibited;
   --  Clone may escape.
   --  Invokes Process with a temporary writable CV_16UC2 Mat that aliases
   --  Data in row-major order: Image (Row, Column) is
   --  Data (Data'First + Row * Columns + Column).
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be Rows * Columns.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Process Callback that receives the temporary writable Image. It
   --  is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when
   --  Data'Length differs from Rows * Columns or a dimension exceeds the
   --  native range.
   procedure With_Writable_Mat_View
     (Data          : aliased in out Buffer_Array;
      Rows, Columns : Positive;
      Process       : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable packed N-dimensional
   --  CV_16UC2 Mat that aliases Data; the final dimension varies fastest.
   --  Shape shall have 2 to 32
   --  (at most 10 on OpenCV 5.0) positive extents and Data'Length shall equal
   --  their product.
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

   --  Invokes Process with a temporary writable CV_16UC2 Mat that aliases
   --  Data with Row_Stride complete pixels between logical row starts.
   --  Row_Stride must be at least Columns and Data must hold at least
   --  Rows * Row_Stride pixels, including padding after the final row.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in complete pixels, between the starts of
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
   --  CV_16UC2 Mat that aliases Data. Strides count complete pixels, not
   --  bytes; the final stride must be 1 and each outer stride must cover its
   --  nested inner block.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length must be at least Shape (first) * Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in complete pixels; the final
   --  stride must be 1 and each outer stride must cover its nested inner
   --  block.
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

   --  Read-only view of a packed row-major buffer. Data may be an aliased
   --  constant; the geometry follows the writable Rows/Columns overload.
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
   --  rules of the writable N-dimensional overload.
   --  @param Data The caller-owned packed buffer that Image aliases; it may
   --  be an aliased constant.
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Process Callback that receives the temporary read-only Image.
   --  It is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Shape
   --  is invalid, has more dimensions than the linked OpenCV supports, or
   --  Data'Length differs from the product of Shape.
   procedure With_Read_Only_Mat_View
     (Data    : aliased Buffer_Array;
      Shape   : Dimension_Array;
      Process : not null access procedure (Image : Mat));

   --  Read-only view of a two-dimensional buffer with Row_Stride complete
   --  pixels between row starts, following the rules of the writable strided
   --  overload.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in complete pixels, between row starts; at
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
   --  N-dimensional overload. Strides count complete pixels, not bytes.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in complete pixels; the final
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
end OpenCV.Core.UInt16_Vec2_Mat_View;
