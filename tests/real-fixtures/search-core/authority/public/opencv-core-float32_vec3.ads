with OpenCV.Core.Vectors;

--  One complete CV_32FC3 Mat element (12 bytes). Components 0 .. 2 are
--  OpenCV channel indices holding single-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec3f
--  (float) alias.
package OpenCV.Core.Float32_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Float32_Value, Length => 3);
