with OpenCV.Core.Fixed_Matrices;

--  Fixed-size 3 x 3 matrix of Float32_Value elements, an instance of
--  OpenCV.Core.Fixed_Matrices. Indices are zero-based and elements are
--  addressed as (Row, Column) with both in 0 .. 2. This is an ordinary Ada
--  array value with no OpenCV native handle; Float32_Matx3x3_Conversions
--  copies it to and from a Mat.
package OpenCV.Core.Float32_Matx3x3 is new
  OpenCV.Core.Fixed_Matrices
    (Element_Type => Float32_Value,
     Row_Count    => 3,
     Column_Count => 3);
