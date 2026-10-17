with OpenCV.Core.Vectors;

--  One complete CV_64FC2 Mat element (16 bytes). Components 0 .. 1 are
--  OpenCV channel indices holding double-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec2d
--  (double) alias.
package OpenCV.Core.Float64_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Float64_Value, Length => 2);
