with OpenCV.Core.Vectors;

--  One complete CV_32FC4 Mat element (16 bytes). Components 0 .. 3 are
--  OpenCV channel indices holding single-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec4f
--  (float) alias.
package OpenCV.Core.Float32_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Float32_Value, Length => 4);
