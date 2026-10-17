with OpenCV.Core.Vectors;

--  One complete CV_32FC2 Mat element (8 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding single-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec2f
--  (float) alias.
package OpenCV.Core.Float32_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Float32_Value, Length => 2);
