with OpenCV.Core.Float32_Vec2;

--  Callback-scoped Mat views over caller-owned two-channel Float32
--  (CV_32FC2) buffers. One Data element is one complete Float32_Vec2.Vector
--  pixel, so lengths and strides count pixels, not scalar channels and not
--  bytes. A view never copies or owns the caller's Data: the temporary Mat
--  handed to the callback aliases Data directly and is valid only during the
--  callback. The writable forms let the callback modify Data through the Mat;
--  the read-only forms pass the Mat in mode and accept constant Data. Shape,
--  size and stride violations raise OpenCV_Error before the callback is
--  invoked. A temporary view cannot be retained, shallow-copied, sliced,
--  reshaped or used as a destination; use Clone to keep independent values.

package OpenCV.Core.Float32_Vec2_Mat_View is
   --  A flat buffer of Float32_Vec2.Vector pixels supplied by the caller. Its
   --  index bounds are the caller's choice: only Data'First (the first
   --  element) and Data'Length (the capacity) are used.
   type Buffer_Array is array (Natural range <>) of Float32_Vec2.Vector;

   --  One Data element is one complete C2 element. The temporary Mat must
   --  not escape Process; Clone is the supported independent escape path.
   --  Invokes Process with a temporary writable CV_32FC2 Mat that aliases
   --  Data; Image (Row, Column) is Data (Data'First + Row * Columns + Column)
   --  and Data'Length must equal Rows * Columns.
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

   --  Packed N-D view: Shape'Length in 2 .. 32
   --  (at most 10 on OpenCV 5.0), positive extents in OpenCV
   --  dimension order, Data'Length = product (Shape) complete C2 elements,
   --  final dimension fastest. Neither Ada lower bound is visible. No copy;
   --  the caller keeps ownership; shallow escape (including Slice and
   --  Reshape) is rejected and Clone is the independent escape path.
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

   --  2-D row-strided view. Row_Stride counts Vec2 elements; backing
   --  includes final-row padding. Image (Row, Column) maps to
   --  Data (Data'First + Row * Row_Stride + Column).
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
     (Data                      : aliased in out Buffer_Array;
      Rows, Columns, Row_Stride : Positive;
      Process                   :
        not null access procedure (Image : in out Mat));

   --  Strided N-D view: one stride per Shape dimension (bounds irrelevant),
   --  counted in complete Vec2 elements, not scalars or bytes. Final stride
   --  is 1 and Strides (I) >= Strides (I + 1) * Shape (I + 1). Index
   --  (I1, .., In) is Data (Data'First + I1 * S1 + .. + In * Sn).
   --  Data'Length >= Shape (first) * Strides (first), including final outer
   --  padding; extra trailing entries are allowed and padding is untouched.
   --  No copy; the caller keeps ownership; shallow escape is rejected and
   --  Clone is the independent escape path.
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
end OpenCV.Core.Float32_Vec2_Mat_View;
