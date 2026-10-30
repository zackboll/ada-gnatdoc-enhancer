with OpenCV.Core.Vectors;

--  One complete CV_32SC3 Mat element (12 bytes). Components 0 .. 2 are
--  OpenCV channel indices holding signed 32-bit integers; no semantic
--  channel meaning is assigned. It corresponds to the native Vec3i (int)
--  alias.
package OpenCV.Core.Int32_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Int32_Value, Length => 3);
