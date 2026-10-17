with OpenCV.Core.Float32_Matx3x3;

--  Conversions between the fixed-size Float32 3 x 3 Matrix and a dense Mat.
--  Both directions copy: the Matrix is an ordinary Ada value, so neither
--  conversion shares storage with the Mat it reads or produces.

package OpenCV.Core.Float32_Matx3x3_Conversions is

   --  Creates a new 3 x 3 single-channel Float32 Mat holding a copy of
   --  Value. Element (Row, Column) of Value becomes the Mat element at that
   --  zero-based row and column. The result owns independent storage.
   --  @param Value The matrix to copy.
   --  @return A new Float32 C1 Mat with 3 rows and 3 columns.
   function To_Mat (Value : OpenCV.Core.Float32_Matx3x3.Matrix) return Mat;

   --  Copies a 3 x 3 single-channel Float32 Mat into a fixed-size Matrix.
   --  The Mat is not modified and the result shares no storage with it.
   --  Non-contiguous Regions are accepted.
   --  @param Image The Mat to read; it must have exactly three rows, three
   --  columns, Float32 depth and one channel.
   --  @return A Matrix whose element (Row, Column) is the Mat element at that
   --  zero-based row and column.
   --  @exception OpenCV_Error Raised when Image does not have exactly three
   --  rows, three columns, Float32 depth and one channel.
   function To_Matx3x3 (Image : Mat) return OpenCV.Core.Float32_Matx3x3.Matrix;

end OpenCV.Core.Float32_Matx3x3_Conversions;
