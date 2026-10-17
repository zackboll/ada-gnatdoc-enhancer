with OpenCV.Core.Float16_Vec2;

--  Callback-scoped CV_16FC2 Mat headers over caller-owned Data. One Data
--  entry is one complete 4-byte C2 element; each component is the exact
--  stored IEEE-754 binary16 encoding (nothing is converted). Packed views
--  require Data'Length = Rows * Columns or product (Shape). Strides count
--  complete Float16_Vec2 elements, not scalar Float16 channels or bytes;
--  the final N-D stride is 1 and padding is never touched. No data is
--  copied and the caller retains ownership. The Mat is valid only during
--  Process: shallow copies, Region, Slice and Reshape are rejected; Clone
--  is the independent escape path. Component 0 and 1 are OpenCV channels
--  0 and 1; no semantic channel meaning is assigned. Shape, size and stride
--  violations raise OpenCV_Error before the callback is invoked.

package OpenCV.Core.Float16_Vec2_Mat_View is

   --  A flat buffer of two-channel pixels supplied by the caller. Its index
   --  bounds are the caller's choice: only Data'First (the first pixel) and
   --  Data'Length (the capacity, counted in pixels) are used.
   type Buffer_Array is array (Natural range <>) of Float16_Vec2.Vector;

   --  Invokes Process with a temporary writable packed CV_16FC2 Mat that
   --  aliases Data. Image (Row, Column) is
   --  Data (Data'First + Row * Columns + Column). Writes through Image
   --  immediately modify Data and vice versa.
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
     (Data          : aliased in out Buffer_Array;
      Rows, Columns : Positive;
      Process       : not null access procedure (Image : in out Mat));

   --  Invokes Process with a temporary writable packed N-dimensional
   --  CV_16FC2 Mat that aliases Data, with the final dimension varying
   --  fastest. Shape iteration order maps to OpenCV dimension order
   --  regardless of Shape'First.
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

   --  Invokes Process with a temporary writable CV_16FC2 Mat that aliases
   --  Data with Row_Stride complete pixels between logical row starts.
   --  Image (Row, Column) maps to Data (Data'First + Row * Row_Stride +
   --  Column). Padding and extra trailing storage are outside the logical
   --  Mat.
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length, in pixels, must be at least Rows * Row_Stride.
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
   --  CV_16FC2 Mat that aliases Data. Strides supplies exactly one stride
   --  per dimension in the same order as Shape, counted in complete pixels.
   --  The final stride must be 1 and each outer stride must cover its nested
   --  inner block: Strides (I) >= Strides (I + 1) * Shape (I + 1).
   --  @param Data The caller-owned buffer that Image aliases, passed by
   --  reference; its length, in pixels, must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in complete pixels (not
   --  scalar channels, not bytes); the final stride must be 1 and each outer
   --  stride must cover its nested inner block.
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

   --  Read-only view of a packed row-major buffer; geometry and capacity
   --  match the writable Rows/Columns overload. Data may be an aliased
   --  constant, and the mode-in Image prevents normal Ada mutation.
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
   --  rules of the writable N-dimensional overload.
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

   --  Read-only view of a two-dimensional buffer with Row_Stride complete
   --  pixels between row starts, following the rules of the writable
   --  strided overload. Padding between rows is not part of the logical Mat.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length, in pixels, must be at least
   --  Rows * Row_Stride.
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
   --  N-dimensional overload. Strides count complete pixels.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length, in pixels, must be at least
   --  Shape (first) * Strides (first).
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
end OpenCV.Core.Float16_Vec2_Mat_View;
