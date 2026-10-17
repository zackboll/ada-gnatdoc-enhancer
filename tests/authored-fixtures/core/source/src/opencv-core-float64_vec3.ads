with OpenCV.Core.Vectors;

--  One complete CV_64FC3 Mat element (24 bytes). Components 0 .. 2 are
--  OpenCV channel indices holding double-precision floating-point values; no
--  semantic channel meaning is assigned. It corresponds to the native Vec3d
--  (double) alias.
package OpenCV.Core.Float64_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Float64_Value, Length => 3);
