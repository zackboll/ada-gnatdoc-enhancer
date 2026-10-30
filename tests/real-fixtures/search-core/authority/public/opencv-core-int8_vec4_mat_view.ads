with OpenCV.Core.Int8_Vec4;

--  Callback-scoped CV_8SC4 Mat headers over caller-owned Data. One Data
--  entry is one complete 4-byte C4 element; each component is a signed
--  -128 .. 127 value. Packed views require Data'Length = Rows * Columns
--  or product (Shape). Strides count complete Int8_Vec4 elements, not
--  scalar Int8 channels or bytes; the final N-D stride is 1 and padding
--  is never touched. No data is copied and the caller retains ownership.
--  The Mat is valid only during Process: shallow copies, Region, Slice
--  and Reshape are rejected; Clone is the independent escape path.
--  Components 0 .. 3 are OpenCV channels 0 .. 3; no semantic channel
--  meaning is assigned.

package OpenCV.Core.Int8_Vec4_Mat_View is

   --  A flat buffer of complete four-channel vectors supplied by the caller.
   --  Only Data'First and Data'Length are used.
   type Buffer_Array is array (Natural range <>) of Int8_Vec4.Vector;

   --  Invokes Process with a temporary writable four-channel Mat that
   --  aliases Data in packed row-major order. Writes through Image modify
   --  Data.
   --  @param Data The caller-owned buffer that Image aliases; its length
   --  must be Rows * Columns.
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
   --  four-channel Mat that aliases Data, with the final dimension varying
   --  fastest.
   --  @param Data The caller-owned packed buffer that Image aliases; its
   --  length must equal the product of Shape.
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

   --  Invokes Process with a temporary writable four-channel Mat that
   --  aliases Data with Row_Stride vectors between logical row starts.
   --  Padding is outside the logical Mat.
   --  @param Data The caller-owned buffer that Image aliases; its length
   --  must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in vectors, between the starts of
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
   --  four-channel Mat that aliases Data. Strides count vectors, not bytes.
   --  @param Data The caller-owned buffer that Image aliases; its length
   --  must be at least Shape (first) * Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in vectors (not bytes); the
   --  final stride must be 1 and each outer stride must cover its nested
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

   --  Read-only view of a packed row-major buffer; the geometry rules match
   --  the writable Rows/Columns overload. Image is passed in mode and is
   --  valid only during the callback.
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

   --  Read-only view of a packed N-dimensional buffer; the geometry rules
   --  match the writable Shape overload.
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

   --  Read-only view of a two-dimensional buffer with Row_Stride vectors
   --  between row starts; the rules match the writable strided overload.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Rows * Row_Stride.
   --  @param Rows Positive row count of Image.
   --  @param Columns Positive column count of Image.
   --  @param Row_Stride Distance, in vectors, between row starts; at least
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

   --  Read-only view of a strided N-dimensional buffer; the rules match the
   --  writable strided Shape overload. Strides count vectors, not bytes.
   --  @param Data The caller-owned buffer that Image aliases; it may be an
   --  aliased constant. Its length must be at least Shape (first) *
   --  Strides (first).
   --  @param Shape Extent of each dimension, 2 to 32 positive values
   --  (at most 10 on OpenCV 5.0).
   --  @param Strides One stride per dimension, in vectors; the final stride
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

end OpenCV.Core.Int8_Vec4_Mat_View;
