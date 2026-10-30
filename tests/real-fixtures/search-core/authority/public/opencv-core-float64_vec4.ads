with OpenCV.Core.Vectors;

--  One complete CV_64FC4 Mat element (32 bytes). Components 0 .. 3 are
--  OpenCV channel indices holding double-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec4d
--  (double) alias.
package OpenCV.Core.Float64_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Float64_Value, Length => 4);
